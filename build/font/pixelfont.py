"""Build Triviela Pixel, the game's body font, from Pixelify Sans (SIL Open Font License 1.1).

    python3 build/font/pixelfont.py            # writes docs/fonts/triviela-pixel-v1.woff2 (and a .ttf copy in out/ for checking)

Pixelify Sans is drawn on an 11-to-the-em pixel grid, but Google's copy sits slightly off it: outlines overhang each pixel by
about a tenth, every advance carries 0.44 px of padding, the kerning and the line metrics are off the grid, and the accents
and punctuation are drawn in half pixels. So no size is ever quite sharp. This script redraws it on its own grid:

  - every letter and digit is read back from the static weight-400 master as a bitmap (a pixel is on when the outline
    covers more than half of it), and rebuilt as whole-pixel squares, 100 units each, at 1100 units to the em
  - the punctuation and the accents, which Pixelify draws in half pixels, are redrawn by hand below on whole pixels
  - accented letters are built from the base letter and the redrawn accent
  - advances are whole pixels (one pixel of space between letters), with no kerning
  - ascent 10 px, descent 3 px, line gap 0: all on the grid

The game asks for one weight. A bold built by widening every stroke one pixel was tried (pass --bold to build it): see FONTLOG.
"""
import os, sys, unicodedata
import numpy as np
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import instancer
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(HERE, 'PixelifySans-wght.ttf')
P = 1000 / 11          # one pixel in the source's units
X0, Y0 = 60, -12       # where the source's pixel grid starts (the coordinate audit, Oct 19, 2026)
U = 100                # one pixel in the new font's units
UPM = 11 * U
ASC, DESC = 10, 3      # in pixels
SS = 24                # coverage samples per pixel each way
BOLD = '--bold' in sys.argv
FAMILY = 'Triviela Pixel' + (' Bold' if BOLD else '')
OUT = 'triviela-pixel-bold-v1' if BOLD else 'triviela-pixel-v1'

# ---- what the font covers: the game's characters and the Latin range ----
CPS = (list(range(0x20, 0x7F)) + [0xA0] + list(range(0xA1, 0x100)) + list(range(0x100, 0x180)) +
       [0x218, 0x219, 0x21A, 0x21B, 0x237, 0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2022,
        0x2026, 0x2039, 0x203A, 0x20AC, 0x2122, 0x2212])
SKIP = {0xAD, 0xBC, 0xBD, 0xBE, 0xA6, 0x132, 0x133, 0x138, 0x17F, 0x149}   # soft hyphen, the fractions, the broken bar, ĳ, kra, long s, ŉ: never used, left to the system font

