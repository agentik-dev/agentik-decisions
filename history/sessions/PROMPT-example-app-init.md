# The example-app sitting: `init`, the `governs` seed, the L3 archtest

You are the coordinator of a sitting in `example-app` (private, the owner's account). This prompt is self-contained. The sitting edits the repo only: it never reaches the NAS (`example-app --context nas-ops` is not run here, the NAS's admin shell never), and it never edits `example-ops`.

## Read first, and nothing else to start

1. `example-app/CLAUDE.md`, then `agentik-decisions/CLAUDE.md` (the contract; its authority line and the retrieval rule).
2. `agentik decisions show 0001` run in `agentik-decisions`: the owner's four rulings, whole. Quote them, never paraphrase.
3. In `agentik-decisions`: `design/decisions-r1.md` §2.5, §5, §6 (`sed -n '67,82p;165,190p'`) and `design/ledger-conversion-r1.md` §5 and §7 (`sed -n '65,69p;83,89p'`). Never either record whole; never `reference/` whole.
4. The tool is `decisions` on PATH (`~/.local/bin/decisions`, put there by `make install` on 2026-09-22), else `/usr/bin/python3 agentik-decisions/src/decisions.py`. Every verb: `agentik decisions --help`.

## What waits on the owner (name it in the charter; stop at the act that waits)

- `design/ledger-conversion-r1.md` §10 A: convert the 91 in-force rulings and R25-86 into example-app `decisions/` as `proposed` files, ruled in batches of at most eight. §10 B: a converted record's `## Words` is the ledger entry whole. Unruled on 2026-09-22. Without A there is no `decisions/legacy-map` and no `convert` packet; acts 1 to 3 below stand without it.
- `design/decisions-r1.md` §3.1: `src/decisions.py` is 1,321 lines against "under a thousand"; split the module or lift the line. Blocks nothing here.
- The freeze banner on example-ops's ledger and hand index (`design/decisions-r1.md` §6 item 2) is a example-ops edit for the owner's own session; this sitting only reads them.

## Acts, each its own commit

1. **`init`.** In `example-app`: `agentik decisions init --ids round --legacy-ledger ../example-ops/example-app-v2/OWNER-DECISIONS.md --legacy-index ../example-ops/example-app-v2/OWNER-DECISIONS-INDEX.md`. It writes `decisions/config`, an empty `decisions/governs`, a rendered empty `decisions/INDEX.md`, and prints the two-line retrieval rule: paste it into example-app `CLAUDE.md` under its authority line. Verify: `agentik decisions show R25-89` prints `standing: not indexed`; `agentik decisions scope --governs "the agent contract"` prints legacy rows by substring with the count line; `agentik decisions check` prints `# 0 findings over 0 records`.
2. **The `governs` seed** (Fable cuts it: a design act, not a build). The four archtest classes `substrate`, `orchestrator`, `wiring`, `shared-leaf` (`reference/example-app/arch_test-header.go.txt:15-23`, one line each, the description from that header), plus one tag per component of the session model's table (`reference/example-ops/SESSIONS.md:9-18`: host-capable-unit, cert-observation, backup-health, deploy-store-fence, layer1-platform-services, layer-dimension, retry-safety, capability-absence, wire-table). `tag: description` per line; `agentik decisions check` green. The seed is a reviewed commit to that file; adding a tag later is the same.
3. **The L3 archtest** (`design/decisions-r1.md` §5, example-app paragraph). The marker pair `<!-- BEGIN GENERATED: decisions -->` / `<!-- END GENERATED: decisions -->` goes after the 144 hand rows of `docs/architecture.md` (`reference/example-app/architecture-L3-section.md:177-178` at the pin; re-measure in the live file); `agentik decisions render docs/architecture.md` writes `0 rows.` between them today, byte-identical on a rerun. One Opus builder (claude-opus-5-5, a packet under 8 KB quoting §5's example-app paragraph whole, in a worktree, commit per item, never push) writes `TestArchitectureL3IsCurrent`: it parses the block and the record files itself, no python, and holds the three properties (every ruled record's sub-decisions have a row; every row's status equals its front matter; no row lacks a record). The old test keeps its hand rows and its floor sentence becomes "hand rows end at R25-89; rows from the first file ruling are generated". example-app `make check` gains `agentik decisions check`, `agentik decisions index --check`, `agentik decisions render --check docs/architecture.md`. Go tests green before the merge.
4. **Only after §10 A is ruled yes:** `decisions/legacy-map` (`design/ledger-conversion-r1.md` §5: one line per distinct `governs` cell, `<cell verbatim> => tag[, tag]`, 75 lines, every right-hand tag a line of `governs`; the tool never tokenises a cell). The `convert` packet itself is cut in `agentik-decisions`, not here; the batches follow the owner's pace.

## Rules

- example-mac `docs/session-budget.md` rules 5 to 8: 180k / 400; a charter under 4 KB in example-app `history/sittings/` at open, current at every commit, exit line filled at close. Fable designs and refutes; Opus builds against a packet; the owner rules. No agent runs `agentik decisions rule`: the plugin's PreToolUse hook denies it and the verb refuses under `CLAUDECODE`.
- Commit messages end `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` (or the builder's model). Never push red; never amend or rebase. Never the ledger whole: a ruling is read by id with `agentik decisions show <id> [n]`.
- The first file ruling is R25-90 (`design/decisions-r1.md` §6 item 1); `new` computes it from the ledger's highest and refuses a collision.

## Exit

The charter's exit line filled; every act green on example-app `make check`; the owner's open rulings restated in plain language with a consumer each; nothing pushed unless the owner's word for the session allows it.
