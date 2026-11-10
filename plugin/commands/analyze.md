---
description: What a repo's git history says: churn, records written against code landed
argument-hint: "[churn] [REPO...] [--since Nd|YYYY-MM-DD] [--until YYYY-MM-DD] [--json]"
allowed-tools: Bash(agentik-decisions *)
---

Run `agentik-decisions analyze $ARGUMENTS` and relay its output verbatim. It writes
nothing. A value printed `-` was not measured; its `not measured:` line says why.
The `block` line gives the CLAUDE.md block's bytes, loaded on every turn, at both
ends of the window. It is read from the commit's blob, so a CLAUDE.md that is a
symlink reads as no block.
