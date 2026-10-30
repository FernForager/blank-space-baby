"""Build Triviela, the daily soccer trivia game.

    python3 build/build.py
    python3 build/build.py --with-pending FILE   # a test copy that also plays cards still waiting on a reviewer

Reads build/template.html, build/head.html, the strings in build/text/ (build/strings.py checks them), the decks in build/decks/ and the verdicts in build/vetting/,
checks every card against the house style and the hook rules, and writes docs/index.html
(the live page). Stops with a list of problems if any card breaks a rule.

Which cards play (Morg, Oct 16, 2026): three Claude reviewers vet every card (REVIEWERS below, one file each in
build/vetting/), and a card plays in the beta once all three have approved its current wording. Morg plays the beta
and can flag a card (it leaves the beta until it changes or the flag is cleared) or lock it (it plays, and nobody may
change it). His marks live in build/vetting/morg.json, synced from the beta's database by tools/vet.py marks.
A card with "out": true never plays. tools/vet.py is how reviewers read cards and record verdicts.
"""
import hashlib, json, os, re, sys
import strings
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
VET = os.path.join(HERE, 'vetting')
REVIEWERS = ('soccer', 'editor', 'facts')   # the soccer expert, the writing editor and the fact checker (Morg, Oct 16, 2026)
BETA_VETTED_ONLY = True   # True once the first vetting pass is done: until then every card that isn't out or flagged plays
BETA_MIN = 48              # with BETA_VETTED_ONLY, the build stops if a color has fewer cards than this (twice the draw's window)
START = [2026, 10, 28]   # the date of puzzle #1 (nine cards went live on the night of Oct 27, 2026, at Morg's go, so #1 starts over on the 28th, the first full nine-card day). Before it, #1 plays early. After the playtest, launch day is #1 again.
DEMO_DAYS = 0             # off since Oct 19, 2026: the playtest is a real daily, one board a day (Morg). It was 7: boards #1 to #7 back to back, then a
                          # thank-you and Start over. The date doesn't move it. 0 for the real daily, one board a day from START
ONE_BOARD = True          # one fixed board until the game is tidy (Morg, Oct 28, 2026): every date plays #1, the countdown hides, and
                          # boards.json can pin #1's nine cards once Morg and Trivelle write them. False for the daily, one board a day
PER = 3                   # cards of each color a day (Morg, Oct 27, 2026: nine a day, three per color, was five): PER in template.html
REPEAT_DAYS = 91          # a card never comes back within 3 months, once there are enough cards
WINDOW = 24               # the draw deals from a shuffle of each color's 24 oldest cards (passed to the page as WINDOW)
LEAGUE_MAX = 2            # at most this many cards a day from one league, Basics included (passed to the page: 2 since nine cards, Oct 27, 2026, 3 of 15 before)

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

def clasher(deck):
    """Two answers clash when they're the same or share a group (they could fill each other's blanks)."""
    groups = {}
    for i, grp in enumerate(deck.get('groups', [])):
        for w in grp:
            groups.setdefault(w, set()).add(i)
    return lambda a, b: a == b or bool(groups.get(a, set()) & groups.get(b, set()))

