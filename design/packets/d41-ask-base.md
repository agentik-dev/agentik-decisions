# Packet d41: a question block carries its own base

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief d41 (hq `history/sessions/BRIEF-2026-11-12-decisions-d41-ask-base.md`), NICE n41, S2 |
| pin | main at `f55e5f8` (0.21.11). Version 0.21.12. Worktree `.claude/worktrees/d41-ask-base`, branch `d41-ask-base`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state |
| may touch | `plugin/lib/decisions/questions.py`, `ask.py`, `answer.py`, `selector.py`; `plugin/skills/{ask,decisions}/SKILL.md`, `plugin/commands/answer.md`; `tests/test_d41_base.py` (new), `tests/test_new.py`, `tests/test_ask.py`, `tests/test_answer_head.py` and any test whose fixture holds `new`'s text; `NICE_TO_HAVE.md` (n41 leaves, two rows join); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib python -m unittest tests.test_d41_base` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words: none new. Entry 9 names six verbs, so no new verb; the repo's `CLAUDE.md`: the plugin carries no data, so the base lives in the repo's file.

The fault, measured at `f55e5f8` with a hand script in temp dirs: after `new`, a commit, words typed at the end of an option line and `Pin` on the answer line, and a commit by path, `answer N --pick Pin` exits 0 and the words are in neither file (d35's HEAD rule takes HEAD's copy as the base, and the commit made the words HEAD's). `ask` with a stub render over a block holding words typed into an option rewrites the block, the words gone, and asks it; git never held them.

## 2. Rulings

- R1 the base line: `<!-- decisions: base D D ... -->`, one D per non-blank line from the heading to the line above **Your answer:**, in order; D the first 8 hex digits of the sha256 of the line, its whitespace runs one space. `make_block` reads the first such line above the answer line into `Block.base` (None when absent); it is no part, no stray and no typed text, and `Block.text` leaves it out. Its own paragraph under the heading.
- R2 `new` writes it. R3 `answer`: the owner's lines are those whose digest the base lacks, counted as `since` counts; a block with a base runs no git; one with none reads HEAD as at the pin. R4 `--pick`'s refusal for a block with a base names `--other` alone.
- R5 `ask` skips a block holding a line its base lacks (HEAD's copy for a block with none that HEAD holds): one warning, not written, not in the JSON. R6 `ask` stamps every block it asks under the lock, with a render or without; a block with no base that HEAD lacks gains none. R7 a second base line is a lint problem. R8 the texts say the base line; the `git diff` before `ask` goes.

## 3. Interfaces: the acceptance table

| # | line | at the pin |
|---|---|---|
| 1 | `new`: one base line; `render --lint` 0 | red: no line |
| 2 | type, commit by path, `--pick Pin`: exit 2, files unchanged, words named | red: exit 0, words in neither file |
| 3 | the same with `--other X`: the Answered line holds the words | red: `Other: X` alone |
| 4 | three orders: `--pick` refused, `--other` keeps each line once | red |
| 5 | `new`, `--pick` with no git repository, and git off `PATH`: exit 0 | red: exit 2, "git holds no copy" |
| 6 | `ask`, stub render, words typed in an option: warning, file unchanged, not in JSON | red: block rewritten, words gone |
| 7 | `ask` over a clean block: render input holds no base line; `--pick` with no commit | red |
| 8 | no base line: `test_answer_head` green; `ask` stamps a block HEAD holds, not one it lacks | red |
| 9 | two base lines: `render --lint` 1 naming the question; a typed line: 0 | red |
| 10 | every other test green; changed fixtures listed | |
| 11 | `make check` green through the queue, once, last | |

## 4. Findings that name this row: ledger, NICE, forks

n41 leaves `NICE_TO_HAVE.md`; two rows join: n82, `head_block`'s removal once no base-less block is left, and n83, a damaged or deleted base line puts its block under HEAD's rule. The owner's fork is closed: the base line as built, decision 39 (2026-11-12).

Round 1 of the review: 2 findings, 0 blocking, both to NICE: F1 is n83 reworded (a damaged base line, then a commit and `ask`'s stamp, loses the words even under `--other`), F2 is n84 (a second base-shaped line the owner types leaves `Block.text`). The last pass also files n85 and n86 from d39's review r1 (`backlog --check`), and merges main at `9e87c4b` (vendored scripts) on the coordinator's word; nothing under `plugin/` changed after the version commit.

## 5. Forbidden reads

No transcript, no live state root, no file under `~/.claude`.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
