---
status: draft
updated: 2026-11-09
owner: the owner
audience: agent
---
# d29: `analyze`, churn first, and a block without its tails

Revised 2026-11-09 on the owner's answers and one refuter round (`REFUTE-2026-11-09-d29-design-r1.md`): the owner named the verb `analyze`, and churn is the first thing it analyzes. This record, its packet, the row and the probes keep `churn` in their names.

From the ruled draft, agentik-hq `history/sessions/DESIGN-DRAFT-2026-11-09-churn.md`: a read-only verb in this repo, R1 to R4 only, from git and `NICE_TO_HAVE.md`, with audit row d2. This repo keeps no ledger; agentik-hq entries 6 and 9 govern it. Churn is accounting over building: commits that write records while little code lands. The probes are beside the draft, in `DESIGN-2026-11-09-churn-probes/`; the fixtures are the packet's.

## 1. The verb

`agentik decisions analyze [churn] [REPO...] [--since Nd|YYYY-MM-DD] [--until YYYY-MM-DD] [--json]`

- Ruled: the analysis is a word after the verb and a bare `analyze` runs every analysis, today `churn` alone, since the owner made churn one thing the verb does and the next analysis then adds a word and changes no caller. A directory of that name is written `./churn`.
- REPO as `backlog`'s: a directory, by default the working directory; each is read at its git top's `HEAD`.
- The window is `since <= committer time <= until`. `--until` defaults to now, `--since` to `14d` before it; a date is 00:00:00 UTC. Git gets both as `YYYY-MM-DDTHH:MM:SSZ`, never a bare date, which takes the clock's time of day (`t0_dates.sh`).
- It runs only `git rev-parse`, `log`, `rev-list` and `show`. It writes no file, takes no lock, runs no model, opens no other tool's state or transcript, and ignores `--ledger`. No hook, lint row or exit code hangs on a number.

## 2. Path classes

One read: `git log HEAD --no-merges --numstat -M -z --since=S --until=U`. A path takes the first rule that fits; a rename is classed by its new path and counts its changed lines only; a binary file counts 0. Lines are added plus deleted.

| class | rule, from the repo root |
|---|---|
| vendor, in no count | a directory `vendor`, `node_modules` or `dist`; a file `go.sum`, `package-lock.json`, `uv.lock` |
| charter, history | `history/sittings/`; the rest of `history/` |
| packets, design | `design/packets/`; the rest of `design/` and `docs/` |
| handoff, nice | `HANDOFF.md`; `NICE_TO_HAVE.md` |
| other | root `DECISIONS.md`, `OPEN-QUESTIONS.md`, `CLAUDE.md`, `DESIGN.md`, `CHANGELOG.md`, `README.md` |
| test | a directory `tests`, `test` or `testdata`; a file `test_*.py`, `*_test.py`, `conftest.py`, `*_test.go`, `*_test.sh` |
| product | everything else |

Charter to other are records; test and product are the build. The table is fixed in code. Known misreads: a site repo's `docs/` is its product; a vendored `scripts/` file, a `*.test.ts` file and `pnpm-lock.yaml` count as product.

## 3. The four ratios

- **R1, records' share of lines.** Record lines over record plus build lines; `not measured: R1 (no line changed)` when both are 0.
- **R2, record commits a landing.** A record commit is a non-merge commit in the window with a path outside vendor, every such path a record. A landing is a merge commit on `HEAD`'s first-parent line in the window (`git rev-list --count --merges --first-parent`). With none the count stays and the ratio is `not measured: R2 (no merge on the first-parent line)`.
- **R3, commits a charter.** For each `history/sittings/*.md` a commit in the window touches: the commits that touch it, and of those the charter-only ones, whose every path is a charter. It prints the charters and each count's median; with none, `not measured: R3 (no charter changed)`.
- **R4, the backlog.** Snapshots at `until` and every 7 days before it, back to `since`. A snapshot is `NICE_TO_HAVE.md` at `git rev-list -1 --first-parent --before=T HEAD`. `backlog.nice_items` reads it: `rows` when every item has an id, else `bullets`, printed with a `b`. Only with rows at the first and the last snapshot: filed is the ids at the last and not the first; of the ids gone, moved are those in a first cell of `history/NICE-overflow.md` at the last, closed the rest. `rising`: three or more snapshots, all rows, each count above the one before. Otherwise `not measured: R4 filed and closed (bullets at <date>: a bullet has no id)` or `(no NICE_TO_HAVE.md at <date>)`, never a guess. Unseen: a row filed and gone between snapshots, and a frozen `history/NICE-<date>.md`.

