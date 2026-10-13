# Adversarial review ADV11: claude-code-decisions since the adv-10 merge (main 6d98bb1)

Target: `git log 4982fc7..main`: d11-fixes-adv10 (ADV10-1 to 7), d12-resync and d13-resync (hygiene, doclint and bounded re-synced, check under an 840 s wall). Every reproduction ran in a temp clone (`/tmp/adv11-rule`, branch `probe`, with a forged Words line committed in the in-force record 0001), never in this checkout. Severity follows the adv-6 scale.

## Findings

**ADV11-1 (high, wrong green): the gate still runs the branch's own checker.** agent-relay now overlays main's harness over the gate's tree. But its `HarnessPaths` (`internal/gate/gate.go`) are `Makefile` and `scripts/` only. This repo's gate code sits elsewhere: `make decisions` runs `$(PY) src/decisions.py` from the branch, and `make test` runs the branch's `tests/run.py` against the branch's `tests/skips.allow`. A packet that lets a builder touch `src/decisions/` or `tests/` therefore lets it edit the check.

Repro: on `probe`, strict `make decisions` exits 1 (`body changed since 6d98bb1`). Then add `return []` at the top of `lint_against`, restore `Makefile` and `scripts/` from 6d98bb1 the way the relay's overlay does, and run `make decisions` again. It prints `# 0 findings over 1 records` and exits 0. Raising the skip pin from 38 to 39 in the branch's `skips.allow` works the same way.

ADV10's verdict asked for main's checker over the branch tree, and only the Makefile half was built. Fix: the Makefile, which is harness, should extract `src/decisions` and `tests/{run.py,gates.py,skips.allow}` at the base (`git archive $(AGAINST) … | tar -x -C $$tmp`) and run that copy over the branch's `decisions/`. The alternative is a per-repo harness list in the relay's queue row that names these paths.

