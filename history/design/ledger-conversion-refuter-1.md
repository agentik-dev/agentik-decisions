# Refuter report 1 for design/ledger-conversion-r1.md, Fable, 2026-09-22, at 2f6dc71

**FAIL** — blocking 5 / major 4 / minor 8. Every `file:line` anchor resolves; the §9 quotes are exact; `reference/`, `src/`, `tests/` are byte-identical between the pin `8d4e644` and HEAD. What fails is three counts false at the pin, one routing that contradicts 0001 (4), and one `scope` rule that hides binding rulings.

## Findings

| id | sev | where | finding | fold |
|---|---|---|---|---|
| B1 | blocking | §6 L76, §10 A L108 | R25-87 to R25-89 are converted into example-app `decisions/`. R25-87 is "the session budget's four decisions" (`OWNER-DECISIONS.md:1641`), R25-88 the overnight relay's (`:1642`), R25-89 the `~/.claude/settings.json` cut (`:1643`). 0001 (4): "the session budget's in example-mac". The run has no per-repo routing. | L76: "R25-86 is converted this way into example-app; R25-87 to R25-89 govern the session budget, the relay and this Mac's settings and go to example-mac by 0001 (4), in a second run with its own map." §10 A: "the 91 in-force rulings and R25-86". |
| B2 | blocking | §2 L30, §6 L81 | Ledger ids with no index row are 7, not 4: R23-1a (`:314`), R23-1b (`:325`), R23-2a (`:343`) have no row; the index carries R23-1 and R23-2 (`INDEX:184-185`, both SPENT). `show R23-1a` prints `not indexed`; the test's "4" cannot pin. | L30: add "and the lettered R23-1a, R23-1b, R23-2a, whose rows are R23-1 and R23-2 (`INDEX:184-185`, SPENT)"; L81: "names 88, 18, 13 and 7"; state that the lettered three are selected by `--ids` only. |
| B3 | blocking | §2 L25-27, §3 L53, §10 B L110 | The quote, longest and total rows measure `show <id>` output, which for the 29 marker entries is a first-sentence index, not the entry: the sum of `show` bodies is exactly 57,162. The entries `convert` writes into `## Words` total 103,047 bytes; the longest is R25-85, 6,469 bytes (`:46`); 66 carry `"`, 25 have none. "All 91 entries together 57,162 bytes" and "45 have none" are false at the pin. | Replace the three rows with the entry numbers (66/25; R25-85 6,469 bytes `:46`; 103,047 bytes); L53 and L110: "25 of the 91 entries carry no quote mark". |
| B4 | blocking | §7 L87 | "A legacy row whose id has a record in `decisions/`, in any status, is skipped" suppresses a binding ledger row for as long as its file is `proposed` (up to twelve batches), so `scope --governs X` over example-app prints nowhere a ruling that still binds. "It binds nothing yet" is false: the ledger row binds until the owner rules the file (0001 (1) freezes the ledger, it does not retire it); parent §3.2: "Unknown is never a pass". | "A legacy row whose id has a record in `decisions/` in any status past `proposed` is skipped, and the record wins; while the record is `proposed` the row prints as before. Nothing binding vanishes, and under one `--status` nothing prints twice." |
| B5 | blocking | §3 L40 | `id` "kept" contradicts parent §2.2 (`id` "unique across `decisions/` and the legacy ledger") and §2.5 ("A collision with any existing id, legacy included, is refused"); `check` v1's "ids unique" as §2.2 defines it is red on all 91. The record narrows `new`'s collision rule to `--out` and never amends §2.2. | One sentence for §2.2: "A legacy id is re-used only by `convert`, whose record then wins (§3.4)." |
| M1 | major | §3 L49 | `## Words` is "the entry whole" and also "the lines `show <id>` prints after its standing line"; for the 29 marker entries `show <id>` prints `(n) <first sentence>` lines, not the entry. A builder cannot satisfy both. | "the entry `find_entry` returns, which `show <id>` prints whole only for an entry without markers". |
| M2 | major | §3 L50 | Two marker sets are not contiguous from 1: R18-2 (`:552`) yields a lone `(2)` cut from a citation, R25-66 (`:72`) numbers from `(0)`. `parse_decisions` refuses both ("n runs from 1"), so `check` is red and the whole-or-nothing run has no rule. Also a bold `**(n) TEXT**` marker normalised to `(n)` leaves a dangling `**` (R25-66 (1) to (5)). | "Markers not contiguous from 1 count as none: the entry converts under the no-marker rule and the count line names it; a bold marker's closing `**` is dropped with its opening." |
| M3 | major | §3 L44, §7 L87 | `rule <id> in-force` as parent §3.3 (line 115) is written exits 2 for every `supersedes` id that `supersede` has not linked back; the eight converted successors name legacy ids with no record, so none can ever be ruled. The record folds `check` only. | Add for §3.3: "`rule` treats a `supersedes` target absent from `decisions/` and present in the ledger as already superseded and writes nothing for it." |
| M4 | major | §6 L77 | "A `governs` cell absent from the map is exit 1" against parent §3.2 (line 95): a writing verb's refusal is 2; 1 is a gate's. The record claims §3.2's conventions. | "exit 2 with one line per cell on stderr". |
| m1 | minor | §2 L24 | 29 entries have markers, 62 none (record 28/63). | "29; the other 62". |
| m2 | minor | §2 L28 | 64 cells occur once (7 twice, 3 thrice, 1 four times), not 60. | "64 cells occur once". |
| m3 | minor | §3 L46 | `consumers` "one string, verbatim": 24 of the 91 fourth cells contain a comma (R25-60's `` `SESSIONS.md`, `STATE.md`, `QUEUE.md` ``), which `parse_value` splits into several strings. | "written `[<cell>]`; a comma inside splits it into several consumers, which `check` accepts". |
| m4 | minor | §3 L48 | Slug "first six words, lower-cased, hyphenated": R11-3's and R18-5's first six words carry `/` (`` `/data/example-app` ``, `srpc/1`), a path separator in a filename. | "cut as `new` cuts it, non-alphanumerics dropped". |
| m5 | minor | §3 L41 | `date` is the row's second cell, but `rule <id> in-force` rewrites it to the ruling day (parent §2.2); the original ruling date then survives only in the ledger line. | Carry it in `## Record`: "`none; ruled <date> in the ledger, converted from ...`". |
| m6 | minor | §4 L63, §6 L76 | `--ids` naming a superseded row (R2-4) writes `superseded-by` empty while R25-60's record names it: `check` symmetry red. | "a superseded row named by `--ids` takes `superseded-by` from its fifth cell". |
| m7 | minor | §8 L93 | R25-77 matches on the parenthetical "(r2 carries the rigor sections)" in its fourth cell (`INDEX:279`); the record anchors `history/packets/core-report.md` instead of the cell. | Anchor the cell. |
| m8 | minor | ceiling | 16,361 of 16,384 bytes: 23 bytes of headroom, so every fold above must be paid by a cut (the change-log row, §1's second paragraph). | Cut before folding. |

## Intent coverage

| owner's sentence | verdict | where |
|---|---|---|
| (1) "Accept, but I'm also open to intelligently refactoring the old OWNER-DECISIONS.md file- I am not attached to it as long as we capture the critical decisions we made." | DONE DIFFERENTLY | §1, §3, §7: the refactor is a verbatim mechanical cut of the IN FORCE set; "intelligently" and "critical" are deferred to the owner's batch review. With B1 to B3 the capture as designed misroutes three and miscounts three. |
| (2) "accept, but borrow from best-in-class implementations/research done in this space if good ones exist." | DONE | §9: three models, quoted exactly at `research/04-adr-canon.md:50`, `:52` and `research/05-adr-with-agents.md:72`. |
| (2) "Don't reinvent the wheel if there is some good approach out there already (that we can at least model after if not directly leverage)" | DONE | §9: leverages none, with the reason (no tool ingests a prose ledger); the one unverified claim (`adr upgrade-repository`) is labelled. |
| (4) "accept - example-ops is not the home for this at all." | DONE | §7: the set lands in example-app. |
| (4) "I don't understand where that is coming from." | DONE (nothing owed) | no directive. |
| (4) "Decisions should be in the repo containing the implementation." | DONE LESS | §7 routes all 95 files to example-app in one run; R25-87 to R25-89 govern example-mac's implementation (B1). |
| (4) "The exception to this are shared components (libraries, frameworks, templates like for my various websites, etc that should all follow the same rough decisions as far as the platform goes)." | DONE (not applicable) | no shared-component ruling among the 91; the record should say so in §7. |

**§10.** A is waited on by the `convert` packet and the example-app plan: real. B is waited on by `rule` on every converted record: real, but its stated ground ("45 of 91 have none") is false (25). **Missing:** C, the home of R25-87 to R25-89 and whether the run is split per repo (B1); and a rule, not a ruling, for the lettered R23-1a/1b/2a (B2).

## Measurements

Script S = `/usr/bin/python3` importing `src/decisions.py` and running `index_rows`, `map_standing`, `find_entry`, `marker_spans`, `main(["--dir","tests/fixtures/legacy","show",id])` over the fixture (a symlink to `reference/`).

| claim | record | measured | how |
|---|---|---|---|
| R-id rows / IN FORCE / SPENT / SUPERSEDED / mixed | 210/91/88/18/13 | 210/91/88/18/13 | S |
| Form A / Form B among 91; entries missing | 55/36; 0 | 55/36; 0 | S (`FORM_B_RE` on the entry's first line) |
| with `(n)` markers / without | 28/63 | 29/62 | S (`marker_spans` non-empty) |
| with `"` / without, over entries | 46/45 | 66/25 | S; over `show` bodies: 46/45 |
| longest | R21-3 2,040 | `show R21-3` = 2,040 bytes; longest entry R25-85 6,469 (`:46`); R21-3 entry 1,922 | `show R21-3 \| wc -c`; S |
| 91 together | 57,162 | entries 103,047; `show` bodies 57,162; `show` whole 64,667 | S |
| distinct governs cells; 4/3/3/3; singletons | 75; yes; 60 | 75; the agent contract 4, the confirm plane 3, layer 1 3, the board 3; 64 | S (`Counter(cells[3])`) |
| SUPERSEDED rows; in-force targets; successors | 18; 14; 8 (R25-60 five, R25-46 three, six with one) | 18; 14; 8: R25-60 [R2-4, R20-2, R24-6, R25-33, R25-34], R25-46 three, R19-5, R25-64, R15-1, R18-2, R25-70, R25-59 one each | S; R2-4 at `INDEX:51` |
| the 4 not-in-force targets | not named | R5-8→R25-20 (not indexed), R9-4→R12-1, R17-3→R21-1, R20-3→R25-53 (spent) | S |
| ids with no index row | 4 | 7: R25-86, R23-1a, R23-1b, R23-2a, R25-87, R25-88, R25-89 | S (217 ledger ids minus 210 rows) |
| R25-63 (4) span | 180 bytes | 180 (span); `show R25-63 4` 288 with header | S; `show R25-63 4 \| wc -c` |
| R16-2 | one paragraph | Form A, no markers, no blank line | `show R16-2`; S |
| R21-3 entry | — | Form A, no markers, has blank lines (the no-marker rule drops them) | S |
| four test cells distinct | four-line map | yes (`QUEUE Q33, Q24, Q20; the corpus root`, `the agent contract`, `` `Power.Down` ``, `` `SESSIONS.md`, `STATE.md`, `QUEUE.md` ``) | S |
| non-contiguous marker sets | none | R18-2 [2], R25-66 [0..5] | S |
| spans with blank lines; entries with a `Rejected:` line | — | 0; 0 | S |
| fourth cells with `,` / `[` `]` | — | 24 / 0 | S |
| `scope --governs rigor` | 2 rows, R25-77 by parenthetical | 2 rows (R24-7 `INDEX:195`, R25-77 `INDEX:279`, cell "(r2 carries the rigor sections)"), count line by substring | `scope --governs rigor` |
| anchors `0001:16-17`, `INDEX:3,51,287`, ledger `:45,:412,:1641-1643`, guardrails `:8,:12`, `research/04:50`, `research/05:72`, SOURCES pins | — | all resolve as quoted | `sed -n` |
| ceiling | under 16 KB | 16,361 | `wc -c` |

The record's structure holds — the field mapping, the map, the verb, the batches, the models — but its §2 was measured over `show`'s marker index rather than the entries it converts, it misses three unindexed ids, and it routes three example-mac rulings into example-app against the owner's own sentence. Fold B1 to B5 and M1 to M4 in the second pass; the minors are line edits, and m8 means cutting before folding.

---

Coordinator's note, 2026-09-22 (Fable, the first coordinator of sitting 2026-09-22-3): saved verbatim at the session budget's 80% line; the folds are NOT yet landed. They are the next coordinator's first act: cut §2's measured rows and §1's second paragraph first (m8), then fold B1 to B5 and M1 to M4 in-line as the table's last column says, then the minors; the record's status row becomes "r1 fold 1 from refuter 1"; the change-log gains one row naming this report. §10 gains decision C (B1: R25-87 to R25-89 go to example-mac by a second run) as a stated design, not a question, since 0001 (4) already rules it; and B2's lettered ids are a rule (`--ids` only). The three counts B3 corrects (66/25, R25-85 at 6,469 bytes, 103,047 bytes) replace mine, which measured `show` output, not entries.
