# Packet d32: the block is loaded on every turn

| item | value |
|---|---|
| from | the owner's ask of 2026-11-09 that the tool stop the block's silent growth; the hq sitting's rulings; hq entries 9 and 17. This repo keeps no ledger: no entry is carried |
| pin | agentik-decisions main de67e4e, plugin 0.15.1, 435 cases; worktree `.claude/worktrees/d32-block-growth`, branch `d32-block-growth` off that main; line numbers are de67e4e's |
| wall | this worktree only; no push, `--amend`, rebase, merge, `make install` or `install-cli`; no bare `make`, no `make` outside the gate queue, no `make readme` (it runs `claude`); never build a relay binary, run a `relay` or `agentik relay` verb, or write in the relay's state directory; no write outside the worktree; no test writes under the live home; `render --fold-tails` only in a throwaway repo; python runs with `PYTHONDONTWRITEBYTECODE=1` |
| may touch | `plugin/lib/decisions/{answer,render,analyze,cli,common}.py` (`common`: `VERSION` only); `tests/test_{answer,render,analyze,plugin}.py`; `tests/test_lookup.py:159` (ruled 22:10); `plugin/commands/{answer,render,analyze}.md`, `plugin/skills/ask/SKILL.md`; `README.md`, `design/readme/{source.md,rendered.sha256}`; `plugin/.claude-plugin/plugin.json`, `pyproject.toml`; `CLAUDE.md`; `NICE_TO_HAVE.md`; this packet as `design/packets/d32-block-growth.md`; a charter |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=plugin/lib python3 -m unittest -v tests.test_answer tests.test_render tests.test_analyze -k test_every_turn_ 2>&1 \| grep -c ' \.\.\. ok$'` reads 7 (de67e4e: 0); the same under `/usr/bin/python3` (3.9.6); `scripts/plugin-version-check` exits 0; `cmp README.md design/readme/source.md` exits 0 |
| verify | `agentik session gate run <absolute worktree path> -- /bin/sh -c 'make check > <scratch log> 2>&1'`, then `agentik session gate wait <id>` in one background Bash, last; it exits 0 whatever the job's code: read the code from its line |
| budget | 80 tool calls or 120k context, `claude-opus-5-5`; one commit per group by explicit path, the packet and the charter first; at either ceiling, a resume line in the charter and stop |

## 1. What the source says: the evidence

Each re-run on de67e4e. P is agentik-hq `history/sessions/PACKET-2026-11-09-decisions-d32-probes/`.

- `bash -eu P/repro.sh <checkout>`: the sample ledger rendered into a CLAUDE.md, `block 539 B`; then `answer 8 --pick Both --source S --amends 1 --add "<92 B>"` prints `entry 1 amended`, `tail was:`, `answer: rewrote the block in …/CLAUDE.md`, exit 0, `block 661 B`; `render --lint` prints nothing, exit 0. Of the 122 B, 30 are the tail note `; amended once, see the ledger` (`render.py:42-53`).
- `answer` renders the block after both files are written (`answer.py:314`, `:320`), into a target with markers only (`:333-344`); its line `:344` names no size, nor `render.py:226`; `--lint` returns at `:195` before a target is named.
- `analyze <repo> --json`, a repo's keys: `charters` … `vendor`, ten (`analyze.py:286-290`): no block.
- `sed -n '/BEGIN GENERATED: decisions/,/END GENERATED: decisions/p' <file> | wc -c`: `~/.claude/CLAUDE.md` 4917, agentik-hq 1517, two other hq repos 3048 and 6031.

## 2. Rulings

1. **Growth shown.** `render.block_bytes(text)`: the bytes of the one block, both marker lines included, else None. `render.growth(old, new)`: `X B to Y B, +D B; the block is loaded on every turn`, no block 0 B, `%+d`. `render` writes `render: wrote <target>: <growth>` (the fold too); `answer` writes `answer: rewrote the block in <target>: <growth>`. `is fresh` and `--check` change nothing and say nothing new.
2. **Growth under Every session refused.** Grounding: `answer` writes its block only after the commit and only into a target with markers, so "larger" is a dry render. Under the lock, after the lint and before `add_answered` (`:302`): when the answer touches Every session, `--amends M` with M in force there (by `--text` or `--add`) or an `--area` that resolves to it (`heading`, `:299`), compare `block(parse(ledger_text), path, target)` with `block(parse(new_ledger), path, target)`, markers or none, since the relay puts the same block in each child's prompt (hq entry 9). Larger without `--every-turn`: exit 2, `answer: this answer adds D B to the block, X B to Y B, which is loaded on every turn; put it in an entry outside `Every session`, which the block lists by title only, or pass --every-turn; nothing written`. Same size or smaller passes. An entry elsewhere grows the block by its title line: shown, never refused. `--every-turn` with `--no-entry`: exit 2, `--every-turn is valid only with --area or --amends`. Growth is the whole block's: the tail note adds 30 B at an entry's first amendment and 3 B at its second, so a same-length reword of an entry never amended is refused. The orchestrator's ruling on that fork (21:42): it stays the whole block's, since the tail is paid every turn too; and when the entry's rendered tail grows by T B with the answer, T above 0, the refusal says so before `; nothing written`: `; T B of it is the entry's tail note`. T1 gains the case: a same-length `--text` on an entry never amended, exit 2, the message holding `30 B of it is the entry's tail note`.
3. **The measure.** `render --lint`, clean, prints one line, `render: the block for <target> is N B; it is loaded on every turn`, N the block `render` would write there (`--into` honoured); a lint problem prints no size. `analyze` gives each repo read `block: {start, end}`, the CLAUDE.md block's bytes at the first-parent commit at or before `since`, and `until` (`rev-list`, `show`), null without a commit, file or block; text: `block  X B to Y B, +D B` after the `==` line, `-` for a null end (no D), no line when both are.
4. **No cap.** No byte limit is set or linted; the number is the owner's.
5. **Texts.** `cli.py`: the usage `:16-17` gains `[--every-turn]`, the flag after `--shorter` (`:148`). The docstrings of `answer.py`, `render.py`, `analyze.py`. README and source, alike, by hand, under the 24,576 B cap (6 B free at de67e4e; the room from `:288`'s `0.8.0` note): `:82`'s usage, `:84` and `:88` restated, a sentence after `:153` naming the refusal and its way out. `answer.md` (under 30 lines; 27 now), `render.md`, `analyze.md`; the ask skill's `:29` usage and by `:51`: `--every-turn` only on the owner's word. hq entry 9's verbs stand: a flag, no verb.
6. **Version 0.16.0**, last, where a5ea745 and 1298da5 bumped: `common.py`'s `VERSION`, `plugin.json`, `pyproject.toml`, `tests/test_plugin.py`'s `VERSION`, README's `--version` row and status line `:278` (the case count), `source.md`, `rendered.sha256`. `CLAUDE.md` line 8 names d29's 0.14.0 as its newest; it gains d31 (`design/packets/d31-backlog-tails.md`, T2 and `--fold-tails`, 0.15.0) and this packet (0.16.0), and `updated:` the date. `NICE_TO_HAVE.md` gains n28, S4, `backlog.py`: "`(closed <date>)` inside a lead stays an item", d31 ruling 2's, never filed. The marketplace line is hq's.

Reversible, the cutter's: the flag's name; `--lint`'s line on stdout.

## 3. Interfaces

`answer … [--every-turn] [--into PATH]`; `render.block_bytes(text)`, int or None; `render.growth(old, new)`, a str; `analyze.block_at(top, head, at)`, int or None. `P/prototype.patch` is a sketch.

## 4. Findings that name this row

(Copy: §1, §4 cut for doclint; whole in agentik-hq.)

0 of 7 ok on de67e4e, 7 on the scratch prototype under 3.12.7 and 3.9.6 (`P/test_d32.py`, its classes split into the three files).

| T | test (`test_every_turn_`…) | red at de67e4e |
|---|---|---|
| 1 | answer: `amends_refuses_growth` (`--add`, a longer `--text`: exit 2, three files byte-identical; `--every-turn`: exit 0, D as refused) | exit 0, not 2 |
| 2 | answer: `area_refuses_growth` (either case of the name; with no CLAUDE.md too; `--area Build` passes, +31 B) | exit 0, not 2 |
| 3 | answer: `same_or_smaller_passes` (a `--shorter` trim prints a minus; a same-length reword at the third amendment, `+0 B`) | usage, exit 2 |
| 4 | answer: `flag_needs_an_entry` | usage |
| 5 | render: `render_prints_bytes` (`0 B to 539 B, +539 B`; a longer entry 1; fresh: no ` B to `) | no size |
| 6 | render: `lint_prints_size` (beside, `--into`; a lint failure: none) | no line |
| 7 | analyze: `analyze_measures_the_block` (JSON both ends, null for a repo without; one text line) | `KeyError: 'block'` |

Today's tests that change, 12, red on the prototype: `test_answer.py`'s seven pass `--every-turn` (`:268`, `:325`, `:372`, `:747`, `:757`, `:772`, the T2 helper `:905`); in `test_render.py` four pin `--lint` silent (`:240`, `:400`, `:455`, `:463`) and read the size line; `test_analyze.py:240` gains `block`. The charter shows the seven red first.

## 5. Forbidden reads

Any other repo, but agentik-hq's DECISIONS.md entries 9 and 17, this packet's probes, and agentik-research's survey (`research/synthesis/tools-decisions.md` §1.5, §2.3). The relay's state directory. Transcripts.

## 6. Report (at most six lines)

Each commit; each acceptance reading; the gate's id and line; the README's bytes; n28; each choice, one sentence.
