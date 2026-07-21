"""Hand-curated taxonomy of stress/empathy/psychopathy neuroscience concepts
and everyday-domain analogs, plus the structural-mapping compatibility engine
that decides which concept/domain pairs are valid to generate an analogy for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Optional

MECHANISM_TYPES = (
    "threshold_trigger",
    "feedback_loop",
    "resource_depletion",
    "contagion_mirroring",
    "calibration_regulation",
    "dual_pathway",
    "learned_pattern",
)

SUBDOMAINS = ("stress", "empathy", "psychopathy")

AUDIENCES = ("undergrad_lecture", "public_talk", "book_chapter")


@dataclass(frozen=True)
class Concept:
    id: str
    name: str
    subdomain: str
    mechanism_type: str
    trigger: str
    mechanism: str
    consequence: str
    caveat: str
    description: str

    def __post_init__(self) -> None:
        if self.subdomain not in SUBDOMAINS:
            raise ValueError(f"Unknown subdomain '{self.subdomain}' for concept '{self.id}'")
        if self.mechanism_type not in MECHANISM_TYPES:
            raise ValueError(f"Unknown mechanism_type '{self.mechanism_type}' for concept '{self.id}'")


@dataclass(frozen=True)
class Domain:
    id: str
    name: str
    mechanism_types: tuple
    trigger_word: str
    process_word: str
    outcome_word: str
    description: str

    def __post_init__(self) -> None:
        unknown = set(self.mechanism_types) - set(MECHANISM_TYPES)
        if unknown:
            raise ValueError(f"Unknown mechanism_types {unknown} for domain '{self.id}'")
        if not self.mechanism_types:
            raise ValueError(f"Domain '{self.id}' has no mechanism_types")


CONCEPTS: tuple = (
    Concept(
        id="hpa_axis_response",
        name="The HPA Axis Stress Response",
        subdomain="stress",
        mechanism_type="threshold_trigger",
        trigger="a perceived threat crosses the brain's danger threshold",
        mechanism="the hypothalamus signals the pituitary, which signals the adrenal glands to release cortisol",
        consequence="the body shifts into a heightened, resource-mobilizing state within minutes",
        caveat="the same cascade that saves you from a genuine threat also fires for threats that are only perceived, which is where chronic activation becomes a problem",
        description="The hypothalamic-pituitary-adrenal (HPA) axis: the body's central hormonal stress-response pathway.",
    ),
    Concept(
        id="allostatic_load",
        name="Allostatic Load",
        subdomain="stress",
        mechanism_type="resource_depletion",
        trigger="stress responses are repeated or prolonged without adequate recovery",
        mechanism="the physiological systems that normally return to baseline start running above it, and repair capacity is drawn down faster than it is replenished",
        consequence="cumulative wear appears across cardiovascular, metabolic, and immune systems, even without any single acute event",
        caveat="allostatic load is a population-level, cumulative construct — it explains long-run risk, not any single person's health on any single day",
        description="Allostatic load: the cumulative physiological cost of chronic or repeated stress-system activation.",
    ),
    Concept(
        id="cognitive_appraisal",
        name="Cognitive Appraisal",
        subdomain="stress",
        mechanism_type="dual_pathway",
        trigger="an event occurs that could plausibly be stressful",
        mechanism="a fast primary appraisal ('is this a threat?') is followed by a slower secondary appraisal ('do I have the resources to cope?')",
        consequence="the same objective event produces a stress response in one person and not in another, depending on how it is appraised",
        caveat="appraisal happens fast and often outside awareness, so 'just think about it differently' understates how automatic the first pass really is",
        description="Lazarus's two-stage cognitive appraisal model: threat assessment followed by a coping-resource assessment.",
    ),
    Concept(
        id="fight_flight_freeze",
        name="Fight-Flight-Freeze",
        subdomain="stress",
        mechanism_type="threshold_trigger",
        trigger="an acute threat is detected",
        mechanism="the sympathetic nervous system triggers one of several fast, largely involuntary defensive modes",
        consequence="attention narrows, energy mobilizes, and behavior shifts toward confrontation, escape, or immobility before conscious deliberation catches up",
        caveat="freeze is a real, involuntary defensive state, not passivity or consent — it is often the least understood of the three",
        description="The fight-flight-freeze response: the nervous system's fast, largely involuntary menu of defensive reactions to acute threat.",
    ),
    Concept(
        id="cortisol_feedback_loop",
        name="The Cortisol Feedback Loop",
        subdomain="stress",
        mechanism_type="feedback_loop",
        trigger="cortisol rises during a stress response",
        mechanism="cortisol binds receptors in the hippocampus and hypothalamus that normally signal the HPA axis to quiet back down",
        consequence="under chronic stress this shutoff signal weakens, and cortisol stays elevated longer than a single stressor would justify",
        caveat="this is a negative feedback loop that can itself become damaged by the very stress it is supposed to regulate",
        description="The cortisol negative feedback loop: the brain's built-in mechanism for turning the stress response back off.",
    ),
    Concept(
        id="learned_helplessness",
        name="Learned Helplessness",
        subdomain="stress",
        mechanism_type="learned_pattern",
        trigger="repeated exposure to uncontrollable, unavoidable stress",
        mechanism="the system learns that effort does not change the outcome, and that association generalizes to new situations where control is actually possible",
        consequence="an organism stops attempting to escape or improve a situation even when an exit now exists",
        caveat="this is a learned association, not a fixed trait — the same mechanism that installs it can be used to unlearn it with a genuinely controllable experience",
        description="Learned helplessness: a learned expectation of no control that persists even after control becomes available again.",
    ),
    Concept(
        id="stress_inoculation",
        name="Stress Inoculation",
        subdomain="stress",
        mechanism_type="calibration_regulation",
        trigger="manageable, graded stress is experienced with support and recovery time",
        mechanism="the stress-response system is exercised at a dose it can handle and adapts, the way a muscle adapts to graded load",
        consequence="future stressors of similar type are met with a faster, better-regulated response instead of an overwhelmed one",
        caveat="the operative word is 'manageable' — the same exposure without adequate support or recovery produces sensitization instead of inoculation",
        description="Stress inoculation: building resilience to future stress through graded, manageable exposure with recovery, not avoidance.",
    ),
    Concept(
        id="allostasis_vs_homeostasis",
        name="Allostasis",
        subdomain="stress",
        mechanism_type="calibration_regulation",
        trigger="the body anticipates a demand before it fully arrives",
        mechanism="instead of holding one fixed setpoint the way homeostasis does, allostatic systems predictively shift the setpoint itself to match anticipated demand",
        consequence="the body can be 'ready' for a stressor in advance, at the cost of running some systems above their resting baseline",
        caveat="allostasis is adaptive by design; it becomes allostatic load specifically when the anticipatory shifting never gets to stand down",
        description="Allostasis: stability achieved through predictive change, as distinct from homeostasis's stability through a fixed setpoint.",
    ),
    Concept(
        id="vagal_tone_polyvagal",
        name="Vagal Tone (Polyvagal Theory)",
        subdomain="stress",
        mechanism_type="calibration_regulation",
        trigger="the environment is read as safe, dangerous, or life-threatening",
        mechanism="the vagus nerve's regulatory tone shifts the autonomic nervous system between social-engagement, mobilization, and shutdown states",
        consequence="the same person can move between calm connection and defensive activation without a new external event, just a change in perceived safety",
        caveat="polyvagal theory is influential in clinical practice but its specific neuroanatomical claims are actively debated among researchers — treat it as a useful clinical heuristic, not settled neuroanatomy",
        description="Polyvagal theory: a framework for how vagal tone shifts the nervous system among social-engagement, mobilization, and shutdown states.",
    ),
    Concept(
        id="amygdala_hijack",
        name="The Amygdala's Fast Pathway",
        subdomain="stress",
        mechanism_type="threshold_trigger",
        trigger="an emotionally intense stimulus arrives faster than the prefrontal cortex can evaluate it",
        mechanism="the amygdala triggers a defensive response via a fast subcortical route before the slower cortical route finishes its analysis",
        consequence="a person reacts intensely to something before they can consciously explain why",
        caveat="'hijack' is a popular-science shorthand for a fast subcortical pathway, not evidence that the amygdala overrides a healthy prefrontal cortex against its will",
        description="The amygdala's fast subcortical threat-detection pathway, popularly called an 'amygdala hijack.'",
    ),
    Concept(
        id="affective_cognitive_empathy",
        name="Affective vs. Cognitive Empathy",
        subdomain="empathy",
        mechanism_type="dual_pathway",
        trigger="another person's emotional state becomes observable",
        mechanism="a fast affective pathway shares the feeling automatically, while a slower cognitive pathway explicitly reasons about their mental state",
        consequence="someone can feel what another person feels without accurately understanding why, or the reverse",
        caveat="the two pathways are dissociable — clinical populations exist with intact cognitive empathy but reduced affective empathy, and the reverse",
        description="The affective/cognitive empathy distinction: feeling what someone feels versus understanding their mental state.",
    ),
    Concept(
        id="emotional_contagion",
        name="Emotional Contagion",
        subdomain="empathy",
        mechanism_type="contagion_mirroring",
        trigger="someone nearby expresses a strong emotion",
        mechanism="the observer's own emotional and physiological state shifts toward the expressed emotion, largely automatically",
        consequence="moods spread through a room, a team, or a family faster than any explicit communication about why",
        caveat="contagion is largely automatic and can happen without the observer even correctly identifying which emotion is spreading",
        description="Emotional contagion: the largely automatic tendency to catch and mirror the emotional states of people around you.",
    ),
    Concept(
        id="mirror_neuron_simulation",
        name="Mirror-Neuron Simulation",
        subdomain="empathy",
        mechanism_type="contagion_mirroring",
        trigger="you observe someone perform an action or express an emotion",
        mechanism="overlapping neural populations activate whether you do the action or feeling yourself or merely watch someone else do it",
        consequence="watching provides a partial internal simulation of the observed state, which is part of how understanding others feels immediate rather than inferred",
        caveat="the strong 'mirror neurons explain empathy' claim popularized in the 2000s has been significantly walked back — treat this as one contributing mechanism among several, not the whole explanation",
        description="Mirror-neuron-based simulation: partial neural overlap between performing or feeling something and observing someone else do it.",
    ),
    Concept(
        id="empathic_accuracy",
        name="Empathic Accuracy",
        subdomain="empathy",
        mechanism_type="calibration_regulation",
        trigger="you try to infer specifically what another person is thinking or feeling",
        mechanism="accuracy depends on correctly weighting context, expression, and prior knowledge of the person, and can be miscalibrated by projecting your own state onto them",
        consequence="people are more accurate about strangers' broad emotions than about close others' specific thoughts, because familiarity breeds overconfidence, not just accuracy",
        caveat="confidence and accuracy are only weakly correlated in empathic judgments — feeling certain you understand someone is not evidence that you do",
        description="Empathic accuracy: how correctly one infers another person's actual thoughts and feelings, as distinct from how confident one feels doing it.",
    ),
    Concept(
        id="empathy_fatigue",
        name="Empathy (Compassion) Fatigue",
        subdomain="empathy",
        mechanism_type="resource_depletion",
        trigger="sustained, repeated exposure to others' distress, especially in caregiving or clinical roles",
        mechanism="the affective-sharing system that makes empathy possible is engaged so continuously that its regulatory capacity is drawn down",
        consequence="empathic responsiveness drops, sometimes alongside emotional exhaustion, as a protective downshift rather than a character flaw",
        caveat="this is a regulatory-capacity problem, best addressed with structural recovery time, not a motivational failure to be argued out of with willpower",
        description="Empathy (compassion) fatigue: depletion of empathic capacity from sustained exposure to others' suffering.",
    ),
    Concept(
        id="perspective_taking",
        name="Perspective-Taking",
        subdomain="empathy",
        mechanism_type="dual_pathway",
        trigger="you need to predict or explain someone else's behavior",
        mechanism="a deliberate, effortful simulation of the other person's beliefs, knowledge, and viewpoint, distinct from simply sharing their feeling",
        consequence="accurate prediction of behavior improves, even in the complete absence of any emotional sharing",
        caveat="perspective-taking is cognitively effortful and depletes with fatigue, time pressure, and cognitive load — it degrades before affective empathy typically does",
        description="Perspective-taking (theory of mind): deliberately modeling another person's beliefs and viewpoint, distinct from feeling what they feel.",
    ),
    Concept(
        id="callous_unemotional_traits",
        name="Callous-Unemotional Traits",
        subdomain="psychopathy",
        mechanism_type="calibration_regulation",
        trigger="a situation that would normally elicit an empathic or guilt response in most people",
        mechanism="reduced responsiveness in the neural circuitry that normally generates affective empathy and guilt, while cognitive empathy often remains largely intact",
        consequence="behavior can be selectively unmoved by others' distress in a specific way, rather than a general deficit in understanding people",
        caveat="callous-unemotional traits are a dimensional, population-distributed research construct measured on a continuum, not a categorical label that applies cleanly to any one individual from a single behavior",
        description="Callous-unemotional (CU) traits: reduced affective empathy and guilt responsiveness with cognitive understanding of others often intact.",
    ),
    Concept(
        id="threat_processing_hyporeactivity",
        name="Threat-Processing Hyporeactivity",
        subdomain="psychopathy",
        mechanism_type="threshold_trigger",
        trigger="a cue that would normally register as fearful or threatening to most observers",
        mechanism="reduced amygdala reactivity raises the threshold at which fear and distress cues are registered as significant",
        consequence="responses to others' fear expressions and to personal risk are both blunted relative to typical reactivity",
        caveat="this describes a statistical shift in threshold across a research sample, not a deterministic prediction about any specific individual's behavior",
        description="Threat-processing hyporeactivity: a research finding of reduced amygdala responsiveness to fear/threat cues associated with psychopathic traits.",
    ),
    Concept(
        id="instrumental_reactive_aggression",
        name="Instrumental vs. Reactive Aggression",
        subdomain="psychopathy",
        mechanism_type="dual_pathway",
        trigger="a provocation, or a goal that aggression would serve",
        mechanism="two distinct routes to aggressive behavior exist — one driven by emotional escalation in response to provocation, one driven by cold, goal-directed calculation independent of provocation",
        consequence="the same aggressive act can arise from very different underlying processes, which matters enormously for prediction and intervention",
        caveat="most real-world aggression involves both pathways to varying degrees — cleanly 'pure instrumental' cases are rarer than the dichotomy suggests",
        description="The instrumental/reactive aggression distinction: goal-directed, low-arousal aggression versus provoked, high-arousal aggression.",
    ),
    Concept(
        id="reward_hypersensitivity",
        name="Reward Hypersensitivity",
        subdomain="psychopathy",
        mechanism_type="threshold_trigger",
        trigger="a cue signals potential reward is available",
        mechanism="an attentional and motivational bias toward reward pursuit that is disproportionately strong relative to competing threat or punishment signals",
        consequence="reward-seeking behavior continues even as punishment cues that would deter most people accumulate",
        caveat="this reflects a relative imbalance between reward- and punishment-sensitivity systems, not an absence of punishment sensitivity altogether",
        description="Reward hypersensitivity: a disproportionately strong pull toward reward cues relative to competing punishment/threat signals.",
    ),
)

DOMAINS: tuple = (
    Domain(
        id="kitchen",
        name="The Kitchen Stove",
        mechanism_types=("threshold_trigger", "resource_depletion", "calibration_regulation"),
        trigger_word="the burner is turned up past a certain point",
        process_word="heat builds in the pan faster than it can dissipate",
        outcome_word="the dish boils over or scorches",
        description="Cooking on a stove: heat thresholds, ingredient depletion, and a cook's calibration of temperature to the dish.",
    ),
    Domain(
        id="weather_storm",
        name="A Building Storm",
        mechanism_types=("threshold_trigger", "feedback_loop"),
        trigger_word="warm, moist air rises past a stability threshold",
        process_word="the storm feeds itself, drawing in more warm air as it intensifies",
        outcome_word="conditions escalate quickly once the threshold is crossed, then eventually discharge and calm",
        description="A developing thunderstorm: a threshold-crossing trigger followed by a self-reinforcing feedback loop.",
    ),
    Domain(
        id="thermostat",
        name="A Home Thermostat",
        mechanism_types=("feedback_loop", "calibration_regulation"),
        trigger_word="the room drifts away from its setpoint",
        process_word="a sensor detects the drift and signals the furnace or air conditioner to correct it",
        outcome_word="the system returns to setpoint, until the next drift starts the loop again",
        description="A home thermostat: continuous sensing and correction around a target setpoint.",
    ),
    Domain(
        id="athletic_training",
        name="Athletic Training Load",
        mechanism_types=("resource_depletion", "calibration_regulation", "threshold_trigger"),
        trigger_word="training volume crosses what the body has recovered capacity for",
        process_word="recovery systems are drawn down faster than they rebuild",
        outcome_word="performance improves with graded load and rest, but overuse injury or burnout follows load without recovery",
        description="Athletic training load: the balance between stress and recovery that either builds capacity or depletes it.",
    ),
    Domain(
        id="traffic_driving",
        name="Merging Into Traffic",
        mechanism_types=("threshold_trigger", "dual_pathway"),
        trigger_word="a gap in traffic appears",
        process_word="a fast reflexive check for immediate danger runs alongside a slower, deliberate judgment of whether the gap is really big enough",
        outcome_word="the merge happens smoothly, or a near-miss occurs, depending on which judgment dominated",
        description="Merging into highway traffic: fast reflexive threat-checking running alongside slower deliberate judgment.",
    ),
    Domain(
        id="garden",
        name="A Garden Over a Season",
        mechanism_types=("resource_depletion", "learned_pattern", "calibration_regulation"),
        trigger_word="the same bed is planted the same way season after season",
        process_word="nutrients are drawn down each cycle while a gardener's technique adjusts based on what worked and failed before",
        outcome_word="yield either improves as technique is calibrated by experience, or declines as depletion outpaces replenishment",
        description="A garden across seasons: nutrient depletion, learned technique, and calibrated care compounding over repeated cycles.",
    ),
    Domain(
        id="orchestra_music",
        name="An Orchestra Tuning Up",
        mechanism_types=("contagion_mirroring", "calibration_regulation"),
        trigger_word="one section's tempo or dynamic shifts",
        process_word="nearby musicians unconsciously adjust to match, section by section",
        outcome_word="the whole orchestra converges on a shared tempo and volume without anyone giving an explicit command",
        description="An orchestra tuning and playing together: how tempo and dynamics spread and synchronize player to player.",
    ),
    Domain(
        id="stadium_wave",
        name="A Stadium Wave",
        mechanism_types=("contagion_mirroring", "threshold_trigger"),
        trigger_word="enough nearby spectators stand and raise their arms to cross a visible threshold",
        process_word="each adjacent section mirrors the section before it with almost no delay",
        outcome_word="a wave of motion propagates around the stadium that no single person is steering",
        description="A stadium wave: individually automatic mirroring that produces coordinated group behavior with no central controller.",
    ),
    Domain(
        id="computer_network",
        name="A Congested Network",
        mechanism_types=("feedback_loop", "threshold_trigger", "dual_pathway"),
        trigger_word="traffic on the link crosses its capacity threshold",
        process_word="a fast automatic congestion-control response kicks in while a slower monitoring process decides whether to reroute",
        outcome_word="packets queue or drop until the fast and slow responses bring load back under the threshold",
        description="A congested computer network: automatic threshold-triggered throttling alongside slower deliberate rerouting decisions.",
    ),
    Domain(
        id="smoke_alarm",
        name="A Smoke Alarm",
        mechanism_types=("threshold_trigger", "calibration_regulation"),
        trigger_word="particle density in the air crosses the sensor's set threshold",
        process_word="the alarm fires immediately and indiscriminately, whether the source is a fire or just burnt toast",
        outcome_word="a well-calibrated sensor catches real fires without constant false alarms, while a miscalibrated one does neither reliably",
        description="A smoke alarm: a fixed detection threshold that trades false alarms against missed real danger depending on calibration.",
    ),
    Domain(
        id="dam_reservoir",
        name="A Reservoir Behind a Dam",
        mechanism_types=("resource_depletion", "feedback_loop"),
        trigger_word="outflow consistently exceeds inflow",
        process_word="reserve capacity drops, and the dam's operators adjust outflow policy in response to the falling level",
        outcome_word="the reservoir stabilizes at a new, lower equilibrium, or keeps declining if the adjustment comes too late",
        description="A reservoir behind a dam: reserves drawn down by sustained outflow, regulated by a feedback response to falling levels.",
    ),
    Domain(
        id="phone_battery",
        name="A Phone Battery",
        mechanism_types=("resource_depletion", "calibration_regulation"),
        trigger_word="background processes keep running without being closed",
        process_word="charge is drawn down faster than the user notices, because no single process looks expensive on its own",
        outcome_word="the phone dies earlier than expected unless usage is calibrated to known drains",
        description="A phone battery drained by background processes: depletion that is invisible moment-to-moment but adds up.",
    ),
)

CONCEPTS_BY_ID = {c.id: c for c in CONCEPTS}
DOMAINS_BY_ID = {d.id: d for d in DOMAINS}


def get_concept(concept_id: str) -> Optional[Concept]:
    return CONCEPTS_BY_ID.get(concept_id)


def get_domain(domain_id: str) -> Optional[Domain]:
    return DOMAINS_BY_ID.get(domain_id)


def is_compatible(concept: Concept, domain: Domain) -> bool:
    return concept.mechanism_type in domain.mechanism_types


def valid_pairs(
    concept_id: Optional[str] = None,
    domain_id: Optional[str] = None,
) -> list:
    """Return all (Concept, Domain) pairs whose mechanism types are compatible,
    optionally filtered to a single concept and/or domain."""
    concepts = [CONCEPTS_BY_ID[concept_id]] if concept_id else list(CONCEPTS)
    domains = [DOMAINS_BY_ID[domain_id]] if domain_id else list(DOMAINS)
    return [(c, d) for c, d in product(concepts, domains) if is_compatible(c, d)]


def valid_triples(
    concept_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    audience: Optional[str] = None,
) -> list:
    """Return all (Concept, Domain, audience) triples, optionally filtered."""
    pairs = valid_pairs(concept_id, domain_id)
    audiences = (audience,) if audience else AUDIENCES
    return [(c, d, a) for c, d in pairs for a in audiences]
