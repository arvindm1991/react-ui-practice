/* ================= Progress (per-browser) ================= */
const Progress = (() => {
  const K = 'mockprep:';
  const mem = {};
  const get = (k, d = null) => {
    if (k in mem) return mem[k];
    try {
      const v = localStorage.getItem(K + k);
      return v == null ? d : JSON.parse(v);
    } catch (e) {
      return d;
    }
  };
  const set = (k, v) => {
    mem[k] = v;
    try { localStorage.setItem(K + k, JSON.stringify(v)); } catch (e) { /* storage unavailable: memory only */ }
  };
  return {
    get,
    set,
    pref: (k, d) => get('pref:' + k, d),
    setPref: (k, v) => set('pref:' + k, v),
    exStatus: (k) => (get('ex', {}) || {})[k] || null,
    setEx: (k, s) => { const m = get('ex', {}) || {}; m[k] = s; set('ex', m); },
  };
})();

/* ================= Guide ================= */
const MODULES = [
  { id: 'start', group: 'Orientation', title: 'Start here' },
  { id: 'plan', group: 'Orientation', title: 'Your 3-day plan' },
  { id: 'scoring', group: 'Orientation', title: 'What gets scored' },
  { id: 'playbook', group: 'Orientation', title: 'The in-round playbook' },
  { id: 'codebase', group: 'Skills', title: 'Reading a codebase fast' },
  { id: 'figma', group: 'Skills', title: 'Figma to CSS' },
  { id: 'css', group: 'CSS', title: 'Boxes, flow and the cascade' },
  { id: 'flex', group: 'CSS', title: 'Flexbox' },
  { id: 'layout', group: 'CSS', title: 'Grid, positioning, overflow, states' },
  { id: 'react', group: 'React', title: 'Components, JSX and props' },
  { id: 'state', group: 'React', title: 'State and rendering' },
  { id: 'events', group: 'React', title: 'Events, forms and lists' },
  { id: 'effects', group: 'React', title: 'Effects and loading data' },
  { id: 'structure', group: 'React', title: 'Structuring a feature' },
  { id: 'data', group: 'JavaScript', title: 'JavaScript for UI work' },
  { id: 'pipeline', group: 'JavaScript', title: 'Data pipelines' },
  { id: 'katas', group: 'JavaScript', title: 'Data drills' },
  { id: 'lookup', group: 'Looking things up', title: 'Thinking in lookups' },
  { id: 'vocab', group: 'Looking things up', title: 'Lookup vocabulary' },
  { id: 'names', group: 'Practice', title: 'Name it, search it' },
  { id: 'drills', group: 'Practice', title: 'Drills' },
  { id: 'speed', group: 'Practice', title: 'Speed runs' },
  { id: 'mocks', group: 'Practice', title: 'Mock interviews' },
  { id: 'daily', group: 'Practice', title: 'Daily challenges' },
  { id: 'primitives', group: 'Practice', title: 'Primitives reference' },
  { id: 'talk', group: 'Interview', title: 'Talking while you code' },
  { id: 'explain', group: 'Interview', title: 'Explain-out-loud questions' },
  { id: 'debug', group: 'Interview', title: 'Debugging fast' },
  { id: 'gotchas', group: 'Interview', title: 'Gotchas' },
  { id: 'cheat', group: 'Interview', title: 'Cheat sheet' },
  { id: 'day', group: 'Interview', title: 'Interview day' },
  { id: 'st-arch', group: 'Staff track', title: 'Architecting an app that grows' },
  { id: 'st-server', group: 'Staff track', title: 'Server state and data fetching' },
  { id: 'st-render', group: 'Staff track', title: 'CSR, SSR and Server Components' },
  { id: 'st-perf', group: 'Staff track', title: 'Performance' },
  { id: 'st-ds', group: 'Staff track', title: 'Design systems and component APIs' },
  { id: 'st-test', group: 'Staff track', title: 'Testing strategy' },
  { id: 'st-ts', group: 'Staff track', title: 'TypeScript for safer React' },
  { id: 'st-lead', group: 'Staff track', title: 'Thinking like a staff engineer' },
];