# ---- hand-drawn glyphs, top row first. (top row index, rows). Column 0 of a row is the glyph's first pixel: every glyph
# starts one pixel in and ends flush with its advance, so letters sit one pixel apart ----
H = {
    'R':  (6, ['###.', '#..#', '#..#', '#..#', '###.', '#.#.', '#..#']),
    ',':  (0, ['##', '.#']),
    ';':  (3, ['.#', '..', '##', '.#']),
    "'":  (6, ['#', '#']),
    '"':  (6, ['#.#', '#.#']),
    '‘':  (6, ['#.', '##']),
    '’':  (6, ['##', '.#']),
    '‚':  (0, ['##', '.#']),
    '“':  (6, ['#..#.', '##.##']),
    '”':  (6, ['##.##', '.#..#']),
    '„':  (0, ['##.##', '.#..#']),
    '(':  (7, ['..#', '.#.', '.#.', '#..', '#..', '#..', '#..', '.#.', '.#.', '..#']),
    ')':  (7, ['#..', '.#.', '.#.', '..#', '..#', '..#', '..#', '.#.', '.#.', '#..']),
    '[':  (7, ['##', '#.', '#.', '#.', '#.', '#.', '#.', '#.', '#.', '##']),
    ']':  (7, ['##', '.#', '.#', '.#', '.#', '.#', '.#', '.#', '.#', '##']),
    '{':  (7, ['..#', '.#.', '.#.', '.#.', '#..', '#..', '.#.', '.#.', '.#.', '..#']),
    '}':  (7, ['#..', '.#.', '.#.', '.#.', '..#', '..#', '.#.', '.#.', '.#.', '#..']),
    '/':  (6, ['...#', '..#.', '..#.', '.#..', '.#..', '#...', '#...']),
    '\\': (6, ['#...', '.#..', '.#..', '..#.', '..#.', '...#', '...#']),
    '-':  (2, ['###']),
    '–':  (3, ['####']),   # the dashes sit a pixel above the hyphen, as in the source, level with the middle of the digits
    '—':  (3, ['######']),
    '−':  (2, ['#####']),
    '_':  (-1, ['#####']),
    '~':  (3, ['.##.#', '#..#.']),
    '^':  (6, ['.#.', '#.#']),
    '`':  (7, ['#.', '.#']),
    '*':  (5, ['#.#', '.#.', '#.#']),
    '+':  (4, ['..#..', '..#..', '#####', '..#..', '..#..']),
    '=':  (3, ['####', '....', '####']),
    '<':  (5, ['...#', '..#.', '.#..', '#...', '.#..', '..#.', '...#']),
    '>':  (5, ['#...', '.#..', '..#.', '...#', '..#.', '.#..', '#...']),
    '@':  (6, ['.###.', '#...#', '#.###', '#.#.#', '#.##.', '#....', '.###.']),
    '%':  (6, ['##...', '##..#', '...#.', '..#..', '.#...', '#..##', '...##']),
    '$':  (7, ['..#..', '.###.', '#...#', '#....', '.###.', '....#', '#...#', '.###.', '..#..']),
    '×':  (5, ['#...#', '.#.#.', '..#..', '.#.#.', '#...#']),
    '÷':  (4, ['..#..', '.....', '#####', '.....', '..#..']),
    '±':  (6, ['..#..', '..#..', '#####', '..#..', '..#..', '.....', '#####']),
    '¬':  (3, ['#####', '....#']),
    '«':  (4, ['..#..#', '.#..#.', '#..#..', '.#..#.', '..#..#']),
    '»':  (4, ['#..#..', '.#..#.', '..#..#', '.#..#.', '#..#..']),
    '‹':  (4, ['..#', '.#.', '#..', '.#.', '..#']),
    '›':  (4, ['#..', '.#.', '..#', '.#.', '#..']),
    '•':  (3, ['##', '##']),
    '…':  (0, ['#.#.#']),
    '°':  (6, ['.#.', '#.#', '.#.']),
    '¨':  (6, ['#.#']),
    '´':  (7, ['.#', '#.']),
    '¯':  (7, ['###']),
    '¸':  (-1, ['.#', '##']),
    '·':  (2, ['#']),
    '¹':  (7, ['.#.', '##.', '.#.', '.#.', '###']),
    '²':  (7, ['.#.', '#.#', '..#', '.#.', '###']),
    '³':  (7, ['##.', '..#', '.#.', '..#', '##.']),
    'ª':  (6, ['.##', '#.#', '.##', '...', '###']),
    'º':  (6, ['.#.', '#.#', '.#.', '...', '###']),
    '©':  (6, ['.#####.', '#.....#', '#.###.#', '#.#...#', '#.###.#', '#.....#', '.#####.']),
    '®':  (6, ['.#####.', '#.....#', '#.##..#', '#.##..#', '#.#.#.#', '#.....#', '.#####.']),
    '™':  (6, ['###.#...#', '.#..##.##', '.#..#.#.#']),
    '¢':  (5, ['..#..', '.###.', '#.#.#', '#.#..', '#.#.#', '.###.', '..#..']),
    '¤':  (5, ['#...#', '.###.', '.#.#.', '.###.', '#...#']),
    '¥':  (6, ['#...#', '#...#', '.#.#.', '#####', '..#..', '#####', '..#..']),
    '€':  (6, ['..###', '.#...', '####.', '.#...', '####.', '.#...', '..###']),
    '¶':  (6, ['.#####', '####.#', '####.#', '.###.#', '...#.#', '...#.#', '...#.#', '...#.#']),
    '†':  (6, ['.#.', '###', '.#.', '.#.', '.#.', '.#.', '.#.']),
    'Ð':  (6, ['.###.', '.#..#', '.#...#', '####.#', '.#...#', '.#..#', '.###.']),
    'Đ':  (6, ['.###.', '.#..#', '.#...#', '####.#', '.#...#', '.#..#', '.###.']),
    'Þ':  (6, ['#....', '####.', '#...#', '#...#', '#...#', '####.', '#....']),
    'þ':  (6, ['#....', '#....', '####.', '#...#', '#...#', '#...#', '####.', '#....', '#....']),
    'Ø':  (7, ['.....#', '.####.', '#..#.#', '#..#.#', '#.#..#', '#.#..#', '##...#', '.####.', '#.....']),
    'ø':  (5, ['.....#', '.####.', '#..#.#', '#.#..#', '##...#', '.####.', '#.....']),
    'ð':  (7, ['.#.#.', '..#..', '.#.#.', '....#', '.####', '#...#', '#...#', '.###.']),
    'Ł':  (6, ['.#....', '.#....', '.##...', '##....', '.#....', '.#...#', '..###.']),
    'ł':  (6, ['.#.', '.#.', '.##', '##.', '.#.', '.#.', '.#.']),
    'đ':  (6, ['...###', '....#.', '.####.', '#...#.', '#...#.', '#...#.', '.###..']),
    'Ħ':  (6, ['#...#', '#####', '#...#', '#####', '#...#', '#...#', '#...#']),
    'ħ':  (6, ['.#...', '###..', '.#.##', '.##..#', '.#...#', '.#...#', '.#...#']),
    'Ŧ':  (6, ['#####', '..#..', '..#..', '.###.', '..#..', '..#..', '..#..']),
    'Ŀ':  (6, ['#....', '#....', '#....', '#..#.', '#....', '#...#', '.###.']),
    'ŀ':  (6, ['#..', '#..', '#..', '#.#', '#..', '#..', '#..']),
    'Ŋ':  (6, ['#...#', '##..#', '#.#.#', '#.#.#', '#.#.#', '#..##', '#...#', '....#', '..##.']),
    'ŋ':  (4, ['####.', '#...#', '#...#', '#...#', '#...#', '....#', '..##.']),
}
# accents, redrawn on whole pixels: (rows, kind). 'above' sits one pixel over the letter, 'below' hangs under the baseline
MARKS = {
    0x300: (['#.', '.#'], 'above', 'grave'),
    0x301: (['.#', '#.'], 'above', 'acute'),
    0x302: (['.#.', '#.#'], 'above', 'center'),
    0x303: (['.##.#', '#..#.'], 'above', 'center'),
    0x304: (['###'], 'above', 'center'),
    0x306: (['#...#', '.###.'], 'above', 'center'),
    0x307: (['#'], 'above', 'center'),
    0x308: (['#.#'], 'above', 'center'),
    0x30A: (['.#.', '#.#', '.#.'], 'above', 'center'),
    0x30B: (['.#.#', '#.#.'], 'above', 'center'),
    0x30C: (['#.#', '.#.'], 'above', 'center'),
    0x327: (['.#', '##'], 'below', 'center'),
    0x328: (['#.', '.#'], 'below', 'right'),
    0x326: (['##', '.#'], 'comma', 'center'),
}

