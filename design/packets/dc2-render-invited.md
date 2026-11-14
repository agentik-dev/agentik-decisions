# Packet dc2-render-invited: `render` rewrites a block that is there, and `init` adds one

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-13, brief dc2 |
| pin | main at `c4ff3f2` (0.22.3), the merge of dc1-init. Version 0.22.4. Worktree `.claude/worktrees/dc2-render-invited`, branch `dc2-render-invited`, nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test runs the real `claude` or writes under the real home |
| may touch | `plugin/lib/decisions/render.py`, `init.py`, `answer.py`, `cli.py` (help lines); `plugin/commands/render.md`, `init.md`; `plugin/skills/decisions/SKILL.md`; `tests/test_dc2_render_invited.py` (new) and each test that took its block from a plain `render` (R7); `README.md` and `design/readme/{source.md,rendered.sha256}` (R6's two places); the version places; `NICE_TO_HAVE.md`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_dc2_render_invited tests.test_dc1_init tests.test_render` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words, asked what `render` should do when a repo's `CLAUDE.md` was written by hand and holds no generated block, option A being "change nothing and print the command that adds one (`agentik decisions init`)": "A but we really should make it clear there are benefits to auditing the CLAUDE.md". The letter is this row; the rest is the next row's.

A packet row by the suite's entry 17: no new verb, flag, file format or ledger entry. Cited: entries 6 (3.9 floor, stdlib), 7 and 8 (a ledger's voice), 37 (made-up names).

Measured at `c4ff3f2` (0.22.3), a temp HOME, a new git repo. L is a ledger of one `Every session` entry. H is a `CLAUDE.md` of hand lines.

- L and H, `render`: `render: wrote CLAUDE.md: 0 B to 236 B, +236 B; the block is loaded on every turn`, then the gate's line, exit 0. H grows by the block and is listed on `.claude/edit-gates`.
- L alone, `render`: the same line; a `CLAUDE.md` is made and gated. `--into NOTES.md` over a hand file: the same (`0 B to 252 B`). `--fold-tails`: `no tail to fold`, then the same append.
- L and H, `init`: `decisions: init: a ledger is already at <path>; nothing written`, exit 2.
- L and H, `answer`: ``answer: CLAUDE.md holds no GENERATED markers; the block is left as it is; `agentik decisions render` writes it``, exit 0.
- L and H, `render --check`: a diff of the append, then `render: CLAUDE.md loads N B, ...`, exit 1.

## 2. Rulings

- R1, the rule. `render` in the repo's scope writes a block only into a target that holds one: one BEGIN before one END, as `tree.markers` reads them. The default target and `--into` alike. A target that is absent, or holds no block (hand text, an empty file, markers only inside a code fence, a link to such a file, a link to nothing), gets nothing: no byte changes, no file is made, no edit-gates list is written, and the run refuses with R2's line, exit 2. A fresh block, a stale one and markers that are not one block behave as at the pin, byte for byte. `--scope tree` is unchanged.
- R2, the line, on stderr through `Refusal`: `render: <target> <state>, and render only rewrites a block that is there; nothing written; <next>`. `<state>` is `is absent` when nothing is at the path (a link to nothing too), else `holds no generated block`. `<next>`, when the target is the `CLAUDE.md` beside the ledger, however it was named: `` `agentik decisions init` adds it ``, with ` --ledger <quoted>` inside the backticks when the run named a ledger, as `locate`'s line writes it. For any other target: ``a file takes the block once it holds the two marker lines, `<!-- BEGIN GENERATED: decisions -->` then `<!-- END GENERATED: decisions -->`, each alone on a line``.
- R3, the modes that write nothing. `--check` on such a target prints, in place of the diff, `render: <target> <state>; <next>` on stdout, then the loaded-bytes line as at the pin, and exits 1. `--lint` is byte for byte the pin's. `--fold-tails` refuses with R2's line before it folds, the ledger untouched.
- R4, `init` adds the block. Where the ledger's path holds a regular file and the `CLAUDE.md` beside it holds a block, the pin's refusal stands word for word, exit 2. Where that file holds none or is absent, `init` lints the ledger as `render` does (a problem prints the lint's lines, exit 1, nothing written), then writes the block rendered from the ledger as it stands, through `render`'s own `block` and `apply`, under the file's own lines; changes no byte of the ledger; lists `CLAUDE.md` alone on the edit-gates list; and prints on stdout, exit 0: `init: DECISIONS.md is already there; it stays as it is`; `init: wrote CLAUDE.md: 0 B to 236 B, +236 B; the block is loaded on every turn`; the gate's line for `CLAUDE.md`, when it is newly listed; the pin's `init: next, ...` line. Every other refusal of `init` at the pin stands (a folder at the ledger's path, markers that are not one block, a block another ledger wrote), and `init` in a repo with no ledger is byte for byte the pin's.
- R5, `answer`. Its line keeps its first two clauses and ends in R2's `<next>`: ``answer: CLAUDE.md holds no GENERATED markers; the block is left as it is; `agentik decisions init` adds it``. Exit 0, the entry written, as at the pin.
- R6, the texts. The docstrings of `render.py` and `init.py`; the help lines for `render` and `init`; a clause each in `plugin/commands/render.md` and `init.md`; the two places `plugin/skills/decisions/SKILL.md` says what `render` and `init` write. In `design/readme/source.md` and `README.md`, by hand in both as dc1 did: the sentence on `render` appending when the markers are absent, and `init`'s line under `## The tool`; the lines above the first `##` stay byte for byte; then the sidecar by the recipe's own `shasum` line.
- R7, the tests that lean on the old add. Each takes its block from `init`, or from a fixture that holds the two marker lines; its assertions stay. A test whose subject was the append moves to `init`.
- R8, the version: 0.22.4 (GUIDE section 7, a change of behaviour with no new verb), alone as the last commit under `plugin/`.

