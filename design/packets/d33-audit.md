# Packet d33: `audit`, the ledger's retire and rewrite candidates

| item | value |
|---|---|
| from | agentik-hq `design/08-fill-wait-reconciler.md` §4 (P1 to P8), §5 row 7, §7, §11 C2; hq entries 7, 9, 17; the suite's survey of the decisions tool, §2.1. No entry is carried |
| pin | main 2bde45c (0.16.1, d32 and its fold); the bump is 0.17.0; worktree `.claude/worktrees/d33-audit`, branch `d33-audit`. Words quoted are de67e4e's: find each by its words |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install`, `install-cli`, bare `make` or `make readme`; never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state; no test reads a real ledger |
| may touch | `plugin/lib/decisions/{audit,cli,common}.py` (`common`: `VERSION` only); `tests/test_{audit,cli,plugin}.py`; `plugin/commands/audit.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `CLAUDE.md`; `NICE_TO_HAVE.md`; this packet as `design/packets/d33-audit.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib /usr/bin/python3 -m unittest -v tests.test_audit 2>&1 \| grep -c ' \.\.\. ok$'` reads 12 (de67e4e: 0), and under 3.12.7; `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; `wait` exits 0 whatever the job's code: read the code from its line |
| budget | a commit per group by explicit path, the packet and the charter first; stop at 90 tool calls or 140k context with a resume line; `claude-opus-5-5` |

## 1. What the source says

This copy shortens hq's §1 to fit doclint's 9,216 B merges its §3 Tests and §4 Interfaces into doclint's six sections, and names no other repo; the rulings are hq's word for word but ruling 4's old-name example, made generic. At de67e4e, `P` = `PYTHONPATH=plugin/lib /usr/bin/python3 -m decisions`:

- `$P audit`: `invalid choice: 'audit'`, exit 2.
- To reuse: `ledger.amended(tail)`, `IN_FORCE_CAP = 25`, `render.block`; `analyze`, `backlog` take `REPO...`; no suite.json reader.
- Retire has no verb: `answer.py`'s cap refusal says move the line under `## Superseded`.
- README 24,570 B; `test_source_size` caps it at 24,576.
- hq 9 names six verbs; `backlog`, `analyze` sit beside them, excluded by `test_descriptions_name_six_verbs_plus_doctor`.
- The prototype, read-only, `--json` counted:

| ledger, tree | in force | P1 | P2 | P3 | P4 | P5 | P6 | P8 | Every session |
|---|---|---|---|---|---|---|---|---|---|
| agentik-hq, suite.json | 12 | no | 1 | 3 | 1 | 0 | 0 | 0 | 0 of 2 |
| the machine's ledger | 5 | no | 1 | 4 | 0 | 0 | 0 | 0 | 4 of 4, 4,554 B |
| a second hq | 25 | yes | 0 | 0 | 0 | 2 | 7 | 0 | 0 of 4 |
| the second hq, 9 siblings as tree | 25 | yes | 0 | 0 | 0 | 0 | 3 | 0 | 0 of 4 |
| a third hq | 14 | no | 5 | 1 | 0 | 0 | 9 | 1 | 0 of 1 |
| the third hq, 7 siblings as tree | 14 | no | 5 | 1 | 0 | 0 | 2 | 1 | 0 of 1 |

The design's numbers hold; a tree cuts P5 2 to 0 and P6 16 to 5 (§5 row 7).

## 2. Rulings

