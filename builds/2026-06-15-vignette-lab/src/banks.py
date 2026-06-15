"""Scenario element banks for combinatorial vignette generation."""

from __future__ import annotations

CHARACTERS: list[dict] = [
    {"name": "Alex",    "age": 24, "role": "undergraduate student",  "pronoun_sub": "they",  "pronoun_obj": "them",  "pronoun_pos": "their"},
    {"name": "Jordan",  "age": 29, "role": "graduate student",       "pronoun_sub": "they",  "pronoun_obj": "them",  "pronoun_pos": "their"},
    {"name": "Morgan",  "age": 34, "role": "research assistant",      "pronoun_sub": "they",  "pronoun_obj": "them",  "pronoun_pos": "their"},
    {"name": "Sarah",   "age": 31, "role": "project manager",         "pronoun_sub": "she",   "pronoun_obj": "her",   "pronoun_pos": "her"},
    {"name": "Marcus",  "age": 27, "role": "software developer",      "pronoun_sub": "he",    "pronoun_obj": "him",   "pronoun_pos": "his"},
    {"name": "Priya",   "age": 38, "role": "clinical psychologist",   "pronoun_sub": "she",   "pronoun_obj": "her",   "pronoun_pos": "her"},
    {"name": "Devon",   "age": 22, "role": "college freshman",        "pronoun_sub": "they",  "pronoun_obj": "them",  "pronoun_pos": "their"},
    {"name": "Lisa",    "age": 45, "role": "high school teacher",     "pronoun_sub": "she",   "pronoun_obj": "her",   "pronoun_pos": "her"},
    {"name": "Tom",     "age": 52, "role": "factory supervisor",      "pronoun_sub": "he",    "pronoun_obj": "him",   "pronoun_pos": "his"},
    {"name": "Yuki",    "age": 26, "role": "medical resident",        "pronoun_sub": "she",   "pronoun_obj": "her",   "pronoun_pos": "her"},
]

# ---------------------------------------------------------------------------
# STRESS THEME
# ---------------------------------------------------------------------------

STRESS_SETTINGS: list[str] = [
    "at their desk in a busy open-plan office with colleagues nearby",
    "in the library an hour before a major exam",
    "in a hospital waiting room after receiving an unexpected diagnosis",
    "at home late at night after a difficult phone call with family",
    "standing outside a job interview, moments before it begins",
    "in their car in a parking lot, having just received bad financial news",
]

STRESS_EVENTS: list[str] = [
    "{pronoun_pos} supervisor unexpectedly criticised {pronoun_pos} work in front of the entire team",
    "{pronoun_sub} was told {pronoun_pos} funding application had been rejected without explanation",
    "a close colleague resigned suddenly, leaving {pronoun_obj} responsible for a project {pronoun_sub} was not prepared for",
    "{pronoun_sub} received a message saying {pronoun_pos} rent would increase by 25% with two weeks' notice",
    "a technical failure destroyed three months of {pronoun_pos} work with no backup",
    "{pronoun_sub} learned a major presentation had been moved up by two days",
    "a trusted mentor delivered harsh criticism on a piece of work {pronoun_sub} had spent weeks on",
    "{pronoun_sub} missed a critical deadline due to a misunderstanding, with significant consequences",
]

STRESS_CHECKS: list[str] = [
    "How stressed does {name} feel right now, on a scale from 1 (not at all) to 7 (extremely)?",
    "To what extent is {name} experiencing a sense of threat or pressure in this moment?",
    "How difficult would it be for {name} to concentrate on something unrelated right now?",
    "How much is {name} worried about what will happen next?",
]

STRESS_PROMPTS: list[str] = [
    "If you were in {name}'s situation right now, how would you feel and what would your first instinct be?",
    "What thoughts do you think are going through {name}'s mind at this moment?",
    "Describe two things {name} might do in the next few minutes to cope with this situation.",
    "How would you rate the severity of {name}'s stressor, and why?",
]

STRESS_NOTE = (
    "Designed to elicit moderate-to-high acute stress. Validate with a self-report measure "
    "(e.g., VAS stress item or STAI-state) immediately after presentation. Stressor involves "
    "social-evaluative threat and/or loss of control — two factors reliably associated with "
    "cortisol reactivity."
)

# ---------------------------------------------------------------------------
# EMPATHY THEME
# ---------------------------------------------------------------------------

EMPATHY_SETTINGS: list[str] = [
    "on a crowded bus during rush hour",
    "in a coffee shop, overhearing a conversation at the next table",
    "in the hallway outside a lecture room after class",
    "at a community event in a local park",
    "in a grocery store checkout line",
    "in the break room at work",
]

EMPATHY_EVENTS: list[str] = [
    "{pronoun_sub} noticed a stranger quietly crying, trying not to draw attention to themselves",
    "{pronoun_sub} overheard a young person on the phone, clearly distressed and saying they had nowhere to go",
    "{pronoun_sub} watched a person drop their groceries and struggle to pick them up, looking embarrassed",
    "{pronoun_sub} observed a colleague being publicly humiliated by a supervisor while others looked away",
    "{pronoun_sub} saw an elderly person fall and struggle to stand while bystanders hesitated",
    "{pronoun_sub} witnessed a child become separated from their caregiver and start to panic",
    "{pronoun_sub} heard a classmate tell a friend they had just failed a course for the second time",
    "{pronoun_sub} noticed a co-worker sitting alone and visibly upset after a meeting ended",
]

