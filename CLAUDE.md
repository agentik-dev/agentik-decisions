---
status: current
updated: 2026-11-11
audience: agent
---
# agentik-decisions: agent contract

A Claude Code plugin, `decisions@agentik`, and a stdlib Python tool, `agentik-decisions` (run as `agentik decisions`), that serve one sectioned DECISIONS.md per repo with six verbs: `show`, `find`, `new`, `ask`, `answer` and `render`, plus `doctor`, `backlog`, `expire`, `analyze` and `audit`. The current design is `design/d18-one-flow.md`; later packets are in `design/packets/`, older ones in `history/`.

- **Read order:** `README.md`, then `design/d18-one-flow.md`, then the newest `history/sittings/*.md`.
- **The ledger:** `## In force` (`### Every session` first, then `### <area>`), `## Proposed`, `## Superseded`. An entry in force is one line, `N. **Title.** paragraph (date; source)`. Numbers are unique and never reused. `agentik decisions render --lint` checks the shape, the caps on entries and the OPEN-QUESTIONS.md beside the ledger; the line `<!-- decisions: legacy below -->` ends the parsed part of an older ledger.
- **The tool:** stdlib Python under the pyenv virtualenv `agentik-decisions` (3.12.7, named in `.python-version`), one package in `plugin/lib/decisions/`, no dependencies, tested with `unittest`. Run it from the checkout as `PYTHONPATH=plugin/lib python -m decisions`; `make install` runs the launcher's `install-cli`, and the vendored `agentik` front door beside it. The plugin comes from agentik-commons' `agentik` marketplace; this repo keeps none.
- **The plugin** carries two skills, `decisions` and `ask`, nine commands and respeak's include file, and no data: a repo owns its ledger.
- **How to write:** `plugin/respeak-include.md`, imported below, is rendered by respeak's `/respeak:include write --out plugin/respeak-include.md` and checked with `check --out`; a hand edit is lost at the next render. respeak stays optional: users get the file without it.
- **Checks:** `make check` runs gates, test, lint, doclint, hygiene, validate and the `decisions` step, then the README's freshness. Edit `design/readme/source.md`, never `README.md`; `make readme` renders it. `scripts/{agentik,hygiene,bounded}` are agentik-commons' copies, checked against `scripts/vendored.sha256`: refresh them with its `scripts/sync`, since a hand edit fails that check.
- **Authority:** this repo keeps no DECISIONS.md; the suite's management ledger binds it, entries 6 to 9.

@plugin/respeak-include.md
