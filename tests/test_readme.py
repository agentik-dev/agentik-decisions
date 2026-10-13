"""The public README: the icon, the render path (scripts/readme-render) and the shape.

No test opens the installed respeak plugin or a path outside this checkout: the
render tests run the script in a temp copy under a fake plugin root.
"""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
ICON = REPO / "assets" / "icon.svg"
IMG = '<img src="assets/icon.svg" alt="" width="56" align="left">'
DOCS = (REPO / "README.md", REPO / "design" / "readme" / "source.md")
MANIFEST = REPO / "plugin" / ".claude-plugin" / "plugin.json"
STATUS = re.compile(r"^Status: version `([^`]+)`, rendered `\d{4}-\d\d-\d\d`, "
                    r"`(\d+)` unittest cases\.$", re.M)
SCRIPT = REPO / "scripts" / "readme-render"

# the fake renderer copies --source to --out and names its own plugin root
FAKE_RENDER = """#!/bin/bash
while [ $# -gt 0 ]; do
  case "$1" in --source) S="$2"; shift 2 ;; --out) O="$2"; shift 2 ;; *) shift ;; esac
done
echo "fake-render depth=$RESPEAK_DEPTH root=$(cd "$(dirname "$0")/.." && pwd)"
cp "$S" "$O"
"""
# the fake verifier exits by FAKE_VERIFY_EXIT
FAKE_VERIFY = "import os, sys\nsys.exit(int(os.environ.get('FAKE_VERIFY_EXIT', '0')))\n"
SOURCE = """# fake

<img src="assets/icon.svg" alt="" width="56" align="left">

A fake repo.

## Status

Status: version `0.0.0`, rendered `2000-01-01`, `0` unittest cases.

## License

MIT.
"""


class Icon(unittest.TestCase):
    """The plugin family's rules: a 64-box, monoline currentColor, plain SVG."""

    def setUp(self):
        self.svg = ICON.read_text(encoding="utf-8")

    def test_under_1500_bytes(self):
        self.assertLess(ICON.stat().st_size, 1500)

    def test_the_64_box(self):
        self.assertIn('viewBox="0 0 64 64"', self.svg)

    def test_accessible(self):
        self.assertIn('role="img"', self.svg)
        self.assertIn('aria-label="decisions"', self.svg)
        self.assertIn("<title>decisions</title>", self.svg)

    def test_monoline_current_color(self):
        self.assertIn('stroke="currentColor"', self.svg)
        self.assertIn('stroke-width="3"', self.svg)
        self.assertIn('stroke-linecap="round"', self.svg)
        self.assertIn('stroke-linejoin="round"', self.svg)
        fills = set(re.findall(r'fill="([^"]*)"', self.svg))
        self.assertLessEqual(fills, {"none", "#fff"})

    def test_plain(self):
        # a gradient dies on a zero-extent stroke bbox; nothing runs or loads
        for banned in ("Gradient", "<filter", "<script", "href", "<image",
                       "url(", "@import", "on"):
            with self.subTest(banned=banned):
                if banned == "on":
                    self.assertNotRegex(self.svg, r"\son\w+=")
                else:
                    self.assertNotIn(banned, self.svg)

    def test_line_3_of_both_files(self):
        for doc in DOCS:
            with self.subTest(doc=doc.name):
                lines = doc.read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines[2], IMG)

    def test_no_png(self):
        self.assertEqual(list((REPO / "assets").glob("*.png")), [])


def fake_plugin(root):
    """A plugin root holding the fake renderer and verifier."""
    scripts = Path(root) / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "respeak-render.sh").write_text(FAKE_RENDER)
    (scripts / "respeak-verify-edit.py").write_text(FAKE_VERIFY)
    return str(root)


def load_script():
    """scripts/readme-render as a module, its main not run."""
    from importlib.machinery import SourceFileLoader
    import importlib.util
    loader = SourceFileLoader("readme_render", str(SCRIPT))
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("readme_render", loader))
    loader.exec_module(module)
    return module


