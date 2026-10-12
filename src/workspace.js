/* ================= Workspace controller ================= */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

let toastTimer = null;
function toast(html, ms = 3200) {
  const t = $('#toast');
  t.innerHTML = html;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, ms);
}

function copyText(text, label) {
  const done = () => toast(`Copied ${esc(label || 'to clipboard')}`, 1600);
  try {
    navigator.clipboard.writeText(text).then(done, () => toast('Copy failed. Select the text and copy it manually.'));
  } catch (e) {
    toast('Copy failed. Select the text and copy it manually.');
  }
}

function filesFor(id, role) {
  const f = EXFILES[id];
  if (role === 'solution') return { ...f.shared, ...f.starter, ...f.solution };
  return { ...f.shared, ...f.starter };
}

function speedFiles(id) {
  const files = filesFor(id, 'starter');
  Object.keys(EXFILES[id].starter).forEach((p) => {
    if (!/\.[jt]sx?$/.test(p)) return;
    const name = p.split('/').pop().replace(/\.[jt]sx?$/, '');
    files[p] = `import React, { useState, useEffect } from 'react';\n\n// Speed run: build this from memory. Requirements are in the Task tab.\nexport default function ${name}() {\n  return null;\n}\n`;
  });
  return files;
}

const SVG = {
  panel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>',
  reload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  reset: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5v14l12-7z"/></svg>',
};

