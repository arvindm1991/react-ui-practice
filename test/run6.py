import asyncio, subprocess, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).parent
PORT = 8767
SHIM = open(ROOT/'run.py').read().split('SHIM = """')[1].split('"""')[0]
async def main():
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)]); time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page = await b.new_page(viewport={'width': 1600, 'height': 950})
            errs=[]; page.on('pageerror', lambda e: errs.append(str(e)))
            async def route(r):
                u = r.request.url
                if 'react-dom' in u: await r.fulfill(body='', content_type='text/javascript')
                elif 'react' in u: await r.fulfill(path=str(ROOT / 'react-bundle.js'), content_type='text/javascript')
                elif 'babel' in u: await r.fulfill(body=SHIM, content_type='text/javascript')
                elif 'fonts.g' in u: await r.fulfill(body='', content_type='text/css')
                else: await r.continue_()
            await page.route('**/*', route)
            await page.goto(f'http://127.0.0.1:{PORT}/'); await page.wait_for_timeout(600)
            await page.evaluate('Workspace.open("m4")'); await page.wait_for_timeout(1200)
            await page.screenshot(path=str(ROOT/'m4-task.png'))
            await page.click('[data-ptab="design"]'); await page.wait_for_timeout(1800)
            host = page.locator('#designHost')
            await page.click('[data-dmode="interact"]')
            print('sub:', await host.locator('.keys-sub').inner_text())
            btn = host.locator('button.btn-primary')
            print('disabled empty:', await btn.is_disabled())
            await host.locator('input.input').fill('CI runner')
            await btn.click(); await page.wait_for_timeout(150)
            print('during:', await btn.inner_text(), await btn.is_disabled())
            await page.wait_for_timeout(900)
            print('sub after create:', await host.locator('.keys-sub').inner_text())
            print('first row:', await host.locator('tbody tr').first.inner_text())
            print('banner:', await host.locator('.secret-banner').count())
            await host.locator('.btn-danger').first.click(); await page.wait_for_timeout(200)
            print('sub after revoke:', await host.locator('.keys-sub').inner_text())
            await host.locator('.toggle input').check(); await page.wait_for_timeout(200)
            print('rows hide revoked:', await host.locator('tbody tr').count())
            await page.screenshot(path=str(ROOT/'m4-design.png'))
            await host.locator('.secret-banner button').click(); await page.wait_for_timeout(200)
            print('banner after done:', await host.locator('.secret-banner').count())
            print('errs', errs)
            await b.close()
    finally: srv.terminate()
asyncio.run(main())
