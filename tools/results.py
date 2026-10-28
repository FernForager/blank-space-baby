"""Sum up the playtest's anonymous results (Morg, Oct 19, 2026).

    python3 tools/results.py FILE [--beta]

FILE is the reply to this query on the triviela-beta database (the Cloudflare tool), saved as JSON:
    SELECT day, score, ids, res, path, host, at FROM results ORDER BY id
Players' rows only (host 'real'), unless --beta, which also counts Morg's own testing on preview links.
Prints, per puzzle: boards finished and the average score, then each color's hit rate, which color players
tap first, and the cards missed most often.
"""
import json, os, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def rows(path):
    d = json.load(open(path))
    while isinstance(d, list) and d and isinstance(d[0], dict) and 'results' in d[0]: d = d[0]['results']
    if isinstance(d, dict) and 'results' in d: d = d['results']
    return d

def cards():   # card id -> (color, deck, answer, sentence)
    out = {}
    for f in sorted(os.listdir(os.path.join(ROOT, 'build', 'decks'))):
        if not f.endswith('.json'): continue
        D = json.load(open(os.path.join(ROOT, 'build', 'decks', f))); items = D['items'] if isinstance(D, dict) else D
        for i, x in enumerate(items):
            out[f[:-5] + ':' + str(x.get('i', i))] = (x.get('d'), f[:-5], x.get('w'), x.get('ex'))
    return out

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(1)
    R = [r for r in rows(sys.argv[1]) if r['host'] == 'real' or '--beta' in sys.argv]
    if not R: print('no finished boards yet'); return
    C = cards(); COL = {1: 'green', 2: 'yellow', 3: 'red'}
    by_day = collections.defaultdict(list)
    for r in R: by_day[r['day']].append(r['score'])
    print(f'{len(R)} finished boards')
    size = {r['day']: len(r['ids'].split()) for r in R}   # a day's cards: 9 since Oct 27, 2026, 15 before
    for d in sorted(by_day): s = by_day[d]; print(f'  #{d + 1}: {len(s)} boards, average {sum(s) / len(s):.1f}/{size[d]}, {s.count(size[d])} GOLAZO!')
    hit, seen, first, miss = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    for r in R:
        ids, res, path = r['ids'].split(), r['res'], [int(x) for x in r['path'].split()]
        first[COL.get(C.get(ids[path[0]], (0,))[0], '?')] += 1
        for cid, v in zip(ids, res):
            col = COL.get(C.get(cid, (0,))[0], '?'); seen[col] += 1; seen[cid] += 1
            if v == '1': hit[col] += 1; hit[cid] += 1
            else: miss[cid] += 1
    print('right by color: ' + ', '.join(f'{c} {100 * hit[c] / seen[c]:.0f}%' for c in ('green', 'yellow', 'red') if seen[c]))
    print('first tap: ' + ', '.join(f'{c} {n}' for c, n in first.most_common()))
    worst = sorted((m for m in miss if seen[m] >= 3), key=lambda m: hit[m] / seen[m])[:10]
    if worst: print('missed most (3+ plays):')
    for m in worst:
        col, deck, w, ex = C.get(m, (0, '?', '?', '?'))
        print(f'  {m} ({COL.get(col, "?")}): right {hit[m]} of {seen[m]}  |  {ex}  ({w})')

if __name__ == '__main__':
    main()
