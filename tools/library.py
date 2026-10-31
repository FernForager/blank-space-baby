"""The library (Morg, Oct 31, 2026): every card and the pools they share, so the cards grow like one organism and stay
consistent with themselves. The repo stays the master copy: build/library/categories.json is the one list of categories,
the decks hold the cards, and this tool reads them all and writes what the Card Room shows.

    python3 tools/library.py                     # the pools' sizes and the consistency report, the top of each finding
    python3 tools/library.py report --all        # every finding in full
    python3 tools/library.py check               # exits 1 when a card still waiting on the reviewers breaks a clear rule below
    python3 tools/library.py export DIR          # library.json for the Card Room (the page beside it reads it), and dates the ledger
    python3 tools/library.py seed                # rebuilds the ledger's dates from git history (needs the whole history)
    python3 tools/library.py apply DIR [--dry]   # Morg's saved edits from the Card Room's database, into the decks

The pools, each built from every card that isn't out (pending and flagged cards count, since they're on their way in):
  categories     the curated list, with each one's cards by color and standing
  hooks          every tile word, with the cards behind it
  answers        every right answer, with its cards and kinds
  wrong answers  every answer a card can show as wrong (its kind's answers in its deck, or Morg's own wr), and the kinds
                 themselves. A number card gets two made-up near misses instead (build.py's near_rule), so it draws none.

The ledger (build/library/ledger.json) remembers when each card came in and when each of its fields last changed, seeded
from git history on Oct 31, 2026 and kept up by export, so the Card Room can show what grew lately. Commit it after export.
"""
import datetime, difflib, hashlib, json, os, re, subprocess, sys, unicodedata
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build as B, strings
LEDGER = os.path.join(B.LIBRARY, 'ledger.json')
SEATTLE = ZoneInfo('America/Los_Angeles')   # Morg's days: a card added at 9 pm in Seattle came in that day
TRACK = ('w', 'ex', 'means', 'hook', 'd', 'k', 'wr', 'tag')   # the fields the ledger dates
LATELY = 7   # days that count as lately in the Card Room
STATES = ('approved', 'locked', 'pending', 'flagged', 'out')
SAYS = re.compile(r'\b(soccer|football)', re.I)

def today(): return datetime.datetime.now(SEATTLE).date().isoformat()
def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def letters(s):
    """s in lowercase without accents, its punctuation kept."""
    s = unicodedata.normalize('NFKD', str(s)).casefold()
    return ''.join(c for c in s if not unicodedata.combining(c))

def key(s):
    """What two spellings of one entry share: case, accents, spaces, hyphens, dots and apostrophes dropped. A score keeps
    its dash, so 2–0 never meets 20."""
    return re.sub(r'[^0-9a-z]+', '', re.sub(r'(?<=\d)\s*[–-]\s*(?=\d)', 'x', letters(s)))

ENDINGS = ('', 's', 'es', 'd', 'ed', 'r', 'er', 'ing')
def inflected(a, b):
    """Two keys that are one word with two endings: corner and corners, replace and replaced, scored and scorer."""
    stem = os.path.commonprefix([a, b])
    return len(stem) >= 4 and a[len(stem):] in ENDINGS and b[len(stem):] in ENDINGS

def number(w): return bool(re.fullmatch(r'[\d,–-]+', w)) or w.lower() in B.SPELLED

def wrongs(it):
    """Morg's own wrong answers on a card, as plain strings."""
    return [x if isinstance(x, str) else (x or {}).get('w', '') for x in it.get('wr') or []]

# ---- every card, with where it stands ----
def cards():
    """Every card in the library's decks, in deck order, with its standing (build.py's), its category, the reviewers it's
    still waiting on and the wrong answers it can draw."""
    verdicts, marks = B.vetting()
    out = []
    for did, lg, flags in B.DAILY:
        deck = json.load(open(os.path.join(B.DECKS, did + '.json')))
        clash = B.clasher(deck)
        for i, it in enumerate(deck['items']):
            cid, h = f'{did}:{i}', B.fingerprint(deck, i, clash)
            st = B.standing(cid, it, h, verdicts, marks)
            wait = [w for w in B.REVIEWERS if not (verdicts[w].get(cid, {}).get('v') == 'ok' and verdicts[w][cid].get('h') == h)] if st == 'pending' else []
            out.append({'id': cid, 'deck': did, 'i': i, 'it': it, 'st': st, 'wait': wait, 'cat': it.get('tag') or B.DECK_CAT[did],
                        'pool': B.wrong_pool(deck, it, clash), 'near': B.near_rule(it), 'women': bool(it.get('women') or 'women' in flags),
                        'league': B.league(lg, it), 'mh': B.mark_hash(it), 'note': (marks.get(cid) or {}).get('note', '') if st == 'flagged' else ''})
    return out

# ---- the pools ----
def entry(pool, text, cid, field=None):
    e = pool.setdefault(key(text), {'forms': Counter(), 'cards': [], 'by': defaultdict(list)})
    e['forms'][text] += 1
    if cid not in e['cards']: e['cards'].append(cid)
    if field: e['by'][field].append(cid)

