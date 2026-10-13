# ledger-conversion r1: a tool-drafted conversion of the in-force set (2026-09-22)

| item | value |
|---|---|
| status | r1 fold 1 from refuter 1 (`design/ledger-conversion-refuter-1.md`, FAIL 5/4/8, 2026-09-22) |
| answers | `decisions/0001-decisions-as-files.md` (1), which names this record its design question and `scope` over example-app its consumer; bound by 0001 (2) and (4) |
| pin | this repo `8d4e644`; the copies under `reference/` are example-ops `d2a62d3`, example-app `4dbce58` (`reference/SOURCES.md`). Every `file:line` is a path in this repo; every count below was measured 2026-09-22 over the pinned fixtures' entries by the refuter's script (`design/ledger-conversion-refuter-1.md`, Measurements); a claim with no anchor is marked unverified |
| ceiling | 16 KB (`wc -c`); three passes ever |
| consumers | the `convert` packet (a later sitting, after the owner rules §10); the example-app sitting's plan (`init`, the `governs` seed, the `legacy-map`, the batches); the archtest successor (`design/decisions-r1.md` §5) |
| fold rule | as `design/decisions-r1.md`: in-line |

## §1 The question

The owner's words, `decisions/0001-decisions-as-files.md:16`: "(1) Accept, but I'm also open to intelligently refactoring the old OWNER-DECISIONS.md file- I am not attached to it as long as we capture the critical decisions we made."

"The critical decisions" are taken to be the ones that still bind, and the hand index already says which those are: its fifth cell, mapped on its opening words (`design/decisions-r1.md` §3.4). Nothing here judges a ruling's importance; the owner does that at review (§7), by ruling a file in force or deleting it while `proposed`.

## §2 The input at the pin

| measure | value |
|---|---|
| R-id rows in the hand index (`reference/example-ops/OWNER-DECISIONS-INDEX.md`) | 210: 91 open with `IN FORCE`, 88 `SPENT`, 18 `SUPERSEDED by`, 13 mixed |
| the 91 by entry form (`design/decisions-r1.md` §3.4) | 55 Form A, 36 Form B; every one has an entry in the ledger |
| the 91 with `(n)` markers | 29; the other 62 are one ruling with no numbered parts |
| the 91 entries carrying a `"` character | 66; 25 have none; a quote mark marks a filename or a phrase as often as the owner's sentence, so it is no signature |
| the longest entry | R25-85, 6,469 bytes (`reference/example-ops/OWNER-DECISIONS.md:46`) |
| all 91 entries together | 103,047 bytes |
| distinct `governs` cells among the 91 | 75, free text: 4 rows say `the agent contract`, 3 `the confirm plane`, 3 `the board`, 3 `layer 1`; 64 cells occur once (`` `SESSIONS.md`, `STATE.md`, `QUEUE.md` `` is one) |
| supersession the index records | 18 rows open `SUPERSEDED by <id>`; the first id token after the words names an in-force row in 14 of them, so 8 in-force ids gain a `supersedes` list (R25-60 five, `reference/example-ops/OWNER-DECISIONS-INDEX.md:51` is one; R25-46 three; six with one) |
| ledger ids with no index row | 7: R25-86 to R25-89 (`reference/example-ops/OWNER-DECISIONS.md:45`, `:1641-1643`), and the lettered R23-1a, R23-1b, R23-2a, whose rows are R23-1 and R23-2 (`reference/example-ops/OWNER-DECISIONS-INDEX.md:184-185`, SPENT); `show` prints `standing: not indexed`; the lettered three are selected by `--ids` only |

The first row's counts are `design/decisions-r1.md` §3.4's; a test pins the rest (§6).

## §3 What the conversion produces

One file per selected row, `<out>/<id>-<slug>.md`, in the §2 format of `design/decisions-r1.md`, every field filled from one named cell or span and nothing else:

