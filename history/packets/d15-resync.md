# Packet d15-resync: the post-S15 re-sync of hygiene, doclint and bounded, the relay's harness list for this repo, and the README count; two acts, one builder

| item | value |
|---|---|
| from | the relay's packets-38 charter, item 4 (§1); its `HarnessOf` and gate overlay at its `main` 71aa3e8; rulings D2 and D4; change-log row d14 (ADV11-1); the session's `scripts/` and three tests at `S`; §4; the STANDING WORD |
| pin | `main` 4cca4c8 or later; branch `d15-resync`, worktree `.claude/worktrees/d15-resync`; the session's `main` with s15-resync merged, its sha `S` measured by the builder at start and written in its charter |
| wall | this repo. No push, `--amend`, rebase, device, `relay`; `make readme` exactly once, at close; never `make e2e`, `make tla`, or `claude plugin validate` by hand; never run the session's tests; copies come from `git -C <session> show S:<path>`, never its working tree (`<session>` is the session repo beside this repo's main checkout, `../claude-code-session` from the checkout's root); if `git -C <session> log --oneline main` names no s15-resync merge, commit nothing and stop; every temp path from `mktemp -d`, every log to a `mktemp` file |
| may touch | `scripts/hygiene`, `scripts/doclint`, `scripts/bounded`, `tests/test_hygiene.py`, `tests/test_doclint.py`, `tests/test_bounded.py`, `Makefile` (the two pins only), `design/decisions-r1-changelog.md` (ONE row), `design/packets/d13-resync.md`, `design/packets/d14-fixes-adv11.md` (each `git mv`'d unedited to the same name under `history/packets/`, only if the new doclint refuses it), `design/readme/source.md` (its status line), `README.md` and `design/readme/rendered.sha256` (by `make readme` only), `history/sittings/*.md`, `history/sessions/NEXT`. Never: `src/`, the other tests, `tests/skips.allow`, `plugin/`, `decisions/`, `design/decisions-r1.md`, `.hygiene-allow`, `.gitignore`, `scripts/readme-render` |
| verify | `make check`, exit 0 at every commit and at close, its log to a `mktemp` file, `readme: fresh` in it; never an acceptance line |
| acceptance | repo root, the pyenv virtualenv that `.python-version` names (`python3` resolves to it); baseline on `main` at this packet's commit in parentheses; a name s15 adds or retires moves an expected count, and the builder's report gives the measured value. Act 1: `grep -cE '^(HYGIENE\|DOCLINT)_SHA = (d63d0ffb\|d5957c6c)' Makefile` reads 0 (2); `grep -lE '^import pytest\|pytest\.' tests/test_doclint.py tests/test_bounded.py \| wc -l` reads 0 (0); `grep -cE 'def test_(suite_rule_fails_closed\|suite_rule_targeted_allowed\|next_names_a_missing_prompt)' tests/test_doclint.py` reads 3 (0); `grep -cE 'def test_(bounded_refuses_nonfinite\|nested_stop_line_is_not_the_gates\|no_survivor_check_greps_the_machine\|stop_line_names_the_reason\|stopped_guardian_does_not_leak_the_suite)' tests/test_bounded.py` reads 5 (0); `grep -c 'def test_hygiene_oversize_is_scanned' tests/test_hygiene.py` reads 1 (0); `env PYTHONPATH=src python3 tests/run.py test_bounded test_doclint test_hygiene 2>&1 \| grep -E '^(OK\|FAILED)'` reads `OK` (`OK`); `python3 scripts/doclint; echo $?` reads 0 (0); `make hygiene doclint; echo $?` reads 0 (0); `grep -cE '^\| d15 \|' design/decisions-r1-changelog.md` reads 1 (0); `grep -c 'harness: \[Makefile, scripts, tests/run.py, tests/gates.py, tests/skips.allow\]' design/decisions-r1-changelog.md` reads 1 (0). Act 2: `grep -c '353. unittest cases' README.md design/readme/source.md` reads 0 each (1 each); `shasum -a 256 -c --status design/readme/rendered.sha256; echo $?` reads 0 (0); `env PYTHONPATH=src python3 -m unittest tests.test_readme 2>&1 \| tail -1` reads `OK` (`OK`); `git status --short \| wc -l` reads 0 |
| budget | 60 turns, 150k context; TWO commits (act 1, act 2), the charter in the last; act 1 is ONE commit so neither `make hygiene` nor `make check` reads red at a commit; the charter names doclint's five rows at open; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

Conventions §6: every copy of `scripts/hygiene` and `scripts/doclint` has the session's sha256. packets-38 item 4: "The decisions queue names `harness: [Makefile, scripts, src/decisions, tests]`". The relay: `harness:` is "a flat list of repo-relative paths a branch may not use to judge itself"; the gate lays them over the branch's tree "as they are on main" and "the overlay deletes a branch's copy that main lacks"; a harness path guards "the path itself or anything under it". Change-log d14: `decisions`, `test` and `gates` run `src/decisions.py`, `src/decisions/` and `tests/{run.py,gates.py,skips.allow}` extracted at the base. The prompt: "No README act this round, unless your builder's change makes a README line false".

## 2. Rulings

Decided inside the design (the packet writer's; the builder records any further choice in the charter):

- Act 1, ONE commit. Take `scripts/hygiene`, `scripts/doclint`, `scripts/bounded` and `tests/test_hygiene.py` byte-identical from `S`; move `HYGIENE_SHA` and `DOCLINT_SHA`. The session's SPENT and its ADV11-15 hygiene arrive with the copies, unedited (§6).
- Port the session's `tests/test_doclint.py` and `tests/test_bounded.py` to `unittest`, as d13 did: a pytest-free class byte-for-byte; each module function a same-named method of a second `TestCase`; `parametrize` as `subTest` with its ids; `tmp_path` as `tempfile.TemporaryDirectory`; a header line names `S` and says it is a port. The port's names equal the session's, so the five `test_bounded` names it retired (§4) go here too. Rejected: pytest (the no-dependency invariant); keeping the S13 ports (4 fail under 2a1dfcb).
- The harness list (packets-38 item 4, inside D2), recorded in the change-log row for §5 at the next fold: the relay's queue for this repo names `harness: [Makefile, scripts, tests/run.py, tests/gates.py, tests/skips.allow]`. Rejected: `[Makefile, scripts, src/decisions, tests]`: the overlay would delete a fix packet's red-first tests and revert its code, so the verify would judge main again. The checker is already held: main's `Makefile` runs `src/decisions.py` and `src/decisions/` extracted at the base (and `src/decisions` would not guard `src/decisions.py`). No `relay/queue.yaml` here yet (D4: it is born with the relay's first row here, copying §5's list).
- A finished packet the new doclint refuses (none at 2a1dfcb) is `git mv`'d unedited to `history/packets/`, the d13 precedent.
- One change-log row `d15`: `S`, the four sha prefixes, the ports, the harness list and its rejected shape, and that the relay does not yet set `DECISIONS_BASE`.
- Act 2, one commit: `make readme` once; the README's `353` cases is false (d14 closed at 363, the ports move it), and the renderer writes the live count. If the render fails its meaning checks, commit nothing for act 2, restore the source, and record that as the open fork.

Deferred, decided: ADV11-6 (the readme walls) to the next README round; ADV11-7 (home paths in rows files) to the repo-relative rows re-sync; §5's 900 s to the next fold. An unexplained red `make check`: commit nothing for that act, record it, stop.

## 3. Interfaces (signatures, not prose)

- `scripts/bounded [--lock FILE] [--wall S] [--load N] -- cmd...`; exits: the command's, 124 wall, 2 lock or load, 1 usage, 127 no start, 128+signum on TERM, INT or HUP; last stderr line `bounded: stop: lock|load|wall`.
- `scripts/doclint [--repo DIR]`, 0 clean, 2 refusal; `GRANDFATHERED`, `SPENT`, `RUNNERS`, `MAKE_TARGETED`. `scripts/hygiene [--json] [--allow FILE] [--repo DIR]`.
- The relay's queue: `harness: [path, ...]` in `defaults` or a row; `HarnessOf` adds `GNUmakefile`, `makefile`, `Makefile`.

## 4. Findings that name this row

Measured on `main` 4cca4c8 with the session's scripts at 2a1dfcb (s14, before s15) in a `mktemp -d` copy: new doclint exit 0 (d13 and d14 pass); new hygiene `hits outside allowlist: 0`; the largest tracked file is 38,537 bytes, so ADV11-15 moves nothing here. At 2a1dfcb: hygiene 157edaff, doclint a45c3ec1, bounded b3c5f7fe, test_hygiene 8154d4da. This repo's three tests under them: Ran 40, 4 failures (two shape tests, `sees_through_wrappers`, `binary_scanned_for_home_over_printable_runs`). The session's `test_hygiene`: Ran 17, OK here; its `test_doclint` and `test_bounded` import pytest. `test_bounded` names retired there: `exit_passthrough`, `load_breaker_exits_2`, `mkdir_era_lock`, `sigterm_ends_143_and_frees_the_lock`, `wall_kills_the_group_grandchild_too`. The relay's `main` sets no `DECISIONS_BASE`.

## 5. Forbidden reads

The moved ledger and reference trees; `decisions/` whole; `design/decisions-r1.md` beyond one `sed -n` section; `history/packets/`; `../example-mac/history/relay/`; the respeak, relay and example-ops repos; in the session, only the three scripts and the three tests at `S`; any file over 8 KB whole except this packet and the `Makefile`.

## 6. Report (one table, four bullets, under 1,000 words)

The table: each acceptance line, its exit and last output line on the branch. Bullets: what was carried (with `S`); choices §2 does not name; what was left undone; the open fork, if any (none is expected).
