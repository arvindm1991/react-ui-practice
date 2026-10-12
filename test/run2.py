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
            page = await ctx.new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))

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

            # 1. open d3 from guide card click
            await page.evaluate('Guide.show("react")')
            await page.click('[data-open="d3"]')
            await page.wait_for_timeout(1200)
            # syntax error
            await page.fill('#code-editor', "import React from 'react';\nexport default function App() {\n  return <div>\n}\n")
            await page.wait_for_timeout(1500)
            out.append(('syntax overlay', await page.inner_text('#errOverlay')))
            await page.screenshot(path=str(ROOT / 'x-syntax.png'))
            # runtime error
            await page.fill('#code-editor', "import React from 'react';\nexport default function App() {\n  const x = undefined;\n  return <div>{x.map(a => a)}</div>;\n}\n")
            await page.wait_for_timeout(1500)
            out.append(('runtime overlay', (await page.inner_text('#errOverlay'))[:200]))
            # key warning + console.log
            await page.fill('#code-editor', "import React from 'react';\nexport default function App() {\n  console.log('hello', { a: 1 });\n  return <ul>{['a','b'].map(a => <li>{a}</li>)}</ul>;\n}\n")
            await page.wait_for_timeout(1500)
            await page.click('[data-btab="console"]')
            out.append(('console', await page.inner_text('#consoleView')))
            out.append(('overlay hidden', await page.evaluate("document.getElementById('errOverlay').hidden")))
            # editor keys: type in editor
            await page.fill('#code-editor', '')
            await page.focus('#code-editor')
            await page.keyboard.type('function A() {')
            await page.keyboard.press('Enter')
            await page.keyboard.type('return 1;')
            out.append(('typed', await page.input_value('#code-editor')))
            # reset
            await page.click('#resetBtn'); await page.click('#resetBtn')
            await page.wait_for_timeout(1200)

            # 2. design inspect, expanded
            await page.click('[data-ptab="design"]')
            await page.wait_for_timeout(1200)
            await page.click('#wideBtn')
            await page.wait_for_timeout(400)
            box = await page.locator('#designCanvas').bounding_box()
            await page.mouse.move(box['x'] + 120, box['y'] + 95)
            await page.wait_for_timeout(300)
            out.append(('inspect', (await page.inner_text('#inspectInfo'))[:300]))
            await page.screenshot(path=str(ROOT / 'x-inspect.png'))
            await page.click('#wideBtn')
            await page.evaluate('Workspace.close()')

            # 3. mock change reveal + speed run
            await page.evaluate('Workspace.open("m1")')
            await page.wait_for_timeout(1200)
            await page.click('#revealChange')
            out.append(('change', (await page.inner_text('#changeBox'))[:120]))
            await page.click('#timerLen')
            out.append(('timer len', await page.inner_text('#timerLen'), await page.inner_text('#timerVal')))
            await page.screenshot(path=str(ROOT / 'x-m1-task.png'))
            await page.evaluate('Workspace.close()')
            await page.evaluate('Workspace.open("d9", { speed: true })')
            await page.wait_for_timeout(1200)
            out.append(('speed term', (await page.inner_text('#termView'))[-120:]))
            out.append(('speed tabs', await page.inner_text('#fileTabs')))
            # new file
            await page.click('#newFileBtn')
            await page.fill('#newFileInput', 'hooks/useDebounce.js')
            await page.press('#newFileInput', 'Enter')
            await page.wait_for_timeout(300)
            out.append(('tree', await page.inner_text('#tree')))
            await page.evaluate('Workspace.close()')

            # 4. modal solution renders within preview
            await page.evaluate('Workspace.open("d7")')
            await page.wait_for_timeout(800)
            await page.click('[data-ptab="solution"]'); await page.click('#revealSol'); await page.click('#loadSol'); await page.click('#loadSol')
            await page.wait_for_timeout(1500)
            await page.evaluate("""() => { const h = document.getElementById('previewHost').shadowRoot; h.querySelector('.btn').click(); }""")
            await page.wait_for_timeout(400)
            await page.screenshot(path=str(ROOT / 'x-modal.png'))
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(200)
            out.append(('modal closed by esc', await page.evaluate("!document.getElementById('previewHost').shadowRoot.querySelector('.backdrop')")))
            await page.click('#resetBtn'); await page.click('#resetBtn')
            await page.evaluate('Workspace.close()')

            # 5. phone + dark
            m = await b.new_context(viewport={'width': 390, 'height': 800}, color_scheme='dark')
            mp = await m.new_page()
            await mp.route('**/*', route)
            await mp.goto(f'http://127.0.0.1:{PORT}/#figma')
            await mp.wait_for_timeout(600)
            await mp.screenshot(path=str(ROOT / 'x-phone-dark.png'))
            sw = await mp.evaluate('document.documentElement.scrollWidth')
            out.append(('phone scrollWidth', sw))
            await mp.evaluate('Workspace.open("d3")')
            await mp.wait_for_timeout(1200)
            await mp.click('[data-view-btn="preview"]')
            await mp.screenshot(path=str(ROOT / 'x-phone-ide.png'))
            out.append(('errors', errs))
            await b.close()
    finally:
        srv.terminate()
    for o in out:
        print(o)

asyncio.run(main())
