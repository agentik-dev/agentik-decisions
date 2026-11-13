# Packet in1: `questions [REPO...] [--json]`, each repo's open questions as one read

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-13, brief in1 (hq design/17's row in1: §3 items 2 and 4, §6, §8) |
| pin | main at `39acf99` (0.21.14). Version 0.21.15. Worktree `.claude/worktrees/in1-questions`, branch `in1-questions`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state, a real ledger or a real repo |
| may touch | `plugin/lib/decisions/questions_read.py` (new), `plugin/lib/decisions/cli.py`; `tests/test_in1_questions.py` (new), `tests/test_cli.py` (`VERBS`); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib:. python -m unittest tests.test_in1_questions tests.test_cli` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words: none bind this row. hq design/17's inbox joins reads the tools give, and the questions file's grammar is this tool's, so this tool prints it. The inbox shows a question as one line and opens it to its block as written; it never rewords it.

The ledger, cited: hq entry 6 (`/usr/bin/python3` at a 3.9 floor, the standard library alone); entry 9 (six verbs; `questions` stands beside them as `backlog` does, never among them); entry 39 (a block's base line); entry 37 (made-up names). At the pin no verb reads OPEN-QUESTIONS.md for a caller: `questions`, with or without a REPO or `--json`, prints argparse's `invalid choice: 'questions'` on stderr, nothing on stdout, exit 2.

## 2. Rulings

- R1, the verb: `questions_read.cmd_questions`; in `cli.py` its docstring paragraph and parser after `backlog`'s, `"questions"` after `"backlog"` in `VERBS`, a branch in `main` before `locate`. It reads no ledger path and ignores `--ledger`. `__init__.py`, `common.py` (but its version) and `questions.py` are not touched.
- R2, never: no lock (it prints the same while `.new.lock` is held), no render, no model, no `git` but `git_top` for the default REPO, no write.
- R3, REPO: a directory; the default is the git top of the working directory, else the working directory. Its file is `REPO/OPEN-QUESTIONS.md`. A REPO that is no directory, holds no such file, or whose file is not UTF-8 goes to `skipped` (`not a directory`, `no OPEN-QUESTIONS.md`, `unreadable`) and the read goes on.
- R4, the exit: 0 whenever the read ran, lint problems and skips included; 2 for a usage error. A `Refusal` under `--json` prints `{"schema": "agentik.questions/1", "ok": false, "error": {"code": "refused", "message": M, "remedy": null}}` on stdout, exit 2.
- R5, `--json`: one object, `{"schema": "agentik.questions/1", "ok": true, "repos": [...], "skipped": [{"repo", "why"}]}`. A repo: `repo`, `file` (real paths), `questions`, `answered` (the `- ` bullets under `## Answered`), `decided` (`{"count", "newest"}`: the bullets under `## Decided without asking` and their greatest date not after today, else `null`), `problems` (`[{"line", "message"}]`).
- R6, a question: `n`, `title`, `line`, `state`, `why`, `proposed`, `recommended`, `options` (`[{"label", "effect", "recommended"}]`), `parts` (`{"stands", "choice", "recommendation"}`), `typed` (`""` when none), `typed_above` (`answer.since` with a base, `[]` without), `base`, `problems` (the block's lint messages, `question N: ` cut), `text` (as written, its base line left out).
- R7, `state` in `selector.skipped`'s order: `answered` (`typed on the answer line`); else `unreadable` (the lint's messages joined by `; `, or `no base line, or more than one`); else `answered` when `typed_above` holds a line (`typed above the answer line`); else `open`, `why` null.
- R8, `proposed`: the first date of the final parenthetical of the question's `## Proposed` line in the `DECISIONS.md` beside the file; `null` for no ledger, no line, no date or a ledger it cannot read.
- R9, the text view: per repo `== <name>  <k> open, <a> answered, <d> decided without asking[, newest <date>]`; a question `<n>  <state>  <title>  recommended: <label>[; proposed <date>][; <why>]`; `problem  OPEN-QUESTIONS.md:<line>  <message>` for a problem naming no block; last, `skipped (<why>): <names>`, one line a reason; a blank line between repos.
- R10, the records: `--help` only. No command page, no README row (the source is 24,572 B of its 24,576 B cap): only the README's two version places change.

## 3. Interfaces: the acceptance table (each a case in `tests/test_in1_questions.py`)

| # | line | at the pin |
|---|---|---|
| 1 | `questions pear --json`, one clean block by `new`: one object; `open`, base true, `recommended` the first label, both options, three parts, `text` with no base line, `proposed` `new`'s date | red: invalid choice, exit 2 |
| 2 | `The barn` typed on the answer line: `answered`, `typed`; a line typed above it: `answered`, `typed_above` | red |
| 3 | one option: `unreadable`, the message in the block's and the repo's `problems`; base line deleted: `unreadable`, base false; one option and typed text: `answered` | red |
| 4 | `answered` and `decided.count` count bullets only; `newest` the greatest of three dates, `2999-01-01` never | red |
| 5 | `pear quince nowhere bare --json`: two repos in order, two skipped with reasons, exit 0 | red |
| 6 | no REPO, from a folder inside `pear`: `repos[0].repo` is its top | red |
| 7 | with `.new.lock` held the same object; every file under the temp home unchanged; a stub `claude` never called | red |
| 8 | the text view of lines 1 to 3 and 5: R9's lines, exit 0 | red |
| 9 | `--help` lists `questions`; `tests/test_cli.py` with `VERBS` holding it after `backlog` | red |
| 10 | `make check` green through the queue, once, last | |

## 4. Findings that name this row: ledger, NICE, forks

None filed. Entry 9's "six verbs" sentences stay. No fork for the owner.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real ledger or questions file.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
