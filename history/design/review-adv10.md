# Adversarial review ADV10: claude-code-decisions since the adv-6 merge (main 63d53c4)

Reviewer: relay row adv-10-decisions, 2026-09-23. Target: the 30 commits from 0756c03 to 63d53c4 (`against.py`, `writing.py`'s lock and `commit_texts`, `settings.bounded`, the POSIX deny hook, `tests/run.py` and `skips.allow`, `tests/hermetic.py`, `scripts/bounded`, `scripts/readme-render`, the Makefile). Every reproduction ran in a temp repo under `/tmp/adv10-*` with the checkout's `src/`. I edited no file I reviewed. The tool still starts nothing of its own kind, so it cannot fork-storm. Its exposure is still the wrong green.

## Findings

**ADV10-1 (high, wrong green): an ignored config file points `check --against` at an empty corpus.** `resolve()` takes `dir` from `.claude/claude-code-session/config.local.yaml` (gitignored, `.gitignore:8`), from the committed `config.yaml`, `~/.claude/decisions/config.yaml`, the session's `resolved.json` or `$DECISIONS_DIR`. `past_records` (`against.py:69`) reads REV under that same redirected dir. Repro: on a branch, forge the Words of an in-force record (strict `check --against main` exits 1). Then write `decisions: {dir: elsewhere}` to `config.local.yaml` and copy `config` and `governs` into `elsewhere/`. After that, `check --against main` prints `0 findings over 0 records` with exit 0, `index --check` exits 0, and `git status` shows only the forged record. Fix: under `--against`, resolve `dir` from the defaults and from `config.yaml` as committed at REV only, and refuse (exit 2) when any other layer moves it. A corpus that had records at REV and has none now is a finding.

**ADV10-2 (medium, the ADV6-1 residual on main): `--ruling` cannot tell the owner from an agent.** On main the Makefile passes `AGAINST=HEAD --ruling`, which admits exactly the delta `rule` writes, and a `sed` writes the same bytes. Repro on main: commit a filled `proposed` draft, `sed` its status to `in-force`, and `check --against HEAD --ruling` exits 0. Once that is committed, every later check compares HEAD with itself. The orchestrator commits straight to main (63d53c4), so an unattended session can mint a ruling that no gate sees. Fix: on main, measure against the last pushed state (`origin/main`), not HEAD. The durable fix is an owner-only proof on each status move, such as a signed commit or tag that `check --ruling` requires. Until that exists, the charters should name this as a known limit.

**ADV10-3 (medium, ADV6-2's fix does not hold): both guards on `rule` are bypassed.** (a) `expect(1)` supplies the TTY. `/usr/bin/expect -c "spawn decisions rule 0003 in-force; expect confirm:; send 0003\r"` (the verb held in a variable) printed `0003 proposed -> in-force`, exit 0, under `env -u CLAUDECODE`. (b) The hook allows `r=rule; decisions $r ...`, `$(echo decisions) rule ...`, `echo rule | xargs -I{} decisions {} ...` and `D=decisions; $D rule ...`: all four exit 0 through `deny-rule.sh`. A token match cannot close these. Fix: `rule` refuses when any ancestor process is `claude` (walk the ppid chain with `ps -o ppid=,comm=`), which neither `env -u` nor a pty removes. The real guard is the git check (ADV10-1, ADV10-2), so the hook's comment should stop calling itself one.

**ADV10-4 (medium, wrong green a builder can move): the skip allow list matches by reason, with no count.** `tests/run.py:37` passes any skip whose reason string is listed. Repro: a test that would fail, decorated `@unittest.skip("set DECISIONS_LEGACY_REFERENCE to the moved reference/ tree (D14)")`, gives `OK (skipped=1)`, `skips: 1 allowed`, exit 0. Nothing notices when 38 legacy skips become 39. Fix: each allow line pins its count (`38 <reason>`), or the test ids. The runner fails on any difference, in either direction.

**ADV10-5 (medium, wrong green): the Makefile falls back to HEAD when there is no local `main`.** `AGAINST ?= $(shell git merge-base main HEAD || git rev-parse HEAD)`. In a clone or CI checkout without a local `main`, the gate measures the branch against itself. Repro: rename `main` to `trunk`, commit a forged in-force Words line, compute AGAINST the Makefile's way: it equals HEAD, and `check --against` exits 0. `AGAINST` can also be overridden from the environment. Fix: fail early with exit 2 (`decisions: no merge base with main`), and use `:=` so the gate line is not overridable.

**ADV10-6 (medium, hang): `make readme` starts `claude -p` with no wall.** Ruling 11 has builders run it at close. The Makefile says "every `claude` start is bounded", but `readme-render:153` and `:164` call `subprocess.run` without `timeout`. respeak's `run_agent` sets no wall and no `--max-turns`. `readme` is not under `scripts/bounded`. Repro: `RESPEAK_RENDER_CMD` set to a 30 s sleeper, the render under `perl -e 'alarm 8'`. It was killed at 8 s (exit 142), and it left `.readme-*.md` in the repo root, untracked and not ignored, with the sleeper still running (`pgrep` 1). No process group is used, so killing the render orphans its runner. RESPEAK_DEPTH still stops recursion, and an account failure exits non-zero and stops the render. Fix: run the target under `scripts/bounded --wall 900`, pass `timeout=` to both calls, and ignore `.readme-*.md`.

**ADV10-7 (medium, wedge): a dead holder's `decisions/.new.lock` refuses every `new`, and nothing flags it.** `held()` (`writing.py:101`) leaves a dead holder's lock "the owner's to remove". Repro: `printf '99999\n' > decisions/.new.lock`, then `new` gives `held by pid 99999 ... waited 2.0s`, exit 2. `git status` shows `?? decisions/.new.lock`, because it is not ignored, so a builder's `git add -A` commits it and wedges every clone. `check` reads 0 findings. Fix: take over a lock whose pid is dead, as `scripts/bounded` does. Gitignore it, and have `check` flag it.

**ADV10-8 (low, unbounded measurement): `check --against` starts one `git show` per record.** With 303 records it takes 2.45 s against 0.05 s without `--against`, so 303 process starts per gate, run in parallel under relay load. That is linear in the ledger example-app will bring (about 210). Fix: one `git cat-file --batch` over the `ls-tree` list.

**ADV10-9 (low, public surface): ADV6-11 covered the markdown files only.** `git grep -l /Users/ -- 'design/packets/*.json'` finds 8 rows files with absolute prompt paths, allowed by `.hygiene-allow:12` (`home`). The repo is private, and going public is not ruled. Fix: carry ruling 8 (repo-relative rows) here too, and drop `home` from that row.

## ADV6 high and medium findings as shipped

| ADV6 | as shipped |
|---|---|
| 1 high | holds on a branch (a strict repro exits 1). ADV10-1 and ADV10-5 defeat it, and ADV10-2 is its residual on main. Not a regression. |
| 2 medium | does not hold (ADV10-3). |
| 3 medium | holds: fails closed under `PATH=/nonexistent`, and a 2.8 MB command reads in 0.8 s, well under the 10 s timeout. |
| 4 medium | holds: `DECISIONS_DIR=elsewhere` over test_check, test_index_render and test_writing gives 93 OK. |
| 5 medium | the pyflakes half holds (63d53c4). The allow list is loose (ADV10-4). The legacy half is still deferred to the convert map. |
| 6 medium | holds: `settings.bounded` kills the whole process group, and git and pyenv each have a timeout. |
| 7 medium | holds: a sed-ruled record with its placeholders gives two findings past proposed. |
| 8 medium | the same-tree half holds, but a dead lock wedges it (ADV10-7). The cross-branch half (gating the merge onto current main) is agent-relay's and is unbuilt. |

## Verdict

Closer, but not yet the authority for example-app rulings. On a branch, `check --against` does what ADV6-1 asked. However, the check reads its own inputs from state the builder controls: an ignored config file (ADV10-1), a missing `main` (ADV10-5), and, structurally, the branch's own Makefile and `against.py`. Because the relay gate runs the branch's `make check`, one Makefile edit on the branch removes the check. Must fix before carrying example-app: ADV10-1, ADV10-5 and ADV10-2 (at least the `origin/main` baseline), plus a relay-side step that runs main's `decisions check --against <base>` over the branch tree rather than the branch's own copy. ADV10-3 and ADV10-4 should land in the same packet. ADV10-6 and ADV10-7 can go in the next hygiene pass, and ADV10-8 and ADV10-9 can wait for the example-app conversion. The one fix that matters most is ADV10-1: freeze `dir` to what is committed at REV.

## The three tests to add first

1. `Against.test_redirected_dir_refused`: a `config.local.yaml` or `$DECISIONS_DIR` that moves `dir` makes `check --against` exit 2, and emptying a corpus that had records at REV is a finding.
2. `Makefile.test_no_main_fails_early`: in a temp repo with no `main`, `make decisions` exits 2 instead of measuring against HEAD.
3. `Run.test_skip_count_pinned`: one extra skip under an allowed reason makes `tests/run.py` exit 1.
