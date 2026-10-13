# Packet P1: `init`, `new`, `supersede`, `rule`

| item | value |
|---|---|
| from | `design/decisions-r1.md` §2, §3.2, §3.3 and `decisions/0001-decisions-as-files.md`, at `85b0b21`. YOU DO NOT READ THE RECORD (§5) |
| where | worktree `.claude/worktrees/p1`, branch `p1` from the packet's commit |
| may touch | `src/decisions.py`, `tests/**`; nothing else |
| acceptance | `make check` exit 0 under `/usr/bin/python3` (3.9.6); the four verbs print and refuse what §1 says; the existing 43 tests still pass |
| budget | 120 turns; commit per item on `p1`, messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; never push, amend or rebase |

## 1. What the record says (quoted whole, `design/decisions-r1.md:<line>`)

Conventions (`:93`, `:95`, `:96`): "A verb that needs the config and finds none exits 2." "2 usage, an unreadable file, a malformed record, a missing config, or a writing verb's refusal (`init`, `new`, `supersede`, `rule`)." "Nothing is written outside `decisions/` except `render`'s block between its markers (§3.5)."

The verbs (`:104`, `:105`, `:110`, `:113`):
| `init [--ids sequential\|round] [--legacy-ledger P --legacy-index P]` | none | `decisions/config`, `decisions/governs` (empty), `decisions/INDEX.md` (rendered, empty); prints the two-line retrieval rule for the repo's `CLAUDE.md` | 2 if `decisions/` exists |
| `new --title T --governs a,b --consumer C [--consumer C2] [--supersedes ID] [--id ID] [--record REF]` | the flags | the file, status `proposed`, placeholders in `## Words` and `## Decisions`; prints its path | 2 on an unknown tag, an id collision, no consumer |
| `supersede <old> <new>` | two ids | writes `supersedes` into the proposed `new` and `superseded-by` into the in-force `old`; changes no status | 2 unless old is `in-force` and new `proposed` |
| `rule <id> <status>` | an id and a target status | the transition of §2.4 | 2 on a forbidden transition, the words placeholder, or an agent shell |

`rule` (`:115`): "`rule` is the only status writer. On `in-force` it sets `date` to today, and for every id in `supersedes`, which `supersede` must already have linked back (else exit 2), sets that record's status to `superseded`, in one act; it writes no link. It refuses with exit 2 when the environment carries `CLAUDECODE` (measured 2026-09-22: the Bash tool's shell exports `CLAUDECODE=1`), naming the hook of §4.4 in its message; the hook denies the call before it runs."

Statuses (`:57-63`): `proposed` entered by `new`, left by `rule`; `in-force` left by "`rule` to `spent` or `retracted`; or `rule` of a successor whose `supersedes` names it"; `superseded` entered by "`rule <successor> in-force`"; `retracted` "withdrawn by the owner without a successor"; the last three are never left.

Ids (`:81`): "`new` computes the next id: for `sequential`, max plus one; for `round`, the next n in the highest round found in `decisions/` and the legacy ledger together; `--id` overrides when the owner opens a new round. A collision with any existing id, legacy included, is refused." Field `id` (`:35`): "unique across `decisions/` and the legacy ledger (§3.4); never changes".

`governs` (`:69`): "one tag per line, `tag: description`, `#` comments allowed. `new` and `check` refuse a tag not in it." "`init` writes it empty with a comment header." Config (`:71-79`): INI, `[ids] scheme = sequential` or `round`; optional `[legacy] ledger`, `index`.

Fields (`:36-42`): `date` "the drafting day; `rule <id> in-force` rewrites it to the ruling day"; `superseded-by` "the tool only, by `supersede`, which `new --supersedes` also calls; `rule` never writes it"; `consumers` "at least one"; `verify` empty. Eight fields, every one present, empty lists `[]` (`:31`).

Slug (`:27`): "the title in lower-case words joined by hyphens, at most six words". Body (`:48-51`): `# <title>`; `## Words`: "`new` writes the placeholder `> (the decider's words go here)`; `rule <id> in-force` refuses while the placeholder stands."; `## Decisions`: paragraphs `(n)` each ending with a `Rejected:` line; `## Record`: "`design/<file>.md §<n>`" "or `none`, followed by the reason".

