# Packet d42: a block with no base line is the owner's, line by line

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-12, brief d42 (hq `history/sessions/BRIEF-2026-11-12-decisions-d42-no-base.md`), NICE n83 S2, n84, n82 |
| pin | main at `00449d5` (0.21.12). Version 0.21.13. Worktree `.claude/worktrees/d42-no-base`, branch `d42-no-base`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state |
| may touch | `plugin/lib/decisions/questions.py`, `answer.py`, `selector.py`; `plugin/skills/{ask,decisions}/SKILL.md`, `plugin/commands/answer.md`; `tests/test_d42_no_base.py` (new), `tests/test_answer_head.py`, `tests/test_d41_base.py` (lines 8 and its stamp case, and line 5's patch of `head_block`), any test whose fixture answers or asks a block with no base line; `NICE_TO_HAVE.md` (n82, n83, n84 leave); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib python -m unittest tests.test_d42_no_base` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words. Entry 39 of the hq's ledger: "`answer` and `ask` treat a line whose digest the base lacks as the owner's and never drop it". No base lacks every digest. Entry 9: six verbs, so no verb and no flag gives a block a base.

The fault, measured at `00449d5` with the designer's probes in a temp root and a temp home: a block with no base line (written before d41, its base line deleted, or damaged by one character so it no longer has `BASE`'s shape) is read against git's HEAD, and a commit by path makes the owner's typed words HEAD's. Deleted and committed: `--pick Pin` exits 0, the words in neither file; `--other X` writes `Other: X` alone. Damaged, committed, `ask`: `ask` stamps a base that holds the typed line's digest, and `--other` keeps the damaged line, not the words. `ask` with a stub render rewrites a base-less block over the words, HEAD holding it or not. A second base-shaped line typed bare: `--pick` exits 0 and the line is in neither file; fenced, `--other`'s Answered line holds the two fence lines alone. A recording `git`: `ask` calls it twice and `answer` once for a block with none.

## 2. Rulings

- R1 one rule: a line of a block is the tool's only when the block's base line holds its digest; nothing else is evidence.
- R2 the base (`questions.py`): a block has a base only when exactly one line above its answer line has `BASE`'s exact shape, and that line alone leaves `Block.text`. With none or two or more, `Block.base` is None and each such line stays in `Block.text` as any line does.
- R3 no base (`answer.since`): every non-blank line above the answer line is the owner's. `head_block`, its git children and the three HEAD messages go; `answer` and `ask` run no git.
- R4 `answer`: `--pick` is refused after an unknown `--pick` and before the stray-lines refusal, listing no lines (the brief's text). `--other X` writes `Other: X; the owner's line: W`, W the stray lines, then the rest, each once, then T, untrimmed, the heading included.
- R5 `ask` (`selector.py`): such a block is not rendered, written back, stamped or in the JSON; one warning after the answered and the lint skips (the brief's text). `ask` stamps only a block it asks; d41's R6 exception goes.
- R6 the lint is unchanged. R7 the texts drop git and HEAD; the way out is `answer N --other`, then `new`. A damaged base line is a line like any other.

## 3. Interfaces: the acceptance table

| # | line | at the pin |
|---|---|---|
| 1 | one hex digit cut, committed, `ask`, `--other X`: warning, file byte for byte; the words kept | red: stamped over, the damaged line kept, the words lost |
| 2 | base line deleted, committed: `--pick` exit 2, R4's text, files unchanged; `--other` keeps the words | red: exit 0, words in neither file; `Other: X` alone |
| 3 | never based, typed, committed: `--pick` 2; `--other` keeps; `ask` with a stub: R5's warning, file unchanged, input without it, JSON `[]` | red: `--pick` 0; reworded and stamped |
| 4 | line 3 with no git repository and with `git` off `PATH`: the same | red: exit 2 "git holds no copy"; `ask` rewrites |
| 5 | a second base-shaped line under a label, bare and fenced: `--pick` 2; `--other` keeps it; lint 1 | red: `--pick` 0; fenced, the fence lines alone |
| 6 | a clean block with no base that HEAD holds: `ask` warns, not in JSON, file unchanged | red: asked and stamped |
| 7 | a recording `git` first on `PATH`: `answer` and `ask` call it never | red: 2 calls and 1 |
| 8 | `test_d41_base`'s lines 1 to 7 and 9 pass; every other test green; changed fixtures listed | |
| 9 | `make check` green through the queue, once, last | |

## 4. Findings that name this row: ledger, NICE, forks

n82, n83 and n84 leave `NICE_TO_HAVE.md`. The owner's fork, filed as hq question 42 and built as recommended: a block with no base line is no longer asked, and `--other` copies its lines whole. Entry 39's amended sentence is the coordinator's.

## 5. Forbidden reads

No transcript, no live state root, no file under `~/.claude`.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
