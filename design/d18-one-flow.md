---
status: current
updated: 2026-09-28
owner: the owner
audience: agent
---
# d18: one flow from fork to entry

This is the design of record for version 0.4.0. The packet that builds it is `design/packets/d18-one-flow.md`. Where this design and the packet differ, the packet holds. Paths are relative to this repo. "The cross-repo ledger" is the portfolio's DECISIONS.md, which binds this repo (entries 1, 3 and 4 are cited here).

Today `new` takes one prose `--answers` string (`src/decisions/cli.py:64`). Nothing in `src/` or `plugin/` names AskUserQuestion or respeak, and an answer becomes an entry by hand. The architecture stays: one ledger per repo, one stdlib package, a plugin that carries no data.

## 1. The flow

1. **Record.** A sitting meets a fork the design cannot settle (entry 4) and runs `decisions new --title T --stands S --choice C --option "Label: effect" ... --recommend R [--report P]`. Two to four `--option` flags replace `--answers`, and the first is the recommendation. `new` refuses with exit 2, and writes nothing, when the count falls outside 2 to 4, a label runs over five words, the choice does not end in `?`, or five questions are already open. The block keeps its four labels (`src/decisions/ask.py:35-36`). The options sit under the third label as `- **Label (Recommended).** effect`, the marker on the first option alone.
2. **Ask.** Once per session (entry 1), when the sitting blocks on the owner or at close, the `decisions:ask` skill runs `decisions ask [N...]`, which asks every open question when no number is given. `ask` renders the blocks through respeak (section 3) and writes them back into `OPEN-QUESTIONS.md`. It then prints a JSON list of AskUserQuestion calls built from the rewritten file. The skill passes each call as it stands, back to back in one turn.
3. **Answer.** For each answer the skill runs `decisions answer N (--pick LABEL | --other TEXT) --source S [--text P] [--area A | --amends M | --no-entry] [--into PATH]` (section 1.2).
4. **Headless.** A sitting without AskUserQuestion, such as a relay child, runs `decisions ask` at close for the render alone. The owner answers on the **Your answer:** line, and the next attended sitting records that answer with `answer`.

### 1.1 The field mapping

AskUserQuestion in Claude Code 2.1.284 takes one to four questions per call and two to four options per question. Its header is advised to stay within 12 characters, a label within five words, and the UI adds "Other" itself.

| Field | Filled from |
| --- | --- |
| `header` | `Decision N`, at most 12 characters up to N = 999 |
| `question` | where things stand, then the choice, ending in `?` |
| `label` | the option label; the first ends in ` (Recommended)` |
| `description` | what that answer sets in motion; option 1 adds the recommendation's first sentence |
| `multiSelect` | false; Other covers the rest |

A call holds at most four questions, so five open questions make two calls.

### 1.2 What `answer` writes

- `--pick` matches a label, ignoring case and ` (Recommended)`; no match exits 2. `--other` carries the owner's free text, restated (entry 3).
- By default it writes entry N under `### A`, as `N. **Title.** P (DATE; the owner's answer to decision N, S)`. A names an area by its exact name, ignoring case; an unknown A becomes a new `### A`, last under `## In force`. `--text` is required except with `--no-entry`.
- `--amends M` replaces the paragraph of entry M, which is in force, with P. The tail of M is kept whole, with every earlier `; amended` clause, and gains `; amended DATE, the owner's answer to decision N, S` after it.
- `--no-entry` records an answer that changes no entry.
- Every run removes question N and its Proposed line. It adds `- N. Title: LABEL (DATE; S)` under `## Answered` in `OPEN-QUESTIONS.md`, and makes that section at the end when it is absent. LABEL is the picked label, or `Other: ` and the restated text. `next_number` counts the Answered lines, so N stays retired.
- It holds `.new.lock` and writes both files or neither (`src/decisions/ask.py:127-134`). It lints both texts before it writes: a problem exits 2 and writes nothing. It then rewrites the CLAUDE.md block, beside the ledger or at `--into`, only when the target holds the markers.
- A result with `afkTimeoutMs` is no answer: the question stays open, and the skill does not ask it again that session.

