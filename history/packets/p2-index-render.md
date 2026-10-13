# Packet P2: `index [--check]` and `render <target> [--check]`

| item | value |
|---|---|
| from | `design/decisions-r1.md` §3.2, §3.3, §3.5 and `decisions/0001-decisions-as-files.md` (2), at the commit the builder's prompt names (P1 merged). YOU DO NOT READ THE RECORD (§5) |
| where | worktree `.claude/worktrees/p2`, branch `p2` from that commit |
| may touch | `src/decisions.py`, `tests/**`; nothing else |
| acceptance | `make check` exit 0 under `/usr/bin/python3` (3.9.6); the two verbs print, write and refuse what §1 says; every earlier test still passes |
| budget | 100 turns; commit per item on `p2`, messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; never push, amend or rebase |

## 1. What the record says (quoted whole, `design/decisions-r1.md:<line>`)

The verbs (`:108`, `:109`):
| `index [--check]` | the records | writes `decisions/INDEX.md`; `--check` renders to memory and prints the diff instead | 1 when the committed index differs |
| `render <target> [--governs X] [--status S] [--check]` | a file carrying the markers | the scope table between the markers (§3.5); `--check` compares instead | 1 stale; 2 no markers |

The block (`:136`): "`render <target>` finds `<!-- BEGIN GENERATED: decisions -->` and `<!-- END GENERATED: decisions -->` in the target and replaces what lies between them with one heading line naming the generating command and the scope table, LF-terminated, byte-identical on a rerun with the same records. The pattern is example-mac's portfolio block (the live `~/.claude/CLAUDE.md` carries `BEGIN GENERATED: portfolio-map` and `END GENERATED: portfolio-map`; not pinned under `reference/`, so unverified at a pin). `--check` renders to memory and exits 1 when the target differs, printing the diff. Markers absent: exit 2, nothing written."

Conventions (`:95`, `:96`, `:97`, `:98`): "1 when `show` finds nothing, or when `index --check`, `render --check`, `check` or `stats --ceilings` refuses". "Nothing is written outside `decisions/` except `render`'s block between its markers (§3.5)." "Unknown is never a pass: an empty result ends with a count line". "Every output that quotes a record or the ledger carries its `file:line`, so a packet can anchor it".

The index prints the title (`:48`): "`# <title>`: one line, the ruling in about ten words. The index (§3.3) prints it." The scope row (`:107`): "one line per matching sub-decision, `<id> (n) <status> <first sentence> <file:line>`, the first sentence being the span's text after its marker up to its first `. `, cut at 120 characters; ids in numeric order (round, n, then a letter suffix) and n within an id".

## 2. Rulings that bind this row
The owner, 0001 `## Words` (2): "accept, but borrow from best-in-class implementations/research done in this space if good ones exist.  Don't reinvent the wheel if there is some good approach out there already (that we can at least model after if not directly leverage)". 0001 (2): "The index and the corpus root's L3 rows are generated from the records and gated by `index --check` and `render --check`; the hand copies retire. The generator and its gate model themselves on the best existing implementations and leverage one directly where it fits: adr-tools' `adr generate toc` for the one-line-per-record index, and the CI-checked generated index pattern of research/05 §6b; where none fits the stdlib python3 and sub-decision constraints, the shape is modelled after them and the packet names what it models."

What this packet models, and leverages: the index is modelled on adr-tools' `adr generate toc` (one line per record, its title linked to its file, in id order) and not leveraged directly (adr-tools is bash over one-title-per-file directories and knows no front matter or sub-decisions); the gate is modelled on the CI-checked generated index (`research/05-adr-with-agents.md:72`: "regenerated from each record's YAML front matter, with the build failing on divergence"), which `index --check` is; nothing is leveraged directly because the stdlib and sub-decision constraints fit no surveyed tool. The rendered block is modelled on example-mac's portfolio block, unverified at a pin.

## 3. Interfaces and the tests that gate them
Coordinator's cuts:
- `index` writes `render_index(records)` (built by P1; its bytes are fixed there and are not changed here unless a test of P1's is wrong, which you report) to `decisions/INDEX.md`, prints its path, exit 0. `index --check` renders to memory and compares with the file's bytes: equal exits 0 silently; different or missing prints a unified diff (`difflib.unified_diff`, names `decisions/INDEX.md` and `<rendered>`) to stdout and exits 1.
- `render <target>`: `<target>` is a path as given, resolved from the working directory; the file is read as UTF-8; the two marker lines are found whole (each on its own line, exactly the record's text); zero or two-of-one is exit 2 `render: no markers in <target>` and nothing is written. Between them the tool writes: line 1 `Generated by \`decisions render <target>[ --governs X][ --status S]\`; never edited by hand.` (flags echoed only when given, in that order); a blank line; a markdown table with header `| id | n | status | date | governs | decision | where |` and its separator row; one row per RECORD sub-decision in the `scope` order and with the `scope` first sentence, `where` being `<file:line>` as `scope` prints it, `governs` comma-joined; a blank line; a last line `<k> rows.` (for zero rows, `0 rows.`). Legacy index rows are never rendered: the archtest successor holds that "no row lacks a record" over the block. Everything outside the markers is byte-preserved; the marker lines stay. `--check` compares the rendered file to the file's bytes and exits 1 with a unified diff when they differ; 0 silently when equal.
- Both verbs need the config (exit 2 without one). `render` writes the target and nothing else; `index` writes only `decisions/INDEX.md`.
Tests: over a temp copy of `tests/fixtures/sample/`: `index` writes the exact bytes P1's test fixes for three records and `# 3 records`; `index --check` 0 after, 1 after one byte is changed and 1 when the file is removed, the diff on stdout. `render` over a temp target holding text, the two markers with stale lines between, and text after: the exact block for the fixture's in-force rows (0002 (1) and (2)), the surrounding text unchanged; a rerun byte-identical (`filecmp` or bytes equality); `--check` 0 after a render, 1 after the block is edited; a target without markers: 2 and unchanged; `--governs tooling` and `--status proposed` filter rows; an empty selection renders `0 rows.`. Over this repo's own `decisions/` (`--dir` the repo root): `index --check` exits 1 today because no `INDEX.md` exists, and the rendered text has one record line for `0001`.

## 4. Findings that name this row
None. Open as HOW: the diff's exact header lines; how the block finds its markers (a line-wise scan is enough).

## 5. Forbidden reads
the record; `design/`; `README.md`; `research/` except `research/05-adr-with-agents.md:72` (one line, `sed -n '72p'`); `history/` except this packet and `history/packets/p1-report.md`; `reference/` entirely.

## 6. Report (one table, five bullets, under 600 words), at `history/packets/p2-report.md` on the branch
- packet sufficient: yes | no, and what was missing
- items built, each with its commit; what you decided that the packet left open
- the acceptance run, exit lines only, plus `wc -c` of the rendered block over the sample fixture and the test count
