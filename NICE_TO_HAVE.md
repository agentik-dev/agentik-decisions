# agentik-decisions: what a review left open, none of it blocking

The findings a review left that block nothing, one row each in agentik-hq design/05 §2's table; a row leaves when it lands. The bullets before 2026-11-01 are frozen in `history/NICE-2026-11-01.md`, never edited: its S4 and unlevelled items stay there, and a packet touching an area greps them by path. Of its S1 to S3 items, one is open on main and is row n1; the other, the uv `Executable already exists` stop of `make install`, closed with d25, whose recipe runs `install-cli` (`Makefile:113-116`).

## Open findings

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n1 | S3 | `tests/gates.py` | The gates' pyflakes and 3.12-syntax passes walk only src and tests, so since d25 they miss `plugin/lib`; put `plugin/lib` in `ROOTS`, drop the shebang check of `src/decisions.py`, then remove that checkout runner | `tests/gates.py:16`, `:45-46`, `:94` | 2026-11-01, d25; `history/NICE-2026-11-01.md:77` |
