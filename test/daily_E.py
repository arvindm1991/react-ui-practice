import asyncio, subprocess, sys, time, pathlib, os, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
PORT = int(os.environ.get('PORT', '8785'))
DIST = os.environ.get('DIST_HTML', '/tmp/claude-0/-home-claude/653a60f8-7891-5769-b62a-4ce1d270b59d/scratchpad/dist-E.html')
SHIM = open(ROOT / 'run.py').read().split('SHIM = """')[1].split('"""')[0]

RESULTS = []


def check(ex, name, cond, detail=''):
    RESULTS.append((ex, name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + ex + ' · ' + name + ('' if cond else '  -> ' + str(detail)))


async def open_design(page, ex):
    await page.evaluate(f'Workspace.open("{ex}")')
    await page.wait_for_timeout(1000)
    await page.click('[data-ptab="design"]')
    await page.wait_for_timeout(1500)
    if (await page.inner_text('#wideBtn')).strip() == 'Expand':
        await page.click('#wideBtn')
        await page.wait_for_timeout(300)
    await page.click('[data-dmode="interact"]')
    await page.wait_for_timeout(100)
    return page.locator('#designHost')


async def active(h):
    return await h.evaluate("h => { const a = h.shadowRoot.activeElement; return a ? (a.getAttribute('aria-label') || a.className || a.tagName) : null; }")


async def shot(page, ex):
    await page.screenshot(path=str(ROOT / 'shots' / f'{ex}.png'))


async def close(page):
    await page.click('[data-ptab="task"]')
    await page.evaluate('Workspace.close()')


# ---------------------------------------------------------------- dc41
async def t41(page):
    ex = 'dc41'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1100)
    notes = h.locator('.note')
    undo = h.locator('button[aria-label^="Undo"]')
    redo = h.locator('button[aria-label^="Redo"]')
    check(ex, 'loads 5 notes', await notes.count() == 5, await notes.count())
    check(ex, 'undo/redo disabled initially', await undo.is_disabled() and await redo.is_disabled())
    await h.locator('button[aria-label="Add note"]').click()
    check(ex, 'add note', await notes.count() == 6)
    await undo.click()
    check(ex, 'undo removes added note', await notes.count() == 5)
    check(ex, 'redo enabled after undo', not await redo.is_disabled())
    await redo.click()
    check(ex, 'redo re-adds', await notes.count() == 6)
    first_text = await notes.nth(0).locator('textarea').input_value()
    await notes.nth(0).locator('.note-delete').click()
    check(ex, 'delete', await notes.count() == 5)
    await h.locator('.canvas').click(position={'x': 5, 'y': 5})
    await page.keyboard.press('Control+z')
    await page.wait_for_timeout(100)
    check(ex, 'Ctrl+Z restores deleted note in place', await notes.count() == 6 and await notes.nth(0).locator('textarea').input_value() == first_text)
    await page.keyboard.press('Control+Shift+z')
    await page.wait_for_timeout(100)
    check(ex, 'Ctrl+Shift+Z redoes delete', await notes.count() == 5)
    await page.keyboard.press('Control+z')
    ta = notes.nth(1).locator('textarea')
    orig = await ta.input_value()
    await ta.click()
    await page.keyboard.press('End')
    await page.keyboard.type(' (edited)')
    await h.locator('.canvas').click(position={'x': 5, 'y': 5})
    check(ex, 'edit text', await ta.input_value() == orig + ' (edited)')
    await undo.click()
    check(ex, 'one undo reverts the whole edit', await ta.input_value() == orig, await ta.input_value())
    await redo.click()
    check(ex, 'redo re-applies edit', await ta.input_value() == orig + ' (edited)')
    await undo.click()
    # a new action clears redo
    await h.locator('button[aria-label="Add note"]').click()
    check(ex, 'new action clears redo', await redo.is_disabled())
    # cap at 20
    for _ in range(25):
        await h.locator('button[aria-label="Add note"]').click()
    meter = await h.locator('.history-meter').inner_text()
    check(ex, 'history meter shows 20 / 20', meter.strip() == '20 / 20', meter)
    total = await notes.count()
    n = 0
    while not await undo.is_disabled() and n < 40:
        await undo.click()
        n += 1
    check(ex, 'history capped at 20 undo steps', n == 20, n)
    check(ex, 'notes after 20 undos', await notes.count() == total - 20, await notes.count())
    await shot(page, ex)
    await close(page)