## 2. One entry shape in every repo

The shape is the lint's (`src/decisions/ledger.py:1-10`). The cross-repo ledger and agent-relay pass it today. Two older ledgers, of 393 and 98 entries in other shapes, fail it.

- In force: `N. **Title.** paragraph (YYYY-MM-DD; source[; amended YYYY-MM-DD, source]…)`, one line.
- Superseded: `- What: replaced by X (entry N), YYYY-MM-DD.`, or `merged into` or `lapsed with` in place of `replaced by`.

`render --lint` gains four checks:

- **L1.** An in-force tail names a source after its date: a `;` or a `,`, then text. Today only the date is checked (`ledger.py:86-88`), and agent-relay's entry 2 uses the comma.
- **L2.** A Superseded line holds a date and names its fate: `replaced by`, `merged into` or `lapsed with`. Today it is unchecked (`ledger.py:79-80`; F11 in `NICE_TO_HAVE.md`).
- **L3.** The `OPEN-QUESTIONS.md` beside the ledger, when present. Its first H1 starts with `# Decisions for the owner`. It holds at most five questions. Each question block has the four labels in order, two to four options with only the first marked, and a **Your answer:** line. Questions and Proposed lines match one to one. Under `## Decided without asking`, an optional opening paragraph is followed by `- ` bullets and nothing more. Under `## Answered`, each bullet ends in a `(DATE; source)` tail.
- **L4.** The line `<!-- decisions: legacy below -->` ends the parsed part. The parser stops there, because today it keeps the current section across an unknown `##` heading (`ledger.py:122-127`). Text below the marker yields no entry, area or problem, and counts toward no cap. `find` also searches the text below the marker, and `show --area` also matches its headings. `new` and `answer` write above the marker.

No `migrate` verb: each repo adopts the shape in its own sitting. An older ledger puts an empty `## In force` and the marker above its first old section, then takes new entries in the shape.

## 3. The respeak contract

- **Direction.** decisions calls respeak, and respeak knows nothing of decisions. `plugin.json` declares no dependency. `src/decisions/speak.py` finds respeak by `RESPEAK_ROOT`, else by the newest installed version. That finder moves there from `scripts/readme-render:58-76`, and the script imports it.
- **Render, once per `ask` run.** `respeak-render.sh --mode technical --source <open blocks> --out <temp> --contract <contract> --max-rounds 2`. The temp sits beside `OPEN-QUESTIONS.md`, so the repo's respeak configuration applies. The renderer already gates its output with the measure and retries. The contract is a constant in `speak.py`: keep headings, numbers, bold labels, option labels and ` (Recommended)` exactly, and rewrite only prose. A block that loses one of them keeps its old text. The cost is one model run per batch.
- **Write-back.** The render runs outside the lock. `ask` then takes `.new.lock`, reads both files again, and replaces each block whose text is unchanged since the render. It updates that block's Proposed line to the new first sentence of the recommendation, and writes both files or neither.
- **Absent or failed.** With respeak missing, or a render that exits nonzero, `ask` keeps the file text, warns on stderr, prints the payload and exits 0.
- **hooks.ask.** respeak's hook stays as it is, unbuilt and waiting on the owner. The `ask` payload already meets its checks, so the hook would only cover questions asked outside decisions.

## 4. What changes where

