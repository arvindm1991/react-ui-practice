/* ================= Workspace: libraries, editor, runtime, inspector ================= */
const ORIG_CONSOLE = { log: console.log, info: console.info, warn: console.warn, error: console.error, debug: console.debug };

const LIBS = {
  react: [
    'https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.development.js',
    'https://unpkg.com/react@18.2.0/umd/react.development.js',
    'https://cdn.jsdelivr.net/npm/react@18.2.0/umd/react.development.js',
  ],
  reactDom: [
    'https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.development.js',
    'https://unpkg.com/react-dom@18.2.0/umd/react-dom.development.js',
    'https://cdn.jsdelivr.net/npm/react-dom@18.2.0/umd/react-dom.development.js',
  ],
  babel: [
    'https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.5/babel.min.js',
    'https://unpkg.com/@babel/standalone@7.23.5/babel.min.js',
    'https://cdn.jsdelivr.net/npm/@babel/standalone@7.23.5/babel.min.js',
  ],
};

let libsPromise = null;
function loadLibs() {
  if (libsPromise) return libsPromise;
  const one = (urls) => new Promise((resolve, reject) => {
    let i = 0;
    const next = () => {
      if (i >= urls.length) { reject(new Error('Could not load ' + urls[0].split('/').slice(-3).join('/'))); return; }
      const s = document.createElement('script');
      s.src = urls[i++];
      s.onload = () => resolve();
      s.onerror = () => { s.remove(); next(); };
      document.head.appendChild(s);
    };
    next();
  });
  libsPromise = Promise.all([
    (window.React ? Promise.resolve() : one(LIBS.react)).then(() => (window.ReactDOM ? null : one(LIBS.reactDom))),
    window.Babel ? Promise.resolve() : one(LIBS.babel),
  ]);
  libsPromise.catch(() => { libsPromise = null; });
  return libsPromise;
}

