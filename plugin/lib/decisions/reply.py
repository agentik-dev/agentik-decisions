"""`reply`: the owner's answer typed onto question N's own answer line (packet in5a).

    reply N (--pick L | --say T) [--dry-run] [--yes]

Writes the text after **Your answer:** on block N's answer line in the OPEN-QUESTIONS.md
beside the ledger, one space between, and nothing else in either file: no entry, no
Proposed line moved, no Answered line, the base line as it was, every other block as it
was. `--pick L` names one option as `answer` matches the owner's typed text (case,
` (Recommended)`, a period and `*` or backticks at either end dropped) and writes its label
as the block spells it; `--say T` writes T, its blanks at either end cut, one line of at
most 2,000 bytes with no control character; T is empty when it holds no character outside
the spaces, controls and format characters. The read, the checks and the write run under
`.new.lock`, as `new` takes it; the write is one rename beside the file, every line end as
it was read, and no git runs.

Refused, exit 1, nothing written: no questions file, no block N, a block whose answer
line holds text or that holds a non-blank line under it (`answer N` is the sitting's next
step), a block with no base line or more than one, a lint problem of block N, an option
L does not name or names twice, a T that is empty, holds a line break or a control
character or is over the bound, a held lock. A line the owner typed above the answer
line does not stop it: `answer` reads it as it does today. `--dry-run` makes every check
and prints the line before and after; without `--yes` the verb shows them and asks once
on a terminal (`y` or `yes` writes), and refuses where stdin is no terminal. It is the
owner's verb at a terminal: a sitting enters the answer with `answer`.
"""

import os
import sys
import unicodedata

from . import answer, ask, questions
from .common import Refusal, commit_texts, disk_text, held, records_of
from .ledger import display

__all__ = ["cmd_reply", "plan", "said", "SAY_MAX", "DONE"]

SAY_MAX = 2000
YES = ("y", "yes")
DONE = ("question %d: your answer is on its line; the sitting enters it with agentik "
        "decisions answer %d\n")


def breaks(char):
    """True when `char` ends a line for `str.splitlines`, as the parser splits."""
    return len(("a%sb" % char).splitlines()) > 1


def unseen(char):
    """True for a space, a line or paragraph separator, a control or a format character:
    one that shows nothing on the answer line (review 1 F1)."""
    return unicodedata.category(char) in ("Zs", "Zl", "Zp", "Cc", "Cf")


def said(number, text):
    """`--say`'s T, its blanks at either end cut (`str.strip`), or a Refusal (R4); a T
    with no character outside the spaces, controls and format characters is empty."""
    text = text.strip()
    where = "reply: question %d:" % number
    if all(unseen(c) for c in text):
        raise Refusal("%s an empty --say; nothing written" % where)
    if any(breaks(c) for c in text):
        raise Refusal("%s --say holds a newline; the answer is one line; nothing written"
                      % where)
    if any(unicodedata.category(c) == "Cc" for c in text):
        raise Refusal("%s --say holds a control character; nothing written" % where)
    size = len(text.encode("utf-8"))
    if size > SAY_MAX:
        raise Refusal("%s --say is %d bytes, over 2,000 bytes; nothing written"
                      % (where, size))
    return text


def picked(block, wanted):
    """The option label `--pick` names, as the block spells it (R3), or a Refusal; the
    refusal shows each label it could name once in backticks, its own at either end
    dropped, never doubled (review 1)."""
    labels = [label for label, _marked, _effect in block.options]
    found = answer.named(block, wanted)
    if len(found) > 1:
        raise Refusal("reply: question %d: %r could name any of %s; pick one label as it "
                      "stands; nothing written"
                      % (block.number, wanted, ", ".join("`%s`" % l.strip("`") for l in found)))
    if not found:
        raise Refusal("reply: question %d has no option %r; its options are %s; nothing "
                      "written" % (block.number, wanted, ", ".join(labels)))
    return found[0]


