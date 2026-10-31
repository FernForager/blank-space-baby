"""Vetting: how the three reviewers read cards and record verdicts, and how Morg's beta marks come in.

    python3 tools/vet.py todo WHO [DECK] [--limit N] [--json]   # cards waiting on WHO's verdict, with all they need to judge them
    python3 tools/vet.py apply WHO FILE.json                    # record verdicts: a JSON list of {id, h, v, note, fix}
    python3 tools/vet.py card ID                                # one card in full: every verdict and mark on it (for Trivelle)
    python3 tools/vet.py review ID [ID ...]                     # named cards as todo shows them, no one's verdicts: for a re-check the desk asks for
    python3 tools/vet.py status                                 # where every card stands
    python3 tools/vet.py fixes [DECK]                           # open fix and cut verdicts on current cards (for Trivelle)
    python3 tools/vet.py take ID WHO                            # write WHO's proposed fix into the deck (for Trivelle)
    python3 tools/vet.py combine ID WHO:field,field WHO:field   # write fields from two reviewers' fixes at once (for Trivelle)
    python3 tools/vet.py edit ID '{"ex": "..."}'                # write the desk's own wording, checked like a fix (for Trivelle)
    python3 tools/vet.py out ID "reason"                        # take a card out of play for good (for Trivelle)
    python3 tools/vet.py decline ID WHO "reason"                # turn down WHO's fix or cut: the card goes back to WHO (for Trivelle)
    python3 tools/vet.py marks FILE.json                        # Morg's beta marks: rows from the database's marks table

WHO is one of the reviewers in build/build.py: soccer (the soccer expert), editor (the writing editor) or facts
(the fact checker). A card ID is <deck id>:<index>, its place in build/decks/<deck id>.json, which never changes.

A verdict is v "ok" (the card is right as it stands), "fix" (it needs a change: say why in note, and put the
changed fields in fix, like {"means": "..."}) or "cut" (it can't be saved: say why). Each verdict carries h, the
fingerprint of the card the reviewer read (todo prints it). apply refuses a verdict whose card has changed since,
so nobody approves wording they never saw, and checks every proposed fix against the house rules before saving it.
A card plays in the beta once all three reviewers have said ok to its current wording, or once Morg locks it. His
marks hold to the card's own fields (build.py's mark_hash), never to the wrong answers its deck-mates lend it, so a
change elsewhere in the deck sends a card back to the reviewers but never lapses a flag or breaks a lock.
"""
import datetime, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import build as B

FIELDS = ('w', 'ex', 'means', 'hook', 'd', 'k', 'src', 'groups')   # what a fix may change. groups: answers to add to the deck's groups
COLOR = {1: 'white (easy)', 2: 'yellow (medium)', 3: 'red (hard)'}

def now(): return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def decks():
    """Every deck in the daily, in order: (id, deck JSON, flags)."""
    return [(did, json.load(open(os.path.join(B.DECKS, did + '.json'))), flags) for did, lg, flags in B.DAILY]

def find(cid):
    did, _, i = cid.partition(':')
    path = os.path.join(B.DECKS, did + '.json')
    if not re.fullmatch(r'[a-z0-9-]+', did) or not i.isdigit() or not os.path.exists(path): sys.exit(f'no such card: {cid}')
    deck = json.load(open(path))
    if int(i) >= len(deck['items']): sys.exit(f'no such card: {cid}')
    return did, deck, int(i)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + '\n')

def save_deck(did, deck):
    """Write a deck back with the indent it already uses, so diffs stay small."""
    path = os.path.join(B.DECKS, did + '.json')
    m = re.search(r'\n( +)"', open(path).read())
    open(path, 'w').write(json.dumps(deck, ensure_ascii=False, indent=len(m.group(1)) if m else 1) + '\n')

