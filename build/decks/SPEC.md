# Blank Space Baby — deck spec (read fully before writing anything)

Blank Space Baby is a phone fill-in-the-blank game for a youth girls' soccer team (players ~12–14) and their parents. Each card shows ONE sentence with the answer blanked out, plus three buttons: the answer and two other answers from the same deck. After answering, the card shows the answer, its short "means" line, and the full sentence. A level is beaten by getting 5 right in a row.

## Output
Write a JSON file (path given in your task) shaped exactly like:
```
{"deck": "<name>", "primary": "<source name + URL>", "secondary": "<source name + URL>", "as_of": "2026-10-14",
 "items": [ {"w": "...", "means": "...", "ex": "...", "k": "...", "src": "https://..."} , ... ],
 "groups": [ ["a","b"], ... ],
 "cut": [ {"w": "...", "why": "..."} ] }
```
- `w`: the answer exactly as it appears on the button and in the sentence. Short (ideally ≤ 16 characters, hard max 20).
- `means`: the line shown after answering. Our own words, never copied. Sentence case, no end period, ideally ≤ 32 characters, hard max 40. For slang: a short definition. For trivia: a short extra fact or a crisp restatement that teaches something (e.g. "Her 2014 album, named for her birth year").
- `ex`: the sentence. Must contain `w` exactly once (case-insensitive, as a whole word/phrase, not inside another word). Must not contain any other wording that gives the answer away. ≤ 70 characters ideally, hard max 85.
- `k`: kind tag. The two wrong buttons are drawn ONLY from items with the same `k`. So within one `k`, every other item's `w` must be clearly WRONG in every sentence of that `k`. Every `k` needs at least 4 items (6+ is better). For slang decks use parts of speech or meaning families as needed. If one tag works, use "word".
- `src`: the URL of the page that supports this item (dictionary entry, official page, etc.).
- `groups`: lists of answers that could plausibly fill each other's blanks (synonyms, near-synonyms). Two answers in one group never appear on the same card. Be generous.
- `cut`: things you considered and dropped, with a few words on why (not in source, borderline, stale, ambiguous).
- `tag` (optional): the card’s own category on its tile when it isn’t its deck’s (Messi, CR7, Technique, World Cup): an id from `build/library/categories.json`, never a new name. A new category goes on that list first, named by Morg. Before handing cards in, `python3 tools/library.py check` holds them to the library’s spelling of every hook and answer.

## House style for `ex` (strict — the owner is an editor and cares)
- ONE plain sentence. Never two sentences.
- No period at the end. `!`, `?`, `?!` or `…` at the end are fine when natural, otherwise no end punctuation at all.
- NEVER semicolons, anywhere (also not in `means`). Use commas, colons or em dashes (—) instead.
- Curly quotes and apostrophes only: ’ “ ” (never ' or "). Scores use an en dash: 3–1.
- Deadpan school-workbook tone: plain, dry, simple. The answer supplies the fun.
- Kid-safe. Anything borderline (sexual, drugs/alcohol, violence, slurs, mean-spirited, gossip about private lives, rude) is OUT. When unsure, cut it and list it in `cut`.
- Spelling: American.
- Try to avoid the words soccer and football (Morg, Oct 26, 2026: the game stays global and never names the sport). Write “the game”, a role or the thing itself instead. Keep one only where the word is the fact (soccer mom, total football, footy).

## Morg’s style
- Read `build/decks/MORG-STYLE.md` before writing or rewording a card: his own edits, before and after, and the patterns they show (Oct 31, 2026). His wording is the model, and the editor holds new cards to it.
- Read `build/decks/VOICE.md` too (Oct 31, 2026): the house voice, with how the sentence shows its answer, what the meaning line teaches, honest difficulty and wrong answers in range.

## Accuracy
- Research with WebSearch/WebFetch. Do not go from memory for any fact that could have changed. Today is 2026-10-14.
- Every item must be supported by the primary source. Use the secondary only to fill gaps or confirm, and note in `src` which one you used.
- Never invent facts, quotes, or dates. If you can't verify, cut it.
- No song lyrics or quoted lines from songs, books or films — not even fragments.

## Hooks and difficulty (the daily, Oct 16, 2026)
Every card also needs these fields:
- `hook`: the word or name on the card’s tile on the daily board. It is the player’s only clue to what the card is about, so they can bet on what they know.
  - Copied from the sentence: one word or a few words in a row, spelled exactly as in `ex` (accents, curly apostrophes, hyphens). You may drop a possessive ’s (Arsenal’s → Arsenal), and lowercase the sentence’s first word if it isn’t a name.
  - Never the answer, never part of it and never containing it (answer Real Madrid: not Real, not Madrid, not Real Madrid’s).
  - Never a giveaway: someone who doesn’t know the fact can’t work out the answer from the hook alone (answer Gunners: not munitions).
  - Short: 12 characters at most, counting spaces, ideally 10 or fewer. One or two words. No “the,” “a” or “an” in front.
  - Readable out loud by a 10-year-old. When the sentence has a short familiar form, use it (Gladbach, not Mönchengladbach).
  - Names the topic: the most recognizable name in the sentence (a player, club, national team, city, award or competition), or for rules, lingo and slang cards the key soccer word or object (throw-in, keeper, crossbar, shin guard).
  - Specific beats general: a club or a player beats a league name (Haaland beats Bundesliga). The panel cut league labels on tiles, and a bare league name works like one. Use a league or competition name only when nothing more specific works.
  - No empty words (team, game, player, fans, season, year, record) unless nothing better exists.
  - Varied: don’t give many cards in one deck the same hook. Two tiles with the same hook on one board would confuse.
- `d`: difficulty, which sets the tile’s card color. One bar for every deck:
  - 1, easy (a green tile, white until Oct 28, 2026): a 10-year-old player and a brand-new soccer parent would both very likely get it right. True basics: rules every young player learns, field words, the most famous names anyone has heard of (Messi, the World Cup, Real Madrid). If you have to follow a league, a club or a national team to know it, it isn’t easy.
  - 2, medium (a yellow card): a regular fan, or a player who watches some games, likely gets it. A beginner might or might not.
  - 3, hard (a red card): a real fan knows it. Deep but gettable (Laws nuance, tactics, history across eras, the women’s game in depth, club lore), never obscure trivia.
  - Judge the card as it’s played: the answer shows up next to two wrong answers of the same kind (`k`) from the same deck.
  - Slang: easy means kids and parents both know it. Known mostly by one side of the family is medium.
- `women`: `true` on a card about the women’s game (a women’s player, team, coach, league or competition), in any deck except NWSL and International Women’s, where every card counts already.
