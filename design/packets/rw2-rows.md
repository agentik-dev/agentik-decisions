# Packet rw2-rows: `rows` and `rows check`, each row's stage read from its records and from git

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-13, brief rw2 |
| pin | main at `39acf99` (0.21.14). Version 0.21.15. Worktree `.claude/worktrees/rw2-rows`, branch `rw2-rows` |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test reads live state |
| may touch | `plugin/lib/decisions/rows.py` (new), `plugin/lib/decisions/cli.py`; `tests/test_rw2_rows.py` (new), `tests/test_cli.py`; `NICE_TO_HAVE.md`; the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_rw2_rows tests.test_cli` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words: none; hq design/16 §4 items 5 and 6. Cited: hq entries 6 (a 3.9 floor, stdlib alone), 9 and 37. The baseline at `39acf99`: §3.

## 2. Rulings

- R1, the verb. `agentik-decisions rows [check] [--json] [--root DIR] [REPO...]` in a new module, `plugin/lib/decisions/rows.py`. `check` is a word, not a flag: the first positional, when it is exactly that. In `cli.py`: its paragraph and parser directly before `install-cli`'s, `"rows"` before `"install-cli"` in `VERBS`, a branch in `main` before `locate`; `tests/test_cli.py` follows. Not touched: `__init__.py`, `backlog.py` (another row's), `common.py` but its version.
- R2, the root. DIR holds one folder a row; the default is `history/rows` under the working directory's git top. DIR's git top is the home. No DIR: exit 2. A row is a folder holding `row.md`. Nothing is written or fetched: git is read through `backlog.Git`, and `status` runs with `--no-optional-locks`.
- R3, the records. Each opens with a title and one table, `| item | value |`. A cell is read with its backticks dropped, by its opening words; the rest is prose.
  - `row.md`: `repo`, `level`, `from`, `base`, `depends_on` (row names, or `none`), `done`, and optionally `branch` (else the folder's name). Each `- [ ]` under `## Owed` is one owed.
  - `build-<n>.md`: `stage` (`first build`, `fix of review <k>`, `phase 2`, `cut`), `head` (a sha), `gate` (`<id> exit <code>`, `<id> running`, `none: <why>`).
  - `review-<n>.md`: `slice` (`<base>..<head>`), `blocks`, `ruling` (empty, or opening `closed` or `fix`). `merge.txt`: by its existence.
  - `done`: empty is open; opening `withdrawn` is given up, and the folder is skipped everywhere; else closed, and `<date> <sha>` when those are its first two words.
- R4, the repo. A cell `hq`, or the home's short name, is the home. Else the REPO named whose short name is the cell; with none named, the folder beside the home called `agentik-<cell>` or `<cell>`. A row whose repo is absent, no checkout or without `main` goes to `skipped` (`{"repo", "why", "rows"}`).
- R5, the words. A landing is what `building_red` finds for the branch. A review covers a build whose head is its slice's end or an ancestor of it. R is the newest review covering the newest build. First match; a next act is text unless marked a command:

| word | when | next |
|---|---|---|
| `pushed` | a landing that the local `origin/main` holds | the open Owed count; with none, the done cell to type, `<date> <sha7>` |
| `landed` | a landing | `push <repo>'s main` |
| `waits` | no branch, no build, a `depends_on` row not landed | those rows |
| `briefed` | no branch, no build | `brief.md`'s path |
| `building` | no build | command `agentik session gate status` |
| `to rule` | R's ruling is empty | R's path |
| `to fix` | it opens `fix` | the branch and R's `blocks` |
| `ready` | it opens `closed`, the merge base is main's head, `merge.txt` is there | command `agentik session gate land <repo's path> <branch> <tip> <merge.txt's path>` |
| `reviewed` | it opens `closed` | `phase 2: merge main into <branch>` when the base is behind, else `merge.txt`'s path |
| `built` | no R | `review <k>: <last reviewed head, else the merge base>..<head>` |

  With no R and a newest build of stage `phase 2`, the word is judged on the newest build of another stage when that gives `reviewed` or `ready`. A `depends_on` row has landed when its `done` is closed or its word is `landed` or `pushed`; a name with no folder is not waited on. `past` counts the commits beyond the newest recorded head (the merge base with no build) and changes no word.
