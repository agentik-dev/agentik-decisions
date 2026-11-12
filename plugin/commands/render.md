---
description: Lint the ledger, then write or check its generated block in CLAUDE.md
argument-hint: "[--scope tree] [--into <path>] [--check | --lint | --fold-tails] [--ceiling]"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions render $ARGUMENTS` and relay its output verbatim. Exit 1 means a
lint problem, each printed as `file:line: message`, or with `--check` a stale
block. `--fold-tails` first writes each tail in force in form T2, `(FIRST; amended K
times, A to B; amended DATE, source)`, and exits 2 unless git's HEAD holds the
ledger as it stands, so git keeps every tail it cuts whole. The block is loaded on
every turn: a write names its growth, `X B to Y B, +D B`, and a clean `--lint`
prints its size. `--scope tree` writes the ledger's `Every session of the tree`
alone, the whole file, into the CLAUDE.md of the folder that holds the repo; it
never replaces a file it did not write, and `--check` fails when that file is
absent or stale. Without `--into` it refuses a folder that holds another tree's folder of
checkouts, since a file there would load in that tree too; a plain `--into` never
replaces a tree's file. `--check` and `--lint` print the file's loaded bytes beside its
ceiling, and `--ceiling` exits 1 when it is over. `--lint` warns on an `Every
session` title outside the ten behaviours and on a rule word in a hand-written
line; a warning never changes the exit.
