#!/usr/bin/env python3
"""decisions - the checkout runner for the package plugin/lib/decisions/.

A dev script, never shipped: the plugin runs plugin/lib/agentik-decisions. Run
as a script, sys.path[0] is src/, where this file would shadow the package, so
plugin/lib/ goes first.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                                "plugin", "lib"))

from decisions.cli import main  # noqa: E402  the package, after its path

if __name__ == "__main__":
    sys.exit(main())
