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

# The decks the daily draws from (Morg, Oct 16, 2026: every soccer deck plus both slang decks, no Taylor Swift), and the
# categories their tiles show, from the library's one list (build/library/categories.json, Morg, Oct 31, 2026: categories
# are reference tags, picked from one curated list). Its decks, in order, are DAILY: (id, league, flags), where
#   league: the draw allows at most LEAGUE_MAX cards a day from one league (2 since nine cards, Oct 27, 2026, LEAGUE_MAX below) ('' for none, '*' for one per card, from its source site)
#   women:  every card in the deck counts as a women's game card (elsewhere a card says so itself, with "women": true)
#   rules:  every card in the deck counts as a rules card
#   slang:  at most one slang card a day across these decks (Morg, Oct 16, 2026), and never a red one
LIBRARY = os.path.join(HERE, 'library')
CATS = json.load(open(os.path.join(LIBRARY, 'categories.json')))
CATEGORY = {c['id']: c for c in CATS['categories']}
DECK_CAT = {d['id']: d['category'] for d in CATS['decks']}   # each deck's own category, shown on its tiles
DAILY = [(d['id'], d.get('league', ''), ' '.join(d.get('flags', []))) for d in CATS['decks']]
FLAGS = ('women', 'rules', 'slang')
WRONG = os.path.join(LIBRARY, 'wrong.json')   # the wrong answers, as their own sets (Morg, Oct 31, 2026: "all wrong answers are a separate database")
SITE_LEAGUE = {'premierleague.com': 'epl', 'laliga.com': 'laliga', 'bundesliga.com': 'bundesliga', 'legaseriea.it': 'seriea',
               'ligue1.com': 'ligue1', 'ligamx.net': 'ligamx', 'mlssoccer.com': 'mls', 'nwslsoccer.com': 'nwsl'}
VET = os.path.join(HERE, 'vetting')
REVIEWERS = ('soccer', 'editor', 'facts')   # the soccer expert, the writing editor and the fact checker (Morg, Oct 16, 2026)
BETA_VETTED_ONLY = True   # True once the first vetting pass is done: until then every card that isn't out or flagged plays
BETA_MIN = 48              # with BETA_VETTED_ONLY, the build stops if a color has fewer cards than this (twice the draw's window)
START = [2026, 10, 30]   # the date of puzzle #1: the day the daily came back as a loop of Morg's nine (Oct 30, 2026), so the #1 finished that day carries over. It was Oct 28, the first full nine-card day. Before it, #1 plays early. After the playtest, launch day is #1 again.
DEMO_DAYS = 0             # off since Oct 19, 2026: the playtest is a real daily, one board a day (Morg). It was 7: boards #1 to #7 back to back, then a
                          # thank-you and Start over. The date doesn't move it. 0 for the real daily, one board a day from START
ONE_BOARD = False         # True: one fixed board (Morg, Oct 28, 2026), every date plays #1 and the countdown hides. Off since Oct 30, 2026,
                          # when the daily came back underneath LOOP below. False for the daily, one board a day
LOOP = 1                  # every day replays this board, its nine cards and their three choices each, while the daily runs for real around it:
                          # a new number each day, the countdown, midnight and Play #N (Morg, Oct 30, 2026: test the daily before its boards are
                          # ready). 0 deals the daily's own boards. Passed to the page as LOOP
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
    if 'tag' in it and it['tag'] not in CATEGORY: bad.append(tag + ('tag is not a category on the list: pick one from build/library/categories.json, or add the category there first', it['tag']))
    if 'wr' in it:   # Morg's own wrong answers: exactly two, different from each other and from the answer, and not already on the card (the audit, Oct 30, 2026)
        ws = [x if isinstance(x, str) else (x or {}).get('w', '') for x in (it['wr'] if isinstance(it['wr'], list) else [])]
        if len(ws) != 2 or not all(ws) or plain(ws[0]) == plain(ws[1]): bad.append(tag + ('wr must be two different wrong answers', it['wr']))
        elif any(plain(x) == plain(w) for x in ws): bad.append(tag + ('a wrong answer in wr is the answer itself', ws))
        elif any(shown(x, it) for x in ws): bad.append(tag + ('a wrong answer in wr is already in the sentence or on the tile', ws))
        for x in ws:
            if ';' in x or re.search(r"['\"]", x) or len(x) > 22: bad.append(tag + ('a wrong answer in wr breaks the house style (no semicolons, curly quotes only, 22 characters at most)', x))
    same = [e['w'] for e in set_entries(level, items, set_id(level, it)) if e['live'] and not clash(e['w'], w)]   # an answer whose card is out is never offered
    if not it.get('out') and len(it.get('wr') or []) < 2 and not any(not clash(a, b) for x, a in enumerate(same) for y, b in enumerate(same) if x != y):   # Morg's own two wrong answers (wr) need no set to draw from
        bad.append(tag + (f'not enough wrong answers in its set {set_id(level, it)} (build/library/wrong.json): it needs two that could never fill each other’s blank',))
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

