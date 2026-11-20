# Packet bk1: `backlog`, `questions` and `expire` resolve their repos at once, and one `rows` read asks git each question once

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-20, brief bk1-reads-fit: an advisor's pick 1 from a read of the suite for design defects. Level S3 |
| pin | main at `7cdbc20` (0.23.12). Version 0.23.13. Worktree `.claude/worktrees/bk1-reads-fit`, branch `bk1-reads-fit`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state, the live home, the user's git config or a real repo's |
| may touch | `plugin/lib/decisions/{common,backlog,questions_read,expire,rows}.py`; `tests/test_bk1_reads_fit.py` (new); the version places (`plugin/.claude-plugin/plugin.json`, `common.py`, `pyproject.toml`, `tests/test_plugin.py`, `README.md`, `design/readme/{source.md,rendered.sha256}`); this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib:. python -m unittest tests.test_bk1_reads_fit` |
| budget | about 90 tool calls |

## 1. What the source says

The owner, 2026-11-20: "Put a new Fable advisor to look for design defects in our suite. Look for the best 3 things to do for our repos and then farm them out to Opus workers when it comes back with a decision." This row is the advisor's pick 1. Measured by the coordinator at the pin: `backlog --json --order HANDOFF.md` over eleven checkouts took 1.1 s, past the 1.0 s wall the suite's status screen gives it, because `_resolved` starts one bounded resolver child a key and `backlog` calls it per repo in turn; one `rows` read ran 525 git calls for 35 rows, 250 of them exact repeats.

D1, the children start at once: `common.records_prime(folders)` starts every key's child together, collects them under one `GIT_TIMEOUT` and fills the cache `_resolved` reads. D2, one `rows` read asks git each question once: a memo of read-only git calls keyed by argv and cwd lives for one `rows.read`. Not an architecture change: one tool, no new seam, no JSON shape changed.

## 2. Rulings

- R1, the prime. `records_prime(folders)` maps each folder to its realpath key, and for every key not yet cached starts `_resolved`'s argv at once, each child its own session as `bounded` makes it. It collects them all under one `GIT_TIMEOUT` from the first start and caches exactly what `_resolved` answers: the answer and values; `{"state": "timeout", "repo": key}` for a child still running at the wall, killed with its group; `nogit` and None by the same tests. A key primed is not resolved again in the process; a key never primed resolves as at the pin. With no git on PATH it does nothing.
- R2, its callers. `backlog`, `questions` and `expire` call it once with all their REPO arguments before their loops. No other verb changes; every output, text and JSON, is the pin's byte for byte.
- R3, the memo. `rows.read` runs under a memo of read-only git calls keyed by (argv, cwd), entered and left by `read` itself; `rows close`, `check`'s writes and every other verb run git as at the pin. A failure or a timeout is memoized as itself for that read alone.
- R4, the version: 0.23.13, alone in the branch's last commit under `plugin/`.
- R5, what stands: `plugin/lib/agentik_records.py` and every vendored file; the child's text, its isolation, its `timeout` and `nogit` answers; every JSON shape; `describe`'s reads and walls.

## 3. Interfaces: the acceptance table (each a case in `tests/test_bk1_reads_fit.py` unless it says otherwise)

Baseline at the pin: cases 1 to 4 fail (the six slow children run in turn, about 2.3 s; no `records_prime`; a `rows` read repeats git calls); case 5 passes, as a guard. Case 6 at the pin, over eleven made-up checkouts and a HANDOFF.md under a temp home: 0.67 to 0.75 s, three runs.

| # | case |
|---|---|
| 1 | with `_CHILD` sleeping 0.3 s first, `backlog --json` over six repos returns in under 1.0 s and its JSON is the unpatched run's |
| 2 | one of six children hangs past a lowered `GIT_TIMEOUT`: that repo reads `timeout`, the five others as unpatched, and no child is left |
| 3 | `questions` and `expire` over three repos start every child before the first is collected, and print what an unprimed run prints |
| 4 | a spy on the bounded call through one `rows --json` over rows in two repos: no (argv, cwd) pair runs twice; the JSON is the unmemoized run's |
| 5 | `rows close --dry-run` after a `rows` read in one process runs its git fresh: no memo outside `read` |
| 6 | by hand: the time of `backlog --json --order HANDOFF.md` over eleven checkouts, at the pin and now |
| 7 | the gate queue's `make check` |

## 4. Findings that name this row: where the brief and the code part

- `_resolved`'s timeout answer is `{"state": "timeout", "repo": key}`, not the brief's bare `{"state": "timeout"}`; the prime caches the code's answer, as R1's "exactly what `_resolved` would have answered" says.

## 5. Forbidden reads

A relay ledger, a reference snapshot, live state, the live home, the user's git config.

## 6. Report

The coordinator's record, one table of the acceptance lines, the gate's job.
