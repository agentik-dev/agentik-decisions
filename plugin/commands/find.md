---
description: List the ledger entries whose title or body holds a word
argument-hint: "<word>"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions find $ARGUMENTS` and relay its output verbatim. No output means
no entry holds the word.
