# Stats, round 1: this week’s fresh facts (TRIVELLE 1, the stat master, Oct 29, 2026)

For Triviela’s first hand-picked board. Every fact here is proved on an official page, with the page’s address, the date it was true and how long it stays true. Facts are in our own words, not cards. Card ideas are drafts for the desk and Morg, and every one still goes to the fact checker before it plays. Leads (facts found only on news sites) are in their own section near the end and never become cards. The watch list is last.

**Sources used:** nwslsoccer.com (its news pages and the league’s own stats API, api-sdp.nwslsoccer.com), uefa.com. More below as the round goes on.

**How the NWSL pages were read** (for the next worker): nwslsoccer.com draws its pages by script. Its stats API answers a plain fetch. The 2026 regular season’s id is `nwsl::Football_Season::0b6761e4701749f593690c0f338da74c` (the standings page’s widget names it), and the useful calls are `/v1/nwsl/football/seasons/<id>/standings/overall`, `/matches` and `/stats/players?category=general&orderBy=goals&direction=desc` (or `orderBy=assists`), all under https://api-sdp.nwslsoccer.com with `?locale=en-US`. News stories hold their text in the page’s script data as `markdownText` (some as a numbered text chunk the field points to), so a short script reads them without a browser. uefa.com stories time out to a plain fetch from here, so they were read with WebFetch.

## The NWSL before Decision Day

### 1. The table with one game left
Every club has played 29 of its 30 games. Gotham FC lead with 58 points (17 wins, 7 draws, 5 losses), ahead of the San Diego Wave (55), the Washington Spirit (52), the Kansas City Current (50), Angel City (49), the Utah Royals (47), the Portland Thorns (47) and the Seattle Reign (44). Then North Carolina (42) and Denver (41), chasing the last playoff place. Chicago are last with 17.
- **Proof:** the league’s stats API, https://api-sdp.nwslsoccer.com/v1/nwsl/football/seasons/nwsl::Football_Season::0b6761e4701749f593690c0f338da74c/standings/overall?locale=en-US (read Oct 29, 2026, 23:47 UTC).
- **Shelf life:** changes on Decision Day, Nov 1, 2026. Not a card.

### 2. The Shield race
Gotham lead San Diego by three points. A win or a draw at home to Utah gives Gotham the first Shield in their history. San Diego, away at Bay FC, win their second Shield (after 2023) only with a win and a Gotham loss. Washington can reach only 55, so it’s a two-club race. Gotham are also the reigning champions, the 2025 title winners.
- **Proof:** “Four teams clinch playoff spot, Croix Bethune breaks assist record,” nwslsoccer.com, Oct 27, 2026, https://www.nwslsoccer.com/news/croix-bethune-breaks-assist-record-royals-clinch-first-playoff-spot-and-summit-put-up-6-in-do-or-die-mat, and the table above.
- **Shelf life:** decided Nov 1. The winner is timeless after that.
- **Card idea (after Nov 1, if Gotham win it):** yellow. “In 2026, Gotham FC won the NWSL Shield for the first time.” Blank the club: answer Gotham FC, wrong answers San Diego Wave, Washington Spirit (both real contenders this year, so believable, and neither is a second right answer since the sentence says first time and 2026). Hook: Shield. If San Diego win it instead: “In 2026, San Diego Wave won their second NWSL Shield,” same wrong-answer idea. Check nwsl:35 and nwsl:8 for overlap (both are Shield cards, older years).

### 3. Decision Day is one afternoon
All eight final games kick off at the same moment: Sunday, Nov 1, 2026, at 22:00 UTC (5 pm in New York, 2 pm in Seattle). Gotham host Utah at Sports Illustrated Stadium in Harrison, New Jersey, and San Diego play at Bay FC’s PayPal Park in San Jose. The league’s plan from July 2025 had named the weekend of Oct 30 to Nov 1, and the schedule put every game on the Sunday.
- **Proof:** the stats API’s match list, https://api-sdp.nwslsoccer.com/v1/nwsl/football/seasons/nwsl::Football_Season::0b6761e4701749f593690c0f338da74c/matches?locale=en-US (read Oct 29, 2026), and the July 2, 2025 framework release (fact 8).
- **Shelf life:** over on Nov 1. Not a card. (nwsl:39 already teaches what Decision Day is.)

