"""agentik decisions - six verbs over one sectioned DECISIONS.md per repo, plus doctor, backlog,
expire, analyze and audit.

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
    answer N (--pick L | --other T) --source S [--text P | --add S]
        (--area A | --amends M [--shorter] [--move-to A] | --no-entry)
        [--into PATH] [--every-turn]
                                  the owner's answer: entry N, an amendment or
                                  none; the question leaves, an Answered line stays;
                                  A resolves as `show --area` does, or is new;
                                  --move-to moves the amended entry under A;
                                  --every-turn lets it grow the block under
                                  Every session, or the tree's file
    render [--scope tree] [--into PATH] [--check | --lint | --fold-tails]
        [--ceiling]               the lint, then the generated block in the
                                  CLAUDE.md beside the ledger, or in PATH;
                                  --scope tree writes the ledger's `Every
                                  session of the tree` alone, the whole file,
                                  into the CLAUDE.md of the folder that holds
                                  the repo; --check and --lint print the
                                  file's loaded bytes beside its ceiling, and
                                  --ceiling fails a file over it; --fold-tails
                                  first writes each tail in force in form T2,
                                  once HEAD holds the ledger
    doctor [--json]               the interpreter, the tool, the plugin, the
                                  provider, the ledger and respeak
    install-cli [--prefix P]      freeze this plugin's lib/ and write the launcher,
                                  its `decisions` link and the `agentik` door
                                  under P (default ~/.local): 0, or 1 it could not
    backlog [REPO...] [--order FILE] [--json]
                                  each repo's NICE_TO_HAVE.md placed against its
                                  HANDOFF.md build order, or FILE's steps for that
                                  repo or `suite`; writes nothing
    expire [REPO...] [--order FILE] [--days N] [--write] [--json]
                                  the closed NICE items and the S4 ones older
                                  than N days (14) on no open step; --write
                                  appends them to history/NICE-overflow.md
                                  and takes them out, once HEAD holds the file;
                                  dry without it
    analyze [churn] [REPO...] [--since Nd|YYYY-MM-DD] [--until YYYY-MM-DD] [--json]
                                  churn from each repo's git history over the
                                  window (14 days to now by default): the share
                                  of lines in records, record commits a landing,
                                  commits a charter, NICE_TO_HAVE.md's rows;
                                  writes nothing
    audit [REPO...] [--tree FILE] [--json]
                                  the ledger's retire and rewrite candidates,
                                  marks P1 to P6 and P8 a lead, Every session
                                  first with each line's bytes in the block;
                                  P5 reads the tree, each REPO, FILE's repos or
                                  the ledger's git top; writes nothing

The ledger is `--ledger PATH`, else DECISIONS.md at the git top level of the
working directory; `backlog`, `expire` and `analyze` read no ledger and ignore it.
`--version` prints the version, which `doctor` compares with the tool on PATH.

The tool is `agentik-decisions`, run as `agentik decisions`; the old name
`decisions` is a second entry point until 2026-12-31 and, with stderr a
terminal, says so in one stderr line before anything else (agentik-r1 4.3).

Exit codes
    0  the answer; `find` with no match too; `backlog` whenever its files could be
       read; `expire` whenever its view printed or its move was made; `analyze`
       and `audit` whenever its view printed; `answer` whose block write failed
       after both files were written (a warning on stderr names `agentik decisions
       render`)
    1  `render`: a lint problem, with --check a stale block or an absent tree's
       file, or under --ceiling a file over its ceiling
    2  usage, an unknown verb, entry or area, an unreadable ledger, a `new` or
       `answer` refusal, an `ask` for an unknown N or under a held lock, a `render`
       target that is the ledger itself, a failed `doctor` check (a `warn` never
       changes the exit; a `--ledger` naming an absent file fails), or a `backlog`
       REPO that is not a directory or a file it cannot read as UTF-8, or an
       `analyze` window it cannot read or argument that is neither an analysis
       nor a directory, or an `expire` REPO not a directory, `--order` FILE it
       cannot read, --days under 1, or a --write whose NICE_TO_HAVE.md HEAD does
       not hold, whose files changed under it, or that failed, or an `audit`
       REPO that is not a directory or `--tree` FILE it cannot read
"""

import argparse
import contextlib
import os
import sys