def shown_form(e):
    """The spelling an entry goes by: its most used one, then the one with capitals (a name), then A to Z."""
    return sorted(e['forms'], key=lambda f: (-e['forms'][f], f == f.lower(), f))[0]

def pools(cs):
    live = [c for c in cs if c['st'] != 'out']
    hooks, answers, wrong, kinds = {}, {}, {}, {}
    for c in live:
        it = c['it']
        entry(hooks, it['hook'], c['id'])
        entry(answers, it['w'], c['id'])
        k = kinds.setdefault((c['deck'], it.get('k', 'word')), {'answers': [], 'cards': [], 'own': 0})
        k['cards'].append(c['id'])
        if it['w'] not in k['answers']: k['answers'].append(it['w'])
        if it.get('wr'): k['own'] += 1
        if it.get('wr'):
            for x in wrongs(it): entry(wrong, x, c['id'], 'mine')
        elif not c['near']:
            for x in c['pool']: entry(wrong, x, c['id'], 'kind')
    return {'hook': hooks, 'answer': answers, 'wrong': wrong, 'kind': kinds}

def categories(cs, text):
    out = []
    for cat in B.CATS['categories']:
        mine = [c for c in cs if c['cat'] == cat['id']]
        decks = [d for d in B.CATS['decks'] if d['category'] == cat['id']]
        out.append({'id': cat['id'], 'name': cat['name'], 'tile': text.get(cat['tag'], ''), 'tag': cat['tag'], 'note': cat.get('note', ''),
                    'home': cat.get('home') or (decks[0]['id'] if decks else ''), 'decks': [d['id'] for d in decks],
                    'n': {st: [sum(1 for c in mine if c['st'] == st and c['it'].get('d') == d) for d in (1, 2, 3)] for st in STATES}})
    return out

# ---- the consistency report ----
def lev(a, b, cap):
    """Edit distance between a and b, or cap + 1 once it's sure to be more than cap."""
    if abs(len(a) - len(b)) > cap: return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1): cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        if min(cur) > cap: return cap + 1
        prev = cur
    return prev[-1]

def near_pairs(keys):
    """Pairs of different entries one or two letters apart (two for longer ones), never two numbers or years, nor a word
    and its own plural or tense."""
    ks, out = sorted(k for k in keys if len(k) >= 5), []
    for x in range(len(ks)):
        for y in range(x + 1, len(ks)):
            a, b = ks[x], ks[y]
            if abs(len(a) - len(b)) > 2: continue
            if (re.search(r'\d', a) and re.search(r'\d', b)) or inflected(a, b): continue
            if lev(a, b, 2 if min(len(a), len(b)) >= 8 else 1) <= (2 if min(len(a), len(b)) >= 8 else 1): out.append((a, b))
    return out

def blanked(it):
    """A card's sentence without its answer, for telling the same fact told twice."""
    return re.sub(r'\s+', ' ', B.rx(it['w']).sub(r'\1___', it['ex'])).lower()

