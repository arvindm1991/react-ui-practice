# Re-scope + primitives: addendum to DAILY_SPEC.md

Read `/home/claude/prep/DAILY_SPEC.md` first (format, JSX standard, testing). This pass fixes two problems the user found
while doing the challenges.

## Problem 1: the time boxes are unrealistic
The user (Arvind) did "dc03 Password show/hide + strength" and said, correctly, it can't be done in 12 minutes. Measured
with `python3 test/size.py <id>`, almost every challenge's reference solution adds 2–4× more code than its stated minutes
allow. The cause: solutions implement Core + Next + Stretch + the change, but the minutes were set as if only a little Core
existed, and Core itself was often too big.

**Calibration from real data:** Arvind's drill "Directory search" adds 48 lines and took him ~27 min (fluent target ~19).
So use: **fluent minutes ≈ 5 + coreCodeLines / 3.5 + coreCssLines / 6**, and the CHANGE adds ≈ changeLines / 3.5.

**Rule: Core + change must fit the level's time box at fluent pace. Core alone must fit in ~70% of it.**

| Level | Card minutes | Core (new code lines, rough max) | Change (lines, max) |
|---|---|---|---|
| 1 | 10–15 | ≤ 25–30 code + ≤ 10 css | optional, ≤ 10 |
| 2 | 15–20 | ≤ 35–45 code + ≤ 12 css | optional, ≤ 12 |
| 3 | 20–30 | ≤ 50–65 code + ≤ 15 css | required, ≤ 15 |
| 4 | 30–40 | ≤ 70–90 code + ≤ 20 css | required, ≤ 20 |
| 5 | 40–45 | ≤ 95–110 code + ≤ 25 css | required, ≤ 25 |

## What to do for EACH of your challenges
1. Measure: `python3 test/size.py dcNN`.
2. **Re-tier the requirements** so the Core requirements fit the table above. Keep the challenge's identity (its main
   feature). Move secondary parts to **Next** (nice to reach) or **Stretch** (optional), keep the wording concrete. You may
   reword a requirement to split it (e.g. "label Weak/Fair/Strong" as Core, "3 coloured bar segments" as Next). Do NOT delete
   features. Everything stays in the solution and stays tested.
   - If even a minimal Core can't fit, simplify by **moving work into the starter codebase** (e.g. the starter already
     includes the CSS for the new component, or an existing helper), or, if it's a Level 3–5 challenge, raise `minutes`
     to the top of its band. Prefer moving CSS into the starter for Level 1–2 so he practises React, not stylesheets,
     at the start (Level 3+ should still require writing CSS for new UI).
   - Make sure the **change** is small (table above) and, if it was big, make it smaller or swap it for a smaller one. The
     solution must still implement it (update the solution and your behaviour test if you change it).
3. Update `minutes` (and `changeAt` ≈ 60–70% of minutes) to match, update the brief's **Pass bar** text ("Core 1–2 working.
   Strong: plus 3–4.") and timeline, update `tiers`, and keep `tiers.length === requirements.length`.
4. In the **solution** files, mark Core with comments so he can compare: `// CORE: <what>` above each Core block and
   `// NEXT: <what>` / `// STRETCH:` / `// CHANGE:` above the others (CSS: `/* CORE */` etc.). Comments only; don't
   restructure working code.
5. Add the **`primitives`** field (below).
6. Run your batch's compile test and behaviour test again (`run.py` + `test/daily_<LETTER>.py`, your port from DAILY_SPEC)
   and fix anything you broke. Rewrite your batch JSON atomically.

## Problem 2: he doesn't know the primitives
He didn't know `RegExp.test()` exists or how to write it. Each challenge now teaches its primitives. Add to the metadata:
```json
"primitives": [
  { "cat": "Regex", "name": "RegExp.test()", "syntax": "/pattern/.test(str)",
    "example": "/\\d/.test('abc1')   // true  (contains a digit)",
    "note": "Returns <b>true/false</b>: does the string contain a match? Use it for simple checks like 'has a number'.",
    "search": "mdn regexp test" }
]
```
- 2–5 per challenge: the specific JS/TS/DOM/React building blocks the **Core + change** need that a beginner might not know
  or might not remember how to type. Include syntax he'd actually type, an example with its result in a comment, a one-line
  note (HTML allowed; say what it RETURNS and any gotcha), and the search phrase he'd use.
- `cat` must be one of: Strings, Numbers, Regex, Arrays, Objects, Map & Set, Dates, Timers, Promises & async, Events, DOM,
  React, TypeScript, CSS, Other.
- Don't repeat trivial basics in every challenge. Introduce a primitive the first time it's needed; repeat it later only if
  it's used in a new way. Across Level 1–2 cover the everyday ones (string methods: `includes`, `toLowerCase`, `trim`,
  `startsWith`, `slice`, `split`/`join`, template literals; `Number()`, `toFixed`, `Math.min/max`; regex `.test`; array
  `map/filter/find/some/every/includes/reduce/sort` with copy, spread; object spread; `Object.entries`; `setTimeout`/
  `setInterval`/`clear*`; `e.target.value`, `e.preventDefault()`, `e.key`; `useState` updater; `useEffect` cleanup;
  `Promise.then/catch/finally`, `async/await`, `try/catch`; `Intl.NumberFormat`/`toLocaleString`; `localStorage` with try/catch; etc.)
- In JSON strings escape backslashes (`"/\\d/"`) and quotes.
- The page renders these in a "Today's primitives" card and on a "Primitives reference" page (built automatically).

## Report
A table: id · old minutes → new minutes · Core lines before → after (from `test/size.py` thinking: estimate Core lines by
the marked CORE blocks) · what moved out of Core · primitives added. Then compile + behaviour test results.
Only edit your batch's files (ex/dcNN.txt, src/daily/batch<LETTER>.json, test/daily_<LETTER>.py).
