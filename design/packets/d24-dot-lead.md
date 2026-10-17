# Packet D24: a lead that opens with its level and a middle dot holds that level

| item | value |
|---|---|
| from | the agentik-hq sitting's ruling of 2026-10-17 (reversible); `design/d23-backlog-view.md` §2 and §7; `src/decisions/backlog.py` (`FORMS`, `lead_of`, `trimmed`, `lead_level`, `nice_items`); `tests/test_backlog.py`; agentik-agents' `NICE_TO_HAVE.md`, its lead shape as read on 2026-10-17; the code at 58eaf02 |
| pin | `main` at 58eaf02 plus this packet's own commit; worktree `.claude/worktrees/d24-dot-lead`, branch `d24-dot-lead` |
| wall | this repo only. No push, merge, `--amend`, rebase, device or network; no `make install` or `make readme`; no `claude` beyond `make check`'s; never build a `relay` binary or run a `relay` or `agentik relay` verb. The acceptance lines, `make doclint` and `make hygiene`, one at a time at `nice -n 10`; every python call carries `PYTHONDONTWRITEBYTECODE=1`. One `make check`, last, started only once `ps -axo command \| grep -E '(^\|/)make( \|$)' \| grep -v grep` prints nothing, and waited for |
| may touch | `src/decisions/backlog.py` (`FORMS`, its comment and `lead_level`'s docstring only), `tests/test_backlog.py` (three new tests and the module docstring's fixture list only), `tests/fixtures/backlog/agents/NICE_TO_HAVE.md` (new), `design/d23-backlog-view.md` (§2's forms sentence and §7's first list line only), `design/packets/d24-dot-lead.md`, `NICE_TO_HAVE.md` (one new section, only if the build leaves something), `history/sittings/*.md`, `history/sessions/NEXT`. Nothing else |
| acceptance | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_backlog -k lead_dot_form 2>&1 \| grep -c ' \.\.\. ok$'` reads 3 (main: 0); `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest -v tests.test_backlog -k column_zero_bullets_only -k lead_level_wins -k lead_forms_only -k token_elsewhere_is_text -k unlevelled_is_s4_marked 2>&1 \| grep -c ' \.\.\. ok$'` reads 5 (main: 5); `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m decisions backlog tests/fixtures/backlog/agents \| grep -c -E '^1 S1  NICE_TO_HAVE\.md:[0-9]+  S1 '` reads 1 (main: 0, and 0 with the fixture copied in); `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_backlog 2>&1 \| grep -c '^OK$'` reads 1 (main: 1); `grep -c -F 'five forms' src/decisions/backlog.py design/d23-backlog-view.md` reads 2 and 1 (main: 0 and 0) |
| budget | 40 turns, 180k context, `claude-opus-5-5`; two acts, one commit each; the charter opens with doclint's five rows |
| verify | `make check` |

## 1. What the source says (quoted)

- d23 §2: "The lead, trimmed of spaces and a final `.` or `,`, holds a level in four forms only: `^S[1-4]$` (`- S4: ...`), `^S[1-4],` (...), `[,;] S[1-4]$` (...) and `\(S[1-4]\)$` (`- **Rename it (S4).**`). A level named mid-lead is text". Its next line: "An unlevelled item keeps `level: null`, is placed as S4 ... never guessed higher. No item is judged landed; an item leaves its file when it lands."
- The code at 58eaf02. `FORMS` (`backlog.py:31-32`) under `:30`'s "# The four forms a lead holds a level in (section 2); anything else is text."; `lead_level` (`:127-130`) tries every form on `trimmed(lead)` (`:120-124`) and keeps the most urgent; `lead_of` (`:111-117`) gives the bold span, else the text to the first `: ` or `. `; `nice_items` tests `FORMS[0]` alone, for a bare `S4:` lead's title (`:174`).
- The finding, reproduced by the hq sitting. agentik-agents writes every item `- **S<n> · title**: ...`: `grep -cE '^- \*\*S[1-4] ·'` reads 56, of 56 items; its line 51 is `- **S1 · tests/test-apirun.py: the mid-run read races ...**`. At 58eaf02 the verb over that checkout reads 53 items `level: null` and 3 at S4 from a `## ... (S4)` heading; line 51 ranks 49 of 56, placed S4. With the fifth form: 0 null (49 S4, 6 S3, 1 S1, each from its lead), line 51 ranks 1.
- Measured in a scratch clone at 58eaf02 (load 4 to 11, 16 cores), the target simulated and reverted: the acceptance lines as the table reads; `tests/run.py` 365 OK (362 on the pin), `test_readme` warning that the README counts 362; `scripts/doclint` 0.

## 2. Rulings

