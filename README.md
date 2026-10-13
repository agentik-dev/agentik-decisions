# agentik-decisions

<img src="assets/icon.svg" alt="" width="56" align="left">

agentik-decisions is a Claude Code plugin, `decisions@agentik`, plus a stdlib Python tool, `agentik-decisions`, for the decisions a repository has settled.
A repository keeps them in one sectioned `DECISIONS.md` at its root, and the tool serves that ledger with six verbs: `show`, `find`, `new`, `ask`, `answer` and `render`, plus `doctor` and `backlog`.

## Why it exists

One owner runs several Claude Code plugins in unattended relay runs, where one session hands its work to the next.
The decisions that shape that work have to reach every session, and no session should read a long file whole to find them.
So the ledger groups its entries by area and caps its size, and `render` copies the few entries every session needs into a generated block in `CLAUDE.md`.
An agent reads the rest by number or by area, and a packet carries the entries it touches verbatim.
Agents draft questions; only the owner moves an entry into force.

## The ledger

`DECISIONS.md` sits at the repository root.
Front matter, a title and prose may come first; then come three sections, in this order:

```
## In force

### Every session

1. **Plain words.** Every entry reads as plain present-tense English. (2026-09-01; the source)

### Build

3. **One interpreter.** The tool runs under Python 3.12. (2026-09-03; the source)

## Proposed

8. **A second interpreter.** The tool also runs under Python 3.13. (proposed 2026-09-08; OPEN-QUESTIONS.md)

## Superseded

- The old gate named by hand: replaced by make (entry 5), 2026-09-05.
```

- `## In force` holds `### Every session` first when present, then one `### <area>` subsection per area; every entry in force sits under a subsection.
- An entry in force is one line: its number, its title in bold ending with a period, or with `?` or `!` and no period, one paragraph, and a closing parenthetical that opens with a date, then a `;` or a `,` and its source.
- A Proposed line is one sentence ending in `(proposed YYYY-MM-DD; OPEN-QUESTIONS.md)`; only the owner's answer moves it into force.
- A Superseded line holds a date and names its fate: `replaced by`, `merged into` or `lapsed with`, in any case; unnumbered lines are legal.
- Numbers are unique across the three sections and never reused.
- At most 25 entries are in force, and at most 7 sit under `Every session`.
- The line `<!-- decisions: legacy below -->` ends the parsed part. An older ledger in another shape puts an empty `## In force` and that line above its old text, then takes new entries in this shape. `show --area` and `find` read the text below the line; the lint and the caps pass over it.

## Install

The tool and the `agentik` front door, from a checkout:

```
make install
```

The plugin, from the `agentik` marketplace:

```
claude plugin marketplace add agentik-dev/agentik-commons
claude plugin install decisions@agentik
```

Development runs under the pyenv virtualenv `agentik-decisions` on Python 3.12, the first line of `.python-version`; `make venv` creates it, and `make doctor` checks the machine and the repository.

```
make venv
make doctor
```

## The tool

`agentik decisions [--ledger PATH] <verb>` (`decisions` is an alias until 2026-12-31); the ledger is `--ledger PATH`, before or after the verb, else `DECISIONS.md` at the git top level of the working directory.

| verb | what it does |
|---|---|
| `show <n>...` | each entry verbatim, under its section heading |
| `show --area NAME` | a whole `###` subsection; NAME is a case-insensitive prefix of its heading, an exact name wins, and a leading `The ` in the heading may be left out |
| `find WORD` | `N Title (area or section)`, the area for an entry in force and the section otherwise, for each entry whose title or body holds the word, case-insensitively; `L<line> <heading> (legacy)` for each block below the legacy line that holds it |
| `new --title T --stands S --choice C --option "L: E" ... --recommend R [--report P]` | the four-part question in `OPEN-QUESTIONS.md`, with 2 to 4 options, the first recommended, and its Proposed line in the ledger |
| `ask [N...]` | the open questions, rendered once through respeak and written back, printed as AskUserQuestion calls (JSON) |
| `answer N (--pick L \| --other T) --source S [--text P] (--area A \| --amends M [--shorter] \| --no-entry) [--into PATH]` | the owner's answer: entry N, an amendment of entry M, or no entry; the question and its Proposed line leave, and an Answered line stays |
| `render [--into PATH] [--check]` | the lint, then the generated block in the `CLAUDE.md` beside the ledger, or in PATH |
| `render --lint` | the lint alone, over the ledger and the `OPEN-QUESTIONS.md` beside it |
| `doctor [--json]` | the interpreter (pyenv's, or the uv tool's that `make install` sets up), the tool and its version, the plugin, the provider, the ledger and respeak (optional: absent is a warn) |
| `backlog [REPO...] [--json]` | each repository's `NICE_TO_HAVE.md` placed against the build order in its `HANDOFF.md`: S1 and S2 items first, then each open step with the items that share a path with it, then S3, then S4; an item with no level prints `S4?`; it reads no ledger and writes nothing |
| `--version` | `agentik-decisions 0.8.0`, the version `doctor` compares with the `agentik-decisions` on PATH |

