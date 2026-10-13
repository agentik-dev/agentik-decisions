---
status: draft
updated: 2026-10-11
owner: the owner
audience: agent
---
# d23: the backlog view, and respeak kept optional

This records the owner's answers of 2026-10-11 to the observer's mods study (example-mac `history/observer/2026-10-11.md`, 18:05 and 18:10); this repo keeps no ledger. (1) A static include file ships (section 6). (2) respeak stays optional. (3) decisions gains a backlog view: each repo's NICE_TO_HAVE.md, ordered against its HANDOFF.md build order; nothing in `src/` reads either file today. The levels are the session plugin's (`claude_session/profiles.yaml:44-47`): S1 harm, S2 blocks the goal, S3 the build order, S4 the rest, never ahead of S3 (portfolio entry 15).

## 1. The verb

`decisions backlog [REPO...] [--json]`

- REPO is a directory, by default the working directory's git top level. Each gets its own block.
- It reads `NICE_TO_HAVE.md` and `HANDOFF.md`, writes nothing, takes no lock, runs no model, and ignores `--ledger`.
- Text: `== <name>  build order: HANDOFF.md:<line> "<heading>", <k> open steps` (or `none` and why); the rows in placement order, `step <n>  HANDOFF.md:<line>  <title>` and `<rank> <level>  NICE_TO_HAVE.md:<line>  <title>`; then `<u> of <m> items carry no level (placed as S4)`. A repo without NICE_TO_HAVE.md says so; with two or more REPO it joins one closing `skipped (no NICE_TO_HAVE.md): ...` line.
- `--json`: `{"repos": [{"repo", "nice", "handoff", "order", "steps": [{"n", "line", "title", "done"}], "items": [{"rank", "line", "title", "level", "placed_as", "level_from", "after_step", "span"}]}], "skipped"}`.
- Exit (entry 25): 0 whenever the files could be read, whatever they hold. 2 for usage, a REPO that is not a directory, or a file unreadable or not UTF-8. Never 1, which stays render's.

## 2. Parsing NICE_TO_HAVE.md

