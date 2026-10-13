# Packet d13-resync: the post-S13 re-sync of hygiene, doclint and bounded, then the README; two acts, one builder

| item | value |
|---|---|
| from | the S13 handovers (`../claude-code-session/history/sittings/2026-09-24-2-s13a-conventions-r10.md` and `...-3-s13b-conventions-r10.md`, their `## Handover` only); `record ../claude-code-session/design/conventions.md --section '§5-7'`, `'§9'`; the session's `scripts/` and three tests at `main` 35b5870; this packet's measurement (§4); the README round's render rules (d10's packet, now under `history/packets/`); the STANDING WORD |
| pin | `main` 9340f9c or later; branch `d13-resync`, worktree `.claude/worktrees/d13-resync` |
| wall | this repo. No push, `--amend`, rebase, device, `relay`; `make readme` exactly once, at close; never `make e2e`, `make tla`, or `claude plugin validate` by hand; never run the session's tests; copies come from `git -C <session> show 35b5870:<path>`, never its working tree; every temp path from `mktemp -d`, every log to a `mktemp` file |
| may touch | `scripts/hygiene`, `scripts/doclint`, `scripts/bounded`, `tests/test_hygiene.py`, `tests/test_doclint.py`, `tests/test_bounded.py`, `Makefile` (the two pins only), `design/packets/d8-resync.md`, `design/packets/d9-fold.md`, `design/packets/d10-readme-r7.md`, `design/packets/d11-fixes-adv10.md`, `design/packets/d12-resync.md` (each `git mv`'d, unedited, to the same name under `history/packets/`), `design/decisions-r1-changelog.md` (ONE row), `design/readme/source.md` (the wall line), `README.md` and `design/readme/rendered.sha256` (by `make readme` only), `history/sittings/*.md`, `history/sessions/NEXT`. Never: `src/`, the other tests, `tests/skips.allow`, `plugin/`, `decisions/`, `design/decisions-r1.md`, `.hygiene-allow`, `.gitignore`, `scripts/readme-render` |
| verify | `make check`, exit 0 at every commit and at close, its log to a `mktemp` file, `readme: fresh` in it; never an acceptance line |
| acceptance | repo root, the pyenv virtualenv that `.python-version` names (`python3` resolves to it); baseline on `main` at this packet's commit in parentheses. Act 1: `shasum -a 256 scripts/hygiene scripts/doclint scripts/bounded tests/test_hygiene.py \| cut -c1-8 \| tr '\n' ' '` reads `d63d0ffb d5957c6c e343b094 0e8c21c3` (`efc59152 b924a7bc 63cebd3d e165533d`); `grep -lE '^import pytest\|pytest\.' tests/test_doclint.py tests/test_bounded.py \| wc -l` reads 0 (0; 2 with the session's copies taken whole); `grep -cE 'def test_(legacy_stems_need_no_verify\|spent_skips_the_suite_rule\|acceptance_shape_refused\|acceptance_shape_allowed)' tests/test_doclint.py` reads 4 (0); `grep -c 'def test_sigterm_without_wall_exits_143' tests/test_bounded.py` reads 1 (0); `env PYTHONPATH=src python3 tests/run.py test_bounded test_doclint test_hygiene 2>&1 \| grep -E '^(OK\|FAILED)'` reads `OK` (`OK`); `ls history/packets/d*.md \| wc -l` reads 14 (9); `ls design/packets/d*.md \| wc -l` reads 1 (6); `python3 scripts/doclint; echo $?` reads 0 (0; 2 with the new doclint alone); `make hygiene doclint; echo $?` reads 0 (0); `grep -cE '^\| d13 \|' design/decisions-r1-changelog.md` reads 1 (0). Act 2: `grep -c '840 s wall' design/readme/source.md README.md` reads 1 each (0 each); `grep -c '900 s' design/readme/source.md README.md` reads 0 each (1 each); `env PYTHONPATH=src python3 -m unittest tests.test_readme 2>&1 \| tail -1` reads `OK` (`OK`); `shasum -a 256 -c --status design/readme/rendered.sha256; echo $?` reads 0 (0); `git status --short \| wc -l` reads 0 |
| budget | 60 turns (50 plus 10 for the render, whose respeak rounds are slow), 150k context; TWO commits (act 1, act 2), the charter in the last; act 1 is ONE commit so neither `make hygiene` nor `make check` reads red at a commit; the charter names doclint's five rows at open; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

Conventions §6: every copy of `scripts/hygiene` and `scripts/doclint` has the session's sha256 (now `d63d0ffb...` and `d5957c6c...`, measured at 35b5870). §9: "The `verify` row is required (doclint's GRANDFATHERED packets excepted)". The new doclint's rule: outside GRANDFATHERED and SPENT no acceptance line runs a whole suite, and "a command word that is not a literal word (`$m`, `$(...)`...)" counts as one. s13a: "a double-quoted word that expands (`"$m"`) counts as non-literal". s13b: `bounded` on TERM, INT or HUP "exits 128+signum without a traceback, wall or not". The owner (run 10 report, decision 1): GRANDFATHERED names agent-relay's 17 pre-AR10 stems; no historical packet is edited to satisfy the new doclint.

