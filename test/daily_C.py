"""Behaviour tests for daily batch C (dc21-dc30). Runs the SOLUTION via the Design tab."""
import asyncio, subprocess, sys, time, pathlib, os
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
PORT = int(os.environ.get('PORT', '8783'))
SHIM = open(ROOT / 'run.py').read().split('SHIM = """')[1].split('"""')[0]
ONLY = sys.argv[1].split(',') if len(sys.argv) > 1 else None

results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + str(detail)))


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


async def new_page(browser, clock=False):
    ctx = await browser.new_context(viewport={'width': 1600, 'height': 950})
    page = await ctx.new_page()
    errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:200]))
    await page.route('**/*', route)
    if clock:
        await page.clock.install()
    await page.goto(f'http://127.0.0.1:{PORT}/')
    await page.wait_for_timeout(600)
    return page, errs


async def open_design(page, ex, wait=1800):
    await page.evaluate(f'Workspace.open("{ex}")')
    await page.wait_for_timeout(900)
    await page.click('[data-ptab="design"]')
    await page.wait_for_timeout(wait)
    await page.click('[data-dmode="interact"]')
    if (await page.inner_text('#wideBtn')).strip() == 'Expand':
        await page.click('#wideBtn')
    await page.wait_for_timeout(300)
    return page.locator('#designHost')


async def close(page):
    await page.click('[data-ptab="task"]')
    await page.evaluate('Workspace.close()')


async def shot(page, ex):
    await page.screenshot(path=str(ROOT / 'shots' / f'{ex}.png'))


async def t21(page):
    h = await open_design(page, 'dc21', wait=0)
    check('dc21 loading text', 'Loading activity' in await h.locator('.card').inner_text())
    await page.wait_for_timeout(1500)
    check('dc21 first page 5 rows', await h.locator('.activity-item').count() == 5, await h.locator('.activity-item').count())
    btn = h.locator('.load-more')
    await btn.click()
    await page.wait_for_timeout(80)
    check('dc21 button Loading…', (await btn.inner_text()) == 'Loading…' and await btn.is_disabled())
    await btn.click(force=True)  # disabled: must not double-load
    await page.wait_for_timeout(1400)
    check('dc21 appended to 10', await h.locator('.activity-item').count() == 10, await h.locator('.activity-item').count())
    check('dc21 first item kept', 'Maya Chen' in await h.locator('.activity-item').first.inner_text())
    await shot(page, 'dc21')
    await h.locator('.load-more').click()
    await page.wait_for_timeout(1400)
    check('dc21 13 rows', await h.locator('.activity-item').count() == 13)
    check('dc21 button gone', await h.locator('.load-more').count() == 0)
    check('dc21 caught up line', "all caught up · 13 events" in await h.locator('.feed-end').inner_text())
    await close(page)


async def t22(page):
    h = await open_design(page, 'dc22', wait=800)
    inp = h.locator('.tag-input')
    await inp.click()
    await inp.type('React')
    await page.keyboard.press('Enter')
    await inp.type('design systems,')
    await page.wait_for_timeout(100)
    chips = h.locator('.tag-box .chip')
    check('dc22 enter + comma add chips', await chips.count() == 2 and (await chips.nth(1).inner_text()).startswith('design systems'), await chips.all_inner_texts())
    check('dc22 input cleared, no comma', await inp.input_value() == '')
    await inp.type('react')
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check('dc22 dup ignored', await chips.count() == 2)
    check('dc22 dup message', 'already added' in await h.locator('.field-help.is-error').inner_text())
    await page.keyboard.press('Backspace')
    await page.wait_for_timeout(100)
    check('dc22 backspace removes last', await chips.count() == 1 and 'React' in await chips.first.inner_text())
    for t in ['css', 'ux', 'tokens', 'figma']:
        await inp.type(t)
        await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check('dc22 five chips + counter', await chips.count() == 5 and '5 / 5' in await h.locator('.field-help').inner_text())
    await shot(page, 'dc22')
    await inp.type('extra')
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check('dc22 max 5 message', await chips.count() == 5 and 'up to 5 tags' in await h.locator('.field-help').inner_text())
    await h.locator('.chip-x').first.click()
    await page.wait_for_timeout(100)
    check('dc22 x removes chip', await chips.count() == 4 and 'React' not in ' '.join(await chips.all_inner_texts()))
    await close(page)


