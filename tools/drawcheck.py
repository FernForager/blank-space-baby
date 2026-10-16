"""Check the daily draw over many days.

    python3 tools/drawcheck.py [days] [page.html]      # default 365 days of docs/index.html

Replays the draw the way every phone does and checks each day's board: 6 white, 6 yellow and 6 red cards,
at least one women's game card and one rules card, at most 3 from one league, at most one card from each
slang deck and never a red one, and no two cards that give each other away (one's answer in the other's
sentence or hook, or a shared answer or hook). Then reports how far apart repeats land, checks that two
fresh page loads deal the same boards, and times the replay.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 365
HTML = open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'docs', 'index.html')).read()

CHECK = """(days) => {
  const T = window.TRIVIELA, t0 = performance.now(), boards = T.deal(days - 1, true), ms = performance.now() - t0;
  const bad = [], last = {}, gaps = [], seen = {}, mix = { women: 0, rules: 0, slang: 0, leagues: {} };
  boards.forEach((tiers, day) => {
    const all = [].concat(...tiers);
    tiers.forEach((t, i) => { if (t.length !== 6 || t.some(c => c.d !== i + 1)) bad.push([day, 'color ' + (i + 1) + ' has ' + t.length]); });
    if (!all.some(c => c.wm)) bad.push([day, 'no women’s card']);
    if (!all.some(c => c.rl)) bad.push([day, 'no rules card']);
    const lg = {}; all.forEach(c => { if (c.lg) lg[c.lg] = (lg[c.lg] || 0) + 1; });
    Object.entries(lg).forEach(([k, n]) => { if (n > 3) bad.push([day, n + ' from ' + k]); mix.leagues[k] = (mix.leagues[k] || 0) + n; });
    const sl = {}; all.forEach(c => { if (c.sl) { sl[c.D.id] = (sl[c.D.id] || 0) + 1; if (c.d === 3) bad.push([day, 'red slang', c.id]); } });
    Object.entries(sl).forEach(([k, n]) => { if (n > 1) bad.push([day, n + ' from ' + k]); });
    for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) if (T.near(all[i], all[j])) bad.push([day, 'give away', all[i].id + ' ' + all[i].w, all[j].id + ' ' + all[j].w]);
    mix.women += all.filter(c => c.wm).length; mix.rules += all.filter(c => c.rl).length; mix.slang += all.filter(c => c.sl).length;
    all.forEach(c => { if (c.id in last) gaps.push(day - last[c.id]); last[c.id] = day; seen[c.id] = 1; });
  });
  gaps.sort((a, b) => a - b);
  const pool = T.POOL.map(p => p.length);
  return { ms: Math.round(ms), bad: bad.slice(0, 40), nbad: bad.length, pool, used: Object.keys(seen).length,
    repeats: gaps.length, minGap: gaps[0] || null, under91: gaps.filter(g => g < 91).length, firstRepeatDay: (() => { const f = {}; let d0 = null;
      boards.forEach((tiers, day) => [].concat(...tiers).forEach(c => { if (f[c.id] && d0 === null) d0 = day; f[c.id] = 1; })); return d0; })(),
    perDay: { women: (mix.women / days).toFixed(2), rules: (mix.rules / days).toFixed(2), slang: (mix.slang / days).toFixed(2) },
    leagues: Object.fromEntries(Object.entries(mix.leagues).map(([k, n]) => [k, (n / days).toFixed(2)])),
    sample: boards[0].map(t => t.map(c => c.hook + ' (' + c.D.id + ')')) };
}"""
FINGER = "(days) => window.TRIVIELA.deal(days - 1, true).map(b => b.map(t => t.map(c => c.id).join(',')).join('|')).join('/')"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        prints = []
        for k in range(2):
            pg = await b.new_page()
            await pg.route('http://bsb.test/**', lambda r: r.fulfill(body=HTML, content_type='text/html'))
            await pg.goto('http://bsb.test/?day=1&reset'); await pg.wait_for_timeout(300)
            if k == 0: res = await pg.evaluate(CHECK, DAYS)
            prints.append(await pg.evaluate(FINGER, DAYS))
            await pg.close()
        await b.close()
    print(f'{DAYS} days replayed in {res["ms"]} ms')
    print('cards in the draw (white, yellow, red):', res['pool'], '| different cards used:', res['used'])
    print('first repeat on day', res['firstRepeatDay'], '| repeats:', res['repeats'], '| closest repeat:', res['minGap'], 'days | repeats inside 91 days:', res['under91'])
    print('per day: women', res['perDay']['women'], '| rules', res['perDay']['rules'], '| slang', res['perDay']['slang'])
    print('per day by league:', res['leagues'])
    print('same boards on a second load:', 'yes' if prints[0] == prints[1] else 'NO')
    print('problems:', res['nbad'])
    for x in res['bad']: print('  ', x)
    print('day 1 board:')
    for t, name in zip(res['sample'], ('white', 'yellow', 'red')): print(f'  {name}:', ', '.join(t))
    sys.exit(1 if res['nbad'] or prints[0] != prints[1] else 0)
asyncio.run(main())
