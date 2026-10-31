"""Render docs/og.png, the 1200×630 picture iMessage and other apps show when triviela.net is texted or posted.

    python3 tools/og.py                      # the chosen direction (DIRECTION below) into docs/og.png
    python3 tools/og.py B out/og-B.png 2     # one direction into a file, at 1× or 2× (to zoom in on the edges)
    python3 tools/og.py all out [SCALE]      # every direction into a folder, as og-A.png, og-B.png, og-C.png

A poster from the real build's own pieces, never a screenshot of the phone (Morg, Oct 31, 2026: "a billboard you'd see on a
Tokyo train, a cool compelling collage of our best elements"). The page is loaded through tools/docsroute.py like the other
tools, then its own pieces are moved into a 1200×630 layout: the sign (the dot-matrix board, redrawn by the page's own
drawSign at poster size), the three balls from the screen with every panel lit, tiles from board #1 with their real hooks,
and the sign's pixel ball. The only words are the sign and Morg's line "daily ⚽ trivia" (his words, Oct 31, 2026), the ⚽ drawn
as the game draws one in a string, its own pixel ball, so it looks the same on every phone.

The directions: A, lights, the sign's dot field over the CRT with the three balls lit under it, the sign alone.
B, collage, the cabinet's cream and green trim, the sign in its rim at a tilt, three fanned tiles, the balls and the line in ink.
C, three cards, the control panel's black, the sign across the top, a tile of each color and the line in the screen's glow.
"""
import asyncio, os, sys
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docsroute import route
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = open(os.path.join(ROOT, 'docs', 'index.html')).read()
DIRECTION = 'B'   # the poster the site uses, Morg's pick
W, H = 1200, 630
HOOKS = ['scorer', 'never played', 'Champions']   # one tile a color from board #1 (Basics, Messi, CR7), all approved or locked

