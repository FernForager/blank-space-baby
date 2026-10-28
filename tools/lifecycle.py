"""Check the daily's life cycle: saving, resuming, locking, sharing, midnight and the playtest demo.

    python3 tools/lifecycle.py [page.html]       # default docs/index.html

Runs twice: as the real daily (DEMO 0) and as the playtest demo (DEMO_DAYS in build.py), whichever the page was built as.

1. A tapped tile opens its card: a reload reopens the same card with the same choices in the same order, and Back returns it
   to the board still to play, its choices in place when it opens again (Morg, Oct 26, 2026).
2. A reload after a right answer keeps the chip, and the board shows it.
3. A miss doesn't end the day: all the day's cards play (9 since Oct 27, 2026), and the share is the grid, exactly (checked
   through the clipboard).
4. A finished day reopens to its result and can't be replayed, and How to play stops opening on its own.
5. At local midnight the countdown runs out and a fresh board appears, numbered one higher.
   In the demo there is no countdown and midnight changes nothing: Play #2 opens #2, the last board ends with a
   thank-you that a reload keeps, and Play again from #1 goes back to #1.
6. The right answer never lands in the same slot three cards running.
Runs on a fake clock set to 23:58 local time on puzzle #1's date.
"""
import asyncio, datetime, json, os, re, sys
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'index.html')).read()
START = json.loads(re.search(r'START = (\[[^\]]+\])', HTML).group(1))
BUILT = int(re.search(r'DEMO = (\d+);', HTML).group(1))
PER = int(re.search(r'var PER = (\d+)', HTML).group(1)); N = 3 * PER   # cards of each color, and a day's cards
def as_demo(n): return re.sub(r'DEMO = \d+;', f'DEMO = {n};', HTML, count=1)
TEXT = json.load(open(os.path.join(ROOT, 'build', 'text', 'en.json')))   # the share's own words
HEAD = re.search(r"var HEAD = '([^']+)'", HTML).group(1)   # the share's header row: a card per column (🟩🟨🟥 since Oct 28, 2026)
fails = []
def ok(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond: fails.append(what)

async def tap(pg, sel):   # a tile tap
    await pg.click(sel)

async def answer(pg, i, right):   # play tile i, right or wrong, then tap on. Returns the right answer's slot
    await tap(pg, f'[data-i="{i}"]'); w = await pg.evaluate("document.getElementById('q').dataset.w")
    ch = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w)")
    pick = w if right else next(x for x in ch if x != w)
    await pg.click(f'.choice[data-w="{pick}"]'); await pg.wait_for_timeout(40); await pg.click('#flip'); await pg.wait_for_timeout(60)
    return ch.index(w)