## 4. The worked example

Window 2026-10-26T00:00:00Z to 2026-11-09T00:00:00Z at the pinned heads, computed twice (`churn_ref.py`, awk).

| | agentik-session `344818a` | agentik-decisions `7ca4c03` | agentik-hq `8172716` |
|---|---|---|---|
| commits, landings | 255, 23 | 23, 3 | 289, 3 |
| R1 records of lines | 5406 of 25913, 21% | 625 of 2401, 26% | 6495 of 9531, 68% |
| R2 record commits, a landing | 81, 3.5 | 8, 2.7 | 258, 86.0 |
| R3 charters: median, max | 21: 7, 16 | 3: 6, 7 | 15: 14, 23 |
| R3 charter-only: median, max | 23: 1, 4 | 3: 1, 1 | 108: 7, 17 |
| R4 snapshots | 151b 256b 12 | 60b 64b 1 | 12b 2 6 |

No threshold of the draft has evidence: every sitting is over its R3 median of 3, since an act's commit carries its charter, and only the charter-only row tells sittings apart. So this packet prints numbers, with no `advice` line, threshold or config key.

## 5. Output, exits, the bound

```
churn  2026-10-26T00:00:00Z..2026-11-09T00:00:00Z
== agentik-hq  commits 289  landings 3  records 68% of 9531 lines  record commits 258, 86.0 a landing  charters 15: median 14 commits, 7 charter-only  NICE 12b 2 6
not measured: R4 filed and closed (bullets at 2026-10-26: a bullet has no id)
== all 3  commits 567  landings 29  records 33% of 37845 lines  record commits 347, 12.0 a landing
not computed: tokens, account spend, work redone at a respawn, rows built and never landed
```

Each analysis opens with a line naming it and the window, so `analyze` and `analyze churn` print alike today. One `==` line a repo. A measured R4 ends `NICE 2 3 5 +5 -1 moved 1 rising`, `moved` and `rising` only when they hold; unmeasured, it ends at the counts. Another unmeasured value prints `-`; each gets a `not measured:` line. `== all N` sums R1 and R2 when two or more repos were read. A percent is whole, half up; a ratio has one decimal; a whole median has none.

`--json` carries the window once and each analysis under its name, `{"since", "until", "churn": {...}}`: the same values as numbers, an unmeasured one as `null`; its keys are the packet's section 3.

Exit, as `backlog`: 0 whenever the view printed; 2 for usage, a bad `--since` or `--until`, `since` after `until`, or an argument that is neither an analysis nor a directory; never 1. A directory outside a work tree, or with no commit, prints `== <name>  not a git work tree` or `no commit`, is `skipped`, and exits 0.

Every git child runs through `common.bounded` at `common.GIT_TIMEOUT`, 10 s. Past it the repo prints `== <name>  timed out after 10 s (git log)`, never a partial ratio; the others print, and the exit stays 0.

## 6. render: the block without its tails (audit d2)

`answer --amends` appends `; amended <date>, <source>` to an entry's tail (`answer.py:111-112` at 87f491f), and `render.block` copies each Every session line whole into CLAUDE.md (`render.py:68`), which every turn loads.

