import asyncio, subprocess, sys, time, pathlib, json
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
import os
PORT = int(os.environ.get('PORT', '8765'))
SHIM = """
window.Babel = { transform(src, opts) {
  const x = new XMLHttpRequest();
  x.open('POST', '/transform?f=' + encodeURIComponent(opts.filename), false);
  x.send(src);
  if (x.status !== 200) { const e = new SyntaxError(opts.filename + ': ' + x.responseText); throw e; }
  return { code: x.responseText };
} };
"""


async def main():
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)])
    time.sleep(0.8)
    errors = []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page = await b.new_page(viewport={'width': 1440, 'height': 900})
            page.on('pageerror', lambda e: errors.append('pageerror: ' + str(e)))
            page.on('console', lambda m: m.type == 'error' and errors.append('console: ' + m.text[:300]))

            async def route(r):
                u = r.request.url
                if 'react-dom' in u:
                    await r.fulfill(body='/* reactdom in bundle */', content_type='text/javascript')
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
            await page.wait_for_timeout(800)
            await page.screenshot(path=str(ROOT / 'guide.png'))
            # visit every module
            mods = await page.evaluate('MODULES.map(m => m.id)')
            for m in mods:
                await page.evaluate(f'Guide.show("{m}")')
            await page.evaluate('Guide.show("css")')
            await page.screenshot(path=str(ROOT / 'guide-css.png'), full_page=False)
            print('guide errors so far:', errors)

            report = {}
            for ex in json.loads(sys.argv[1]) if len(sys.argv) > 1 else await page.evaluate('Object.keys(EXERCISES)'):
                errors.clear()
                await page.evaluate(f'Workspace.open("{ex}")')
                await page.wait_for_timeout(1600)
                term = await page.inner_text('#termView')
                ov = await page.evaluate("!document.getElementById('errOverlay').hidden")
                cons = await page.inner_text('#consoleView')
                starter = {'compiled': 'Compiled successfully' in term.split('Compiling...')[-1], 'overlay': ov, 'console': cons[:200]}
                await page.screenshot(path=str(ROOT / 'shots' / f'{ex}-starter.png'))
                # load solution
                await page.click('[data-ptab="solution"]')
                await page.click('#revealSol')
                await page.click('#loadSol')
                await page.click('#loadSol')
                await page.wait_for_timeout(1800)
                term = await page.inner_text('#termView')
                ov = await page.evaluate("!document.getElementById('errOverlay').hidden")
                ovtext = await page.inner_text('#errOverlay') if ov else ''
                cons = await page.inner_text('#consoleView')
                sol = {'compiled': 'Compiled successfully' in term.split('Compiling...')[-1], 'overlay': ovtext[:300], 'console': cons[:300]}
                await page.screenshot(path=str(ROOT / 'shots' / f'{ex}-solution.png'))
                await page.click('[data-ptab="design"]')
                await page.wait_for_timeout(1500)
                await page.screenshot(path=str(ROOT / 'shots' / f'{ex}-design.png'))
                # reset workspace for future runs
                await page.click('#resetBtn'); await page.click('#resetBtn')
                await page.click('[data-ptab="task"]')
                await page.evaluate('Workspace.close()')
                report[ex] = {'starter': starter, 'solution': sol, 'errors': list(errors)}
            for k, v in report.items():
                print(k, json.dumps(v)[:900])
            await b.close()
    finally:
        srv.terminate()

asyncio.run(main())