One example per verb:

```
agentik decisions show 4                # entry 4 under its heading
agentik decisions show 4 12             # two entries, each heading once
agentik decisions show --area relay     # the whole Relay area
agentik decisions find interpreter      # the title line of each entry that names it
agentik decisions new --title "Pin the interpreter" --stands "It runs under 3.12." --choice "Pin 3.12, or follow the newest?" --option "Pin: Keeps one interpreter." --option "Follow: Tracks releases." --recommend "Pin 3.12."
agentik decisions ask                   # the open questions as AskUserQuestion calls
agentik decisions answer 9 --pick pin --source "the sitting" --text "Pin 3.12." --area build
agentik decisions render                # write the block into the CLAUDE.md beside the ledger
agentik decisions render --check        # exit 1 and the diff when the block is stale
agentik decisions render --lint         # exit 1 and one line per problem
agentik decisions render --into ~/.claude/CLAUDE.md
agentik decisions doctor --json
agentik decisions backlog               # this repository's backlog against its build order
```

`new` appends `## N. T` to the `OPEN-QUESTIONS.md` beside the ledger, before `## Decided without asking` when that heading exists, with or without text after it:

```
## 9. Pin the interpreter

**Where things stand.** It runs under 3.12.

**The choice.** Pin 3.12, or follow the newest?

**What each answer sets in motion.**

- **Pin (Recommended).** Keeps one interpreter.
- **Follow.** Tracks releases.

**Recommendation.** Pin 3.12.

**Your answer:**
```

An optional **Report.** paragraph comes before the answer line.
`new` also appends the Proposed line for N, the recommendation's first sentence, which runs past `e.g.`, `i.e.`, `etc.` and `vs.`, and creates `## Proposed` before `## Superseded` when it is absent.
N is one more than the highest number in the ledger and in `OPEN-QUESTIONS.md`, so an answered question keeps its number as an entry.
When `OPEN-QUESTIONS.md` is absent, `new` creates it with a `# Decisions for the owner` heading and an empty `## Decided without asking`.
The read, the number and both writes run under `.new.lock` beside the ledger, so parallel runs take distinct numbers, and both files are written or neither is.
An empty part, or a title the ledger's lint cannot take, exits 2 and writes nothing; a title may hold a single `*`, as in a backticked `*.md`, but not `**`.
So does an option count outside 2 to 4, a label over five words or holding `(Recommended)`, a choice that does not end in `?`, or a sixth open question.
The first label holds at most four words, since ` (Recommended)` follows it, and no label is `Other` in any case, since AskUserQuestion adds that option itself.

`ask` skips, with one warning each, a block whose **Your answer:** line is filled in, which `agentik decisions answer N` enters first, and a block the lint refuses.
It puts the other open blocks through respeak's renderer once, with a contract that keeps headings, numbers, bold labels, option labels and ` (Recommended)` and rewrites only prose.
The render runs in a temp dir as `OPEN-QUESTIONS.md`, beside a copy of the repo's `.claude/respeak/`, and its `claude -p` child runs as a marked session helper.
It writes the rendered blocks back under `.new.lock`, both files or neither.
It keeps any block that lost a label, emptied a part, gained prose outside its parts, or was edited during the render, and it refreshes each Proposed line.
It then prints one AskUserQuestion call per four questions: the header `Decision N`, the question from where things stand and the choice, and each option's label and effect.
With respeak absent, a failed render, or a directory `ask` cannot write, the text stays, one warning goes to stderr, and the exit is 0; a failed render's warning carries the renderer's first error line.
A sitting without AskUserQuestion runs `ask` for the render alone; the owner answers on the **Your answer:** line.