CSS = """
#poster { position: fixed; inset: 0; width: 1200px; height: 630px; overflow: hidden; z-index: 50; font-family: var(--body-font); font-weight: 600; color: var(--text); }
#poster > * { position: absolute; }
#poster .marquee.dm { height: auto; padding: 0; margin: 0; }
#poster .marquee.dm .subhead { visibility: hidden; }
#poster .marquee.dm canvas { inset: 0; width: 100%; height: 100%; }
#poster .marquee .menu-b { display: none; }
#poster .balls { display: flex; width: auto; column-gap: 0; }
#poster .balls .ball { width: 170px; flex: none; }
#poster .balls .bi { overflow: visible; }
#poster .tile { width: 300px; height: 230px; min-height: 0; padding: 16px 20px 14px; border-radius: 24px; box-shadow: 0 10px 0 var(--btn-edge), 0 16px 22px rgba(0,0,0,.25); transform-origin: 50% 50%; }
#poster .tile.c1::after, #poster .tile.c2::after, #poster .tile.c3::after { top: 16px; right: 18px; width: 30px; height: 42px; border-radius: 6px; box-shadow: 0 0 0 2px rgba(0,0,0,.18); }
#poster .tile .tag { font-size: 33px; line-height: 1; letter-spacing: 0; max-width: calc(100% - 72px); }
#poster .tile .hk { font-size: 44px; line-height: 1.15; letter-spacing: 0; text-align: center; margin: auto 0; }
#poster .line { margin: 0; white-space: nowrap; line-height: 1; font-size: 77px; }
#poster .line .tball { --bu: 3px; height: .64em; margin: 0 .08em; vertical-align: baseline; }
#poster .line .tball svg { bottom: calc(.318em - 9.5 * var(--bu)); }
#poster .scan { inset: 0; pointer-events: none; z-index: 5; background: repeating-linear-gradient(0deg, rgba(0,0,0,.2) 0 2px, transparent 2px 6px); box-shadow: inset 0 0 90px rgba(0,0,0,.7); }
#poster .trim { top: 0; bottom: 0; width: 14px; background: var(--body-dark); }
#poster .trim.l { left: 0; } #poster .trim.r { right: 0; }

/* A: the sign alone, the cabinet's own stack edge to edge: the dot board over the screen, the three balls lit on it */
#poster[data-d="A"] { background: radial-gradient(130% 110% at 50% 60%, #0D2216 0%, #07130C 70%); }
#poster[data-d="A"] .marquee { left: 0; top: 0; width: 1200px; height: 396px; border-radius: 0; box-shadow: inset 0 -3px 0 #000, 0 4px 0 var(--body-dark); }
#poster[data-d="A"] .marquee.dm canvas { inset: 8px 0 12px; height: calc(100% - 20px); }
#poster[data-d="A"] .scan { top: 400px; }
#poster[data-d="A"] .balls { left: 50%; top: 418px; transform: translateX(-50%); column-gap: 72px; }
#poster[data-d="A"] .balls .ball { width: 192px; }

/* B: the collage on the cabinet's cream body, with its green trim */
#poster[data-d="B"] { background: var(--body); }
#poster[data-d="B"] .marquee { left: 40px; top: 36px; width: 860px; height: 200px; transform: rotate(-2.5deg); }
#poster[data-d="B"] .marquee.dm canvas { inset: 12px; width: calc(100% - 24px); height: calc(100% - 24px); }
#poster[data-d="B"] .crt { left: 44px; top: 396px; width: 500px; height: 200px; padding: 10px; box-sizing: border-box; border-radius: 22px; background: var(--bezel); box-shadow: 0 4px 0 var(--body-dark), inset 0 0 0 2px #222; transform: rotate(2deg); }
#poster[data-d="B"] .crt .screen { position: relative; height: 100%; border-radius: 13px; overflow: hidden; background: radial-gradient(130% 110% at 50% 40%, #0D2216 0%, #07130C 70%); display: flex; align-items: center; justify-content: center; }
#poster[data-d="B"] .crt .screen::after { content: ""; position: absolute; inset: 0; pointer-events: none; border-radius: inherit; background: repeating-linear-gradient(0deg, rgba(0,0,0,.22) 0 2px, transparent 2px 6px); box-shadow: inset 0 0 40px rgba(0,0,0,.7); }
#poster[data-d="B"] .balls { position: static; column-gap: 24px; }
#poster[data-d="B"] .balls .ball { width: 126px; }
#poster[data-d="B"] .tile { width: 250px; height: 190px; }
#poster[data-d="B"] .tile.t0 { left: 928px; top: 52px; transform: rotate(5deg); }
#poster[data-d="B"] .tile.t1 { left: 604px; top: 300px; transform: rotate(-5deg); }
#poster[data-d="B"] .tile.t2 { left: 884px; top: 372px; transform: rotate(4deg); }
#poster[data-d="B"] .line { left: 46px; top: 282px; color: var(--btn-ink); }
#poster[data-d="B"] .line .tball svg { background: var(--btn-ink); border-radius: 50%; }   /* on cream the sprite's open pixels need ink behind them, or its patches vanish */

/* C: three cards on the control panel */
#poster[data-d="C"] { background: linear-gradient(180deg, #1A1D1B 0%, #0D0F0E 100%); }
#poster[data-d="C"] .marquee { left: 60px; top: 30px; width: 1080px; height: 214px; }
#poster[data-d="C"] .marquee.dm canvas { inset: 9px 12px; width: calc(100% - 24px); height: calc(100% - 18px); }
#poster[data-d="C"] .tile { width: 330px; height: 210px; top: 268px; }
#poster[data-d="C"] .tile .hk { font-size: 55px; }
#poster[data-d="C"] .tile.t0 { left: 60px; } #poster[data-d="C"] .tile.t1 { left: 435px; } #poster[data-d="C"] .tile.t2 { left: 810px; }
#poster[data-d="C"] .line { left: 0; right: 0; top: 514px; text-align: center; color: var(--glow); text-shadow: 0 0 6px rgba(92,240,154,.55); }
"""

