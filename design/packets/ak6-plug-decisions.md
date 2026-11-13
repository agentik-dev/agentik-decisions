# Packet ak6-plug-decisions: `describe`, what the tool reads here; its checks in the one shape

| item | value |
|---|---|
| from | the hq's coordinator, 2026-11-13, brief ak6 |
| pin | main at `b059365` (0.21.17). Version 0.21.18. Worktree `.claude/worktrees/ak6-plug-decisions`, branch `ak6-plug-decisions`, nothing linked |
| wall | this worktree; no push, `--amend`, rebase, merge, install or bare `make`; no test reads live state |
| may touch | `plugin/lib/decisions/plug.py` (new), `cli.py`, `doctor.py`, `backlog.py`; `tests/test_ak6_plug.py` (new), `tests/test_cli.py`, `tests/test_doctor.py`, `tests/test_backlog.py` where they pin a key this row changes; the version places, `README.md`, `design/readme/{source.md,rendered.sha256}`; `NICE_TO_HAVE.md`; this packet; the charter |
| verify | the gate queue's `make check`, once, last |
| acceptance | §3; `python -m unittest tests.test_ak6_plug tests.test_cli tests.test_doctor tests.test_plugin tests.test_backlog` |
| budget | about 90 tool calls |

## 1. What the source says: the owner's words and the pin

The owner: "Make plugin configuration discoverable and drill down." The suite's `agentik config decisions` lists a tool's settings and `agentik config decisions.ledger` prints one as a card. This tool keeps no settings file, so its answer is what it reads here and which flag changes it. Cited: hq entries 6 (`/usr/bin/python3`, a 3.9 floor, stdlib alone), 9 (at most 25 in force, a figure no setting moves) and 37 (made-up names).

At `b059365`, in a temp HOME: `describe` is argparse's `invalid choice`, exit 2; `doctor --json` prints `{checks: [{name, status, detail}], provider}`; `backlog --json` opens with `repos`; `questions --json` and `rows --json` already open with `schema` and `ok`.

## 2. Rulings

