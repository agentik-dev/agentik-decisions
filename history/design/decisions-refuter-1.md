# Refutation 1 of `design/decisions-r1.md` (r1)

| item | value |
|---|---|
| pin | repo `70d5036`; reference pins example-ops `d2a62d3`, example-app `4dbce58`, example-mac `f4d6389` (`reference/SOURCES.md`) |
| read | the record and `research/06` whole; the sitting prompt; the refuter shape `:1-30`; the fixtures by grep and sed only |
| record | 34,585 bytes (`wc -c`), under 40 KB |
| anchors | `# 79 anchors, 0 bad` |

## §1 What holds

- §1's invariants are verbatim: python equality of `:15-19` against `research/06:125-129` is True.
- The marker rule of `:128` reproduces R25-63 (4) 180 B, R25-86 (13) 237 B, R25-87 (3) 255 B (script in §4). Bold-preferred is load-bearing: `:45` has 23 bold and 61 plain `(n)`.
- Ledger 242,404 B / 1,643 lines; index 41,576 B; `:45` 13,654 B; 66 Form B lines; 214 unique column-1 ids; `:874`, `:883`, `:914` indented; index last R-id row R25-85 at `:287`, no R25-86..89 row; `:1642-1643` both 2026-09-22; L3 section 144 dated rows.
- Every quoted fixture sentence is verbatim (`:84`, `:78`, `:60`, `:671`, `SESSIONS.md:31,57`, `build-packet-r1.md:111`, `r1-brief.md:386-387`, ASSESSMENT `:33,43`, archtest `:14-17`, `research/01:170-171`).
- `CLAUDECODE=1` is exported here; pyflakes is absent from `/usr/bin/python3`; the live `~/.claude/CLAUDE.md:27,75` carry the two `GENERATED: portfolio-map` markers, so the §3.5 claim marked unverified holds.
- The four owner sentences in §7 are substrings of `research/02:71-73`, dates right.

## §2 Intent coverage

| item | mark | § | evidence |
|---|---|---|---|
| P2-1 extractor first, no round | DONE | §3.3, :193 | Act 3; "wait on no ruling" |
| P2-2 six fields, forward-only | DONE DIFFERENTLY | §2.2 | eight fields, as the prompt lists |
| P2-3 generated index + L3, gated | DONE | §3.3, §5, §6.3 | gated; successor test |
| P2-4 lint on proposed records | DONE LESS | :117 | v2 (06 Part 3 defers it too) |
| P2 model + four assumptions | DONE | §8.3 | T=300, C=100k, L=2, ~667 tokens |
| P2 vehicle | DONE | §3.1, §4 | one module; skill body on use |
| P2 per-repo footprint | DONE | §2.1, §2.5, §5 | all five named |
| P2 registry | DONE LESS | :224 | deferred to sitting 2 |
| P2 bound | DONE LESS | :117 | `check` v2 only |
| P2 charter | NOT DONE | none | `grep -ci charter` = 0 |
| P2 new projects | DONE LESS | :51 | layout record; birth-day rule absent |
| P2 don't: `../CLAUDE.md` | NOT DONE | none | grep = 0 |
| P2 don't: over three passes | DONE | :7 | "three passes ever" |
| P3 five invariants | DONE | §1 | verbatim |
| P3 row 1 schema, `new` | DONE | §2, :105 | |
| P3 row 2 verbs, slash commands | DONE LESS | :159 | show, scope, new only |
| P3 row 3 render, threshold | DONE | §3.5, :154 | |
| P3 row 4 legacy lookup | DONE | §3.4 | |
| P3 row 5 gate | DONE | §5 | |
| P3 row 6 manners | DONE | :153 | |
| P3 row 7 `rule`, deny hook | DONE | :115, §4.4 | plus `CLAUDECODE` |
| P3 row 8 semantic contradiction | DONE | :117, §9 | |
| P3 plugin never carries data | DONE DIFFERENTLY | :146 | F5 |
| P3 install paths | DONE | §3.6, §4.1 | |
| P3 v1-1 show/scope + legacy | DONE | §3.3, §3.4 | |
| P3 v1-2 `new` from R25-88 | DONE DIFFERENTLY | §6.1 | R25-90, measured |
| P3 v1-3 index, render, archtest | DONE | §3.3, §5 | |
| P3 v1-4 skill + hook | DONE | §4 | |
| P3 v2 leftovers | DONE | :117, :224 | |
| P3 sizing, no token number | DONE | §3.1, §4.2, §8.2 | |
| Act 1 §1 | DONE | §1 | |
| Act 1 §2 | DONE | §2 | pinned to `:111` and B2 |
| Act 1 §3 | DONE | §3 | ten verbs; F3 |
| Act 1 §4 | DONE | §4 | eight files |
| Act 1 §5 | DONE | §5 | F6 |
| Act 1 §6 | DONE DIFFERENTLY | §6 | R25-90 not R25-88; 214 not 212 |
| Act 1 §7 | DONE | §7 | consumers, amendments, sentences |
| Act 1 §8 | DONE | §8 | 255/237/180 reproduced |
| Act 1 §9 | DONE | §9 | all eight named |
| Act 1 change-log | DONE LESS | :230 | F12 |

