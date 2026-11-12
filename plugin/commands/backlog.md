---
description: Each repo's NICE_TO_HAVE.md placed against its HANDOFF.md build order
argument-hint: "[REPO...] [--order FILE] [--json]"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions backlog $ARGUMENTS` and relay its output verbatim. It writes
nothing. An item printed `S4?` carries no level and is placed as S4. A closed lead
(`**Closed`, `~~`, `[x]`) is no item: `N closed, not placed` counts it.