def view(did, deck, i, flags=''):
    """All a reviewer needs to judge one card."""
    it = deck['items'][i]
    own = {w: m for w, m in B.draws(did, deck, it) if m is not None}   # wrong answers with a meaning of their own, which a wrong pick shows
    return {'id': f'{did}:{i}', 'h': B.fingerprint(did, deck, i), 'deck': deck.get('deck', did), 'source': deck.get('primary', ''),
            'color': COLOR.get(it.get('d'), '?'), 'kind': it.get('k', 'word'), 'set': B.set_id(did, it), 'answer': it['w'], 'sentence': it['ex'],
            'means': it['means'], 'hook': it.get('hook', ''), 'src': it.get('src', ''),
            'wrong_answers': B.wrong_pool(did, deck, it), **({'wrong_meanings': own} if own else {}), 'notes': [x for x in ((f'number answer: the game makes up its two wrong answers, {B.near_rule(it)} (the list above is only the fallback), so the fact must be exact, since a near miss can’t be a second right answer' if B.near_rule(it) else ''), ('women’s game' if it.get('women') or 'women' in flags else ''),
            ('slang deck: no proper names' if 'slang' in flags else ''), ('can go stale: check it is still true today' if it.get('current') else '')) if x]}

def todo(who, deck_id=None, limit=None, as_json=False):
    """Cards waiting on who: no verdict, a verdict for an older wording, or a fix the desk turned down (with its reason)."""
    verdicts, marks = B.vetting()
    out = []
    for did, deck, flags in decks():
        if deck_id and did != deck_id: continue
        clash = B.clasher(deck)
        for i, it in enumerate(deck['items']):
            cid = f'{did}:{i}'
            if it.get('out') or (marks.get(cid) or {}).get('m') == 'lock': continue
            v = verdicts[who].get(cid)
            if v and v.get('h') == B.fingerprint(did, deck, i, clash): continue
            c = view(did, deck, i, flags); n = desk_note(cid, who)
            if n: c['notes'].append(n)
            out.append(c)
    left = len(out)
    if limit: out = out[:limit]
    if as_json: print(json.dumps(out, ensure_ascii=False, indent=1)); return
    for c in out:
        print(f"\n{c['id']}  h={c['h']}  {c['deck']}  {c['color']}  wrong answers from: {c['set']}")
        print(f"  sentence: {c['sentence']}\n  answer:   {c['answer']}\n  means:    {c['means']}\n  tile:     {c['hook']}")
        print(f"  wrong answers it can draw: {' · '.join(c['wrong_answers']) or 'none'}\n  source:   {c['src']}")
        for w, m in c.get('wrong_meanings', {}).items(): print(f'  a wrong pick of {w} shows: {m}')
        for n in c['notes']: print(f'  note:     {n}')
    print(f'\n{left} waiting on {who}' + (f', {len(out)} shown' if limit and left > limit else ''))

def changed(deck, i, fix):
    """The deck with a fix applied: its card fields replaced, and any groups added."""
    fix = dict(fix); groups = fix.pop('groups', None) or []
    items = list(deck['items']); items[i] = dict(items[i], **fix)
    old = deck.get('groups', [])
    return dict(deck, items=items, groups=old + [g for g in groups if g not in old])

def problems_with(did, deck, i, fix):
    """The house-rule problems a fix would give a card, or why the fix itself is malformed."""
    groups = fix.get('groups')
    if groups is not None:
        answers = {x['w'] for x in deck['items']}
        if not isinstance(groups, list) or not all(isinstance(g, list) and len(g) >= 2 and all(isinstance(w, str) and w in answers for w in g) for g in groups):
            return [(did, deck['items'][i]['w'], 'groups must be a list of lists of two or more answers from this deck')]
    trial = changed(deck, i, fix)
    return B.item_problems(did, trial['items'], B.clasher(trial), trial['items'][i], hooks=True)

def apply(who, path):
    rows = json.load(open(path))
    if isinstance(rows, dict): rows = [rows]
    vpath = os.path.join(B.VET, who + '.json')
    mine = B.load_json(vpath, {}); _, marks = B.vetting()   # the reviewer's own file only: desk records stay in desk.json
    saved, refused = 0, []
    for r in rows:
        cid, v = r.get('id', ''), r.get('v')
        try: did, deck, i = find(cid)
        except SystemExit: refused.append((cid, 'no such card')); continue
        it = deck['items'][i]
        why = None
        if v not in ('ok', 'fix', 'cut'): why = 'v must be ok, fix or cut'
        elif r.get('h') != B.fingerprint(did, deck, i): why = 'the card or the wrong answers it can draw have changed since you read it: read it again with todo or card'
        elif (marks.get(cid) or {}).get('m') == 'lock': why = 'Morg locked this card'
        elif v != 'ok' and not (r.get('note') or '').strip(): why = 'a fix or a cut needs a note saying why'
        elif v == 'fix':
            fix = r.get('fix') or {}
            if not isinstance(fix, dict) or not fix or set(fix) - set(FIELDS): why = f'fix must be an object of changed fields, from {", ".join(FIELDS)}'
            else:
                if changed(deck, i, fix) == deck: why = 'the fix changes nothing'
                else:
                    bad = problems_with(did, deck, i, fix)
                    if bad: why = 'the fix breaks house rules: ' + '; '.join(' '.join(str(x) for x in b[2:]) for b in bad)
        if why: refused.append((cid, why)); continue
        entry = {'v': v, 'h': r['h'], 'at': now()}
        if r.get('note'): entry['note'] = r['note'].strip()
        if v == 'fix': entry['fix'] = r['fix']
        mine[cid] = entry; saved += 1
    save_json(vpath, mine)
    print(f'saved {saved} verdicts for {who}')
    for cid, why in refused: print(f'  refused {cid}: {why}')
    if refused: sys.exit(1)

