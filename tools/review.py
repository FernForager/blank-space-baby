"""Build the card review page (a claude.ai artifact) from the decks in the daily.

    python3 tools/review.py OUT.html

Morg approves, flags or cuts each card there: its sentence, its means line, its tile word (hook) and its color.
Each card also lists the wrong answers it can draw, so a giveaway or a second right answer shows.
Decisions live in the artifact's database, one collection per deck (r_<deck id>), one document per card index,
with the card's answer, sentence, hook and color as reviewed, so Claude can read them back.
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

data = []
for did, name in DECKS:
    d = json.load(open(os.path.join(ROOT, 'build', 'decks', did + '.json')))
    data.append({'id': did, 'name': name, 'cards': [[x['w'], x['ex'], x['means'], x.get('k', 'word'), x.get('d', 0), 1 if x.get('current') else 0, x['src'],
                                                     x.get('hook', ''), wrongs(d, x)] for x in d['items']]})
page = open(os.path.join(ROOT, 'tools', 'review.html')).read().replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
open(sys.argv[1], 'w').write(page)
print('wrote', sys.argv[1], sum(len(x['cards']) for x in data), 'cards')
