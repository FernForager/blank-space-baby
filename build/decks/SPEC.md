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

## House style for `ex` (strict — the owner is an editor and cares)
- ONE plain sentence. Never two sentences.
- No period at the end. `!`, `?`, `?!` or `…` at the end are fine when natural, otherwise no end punctuation at all.
- NEVER semicolons, anywhere (also not in `means`). Use commas, colons or em dashes (—) instead.
- Curly quotes and apostrophes only: ’ “ ” (never ' or "). Scores use an en dash: 3–1.
- Deadpan school-workbook tone: plain, dry, simple. The answer supplies the fun.
- Kid-safe. Anything borderline (sexual, drugs/alcohol, violence, slurs, mean-spirited, gossip about private lives, rude) is OUT. When unsure, cut it and list it in `cut`.
- Spelling: American.

## Accuracy
- Research with WebSearch/WebFetch. Do not go from memory for any fact that could have changed. Today is 2026-10-14.
- Every item must be supported by the primary source. Use the secondary only to fill gaps or confirm, and note in `src` which one you used.
- Never invent facts, quotes, or dates. If you can't verify, cut it.
- No song lyrics or quoted lines from songs, books or films — not even fragments.