def report(cs, P):
    """Every finding, as {code, pool, title, why, rule, items: [{text, cards}]}. rule: a clear rule, which check holds
    new and reworded cards to. The rest are for a person to look at: most are fine, some are slips."""
    by = {c['id']: c for c in cs}
    live = [c for c in cs if c['st'] != 'out']
    F = []
    def add(code, pool, title, why, items, rule=False):
        F.append({'code': code, 'pool': pool, 'title': title, 'why': why, 'rule': rule, 'items': items})
    q = lambda s: '“' + s + '”'
    forms = lambda e: ' and '.join(q(f) for f in sorted(e['forms']))
    case = lambda e: len({letters(f) for f in e['forms']}) < len(e['forms'])   # two forms apart only in capitals or accents
    marks = lambda e: len({letters(f) for f in e['forms']}) > 1   # two forms apart in hyphens, spaces or punctuation
    add('forms-hook', 'hook', 'Hooks with two capitals or accents', 'One tile word, one spelling: a hook lowercases a common word, and a name keeps its accents',
        [{'text': forms(e), 'cards': e['cards']} for e in P['hook'].values() if case(e)], rule=True)
    add('forms-answer', 'answer', 'Answers with two capitals or accents', 'One answer, one spelling, on every card that uses it',
        [{'text': forms(e), 'cards': e['cards']} for e in P['answer'].values() if case(e)], rule=True)
    add('marks-hook', 'hook', 'Hooks hyphenated or spaced two ways', 'Often the grammar (a hyphen before a noun: a top-flight club), sometimes a slip',
        [{'text': forms(e), 'cards': e['cards']} for e in P['hook'].values() if marks(e)])
    add('marks-answer', 'answer', 'Answers hyphenated or spaced two ways', 'Often the grammar, sometimes a slip',
        [{'text': forms(e), 'cards': e['cards']} for e in P['answer'].values() if marks(e)])
    clash = []
    for k, e in P['wrong'].items():   # a wrong answer spelled unlike the same answer on its own card
        a = P['answer'].get(k)
        if a and set(e['forms']) - set(a['forms']): clash.append({'text': ' and '.join(q(f) for f in sorted(set(e['forms']) | set(a['forms']))), 'cards': e['by'].get('mine', []) + a['cards']})
    add('forms-wrong', 'wrong', 'Wrong answers spelled unlike the answer', 'Morg’s own wrong answer and the same answer on another card, spelled two ways', clash, rule=True)
    kinds = defaultdict(set)
    for c in live: kinds[(c['deck'], key(c['it']['w']))].add(c['it'].get('k', 'word'))
    add('kinds-answer', 'answer', 'Answers in two kinds of one deck', 'An answer lends itself as a wrong answer to every card of its kind, so in two kinds it lends itself twice',
        [{'text': f'{q(shown_form(P["answer"][w]))} in {d}: ' + ', '.join(sorted(ks)), 'cards': [c for c in P['answer'][w]['cards'] if by[c]['deck'] == d]} for (d, w), ks in kinds.items() if len(ks) > 1])
    add('own-tag', 'category', 'A card’s own category repeats its deck’s', 'A card names a category only to show another one than its deck’s',
        [{'text': f'{c["id"]} names {c["it"]["tag"]}, its deck’s own', 'cards': [c['id']]} for c in cs if c['it'].get('tag') == B.DECK_CAT[c['deck']]], rule=True)
    answer_keys = set(P['answer'])
    add('hook-answer', 'hook', 'Hooks that are another card’s answer', 'Fine, and the draw keeps the two apart, but they can never share a board',
        [{'text': f'{q(shown_form(e))}, the answer on ' + ', '.join(P['answer'][k]['cards']), 'cards': e['cards'] + P['answer'][k]['cards']} for k, e in P['hook'].items() if k in answer_keys])
    for pool, name in (('hook', 'hooks'), ('answer', 'answers'), ('wrong', 'wrong answers')):   # among wrong answers, only Morg’s own: the rest are answers
        add('near-' + pool, pool, f'Near twins among the {name}', 'One or two letters apart: a typo, two names for one thing, or two names that look alike',
            [{'text': q(shown_form(P[pool][a])) + ' and ' + q(shown_form(P[pool][b])), 'cards': P[pool][a]['cards'] + P[pool][b]['cards']} for a, b in near_pairs(P[pool])
             if pool != 'wrong' or a not in P['answer'] or b not in P['answer']])
    same = []
    for k, e in P['answer'].items():
        ids = e['cards']
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                r = difflib.SequenceMatcher(None, blanked(by[ids[x]]['it']), blanked(by[ids[y]]['it'])).ratio()
                if r >= .6: same.append({'text': f'{q(shown_form(e))}: {ids[x]} and {ids[y]} ({round(r * 100)}% alike)', 'cards': [ids[x], ids[y]], 'r': r})
    add('same-fact', 'card', 'The same fact twice?', 'Two cards with one answer and sentences much alike: one fact lives in one deck',
        sorted(same, key=lambda s: -s['r']))
    thin, mixed = [], []
    for (d, k), e in P['kind'].items():
        if e['own'] == len(e['cards']): continue   # every card in it has Morg’s own two wrong answers
        if len(e['answers']) < 4: thin.append({'text': f'{d} {k}: {len(e["answers"])} answers (' + ', '.join(e['answers']) + ')', 'cards': e['cards']})
        nums = [a for a in e['answers'] if number(a)]
        if nums and len(nums) < len(e['answers']): mixed.append({'text': f'{d} {k}: ' + ', '.join(e['answers']), 'cards': e['cards']})
    add('thin-kind', 'wrong', 'Kinds too thin', 'A kind needs at least 4 answers (build/decks/SPEC.md), so its cards don’t show the same wrong answers every time', thin)
    add('mixed-kind', 'wrong', 'Kinds that mix numbers and words', 'A number can turn up as the wrong answer to a word, an easy give-away', mixed)
    add('lonely-wrong', 'wrong', 'Wrong answers only one card can draw', 'A wrong answer its kind lends to one card alone: the kind may be too narrow',
        [{'text': f'{q(shown_form(e))} on {e["by"]["kind"][0]}', 'cards': e['by']['kind']} for e in P['wrong'].values() if len(e['by'].get('kind', [])) == 1 and not e['by'].get('mine')])
    rep = defaultdict(list)
    for c in live: rep[(c['deck'], key(c['it']['hook']))].append(c['id'])
    add('hook-repeat', 'hook', 'Hooks many cards in one deck share', 'Tiles read alike when one deck leans on one word (build/decks/SPEC.md: varied)',
        [{'text': f'{q(shown_form(P["hook"][h]))} on {len(ids)} cards in {d}', 'cards': ids} for (d, h), ids in sorted(rep.items(), key=lambda x: -len(x[1])) if len(ids) >= 4])
    add('cross-cat', 'category', 'Cards shown under another category', 'The tile shows the card’s own category, while the draw counts it by its deck’s league and flags',
        [{'text': f'{c["id"]} shows {B.CATEGORY[c["cat"]]["name"]}, from {c["deck"]}' + (f' (counts as {c["league"]})' if c['league'] else ''), 'cards': [c['id']]} for c in live if c['it'].get('tag') and c['it']['tag'] != B.DECK_CAT[c['deck']]])
    add('says', 'card', 'Cards that say soccer or football', 'Kept only where the word is the fact (soccer mom, total football, footy): the editor reads each one',
        [{'text': f'{c["id"]}: ' + ', '.join(sorted({m.lower() for m in SAYS.findall(" ".join([c["it"]["ex"], c["it"]["means"], c["it"]["hook"], c["it"]["w"]] + wrongs(c["it"])))})), 'cards': [c['id']]}
         for c in live if SAYS.search(' '.join([c['it']['ex'], c['it']['means'], c['it']['hook'], c['it']['w']] + wrongs(c['it'])))])
    for f in F:
        for x in f['items']: x.pop('r', None); x['cards'] = list(dict.fromkeys(x['cards']))
    return F

