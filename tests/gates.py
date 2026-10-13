#!/usr/bin/env python3
"""Gates run by `make check`: the shebang, 3.12 syntax over src/ and tests/, and
pyflakes.  Exit 0 when every gate holds, 1 when one refuses.  Pyflakes absent is
a skip, and a skip passes only when `tests/skips.allow` lists its reason (ADV6-5)
with a count (ADV10-4).

    tests/gates.py [--skips-allow FILE]
"""

import argparse
import ast
import io
import os
import sys

ROOTS = ("src", "tests")
SKIPS_ALLOW = "tests/skips.allow"
PYFLAKES_ABSENT = "pyflakes absent"


class AllowError(Exception):
    """A `skips.allow` line with no leading count (ADV10-4)."""


def read_allow(path):
    """{reason: count} of `path`: `<count> <reason>` lines, `#` comments; empty if absent.

    A line without a leading count is an AllowError `<path>:<n>: no count`."""
    try:
        lines = io.open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return {}
    allowed = {}
    for number, line in enumerate(lines, 1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        count, _sep, reason = text.partition(" ")
        if not count.isdigit() or not reason.strip():
            raise AllowError("%s:%d: no count" % (path, number))
        allowed[reason.strip()] = int(count)
    return allowed


def shebang_gate():
    first = io.open("src/decisions.py", encoding="utf-8").readline().rstrip("\n")
    if first != "#!/usr/bin/env python3":
        sys.stderr.write("gate: src/decisions.py line 1 is %r, want '#!/usr/bin/env python3'\n" % first)
        return 1
    print("gate: shebang ok")
    return 0


def sources():
    for root in ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in sorted(filenames):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def syntax_gate():
    bad = 0
    for path in sources():
        text = io.open(path, encoding="utf-8").read()
        try:
            ast.parse(text, filename=path, feature_version=(3, 12))
        except SyntaxError as exc:
            sys.stderr.write("gate: %s is not 3.12-compatible: %s\n" % (path, exc))
            bad += 1
    if bad:
        return 1
    print("gate: 3.12 syntax ok")
    return 0


def pyflakes_gate(skips_allow=SKIPS_ALLOW):
    try:
        from pyflakes import api, reporter
    except ImportError:
        try:
            allowed = read_allow(skips_allow)
        except AllowError as exc:
            sys.stderr.write("gate: %s\n" % exc)
            return 1
        if PYFLAKES_ABSENT in allowed:
            print("gate: %s, allowed by %s" % (PYFLAKES_ABSENT, skips_allow))
            return 0
        sys.stderr.write("gate: %s, not in %s\n" % (PYFLAKES_ABSENT, skips_allow))
        return 1
    found = 0
    rep = reporter.Reporter(sys.stdout, sys.stderr)
    for root in ROOTS:
        found += api.checkRecursive([root], rep)
    if found:
        sys.stderr.write("gate: pyflakes reported %d\n" % found)
        return 1
    print("gate: pyflakes ok")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="gates")
    parser.add_argument("--skips-allow", dest="skips_allow", default=SKIPS_ALLOW)
    args = parser.parse_args(argv)
    status = shebang_gate() | syntax_gate()
    return status | pyflakes_gate(args.skips_allow)


if __name__ == "__main__":
    sys.exit(main())
