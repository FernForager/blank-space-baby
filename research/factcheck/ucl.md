# ucl fact-check (2026-10-16)

67 cards checked. 63 pass. 4 have problems.

Source: uefa.com only (season pages under /uefachampionsleague/history/seasons/, the all-time stats on /uefachampionsleague/history/, the final records page, the Women’s Champions League history page and history article, and uefa.com news reports)

- **[15]** `Steaua București`: the sentence and hook name Barcelona, yet Barcelona is in the same `k` and not grouped with Steaua, so a player can see “Barcelona” as a wrong button for “___ beat Barcelona.” The fact itself is right (Steaua 0–0 Barcelona, 2–0 on penalties, Duckadam the hero). Source: https://www.uefa.com/uefachampionsleague/history/seasons/1985/. Fix: add the groups entry `["Steaua București", "Barcelona"]`
- **[30]** `Luis Enrique`: the fact and means are right (Barcelona 2015, Paris 2025 and 2026, three titles), but the src season page never names the coach. Minor src issue. Source: https://www.uefa.com/uefachampionsleague/news/0252-0e98c715bb79-dea77f56e2bd-1000--final-records-and-statistics/. Fix: use that URL as src
- **[48]** `Barcelona`: right (“an unprecedented sixth straight final”), but the src 2025–26 season page doesn’t show the six-final run. Minor src issue. Source: https://www.uefa.com/womenschampionsleague/news/0250-0c50f8c5a638-5677bdc4dec5-1000--uefa-women-s-champions-league-history/. Fix: use that URL as src
- **[61]** `5–0`: right (the biggest win in any European Cup or Champions League final), but the src 2025 season page doesn’t state the record. Minor src issue. Source: https://www.uefa.com/uefachampionsleague/news/0252-0e98c715bb79-dea77f56e2bd-1000--final-records-and-statistics/. Fix: use that URL as src

Also noted, not counted as problems:
- Seven women’s cards share the hook “women’s” (47, 48, 50, 51, 52, 53, 54). The draw never deals two same-hook cards on one board, so only one of them can appear a day, which works against the women’s-card guardrail. “women’s” also names nothing
- Other repeated hooks: “Real Madrid” on five cards, and “scoring list”, “top scorer”, “2012 final”, “Manchester”, “Inter”, “Bayern”, “Barcelona”, “Lyon”, “Tottenham” and “PSG” on two each
- Lewandowski’s 109 (and Ronaldo’s and Messi’s totals) can still move if they play in the 2026–27 competition, which has started
- uefa.com refuses plain fetches, so the live pages were read in headless Chromium