def entry_flags(cs, P):
    """Each pool entry's own findings, for its badges in the Card Room: [code, detail]."""
    X = {'hook': defaultdict(list), 'answer': defaultdict(list), 'wrong': defaultdict(list), 'kind': defaultdict(list)}
    live = [c for c in cs if c['st'] != 'out']
    for name in ('hook', 'answer', 'wrong'):
        for k, e in P[name].items():
            if len({letters(f) for f in e['forms']}) < len(e['forms']): X[name][k].append(['case', ''])
            if len({letters(f) for f in e['forms']}) > 1: X[name][k].append(['marks', ''])
        for a, b in near_pairs(P[name]):
            X[name][a].append(['near', shown_form(P[name][b])]); X[name][b].append(['near', shown_form(P[name][a])])
    for k in P['hook']:
        if k in P['answer']: X['hook'][k].append(['answer', '']); X['answer'][k].append(['hook', ''])
    kinds = defaultdict(set)
    for c in live: kinds[(c['deck'], key(c['it']['w']))].add(c['it'].get('k', 'word'))
    for (d, k), ks in kinds.items():
        if len(ks) > 1: X['answer'][k].append(['kinds', d + ': ' + ', '.join(sorted(ks))])
    rep = Counter((c['deck'], key(c['it']['hook'])) for c in live)
    for (d, k), n in rep.items():
        if n >= 4: X['hook'][k].append(['repeat', f'{n} in {d}'])
    for k, e in P['wrong'].items():
        if e['by'].get('mine'): X['wrong'][k].append(['mine', ''])
        if len(e['by'].get('kind', [])) == 1 and not e['by'].get('mine'): X['wrong'][k].append(['lonely', ''])
        a = P['answer'].get(k)
        if a and set(e['forms']) - set(a['forms']): X['wrong'][k].append(['case', ''])
    for (d, k), e in P['kind'].items():
        if e['own'] == len(e['cards']): X['kind'][(d, k)].append(['own', '']); continue
        if len(e['answers']) < 4: X['kind'][(d, k)].append(['thin', ''])
        nums = [a for a in e['answers'] if number(a)]
        if nums and len(nums) < len(e['answers']): X['kind'][(d, k)].append(['mixed', ', '.join(nums)])
    return X

def print_report(cs, P, F, full=False):
    live = [c for c in cs if c['st'] != 'out']
    play = sum(c['st'] in ('approved', 'locked') for c in live)
    print(f'The library: {len(cs)} cards in {len(B.CATS["categories"])} categories and {len(B.DAILY)} decks, {len(live)} not out, {play} in play')
    print(f'  hooks {len(P["hook"])}, answers {len(P["answer"])}, wrong answers {len(P["wrong"])} in {len(P["kind"])} kinds, '
          f'{sum(1 for c in live if c["near"] and not c["it"].get("wr"))} number cards with made-up near misses')
    print(f'\nConsistency: {sum(len(f["items"]) for f in F)} findings ({sum(len(f["items"]) for f in F if f["rule"])} against a clear rule)')
    for f in F:
        if not f['items']: continue
        print(f'\n{f["title"]}: {len(f["items"])}' + ('  (a clear rule: check holds new and reworded cards to it)' if f['rule'] else ''))
        print(f'  {f["why"]}')
        for x in f['items'] if full else f['items'][:5]: print('   ', x['text'])
        if not full and len(f['items']) > 5: print(f'    … {len(f["items"]) - 5} more (report --all)')

def slips(c, cs_by, P):
    """The clear rules a card breaks against the cards in play: a hook, an answer or one of Morg’s own wrong answers spelled
    with other capitals or accents than the cards in play spell it, or an own category that repeats its deck’s."""
    it, out = c['it'], []
    play = lambda x: cs_by[x]['st'] in ('approved', 'locked') and x != c['id']
    def against(pool, form, fld, what):
        e = P[pool].get(key(form))
        seen = {cs_by[x]['it'][fld] for x in (e['cards'] if e else []) if play(x)}
        other = sorted(f for f in seen if f != form and letters(f) == letters(form))
        if other and form not in seen: out.append(f'its {what} “{form}” is spelled “{other[0]}” on the cards in play')
    against('hook', it['hook'], 'hook', 'hook')
    against('answer', it['w'], 'w', 'answer')
    for x in wrongs(it): against('answer', x, 'w', 'wrong answer')
    if it.get('tag') and it['tag'] == B.DECK_CAT[c['deck']]: out.append(f'its own category {it["tag"]} is its deck’s already')
    return out