from .analyze import cmd_analyze
from .answer import cmd_answer
from .audit import cmd_audit
from .backlog import cmd_backlog
from .expire import cmd_expire
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
    answer.add_argument("--add", default=None, metavar="S",
                        help="with --amends, in place of --text: sentences appended to the "
                        "paragraph as it stands")
    lands = answer.add_mutually_exclusive_group(required=True)
    lands.add_argument("--area", default=None, metavar="A",
                       help="entry N last under ### A: an exact name, else a unique prefix, a "
                       "leading \"The\" left out; a name no heading matches is a new area")
    lands.add_argument("--amends", type=int, default=None, metavar="M",
                       help="replace entry M's paragraph")
    lands.add_argument("--no-entry", action="store_true", help="an answer that sets no entry")
    answer.add_argument("--shorter", action="store_true",
                        help="with --amends: let through a --text that drops a sentence of "
                        "the old paragraph")
    answer.add_argument("--move-to", default=None, metavar="A",
                        help="with --amends: move the amended entry last under ### A, "
                        "resolved as --area is")
    answer.add_argument("--every-turn", action="store_true",
                        help="let through an answer that makes the block, loaded on every "
                        "turn, larger under Every session, or the tree's file larger")
    answer.add_argument("--into", default=None,
                        help="the CLAUDE.md block's target; the default is beside the ledger")

    render = subs.add_parser("render", parents=[ledger],
                             help="the lint, then the generated block in a CLAUDE.md")
    render.add_argument("--into", default=None,
                        help="the target; the default is the CLAUDE.md beside the ledger, "
                        "or under --scope tree the folder's")
    render.add_argument("--scope", choices=("repo", "tree"), default="repo",
                        help="tree: the ledger's `Every session of the tree` alone, the whole "
                        "file, into the CLAUDE.md of the folder that holds the repo")
    render.add_argument("--ceiling", action="store_true",
                        help="with --check or --lint: exit 1 when the file loads more than "
                        "its ceiling")
    mode = render.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="write nothing; print the diff, exit 1 when stale")
    mode.add_argument("--lint", action="store_true", help="the lint alone")
    mode.add_argument("--fold-tails", action="store_true",
                      help="rewrite each tail in force in form T2, then the block")

    doctor = subs.add_parser("doctor", parents=[ledger],
                             help="check this machine and this repo")
    doctor.add_argument("--json", action="store_true")

    backlog = subs.add_parser("backlog", parents=[ledger],
                              help="each repo's NICE_TO_HAVE.md against its build order")
    backlog.add_argument("repos", nargs="*", metavar="REPO",
                         help="a repo's directory; the default is the git top level")
    backlog.add_argument("--order", metavar="FILE",
                         help="one HANDOFF.md for every REPO: its steps whose `repo` cell "
                              "is the repo's name less `agentik-`, or `suite`")
    backlog.add_argument("--json", action="store_true")

    expire = subs.add_parser("expire", parents=[ledger],
                             help="move closed and old S4 NICE items to history/NICE-overflow.md")
    expire.add_argument("repos", nargs="*", metavar="REPO",
                        help="a repo's directory; the default is the git top level")
    expire.add_argument("--order", metavar="FILE",
                        help="one HANDOFF.md for every REPO, as backlog takes it")
    expire.add_argument("--days", type=int, default=14, metavar="N",
                        help="an open S4 item older than N days expires; the default is 14")
    expire.add_argument("--write", action="store_true",
                        help="make the move; without it nothing is written")
    expire.add_argument("--json", action="store_true")

    analyze = subs.add_parser("analyze", parents=[ledger],
                              help="what a repo's history says: churn, from git; writes nothing")
    analyze.add_argument("repos", nargs="*", metavar="[churn] REPO",
                         help="the analysis, `churn`, then each repo's directory; the "
                              "default is every analysis of the git top level")
    analyze.add_argument("--since", default=None, metavar="Nd|YYYY-MM-DD",
                         help="the window's start, 00:00:00 UTC; the default is 14d before "
                              "--until")
    analyze.add_argument("--until", default=None, metavar="YYYY-MM-DD",
                         help="the window's end, 00:00:00 UTC; the default is now")
    analyze.add_argument("--json", action="store_true")

    audit = subs.add_parser("audit", parents=[ledger],
                            help="the ledger's retire and rewrite candidates; writes nothing")
    audit.add_argument("repos", nargs="*", metavar="REPO",
                       help="a repo of the tree P5 and P6 read; the default is the ledger's "
                            "git top")
    audit.add_argument("--tree", default=None, metavar="FILE",
                       help='a file {"repos": [{"name": N, "path": P}]} naming the tree\'s repos')
    audit.add_argument("--json", action="store_true")

    install = subs.add_parser("install-cli",
                              help="put this plugin's launcher on the terminal's PATH (GUIDE section 10)")
    install.add_argument("--prefix", default=None,
                         help="where bin/ and share/ go; the default is ~/.local")
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
        # the launcher's record of what Apple's python added, undone before any child (GUIDE 10)
        with contextlib.suppress(ImportError):
            import agentik_install
            agentik_install.restore_parent_env()
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
    if args.verb == "install-cli":
        return cmd_install_cli(args, out, err)
    try:
        if args.verb == "doctor":
            # `doctor` finds the ledger for itself and reports its absence as a check.
            return cmd_doctor(args, out, err)
        if args.verb == "backlog":
            # `backlog` reads NICE_TO_HAVE.md and HANDOFF.md, never a ledger.
            return cmd_backlog(args, out, err)
        if args.verb == "expire":
            # `expire` reads and writes NICE_TO_HAVE.md, never a ledger.
            return cmd_expire(args, out, err)
        if args.verb == "analyze":
            # `analyze` reads git and NICE_TO_HAVE.md, never a ledger.
            return cmd_analyze(args, out, err)
        path = locate(getattr(args, "ledger", None), os.getcwd())
        return VERBS[args.verb](args, path, out, err)
    except Refusal as exc:
        err.write("decisions: %s\n" % exc)
        return 2


def cmd_install_cli(args, out, err):
    """The canonical install-cli (agentik_install, beside the package in lib/): 0 or 1."""
    import agentik_install
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        return agentik_install.install_cli(args.prefix)


VERBS = {"show": cmd_show, "find": cmd_find, "new": cmd_new, "ask": cmd_ask,
         "answer": cmd_answer, "render": cmd_render, "doctor": cmd_doctor,
         "backlog": cmd_backlog, "expire": cmd_expire, "analyze": cmd_analyze, "audit": cmd_audit,
         "install-cli": cmd_install_cli}