async def t23(browser):
    page, errs = await new_page(browser, clock=True)
    h = await open_design(page, 'dc23', wait=1000)
    time_el = h.locator('.time')
    start = h.locator('.btn-primary')
    check('dc23 initial 25:00', await time_el.inner_text() == '25:00')
    await start.click()
    check('dc23 label Pause', await start.inner_text() == 'Pause')
    await page.clock.run_for(3000)
    await page.wait_for_timeout(100)
    check('dc23 ticks to 24:57', await time_el.inner_text() == '24:57', await time_el.inner_text())
    # rapid toggles must not create extra intervals
    for _ in range(5):
        await start.click()
    await page.wait_for_timeout(50)
    check('dc23 paused after odd toggles', await start.inner_text() == 'Start')
    await start.click()
    await page.clock.run_for(2000)
    await page.wait_for_timeout(100)
    check('dc23 single interval (24:55)', await time_el.inner_text() == '24:55', await time_el.inner_text())
    await start.click()
    await page.clock.run_for(3000)
    await page.wait_for_timeout(50)
    check('dc23 pause holds', await time_el.inner_text() == '24:55', await time_el.inner_text())
    await start.click()
    for _ in range(30):
        await page.clock.run_for(50 * 1000)
    await page.wait_for_timeout(200)
    t = await time_el.inner_text()
    pill = (await h.locator('.mode-pill').text_content()).strip()
    check('dc23 switched to Break and keeps running', pill == 'Break' and (t.startswith('04:') or t.startswith('05:')) and await start.inner_text() == 'Pause', (t, pill))
    check('dc23 break style + session dot', await h.locator('.timer.mode-break').count() == 1 and '1 of 4' in await h.locator('.sessions-label').inner_text())
    await shot(page, 'dc23')
    for _ in range(7):
        await page.clock.run_for(50 * 1000)
    await page.wait_for_timeout(200)
    pill = (await h.locator('.mode-pill').text_content()).strip()
    check('dc23 break ends -> Focus 25:00 stopped', pill == 'Focus' and await time_el.inner_text() == '25:00' and await start.inner_text() == 'Start', (pill, await time_el.inner_text()))
    await start.click()
    await page.clock.run_for(4000)
    await page.wait_for_timeout(100)
    w = await h.locator('.progress-fill').evaluate('e => e.style.width')
    check('dc23 progress bar derived', w not in ('', '0%'), w)
    await h.locator('.btn-ghost').click()
    await page.wait_for_timeout(100)
    check('dc23 reset', await time_el.inner_text() == '25:00' and (await h.locator('.mode-pill').text_content()).strip() == 'Focus' and await start.inner_text() == 'Start')
    check('dc23 no errors', not errs, errs)
    await page.context.close()


async def t24(page):
    await page.evaluate('localStorage.removeItem("northwind-theme")')
    await page.emulate_media(color_scheme='light')
    h = await open_design(page, 'dc24', wait=800)
    app = h.locator('.app')
    check('dc24 default system->light', await app.get_attribute('data-theme') == 'light' and await h.locator('.theme-note').count() == 1)
    await h.locator('.segmented[aria-label="Theme"] .segment', has_text='Dark').click()
    await page.wait_for_timeout(100)
    bg = await app.evaluate('e => getComputedStyle(e).backgroundColor')
    check('dc24 dark applied', await app.get_attribute('data-theme') == 'dark' and bg == 'rgb(11, 17, 32)', bg)
    check('dc24 saved', await page.evaluate('localStorage.getItem("northwind-theme")') == 'dark')
    await shot(page, 'dc24')
    await close(page)
    h = await open_design(page, 'dc24', wait=800)
    app = h.locator('.app')
    check('dc24 restored after reload', await app.get_attribute('data-theme') == 'dark' and await h.locator('.segment.is-selected', has_text='Dark').count() == 1)
    await h.locator('.segmented[aria-label="Theme"] .segment', has_text='System').click()
    await page.wait_for_timeout(100)
    check('dc24 system light', await app.get_attribute('data-theme') == 'light')
    await page.emulate_media(color_scheme='dark')
    await page.wait_for_timeout(150)
    check('dc24 system follows OS live', await app.get_attribute('data-theme') == 'dark' and 'dark' in await h.locator('.theme-note').inner_text())
    await page.emulate_media(color_scheme='light')
    await page.evaluate('localStorage.removeItem("northwind-theme")')
    await close(page)


