"""Before main moves: the live build against the new one, so a push never changes a board someone is playing.

    python3 tools/golive.py [REF]      # REF: the live build's commit, default origin/main

1. Yesterday's, today's and tomorrow's boards (Seattle dates, which covers every time zone's today) deal the same 15 cards
   with the same three choices in the same order. Later days only report a change: pinned boards change them on purpose.
2. A day in progress on the live build (three cards played, a fourth open) opens on the new one with the same card and
   choices, Back works, and it plays to the end.
3. A day finished on the live build reopens to its end screen with its results unchanged.
Runs on the real clock in Seattle time.
"""
import asyncio, json, os, subprocess, sys
from playwright.async_api import async_playwright
from docsroute import route
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
OLD = subprocess.run(['git', 'show', f'{REF}:docs/index.html'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
NEW = open(os.path.join(ROOT, 'docs', 'index.html')).read()
DEAL = "d => TRIVIELA.deal(d).flat().map(c => [c.id, TRIVIELA.choices(c, d)])"   # a day's 15 cards and their choices
fails = []
def ok(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond: fails.append(what)

async def page(b, html, saved=None):   # a phone in Seattle, with whatever the old build left in its storage
    ctx = await b.new_context(viewport={'width': 402, 'height': 744}, timezone_id='America/Los_Angeles', service_workers='block', reduced_motion='reduce')
    pg = await ctx.new_page(); pg.errs = []; pg.on('pageerror', lambda e: pg.errs.append(str(e)))
    init = "try { localStorage.setItem('bsb-intro-off', 'true') } catch (e) {}"
    for k, v in (saved or {}).items(): init += f"try {{ localStorage.setItem({json.dumps(k)}, {json.dumps(v)}) }} catch (e) {{}}"
    await pg.add_init_script(init)
    await pg.route('https://bsb.test/**', route(html))
    await pg.goto('https://bsb.test/'); await pg.wait_for_timeout(400)
    return ctx, pg

state = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('bsb-daily'))")
storage = lambda pg: pg.evaluate("Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)]))")
view = lambda pg: pg.evaluate("document.getElementById('cab').dataset.v")
choices = lambda pg: pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w)")

async def play(pg, i, right):   # tile i, right or wrong, then Next
    await pg.click(f'[data-i="{i}"]'); await pg.wait_for_timeout(60)
    w = await pg.evaluate("document.getElementById('q').dataset.w")
    await pg.click(f'.choice[data-w="{w if right else next(x for x in await choices(pg) if x != w)}"]')
    await pg.wait_for_timeout(60); await pg.click('#go'); await pg.wait_for_timeout(80)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. the boards being played somewhere right now
        c1, o = await page(b, OLD); c2, n = await page(b, NEW)
        so, sn = await state(o), await state(n); d = sn['day']
        print(f'-- {REF} (live) against docs/index.html, today #{d + 1} in Seattle')
        ok(so['day'] == d and [(t['id'], t['ch']) for t in so['tiles']] == [(t['id'], t['ch']) for t in sn['tiles']], f'#{d + 1}, today: a fresh board is the same 15 cards with the same choices')
        for k in [x for x in (d - 1, d + 1) if x >= 0]:
            ok(await o.evaluate(f"({DEAL})({k})") == await n.evaluate(f"({DEAL})({k})"), f'#{k + 1}, {"yesterday" if k < d else "tomorrow"} somewhere: the same cards and choices')
        changed = [k + 1 for k in range(d + 2, d + 8) if await o.evaluate(f"({DEAL})({k})") != await n.evaluate(f"({DEAL})({k})")]
        print(f'      later days that change: {", ".join("#" + str(k) for k in changed) if changed else "none"}')
        await c1.close(); await c2.close()
        # 2. a day in progress
        c1, o = await page(b, OLD)
        await play(o, 0, True); await play(o, 6, False); await play(o, 12, True)
        await o.click('[data-i="2"]'); await o.wait_for_timeout(60)
        was = await choices(o); saved = await storage(o); await c1.close()
        c2, n = await page(b, NEW, saved)
        ok(await view(n) == 'play' and await choices(n) == was, 'a day in progress reopens its open card with the same choices in the same order')
        s = await state(n); ok([s['res'][i] for i in (0, 6, 12)] == [1, 2, 1], 'its three played cards keep their results')
        await n.click('#go'); await n.wait_for_timeout(120)   # Back: the key, never the screen
        s = await state(n); ok(await view(n) == 'board' and s['open'] == -1 and s['res'][2] == 0, 'Back returns its open card to the board still to play')
        for i in range(15):
            if (await state(n))['res'][i] == 0: await play(n, i, i % 3 != 1)
        s = await state(n)
        ok(await view(n) == 'end' and sorted(s['path']) == list(range(15)), 'it plays to the end screen, each card once in its path')
        ok(not n.errs, 'no script errors ' + str(n.errs)); await c2.close()
        # 3. a finished day
        c1, o = await page(b, OLD)
        for i in range(15): await play(o, i, i % 4 != 0)
        saved = await storage(o); res = json.loads(saved['bsb-daily'])['res']; await c1.close()
        c2, n = await page(b, NEW, saved)
        ok(await view(n) == 'end' and (await state(n))['res'] == res, 'a finished day reopens to its end screen with its results unchanged')
        ok(not n.errs, 'no script errors ' + str(n.errs)); await c2.close()
        await b.close()
    print('all good' if not fails else f'{len(fails)} failed')
    sys.exit(1 if fails else 0)
asyncio.run(main())