# ---- the wrong answers, as their own sets (build/library/wrong.json, Morg, Oct 31, 2026) ----
# Each set has an id, <deck>/<kind>, a name, a note and its entries: {w, from: "<deck>:<i>"}, an answer borrowed from a card of
# the set's deck, its meaning line that card's means (so a reworded card never leaves a stale copy), or {w, m}, a wrong answer
# with a meaning of its own. A card draws from the set its k names in its deck. An answer joins a set only when Morg or the
# desk adds it: a new card never joins one by itself, and a card going out stays in every set it's in. A borrowed entry shows
# only with vetted wording: while its card sits out, it borrows from the first card that plays with its answer in the set's kind
# (main(), stand_in). Seeded on Oct 31,
# 2026 from the kinds as they were (every answer of each kind's cards not out), so no fingerprint or choice moved.
def load_sets(path=WRONG):
    return load_json(path, {'sets': []})

SETS = None   # the sets as loaded (wrong_sets() below), or as a tool set them for a trial
def wrong_sets():
    global SETS
    if SETS is None: SETS = load_sets()
    return SETS

def save_sets(data, path=WRONG):
    """One entry a line, so two branches that touch different sets merge cleanly."""
    global SETS
    out = ['{', ' "@note": ' + json.dumps(data.get('@note', ''), ensure_ascii=False) + ',', ' "sets": [']
    for n, st in enumerate(data['sets']):
        head = json.dumps({k: st[k] for k in st if k != 'entries'}, ensure_ascii=False)[:-1]
        rows = [json.dumps(e, ensure_ascii=False) for e in st.get('entries', [])]
        out.append('  ' + head + ', "entries": [' + ('\n   ' + ',\n   '.join(rows) + '\n  ' if rows else '') + ']}' + (',' if n < len(data['sets']) - 1 else ''))
    open(path, 'w').write('\n'.join(out + [' ]', '}']) + '\n')
    SETS = data

def set_id(did, it):
    """The set a card draws its wrong answers from: its kind (k) in its deck."""
    return f"{did}/{it.get('k', 'word')}"

def set_entries(did, items, sid=None, sets=None):
    """The entries of a deck's sets (or of the one set sid), each as {sid, w, m, i, live}: m is None and i the card's place
    for an entry borrowed from a card, whose answer it reads from the card as it is now, and live says whether it can show
    (its card isn't out). Unknown cards are skipped here and refused by wrong_problems(). sets: a trial copy of the sets
    (a tool weighing a change), or None for the file's."""
    out = []
    for st in (sets or wrong_sets())['sets']:
        if not st['id'].startswith(did + '/') or (sid and st['id'] != sid): continue
        for e in st.get('entries', []):
            if 'from' in e:
                d, _, i = str(e['from']).partition(':')
                if d != did or not i.isdigit() or int(i) >= len(items): continue
                c = items[int(i)]
                out.append({'sid': st['id'], 'w': c['w'], 'm': None, 'i': int(i), 'live': not c.get('out')})
            else: out.append({'sid': st['id'], 'w': e.get('w', ''), 'm': e.get('m', ''), 'i': None, 'live': True})
    return out

def draws(did, deck, it, clash=None, sets=None):
    """The wrong answers the game may put on this card's other two buttons, as (answer, own meaning or None): from its set,
    never clashing with its answer and never already in its sentence or on its tile. When its set has fewer than two that
    can show, the deck's other sets fill in, as the page's choices() does."""
    if it.get('wr'): return [(x if isinstance(x, str) else x['w'], None) for x in it['wr']]   # Morg's own two wrong answers, and only those
    clash = clash or clasher(deck)
    mine, every = set_id(did, it), [e for e in set_entries(did, deck['items'], sets=sets) if not clash(e['w'], it['w']) and not shown(e['w'], it)]
    same = [e for e in every if e['sid'] == mine]
    if len({e['w'] for e in same if e['live']}) < 2: same += [e for e in every if e['sid'] != mine]
    out = {}
    for e in same: out.setdefault(e['w'], set()).add(e['m'])
    return [(w, m) for w, ms in out.items() for m in sorted(ms, key=lambda m: (m is not None, m or ''))]

