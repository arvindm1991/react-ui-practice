"""Assemble the single-file artifact from src/ and ex/."""
import json, re, pathlib, sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / 'src'
EX = ROOT / 'ex'

INDEX = """import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

const root = createRoot(document.getElementById('root'));
root.render(<App />);
"""


def parse_ex(text):
    files = {'shared': {}, 'starter': {}, 'solution': {}}
    parts = re.split(r'^@@@ (\w+) (\S+)\n', text, flags=re.M)
    for i in range(1, len(parts), 3):
        role, path, body = parts[i], parts[i + 1], parts[i + 2]
        files[role][path] = body.rstrip('\n') + '\n'
    if 'src/index.jsx' not in files['shared']:
        files['shared']['src/index.jsx'] = INDEX
    return files


def build(out_path, extra_head=''):
    exfiles = {p.stem: parse_ex(p.read_text()) for p in sorted(EX.glob('*.txt'))}
    js_ex = 'const EXFILES = ' + json.dumps(exfiles, ensure_ascii=False).replace('</', '<\\/') + ';\n'
    # Daily challenges: each batch is src/daily/*.json -> { "<id>": {exercise...}, ... }.
    # Broken or half-written batches are skipped so parallel authors don't break each other.
    daily = {}
    for jp in sorted((SRC / 'daily').glob('*.json')):
        try:
            daily.update(json.loads(jp.read_text()))
        except Exception as e:  # noqa: BLE001
            print('WARN skipping', jp.name, e, file=sys.stderr)
    daily = {k: v for k, v in daily.items() if k in exfiles}
    js_daily = 'Object.assign(EXERCISES, ' + json.dumps(daily, ensure_ascii=False).replace('</', '<\\/') + ');\n'
    js = '\n'.join([
        js_ex,
        (SRC / 'data.js').read_text(),
        js_daily,
        (SRC / 'ide.js').read_text(),
        (SRC / 'play.js').read_text(),
        (SRC / 'katas.js').read_text(),
        (SRC / 'guide.js').read_text(),
        (SRC / 'workspace.js').read_text(),
        """
Workspace.init();
Guide.init();
const warm = () => loadLibs().catch(() => {});
if ('requestIdleCallback' in window) requestIdleCallback(warm, { timeout: 4000 }); else setTimeout(warm, 1500);
""",
    ])
    order = ['css1', 'css2', 'css3', 'react1', 'react2', 'react3', 'react4', 'react5', 'js', 'pipeline', 'gotchas', 'staff1', 'staff2', 'staff3', 'staff4', 'staff5', 'staff6', 'staff7', 'staff8']
    lessons = '\n'.join((SRC / 'lessons' / f'{n}.html').read_text() for n in order)
    LEVELS = [
        (1, 'Level 1 · Foundations', '10–15 min. One concept each. Do these until they feel automatic.'),
        (2, 'Level 2 · Everyday features', '15–20 min. Loading data, forms, modals, lists with interactions.'),
        (3, 'Level 3 · Real interview size', '20–30 min. The size of a real 30-minute round.'),
        (4, 'Level 4 · Complex features', '30–40 min. Several pieces of state working together.'),
        (5, 'Level 5 · Staff-level', '40–45 min. Keyboard, accessibility, performance, edge cases.'),
    ]
    sections = []
    for lv, title, blurb in LEVELS:
        ids = sorted([k for k, v in daily.items() if v.get('level') == lv], key=lambda k: daily[k].get('order', 0))
        if ids:
            sections.append(f'<h2>{title}</h2><p>{blurb}</p><div data-exs="{",".join(ids)}"></div>')
    tpl_daily = ('<template id="tpl-daily"><h1>Daily challenges</h1>'
                 '<p class="lede">One a day, in order. All TypeScript, all inside an existing app, all with a mock API that has a random delay, like the real round. '
                 'Write it without AI, with the timer on. Look things up on MDN or Google the way you would in the interview.</p>'
                 '<div class="callout"><span class="callout-label">The daily loop</span><p>Read the task (2 min) · say your plan out loud · build Core first · '
                 'tick the self-review honestly · only then open the Solution tab. If you finish well under time, move up a level. '
                 'If you blow way past it, redo the same challenge tomorrow from scratch.</p></div>'
                 + ''.join(sections) + '</template>')
    html = (SRC / 'head.html').read_text() + extra_head + '\n' + (SRC / 'body.html').read_text() + '\n' + lessons + '\n' + tpl_daily + '\n<script>\n' + js + '\n</script>\n'
    pathlib.Path(out_path).write_text(html)
    return exfiles


if __name__ == '__main__':
    ex = build(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'dist' / 'index.html'))
    print('exercises:', ', '.join(ex.keys()))
