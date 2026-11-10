# agentik-decisions: what a review left open, none of it blocking

The findings a review left that block nothing, one row each in agentik-hq design/05 §2's table; a row leaves when it lands. The bullets before 2026-11-01 are frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet touching an area greps them by path. Of its S1 to S3 items, one is open on main and is row n1; the other, the uv `Executable already exists` stop of `make install`, closed with d25, whose recipe runs `install-cli` (`Makefile:113-116`).

## Open findings

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n1 | S3 | `tests/gates.py` | The gates' pyflakes and 3.12-syntax passes walk only src and tests, so since d25 they miss `plugin/lib`; put `plugin/lib` in `ROOTS`, drop the shebang check of `src/decisions.py`, then remove that checkout runner | `tests/gates.py:16`, `:45-46`, `:94` | 2026-11-01, d25; `history/NICE-2026-11-01.md:77` |
| n2 | S1 | `questions.py`, `answer.py` | Text typed off a column-0 `**Your answer:**` line or the lines under it (a leading space, `**Your answer: T**`, `**Your answer**: T`, a paragraph above, an option line) is deleted, exit 0, on main too; joins the `--amends` packet: `--pick` refuses a line no part takes | `questions.py:139`; probes p2 J1 to J3, p3 J4, J5, p6 | 2026-11-09, d28 review r1 F3 |
| n3 | S4 | `questions.py` | A `## ` line under the answer ends the block, and the condition under it stays as an orphan section, lint 0; lint an unknown `## ` section | `questions.py:115`; probe p2 C2 | 2026-11-09, d28 review r1 F4 |
| n4 | S4 | `questions.py` | An unclosed fence under one question swallows the next; `answer --other` then removes that block and the lint goes red; refuse when a fence under the answer line swallows a `## N.` line | `questions.py:107-113`; probe p5 M8 | 2026-11-09, d28 review r1 F5 |
| n5 | S4 | `answer.py` | When the owner's line holds a label as its prefix, the refusal "says more than a label" misleads: it reads as if no label were named | `answer.py` `pick`; the review's note | 2026-11-09, d28 review r1 note |
| n6 | S4 | `answer.py`, lint | Labels that differ by case alone dead-end: the lint refuses them and `answer` refuses a line that names both, so the block moves only once a label is edited by hand | probe p4 F2 | 2026-11-09, d28 review r1 note |
