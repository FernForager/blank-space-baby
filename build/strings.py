"""The game's strings: every word it shows or says, apart from the cards (research/text-system.md).

    from strings import load, problems
    text, meta = load()            # build/text/en.json: {id: text} and {id: {note, slot, placeholders}}

build.py puts them into the page and stops on any problem below. tools read them the same way.
"""
import html, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.join(HERE, 'text')
ID = re.compile(r'^[a-z][a-z0-9]*(?:\.[a-zA-Z0-9]+)*$')
DYNAMIC = ('tag.', 'color.', 'row.', 'gate.', 'beta.')   # ids the game builds from a prefix ('tag.' + its deck's tag), so never "unused"

def load(lang='en'):
    raw = json.load(open(os.path.join(TEXT, lang + '.json')))
    text = {k: v for k, v in raw.items() if not k.startswith('@')}
    meta = {k[1:]: v for k, v in raw.items() if k.startswith('@') and not k.startswith('@@')}
    return text, meta

def holes(s): return set(re.findall(r'\{(\w+)\}', s))

def problems(text, meta, template):
    """House style, notes and placeholders for every string, and every id the template asks for."""
    out = []
    for k, s in text.items():
        m = meta.get(k)
        if not ID.match(k): out.append((k, 'an id is lowercase words joined by dots'))
        if not m or not m.get('note'): out.append((k, 'needs a note saying where it shows ("@' + k + '": {"note": …})'))
        if ';' in s: out.append((k, 'a semicolon (house style: never)'))
        if "'" in s or '"' in s: out.append((k, 'a straight quote or apostrophe (use ’ “ ”)'))
        if '<' in s or '&' in s: out.append((k, 'HTML in a string (the game does the typesetting)'))
        if s != s.strip() or '  ' in s.replace('  {score}', ''): out.append((k, 'a stray space'))
        if re.search(r'\b(soccer|football)', s, re.I): out.append((k, 'says soccer or football (Morg, Oct 26, 2026: never, so the game stays global)'))   # the image's score line may keep a wide gap before its score (#42  11/15)
        named = set((m or {}).get('placeholders', {}))
        if holes(s) - named: out.append((k, 'placeholder ' + ', '.join(sorted(holes(s) - named)) + ' isn’t listed in its "placeholders"'))
        if named - holes(s): out.append((k, 'lists placeholder ' + ', '.join(sorted(named - holes(s))) + ' but doesn’t use it'))
    for k in meta:
        if k not in text: out.append((k, 'a note for a string that doesn’t exist'))
    asked = set(re.findall(r'data-t(?:-label|-alt)?="([a-z][a-zA-Z0-9.]*)"', template))
    asked |= {q for q in re.findall(r"'([a-z][a-z0-9]*\.[a-zA-Z0-9.]*[a-zA-Z0-9])'", template) if q.split('.')[0] + '.' in {k.split('.')[0] + '.' for k in text}}
    asked |= {q for q in re.findall(r"\b(?:tx|th)\('([^']+)'", template) if not q.endswith('.')}
    asked |= {q for q in re.findall(r'data-tid="([a-z][a-zA-Z0-9.]*[a-zA-Z0-9])"', template)}   # th() and data-tid with a new prefix used to slip past (the audit, Oct 30, 2026)
    asked |= {'tag.' + v for v in re.findall(r"'(?:[\w-]+)':\s*'(\w+)'|\b\w+:\s*'(\w+)'", re.search(r'var TAG = \{(.*?)\};', template, re.S).group(1)) for v in v if v}
    asked |= {'color.%d' % d for d in (1, 2, 3)} | {'row.%d' % d for d in (1, 2, 3)} | {'gate.clear', 'gate.enter'}
    for k in sorted(asked - set(text)): out.append((k, 'the game asks for it, but build/text has no such string'))
    for k in sorted(set(text) - asked):
        if not k.startswith(DYNAMIC) and k not in ('brand', 'meta.description') and "'" + k + "'" not in template: out.append((k, 'not used anywhere in the game'))
    return out

def fill_head(page, text):
    """The page head's __T:id__ marks (the title, the link preview), as escaped plain text."""
    return re.sub(r'__T:([\w.]+)__', lambda m: html.escape(text[m.group(1)]), page)

