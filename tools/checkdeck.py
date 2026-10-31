"""Check one deck file against the house style and the deck spec, without building the game.

    python3 tools/checkdeck.py build/decks/mls.json      # prints problems, exits 1 if any

Uses the same rules as build/build.py (house style, hooks and difficulty), plus: every item needs a source,
answers stay short, and each kind needs at least 4 items.
"""
import json, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build'))
from build import check

path = sys.argv[1]
deck = json.load(open(path))
items = deck['items']
bad = [p for p in check(os.path.basename(path).removesuffix('.json'), deck, hooks=True)]   # the deck id names its sets of wrong answers
kinds = collections.Counter(it.get('k', 'word') for it in items)
for k, n in kinds.items():
    if n < 4: bad.append((k, 'kind has fewer than 4 items', n))
seen = collections.Counter(it['w'].lower() for it in items)
for it in items:
    w = it['w']
    if not it.get('src', '').startswith('http'): bad.append((w, 'missing src URL'))
    if len(w) > 20: bad.append((w, 'answer over 20 characters'))
    if seen[w.lower()] > 1: bad.append((w, 'same answer used more than once (allowed, but check the cards differ)'))
for p in bad: print(*p, sep=' | ')
print(f'{path}: {len(items)} items, {len(kinds)} kinds, {len(bad)} problems')
sys.exit(1 if any('allowed, but' not in str(p) for p in bad) else 0)
