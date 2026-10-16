# Triviela — brief for every session

Read this first. It holds the decisions already made so nobody re-learns them. Then read DOSSIER.md for where things stand, what’s been tried and what’s next.

## What it is
**Triviela** (trivia + trivela, the outside-of-the-foot curling kick, Morg's coinage on Oct 15, 2026. One L. Portuguese spells the kick "trivela" and has no "triviela" variant, so the extra i is ours and deliberate) is a public, standalone soccer trivia game: a daily puzzle in an arcade-cabinet look. It began as a word game for Morg's daughter's youth team (Seattle Celtic G14) and grew into its own thing on Oct 16, 2026, so it no longer folds into Carpool HQ. Built by Morg (owner, names everything, approves all player-facing text) with Claude. Domain: triviela.net (bought on Squarespace, not yet pointed at Cloudflare Pages). Today it still lives at https://fernforager.github.io/blank-space-baby/. The repo, that address and the saved-progress keys (`bsb-…`) keep the old name Blank Space Baby on purpose.

## Working with Morg
- He's an English major and veteran editor/localizer, new to coding, learning by building. Explain in plain language. Suggest better workflows when you see them.
- He works almost entirely from the Claude iOS app on an iPhone 17. Give steps that work on the phone, and say up front when something needs a computer or the web.
- He names everything and approves all player-facing text (titles, labels, prompts, reactions). Anything you write for players is a placeholder until he signs off.
- `main` is the live site. **Never push to `main` without Morg's OK.** Work on a branch, show him, then merge when he says so.
- He wants directness, honest pushback, short answers when short is right, and small fixes done now rather than later.
- Keep usage lean.
- No semicolons in anything you write for him: replies, docs, code comments, commit messages. He prefers em dashes, colons, commas or periods.

## How to build and check
```
python3 build/build.py      # checks every card, writes docs/index.html
```
- `build/template.html`: the whole game (HTML, CSS, JS in one file). `__LEVELS__` is replaced with the decks.
- `build/head.html`: the page head (Home Screen meta, icons, manifest).
- `build/decks/*.json`: one deck per level. `SPEC.md` there is the deck-writing spec. Read it before editing a deck.
- `docs/`: what GitHub Pages serves (index.html, icons, manifest, `sw.js` for offline play, `og.png` for link previews). Don't hand-edit docs/index.html. Rebuild it. Rerun `python3 tools/og.py` if the look or the icons change.
- Preview links: Cloudflare Pages (project blank-space-baby, output `docs`, no build command) deploys every pushed branch to `https://<branch>.blank-space-baby.pages.dev` within a minute or two. Give Morg that link with every branch so he can play it on his phone before merging. `main` also deploys to https://blank-space-baby.pages.dev, but GitHub Pages stays the official link.
- Test in headless Chromium at device scale 3 (the iPhone is 3×, so 2× hides jaggies) (Playwright is preinstalled in Claude's cloud workspace) at 402×744 (his phone in the Claude viewer), 375×667 and 320×568. Every screen must fit with no scrolling. Zoom in on punctuation, line ends and icon pixels before calling anything done, not just the whole screen at a glance.

## Palette (locked Oct 15, 2026, shared with Carpool HQ)
Hex is the standard for screens. For print, convert with the Pantone Connect app, never from memory.

| Use | Hex | Notes |
|---|---|---|
| Celtic Green | #00843D | Pantone 348 C. Crest, text on cream, the cabinet trim, the right-answer edge |
| Irish Green | #45BE76 | Pantone 15-6340 TCX. Surfaces: the right-answer button, earned rings, HQ's dark-mode green |
| Page | #F2EDE4 | Warm white: the cabinet body, theme-color, manifest |
| Card | #FBF8F3 | HQ cards |
| Ink | #1E2A3B | All dark text and sprite outlines |
| Dark page | #161B22 | HQ dark mode (the game doesn't follow dark mode yet) |
| Button cream | #F6F0E2 | Game keys |

Game-only effects, not brand colors: the CRT glow #5CF09A, and the wrong-answer red #FF5A5F. Don't add new greens.

## The game as built today (the arcade version, before the daily)
- Cabinet look: the phone is an arcade cabinet on HQ's warm white, with Celtic Green trim along the sides and under the black parts. Marquee sign up top reading TRIVIELA, a CRT screen in a black bezel (scanlines, glowing green pixel text), and a black control panel with push-buttons.
- No title screen: the game opens straight on category select, and the sign flickers on. (Tried and dropped: an attract-mode title, coin slots, a pinball start button. Morg found them janky.)
- Category select: ten named cream keys in two columns on the panel, in the order of the plan table below. Each key has a small pentagon at the right: an outline until beaten, then solid black like a ball patch. Categories without a deck yet show as dim, disabled keys. The CRT shows the board: six same-size pentagons, one in the middle with a simple lock and five around it, clockwise from the top, all dim green outlines. Beating a category sends a glowing white pentagon flying from its key into the next open slot. Like seams on a real ball, flat sides face each other: each outer pentagon turns a flat side to the center (slot k is turned 72k degrees), the center points down, and a flying pentagon turns into place as it lands. Rotation lives on the polygon (an SVG transform), so CSS animations on the shape can't undo it. Five filled slots wake the boss: the lock goes, the center fills white and bobs, and tapping the screen opens the boss. No per-category colors: it's a soccer ball, so black and white only (Morg's call). All pentagons are vector shapes from `pent()` (filled, or `pent(true)` for an outline), never pixel sprites: a pixel grid can't hold a pentagon's 36° and 72° edges, and percentage-sized sprites land on fractional device pixels. Pixel sprites must render at whole-number device pixels. The five icons (phone, cassette, ball, bracelet, trophy) still show in the play HUD.
- Play: one sentence with a blinking dashed blank and three cream buttons. Right = green with a pixel ✓. Wrong = red with a pixel ✕ and a shake, and the other choice dims. After answering, the blank fills in with the right answer: glowing green on a win, plain white with a dashed underline on a miss. Meanings show only on the buttons (the right answer's, plus your own wrong pick's) and wrap to two lines at most. The untouched choice stays unexplained.
- 5 right in a row beats a level. One miss ends that run (retry with the replay icon). Beaten levels stay beaten on the device (localStorage `bsb-cleared`). Five beaten categories fill the slots and wake the final boss, whose game is TBD. Each level walks a saved shuffled order (`bsb-q-<id>`) so replays bring new cards. The right answer never lands in the same slot 3 times running.
- Fonts: Press Start 2P (marquee, title, numbers) and Pixelify Sans (everything else). Pixelify draws 5 like an S, so the code sets every digit in Press Start 2P. Its "fi" ligature looks like an A, so ligatures are off. Keep both fixes.
- Less is more: no instructions, labels or congrats text. Icons, color and layout carry it.

## Direction (Oct 16, 2026)
**The lane:** soccer trivia for the whole soccer family: the men's and the women's game, players and parents, US and global. Fun as trivia and fun as learning. Most soccer daily games are guess-the-player puzzles for hardcore fans of men's European football. Triviela teaches (every card has a "means" line), covers rules, lingo, history and every league, and starts from the elementary basics.
- **Soccer first.** Be stingy with non-soccer categories. Kid Slang is the model of a good one (its sentences are still all about soccer).
- **Learning:** it should teach real things: the offside rule, formations, field markings, ref signals, and the basics (how many players, what a throw-in is, positions).

## The daily game (decided Oct 16, 2026)
- **One run a day.** Everyone gets the same board that day.
- **The board:** 36 cards in a 6 × 6 grid, all shown at the start. Six categories across the top (they change daily, drawn from the pool), six cards down each column from easy at the top to hard at the bottom. The player picks any card, in any order: choose your own adventure.
- **Chips and the ball:** each right answer clicks a pentagon chip into the ball plaque (the six-pentagon board: center plus five). 6 chips complete the ball, which is a **goal**. The plaque clears and the next ball starts.
- **One miss ends the day.** Goals are banked, so a miss never takes one away.
- **Results:** 0 goals is **Nil**, 1 **Goal**, 2 **Brace**, 3 **Hat trick**. 18 right is the hat trick and the perfect day, the most there is. You only need 18 of the 36, so the hardest cards are there for the devoted.
- **Why 6 per goal, not 12:** with three buttons and one miss ending the run, a fan who's right 85% of the time makes 6 in a row about 38% of the time but 12 in a row only about 14%. At 12, most days would be Nil.
- **The share text** is the heart of it (texting results is what made Wordle). Base form, Morg's pick:
  ```
  Triviela #42
  ⚽⚽ Brace
  triviela.net
  ```
- **Design compass:** think Zach Gage. Simple rules, real stakes, a clean ending, a perfect day that's possible. No jokers, no second chances, no endless mode. Less is more.

## Open questions (Oct 16, 2026)
- **Share text detail:** whether to add a 6 × 6 grid of the run (⚫ right, 🟥 the miss, ⚪ untouched), so friends see each other's path. Morg prefers less.
- **Layout:** where the ball plaque and the 6 × 6 board sit (screen vs panel), and whether difficulty shows on the board (proposed: yes).
- **Picture cards (proposed, not approved):** the CRT becomes a glowing chalkboard pitch drawn in vector lines. Offside (Onside / Offside / Not involved), name the formation, name the field marking or restart, ref signals, goal or no goal. Same three buttons. Each card is a few lines of data (dots, arrows, lines), so they scale. Sourcing: IFAB Laws of the Game for rules and the field, and one coaching authority for formations (US Soccer Learning Center proposed). A prototype of one offside, one formation and one field card was offered.
- **A basics category** (working name Soccer 101, Morg's earlier name): all easy, for new families and young players.
- **The category pool:** which soccer categories, and the few non-soccer ones beyond Kid Slang.
- **Content pace:** Morg approves every card, so his review pace sets the pace of the game. The review page is https://claude.ai/artifact/M7WgEfdhNp6sMGGCNLrW7V (decisions saved per card in collections `r_<deck id>`, readable with ArtifactData). Built by `tools/review.py` from `tools/review.html`.
- **triviela.net:** add the domain in Cloudflare, then switch Squarespace to Cloudflare's nameservers (a new domain can't transfer registrars for 60 days). Moving off fernforager.github.io resets saved progress, which is fine before launch.

## Where things are (Oct 16, 2026)
- `main` (live): batch 1 (fill-in answers, offline, link preview, palette work in progress).
- `ball` branch (preview https://ball.blank-space-baby.pages.dev, not merged): the six-pentagon board, ten named keys, the locked palette, the name Triviela.
- `soccer-decks` branch (built on `ball`): 17 new soccer decks, 1,115 cards from official sources only, awaiting Morg's review. Not wired into the game yet.

## The old plan (Oct 15, 2026, superseded by the daily game above)
Ten categories, named on screen. The test for each one: who has the edge? Kids and parents play the same game, and each side owns some categories.

| Category | Edge | Deck |
|---|---|---|
| Kid Slang | kids | built (was Gen Alpha) |
| Parent Slang | parents | built (was Parents) |
| Grandparent Slang | nobody | new |
| Taylor Swift | kids, moms | built (was Swifties) |
| Old Tech | parents | new |
| 7th Grade | kids | new |
| Soccer Lingo | the team | built (was Soccer Fanatics) |
| World Cup 2026 | everyone | new |
| Seattle | everyone | new |
| EPL | soccer dads | built (was Premier League) |

- The meta-game: 5 right in a row in a category earns that category's pentagon, which flies into a slot around the boss pentagon. Any five wake the final boss. With 10 categories you can fail five and still get there.
- Cards will get harder from 1 to 5 within a run (a difficulty tag of 1–3 per card). Gradual is fine.
- Build order: the board, pentagons and names with the five built decks first. Then add new decks one at a time, each approved by Morg before the next.
- Still open: whether a failed category goes dark for the rest of a game (it only matters once there are six or more decks), and the boss game itself.

## House style for all text (strict)
- One plain sentence per card, deadpan school-workbook tone. The answer supplies the fun.
- No period at the end (!, ?, ?! and … are fine). **Never semicolons, anywhere.** Use commas, colons, em dashes (closed up: word—word) or periods.
- Curly quotes and apostrophes only. Scores and ranges use an en dash (6–0, 2025–26). American spelling.
- Punctuation never wraps away from the word or blank it touches. Hyphenated words and ranges never break across lines (the code handles both).
- Slang decks (Gen Alpha, Parents, Soccer Fanatics): every sentence is about soccer. No proper names, real or made up. Use roles (the coach, the ref, the keeper, the striker, the captain) and Mom, Dad, Grandpa, Grandma.
- Trivia decks (Swifties, Premier League): plain factual sentences, real names allowed.
- Clubs and national teams take British plural verbs ("Arsenal are", "Aston Villa have"), Morg's call on Oct 16, 2026.
- Kid-safe: anything borderline (sexual, drugs, alcohol, slurs, mean-spirited, private-life gossip) is out. When unsure, cut it.
- No song lyrics or quoted lines from songs, books or films, not even fragments.

## Sources per deck
- Gen Alpha: Merriam-Webster first, Dictionary.com Slang (2023+ entries) as the advance guard. M-W's sense wins. No older slang. Meanings are our own short wording.
- Parents (slang of parents aged ~40–50, teens around 1989–2004, mostly '90s): M-W first, Green's Dictionary of Slang second, words picked by when they peaked.
- Soccer Fanatics: M-W (soccer sense) first, Dictionary.com (including its Collins British entries) second. Terms in neither are out (e.g. worldie, golazo, top bins, park the bus, brace).
- Swifties: official sources first (taylorswift.com, the Recording Academy, RIAA, Billboard), Wikipedia second. No personal life.
- Premier League: premierleague.com first. Items with `"current": true` (champion, promoted clubs, managers) are as of Oct 14, 2026 and need checking every season.
- Soccer trivia decks (Oct 16, 2026): as few official sources as possible, one per category, no Wikipedia or news sites, not even as a backup. MLS mlssoccer.com, NWSL nwslsoccer.com, La Liga laliga.com, Bundesliga bundesliga.com, Serie A legaseriea.it, Ligue 1 ligue1.com, Liga MX ligamx.net, EPL premierleague.com, Champions League uefa.com, World Cup 2026 and Legends and Awards fifa.com (Awards may add ballondor.com), international men's and women's fifa.com plus uefa.com and ussoccer.com, Soccer Rules theifab.com, Club Nicknames the league sites above, Soccer Lingo Merriam-Webster and Dictionary.com. If the official site doesn't support a fact, the card is out.
- Research anything that could have changed. Don't trust memory for current facts.

## Open
- Final boss game: TBD (Morg decides).
- Morg may rename or redraw any icon. The Soccer Lingo HUD icon (a ball) is the weakest. A jersey was offered.
