"""`describe`: this tool as the suite reads it (packet ak6, the plug's contract).

    describe --json                 the tool: its version, needs, verbs and reads
    describe config --json [KEY]    each setting it reads here: its value, where it
                                    comes from and what changes it

The tool keeps no settings file, so a setting is what a verb reads here: a path the verb
would find, or a figure read from its constant and never typed again. Both reads run with
no ledger and outside a git work tree, read no ledger's text, write nothing and exit 0;
`describe` without `--json`, or with a word other than `config`, exits 2. A read of the plug
that cannot run (a cwd that is gone, an OSError, a decode error) prints the contract's §2
object on stdout and exits 2, never a traceback.
"""

import json
import os

from .common import VERSION, Refusal, git_top
from .doctor import PLUGIN
from .ledger import IN_FORCE_CAP, locate
from .rows import ROOT
from .speak import RENDER, respeak_root
from .tree import CEILINGS

__all__ = ["cmd_describe", "describe", "config", "settings", "SUMMARIES", "USAGE"]

TOOL = "decisions"
REPO = "agentik-dev/agentik-decisions"
SUMMARY = "Keeps each repo's ledger of decisions and the owner's open questions."
# The suite's design reserves `agentik rows` for this tool (P2); every other verb is its own.
TOP = ("rows",)
USAGE = "describe takes `describe --json` or `describe config --json [KEY]`"
NEEDS = [{"name": "git", "kind": "program", "why": "finds the repo's top and reads its history",
          "optional": False},
         {"name": "respeak@agentik", "kind": "plugin",
          "why": "it renders the owner's questions; without it `ask` keeps its text",
          "optional": True}]
READS = [{"kind": "config", "name": "settings", "argv": ["describe", "config", "--json"]},
         {"kind": "doctor", "name": "doctor", "argv": ["doctor", "--json"]},
         {"kind": "status", "name": "backlog", "argv": ["backlog", "--json"]},
         {"kind": "status", "name": "rows", "argv": ["rows", "--json"]},
         {"kind": "status", "name": "questions", "argv": ["questions", "--json"]}]
# R6: one sentence a setting, under 100 characters.
SUMMARIES = {
    "ledger": "The ledger every verb reads: DECISIONS.md at the git top level unless a flag "
              "names another.",
    "respeak.root": "Where `ask` finds respeak to render the owner's questions; without it the "
                    "text stays as written.",
    "rows.root": "The folder `rows` reads each build row's records from.",
    "expire.days": "The age, in days, past which `expire` takes an S4 item on no open step out "
                   "of the list.",
    "cap.in_force": "How many entries a ledger may hold in force before the lint refuses it.",
    "ceiling.global": "The bytes a user's global CLAUDE.md may load before `render --ceiling` "
                      "fails it.",
    "ceiling.tree": "The bytes a tree's CLAUDE.md may load before `render --ceiling` fails it.",
    "ceiling.hq": "The bytes an hq's CLAUDE.md may load before `render --ceiling` fails it.",
    "ceiling.repo": "The bytes a repo's CLAUDE.md may load before `render --ceiling` fails it.",
}
FIXED = "The figure is the tool's own; a release changes it."
FLAG = "The flag holds for that one run and is saved nowhere."
# Review 1 R1-F2: a variable that names no renderer is the env layer's value, the tool then
# uses none, and the note says so.
VARIABLE = ("The variable holds for that one run and is saved nowhere; a RESPEAK_ROOT without "
            "%s gives no renderer, and `ask` keeps its text." % RENDER)
ENV = "RESPEAK_ROOT"
PATHS = ("ledger", "respeak.root", "rows.root")
# The plug's other reads (READS' argvs), by verb: the schema each answers.
SCHEMAS = {"doctor": "agentik.doctor/1", "backlog": "agentik.decisions.backlog/1",
           "rows": "agentik.rows/1", "questions": "agentik.questions/1"}


def _parser():
    # cli imports this module, so its parser is read late
    from .cli import VERBS, build_parser
    return VERBS, build_parser()


def _subparsers(parser):
    return next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")


def verbs(parser, names):
    """Each verb in help's order: the first clause of its help line, and whether it is top."""
    helps = {a.dest: a.help or "" for a in _subparsers(parser)._choices_actions}
    return [{"name": name, "summary": helps.get(name, "").split(";")[0].strip(),
             "top": name in TOP} for name in names]


def describe():
    names, parser = _parser()
    return {"schema": "agentik.describe/1", "ok": True, "tool": TOOL, "version": VERSION,
            "summary": SUMMARY, "repo": REPO, "plugin": PLUGIN, "needs": NEEDS,
            "verbs": verbs(parser, list(names)), "reads": READS}