- **CLI.** `new` takes options. New modules serve `ask`, `answer`, the `OPEN-QUESTIONS.md` parser and `speak.py`. L1 to L4 land in `ledger.py`, and L3 reads the parser. `cli.py` registers two verbs (`:48`, `:107`).
- **Plugin.** A new `skills/ask/SKILL.md` drives the selector, and a new `commands/answer.md` runs `answer`. The skill serves `/decisions:ask`, so no `commands/ask.md` is added. `skills/decisions/SKILL.md` section 4 says an answer enters the ledger through `answer`. It also says an agent edits an entry in force only by `answer --amends`, on the owner's answer (today: "never edits", `:45-46`). The command and layout checks in `tests/test_plugin.py` follow (`:12`, `:51`, `:64`).
- **Docs.** The "four verbs" descriptions change in `plugin/.claude-plugin/plugin.json:4`, `.claude-plugin/marketplace.json`, `pyproject.toml:8`, `CLAUDE.md` and the `cli.py` docstring. The README changes through `design/readme/source.md`, then `make readme`.
- **Stays.** `show`, `find`, `render`, `doctor`, the lock, the numbering and the Proposed line.
- **Version.** 0.4.0 in `plugin.json`, `marketplace.json` and `pyproject.toml`. The session plugin's `^0.3` range excludes 0.4.0. The sitting moves it in that plugin's own repo afterwards, outside this packet.

## 5. Packet d18, one sitting

The packet names each test in its acceptance table. In outline:

1. **`new` takes options** (`test_new.py`): `test_two_to_four_options`, `test_first_option_recommended`, `test_choice_ends_in_question_mark`, `test_long_label_refused`, `test_sixth_question_refused`, `test_answers_flag_removed`.
2. **`answer`** (`test_answer.py`): `test_pick_writes_entry_n`, `test_amends_keeps_earlier_amendments`, `test_no_entry_retires_number`, `test_unknown_label_exits_2`, `test_both_files_or_neither`, `test_block_rewritten_only_with_markers`.
3. **`ask` and respeak** (`test_ask.py`, a stub `RESPEAK_ROOT`): `test_five_questions_two_calls`, `test_payload_fields`, `test_one_render_beside_file`, `test_lost_label_keeps_old_text`, `test_ask_writes_back`, `test_no_respeak_exits_0`.
4. **Lint, plugin, docs, version.** `test_ledger.py` covers L1 to L4 with `test_legacy_marker_stops_parsing` among them. `render --lint` exits 0 on the cross-repo ledger and on agent-relay's. `make readme` runs, then `make check` exits 0.

## 6. Decided here, each reversible (entry 1)

- The label stays **Recommendation.** (`ask.py:36`), not the placement report's "Recommended answer".
- Each repo keeps its own `OPEN-QUESTIONS.md` (`ask.py:126`), not one shared file; a cross-repo question goes to the cross-repo ledger's repo.
- Fields carry the four parts, not labels in the question text. Front matter is not linted.
- A selector answer is the owner's act; an agent records it with `answer`.
- The contract is a constant in the package, since the installed CLI cannot read the plugin's files.
- A skill and a command of the same name collide, so the skill alone serves `ask`.
- L1 takes a comma after the date, so agent-relay's entry 2 passes unchanged.
- `ask` renders outside the lock, since a render outlasts the lock's 5-second wait.
- `answer --note` is dropped: nothing in the flow reads it.

## 7. Decided 2026-09-28 (the owner: take the recommendations)

1. `ask` and `answer` are real verbs; the sitting amends entry 4 of the cross-repo ledger, and the builder touches no other repo.
2. An older ledger takes new entries only: the legacy marker ends the parsed part, and show and find still read the text below it.
3. L3 checks the question blocks and the Answered tails, and the Decided lines only as bullets, so no existing ledger breaks.
4. `ask` writes the rendered blocks back under `.new.lock`, both files or neither, then builds the payload from the rewritten file.
5. The measure-and-rerun gate, `metadata.source` and `preview` are cut; a missing or failed respeak leaves the text, warns and exits 0.
6. The "four verbs" descriptions change, and the skill's "never edits an entry in force" gives way to `answer --amends` on the owner's answer.
7. The version is 0.4.0 here; the session plugin's range moves in its own repo afterwards.
8. respeak's hooks.ask stays as it is, unbuilt and waiting on the owner; nothing here defers or reverses it.