def card(cid):
    did, deck, i = find(cid)
    flags = dict((d, f) for d, _, f in B.DAILY).get(did, '')
    verdicts, marks = B.vetting()
    c = view(did, deck, i, flags); it = deck['items'][i]
    print(json.dumps(c, ensure_ascii=False, indent=1))
    print('standing:', B.standing(cid, it, c['h'], verdicts, marks) if did in dict((d, 1) for d, _, _ in B.DAILY) else 'not in the daily')
    for who in B.REVIEWERS:
        v = verdicts[who].get(cid)
        print(f'{who}:', json.dumps(v, ensure_ascii=False) if v else 'no verdict', '' if not v or v.get('h') == c['h'] else '(for an older wording)')
    if marks.get(cid): print('Morg:', json.dumps(marks[cid], ensure_ascii=False), '' if marks[cid].get('h') == B.mark_hash(it) else '(for an older wording)')

def status():
    verdicts, marks = B.vetting()
    tally = {k: [0, 0, 0] for k in ('approved', 'locked', 'pending', 'flagged', 'out')}
    per = {who: {'ok': 0, 'fix': 0, 'cut': 0, 'waiting': 0} for who in B.REVIEWERS}
    for did, deck, flags in decks():
        clash = B.clasher(deck)
        for i, it in enumerate(deck['items']):
            cid, h = f'{did}:{i}', B.fingerprint(did, deck, i, clash)
            st = B.standing(cid, it, h, verdicts, marks)
            if it.get('d') in (1, 2, 3): tally[st][it['d'] - 1] += 1
            if st in ('out', 'locked'): continue
            for who in B.REVIEWERS:
                v = verdicts[who].get(cid)
                per[who][v['v'] if v and v.get('h') == h else 'waiting'] += 1
    for k, (a, b, c) in tally.items(): print(f'{k:9} {a + b + c:5}   white {a}, yellow {b}, red {c}')
    for who, n in per.items(): print(f'{who:9} ' + ', '.join(f'{v} {k}' for k, v in n.items()))

def fixes(deck_id=None):
    verdicts, marks = B.vetting(); n = 0
    for did, deck, flags in decks():
        if deck_id and did != deck_id: continue
        clash = B.clasher(deck)
        for i, it in enumerate(deck['items']):
            cid, h = f'{did}:{i}', B.fingerprint(did, deck, i, clash)
            if it.get('out') or (marks.get(cid) or {}).get('m') == 'lock': continue
            open_ = {who: verdicts[who][cid] for who in B.REVIEWERS if verdicts[who].get(cid, {}).get('h') == h and verdicts[who][cid]['v'] != 'ok'}
            if not open_: continue
            n += 1
            print(f'\n{cid}  {it["ex"]}  [{it["w"]}]  means: {it["means"]}  tile: {it.get("hook")}  {COLOR.get(it.get("d"))}')
            for who, v in open_.items():
                print(f'  {who} says {v["v"]}: {v.get("note", "")}' + (f'\n    fix: {json.dumps(v["fix"], ensure_ascii=False)}' if v.get('fix') else ''))
    print(f'\n{n} cards with open fixes or cuts')

