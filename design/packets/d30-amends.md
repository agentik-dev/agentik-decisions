# Packet d30: what `answer` keeps

| item | value |
|---|---|
| from | agentik-hq `history/sessions/REPLY-2026-11-09-*.md` §b: b1 (S1), b2, b4 (S4); `REFUTE-2026-11-09-d28-r1.md` there: F3 (S1); hq entries 8 and 9. This repo keeps no ledger: no entry is carried |
| pin | agentik-decisions main after d28 lands (its head 93d0a0f), plugin 0.12.1, 391 cases; worktree `.claude/worktrees/d30-amends`, branch `d30-amends` off that main; line numbers are 93d0a0f's |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install` or `install-cli`; no `make` outside the gate queue, no `make readme` (it runs `claude`); never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state directory; no test writes under the live home; no gate verb under a temp HOME; python runs with `PYTHONDONTWRITEBYTECODE=1` |
| may touch | `plugin/lib/decisions/{answer,questions,ledger,cli,common}.py` (`common`: `VERSION` only); `tests/test_{answer,plugin,cli,ledger}.py`; `plugin/skills/ask/SKILL.md`, `plugin/commands/answer.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `NICE_TO_HAVE.md`; this packet as `design/packets/d30-amends.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib python3 -m unittest -v tests.test_answer tests.test_plugin -k test_kept_ 2>&1 \| grep -c ' \.\.\. ok$'` reads 9 (93d0a0f: 0); `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the job's code: read the code from its line |
| budget | 80 tool calls or 120k context, `claude-opus-5-5`; one commit per act by explicit path, the packet and the charter (doclint's five rows) first |

## 1. What the source says: the evidence

Each re-run on 93d0a0f, scratch: entry 1, under `Every session` and rendered into a CLAUDE.md, reads `Every landing runs the full check through the gate queue, never a part of it.`; P is `answer 2 --pick "Each tool's NICE" --source S`.

- b1 (`answer.py:104-109` tests length only). `P --amends 1 --text "A red check stops the landing and leaves main where it was."`: `entry 1 amended`, exit 0, lint 0; `grep -c 'never a part of it'` reads 1 then 0 in the ledger and in CLAUDE.md. The reply's probe, a consumer's 830 B entry: the same.
- b2. Entry 16 ends `(2026-10-17; moved from entry 6 (2026-09-12) by entry 11)`; `--amends 16 --text "<its sentences> (2026-10-17; moved from entry 6 The bridge serves tools only."`: exit 0, lint 0, the bracket unclosed in the body.
- b4 (`answer.py:206`, `:264`). At 25 in force `answer 26 --pick YES --source S --area A` exits 2 on `--text is required unless --no-entry`; with `--text`, on `26 entries in force; the cap is 25`.
- F3 (`questions.py:139-145`). L, `Stay in hq, and never move the S1 rows out of the audit file`, typed as J1 ` **Your answer:** L`, J2 `**Your answer: L**`, J5 `**Your answer**: L`, J3 a paragraph above the line, J4 the end of an option's line: each time `P --no-entry` exits 0 and `grep -c "never move the S1"` reads 0 in both files.

## 2. Rulings

1. **A dropped sentence.** O is M's paragraph as `amend_entry` cuts it; its sentences are O through `ask.clean`, cut after each word ending in `.`, `?` or `!`. `--text`, cleaned, keeps a sentence it holds whole, between spaces or its ends. One not kept, without `--shorter`: exit 2, nothing written; the refusal reads `drops K of its N sentences`, names `--add` and `--shorter`, and lists each one on a line after `nothing written:`. The half-length test goes, implied; `replaced:` prints as now.
2. **`--add S`** replaces `--text` under `--amends M`: the paragraph is O, a space, S cleaned; no `replaced:`. Exit 2, `--add takes the place of --text under --amends`: with `--text`, `--shorter`, `--area`, `--no-entry`, or empty. S holds to D22's rule and ruling 3, named as `--add`.
3. **b2.** A `--text` or `--add` with a `(` followed at once by a `YYYY-MM-DD` and never closed (a `)` closes the nearest open `(`): exit 2 in every mode, ``holds a `(` that opens with a date and never closes``. The lint stays (hq entry 9's shape): a NICE row.
4. **b4.** Under `--area` with 25 in force, as the lint counts, exit 2 before the `--text` test: `25 entries are in force, the cap`, then the ways out: a line under `## Superseded`, `--amends M`, `--no-entry`. `new` stays silent: a NICE row.
5. **F3.** A block's parts: the four labels' paragraphs and the `**Report.**` one of `new --report`, each its bold line and the lines under it to a blank; the option lines under the third label; the **Your answer:** line and all under it (d28's T). `Block.stray` is every other non-blank line, in order. With stray lines `--pick` exits 2 in every mode, an unknown label's refusal first: `holds text no part of its block takes; pass --other`, which keeps it, or join it to its part; then each line after `nothing written:`. `--other X` goes in whatever T names, as `Other: X; the owner's line: W`, W the stray lines then T (`Other: X` when X is W, ignoring case). W never enters `DECISIONS.md` (hq entry 8). `ask`, the lint and `selector.loose` stay.
6. **J4 stays open**: text typed into an option's line or a part's paragraph is that part's, and the tool keeps no copy of the block it wrote. NICE row n2 narrows to it. The packet after: b3 (`backlog`'s tally read as a level), the `archive` verb, J4 with it.
7. **Texts.** Rulings 1, 2 and 5: the ask skill's `:42-49` (under 60 lines), `answer.md` (under 31), `answer.py`'s docstring. §3's usage: `cli.py:16`, README `:82`, `answer.md:3`, the skill's `:29`. README and source, alike, by hand: `:150` restated, rulings 4 and 5 a sentence each, on the `0.5.x` notes' bytes (`:282-284`; 66 B were free at 93d0a0f).
8. **Version 0.13.0**, last (a flag), where d28's ruling 8 lists; the marketplace line is the hq sitting's.

Reversible, the cutter's: `--shorter` keeps its name and covers every drop; b2's guard is the verb's, not the lint's; a stray line is refused, not read as the answer.

## 3. Interfaces

`[--text P | --add S]` in `answer`'s usage; `ledger.sentences(paragraph)` and `ledger.dropped(old, new)`, lists; `ledger.unclosed(body)`, a bool; `amend_entry(…, add=None)`; `Block.stray`, a tuple, the last field.

F1: the sample ledger, entry 1 given a second sentence, beside a CLAUDE.md with its rendered block. F2: the sample at 25 in force.

## 4. Findings that name this row

`tests/test_answer.py`, eight `test_kept_`: 0 of 8 ok on 93d0a0f, 8 on a scratch prototype.

- b1: `amends_refuses_a_dropped_sentence` (F1: `drops 2 of its 2`, `drops 1`, three files byte-identical; all kept in another order, exit 0); `add_appends` (F1: ledger and block hold O then S); `add_refusals` (ruling 2's seven).
- b2: `text_with_an_unclosed_dated_bracket_refuses` (three modes; a closed one passes). b4: `cap_refusal_comes_first_and_names_the_ways_out` (F2; then `--amends 3 --add` exits 0).
- F3: `stray_line_refuses_pick` (J1, J2, J5, J3, a line under an option; three modes; byte-identical); `stray_line_stays_under_other` (Answered holds W, the ledger none); `report_line_is_a_part` (`stray == ()`, `--pick` exits 0).
- `tests/test_plugin.py`: `test_kept_ask_skill_says_what_answer_keeps`.

Today's tests that change: `test_amends_refuses_a_paragraph_cut_by_half` gives way to the first, and five that swap entry 3's one sentence pass `--shorter`. The charter shows the nine red first.

## 5. Forbidden reads

Any other repo, but `from`'s two agentik-hq records and agentik-research's survey (`research/synthesis/tools-decisions.md` §1.4, §2.4). The relay's state directory. Transcripts.

## 6. Report (at most six lines)

Each act's commit; each acceptance reading; the gate's id and line; the README's bytes; the NICE rows; each choice, one sentence.