## §3 Internal contradictions

1. `:53` "`show <id> <n>` prints one `(n)` paragraph with its `Rejected:` line, never the record; `scope` prints one line per sub-decision." vs `:106` cell "the record whole, or sub-decision n".
2. `:40` cell "the tool only, by `rule` of the successor" vs `:110` "writes `supersedes` into the proposed `new` and `superseded-by` into the in-force `old`; changes no status" and `:115` "for every id in `supersedes` sets that record's status to `superseded` and its `superseded-by` to this id, in one act."
3. `:95` "Exit codes: 0 the answer or the gate holds; 1 a lookup finds nothing or a gate refuses; 2 usage, an unreadable file, a malformed record, a missing config." vs `:105` "2 on an unknown tag, an id collision, no consumer", `:110` "2 unless old is `in-force` and new `proposed`", `:113` "2 on a forbidden transition", `:107` "0, even when empty".
4. `:98` "Every output that quotes a record or the ledger carries its `file:line`, so a packet can anchor it" vs `:107` "one line per matching sub-decision, `<id> (n) <status> <first sentence>`".
5. `:171` "It never skips, because with §7's decision 4 the records are in the same repository, and it cannot go red by omission of a hand step because there is no hand step: the fix is always `decisions render docs/architecture.md`." vs `:169` "`index --check` exits nonzero when the committed index disagrees with the records, and `render --check` when a block is stale, so a ruling that forgot its render is red in the same act."
6. `:146` "The plugin carries no data: no `decisions/` directory is read by anything in it, and the only paths it names are the verbs." vs `:146` "This repo will own a `decisions/` of its own, as any consuming repo does, and the marketplace packages the repo". Measured: both sibling `marketplace.json` set `source: "."`.
7. `:53` "`scope` prints one line per sub-decision." vs `:132` "A legacy row never prints a sub-decision number, because the index has none."

Id scheme vs R25-90 and the §7 dates: no contradiction.

## §4 Unpinned or unverified claims

- `:125` "147 such lines": 148; `:314` `R23-1a.`, `:325` `R23-1b.`, `:343` `R23-2a.` match neither form. Pin: 148 and a rule for lettered ids.
- `:128` "`:78` opens with `(1) a (2) a (3) b ... (4) a`": it reads `(1) b and its fine to port the boards. ... (2) a (3) c (4) a`. Pin: as measured.
- `:130` "`1 (A1)` to `21`, `:9-30`": `:9` is the header, `21 (F21)` is `:31`; 27 unlabelled rows, not 21. Pin: `:11-31` and the other six.
- `:130` standing map: of 210 R-id rows the exact cells are 59 `IN FORCE`, 62 `SPENT`, 0 `SUPERSEDED by <id>`; 32, 26, 18 carry a decoration (`IN FORCE (built)`); 13 mixed. As written 76 print `mixed:`. Pin: prefix match.
- `:195` "except the last four": after `:1600` only R25-87 to R25-89 open a line; R25-86 is `:45`. Pin: three.
- `:6` pin `dd923c9`, file at `70d5036`; `:177` "`README.md:52,58` say R25-88" holds only at `dd923c9`. Pin: both commits.
- `:230` "`README.md:9,52,58`": hunks at 7, 9, 52, 58 (7: 239,623 to 242,404; 212 to 214). Pin: add 7.
- `:199` clipped at a comma; the sentence continues ", and I want to be Fable heavy on these sessions." Pin: whole, or mark the clip.
- `:163` the NAS's admin shell guard stays unverified (no fixture).

```python
import re; L=open("reference/example-ops/OWNER-DECISIONS.md",encoding="utf-8").read().split("\n")
def spans(t):
    m=re.match(r"- \*\*(.*?)\*\*",t); b=t[m.end():] if m else t
    bold=[(x.start(),int(x.group(1))) for x in re.finditer(r"\*\*\((\d+)\)",b)]
    plain=[(x.start(),int(x.group(1))) for x in re.finditer(r"(?<!\*)\((\d+)\)",b)]
    ms=bold or plain; return {n:b[p:(ms[i+1][0] if i+1<len(ms) else len(b))] for i,(p,n) in enumerate(ms)}
for ln,n in ((78,4),(45,13),(1641,3)): print(ln,n,len(spans(L[ln-1])[n].encode()))
print(sum(1 for l in L if re.match(r"^R\d+-\d+\. ",l)), sum(1 for l in L if re.match(r"^- \*\*R\d+-\d+ \(",l)))
I=[l for l in open("reference/example-ops/OWNER-DECISIONS-INDEX.md",encoding="utf-8").read().split("\n") if re.match(r"^\| R\d+-\d+ \|",l)]
c=[[x.strip() for x in r.split("|")][5] for r in I]; print(len(I),sum(x=="IN FORCE" for x in c),sum(x=="SPENT" for x in c),sum(bool(re.fullmatch(r"SUPERSEDED by R\d+-\d+",x)) for x in c),sum(x.startswith("IN FORCE") and x!="IN FORCE" for x in c))
```
From the repo root: `78 4 180`, `45 13 237`, `1641 3 255`, `148 66`, `210 59 62 0 32`.