### 4. The Golden Boot and the scoring record
Ashley Sanchez of the North Carolina Courage has 20 goals in 29 games, level with Temwa Chawinga’s single-season record of 20 (2024). One more on Nov 1 and the record is hers alone, the first 21-goal season in league history. She reached 20 with a goal in Utah in September, after five goals in four games that month (September Player of the Month). Next: Orlando’s Barbra Banda (17) and Portland’s Sophia Wilson (13). Banda could catch her only with a hat trick while Sanchez doesn’t score.
- **Proof:** the stats API’s scorers, https://api-sdp.nwslsoccer.com/v1/nwsl/football/seasons/nwsl::Football_Season::0b6761e4701749f593690c0f338da74c/stats/players?locale=en-US&category=general&orderBy=goals&direction=desc&page=1&pageNumElement=25 (read Oct 29, 2026), “Matchweek 26: The Home Stretch,” nwslsoccer.com, Oct 23, 2026, https://www.nwslsoccer.com/news/matchweek-26-the-home-stretch, and the Player of the Month release, Oct 1, 2026, https://www.nwslsoccer.com/news/north-carolina-courage-forward-ashley-sanchez-named-september-player-of-the-month.
- **Shelf life:** the total and the record change on Nov 1. The leads’ figure of 15 goals (research/nine/mls-nwsl.md) is stale. Already on cards: nwsl:31 (Chawinga first to 20, in 2024). The deck’s cut list held Sanchez back because the record was still moving.
- **Card idea (after Nov 1):** red. If she scores: “In 2026, Ashley Sanchez became the first NWSL player to score 21 goals in a season,” answer 21, near-miss numbers. If she doesn’t: “Ashley Sanchez won the 2026 Golden Boot with ___ goals,” answer 20 (green would be too generous: you have to follow the league).

### 5. Croix Bethune’s assist record
Kansas City’s Croix Bethune set the NWSL record for assists in a season with her 11th, setting up Vanessa DiBernardo’s winner in a 2–1 win over the Washington Spirit on Oct 25, 2026. The old record of 10 was Tobin Heath’s (2016), and Bethune had tied it in 2024, playing for Washington, the club she beat to break it. Utah’s Cloé Lacasse is next with 10.
- **Proof:** the Oct 27, 2026 recap (fact 2’s address), the Oct 23 preview (fact 4’s), and the stats API’s assist list, https://api-sdp.nwslsoccer.com/v1/nwsl/football/seasons/nwsl::Football_Season::0b6761e4701749f593690c0f338da74c/stats/players?locale=en-US&category=general&orderBy=assists&direction=desc&page=1&pageNumElement=6 (read Oct 29, 2026: Bethune 11, Lacasse 10).
- **Shelf life:** “broke the record in 2026” is timeless. The count (11) can still grow on Nov 1, so a number card waits for Decision Day.
- **Card idea:** red. “In 2026, Croix Bethune broke Tobin Heath’s record for ___ in a season.” Answer assists, wrong answers goals, shutouts (all three are season records a fan has heard of). Hook: Bethune. Needs a kind (`k`) of stat words, which the deck may not have yet: the desk’s call.

### 6. Utah’s first playoff place, Portland’s twelfth
Four clubs clinched playoff places on the weekend of Oct 23–25, 2026: Kansas City (a third straight), Portland, Angel City (the first time since 2023) and Utah, who made the playoffs for the first time in club history. Portland are in for a 12th time, more than any other club. Gotham, San Diego and Washington were already in, so seven places are filled. The eighth goes to Seattle with a win at home to Orlando on Nov 1, and otherwise to North Carolina or Denver, who play each other.
- **Proof:** the Oct 27, 2026 recap (fact 2’s address).
- **Shelf life:** Utah’s first and Portland’s 12th are timeless as 2026 facts. The eighth place is decided Nov 1.
- **Card ideas:** red. “In 2026, the Utah Royals reached the NWSL playoffs for the first time.” Blank the club: answer Utah Royals, wrong answers Bay FC, Racing Louisville (both were knocked out of the 2026 race in Week 23, by the Oct 23 preview, so neither can fit). Yellow: “In 2026, the Portland Thorns reached the NWSL playoffs for a record ___ time,” answer 12th, near misses. Hook: Thorns. (nwsl:0 and nwsl:53 are Portland cards about titles and home, not this.)

