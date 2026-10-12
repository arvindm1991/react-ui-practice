import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright
sys.path.insert(0,'.')
from run4 import SHIM
async def main():
    srv = subprocess.Popen([sys.executable, 'server.py', '8770']); time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            pg = await b.new_page(viewport={'width':1280,'height':900})
            errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
            async def route(r):
                u=r.request.url
                if 'react-dom' in u: await r.fulfill(body='', content_type='text/javascript')
                elif 'react' in u: await r.fulfill(path='react-bundle.js', content_type='text/javascript')
                elif 'babel' in u: await r.fulfill(body=SHIM, content_type='text/javascript')
                elif 'fonts.g' in u: await r.fulfill(body='', content_type='text/css')
                else: await r.continue_()
            await pg.route('**/*', route)
            await pg.goto('http://127.0.0.1:8770/#pipeline'); await pg.wait_for_timeout(600)
            pl = pg.locator('.play').first
            await pl.scroll_into_view_if_needed(); await pg.wait_for_timeout(1500)
            print('pipeline console:', await pl.locator('.play-console').inner_text())
            print('pipeline status:', await pl.locator('.play-status').inner_text())
            await pg.screenshot(path='pipe.png', full_page=True)
            await pg.evaluate('Guide.show("katas")'); await pg.wait_for_timeout(400)
            n = await pg.locator('.kata').count()
            res=[]
            for i in range(n):
                k = pg.locator('.kata').nth(i)
                await k.locator('.kata-sol').click()
                code = await k.locator('.kata-solcode').inner_text()
                await k.locator('textarea').fill(code)
                await k.locator('.kata-run').click()
                v = await k.locator('.kata-verdict').inner_text()
                res.append((await k.locator('h3').inner_text(), v))
                if 'Correct' not in v:
                    print('---', code, '\n>>', await k.locator('.kata-yours').inner_text())
            for r in res: print(r)
            # mutation check: sort in place
            k = pg.locator('.kata').nth(5)
            await k.locator('textarea').fill("return orders.sort((a,b)=>b.amount-a.amount).map(o=>o.id);")
            await k.locator('.kata-run').click()
            print('mutation:', await k.locator('.kata-verdict').inner_text())
            k = pg.locator('.kata').nth(1)
            await k.locator('textarea').fill("people.map(p => p.name)")
            await k.locator('.kata-run').click()
            print('no return:', await k.locator('.kata-verdict').inner_text(), '|', await k.locator('.kata-shape-yours').inner_text())
            await pg.screenshot(path='katas.png', clip={'x':0,'y':0,'width':1280,'height':1600}, full_page=True)
            print('errors', errs)
            await b.close()
    finally: srv.terminate()
asyncio.run(main())
