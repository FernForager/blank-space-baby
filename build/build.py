"""Build Blank Space Baby.

    python3 build/build.py

Reads build/template.html, build/head.html and the decks in build/decks/,
checks every card against the house style, and writes docs/index.html
(the live page). Stops with a list of problems if any card breaks a rule.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECKS = os.path.join(HERE, 'decks')

# The ten categories, in panel order (reading left to right, two per row). Names show on the keys.
# A category with no deck file yet shows as a dim key until its deck is written and approved.
CATS = [
    ('alpha',   'alpha.json',    'Kid Slang'),
    ('parents', 'parents.json',  'Parent Slang'),
    ('grand',   None,            'Grandparent Slang'),
    ('swift',   'swifties.json', 'Taylor Swift'),
    ('tech',    None,            'Old Tech'),
    ('grade7',  None,            '7th Grade'),
    ('soccer',  'soccer.json',   'Soccer Lingo'),
    ('wc',      None,            'World Cup 2026'),
    ('sea',     None,            'Seattle'),
    ('epl',     'epl.json',      'EPL'),
]
LEVELS = [c for c in CATS if c[1]]

def rx(w):
    return re.compile(r'(^|[^A-Za-z0-9])(' + re.escape(w) + r')(?![A-Za-z0-9])', re.I)

def check(level, deck):
    bad, items = [], deck['items']
    groups = {}
    for i, grp in enumerate(deck.get('groups', [])):
        for w in grp:
            groups.setdefault(w, set()).add(i)
    clash = lambda a, b: a == b or bool(groups.get(a, set()) & groups.get(b, set()))
    for it in items:
        it.setdefault('k', 'word')
        w, ex, mn = it['w'], it['ex'], it['means']
        tag = (level, w)
        if len(rx(w).findall(ex)) != 1: bad.append(tag + ('answer must appear exactly once in the sentence', ex))
        for s in (ex, mn):
            if ';' in s: bad.append(tag + ('semicolon', s))
            if re.search(r"['\"]", s): bad.append(tag + ('straight quote or apostrophe', s))
        if ex.rstrip().endswith('.'): bad.append(tag + ('period at the end', ex))
        if re.search(r'[.!?][”"]?\s+[A-Z]', re.sub(r'\b(Mrs|Mr|Ms|No|St|vs)\. ', 'X ', ex)): bad.append(tag + ('looks like two sentences', ex))
        if len(ex) > 85: bad.append(tag + ('sentence over 85 characters', len(ex)))
        if len(mn) > 40: bad.append(tag + ('meaning over 40 characters', mn))
        if len(w) > 22: bad.append(tag + ('answer over 22 characters',))
        same = [x for x in items if x is not it and x.get('k', 'word') == it['k'] and not clash(x['w'], w)]
        if not any(not clash(x['w'], y['w']) for x in same for y in same if x is not y):
            bad.append(tag + ('not enough same-kind wrong answers',))
    return bad

def main():
    levels, problems = [], []
    for lid, fname, name in LEVELS:
        deck = json.load(open(os.path.join(DECKS, fname)))
        problems += check(lid, deck)
        levels.append({'id': lid, 'name': name, 'groups': deck.get('groups', []),
                       'items': [{k: v for k, v in it.items() if k in ('w', 'means', 'ex', 'k')} for it in deck['items']]})
        print(f'{name}: {len(deck["items"])} cards')
    if problems:
        print('\nProblems:')
        for p in problems: print('  ', p)
        sys.exit(1)
    tpl = open(os.path.join(HERE, 'template.html')).read().replace('__LEVELS__', json.dumps(levels, ensure_ascii=False)).replace('__CATS__', json.dumps([{'id': c[0], 'name': c[2], 'soon': not c[1]} for c in CATS], ensure_ascii=False))
    top, body = tpl.split('<style>', 1)              # title + font links move into <head>
    top = '\n'.join(l for l in top.splitlines() if 'claude:' not in l)
    head = open(os.path.join(HERE, 'head.html')).read().replace('</head>', top.strip() + '\n</head>')
    body = '<style>' + body
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    open(os.path.join(ROOT, 'docs', 'index.html'), 'w').write(head + body + '\n</body>\n</html>\n')
    print('wrote docs/index.html')

if __name__ == '__main__':   # so tools/checkdeck.py can import check() without rebuilding
    main()
