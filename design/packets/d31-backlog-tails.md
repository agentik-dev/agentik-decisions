# Packet d31: `backlog`'s closed leads, and the tail in form T2

| item | value |
|---|---|
| from | agentik-hq `history/sessions/REPLY-2026-11-09-*.md` §b: b3 (S2); `AUDIT-2026-11-09-data-loss-efficiency.md` there: d2 (S4); this repo's `design/d29-churn.md` §7 and the owner's yes to its T2, 2026-11-09; hq entries 8 and 9. This repo keeps no ledger: no entry is carried |
| pin | agentik-decisions main after d29 lands (its head 937cf6c), plugin 0.14.0; worktree `.claude/worktrees/d31-backlog-tails`, branch `d31-backlog-tails` off that main; line numbers are 937cf6c's |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install` or `install-cli`; no `make` outside the gate queue, no `make readme` (it runs `claude`); never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state directory; no test writes under the live home; no gate verb under a temp HOME; python runs with `PYTHONDONTWRITEBYTECODE=1` |
| may touch | `plugin/lib/decisions/{backlog,ledger,questions,answer,render,cli,common}.py` (`common`: `VERSION` only); `tests/test_{backlog,render,answer,ledger,cli,plugin}.py`; `plugin/commands/{backlog,render,answer}.md`, `plugin/skills/ask/SKILL.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `NICE_TO_HAVE.md`; this packet as `design/packets/d31-backlog-tails.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib python3 -m unittest -v tests.test_backlog tests.test_render tests.test_answer -k test_closed_ -k test_t2_ 2>&1 \| grep -c ' \.\.\. ok$'` reads 11 (937cf6c: 0); `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the job's code: read the code from its line |
| budget | 90 tool calls or 120k context, `claude-opus-5-5`; one commit per act by explicit path, the packet and the charter (doclint's five rows) first |

## 1. What the source says: the evidence

Each re-run on 937cf6c, scratch.

- b3 (`backlog.py:35`, `:202`, `:209-227`). F1, the reply's file: ten lines, one open. `backlog` places all ten, five as S1: three by the tally in `## From a review (0 S1, 0 S2, 0 S3, 4 S4)`, their leads `**Closed …**`, `~~` and `[x]` hiding each line's own `S4`.
- d2. d29 (f4ebc71) cut the tail out of the block. The ledger file's tail still gains `; amended <date>, <source>` at each `--amends` (`answer.py:126-127`). T2, the design's §7: `(2026-09-21; amended 4 times, 2026-09-29 to 2026-10-13; amended 2026-10-31, <the latest, whole>)`.
- A T2 tail breaks three things today: the lint refuses it, `entry 1: its tail names a source after the date` (`questions.py:56`); the block reads `amended once` where the tail names four (`render.py`'s `AMENDED`); the sample's entry 3, ending `amended 2026-09-10 (twice))`, would keep no source.

## 2. Rulings

1. **A tally is no level.** `LEVEL` (`backlog.py:35`) skips an `S<n>` after a digit and a space: `## S2: the gate (1 S2)` stays S2, `## 10 S4 left` gives none.
2. **A closed lead is no item.** Closed: a bullet's text, or a row's `id` or `finding` cell, that opens `**Closed`, `~~`, `[x]`, `[X]`, or a bare `Closed` and a date. `nice_items`, the placement and the `carry no level` count leave it out. The text view then ends `N closed, not placed`, only when N is over 0; `--json` gives each repo `closed`, the line numbers, always. `(closed <date>)` inside a lead and `DONE at` stay items: a NICE row.
3. **T2.** A tail is read outside its nested parentheticals. An amendment opens at a `;` or `,` followed by `amended DATE` and runs to the next. The combined clause, `; amended once, DATE` or `; amended K times, DATE to DATE`, counts only before every dated one. T2 is the first date; the combined clause for every amendment but the latest (their count, the first's date and the last's; absent at none); then the latest from `amended` to the tail's end, byte for byte. The first source, each move and each older source go. A tail with no dated amendment, or no opening date, stays.
4. **`answer --amends`** writes T2 with its own amendment the latest, every one the tail held now older. When that cuts text, stdout gains `tail was: (<the old tail>)` after `replaced:`. d19's whole-tail rule (the survey's §1.4) gives way on the owner's word: the cut is printed, the Answered line keeps each answer's source, git keeps the rest.
5. **`render --fold-tails`**, exclusive with `--check` and `--lint`: after the lint, under `answer`'s lock, it rewrites to T2 the tail of each entry in force that T2 shortens, then writes the block as `render` does. With none: `render: no tail to fold in DECISIONS.md`, exit 0. Else HEAD must hold the ledger, tracked and unchanged, or exit 2: `HEAD does not hold DECISIONS.md as it stands; commit it first; nothing written`. It prints `render: folded the tails of K entries in DECISIONS.md, X B to Y B; <short sha> holds them whole`. A T2 tail the lint would refuse stays: `render: entry N's latest amendment names no source, so its tail stays as it stands`, on stderr.
6. **The lint reads T2 and asks for no form.** `questions.TAIL` (`:56`) takes one combined clause before the dated ones; like them it names no source.
7. **The block and T2.** d29's short form is cut from the ledger's tail at each render and T2 shortens that tail in the file, so a fold moves no byte of the block: `short_tail` counts with `ledger.amended(tail)`, the combined clause's count plus each dated amendment; `render.py`'s `AMENDED` goes.
8. **Texts.** `cli.py:21`. README and source, alike, by hand, 24 B under the 24,576 B cap: `:150` restated, a `--fold-tails` row after `:84`, `:86` gains the closed line, and how to find an older amendment: `git log -p -S'amended <the clause's first date>' -- DECISIONS.md` shows the commit that cut it, the whole tail on its `-` line. `render.md`, `backlog.md`, `answer.md`; the ask skill's `:47`.
9. **Version 0.15.0**, last, where d30's ruling 8 lists; the marketplace line is the hq sitting's.

Reversible, the cutter's: the fold is a `render` flag, not a seventh verb; it reads git only with text to cut; a bare `Closed` counts only before a date; `K times` writes `A to B` even when the dates are one.

## 3. Interfaces

`render [--into PATH] [--check | --lint | --fold-tails]`. `backlog.scanned(text)`, `(items, closed lines)`, `nice_items` its first; `ledger.amendments(tail)`, `(older, dated)`: `(count, first date, last date)` and `[(index, date)]`; `ledger.amended(tail)`, an int; `ledger.folded(tail, amendment=None)`, a str; `render.fold_tails(text)`, `(text, numbers folded, numbers left)`; `render.head_holds(path)`, a short sha or None.

F1: the reply's file, inline. F2: a ledger committed in a git work tree: entry 1 (Every session) holds four amendments, two moves and nested dated parentheticals; 4 one; 3 an `amended DATE` decoy in its paragraph and one nested in its tail, then two real; 5 the sample entry 3's tail; 2 none; a Superseded line two.

## 4. Findings that name this row

0 of 11 ok on 937cf6c, 11 on a scratch prototype.

- `tests/test_backlog.py`, three `test_closed_`: `tally_is_no_level` (none, S2, none, S3); `leads_go_to_one_line` (F1: three items, then `7 closed, not placed`); `lines_in_json_and_none_without_one` (`closed` is `[5, 6, 7, 11, 13, 19, 20]`; `Closed captions …` and `**Closedown …**` are items, no line).
- `tests/test_render.py`, seven `test_t2_` on F2: `lint_reads_the_form` (the folded text lints clean); `fold_is_lossless` (three entries folded to the expected bytes; each keeps its line up to the tail, its first date, its count (4, 0, 1, 2, 1) and its latest amendment; `git show HEAD:DECISIONS.md` is F2); `fold_is_idempotent` (again, uncommitted: `no tail to fold`, exit 0, no byte moves); `fold_keeps_nested_parentheses_and_dates` (no decoy counted; 5 untouched, its stderr line; `ledger.unclosed` false for each body); `fold_then_check_passes` (`--check` exits 0 after it); `block_keeps_its_count` (the short block byte-identical; `tails=True` 279 B shorter, what entries 1 and 4 lost); `fold_refuses_what_head_does_not_hold` (a changed ledger, then no git: exit 2, no byte written).
- `tests/test_answer.py`: `test_t2_amends_writes_the_form` (two old amendments become `amended 2 times, 2026-09-10 to 2026-09-12`, `tail was:` printed; again: `3 times`; a never-amended entry: its first date, then the amendment).

Today's tests that change: those asserting a whole tail after `--amends` (`test_answer.py:75`, `:94`, `:449`) restate it in T2; a pinned `--json` shape gains `closed`. The charter shows the eleven red first.

## 5. Forbidden reads

Any other repo, but `from`'s two agentik-hq records and agentik-research's survey (`research/synthesis/tools-decisions.md` §1.4, §2.3, §2.5). The relay's state directory. Transcripts.

## 6. Report (at most six lines)

Each act's commit; each acceptance reading; the gate's id and line; the README's bytes; the NICE rows; each choice, one sentence.
