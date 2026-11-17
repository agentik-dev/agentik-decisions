"""Row sy3-sync R2: `install-cli --force` (commons' `install_cli(prefix, force=, takes_force=True)`).

A command install-cli placed in a temp prefix, its VERSION then raised above this plugin's, is a
newer command: install-cli leaves it with the one line commons' copy prints, which names
`--force`, and exits 0; with `--force` it places this plugin's tree over it. The prefix is a temp
dir, never the live home.
"""

import io
import os
import re
import shutil
import tempfile

import agentik_install
import decisions
from tests.hermetic import Hermetic

NEWER = "99.0.0"


class Force(Hermetic):

    def setUp(self):
        super().setUp()
        self.prefix = os.path.realpath(tempfile.mkdtemp(prefix="decisions-force-"))
        self.addCleanup(shutil.rmtree, self.prefix, True)
        self.launcher = os.path.join(self.prefix, "bin", "agentik-decisions")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        return decisions.main(list(argv), out=out, err=err), out.getvalue(), err.getvalue()

    def read(self):
        with open(self.launcher, encoding="utf-8") as handle:
            return handle.read()

    def newer_command(self):
        code, out, err = self.run_cli("install-cli", "--prefix", self.prefix)
        self.assertEqual(code, 0, out + err)
        text = self.read()
        raised = re.sub(r"(?m)^VERSION=.*$", "VERSION=%s" % NEWER, text, count=1)
        self.assertNotEqual(raised, text)
        with open(self.launcher, "w", encoding="utf-8") as handle:
            handle.write(raised)
        return raised

    def test_a_newer_command_is_left_with_one_line_naming_force(self):
        raised = self.newer_command()
        code, out, err = self.run_cli("install-cli", "--prefix", self.prefix)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Left %s at %s, newer than this plugin's %s; --force places it.\n"
                         % (self.launcher, NEWER, agentik_install.version()))
        self.assertEqual(self.read(), raised)

    def test_force_places_this_tree_over_a_newer_command(self):
        self.newer_command()
        code, out, err = self.run_cli("install-cli", "--prefix", self.prefix, "--force")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(out.startswith("Placed %s %s" % (self.launcher, agentik_install.version())), out)
        self.assertIn("\nVERSION=%s\n" % agentik_install.version(), self.read())

    def test_the_help_names_force(self):
        code, out, _ = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("install-cli [--prefix P] [--force]", out)
        code, out, _ = self.run_cli("install-cli", "--help")
        self.assertEqual(code, 0)
        self.assertIn("--force", out)


if __name__ == "__main__":
    import unittest
    unittest.main()
