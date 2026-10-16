# Dossier: Triviela (formerly Blank Space Baby)

> **Oct 16, 2026:** much of this dossier describes the old Blank Space Baby arcade game. The game is now Triviela, a public daily soccer trivia game. CLAUDE.md ("Direction", "The daily game", "Open questions", "Where things are") is the current source of truth. Where they disagree, CLAUDE.md wins. Sections 7 and 8 here (roadmap ideas and things tried and dropped) are still useful history.

Handoff for Claude Code sessions, written Oct 14, 2026 at the end of the session that built the game. Read `CLAUDE.md` first: it has the standing rules (house style, sources, look, game rules). This file covers where things stand, what's been tried, what's next and how to work.

This repo is **public**. Never commit personal details: no last names, addresses, phone numbers, family names or photos.

---

## 1. Where things stand

- **Live:** https://fernforager.github.io/blank-space-baby/ (GitHub Pages, `main` branch, `/docs` folder). Morg has it on his Home Screen as **BSB**.
- **Built:** title screen → level select → play → level beaten → final boss (locked until all five are beaten, its game is TBD).
- **Decks (318 cards):**

  | Level | Cards | What it is |
  |---|---|---|
  | Gen Alpha | 112 | Current kid slang |
  | Parents | 51 | '90s slang |
  | Soccer Fanatics | 55 | Soccer terms |
  | Swifties | 50 | Taylor Swift facts |
  | Premier League | 50 | League facts, 8 of them current-season |

- **Checked:** every screen fits without scrolling at 402×744, 375×667 and 320×568. A play sweep of every level is clean. The build refuses cards that break house style.
- **Morg's verdict on v36:** "decent, long way to go." The next work is polish, not features.

## 2. How to work with Morg

`CLAUDE.md` has the essentials. The ones that matter most day to day:

- **Start from what he can see.** He judges on his phone, so show screenshots and say what changed in a sentence or two. Don't recap the steps.
- **He gives short, iterative feedback** ("too busy," "flip it," "nope," "I liked it before"). Take it literally and move fast. When he says revert, revert all the way, then improve from there.
- **He names everything and writes or approves every word players see.** Placeholders are fine while building, but flag them as his to replace.
- **He hates clutter and static text.** No instructions, labels, "Great job!" or tutorials. Balance and spacing matter as much as features.
- **Pixel-perfect matters.** Before saying something is done, zoom into screenshots: punctuation against the blank, line breaks, icon pixels, glyph shapes.
- **Push back honestly.** He'd rather hear "that won't work because…" than get agreement.
- **He works from an iPhone in the Claude app, with no computer.** Anything he has to do himself should be iPhone steps (Safari or the GitHub app). Say up front if something truly needs a computer.

## 3. The workflow

1. **Branch per task.** `main` is live. Never push to `main` without Morg's OK.
2. **Build and test** before showing anything:
   ```
   python3 build/build.py            # style check + writes docs/index.html
   python3 tools/screens.py          # every screen at 3 phone sizes → out/
   python3 tools/sweep.py 60         # plays 60 cards per level, flags problems
   python3 tools/sweep.py 30 320 568 # same on the smallest phone
   ```
   Then look at the screenshots yourself and zoom in on details.
3. **Open a pull request.** Morg taps **Merge** in the GitHub app or Safari. That merge is his OK to go live.
4. **Preview links.** Cloudflare Pages deploys every pushed branch to `https://<branch>.blank-space-baby.pages.dev`. Put that link in the pull request and in your reply so Morg can play it before merging.

## 4. How the code works

- **One file:** all of `build/template.html` (HTML, CSS and JS) ends up in `docs/index.html`. No frameworks, no build tools beyond `build/build.py`.
- **Views:** `#cab[data-v]` is `title`, `select`, `play`, `clear` or `boss`. CSS shows the matching screen view (`#v-*`) and panel view (`#p-*`). The whole CRT screen (`#flip`) is the "continue" tap target. `#home` returns to level select.
- **Panel height:** title, select and boss share one short panel (`--deck-h`) so the screen gets the room. Play uses the natural, taller panel.
- **Sprites:** `SPR` holds pixel art as arrays of row strings. `#` is a single-color pixel. Letters are palette colors (`PAL`: K ink, W white, Y gold, O orange, R red, B blue, P purple, G green, k pink, D dark). `svg(name, scale, cls, color)` draws them. `color=true` paints the palette (level buttons). Without it you get the one-color CRT version: ink outline only, or every pixel if the sprite has no ink.
- **Cards:** each card has `w` (answer), `means` (short meaning), `ex` (the sentence) and `k` (kind). The two wrong choices come from the same `k`. `groups` lists answers that could fill each other's blanks, and two answers from one group never share a card. If a kind runs short, it falls back to any kind in the level.
- **Sentence rendering, in order:** escape → swap the answer for a blank, glued to its punctuation so they never split (`glue`) → keep hyphenated words and ranges unbroken (`keep()`) → set digits in Press Start 2P (`num()`).
- **Saved on the phone:** `bsb-cleared` holds the beaten levels. `bsb-q-<level>` holds that level's shuffled order and position, so replays deal new cards. All access is wrapped in try/catch.
- **Answer slots:** shuffled, but never the same slot three times running (`lastSlots`).

## 5. First session: do these first

