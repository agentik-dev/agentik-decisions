# Packet d-n2: `new`, `ask` and the respeak child (0.7.0)

| item | value |
|---|---|
| from | `NICE_TO_HAVE.md` at d-n1 9077979, lines 21 (1b F2), 24 (1b F7), 25 (1b F8), 26 (1b F9), 27 (1b F10), 29 (1b F12), 30 (1b F13), 31 (1b F14), 32 (a render may add prose), 35 (the `.decisions-ask-*` temps), 37 (`RESPEAK_DEPTH`), 39 (option 1's description), 40 (`--source`), 47 (`new` counts five words), 51 (`--area` guidance), 59 (the observer, 2026-10-02: the render's child unmarked); the owner's word, 2026-10-12 18:42; the observer's sort, 2026-10-12 18:55 |
| pin | branch `d-n2` off `d-n1` at 9077979 (D22 and d-n1 land first; this branch merges after them); worktree `.claude/worktrees/d-n2`; a hand-run builder, not a relay row |
| wall | this repo only. No push, merge, `--amend` or rebase. No `make check` or `make install`: a relay night is live and this plugin is read from its repo dir; run the test modules named here, `make test`, `make doclint` and `make hygiene`, and `make readme` once, last. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never build a `relay` binary or run a `relay` verb. Tests set `HOME` and the XDG dirs to temp dirs; no live `claude` in a test |
| may touch | `src/decisions/ask.py`, `src/decisions/selector.py`, `src/decisions/speak.py`, `src/decisions/common.py`, `src/decisions/new.py` (or wherever `new` lives), `plugin/skills/ask/SKILL.md`, `.gitignore`, `tests/test_new.py`, `tests/test_ask.py`, `tests/test_selector_describe.py`, `tests/test_plugin.py`, the three manifests, `design/readme/source.md`, `README.md` and `design/readme/rendered.sha256` (by `make readme`), `design/packets/d-n2-new-ask-respeak.md`, `NICE_TO_HAVE.md`, `history/sittings/*.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_new tests.test_ask tests.test_selector_describe tests.test_plugin 2>&1 \| tail -1` reads `OK`; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_ask -k marked_helper -k temp_dir -k answered_block 2>&1 \| grep -c ' \.\.\. ok$'` reads 3 or more; `grep -c 'RESPEAK_RENDER_DEPTH' src/decisions/speak.py` reads 1 or more; `grep -c '"version": "0.7.0"' plugin/.claude-plugin/plugin.json` reads 1; `grep -c '^# Packet d-n2:' design/packets/d-n2-new-ask-respeak.md` reads 1 |
| budget | one builder sitting; one commit per act; act 1 the red tests |
| verify | the observer runs `make check` before the merge, once no relay verb is live |

## 1. What the source says

The sixteen lines in the `from` row, quoted in `NICE_TO_HAVE.md`; each names its fix. In short:
1. F2 and L32: a render that empties a part (a blank line after `**Recommendation.**`) or adds prose (after `**Your answer:**`) is not kept; the original text is.
2. F7: the next number counts the `N.` lines below the legacy marker too.
3. F8: `ask` skips a block whose `**Your answer:**` is filled in; the skill runs `answer` for it first.
4. F9: `ask` does not build a payload from a block the lint refuses (five options); skip it with a warning.
5. F10 and L35: the render runs in a temp dir as `OPEN-QUESTIONS.md`, so respeak scopes keyed on that name apply; no `.decisions-ask-*` temp is left beside the file, and none survives a kill there.
6. F12: in a read-only directory `ask` keeps the text and exits as it does for a failed render, never 1 with no payload.
7. F13 and L47: `new` refuses an option labelled "Other" in any case, and caps the first label at four words.
8. F14: a failed render's warning carries the renderer's first stderr line.
9. L37 and L59: the render's `claude -p` child runs as a marked helper: `CLAUDE_SESSION_HELPER=1`, `CLAUDE_SESSION_DEPTH` one more than the caller's, refused past depth 2, and respeak's own guard `RESPEAK_RENDER_DEPTH` set, as `scripts/readme-render` does.
10. L39: option 1's description states the effect once, with a stop before the recommendation.
11. L40 and L51: the ask skill says what `--source` carries and how to choose `--area` from the areas `show` lists.

## 2. Rulings

Act 1 commits the red tests, failing, before any fix: `test_ask.Ask.test_a_render_that_empties_a_part_keeps_the_text`, `test_an_answered_block_is_not_asked`, `test_a_block_the_lint_refuses_is_not_asked`, `test_the_render_reads_open_questions_md_in_a_temp_dir`, `test_a_read_only_directory_keeps_the_text`, `test_a_failed_render_warns_with_its_first_stderr_line`, `test_added_prose_after_the_answer_line_keeps_the_text`, `test_the_render_runs_as_a_marked_helper`; `test_new.New.test_the_next_number_counts_legacy_entries`; `test_new.Options.test_an_other_label_refused`, `test_a_five_word_first_label_refused`; `test_selector_describe.Describe.test_a_restated_effect_appears_once`; `test_plugin.StructureTest.test_ask_skill_names_source_and_area_choice`. A name may change to fit the module; the assertion may not. `test_ask.Ask.test_one_render_beside_file` contradicts item 5: rewrite it so the render's working directory still carries the repo's respeak config (copy or point at it) while the file is named `OPEN-QUESTIONS.md` in a temp dir. Decide what §1 leaves open and log it in one sentence. Remove from `NICE_TO_HAVE.md` the sixteen items closed. What lies outside §1 goes to `NICE_TO_HAVE.md`.

## 3. Interfaces

`ask` (skips answered and refused blocks with a warning; the render as a marked helper in a temp dir); `new` (refuses "Other" and a first label over four words). Version 0.7.0.

## 4. Findings that name this row

The sixteen `NICE_TO_HAVE.md` lines in the `from` row.

## 5. Forbidden reads

Transcripts whole; anything under the relay's state directory; other repos beyond reading a ledger for a lint probe.

## 6. Report

At most 250 words: each act's commit, each red test before and after, each acceptance line's result, `make readme`'s result, behavior changes callers will see, the choices made, any note filed.
