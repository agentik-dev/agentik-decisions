"""scripts/hygiene: counts per group, the allowlist, binaries skipped, exits,
the private list, and no matched text or private pattern ever printed. Fixture
strings are assembled at runtime so this file stays clean under the scan itself;
every run reads an invented private list, never the caller's."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hygiene"
PRIVATE_ENV = "AGENTIK_HYGIENE_PRIVATE"

# The invented private list every run reads: domain, private and person live
# only there, as the owner's do; each term assembled so it never sits here whole.
PRIVATE_ROWS = [("domain", "frobnit" + r"z\.test"), ("private", "quuxmirr" + "or"),
                ("person", "zorb" + "lax"), ("sibling", "flurb" + "plugin")]
# One fixture per group; each assembled so the literal never sits in this file.
FIXTURES = {
    "home": "see /Us" + "ers/alice/notes",
    "lan": "host 192." + "168.1.9 and 10." + "0.0.7",
    "domain": "https://wiki.frobnit" + "z.test/x",
    "private": "the quuxmirr" + "or mirror",
    "person": "by Zorb" + "lax",
    "sibling": "load flurb" + "plugin first",
}
# The text each fixture matches on, lower-cased.
MATCHED = ["/us" + "ers/alice", "192." + "168.", "10." + "0.0.7", "frobnit" + "z.test",
           "quuxmirr" + "or", "zorb" + "lax", "flurb" + "plugin"]


def write_private(path, rows, extra=""):
    Path(path).write_text(extra + "".join("%s\t%s\n" % row for row in rows),
                          encoding="utf-8")


_PRIVATE_DIR = tempfile.TemporaryDirectory()
PRIVATE_FILE = os.path.join(_PRIVATE_DIR.name, "hygiene-private.tsv")
write_private(PRIVATE_FILE, PRIVATE_ROWS)


def git(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)


def run(repo, *args, env=None):
    """The scan over `repo` with the invented private list; `env` overrides the
    environment, a None value unsets the name."""
    full = dict(os.environ, **{PRIVATE_ENV: PRIVATE_FILE})
    for name, value in (env or {}).items():
        if value is None:
            full.pop(name, None)
        else:
            full[name] = value
    p = subprocess.run([str(SCRIPT), "--repo", repo, *args],
                       capture_output=True, text=True, env=full)
    return p.returncode, p.stdout, p.stderr


class HygieneTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        git(self.repo, "init", "-q")
        for group, text in FIXTURES.items():
            Path(self.repo, group + ".txt").write_text("clean\n" + text + "\n" + text + "\n")
        Path(self.repo, "docs").mkdir()
        Path(self.repo, "docs", "allowed.md").write_text(FIXTURES["sibling"] + "\n")
        Path(self.repo, "docs", "deep").mkdir()
        Path(self.repo, "docs", "deep", "x.md").write_text(FIXTURES["sibling"] + "\n")
        Path(self.repo, "blob.bin").write_bytes(b"\0\1" + FIXTURES["person"].encode())
        Path(self.repo, "untracked.txt").write_text(FIXTURES["domain"] + "\n")
        Path(self.repo, ".hygiene-allow").write_text(
            "# comment\ndocs/*.md: sibling\nlan.txt: lan,home\n")
        git(self.repo, "add", "--", *[p for p in os.listdir(self.repo)
                                      if p not in (".git", "untracked.txt")])

    def tearDown(self):
        self.tmp.cleanup()

    def json_result(self, *args):
        code, out, _ = run(self.repo, "--json", *args)
        return code, json.loads(out)

    def test_counts_per_group(self):
        code, d = self.json_result()
        self.assertEqual(code, 2)
        for group in ("home", "lan", "private", "person"):
            self.assertEqual(d["groups"][group], {"lines": 2, "files": 1}, group)
        self.assertEqual(d["groups"]["domain"], {"lines": 3, "files": 2})
        self.assertEqual(d["groups"]["sibling"], {"lines": 4, "files": 3})

    def test_allowlist_and_binary_and_untracked(self):
        code, d = self.json_result()
        hits = {(f["path"], f["group"]): f["lines"] for f in d["files"]}
        self.assertNotIn(("lan.txt", "lan"), hits)
        self.assertNotIn(("docs/allowed.md", "sibling"), hits)
        # the glob's * stays inside one segment
        self.assertEqual(hits[("docs/deep/x.md", "sibling")], 1)
        self.assertFalse(any(p == "blob.bin" for p, _ in hits))
        # the working tree: an untracked file is scanned before its commit
        self.assertEqual(hits[("untracked.txt", "domain")], 1)
        self.assertEqual(d["hits_outside_allowlist"], sum(hits.values()))
        self.assertEqual(d["hits_outside_allowlist"], 2 * 5 + 1 + 1)

    def test_green_exits_zero(self):
        Path(self.repo, ".hygiene-allow").write_text(
            "*.txt: home,lan,domain,private,person,sibling\ndocs/*.md: sibling\n"
            "docs/*/*.md: sibling\n")
        code, d = self.json_result()
        self.assertEqual((code, d["hits_outside_allowlist"], d["files"]), (0, 0, []))

    def test_never_prints_matched_text(self):
        for args in ((), ("--json",)):
            code, out, err = run(self.repo, *args)
            self.assertEqual(code, 2)
            for token in MATCHED:
                self.assertNotIn(token, (out + err).lower(), args)
        self.check_text_table()  # folded, so the README's test count holds

    def test_nul_file_scans_secret_and_email(self):
        # ADV10-17: a NUL file's printable runs are scanned for home, secret and email
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            data = (b"\0 abcd" + b"@" + b"example.org sk-an" + b"t" + b"-abcdefghij\n"
                    + b"\0" + ("/Us" + "ers/alice/p.png").encode() + b"\0"
                    + FIXTURES["person"].encode() + b"\0\x01")
            Path(repo, "b.bin").write_bytes(data)
            code, d = self.json_in(repo)
            self.assertEqual(code, 2)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("b.bin", "email", 1), ("b.bin", "home", 1),
                              ("b.bin", "secret", 1)])

    def check_text_table(self):
        code, out, _ = run(self.repo)
        lines = out.splitlines()
        self.assertEqual(lines[0].split(), ["group", "lines", "files"])
        self.assertIn("home.txt  home  2", lines)
        self.assertEqual(lines[-1], "hits outside allowlist: 12")

    def test_working_tree_scanned(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "a.md").write_text(FIXTURES["person"] + "\n")
            Path(repo, "b.md").write_text(FIXTURES["person"] + "\n")
            Path(repo, ".gitignore").write_text("b.md\n")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            # untracked a.md is scanned, ignored b.md never
            self.assertEqual((code, d["groups"]["person"]["files"]), (2, 1))
            self.assertEqual([f["path"] for f in d["files"]], ["a.md"])

    def test_person_evaluated_under_sittings(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "history", "sittings").mkdir(parents=True)
            Path(repo, "history", "sittings", "x.md").write_text(
                FIXTURES["person"] + "\n" + FIXTURES["sibling"] + "\n")
            Path(repo, "x.md").write_text(FIXTURES["person"] + "\n")
            git(repo, "add", "-A")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            # a charter is scanned for the owner's terms too; sibling alone is skipped there
            self.assertEqual((d["groups"]["person"]["files"], d["hits_outside_allowlist"]),
                             (2, 2))
            self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                             {("x.md", "person"), ("history/sittings/x.md", "person")})

    def test_sibling_not_evaluated_under_sittings(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "history", "sittings").mkdir(parents=True)
            Path(repo, "history", "sittings", "x.md").write_text(
                FIXTURES["sibling"] + "\n" + FIXTURES["home"] + "\n")
            Path(repo, "x.md").write_text(FIXTURES["sibling"] + "\n")
            git(repo, "add", "-A")
            code, out, _ = run(repo, "--json")
            d = json.loads(out)
            self.assertEqual((d["groups"]["sibling"]["files"], d["groups"]["home"]["files"],
                              d["hits_outside_allowlist"]), (1, 1, 2))
            # a sibling named by path still trips home under the charters
            self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                             {("x.md", "sibling"), ("history/sittings/x.md", "home")})

    def test_script_scans_itself_clean(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "hygiene").write_bytes(SCRIPT.read_bytes())
            Path(repo, "test_hygiene.py").write_bytes(Path(__file__).read_bytes())
            git(repo, "add", "hygiene", "test_hygiene.py")
            code, out, _ = run(repo, "--json")
            self.assertEqual((code, json.loads(out)["hits_outside_allowlist"]), (0, 0))

    def test_usage_and_git_failure_exit_one(self):
        self.assertEqual(run(self.repo, "--bogus")[0], 1)
        self.assertEqual(run(self.repo, "--allow")[0], 1)
        self.assertEqual(run(self.repo, "--allow", "missing")[0], 1)
        Path(self.repo, ".hygiene-allow").write_text("no-colon-here\n")
        self.assertEqual(run(self.repo)[0], 1)
        with tempfile.TemporaryDirectory() as notgit:
            self.assertEqual(run(notgit)[0], 1)

    def test_hygiene_catches_secret_symlink_and_path(self):
        # ADV6-1: a key, a symlink to a home path, a file named for a private repo.
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "k.md").write_text("sk-an" + "t-x\n")
            os.symlink("/Us" + "ers/x", os.path.join(repo, "l"))
            Path(repo, "quuxmirr" + "or.md").write_text("")
            code, d = self.json_in(repo)
            self.assertEqual((code, d["hits_outside_allowlist"]), (2, 3))
            self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                             {("k.md", "secret"), ("l", "home"),
                              ("quuxmirr" + "or.md", "private")})

    def json_in(self, repo, *args):
        code, out, _ = run(repo, "--json", *args)
        return code, json.loads(out)

    def test_secret_group_catches_each_key_shape(self):
        keys = ["sk-an" + "t-api03-abcDEF_12-x", "gh" + "p_" + "a1B2" * 9,
                "github_" + "pat_" + "11AB" * 6, "AGE-SECRET-" + "KEY-1" + "QZ" * 20,
                "AK" + "IA" + "ABCDEFGH23456789", "-----BEG" + "IN RSA PRIV" + "ATE KEY-----",
                "-----BEG" + "IN PRIV" + "ATE KEY-----"]
        # the prefixes named in prose, and lowercase look-alikes, are not keys
        prose = ["`sk-an" + "t-`", "`gh" + "p_`", "BEG" + "IN .* PRIV" + "ATE KEY",
                 "ak" + "ia" + "abcdefgh23456789"]
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "keys.md").write_text("\n".join(keys) + "\n")
            Path(repo, "prose.md").write_text("\n".join(prose) + "\n")
            code, d = self.json_in(repo)
            self.assertEqual(code, 2)
            self.assertEqual(d["groups"]["secret"], {"lines": len(keys), "files": 1})
            out = run(repo)[1] + run(repo, "--json")[1]
            for key in keys:
                self.assertNotIn(key, out)

    def test_email_and_lan_172_and_local(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "e.md").write_text("mail al" + "ice@" + "example.com\nno at here\n")
            Path(repo, "n.md").write_text(
                "172." + "20.1.2\n172." + "31.0.1\nnas" + ".local here\n"
                "172.32.0.1\n172.15.0.1\n~/.local/state\n")
            code, d = self.json_in(repo)
            self.assertEqual(code, 2)
            self.assertEqual(d["groups"]["email"], {"lines": 1, "files": 1})
            self.assertEqual(d["groups"]["lan"], {"lines": 3, "files": 1})

    def test_binary_scanned_for_home_over_printable_runs(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            png = (b"\x89PNG\0\0" + ("/Us" + "ers/alice/p.png").encode() + b"\0"
                   + FIXTURES["person"].encode() + b"\0" + ("~/co" + "de/").encode()
                   + b"\0\x01")
            Path(repo, "a.png").write_bytes(png)
            code, d = self.json_in(repo)
            # one run of 8+ bytes carries the home path; the 7-byte run and the
            # person text are not evaluated in a binary
            self.assertEqual(code, 2)
            self.assertEqual(d["files"], [{"path": "a.png", "group": "home", "lines": 1}])
            self.assertEqual(d["oversize"], 0)
            # UTF-16 (a BOM, or NULs on 90% of the odd or even bytes) is text (ADV10-8)
            text = "/Us" + "ers/alice/x\n" + FIXTURES["person"] + "\n"
            Path(repo, "le.md").write_bytes(text.encode("utf-16-le"))
            Path(repo, "be.md").write_bytes(text.encode("utf-16"))
            Path(repo, "zeros.bin").write_bytes(b"\0" * 64)
            # a file over 4 MiB is streamed, every line of it (ADV11-3)
            Path(repo, "big.txt").write_bytes(("/Us" + "ers/alice\n").encode() * 500000)
            code, d = self.json_in(repo)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("a.png", "home", 1), ("be.md", "home", 1), ("be.md", "person", 1),
                              ("big.txt", "home", 500000), ("le.md", "home", 1),
                              ("le.md", "person", 1)])
            self.assertEqual(d["oversize"], 1)

    def test_hygiene_oversize_is_scanned(self):
        # ADV11-3: 4 MiB + 1 of one line, then a home path: streamed, one hit, never a pass
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "f").write_bytes(b"x" * (4 * 1024 * 1024 + 1)
                                        + ("\n/Us" + "ers/me/x\n").encode())
            code, d = self.json_in(repo)
            self.assertEqual(code, 2)
            self.assertEqual(d["groups"]["home"]["lines"], 1)
            self.assertEqual(d["oversize"], 1)
            # a binary and a UTF-16 file over the cap stream too, a run across a chunk seen
            Path(repo, "f").unlink()
            Path(repo, "b.bin").write_bytes(b"\0" + b"y" * (1024 * 1024 - 4)
                                            + ("/Us" + "ers/me/bin").encode() + b"\0" * (4 << 20))
            Path(repo, "w.md").write_bytes(("z" * (5 << 20) + "\n/Us" + "ers/me/w\n")
                                           .encode("utf-16"))
            code, d = self.json_in(repo)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("b.bin", "home", 1), ("w.md", "home", 1)])
            self.assertEqual(d["oversize"], 2)

    def test_hygiene_relay_adv11_15_first_line(self):
        # agent-relay's ADV11-15: a tracked file over 4 MiB whose first line holds a home
        # path and an email passed by path only, exit 0; streamed now (S14), both counted.
        # Binaries still skip lan, domain, private, person and sibling (ADV10-17, unchanged)
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "big.md").write_bytes(("/Us" + "ers/alice/x mail al" + "ice@"
                                              + "example.com\n").encode() + b"y" * (5 << 20))
            git(repo, "add", "big.md")
            code, d = self.json_in(repo)
            self.assertEqual(code, 2)
            self.assertEqual(sorted((f["path"], f["group"], f["lines"]) for f in d["files"]),
                             [("big.md", "email", 1), ("big.md", "home", 1)])
            self.assertEqual(d["oversize"], 1)

    def test_secret_allow_row_only_under_fixtures(self):
        with tempfile.TemporaryDirectory() as repo:
            git(repo, "init", "-q")
            Path(repo, "tests", "fixtures").mkdir(parents=True)
            Path(repo, "tests", "fixtures", "k.md").write_text("sk-an" + "t-x\n")
            Path(repo, ".hygiene-allow").write_text("tests/fixtures/*.md: secret\n")
            self.assertEqual(self.json_in(repo)[0], 0)
            for row in ("*.md: secret", "tests/*.md: secret,home", "tests/fixture*/k.md: secret"):
                Path(repo, ".hygiene-allow").write_text(row + "\n")
                self.assertEqual(run(repo)[0], 1, row)

    def test_symlink_target_not_followed(self):
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as out:
            git(repo, "init", "-q")
            Path(out, "t.md").write_text(FIXTURES["person"] + "\n")
            os.symlink(os.path.join(out, "t.md"), os.path.join(repo, "link"))
            code, d = self.json_in(repo)
            # the target path is scanned; the target's content is not read
            self.assertEqual(d["groups"]["person"]["files"], 0)



class PrivateListTest(unittest.TestCase):
    """The private list: loaded from the environment or the config home, its
    absence one stderr line, --require-private, comments and blanks, and no
    private pattern ever printed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.tmp.name, "repo")
        os.mkdir(self.repo)
        git(self.repo, "init", "-q")
        self.term = "blorp" + "tastic"

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, *args, env=None):
        code, out, err = run(self.repo, "--json", *args, env=env)
        return code, (json.loads(out) if out else None), err

    def test_private_list_loads_a_new_group_and_hits(self):
        listed = os.path.join(self.tmp.name, "p.tsv")
        write_private(listed, PRIVATE_ROWS + [("codename", self.term[:5] + "t[a]stic")])
        Path(self.repo, "a.md").write_text("the " + self.term.upper() + " plan\n"
                                           + FIXTURES["person"] + "\n")
        code, d, err = self.scan(env={PRIVATE_ENV: listed})
        self.assertEqual((code, err), (2, ""))
        self.assertEqual(d["groups"]["codename"], {"lines": 1, "files": 1})
        self.assertEqual(d["groups"]["person"], {"lines": 1, "files": 1})
        self.assertEqual({(f["path"], f["group"]) for f in d["files"]},
                         {("a.md", "codename"), ("a.md", "person")})
        text = run(self.repo, env={PRIVATE_ENV: listed})
        self.assertIn("a.md  codename  1", text[1].splitlines())
        for out in (json.dumps(d), text[1] + text[2]):
            self.assertNotIn("t[a]stic", out)
            self.assertNotIn(self.term, out.lower())

    def test_absent_list_is_one_line_and_generic_groups_decide(self):
        missing = os.path.join(self.tmp.name, "none.tsv")
        Path(self.repo, "a.md").write_text(FIXTURES["person"] + "\n" + FIXTURES["domain"] + "\n")
        code, d, err = self.scan(env={PRIVATE_ENV: missing})
        self.assertEqual(err, "hygiene: no private list at %s; generic groups only\n" % missing)
        self.assertEqual((code, d["hits_outside_allowlist"]), (0, 0))
        self.assertNotIn("person", d["groups"])
        Path(self.repo, "b.md").write_text(FIXTURES["home"] + "\n")
        code, d, err = self.scan(env={PRIVATE_ENV: missing})
        self.assertEqual((code, d["files"]), (2, [{"path": "b.md", "group": "home", "lines": 1}]))
        self.assertEqual(len(err.splitlines()), 1)

    def test_require_private_exits_two_when_absent_or_unreadable(self):
        Path(self.repo, "a.md").write_text("clean\n")
        missing = os.path.join(self.tmp.name, "none.tsv")
        code, out, err = run(self.repo, "--require-private", env={PRIVATE_ENV: missing})
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no private list at %s" % missing, err)
        code, _, err = run(self.repo, "--require-private", env={PRIVATE_ENV: self.tmp.name})
        self.assertEqual(code, 2)
        self.assertIn("is unreadable", err)
        bad = os.path.join(self.tmp.name, "latin1.tsv")
        Path(bad).write_bytes(b"person\t\xff\xfe\n")
        self.assertEqual(run(self.repo, "--require-private", env={PRIVATE_ENV: bad})[0], 2)
        self.assertEqual(run(self.repo, "--require-private")[0], 0)

    def test_comments_and_blanks_skipped(self):
        listed = os.path.join(self.tmp.name, "p.tsv")
        write_private(listed, PRIVATE_ROWS, extra="# person\t%s\n\n   \n\t\n" % self.term)
        Path(self.repo, "a.md").write_text(self.term + "\n")
        code, d, err = self.scan(env={PRIVATE_ENV: listed})
        self.assertEqual((code, err, d["hits_outside_allowlist"]), (0, "", 0))
        Path(self.repo, "b.md").write_text(FIXTURES["person"] + "\n")
        code, d, _ = self.scan(env={PRIVATE_ENV: listed})
        self.assertEqual((code, d["files"]), (2, [{"path": "b.md", "group": "person", "lines": 1}]))

    def test_bad_row_names_its_line_never_its_pattern(self):
        listed = os.path.join(self.tmp.name, "p.tsv")
        for row in ("person\t(" + self.term + "\n", "person " + self.term + "\n",
                    "Bad Group\t" + self.term + "\n"):
            Path(listed).write_text("# ok\n" + row)
            code, out, err = run(self.repo, env={PRIVATE_ENV: listed})
            self.assertEqual((code, out), (1, ""), row)
            self.assertIn("%s:2:" % listed, err)
            self.assertNotIn(self.term, err)

    def test_default_path_is_the_config_home(self):
        conf = os.path.join(self.tmp.name, "conf")
        os.makedirs(os.path.join(conf, "agentik"))
        write_private(os.path.join(conf, "agentik", "hygiene-private.tsv"), PRIVATE_ROWS)
        Path(self.repo, "a.md").write_text(FIXTURES["person"] + "\n")
        code, d, err = self.scan(env={PRIVATE_ENV: None, "XDG_CONFIG_HOME": conf})
        self.assertEqual((code, err, d["groups"]["person"]["lines"]), (2, "", 1))
        home = os.path.join(self.tmp.name, "home")
        os.makedirs(os.path.join(home, ".config"))
        os.symlink(os.path.join(conf, "agentik"), os.path.join(home, ".config", "agentik"))
        code, d, err = self.scan(env={PRIVATE_ENV: None, "XDG_CONFIG_HOME": None, "HOME": home})
        self.assertEqual((code, err, d["groups"]["person"]["lines"]), (2, "", 1))

    def test_allow_row_for_an_unloaded_group_is_inert(self):
        Path(self.repo, "a.md").write_text(FIXTURES["person"] + "\n")
        Path(self.repo, ".hygiene-allow").write_text("a.md: person\n")
        missing = os.path.join(self.tmp.name, "none.tsv")
        self.assertEqual(self.scan(env={PRIVATE_ENV: missing})[0], 0)
        self.assertEqual(self.scan()[0], 0)
        Path(self.repo, ".hygiene-allow").write_text("a.md: person,Not A Group\n")
        self.assertEqual(run(self.repo)[0], 1)


if __name__ == "__main__":
    unittest.main()
