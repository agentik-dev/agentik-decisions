# Packet d38: `list_gate` learns the layer, and `render --lint` warns on two couplings

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief d38 (hq `history/sessions/BRIEF-2026-11-12-decisions-d38-gate-layers.md`); design of record hq design/12 §3.2, §3.4, §3.5. A small change by entry 17, cut as a packet because its tests carry it past 50 lines |
| pin | main at `fb2fa97` (0.21.4). Version 0.21.5. Worktree `.claude/worktrees/d38-gate-layers`, branch `d38-gate-layers`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state or writes outside its temp home |
| may touch | `plugin/lib/decisions/render.py`; `plugin/skills/instruct/SKILL.md` only if R1 makes a sentence false; `tests/test_d38_gate_layers.py` (new); `tests/test_tree_scope.py` (one assertion R1 moves: the folder now holds `.claude`); the four version places, `tests/test_plugin.py`, `README.md` and `design/readme/{source.md,rendered.sha256}`; this packet and the sitting's record |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib python -m unittest tests.test_d38_gate_layers` green (at the pin: 12 run, 6 failures, 1 error) |
| budget | about 90 tool calls |

## 1. The owner's words

- Entry 31 (2026-11-12): "The gate lists are layered as the instruction files are. The owner's list, ~/.claude/edit-gates, holds the user-scoped files, the global CLAUDE.md among them. A folder's list covers every repo under that folder. A checkout's list holds its own files. The agentik tools (render, answer, the instruct skill, gates write) write all three layers and manage them alike; no hq writes a member's list by hand."
- Decision 32 (2026-11-12): the coupling checks as a `render --lint` warning, in the public plugin, no ledger entry.

## 2. Rulings

- R1, the layer `list_gate` writes (`render.py:84`; `answer` calls it): in a checkout, its `.claude/edit-gates`, as at the pin; else under the owner's config folder (`CLAUDE_CONFIG_DIR`, else `~/.claude`), the owner's list, as at the pin; else, when the target's own folder is below the home folder, that folder's `.claude/edit-gates`, the line relative to it; else the owner's list. Never under `tests`, `testdata` or `fixtures`. Listed once.
- R2, `render --lint` (both scopes) gains two stderr warnings, exit unchanged: a non-comment line of the ledger's checkout's list that is absolute, starts with `~` or `..`, or whose first segment names a folder beside the checkout; a `/` or `~/` line of the owner's list, outside the config folder, that lies in a git checkout or under a folder below the home folder holding its own `.claude/edit-gates`. A list absent is read as empty.
- R3, a new list's header names no hq and no design number; an existing file keeps its header.
- R4, the instruct skill's page changes only if R1 makes a sentence of it false.

## 3. Acceptance (the brief's six; each a case in `tests/test_d38_gate_layers.py`)

| # | line | at the pin |
|---|---|---|
| 1 | `--scope tree --into <folder>/CLAUDE.md` twice: the folder's list holds `CLAUDE.md` once, the owner's nothing | red (the owner's list took it) |
| 2 | a checkout's target: its list; `<config>/CLAUDE.md`: the owner's; `tests/fixtures/`: nowhere | green |
| 3 | a checkout list with `../plum/CLAUDE.md`, `/abs/x`, `~/x`, `plum/x`: four warnings; a clean list: none | red |
| 4 | an owner's line in a checkout and one under a listed folder: one warning each; under the config folder: none | red |
| 5 | `--lint`'s exit is the same with and without the warnings | green (no warnings to change it) |
| 6 | a new list's header has no `hq` and no `design/` | red |

## 4. Forbidden reads

No transcript, no live state root, no file under `~/.claude`.