def item_problems(level, items, clash, it, hooks=True):
    """Everything wrong with one card, as (deck, answer, problem, detail) tuples. items is its deck, for the wrong answers."""
    bad = []
    it.setdefault('k', 'word')
    w, ex, mn = it['w'], it['ex'], it['means']
    tag = (level, w)
    if len(rx(w).findall(ex)) != 1: bad.append(tag + ('answer must appear exactly once in the sentence', ex))
    for s in (ex, mn):
        if ';' in s: bad.append(tag + ('semicolon', s))
        if re.search(r"['\"]", s): bad.append(tag + ('straight quote or apostrophe', s))
    if ex.rstrip().endswith('.'): bad.append(tag + ('period at the end', ex))
    if re.search(r'[.!?][”"]?\s+[A-Z]', re.sub(r'\b(Mrs|Mr|Ms|No|St|vs|D\.C|U\.S)\. ', 'X ', ex)): bad.append(tag + ('looks like two sentences', ex))   # D.C. United, U.S. Soccer
    if len(ex) > 85: bad.append(tag + ('sentence over 85 characters', len(ex)))
    if len(mn) > 40: bad.append(tag + ('meaning over 40 characters', mn))
    if len(w) > 22: bad.append(tag + ('answer over 22 characters',))
    if hooks: bad += [tag + (p, it.get('hook')) for p in hook_problems(it)]
    if 'wr' in it:   # Morg's own wrong answers: exactly two, different from each other and from the answer, and not already on the card (the audit, Oct 30, 2026)
        ws = [x if isinstance(x, str) else (x or {}).get('w', '') for x in (it['wr'] if isinstance(it['wr'], list) else [])]
        if len(ws) != 2 or not all(ws) or plain(ws[0]) == plain(ws[1]): bad.append(tag + ('wr must be two different wrong answers', it['wr']))
        elif any(plain(x) == plain(w) for x in ws): bad.append(tag + ('a wrong answer in wr is the answer itself', ws))
        elif any(shown(x, it) for x in ws): bad.append(tag + ('a wrong answer in wr is already in the sentence or on the tile', ws))
        for x in ws:
            if ';' in x or re.search(r"['\"]", x) or len(x) > 22: bad.append(tag + ('a wrong answer in wr breaks the house style (no semicolons, curly quotes only, 22 characters at most)', x))
    same = [x for x in items if x is not it and not x.get('out') and x.get('k', 'word') == it['k'] and not clash(x['w'], w)]   # cut cards are never offered
    if not it.get('out') and len(it.get('wr') or []) < 2 and not any(not clash(x['w'], y['w']) for x in same for y in same if x is not y):   # Morg's own two wrong answers (wr) need no kind to draw from
        bad.append(tag + ('not enough same-kind wrong answers',))
    return bad

def check(level, deck, hooks=False):
    items, clash = deck['items'], clasher(deck)
    return [p for it in items for p in item_problems(level, items, clash, it, hooks)]

# ---- the wrong answers a card can draw (the same rules as choices() in template.html) ----
def plain(s):
    """Lowercase words with spaces round them, as the game compares them (template.html's plain)."""
    return ' ' + ' '.join(re.sub(r'[^0-9a-z\u00c0-\u024f]+', ' ', s.lower()).split()) + ' '

def shown(w, it):
    """Is the answer w already in this card's sentence (its own answer left out) or hook? Then it can't be one of its wrong answers."""
    return plain(w) in plain(it['ex']).replace(plain(it['w']), ' ', 1) + plain(it.get('hook') or '')

def wrong_pool(deck, it, clash=None):
    """The answers the game may put on this card's other two buttons: from its deck, not out, not clashing with its answer
    and not already in its sentence or on its tile. Same kind first, and any kind when the same kind has fewer than two."""
    if it.get('wr'): return [x if isinstance(x, str) else x['w'] for x in it['wr']]   # Morg's own two wrong answers, and only those
    clash = clash or clasher(deck)
    ok = lambda x: not x.get('out') and not clash(x['w'], it['w']) and not shown(x['w'], it)
    same = list(dict.fromkeys(x['w'] for x in deck['items'] if x.get('k', 'word') == it.get('k', 'word') and ok(x)))
    if len(same) >= 2: return same
    return same + list(dict.fromkeys(x['w'] for x in deck['items'] if x.get('k', 'word') != it.get('k', 'word') and ok(x) and x['w'] not in same))

# ---- vetting ----
HASHED = ('w', 'ex', 'means', 'hook', 'd', 'k')   # what a player sees of a card, and the kind that picks its wrong answers
def card_hash(it, pool):
    """A short fingerprint of a card and the wrong answers it can draw. A verdict or a lock holds only while the card still
    has the fingerprint it was given for, so a change to the card, or to the answers it can be offered, sends it back."""
    wm = [x.get('m', '') for x in it.get('wr') or [] if isinstance(x, dict)]   # a wrong answer's own meaning shows after a wrong pick, so it counts too
    return hashlib.sha1(json.dumps([it.get(k, 'word' if k == 'k' else None) for k in HASHED] + [sorted(pool)] + ([wm] if wm else []), ensure_ascii=False).encode()).hexdigest()[:10]

def fingerprint(deck, i, clash=None):
    return card_hash(deck['items'][i], wrong_pool(deck, deck['items'][i], clash))