async def t25(page):
    h = await open_design(page, 'dc25', wait=800)
    ta = h.locator('.composer-input')
    await ta.fill('See you soon')
    await ta.evaluate('e => e.setSelectionRange(3, 3)')
    await h.locator('.tool-btn').click()
    await page.wait_for_timeout(80)
    check('dc25 loading', 'Loading emoji' in await h.locator('.emoji-popover').inner_text())
    await page.wait_for_timeout(1100)
    check('dc25 tabs + grid', await h.locator('.emoji-tab').count() == 3 and await h.locator('.emoji-btn').count() == 12)
    await h.locator('.emoji-tab').nth(2).click()
    await page.wait_for_timeout(80)
    check('dc25 inside click keeps open', await h.locator('.emoji-popover').count() == 1 and 'Work' in await h.locator('.emoji-heading').inner_text())
    await h.locator('.emoji-btn', has_text='🚀').click()
    await page.wait_for_timeout(150)
    val = await ta.input_value()
    caret = await ta.evaluate('e => e.selectionStart')
    check('dc25 inserted at cursor', val == 'See🚀 you soon', val)
    check('dc25 caret after emoji + closed', caret == 5 and await h.locator('.emoji-popover').count() == 0, caret)
    await ta.evaluate('e => e.setSelectionRange(0, 3)')  # select "See" -> replace
    await h.locator('.tool-btn').click()
    await page.wait_for_timeout(1100)
    check('dc25 recent row', await h.locator('.recent-row .emoji-btn').count() == 1)
    await h.locator('.emoji-section:not(.recent-row) .emoji-btn').first.click()
    await page.wait_for_timeout(150)
    check('dc25 replaces selection', await ta.input_value() == '😀🚀 you soon', await ta.input_value())
    await h.locator('.tool-btn').click()
    await page.wait_for_timeout(1100)
    rec = await h.locator('.recent-row .emoji-btn').all_inner_texts()
    check('dc25 recent most-recent-first', rec == ['😀', '🚀'], rec)
    await shot(page, 'dc25')
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(100)
    check('dc25 escape closes', await h.locator('.emoji-popover').count() == 0)
    await h.locator('.tool-btn').click()
    await page.wait_for_timeout(100)
    await h.locator('.channel-head').click()
    await page.wait_for_timeout(100)
    check('dc25 outside click closes', await h.locator('.emoji-popover').count() == 0)
    await close(page)


async def t26(page):
    h = await open_design(page, 'dc26', wait=800)
    inp = h.locator('.search-input')
    check('dc26 empty hint', 'Start typing to search 18 people' in await h.locator('.dir-message').inner_text())
    await inp.type('j')
    await page.wait_for_timeout(420)
    check('dc26 searching shown', await h.locator('.dir-status').count() == 1)
    await inp.type('an', delay=40)
    await page.wait_for_timeout(1900)
    names = await h.locator('.person-name').all_inner_texts()
    check('dc26 race: jan results win (5)', len(names) == 5 and 'Jamal Wright' not in names, names)
    check('dc26 no searching after settle', await h.locator('.dir-status').count() == 0)
    await inp.type('e')  # "jane": old results stay visible + dimmed while loading
    await page.wait_for_timeout(450)
    check('dc26 stale results dimmed, not cleared', await h.locator('.directory.is-loading').count() == 1 and await h.locator('.person').count() == 5)
    marks = await h.locator('mark.match').all_inner_texts()
    check('dc26 highlight uses results query (jan)', len(marks) == 5 and all(m.lower() == 'jan' for m in marks), marks)
    await page.keyboard.press('Backspace')
    await page.wait_for_timeout(1500)
    marks = await h.locator('mark.match').all_inner_texts()
    check('dc26 highlight', len(marks) == 5 and marks[0].lower() == 'jan', marks)
    await shot(page, 'dc26')
    await inp.fill('zzz')
    await page.wait_for_timeout(1000)
    check('dc26 no match', 'No people match "zzz"' in await h.locator('.dir-message').inner_text())
    await inp.fill('')
    await page.wait_for_timeout(200)
    check('dc26 cleared', 'Start typing' in await h.locator('.dir-message').inner_text() and await h.locator('.dir-status').count() == 0)
    await close(page)


