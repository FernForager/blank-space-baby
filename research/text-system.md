# The text system (Oct 26, 2026)

Morg’s brief: every piece of English in the game is replaceable in one click, text is its own pipeline, every place text appears is as easy to nudge as anything else, and the text display and its backend are best in class. His example was the slogan, which wasn’t centered in its space (fixed Oct 26 with `text-box`, commit 049ae41).

Cards stay in their decks, since the vetting team and the build already run them. This system covers every other word: the slogan, the sign, How to play, the menu, the keys, the end screen, the share text, the Share board image, the link preview and every spoken label.

## What the industry does, and what we take
- **One string table, keyed by stable names, with a note for every string.** Every serious game and app keeps its text out of the code, keys it by descriptive IDs that never change when the wording does, and attaches context to each string (where it shows, how long it may be). Translators’ biggest complaint is strings with no context. Google’s ARB format (Flutter’s) does it in plain JSON: `"key": "text"` with an `"@key"` entry beside it for the note and the placeholders. We use that shape, so any localization tool reads our file as is.
  - https://github.com/google/app-resource-bundle/wiki/ApplicationResourceBundleSpecification
  - https://alconost.com/en/blog/game-translation-context
  - https://developers.meta.com/horizon/design/localization/
- **Placeholders, never glued pieces.** “{n} in a row!” is one string, not “n” + “ in a row!”, so another language can put the number where it belongs. The braces are ICU’s, the syntax ARB and MessageFormat 2.0 (Unicode’s new standard, in ICU since 2024) both read, so plurals or genders can come later without changing the file.
  - https://blogs.igalia.com/compilers/2024/05/06/messageformat-2-0-a-new-standard-for-translatable-messages/
- **Typography as data (design tokens).** Design teams keep sizes, faces and spacing in one table that tools read, so a change lands everywhere at once. The W3C community group’s token format went stable in Oct 2025. Our version is one table of text slots: every place text appears, with its face, size per phone, alignment, wrapping, line limit and nudge.
  - https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/
- **Pseudo-localization.** Before any real translation, swap every string for a longer, accented version (`[Ĥöŵ ŵéļļ ðö ýöû ķñöŵ… ~~~]`), about 40% longer, and look for anything that overflows, got cut, or stayed plain English (a string someone hard-coded). Microsoft and Google have done this for decades.
  - https://simplelocalize.io/blog/posts/pseudo-localization-guide
  - https://opensource.googleblog.com/2011/06/pseudolocalization-to-catch-i18n-errors.html
- **In-context editing.** The best localization tools (Lokalise’s LiveJS, Phrase’s in-context editor) let you change a string on the live screen and see it fit. That’s the model for Morg’s editor: tap the words on his phone, change them, see them fit, Send.
  - https://docs.lokalise.com/en/articles/1592525-livejs-web-in-context-editor
- **Optical centering.** CSS `text-box` (Chrome 133, Safari 18.2) trims a line to its letters, so centered text is centered on the ink, not on the font’s invisible padding. It’s what fixed the slogan.
  - https://developer.chrome.com/blog/css-text-box-trim
- **Even line breaks.** `text-wrap: balance` evens out lines of a short block (titles, the slogan). `pretty` avoids a lone last word in longer text: Safari’s version weighs the whole paragraph, Chrome’s only the last lines.
  - https://mjtsai.com/blog/2025/04/11/css-text-wrap-pretty-in-webkit
  - https://blog.logrocket.com/css-text-wrap-balance-vs-text-wrap-pretty/

## The design
### 1. The strings: `build/text/en.json`
Every player-facing string, ARB-shaped:
```
"end.best": "Best: {run}",
"@end.best": { "note": "Under the score on the end screen, when the day’s longest run of right answers is 2 or more", "slot": "best", "placeholders": { "run": { "example": "Hat Trick!" } } }
```
- IDs are named by screen and role (`board.slogan`, `menu.howto`, `share.score`) and never change.
- The text holds no HTML. The game adds the typography itself: digits in the arcade face, punctuation glued to its word, GOLAZO! in the arcade face.
- The build puts the strings into the markup at build time (no flash, no wait for scripts) and gives the script the same table for everything it writes (`t('streak.n', {n: 4})`).
- The build refuses a string with a semicolon, a straight quote or apostrophe, an unknown placeholder or a missing note, and any ID the game uses that the file doesn’t have.
- Another language later is another file (`es.json`) with the same IDs.

### 2. The slots: `build/text/slots.json`
Every place text appears, one row each: the face (pixel or arcade), the size (and the size on short and narrow phones), weight, line height, alignment, wrapping (one line, balanced, pretty), the most lines allowed, letter spacing, `trim` (center on the letters) and `nudge` (move it a few pixels, x and y). The build turns the table into the game’s text CSS, so moving or resizing text means changing one row. The old typography in the stylesheet goes.

### 3. The text check: `tools/textcheck.py`
Plays every screen at the three phone sizes and checks every slot:
- the text fits its box, with no overflow or clipping
- it keeps to its line limit
- two-line text is balanced (the last line at least about a third of the first)
- centered text is centered on its ink, within a device pixel or two
- every character is in its font
- the widest values of every placeholder (`#365`, `14 in a row!`) are tested too
- `--pseudo` runs it all again with every string about 40% longer and accented. That finds the tight spots before anyone writes a new line, and any English the game shows without going through the file.

It writes a contact sheet, every string in its slot at all three sizes, so a wording change can be judged by eye at a glance.

### 4. Morg’s text editor
On a preview link, `?text` turns on edit mode right in the game. Every piece of text gets a faint outline, and tapping it opens a box with its note and its slot’s limit. As he types, the real text on the real screen changes, at his real phone size, and turns red if it doesn’t fit. Send posts his changes to the beta’s service (as Flag and Lock already do). The hub’s “Apply my text edits” ask has Trivelle write them into `en.json`, rebuild, run the text check and put them on the beta. The real site never shows edit mode.

## Order of work
1. **The strings and the slots**, moved out of the code with no visible change. Proved by pixel-diffing every screen at three sizes before and after.
2. **The text check and the contact sheet**, with pseudo-localization.
3. **The polish pass**: centered on the letters and balanced everywhere it should be, each change shown as a before and after.
4. **The in-game editor.**