def take(cid, who):
    did, deck, i = find(cid)
    verdicts, marks = B.vetting()
    v, it = verdicts[who].get(cid), deck['items'][i]
    if not v or v.get('v') != 'fix': sys.exit(f'{who} has no fix on {cid}')
    if v.get('h') != B.fingerprint(did, deck, i): sys.exit(f'{who}’s fix was for an older wording of {cid}')
    if (marks.get(cid) or {}).get('m') == 'lock': sys.exit(f'Morg locked {cid}')
    bad = problems_with(did, deck, i, v['fix'])
    if bad: sys.exit('the fix breaks house rules: ' + '; '.join(' '.join(str(x) for x in b[2:]) for b in bad))
    new = changed(deck, i, v['fix']); save_deck(did, new); p = new['items'][i]
    carried = carry(did, deck, new, skip=(i,)); follow(cid, deck, new)
    dpath = os.path.join(B.VET, 'desk.json'); desk = B.load_json(dpath, {})   # the proposer's ok on the wording it asked for,
    old = B.fingerprint(did, deck, i)                                          # and any other reviewer's who asked for the same
    for w in B.REVIEWERS:
        o = verdicts[w].get(cid)
        if w == who or (o and o.get('v') == 'fix' and o.get('h') == old and o.get('fix') == v['fix']):
            desk.setdefault(cid, {})[w] = {'h': B.fingerprint(did, new, i), 'at': now()}
    save_json(dpath, desk)
    print(f'{cid} now reads: {p["ex"]}  [{p["w"]}]  means: {p["means"]}  tile: {p.get("hook")}  (fingerprint {B.fingerprint(did, new, i)}: counts as {who}’s ok, back to the other two)' + (f'  ({carried} oks carried on deck-mates)' if carried else ''))
    if v['fix'].get('groups'): print('  groups added:', v['fix']['groups'], '(cards that can draw them get new fingerprints too)')

def combine(cid, parts):
    """Apply fields from several reviewers' fixes on one card at once, as WHO:field,field ... It counts as no one's ok,
    since the result is no one's exact proposal, so all three see the card fresh."""
    did, deck, i = find(cid)
    verdicts, marks = B.vetting(); h = B.fingerprint(did, deck, i); fix = {}
    if (marks.get(cid) or {}).get('m') == 'lock': sys.exit(f'Morg locked {cid}')
    for part in parts:
        who, _, fields = part.partition(':')
        v = verdicts.get(who, {}).get(cid)
        if not v or v.get('v') != 'fix' or v.get('h') != h: sys.exit(f'{who} has no current fix on {cid}')
        for f in fields.split(','):
            if f not in v['fix']: sys.exit(f'{who}’s fix on {cid} has no {f}')
            fix[f] = v['fix'][f]
    bad = problems_with(did, deck, i, fix)
    if bad: sys.exit('the combined fix breaks house rules: ' + '; '.join(' '.join(str(x) for x in b[2:]) for b in bad))
    new = changed(deck, i, fix); save_deck(did, new); p = new['items'][i]
    carried = carry(did, deck, new, skip=(i,)); follow(cid, deck, new)
    print(f'{cid} now reads: {p["ex"]}  [{p["w"]}]  means: {p["means"]}  tile: {p.get("hook")}  (combined, back to all three)' + (f'  ({carried} oks carried on deck-mates)' if carried else ''))

def edit(cid, fix):
    """The desk's own wording, for when no proposal is quite right. Checked against the house rules like a reviewer's
    fix, and it counts as no one's ok, so all three see the card fresh."""
    did, deck, i = find(cid)
    _, marks = B.vetting()
    if (marks.get(cid) or {}).get('m') == 'lock': sys.exit(f'Morg locked {cid}')
    fix = json.loads(fix)
    if not isinstance(fix, dict) or not fix or set(fix) - set(FIELDS): sys.exit(f'the edit must be an object of changed fields, from {", ".join(FIELDS)}')
    bad = problems_with(did, deck, i, fix)
    if bad: sys.exit('the edit breaks house rules: ' + '; '.join(' '.join(str(x) for x in b[2:]) for b in bad))
    new = changed(deck, i, fix)
    if new == deck: sys.exit('the edit changes nothing')
    save_deck(did, new); p = new['items'][i]
    carried = carry(did, deck, new, skip=(i,)); follow(cid, deck, new)
    print(f'{cid} now reads: {p["ex"]}  [{p["w"]}]  means: {p["means"]}  tile: {p.get("hook")}  (the desk’s wording, back to all three)' + (f'  ({carried} oks carried on deck-mates)' if carried else ''))