### 7. Kansas City’s hat tricks
The Kansas City Current had three hat tricks by mid-October 2026, from Temwa Chawinga, Haley Hopkins and Debinha (in Matchweek 24). They are the first NWSL club with hat tricks in back-to-back games and the first with three in one season.
- **Proof:** “Matchweek 25: The Final Countdown,” nwslsoccer.com, Oct 15, 2026, https://www.nwslsoccer.com/news/matchweek-25-the-final-countdown.
- **Shelf life:** the two firsts are timeless. The count of three can grow, so write “first club with three hat tricks in a season.”
- **Card idea:** red. “In 2026, the ___ became the first NWSL club to score three hat tricks in one season.” Answer Kansas City Current, wrong answers Orlando Pride, Portland Thorns. Hook: hat tricks.

### 8. The playoff dates
Eight clubs make the 2026 NWSL Playoffs. The top four host the quarterfinals, Nov 6–8. The semifinals are Nov 13–15, and the 2026 NWSL Championship is on Nov 21. ESPN and ABC show two quarterfinals, CBS and Prime Video one each, and the final is in primetime on CBS for a fifth straight year. This was also the league’s first season with 16 clubs, with Boston Legacy and Denver new, each playing 30 games (240 in the regular season, by the match list).
- **Proof:** “NWSL Announces 2026 Schedule Footprint,” nwslsoccer.com, July 2, 2025, https://www.nwslsoccer.com/news/nwsl-announces-2026-schedule-footprint, the Oct 23 preview (“Top-4 Finish (Home Quarterfinal)”), and the match list (fact 3).
- **Shelf life:** dates pass by Nov 21. Already on cards: nwsl:30 (16 clubs in 2026) and nwsl:63 (Boston Legacy and Denver Summit’s first season). Not news, so no new card.

### 9. The final and the awards night
The 2026 NWSL Championship is on Saturday, Nov 21, at 8 pm ET at Audi Field in Washington, D.C., on CBS and Paramount+. Championship week has the NWSL Awards on Nov 18 (6:30 pm ET on ESPN2, at Lisner Auditorium at George Washington University, hosted by Jess Sims), the Skills Challenge on Nov 20 at Episcopal High School in Alexandria, Virginia, and a 5K and a fan fest at the Wharf on the day of the final. Audi Field is also Washington’s home: the Spirit play Chicago there on Decision Day.
- **Proof:** the championship page, https://www.nwslsoccer.com/championship (read Oct 29, 2026), and the awards page, https://www.nwslsoccer.com/awards (read Oct 29, 2026), the match list for the Spirit’s home.
- **Shelf life:** the awards on Nov 18 and the final on Nov 21 bring the season’s freshest facts: the MVP, the other awards and the champion. Already on a card: nwsl:48 (Audi Field hosts both the 2022 and 2026 finals). A future-tense card about the final would go stale on Nov 22, so wait for the result.

## The 2026 Ballon d’Or (London, Oct 26)

### 10. Harry Kane wins
Bayern Munich’s Harry Kane, 33, won the 2026 men’s Ballon d’Or on Monday, Oct 26, at the London Palladium, ahead of Kylian Mbappé (second) and Lamine Yamal (third). It was the first ceremony held in London, in the award’s 70th year. He also won the men’s Striker of the Year award that night. His season: 73 goals for club and country in 2025–26, the Bundesliga’s top scorer for a third year running and 14 Champions League goals as Bayern reached the semifinals and won a domestic treble.
- **Proof:** “Harry Kane wins 2026 Men’s Ballon d’Or,” uefa.com, Oct 26, 2026 (updated Oct 27), https://www.uefa.com/uefachampionsleague/news/02aa-21ec47378e70-b29defb43769-1000--harry-kane-wins-2026-men-s-ballon-d-or/, and “Alexia Putellas and Harry Kane win 2026 Ballon d’Or awards,” uefa.com, Oct 27, 2026, https://www.uefa.com/news-media/news/02aa-21ec75ddadcd-43023dfa1670-1000--alexia-putellas-and-harry-kane-win-2026-ballon-d-ortm-awards/ (the venue, the winners list). The awards have been run by France Football and UEFA together since 2024, so uefa.com is their own site. ballondor.com refuses this workspace’s fetches.
- **Shelf life:** timeless. The next ceremony, fall 2027, adds a new winner.
- **Card ideas:** green. “The 2026 Ballon d’Or went to ___,” answer Harry Kane, wrong answers Kylian Mbappé, Lamine Yamal (second and third, so believable, and neither won). Hook: Ballon d’Or. Yellow: “Harry Kane won the 2026 Ballon d’Or playing for ___,” answer Bayern Munich, wrong answers Tottenham, Real Madrid. Hook: Harry Kane. Already on cards: awards:66 (his 2018 World Cup Golden Boot), bundesliga:13 and epl-more:0 and :18 (his Bayern and Tottenham records), never this.