async def t27(page):
    h = await open_design(page, 'dc27', wait=0)
    check('dc27 loading', 'Loading board' in await h.locator('.board-loading').inner_text())
    await page.wait_for_timeout(1400)
    counts = await h.locator('.count').all_inner_texts()
    check('dc27 counts 3, 2/3, 2', counts == ['3', '2 / 3', '2'], counts)
    todo = h.locator('.column').nth(0)
    check('dc27 left disabled in To do', await todo.locator('.move-btn[aria-label="Move left"]').first.is_disabled())
    await todo.locator('.add-input').fill('   ')
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(80)
    check('dc27 blank ignored', await todo.locator('.card').count() == 3)
    await todo.locator('.add-input').fill('Write launch email')
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(100)
    check('dc27 add card', await todo.locator('.card').count() == 4 and 'Write launch email' in await todo.locator('.card').last.inner_text())
    check('dc27 input cleared', await todo.locator('.add-input').input_value() == '')
    await todo.locator('.card').first.locator('[aria-label="Move right"]').click()
    await page.wait_for_timeout(100)
    counts = await h.locator('.count').all_inner_texts()
    check('dc27 move right', counts == ['3', '3 / 3', '2'], counts)
    check('dc27 full style', await h.locator('.count.is-full').count() == 1)
    await todo.locator('.card').first.locator('[aria-label="Move right"]').click()
    await page.wait_for_timeout(100)
    counts = await h.locator('.count').all_inner_texts()
    check('dc27 WIP blocks', counts == ['3', '3 / 3', '2'] and 'WIP limit of 3' in await h.locator('.wip-notice').inner_text(), counts)
    await shot(page, 'dc27')
    done = h.locator('.column').nth(2)
    check('dc27 right disabled in Done', await done.locator('[aria-label="Move right"]').first.is_disabled())
    await h.locator('.column').nth(1).locator('.card').first.locator('[aria-label="Move right"]').click()
    await page.wait_for_timeout(100)
    counts = await h.locator('.count').all_inner_texts()
    check('dc27 move to done clears notice', counts == ['3', '2 / 3', '3'] and await h.locator('.wip-notice').count() == 0, counts)
    await close(page)