- R1, what stands. Every verb prints what it printed, but for the keys R6 and R7 add. `doctor`'s text and exit (2 on a `fail`) stay. No settings file, no new variable read.
- R2, the module `plugin/lib/decisions/plug.py`: `cmd_describe` and the settings table. In `cli.py` the verb's paragraph, its parser before `install-cli`'s, `"describe"` before `"install-cli"` in `VERBS`, a branch in `main` before `locate`. No command page.
- R3, `describe --json`: `tool` `decisions`, `version` `common.VERSION`, a summary under 80 characters; `needs` `git` (program) and `respeak@agentik` (plugin, optional: `ask` keeps its text without it); `verbs` in help's order, each the first clause of its help line, `top` true for `rows` alone; `reads` `config`, `doctor`, then status reads `backlog`, `rows`, `questions`, each its verb plus `--json`.
- R4, the layers: `default` (present) and `env` (present when `RESPEAK_ROOT` is set); both path null, neither travels. No `user` layer.
- R5, nine settings, `live` true, each figure read from its constant: `ledger` (path, `locate(None, cwd)` or null; `launch` `agentik decisions --ledger VALUE show 1`), `respeak.root` (path, `respeak_root`, source `env` when the variable gave it; `launch` `RESPEAK_ROOT=VALUE agentik decisions ask`), `rows.root` (path, what `rows` reads with no `--root`, null outside a work tree; `launch` `agentik decisions rows --root VALUE`), `expire.days` (integer, the parser's default, 14; `launch` `agentik decisions expire --days VALUE`), `cap.in_force` (`IN_FORCE_CAP`), `ceiling.global`, `ceiling.tree`, `ceiling.hq`, `ceiling.repo` (`CEILINGS[...][0]`), the last five `fixed`, note `The figure is the tool's own; a release changes it.`
- R6, the summaries: one table in `plug.py`, the brief's nine sentences word for word.
- R7, `describe config --json [KEY]` runs with no ledger and outside a work tree, reads no ledger's text, exits 0, `warnings` `[]`; an unknown KEY gives `settings` `[]`, exit 0. `describe` without `--json`, or a word after it that is not `config`: exit 2, one stderr line naming `describe --json`.
- R8, the other reads. `doctor --json`: `schema`, `ok` true, `tool`, `failed`, `warned`, `checks` each gaining `remedy`, then `provider`. A remedy only where a constant or the detail names one command: `MARKETPLACE_HINT`, `PLUGIN_HINT`, `agentik decisions render --lint` for a ledger that does not lint, `/decisions:install-cli` for a `tool` check not `ok` (`make install` works only in a checkout); else null. `backlog --json`, both forms: `"schema": "agentik.decisions.backlog/1"`, `"ok": true` first, every other key as it was.

## 3. Interfaces: the plug's contract, digested, and the acceptance list

The shared contract (rows ak5 to ak9) binds the shapes; this is its part this tool prints.

- §2 envelope: `{"schema": "agentik.<read>/1", "ok": true, "tool": "decisions", ...}`; a new key never raises the number; `ok` true means the read ran. One JSON object and a newline on stdout, UTF-8, no ESC byte; notes to stderr. A read writes nothing outside `$XDG_CACHE_HOME/agentik/` (bytecode included: the launcher sets the pycache prefix there) and stays well under 1 s.
- §3 `describe --json` keys: `schema`, `ok`, `tool`, `version`, `summary`, `repo` (`owner/repo`), `plugin`, `needs` (`name`, `kind` program/package/plugin/toolchain, `why`, `optional`), `verbs` (`name`, `summary`, `top`), `reads` (`kind` config/doctor/status, `name`, `argv`; at most one config and one doctor). The suite refuses an answer missing a key.
- §4 config read: `layers` (`name`, `path`, `present`, `travels`), `settings`, `warnings` (`key`, `reason`, `value`, `path`, `line`). A setting: `key`, `value`, `default` (what ships; changed when not null and unequal, one JSON type), `type` (string/integer/number/boolean/list/path/secret), `choices`, `summary` (under 100 characters), `source` (`layer`, `path`, `line`), `change` (`kind` command/edit/launch/fixed, `command`, `path`, `block`, `note`, all five keys), `live`, `values` (`{layer, value}` lowest first). With KEY: that setting or `[]`, exit 0; `layers` and `warnings` whole.
- §5 doctor read: `schema`, `ok`, `tool`, `failed`, `warned`, `checks` (`name`, `status` ok/note/warn/fail, `detail`, `remedy`: one command or null; a checkout-only line is none). Exit and text stay the tool's.
- §6 a status read gains `schema` (`agentik.<tool>.<name>/1`) and `ok` first and keeps every other key; one that carries a `schema` keeps it.
- §7 tests: describe's keys, no ESC, under 1 s; each read prints `schema` and `ok`; every setting every key, every layer a name of `layers`; an unknown KEY `[]`; the temp HOME unchanged outside the cache.

Cases in `tests/test_ak6_plug.py`, each red at the pin (`invalid choice: 'describe'`, or the old keys), through `plugin/bin/agentik-decisions` in a temp HOME with `XDG_*` under it:

1. `describe --json`: exit 0, every §3 key, five reads, `rows` the one `top`, no ESC, under 1 s; `describe` and `describe nosuch --json` exit 2.
2. In a temp git repo with a `DECISIONS.md`: nine settings, every §4 key; `ledger` its absolute path, layer `default`, `launch`; `expire.days` 14 against 14; `cap.in_force` 25, `fixed`; the ceilings equal `tree.CEILINGS`.
3. Outside a work tree: exit 0, `ledger` and `rows.root` null.
4. `RESPEAK_ROOT` on a made-up folder holding the renderer: that folder, layer `env`, the `env` layer present; unset: null, `default`.
5. A keyed read prints one setting; `nosuch` prints `[]`, exit 0.
6. `doctor --json` in §5's shape; the marketplace's remedy `MARKETPLACE_HINT` when none is known, the tool's `/decisions:install-cli` off PATH, an `ok` check's null; the text and exit as at the pin.
7. `backlog . --json` and `backlog --json --order FILE REPO` open with `schema`, `ok`; the pin's keys follow.
8. After lines 1 to 5, HOME outside the cache and the repo are byte for byte as they were.
9. By hand: the suite's `config` reads `decisions.ledger`, `decisions.ceiling.repo` and the list.
10. The unittest line in the header passes. 11. The gate's check, once, last.

## 4. Findings that name this row: ledger, NICE, forks

Not built: a settings file, a `term` module or catalogue, a human `describe`, the suite's side, a README row (the source is 4 B under its cap: only its two version places change). No fork. Version `0.21.18`, alone in the last commit under `plugin/`.

The contract's §2 to §7 copied whole pass this file's 9,216 B cap, so §3 holds a digest.

## 5. Forbidden reads

No transcript, no live state root, no gate ledger, no file under `~/.claude`, no relay ledger.

## 6. Report

The hand-back to the hq's coordinator, at most 45 lines.