# ---------------------------------------------------------------- dc42
async def t42(page):
    ex = 'dc42'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1300)
    cards = h.locator('.photo-card')
    c0 = await cards.count()
    check(ex, 'first page loaded', c0 >= 8 and c0 % 8 == 0, c0)
    scroller = h.locator('.feed-scroll')
    bottom = await scroller.evaluate('e => e.scrollHeight')
    await scroller.evaluate(f'e => {{ e.scrollTop = {bottom}; }}')
    await page.wait_for_timeout(100)
    check(ex, 'loading row while next page loads', await h.locator('.spinner-row').count() == 1)
    # hammer the sentinel in and out of view while the request is in flight (fixed positions)
    for _ in range(4):
        await scroller.evaluate(f'e => {{ e.scrollTop = {bottom} - 1500; }}')
        await page.wait_for_timeout(25)
        await scroller.evaluate(f'e => {{ e.scrollTop = {bottom}; }}')
        await page.wait_for_timeout(25)
    await page.wait_for_timeout(1300)
    check(ex, 'exactly one more page (no duplicate load)', await cards.count() == c0 + 8, await cards.count())
    for _ in range(12):
        if await h.locator('.feed-end').count():
            break
        await scroller.evaluate('e => { e.scrollTop = e.scrollHeight; }')
        await page.wait_for_timeout(1300)
    labels = await cards.evaluate_all('els => els.map(e => e.getAttribute("aria-label"))')
    check(ex, 'all 40 photos loaded', len(labels) == 40, len(labels))
    check(ex, 'no duplicates', len(set(labels)) == len(labels))
    end = h.locator('.feed-end')
    check(ex, 'end message', await end.count() == 1 and '40 photos' in await end.inner_text())
    await scroller.evaluate('e => { e.scrollTop = e.scrollHeight; }')
    await page.wait_for_timeout(1300)
    check(ex, 'stops at the end', await cards.count() == 40 and await h.locator('.spinner-row').count() == 0)
    btn = h.locator('.back-to-top')
    check(ex, 'back to top visible after scrolling', await btn.count() == 1)
    await shot(page, ex)
    await btn.click()
    await page.wait_for_timeout(1500)
    st = await scroller.evaluate('e => e.scrollTop')
    check(ex, 'back to top scrolls to 0', st == 0, st)
    check(ex, 'back to top hidden at top', await btn.count() == 0)
    await close(page)


# ---------------------------------------------------------------- dc43
async def t43(page):
    ex = 'dc43'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1200)
    titles = h.locator('.track-title')

    async def order():
        return await titles.all_inner_texts()
    o = await order()
    check(ex, 'loads 8 tracks', len(o) == 8, o)
    save = h.locator('.save-btn')
    check(ex, 'clean: save disabled + saved state', await save.is_disabled() and 'saved' in (await h.locator('.save-state').inner_text()).lower())
    check(ex, 'total duration in header', '30 min' in await h.locator('.pl-meta').inner_text())
    check(ex, 'first Move up disabled', await h.locator('button[aria-label="Move Paper Lanterns up"]').is_disabled())
    await h.locator('button[aria-label="Move Paper Lanterns down"]').click()
    o = await order()
    check(ex, 'move down', o[:2] == ['Slow Orbit', 'Paper Lanterns'], o)
    starts = await h.locator('.track-start').all_inner_texts()
    check(ex, 'start times recalculated', starts[1] == 'starts 4:11', starts[:3])
    check(ex, 'unsaved changes shown', 'Unsaved changes' in await h.locator('.save-state').inner_text())
    check(ex, 'save enabled when dirty', not await save.is_disabled())
    await h.locator('button[aria-label="Move Paper Lanterns up"]').click()
    check(ex, 'moving back = clean again', await save.is_disabled())
    # drag and drop: Halftone onto top half of Slow Orbit
    src = h.locator('.track', has_text='Halftone')
    dst = h.locator('.track', has_text='Slow Orbit')
    await src.drag_to(dst, target_position={'x': 200, 'y': 6})
    await page.wait_for_timeout(200)
    o = await order()
    if o[1] != 'Halftone':
        # fallback: dispatch the DnD events with a shared DataTransfer
        await page.evaluate('''() => {
          const root = document.getElementById('designHost').shadowRoot;
          const rows = [...root.querySelectorAll('.track')];
          const s = rows.find(r => r.textContent.includes('Halftone'));
          const d = rows.find(r => r.textContent.includes('Slow Orbit'));
          const dt = new DataTransfer();
          const r = d.getBoundingClientRect();
          const opts = { bubbles: true, cancelable: true, composed: true, dataTransfer: dt, clientX: r.left + 100, clientY: r.top + 4 };
          s.dispatchEvent(new DragEvent('dragstart', opts));
          d.dispatchEvent(new DragEvent('dragover', opts));
          d.dispatchEvent(new DragEvent('drop', opts));
          s.dispatchEvent(new DragEvent('dragend', opts));
        }''')
        await page.wait_for_timeout(200)
        o = await order()
        print('   (used dispatched DnD events)')
    check(ex, 'drag and drop reorders (before target)', o[:3] == ['Paper Lanterns', 'Halftone', 'Slow Orbit'], o)
    # drag down: Paper Lanterns after Coastline
    await page.evaluate('''() => {
      const root = document.getElementById('designHost').shadowRoot;
      const rows = [...root.querySelectorAll('.track')];
      const s = rows.find(r => r.textContent.includes('Paper Lanterns'));
      const d = rows.find(r => r.textContent.includes('Coastline'));
      const dt = new DataTransfer();
      const r = d.getBoundingClientRect();
      const opts = { bubbles: true, cancelable: true, composed: true, dataTransfer: dt, clientX: r.left + 100, clientY: r.bottom - 4 };
      s.dispatchEvent(new DragEvent('dragstart', opts));
      d.dispatchEvent(new DragEvent('dragover', opts));
    }''')
    await page.wait_for_timeout(100)
    check(ex, 'drop indicator shown', await h.locator('.track.drop-after').count() == 1)
    await page.evaluate('''() => {
      const root = document.getElementById('designHost').shadowRoot;
      const rows = [...root.querySelectorAll('.track')];
      const s = rows.find(r => r.textContent.includes('Paper Lanterns'));
      const d = rows.find(r => r.textContent.includes('Coastline'));
      const r = d.getBoundingClientRect();
      const opts = { bubbles: true, cancelable: true, composed: true, dataTransfer: new DataTransfer(), clientX: r.left + 100, clientY: r.bottom - 4 };
      d.dispatchEvent(new DragEvent('drop', opts));
      s.dispatchEvent(new DragEvent('dragend', opts));
    }''')
    await page.wait_for_timeout(100)
    o = await order()
    check(ex, 'drag down lands after target', o.index('Paper Lanterns') == o.index('Coastline') + 1, o)
    check(ex, 'indicator cleared after drop', await h.locator('.track.drop-after, .track.drop-before').count() == 0)
    await shot(page, ex)
    await save.click()
    await page.wait_for_timeout(100)
    check(ex, 'saving pending state', (await save.inner_text()) == 'Saving…' and await save.is_disabled())
    await page.wait_for_timeout(1400)
    check(ex, 'saved', 'saved' in (await h.locator('.save-state').inner_text()).lower() and await save.is_disabled())
    saved = await order()
    await h.locator('button[aria-label="Move Velvet Static up"]').click()
    await h.locator('.ghost-btn').click()
    check(ex, 'discard restores saved order', await order() == saved)
    await close(page)


