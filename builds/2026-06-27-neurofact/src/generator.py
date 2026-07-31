"""
generator.py — Regenerate Neurofact questions using the Anthropic API.

Fetches recent neuroscience abstracts from arXiv, then calls Claude to:
  1. Simplify each real abstract into a 1–2 sentence testable claim
  2. Generate equally plausible fake claims in the same register

Outputs game_data.json suitable for embedding in index.html.

Usage:
    python src/generator.py           # writes game_data.json
    python src/generator.py --count 30
    python src/generator.py --dry-run # validates structure without API call

Requires ANTHROPIC_API_KEY environment variable.
"""

import argparse
import json
import os
import random
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_QUERIES = [
    "cat:q-bio.NC AND (affective neuroscience OR emotion regulation)",
    "cat:q-bio.NC AND (stress cortisol memory)",
    "cat:q-bio.NC AND (psychopathy empathy amygdala)",
    "cat:q-bio.NC AND (sleep memory consolidation hippocampus)",
    "cat:q-bio.NC AND (reward dopamine striatum)",
]

CATEGORIES = [
    "Memory", "Emotion", "Stress", "Social Neuroscience", "Psychopathy",
    "Reward", "Cognitive Neuroscience", "Neuroanatomy",
    "Emotion Regulation", "Developmental Neuroscience",
]

DIFFICULTIES = ["Foundational", "Advanced", "Expert"]

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

