"""Check the daily draw over many days.

    python3 tools/drawcheck.py [days] [page.html]      # default 365 days of docs/index.html

Replays the draw the way every phone does and checks each day's board: PER white, yellow and red cards (3 each since
Oct 27, 2026), at least one women's game card and one rules card, at most LEAGUE_MAX from one league, at most one slang card
and never a red one, and no two cards that give each other away (one's answer in the other's
sentence or hook, or a shared answer or hook). Then every card's three choices on every day: the answer among three
different ones, and every wrong answer one its reviewers saw (the build's wrong_pool from its set in build/library/wrong.json,
what tools/vet.py shows them) or a
made-up near miss on a number card (the audit, Oct 30, 2026: a playing card never shows a wrong answer nobody vetted).
Then reports how far apart repeats land, checks that two fresh page loads deal the same boards, and times the replay.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 365
HTML = open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'docs', 'index.html')).read()
import re
PER = int(re.search(r'var PER = (\d+)', HTML).group(1)); LMAX = int(re.search(r'LEAGUE_MAX = (\d+)', HTML).group(1))   # read from the page itself
sys.path.insert(0, os.path.join(ROOT, 'build')); import build as B
POOLS, NUMERIC = {}, {}   # what the reviewers saw of each card's wrong answers, and whether the page makes up near misses for it
for did, _, _ in B.DAILY:
    deck = json.load(open(os.path.join(B.DECKS, did + '.json'))); clash = B.clasher(deck)
    for i, it in enumerate(deck['items']): POOLS[f'{did}:{i}'] = B.wrong_pool(did, deck, it, clash); NUMERIC[f'{did}:{i}'] = bool(B.near_rule(it))

CHECK = """([days, per, lmax, pools, numeric, spelled]) => {
  const T = window.TRIVIELA, t0 = performance.now(), boards = T.deal(days - 1, true), ms = performance.now() - t0;
  const bad = [], pinned = [], last = {}, gaps = [], seen = {}, mix = { women: 0, rules: 0, slang: 0, leagues: {} };
  let checked = 0, nearMiss = 0;
  boards.forEach((tiers, day) => {
    const all = [].concat(...tiers);
    tiers.forEach((t, i) => { if (t.length !== per || t.some(c => c.d !== i + 1)) bad.push([day, 'color ' + (i + 1) + ' has ' + t.length]); });
    const mine = T.PIN && T.PIN[day + 1];   // Morg's own board: the page deals it as he set it, guardrails and all (Hand-made boards in CLAUDE.md)
    const rule = (what) => (mine ? pinned : bad).push(what);
    if (!all.some(c => c.wm)) rule([day, 'no women’s card']);
    if (!all.some(c => c.rl)) rule([day, 'no rules card']);
    const lg = {}; all.forEach(c => { if (c.lg) lg[c.lg] = (lg[c.lg] || 0) + 1; });
    Object.entries(lg).forEach(([k, n]) => { if (n > lmax) bad.push([day, n + ' from ' + k]); mix.leagues[k] = (mix.leagues[k] || 0) + n; });
    const sl = all.filter(c => c.sl); sl.forEach(c => { if (c.d === 3) bad.push([day, 'red slang', c.id]); });
    if (sl.length > 1) bad.push([day, sl.length + ' slang cards']);
    for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) if (T.near(all[i], all[j])) bad.push([day, 'give away', all[i].id + ' ' + all[i].w, all[j].id + ' ' + all[j].w]);
    all.forEach(c => {   // the three choices, as every phone shows them that day
      const ws = T.choices(c, day).map(x => x.w);
      if (ws.length !== 3 || new Set(ws).size !== 3 || ws.indexOf(c.w) < 0) bad.push([day, 'choices', c.id, ws.join(' / ')]);
      ws.filter(w => w !== c.w).forEach(w => {
        if ((pools[c.id] || []).indexOf(w) >= 0) return;
        if (numeric[c.id] && (/^\\d[\\d,]*$/.test(w) || spelled.indexOf(w) >= 0)) { nearMiss++; return; }
        bad.push([day, 'a wrong answer its reviewers never saw', c.id, w]);
      });
      checked++;
    });
    mix.women += all.filter(c => c.wm).length; mix.rules += all.filter(c => c.rl).length; mix.slang += all.filter(c => c.sl).length;
    all.forEach(c => { if (c.id in last) gaps.push(day - last[c.id]); last[c.id] = day; seen[c.id] = 1; });
  });
  gaps.sort((a, b) => a - b);
  const pool = T.POOL.map(p => p.length);
  return { ms: Math.round(ms), bad: bad.slice(0, 40), nbad: bad.length, pinned, pool, used: Object.keys(seen).length, checked, nearMiss,
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
            if k == 0: res = await pg.evaluate(CHECK, [DAYS, PER, LMAX, POOLS, NUMERIC, B.SPELLED])
            prints.append(await pg.evaluate(FINGER, DAYS))
            await pg.close()
        await b.close()
    print(f'{DAYS} days replayed in {res["ms"]} ms')
    print('cards in the draw (white, yellow, red):', res['pool'], '| different cards used:', res['used'])
    print('first repeat on day', res['firstRepeatDay'], '| repeats:', res['repeats'], '| closest repeat:', res['minGap'], 'days | repeats inside 91 days:', res['under91'])
    print('per day: women', res['perDay']['women'], '| rules', res['perDay']['rules'], '| slang', res['perDay']['slang'])
    print('per day by league:', res['leagues'])
    print('same boards on a second load:', 'yes' if prints[0] == prints[1] else 'NO')
    print('choices checked:', res['checked'], '| wrong answers from the reviewers’ lists or made-up near misses, nothing else | near misses:', res['nearMiss'])
    if res['pinned']: print('on Morg’s own boards, his call, not counted:', '; '.join(f'#{d + 1} {w}' for d, w in res['pinned']))
    print('problems:', res['nbad'])
    for x in res['bad']: print('  ', x)
    print('day 1 board:')
    for t, name in zip(res['sample'], ('white', 'yellow', 'red')): print(f'  {name}:', ', '.join(t))
    sys.exit(1 if res['nbad'] or prints[0] != prints[1] else 0)
asyncio.run(main())
