"""Render the daily's screens at three phone sizes.

    python3 tools/screens.py [page.html]       # default docs/index.html, writes PNGs to out/

For each size: board (a fresh day), q (a card open), win (a right answer),
board3 (three chips in), goal (the sixth chip landing), board6 (a goal banked), miss (a wrong answer),
end (the end of the day) and hat (a perfect day).
Prints a line for any screen that scrolls or throws a JS error, the smallest hook font on each board,
and any hook that still overflows its tile.
Uses Playwright's Chromium. If Google Fonts can't load in the sandbox, install Press Start 2P and
Pixelify Sans into ~/.fonts (from raw.githubusercontent.com/google/fonts) so the pixel fonts render.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'index.html')).read()
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)
SIZES = [(402, 744), (375, 667), (320, 568)]   # iPhone 17 in the Claude viewer, iPhone SE 2/3, iPhone SE 1
FONTS = """() => { const h = [...document.querySelectorAll('.hk')]; if (!h.length) return null;
  return { min: Math.min(...h.map(e => parseFloat(getComputedStyle(e).fontSize))), max: Math.max(...h.map(e => parseFloat(getComputedStyle(e).fontSize))),
           over: h.filter(e => e.scrollWidth > e.clientWidth + 0.5).map(e => e.textContent) }; }"""

async def tap(pg, sel):   # a tile tap: the day's first tile asks for a second tap
    await pg.click(sel)
    if await pg.evaluate("document.getElementById('cab').dataset.v") == 'board' and await pg.evaluate("!!document.querySelector('.tile.armed')"):
        await pg.click(sel)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for W, H in SIZES:
            ctx = await b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=3)
            pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.route('http://bsb.test/**', lambda r: r.fulfill(body=HTML, content_type='text/html'))
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
            f = await pg.evaluate(FONTS); print(W, H, 'hook font', f['min'], '–', f['max'], 'px', ('OVERFLOW ' + str(f['over'])) if f['over'] else '')
            await tap(pg, '[data-i="0"]'); await pg.wait_for_timeout(400); await shot('q')
            w = await pg.evaluate("document.getElementById('q').dataset.w")
            await pg.click(f'.choice[data-w="{w}"]'); await pg.wait_for_timeout(400); await shot('win')
            await pg.click('#flip'); await pg.wait_for_timeout(1100)
            for i in (6, 12):
                await right(i); await pg.click('#flip'); await pg.wait_for_timeout(1100)
            await shot('board3')
            for i in (1, 7):
                await right(i); await pg.click('#flip'); await pg.wait_for_timeout(1100)
            await right(13); await pg.click('#flip'); await pg.wait_for_timeout(700); await shot('goal')
            await pg.wait_for_timeout(1200); await shot('board6')
            await tap(pg, '[data-i="14"]'); await pg.wait_for_timeout(350)
            wrong = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w).find(x => x !== document.getElementById('q').dataset.w)")
            await pg.click(f'.choice[data-w="{wrong}"]'); await pg.wait_for_timeout(500); await shot('miss')
            await pg.click('#flip'); await pg.wait_for_timeout(500); await shot('end')
            await pg.reload(); await pg.wait_for_timeout(1200)
            if await pg.evaluate("document.getElementById('cab').dataset.v") != 'end': print(W, H, 'a finished day did not reopen to the end')
            await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('bsb-daily')); s.res = s.res.map(() => 1); s.open = -1; localStorage.setItem('bsb-daily', JSON.stringify(s)); }")
            await pg.reload(); await pg.wait_for_timeout(1200); await shot('hat')
            if errs: print(W, H, 'JS ERRORS', errs)
            await ctx.close()
        await b.close()
    print('screens in', OUT)
asyncio.run(main())
