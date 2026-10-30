# GM handoff: TRIVELLE (session_014c87SZPcUX9dUDfVKhzS8s) to TRIVELLE 3, Oct 30, 2026

The first handoff under section 12 of the hub’s shared team-practices note (Morg’s yes, Oct 30, 2026): this chat passed 600,000 tokens, and the natural break is the go-live of Morg’s first nine. CLAUDE.md is current to this commit, so this note holds only what a fresh chat can’t read there. Written in the order its absence hurts.

## 1. Running workers
None. TRIVELLE 1 (stat master, round 1, `session_01EtV5RnZ5vsoGsfAFGW45mG`) and TRIVELLE 2 (fact check of the three new cards, `session_01EtV5RmgtTULB62xt9yogBh`) are both (done). The next worker number is 3. The five audit reviewers were helper agents inside this chat, finished.

## 2. Scheduled tasks bound to the old chat
One: “Sync Triviela beta flags” (`trig_01CuT222XP868KrTqdcq13fY`, twice a day at 7:53 am and 7:53 pm Seattle, fires into the old session). It has never found a row. The successor creates its own with the same prompt (CLAUDE.md, “Syncing the marks”) and the old one is deleted at cutover. No send_later check-ins are pending.

## 3. The hub’s pointer
`team/triviela`, field `session` (version 6), must become the successor’s id before the old chat stops, or Hubble’s pings go nowhere. The stat master’s and fact checker’s standing instructions name “the GM in your orders”, so only new orders need the new id.

## 4. Open items with no owner yet
- **The slimmer CLAUDE.md** (Morg’s yes, hub decision `audit`, item 4): about half its 26,000 tokens describe versions long gone (18 cards, 15 cards, the 5×3 board, milestone 1). Move the history into `research/history.md` and keep CLAUDE.md as the current game plus Morg’s rules. The catch: current rules sit inside superseded sections (near-miss numbers, sharp text, digits and fonts live under “The shootout”), so it’s a rewrite into “the game as built”, not a cut. The successor’s first job, at max.
- **The audit’s open list**, in `research/audit-2026-10-30.md` under “Open, for later”: flags and locks on a content-only fingerprint, the build replaying the page’s choices, the 2× iPhone checks, the screen-reader gaps (needs one new spoken word, so Morg’s OK), and the small ones.
- **Morg’s to-dos in the hub:** the preview-link sign-in (`accesspolicy`), the www redirect (`wwwredirect`), and “Say go in the Triviela chat” (`golivechat`) for the nine.
- **Hubble** was asked (Oct 30) to show each chat’s size in the hub, read once a round. No reply needed.
- **Scout** may edit team-practices (version 4 now). Whoever learns a rule changes the document first, logs it, and sends the other GM one line.
- **Cards waiting on events** (`stats/round-1.md`, the watch list): NWSL Decision Day Nov 1 (Gotham’s first Shield, Sanchez’s Golden Boot, Bethune’s assists), MLS Decision Day Nov 7 (Messi’s Golden Boot), the NWSL final Nov 21. Each is a stat master round: a fresh session from `stats/STAT-MASTER.md`, holding for Morg’s effort and go.
- **For the editor, before the daily comes back:** the 14 hooks too wide for the smallest phone (`out/tilecheck.txt`), the 29 cards that say soccer or football, and Morg’s score titles 0 to 9 (his idea, hub work item).
- **Parked:** the secret shootout (its own session, Morg: one thing at a time), the Board Room’s six drafts.

## 5. The audit log of verified tips
Triviela’s log is the “Gone live” bullets in CLAUDE.md. Live now: `main` 9b41b32 (Oct 29, the tidy-up update). Next: the nine plus the audit’s fixes, `daily` 237f6ff, golive.py all good (the save moves to v 6, so every phone starts the nine fresh), waiting on Morg’s go in chat (a hub answer doesn’t pass the permission check for a push to `main`).

## 6. In flight and next
- **In flight:** the go-live above. On Morg’s go: `git push origin daily:main`, wait a minute or two for Pages, `python3 tools/livecheck.py`, then a “Gone live” line in CLAUDE.md, decision `golive4` done, to-do `golivechat` done.
- **Next:** the slimmer CLAUDE.md, then the audit’s open list in order.
- **Cutover:** reports before the cutover came to the old chat, which forwards them. The old chat stays ACTIVE until TRIVELLE 3 is ACTIVE.