# ---------------------------------------------------------------- dc44
async def t44(page):
    ex = 'dc44'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1000)
    pal = h.locator('.palette')
    opts = h.locator('[role="option"]')
    await h.locator('.nav-item', has_text='Deployments').click()
    await page.keyboard.press('Control+k')
    await page.wait_for_timeout(100)
    check(ex, 'Ctrl+K opens palette', await pal.count() == 1)
    check(ex, 'input focused on open', await active(h) == 'palette-input', await active(h))
    check(ex, 'all 7 commands listed', await opts.count() == 7, await opts.count())
    check(ex, 'grouped under 3 section headers', [t.lower() for t in await h.locator('.palette-section').all_inner_texts()] == ['navigation', 'deployments', 'appearance'])
    await page.keyboard.type('rdp')
    await page.wait_for_timeout(50)
    texts = await opts.all_inner_texts()
    check(ex, 'fuzzy filter: rdp -> Redeploy production', texts == ['Redeploy production'], texts)
    check(ex, 'empty sections hidden', [t.lower() for t in await h.locator('.palette-section').all_inner_texts()] == ['deployments'])
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check(ex, 'Enter runs command + closes', await pal.count() == 0 and await h.locator('.deploy').count() == 5 and 'Queued' in await h.locator('.deploy').first.inner_text())
    check(ex, 'toast shown', 'Redeploy queued' in await h.locator('.toast').inner_text())
    a = await active(h)
    check(ex, 'focus returned to previous element', a and a.startswith('nav-item'), a)
    await h.locator('.search-trigger').click()
    await page.wait_for_timeout(100)
    check(ex, 'trigger button opens palette', await pal.count() == 1)
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('ArrowDown')
    ad = await h.locator('.palette-input').get_attribute('aria-activedescendant')
    check(ex, 'arrows move active + aria-activedescendant', ad == 'cmd-go-settings' and 'Go to Settings' in await h.locator('.palette-item.is-active').inner_text(), ad)
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check(ex, 'navigated to Settings', await h.locator('.topbar h1').inner_text() == 'Settings')
    check(ex, 'focus back on trigger', await active(h) == 'search-trigger', await active(h))
    await page.keyboard.press('Control+k')
    await page.keyboard.press('ArrowUp')
    check(ex, 'ArrowUp wraps to last', 'sidebar' in await h.locator('.palette-item.is-active').inner_text())
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(100)
    check(ex, 'Escape closes without running', await pal.count() == 0 and await h.locator('.sidebar.is-collapsed').count() == 0)
    await page.keyboard.press('Control+k')
    await page.keyboard.type('theme')
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check(ex, 'theme command changes app', await h.locator('.app.theme-light').count() == 1)
    await page.keyboard.press('Control+k')
    await page.keyboard.type('zzz')
    check(ex, 'no-match message', 'No commands match' in await h.locator('.palette-empty').inner_text())
    await page.keyboard.press('Control+k')
    await page.wait_for_timeout(100)
    check(ex, 'Ctrl+K again closes', await pal.count() == 0)
    await page.keyboard.press('Control+k')
    await page.keyboard.type('theme')
    await page.keyboard.press('Enter')
    await page.keyboard.press('Control+k')
    await page.keyboard.type('go')
    await page.wait_for_timeout(100)
    await shot(page, ex)
    await h.locator('.palette-backdrop').click(position={'x': 5, 'y': 5})
    check(ex, 'backdrop click closes', await pal.count() == 0)
    await close(page)