**ADV11-2 (medium, wrong green; ADV10-5's residual): the base is a ref that any worktree can move.** On a branch, `AGAINST` is `git merge-base main HEAD`, and every worktree shares the `main` ref. Repro on `probe`: `git update-ref refs/heads/main HEAD`, then `make decisions`, exits 0 (the step before exited 1). On main, `origin/main` can be moved the same way. agent-relay's `branch-move` guard matches `git update-ref` by its shape, which makes it a courtesy, like `deny-rule.sh`.

Meanwhile `override` now stops the one party that knows the right base, the driver, from passing it in. Fix: the gate passes its stage-time sha of main (for example `DECISIONS_BASE` in the gate's environment, which a sitting does not control at gate time). The Makefile then requires that sha to be an ancestor of HEAD, and falls back to the merge base only for a run by hand. The relay can also refuse a gate when main moved after the stage.

**ADV11-3 (medium, ADV10-3 holds in part): the ancestor walk ends at launchd after a double fork.** Run from this agent's shell, `claude_ancestor()` returns `'pid 80455 claude'`. Run inside `( nohup sh -c '…' & )`, the subshell exits, the child is reparented to pid 1, and the same call returns `None`. `rule` itself was not run past the guards: the harness's permission layer refused that step, so this review claims only that the walk returns `None`. The name match is also tied to the install: the native binary's comm is `claude`, but an npm install runs as `node`.

No ancestry test can close this. The walk is a courtesy, as the hook is, and the durable proof is the owner-signed commit, deferred by the owner on 2026-09-24 (2). Fix: say so in `claude_ancestor`'s docstring and in the change-log's known limits. No new fork.

**ADV11-4 (medium, concurrency): two `new` calls can both take over one dead lock.** `held()` re-reads the pid before `os.remove`, but that read-then-remove is not atomic, and `finally` removes the lock without checking whose it is. Repro (`/tmp/adv11-race.py`, a pid-99999 lock, B's `os.remove` wrapped so that A runs between B's re-read and B's remove):

- A prints `took over … from dead pid 99999` and `A holds pid 96041`.
- B prints the same takeover line and `B holds pid 96018 while A still holds`.
- A's lock file then names B's pid, so A's `finally` removed B's lock.

Two mints can now read the same next id. Fix: keep the lock file and take `fcntl.flock` on it, as `scripts/bounded` does, so a dead holder's lock is released by the kernel. Failing that, take over by `os.rename` of a private temp onto the path after a matching `fstat` inode, and in `finally` remove the file only if it still names our pid and inode.

**ADV11-5 (medium, wrong green a builder can move): `expectedFailure` passes the skip pin.** `tests/run.py` counts `result.skipped` only. Repro: `tests/test_zz_probe.py` with `@unittest.expectedFailure` on `assertEqual(1, 2)` gives `OK (expected failures=1)`, `skips: 0 allowed`, exit 0. Under discovery it gives `OK (skipped=38, expected failures=1)`, `skips: 38 allowed`. Fix: the runner fails on any expected failure or unexpected success unless a counted allow line lists it, and that allow file is main's (ADV11-1).

**ADV11-6 (low, bound): the readme walls add up past their outer wall.** The children's walls are 120 s (count), 840 s (render) and 120 s (verifier), 1,080 s in total, under `make readme`'s `bounded --wall 900`. When the outer wall fires first, `finally` never runs. The temp file is ignored now, so it only lingers. Fix: derive the three walls from one budget, for example 60, 720 and 60.

**ADV11-7 (low, public surface; ADV10-9 grown): the home paths have spread.** `git grep -l /Users/` now lists 10 `design/packets/rows-*.json` files, up from 8. `.hygiene-allow:12` still admits `home` for them. This stays deferred to the repo-relative rows re-sync (its consumer).

## ADV10 high and medium findings as shipped

| ADV10 | as shipped |
|---|---|
| 1 high | holds: `config.local.yaml` with `dir: elsewhere` gives exit 2, naming the layer and the path. ADV11-1 goes around it, not through it. Not a regression. |
| 2 medium | holds as scoped: the base is `origin/main`, and a `ruled since` line is printed per move. The owner-proof half is deferred by ruling. The ref move of ADV11-2 reaches `origin/main` too. |
| 3 medium | in part: the hook is named a courtesy, and the walk catches a live `claude` parent but not a reparented one (ADV11-3). |
| 4 medium | holds for skips, in both directions. `expectedFailure` (ADV11-5) and the pin living on the branch (ADV11-1) remain. |
| 5 medium | holds for a missing `main`, which is exit 2. A moved `main` defeats it (ADV11-2). |
| 6 medium | holds: with a 3 s render wall under `scripts/bounded`, the result was `refused, respeak-render.sh took over 3 s`, exit 2, no orphaned `sleep`, and no temp file left. ADV11-6 is low. |
| 7 medium | holds for the wedge: the dead lock is taken over, and `check` flags a stale one. The takeover races (ADV11-4). |

No regression.

## Verdict

Not yet the authority for example-app rulings. Every ADV10 fix holds where it was aimed, but the gate still trusts two things a builder controls: the checker's code on the branch (ADV11-1), and a base read from a mutable ref (ADV11-2). The one fix that matters most is ADV11-1, because it is the same class as ADV10-10, which the relay closed for the Makefile only. Fix before carrying example-app: ADV11-1 and ADV11-2. The same packet should also take ADV11-4 and ADV11-5. ADV11-3 needs only its known-limit text. ADV11-6 and ADV11-7 can wait for the next re-sync.

## The three tests to add first

1. `test_makefile`: a temp repo whose branch commits a forged in-force record and `return []` in `lint_against`. `make decisions` exits 1 because it runs the base's `src/decisions`.
2. `test_makefile`: with `main` moved to HEAD and `DECISIONS_BASE` pinned to the true base, the gate exits 1. A pinned base that is not an ancestor of HEAD exits 2.
3. `test_writing`: two processes take over one dead lock, and exactly one of them holds it. A holder's exit never removes a lock that names another pid. `test_run` also fails an `expectedFailure` that is not pinned.