`answer` takes the owner's answer to question N: `--pick` a label, ignoring case and ` (Recommended)`, or `--other` the owner's text restated.
One of `--area`, `--amends` and `--no-entry` is required.
It writes entry N under the `###` area `--area` names, as `N. **Title.** P (DATE; the owner's answer to decision N, S)`, with no period after a title ending in `?` or `!`.
`--area` resolves as `show --area` does, a unique prefix included, and the output names the heading matched; two matches exit 2, and a name no heading matches makes a new area.
`--amends M` replaces entry M's paragraph, keeps its tail whole and appends one amendment to it, and exits 2 when M's tail is missing or does not open with a date; `--no-entry` changes no entry.
`--text` is the body only: `answer` writes the bold title and the tail, and a `--text` that opens with a bold title or ends in a `(DATE; source)` tail exits 2 and writes nothing.
With `--amends M`, `--text` is the whole paragraph in force after the answer; the old paragraph prints as `replaced:`, and a paragraph under half the old one's length is refused unless `--shorter`.
Every run removes question N and its Proposed line, and adds `- N. Title: LABEL (DATE; S)` under `## Answered`, under `.new.lock`, both files or neither.
It then rewrites the `CLAUDE.md` block when that file holds the markers.
A `--into` target that is the ledger itself exits 2 before anything is written.
Once both files are written, the answer stands.
When the block cannot be written, one warning on stderr names the `agentik decisions render` command, with the `--ledger` and `--into` the answer used, and the exit is 0.

`render` lints first in every mode: the section shape, the entry shape, unique numbers and both caps.
An entry's tail opens with its date and names a source after it; `amended DATE` names no source.
An entry's body holds more than its tail, and its bold title and its tail each appear once.
A Proposed line's tail names `OPEN-QUESTIONS.md`.
A Superseded line holds a date and names its fate.
After an unknown `## ` heading no entry belongs to the section or the area before it.
When an `OPEN-QUESTIONS.md` sits beside the ledger, its first heading starts `# Decisions for the owner`.
At most five questions stay open, and each block holds the four labels in order.
It carries 2 to 4 options, with the first alone recommended, and no two labels equal ignoring case.
Each block ends in an answer line, no two blocks share a number, and each question has its Proposed line.
Front matter and a `## ` line inside a code fence are skipped.
Lines under `## Decided without asking` are `- ` bullets after an optional paragraph, and each line under `## Answered` ends in `(DATE; source)`.
Each problem prints `file:line: message`, and the exit is 1.
Otherwise it writes the block between `<!-- BEGIN GENERATED: decisions -->` and `<!-- END GENERATED: decisions -->`, replacing a stale block in place, or appends it after one blank line when the markers are absent.
`--check` writes nothing: it prints a unified diff and exits 1 when the block is stale, 0 when it is fresh.
The block holds one line naming its source and the command that regenerates it, then the `Every session` entries verbatim.
It adds one line per other entry in force, `- N Title (area)`, under a sentence naming the `show N` command that reads one.
Proposed and Superseded entries stay out.
Rendered into a file that sits beside no ledger, such as `~/.claude/CLAUDE.md`, the block names the ledger whole, and its commands carry `--ledger`.
A target that is the ledger itself, by its path, a link, a hard link or its name in another case on a case-insensitive disk, exits 2 and writes nothing.
Every verb that writes keeps a file's line ends, CRLF or LF, and writes through a link to the file it names, so the link stays; a link into a missing directory exits 2.

Exit codes:

| code | meaning |
|---|---|
| 0 | the answer; `find` with no match too; `backlog` whenever its files could be read; `answer` whose block write failed after both files were written, with its warning |
| 1 | `render`: a lint problem, or with `--check` a stale block |
| 2 | usage, an unknown verb, entry or area, an unreadable ledger, a `new` or `answer` refusal, an `ask` for an unknown N or under a held lock, a `render` or `answer` target that is the ledger itself, a failed `doctor` check (a `--ledger` that names an absent file among them), or a `backlog` directory that is missing or a file it cannot read as UTF-8; a `warn` never changes the exit |

## The plugin

The plugin carries manners and no data; a repository owns its ledger.

| part | name | what it does |
|---|---|---|
| skill | `decisions` | consult, cite and draft entries before touching a decided area |
| skill | `/decisions:ask` | ask the open questions once, in one batch, through AskUserQuestion, then enter each answer |
| command | `/decisions:show <n>...` | entries by number, or one area with `--area <name>` |
| command | `/decisions:find <word>` | the title line of each entry that holds the word |
| command | `/decisions:new --title T --stands S --choice C --option "L: E" ... --recommend R` | the four-part question and its Proposed line |
| command | `/decisions:answer N --pick L --source S --text P --area A` | the owner's answer, entered in the ledger |
| command | `/decisions:render [--check]` | the lint, then the block in `CLAUDE.md` |
| command | `/decisions:backlog [REPO...]` | the backlog, placed against the build order; the skill runs it before S4 work |

