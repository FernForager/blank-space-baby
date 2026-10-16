"""Build the card review page (a claude.ai artifact) from the new soccer decks.

    python3 tools/review.py OUT.html

Morg approves, flags or cuts each card there. Decisions live in the artifact's database,
one collection per deck (r_<deck id>), one document per card index, so Claude can read them back.
"""
import json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECKS = [('mls','MLS'),('nwsl','NWSL'),('intl-men','International Men’s'),('intl-women','International Women’s'),('wc26','World Cup 2026'),
         ('laliga','La Liga'),('bundesliga','Bundesliga'),('seriea','Serie A'),('ligue1','Ligue 1'),('ligamx','Liga MX'),('ucl','Champions League'),
         ('rules','Soccer Rules'),('legends','Soccer Legends'),('nicknames','Club Nicknames'),('awards','Awards'),('epl-more','EPL (new cards)'),('lingo-more','Soccer Lingo (new words)')]
data = []
for did, name in DECKS:
    d = json.load(open(os.path.join(ROOT, 'build', 'decks', did + '.json')))
    data.append({'id': did, 'name': name, 'cards': [[x['w'], x['ex'], x['means'], x['k'], x.get('d', 0), 1 if x.get('current') else 0, x['src']] for x in d['items']]})
page = open(os.path.join(ROOT, 'tools', 'review.html')).read().replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
open(sys.argv[1], 'w').write(page)
print('wrote', sys.argv[1], sum(len(x['cards']) for x in data), 'cards')
