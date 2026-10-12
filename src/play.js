/* ================= Inline lesson playgrounds ================= */
const PLAY_INDEX = `import React from 'react';
import { createRoot } from 'react-dom/client';
import './base.css';
import './styles.css';
import App from './App';

createRoot(document.getElementById('root')).render(<App />);
`;
const PLAY_BASE_CSS = `body { margin: 12px; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; font-size: 15px; color: #1A1F2B; }
button { font: inherit; }`;

const Play = (() => {
  const live = [];
  let active = null;
  let seq = 0;

  function parse(src) {
    const text = src.replace(/^\n/, '').replace(/\s+$/, '') + '\n';
    const parts = text.split(/^\/\*\*\* css \*\*\*\/\n/m);
    return { 'src/App.jsx': parts[0].replace(/\s+$/, '') + '\n', 'src/styles.css': (parts[1] || '').replace(/\s+$/, '') + '\n' };
  }

  function mount(scriptEl) {
    const id = ++seq;
    const base = parse(scriptEl.textContent);
    const hasCss = base['src/styles.css'].trim().length > 0;
    const title = scriptEl.dataset.title || 'Try it';
    const h = Number(scriptEl.dataset.h || 240);
    const ph = scriptEl.dataset.ph ? Number(scriptEl.dataset.ph) : null;
    const showConsole = scriptEl.dataset.console !== 'off';
    const files = { ...base };
    let current = 'src/App.jsx';

    const wrap = document.createElement('div');
    wrap.className = 'play';
    wrap.innerHTML = `
      <div class="play-bar">
        <span class="play-title">▶ ${esc(title)}</span>
        <div class="play-tabs">
          <button class="play-tab is-on" data-f="src/App.jsx">App.jsx</button>
          ${hasCss ? '<button class="play-tab" data-f="src/styles.css">styles.css</button>' : ''}
        </div>
        <span class="play-status"></span>
        <button class="play-btn" data-act="run" title="Run again (Ctrl/⌘ + S)">Run again</button>
        <button class="play-btn" data-act="reset" title="Undo your edits">Reset</button>
      </div>
      <div class="play-editor" style="height:${h}px"></div>
      <div class="play-out">
        <div class="play-label">Preview <span>· edits re-run automatically</span></div>
        <div class="play-preview" ${ph ? `style="height:${ph}px"` : ''}><div class="play-host"></div><div class="play-msg">Loading React…</div></div>
        ${showConsole ? `<div class="play-label play-console-label">Console <button class="play-clear" data-act="clear">Clear</button></div><div class="play-console"></div>` : ''}
      </div>`;
    scriptEl.replaceWith(wrap);

    const statusEl = wrap.querySelector('.play-status');
    const msg = wrap.querySelector('.play-msg');
    const consoleEl = wrap.querySelector('.play-console');
    let lines = [];
    let rt = null;
    let timer = null;

    const renderConsole = () => {
      if (!consoleEl) return;
      consoleEl.innerHTML = lines.length
        ? lines.map((l) => `<div class="pc-${l.level}">${l.count > 1 ? `<span class="pc-n">${l.count}</span>` : ''}${esc(l.text)}</div>`).join('')
        : '<div class="pc-empty">console.log output shows here.</div>';
      consoleEl.scrollTop = consoleEl.scrollHeight;
    };
    const log = (level, text) => {
      const all = String(text).split('\n'); const t = all.slice(0, 200).join('\n') + (all.length > 200 ? `\n… ${all.length - 200} more lines` : '');
      const last = lines[lines.length - 1];
      if (last && last.text === t && last.level === level) last.count++;
      else lines.push({ level, text: t, count: 1 });
      if (lines.length > 80) lines = lines.slice(-80);
      renderConsole();
    };
    const showError = (err) => {
      const text = String((err && err.message) || err).split('\n').slice(0, 10).join('\n');
      msg.hidden = false;
      msg.className = 'play-msg is-err';
      msg.textContent = (err && err.isCompile ? 'Syntax error\n\n' : 'Error\n\n') + text;
      statusEl.textContent = err && err.isCompile ? 'Syntax error' : 'Error';
      statusEl.className = 'play-status is-err';
    };
    const inst = { id, log, showError, wrap, destroy: () => { clearTimeout(timer); if (rt) rt.reset(); } };

    const run = () => {
      clearTimeout(timer);
      if (!window.React || !window.Babel) {
        loadLibs().then(run).catch(() => {
          msg.hidden = false;
          msg.className = 'play-msg is-err';
          msg.textContent = 'Could not load React from the CDN. Check your connection or ad blocker.';
        });
        return;
      }
      if (!rt) rt = new Runtime(wrap.querySelector('.play-host'), { onLog: log });
      lines = [];
      renderConsole();
      msg.hidden = true;
      msg.className = 'play-msg';
      statusEl.textContent = '';
      statusEl.className = 'play-status';
      const prev = active;
      active = inst;
      const err = rt.run({ 'src/index.jsx': PLAY_INDEX, 'src/base.css': PLAY_BASE_CSS, ...files });
      if (err) showError(err);
      else { statusEl.textContent = 'Running'; statusEl.className = 'play-status is-ok'; }
      if (prev && prev !== inst && !wrap.contains(document.activeElement)) active = prev;
    };

    const editor = new CodeEditor(wrap.querySelector('.play-editor'), {
      id: 'play-' + id,
      onChange: (v) => {
        files[current] = v;
        clearTimeout(timer);
        statusEl.textContent = 'Editing…';
        statusEl.className = 'play-status';
        timer = setTimeout(run, 650);
      },
      onRun: run,
      onCursor: () => {},
    });
    editor.ta.setAttribute('aria-label', `${title} code editor`);
    editor.setValue(files[current], langFor(current), false);

    wrap.addEventListener('pointerdown', () => { active = inst; });
    wrap.addEventListener('focusin', () => { active = inst; });
    wrap.addEventListener('click', (e) => {
      const tab = e.target.closest('[data-f]');
      if (tab) {
        current = tab.dataset.f;
        wrap.querySelectorAll('.play-tab').forEach((b) => b.classList.toggle('is-on', b === tab));
        editor.setValue(files[current], langFor(current), false);
        return;
      }
      const act = e.target.closest('[data-act]');
      if (!act) return;
      if (act.dataset.act === 'reset') {
        Object.assign(files, base);
        editor.setValue(files[current], langFor(current), false);
        run();
      }
      if (act.dataset.act === 'clear') { lines = []; renderConsole(); }
      if (act.dataset.act === 'run') run();
    });

    live.push(inst);
    // Run when scrolled near, so a long lesson doesn't boot every example at once
    const io = new IntersectionObserver((entries) => {
      if (entries.some((en) => en.isIntersecting)) { io.disconnect(); run(); }
    }, { rootMargin: '300px' });
    io.observe(wrap);
    inst.io = io;
    renderConsole();
  }

  function unmountAll() {
    live.splice(0).forEach((p) => { if (p.io) p.io.disconnect(); p.destroy(); });
    active = null;
  }

  /* ---- route console.error / warn and uncaught errors to whoever is showing code ---- */
  const route = (level, args) => {
    const text = fmtArgs(args);
    if (typeof Workspace !== 'undefined' && Workspace.isOpen()) Workspace.log(level, text);
    else if (active) active.log(level, text);
  };
  console.error = (...a) => { ORIG_CONSOLE.error.apply(console, a); route('error', a); };
  console.warn = (...a) => { ORIG_CONSOLE.warn.apply(console, a); route('warn', a); };
  window.addEventListener('error', (e) => {
    if ((typeof Workspace !== 'undefined' && Workspace.isOpen()) || !active) return;
    const err = e.error || new Error(e.message || 'Unknown error');
    active.log('error', `Uncaught ${err.name || 'Error'}: ${err.message}`);
    active.showError(err);
    if (e.preventDefault) e.preventDefault();
  });

  return { mount, unmountAll };
})();

