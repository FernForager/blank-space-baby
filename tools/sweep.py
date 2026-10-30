"""Play many days of the daily and flag anything broken.

    python3 tools/sweep.py [days] [width] [height] [page.html]    # defaults: 30 402 744 docs/index.html

Plays every card of each day (animations off, every answer right), checking each one: three different
choices with the answer among them, a blank in the sentence, nothing overflowing the screen before or
after answering, the answered sentence clear of the go arrow and the beta's flag and lock keys (with the
smallest gap between a line and a key under it), and the page never scrolling. On each board it checks every hook fits its tile and
records the smallest hook font. Prints how often the right answer lands in each slot (should be even).
"""
import asyncio, collections, os, sys
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
W = int(sys.argv[2]) if len(sys.argv) > 2 else 402
H = int(sys.argv[3]) if len(sys.argv) > 3 else 744
HTML = open(sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, 'docs', 'index.html')).read()
CARD = """() => { const q = document.getElementById('q'), f = document.querySelector('.face');
  return { w: q.dataset.w, ch: [...document.querySelectorAll('.choice')].map(b => b.dataset.w), blank: !!q.querySelector('.blank'),
           ov: q.scrollWidth > q.clientWidth + 1 || f.scrollHeight > f.clientHeight + 1, scroll: document.documentElement.scrollHeight > innerHeight }; }"""
AFTER = """() => { const q = document.getElementById('q'), f = document.querySelector('.face');
  return q.scrollWidth > q.clientWidth + 1 || f.scrollHeight > f.clientHeight + 1 || document.documentElement.scrollHeight > innerHeight; }"""
# after answering, the sentence must clear the go arrow and, on preview links, the beta's flag and lock keys
CLEAR = """() => { const r = document.createRange(); r.selectNodeContents(document.getElementById('q'));
  const lines = [...r.getClientRects()], keys = [...document.querySelectorAll('#go:not(.wait), #g-play .bk:not([hidden])')].map(e => e.getBoundingClientRect());
  const hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  const above = [].concat(...lines.map(l => keys.filter(k => l.left < k.right && k.left < l.right).map(k => k.top - l.bottom)));   // only keys a line sits over
  return { hit: lines.some(l => keys.some(k => hit(l, k))), gap: above.length ? Math.min(...above) : 999, keys: keys.length }; }"""
BOARD = """() => { const h = [...document.querySelectorAll('.hk')];
  return { min: Math.min(...h.map(e => parseFloat(getComputedStyle(e).fontSize))), over: h.filter(e => e.scrollWidth > e.clientWidth + 0.5).map(e => e.textContent),
           scroll: document.documentElement.scrollHeight > innerHeight }; }"""

async def tap(pg, sel):   # a tile tap
    await pg.click(sel)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=2 if W <= 320 else 3, reduced_motion='reduce')   # a 320-wide iPhone is 2×, the rest 3× (the audit, Oct 30, 2026)
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.route('http://bsb.test/**', lambda r: r.fulfill(body=HTML, content_type='text/html'))
        slots, problems, fonts, cards, gaps = collections.Counter(), [], [], 0, []
        for day in range(1, DAYS + 1):
            await pg.goto(f'http://bsb.test/?day={day}&reset'); await pg.wait_for_timeout(250)
            bd = await pg.evaluate(BOARD); fonts.append(bd['min'])
            if bd['over'] or bd['scroll']: problems.append((day, 'board', bd))
            N = await pg.evaluate("document.querySelectorAll('#p-board [data-i]').length")   # the day's cards, 9 since Oct 27, 2026
            for i in range(N):
                await tap(pg, f'[data-i="{i}"]')
                st = await pg.evaluate(CARD); cards += 1
                if len(set(st['ch'])) != 3 or st['w'] not in st['ch'] or not st['blank'] or st['ov'] or st['scroll']: problems.append((day, i, st))
                slots[st['ch'].index(st['w'])] += 1
                await pg.click(f'.choice[data-w="{st["w"]}"]')
                if await pg.evaluate(AFTER): problems.append((day, i, 'answer screen overflows', st['w']))
                cl = await pg.evaluate(CLEAR); gaps.append(cl['gap'])
                if cl['hit']: problems.append((day, i, 'the sentence runs into the keys at the bottom', st['w'], cl))
                await pg.click('#flip'); await pg.wait_for_timeout(30 if i < N - 1 else 4500)
            if await pg.evaluate("document.getElementById('cab').dataset.v") != 'end': problems.append((day, f'no end screen after {N} right'))
        print(f'{W}x{H}: {DAYS} days, {cards} cards, slots {dict(sorted(slots.items()))}, smallest hook font {min(fonts):.1f}px, closest the sentence comes to a key below it {min(gaps):.0f}px')
        print('problems:', len(problems))
        for x in problems[:20]: print('  ', x)
        print('JS errors:', errs or 'none'); await b.close()
        # a problem on a board that plays fails the sweep (the audit, Oct 30, 2026: it used to exit 0 whatever it found). With one
        # fixed board only #1 plays, so the rest are listed for the editor, the same rule as tools/tilecheck.py
        one = 'var ONE = true' in HTML; fatal = [x for x in problems if not one or x[0] == 1]
        if one and len(fatal) < len(problems): print(f'{len(problems) - len(fatal)} of them on boards that don\'t play while one fixed board holds: for the editor')
        return 1 if fatal or errs else 0
sys.exit(asyncio.run(main()))