def bm(top, rows):
    """A bitmap as a set of (col, row) pixels, column 1 first (the one-pixel left side)."""
    return {(c + 1, top - r) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == '#'}

def contours_of(f, name):
    gs = f.getGlyphSet(); pen = DecomposingRecordingPen(gs); gs[name].draw(pen)
    cs, cur = [], []
    for op, args in pen.value:
        if op == 'moveTo': cur = [args[0]]
        elif op == 'lineTo': cur.append(args[0])
        elif op in ('qCurveTo', 'curveTo'): cur.extend(args)
        elif op in ('closePath', 'endPath'):
            if cur: cs.append(cur); cur = []
    return cs

def auto(f, name):
    """Read a source glyph back as pixels: on where the outline covers over half the cell."""
    cs = contours_of(f, name)
    if not cs: return set(), 0
    q = [[((x - X0) / P, (y - Y0) / P) for x, y in c] for c in cs]
    xs = [p[0] for c in q for p in c]; ys = [p[1] for c in q for p in c]
    x0, x1 = int(np.floor(min(xs))) - 1, int(np.ceil(max(xs))) + 1
    y0, y1 = int(np.floor(min(ys))) - 1, int(np.ceil(max(ys))) + 1
    W, Hh = (x1 - x0) * SS, (y1 - y0) * SS
    SX, SY = np.meshgrid(x0 + (np.arange(W) + .5) / SS, y0 + (np.arange(Hh) + .5) / SS)
    wind = np.zeros((Hh, W), int)
    for c in q:
        for i in range(len(c)):
            (ax, ay), (bx, by) = c[i], c[(i + 1) % len(c)]
            if ay == by: continue
            cross = (ay <= SY) & (SY < by) if ay < by else (by <= SY) & (SY < ay)
            xi = ax + (SY - ay) / (by - ay) * (bx - ax)
            wind += np.where(cross & (SX < xi), 1 if by > ay else -1, 0)
    cov = (wind != 0).reshape(y1 - y0, SS, x1 - x0, SS).mean(axis=(1, 3))
    amb = int(((cov > .2) & (cov < .8)).sum())
    return {(x0 + c + 1, y0 + r) for r in range(cov.shape[0]) for c in range(cov.shape[1]) if cov[r, c] > .5}, amb