# ---------------------------------------------------------------- dc45
async def t45(page):
    ex = 'dc45'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1200)
    rows = h.locator('tbody tr')
    check(ex, 'loads 5 rows', await rows.count() == 5)

    async def row_total(name):
        return await h.locator('tbody tr', has_text=name).locator('.cell-total').inner_text()

    async def foot():
        return await h.locator('tfoot td.cell').all_inner_texts()
    check(ex, 'row total derived', await row_total('Rent') == '$12,600', await row_total('Rent'))
    f = await foot()
    check(ex, 'column totals + grand total', f == ['$27,740', '$28,510', '$28,860', '$85,110'], f)
    await h.locator('button[aria-label^="Rent Jul"]').click()
    inp = h.locator('.cell-input')
    check(ex, 'click opens editor focused', await inp.count() == 1 and await active(h) == 'Rent Jul')
    await inp.fill('5000')
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(50)
    check(ex, 'Enter commits', await h.locator('button[aria-label^="Rent Jul"]').inner_text() == '$5,000')
    check(ex, 'Enter moves down', await inp.get_attribute('aria-label') == 'Payroll Jul', await inp.get_attribute('aria-label') if await inp.count() else 'no editor')
    check(ex, 'totals update', await row_total('Rent') == '$13,400' and (await foot())[0] == '$28,540', await foot())
    await page.keyboard.press('Escape')
    check(ex, 'Escape cancels editing', await inp.count() == 0)
    await h.locator('button[aria-label^="Software Sep"]').click()
    await inp.fill('abc')
    await page.keyboard.press('Tab')
    await page.wait_for_timeout(50)
    check(ex, 'Tab wraps to next row', await inp.count() == 1 and await inp.get_attribute('aria-label') == 'Advertising Jul')
    inv = h.locator('td.is-invalid')
    check(ex, 'invalid input highlighted', await inv.count() == 1 and await inv.inner_text() == 'abc')
    check(ex, 'invalid excluded from totals', await row_total('Software') == '$2,550', await row_total('Software'))
    check(ex, 'invalid warning', '1 cell needs a number' in await h.locator('.sheet-warning').inner_text())
    await page.keyboard.press('Shift+Tab')
    await page.wait_for_timeout(50)
    check(ex, 'Shift+Tab moves back with value', await inp.get_attribute('aria-label') == 'Software Sep' and await inp.input_value() == 'abc')
    await inp.fill('1,000')
    await page.keyboard.press('Tab')
    await page.keyboard.press('Escape')
    check(ex, 'fixing invalid clears highlight', await inv.count() == 0 and await row_total('Software') == '$3,550')
    await h.locator('button[aria-label^="Travel Aug"]').click()
    await inp.fill('100')
    await h.locator('.app-header').click()
    await page.wait_for_timeout(50)
    check(ex, 'blur commits', await inp.count() == 0 and await h.locator('button[aria-label^="Travel Aug"]').inner_text() == '$100')
    await h.locator('.add-input').fill('Insurance')
    await h.locator('.add-btn').click()
    check(ex, 'add row', await rows.count() == 6 and await row_total('Insurance') == '$0')
    await h.locator('button[aria-label^="Insurance Aug"]').click()
    await inp.fill('250')
    await page.keyboard.press('Enter')
    check(ex, 'new row editable + Enter on last row closes', await inp.count() == 0 and await row_total('Insurance') == '$250')
    before = await foot()
    await h.locator('button[aria-label="Delete Advertising"]').click()
    after = await foot()
    check(ex, 'delete row updates totals', await rows.count() == 5 and after[3] != before[3], (before, after))
    vals = await h.locator('tbody .cell-total').all_inner_texts()
    tot = sum(int(v.replace('$', '').replace(',', '')) for v in vals)
    check(ex, 'grand total equals sum of row totals', after[3] == '${:,}'.format(tot), (after, tot))
    await h.locator('button[aria-label^="Payroll Aug"]').click()
    await inp.fill('lots')
    await page.keyboard.press('Enter')
    await page.keyboard.press('Escape')
    await shot(page, ex)
    await close(page)


