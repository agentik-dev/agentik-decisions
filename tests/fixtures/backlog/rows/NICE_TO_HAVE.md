# Nice to have

Trimmed for d26: design/05 section 2's rows beside the bullets. The archive is `history/nice-archive.md`.

## Doctor

- S3: a bullet before the table, in `plugin/lib/tool/doctor.py`

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n1 | S2 | `plugin/lib/tool/doctor.py` | **The hint names make install**: it should name install-cli | `doctor.py:40` | 2026-11-01, d25 |
| n2 | S4? | doctor | An unsure level cell. It reads unlevelled | not confirmed | 2026-11-01 |
| n3 | s3 | doctor | A lower-case level is text | not confirmed | 2026-11-01 |
| n4 | S3 | `scripts/doclint` | A cell holding `a \| b` keeps its pipe. It names `plugin/lib/tool/backlog.py` | the `tests/fixtures/x.md` repro | 2026-11-01 |
| n5 |  | doctor | An empty level cell. S1 in the finding is text | `README.md:3` | 2026-11-01 |

- S1: a bullet after the table, its level from the lead

## Other tables

| rank | work | state |
|---|---|---|
| 1 | Another header yields nothing | open |

| id | level | area | finding | evidence |
|---|---|---|---|---|
| n8 | S1 | doctor | Five columns is another header | none |

| id | level | area | finding | evidence | from |
| n9 | S1 | doctor | No separator line, so no table | none | 2026-11-01 |

```
| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n10 | S1 | doctor | A fenced row is no item | none | 2026-11-01 |
```

## S2 over these rows

Each line is S1.

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n6 | S4 | `design/d23-backlog-view.md` | A row's level is its cell's | agentik-hq design/05 | 2026-11-01 |
| n7 | S9 | doctor | A row takes no level from the heading or the sentence | none | 2026-11-01 |

- A bullet after the rows takes the sentence's level
