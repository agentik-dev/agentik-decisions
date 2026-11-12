---
description: The ledger's retire and rewrite candidates, Every session first with the bytes each costs
argument-hint: "[REPO...] [--tree FILE] [--json] | --edits C [REPO] [--json]"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions audit $ARGUMENTS` and relay its output verbatim. It edits
nothing. Each candidate names its marks: P2 amended three or more times, P3 a tail
that says it moved, P4 a tail longer than its paragraph, P5 nothing in the tree
cites it, P6 a path or verb gone; P1 in the head line, the ledger at its cap. P8 is
a lead for a reader to confirm, and P7 is not detected. The owner acts in one batch
with `new`, `ask` and `answer`; a retire moves the entry's line under
`## Superseded` by hand.
`--edits C` lists each commit after C that touches instruction text without an
`instruct:` subject: a list for the owner, exit 0 either way.
