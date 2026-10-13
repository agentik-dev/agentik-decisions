---
status: current
updated: 2026-09-28
audience: agent
---
# sample: what is settled

A sample ledger for the tests: two entries every session reads, three areas, one proposal and two superseded lines.

## In force

### Every session

1. **Plain words.** Every entry reads as plain present-tense English. (2026-09-01; the sample)

2. **Small ledgers.** A ledger holds at most 25 entries in force. (2026-09-02; the sample)

### Build

3. **One interpreter.** The tool runs under Python 3.12 from the standard library alone. (2026-09-03; the sample, amended 2026-09-10 (twice))

4. **Tests first.** Every verb has its own tests. (2026-09-04; the sample)

### Build tools

5. **Make is the gate.** `make check` runs every gate. (2026-09-05; the sample)

### Release

7. **Releases follow the manifest.** A release name equals the manifest version. (2026-09-07; the sample)

## Proposed

8. **A second interpreter.** The tool also runs under Python 3.13. (proposed 2026-09-08; OPEN-QUESTIONS.md)

## Superseded

- Entries as separate files: replaced by one ledger (entry 2), 2026-09-02.
6. The old gate named by hand: replaced by make (entry 5), 2026-09-05.
