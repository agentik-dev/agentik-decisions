# Packet d-n3: the ledger's shape, the lint, `answer` and `find` (0.8.0)

| item | value |
|---|---|
| from | `NICE_TO_HAVE.md` at main 01431da, lines 11 (F7), 12 (F9), 13 (F10), 14 (F11), 17 (F14), 21 (d18 1b F5), 22 (1b F6), 23 (1b F11), 24 (L1 takes `amended`), 25 (fenced `## `), 30 (2a F5), 31 (2a F7), 32 (`--area` not stripped), 33 (L2's case), 35 (the success line), 36 (two copies), 43 (D19 left open 2a F7), 51 (the observer, check-in 96: `?.`); the observer's sort, 2026-10-12 18:55 |
| pin | branch `d-n3` off main at 01431da; worktree `.claude/worktrees/d-n3`; a hand-run builder, not a relay row |
| wall | this repo only. No push, merge, `--amend` or rebase. No `make check` or `make install`: this plugin is read from its repo dir; run the test modules named here, `make test`, `make doclint` and `make hygiene`, and `make readme` once, last, with `RESPEAK_RENDER_WALL=1200`. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never build a `relay` binary or run a `relay` verb. Tests set `HOME` and the XDG dirs to temp dirs; no live `claude` in a test |
| may touch | `src/decisions/ledger.py`, `src/decisions/questions.py`, `src/decisions/ask.py`, `src/decisions/answer.py`, `src/decisions/lookup.py`, `src/decisions/cli.py`, `src/decisions/common.py`, `plugin/commands/answer.md`, `plugin/skills/ask/SKILL.md`, `plugin/skills/decisions/SKILL.md`, `tests/test_ledger.py`, `tests/test_new.py`, `tests/test_answer.py`, `tests/test_ask.py`, `tests/test_lookup.py`, `tests/test_cli.py`, `tests/test_plugin.py`, `tests/fixtures/`, the three manifests, `design/readme/source.md`, `README.md` and `design/readme/rendered.sha256` (by `make readme`), `design/packets/d-n3-shape-lint-answer-find.md`, `NICE_TO_HAVE.md`, `history/sittings/*.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_ledger tests.test_new tests.test_answer tests.test_ask tests.test_lookup tests.test_cli tests.test_plugin 2>&1 \| tail -1` reads `OK`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_ledger -k l1_ -k l2_fate -k l3_ -k one_final 2>&1 \| grep -c ' \.\.\. ok$'` reads 8 or more; `grep -c 'def final_parenthetical' src/decisions/*.py \| grep -c ':1$'` reads 1; `grep -c '"version": "0.8.0"' plugin/.claude-plugin/plugin.json` reads 1; `grep -c '^# Packet d-n3:' design/packets/d-n3-shape-lint-answer-find.md` reads 1 |
| budget | one builder sitting; one commit per act; act 1 the red tests |
| verify | the observer runs `render --lint` over every real ledger on this Mac against main's results, then `make check` before the merge, once no relay verb is live |

## 1. What the source says

The eighteen lines in the `from` row, quoted in `NICE_TO_HAVE.md`; each names its fix. In short:
1. F7: after an unknown `## ` heading, `show` and `find` reset both the section and the area, so no entry lands under the area before it.
2. F9 and line 51: the Proposed line's first sentence does not cut at a common abbreviation (`e.g.`, `i.e.`, `etc.`, `vs.`); a title may end in `?` or `!`, the shape takes `?**` and `!**` as the title's end, and `ask` (the Proposed line) and `answer` (the entry) add no `.` after a title that already ends in `?` or `!`.
3. F10: a `## Decided without asking` heading with trailing text is matched by prefix, so `new` appends inside that section.
4. F11: the lint refuses an entry in force whose body is only its parenthetical, and a Proposed line whose tail does not name `OPEN-QUESTIONS.md`.
5. F14: the README and `find --help` say `find` prints `N Title (area or section)`.
6. 1b F5: `answer`'s `--area | --amends | --no-entry` group is required in argparse, so the usage shows no brackets and the refusal is argparse's exit 2.
7. 1b F6, line 32 and line 35: `answer --area` strips its value and resolves it through `lookup.pick_area` (a prefix, a leading "The" dropped), so a near-miss reaches the existing area; the success line prints the heading matched, not the text typed. An ambiguous or unmatched name keeps today's behavior for a new area (a new `### ` heading) only when no prefix matches; two matches refuse.
8. 1b F11: L3 skips the front matter as `ledger.parse` does, so a `# ` comment there is not the first H1.
9. Line 24: L1 does not take `amended` (as in `(2026-09-28; amended 2026-09-29)`) as naming a source.
10. Line 25 and 2a F5: L3 ignores a `## ` line inside a code fence, flags two `## N.` blocks with one number, and flags two option labels equal ignoring case.
11. 2a F7 and line 43: L1 finds the date at the tail's start only; `answer --amends` refuses an entry whose tail is missing or does not open with a date, and writes nothing.
12. L2's fate phrases (`Superseded by`, `Replaced by`, and the rest) match ignoring case.
13. Line 36: one `final_parenthetical` (in `ledger.py`) and one `ANSWERED_LINE` (in `questions.py`); the other modules import them.

## 2. Rulings

Act 1 commits the red tests, failing, before any fix: `test_lookup.Show.test_an_unknown_section_resets_the_area`; `test_new.Titles.test_a_question_title_takes_no_period`, `test_the_first_sentence_passes_e_g`; `test_new.New.test_a_decided_heading_with_trailing_text`; `test_ledger.Shape.test_l1_body_only_a_tail_and_proposed_without_open_questions`, `test_l1_amended_is_not_a_source`, `test_l1_the_date_opens_the_tail`, `test_l2_fate_ignores_case`; `test_ledger.Questions.test_l3_skips_front_matter`, `test_l3_fenced_heading_and_repeated_number`, `test_l3_labels_equal_ignoring_case`, `test_one_final_parenthetical`; `test_cli.Verbs.test_find_help_says_area_or_section`, `test_answer_needs_area_amends_or_no_entry`; `test_answer.Answer.test_area_prefix_resolves_and_prints_the_heading`, `test_amends_refuses_a_tail_without_a_date`, `test_area_is_stripped`, `test_a_question_title_takes_no_period`. A name may change to fit the module; the assertion may not.

A stricter lint must not turn a real ledger red. Before the fix round ends, copy each `DECISIONS.md` one directory below this repo's parent into a temp dir and run `render --lint` on it under main and under the branch; the exit codes and problem lines must match, except where a ledger already fails on main. A new check that turns a passing real ledger red is narrowed until it passes, and the narrowing is logged in one sentence; if no narrowing keeps the defect closed, the item is left open in `NICE_TO_HAVE.md` with the ledger's line as its repro. Copies only: never write in another repo.

Decide what §1 leaves open and log it in one sentence. Remove from `NICE_TO_HAVE.md` the items closed. What lies outside §1 goes to `NICE_TO_HAVE.md`. If items 5 and 6 cannot land with the README render, they may carry: file them back and say so.

## 3. Interfaces

The lint (L1 to L3 stricter, as §1 items 4 and 8 to 12 say); `answer` (`--area` resolved and stripped, the lands group required, `--amends` refusing a dateless tail, no `?.`); `ask` (no `?.`); `show` and `find` (an unknown section resets the area); `find --help`. Version 0.8.0.

## 4. Findings that name this row

The eighteen `NICE_TO_HAVE.md` lines in the `from` row.

## 5. Forbidden reads

Transcripts whole; anything under the relay's state directory; other repos beyond copying a ledger for a lint probe.

## 6. Report

At most 250 words: each act's commit, each red test before and after, each acceptance line's result, the real-ledger lint probe (main against branch), `make readme`'s result, behavior changes callers will see, the choices made, any note filed.
