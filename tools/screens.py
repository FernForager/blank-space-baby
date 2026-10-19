"""Render the daily's screens at three phone sizes.

    python3 tools/screens.py [page.html]       # default docs/index.html, writes PNGs to out/

For each size: board (a fresh day), q (a card open), win (a right answer),
board3 (three panels lit), miss (a wrong answer), end (14/15) and hat (a perfect day, GOLAZO!).
Prints a line for any screen that scrolls or throws a JS error, and any card that spills out of the panel.
Uses Playwright's Chromium. The fonts come from docs/fonts, as on the site.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
from docsroute import route   # the page plus docs/fonts
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'index.html')).read()
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)
SIZES = [(402, 744), (375, 667), (320, 568)]   # iPhone 17 in the Claude viewer, iPhone SE 2/3, iPhone SE 1
FONTS = """() => { const t = [...document.querySelectorAll('#p-board .tile')], p = document.getElementById('p-board').getBoundingClientRect();
  return t.filter(e => { const r = e.getBoundingClientRect(); return r.right > p.right + .5 || r.bottom > p.bottom + .5; }).length; }"""

async def tap(pg, sel):   # a tile tap
    await pg.click(sel)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for W, H in SIZES:
            ctx = await b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=3)
            pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script("try { localStorage.setItem('bsb-intro-off', 'true') } catch (e) {}")   # skip the how-to-play screen
            await pg.route('http://bsb.test/**', route(HTML))
            url = 'http://bsb.test/?day=1'
            async def shot(n):
                sh = await pg.evaluate("[document.documentElement.scrollHeight, innerHeight]")
                if sh[0] > sh[1]: print(W, H, n, 'SCROLLS', sh)
                await pg.screenshot(path=os.path.join(OUT, f'{W}_{n}.png'))
            async def right(i, wait=1100):
                await tap(pg, f'[data-i="{i}"]'); await pg.wait_for_timeout(350)
                w = await pg.evaluate("document.getElementById('q').dataset.w")
                await pg.click(f'.choice[data-w="{w}"]'); await pg.wait_for_timeout(350)
            await pg.goto(url + '&reset'); await pg.wait_for_timeout(1500)
            await shot('board')
            f = await pg.evaluate(FONTS)
            if f: print(W, H, f, 'cards spill out of the panel')
            await tap(pg, '[data-i="0"]'); await pg.wait_for_timeout(400); await shot('q')
            w = await pg.evaluate("document.getElementById('q').dataset.w")
            await pg.click(f'.choice[data-w="{w}"]'); await pg.wait_for_timeout(400); await shot('win')
            await pg.click('#flip'); await pg.wait_for_timeout(1100)
            for i in (5, 10):
                await right(i); await pg.click('#flip'); await pg.wait_for_timeout(600)
            await shot('board3')
            await tap(pg, '[data-i="1"]'); await pg.wait_for_timeout(350)
            wrong = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w).find(x => x !== document.getElementById('q').dataset.w)")
            await pg.click(f'.choice[data-w="{wrong}"]'); await pg.wait_for_timeout(500); await shot('miss')
            await pg.click('#flip'); await pg.wait_for_timeout(600)
            for i in (2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14):
                await right(i); await pg.click('#flip'); await pg.wait_for_timeout(300)
            await pg.wait_for_timeout(1500); await shot('end')
            await pg.reload(); await pg.wait_for_timeout(1200)
            if await pg.evaluate("document.getElementById('cab').dataset.v") != 'end': print(W, H, 'a finished day did not reopen to the end')
            await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('bsb-daily')); s.res = s.res.map(() => 1); s.open = -1; localStorage.setItem('bsb-daily', JSON.stringify(s)); }")
            await pg.reload(); await pg.wait_for_timeout(1200); await shot('hat')
            if errs: print(W, H, 'JS ERRORS', errs)
            await ctx.close()
        await b.close()
    print('screens in', OUT)
asyncio.run(main())