### 11. England’s first winner in 25 years
Kane is the first Englishman to win the Ballon d’Or since Michael Owen, of Liverpool, in 2001. England’s winners are Stanley Matthews (1956, the very first winner), Bobby Charlton (1966), Kevin Keegan (1978 and 1979), Owen (2001) and Kane (2026): five men, six wins.
- **Proof:** the Kane story (fact 10: “the first Englishman to win the award in 25 years”), and “Ballon d’Or laureates: Who has won football’s most prestigious award?”, uefa.com, updated Oct 26, 2026, https://www.uefa.com/ballondor/news/0292-1c27056169a7-bc88d1fdba43-1000--ballon-d-or-laureates-who-has-won-football-s-most-prestig/ (the full list by year).
- **Shelf life:** timeless.
- **Card idea:** yellow. “Before Harry Kane in 2026, the last Englishman to win the Ballon d’Or was ___ in 2001.” Answer Michael Owen, wrong answers Steven Gerrard, David Beckham (famous English players of that era who never won it). Hook: Harry Kane. Red: “Stanley Matthews won the first Ballon d’Or, in ___,” answer 1956, near misses. Hook: Matthews.

### 12. Alexia Putellas’s third
Alexia Putellas won the women’s Ballon d’Or for the third time, after 2021 and 2022. That ties Aitana Bonmatí’s three (2023, 2024, 2025) for the most in the women’s award, which began in 2018. The winners list names her clubs as Barcelona and London City Lionesses.
- **Proof:** the uefa.com awards story and the laureates page (fact 10 and 11’s addresses: “Alexia Putellas: 3 (2021, 2022, 2026)”, “Aitana Bonmatí: 3 (2023, 2024, 2025)”).
- **Shelf life:** timeless as “her third, in 2026.” “Shares the record” changes the day either wins a fourth (fall 2027 at the earliest).
- **Card idea:** yellow. “In 2026, Alexia Putellas won her ___ Ballon d’Or.” Answer third, wrong answers second, fourth. Hook: Putellas. (awards deck has her two Best FIFA awards, a different prize.) The London City Lionesses part is a lead (see Leads).

### 13. Charlyn Corral, Striker of the Year
Mexico’s Charlyn Corral, of Pachuca, won the women’s Striker of the Year award. Kane won the men’s. uefa.com calls it Striker of the Year, not the Gerd Müller Trophy, so a card should use that name (whether the old name still applies is a lead).
- **Proof:** the uefa.com awards story (fact 10): “Women’s Striker of the Year, Charlyn Corral (Mexico, CF Pachuca)”.
- **Shelf life:** timeless.
- **Card idea:** red. “Mexico’s Charlyn Corral was named the 2026 Ballon d’Or Striker of the Year, playing for ___.” Answer Pachuca, wrong answers Tigres, América (the Liga MX Femenil’s big clubs). Hook: Corral. Fact checker: confirm against ligamx.net too, since the card would sit in the Liga MX or Awards deck.