The retrieval rule `init` prints, quoted exactly (`:152`): "Decisions live in `decisions/`; before touching a governed area run `decisions scope --governs <tag>`, and read one ruling with `decisions show <id> [n]`. Never read `decisions/INDEX.md` or the ledger whole; draft with `decisions new`, status `proposed`, and never run `decisions rule`."

## 2. Rulings that bind this row
0001 (1): "drafted `proposed` by agents and moved to `in-force` only by the owner". 0001 (3): "adding a tag is a reviewed commit." `CLAUDE.md`: stdlib, `#!/usr/bin/python3`, 3.9, one module, `unittest`.

## 3. Interfaces and the tests that gate them
Coordinator's cuts (WHAT, fixed here so P2 can build on them):
- `render_index(records) -> str` lives in `src/decisions.py` from this packet; `init` writes its output for zero records. The bytes: line 1 `# Decisions index`; line 2 blank; line 3 `Generated by \`decisions index\`; never edited by hand. Read one ruling with \`decisions show <id> [n]\`; read a scope with \`decisions scope --governs <tag>\`.`; line 4 blank; then one line per record in `id_key` order, `- <id> <status> <date> [<title>](<filename>) governs=<tags comma-joined>`; a blank line; last line `# <k> records`; LF-terminated. For zero records lines 5 and 6 are absent: the count line follows the blank line 4.
- `init` takes the root from `--dir` or the working directory and needs no config; `governs` is the two comment lines of this repo's `decisions/governs:1-2` and nothing else; the two-line rule goes to stdout.
- `new`: the placeholder paragraph in `## Decisions` is `(1) (the sub-decision goes here)` then `Rejected: (the shape not taken, and why)`; `## Record` is `--record REF` or `none; (why there is no record)`. A legacy id collides when the configured ledger has an entry for it or the index has its row (use `find_entry` and `index_rows`). Round scheme: the highest round is the max over records and, when configured, ledger entry ids. `--supersedes ID` writes the file then runs `supersede`'s logic; if that refuses, the file is removed and exit 2.
- `supersede old new`: appends `old` to `new`'s `supersedes` if absent; sets `old`'s `superseded-by` to `new`; 2 when `old` already has a different `superseded-by`. Front matter only, via `render_front_matter`; body bytes unchanged.
- `rule`: allowed transitions are `proposed -> in-force`, `proposed -> retracted`, `in-force -> spent`, `in-force -> retracted`; `superseded` is reached only by the cascade; everything else is 2 with `rule: forbidden transition <a> -> <b>`. The `CLAUDECODE` check reads `os.environ` at call time, so tests clear it with `unittest.mock.patch.dict`.
Tests: every writing verb runs over a COPY of `tests/fixtures/sample/decisions/` in a temp dir; the fixture gains `governs` with lines `format: the record format` and `tooling: the tool`, otherwise unchanged. `init` in an empty temp dir writes the three files with the exact bytes above and prints the two lines; a second `init` exits 2. `new` writes `0004-<slug>.md` with all eight fields and prints the path; unknown tag, no consumer, `--id 0002`: 2; over a temp copy of the legacy fixture `--id R25-87` and `--id R16-2` exit 2, and under `scheme = round` the computed id is `R25-90`. `supersede 0002 0004` writes both links; `supersede 0003 0004`: 2. `rule 0004 in-force` with the placeholder: 2; with words written it sets status and today's date and cascades `0002` to `superseded` when linked; unlinked: 2; `rule 0004 spent` from proposed: 2; with `CLAUDECODE=1`: 2, the message naming the hook.

## 4. Findings that name this row
None. Open as HOW: refusal wording beyond the two fixed above; where the verbs sit.

## 5. Forbidden reads
the record; `design/ledger-conversion-r1.md`; `README.md`; `research/`; `history/` except this packet and `history/packets/core-report.md`; `reference/` except grep and sed over the two pinned ledger files, never whole.

## 6. Report (one table, five bullets, under 800 words), at `history/packets/p1-report.md` on the branch
- packet sufficient: yes | no, and what was missing
- items built, each with its commit; what you decided that the packet left open (a gap in the WHAT stops you there, as a report line)
- the acceptance run, exit lines only, plus the test count and `wc -l src/decisions.py`
