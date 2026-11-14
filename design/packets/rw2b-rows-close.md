# Packet rw2b-rows-close: `rows close`, and what a cut builder's charter left

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-14, brief rw2b |
| pin | main at `1ace01a` (0.23.0), the merge of dc3-claude-md-audit, after dc1-init. Version 0.23.1, alone as the last commit under `plugin/`. Worktree `.claude/worktrees/rw2b-rows-close`, branch `rw2b-rows-close`, nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test reads live state or writes under the real home |
| may touch | `plugin/lib/decisions/rows.py`, `plugin/lib/decisions/cli.py` (the docstring's `rows` lines, its exit list, the `rows` parser); `tests/test_rw2b_close.py` (new), `tests/test_rw2_rows.py` (the key count, 19 to 20); the version places; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_rw2b_close tests.test_rw2_rows` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

hq design/16 §4 items 6 and 7, the two parts cut from rw2. Cited: hq entries 6 (a 3.9 floor, stdlib alone), 9 and 37. A landed and pushed row reads `pushed  next: type done: <date> <sha7>`, and a hand types the cell. This row adds the one writer, `rows close`, and gives the read what a cut builder's charter left. Every other row's lines keep their bytes.

Measured at `1ace01a`, from this worktree, a temp HOME, in the hq's checkout, read only: `rows close rw2-rows` reads both words as REPOs (seven `skipped (not named)` lines, `no open rows under <root>`, exit 0); `--dry-run` is `unrecognized arguments`, exit 2; `rows --json` holds 52 open rows of 19 keys, three `building` (one 8 commits past its record), nothing of a charter. `design/readme/source.md` is 24,574 B of a 24,576 B cap: no README line. The suite: 821 cases.

## 2. Rulings

- R1, the form. `rows close ROW [--withdrawn WHY] [--root DIR] [--repo DIR] [--dry-run] [-y|--yes]`; `close` is the first word as `check` is, words and options in any order. Refusals, exit 2, nothing written: `rows close: name one row`; `rows close: one row a call`; `rows close takes no --json`; `rows: --withdrawn, --repo, --dry-run and -y go with close`; `rows close: --withdrawn takes one line of words with no | in it` (WHY empty, of several lines, or holding a pipe).
- R2, the row. `<DIR>/<ROW>/row.md`, DIR as the read finds it. `rows close: no row <ROW> under <DIR>`, or `no such row under <DIR>` for a ROW that does not match `NAME`. No `done` row in the first table: `rows close: <path> has no done cell; nothing written`. A `done` cell closed or withdrawn: stdout `rows close: <ROW> is closed already: <the cell, 80 characters at most>`, exit 0.
- R3, the repo. `--repo DIR` is the row's checkout whatever its name; else `Repos.where` on the cell. `rows close: <ROW>'s repo is not found (<why>); name its checkout with --repo DIR`; `rows close: --repo <DIR> is no checkout with a main`. `--withdrawn` reads no repo and no git.
- R4, when it closes: the row's word, by the read's own functions, is `pushed`, and nothing is open under `## Owed`. Else `rows close: <ROW> is <word>, not pushed; nothing written` or `rows close: <ROW> has <n> open under ## Owed; nothing written`. A contradiction (`stale_of`) blocks nothing: one stderr line each, `rows close <ROW>: stale: <what>`.
- R5, what it writes. The cell is `<date> <sha7>` of the landing merge. In `row.md` the first table's `done` row becomes `| done | <cell> |`; every other byte stays. The done file is `backlog.DONE_FILE` under the home; its line `<ROW>: <title>, done <cell>` (title: the first line less `# Row <ROW>: `; another shape gives `<ROW>, done <cell>`), `- ` first when the file's last line that is not blank opens so, as `moved` does. An absent file is made; a file holding a word that opens with the sha7 gets no line. One `commit_texts` call: both or neither. No `git add`, no commit.
- R6, `--withdrawn WHY`: the cell `withdrawn <ask.today()>: <WHY>`, on any open row whatever its word and `## Owed`; `row.md` alone.
- R7, the lines. Stdout first: `rows close <ROW>: <row.md>: done <cell>`; `rows close <ROW>: <done file>: <line>` or `...: holds <sha7> already, no line`. Then `--dry-run` (it wins over `-y`): `rows close: dry run, nothing written`, exit 0; `-y`: the write, `rows close: <ROW> closed` or `withdrawn`, exit 0; neither, stdin and stderr terminals: on stderr `Write this? y for yes, n or Enter for no. `, `y` or `yes` in any case writes, anything else, an end of file or an interrupt `rows close: declined, nothing written`, exit 2; neither, no terminal: `rows close: nothing written, since it cannot ask here; run it again with -y`, exit 2. Every line through `clean`; the question behind `asked(stdin_tty, stderr_tty, reader, err)`.
- R8, the cut builder. An open row that is `building`, or `to fix` with `past` above 0, holds an object under a twentieth key, `cut`, after `next`; every other row `cut: null`. `charter`: the newest by date, then by `<n>` as a number, of the `<date>-<n>.md` or `<date>-<n>-<chain>.md` files `git diff --name-only --diff-filter=AM <merge base> <tip> -- history/sittings/` lists, read from the tip with `git show`, or null. `unchecked`: its `- [ ]` lines under `## Done-ness`, null with no charter. `next_act`: the first line not blank under `## Next act`, 100 characters at most, or null. `commits`: `{sha, subject}` past the newest recorded head (the merge base with none), newest first, 50 at most. `paths`: the worktree's changed and untracked paths, 50 at most. Text under the row's line and its `stale:` lines: `  charter <path>: <n> unchecked; next act: <line or none>` or `  charter: none on <branch>`; `  past: <sha7> <subject>` for three, then `  past: and <k> more`; `  dirty: <p>, <p>, <p>` with ` and <k> more`.
- R9, the words. `cli.py`'s docstring gains the `rows close` form, says the read and `check` write nothing, and its exit list names the close under 2; the parser's help the same. No command page, no README row. `tests/test_rw2_rows.py`: the key count 19 to 20, its one edit.

Where the design and the code differ (the row's paragraph): the text shows three of each and a count, `--json` the rest; a row with a contradiction closes and prints it; with neither `-y` nor `--dry-run` and no terminal, nothing is written, exit 2.

## 3. Interfaces: the acceptance list

The home `depot` with `history/rows/`, the repo `agentik-crate` beside it, rows `p1-crate` and the like, on `test_rw2_rows.Rows`. All in `tests/test_rw2b_close.py`; at the pin each is red (`close` read as a REPO, or `unrecognized arguments`, exit 2), line 10 green.

1. `rows close p1-crate -y` on a pushed row owing nothing: R7's two lines and `closed`, exit 0; the cell and the line as R5; `rows` no longer lists it.
2. `--dry-run`, and `--dry-run -y`: R7's lines, exit 0, both files' bytes kept.
3. Each refusal of R1 to R4 by its words, exit 2, bytes kept.
4. The done file absent, ending in a bullet, holding the sha7; a first line of another shape.
5. `--withdrawn "superseded by p9" -y` on a `building` row with two owed: the cell, no line; the read skips it, `rows check` reds nothing; a WHY with a pipe, or empty, refused.
6. Neither flag: no terminal, exit 2; the question answered `y`, `YES`, an empty line, an end of file.
7. `commit_texts` failing on the done file: `row.md` keeps its bytes.
8. Closed and withdrawn rows: `is closed already`, exit 0; a contradiction closes and prints its `stale:` line.
9. A `building` row whose branch added charters `-9` and `-14`, five commits, four loose paths: R8's keys and lines; a charter merged in from main not read; no charter; `built` and `to fix` at `past` 0 hold null; `to fix` one past holds the object.
10. `tests/test_rw2_rows.py` with its one edit; `rows` and `rows check` text for every other word byte-equal to the pin's.
11. The suite and `make check`, once, last, green; 0.23.1 the last commit under `plugin/`.

## 4. Findings that name this row: ledger, NICE, forks

Left: `backlog --check --write` adding a done line where the file holds the sha (a NICE row); a README row. `backlog.py` is imported from, unchanged. No fork.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real row folder in a test.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