EMPATHY_CHECKS: list[str] = [
    "To what extent does {name} feel what the other person is feeling, on a scale from 1 (not at all) to 7 (very strongly)?",
    "How motivated does {name} feel to help the other person?",
    "How much distress is {name} experiencing on behalf of the other person?",
    "How accurately do you think {name} understands what the other person is going through?",
]

EMPATHY_PROMPTS: list[str] = [
    "What do you think {name} is experiencing emotionally in this moment, and why?",
    "What factors might make it easier or harder for {name} to feel empathy here?",
    "Describe what {name} might do next, and what would drive that decision.",
    "Is {name} experiencing empathic concern, personal distress, or both? Explain your reasoning.",
]

EMPATHY_NOTE = (
    "Designed to activate empathic concern and perspective-taking. Useful for distinguishing "
    "affective empathy (feeling another's emotion) from cognitive empathy (understanding it). "
    "Vary the salience of the target person's distress across conditions to examine thresholds "
    "for empathic response."
)

# ---------------------------------------------------------------------------
# MORAL THEME
# ---------------------------------------------------------------------------

MORAL_SETTINGS: list[str] = [
    "at their desk at the end of a long workday",
    "in the university library between classes",
    "at home alone on a quiet evening",
    "in a coffee shop checking their phone",
    "in a hospital break room during a shift",
    "waiting in line at a store checkout",
]

MORAL_EVENTS: list[str] = [
    "{pronoun_sub} realised {pronoun_sub} had been given too much change by mistake, but the cashier had already moved on",
    "{pronoun_sub} found a wallet containing a significant amount of cash and no ID",
    "{pronoun_sub} overheard {pronoun_pos} manager making a discriminatory comment to a colleague",
    "{pronoun_sub} discovered that a co-worker had falsified data in a report that had already been submitted",
    "{pronoun_sub} was asked by a friend to provide an alibi for something {pronoun_sub} was uncertain about",
    "{pronoun_sub} found evidence that a classmate had plagiarised an assignment — and was awarded the top grade",
    "{pronoun_sub} witnessed a minor accident caused by another person, who then left the scene",
    "{pronoun_sub} received confidential information by mistake that would benefit {pronoun_pos} own interests",
]

MORAL_CHECKS: list[str] = [
    "How morally wrong does {name} believe the situation is, on a scale from 1 (not at all) to 7 (extremely)?",
    "How personally responsible does {name} feel to do something about this?",
    "How much guilt or discomfort is {name} experiencing right now?",
    "How difficult does {name} find it to know what the right thing to do is?",
]

MORAL_PROMPTS: list[str] = [
    "What do you think {name} should do, and what makes this difficult?",
    "What factors are likely pulling {name} toward action versus inaction?",
    "What would most people do in {name}'s position — and what should they do? Are these different?",
    "Identify the competing moral obligations {name} faces in this situation.",
]

MORAL_NOTE = (
    "Designed to elicit moral discomfort and activate competing normative frameworks "
    "(deontological vs. consequentialist). Useful for studies on moral judgment, "
    "bystander intervention, and ethical decision-making. Intensity of the moral violation "
    "can be calibrated by varying the stakes described in the event text."
)

# ---------------------------------------------------------------------------
# Theme registry
# ---------------------------------------------------------------------------

THEMES: dict[str, dict] = {
    "stress": {
        "settings":  STRESS_SETTINGS,
        "events":    STRESS_EVENTS,
        "checks":    STRESS_CHECKS,
        "prompts":   STRESS_PROMPTS,
        "note":      STRESS_NOTE,
        "label":     "Acute Stress Induction",
        "description": (
            "Scenarios in which the protagonist faces an unexpected, uncontrollable stressor "
            "involving social-evaluative threat or loss of resources."
        ),
    },
    "empathy": {
        "settings":  EMPATHY_SETTINGS,
        "events":    EMPATHY_EVENTS,
        "checks":    EMPATHY_CHECKS,
        "prompts":   EMPATHY_PROMPTS,
        "note":      EMPATHY_NOTE,
        "label":     "Empathy Elicitation",
        "description": (
            "Scenarios in which the protagonist witnesses another person in distress, "
            "activating perspective-taking and empathic concern."
        ),
    },
    "moral": {
        "settings":  MORAL_SETTINGS,
        "events":    MORAL_EVENTS,
        "checks":    MORAL_CHECKS,
        "prompts":   MORAL_PROMPTS,
        "note":      MORAL_NOTE,
        "label":     "Moral Dilemma",
        "description": (
            "Scenarios in which the protagonist discovers an ethical violation or faces "
            "a situation requiring a morally-loaded decision."
        ),
    },
}
