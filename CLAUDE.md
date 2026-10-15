# Blank Space Baby — brief for every session

Read this first. It holds the decisions already made so nobody re-learns them.

## What it is
A fill-in-the-blank arcade word game for a youth girls' soccer team (Seattle Celtic G14, players ~12–14) and their parents. Built by Morg (owner, names everything, approves all player-facing text) with Claude. Soft-launching standalone at https://fernforager.github.io/blank-space-baby/ ; later it folds into the team's Carpool HQ app (repo FernForager/carpool-hq) as Arcade game #2 by copying `docs/index.html` into HQ's Arcade.

## Working with Morg
- He's an English major and veteran editor/localizer, new to coding, learning by building. Explain in plain language. Suggest better workflows when you see them.
- He works almost entirely from the Claude iOS app on an iPhone 17. Give steps that work on the phone; say up front when something needs a computer or the web.
- He names everything and approves all player-facing text (titles, labels, prompts, reactions). Anything you write for players is a placeholder until he signs off.
- `main` is the live site. **Never push to `main` without Morg's OK.** Work on a branch, show him, then merge when he says so.
- He wants directness, honest pushback, short answers when short is right, and small fixes done now rather than later.
- Keep usage lean.

## How to build and check
```
python3 build/build.py      # checks every card, writes docs/index.html
```
- `build/template.html`: the whole game (HTML, CSS, JS in one file). `__LEVELS__` is replaced with the decks.
- `build/head.html`: the page head (Home Screen meta, icons, manifest).
- `build/decks/*.json`: one deck per level. `SPEC.md` there is the deck-writing spec. Read it before editing a deck.
- `docs/`: what GitHub Pages serves (index.html, icons, manifest). Don't hand-edit docs/index.html; rebuild it.
- Test in headless Chromium (Playwright is preinstalled in Claude's cloud workspace) at 402×744 (his phone in the Claude viewer), 375×667 and 320×568. Every screen must fit with no scrolling. Zoom in on punctuation, line ends and icon pixels before calling anything done, not just the whole screen at a glance.

## The game
- Cabinet look: the phone is an arcade cabinet on club green #0B8343 (sampled from the Seattle Celtic logo). Marquee sign up top, a CRT screen in a black bezel (scanlines, glowing green pixel text), a black control panel with push-buttons, and two orange coin slots (hidden on short phones).
- Title screen: the sign is dark, the title plays on the CRT, and a big round green start button lights the sign.
- Level select: five round arcade buttons in one row, icons only (no labels). Gen Alpha = phone with a deadpan face, Parents = orange cassette, Soccer Fanatics = soccer ball, Swifties = rainbow friendship bracelet, Premier League = gold trophy. A beaten level's ring glows green. The CRT shows the locked final boss with five progress lights.
- Play: one sentence with a blinking dashed blank and three cream buttons. Right = green with a pixel ✓. Wrong = red with a pixel ✕ and a shake, and the other choice dims. After answering, the screen shows the answer, its short meaning and the full sentence. Only the right answer's meaning shows, plus your own wrong pick's; the untouched choice stays unexplained.
- 5 right in a row beats a level. One miss ends that run (retry with the replay icon). Beaten levels stay beaten on the device (localStorage `bsb-cleared`). All five wake the final boss, whose game is TBD. Each level walks a saved shuffled order (`bsb-q-<id>`) so replays bring new cards. The right answer never lands in the same slot 3 times running.
- Fonts: Press Start 2P (marquee, title, numbers) and Pixelify Sans (everything else). Pixelify draws 5 like an S, so the code sets every digit in Press Start 2P. Its "fi" ligature looks like an A, so ligatures are off. Keep both fixes.
- Less is more: no instructions, labels or congrats text. Icons, color and layout carry it.

## House style for all text (strict)
- One plain sentence per card, deadpan school-workbook tone. The answer supplies the fun.
- No period at the end (!, ?, ?! and … are fine). **Never semicolons, anywhere.** Use commas, colons, em dashes (closed up: word—word) or periods.
- Curly quotes and apostrophes only. Scores and ranges use an en dash (6–0, 2025–26). American spelling.
- Punctuation never wraps away from the word or blank it touches. Hyphenated words and ranges never break across lines (the code handles both).
- Slang decks (Gen Alpha, Parents, Soccer Fanatics): every sentence is about soccer. No proper names, real or made up. Use roles (the coach, the ref, the keeper, the striker, the captain) and Mom, Dad, Grandpa, Grandma.
- Trivia decks (Swifties, Premier League): plain factual sentences, real names allowed.
- Kid-safe: anything borderline (sexual, drugs, alcohol, slurs, mean-spirited, private-life gossip) is out. When unsure, cut it.
- No song lyrics or quoted lines from songs, books or films, not even fragments.

## Sources per deck
- Gen Alpha: Merriam-Webster first, Dictionary.com Slang (2023+ entries) as the advance guard; M-W's sense wins. No older slang. Meanings are our own short wording.
- Parents (slang of parents aged ~40–50, teens around 1989–2004, mostly '90s): M-W first, Green's Dictionary of Slang second; words picked by when they peaked.
- Soccer Fanatics: M-W (soccer sense) first, Dictionary.com (including its Collins British entries) second. Terms in neither are out (e.g. worldie, golazo, top bins, park the bus, brace).
- Swifties: official sources first (taylorswift.com, the Recording Academy, RIAA, Billboard), Wikipedia second. No personal life.
- Premier League: premierleague.com first. Items with `"current": true` (champion, promoted clubs, managers) are as of Oct 14, 2026 and need checking every season.
- Research anything that could have changed. Don't trust memory for current facts.

## Open
- Final boss game: TBD (Morg decides).
- Morg may rename or redraw any icon; the soccer ball is the weakest.
