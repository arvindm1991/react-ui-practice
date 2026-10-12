import asyncio, subprocess, sys, time, pathlib, os
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
PORT = 8781
DIST = os.environ.get('DIST_HTML', '/tmp/claude-0/-home-claude/653a60f8-7891-5769-b62a-4ce1d270b59d/scratchpad/dist-A.html')
SHIM = open(ROOT / 'run.py').read().split('SHIM = """')[1].split('"""')[0]

RESULTS = []


def check(ex, name, ok, detail=''):
    RESULTS.append((ex, name, bool(ok)))
    print(('PASS' if ok else 'FAIL'), ex, '-', name, ('' if ok else '| ' + str(detail)))


async def open_design(page, ex):
    await page.evaluate(f'Workspace.open("{ex}")')
    await page.wait_for_timeout(900)
    await page.click('[data-ptab="design"]')
    await page.wait_for_timeout(1500)
    await page.click('[data-dmode="interact"]')
    btn = page.locator('#wideBtn')
    if (await btn.inner_text()).strip() == 'Expand':
        await btn.click()
        await page.wait_for_timeout(400)
    return page.locator('#designHost')


async def shot(page, ex):
    await page.wait_for_timeout(400)
    await page.screenshot(path=str(ROOT / 'shots' / f'{ex}.png'))


async def close(page):
    await page.evaluate('Workspace.close()')
    await page.wait_for_timeout(200)


async def t_dc01(page, h):
    ex = 'dc01'
    likes = h.locator('.likes')
    btn = h.locator('.like-btn')
    check(ex, 'initial 241 likes', await likes.inner_text() == '241 likes', await likes.inner_text())
    await btn.click()
    check(ex, 'liked -> 242 likes', await likes.inner_text() == '242 likes', await likes.inner_text())
    check(ex, 'liked class + aria', await btn.get_attribute('aria-pressed') == 'true' and 'is-liked' in (await btn.get_attribute('class')))
    fill = await h.locator('.like-btn path').get_attribute('fill')
    check(ex, 'heart filled', fill == 'currentColor', fill)
    color = await btn.evaluate('e => getComputedStyle(e).color')
    check(ex, 'heart red', color == 'rgb(232, 68, 90)', color)
    await shot(page, ex)
    await btn.click()
    check(ex, 'unlike -> 241', await likes.inner_text() == '241 likes')
    await h.locator('.photo').dblclick()
    check(ex, 'change: dblclick likes', await likes.inner_text() == '242 likes')
    await h.locator('.photo').dblclick()
    check(ex, 'change: dblclick never unlikes', await likes.inner_text() == '242 likes')


async def t_dc02(page, h):
    ex = 'dc02'
    bio = h.locator('#bio')
    count = h.locator('.bio-count')
    save = h.locator('.btn-primary')
    init = await bio.input_value()
    check(ex, 'initial remaining', await count.inner_text() == f'{160 - len(init)} characters left', await count.inner_text())
    await bio.fill('x' * 159)
    check(ex, 'singular', await count.inner_text() == '1 character left', await count.inner_text())
    cls = await h.locator('.bio-meter').get_attribute('class')
    check(ex, 'warn class under 20', 'is-warn' in cls, cls)
    col = await count.evaluate('e => getComputedStyle(e).color')
    check(ex, 'warn amber', col == 'rgb(245, 165, 36)', col)
    await bio.fill('x' * 165)
    check(ex, 'over text', await count.inner_text() == '5 characters over', await count.inner_text())
    col = await count.evaluate('e => getComputedStyle(e).color')
    check(ex, 'over red', col == 'rgb(242, 85, 107)', col)
    check(ex, 'save disabled over', await save.is_disabled())
    check(ex, 'textarea red border', 'is-over' in (await bio.get_attribute('class')))
    w = await h.locator('.bio-bar-fill').evaluate('e => e.style.width')
    check(ex, 'change: bar capped 100%', w == '100%', w)
    await bio.fill('x' * 80)
    w = await h.locator('.bio-bar-fill').evaluate('e => e.style.width')
    check(ex, 'change: bar 50%', w == '50%', w)
    check(ex, 'save enabled', not await save.is_disabled())
    await bio.fill('x' * 150)
    await shot(page, ex)