def expected(s, n):   # the share text for a saved day: the board's shape, every card in its spot, a miss as its card, then the score
    k = len(s['res']); cols = [[('⚽' if s['res'][i] == 1 else '❌') for i in range(k) if s['tiles'][i]['d'] == d] for d in (1, 2, 3)]
    rows = [''.join(cols[d][j] for d in range(3)) for j in range(k // 3)]   # the board's shape: a line per spot, white, yellow, red
    right = sum(1 for r in s['res'] if r == 1)
    return TEXT['share.title'].replace('{day}', str(n)) + '\n' + HEAD + '\n' + '\n'.join(rows) + '\n' + ('GOLAZO!' if right == k else f'{right}/{k}') + '\n' + TEXT['share.tagline'] + '\n' + TEXT['share.site']


async def run(b, html, demo):
    print(f'-- as the {"demo, " + str(demo) + " boards" if demo else "real daily"}')
    ctx = await b.new_context(viewport={'width': 402, 'height': 744}, reduced_motion='reduce')
    await ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin='https://bsb.test')
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.add_init_script("try { localStorage.setItem('bsb-intro-off', 'true') } catch (e) {}")   # skip the how-to-play screen
    await pg.clock.install(time=datetime.datetime(START[0], START[1], START[2], 23, 58, 0))
    await pg.route('https://bsb.test/**', lambda r: r.fulfill(body=html, content_type='text/html'))
    await pg.goto('https://bsb.test/'); await pg.wait_for_timeout(300)
    state = lambda: pg.evaluate("JSON.parse(localStorage.getItem('bsb-daily'))")
    s = await state(); ok(s and s['day'] == 0, 'a fresh day is saved as soon as the board opens')
    # 1. commit
    await pg.click('[data-i="3"]')
    v = await pg.evaluate("document.getElementById('cab').dataset.v")
    ok(v == 'play', f'the first tile of the day opens on one tap: {v}')
    before = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w)")
    await pg.reload(); await pg.wait_for_timeout(300)
    v = await pg.evaluate("document.getElementById('cab').dataset.v")
    after = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w)")
    ok(v == 'play' and before == after, 'a reload reopens the tapped card with the same choices in order')
    # 1b. Back: out of the card without answering it, and the same card again later, its choices where they were
    await pg.click('#go'); await pg.wait_for_timeout(100)
    s = await state(); v = await pg.evaluate("document.getElementById('cab').dataset.v")
    playable = await pg.evaluate("!document.querySelector('[data-i=\"3\"]').disabled")
    ok(v == 'board' and s['open'] == -1 and s['res'][3] == 0 and playable and s['path'] == [], 'Back returns to the board with the card still to play')
    await pg.reload(); await pg.wait_for_timeout(300)
    ok(await pg.evaluate("document.getElementById('cab').dataset.v") == 'board', 'a reload after Back shows the board, not the card')
    await pg.click('[data-i="3"]'); await pg.wait_for_timeout(100)
    again = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w)")
    ok(again == before, 'the card opens again with the same choices in the same places')
    # 2. a right answer survives a reload before tapping on
    w = await pg.evaluate("document.getElementById('q').dataset.w")
    await pg.click(f'.choice[data-w="{w}"]'); await pg.reload(); await pg.wait_for_timeout(300)
    s = await state(); v = await pg.evaluate("document.getElementById('cab').dataset.v")
    lit = await pg.evaluate("document.querySelectorAll('#v-board .ball .pt.on:not(.core)').length")   # the three balls: one ring of five lit, their free-space centers aside
    ok(v == 'board' and s['res'][3] == 1 and lit == 5, f'a right answer is saved at once and its ring is lit in its ball after a reload ({lit} panels)')
    # the rest of the day: every tile is played, two of them wrong, and the right answer never takes one slot 3 times running
    slots = [s['tiles'][3]['ch'].index(next(c for c in s['tiles'][3]['ch'] if c['w'] == s['tiles'][3]['w']))]
    for i in [x for x in range(N) if x != 3]:
        ch = await answer(pg, i, i not in (PER + 2, 2 * PER + 1)); slots.append(ch)   # a yellow and a red missed
    ok(not any(slots[k] == slots[k + 1] == slots[k + 2] for k in range(len(slots) - 2)), f'the right answer never takes one slot 3 times running ({"".join(map(str, slots))})')
    # 3. a miss doesn't end the day: all the cards play, then the share is the grid, every card in its spot
    s = await state(); v = await pg.evaluate("document.getElementById('cab').dataset.v")
    ok(v == 'end' and all(s['res']), f'the day ends only after all {N} cards: {v}')
    ok(sorted(s['path']) == list(range(N)) and s['path'][0] == 3, f'the path holds the {N} cards once each, in the order answered: {s["path"]}')
    await pg.click('#share'); await pg.wait_for_timeout(200)
    text = await pg.evaluate("navigator.clipboard.readText()")
    ok(text == expected(s, 1), 'the share text is exact: ' + repr(text))
    score = await pg.evaluate("document.querySelector('#v-end .score').textContent")
    ok(score == f'{N - 2}/{N}', f'the end screen shows the score: {score}')
    ok(await pg.evaluate("localStorage.getItem('bsb-intro-off')") == 'true', 'a finished day stops How to play from opening on its own')
    # 4. locked
    await pg.reload(); await pg.wait_for_timeout(300)
    v = await pg.evaluate("document.getElementById('cab').dataset.v")
    n = await pg.evaluate("document.querySelectorAll('[data-i]:not([disabled])').length")
    ok(v == 'end' and n == 0, 'a finished day reopens to its result, with nothing left to tap')
    if not demo:
        # 5. midnight
        c0, left = await pg.evaluate("""[document.getElementById('clock').textContent,
            Math.floor((new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate() + 1) - new Date()) / 1000)]""")
        c0 = re.search(r'\d\d:\d\d:\d\d', c0).group(0)   # the digits, after the Next board in label
        h, m, sec = map(int, c0.split(':'))
        ok(abs(h * 3600 + m * 60 + sec - left) <= 1, f'the countdown shows the time to local midnight: {c0}')
        ok(await pg.evaluate("document.getElementById('e-next').hidden && document.getElementById('e-again').hidden"), 'the real daily has no next or start-over keys')
        await pg.clock.run_for(125_000); await pg.wait_for_timeout(300)
        v = await pg.evaluate("document.getElementById('cab').dataset.v"); s = await state()
        ok(v == 'board' and s['day'] == 1 and not any(s['res']), 'at midnight a fresh board appears, as puzzle #2')
    else:
        # 5. the demo: no countdown, Play #2 opens the next board, the last one thanks you and offers Play again from #1
        row = lambda: pg.evaluate("""({ clock: document.getElementById('clock').hidden ? null : document.getElementById('clock').textContent,
            next: document.getElementById('e-next').hidden ? null : document.getElementById('e-next').textContent,
            again: !document.getElementById('e-again').hidden, thanks: !!document.getElementById('thanks-s') })""")
        r = await row(); ok(r == {'clock': None, 'next': 'Play #2', 'again': False, 'thanks': False}, f'a finished board offers only #2, with no countdown (Start over lives in the menu): {r}')
        await pg.clock.run_for(125_000); await pg.wait_for_timeout(300)
        v = await pg.evaluate("document.getElementById('cab').dataset.v"); s = await state()
        ok(v == 'end' and s['day'] == 0, 'midnight changes nothing in the demo')
        await pg.click('#e-next'); await pg.wait_for_timeout(300)
        v = await pg.evaluate("document.getElementById('cab').dataset.v"); s = await state()
        ok(v == 'board' and s['day'] == 1 and not any(s['res']), 'Play #2 opens a fresh board, #2')
        for i in range(N): await answer(pg, i, False)
        await pg.click('#share'); await pg.wait_for_timeout(200)
        text = await pg.evaluate("navigator.clipboard.readText()")
        ok(text == TEXT['share.title'].replace('{day}', '2') + '\n' + HEAD + '\n' + '❌❌❌\n' * PER + f'0/{N}\n' + TEXT['share.tagline'] + '\n' + TEXT['share.site'], 'board #2, all missed, shares as #2: ' + repr(text))
        await pg.evaluate(f"localStorage.setItem('bsb-demo', '{demo - 1}'); localStorage.removeItem('bsb-daily')"); await pg.reload(); await pg.wait_for_timeout(300)
        s = await state(); ok(s['day'] == demo - 1, f'the demo picks up where it was left, on #{demo}')
        for i in range(N): await answer(pg, i, True)
        await pg.wait_for_timeout(5000)
        s = await state(); lit = await pg.evaluate("document.querySelectorAll('#v-board .ball .pt.on:not(.core)').length")
        await pg.click('#share'); await pg.wait_for_timeout(200)
        text = await pg.evaluate("navigator.clipboard.readText()")
        ok(text == TEXT['share.title'].replace('{day}', str(demo)) + '\n' + HEAD + '\n' + '⚽⚽⚽\n' * PER + 'GOLAZO!\n' + TEXT['share.tagline'] + '\n' + TEXT['share.site'], 'a perfect day shares as GOLAZO!: ' + repr(text))
        r = await row()
        ok(r == {'clock': None, 'next': None, 'again': True, 'thanks': True}, f'the last board thanks you and offers Play again from #1: {r}')
        await pg.reload(); await pg.wait_for_timeout(300); r = await row()
        ok(await pg.evaluate("document.getElementById('cab').dataset.v") == 'end' and r['thanks'], 'a reload keeps the thank-you')
        await pg.click('#e-again'); await pg.wait_for_timeout(300)
        v = await pg.evaluate("document.getElementById('cab').dataset.v"); s = await state()
        ok(v == 'board' and s['day'] == 0 and not any(s['res']), 'Play again from #1 goes back to a fresh #1')
    ok(not errs, 'no JS errors ' + str(errs))
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await run(b, as_demo(0), 0)
        await run(b, as_demo(BUILT or 7), BUILT or 7)
        await b.close()
    print('all good' if not fails else f'{len(fails)} failed')
    sys.exit(1 if fails else 0)
asyncio.run(main())
