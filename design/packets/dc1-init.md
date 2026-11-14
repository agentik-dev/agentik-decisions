# Packet dc1-init: `init`, a ledger and its block in a new repo, and a verb that says what it gated

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-13, brief dc1 |
| pin | main at `b059365` (0.21.17), as the brief names. Version 0.22.0. Worktree `.claude/worktrees/dc1-init`, branch `dc1-init`, nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test runs the real `claude` or writes under the real home |
| may touch | `plugin/lib/decisions/init.py` (new), `cli.py`, `ledger.py`, `render.py`, `answer.py`; `plugin/commands/init.md` (new), `plugin/skills/decisions/SKILL.md`; `tests/test_dc1_init.py` (new) and each test whose expected text R4 to R6 change; `CLAUDE.md`'s first paragraph and its count of commands; `README.md` and `design/readme/{source.md,rendered.sha256}` under `## The tool` only; the version places; `NICE_TO_HAVE.md`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_dc1_init tests.test_plugin tests.test_cli` |
| budget | about 90 tool calls |

## 1. What the source says: the code at the pin

The owner's words: "How close are we to being able to install this on my work computer?" and "I want to use it today." A newcomer's second act with the suite is to settle one thing in a repo and watch a new session obey it. At the pin that repo has no ledger and no verb makes one, the answer never reaches `CLAUDE.md`, and the tool gates two of the person's files without a word.

Cited: the suite's entries 6 (a 3.9 floor, the standard library alone), 7 and 8 (a ledger's voice), 9 (the six verbs; `init` joins the verbs beside them, as `doctor` and `backlog` do), 17 (a new verb takes a packet) and 37 (made-up names). The baseline at `b059365`: §3.

## 2. Rulings

- R1, the verb. `agentik decisions init [--ledger PATH]`. Where `locate` would refuse with "no ledger at", it writes the ledger: the title line `# Decisions` and the three sections `## In force`, `## Proposed`, `## Superseded`, empty, in the shape `render --lint` passes. Then it writes the block into the `CLAUDE.md` beside the ledger through `render`'s own `block` and `apply`: 171 B at the pin, appended under whatever a hand-written `CLAUDE.md` holds, no line of that file changed. No `OPEN-QUESTIONS.md`: `new` makes it.
- R2, what `init` prints, on stdout, one line a write: the ledger written; the block's line in `render`'s own words (`0 B to 171 B, +171 B; the block is loaded on every turn`); R4's line; a last line naming `agentik decisions new` as the next act. Exit 0.
- R3, where `init` refuses, exit 2, nothing written: a ledger is already at the path (the line names it); outside a git work tree with no `--ledger` (the pin's refusal, unchanged).
- R4, the gate says itself. `list_gate` returns the list it wrote, or None. Each caller that gets a list back prints one line on stdout: the file now listed, the list's path, that a session changes the file through `/decisions:instruct` and never by its own edit, and that deleting the line lifts it. `init` lists `DECISIONS.md` and `CLAUDE.md` and says both in one line. `render` and `answer` say theirs the first time; a file already listed prints no line.
- R5, every "no ledger" refusal names the next act: `locate`'s `no ledger at <path>` gains a clause naming `agentik decisions init`; `doctor`'s `ledger` warning carries `locate`'s words, so it gains the same. The bare command's verb list and `--help` gain `init`.
- R6, `answer` with no markers: its line gains what writes the block, `agentik decisions render` (with `--ledger` and `--into` when given). Exit 0; `answer` still never makes a block where none is.
- R7, the command. `plugin/commands/init.md`, in `install-cli.md`'s form: the plugin's own launcher, `${CLAUDE_PLUGIN_ROOT}/bin/agentik-decisions init $ARGUMENTS`, `disable-model-invocation: true`, the output relayed verbatim. A person who installed the plugin alone has no `agentik-decisions` on the terminal.
- R8, the texts. The `decisions` skill gains `init` where it lists the verbs; `README.md` and `design/readme/source.md` gain it under `## The tool` only, by hand, the lines above the first `##` byte for byte; the sidecar by the readme recipe's `shasum` line; `CLAUDE.md`'s first paragraph names it.
- R9, the version: 0.22.0 (GUIDE §7, a new verb), alone in the last commit under `plugin/`.

## 3. Interfaces: the acceptance list

Cases in `tests/test_dc1_init.py`, each in a temp HOME and a repo made by `git init`. At `b059365`: line 1's command is an argparse `invalid choice: 'init'`, exit 2; line 6's verbs each print `decisions: no ledger at <repo>/DECISIONS.md`, exit 2; line 8's `answer` prints `answer: CLAUDE.md holds no GENERATED markers; the block is left as it is` and leaves no `CLAUDE.md`.

1. `init` in an empty repo: exit 0; the three sections, `render --lint` clean; `CLAUDE.md` is the block alone, 171 B; `.claude/edit-gates` lists both files; stdout names the ledger, the block and both gated files.
2. Then `new --title "Indent" ...` and `answer 1 --pick Spaces ... --area "Every session" --every-turn`: each exit 0; `answer: rewrote the block in CLAUDE.md: 171 B to 236 B, +65 B; the block is loaded on every turn`; the entry's line in `CLAUDE.md`; `render --check` exits 0, no `render` typed.
3. A second `init`: exit 2, a line naming the ledger, every file byte for byte.
4. A `CLAUDE.md` of three hand-written lines: they stand byte for byte, the block after them.
5. Outside a git work tree: exit 2, nothing written. `--ledger <dir>/DECISIONS.md`: both files beside that path.
6. No ledger: `show 1`, `new` and `render` exit 2 with a line holding `agentik decisions init`; `doctor`'s `ledger` line too.
7. A hand-made ledger: the first `render` says `CLAUDE.md` is listed and names `/decisions:instruct`, the second nothing; the first `answer` says it of `DECISIONS.md`, the second nothing.
8. `answer` where `CLAUDE.md` has no markers: exit 0, its line names `agentik decisions render`.
9. `plugin/commands/init.md` runs the plugin's launcher; that launcher with PATH `/usr/bin:/bin` holds line 1; `--help` lists `init`.
10. The README above its first `##` is the pin's; `shasum -a 256 -c design/readme/rendered.sha256` OK.
11. `make check` green through the gate queue.

## 4. Findings that name this row: ledger, NICE, forks

Not built: the README's top (fh5), `describe` (ak6), any change to the session plugin, a verb that removes a ledger or lifts a gate, a change to `--every-turn`'s rule. No fork; four messages new or changed, so no respeak pass.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
