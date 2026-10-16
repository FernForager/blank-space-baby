"""Build Triviela, the daily soccer trivia game.

    python3 build/build.py

Reads build/template.html, build/head.html and the decks in build/decks/,
checks every card against the house style and the hook rules, and writes docs/index.html
(the live page). Stops with a list of problems if any card breaks a rule.
"""
import json, os, re, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECKS = os.path.join(HERE, 'decks')

# The decks the daily draws from (Morg, Oct 16, 2026: every soccer deck plus both slang decks, no Taylor Swift).
#   league: the draw allows at most 3 cards a day from one league ('' for none, '*' for one per card, from its source site)
#   women:  every card in the deck counts as a women's game card (elsewhere a card says so itself, with "women": true)
#   rules:  every card in the deck counts as a rules card
#   slang:  at most one slang card a day across these decks (Morg, Oct 16, 2026), and never a red one
DAILY = [
    # id            league         flags
    ('alpha',      '',            'slang'),
    ('parents',    '',            'slang'),
    ('basics',     'basics',      ''),        # Soccer 101: all white, capped at 3 a day like a league
    ('soccer',     '',            ''),
    ('lingo-more', '',            ''),
    ('rules',      '',            'rules'),
    ('epl',        'epl',         ''),
    ('epl-more',   'epl',         ''),
    ('laliga',     'laliga',      ''),
    ('bundesliga', 'bundesliga',  ''),
    ('seriea',     'seriea',      ''),
    ('ligue1',     'ligue1',      ''),
    ('ligamx',     'ligamx',      ''),
    ('mls',        'mls',         ''),
    ('nwsl',       'nwsl',        'women'),
    ('ucl',        'ucl',         ''),
    ('nicknames',  '*',           ''),
    ('intl-men',   '',            ''),
    ('intl-women', '',            'women'),
    ('wc26',       '',            ''),
    ('legends',    '',            ''),
    ('awards',     '',            ''),
]
SITE_LEAGUE = {'premierleague.com': 'epl', 'laliga.com': 'laliga', 'bundesliga.com': 'bundesliga', 'legaseriea.it': 'seriea',
               'ligue1.com': 'ligue1', 'ligamx.net': 'ligamx', 'mlssoccer.com': 'mls', 'nwslsoccer.com': 'nwsl'}
START = [2026, 10, 16]   # the date of puzzle #1: launch day (Morg, Oct 16, 2026). A placeholder until that date is set.
REPEAT_DAYS = 91          # a card never comes back within 3 months, once there are enough cards
WINDOW = 24               # the draw deals from a shuffle of each color's 24 oldest cards (WINDOW in template.html)

def rx(w):
    return re.compile(r'(^|[^A-Za-z0-9])(' + re.escape(w) + r')(?![A-Za-z0-9])', re.I)

HOOK_MAX = 12
def words(s): return re.findall(r'[\w’]+', s.lower())
def holds(a, b): return bool(b) and any(a[i:i + len(b)] == b for i in range(len(a) - len(b) + 1))   # word list b sits inside word list a

def hook_problems(it):
    """What's wrong with a card's hook (the word on its tile) and difficulty d. The rules are in build/decks/SPEC.md."""
    h, w, ex, bad = it.get('hook'), it['w'], it['ex'], []
    if not isinstance(h, str) or not h.strip(): bad.append('missing hook')
    else:
        if h != h.strip() or '  ' in h: bad.append('extra spaces in hook')
        if len(h) > HOOK_MAX: bad.append(f'hook over {HOOK_MAX} characters')
        if re.search(r"['\"]", h): bad.append('straight quote in hook')
        if re.match(r'(the|a|an)\s', h, re.I): bad.append('hook starts with the, a or an')
        if not re.search(r'(?<![\w’-])' + re.escape(h) + r'(?![\w-])', ex, re.I): bad.append('hook is not in the sentence')
        hw, ww = words(h), words(w)
        if holds(hw, ww) or holds(ww, hw): bad.append('hook is, holds or is part of the answer')
    if it.get('d') not in (1, 2, 3): bad.append('missing or bad difficulty d (1–3)')
    if 'women' in it and it['women'] is not True: bad.append('women must be true or left out')
    return bad

def check(level, deck, hooks=False):
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
        if hooks: bad += [tag + (p, it.get('hook')) for p in hook_problems(it)]
        same = [x for x in items if x is not it and x.get('k', 'word') == it['k'] and not clash(x['w'], w)]
        if not any(not clash(x['w'], y['w']) for x in same for y in same if x is not y):
            bad.append(tag + ('not enough same-kind wrong answers',))
    return bad

def league(deck_league, it):
    if deck_league != '*': return deck_league
    return SITE_LEAGUE.get(urlparse(it['src']).netloc.removeprefix('www.'), '')

def main():
    decks, problems, tiers = [], [], [0, 0, 0]
    for did, lg, flags in DAILY:
        deck = json.load(open(os.path.join(DECKS, did + '.json')))
        problems += check(did, deck, hooks=True)
        items = []
        for it in deck['items']:
            x = {k: it[k] for k in ('w', 'means', 'ex', 'k', 'hook', 'd') if k in it}
            if lg == '*': x['lg'] = league(lg, it)
            if it.get('women'): x['wm'] = 1
            items.append(x)
            if it.get('d') in (1, 2, 3) and not ('slang' in flags and it['d'] == 3): tiers[it['d'] - 1] += 1
        decks.append({'id': did, 'lg': '' if lg == '*' else lg, 'wm': int('women' in flags), 'rl': int('rules' in flags),
                      'sl': int('slang' in flags), 'groups': deck.get('groups', []), 'items': items})
        print(f'{did}: {len(items)} cards')
    if problems:
        print('\nProblems:')
        for p in problems: print('  ', p)
        sys.exit(1)
    print('\nIn the draw:', ', '.join(f'{n} {c}' for n, c in zip(tiers, ('white', 'yellow', 'red'))))
    need = 6 * REPEAT_DAYS + WINDOW   # 6 a day for 3 months, plus the 24 oldest the draw shuffles from
    print(f'Cards can stay 3 months apart once each color has about {need} cards. Until then the draw spaces them as far apart as it can:')
    print(f'the smallest color ({min(tiers)} cards) repeats about every {(min(tiers) - WINDOW) // 6} days.')
    tpl = open(os.path.join(HERE, 'template.html')).read()
    tpl = tpl.replace('__DECKS__', json.dumps(decks, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')).replace('__START__', json.dumps(START))
    top, body = tpl.split('<style>', 1)              # title + font links move into <head>
    top = '\n'.join(l for l in top.splitlines() if 'claude:' not in l)
    head = open(os.path.join(HERE, 'head.html')).read().replace('</head>', top.strip() + '\n</head>')
    body = '<style>' + body
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    open(os.path.join(ROOT, 'docs', 'index.html'), 'w').write(head + body + '\n</body>\n</html>\n')
    print('wrote docs/index.html')

if __name__ == '__main__':   # so tools/checkdeck.py can import check() without rebuilding
    main()