| field | source |
|---|---|
| `id` | the row's id, kept: example-app runs `scheme = round` and "185 hits cite them" (`design/decisions-r1.md` §2.5); a legacy id is re-used by `convert` alone, and its record then wins (§7; one sentence owed to parent §2.2) |
| `date` | the row's second cell |
| `status` | `proposed`, always |
| `governs` | the tags `decisions/legacy-map` gives for the row's fourth cell (§5) |
| `supersedes` | the ids of the rows whose fifth cell opens `SUPERSEDED by <this id>`, the first id token after the words, in index order; else `[]` |
| `superseded-by` | empty; a superseded row named by `--ids` takes it from its fifth cell |
| `consumers` | the row's fourth cell verbatim, written `[<cell>]`, which the index header names "the record it governs" (`reference/example-ops/OWNER-DECISIONS-INDEX.md:3`); a comma inside splits it into several consumers, which `check` accepts |
| `verify` | empty |
| `# <title>` | the row's third cell verbatim, "what it ruled in about ten words" (`:3`); the slug cut as `new` cuts it, non-alphanumerics dropped |
| `## Words` | the entry `find_entry` returns, whole and verbatim, as a blockquote, which `show <id>` prints whole only for an entry without markers; then one fixed line: `The ledger, <file:line>; the owner ratified the log (R25-19); his own sentences inside it are not separable by the tool.` |
| `## Decisions` | with markers contiguous from 1: one paragraph per marker span, the span as `show <id> n` prints it, a bold marker normalised to plain `(n)`, its closing `**` dropped with its opening; markers not contiguous from 1 (R18-2, R25-66) count as none and the count line names the entry; without markers: one paragraph `(1)` holding the entry's text after its id token, and for Form B after its date, blank lines inside the entry dropped so that the paragraph is one. Each paragraph ends with the fixed line `Rejected: not recorded in the ledger.` |
| `## Record` | `none; ruled <date> in the ledger, converted from <ledger file:line> and <index file:line> by decisions convert` (`rule` rewrites `date`, parent §2.2) |

The words are the ledger's, not a quotation cut from inside it: the index calls the ledger "the log (R25-19)" (`reference/example-ops/OWNER-DECISIONS-INDEX.md:3`), and 25 of the 91 entries carry no quote mark. The fixed `Rejected:` line is a placeholder in the sense `new` uses, not a sentence the tool composed: `check` v1 accepts it as structure, `rule` refuses only the `## Words` placeholder, and the owner ruling a record with it in force is accepting that the ledger recorded no rejected shape, which is true. 
Rejected: quoting only the double-quoted spans (a quote mark is no signature; 25 entries have none); one `(1)` per entry regardless of markers (29 carry parts `show <id> n` already cuts, and the sub-decision is the unit served).

## §4 What it never does

- Never writes outside `--out`, and nothing at all when any row cannot be converted (§6): a run is whole or nothing.
- Never touches the ledger or its hand index: both are read in place, by id, as `design/decisions-r1.md` §3.4 reads them; the ledger's freeze (0001 (1)) holds.
- Never invents a word: every body sentence is the ledger's or the index's, and the only other text is the two fixed lines of §3.
- Never sets a status other than `proposed`, and never runs `rule`.
- Never guesses a tag: a `governs` cell absent from the map refuses the run (§5).
- Never selects a spent, superseded or mixed row by standing; `--ids` may name one.

## §5 The tag seed

