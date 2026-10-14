# review-r6: the design decisions of claude-code-decisions since 2026-09-22 (2026-09-23)

By the Fable reviewer of relay row review-6-decisions at `main` 0cde5c1, from the defect brief (example-mac `history/relay/2026-09-23-defects.md` D1 to D7), the handovers 2026-09-22-1 to 2026-09-23-4, the eight packets d-split to d6-resync, `decisions-r1.md`, its change-log and `ledger-conversion-r1.md`. Nothing built or fixed. Consumers: the owner; the next packet-writing sitting; the r2 fold.

## 1. Decisions ledger

"Record": in the design of record (decisions-r1 or its change-log). "Charter": only in a handover, the section it belongs in named.

- R6-1 The four §7 decisions ruled as `decisions/0001` (change-log, ruled). Record.
- R6-2 Ruling C: the package `src/decisions/`, 7 modules under 333 lines, a 12-line runner (d-split). Record. `__init__` re-exports by a loop for pyflakes (charter 22-5): §3.1.
- R6-3 D14: `reference/` and `research/` to example-ops, pins unchanged; 29 ledger tests skip without `DECISIONS_LEGACY_REFERENCE` (d0-leave). Record; the five tests beyond the packet's 24 (charter 22-6): §5.
- R6-4 The python ruling: pyenv 3.12.7 via `.python-version`, `#!/usr/bin/env python3`, 3.12+, 0.2.0 (d1). Change-log row only; §3.1 and §5 still say Apple 3.9.
- R6-5 The settings resolver (seven layers) and `doctor` (d1). Change-log only; the resolved.json shape is assumed (charter 22-7): §2.5, §3.3.
- R6-6 `make check` = gates, test, lint, doclint, hygiene, validate, decisions, README freshness (d1, d4). Change-log; §5 lists r1's gate.
- R6-7 D11: `make marketplace` the per-repo default, unrun (d1). Change-log; §4.1.
- R6-8 README rendered from `design/readme/source.md` by respeak through `make readme` (`claude -p`, two rounds, three runs a row), never by hand; render notes in the source (d2, charter 22-8b). Change-log; needs a §4.5.
- R6-9 CLAUDE.md cites record lines; the README names no private repo; a per-file hygiene allowlist (d0, d2). Record.
- R6-10 D15: `record` ships in the session, cited by name here (d2 §2). Charter only: §3.6.
- R6-11 `convert --from-legacy` under (A) and (B): `--out` only, Words the whole entry, `--ids`/`--status`, an unmapped cell stops the run, the §7 scope rule (d3, charter 22-9). Record. Built while `parked`: the relay ignored the flag; the owner merged it (a4674c8).
- R6-12 README freshness by the sidecar `rendered.sha256`, not mtime (d4 item 24, closing charter 22-8's fresh-clone defect). Record.
- R6-13 The two canonical scripts byte-identical, sha-pinned in `hygiene`, re-synced by a packet each time the session moves (d4, d5, d6); their tests ride since d6, reversing d5. Record; conventions §6 (session) names scripts only.
- R6-14 MIT, byte-identical to respeak's; pyproject's license waits for go-public (d4). Record.
- R6-15 The synthetic legacy fixture with ungated twins (d4 item 31). Record.
- R6-16 The README source says 222 tests, the suite is 229; the line waits for a render (charters 23-3, 23-4). Charter only: a defect, §2 below.
- R6-17 Design records are never edited after r1; every change is a change-log row (d1 §2, applied since). Nowhere written: decisions-r1's head or the conventions.

The tally, reconciled 2026-10-14 (a research fix): five entries are change-log only (R6-4 to R6-8), two are charter only (R6-10, R6-16), one is written nowhere (R6-17), and nine are in the record. The handover of `history/sittings/2026-09-23-5.md` says seven and three; the tags above are the count that stands.

## 2. Reversals and tensions

- Interpreter: §3.1 and §5 (Apple 3.9) and the global CLAUDE.md ("never env python3") against the ruling of 12:55. The ruling wins; the record body and the global line yield (the example-mac reconcile is deferred).
- The deny hook runs `exec python3` from PATH: the wrong python under the global rule, any python under the ruling. It needs none (§3, item 3).
- Acceptance: all eight packets carry `make check` as an acceptance line; the run-5 rule (D1) refuses it. Landed rows stand; later packets name targeted lines and keep `make check` as the verify line.
- d5 left the tests untouched; d6 copied them on a measurement. d6 wins; conventions §6 should name four files.
- The sidecar makes the source un-editable without a model spend, so a count in it (R6-16) is a standing red. The source should carry no number a gate changes.

## 3. Fork-storm class

No closed cycle exists here: nothing under this tree runs the relay, `make`, or a `claude` session that can run `make`. The class is present as four open edges.

1. `make check` → `validate` → `claude plugin validate`, twice. Cycle: none. Bound: NONE (no timeout; a node start is seconds idle, minutes under load). Fix: `timeout 60` on both, one message when `claude` is absent.
2. `make readme` → `respeak-render.sh` → `claude -p`: a session inside a session, two rounds, three runs a row. Cycle: closes only if the respeak agent had Bash and ran `make readme`; it has Read, Grep, Glob, Write. Bound: that tool set and `--max-rounds 2`; not in `check`. Fix: the target sets `RESPEAK_DEPTH` and refuses when it is set; never an acceptance line.
3. The PreToolUse hook → `python3` through the pyenv shim, `timeout: 10`. Cycle: none. Bound: 10 s, after which the hook FAILS OPEN (a timed-out hook does not block; Anthropic's Hooks reference, <https://code.claude.com/docs/en/hooks>, read 2026-10-14, confirms it: a timed-out `command`, `http` or `mcp_tool` hook doesn't block the tool call, `"onFailure": "block"` on a `command` or `http` hook reverses it from Claude Code 2.1.295, and command hooks default to 600 s); the `CLAUDECODE` tripwire in `rule` is the layer that holds under load (tests/test_writing.py:399). Fix: a pure `/bin/sh` hook with `grep -E`, no interpreter start.
4. `make check` as acceptance on every packet: a relay baseline runs 229 tests and two `claude` starts per row per plan. Cycle: none here (D5's closes in agent-relay). Bound: the relay's 900 s a line; NONE in this repo. Fix: targeted lines; `check` measured at close (the charter).

Also: `tests/test_index_render.py` `test_this_repo` runs `index --check` on the live checkout (D7's class): a record added without a render turns the unit suite red, not only the gate; fix, a fixture. `make` never calls `make`; no git hook is installed (§5's pre-push was never built; the 05:53 ruling (4) settled no hooks shim); `doctor` runs `pyenv install --list` without a timeout, outside `check`.

## 4. Timing and edge conditions

- No `subprocess.run` in the tool or scripts has a timeout: `git rev-parse` on every invocation (settings), `git ls-files` (doclint, hygiene), `pyenv` (doctor). Invariant: a read never blocks past 30 s, then refuses. No test.
- `PY ?= python3` goes through the pyenv shim seven times per `check`; under the storm shells waited 60 s on the rehash lock. Invariant: `check` under 60 s idle. No test; `PY := $(shell pyenv which python3)` resolves once.
- `make venv` writes one `.pth` naming one checkout's `src`; a second worktree's `python3 -m decisions` imports the first tree (charter 22-8): a wrong pass. `test` and `decisions` are safe (PYTHONPATH, the runner); `doctor` is not. Invariant: every gate line imports the tree it runs in. No test.
- `new` lists the directory for the next id and writes without an exclusive create; `index` writes INDEX.md in place. Two runs in one tree can duplicate an id or race `--check` against a half-written file. Invariant: ids unique (caught later by `check`); temp plus `os.replace`. No race test.
- Two branches that both edit the README source hand-merge README.md and the sidecar, breaking "never by hand". Invariant: rows that edit the source chain. No test.
- `validate` needs `claude` on PATH: without it `check` is red on main and branch alike and a relay gate passes the row as same-as-main (D4's class). Invariant: an environmental red is `unrun`, never a baseline (AR10); here, a distinct message.
- The hook's regex misses `$D rule`; the tripwire catches it unless the shell drops `CLAUDECODE`. Two layers stay; a test with the hook absent exists.
- Fixed temp paths (`/tmp/d4.log`, `/tmp/d5.log`, `/tmp/d6.log`, `/tmp/d-split`) in every packet's acceptance: parallel rows and sessions share them. Measured at close: this review's `make check > /tmp/r6-check.log` interleaved with another row's live `make check` on the same path. Invariant: every temp path is `mktemp`. No test.

## 5. TLA+

No protocol here deserves a model. The status machine is four states, two links and one cascade, driven serially by the owner's hand; a randomized test over sequences of `new`, `supersede`, `rule` asserting link symmetry and status agreement covers it.

## 6. Decisions for the owner

1. An r2 fold of decisions-r1: §3.1, §4.1 and §5 read r1 (Apple 3.9, a pre-push hook, no marketplace target) while eight change-log rows and the packets hold the truth (R6-4 to R6-8, R6-17). Recommend one bounded round folding the rows in-line before the example-app-init sitting. Consumer: that packet's `from` row.
2. The README source carries no count a gate changes (R6-16). Recommend the sentence say the suite runs under unittest, fixed at the next render. Consumer: the next `make readme`.
3. Drop the shared virtualenv's `.pth`; every `-m decisions` line sets PYTHONPATH=src; the installed tool comes from `uv tool install` only. Mac state, so yours. Consumer: the next worktree builder; the example-mac freeze.
4. Keep `claude` required in the gate, with `timeout 60` and a "no claude" message the relay classifies as unrun. Consumer: the relay's gate; conventions §5.
5. Adopt the run-5 acceptance rule here (targeted lines, `make check` as verify only) and rewrite the hook in sh. Consumer: the next packet-writing sitting.
