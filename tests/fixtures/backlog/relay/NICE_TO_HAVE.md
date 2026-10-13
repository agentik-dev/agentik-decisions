---
status: current
updated: 2026-10-11
audience: agent
---
# agent-relay: what a review or a packet left open, none of it blocking

Nothing here blocks a review or a merge. An S1 in prose is text.

## AR70 landed (2026-10-11): what its build left open
- Ruling 9's first edge: a kill landing after the child's exit but before `RunRow` reads its cause reads as the pause's kill.
  A continuation line belongs to the item.
  - A nested bullet is not an item, S1.
- A paused row with no outcome out and no held stage at the wake now reads as a bug (`ErrBug`).

```text
- a fenced line is not an item
```

## AR70 rounds one and two (2026-10-11): notes, no block, S4 (F1, a held line on a running night, fixed at e08f389)
- If the night is draining after the wake, the stop loses 2a504c2's detail "the night is draining". (round two N3)
- Under a bug, the landing's `stepSitting` (night.go:1141) skips `setRow`. (round one, design N2)

### A subheading under the levelled heading
- The `fresh` gate on the probe (night.go:1123) is named by no ruling. (regressions N1)

## `relay plan` stamps its lines with a night it does not own (2026-10-11, the observer; S4)
- A plain `relay plan` names itself the next night (`NightName`, cmd/relay/main.go:528).

## The attendant runs out of turns on a check-in
- `plugin/agents/attendant.md` keeps `maxTurns: 20` with no report bound.