/* ---------- syntax highlighting ---------- */
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const JS_RE = /(\/\/[^\n]*|\/\*[\s\S]*?(?:\*\/|$))|(`(?:\\[\s\S]|[^`\\])*`?|'(?:\\.|[^'\\\n])*'?|"(?:\\.|[^"\\\n])*"?)|(<\/?)([A-Za-z][\w.-]*)|\b(import|from|export|default|function|return|const|let|var|if|else|for|of|in|while|do|new|async|await|try|catch|finally|throw|class|extends|typeof|instanceof|switch|case|break|continue|null|undefined|true|false|this)\b|\b(\d[\d_]*(?:\.\d+)?)\b|\b([A-Za-z_$][\w$]*)(?=\s*\()/g;
const CSS_RE = /(\/\*[\s\S]*?(?:\*\/|$))|("(?:[^"\\\n]|\\.)*"?|'(?:[^'\\\n]|\\.)*'?)|(@[\w-]+)|(#[0-9a-fA-F]{3,8}(?![\w-]))|(-?\d*\.?\d+(?:px|rem|em|%|vh|vw|fr|ms|s|deg)?)(?![\w-])|(--[\w-]+|[a-zA-Z-]+)(?=\s*:[^;{}]*[;}])|([.#][\w-]+|::?[\w-]+)/g;

function highlight(src, lang) {
  if (lang === 'tsx') lang = 'jsx';
  if (lang === 'ts') lang = 'js';
  let out = '';
  let last = 0;
  let m;
  if (lang === 'css') {
    CSS_RE.lastIndex = 0;
    while ((m = CSS_RE.exec(src))) {
      if (m[0] === '') { CSS_RE.lastIndex++; continue; }
      out += esc(src.slice(last, m.index));
      const cls = m[1] ? 't-com' : m[2] ? 't-str' : m[3] ? 't-at' : m[4] ? 't-num' : m[5] ? 't-num' : m[6] ? 't-prop' : 't-sel';
      out += `<span class="${cls}">${esc(m[0])}</span>`;
      last = CSS_RE.lastIndex;
    }
  } else if (lang === 'jsx' || lang === 'js') {
    JS_RE.lastIndex = 0;
    while ((m = JS_RE.exec(src))) {
      if (m[0] === '') { JS_RE.lastIndex++; continue; }
      out += esc(src.slice(last, m.index));
      if (m[1]) out += `<span class="t-com">${esc(m[1])}</span>`;
      else if (m[2]) out += `<span class="t-str">${esc(m[2])}</span>`;
      else if (m[4]) out += esc(m[3]) + `<span class="t-tag">${esc(m[4])}</span>`;
      else if (m[5]) out += `<span class="t-kw">${m[5]}</span>`;
      else if (m[6]) out += `<span class="t-num">${m[6]}</span>`;
      else out += `<span class="t-fn">${esc(m[7])}</span>`;
      last = JS_RE.lastIndex;
    }
  } else {
    return esc(src);
  }
  return out + esc(src.slice(last));
}
const langFor = (path) => (path.endsWith('.css') ? 'css' : path.endsWith('.json') ? 'json' : /\.[jt]sx$/.test(path) ? 'jsx' : 'js');

/* ---------- editor (textarea + highlighted overlay) ---------- */
const PAIRS = { '(': ')', '[': ']', '{': '}' };
const CLOSERS = new Set([')', ']', '}']);

class CodeEditor {
  constructor(el, opts) {
    this.opts = opts || {};
    this.lang = 'jsx';
    this.n = 0;
    el.innerHTML =
      '<div class="ce"><div class="ce-gutter" aria-hidden="true"><div class="ce-lines"></div></div>' +
      '<div class="ce-wrap"><pre class="ce-hl" aria-hidden="true"><code></code></pre>' +
      '<textarea class="ce-ta" id="' + (this.opts.id || 'code-editor') + '" spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off" wrap="off" aria-label="Code editor"></textarea></div></div>';
    this.ta = el.querySelector('textarea');
    this.hl = el.querySelector('.ce-hl');
    this.code = el.querySelector('code');
    this.lines = el.querySelector('.ce-lines');
    this.ta.addEventListener('input', () => { this.render(); this.opts.onChange && this.opts.onChange(this.ta.value); });
    this.ta.addEventListener('scroll', () => this.sync());
    this.ta.addEventListener('keydown', (e) => this.key(e));
    ['keyup', 'click', 'select', 'focus'].forEach((ev) => this.ta.addEventListener(ev, () => this.cursor()));
  }
  setValue(value, lang, readOnly) {
    this.lang = lang;
    this.ta.value = value;
    this.ta.readOnly = !!readOnly;
    this.render();
    this.ta.scrollTop = 0;
    this.ta.scrollLeft = 0;
    this.sync();
    try { this.ta.setSelectionRange(0, 0); } catch (e) { /* ignore */ }
    this.cursor();
  }
  render() {
    const v = this.ta.value;
    this.code.innerHTML = highlight(v, this.lang) + '\n';
    const n = v.split('\n').length;
    if (n !== this.n) {
      this.n = n;
      let s = '';
      for (let i = 1; i <= n; i++) s += `<div>${i}</div>`;
      this.lines.innerHTML = s;
      this.curLine = -1;
    }
    this.cursor();
    this.sync();
  }
  sync() {
    this.hl.style.transform = `translate(${-this.ta.scrollLeft}px, ${-this.ta.scrollTop}px)`;
    this.lines.style.transform = `translateY(${-this.ta.scrollTop}px)`;
  }
  cursor() {
    const v = this.ta.value;
    const s = this.ta.selectionStart;
    const before = v.slice(0, s);
    const line = before.split('\n').length - 1;
    const col = s - (before.lastIndexOf('\n') + 1);
    if (line !== this.curLine) {
      const prev = this.lines.children[this.curLine];
      if (prev) prev.classList.remove('is-cur');
      const cur = this.lines.children[line];
      if (cur) cur.classList.add('is-cur');
      this.curLine = line;
    }
    this.opts.onCursor && this.opts.onCursor(line + 1, col + 1);
  }
  insert(text) {
    const ta = this.ta;
    ta.focus();
    let ok = false;
    try { ok = text ? document.execCommand('insertText', false, text) : document.execCommand('delete', false); } catch (e) { ok = false; }
    if (!ok) {
      ta.setRangeText(text, ta.selectionStart, ta.selectionEnd, 'end');
      ta.dispatchEvent(new Event('input'));
    }
  }
  lineRange() {
    const v = this.ta.value;
    const s = this.ta.selectionStart;
    let en = this.ta.selectionEnd;
    if (en > s && v[en - 1] === '\n') en--;
    const ls = v.lastIndexOf('\n', s - 1) + 1;
    let le = v.indexOf('\n', en);
    if (le < 0) le = v.length;
    return [ls, le];
  }
  replaceLines(fn) {
    const [ls, le] = this.lineRange();
    const out = fn(this.ta.value.slice(ls, le).split('\n')).join('\n');
    this.ta.setSelectionRange(ls, le);
    this.insert(out);
    this.ta.setSelectionRange(ls, ls + out.length);
  }
  key(e) {
    const ta = this.ta;
    const v = ta.value;
    const s = ta.selectionStart;
    const en = ta.selectionEnd;
    const mod = e.metaKey || e.ctrlKey;
    if (mod && (e.key === 's' || e.key === 'Enter')) { e.preventDefault(); this.opts.onRun && this.opts.onRun(); return; }
    if (ta.readOnly) return;
    if (mod && e.key === '/') {
      e.preventDefault();
      const css = this.lang === 'css';
      this.replaceLines((lines) => {
        const nonEmpty = lines.filter((l) => l.trim());
        const commented = nonEmpty.length > 0 && nonEmpty.every((l) => (css ? /^\s*\/\*.*\*\/\s*$/.test(l) : /^\s*\/\//.test(l)));
        const minIndent = Math.min(...nonEmpty.map((l) => l.match(/^\s*/)[0].length));
        return lines.map((l) => {
          if (!l.trim()) return l;
          if (commented) return css ? l.replace(/\/\*\s?/, '').replace(/\s?\*\/(\s*)$/, '$1') : l.replace(/\/\/\s?/, '');
          return css ? l.slice(0, minIndent) + '/* ' + l.slice(minIndent) + ' */' : l.slice(0, minIndent) + '// ' + l.slice(minIndent);
        });
      });
      return;
    }
    if (e.key === 'Tab') {
      e.preventDefault();
      if (e.shiftKey || (s !== en && v.slice(s, en).includes('\n'))) {
        this.replaceLines((lines) => lines.map((l) => (e.shiftKey ? l.replace(/^ {1,2}|^\t/, '') : '  ' + l)));
      } else {
        this.insert('  ');
      }
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.altKey && !mod) {
      e.preventDefault();
      const before = v.slice(0, s);
      const line = before.slice(before.lastIndexOf('\n') + 1);
      const indent = line.match(/^[ \t]*/)[0];
      const lt = line.trimEnd();
      const after = v.slice(en);
      const opens = /[{(\[]$/.test(lt) || (/<[A-Za-z]/.test(lt) && /[^/=]>$/.test(lt) && !/<\/[\w.]*>$/.test(lt));
      if (opens) {
        if (/^[ \t]*([}\])]|<\/)/.test(after)) {
          this.insert('\n' + indent + '  \n' + indent);
          const pos = s + 1 + indent.length + 2;
          ta.setSelectionRange(pos, pos);
        } else {
          this.insert('\n' + indent + '  ');
        }
      } else {
        this.insert('\n' + indent);
      }
      return;
    }
    if (mod || e.altKey) return;
    if (PAIRS[e.key] && s === en) {
      const next = v[s];
      if (!next || /[\s)\]},;]/.test(next)) {
        e.preventDefault();
        this.insert(e.key + PAIRS[e.key]);
        ta.setSelectionRange(s + 1, s + 1);
        return;
      }
    }
    if (CLOSERS.has(e.key) && s === en) {
      if (v[s] === e.key) { e.preventDefault(); ta.setSelectionRange(s + 1, s + 1); this.cursor(); return; }
      const ls = v.lastIndexOf('\n', s - 1) + 1;
      const lead = v.slice(ls, s);
      if (lead.length >= 2 && /^ +$/.test(lead)) {
        e.preventDefault();
        ta.setSelectionRange(s - 2, s);
        this.insert(e.key);
        return;
      }
    }
    if (e.key === 'Backspace' && s === en && s > 0 && PAIRS[v[s - 1]] && PAIRS[v[s - 1]] === v[s]) {
      e.preventDefault();
      ta.setSelectionRange(s - 1, s + 1);
      this.insert('');
    }
  }
  focus() { this.ta.focus(); }
}

/* ---------- preview runtime: tiny CommonJS bundler over Babel ---------- */
const BASE_PREVIEW_CSS = `
.__pg_body { display: block; margin: 8px; font: 16px/normal "Times New Roman", Times, serif; color: #000;
  letter-spacing: normal; text-align: start; -webkit-font-smoothing: auto; color-scheme: light;
  container-type: inline-size; container-name: pgbody; }`;

function rewriteCss(css) {
  return css
    .replace(/(^|[\s,{}>+~(])(html|body|:root)(?=[\s,{.:#\[>+~)]|$)/g, (m, p) => p + '.__pg_body')
    .replace(/(-?\d*\.?\d+)[dsl]?vh\b/g, 'calc($1 * var(--pgvh, 1vh))')
    .replace(/(-?\d*\.?\d+)[dsl]?vw\b/g, 'calc($1 * var(--pgvw, 1vw))')
    .replace(/@media([^{]*)\{/g, (m, q) => (/width/.test(q) && !/prefers|print/.test(q)
      ? '@container pgbody ' + q.replace(/\b(only\s+)?(screen|all)\s*(and)?/g, '').trim() + ' {'
      : m));
}

function resolvePath(from, spec, files) {
  if (!spec.startsWith('.') && !spec.startsWith('/')) {
    const err = new Error(`Module not found: Can't resolve '${spec}' in '${from.split('/').slice(0, -1).join('/')}'. Only react and react-dom are installed in this workspace.`);
    err.isCompile = true;
    throw err;
  }
  const base = spec.startsWith('/') ? [] : from.split('/').slice(0, -1);
  spec.split('/').forEach((part) => {
    if (part === '.' || part === '') return;
    if (part === '..') base.pop();
    else base.push(part);
  });
  const p = base.join('/');
  const tries = [p, p + '.tsx', p + '.ts', p + '.jsx', p + '.js', p + '/index.tsx', p + '/index.ts', p + '/index.jsx', p + '/index.js'];
  for (const c of tries) if (files[c] != null) return c;
  const err = new Error(`Module not found: Can't resolve '${spec}' in '${from.split('/').slice(0, -1).join('/')}'`);
  err.isCompile = true;
  throw err;
}