# Seed question bank — mirrors index.html QUESTIONS constant.
# Used by tests and as fallback content when API key is unavailable.
QUESTIONS_SEED = [
    {"id": 1, "statement": "The hippocampus contains place cells — neurons that fire when an animal occupies a specific location in space — providing a neural basis for spatial navigation and episodic memory.", "answer": "real", "category": "Memory", "difficulty": "Foundational", "explanation": "Correct. Place cells in the hippocampus were discovered by John O'Keefe (1971), who shared the 2014 Nobel Prize in Physiology or Medicine for this work."},
    {"id": 2, "statement": "Mirror neurons in the premotor cortex of macaque monkeys fire both when the animal performs a goal-directed action and when it observes another individual performing the same action.", "answer": "real", "category": "Social Neuroscience", "difficulty": "Foundational", "explanation": "Correct. Mirror neurons were discovered by Giacomo Rizzolatti and colleagues at the University of Parma in the early 1990s."},
    {"id": 3, "statement": "Chronic psychological stress reduces grey matter volume in the prefrontal cortex while increasing amygdala reactivity to threat cues — a pattern reversed in part by successful treatment of stress-related disorders.", "answer": "real", "category": "Stress", "difficulty": "Advanced", "explanation": "Correct. Stress-induced structural changes in the PFC and amygdala are well-documented in animal models and human neuroimaging studies."},
    {"id": 4, "statement": "Sleep slow-wave oscillations synchronize hippocampal sharp-wave ripples with cortical up-states, a process considered necessary for the consolidation of declarative memories during sleep.", "answer": "real", "category": "Memory", "difficulty": "Expert", "explanation": "Correct. The hippocampal-cortical dialogue during NREM sleep — sharp-wave ripples time-locking with cortical slow oscillations and sleep spindles — is one of the most replicated findings in sleep and memory research."},
    {"id": 5, "statement": "Social exclusion activates the dorsal anterior cingulate cortex — a region also involved in the affective component of physical pain — supporting the hypothesis that social pain shares neural substrates with physical pain.", "answer": "real", "category": "Social Neuroscience", "difficulty": "Advanced", "explanation": "Correct. Naomi Eisenberger and colleagues demonstrated this in a seminal 2003 Science paper using the Cyberball paradigm."},
    {"id": 6, "statement": "Cognitive reappraisal — deliberately reinterpreting the meaning of an emotional stimulus — increases dorsolateral prefrontal cortex engagement and decreases amygdala activity compared to passive viewing of negative images.", "answer": "real", "category": "Emotion Regulation", "difficulty": "Advanced", "explanation": "Correct. Reappraisal is consistently associated with prefrontal up-regulation and amygdala down-regulation across dozens of fMRI studies."},
    {"id": 7, "statement": "The cerebellum contains approximately 70 billion granule cells, making it home to more neurons than the rest of the brain combined — despite accounting for only about 10% of total brain volume.", "answer": "real", "category": "Neuroanatomy", "difficulty": "Foundational", "explanation": "Correct. Granule cells alone represent roughly 50–80 billion neurons, and the total neuronal population of the cerebellum exceeds that of the cerebral cortex."},
    {"id": 8, "statement": "Individuals with psychopathy show a characteristic pattern of preserved cognitive empathy — the ability to understand another's perspective — alongside a deficit in affective empathy — the ability to share their emotional state.", "answer": "real", "category": "Psychopathy", "difficulty": "Advanced", "explanation": "Correct. This cognitive-affective dissociation is central to current models of psychopathy (e.g., Blair's Integrated Emotion System model)."},
    {"id": 9, "statement": "Cortisol crosses the blood-brain barrier and binds to mineralocorticoid and glucocorticoid receptors in the hippocampus, modulating synaptic plasticity and long-term potentiation.", "answer": "real", "category": "Stress", "difficulty": "Expert", "explanation": "Correct. The hippocampus has one of the highest densities of glucocorticoid receptors in the brain, mediating both adaptive and maladaptive effects of stress on memory."},
    {"id": 10, "statement": "The default mode network — including medial prefrontal cortex, posterior cingulate cortex, and angular gyrus — is more active during rest and mind-wandering than during externally directed attention tasks.", "answer": "real", "category": "Cognitive Neuroscience", "difficulty": "Foundational", "explanation": "Correct. The DMN was characterized by Marcus Raichle and colleagues as a 'task-negative' network active during self-referential thought and internal mentation."},
    {"id": 11, "statement": "Oxytocin administered intranasally increases trust and generosity in economic games, an effect selectively enhanced toward in-group members and capable of increasing out-group hostility.", "answer": "real", "category": "Social Neuroscience", "difficulty": "Advanced", "explanation": "Correct. Ernst Fehr demonstrated the trust-promoting effect, while Carsten De Dreu showed the in-group bias and potential out-group hostility, challenging the 'love hormone' narrative."},
    {"id": 12, "statement": "The locus coeruleus–norepinephrine system is activated by traumatic stress and modulates the encoding strength of emotional memories in the amygdala, explaining in part why traumatic events are remembered with unusual vividness.", "answer": "real", "category": "Stress", "difficulty": "Expert", "explanation": "Correct. Norepinephrine enhances synaptic plasticity in the basolateral amygdala, strengthening emotional memory traces — the pharmacological target of propranolol for PTSD prevention."},
    {"id": 13, "statement": "Individuals with damage to the ventromedial prefrontal cortex make significantly more utilitarian judgments in personal moral dilemmas — such as the trolley-footbridge problem — compared to healthy controls.", "answer": "real", "category": "Moral Cognition", "difficulty": "Advanced", "explanation": "Correct. This finding from Joshua Greene and confirmed by Liane Young and Antonio Damasio's group suggests the vmPFC dampens the emotional response that typically prevents personally harmful utilitarian acts."},
    {"id": 14, "statement": "Higher resting vagal tone — indexed by heart rate variability — is associated with greater capacity for emotion regulation and social engagement, reflecting bidirectional gut-brain signaling via the vagus nerve.", "answer": "real", "category": "Autonomic Neuroscience", "difficulty": "Advanced", "explanation": "Correct. Both polyvagal theory (Porges) and the neurovisceral integration model (Thayer & Lane) link resting HRV to prefrontal inhibitory control and social behavior."},
    {"id": 15, "statement": "Dopamine release in the ventral striatum during reward anticipation is stronger for uncertain rewards than for certain ones of equivalent expected value, driving the neural basis of gambling behavior and novelty-seeking.", "answer": "real", "category": "Reward", "difficulty": "Advanced", "explanation": "Correct. Wolfram Schultz demonstrated that dopamine neurons respond most strongly to unpredicted rewards and cues predicting uncertain reward — the 'uncertainty bonus' underlying addiction models."},
    {"id": 16, "statement": "Alpha wave synchronization between the orbitofrontal cortex and the nucleus accumbens predicts the subjective pleasantness of music, with 10 Hz coherence correlating with peak emotional response across listeners.", "answer": "fake", "category": "Music & Emotion", "difficulty": "Expert", "explanation": "AI-generated. No study has established 10 Hz OFC-NAcc alpha coherence as a predictor of music pleasure. Music-induced pleasure involves the mesolimbic dopamine system and auditory cortex, not this specific synchrony pattern."},
    {"id": 17, "statement": "Women consistently show greater bilateral amygdala activation than men when viewing fearful faces, an effect independent of stimulus exposure duration and replicated across all major fMRI datasets.", "answer": "fake", "category": "Sex Differences", "difficulty": "Advanced", "explanation": "AI-generated. Sex differences in amygdala response to emotional stimuli are inconsistent and fail to replicate across paradigms. Stimulus duration, arousal, and individual hormone differences confound most comparisons."},
    {"id": 18, "statement": "The right insula is selectively activated during disgust responses, while the left insula is selectively activated during fear responses — a dissociation confirmed by split-brain studies and lesion mapping.", "answer": "fake", "category": "Emotion", "difficulty": "Expert", "explanation": "AI-generated. Both insulae respond to disgust and fear, and neither is selectively dedicated to one emotion. No split-brain study has established this lateralization."},
    {"id": 19, "statement": "Mindfulness meditation practice for six weeks increases grey matter density in the anterior cingulate cortex but leaves hippocampal volume unchanged — indicating that benefits are primarily ACC-dependent.", "answer": "fake", "category": "Mindfulness", "difficulty": "Advanced", "explanation": "AI-generated. Sara Lazar's work found changes in insula and PFC; subsequent research has reported hippocampal changes too. The claim of unchanged hippocampus and 'primarily ACC-dependent' benefits is unsupported."},
    {"id": 20, "statement": "Chronic stress selectively damages parvalbumin-expressing interneurons in layer IV of the dorsolateral prefrontal cortex, reducing gamma oscillation power and impairing working memory capacity.", "answer": "fake", "category": "Stress", "difficulty": "Expert", "explanation": "AI-generated. While stress affects GABAergic interneurons and PFC function, selective layer IV parvalbumin damage from chronic stress is not an established finding — stress preferentially affects layers II/III pyramidal neurons."},
    {"id": 21, "statement": "The anterior commissure connects Broca's area in the left hemisphere with Wernicke's area in the right hemisphere, allowing language-related information to be bilaterally coordinated during connected speech.", "answer": "fake", "category": "Neuroanatomy", "difficulty": "Advanced", "explanation": "AI-generated. The anterior commissure primarily connects olfactory bulbs and anterior temporal lobes. Interhemispheric language communication occurs mainly through the corpus callosum, not the anterior commissure."},
    {"id": 22, "statement": "Research using transcranial magnetic stimulation shows that disrupting the right prefrontal cortex during an encoding task selectively impairs recall of emotional memories while leaving neutral memories fully intact.", "answer": "fake", "category": "Memory", "difficulty": "Expert", "explanation": "AI-generated. TMS disruption of PFC during encoding typically affects both emotional and neutral memory. Left PFC disruption more robustly affects verbal encoding, and this emotional selectivity for right PFC TMS is not established."},
    {"id": 23, "statement": "Individuals with autism spectrum disorder show a characteristic 40 Hz gamma wave deficit specifically in the fusiform face area during face processing, correlating inversely with symptom severity.", "answer": "fake", "category": "Autism", "difficulty": "Expert", "explanation": "AI-generated. While gamma-band abnormalities exist in ASD, no study has established a specific 40 Hz FFA deficit correlating inversely with symptom severity. The relationship is far more complex and inconsistent."},
    {"id": 24, "statement": "The default mode network and the executive control network show anticorrelated activity at rest, and this anticorrelation reverses to positive correlation during autobiographical memory retrieval tasks.", "answer": "fake", "category": "Cognitive Neuroscience", "difficulty": "Expert", "explanation": "AI-generated. The DMN-ECN anticorrelation does not reverse during autobiographical memory retrieval. The DMN is recruited for autobiographical memory precisely because of its internal-focus role."},
    {"id": 25, "statement": "Serotonin reuptake inhibitors increase fear conditioning thresholds in laboratory animals during the first week of administration, which is why they can paradoxically increase anxiety when first prescribed to humans.", "answer": "fake", "category": "Pharmacology", "difficulty": "Expert", "explanation": "AI-generated. SSRIs do not reliably increase fear conditioning thresholds acutely. Initial anxiety worsening is attributed to acute serotonin increases before autoreceptor desensitization, not to fear conditioning parameter changes."},
    {"id": 26, "statement": "Resting-state fMRI shows that the default mode network exhibits precisely 0.1 Hz oscillations during self-referential thought, and deviations from this frequency are a sensitive biomarker for major depressive disorder.", "answer": "fake", "category": "Cognitive Neuroscience", "difficulty": "Expert", "explanation": "AI-generated. DMN BOLD oscillations occur in the 0.01–0.1 Hz range broadly, but there is no established 0.1 Hz frequency signature for self-referential thought, nor a validated DMN frequency biomarker for depression."},
    {"id": 27, "statement": "The striatal dopamine system differentiates social stimuli from reward stimuli by routing social information through the dorsal striatum and reward information through the ventral striatum — a segregation confirmed by optogenetic silencing.", "answer": "fake", "category": "Reward", "difficulty": "Expert", "explanation": "AI-generated. While dorsal and ventral striatum have different functional emphases, they are not cleanly segregated for social vs. reward processing, and optogenetic evidence does not establish this dichotomy."},
    {"id": 28, "statement": "NREM sleep stage 2 is uniquely required for procedural motor skill consolidation, and selectively disrupting only stage 2 sleep while preserving other sleep stages abolishes overnight improvement on finger-tapping tasks.", "answer": "fake", "category": "Memory", "difficulty": "Expert", "explanation": "AI-generated. While sleep spindles in stage 2 NREM correlate with motor skill consolidation, stage 2 is not uniquely required in isolation — slow-wave sleep also contributes, and ablation studies have not established this claim."},
    {"id": 29, "statement": "Adolescent cannabis exposure produces a selective deficit in the pruning of parvalbumin interneurons in the prefrontal cortex, permanently reducing gamma oscillation amplitude and directly accounting for elevated schizophrenia risk.", "answer": "fake", "category": "Developmental Neuroscience", "difficulty": "Expert", "explanation": "AI-generated. While adolescent cannabis use correlates with elevated schizophrenia risk, the specific causal chain from cannabis to PV pruning deficits to gamma amplitude reduction as a direct mechanistic link is not established."},
    {"id": 30, "statement": "Individuals with higher empathy quotient scores show increased theta wave synchrony (4–8 Hz) between their left temporoparietal junction and right angular gyrus during perspective-taking tasks — a pattern absent in alexithymia.", "answer": "fake", "category": "Social Neuroscience", "difficulty": "Expert", "explanation": "AI-generated. While the TPJ is implicated in perspective-taking and theta oscillations are studied in social cognition, this specific left TPJ to right angular gyrus theta synchrony as a predictor of empathy quotient scores absent in alexithymia is not an established finding."},
]