def wrong_pool(did, deck, it, clash=None, sets=None):
    """The answers this card can be offered as wrong (draws() above), what its reviewers see."""
    return list(dict.fromkeys(w for w, _ in draws(did, deck, it, clash, sets)))

def wrong_problems(data=None):
    """What's wrong with the sets: an id that names no deck, a set listed twice or with an answer twice, an entry borrowed
    from no card, from another deck's card or with another answer than its card has now, and any house-style slip in a
    wrong answer or meaning of its own (no semicolons, curly quotes only, 22 characters for an answer, 40 for a meaning)."""
    bad, seen = [], set()
    data = data or wrong_sets()
    if not isinstance(data.get('sets'), list): return ['build/library/wrong.json needs a list of sets']
    for st in data['sets']:
        sid = str(st.get('id', ''))
        did, _, k = sid.partition('/')
        if did not in DECK_CAT or not k: bad.append(f'set {sid!r}: an id is <deck>/<kind>, with a deck on the library’s list'); continue
        if sid in seen: bad.append(f'set {sid}: listed twice')
        seen.add(sid)
        if not str(st.get('name', '')).strip() or not isinstance(st.get('note', ''), str): bad.append(f'set {sid}: it needs a name, and its note is text')
        if set(st) - {'id', 'name', 'note', 'entries'} or not isinstance(st.get('entries'), list): bad.append(f'set {sid}: id, name, note and a list of entries only'); continue
        items, answers = json.load(open(os.path.join(DECKS, did + '.json')))['items'], set()
        for e in st['entries']:
            w = e.get('w') if isinstance(e, dict) else None
            if not isinstance(w, str) or not w or set(e) - {'w', 'from', 'm'} or ('from' in e) == ('m' in e):
                bad.append(f'set {sid}: {e!r}: an entry is {{w, from}} or {{w, m}}'); continue
            if 'from' in e:
                d, _, i = str(e['from']).partition(':')
                if d != did or not i.isdigit() or int(i) >= len(items): bad.append(f'set {sid}: {w} borrows from {e["from"]}, not a card of {did}')
                elif items[int(i)]['w'] != w: bad.append(f'set {sid}: {w} borrows from {e["from"]}, whose answer is now {items[int(i)]["w"]}: update the entry')
            else:
                m = e['m']
                if not isinstance(m, str) or len(m) > 40: bad.append(f'set {sid}: {w}: its meaning is text, 40 characters at most')
                for x in (w, m if isinstance(m, str) else ''):
                    if ';' in x or re.search(r"['\"]", x): bad.append(f'set {sid}: {x!r}: no semicolons, curly quotes only')
                if len(w) > 22: bad.append(f'set {sid}: {w}: an answer is 22 characters at most')
            if plain(w) in answers: bad.append(f'set {sid}: {w} is in it twice')
            answers.add(plain(w))
    return bad

# ---- vetting ----
HASHED = ('w', 'ex', 'means', 'hook', 'd', 'k')   # what a player sees of a card, and the kind that picks its wrong answers
def card_hash(it, pool, own=()):
    """A short fingerprint of a card and the wrong answers it can draw. A verdict or a lock holds only while the card still
    has the fingerprint it was given for, so a change to the card, or to the answers it can be offered, sends it back.
    own: the [answer, meaning] pairs of set entries with a meaning of their own, which show after a wrong pick, so they
    count too (a borrowed meaning is its card's means, which that card's own fingerprint covers)."""
    wm = [x.get('m', '') for x in it.get('wr') or [] if isinstance(x, dict)]   # a wrong answer's own meaning shows after a wrong pick, so it counts too
    return hashlib.sha1(json.dumps([it.get(k, 'word' if k == 'k' else None) for k in HASHED] + [sorted(pool)] + ([wm] if wm else []) + ([sorted(own)] if own else []), ensure_ascii=False).encode()).hexdigest()[:10]

def fingerprint(did, deck, i, clash=None, sets=None):
    d = draws(did, deck, deck['items'][i], clash, sets)
    return card_hash(deck['items'][i], list(dict.fromkeys(w for w, _ in d)), [[w, m] for w, m in d if m is not None])

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

