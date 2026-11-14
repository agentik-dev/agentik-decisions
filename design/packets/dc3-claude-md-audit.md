# Packet dc3-claude-md-audit: the line that says what a hand-kept file loads, and the skill that audits it

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-13, brief dc3 |
| pin | main at `ab7b4f5` (0.22.5), the merge of dc2-render-invited. The version waits for phase 2. Worktree `.claude/worktrees/dc3-claude-md-audit`, branch `dc3-claude-md-audit`, nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test runs the real `claude` or writes under the real home |
| may touch | `plugin/lib/decisions/render.py`, `init.py`; `plugin/skills/audit-claude-md/SKILL.md` (new); `plugin/skills/decisions/SKILL.md`; `CLAUDE.md`; `README.md` and `design/readme/{source.md,rendered.sha256}`; `tests/test_dc3_claude_md_audit.py` (new), `tests/test_plugin.py` (its list of skills), and each test that asserted the pin's stdout of `init` or `render` over a hand-kept file; the version places at phase 2; `NICE_TO_HAVE.md`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_dc3_claude_md_audit tests.test_dc2_render_invited tests.test_dc1_init tests.test_instruct tests.test_plugin` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words: "we really should make it clear there are benefits to auditing the CLAUDE.md - perhaps we even vend a skill to help the claude code session refactor these files."

A packet row (suite entry 17). Cited: entries 6, 7, 8 and 37.

Measured at `ab7b4f5` (0.22.5), a temp HOME, a new git repo. F is a `CLAUDE.md` of five lines: `# Mine`, a blank line, `<!-- a note for people -->`, `Never push on a Friday.`, `@docs/extra.md`; `docs/extra.md` is two lines, 32 B. By `tree.loaded_bytes`, F loads 79 B: 47 of hand lines, 32 of the import, the comment's 27 not counted. L is a ledger of one `Every session` entry.

- F, `init` with no ledger: four lines, the ledger's, `wrote CLAUDE.md: 0 B to 171 B`, the gate's line for both files, `init: next, ...`; exit 0. Nothing says what F loads.
- F and L, `init`: `init: DECISIONS.md is already there; ...`, `wrote CLAUDE.md: 0 B to 236 B`, the gate's line, `next`; exit 0.
- F and L, `render`: stdout empty; stderr dc2's refusal, `` ...holds no generated block, and render only rewrites a block that is there; nothing written; `agentik decisions init` adds it ``; exit 2.
- F and L, `render --lint`: the block's size, then `render: CLAUDE.md loads 246 B, comments aside and imports included; ...`; the warning on line 4's `never`; exit 0. `--check`: dc2's line and the loaded bytes, exit 1.
- The descriptions `tests/test_instruct.py` counts: 483 B of 1,024 (`scripts/plugin-description-bytes`).

## 2. Rulings

- R1, the figure. What the file loads as its owner wrote it, before any block: `tree.loaded_bytes` of the target's text, comments aside and imports included. The line prints only when that text, comments aside, holds a line that is not blank.
- R2, the line, on stdout, the figure with thousands commas as `measure` writes them: ``<verb>: <target> loads <N> B of hand-written text on every turn of every session started here; /decisions:audit-claude-md goes through it with you and finds the lines no session acts on and the rules that belong in the ledger``. `init` prints it when it adds the block to such a file, the ledger new or already there: after the gate's line, before the `next` line. `render` prints it before it refuses such a file for holding no block. Nothing else prints it: not `--check`, `--lint`, a run that rewrites a block, or an absent file.
- R3, the skill. `plugin/skills/audit-claude-md/SKILL.md`, the brief's page word for word. Where a command it names differs at the pin, trust the code and say so. Its `disable-model-invocation: true` keeps its description out of every session; only the typed command starts it.
- R4, the texts. `CLAUDE.md`'s sentence on the plugin's skills (four, one started only by a person). One line in `plugin/skills/decisions/SKILL.md` where it lists what the owner types. In `design/readme/source.md` and `README.md`, by hand in both as dc1 did, one line under `## The tool`, the lines above the first `##` byte for byte, then the sidecar.
- R5, the version: the next by GUIDE section 7 for a new skill, alone as the last commit under `plugin/`, at phase 2.

## 3. Interfaces: the acceptance list

Cases in `tests/test_dc3_claude_md_audit.py`, each in a temp HOME and a new `git init` repo.

1. F, `init`, with no ledger and with a ledger there: stdout holds R2's line word for word with `init:`, `CLAUDE.md` and `79 B`, after the gate's line and before `next`. A text that loads over 999 B prints its figure with a comma. Red at the pin.
2. F and a ledger there, `render`: stdout is R2's line with `render:`; stderr is dc2's refusal; exit 2; nothing written. Red at the pin.
3. No line: `init` in an empty repo; `init` and `render` over an empty file, one of blank lines, and one of a comment alone; `render` over an absent file.
4. Byte-equal to the pin, stdout and stderr: `render --check` and `render --lint` over F; `render` over a fresh block and over a stale one; `answer`.
5. The page is R3's text; its frontmatter holds `name: audit-claude-md` and `disable-model-invocation: true`; the sum the descriptions test counts is the pin's, 483 B, to the byte.
6. Each `agentik decisions <verb>` the page names is a verb of the tool, and each flag beside it a flag of that verb; `render --lint` and `render --lint --into <draft>` run on F's repo, exit 0, each printing a `loads N B` line, and no file changes.
7. The page holds step 2's eight names; no byte figure, by the pattern `tests/test_instruct.py` holds the `instruct` page to; none of the eight tests' sentences; and each `/decisions:<name>` the page or a printed line names is a file under `plugin/commands` or `plugin/skills`.
8. Both suites green; `make check` once, last, through the gate queue; the version as R5 at phase 2.

## 4. Findings that name this row: ledger, NICE, forks

Left out: a verb or flag that marks hand lines; a model's walk in a test (the first walk is the owner's); any change to the `instruct` page; a model-started form of the skill. No fork for the owner; one line is new, so no respeak pass.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
