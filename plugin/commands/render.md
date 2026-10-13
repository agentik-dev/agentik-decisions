---
description: Lint the ledger, then write or check its generated block in CLAUDE.md
argument-hint: "[--into <path>] [--check | --lint]"
allowed-tools: Bash(decisions *)
---

Run `decisions render $ARGUMENTS` and relay its output verbatim. Exit 1 means a
lint problem, each printed as `file:line: message`, or with `--check` a stale
block.
