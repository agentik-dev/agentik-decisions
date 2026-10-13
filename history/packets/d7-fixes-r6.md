# Packet d7-fixes-r6: the r6 and ADV6 fixes, six acts, one builder

| item | value |
|---|---|
| from | `design/review-adv6.md` and `design/review-r6.md` (whole); example-mac `history/relay/2026-09-23-defects.md` D2 items 1, 4, 8; `design/decisions-r1.md` §3.2, §3.3, §4.4, §5 by `sed -n`; the standing word (decide inside the design, record, one open fork at most) |
| pin | `main` 0756c03 or later; branch `d7-fixes-r6`, worktree `.claude/worktrees/d7-fixes-r6` |
| wall | this repo. No push, `--amend`, rebase, device; never `make readme` or `claude plugin validate` by hand; every temp path from `mktemp -d`; outside the repo read only D2 |
| may touch | `src/decisions/*.py` (`against.py` new), `tests/*.py` except `test_hygiene.py` and `test_doclint.py` (`hermetic.py`, `test_hermetic.py`, `test_against.py` new), `plugin/scripts/*.sh`, `Makefile`, `design/decisions-r1-changelog.md` (three rows), `history/sittings/*.md`. Never: `decisions/`, `design/readme/`, `README.md`, `scripts/`, the rest of `plugin/`, `pyproject.toml`, `.hygiene-allow` |
| acceptance | repo root, virtualenv, `P="PYTHONPATH=src python3"`; baseline on `main` in parentheses: `$P -m unittest tests.test_hermetic tests.test_against -q 2>&1 \| tail -1` reads `OK` (`FAILED`); `$P -m unittest tests.test_writing tests.test_check tests.test_plugin -q 2>&1 \| tail -1` reads `OK` (`OK`); `grep -c 'CheckThisRepo\|test_this_repo' tests/test_check.py tests/test_index_render.py \| grep -vc ':0$'` reads 0 (2); `T=$(mktemp -d); git init -q $T; cp -r tests/fixtures/sample/decisions $T/; git -C $T add -A; git -C $T -c user.name=t -c user.email=t@t commit -qm base; sed -i '' 's/^status: proposed/status: in-force/' $T/decisions/0001-*.md; $P -m decisions --dir $T check --against HEAD; echo $?` reads 1 with a `status changed since HEAD` line (2); `PATH=/nonexistent /bin/sh plugin/scripts/test-deny-rule.sh; echo $?` reads 0 (1); `grep -c python plugin/scripts/deny-rule.sh` reads 0 (1); `env -i PATH=/usr/bin:/bin HOME=$HOME make validate 2>&1 \| grep -c 'validate: unrun'` reads 1 (0); `RESPEAK_DEPTH=1 RESPEAK_ROOT=/nonexistent make readme 2>&1 \| grep -c 'RESPEAK_DEPTH is set'` reads 1 (0); `grep -cE '^\| (d7\|D15\|r1 frozen) \|' design/decisions-r1-changelog.md` reads 3 (0); `git status --short \| wc -l` reads 0 (0). The verify line is `make check`, exit 0 at every commit and at close, never an acceptance line |
| budget | 120 turns (six acts; act 0 touches eight test files), 150k context; ONE commit per act, the charter in the last or its own; the charter names doclint's five rows at open; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

ADV6-1: "Nothing compares a record with its committed past. Fix: `check --against <rev>`". The verdict: "an unattended builder can manufacture an `in-force` ruling that every gate accepts." ADV6-2: "a typed confirmation of the id on a TTY". r6 §3 edge 1: "`timeout 60` on both, one message when `claude` is absent".

## 2. Rulings

Order fixed; each act's reproducing test lands in its commit, red before, green after.