async def t_dc03(page, h):
    ex = 'dc03'
    pw = h.locator('#password')
    show = h.locator('.show-btn')
    submit = h.locator('.btn-primary')
    check(ex, 'starts hidden', await pw.get_attribute('type') == 'password')
    await show.click()
    check(ex, 'show -> text + Hide', await pw.get_attribute('type') == 'text' and (await show.inner_text()).strip() == 'Hide')
    await show.click()
    check(ex, 'hide again', await pw.get_attribute('type') == 'password' and (await show.inner_text()).strip() == 'Show')
    check(ex, 'empty: no label', (await h.locator('.strength-label').inner_text()) == '' and await h.locator('.segment.is-on').count() == 0)
    await pw.fill('abc')
    check(ex, 'typed 0 rules -> Weak/1', await h.locator('.strength-label').inner_text() == 'Weak' and await h.locator('.segment.is-on').count() == 1)
    await pw.fill('abcdefgh1')
    check(ex, 'two rules -> Fair/2', await h.locator('.strength-label').inner_text() == 'Fair' and await h.locator('.segment.is-on').count() == 2)
    await h.locator('#email').fill('ana@acme.co')
    check(ex, 'submit disabled until strong', await submit.is_disabled())
    await pw.fill('abcdefgh1!')
    check(ex, 'strong -> 3', await h.locator('.strength-label').inner_text() == 'Strong' and await h.locator('.segment.is-on').count() == 3)
    await page.wait_for_timeout(300)
    col = await h.locator('.segment.is-on').first.evaluate('e => getComputedStyle(e).backgroundColor')
    check(ex, 'strong green', col == 'rgb(18, 161, 80)', col)
    check(ex, 'submit enabled', not await submit.is_disabled())
    await pw.fill('a1')
    met = await h.locator('.rule.is-met').all_inner_texts()
    check(ex, 'change: rules checklist', await h.locator('.rule').count() == 3 and len(met) == 1 and 'number' in met[0], met)
    await pw.fill('sunset99')
    await show.click()
    await shot(page, ex)


async def t_dc04(page, h):
    ex = 'dc04'
    await page.wait_for_timeout(1400)
    tabs = await h.locator('.tab').all_inner_texts()
    check(ex, 'tab labels', [t.strip() for t in tabs] == ['Description', 'Specs', 'Reviews (3)'], tabs)
    check(ex, 'description default', await h.locator('.panel-text').count() == 1 and (await h.locator('.tab.is-active').inner_text()).strip() == 'Description')
    await h.locator('.tab', has_text='Specs').click()
    check(ex, 'specs shows table only', await h.locator('.specs').count() == 1 and await h.locator('.panel-text').count() == 0)
    check(ex, 'aria-selected', await h.locator('.tab', has_text='Specs').get_attribute('aria-selected') == 'true')
    await h.locator('.tab', has_text='Reviews').click()
    check(ex, 'reviews list', await h.locator('.review').count() == 3)
    await h.locator('.tab', has_text='Description').click()
    await h.locator('button.rating-link').click()
    check(ex, 'change: rating link -> reviews', await h.locator('.review').count() == 3 and 'Reviews' in await h.locator('.tab.is-active').inner_text())
    await h.locator('.tab', has_text='Specs').click()
    await shot(page, ex)


