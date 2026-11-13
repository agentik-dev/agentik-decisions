---
description: Each repo's NICE_TO_HAVE.md placed against its HANDOFF.md build order
argument-hint: "[REPO...] [--order FILE] [--check [--write]] [--json]"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions backlog $ARGUMENTS` and relay its output verbatim. Only `--check --write`
writes: it moves each landed `building` row of the `--order` FILE to
`history/handoff-done.md`. `--check` alone holds each row's state cell against git and
exits 1 on a stale one. Only a `--no-ff` merge reads as a landing: a fast-forward or a squash
leaves the row `building` until it is typed `done`. An item printed `S4?` carries no level and is placed as S4. A closed lead
(`**Closed`, `~~`, `[x]`) is no item: `N closed, not placed` counts it.
