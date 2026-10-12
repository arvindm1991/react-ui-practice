# Staff track: authoring spec

## Reader
Arvind: a Director of Product & Engineering and ex-founder who knows React fundamentals and is working through 60
hand-coding challenges. He wants to understand **how staff-level frontend engineers think** about the topics that
UI exercises don't cover. This track is **reading only, with no exercises to practise**: concepts, mental models, and how to
approach decisions. He has said that dense lists and abstract explanations don't work for him. He learns from
**concrete examples built up from scratch** ("here's a real app, here's the problem that shows up at 50 components,
here's what people tried, here's the idea that fixes it"). Plain words, short paragraphs, define every term the first time.

## Format (MUST match the existing prep kit)
- Lesson files live in `/home/claude/prep/src/lessons/<file>.html`, one `<template id="tpl-<moduleId>">` each.
  Study `src/lessons/react3.html`, `src/lessons/react5.html` and `src/lessons/pipeline.html` for the building blocks and
  `src/head.html` for available CSS classes and colour variables:
  `<h1>`, `<p class="lede">`, `<div class="goals"><b>After this lesson you can</b><ul>…</ul></div>`, numbered `<h2>`
  sections, `<script type="text/x-code" data-lang="jsx|js|ts|tsx|css|html" data-title="…">` code snippets (raw code,
  no escaping needed inside), `.callout` boxes (check head.html for variants), `.ba` before/after, `.trace`, tables inside
  `<div class="table-wrap"><table>`, and quizzes via `data-quiz` (see how existing lessons and `QUIZZES` in `src/data.js` do
  it; if quizzes require editing data.js, use a `<details>` "Check yourself" block instead. Do NOT edit data.js).
- Diagrams: inline `<svg>` with `viewBox`, `width="100%"`, using `currentColor` and the CSS variables defined in
  head.html, so they work in light AND dark mode. Boxes and arrows that show the real flow. Text ≥ 12px.
- Each lesson: ~2,000–3,000 words, 2+ diagrams, one running example app carried through the whole lesson (e.g. "Lexi",
  a reading app for schools with teacher dashboards, student reading sessions and district reports), real code snippets in
  TypeScript/TSX, a "How a staff engineer approaches this" section (the questions they ask, the decision framework, the trade-offs
  stated as "X gives you A at the cost of B; choose it when C"), a "Common mistakes" section, a "What to say in a design
  review / interview" callout, and a short recap.
- No `&&`/ternaries inside JSX in code samples that show recommended code (his personal standard: decisions above the
  return with `if`), except where you are specifically showing what library code or other people's code looks like.
- Be technically accurate and current as of mid-2026 (React 19, Next.js App Router, React Server Components, TanStack
  Query v5, Vitest/Jest + React Testing Library, Playwright, Core Web Vitals with INP). When unsure about a specific
  API detail, describe the concept rather than inventing an API.

## Verify before reporting
- HTML is balanced, exactly one template per file with the right id.
- Run `python3 -c` or a small script to check the template parses (e.g. with html.parser, counting open/close tags).
- Do not edit any shared files (data.js, guide.js, build.py, head.html, other lessons). The coordinator wires the modules in.
- Report: file names, template ids, titles, word counts, and a 2-line summary of each lesson.
