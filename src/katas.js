/* ================= Data pipeline drills ================= */
const KATA_NOW = new Date('2026-10-06T12:00:00');
const KATA_GROUP_ORDER = ['Today', 'Yesterday', 'Previous 7 days', 'Older'];
function kataGetDateGroup(iso) {
  const day = (d) => { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; };
  const days = Math.round((day(KATA_NOW) - day(iso)) / 86400000);
  if (days <= 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days <= 7) return 'Previous 7 days';
  return 'Older';
}

// refs use the same helper name the drills expose
const getDateGroup = kataGetDateGroup;

const KATA_DATA = {
  people: [
    { id: 'u1', name: 'Ada Lovelace', email: 'ada@example.com', team: 'Research' },
    { id: 'u2', name: 'Grace Hopper', email: 'grace@example.com', team: 'Platform' },
    { id: 'u3', name: 'Alan Turing', email: 'alan@example.com', team: 'Research' },
    { id: 'u4', name: 'Katherine Johnson', email: 'kj@example.com', team: 'Applied' },
    { id: 'u5', name: 'Linus Pauling', email: 'linus@example.com', team: 'Platform' },
    { id: 'u6', name: 'Margaret Hamilton', email: 'margaret@example.com', team: 'Applied' },
  ],
  orders: [
    { id: 'A1', customer: 'Northwind', amount: 1290.5, status: 'paid' },
    { id: 'A2', customer: 'Blue Fern', amount: 342, status: 'pending' },
    { id: 'A3', customer: 'Kestrel', amount: 87.25, status: 'refunded' },
    { id: 'A4', customer: 'Atlas', amount: 5120, status: 'paid' },
    { id: 'A5', customer: 'Juniper', amount: 760, status: 'pending' },
    { id: 'A6', customer: 'Orchid', amount: 45, status: 'paid' },
  ],
  conversations: [
    { id: 'c3', title: 'Draft launch email', updatedAt: '2026-10-05T16:20:00', starred: false },
    { id: 'c7', title: 'Trip plan: Kyoto', updatedAt: '2026-09-20T18:00:00', starred: false },
    { id: 'c1', title: 'Refactor billing webhook', updatedAt: '2026-10-06T09:15:00', starred: false },
    { id: 'c5', title: 'Summarize interview notes', updatedAt: '2026-10-03T14:00:00', starred: true },
    { id: 'c2', title: 'Explain CSS grid', updatedAt: '2026-10-06T07:40:00', starred: true },
    { id: 'c8', title: 'Debug useEffect', updatedAt: '2026-09-02T11:11:00', starred: false },
    { id: 'c4', title: 'SQL: weekly active users', updatedAt: '2026-10-05T10:05:00', starred: false },
    { id: 'c6', title: 'Regex for timestamps', updatedAt: '2026-10-01T09:30:00', starred: false },
  ],
  users: [
    { id: 'u1', name: 'Priya' },
    { id: 'u2', name: 'Jonas' },
    { id: 'u3', name: 'Lena' },
  ],
  messages: [
    { id: 'm1', userId: 'u2', text: 'Deploy is green', read: true },
    { id: 'm2', userId: 'u1', text: 'Review moved to Thursday', read: false },
    { id: 'm3', userId: 'u3', text: 'Mockups attached', read: false },
    { id: 'm4', userId: 'u1', text: 'Thanks!', read: true },
    { id: 'm5', userId: 'u2', text: 'Chart axis at zero?', read: false },
  ],
  todos: [
    { id: 1, title: 'Fix truncation', done: false },
    { id: 2, title: 'Add empty state', done: true },
    { id: 3, title: 'Write tests', done: false },
  ],
};

