# Daily challenges: authoring spec

You are writing React + TypeScript practice challenges for Arvind, a product/engineering leader who is
training to implement UI features **by hand, without AI**, in a timed CodeSignal-style round
(an existing small app + a mock API + a Figma-style target; he adds one feature). He will do one per day,
in order, for 60 days. Difficulty rises from 10-minute single-concept drills to 45-minute
staff-level features. Quality matters more than speed: every challenge must be realistic, fair for its time
box, fully working, and tested.

## Read these first (reference implementation)
- `/home/claude/prep/ex/m7.txt`: a complete challenge file (TypeScript, api.ts with random delay,
  App.tsx with several named components, starter vs solution, styles).
- `/home/claude/prep/src/data.js`: search for `m7: {` to see the metadata shape (brief, tiers, requirements,
  change, hints, rubric, spec).
- `/home/claude/prep/test/run.py` and `/home/claude/prep/test/run8.py`: how challenges are compile-tested and
  behaviour-tested with Playwright.

## Files you write (and ONLY these; other authors are working in parallel)
1. One file per challenge: `/home/claude/prep/ex/dcNN.txt` (NN = 01..60, zero-padded), in the `@@@` format:
   ```
   @@@ shared src/api.ts            (files identical in starter and solution)
   @@@ shared src/...               (helpers/components that already exist in the "codebase")
   @@@ starter src/App.tsx          (what he starts with)
   @@@ starter src/styles.css
   @@@ solution src/App.tsx         (the reference solution: overrides the starter file)
   @@@ solution src/styles.css      (full stylesheet including the added CSS)
   @@@ solution src/components/X.tsx (any NEW files the solution adds)
   ```
   `src/index.jsx` is added automatically (it imports `./App` and `./styles.css`). Do NOT write it.
   Imports resolve `.tsx`, `.ts`, `.jsx`, `.js` (omit the extension in imports). Only `react` and `react-dom`
   are available as packages, no other npm packages.
2. One metadata file for your batch: `/home/claude/prep/src/daily/batch<LETTER>.json`, a JSON object
   mapping id → exercise. It must be valid JSON (double quotes, no trailing commas, no functions).
   Write it atomically at the end (write to a temp name, then rename), so the shared build never sees half a file.

## Metadata shape (JSON)
```json
"dc07": {
  "kind": "drill",
  "level": 1,
  "order": 7,
  "minutes": 12,
  "title": "Searchable list",
  "focus": "src/App.tsx",
  "summary": "One sentence shown on the card.",
  "skills": ["controlled input", "derived filter"],
  "brief": "<p>HTML. What exists already, what to build, what to read first. Mention the api.ts delay if used.</p><div style=\"border:1px solid var(--ide-line);border-radius:8px;padding:10px 12px;margin:12px 0;font-size:13px\"><b>Pass bar:</b> Core working. <b>Strong:</b> plus Next.</div><details class=\"details\"><summary>Reference \"plan out loud\" (open after saying yours)</summary><div style=\"font-size:13px\"><p>...</p></div></details>",
  "tiers": ["Core", "Core", "Next", "Stretch"],
  "requirements": ["HTML string, one per tier entry, concrete and checkable"],
  "change": { "title": "...", "html": "<p>Mid-session change...</p>" },
  "changeAt": 9,
  "hints": ["HTML strings, progressively more specific, end with the key code shape"],
  "rubric": ["What an interviewer would note (6-7 items)"],
  "spec": {
    "colors": [["--primary", "#4F46E5"], ["Name", "#hex or rgba(...)"]],
    "notes": [["Thing", "measurements like 'h 36 · radius 8 · pad 12 16'"]]
  }
}
```
- `kind` is always `"drill"`. `level` and `order` come from your assignment list below. `focus` is the file he should start in.
- `change`/`changeAt` are optional for Level 1–2 and **required for Level 3–5** (a mid-session requirement change at roughly
  60–70% of the time, which takes ~10–20% of the time to implement). If you include `change`, the solution must include it.
- `tiers` length must equal `requirements` length. Use 2–3 Core, 1–2 Next, 0–1 Stretch. "Core working" must be achievable
  well inside `minutes` for someone at that level.
