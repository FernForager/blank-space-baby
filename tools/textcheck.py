"""The text check: every string in its slot, on every screen, at three phone sizes (research/text-system.md).

    python3 tools/textcheck.py              # checks docs/index.html, writes out/text-sheet.png (every slot, all three sizes)
    python3 tools/textcheck.py --pseudo     # every string about 40% longer and accented, to find the tight spots before
                                            # anyone writes a longer line, and any English the game shows from outside build/text
    python3 tools/textcheck.py --page FILE  # another build
    python3 tools/textcheck.py --states     # also list the slots each screen showed

It plays the daily, the 7-board demo and the lock (switched off on the real site) on puzzle #365, the widest number. In every screen it finds every slot in build/text/slots.json and checks the text in it:
  - fits: no letter outside its box, and nothing cut off by a box that clips
  - lines: no more than the slot's "lines"
  - even: two or more lines, the last at least a third as wide as the longest (a lone word on its own line reads as a mistake)
  - centered: a centered single line, with any icon beside it, sits within a device pixel of the middle of its box
  - glyphs: every character is in the font the slot asks for, not a fallback
  - English left in the code (--pseudo only): visible words that didn't come from build/text
Card text (hooks, sentences, answers, meanings) is checked here too, and across a month of boards by tools/sweep.py.
Exits 1 on any problem (not in --pseudo mode, where problems are the point).
"""
import asyncio, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build'))
from docsroute import route
import strings
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'out')
SIZES = [(402, 744), (375, 667), (320, 568)]   # iPhone 17 in the Claude viewer, iPhone SE 2/3, iPhone SE 1
SCALE = 3
args = sys.argv[1:]
PSEUDO = '--pseudo' in args
PAGE = args[args.index('--page') + 1] if '--page' in args else os.path.join(ROOT, 'docs', 'index.html')

# ---- pseudo-localization: accented, about 40% longer, the placeholders and GOLAZO!'s shape kept ----
# the accents are all in Latin-1 and Latin Extended-A, which cover the languages the game might meet first (Spanish, Portuguese,
# French, German, Italian, Polish …), so a character the check finds missing from a font is a real gap
ACCENT = dict(zip('abcdeghijklnorstuwyzABCDEGHIJKLNORSTUWYZ', 'åbçðéĝĥîĵķļñöŕšţûŵýžÅBÇÐÉĜĤÎĴĶĻÑÖŔŠŢÛŴÝŽ'))
def pseudo(s):
    if re.fullmatch(r'[a-z0-9.\-{}]+\.png', s) or not re.search(r'[A-Za-z]', re.sub(r'\{\w+\}', '', s)): return s   # a file name, or no words (11/15)
    out = re.sub(r'(\{\w+\})|([A-Za-z])', lambda m: m.group(1) or ACCENT.get(m.group(2), m.group(2)), s)
    n = len(re.sub(r'\{\w+\}', '', s))
    grow = 1.0 if n <= 10 else .8 if n <= 20 else .6 if n <= 30 else .5 if n <= 50 else .4   # short strings grow the most (IBM's rule of thumb)
    pad = round(n * grow)
    words = ['ŵöŕð', 'ļöñĝ', 'ţéxţ', 'fîļļ']
    extra = ''
    while len(extra) < pad: extra += ' ' + words[len(extra) % 4]
    return out + extra[:pad + 1].rstrip()

KNOWN = [pseudo(v) for v in strings.load()[0].values()]   # every string as --pseudo shows it

def page_html(demo=False):
    html = open(PAGE).read()
    if demo: html = re.sub(r'DEMO = 0\b', 'DEMO = 7', html, count=1)
    if PSEUDO:
        m = re.search(r'var TEXT = (\{.*?\});\n', html)
        text = {k: pseudo(v) for k, v in json.loads(m.group(1)).items()}
        html = html[:m.start(1)] + json.dumps(text, ensure_ascii=False).replace('</', '<\\/') + html[m.end(1):]
    return html

