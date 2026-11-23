---
name: audit-claude-md
description: >
  Go through a CLAUDE.md with its owner: what its hand-written lines cost on
  every turn, which are rules for the ledger, and which can leave.
argument-hint: "[<file>]"
disable-model-invocation: true
allowed-tools: Bash(agentik decisions *), Bash(agentik-decisions *), Bash(agentik session gates*)
---

# Audit a CLAUDE.md

Every line of a CLAUDE.md is loaded on every turn of every session started under its
folder. A line earns that only when a session would act differently without it. The
owner typed this command, so the owner's word is present; the owner still says yes
before anything is written.

The file is `$ARGUMENTS`, or the `CLAUDE.md` at the repo's top. You audit its
hand-written lines. The block between the GENERATED markers is the ledger's text, and
`agentik decisions audit` reads that.

- If step 1 says there is no ledger, stop: `/decisions:init` starts one, and a rule you
  find needs a ledger to move into. If `agentik` is not found, `/decisions:install-cli`.
- If the file is outside this repo, go as far as step 4 and write nothing.

## The walk

1. **Measure.** Run `agentik decisions render --lint`, with `--into <file>` when the
   file is not the `CLAUDE.md` beside the ledger. Keep its line that says what the file
   loads, and each warning about a hand-written line. Read what a session here loads
   beside this file: the `CLAUDE.md` in the home folder's `.claude`, each `CLAUDE.md`
   in a folder above the repo, and each file an `@path` line imports.
2. **Sort each item**, a bullet, a paragraph, a table or an import, under the first
   name that fits:
   - **rule**: it forbids or requires. It becomes a ledger entry with its words and
     its reason kept, under `Every session` only when it binds every turn.
   - **twice**: the ledger, the block or another loaded file says it. It leaves; name
     the copy that stays.
   - **stale**: it names a path or a command that is gone (check each), or it tells
     history. It leaves, or is corrected when the thing only moved.
   - **one act**: it is needed for one act and on no other turn. It moves to a page in
     the repo, and one line naming the act and the page stays.
   - **in the repo**: a session reads it off the README, the Makefile or the tree in
     one look. It leaves.
   - **for people**: it is written for a human reader. It moves into an HTML comment,
     which no session loads, or to the README.
   - **import**: an `@path` line loads its whole file on every turn. It becomes a line
     naming when to read that file.
   - **keeps**: it is true only here, and you can name the act a session would get
     wrong on an ordinary turn without it. It stays, word for word.

   Where a name does not settle an item, load the `decisions:instruct` skill and use
   the eight tests on its page.
3. **Draft** the file as it would stand, the block untouched, in a new file outside
   the repo. Run `agentik decisions render --lint --draft <draft>`, with `--into <file>`
   as in step 1, and keep its line too.
4. **Show** one table, a row an item: its lines, its first words, its name and what
   happens to it. Under it give what the file loads now and as drafted, each figure
   copied from the tool's line and never counted by you. Then give each rule as the
   entry it would be. List apart any "never" that would leave or narrow; propose that
   only when the owner asks for it.
5. **Ask once**: all of it; the moves and removals without the ledger entries; some,
   which the owner names; or nothing. On nothing, delete the draft and stop.
6. **Write through the `decisions:instruct` skill's flow**, the owner's pick standing
   as the owner's word. Entries first: each rule by `agentik decisions new`, your draft
   its recommended option, then the owner's answer. A rule's line leaves the file only
   once `agentik decisions show N` prints its entry. Then the new pages. Then the hand
   text: when an edit-gates list names the file, by `agentik session gates write <file>
   --from <draft> --preview`, its diff shown, then `--expect <hash>`; when none names
   it, by an ordinary edit. If the gate refuses and that command is not installed,
   print the diff for the owner to apply.
7. **Check and say.** `agentik decisions render --check` is clean. Say the two figures,
   what moved where, and that sessions started from now on load the new text. Offer
   the commit by explicit path, its subject `instruct: audit: <file>`.

## What you never do

- Write inside the generated block, edit a ledger by hand, or change an edit-gates
  list.
- Reword a line that keeps, or shorten a rule on its way to the ledger: a rule cut for
  size loses its reason.
- Add a line. An audit moves and removes.
- Write before the owner's yes, or write what the owner did not pick.
