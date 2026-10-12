import asyncio, subprocess, sys, time, pathlib
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from run import SHIM, ROOT, PORT


async def main():
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)])
    time.sleep(0.8)
    out = []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            ctx = await b.new_context(viewport={'width': 1440, 'height': 900})
            await ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
            page = await ctx.new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            page.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:200]))

            async def route(r):
                u = r.request.url
                if 'react-dom' in u: await r.fulfill(body='', content_type='text/javascript')
                elif 'react' in u: await r.fulfill(path=str(ROOT / 'react-bundle.js'), content_type='text/javascript')
                elif 'babel' in u: await r.fulfill(body=SHIM, content_type='text/javascript')
                elif 'fonts.g' in u: await r.fulfill(body='', content_type='text/css')
                else: await r.continue_()
            await page.route('**/*', route)
            await page.goto(f'http://127.0.0.1:{PORT}/')
            await page.wait_for_timeout(500)
            for m in ['lookup', 'vocab', 'names']:
                await page.evaluate(f'Guide.show("{m}")')
                await page.wait_for_timeout(150)
                await page.screenshot(path=str(ROOT / f'l-{m}.png'), full_page=(m != 'names'))
            # vocab interactions
            await page.evaluate('Guide.show("vocab")')
            await page.fill('#vocabFilter', 'scroll')
            out.append(('vocab rows for scroll', await page.locator('.vocab-table tr').count()))
            await page.check('#vocabHide')
            out.append(('hidden names', await page.locator('.vocab-name.is-hidden').count()))
            # lookup drill
            await page.evaluate('Guide.show("names")')
            await page.fill('#ldAns', 'click outside, ref contains')
            await page.click('[data-act="reveal"]')
            await page.wait_for_timeout(100)
            await page.screenshot(path=str(ROOT / 'l-names-revealed.png'), full_page=True)
            await page.click('[data-grade="part"]')
            out.append(('after grade', await page.inner_text('.ld-stats')))
            await page.click('[data-act="timer"]')
            await page.wait_for_timeout(2100)
            out.append(('clock', await page.inner_text('.ld-clock')))
            await page.click('[data-act="missed"]')
            out.append(('missed first prompt', (await page.inner_text('.ld-prompt'))[:60]))
            # snippets lang check: go through all scenarios revealing
            for i in range(24):
                await page.click('[data-act="reveal"]')
                await page.click('[data-act="next"]')
            out.append(('cycled ok', True))

            # curveball c1 solution: click-outside & copy
            await page.evaluate('Workspace.open("c1")')
            await page.wait_for_timeout(1200)
            await page.screenshot(path=str(ROOT / 'c1-task.png'))
            await page.fill('#lookupPlan', 'relative time -> Intl.RelativeTimeFormat')
            await page.click('[data-ptab="solution"]'); await page.click('#revealSol'); await page.click('#loadSol'); await page.click('#loadSol')
            await page.wait_for_timeout(1800)
            ev = lambda js: page.evaluate("() => { const r = document.getElementById('previewHost').shadowRoot; " + js + " }")
            out.append(('times', await ev("return [...r.querySelectorAll('.time')].map(t => t.textContent)")))
            # open menu on first comment via real mouse clicks
            btn = page.locator('#previewHost [aria-label="More actions"]').first
            await btn.click()
            await page.wait_for_timeout(150)
            out.append(('menu open', await ev("return !!r.querySelector('.menu')")))
            # click inside menu item -> delete should work
            await page.locator('#previewHost .menu .danger').click()
            await page.wait_for_timeout(150)
            out.append(('comments after delete', await ev("return r.querySelectorAll('.comment').length")))
            await btn.click()
            await page.wait_for_timeout(100)
            await page.locator('#previewHost h1').click()
            await page.wait_for_timeout(150)
            out.append(('menu closed by outside click', await ev("return !r.querySelector('.menu')")))
            await btn.click()
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(150)
            out.append(('menu closed by Esc', await ev("return !r.querySelector('.menu')")))
            await page.locator('#previewHost .ghost-btn', has_text='Copy link').first.click()
            await page.wait_for_timeout(200)
            out.append(('copied label', await ev("return [...r.querySelectorAll('.ghost-btn')].map(b=>b.textContent).filter(t=>t.includes('Copied')).length")))
            ta = page.locator('#previewHost .composer-input')
            await ta.click()
            await page.keyboard.type('Line one\nline two\nline three\nline four')
            await page.wait_for_timeout(200)
            out.append(('ta height', await ev("return r.querySelector('.composer-input').style.height")))
            await page.keyboard.press('Control+Enter')
            await page.wait_for_timeout(300)
            out.append(('comments after post', await ev("return r.querySelectorAll('.comment').length")))
            await page.screenshot(path=str(ROOT / 'c1-solution.png'))
            await page.click('#resetBtn'); await page.click('#resetBtn')
            await page.evaluate('Workspace.close()')

            # c2
            await page.evaluate('Workspace.open("c2")')
            await page.wait_for_timeout(1000)
            await page.click('[data-ptab="solution"]'); await page.click('#revealSol'); await page.click('#loadSol'); await page.click('#loadSol')
            await page.wait_for_timeout(1800)
            await page.locator('#previewHost .sort-btn', has_text='Version').click()
            await page.wait_for_timeout(100)
            out.append(('versions asc', await ev("return [...r.querySelectorAll('tbody td code')].map(c=>c.textContent).join(' ')")))
            await page.locator('#previewHost tbody input').nth(1).click()
            await page.wait_for_timeout(100)
            out.append(('indeterminate', await ev("return r.querySelector('thead input').indeterminate")))
            await page.evaluate("() => { document.getElementById('previewHost').shadowRoot.querySelector('.table-scroll').scrollTop = 200 }")
            await page.wait_for_timeout(100)
            await page.screenshot(path=str(ROOT / 'c2-solution.png'))
            await page.click('#resetBtn'); await page.click('#resetBtn')
            await page.evaluate('Workspace.close()')
            await page.evaluate('Guide.show("plan")')
            await page.screenshot(path=str(ROOT / 'l-plan.png'), full_page=True)
            out.append(('errors', errs))
            await b.close()
    finally:
        srv.terminate()
    for o in out:
        print(o)

asyncio.run(main())