- R6, `--json`: `{"schema": "agentik.rows/1", "ok": true, "root", "home", "rows", "skipped"}`, the open rows by name. A row: `row`, `repo`, `level`, `from`, `depends_on`, `waits`, `state`, `stale`, `branch`, `worktree` (its path or null), `tip`, `dirty` (the worktree's count, or null), `past`, `record` (the file the word came from), `head`, `gate` (`{"id", "exit"}`, `exit` null while running; null for `none:`), `ruling` (the newest review's word or null), `owed`, `next` (`{"text", "command"}`, the command null when there is none). A `Refusal` prints `{"schema", "ok": false, "error": {"code", "message", "remedy"}}` on stdout, exit 2.
- R7, the contradictions, strings in `stale`:
  - `head <sha> of build-<n>.md is not on <branch>`: no commit, or no ancestor of the tip (of the landing's second parent when the branch is gone). `slice end <sha> of review-<n>.md is not on <branch>`: the same.
  - `level <L> differs from <from>'s <M>`: `from` opens `HANDOFF <n>` and that row of the home's build order holds another level (read here over `backlog.gathered`); or it opens `<repo> n<k>[, n<j>]` and the most urgent level of those ids still in that repo's `NICE_TO_HAVE.md` is another. Else no check.
  - `branch <branch> is gone and no merge names it`: a build, no branch, no landing.
  - A closed row, in `check` only: `done <sha> is not on main's first-parent line` (`done_red`; a plain commit passes in the home alone).
- R8, the exits and text. `rows` exits 0 with contradictions shown. A line a row: `<row>  <level> <repo>  <word>  tip <sha7> +<past>  dirty <n>  gate <id> exit <code>  next: <command or text>`, a part with nothing to say left out; under it `  stale: <what>`; then `skipped (<why>): <repo>: <rows>`; `no open rows under <root>` when none. `rows check` walks open and closed rows and prints `<row>  stale: <what>`, the skipped lines and `checked <n> rows under <root>: <m> stale`; exit 1 when m is above 0. An unfinished row is never a red. Its `--json` adds `checked` and a top-level `stale` (`[{"row", "what"}]`).
- R9, the records: `--help`, lines within 100 characters. No command page. No README row: its source is 4 B under its cap.

## 3. Interfaces: the acceptance list

Cases in `tests/test_rw2_rows.py` on `Orchard`, made-up rows; each red at the pin: `invalid choice: 'rows'`, exit 2.

1. One row through every word, `--json` at each step: `briefed`; `waits` behind an open `p0-cart`; `building`; `built` (the act names review 1 and its slice); `to rule`; `to fix`; `built` at `build-2.md`; `reviewed` (the act `merge.txt`, and phase 2 once main moves); still `reviewed` at a `phase 2` build with main merged in; `ready` at `merge.txt` (the command holds the tip and the file); `landed` at a `--no-ff` merge `Merge <branch>: ...`; `pushed` once `refs/remotes/origin/main` is main.
2. Cells as hands write them (a head in backticks with prose after it, a gate with a note, a `branch` cell) give the same words; `gate` reads `{"id", "exit": 0}`, null `exit` for `running`, null for `none:`. Two commits past the head and one dirty path: `past` 2, `dirty` 1.
3. Each contradiction of R7, one at a time: `rows check` exits 1 with its line; mended, `0 stale` and exit 0. The rows of line 1 are never red.
4. A row of an absent repo and one of a folder that is no checkout: in `skipped`, named, both forms exit 0. A REPO named: another repo's row is skipped.
5. A `withdrawn` folder with no branch is in no list. A closed folder is checked and not listed; `done | landed, pushed` is no red.
6. A row holds exactly R6's keys. The text view prints R8's lines. No root: exit 2, and R6's error under `--json`. `--help` lists `rows`.
7. A read leaves the home and `pear`, `.git` included, byte for byte as they were.

## 4. Findings that name this row: ledger, NICE, forks

Not built: `rows close`, a cut builder's charter read, `covers`, `agentik rows`, the gate's files, any write. No fork. Version `0.21.15`, last under `plugin/`, where `acf8870` put it.

Review 1, ruled fix, mended here: F1 words and options in any order (`parse_known_args`; other verbs as before); F2 the land command `shlex.quote`d; F3 each text line through speak's escape and control filters; F4 a stage by its opening words; F5 a cell is its row's second cell; L1 an unreadable record skips its row. L3 to L11: NICE n89 to n93.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no real row folder in a test.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