def _setting(key, kind, value, default=None, layer="default", command=None, note=None,
             values=None):
    return {"key": key, "value": value, "default": default,
            "type": "path" if key in PATHS else "integer",
            "choices": None, "summary": SUMMARIES[key],
            "source": {"layer": layer, "path": None, "line": None},
            "change": {"kind": kind, "command": command, "path": None, "block": None,
                       "note": FIXED if kind == "fixed" else note},
            "live": True,
            "values": values if values is not None else
            [] if value is None else [{"layer": layer, "value": value}]}


def _top(cwd):
    try:
        return git_top(cwd)
    except Refusal:
        return None


def settings(cwd, env):
    """The nine settings of R5, in their order, as they stand in `cwd` under `env`."""
    try:
        found = locate(None, cwd)
    except Refusal:
        found = None
    home = env.get("HOME") or os.path.expanduser("~")
    cache = os.path.join(home, ".claude", "plugins", "cache")
    # the contract's §4: each layer that sets the key, lowest first; the variable sets it
    # whenever it is not empty, as `respeak_root` reads it, whether or not it names a renderer;
    # the default layer is the root found without it (fk4: the suite's sources, else the file)
    shipped = respeak_root({k: v for k, v in env.items() if k != ENV}, cache)
    named = env.get(ENV) or None
    layered = ([{"layer": "default", "value": shipped}] if shipped else []) + (
        [{"layer": "env", "value": named}] if named else [])
    top = _top(cwd)
    days = _subparsers(_parser()[1]).choices["expire"].get_default("days")
    rows = [_setting("ledger", "launch", found, command="agentik decisions --ledger VALUE show 1",
                     note=FLAG),
            _setting("respeak.root", "launch", respeak_root(env, cache),
                     layer="env" if named else "default",
                     command="%s=VALUE agentik decisions ask" % ENV, note=VARIABLE,
                     values=layered),
            _setting("rows.root", "launch", os.path.join(top, ROOT) if top else None,
                     command="agentik decisions rows --root VALUE", note=FLAG),
            _setting("expire.days", "launch", days, days,
                     command="agentik decisions expire --days VALUE", note=FLAG),
            _setting("cap.in_force", "fixed", IN_FORCE_CAP, IN_FORCE_CAP)]
    for name in ("global", "tree", "hq", "repo"):
        figure = CEILINGS[name][0]
        rows.append(_setting("ceiling." + name, "fixed", figure, figure))
    return rows


def config(key=None, cwd=None, env=None):
    cwd = os.getcwd() if cwd is None else cwd
    env = os.environ if env is None else env
    layers = [{"name": "default", "path": None, "present": True, "travels": False},
              {"name": "env", "path": None, "present": bool(env.get(ENV)), "travels": False}]
    found = settings(cwd, env)
    if key is not None:
        found = [s for s in found if s["key"] == key]
    return {"schema": "agentik.config/1", "ok": True, "tool": TOOL, "layers": layers,
            "settings": found, "warnings": []}


def schema_of(args):
    """The schema of the plug's read that `args` asks for, or None for any other run."""
    if not getattr(args, "json", False):
        return None
    if args.verb == "describe":
        words = list(getattr(args, "words", None) or [])
        return "agentik.config/1" if words else "agentik.describe/1"
    return SCHEMAS.get(args.verb)


def failure(schema, exc):
    """The contract's §2 object for a read stopped by `exc`: `no_cwd` when the working
    directory cannot be read, else `refused`, `bad_file` (a decode error) or `unreadable`."""
    try:
        os.getcwd()
    except OSError as gone:
        code = "no_cwd"
        message = ("the working directory is gone or cannot be read (%s); run the read from "
                   "a folder that exists" % (gone.strerror or gone))
    else:
        code = ("refused" if isinstance(exc, Refusal) else
                "bad_file" if isinstance(exc, UnicodeError) else "unreadable")
        message = str(exc) or exc.__class__.__name__
    return {"schema": schema, "ok": False, "tool": TOOL,
            "error": {"code": code, "message": " ".join(message.split()), "remedy": None}}


def answer_failure(schema, exc, out):
    out.write(json.dumps(failure(schema, exc), indent=2) + "\n")
    return 2


def cmd_describe(args, out, err):
    words = list(getattr(args, "words", None) or [])
    if not getattr(args, "json", False) or (words and words[0] != "config") or len(words) > 2:
        err.write("decisions: %s\n" % USAGE)
        return 2
    try:
        got = config(words[1] if len(words) > 1 else None) if words else describe()
    except (Refusal, OSError, UnicodeError) as exc:
        return answer_failure(schema_of(args), exc, out)
    out.write(json.dumps(got, indent=2) + "\n")
    return 0
