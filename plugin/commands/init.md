---
description: "Start a repo's decisions: an empty DECISIONS.md and its block in the CLAUDE.md beside it"
argument-hint: "[--ledger PATH]"
allowed-tools: [Bash(*/bin/agentik-decisions init*)]
disable-model-invocation: true
---

!`${CLAUDE_PLUGIN_ROOT}/bin/agentik-decisions init $ARGUMENTS`

The plugin's own launcher runs this, never one on PATH: a person who installed the plugin
alone has no agentik-decisions on the terminal. It writes the ledger at the git top, or at
--ledger, and the block in the CLAUDE.md beside it, below any hand-written lines, and lists
both files on the repo's edit-gates list. Where a ledger is already there and the
CLAUDE.md beside it holds no block, it adds the block alone and leaves the ledger as it is.
Relay its output verbatim, or its error and exit
code. Do not retry unless the user asks.
