---
status: current
updated: 2026-09-28
owner: the owner
audience: agent
---
# Packet d17: the four-verb redesign

The design of record is example-mac `DECISIONS.md` entry 4 and `example-mac/history/research/2026-09-28-decision-records.md` §6. Read §6 with the record tool (`/Users/you/code/claude-code-session/plugin/scripts/record <file> --section 15`), never whole. Where this packet and §6 differ, this packet holds, because it carries the owner's direction of 2026-09-28 and the choices made inside the design.

Repos in scope: `claude-code-decisions` (the plugin), `example-mac` (one Superseded line only), and `agent-relay` (its ledger and its `decisions/` directory only). Work on `main` in each repo, commit per item, and push nothing. Write commit messages with the Write tool and commit with `git commit -F <file>`. A hook denies shell text that uses the word "rule" as a verb, so never put ledger text or commit text in a heredoc.

## The ledger format

- One `DECISIONS.md` at the repo root. `## In force` holds `### Every session` first when present, then area subsections (`### <area>`). Every in-force entry sits under a `###` subsection. `## Proposed` and `## Superseded` follow; either may be absent.
- An in-force entry is one line: `N. **Title.** paragraph (…YYYY-MM-DD…)`. It ends in a parenthetical that holds a date. The title ends with a period inside the bold.
- A Proposed line is `N. **Title.** one sentence (proposed YYYY-MM-DD; OPEN-QUESTIONS.md)`.
- A Superseded line is `- text naming the replacement, date.` or `N. text …`. Unnumbered lines are legal, since older ledgers dropped their numbers.
- Numbers are unique across all three sections and never reused. Caps: at most 25 in force, at most 7 under `Every session`.
- The caps are rulings, not measurements (noted 2026-10-14, a research fix): the owner set both in example-mac entry 4 (2026-09-25), and d17 builds them. No outside source gives either number. The nearest evidence: adherence falls as instructions multiply (Jaroslawicz et al., "How Many Instructions Can LLMs Follow at Once?", 2025, per the research site's reading, 2026-10-14: Claude Sonnet 4 at 94.4% with 100 instructions and 42.9% with 500), and Anthropic's memory page (<https://code.claude.com/docs/en/memory>, read 2026-10-14) advises under 200 lines a CLAUDE.md. The caps count entries, not bytes. Measured 2026-10-14, one consumer's generated block held four `Every session` entries of 333 to 2,462 bytes and 21 index lines of about 80 bytes, 7,693 bytes in all; at the caps (seven verbatim, 18 index lines) that is about 12 KB at its mean entry and about 19 KB at its longest, and the research site's typical 2,000 to 3,500 bytes an entry gives 14 to 25 KB, loaded in every session.

## The verbs

The CLI keeps the name `decisions`. It finds the ledger at `--ledger PATH`, else `DECISIONS.md` at the git top level of the working directory.

- `show <n>...` prints each entry verbatim, under its section heading. `show --area <name>` prints that whole subsection; the name matches a heading by case-insensitive prefix, and an ambiguous prefix names its candidates. An unknown number or area exits 2.
- `find <word>` prints the title line (number, title, section) of each entry whose title or body holds the word, case-insensitively. No match prints nothing and exits 0.
- `new --title T --stands S --choice C --answers A --recommend R [--report P]` writes the four-part question. It appends `## N. T` to the `OPEN-QUESTIONS.md` beside the ledger, before `## Decided without asking` when that heading exists, with four bold-labelled paragraphs in this order: **Where things stand.**, **The choice.**, **What each answer sets in motion.**, **Recommendation.**. Then come an optional **Report.** paragraph and an empty **Your answer:** line. It also appends the Proposed line for N to the ledger, creating `## Proposed` before `## Superseded` when absent. N is one more than the highest number in the ledger and in `OPEN-QUESTIONS.md`, so an answered question keeps its number as an entry. When `OPEN-QUESTIONS.md` is absent, `new` creates it with a `# Decisions for the owner` heading and an empty `## Decided without asking`. An empty part exits 2 and writes nothing.
- `render [--into PATH] [--check | --lint]` lints the ledger first: section shape, entry shape, unique numbers, both caps. A lint error prints `file:line: message` and exits 1, whatever the mode. `--lint` stops there. Otherwise render builds the block and writes it between `<!-- BEGIN GENERATED: decisions -->` and `<!-- END GENERATED: decisions -->` in PATH. PATH defaults to the `CLAUDE.md` beside the ledger; example-mac passes `--into ~/.claude/CLAUDE.md`. When the markers are absent, the block is appended at the end of the file after one blank line. `--check` writes nothing: it prints a unified diff of what render would change and exits 1 when the block is stale, 0 when fresh.
- The block: one line naming its source and the command that regenerates it; the `Every session` entries verbatim; then one line per other in-force entry, `- N Title (area)`, under a sentence saying `decisions show N` reads one. Proposed and Superseded entries stay out of the block.
- `doctor` stays as the maintenance verb that entry 15 asks of each plugin repo. It is not a ledger verb and changes nothing about the four.

## Dropped

Record files, front matter on entries, the closed tag list, `INDEX.md`, the `governs` map, `decisions/config`, the `rule` verb and its hook (`plugin/hooks/hooks.json`, `plugin/scripts/deny-rule.sh`, `plugin/scripts/test-deny-rule.sh`), `scope`, `against`, `supersede`, `convert`, `stats`, `init`, the `check` and `index` verbs, and the legacy reader. Delete a module and its tests when nothing left uses it. Tests move with the code: the four verbs and the lint get their own tests.

## Acceptance

| id | criterion | proof |
|---|---|---|
| A1 | The CLI has exactly the verbs `show`, `find`, `new`, `render`, `doctor` | `decisions --help` lists them; each dropped verb exits 2 as unknown |
| A2 | `show` prints entries verbatim under their heading; `--area` prints a subsection; unknown exits 2 | tests over a sample sectioned ledger |
| A3 | `find` prints matching title lines, case-insensitive, over titles and bodies | tests |
| A4 | `new` writes the four-part question and the Proposed line with the shared next number | tests: fresh file, existing file, the insert point, an empty part |
| A5 | `render` writes the block between the markers, replaces a stale block in place, and appends when the markers are absent | tests |
| A6 | `render --check` prints the diff and exits 1 when stale, 0 when fresh, and writes nothing | tests with a file hash before and after |
| A7 | The lint catches a duplicate number, 26 in force, 8 in `Every session`, an entry outside a subsection, and an entry without its dated parenthetical | one test per case |
| A8 | The plugin serves the four verbs: commands `show`, `find`, `new`, `render`; the skill rewritten to them; no hook left; version 0.3.0 in `plugin.json`, `marketplace.json` and `pyproject.toml` | `make check` (validate) and a read of `plugin/` |
| A9 | The plugin repo holds no `decisions/` directory and no record file | `ls`; git log |
| A10 | Record 0001 of this repo folds into example-mac `DECISIONS.md` as one Superseded line naming entry 4 as its replacement | the line in example-mac |
| A11 | agent-relay record 0001 folds into agent-relay `DECISIONS.md` as a numbered entry under an area subsection, and agent-relay holds no `decisions/` directory | `decisions render --lint --ledger agent-relay/DECISIONS.md` exits 0 |
| A12 | The plugin's old designs move to `history/design/`, and the old packets (d13 to d16 and the `rows-*.json` files) to `history/packets/`; `design/` keeps this packet and `design/readme/` | `git status`, `ls design` |
| A13 | README and CLAUDE.md in the plugin describe the four verbs and the ledger format, and say nothing of records, tags, the index or the hook | a read; `make check` readme gate |
| A14 | Every repo touched passes its own check | `make check` in claude-code-decisions exits 0; `make check` in agent-relay exits 0 when that target exists; `make status` in example-mac shows no new drift |
| A15 | Every Markdown file touched reads 0 under respeak-measure, fail on error, the resolved technical config, and passes the portfolio doclint | the scratchpad `measure.sh <repo> <files>`; `make -C example-mac doclint REPO=<repo>` shows no FAIL for each repo touched; today the plugin fails `docs.frontmatter` on `CLAUDE.md`, which the A13 rewrite fixes, and agent-relay fails it on `DECISIONS.md`, which the A11 fold fixes |

## Out of scope

example-mac's own reshape into sections, any write to `~/.claude/CLAUDE.md`, the `render --check` line in example-mac `make verify`, the relay's prompt block, the respeak changes, the interpreter wrapper, and any push.
