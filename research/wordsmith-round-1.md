# Wordsmith #18, round one (Oct 31, 2026)

Morg asked for a writer, “our Mark Twain”, so the cards “just feel really good”: nothing silly-easy, wrong answers in range. This round wrote the house voice (`build/decks/VOICE.md`), reworded 19 weak cards with `tools/vet.py edit` (back to all three reviewers), and leaves four taste tests for Morg and a list of decoy problems for Decoys #17. Branch `wordsmith`.

## The 19 cards
Picked from a dump of all 1,490 cards in play, skipping Morg’s pinned nine, the Board Room’s seven drafts and the three locked cards. Only `ex`, `means`, `hook` and two `src` fields changed, never an answer or a kind, so no deck-mate’s wrong answers moved. Every new fact was read on the card’s official source first.

| Card | What was weak | What changed |
|---|---|---|
| `soccer:2` volley | the sentence defined the answer | it shows a volley, hook `cross` |
| `lingo-more:25` free agent | the sentence said what the means says | the star’s phone begins to ring |
| `lingo-more:31` professional foul | the same | the last defender tugs a shirt, hook `defender` |
| `alpha:81` girl dinner | not about the game | halftime orange slices, hook `halftime` |
| `basics:0` gloves | an unclear means | “Optional for every player under Law 4” (theifab.com Q&A) |
| `wc26:37` Bronze Ball | the sentence defined the answer | the Golden Boot moves up, the means defines |
| `ucl:40` Glasgow | means “At Hampden Park” | “Won by a famous Zidane finish” (uefa.com 2001–02 season page, now its src) |
| `ucl:65` 4–1 | means “Real Madrid kept the trophy” | “Their second title in a row” (uefa.com), hook `Cardiff` |
| `ucl:17` Atlético Madrid | “on penalties” twice | “Real’s neighbors lost the shoot-out 5–3” |
| `bundesliga:41` Werkself | a bare nickname | the Bayer workers in the sentence, “Once mocked as Neverkusen” (bundesliga.com) |
| `seriea:12` Lazio | means “The Olympics began in Greece” | “home of the Olympics” in the sentence, “Founded in 1900 as a running club” (legaseriea.it) |
| `epl:28` London | means “Home to several league clubs” | “They left Highbury for it in 2006” (premierleague.com) |
| `mls:10` FC Cincinnati | means echoed the sentence | “For the best regular-season record” (mlssoccer.com) |
| `nwsl:53` Portland | means “Portland Thorns FC” | “Home field: Providence Park” (nwslsoccer.com schedule) |
| `nwsl:59` Louisville | means “Racing Louisville FC” | “Home field: Lynn Family Stadium” (nwslsoccer.com schedule) |
| `intl-women:64` Seleção | means “Marta’s national team” | “Marta’s 17 World Cup goals are a record” (fifa.com) |
| `intl-women:4` Spain | means “Their first World Cup final” | “Eight years after their World Cup debut” (fifa.com, now its src) |
| `ligue1:32` La Beaujoire | means “Stade de la Beaujoire in full” | “Home of Les Canaris” (ligue1.com) |
| `laliga:31` Zidane | “took over” twice | “replaced”, “He was 43 at the time” |

## Taste tests for Morg
Each lists the wording that landed first (the pick), then the others. His picks go into `MORG-STYLE.md`.

1. **How a meaning line pays off** (`bundesliga:41`)
   - A, pick: Leverkusen, founded by Bayer company workers, are the **Werkself** · means: Once mocked as Neverkusen
   - B: Founded by Bayer company workers in 1904, Leverkusen are the **Werkself** · means: Literally, the Factory XI
   - C, the old one: Leverkusen are nicknamed the **Werkself** · means: German for factory team
2. **How much story in a lingo sentence** (`lingo-more:25`)
   - A, pick: Her contract over, the star became a **free agent** and her phone began to ring
   - B: The star’s contract ran out, so she was a **free agent** and every team called
   - C, the old one: With no contract, the star became a **free agent** and could join any team
3. **A green card that defines its own answer** (`wc26:37`)
   - A, pick: At the 2026 World Cup, Kylian Mbappé won the Golden Boot and the **Bronze Ball** · means: Given to the third-best player
   - B, the old one: Kylian Mbappé won the **Bronze Ball** as the tournament’s third-best player · means: He also won the Golden Boot
4. **Which fact leads** (`seriea:12`)
   - A, pick: **Lazio** took their sky blue and white from the flag of Greece, home of the Olympics · means: Founded in 1900 as a running club
   - B: **Lazio** began in 1900 as a running club and took their colors from Greece’s flag · means: Greece, home of the Olympics
   - C: **Lazio** wear the colors of Greece’s flag, a nod to the Olympics · means: Founded in 1900 as a running club

A house-style question, not a taste test: the serial comma. The decks write series without it 28 times and with it 8 times (`legends:59`: “in 2013, 2017, and 2022”). Pick: none, the decks’ majority, and it saves room on the small phone.

## Decoy problems for Decoys #17
Noted, not changed: wrong answers out of range of the right one.
- `rules:7`, `rules:14`: a 45-minute half and a 10-minute sin bin draw 8 seconds and 5 seconds.
- `intl-women:57`: Carli Lloyd’s 16-minute hat trick draws golden goal, SheBelieves Cup and Algarve Cup.
- `nicknames:50`: “a local way of saying hey” draws mattress makers, frogs, anchovies and parakeets.
- `legends:9`: the first keeper to win the Golden Ball draws only outfield players.
- `legends:59`, `legends:60`: Sinclair’s Thorns and Barcelona’s women draw men’s clubs (Santos, Dynamo Moscow, Flamengo).
- `awards:46`: England, beaten in the 2023 final, draws Celtic, a club. It is also a match fact in Awards, the same fact as `intl-women:4`.
- `intl-men:14`: Messi’s 2022 Golden Ball draws Tim Howard and Bert Patenaude.
- `nwsl:37`: Houston’s 2020 Challenge Cup draws Golden Boot, Ironwoman, Decision Day and draft.
- `wc26:37`: the award kind holds only Golden Glove and Young Player Award. It needs the Golden Ball and Silver Ball.
- `bundesliga:41`: Werkself is the only German word among Billy Goats, Eagles and Lions.
- `basics:0`: the gear kind’s singular “shoe” (the sentence keeps “her” so it still reads).
- `soccer:54`: relegated draws only offside and clinical.

## For later rounds
- Two templates make whole decks read alike: “X play their home games at Y” (40 cards) and “X are nicknamed the Y” (36). Rework them deck by deck, meaning lines first.
- Everton’s Toffees and Hamburg’s Red Shorts can’t say why: their sources don’t explain the nicknames.
- Not done this round: a screenshot of each reworded sentence at 320×568. `tools/tilecheck.py` passed every new hook in a test build with the pending cards, and the longest new sentence is 81 characters, inside the 85 the checks already cover.
