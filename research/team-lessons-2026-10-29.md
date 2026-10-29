# Running a team of Claude sessions: what Peninsula Hiker learned

Sent by Scout, the GM of the Peninsula Hiker chat (session_01EtV5RmLoxwvQiSdRwYxdyZ), to TRIVELLE on Oct 29, 2026, at Morg's ask, before Triviela's nine research workers start. Scout's words, with its few semicolons turned into commas and periods for the house style: lessons, not orders, except section 2, which is Morg's own rule. What Triviela takes from it is in CLAUDE.md, under "Running a team of sessions".

*Written 2026-10-29 after two nights with up to 32 sessions at once. Every rule here came from something that went wrong or from Morg saying how they want it.*

## 1. The shape
- **One coordinator, many workers.** One session coordinates (we call it the GM). It starts the workers, gives each one job, decides the order their work lands, checks every landing itself, deploys, and reports to Morg. Workers never deploy.
- **One job per worker, start to finish.** Each worker takes one job from its brief to its landing, on its own branch, then stops. Say "No new jobs" out loud in every order near the end of a session, or a worker that finishes early will start something.
- **Numbers, and one writer for the counter.** Workers are numbered. The GM takes each number and writes it back before the worker begins. Two workers once read the counter at the same moment and took the same number.
- **Titles that scan in order.** Put the number first, then the state, then the job: `⛰️ Scout 7 · ACTIVE · Android playthrough`. The states are HOLD, ACTIVE, (paused) and (done). Only sessions at work say ACTIVE.

## 2. Starting a worker
- **Morg sets the effort, so every start waits for Morg.** Only Morg can set a session's effort. Whoever starts a session sends Morg a push notification at once, naming the session's title and the effort it needs, and adds one to-do in the hub: "Set <title> to <effort>".
- **Orders, then hold.** A worker given orders, new or woken from a pause, replies in one line with its plan, its size and the effort it needs. It retitles itself HOLD and waits until Morg says go, typed in its own session or relayed word for word by the GM. Only then does it retitle itself ACTIVE and start. Every set of orders ends by saying so.
- **Brief it like a peer.** The brief is the worker's whole context. Say the goal and what done means, what is already ruled out, which files to read, own and not touch, how to land and which checks to run, and whom to report to, by session id. A brief you can't write clearly means the job isn't understood yet.
- **Name the coordinator in every brief.** Workers started under one coordinator kept reporting to it after another took over.

## 3. While they work
- **Push after every meaningful step.** Usage limits stop every session mid-turn with no warning. Work that only lives in a container can be lost, and a pushed branch never is.
- **Files have owners.** A job owns the files its brief names. A shared file (the instructions file, the package and its lock, the build's budgets, the main page, the decision log's numbering) changes only after a heads-up to the GM.
- **Never loosen a check alone.** A budget, threshold or test is never relaxed inside a feature commit. It changes only with the GM's agreement, in its own commit that says why, and Morg hears about it.
- **Generated files are generated again after a merge,** never merged by hand.
- **Size long runs before starting them.** A 45-minute screenshot round once held a worker, and every landing behind it, for the evening's last hour.

## 4. Landing on the shared branch
- Merge the shared branch into your own branch, then run the full CI once.
- **If the tip moved since, run the short check instead:** lint plus the tests that read your files. Workers once re-ran the full CI after every merge while the tip moved every few minutes, and none could land.
- **Push by fast-forward only, never force.** A refused push means the tip moved: merge, short check, push again.
- **Never push the deploy branches.** The GM deploys.
- **Report in one message:** what landed with its commit, what it changes, which check ran last, what's left. Then retitle (done).
- **The GM verifies every landed tip** with its own full CI and logs each verified tip where an auditor can read it. A red tip belongs to the worker that landed it, ahead of new work.

## 5. Independent reviews pay for themselves
The GM ran read-only reviewers, each with a fresh context, one per landing. Give a reviewer the code and the question, not your conclusion. Write the findings into one file and route each to its owner. In one night they caught a crash, a missing save-format version bump that would have made old builds call new saves corrupt, and a schema hole that let one bad data entry hang the page.

## 6. Usage: what it really costs
- **Swarms burn fast.** 32 sessions used a whole 5-hour window in about 30 minutes, and about 14% of a week's usage in half an hour. Size the team to the budget.
- **Fresh beats woken for new work.** A session woken with a 500,000-token context pays to read it all again, then on every turn after. A fresh session with a good brief costs a fraction. Wake an old session only to finish its own job.
- **Spend the strongest model on design, architecture and reviews,** and a cheaper one on landing, upkeep and playthroughs.
- **Keep the GM's own turns lean,** and leave it room to verify, deploy and hand off after everyone else stops.

## 7. Pausing, the taper, resuming
- **Morg sets the clock:** work until a set time, nothing new after it, everything landed or paused within 30 minutes.
- **Warn before a limit:** about five minutes to push the branch, write the pause note and retitle (paused).
- **A pause note is enough to restart from:** the branch, its last commit, what's done, what's next.
- **At the end, the GM writes one resume item** listing every paused worker and its next step. Resuming is a set of orders, so it holds for Morg's effort and go too.

## 8. The inbox
- **Every decision for Morg goes in the hub, written short:** a few words of title, the pick alone, at most two lines of why. In chat, one line says the hub has something new.
- **One inbox:** anything Morg must do is a decision or a to-do, never only a line in the work list.
- **Workers write only their own hub items,** and the GM keeps the overview.
- **Creative calls get pictures from the build,** side by side, with a pick.

## 9. Check-ins, not polling
When the GM is waiting on others, it arms one check-in for later and lets reports wake it. It deletes stale check-ins and never polls in a loop.

## 10. Talking to Morg
- **Lead with the outcome,** keep it short, and end every message with the effort the session should run at.
- **Make a stop plain:** when a session stops, the last message opens by saying so.
- **When Morg states a rule, write it into the instructions file the same hour,** and where you can, make a check enforce it.

## 11. What went wrong, and the fix
1. Two workers took one number. Fix: the GM assigns numbers.
2. Reports went to the old coordinator. Fix: every brief names the GM's session id.
3. Full CI runs chased a moving tip. Fix: one full CI per landing, then the short check.
4. A long run blocked the last hour. Fix: size long runs first.
5. A budget was raised inside a feature. Fix: checks change only in their own commit, with the GM's yes.
6. The GM switched branches while its own CI ran in the same folder, which spoiled the run. Fix: one worktree per line of work.
7. A usage limit stopped every session mid-turn. Fix: push after every step, and warn before limits.
8. A change made the page hang only under software rendering, which silently blocked every screenshot tool. Fix: keep a smoke test that loads the real page, and treat "the page won't come up in the container" as a bug.
9. Workers started before Morg could set their effort. Fix: orders, then hold.
