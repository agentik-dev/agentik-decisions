# Packet d29: `analyze`, churn first, and a block without its tails

Revised 2026-11-09: the owner named the verb `analyze`. This packet, the design, the row, its branch and worktree keep `churn` in their names.

| item | value |
|---|---|
| from | the design `design/d29-churn.md` (agentik-hq `history/sessions/DESIGN-2026-11-09-decisions-churn.md`, refuted once), with audit row d2; hq entries 6 and 9 (§1). This repo keeps no ledger |
| pin | agentik-decisions main after d30 lands, plugin 0.13.0, `399` cases; worktree `.claude/worktrees/d29-churn`, branch `d29-churn` off that main |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install` or `install-cli`; no `make` outside the gate queue, no `make readme` (it runs `claude`); never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state directory; no test writes under the live home or runs git in a live repo; no gate verb under a temp HOME; python runs with `-B` |
| may touch | `plugin/lib/decisions/{analyze,cli,__init__,render}.py`, `plugin/lib/decisions/common.py` (`VERSION` only); `plugin/commands/analyze.md`; `tests/test_{analyze,render,answer,cli,plugin}.py`; `README.md`, `design/readme/{source.md,rendered.sha256}`, `CLAUDE.md`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `.hygiene-allow`, `NICE_TO_HAVE.md`; `design/d29-churn.md`, this packet as `design/packets/d29-churn.md`; a charter |
| acceptance | `PYTHONPATH=plugin/lib python3 -B -m unittest -v tests.test_analyze -k test_known_ 2>&1 \| grep -c ' \.\.\. ok$'` reads 15 (87f491f: 0); `PYTHONPATH=plugin/lib python3 -B -m unittest -v tests.test_render tests.test_answer -k test_tails_ 2>&1 \| grep -c ' \.\.\. ok$'` reads 5 (87f491f: 0); `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the job's code: read the code from its line |
| budget | 100 tool calls or 120k context, `claude-opus-5-5`; one commit per act by explicit path; the packet, the design and the charter first |

## 1. What the source says

Read first: `design/d29-churn.md`; `backlog.py`'s `nice_items` and `cmd_backlog`; `common.py`'s `bounded` and `git_top`; `render.py`; the hung git of `tests/test_common.py`. The survey (agentik-research `research/synthesis/tools-decisions.md` §1.5, §2.3, §2.5) has nothing on git history: this is the tool's first `git log`.

- hq entry 9: `analyze` joins `doctor` and `backlog` beside its "six verbs". `render` "copies that section into a generated block": the owner's yes covers act 4, and the hq sitting amends the entry.
- hq entry 6: "a runtime floor of Python 3.9 on the standard library alone"; `make test` reruns on `/usr/bin/python3`.

**Not here:** design §7's fold and §8's list; re-rendering any CLAUDE.md; the skill.

## 2. Rulings

