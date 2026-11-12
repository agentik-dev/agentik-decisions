# Packet d37: the lane for changing an instruction: `instruct`, `answer --preview`, `audit --edits`

| item | value |
|---|---|
| from | hq design/09 §2 (the layers and their order, which step 4 uses), §7.1 (the skill and its command: the flow's eight steps, what it refuses, what goes to the owner), §7.2 ("The list that sees the rest", the guarded files), §7.3 (the table `where` prints), §7.4; the instruction audit's eight tests ("The tests, for each line"). No entry is carried: this repo keeps no DECISIONS.md (`CLAUDE.md`, Authority); hq 9 binds the ledger's verbs, cited by number. The second of two packets; d36 built `render --scope tree` and the ceilings |
| pin | main 5a68c0f (0.20.1); the bump is 0.21.0, a packet's minor for new flags and a skill; worktree `.claude/worktrees/d37-instruct`, branch `d37-instruct`; nothing linked from main |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install`, `install-cli`, bare `make` or `make readme`; no `claude` process, subagent or plugin update; never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state; no test reads a live ledger or writes above its temp folder; no `answer` and no writing `render` against a real ledger |
| may touch | `plugin/lib/decisions/{answer,audit,cli,common}.py` (`common`: `VERSION` only); `tests/test_instruct.py` (new), `tests/test_{plugin,cli}.py`; `plugin/skills/instruct/SKILL.md` and `plugin/commands/instruct.md` (new); `plugin/commands/*.md` (the flag) and `plugin/skills/{decisions,ask}/SKILL.md` (descriptions, a pointer); `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `CLAUDE.md`; `NICE_TO_HAVE.md`; `.hygiene-allow`; this packet |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib /usr/bin/python3 -m unittest -v tests.test_instruct 2>&1 \| grep -c ' \.\.\. ok$'` reads 21 (5a68c0f with this file: 1), and under 3.12.7; the descriptions the model loads sum under 1,024 B, as `tests.test_instruct` counts them (1,038 B at the pin, two skills and ten commands, without the new skill); `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 and the source is at most 24,576 B (24,497 B at the pin) |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id> --strict` in one background Bash, last |
| budget | a commit per group by explicit path, this packet first, then the tests, then the change; `claude-opus-5-5` |

## 1. What the source says

The owner's words (2026-11-11): "A focus should be on avoiding Claude.md bloat and making sure that the rulings/guidelines/claude configs get updated the correct way through a lane, not ad hoc."

At the pin:

- `answer` writes the ledger and the questions file, then the block; it has no mode that shows its result first. Its refusals (the lint, the growth of the block or of the tree's file, the owner's typed lines, the cap) all come before `commit_texts`.
- `audit` lists the ledger's retire and rewrite candidates and reads no history; it needs a ledger.
- The plugin has two skills and ten commands, none hidden; their descriptions sum to 1,038 B. agentik-commons' main (8db5ccc) holds no description check script; a branch `p1-description-gate` is unlanded, so the sum here is measured by the test, not by a copied script.

## 2. Rulings

1. **`answer --preview`.** Every check `answer` makes runs, under the same lock, and a refusal is the same exit and the same words. Then it prints the entry as it would be written (or `no entry`), the Answered line, `replaced:` and `tail was:` as the answer would, the unified diff of the repo's file as `render` would leave it, and, when the tree's section changes, of the folder's file; and for each file `answer --preview: PATH loads X B now and Y B after, ±D B; the ceiling for KIND is C B`. It writes nothing: the ledger, the questions file and every CLAUDE.md stay byte for byte.
2. **`audit --edits C [REPO]`.** The commits after C to HEAD, oldest first, that touch a guarded path and whose subject does not begin `instruct:`, one line each: the short sha, the subject, the paths. Guarded, at the top level only: `CLAUDE.md`, `CLAUDE.local.md`, `.claude/CLAUDE.md`, `AGENTS.md`, `.claude/rules/**`, `DECISIONS.md`, `.claude/settings*.json`; a path with a `tests`, `testdata` or `fixtures` folder is never guarded. It reads REPO, else `--ledger`'s folder, else the working directory, and needs no ledger. Exit 0 listed or not; a commit name git cannot resolve, or one that opens with `-`, exits 2. `--json` gives the rows.
3. **The skill**, `plugin/skills/instruct/SKILL.md`: §7.1's eight steps, refusals and owner-only changes in the page's own words; the eight tests word for word, their one copy; §7.3's table with a "shown by" command on each row; the chain's three ledgers by how each is found; no figure a writer could aim at.
4. **The command**, `plugin/commands/instruct.md`: `/decisions:instruct [<the change in plain words> | adopt <file> | where]`, `disable-model-invocation: true`; its body sends each form to the skill's page.
5. **The subject.** A change the skill lands is committed as `instruct: <title>: <what changed>`.
6. **Descriptions.** No skill, agent or hook text of this plugin tells the model to start a command (they run the CLI), so each command takes `disable-model-invocation: true`; the two skills' descriptions are tightened.
7. **Records.** README and source by hand under the cap, CLAUDE.md's count of skills and commands, the `decisions` skill's pointer to `instruct`; NICE rows from d36's second review; 0.21.0 in the four version places and `test_plugin.py`.

## 3. Interfaces: the tests

`tests/test_instruct.py`, 21 cases, every file under the case's temp folder. At 5a68c0f 1 ok (a bad commit name exits 2, by argparse there) and 20 red, under 3.9.6 and 3.12.7.

| class | holds |
|---|---|
| `Preview` | ruling 1: every file hashed before and after; the entry, the block's diff and the bytes; the answer after a preview writes the line it showed; an amendment's Every session diff; `--no-entry`; three refusals the same with and without `--preview` |
| `TreePreview` | ruling 1: the folder's file's diff and both kinds of file; its growth refused alike |
| `Edits` | ruling 2: a hand edit listed, an `instruct:` commit, a fixture's ledger, a nested file and code omitted, `.claude/settings.local.json`, `.claude/rules/**` and `AGENTS.md` listed; an empty list exits 0; `--json`; a bad name exits 2; no ledger needed |
| `Skill` | rulings 3, 4 and 6: the eight tests, the flow's commands and the subject, the table's "shown by" column, no byte figure, the command's flag, the description sum |

Tests that change: `test_plugin.py` takes the third skill and the eleventh command.

## 4. Findings that name this row

n47 (the folder's file stale after an answer) stays: `--preview` shows its diff, and `answer` still leaves the write to `render --scope tree`. New rows n54 to n56, d36's second review.

## 5. Forbidden reads

Other repos but hq design/09's sections and the audit page named in `from`, and agentik-commons' main for a description script; a real ledger, OPEN-QUESTIONS.md or CLAUDE.md from a test; the relay's state; transcripts.

## 6. Report

Each commit; the acceptance readings at the pin and now; the gate's id and line; the description sum before and after; the README's bytes; the NICE rows; each choice; the sentences a record outside this repo needs.