- An item is a column-0 `- ` bullet with its indented lines; prose, headings and nested bullets are not items. Its lead is its bold lead, else its text to the first `: ` or `. `, else its first 120 characters (example-app's line 50, `- Refuse a slash in a workflow kind. (workflow.md review S4 (4))`, leads `Refuse a slash in a workflow kind`). Its title is its lead, at most 80 characters.
- A level is a lone token `\bS[1-4]\b` (`S21` is not one), read in three places, the first found winning: the item's lead, in a form below; a sentence `Each line is S<n>.` or `Each line below is S<n>.` under a heading before its first item, as in example-ops; a `##` or `###` heading, over every item to the next heading of its depth or higher, as in agent-relay's `## AR70 ...: notes, no block, S4 (...)`. A token elsewhere is text (example-ops's "calls S3" is AWS). Two in one place: the most urgent wins.
- The lead, trimmed of spaces and a final `.` or `,`, holds a level in four forms only: `^S[1-4]$` (`- S4: ...`), `^S[1-4],` (`- S4, unconfirmed source: ...`), `[,;] S[1-4]$` (session's `- S21 (2026-10-10), S4: ...`) and `\(S[1-4]\)$` (`- **Rename it (S4).**`). A level named mid-lead is text: example-app's `- Row rtfix4 takes findings S1 and S2 of the rt2 review: ...` reads `S4?`.
- An unlevelled item keeps `level: null`, is placed as S4 (a review note's level) and printed `S4?`, never guessed higher. No item is judged landed; an item leaves its file when it lands.

## 3. Reading the build order

- The section is the `##` after the line `<!-- decisions: build order -->`, else the first `##` starting, case-insensitively, with `Build order`, `Open work`, `Next work` or the word `Next`, up to the next `##`. Owner-step lists do not match.
- Steps, in file order: column-0 items `N. ` (example-mac, example-config) and table rows whose first cell is an integer (example-app). A section holding both shapes reads only the first one found, and the other is ignored. The title is the bold lead or the row's second cell, else 80 characters.
- A step is done when its lead (to the first `. `, at most 120 characters) holds the word `done` or `DECIDED`, or a row's last cell starts `done`. Done steps leave the text order.
- With no such section (example-ops, the plugin repos), the level order alone.

## 4. Placement

1. S1, then S2 items, ahead of step 1.
2. Each open step, followed by the S3, S4 and unlevelled items on its path: sharing a backticked span holding `/` or a file extension, compared with a trailing `:N` or `:N-M` cut. An item follows the first such open step.
3. After the last step: unattached S3, then S4 and unlevelled together.

Within each group, file order. No item rises ahead of a step it is not attached to, so no S4 precedes S3.

## 5. Verb, command, skill

A CLI verb (`src/decisions/backlog.py`, registered in `src/decisions/cli.py`) and a command, `plugin/commands/backlog.md`; no new skill. One sentence in `plugin/skills/decisions/SKILL.md`: run `decisions backlog` before taking S4 work. Like `doctor`, it is not a ledger verb, so entry 16's six stay six. The verb lists and `design/readme/source.md` name it; the version moves to 0.5.0.

## 6. The respeak contract (answers 2 and 1)

- Optional, never a dependency: `plugin.json` and `marketplace.json` declare none; respeak knows nothing of decisions. Every verb, test and doctor check works without it; a respeak-only check runs only when respeak is found and skips otherwise, its reason in `tests/skips.allow`.
- The author, who has respeak, generates a default-behavior include file with respeak's author-side verb (a sibling record in claude-code-respeak). decisions ships that file under `plugin/` and imports it from `CLAUDE.md`; users get the behavior without respeak. Its path follows the sibling record.
- Found by `speak.respeak_root`: a set `RESPEAK_ROOT` if it holds `scripts/respeak-render.sh`, else none (the cache is not tried); unset, the highest version tuple under `~/.claude/plugins/cache/*/respeak/<version>/` holding it; `RESPEAK_DEPTH` set, no render.
- Used at run time by `ask` (d18 section 3) alone: absent or failed, the text stays, one stderr warning, exit 0.
- `scripts/readme-render` and the include's regeneration are author-side tools (answer 1 as clarified at 18:10: the author generates the include, users never need respeak). Without respeak they refuse: readme-render exits 2 (`tests/test_readme.py` `test_empty_cache_refuses`), and 1 or 2 on a failed render. That stays: script and test unchanged.
- backlog renders nothing. `doctor` gains a `respeak` line, `ok` with the root or `warn` when absent; a warn never changes the exit.

## 7. Acceptance

`tests/test_backlog.py`, fixtures in `tests/fixtures/backlog/` trimmed from the real files:

- `test_column_zero_bullets_only`; `test_lead_level_wins`, `test_lead_forms_only` (the four; `Row rtfix4 ... S1 and S2` reads `S4?`), `test_intro_sentence_level`, `test_heading_level_covers_items` (the three real shapes); `test_token_elsewhere_is_text` (`calls S3`, `S21`).
- `test_unlevelled_is_s4_marked`: null, `placed_as` S4, `S4?`, the count line.
- `test_marker_beats_prefix`, `test_owner_steps_are_not_order`, `test_numbered_steps_done`, `test_table_steps_done`, `test_first_step_shape_wins`.
- `test_s1_s2_before_step_one`, `test_span_attaches_after_step`, `test_done_step_attaches_nothing`, `test_tail_s3_then_s4_in_file_order`.
- `test_no_handoff_exit_0`, `test_no_nice_exit_0`, `test_not_a_directory_exit_2`, `test_bad_utf8_exit_2`, `test_json_fields`, `test_many_repos_and_skipped`, `test_writes_nothing`.
- `test_backlog_runs_no_render` (a stub renderer leaves no trace), `test_plugin_declares_no_dependency`, `test_include_shipped_and_imported`, `test_suite_green_without_respeak` (empty cache), `test_doctor_respeak_warn_absent`.
- By hand: `decisions backlog` over agent-relay, claude-code-session, example-ops, example-mac and example-app exits 0, and example-app's NICE_TO_HAVE.md:330 prints `S4?`; `make check` exits 0.

## 8. Open risks

- A level in a bullet's tail or mid-lead is missed and reads `S4?`: it errs low, never hides.
- A heading is read whole; one naming a level it does not give lifts its items (none today).
- The heading prefixes fit today's files; a new title needs the marker.
- Done detection by word can misread a lead.
- Row ids (P61, AR71) are not matched, since `S4` and `F1` look alike.
- example-ops's 600 items make a long view; a cap may follow use.
- The plugin repos keep no HANDOFF.md, so no build order yet.
- The include's freshness is checked only where respeak is present.