1. **Cloudflare Pages preview links.** Done Oct 15, 2026. See §3, step 4.
2. **Ask Morg what bugs him most** after playing v36 on the real link, then do a polish pass on that. Known soft spots:
   - **Soccer ball icon:** reads as "ball-ish." Try a bigger grid or a different symbol (whistle, cleat), shown side by side.
   - **Boss sprite:** placeholder art.
   - **Answer screen after a pick:** a lot of empty screen sits above the word on tall phones.
   - **Pixelify Sans's uppercase B:** it can read like a G, which is a font quirk. If Morg notices, consider a different body font. Get his OK first. The font is part of a look he approved.
   - **CRT icons:** the HUD's one-color icons are tiny (scale 2). Check they read.
3. **Link preview for texting:** done (`docs/og.png` from `tools/og.py`, plus `og:title`). Add an `og:description` only if Morg writes a tagline.

## 6. Open questions for Morg (don't decide for him)

- **The final boss game.** Ideas to offer, not choose: a speed round (blanks from all five decks against a timer), a mixed deck with "lives" instead of one miss, or a boss that "talks" in nonsense slang you have to decode. Nothing in the code yet beyond the locked sprite.
- **Miss rule:** right now a miss ends only that level's run. The all-or-nothing version (a miss resets everything) was offered and is still open.
- **Swap or redraw any icon.** All five are placeholders he's OK'd for now.
- **Deck items flagged for his review:**
  - Parents: *homie*, *posse* and *home skillet* (Green's notes gang or racial history).
  - Premier League: British plural verbs for clubs ("Arsenal **are**").
  - Soccer Fanatics: "keepy-uppy," Dictionary.com's spelling.

## 7. Long-term roadmap

- **Fold into Carpool HQ.** HQ (repo FernForager/carpool-hq, a family carpool app with an Arcade tab planned for 5 games) gets a copy of `docs/index.html` in its Arcade when Morg says so. Both sites live on fernforager.github.io, so saved progress carries over. HQ has its own `builder/` and a plan doc. Ask Morg before touching that repo.
- **Keep decks fresh:**
  - Gen Alpha slang moves fast. Every month or two, check M-W's Slang & Trending pages and Dictionary.com's slang entries for new words, and propose additions and retirements to Morg.
  - Premier League cards marked `"current": true` need checking each summer (champion, promoted clubs, managers) and when managers change.
  - Swifties needs updating after new releases or records.
- **New levels:** same pipeline. Write a deck to `build/decks/SPEC.md`, add it to `LEVELS` in `build/build.py`, draw an icon in `SPR`, give it a `PAL`-colored version, and test at all sizes. With 6+ levels, the row of round buttons needs a new layout, so plan that with Morg first.
- **Sound** (8-bit blips on right, wrong, level beaten): must start muted or be very quiet, and Morg decides. Note that iOS won't vibrate from a web page.
- **Sharing a result** (a text-able line like "BSB ■■■■■"): only if Morg wants it, and he writes the format.
- **Gear:** no computer needed so far. If the work turns to fine-grained game feel (touch timing, animation curves), a laptop with a real browser for quick tries would start paying off. Recommend it only then.

## 8. Things tried and dropped (don't re-propose)

- **Names:** Decode It (an early working title), Wait Actually, Slango, Slangle, Slang Wrangler, Slanguage Arts. Morg named it **Blank Space Baby**, then renamed it **Triviela** on Oct 15, 2026 (trivia + trivela): the Taylor Swift pun leaned too hard on one category out of ten. Also tried and passed over: Triviella (the sea snail genus, two L's) and Triviidae (its family, hard to say), plus Ball Knowledge, Five-a-Side, Mind the Gap, Nutmeg, Fill the Gap, Patchwork, Pass It On and Blank Check.
- **Look:**
  - A full Apple-style redesign. Morg's reaction: "I liked it before."
  - A gold star on wins.
  - Vertical stripes, hoops, dots and a mesh-shorts texture behind the cards (flat club green won).
  - A pixel-clover Home Screen icon (for HQ).
  - A "?" bubble that looked like help.
- **Layout:** two-sentence cards, end periods, made-up names, older but still-used slang (in Gen Alpha), song lyrics or Shakespeare as prompts, and a 3D card flip (replaced by the CRT flicker).
- **Words cut from Gen Alpha by Morg:** gucci, cheugy, extra, demure, gurting, jit, 41. Kept on purpose: yeet, lit.
- **Kid-safety cuts** are listed in each deck's `cut` list. Don't bring them back.

## 9. Gotchas

- **Playwright in the sandbox:** the Python package may be missing. Install the version that matches the preinstalled Chromium (`pip install playwright==1.56.0` for chromium-1194). Never run `playwright install`.
- **Offline:** `docs/sw.js` serves the page network-first (3-second fallback to the saved copy) and everything else cache-first. Bump `CACHE` in it if a cached file other than the page ever needs replacing. When the game folds into HQ, check `sw.js` against HQ's own setup.
- **Fonts in the sandbox:** Google Fonts may be blocked, so screenshots fall back to system fonts and look wrong. Install Press Start 2P and Pixelify Sans into `~/.fonts` from github.com/google/fonts before trusting screenshots.
- **Two font fixes to keep:** Pixelify Sans draws 5 like an S and its "fi" ligature like an A, so keep digits in Press Start 2P and ligatures off. Check any new font for both problems.
- **The Claude app's artifact viewer** adds its own title bar. That's not the game repeating its title. The real site has no such bar.
- **Safe areas:** `.cab` pads by `env(safe-area-inset-*)` because the Home Screen version draws under the status bar. Test that the marquee clears the notch.
- **The style checker** in `build/build.py` blocks semicolons, straight quotes, end periods, two-sentence cards, a missing or doubled answer, and kinds with too few wrong answers. Extend it rather than working around it.
