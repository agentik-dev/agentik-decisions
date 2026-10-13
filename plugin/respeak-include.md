<!-- respeak include v1, inputs fcaf32e7; regenerate with /respeak:include, do not edit -->
# How to write in this repo

Two lanes. Notes, packets, tool output and messages between agents are the
machine lane. What a person reads is the human lane: replies to the user,
and `README.md`, `DECISIONS.md`, `DESIGN.md`, `NICE_TO_HAVE.md`,
`OPEN-QUESTIONS.md`, `HANDOFF.md` and `design/readme/`.

Machine lane: write in full. Use no shorthand: this repo ships no lexicon.
Never shorten error messages, security findings, the user's quotes, or
numbers with units.

Human lane: write for a peer engineer in technical mode: the conclusion
first, then the evidence as file:line or the command that shows it, then
open questions. When the user names another reader, switch mode:

- eli5 (a newcomer, "plain English"): one idea per sentence, at most one
  analogy, and the next sentence says the real thing.
- bluf (a manager, "bottom line"): the result, decision or ask first, with
  owner and deadline; a manager can forward it unedited.

In every mode: short sentences, active voice, concrete words, no filler
openers, no hype, no closing summary of what was just said.

The respeak plugin is optional. With it installed, `/respeak:respeak [mode]`
renders a narrative and its gate checks these rules. Without it, follow them
by hand.
