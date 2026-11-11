# Packet d35: `answer` keeps what the owner typed in a question block

| item | value |
|---|---|
| from | the suite review of 2026-11-10, agentik-decisions finding 1; NICE n2, n17; d28; d30 ruling 5; d31 and d34 ruling 5. No entry is carried: this repo keeps no DECISIONS.md (`CLAUDE.md:17`); hq 8 and hq 9 bind `answer`, cited by number |
| pin | main 5b18ff5 (0.18.2); the bump is 0.19.0, a packet's minor as d31 to d34 took; worktree `.claude/worktrees/d35-answer-keeps-owner-text`, branch `d35-answer-keeps-owner-text` |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install`, `install-cli`, bare `make` or `make readme`; never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state; no test reads a live ledger |
| may touch | `plugin/lib/decisions/{answer,common}.py` (`common`: `VERSION` only); `tests/test_{answer,answer_head,bare_machine,plugin}.py`; `plugin/commands/answer.md`; `plugin/skills/{ask,decisions}/SKILL.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `CLAUDE.md`; `NICE_TO_HAVE.md`; this packet as `design/packets/d35-answer-keeps-owner-text.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib /usr/bin/python3 -m unittest -v tests.test_answer_head tests.test_answer 2>&1 \| grep -c ' \.\.\. ok$'` reads 64 (5b18ff5 with the probes' file: 56), and under 3.12.7; `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last |
| budget | a commit per group by explicit path, the packet and the charter first; stop at 90 tool calls or 140k context with a resume line; `claude-opus-5-5` |

## 1. What the source says

Run 2026-11-10 at 5b18ff5 on scratch copies; the probes are `PACKET-2026-11-10-decisions-d35-probes/`.

- `questions.make_block` gives each line of a block to a part; `Block.stray` holds only a line no part takes. `answer.pick` refuses `--pick` for a stray line (d30 ruling 5) and for a **Your answer:** line that is not the picked label (d28); `remove_block` then drops the block. No copy is kept.
- So text typed inside a part leaves with it, exit 0: at the end of an option's line (B), in a part's paragraph (C), as an option line of the owner's own (D), under `**Report.**`. `probe-answer.sh`, rerun by the coordinator: the words are in neither file after, and were never committed (NICE n2, S1; n17).
- hq 9: "`answer` writes the owner's choice as an entry." hq 8, by d30 ruling 5: the owner's line never enters DECISIONS.md.
- `render --fold-tails` (d31) and `expire --write` (d34 ruling 5) refuse until HEAD holds what they cut; `selector.write_back` lets `ask` rewrite a block's prose in place.
- `tests/test_answer.py`: 53 cases, none in a git work tree.

## 2. Rulings

1. **The base.** Under `.new.lock`, once block N is found, `answer` reads block N from HEAD's blob of the questions file, as `render.head_holds` reads one: in the real path's directory, each git child under `GIT_TIMEOUT`.
2. **The owner's lines.** Each non-blank line of the working block above its **Your answer:** line that the base lacks, in order; runs of spaces count as one, and each base line holds one. A line deleted since the commit is none. The answer line and what is under it stay d28's T.
3. **`--pick`** with such a line exits 2 and writes nothing: the refusal says the block holds lines HEAD's copy lacks, names `--other` and a commit as the ways out, then lists each line (the words of `d35-answer.patch`). The order: no open question N; ruling 5; an unknown label; d30's stray lines, its words unchanged; these lines; d28's T.
4. **`--other X`** keeps them: `Other: X; the owner's line: W`, W being d30's stray lines, then these, each once, then T.
5. **No copy, no answer.** When git holds no copy of question N, `--pick` and `--other` both exit 2 and write nothing: `answer: git holds no copy of question N (<why>), so answer cannot tell what was typed into its block`, then the way out, a commit of OPEN-QUESTIONS.md. `<why>`: `no commit to read there` (no work tree, or no commit), `HEAD does not hold <name>` (untracked), `HEAD's <name> holds no question N` (put since the commit), `git cannot read it: ...` (git absent, past its bound, a blob not UTF-8).
6. **A block `ask` reworded after its commit** reads as ruling 2's lines: `--pick` exits 2 and lists them, and after a commit the rerun passes. The `ask` skill gains the step: after `ask` returns, read `git diff OPEN-QUESTIONS.md`, commit both files by path, then ask the owner.
7. **What it does not see.** Text typed before the block's last commit leaves with the block; git holds it: a NICE row (S3), not this packet. `ask`, `new`, `render`, the lint, `questions.py` and `selector.py` stay.
8. **Texts and 0.19.0**, last. The four version places; `answer.py`'s docstring; a sentence each in `answer.md` and the two skills, ruling 6's step in `ask`; CLAUDE.md's design list. README and source alike by hand: line 144 becomes the sentence below and line 153 (`A line no part of its block takes, ...`) goes: 397 B to 383 B, the file 24,575 B to 24,561 B, cap 24,576; the Status line and the `--version` row keep their widths (`0.19.0`, `514`). Nothing moves out.

