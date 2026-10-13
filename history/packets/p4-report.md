# Packet P4 report: the plugin under `plugin/`

| item | files | commit |
|---|---|---|
| 1 skill | `plugin/skills/decisions/SKILL.md` (75 lines; body 68) | `f4085d9` |
| 2 commands | `plugin/commands/show.md`, `scope.md`, `new.md` (7, 8, 7 lines) | `990011b`, `fc953cc` |
| 3 hook, scripts, tests | `plugin/hooks/hooks.json`, `plugin/scripts/deny-rule.sh`, `plugin/scripts/test-deny-rule.sh` (both executable), `tests/test_plugin.py` (7 tests) | `676cec2` |
| acceptance | `make check` under `/usr/bin/python3` | exit 0, 50 tests OK |

- **Packet sufficient: yes**, with two small gaps closed without inventing design. (a) §3 says to read the command shape from `claude-code-respeak/commands/*.md`, but that directory does not exist. I read one sibling command instead, `claude-code-agents/commands/delegate-costs.md` (read-only), for the frontmatter shape. (b) §1 writes the scope command as `/decisions:scope <tag> [status]`, but the tool (`src/decisions.py:502-505`) takes status as `--status`, not as a position. So `decisions scope --governs $ARGUMENTS` would break when a status is given.
- **Items built:** skill `f4085d9`, commands `990011b` and then `fc953cc` (the scope fix), hook, scripts and tests `676cec2`. `plugin/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` are untouched.
- **What I decided that the packet left open:** `scope.md` runs `decisions scope --governs $1` and adds `--status $2` only when a second argument is given. `show.md` and `new.md` pass `$ARGUMENTS` straight through. Each command has an `argument-hint`. The hook entry has `timeout: 10`, copying the respeak shape. `deny-rule.sh` uses `exec /usr/bin/python3 -c` with stdlib `json` and `re`. Any failure to parse or find the command exits 0. `test_plugin.py` checks every directory named `decisions` inside `plugin/` and allows only `skills/decisions/`, because the layout requires it. The skill's description is written as a folded (`>`) scalar. The unverified clause about marketplace `source` naming a subtree ends the skill in one parenthesis.
- **Acceptance run:** `make check exit=0`; `gate: shebang ok`; `gate: 3.9 syntax ok`; `gate: pyflakes absent, skipped`; `Ran 50 tests`; `OK`. Skill body `wc -l`: 68 (75 with frontmatter).
- **The two JSON lines:** `decisions rule 0001 in-force` exits 2 with the reason on stderr. `decisions show 0001` exits 0 and prints nothing (`test-deny-rule: ok (2 then 0)`). Extra checks: empty stdin exits 0, malformed stdin exits 0, and `python3 src/decisions.py rule 1` exits 2.