- `minutes`: Level 1: 10–15 · Level 2: 15–20 · Level 3: 20–30 · Level 4: 30–40 · Level 5: 40–45.
- Hints use `&lt;` / `&gt;` for angle brackets inside `<code>` (they are HTML).
- In JSON strings, escape `"` as `\"` and `\` as `\\`. Validate with `python3 -c "import json;json.load(open(path))"`.

## The codebase you write (starter)
- **Always TypeScript**: `src/App.tsx`, plus `src/api.ts` when data is involved (most Level 2+ challenges), plus
  optional `src/types.ts`, `src/utils/*.ts`, `src/components/*.tsx`.
- The starter is a **working, styled small app** (a realistic product surface: a settings page, an inbox, a store, a
  dashboard...) with **several named components** (in App.tsx and/or components/). The challenge adds ONE feature to it.
  It should render meaningful UI immediately. Never "a blank page plus a JSON dump".
- Put **reusable helpers in the codebase** that the solution should reuse (a `formatPrice`, an `Avatar`, a `Button`), and
  mention in the brief that `utils/` and `components/` are worth reading. Reuse is part of what is scored.
- `api.ts` pattern (copy from m7): `randomDelay(min, max)` returning a Promise via setTimeout; exported `async` functions
  returning copies of data (`map((x) => ({ ...x }))`); exported `type`s. Delays roughly 300–1500 ms.
  If a challenge needs errors, make failure **deterministic and controllable** (e.g. a `shouldFail` argument wired to a
  "Simulate failure" checkbox in the starter UI, or a specific input like the email `taken@example.com`). Never fail at
  random, because tests must be reliable.
- Starter CSS: complete for what exists. Use CSS custom properties on `:root`. The candidate writes the CSS for the new
  feature, so the solution's stylesheet adds a clearly marked block `/* ---- Added: <feature> ---- */`.
- Keep files a realistic size: starters roughly 60–200 lines total; solutions should be what a strong engineer would write
  in the time box (Level 1 ≈ 30–80 new lines, Level 5 ≈ 150–300).

## Reference solution style (MANDATORY: this is Arvind's personal JSX standard)
1. Every arrow function body uses braces + `return` (`items.map((x) => { return <li key={x.id}>…</li>; })`).
   Exception: tiny inline event handlers are written `onClick={() => { doThing(id); }}`. Note the braces here too.
2. Decisions happen **above the return** with plain `if`, stored in variables. **No `&&` and no ternaries inside JSX.**
   (`let empty = null; if (list.length === 0) { empty = <p>None</p>; }` then `{empty}`.)
3. Skip inside a map with `if (!x) { return null; }`.
4. Class names are built above: `let cls = 'row'; if (active) { cls = 'row is-active'; }`.
5. Handlers are named functions above the return, called from JSX via arrows.
6. Inputs are always controlled: `value` + `onChange`.
7. Inside JSX only tags, text and `{variable}`.
Component order: state → effects → handlers → derived data → decisions → JSX.
Async loading uses `useEffect` + `.then` with a `let cancelled = false` guard and a cleanup that sets it.
Use the updater form when the new state depends on the old. Never mutate state. Keys are stable ids.
TypeScript: type props with an inline type or a `type XProps = {...}`, `useState<Item[]>([])`, `import type { X } from './api'`.
Keep types light, like a pragmatic product engineer, not type gymnastics. Add short comments only where they teach
something (e.g. `// derived: never stored in state`).

## Challenge quality bar
- Realistic product feature, the kind of thing a Figma mock would show. Vary the domains (fintech, education, travel,
  dev tools, social, e-commerce, health, AI products...). Vary visual style so they don't all look the same.
- Every requirement is concrete and checkable (exact labels, exact behaviour, edge cases named).
- Level 1–2 teach one or two patterns cleanly. Level 3+ combine patterns. Level 5 requires staff-level care:
  keyboard support, ARIA, focus management, race conditions, performance, optimistic updates with rollback, etc.
- The brief tells him what exists and what to read; the "plan out loud" reference states where state lives and why.
- Hints escalate from a nudge to the exact code shape. At least one hint names what to **search on MDN/Google** for anything
  he might not know (e.g. "search: mdn selectionStart").

## Testing (MANDATORY, do not report done until all pass)
Work from `/home/claude/prep`. Use YOUR OWN port and output path so you don't collide with other authors:
```
python3 build.py /tmp/claude-0/-home-claude/653a60f8-7891-5769-b62a-4ce1d270b59d/scratchpad/dist-<LETTER>.html
cd test && DIST_HTML=/tmp/claude-0/-home-claude/653a60f8-7891-5769-b62a-4ce1d270b59d/scratchpad/dist-<LETTER>.html PORT=<yourport> timeout 600 python3 run.py '["dc01","dc02"]'
```
`run.py` checks that the starter and the solution both compile with no error overlay and no console errors.
(Other batches' half-written files may print a WARN from build.py; ignore warnings about other batches.)

Then write `test/daily_<LETTER>.py` (copy the Playwright structure from `test/run8.py`, use your own port, and set the
`DIST_HTML` env for the server subprocess) that, for EACH of your challenges, opens it with
`Workspace.open("dcNN")`, goes to the Design tab (which renders the SOLUTION), switches to Interact mode, and exercises
the core behaviours **plus the change** through the UI (click, type, wait for the mock delay, then assert text/counts).
Print PASS/FAIL per check; fix the solution until every check passes. Locators inside the preview work via
`page.locator('#designHost').locator('.your-class')`. Wait at least the API's max delay + 200 ms after triggering a load.
Also take one screenshot per challenge of the design tab into `test/shots/dcNN.png` and LOOK at it (Read tool):
it must look like a polished product UI, not unstyled HTML. Note: the design pane is narrow (~320px), so click the "Expand"
button (`#wideBtn`) before screenshots.

Finally, report: a table of id · title · minutes · level, plus "all compile ✓, all behaviour checks ✓" (or what failed).
Do not edit shared files (src/*.js, src/*.html, build.py, test/run*.py, other batches' files).