JS = """
async (o) => {
  const Q = s => document.querySelector(s);
  const st = document.createElement('style'); st.textContent = o.css; document.head.appendChild(st);
  const P = document.createElement('div'); P.id = 'poster'; P.dataset.d = o.dir; document.body.appendChild(P);
  const el = (cls, ...kids) => { const d = document.createElement('div'); d.className = cls; d.append(...kids); return d; };
  // the sign: the page's own marquee, moved in whole, so drawSign redraws its dots at the poster's size on resize
  const sign = Q('.marquee');
  // the balls, cloned from the board's screen, every panel and the rim lit (the perfect day's look, in each ball's own color)
  const balls = Q('#v-board .balls').cloneNode(true);
  balls.querySelectorAll('.pt').forEach(p => p.classList.add('on'));
  balls.querySelectorAll('.bi').forEach(b => b.classList.remove('full'));
  // tiles from today's board, by hook, as the board draws them (its category and its hook, the color card in the corner)
  const tiles = [...document.querySelectorAll('#p-board .tile')];
  const tile = (hook, k) => {
    const t = tiles.find(t => t.querySelector('.hk').textContent.replace(/\\u00a0/g, ' ') === hook);
    if (!t) throw new Error('no tile on the board with the hook ' + hook);
    const c = t.cloneNode(true); c.removeAttribute('style'); c.removeAttribute('disabled'); c.classList.add('t' + k);
    c.querySelectorAll('.hk, .tag').forEach(e => e.removeAttribute('style')); return c;
  };
  // Morg's line, the ⚽ as the sign's own pixel ball (the game's way of drawing one in a string)
  const ball = Q('.subhead .tball');
  const line = () => { const p = document.createElement('p'); p.className = 'line'; p.append('daily ', ball.cloneNode(true), ' trivia'); return p; };
  if (o.dir === 'A') { P.append(sign, balls, el('scan')); }
  if (o.dir === 'B') { P.append(el('trim l'), el('trim r'), sign, el('crt', el('screen', balls)), ...o.hooks.map(tile), line()); }
  if (o.dir === 'C') { P.append(sign, ...o.hooks.map(tile), line()); }
  await document.fonts.ready;
  window.dispatchEvent(new Event('resize'));
  await new Promise(r => setTimeout(r, 100));
  // drawSign keeps the menu's room at the right (34 px in its pitch), so the name sits a little left of the middle: shift the
  // canvas by half the difference between its two side gaps (its own numbers: 47 font pixels across, 2 dots each, 3 spare)
  const c = Q('#sign'), w = c.clientWidth, pitch = (w - 34) / 97, nx = Math.floor(w / pitch), ox = Math.floor((nx - 96) / 2);
  const gapL = (ox + 1) * pitch, gapR = w - (ox + 95) * pitch; c.style.transform = 'translateX(' + ((gapR - gapL) / 2).toFixed(1) + 'px)';
  return [w, c.clientHeight, pitch.toFixed(2), Math.floor(c.clientHeight / pitch), ((gapR - gapL) / 2).toFixed(1)];
}
"""

async def render(dir, out, scale):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=scale)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.route('http://bsb.test/**', route(HTML))
        await pg.goto('http://bsb.test/?day=1&reset'); await pg.wait_for_timeout(1500)
        await pg.evaluate("document.fonts.ready.then(() => 1)")
        info = await pg.evaluate(JS, {'dir': dir, 'css': CSS, 'hooks': HOOKS})
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=out); await b.close()
    if errs: print('JS ERRORS', errs)
    print('wrote', os.path.relpath(out, ROOT), 'direction', dir, 'at', str(scale) + '×', 'sign', info)

def main():
    a = sys.argv[1:]
    if not a: return asyncio.run(render(DIRECTION, os.path.join(ROOT, 'docs', 'og.png'), 1))
    scale = int(a[2]) if len(a) > 2 else 1
    if a[0] == 'all':
        os.makedirs(a[1], exist_ok=True)
        for d in 'ABC': asyncio.run(render(d, os.path.join(a[1], f'og-{d}.png'), scale))
    else: asyncio.run(render(a[0].upper(), a[1], scale))
main()
