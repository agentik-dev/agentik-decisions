---
status: open
updated: 2026-10-16
owner: kevin
audience: agent
---
# Ask from home-tech: `backlog` reads a level only at a lead's end, and a done row never leaves, 2026-10-16

From umbrella sitting 2026-10-16-17-umbrella, from its survey of home-tech's `NICE_TO_HAVE.md` through `agentik decisions backlog`. Two asks, never rulings; this repo's sitting decides how and when.

1. **A lead that opens with its level reads unlevelled.** `src/decisions/backlog.py` line 30, `FORMS`, takes a level in four shapes: the whole lead, `S4,` at its head, `, S4` or `; S4` at its end, and `(S4)` at its end. home-tech's refuter notes since packet site-claims-96 put the level first, `- **(S4) The hand row ...**`, so 17 of its rows read `S4?` until the sitting added a section sentence. Either `FORMS` gains the head form, `^\(S[1-4]\) `, or the plugin's reference names the four shapes where a writer of a note sees them (its `SKILL.md`, next to the section sentence). home-tech's measure of today: 650 of 850 rows still read `S4?`, the older sections with no sentence and no lead form.

2. **A row marked done stays in the backlog.** `DONE` (line 45) grades a build-order step by the word `done` in its lead; a `NICE_TO_HAVE.md` row has no such read, so a row whose text ends "Done on 2026-10-16 by sitting ...: ..." keeps its place and its count (home-tech's line 27 today, the hand row that left `docs/manageability.md` at f9007c1f). Either a row with a `Done on <date>` sentence leaves the placed list and is counted apart, or the output names the shape a done row should take so a repo can keep its rows and its count honest. The count is what the umbrella's survey reads first.

Nothing is asked back.
