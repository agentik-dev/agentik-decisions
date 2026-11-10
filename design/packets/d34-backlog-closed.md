# Packet d34: the backlog's closed marker and `expire`; `audit` shows every Every session entry

| item | value |
|---|---|
| from | agentik-hq `design/08-fill-wait-reconciler.md` §5 row 7, §6 item 6; the review's P4; GUIDE §9, §10; d23 §2 to §4; d31 ruling 2. No entry is carried |
| pin | main aa61ca7 (74b7cf3, d33 at 0.17.1, plus a hygiene sync); the bump is 0.18.0; worktree `.claude/worktrees/d34-expire`, branch `d34-expire` |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install`, `install-cli`, bare `make` or `make readme`; never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state |
| may touch | `plugin/lib/decisions/{expire,audit,cli,common}.py` (`common`: `VERSION` only); `tests/test_{expire,audit,cli,plugin}.py`; `plugin/commands/expire.md`; `plugin/skills/decisions/SKILL.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `CLAUDE.md`; `NICE_TO_HAVE.md`; this packet as `design/packets/d34-backlog-closed.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib /usr/bin/python3 -m unittest -v tests.test_expire tests.test_audit 2>&1 \| grep -c ' \.\.\. ok$'` reads 36 (aa61ca7: 21), and under 3.12.7; `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; `wait` exits 0 whatever the job's code: read the code from its line |
| budget | a commit per group by explicit path, the packet and the charter first; stop at 90 tool calls or 140k context with a resume line; `claude-opus-5-5` |

## 1. What the source says

Run 2026-11-10 at aa61ca7; `P` is `PYTHONPATH=plugin/lib /usr/bin/python3 -m decisions`.

- design/08 §5 row 7: "one closed marker and an `expire` verb". P4: in another tree 2,549 of 4,352 lines open, 90% S4 or untagged; "closure has no one marker"; "an S4 line not ranked above the cut line in 14 days is deleted (git keeps it)"; S1 to S3 with a reproduction lift into HANDOFF.
- `$P expire`: `invalid choice: 'expire'`, exit 2.
- `backlog.py:38` `CLOSED` reads five closed leads (d31 ruling 2). The suite's 9 NICE files hold 100 items (89 rows, 11 bullets) and 0 closed in any form. The rows hug recordlint's 400-character bound: median 338, max 398.
- GUIDE §9: "a row leaves when it lands"; recordlint moves "the oldest S4 rows, appended, to history/NICE-overflow.md".
- B. In agentik-hq, `agentik decisions audit` prints `... 2 of 7 under Every session; ...`, then `Every session, paid every turn: none`; `--json` `candidates`: 6, none `every_session`. `audit.py:272`, `if marks:`, drops an unmarked entry; the docstring (:25) says they print first.
- The prototype, dry over the suite at 14 days: one repo's 6 unlevelled bullets expire, another's 5 bullets carry no date, 3 S3 rows kept. `--write` on scratch clones (6 bullets; at `--days 1`, 5 rows): each removed line is in the archive byte for byte, the rest in order; again, nothing moves.

## 2. Rulings

1. **The one marker** (the cutter's). Write `Closed YYYY-MM-DD <sha, record or "void">: ` opening a row's `finding` cell, then the finding's lead (the closing commit keeps the rest), or opening a bullet. Today's `CLOSED` reads it: marked copies of the 9 files read 100 of 100 closed. recordlint: the marker before the whole finding puts 29 of 89 rows over 400 (4 files red); before the lead, 1 (403 characters), which the closer shortens. d31's other forms stay read; the docs name this one; no parser change. `(closed DATE)` mid-lead stays an item: n28 leaves.
2. **The verb**, design/08's, not a `backlog` flag: `expire [REPO...] [--order FILE] [--days N] [--write] [--json]`, `expire.py`; REPO and `--order` as `backlog`; it reads no ledger.
3. **Which items.** Each closed item, whatever its date; each open item placed as S4 (S4 or no level) with no `after_step`, dated more than N days ago (14, P4's; `--days`, at least 1). The date: the first valid `YYYY-MM-DD` of a row's `from`, or of a bullet. Kept, listed: S1 to S3 or on an open step's path, past N days ("lift each into HANDOFF.md or close it"). No date: never expires.
4. **Dry by default**, writing nothing: `== <name>  expire: C closed, A S4 older than N days on no open step`; a line per item (`closed  NICE_TO_HAVE.md:L  <id>  <lead after the marker>`, or level, date, age); the kept block; the undated lines; last, `dry: nothing written; --write moves these K, appended byte for byte, to history/NICE-overflow.md`.
5. **`--write` loses nothing.** Each repo with items to move: HEAD holds NICE_TO_HAVE.md byte for byte (`render.head_holds`), all checked before any write, else `expire: HEAD does not hold <path> as it stands; commit it first; nothing written`. Under the repo's `.new.lock`, a re-read (changed: refuse); one `commit_texts` (archive first, rollback): each item's lines, a bullet's indented ones too, leave NICE_TO_HAVE.md, no other byte moving, appended byte for byte to `history/NICE-overflow.md` (made when absent, never rewritten), under ``## <today>: `expire --days N`, from <sha>``, rows under the NICE header, then bullets. Last line: `expire: moved K items from NICE_TO_HAVE.md (X B to Y B) to history/NICE-overflow.md; <sha> holds them too`.
6. **Exits** (GUIDE §10): 0 when the view printed or the move was made; 2 for usage (`--days` under 1), a REPO or `--order` absent, a file unreadable, ruling 5's refusals, a failed write. Never 1: no check says no.
7. **B.** Every Every session entry prints under `Every session, paid every turn:` in block order, `N Title  <bytes> B`, then two spaces and its marks when it has any; ` none` only with no such entry. `Other entries in force:` keeps marked entries only. `--json` gains `every_session_entries` (the cutter's name), each `{number, title, area, every_session, bytes, marks}`, `marks` `[]` when none; `candidates` and every d33 key stay. The docstring says so.
8. **Texts and 0.18.0**, last. The four version places (1298da5's); `cli.py`'s docstring (the patch's); `plugin/commands/expire.md` on `backlog.md`'s; `test_plugin.py`'s `COMMANDS` and six-verbs exclusion (`:183`) gain `expire.md`; `test_cli.py`'s `VERBS`; CLAUDE.md's verb line and design list; a SKILL.md sentence (mark, then `expire`); README and source alike by hand, at most 24,576 B (24,570 today). The marketplace line is hq's.

## 3. Interfaces: the tests, then `--json`

The probes' `test_expire.py` becomes `tests/test_expire.py`; `test_audit_every.py`'s cases join `tests/test_audit.py`. At aa61ca7 15 red (`invalid choice`; no `every_session_entries`; `none`); on the prototype 15 green, 3.9.6 and 3.12.7.

| T | test | holds |
|---|---|---|
| 1 | `test_closed_items_expire_whatever_their_date` | the marker's row, a `~~` bullet |
| 2 | `test_old_s4_and_unlevelled_expire_past_the_bound` | 15 days out, 14 in; `--days 30` |
| 3 | `test_s1_to_s3_and_an_open_steps_path_are_kept_and_listed` | S3; an open step's path |
| 4 | `test_an_item_with_no_date_never_expires` | `undated` |
| 5 | `test_dry_by_default_writes_nothing` | bytes kept; the lines |
| 6 | `test_write_moves_each_line_byte_for_byte` | NICE less them; the archive |
| 7 | `test_write_again_moves_nothing` | idempotent |
| 8 | `test_write_appends_to_an_archive_it_keeps` | a byte-exact prefix |
| 9 | `test_write_refuses_unless_head_holds_the_file` | 2; no byte, two repos |
| 10 | `test_json_names_each_move` | the keys below; `end` |
| 11 | `test_order_file_stands_for_the_handoff` | `--order` |
| 12 | `test_exit_two_for_usage` | REPO, `--order`, `--days 0`, `x` |
| 13 | `test_every_entry_under_every_session_prints_marked_or_not` | both; others marked only |
| 14 | `test_json_gains_every_session_entries_and_keeps_its_keys` | d33's keys; bytes; `[]` |
| 15 | `test_no_every_session_entry_prints_none` | ` none`, `[]` |

Today's tests that change: `test_cli`'s `test_help_lists_the_eight_verbs`, `test_no_verb_exits_2`, `test_the_runner_prints_help` (`VERBS`), and through them a whole-suite case each in `test_backlog` and `test_hermetic`; `test_plugin`'s `COMMANDS` and `VERSION`. `test_audit`'s 21 stay unchanged.

`expire --json`: `{days, today, write, repos: [{repo, nice, archive, expired: [{line, end, id, level, reason, title, date, age}], kept (also after_step), undated, moved, bytes, head}], skipped}`; `reason` is `closed` or `aged`.

## 4. Findings that name this row

design/08 §5 row 7 and §6 item 6. The review's P4: the marker, the 14 days, the lift (listed, left to a person). n28 (S4): ruling 1 settles it; it leaves.

## 5. Forbidden reads

Other repos but `from`'s records and the probes; a real NICE file or ledger from a test; the relay's state; transcripts.

## 6. Report (six lines)

Each commit; the acceptance readings; the gate's id and line; the README's bytes; the NICE rows; each choice.
