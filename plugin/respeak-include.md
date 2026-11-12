<!-- respeak include v3, inputs 4a91c210; regenerate with /respeak:include, do not edit -->
# How to write in this repo

What a person reads: replies to the user, and `README.md`, `DECISIONS.md`,
`DESIGN.md`, `NICE_TO_HAVE.md`, `OPEN-QUESTIONS.md`, `HANDOFF.md` and
`design/readme/`. Write it for a peer engineer in technical mode: the
conclusion first, then the evidence as file:line or the command that shows
it, then open questions. When the user names another reader, switch mode:

- eli5 (a newcomer, "plain English"): one idea per sentence, at most one
  analogy, and the next sentence says the real thing.
- bluf (a manager, "bottom line"): the result, decision or ask first, with
  owner and deadline; a manager can forward it unedited.

Never shorten error messages, security findings, the user's quotes, or
numbers with units, whoever reads the text.

In every mode: short sentences, active voice, concrete words; no filler
openers, no hype, no closing recap. Done, fixed, passing or green needs a
tool result that shows it; else say claimed, not verified, and what would
verify it.

The respeak plugin is optional: with it, `/respeak:respeak [mode]` renders a
narrative; without it, follow them by hand.
