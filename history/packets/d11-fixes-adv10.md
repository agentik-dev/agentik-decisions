# Packet d11-fixes-adv10: the ADV10 fixes, six acts, one builder

| item | value |
|---|---|
| from | `design/review-adv10.md` (whole): ADV10-1 high, ADV10-2 to 7 medium; its verdict and its three tests; run 10's rulings name no decisions row; the STANDING WORD (decide inside the design, record, one open fork at most) |
| pin | `main` 4982fc7 or later; branch `d11-fixes-adv10`, worktree `.claude/worktrees/d11-fixes-adv10` |
| wall | this repo. No push, `--amend`, rebase, device, `relay`; never `make readme` or `claude plugin validate` by hand; every temp path from `mktemp -d`; write any file holding the owner's verb with the Write tool, never a heredoc (the hook denies it) |
| may touch | `src/decisions/*.py`, `tests/*.py` except `test_hygiene.py` and `test_doclint.py` (`test_makefile.py` new), `tests/skips.allow`, `scripts/readme-render`, `plugin/scripts/deny-rule.sh` (its comment only), `Makefile`, `.gitignore`, `design/decisions-r1-changelog.md` (one row), `history/sittings/*.md`. Never: `decisions/`, `design/readme/`, `README.md`, `scripts/bounded`, `scripts/hygiene`, `scripts/doclint`, `.hygiene-allow`, the rest of `plugin/` |
| verify | `make check`, exit 0 at every commit and at close, its log to a `mktemp` file; never an acceptance line |
| acceptance | repo root, the virtualenv, `P="PYTHONPATH=src python3"`; `S` is `T=$(mktemp -d); git init -q -b main $T; cp -r tests/fixtures/sample/decisions $T/; git -C $T add -A; git -C $T -c user.name=t -c user.email=t@t commit -qm base`; baseline on `main` 4982fc7 in parentheses. Act 0: `S; mkdir -p $T/.claude/claude-code-session $T/elsewhere; printf 'decisions:\n  dir: elsewhere\n' > $T/.claude/claude-code-session/config.local.yaml; cp $T/decisions/config $T/decisions/governs $T/elsewhere/; $P -m decisions --dir $T check --against HEAD; echo $?` reads 2 (0, `0 findings over 0 records`); `$P -m unittest tests.test_against -q 2>&1 \| tail -1` reads `OK`. Act 1: `$P -m unittest tests.test_makefile -q 2>&1 \| tail -1` reads `OK` (no module); `make -n decisions AGAINST=bogus 2>/dev/null \| grep -c bogus` reads 0 (1). Act 2: `$P -c 'from decisions.writing import claude_ancestor as a; print(bool(a()))'` reads `True` under the builder (ImportError); `$P -m unittest tests.test_writing -q 2>&1 \| tail -1` reads `OK`. Act 3: `grep -c '^38 ' tests/skips.allow` reads 1 (0); `$P -m unittest tests.test_gates -q 2>&1 \| tail -1` reads `OK`. Act 4: `T=$(mktemp -d); cp -r tests/fixtures/sample/decisions $T/; git init -q $T; printf '99999\n' > $T/decisions/.new.lock; $P -m decisions --dir $T new --title x --governs tooling --consumer y; echo $?` reads 0 (2, `held by pid 99999`); `git check-ignore -q decisions/.new.lock .readme-x.md; echo $?` reads 0 (1); `grep -c 'timeout=' scripts/readme-render` reads 3 (0); `grep -A1 '^readme:' Makefile \| grep -c 'bounded --wall 900'` reads 1 (0). Act 5: `grep -cE '^\| d11 \|' design/decisions-r1-changelog.md` reads 1 (0); `git status --short \| wc -l` reads 0 |
| budget | 80 turns (the run cap; six small acts), 150k context; ONE commit per act, the charter in the last; the charter names doclint's five rows at open; checkpoint at 80%; never push, amend or rebase |

## 1. What the source says (quoted)

ADV10-1: "resolve `dir` from the defaults and from `config.yaml` as committed at REV only, and refuse (exit 2) when any other layer moves it." ADV10-2: "on main, measure against the last pushed state (`origin/main`)". §2 restates the rest.

## 2. Rulings

Order fixed; each act's reproducing test lands in its commit, red before, green after.

