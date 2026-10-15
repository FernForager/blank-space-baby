"""Play many cards in every level and flag anything broken.

    python3 tools/sweep.py [cards_per_level] [width] [height]     # defaults: 60 402 744

Checks each card: three different choices, the answer among them, a blank in the
sentence, nothing overflowing the screen (before or after answering). Also prints how often the
right answer lands in each slot (should be roughly even). Answers every card right,
so it also walks through level-beaten screens.
"""
import asyncio, collections, os, sys
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(ROOT, 'docs', 'index.html')).read()
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
W = int(sys.argv[2]) if len(sys.argv) > 2 else 402
H = int(sys.argv[3]) if len(sys.argv) > 3 else 744

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': W, 'height': H})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.route('http://bsb.test/', lambda r: r.fulfill(body=HTML, content_type='text/html')); await pg.goto('http://bsb.test/')
        await pg.click('#coin'); await pg.wait_for_timeout(600)
        levels = await pg.evaluate("[...document.querySelectorAll('#p-select .cat:not(.soon)')].map(b => b.id.slice(2))")
        for lv in levels:
            await pg.click('#t-' + lv); seen = collections.Counter(); slots = collections.Counter(); problems = []
            for i in range(N):
                st = await pg.evaluate("""() => ({w: document.getElementById('q').dataset.w, ch: [...document.querySelectorAll('.choice')].map(b => b.dataset.w),
                    blank: !!document.querySelector('#q .blank'),
                    ov: document.getElementById('q').scrollWidth > document.getElementById('q').clientWidth + 1,
                    fh: document.querySelector('.face').scrollHeight > document.querySelector('.face').clientHeight + 1})""")
                seen[st['w']] += 1
                if len(set(st['ch'])) != 3 or st['w'] not in st['ch'] or not st['blank'] or st['ov'] or st['fh']: problems.append(st)
                slots[st['ch'].index(st['w'])] += 1
                await pg.click(f'.choice[data-w="{st["w"]}"]')
                if await pg.evaluate("document.querySelector('.face').scrollHeight > document.querySelector('.face').clientHeight + 1 || document.getElementById('q').scrollWidth > document.getElementById('q').clientWidth + 1"):
                    problems.append(('answer screen overflows', st['w']))
                await pg.click('#flip')
                if await pg.evaluate("document.getElementById('cab').dataset.v") == 'clear':
                    await pg.click('#flip'); await pg.click('#t-' + lv)
            print(f'{lv}: {len(seen)} different cards, slots {dict(sorted(slots.items()))}, problems {problems[:5] or "none"}')
            if await pg.evaluate("document.getElementById('cab').dataset.v") == 'play': await pg.click('#home')
        print('JS errors:', errs or 'none'); await b.close()
asyncio.run(main())