// Each drill: inputs are variable names available in your code. ref computes the expected output.
const KATAS = [
  // ---- One tool at a time ----
  { id: 'k1', group: 'One tool at a time', title: 'Keep some items',
    prompt: 'Return the people on the Research team.',
    inputs: ['people'], want: 'an array of person objects (fewer than you started with)',
    ref: ({ people }) => people.filter((p) => p.team === 'Research'),
    hint: 'Keeping some items → <code>filter</code>. Your function returns true for the ones to keep.',
    why: '<code>filter</code> always returns an array, possibly empty, with the same kind of items as the input.' },
  { id: 'k2', group: 'One tool at a time', title: 'Reshape every item',
    prompt: 'Return just the names, as an array of strings.',
    inputs: ['people'], want: 'an array of strings, same length as people',
    ref: ({ people }) => people.map((p) => p.name),
    hint: 'One output per input, but a different shape → <code>map</code>.',
    why: '<code>map</code> always returns an array of the same length. What goes in each slot is whatever your function returns.' },
  { id: 'k3', group: 'One tool at a time', title: 'Get one item',
    prompt: "Return the person whose id is 'u3' (the object itself, not an array).",
    inputs: ['people'], want: 'one person object',
    ref: ({ people }) => people.find((p) => p.id === 'u3'),
    hint: 'Exactly one thing → <code>find</code>. Not <code>filter</code>, which would give you an array with one item in it.',
    why: '<code>find</code> returns the first match, or <code>undefined</code> if nothing matches. That\'s why you write <code>if (!selected)</code> before using it.' },
  { id: 'k4', group: 'One tool at a time', title: 'Count something',
    prompt: 'Return how many messages are unread.',
    inputs: ['messages'], want: 'a number',
    ref: ({ messages }) => messages.filter((m) => !m.read).length,
    hint: 'Count of a subset → <code>filter(...).length</code>.',
    why: 'Counting one kind of thing doesn\'t need <code>reduce</code>. Filter, then take the length.' },
  { id: 'k5', group: 'One tool at a time', title: 'Yes or no',
    prompt: 'Return true if any order is still pending.',
    inputs: ['orders'], want: 'a boolean',
    ref: ({ orders }) => orders.some((o) => o.status === 'pending'),
    hint: '"Is there any…" → <code>some</code>. "Are all…" → <code>every</code>.',
    why: '<code>some</code> stops at the first match and returns true or false.' },
  { id: 'k6', group: 'One tool at a time', title: 'Change the order',
    prompt: 'Return the order ids, biggest amount first. Don\'t change the original array.',
    inputs: ['orders'], want: 'an array of id strings',
    ref: ({ orders }) => [...orders].sort((a, b) => b.amount - a.amount).map((o) => o.id),
    hint: 'Copy first: <code>[...orders].sort((a, b) =&gt; b.amount - a.amount)</code>, then <code>map</code> to ids. <code>b - a</code> = biggest first.',
    why: '<code>sort</code> changes the array it\'s called on. On state, that\'s a bug, so always sort a copy.' },
  { id: 'k7', group: 'One tool at a time', title: 'Add up',
    prompt: 'Return the total amount of all paid orders.',
    inputs: ['orders'], want: 'a number',
    ref: ({ orders }) => orders.filter((o) => o.status === 'paid').reduce((sum, o) => sum + o.amount, 0),
    hint: 'Filter to paid, then <code>reduce((sum, o) =&gt; sum + o.amount, 0)</code>. The <code>0</code> is the starting total.',
    why: 'Many values → one value is what <code>reduce</code> is for. The starting value decides the output\'s shape: <code>0</code> gives a number.' },
  { id: 'k8', group: 'One tool at a time', title: 'Unique values',
    prompt: 'Return the list of teams, each once, A to Z.',
    inputs: ['people'], want: 'an array of strings, no duplicates',
    ref: ({ people }) => [...new Set(people.map((p) => p.team))].sort(),
    hint: '<code>map</code> to teams → <code>new Set(...)</code> removes duplicates → spread back into an array → <code>sort()</code>.',
    why: 'A <code>Set</code> is not an array (no <code>.map</code>), so spread it: <code>[...new Set(x)]</code>.' },

  // ---- Arrays and objects ----
  { id: 'k9', group: 'Arrays ↔ objects', title: 'Count per kind',
    prompt: 'Return how many orders have each status, like <code>{ paid: 3, pending: 2, refunded: 1 }</code>.',
    inputs: ['orders'], want: 'an object: status → count',
    ref: ({ orders }) => orders.reduce((acc, o) => { acc[o.status] = (acc[o.status] || 0) + 1; return acc; }, {}),
    hint: '<code>reduce</code> starting from <code>{}</code>: for each order, <code>acc[o.status] = (acc[o.status] || 0) + 1</code>, then <code>return acc</code>.',
    why: 'Starting <code>reduce</code> with <code>{}</code> builds an object. Brackets <code>acc[o.status]</code> because the key is in a variable.' },
  { id: 'k10', group: 'Arrays ↔ objects', title: 'Group with groupBy',
    prompt: 'Group people by team using <code>Object.groupBy</code>. Return what it gives you.',
    inputs: ['people'], want: 'an object: team → array of people',
    ref: ({ people }) => Object.groupBy(people, (p) => p.team),
    hint: '<code>return Object.groupBy(people, (p) =&gt; p.team);</code> Look at the shape in the output: it\'s an object, not an array.',
    why: '<code>Object.groupBy</code> returns an <b>object</b>. Keys are the group names; values are arrays. You can\'t <code>.map()</code> it directly.' },
  { id: 'k11', group: 'Arrays ↔ objects', title: 'Object → array you can render',
    prompt: 'Group people by team, then turn it into an array like <code>[{ team: "Research", count: 2 }, …]</code>.',
    inputs: ['people'], want: 'an array of { team, count }',
    ref: ({ people }) => Object.entries(Object.groupBy(people, (p) => p.team)).map(([team, list]) => ({ team, count: list.length })),
    hint: '<code>Object.entries(grouped)</code> gives <code>[[key, value], …]</code>. Then <code>.map(([team, list]) =&gt; ({ team, count: list.length }))</code>.',
    why: 'This is the bridge: object → <code>Object.entries</code> → array → <code>map</code> → JSX. Parentheses around <code>{ }</code> to return an object from an arrow.' },
  { id: 'k12', group: 'Arrays ↔ objects', title: 'Lookup table by id',
    prompt: 'Turn users into an object keyed by id: <code>{ u1: { id, name }, u2: … }</code>.',
    inputs: ['users'], want: 'an object: id → user',
    ref: ({ users }) => Object.fromEntries(users.map((u) => [u.id, u])),
    hint: 'Make pairs with <code>map((u) =&gt; [u.id, u])</code>, then <code>Object.fromEntries(...)</code>. (A <code>reduce</code> works too.)',
    why: 'Use an object when you\'ll look things up by key many times: <code>byId[\'u2\']</code> is instant, instead of a <code>find</code> each time.' },
  { id: 'k13', group: 'Arrays ↔ objects', title: 'Combine two lists',
    prompt: 'Return each message as a string <code>"Name: text"</code>, using the users list for names.',
    inputs: ['messages', 'users'], want: 'an array of strings',
    ref: ({ messages, users }) => { const byId = Object.fromEntries(users.map((u) => [u.id, u])); return messages.map((m) => `${byId[m.userId].name}: ${m.text}`); },
    hint: 'Build the lookup from the last drill, then <code>messages.map((m) =&gt; `${byId[m.userId].name}: ${m.text}`)</code>.',
    why: 'Joining two lists = a lookup object + a <code>map</code>. You could <code>find</code> inside the map instead; it\'s fine for small lists.' },
  { id: 'k14', group: 'Arrays ↔ objects', title: 'Update one item (state-safe)',
    prompt: 'Return a NEW todos array where todo id 3 is marked done. Don\'t change the original.',
    inputs: ['todos'], want: 'an array of todos, same length',
    ref: ({ todos }) => todos.map((t) => (t.id === 3 ? { ...t, done: true } : t)),
    hint: '<code>todos.map((t) =&gt; t.id === 3 ? { ...t, done: true } : t)</code>',
    why: 'The setState pattern. <code>map</code> gives a new array; <code>{ ...t }</code> gives a new object for the changed one.' },

  // ---- Full pipelines ----
  { id: 'k15', group: 'Full pipelines', title: 'Search + sort',
    prompt: 'With <code>query = "e"</code>: return titles of conversations whose title contains the query (any case), newest first.',
    inputs: ['conversations'], want: 'an array of title strings',
    setup: 'const query = "e";',
    ref: ({ conversations }) => {
      const q = 'e';
      return conversations
        .filter((c) => c.title.toLowerCase().includes(q))
        .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
        .map((c) => c.title);
    },
    hint: 'Three steps, in order: <code>filter</code> (title lowercased includes q) → <code>sort</code> (newest first: <code>new Date(b.updatedAt) - new Date(a.updatedAt)</code>) → <code>map</code> to titles. <code>filter</code> already made a copy, so sorting after it is safe.',
    why: 'Filter first (less to sort), then sort, then shape for display.' },
  { id: 'k16', group: 'Full pipelines', title: 'Sections in a fixed order',
    prompt: 'Return sections for the sidebar: <code>[{ label: "Today", ids: [...] }, …]</code> in GROUP_ORDER, newest first inside each, skipping empty groups.',
    inputs: ['conversations'], helpers: true, want: 'an array of { label, ids }',
    ref: ({ conversations }) => {
      const sorted = [...conversations].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
      return KATA_GROUP_ORDER
        .map((label) => ({ label, ids: sorted.filter((c) => getDateGroup(c.updatedAt) === label).map((c) => c.id) }))
        .filter((s) => s.ids.length > 0);
    },
    hint: 'Sort a copy newest first. Then <code>GROUP_ORDER.map((label) =&gt; ({ label, ids: sorted.filter(c =&gt; getDateGroup(c.updatedAt) === label).map(c =&gt; c.id) }))</code>, then <code>.filter(s =&gt; s.ids.length &gt; 0)</code>.',
    why: 'Looping over the ORDER you want (not the data) guarantees "Today" comes first. This is the Chat sidebar mock.' },
  { id: 'k17', group: 'Full pipelines', title: 'Starred section first',
    prompt: 'Same as before, but starred chats go in a "Starred" section at the top and NOT in their date group.',
    inputs: ['conversations'], helpers: true, want: 'an array of { label, ids }',
    ref: ({ conversations }) => {
      const sorted = [...conversations].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
      const sections = [];
      const starred = sorted.filter((c) => c.starred);
      if (starred.length) sections.push({ label: 'Starred', ids: starred.map((c) => c.id) });
      KATA_GROUP_ORDER.forEach((label) => {
        const ids = sorted.filter((c) => !c.starred && getDateGroup(c.updatedAt) === label).map((c) => c.id);
        if (ids.length) sections.push({ label, ids });
      });
      return sections;
    },
    hint: 'Build the Starred section from <code>sorted.filter(c =&gt; c.starred)</code>. In the date groups, add <code>!c.starred &amp;&amp;</code> to the filter. Combine: <code>[starredSection, ...dateSections]</code> (skip any that are empty).',
    why: 'The mid-interview change. Because everything is derived, it\'s a few lines, not a rewrite.' },
  { id: 'k18', group: 'Full pipelines', title: 'Dashboard numbers',
    prompt: 'Return <code>{ total, paidCount, biggest }</code>: total of all amounts, number of paid orders, and the customer with the biggest order.',
    inputs: ['orders'], want: 'an object with 3 keys',
    ref: ({ orders }) => ({
      total: orders.reduce((s, o) => s + o.amount, 0),
      paidCount: orders.filter((o) => o.status === 'paid').length,
      biggest: [...orders].sort((a, b) => b.amount - a.amount)[0].customer,
    }),
    hint: 'Three separate small calculations, then put them in one object. Biggest: sort a copy by amount descending and take <code>[0]</code>.',
    why: 'Stat cards are just several small derived values. Write each on its own line; don\'t force it into one reduce.' },
];

