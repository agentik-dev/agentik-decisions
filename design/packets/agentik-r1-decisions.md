# Packet agentik-r1-decisions: `agentik-decisions`, the `decisions@agentik` plugin, no own marketplace

| item | value |
|---|---|
| from | agentik-commons `design/agentik-r1.md` §4.1, §4.3, §5.1–§5.3, §6.1, §6.2 (this repo's row), §6.3 (c1 c4 c7 c9 c10), §8.1–§8.2, §10 (D3); step 0 landed in the owner's ledger (2026-10-13). The builder reads THIS packet, those sections and §5; nothing else |
| pin | `main` at `80d59eb` or later; agentik-commons `main` after agentik-r1-commons merges; branch and worktree `agentik-r1-decisions`, off main |
| wall | this repo only; agentik-commons read-only (its `scripts/sync` writes here). No push, `--amend`, rebase, network. Merged without installing (§8.1 step 2): no `make install`, `uv tool install` or `make venv`; no `claude plugin` command but `make check`'s `validate`. Never write in `~/.local/state` or `~/.config`, read a transcript, or build or run a relay binary or verb. Python calls carry `PYTHONDONTWRITEBYTECODE=1` |
| may touch | `pyproject.toml`, `.python-version`, `.gitignore`, `Makefile`, `CLAUDE.md`, `.hygiene-allow`, `src/decisions/*.py`, `plugin/commands/*.md`, `plugin/skills/*/SKILL.md`, `tests/**`, `history/sessions/PROMPT-*` (the 4 live briefs), `design/readme/source.md` then `make readme` (README.md and its sidecar), `scripts/{agentik,hygiene,bounded,vendored.sha256}` by sync only, `NICE_TO_HAVE.md`; delete `.claude-plugin/marketplace.json`. Under `design/`, only this packet's §6 report |
| acceptance | `test -e .claude-plugin/marketplace.json; echo $?` reads `1`; `grep -c '^agentik-decisions = ' pyproject.toml` reads `1`; `head -1 .python-version` reads `agentik-decisions` |
| budget | 100 turns, 150k context; commit per act; checkpoint at 80% |
| verify | `make check` |

## 1. What the source says

- **§4.1, §4.3.** The tool is `agentik-decisions` (dist renamed, `uv tool install .`); `decisions` stays as a second entry point until 2026-12-31. Verbs stay. Under the old name, with stderr a terminal, one stderr line `decisions: renamed; use 'agentik decisions …' (ends 2026-12-31)`; pipes see nothing. render's block wording (`render.py:58–59`) stays until r2.
- **§5.1–§5.2.** The plugin becomes `decisions@agentik`, namespace unchanged; plugin code calls the dash name; `allowed-tools` becomes `Bash(agentik-decisions *)`. This repo's `marketplace.json` is deleted.
- **§6.3.** c1: the session state folder `claude-code-session` → `agentik-session` (`doctor.py:213`). c4: `.claude/claude-code-session/` → `.claude/agentik/` (`.gitignore:8`). c7: plugin IDs → `decisions@agentik`, doctor accepts both and warns (`doctor.py:37–38`). c9: dist → `agentik-decisions`, fallback the `decisions` entry point. c10: venvs `claude-code-{decisions,respeak}` → `agentik-*` (`.python-version`, `Makefile:99–103,123`), fallback `pyenv prefix new || old`.
- **§6.2, this row.** (a) `CLAUDE.md`, `tests/fixtures/backlog/*`; (b) `mkt.json`, `README.md`, `pyproject.toml`, 4 PROMPT-*; (c) as above; tests `test_doctor`, `test_hermetic`, `test_readme`.
- **§8.2, D3.** Vendor `scripts/{agentik,hygiene,bounded}` by commons' `scripts/sync`; `renamed` reads 0. Fails before: `agentik-decisions --version` runs. The install also installs the vendored `agentik`.

**Live hits today** (lines per file). Clear 27: `marketplace.json` 2, `.gitignore` 1, `CLAUDE.md` 3, `README.md` 9, PROMPT-* 2/3/4/10, `plugin/commands/*` 8, `skills/ask` 8, `skills/decisions` 12, `pyproject.toml` 1, `src/decisions/{answer,cli,selector}` 4, `tests/fixtures/backlog/*` 4, `tests/{test_answer,test_ask,test_backlog,test_plugin,test_hermetic}` 14. Allow 11 (ruling 9): `Makefile` 8, `.python-version` 1, `scripts/{doclint,readme-render}` 2, `src/decisions/{doctor,render}` 5, `tests/{test_doclint,test_doctor,test_hygiene,test_readme,test_render}` 19. Plus 15 charters (ruling 10).

## 2. Rulings (decided inside the record, one sentence each)

1. A c-item reader takes the new path when it exists, else the old one when it exists, else the new; a writer writes where its reader resolved.
2. `.python-version` holds two lines, `agentik-decisions` then `claude-code-decisions`, so pyenv takes the first that exists (c10's `new || old`); `make venv` creates the new one at the switch, and `RESPEAK_PYTHON` tries `agentik-respeak` then `claude-code-respeak`.
3. `.gitignore` ignores `.claude/*/config.local.yaml`, which covers both c4 folders and names neither.
4. No version bump in r1: `0.8.0` stays everywhere, so commons' marketplace entry stays true; r2 bumps the major (§8.6).
5. `--version` prints `agentik-decisions 0.8.0` under either name; argparse's `prog` and every command the tool prints for a person (answer's warning, selector's hint) use the front-door form `agentik decisions …`.
6. The note fires when `basename(argv[0]) == "decisions"` and `sys.stderr.isatty()`, before parsing, so `--version` and errors keep their exits.
7. The `marketplace` target goes; `validate` runs `claude plugin validate plugin/` only; `install` runs `uv tool install .` then `install -m 755 scripts/agentik $(BINDIR)/agentik`, `BINDIR ?= $(HOME)/.local/bin`.
8. `hygiene` checks `shasum -a 256 -c --status scripts/vendored.sha256` in place of `HYGIENE_SHA`; `DOCLINT_SHA` stays (doclint is not vendored in r1); `test_hygiene.py` only swaps its expected exits (1 hit, 2 usage).
9. Each allowed file gets one row `<path>: renamed  # <reason>`: §6.1's exceptions (hygiene, doclint, readme-render, their tests, test_readme's reject list), render's wording (render.py, test_render.py), the c1/c7/c9 fallbacks (doctor.py, test_doctor.py), the c10 fallback (`.python-version`, `Makefile`); old names in their comments still go.
10. `history/sittings/*: renamed  # per-packet records (§5.3)`, since commons' newest-per-suffix rule counts each packet charter as live.
11. `test_plugin.py`'s version test reads `plugin.json`, `pyproject.toml` and `common.py` only.

Any further fork: decide inside the record; log it in §6.

## 3. Interfaces

| item | contract |
|---|---|
| `pyproject.toml` | `name = "agentik-decisions"`; `[project.scripts]` `agentik-decisions` and `decisions`, both `decisions.cli:main` |
| doctor rows | tool: `agentik-decisions` on PATH ok, only `decisions` warn (`alias only; make install`); marketplace: `agentik` ok, only `claude-code-decisions` warn; plugin: `decisions@agentik` ok, only the old ID warn; provider path by ruling 1 |
| plugin files | each runs `agentik-decisions <verb>`; `allowed-tools: Bash(agentik-decisions *)` (the ask skill keeps `AskUserQuestion`) |
| README | title `agentik-decisions`; install `make install`, `claude plugin marketplace add agentik-dev/agentik-commons`, `claude plugin install decisions@agentik`; verbs as `agentik decisions <verb>` |

## 4. Findings that name this row

None. The table is the whole acceptance (the header holds its read-only subset; `verify` the gate line), run in the worktree after the last commit; define first `E() { PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c 'import sys,tomllib,importlib.metadata as m;s=tomllib.load(open("pyproject.toml","rb"))["project"]["scripts"];n=sys.argv[1];sys.argv=[n]+sys.argv[2:];m.EntryPoint(n,s[n],"console_scripts").load()()' "$@"; }` (it runs a `[project.scripts]` entry by name, uninstalled).

| # | line | reads |
|---|---|---|
| 1 | `make check >/dev/null 2>&1; echo $?` | `0` |
| 2 | `scripts/hygiene --json \| python3 -c 'import json,sys;print(sum(f["group"]=="renamed" for f in json.load(sys.stdin)["files"]))'` | `0` |
| 3 | `E agentik-decisions --version 2>/dev/null` | `agentik-decisions 0.8.0` |
| 4 | `E decisions --version 2>/dev/null` | `agentik-decisions 0.8.0` |
| 5 | `E decisions show --help 2>&1 >/dev/null \| grep -c renamed` | `0` |
| 6 | `test -e .claude-plugin/marketplace.json; echo $?` | `1` |
| 7 | `shasum -a 256 -c scripts/vendored.sha256 \| grep -c ': OK$'` | `3` |
| 8 | `C="$(git rev-parse --path-format=absolute --git-common-dir)/../../agentik-commons"; cmp -s scripts/hygiene "$C/scripts/hygiene" && cmp -s scripts/agentik "$C/bin/agentik" && echo same` | `same` |
| 9 | `grep -rh '^allowed-tools' plugin \| grep -vc 'Bash(agentik-decisions \*)'` | `0` |
| 10 | `make -n install BINDIR=/nowhere \| grep -c 'scripts/agentik /nowhere/agentik'` | `1` |
| 11 | `head -1 .python-version; grep -c 'claude-code-decisions' .gitignore` | `agentik-decisions` then `0` |
| 12 | `git status --short \| wc -l` | `0` |

Fails before: line 3 (no such entry point), and lines 2, 6, 7. P3 is the switch's.

## 5. Forbidden reads

Read-only outside this repo: `$C` (line 8): `design/agentik-r1.md` (the sections in `from`), `GUIDE.md`; run `"$C/scripts/sync" .` once.

Forbidden: transcripts, `~/.local/state`, `~/.config` (hygiene reads its private list; never print it), the owner's ledger, other repos.

## 6. Report (under 1,500 words)

The acceptance table with each line's output; the commits; each ruling beyond §2; what went to `NICE_TO_HAVE.md`.
