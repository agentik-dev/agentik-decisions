---
description: Enter the owner's answer to open question N in the ledger
argument-hint: "N (--pick L | --other T) --source S [--text P] (--area A | --amends M [--shorter] | --no-entry) [--into PATH]"
allowed-tools: Bash(agentik-decisions *)
---

Run `agentik-decisions answer $ARGUMENTS` and relay its output verbatim. Run it only on
the owner's answer: a pick from AskUserQuestion, or the text on the question's
**Your answer:** line. `--text` is the entry's body only, never its bold title
or its `(date; source)` tail, which `answer` writes; a `--text` holding either
is refused. It is needed except with `--no-entry`; with `--amends M` it is the
whole paragraph in force after the answer, every sentence that stays with the
change made, and `--shorter` lets through one under half the old one's length.
One of `--area`, `--amends` and `--no-entry` is required. `--area A` resolves
as `agentik-decisions show --area A` does, a unique prefix included, but among the
headings above the legacy marker only, and `Every session` only by its whole
name; the output names the heading it matched, and a name no heading matches
makes a new area.
`--into` names the CLAUDE.md that holds the ledger's block when
it is not the one beside the ledger; pass the same `--into` that
`agentik-decisions render` uses.
