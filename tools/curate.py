"""Data for Morg's curation page (Oct 26, 2026): boards #2 to #7 by hand.

    python3 tools/curate.py export OUT_DIR [CATS]   # pool.json: every card in the draw, with its wrong answers on each day #2 to #7,
                                                    # and draft.json: a first draft of boards #2 to #7 from only the categories CATS
                                                    # (deck ids, comma separated), following the draw's own guardrails
The page (an artifact) reads pool.json beside it and keeps Morg's boards in its own database. Trivelle reads them back
with ArtifactData and writes build/boards.json, and any card he edited or wrote into its deck, once the fact checker has
checked it.
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docsroute import route
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAGS = {'basics': '101', 'rules': 'Rules', 'soccer': 'Lingo', 'lingo-more': 'Lingo', 'alpha': 'Slang', 'parents': 'Slang', 'epl': 'EPL', 'epl-more': 'EPL',
        'mls': 'MLS', 'nwsl': 'NWSL', 'ucl': 'UCL', 'wc26': 'WC26', 'laliga': 'La Liga', 'seriea': 'Serie A', 'ligue1': 'Ligue 1', 'ligamx': 'Liga MX',
        'bundesliga': 'Bundesliga', 'intl-men': 'World', 'intl-women': 'World', 'legends': 'Legends', 'awards': 'Awards', 'nicknames': 'Clubs'}
DAYS = range(1, 7)   # day index 1 to 6 is puzzle #2 to #7

EXPORT = r"""(args) => {
  const [days, cats, tags] = args, T = window.TRIVIELA, deal = T.deal(6, true);
  const deck = c => c.id.split(':')[0];
  const pool = [].concat(T.POOL[0], T.POOL[1], T.POOL[2]).map(c => ({ id: c.id, deck: deck(c), tag: tags[deck(c)], d: c.d, w: c.w, m: c.m, ex: c.ex, hook: c.hook, k: c.k,
    lg: c.lg, wm: c.wm ? 1 : 0, rl: c.rl ? 1 : 0, sl: c.sl ? 1 : 0, ch: Object.fromEntries(days.map(d => [d + 1, T.choices(c, d).map(x => x.w)])) }));
  const one = [].concat(deal[0][0], deal[0][1], deal[0][2]).map(c => c.id);   // #1, as dealt: it stays
  // the first draft: from the chosen categories only, the draw's guardrails, no card twice in the week
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const used = new Set(one), boards = {};
  const ok = c => cats.includes(deck(c)) && !used.has(c.id);
  for (const day of days) {
    let best = null;
    for (let tries = 0; tries < 400 && !best; tries++) {
      const got = [], lg = {}, tag = {};
      const fits = c => !got.some(x => T.near(x, c) || T.near(c, x)) && (!c.lg || (lg[c.lg] || 0) < 3) && (tag[tags[deck(c)]] || 0) < 3 && !(c.sl && got.some(x => x.sl));
      const take = c => { got.push(c); if (c.lg) lg[c.lg] = (lg[c.lg] || 0) + 1; tag[tags[deck(c)]] = (tag[tags[deck(c)]] || 0) + 1; };
      const cols = [[], [], []];
      // a women's card and a rules card first, in any color
      for (const want of [c => c.wm, c => c.rl]) {
        const c = shuffle([].concat(...T.POOL).filter(c => want(c) && ok(c) && fits(c)))[0];
        if (c && cols[c.d - 1].length < 5) { take(c); cols[c.d - 1].push(c); }
      }
      for (let t = 0; t < 3; t++) for (const c of shuffle(T.POOL[t].filter(ok))) { if (cols[t].length >= 5) break; if (!got.includes(c) && fits(c)) { take(c); cols[t].push(c); } }
      if (cols.every(c => c.length === 5) && got.some(c => c.wm) && got.some(c => c.rl)) best = cols;
    }
    if (!best) return { error: 'could not draft #' + (day + 1) };
    best.forEach(col => col.forEach(c => used.add(c.id)));
    boards[day + 1] = [].concat(...best.map(col => shuffle(col))).map(c => c.id);
  }
  return { pool, one, boards };
}"""

async def export(out, cats):
    html = open(os.path.join(ROOT, 'docs', 'index.html')).read()
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await (await b.new_context()).new_page()
        await pg.route('http://bsb.test/**', route(html))
        await pg.goto('http://bsb.test/?day=1'); await pg.wait_for_timeout(800)
        r = await pg.evaluate(EXPORT, [list(DAYS), cats, TAGS])
        await b.close()
    if 'error' in r: sys.exit(r['error'])
    os.makedirs(out, exist_ok=True)
    json.dump({'cards': r['pool'], 'one': r['one'], 'tags': TAGS}, open(os.path.join(out, 'pool.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'boards': r['boards'], 'cats': cats}, open(os.path.join(out, 'draft.json'), 'w'), ensure_ascii=False, indent=1)
    print(f"{len(r['pool'])} cards, #1 kept, drafts for #" + ', #'.join(r['boards']) + f" from {len(cats)} decks")

if __name__ == '__main__':
    if sys.argv[1] == 'export':
        cats = sys.argv[3].split(',') if len(sys.argv) > 3 else list(TAGS)
        asyncio.run(export(sys.argv[2], cats))
