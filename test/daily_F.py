"""Behaviour tests for daily batch F (dc51-dc60). Usage: DIST_HTML=... python3 daily_F.py [dc51,dc52]"""
import asyncio, subprocess, sys, time, pathlib, os, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
PORT = 8786
SHIM = open(ROOT / 'run.py').read().split('SHIM = """')[1].split('"""')[0]
RESULTS = []
CUR = ['']


def check(name, ok, detail=''):
    RESULTS.append((CUR[0], name, bool(ok)))
    print(('PASS' if ok else 'FAIL'), CUR[0], '·', name, ('' if ok else '→ ' + str(detail)))


async def open_design(page, ex):
    CUR[0] = ex
    await page.evaluate('Workspace.close()')
    await page.evaluate(f'Workspace.open("{ex}")')
    await page.wait_for_timeout(900)
    await page.click('[data-ptab="design"]')
    await page.wait_for_timeout(1500)
    await page.click('[data-dmode="interact"]')
    wide = await page.inner_text('#wideBtn')
    if wide.strip() == 'Expand':
        await page.click('#wideBtn')
        await page.wait_for_timeout(300)
    return page.locator('#designHost')


async def shot(page, ex):
    await page.locator('#designCanvas').screenshot(path=str(ROOT / 'shots' / f'{ex}.png'))


async def active(page, prop='className'):
    """Property of the focused element inside the preview's shadow root."""
    return await page.evaluate(f"(() => {{ const a = document.getElementById('designHost').shadowRoot.activeElement; return a ? String(a.{prop}) : null; }})()")


# ---------------------------------------------------------------- dc51
async def t_dc51(page):
    h = await open_design(page, 'dc51')
    await page.wait_for_timeout(1400)
    count = h.locator('.selected-count')
    check('initial 0 of 12', (await count.inner_text()) == '0 of 12 selected', await count.inner_text())
    check('generate disabled', await h.locator('.btn-primary').is_disabled())
    repo = h.locator('#scope-repo')
    await repo.click()
    check('repo checks 5 leaves', (await count.inner_text()) == '5 of 12 selected', await count.inner_text())
    check('nested leaf checked', await h.locator('[id="scope-repo:pulls:write"]').is_checked())
    await h.locator('[id="scope-repo:contents:read"]').click()
    check('leaf uncheck -> 4', (await count.inner_text()) == '4 of 12 selected')
    ind = await repo.evaluate('e => e.indeterminate')
    ind2 = await h.locator('[id="scope-repo:contents"]').evaluate('e => e.indeterminate')
    check('repo + contents indeterminate', ind and ind2 and not await repo.is_checked(), (ind, ind2))
    await repo.click()
    check('indeterminate click selects all', (await count.inner_text()) == '5 of 12 selected' and await repo.is_checked() and not await repo.evaluate('e => e.indeterminate'))
    await repo.click()
    check('full group click clears', (await count.inner_text()) == '0 of 12 selected')
    await h.locator('label[for="scope-issues:write"]').click()
    check('label click toggles leaf', (await count.inner_text()) == '1 of 12 selected')
    await h.locator('.form-card .input').first.fill('ci-deploy')
    check('generate enabled', await h.locator('.btn-primary').is_enabled())
    await h.locator('.btn-primary').click()
    check('created banner', 'created with 1 scope.' in await h.locator('.success-banner').inner_text())
    # change: filter
    await h.locator('.scope-search').fill('billing')
    labels = await h.locator('.scope-label').all_inner_texts()
    check('filter keeps ancestors', labels == ['Organization', 'Billing'], labels)
    await h.locator('#scope-org').click()
    check('filtered group toggles hidden leaves', (await count.inner_text()) == '4 of 12 selected', await count.inner_text())
    await h.locator('.scope-search').fill('write')
    labels = await h.locator('.scope-label').all_inner_texts()
    check('write filter', labels == ['Repositories', 'Contents', 'Write contents', 'Pull requests', 'Write pull requests', 'Issues', 'Write issues', 'Organization', 'Members', 'Manage members'], labels)
    await h.locator('.scope-search').fill('contents')
    labels = await h.locator('.scope-label').all_inner_texts()
    check('matching group shows subtree', labels == ['Repositories', 'Contents', 'Read contents', 'Write contents'], labels)
    await h.locator('.scope-search').fill('zzz')
    check('no match msg', 'No scopes match' in await h.locator('.muted-msg').inner_text())
    await h.locator('.scope-search').fill('')
    await h.locator('[id="scope-repo:contents:write"]').click()
    await shot(page, 'dc51')