let factorySeq = 0;
function makeFactory(code, path) {
  const params = ['require', 'module', 'exports', 'React', 'console', 'document', 'window'];
  const body = code + '\n//# sourceURL=preview:///' + path;
  try {
    return new Function(...params, body);
  } catch (e) {
    if (e instanceof SyntaxError) throw e;
    window.__pgFactories = window.__pgFactories || {};
    const key = 'f' + (++factorySeq);
    const s = document.createElement('script');
    s.textContent = `window.__pgFactories.${key} = function(${params.join(',')}) {\n${body}\n};`;
    document.head.appendChild(s);
    s.remove();
    const f = window.__pgFactories[key];
    delete window.__pgFactories[key];
    if (!f) throw new Error('This browser blocked running the preview code.');
    return f;
  }
}

function fmtVal(v, depth = 0) {
  if (typeof v === 'string') return v;
  if (v instanceof Error) return `${v.name}: ${v.message}`;
  if (typeof v === 'function') return `ƒ ${v.name || 'anonymous'}()`;
  if (typeof v === 'undefined') return 'undefined';
  if (v === null || typeof v !== 'object') return String(v);
  if (v instanceof Element) return `<${v.tagName.toLowerCase()}${v.className ? ' class="' + v.className + '"' : ''}>`;
  try {
    const seen = new WeakSet();
    return JSON.stringify(v, (k, val) => {
      if (typeof val === 'object' && val !== null) { if (seen.has(val)) return '[Circular]'; seen.add(val); }
      if (typeof val === 'function') return `ƒ ${val.name || ''}()`;
      if (val && val.$$typeof) return '[React element]';
      return val;
    }, 2);
  } catch (e) {
    return String(v);
  }
}
function fmtArgs(args) {
  if (typeof args[0] === 'string' && /%[sdoOifc]/.test(args[0])) {
    let i = 1;
    const first = args[0].replace(/%[sdoOifc]/g, (m) => {
      if (m === '%c') { i++; return ''; }
      return i < args.length ? fmtVal(args[i++]) : m;
    });
    return [first, ...args.slice(i).map((a) => fmtVal(a))].join(' ');
  }
  return args.map((a) => fmtVal(a)).join(' ');
}

