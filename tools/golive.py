"""Before main moves: the live build against the new one, so a push never changes a board someone is playing.

    python3 tools/golive.py [REF]      # REF: the live build's commit, default origin/main

1. Yesterday's, today's and tomorrow's dates in Seattle (which covers every time zone's today) show the same puzzle, its
   same cards with the same three choices in the same order. Date by date, so moving #1's date shows up too. Later dates
   only report a change: pinned boards change them on purpose.
2. A day in progress on the live build (three cards played, a fourth open) opens on the new one with the same card and
   choices, Back works, and it plays to the end.
3. A day finished on the live build reopens to its end screen with its results unchanged.
When the new build changes the save's version (v 5 on Oct 27, 2026: nine cards), saved days start fresh by design, so
2 and 3 are skipped and say so.
Runs on the real clock in Seattle time.
"""
import asyncio, datetime, json, os, re, subprocess, sys
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright
from docsroute import route
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
OLD = subprocess.run(['git', 'show', f'{REF}:docs/index.html'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
NEW = open(os.path.join(ROOT, 'docs', 'index.html')).read()
DEAL = "d => TRIVIELA.deal(d).flat().map(c => [c.id, TRIVIELA.choices(c, d)])"   # a day's cards and their choices
def start(html): return datetime.date(*json.loads(re.search(r'START = (\[[^\]]+\])', html).group(1)))
def number(first, date): return max(0, (date - first).days)   # the puzzle a build shows on a date: before #1's date, #1 plays early
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
        # 1. the boards being played somewhere right now, date by date
        c1, o = await page(b, OLD); c2, n = await page(b, NEW)
        so, sn = await state(o), await state(n)
        today, fo, fn = datetime.datetime.now(ZoneInfo('America/Los_Angeles')).date(), start(OLD), start(NEW)
        board = lambda pg, k: pg.evaluate(f"({DEAL})({k})")
        print(f'-- {REF} (live) against docs/index.html, {today:%b %-d} in Seattle')
        ok(so['day'] == sn['day'] and [(t['id'], t['ch']) for t in so['tiles']] == [(t['id'], t['ch']) for t in sn['tiles']], f'today: a fresh board is the same #{sn["day"] + 1}, its cards and choices')
        later = []
        for off in (-1, 1, 2, 3, 4, 5, 6, 7):
            date = today + datetime.timedelta(off); ko, kn = number(fo, date), number(fn, date)
            same = ko == kn and await board(o, ko) == await board(n, kn)
            what = f'#{kn + 1}, the same cards and choices' if same else f'#{ko + 1} becomes #{kn + 1}' if ko != kn else f'#{kn + 1} gets new cards or choices'
            if off < 2: ok(same, f'{"yesterday" if off < 0 else "tomorrow"} somewhere ({date:%b %-d}): {what}')
            elif not same: later.append(f'{date:%b %-d}: {what}')
        print('      later dates that change: ' + ('. '.join(later) if later else 'none'))
        await c1.close(); await c2.close()
        if so['v'] != sn['v']:
            print(f"      the save changes from v{so['v']} to v{sn['v']}, so days saved on the live build start fresh on the new one, by design: 2 and 3 skipped")
            await b.close(); print('all good' if not fails else f'{len(fails)} failed'); sys.exit(1 if fails else 0)
        N = len(sn['tiles']); third = N // 3   # the day's cards, and where yellow and red start
        # 2. a day in progress
        c1, o = await page(b, OLD)
        await play(o, 0, True); await play(o, third, False); await play(o, 2 * third, True)
        await o.click('[data-i="2"]'); await o.wait_for_timeout(60)
        was = await choices(o); saved = await storage(o); await c1.close()
        c2, n = await page(b, NEW, saved)
        ok(await view(n) == 'play' and await choices(n) == was, 'a day in progress reopens its open card with the same choices in the same order')
        s = await state(n); ok([s['res'][i] for i in (0, third, 2 * third)] == [1, 2, 1], 'its three played cards keep their results')
        await n.click('#go'); await n.wait_for_timeout(120)   # Back: the key, never the screen
        s = await state(n); ok(await view(n) == 'board' and s['open'] == -1 and s['res'][2] == 0, 'Back returns its open card to the board still to play')
        for i in range(N):
            if (await state(n))['res'][i] == 0: await play(n, i, i % 3 != 1)
        s = await state(n)
        ok(await view(n) == 'end' and sorted(s['path']) == list(range(N)), 'it plays to the end screen, each card once in its path')
        ok(not n.errs, 'no script errors ' + str(n.errs)); await c2.close()
        # 3. a finished day
        c1, o = await page(b, OLD)
        for i in range(N): await play(o, i, i % 4 != 0)
        saved = await storage(o); res = json.loads(saved['bsb-daily'])['res']; await c1.close()
        c2, n = await page(b, NEW, saved)
        ok(await view(n) == 'end' and (await state(n))['res'] == res, 'a finished day reopens to its end screen with its results unchanged')
        ok(not n.errs, 'no script errors ' + str(n.errs)); await c2.close()
        await b.close()
    print('all good' if not fails else f'{len(fails)} failed')
    sys.exit(1 if fails else 0)
asyncio.run(main())