0. This packet and the design (from agentik-hq, bytes unchanged), a `.hygiene-allow` row for the design, the charter: one commit, first.
1. `analyze.py`: `ANALYSES` and the word after the verb (design §1); churn's class table, the numstat read, R1, R2, R3; the subparser and `VERBS`; `__init__` re-exports it.
2. R4: snapshots, forms, filed, closed, moved, rising.
3. The text and `--json` views, the exits, the bound, the read-only tests.
4. d2 (design §6), on the owner's yes: `render.block` writes the short tail and `--check` passes both forms.
5. Docs: `plugin/commands/analyze.md` as `backlog.md`; README and its source, edited alike by hand (each place `backlog` is listed, the block paragraph's "verbatim", the status line) on the bytes of its `0.6.0` note, deleted (891 B at 87f491f, `grep '0\.6\.0' README.md | wc -c`), then the sidecar; `CLAUDE.md`'s verb line.
6. Version 0.14.0, last: a minor for a verb and a block form.
7. The gate.

Decide inside the design; record each choice in the charter's Handover. Stop and report, committing what is there, on a §3 answer your code cannot reach without changing a definition, or a test of today's behaviour that must change beyond §4's.

## 3. Interfaces

`agentik decisions analyze [churn] [REPO...] [--since Nd|YYYY-MM-DD] [--until YYYY-MM-DD] [--json]`; `render.block(ledger, path, target, tails=False)`.

`--json`: `{since, until, churn: {repos: [{repo, head, commits, landings, lines: {<class>: n}, vendor, record_commits, charters: {count, median, max, alone: {commits, median, max}}, nice: {snapshots: [{at, commit, form, items}], filed, closed, moved, rising}, not_measured: []}], all: {commits, landings, lines, record_commits}, skipped: [{repo, why}], not_computed: []}}`; `all` is `null` under two repos.

Fixtures: the test builds each in a temp directory, `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` fixed (merges too), identity by `-c`. The window is 2026-10-26 to 2026-11-09.

| | built as | known answer |
|---|---|---|
| A | one commit each: `src/app.py` 5 lines, `tests/test_app.py` 3, a charter 4, `vendor/lib/x.py` 7 | commits 4; product 5, test 3, charter 4, vendor 7; `records 33% of 12 lines`; record commits 1; landings 0, R2 `not measured`; charters 1, median 1 |
| B | 2026-10-20: `src/app.py`, 20 lines. Branch `row`: a packet 6 with a charter 2; `git mv` to `plugin/lib/app.py` plus a line, the charter to 3 lines; to 4; to 5; `merge --no-ff`; then a second charter 2 with `HANDOFF.md` 9 | commits 5, landings 1; charter 7, packets 6, handoff 9, product 1; `records 96% of 23 lines`; record commits 4, `4.0 a landing`; charters 2: median 2.5, max 4; alone 2: median 1, max 2 |
| C | rows n1 n2 (10-25); n2 n3 n4 (10-30); branch `side` adds n9 (11-01), merged 11-03; n3 n4 n5 n6 n9, n2 in the overflow (11-05) | `NICE 2 3 5 +5 -1 moved 1 rising`; the middle is 4 without `--first-parent` |
| D | three bullets (10-25); a table, n1 (11-01); n1 n2 (11-05) | `NICE 3b 1 2` and design §5's `not measured:` line; with `--since 2026-11-02`, `NICE 1 2 +1 -0` |
| E | one commit, 2026-10-01 | commits 0; R1 to R4 each `not measured`; exit 0 |

`tests/test_analyze.py`, fifteen `test_known_`: `classes` (with design §5's last line), `no_landing` (A; the bare `analyze` prints the same); `landing_and_rename`, `charters`, `json` (B, the keys above); `rows`, `first_parent` (C); `bullets` (D); `empty` (E); `all` (A and B: `== all 2  commits 9  landings 1  records 74% of 35 lines  record commits 5, 5.0 a landing`); `exits` (not a work tree: its line, 0; not a directory, a bad `--since`, `since` after `until`: 2); `dates` (a logging git: no bare date in `--since`, `--until`, `--before`); `git_verbs` (only `rev-parse`, `log`, `rev-list`, `show`); `timeout` (a hung git, `GIT_TIMEOUT` 1: the line, no ratio, exit 0); `writes_nothing` (A to D with `.git`; text and `--json`).

Five `test_tails_`, on design §6's three tails: `short_in_the_block` (the three lines; 75 B under the whole form), `whole_form_checks_fresh` (exit 0, stderr's `75 B more`, nothing written), `stale_still_exits_1` (a whole-form block, then the ledger changes), `render_rewrites_then_fresh`, and in `tests/test_answer.py` `after_amends` (amended with d30's `--add`: the block's line ends `; amended once, see the ledger)`).

## 4. Findings that name this row

Audit d2: `answer.py:111-112`, `render.py:68` at 87f491f. Tests of today's behaviour that change: `Base.block()` in `tests/test_render.py` (the sample's two lines lose `; the sample`), `VERBS` in `tests/test_cli.py`, and in `tests/test_plugin.py` `COMMANDS`, the six-commands test and `served`, which leaves `backlog.md` out. NICE rows to file: F5 (S3) and F6 to F8 (S4) of `REFUTE-2026-11-09-d29-design-r1.md`, beside the design.

## 5. Forbidden reads

A file over 8 KB whole, but `backlog.py`; a relay or session ledger; a transcript; outside this repo, only the agentik-hq records named here and agentik-research's survey.

## 6. Report (at most eight lines)

The branch and sha; each act's commit; the gate's id and its code from its line; the suite's count; each §3 answer met or not; each choice; the NICE rows; if you stopped, the resume line.
