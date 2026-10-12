# React UI Practice

A self-contained practice kit for timed React UI rounds: "implement this Figma mockup in an existing codebase, no AI".
It runs entirely in the browser as one HTML file. No install, no account, no backend.

**Open it:** download [`dist/index.html`](dist/index.html) and double-click it. (React and the JSX/TypeScript compiler
load from a public CDN the first time you open a workspace.)

## What's inside
- **Lessons** on CSS layout (boxes, flexbox, grid), React (components, state, events and forms, effects and data loading,
  structuring a feature), JavaScript data pipelines, debugging, gotchas, and looking things up quickly. Most lessons have live
  playgrounds and quizzes.
- **A CodeSignal-style workspace**: file explorer, editor, live preview, console, a timer, a Design tab with an inspectable
  target (the "Figma"), hints, a self-review rubric and a reference solution.
- **Drills, speed runs and mock interviews**, including feature-extension mocks sized like a real 30–55 minute round with a
  requirement change partway through.
- **60 daily challenges** in TypeScript, from 10-minute single-concept drills to 45-minute staff-level features (accessible
  combobox, virtualized list, streaming AI chat with Stop, drag-and-drop with rollback, date range picker). Each runs inside a
  small working app with a mock API that has a random delay.
- **Data drills**: 18 filter / map / group / reduce exercises with expected-output checks.
- **Staff track**: 8 reading lessons on architecture, server state, rendering models, performance, design systems, testing,
  TypeScript, and thinking like a staff engineer.
- **`notes/notes.html`**: a one-page cheat sheet of patterns and the mistakes that cost the most time.

Progress is saved in your browser's localStorage.

## Project layout
```
src/            shell (head.html, body.html), lessons/, data.js, ide.js (editor + preview runtime), workspace.js, guide.js, ...
src/daily/      metadata for the 60 daily challenges
ex/             every exercise as a text bundle: shared / starter / solution files
build.py        assembles everything into dist/index.html
test/           Playwright checks (compile every starter + solution, behaviour tests per challenge batch)
notes/          the standalone cheat sheet
```

## Build and test
```bash
python3 build.py                      # writes dist/index.html
cd test && python3 run.py             # compile-check every exercise (needs Python Playwright + Chromium and esbuild)
python3 test/daily_A.py               # behaviour tests for a batch of daily challenges (A–F)
```
The tests serve the page locally and replace the CDN React/Babel with a local bundle and an esbuild transform so they run
offline; see `test/server.py` and `test/run.py` for the paths they expect.

## Adding a challenge
Write `ex/<id>.txt` with `@@@ shared|starter|solution <path>` sections, add its metadata (title, minutes, requirements, hints,
rubric, design spec) to `src/data.js` or a `src/daily/*.json` batch, and rebuild. `DAILY_SPEC.md` and `STAFF_SPEC.md` are the
authoring specs used for the daily challenges and the staff track.