/* ---------- shape description and comparison ---------- */
function describeShape(v) {
  if (v === undefined) return 'undefined (nothing returned)';
  if (v === null) return 'null';
  if (Array.isArray(v)) {
    if (!v.length) return 'array (empty)';
    const inner = v[0] === null ? 'null' : Array.isArray(v[0]) ? 'arrays' : typeof v[0] === 'object' ? 'objects' : typeof v[0] + 's';
    return `array of ${v.length} ${inner}`;
  }
  if (v instanceof Set) return `Set of ${v.size} (not an array: spread it with [...set])`;
  if (typeof v === 'object') {
    const keys = Object.keys(v);
    return `object with ${keys.length} key${keys.length === 1 ? '' : 's'}: ${keys.slice(0, 5).join(', ')}${keys.length > 5 ? ', …' : ''}`;
  }
  return typeof v;
}

function deepEqual(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) < 1e-9;
  if (a === b) return true;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) return a.length === b.length && a.every((x, i) => deepEqual(x, b[i]));
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    return ka.length === kb.length && ka.every((k) => Object.prototype.hasOwnProperty.call(b, k) && deepEqual(a[k], b[k]));
  }
  return false;
}

function showValue(v) {
  if (v === undefined) return 'undefined';
  if (v instanceof Set) return 'Set ' + JSON.stringify([...v]);
  try { return JSON.stringify(v, null, 2); } catch (e) { return String(v); }
}