> `answer` reads the owner's text on the **Your answer:** line and under it: text that names an option takes only `--pick` of it; other text, a line no part of the block takes and a line HEAD's copy of the block lacks refuse `--pick` and stay in the Answered line under `--other`, as `Other: X; the owner's line: T`, never in the ledger; with no copy in HEAD it exits 2: commit first.

## 3. Interfaces: the tests, then the prototype

The probes' `test_answer_head.py` becomes `tests/test_answer_head.py`: 11 cases. At 5b18ff5, 3 ok and 8 red under 3.9.6 and 3.12.7. On the prototype (`d35-answer.patch`, `answer.py` alone), 11 ok under both.

| T | test | holds |
|---|---|---|
| 1 | `test_text_at_the_end_of_an_option_line_refuses_pick` | B; no file changes |
| 2 | `test_a_line_typed_into_a_parts_paragraph_refuses_pick` | C |
| 3 | `test_an_option_line_of_the_owners_own_refuses_pick` | D; a `--pick` of it too |
| 4 | `test_a_line_typed_under_the_report_refuses_pick` | n17 |
| 5 | `test_other_keeps_each_line_head_lacks_in_the_answered_line` | ruling 4 |
| 6 | `test_a_block_reworded_since_its_commit_refuses_pick_until_head_holds_it` | ruling 6 |
| 7 | `test_no_copy_of_the_question_in_head_refuses_pick_and_other` | no tree, no commit, untracked, put since |
| 8 | `test_git_that_cannot_run_refuses` | a PATH without git |
| 9 to 11 | the last three, green today | a block as HEAD holds it; typed text HEAD holds; d30's stray line, once |

Today's tests that change: `tests/test_answer.py`'s fixture commits (`d35-fixture.patch`: `Answer.new` calls the probes' `commit`); with it the prototype reads 42 of 53. Ten of the other 11 (named in `proto-answer-312.log`) write a block or ledger by hand after `new` and take a `commit(self.tmp)` before `answer`; `test_both_files_or_neither` lists the directory and meets `.git`. No expectation of `answer` changes. Three git spawns a case took the file from 0.7 s to 12.8 s under load: make the repo once a class, commit with one spawn. `test_cli`, `test_plugin`, `test_ask`, `test_new`: 80 ok on the prototype; `test_bare_machine` not run.

## 4. Findings that name this row

NICE n2 (S1) and n17 leave; n3 to n16 and n18 stay. New rows: ruling 7's (S3); `--other` keeps a changed line whole, not the typed part alone (S4).

## 5. Forbidden reads

Other repos but `from`'s records and the probes; a real ledger or OPEN-QUESTIONS.md from a test; the relay's state; transcripts.

## 6. Report (six lines)

Each commit; the acceptance readings; the gate's id and line; the README's bytes; the NICE rows; each choice.