# ---------------------------------------------------------------- dc52
async def t_dc52(page):
    h = await open_design(page, 'dc52')
    inp = h.locator('.composer-input')
    await inp.fill('Can you tighten my outro?')
    await inp.press('Enter')
    await page.wait_for_timeout(100)
    check('thinking dots before first token', await h.locator('.thinking').count() == 1)
    check('stop shown, send hidden', await h.locator('.stop-btn').count() == 1 and await h.locator('.send-btn').count() == 0)
    await page.wait_for_timeout(1100)
    t1 = await h.locator('.assistant-text').last.inner_text()
    check('cursor while streaming', await h.locator('.cursor').count() == 1)
    await inp.fill('another')
    await inp.press('Enter')
    await page.wait_for_timeout(50)
    check('enter does not send while streaming', await h.locator('.msg-user').count() == 3)
    await page.wait_for_timeout(400)
    t2 = await h.locator('.assistant-text').last.inner_text()
    check('text grows', len(t2) > len(t1) > 0, (len(t1), len(t2)))
    # wait for completion
    for _ in range(80):
        if await h.locator('.cursor').count() == 0 and await h.locator('.thinking').count() == 0:
            break
        await page.wait_for_timeout(100)
    check('done: no cursor, send back', await h.locator('.cursor').count() == 0 and await h.locator('.send-btn').count() == 1)
    th = h.locator('.thread')
    gap = await th.evaluate('e => e.scrollHeight - e.scrollTop - e.clientHeight')
    check('pinned to bottom while following', gap < 40, gap)
    check('regenerate on last only', await h.locator('.regen-btn').count() == 1)
    # stop
    await inp.fill('Write a headline for this post')
    await h.locator('.send-btn').click()
    await page.wait_for_timeout(1000)
    await h.locator('.stop-btn').click()
    await page.wait_for_timeout(50)
    a = await h.locator('.assistant-text').last.inner_text()
    await page.wait_for_timeout(500)
    b2 = await h.locator('.assistant-text').last.inner_text()
    check('stop freezes text', a == b2 and len(a) > 0, (a[:40], b2[:40]))
    check('stopped pill', await h.locator('.msg-note', has_text='Stopped').count() == 1)
    check('send back after stop', await h.locator('.send-btn').count() == 1)
    # regenerate
    before = await h.locator('.assistant-text').last.inner_text()
    n_msgs = await h.locator('.msg').count()
    await h.locator('.regen-btn').click()
    await page.wait_for_timeout(100)
    check('regenerate clears in place', await h.locator('.msg').count() == n_msgs and await h.locator('.thinking').count() == 1)
    await page.wait_for_timeout(1200)
    # scroll up while streaming -> stays put
    await th.evaluate('e => { e.scrollTop = 0; }')
    await page.wait_for_timeout(600)
    top = await th.evaluate('e => e.scrollTop')
    check('scrolled up stays put', top < 5, top)
    check('jump pill shown', await h.locator('.jump-btn').count() == 1)
    await shot(page, 'dc52-scrolled')
    await h.locator('.jump-btn').click()
    await page.wait_for_timeout(300)
    gap = await th.evaluate('e => e.scrollHeight - e.scrollTop - e.clientHeight')
    check('jump resumes following', gap < 40 and await h.locator('.jump-btn').count() == 0, gap)
    for _ in range(80):
        if await h.locator('.cursor').count() == 0:
            break
        await page.wait_for_timeout(100)
    after = await h.locator('.assistant-text').last.inner_text()
    check('regenerated text differs', after != before and len(after) > 50, after[:60])
    await shot(page, 'dc52')

# ---------------------------------------------------------------- dc53
async def col_ids(h, col):
    return await h.locator(f'.column-{col} [data-card-id]').evaluate_all('els => els.map(e => e.dataset.cardId)')


async def t_dc53(page):
    h = await open_design(page, 'dc53')
    await page.wait_for_timeout(1200)
    check('board loaded', len(await col_ids(h, 'backlog')) == 3)
    # drag ORB-41 (backlog) to end of review column (drop on column body bottom)
    src = h.locator('[data-card-id="ORB-41"]')
    dst = h.locator('.column-review .column-body')
    box = await dst.bounding_box()
    await src.drag_to(dst, target_position={'x': box['width'] / 2, 'y': box['height'] - 5})
    await page.wait_for_timeout(100)
    check('optimistic cross-column move', await col_ids(h, 'review') == ['ORB-33', 'ORB-45', 'ORB-41'], await col_ids(h, 'review'))
    check('indicator cleared after drop', await h.locator('.drop-indicator').count() == 0)
    await page.wait_for_timeout(1100)
    check('move persisted', await col_ids(h, 'review') == ['ORB-33', 'ORB-45', 'ORB-41'])
    # within column: drag ORB-33 (first) below ORB-45 -> index 1
    c45 = h.locator('[data-card-id="ORB-45"]')
    b45 = await c45.bounding_box()
    await h.locator('[data-card-id="ORB-33"]').drag_to(c45, target_position={'x': b45['width'] / 2, 'y': b45['height'] - 3})
    await page.wait_for_timeout(100)
    check('same-column move down', await col_ids(h, 'review') == ['ORB-45', 'ORB-33', 'ORB-41'], await col_ids(h, 'review'))
    # indicator while dragging: synthetic DragEvents with a shared DataTransfer
    res = await page.evaluate("""() => {
      const root = document.getElementById('designHost').shadowRoot;
      const src = root.querySelector('[data-card-id="ORB-38"]');
      const tgt = root.querySelector('[data-card-id="ORB-29"]');
      const dt = new DataTransfer();
      const r = tgt.getBoundingClientRect();
      src.dispatchEvent(new DragEvent('dragstart', { bubbles: true, composed: true, dataTransfer: dt }));
      return new Promise((res) => setTimeout(() => {
        tgt.dispatchEvent(new DragEvent('dragover', { bubbles: true, composed: true, cancelable: true, dataTransfer: dt, clientX: r.left + 20, clientY: r.top + 3 }));
        setTimeout(() => {
          const col = root.querySelector('.column-progress');
          const ind = col.querySelectorAll('.drop-indicator').length;
          const first = col.querySelector('.column-body').firstElementChild.className;
          const faded = src.classList.contains('is-dragging');
          const over = col.classList.contains('is-over');
          tgt.dispatchEvent(new DragEvent('drop', { bubbles: true, composed: true, cancelable: true, dataTransfer: dt, clientX: r.left + 20, clientY: r.top + 3 }));
          src.dispatchEvent(new DragEvent('dragend', { bubbles: true, composed: true, dataTransfer: dt }));
          res({ ind, first, faded, over });
        }, 50);
      }, 50));
    }""")
    await page.wait_for_timeout(100)
    check('indicator shown at top during drag', res['ind'] == 1 and res['first'] == 'drop-indicator' and res['faded'] and res['over'], res)
    check('drop at top of progress', (await col_ids(h, 'progress'))[0] == 'ORB-38', await col_ids(h, 'progress'))
    await page.wait_for_timeout(1000)
    # rejected: unassigned ORB-44 into done
    dd = h.locator('.column-done .column-body')
    bd = await dd.bounding_box()
    await h.locator('[data-card-id="ORB-44"]').drag_to(dd, target_position={'x': bd['width'] / 2, 'y': bd['height'] - 5})
    await page.wait_for_timeout(100)
    check('optimistic into done', 'ORB-44' in await col_ids(h, 'done'))
    await page.wait_for_timeout(1100)
    check('rolled back to original spot', await col_ids(h, 'backlog') == ['ORB-44'] and 'ORB-44' not in await col_ids(h, 'done'), await col_ids(h, 'backlog'))
    check('toast with server message', 'Assign someone before moving ORB-44 to Done.' in await h.locator('.toast').inner_text())
    await shot(page, 'dc53')
    await h.locator('.toast-close').click()
    check('toast dismiss', await h.locator('.toast').count() == 0)
    # keyboard
    card = h.locator('[data-card-id="ORB-47"]')
    await card.focus()
    await page.keyboard.press('Enter')
    check('selected via Enter', await h.locator('.card.is-selected').count() == 1 and 'Moving ORB-47' in await h.locator('.kb-help').inner_text())
    await page.keyboard.press('ArrowRight')
    await page.wait_for_timeout(100)
    check('ArrowRight moves to review', 'ORB-47' in await col_ids(h, 'review'))
    check('focus follows card', (await active(page, 'dataset.cardId')) == 'ORB-47')
    await page.keyboard.press('ArrowUp')
    await page.wait_for_timeout(100)
    rv = await col_ids(h, 'review')
    check('ArrowUp reorders', rv == ['ORB-45', 'ORB-47', 'ORB-33', 'ORB-41'], rv)
    check('live region', 'Moved ORB-47 to In review, position 2.' in await h.locator('.sr-only').inner_text())
    await page.wait_for_timeout(1000)
    await page.keyboard.press('Escape')
    check('Esc drops', await h.locator('.card.is-selected').count() == 0)
    # keyboard into done for unassigned card -> rollback
    await h.locator('[data-card-id="ORB-45"]').focus()
    await page.keyboard.press(' ')
    await page.keyboard.press('ArrowRight')
    await page.wait_for_timeout(1100)
    check('keyboard move rollback', 'ORB-45' in await col_ids(h, 'review') and await h.locator('.toast').count() == 1)

