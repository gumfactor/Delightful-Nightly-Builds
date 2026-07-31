# Manual — Neurofact

## Playing the Game

Open `index.html` in any browser — no server, no build step, no internet connection required.

```
open builds/2026-06-27-neurofact/index.html
```

1. Click **Start Game** on the intro screen.
2. Read each claim carefully. Both real findings and AI-generated fakes are written in scientific language.
3. Click **✓ Real Finding** or **✗ AI Generated**.
4. The correct answer is revealed, with a brief explanation.
5. Click **Next →** to advance.
6. After 30 questions, your grade and accuracy breakdown appear. Click **Play Again** to shuffle and restart.

## Scoring

| Accuracy | Grade | Label |
|----------|-------|-------|
| ≥ 90% | A | Neuroscience Luminary |
| 80–89% | B | Research-Literate |
| 70–79% | C | Cautiously Credulous |
| 60–69% | D | Fooled by Plausibility |
| < 60% | F | Read More Papers |

## Regenerating Questions

To refresh the question bank using the Anthropic API:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python src/generator.py
```

This fetches recent neuroscience abstracts from arXiv, calls Claude to simplify real findings and generate plausible fakes, and writes `game_data.json`. To embed the new questions in the game, paste the JSON array from `game_data.json` over the `QUESTIONS` constant in `index.html`.

### Options

```
python src/generator.py --count 30    # default: 30 questions (15 real, 15 fake)
python src/generator.py --dry-run     # validate without calling API
python src/generator.py --output path/to/custom.json
```

## Running Tests

### Playwright (browser game — 36 tests)
```bash
cd builds/2026-06-27-neurofact
npx playwright test
```

### pytest (generator logic — 36 tests)
```bash
cd builds/2026-06-27-neurofact
python3 -m pytest tests/test_generator.py -v
```

### Both at once
```bash
python3 -m pytest tests/test_generator.py -v && npx playwright test
```

## Question Categories

| Category | Example topics |
|----------|---------------|
| Memory | Place cells, sleep consolidation, TMS interference |
| Stress | Cortisol, HPA axis, amygdala reactivity |
| Social Neuroscience | Mirror neurons, social pain, oxytocin |
| Psychopathy | Fear-potentiated startle, cognitive vs. affective empathy |
| Emotion Regulation | Reappraisal, prefrontal control |
| Reward | Dopamine uncertainty, ventral striatum |
| Cognitive Neuroscience | Default mode network, executive control |
| Neuroanatomy | Cerebellum, fiber tracts, commissures |
| Developmental Neuroscience | Neonatal lesions, adolescent cannabis, adversity |
| Hormones | Testosterone and social behavior |
| Autonomic Neuroscience | Vagal tone, heart rate variability |
| Interoception | Heartbeat perception, emotional granularity |
| Moral Cognition | vmPFC lesions, utilitarian judgment |

## Difficulty Levels

- **Foundational** — textbook-level findings most graduate students should know
- **Advanced** — findings from major empirical papers, requires domain familiarity
- **Expert** — specific mechanistic claims that require deep literature knowledge
