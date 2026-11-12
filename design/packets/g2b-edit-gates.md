# Packet g2b (decisions side): render and answer list what they write; the skill's steps 6 and 7

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief g2b (hq `history/sessions/BRIEF-2026-11-12-session-g2b-edit-gates.md` §5); design of record hq design/09 §7.2 "The edit gates" at hq 39e1a63; refuter r1: proceed. Its sister: agentik-session branch `g2b-edit-gates` (the gates, g3, `gates write`) |
| pin | main at `5e57f3f` (0.21.1). Version 0.21.2 (the listing), 0.21.3 (the skill), 0.21.4 (in every version place). Worktree `.claude/worktrees/g2b-edit-gates`, branch `g2b-edit-gates` |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state |
| may touch | `plugin/lib/decisions/{render,answer}.py`; `plugin/skills/instruct/SKILL.md`; `plugin/.claude-plugin/plugin.json`; `tests/test_g2b_gates.py` (new); `README.md` and `design/readme/{source.md,rendered.sha256}` if the version is named there; this packet and the sitting's record |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib python3 -m unittest tests.test_g2b_gates` green (absent at the pin: red) |
| budget | shares the builder's 90 tool calls with the session side |

## 1. What the source says: the code at the pin

- `render` writes its target through `common.write_text` (the default target, `--into`, and `--scope tree` in `cmd_tree`); `answer` writes the ledger with `commit_texts` and rewrites the block in `rewrite_block`. Nothing names a written file in any list.

## 2. Rulings: the requirements

- `render` (its default target, `--into`, and `--scope tree`) and `answer` (the ledger and the block it rewrites) add the file they write to its scope's list, once: a file in a checkout (the nearest folder above it holding `.git`) to that checkout's `.claude/edit-gates`, as a path relative to the top level; a file in no checkout (the global file, a tree folder's file) to the user's `edit-gates` in `CLAUDE_CONFIG_DIR`, else `~/.claude`, as a `~/` path under the home folder, else absolute. Never a file under a `tests`, `testdata` or `fixtures` folder. `--check` and `--lint` list nothing.
- The instruct skill: sent by the gate on the owner's own ask in this conversation, it takes that as the typed command, and step 6 asks at once; step 7 writes a gated hand line, page or settings file with `agentik session gates write <file> --from <draft> --preview`, the preview in the question, and on yes `--expect <hash>`; `allowed-tools` gains `Bash(agentik session gates*)`.

## 3. Interfaces: the acceptance table

7. `render --into` twice lists its target once; a target under `tests/fixtures/` is never listed (`tests/test_g2b_gates.py`), and the gate's `make check` exit 0.

## 4. Findings that name this row: ledger, NICE, forks

- hq entries 6, 9 and 17 bind it: the tool keeps its six verbs; the lane's write is the session plugin's.

## 5. Forbidden reads

No transcript, no live state root, no file under `~/.claude`.

## 6. Report

The hq hand-back `history/sessions/HANDBACK-2026-11-12-session-g2b-edit-gates.md`.
