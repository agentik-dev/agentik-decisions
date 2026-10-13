# Second sitting of agentik-decisions: the conversion question, the writing verbs, the generated index

You are the coordinator of the second sitting in `agentik-decisions` (private, the owner's account, remote `origin`). The first sitting (2026-09-22) wrote the design record, had it refuted and folded, built and merged the settled core (`show`, `scope`, the legacy fallback; 43 tests), and put four decisions to the owner, who ruled them in his own words as `decisions/0001-decisions-as-files.md`. This prompt is self-contained.

## Read, in this order, and nothing else to start

1. `CLAUDE.md` (the contract; its authority line names record 0001 and the retrieval rule).
2. `history/sittings/2026-09-22-2.md` (the closed charter; its handover lists five items, (a) to (e)).
3. `/usr/bin/python3 src/decisions.py show 0001` (the owner's ruling, whole: four sub-decisions, each with its rejected shape). Never paraphrase it; quote it.
4. `design/decisions-r1.md` §3 to §5 whole (the tool, the plugin, the gates: `sed -n '83,171p'`), and §2 by need. Do not read §7 (ruled; 0001 supersedes its decision 4 routing) or §6 whole. The record is 40,408 of 40,960 bytes: any fold moves history out or stays terse, and this record has ONE pass left of its three.
5. `history/packets/core.md` and `history/packets/core-report.md` (the packet shape that worked, and the builder's HOW decisions, which stand).

Then open the sitting: `history/sittings/2026-09-22-3.md` (or the date's next number) under 4 KB in the shape of the closed charters. Rules 5 to 8 of example-mac `docs/session-budget.md` bind: 180k / 400, charter current at 80%, respawn at a checkpoint; up to FIVE Opus at a time for well-defined tasks (the owner's word of 2026-09-22), all design and refutation by Fable.

## The goal of this sitting

Three acts, each its own commit or merge, in order. Stop after any act if the budget says so; the charter carries the handover.

**Act 1: the conversion question, designed and refuted (Fable).** Record 0001 (1): the owner is "open to intelligently refactoring the old OWNER-DECISIONS.md file" as long as "we capture the critical decisions we made". Write `design/ledger-conversion-r1.md`, under 16 KB, pinned to `reference/example-ops/` as decisions-r1 is: what a tool-drafted conversion of the IN-FORCE set is (91 index rows open with `IN FORCE` at the pin; the sub-decision spans `show` already cuts; the owner's quoted words inside each entry as `## Words`; the index's `governs` cell as the tag seed, mapped onto a closed example-app vocabulary); what it produces (records with status `proposed`, one per in-force ruling, in the EXAMPLE-APP repo per 0001 (4), reviewed and ruled by the owner in batches of at most eight, per the flapping guardrails); what it never does (touch the ledger, invent words, rule); its consumer (`scope --governs <wall>` over example-app with real tags, replacing the substring match over free text); and the verb's shape (`convert --from-legacy [--status in-force] --out <dir>`, exit codes as §3.2). Name the models it follows per 0001 (2): adr-tools' `generate toc` and the CI-checked index pattern (`research/05-adr-with-agents.md` §6b), and say what is leveraged directly and what is modelled. One Fable refuter pass, read-only, intent-coverage rows for 0001 (1), (2) and (4); fold in-line; commit the report beside the record. Decisions for the owner, if any, in plain language with a consumer each; ask nothing that nothing waits on.

**Act 2: the writing verbs and the generated index (up to four Opus builders, one packet each, under 8 KB, quoting decisions-r1 whole sentences; the builders never receive the record).** Packets, cut by the coordinator from §2 and §3 of the record and from 0001:
- P1 `init`, `new`, `supersede`, `rule` (§3.3 rows; `rule` refuses under `CLAUDECODE`; `supersede` writes both links, `rule` writes status only; `new` refuses an unknown tag and an id collision including legacy ids). Tests over `tests/fixtures/sample/` plus a temp dir.
- P2 `index [--check]` and `render <target> [--check]` (§3.3, §3.5; the marker pair `<!-- BEGIN GENERATED: decisions -->` / `<!-- END GENERATED: decisions -->`; byte-identical reruns; the packet names adr-tools' `generate toc` as the model of the one-line index and quotes 0001 (2)).
- P3 `check` v1 (§3.3's lint list, including all eight front-matter fields present; the sample fixture gains its `governs` file and `superseded-by:` lines) and `stats` (counts only).
- P4 the plugin under `plugin/` (§4: `skills/decisions/SKILL.md` under 500 lines with the four parts; `commands/show.md`, `scope.md`, `new.md`; `hooks/hooks.json` with the PreToolUse deny on `agentik decisions rule`; `scripts/deny-rule.sh`; a shell test feeding the hook two JSON lines).
Each builder works in its own worktree under `.claude/worktrees/<packet>` on branch `<packet>`, commits per item, never pushes. P1 and P2 both touch `src/decisions.py`: run P1 first, then P2 and P3 from P1's merge; P4 is independent. The coordinator merges each on a green `make check` over the merged tree, and never pushes red.

**Act 3: dogfood and the two unverified claims.** After the merges: `agentik decisions check` and `agentik decisions index --check` join this repo's `make check`; `agentik decisions index` writes `decisions/INDEX.md` for record 0001 and it is committed; `make install` wraps `uv tool install .` and is tried once (report the exit line, do not fix `uv` itself); `claude plugin install` from this repo is tried once to prove the marketplace `source: "./plugin"` subtree (decisions-r1 §4.1 marks it unverified); each result goes into the record's change-log as one row, measured, and a failure is a handover item, not a redesign.

## Rules that bind every act

- Stdlib python3 only (`#!/usr/bin/python3`, 3.9-compatible, Apple's 3.9.6; never `env python3`). No dependencies. The plugin carries no data.
- Fable designs and refutes; Opus builds against a packet; a builder commits per item and reports under the packet's §6 cap.
- The owner rules; agents draft. Only `rule` changes a status, and no agent runs it. A status set by hand, as 0001's was, is not repeated: from this sitting `rule` exists.
- Quote, never paraphrase, the owner's sentences (0001 `## Words`) and the record's sentences in packets.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` (or the builder's model). Never push a red `make check`. Never edit `reference/`.
- Unknown is never a pass: a claim you cannot verify at a pin is reported as unverified, in the record.

## Outside this sitting (the owner's hands)

- Rule the conversion question's decisions, if Act 1 puts any.
- The example-app sitting that runs `init` in the example-app repo, seeds its `governs` from the archtest classes and the session model's components, and changes the L3 archtest (decisions-r1 §5): a prompt for it is this sitting's closing handover, written only if Act 2 merged P1 and P2.
- Register the repo in example-mac `repos.yaml`; ratify or discard the two respeak lexicon proposals under `.claude/respeak/proposals/`.

## Exit

The charter's exit line filled; Act 1's record and refuter report committed; every merged branch green; `history/sessions/NEXT` rewritten to the next prompt's path only if there is a safe next phase (R25-88 (1)), otherwise removed; `main` pushed green.
