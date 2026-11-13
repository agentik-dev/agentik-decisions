# Packet d40: six small mends

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief d40 (hq `history/sessions/BRIEF-2026-11-12-decisions-d40-mends.md`). Six rows of `NICE_TO_HAVE.md`, each well specified; n43 is a reproduced fault |
| pin | main at `b51d923` (0.21.9). Version 0.21.10. Worktree `.claude/worktrees/d40-mends`, branch `d40-mends` |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state |
| may touch | `plugin/lib/decisions/render.py`, `answer.py`, `tree.py` (R1 only), and `plugin/lib` files pyflakes names (R2); `tests/gates.py`; `tests/test_d40_mends.py` (new), `tests/test_analyze.py`; `NICE_TO_HAVE.md` (the six rows leave); the version places, `tests/test_plugin.py`, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §2; `PYTHONPATH=plugin/lib python3 -m unittest tests.test_d40_mends` |
| budget | about 90 tool calls |

## 1. Rulings (one commit each, its test red at the pin)

- R1 n43: `head_holds` runs its git children without git's repository variables; one list, `tree.REPO_VARIABLES`, which `answer` now imports instead of keeping its own (`answer` imports `render`, so `render` cannot import `answer`).
- R2 n1: `plugin/lib` joins `ROOTS`; the shebang gate goes; the checkout runner `src/decisions.py` stays when anything names it.
- R3 n19: a test pins the two-rules case `docs/tests/x.md`; no product code.
- R4 n79: the `/`, `~`, `..` test comes before the NUL filter in the checkout list's reader.
- R5 n80: the list is read with `errors="replace"`.
- R6 n81: the cannot-be-listed warning spells target and list one way; the unmakeable line says "cannot be resolved". No other message changes; no new flag.

## 2. Acceptance

| # | line | at the pin |
|---|---|---|
| 1 | `GIT_DIR` naming another repo: `render --fold-tails` and `expire --write` read this repo's HEAD | red |
| 2 | an unused import, and 3.13-only syntax, under `plugin/lib` each turn the gates red | green |
| 3 | `docs/tests/x.md`: the two-rules case passes and names the winner | n/a (new) |
| 4 | `/abs\0x` in a checkout's list warns once; a NUL line with no such prefix is skipped silently | red |
| 5 | one `\xff` line and one warning line: the warning prints | red |
| 6 | one spelling for the two paths; "cannot be resolved" for the unmakeable line | red |
| 7 | `make check` green through the queue, once, last | |
