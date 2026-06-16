# Future Features — Spaced Repetition Flashcards

## 1. Retention Statistics Dashboard

Add a "Stats" view (accessible via a tab or button) showing:
- Per-deck: total cards, mastered (interval > 21 days), learning, new
- Overall retention rate: (cards rated ≥ 3 on first attempt) / (cards reviewed)
- Study streak: consecutive days with at least one review completed
- Average EF per deck as a proxy for how well you're learning
- Daily review count history (bar chart, localStorage data)

This closes the feedback loop — the user can see if the algorithm is working and identify decks where retention is weakest.

## 2. User-Editable Card Decks via JSON Import

Add an "Import Deck" button that accepts a JSON file in the current card format:
```json
[{"id": "my01", "front": "Question", "back": "Answer"}]
```

This allows creating custom decks for course content, grant terminology, paper notes, or any other domain without touching the source HTML. Validation should flag malformed cards with helpful error messages. Export should also be supported for backup.

## 3. Additional Pre-Built Decks

High-value decks based on the user's learning goals and domains:
- **Neuroscience Terms** — key concepts for Social Affective Neuroscience (amygdala function, HPA axis, vagal tone, empathy circuitry, psychopathy markers)
- **fMRI/Neuroimaging Methods** — preprocessing steps, statistical thresholds, software tools (FSL, SPM, FreeSurfer), common artifacts and fixes
- **Research Statistics** — effect sizes, power analysis, mixed models, multiple comparisons corrections
- **Canadian Business Law** — relevant to The Canada List: incorporation types, consumer protection, trademark basics
- **Investment Analysis** — DCF concepts, valuation multiples, reading 10-K filings, risk metrics

## 4. Undo Last Rating

Add an "Undo" button that appears briefly after rating a card (e.g., 5 seconds). Clicking it reverts the card's state to what it was before the rating and adds the card back to the end of the current queue. This prevents a misclick from permanently changing the schedule.

Implementation: keep a `lastAction` object in memory (not localStorage) with the previous card state and card ID, clear it on page close or when the next rating is applied.

## 5. Keyboard Shortcuts

Allow rating cards without touching a mouse or tapping precisely on mobile:
- `Space` or `Enter` → Reveal answer
- `1` or `a` → Again
- `2` or `h` → Hard  
- `3` or `g` → Good
- `4` or `e` → Easy

Add a visible keyboard hint below the rating buttons. This makes desktop review significantly faster — typical power users rate 20 cards in under 2 minutes with keyboard shortcuts.

## 6. Offline PWA Installation

Convert `index.html` into a Progressive Web App with a minimal service worker and a `manifest.json`. This allows installing the flashcard app as a home screen icon on iPhone/Android — one tap, no URL bar, full-screen. The study habit becomes more accessible when it's as easy to open as a native app.

The service worker should cache the single HTML file, making the app fully functional with no network connection.
