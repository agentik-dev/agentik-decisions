# Packet d43: `backlog --check` reads a branch built on since its merge as live

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief d43 (hq `history/sessions/BRIEF-2026-11-12-decisions-d43-backlog-built-on.md`), NICE n85 S3, n86 S4; d42's review r1 (R1-F1, R1-F2) filed here |
| pin | main at `01b41e3` (0.21.13, d42's merge; the brief's `00449d5` moved on). Version 0.21.14. Worktree `.claude/worktrees/d43-backlog-built-on`, branch `d43-backlog-built-on`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state, a real HANDOFF or a real repo |
| may touch | `plugin/lib/decisions/backlog.py` (`reference`, `building_red`, `checked`, `cmd_check`); `tests/test_d43_backlog_built_on.py` (new), `tests/test_d39_backlog_check.py` (one case's REPO list, R2); `plugin/commands/backlog.md`; `NICE_TO_HAVE.md` (n85, n86 leave; d42 R1-F1, R1-F2 filed); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib:. python -m unittest tests.test_d43_backlog_built_on tests.test_d39_backlog_check` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words: none new. hq design/14 §5: a landing is `gate land`'s `--no-ff` merge, and what git cannot prove "reads as `building` until typed `done`".

The fault, measured at `01b41e3` with this packet's tests: `building_red` takes the newest merge on main's first-parent line whose subject opens `Merge <branch>` and never asks where the branch stands. A branch merged once by name and then built on reads `stale: landed`, and `--check --write` moves the live row to the done file; a branch deleted at its landing and cut again from main reads the same, with a commit of its own or none. `reference` takes a `<repo>` only from the table's repo column, so `waiting: quince q1` with `quince` named on the command line is no reference, and `building quince q1` reads `quince` as the branch: `stale: branch gone`. A `waiting:` cell of no known form is `"on": null` in `--json` and nothing in the text view.

## 2. Rulings

- R1, landed (`building_red`): a merge named for the branch counts only when the branch is gone, or its tip is the merge's second parent or an ancestor of it (`git merge-base --is-ancestor <tip> <merge>^2`, a read). Each named merge on the line is tried, newest first. The unnamed merge whose second parent is the tip counts as at the pin.
- R2, a repo's name (`reference`, `checked`): `<repo>` in `waiting: <repo> <branch>` and `building <repo> <branch>` is a name of the table's repo column or the short name of a REPO named on the command line that is a checkout.
- R3, the unread cell (`cmd_check`): a `waiting:` cell that is none of d39 R1's four forms is named on one line of the text view, never red and no part of the stale count: `unread (waiting names no owner, row or repo): <n>, ...`. `--json` keeps `"on": null`.
- Decided in the brief: a fast-forward and a squash stay unread as landings; `plugin/commands/backlog.md` says so in one sentence. n85 and n86 leave `NICE_TO_HAVE.md`.

## 3. Interfaces: the acceptance table (each a case in `tests/test_d43_backlog_built_on.py`)

| # | line | at the pin |
|---|---|---|
| 1 | merged by name, then a commit on the branch: `building more1` clean; `--check --write` writes neither file | red: `stale: landed`, the row moved |
| 2 | merged by name, deleted, cut again from main, with a commit and with none: clean | red: `stale: landed` both |
| 3 | merged by name at its tip, behind it, or gone: `stale: landed <sha> <date>` of the newest such merge | green |
| 4 | `waiting: quince q1`, `building quince q1` in `suite` rows, `quince` named and in no repo cell: both `stale: landed` | red: no reference; `stale: branch gone` |
| 5 | `waiting: plum p1`: the `unread` line names the row, exit 0; `--json` `"on": null` | red: no line |
| 6 | a fast-forwarded branch and a squashed one: clean | green |
| 7 | `tests/test_d39_backlog_check.py` green; a table with no unread cell prints what it printed at the pin | green |
| 8 | `make check` green through the queue, once, last | |

## 4. Findings that name this row: ledger, NICE, forks

n85 and n86 leave. d42's review r1 leaves two NICE rows, filed here: R1-F1 (three sentences say `answer` or `ask` runs no git) and R1-F2 (`answer N --other` refused while another block fails the lint). No fork for the owner.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real HANDOFF.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
