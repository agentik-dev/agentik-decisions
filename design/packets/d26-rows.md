# Packet d26: backlog reads NICE rows

The brief `agentik-hq history/sessions/BRIEF-2026-11-01-d26.md`, in this repo's packet shape (GUIDE §9, doclint): its rows and text as written, home paths named by repo, its four sections under the six headings, and an acceptance row drawn from its §2.

| item | value |
|---|---|
| from | agentik-hq HANDOFF 18 (build 7, the owner's word of 2026-11-01); agentik-hq `design/05-records-as-tables.md` §5, §7 item 1, §2's NICE shape, §1's `backlog` lines, §12 |
| pin | agentik-decisions main cf9f28e, plugin 0.10.1; worktree `.claude/worktrees/d26-rows`, branch `d26-rows` |
| wall | this repo; read agentik-hq and the other agentik repos, never write there; no push, `--amend`, rebase, merge, real `make install`, real `install-cli`; `claude` only as `claude plugin validate` and `claude plugin test plugin`; a test never writes under the live `.local`, `.claude`, `.config` of the home; never touch the home's `.config/agentik/hooks-follow-launcher`; no relay verb; no `kill`, `pkill` or signal from a script; never a gate verb under a temp HOME; zsh here, `bash -c` for bash syntax |
| may touch | `plugin/lib/decisions/backlog.py` and what it needs, `tests/`, `design/d23-backlog-view.md`, `README.md`'s backlog section and its sidecar, `plugin/.claude-plugin/plugin.json`, `NICE_TO_HAVE.md` (bullets, as today), this packet as `design/packets/d26-rows.md`, a charter |
| acceptance | `tests/test_backlog.py` otherwise unchanged and green; the bare-machine test, `tests/test_bare_machine.py`, green; the gate's check green (§2 act 5) |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c "make check > <scratch log> 2>&1"`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the code: read the code from its line |
| budget | One commit per act. **Stop at 100k context or 70 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

## 1. What the source says (quoted)

Read first, by sections: design/05 §1, §2, §5, §7, §12; this repo's `design/d23-backlog-view.md` (its §2 lead forms, §3 build order) and d24's dot form where the code holds it; `plugin/lib/decisions/backlog.py` whole (it is the subject); `tests/test_backlog.py`.

What this is: `agentik decisions backlog` learns the NICE table of design/05 §2, so every repo can convert its NICE after this lands and nothing reds. **Not here:** converting any NICE or HANDOFF (later packets); recordlint (c3); the charter (s52); fixing hq's `build order: none`, which h1 does by adding the marker and the `## The build order` heading.

## 2. Rulings

0. This packet, committed first.
1. **NICE rows.** `nice_items` also reads rows of a table whose header is exactly `| id | level | area | finding | evidence | from |` (after its separator line), under any `##`: the level from the `level` cell (`^S[1-4]$`; anything else is unlevelled, as today), the title from `finding`, spans from `area`, `finding` and `evidence`, the `id` carried in the text view and in `--json`. Cells split on unescaped pipes, `\|` kept (as `:46` does for HANDOFF). The bullet forms and d24's `^S[1-4] ·` stay, for good. Rows and bullets in one file come out in file order. A table under another header yields no items. Tests for each sentence.
2. **`--order FILE`** (design/05 §5; cuttable if it needs more than the parser has). One HANDOFF for every REPO given: an item attaches only to an open step whose `repo` cell is the repo's directory name less `agentik-`, or `suite`. The HANDOFF table is design/05 §2's `| # | item | level | repo | where | state |`; today's reader of digits-first rows (`:207-224`) is its base. Tests: by repo, by `suite`, a done step attracts nothing, no `repo` column falls back to today's view. If cut, say why in the charter and add a NICE line.
3. **Docs.** `design/d23-backlog-view.md` names the row form beside the bullet forms; README's backlog section says rows are read and how to write one; the sidecar by hand if the README has one, no `make readme` if it runs `claude`.
4. **The version.** Plugin 0.11.0, one bump, last (a minor: a new form and a flag). If `plugin-version-check` asks again after a later change, bump the patch.
5. The gate, last.

The stop: stop and report, committing what is there, on: a row form that cannot be read without changing what today's bullet forms place; a test of today's behaviour that must change. A stop is a result.

## 3. Interfaces (signatures, not prose)

`agentik decisions backlog [REPO...] [--order FILE] [--json]`; `nice_items(text)` items gain `id` and `level_from: "cell"` for a row; a step read from a table with a `repo` column carries it.

## 4. Findings that name this row

design/05 §1: `## The build order` fails `PREFIX` (`backlog.py:47`), NICE read as column-0 bullets only (`:165`); §12's S4 citation misses (`view` is `:264-274`).

## 5. Forbidden reads

A file over 8 KB whole, but `backlog.py`, which the brief names whole; a relay ledger; anything outside this repo but the brief, agentik-hq's design/05 and the other agentik repos read only.

## 6. Report (capped)

At most ten lines: the branch and sha; each act's commit; the gate's id and its code from its line; the suite's counts; `--order` built or cut; anything left over, and if you stopped, the exact resume line.
