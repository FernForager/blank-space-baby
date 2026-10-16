"""Render every screen of the game at three phone sizes.

    python3 tools/screens.py            # writes PNGs to out/

Screens: select, q (question), win (right answer), clear (a pentagon flying in),
select2 (after a win), miss (wrong answer), select_all and boss (all five beaten).
Prints a line for any screen that scrolls or throws a JS error.
Uses Playwright's Chromium. If Google Fonts can't load in the sandbox, install
Press Start 2P and Pixelify Sans into ~/.fonts (from github.com/google/fonts) so the
pixel fonts render.
"""
import asyncio, os
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(ROOT, 'docs', 'index.html')).read()
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)
SIZES = [(402, 744), (375, 667), (320, 568)]   # iPhone 17 in the Claude viewer, iPhone SE 2/3, iPhone SE 1

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for W, H in SIZES:
            ctx = await b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=3)
            pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.route('http://bsb.test/', lambda r: r.fulfill(body=HTML, content_type='text/html'))
            await pg.goto('http://bsb.test/'); await pg.wait_for_timeout(1500)
            async def shot(n):
                sh = await pg.evaluate("[document.documentElement.scrollHeight, innerHeight]")
                if sh[0] > sh[1]: print(W, H, n, 'SCROLLS', sh)
                await pg.screenshot(path=os.path.join(OUT, f'{W}_{n}.png'))
            await pg.wait_for_timeout(300); await shot('select')
            await pg.click('#t-swift'); await pg.wait_for_timeout(400); await shot('q')
            for i in range(5):
                w = await pg.evaluate("document.getElementById('q').dataset.w")
                await pg.click(f'.choice[data-w="{w}"]'); await pg.wait_for_timeout(350)
                if i == 1: await shot('win')
                await pg.click('#flip'); await pg.wait_for_timeout(300)
            await shot('clear')
            await pg.click('#flip'); await pg.wait_for_timeout(1100); await shot('select2')
            await pg.click('#t-epl'); await pg.wait_for_timeout(300)
            wrong = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w).find(x => x !== document.getElementById('q').dataset.w)")
            await pg.click(f'.choice[data-w="{wrong}"]'); await pg.wait_for_timeout(500); await shot('miss')
            await pg.evaluate("localStorage.setItem('bsb-cleared', JSON.stringify(['alpha','parents','soccer','swift','epl']))")
            await pg.reload(); await pg.wait_for_timeout(1200); await shot('select_all')
            await pg.click('#flip'); await pg.wait_for_timeout(400); await shot('boss')
            if errs: print(W, H, 'JS ERRORS', errs)
            await ctx.close()
        await b.close()
    print('screens in', OUT)
asyncio.run(main())