# ---- near misses: the same rules as near2() in template.html, in words, so a reviewer sees what a number card draws ----
HEDGE = re.compile(r'\b(more than|at least|nearly|almost|about|around|roughly|some|up to|over|under)\s+$', re.I)
SPELLED = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
           'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty']
def near_rule(it):
    """How the page makes up a number card's two wrong answers (near2 in template.html), in words, or None for a card that draws
    them from its deck: a card with its own wr, a word answer, or a number right after a hedge (more than, about). The deck's
    pool is still the fallback when the page can't make two near misses, so wrong_pool matters for these cards too."""
    w = str(it['w']); sp = SPELLED.index(w) if w in SPELLED else -1
    if it.get('wr') or (sp < 2 and not re.fullmatch(r'\d[\d,]*', w)): return None
    at = it['ex'].find(w)
    if at >= 0 and HEDGE.search(it['ex'][:at]): return None
    a = sp if sp >= 2 else int(w.replace(',', ''))
    year = sp < 2 and ('year' in it.get('k', 'word') or (re.fullmatch(r'\d{4}', w) and 1850 < a < 2100))
    if sp >= 2: return 'two spelled counts 1 to 3 off, never above twenty'
    if year: return 'two years ' + ('4 or 8' if re.search(r'World Cup|Euro\b|Olympic', it['ex']) else '1 to 10') + ' off, never past the puzzle’s own year unless the answer is'
    if a <= 12: return 'two counts 1 to 3 off'
    return 'two numbers 10 to 35 percent off, at the answer’s own roundness'

def mark_hash(it):
    """The fingerprint Morg's flags and locks hold to: the card's own fields alone (what a player sees, its kind, and his own
    wrong answers with their meanings), never the wrong answers its deck-mates lend it. A reviewer's verdict covers those
    too (card_hash), so a deck-mate's change sends a card back to the reviewers but never lapses a flag or breaks a lock
    (the audit, Oct 30, 2026: before, a lock stopped the build when only a deck-mate changed)."""
    wr = [[x, ''] if isinstance(x, str) else [x.get('w'), x.get('m', '')] for x in it.get('wr') or []]
    return hashlib.sha1(json.dumps([it.get(k, 'word' if k == 'k' else None) for k in HASHED] + [wr], ensure_ascii=False).encode()).hexdigest()[:10]

def load_json(path, default):
    try: return json.load(open(path))
    except FileNotFoundError: return default

def vetting():
    """Every reviewer's verdicts ({card id: {v, h, note, fix, at}}) and Morg's marks ({card id: {m, h, note, at}}).
    A reviewer's own fix, once the desk applies it exactly as proposed (tools/vet.py take), counts as that reviewer's
    ok on the new wording: the desk records it in desk.json ({card id: {who: {h, at}}}), since only reviewers write
    their own files. Whichever is newer, the reviewer's verdict or the desk's record, stands."""
    verdicts = {who: load_json(os.path.join(VET, who + '.json'), {}) for who in REVIEWERS}
    for cid, takes in load_json(os.path.join(VET, 'desk.json'), {}).items():
        for who, t in takes.items():
            v = verdicts.get(who, {}).get(cid)
            if who not in verdicts or (v and v.get('at', '') > t['at']): continue
            if t.get('declined'): verdicts[who].pop(cid, None)   # the desk turned the fix down: the card goes back to its reviewer
            else: verdicts[who][cid] = {'v': 'ok', 'h': t['h'], 'at': t['at'], 'note': 'its own fix, applied as proposed'}
    return verdicts, load_json(os.path.join(VET, 'morg.json'), {}).get('cards', {})

def standing(cid, it, h, verdicts, marks):
    """Where a card stands: out, locked, flagged, approved (all three reviewers said ok to this wording) or pending.
    h is the card's fingerprint (fingerprint() above), which the verdicts hold to. Morg's marks hold to mark_hash(it)."""
    m = marks.get(cid)
    if it.get('out'): return 'out'
    if m and m['m'] == 'lock': return 'locked'
    if m and m['m'] == 'flag' and m['h'] == mark_hash(it): return 'flagged'
    if all(verdicts[who].get(cid, {}).get('v') == 'ok' and verdicts[who][cid].get('h') == h for who in REVIEWERS): return 'approved'
    return 'pending'