1. **The verb.** `audit [REPO...] [--tree FILE] [--json]`, `audit.py`. It parses the ledger tolerantly, as `show` does, runs only `git rev-parse` and `git --no-optional-locks grep`, each bounded at `GIT_TIMEOUT`, writes nothing, takes no lock. Exit 0 whenever the view printed; 2 for usage, an unreadable ledger or `--tree`, a REPO no directory (`audit: <x> is not a directory`, `audit: --tree <x> is not a file`).
2. **The tree** (my choice; the design names suite.json's shape only): REPO directories, as `analyze` takes them, plus `--tree FILE`, `{"repos": [{"name": N, "path": P}]}`, relative ones resolved against the directory above FILE's (`~/code` for hq's). One absent or ungreppable prints `not read: <name>`. Neither: the ledger's git top.
3. **P1 to P4.** P1, in the head line: `N of 25 in force (P1, at the cap)`. P2: `amended(tail) >= 3`. P3: the tail holds `moved from` or `moved here` (my choice: hq's tails say "moved here"), its clause quoted. P4: the tail's bytes over the paragraph's.
4. **P5.** A citation: `entry N`, `entries N, M and K`, `<alias> N`, `<alias> entry N`, any case; aliases are the repo's name and, for `X-hq`, `X` and `hq`. Read: the tree's tracked text files (`git grep -I -i -l -z -E` picks them) but the ledger, plus every other entry's line. Any match counts, so a P5 means nothing names N. An old name (a repo's former name and a number) is missed: a NICE line.
5. **P6.** A backticked token with a `/`; no placeholder (`<>*{}$=`, a space, `...`), not opening `-` or `#` or `host.tld/`; a `:N` suffix cut. Gone when under none of the ledger's top, each tree repo, the top's parent; `~` and absolute as they are. And `decisions X`, X not in `cli.VERBS`; other tools' verbs are not checked (that runs another tool). Today's residue, three tokens that name no path of the tree, a reader dismisses at a look.
6. **P7 is not detected** (my choice): hq 7's test is what a subject is, not its words; eleven process words (review, session, packet, owner, ...; the probes' README) hit 54 of the four ledgers' 56 bodies. The text prints `not detected: P7 (...): a reader confirms it`; `--json` `"not_detected": ["P7"]`.
7. **P8 is a lead.** Title words less a stop list; a pair shares at least 2 and over half the shorter's. Under `Leads, for a reader to confirm:`, never a mark; `--json` `leads`, `"lead": true`.
8. **Order and bytes** (the orchestrator's). `Every session, paid every turn:` first, then `Other entries in force:`; each `N Title  <bytes> B  P2 ...; P5 ...`. The bytes: the entry's line in `render.block`'s output plus its newline, read from it, not copied (the prototype copies `short_tail`; d32 changes the block).
9. **The end**, the text's last line verbatim: "audit edits nothing. The owner acts in one batch: `agentik decisions new` puts each retire or rewrite question, `ask` asks them, `answer` enters each: a rewrite is `answer N --amends M --shorter`, a retire moves the entry's line under `## Superseded`."
10. **Texts and 0.17.0**, last. `common.VERSION`, `plugin.json`, `pyproject.toml`, `test_plugin.py`'s `VERSION` (1298da5's four). `cli.py`'s docstring: a Verbs row, exits 0 and 2. `plugin/commands/audit.md` on `analyze.md`'s model; `COMMANDS` and the six-verbs exclusion; `test_cli.py`'s `VERBS`; `CLAUDE.md`'s verb line. README and source alike, by hand, at most 24,576 B: the verb, exit, command, test, status, `plugin/commands/` rows, cutting bytes elsewhere; the case count; the sidecar. The marketplace line is hq's.

## 3. Interfaces: the tests, then `--json`

The probes' `test_d33.py` becomes `tests/test_audit.py`. At de67e4e 12 red, `invalid choice: 'audit'`; on the prototype 12 green, 3.9.6 and 3.12.7.

| T | test | holds |
|---|---|---|
| 1 | `test_p1_at_the_cap` | 25: P1; 24: none |
| 2 | `test_p2_amended_three_times` | 3 dated, T2's 2 plus 1: P2; 2: none |
| 3 | `test_p3_moved_tail` | from, here: P3; in a body: none |
| 4 | `test_p4_tail_longer_than_body` | P4 |
| 5 | `test_p5_uncited_in_the_tree` | each citation form; own line no cite |
| 6 | `test_p5_tree_file_of_suite_shape` | `--tree`; `not read: absent` |
| 7 | `test_p6_gone_path_and_verb` | gone path and verb; placeholder none |
| 8 | `test_p7_named_not_detected` | named, no mark |
| 9 | `test_p8_title_overlap_is_a_lead` | under Leads only |
| 10 | `test_every_session_first_with_block_bytes` | first; the block's line plus 1 |
| 11 | `test_writes_nothing_and_ends_with_the_owner_way` | bytes and mtimes kept; ruling 9 |
| 12 | `test_exit_two_for_usage` | REPO, `--tree`, `--ledger`: 2 |

The verb turns 3 of today's tests red, ruling 10's lists: `test_cli`'s `test_help_lists_the_eight_verbs`, `test_no_verb_exits_2`, `test_the_runner_prints_help` (and through them `test_hermetic`'s and `test_backlog`'s whole-suite cases).

`audit --json`: `ledger, in_force, cap, at_cap, every_session, every_session_cap, block_bytes, candidates [{number, title, area, every_session, bytes, marks [{mark, lead, evidence}]}], leads [{mark, lead, numbers, titles, shared}], not_detected, tree, not_read`, for design/08's reconciler.

## 4. Findings that name this row

design/08 §11 C2 (S4): T1 to T12 cover `audit`. Survey §2.1, retire has no verb: ruling 9 names the hand edit. design/08 §7: hq 9's verb list is the churn draft's open question; no ledger is amended here.

## 5. Forbidden reads

Other repos but `from`'s records and the probes; the real ledgers. The relay's state. Transcripts.

## 6. Report (six lines)

Each commit; the acceptance readings; the gate's id and line; the README's bytes; the NICE rows; each choice.