# ---- the measurement, run in the page ----
MEASURE = r"""(slots) => {
  const owner = new Map();   // each element's slot: the last row of the table that matches it, as in the CSS
  for (const [name, s] of Object.entries(slots)) for (const el of document.querySelectorAll(s.sel)) owner.set(el, name);
  const shown = el => { if (!el.getClientRects().length) return false; for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e);
    if (c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) return false; if (e.hidden) return false; } return true; };
  const cv = document.createElement('canvas').getContext('2d');
  const has = (ch, fam, wt) => { if (/\s/.test(ch)) return true; cv.font = `${wt} 40px ${fam}, serif`; const a = cv.measureText(ch).width;
    cv.font = `${wt} 40px ${fam}, monospace`; return Math.abs(a - cv.measureText(ch).width) < .01; };
  const out = [];
  for (const [el, name] of owner) {
    if (!shown(el)) continue;
    const texts = [], walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n; (n = walk.nextNode());) {
      if (!n.data.trim()) continue;
      let p = n.parentElement; while (p && !owner.has(p)) p = p.parentElement;
      if (p === el && shown(n.parentElement)) texts.push(n);
    }
    if (!texts.length) continue;
    const rects = [];
    for (const n of texts) { const r = document.createRange(); r.selectNodeContents(n); for (const q of r.getClientRects()) if (q.width > .5) rects.push(q); }
    if (!rects.length) continue;
    const cs = getComputedStyle(el), b = el.getBoundingClientRect(), fs = parseFloat(cs.fontSize);
    const box = { l: b.left + parseFloat(cs.borderLeftWidth) + parseFloat(cs.paddingLeft), r: b.right - parseFloat(cs.borderRightWidth) - parseFloat(cs.paddingRight),
                  t: b.top + parseFloat(cs.borderTopWidth), b: b.bottom - parseFloat(cs.borderBottomWidth) };
    const ink = { l: Math.min(...rects.map(q => q.left)), r: Math.max(...rects.map(q => q.right)), t: Math.min(...rects.map(q => q.top)), b: Math.max(...rects.map(q => q.bottom)) };
    const lines = [];   // rects on one line share most of their height
    for (const q of [...rects].sort((a, c) => a.top - c.top)) {
      const mid = (q.top + q.bottom) / 2, L = lines.find(x => Math.abs(x.mid - mid) < fs * .45);
      if (L) { L.l = Math.min(L.l, q.left); L.r = Math.max(L.r, q.right); } else lines.push({ mid, l: q.left, r: q.right });
    }
    const clip = [];   // the boxes that cut text off: this one and any ancestor that clips
    for (let e = el; e && e !== document.body; e = e.parentElement) { const c = getComputedStyle(e);
      if (c.overflowX !== 'visible' || c.overflowY !== 'visible') { const q = e.getBoundingClientRect(); clip.push({ l: q.left, r: q.right, t: q.top, b: q.bottom, who: e.className || e.id || e.tagName }); } }
    clip.push({ l: 0, r: innerWidth, t: 0, b: innerHeight, who: 'the screen edge' });   // and nothing past the phone's own edge
    let cut = 0, cutBy = '';
    for (const c of clip) { const d = Math.max(c.l - ink.l, ink.r - c.r, c.t - ink.t, ink.b - c.b); if (d > cut) { cut = d; cutBy = c.who; } }
    const missing = new Set();
    for (const n of texts) { const c = getComputedStyle(n.parentElement), fam = c.fontFamily.split(',')[0], wt = c.fontWeight;
      for (const ch of n.data) if (!missing.has(ch) && !has(ch, fam, wt)) missing.add(ch); }
    // what's centered is the text with its icons (a card, an arrow) together, so icons join the ink for the centering check
    const marks = [...el.querySelectorAll('svg, i, img')].filter(k => { let p = k.parentElement; while (p && !owner.has(p)) p = p.parentElement; return p === el && k.getClientRects().length; })
      .map(k => k.getBoundingClientRect()).filter(q => q.width > .5);
    const all = { l: Math.min(ink.l, ...marks.map(q => q.left)), r: Math.max(ink.r, ...marks.map(q => q.right)) };
    const idEl = el.closest('[data-t],[data-tid]') || el.querySelector('[data-t],[data-tid]');
    const card = el.closest('.tile') && !el.matches('.tile .tag') ? 'card' : el.closest('.sentence,.choice') ? 'card' : '';
    out.push({ slot: name, id: card || (idEl ? (idEl.dataset.t || idEl.dataset.tid) : ''), text: texts.map(n => n.data).join(' ').replace(/\s+/g, ' ').trim(),
      fs, align: cs.textAlign, lines: lines.length, widths: lines.map(x => x.r - x.l), over: Math.max(ink.l < box.l - 1 ? box.l - ink.l : 0, ink.r > box.r + 1 ? ink.r - box.r : 0),
      cut, cutBy, off: ((all.l - box.l) - (box.r - all.r)) / 2, missing: [...missing].join(''),
      crop: { x: b.left, y: b.top, w: b.width, h: b.height }, covered: (() => { const h = document.elementFromPoint((ink.l + ink.r) / 2, (ink.t + ink.b) / 2); return !h || !(el.contains(h) || h.contains(el)); })() });
  }
  return out;
}"""
STRAYS = r"""(known) => {   // visible words not from build/text: in --pseudo every string is accented, so a word found in none of them came from somewhere else
  const out = [], walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walk.nextNode());) {
    const p = n.parentElement; if (!p || p.closest('script,style,.hk,.sentence,.choice,[aria-hidden="true"]') || !p.getClientRects().length) continue;
    let vis = true; for (let e = p; e; e = e.parentElement) { const c = getComputedStyle(e); if (c.display === 'none' || c.visibility === 'hidden' || e.hidden) { vis = false; break; } }
    const t = n.data.trim();
    if (vis && /[A-Za-z]{2,}/.test(t) && !known.some(k => k.includes(t))) out.push(t);
  }
  return out;
}"""

