# Packet d39: `backlog --check`, the state cell held against git

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief d39 (hq `history/sessions/BRIEF-2026-11-12-decisions-d39-backlog-check.md`); design of record hq design/14 §3.2, §3.3, §4 item 1, §5. A packet: it adds a flag |
| pin | main at `9dd7af4` (0.21.6, d38's merge). Version 0.21.7, 0.21.8 after r1, 0.21.9 after r2. Worktree `.claude/worktrees/d39-backlog-check`, branch `d39-backlog-check`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state, a real HANDOFF or a real repo, or writes outside its temp home |
| may touch | `plugin/lib/decisions/backlog.py`, `cli.py` (the two flags and the usage lines), `render.py` (R7, `_gate_line` only); `tests/test_d39_backlog_check.py` (new); `plugin/skills/decisions/SKILL.md`, `plugin/commands/backlog.md`; the four version places, `tests/test_plugin.py`, `README.md` and `design/readme/{source.md,rendered.sha256}`; this packet and the sitting's record |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib:. python -m unittest tests.test_d39_backlog_check` green (at the pin: every case red, `--check` unknown) |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

- `build_order` (`backlog.py:246`) reads a HANDOFF table's rows; a row's `done` is its last cell opening `done`, and nothing else of the cell is read. `cmd_backlog` (`:405`) reads two files, writes nothing and exits 0 or 2; it refuses a REPO that is not a directory.
- `_gate_line` (`render.py:107`) places a target by its real path first since d38 r1, so `<config dir>/CLAUDE.md` linked into a checkout goes to that checkout's list.
- The owner's words: none new; design/14 §6 asks nothing, its choices are logged in its §7.

## 2. Rulings: the requirements

- R1, the reference: a `waiting:` cell's first words are `owner <n>`, `row <n>`, `the owner: <text>` (tried first), else `<repo> <branch>` with `<repo>` a name of the table's repo column; free text may follow after `;`. `building <row>` names a branch, `building <repo> <branch>` another repo's. `done <date> <sha>` and `watch:` as today. `--json` carries it; the text view is unchanged.
- R2, `backlog --check --order FILE [REPO...]`: REPOs as `--order` takes them; with none, only the `hq` and `suite` rows. A REPO with no `NICE_TO_HAVE.md` is checked. A row whose repo is not named or absent is skipped and named on one line, never red.
- R3, the reds, each in the row's repo (`hq` and `suite` rows in FILE's own checkout): `building <row>`: `stale: landed <sha> <date>` when a merge on main's first-parent line opens `merge <row>` or `Merge <row>` with the whole name, or its second parent is the branch's tip; else `stale: branch gone` when the branch is absent. `done <date> <sha>`: red when the sha is not a merge on main's first-parent line (for an `hq` row a plain commit counts). `waiting: owner <n>`: `answered` when `n` is under `## Answered` of the `OPEN-QUESTIONS.md` beside FILE. `waiting: row <n>`: `resolved` when `n` is not in the table. `waiting: <repo> <branch>`: as a `building` cell in that repo. `the owner:` and `watch:` are never red.
- R4: exit 1 on any stale cell, 0 on none, 2 usage. One line a red: number, the cell's first words, the red. `--json` the same per row, skipped rows included.
- R5, `--check --write`: a `stale: landed` `building` row becomes `done <date> <sha>`, its line is appended to `history/handoff-done.md` beside FILE in the shape of that file's last line, and the row leaves the table whole; nothing else changes, and nothing is written with no such row. `--write` alone exits 2.
- R6: no gate ledger, no relay state, no network; git only as `git -C <repo>`, read-only.
- R7: `_gate_line` tests the owner's folders on the spelled path before the real-path checkout lookup.

## 3. Interfaces: the acceptance table (the brief's eight; each a case in `tests/test_d39_backlog_check.py` but 8)

| # | line | at the pin |
|---|---|---|
| 1 | each red of R3, and the clean cell beside it, in a temp repo with a temp HANDOFF | red (`--check` unknown, exit 2) |
| 2 | `g2` against a merge of `g2b-edit-gates`: not landed; an otherwise-worded merge of the branch's tip: landed; a deleted branch after an unnamed merge: `stale: branch gone` | red |
| 3 | a row whose repo is absent: skipped, named, exit 0; no REPO: only `hq` and `suite` rows | red |
| 4 | `--check --write`, one landed and one clean row: the landed row leaves, its line is the done file's last, every other byte stays; a second run writes nothing, exit 0 | red |
| 5 | `--check` alone leaves both files byte for byte; `--write` alone exits 2 | red |
| 6 | `--json` parses and carries each row's reference and red | red |
| 7 | R7: `<config dir>/CLAUDE.md` a link into a checkout: the owner's list gains it once, the checkout's nothing | red |
| 8 | `tests/test_backlog.py` green; `backlog .` and `backlog --order` text as at the pin over the fixtures | green |

## 4. Findings that name this row: ledger, NICE, forks

- hq entries 17 and 25 and design/14 §7 bind it; R7 is d38's round-2 note (hq `REFUTE-2026-11-12-d38-r2.md`).

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real HANDOFF.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