def tile_tag(cat):
    """The tag.* string id a category shows on its tiles, less its tag. prefix: what the page’s TAG and a card’s own tag hold."""
    return CATEGORY[cat]['tag'].removeprefix('tag.') if cat in CATEGORY else cat

def tag_js():
    """The page's TAG, each deck's tile category, written the way the template wrote it by hand before Oct 31, 2026."""
    key = lambda k: k if re.fullmatch(r'[a-z_][a-z0-9_]*', k) else repr(k)
    return '{ ' + ', '.join(f'{key(did)}: {tile_tag(DECK_CAT[did])!r}' for did, _, _ in DAILY) + ' }'

def category_problems(text):
    """What's wrong with the library's category list (build/library/categories.json): every category has a name and its
    tag string in build/text, every deck has its file and names a category on the list, and a category with no deck of
    its own names the deck its new cards go to. A card's own tag is checked with the card (item_problems)."""
    bad, seen = [], set()
    for c in CATS['categories']:
        cid = c.get('id', '')
        if not re.fullmatch(r'[a-z0-9-]{1,30}', cid): bad.append(f'category {cid!r}: an id is lowercase letters, digits and hyphens')
        if cid in seen: bad.append(f'category {cid}: on the list twice')
        seen.add(cid)
        if not str(c.get('name', '')).strip(): bad.append(f'category {cid}: no name')
        if not str(c.get('tag', '')).startswith('tag.') or c['tag'] not in text: bad.append(f'category {cid}: its tag {c.get("tag")} is not a string in build/text/en.json (add it with a note and the tag slot: Morg approves it)')
        if c.get('home') and c['home'] not in DECK_CAT: bad.append(f'category {cid}: its home {c["home"]} is not a deck on the list')
        if not c.get('home') and cid not in DECK_CAT.values(): bad.append(f'category {cid}: no deck of its own, so it needs a home, the deck its new cards go to')
    seen = set()
    for d in CATS['decks']:
        if d['id'] in seen: bad.append(f'deck {d["id"]}: on the list twice')
        seen.add(d['id'])
        if d.get('category') not in CATEGORY: bad.append(f'deck {d["id"]}: its category {d.get("category")} is not on the list')
        if not os.path.exists(os.path.join(DECKS, d['id'] + '.json')): bad.append(f'deck {d["id"]}: no file build/decks/{d["id"]}.json')
        if not isinstance(d.get('league', ''), str) or set(d.get('flags', [])) - set(FLAGS): bad.append(f'deck {d["id"]}: league must be a string, flags only ' + ', '.join(FLAGS))
    return bad

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
        if not n.isdigit() or int(n) < (1 if ONE_BOARD or LOOP else 2): bad.append(f'board {n}: boards are puzzle numbers from 2 (#1 stays as dealt), or #1 while ONE_BOARD or LOOP replays it')
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
    pin = json.load(open(os.path.join(ROOT, '.claude', 'settings.json'))).get('env', {}).get('CLAUDE_CODE_EFFORT_LEVEL')
    if pin:   # an effort level in the settings file must never reach daily (playbook 4: Morg sets each level in the app)
        sys.exit(f'.claude/settings.json sets CLAUDE_CODE_EFFORT_LEVEL ({pin}): remove it before building (branch pins are retired, playbook 4)')
    text, meta = strings.load()   # every word but the cards: build/text/en.json (research/text-system.md)
    bad = category_problems(text)
    if bad:
        print('\nProblems with build/library/categories.json:'); [print('  ', b) for b in bad]; sys.exit(1)
    bad = wrong_problems()
    if bad:
        print('\nProblems with build/library/wrong.json:'); [print('  ', b) for b in bad]; sys.exit(1)
    decks, problems, tiers, wrong = [], [], [0, 0, 0], {}
    verdicts, marks = vetting()
    stand = {}
    for did, lg, flags in DAILY:
        if not re.fullmatch(r'[a-z0-9-]{1,30}', did): problems.append((did, '', 'a deck id must be lowercase letters, digits and hyphens (the beta’s services and results refuse anything else)'))
        deck = json.load(open(os.path.join(DECKS, did + '.json')))
        problems += check(did, deck, hooks=True)
        items, clash = [], clasher(deck)
        for i, it in enumerate(deck['items']):
            cid, h = f'{did}:{i}', fingerprint(did, deck, i, clash)
            st = stand[cid] = standing(cid, it, h, verdicts, marks)
            m = marks.get(cid)
            if st == 'locked' and m['h'] != mark_hash(it): problems.append((did, it['w'], 'locked by Morg but changed since: undo the change or ask him to unlock it'))
            if st in ('out', 'flagged') or (BETA_VETTED_ONLY and st == 'pending' and not test_copy): continue
            x = {k: it[k] for k in ('w', 'means', 'ex', 'k', 'hook', 'd', 'wr') if k in it}   # wr: Morg's own wrong answers
            if 'tag' in it: x['tag'] = tile_tag(it['tag'])   # the card's own category, over its deck's, as its tile string
            x['i'], x['h'] = i, mark_hash(it)   # the card's place in its deck and the fingerprint its marks hold to: the beta's flag and lock keys send both
            if st == 'locked': x['lk'] = 1
            if lg == '*': x['lg'] = league(lg, it)
            if it.get('women'): x['wm'] = 1
            items.append(x)
            if it.get('d') in (1, 2, 3) and not ('slang' in flags and it['d'] == 3): tiers[it['d'] - 1] += 1
        plays = {x['i']: x.get('k', 'word') for x in items}   # a borrowed wrong answer shows only while its card plays: [kind, its card's place], or [kind, answer, meaning] of its own
        def stand_in(e):
            """A borrowed entry whose card sits out (pending or flagged) borrows from the first card that plays with the same answer
            in the set's kind, as the page drew before the sets, so a card in review never takes its answer off its deck-mates."""
            if e['i'] is None or e['i'] in plays: return e
            k = e['sid'].partition('/')[2]
            j = next((j for j in sorted(plays) if plays[j] == k and deck['items'][j]['w'] == e['w']), None)
            return j is not None and dict(e, i=j)
        es = sorted(filter(None, map(stand_in, set_entries(did, deck['items']))), key=lambda e: (e['i'] is None, e['i'] or 0))   # in the cards' order, as the page drew them before the sets
        wrong[did] = [[e['sid'].partition('/')[2], e['i']] if e['i'] is not None else [e['sid'].partition('/')[2], e['w'], e['m']] for e in es]
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
    elif LOOP: print(f'The daily runs, and every day replays board #{LOOP}, its cards and choices (LOOP in build.py, 0 for the daily’s own boards).')
    pins = pinned(decks)
    tpl = open(os.path.join(HERE, 'template.html')).read()
    if 'var WRONG = __WRONG__;' not in tpl: sys.exit('build/template.html must take its wrong answers from the build (var WRONG = __WRONG__;): the sets live in build/library/wrong.json')
    if 'var TAG = __TAG__;' not in tpl: sys.exit('build/template.html must take its TAG from the build (var TAG = __TAG__;): the categories live in build/library/categories.json')
    tpl = tpl.replace('__TAG__', tag_js())   # each deck's tile category, from the library's list, so a deck can't show a blank one
    slots = strings.load_slots()   # every place text appears: build/text/slots.json
    bad = strings.problems(text, meta, tpl) + strings.slot_problems(slots, meta)
    if bad:
        print('\nText problems (build/text/en.json):')
        for p in bad: print('  ', p)
        sys.exit(1)
    print(f'Text: {len(text)} strings in {len(slots)} slots')
    tpl = tpl.replace('/*__TYPE__*/', strings.slot_css(slots)).replace('__FIT__', json.dumps(strings.slot_fit(slots)))
    pm, ps = strings.page_meta(meta, slots)
    tpl = tpl.replace('__TEXTMETA__', json.dumps(pm, ensure_ascii=False).replace('</', '<\\/')).replace('__SLOTS__', json.dumps(ps, ensure_ascii=False))
    tpl = tpl.replace('__PIN__', json.dumps(pins)).replace('__WRONG__', json.dumps(wrong, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
    tpl = tpl.replace('__TEXT__', json.dumps(text, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
    tpl = tpl.replace('__DECKS__', json.dumps(decks, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')).replace('__WINDOW__', str(WINDOW)).replace('__LEAGUE_MAX__', str(LEAGUE_MAX)).replace('__START__', json.dumps(START)).replace('__DEMO__', str(DEMO_DAYS)).replace('__PER__', str(PER)).replace('__ONE__', 'true' if ONE_BOARD else 'false').replace('__LOOP__', str(int(LOOP)))
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
