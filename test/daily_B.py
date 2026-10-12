"""Behaviour tests for daily challenges batch B (dc11-dc20). Runs the SOLUTION in the Design tab."""
import asyncio, os, subprocess, sys, time, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
PORT = 8782
DIST = os.environ.get('DIST_HTML', '/tmp/claude-0/-home-claude/653a60f8-7891-5769-b62a-4ce1d270b59d/scratchpad/dist-B.html')
SHIM = open(ROOT / 'run.py').read().split('SHIM = """')[1].split('"""')[0]
ONLY = sys.argv[1].split(',') if len(sys.argv) > 1 else None

results = []
# First-load states (skeleton/loading text) are gone before open_design returns, so catch them right after mount.
EARLY = {'dc13': '.skeleton-card', 'dc14': '.loading'}
early = {}


def check(ex, name, ok, detail=''):
    results.append((ex, name, bool(ok)))
    print(('PASS' if ok else 'FAIL'), ex, '·', name, ('' if ok else '→ ' + str(detail)))


async def open_design(page, ex):
    await page.evaluate(f'Workspace.open("{ex}")')
    await page.wait_for_timeout(900)
    await page.click('[data-ptab="design"]')
    sel = EARLY.get(ex)
    if sel:
        loc = page.locator('#designHost').locator(sel)
        try:
            await loc.first.wait_for(state='attached', timeout=3000)
            early[ex] = await loc.count()
        except Exception:  # noqa: BLE001
            early[ex] = 0
    await page.wait_for_timeout(1500)
    if (await page.inner_text('#wideBtn')).strip() == 'Expand':
        await page.click('#wideBtn')
        await page.wait_for_timeout(300)
    await page.click('[data-dmode="interact"]')
    return page.locator('#designHost')


async def close(page):
    await page.click('[data-ptab="task"]')
    await page.evaluate('Workspace.close()')


async def shot(page, ex):
    await page.screenshot(path=str(ROOT / 'shots' / f'{ex}.png'))


async def t_dc11(page, h):
    ex = 'dc11'
    cnt = h.locator('.enabled-count')
    check(ex, 'initial 4 of 7', (await cnt.inner_text()) == '4 of 7 enabled', await cnt.inner_text())
    check(ex, '7 toggles in rows', await h.locator('.setting-row .toggle').count() == 7)
    await h.locator('.setting-row').nth(3).locator('.toggle').click()
    check(ex, 'toggle one on -> 5', (await cnt.inner_text()) == '5 of 7 enabled', await cnt.inner_text())
    check(ex, 'aria-checked flipped', await h.locator('.setting-row').nth(3).locator('.toggle').get_attribute('aria-checked') == 'true')
    await h.locator('.setting-row').nth(0).locator('.toggle').click()
    check(ex, 'toggle one off -> 4', (await cnt.inner_text()) == '4 of 7 enabled')
    await shot(page, ex)
    await h.locator('.link-btn').click()
    check(ex, 'turn all off -> 0', (await cnt.inner_text()) == '0 of 7 enabled')
    check(ex, 'all rows muted', await h.locator('.setting-row.is-off').count() == 7)
    check(ex, 'change: label Turn all on', (await h.locator('.link-btn').inner_text()) == 'Turn all on')
    await h.locator('.link-btn').click()
    check(ex, 'change: turn all on -> 7', (await cnt.inner_text()) == '7 of 7 enabled')
    check(ex, 'label back to Turn all off', (await h.locator('.link-btn').inner_text()) == 'Turn all off')
    check(ex, 'DND toggle still independent', await h.locator('.dnd .toggle').get_attribute('aria-checked') == 'false')


