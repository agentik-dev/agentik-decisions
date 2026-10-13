# Packet D20: `make readme` keeps the render the verifier refused

| item | value |
|---|---|
| from | `NICE_TO_HAVE.md`, the line "The observer, 2026-10-02 (D19's landing): `make readme` was refused twice before it passed"; `scripts/readme-render`'s docstring, steps 4 and 5 |
| pin | this repo's `main` at the commit that lands this packet; worktree `.claude/worktrees/d20`, branch `d20` |
| wall | this repo only. No push, `--amend`, rebase, device or network. No `make check`, no `make readme` and no `make install`: a relay night is live, so run only the test modules named here. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never run or build a `relay` binary. Never start `claude`: the tests use the fake renderer and verifier they already write |
| may touch | `scripts/readme-render`, `tests/test_readme.py`, `NICE_TO_HAVE.md`, `history/sittings/*.md` if this repo keeps them. Nothing else; `.gitignore` already ignores `.readme-*.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest -v tests.test_readme -k refused 2>&1 \| grep -c ' \.\.\. ok$'` reads 3 or more, and `grep -c 'FAIL'` over the same output reads 0; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest tests.test_readme 2>&1 \| tail -1` reads `OK` |
| budget | 30 turns, `claude-opus-5-5`; one commit per act |
| verify | the observer runs `make check` before the merge, once no relay verb is live |

## 1. What the source says (quoted)
- The sighting: "`make readme` was refused twice before it passed, on a source change of one sentence. Run 1 (7 min 38 s): "numeric tokens: lost {} gained {'2': 1}". Run 2 (3 min 42 s): "fenced code blocks changed (9 -> 9 or content differs)". Run 3 (6 min 43 s) passed. [...] `readme-render` deletes a refused render, so nothing shows what the model changed; keep the refused file beside the README, or print the verifier's differing lines".
- The docstring: "4. respeak-verify-edit.py source temp must pass, else README.md is untouched; 5. the temp file moves over README.md".
- Today, `stamp_and_render`'s `finally` unlinks the temp on every path, the verifier's refusal among them.

## 2. Rulings
1. **The refused render is kept.** When the verifier exits non-zero, the render moves to `.readme-refused.md` at the repo root (an existing one is replaced), README.md and the source stay as today, and the exit stays 2. stderr gains one line naming the file and the command that shows the change: `readme-render: the refused render is .readme-refused.md; diff README.md .readme-refused.md`.
2. **Only the verifier's refusal keeps it.** A style-gate failure (exit 1), a renderer exit, a timeout or a setup refusal leaves no `.readme-` file, as today (ADV10-6 stays true).
3. **A pass removes a stale one.** A run whose verifier passes removes `.readme-refused.md` if it exists, so the file never outlives the render it describes.
4. **No retry.** The target still renders once. A retry inside the target doubles a spend the owner did not ask for; leave it.
5. **Tests.** Three, each red on `main`, each with `refused` in its name: the verifier's refusal keeps exactly one new file, `.readme-refused.md`, holding the fake render's text, and stderr names it; a style-gate failure leaves none; a passing run after a refusal removes it. `test_failing_verifier_writes_nothing` asserts the set of written files is unchanged; change only that assertion so it allows `.readme-refused.md`, and say so in the report. The docstring's step 4 says the refused render is kept.
6. The `NICE_TO_HAVE.md` sighting keeps its first sentences and loses the clause this lands, with "(landed as D20)".

## 3. Interfaces (signatures, not prose)
New: the constant `REFUSED = ".readme-refused.md"` in `scripts/readme-render`. Unchanged: `main`'s argv and exit codes, `stamp_and_render`'s signature, the sidecar, the stdout lines.

## 4. Findings that name this row
`scripts/readme-render:174-216` (`stamp_and_render`; the verifier at `:199-202`, the `finally` at `:208-211`); `tests/test_readme.py:104` (`FAKE_VERIFY`), `:128-130` (`run_script`, `FAKE_VERIFY_EXIT`), `:159` (the hung render), `:191-197` (`test_failing_verifier_writes_nothing`); `.gitignore` (`.readme-*.md`).

## 5. Forbidden reads
Other repos; the account's `~/.local/state`, its claude install, its user-level CLAUDE.md, git config, ssh config, ledgers, transcripts; packets but this; worktrees but yours.

## 6. Report (capped)
The acceptance lines with their counts, `make doclint`'s and `make hygiene`'s last lines. Bullets: each test's red line on `main`; the existing assertion changed; what was left. Last line: branch, head sha.