def place(base, mark, kind, align, cap):
    """Put an accent on a letter: centered on its ink (an acute leans right, a grave left), one pixel clear of it."""
    mrows = mark
    cols = [c for c, r in base] or [1]
    lo, hi = min(cols), max(cols)
    w = len(mrows[0]); h = len(mrows); room = hi - lo + 1 - w
    if align == 'right': x = hi - 1
    elif align == 'grave': x = lo + room // 2
    else: x = lo + (room + 1) // 2   # an odd fit leans right: an acute's foot sits on the letter's middle
    if kind == 'above':
        top_ink = max([r for c, r in base] or [4])
        top = top_ink + 1 + h
        if h == 3: top -= 1   # the ring sits on the letter
    elif kind == 'below': top = -1
    else: top = -2            # comma below: one pixel clear of the baseline
    return {(x + c, top - r) for r, row in enumerate(mrows) for c, ch in enumerate(row) if ch == '#'}

def build():
    src = instancer.instantiateVariableFont(TTFont(SRC), {'wght': 400})
    cmap = src.getBestCmap(); hm = src['hmtx']
    glyphs = {}   # name -> (pixels, advance)
    report = []
    def from_src(ch):
        n = cmap[ord(ch)]
        px, amb = auto(src, n)
        adv = int(round(hm[n][0] / P - 0.446))
        if px: adv = max(adv, max(c for c, r in px) + 1)
        return px, adv, amb
    names = {}
    for cp in CPS:
        if cp in SKIP: continue
        ch = chr(cp)
        name = 'uni%04X' % cp if cp > 0x7E or not ch.isalnum() else ch
        if cp == 0x20: name = 'space'
        if ch in H:
            px = bm(*H[ch]); adv = max(c for c, r in px) + 1
        else:
            d = unicodedata.normalize('NFD', ch)
            if len(d) > 1 and all(ord(m) in MARKS for m in d[1:]) and (ord(d[0]) in cmap or d[0] in H):
                b = d[0]
                if b == 'i': b = 'ı'
                if b == 'j': b = 'ȷ'
                bpx, badv = (bm(*H[b]), max(c for c, r in bm(*H[b])) + 1) if b in H else from_src(b)[:2]
                px = set(bpx); adv = badv
                for m in d[1:]:
                    rows, kind, align = MARKS[ord(m)]
                    if ch in 'ďľť' and ord(m) == 0x30C:   # a caron on a tall letter is a little tick to its right
                        hi = max(c for c, r in bpx); px |= {(hi + 2, 6), (hi + 2, 5)}; adv = hi + 3; continue
                    if ch in 'ģ' and ord(m) == 0x327:
                        rows, kind = ['.#', '#.'], 'above'
                    elif ord(m) == 0x327 and ch in 'ĢĶķĻļŅņŖŗ':
                        rows, kind = MARKS[0x326][0], 'comma'
                    px |= place(bpx, rows, kind, align, ch.isupper())
                lo = min(c for c, r in px)
                if lo < 1: px = {(c + 1 - lo, r) for c, r in px}; adv += 1 - lo
                adv = max(adv, max(c for c, r in px) + 1)
            elif ord(ch) in cmap:
                px, adv, amb = from_src(ch)
                if ch == 'j':   # Pixelify's j has no dot (a quirk of the source): give it the i's dot, over its stem
                    px.add((max(c for c, r in px), 6))
                if amb: report.append('%s (U+%04X): %d half-covered pixels, read back by majority' % (ch, cp, amb))
            else:
                report.append('missing U+%04X' % cp); continue
        if cp in (0x20, 0xA0): px, adv = set(), 3   # a four-pixel gap between words (the source's is 3.5)
        if BOLD and px:
            px = px | {(c + 1, r) for c, r in px}; adv += 1
        glyphs[name] = (px, adv); names[cp] = name
    return glyphs, names, report, src

