"""Every card's tile words in a real tile, at three phone sizes: the text boxes of the board (Morg, Oct 28, 2026).

    python3 tools/tilecheck.py          # every card in the draw, against the rules below. Writes out/tilecheck.txt

The rules, from the tag and hook rows of build/text/slots.json: a card's category (its tag) sits on one line, never clipped,
and its hook takes two lines at most, shrinking no further than its row's "shrink" allows, with no word broken across
lines, no hyphenated word split, and no word left alone on the last line. The cards that play now (the fixed board while
ONE_BOARD holds, or else every card in the draw) must pass, or it exits 1. The rest are listed for the editor to shorten.
"""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright
from docsroute import route
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(ROOT, 'docs', 'index.html')).read()
ONE = re.search(r'var ONE = (true|false)', HTML).group(1) == 'true' or bool(re.search(r'var LOOP = [1-9]', HTML))   # one board plays: the fixed board, or the loop's (Oct 30, 2026)
SIZES = [(402, 744, 3), (375, 667, 3), (320, 568, 2)]   # each phone at its own scale: a 320-wide iPhone is 2× (the audit, Oct 30, 2026)
MEASURE = """() => {
  const board = document.getElementById('p-board'), boxes = [...board.querySelectorAll('[data-i]')], out = [];
  // lines by the middle of each box: digits sit in the arcade face a little lower than the letters, so tops alone would split a line
  const lines = (rects, tol) => { const m = []; rects.filter(x => x.width > .5).forEach(x => { const c = x.top + x.height / 2; if (!m.some(y => Math.abs(y - c) < tol)) m.push(c); }); return m.sort((a, b) => a - b); };
  const boxLines = (el, tol) => { const r = document.createRange(); r.selectNodeContents(el); return lines([...r.getClientRects()], tol); };
  const words = (el, tol) => {   // each word (split at spaces, the no-break glue included) and the lines its letters sit on
    const chars = [], it = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
    while ((n = it.nextNode())) for (let i = 0; i < n.data.length; i++) chars.push([n, i, n.data[i]]);
    const w = []; let start = -1;
    chars.concat([[null, 0, ' ']]).forEach((c, i) => {
      const gap = /[\\s\\u00a0]/.test(c[2]);
      if (!gap && start < 0) start = i;
      if (gap && start >= 0) { const a = chars[start], z = chars[i - 1], r = document.createRange(); r.setStart(a[0], a[1]); r.setEnd(z[0], z[1] + 1); w.push({ lines: lines([...r.getClientRects()], tol) }); start = -1; }
    });
    return w;
  };
  const cards = TRIVIELA.ALL;
  boxes.forEach(b => { b.className = 'key tile c1'; b.innerHTML = '<span class="hk">x</span>'; b.disabled = false; });
  const base = parseFloat(getComputedStyle(boxes[0].querySelector('.hk')).fontSize);
  for (let k = 0; k < cards.length; k += boxes.length) {
    const chunk = cards.slice(k, k + boxes.length);
    chunk.forEach((c, j) => { boxes[j].className = 'key tile c' + c.d; boxes[j].innerHTML = TRIVIELA.face(c); });
    TRIVIELA.tighten(board); chunk.forEach((c, j) => TRIVIELA.fit(boxes[j]));
    chunk.forEach((c, j) => {
      const b = boxes[j], tag = b.querySelector('.tag'), hk = b.querySelector('.hk'), fs = parseFloat(getComputedStyle(hk).fontSize), tol = fs * .45;
      const ls = boxLines(hk, tol), ws = words(hk, tol), last = ls[ls.length - 1];
      const onLast = ws.filter(x => x.lines.some(y => Math.abs(y - last) < tol)).length;
      out.push({ id: c.id, d: c.d, hook: c.hook, tag: tag.textContent, fs: fs, base: base, lines: ls.length,
        wide: hk.scrollWidth > hk.clientWidth + .5, split: ws.some(x => x.lines.length > 1),
        alone: ws.length >= 3 && ls.length > 1 && onLast === 1,
        tagClip: tag.scrollWidth > tag.clientWidth + .5, tagLines: boxLines(tag, parseFloat(getComputedStyle(tag).fontSize) * .45).length });
    });
  }
  return out;
}"""
async def main():
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for W, H, DPR in SIZES:
            ctx = await b.new_context(viewport={'width': W, 'height': H}, device_scale_factor=DPR, timezone_id='America/Los_Angeles', service_workers='block', reduced_motion='reduce')
            pg = await ctx.new_page()
            await pg.route('https://bsb.test/**', route(HTML)); await pg.goto('https://bsb.test/'); await pg.wait_for_timeout(800)
            await pg.evaluate("document.fonts.ready")
            playing = await pg.evaluate("TRIVIELA.state().tiles.map(t => t.id)")
            res[W] = await pg.evaluate(MEASURE)
            await ctx.close()
        await b.close()
    play = set(playing) if ONE else {r['id'] for r in res[SIZES[0][0]]}
    rules = [('lines', lambda r: r['lines'] > 2, 'hook on more than two lines'), ('wide', lambda r: r['wide'], 'a hook word wider than its tile, even shrunk'),
             ('split', lambda r: r['split'], 'a word or hyphenated word split across lines'), ('alone', lambda r: r['alone'], 'a word alone on the last line'),
             ('tag', lambda r: r['tagClip'] or r['tagLines'] > 1, 'category cut off or on two lines')]
    bad, lines_out = {}, []
    for W, rows in res.items():
        shrunk = [r for r in rows if r['fs'] < r['base'] - .01]
        lines_out.append(f'-- {W} wide, {dict((w, d) for w, _, d in SIZES)[W]}×: hook {rows[0]["base"]:g} px, {len(shrunk)} of {len(rows)} hooks shrink to fit (smallest {min([r["fs"] for r in rows]):g} px)')
        for key, test, what in rules:
            hit = [r for r in rows if test(r)]
            lines_out.append(f'   {len(hit):4} {what}')
            for r in hit: bad.setdefault(r['id'], {'hook': r['hook'], 'tag': r['tag'], 'why': set()})['why'].add(f'{what} at {W}')
    print('\n'.join(lines_out))
    os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
    with open(os.path.join(ROOT, 'out', 'tilecheck.txt'), 'w') as f:
        f.write('\n'.join(lines_out) + '\n\n')
        for cid, v in sorted(bad.items()): f.write(f'{cid}\t{v["tag"]}\t{v["hook"]}\t' + '; '.join(sorted(v['why'])) + '\n')
    now = sorted(c for c in bad if c in play)
    print(f'{len(bad)} cards break a rule somewhere (out/tilecheck.txt). Playing now ({"the one board that plays" if ONE else "the whole draw"}): {len(now)}')
    for c in now: print('  ', c, '|', bad[c]['tag'], '|', bad[c]['hook'], '|', '; '.join(sorted(bad[c]['why'])))
    sys.exit(1 if now else 0)
asyncio.run(main())
