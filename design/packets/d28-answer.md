# Packet d28: `answer` reads the owner's typed line

| item | value |
|---|---|
| from | agentik-hq `history/sessions/AUDIT-2026-11-09-data-loss-efficiency.md` §2 row d1 (S1), its probe p6 (a) re-run 2026-11-09; hq entries 8 and 9. This repo keeps no ledger: no entry is carried |
| pin | agentik-decisions main 7ca4c03, plugin 0.11.0; worktree `.claude/worktrees/d28-answer`, branch `d28-answer` off main |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install` or `install-cli`; no `make` outside the gate queue, no `make readme` (it runs `claude`); never build a relay binary, run a `relay` or `agentik relay` verb, or write in `~/.local/state/agent-relay`; no test writes under the live home; no gate verb under a temp HOME; python runs with `PYTHONDONTWRITEBYTECODE=1` |
| may touch | `plugin/lib/decisions/questions.py`, `plugin/lib/decisions/answer.py`, `plugin/lib/decisions/common.py`; `tests/test_answer.py`, `tests/test_ask.py`, `tests/test_plugin.py`; `plugin/skills/ask/SKILL.md`, `plugin/commands/answer.md`; `README.md`, `design/readme/source.md`, `design/readme/rendered.sha256`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `NICE_TO_HAVE.md`; this packet as `design/packets/d28-answer.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib python3 -m unittest -v tests.test_answer tests.test_ask tests.test_plugin -k typed 2>&1 \| grep -c ' \.\.\. ok$'` reads 9 (main: 0); `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib python3 -m unittest tests.test_answer tests.test_ask tests.test_plugin tests.test_ledger 2>&1 \| tail -1` reads `OK` (main: 94 OK); `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the job's code: read the code from its line |
| budget | 60 tool calls or 100k context, `claude-opus-5-5`; one commit per act by explicit path, the packet and the charter (doclint's five rows) first |

## 1. What the source says: the evidence

- `answer.py:166-169` calls `pick`, which never reads `Block.answer`; `:194` removes the block. README line 141 and the ask skill's step 5 send the owner to that line.
- Re-run on main. The owner's line: `Stay in hq, and never move the S1 rows out of the audit file`. `answer 2 --pick "Each tool's NICE" --source S --area "The tool" --text P` prints `answer: 2, Each tool's NICE; entry 2 under …`, exit 0; `grep -c "never move the S1 rows"` reads `OPEN-QUESTIONS.md:0 DECISIONS.md:0`.
- The same loss, reproduced at exit 0: `--other`, `--amends 1`, `--no-entry`; and text typed under the line, where `Block.answer` is empty, the lint passes, `ask` asks again and any `answer` deletes it. A line of spaces is empty; `new` writes no placeholder.

## 2. Rulings

T is the block's typed text: what follows `**Your answer:**` on its line and every non-blank line after it to the block's end, joined by one space. T names option K when it equals K's label once `*` and backticks at either end, case, a trailing ` (Recommended)` and a period before or after it are dropped.

1. `Block.answer` is T, `None` with no line, so `ask` skips a block answered under the line, its warning unchanged.
2. T empty: `answer` prints, exits and writes as on main.
3. T names K: `--pick K` is as on main. `--pick` of another option, and `--other`, exit 2 and write nothing: ``answer: question N's **Your answer:** line names the option `K`; pass --pick with it; nothing written``.
4. T is anything else (the picked or another label with a condition, free text): `--pick` exits 2 and writes nothing: `answer: question N's **Your answer:** line says more than a label; pass --other, which keeps the line; nothing written:`, then T on its own line.
5. T is anything else, `--other X`: exit 0; the label, in the done and Answered lines, is `Other: X; the owner's line: T`, or `Other: X` when X equals T ignoring case.
6. T never enters `DECISIONS.md`: an entry restates (hq entry 8), and `--text` stays the caller's. Rulings 3 to 5 hold under `--area`, `--amends` and `--no-entry`, before any write. An unknown `--pick` label keeps its refusal.
7. Texts. The ask skill's step 1 states rulings 3 to 5 and that text under the line counts, its body under 60 lines; `plugin/commands/answer.md` in one sentence; `answer.py`'s docstring. README and source alike: one sentence, at most 300 bytes, after line 143, its bytes from deleting the `0.4.0` and `0.3.0` notes (lines 284 and 285, 334 B): the file is 24,574 B of `test_source_size`'s 24,576.
8. Version 0.12.0, last: `plugin.json`, `pyproject.toml:7`, `common.py:18`, `tests/test_plugin.py:14`, README and source at `:87` and the status line, with the live count `tests.test_readme` asks for; then the sidecar by `shasum -a 256`. The marketplace line is the hq sitting's.

## 3. Interfaces

`Block.answer`: T or `None`. `answer.pick(block, args) -> label`, raising `Refusal`. No new flag.

## 4. Findings that name this row

d1, by test. `tests/test_answer.py`, green on main: `test_typed_empty_picks` (spaces too), `test_typed_label_picks` (`**pin (Recommended).**`). Red on main: `test_typed_other_label_refuses_pick`; `test_typed_condition_refuses_pick` (three modes, both files byte-identical); `test_typed_label_refuses_other`; `test_typed_line_kept_under_other` (the lint green, T absent from the ledger); `test_typed_under_the_line_is_the_answer`. `tests/test_ask.py`: `test_typed_under_the_line_is_not_asked`. `tests/test_plugin.py`: `test_ask_skill_enters_a_typed_line`. The charter shows the seven red first.

## 5. Forbidden reads

Any other repo, beyond the audit `from` names. `~/.local/state/agent-relay`. Transcripts.

## 6. Report (at most six lines)

Each act's commit; each acceptance reading; the gate's id and line; the README's bytes; each choice inside the rulings, one sentence.
