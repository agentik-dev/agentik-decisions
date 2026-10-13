---
status: current
updated: 2026-09-29
audience: agent
---
# Intake: the portfolio ledger moved to example-ops, 2026-09-29

The portfolio ledger moved from example-mac to example-ops on 2026-09-29, by the owner's decision. The entries that bind every repo are now in example-ops's `DECISIONS.md`, and each has a new number. These are asks, and nothing here decides anything for this repo. Each ask is a citation to update in this repo's next sitting. Files under `history/` keep their text, because they record their own time.

Pin: claude-code-decisions cabf60e; example-ops b7f446b5.

## The numbers this repo cites

| example-mac | example-ops | title |
|---|---|---|
| 4 | 16 | Where a decision lives and who makes it |
| 15 | 26 | The plugin repos' build conventions |

The whole map is `history/2026-09-29-portfolio-ledger-map.md` in example-ops. Cite an entry by its title, since a title survives a move.

## The asks

1. `CLAUDE.md:8` cites example-mac `DECISIONS.md` entry 4 as the design. It is entry 16 of example-ops's `DECISIONS.md`.
2. `CLAUDE.md:16` says example-mac entries 4 and 15 bind this repo. They are entries 16 and 26.
3. `design/d17-four-verbs.md:9` and `:49` cite example-mac entry 4. The packet has landed, so this repo decides whether it is a record that keeps its text.

## What needs no change

- `README.md:178` and `design/readme/source.md:195` name the portfolio's ledger with no path.
- `src/decisions/render.py:41` names a portfolio ledger in a docstring, with no path.
- The tool ran on the moved ledger as it is: `decisions render --lint` exits 0 there, and `render --into` wrote the user-level block from it.

## One finding from the move, for this repo's NICE_TO_HAVE.md

The generated block lists every entry in force by title. A portfolio ledger that is also a repo's own ledger then shows that repo's local entries to a session in any repo. A way to mark an area as local to its repo would keep the user-level block short.
