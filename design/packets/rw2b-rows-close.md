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

hq design/16 §4 items 6 and 7, the two parts cut from rw2. Cited: hq entries 6 (a 3.9 floor, stdlib alone), 9 and 37.

A landed and pushed row reads `pushed  next: type done: <date> <sha7>`, and a hand types the cell. This row adds the one writer, `rows close`, and gives the read what a cut builder's charter left. Every other row's lines keep their bytes.

Measured at `1ace01a` (0.23.0), `python -B -m decisions` from this worktree, a temp HOME, in the hq's checkout, read only:
- `rows close rw2-rows`: `close` and `rw2-rows` are read as REPO names; seven `skipped (not named): ...` lines, then `no open rows under <root>`, exit 0, nothing written.
- `rows close rw2-rows --dry-run`: `agentik decisions: error: unrecognized arguments: --dry-run`, exit 2.
- `rows --json`: 52 open rows of 19 keys; three read `building` (one 8 commits past its record), nine `pushed`; nothing of a charter.
- `design/readme/source.md` is 24,574 B under a 24,576 B cap, so the row adds no README line.
- The suite: 821 cases.

## 2. Rulings

- R1, the form. `rows close ROW [--withdrawn WHY] [--root DIR] [--repo DIR] [--dry-run] [-y|--yes]`. `close` is the first word as `check` is, words and options in any order, so `close` no longer names a REPO. Each refusal below is a `Refusal` (the tool prints `decisions: ` before it), exit 2, nothing written:
  - `rows close: name one row`
  - `rows close: one row a call`
  - `rows close takes no --json`
  - `rows: --withdrawn, --repo, --dry-run and -y go with close`
  - `rows close: --withdrawn takes one line of words with no | in it` (WHY empty, of several lines, or holding a pipe)
- R2, the row. `<DIR>/<ROW>/row.md`, DIR as the read finds it. No such file, or a ROW that does not match `NAME`: `rows close: no row <ROW> under <DIR>`, the name left out (`no such row under <DIR>`) when it does not match. No `done` row in the first table: `rows close: <path> has no done cell; nothing written`. A `done` cell that is not empty, closed or withdrawn: stdout `rows close: <ROW> is closed already: <the cell, 80 characters at most>`, exit 0, nothing written.
- R3, the repo. `--repo DIR` is the row's checkout whatever its name; without it, `Repos.where` on the row's cell. `rows close: <ROW>'s repo is not found (<why>); name its checkout with --repo DIR`, or `rows close: --repo <DIR> is no checkout with a main`. `--withdrawn` reads no repo and no git.
- R4, when it closes. The row's word, from the read's own functions, is `pushed`, and nothing is open under `## Owed`. Otherwise, exit 2: `rows close: <ROW> is <word>, not pushed; nothing written`; `rows close: <ROW> has <n> open under ## Owed; nothing written`. A contradiction (`stale_of`) blocks nothing: each is one stderr line, `rows close <ROW>: stale: <what>`.
- R5, what it writes. The cell is `<date> <sha7>`: the landing merge's date and its first seven characters, the words `pushed` prints today after `type done:`. In `row.md` the `done` row of the first table becomes `| done | <date> <sha7> |`; every other byte stays. The done file is `backlog.DONE_FILE` under the home. Its new line is `<ROW>: <title>, done <date> <sha7>`, the title being `row.md`'s first line less `# Row <ROW>: ` (a first line of another shape: `<ROW>, done <date> <sha7>`), with `- ` before it when the file's last line that is not blank opens with `- `, as `moved` does. An absent file is made. No line is added when the file holds a word that opens with that sha7. Both texts go through one `commit_texts` call: both or neither. The verb runs no `git add` and no commit.
- R6, `--withdrawn WHY`. The cell is `withdrawn <today>: <WHY>`, today from `ask.today()`. Any open row, whatever its word and its `## Owed`. `row.md` alone; no done line.
- R7, the lines. On stdout, first what would be written: `rows close <ROW>: <path of row.md>: done <the cell>`; `rows close <ROW>: <path of the done file>: <the line>`, or `rows close <ROW>: <path of the done file>: holds <sha7> already, no line`. Then one of:
  - `--dry-run` (it wins over `-y`): `rows close: dry run, nothing written`, exit 0.
  - `-y`: the write, then `rows close: <ROW> closed` or `rows close: <ROW> withdrawn`, exit 0.
  - neither, stdin and stderr both terminals: on stderr `Write this? y for yes, n or Enter for no. `; `y` or `yes` in any case writes; anything else, an end of file or an interrupt: `rows close: declined, nothing written`, exit 2.
  - neither, no terminal: `rows close: nothing written, since it cannot ask here; run it again with -y`, exit 2.

  Every line goes through `clean`. The question sits behind one function that takes the two `isatty` answers and a reader, so a test holds it with no pty.