/* ================= Layout explorer (flex / grid) ================= */
const EXPLORERS = {
  flex: {
    items: ['Logo', 'Docs', 'Pricing about us', 'Sign in'],
    base: { display: 'flex' },
    controls: [
      ['flex-direction', ['row', 'column']],
      ['justify-content', ['flex-start', 'center', 'flex-end', 'space-between', 'space-around', 'space-evenly']],
      ['align-items', ['stretch', 'flex-start', 'center', 'flex-end', 'baseline']],
      ['gap', ['0', '8px', '16px', '32px']],
      ['flex-wrap', ['nowrap', 'wrap']],
    ],
    defaults: { 'flex-direction': 'row', 'justify-content': 'flex-start', 'align-items': 'stretch', gap: '8px', 'flex-wrap': 'nowrap' },
    itemStyle: (i) => `padding:${[8, 14, 8, 20][i]}px 12px;`,
    child: { label: 'Item 3 gets', options: ['nothing', 'flex: 1', 'margin-left: auto', 'align-self: center'] },
  },
  grid: {
    items: ['1', '2', '3', '4', '5', '6', '7'],
    base: { display: 'grid' },
    controls: [
      ['grid-template-columns', ['1fr 1fr 1fr', 'repeat(4, 1fr)', '200px 1fr', '1fr 2fr', 'repeat(auto-fill, minmax(120px, 1fr))']],
      ['gap', ['0', '8px', '16px']],
      ['justify-items', ['stretch', 'start', 'center', 'end']],
      ['align-items', ['stretch', 'start', 'center', 'end']],
    ],
    defaults: { 'grid-template-columns': '1fr 1fr 1fr', gap: '8px', 'justify-items': 'stretch', 'align-items': 'stretch' },
    itemStyle: (i) => `padding:${i === 1 ? 24 : 10}px 10px;`,
    child: { label: 'Item 1 gets', options: ['nothing', 'grid-column: span 2', 'grid-column: 1 / -1', 'grid-row: span 2'] },
  },
};

