// Confound Hunter — vignette and flaw-taxonomy data.
// Classic script (no ES modules) so the game opens directly via file://.

var FLAW_ORDER = [
  'confound', 'selection', 'no_control', 'demand', 'ceiling',
  'regression', 'corr_causation', 'underpowered', 'blinding', 'generalization'
];

var FLAW_TYPES = {
  confound: {
    name: 'Uncontrolled Confound',
    description: 'A third variable — tied to how the study was run, not who was in it — changes right along with the manipulation and could explain the result instead.'
  },
  selection: {
    name: 'Selection Bias',
    description: 'The comparison groups were formed by self-selection or pre-existing membership rather than random assignment, so they may have differed before the study even began.'
  },
  no_control: {
    name: 'No Control Group',
    description: 'There is nothing to compare the treated group against, so there is no way to tell whether the outcome would have happened anyway.'
  },
  demand: {
    name: 'Demand Characteristics',
    description: 'Participants or researchers picked up on the study’s hypothesis and responded to what they thought was expected, rather than responding naturally.'
  },
  ceiling: {
    name: 'Ceiling / Floor Effect',
    description: 'Scores were bunched at the top or bottom of the measurement scale, leaving no room to detect a real difference.'
  },
  regression: {
    name: 'Regression to the Mean',
    description: 'A group was selected because of an extreme score, which naturally drifts back toward average on retest — a statistical inevitability, not necessarily a treatment effect.'
  },
  corr_causation: {
    name: 'Correlation ≠ Causation',
    description: 'Two variables move together in purely observational data, but that alone doesn’t establish that one causes the other.'
  },
  underpowered: {
    name: 'Underpowered Sample',
    description: 'The sample is too small to reliably detect an effect of the size being claimed.'
  },
  blinding: {
    name: 'Lack of Blinding',
    description: 'Someone who knows the group assignment — a participant or a rater — is in a position to (consciously or not) bias the outcome.'
  },
  generalization: {
    name: 'Overgeneralization',
    description: 'The sample is narrow or unusual, but the conclusion is stated as if it applies to a much broader population.'
  }
};

function opt(correct, d1, d2, d3, position) {
  var others = [d1, d2, d3];
  var out = [];
  var oi = 0;
  for (var i = 0; i < 4; i++) {
    if (i === position) {
      out.push(correct);
    } else {
      out.push(others[oi]);
      oi++;
    }
  }
  return out;
}