async def t28(page):
    h = await open_design(page, 'dc28', wait=1300)
    comments = h.locator('.comment')
    check('dc28 replies collapsed', await h.locator('.reply').count() == 0)
    toggles = await h.locator('.muted-link').all_inner_texts()
    check('dc28 toggle labels', toggles == ['Show 3 replies', 'Show 1 reply'], toggles)
    await comments.nth(0).locator('.link-btn', has_text='Show 3 replies').click()
    await page.wait_for_timeout(80)
    check('dc28 expand', await comments.nth(0).locator('.reply').count() == 3 and 'Hide replies' in await comments.nth(0).inner_text())
    await comments.nth(0).get_by_role('button', name='Reply', exact=True).first.click()
    await page.wait_for_timeout(80)
    check('dc28 one box under comment 1', await h.locator('.reply-box').count() == 1 and await comments.nth(0).locator('.reply-box').count() == 1)
    await comments.nth(1).get_by_role('button', name='Reply', exact=True).click()
    await page.wait_for_timeout(80)
    check('dc28 box moves to comment 2', await h.locator('.reply-box').count() == 1 and await comments.nth(1).locator('.reply-box').count() == 1)
    ph = await h.locator('.reply-input').get_attribute('placeholder')
    focused = await h.locator('.reply-input').evaluate('e => e.getRootNode().activeElement === e')
    check('dc28 placeholder + focus', ph == 'Reply to Ivy Chen…' and focused, (ph, focused))
    check('dc28 blank disabled', await h.locator('.post-btn').is_disabled())
    await h.locator('.reply-input').fill('Up to a day ahead, keep it covered.')
    await h.locator('.post-btn').click()
    await page.wait_for_timeout(80)
    check('dc28 pending', await h.locator('.post-btn').inner_text() == 'Posting…' and await h.locator('.reply-input').is_disabled())
    await shot(page, 'dc28')
    await page.wait_for_timeout(1300)
    r = comments.nth(1).locator('.reply')
    check('dc28 reply added + box closed', await r.count() == 1 and 'You' in await r.inner_text() and await h.locator('.reply-box').count() == 0)
    check('dc28 thread expanded after post', 'Hide replies' in await comments.nth(1).inner_text())
    await comments.nth(0).locator('.link-btn', has_text='Hide replies').click()
    await page.wait_for_timeout(80)
    check('dc28 collapse', await comments.nth(0).locator('.reply').count() == 0)
    await comments.nth(2).get_by_role('button', name='Reply', exact=True).click()
    await h.locator('.ghost-btn').click()
    await page.wait_for_timeout(80)
    check('dc28 cancel', await h.locator('.reply-box').count() == 0)
    await close(page)


async def t29(page):
    h = await open_design(page, 'dc29', wait=1300)
    counter = h.locator('.counter')
    await page.mouse.move(5, 5)
    check('dc29 1 / 7', await counter.inner_text() == '1 / 7')
    await h.locator('.nav-next').click()
    check('dc29 next', await counter.inner_text() == '2 / 7')
    await h.locator('.nav-prev').click()
    await h.locator('.nav-prev').click()
    check('dc29 prev wraps', await counter.inner_text() == '7 / 7')
    await h.locator('.nav-next').click()
    check('dc29 next wraps', await counter.inner_text() == '1 / 7')
    await h.locator('.dot').nth(2).click()
    check('dc29 dot', await counter.inner_text() == '3 / 7' and await h.locator('.dot.is-active').count() == 1)
    await page.mouse.move(5, 5)
    await page.wait_for_timeout(4400)
    check('dc29 autoplay', await counter.inner_text() == '4 / 7', await counter.inner_text())
    await page.wait_for_timeout(3000)
    await h.locator('.nav-next').click()  # 5 / 7, restarts the 4 s countdown
    await page.mouse.move(5, 5)
    await page.wait_for_timeout(1800)
    check('dc29 manual move restarts countdown', await counter.inner_text() == '5 / 7', await counter.inner_text())
    await h.locator('.nav-prev').click()  # back to 4 / 7
    await h.locator('.photo').hover()
    await page.wait_for_timeout(4500)
    check('dc29 hover pauses', await counter.inner_text() == '4 / 7', await counter.inner_text())
    await h.locator('.photo').click()
    await page.keyboard.press('ArrowRight')
    await page.wait_for_timeout(50)
    check('dc29 ArrowRight', await counter.inner_text() == '5 / 7', await counter.inner_text())
    await page.keyboard.press('ArrowLeft')
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(50)
    check('dc29 ArrowLeft', await counter.inner_text() == '3 / 7', await counter.inner_text())
    await h.locator('.reserve').focus()
    await page.keyboard.press('ArrowRight')
    await page.wait_for_timeout(50)
    check('dc29 arrows outside ignored', await counter.inner_text() == '3 / 7')
    await shot(page, 'dc29')
    await close(page)


