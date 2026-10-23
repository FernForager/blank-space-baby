# Everything built since milestone 1 (Oct 19 to Oct 22, 2026)

Milestone 1 is the version live on triviela.net since Oct 19, 2026: the shootout, layout A, the 7-board demo, hooks on cream tiles in three columns. On Oct 22, 2026 Morg played the newer beta, missed the hooks and the earlier look, and asked to go back to milestone 1, keep everything else and choose what to bring back. Nothing was deleted.

Where it all lives:
- `milestone-1`: the live version, bookmarked (https://milestone-1.blank-space-baby.pages.dev).
- `beta-oct22`: the beta exactly as it was, with everything below (https://beta-oct22.blank-space-baby.pages.dev). Each item is in its commits there, listed in order below.
- `mock-53` and `mock-tags`: the two mockups, with their switches (`?look=b`, `?hooks=1`, `?look=icons`).
- `daily`: the beta, back to milestone 1 on Oct 22, 2026. The font files, `functions/api/result.js`, `tools/docsroute.py` and `tools/results.py` stay in it, unused until their items come back.

## Look
1. **The 3D ball** (`9c8e7ee`): a true soccer ball pressed onto a sphere, curved seams, a soft rim glow, like a hologram. Replaces the flat drawing.
2. **The slogan on the cabinet** (`4cd00c6`): “How well do you know the beautiful game?” in ink between the screen and the cards.
3. **The sign’s subheading** (`0ee5dbd`, `54b877a`): “Soccer trivia shootout” in small solid letters under TRIVIELA.
4. **Sharp text, stage 1** (`fa6fda2`): arcade letters at crisp sizes and real weight (no smeared fake bold), two-line hooks and meanings split evenly, hooks clear of the corner card, the menu key reads Start over, the sign’s dots on whole pixels. Mostly fixes.
5. **Our own fonts** (`d7e133d` to `d1f09af`, `0339ba9`): the main font redrawn on its pixel grid with a little extra weight (“+2”), the j with a dot, stored with the game (no Google, works offline). Goes with item 6.
6. **Digits matched to the text** (`4d79b4e`): numbers as tall as the capitals and on the line. Fixes a “#3” sitting high, which item 4 caused.

## Play
7. **Attract mode** (`ac16aa7`, `6285a64`, `c4d5ce5`): until the first tap of each new board, a wave of light runs across the tiles and the screen blinks PICK A CARD with an arrow. Made after Morg’s kids froze on the first screen.
8. **The 5×3 board** (`17c7f18`): 5 across, 3 down, a row per color, every card face down (a referee’s card in its slot, no hook) until played. The hooks moved to the Share board image. This is the one Morg missed the hooks on.
9. **Category tags** (`952ed84`): a short word under each card naming its category (EPL, Rules, 101 …). Made for the face-down board. On the hooked board it would crowd the tile.
10. **Streaks** (`952ed84`): right answers in a row shout Brace! at 2, Hat Trick! at 3, then “4 in a row!”. The best run shows on the end screen and in the share (`12/15 · Hat Trick!`). Works on any board.

## Share
11. **A miss as its own card** (`17c7f18`): ⬜ 🟨 🟥 instead of ❌ (🔴 was tried in between, `0a1cf99`). Works on any board.
12. **Fixed spots** (`17c7f18`): the share and the play screen’s scoreboard keep every card in its board spot, so the same spot is the same card for everyone, instead of the order played. Works on any board.
13. **Share board** (`17c7f18`, `952ed84`): a second key on the end screen sends a picture of the finished board, every card with its hook and ⚽ or its card. Works on any board.

## The playtest
14. **One board a day with anonymous results** (`998945b`): the 7-board demo off, a real daily with a countdown, and each finished board sends its score and cards (no names) so we learn which cards are too hard. Needed before testers get the link.