const Guide = (() => {
  let current = null;

  function num(i) { return String(i + 1).padStart(2, '0'); }

  function counts() {
    const read = Progress.get('read', {}) || {};
    const ex = Progress.get('ex', {}) || {};
    const total = MODULES.length + Object.keys(EXERCISES).length;
    const done = MODULES.filter((m) => read[m.id]).length + Object.keys(EXERCISES).filter((k) => ex[k] === 'done').length;
    return { done, total };
  }

  function renderTop() {
    const read = Progress.get('read', {}) || {};
    const ex = Progress.get('ex', {}) || {};
    const lessons = MODULES.filter((m) => read[m.id]).length;
    const exDone = Object.keys(EXERCISES).filter((k) => ex[k] === 'done' || ex[k + '~speed'] === 'done').length;
    $('#progressText').textContent = `${lessons} of ${MODULES.length} lessons · ${exDone} of ${Object.keys(EXERCISES).length} exercises`;
    $('#progressFill').style.width = Math.round((lessons / MODULES.length) * 100) + '%';
  }

  function renderToc() {
    const read = Progress.get('read', {}) || {};
    let html = '';
    let group = null;
    MODULES.forEach((m, i) => {
      if (m.group !== group) {
        group = m.group;
        html += `<p class="toc-group">${group}</p>`;
      }
      html += `<button class="toc-link ${m.id === current ? 'is-current' : ''} ${read[m.id] ? 'is-done' : ''}" data-goto="${m.id}">
        <span class="toc-num">${num(i)}</span><span>${m.title}</span><span class="toc-dot" aria-hidden="true"></span></button>`;
    });
    $('#toc').innerHTML = html;
    $('#tocSelect').innerHTML = MODULES.map((m, i) => `<option value="${m.id}" ${m.id === current ? 'selected' : ''}>${num(i)} · ${m.title}${read[m.id] ? ' ✓' : ''}</option>`).join('');
  }

  function snippet(el) {
    const lang = el.dataset.lang || 'jsx';
    const src = el.textContent.replace(/^\n/, '').replace(/\s+$/, '');
    const wrap = document.createElement('div');
    wrap.className = 'snippet';
    wrap.innerHTML = `<div class="snippet-bar"><span>${esc(el.dataset.title || lang)}</span><button type="button">Copy</button></div><pre>${highlight(src, lang)}</pre>`;
    wrap.querySelector('button').addEventListener('click', () => copyText(src, 'snippet'));
    el.replaceWith(wrap);
  }

  function quiz(el) {
    const id = el.dataset.quiz;
    const qs = QUIZZES[id];
    const saved = Progress.get('quiz:' + id, {}) || {};
    const score = () => {
      const s = Progress.get('quiz:' + id, {}) || {};
      const answered = Object.keys(s).length;
      const right = Object.keys(s).filter((k) => s[k] === qs[k].a).length;
      return answered ? `${right} / ${qs.length} correct` : `${qs.length} questions`;
    };
    el.className = 'quiz';
    el.innerHTML = `<div class="quiz-head"><h3>Check yourself</h3><span class="quiz-score">${score()}</span></div>` +
      qs.map((q, i) => `<div class="q" data-q="${i}"><p class="q-text">${q.q}</p><div class="q-opts">${q.o.map((o, j) => `<button class="q-opt" data-o="${j}">${o}</button>`).join('')}</div><p class="q-why" hidden></p></div>`).join('') +
      `<button class="pager-reset" type="button" style="justify-self:start;border:0;background:none;color:var(--muted);font-size:13px;cursor:pointer;text-decoration:underline">Reset answers</button>`;
    const mark = (qEl, i, pick) => {
      const q = qs[i];
      qEl.querySelectorAll('.q-opt').forEach((b, j) => {
        b.disabled = true;
        if (j === q.a) b.classList.add('is-right');
        if (j === pick && pick !== q.a) b.classList.add('is-wrong');
      });
      const why = qEl.querySelector('.q-why');
      why.innerHTML = `<b>${pick === q.a ? 'Right.' : 'Not quite.'}</b> ${q.why}`;
      why.hidden = false;
    };
    el.querySelectorAll('.q').forEach((qEl) => {
      const i = Number(qEl.dataset.q);
      if (saved[i] != null) mark(qEl, i, saved[i]);
      qEl.addEventListener('click', (e) => {
        const b = e.target.closest('.q-opt');
        if (!b || b.disabled) return;
        const pick = Number(b.dataset.o);
        const s = Progress.get('quiz:' + id, {}) || {};
        s[i] = pick;
        Progress.set('quiz:' + id, s);
        mark(qEl, i, pick);
        el.querySelector('.quiz-score').textContent = score();
      });
    });
    el.querySelector('.pager-reset').addEventListener('click', () => {
      Progress.set('quiz:' + id, {});
      quiz(el);
    });
  }

  function checklist(ul) {
    const id = ul.dataset.checklist;
    const state = Progress.get('checks:' + id, {}) || {};
    ul.classList.add('checklist');
    ul.querySelectorAll('li[data-id]').forEach((li) => {
      const k = li.dataset.id;
      const inner = li.innerHTML;
      li.innerHTML = `<label class="check ${state[k] ? 'is-done' : ''}"><input type="checkbox" id="chk-${id}-${k}" ${state[k] ? 'checked' : ''}><span>${inner}</span></label>`;
      li.querySelector('input').addEventListener('change', (e) => {
        const s = Progress.get('checks:' + id, {}) || {};
        s[k] = e.target.checked;
        Progress.set('checks:' + id, s);
        li.querySelector('.check').classList.toggle('is-done', e.target.checked);
      });
    });
  }

  function exCards(el, speed) {
    const ids = (el.dataset.exs || el.dataset.speeds).split(',');
    el.className = 'ex-grid';
    el.innerHTML = ids.map((id) => {
      const x = EXERCISES[id];
      const k = id + (speed ? '~speed' : '');
      const st = Progress.exStatus(k);
      const mins = speed ? x.minutes + 5 : x.minutes;
      const label = speed ? 'Speed run' : x.level ? 'Day ' + x.order + ' · L' + x.level : x.kind === 'mock' ? 'Mock' : x.kind === 'curveball' ? 'Curveball' : 'Drill';
      return `<article class="ex-card">
        <div class="ex-meta"><span class="ex-tag ${x.kind === 'mock' ? 'is-mock' : x.kind === 'curveball' ? 'is-curve' : ''}">${label}</span><span>${mins} min</span>
          <span class="ex-status ${st === 'done' ? 'is-done' : ''}">${st === 'done' ? 'Done ✓' : st === 'started' ? 'In progress' : ''}</span></div>
        <h3>${esc(x.title)}</h3>
        <p>${speed ? 'Blank component files. Rebuild it from memory: ' + esc(x.skills.slice(0, 3).join(', ')) + '.' : esc(x.summary)}</p>
        ${speed ? '' : `<div class="ex-skills">${x.skills.map((s) => `<span>${esc(s)}</span>`).join('')}</div>`}
        <button class="btn-open" data-open="${id}" ${speed ? 'data-speed="1"' : ''}>${SVG.play.replace('<svg', '<svg width="12" height="12"')} Open in workspace</button>
      </article>`;
    }).join('');
  }

  function explainCards(el) {
    el.innerHTML = EXPLAIN.map((x, i) => `<details class="q" style="cursor:pointer"><summary class="q-text" style="margin:0">${i + 1}. ${esc(x.q)}</summary><p style="margin:10px 0 0;color:var(--muted)">${esc(x.a)}</p></details>`).join('');
    el.style.display = 'grid';
    el.style.gap = '10px';
  }

  const gq = (q) => 'https://www.google.com/search?q=' + encodeURIComponent(q);

  function vocab(el) {
    let hide = false;
    el.innerHTML = `<div class="vocab-tools">
        <input type="search" id="vocabFilter" class="vocab-filter" placeholder="Filter: try “scroll”, “date”, “checkbox”…" aria-label="Filter vocabulary">
        <label class="vocab-toggle"><input type="checkbox" id="vocabHide"> Quiz me: hide the names</label>
      </div><div class="vocab-body"></div>`;
    const body = el.querySelector('.vocab-body');
    const render = () => {
      const f = el.querySelector('#vocabFilter').value.trim().toLowerCase();
      let html = '';
      VOCAB.forEach((g) => {
        const rows = g.rows.filter((r) => !f || r.join(' ').toLowerCase().includes(f));
        if (!rows.length) return;
        html += `<h3>${esc(g.group)}</h3><div class="table-wrap"><table class="vocab-table"><tr><th>You need…</th><th>It's called</th><th>Type this</th></tr>${rows.map((r) => `<tr><td>${esc(r[0])}</td><td><span class="vocab-name ${hide ? 'is-hidden' : ''}" tabindex="0" role="button" aria-label="Reveal name">${esc(r[1])}</span></td><td><a class="q-link" href="${gq(r[2])}" target="_blank" rel="noopener">${esc(r[2])}</a></td></tr>`).join('')}</table></div>`;
      });
      body.innerHTML = html || '<p style="color:var(--muted)">Nothing matches. That itself is useful: describe it in plain words plus “css” or “react” and search.</p>';
    };
    el.querySelector('#vocabFilter').addEventListener('input', render);
    el.querySelector('#vocabHide').addEventListener('change', (e) => { hide = e.target.checked; render(); });
    body.addEventListener('click', (e) => { const n = e.target.closest('.vocab-name'); if (n) n.classList.remove('is-hidden'); });
    body.addEventListener('keydown', (e) => { const n = e.target.closest('.vocab-name'); if (n && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); n.classList.remove('is-hidden'); } });
    render();
  }

  function lookupDrill(el) {
    const grades = () => Progress.get('lk:grades', {}) || {};
    let order = SCENARIOS.map((_, i) => i);
    let pos = 0;
    let revealed = false;
    let timerOn = false;
    let left = 90;
    let tick = null;
    el.className = 'ld';
    const stopTick = () => { clearInterval(tick); tick = null; };
    const summary = () => {
      const g = grades();
      const c = { got: 0, part: 0, miss: 0 };
      Object.values(g).forEach((v) => { c[v] = (c[v] || 0) + 1; });
      return `<span class="ld-pill is-got">${c.got} nailed</span><span class="ld-pill is-part">${c.part} partly</span><span class="ld-pill is-miss">${c.miss} missed</span><span class="ld-pill">${SCENARIOS.length - Object.keys(g).length} to go</span>`;
    };
    const render = () => {
      const i = order[pos];
      const sc = SCENARIOS[i];
      const ans = Progress.get('lk:ans:' + i, '') || '';
      const g = grades()[i];
      el.innerHTML = `
        <div class="ld-top">
          <div class="ld-stats">${summary()}</div>
          <div class="ld-ctrl">
            <button class="ld-btn" data-act="shuffle">Shuffle</button>
            <button class="ld-btn" data-act="missed">Missed first</button>
            <button class="ld-btn ${timerOn ? 'is-on' : ''}" data-act="timer">${timerOn ? '90s timer on' : '90s timer'}</button>
          </div>
        </div>
        <article class="ld-card">
          <div class="ld-meta"><span>Scenario ${pos + 1} of ${order.length}</span>${timerOn && !revealed ? `<span class="ld-clock ${left <= 15 ? 'is-low' : ''}">${left}s</span>` : ''}${g ? `<span class="ld-pill is-${g}">${{ got: 'Nailed', part: 'Partly', miss: 'Missed' }[g]} last time</span>` : ''}</div>
          <p class="ld-prompt">${esc(sc.p)}</p>
          <label class="ld-label" for="ldAns">Break it down, name the pieces, write the exact queries you'd type</label>
          <textarea id="ldAns" class="ld-ans" rows="5" placeholder="State: …&#10;Event: …&#10;It's called: …&#10;Search: “…”">${esc(ans)}</textarea>
          ${revealed ? `
            <div class="ld-reveal">
              <div><h4>Breakdown</h4><ul>${sc.b.map(([k, v]) => `<li><b>${esc(k)}:</b> ${esc(v)}</li>`).join('')}</ul></div>
              <div><h4>It's called</h4><ul>${sc.n.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>
              <div><h4>Type this</h4><ul>${sc.q.map((q) => `<li><a class="q-link" href="${gq(q)}" target="_blank" rel="noopener">${esc(q)} ↗</a></li>`).join('')}</ul></div>
            </div>
            <div class="snippet"><div class="snippet-bar"><span>What you'd end up writing</span><button type="button" data-act="copy">Copy</button></div><pre>${highlight(sc.s, /^[.@a-z-]+\s*\{|^\.|^@/.test(sc.s) && !/=>|const /.test(sc.s) ? 'css' : 'jsx')}</pre></div>
            ${sc.tip ? `<p class="ld-tip"><b>Say this:</b> ${esc(sc.tip)}</p>` : ''}
            <div class="ld-grade"><span>How did you do?</span>
              <button class="ld-btn ${g === 'got' ? 'is-got' : ''}" data-grade="got">Nailed it</button>
              <button class="ld-btn ${g === 'part' ? 'is-part' : ''}" data-grade="part">Partly</button>
              <button class="ld-btn ${g === 'miss' ? 'is-miss' : ''}" data-grade="miss">Missed</button>
            </div>` : `<button class="btn-open" data-act="reveal">Reveal answer</button>`}
          <div class="ld-nav">
            <button class="ld-btn" data-act="prev" ${pos === 0 ? 'disabled' : ''}>← Previous</button>
            <button class="ld-btn" data-act="next">${pos === order.length - 1 ? 'Back to first' : 'Next →'}</button>
          </div>
        </article>`;
      const ta = el.querySelector('#ldAns');
      ta.addEventListener('input', () => Progress.set('lk:ans:' + i, ta.value));
    };
    const go = (n) => {
      pos = (n + order.length) % order.length;
      revealed = false;
      left = 90;
      stopTick();
      if (timerOn) startTick();
      render();
      const ta = el.querySelector('#ldAns');
      if (ta) ta.focus({ preventScroll: true });
    };
    const startTick = () => {
      stopTick();
      tick = setInterval(() => {
        if (!el.isConnected) { stopTick(); return; }
        left--;
        if (left <= 0) { stopTick(); revealed = true; render(); return; }
        const c = el.querySelector('.ld-clock');
        if (c) { c.textContent = left + 's'; c.classList.toggle('is-low', left <= 15); }
      }, 1000);
    };
    el.addEventListener('click', (e) => {
      const b = e.target.closest('[data-act],[data-grade]');
      if (!b) return;
      const act = b.dataset.act;
      if (b.dataset.grade) {
        const g = grades();
        g[order[pos]] = b.dataset.grade;
        Progress.set('lk:grades', g);
        if (window.Guide) renderTop();
        go(pos + 1);
        return;
      }
      if (act === 'reveal') { revealed = true; stopTick(); render(); }
      if (act === 'next') go(pos + 1);
      if (act === 'prev') go(pos - 1);
      if (act === 'copy') copyText(SCENARIOS[order[pos]].s, 'snippet');
      if (act === 'shuffle') {
        for (let k = order.length - 1; k > 0; k--) { const j = Math.floor(Math.random() * (k + 1)); [order[k], order[j]] = [order[j], order[k]]; }
        go(0);
      }
      if (act === 'missed') {
        const g = grades();
        const rank = (i) => ({ miss: 0, part: 1 }[g[i]] ?? (g[i] ? 3 : 2));
        order = SCENARIOS.map((_, i) => i).sort((a, b) => rank(a) - rank(b));
        go(0);
      }
      if (act === 'timer') { timerOn = !timerOn; left = 90; if (timerOn && !revealed) startTick(); else stopTick(); render(); }
    });
    render();
  }

  function show(id, scroll = true) {
    const m = MODULES.find((x) => x.id === id) || MODULES[0];
    current = m.id;
    const i = MODULES.indexOf(m);
    const tpl = document.getElementById('tpl-' + m.id);
    const read = Progress.get('read', {}) || {};
    const main = $('#content');
    Play.unmountAll();
    main.innerHTML = '';
    const art = document.createElement('article');
    art.className = 'module';
    art.innerHTML = `<p class="eyebrow">${num(i)} · ${m.group}</p>`;
    art.appendChild(tpl.content.cloneNode(true));
    art.querySelectorAll('script[type="text/x-code"]').forEach(snippet);
    art.querySelectorAll('[data-quiz]').forEach(quiz);
    art.querySelectorAll('ul[data-checklist]').forEach(checklist);
    art.querySelectorAll('[data-exs]').forEach((el) => exCards(el, false));
    art.querySelectorAll('[data-speeds]').forEach((el) => exCards(el, true));
    art.querySelectorAll('[data-explain]').forEach(explainCards);
    art.querySelectorAll('script[type="text/x-play"]').forEach((el) => Play.mount(el));
    art.querySelectorAll('[data-explorer]').forEach(mountExplorer);
    art.querySelectorAll('[data-katas]').forEach(mountKatas);
    art.querySelectorAll('[data-vocab]').forEach(vocab);
    art.querySelectorAll('[data-lookdrill]').forEach(lookupDrill);
    const prev = MODULES[i - 1];
    const next = MODULES[i + 1];
    const pager = document.createElement('nav');
    pager.className = 'pager';
    pager.innerHTML = `
      ${prev ? `<button data-goto="${prev.id}"><small>← Previous</small>${prev.title}</button>` : ''}
      <button class="next" data-read="${m.id}" style="${read[m.id] ? '' : 'background:var(--ink);color:var(--bg);border-color:var(--ink)'}">
        <small style="${read[m.id] ? '' : 'color:inherit;opacity:.75'}">${read[m.id] ? 'Done ✓' : 'Mark done'}${next ? ' · next' : ''}</small>${next ? next.title : 'Back to start'}</button>`;
    art.appendChild(pager);
    main.appendChild(art);
    renderToc();
    renderTop();
    Progress.set('last', m.id);
    if (location.hash.slice(1) !== m.id) {
      try { history.replaceState(null, '', '#' + m.id); } catch (e) { /* ignore */ }
    }
    if (scroll) window.scrollTo({ top: 0 });
  }

  function refresh() { show(current, false); }

  function init() {
    document.addEventListener('click', (e) => {
      const go = e.target.closest('[data-goto]');
      if (go && !go.closest('#ide')) { e.preventDefault(); show(go.dataset.goto); return; }
      const rd = e.target.closest('[data-read]');
      if (rd) {
        const r = Progress.get('read', {}) || {};
        r[rd.dataset.read] = true;
        Progress.set('read', r);
        const i = MODULES.findIndex((m) => m.id === rd.dataset.read);
        show((MODULES[i + 1] || MODULES[0]).id);
        return;
      }
      const op = e.target.closest('[data-open]');
      if (op && !op.closest('#ide')) Workspace.open(op.dataset.open, { speed: !!op.dataset.speed });
    });
    $('#tocSelect').addEventListener('change', (e) => show(e.target.value));
    const applyToc = (collapsed) => {
      document.body.classList.toggle('toc-collapsed', collapsed);
      $('#tocToggle').setAttribute('aria-expanded', String(!collapsed));
      $('#tocToggleLabel').textContent = collapsed ? 'Show topics' : 'Hide topics';
    };
    applyToc(Progress.pref('tocCollapsed', false));
    $('#tocToggle').addEventListener('click', () => {
      const collapsed = !document.body.classList.contains('toc-collapsed');
      Progress.setPref('tocCollapsed', collapsed);
      applyToc(collapsed);
    });
    window.addEventListener('hashchange', () => {
      const id = location.hash.slice(1);
      if (id && id !== current && MODULES.some((m) => m.id === id)) show(id);
    });
    const start = location.hash.slice(1);
    show(MODULES.some((m) => m.id === start) ? start : Progress.get('last', 'start'), false);
    window.addEventListener('beforeunload', () => Progress.set('last', current));
  }

  return { init, show, refresh };
})();
window.Guide = Guide;
