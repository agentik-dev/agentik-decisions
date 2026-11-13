"""`questions`: each repo's OPEN-QUESTIONS.md as one read (packet in1, hq design/17 row in1).

    agentik-decisions questions [REPO...] [--json]

A REPO is a directory, by default the git top of the working directory, else the
working directory; its file is REPO/OPEN-QUESTIONS.md. A REPO that is no directory,
holds no such file, or whose file is not UTF-8 is skipped with its reason and the
read goes on. Each question is read from `questions.parse`'s block and judged in the
order `ask` judges it (`selector.skipped`): answered on its answer line, else
unreadable (the lint names it, or it has no base line or more than one), else
answered above its answer line (`answer.since`), else open. Its Proposed date is
read from the DECISIONS.md beside the file. It takes no lock, renders nothing, starts
no model, runs no git but `git_top` for the default REPO, and writes nothing. Exit 0
whenever the read ran; `render --lint` stays the check.
"""

import datetime
import json
import os
import re

from . import answer, ledger, questions
from .common import Refusal, git_top

__all__ = ["cmd_questions", "read_repo", "SCHEMA"]

SCHEMA = "agentik.questions/1"
NO_DIR, NO_FILE, UNREADABLE = "not a directory", "no OPEN-QUESTIONS.md", "unreadable"
TYPED_ON = "typed on the answer line"
TYPED_ABOVE = "typed above the answer line"
NO_BASE = "no base line, or more than one"
STAMP = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")


def today():
    return datetime.date.today().isoformat()


def proposed_dates(path):
    """{N: the first date of the final parenthetical of Proposed line N} of the ledger at
    `path`; {} when it is absent or cannot be read (R8: never a refusal)."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return {}
    dates = {}
    for entry in ledger.parse(text, path).entries:
        if entry.section != ledger.PROPOSED or entry.number in dates:
            continue
        found = ledger.DATE.search(ledger.final_parenthetical(entry.body) or "")
        dates[entry.number] = found.group(0) if found else None
    return dates


def block_problems(block, problems):
    """The lint's messages that name `block`, their `question N: ` head cut."""
    head = "question %d: " % block.number
    return [m[len(head):] for n, m in problems if n == block.start + 1 and m.startswith(head)]


def judged(block, own, above):
    """(state, why) in `selector.skipped`'s order (R7)."""
    if block.answer:
        return "answered", TYPED_ON
    if own:
        return "unreadable", "; ".join(own)
    if block.base is None:
        return "unreadable", NO_BASE
    if above:
        return "answered", TYPED_ABOVE
    return "open", None


def question(block, problems, dates):
    own = block_problems(block, problems)
    above = answer.since(block) if block.base is not None else []
    state, why = judged(block, own, above)
    options = [{"label": label, "effect": effect, "recommended": marked}
               for label, marked, effect in block.options]
    recommended = next((o["label"] for o in options if o["recommended"]), None)
    labels = questions.LABELS
    return {"n": block.number, "title": block.title, "line": block.start + 1, "state": state,
            "why": why, "proposed": dates.get(block.number), "recommended": recommended,
            "options": options,
            "parts": {"stands": block.parts.get(labels[0]), "choice": block.parts.get(labels[1]),
                      "recommendation": block.parts.get(labels[3])},
            "typed": block.answer or "", "typed_above": above, "base": block.base is not None,
            "problems": own, "text": block.text}


def bullets(rows):
    return [text for _n, text in rows if text.startswith("- ")]


def is_day(stamp):
    """True when `stamp` names a day of the calendar (F1)."""
    try:
        datetime.date.fromisoformat(stamp)
    except ValueError:
        return False
    return True


def read_repo(repo):
    """(the repo's object, None) or (None, why it is skipped)."""
    if not os.path.isdir(repo):
        return None, NO_DIR
    path = os.path.join(repo, questions.NAME)
    if not os.path.isfile(path):
        return None, NO_FILE
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return None, UNREADABLE
    parsed = questions.parse(text)
    dates = proposed_dates(os.path.join(repo, ledger.NAME))
    decided = bullets(parsed.decided)
    now = today()
    stamps = [d for line in decided for d in STAMP.findall(line) if is_day(d) and d <= now]
    return {"repo": repo, "file": os.path.realpath(path),
            "questions": [question(b, parsed.problems, dates) for b in parsed.blocks],
            "answered": len(bullets(parsed.answered)),
            "decided": {"count": len(decided), "newest": max(stamps) if stamps else None},
            "problems": [{"line": n, "message": m} for n, m in parsed.problems]}, None


def loose_problems(view):
    """The repo's problems that name no block."""
    named = set()
    for q in view["questions"]:
        head = "question %d: " % q["n"]
        named.update((q["line"], head + m) for m in q["problems"])
    return [p for p in view["problems"] if (p["line"], p["message"]) not in named]


def as_text(view):
    decided = view["decided"]
    head = "== %s  %d open, %d answered, %d decided without asking" % (
        os.path.basename(view["repo"]), len(view["questions"]), view["answered"],
        decided["count"])
    if decided["newest"]:
        head += ", newest %s" % decided["newest"]
    lines = [head]
    for q in view["questions"]:
        line = "%d  %s  %s" % (q["n"], q["state"], q["title"])
        if q["recommended"] is not None:
            line += "  recommended: %s" % q["recommended"]
        for extra in (("proposed %s" % q["proposed"]) if q["proposed"] else None, q["why"]):
            if extra:
                line += "; %s" % extra
        lines.append(line)
    for p in loose_problems(view):
        lines.append("problem  %s:%d  %s" % (questions.NAME, p["line"], p["message"]))
    return lines


def read_all(names):
    """(the repos' objects, the skipped ones), in the order named."""
    repos, skipped = [], []
    for name in names:
        repo = os.path.realpath(name)
        view, why = read_repo(repo)
        if view is None:
            skipped.append({"repo": repo, "why": why})
        else:
            repos.append(view)
    return repos, skipped


def cmd_questions(args, out, err):
    as_json = getattr(args, "json", False)
    try:
        names = list(getattr(args, "repos", None) or [])
        if not names:
            here = os.getcwd()
            names = [git_top(here) or here]
        repos, skipped = read_all(names)
    except Refusal as exc:
        if not as_json:
            raise
        out.write(json.dumps({"schema": SCHEMA, "ok": False, "error": {
            "code": "refused", "message": str(exc), "remedy": None}}, indent=2) + "\n")
        return 2
    if as_json:
        out.write(json.dumps({"schema": SCHEMA, "ok": True, "repos": repos,
                              "skipped": skipped}, indent=2) + "\n")
        return 0
    blocks = ["\n".join(as_text(view)) for view in repos]
    reasons = []
    for s in skipped:
        if s["why"] not in reasons:
            reasons.append(s["why"])
    tail = ["skipped (%s): %s" % (why, ", ".join(os.path.basename(s["repo"]) for s in skipped
                                                 if s["why"] == why)) for why in reasons]
    if tail:
        blocks.append("\n".join(tail))
    out.write("\n\n".join(blocks) + ("\n" if blocks else ""))
    return 0