def check(cs, P):
    """Every card still waiting on the reviewers (a new or reworded one) against the clear rules (slips). The cards in
    play today meet these rules only in the report, so this never fails on them (the orders, Oct 31, 2026: never fail
    on today’s cards without the GM’s yes)."""
    by = {c['id']: c for c in cs}
    bad = [(c['id'], s) for c in cs if c['st'] == 'pending' for s in slips(c, by, P)]
    for cid, s in bad: print(f'{cid}: {s}')
    print(f'{len(bad)} slips on new or reworded cards' if bad else 'No new or reworded card breaks a clear rule')
    return not bad

# ---- the ledger: when each card came in, and when each field last changed ----
def fh(v): return hashlib.sha1(json.dumps(v, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:5]

def git(*a): return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, check=True).stdout

def save_ledger(led):
    """One card a line, so two branches that date different cards merge cleanly."""
    rows = [f' {json.dumps(cid)}: {json.dumps(v, ensure_ascii=False, separators=(",", ":"))}' for cid, v in led['cards'].items()]
    note = json.dumps(led['@note'], ensure_ascii=False)
    open(LEDGER, 'w').write('{\n "@note": ' + note + ',\n "cards": {\n' + ',\n'.join(rows) + '\n }\n}\n')

NOTE = ('When each card came into the library and when each of its fields last changed, as Seattle dates: a, the day it came in, '
        'h, a short hash of each tracked field (' + ', '.join(TRACK) + ', in that order), and c, the day a field changed, for each '
        'field that changed after the card came in. Seeded from git history on Oct 31, 2026 by tools/library.py seed, and kept up by '
        'tools/library.py export, which dates anything new or changed to the day it runs. Commit it after export.')

def dated(e, f):
    """The day a ledger entry's field got its current value."""
    return e.get('c', {}).get(f, e['a'])

def note(e, vals, day):
    """Record a card's field hashes in its ledger entry, dating any that changed to day."""
    old = e.get('h', '').split()
    for n, f in enumerate(TRACK):
        if n < len(old) and old[n] != vals[f] and day != e['a']: e.setdefault('c', {})[f] = day
    e['h'] = ' '.join(vals[f] for f in TRACK)

def seed():
    if git('rev-parse', '--is-shallow-repository').strip() == 'true':
        sys.exit('The clone is shallow, so its history starts late: git fetch --unshallow origin, then seed again')
    led = {'@note': NOTE, 'cards': {}}
    for did, _, _ in B.DAILY:
        path = f'build/decks/{did}.json'
        for line in filter(None, git('log', '--reverse', '--format=%H %cI', '--', path).split('\n')):
            sha, when = line.split()
            day = datetime.datetime.fromisoformat(when).astimezone(SEATTLE).date().isoformat()
            try: deck = json.loads(git('show', f'{sha}:{path}'))
            except (subprocess.CalledProcessError, ValueError): continue
            for i, it in enumerate(deck.get('items', [])):
                cid = f'{did}:{i}'
                note(led['cards'].setdefault(cid, {'a': day}), {f: fh(it.get(f)) for f in TRACK}, day)
    stamp(led, cards())   # anything not committed yet comes in today
    save_ledger(led)
    print(f'ledger: {len(led["cards"])} cards dated from git history')

def stamp(led, cs):
    """Date what's new or changed since the ledger last saw it to today. Returns how many cards and fields."""
    t, n, f = today(), 0, 0
    for c in cs:
        vals = {x: fh(c['it'].get(x)) for x in TRACK}
        e = led['cards'].get(c['id'])
        if not e: led['cards'][c['id']] = {'a': t, 'h': ' '.join(vals[x] for x in TRACK)}; n += 1; continue
        was = e.get('h')
        note(e, vals, t)
        f += sum(a != b for a, b in zip((was or '').split(), e['h'].split()))
    return n, f

def load_ledger():
    try: return json.load(open(LEDGER))
    except FileNotFoundError: return {'@note': NOTE, 'cards': {}}

# ---- Morg's edits from the Card Room, back into the decks ----
STYLE = os.path.join(B.DECKS, 'MORG-STYLE.md')
NAMES = {'ex': 'ex', 'w': 'w', 'hook': 'hook', 'means': 'means', 'wr': 'wr', 'd': 'color', 'cat': 'category'}
WORDING = ('ex', 'w', 'hook', 'means', 'wr')   # what the fact checker's facts-only pass reads again

def room(src):
    """The Card Room's database as ArtifactData saved it: a folder with edits/, new/, asks/ and done/ (list each
    collection with out_dir), or one JSON file {"edits": [...], ...}. Each document as {id, version, data}."""
    def doc(raw, did):
        if isinstance(raw, dict) and isinstance(raw.get('data'), dict):   # a wrapper with the document under data
            return {'id': raw.get('doc_id') or raw.get('id') or did, 'version': raw.get('version'), 'data': raw['data']}
        return {'id': (raw or {}).get('_id') or did, 'version': (raw or {}).get('_version'), 'data': {k: v for k, v in (raw or {}).items() if not k.startswith('_')}}
    out = {'edits': [], 'new': [], 'asks': [], 'done': []}
    if os.path.isdir(src):
        for col in out:
            d = os.path.join(src, col)
            for name in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                if name.endswith('.json'): out[col].append(doc(json.load(open(os.path.join(d, name))), name[:-5]))
    else:
        raw = json.load(open(src))
        for col in out: out[col] = [doc(x, (x or {}).get('id', '')) for x in raw.get(col, [])]
    return out

