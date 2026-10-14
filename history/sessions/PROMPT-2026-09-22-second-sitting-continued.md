# Second sitting of agentik-decisions, continued: P2, P3, Act 3, the exit

You are the coordinator resuming sitting `history/sittings/2026-09-22-3.md` in `agentik-decisions` (private, the owner's account, remote `origin`, branch `main`). The sitting's prompt is `history/sessions/PROMPT-2026-09-22-second-sitting.md`; every rule in it binds. The first coordinator exited at the session budget's 80% line after Act 1 and part of Act 2. This prompt is self-contained.

## Read, in this order, and nothing else to start

1. `CLAUDE.md`.
2. `history/sittings/2026-09-22-3.md` (the charter: its Done-ness boxes and Handover say exactly where the sitting stands; trust them over this prompt if they differ).
3. `history/sessions/PROMPT-2026-09-22-second-sitting.md` §"Act 2" and §"Act 3" and §"Rules that bind every act" and §"Exit".
4. `history/packets/p2-index-render.md` and `history/packets/p3-check-stats.md` (the packets, already cut; do not rewrite them).
5. `history/packets/p1-report.md` (the P1 builder's HOW decisions, which stand) and, by need, `git log --oneline | head -20`.

Never read `design/decisions-r1.md` whole (40 KB, one refuter pass left); `sed -n '100,118p'` for §3.3 and the change-log at its tail by need. Never read `reference/` whole. Read `decisions/0001-decisions-as-files.md` only with `show`.

## What remains

- **First, Act 1c, the folds.** `design/ledger-conversion-refuter-1.md` is saved verbatim (FAIL, 5 blocking); its findings table's last column is the fold text. The record has 14 bytes of headroom under 16,384: cut first (§2's measured rows are replaced, not added to; §1's second paragraph can lose its last sentence), then fold B1 to B5 and M1 to M4 in-line, then the minors; B1 becomes a stated design in §7 (R25-87 to R25-89 go to example-mac in a second run, by 0001 (4)), not a question; B2's lettered ids are a rule (`--ids` only). B5 and M3 each want one sentence in `design/decisions-r1.md` (§2.2 and §3.3): land them as terse in-line folds only after the change-log is moved out (see Act 3) and record them in one change-log row. Then the status row reads "r1 fold 1 from refuter 1" and the change-log gains one row. Commit.

- **Act 2, P3:** P1, P2 and P4 are merged (charter). If the charter still shows `p3` running, the builder died with the session: `git log main..p3` in `.claude/worktrees/p3` shows its commits; if `history/packets/p3-report.md` exists there and `make check` is green in that worktree, merge (keep both sides of a `build_parser`, `VERBS` or docstring conflict), run `make check` on `main`, remove the worktree. If the branch is partial, spawn one Opus builder (claude-opus-5-5) in that worktree to finish `history/packets/p3-check-stats.md` from where the log stops, same rules as before (commit per item, `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, never push or amend, forbidden reads per the packet's §5). After the merge `src/decisions.py` passes a thousand lines, crossing decisions-r1 §3.1's "under a thousand lines": one measured change-log row, not a redesign, and a handover item for the owner (split the module or lift the line).
- **Act 3** as the sitting prompt says: `agentik decisions check` and `agentik decisions index --check` join `make check` (targets in the Makefile, run with `$(PY) src/decisions.py`); `agentik decisions index` writes `decisions/INDEX.md` for record 0001, committed; `make install` wrapping `uv tool install .` tried once (report the exit line; do not fix `uv`); `claude plugin install` from this repo tried once for the `source: "./plugin"` subtree (§4.1 unverified); each result one measured change-log row in `design/decisions-r1.md`. That record is 40,408 of 40,960 bytes: before adding rows, move its `## Change-log` table out to `design/decisions-r1-changelog.md` whole, leaving a one-line pointer where it stood (the table is the record's tail, so no anchor above it moves), and say so in the first row of the moved table.
- **Act 1's refuter report**, if the charter shows it unsaved: it is written by the first coordinator to `design/ledger-conversion-refuter-1.md` and its folds land in-line in `design/ledger-conversion-r1.md` (16 KB ceiling, at 16,361 bytes: fold by replacing, never by adding). If the file is absent, run one Fable refuter pass yourself with the brief in the charter's handover.
- **The example-app sitting's prompt** (`history/sessions/PROMPT-example-app-init.md`, under 6 KB) is written only if P1 and P2 are merged: `init` in the example-app repo with `scheme = round` and `[legacy]` pointing at example-ops's ledger; the `governs` seed from the archtest classes and the session model's components (decisions-r1 §2.5); the `legacy-map` of ledger-conversion-r1 §5 if the owner has ruled its §10 A; the L3 archtest change (§5). Name the owner's rulings it waits on.

## Exit

The charter's exit line filled; every merged branch green; `history/sessions/NEXT` removed when nothing safe remains, or rewritten to the example-app prompt's path; `main` pushed green only if the sitting prompt's exit line still allows it (the relay run says never push: obey the relay).