class Render(unittest.TestCase):
    """scripts/readme-render in a temp repo under a fake plugin root."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = self.tmp / "repo"
        (self.repo / "design" / "readme").mkdir(parents=True)
        (self.repo / "plugin" / ".claude-plugin").mkdir(parents=True)
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "__init__.py").write_text("")
        (self.repo / "tests" / "test_two.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n"
            "    def test_a(self): pass\n    def test_b(self): pass\n")
        (self.repo / "plugin" / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "fake", "version": "9.8.7"}))
        (self.repo / "design" / "readme" / "source.md").write_text(SOURCE)
        (self.repo / "design" / "readme" / "contract.txt").write_text("notes\n")
        self.root = fake_plugin(self.tmp / "plugin-root")

    def run_script(self, *extra, verify="0", depth=None, more_env=None):
        env = {k: v for k, v in os.environ.items() if k != "RESPEAK_DEPTH"}
        env["FAKE_VERIFY_EXIT"] = verify
        env.update(more_env or {})
        if depth:
            env["RESPEAK_DEPTH"] = depth
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo),
             "--python", sys.executable] + list(extra),
            env=env, capture_output=True, text=True)

    def written(self):
        return sorted(p.name for p in self.repo.rglob("*")
                      if p.is_file() and "__pycache__" not in p.parts)

    def test_happy_path_stamps_two_lines(self):
        run = self.run_script("--plugin-root", self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("depth=1", run.stdout)
        readme = (self.repo / "README.md").read_text()
        self.assertRegex(readme, r"Status: version `9\.8\.7`, rendered "
                         r"`\d{4}-\d\d-\d\d`, `2` unittest cases\.")
        self.assertEqual(readme, (self.repo / "design/readme/source.md").read_text())
        sidecar = (self.repo / "design/readme/rendered.sha256").read_text().splitlines()
        self.assertEqual(len(sidecar), 2)
        self.assertTrue(sidecar[0].endswith("  design/readme/source.md"))
        self.assertTrue(sidecar[1].endswith("  README.md"))
        check = subprocess.run(["shasum", "-a", "256", "-c", "--status",
                                "design/readme/rendered.sha256"], cwd=self.repo)
        self.assertEqual(check.returncode, 0)

    def test_a_hung_render_is_refused_and_leaves_no_temp(self):
        # ADV10-6: the render has a wall; its temp goes with the refusal
        from importlib.machinery import SourceFileLoader
        import importlib.util
        loader = SourceFileLoader("readme_render", str(SCRIPT))
        spec = importlib.util.spec_from_loader("readme_render", loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        (Path(self.root) / "scripts" / "respeak-render.sh").write_text(
            "#!/bin/bash\nexec sleep 30\n")
        source = (self.repo / "design/readme/source.md").read_text()
        err = io.StringIO()
        with mock.patch.object(module, "RENDER_WALL", 1), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = module.main(["--repo", str(self.repo), "--python", sys.executable,
                                "--plugin-root", self.root])
        self.assertEqual(code, 2)
        self.assertIn("respeak-render.sh took over 1 s", err.getvalue())
        self.assertEqual(list(self.repo.glob(".readme-*.md")), [])
        self.assertFalse((self.repo / "README.md").exists())
        self.assertEqual((self.repo / "design/readme/source.md").read_text(), source)

    def test_no_status_line_writes_nothing(self):
        source = self.repo / "design/readme/source.md"
        source.write_text(SOURCE.replace("Status: version", "Version"))
        before, files = source.read_text(), self.written()
        run = self.run_script("--plugin-root", self.root)
        self.assertEqual(run.returncode, 2)
        self.assertIn("status line", run.stderr)
        self.assertEqual(source.read_text(), before)
        self.assertEqual(self.written(), files)

    def test_failing_verifier_writes_nothing(self):
        before, files = SOURCE, self.written()
        run = self.run_script("--plugin-root", self.root, verify="1")
        self.assertEqual(run.returncode, 2)
        self.assertIn("verifier", run.stderr)
        self.assertEqual((self.repo / "design/readme/source.md").read_text(), before)
        self.assertEqual([f for f in self.written() if f != ".readme-refused.md"], files)

    def test_refused_render_is_kept_and_named(self):
        # D20 ruling 1: the verifier's refusal keeps the render, and stderr names it
        files = self.written()
        run = self.run_script("--plugin-root", self.root, verify="1")
        self.assertEqual(run.returncode, 2)
        self.assertEqual(self.written(), sorted(files + [".readme-refused.md"]))
        kept = (self.repo / ".readme-refused.md").read_text()
        self.assertRegex(kept, r"Status: version `9\.8\.7`, rendered "
                         r"`\d{4}-\d\d-\d\d`, `2` unittest cases\.")
        self.assertEqual(STATUS.sub("", kept), STATUS.sub("", SOURCE))
        self.assertIn("readme-render: the refused render is .readme-refused.md; "
                      "diff README.md .readme-refused.md", run.stderr)
        self.assertFalse((self.repo / "README.md").exists())

    def test_style_gate_failure_keeps_no_refused_render(self):
        # D20 ruling 2: only the verifier's refusal keeps a render
        refused = ".readme-refused.md"
        (Path(self.root) / "scripts" / "respeak-render.sh").write_text(FAKE_RENDER + "exit 1\n")
        files = self.written()
        run = self.run_script("--plugin-root", self.root, verify="1")
        self.assertEqual(run.returncode, 1)
        self.assertIn("style gate", run.stderr)
        self.assertFalse((self.repo / refused).exists())
        self.assertEqual(list(self.repo.glob(".readme-*.md")), [])
        self.assertEqual(self.written(), files)

    def test_a_pass_removes_a_stale_refused_render(self):
        # D20 ruling 3: the refused file never outlives the render it describes
        self.assertEqual(self.run_script("--plugin-root", self.root, verify="1").returncode, 2)
        self.assertTrue((self.repo / ".readme-refused.md").is_file())
        run = self.run_script("--plugin-root", self.root)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((self.repo / "README.md").is_file())
        self.assertEqual(list(self.repo.glob(".readme-*.md")), [])

    def in_process(self, **walls):
        """(exit, stderr) of the script's main run in this process, its walls lowered."""
        module, err = load_script(), io.StringIO()
        with contextlib.ExitStack() as stack:
            for name, value in walls.items():
                stack.enter_context(mock.patch.object(module, name, value))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(contextlib.redirect_stderr(err))
            code = module.main(["--repo", str(self.repo), "--python", sys.executable,
                                "--plugin-root", self.root])
        return code, err.getvalue()

    def fake(self, render=FAKE_RENDER, verify=FAKE_VERIFY):
        (Path(self.root) / "scripts" / "respeak-render.sh").write_text(render)
        (Path(self.root) / "scripts" / "respeak-verify-edit.py").write_text(verify)

    def test_a_refused_path_that_is_a_directory(self):
        # D20 left open: a directory at .readme-refused.md is refused by name with exit 2,
        # README.md and the sidecar unwritten, on a refusal and on a pass alike
        (self.repo / ".readme-refused.md").mkdir()
        files = self.written()
        for verify in ("1", "0"):
            with self.subTest(verify=verify):
                run = self.run_script("--plugin-root", self.root, verify=verify)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn(".readme-refused.md", run.stderr)
                self.assertNotIn("Traceback", run.stderr)
                self.assertTrue((self.repo / ".readme-refused.md").is_dir())
                self.assertEqual(self.written(), files)
                self.assertEqual((self.repo / "design/readme/source.md").read_text(), SOURCE)

    def test_verifier_timeout_keeps_no_refused_render(self):
        # D20 mutant: a verifier past its wall keeps no render
        self.fake(verify="import time\ntime.sleep(30)\n")
        code, err = self.in_process(VERIFY_WALL=1)
        self.assertEqual(code, 2)
        self.assertIn("respeak-verify-edit.py took over 1 s", err)
        self.assertFalse((self.repo / ".readme-refused.md").exists())
        self.assertEqual(list(self.repo.glob(".readme-*.md")), [])
        self.assertFalse((self.repo / "README.md").exists())

    def test_a_renderer_exit_3_keeps_no_refused_render(self):
        # D20 mutant: a renderer exit other than 0 and 1 keeps no render
        self.fake(render=FAKE_RENDER + "exit 3\n")
        files = self.written()
        run = self.run_script("--plugin-root", self.root, verify="1")
        self.assertEqual(run.returncode, 2)
        self.assertIn("the renderer exited 3", run.stderr)
        self.assertFalse((self.repo / ".readme-refused.md").exists())
        self.assertEqual(self.written(), files)

    def test_a_refusal_replaces_an_old_refused_render(self):
        # D20 mutant: a refusal replaces an older .readme-refused.md with its own render
        (self.repo / ".readme-refused.md").write_text("old\n")
        run = self.run_script("--plugin-root", self.root, verify="1")
        self.assertEqual(run.returncode, 2)
        kept = (self.repo / ".readme-refused.md").read_text()
        self.assertNotEqual(kept, "old\n")
        self.assertEqual(STATUS.sub("", kept), STATUS.sub("", SOURCE))
        self.assertEqual(list(self.repo.glob(".readme-*.md")), [self.repo / ".readme-refused.md"])

    def test_a_later_failure_removes_a_stale_refused_render(self):
        # L69: a stale .readme-refused.md never outlives a later run that failed another way
        cases = (("style gate", dict(render=FAKE_RENDER + "exit 1\n"), 1),
                 ("renderer exit 3", dict(render=FAKE_RENDER + "exit 3\n"), 2),
                 ("verifier timeout", dict(verify="import time\ntime.sleep(30)\n"), 2))
        for name, scripts, want in cases:
            with self.subTest(case=name):
                (self.repo / ".readme-refused.md").write_text("old\n")
                self.fake(**scripts)
                code, err = self.in_process(VERIFY_WALL=1)
                self.assertEqual(code, want, err)
                self.assertFalse((self.repo / ".readme-refused.md").exists())
                self.assertEqual(list(self.repo.glob(".readme-*.md")), [])
                self.assertFalse((self.repo / "README.md").exists())

    def test_depth_set_refuses(self):
        run = self.run_script("--plugin-root", self.root, depth="1")
        self.assertEqual(run.returncode, 2)
        self.assertIn("RESPEAK_DEPTH", run.stderr)
        self.assertFalse((self.repo / "README.md").exists())

    def helper_env(self, depth):
        # relay-r1 §10: the markers a sitting gives its helper, HOME and XDG in temp dirs
        env = {"RELAY_ROW": "d99-x", "CLAUDE_SESSION_MAX_TURNS": "40",
               "CLAUDE_SESSION_DEPTH": depth, "KEEP_ME": "1"}
        for name in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
            env[name] = str(self.tmp / name.lower())
        return env

    def test_renderer_runs_as_a_marked_helper(self):
        # relay-r1 §10: the render runs as CLAUDE_SESSION_DEPTH=d+1 CLAUDE_SESSION_HELPER=1,
        # keeps RELAY_ROW and CLAUDE_SESSION_MAX_TURNS, and its `claude -p` has --max-turns;
        # the count and the verifier, the sitting's own steps, keep the sitting's depth.
        seen = {step: self.tmp / ("%s.env" % step) for step in ("count", "render", "verify")}
        argv = self.tmp / "claude.argv"
        dump = ("import os\nopen(%r, 'w').write('\\n'.join("
                "'%%s=%%s' %% kv for kv in os.environ.items()))\n")
        (self.repo / "tests" / "test_two.py").write_text(
            dump % str(seen["count"]) + "import unittest\nclass T(unittest.TestCase):\n"
            "    def test_a(self): pass\n    def test_b(self): pass\n")
        scripts = Path(self.root) / "scripts"
        (scripts / "respeak-render.sh").write_text(FAKE_RENDER.replace(
            'cp "$S" "$O"', 'cp "$S" "$O"\nenv > "%s"\n"${RESPEAK_RENDER_CMD:-claude}" -p '
            '--model m --add-dir a b < /dev/null' % seen["render"]))
        (scripts / "respeak-verify-edit.py").write_text(dump % str(seen["verify"]))
        bin_dir = self.tmp / "bin"  # a fake claude first on PATH: no live claude
        bin_dir.mkdir()
        (bin_dir / "claude").write_text('#!/bin/sh\nprintf "%%s\\n" "$@" > "%s"\n' % argv)
        (bin_dir / "claude").chmod(0o755)
        more = dict(self.helper_env("1"), PATH="%s:%s" % (bin_dir, os.environ["PATH"]))
        run = self.run_script("--plugin-root", self.root, more_env=more)
        self.assertEqual(run.returncode, 0, run.stderr)
        env = {step: dict(line.split("=", 1) for line in path.read_text().splitlines()
                          if "=" in line) for step, path in seen.items()}
        self.assertEqual(env["render"]["CLAUDE_SESSION_DEPTH"], "2")
        self.assertEqual(env["render"]["CLAUDE_SESSION_HELPER"], "1")
        self.assertEqual(env["render"]["RELAY_ROW"], "d99-x")
        self.assertEqual(env["render"]["CLAUDE_SESSION_MAX_TURNS"], "40")
        self.assertEqual(env["render"]["KEEP_ME"], "1")
        for step in ("count", "verify"):
            self.assertEqual(env[step]["CLAUDE_SESSION_DEPTH"], "1")
            self.assertNotIn("CLAUDE_SESSION_HELPER", env[step])
            self.assertEqual(env[step]["RELAY_ROW"], "d99-x")
        args = argv.read_text().splitlines()
        self.assertEqual(args[0], "-p")
        self.assertIn("--max-turns", args)
        self.assertTrue(args[args.index("--max-turns") + 1].isdigit())

    def test_renderer_helper_refused_past_depth_2(self):
        # relay-r1 §10: a helper is refused past depth 2 (and a malformed depth with it),
        # before the source is stamped: the fake renderer never runs, nothing is written.
        ran = self.tmp / "render.ran"
        (Path(self.root) / "scripts" / "respeak-render.sh").write_text(
            FAKE_RENDER.replace('cp "$S" "$O"', 'cp "$S" "$O"\ntouch "%s"' % ran))
        files = self.written()
        for depth in ("2", "3", "x", "-1"):
            with self.subTest(depth=depth):
                run = self.run_script("--plugin-root", self.root,
                                      more_env=self.helper_env(depth))
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertIn("CLAUDE_SESSION_DEPTH", run.stderr)
                self.assertFalse(ran.exists())
                self.assertEqual((self.repo / "design/readme/source.md").read_text(), SOURCE)
                self.assertEqual(self.written(), files)

    def test_cache_picks_the_highest_version_tuple(self):
        cache = self.tmp / "cache"
        fake_plugin(cache / "respeak" / "respeak" / "0.6.0")
        fake_plugin(cache / "claude-code-respeak" / "respeak" / "0.6.1")
        run = self.run_script("--cache", str(cache))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("claude-code-respeak/respeak/0.6.1", run.stdout)
        self.assertNotIn("0.6.0", run.stdout)

    def test_empty_cache_refuses(self):
        run = self.run_script("--cache", str(self.tmp / "none"))
        self.assertEqual(run.returncode, 2)
        self.assertFalse((self.repo / "README.md").exists())


