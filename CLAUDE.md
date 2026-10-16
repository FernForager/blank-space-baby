# Triviela — brief for every session

Read this first. It holds the decisions already made so nobody re-learns them. Then read DOSSIER.md for where things stand, what’s been tried and what’s next.

## What it is
**Triviela** (trivia + trivela, the outside-of-the-foot curling kick, Morg's coinage on Oct 15, 2026. One L. Portuguese spells the kick "trivela" and has no "triviela" variant, so the extra i is ours and deliberate) is a public, standalone soccer trivia game: a daily puzzle in an arcade-cabinet look. It began as a word game for Morg's daughter's youth team (Seattle Celtic G14) and grew into its own thing on Oct 16, 2026. It's a standalone game first. Morg may still embed it in Carpool HQ's Arcade later, for fun. Built by Morg (owner, names everything, approves all player-facing text) with Claude. Domain: triviela.net (bought on Squarespace, not yet pointed at Cloudflare Pages). Today it still lives at https://fernforager.github.io/blank-space-baby/. The repo, that address and the saved-progress keys (`bsb-…`) keep the old name Blank Space Baby on purpose.

## Working with Morg
- He's an English major and veteran editor/localizer, new to coding, learning by building. Explain in plain language. Suggest better workflows when you see them.
- He works almost entirely from the Claude iOS app on an iPhone 17. Give steps that work on the phone, and say up front when something needs a computer or the web.
- He names everything and approves all player-facing text (titles, labels, prompts, reactions). Anything you write for players is a placeholder until he signs off.
- `main` is the live site. **Never push to `main` without Morg's OK.** Work on a branch, show him, then merge when he says so.
- He wants directness, honest pushback, short answers when short is right, and small fixes done now rather than later.
- Quality first, efficiency second (Morg, Oct 16, 2026). Don't cut corners to save tokens, but don't waste them either.
- No semicolons in anything you write for him: replies, docs, code comments, commit messages. He prefers em dashes, colons, commas or periods.

## How to build and check
```
python3 build/build.py               # checks every card, writes docs/index.html
python3 tools/screens.py             # every daily screen, both board layouts, three phone sizes, into out/
python3 tools/sweep.py 30 320 568 grid   # plays every card of 30 days, flags overflow and scrolling
python3 tools/drawcheck.py           # a year of draws: guardrails, repeat spacing, same boards on every load
python3 tools/lifecycle.py           # saving, resuming, locking, the share text, midnight
```
- `build/template.html`: the whole game (HTML, CSS, JS in one file). `__DECKS__` is replaced with the decks, `__START__` with the date of puzzle #1.
- `build/head.html`: the page head (Home Screen meta, icons, manifest).
- `build/decks/*.json`: one deck per category. `SPEC.md` there is the deck-writing spec (hooks and difficulty included). Read it before editing a deck.
- `docs/`: what GitHub Pages serves (index.html, icons, manifest, `sw.js` for offline play, `og.png` for link previews). Don't hand-edit docs/index.html. Rebuild it. Rerun `python3 tools/og.py` if the look or the icons change.
- Preview links: Cloudflare Pages (project blank-space-baby, output `docs`, no build command) deploys every pushed branch to `https://<branch>.blank-space-baby.pages.dev` within a minute or two. Give Morg that link with every branch so he can play it on his phone before merging. `main` also deploys to https://blank-space-baby.pages.dev, but GitHub Pages stays the official link.
- Cloud sessions run `.claude/hooks/session-start.sh` at startup: it installs Playwright for Python (1.56.0, matching the preinstalled Chromium) and the game's two fonts, so screenshots are right from the first minute.
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

Game-only effects, not brand colors: the CRT glow #5CF09A, the wrong-answer red #FF5A5F, and on the `daily` branch the card colors, yellow card #F7C948 and red card #D52B1E. Don't add new greens.

## The game as built today (the arcade version, before the daily)
This is `main`. The `daily` branch replaces it (see "The daily as built" below).
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

## The daily game (decided Oct 16, 2026, corrected the same day)
- **One run a day.** Everyone gets the same 18 cards that day.
- **The hopper:** every card is tagged easy, medium or hard. Each day draws **6 easy, 6 medium and 6 hard** at random from all categories, so odd neighbors sit side by side (Build Out next to Rangers FC next to Rabona). No hand-curated boards, and no brutal tier: hard means a real fan knows it, not obscure trivia.
- **The board:** all 18 cards are laid out at the start, and the player taps any of them, in any order: choose your own adventure. Each tile shows a **hook**, a word or name from the card's sentence that is never the answer (e.g. "Rangers FC"). **Difficulty is shown as card colors:** easy tiles are white, medium are a yellow card, hard are a red card (Morg's idea, Oct 16, 2026). Showing it makes the choice a visible gamble and stops anyone being knocked out on their first tap by luck. White, yellow and red also differ in brightness, so colorblind players can tell them apart. Watch that the red tile doesn't get confused with the red wrong-answer feedback.
- **Chips and goals:** every right answer adds a pentagon chip to the player's ball, wherever on the board it came from. **Every 6 chips is a goal.** Choice is real: grab safe-looking tiles to bank a goal, or take the scary ones while fresh.
- **One miss ends the day.** Goals are banked, so a miss never takes one away.
- **Results:** 0 goals is **Nil**, 1 **Goal**, 2 **Brace**, 3 **Hat trick**. Clearing all 18 is the hat trick and the perfect day.
- **Why 6 per goal:** with three buttons and one miss ending the run, a fan right 85% of the time makes 6 in a row about 38% of the time but 12 only about 14%.
- **Proposed board shape (not yet approved):** a round honeycomb of 19 hexagons (center, a ring of 6, a ring of 12), the shape of a ball. The 18 outer hexagons are the cards, and the center shows the player's ball filling with pentagon chips. On a real ball the white panels are hexagons and the black ones pentagons, so each shape does one job.
- **The share text** is the heart of it. Morg's pick, with the count of right answers (locked Oct 16, 2026):
  ```
  Triviela #42
  ⚽⚽ Brace · 17
  triviela.net
  ```
  A day with no goal reads `Nil · 4`. No grid or path row: less is more.
