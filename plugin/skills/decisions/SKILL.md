---
name: decisions
description: >
  Consult, cite and draft the entries of a repo's DECISIONS.md. Use before
  touching a decided area, when a question needs the owner, or when cutting a
  packet or brief.
allowed-tools: Bash(decisions *)
---

# Decisions

A repo keeps its decisions in one `DECISIONS.md` at its root. This skill
carries the manners for reading and drafting them with the `decisions` tool,
and it carries no data.

## 1. The ledger

- `## In force` holds `### Every session` first when present, then one
  `### <area>` per area. Each entry is one line:
  `N. **Title.** paragraph (date; source)`. The tail opens with the date, and
  a title that ends in `?` or `!` takes no period.
- `## Proposed` holds one line per open question:
  `N. **Title.** one sentence (proposed YYYY-MM-DD; OPEN-QUESTIONS.md)`.
- `## Superseded` holds one line per retired entry, naming its replacement.
- Numbers are unique across the three sections and never reused. At most 25
  entries are in force, and at most 7 sit under `Every session`.
- An older ledger in another shape puts an empty `## In force` and the line
  `<!-- decisions: legacy below -->` above its old text, then takes new
  entries in this shape. The text below that line is read by `show` and
  `find`, and the lint passes over it.

## 2. Reading

- The `Every session` entries arrive in the CLAUDE.md block that
  `decisions render` writes, with one line for each other entry in force.
- Before touching an area, read it: `decisions show --area <name>` prints the
  whole area, and `decisions show <n>...` prints the entries named.
- `decisions find <word>` lists the entries that mention a word.
- Read by entry or by area, and never read the ledger whole.

## 3. Handing decisions to another agent

A packet or a sub-agent brief carries a `Decisions:` line naming the areas and
the entry numbers the task touches, for example `relay; 12`. Paste the output
of `decisions show` under it verbatim, so the builder reads no ledger. Never
paraphrase or trim an entry: a paraphrase is new, undecided text.

## 4. Drafting

- Only the owner's answer moves an entry into `## In force` or out of it. An
  answer enters the ledger through `decisions answer`, and an agent edits an
  entry in force only by `decisions answer --amends`, on the owner's answer.
  Its `--text` is the whole paragraph in force after the answer: every
  sentence that stays, with the change made. In every answer `--text` is the
  body only: `answer` writes the bold title and the `(date; source)` tail, and
  refuses a `--text` that opens with a bold title or ends in a dated tail.
- Put a question with `decisions new`, in four parts: where things stand, the
  choice, what each answer sets in motion, and the recommendation. Two to four
  `--option "Label: effect"` flags name the answers, the first the recommended
  one. It writes the question into OPEN-QUESTIONS.md and a Proposed line into
  the ledger, both under the same new number.
- Ask the owner once per session, in one batch: the ask skill runs
  `decisions ask` and puts the open questions through AskUserQuestion.
- Settle a reversible choice inside the design, and log it in one sentence
  under `## Decided without asking` in OPEN-QUESTIONS.md.
- Before taking S4 work, run `decisions backlog`, which places each item of
  NICE_TO_HAVE.md against the build order in HANDOFF.md.
- Write an entry in plain present-tense English. Its first sentence states the
  decision whole, and its closing parenthetical names the date and the source.

## 5. Keeping the block fresh

After the ledger changes, `decisions render` rewrites the block in the
CLAUDE.md beside it. `decisions render --check` prints the diff and exits 1
when the block is stale, and a lint problem exits 1 in every mode.