def league(deck_league, it):
    if deck_league != '*': return deck_league
    return SITE_LEAGUE.get(urlparse(it['src']).netloc.removeprefix('www.'), '')

def pinned(decks):
    """Morg's own boards (build/boards.json): {"2": [9 card ids], ...}, puzzle number to its cards in board order, three green,
    then three yellow, then three red. Every card must be in the draw, in its spot's color, and on one board only."""
    raw = load_json(os.path.join(HERE, 'boards.json'), {})
    boards = {k: v for k, v in raw.items() if not k.startswith('@')}
    color = {f"{d['id']}:{x['i']}": x['d'] for d in decks for x in d['items'] if not (d['sl'] and x['d'] == 3)}   # red slang never deals, so the page would drop it from a pin too (the audit)
    bad, seen = [], {}
    for n, ids in boards.items():
        if not n.isdigit() or int(n) < (1 if ONE_BOARD else 2): bad.append(f'board {n}: boards are puzzle numbers from 2 (#1 stays as dealt), or #1 while ONE_BOARD holds one fixed board')
        if len(ids) != 3 * PER: bad.append(f'board #{n}: {len(ids)} cards, not {3 * PER}')
        for k, cid in enumerate(ids):
            if cid not in color: bad.append(f'board #{n}: {cid} is not in the draw (out, flagged, waiting on a reviewer, or no such card)'); continue
            if color[cid] != k // PER + 1: bad.append(f'board #{n}: {cid} is {("green", "yellow", "red")[color[cid] - 1]} but sits in spot {k + 1}')
            if cid in seen: bad.append(f'board #{n}: {cid} is on board #{seen[cid]} too')
            seen[cid] = n
    if bad:
        print('\nProblems with build/boards.json:'); [print('  ', b) for b in bad]; sys.exit(1)
    if boards: print('Pinned boards: ' + ', '.join('#' + n for n in sorted(boards, key=int)))
    return {int(n): ids for n, ids in boards.items()}

