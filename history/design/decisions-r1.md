# decisions r1: the record of record for claude-code-decisions (2026-09-22)

| item | value |
|---|---|
| status | r2, folded 2026-09-23 (pass two of three): the change-log's design rows are in-line, the `r2` row names them and the sections touched; r1's refuter pass (`design/decisions-refuter-1.md`) and its folds stand |
| pin | this repo at `dd923c9`, the seed this record was cut from; the record itself lands at `70d5036` and its fold at the commit the change-log names. The copies under `reference/` are example-ops `d2a62d3`, example-app `4dbce58`, example-mac `f4d6389` (`reference/SOURCES.md`). D14: every `reference/` and `research/` path here resolves under example-ops `example-app-v2/reference/decisions/` (the trees moved whole on 2026-09-22, pins unchanged). Every `file:line` below is a path in THIS repo at that commit and resolves with `sed -n '<N>p' <file>`; a claim with no anchor is marked unverified |
| ceiling | 40 KB (`wc -c`); three passes ever for this record (R25-59's bound, `reference/example-ops/OWNER-DECISIONS.md:86`) |
| consumers | Act 3's packet (§3.3 `show` and `scope`, §3.4); the second sitting's packets (`new`, `index`, `render`, `rule`, the skill, the hook); the owner's ruling on §7 |
| fold rule | the body is frozen between passes; every change is a row of `design/decisions-r1-changelog.md`, and a pass folds the rows in-line. Never insert above an anchor another file cites (`reference/memory/line-anchors-shift-on-insert.md`; none cites this file by line at r2) |

## §1 The essence

The invariants, quoted verbatim from `research/06-evaluation.md:125-129`. They are the data model; §2 is their notation and restates none of them.

> - A record holds one ruling, has a stable id, a date, and the decider's verbatim words. It is never edited once ruled; it is superseded by a later record that links back, and the tool writes both links.
> - Every record carries a status from a closed vocabulary, a `governs` list from a closed per-repo vocabulary, at least one named consumer, and one line per sub-decision naming the rejected shape.
> - The index is generated from the records and gated. No hand-written copy of it exists anywhere, including a corpus root's table or a CLAUDE.md block.
> - A reader extracts, never reads: one sub-decision by id, or the in-force set for one scope. The whole log is history.
> - Only the owner moves a record out of proposed. Agents draft.

One reading rule the invariants imply and this record makes explicit: the tool may write the front matter of a ruled record (status, `superseded-by`, the ruling date), because those are the links and the standing the first invariant says the tool writes. The body below the front matter is never edited once ruled. Git holds the proof; `check` holds the structure (§3.3).

## §2 The record format

### §2.1 The file

One record is one file, `decisions/<id>-<slug>.md`, UTF-8, LF. The id is a front-matter field (§2.2); the filename begins with the id so that a directory listing is already an id-ordered index, and `check` refuses a file whose name does not begin with its own id. The slug is the title in lower-case words joined by hyphens, at most six words; it is decoration, and nothing parses it.

### §2.2 The front matter

Between two `---` lines, a flat `key: value` block. The tool parses it itself, stdlib only: scalars, and lists written `[a, b]`. No other YAML is accepted, and `check` refuses anything else (a nested key, a multi-line scalar, a quoted string containing `]`). Eight fields, every one present in every record, empty lists written `[]`:

| field | value | written by | rule |
|---|---|---|---|
| `id` | the repo's scheme (§2.5) | `new` | unique across `decisions/` and the legacy ledger (§3.4); never changes; a legacy id is re-used only by `convert`, whose record then wins (`design/ledger-conversion-r1.md` §7) |
| `date` | `YYYY-MM-DD` | `new`, then `rule` | the drafting day; `rule <id> in-force` rewrites it to the ruling day |
| `status` | §2.4 | `new`, `rule` | `new` writes `proposed`; only `rule` changes it (§3.3), and `rule` cascades a supersession |
| `governs` | list of tags | the drafter | at least one; every tag is a line of `decisions/governs` (§2.5) |
| `supersedes` | list of ids | `new --supersedes`, `supersede` | every id exists; each named record is `in-force` when this one is ruled |
| `superseded-by` | one id or empty | the tool only, by `supersede`, which `new --supersedes` also calls; `rule` never writes it | symmetric with the successor's `supersedes` |
| `consumers` | list of strings | the drafter | at least one: a path, a test name, a make target, a packet, or a record id; "no ruling without a consumer" (`reference/example-ops/ASSESSMENT-2026-09-19-decision-flapping.md:43`) |
| `verify` | one command line or empty | the drafter | the check that holds the decision mechanically, when one exists (`research/05-adr-with-agents.md:60`) |

### §2.3 The body

Four parts, in this order, each introduced by the heading shown; `check` refuses a record missing one.

1. `# <title>`: one line, the ruling in about ten words. The index (§3.3) prints it.
2. `## Words`: the decider's verbatim words in a blockquote. Mandatory; the field the ledger is organized around and the anti-flapping device (`research/06-evaluation.md:23`). `new` writes the placeholder `> (the decider's words go here)`; `rule <id> in-force` refuses while the placeholder stands. An "as recommended" ruling quotes those words. Agents never write this section on a ruled record.
3. `## Decisions`: the numbered sub-decisions. Each is one paragraph beginning `(n)`, n contiguous from 1, and each ends with one line beginning `Rejected:` naming the shape not taken and why, in one sentence. One ruling per record is one subject; its sub-decisions are its numbered parts, as the late ledger entries already do (R25-87 carries four, `reference/example-ops/OWNER-DECISIONS.md:1641`). A record with one part carries `(1)` alone.
4. `## Record`: one line, `design/<file>.md §<n>`, pointing at the design record section the ruling answers; or `none`, followed by the reason, for a ruling that had no record (a repo's first, layout record cites its own README).

**The unit served is the sub-decision.** `show <id> <n>` prints one `(n)` paragraph with its `Rejected:` line; `show <id>` alone prints a record whole and a legacy entry as its marker index (§3.4), never a ledger line; `scope` prints one line per sub-decision, and one line per legacy index row, which has none. This pins the packet's own row BP-2 (`reference/example-ops/build-packet-r1.md:111`: "prints a ruling's NUMBERED SUB-DECISION from `OWNER-DECISIONS.md`, never its line") and the refuter finding that forced it (`reference/example-ops/build-packet-refuter-1.md:19`, B2: one line of 6,470 bytes is 79% of a packet).

### §2.4 The status vocabulary

| status | meaning | entered by | left by |
|---|---|---|---|
| `proposed` | drafted; binds nothing; agents may write it | `new` | `rule` |
| `in-force` | binds | `rule` | `rule` to `spent` or `retracted`; or `rule` of a successor whose `supersedes` names it |
| `superseded` | replaced; `superseded-by` names the successor | `rule <successor> in-force` | never |
| `retracted` | withdrawn by the owner without a successor | `rule` | never |
| `spent` | its subject is built, executed or passed; nothing binds any more | `rule` | never |

Three of the five are the hand index's own standing words (`reference/example-ops/OWNER-DECISIONS-INDEX.md:5`: IN FORCE, SUPERSEDED by, SPENT); `proposed` and `retracted` are the two ends a draft needs. The last three are terminal. `scope` defaults to `in-force`; the other four are history and are read only by id.

### §2.5 `governs`, ids, and the config

**`decisions/governs`** is the closed vocabulary: one tag per line, `tag: description`, `#` comments allowed. `new` and `check` refuse a tag not in it. Adding a tag is a commit to that file, reviewed like code. `init` writes it empty with a comment header. For example-app the natural seed is the four archtest classes (`reference/example-app/arch_test-header.go.txt:15-23`: substrate, orchestrator, wiring, shared-leaf) plus the components of the session model's table (`reference/example-ops/SESSIONS.md:9-18`); cutting that seed is the example-app sitting's act, not this record's.

**`decisions/config`** is INI, read with `configparser`:

    [ids]
    scheme = sequential   ; 0001, 0002 ... zero-padded to four digits
    ; scheme = round      ; R<round>-<n>: example-app keeps its R-ids, since 185 hits cite them (research/01-ledger-shape.md:170-171)

    [legacy]              ; optional; §3.4
    ledger = ../example-ops/example-app-v2/OWNER-DECISIONS.md
    index = ../example-ops/example-app-v2/OWNER-DECISIONS-INDEX.md

`new` computes the next id: for `sequential`, max plus one; for `round`, the next n in the highest round found in `decisions/` and the legacy ledger together; `--id` overrides when the owner opens a new round. A collision with any existing id, legacy included, is refused. `new` holds `decisions/.new.lock` (`O_CREAT|O_EXCL`) from before it reads the records to after its write, so two `new` calls in one tree mint two ids; a held lock is waited on up to 2 s, then exit 2 naming the file, its pid and its age. The lock does not span worktrees: two branches cut from one main mint one id, each branch's gate is green, and main's `check` catches the duplicate at the second merge; a gate that measures the branch merged onto the current main is agent-relay's (ADV6-8).

**Where `decisions/` is.** The resolver of the session's conventions §3, seven layers, a later one winning: the shipped default `decisions`, the user's `~/.claude/decisions/config.yaml`, the repo's and the repo-local section of `.claude/claude-code-session/config*.yaml`, the session's `resolved.json` (only when its provider is `session` in range; its shape is assumed, not pinned), `$DECISIONS_DIR`, and `--dir`. The session is an override, never a requirement; `doctor` says which layer held.

## §3 The tool

### §3.1 Shape

One package, `src/decisions/`, stdlib only, every module under a thousand lines (ruling C), behind the runner `src/decisions.py`; `__init__` re-exports by a loop so pyflakes reads no star import. `#!/usr/bin/env python3`, 3.12+, run under the pyenv virtualenv `claude-code-decisions` (3.12.7) that `.python-version` names; never the system python3 (the python ruling of 2026-09-22 12:55). `pyproject.toml` declares the console script `decisions` and no dependency. `tests/` runs under `unittest`. `uv tool install .` from the repo puts `decisions` on PATH (the language-tooling rule, `reference/memory/local-installs-use-language-tooling.md:11-13`); a brew formula is the end state (`:30`). In a checkout it runs as `PYTHONPATH=src python3 -m decisions <verb>` or `python3 src/decisions.py <verb>`; `make venv` builds the virtualenv with pyflakes and writes no `.pth`. The package lives under `src/` so that it never shadows the repo's own `decisions/` directory.

The pattern is `reference/example-ops/cite-check.py`: inputs named on the command line, quiet output by default, exit 0 when the answer or the gate holds, 1 when the gate refuses, 2 on a usage error or an unreadable input (`reference/example-ops/cite-check.py:81-84`).

### §3.2 Conventions across verbs

- The repo root is found by walking up from the working directory to a `decisions/config`; `--dir <path>` overrides. A verb that needs the config and finds none exits 2.
- Output is stdout, one record or one row per line; errors go to stderr prefixed by the verb's name.
- Exit codes: 0 the answer or the gate holds, and `scope` always; 1 when `show` finds nothing, or when `index --check`, `render --check`, `check` or `stats --ceilings` refuses; 2 usage, an unreadable file, a malformed record, a missing config, or a writing verb's refusal (`init`, `new`, `supersede`, `rule`).
- Nothing is written outside `decisions/` except `render`'s block between its markers (§3.5) and `convert`'s `--out`.
- Every write is atomic: `commit_texts` writes each file to a temp beside it (`.<name>.<rand>.tmp`), fsyncs, then `os.replace`s them in order; on any failure the temps go and every replaced file is restored, so a verb that writes several files (`supersede`, `rule`'s cascade, `new --supersedes`) writes all or none (ADV6-9). Readers skip names beginning with `.`, so a temp or the lock is never a record.
- Unknown is never a pass: an empty result ends with a count line `# 0 rows`; a legacy id absent from the hand index prints `standing: not indexed`, never in-force (§3.4).
- Every output that quotes a record or the ledger carries its `file:line`, so a packet can anchor it (`reference/example-ops/build-packet-r1.md:29-66`, the §2 shape).

### §3.3 The verbs

| verb | input | output | exit | ships |
|---|---|---|---|---|
| `init [--ids sequential\|round] [--legacy-ledger P --legacy-index P]` | none | `decisions/config`, `decisions/governs` (empty), `decisions/INDEX.md` (rendered, empty); prints the two-line retrieval rule for the repo's `CLAUDE.md` | 2 if `decisions/` exists | v1, sitting 2 |
| `new --title T --governs a,b --consumer C [--consumer C2] [--supersedes ID] [--id ID] [--record REF]` | the flags | the file, status `proposed`, placeholders in `## Words` and `## Decisions`; prints its path | 2 on an unknown tag, an id collision, no consumer | v1, sitting 2 |
| `show <id> [n]` | an id; optionally a sub-decision number | the record whole (a legacy entry: its marker index, §3.4), or sub-decision n; header line `<id> (n) <status> <date> governs=<tags> <file:line>`, and for a legacy id `<id> (n) standing: <standing> <file:line>` | 1 not found; 1 when n does not exist | v1, Act 3 |
| `scope --governs X [--status S] [--full]` | one tag; status default `in-force` | one line per matching sub-decision, `<id> (n) <status> <first sentence> <file:line>`, the first sentence being the span's text after its marker up to its first `. `, cut at 120 characters; ids in numeric order (round, n, then a letter suffix) and n within an id; legacy rows after the record rows (§3.4); `--full` prints the paragraphs; ends `# <k> rows` | 0, even when empty (a config with no records is empty, not missing) | v1, Act 3 |
| `index [--check]` | the records | writes `decisions/INDEX.md`; `--check` renders to memory and prints the diff instead | 1 when the committed index differs | v1, sitting 2 |
| `render <target> [--governs X] [--status S] [--check]` | a file carrying the markers | the scope table between the markers (§3.5); `--check` compares instead | 1 stale; 2 no markers | v1, sitting 2 |
| `supersede <old> <new>` | two ids | writes `supersedes` into the proposed `new` and `superseded-by` into the in-force `old`; changes no status | 2 unless old is `in-force` and new `proposed` | v1, sitting 2 |
| `check` | the records | one line per finding, `<file>: <finding>` | 1 on any finding | v1 subset, sitting 2; v2 lints below |
| `stats` | the records | counts by status and by tag | `--ceilings`: 1 past a ceiling | v2 |
| `rule <id> <status>` | an id and a target status | the transition of §2.4 | 2 on a forbidden transition, any placeholder past `proposed`, an agent shell, or a mistyped confirmation | v1, sitting 2 |
| `check --against REV [--ruling]` | the records and their past at REV | as `check` | 1 when a record moved: on a branch no status moves and no ruled byte changes; on main (`--ruling`) only `rule`'s and `supersede`'s deltas pass | d7 (ADV6-1) |
| `convert --from-legacy --out DIR [--ids L] [--status S] [--map F] [--check]` | the legacy ledger and index | `proposed` records under `--out` only, Words the whole ledger entry (rulings A and B); an unmapped cell stops the run, whole or nothing (`design/ledger-conversion-r1.md` §3 to §7) | 2 on a refusal | d3, parked with (A) |
| `doctor [--json]` | this machine and repo | `ok\|warn\|fail <name>: <detail>` for python (a newer pyenv 3.x is a warn), tool, marketplace, plugin, provider, config, records | 2 on any `fail` | d1 |

`rule` is the only status writer. On `in-force` it sets `date` to today, and for every id in `supersedes`, which `supersede` must already have linked back (else exit 2), sets that record's status to `superseded`, in one act, through `commit_texts`; it writes no link. On a TTY it asks the owner to type the id and status back, and refuses a mismatch; it refuses every placeholder (`## Words`, a `(n)`, `Rejected:`, `## Record`) on a record leaving `proposed`. A `supersedes` target absent from `decisions/` and present in the ledger counts as already superseded, and nothing is written for it (`design/ledger-conversion-r1.md` §7). It refuses with exit 2 when the environment carries `CLAUDECODE` (measured 2026-09-22: the Bash tool's shell exports `CLAUDECODE=1`), naming the hook of §4.4 in its message; the hook denies the call before it runs. Two mechanical layers, on the model of the break-glass guard (`reference/example-ops/OWNER-DECISIONS.md:671`, R16-2: "The safeguard is MECHANICAL, not a remembered rule").

`check --against REV` holds the first invariant against a hand edit, which no verb sees: the Makefile passes the merge base on a branch and `HEAD --ruling` on main (ADV6-1). `check`, v1: ids unique; the filename begins with the id; the eight fields present and well-formed; `status` in §2.4; `governs` non-empty and within `decisions/governs`; `consumers` non-empty; `supersedes` targets exist and `superseded-by` is symmetric; `## Words` is not the placeholder on any record past `proposed`; `(n)` contiguous from 1, each paragraph with a `Rejected:` line; `## Record` present. `check`, v2: every consumer resolves (a path exists; a test name or make target greps); the overlap lint, a `proposed` record sharing a tag with an `in-force` one must name it in `supersedes` or cite its id in the body; the ceilings, warn above twenty in force per tag and fail above a hundred in force overall (`research/06-evaluation.md:109`). Semantic contradiction stays a reviewer's job (`research/06-evaluation.md:144`).

### §3.4 The legacy fallback

Moved whole at r2 to `design/decisions-r1-s34-legacy.md`, unchanged, to keep this record under its ceiling.

### §3.5 The generated block

`render <target>` finds `<!-- BEGIN GENERATED: decisions -->` and `<!-- END GENERATED: decisions -->` in the target and replaces what lies between them with one heading line naming the generating command and the scope table, LF-terminated, byte-identical on a rerun with the same records. The pattern is example-mac's portfolio block (the live `~/.claude/CLAUDE.md` carries `BEGIN GENERATED: portfolio-map` and `END GENERATED: portfolio-map`; not pinned under `reference/`, so unverified at a pin). `--check` renders to memory and exits 1 when the target differs, printing the diff. Markers absent: exit 2, nothing written. Targets: a corpus root's L3 block (§6), or a small repo's `CLAUDE.md` under the threshold of §8.3.

### §3.6 Install

`make install` wraps `uv tool install .`; the tool lands in `~/.local/bin/decisions`, which example-mac records with the rest of the machine (the owner's freeze step, outside this sitting). A brew formula is the end state for a machine without the repo (`reference/memory/local-installs-use-language-tooling.md:28-31`). Never a hand-copied file. `record`, the reader of sealed records by section, is not a verb here: it ships in claude-code-session as `scripts/record` with the skill `/session:read` (D15, ruled 2026-09-22 13:25), and this repo cites it by name. The licence is MIT, byte-identical to respeak's; `pyproject.toml`'s licence field waits for the repo to go public.

## §4 The plugin

### §4.1 Layout

The siblings put the plugin at the repo root with `source: "."` (`reference/plugins/respeak/tree.txt`, `reference/plugins/agents/tree.txt`; both `marketplace.json` files carry it), which here would package `reference/` (the 242 KB ledger copy) and `research/` into the plugin. This plugin therefore lives in a subtree: `.claude-plugin/marketplace.json` at the repo root names `source: "./plugin"`, and the files are `plugin/.claude-plugin/plugin.json` (name `decisions`, author as `reference/plugins/agents/plugin.json`), `plugin/skills/decisions/SKILL.md`, `plugin/commands/show.md`, `plugin/commands/scope.md`, `plugin/commands/new.md`, `plugin/hooks/hooks.json` and `plugin/scripts/deny-rule.sh`. The package is that subtree and nothing else: no `decisions/` directory, no fixture and no research is in it, and the only paths it names are the verbs. This repo's own `decisions/`, `reference/` and `research/` sit outside it. Verified 2026-09-22: `claude plugin marketplace add <repo path>` then `claude plugin install decisions@claude-code-decisions` installed the subtree at user scope, and `claude plugin details` inventories the skill, the three commands and the PreToolUse hook. `make marketplace` is that pair as the per-repo default (D11: one marketplace per repo), idempotent, printing `known|added` then `present|installed`; a new plugin repo copies it and changes two names.

### §4.2 The skill

`skills/decisions/SKILL.md`, frontmatter as `reference/plugins/respeak/SKILL.md:1-10` (name, a description under 200 characters, `allowed-tools: Bash(decisions *)`), body under 500 lines. Only the description loads at session start; the body loads on use (`research/06-evaluation.md:106`). Anthropic's skills page (<https://code.claude.com/docs/en/skills>, read 2026-10-14) adds the caps: the listing holds every skill's name; each description, with `when_to_use`, is cut at 1,536 characters; the listing's budget is 1% of the context window, and descriptions are dropped, least used first, when it overflows; the body, once invoked, stays in context and is not re-read; after compaction the most recent invocation of each skill returns capped at its first 5,000 tokens, within 25,000 for all skills together. So the skill keeps its key rule near the top (added 2026-10-14, a research fix). The body carries, in this order:

1. The two-line retrieval rule a consuming repo puts in its `CLAUDE.md`, quoted exactly as `init` prints it: "Decisions live in `decisions/`; before touching a governed area run `decisions scope --governs <tag>`, and read one ruling with `decisions show <id> [n]`. Never read `decisions/INDEX.md` or the ledger whole; draft with `decisions new`, status `proposed`, and never run `decisions rule`."
2. The manners: consult before touching a governed area; never load the index whole above the threshold; draft with `new`; name a consumer; cite or supersede any overlapping in-force record; put a ruling to the owner in plain language with its context, a few at a time (`reference/memory/decision-flapping-guardrails.md`).
3. The threshold, stated as the model of §8.3 with its three assumptions and the rule of thumb: an in-force set under about 2.7 KB may be rendered inline by `render`; above it the repo carries the two-line rule only.
4. How a packet's §2 and a refuter's brief are cut: `decisions scope --governs <wall> --full`, pasted whole, never paraphrased (`reference/example-ops/build-packet-r1.md:64`).

### §4.3 The commands

Each is a short markdown command that runs one verb and adds nothing: `/decisions:show <id> [n]`, `/decisions:scope <tag> [status]`, `/decisions:new <title> --governs ... --consumer ...`. Under thirty lines each. No command for `rule`, `supersede`, `index` or `render`: the first is the owner's, and the rest are `make check`'s.

### §4.4 The hook

`hooks/hooks.json`: one `PreToolUse` entry, matcher `Bash`, command `"${CLAUDE_PLUGIN_ROOT}/scripts/deny-rule.sh"`, on the shape of `reference/plugins/respeak/hooks.json` (which has a `PostToolUse` on `Write|Edit`). The script is POSIX sh (`cat`, `tr`, `sed`, `grep -E`, no interpreter to start or lock); it reads the hook's JSON on stdin, takes `tool_input.command`, drops quotes and JSON escapes, and when a `decisions`, `decisions.py` or `decisions.cli` token is followed by a `rule` token in one simple command it exits 2 with the reason on stderr: "rule is the owner's verb; put the ruling to the owner in plain language". Exit 2 blocks the call and returns the reason to the agent. Input it cannot read also exits 2 (fail closed, ADV6-3); a string that only mentions the verb is denied too (ADV6-10, kept). Anything else exits 0 and prints nothing. A test feeds the script two JSON lines and expects one deny. The guard it copies, the NAS's admin shell deny in example-ops, is named in the portfolio's CLAUDE.md and not pinned here: unverified at a pin.

### §4.5 The README

`README.md` is rendered, never written by hand: `make readme` runs respeak's renderer in technical mode (`claude -p`, at most two rounds) over `design/readme/source.md`, which carries the render notes, and writes the two-line sidecar `design/readme/rendered.sha256` (source, README). `make check` reads the README fresh when the sidecar verifies, not by mtime, so a fresh clone is fresh. The README names no private repository; `CLAUDE.md` cites record lines, and hygiene's per-file allow list (`.hygiene-allow`) names each exception with its group.

## §5 The gates

**This repo.** `make check` runs `check-unlocked` under `scripts/bounded` (one per tree by the lock `.check.lock`, a 900 s wall, held off above a load of four per core; a child is group-killed at its wall), in order: `gates` (the shebang `#!/usr/bin/env python3` on `src/decisions.py`, 3.12 syntax over `src/` and `tests/`, pyflakes); `test`, the suite through `tests/run.py`; `lint` (`compileall`); `doclint`; `hygiene`, whose two scripts are byte-identical to the session's canonical copies, sha-pinned in the Makefile and re-synced by a packet each time the session moves; `validate`, `claude plugin validate` on `plugin/` and `.`, each under a 60 s wall; `decisions`, `check --against` and `index --check`; then the README's freshness by its sidecar, refused when the source is absent. `$(PY)` is the interpreter `.python-version` names, resolved once. No git hook: the gate is `make check` and the driver's gate (ruling 4 of 2026-09-23 05:53). Acceptance lines are targeted; `make check` is a packet's verify line only.

**Skips.** A skip is a gate that did not run, never a pass: every skip reason is a verbatim line of `tests/skips.allow`, `gates.py` refuses pyflakes absent unless the file lists it, and `tests/run.py` exits 1 on any unlisted skip reason (ADV6-5). Listed today: pyflakes absent (until the owner's `make venv`) and the legacy tests' reason, 38 tests over the real ledger (D14: nothing sets `DECISIONS_LEGACY_REFERENCE`). Their synthetic excerpt waits for the convert map; the synthetic fixture under `tests/fixtures/legacy/` with ungated twins runs meanwhile.

**Hygiene over `design/`.** The `home` group is enforced over `design/*.md` and `design/packets/*.md`: sibling paths are repo-relative (`../<repo>`), never a home path (ADV6-11). The row files `design/packets/rows-*.json` keep it until their loader takes a repo-relative prompt.

**A consuming repo.** Its `make check` calls `decisions check --against <base>`, `decisions index --check`, and `decisions render --check <target>` for every rendered target. `index --check` exits nonzero when the committed index disagrees with the records, and `render --check` when a block is stale, so a ruling that forgot its render is red in the same act.

**example-app.** The successor of `TestArchitectureL3CoversTheDecisionLog` (`reference/example-app/architecture_l3_completeness_test.go:254-317`) is `TestArchitectureL3IsCurrent`: it reads the generated block between the markers in `docs/architecture.md` and the record files under the repo's own `decisions/`, and holds three things: every ruled record's sub-decisions have a row, every row's status equals its record's front matter, and no row lacks a record. It never skips, because with §7's decision 4 the records are in the same repository, and there is no hand step to omit: it goes red only when `render` was not run in the act, and the fix is always the one command, `decisions render docs/architecture.md`. The Go test parses front matter and `(n)` markers itself and never needs python. The current test keeps holding the hand rows until the freeze is ruled; after it the hand rows are a constant (144 rows to R25-89 at the pin, `reference/example-app/architecture-L3-section.md:177-178`) and the test retires with its floor sentence replaced by "hand rows end at R25-89; rows from the first file ruling are generated".

## §6 The first consumer, example-app

**What changes.**

1. From the first ruling after the ledger's highest on the day the owner rules §7's decision 1, rulings are files under example-app's own `decisions/` (the placement rule: a record lives in the repository whose implementation it governs; ruled 2026-09-22). At the pin the highest is R25-89 (`reference/example-ops/OWNER-DECISIONS.md:1642-1643`, both dated 2026-09-22), so the first file ruling is R25-90. `research/06-evaluation.md:38,71,155` and `README.md:52,58` say R25-88: stale by the two rulings of the pin's morning, and corrected here rather than there (the research is a sealed sitting's output; the README's row is corrected in the same commit as this record).
2. The ledger freezes as history, with a banner and no other edit. R25-60 (5) holds (`reference/example-ops/OWNER-DECISIONS.md:84`: "this log stays the log (R25-19) and is not trimmed by the restructure"). The hand index freezes at R25-85 with a banner saying R25-86 to R25-89 are unindexed; the fallback prints them `not indexed` (§3.4).
3. The L3 table keeps its 144 hand rows as history and gains the generated block after them, written by `decisions render docs/architecture.md`. R25-72 (5)'s "recorded once at the sitting's end with its L3 row in the same act" (`reference/example-ops/OWNER-DECISIONS.md:60`) becomes "with `render` in the same act", and the act is gated (§5).
4. Packet §2 and refuter briefs are `decisions scope --governs <wall> --full` output (`reference/example-ops/build-packet-r1.md:29-66`); the walls are archtest classes, so the example-app vocabulary carries them (§2.5).
5. `SESSIONS.md:57`'s sentence, "the corpus root's L3 table in example-app mirrors each ruling the same day, or every example-app gate is red", becomes "the corpus root's block is rendered in the same act, or `render --check` is red".

**What does not change.**

- No hand conversion of the 214 ids at line start in the ledger (`grep -oE '^(- \*\*)?R[0-9]+-[0-9]+' | sort -u | wc -l` at the fixture); the fallback reads them in place, and `convert` drafts `proposed` records to `--out` under rulings (A) and (B), parked until a consumer can test it.
- The adversarial round stays (`reference/example-ops/r1-brief.md:378-395`, §7: "Fewer tokens is not a reason to skip the bar that rejected two r1s three-for-three").
- `SESSIONS.md:31`'s forbidden reads stay: "Never the whole corpus, never the docket, never `OWNER-DECISIONS.md` beyond the rulings the record cites by number." The tool is how the cited rulings are read.
- The authority chain stays (`reference/example-app/CLAUDE.md:38`): the record files are the ledger's continuation, above the sealed designs.
- The contiguity gate next door stays; `new` computes the next id, so no number is skipped across the freeze.

## §7 The four decisions for the owner

Each is put in plain language with its context, names its consumer, names what waits on it, and quotes the owner's sentence where one bears (`research/02-churn-timeline.md:67-76`). Nothing here is asked that nothing is waiting on: `show` and `scope` over the frozen ledger wait on no ruling, which is why Act 3 builds them first.

**Decision 1. Rulings become files; the ledger freezes as history.** The ledger is 242,404 bytes at the pin, 214 rulings in one file, newest first except the last three, R25-87 to R25-89, which sit at the physical end (`reference/example-ops/OWNER-DECISIONS.md:1641-1643`). You ruled it "the log" (R25-19, `:43`) and "not trimmed" (R25-60 (5), `:84`), and nothing here trims it. The decision: from the first ruling after the ledger's highest on the day you rule (R25-90 at the pin), each ruling is one file with front matter, drafted by `new` in status `proposed` and moved to `in-force` only by you with `rule`; the ledger and its hand index freeze with a banner and are never converted. It amends R25-19 (the log continues in files); R25-60 (5) holds. Consumer: `new` and `rule`; packet §2 lines come from `scope`. What waits: `new` for example-app; without it, agents keep writing one-line entries into a file that is one line per ruling. Your sentences: 2026-09-11, "Aggressively purge the noise." (`research/02-churn-timeline.md:71`); 2026-09-12, "We need a clean start." (`research/02-churn-timeline.md:73`).

**Decision 2. The index and the L3 table are generated and gated; the hand copies retire.** Every ruling owed a hand-written row in example-app the same day: "a ruling and its L3 row are written in one act" (R25-63 (4), `reference/example-ops/OWNER-DECISIONS.md:78`) and "recorded once at the sitting's end with its L3 row in the same act; `OWNER-DECISIONS-INDEX.md` stays the reader's way in" (R25-72 (5), `reference/example-ops/OWNER-DECISIONS.md:60`). The mirror broke three times in four days (`reference/example-app/architecture_l3_completeness_test.go:14-17`), and the hand index is four rulings behind at the pin. The decision: from the first file ruling, the L3 rows are a generated block that `render` writes, the index is `decisions/INDEX.md` that `index` writes, `index --check` and `render --check` gate `make check`, the archtest becomes "the block is current" (§5), and no hand copy is written again. It amends R25-72 (5) and R25-63 (4): the one act stays, and its second half becomes a command. Consumer: the archtest successor and `make check`. What waits: `render` for example-app and the test change. Your sentence, 2026-09-12: "Why do we keep letting it fail? Address this once and for all." (`research/02-churn-timeline.md:72`).

**Decision 3. `governs` is a closed list, and scoped sets are queries, never directories.** Six of the last eight rulings bind two to five components each (`README.md:44`), so a directory per component would split or duplicate them, and a worker scoped to one directory would miss a global constraint. The decision: each repo carries `decisions/governs`, a closed list of tags; a record names its tags; the scoped set is `decisions scope --governs <tag>`; no per-component directories, ever. For example-app the seed is the four archtest classes plus the session model's components, cut at `init` by the example-app sitting. It amends nothing ruled. Consumer: `scope`, the packet generator, refuter briefs. What waits: the example-app vocabulary at `init`, and `new`'s refusal of an unknown tag. Your sentence, 2026-09-12: "I'd like you to make the compartmentalization extremely clear, and I want to be Fable heavy on these sessions." (`research/02-churn-timeline.md:73`).

**Decision 4. Records live beside the gate that reads them.** The archtest reads the ledger from a sibling repository on disk and skips when it is absent (`reference/example-app/architecture_l3_completeness_test.go:256-265`), so on a CI runner the property is unheld and the skip is the deliberate shape. The decision: product rulings live in example-app `decisions/`; rulings on the session model and the portfolio, like R25-87, live in example-mac `decisions/`; example-ops keeps the frozen ledger and a `decisions/` of its own for example-ops. Then the archtest successor never skips (§5). It amends the placement in `SESSIONS.md:57`, which names the example-ops file as the mirror's source; R25-19 named the file, not the repository. Consumer: the archtest successor; `init` in each of the three repos. What waits: where `init` runs for example-app. No owner sentence bears on it directly; the assessment's finding that "rulings made before anything uses them are the ones that get re-cut" (`reference/example-ops/ASSESSMENT-2026-09-19-decision-flapping.md:33`) is why its consumer is named.

## §8 The measure

**§8.1 The win is smaller lookups and fewer repair turns.** Baselines at the pin, `wc -c` and a span measurement over the fixture:

| read | bytes |
|---|---|
| the whole ledger | 242,404 |
| the hand index | 41,576 |
| the longest one-line ruling, R25-86 (`reference/example-ops/OWNER-DECISIONS.md:45`) | 13,654 |
| one sub-decision: R25-87 (3) / R25-86 (13) / R25-63 (4) | 255 / 237 / 180 |

Repair turns: the L3 mirror failed three times in four days (`reference/example-app/architecture_l3_completeness_test.go:14-17`), and `make check` was red on `main` until `4dbce58` (`README.md:11`). With §5 that class of turn does not exist, because the block is rendered, not remembered.

**§8.2 No token number is claimed.** The program attributes the rise in its token use to the corpus and how sessions read it together (a figure of 2.8x stood here with no source; it was removed 2026-10-14, a research fix), and no measurement isolates the ledger's share (`research/06-evaluation.md:32`). `scripts/burn-report` is specified and not built (`reference/example-ops/r1-brief.md:362,425`); until it exists, this record claims bytes per lookup and repair turns, nothing in tokens or dollars.

**§8.3 The inline threshold is a model.** An index loaded every turn costs its size times the turns: S × T. A retrieval costs one extra turn that re-reads the context: L × C for L lookups. Inline wins when S < L × C / T. The three assumptions, from `research/06-evaluation.md:93-100`: T = 300 turns per sitting, C = 100k tokens of context per turn, L = 2 lookups per sitting. Then S < 667 tokens, about 2.7 KB at four bytes a token. A site repo with eight decisions sits under it and renders inline; the example-app in-force set, about a hundred, sits far above it and stays on demand. Each assumption is confirmed or replaced by the burn-report, and the skill states the model, not the number, as the rule.

**§8.3a The model in cached-read terms (added 2026-10-14, a research fix).** Both sides of §8.3 are mostly cache reads, so the threshold holds to first order: the read rate multiplies S × T and L × C alike and cancels. The dollar figures do not carry over from base input. Per Anthropic's Pricing page (<https://platform.claude.com/docs/en/about-claude/pricing>, read 2026-10-14), a cache read costs 0.1x base input, 0.05x on Opus 5.5 and Sonnet 5.5 ($0.20 and $0.10 per million tokens) and 0.025x on Fable 5.1 ($0.25 per million); a write costs 1.25x base for the five-minute lifetime and 2x for one hour. At the assumed values on Opus 5.5, the 667-token index over 300 turns is about 200k read tokens, about $0.04 a sitting, and two lookups that re-read 100k each cost the same. The miss term: a gap past the cache lifetime, a model switch, a tool-definition change, a compaction or a Claude Code upgrade reprices the whole context at the write rate, the inline index with it. With M misses a sitting, write rate w and read rate r, inline wins when S < L × C / (T + M × (w/r − 1)). On Opus 5.5 or Sonnet 5.5 with five-minute writes w/r is 25, so each miss counts as 24 more turns (two misses put the threshold near 575 tokens); on Fable 5.1 w/r is 50. The burn-report measures M beside T, C and L.

**§8.4 What Act 3 measures.** The builder's report records `show R25-87 3 | wc -c` and `scope --governs <a tag from the index> | wc -c` over the fixtures, so the first row of this table has a measured successor before anything claims it.

## §9 Out of scope, by name

MADR's optional sections; Y-statements as prose; per-component directories; static-site tooling (log4brains and its kind); MCP servers; hand conversion of the 214 rulings; `@`-imports of any index (Claude Code expands them at launch, `research/06-evaluation.md:40`); agent-authored rulings in the AgDR style (agents draft `proposed`, only the owner rules). Also outside this record: the example-app `governs` seed (§2.5), the example-mac registry field, the contradiction-review agent, and `check`'s v2 lints, all named for the second sitting or later. Two more things the evaluation names are held here: no decision content ever goes into the portfolio `CLAUDE.md` above the checkouts, because a parent file taxes every repo beneath it (`research/06-evaluation.md:113`); and the charter's "decided this sitting" line names record ids and STATE renders it as today, with no new field (`research/06-evaluation.md:110`).

**§9a The vendor pages, and the parent-file ban against d17 (added 2026-10-14, a research fix).** Anthropic's memory page (<https://code.claude.com/docs/en/memory>, read 2026-10-14) confirms that `@`-imports load at launch, nest at most four hops and save no context; that CLAUDE.md arrives as a user message after the system prompt with no guarantee of strict compliance; that the project-root CLAUDE.md is re-read after `/compact` while nested files load again on demand; that it advises under 200 lines a file; and that auto memory loads the first 200 lines or 25KB of `MEMORY.md`. The monorepo page (<https://code.claude.com/docs/en/large-codebases>, read 2026-10-14) confirms that every CLAUDE.md in the working directory and its ancestors loads at launch, and that `claudeMdExcludes` skips a file by path or glob. The tension: the ban above keeps decision content out of any parent CLAUDE.md, yet d17 (`design/d17-four-verbs.md`) renders a cross-repo block into a user-level CLAUDE.md, which loads in every session at least as widely. d17 supersedes the ban for that one block and keeps it everywhere else: the block holds only the `Every session` entries, at most seven, and the rest of a ledger stays on demand through `show` and `find`. The tax the ban named is real and is bounded by that cap, not removed (d17 records the cap's bytes).

## Change-log

Moved whole to `design/decisions-r1-changelog.md` on 2026-09-22; rows are appended there, never here.