async def t_dc12(page, h):
    ex = 'dc12'
    plans = h.locator('.plan')
    creator = plans.nth(1)
    check(ex, 'monthly default $12/month', (await creator.locator('.price').inner_text()).replace('\n', '') == '$12/month', await creator.locator('.price').inner_text())
    check(ex, 'hobby Free no period', (await plans.nth(0).locator('.price').inner_text()).strip() == 'Free')
    await h.locator('.billing-opt', has_text='Yearly').click()
    check(ex, 'yearly active pill', 'is-active' in (await h.locator('.billing-opt', has_text='Yearly').get_attribute('class')))
    check(ex, 'creator $120/year', (await creator.locator('.price').inner_text()).replace('\n', '') == '$120/year', await creator.locator('.price').inner_text())
    check(ex, 'creator note $10/mo', (await creator.locator('.price-note').inner_text()) == '$10/mo, billed yearly')
    check(ex, 'studio $290 and $24.17', (await plans.nth(2).locator('.amount').inner_text()) == '$290' and (await plans.nth(2).locator('.price-note').inner_text()) == '$24.17/mo, billed yearly')
    check(ex, 'hobby still Free, no note', (await plans.nth(0).locator('.price').inner_text()).strip() == 'Free' and await plans.nth(0).locator('.price-note').count() == 0)
    await creator.locator('.choose-btn').click()
    check(ex, 'creator selected', 'is-selected' in (await creator.get_attribute('class')) and (await creator.locator('.choose-btn').inner_text()) == 'Selected ✓')
    await plans.nth(2).locator('.choose-btn').click()
    check(ex, 'only one selected', await h.locator('.plan.is-selected').count() == 1 and 'is-selected' in (await plans.nth(2).get_attribute('class')))
    await creator.locator('.more-btn').click()
    check(ex, 'creator expanded to 7', await creator.locator('.features li').count() == 7 and (await creator.locator('.more-btn').inner_text()) == 'Show less')
    check(ex, 'studio still collapsed', await plans.nth(2).locator('.features li').count() == 3)
    await shot(page, ex)
    await creator.locator('.more-btn').click()
    check(ex, 'collapse back to 3', await creator.locator('.features li').count() == 3)
    await h.locator('.billing-opt', has_text='Monthly').click()
    check(ex, 'back to monthly', (await creator.locator('.amount').inner_text()) == '$12' and await creator.locator('.price-note').count() == 0)


async def t_dc13(page, h):
    ex = 'dc13'
    check(ex, '3 skeletons on first load', early.get(ex) == 3, early.get(ex))
    await page.wait_for_timeout(200)
    check(ex, '4 in-progress courses', await h.locator('.course-card').count() == 4)
    await h.locator('.tab', has_text='Completed').click()
    await page.wait_for_timeout(80)
    check(ex, 'skeletons on tab change', await h.locator('.skeleton-card').count() == 3)
    await page.wait_for_timeout(1400)
    check(ex, '2 completed', await h.locator('.course-card').count() == 2)
    await h.locator('.tab', has_text='Wishlist').click()
    await page.wait_for_timeout(1400)
    check(ex, 'empty state', 'No courses here yet' in (await h.locator('.state-panel').inner_text()) and await h.locator('.primary-btn', has_text='Browse catalog').count() == 1)
    await h.locator('.devbar input').check()
    await h.locator('.tab', has_text='In progress').click()
    await page.wait_for_timeout(1400)
    check(ex, 'error panel', await h.locator('.state-panel.is-error').count() == 1 and 'Couldn’t load your courses.' in (await h.locator('.state-panel').inner_text()))
    await shot(page, ex)
    await h.locator('.primary-btn', has_text='Retry').click()
    await page.wait_for_timeout(80)
    check(ex, 'retry shows skeletons', await h.locator('.skeleton-card').count() == 3)
    await page.wait_for_timeout(1400)
    check(ex, 'retry still failing -> error', await h.locator('.state-panel.is-error').count() == 1)
    await h.locator('.devbar input').uncheck()
    await page.wait_for_timeout(1400)
    check(ex, 'uncheck -> loads', await h.locator('.course-card').count() == 4)
    await h.locator('.devbar input').check()
    await page.wait_for_timeout(1400)
    await h.locator('.devbar input').uncheck()  # back to normal via retry path
    await page.wait_for_timeout(1400)
    # race: click Completed then In progress fast; result must be In progress (4)
    for _ in range(3):
        await h.locator('.tab', has_text='Completed').click()
        await h.locator('.tab', has_text='In progress').click()
        await page.wait_for_timeout(1400)
        if await h.locator('.course-card').count() != 4:
            break
    check(ex, 'fast tab switch shows the last tab', await h.locator('.course-card').count() == 4)