- Act 0 (ADV6-4, r6's `test_this_repo`): `tests/hermetic.py` holds `Hermetic(unittest.TestCase)`; every class calling `decisions.main` inherits it. `CheckThisRepo` and `test_this_repo` are deleted. `tests/test_hermetic.py`: `NoLiveState` (ADV6's third test over a temp sample) and `GuardFires` (opening `<repo>/decisions/config` inside a Hermetic test raises).
- Act 1 (ADV6-1, D2 item 1): `check --against REV`, a new module. Decided: on a branch NO status may change and no non-`proposed` record may change in any byte; on `main` (`--ruling`) the exact deltas of `rule` and `supersede` pass, with the body identical to REV, because the owner rules on committed words. A record absent at REV is `proposed`. An empty or unresolvable REV is exit 2 before any lint.
- Act 2 (ADV6-2's tool half, ADV6-7): `rule` keeps the `CLAUDECODE` refusal, then refuses when stdin is not a TTY, then asks for the id typed back; nothing is written before the match. `rule` on `in-force` and `lint_body` past `proposed` refuse the Decisions and Record placeholders as they refuse the Words one. Tests patch `decisions.writing.sys.stdin` with a TTY-shaped StringIO.
- Act 3 (ADV6-2's hook half, ADV6-3, r6 edge 3): `deny-rule.sh` is POSIX sh, `cat`, `tr`, `sed`, `grep -E`, no interpreter; unreadable input exits 2. Decided: no quote stripping, so ADV6-10's false positive stays (a tokenizer needs the interpreter that fails open). `hooks.json` unchanged.
- Act 4 (ADV6-6, r6 edges 1 and 2, §6 (3) and (4)): `git_top` and `doctor` run their subprocess with `timeout=10` (`PYENV_TIMEOUT`, a constant the test lowers); git's timeout is a Refusal, pyenv's a `warn`. Makefile: `validate` is `unrun` (exit 2) without `claude` and each start runs under `perl -e 'alarm 60; exec @ARGV'`; `readme` refuses under `RESPEAK_DEPTH` and exports it; `venv` writes no `.pth` and installs pyflakes; `doctor` sets `PYTHONPATH=src`; `PY` resolves once (`:=` under `ifndef PY`).
- Act 5 (R6-10, R6-17, r6 §2): three change-log rows (§3). Nothing in `design/decisions-r1.md` moves.

Deferred, decided: ADV6-5 with the example-app conversion; ADV6-8 (a lock in `new`; the relay gate measuring the merged branch), ADV6-9 (temp plus `os.replace`, rollback) and ADV6-11 (hygiene `home` over `design/`) to the next packet, d8. `design/readme/source.md` is not edited; its `--against` sentence and suite count wait for the owner's next render. An unexplained red `make check`: commit nothing for that act, record it in the charter as the one open fork, stop.

## 3. Interfaces (signatures, not prose)

- `tests/hermetic.py`: `REPO`; `Hermetic.setUp` patches `os.environ` (clear) to `HOME=<tmp>/home`, `XDG_STATE_HOME=<tmp>/state`, the caller's `PATH`, and patches `io.open` and `builtins.open` with a guard raising `AssertionError` for any path under `REPO/decisions/`.
- `src/decisions/against.py` (under 200 lines): `lint_against(root, rev, ruling, items) -> [(relpath, finding)]`, git by `subprocess.run(..., cwd=root, timeout=30)`; a REV that fails `rev-parse --verify` is a Refusal. Findings begin `status changed since REV`, `body changed since REV`, `<field> changed since REV`, `removed since REV`, `born <status>`. Under `ruling` only: `status` by `TRANSITIONS` or in-force to superseded, `date` on in-force, and the two link fields as `supersede` writes them, symmetric. `cli.py`: `check [--against REV] [--ruling]`, `--ruling` alone exit 2.
- `Makefile`: `AGAINST ?= $(shell git merge-base main HEAD 2>/dev/null || git rev-parse HEAD 2>/dev/null)`; `RULING := $(if $(filter main,$(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)),--ruling,)`; `decisions:` runs `check --against "$(AGAINST)" $(RULING)` then `index --check`; `validate:` prints `validate: unrun, no claude on PATH` and exits 2 when `command -v claude` fails.
- `writing.py`: `confirm(ident, err, stdin=None)`; not `isatty()` is a Refusal; the prompt `rule: type %s to confirm: ` goes to `err`; a mismatch is a Refusal. Called after the transition and link checks, before the first `write_text`.
- `deny-rule.sh` and `test-deny-rule.sh` both set `PATH=/usr/bin:/bin` on line 2. Deny (2, the reason unchanged) ADV6-2's three repro lines plus the `python3 -m decisions rule`, `python3 src/decisions.py rule` and `cd x && decisions rule` forms; pass (0, silent) `show`, `scope`, `git log --grep rule`; unreadable (2, `deny-rule: cannot read tool_input.command`) empty stdin, no `command` key. The test runs them all and prints `test-deny-rule: ok (<n>)`. Write both scripts with the Write tool, never a heredoc (§4).
- Change-log rows: `D15` (`record` ships in claude-code-session as `scripts/record`, cited by name here; §3.6); `r1 frozen` (the body of decisions-r1 is never edited after r1, every change a row here, the r2 fold its own bounded round); `d7` (this packet's acts and the run-5 acceptance rule).

## 4. Findings that name this row

On `main` 0756c03: `make check` 0; `import pyflakes` fails (ADV6-5a); `timeout` is brew coreutils, `/usr/bin/perl` is Apple's 5.34; eight test files call `decisions.main`; the self-checks are `test_check.py:266` and `test_index_render.py:98`; `settings.py:84` and `doctor.py:47` have no timeout; `Makefile:32` `validate` is unbounded, `:45` `venv` writes the `.pth`; `deny-rule.sh:6` is `exec python3`; `env -i` still finds Apple's python3, so ADV6-3 needs `PATH=/nonexistent`. The installed hook denied this packet's own heredoc (ADV6-10 live); the Write tool wrote it.

## 5. Forbidden reads

The moved ledger and reference trees; `decisions/` whole; `design/decisions-r1.md` beyond the four sections; the refuters and packets d-split to d6; `../example-mac/history/relay/` beyond D2; the session, respeak, agent-relay and example-ops repos; any file over 8 KB whole except the two reviews and the `Makefile`.

## 6. Report (one table, four bullets, under 1,000 words)

The table: each acceptance line, its exit and last output line on the branch. Bullets: the findings carried and the ones deferred to d8; choices §2 does not name; what was left undone; the one open fork, if any. The last line: the branch name and its head sha.