The index's `governs` column is free text and the reason `scope` matches by substring today (`design/decisions-r1.md` §3.4). The conversion maps it onto the closed vocabulary through a second closed file beside `decisions/governs` in the consuming repo, `decisions/legacy-map`: one line per cell, `<cell verbatim> => tag[, tag]`, `#` comments allowed; every tag on the right is a line of `decisions/governs`, and `convert` refuses a line that breaks that. 75 lines for example-app (§2). A cell that lists several things (`` `SESSIONS.md`, `STATE.md`, `QUEUE.md` ``) maps to several tags on one line; the tool never tokenises a cell. Cutting the map is the example-app sitting's act, with the `governs` seed it already owns (`design/decisions-r1.md` §2.5: the four archtest classes plus the session model's components).

Rejected: substring matching over the cell, which is the fallback this replaces; and one tag per distinct cell, which would invent 75 tags and make `scope` no narrower than the index.

## §6 The verb

`convert --from-legacy [--status in-force] [--ids A,B] --out <dir> [--map <file>] [--check]`, ships v1 in the sitting after the owner rules §10, in `src/decisions.py` under the conventions of `design/decisions-r1.md` §3.2.

- Reads the config's `[legacy]` (exit 2 when absent), the map (default `decisions/legacy-map`, exit 2 when absent or when a right-hand tag is not in `decisions/governs`), then the index and the ledger.
- Selects rows whose standing maps to `--status` (default `in-force`; a mixed cell matches nothing), plus every id named by `--ids` whatever its standing, a not-indexed id included: R25-86 is converted this way into example-app; R25-87 to R25-89 govern the session budget, the relay and this Mac's settings and go to example-mac by 0001 (4), in a second run with its own map.
- A selected id with no ledger entry, or an unreadable one, is exit 2; a `governs` cell absent from the map is exit 2 with one line per cell on stderr and nothing written; a file already in `--out` for a selected id is exit 2, the collision rule `new` has.
- Writes the files; prints one line per file, `<id> <path>`, and ends `# <k> records written; not selected: <a> spent, <b> superseded, <c> mixed, <d> not indexed`. Exit 0.
- Byte-identical on a rerun while the ledger and the map are unchanged: no timestamp, no pin, no ordering that depends on the filesystem. `--check` converts to memory, compares with `--out`, prints the diff and exits 1 on a difference, as `index --check` does.

Tests, over `tests/fixtures/legacy` and a temporary directory with a four-line map: `--ids R25-63,R16-2,R21-3,R25-60` writes four files; R25-63's `## Decisions` has four paragraphs and its `(4)` is the 180-byte span; R16-2 has one; R25-60's `supersedes` is the five ids of §2 in index order; `check` is green over the four with a `governs` carrying the mapped tags; `scope --governs <tag>` over the temporary root prints record rows with `(n)` and no substring count line; a rerun is byte-identical; an unmapped cell writes nothing; `--status in-force` over the whole fixture writes 91 files and the count line names 88, 18, 13 and 7.

## §7 The review, and what waits on it

The converted set, the 91 and R25-86, lands in the example-app repo (0001 (4): "Decisions should be in the repo containing the implementation") as 92 `proposed` files in one commit, binding nothing; R25-87 to R25-89 go to example-mac in a second run with its own map, by 0001 (4), and none of the 91 is a shared component under 0001 (4)'s exception. The owner rules them in batches of at most eight, put in plain language with the title, the tags and the ledger line each, the ones that gate work first (`reference/memory/decision-flapping-guardrails.md:8`: "a few at a time, the ones that gate work first"; `:12`: "plain language and small sets"). Twelve batches at most. Three outcomes per record: `rule <id> in-force` as it stands; edited while `proposed` (the words replaced by his own, a `Rejected:` line filled) and then ruled; or deleted while `proposed`, the ledger keeping the ruling as history with its index standing untouched. No agent runs `rule`.

While batches are open, the in-force set over example-app is split between files and index rows, and one rule keeps `scope` honest: a legacy row whose id has a record in `decisions/` in any status past `proposed` is skipped, and the record wins; while the record is `proposed` the row prints as before. Nothing binding vanishes, and under one `--status` nothing prints twice. `check` resolves a `supersedes` target absent from `decisions/` against the ledger when `[legacy]` is configured: it exists when the ledger has its entry, and symmetry holds when its index row opens `SUPERSEDED by <this id>` (P3 built it). `rule` treats a `supersedes` target absent from `decisions/` and present in the ledger as already superseded and writes nothing for it. The `scope` rule is the `convert` packet's sentence for parent §3.4; the `rule` sentence is owed to parent §3.3.

The L3 block: after `render` exists, a converted record ruled in force gets a generated row and its hand row leaves the constant in the same act, so no id has two rows and the archtest successor's "no row lacks a record" holds over the generated block alone; the example-app sitting's act (`design/decisions-r1.md` §5).

## §8 The consumer

`scope --governs <wall>` over example-app with real tags, and through it every packet's §2 and every refuter's brief (`design/decisions-r1.md` §4.2 item 4). Today `scope --governs rigor` over the fixtures returns two rows by substring, one of them R25-77 matched on a parenthetical in its cell (`reference/example-ops/OWNER-DECISIONS-INDEX.md:279`), and the count line says so; after the conversion and the map, a tag matches a record or nothing, every row carries `(n)` and a first sentence, and the substring count line prints only for the spent and superseded history no packet cuts from. The second consumer is the archtest successor (§7).

## §9 What is modelled and what is leveraged (0001 (2))

The owner's words, `decisions/0001-decisions-as-files.md:17`: "borrow from best-in-class implementations/research done in this space if good ones exist. Don't reinvent the wheel if there is some good approach out there already (that we can at least model after if not directly leverage)".

- **Modelled: adr-tools `adr new -s`.** "will create a new ADR file that is flagged as superceding ADR 9, and changes the status of ADR 9 to indicate that it is superceded by the new ADR" (`research/04-adr-canon.md:50`). The conversion writes the forward link from the index's backward one (§3 `supersedes`) and leaves the old entry untouched, because the ledger is frozen; the two-way link adr-tools writes into the old file is what `supersede` writes between two records (`design/decisions-r1.md` §3.3), never into the ledger.
- **Modelled: adr-tools `adr generate toc`** for the one-line index the converted set joins, built by `index` (P2 of this sitting); the conversion's count line and `--check` copy `index --check`'s shape.
- **Modelled: the CI-checked generated index.** "a **generated index checked in CI**: `docs/adr/README.md` regenerated from each record's YAML front matter, with the build failing on divergence" (`research/05-adr-with-agents.md:72`). The converted set is held by the same gate: `check` and `index --check` in the example-app `make check`.
- **Leveraged directly: nothing.** No surveyed tool ingests a 242 KB newest-first prose ledger with two entry forms and hand-numbered parts; adr-tools is bash over one-title-per-file directories, and its repository-upgrade verb (unverified at a pin) renames files it wrote itself. The parser this verb needs is the one built for `show`: the conversion is the fallback's reader with a writer behind it.

## §10 Decisions for the owner

**A. Run the conversion as designed: the 91 in-force rulings and R25-86 become `proposed` files in example-app `decisions/`, ruled in batches of at most eight.** Consumer: the example-app sitting's plan, and `scope --governs <wall>` over example-app, which until then cuts packet lines by substring over free text. Recommended: yes; the run is one command, whole or nothing, and a batch he dislikes is deleted while `proposed`. Rejected: converting by hand (0001 (1)'s rejected shape) and converting all 214 (`design/decisions-r1.md` §9).