async def t_dc14(page, h):
    ex = 'dc14'
    check(ex, 'loading text until both requests finish', early.get(ex) == 1, early.get(ex))
    await page.wait_for_timeout(200)
    chips = h.locator('.chip')
    texts = [t.replace('\n', ' ').strip() for t in await chips.all_inner_texts()]
    check(ex, 'chips with counts', texts == ['All 12', 'Indoor plants 5', 'Pots 4', 'Plant care 3', 'Gift cards 0'], texts)
    check(ex, 'All active', 'is-active' in (await chips.nth(0).get_attribute('class')))
    check(ex, '12 products', await h.locator('.product').count() == 12)
    await h.locator('.chip', has_text='Pots').click()
    check(ex, 'Pots -> 4', await h.locator('.product').count() == 4)
    check(ex, 'Pots active only', await h.locator('.chip.is-active').count() == 1 and 'Pots' in (await h.locator('.chip.is-active').inner_text()))
    check(ex, 'Gift cards disabled', await h.locator('.chip', has_text='Gift cards').is_disabled())
    await shot(page, ex)
    await h.locator('.chip', has_text='Plant care').click()
    check(ex, 'Plant care -> 3', await h.locator('.product').count() == 3)
    await chips.nth(0).click()
    check(ex, 'All -> 12', await h.locator('.product').count() == 12)


async def first_desc(h):
    return (await h.locator('tbody tr').first.locator('.desc').inner_text()).strip()


async def t_dc15(page, h):
    ex = 'dc15'
    await page.wait_for_timeout(1200)
    check(ex, '10 rows', await h.locator('tbody tr').count() == 10)
    orig = await first_desc(h)
    check(ex, 'all arrows neutral', (await h.locator('.arrow').all_inner_texts()) == ['↕'] * 4)
    amount = h.locator('.sort-btn', has_text='Amount')
    await amount.click()
    check(ex, 'amount asc lowest first', await first_desc(h) == 'Gusto payroll', await first_desc(h))
    check(ex, 'amount asc arrow + aria', (await amount.locator('.arrow').inner_text()) == '▲' and await h.locator('th[aria-sort="ascending"]').count() == 1)
    await amount.click()
    check(ex, 'amount desc highest first', await first_desc(h) == 'Stripe payout')
    check(ex, 'amount desc arrow', (await amount.locator('.arrow').inner_text()) == '▼')
    await h.locator('.sort-btn', has_text='Date').click()
    check(ex, 'date asc earliest', await first_desc(h) == 'Amazon Web Services', await first_desc(h))
    check(ex, 'amount back to ↕', (await amount.locator('.arrow').inner_text()) == '↕')
    await h.locator('.sort-btn', has_text='Date').click()
    check(ex, 'date desc latest', await first_desc(h) == 'Acme Corp invoice #1042')
    await h.locator('.sort-btn', has_text='Description').click()
    descs = [t.strip() for t in await h.locator('tbody .desc').all_inner_texts()]
    check(ex, 'description asc alphabetical', descs == sorted(descs, key=str.lower), descs)
    await shot(page, ex)
    await h.locator('.sort-btn', has_text='Category').click()
    cats = [t.strip() for t in await h.locator('tbody .cat').all_inner_texts()]
    check(ex, 'category asc', cats == sorted(cats), cats)
    await h.locator('.sort-btn', has_text='Category').click()
    await h.locator('.sort-btn', has_text='Category').click()
    check(ex, 'change: third click clears to API order', await first_desc(h) == orig and (await h.locator('.arrow').all_inner_texts()) == ['↕'] * 4, await first_desc(h))


