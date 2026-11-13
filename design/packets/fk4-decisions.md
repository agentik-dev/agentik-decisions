# Packet fk4-decisions: `ask` and the doctor find respeak by the suite's answer, not by the newest cache folder

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-13, brief fk4 |
| pin | main at `ba33fc7` (0.21.20, after ak6). Version 0.22.3 (dc1-init lands 0.22.2 first). Worktree `.claude/worktrees/fk4-decisions`, branch `fk4-decisions`, nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test starts the real `claude` or suite, or reads the live home |
| may touch | `plugin/lib/decisions/speak.py`, `doctor.py`, `plug.py` and `scripts/readme-render` (the two callers of `newest_root`); `tests/test_fk4_source.py` (new), `tests/test_backlog.py` (one assertion), `tests/test_ak6_plug.py` (a fixture: the installed file R3 now reads; respeak's check's key list gains `source`), `tests/test_readme.py` (the two `--cache` cases: a temp HOME, and the installed file decides); the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_fk4_source tests.test_backlog tests.test_bare_machine tests.test_doctor tests.test_ak6_plug` |
| budget | about 90 tool calls |

## 1. The finding, measured

`speak.respeak_root` takes `RESPEAK_ROOT`, else `newest_root`: the highest `*/respeak/<N.N.N>/` under the plugin cache holding the renderer, of any marketplace, installed or not. The brief measured at `b059365`, in made-up homes: a fork alone (`respeak@acme-tools` 0.12.6) reads ok, the fork's folder; the fork at `0.12.6-acme.1` reads `respeak not found`; nothing installed and a leftover folder reads ok; `respeak@agentik` 0.12.6 with the fork at 0.12.7 reads the fork's. The suite now has one finder, `agentik-suite describe sources --json`; both doctors take its answer, or one shared rule where there is none.

## 2. Rulings

- R1, the order. `RESPEAK_ROOT` stays first: set (not empty), it gives the root, or none when it holds no renderer, and nothing else is asked.
- R2, the read. Else start `$HOME/.local/bin/agentik-suite describe sources --json respeak` (never PATH), the caller's environment and cwd, under a wall of 5 s; the whole answer is read (`doctor.first_output`'s 4,096 B cut does not serve). It counts when the exit is 0 and stdout is one object with `schema` `agentik.sources/1`, `ok` true and one row in `tools`. The row's keys: `kind` (`own`, `plugin`, `folder`, `undecided`, `absent`), `plugin` (null for a folder), `root`, `version`, `found`, `declared` (`{"path", "line"}` or null), `seen` (`[{"plugin", "version", "scope", "root"}]`). `own` means `respeak@agentik`.
- R3, no read. With no launcher or any other answer (today's suite exits 2): from `installed_plugins.json` beside the cache, the entries over every id's list whose plugin is named `respeak` and whose `scope` is `user` or `managed`. One: it stands, its `installPath` the root. Two or more: no root, and the words `not checked: say which with the suite's sources`. None: no root.
- R4, the root. A source that stands and is found gives its root when `<root>/scripts/respeak-render.sh` is a file; `undecided`, `absent` and not found give none, and no other folder fills in. `newest_root` and `version_key` go, with their `__all__` names.
- R5, the shape. `speak.respeak_source(environ, cache)` returns the root and how it was found (`variable`, `read` or `file`) with `kind`, `plugin`, `version`, `declared` and `seen`; `respeak_root(environ, cache)` keeps its signature and returns that root, so `selector.render` does not change.
- R6, `check_respeak`'s line. By the variable: ok, the root, and that `RESPEAK_ROOT` gave it. `own`: ok, the root as the detail. `plugin` or `folder` with a root: ok, a detail with no id, marketplace, folder or version; the JSON check gains `source` `{"kind", "plugin", "root", "version", "declared"}` (null in the two cases before), and the text line prints the root after the detail. `undecided`: warn, the count, `remedy` `agentik config suite.sources.respeak`. A line whose plugin is not installed or whose folder is gone: warn, naming `path:line`. R3's two or more: warn, its words. None, and `absent`: today's warn, byte for byte.
- R7, not this row's: `check_plugin`, `check_marketplace`, and `selector.render`'s line with no root (`tests/test_bare_machine.py` pins it).

## 3. Acceptance

Tests in `tests/test_fk4_source.py`, each in a temp HOME; a stub launcher at `<home>/.local/bin/agentik-suite` prints a canned answer and logs its argv; a root is `<home>/.claude/plugins/cache/<marketplace>/respeak/<version>` holding the renderer. At the pin the file runs 11 tests: 14 failures, 47 errors (line 5's errors are the missing `SOURCES_WALL`).

1. Red at the pin: the fork alone at `0.12.6-acme.1`, the stub saying it stands: `respeak_root` gives its root; `check_respeak` is ok.
2. The fork alone at 0.12.6, by the stub: its root; `doctor --json`'s check holds no `acme` in `detail` or `remedy`, `source.root` is the root; the text line holds it.
3. Red at the pin: a leftover folder, nothing installed, the stub answering `absent`: no root, today's warn.
4. Red at the pin: both installed, the stub answering `undecided` with two `seen`: no root; a warn; `remedy` the hint; no `acme` in the detail.
5. No launcher, exit 2, `ok` false, another schema, no JSON, a sleep past the wall (and a flood): the file decides. The fork alone at either version, scope `user`: its root. Both at `user`: no root, the words. The leftover folder: no root.
6. `RESPEAK_ROOT` set in each home: its root, the stub's log empty, the line says the variable gave it; a folder with no renderer: no root.
7. `respeak@agentik` alone, by the stub and by the file: ok, its root the detail, `source` null.
8. `tests/test_bare_machine.py` and `test_suite_green_without_respeak` pass unchanged; in `test_doctor_respeak_warn_absent` the variable's assertion turns; `grep -n "newest_root\|def version_key" plugin/lib/decisions/speak.py` prints nothing.
9. The full suite; the gate's `make check`, green.

## 4. Left

The suite's finder (fk1, built against the schema above and a stub; the landing waits on it); the session tool's doctor (fk3); what an issue report does with `source` (fk6).

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no relay ledger.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
