"""Apply Morg's text edits from the beta's text editor (research/text-system.md) to build/text/en.json.

    python3 tools/textedits.py FILE [--confirm]   # FILE: the saved reply to SELECT id, body, at FROM texts WHERE applied = 0 ORDER BY id

Read the rows with the Cloudflare tool (the triviela-beta database), save the reply, run this, then rebuild, run
tools/textcheck.py, and mark the rows done: UPDATE texts SET applied = 1 WHERE id <= <the last id this prints>.
Each edit names the text it replaced. If en.json no longer has that text (it changed since Morg's edit), the edit is skipped
and listed, so nothing is overwritten unseen. Later batches win over earlier ones for the same string.
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build'))
import strings

EN = os.path.join(strings.TEXT, 'en.json')

def rows(path):
    d = json.load(open(path))
    while isinstance(d, list) and d and isinstance(d[0], dict) and 'results' in d[0]: d = d[0]['results']   # the tool's reply shape
    if isinstance(d, dict) and 'results' in d: d = d['results']
    return sorted(d, key=lambda r: r['id'])

GUARDED = ('brand', 'share.site', 'share.title', 'image.file', 'meta.description')

def main(path, confirm=False):
    src = open(EN).read()
    text, meta = strings.load()
    final, last = {}, 0
    for r in rows(path):
        last = max(last, r['id'])
        for e in json.loads(r['body']): final[e['id']] = (e['from'], e['to'], r['at'])
    done, skipped, held = [], [], []
    for k, (was, to, at) in final.items():
        if k not in text: skipped.append(f'{k}: no such string now'); continue
        if text[k] == to: continue
        if text[k] != was: skipped.append(f'{k}: changed since the edit (now “{text[k]}”, edit was from “{was}” to “{to}”)'); continue
        # anyone who finds a preview link can post an edit (the audit, Oct 30, 2026): the game's name and address, and any
        # new web or email address, wait for Morg to say the edit is his
        if not confirm and (k in GUARDED or re.search(r'[\w-]+\.[a-z]{2,}\b|@', to.replace(was, ''))):
            held.append(f'{k}: “{text[k]}” → “{to}” (the game’s name or address, or a new web address: confirm with Morg, then rerun with --confirm)'); continue
        pat = re.compile(r'^(\s*' + re.escape(json.dumps(k)) + r':\s*)' + re.escape(json.dumps(text[k], ensure_ascii=False)) + r'(,?\s*)$', re.M)
        if len(pat.findall(src)) != 1: skipped.append(f'{k}: couldn’t find its line in en.json'); continue
        src = pat.sub(lambda m: m.group(1) + json.dumps(to, ensure_ascii=False) + m.group(2), src)
        done.append(f'{k}: “{text[k]}” → “{to}”')
    if done:
        open(EN, 'w').write(src)
        new, newmeta = strings.load()   # the same checks as the build, before anything else runs
        bad = [p for p in strings.problems(new, newmeta, open(os.path.join(os.path.dirname(strings.TEXT), 'template.html')).read()) if p[0] in final]
        for p in bad: print('problem:', p)
    print(f'{len(done)} applied' + (f', {len(skipped)} skipped' if skipped else '') + (f', {len(held)} held' if held else ''))
    for x in done: print('  ', x)
    for x in skipped: print('   skipped', x)
    for x in held: print('   held', x)
    if last and not held: print(f'then: UPDATE texts SET applied = 1 WHERE id <= {last}')
    elif last: print('held edits stay unapplied: once Morg confirms, rerun with --confirm, then mark the rows done')

if __name__ == '__main__':
    main(sys.argv[1], '--confirm' in sys.argv[2:])
