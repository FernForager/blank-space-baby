"""Render docs/og.png, the 1200x630 picture shown when the game's link is texted or posted.

    python3 tools/og.py

The cabinet with the sign lit and one sample card on the screen. Change CARD to show a different one.
"""
import asyncio, os
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(ROOT, 'docs', 'index.html')).read()
CARD = 'The halftime orange slices were <span class="nb"><span class="blank"></span></span>'
STYLE = """
  body { background: #0B8343; } .cab { max-width: 300px; gap: 8px; padding: 10px 14px 0; } .coin { display: none !important; }
  .marquee { padding: 10px 8px 11px; } .cab[data-v="title"] .marquee h1 { opacity: 1 !important; font-size: 13px; }
  .cab[data-v="title"] .arc .cap { filter: none !important; } .arc .ring { width: 50px !important; height: 50px !important; } .cab[data-v="title"] .panel { height: 72px !important; padding: 0 12px; }
  .screen { padding: 12px 16px; } #v-title .logo { display: none !important; }
  #v-title .demo { display: flex !important; flex: 1; align-self: stretch; flex-direction: column; justify-content: center; }
  #dq { font-size: 23px !important; } .blank { animation: none !important; }
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 600, 'height': 315}, device_scale_factor=2)
        await pg.route('http://bsb.test/', lambda r: r.fulfill(body=HTML, content_type='text/html'))
        await pg.goto('http://bsb.test/'); await pg.wait_for_timeout(1500)
        await pg.add_style_tag(content=STYLE)
        await pg.evaluate("c => { document.getElementById('dq').innerHTML = c; }", CARD)
        await pg.wait_for_timeout(300); await pg.screenshot(path=os.path.join(ROOT, 'docs', 'og.png')); await b.close()
    print('wrote docs/og.png')
asyncio.run(main())
