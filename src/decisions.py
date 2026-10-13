#!/usr/bin/env python3
"""decisions - the checkout runner for the package src/decisions/.

Run as a script, sys.path[0] is src/, where the package wins over this file.
"""

import sys

from decisions.cli import main

if __name__ == "__main__":
    sys.exit(main())
