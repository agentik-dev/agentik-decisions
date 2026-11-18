# Packet rr4: decisions finds a repo's records through the resolver

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-18, brief rr4; hq design/28 (the records root) §1, §2 item 5, §3 items 2 to 5, 12 and 18, §11 lead 8; commons GUIDE §12. Level S3 |
| pin | main at `ff549b6` (0.23.9). Version 0.23.10. Worktree `.claude/worktrees/rr4-decisions-records`, branch `rr4-decisions-records`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state, the live home, the user's git config or a real repo's |
| may touch | what commons' `scripts/sync` places (`plugin/lib/agentik_records.py`, `scripts/hygiene`, `scripts/vendored.sha256`), unedited; `plugin/lib/decisions/{common,ask,answer,selector,render,ledger,questions_read,backlog,expire,rows,analyze,cli}.py`; `tests/test_rr4_records.py` (new); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib:. python -m unittest tests.test_rr4_records` |
| budget | about 90 tool calls |

## 1. What the source says

A public repo's working records live outside its clone. One key in the clone's own git config, `agentik.records`, names the folder; commons' resolver answers `own`, `out`, `unset` or `broken` for any folder. Every default that is a record's path comes from the resolver; an explicit flag still wins. A record of a repo in state `out` is not versioned with the code: no tool reads one at a commit of the code repo; where history is wanted (`analyze`), it is `git -C <holder>` over `<prefix>/<path>`.

## 2. Rulings

- D1, the sync: commons' `scripts/sync` from commons main `ca83060`, a commit of its own after this packet; nothing synced is edited.
- D2, one read: `common.records_of(folder, verb, write)` calls `agentik_records.resolve` once per repo per call (a cache the CLI's `main` empties). `own` gives back the caller's folder, byte for byte today's; a folder in no git checkout is `own`. `out`: the key's folder. `unset`: a read gets None (no record), a write refuses naming the key. `broken`: every read and write refuses with one line, the key, its values and the reason, exit 2.
- D3, the paths: under the resolved folder, `OPEN-QUESTIONS.md` and `.new.lock` (the ledger stays in the repo; with `--ledger` the repo is the ledger's git top); `NICE_TO_HAVE.md`, `HANDOFF.md`, the done file and the NICE overflow for `backlog`, `expire`, `questions` and each REPO; `rows`' default root `history/rows`, its `HANDOFF.md` and done file. `--ledger`, `--into`, `--root` and `--order` win as today; `backlog --check` reads beside its `--order` FILE as today.
- D4, git: `analyze`'s snapshots of the wish list and its overflow run `git -C <holder>` over `<prefix>/<path>` at the holder's first-parent commits, and none with no holder (one `not measured:` line); its output says once that the records are dated by the holder's commits. `rows`, for a row whose repo is `out`, reads the newest charter in that repo's records named for the row, not the branch tip's.
- D5, no commit: decisions commits nothing.
- D6, the words: the help where a default path is named, the README source, the version 0.23.10.

## 3. Interfaces: the acceptance table (each a case in `tests/test_rr4_records.py`)

Baseline at the pin: the module's cases fail (no verb reads the key; the questions file sits beside the ledger); every other test passes.

| # | case |
|---|---|
| 1 | `ask` then `answer` in `out` write and read `OPEN-QUESTIONS.md` and the lock under the records; the ledger stays in the clone; `unset` refuses naming the key; `broken` refuses with the key, value and reason, exit 2; `own` as today |
| 2 | `questions` reads the records' file in `out`, skips as "no OPEN-QUESTIONS.md" in `unset`, refuses in `broken` |
| 3 | `backlog` and `expire` read the records' `NICE_TO_HAVE.md` and `HANDOFF.md`; `expire --write` moves into the records' overflow; `unset` reads none, its write refuses; `broken` refuses |
| 4 | `rows` reads `history/rows` under the records in `out`; `unset` and `broken` refuse; `--root` wins in `out` |
| 5 | `analyze` in `out` with a holder snapshots the holder's commits and says so once; with no holder, one `not measured:` line |
| 6 | an explicit `--ledger` and `--order` win in `out` |

## 4. Findings that name this row: where the brief and the code part

- `render`'s write and `ledger`'s lint (L3) also read the questions file and lock beside the ledger; they follow the same function, so the ledger's lint and `ask` agree on one file.
- `expire --write` checks that HEAD holds `NICE_TO_HAVE.md`; in `out` that HEAD is the holder's, and with no holder the write refuses as an uncommitted file does today.
- Review 1's fix (each a case in `tests/test_rr4_fix1.py`). C1: the resolver runs in a child of its own session under `GIT_TIMEOUT`, so a hung git is one refusal line and dies with the call; the synced module is unedited. C2: where the resolver cannot answer and a `.git` lies above, a write refuses and a read finds no record; with none above, or with no git on PATH, the folder reads as `own`, so `ask` and `answer` run with no git as d41 and d42 made them. C3: in `out`, `rows` takes the newest charter whose chain goes with the row: no chain, the row's name, or its head before a `-`. C4: a REPO in `out` is keyed by its records folder and read at its git top.

## 5. Forbidden reads

A relay ledger, a reference snapshot, live state, the live home, the user's git config.

## 6. Report

The coordinator's record, one table of the acceptance lines, the gate's job.