async def main():
    slots = strings.load_slots()
    sel = {k: {'sel': v['sel']} for k, v in slots.items()}
    found, problems, strays, crops = [], [], set(), {}
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for W, H in SIZES:
            for demo in (False, True):
                html = page_html(demo)
                ctx = await br.new_context(viewport={'width': W, 'height': H}, device_scale_factor=SCALE)
                pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.on('dialog', lambda d: asyncio.ensure_future(d.accept('test')))
                await pg.route('http://bsb.test/**', route(html))
                await pg.route('http://bsb.test/api/**', lambda r: r.fulfill(status=200, body='{"ok":true}', content_type='application/json'))
                async def look(state):   # measured at rest: every animation (a shout's pop, a blink) at its plain style
                    still = await pg.add_style_tag(content='*, *::before, *::after { animation: none !important; transition: none !important; } .pitch.fxon .shout { opacity: 1 !important; }')   # GOLAZO! at its peak
                    await pg.wait_for_timeout(80)
                    shot = Image.open(io.BytesIO(await pg.screenshot()))
                    for m in await pg.evaluate(MEASURE, sel):
                        m.update(W=W, H=H, state=state); found.append(m)
                        key = (m['slot'], m['id'] if m['id'] != 'card' else '', W)
                        if not m['covered'] and len(crops.setdefault(key, [])) < (1 if m['id'] == 'card' else 2) and m['text'] not in [c[0] for c in crops[key]]:
                            c = m['crop']; pad = 6
                            box = tuple(round(v * SCALE) for v in (c['x'] - pad, c['y'] - pad, c['x'] + c['w'] + pad, c['y'] + c['h'] + pad))
                            crops[key].append((m['text'], shot.crop(box)))
                    if PSEUDO: strays.update(await pg.evaluate(STRAYS, KNOWN))
                    await still.evaluate('e => e.remove()')
                async def card(i, good=True):
                    await pg.click(f'[data-i="{i}"]'); await pg.wait_for_timeout(420)
                    w = await pg.evaluate("document.getElementById('q').dataset.w")
                    if not good: w = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w).find(x => x !== document.getElementById('q').dataset.w)")
                    await pg.click(f'.choice[data-w="{w}"]'); await pg.wait_for_timeout(420)
                async def setday(res, path):   # a saved day: each tile's result and the tap order
                    await pg.evaluate("([res, path]) => { const s = JSON.parse(localStorage.getItem('bsb-daily')); s.res = res; s.path = path; s.open = -1; localStorage.setItem('bsb-daily', JSON.stringify(s)); }", [res, path])
                    await pg.goto(base); await pg.wait_for_timeout(1200)   # without ?reset, which would clear it
                    if await pg.is_visible('#in-go'): await pg.click('#in-go'); await pg.wait_for_timeout(450)   # How to play opens until a day is finished
                base = 'http://bsb.test/' + ('' if demo else '?day=365')
                url = 'http://bsb.test/' + ('?reset' if demo else '?day=365&reset')
                if not demo:
                    await pg.goto(url); await pg.wait_for_timeout(1500); await look('how to play')
                    await pg.click('#in-go'); await pg.wait_for_timeout(500); await look('board')
                    await pg.click('#menu-b'); await pg.wait_for_timeout(450); await look('menu'); await pg.click('#m-close'); await pg.wait_for_timeout(450)
                    await pg.click('[data-i="0"]'); await pg.wait_for_timeout(450); await look('card')
                    w = await pg.evaluate("document.getElementById('q').dataset.w"); await pg.click(f'.choice[data-w="{w}"]'); await pg.wait_for_timeout(450)
                    await look('answered')
                    await pg.click('#b-flag'); await pg.wait_for_timeout(500); await look('beta message')
                    await pg.click('#b-flag'); await pg.wait_for_timeout(1800)
                    await pg.click('#flip'); await pg.wait_for_timeout(1200)
                    await card(5); await pg.click('#flip'); await pg.wait_for_timeout(250); await look('streak')
                    await pg.wait_for_timeout(1800)
                    # a day with one miss
                    await setday([2] + [1] * 12 + [0, 0], list(range(13)))
                    await card(13); await pg.click('#flip'); await pg.wait_for_timeout(1700)
                    await card(14); await pg.click('#flip'); await pg.wait_for_timeout(250); await look('last card')
                    await pg.wait_for_timeout(1800); await look('end, 14 right')
                    await pg.click('.egrid [data-k="0"]'); await pg.wait_for_timeout(420); await look('a card again')   # the grid opens each card again
                    for _ in range(14): await pg.click('#v-end'); await pg.wait_for_timeout(380)
                    await look('the last card again'); await pg.click('#v-end'); await pg.wait_for_timeout(420)
                    await pg.click('#sboard'); await pg.wait_for_timeout(1200); await look('share board pop-up'); await pg.click('#bimg-x'); await pg.wait_for_timeout(400)
                    # a perfect day
                    await setday([1] * 14 + [0], list(range(14)))
                    await card(14); await pg.click('#flip'); await pg.wait_for_timeout(1500); await look('golazo')
                    await pg.wait_for_timeout(3500); await look('end, golazo')
                    await pg.goto('http://bsb.test/?gate'); await pg.wait_for_timeout(1000)
                    for k in '999': await pg.click(f'[data-k="{k}"]')
                    await pg.click('[data-k="enter"]'); await pg.wait_for_timeout(250); await look('lock')
                else:
                    await pg.goto(url); await pg.wait_for_timeout(1200)
                    if await pg.is_visible('#in-go'): await pg.click('#in-go'); await pg.wait_for_timeout(450)
                    await pg.click('#menu-b'); await pg.wait_for_timeout(450); await look('demo menu')
                    await pg.click('#m-restart'); await pg.wait_for_timeout(450); await look('start over pop-up'); await pg.click('#ra-no'); await pg.wait_for_timeout(450)
                    await setday([1, 2] * 7 + [1], list(range(15))); await look('demo end')
                    await pg.evaluate("localStorage.setItem('bsb-demo', '6'); localStorage.removeItem('bsb-daily')"); await pg.goto(base); await pg.wait_for_timeout(1000)
                    await setday([1, 2] * 7 + [1], list(range(15))); await look('demo last board')
                if errs: problems.append(f'{W}×{H} JS errors: {errs}')
                await ctx.close()
        await br.close()

    # ---- the verdicts ----
    seen = set()
    for m in found:
        s, where = slots[m['slot']], f"{m['W']}×{m['H']} {m['state']}: {m['slot']} {m['id'] or ''} “{m['text'][:48]}”"
        say = lambda what: problems.append(f'{where} {what}') if (where, what) not in seen and not seen.add((where, what)) else None
        if m['over'] > 0: say(f'runs {m["over"]:.1f} px outside its box')
        if m['cut'] > 1: say(f'cut off {m["cut"]:.1f} px by {m["cutBy"]}')
        if s.get('lines') and m['lines'] > s['lines']: say(f'takes {m["lines"]} lines, the slot allows {s["lines"]}')
        if m['lines'] >= 2 and min(m['widths'][-1:]) < max(m['widths']) / 3: say(f'uneven lines ({", ".join(str(round(w)) for w in m["widths"])} px)')
        if m['align'] == 'center' and m['lines'] == 1 and abs(m['off']) * SCALE > 1.5 and m['over'] == 0: say(f'{abs(m["off"]):.1f} px off center')
        if m['missing']: say(f'characters not in its font: {m["missing"]}')
    if PSEUDO:
        for t in sorted(strays): problems.append(f'English not from build/text: “{t}”')
    measured = {m['slot'] for m in found}
    unseen = [k for k in slots if k not in measured]
    if unseen: print('slots with no text of their own on these screens (size or line height only, or not reached):', ', '.join(unseen))
    for k, s in slots.items():
        if k not in measured and 'lines' in s: problems.append(f'slot {k} never showed up on any screen the check plays: add a screen for it')
    if '--states' in args:   # which slots each screen showed
        for st in dict.fromkeys(m['state'] for m in found): print(st, sorted({m['slot'] for m in found if m['state'] == st}))
    sheet(crops, slots)
    ids = {m['id'] for m in found if m['id'] not in ('', 'card')}
    print(f'{len(found)} pieces of text on {len({(m["W"], m["state"]) for m in found})} screens, {len(measured)} of {len(slots)} slots, {len(ids)} string ids' + (' (pseudo)' if PSEUDO else ''))
    for q in problems: print('  ', q)
    print('all good' if not problems else f'{len(problems)} problems')
    print('contact sheet:', os.path.join(OUT, 'text-sheet' + ('-pseudo' if PSEUDO else '') + '.png'))
    if problems and not PSEUDO: sys.exit(1)