### 14. The rest of the night, and Messi’s eight
The other 2026 winners: Lamine Yamal and Vicky López (young talents, both Barcelona), Unai Simón (Athletic Club) and Cata Coll (Barcelona) in goal, Luis de la Fuente (Spain) and Pere Romeu (Barcelona) as coaches, Paris Saint-Germain and Barcelona as clubs of the year, and Bukayo Saka the Sócrates Award for his charity work. Spain swept the coaching and goalkeeping awards. Lionel Messi stays on a record eight Ballon d’Ors (2009–12, 2015, 2019, 2021, 2023), and Cristiano Ronaldo on five.
- **Proof:** the uefa.com awards story and the laureates page (facts 10 and 11).
- **Shelf life:** timeless, apart from the record counts, which hold at least until the fall 2027 ceremony.
- **Card idea:** yellow. “Lionel Messi has won a record ___ Ballon d’Ors.” Answer 8, near misses. Hook: Messi. Already a draft in research/nine/messi.md, and no card teaches it yet (the decks have Ballon d’Or cards for Modrić, Kopa, Dembélé and Kaká only). On the watch list.

## Messi’s Princess of Asturias Award

### 15. Spain’s top sports prize
Lionel Messi won the 2026 Princess of Asturias Award for Sports. The jury announced it on June 3, 2026, choosing him from 27 nominations from 12 countries, for his talent, his career and his charity work for children’s health and education (the Leo Messi Foundation), and calling him the player with the most titles in the history of the game. The Princess of Asturias Foundation gave the awards on Friday, Oct 23, 2026, at the Campoamor Theatre in Oviedo, with the King and Queen presiding and the Princess of Asturias there. Each laureate gets a Joan Miró sculpture, a diploma, an insignia and 50,000 euros. Messi flew to Spain to collect it and came off the bench for Inter Miami at Red Bull New York the next day.
- **Proof:** the award’s own site, the Princess of Asturias Foundation: “Leo Messi, Princess of Asturias Award for Sports 2026,” fpa.es, June 3, 2026 (published June 4, updated July 27), https://www.fpa.es/en/area-of-communication-and-media/press-releases/leo-messi-princess-of-asturias-award-for-sports-2026/, the ceremony programme, fpa.es, Oct 16, 2026, https://www.fpa.es/en/area-of-communication-and-media/press-releases/general-programme-for-the-visit-of-tm-the-king-and-queen-of-spain-trh-the-princess-of-asturias-and-infanta-sofia-on-the-occasion-of-the-2026-princess-of-asturias-awards-ceremony/ (the ceremony at 4:30 pm on Friday, Oct 23, at the Campoamor), and the jury’s words in the Oct 7, 2026 release, https://www.fpa.es/en/area-of-communication-and-media/press-releases/leo-messi-2026-princess-of-asturias-laureate-for-sports-will-meet-with-the-educational-community/. That he flew there and back to receive it: mlssoccer.com, Oct 26, 2026, https://www.mlssoccer.com/news/nashville-s-shield-standard-el-trafico-fireworks-more-from-matchday-32. fpa.es is a new source for Morg to OK (the award’s own site, like ballondor.com for the Ballon d’Or).
- **Shelf life:** timeless.
- **Card idea:** red. “In 2026, Lionel Messi won Spain’s Princess of ___ Award for Sports.” Answer Asturias, wrong answers Girona, Castile (Spanish places that sound just as royal, and the fact checker should confirm neither gives a sports award of that name). Hook: Messi. Or yellow, blanking the man: “The 2026 Princess of Asturias Award for Sports went to ___,” answer Lionel Messi, wrong answers Cristiano Ronaldo, Lamine Yamal. The prize goes across sports (Serena Williams in 2025, Carolina Marín in 2024, by the fpa.es laureates list), so the sentence must keep 2026 in it.
- **Also on the page:** his bio says he trained at Newell’s Old Boys in Rosario, moved to Barcelona with his father at 13 to join La Masia, and debuted for the first team in 2004. It credits him with 47 titles (as of June 2026, before the Campeones Cup made it 48, research/nine/messi.md fact 23), 35 of them with Barcelona between 2005 and 2021, eight Ballon d’Ors, three The Best awards, six European Golden Shoes, the Guinness record of 91 goals in 2012, and two Laureus Sportsman of the Year awards (2020 and 2023), the only male footballer to win it. These are player facts, so the club sites (or fifa.com and laliga.com) should prove them for a card: see the Messi and CR7 section.
