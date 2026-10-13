---
status: current
updated: 2026-10-11
audience: agent
---
# agentik-decisions: agent contract

A Claude Code plugin, `decisions@agentik`, and a stdlib Python tool, `agentik-decisions` (run as `agentik decisions`; the old name `decisions` is its alias until 2026-12-31), that serve one sectioned DECISIONS.md per repo with six verbs: `show`, `find`, `new`, `ask`, `answer` and `render`, plus `doctor` and `backlog`. The design is example-mac DECISIONS.md entry 4; `design/d23-backlog-view.md` adds `backlog` in 0.5.0; the design for 0.4.0 is `design/d18-one-flow.md`, built by `design/packets/d18-one-flow.md`; `design/d17-four-verbs.md` built 0.3.0, and the older designs and packets sit in `history/`.

- **Read order:** `README.md`, then `design/d18-one-flow.md`, then the newest `history/sittings/*.md`.
- **The ledger:** `## In force` (`### Every session` first, then `### <area>`), `## Proposed`, `## Superseded`. An entry in force is one line, `N. **Title.** paragraph (date; source)`. Numbers are unique and never reused; at most 25 are in force and 7 sit under `Every session`. `agentik decisions render --lint` checks the shape and the OPEN-QUESTIONS.md beside the ledger; the line `<!-- decisions: legacy below -->` ends the parsed part of an older ledger.
- **The tool:** stdlib Python under the pyenv virtualenv `agentik-decisions` (3.12.7, the first line of `.python-version`; pyenv takes its second while the first is absent), one package in `src/decisions/`, no dependencies, tested with `unittest`. Run it from the checkout as `PYTHONPATH=src python -m decisions`; `make install` installs it with `uv tool install`, and the vendored `agentik` front door beside it. The plugin comes from agentik-commons' `agentik` marketplace; this repo keeps none.
- **The plugin** carries two skills, `decisions` and `ask`, six commands and respeak's include file, and no data: a repo owns its ledger.
- **How to write:** `plugin/respeak-include.md`, imported below, is rendered by the author with respeak's `/respeak:include write --out plugin/respeak-include.md` and checked with `check --out`; never edit it by hand. respeak stays optional: users get the file without it.
- **Checks:** `make check` runs gates, test, lint, doclint, hygiene, validate and the `decisions` step, then the README's freshness. Edit `design/readme/source.md`, never `README.md`; `make readme` renders it. `scripts/{agentik,hygiene,bounded}` are agentik-commons' copies, checked against `scripts/vendored.sha256`: refresh them with its `scripts/sync`, never by hand.
- **Sittings:** example-mac `docs/session-budget.md`; a charter under 4 KB in `history/sittings/` at open.
- **Authority:** this repo keeps no DECISIONS.md; example-mac entries 4 and 15 bind it. A builder decides inside the packet and escalates only a fork the packet cannot settle.

@plugin/respeak-include.md
