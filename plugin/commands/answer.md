---
description: Enter the owner's answer to open question N in the ledger
argument-hint: "N (--pick L | --other T) --source S [--text P | --add S] (--area A | --amends M [--shorter] [--move-to A] | --no-entry) [--into PATH] [--every-turn] [--preview]"
allowed-tools: Bash(agentik-decisions *)
disable-model-invocation: true
---

Run `agentik-decisions answer $ARGUMENTS` and relay its output verbatim. Run it only on
the owner's answer: a pick from AskUserQuestion, or the text on the question's
**Your answer:** line. `answer` reads the question's **Your answer:** line and the
text under it: text that names an option takes only `--pick` of it, and any other
text only `--other`, whose Answered line keeps the owner's words. `--text` is the entry's body only, never its bold title
or its `(date; source)` tail, which `answer` writes; a `--text` holding either
is refused. It is needed except with `--no-entry`; with `--amends M` it is the
whole paragraph in force after the answer, every sentence that stays with the
change made: one that drops a sentence is refused unless `--shorter`, and
`--add S` in its place appends S to the paragraph as it stands. `--amends M`
writes M's tail in form T2, its first date, a count of the older amendments and
this one whole, and prints the tail it cut as `tail was:`. A line no part of its
block takes, and a line HEAD's copy of the block lacks, refuse `--pick`; `--other` keeps them in the Answered line; with no copy of question N in git's HEAD, it exits 2: read the block first, since a commit makes its lines the block's own and `--other` must then carry the owner's words, and commit OPEN-QUESTIONS.md.
One of `--area`, `--amends` and `--no-entry` is required. `--area A` resolves
as `agentik-decisions show --area A` does, a unique prefix included, but among the
headings above the legacy marker only, and `Every session` and `Every session of the tree` only by their whole names; the output names the heading it matched,
and a name no heading matches makes a new area. `--move-to A`, with `--amends M` alone, moves the amended entry last under A, resolved as `--area` is.
`--into` names the CLAUDE.md that holds the ledger's block when
it is not the one beside the ledger; pass the same `--into` that
`agentik-decisions render` uses. The block is loaded on every turn: its line
names its growth, and growth under `Every session`, or of the tree's file under `Every session of the tree`, is refused, exit 2, unless `--every-turn`, passed
only on the owner's word. `--preview` makes every check, prints the entry, each file's diff and its bytes beside the ceiling, and writes nothing.