class Shape(unittest.TestCase):
    """The README and its source: the status line, the headings, the size, no private path."""

    def test_one_status_line_each_with_the_version_and_the_live_count(self):
        version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
        live = unittest.TestLoader().discover(
            str(REPO / "tests"), top_level_dir=str(REPO)).countTestCases()
        for doc in DOCS:
            with self.subTest(doc=doc.name):
                found = STATUS.findall(doc.read_text(encoding="utf-8"))
                self.assertEqual(len(found), 1)
                self.assertEqual(found[0][0], version)
                # A builder adds tests but never renders (d11): the README may lag the
                # suite, loudly, until the next `make readme`; it never overclaims.
                counted = int(found[0][1])
                self.assertLessEqual(counted, live)
                if counted < live:
                    sys.stderr.write("readme: %s counts %d tests, the suite has %d; "
                                     "make readme at the next render\n"
                                     % (doc.name, counted, live))

    def test_status_line_first_under_status(self):
        for doc in DOCS:
            with self.subTest(doc=doc.name):
                lines = doc.read_text(encoding="utf-8").splitlines()
                i = lines.index("## Status")
                under = [line for line in lines[i + 1:] if line.strip()][0]
                self.assertRegex(under, STATUS)

    def test_headings_equal(self):
        heads = [[line for line in doc.read_text(encoding="utf-8").splitlines()
                  if line.startswith("## ")] for doc in DOCS]
        self.assertEqual(heads[0], heads[1])

    def test_source_size(self):
        self.assertLessEqual(DOCS[1].stat().st_size, 24576)

    def test_no_word_of_the_per_file_format(self):
        """A13: the README, its source and CLAUDE.md name no record, tag, index or hook."""
        banned = re.compile(r"\b(records?|tags?|index|hooks?)\b", re.I)
        for doc in DOCS + (REPO / "CLAUDE.md",):
            with self.subTest(doc=doc.name):
                self.assertEqual(banned.findall(doc.read_text(encoding="utf-8")), [])

    def test_no_private_or_sibling_path(self):
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            for banned in ("../", "/Users/", "example-app", "claude-code-agents", "agent-relay"):
                with self.subTest(doc=doc.name, banned=banned):
                    self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
