# Brief for the nine-card research workers (draft, Oct 29, 2026)

Written by GM TRIVELLE (session `session_014c87SZPcUX9dUDfVKhzS8s`) for the workers it starts after the usage reset, once Morg says go. Each worker gets this file plus its own job below.

## The plan, resized

Morg's plan was nine workers, one per category. The inventory in `README.md` shows the vetted pool already holds plenty of cards for seven of the nine, and Trivelle researched Messi and CR7 itself before the reset (`messi.md`, `cr7.md`). Technique turned out to have 22 vetted cards already (`README.md`). So two workers cover what's left:

| # | Title | Job | Effort |
|---|---|---|---|
| 1 | TRIVELLE 1 · HOLD · MLS and NWSL | fresh facts from both 2026 seasons | medium |
| 2 | TRIVELLE 2 · HOLD · EPL and World Cup | fresh facts from this season and this summer | medium |

Technique, Lingo and Basics need no research: the desk picks their cards from the vetted pool. Job 3 below, a few fresh Technique facts, is there if Morg wants more than the pool holds. The Messi and CR7 leads (facts so far only on news sites) go to whoever has room after, or to Trivelle.

## Before you start (Morg's rules)

1. Reply in one line: your plan, its size, the effort it needs.
2. Retitle your session `TRIVELLE <n> · HOLD · <job>` and wait. Only Morg sets your effort. Start when he says go, typed in your session or relayed word for word by GM TRIVELLE.
3. Then retitle `TRIVELLE <n> · ACTIVE · <job>` and begin.

## What done means

A research pile in `research/nine/<job>.md`, in the shape of `research/nine/messi.md` (read it first): about 25 facts, each with its official source, the page's date and what's fresh, then 6 to 10 card ideas across the three colors with their wrong answers, then what's still open. Stop at 25 facts or about an hour, whichever comes first. No new jobs.

## The rules

- **Official sources only** confirm a fact: the list in CLAUDE.md, "Sources per deck". News sites and Wikipedia can point you to a fact (call it a **lead**), never confirm it. Never trust memory for anything that could have changed, and give every number its source's date.
- **fifa.com** comes back empty in a plain fetch: use `python3 tools/fifa.py <fifa.com url>`, which reads FIFA's own content feed.
- **Facts, never wording:** no copying anyone's sentences or question lists. Every idea in your own words.
- **Card ideas follow `build/decks/SPEC.md`** (read it): one plain sentence holding the answer, a hook from the sentence that isn't the answer, two believable wrong answers, and never the words soccer or football (CLAUDE.md, "House style").
- **No semicolons** in anything you write. Morg's house rule: use commas, colons, em dashes or periods.
- **Files:** you own only `research/nine/<job>.md`. No deck edits, no builds, no hub writes, and no messages to Morg's other chats.
- **Git:** work on your own branch, `nine-<job>`, made from `origin/daily`. Push after every five facts, since a usage limit can stop you mid-turn with no warning. Never push `daily` or `main`.

## Reporting

One message to GM TRIVELLE with send_message (`session_014c87SZPcUX9dUDfVKhzS8s`): your branch and last commit, how many facts, your three best card ideas, and what's left. Then retitle `TRIVELLE <n> · (done) · <job>`.

## The jobs

### 1 · MLS and NWSL

Fresh facts from both 2026 seasons, from mlssoccer.com and nwslsoccer.com only:
- **MLS:** Decision Day's date (a news report says Nov 7: confirm), the Golden Boot race (Messi led with 25 goals on Oct 29), the Supporters' Shield, MVP finalists, MLS Cup 2026's date and format, records set in 2026, new stadiums (Inter Miami's Nu Stadium) and new teams.
- **NWSL:** the 2026 Shield, the Golden Boot, records set in 2026, the playoffs and the championship's date and venue, new teams in 2026, the season's awards.
- Mark anything that will change before mid-November for the watch list (`build/vetting/WATCH.md`).
- **What exists:** 61 MLS cards and 65 NWSL cards are in the draw. Skip facts they already teach.

### 2 · EPL and World Cup

Fresh facts, from premierleague.com and fifa.com:
- **EPL:** the 2026–27 season so far (the leaders, the top scorers, records broken, the promoted clubs, new managers), and anything from the last few weeks.
- **The World Cup:** what the wc26 deck doesn't teach yet (it holds 60-odd cards on the 2026 tournament), the next World Cups (2030, 2034) and the 2027 Women's World Cup in Brazil, including any draw or schedule news this autumn.
- **A lead to confirm:** Harry Kane won the 2026 Ballon d'Or on Oct 26 in London, the first Englishman since Michael Owen in 2001, and Alexia Putellas won the women's award for the third time. The Awards deck's sources are fifa.com and ballondor.com.
- **What exists:** 104 EPL cards and 193 cards that touch the World Cup are in the draw. Skip facts they already teach.

### 3 · Technique (only if Morg wants more)

The pool's 22 Technique cards are listed in `README.md`, and Morg's "tech" question is answered there. If he wants fresh ones:
- **What it holds:** the named moves (rabona, Panenka, trivela, Cruyff turn, step-over, nutmeg, bicycle kick, scorpion kick, rainbow flick, olímpico) and the core skills (first touch, the inside-of-the-foot pass, the instep drive, heading, the throw-in).
- **Its sources:** propose the fewest. Likely theifab.com for what the Laws allow (a feint in a penalty run-up, Law 14, a throw-in's feet and hands, Law 15, playing in a dangerous manner, Law 12), Merriam-Webster and Dictionary.com for the names of moves (the Lingo deck's sources), and maybe ussoccer.com's coaching pages for the skills. Morg decides, so give your pick and why.
- **Ideas the pool lacks:** the passed penalty (Law 14 lets the kicker roll it forward for a teammate), a free kick lifted with both feet (Law 13), the Cruyff turn's 1974 World Cup debut, the rabona, the rainbow flick, the trivela by name.