# ---------------------------------------------------------------- dc46
async def t46(page):
    ex = 'dc46'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1200)
    seats = h.locator('.seat')

    def seat(id_):
        return h.locator(f'.seat[aria-label^="Row {id_[0]}, seat {id_[1:]},"]')
    check(ex, '60 seats, 12 taken', await seats.count() == 60 and await h.locator('.seat.is-taken').count() == 12)
    await seat('A5').click()
    check(ex, 'select seat', 'is-selected' in await seat('A5').get_attribute('class') and await seat('A5').get_attribute('aria-pressed') == 'true')
    check(ex, 'summary lists seat + tier price', await h.locator('.picked-row').count() == 1 and '$95' in await h.locator('.summary-total').inner_text())
    for s_ in ['C4', 'C5', 'E5']:
        await seat(s_).click()
    check(ex, 'total by tier', '$265' in await h.locator('.summary-total').inner_text() and await h.locator('.book-btn').inner_text() == 'Book 4 seats · $265', await h.locator('.book-btn').inner_text())
    await seat('E6').click()
    check(ex, 'max 4 seats + notice', await h.locator('.seat.is-selected').count() == 4 and 'up to 4' in await h.locator('.banner').inner_text())
    await seat('A3').click(force=True)
    check(ex, 'taken seat not selectable', await h.locator('.seat.is-selected').count() == 4)
    await h.locator('button[aria-label="Remove seat E5"]').click()
    check(ex, 'remove from summary', await h.locator('.seat.is-selected').count() == 3 and '$225' in await h.locator('.summary-total').inner_text())
    await h.locator('.book-btn').click()
    await page.wait_for_timeout(100)
    check(ex, 'booking pending state', await h.locator('.book-btn').inner_text() == 'Booking…' and await h.locator('.book-btn').is_disabled())
    await page.wait_for_timeout(1500 + 1100)
    check(ex, 'C5 rejection shows error', await h.locator('.banner.is-error').count() == 1 and 'C5' in await h.locator('.banner.is-error').inner_text())
    check(ex, 'map refreshed: C5 now taken', 'is-taken' in await seat('C5').get_attribute('class'))
    check(ex, 'C5 dropped from selection', await h.locator('.picked-row').count() == 2 and '$160' in await h.locator('.summary-total').inner_text())
    await h.locator('.book-btn').click()
    await page.wait_for_timeout(1500 + 1100)
    check(ex, 'successful booking', await h.locator('.banner.is-success').count() == 1 and 'Booked' in await h.locator('.banner').inner_text())
    check(ex, 'booked seats now taken, selection cleared', 'is-taken' in await seat('A5').get_attribute('class') and await h.locator('.picked-row').count() == 0)
    # keyboard
    check(ex, 'roving tabindex: one seat in tab order', await h.locator('.seat[tabindex="0"]').count() == 1)
    await seat('B1').focus()
    await page.keyboard.press('ArrowRight')
    a = await active(h)
    check(ex, 'ArrowRight moves focus', a and a.startswith('Row B, seat 2,'), a)
    await page.keyboard.press('ArrowDown')
    a = await active(h)
    check(ex, 'ArrowDown moves across taken seat', a and a.startswith('Row C, seat 2,') and 'taken' in a, a)
    await page.keyboard.press('ArrowRight')
    await page.keyboard.press('Space')
    check(ex, 'Space selects focused seat', await seat('C3').get_attribute('aria-pressed') == 'true')
    await page.keyboard.press('Enter')
    check(ex, 'Enter toggles off', await seat('C3').get_attribute('aria-pressed') == 'false')
    await page.keyboard.press('ArrowLeft')
    await page.keyboard.press('Enter')
    check(ex, 'Enter on taken seat does nothing', await h.locator('.seat.is-selected').count() == 0)
    for _ in range(4):
        await page.keyboard.press('ArrowUp')
    a = await active(h)
    check(ex, 'stops at edge', a and a.startswith('Row A, seat 2,'), a)
    await seat('D8').click()
    await seat('D9').click()
    await shot(page, ex)
    await close(page)


# ---------------------------------------------------------------- dc47
async def t47(page):
    ex = 'dc47'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1100)
    comments = h.locator('.comment')
    check(ex, 'all 10 comments rendered recursively', await comments.count() == 10, await comments.count())
    check(ex, 'depth 4 nesting', await h.locator('[data-id="c1"] [data-id="c2"] [data-id="c3"] [data-id="c4"]').count() == 1)
    top = h.locator('.comments > .comment')
    ids = await top.evaluate_all('els => els.map(e => e.dataset.id)')
    check(ex, 'top sort by score', ids == ['c8', 'c1', 'c6'], ids)
    kids = await h.locator('[data-id="c1"] > div > .replies > .comment').evaluate_all('els => els.map(e => e.dataset.id)')
    check(ex, 'children sorted by top', kids == ['c2', 'c5'], kids)
    await h.locator('[data-id="c1"] > .comment-head .collapse-btn').click()
    check(ex, 'collapse hides subtree', await comments.count() == 6)
    check(ex, 'hidden replies count', (await h.locator('[data-id="c1"] .hidden-count').inner_text()) == '4 replies hidden')
    check(ex, '[+] and aria-expanded=false', await h.locator('[data-id="c1"] > .comment-head .collapse-btn').inner_text() == '[+]' and await h.locator('[data-id="c1"] > .comment-head .collapse-btn').get_attribute('aria-expanded') == 'false')
    await h.locator('[data-id="c1"] > .comment-head .collapse-btn').click()
    check(ex, 'expand restores', await comments.count() == 10)
    await h.locator('[data-id="c3"] > .comment-head .collapse-btn').click()
    check(ex, 'collapse nested only', await comments.count() == 9 and (await h.locator('[data-id="c3"] .hidden-count').inner_text()) == '1 reply hidden')
    await h.locator('[data-id="c3"] > .comment-head .collapse-btn').click()
    score = h.locator('[data-id="c4"] .score')
    await h.locator('button[aria-label="Upvote jun"]').click()
    check(ex, 'optimistic upvote', await score.inner_text() == '4')
    await page.wait_for_timeout(1000)
    check(ex, 'vote kept after success', await score.inner_text() == '4' and await h.locator('button[aria-label="Upvote jun"]').is_disabled())
    await h.locator('.offline-toggle input').check()
    lee = h.locator('[data-id="c9"] > div > .comment-actions .score')
    await h.locator('button[aria-label="Upvote lee"]').click()
    check(ex, 'optimistic while offline', await lee.inner_text() == '10')
    await page.wait_for_timeout(1100)
    check(ex, 'rollback on failure', await lee.inner_text() == '9' and not await h.locator('button[aria-label="Upvote lee"]').is_disabled())
    check(ex, 'error message on failure', await h.locator('.vote-error').count() == 1)
    await h.locator('.sort-select').select_option('new')
    ids = await top.evaluate_all('els => els.map(e => e.dataset.id)')
    check(ex, 'sort new (top level)', ids == ['c6', 'c1', 'c8'], ids)
    kids = await h.locator('[data-id="c1"] > div > .replies > .comment').evaluate_all('els => els.map(e => e.dataset.id)')
    check(ex, 'sort new applies to children', kids == ['c5', 'c2'], kids)
    await h.locator('.offline-toggle input').uncheck()
    await h.locator('.sort-select').select_option('top')
    await h.locator('[data-id="c6"] > .comment-head .collapse-btn').click()
    await shot(page, ex)
    await close(page)