class Runtime {
  constructor(host, opts) {
    this.host = host;
    this.opts = opts || {};
    this.shadow = host.attachShadow({ mode: 'open' });
    this.cache = new Map();
    this.roots = [];
    const ro = new ResizeObserver(() => {
      host.style.setProperty('--pgvh', host.clientHeight / 100 + 'px');
      host.style.setProperty('--pgvw', host.clientWidth / 100 + 'px');
    });
    ro.observe(host);
    // A form submit without preventDefault would navigate the whole page away.
    // Block it, and say what a real browser would have done.
    this.shadow.addEventListener('submit', (e) => {
      if (e.defaultPrevented) return;
      e.preventDefault();
      if (this.opts.onLog) this.opts.onLog('warn', 'The form submitted without e.preventDefault(). In a real browser the page would reload here and all state would be lost.');
    });
    this.reset();
  }
  reset() {
    this.roots.forEach((r) => { try { r.unmount(); } catch (e) { /* ignore */ } });
    this.roots = [];
    (this.listeners || []).forEach(([t, type, fn, o]) => t.removeEventListener(type, fn, o));
    this.listeners = [];
    this.shadow.innerHTML = `<style>${BASE_PREVIEW_CSS}</style><style data-user></style><div class="__pg_body"><div id="root"></div></div>`;
    this.bodyEl = this.shadow.querySelector('.__pg_body');
    this.rootEl = this.shadow.getElementById('root');
    this.host.style.background = '#fff';
  }
  compile(path, src) {
    const hit = this.cache.get(path);
    if (hit && hit.src === src) return hit.code;
    let code;
    try {
      code = window.Babel.transform(src, {
        filename: path,
        sourceType: 'module',
        presets: /\.tsx?$/.test(path)
          ? [['react', { runtime: 'classic' }], ['typescript', { isTSX: path.endsWith('.tsx'), allExtensions: true }]]
          : [['react', { runtime: 'classic' }]],
        plugins: ['transform-modules-commonjs'],
        retainLines: true,
      }).code;
    } catch (e) {
      e.isCompile = true;
      throw e;
    }
    this.cache.set(path, { src, code });
    return code;
  }
  makeConsole() {
    const c = {};
    ['log', 'info', 'warn', 'error', 'debug', 'table'].forEach((k) => {
      c[k] = (...args) => {
        if (this.opts.onLog) this.opts.onLog(k === 'table' || k === 'debug' ? 'log' : k, fmtArgs(args));
        (ORIG_CONSOLE[k] || ORIG_CONSOLE.log).apply(console, args);
      };
    });
    return c;
  }
  run(files, entry = 'src/index.jsx') {
    this.reset();
    const React = window.React;
    const ReactDOM = window.ReactDOM;
    const runtime = this;
    const createRoot = (el, o) => {
      const internals = ReactDOM.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED;
      if (internals && 'usingClientEntryPoint' in internals) internals.usingClientEntryPoint = true;
      try {
        const r = ReactDOM.createRoot(el, o);
        runtime.roots.push(r);
        return r;
      } finally {
        if (internals && 'usingClientEntryPoint' in internals) internals.usingClientEntryPoint = false;
      }
    };
    const externals = {
      react: React,
      'react-dom': ReactDOM,
      'react-dom/client': { createRoot, hydrateRoot: createRoot },
    };
    // Listeners on document/window see events from inside the preview's shadow root
    // with their real target (so ref.contains(e.target) works for "click outside").
    const wrapped = new WeakMap();
    const retarget = (fn) => {
      if (typeof fn !== 'function') return fn;
      if (!wrapped.has(fn)) {
        wrapped.set(fn, function (e) {
          const real = e.composedPath ? e.composedPath()[0] : e.target;
          if (real === e.target) return fn.call(this, e);
          const ev = new Proxy(e, {
            get(t, p) {
              if (p === 'target') return real;
              const v = Reflect.get(t, p);
              return typeof v === 'function' ? v.bind(t) : v;
            },
          });
          return fn.call(this, ev);
        });
      }
      return wrapped.get(fn);
    };
    const listenerTrap = (t, p) => {
      if (p === 'addEventListener') return (type, fn, o) => { t.addEventListener(type, retarget(fn), o); runtime.listeners.push([t, type, retarget(fn), o]); };
      if (p === 'removeEventListener') return (type, fn, o) => t.removeEventListener(type, wrapped.get(fn) || fn, o);
      return undefined;
    };
    const winProxy = new Proxy(window, {
      get(t, p) {
        const l = listenerTrap(t, p);
        if (l) return l;
        if (p === 'document') return docProxy;
        const v = Reflect.get(t, p);
        return typeof v === 'function' && !/^[A-Z]/.test(String(p)) ? v.bind(t) : v;
      },
    });
    const docProxy = new Proxy(document, {
      get(t, p) {
        const l = listenerTrap(t, p);
        if (l) return l;
        if (p === 'getElementById') return (id) => (id === 'root' ? runtime.rootEl : runtime.shadow.getElementById(id));
        if (p === 'querySelector') return (sel) => runtime.shadow.querySelector(sel);
        if (p === 'querySelectorAll') return (sel) => runtime.shadow.querySelectorAll(sel);
        if (p === 'body') return runtime.bodyEl;
        const v = Reflect.get(t, p);
        return typeof v === 'function' ? v.bind(t) : v;
      },
    });
    const consoleProxy = this.makeConsole();
    const cssPaths = [];
    const modules = {};
    const load = (path) => {
      if (modules[path]) return modules[path].exports;
      const module = { exports: {} };
      modules[path] = module;
      const code = this.compile(path, files[path]);
      const fn = makeFactory(code, path);
      fn(requireFrom(path), module, module.exports, React, consoleProxy, docProxy, winProxy);
      return module.exports;
    };
    const requireFrom = (from) => (spec) => {
      if (Object.prototype.hasOwnProperty.call(externals, spec)) return externals[spec];
      const path = resolvePath(from, spec, files);
      if (path.endsWith('.css')) {
        if (!cssPaths.includes(path)) cssPaths.push(path);
        return {};
      }
      return load(path);
    };
    let error = null;
    try {
      if (files[entry] == null) throw Object.assign(new Error(`Entry file ${entry} is missing.`), { isCompile: true });
      load(entry);
    } catch (e) {
      error = e;
    }
    this.shadow.querySelector('style[data-user]').textContent = cssPaths.map((p) => `/* ${p} */\n` + rewriteCss(files[p])).join('\n');
    setTimeout(() => this.syncBackground(), 60);
    return error;
  }
  syncBackground() {
    const bg = getComputedStyle(this.bodyEl).backgroundColor;
    this.host.style.background = !bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent' ? '#fff' : bg;
  }
}