const Workspace = (() => {
  let ex = null;
  let exId = null;
  let key = null;
  let speed = false;
  let base = {};
  let files = {};
  let openTabs = [];
  let active = null;
  let editor = null;
  let runtime = null;
  let designRt = null;
  let inspector = null;
  let designFor = null;
  let isOpen = false;
  let saveTimer = null;
  let runTimer = null;
  let autoRun = Progress.pref('autoRun', true);
  let collapsed = new Set();
  let consoleEntries = [];
  let errCount = 0;
  let bottomTab = 'terminal';
  let solRevealed = false;
  const timer = { limit: 0, elapsed: 0, running: false, handle: null, changeAt: null, changeShown: false };

  /* ---------- open / close ---------- */
  function open(id, opts = {}) {
    ex = EXERCISES[id];
    exId = id;
    speed = !!opts.speed;
    key = id + (speed ? '~speed' : '');
    base = speed ? speedFiles(id) : filesFor(id, 'starter');
    files = Progress.get('files:' + key) || { ...base };
    if (!files['src/index.jsx']) files['src/index.jsx'] = base['src/index.jsx'];
    collapsed = new Set();
    solRevealed = false;
    designFor = null;
    const focus = files[ex.focus] != null ? ex.focus : 'src/App.jsx';
    openTabs = [...new Set([focus, files['src/App.jsx'] != null && focus !== 'src/App.jsx' ? 'src/App.jsx' : null].filter(Boolean))];
    if (speed) openTabs = Object.keys(EXFILES[id].starter).filter((p) => /\.[jt]sx?$/.test(p));
    active = openTabs[0];

    $('#ideKind').textContent = speed ? 'Speed run' : ex.level ? 'Daily · Level ' + ex.level : ex.kind === 'mock' ? 'Mock interview' : ex.kind === 'curveball' ? 'Curveball' : 'Drill';
    $('#ideTitle').textContent = ex.title;
    if (Progress.exStatus(key) !== 'done') Progress.setEx(key, 'started');

    const durations = durationChoices();
    setTimer(durations[0]);

    renderTree();
    renderTabs();
    openFile(active);
    showPaneTab('task');
    renderTask();
    $('#solView').innerHTML = '';
    setView('code');

    $('#ide').hidden = false;
    document.body.classList.add('ide-open');
    isOpen = true;
    patchConsole(true);

    consoleEntries = [];
    errCount = 0;
    renderConsole();
    term([], true);
    term([
      ['prompt', '$ npm start'],
      ['muted', '> workspace@1.0.0 start'],
      ['muted', '> react-scripts start'],
      ['', ''],
      ['info', 'Starting the development server...'],
    ]);
    showBottomTab('terminal');
    run();
    setTimeout(() => editor.focus(), 50);
  }

  function close() {
    flushSave();
    stopTimer();
    isOpen = false;
    patchConsole(false);
    if (runtime) runtime.reset();
    $('#ide').hidden = true;
    document.body.classList.remove('ide-open');
    if (window.Guide) Guide.refresh();
  }

  function durationChoices() {
    if (speed) return [ex.minutes + 5, ex.minutes, ex.minutes + 10];
    if (ex.kind === 'mock') return [ex.minutes, 45, 60, 90].filter((v, i, a) => a.indexOf(v) === i);
    if (ex.kind === 'curveball') return [ex.minutes, 20, 45];
    return [ex.minutes, 10, 15, 20, 30, 45].filter((v, i, a) => a.indexOf(v) === i);
  }

  /* ---------- console mirroring ---------- */
  // console.error / console.warn are routed here by the global console sink (play.js)
  function patchConsole() {}

  /* ---------- files ---------- */
  function scheduleSave() {
    clearTimeout(saveTimer);
    $('#sbSave').textContent = 'Saving…';
    saveTimer = setTimeout(flushSave, 400);
  }
  function flushSave() {
    clearTimeout(saveTimer);
    if (!key) return;
    Progress.set('files:' + key, files);
    const s = $('#sbSave');
    if (s) s.textContent = 'All changes saved';
  }

  function openFile(path) {
    if (files[path] == null) return;
    if (!openTabs.includes(path)) openTabs.push(path);
    active = path;
    $('#editorEmpty').hidden = true;
    editor.setValue(files[path], langFor(path), false);
    $('#sbLang').textContent = path.endsWith('.tsx') ? 'TypeScript React' : path.endsWith('.ts') ? 'TypeScript' : { jsx: 'JavaScript React', js: 'JavaScript', css: 'CSS', json: 'JSON' }[langFor(path)];
    renderTabs();
    renderTree();
    setView('code');
  }

  function closeTab(path) {
    openTabs = openTabs.filter((p) => p !== path);
    if (active === path) {
      active = openTabs[openTabs.length - 1] || null;
      if (active) openFile(active);
      else { $('#editorEmpty').hidden = false; renderTabs(); renderTree(); }
    } else {
      renderTabs();
    }
  }

  function renderTabs() {
    const wrap = $('#fileTabs');
    wrap.innerHTML = openTabs.map((p) => `
      <button class="tab ${p === active ? 'is-active' : ''}" data-path="${esc(p)}" title="${esc(p)}">
        <span class="ft ft-${p.split('.').pop()}">${p.split('.').pop().toUpperCase()}</span>${esc(p.split('/').pop())}
        <span class="tab-close" data-close="${esc(p)}" role="button" aria-label="Close ${esc(p)}">×</span>
      </button>`).join('');
    const sel = $('#fileSwitch');
    sel.innerHTML = Object.keys(files).sort().map((p) => `<option value="${esc(p)}" ${p === active ? 'selected' : ''}>${esc(p)}</option>`).join('');
  }

  function buildTree() {
    const root = { dirs: {}, files: [] };
    Object.keys(files).sort().forEach((p) => {
      const parts = p.split('/');
      let node = root;
      parts.slice(0, -1).forEach((d, i) => {
        const full = parts.slice(0, i + 1).join('/');
        node.dirs[d] = node.dirs[d] || { path: full, dirs: {}, files: [] };
        node = node.dirs[d];
      });
      node.files.push(p);
    });
    return root;
  }

  function renderTree() {
    const tree = buildTree();
    let html = '';
    const walk = (node, depth) => {
      Object.keys(node.dirs).sort().forEach((name) => {
        const d = node.dirs[name];
        const isCol = collapsed.has(d.path);
        html += `<button class="tree-row is-dir" data-dir="${esc(d.path)}" style="padding-left:${8 + depth * 12}px"><span class="ic">${isCol ? '▸' : '▾'}</span><span class="name">${esc(name)}</span></button>`;
        if (!isCol) walk(d, depth + 1);
      });
      node.files.forEach((p) => {
        const ext = p.split('.').pop();
        const userMade = base[p] == null;
        html += `<div class="tree-row ${p === active ? 'is-active' : ''}" role="button" tabindex="0" data-file="${esc(p)}" style="padding-left:${8 + depth * 12 + 14}px"><span class="ft ft-${ext}">${ext.toUpperCase()}</span><span class="name">${esc(p.split('/').pop())}</span>${userMade ? `<span class="icon-btn" style="margin-left:auto;width:20px;height:20px" data-del="${esc(p)}" title="Delete file">×</span>` : ''}</div>`;
      });
    };
    walk(tree, 0);
    $('#tree').innerHTML = html;
  }

  function startNewFile() {
    const box = $('#newFile');
    box.hidden = false;
    $('#newFileErr').hidden = true;
    const input = $('#newFileInput');
    input.value = 'components/';
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  }
  function commitNewFile() {
    const input = $('#newFileInput');
    let p = input.value.trim().replace(/^\.?\//, '');
    if (!p.startsWith('src/')) p = 'src/' + p;
    const err = (m) => { $('#newFileErr').textContent = m; $('#newFileErr').hidden = false; };
    if (!/^[\w./-]+\.(jsx|js|tsx|ts|css)$/.test(p)) return err('Use a name ending in .jsx, .js, .tsx, .ts or .css (no spaces).');
    if (files[p] != null) return err('That file already exists.');
    const name = p.split('/').pop().replace(/\.\w+$/, '');
    files[p] = /\.[jt]sx$/.test(p)
      ? `import React from 'react';\n\nexport default function ${name.replace(/[^\w]/g, '')}() {\n  return <div></div>;\n}\n`
      : '';
    $('#newFile').hidden = true;
    scheduleSave();
    openFile(p);
  }

  /* ---------- editor events ---------- */
  function onEdit(value) {
    if (!active) return;
    files[active] = value;
    scheduleSave();
    if (autoRun) {
      clearTimeout(runTimer);
      runTimer = setTimeout(run, 900);
    }
  }

  /* ---------- run ---------- */
  function run() {
    clearTimeout(runTimer);
    flushSave();
    $('#errOverlay').hidden = true;
    const loading = $('#previewLoading');
    if (!window.React || !window.ReactDOM || !window.Babel) {
      loading.hidden = false;
      loading.textContent = 'Loading React and the compiler…';
      loadLibs().then(() => { loading.hidden = true; run(); }).catch(() => {
        loading.innerHTML = 'Could not load React from the CDN.<br>Check your connection or ad blocker, then press Run.';
        term([['err', 'Failed to load react / react-dom / babel from the CDN.']]);
      });
      return;
    }
    loading.hidden = true;
    if (!runtime) runtime = new Runtime($('#previewHost'), { onLog: addConsole });
    consoleEntries = [];
    errCount = 0;
    renderConsole();
    const t0 = performance.now();
    term([['info', 'Compiling...']]);
    const err = runtime.run(files);
    const ms = Math.max(1, Math.round(performance.now() - t0));
    if (err) {
      showError(err);
      if (err.isCompile) {
        term([['err', 'Failed to compile.'], ['', ''], ['err', cleanMsg(err)], ['', '']]);
        $('#sbBuild').innerHTML = '<span class="bad">● Failed to compile</span>';
      } else {
        term([['ok', `Compiled successfully in ${ms}ms`], ['warn', 'Runtime error while loading modules. See the preview.']]);
        addConsole('error', `Uncaught ${err.name || 'Error'}: ${err.message}`);
        $('#sbBuild').innerHTML = '<span class="bad">● Runtime error</span>';
      }
    } else {
      term([['ok', 'Compiled successfully!'], ['muted', `webpack compiled in ${ms} ms · http://localhost:3000`], ['', '']]);
      $('#sbBuild').innerHTML = '<span class="ok">● Compiled</span>';
    }
  }

  function cleanMsg(err) {
    return String(err.message || err).replace(/^\/?/, '').split('\n').slice(0, 16).join('\n');
  }

  function showError(err, runtimeErr) {
    const o = $('#errOverlay');
    const title = err && err.isCompile ? 'Failed to compile' : 'Uncaught runtime error';
    o.innerHTML = `<div class="err-head"><h4>${title}</h4><button class="icon-btn" id="errClose" aria-label="Dismiss">×</button></div><pre>${esc(cleanMsg(err))}</pre><p class="err-foot">${err && err.isCompile ? 'Fix the error and save. The preview rebuilds automatically.' : 'Check the Console tab for details. Fix the code and save, or press Run.'}</p>`;
    o.hidden = false;
    if (runtimeErr) $('#sbBuild').innerHTML = '<span class="bad">● Runtime error</span>';
  }

  function onWindowError(e) {
    if (!isOpen) return;
    const err = e.error || new Error(e.message || 'Unknown error');
    if (e.preventDefault) e.preventDefault();
    addConsole('error', `Uncaught ${err.name || 'Error'}: ${err.message}`);
    showError(err, true);
  }
  window.addEventListener('error', onWindowError);
  window.addEventListener('unhandledrejection', (e) => {
    if (!isOpen) return;
    const r = e.reason;
    addConsole('error', `Uncaught (in promise) ${r && r.name ? r.name + ': ' + r.message : fmtVal(r)}`);
  });

  /* ---------- terminal + console ---------- */
  let termLines = [];
  function term(lines, reset) {
    if (reset) termLines = [];
    termLines.push(...lines);
    if (termLines.length > 400) termLines = termLines.slice(-400);
    const view = $('#termView');
    view.innerHTML = termLines.map(([cls, text]) => `<div class="${cls === 'prompt' ? 'prompt' : cls ? 'l-' + cls : ''}">${esc(text) || '&nbsp;'}</div>`).join('');
    view.scrollTop = view.scrollHeight;
  }

  function addConsole(level, text) {
    const all = String(text).split('\n'); const t = all.slice(0, 200).join('\n') + (all.length > 200 ? `\n… ${all.length - 200} more lines` : '');
    const last = consoleEntries[consoleEntries.length - 1];
    if (last && last.text === t && last.level === level) last.count++;
    else consoleEntries.push({ level, text: t, count: 1 });
    if (consoleEntries.length > 300) consoleEntries.shift();
    if (level === 'error') errCount++;
    renderConsole();
  }
  function renderConsole() {
    const view = $('#consoleView');
    if (!view) return;
    view.innerHTML = consoleEntries.length
      ? consoleEntries.map((c) => `<div class="l-row ${c.level === 'error' ? 'l-err' : c.level === 'warn' ? 'l-warn' : ''}">${c.count > 1 ? `<span class="l-count">${c.count}</span>` : ''}${esc(c.text)}</div>`).join('')
      : '<div class="l-muted">console.log output and React warnings appear here.</div>';
    view.scrollTop = view.scrollHeight;
    const badge = $('#consoleBadge');
    const n = consoleEntries.reduce((s, c) => s + c.count, 0);
    badge.textContent = n;
    badge.hidden = n === 0;
    badge.style.background = errCount ? 'var(--ide-red)' : '';
    badge.style.color = errCount ? '#fff' : '';
  }
  function showBottomTab(name) {
    bottomTab = name;
    $$('[data-btab]').forEach((b) => b.classList.toggle('is-active', b.dataset.btab === name));
    $('#termView').hidden = name !== 'terminal';
    $('#consoleView').hidden = name !== 'console';
  }

  /* ---------- timer ---------- */
  function setTimer(minutes) {
    stopTimer();
    timer.limit = minutes * 60;
    timer.elapsed = 0;
    timer.changeShown = false;
    timer.changeAt = ex.change ? Math.round(timer.limit * (ex.changeAt / ex.minutes)) : null;
    $('#timerLen').textContent = minutes + ' min';
    renderTimer();
  }
  function renderTimer() {
    const left = timer.limit - timer.elapsed;
    const abs = Math.abs(left);
    const s = `${left < 0 ? '+' : ''}${String(Math.floor(abs / 60)).padStart(2, '0')}:${String(abs % 60).padStart(2, '0')}`;
    $('#timerVal').textContent = s;
    const el = $('#timer');
    el.classList.toggle('is-low', left > 0 && left <= Math.min(600, timer.limit * 0.2));
    el.classList.toggle('is-over', left <= 0 && timer.limit > 0);
    $('#timerToggle').textContent = timer.running ? 'Pause' : timer.elapsed ? 'Resume' : 'Start';
  }
  function startTimer() {
    if (timer.running) return;
    timer.running = true;
    timer.handle = setInterval(() => {
      timer.elapsed++;
      if (timer.changeAt != null && !timer.changeShown && timer.elapsed >= timer.changeAt) revealChange(true);
      if (timer.elapsed === timer.limit) toast('<b>Time.</b> Wrap up and walk through what you built, then do the self-review in the Task tab.', 6000);
      renderTimer();
    }, 1000);
    renderTimer();
  }
  function stopTimer() {
    timer.running = false;
    clearInterval(timer.handle);
    if ($('#timerVal')) renderTimer();
  }

  function revealChange(fromTimer) {
    timer.changeShown = true;
    const box = $('#changeBox');
    if (!box) return;
    box.classList.add('is-live');
    box.innerHTML = `<h4>New requirement: ${esc(ex.change.title)}</h4>${ex.change.html}<p style="margin-top:10px;color:var(--ide-muted);font-size:13px">Pause, say how this fits into what you have, then make the smallest change that does it.</p>`;
    if (fromTimer) {
      toast(`<b>Interviewer:</b> one more requirement. See the Task tab.`, 6000);
      const dot = $('[data-ptab="task"] .dot');
      if (dot && !$('[data-ptab="task"]').classList.contains('is-active')) dot.hidden = false;
    }
  }

  /* ---------- left pane: task / design / solution ---------- */
  function showPaneTab(name) {
    if (name !== 'design') $('#paneTask').classList.remove('is-wide');
    $$('[data-ptab]').forEach((b) => b.classList.toggle('is-active', b.dataset.ptab === name));
    $$('[data-pview]').forEach((v) => { v.hidden = v.dataset.pview !== name; });
    if (name === 'task') { const dot = $('[data-ptab="task"] .dot'); if (dot) dot.hidden = true; }
    if (name === 'design') renderDesign();
    if (name === 'solution') renderSolution();
  }

  function renderTask() {
    const req = Progress.get('req:' + key) || [];
    const rub = Progress.get('rub:' + key) || [];
    const done = Progress.exStatus(key) === 'done';
    const kind = speed ? 'Speed run' : ex.level ? 'Daily challenge · Level ' + ex.level : ex.kind === 'mock' ? 'Mock interview' : ex.kind === 'curveball' ? 'Curveball' : 'Drill';
    const mins = durationChoices()[0];
    let html = `<div class="task-meta"><span>${kind} · ${mins} min</span><span>Start in ${esc(speed ? openTabs.join(', ') : ex.focus)}</span></div>
      <h2>${esc(ex.title)}</h2>`;
    if (speed) {
      html += `<p><b>From memory, no peeking.</b> The component files are blank. Data and CSS are still there. Rebuild the whole thing against the clock. If you stall, that's the pattern to drill again.</p>`;
    } else {
      html += ex.brief;
    }
    if (ex.lookups && !speed) {
      const plan = Progress.get('plan:' + key) || '';
      html += `<h3>Lookup plan · before you code</h3>
        <p style="font-size:13px;color:var(--ide-muted)">One line per requirement: the <b>name</b> of the thing, then the <b>query</b> you'd type. Unsure of a name? Write the plain-words description; that's a valid first search.</p>
        <textarea id="lookupPlan" rows="6" placeholder="relative time → Intl.RelativeTimeFormat → &quot;js relative time format mdn&quot;" style="width:100%;background:var(--ide-bg);color:var(--ide-text);border:1px solid var(--ide-line);border-radius:6px;padding:8px;font:12px/1.5 var(--font-mono)">${esc(plan)}</textarea>
        <details class="details"><summary>Compare with a reference lookup plan</summary><div>
          <p style="font-size:12px;color:var(--ide-muted);margin-top:4px">Each search link opens Google in a new tab, so you can see what the query actually returns.</p>
          <ul style="list-style:none;padding:0;display:grid;gap:8px">${ex.lookups.map(([need, name, q]) => `<li style="font-size:13px"><b>${esc(need)}</b><br><span style="color:var(--ide-muted)">${esc(name)}</span><br><a href="https://www.google.com/search?q=${encodeURIComponent(q)}" target="_blank" rel="noopener" style="color:var(--ide-blue);font-family:var(--font-mono);font-size:12px">${esc(q)} ↗</a></li>`).join('')}</ul>
        </div></details>`;
    }
    html += `<h3>Requirements</h3><ul class="req">${ex.requirements.map((r, i) => {
      const t = ex.tiers ? ex.tiers[i] : '';
      const tc = { Core: '#1C7A43', Next: '#3451D1', Stretch: '#8A8F98' }[t] || '';
      const tag = t ? `<b style="display:inline-block;font-size:10px;letter-spacing:.04em;text-transform:uppercase;color:#fff;background:${tc};border-radius:4px;padding:1px 6px;margin-right:6px">${t}</b>` : '';
      return `<li><label><input type="checkbox" data-req="${i}" ${req.includes(i) ? 'checked' : ''}><span>${tag}${r}</span></label></li>`;
    }).join('')}</ul>`;
    if (ex.change && !speed) {
      html += `<div class="change-box" id="changeBox"><h4 style="color:var(--ide-muted)">Locked: one more requirement</h4>
        <p>Your "interviewer" adds a requirement at about ${Math.round((timer.changeAt || 0) / 60)} minutes in. Start the timer and keep going, or reveal it now.</p>
        <button class="ide-btn" id="revealChange">Reveal now</button></div>`;
    }
    if (!speed) {
      html += `<details class="details"><summary>Hints</summary><div><ul>${ex.hints.map((h) => `<li>${h}</li>`).join('')}</ul></div></details>`;
    }
    html += `<h3>Self-review</h3><p style="color:var(--ide-muted);font-size:13px">Tick what's true when time is up. This is roughly what an interviewer notes.</p>
      <ul class="req">${ex.rubric.map((r, i) => `<li><label><input type="checkbox" data-rub="${i}" ${rub.includes(i) ? 'checked' : ''}><span>${r}</span></label></li>`).join('')}</ul>`;
    if (ex.kind === 'mock' && !speed) {
      const deb = Progress.get('debrief:' + key) || '';
      html += `<h3>Debrief</h3>
        <p style="font-size:13px;color:var(--ide-muted)">Where did time bleed? Syntax recall, CSS guesswork, state design, reading the codebase, or debugging? Then patch that leak:</p>
        <ul style="font-size:13px">
          <li>CSS guesswork → Flexbox lesson, then Profile card, Project cards</li>
          <li>State in the wrong place → Structuring a feature, then Inbox</li>
          <li>Effects, loading, races → Effects and loading data, then Orders</li>
          <li>Forms → Feedback list</li>
          <li>Slow typing of patterns → the speed runs</li>
          <li>Didn't know what to search for → Name it, search it, then a curveball</li>
          <li>Slow orientation → Reading a codebase fast, then redo only the first 5 minutes of this mock</li>
        </ul>
        <textarea id="debrief" rows="4" placeholder="Notes to self…" style="width:100%;background:var(--ide-bg);color:var(--ide-text);border:1px solid var(--ide-line);border-radius:6px;padding:8px;font:13px var(--font-body)">${esc(deb)}</textarea>`;
    }
    html += `<div class="done-btn">${done
      ? `<button class="ide-btn" id="markDone">Done ✓ · Mark as not done</button>`
      : `<button class="ide-btn is-primary" id="markDone">Mark as done</button>`}</div>`;
    $('#taskView').innerHTML = html;
    if (timer.changeShown) revealChange(false);
  }

  function renderDesign() {
    const view = $('[data-pview="design"]');
    if (designFor !== exId) {
      designFor = exId;
      inspector = null;
      const s = ex.spec;
      view.innerHTML = `
        <div class="design-bar">
          <div class="seg" role="group" aria-label="Mode"><button class="is-on" data-dmode="inspect">Inspect</button><button data-dmode="interact">Interact</button></div>
          <span class="design-hint">Target design. In the interview this is a Figma file.</span>
          <button class="ide-btn" id="wideBtn">${$('#paneTask').classList.contains('is-wide') ? 'Collapse' : 'Expand'}</button>
        </div>
        <div class="design-scroll">
          <div class="design-canvas" id="designCanvas"><div class="design-host" id="designHost"></div><div class="preview-loading" id="designLoading">Loading…</div></div>
          <div class="inspect-info" id="inspectInfo"></div>
          <div class="spec">
            <h3>Colors · click to copy</h3>
            <div class="spec-colors">${s.colors.map(([n, hex]) => {
              const sw = hex.split(' ')[0];
              return `<button class="spec-color" data-copy="${esc(sw)}"><span class="swatch" style="background:${esc(sw)}"></span><span>${esc(n)}<small>${esc(hex)}</small></span></button>`;
            }).join('')}</div>
            <h3>Measurements</h3>
            <ul class="spec-list">${s.notes.map(([k, v]) => `<li><span>${esc(k)}</span><span>${esc(v)}</span></li>`).join('')}</ul>
          </div>
        </div>`;
      if (designRt) { designRt.reset(); }
      designRt = null;
    }
    loadLibs().then(() => {
      $('#designLoading').hidden = true;
      if (!designRt) {
        designRt = new Runtime($('#designHost'), {});
        designRt.run(filesFor(exId, 'solution'));
        inspector = new Inspector(designRt, $('#designCanvas'), $('#inspectInfo'));
      }
    }).catch(() => { $('#designLoading').textContent = 'Could not load React from the CDN.'; });
  }

  function renderSolution() {
    const view = $('#solView');
    if (!solRevealed) {
      view.innerHTML = `<div class="sol-gate"><p>Finish first, or at least get stuck for real. Reading a solution feels like learning but builds far less than struggling for 5 more minutes.</p>
        <button class="ide-btn" id="revealSol">Show the reference solution</button></div>`;
      return;
    }
    const sol = filesFor(exId, 'solution');
    const start = filesFor(exId, 'starter');
    const changed = Object.keys(sol).filter((p) => sol[p] !== start[p] && p !== 'src/index.jsx').sort((a, b) => (a.endsWith('.css') ? 1 : 0) - (b.endsWith('.css') ? 1 : 0));
    view.innerHTML = `<p style="color:var(--ide-muted);font-size:13px">One good answer, not the only one. ${ex.change ? 'It includes the mid-session change.' : ''} Compare structure and state placement more than styling details.</p>
      <p><button class="ide-btn" id="loadSol">Load solution into the editor</button> <span id="loadSolNote" style="font-size:12px;color:var(--ide-muted)"></span></p>
      ${changed.map((p) => `<div class="sol-file"><div class="sol-file-head"><span>${esc(p)}</span><button class="icon-btn" style="width:auto;padding:0 8px;font-size:12px" data-copysol="${esc(p)}">Copy</button></div><pre>${highlight(sol[p], langFor(p))}</pre></div>`).join('')}`;
  }

  /* ---------- views (narrow screens) ---------- */
  function setView(v) {
    $('#ideBody').dataset.view = v;
    $$('[data-view-btn]').forEach((b) => b.classList.toggle('is-on', b.dataset.viewBtn === v));
  }

  /* ---------- wiring ---------- */
  function init() {
    editor = new CodeEditor($('#editorArea'), {
      onChange: onEdit,
      onRun: run,
      onCursor: (ln, col) => { $('#sbPos').textContent = `Ln ${ln}, Col ${col}`; },
    });
    $('#ideBack').addEventListener('click', close);
    $('#runBtn').addEventListener('click', run);
    $('#reloadBtn').addEventListener('click', run);
    $('#toggleTask').addEventListener('click', () => $('#paneTask').classList.toggle('is-collapsed'));
    $('#autoRun').checked = autoRun;
    $('#autoRun').addEventListener('change', (e) => { autoRun = e.target.checked; Progress.setPref('autoRun', autoRun); });

    $('#timerToggle').addEventListener('click', () => (timer.running ? stopTimer() : startTimer()));
    $('#timerReset').addEventListener('click', () => setTimer(timer.limit / 60));
    $('#timerLen').addEventListener('click', () => {
      const ch = durationChoices();
      const i = ch.indexOf(timer.limit / 60);
      setTimer(ch[(i + 1) % ch.length]);
      renderTask();
    });

    $('#fileTabs').addEventListener('click', (e) => {
      const c = e.target.closest('[data-close]');
      if (c) { e.stopPropagation(); closeTab(c.dataset.close); return; }
      const t = e.target.closest('[data-path]');
      if (t) openFile(t.dataset.path);
    });
    $('#fileSwitch').addEventListener('change', (e) => openFile(e.target.value));

    $('#tree').addEventListener('click', (e) => {
      const del = e.target.closest('[data-del]');
      if (del) {
        e.stopPropagation();
        const p = del.dataset.del;
        if (del.dataset.armed) {
          delete files[p];
          closeTab(p);
          scheduleSave();
          renderTree();
          run();
        } else {
          del.dataset.armed = '1';
          del.textContent = 'Delete?';
          del.style.width = 'auto';
          setTimeout(() => { if (del.isConnected) { delete del.dataset.armed; del.textContent = '×'; del.style.width = '20px'; } }, 2500);
        }
        return;
      }
      const d = e.target.closest('[data-dir]');
      if (d) { const p = d.dataset.dir; collapsed.has(p) ? collapsed.delete(p) : collapsed.add(p); renderTree(); return; }
      const f = e.target.closest('[data-file]');
      if (f) openFile(f.dataset.file);
    });
    $('#tree').addEventListener('keydown', (e) => {
      const f = e.target.closest('[data-file]');
      if (f && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openFile(f.dataset.file); }
    });
    $('#newFileBtn').addEventListener('click', startNewFile);
    $('#newFileInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); commitNewFile(); }
      if (e.key === 'Escape') { $('#newFile').hidden = true; }
    });
    $('#newFileOk').addEventListener('click', commitNewFile);

    const resetTop = $('#resetTopBtn');
    resetTop.addEventListener('click', () => {
      if (resetTop.dataset.armed) {
        delete resetTop.dataset.armed;
        resetTop.textContent = 'Reset code';
        files = { ...base };
        openTabs = openTabs.filter((p) => files[p] != null);
        if (!openTabs.length) openTabs = [ex.focus in files ? ex.focus : 'src/App.jsx'];
        if (files[active] == null) active = openTabs[0];
        flushSave();
        renderTree();
        openFile(active);
        run();
        toast('Workspace reset to the starter files.');
      } else {
        resetTop.dataset.armed = '1';
        resetTop.textContent = 'Click again to reset';
        setTimeout(() => { if (resetTop.dataset.armed) { delete resetTop.dataset.armed; resetTop.textContent = 'Reset code'; } }, 3000);
      }
    });
    const resetBtn = $('#resetBtn');
    resetBtn.addEventListener('click', () => {
      if (resetBtn.dataset.armed) {
        delete resetBtn.dataset.armed;
        resetBtn.innerHTML = SVG.reset;
        files = { ...base };
        openTabs = openTabs.filter((p) => files[p] != null);
        if (!openTabs.length) openTabs = [ex.focus in files ? ex.focus : 'src/App.jsx'];
        if (files[active] == null) active = openTabs[0];
        flushSave();
        renderTree();
        openFile(active);
        run();
        toast('Workspace reset to the starter files.');
      } else {
        resetBtn.dataset.armed = '1';
        resetBtn.textContent = 'Reset?';
        resetBtn.style.width = 'auto';
        resetBtn.style.padding = '0 6px';
        setTimeout(() => { if (resetBtn.dataset.armed) { delete resetBtn.dataset.armed; resetBtn.innerHTML = SVG.reset; resetBtn.style.width = ''; resetBtn.style.padding = ''; } }, 3000);
      }
    });

    $$('[data-ptab]').forEach((b) => b.addEventListener('click', () => showPaneTab(b.dataset.ptab)));
    $$('[data-btab]').forEach((b) => b.addEventListener('click', () => showBottomTab(b.dataset.btab)));
    $$('[data-view-btn]').forEach((b) => b.addEventListener('click', () => setView(b.dataset.viewBtn)));
    $('#clearBottom').addEventListener('click', () => {
      if (bottomTab === 'console') { consoleEntries = []; errCount = 0; renderConsole(); } else term([], true);
    });

    $('#paneTask').addEventListener('change', (e) => {
      const t = e.target;
      if (t.dataset.req != null || t.dataset.rub != null) {
        const k = (t.dataset.req != null ? 'req:' : 'rub:') + key;
        const i = Number(t.dataset.req != null ? t.dataset.req : t.dataset.rub);
        const list = new Set(Progress.get(k) || []);
        t.checked ? list.add(i) : list.delete(i);
        Progress.set(k, [...list]);
      }
    });
    $('#paneTask').addEventListener('input', (e) => {
      if (e.target.id === 'debrief') Progress.set('debrief:' + key, e.target.value);
      if (e.target.id === 'lookupPlan') Progress.set('plan:' + key, e.target.value);
    });
    $('#paneTask').addEventListener('click', (e) => {
      const t = e.target;
      if (t.id === 'revealChange') revealChange(false);
      if (t.id === 'wideBtn') {
        const wide = $('#paneTask').classList.toggle('is-wide');
        t.textContent = wide ? 'Collapse' : 'Expand';
        if (inspector) inspector.hide();
      }
      if (t.id === 'markDone') {
        const done = Progress.exStatus(key) === 'done';
        Progress.setEx(key, done ? 'started' : 'done');
        if (!done) { stopTimer(); toast('Marked as done. Compare with the Solution tab next.'); }
        renderTask();
      }
      if (t.id === 'revealSol') { solRevealed = true; renderSolution(); }
      const cs = t.closest('[data-copysol]');
      if (cs) copyText(filesFor(exId, 'solution')[cs.dataset.copysol], cs.dataset.copysol);
      const cc = t.closest('[data-copy]');
      if (cc) copyText(cc.dataset.copy, cc.dataset.copy);
      if (t.id === 'loadSol') {
        if (t.dataset.armed) {
          files = { ...filesFor(exId, 'solution') };
          flushSave();
          renderTree();
          openFile(files[active] != null ? active : ex.focus);
          run();
          $('#loadSolNote').textContent = 'Loaded. Reset (in Explorer) brings back the starter.';
          delete t.dataset.armed;
          t.textContent = 'Load solution into the editor';
        } else {
          t.dataset.armed = '1';
          t.textContent = 'This replaces your code. Click again to confirm';
        }
      }
      const dm = t.closest('[data-dmode]');
      if (dm) {
        $$('[data-dmode]').forEach((b) => b.classList.toggle('is-on', b === dm));
        if (inspector) inspector.setOn(dm.dataset.dmode === 'inspect');
      }
    });

    // splitters
    $$('[data-split]').forEach((sp) => {
      sp.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        sp.setPointerCapture(e.pointerId);
        sp.classList.add('is-drag');
        const kind = sp.dataset.split;
        const ide = $('#ide');
        const body = $('#ideBody').getBoundingClientRect();
        const right = $('.pane-right').getBoundingClientRect();
        const move = (ev) => {
          if (kind === 'right') ide.style.setProperty('--right-w', clamp(body.right - ev.clientX, 240, body.width - 380) + 'px');
          if (kind === 'task') ide.style.setProperty('--task-w', clamp(ev.clientX - body.left, 240, 620) + 'px');
          if (kind === 'bottom') ide.style.setProperty('--bottom-h', clamp(right.bottom - ev.clientY, 60, right.height - 140) + 'px');
        };
        const up = () => {
          sp.classList.remove('is-drag');
          sp.removeEventListener('pointermove', move);
          sp.removeEventListener('pointerup', up);
        };
        sp.addEventListener('pointermove', move);
        sp.addEventListener('pointerup', up);
      });
    });

    document.addEventListener('keydown', (e) => {
      if (!isOpen) return;
      if ((e.metaKey || e.ctrlKey) && e.key === 's') { e.preventDefault(); run(); }
    });
  }

  return { init, open, close, isOpen: () => isOpen, log: (level, text) => addConsole(level, text) };
})();