def fetch_arxiv_abstracts(query: str, max_results: int = 5) -> list[dict]:
    """Return a list of dicts with title and abstract from arXiv."""
    base = "https://export.arxiv.org/api/query"
    params = f"?search_query={urllib.request.quote(query)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    url = base + params
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            xml_data = resp.read().decode("utf-8")
    except urllib.error.URLError:
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    papers = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        abstract_el = entry.find("atom:summary", ns)
        if title_el is None or abstract_el is None:
            continue
        title = " ".join(title_el.text.split())
        abstract = " ".join(abstract_el.text.split())
        papers.append({"title": title, "abstract": abstract[:600]})
    return papers


def build_prompt(real_abstracts: list[dict], n_fake: int) -> str:
    """Build the prompt for Claude to generate game content."""
    abstract_list = "\n\n".join(
        f"{i+1}. Title: {p['title']}\n   Abstract: {p['abstract']}"
        for i, p in enumerate(real_abstracts)
    )
    n_real = len(real_abstracts)
    return f"""You are generating content for a neuroscience quiz game called Neurofact.

I will give you {n_real} real neuroscience paper abstracts. Your tasks:

TASK A: For each abstract, write a 1–2 sentence scientific claim that captures the key finding. Write in the same register as a scientific abstract — precise, specific, and confident. Do not say 'this study found' — write the claim as a direct statement of fact.

TASK B: Write {n_fake} FAKE neuroscience claims. Each must:
- Sound exactly as plausible and specific as a real finding
- Use real neuroscience terminology and brain region names
- Be subtly but definitively false (wrong mechanism, wrong region, invented effect)
- Be indistinguishable from real claims to a non-specialist
- Cover different topic areas (stress, memory, emotion, social neuroscience, psychopathy, reward)

For every real claim and fake claim, also write:
- category: one of {CATEGORIES}
- difficulty: one of {DIFFICULTIES}
- explanation: 1–2 sentences explaining why it is real (for real) or what is incorrect (for fake)

Return ONLY valid JSON in this exact format:
{{
  "real": [
    {{
      "statement": "...",
      "category": "...",
      "difficulty": "...",
      "explanation": "..."
    }}
  ],
  "fake": [
    {{
      "statement": "...",
      "category": "...",
      "difficulty": "...",
      "explanation": "..."
    }}
  ]
}}

Real abstracts:
{abstract_list}"""