Standing rules. The charter, `history/sittings/<date>-<n>-d24.md`, opens at act 1 and closes before the last commit. The repo is public: no home path, owner name or household repo name, in the fixture least of all. Act 1's first tests are red on the pin, the red line in its commit message. This repo keeps no `DECISIONS.md` (d23's opening); the packet cites d23 and the hq ruling.

1. **The fifth form**: `^S([1-4]) · ` on the trimmed lead, the level, a space, U+00B7 and a space at the lead's head, in a bold lead (`- **S3 · tests: ...**`) or a plain one (`- S3 · bin/x: ...`, the lead to the first `: `). It goes after the four, so `FORMS[0]` keeps its index and its title rule. Two forms in one lead: the most urgent wins, as now.
2. **The dot needs its spaces** (the ruling's open point, decided here): `S3·x` and `S3 ·x` are text. Every form is exact and a level is never guessed higher (§2); a glued middle dot also writes a product or a joined name (`S1·S2`), which a loose form would read as a level; and all 56 of agentik-agents' dot leads carry a space each side while `grep -c 'S[1-4]·'` reads 0 there, so the strict form takes every real lead and nothing new.
3. **What stays.** `S21 ·` is no level. A dot mid-lead or at its end is text. The title keeps its lead whole (`S3 · tests: ...`), as the other forms keep their token (round one's N4 in `NICE_TO_HAVE.md`). No item is judged landed: agentik-agents' S1 at line 51 says "answered by a-s13" and will rank first; whether an answered row stays is that file's, not this reader's.
4. **Act 1, the reading.** This packet; the fixture `tests/fixtures/backlog/agents/NICE_TO_HAVE.md`, trimmed from agentik-agents' shape, with no HANDOFF.md and no name hygiene's `renamed` group flags (that file holds two): its `#` legend heading naming S1 to S4 (depth 1, no level); bold dot leads at S1 to S4; plain ones at S1 to S4; `**S21 · ...**`, `**S3·x ...**` and a dot mid-lead; the bold S1 after the S2 to S4 leads and the three texts, the plain S1 after it; then a `## ... (S4)` section whose dot S3 beats its heading. In `Backlog`, after `test_lead_forms_only`: `test_lead_dot_form` (the eight leads and the sectioned S3, each `level_from` `lead`; one title whole), `test_lead_dot_form_exact` (the three texts read `None`), `test_lead_dot_form_ranks_first` (rank 1 is the bold S1 in `--json` and on the text's first item line; the count line as measured, `3 of 13` for the fixture above). Red first, then `FORMS`, its comment and `lead_level`'s docstring ("five forms"), and the module docstring's fixture list. One commit.
5. **Act 2, the record.** d23 §2: "four forms only" becomes "five forms only", the fifth `^S[1-4] · `, the middle dot U+00B7 between two spaces, with agentik-agents' `- **S3 · tests: ...**` as its example and `S3·x` as text (d24); §7's first line names the three tests after `test_lead_forms_only`. The charter closes. One commit.
6. **Versions and the README.** Nothing under `plugin/` changes, so the plugin stays 0.9.0 and `plugin-version-check` passes; the tool's version is one with the three manifests (`common.py`), so `pyproject.toml` stays 0.9.0. README.md and its source are untouched: the `tests/test_backlog.py` row already says "the levels", and the status count lags the suite by three, loudly, until the next `make readme` (d11, `test_readme`). A release note, as 0.5.2 was for d22, is the hq sitting's at the merge.

## 3. Interfaces (signatures, not prose)

- `FORMS` gains a fifth pattern, last: `re.compile(r"^S([1-4]) · ")` or its literal spelling.
- Test-only otherwise: the fixture and three `Backlog` methods. No new function, `--json` key, flag, exit or exported name.

## 4. Findings that name this row

- The hq sitting's reproduction (§1). No item of `NICE_TO_HAVE.md` names it.
- Failing before the fix, with the fixture in: `test_lead_dot_form` (`(None, None) != ('S1', 'lead')`) and `test_lead_dot_form_ranks_first`; `test_lead_dot_form_exact` passes on the pin and guards ruling 2.
- Adjacent, not this row: `history/sessions/INTAKE-2026-10-16-example-ops-the-level-at-a-leads-head.md`, ask 1 (a head form `^\(S[1-4]\) `) and ask 2 (a done row). The ruling changes nothing else in the reading, so both stay open there.

## 5. Forbidden reads

Any other repo: §1 quotes agentik-agents' shape, and the fixture is built from it. The relay's state directory. Transcripts.

## 6. Report (capped)

At most 150 words: each act's commit and act 1's red line; each acceptance line's reading; the exits of `make doclint` and `make check`, and `make hygiene`'s last line; each choice made inside the rulings in one sentence. Last line: branch, head sha. Fork for the owner: none.