def sheet(crops, slots):
    """Every slot with its strings, at the three phone sizes side by side, to judge a wording change at a glance."""
    os.makedirs(OUT, exist_ok=True)
    try: font = ImageFont.truetype('DejaVuSans.ttf', 26)
    except OSError: font = ImageFont.load_default()
    keys = sorted({(k[0], k[1]) for k in crops}, key=lambda k: (list(slots).index(k[0]), k[1]))
    COLW, GAP = 1240, 24
    rows = []
    for slot, sid in keys:
        cells = [[im for _, im in crops.get((slot, sid, W), [])] for W, _ in SIZES]
        h = max((sum(im.height + 8 for im in c) for c in cells), default=0)
        if h: rows.append((slot, sid, cells, h))
    H = sum(h + 60 + GAP for *_, h in rows) + 80
    img = Image.new('RGB', (COLW * 3 + GAP * 4, H), '#2A2F2C'); d = ImageDraw.Draw(img)
    for i, (W, Hh) in enumerate(SIZES): d.text((GAP + i * (COLW + GAP), 24), f'{W}×{Hh}', fill='#9FB5A8', font=font)
    y = 80
    for slot, sid, cells, h in rows:
        d.text((GAP, y), f'{slot}  ·  {sid or "-"}  ·  {slots[slot]["where"]}', fill='#EAFBF0', font=font)
        for i, c in enumerate(cells):
            yy = y + 44
            for im in c:
                if im.width > COLW: im = im.resize((COLW, round(im.height * COLW / im.width)))
                img.paste(im, (GAP + i * (COLW + GAP), yy)); yy += im.height + 8
        y += h + 60 + GAP
    img.save(os.path.join(OUT, 'text-sheet' + ('-pseudo' if PSEUDO else '') + '.png'))

asyncio.run(main())