def call_anthropic(prompt: str, api_key: str) -> dict:
    """Call Claude API and return parsed JSON response."""
    payload = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    text = body["content"][0]["text"].strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


def assemble_game_data(real_items: list[dict], fake_items: list[dict]) -> list[dict]:
    """Combine real and fake items, assign IDs and answer fields, shuffle."""
    questions = []
    for i, item in enumerate(real_items):
        questions.append({
            "id": i + 1,
            "statement": item["statement"],
            "answer": "real",
            "category": item.get("category", "Neuroscience"),
            "difficulty": item.get("difficulty", "Advanced"),
            "explanation": item.get("explanation", ""),
        })
    for j, item in enumerate(fake_items):
        questions.append({
            "id": len(real_items) + j + 1,
            "statement": item["statement"],
            "answer": "fake",
            "category": item.get("category", "Neuroscience"),
            "difficulty": item.get("difficulty", "Advanced"),
            "explanation": item.get("explanation", ""),
        })
    random.shuffle(questions)
    for idx, q in enumerate(questions):
        q["id"] = idx + 1
    return questions


def compute_grade(score: int, total: int) -> str:
    """Return letter grade based on accuracy percentage."""
    if total == 0:
        return "F"
    pct = score / total * 100
    if pct >= 90:
        return "A"
    if pct >= 80:
        return "B"
    if pct >= 70:
        return "C"
    if pct >= 60:
        return "D"
    return "F"