async def t30(page):
    h = await open_design(page, 'dc30', wait=1500)
    dripper = h.locator('.product', has_text='Ceramic dripper')
    await dripper.locator('.add-btn').click()
    await dripper.locator('.add-btn').click()
    check('dc30 badge 2', await h.locator('.badge').inner_text() == '2')
    await h.locator('.cart-btn').click()
    await page.wait_for_timeout(100)
    check('dc30 drawer line qty 2', await h.locator('.line').count() == 1 and await h.locator('.qty-value').inner_text() == '2')
    check('dc30 totals', await h.locator('.subtotal').inner_text() == '$56.00' and await h.locator('.tax').inner_text() == '$4.62' and await h.locator('.total-value').inner_text() == '$60.62')
    check('dc30 shipping progress', 'Add $19.00 more' in await h.locator('.ship-text').inner_text())
    await h.locator('.coupon-input').fill('bogus')
    await h.locator('.coupon-btn').click()
    await page.wait_for_timeout(60)
    check('dc30 checking', await h.locator('.coupon-btn').inner_text() == 'Checking…')
    await page.wait_for_timeout(1150)
    check('dc30 invalid coupon', 'Code "BOGUS" isn\'t valid.' in await h.locator('.coupon-error').inner_text(), await h.locator('.coupon-error').inner_text())
    await h.locator('[aria-label="Increase quantity"]').click()
    await page.wait_for_timeout(60)
    check('dc30 qty 3 + unlocked', await h.locator('.qty-value').inner_text() == '3' and await h.locator('.ship.is-unlocked').count() == 1)
    await h.locator('.coupon-input').fill('save10')
    await h.locator('.coupon-btn').click()
    await page.wait_for_timeout(1200)
    check('dc30 coupon applied', 'SAVE10 applied' in await h.locator('.coupon-applied').inner_text())
    check('dc30 discount totals', await h.locator('.sum-row.discount').inner_text() == 'Discount\n-$8.40' and await h.locator('.tax').inner_text() == '$6.24' and await h.locator('.total-value').inner_text() == '$81.84',
          (await h.locator('.sum-row.discount').inner_text(), await h.locator('.tax').inner_text(), await h.locator('.total-value').inner_text()))
    await shot(page, 'dc30')
    await h.locator('.close-btn').click()
    await page.wait_for_timeout(60)
    check('dc30 closed', await h.locator('.drawer').count() == 0)
    await h.locator('.cart-btn').click()
    await page.wait_for_timeout(60)
    check('dc30 coupon survives reopen', await h.locator('.coupon-applied').count() == 1)
    await h.locator('[aria-label="Decrease quantity"]').click()
    await h.locator('[aria-label="Decrease quantity"]').click()
    check('dc30 minus disabled at 1', await h.locator('[aria-label="Decrease quantity"]').is_disabled() and await h.locator('.qty-value').inner_text() == '1')
    await h.locator('.line .text-btn').click()
    await page.wait_for_timeout(60)
    check('dc30 remove -> empty', 'Your cart is empty' in await h.locator('.drawer').inner_text() and await h.locator('.badge').inner_text() == '0')
    await h.locator('.drawer-backdrop').click(position={'x': 10, 'y': 10})
    await page.wait_for_timeout(60)
    check('dc30 backdrop closes', await h.locator('.drawer').count() == 0)
    await close(page)


async def main():
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)], env={**os.environ})
    time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page, errs = await new_page(b)
            tests = [('dc21', t21), ('dc22', t22), ('dc24', t24), ('dc25', t25), ('dc26', t26), ('dc27', t27), ('dc28', t28), ('dc29', t29), ('dc30', t30)]
            for ex, fn in tests:
                if ONLY and ex not in ONLY:
                    continue
                errs.clear()
                try:
                    await fn(page)
                except Exception as e:  # noqa: BLE001
                    check(ex + ' crashed', False, e)
                    try:
                        await close(page)
                    except Exception:  # noqa: BLE001
                        pass
                check(ex + ' no page errors', not errs, errs)
            if not ONLY or 'dc23' in ONLY:
                try:
                    await t23(b)
                except Exception as e:  # noqa: BLE001
                    check('dc23 crashed', False, e)
            await b.close()
    finally:
        srv.terminate()
    fails = [n for n, ok in results if not ok]
    print(f'\n{len(results) - len(fails)}/{len(results)} passed')
    if fails:
        print('FAILED:', fails)


asyncio.run(main())
