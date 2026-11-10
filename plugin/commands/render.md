---
description: Lint the ledger, then write or check its generated block in CLAUDE.md
argument-hint: "[--into <path>] [--check | --lint | --fold-tails]"
allowed-tools: Bash(agentik-decisions *)
---

Run `agentik-decisions render $ARGUMENTS` and relay its output verbatim. Exit 1 means a
lint problem, each printed as `file:line: message`, or with `--check` a stale
block. `--fold-tails` first writes each tail in force in form T2, `(FIRST; amended K
times, A to B; amended DATE, source)`, and exits 2 unless git's HEAD holds the
ledger as it stands, so git keeps every tail it cuts whole. The block is loaded on
every turn: a write names its growth, `X B to Y B, +D B`, and a clean `--lint`
prints its size.
