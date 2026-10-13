# Packet A3: `show` and `scope`, with the legacy fallback

| item | value |
|---|---|
| from | `design/decisions-r1.md` §2, §3.1 to §3.4, at `8bb67d8`. YOU DO NOT READ IT (§5) |
| where | worktree `.claude/worktrees/core`, branch `core` from `8bb67d8` |
| may touch | `src/decisions.py`, `tests/**`, `Makefile`, `pyproject.toml`, `.claude-plugin/marketplace.json`, `plugin/.claude-plugin/plugin.json`; nothing else |
| acceptance | `make check` exit 0 under `/usr/bin/python3` (3.9.6); §3's commands print what §3 says |
| budget | 120 turns; commit per item on `core`, messages ending `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`; never push, amend or rebase |

## 1. What the record says (quoted whole, `design/decisions-r1.md:<line>`)

Shape (`:87`): "One file, `src/decisions.py`, `#!/usr/bin/python3`, 3.9-compatible, stdlib only, under a thousand lines."

Conventions (`:93`, `:95`): "The repo root is found by walking up from the working directory to a `decisions/config`; `--dir <path>` overrides." "Exit codes: 0 the answer or the gate holds, and `scope` always; 1 when `show` finds nothing, or when `index --check`, `render --check`, `check` or `stats --ceilings` refuses; 2 usage, an unreadable file, a malformed record, a missing config, or a writing verb's refusal (`init`, `new`, `supersede`, `rule`)."

The file (`:27`): "One record is one file, `decisions/<id>-<slug>.md`, UTF-8, LF." Front matter (`:31`): "Between two `---` lines, a flat `key: value` block. The tool parses it itself, stdlib only: scalars, and lists written `[a, b]`." Fields (`:35-42`): `id`, `date`, `status`, `governs`, `supersedes`, `superseded-by`, `consumers`, `verify`. Statuses (`:57-63`): `proposed`, `in-force`, `superseded`, `retracted`, `spent`. Body headings in order (`:48-51`): `# <title>`, `## Words`, `## Decisions`, `## Record`. (`:50`) "Each is one paragraph beginning `(n)`, n contiguous from 1, and each ends with one line beginning `Rejected:` naming the shape not taken and why, in one sentence."

The verbs (`:106-107`):
| `show <id> [n]` | an id; optionally a sub-decision number | the record whole (a legacy entry: its marker index, §3.4), or sub-decision n; header line `<id> (n) <status> <date> governs=<tags> <file:line>`, and for a legacy id `<id> (n) standing: <standing> <file:line>` | 1 not found; 1 when n does not exist |
| `scope --governs X [--status S] [--full]` | one tag; status default `in-force` | one line per matching sub-decision, `<id> (n) <status> <first sentence> <file:line>`, the first sentence being the span's text after its marker up to its first `. `, cut at 120 characters; ids in numeric order (round, n, then a letter suffix) and n within an id; legacy rows after the record rows (§3.4); `--full` prints the paragraphs; ends `# <k> rows` | 0, even when empty (a config with no records is empty, not missing) |

Config (`:71-79`): INI, `configparser`; `[ids] scheme`; `[legacy] ledger`, `index`.

Legacy (`:123`): "`show <id> [n]` reads `decisions/` first, then the ledger." (`:125`) "**Form A**, a line at column 1 beginning `R<r>-<n>. `, where n may carry a one-letter suffix that makes its own id (`R23-1a` at `reference/example-ops/OWNER-DECISIONS.md:314`, `:325`, `:343`; 148 such lines; an indented line that begins with an id is a continuation or a refinement, `:874`, `:883`, `:914`, never an entry; one entry line opens with two ids, `:710`, R15-1 narrowing R13-2, and the entry's id is the first). The entry runs from that line to the line before the next column-1 id line or the next `#` heading, trailing blank lines dropped." (`:126`) "**Form B**, one line beginning `- **R<r>-<n> (<date>)` (66 lines). The entry is that line".

Markers (`:128`): [...] "The rule: markers are searched after the headline, which is the first `**...**` span of the entry's first line, Form A or B; bold markers are preferred when the entry has any; a `(n)` that follows an id token, as in `R25-60 (5)`, is a citation, not a marker; sub-decision n is the span from its marker to the next marker or the entry's end. `show <id>` with no n prints the header and one line per marker, `(n)` and its first sentence, and an entry with no markers whole. The header line prints the ledger line number. A missing n exits 1 with `no (n) in <id>`."

