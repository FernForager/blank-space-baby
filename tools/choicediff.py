"""Before and after: every card's fingerprint and its choices over a year, a git ref's build against the working tree's.

    python3 tools/choicediff.py [REF] [DAYS]     # default origin/daily and 366 days (puzzles #1 to #366)

Builds REF in a throwaway worktree, reads the working tree's docs/index.html as built (run build/build.py first), and
compares them card by card: the fingerprint its verdicts hold to (build.py's fingerprint), the wrong answers its reviewers
see (wrong_pool), and its three choices with their meaning lines on every day (the page's TRIVIELA.choices). Prints each
card that differs and exits 1 if any does. It proved the move to the sets (build/library/wrong.json, Oct 31, 2026): zero
differences. After a set is edited, it lists the cards whose fingerprints and choices moved.
"""
import asyncio, hashlib, inspect, json, os, subprocess, sys, tempfile
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from docsroute import route
REF = sys.argv[1] if len(sys.argv) > 1 else 'origin/daily'
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 366

PRINTS = r'''
import inspect, json, os, sys
sys.path.insert(0, 'build'); import build as B
by_did = 'did' in inspect.signature(B.fingerprint).parameters   # the sets (Oct 31, 2026) added the deck id to both
out = {}
for did, _, _ in B.DAILY:
    deck = json.load(open(os.path.join(B.DECKS, did + '.json'))); clash = B.clasher(deck)
    for i, it in enumerate(deck['items']):
        fp = B.fingerprint(did, deck, i, clash) if by_did else B.fingerprint(deck, i, clash)
        pool = B.wrong_pool(did, deck, it, clash) if by_did else B.wrong_pool(deck, it, clash)
        out[f'{did}:{i}'] = [fp, sorted(pool)]
print(json.dumps(out, ensure_ascii=False))
'''
CHOICES = '''([ids, days]) => { const T = window.TRIVIELA, by = {}; T.ALL.forEach(c => { by[c.id] = c; });
  return ids.map(id => { const c = by[id], s = [];
    for (let d = 0; d < days; d++) s.push(T.choices(c, d).map(x => x.w + ' — ' + x.m).join(' | '));
    return s; }); }'''

def prints(tree):
    return json.loads(subprocess.run([sys.executable, '-c', PRINTS], cwd=tree, capture_output=True, text=True, check=True).stdout)

async def choices(html):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.route('http://bsb.test/**', route(html))
        await pg.goto('http://bsb.test/?day=1&reset'); await pg.wait_for_timeout(300)
        ids = await pg.evaluate('() => window.TRIVIELA.ALL.map(c => c.id)')
        out = {}
        for n in range(0, len(ids), 40):
            for cid, days in zip(ids[n:n + 40], await pg.evaluate(CHOICES, [ids[n:n + 40], DAYS])): out[cid] = days
        await b.close()
    return out

def main():
    tmp = tempfile.mkdtemp(prefix='choicediff-')
    subprocess.run(['git', '-C', ROOT, 'worktree', 'add', '--detach', '-q', tmp, REF], check=True)
    try:
        subprocess.run([sys.executable, 'build/build.py'], cwd=tmp, capture_output=True, text=True, check=True)
        old_html, new_html = open(os.path.join(tmp, 'docs', 'index.html')).read(), open(os.path.join(ROOT, 'docs', 'index.html')).read()
        old_fp, new_fp = prints(tmp), prints(ROOT)
    finally:
        subprocess.run(['git', '-C', ROOT, 'worktree', 'remove', '--force', tmp], check=True)
    old_ch, new_ch = asyncio.run(choices(old_html)), asyncio.run(choices(new_html))
    bad = 0
    for cid in sorted(set(old_fp) | set(new_fp)):
        a, b = old_fp.get(cid), new_fp.get(cid)
        if a != b:
            bad += 1
            print(f'{cid}: fingerprint {a and a[0]} → {b and b[0]}' + (f', wrong answers {a and a[1]} → {b and b[1]}' if (a and a[1]) != (b and b[1]) else ''))
    played = sorted(set(old_ch) | set(new_ch))
    for cid in played:
        a, b = old_ch.get(cid), new_ch.get(cid)
        if a == b: continue
        bad += 1
        if not a or not b: print(f'{cid}: plays only {"after" if b else "before"}'); continue
        diff = [d for d in range(DAYS) if a[d] != b[d]]
        print(f'{cid}: choices differ on {len(diff)} of {DAYS} days, first on day index {diff[0]}: {a[diff[0]]}  →  {b[diff[0]]}')
    digest = lambda ch: hashlib.sha1(json.dumps(ch, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    print(f'{REF} against the working tree: {len(set(old_fp) | set(new_fp))} fingerprints, {len(played)} playing cards × {DAYS} days of choices '
          f'(digests {digest(old_ch)} and {digest(new_ch)}), {bad} differences')
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