- R8, the cut builder (item 7). An open row whose word is `building`, or `to fix` with `past` above 0, gains an object under a twentieth key, `cut`, after `next`; every other row holds `cut: null`. Its keys:
  - `charter`: of the files `git diff --name-only --diff-filter=AM <merge base with main> <tip> -- history/sittings/` lists whose name is `<date>-<n>.md` or `<date>-<n>-<chain>.md`, the newest by date, then by `<n>` as a number (`-14` is after `-9`); its path, or null. It is read from the tip with `git show`, never from the worktree, so a charter that main's merge brought in is not the builder's.
  - `unchecked`: the lines opening `- [ ]` under `## Done-ness`; null with no charter.
  - `next_act`: the first line that is not blank under `## Next act`, 100 characters at most; null with none.
  - `commits`: `{sha, subject}` for each commit past the newest recorded head, or past the merge base with no record; newest first, 50 at most. `past` stays the count.
  - `paths`: the worktree's changed and untracked paths as `dirty_of` reads them, 50 at most. `dirty` stays the count.

  In text, under the row's line and its `stale:` lines: `  charter <path>: <n> unchecked; next act: <line>` (`next act: none` with no such section), or `  charter: none on <branch>`; `  past: <sha7> <subject>` for the newest three, then `  past: and <k> more`; `  dirty: <path>, <path>, <path>` and, past three, ` and <k> more` on the same line. The text holds three of each and a count; `--json` has the rest.
- R9, the words about it. `cli.py`'s docstring gains the `rows close` form, drops `writes nothing` for `rows` (the read and `check` write nothing; `close` writes two files), and its exit list names the close under 2. The parser's help says the same. No command page and no README row. `tests/test_rw2_rows.py`'s count of `KEYS` goes from 19 to 20, its one edit.

Where the design and the code differ, and which gives way (the row's paragraph): item 7's "prints the commits and dirty paths" gives way to three of each and a count; item 6 gives no word on a row with a contradiction, so the close goes through and prints each as a `stale:` line; P6 (design/15) gives a writer `--dry-run` and `-y`, and with neither and no terminal the verb writes nothing and exits 2.

## 3. Interfaces: the acceptance list

The home is `depot`, with `history/rows/`; the repo beside it is `agentik-crate`; rows are `p1-crate` and the like, built on `test_rw2_rows.Rows`. All in `tests/test_rw2b_close.py`, each red at the pin.

| # | line | at the pin (`1ace01a`, measured) |
|---|---|---|
| 1 | `rows close p1-crate -y` on a pushed row that owes nothing: R7's two lines and `rows close: p1-crate closed`, exit 0; the cell and the done line as R5; `rows` no longer lists it | `close` and the row are read as REPOs: `no open rows under <root>`, exit 0, nothing written |
| 2 | the same with `--dry-run`, and with `--dry-run -y`: R7's lines, exit 0, both files' bytes kept | `unrecognized arguments: --dry-run`, exit 2 |
| 3 | each refusal of R1 to R4 by its words, exit 2, both files' bytes kept | no such line |
| 4 | the done file: absent, it is made; ending in a bullet, the line is a bullet; holding the sha7, no line and the cell alone is written; a `row.md` whose first line is not `# Row p1-crate: ...` | nothing written |
| 5 | `rows close p2-crate --withdrawn "superseded by p9" -y` on a `building` row with two owed: the cell, no done line; the read then skips the folder and `rows check` reds nothing for its branch; a WHY with a pipe, and an empty one, refused | `unrecognized arguments`, exit 2 |
| 6 | neither flag: no terminal gives R7's line, exit 2; the question answered `y`, `YES`, an empty line and an end of file | no question |
| 7 | `commit_texts` made to fail on the done file: `row.md` keeps its bytes | no write |
| 8 | a closed row and a withdrawn one: `is closed already`, exit 0, nothing written; a row with a contradiction closes and prints its `stale:` line | no such line |
| 9 | `rows --json` and the text for a `building` row whose branch added charters `-9` and `-14`: R8's keys and lines; a charter merged in from main is not read; no charter; `built`, and `to fix` with `past` 0, hold `cut: null`; `to fix` with one commit past holds the object | 19 keys, no line |
| 10 | `tests/test_rw2_rows.py` passes with its one edit; the text of `rows` and `rows check` for rows of every other word is byte-equal to the pin's | green |
| 11 | the suite; `make check`, once, last, through the gate queue, green; 0.23.1 in the version places, alone as the last commit under `plugin/` | 821 cases, green at 0.23.0 |

## 4. Findings that name this row: ledger, NICE, forks

Left: `backlog --check --write` adding a done line where the file holds the sha (a NICE row, the coordinator's); a README row. `backlog.py` is imported from and not changed. No fork.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real row folder in a test.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