Standing (`:130`): "Standing comes from the hand index: the row beginning `| <id> |` and its fifth cell, mapped on the cell's opening words. A cell beginning `IN FORCE` prints `in-force`; beginning `SUPERSEDED by R<r>-<n>` prints `superseded by R<r>-<n>`; beginning `SPENT` prints `spent`; the rest of the cell, a decoration such as `(built)`, follows the status on the same line; any other cell, such as `half SPENT; the deletion half is IN FORCE` (`reference/example-ops/OWNER-DECISIONS-INDEX.md:211`), prints `mixed: <cell>` verbatim and matches no `--status`; no row prints `not indexed`."

Legacy scope (`:132`): "`scope --governs X` reads the records, then the index: rows whose fourth cell contains X, case-insensitively, and whose standing maps to `--status` (`superseded by R<r>-<n>` matches `superseded`; a `mixed:` cell matches nothing), printed after the record rows in index order as `<id> legacy <status> <third cell> <file:line>`, the same line under `--full`. The index's `governs` column is free text, so this is a substring match, and the one count line says so whenever a legacy row is present: `# <k> rows (legacy rows by substring over the hand index)`. A legacy row never prints a sub-decision number, because the index has none."

## 2. Rulings that bind this row
`CLAUDE.md`: stdlib python3, `#!/usr/bin/python3`, 3.9-compatible, one module, `unittest`, no dependencies.

## 3. Interfaces and the tests that gate them
exposes: `main(argv) -> int`; `[project.scripts] decisions = "decisions:main"` (setuptools, src layout).
Fixtures: `tests/fixtures/sample/decisions/` (`scheme = sequential`; `governs` with two tags; `0001` proposed, `0002` in-force with two sub-decisions, `0003` superseded); `tests/fixtures/legacy/decisions/config` whose `[legacy]` names the two `reference/example-ops/` files relative to the repo root.
Tests: front-matter round trip and refusals; `show 0002` whole; `show 0002 2` prints the paragraph plus its `Rejected:` line; `show 0002 9` and `show 9999` exit 1; `scope --governs <tag>` prints in-force rows only, numeric order, then `# k rows`; `--status proposed`; `--full`; an empty scope exits 0 with `# 0 rows`. LEGACY: `show R25-87 3` prints the 255-byte span beginning `(3) The window:`, `standing: not indexed`, line 1641; `show R25-63 4` prints the 180-byte span beginning `**(4) THE L3 FORCING FUNCTION IS KEPT**`, line 78, standing `in-force`; `show R25-86 13` prints a 237-byte span, line 45; `show R25-86` prints the header and 23 marker lines; `show R16-2` prints lines 671 to 685 whole (Form A, no markers); `show R16-2 1` exits 1; `scope --governs rigor` prints `R24-7 legacy in-force rigor is tiered reference/example-ops/OWNER-DECISIONS-INDEX.md:195` then `# 1 rows (legacy rows by substring over the hand index)`.
`make check`: unittest under `/usr/bin/python3`; pyflakes only when it imports, else one line saying absent; line 1 of `src/decisions.py` is `#!/usr/bin/python3`; `ast.parse(feature_version=(3, 9))` over `src/`, `tests/`. Stubs: `.claude-plugin/marketplace.json` with `"source": "./plugin"`; `plugin/.claude-plugin/plugin.json`: name `decisions`, version `0.1.0`, one-sentence description, author the owner.

## 4. Findings that name this row
Folded into §1. Open as HOW: the refusal messages' wording.

## 5. Forbidden reads
the record; `README.md`; `research/`; `history/` except this packet; `reference/` except the two fixtures (grep and sed, never whole) and `reference/example-ops/cite-check.py:1-90` (the pattern).

## 6. Report (one table, five bullets, under 800 words)
- packet sufficient: yes | no, and what was missing
- items built, each with its commit; what you decided that the packet left open (a gap in the WHAT stops you there, as a report line)
- the acceptance run, exit lines only, plus `wc -c` of `show R25-87 3` and of `scope --governs rigor` over the legacy fixture
