"""agentik decisions - six verbs over one sectioned DECISIONS.md per repo, plus doctor and backlog.

Verbs
    show <n>... | --area NAME     entries verbatim under their heading, or a whole
                                  `###` subsection (a case-insensitive prefix;
                                  a leading "The " may be left out)
    find WORD                     `N Title (area or section)` of each entry holding
                                  WORD: the area for an entry in force
    new --title T --stands S --choice C --option "L: E" ... --recommend R
        [--report P]              the four-part question in OPEN-QUESTIONS.md, 2 to
                                  4 options the first recommended, and its Proposed
                                  line in the ledger
    ask [N...]                    the open questions, rendered once through respeak
                                  and written back, as AskUserQuestion calls (JSON)
    answer N (--pick L | --other T) --source S [--text P]
        (--area A | --amends M [--shorter] | --no-entry) [--into PATH]
                                  the owner's answer: entry N, an amendment or
                                  none; the question leaves, an Answered line stays;
                                  A resolves as `show --area` does, or is new
    render [--into PATH] [--check | --lint]
                                  the lint, then the generated block in the
                                  CLAUDE.md beside the ledger, or in PATH
    doctor [--json]               the interpreter, the tool, the plugin, the
                                  provider, the ledger and respeak
    backlog [REPO...] [--json]    each repo's NICE_TO_HAVE.md placed against its
                                  HANDOFF.md build order; writes nothing

The ledger is `--ledger PATH`, else DECISIONS.md at the git top level of the
working directory; `backlog` reads no ledger and ignores it. `--version` prints
the version, which `doctor` compares with the tool on PATH.

The tool is `agentik-decisions`, run as `agentik decisions`; the old name
`decisions` is a second entry point until 2026-12-31 and, with stderr a
terminal, says so in one stderr line before anything else (agentik-r1 4.3).

Exit codes
    0  the answer; `find` with no match too; `backlog` whenever its files could be
       read; `answer` whose block write failed after both files were written (a
       warning on stderr names `agentik decisions render`)
    1  `render`: a lint problem, or with --check a stale block
    2  usage, an unknown verb, entry or area, an unreadable ledger, a `new` or
       `answer` refusal, an `ask` for an unknown N or under a held lock, a `render`
       target that is the ledger itself, a failed `doctor` check (a `warn` never
       changes the exit; a `--ledger` naming an absent file fails), or a `backlog`
       REPO that is not a directory or a file it cannot read as UTF-8
"""

import argparse
import contextlib
import os
import sys

from .answer import cmd_answer
from .backlog import cmd_backlog
from .ask import cmd_new
from .selector import cmd_ask
from .common import VERSION, Refusal
from .doctor import cmd_doctor
from .ledger import locate
from .lookup import cmd_find, cmd_show
from .render import cmd_render

__all__ = ["build_parser", "main", "alias_note", "VERBS", "ALIAS", "NOTE"]

# agentik-r1 4.3: the old name runs the same code until 2026-12-31; a person at a
# terminal is told once, and pipes, hooks and gates see nothing.
ALIAS = "decisions"
NOTE = "decisions: renamed; use 'agentik decisions \u2026' (ends 2026-12-31)\n"