def cell(v):
    if v is None: return '(none)'
    if isinstance(v, list): v = ', '.join(wrongs({'wr': v}))
    if isinstance(v, int) and not isinstance(v, bool): v = ('', 'green', 'yellow', 'red')[v] if 0 < v < 4 else str(v)
    return str(v).replace('|', '\\|').replace('\n', ' ')

def log_style(rows):
    """Morg's changes as before-and-after rows at the top of build/decks/MORG-STYLE.md's log, newest first."""
    text = open(STYLE).read()
    head = '| Card | Field | Before | After | Date |\n|---|---|---|---|---|\n'
    if head not in text: sys.exit('build/decks/MORG-STYLE.md has no log table to add to')
    lines = ''.join(f'| {cid} | {NAMES.get(f, f)} | {cell(b)} | {cell(a)} | {today()} |\n' for cid, f, b, a in rows)
    open(STYLE, 'w').write(text.replace(head, head + lines, 1))

def apply(src, dry=False):
    """Every saved edit and new card from the Card Room, turned into what the desk does by hand: an edit is checked
    against the house rules like tools/vet.py edit and written into its deck in place (so it goes back to the three
    reviewers), with the oks of deck-mates that only lost a wrong answer carried, a new card goes on the end of its
    deck, and every changed field is logged in build/decks/MORG-STYLE.md. A locked card, a card that's out, a field
    someone else changed since Morg edited it, or an edit that breaks a house rule is held, never forced."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import vet as V
    R = room(src)
    _, marks = B.vetting()
    done, style, facts, writes = [], [], [], []
    stamp = now().replace('-', '').replace(':', '')
    last = {}   # the room's log: the newest record for each saved document, as it was saved (its at)
    for x in sorted(R['done'], key=lambda x: x['data'].get('at', '')): last[(x['data'].get('col'), x['data'].get('id'), x['data'].get('for'))] = x['data']
    def settled(col, d):   # applied, dropped or added already, for the wording Morg saved
        return (last.get((col, d['id'], d['data'].get('at'))) or {}).get('st') in ('applied', 'dropped', 'added')
    def result(col, d, st, res, cid=None):
        """Each outcome is a new record in the room's done log, so no write ever needs a document's version."""
        done.append((st, col, d['id'], res))
        w = {'col': col, 'id': d['id'], 'for': d['data'].get('at', ''), 'st': st, 'res': res, 'at': now()}
        if cid: w['card'] = cid
        writes.append({'op': 'set', 'collection': 'done', 'doc_id': f'{col}~{d["id"]}~{stamp}', 'data': w})
    for d in R['edits']:
        e = d['data']; f = e.get('f') or {}
        if e.get('st') != 'saved' or settled('edits', d): continue
        cid = e.get('id') or d['id']
        try: did, deck, i = V.find(cid)
        except SystemExit: result('edits', d, 'held', 'no such card'); continue
        it = deck['items'][i]
        now_ = {'ex': it['ex'], 'w': it['w'], 'hook': it.get('hook'), 'means': it['means'], 'd': it.get('d'), 'cat': it.get('tag') or B.DECK_CAT[did], 'wr': wrongs(it) or None}
        if (marks.get(cid) or {}).get('m') == 'lock': result('edits', d, 'held', 'You locked this card: unlock it on the beta, or say OK in the chat, and the GM applies it'); continue
        if it.get('out'): result('edits', d, 'held', 'This card is out: ' + it.get('out_why', '')); continue
        bad = [k for k in f if k not in now_]
        if bad: result('edits', d, 'held', 'fields the room can’t edit: ' + ', '.join(bad)); continue
        clash = [k for k in f if now_[k] != (e.get('was') or {}).get(k) and now_[k] != f[k]]
        if clash: result('edits', d, 'held', 'Changed since you edited it: ' + ', '.join(f'{NAMES[k]} now reads “{cell(now_[k])}”' for k in clash)); continue
        if 'cat' in f and f['cat'] not in B.CATEGORY: result('edits', d, 'held', f'{f["cat"]} is not on the category list'); continue
        new = dict(it); ch = [(k, now_[k], v) for k, v in f.items() if now_[k] != v]
        for k, before, v in ch:
            if k == 'cat':
                if v == B.DECK_CAT[did]: new.pop('tag', None)
                else: new['tag'] = v
            elif k == 'wr':
                if not v: new.pop('wr', None)
                else:   # a wrong answer Morg kept keeps its own meaning line
                    old = {wrongs({'wr': [x]})[0]: x for x in it.get('wr') or []}
                    new['wr'] = [old.get(x, x) for x in v]
            else: new[k] = v
        if not ch: result('edits', d, 'applied', 'Already in the deck'); continue
        trial = dict(deck, items=deck['items'][:i] + [new] + deck['items'][i + 1:])
        probs = B.item_problems(did, trial['items'], B.clasher(trial), new, hooks=True)
        if probs: result('edits', d, 'held', 'It breaks a house rule: ' + '. '.join(' '.join(str(x) for x in p[2:]) for p in probs)); continue
        carried = 0
        if not dry:
            V.save_deck(did, trial); carried = V.carry(did, deck, trial, skip=(i,))
        style += [(cid, k, b, a) for k, b, a in ch]
        if any(k in WORDING for k, _, _ in ch): facts.append(cid)
        result('edits', d, 'applied', 'In its deck: ' + ', '.join(NAMES[k] for k, _, _ in ch) + (', back to the three reviewers' if any(k != 'cat' for k, _, _ in ch) else '') + (f' ({carried} deck-mates keep their oks)' if carried else ''), cid)
    for d in R['new']:
        n = d['data']
        if n.get('st') != 'saved' or settled('new', d): continue
        did, cat = n.get('deck') or (B.CATEGORY.get(n.get('cat')) or {}).get('home') or '', n.get('cat')
        if cat not in B.CATEGORY: result('new', d, 'held', f'{cat} is not on the category list'); continue
        if did not in B.DECK_CAT and cat in B.CATEGORY: did = B.CATEGORY[cat].get('home') or next(x for x, c in B.DECK_CAT.items() if c == cat)
        path = os.path.join(B.DECKS, did + '.json'); deck = json.load(open(path))
        kinds = {x.get('k', 'word') for x in deck['items']}
        k = n.get('k') or 'own'
        if k != 'own' and k not in kinds: result('new', d, 'held', f'{did} has no kind {k}'); continue
        item = {'w': n.get('w', ''), 'means': n.get('means', ''), 'ex': n.get('ex', ''), 'k': k, 'src': n.get('src') or '', 'hook': n.get('hook', ''), 'd': n.get('d')}
        if k == 'own' or [x for x in n.get('wr') or [] if x]: item['wr'] = [x for x in n.get('wr') or [] if x]
        if n.get('wm') and 'women' not in dict((x, f) for x, _, f in B.DAILY).get(did, ''): item['women'] = True
        if cat != B.DECK_CAT[did]: item['tag'] = cat
        twin = next((j for j, x in enumerate(deck['items']) if x['w'] == item['w'] and x['ex'] == item['ex']), None)
        if twin is not None: result('new', d, 'applied', 'Already in its deck', f'{did}:{twin}'); continue
        trial = dict(deck, items=deck['items'] + [item])
        probs = B.item_problems(did, trial['items'], B.clasher(trial), item, hooks=True)
        if probs: result('new', d, 'held', 'It breaks a house rule: ' + '. '.join(' '.join(str(x) for x in p[2:]) for p in probs)); continue
        cid = f'{did}:{len(deck["items"])}'
        grew = sum(B.fingerprint(deck, j) != B.fingerprint(trial, j) for j in range(len(deck['items'])) if not deck['items'][j].get('out'))
        if not dry: V.save_deck(did, trial)
        style += [(cid, f, '(new card)', item[f]) for f in ('ex', 'w', 'hook', 'means', 'wr') if item.get(f)]
        facts.append(cid)
        result('new', d, 'applied', f'On the end of {did} as {cid}' + (f', and {grew} deck-mates can now draw its answer, so they go back to the reviewers' if grew else '') + ('' if item['src'] else '. No source yet: the fact checker finds one on the deck’s site'), cid)
    asks = [d for d in R['asks'] if d['data'].get('st') == 'asked' and not settled('asks', d)]
    if style and not dry: log_style(style)
    for st, col, did, res in done: print(f'{st.upper():8} {col:5} {did}: {res}')
    for a in asks: print(f'ASK      category “{a["data"].get("name")}”' + (f', tile “{a["data"].get("tile")}”' if a['data'].get('tile') else '') + (f': {a["data"].get("note")}' if a['data'].get('note') else '') + '. Morg names it, then the GM adds it to build/library/categories.json with its tag string')
    if not done and not asks: print('Nothing saved in the Card Room waits to be applied'); return
    if dry: print('\nA dry run: nothing was written'); return
    if facts:
        print('\nFor the fact checker’s facts-only pass (then lock them for Morg once the facts hold, as for his Board Room cards):')
        print('  python3 tools/vet.py review ' + ' '.join(facts))
    if writes:
        out = os.path.join(src if os.path.isdir(src) else os.path.dirname(os.path.abspath(src)), 'applied.json')
        json.dump([writes[n:n + 50] for n in range(0, len(writes), 50)], open(out, 'w'), ensure_ascii=False, indent=1)
        print(f'\nThe room’s log, in batches of 50 for ArtifactData batch (new documents in done, so no versions needed): {out}')
    print('Then: python3 build/build.py, python3 tools/library.py check, python3 tools/library.py export DIR and republish library.json,')
    print('and commit the decks, build/vetting/desk.json, build/decks/MORG-STYLE.md and build/library/ledger.json')

# ---- the Card Room's data ----
def export(out):
    cs = cards()
    led = load_ledger(); n, f = stamp(led, cs)
    if n or f: save_ledger(led)
    text, _ = strings.load()
    P = pools(cs); F = report(cs, P)
    idx = {c['id']: j for j, c in enumerate(cs)}
    day = lambda cid, fld: dated(led['cards'][cid], fld)
    live = [c for c in cs if c['st'] != 'out']
    def card(c):
        it, e = c['it'], led['cards'][c['id']]
        x = {'id': c['id'], 'k': it.get('k', 'word'), 'c': c['cat'], 'd': it.get('d'), 's': c['st'][0], 'w': it['w'], 'ex': it['ex'], 'm': it['means'],
             'h': it['hook'], 'src': it.get('src', ''), 'a': e['a'], 'e': max([e['a']] + list(e.get('c', {}).values())), 'fp': c['mh']}
        if it.get('tag'): x['own'] = 1
        if it.get('wr'): x['wr'] = it['wr']
        if c['women']: x['wm'] = 1
        if c['near'] and not it.get('wr'): x['nr'] = c['near']   # the cards a wrong answer can go on are in pools.wrong
        if c['wait']: x['wt'] = c['wait']
        if c['note']: x['fn'] = c['note']
        if it.get('out'): x['ow'] = it.get('out_why', '')
        return x
    def first(e, fld): return min(day(c, fld) for c in e['cards'])
    X = entry_flags(cs, P)
    def pool(name, fld):
        rows = []
        for k, e in P[name].items():
            r = {'t': shown_form(e), 'c': [idx[c] for c in e['cards']], 'n': first(e, fld)}
            if len(e['forms']) > 1: r['f'] = sorted(e['forms'])
            if X[name].get(k): r['x'] = X[name][k]
            if name == 'wrong':
                r['c'] = [idx[c] for c in e['by'].get('kind', [])]
                if e['by'].get('mine'): r['o'] = [idx[c] for c in e['by']['mine']]
                r['n'] = min([day(c, 'wr') for c in e['by'].get('mine', [])] + [day(c, 'w') for c in P['answer'].get(k, {'cards': []})['cards']] or [led['cards'][e['cards'][0]]['a']])
                if k in P['answer']: r['ans'] = 1
            rows.append(r)
        return rows
    kinds = [dict({'dk': d, 'k': k, 'a': e['answers'], 'c': [idx[c] for c in e['cards']], 'own': e['own']}, **({'x': X['kind'][(d, k)]} if X['kind'].get((d, k)) else {}))
             for (d, k), e in P['kind'].items()]
    dates = sorted({e['a'] for e in led['cards'].values()} | {today()})
    days = [(datetime.date.fromisoformat(dates[0]) + datetime.timedelta(n)).isoformat() for n in range((datetime.date.fromisoformat(today()) - datetime.date.fromisoformat(dates[0])).days + 1)]
    growth = {'days': days,
              'cards': [sum(led['cards'][c['id']]['a'] <= d for c in live) for d in days],
              'hook': [sum(first(e, 'hook') <= d for e in P['hook'].values()) for d in days],
              'answer': [sum(first(e, 'w') <= d for e in P['answer'].values()) for d in days],
              'wrong': [sum(r['n'] <= d for r in pool('wrong', 'w')) for d in days]}
    decks = []
    for d in B.CATS['decks']:
        raw = json.load(open(os.path.join(B.DECKS, d['id'] + '.json')))
        decks.append({'id': d['id'], 'name': d['name'], 'cat': d['category'], 'league': d.get('league', ''), 'flags': d.get('flags', []),
                      'src': raw.get('primary', ''), 'n': len(raw['items'])})
    data = {'v': 1, 'at': now(), 'today': today(), 'lately': LATELY, 'commit': git('rev-parse', '--short', 'HEAD').strip(),
            'reviewers': list(B.REVIEWERS), 'cats': categories(cs, text), 'decks': decks, 'cards': [card(c) for c in cs],
            'pools': {'hook': pool('hook', 'hook'), 'answer': pool('answer', 'w'), 'wrong': pool('wrong', 'w'), 'kind': kinds},
            'growth': growth, 'report': [{**{k: v for k, v in f.items() if k != 'items'}, 'items': [{'text': x['text'], 'c': [idx[c] for c in x['cards']]} for x in f['items']]} for f in F],
            'rules': {'hook_max': B.HOOK_MAX, 'ex_max': 85, 'means_max': 40, 'w_max': 22, 'spelled': B.SPELLED, 'hedge': B.HEDGE.pattern}}
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'library.json')
    open(path, 'w').write(json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    print(f'wrote {path}: {len(cs)} cards, {os.path.getsize(path) // 1024} KB' + (f'. Ledger: {n} new cards and {f} changed fields dated today (commit build/library/ledger.json)' if n or f else ''))

if __name__ == '__main__':
    a = sys.argv[1:]
    cmd = a[0] if a else 'report'
    if cmd == 'report':
        cs = cards(); P = pools(cs); print_report(cs, P, report(cs, P), '--all' in a)
    elif cmd == 'check':
        cs = cards(); sys.exit(0 if check(cs, pools(cs)) else 1)
    elif cmd == 'export' and len(a) > 1: export(a[1])
    elif cmd == 'seed': seed()
    elif cmd == 'apply' and len(a) > 1: apply(a[1], '--dry' in a)
    else: sys.exit(__doc__)