**B. A converted record's `## Words` is the ledger entry whole, as his ratified log text, since the tool cannot separate his sentences from the drafter's.** Consumer: `rule` on every converted record, which refuses only the placeholder and will accept these words. Recommended: yes; at review he replaces any entry's words with his own before ruling. Rejected: cutting quoted spans, because 25 of 91 entries have none.

## Change-log

| pass | date | what landed, and where |
|---|---|---|
| r1 | 2026-09-22 | Written from 0001 (1), (2), (4) and `design/decisions-r1.md` §2, §3.2 to §3.4, §5 |
| r1 fold 1 | 2026-09-22 | All 17 of `design/ledger-conversion-refuter-1.md` (FAIL 5/4/8) in-line, cut first: §2 remeasured over entries; R25-87 to R25-89 to example-mac (§6, §7, §10 A); lettered ids by `--ids` only; the record wins only past `proposed`; `rule` on a ledger-only target; an unmapped cell exit 2; two sentences owed to parent §2.2 and §3.3 |
| d3-convert | 2026-09-22 | §6 built as `src/decisions/convert.py` (the package, not one file, ruling C) and §7's `scope` rule in `legacy_scope`, under rulings (A) (built and tested read-only, no run lands) and (B) (`## Words` the whole entry); `--ids` alone selects only the ids; a not-indexed id takes its map line by id and its tags as consumers; packet d3-convert |
