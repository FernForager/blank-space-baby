"""After main moves: play today's board on the live triviela.net, as a new phone in Seattle time.

    python3 tools/livecheck.py

Run it once triviela.net serves the new build. Checks the page is docs/index.html byte for byte (apart from Cloudflare’s visit counter), How to play opens on a
first visit, today's board is the build's, Back works, the real site never shows Flag or Lock or calls the beta's services,
a full day ends on the end screen with its grid, the share text is exact, and the result post is well formed. The post is
caught here, so no row reaches the results table.
"""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright
from docsroute import route
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = open(os.path.join(ROOT, 'docs', 'index.html')).read()
TEXT = json.load(open(os.path.join(ROOT, 'build', 'text', 'en.json')))   # the share's own words
fails = []
def ok(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond: fails.append(what)

def expected(s, n):   # the share text for a saved day, the same as expected() in tools/lifecycle.py
    cols = [[('⚽' if s['res'][i] == 1 else '❌') for i in range(15) if s['tiles'][i]['d'] == d] for d in (1, 2, 3)]
    rows = [''.join(cols[d][j] for d in range(3)) for j in range(5)]
    right = sum(1 for r in s['res'] if r == 1)
    return TEXT['share.title'].replace('{day}', str(n)) + '\n⬜🟨🟥\n' + '\n'.join(rows) + '\n' + ('GOLAZO!' if right == 15 else f'{right}/15') + '\n' + TEXT['share.tagline'] + '\n' + TEXT['share.site']

state = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('bsb-daily'))")
view = lambda pg: pg.evaluate("document.getElementById('cab').dataset.v")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        opts = dict(timezone_id='America/Los_Angeles', service_workers='block', reduced_motion='reduce')
        # today's board as the build deals it
        ctx = await b.new_context(**opts); pg = await ctx.new_page()
        await pg.add_init_script("try { localStorage.setItem('bsb-intro-off', 'true') } catch (e) {}")
        await pg.route('https://bsb.test/**', route(BUILD)); await pg.goto('https://bsb.test/'); await pg.wait_for_timeout(400)
        want = await state(pg); await ctx.close()
        # the live site, as a new phone
        ctx = await b.new_context(viewport={'width': 402, 'height': 744}, device_scale_factor=3, **opts)
        await ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin='https://triviela.net')
        pg = await ctx.new_page(); errs, posts, beta = [], [], []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        async def catch(r):   # the result post stops here
            posts.append(json.loads(r.request.post_data or 'null')); await r.fulfill(status=200, body='{"ok":true}', content_type='application/json')
        async def refuse(r):
            beta.append(r.request.url); await r.fulfill(status=204, body='')
        await pg.route('**/api/result', catch); await pg.route('**/api/mark', refuse); await pg.route('**/api/text', refuse)
        resp = await pg.goto('https://triviela.net/'); await pg.wait_for_timeout(1500)
        live = re.sub(r'<script[^>]*static\.cloudflareinsights\.com/beacon[^>]*>\s*</script>\n?', '', await resp.text())   # Cloudflare’s visit counter, added to pages browsers fetch
        ok(live == BUILD, 'triviela.net serves docs/index.html byte for byte, apart from Cloudflare’s visit counter')
        ok(await pg.evaluate("!document.getElementById('intro').hidden"), 'a first visit opens How to play over the board')
        await pg.evaluate("localStorage.setItem('bsb-intro-off', 'true')"); await pg.reload(); await pg.wait_for_timeout(1500)
        s = await state(pg); n = s['day'] + 1
        ok([(t['id'], t['ch']) for t in s['tiles']] == [(t['id'], t['ch']) for t in want['tiles']], f'#{n} is the build’s board, its cards and choices')
        await pg.click('[data-i="7"]'); await pg.wait_for_timeout(500)
        ok('back' in await pg.evaluate("document.getElementById('go').className"), 'an open card offers Back')
        await pg.click('#go'); await pg.wait_for_timeout(500)
        ok(await view(pg) == 'board', 'Back returns to the board')
        for i in range(15):   # two misses
            await pg.click(f'[data-i="{i}"]'); await pg.wait_for_timeout(450)
            w = await pg.evaluate("document.getElementById('q').dataset.w")
            ch = await pg.evaluate("[...document.querySelectorAll('.choice')].map(b => b.dataset.w)")
            await pg.click(f'.choice[data-w="{w if i not in (2, 11) else next(x for x in ch if x != w)}"]'); await pg.wait_for_timeout(450)
            if i == 0: ok(await pg.evaluate("document.getElementById('b-flag').hidden && document.getElementById('b-lock').hidden"), 'no Flag or Lock keys')
            await pg.click('#go'); await pg.wait_for_timeout(450)
        await pg.wait_for_timeout(1500); s = await state(pg)
        ok(await view(pg) == 'end' and s['res'].count(2) == 2 and s['res'].count(1) == 13, 'a full day ends on the end screen, 13 right and 2 missed')
        ok(await pg.evaluate("document.querySelectorAll('.egrid .egh').length") == 3 and await pg.evaluate("document.querySelectorAll('.egrid .mk').length") == 15, 'the end grid has its three card headers and 15 marks')
        await pg.click('#share'); await pg.wait_for_timeout(400)
        clip = await pg.evaluate("navigator.clipboard.readText()")
        ok(clip == expected(s, n), 'the share text is exact: ' + repr(clip))
        ok(len(posts) == 1 and posts[0]['day'] == s['day'] and len(posts[0]['ids']) == 15 and posts[0]['res'] == s['res'] and sorted(posts[0]['path']) == list(range(15)), f'one result post, well formed, caught before the server ({len(posts)})')
        ok(not beta, 'no calls to the beta’s services ' + str(beta))
        ok(not errs, 'no script errors ' + str(errs))
        await ctx.close(); await b.close()
    print('all good' if not fails else f'{len(fails)} failed')
    sys.exit(1 if fails else 0)
asyncio.run(main())