var VIGNETTES = [
  // ---- Chapter 1: Classic Flaws (straightforward) ----
  { id: 1, chapter: 1, flaw: 'confound',
    text: 'In a memory study, everyone in the "nap" group is tested in a quiet, dim room at 2pm, while everyone in the "no-nap" group is tested in a bright, noisy hallway at 9am. The nap group recalls more words, and the researcher concludes that napping improves memory.',
    options: opt('confound', 'no_control', 'selection', 'demand', 1),
    explanation: 'The room, noise level, and time of day all vary together with the nap/no-nap assignment. Any of those — not the nap itself — could explain the memory difference. This is an uncontrolled confound: a variable other than the one being studied that changes right along with it.' },
  { id: 2, chapter: 1, flaw: 'selection',
    text: 'A running club offers a free 8-week training program. The people who voluntarily sign up finish it and report lower resting heart rates than club members who never signed up. The club advertises: "Our program lowers resting heart rate."',
    options: opt('selection', 'confound', 'no_control', 'corr_causation', 2),
    explanation: 'The two groups were never comparable to begin with — people who choose to sign up for a training program are probably already more fit or motivated than people who don’t. This is selection bias: the groups differ systematically before the study starts, with no random assignment to rule that out.' },
  { id: 3, chapter: 1, flaw: 'no_control',
    text: 'A clinic gives all of its patients a new breathing exercise for panic attacks. After four weeks, patients report fewer panic episodes than they did before starting. The clinic concludes the breathing exercise works.',
    options: opt('no_control', 'regression', 'confound', 'corr_causation', 0),
    explanation: 'There’s no comparison group — no one went four weeks without the exercise to see what would have happened anyway. Panic symptoms often ease on their own over time, and without a control group there’s no way to separate that from a true treatment effect.' },
  { id: 4, chapter: 1, flaw: 'demand',
    text: 'A researcher tells participants, "This is a study on whether calming music reduces test anxiety," then plays calming music before a test and asks them to rate how anxious they feel. Anxiety ratings are lower than in a silent control group.',
    options: opt('demand', 'blinding', 'no_control', 'confound', 3),
    explanation: 'Participants were told exactly what the study expected to find. That knowledge alone can shape self-reported anxiety ratings, independent of any real effect of the music — a classic demand characteristic.' },
  { id: 5, chapter: 1, flaw: 'ceiling',
    text: 'A researcher gives a very easy vocabulary test to a group of PhD students to see if a new study technique improves scores. Nearly everyone scores 98-100%, both before and after the technique, so the researcher concludes the technique has no effect.',
    options: opt('ceiling', 'underpowered', 'no_control', 'generalization', 1),
    explanation: 'Almost everyone is already near the top of the scale before the study even starts. There’s no room left for scores to rise, so a real improvement could easily be masked — this is a ceiling effect, not evidence the technique doesn’t work.' },
  { id: 6, chapter: 1, flaw: 'regression',
    text: 'A school selects the 20 students with the very lowest scores on a stress survey and enrolls them in a new relaxation workshop. Three months later, their average stress score has dropped substantially. The school credits the workshop.',
    options: opt('regression', 'no_control', 'selection', 'ceiling', 2),
    explanation: 'These students were selected specifically because their scores were extreme at that single moment. Extreme scores naturally tend to move back toward the average on retest, regardless of any intervention — that’s regression to the mean.' },
  { id: 7, chapter: 1, flaw: 'corr_causation',
    text: 'A survey finds that employees who report drinking more coffee also report higher job satisfaction. A blog headline reads: "Coffee makes you happier at work."',
    options: opt('corr_causation', 'confound', 'selection', 'generalization', 0),
    explanation: 'This is a purely observational association between two variables with no manipulation and no groups being compared. Coffee drinking and job satisfaction could both be driven by something else entirely — correlation alone can’t establish that coffee causes happiness.' },
  { id: 8, chapter: 1, flaw: 'underpowered',
    text: 'A pilot study tests a new grief-counseling technique with 4 participants total (2 per group) and reports a "large, statistically significant improvement in mood." The lab announces the technique is ready for wider clinical use.',
    options: opt('underpowered', 'no_control', 'generalization', 'ceiling', 3),
    explanation: 'With only 2 participants per group, the study has almost no ability to reliably detect a true effect, and any "significant" result from a sample this small is fragile and easily driven by one or two individuals — the sample is badly underpowered for the claim being made.' },
  { id: 9, chapter: 1, flaw: 'blinding',
    text: 'In a drug trial, the same research assistant who knows which patients received the real antidepressant and which received placebo also conducts the follow-up mood interviews and assigns the mood ratings.',
    options: opt('blinding', 'demand', 'confound', 'selection', 1),
    explanation: 'Because the rater knows who is in which group, their scoring can be consciously or unconsciously influenced by that knowledge, even with good intentions. This is a lack of blinding — the fix is to keep raters unaware of group assignment.' },
  { id: 10, chapter: 1, flaw: 'generalization',
    text: 'A team recruits 30 first-year psychology majors at one university, runs a study on decision-making under stress, and concludes: "Humans make riskier decisions under stress."',
    options: opt('generalization', 'selection', 'underpowered', 'corr_causation', 2),
    explanation: 'Thirty psychology undergraduates from a single university are a narrow, unusual slice of humanity — not necessarily representative of "humans" broadly. The conclusion is stated far more broadly than the sample can support.' },

  // ---- Chapter 2: Level Up (subtler wording, same flaw types) ----
  { id: 11, chapter: 2, flaw: 'confound',
    text: 'A university compares two sections of the same course: one meets in a renovated, air-conditioned building and is taught the "flipped classroom" method; the other meets in an older, warmer building with traditional lectures. The flipped-classroom section scores higher on the final exam, and the department concludes the flipped method is more effective.',
    options: opt('confound', 'selection', 'no_control', 'generalization', 0),
    explanation: 'Teaching method isn’t the only thing that differs between the two sections — building comfort and room quality travel along with it. Any of those could explain the exam-score gap, which makes the comparison confounded.' },
  { id: 12, chapter: 2, flaw: 'selection',
    text: 'An employer offers an optional resilience-training seminar. A year later, employees who attended have fewer sick days than employees who didn’t. HR reports the seminar "reduces absenteeism by 30%."',
    options: opt('selection', 'corr_causation', 'confound', 'no_control', 1),
    explanation: 'Employees who opt into a voluntary wellness seminar are likely already more engaged or health-conscious than those who skip it. Without random assignment, that pre-existing difference — not the seminar — could be driving the gap in sick days.' },
  { id: 13, chapter: 2, flaw: 'no_control',
    text: 'A forensic psychology lab develops a new interview protocol for reducing false confessions and trains detectives to use it. Six months after training, the department’s false-confession complaints have dropped, and the lab reports the protocol as the cause.',
    options: opt('no_control', 'regression', 'confound', 'generalization', 2),
    explanation: 'There’s no comparable set of detectives or cases that continued under the old protocol during the same period. Complaint rates can drift for many reasons — without a control group, the protocol can’t be credited with confidence.' },
  { id: 14, chapter: 2, flaw: 'demand',
    text: 'In a study on implicit bias training, the facilitator explains the training’s goal to reduce bias in detail before administering a post-training bias questionnaire, and reminds participants, "try to think about what you learned today" as they complete it.',
    options: opt('demand', 'blinding', 'ceiling', 'confound', 3),
    explanation: 'Participants are being cued, right before they answer, to respond in line with what the training just taught them. Their questionnaire answers may reflect what they think they’re supposed to say rather than a genuine shift in bias.' },
  { id: 15, chapter: 2, flaw: 'ceiling',
    text: 'A hospital rolls out a new hand-hygiene reminder system on a ward where staff compliance was already measured at 96% before the rollout. Three months later compliance is 97%, and the hospital concludes the reminder system "barely helps."',
    options: opt('ceiling', 'underpowered', 'no_control', 'regression', 0),
    explanation: 'Compliance was already close to the maximum possible score before the intervention even started. With almost no room left to improve, a small numeric change looks unimpressive, even if the underlying effect is real — a ceiling effect.' },
  { id: 16, chapter: 2, flaw: 'regression',
    text: 'A sports psychologist works one-on-one with the three golfers on the team who had by far the worst rounds at last week’s tournament. After one session each, all three shoot noticeably better rounds the following week, and the psychologist cites this as proof the technique works.',
    options: opt('regression', 'no_control', 'selection', 'confound', 1),
    explanation: 'These golfers were picked precisely because their scores were unusually bad in that one tournament. Performance that extreme tends to bounce back toward a player’s normal average on its own — regression to the mean, not necessarily the intervention.' },
  { id: 17, chapter: 2, flaw: 'corr_causation',
    text: 'Archival data across 40 countries show that nations with higher chocolate consumption per capita also have more Nobel laureates per capita. A widely shared article concludes chocolate boosts scientific achievement.',
    options: opt('corr_causation', 'confound', 'selection', 'generalization', 2),
    explanation: 'This is a cross-national correlation with no experiment and no groups being compared — richer, more developed countries tend to have both more chocolate consumption and more research infrastructure. The association doesn’t establish causation.' },
  { id: 18, chapter: 2, flaw: 'underpowered',
    text: 'A neuroimaging study scans 6 participants total (3 per group) and reports a specific pattern of amygdala activation that "significantly distinguishes" the two groups, describing it as a robust biomarker.',
    options: opt('underpowered', 'generalization', 'ceiling', 'no_control', 3),
    explanation: 'Neuroimaging effects estimated from 3 people per group are notoriously unstable — a "significant" pattern from a sample this small is very likely to be noise that won’t replicate, rather than a reliable biomarker.' },
  { id: 19, chapter: 2, flaw: 'blinding',
    text: 'In a study testing whether a new pain cream works better than a plain moisturizer, both patients and the nurse recording pain ratings are told which cream is the "real" medicated one and which is the placebo.',
    options: opt('blinding', 'demand', 'no_control', 'confound', 0),
    explanation: 'Both the patient and the person recording the outcome know which treatment is which. That knowledge can shape both how patients report pain and how the nurse records it — the study isn’t blinded on either side.' },
  { id: 20, chapter: 2, flaw: 'generalization',
    text: 'Researchers test a new cognitive task in a lab using 25 undergraduate volunteers who are also all varsity athletes, and conclude their findings about attention and reaction time apply to "people recovering from concussion" generally.',
    options: opt('generalization', 'no_control', 'underpowered', 'selection', 1),
    explanation: 'Young, healthy varsity athletes are a very specific and unusually fit population — quite different from the broader, more medically diverse group of people recovering from concussion that the conclusion is being applied to.' },

  // ---- Chapter 3: Detective Finals (trickiest — near-miss distractors) ----
  { id: 21, chapter: 3, flaw: 'confound',
    text: 'A lab testing whether background nature sounds reduce stress during a cognitive task always runs the nature-sounds condition using a research assistant who is warm and encouraging, and always runs the silence condition using a different research assistant who is brisk and formal. Participants were randomly assigned to condition. Stress ratings are lower in the nature-sounds condition.',
    options: opt('confound', 'demand', 'selection', 'blinding', 2),
    explanation: 'Random assignment rules out selection bias here — the groups start out equivalent. But the two research assistants’ manner is bundled with the sound condition, so warmth/formality (not the nature sounds) could be driving the stress difference. That’s a confound layered on top of an otherwise well-randomized design.' },
  { id: 22, chapter: 3, flaw: 'selection',
    text: 'A stress-management app tracks its users and finds that people who kept the app installed for 6+ months report significantly lower anxiety than people who deleted it in the first week. The company claims the app "reduces anxiety with sustained use."',
    options: opt('selection', 'no_control', 'corr_causation', 'regression', 0),
    explanation: 'This isn’t a bare correlation between two unrelated variables — it’s a comparison between two groups (kept vs. deleted the app) that were never randomly assigned. People who stick with a self-help app for 6 months likely differ from quitters in motivation or baseline anxiety trajectory before the app is even considered, which is selection bias.' },
  { id: 23, chapter: 3, flaw: 'no_control',
    text: 'A prison introduces a new cognitive-behavioral program for a single cohort of inmates and tracks their disciplinary infractions before and after the program, finding a drop afterward. Because infractions were measured on the very same inmates both times, the facility calls this "a controlled before-after comparison."',
    options: opt('no_control', 'regression', 'confound', 'selection', 1),
    explanation: 'Measuring the same group before and after isn’t the same as having a control group — there’s still no comparable group that didn’t receive the program during the same period, so we can’t rule out that infractions would have dropped anyway.' },
  { id: 24, chapter: 3, flaw: 'demand',
    text: 'In a randomized, blinded trial testing a new empathy-training video, the post-test questionnaire is titled "Empathy Training Outcomes Survey" and its first question asks, "How much did the empathy training you just watched change your perspective?"',
    options: opt('demand', 'blinding', 'confound', 'corr_causation', 3),
    explanation: 'Even though random assignment and blinding of condition were handled correctly elsewhere, the questionnaire itself tips participants off to exactly what’s being measured and expected, which can shape self-reported answers independent of any real effect — the flaw lives in the measurement instrument, not the design.' },
  { id: 25, chapter: 3, flaw: 'ceiling',
    text: 'A study on a new sleep intervention only recruits participants who already sleep a healthy 7-8 hours a night, then measures whether the intervention increases total sleep time. It finds "no significant increase" and concludes the intervention doesn’t work.',
    options: opt('ceiling', 'selection', 'underpowered', 'no_control', 0),
    explanation: 'Recruiting only already-healthy sleepers means there’s very little room for sleep duration to increase further — a ceiling effect on the outcome measure itself, not a sampling bias between comparison groups, since there’s only one group of already-well-rested people being tracked.' },
  { id: 26, chapter: 3, flaw: 'regression',
    text: 'A clinic re-tests every patient who scored in the clinical range for depression at intake, three months into treatment, and reports that scores improved "significantly" on average — but only for the subset of patients whose intake score was in the most severe top 10%.',
    options: opt('regression', 'no_control', 'ceiling', 'underpowered', 1),
    explanation: 'By focusing specifically on the patients with the most extreme initial scores, the clinic has set up exactly the conditions for regression to the mean — the most severe scorers are the ones most likely to look better on retest for purely statistical reasons, treatment aside.' },
  { id: 27, chapter: 3, flaw: 'corr_causation',
    text: 'A 10-year longitudinal survey finds that people who report more close friendships at age 30 also report better cardiovascular health at age 60, even after the researchers statistically adjust for income, smoking, and exercise. A magazine headline reads: "Friendship protects your heart."',
    options: opt('corr_causation', 'confound', 'generalization', 'underpowered', 2),
    explanation: 'Statistically adjusting for a few known variables narrows the possibilities but doesn’t turn an observational survey into an experiment — there could still be unmeasured factors driving both friendship and heart health. No one was randomly assigned to have more or fewer friends, so causation still can’t be established from this design alone.' },
  { id: 28, chapter: 3, flaw: 'underpowered',
    text: 'A well-designed, properly randomized, double-blind trial of a new anxiety medication enrolls 400 participants, but a rare side effect is later found to occur in about 1 in 500 people. The trial reports "no cases observed" and concludes the side effect doesn’t exist.',
    options: opt('underpowered', 'no_control', 'ceiling', 'generalization', 3),
    explanation: 'Everything about the trial’s core design is sound — the problem is that with only 400 participants, a side effect occurring at roughly 1-in-500 would be expected to show up in less than one person on average. The sample is underpowered specifically for detecting rare events, even though it’s plenty large for the main efficacy question.' },
  { id: 29, chapter: 3, flaw: 'blinding',
    text: 'A study uses a validated, standardized rating scale and trains raters carefully, but the same clinician who diagnosed each patient’s disorder (and therefore knows which patients belong to the "high-severity" group under study) also scores every participant’s outcome video using that scale.',
    options: opt('blinding', 'demand', 'confound', 'selection', 0),
    explanation: 'Standardizing the scale and training the raters helps, but it doesn’t fix the fact that the rater knows each patient’s group membership going in. That knowledge can still color subjective judgment calls when scoring ambiguous moments in the video, even with a good instrument in hand.' },
  { id: 30, chapter: 3, flaw: 'generalization',
    text: 'A well-powered, randomly assigned, properly blinded trial of a stress-reduction technique is conducted entirely on active-duty special forces soldiers, and the published paper’s abstract concludes: "This technique is recommended for stress reduction in the general population."',
    options: opt('generalization', 'selection', 'underpowered', 'corr_causation', 1),
    explanation: 'The internal design here is excellent — randomization, blinding, and power are all handled well. The problem is external: elite special forces soldiers are an extremely atypical population, so a conclusion aimed at "the general population" overreaches what this specific sample can support.' }
];