## 2. Rulings

Decided inside the design (the packet writer's; the builder records any further choice in the charter):

- Act 1, ONE commit. Take `scripts/hygiene`, `scripts/doclint`, `scripts/bounded` and `tests/test_hygiene.py` byte-identical from the session's `main` 35b5870; move `HYGIENE_SHA` and `DOCLINT_SHA`.
- The session's `tests/test_doclint.py` now imports pytest (four module-level tests, one parametrized), which this repo does not carry (stdlib, `unittest`). Port it, as d12 ported `test_bounded`: the `DoclintTest` class byte-for-byte, the four functions as methods of a second `unittest.TestCase` class with the same names, `parametrize` as `subTest` with its ids, `assert` as `assertEqual`/`assertTrue`; a header line names the session's sha and says it is a port. Rejected: keeping the 330bded copy (it passes, measured, but never tests GRANDFATHERED, SPENT or the new shapes), and adding pytest (the repo's no-dependency invariant).
- `tests/test_bounded.py` (this repo's port) gains the session's `test_sigterm_without_wall_exits_143` in `unittest` (the command's exit passes through, a load under the ceiling keeps its exit, SIGTERM with no wall is 143 with no `Traceback` and the child dies). The comment in `test_sigterm_ends_143_and_frees_the_lock` that blames 63cebd3d becomes: with a wall, the gate's shape; the d12 finding is closed by e343b094.
- The five packets d8 to d12 are finished and merged; the new doclint refuses all five (18 lines, every one a `$P` or `$PY` command word). `git mv` them unedited to `history/packets/` (the d12 precedent, where d-split and d0 to d7 already rest). Rejected: editing their acceptance lines (falsifies a finished record) and naming this repo's stems in the canonical GRANDFATHERED (the canonical copy is never edited here, §6; that tuple is agent-relay's and the session's). This packet's own lines spell `python3` literally for that reason.
- One change-log row `d13`: the four sha prefixes, the doclint port and why, the five packets moved, the SIGTERM case, and that `design/decisions-r1.md` §5 still says 900 s until the next fold.
- Act 2, one commit: `design/readme/source.md`'s wall line says `a 840 s wall`; run `make readme` once (the renderer of record rewrites the status line with the live count and the sidecar), then `make check`. If the render fails its meaning checks, commit nothing for act 2, restore the source, and record it as the open fork.

Deferred, decided: `design/decisions-r1.md` §5's 900 s waits for the next fold (d12's row says so; the fold is its own packet). An unexplained red `make check`: commit nothing for that act, record it, stop.

## 3. Interfaces (signatures, not prose)

- `scripts/bounded [--lock FILE] [--wall S] [--load N] -- cmd...`; exits: the command's, 124 wall, 2 lock or load, 1 usage, 127 no start, 128+signum on TERM, INT or HUP; last stderr line `bounded: stop: lock|load|wall`.
- `scripts/doclint [--repo DIR]`, 0 clean, 2 refusal; `GRANDFATHERED`, `SPENT` tuples. `scripts/hygiene [--json] [--allow FILE] [--repo DIR]`.
- `make readme`: `scripts/readme-render` under `bounded --wall 900`; writes `README.md` and `design/readme/rendered.sha256`.

## 4. Findings that name this row

Measured on `main` c5ef33c with the session's files at 35b5870 in a `mktemp -d` copy (`git archive HEAD`, `git init`): new hygiene `hits outside allowlist: 0`; new doclint exit 2, 18 whole-suite lines in d8 to d12, none elsewhere; with the five moved, exit 0. This repo's `test_bounded`, `test_doclint` (330bded) and the new `test_hygiene` ran 46, OK, under the new scripts; the session's `test_doclint` and `test_bounded` fail to import (`No module named 'pytest'`). `test_makefile test_gates test_readme` ran 41, OK. The suite counts 359 cases; the README says 314 and 900 s. No `.hygiene-allow` row needed.

## 5. Forbidden reads

The moved ledger and reference trees; `decisions/` whole; `design/decisions-r1.md` beyond one `sed -n` section; the moved packets beyond `history/packets/d10-readme-r7.md`'s §2; `../example-mac/history/relay/`; the respeak, agent-relay and example-ops repos; in the session, only the three scripts, the three tests and the two handovers; any file over 8 KB whole except this packet and the `Makefile`.

## 6. Report (one table, four bullets, under 1,000 words)

The table: each acceptance line, its exit and last output line on the branch. Bullets: what was carried; choices §2 does not name; what was left undone (`decisions-r1` §5's 900 s); the open fork, if any (none is expected).
