import asyncio, subprocess, sys, time, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
PORT = 8766
SHIM = """
window.Babel = { transform(src, opts) {
  const x = new XMLHttpRequest();
  x.open('POST', '/transform?f=' + encodeURIComponent(opts.filename), false);
  x.send(src);
  if (x.status !== 200) { throw new SyntaxError(opts.filename + ': ' + x.responseText); }
  return { code: x.responseText };
} };
"""
LESSONS = ['css', 'flex', 'layout', 'react', 'state', 'events', 'effects', 'structure', 'data']


async def main():
    srv = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), str(PORT)])
    time.sleep(0.8)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
            page = await b.new_page(viewport={'width': 1440, 'height': 900})
            errs = []
            page.on('pageerror', lambda e: errs.append('pageerror ' + str(e)))

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
            for m in LESSONS:
                await page.evaluate(f'Guide.show("{m}")')
                n = await page.locator('.play').count()
                for i in range(n):
                    await page.locator('.play').nth(i).scroll_into_view_if_needed()
                    await page.wait_for_timeout(250)
                await page.wait_for_timeout(1200)
                res = await page.evaluate("""() => [...document.querySelectorAll('.play')].map(p => ({
                  title: p.querySelector('.play-title').textContent,
                  status: p.querySelector('.play-status').textContent,
                  msg: p.querySelector('.play-msg').hidden ? '' : p.querySelector('.play-msg').textContent.slice(0, 160),
                  cons: [...p.querySelectorAll('.play-console > div')].map(d => d.className + ':' + d.textContent).join(' | ').slice(0, 300),
                  h: p.querySelector('.play-host').getBoundingClientRect().height,
                  sh: p.querySelector('.play-host').scrollHeight,
                }))""")
                print('==', m, 'playgrounds:', n, 'explorers:', await page.locator('.explorer').count(), 'quiz:', await page.locator('.q').count())
                for r in res:
                    flag = '!!' if ('err' in r['status'].lower() or r['msg'] or 'pc-error' in r['cons'] or 'pc-warn' in r['cons']) else 'ok'
                    print('  ', flag, r['title'], '|', r['status'], '| h', round(r['h']), 'sh', r['sh'], '|', r['msg'], '|', r['cons'][:220])
                await page.screenshot(path=str(ROOT / f'L-{m}.png'), full_page=True)
            # interactions: counter click, key bug
            await page.evaluate('Guide.show("state")')
            pl = page.locator('.play').nth(1)
            await pl.scroll_into_view_if_needed(); await page.wait_for_timeout(800)
            await pl.locator('.play-host button').first.click()
            await page.wait_for_timeout(200)
            print('counter text:', await pl.locator('.play-host p').inner_text(), '| console:', await pl.locator('.play-console').inner_text())
            # edit code
            ta = pl.locator('textarea')
            await ta.click()
            await page.keyboard.press('Control+End')
            await page.keyboard.type('\n// edit')
            await page.wait_for_timeout(1500)
            print('after edit status:', await pl.locator('.play-status').inner_text())
            # form submit guard
            await page.evaluate('Guide.show("events")')
            fp = page.locator('.play').nth(2)
            await fp.scroll_into_view_if_needed(); await page.wait_for_timeout(800)
            await fp.locator('.play-host input').fill('you@acme.dev')
            await fp.locator('.play-host input').press('Enter')
            await page.wait_for_timeout(1200)
            print('invited list:', await fp.locator('.play-host ul').inner_text())
            print('url still', page.url)
            print('errors', errs)
            await b.close()
    finally:
        srv.terminate()

if __name__ == "__main__":
    asyncio.run(main())