## 3. Interfaces: the acceptance list

Cases in `tests/test_dc2_render_invited.py`, each in a temp HOME and a new `git init` repo, the tool run from the worktree; L is written as a fixture, so the repo starts with no `.claude` folder.

1. L and H, `render`: exit 2; stderr is R2's line with `CLAUDE.md holds no generated block` and `` `agentik decisions init` adds it ``; stdout empty; H byte for byte; no `.claude` folder. Red at the pin.
2. L alone, `render`: exit 2, `CLAUDE.md is absent`; no `CLAUDE.md`, no `.claude`. Red at the pin.
3. Hand lines above and below a block that holds the one line `old text`: `render` prints `render: wrote CLAUDE.md: 79 B to 236 B, +157 B; ...` and the gate's line, exit 0; again, `render: CLAUDE.md is fresh`. Green at the pin and after.
4. Each exits 2 with R2's line and leaves every file byte for byte: an empty `CLAUDE.md`; one of blank lines; one whose only markers are in a code fence; one with CRLF line ends; a link to a hand-kept `AGENTS.md` beside it; a link to a hand file in another folder; a link to nothing, and no file is made there.
5. `render --into NOTES.md` over a hand file, and `--into NEW.md` with no such file: exit 2, R2's line ending in the two marker lines; nothing written. With the two marker lines put in `NOTES.md`, the same command exits 0 and the block is between them.
6. `render --check` on lines 1 and 2: exit 1; stdout's first line is R3's; no line starts `+++`; the last line is the pin's loaded-bytes line; nothing written. `render --lint` on line 1: stdout and stderr byte-equal to the pin's.
7. L committed with a tail to fold, and H: `render --fold-tails` exits 2 with R2's line and L is byte for byte.
8. L and H, `init`: exit 0; L byte for byte; `CLAUDE.md` is H, a blank line and the 236 B block; stdout is R4's four lines word for word; `.claude/edit-gates` names `CLAUDE.md` and not `DECISIONS.md`; then `render` prints `render: CLAUDE.md is fresh`. Red at the pin.
9. `init` over L alone: exit 0, `CLAUDE.md` is the block alone. Over L with its block: the pin's refusal, exit 2, nothing written. Over a ledger that fails the lint: the lint's lines, exit 1, nothing written. `init --ledger sub/DECISIONS.md` over a ledger there: the block lands in `sub/CLAUDE.md`.
10. The round trip: on line 1's and line 2's repos, the command between the refusal's backticks exits 0, and `render` after it prints `is fresh`. With `--ledger sub/DECISIONS.md` the refusal's command carries it and runs.
11. L and H, an `answer` that adds an `Every session` entry: exit 0, the entry in the ledger, H byte for byte, and its line is R5's.
12. dc1's acceptance lines 1, 2 and 4 (an empty repo; `new` and `answer` with no `render` typed; three hand lines) hold as at the pin.
13. Both suites green; `make check` once, last, through the gate queue; the version as R8.

## 4. Findings that name this row: ledger, NICE, forks

Not built: the owner's "benefits to auditing the CLAUDE.md" (the next row's), any change to `--scope tree`, `audit` or the session plugin. No fork.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
