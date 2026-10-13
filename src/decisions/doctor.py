"""`doctor`: this machine and this repo, one line per check.

    ok|warn|fail <name>: <detail>

Checks: python (a pyenv 3.12+ interpreter, a newer 3.x pyenv can install a
warn; or the uv tool's interpreter at 3.12+, as `make install` runs it), tool
(`decisions` on PATH at this package's version; another version, or none its
`--version` names, is a warn), marketplace and plugin (the two json files
under ~/.claude/plugins/), provider (the session's resolved file: in range,
none, out of range or unparsable), ledger (the DECISIONS.md `--ledger` names
or the git top holds: lint clean, absent at the git top as a warn, a named
file absent or its problems as a fail)
and respeak (design d23 section 6: `ok` with the root `speak.respeak_root`
finds, else a warn, since only `ask` renders through it and keeps its text
without it).
Exit 0 with no `fail`, 2 otherwise; a `warn` never changes it. `--json` prints
{"checks": [{name, status, detail}], "provider": "none"|"session <v>, profile <p>"}.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

from .common import VERSION, Refusal, bounded
from .ledger import lint, locate
from .speak import respeak_root

__all__ = ["cmd_doctor", "run_checks", "read_provider", "in_range", "MARKETPLACE", "PLUGIN",
           "PROVIDER_RANGE"]

MARKETPLACE = "claude-code-decisions"
PLUGIN = "decisions@claude-code-decisions"
MIN_PYTHON = (3, 12)
# `pyenv install --list` waits on pyenv's rehash lock under load (ADV6-6).
PYENV_TIMEOUT = 10
# `decisions --version` on PATH is a child too, so it is bounded (ADV6-6), and only
# its first TOOL_BYTES of output are read (B3).
TOOL_TIMEOUT = 10
TOOL_BYTES = 4096
# claude-code-session conventions section 3: the resolved file is read only in range.
PROVIDER_RANGE = ">=2.0.0-alpha.1,<3.0.0"
_SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")


def _home(env):
    return env.get("HOME") or os.path.expanduser("~")


def uv_tools(env):
    """uv's tool directory: UV_TOOL_DIR, else XDG_DATA_HOME/uv/tools, else under ~/.local/share."""
    if env.get("UV_TOOL_DIR"):
        return env["UV_TOOL_DIR"]
    data = env.get("XDG_DATA_HOME") or os.path.join(_home(env), ".local", "share")
    return os.path.join(data, "uv", "tools")


def below(path, root):
    """True when `path` lies under `root`, both resolved."""
    return os.path.realpath(path).startswith(os.path.realpath(root) + os.sep)


def check_python(env, prefix=None, version=None):
    prefix = sys.prefix if prefix is None else prefix
    version = tuple(sys.version_info[:3]) if version is None else tuple(version)
    have = "%d.%d.%d" % version
    pyenv_root = env.get("PYENV_ROOT") or os.path.join(_home(env), ".pyenv")
    tools = uv_tools(env)
    if version[:2] >= MIN_PYTHON and below(prefix, tools):
        # `make install` runs the tool under uv: its interpreter is uv's, not pyenv's.
        return "ok", "%s at %s (uv tool)" % (have, prefix)
    if version[:2] < MIN_PYTHON or not below(prefix, os.path.join(pyenv_root, "versions")):
        return "fail", "%s at %s; want 3.12+ under %s/versions/ or a uv tool under %s" % (
            have, prefix, pyenv_root, tools)
    pyenv = shutil.which("pyenv", path=env.get("PATH"))
    if not pyenv:
        return "warn", "%s at %s; pyenv not on PATH, newer releases unchecked" % (have, prefix)
    try:
        listed = bounded([pyenv, "install", "--list"], PYENV_TIMEOUT, env=dict(env))[1]
    except subprocess.TimeoutExpired:
        return "warn", "%s at %s; pyenv install --list timed out after %d s, newer " \
            "releases unchecked" % (have, prefix, PYENV_TIMEOUT)
    except OSError as exc:
        return "warn", "%s; pyenv install --list failed: %s" % (have, exc)
    stable = [tuple(int(p) for p in m.groups())
              for m in re.finditer(r"(?m)^\s*(3)\.(\d+)\.(\d+)\s*$", listed)]
    newest = max(stable) if stable else None
    if newest and newest > version:
        return "warn", "newer python available: %d.%d.%d (have %s)" % (newest + (have,))
    return "ok", "%s at %s" % (have, prefix)


