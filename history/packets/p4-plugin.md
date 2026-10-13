# Packet P4: the plugin under `plugin/`

| item | value |
|---|---|
| from | `design/decisions-r1.md` §4 and §8.3, at `85b0b21`. YOU DO NOT READ THE RECORD (§5) |
| where | worktree `.claude/worktrees/p4`, branch `p4` from the packet's commit |
| may touch | `plugin/**` (never `plugin/.claude-plugin/plugin.json`'s name or author), `tests/test_plugin.py`; nothing else |
| acceptance | `make check` exit 0 under `/usr/bin/python3` (3.9.6); the hook denies one of two JSON lines; the skill body is under 500 lines; each command under thirty |
| budget | 80 turns; commit per item on `p4`, messages ending `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; never push, amend or rebase |

## 1. What the record says (quoted whole, `design/decisions-r1.md:<line>`)

Layout (`:146`): "the files are `plugin/.claude-plugin/plugin.json` (name `decisions`, author as `reference/plugins/agents/plugin.json`), `plugin/skills/decisions/SKILL.md`, `plugin/commands/show.md`, `plugin/commands/scope.md`, `plugin/commands/new.md`, `plugin/hooks/hooks.json` and `plugin/scripts/deny-rule.sh`. The package is that subtree and nothing else: no `decisions/` directory, no fixture and no research is in it, and the only paths it names are the verbs."

The skill (`:150`): "`skills/decisions/SKILL.md`, frontmatter as `reference/plugins/respeak/SKILL.md:1-10` (name, a description under 200 characters, `allowed-tools: Bash(decisions *)`), body under 500 lines. Only the description loads at session start; the body loads on use (`research/06-evaluation.md:106`). The body carries, in this order:"

(`:152`) "1. The two-line retrieval rule a consuming repo puts in its `CLAUDE.md`, quoted exactly as `init` prints it: "Decisions live in `decisions/`; before touching a governed area run `decisions scope --governs <tag>`, and read one ruling with `decisions show <id> [n]`. Never read `decisions/INDEX.md` or the ledger whole; draft with `decisions new`, status `proposed`, and never run `decisions rule`.""

(`:153`) "2. The manners: consult before touching a governed area; never load the index whole above the threshold; draft with `new`; name a consumer; cite or supersede any overlapping in-force record; put a ruling to the owner in plain language with its context, a few at a time (`reference/memory/decision-flapping-guardrails.md`)."

(`:154`) "3. The threshold, stated as the model of §8.3 with its three assumptions and the rule of thumb: an in-force set under about 2.7 KB may be rendered inline by `render`; above it the repo carries the two-line rule only." §8.3 (`:218`): "An index loaded every turn costs its size times the turns: S × T. A retrieval costs one extra turn that re-reads the context: L × C for L lookups. Inline wins when S < L × C / T. The three assumptions, from `research/06-evaluation.md:93-100`: T = 300 turns per sitting, C = 100k tokens of context per turn, L = 2 lookups per sitting. Then S < 667 tokens, about 2.7 KB at four bytes a token." "the skill states the model, not the number, as the rule."

(`:155`) "4. How a packet's §2 and a refuter's brief are cut: `decisions scope --governs <wall> --full`, pasted whole, never paraphrased (`reference/example-ops/build-packet-r1.md:64`)."

The commands (`:159`): "Each is a short markdown command that runs one verb and adds nothing: `/decisions:show <id> [n]`, `/decisions:scope <tag> [status]`, `/decisions:new <title> --governs ... --consumer ...`. Under thirty lines each. No command for `rule`, `supersede`, `index` or `render`: the first is the owner's, and the rest are `make check`'s."

The hook (`:163`): "`hooks/hooks.json`: one `PreToolUse` entry, matcher `Bash`, command `"${CLAUDE_PLUGIN_ROOT}/scripts/deny-rule.sh"`, on the shape of `reference/plugins/respeak/hooks.json` (which has a `PostToolUse` on `Write|Edit`). The script reads the hook's JSON on stdin, takes `tool_input.command`, and when the command matches `\b(decisions|decisions\.py)\s+rule\b` exits 2 with the reason on stderr: "rule is the owner's verb; put the ruling to the owner in plain language". Exit 2 blocks the call and returns the reason to the agent. Anything else exits 0 and prints nothing. A test feeds the script two JSON lines and expects one deny."

## 2. Rulings that bind this row
0001 (3): "a scoped set is the query `scope --governs <tag>`; a record names its tags". `CLAUDE.md`: "The plugin carries manners (one skill, a few commands, one hook) and NO data: a repo owns its `decisions/`."

## 3. Interfaces and the tests that gate them
Coordinator's cuts:
- A command is a markdown file with a frontmatter of `description` and `allowed-tools: Bash(decisions *)` (the live siblings' command files are listed in `reference/plugins/*/tree.txt` but not pinned; read the shape from `claude-code-respeak/commands/*.md`, one file, read-only); the body runs `decisions <verb> $ARGUMENTS` and adds nothing.
- `deny-rule.sh` is `#!/bin/sh`; it may call `/usr/bin/python3 -c` for the JSON parse (stdlib `json`, `re`), never `jq`; a malformed or empty stdin exits 0 silently. The regex is the record's, over `tool_input.command` only.
- The shell test is `plugin/scripts/test-deny-rule.sh`: feeds `{"tool_name":"Bash","tool_input":{"command":"decisions rule 0001 in-force"}}` and `{"tool_name":"Bash","tool_input":{"command":"decisions show 0001"}}`, expects exit 2 then 0, and the reason on stderr for the first; exits nonzero on any mismatch. `tests/test_plugin.py` (unittest) runs that script with `subprocess` and asserts exit 0, and also asserts: the skill body under 500 lines, the description under 200 characters, each command under thirty lines, `hooks.json` parses and its one entry is `PreToolUse` with matcher `Bash`, and `plugin/` contains no `decisions/` directory.
- The skill's part 3 states the model (S × T against L × C, the three assumptions) and names 2.7 KB only as the worked example.

## 4. Findings that name this row
None. Unverified at a pin (say so in the skill, in one clause, never as fact): that a marketplace `source` may name a subtree; the coordinator proves it after the merge.

## 5. Forbidden reads
the record; `design/`; `README.md`; `research/`; `history/` except this packet; `reference/` except `reference/plugins/**` (small; read what you copy) and `reference/memory/decision-flapping-guardrails.md`; `decisions/`.

## 6. Report (one table, five bullets, under 600 words), at `history/packets/p4-report.md` on the branch
- packet sufficient: yes | no, and what was missing
- items built, each with its commit; what you decided that the packet left open
- the acceptance run, exit lines only, plus `wc -l` of the skill body and the two JSON lines' exits