def main(test_copy=None):
    """Build the game into docs/index.html, or, given test_copy, into that file with pending cards playing too, so the
    desk can try a reworded card on a phone screen before the reviewers have passed it."""
    decks, problems, tiers = [], [], [0, 0, 0]
    verdicts, marks = vetting()
    stand = {}
    for did, lg, flags in DAILY:
        if not re.fullmatch(r'[a-z0-9-]{1,30}', did): problems.append((did, '', 'a deck id must be lowercase letters, digits and hyphens (the beta’s services and results refuse anything else)'))
        deck = json.load(open(os.path.join(DECKS, did + '.json')))
        problems += check(did, deck, hooks=True)
        items, clash = [], clasher(deck)
        for i, it in enumerate(deck['items']):
            cid, h = f'{did}:{i}', fingerprint(deck, i, clash)
            st = stand[cid] = standing(cid, it, h, verdicts, marks)
            m = marks.get(cid)
            if st == 'locked' and m['h'] != mark_hash(it): problems.append((did, it['w'], 'locked by Morg but changed since: undo the change or ask him to unlock it'))
            if st in ('out', 'flagged') or (BETA_VETTED_ONLY and st == 'pending' and not test_copy): continue
            x = {k: it[k] for k in ('w', 'means', 'ex', 'k', 'hook', 'd', 'wr', 'tag') if k in it}   # wr: Morg's own wrong answers. tag: the card's own category, over its deck's
            x['i'], x['h'] = i, mark_hash(it)   # the card's place in its deck and the fingerprint its marks hold to: the beta's flag and lock keys send both
            if st == 'locked': x['lk'] = 1
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
    counts = {k: list(stand.values()).count(k) for k in ('approved', 'locked', 'pending', 'flagged', 'out')}
    print('\nVetting:', ', '.join(f'{n} {k}' for k, n in counts.items()), '(the beta plays ' + ('only approved and locked cards)' if BETA_VETTED_ONLY else 'every card that isn’t out or flagged, until the first vetting pass is done)'))
    if BETA_VETTED_ONLY and min(tiers) < BETA_MIN:
        print(f'\nToo few vetted cards to deal a board: {tiers} (green, yellow, red), and each color needs {BETA_MIN}.'); sys.exit(1)
    print('In the draw:', ', '.join(f'{n} {c}' for n, c in zip(tiers, ('green', 'yellow', 'red'))))
    need = PER * REPEAT_DAYS + WINDOW   # PER a day of each color for 3 months, plus the 24 oldest the draw shuffles from
    print(f'Cards can stay 3 months apart once each color has about {need} cards. Until then the draw spaces them as far apart as it can:')
    print(f'the smallest color ({min(tiers)} cards) repeats about every {(min(tiers) - WINDOW) // PER} days.')
    if DEMO_DAYS: print(f'Demo: boards #1 to #{DEMO_DAYS} play back to back, then a thank-you (DEMO_DAYS in build.py, 0 for the real daily).')
    if ONE_BOARD: print('One fixed board: every date plays #1, with no countdown (ONE_BOARD in build.py, False for the daily).')
    pins = pinned(decks)
    tpl = open(os.path.join(HERE, 'template.html')).read()
    tagmap = re.search(r'var TAG = \{(.*?)\};', tpl, re.S)
    untagged = [did for did, lg, flags in DAILY if not tagmap or not re.search(r"(^|[\s{,])'?" + re.escape(did) + r"'?\s*:", tagmap.group(1))]
    if untagged: print('\nDecks with no category in the template’s TAG (their tiles would show a blank category):', ', '.join(untagged)); sys.exit(1)
    text, meta = strings.load()   # every word but the cards: build/text/en.json (research/text-system.md)
    slots = strings.load_slots()   # every place text appears: build/text/slots.json
    bad = strings.problems(text, meta, tpl) + strings.slot_problems(slots, meta)
    if bad:
        print('\nText problems (build/text/en.json):')
        for p in bad: print('  ', p)
        sys.exit(1)
    tagless = sorted({f"{d['id']}:{x['i']} tag {x['tag']}" for d in decks for x in d['items'] if 'tag' in x and 'tag.' + x['tag'] not in text})
    if tagless:
        print('\nCards with a tag build/text has no string for (add tag.<id> to en.json):'); [print('  ', t) for t in tagless]; sys.exit(1)
    print(f'Text: {len(text)} strings in {len(slots)} slots')
    tpl = tpl.replace('/*__TYPE__*/', strings.slot_css(slots)).replace('__FIT__', json.dumps(strings.slot_fit(slots)))
    pm, ps = strings.page_meta(meta, slots)
    tpl = tpl.replace('__TEXTMETA__', json.dumps(pm, ensure_ascii=False).replace('</', '<\\/')).replace('__SLOTS__', json.dumps(ps, ensure_ascii=False))
    tpl = tpl.replace('__PIN__', json.dumps(pins))
    tpl = tpl.replace('__TEXT__', json.dumps(text, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
    tpl = tpl.replace('__DECKS__', json.dumps(decks, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')).replace('__WINDOW__', str(WINDOW)).replace('__LEAGUE_MAX__', str(LEAGUE_MAX)).replace('__START__', json.dumps(START)).replace('__DEMO__', str(DEMO_DAYS)).replace('__PER__', str(PER)).replace('__ONE__', 'true' if ONE_BOARD else 'false')
    top, body = tpl.split('<style>', 1)              # title + font links move into <head>
    top = '\n'.join(l for l in top.splitlines() if 'claude:' not in l)
    head = strings.fill_head(open(os.path.join(HERE, 'head.html')).read().replace('</head>', top.strip() + '\n</head>'), text)
    mf = os.path.join(ROOT, 'docs', 'manifest.webmanifest'); man = json.load(open(mf))   # the Home Screen name
    if (man['name'], man['short_name']) != (text['brand'],) * 2:
        man['name'] = man['short_name'] = text['brand']; open(mf, 'w').write(json.dumps(man, indent=2, ensure_ascii=False) + '\n')
    body = '<style>' + body
    path = test_copy or os.path.join(ROOT, 'docs', 'index.html')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, 'w').write(head + body + '\n</body>\n</html>\n')
    print('wrote ' + (f'{path} (a test copy, with pending cards)' if test_copy else 'docs/index.html'))

if __name__ == '__main__':   # so tools/checkdeck.py can import check() without rebuilding
    a = sys.argv[1:]
    main(a[a.index('--with-pending') + 1] if '--with-pending' in a[:-1] else None)