def first_output(argv, env):
    """(returncode, the first TOOL_BYTES of stdout, decoded with replacement) of `argv`.

    The pipe closes after TOOL_BYTES, so a child still writing ends on SIGPIPE; its
    session is killed past TOOL_TIMEOUT, and `subprocess.TimeoutExpired` propagates."""
    child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, env=env, start_new_session=True)
    deadline = time.monotonic() + TOOL_TIMEOUT
    got = []
    reader = threading.Thread(target=lambda: got.append(child.stdout.read(TOOL_BYTES)),
                              daemon=True)
    reader.start()
    reader.join(TOOL_TIMEOUT)
    code = None
    if not reader.is_alive():
        child.stdout.close()
        try:
            code = child.wait(max(deadline - time.monotonic(), 0.01))
        except subprocess.TimeoutExpired:
            code = None
    if code is None:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except OSError:
            pass
        child.wait()
        reader.join(1)
        raise subprocess.TimeoutExpired(argv, TOOL_TIMEOUT)
    return code, got[0].decode("utf-8", errors="replace")


def check_tool(env):
    """ok: `decisions` on PATH names this package's version; warn: absent, or another version."""
    found = shutil.which("decisions", path=env.get("PATH"))
    if not found:
        return "warn", "`decisions` not on PATH (make install)"
    # B2: a PYTHONPATH naming a checkout would make the installed tool import it.
    clean = {k: v for k, v in env.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    try:
        code, said = first_output([found, "--version"], clean)
    except subprocess.TimeoutExpired:
        return "warn", "%s --version timed out after %d s; its version unchecked (make install)" \
            % (found, TOOL_TIMEOUT)
    except (OSError, ValueError) as exc:
        return "warn", "%s --version failed: %s (make install)" % (found, exc)
    match = re.search(r"(\d+\.\d+\.\d+\S*)\s*$", said.strip()) if code == 0 else None
    if match and match.group(1) == VERSION:
        return "ok", "%s %s" % (found, VERSION)
    have = "version %s" % match.group(1) if match else "a version it does not name"
    return "warn", "%s is %s, this package is %s (make install)" % (found, have, VERSION)


def _plugins_json(env, name):
    path = os.path.join(_home(env), ".claude", "plugins", name)
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle), path
    except (OSError, ValueError):
        return None, path


def check_marketplace(env):
    data, path = _plugins_json(env, "known_marketplaces.json")
    if isinstance(data, dict) and MARKETPLACE in data:
        return "ok", "%s known" % MARKETPLACE
    return "warn", "%s not in %s (make marketplace)" % (MARKETPLACE, path)


def check_plugin(env):
    data, path = _plugins_json(env, "installed_plugins.json")
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if isinstance(plugins, dict) and PLUGIN in plugins:
        return "ok", "%s installed" % PLUGIN
    return "warn", "%s not in %s (make marketplace)" % (PLUGIN, path)


def _version_key(text):
    """A sort key with semver precedence: a prerelease sorts before its release."""
    match = _SEMVER.match(text.strip())
    if not match:
        raise ValueError("not a version: %r" % text)
    core = tuple(int(match.group(i)) for i in (1, 2, 3))
    pre = match.group(4)
    if pre is None:
        return core + ((1,),)
    parts = []
    for ident in pre.split("."):
        # numeric identifiers sort before alphanumeric ones
        parts.append((0, int(ident), "") if ident.isdigit() else (1, 0, ident))
    return core + ((0, tuple(parts)),)