- **Colors shown at launch** (locked). Hidden-until-answered can be tried with a few serious fans in the playtest.
- **Reset at local midnight,** like Wordle. Each date has one puzzle number, and everyone who plays #42 gets the same board.
- **Repeats:** a card can come back, but never within 3 months. (At 18 a day, never repeating in a year would need about 6,500 cards.)
- **Design compass:** think Zach Gage. Simple rules, real stakes, a clean ending, a perfect day that's possible. No jokers, no second chances, no endless mode. Less is more.
- **A misunderstanding to avoid:** on Oct 16 Claude wrongly turned this into three balls of 6 tiles shown one after another, which made tile choice meaningless. It is one board of all 18. The 18-player panel (`research/player-panel-2026-10-16.md`) reviewed the wrong version, so ignore its point that choice doesn't matter. Its other advice still holds. Round two, on the correct design, is `research/player-panel-2026-10-16-round2.md`. Its pre-launch roadmap: build the daily plainly, save mid-run and lock the finished day, the end screen and share, a readability test on real phones with real people (it decides honeycomb vs a simpler board), a content pass (truly easy whites as basics, hard means deep not obscure, three believable choices, draw guardrails: at least one women's card and one rules card a day, at most 2–3 from one league, Kid Slang at most once and never red), then a week with the G14 team and parents before triviela.net. After launch: reveal all cards once your day ends, the anonymous difficulty counter, clear-cut offside picture cards.