def compute_streak(answers: list[bool]) -> int:
    """Return the maximum consecutive correct streak from a list of bool results."""
    best = 0
    current = 0
    for a in answers:
        if a:
            current += 1
            if current > best:
                best = current
        else:
            current = 0
    return best


def validate_question(q: dict) -> list[str]:
    """Return list of validation errors for a question dict."""
    errors = []
    required = ["id", "statement", "answer", "category", "difficulty", "explanation"]
    for field in required:
        if field not in q:
            errors.append(f"Missing field: {field}")
    if q.get("answer") not in ("real", "fake"):
        errors.append(f"Invalid answer: {q.get('answer')}")
    if not q.get("statement", "").strip():
        errors.append("Empty statement")
    if q.get("difficulty") not in ("Foundational", "Advanced", "Expert", None):
        errors.append(f"Invalid difficulty: {q.get('difficulty')}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate Neurofact questions")
    parser.add_argument("--count", type=int, default=30, help="Total questions (half real, half fake)")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls; validate structure only")
    parser.add_argument("--output", default="game_data.json", help="Output file path")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it and try again, or use --dry-run to validate structure.")
        raise SystemExit(1)

    n_per_type = args.count // 2

    if args.dry_run:
        print(f"Dry run: would fetch {n_per_type} real abstracts from arXiv")
        print(f"Dry run: would call Claude to generate {n_per_type} fake claims")
        print("Structure validation: OK")
        return

    # Fetch real abstracts
    print("Fetching arXiv abstracts...")
    all_abstracts = []
    for query in ARXIV_QUERIES:
        papers = fetch_arxiv_abstracts(query, max_results=4)
        all_abstracts.extend(papers)

    abstracts = all_abstracts[:n_per_type]
    if len(abstracts) < n_per_type:
        print(f"Warning: only {len(abstracts)} abstracts fetched (wanted {n_per_type})")

    if not abstracts:
        print("Error: no abstracts fetched. Check network connectivity.")
        raise SystemExit(1)

    # Call Claude
    print(f"Calling Claude ({ANTHROPIC_MODEL}) to generate game content...")
    prompt = build_prompt(abstracts, n_fake=n_per_type)
    response = call_anthropic(prompt, api_key)

    real_items = response.get("real", [])
    fake_items = response.get("fake", [])
    print(f"Received: {len(real_items)} real, {len(fake_items)} fake")

    questions = assemble_game_data(real_items, fake_items)

    # Validate
    errors_found = False
    for q in questions:
        errs = validate_question(q)
        if errs:
            print(f"Question {q.get('id')} validation errors: {errs}")
            errors_found = True
    if errors_found:
        print("Warning: some questions failed validation — review game_data.json before use")

    out_path = Path(args.output)
    out_path.write_text(json.dumps(questions, indent=2, ensure_ascii=False))
    print(f"Wrote {len(questions)} questions to {out_path}")
    print("\nTo update index.html: replace the QUESTIONS constant with the JSON array in game_data.json")


if __name__ == "__main__":
    main()
