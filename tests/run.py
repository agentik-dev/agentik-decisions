#!/usr/bin/env python3
"""The suite, refusing an unlisted skip (ADV6-5).

    tests/run.py [--skips-allow FILE] [module ...]

Discovers `tests` from `.` when no module is named, runs it with
`TextTestRunner(verbosity=1)`, then prints `skips: <n> allowed`, or one
`skips: <reason> counted <n>, pinned <m>` line per miss and exits 1.  Each
`tests/skips.allow` line pins `<count> <reason>` (ADV10-4): under discovery
every count matches exactly, in either direction; a named-module run counts
at most the pin.  A line without a count, or a failing suite, exits 1 too.
Every expected failure and unexpected success prints one `expected: <test id>
is an expected failure|an unexpected success` line and exits 1 (ADV11-5).
"""

import argparse
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gates import PYFLAKES_ABSENT, SKIPS_ALLOW, AllowError, read_allow


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run")
    parser.add_argument("--skips-allow", dest="skips_allow", default=SKIPS_ALLOW)
    parser.add_argument("modules", nargs="*")
    args = parser.parse_args(argv)
    # module names resolve from `.`, as discovery's top level does
    sys.path.insert(0, os.getcwd())
    loader = unittest.TestLoader()
    if args.modules:
        suite = loader.loadTestsFromNames(args.modules)
    else:
        suite = loader.discover("tests", top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.stderr.flush()
    try:
        pinned = read_allow(args.skips_allow)
    except AllowError as exc:
        print("skips: %s" % exc)
        return 1
    # pyflakes absent is the gates' skip, never the suite's
    pinned.pop(PYFLAKES_ABSENT, None)
    counted = {}
    for _test, reason in result.skipped:
        counted[reason] = counted.get(reason, 0) + 1
    misses = []
    for reason in sorted(set(counted) | set(pinned)):
        n, m = counted.get(reason, 0), pinned.get(reason, 0)
        if n > m or (n < m and not args.modules):
            misses.append("skips: %s counted %d, pinned %d" % (reason, n, m))
    for test, _trace in result.expectedFailures:
        misses.append("expected: %s is an expected failure" % test.id())
    for test in result.unexpectedSuccesses:
        misses.append("expected: %s is an unexpected success" % test.id())
    for line in misses:
        print(line)
    if not misses:
        print("skips: %d allowed" % len(result.skipped))
    return 0 if result.wasSuccessful() and not misses else 1


if __name__ == "__main__":
    sys.exit(main())
