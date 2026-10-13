# Packet D22: `answer --text` is the body only; the lint sees a doubled title or tail

| item | value |
|---|---|
| from | `NICE_TO_HAVE.md`'s items of 2026-10-09 (D21's README text) and 2026-10-10 (§1); `answer.py` (`cmd_answer`, `amend_entry`); `ledger.py` (`check_entry`) |
| pin | this repo's `main` at the commit that lands this packet; worktree `.claude/worktrees/d22`, branch `d22` |
| wall | this repo only. No push, `--amend`, rebase, device or network. No `make check`, `make install` or `make readme`: a relay night may be live; run only the test modules named here, `make doclint` and `make hygiene`. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never build a `relay` binary or run a `relay` verb |
| may touch | `src/decisions/answer.py`, `src/decisions/ledger.py`, `src/decisions/cli.py` (help only), `tests/test_answer.py`, `tests/test_ledger.py`, `plugin/skills/ask/SKILL.md`, `plugin/skills/decisions/SKILL.md`, `plugin/commands/answer.md`, `design/readme/source.md`, `NICE_TO_HAVE.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_answer tests.test_ledger -k body_only -k twice 2>&1 \| grep -c ' \.\.\. ok$'` reads 4 or more; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_answer tests.test_ledger tests.test_render tests.test_cli tests.test_plugin 2>&1 \| tail -1` reads `OK`; `PYTHONDONTWRITEBYTECODE=1 make doclint hygiene` exits 0; `grep -c 'body only' plugin/skills/ask/SKILL.md plugin/commands/answer.md src/decisions/cli.py` reads 1 or more for each |
| budget | 40 turns, `claude-opus-5-5`; one commit per act |
| verify | the observer runs `make readme` and `make check` before the merge, once no relay verb is live |

## 1. What the source says (quoted)

- `cli.py`, `ask/SKILL.md`, `commands/answer.md`: `--text` is "the entry's paragraph". `cmd_answer` writes `"%d. **%s.** %s (%s; %s)"`; `amend_entry` writes `"%d. **%s** %s (%s; amended %s)"` with M's title and tail.
- The sighting (the observer, 2026-10-10): two real entries given a ledger-shaped line as `--text` came out with the bold title and the `(date; source)` tail twice; `render --lint` passed both.

## 2. Rulings

1. `--text` is the body only in both modes; `answer` writes the title and the tail. A new entry is `N. **<question title>.** P (<date>; the owner's answer to decision N, S)`. With `--amends M` it keeps M's title and whole tail, writing `M. **<M's title>** P (<M's tail>; amended <date>, …)`; P is then the whole body in force after the answer (D21's "whole paragraph").
2. When an entry is written, `answer` refuses before the lock (exit 2, nothing written) a `--text` that after `ask.clean` opens with a bold span (`**` or `N. **`) or ends in a parenthetical opening with a date then `;` or `,` and a source (`questions.TAIL.match`). The refusal names the part and says `--text` is the body only. `--no-entry` ignores `--text`, as now.
3. Only the body's start and end count: a dated parenthetical before a final period, or a later `**`, passes.
4. `render --lint` reads each entry in force or proposed alike, over its body between title and final tail: `entry N: its bold title appears twice`, `entry N: its (date; source) tail appears twice`. One function serves both.
5. The help and the three plugin pages say `--text` is the body only. `design/readme/source.md`: the `answer` row gains `[--shorter]` after `--amends M`; the `--amends M` sentence says `--text` is the whole paragraph in force, the old one prints as `replaced:`, and one under half its length is refused unless `--shorter`; one line says `--text` is the body only; the lint names ruling 4.
6. D21 stands: its tests pass unchanged.

## 3. Interfaces (signatures, not prose)

- `ledger.repeats(body) -> list` of `"title"`, `"tail"`, in order; `[]` for none.
- `answer N … --text P` refuses as ruling 2.

## 4. Findings that name this row

- §1's sighting; D21's README text. Failing before the fix: `test_body_only_refuses_a_title` (`**T.** P` and `9. **T.** P`: exit 2, both files byte-identical), `test_body_only_refuses_a_tail` (`P (2026-09-28; s)`, with `--area` and `--amends 3`), `test_a_title_or_tail_twice` (the lint names each part). `test_body_only_passes_inner_parts` guards ruling 3.

## 5. Forbidden reads

Any other repo. The relay's state directory. Transcripts.

## 6. Report (capped)

At most 150 words: each act's commit, each acceptance line's reading, and each choice made inside the rulings in one sentence.