# ---- the slots: every place text appears (build/text/slots.json), turned into the game's text CSS ----
FACES = {'pixel': 'var(--body-font)', 'arcade': 'var(--pixel)'}
WRAPS = {'line': 'white-space: nowrap', 'balance': 'text-wrap: balance', 'pretty': 'text-wrap: pretty'}
MEDIA = (('mid', '(max-height: 700px)'), ('short', '(max-height: 640px)'), ('narrow', '(max-width: 360px)'))
KEYS = {'where', 'sel', 'face', 'weight', 'size', 'fallback', 'mid', 'short', 'narrow', 'lh', 'track', 'trackShort', 'case', 'align', 'wrap', 'lines', 'trim', 'nudge', 'fit', 'shrink'}

def load_slots():
    raw = json.load(open(os.path.join(TEXT, 'slots.json')))
    return {k: v for k, v in raw.items() if not k.startswith('@')}

def px(v): return v if isinstance(v, str) else (f'{v:g}px' if v else '0')

def slot_problems(slots, meta):
    out = []
    for k, s in slots.items():
        if set(s) - KEYS: out.append(('slot ' + k, 'unknown setting ' + ', '.join(sorted(set(s) - KEYS))))
        if not s.get('where') or not s.get('sel'): out.append(('slot ' + k, 'needs "where" and "sel"'))
        if s.get('face', 'pixel') not in FACES: out.append(('slot ' + k, 'face is pixel or arcade'))
        if s.get('wrap', 'line') not in WRAPS: out.append(('slot ' + k, 'wrap is line, balance or pretty'))
        if 'shrink' in s and not (0.5 <= s['shrink'] <= 1): out.append(('slot ' + k, 'shrink is the smallest share of its size the text may shrink to, from 0.5 to 1'))
    for k, m in meta.items():
        if m.get('slot') and m['slot'] not in slots: out.append((k, 'its slot "' + m['slot'] + '" isn’t in build/text/slots.json'))
    return out

def page_meta(meta, slots):
    """What the in-game text editor shows: each string's note, slot and blanks, and each slot's selector, line limit and place."""
    m = {k: {'note': v.get('note', ''), 'slot': v.get('slot', ''), 'ph': ', '.join('{%s} (%s)' % (p, d.get('example', '')) for p, d in v.get('placeholders', {}).items())} for k, v in meta.items()}
    s = {k: dict({'sel': v['sel'], 'lines': v.get('lines', 0), 'where': v['where']}, **({'shrink': v['shrink']} if 'shrink' in v else {})) for k, v in slots.items()}
    return m, s

def slot_fit(slots):
    """The slots whose too-wide words tighten to fit: {selector: the tightest letter spacing, in device pixels}, for the page's tighten()."""
    return {s['sel']: s['fit'] for s in slots.values() if 'fit' in s}

def slot_css(slots):
    """One rule per slot, then the phone sizes, in the table's order (a later row wins a tie)."""
    base, media = [], {q: [] for _, q in MEDIA}
    for k, s in slots.items():
        d = []
        if 'face' in s: d.append('font-family: ' + FACES[s['face']])
        if 'weight' in s: d.append(f'font-weight: {s["weight"]}')
        if 'fallback' in s: d.append('font-size: ' + px(s['fallback']))   # for a browser without container units (iOS 15): the size below wins where it is understood
        if 'size' in s: d.append('font-size: ' + px(s['size']))
        if 'lh' in s: d.append(f'line-height: {s["lh"]:g}')
        if 'track' in s: d.append('letter-spacing: ' + px(s['track']))
        if 'case' in s: d.append('text-transform: ' + {'upper': 'uppercase', 'lower': 'lowercase'}[s['case']])
        if 'align' in s: d.append('text-align: ' + s['align'])
        if 'wrap' in s: d.append(WRAPS[s['wrap']])
        if s.get('trim'): d.append('text-box: trim-both cap alphabetic')
        if s.get('nudge'): d.append('translate: ' + ' '.join(px(v) for v in s['nudge']))
        base.append(f'{s["sel"]} {{ {"; ".join(d)}; }}   /* {k} */')
        for key, q in MEDIA:
            m = []
            if key in s: m.append('font-size: ' + px(s[key]))
            if key == 'short' and 'trackShort' in s: m.append('letter-spacing: ' + px(s['trackShort']))
            if m: media[q].append(f'{s["sel"]} {{ {"; ".join(m)}; }}')
    out = ['/* the text slots, written by build.py from build/text/slots.json: change a row there, not here */'] + base
    for q, rules in media.items():
        if rules: out.append(f'@media {q} {{ ' + ' '.join(rules) + ' }')
    return '\n'.join(out)