def plan(path_q, number, args, say):
    """(the file's text as on disk, its text after, the line index, the line before, the
    line after), each check of R3 and R5 made, or a Refusal."""
    if not os.path.exists(path_q):
        raise Refusal("reply: question %d: no %s beside the ledger; nothing written"
                      % (number, display(path_q)))
    old = disk_text(path_q)
    parsed = questions.parse(old)
    found = [b for b in parsed.blocks if b.number == number]
    if not found:
        raise Refusal("reply: no open question %d in %s; nothing written"
                      % (number, display(path_q)))
    if len(found) > 1:
        raise Refusal("reply: question %d: %s holds %d blocks of that number; nothing written"
                      % (number, display(path_q), len(found)))
    block = found[0]
    if block.answer:
        raise Refusal("reply: question %d is answered already, on or under its %s line: %s; "
                      "the sitting enters it with agentik decisions answer %d; nothing written"
                      % (number, questions.ANSWER, block.answer, number))
    if block.base is None:
        raise Refusal("reply: question %d's block has no base line, or more than one, so its "
                      "own lines cannot be told from typed ones; nothing written" % number)
    head = "question %d: " % number
    own = [m[len(head):] for n, m in parsed.problems
           if n == block.start + 1 and m.startswith(head)]
    if own:
        raise Refusal("reply: question %d: the lint refuses its block: %s; nothing written"
                      % (number, "; ".join(own)))
    text = picked(block, args.pick) if args.pick is not None else say
    lines = old.splitlines(keepends=True)
    at = next(i for i in range(block.start + 1, block.stop)
              if lines[i].rstrip().startswith(questions.ANSWER))
    before = lines[at].rstrip("\r\n")
    after = "%s %s" % (questions.ANSWER, text)
    lines[at] = after + lines[at][len(before):]
    new = "".join(lines)
    again = [b for b in questions.parse(new).blocks if b.number == number]
    if (len(again) != 1 or not again[0].answer
            or again[0].answer != " ".join(text.split())):
        raise Refusal("reply: question %d: the line would not read back as typed; nothing "
                      "written" % number)
    return old, new, at, before, after


def shown(out, path_q, number, at, before, after):
    out.write("question %d, %s line %d:\n- %s\n+ %s\n" % (number, display(path_q), at + 1,
                                                         before, after))


def is_tty(stream):
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError, OSError):
        return False


def asked(number, stdin, err):
    """R7: one question on `err`; True for `y` or `yes`, any case."""
    err.write("write it on question %d's answer line? [y/N] " % number)
    err.flush()
    try:
        got = stdin.readline()
    except (EOFError, KeyboardInterrupt):
        got = ""
    if not got:
        err.write("\n")
    return got.strip().lower() in YES


def run(args, path, out, err):
    number = args.number
    say = said(number, args.say) if args.say is not None else None
    home = records_of(os.path.dirname(path), "reply", write=True)
    path_q = os.path.join(home, ask.QUESTIONS)
    lock = os.path.join(home, ask.LOCK)
    with held(lock, ask.NEW_WAIT, err):
        old, new, at, before, after = plan(path_q, number, args, say)
        if args.dry_run or args.yes:
            if args.dry_run:
                shown(out, path_q, number, at, before, after)
                out.write("reply: dry run, nothing written\n")
                return 0
            commit_texts([(path_q, new)], as_read=True)
            out.write(DONE % (number, number))
            return 0
    stdin = sys.stdin
    if not is_tty(stdin):
        raise Refusal("reply: question %d: stdin is no terminal, so reply cannot ask; run it "
                      "again with --yes; nothing written" % number)
    shown(out, path_q, number, at, before, after)
    out.flush()
    if not asked(number, stdin, err):
        raise Refusal("reply: question %d: declined; nothing written" % number)
    # the lock is not held while the owner reads: under it again, the file must be as shown
    with held(lock, ask.NEW_WAIT, err):
        now = plan(path_q, number, args, say)
        if now[0] != old:
            raise Refusal("reply: question %d: %s changed while you were asked; nothing "
                          "written" % (number, display(path_q)))
        commit_texts([(path_q, now[1])], as_read=True)
    out.write(DONE % (number, number))
    return 0


def cmd_reply(args, path, out, err):
    """R5: each refusal is exit 1, one line on `err`."""
    try:
        return run(args, path, out, err)
    except Refusal as exc:
        err.write("decisions: %s\n" % " ".join(str(exc).split()))
        return 1