## §5 Does Act 3 stand?

A builder must decide:

1. `show <id>` with no n over a ledger id: the entry whole (`:106`) or refused (`:53`).
2. Whether `R23-1a` is an id and where `show R23-1` ends (`:125` excludes the letter; `:185` counts it).
3. "the next id line" (`:125`): column 1 only, or markup then an id (`:874`, `:883`).
4. The headline of a Form A entry (`:128` defines it for Form B only); R16-2 has no `(n)`; its expectation is unstated.
5. Plain markers that are cross-references, `R25-60 (5)`, in a plain-marker entry (`:128`): unruled; the fixtures pass.
6. Standing: exact or prefix (`:130`); whether `mixed:` rows match `--status in-force` (`:132`); and `superseded by X` under `--status superseded`.
7. The `show` header for a legacy id (`:106`): `<date>` for Form A and `governs=` have no source.
8. `<first sentence>` (`:107`) is undefined; R25-86 (13) opens inside the owner's quote.
9. Record rows lack `file:line`, legacy rows carry it; `--full` on a legacy row; two count-line texts (`:107`, `:132`).
10. "id then n order" (`:107`): numeric by (round, n) or lexical; where legacy rows sit (`:132`).
11. `scope` with no `[legacy]` and an empty `decisions/`: 0 with `# 0 rows` (`:107`) or 2 (`:93`).

`show` and `scope` STAND WITH FOLDS: F1, F2, F3, F7, and one line each for items 2, 8 and 10. Each fold is a sentence the packet then quotes.

## §6 Findings

| finding | grade | measurement | fix |
|---|---|---|---|
| F1 `show <id>`: "never the record" and "the record whole" | MAJOR | `:53` vs `:106`; `sed -n 45p \| wc -c` = 13,654, the size B2 rejected | n mandatory for a Form B id at `:106`, or strike "never the record" at `:53`. |
| F2 Standing map drops decorated cells | MAJOR | §4: 76 of 210 print `mixed:`; `--status in-force` loses 32 | `:130`: map on the cell's opening words; `mixed:` only otherwise. |
| F3 Exit codes disagree | MAJOR | §3 item 3: `:95` vs `:104`, `:105`, `:110`, `:113`, `:107` | Rewrite `:95` to the table: 2 a verb's refusal, 1 `show` not found and `--check`, 0 `scope` always. |
| F4 Two writers of `superseded-by` | MAJOR | §3 item 2: `:40`, `:110`, `:115` | One writer: `supersede` both links and `rule` the status, or `supersede` writes `supersedes` only. |
| F5 "Carries no data" vs `source: "."` | MAJOR | §3 item 6; `reference/` is 242,404 B | `:146`: say what the copy contains and that the plugin reads none of it, or name a subtree. |
| F6 "Cannot go red by omission" | MINOR | `:171` vs `:169` | `:171`: "red only when `render` was not run; the fix is one command". |
| F7 `scope` rows lack `file:line` | MINOR | `:98` vs `:107` | Add it to the row or exempt `scope` at `:98`. |
| F8 Form A count, lettered ids | MINOR | 148 not 147; `:314`, `:325`, `:343` | `:125`: 148; rule the lettered lines. |
| F9 "the last four" | MINOR | three after `:1600` | `:195`: three. |
| F10 `:78` misquoted | MINOR | `(1) b ... (2) a (3) c (4) a` | `:128`: as measured. |
| F11 Index rows `:9-30` | MINOR | `21 (F21)` at `:31`; 27 unlabelled | `:130`: `:11-31`, name six more. |
| F12 Change-log and pin | MINOR | hunks 7, 9, 52, 58; `:6` vs `70d5036` | Add 7 at `:230`; both commits at `:6`. |
| F13 Owner sentence clipped | MINOR | `:199` ends at a comma | Quote whole or mark the clip. |
| F14 Two Part 2 items absent | MINOR | grep `charter` = 0, `../CLAUDE` = 0 | One sentence each in §9 or §6. |

## §7 Verdict

**PASS WITH FOLDS. 0 BLOCKING, 5 MAJOR, 9 MINOR.**

- The data model, the marker rule and every fixture number that matters reproduce.
- The five MAJORs are one-sentence folds; none changes the design.
- F1, F2, F3 and F7 fold before the Act 3 packet is cut, because the packet quotes those sentences.
- Coverage of 06 Parts 2 and 3 is complete but for the charter line and the `../CLAUDE.md` don't.
- 34,585 of 40,960 bytes. Owner sentences: four verbatim substrings of `research/02:71-73`, dates right, one clipped at a comma. Nothing is asked that nothing waits on (`:195`, `:197`, `:199`, `:201`).