async def t_dc16(page, h):
    ex = 'dc16'
    await page.wait_for_timeout(1100)
    rng = h.locator('.range')
    check(ex, 'page1 range', (await rng.inner_text()) == 'Showing 1–5 of 23', await rng.inner_text())
    prev = h.locator('.pager-btn', has_text='Prev')
    nxt = h.locator('.pager-btn', has_text='Next')
    check(ex, 'prev disabled on 1', await prev.is_disabled() and not await nxt.is_disabled())
    check(ex, '5 page numbers', await h.locator('.page-num').count() == 5)
    await nxt.click()
    await page.wait_for_timeout(60)
    check(ex, 'old rows dimmed while loading', await h.locator('.table.is-loading').count() == 1 and await h.locator('tbody tr').count() == 5)
    await page.wait_for_timeout(1100)
    check(ex, 'page2 range', (await rng.inner_text()) == 'Showing 6–10 of 23', await rng.inner_text())
    check(ex, 'page2 first order #1118', (await h.locator('.order-no').first.inner_text()) == '#1118')
    check(ex, 'aria-current page 2', (await h.locator('.page-num[aria-current="page"]').inner_text()) == '2')
    await shot(page, ex)
    await h.locator('.page-num', has_text='5').click()
    await page.wait_for_timeout(1100)
    check(ex, 'last page range', (await rng.inner_text()) == 'Showing 21–23 of 23')
    check(ex, 'last page 3 rows', await h.locator('tbody tr').count() == 3)
    check(ex, 'next disabled at end', await nxt.is_disabled() and not await prev.is_disabled())
    await prev.click()
    await page.wait_for_timeout(1100)
    check(ex, 'prev -> page 4', (await rng.inner_text()) == 'Showing 16–20 of 23')


async def t_dc17(page, h):
    ex = 'dc17'
    email = h.locator('#email')
    pw = h.locator('#password')
    cf = h.locator('#confirm')
    await email.fill('bad')
    check(ex, 'no error while typing', await h.locator('.field-error').count() == 0)
    await pw.click()
    check(ex, 'email error after blur', (await h.locator('#email-error').inner_text()) == 'Enter a valid email address')
    check(ex, 'checklist 0 met', await h.locator('.rule').count() == 3 and await h.locator('.rule.is-met').count() == 0)
    await pw.fill('abcdefgh')
    check(ex, 'length met', await h.locator('.rule.is-met').count() == 1)
    await pw.fill('Abcdefg1')
    check(ex, 'all rules met', await h.locator('.rule.is-met').count() == 3)
    await cf.fill('Abcdefg2')
    await email.click()
    check(ex, 'confirm mismatch', (await h.locator('#confirm-error').inner_text()) == 'Passwords don’t match')
    await email.fill('')
    await pw.click()
    check(ex, 'email required', (await h.locator('#email-error').inner_text()) == 'Email is required')
    await h.locator('.submit').click()
    await page.wait_for_timeout(200)
    check(ex, 'invalid submit: errors shown, no API call', await h.locator('.field-error').count() == 2 and (await h.locator('.submit').inner_text()) == 'Create account')
    await email.fill('taken@example.com')
    await cf.fill('Abcdefg1')
    await h.locator('.submit').click()
    await page.wait_for_timeout(80)
    check(ex, 'Creating… disabled', (await h.locator('.submit').inner_text()) == 'Creating…' and await h.locator('.submit').is_disabled())
    await page.wait_for_timeout(1400)
    check(ex, 'API error banner', 'already exists' in (await h.locator('.api-error').inner_text()))
    check(ex, 'form kept', (await email.input_value()) == 'taken@example.com' and (await h.locator('.submit').inner_text()) == 'Create account')
    await shot(page, ex)
    await email.fill('jordan@kiln.io')
    await h.locator('.submit').click()
    await page.wait_for_timeout(1400)
    check(ex, 'success panel', 'Check your inbox' in (await h.locator('.success').inner_text()) and 'jordan@kiln.io' in (await h.locator('.success').inner_text()))


