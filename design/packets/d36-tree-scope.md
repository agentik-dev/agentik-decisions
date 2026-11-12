# Packet d36: a tree's rules rendered into the folder's file, and the ceilings in bytes

| item | value |
|---|---|
| from | hq design/09 §1 (what Claude Code loads), §3 (the mechanism, the folder's file, how it is checked), §4 (the ten titles), §5.2 (the folder's file), §7.2 "The checks", §8 (hq entry 9), §9 step 1 and "A ceiling starts as a warning". No entry is carried: this repo keeps no DECISIONS.md (`CLAUDE.md`, Authority); hq 9 binds the ledger's shape and `render`, cited by number. The first of two packets: `answer --preview`, `audit --edits` and the `instruct` skill are the second's |
| pin | main 497abb7 (0.19.2); the bump is 0.20.0, a packet's minor for a new flag; worktree `.claude/worktrees/d36-tree-scope`, branch `d36-tree-scope`; nothing linked from main (the pyenv virtualenv `.python-version` names is found from any checkout) |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install`, `install-cli`, bare `make` or `make readme`; never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state; no test reads a live ledger or writes above its temp folder; `render --scope tree` is never run against a real ledger without `--into` a temp file |
| may touch | `plugin/lib/decisions/{ledger,render,answer,audit,cli,common}.py` (`common`: `VERSION` only), a new `plugin/lib/decisions/tree.py`; `tests/test_tree_scope.py` (new), `tests/test_{render,ledger,lookup,audit,plugin}.py`; `plugin/commands/{render,answer}.md`; `plugin/skills/decisions/SKILL.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `CLAUDE.md`; `NICE_TO_HAVE.md`; `.hygiene-allow`; this packet |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib /usr/bin/python3 -m unittest -v tests.test_tree_scope 2>&1 \| grep -c ' \.\.\. ok$'` reads 28 (497abb7 with this file: 3), and under 3.12.7; `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 and the source is at most 24,576 B (24,561 B at the pin) |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id> --strict` in one background Bash, last |
| budget | a commit per group by explicit path, this packet first, then the tests, then the change; `claude-opus-5-5` |

## 1. What the source says

The owner's words (2026-11-11): "A focus should be on avoiding Claude.md bloat and making sure that the rulings/guidelines/claude configs get updated the correct way through a lane, not ad hoc. This is what we designed in the last session but I want to make it a reality now that we've done the folder moves."

At the pin:

- `ledger.parse` takes any `###` under `## In force` as an area, so `### Every session of the tree` already lints, unless it comes before `### Every session` ("comes first"). It fails a ledger on an eighth `Every session` entry (`EVERY_SESSION_CAP = 7`).
- `render.block` lists the `Every session` entries in ledger order and every other entry in force as `- N Title (area)`; a tree section would land in that list.
- `render` writes the block into any target whose markers are one BEGIN before one END, whatever ledger its `Generated from` line names; `--lint` prints the block's bytes, `--check` prints only a diff.
- `answer --area` resolves `Every session` by its whole name only (`whole=`); `--amends M` amends in place and cannot name a section.
- `audit` prints `N of 7 under Every session`, and every Every session entry with its block bytes (d34).
- The two §5.2 examples measure 1,217 B and 1,838 B loaded once each whole-line HTML comment is dropped, as the design gives them.

## 2. Rulings