def in_range(version, spec=PROVIDER_RANGE):
    """True when `version` satisfies every comma-separated comparator of `spec`."""
    have = _version_key(version)
    for clause in spec.split(","):
        match = re.match(r"^\s*(>=|<=|>|<|==|=)?\s*(\S+)\s*$", clause)
        if not match:
            raise ValueError("not a comparator: %r" % clause)
        op, want = match.group(1) or "==", _version_key(match.group(2))
        ok = {">=": have >= want, "<=": have <= want, ">": have > want,
              "<": have < want, "==": have == want, "=": have == want}[op]
        if not ok:
            return False
    return True


def read_provider(env):
    """The session's resolved file: {status, version, profile, path, detail}."""
    state = env.get("XDG_STATE_HOME") or os.path.join(_home(env), ".local", "state")
    session = env.get("CLAUDE_CODE_SESSION_ID")
    absent = {"status": "absent", "version": None, "profile": None, "path": None,
              "detail": "none (standalone)"}
    if not session:
        return absent
    path = os.path.join(state, "claude-code-session", "sessions", session, "resolved.json")
    if not os.path.isfile(path):
        return dict(absent, path=path)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        provider = data["provider"]
        plugin, version = provider["plugin"], str(provider["version"])
        profile = provider.get("profile")
        inside = plugin == "session" and in_range(version)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return {"status": "unparsable", "version": None, "profile": None, "path": path,
                "detail": "unparsable %s: %s" % (path, exc)}
    if not inside:
        return {"status": "out-of-range", "version": version, "profile": profile,
                "path": path, "detail": "%s %s outside %s" % (plugin, version, PROVIDER_RANGE)}
    return {"status": "in-range", "version": version, "profile": profile, "path": path,
            "detail": "session %s, profile %s" % (version, profile)}


def check_provider(provider):
    status = {"absent": "ok", "in-range": "ok"}.get(provider["status"], "warn")
    detail = provider["detail"]
    if status == "warn":
        detail += "; running standalone"
    return status, detail


def check_ledger(ledger, cwd):
    """ok: the ledger lints clean; warn: none at the git top; fail: a named ledger absent
    (F16), or the lint finds problems."""
    try:
        path = locate(ledger, cwd)
    except Refusal as exc:
        return ("fail" if ledger else "warn"), str(exc)
    try:
        found, problems = lint(path, cwd)
    except Refusal as exc:
        return "fail", str(exc)
    if problems:
        return "fail", "%s: %d lint problems (decisions render --lint)" % (
            found.path, len(problems))
    return "ok", "%s: %d entries, lint clean" % (found.path, len(found.entries))


def check_respeak(env):
    """ok: the respeak root `ask` would use; warn: none, and `ask` keeps its text."""
    root = respeak_root(env, os.path.join(_home(env), ".claude", "plugins", "cache"))
    if root:
        return "ok", root
    return "warn", ("respeak not found (RESPEAK_ROOT or an installed plugin); optional: "
                    "`ask` keeps its text unrendered, every other verb runs the same")


def run_checks(cwd=None, env=None, ledger=None):
    """[(name, status, detail)] and the provider summary."""
    cwd = os.getcwd() if cwd is None else cwd
    env = os.environ if env is None else env
    provider = read_provider(env)
    checks = [("python",) + check_python(env), ("tool",) + check_tool(env),
              ("marketplace",) + check_marketplace(env), ("plugin",) + check_plugin(env),
              ("provider",) + check_provider(provider), ("ledger",) + check_ledger(ledger, cwd),
              ("respeak",) + check_respeak(env)]
    summary = ("session %s, profile %s" % (provider["version"], provider["profile"])
               if provider["status"] == "in-range" else "none")
    return checks, summary


def cmd_doctor(args, out, err):
    checks, provider = run_checks(ledger=getattr(args, "ledger", None))
    if getattr(args, "json", False):
        out.write(json.dumps({"checks": [{"name": n, "status": s, "detail": d}
                                         for n, s, d in checks],
                              "provider": provider}, indent=2) + "\n")
    else:
        for name, status, detail in checks:
            out.write("%s %s: %s\n" % (status, name, detail))
    return 2 if any(status == "fail" for _, status, _ in checks) else 0