One example each:

```
/decisions:show 4 12
/decisions:show --area relay
/decisions:find interpreter
/decisions:ask
/decisions:render --check
/decisions:backlog
```

Or say it: "which decisions cover the relay?" reaches the skill.

## Configuration

The tool reads no configuration file: the ledger is `--ledger` or `DECISIONS.md` at the git top level.
The session plugin is an optional provider and never a requirement: `doctor` reports whether the session's resolved file is absent, in range, out of range or unparsable, and the tool runs the same either way.

## Design

- The portfolio's ledger decides where decisions live and names the six verbs; this version follows it.
- `design/d23-backlog-view.md`: the backlog view this version adds, and respeak kept optional.
- `design/d18-one-flow.md`: the design of the flow, one flow from a fork to an entry; `design/packets/d18-one-flow.md` built it, with its acceptance table.
- `design/d17-four-verbs.md`: the packet that built version `0.3.0`.
- `history/design/` and `history/packets/`: the designs and packets of the per-file format before it.
- `history/sittings/`: one charter per working session; each handover lists the choices made inside the design.

## Tests

Each file runs alone in seconds:

| File | What it pins |
|---|---|
| `tests/test_ledger.py` | the parser and the lint: each shape, unique numbers, both caps, the tail, the fate, the questions file, the legacy line |
| `tests/test_lookup.py` | `show` and `find` over the sample ledger, and below the legacy line |
| `tests/test_new.py` | `new`: a fresh file, an existing one, the insert point, the options, an empty part |
| `tests/test_answer.py` | `answer`: a pick, an amendment, no entry, both files or neither, the block |
| `tests/test_ask.py` | `ask` under a stub renderer: the calls, the fields, one render in a temp dir, the write-back, the skipped blocks, the helper marks, no respeak |
| `tests/test_render.py` | `render`, `--check` and `--lint`, with the file's hash before and after |
| `tests/test_cli.py` | the six verbs, `doctor` and `backlog`, the dropped ones, and where the ledger is found |
| `tests/test_common.py` | the bounded child, the git top and the one-rename write |
| `tests/test_doctor.py` | `doctor` under a fake `pyenv` and a temp home |
| `tests/test_backlog.py` | `backlog` over fixtures trimmed from real files: the levels, the build order, the placement, the exits, no write and no render |
| `tests/test_plugin.py` | the plugin subtree: six commands, the two skills, one version |
| `tests/test_makefile.py` | the harness `make test` runs, and the `decisions` step |
| `tests/test_hermetic.py` | the suite reads no live state |
| `tests/test_gates.py` | a skip is a gate that did not run, never a pass |
| `tests/test_bounded.py` | the exits, the lock, the wall and the load breaker of `scripts/bounded` |
| `tests/test_hygiene.py` | `scripts/hygiene` |
| `tests/test_doclint.py` | `scripts/doclint` |
| `tests/test_readme.py` | this README: the icon, the render path, the status line and the shape |

```
PYTHONPATH=src python3 -m unittest tests.test_ledger
PYTHONPATH=src python3 -m unittest tests.test_readme
make check
```

`make check` runs under `scripts/bounded`, in order: `gates`, `test`, `lint`, `doclint`, `hygiene`, `validate`, `decisions` (`render --check` when the repository keeps a `DECISIONS.md`), then the README's freshness by its sidecar.
`tests/skips.allow` lists the skips the suite may report; it lists none, and the suite exits 1 on any skip that file does not list.

## Conventions shared with the sibling plugins

This plugin is one of several built to the same conventions.
`scripts/{hygiene,bounded,agentik}` are agentik-commons' copies, pinned by `scripts/vendored.sha256`; `scripts/doclint` (charters, packets, links) is byte-identical across them, pinned in the Makefile.
`scripts/hygiene` keeps only generic patterns; the private ones (a person, a private repo, a host, a domain) live outside it, in `$AGENTIK_HYGIENE_PRIVATE` or `~/.config/agentik/hygiene-private.tsv`, `group<TAB>regex` rows.
Without it the scan warns once and runs the generic groups; `--require-private` exits 2.
`scripts/bounded` holds `make check` to one run per tree, a 840 s wall, and no start above a load of 4 per core.
Each README is rendered from its source, and the sidecar `design/readme/rendered.sha256` holds the two hashes `make check` reads.

| id | range | role |
|---|---|---|
| `respeak` | `^0.6` | renders this README, and the questions `ask` puts when it is installed |
| `agentik-session` | `>=2.0.0-alpha.1,<3.0.0` | the optional provider that `doctor` reports |