# ---------------------------------------------------------------- dc48
async def t48(page):
    ex = 'dc48'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1000)
    cards = h.locator('.field-card')
    labels = h.locator('.label-input')
    check(ex, 'loads 2 fields', await cards.count() == 2)
    check(ex, 'preview renders fields', await h.locator('.pv-field').count() == 2)
    await h.locator('.type-btn', has_text='Dropdown').click()
    check(ex, 'add dropdown', await cards.count() == 3 and await h.locator('.pv-field select').count() == 1)
    await labels.nth(2).fill('Team size')
    check(ex, 'label edit updates preview', 'Team size' in await h.locator('.pv-field').nth(2).inner_text())
    await h.locator('.options-input').fill('Small\nMedium\nLarge')
    opts = await h.locator('.pv-field select option').all_inner_texts()
    check(ex, 'options edit updates preview', opts == ['Choose…', 'Small', 'Medium', 'Large'], opts)
    await cards.nth(2).locator('.toggle').click()
    check(ex, 'required toggle -> star in preview', await h.locator('.pv-field').nth(2).locator('.pv-star').count() == 1)
    await h.locator('.type-btn', has_text='Checkbox').click()
    check(ex, 'add checkbox', await cards.count() == 4 and await h.locator('.pv-check input[type=checkbox]').count() == 1)
    await h.locator('button[aria-label="Move Team size up"]').click()
    vals = [await labels.nth(i).input_value() for i in range(await labels.count())]
    check(ex, 'reorder', vals[:3] == ['Full name', 'Team size', 'Work email'], vals)
    check(ex, 'preview follows order', 'Team size' in await h.locator('.pv-field').nth(1).inner_text())
    check(ex, 'first Move up disabled', await h.locator('button[aria-label="Move Full name up"]').is_disabled())
    await h.locator('button[aria-label="Delete Untitled checkbox"]').click()
    check(ex, 'delete field', await cards.count() == 3 and await h.locator('.pv-check').count() == 0)
    await h.locator('.pv-submit').click()
    errs = await h.locator('.pv-error').all_inner_texts()
    check(ex, 'required validation', errs == ['This field is required'] * 3, errs)
    await h.locator('.pv-field').nth(0).locator('input').fill('Ada Lovelace')
    check(ex, 'error clears on input', await h.locator('.pv-error').count() == 2)
    await h.locator('.pv-field').nth(2).locator('input').fill('ada@nope')
    await h.locator('.pv-submit').click()
    errs = await h.locator('.pv-error').all_inner_texts()
    check(ex, 'email validation', 'Enter a valid email' in errs, errs)
    await h.locator('.pv-field').nth(2).locator('input').fill('ada@example.com')
    await h.locator('.pv-field select').select_option('Medium')
    await h.locator('.pv-submit').click()
    check(ex, 'valid submit', await h.locator('.form-success').count() == 1 and await h.locator('.pv-error').count() == 0)
    data = json.loads(await h.locator('.json').inner_text())
    f = data['fields']
    check(ex, 'JSON export reflects state', data['name'] == 'Beta waitlist' and [x['label'] for x in f] == ['Full name', 'Team size', 'Work email'] and f[1]['required'] is True and f[1]['options'] == ['Small', 'Medium', 'Large'] and f[1]['type'] == 'select', f)
    await cards.nth(2).locator('.toggle').click()
    data = json.loads(await h.locator('.json').inner_text())
    check(ex, 'JSON updates live', data['fields'][2]['required'] is False)
    await h.locator('.pv-submit').click()
    await shot(page, ex)
    await close(page)