async def t_dc05(page, h):
    ex = 'dc05'
    q = h.locator('.faq-question')
    check(ex, 'all closed', await h.locator('.faq-answer').count() == 0)
    await q.nth(1).click()
    check(ex, 'open one', await h.locator('.faq-answer').count() == 1 and 'build command' in await h.locator('.faq-answer').inner_text())
    check(ex, 'aria-expanded', await q.nth(1).get_attribute('aria-expanded') == 'true')
    await q.nth(3).click()
    check(ex, 'one at a time', await h.locator('.faq-answer').count() == 1 and '14 regions' in await h.locator('.faq-answer').inner_text())
    await page.wait_for_timeout(300)
    tr = await h.locator('.faq-item.is-open .chevron').evaluate('e => getComputedStyle(e).transform')
    check(ex, 'chevron rotated', tr.startswith('matrix(-1'), tr)
    await q.nth(3).click()
    check(ex, 'click open closes', await h.locator('.faq-answer').count() == 0)
    await q.nth(0).click()
    await h.locator('.vote-btn', has_text='Yes').click()
    check(ex, 'change: thanks after vote', await h.locator('.thanks').count() == 1 and await h.locator('.vote-btn').count() == 0)
    await q.nth(0).click()
    await q.nth(0).click()
    check(ex, 'change: vote remembered', await h.locator('.thanks').count() == 1)
    await q.nth(2).click()
    check(ex, 'change: other item unvoted', await h.locator('.vote-btn').count() == 2)
    await shot(page, ex)


async def t_dc06(page, h):
    ex = 'dc06'
    await page.wait_for_timeout(1400)
    badge = h.locator('.left-badge')
    check(ex, 'loaded 4 tasks', await h.locator('.task').count() == 4)
    check(ex, '3 left', await badge.inner_text() == '3 left', await badge.inner_text())
    inp = h.locator('.add-input')
    await inp.fill('   ')
    check(ex, 'add disabled when blank', await h.locator('.add-btn').is_disabled())
    await inp.press('Enter')
    check(ex, 'blank ignored', await h.locator('.task').count() == 4)
    await inp.fill('Lab report draft')
    await inp.press('Enter')
    check(ex, 'enter adds to bottom', await h.locator('.task').count() == 5 and 'Lab report draft' in await h.locator('.task').last.inner_text())
    check(ex, 'input cleared', await inp.input_value() == '')
    check(ex, '4 left', await badge.inner_text() == '4 left')
    await inp.fill('Email Ms. Rivera')
    await h.locator('.add-btn').click()
    check(ex, 'button adds', await h.locator('.task').count() == 6 and await badge.inner_text() == '5 left')
    await h.locator('.task').nth(1).locator('.task-check').click()
    check(ex, 'toggle done', 'is-done' in await h.locator('.task').nth(1).get_attribute('class') and await badge.inner_text() == '4 left')
    await h.locator('.task').nth(5).locator('.delete-btn').click()
    check(ex, 'delete', await h.locator('.task').count() == 5 and await badge.inner_text() == '3 left')
    await shot(page, ex)
    clear = h.locator('.clear-btn')
    check(ex, 'change: clear shows count', (await clear.inner_text()) == 'Clear completed (2)', await clear.inner_text())
    await clear.click()
    check(ex, 'change: clear removes done', await h.locator('.task').count() == 3 and await h.locator('.clear-btn').count() == 0)
    for i in range(3):
        await h.locator('.task').nth(i).locator('.task-check').click()
    check(ex, 'all done', await badge.inner_text() == 'All done')