The rule, in `block` alone, so `render` and `answer` share it: an Every session entry's tail becomes its first date and the count of `amended <date>` in it. Number, title and paragraph stay word for word; a tail that opens with no date is written whole; the ledger and `show` do not change.

| tail in the ledger | in the block |
|---|---|
| `(2026-10-02; the owner)` | `(2026-10-02)` |
| `(2026-10-03 and 2026-10-04; the owner; amended 2026-10-06, answer 5)` | `(2026-10-03; amended once, see the ledger)` |
| `(2026-09-21; the owner; amended 2026-10-01, answer 3; amended 2026-10-05, answer 4)` | `(2026-09-21; amended 2 times, see the ledger)` |

In `d2_fixture.py` these three take its block from 675 to 600 B.

`render --check` exits 0 on the short form, and also on the whole-tail form, with one stderr line: `render: CLAUDE.md carries the entries' whole tails, <n> B more; run render to shorten it`. Both are functions of today's ledger, so a stale block still exits 1 with the diff. Without this, every repo whose `make check` runs `render --check` turns red at the tool's install. `render` writes the short form, as `answer` does when the markers are there.

On the owner's machine, ledgers as of 2026-11-09 16:00 PST (`r1-d2_pinned.py --at 2026-11-09T16:00:00-08:00`): 24 blocks, 50,793 B to 41,615 B, 13 of them shorter (47,227 to 39,544 B after one hq's fold, `d2_blocks.py`); the machine-wide one, at user level, 6,840 to 4,917 B.

The owner said yes on 2026-11-09. agentik-hq entry 9 and the machine-wide ledger's entry 21 both say "copies" (refuter F2), so the hq sitting amends both: the block keeps each entry's number, title and paragraph word for word and cuts its tail to the first date and a count, `(2026-09-21; amended 5 times, see the ledger)`.

## 7. For the owner, next batch: the ledger's own tail

The ticked question also gave the ledger's tail a form, T1: the first date, then the latest amendment's date and source; git holds the rest. The owner's note on the tick: "You can keep shorter ledger tails, but maybe you can summarize ledger items (combine them) at the tail." This designer's reading, not the owner's words: (a) one combined clause in the tail for the amendments T1 leaves to git, not (b) a ledger's older entries combined into summaries, since the note's "tail" is the question's. T2 is T1 with that clause second, as here:

- The machine-wide ledger's 22, 1,140 B: `(2026-09-21; amended 4 times, 2026-09-29 to 2026-10-13; amended 2026-10-31, the owner's word, agentik-hq design/03 §10 question 2; agentik-session S48 moved the default)`.
- agentik-hq 6, 197 B: `(2026-09-22; amended once, 2026-10-13; amended 2026-10-31, the owner's word, sitting 2026-10-31-1-hq)`.

Of the 51,427 B of tails in the owner's 24 ledgers T1 saves 22,844 and T2 21,722, per read, not per turn (`$TMPDIR/d29-r2/tails.py --show user 22 --show agentik-hq 6`, scratch). Both lose each earlier amendment's source, the first source, each move and 18 backticked pointers; git keeps them. T2 keeps the count act 4 prints, for `block` to read; T1 turns it to `amended once` on 5 block lines (`blocks.py` there). Not folded: no verb writes either form, both rewrite ledger text in every tree, and T2 rests on a reading. Act 4 stands as approved.

The question: which did your note mean? Recommended: (a), as T2, 35 B an entry over the ticked form, the count kept in sight. Or T1 as ticked. Or (b), a separate design.

## 8. Not here; the refuter's round

Not here: R5 to R8, tokens, thresholds, `advice`, `suite.json`, a `make status` line, section 7's fold. The owner's yes of 2026-11-09 to the three open choices changes only later packets; there `make status` prints one advice line, read from `analyze --json`.

The refuter's F1 to F4 are folded here and in the packet; F5 (S3) and F6 to F8 (S4) are NICE rows the packet files.
