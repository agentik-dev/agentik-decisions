# Packet d-n1: render's target and writes, doctor's rows, the README render's leftovers (0.6.0)

| item | value |
|---|---|
| from | `NICE_TO_HAVE.md` at d22 3af7701, lines 11 (F4), 12 (F5), 13 (F6), 21 (F15), 22 (F16), 23 (doctor's python row), 46 and 47 (d18 1a obs), 56's first half (`Hermetic` and `XDG_CONFIG_HOME`), 68 (D20 left open), 69 (D20's three mutants); the owner's word, 2026-10-12 18:42: implement decisions' NICE items; the observer's sort, 2026-10-12 18:55 |
| pin | branch `d-n1` off `d22` at 3af7701 (D22 lands first; this branch merges after it); worktree `.claude/worktrees/d-n1`; a hand-run builder, not a relay row |
| wall | this repo only. No push, merge, `--amend` or rebase. No `make check` or `make install`: a relay night is live and this plugin is read from its repo dir; run the test modules named here, `make test`, `make doclint` and `make hygiene`, and `make readme` once, last. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never build a `relay` binary or run a `relay` verb. Tests set `HOME` and the XDG dirs to temp dirs; no live `claude` in a test |
| may touch | `src/decisions/common.py`, `src/decisions/render.py`, `src/decisions/ask.py`, `src/decisions/answer.py`, `src/decisions/doctor.py`, `src/decisions/cli.py`, `scripts/readme-render`, `tests/test_render.py`, `tests/test_answer.py`, `tests/test_doctor.py`, `tests/test_readme.py`, `tests/test_cli.py`, `tests/test_hermetic.py`, `tests/hermetic.py`, `tests/test_plugin.py` (the version), the three manifests, `design/readme/source.md`, `README.md` and `design/readme/rendered.sha256` (by `make readme`), `design/packets/d-n1-render-doctor-writes.md`, `NICE_TO_HAVE.md`, `history/sittings/*.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_render tests.test_doctor tests.test_answer tests.test_cli tests.test_hermetic tests.test_readme 2>&1 \| tail -1` reads `OK`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_render -k crlf -k symlinked -k into_the_ledger 2>&1 \| grep -c ' \.\.\. ok$'` reads 3 or more; `grep -c '"version": "0.6.0"' plugin/.claude-plugin/plugin.json` reads 1; `grep -c '^# Packet d-n1:' design/packets/d-n1-render-doctor-writes.md` reads 1 |
| budget | one builder sitting; one commit per act; act 1 the red tests |
| verify | the observer runs `make check` before the merge, once no relay verb is live |

## 1. What the source says

The eleven lines in the `from` row, quoted from `NICE_TO_HAVE.md`; each names its fix. In short:
1. F4: on a CRLF file, `render` and `new` write LF outside the block; keep the file's line ends.
2. F5: `render` replaces a symlinked target with a regular file; write through `os.path.realpath`.
3. F6: `render --into` accepts the ledger itself; refuse with exit 2 when the realpaths match, the ledger unchanged.
4. F15: `doctor` reports a stale installed tool as ok; warn when the version on PATH differs from this package's.
5. F16: `doctor --ledger` naming a missing file warns and exits 0; fail with exit 2.
6. Doctor's python row: a uv-tool python is ok; the row stops failing every repo.
7. L46: `answer` exits 2 when the CLAUDE.md block write fails after both files are written; keep the answer, warn naming `render`, exit not 2.
8. L47: the `cli.py` docstring's exit-code line stays within 100 characters.
9. L56, first half: `Hermetic` sets `XDG_CONFIG_HOME` to a temp dir instead of clearing it.
10. L68: a `.readme-refused.md` that is a directory: the refusal names it and exits as the packet D20 says.
11. L69: tests that kill D20's three mutants: a verifier timeout, a renderer exit of 3, and a stale refused render left behind.

## 2. Rulings

Act 1 commits the red tests, failing, before any fix: `test_render.Render.test_a_crlf_target_keeps_crlf_outside_the_block`, `test_a_symlinked_target_stays_a_link`, `test_into_the_ledger_itself_exits_2`; `test_doctor.Doctor.test_a_stale_tool_warns`, `test_a_named_missing_ledger_fails`, `test_a_uv_tool_python_is_ok`; `test_answer.Answer.test_a_failed_block_write_keeps_the_answer`; `test_cli.Verbs.test_doc_lines_within_100_characters`; `test_hermetic.GuardFires.test_xdg_config_home_is_a_temp_dir`; `test_readme.Render.test_a_refused_path_that_is_a_directory`, `test_verifier_timeout_keeps_no_refused_render` and the exit-3, replaced-old and stale-removed variants. A name may change to fit the module; the assertion may not. Decide what §1 leaves open and log it in one sentence. Exit codes change for callers (the relay orchestrator runs `answer`; every repo runs `doctor`): name each change in the README source. Remove from `NICE_TO_HAVE.md` the eleven items closed, leaving L56's second half. What lies outside §1 goes to `NICE_TO_HAVE.md`.

## 3. Interfaces

`render` and `new` keep a CRLF file's line ends; `render --into <ledger>` exits 2; `doctor` warns on a stale tool and exits 2 on a missing `--ledger`; `answer` after a failed block write exits as a warning, not 2. Version 0.6.0.

## 4. Findings that name this row

The eleven `NICE_TO_HAVE.md` lines in the `from` row.

## 5. Forbidden reads

Transcripts whole; the relay's state directory; any other repo beyond reading a `DECISIONS.md` for a lint probe.

## 6. Report

At most 250 words: each act's commit, each red test before and after, each acceptance line's result, `make readme`'s result, the exit-code changes, the choices made, any note filed.