async def t_dc07(page, h):
    ex = 'dc07'
    await page.wait_for_timeout(1500)
    check(ex, 'loaded 9', await h.locator('.staff-card').count() == 9)
    check(ex, 'count 9 of 9', await h.locator('.count').inner_text() == 'Showing 9 of 9')
    s = h.locator('.search')
    await s.fill('nurse')
    check(ex, 'role match', await h.locator('.staff-card').count() == 2 and await h.locator('.count').inner_text() == 'Showing 2 of 9')
    await s.fill('  PRIYA ')
    check(ex, 'case/trim name match', await h.locator('.staff-card').count() == 1 and 'Priya' in await h.locator('.staff-card').inner_text())
    await s.fill('xyz')
    check(ex, 'no matches', 'No matches for “xyz”' in await h.locator('.message').inner_text())
    await h.locator('.link-btn').click()
    check(ex, 'clear search', await s.input_value() == '' and await h.locator('.staff-card').count() == 9)
    await h.locator('.chip').click()
    check(ex, 'change: on call only', await h.locator('.staff-card').count() == 4 and await h.locator('.count').inner_text() == 'Showing 4 of 9')
    await s.fill('dr.')
    check(ex, 'change: combines with search', await h.locator('.staff-card').count() == 2)
    await s.fill('')
    await shot(page, ex)


async def t_dc08(page, h):
    ex = 'dc08'
    minus = h.locator('.step-btn').nth(0)
    plus = h.locator('.step-btn').nth(1)
    qty = h.locator('.qty')
    check(ex, 'starts at 1, minus disabled', await qty.inner_text() == '1' and await minus.is_disabled())
    await plus.click(); await plus.click()
    check(ex, 'plus to 3', await qty.inner_text() == '3')
    sub = await h.locator('.summary-row').first.inner_text()
    check(ex, 'subtotal label + value', 'Subtotal (3 × $48.00)' in sub and '$144.00' in sub, sub)
    await minus.click()
    check(ex, 'minus to 2', await qty.inner_text() == '2')
    check(ex, 'change: fees', await h.locator('.fees').inner_text() == '$9.00')
    check(ex, 'change: total + checkout', await h.locator('.total').inner_text() == '$105.00' and await h.locator('.checkout').inner_text() == 'Checkout · $105.00', await h.locator('.checkout').inner_text())
    for _ in range(10):
        if await plus.is_disabled():
            break
        await plus.click()
    check(ex, 'max 8, plus disabled', await qty.inner_text() == '8' and await plus.is_disabled())
    check(ex, 'max note', await h.locator('.max-note').inner_text() == 'Max 8 tickets per order')
    await shot(page, ex)


async def t_dc09(page, h):
    ex = 'dc09'
    await page.wait_for_timeout(1200)
    names = lambda: h.locator('.stay-name').all_inner_texts()
    orig = await names()
    check(ex, 'loaded 6', len(orig) == 6, orig)
    btn = h.locator('.sort-btn')
    await btn.click()
    opts = await h.locator('.sort-option').all_inner_texts()
    check(ex, 'menu opens with 4 options', len(opts) == 4, opts)
    await btn.click()
    check(ex, 'button toggles closed', await h.locator('.sort-menu').count() == 0)
    await btn.click()
    await h.locator('.sort-option', has_text='Price: low to high').click()
    check(ex, 'closes on select', await h.locator('.sort-menu').count() == 0)
    check(ex, 'label updates', 'Price: low to high' in await btn.inner_text())
    n = await names()
    check(ex, 'sorted asc', n[0] == 'Harbor Studio' and n[-1] == 'Lakeview A-Frame', n)
    await btn.click()
    await h.locator('.sort-option', has_text='Top rated').click()
    n = await names()
    check(ex, 'top rated', n[0] == 'Treehouse Loft', n)
    await btn.click()
    await h.locator('.sort-option', has_text='Recommended').click()
    check(ex, 'recommended restores order', await names() == orig)
    await btn.click()
    await h.locator('.toolbar h1').click()
    check(ex, 'outside click closes', await h.locator('.sort-menu').count() == 0)
    await btn.click()
    await page.keyboard.press('Escape')
    check(ex, 'change: escape closes', await h.locator('.sort-menu').count() == 0)
    await btn.click()
    await h.locator('.sort-option', has_text='high to low').click()
    await btn.click()
    sel = h.locator('.sort-option.is-selected')
    check(ex, 'change: selected has check', await sel.count() == 1 and '✓' in await sel.inner_text() and 'high to low' in await sel.inner_text())
    await shot(page, ex)
    await page.keyboard.press('Escape')


