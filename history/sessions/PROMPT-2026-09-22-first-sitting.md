# First sitting of claude-code-decisions: the design record r1, one refuter pass, then the settled core

You are the coordinator of the first sitting in `claude-code-decisions` (private, the owner's account). The repo was seeded on 2026-09-22 from a research sitting on Architecture Decision Records; nothing is built and nothing is ruled. This prompt is self-contained: the repo's memory directory is empty, and the research sitting's conclusions are in the files named below, not in any memory.

## Read, in this order, and nothing else to start

1. `CLAUDE.md` (the contract, under 1.5 KB).
2. `README.md` (the problem, the vision, what the tooling does).
3. `research/06-evaluation.md` (the verdict, the incorporation plan, the tool/plugin split, the four open decisions). Reports 01 to 05 carry the citations; open one only when 06 sends you there.
4. `reference/SOURCES.md`. The snapshots it lists are pinned copies for grepping; never read one whole (the ledger is 240 KB).

Then open the sitting: write `history/sittings/2026-MM-DD-1.md` under 4 KB in the shape of `reference/example-ops/charter-example-2026-09-22-2.md` (goal, budget, pins, window, agents; done-ness; handover; next act). Rules 5 to 8 of `reference/example-mac/session-budget.md` bind: 180k context / 400 turns, bring the charter current at 80%, respawn at a checkpoint, three Opus at a time, media never re-enters context.

## The goal of this sitting

Three acts, each its own commit, in order. Stop after any act if the budget says so; the charter carries the handover.

**Act 1: `design/decisions-r1.md`, the record of record, under 40 KB.** Its sections:

- §1 The essence: the invariants, quoted verbatim from `research/06-evaluation.md` Part 3. They are the data model; do not restate them in other words.
- §2 The record format: the front matter fields (id, date, status, governs, supersedes, superseded-by, consumers, verify); the body (the decider's verbatim words, the numbered sub-decisions, the rejected shape per sub-decision, a pointer to the design record section); the status vocabulary (proposed, in-force, superseded, retracted, spent); the per-repo `governs` vocabulary file; ids (sequential for new repos; example-app keeps R-ids). Pin the sub-decision as the unit served (`reference/example-ops/build-packet-r1.md` line 111 and its refuter's B2).
- §3 The tool: one stdlib python3 module; the verbs `init`, `new`, `show`, `scope`, `index [--check]`, `render`, `supersede`, `check`, `stats`, `rule`; inputs, outputs, exit codes; the legacy fallback over a configured ledger and hand index (the fixtures in `reference/example-ops/`); the generated-block-between-markers renderer; the install path (`uv tool install`, brew formula as the end state). Follow the pattern of `reference/example-ops/cite-check.py` for pinned inputs and exit codes.
- §4 The plugin: one skill under 500 lines carrying the manners and the inline-versus-retrieve threshold; the slash commands; one PreToolUse hook denying agentic `rule`; no data in the plugin. Layout as `reference/plugins/` shows (plugin.json, marketplace.json, `skills/<name>/SKILL.md`, `commands/`, `hooks/hooks.json`).
- §5 The gates: `index --check` and `check` in `make check` and a pre-push hook; for example-app, the successor of `TestArchitectureL3CoversTheDecisionLog` (`reference/example-app/architecture_l3_completeness_test.go`): "the generated block is current", never "every id has a hand row".
- §6 The first consumer, example-app: what changes (rulings are files from R25-88; the ledger freezes as history; the L3 table becomes a generated block; packet §2 and refuter briefs are `scope` output) and what does not (no conversion of the 212 rulings; the adversarial round stays; `SESSIONS.md` line 31's forbidden reads stay).
- §7 The four decisions for the owner, in plain language with context, a few sentences each, each naming its consumer and what it amends (R25-19; R25-60 (5); R25-72 (5); R25-63 (4)). Quote the owner's sentences from `research/02-churn-timeline.md` §4 where they bear. Ask nothing that nothing is waiting on.
- §8 The measure: the win is smaller lookups and fewer repair turns; no token number is claimed until example-ops's burn-report exists; the inline threshold is stated as a model with its three assumptions.
- §9 Out of scope, by name: MADR's optional sections, Y-statements as prose, per-component directories, static-site tooling, MCP servers, history conversion, @-imports of any index, agent-authored rulings.
- A change-log at the end, grep-verifiable: every claim of an edit names the section it landed in.

**Act 2: one refuter pass.** A Fable agent, read-only, given the record and `research/06-evaluation.md`, returns: an intent-coverage row per Part 2 and Part 3 item of 06 (DONE / DONE LESS / DONE DIFFERENTLY), every internal contradiction, every unpinned claim, and a verdict. Fold in-line (never insert above an anchor other records cite); the bound is three passes in total for this record, ever. Commit the refuter's report under `design/` beside the record.

**Act 3: the settled core, only if the refuter leaves §2 and §3's `show` and `scope` standing.** One Opus builder, against a packet you write in the shape of `reference/example-ops/build-packet-r1.md` (under 8 KB; the builder never receives the record), builds: `decisions/` module skeleton, `show <id> [n]` and `scope --governs X --status in-force` over a `decisions/` directory AND the legacy fallback over the fixtures in `reference/example-ops/`, `unittest` tests that prove both, a `Makefile` with `check` (unittest, `python3 -m pyflakes` if present, a shebang and 3.9-compatibility check), and the `.claude-plugin/plugin.json` stub. The builder commits per item on a branch; you run `make check` over the merged tree before merging, and never push red.

## Rules that bind every act

- Stdlib python3 only (`#!/usr/bin/python3`, 3.9-compatible; that path is Apple's 3.9.6 on this Mac, never `env python3`). No dependencies. The plugin carries no data.
- Fable designs and refutes; Opus builds against a packet; at most three Opus at a time; a builder commits per item and reports under a cap.
- The owner rules; agents draft. Decisions are put in plain language with context, a few at a time, each with a consumer. No ruling without a consumer. Measurement precedes claim. Quote, never paraphrase, the owner's sentences.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` (or the builder's model). Never push a red `make check`. Never edit `reference/` (it is pinned; add a new pin as a new file if the origin must be re-snapshotted).
- Unknown is never a pass: a claim you cannot verify at a pin is reported as unverified, in the record.

## Outside this sitting (the owner's hands)

- Rule the four decisions of §7.
- Register the repo in example-mac `repos.yaml` and regenerate the portfolio map (`EXAMPLE_MAC_RUN_GEN=1`, then `make freeze`).
- Decide the repo's visibility (private today because `reference/` holds the owner ledger).

## Exit

The charter's exit line filled; the record and the refuter report committed; act 3 merged only on a green `make check`; the handover set naming what the second sitting starts with.