# ---------------------------------------------------------------- dc49
async def t49(page):
    ex = 'dc49'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1200)
    inp = h.locator('#visited')
    lb = h.locator('[role="listbox"]')
    opts = h.locator('[role="option"]')
    chips = h.locator('.cb-chip')
    check(ex, 'combobox ARIA wiring', await inp.get_attribute('role') == 'combobox' and await inp.get_attribute('aria-controls') == await lb.get_attribute('id') and await inp.get_attribute('aria-expanded') == 'false')
    await inp.click()
    check(ex, 'opens on click', await inp.get_attribute('aria-expanded') == 'true' and await lb.is_visible() and await opts.count() == 40)
    await inp.type('an')
    names = await h.locator('.cb-name').all_inner_texts()
    check(ex, 'typing filters', len(names) > 0 and all('an' in n.lower() for n in names) and len(names) < 40, names)
    first_id = await opts.nth(0).get_attribute('id')
    check(ex, 'first option active', await inp.get_attribute('aria-activedescendant') == first_id)
    await page.keyboard.press('ArrowDown')
    check(ex, 'ArrowDown moves active', await inp.get_attribute('aria-activedescendant') == await opts.nth(1).get_attribute('id'))
    await page.keyboard.press('End')
    check(ex, 'End -> last', await inp.get_attribute('aria-activedescendant') == await opts.nth(len(names) - 1).get_attribute('id'))
    await page.keyboard.press('Home')
    check(ex, 'Home -> first', await inp.get_attribute('aria-activedescendant') == first_id)
    await page.keyboard.press('ArrowUp')
    check(ex, 'ArrowUp clamps at first', await inp.get_attribute('aria-activedescendant') == first_id)
    await page.keyboard.press('Enter')
    check(ex, 'Enter selects -> chip', await chips.count() == 1 and names[0] in await chips.first.inner_text())
    check(ex, 'query cleared, list stays open, focus on input', await inp.input_value() == '' and await inp.get_attribute('aria-expanded') == 'true' and await active(h) == 'cb-input')
    check(ex, 'selected option aria-selected', await h.locator('[role="option"][aria-selected="true"]').count() == 1)
    await inp.type('jap')
    await page.keyboard.press('Enter')
    check(ex, 'second chip', await chips.count() == 2 and 'Japan' in await chips.nth(1).inner_text())
    await page.keyboard.press('Escape')
    check(ex, 'Escape closes', await inp.get_attribute('aria-expanded') == 'false' and not await lb.is_visible())
    check(ex, 'activedescendant cleared when closed', await inp.get_attribute('aria-activedescendant') is None)
    await page.keyboard.press('ArrowDown')
    check(ex, 'ArrowDown reopens', await inp.get_attribute('aria-expanded') == 'true')
    await page.keyboard.press('Escape')
    await page.keyboard.press('Backspace')
    check(ex, 'Backspace on empty removes last chip', await chips.count() == 1)
    await inp.type('zz')
    check(ex, 'no-match message', 'No countries match' in await lb.inner_text())
    await page.keyboard.press('Escape')
    await page.keyboard.press('Escape')
    check(ex, 'second Escape clears query', await inp.input_value() == '')
    await inp.type('fra')
    await page.keyboard.press('Tab')
    check(ex, 'Tab closes without selecting', await inp.get_attribute('aria-expanded') == 'false' and await chips.count() == 1)
    await h.locator(f'button[aria-label="Remove {names[0]}"]').click()
    check(ex, 'chip remove + focus back to input', await chips.count() == 0 and await active(h) == 'cb-input')
    await inp.fill('')
    await inp.type('france')
    await page.keyboard.press('Enter')
    await inp.type('japan')
    await h.locator('.cb-option', has_text='Japan').click()
    check(ex, 'mouse click selects', await chips.count() == 2)
    await inp.type('fran')
    await page.keyboard.press('Enter')
    check(ex, 'selecting a selected option toggles it off', await chips.count() == 1)
    await inp.type('fran')
    await page.keyboard.press('Enter')
    await page.keyboard.press('Escape')
    await h.locator('.btn-primary').click()
    saved = await h.locator('.saved').inner_text()
    check(ex, 'form submit sees selection', 'Japan, France' in saved, saved)
    await h.locator('.cb-clear').click()
    check(ex, 'clear button clears all + focuses input', await chips.count() == 0 and await active(h) == 'cb-input')
    await inp.type('in')
    await page.keyboard.press('Enter')
    await inp.type('sw')
    await page.keyboard.press('ArrowDown')
    await page.wait_for_timeout(50)
    await shot(page, ex)
    await close(page)