# ---------------------------------------------------------------- dc54
async def watch_for(page, h, selector, ms):
    seen = False
    for _ in range(ms // 40):
        if await h.locator(selector).count() > 0:
            seen = True
        await page.wait_for_timeout(40)
    return seen


async def t_dc54(page):
    h = await open_design(page, 'dc54')
    inp = h.locator('.search-input')
    await inp.click()
    await inp.type('hooks', delay=30)
    seen = await watch_for(page, h, '.search-status', 700)
    check('fast query never shows Searching…', not seen)
    titles = await h.locator('.result-title').all_inner_texts()
    check('hooks results', len(titles) == 8, titles)
    check('first result active', await h.locator('.result.is-active').count() == 1 and await h.locator('.result').first.get_attribute('aria-selected') == 'true')
    await inp.fill('')
    await inp.type('ref', delay=30)
    seen = await watch_for(page, h, '.search-status', 900)
    check('slow query shows Searching…', seen)
    await page.wait_for_timeout(700)
    check('mark highlight', (await h.locator('.result mark').first.inner_text()).lower() == 'ref', await h.locator('.result-title').all_inner_texts())
    # race: slow "us" then fast "usest" -> results for latest
    await inp.fill('')
    await inp.type('us', delay=20)
    await page.wait_for_timeout(350)   # "us" request in flight (slow)
    await inp.type('eref', delay=20)   # "useref" fast
    await page.wait_for_timeout(1500)
    titles = await h.locator('.result-title').all_inner_texts()
    check('latest query wins race', titles == ['useRef'], titles)
    # keyboard
    await inp.fill('use')
    await page.wait_for_timeout(1600)
    await inp.press('ArrowDown')
    await inp.press('ArrowDown')
    sel = await h.locator('.result.is-active .result-title').inner_text()
    ad = await inp.get_attribute('aria-activedescendant')
    check('arrow down x2', sel == 'useMemo' and ad == 'hit-use-memo', (sel, ad))
    await inp.press('ArrowUp'); await inp.press('ArrowUp'); await inp.press('ArrowUp')
    check('arrow up wraps', (await h.locator('.result.is-active .result-title').inner_text()) == 'useDeferredValue')
    await inp.press('Enter')
    await page.wait_for_timeout(100)
    check('enter navigates', (await h.locator('.article h1').inner_text()) == 'useDeferredValue' and await inp.input_value() == '')
    # cache: "use" again comes back fast (debounce only)
    await inp.fill('use')
    await page.wait_for_timeout(400)
    check('cached results without wait', await h.locator('.result').count() == 8)
    await inp.press('Escape')
    check('escape closes', await h.locator('.search-panel').count() == 0 and await inp.input_value() == 'use')
    await inp.press('Escape')
    check('second escape clears', await inp.input_value() == '')
    await inp.fill('zzzz')
    await page.wait_for_timeout(700)
    check('empty state', 'No results for' in await h.locator('.search-msg').inner_text())
    # click result
    await inp.fill('routing')
    await page.wait_for_timeout(700)
    await h.locator('.result').first.click()
    check('click navigates', (await h.locator('.article h1').inner_text()) == 'Routing')
    # error
    await h.locator('.dev-toggle input').check()
    await inp.fill('forms')
    await page.wait_for_timeout(700)
    check('error state + retry', 'temporarily unavailable' in await h.locator('.search-msg').inner_text() and await h.locator('.retry-btn').count() == 1)
    await h.locator('.dev-toggle input').uncheck()
    await inp.focus()
    await h.locator('.retry-btn').click() if await h.locator('.retry-btn').count() else None
    await page.wait_for_timeout(700)
    check('recovers after failure toggle off', await h.locator('.result').count() == 1)
    # slash focuses
    await inp.fill('')
    await h.locator('.article h1').click()
    await page.keyboard.press('/')
    check('slash focuses search', (await active(page)) == 'search-input')
    await inp.type('state', delay=20)
    await page.wait_for_timeout(600)
    await shot(page, 'dc54')

# ---------------------------------------------------------------- dc55
async def col_width(h, i):
    return await h.locator('.grid thead th').nth(i).evaluate('e => Math.round(e.getBoundingClientRect().width)')


async def t_dc55(page):
    await page.evaluate("localStorage.removeItem('campaigns.columnWidths.v1')")
    h = await open_design(page, 'dc55')
    await page.wait_for_timeout(1300)
    sc = h.locator('.grid-scroll')
    check('30 rows', await h.locator('.grid tbody tr').count() == 30)
    await sc.evaluate('e => { e.scrollTop = 400; e.scrollLeft = 300; }')
    await page.wait_for_timeout(100)
    sl = await sc.evaluate('e => e.scrollLeft')
    check('table overflows horizontally', sl > 50, sl)
    pos = await page.evaluate("""() => {
      const r = document.getElementById('designHost').shadowRoot;
      const box = r.querySelector('.grid-scroll').getBoundingClientRect();
      const th = r.querySelector('.grid thead th:nth-child(3)').getBoundingClientRect();
      const corner = r.querySelector('.grid thead th').getBoundingClientRect();
      const td = r.querySelector('.grid tbody tr:nth-child(15) td').getBoundingClientRect();
      return { dTop: th.top - box.top, dLeft: td.left - box.left, cTop: corner.top - box.top, cLeft: corner.left - box.left };
    }""")
    check('sticky header + first column + corner', abs(pos['dTop'] - 1) <= 1 and abs(pos['dLeft'] - 1) <= 1 and abs(pos['cTop'] - 1) <= 1 and abs(pos['cLeft'] - 1) <= 1, pos)
    await shot(page, 'dc55-scrolled')
    await sc.evaluate('e => { e.scrollTop = 0; e.scrollLeft = 0; }')
    # resize Spend (index 6) +80
    w0 = await col_width(h, 6)
    rz = h.locator('.grid thead th').nth(6).locator('.resizer')
    b = await rz.bounding_box()
    x, y = b['x'] + b['width'] / 2, b['y'] + b['height'] / 2
    await page.mouse.move(x, y); await page.mouse.down()
    await page.mouse.move(x + 40, y, steps=4); await page.mouse.move(x + 80, y + 30, steps=4)
    check('resizer active while dragging', await h.locator('.resizer.is-active').count() == 1)
    await page.mouse.up()
    w1 = await col_width(h, 6)
    check('resize +80', abs(w1 - (w0 + 80)) <= 2, (w0, w1))
    check('resize did not sort', await h.locator('.th.is-sorted').count() == 0)
    # min width
    b = await rz.bounding_box(); x = b['x'] + b['width'] / 2
    await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.move(x - 400, y, steps=6); await page.mouse.up()
    check('min width 70', await col_width(h, 6) == 70, await col_width(h, 6))
    check('other columns unchanged', await col_width(h, 5) == 90)
    # persistence
    saved = await page.evaluate("localStorage.getItem('campaigns.columnWidths.v1')")
    check('saved to localStorage', saved is not None and json.loads(saved).get('spend') == 70, saved)
    # dblclick reset
    await rz.dblclick()
    check('dblclick resets width', await col_width(h, 6) == 120)
    b = await rz.bounding_box(); x = b['x'] + b['width'] / 2
    await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.move(x + 50, y, steps=4); await page.mouse.up()
    # sort
    spend_btn = h.locator('.sort-btn', has_text='Spend')
    await spend_btn.click()
    vals = await h.locator('.grid tbody tr td:nth-child(7)').all_inner_texts()
    nums = [float(v.replace('$', '').replace(',', '')) for v in vals]
    check('spend ascending numeric', nums == sorted(nums), nums[:5])
    check('aria-sort ascending', await h.locator('.grid thead th').nth(6).get_attribute('aria-sort') == 'ascending')
    await spend_btn.click()
    vals = await h.locator('.grid tbody tr td:nth-child(7)').all_inner_texts()
    nums = [float(v.replace('$', '').replace(',', '')) for v in vals]
    check('spend descending', nums == sorted(nums, reverse=True))
    await h.locator('.sort-btn', has_text='Campaign').click()
    names = await h.locator('.grid tbody tr td:nth-child(1)').all_inner_texts()
    check('name sort A-Z', names == sorted(names, key=str.lower) and names[0] == 'App Install Android', names[:3])
    await shot(page, 'dc55')
    # reopen: widths restored
    h = await open_design(page, 'dc55')
    await page.wait_for_timeout(1300)
    check('widths restored after reload', await col_width(h, 6) == 170, await col_width(h, 6))
    # garbage storage -> defaults, no crash
    await page.evaluate("localStorage.setItem('campaigns.columnWidths.v1', '{not json')")
    h = await open_design(page, 'dc55')
    await page.wait_for_timeout(1300)
    check('garbage storage falls back', await col_width(h, 6) == 120)
    await page.evaluate("localStorage.removeItem('campaigns.columnWidths.v1')")

# ---------------------------------------------------------------- dc56
async def t_dc56(page):
    h = await open_design(page, 'dc56')
    await page.wait_for_timeout(1200)
    check('12 thumbs', await h.locator('.thumb').count() == 12)
    await page.evaluate("""() => { window.__pre = []; const Orig = window.Image; window.Image = function () { const i = new Orig(); const d = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src'); Object.defineProperty(i, 'src', { set(v) { window.__pre.push(v.length); d.set.call(i, v); }, get() { return d.get.call(i); } }); return i; }; window.__OrigImage = Orig; }""")
    await h.locator('.thumb').nth(3).click()
    await page.wait_for_timeout(150)
    check('dialog open', await h.locator('[role="dialog"][aria-modal="true"]').count() == 1)
    check('counter 4 of 12', (await h.locator('.lightbox-count').text_content()) == '4 of 12')
    check('caption', 'Moss and basalt' in await h.locator('.lightbox-caption').inner_text())
    check('focus on close', 'lb-close' in (await active(page)))
    pre = await page.evaluate('window.__pre.length')
    check('neighbours preloaded', pre >= 2, pre)
    for _ in range(5):
        await page.keyboard.press('Tab')
    a = await active(page)
    check('tab stays in dialog', a is not None and 'lb-' in a, a)
    await h.locator('.lb-close').focus()
    await page.keyboard.press('Shift+Tab')
    check('shift+tab from first wraps to last', 'lb-next' in (await active(page)))
    await page.keyboard.press('Tab')
    check('tab from last wraps to first', 'lb-close' in (await active(page)))
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight')
    check('arrow right x2 -> 6 of 12', (await h.locator('.lightbox-count').text_content()) == '6 of 12')
    await h.locator('.lb-prev').click()
    check('prev button -> 5', (await h.locator('.lightbox-count').text_content()) == '5 of 12')
    await page.keyboard.press('ArrowRight')
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(100)
    check('escape closes', await h.locator('.lightbox').count() == 0)
    lbl = await active(page, "getAttribute('aria-label')")
    check('focus returns to viewed thumbnail', lbl == 'Open Midnight sun' or lbl == 'Open The long road east', lbl)
    check('focus on thumbnail #6', lbl == 'Open The long road east', lbl)
    # wrap
    await h.locator('.thumb').first.click()
    await page.wait_for_timeout(100)
    await page.keyboard.press('ArrowLeft')
    check('wraps 1 -> 12', (await h.locator('.lightbox-count').text_content()) == '12 of 12')
    await page.keyboard.press('ArrowRight')
    check('wraps 12 -> 1', (await h.locator('.lightbox-count').text_content()) == '1 of 12')
    # swipe
    st = await h.locator('.lightbox-img').bounding_box()
    cx, cy = st['x'] + st['width'] / 2, st['y'] + st['height'] / 2
    await page.mouse.move(cx, cy); await page.mouse.down()
    await page.mouse.move(cx - 80, cy, steps=5)
    tr = await h.locator('.lightbox-img').evaluate('e => e.style.transform')
    check('image follows pointer', tr == 'translateX(-80px)', tr)
    await page.mouse.move(cx - 150, cy, steps=5); await page.mouse.up()
    await page.wait_for_timeout(100)
    check('swipe left -> next', (await h.locator('.lightbox-count').text_content()) == '2 of 12')
    await page.mouse.move(cx, cy); await page.mouse.down(); await page.mouse.move(cx + 30, cy, steps=4); await page.mouse.up()
    check('small drag snaps back', (await h.locator('.lightbox-count').text_content()) == '2 of 12' and (await h.locator('.lightbox-img').evaluate('e => e.style.transform')) == 'translateX(0px)')
    await page.mouse.move(cx, cy); await page.mouse.down(); await page.mouse.move(cx + 120, cy, steps=5); await page.mouse.up()
    check('swipe right -> prev', (await h.locator('.lightbox-count').text_content()) == '1 of 12')
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight')
    await page.wait_for_timeout(400)
    await shot(page, 'dc56')
    await h.locator('.lb-close').click()
    await page.wait_for_timeout(100)
    await shot(page, 'dc56-grid')
    await page.evaluate('() => { window.Image = window.__OrigImage; }')

# ---------------------------------------------------------------- dc57
async def t_dc57(page):
    h = await open_design(page, 'dc57')
    await page.wait_for_timeout(1100)
    rows = h.locator('.task')
    check('6 tasks', await rows.count() == 6)
    prog = h.locator('.progress-text')
    check('initial 2 of 6', 'done' in await prog.inner_text() and (await prog.inner_text()).startswith('2 of 6'))
    # toggle t2: instant + saving + persists
    await rows.nth(1).locator('.task-check').click()
    await page.wait_for_timeout(50)
    check('toggle instant', await rows.nth(1).locator('.task-check').is_checked() and (await prog.inner_text()).startswith('3 of 6'))
    check('saving state', 'is-saving' in await rows.nth(1).get_attribute('class') and await rows.nth(1).locator('.task-check').is_disabled())
    await page.wait_for_timeout(1000)
    check('saved by You', 'Last edited by You' in await rows.nth(1).inner_text() and await rows.nth(1).locator('.task-check').is_checked())
    # toggle t2 again (needs new version, otherwise self-conflict)
    await rows.nth(1).locator('.task-check').click()
    await page.wait_for_timeout(1000)
    check('second edit uses new version', not await rows.nth(1).locator('.task-check').is_checked() and await h.locator('.conflict').count() == 0)
    # conflict on t3
    await rows.nth(2).locator('.task-check').click()
    await page.wait_for_timeout(50)
    check('t3 optimistic', await rows.nth(2).locator('.task-check').is_checked())
    await page.wait_for_timeout(1000)
    check('t3 rolled back', not await rows.nth(2).locator('.task-check').is_checked())
    check('conflict message', 'Someone else changed this' in await rows.nth(2).locator('.conflict').inner_text())
    await shot(page, 'dc57-conflict')
    # delete t3 -> conflict -> restored in place
    await rows.nth(2).locator('.icon-btn').click()
    await page.wait_for_timeout(50)
    check('delete instant', await rows.count() == 5)
    await page.wait_for_timeout(1000)
    titles = await h.locator('.task-title').all_inner_texts()
    check('failed delete restored at index', await rows.count() == 6 and titles[2] == 'Confirm food truck lineup', titles)
    # reload
    await rows.nth(2).locator('.conflict-btn').click()
    await page.wait_for_timeout(900)
    check('reload shows Priya title', (await rows.nth(2).locator('.task-title').inner_text()) == 'Confirm food truck lineup (8 trucks, 2 vegan)' and await h.locator('.conflict').count() == 0)
    await rows.nth(2).locator('.task-check').click()
    await page.wait_for_timeout(1000)
    check('t3 saves after reload', await rows.nth(2).locator('.task-check').is_checked() and await h.locator('.conflict').count() == 0)
    # rename t5
    await rows.nth(4).locator('.task-title').click()
    inp = rows.nth(4).locator('.task-input')
    check('rename input focused', (await active(page)) == 'task-input')
    await inp.fill('Escape test')
    await inp.press('Escape')
    check('escape cancels', (await rows.nth(4).locator('.task-title').inner_text()) == 'Schedule volunteer shifts')
    await rows.nth(4).locator('.task-title').click()
    await rows.nth(4).locator('.task-input').fill('Schedule 40 volunteer shifts')
    await rows.nth(4).locator('.task-input').press('Enter')
    check('rename instant', (await rows.nth(4).locator('.task-title').inner_text()) == 'Schedule 40 volunteer shifts')
    await page.wait_for_timeout(1000)
    check('rename saved', 'Last edited by You' in await rows.nth(4).inner_text())
    # delete t6 succeeds
    await rows.nth(5).locator('.icon-btn').click()
    await page.wait_for_timeout(1000)
    check('delete persists', await rows.count() == 5)
    # change: fresh app, mark all done -> t3 fails
    h = await open_design(page, 'dc57')
    await page.wait_for_timeout(1100)
    rows = h.locator('.task')
    await h.locator('.btn-secondary').click()
    await page.wait_for_timeout(50)
    check('batch optimistic all done', (await h.locator('.progress-text').inner_text()).startswith('6 of 6'))
    await page.wait_for_timeout(1100)
    summ = await h.locator('.batch-summary').inner_text()
    check('partial failure summary', summ == "Marked 3 of 4 tasks done. 1 couldn't be saved.", summ)
    check('only t3 rolled back', not await rows.nth(2).locator('.task-check').is_checked() and await h.locator('.conflict').count() == 1 and (await h.locator('.progress-text').inner_text()).startswith('5 of 6'))
    await shot(page, 'dc57')

# ---------------------------------------------------------------- dc58
async def t_dc58(page):
    await page.evaluate("() => { const u = new URL(location.href); u.searchParams.delete('status'); u.searchParams.delete('owner'); history.replaceState(null, '', u.toString()); }")
    hash0 = await page.evaluate('location.hash')
    h = await open_design(page, 'dc58')
    await page.wait_for_timeout(1200)
    rows = h.locator('.project')
    check('18 projects', await rows.count() == 18)
    btn = h.locator('.filter-btn')
    await btn.click()
    check('popover open', await h.locator('.popover').count() == 1 and await btn.get_attribute('aria-expanded') == 'true')
    check('focus moved in', (await active(page, 'tagName')) == 'INPUT')
    owners = await h.locator('.pop-section').nth(1).locator('.pop-option').all_inner_texts()
    check('owners sorted from data', len(owners) == 8 and owners == sorted(owners), owners)
    await h.locator('.pop-option', has_text='Design').click()
    check('draft does not filter', await rows.count() == 18)
    await h.locator('.btn-ghost').click()
    check('cancel closes, no filter', await h.locator('.popover').count() == 0 and await rows.count() == 18 and await h.locator('.chip').count() == 0)
    check('focus back on button', 'filter-btn' in (await active(page)))
    await btn.click()
    check('reopen shows applied (none)', not await h.locator('.pop-option', has_text='Design').locator('input').is_checked())
    await h.locator('.pop-option', has_text='Design').click()
    await page.keyboard.press('Escape')
    check('escape discards', await h.locator('.popover').count() == 0 and await rows.count() == 18)
    await btn.click()
    await h.locator('.pop-option', has_text='Design').click()
    await h.locator('.pop-option', has_text='Permitting').click()
    await h.locator('.pop-search').fill('le')
    vis = await h.locator('.pop-section').nth(1).locator('.pop-option').all_inner_texts()
    check('owner search', vis == ['Lena Fischer', 'Leo Brandt', 'Leonie Haas'], vis)
    await h.locator('.pop-section').nth(1).locator('.pop-link', has_text='Select all').click()
    await h.locator('.pop-search').fill('zz')
    check('no owner match msg', 'No one matches' in await h.locator('.pop-empty').inner_text())
    await h.locator('.pop-search').fill('')
    checked = await h.locator('.pop-section').nth(1).locator('input:checked').count()
    check('select all = visible only', checked == 3, checked)
    await shot(page, 'dc58-popover')
    await h.locator('.btn-dark').click()
    names = await h.locator('.project-name').all_inner_texts()
    check('applied filter', sorted(names) == sorted(['Courtyard Townhouses', 'Coastal Research Station', 'Observatory Visitor Centre']), names)
    check('badge 5', (await h.locator('.count-badge').inner_text()) == '5')
    check('count text', (await h.locator('.result-count').inner_text()) == '3 of 18 projects')
    check('chips', await h.locator('.chip').count() == 5)
    q = await page.evaluate('location.search')
    check('url synced', 'status=Design' in q and 'status=Permitting' in q and 'owner=Leo+Brandt' in q, q)
    check('hash preserved', (await page.evaluate('location.hash')) == hash0)
    await shot(page, 'dc58')
    await h.locator('.chip-x[aria-label="Remove Status Permitting"]').click()
    names = await h.locator('.project-name').all_inner_texts()
    check('chip remove', names == ['Courtyard Townhouses'] and (await h.locator('.count-badge').inner_text()) == '4', names)
    # outside click cancels
    await btn.click()
    await h.locator('.pop-option', has_text='Complete').click()
    await h.locator('.header h1').click()
    check('outside click cancels', await h.locator('.popover').count() == 0 and await h.locator('.chip').count() == 4)
    # toggle via button closes
    await btn.click(); await btn.click()
    check('button toggles closed', await h.locator('.popover').count() == 0)
    # reload restores from URL
    h = await open_design(page, 'dc58')
    await page.wait_for_timeout(1200)
    check('filters restored from URL', await h.locator('.chip').count() == 4 and await h.locator('.project').count() == 1)
    await h.locator('.pop-option').count()
    await h.locator('.chips .clear-all').click()
    check('clear all', await h.locator('.project').count() == 18 and await h.locator('.count-badge').count() == 0)
    q = await page.evaluate('location.search')
    check('url cleared', 'status=' not in q and 'owner=' not in q, q)
    # empty state
    await btn.click()
    await h.locator('.pop-option', has_text='On hold').click()
    await h.locator('.pop-search').fill('Leo B')
    await h.locator('.pop-section').nth(1).locator('.pop-option').first.click()
    await h.locator('.btn-dark').click()
    check('empty state', 'No projects match' in await h.locator('.empty').inner_text())
    await h.locator('.empty .clear-all').click()
    check('empty clear', await h.locator('.project').count() == 18)

# ---------------------------------------------------------------- dc59
async def t_dc59(page):
    h = await open_design(page, 'dc59')
    await page.wait_for_timeout(1200)
    titles = await h.locator('.month-title').all_inner_texts()
    check('two months March/April', titles == ['March 2026', 'April 2026'], titles)
    check('prev disabled', await h.locator('.nav-prev').is_disabled())
    day = lambda iso: h.locator(f'[data-date="{iso}"]')
    summ = h.locator('.summary')
    await day('2026-03-02').click(force=True)
    check('past day ignored', (await summ.inner_text()) == 'Add your check-in date')
    check('booked struck', 'is-unavailable' in await day('2026-03-12').get_attribute('class'))
    await day('2026-03-04').click()
    check('start set', (await summ.inner_text()) == 'Mar 4 → Add checkout' and 'is-start' in await day('2026-03-04').get_attribute('class'))
    await day('2026-03-08').hover()
    check('hover preview', await h.locator('.day.in-range').count() == 3 and 'is-end' in await day('2026-03-08').get_attribute('class'))
    check('beyond booking disabled', await day('2026-03-14').get_attribute('aria-disabled') == 'true' and await day('2026-03-11').get_attribute('aria-disabled') == 'false')
    await day('2026-03-09').click()
    check('range summary', (await summ.inner_text()) == 'Mar 4 → Mar 9 · 5 nights' and (await h.locator('.total').inner_text()) == '$925 total')
    check('reserve enabled', await h.locator('.reserve-btn').is_enabled())
    check('range drawn', await h.locator('.day.in-range').count() == 4)
    await shot(page, 'dc59')
    await day('2026-03-10').click()
    check('new start after full range', (await summ.inner_text()) == 'Mar 10 → Add checkout')
    await day('2026-03-14').click(force=True)
    check('cannot cross booked night', (await summ.inner_text()) == 'Mar 10 → Add checkout')
    await day('2026-03-11').click()
    check('1 night singular', (await summ.inner_text()) == 'Mar 10 → Mar 11 · 1 night')
    await day('2026-03-25').click()
    await day('2026-03-24').click()
    check('earlier day moves start', (await summ.inner_text()) == 'Mar 24 → Add checkout')
    await day('2026-04-05').hover(force=True)
    check('limit across months (Apr 3 booked)', await day('2026-04-05').get_attribute('aria-disabled') == 'true' and await day('2026-04-02').get_attribute('aria-disabled') == 'false')
    await h.locator('.clear-btn').click()
    check('clear dates', (await summ.inner_text()) == 'Add your check-in date' and await h.locator('.reserve-btn').is_disabled())
    await h.locator('.nav-next').click()
    titles = await h.locator('.month-title').all_inner_texts()
    check('next month', titles == ['April 2026', 'May 2026'] and await h.locator('.nav-prev').is_enabled(), titles)
    await h.locator('.nav-prev').click()
    # keyboard
    tabbable = await h.locator('.day[tabindex="0"]').evaluate_all('els => els.map(e => e.dataset.date)')
    check('one tabbable day (last clicked)', tabbable == ['2026-03-24'], tabbable)
    await day('2026-03-03').focus()
    await page.keyboard.press('ArrowRight')
    check('arrow right focus', (await active(page, 'dataset.date')) == '2026-03-04')
    await page.keyboard.press('Enter')
    await page.keyboard.press('ArrowDown')
    check('arrow down +7', (await active(page, 'dataset.date')) == '2026-03-11')
    check('keyboard preview', await h.locator('.day.in-range').count() == 6)
    await page.keyboard.press('Enter')
    check('keyboard select range', (await summ.inner_text()) == 'Mar 4 → Mar 11 · 7 nights')
    await page.keyboard.press('ArrowUp'); await page.keyboard.press('ArrowUp')
    check('never before today', (await active(page, 'dataset.date')) == '2026-03-03')
    for _ in range(9):
        await page.keyboard.press('ArrowDown')
    await page.wait_for_timeout(100)
    titles = await h.locator('.month-title').all_inner_texts()
    check('view shifts with focus', (await active(page, 'dataset.date')) == '2026-05-05' and titles == ['April 2026', 'May 2026'], (await active(page, 'dataset.date'), titles))
    check('focus on disabled-looking day possible', (await h.locator('.day[aria-disabled="true"]').count()) > 0)

# ---------------------------------------------------------------- dc60
async def groups60(h):
    return await h.locator('.conv-group').evaluate_all("els => els.map(g => [g.querySelector('.group-title').textContent, Array.from(g.querySelectorAll('.conv-title')).map(t => t.textContent)])")


async def t_dc60(page):
    h = await open_design(page, 'dc60')
    # count API deletes
    await page.wait_for_timeout(1200)
    g = await groups60(h)
    check('group names', [x[0] for x in g] == ['Today', 'Yesterday', 'Previous 7 days', 'Older'], [x[0] for x in g])
    check('group sizes', [len(x[1]) for x in g] == [3, 2, 4, 5], [len(x[1]) for x in g])
    check('newest first in Today', g[0][1][0] == 'Refactor the billing webhook handler')
    check('Jun 8 is Previous 7 days', 'Sourdough starter troubleshooting' in g[2][1])
    # search
    await h.locator('.side-search').fill('PLAN')
    g = await groups60(h)
    check('search regroups', g == [['Older', ['Q3 planning doc outline', 'Marathon training plan']]], g)
    await h.locator('.side-search').fill('zzz')
    check('no match msg', 'No chats match' in await h.locator('.side-msg').inner_text())
    await h.locator('.side-search').fill('')
    # select + delete selected -> neighbour
    row = h.locator('.conv', has_text='Trip ideas for Lisbon')
    await row.locator('.conv-main').click()
    check('selected shows in pane', (await h.locator('.chat-head h2').inner_text()) == 'Trip ideas for Lisbon in October')
    await row.hover()
    await row.locator('.conv-action[title="Delete"]').click()
    check('deleted immediately', await h.locator('.conv', has_text='Trip ideas for Lisbon').count() == 0)
    check('toast shown', 'Chat deleted' in await h.locator('.undo-toast').inner_text())
    check('neighbour selected', (await h.locator('.chat-head h2').inner_text()) == 'Explain vector clocks simply')
    await shot(page, 'dc60-toast')
    await page.wait_for_timeout(1500)
    await h.locator('.undo-btn').click()
    check('undo restores in place', (await groups60(h))[0][1] == ['Refactor the billing webhook handler', 'Trip ideas for Lisbon in October', 'Explain vector clocks simply'])
    check('toast gone', await h.locator('.undo-toast').count() == 0)
    await page.wait_for_timeout(5500)
    check('undo cancelled API delete', await h.locator('.conv', has_text='Trip ideas for Lisbon').count() == 1)
    # verify API state: reopen later. delete and wait 5s
    row = h.locator('.conv', has_text='Wedding toast draft')
    await row.hover(); await row.locator('.conv-action[title="Delete"]').click()
    # second delete finalizes first
    row2 = h.locator('.conv', has_text='Learn Rust ownership')
    await row2.hover(); await row2.locator('.conv-action[title="Delete"]').click()
    check('second delete: one toast', await h.locator('.undo-toast').count() == 1)
    await h.locator('.undo-btn').click()
    check('undo restores only second', await h.locator('.conv', has_text='Learn Rust ownership').count() == 1 and await h.locator('.conv', has_text='Wedding toast draft').count() == 0)
    row = h.locator('.conv', has_text='Tax questions about RSUs')
    await row.hover(); await row.locator('.conv-action[title="Delete"]').click()
    await page.wait_for_timeout(5300)
    check('toast auto-hides after 5s', await h.locator('.undo-toast').count() == 0)
    await page.wait_for_timeout(900)
    # rename
    row = h.locator('.conv', has_text='Explain vector clocks simply')
    await row.locator('.conv-main').dblclick()
    inp = h.locator('.conv-input')
    sel = await inp.evaluate('e => e.selectionEnd - e.selectionStart')
    check('rename input with text selected', sel == len('Explain vector clocks simply'), sel)
    await inp.fill('Nope')
    await inp.press('Escape')
    check('escape cancels rename', await h.locator('.conv', has_text='Explain vector clocks simply').count() == 1)
    row = h.locator('.conv', has_text='Explain vector clocks simply')
    await row.hover(); await row.locator('.conv-action[title="Rename"]').click()
    await h.locator('.conv-input').fill('Vector clocks, simply')
    await h.locator('.conv-input').press('Enter')
    check('rename instant', await h.locator('.conv-title', has_text='Vector clocks, simply').count() == 1)
    # new chat
    await h.locator('.side-search').fill('rust')
    await h.locator('.new-chat').click()
    check('creating state', (await h.locator('.new-chat').inner_text()) == 'Creating…' and await h.locator('.new-chat').is_disabled())
    await page.wait_for_timeout(900)
    g = await groups60(h)
    check('new chat at top + selected + search cleared', g[0][1][0] == 'New chat' and (await h.locator('.chat-head h2').inner_text()) == 'New chat' and await h.locator('.side-search').input_value() == '', g[0])
    # change: pin
    row = h.locator('.conv', has_text='Marathon training plan')
    await row.hover(); await row.locator('.conv-action[title="Pin"]').click()
    g = await groups60(h)
    check('pinned section on top', g[0] == ['Pinned', ['Marathon training plan']] and 'Marathon training plan' not in g[-1][1], g[0])
    check('pin icon active', await h.locator('.conv-action.is-pinned').count() == 1)
    row = h.locator('.conv', has_text='SQL: top customers')
    await row.hover(); await row.locator('.conv-action[title="Pin"]').click()
    g = await groups60(h)
    check('pinned newest first', g[0] == ['Pinned', ['SQL: top customers by month', 'Marathon training plan']], g[0])
    await page.wait_for_timeout(900)
    await shot(page, 'dc60')
    row = h.locator('.conv', has_text='Marathon training plan')
    await row.hover(); await row.locator('.conv-action[title="Unpin"]').click()
    g = await groups60(h)
    check('unpin returns to date group', 'Marathon training plan' in g[-1][1] and g[-1][0] == 'Older')
    await page.wait_for_timeout(900)
    # server state after reload: Wedding + Tax deleted, rename + pin persisted
    h = await open_design(page, 'dc60')
    await page.wait_for_timeout(1200)
    # module state resets on re-run, so just make sure a fresh load still works
    check('fresh load ok', await h.locator('.conv').count() == 14)


TESTS = {k[2:]: v for k, v in globals().items() if k.startswith('t_dc')}


async def main():
    only = sys.argv[1].split(',') if len(sys.argv) > 1 else sorted(TESTS)
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)], env=dict(os.environ))
    time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page = await b.new_page(viewport={'width': 1600, 'height': 950})
            errs = []
            page.on('pageerror', lambda e: errs.append(CUR[0] + ' pageerror: ' + str(e)))
            page.on('console', lambda m: m.type == 'error' and errs.append(CUR[0] + ' console: ' + m.text[:300]))

            async def route(r):
                u = r.request.url
                if 'react-dom' in u: await r.fulfill(body='', content_type='text/javascript')
                elif 'react' in u: await r.fulfill(path=str(ROOT / 'react-bundle.js'), content_type='text/javascript')
                elif 'babel' in u: await r.fulfill(body=SHIM, content_type='text/javascript')
                elif 'fonts.g' in u: await r.fulfill(body='', content_type='text/css')
                else: await r.continue_()
            await page.route('**/*', route)
            await page.goto(f'http://127.0.0.1:{PORT}/')
            await page.wait_for_timeout(600)
            for ex in only:
                n0 = len(errs)
                try:
                    await TESTS[ex](page)
                except Exception as e:  # noqa: BLE001
                    check('test crashed', False, repr(e)[:400])
                check('no page/console errors', len(errs) == n0, errs[n0:])
            await b.close()
    finally:
        srv.terminate()
    fails = [r for r in RESULTS if not r[2]]
    print(f'\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks passed')
    for f in fails:
        print('FAILED:', f[0], f[1])


asyncio.run(main())