## Status

Status: version `0.8.0`, rendered `2026-10-13`, `361` unittest cases.

| Surface | State |
|---|---|
| Verbs `show`, `find`, `new`, `ask`, `answer`, `render`, `doctor`, `backlog` | Working |
| The lint: section shape, entry shape, the tail, the fate, unique numbers, both caps, the questions file, the legacy line | Working |
| The plugin: two skills, six commands and respeak's include file | Working |
| The session provider in `doctor` | Working |

Version `0.8.0` tightens the lint and `answer`. The lint now refuses an entry whose tail does not open with its date, or names only `amended DATE`. It also refuses an entry in force that is only its tail, and a Proposed line whose tail omits `OPEN-QUESTIONS.md`. It takes fate phrases in any case, and a title that ends in `?` or `!`. In `OPEN-QUESTIONS.md` it skips front matter and fenced `## ` lines, and flags a repeated question number and two labels equal ignoring case. `answer` requires one of `--area`, `--amends` and `--no-entry` in its usage, resolves `--area` by prefix and prints the heading matched, and refuses to amend an entry whose tail does not open with a date. `new` and `answer` write no period after a title ending in `?` or `!`, and `find` prints `N Title (area or section)`.

Version `0.7.0` tightens `new` and `ask`. `new` refuses an option named `Other` and a first label over four words, and a new question's number passes the entries below the legacy marker. `ask` skips an answered block and a block the lint refuses, and keeps the text beside a directory it cannot write, where it stopped with a traceback. It keeps a block whose render emptied a part or added prose, runs the render in a temp dir as a marked session helper, and states a restated effect once in the recommended option's description.
Version `0.6.0` changes five exits that callers see. `answer` exits 0 with a warning naming the `render` command when the block write fails after both files are written, where it exited 2. `doctor --ledger` naming an absent file fails and exits 2, where it warned and exited 0. Under the uv tool's interpreter at 3.12 or later, which `make install` sets up, `doctor` no longer fails its python row and exits 0, where it exited 2. `render` and `answer` exit 2 and write nothing for a target that is the ledger itself, by its path, a link, a hard link or its name in another case. Both exited 0, and wrote the block into the ledger. A target that is a link into a missing directory exits 2, where `0.5.2` replaced the link with a file and exited 0. `doctor` also warns when the `decisions` on PATH names another version, `decisions --version` prints the version, and every write keeps a CRLF file's line ends and a link.
Version `0.5.2` makes `answer --text` the body only. `answer` refuses a `--text` that opens with a bold title or ends in a dated tail, and the lint names an entry whose title or tail is doubled.
Version `0.5.1` ships respeak's include file, `plugin/respeak-include.md`, which `CLAUDE.md` imports; respeak stays optional.
Version `0.5.0` adds `backlog`, and `doctor` reports respeak, which stays optional.
Version `0.4.0` drops `new --answers`: `new` takes two to four `--option` flags instead, and `ask` and `answer` carry a question from the file to the owner and the answer into the ledger.
Version `0.3.0` broke `0.2.0` on purpose: the per-file format and its verbs are gone, and a repository moves its entries into one ledger by hand.

## Layout

```
.hygiene-allow             the names scripts/hygiene permits, per path
.python-version            the pyenv virtualenv the checks run under (3.12)
CLAUDE.md                  how a session in this repo works and checks
Makefile                   make check, make readme, make doctor, make venv, make install
assets/icon.svg            the project icon
plugin/                    the plugin, self-contained: what an install copies
plugin/skills/decisions/   the skill that consults and drafts
plugin/skills/ask/         the skill that asks the owner: /decisions:ask
plugin/commands/           show, find, new, answer, render, backlog
plugin/respeak-include.md  respeak's include file: how to write here; CLAUDE.md imports it
src/decisions.py           the runner
src/decisions/             the package, each module under a thousand lines
design/                    the current design, its packet and this README's source
scripts/readme-render      make readme: the status line, the render, the verifier, the stamp
scripts/hygiene            the name and path lint
scripts/doclint            charters, packets and relative links
scripts/bounded            the wall, lock and load breaker make check runs under
scripts/agentik            the agentik front door
tests/                     unittest suites and the sample ledger
history/                   the old designs and packets, and one charter per working session
```

`make readme` renders this README from `design/readme/source.md` in technical mode; `make check` refuses a README older than its source.

## License

[MIT](/LICENSE); LICENSE holds the copyright line.
