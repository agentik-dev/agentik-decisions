# Packet d27: resync recordlint, run it in doclint, the NICE as a table

The brief `agentik-hq history/sessions/BRIEF-2026-11-01-d27-ar99-r17.md`, shared by three repos, in this repo's packet shape (GUIDE §9, doclint): its rows and text as written, cut to this repo's row, home paths named by repo, its four sections under the six headings.

| item | value |
|---|---|
| from | agentik-hq HANDOFF 18 (build 7, the owner's word of 2026-11-01); agentik-hq `design/05-records-as-tables.md` §2, §3, §4, §7 items 6, 7, 8; hq entry 6 |
| pin | agentik-decisions main 728d80b, plugin 0.11.0; worktree `.claude/worktrees/d27-rows`, branch `d27-rows`; commons main eff4fd5 (`scripts/recordlint` d6c5c217, on `env python3`); design/05 counts 0 open S1 to S3 here |
| wall | this repo's worktree only; read agentik-hq, agentik-commons and the other agentik repos at main, never write there, except that agentik-commons' `scripts/sync <this worktree>` writes into this worktree; no push, `--amend`, rebase, merge, real `make install`, real `install-cli`; `claude` only as `claude plugin validate` and `claude plugin test plugin`; a test never writes under the live `.local`, `.claude`, `.config` of the home; never touch the home's `.config/agentik/hooks-follow-launcher`; no relay verb, no relay binary built or run outside `make`'s test harness; no `kill`, `pkill` or signal from a script; never a gate verb under a temp HOME; zsh here, `bash -c` for bash syntax; `rm -r` only as `"${VAR:?}"` |
| may touch | `scripts/` (by `sync` only), `plugin/bin/` and `plugin/lib/` only as `sync` places its canonical copies, `Makefile` (the doclint target), `NICE_TO_HAVE.md`, `history/NICE-2026-11-01.md` (by `git mv` only), `.hygiene-allow`, `plugin/.claude-plugin/plugin.json` and what a test pins to its version (only if `plugin-version-check` asks), this packet as `design/packets/d27-rows.md`, a charter under `history/sittings/` |
| acceptance | §2's acts; `scripts/recordlint` exits 0 on the new NICE; `make doclint` runs it |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c "make check > <scratch log> 2>&1"`, then `agentik session gate wait <id>` in one background Bash, last. It exits 0 whatever the job's code: read the code from its line |
| budget | One commit per act. **Stop at 100k context or 70 tool calls:** commit the act in flight, write the exact resume line, report. `claude-opus-5-5` |

## 1. What the source says (quoted)

Read first, by sections: design/05 §2, §3, §4; commons `GUIDE.md` §9's rows paragraph; commons `scripts/recordlint`'s head comment; this repo's `Makefile` doclint and hygiene targets.

What this is: the last three repos take design/05's tables, as commons, agents, session and hq did today. **Not here:** any other repo; any change to doclint; code.

## 2. Rulings

0. This packet, committed first, as this repo's packet file (its `design/packets/` shape, reshaped so doclint and hygiene pass, as earlier packets were).
1. **Resync.** agentik-commons' `scripts/sync <this worktree>`; commit what it places. If it changes anything beyond `scripts/recordlint` and its `vendored.sha256` line, list each path in the report, and run the tests before committing: a canonical copy that breaks a test of today's behaviour is a stop.
2. **Makefile.** The `doclint` target runs `scripts/recordlint` after its existing lines.
3. **The NICE.** design/05 §3: `git mv NICE_TO_HAVE.md history/NICE-2026-11-01.md`, and in that commit `history/NICE-2026-11-01.md: sibling` under the `NICE_TO_HAVE.md: sibling` row of `.hygiene-allow` (same group and a matching comment). A new `NICE_TO_HAVE.md`: a title, one head paragraph naming the archive, then `\| id \| level \| area \| finding \| evidence \| from \|` under a `##`, holding the S1 to S3 items confirmed open on main by a `file:line` or a test; ids from `n1`. S4 and unlevelled stay archived. An empty table is fine when none is open; the head paragraph says so.
4. **The version**, only if `plugin-version-check` asks: the patch.
5. The gate, last.

The stop: stop and report, committing what is there, on: `sync` placing a copy that breaks a test; hygiene red on a file that cannot be allowed without a new reason row; an S1 or S2 item found open (report it, do not fix it). A stop is a result.

## 3. Interfaces (signatures, not prose)

`scripts/recordlint [FILE...]`, vendored by `sync` under `scripts/vendored.sha256`; `make doclint` runs `scripts/doclint`, then `scripts/recordlint`.

## 4. Findings that name this row

design/05 §3: this repo's NICE holds 0 open S1 to S3 by its count; the frozen archive stays as written.

## 5. Forbidden reads

A file over 8 KB whole; a relay ledger or a reference snapshot whole; anything outside this repo but the brief, agentik-hq's design/05, commons' GUIDE and `scripts/recordlint`, the other agentik repos read only.

## 6. Report (at most eight lines)

The branch and sha; each act's commit; what `sync` placed; the gate's id and its code from its line; the suite's counts; the NICE rows kept (ids, levels, one line each); if stopped, the exact resume line.
