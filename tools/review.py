"""Build the card review queues for Morg's hub from the decks in the daily.

    python3 tools/review.py --hub OUTDIR     # one JSON file per deck: a review queue for the hub (Oct 16, 2026)
    python3 tools/review.py OUT.html         # the old standalone review page, kept for reference

Morg approves, flags or cuts each card in the hub: its sentence, its means line, its tile word (hook) and its color.
Each card also lists the wrong answers it can draw, so a giveaway or a second right answer shows.
Each file is one document for the hub's collection projects/triviela/reviews (send them with ArtifactData). Morg's
verdicts land in projects/triviela/verdicts, one document per card, named <deck id>~<card index>, with the answer,
sentence, hook and color he saw.
"""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = [('mls','MLS'),('nwsl','NWSL'),('intl-men','International Men’s'),('intl-women','International Women’s'),('wc26','World Cup 2026'),
         ('laliga','La Liga'),('bundesliga','Bundesliga'),('seriea','Serie A'),('ligue1','Ligue 1'),('ligamx','Liga MX'),('ucl','Champions League'),
         ('rules','Soccer Rules'),('legends','Soccer Legends'),('nicknames','Club Nicknames'),('awards','Awards'),('epl-more','EPL (new cards)'),('lingo-more','Soccer Lingo (new words)'),
         # the decks from the arcade game: only their tile words and colors are new
         ('soccer','Soccer Lingo (new tiles and colors)'),('epl','EPL (new tiles and colors)'),('alpha','Kid Slang (new tiles and colors)'),('parents','Parent Slang (new tiles and colors)')]

def wrongs(deck, it):
    """The answers the game may put on this card's other two buttons: same kind, and not grouped with it (build.py's clash)."""
    groups = {}
    for i, grp in enumerate(deck.get('groups', [])):
        for w in grp: groups.setdefault(w, set()).add(i)
    clash = lambda a, b: a == b or bool(groups.get(a, set()) & groups.get(b, set()))
    out = []
    for x in deck['items']:
        if x.get('k', 'word') == it.get('k', 'word') and not clash(x['w'], it['w']) and x['w'] not in out: out.append(x['w'])
    return out

TILE = {1: ('#FFFFFF', '#1E2A3B', 'White tile (easy)'), 2: ('#F7C948', '#1E2A3B', 'Yellow card (medium)'), 3: ('#D52B1E', '#FFFFFF', 'Red card (hard)')}

def hub_item(i, x, pool):
    shown = ' · '.join(pool[:8]) + (f' · and {len(pool) - 8} more' if len(pool) > 8 else '')
    color, ink, label = TILE.get(x.get('d'), ('#FFFFFF', '#1E2A3B', ''))
    host = x['src'].split('/')[2] if x['src'].startswith('http') else x['src']
    return {'id': str(i), 'text': x['ex'], 'mark': x['w'], 'sub': x['means'],
            'tile': {'text': x.get('hook', ''), 'color': color, 'ink': ink, 'label': label},
            'lines': ['Wrong answers it can draw: ' + (shown or 'none')],
            'chips': [x.get('k', 'word')] + (['can go stale'] if x.get('current') else []),
            'link': {'label': 'Source: ' + host, 'url': x['src']},
            'snap': {'w': x['w'], 'ex': x['ex'], 'means': x['means'], 'hook': x.get('hook', ''), 'd': x.get('d')}}

if __name__ == '__main__':
    if sys.argv[1] == '--hub':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True); n = 0
        for order, (did, name) in enumerate(DECKS):
            d = json.load(open(os.path.join(ROOT, 'build', 'decks', did + '.json')))
            q = {'title': name, 'order': order + 1, 'seconds': 15, 'items': [hub_item(i, x, wrongs(d, x)) for i, x in enumerate(d['items'])]}
            body = json.dumps(q, ensure_ascii=False)
            assert len(body.encode()) < 250_000, (did, len(body.encode()), 'too big for one hub document')
            open(os.path.join(out, did + '.json'), 'w').write(body); n += len(q['items'])
        print('wrote', len(DECKS), 'review queues,', n, 'cards, into', out)
    else:
        data = []
        for did, name in DECKS:
            d = json.load(open(os.path.join(ROOT, 'build', 'decks', did + '.json')))
            data.append({'id': did, 'name': name, 'cards': [[x['w'], x['ex'], x['means'], x.get('k', 'word'), x.get('d', 0), 1 if x.get('current') else 0, x['src'],
                                                             x.get('hook', ''), wrongs(d, x)] for x in d['items']]})
        page = open(os.path.join(ROOT, 'tools', 'review.html')).read().replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
        open(sys.argv[1], 'w').write(page)
        print('wrote', sys.argv[1], sum(len(x['cards']) for x in data), 'cards')