async def t_dc10(page, h):
    ex = 'dc10'
    stars = h.locator('.star')
    label = h.locator('.rating-label')
    submit = h.locator('.submit')
    check(ex, '5 star buttons', await stars.count() == 5)
    check(ex, 'empty label + disabled', await label.inner_text() == 'Tap a star to rate' and await submit.is_disabled())
    await stars.nth(3).hover()
    check(ex, 'hover preview 4', await h.locator('.star.is-on').count() == 4 and await label.inner_text() == 'Good')
    await h.locator('.rate-block h1').hover()
    check(ex, 'leave restores 0', await h.locator('.star.is-on').count() == 0)
    await stars.nth(4).click()
    await h.locator('.rate-block h1').hover()
    check(ex, 'click sets 5 Excellent', await h.locator('.star.is-on').count() == 5 and await label.inner_text() == 'Excellent')
    check(ex, 'submit enabled', not await submit.is_disabled())
    col = await stars.first.evaluate('e => getComputedStyle(e).color')
    check(ex, 'gold color', col == 'rgb(255, 178, 30)', col)
    await stars.nth(1).hover()
    check(ex, 'hover overrides set', await h.locator('.star.is-on').count() == 2 and await label.inner_text() == 'Poor')
    await h.locator('.rate-block h1').hover()
    await h.locator('.clear-btn').click()
    check(ex, 'clear resets', await h.locator('.star.is-on').count() == 0 and await submit.is_disabled() and await h.locator('.clear-btn').count() == 0)
    await stars.nth(1).click()
    await h.locator('.rate-block h1').hover()
    check(ex, 'change: chips at 2 stars', await h.locator('.chip').count() == 4 and await submit.is_disabled())
    await h.locator('.chip', has_text='Cold food').click()
    await h.locator('.chip', has_text='Late').click()
    check(ex, 'change: multi-select enables', await h.locator('.chip.is-on').count() == 2 and not await submit.is_disabled())
    await h.locator('.chip', has_text='Late').click()
    check(ex, 'change: chip toggles off', await h.locator('.chip.is-on').count() == 1)
    await shot(page, ex)
    await stars.nth(3).click()
    check(ex, 'change: chips hidden at 4', await h.locator('.chip').count() == 0 and not await submit.is_disabled())
    await submit.click()
    check(ex, 'submit shows thanks', await h.locator('.thanks').count() == 1)


TESTS = {'dc01': t_dc01, 'dc02': t_dc02, 'dc03': t_dc03, 'dc04': t_dc04, 'dc05': t_dc05,
         'dc06': t_dc06, 'dc07': t_dc07, 'dc08': t_dc08, 'dc09': t_dc09, 'dc10': t_dc10}


async def main():
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
                if 'react-dom' in u: await r.fulfill(body='', content_type='text/javascript')
                elif 'react' in u: await r.fulfill(path=str(ROOT / 'react-bundle.js'), content_type='text/javascript')
                elif 'babel' in u: await r.fulfill(body=SHIM, content_type='text/javascript')
                elif 'fonts.g' in u: await r.fulfill(body='', content_type='text/css')
                else: await r.continue_()
            await page.route('**/*', route)
            await page.goto(f'http://127.0.0.1:{PORT}/')
            await page.wait_for_timeout(600)
            only = sys.argv[1:] or list(TESTS)
            for ex in only:
                errs.clear()
                h = await open_design(page, ex)
                try:
                    await TESTS[ex](page, h)
                except Exception as e:  # noqa: BLE001
                    check(ex, 'no exception', False, repr(e)[:300])
                check(ex, 'no page/console errors', not errs, errs)
                await close(page)
            await b.close()
    finally:
        srv.terminate()
    fails = [r for r in RESULTS if not r[2]]
    print(f'\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks passed')
    for f in fails:
        print('FAILED:', f)


asyncio.run(main())