def carry(did, before, after, skip=(), sets=(None, None)):
    """After a deck changes, keep the oks of every other card whose only change is losing wrong answers: a card offered
    fewer decoys can't gain a second right answer, so its reviewers needn't see it again. A card that gains a decoy
    goes back to them. Recorded in desk.json like a taken fix. Since the sets (build/library/wrong.json, Oct 31, 2026)
    only new groups and an answer dropped from a set take decoys away like this (sets: the sets before and after, for a
    set's change): a card going out stays in every set it's in, so out carries nothing."""
    verdicts, _ = B.vetting(); cb, ca = B.clasher(before), B.clasher(after)
    dpath = os.path.join(B.VET, 'desk.json'); desk = B.load_json(dpath, {}); n = 0
    for j, it in enumerate(after['items']):
        if j in skip or it.get('out') or j >= len(before['items']): continue
        old, new = B.fingerprint(did, before, j, cb, sets[0]), B.fingerprint(did, after, j, ca, sets[1])
        if old == new or {k: v for k, v in before['items'][j].items()} != it: continue
        if not set(B.draws(did, after, it, ca, sets[1])) <= set(B.draws(did, before, before['items'][j], cb, sets[0])): continue
        cid = f'{did}:{j}'
        for w in B.REVIEWERS:
            v = verdicts[w].get(cid)
            if v and v.get('v') == 'ok' and v.get('h') == old:
                desk.setdefault(cid, {})[w] = {'h': new, 'at': now()}; n += 1
    save_json(dpath, desk)
    return n

def decline(cid, who, why):
    """Turn down a reviewer's fix or cut with a reason. The card goes back into that reviewer's todo with the reason."""
    did, deck, i = find(cid)
    verdicts, _ = B.vetting(); v = verdicts[who].get(cid)
    if not v or v.get('v') == 'ok': sys.exit(f'{who} has no fix or cut on {cid}')
    dpath = os.path.join(B.VET, 'desk.json'); desk = B.load_json(dpath, {})
    desk.setdefault(cid, {})[who] = {'declined': True, 'note': why, 'h': B.fingerprint(did, deck, i), 'at': now()}; save_json(dpath, desk)
    print(f'declined {who}’s {v["v"]} on {cid}: {why}')

def desk_note(cid, who):
    t = B.load_json(os.path.join(B.VET, 'desk.json'), {}).get(cid, {}).get(who)
    return f'Trivelle turned down your last verdict: {t["note"]}' if t and t.get('declined') else ''

def take_out(cid, why):
    did, deck, i = find(cid)
    marks = B.vetting()[1]
    if (marks.get(cid) or {}).get('m') == 'lock': sys.exit(f'Morg locked {cid}: ask him to unlock it first')
    before = json.loads(json.dumps(deck))
    deck['items'][i]['out'] = True; deck['items'][i]['out_why'] = why; save_deck(did, deck)
    sets = [st['id'] for st in B.wrong_sets()['sets'] if any(e.get('from') == cid for e in st['entries'])]
    grew = [f'{did}:{j}' for j, x in enumerate(deck['items']) if j != i and not x.get('out') and B.fingerprint(did, before, j) != B.fingerprint(did, deck, j)]
    print(f'{cid} is out: {why}' + (f'  (its answer stays in {", ".join(sets)}, where it stops showing while the card is out: drop it there, or give it a meaning of its own, in build/library/wrong.json)' if sets else '')
          + (f'  ({len(grew)} cards now draw from their deck’s other sets too, so they go back to the reviewers: {" ".join(grew)})' if grew else ''))

def follow(cid, before, after):
    """A borrowed wrong answer reads its card's answer as it is now, so when a card's answer changes, its entries in the
    sets (build/library/wrong.json) take the new spelling too, and the cards that can draw it go back to the reviewers."""
    i = int(cid.partition(':')[2]); w = after['items'][i]['w']
    if before['items'][i]['w'] == w: return
    data = B.wrong_sets(); n = 0
    for st in data['sets']:
        for e in st['entries']:
            if e.get('from') == cid: e['w'] = w; n += 1
    if n: B.save_sets(data); print(f'  its answer {w} now stands in {n} set' + ('s' if n > 1 else '') + ' of wrong answers too')