def build_parser():
    ledger = argparse.ArgumentParser(add_help=False)
    ledger.add_argument("--ledger", default=argparse.SUPPRESS,
                        help="the ledger; the default is DECISIONS.md at the git top level")
    parser = argparse.ArgumentParser(prog="agentik decisions", description=__doc__, parents=[ledger],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version="agentik-decisions %s" % VERSION)
    subs = parser.add_subparsers(dest="verb", metavar="{%s}" % ",".join(VERBS))

    show = subs.add_parser("show", parents=[ledger],
                           help="entries verbatim under their heading, or one area")
    show.add_argument("numbers", nargs="*", type=int, metavar="n")
    show.add_argument("--area", default=None)

    find = subs.add_parser("find", parents=[ledger],
                           help="the title line of each entry holding a word",
                           description="`N Title (area or section)` for each entry whose "
                           "title or body holds WORD, ignoring case: the area for an entry "
                           "in force, else its section; `L<line> <heading> (legacy)` for a "
                           "block below the legacy marker that holds it")
    find.add_argument("word")

    new = subs.add_parser("new", parents=[ledger],
                          help="the four-part question and its Proposed line")
    new.add_argument("--title", required=True)
    new.add_argument("--stands", required=True, help="where things stand")
    new.add_argument("--choice", required=True, help="the choice, ending in `?`")
    new.add_argument("--option", action="append", dest="options", metavar="'LABEL: EFFECT'",
                     help="an answer and what it sets in motion; 2 to 4, the first "
                          "is the recommendation")
    new.add_argument("--recommend", required=True, help="the recommendation")
    new.add_argument("--report", default=None, help="the report the question rests on")

    asks = subs.add_parser("ask", parents=[ledger],
                           help="the open questions as AskUserQuestion calls, in JSON")
    asks.add_argument("numbers", nargs="*", type=int, metavar="N")

    answer = subs.add_parser("answer", parents=[ledger],
                             help="the owner's answer to question N, into the ledger")
    answer.add_argument("number", type=int, metavar="N")
    chosen = answer.add_mutually_exclusive_group(required=True)
    chosen.add_argument("--pick", default=None, metavar="LABEL", help="an option's label")
    chosen.add_argument("--other", default=None, metavar="TEXT",
                        help="the owner's own answer, restated")
    answer.add_argument("--source", required=True, help="where the owner answered")
    answer.add_argument("--text", default=None, metavar="P",
                        help="the entry's body only, without its bold title or its (date; "
                        "source) tail, which answer writes; with --amends, the whole body in "
                        "force after the answer")
    lands = answer.add_mutually_exclusive_group(required=True)
    lands.add_argument("--area", default=None, metavar="A",
                       help="entry N last under ### A: an exact name, else a unique prefix, a "
                       "leading \"The\" left out; a name no heading matches is a new area")
    lands.add_argument("--amends", type=int, default=None, metavar="M",
                       help="replace entry M's paragraph")
    lands.add_argument("--no-entry", action="store_true", help="an answer that sets no entry")
    answer.add_argument("--shorter", action="store_true",
                        help="with --amends: let through a paragraph under half the old "
                        "one's length")
    answer.add_argument("--into", default=None,
                        help="the CLAUDE.md block's target; the default is beside the ledger")

    render = subs.add_parser("render", parents=[ledger],
                             help="the lint, then the generated block in a CLAUDE.md")
    render.add_argument("--into", default=None,
                        help="the target; the default is the CLAUDE.md beside the ledger")
    mode = render.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="write nothing; print the diff, exit 1 when stale")
    mode.add_argument("--lint", action="store_true", help="the lint alone")

    doctor = subs.add_parser("doctor", parents=[ledger],
                             help="check this machine and this repo")
    doctor.add_argument("--json", action="store_true")

    backlog = subs.add_parser("backlog", parents=[ledger],
                              help="each repo's NICE_TO_HAVE.md against its build order")
    backlog.add_argument("repos", nargs="*", metavar="REPO",
                         help="a repo's directory; the default is the git top level")
    backlog.add_argument("--json", action="store_true")
    return parser


def alias_note(argv0, err):
    """The one renamed line, when the tool runs under its old name and `err` is a terminal."""
    isatty = getattr(err, "isatty", None)
    if os.path.basename(argv0 or "") == ALIAS and isatty is not None and isatty():
        err.write(NOTE)


def main(argv=None, out=None, err=None):
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    if argv is None:
        alias_note(sys.argv[0], err)
        argv = sys.argv[1:]
    argv = list(argv)
    try:
        # argparse prints --help and its usage errors itself: into `out` and `err`.
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if not args.verb:
        err.write("decisions: name a verb: %s\n" % ", ".join(VERBS))
        return 2
    try:
        if args.verb == "doctor":
            # `doctor` finds the ledger for itself and reports its absence as a check.
            return cmd_doctor(args, out, err)
        if args.verb == "backlog":
            # `backlog` reads NICE_TO_HAVE.md and HANDOFF.md, never a ledger.
            return cmd_backlog(args, out, err)
        path = locate(getattr(args, "ledger", None), os.getcwd())
        return VERBS[args.verb](args, path, out, err)
    except Refusal as exc:
        err.write("decisions: %s\n" % exc)
        return 2


VERBS = {"show": cmd_show, "find": cmd_find, "new": cmd_new, "ask": cmd_ask,
         "answer": cmd_answer, "render": cmd_render, "doctor": cmd_doctor,
         "backlog": cmd_backlog}