async def t_dc17_submit_invalid(page, h):
    ex = 'dc17'
    await h.locator('.submit').click()
    await page.wait_for_timeout(200)
    check(ex, 'submit empty shows all 3 errors, no API', await h.locator('.field-error').count() == 3 and (await h.locator('.submit').inner_text()) == 'Create account')


async def t_dc18(page, h):
    ex = 'dc18'
    await page.wait_for_timeout(1000)
    check(ex, 'empty prompt', 'Select a patient' in (await h.locator('.chart-pane').inner_text()))
    await h.locator('.patient-row', has_text='Daniel Reyes').click()
    await page.wait_for_timeout(60)
    check(ex, 'loading chart', 'Loading chart…' in (await h.locator('.chart-pane').inner_text()))
    check(ex, 'row selected', await h.locator('.patient-row.is-selected').count() == 1 and 'Daniel' in (await h.locator('.patient-row.is-selected').inner_text()))
    await page.wait_for_timeout(900)
    check(ex, 'Daniel chart', (await h.locator('.chart-name').inner_text()) == 'Daniel Reyes')
    check(ex, 'no known allergies', 'No known allergies' in (await h.locator('.chart-pane').inner_text()))
    check(ex, 'vitals 3', await h.locator('.vital').count() == 3)
    # race: Margaret (slow) then Daniel immediately
    ok = True
    for _ in range(3):
        await h.locator('.patient-row', has_text='Margaret Ellison').click()
        await page.wait_for_timeout(50)
        await h.locator('.patient-row', has_text='Daniel Reyes').click()
        await page.wait_for_timeout(900)
        n1 = await h.locator('.chart-name').inner_text() if await h.locator('.chart-name').count() else ''
        await page.wait_for_timeout(800)  # Margaret's slow response arrives in here
        n2 = await h.locator('.chart-name').inner_text() if await h.locator('.chart-name').count() else ''
        if n1 != 'Daniel Reyes' or n2 != 'Daniel Reyes':
            ok = False
            print('   race got', n1, n2)
    check(ex, 'stale Margaret response ignored', ok)
    await h.locator('.patient-row', has_text='Margaret Ellison').click()
    await page.wait_for_timeout(1700)
    check(ex, 'Margaret chart loads', (await h.locator('.chart-name').inner_text()) == 'Margaret Ellison' and 'Penicillin' in (await h.locator('.chart-pane').inner_text()))
    await shot(page, ex)


async def t_dc19(page, h):
    ex = 'dc19'
    toasts = h.locator('.toast')
    await h.locator('.btn', has_text='Clear cache').click()
    await page.wait_for_timeout(100)
    check(ex, 'cache toast', await toasts.count() == 1 and 'Cache cleared for api-gateway' in (await toasts.first.inner_text()))
    await h.locator('.btn', has_text='Deploy to staging').click()
    await page.wait_for_timeout(1000)
    check(ex, 'deploy success toast', await h.locator('.toast.is-success', has_text='to staging').count() == 1)
    await h.locator('.btn', has_text='Roll back production').click()
    await page.wait_for_timeout(1000)
    check(ex, 'rollback error toast', await h.locator('.toast.is-error', has_text='change freeze').count() == 1)
    await shot(page, ex)
    # cache toast (oldest, ~2.1s old) should be gone by ~3.2s
    await page.wait_for_timeout(1200)
    # deploy toast's age depends on the API delay, so only assert the deterministic ends
    check(ex, 'oldest auto-dismissed, newest remains', await h.locator('.toast', has_text='Cache cleared').count() == 0 and await h.locator('.toast.is-error').count() == 1, await toasts.count())
    await h.locator('.toast.is-error .toast-close').click()
    check(ex, 'manual close', await h.locator('.toast.is-error').count() == 0)
    await page.wait_for_timeout(2200)
    check(ex, 'all auto-dismissed', await toasts.count() == 0)
    for _ in range(4):
        await h.locator('.btn', has_text='Clear cache').click()
        await page.wait_for_timeout(150)
    check(ex, 'change: max 3 toasts', await toasts.count() == 3, await toasts.count())
    await page.wait_for_timeout(3300)
    check(ex, 'capped toasts all dismiss', await toasts.count() == 0)
    await h.locator('.btn', has_text='Clear cache').click()
    await page.wait_for_timeout(1500)
    await h.locator('.btn', has_text='Clear cache').click()
    await page.wait_for_timeout(100)
    await toasts.nth(1).locator('.toast-close').click()
    await page.wait_for_timeout(1650)  # first toast is now ~3.25 s old
    check(ex, 'closing one does not reset the other timer', await toasts.count() == 0, await toasts.count())