def import_marks(path):
    """Morg's marks from the beta (rows of the marks table, oldest first) folded into build/vetting/morg.json.
    A flag or a lock stands until an unflag or an unlock for the same card. Prints what's new."""
    rows = json.load(open(path))
    if isinstance(rows, list) and rows and isinstance(rows[0], dict) and 'results' in rows[0]: rows = rows[0]['results']   # the database tool's reply
    if isinstance(rows, dict): rows = rows.get('results', [])
    mpath = os.path.join(B.VET, 'morg.json')
    state = B.load_json(mpath, {'last': 0, 'cards': {}})
    new, held = [], []
    def current(cid):   # the card's fingerprint now, or None for a card that doesn't exist
        did, _, i = cid.partition(':')
        path = os.path.join(B.DECKS, did + '.json')
        if not re.fullmatch(r'[a-z0-9-]+', did) or not i.isdigit() or not os.path.exists(path): return None
        deck = json.load(open(path))
        return B.mark_hash(deck['items'][int(i)]) if int(i) < len(deck['items']) else None
    for r in sorted(rows, key=lambda r: int(r['id'])):
        if int(r['id']) <= state['last']: continue
        state['last'] = int(r['id']); cid, m = r['card'], r['mark']
        # Anyone who finds a preview link can post a mark (the audit, Oct 30, 2026), so a lock must name the card as it is
        # now, and an unlock the lock it lifts. Anything else waits for Morg to confirm it.
        if (m == 'lock' and r['hash'] != current(cid)) or (m == 'unlock' and state['cards'].get(cid, {}).get('m') == 'lock' and r['hash'] != state['cards'][cid]['h']):
            held.append(r); continue
        if m in ('flag', 'lock'): state['cards'][cid] = {'m': m, 'h': r['hash'], 'note': r.get('note') or '', 'at': r['at'], 'row': int(r['id'])}
        elif state['cards'].get(cid, {}).get('m') == m[2:]: del state['cards'][cid]   # unflag clears a flag, unlock a lock
        new.append(r)
    save_json(mpath, state)
    for r in new: print(f"{r['id']}  {r['mark']:7} {r['card']}  {r.get('note') or ''}")
    for r in held: print(f"HELD {r['id']}  {r['mark']:7} {r['card']}: its fingerprint {r['hash']} doesn't match the card, so ask Morg before recording it by hand")
    print(f'{len(new)} new marks' + (f', {len(held)} held' if held else '') + f', up to row {state["last"]}')
def review(cids):
    """Named cards, each as todo shows it and nothing more, so a reviewer re-judging them never sees another's verdict."""
    flags = dict((d, f) for d, _, f in B.DAILY)
    out = []
    for cid in cids:
        did, deck, i = find(cid)
        out.append(view(did, deck, i, flags.get(did, '')))
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    cmd, rest = a[0], a[1:]
    opt = lambda name: rest[rest.index(name) + 1] if name in rest else None
    plain_args = [x for j, x in enumerate(rest) if not x.startswith('--') and (j == 0 or rest[j - 1] != '--limit')]
    if cmd == 'todo':
        who = plain_args[0] if plain_args else None
        if who not in B.REVIEWERS: sys.exit('WHO must be one of ' + ', '.join(B.REVIEWERS))
        todo(who, plain_args[1] if len(plain_args) > 1 else None, int(opt('--limit')) if opt('--limit') else None, '--json' in rest)
    elif cmd == 'apply':
        if len(plain_args) != 2 or plain_args[0] not in B.REVIEWERS: sys.exit('usage: vet.py apply WHO FILE.json')
        apply(plain_args[0], plain_args[1])
    elif cmd == 'card': card(plain_args[0])
    elif cmd == 'review': review(plain_args)
    elif cmd == 'status': status()
    elif cmd == 'fixes': fixes(plain_args[0] if plain_args else None)
    elif cmd == 'take': take(plain_args[0], plain_args[1])
    elif cmd == 'out': take_out(plain_args[0], plain_args[1])
    elif cmd == 'combine': combine(plain_args[0], plain_args[1:])
    elif cmd == 'edit': edit(plain_args[0], plain_args[1])
    elif cmd == 'decline': decline(plain_args[0], plain_args[1], plain_args[2])
    elif cmd == 'marks': import_marks(plain_args[0])
    else: sys.exit(__doc__)