## The daily as built (`daily` branch, Oct 16, 2026, not merged)
It replaces the arcade game: no category keys, no boss. The cabinet, palette, fonts, sentence rendering and answer buttons are unchanged.
- **The pool:** `DAILY` in `build/build.py`: every soccer deck plus Kid Slang and Parent Slang (Morg, Oct 16, 2026). Taylor Swift stays out. Every card has a `hook` and a `d`, written by one agent and checked by a second against the rules in `build/decks/SPEC.md`, with one bar for every deck: white means a 10-year-old player and a brand-new soccer parent would both get it (Morg, Oct 16, 2026). The build refuses a card without them. A card about the women’s game outside the NWSL and International Women’s decks says `"women": true`.
- **The draw:** seeded by the local date, so every phone deals the same board. Each color keeps a line of its cards, oldest first. A day deals from a shuffle of the 24 oldest in each line, and dealt cards go to the back, so a card comes back as late as the deck allows. The page replays every day from #1 to rebuild the lines (about 30 ms for a year). Guardrails: at least one women’s game card and one Soccer Rules card, at most 3 cards from one league (both EPL decks count as EPL, Club Nicknames go by their source site, the Champions League counts as one league), at most one card from each slang deck and never a red one, and no two cards that give each other away (one’s answer in the other’s sentence or hook, or a shared answer or hook). The two wrong answers are seeded too, so everyone sees the same three choices.
- **Repeats:** the 3-month rule needs about 570 cards in each color. Until then cards come back as late as the deck allows, about every 6 weeks for whites today (276 white, 805 yellow, 292 red). `python3 build/build.py` prints the current numbers.
- **Puzzle numbering:** `START` in `build/build.py` is the date of #1. It’s a placeholder (Oct 16, 2026) until Morg picks.
- **Play:** tap any tile. A tapped tile is committed (Morg, Oct 16, 2026): no way back, and a reload reopens the same card. The right answer still never takes the same slot 3 times running. A right answer’s chip flies into the ball, the five around clockwise from the top and then the center. The sixth is a goal: the ball flashes, a goal lamp lights and the ball empties. One miss ends the day.
- **Saved on the phone:** `bsb-daily` holds today’s board (the cards themselves, so a deck change mid-day can’t alter a started board), each tile’s result, the open card, the tap order and the last two answer slots. It saves on every tap. A finished day reopens to its end screen. A finished or untouched day rolls over at local midnight. A day in progress stays until it’s finished or the page reloads.
- **End screen:** the goal lamps, the result word with the count (Brace · 17) and the card that got you: its sentence with the answer filled in, then its means line. The panel has one share key showing the exact text it sends (the share sheet on a phone, the clipboard on a computer) and the countdown to local midnight.
- **Board layouts (open, Morg picks):** `?board=hex` is the honeycomb on the screen (flat-top hexes, whites in the inner ring, yellow and red cards alternating outside) with the goal lamps on the panel. `?board=grid` is the ball and lamps on the screen with 18 keys on the panel, one card color per column. Hex is the default until Morg picks. Hooks shrink to fit their tile on two lines.
- **Preview-only switches:** on `*.blank-space-baby.pages.dev`, `?day=N` shows puzzle N and `?reset` clears today’s saved run. They never work on the real site.

## Open questions (Oct 16, 2026)
- **Layout:** where the board and the ball sit (screen vs panel). Built both ways on the `daily` branch for Morg to compare: the honeycomb on the screen, or the ball on the screen with the tiles as keys on the panel.
- **Picture cards (proposed, not approved):** the CRT becomes a glowing chalkboard pitch drawn in vector lines. Offside (Onside / Offside / Not involved), name the formation, name the field marking or restart, ref signals, goal or no goal. Same three buttons. Each card is a few lines of data (dots, arrows, lines), so they scale. Sourcing: IFAB Laws of the Game for rules and the field, and one coaching authority for formations (US Soccer Learning Center proposed). A prototype of one offside, one formation and one field card was offered.
- **A basics category** (working name Soccer 101, Morg's earlier name): all easy, for new families and young players.
- **The category pool:** which soccer categories, and the few non-soccer ones beyond Kid Slang.
- **Content pace:** Morg approves every card, so his review pace sets the pace of the game. The review page is https://claude.ai/artifact/M7WgEfdhNp6sMGGCNLrW7V (decisions saved per card in collections `r_<deck id>`, readable with ArtifactData). Built by `tools/review.py` from `tools/review.html`.
- **triviela.net:** add the domain in Cloudflare, then switch Squarespace to Cloudflare's nameservers (a new domain can't transfer registrars for 60 days). Moving off fernforager.github.io resets saved progress, which is fine before launch.

## Where things are (Oct 16, 2026)
- `main` (live): the arcade version, with the six-pentagon board, ten named keys, the locked palette and the name Triviela, plus the 17 soccer decks (1,115 cards from official sources only, still in Morg’s review, not in the arcade game).
- `daily` branch (preview https://daily.blank-space-baby.pages.dev, not merged): the daily game, both board layouts, hooks and difficulty on every card.

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
