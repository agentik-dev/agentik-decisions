# Packet su5: `backlog --json` gives each step its level and its state cell

| item | value |
|---|---|
| from | the management sitting's coordinator, 2026-11-13, brief su5; hq design/18 row su5 (§3.3 item 11, §6). Level S3 |
| pin | main at `39acf99` (0.21.14). Version 0.21.15. Worktree `.claude/worktrees/su5-backlog-fields`, branch `su5-backlog-fields`; nothing linked from main |
| wall | this worktree; no push, `--amend`, rebase, merge or install; no bare `make` (the gate queue only); no test reads live state, a real HANDOFF or a real repo |
| may touch | `plugin/lib/decisions/backlog.py` (`build_order`, `as_json`, the head comment; one call in `cmd_backlog`, see §4); `tests/test_su5_backlog_fields.py` (new); `tests/test_backlog.py` (one assertion, see §4); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | the table in §3; `PYTHONPATH=plugin/lib:. python -m unittest tests.test_su5_backlog_fields` |
| budget | about 90 tool calls |

## 1. What the source says

The owner's words: none bind this row. hq design/18 row su5: a build order row whose state cell reads `waiting: the owner` is counted by `agentik status` and listed by the inbox, and both read it from `backlog --json`. At the pin a step of `backlog --order FILE pear --json` holds exactly `n`, `line`, `title`, `done`, `repo`, and without `--order` or from a `N. ` list exactly `n`, `line`, `title`, `done`: neither the level nor the cell.

The ledger: this repo keeps none; the suite's management ledger binds it, cited not copied: entry 6 (`/usr/bin/python3` at a 3.9 floor, the standard library alone), entry 9 (six verbs, the views beside them), entry 37 (a public repo: made-up names). GUIDE §9's table: `| # | item | level | repo | where | state |`, the state opening `open`, `building <row>`, `waiting: <on what>`, `watch: <the sighting>` or `done <date> <sha>`.

## 2. Rulings

- R1, where: `build_order` and `as_json`; `--check`, `--write`, `expire` and every text view print what they print at the pin.
- R2, `level`: the row's cell under the header's `level` column when it is `S1` to `S4`, else `null`; no `level` column, another shape and a `N. ` list step give `null`.
- R3, `state`: `null` for a `N. ` list step, else `{cell, word, rest, on, n, text}`. `cell` is the cell as `build_order` reads it (`--check --json`'s `cell`); `word` its first word less one trailing `:`, `null` for an empty cell; `rest` what follows that word, stripped; `on` (for `waiting` only) what `reference` reads: `"the owner"`, `"owner"`, `"row"`, `"branch"` or `null`; `n` the number of `waiting: owner <n>` or `row <n>`; `text` the words after `the owner:` for that form, else after the cell's first `;`, stripped.
- R4, the names `reference` takes: the table's repo cells and the short name of each REPO named, a checkout or not. No `git` call is added.
- R5: both keys in every step, with `--order FILE` and without; `repo` stays only under `--order`.
- R6: the object stays `{"repos": [...], "skipped": [...]}`; no `schema` or `ok`.
- R7: the module's head comment names the two keys; `cli.py`, the command page, the skills and the README's verb table stay as they are (the README source sits at 24,572 B of its 24,576 B cap).

## 3. Interfaces: the acceptance table (each a case in `tests/test_su5_backlog_fields.py`)

The table's four rows: `3 | S2 | pear | waiting: the owner: opens the gate; then the cart`, `4 | S3 | pear | waiting: owner 9; after row 3`, `5 | S4 | pear | building p1-crate`, `6 | soon | pear | open`.

| # | line | at the pin |
|---|---|---|
| 1 | `--order FILE pear --json`: step 3 `level` `S2`, `state` whole as R3; step 4 `on` `owner`, `n` 9, `text` `after row 3`; step 5 `word` `building`, `rest` `p1-crate`; step 6 `level` null, `word` `open` | red: the step's keys are `n, line, title, done, repo` |
| 2 | `waiting: row 4` on `row` n 4; `waiting: pear p1-crate` on `branch`; `waiting: plum p1`, `plum` not named, on null and named (no checkout) on `branch`; `watch:`, `done`, an empty cell | red: no `state` |
| 3 | `backlog pear --json` from pear's own HANDOFF.md: `level`, `state`, no `repo` | red: `n, line, title, done` |
| 4 | the `numbered` fixture: `level` and `state` null; a table with no `level` column: `level` null, the state read | red: no key |
| 5 | held: the text view's seven lines; `--check --json`'s keys; line 1 leaves the temp home as it was | green |
| 6 | held: `tests/test_backlog.py` (but §4), `test_d39_backlog_check`, `test_d43_backlog_built_on`, `test_expire` | green |
| 7 | `make check` green through the queue, once, last | |

## 4. Where the brief and the code part

- `tests/test_backlog.py`'s `test_json_fields` holds a `N. ` list step to exactly `{n, line, title, done}`, which R3, R5 and line 4 change; its one assertion gains `level` and `state`. The brief's held line says that file passes with no edit: the rulings win.
- R4's names need the REPOs named, which only `cmd_backlog` knows: `as_json` takes them as an argument and `cmd_backlog`'s `--json` call passes them, its one changed line.

No fork for the owner.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real HANDOFF.

## 6. Report

The hand-back to the hq's coordinator.