function mountExplorer(el) {
  const cfg = EXPLORERS[el.dataset.explorer];
  const state = { ...cfg.defaults };
  let child = 'nothing';
  const childIdx = el.dataset.explorer === 'flex' ? 2 : 0;
  el.className = 'explorer';
  const sid = 'ex-' + el.dataset.explorer;
  el.innerHTML = `
    <div class="explorer-controls">
      ${cfg.controls.map(([prop, opts]) => `<label><span>${prop}</span><select id="${sid}-${prop}" data-prop="${prop}">${opts.map((o) => `<option ${o === state[prop] ? 'selected' : ''}>${o}</option>`).join('')}</select></label>`).join('')}
      <label><span>${cfg.child.label}</span><select id="${sid}-child" data-child="1">${cfg.child.options.map((o) => `<option>${o}</option>`).join('')}</select></label>
    </div>
    <div class="explorer-stage"><div class="explorer-box"></div><div class="explorer-axis" aria-hidden="true"></div></div>
    <div class="snippet"><div class="snippet-bar"><span>The CSS for what you see</span></div><pre class="explorer-code"></pre></div>`;
  const box = el.querySelector('.explorer-box');
  const axis = el.querySelector('.explorer-axis');
  const code = el.querySelector('.explorer-code');
  const render = () => {
    const css = { ...cfg.base, ...state };
    box.setAttribute('style', Object.entries(css).map(([k, v]) => `${k}:${v}`).join(';'));
    box.innerHTML = cfg.items.map((t, i) => {
      const extra = i === childIdx && child !== 'nothing' ? child + ';' : '';
      return `<div class="explorer-item ${i === childIdx && child !== 'nothing' ? 'is-picked' : ''}" style="${cfg.itemStyle(i)}${extra}">${esc(t)}</div>`;
    }).join('');
    if (el.dataset.explorer === 'flex') {
      const col = state['flex-direction'] === 'column';
      axis.innerHTML = `<span class="ax-main">Main axis → ${col ? '↓ (column)' : '→ (row)'} · justify-content</span><span class="ax-cross">Cross axis ${col ? '→' : '↓'} · align-items</span>`;
    } else {
      axis.innerHTML = '<span class="ax-main">Columns are defined on the parent; items fill cells left to right, then wrap to a new row</span>';
    }
    const lines = Object.entries(css).map(([k, v]) => `  ${k}: ${v};`).join('\n');
    let txt = `.parent {\n${lines}\n}`;
    if (child !== 'nothing') txt += `\n\n.${el.dataset.explorer === 'flex' ? 'item-3' : 'item-1'} {\n  ${child};\n}`;
    code.innerHTML = highlight(txt, 'css');
  };
  el.addEventListener('change', (e) => {
    const s = e.target;
    if (s.dataset.prop) state[s.dataset.prop] = s.value;
    if (s.dataset.child) child = s.value;
    render();
  });
  render();
}