def outline(px):
    """Trace the pixels' outer edges into closed contours, clockwise around ink (TrueType's direction)."""
    edges = {}
    for c, r in px:
        if (c - 1, r) not in px: edges.setdefault((c, r), []).append((c, r + 1))
        if (c, r + 1) not in px: edges.setdefault((c, r + 1), []).append((c + 1, r + 1))
        if (c + 1, r) not in px: edges.setdefault((c + 1, r + 1), []).append((c + 1, r))
        if (c, r - 1) not in px: edges.setdefault((c + 1, r), []).append((c, r))
    out = []
    while edges:
        start = next(iter(edges)); a = start; path = [a]; prev = None
        while True:
            nxt = edges[a]
            if len(nxt) > 1 and prev is not None:   # two pixels touching at a corner: turn right, so each stays its own shape
                dx, dy = a[0] - prev[0], a[1] - prev[1]
                right = (a[0] + dy, a[1] - dx)
                b = right if right in nxt else nxt[0]
            else: b = nxt[0]
            nxt.remove(b)
            if not nxt: del edges[a]
            prev, a = a, b
            if a == start: break
            path.append(a)
        # drop points in the middle of straight runs
        pts = []
        n = len(path)
        for i in range(n):
            p0, p1, p2 = path[i - 1], path[i], path[(i + 1) % n]
            if (p1[0] - p0[0]) * (p2[1] - p1[1]) - (p1[1] - p0[1]) * (p2[0] - p1[0]) != 0: pts.append(p1)
        out.append(pts)
    return out

