# Packet P3: `check` v1 and `stats`

| item | value |
|---|---|
| from | `design/decisions-r1.md` §2.1 to §2.3, §3.2, §3.3, and `design/ledger-conversion-r1.md` §7, at the commit the builder's prompt names (P1 merged). YOU DO NOT READ EITHER RECORD (§5) |
| where | worktree `.claude/worktrees/p3`, branch `p3` from that commit |
| may touch | `src/decisions.py`, `tests/**`; nothing else. Coordinate with nobody: P2 edits the same module on another branch and the coordinator merges |
| acceptance | `make check` exit 0 under `/usr/bin/python3` (3.9.6); `check` over `decisions/` of this repo exits 0; every earlier test still passes |
| budget | 100 turns; commit per item on `p3`, messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; never push, amend or rebase |

## 1. What the record says (quoted whole, `design/decisions-r1.md:<line>`)

The verbs (`:111`, `:112`):
| `check` | the records | one line per finding, `<file>: <finding>` | 1 on any finding |
| `stats` | the records | counts by status and by tag | `--ceilings`: 1 past a ceiling | v2 |

The lints (`:117`): "`check`, v1: ids unique; the filename begins with the id; the eight fields present and well-formed; `status` in §2.4; `governs` non-empty and within `decisions/governs`; `consumers` non-empty; `supersedes` targets exist and `superseded-by` is symmetric; `## Words` is not the placeholder on any record past `proposed`; `(n)` contiguous from 1, each paragraph with a `Rejected:` line; `## Record` present. `check`, v2: every consumer resolves (a path exists; a test name or make target greps); the overlap lint, a `proposed` record sharing a tag with an `in-force` one must name it in `supersedes` or cite its id in the body; the ceilings, warn above twenty in force per tag and fail above a hundred in force overall (`research/06-evaluation.md:109`). Semantic contradiction stays a reviewer's job (`research/06-evaluation.md:144`)." Only v1 ships here; `--ceilings` is not built and argparse refuses it.

The file (`:27`): "the filename begins with the id so that a directory listing is already an id-ordered index, and `check` refuses a file whose name does not begin with its own id." Front matter (`:31`): "The tool parses it itself, stdlib only: scalars, and lists written `[a, b]`. No other YAML is accepted, and `check` refuses anything else (a nested key, a multi-line scalar, a quoted string containing `]`). Eight fields, every one present in every record, empty lists written `[]`". The fields (`:35-42`): `id`, `date` "`YYYY-MM-DD`", `status`, `governs` "at least one; every tag is a line of `decisions/governs`", `supersedes` "every id exists", `superseded-by` "one id or empty" "symmetric with the successor's `supersedes`", `consumers` "at least one", `verify` "one command line or empty". The body (`:46`): "Four parts, in this order, each introduced by the heading shown; `check` refuses a record missing one." (`:49`): "`new` writes the placeholder `> (the decider's words go here)`". (`:50`): "Each is one paragraph beginning `(n)`, n contiguous from 1, and each ends with one line beginning `Rejected:` naming the shape not taken and why, in one sentence." Statuses (`:57-63`): `proposed`, `in-force`, `superseded`, `retracted`, `spent`.

Conventions (`:95`, `:97`): "1 when `show` finds nothing, or when `index --check`, `render --check`, `check` or `stats --ceilings` refuses; 2 usage, an unreadable file, a malformed record, a missing config". "Unknown is never a pass: an empty result ends with a count line".

Legacy ids, `design/ledger-conversion-r1.md` §7: "`check` resolves a `supersedes` target absent from `decisions/` against the ledger when `[legacy]` is configured: it exists when the ledger has its entry, and symmetry holds when its index row opens `SUPERSEDED by <this id>`."

## 2. Rulings that bind this row
0001 (3): "`governs` is a closed per-repository list in `decisions/governs`; a scoped set is the query `scope --governs <tag>`; a record names its tags; adding a tag is a reviewed commit." `CLAUDE.md`: "the index generated and gated; readers extract, never read".

## 3. Interfaces and the tests that gate them
Coordinator's cuts:
- `check` loads every `decisions/*.md` except `INDEX.md`; a file the parser refuses is a finding (`<file>: malformed front matter: <detail>`), not exit 2, so one bad file does not hide the rest; findings print in file order, one per line, `<relative path>: <finding>`; exit 1 on any finding; with none, one line `# 0 findings over <n> records` and exit 0. The eight-field lint names each missing or extra field. `date` must match `\d{4}-\d{2}-\d{2}`. A legacy `supersedes` target is looked up with `find_entry` and `index_rows`; the symmetry test reads the row's fifth cell; without `[legacy]` an id absent from `decisions/` is a finding.
- The `Rejected:` rule is the core builder's (`history/packets/core-report.md`): exactly one line of the paragraph begins `Rejected:`, and not its first.
- `stats`: prints one line per status in the §2.4 order, `<status>: <k>` (zero included), a blank line, one line per tag of `decisions/governs` in file order, `<tag>: <k> records, <j> in-force`, then `# <n> records`; exit 0; needs the config.
- The sample fixture is corrected to the eight-field rule: `tests/fixtures/sample/decisions/0001-*.md` gains `supersedes: []` and `superseded-by:` (empty); `0002-*.md` gains `superseded-by:`; `0003-*.md`'s `superseded-by: [0002]` becomes `superseded-by: 0002`. Every earlier test that reads the fixture must still pass; if one asserted the old bytes, fix the test and say so in the report.
Tests: `check` over a temp copy of the corrected sample fixture exits 0 with `# 0 findings over 3 records`; one finding each for: a duplicate id, a filename not beginning with its id, a missing field, an unknown status, an unknown tag, empty `consumers`, a `supersedes` target that does not exist, an asymmetric `superseded-by`, the words placeholder on an `in-force` record, a `(3)` after `(1)`, a paragraph without `Rejected:`, a missing `## Record`, a nested YAML key; every finding line begins with the file's relative path. Over a temp copy of the legacy fixture with one record whose `supersedes` is `[R2-4]` (index row `SUPERSEDED by R25-60 (5) ...`): a finding when the record's id is not `R25-60`, none when it is. `check` over this repo's own `decisions/` (`--dir` the repo root) exits 0. `stats` over the sample fixture prints the exact lines for its three records and two tags.

## 4. Findings that name this row
None. Open as HOW: finding wording; whether `check` and `stats` share a loader that tolerates a malformed file.

## 5. Forbidden reads
both records; `README.md`; `research/`; `history/` except this packet, `history/packets/core-report.md` and `history/packets/p1-report.md`; `reference/` except grep and sed over the two pinned ledger files, never whole.

## 6. Report (one table, five bullets, under 600 words), at `history/packets/p3-report.md` on the branch
- packet sufficient: yes | no, and what was missing
- items built, each with its commit; what you decided that the packet left open
- the acceptance run, exit lines only, plus the finding count over `decisions/` of this repo and the test count