function mountKatas(el) {
  const filter = el.dataset.katas;
  const list = KATAS.filter((k) => !filter || k.group === filter);
  el.className = 'katas';
  list.forEach((k) => {
    const card = document.createElement('section');
    card.className = 'kata';
    const solved = Progress.get('kata:' + k.id);
    const inputsText = k.inputs.map((n) => `const ${n} = ${JSON.stringify(KATA_DATA[n], null, 2)};`).join('\n\n');
    const expected = k.ref(JSON.parse(JSON.stringify(KATA_DATA)));
    const starter = Progress.get('kata-code:' + k.id) || `${k.setup ? k.setup + '\n' : ''}return ;`;
    card.innerHTML = `
      <div class="kata-head">
        <span class="kata-status ${solved ? 'is-done' : ''}">${solved ? '✓' : ''}</span>
        <h3>${esc(k.title)}</h3>
      </div>
      <p class="kata-prompt">${k.prompt}</p>
      <p class="kata-want"><b>Output shape:</b> ${esc(k.want)}</p>
      <details class="kata-data"><summary>Input data: ${k.inputs.map((n) => `<code>${n}</code>`).join(', ')}${k.helpers ? ' + <code>getDateGroup(iso)</code>, <code>GROUP_ORDER</code>' : ''}</summary><pre>${highlight(inputsText, 'js')}${k.helpers ? '\n\n' + highlight(`const GROUP_ORDER = ${JSON.stringify(KATA_GROUP_ORDER)};\n// getDateGroup('2026-10-05T10:05:00') → 'Yesterday'  (today is Oct 6)`, 'js') : ''}</pre></details>
      <div class="kata-editor"></div>
      <div class="kata-bar">
        <button class="ld-btn kata-run">Run ▶</button>
        <button class="ld-btn kata-hint">Hint</button>
        <button class="ld-btn kata-sol">Show answer</button>
        <span class="kata-verdict" role="status"></span>
      </div>
      <p class="kata-hinttext" hidden>${k.hint}</p>
      <div class="kata-out">
        <div><div class="kata-out-label">Your output <span class="kata-shape-yours"></span></div><pre class="kata-yours">Press Run</pre></div>
        <div><div class="kata-out-label">Expected <span>${esc(describeShape(expected))}</span></div><pre>${esc(showValue(expected))}</pre></div>
      </div>
      <div class="kata-why" hidden><b>Why:</b> ${k.why}<pre class="kata-solcode"></pre></div>`;
    el.appendChild(card);

    const editor = new CodeEditor(card.querySelector('.kata-editor'), {
      id: 'kata-' + k.id,
      onChange: (v) => Progress.set('kata-code:' + k.id, v),
      onRun: () => run(),
      onCursor: () => {},
    });
    editor.ta.setAttribute('aria-label', k.title + ' code');
    editor.setValue(starter, 'js', false);

    const verdict = card.querySelector('.kata-verdict');
    const yours = card.querySelector('.kata-yours');
    const yoursShape = card.querySelector('.kata-shape-yours');

    function run() {
      const data = JSON.parse(JSON.stringify(KATA_DATA));
      const before = JSON.stringify(k.inputs.map((n) => data[n]));
      let result;
      let error = null;
      try {
        const fn = new Function(...k.inputs, 'getDateGroup', 'GROUP_ORDER', editor.ta.value);
        result = fn(...k.inputs.map((n) => data[n]), kataGetDateGroup, KATA_GROUP_ORDER.slice());
      } catch (e) {
        error = e;
      }
      if (error) {
        yours.textContent = `${error.name}: ${error.message}`;
        yoursShape.textContent = '';
        verdict.textContent = 'Error. Read the message on the left.';
        verdict.className = 'kata-verdict is-bad';
        return;
      }
      yours.textContent = showValue(result);
      yoursShape.textContent = describeShape(result);
      const mutated = JSON.stringify(k.inputs.map((n) => data[n])) !== before;
      const ok = deepEqual(result, expected);
      if (ok && !mutated) {
        verdict.textContent = 'Correct ✓';
        verdict.className = 'kata-verdict is-ok';
        Progress.set('kata:' + k.id, true);
        card.querySelector('.kata-status').textContent = '✓';
        card.querySelector('.kata-status').classList.add('is-done');
        card.querySelector('.kata-why').hidden = false;
      } else if (ok && mutated) {
        verdict.textContent = 'Right answer, but you changed the input data. Copy before sort/push.';
        verdict.className = 'kata-verdict is-warn';
      } else {
        verdict.textContent = result === undefined ? 'Nothing returned. Did you write return?' : 'Not yet. Compare the shapes first, then the values.';
        verdict.className = 'kata-verdict is-bad';
      }
    }
    card.querySelector('.kata-run').addEventListener('click', run);
    card.querySelector('.kata-hint').addEventListener('click', () => { card.querySelector('.kata-hinttext').hidden = false; });
    card.querySelector('.kata-sol').addEventListener('click', () => {
      const src = k.ref.toString()
        .replace(/^\(\{[^}]*\}\)\s*=>\s*/, '')
        .replace(/KATA_GROUP_ORDER/g, 'GROUP_ORDER')
        .replace(/^\{\n?/, '').replace(/\n?\s*\}$/, '');
      const body = /^\s*(const|let|return|if)\b/.test(src) ? src : 'return ' + src + ';';
      const solEl = card.querySelector('.kata-solcode');
      solEl.innerHTML = highlight(body.replace(/^ {6}/gm, ''), 'js');
      card.querySelector('.kata-why').hidden = false;
    });
  });
}
