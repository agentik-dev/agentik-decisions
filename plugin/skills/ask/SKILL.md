---
name: ask
description: >
  Ask the owner the open questions in a repo's OPEN-QUESTIONS.md in one batch
  through AskUserQuestion, then enter each answer with decisions answer.
allowed-tools: Bash(decisions *), AskUserQuestion
---

# Ask

The owner is asked once per session, in one batch: when the sitting blocks on
the owner, or at close.

1. Run `decisions ask`, which takes every open question, or
   `decisions ask N...` for the ones named. It renders the open questions
   through respeak once, writes them back into OPEN-QUESTIONS.md, and prints a
   JSON list of AskUserQuestion calls. A warning with exit 0 means the text
   stayed as it was; exit 2 names an unknown N or a held lock. A question
   whose **Your answer:** line is filled in is not asked: run
   `decisions answer N` for it first, from that line. A question the lint
   refuses is not asked either; its warning names the fault.
2. Pass each call to AskUserQuestion as it stands, back to back in one turn.
   Never reword a question, a label or a description.
3. For each answer, run
   `decisions answer N (--pick LABEL | --other TEXT) --source S [--text P] (--area A | --amends M [--shorter] | --no-entry) [--into PATH]`.
   `--pick` takes the label chosen. For "Other", `--other` carries the owner's
   text, restated in plain words. `--source` carries the tail's source: the
   owner's word, where it was given, and the file that records it, such as
   `the owner's word, given in this sitting and recorded in <charter>`.
   `--text` is the entry's body only, never its bold title or its
   `(date; source)` tail: `answer` writes both, and refuses a `--text` that
   opens with a bold title or ends in a dated tail. `--area` names the area
   of a new entry N: choose it from the ledger's `###` areas, which
   `decisions show --area NAME` lists, exiting 2, when NAME matches none;
   name a new one only when none fits. `answer` resolves `--area` as `show`
   does, so a unique prefix reaches the existing area, and two matches are
   refused; it skips the headings below the legacy marker and takes
   `Every session` only by its whole name. `--amends M` replaces the
   paragraph of entry M, and `--no-entry` enters an answer that changes no
   entry. With
   `--amends M`, `--text` is the whole paragraph in force after the answer:
   every sentence of M that stays, with the change made, never the change
   alone; M's title and tail stay as they are. The run prints `replaced:`
   with M's old paragraph; a paragraph under half the old one's length is
   refused unless `--shorter`. When the
   ledger's block lives in a CLAUDE.md that is not beside it, pass the same
   `--into` that `decisions render` uses: the cross-repo ledger's block is in
   the user-level CLAUDE.md, `--into ~/.claude/CLAUDE.md`.
4. A result with `afkTimeoutMs` is no answer: the question stays open, and it
   is not asked again this session.
5. A sitting without AskUserQuestion, such as a relay child, runs
   `decisions ask` at close for the render alone. The owner answers on the
   **Your answer:** line, and the next attended sitting enters that answer
   with `decisions answer`.