def save(glyphs, names, src):
    order = ['.notdef'] + [n for n in glyphs]
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({cp: n for cp, n in names.items()})
    gl, mt = {}, {}
    notdef = {(c, r) for c in range(1, 5) for r in range(0, 7) if c in (1, 4) or r in (0, 6)}
    for n, (px, adv) in [('.notdef', (notdef, 5))] + list(glyphs.items()):
        pen = TTGlyphPen(None)
        for cont in outline(px):
            pen.moveTo((cont[0][0] * U, cont[0][1] * U))
            for x, y in cont[1:]: pen.lineTo((x * U, y * U))
            pen.closePath()
        g = pen.glyph(); gl[n] = g
        mt[n] = (adv * U, min([c for c, r in px]) * U if px else 0)
    fb.setupGlyf(gl); fb.setupHorizontalMetrics(mt)
    fb.setupHorizontalHeader(ascent=ASC * U, descent=-DESC * U, lineGap=0)
    sname = src['name']
    style = 'Bold' if BOLD else 'Regular'
    fb.setupNameTable({
        'copyright': 'Copyright 2021 The Pixelify Sans Project Authors (https://github.com/eifetx/Pixelify-Sans). Triviela Pixel changes 2026 for Triviela (https://triviela.net).',
        'familyName': FAMILY, 'styleName': 'Regular', 'uniqueFontIdentifier': '1.000;TRIV;TrivielaPixel-' + style,
        'fullName': FAMILY, 'version': 'Version 1.000', 'psName': FAMILY.replace(' ', '') + '-Regular',
        'description': 'Pixelify Sans redrawn on its own 11-pixel grid: whole-pixel outlines and advances, no kerning, grid line metrics.',
        'licenseDescription': 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org',
        'licenseInfoURL': 'https://openfontlicense.org',
    })
    fb.setupOS2(sTypoAscender=ASC * U, sTypoDescender=-DESC * U, sTypoLineGap=0, usWinAscent=ASC * U, usWinDescent=DESC * U,
                fsSelection=0x40 | 0x80, usWeightClass=400, sxHeight=5 * U, sCapHeight=7 * U, achVendID='TRIV',
                yStrikeoutSize=U, yStrikeoutPosition=3 * U)
    fb.setupPost(underlinePosition=-2 * U, underlineThickness=U)
    fb.setupHead(unitsPerEm=UPM)
    f = fb.font
    f['head'].fontRevision = 1.0
    f['OS/2'].version = 4
    import time; from fontTools.misc.timeTools import timestampFromString
    f['head'].created = f['head'].modified = timestampFromString('Mon Oct 19 00:00:00 2026')
    gasp = newTable('gasp'); gasp.version = 1; gasp.gaspRange = {0xFFFF: 0x000A}; f['gasp'] = gasp
    os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
    ttf = os.path.join(ROOT, 'out', OUT + '.ttf'); f.save(ttf)
    f.flavor = 'woff2'
    woff = os.path.join(ROOT, 'docs', 'fonts', OUT + '.woff2'); os.makedirs(os.path.dirname(woff), exist_ok=True); f.save(woff)
    return ttf, woff

def arcade():
    """Triviela Arcade: Press Start 2P, unchanged but subset to the Latin range. Press Start 2P's license reserves its name,
    and a subset counts as a modified version, so it travels under its own name."""
    from fontTools import subset
    f = TTFont(os.path.join(HERE, 'PressStart2P-Regular.ttf'))
    opts = subset.Options(); opts.layout_features = []; opts.name_IDs = ['*']; opts.notdef_outline = True; opts.hinting = False; opts.drop_tables += ['GSUB', 'GPOS', 'GDEF']
    s = subset.Subsetter(opts)
    s.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026])
    s.subset(f)
    nm = f['name']
    for rec in list(nm.names):
        if rec.nameID in (1, 3, 4, 6, 16, 17, 18, 21, 22): nm.removeNames(nameID=rec.nameID)
    for nid, v in {1: 'Triviela Arcade', 2: 'Regular', 3: '1.000;TRIV;TrivielaArcade-Regular', 4: 'Triviela Arcade', 6: 'TrivielaArcade-Regular'}.items():
        nm.setName(v, nid, 3, 1, 0x409); nm.setName(v, nid, 1, 0, 0)
    old = nm.getDebugName(0) or ''
    for plat in ((3, 1, 0x409), (1, 0, 0)):
        nm.setName(old.rstrip('. ') + '. Triviela Arcade is a subset of Press Start 2P, renamed as its license requires, 2026.', 0, *plat)
    f.flavor = 'woff2'
    out = os.path.join(ROOT, 'docs', 'fonts', 'triviela-arcade-v1.woff2'); f.save(out)
    return out

if __name__ == '__main__':
    glyphs, names, report, src = build()
    ttf, woff = save(glyphs, names, src)
    if not BOLD:
        a = arcade(); print('Triviela Arcade: %s (%d bytes)' % (os.path.relpath(a, ROOT), os.path.getsize(a)))
    for line in report: print(' ', line)
    print('%s: %d glyphs, %s (%d bytes)' % (FAMILY, len(glyphs), os.path.relpath(woff, ROOT), os.path.getsize(woff)))
