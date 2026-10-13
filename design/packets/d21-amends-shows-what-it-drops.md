# Packet D21: `answer --amends` shows what it replaces, and refuses a paragraph cut by half

| item | value |
|---|---|
| from | the observer's sighting of 2026-10-08 in §1; `src/decisions/answer.py` (`amend_entry`, `cmd_answer`); the `--amends` wording in `plugin/skills/ask/SKILL.md`, `plugin/skills/decisions/SKILL.md` and `plugin/commands/answer.md` |
| pin | this repo's `main` at the commit that lands this packet; worktree `.claude/worktrees/d21`, branch `d21` |
| wall | this repo only. No push, `--amend`, rebase, device or network. No `make check` and no `make install`: a relay night may be live, so run only the test modules named here, `make doclint` and `make hygiene`. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never run or build a `relay` binary, and never run any `relay` verb |
| may touch | `src/decisions/answer.py`, `src/decisions/cli.py` (the flag only), `tests/test_answer.py`, `tests/test_cli.py` only if a usage string is asserted there, the three plugin files named in `from`, `design/readme/source.md` with `make readme` if it states `--amends`, `NICE_TO_HAVE.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_answer -k amend 2>&1 \| grep -c ' \.\.\. ok$'` reads 6 or more; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_answer tests.test_cli tests.test_plugin 2>&1 \| tail -1` reads `OK`; `PYTHONDONTWRITEBYTECODE=1 make doclint hygiene` exits 0; `grep -c 'whole paragraph' plugin/skills/ask/SKILL.md` reads 1 or more |
| budget | 40 turns, `claude-opus-5-5`; one commit per act |
| verify | the observer runs `make check` before the merge, once no relay verb is live |

## 1. What the source says (quoted)

- `answer.py`'s docstring: "`--amends M` replaces entry M's paragraph and adds to its tail an amendment". `ask/SKILL.md`: "`--text` is the entry's paragraph. … `--amends M` replaces the paragraph of entry M".
- The sighting (example-app, 2026-10-08, commit 9ccbf00d): a session ran `answer 59 --amends 29 --text <two new sentences>`. Entry 29's line went from 2,267 bytes to 801. Its whole body in force was gone, and the run printed only "entry 29 amended". The session found it an hour later and repaired it by hand (182b6983). The verb did what it documents; nothing told the caller what it dropped.

## 2. Rulings

1. `--text` with `--amends M` is the whole paragraph in force after the answer: every sentence that stays, with the change made. The three plugin files say so in those words ("the whole paragraph").
2. On success, `answer --amends M` prints, after its done line, one line `replaced: <the old paragraph>`: the body between the bold title and the tail, as it stood.
3. When the new paragraph is under half the old paragraph's length (characters, after `ask.clean`), `answer --amends M` refuses with exit 2 and writes nothing. The refusal names both lengths, prints the old paragraph on its own line so the caller can copy it, and names `--shorter`.
4. `--shorter` lets that paragraph through; it is valid only with `--amends` (otherwise exit 2, nothing written). Rulings 2 and 4 hold together: a `--shorter` run still prints `replaced:`.
5. Nothing else in `answer` changes: the tail, the earlier amendments (D19), the question's removal and the CLAUDE.md block stay as they are.

## 3. Interfaces (signatures, not prose)

- `amend_entry(text, ledger, number, paragraph, amendment, shorter=False) -> (new_text, old_paragraph)`
- `answer N … --amends M [--shorter]`

## 4. Findings that name this row

- The sighting in §1. Tests, each failing before the fix: a delta paragraph under half the old one refuses and leaves both files byte-identical; the same with `--shorter` writes and prints `replaced:`; a whole paragraph writes and prints `replaced:` with the old body; `--shorter` without `--amends` refuses. Existing amend tests whose fixture paragraphs fall under the half rule pass `--shorter` or lengthen their `--text`; say which in the commit.

## 5. Forbidden reads

Any other repo. `~/.local/state/agent-relay`. Transcripts.

## 6. Report (capped)

At most 150 words: each act's commit, each acceptance line with its reading, and any choice made inside the rulings, one sentence each.