# ---------------------------------------------------------------- dc50
async def t50(page):
    ex = 'dc50'
    h = await open_design(page, ex)
    await page.wait_for_timeout(1700)
    rows = h.locator('.log-row')
    sc = h.locator('.log-scroll')
    n = await rows.count()
    check(ex, 'only a window of rows rendered', 10 < n < 90, n)
    check(ex, 'spacer has full height', await h.locator('.log-spacer').evaluate('e => e.offsetHeight') == 260000)
    check(ex, 'first row is line 1', await rows.first.get_attribute('data-line') == '1')
    await sc.evaluate('e => { e.scrollTop = e.scrollHeight; }')
    await page.wait_for_timeout(150)
    check(ex, 'scrolled to bottom shows line 10000', await h.locator('.log-row[data-line="10000"]').count() == 1 and await rows.count() < 90)
    hb = await h.locator('.log-header').bounding_box()
    sb = await sc.bounding_box()
    check(ex, 'header sticky', abs(hb['y'] - sb['y']) < 2, (hb, sb))
    await sc.evaluate('e => { e.scrollTop = 130000; }')
    await page.wait_for_timeout(150)
    lines = [int(x) for x in await rows.evaluate_all('els => els.map(e => e.dataset.line)')]
    check(ex, 'middle window correct', min(lines) <= 5001 <= max(lines) and len(lines) < 90, (min(lines), max(lines)))
    await h.locator('.level-tab', has_text='ERROR').click()
    await page.wait_for_timeout(100)
    cnt = await h.locator('.match-count').inner_text()
    check(ex, 'level filter keeps virtualization', await rows.count() < 90 and await h.locator('.log-row:not(.level-error)').count() == 0, cnt)
    check(ex, 'filter resets scroll', await sc.evaluate('e => e.scrollTop') == 0)
    nerr = int(cnt.split('/')[0].strip().replace(',', ''))
    check(ex, 'spacer shrinks with filter', await h.locator('.log-spacer').evaluate('e => e.offsetHeight') == nerr * 26, nerr)
    await h.locator('.filter-input').fill('timeout')
    await page.wait_for_timeout(100)
    msgs = await h.locator('.log-row .c-msg').all_inner_texts()
    check(ex, 'text filter', len(msgs) > 0 and all('timeout' in m for m in msgs), msgs[:3])
    hidden_line = None
    for ln in range(1, 200):
        if await h.locator(f'.log-row[data-line="{ln}"]').count() == 0:
            hidden_line = ln
            break
    await h.locator('.jump-input').fill(str(hidden_line))
    await h.locator('.jump-btn').click()
    check(ex, 'jump to filtered-out line explains', 'hidden by the current filter' in await h.locator('.jump-error').inner_text())
    await h.locator('.filter-input').fill('')
    await h.locator('.level-tab', has_text='ALL').click()
    await h.locator('.jump-input').fill('5000')
    await h.locator('.jump-btn').click()
    await page.wait_for_timeout(150)
    row = h.locator('.log-row[data-line="5000"]')
    ok = await row.count() == 1
    check(ex, 'jump renders target row highlighted', ok and 'is-highlighted' in await row.get_attribute('class'))
    if ok:
        rb = await row.bounding_box()
        sb = await sc.bounding_box()
        check(ex, 'target row visible in viewport', sb['y'] + 30 <= rb['y'] and rb['y'] + rb['height'] <= sb['y'] + sb['height'], (rb, sb))
    check(ex, 'jump error cleared', await h.locator('.jump-error').count() == 0)
    await h.locator('.jump-input').fill('20000')
    await h.locator('.jump-btn').click()
    check(ex, 'out of range jump error', 'between 1 and 10,000' in await h.locator('.jump-error').inner_text())
    await h.locator('.jump-input').fill('5000')
    await h.locator('.jump-btn').click()
    await page.wait_for_timeout(1300)
    await shot(page, ex)
    await close(page)


TESTS = {'dc41': t41, 'dc42': t42, 'dc43': t43, 'dc44': t44, 'dc45': t45, 'dc46': t46, 'dc47': t47, 'dc48': t48, 'dc49': t49, 'dc50': t50}


async def main():
    which = json.loads(sys.argv[1]) if len(sys.argv) > 1 else list(TESTS)
    env = dict(os.environ, DIST_HTML=DIST)
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)], env=env)
    time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page = await b.new_page(viewport={'width': 1600, 'height': 950})
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            page.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:300]))

            async def route(r):
                u = r.request.url
                if 'react-dom' in u:
                    await r.fulfill(body='', content_type='text/javascript')
                elif 'react' in u:
                    await r.fulfill(path=str(ROOT / 'react-bundle.js'), content_type='text/javascript')
                elif 'babel' in u:
                    await r.fulfill(body=SHIM, content_type='text/javascript')
                elif 'fonts.g' in u:
                    await r.fulfill(body='', content_type='text/css')
                else:
                    await r.continue_()
            await page.route('**/*', route)
            await page.goto(f'http://127.0.0.1:{PORT}/')
            await page.wait_for_timeout(600)
            for ex in which:
                errs.clear()
                try:
                    await TESTS[ex](page)
                except Exception as e:  # noqa: BLE001
                    check(ex, 'test crashed', False, repr(e)[:400])
                    try:
                        await close(page)
                    except Exception:  # noqa: BLE001
                        pass
                check(ex, 'no page/console errors', not errs, errs[:3])
            await b.close()
    finally:
        srv.terminate()
    fails = [r for r in RESULTS if not r[2]]
    print(f'\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks passed')
    for f in fails:
        print('FAILED:', f[0], f[1])


asyncio.run(main())
