# Packet d25: decisions in its plugin

| item | value |
|---|---|
| from | agentik-hq HANDOFF 17, build 2; `~/code/agentik-hq/design/04-self-contained-plugins.md` §7 item 5, §2, §3, §5 step 4, §6; hq entry 6 at a 3.9 floor; commons' c1 at 44131bf |
| pin | agentik-decisions main f3de271, plugin 0.9.0; worktree `.claude/worktrees/d25-plugin`, branch `d25-plugin` |
| wall | this repo; read `~/code/agentik-commons` (44131bf) and `~/code/agentik-session` (d641fd3), never write there except running commons' `scripts/sync <this worktree>`; no push, `--amend`, rebase, merge, real `make install`, real `install-cli`, `uv tool` anything; `claude` only as `claude plugin validate` and `claude plugin test plugin`; a test never writes under the live `~/.local`, `~/.claude`, `~/.config/agentik`; never touch `~/.config/agentik/hooks-follow-launcher`; no relay verb; no `kill`, `pkill` or signal from a script; never a gate verb under a temp HOME |
| may touch | `src/` to `plugin/lib/` by `git mv`, `plugin/` (bin, lib, commands, skills, `plugin.json`), `scripts/` (sync's copies and `vendored.sha256`), `Makefile`, `pyproject.toml`, `tests/`, `README.md`, `design/readme/*`, `NICE_TO_HAVE.md`, `CLAUDE.md`'s non-generated lines, this packet as `design/packets/d25-plugin.md`, a charter |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c "make check > <scratch log>"`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the code: read the code from its line |
| budget | acts as in §2, one commit each. **Stop at 140k context or 100 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

Read first, by sections, never whole: design/04 §2, §3, §5, §6, §7's first paragraph, its bare-machine test and item 5; commons' `GUIDE.md` §5, §10 and `scripts/sync`; session's `plugin/lib/agentik-session` (the four-line runner) and `tests/test_bare_machine.py` for the shape.

## 1. What this is

Decisions runs from its plugin with no clone, venv or uv tool: the package in `plugin/lib/decisions`, under `/usr/bin/python3 -I`, with the canonical launcher and `install-cli` from commons. **Not here:** agents (a-s18), the `suite` plugin (c2), uninstalling the uv tool (hq's install step).

## 2. Acts and rulings

0. This packet, committed first.
1. **The move.** `git mv src/decisions plugin/lib/decisions`, every path, the suite green, no behaviour change.
2. **The floor.** The package runs under Apple's 3.9.6: fix what doesn't (annotations, syntax, stdlib calls), each a small change; `pyproject.toml`'s `requires-python` to match. `make test` also runs the suite under `/usr/bin/python3`, as session's floor does; report both counts.
3. **The plugin's code.** `plugin/lib/agentik-tool.conf` (`tool_name=agentik-decisions`, `remedy=/decisions:install-cli`, `runner=agentik-decisions`, `old_name=decisions`, `old_state=`); the runner `plugin/lib/agentik-decisions` in session's four-line form; then run commons' `scripts/sync` on this worktree for `plugin/lib/agentik_install.py`, `plugin/bin/agentik-decisions`, `plugin/bin/agentik` and `vendored.sha256`. `install-cli` is a verb of decisions' CLI that calls the canonical module, plus `/decisions:install-cli`. `src/decisions.py`, the checkout runner: `#!/usr/bin/python3` or gone; say which.
4. **`make install`** keeps a dirty guard, then runs `plugin/bin/agentik-decisions install-cli`, honouring `HOME`/`PREFIX` so a test can aim it at a temp home. `uv tool install .` goes.
5. **The bare-machine test** joins the suite: `git archive HEAD plugin` into `$T/.claude/plugins/cache/agentik/decisions/<version>/`, env exactly `HOME=$T`, `PATH=/usr/bin:/bin`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, a decoy package in the cwd. In a temp git repo with a small ledger it runs `show`, `find`, `new`, `ask`, `answer`, `render --check` and `backlog` through `plugin/bin/agentik-decisions`. `ask` with no respeak prints design/04 §5's line, `ask: no respeak (RESPEAK_ROOT or an installed plugin); the questions stay as written`, on stderr and exits 0. Then `install-cli` under `$T` gives a launcher whose `--version` reads the new version, with a `decisions` link, under `PATH=/usr/bin:/bin`.
6. **Docs and the version.** README and CLAUDE.md say install is `install-cli`; plugin `0.10.0`, one bump, last; the README count from the suite.

## 3. The stop

Stop and report, committing what is there, on: a verb that cannot run at 3.9 without a design change; the canonical module unable to name decisions without editing it; the bare test unable to pass. A stop is a result.

## 4. Report (at most twelve lines)

The branch and sha; each gate's id and its code from the line; each act's result; both suites' counts; the check's seconds; the bare test's verbs and exits; anything decided or left over, and if you stopped at the budget, the exact resume line.
