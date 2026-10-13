---
description: Put a question to the owner in four parts, with its Proposed line
argument-hint: "--title T --stands S --choice C --option \"L: E\" ... --recommend R [--report P]"
allowed-tools: Bash(decisions *)
---

Run `decisions new $ARGUMENTS` and relay its output verbatim. When a part is
missing, ask for it in plain words first: where things stand, the choice, what
each answer sets in motion, and the recommendation. Two to four
`--option "Label: effect"` flags name the answers, the first the recommended one.