/* ---------- design inspector ---------- */
function toHex(c) {
  const m = /rgba?\(([^)]+)\)/.exec(c || '');
  if (!m) return c;
  const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
  const hex = '#' + p.slice(0, 3).map((n) => Math.round(n).toString(16).padStart(2, '0')).join('').toUpperCase();
  return p.length > 3 && p[3] < 1 ? `${hex} · ${Math.round(p[3] * 100)}%` : hex;
}
const isClear = (c) => !c || c === 'transparent' || /rgba\([^)]*,\s*0\)$/.test(c) || c === 'rgba(0, 0, 0, 0)';
function boxStr(a, b, c, d) {
  const v = [a, b, c, d].map((x) => Math.round(parseFloat(x) * 10) / 10);
  if (v.every((x) => x === v[0])) return v[0] + '';
  if (v[0] === v[2] && v[1] === v[3]) return `${v[0]} ${v[1]}`;
  return v.join(' ');
}

class Inspector {
  constructor(runtime, canvas, info) {
    this.rt = runtime;
    this.canvas = canvas;
    this.info = info;
    this.on = true;
    this.pinned = null;
    this.current = null;
    this.box = document.createElement('div');
    this.box.className = 'inspect-box';
    this.box.hidden = true;
    this.box.innerHTML = '<span class="inspect-label"></span>';
    this.pads = [0, 1, 2, 3].map(() => {
      const d = document.createElement('div');
      d.className = 'inspect-pad';
      d.hidden = true;
      canvas.appendChild(d);
      return d;
    });
    canvas.appendChild(this.box);
    const sh = runtime.shadow;
    sh.addEventListener('pointermove', (e) => {
      if (!this.on || this.pinned) return;
      const el = this.pick(e);
      if (el) this.show(el); else this.hide();
    });
    sh.addEventListener('click', (e) => {
      if (!this.on) return;
      e.preventDefault();
      e.stopPropagation();
      const el = this.pick(e);
      this.pinned = this.pinned === el ? null : el;
      if (el) this.show(el);
    }, true);
    runtime.host.addEventListener('pointerleave', () => { if (!this.pinned) this.hide(); });
    runtime.host.addEventListener('scroll', () => { if (this.current) this.show(this.current); });
    this.renderInfo(null);
  }
  setOn(on) {
    this.on = on;
    this.pinned = null;
    this.hide();
  }
  pick(e) {
    const el = e.composedPath()[0];
    if (!(el instanceof Element) || el === this.rt.bodyEl || el === this.rt.rootEl || !this.rt.bodyEl.contains(el)) return null;
    return el;
  }
  hide() {
    this.current = null;
    this.box.hidden = true;
    this.pads.forEach((p) => { p.hidden = true; });
  }
  show(el) {
    this.current = el;
    const r = el.getBoundingClientRect();
    const c = this.canvas.getBoundingClientRect();
    const x = r.left - c.left;
    const y = r.top - c.top;
    Object.assign(this.box.style, { left: x + 'px', top: y + 'px', width: r.width + 'px', height: r.height + 'px' });
    this.box.hidden = false;
    const tag = el.tagName.toLowerCase() + (el.classList.length ? '.' + [...el.classList].join('.') : '');
    this.box.querySelector('.inspect-label').textContent = `${tag}  ${Math.round(r.width)} × ${Math.round(r.height)}`;
    this.box.querySelector('.inspect-label').style.top = y < 22 ? r.height + 2 + 'px' : '-20px';
    const cs = getComputedStyle(el);
    const bt = parseFloat(cs.borderTopWidth); const bl = parseFloat(cs.borderLeftWidth);
    const br = parseFloat(cs.borderRightWidth); const bb = parseFloat(cs.borderBottomWidth);
    const pt = parseFloat(cs.paddingTop); const pr = parseFloat(cs.paddingRight);
    const pb = parseFloat(cs.paddingBottom); const pl = parseFloat(cs.paddingLeft);
    const ix = x + bl; const iy = y + bt; const iw = r.width - bl - br; const ih = r.height - bt - bb;
    const rects = [
      [ix, iy, iw, pt], [ix + iw - pr, iy + pt, pr, ih - pt - pb],
      [ix, iy + ih - pb, iw, pb], [ix, iy + pt, pl, ih - pt - pb],
    ];
    this.pads.forEach((p, i) => {
      const [px, py, pw, ph] = rects[i];
      if (pw <= 0 || ph <= 0) { p.hidden = true; return; }
      Object.assign(p.style, { left: px + 'px', top: py + 'px', width: pw + 'px', height: ph + 'px' });
      p.hidden = false;
    });
    this.renderInfo(el, cs, r, tag);
  }
  renderInfo(el, cs, r, tag) {
    if (!el) {
      this.info.innerHTML = '<div class="inspect-empty">Hover over the design to read sizes, spacing, colors and type. Click to pin a layer. Blue shading is padding.</div>';
      return;
    }
    const rows = [];
    const add = (k, v, color) => rows.push(`<dt>${k}</dt><dd>${color ? `<span class="swatch" style="background:${color}"></span>` : ''}${esc(v)}</dd>`);
    add('Size', `${Math.round(r.width * 10) / 10} × ${Math.round(r.height * 10) / 10}`);
    const pad = boxStr(cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft);
    if (pad !== '0') add('Padding', pad);
    const mar = boxStr(cs.marginTop, cs.marginRight, cs.marginBottom, cs.marginLeft);
    if (mar !== '0') add('Margin', mar);
    if (/flex/.test(cs.display)) {
      add('Layout', `flex ${cs.flexDirection}`);
      const gap = cs.columnGap === cs.rowGap ? cs.columnGap : `${cs.rowGap} ${cs.columnGap}`;
      if (gap && gap !== 'normal' && gap !== '0px') add('Gap', gap);
      add('Align', `justify ${cs.justifyContent} · align ${cs.alignItems}`);
    } else if (/grid/.test(cs.display)) {
      add('Layout', 'grid');
      add('Columns', cs.gridTemplateColumns);
      const gap = cs.columnGap === cs.rowGap ? cs.columnGap : `${cs.rowGap} ${cs.columnGap}`;
      if (gap && gap !== 'normal' && gap !== '0px') add('Gap', gap);
    } else {
      add('Display', cs.display);
    }
    if (cs.position !== 'static') add('Position', `${cs.position}  top ${cs.top} · right ${cs.right}`);
    const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (hasText || /^(input|button|select|textarea)$/i.test(el.tagName)) {
      add('Font', `${cs.fontFamily.split(',')[0].replace(/"/g, '')}`);
      add('Type', `${cs.fontSize} / ${cs.lineHeight} · ${cs.fontWeight}`);
      if (cs.letterSpacing !== 'normal' && cs.letterSpacing !== '0px') add('Letter spacing', cs.letterSpacing);
      if (cs.textTransform !== 'none') add('Transform', cs.textTransform);
      add('Text color', toHex(cs.color), cs.color);
    }
    if (!isClear(cs.backgroundColor)) add('Fill', toHex(cs.backgroundColor), cs.backgroundColor);
    if (cs.backgroundImage !== 'none') add('Fill image', cs.backgroundImage.slice(0, 80));
    if (parseFloat(cs.borderTopWidth) || parseFloat(cs.borderRightWidth) || parseFloat(cs.borderBottomWidth) || parseFloat(cs.borderLeftWidth)) {
      const w = boxStr(cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth);
      const sideColor = parseFloat(cs.borderTopWidth) ? cs.borderTopColor : parseFloat(cs.borderBottomWidth) ? cs.borderBottomColor : parseFloat(cs.borderLeftWidth) ? cs.borderLeftColor : cs.borderRightColor;
      add('Stroke', `${w} ${toHex(sideColor)}`, sideColor);
    }
    const rad = boxStr(cs.borderTopLeftRadius, cs.borderTopRightRadius, cs.borderBottomRightRadius, cs.borderBottomLeftRadius);
    if (rad !== '0') add('Radius', rad);
    if (cs.boxShadow !== 'none') add('Shadow', cs.boxShadow);
    if (cs.opacity !== '1') add('Opacity', cs.opacity);
    this.info.innerHTML = `<div class="inspect-info-head">${esc(tag)}${this.pinned ? '  · pinned' : ''}</div><dl>${rows.join('')}</dl>`;
  }
}
