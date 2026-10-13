---
status: current
updated: 2026-10-11
owner: the owner
audience: the owner, agent
---
# Intake: `decisions answer` refuses an answer while the open questions exceed the cap, 2026-10-11

This is an ask from example-ops, not a ruling. claude-code-decisions decides it.

Pin: example-ops main at 39c393f2, sitting `history/sittings/2026-10-11-1-cloudflare.md`; the tool as installed on 2026-10-11 (`src/decisions/answer.py`, `cmd_answer`, and `src/decisions/questions.py`, the `OPEN_CAP` check).

## The ask

Please let `decisions answer N` write when the answer lowers the count of open questions, even while that count still exceeds the cap of five.

## What happened

Two sittings put four questions each the same day, each within the cap. When their branches merged, `OPEN-QUESTIONS.md` held eight open questions. The sitting that held the owner's answers to four of them ran `decisions answer 45 ...`, and the tool refused:

```
answer: the result fails the lint; nothing written:
OPEN-QUESTIONS.md:100: 7 questions open; the cap is 5
```

`cmd_answer` lints the result of the write and refuses on any problem. The cap problem is one the answer cannot cause: an answer always removes one question, so the result has fewer open questions than the input. The refusal left the ledger unable to take the owner's answers until two of them were in, which the tool itself prevented.

The sitting worked around it by setting the other sitting's four questions aside (their blocks in `OPEN-QUESTIONS.md` and their Proposed lines in `DECISIONS.md`, since the lint pairs them), running the four answers, and restoring the four byte for byte. That is four hand edits of the two files the tool exists to guard.

## The recommended answer

In `cmd_answer`, drop a cap problem from the result's lint when the result's count of open questions is lower than the input's, or lint the cap on the input and the shape on the result. `decisions new` keeps refusing a question that would exceed the cap, which is the cap's purpose. A one-line test: eight open questions, `answer 1 ...` writes and the result holds seven.

## Also seen

`--amends N` prints the whole old paragraph under `replaced:`; for entry 9 of example-ops's ledger that is 3.5 KB on every answer. A `--quiet` flag, or printing the first 80 characters and the length, would spare a sitting's context.