1. **The section.** A ledger may hold `### Every session of the tree` under `## In force`, before or after `### Every session` (which still comes before every other area). Its entries are in force for `show`, `find`, `ask`, `answer` and `audit`; `audit` lists them with their bytes in the folder's file, labelled as the tree's. `answer --area` reaches it by its whole name only, as `Every session`. Today's means cannot move an entry, so `answer` gains `--move-to A`, valid only with `--amends M`: the amended entry goes last under A, resolved as `--area` is. An answer that touches the tree's section and grows the folder's file is refused like the block's growth, and `--every-turn` lets it through; `answer` never writes the folder's file, and says on stderr which command does.
2. **`render --scope tree`.** The tree's section alone, every entry in full (its tail cut as the block cuts one), into the `CLAUDE.md` of the folder that holds the main checkout of the ledger's repo (`git rev-parse --git-common-dir` from a worktree), or into `--into`. The file is §5.2's first example: the comment naming the folder's file, the title `# The <folder> tree`, the block naming `<checkout>/<ledger>` and the ledger's path under `~`. Its text never depends on `--into`. `--check` exits 1 when the file is absent or differs. A ledger without the section exits 2, the tool's refusal code.
3. **The plain render** leaves the tree's entries out, bodies and titles both. As built, ruling 5's order narrows the brief's "byte for byte as today". A ledger without the section renders as at the pin when its `Every session` titles are outside the ten or in their order.
4. **Never over another's file.** Both scopes refuse, exit 2, a target whose block names another ledger (the `Generated from` path, or a tree file's `Each is an entry of` path, compared as the main checkout holds each). `--scope tree` also refuses a target that exists and is not a tree file this ledger wrote. Each refusal names both ledgers or the file.
5. **Order and titles.** Both blocks list their entries in the order of the ten titles (`ledger.TITLES`), case and runs of spaces aside; any other title keeps its place after them in ledger order. `--lint` warns on stderr, its exit unchanged, on such a title, then once on the ten, and on each hand-written line outside the block, an HTML comment and a code fence that holds `never`, `always`, `must` or `only` as a whole word, any case.
6. **The ceilings.** No count caps `Every session`. `--lint` and `--check` print `render: FILE loads N B, comments aside and imports included; the ceiling for KIND is C B[; over by D B]`, of the file as render would leave it: a comment that opens a line goes whole, and each `@path` outside a code fence or span that names a file adds that file's loaded bytes, to a depth of four, each file once. KIND is the Mac's global file (a `CLAUDE.md` directly in the home folder's `.claude`), a tree's file (`--scope tree`), an hq's file (a ledger with the tree's section) or a repo's file; the figures are `tree.CEILINGS` alone. `--ceiling`, with `--check` or `--lint` only, makes the excess exit 1.
7. **Records.** README and source alike by hand (24,561 B to 24,497 B, cap 24,576), the skill, the two commands, CLAUDE.md's lint sentence; NICE n16 (the cap of 7) leaves. 0.20.0 in the four version places and `test_plugin.py`.

## 3. Interfaces: the tests

`tests/test_tree_scope.py`, 28 cases, every file under the case's temp home (`<home>/work/orchard/orchard-hq`). At 497abb7 3 ok (the section lints, `show` and `find` read it, the sample's block byte for byte) and 25 red, under 3.9.6 and 3.12.7.

| class | holds |
|---|---|
| `Section` | ruling 1: the lint, either order, `show`, `find`, `audit --json` and its text |
| `ScopeTree` | ruling 2: §5.2's form byte for byte, `--check` fresh, absent and edited fail, `--into`, a worktree's folder, no section refused |
| `PlainRender` | ruling 3: the tree left out; the sample as at the pin |
| `Refusals` | ruling 4: a block from another ledger, plain and tree; a hand-written file |
| `Order`, `Warnings` | ruling 5 |
| `Ceilings` | ruling 6: eight entries lint, the four kinds under and over, with and without `--ceiling`, an import counted and a comment not, `--ceiling` alone refused |
| `Answers` | ruling 1: `--area` by the whole name, a prefix never, `--amends --move-to`, `--move-to` alone refused |

Tests that change: `test_render.py` reads the loaded-bytes line out of `--check` and `--lint` and the warnings out of stderr where it pinned them silent; `test_lookup.py` the same; `test_ledger.py` lints eight entries clean; `test_audit.py` takes the new keys `tree_session`, `tree_session_entries` and a row's `tree` (`every_session_cap` stays, `null`).

## 4. Findings that name this row

NICE n16 (the cap of 7 refuses late) leaves: the cap is gone. New rows: n47, the folder's file stale after an answer until `render --scope tree` (S4); n48, a comment that opens mid-line is counted (S4); n49, `--move-to` keeps the title (S4).

## 5. Forbidden reads

Other repos but hq design/09's sections named in `from`; a real ledger, OPEN-QUESTIONS.md or CLAUDE.md from a test; any folder's `CLAUDE.md` outside a temp root; the relay's state; transcripts.

## 6. Report

Each commit; the acceptance readings at the pin and now; the gate's id and line; the README's bytes; the NICE rows; each choice; the new sentence hq entry 9 needs.