async def t_dc20(page, h):
    ex = 'dc20'
    await page.wait_for_timeout(1100)
    rows = h.locator('.file-row')
    check(ex, '6 files', await rows.count() == 6)
    await rows.nth(0).locator('.icon-btn').click()
    check(ex, 'modal names file', (await h.locator('.modal-title').inner_text()) == 'Delete “Q3 roadmap.pdf”?')
    check(ex, 'alertdialog role + aria-modal', await h.locator('[role="alertdialog"][aria-modal="true"]').count() == 1)
    focused = await h.locator('.modal .btn-secondary').evaluate('el => el.getRootNode().activeElement === el')
    check(ex, 'focus starts on Cancel', focused)
    await h.locator('.modal-text').click()
    check(ex, 'inside click keeps', await h.locator('.modal').count() == 1)
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(100)
    check(ex, 'escape closes', await h.locator('.modal').count() == 0)
    await rows.nth(1).locator('.icon-btn').click()
    await h.locator('.btn', has_text='Cancel').click()
    check(ex, 'cancel closes', await h.locator('.modal').count() == 0 and await rows.count() == 6)
    await rows.nth(1).locator('.icon-btn').click()
    await h.locator('.backdrop').click(position={'x': 5, 'y': 5})
    check(ex, 'backdrop closes', await h.locator('.modal').count() == 0)
    await rows.nth(2).locator('.icon-btn').click()
    await shot(page, ex)
    await h.locator('.btn-danger').click()
    await page.wait_for_timeout(60)
    check(ex, 'Deleting… + disabled', (await h.locator('.btn-danger').inner_text()) == 'Deleting…' and await h.locator('.modal .btn-secondary').is_disabled())
    await page.keyboard.press('Escape')
    check(ex, 'escape ignored while deleting', await h.locator('.modal').count() == 1)
    await page.wait_for_timeout(1200)
    names = await h.locator('.file-name').all_inner_texts()
    check(ex, 'row removed + modal closed', await rows.count() == 5 and 'Offsite agenda.docx' not in names and await h.locator('.modal').count() == 0, names)


TESTS = [('dc11', t_dc11), ('dc12', t_dc12), ('dc13', t_dc13), ('dc14', t_dc14), ('dc15', t_dc15), ('dc16', t_dc16),
         ('dc17', t_dc17), ('dc17', t_dc17_submit_invalid), ('dc18', t_dc18), ('dc19', t_dc19), ('dc20', t_dc20)]


async def main():
    env = dict(os.environ, DIST_HTML=DIST)
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)], env=env)
    time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page = await b.new_page(viewport={'width': 1600, 'height': 950})
            errs = []
            page.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
            page.on('console', lambda m: m.type in ('error', 'warning') and errs.append(m.type + ': ' + m.text[:300]))

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
            for ex, fn in TESTS:
                if ONLY and ex not in ONLY:
                    continue
                errs.clear()
                h = await open_design(page, ex)
                try:
                    await fn(page, h)
                except Exception as e:  # noqa: BLE001
                    check(ex, fn.__name__ + ' crashed', False, repr(e)[:300])
                check(ex, 'no console errors/warnings', not errs, errs[:3])
                await close(page)
            await b.close()
    finally:
        srv.terminate()
    fails = [r for r in results if not r[2]]
    print(f'\n{len(results) - len(fails)}/{len(results)} checks passed')
    if fails:
        sys.exit(1)

asyncio.run(main())
