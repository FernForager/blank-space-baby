# The nine cards for the fixed board (Oct 29, 2026)

Morg's plan, from the car on Oct 29: one card per category, nine categories, three green, three yellow, three red. The board plays as #1 every day while `ONE_BOARD` holds (`build/boards.json` pins "1").

**The nine categories (Morg's names):** Messi, CR7, MLS, NWSL, EPL, World Cup, Technique, Lingo (kid slang included) and Basics (was 101).

**What Morg wants:** facts that are either timeless classics or fresh, a week or two old, since current stats are an edge no printed quiz has. Fresh numbers go on as "as of" cards (for example, "Through October 2026, Messi had ___ MLS goals") and onto `build/vetting/WATCH.md`. Ask a birth year, never an age. Facts are facts, but we never copy anyone's wording or question lists: every card gets its own sentence in the house style, confirmed on its official source.

## What we already have (cards in the draw, all vetted, Oct 29)

| Category | Cards | Green | Yellow | Red | Where they live |
|---|---|---|---|---|---|
| Messi | 21 | 8 | 8 | 5 | laliga, mls, ucl, intl-men, wc26, legends, awards |
| CR7 | 8 | 4 | 4 | 0 | ucl, intl-men, wc26, awards, epl-more, laliga, seriea |
| MLS | 61 | 3 | 34 | 24 | mls |
| NWSL | 65 | 6 | 46 | 13 | nwsl |
| EPL | 104 | 2 | 81 | 21 | epl, epl-more |
| World Cup | 193 | 26 | 124 | 43 | wc26, plus every card that names the World Cup |
| Technique | 22 | 7 | 12 | 3 | the moves and skills, sorted by hand (list below) |
| Lingo | 276 | 184 | 92 | 0 | soccer, lingo-more, alpha, parents (slang never plays red) |
| Basics | 223 | 182 | 33 | 8 | basics, rules |

So the research is really about two things: Messi and CR7 (Morg's own question list, and fresh stats), and a fresh-this-month pass on MLS, NWSL, EPL and the World Cup. Technique, Lingo and Basics can come straight from the vetted pool.

**Technique, already vetted** (by hand from a keyword sweep):
- green: soccer:0 bicycle kick, soccer:2 volley, soccer:3 header, soccer:5 backheel, lingo-more:59 dribble, basics:96 bicycle and scissors kicks are legal unless dangerous, basics:73 a corner that curls straight in counts (the olímpico, without the word)
- yellow: soccer:1 scissors kick, soccer:7 nutmeg, soccer:8 stepover, soccer:10 chip, soccer:12 Panenka, lingo-more:3 inswinger, lingo-more:4 half volley, rules:63 feinting at a penalty, intl-men:29 Panenka's Euro 1976 penalty, intl-men:31 Gavi's trivela volley, ucl:21 Bale's overhead kick in the 2018 final, awards:70 Ovalle's scorpion kick
- red: awards:37 Oleksy's scissors kick, awards:39 Montiel's overhead kick, intl-men:27 van Basten's volley in the Euro 1988 final

**Morg's "tech" question:** neither of our Lingo dictionaries has it. Merriam-Webster's "tech" means technician or technology only, and "tekkers" (British slang for technique) is in neither Merriam-Webster nor Dictionary.com. So the category stays Technique, and "tekkers" can't be a Lingo card.

## Tags

A tile's category comes from its deck id (`TAG` in the template, strings `tag.*` in `build/text/en.json`). Messi, CR7 and Technique cards need their own decks (`messi.json`, `cr7.json`, `technique.json`, tags "Messi", "CR7", "Technique"), so a Messi card from the Awards deck would still say Awards. Basics is a rename of `tag.basics` ("101" today). "World Cup" for the wc26 deck ("WC26" today) and "Lingo" for the slang decks ("Slang" today) are Morg's words for this board, to confirm before building. Every name fits a tile: "Bundesliga", longer than all of them, already passes `tools/tilecheck.py` at 320 px.

A simpler way for cards that already exist: an optional `tag` on the card itself, which `tagOf()` would read before the deck's. It isn't part of a card's fingerprint, so a vetted card keeps its verdicts, and nothing moves between decks. New cards (most Messi and CR7 ones) can still live in their own decks.

## Files

- `messi.md`, `cr7.md`: the research, every fact with its official source and the date it was true.
- `mls-nwsl.md`: fresh MLS facts and NWSL leads, the start of the first worker's job.
- `epl-wc.md`: what the pool already has for EPL and the World Cup, and this week's Ballon d'Or leads.
- `draft-board.md`: a first draft of the nine, for Morg to react to.
- `BRIEF.md`: the brief for the workers who research the rest, three of them instead of nine.
