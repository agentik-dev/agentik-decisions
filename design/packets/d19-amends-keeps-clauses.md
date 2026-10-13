# Packet D19: `answer --amends` keeps the entry's earlier amendments

| item | value |
|---|---|
| from | `design/d18-one-flow.md` §`answer` (the `--amends M` line and the entry shape); `NICE_TO_HAVE.md` lines "d18 1a obs (1b obs)" and "d18 2a F6"; the sighting in §1 |
| pin | this repo's `main` at the commit that lands this packet; worktree `.claude/worktrees/d19`, branch `d19` |
| wall | this repo only. No push, `--amend`, rebase, device or network. No `make check` and no `make install`: a relay night may be live, so run only the test modules named here. Every python call carries `PYTHONDONTWRITEBYTECODE=1`. Never run or build a `relay` binary |
| may touch | `src/decisions/answer.py`, `tests/test_answer.py`, `design/d18-one-flow.md` (the two lines §2 names), `design/readme/source.md` only if it states the old rule, `NICE_TO_HAVE.md` |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest -v tests.test_answer -k amends 2>&1 \| grep -c ' \.\.\. ok$'` reads 2 or more and `grep -c 'FAIL\|ERROR'` over the same output reads 0; `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest tests.test_answer tests.test_render 2>&1 \| tail -1` reads `OK`; `grep -c 'split("; amended"' src/decisions/answer.py` reads 0 |
| budget | 40 turns, `claude-opus-5-5`; one commit per act |
| verify | the observer runs `make check` before the merge, once no relay verb is live |

## 1. What the source says (quoted)
- d18: "`--amends M` replaces the paragraph of entry M, which is in force, with P. The tail of M keeps its text before the first `; amended` and gains `; amended DATE, the owner's answer to decision N, S`."
- `answer.py` line 66: `base = tail.split("; amended", 1)[0]`.
- The sighting, a consumer's ledger on 2026-10-02 at 05:27: entry 9 carried `; amended 2026-10-01, the owner's answer to decision 31, <a charter>`. Answering decision 35 with `--amends 9` dropped that clause, and the sitting put it back by hand. The entry now reads `…; amended 2026-10-01, the owner's answer to decision 31, …; amended 2026-10-02, the owner's answer to decision 35, …`, and its lint passes.

## 2. Rulings
1. `--amends M` keeps the whole tail of M and appends the new `; amended DATE, the owner's answer to decision N, S`. An earlier amendment names an owner's answer that the paragraph still rests on, so the tool never drops one. (the observer, 2026-10-02; a reversible choice under entry 15)
2. `amend_entry` no longer splits the tail. This closes "d18 2a F6" (the split inside a nested parenthetical) as a side effect; say so in `NICE_TO_HAVE.md` by removing that line and the "d18 1a obs (1b obs)" line.
3. `test_amends_keeps_latest_amendment` is renamed `test_amends_keeps_earlier_amendments` and expects both clauses after two amendments, in order, and that the lint passes. Add one test for the nested case: a tail holding `(twice); amended` inside a parenthetical stays balanced after an amend.
4. The design's two lines change to match: the `--amends M` line says the tail is kept whole, and the shape line reads `(YYYY-MM-DD; source[; amended YYYY-MM-DD, source]…)`.
5. Out of scope: "d18 2a F7" (an entry with no tail), the lint's reading of dates, and anything in `ask`, `new` or `render`.

## 3. Interfaces (signatures, not prose)
`amend_entry(text, ledger, number, paragraph, amendment) -> str`, unchanged; its docstring says the tail gains `amendment` after what it holds.

## 4. Findings that name this row
None open.

## 5. Forbidden reads
Transcripts, `~/.local/state`, and any repo but this one.

## 6. Report (capped)
At most 150 words: the commits, the acceptance numbers as measured, the test that failed before the fix (run it on `main`'s `answer.py` first and quote its failure line), and anything left.