- Act 0 (ADV10-1): under `--against`, the records dir is frozen to REV: the defaults overlaid by `.claude/claude-code-session/config.yaml` as committed at REV (absent: `decisions`). When the working resolution differs, a Refusal (exit 2) names the layers `resolve` applied past the defaults. A corpus with records at REV and none now is the finding `corpus emptied since REV`. A committed dir move is refused too; on `main` it reads red until the owner pushes.
- Act 1 (ADV10-5, ADV10-2): the Makefile's `AGAINST` and `RULING` are `override ... :=`. On a branch, `AGAINST` is `git merge-base main HEAD`; none is exit 2 `decisions: no merge base with main`. On `main` it is `origin/main` with `--ruling`; none is exit 2 `decisions: no origin/main on main`. Under `--ruling`, `check` prints one `ruled since REV: <relpath> <from> -> <to>` line per admitted status move (stdout, not a finding). The owner-only proof is §6's open fork.
- Act 2 (ADV10-3): `rule` refuses in this order: `CLAUDECODE`, a `claude` ancestor, no TTY, the id typed back. `claude_ancestor` failing to read the chain is a refusal (fail closed). `Hermetic.setUp` patches `decisions.writing.claude_ancestor` to return None, and the `Ancestry` class exercises the real one through a fake runner. `deny-rule.sh`'s comment stops calling itself the guard.
- Act 3 (ADV10-4): each `skips.allow` line is `<count> <reason>`. A line without a leading count is `skips.allow:<n>: no count`, exit 1. Discovery matches every count exactly; a named-module run counts at most the pin. A miss prints `skips: <reason> counted <n>, pinned <m>`. The pyflakes gate reads the reasons as before.
- Act 4 (ADV10-6, ADV10-7): `readme:` runs under `$(PY) scripts/bounded --wall 900 --`. The three `subprocess.run` calls in `readme-render` take `timeout=` (the count 120 s, the render 840 s, the verifier 120 s); a TimeoutExpired is `Refused`, so `finally` removes the temp. `.gitignore` gains `.readme-*.md` and `.new.lock`. `held` takes over a lock whose pid does not exist (`os.kill(pid, 0)`: ProcessLookupError), retries `O_EXCL`, writes `new: took over <relpath> from dead pid N` to err. A live or unreadable pid waits, then refuses. `check` finds `stale lock <relpath>: pid N is not running`.
- Act 5: one change-log row `d11`: the frozen dir, `origin/main` on main, the ancestry guard, and the known limit that `--ruling` cannot tell the owner from an agent until §6's fork is ruled. Nothing in `design/decisions-r1.md` moves.

Deferred, decided: ADV10-8 (one `git cat-file --batch`) goes with the example-app conversion. ADV10-9 waits for ruling 8 in agent-relay (`packets-34-relay`), after which a hygiene pass here drops `home` from the rows allow row. The verdict's relay-side step (main's check over the branch tree) is agent-relay's. An unexplained red `make check`: commit nothing for that act, record it in the charter as the open fork, and stop.

## 3. Interfaces (signatures, not prose)

- `against.py`: `dir_at(root, sha) -> str`, and `lint_against(root, rev, ruling, items, settings=None)`. A `settings` whose `dir` is not `dir_at` is a Refusal: `check: --against REV reads <dir_at>; <layer> (<path>) moved it to <dir>`. `ruled_moves(...) -> [(relpath, from, to)]` for the stdout lines.
- `writing.py`: `claude_ancestor(pid=None, runner=None) -> str|None`. It walks `ps -o ppid=,comm= -p <pid>` (5 s timeout, at most 64 hops, stop at pid 1 or a repeat) and returns `pid N claude` when a `comm` basename is `claude`, `unknown: <why>` on a ps failure, and None otherwise. The refusal is `rule: refused: <that>; rule from your own terminal`.
- `held(root, wait)`: a dead-pid takeover at most once per call.
- `tests/test_makefile.py`: temp repos with copies of `Makefile` and `src/`, `make PY=<sys.executable> decisions`; classes `NoMain` (branch `trunk`), `NoOrigin`, `OverrideIgnored` (`make -n`), `MainAgainstOrigin` (`git update-ref refs/remotes/origin/main` at the base, then a committed body edit to an in-force record reads red, where `AGAINST=HEAD` read green).
- `tests/test_against.py` `RedirectedDir`: `config.local.yaml`, `$DECISIONS_DIR` and a committed `config.yaml` move each exit 2, and an emptied corpus is exit 1. `tests/test_gates.py` `SkipCount`: an extra skip and a missing skip under discovery each exit 1, and a line with no count exits 1.

## 4. Findings that name this row

On `main` 4982fc7: `past_records` reads `records_dir()` (`against.py:69`); `Makefile` `AGAINST ?=` line 51, `readme:` line 90 unbounded; `readme-render` has no `timeout=`; `tests/run.py:37` matches reasons with no count; `ps -o comm=` names `claude` twice in this sitting's ancestry. The hook denied this sitting's own measuring line.

## 5. Forbidden reads

The moved ledger and reference trees; `decisions/` whole; `design/decisions-r1.md` beyond one `sed -n` section; the refuters and older packets; `../example-mac/history/relay/`; the session, respeak, agent-relay and example-ops repos; any file over 8 KB whole except the review and the `Makefile`.

## 6. Report (one table, four bullets, under 1,000 words)

The table: each acceptance line, its exit and last output line on the branch. Bullets: the findings carried and those deferred; choices §2 does not name; what was left undone; the open fork. The open fork (the packet writer's, for the owner): the owner-only proof of a ruling (ADV10-2's durable fix); recommended, `check --ruling` admits a status move only in a commit signed by a key in a committed allowed-signers file (git SSH signing, the password manager's agent). Its consumer is the example-app conversion. The last line: the branch name and its head sha.
