---
description: Closed NICE items and S4 ones past their days, moved to history/NICE-overflow.md
argument-hint: "[REPO...] [--order FILE] [--days N] [--write] [--json]"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions expire $ARGUMENTS` and relay its output verbatim. Without
`--write` it writes nothing. It lists each closed item, each open S4 or `S4?` item
dated more than N days ago (14) on no open step, the older S1 to S3 ones to lift
into HANDOFF.md or close, and the undated ones, which never expire. `--write`
belongs in a commit of its own: once HEAD holds NICE_TO_HAVE.md, it appends those
lines byte for byte to history/NICE-overflow.md and takes them out. Close an item
by opening its `finding`, or its bullet, with
`Closed YYYY-MM-DD <sha, history file or void>: ` and then its lead, shortened so
the row stays within 400 characters.
