"""evals/e2e_run.py's sandbox: a design run cannot read the hidden bounds,
the repo's tests/ or results/, its .git, ~/dev/boards, the box state or the
grading code, cannot reach 127.0.0.1 or any host off the egress allowlist,
and can read its /work and the toolchain. Its auth, its stop rules and its
tool grants are tested without bwrap; nothing here starts a real claude."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "evals"))
import e2e_run  # noqa: E402
import egress  # noqa: E402


def _bwrap_ok() -> bool:
    return (sys.platform == "linux" and bool(shutil.which("bwrap"))
            and e2e_run.bwrap_works())


# CI's container can't start bwrap: every probe would read False, so the
# hidden-path test would pass vacuously and the readable one would fail.
needs_bwrap = pytest.mark.skipif(
    not _bwrap_ok(), reason="`true` does not run inside bwrap here (no bwrap,"
                            " or no user namespaces, as in CI's container)")

# in-sandbox client: reach host:port directly, or CONNECT through the proxy
_NET = r'''
import socket, sys
mode, host, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    if mode == "direct":
        socket.create_connection((host, port), timeout=5)
        print("open")
    else:
        s = socket.create_connection(("127.0.0.1", %d), timeout=10)
        s.sendall(b"CONNECT %%s:%%d HTTP/1.1\r\n\r\n" %% (host.encode(), port))
        print(s.recv(200).split(b"\r\n")[0].decode() or "closed")
except OSError as e:
    print(type(e).__name__)
''' % e2e_run.EGRESS_PORT


def _net(mode, host, port, **kw):
    r = e2e_run.sandbox_exec([e2e_run.PY, "-c", _NET, mode, host,
                              str(port)], capture_output=True, text=True,
                             **kw)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@needs_bwrap
def test_hidden_paths_are_unreadable(tmp_path):
    home = Path.home()
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "runs.jsonl").write_text("{}\n")
    hidden = [
        str(REPO / "tests" / "fixtures" / "stages" / "e2e" / "usbc_ldo"
            / "bounds.yaml"),
        str(REPO / "tests"),
        str(REPO / "results"),
        str(tmp_path / "results" / "runs.jsonl"),
        str(REPO / ".git"),
        str(home / "dev" / "boards"),
        str(home / "dev"),
        str(home / ".cc"),
        str(home / ".claude" / "projects"),
    ]
    # the host side really has what the sandbox must hide
    assert (REPO / "tests" / "fixtures" / "stages" / "e2e" / "usbc_ldo"
            / "bounds.yaml").is_file()
    seen = e2e_run.probe(hidden)
    assert seen == {p: False for p in hidden}


@needs_bwrap
def test_the_skill_copy_leaves_out_the_grading_code(tmp_path):
    work = tmp_path / "work"
    e2e_run.stage_work(work, "hwde")
    sk = f"{e2e_run.WORK}/.claude/skills/hwde"
    hidden = [f"{sk}/{rel}" for rel in sorted(e2e_run.SKILL_HIDE)]
    assert {"scripts/bench.py", "scripts/lib/e2elib.py",
            "reference/e2e-scoring.md"} <= e2e_run.SKILL_HIDE
    for rel in e2e_run.SKILL_HIDE:    # each one exists on the host
        assert (e2e_run.SKILL / rel).is_file(), rel
    seen = e2e_run.probe(hidden + [f"{sk}/SKILL.md"], work=work)
    assert seen == {**{p: False for p in hidden}, f"{sk}/SKILL.md": True}


@needs_bwrap
def test_work_and_system_are_readable():
    seen = e2e_run.probe(["/work", "/usr/bin/env"])
    assert seen == {"/work": True, "/usr/bin/env": True}


@needs_bwrap
def test_key_mode_sees_nothing_under_dot_claude():
    """API-key mode binds no ~/.claude path at all."""
    home = Path.home()
    paths = [str(home / ".claude"), str(home / e2e_run.CREDS),
             str(home / ".claude.json"), str(e2e_run.KEY_FILE.parent)]
    assert e2e_run.probe(paths, creds=None) == {p: False for p in paths}


@needs_bwrap
def test_login_mode_binds_only_the_credentials_file(tmp_path):
    """Login mode: the credentials file is there, read-write (an OAuth
    refresh writes it back), and nothing else of ~/.claude is. A stand-in
    file, never the real login."""
    creds = tmp_path / "creds.json"
    creds.write_text('{"stand": "in"}')
    inside = str(Path.home() / e2e_run.CREDS)
    r = e2e_run.sandbox_exec(
        ["/bin/sh", "-c", 'cat "$1" && echo && printf x >> "$1" && ls -A "$2"',
         "sh", inside, str(Path.home() / ".claude")],
        creds=creds, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ['{"stand": "in"}', ".credentials.json"]
    assert creds.read_text() == '{"stand": "in"}x'


@needs_bwrap
def test_loopback_services_are_unreachable():
    """127.0.0.1 inside is the sandbox's own: a host listener (one this
    test opens, and the box's 5200) is not there, directly or via proxy."""
    with socket.socket() as ls:
        ls.bind(("127.0.0.1", 0))
        ls.listen(1)
        port = ls.getsockname()[1]
        for p in (port, 5200):
            assert _net("direct", "127.0.0.1", p) == "ConnectionRefusedError"
            assert _net("proxy", "127.0.0.1", p) == "HTTP/1.1 403 Forbidden"
        assert _net("proxy", "localhost", 443) == "HTTP/1.1 403 Forbidden"


@needs_bwrap
def test_an_arbitrary_host_is_unreachable():
    # no route at all off the loopback, and the proxy refuses the name
    assert _net("direct", "1.1.1.1", 443) in ("OSError", "TimeoutError")
    assert _net("proxy", "example.com", 443) == "HTTP/1.1 403 Forbidden"
    assert _net("proxy", "api.anthropic.com", 80) == "HTTP/1.1 403 Forbidden"


# in-sandbox client: connect each AF_UNIX address in argv ("@x" = abstract)
_UNIX = r'''
import socket, sys
for a in sys.argv[1:]:
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(5)
    try:
        s.connect("\0" + a[1:] if a.startswith("@") else a)
        print(a, "open")
    except OSError as e:
        print(a, type(e).__name__)
    finally:
        s.close()
'''


def _unix(addrs):
    r = e2e_run.sandbox_exec([e2e_run.PY, "-c", _UNIX, *addrs],
                             capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return dict(ln.rsplit(" ", 1) for ln in r.stdout.splitlines())


def _host_unix_sockets() -> list[str]:
    """Every listening/bound AF_UNIX address the host netns lists, path
    sockets as paths and abstract ones as "@name"."""
    out = []
    for ln in Path("/proc/net/unix").read_text().splitlines()[1:]:
        f = ln.split()
        if len(f) >= 8 and f[7] not in out:
            out.append(f[7])
    return out


@needs_bwrap
def test_no_host_unix_socket_connects(tmp_path):
    """Every path socket the host has, plus a live one this test opens,
    is unreachable from inside: none is bound in."""
    d = tempfile.mkdtemp(dir=os.environ.get("XDG_RUNTIME_DIR") or "/tmp")
    live = str(Path(d) / "l")
    with socket.socket(socket.AF_UNIX) as ls:
        ls.bind(live)
        ls.listen(1)
        try:
            paths = [a for a in _host_unix_sockets() if a.startswith("/")]
            assert live in paths
            seen = _unix(paths)
        finally:
            shutil.rmtree(d)
    assert set(seen) == set(paths)
    assert [a for a, v in seen.items() if v == "open"] == []


@needs_bwrap
def test_an_abstract_host_socket_does_not_connect():
    """Abstract sockets belong to the netns: a host listener isn't there."""
    name = f"hwde-sbx-{os.getpid()}"
    with socket.socket(socket.AF_UNIX) as ls:
        ls.bind("\0" + name)
        ls.listen(1)
        assert _unix(["@" + name]) == {"@" + name: "ConnectionRefusedError"}


@needs_bwrap
def test_the_host_resolver_is_unreachable():
    """systemd-resolved's varlink socket is not bound in, and no name
    resolves inside: DNS happens on the host, in the egress proxy."""
    vl = "/run/systemd/resolve/io.systemd.Resolve"
    assert _unix([vl]) == {vl: "FileNotFoundError"}
    r = e2e_run.sandbox_exec(
        [e2e_run.PY, "-c", "import socket\ntry:\n"
         "    socket.getaddrinfo('example.com', 443)\n    print('resolved')\n"
         "except OSError as e:\n    print(type(e).__name__)"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "gaierror"


@needs_bwrap
def test_the_proxy_is_the_only_socket_file_inside():
    walk = (r"import os, stat" "\n"
            r"for root, ds, fs in os.walk('/'):" "\n"
            r"    if root == '/': ds[:] = [d for d in ds if d != 'proc']" "\n"
            r"    for f in fs:" "\n"
            r"        p = os.path.join(root, f)" "\n"
            r"        try:" "\n"
            r"            if stat.S_ISSOCK(os.lstat(p).st_mode): print(p)" "\n"
            r"        except OSError: pass")
    r = e2e_run.sandbox_exec([e2e_run.PY, "-c", walk], capture_output=True,
                             text=True, timeout=600)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["/egress/proxy.sock"]


@needs_bwrap
def test_a_dead_proxy_fails_closed(tmp_path):
    """With nothing serving the socket, nothing gets out."""
    d = tempfile.mkdtemp(dir=os.environ.get("XDG_RUNTIME_DIR") or "/tmp")
    sock = Path(d) / "s"                       # short: the 108-byte limit
    s = socket.socket(socket.AF_UNIX)
    s.bind(str(sock))
    s.close()                                  # a socket file, no listener
    try:
        _dead_proxy(tmp_path, sock)
    finally:
        shutil.rmtree(d)


def _dead_proxy(tmp_path, sock):
    argv = e2e_run.sandbox_argv(tmp_path, sock)
    r = subprocess.run(argv + [e2e_run.PY, "-c", _NET, "proxy",
                               "api.anthropic.com", "443"],
                       capture_output=True, text=True)
    assert r.stdout.strip() in ("closed", "ConnectionResetError",
                                "BrokenPipeError"), r.stdout + r.stderr
    r = subprocess.run(argv + [e2e_run.PY, "-c", _NET, "direct",
                               "1.1.1.1", "443"],
                       capture_output=True, text=True)
    assert r.stdout.strip() in ("OSError", "TimeoutError")


def _online(host="api.anthropic.com") -> bool:
    try:
        socket.create_connection((host, 443), timeout=5).close()
        return True
    except OSError:
        return False


@needs_bwrap
@pytest.mark.net
@pytest.mark.skipif(not _online(), reason="network-dependent: this host "
                                          "can't reach api.anthropic.com")
def test_the_allowed_host_is_reachable_through_the_proxy():
    assert (_net("proxy", "api.anthropic.com", 443)
            == "HTTP/1.1 200 Connection established")


def test_the_egress_allowlist():
    for host in ("api.anthropic.com", "jlcpcb.com", "cart.jlcpcb.com",
                 "wmsc.lcsc.com", "easyeda.com", "API.Anthropic.com."):
        assert egress.allowed(host, 443), host
    for host, port in (("api.anthropic.com", 80), ("example.com", 443),
                       ("127.0.0.1", 443), ("localhost", 443),
                       ("evil-jlcpcb.com", 443), ("lcsc.com.evil.io", 443),
                       ("anthropic.com", 443)):
        assert not egress.allowed(host, port), (host, port)
    assert egress._target(b"CONNECT a.b:443 HTTP/1.1\r\n\r\n") == ("a.b", 443)
    for bad in (b"GET http://a.b/ HTTP/1.1\r\n\r\n", b"CONNECT a.b HTTP/1.1",
                b"CONNECT [::1]:443 HTTP/1.1\r\n\r\n", b"\xff\xfe"):
        assert egress._target(bad) is None, bad


# --- auth: one setting, an API key file or the login -----------------------

@pytest.fixture
def keyenv(tmp_path, monkeypatch):
    monkeypatch.delenv(e2e_run.KEY_FILE_ENV, raising=False)
    monkeypatch.setattr(e2e_run, "KEY_FILE", tmp_path / "default-key")
    creds = tmp_path / "creds.json"
    monkeypatch.setenv(e2e_run.CREDS_ENV, str(creds))
    return tmp_path, creds


def test_auth_prefers_a_key_file_and_refuses_a_bad_one(keyenv, monkeypatch):
    tmp, creds = keyenv
    with pytest.raises(e2e_run.AuthError, match="no credential"):
        e2e_run.auth()
    creds.write_text("{}")
    assert e2e_run.auth() == {"mode": "login", "creds": creds}
    key = tmp / "key"
    monkeypatch.setenv(e2e_run.KEY_FILE_ENV, str(key))
    with pytest.raises(e2e_run.AuthError, match="not falling back"):
        e2e_run.auth()                       # named, missing: no login
    key.write_text("sk-test\n")
    key.chmod(0o644)
    with pytest.raises(e2e_run.AuthError, match="must be 600"):
        e2e_run.auth()
    key.chmod(0o600)
    assert e2e_run.auth() == {"mode": "key", "key": "sk-test"}
    key.write_text("")
    with pytest.raises(e2e_run.AuthError, match="empty"):
        e2e_run.auth()
    monkeypatch.delenv(e2e_run.KEY_FILE_ENV)    # the default path counts
    dflt = tmp / "default-key"
    dflt.write_text("sk-default")
    dflt.chmod(0o600)
    assert e2e_run.auth() == {"mode": "key", "key": "sk-default"}


def _fake_run(monkeypatch, tmp_path, stdout='{"total_cost_usd": 1.5}'):
    calls = []

    def fake(cmd, work=None, **kw):
        calls.append({"cmd": cmd, **kw})
        return subprocess.CompletedProcess(cmd, 0, stdout, "")
    monkeypatch.setattr(e2e_run, "sandbox_exec", fake)
    monkeypatch.setattr(e2e_run, "score", lambda *a: None)
    monkeypatch.setattr(e2e_run, "kicad_version", lambda: None)
    monkeypatch.setattr(e2e_run, "paused", lambda repo="ai-ee": False)
    monkeypatch.setattr(e2e_run, "have_bwrap", lambda: True)
    argv = ["--brief", "usbc_ldo", "--arm", "bare", "--runs-root",
            str(tmp_path / "runs"), "--out", str(tmp_path / "out.jsonl")]
    return calls, argv


def test_key_mode_passes_the_key_in_the_environment_only(keyenv, monkeypatch):
    tmp, creds = keyenv
    creds.write_text("{}")
    key = tmp / "key"
    key.write_text("sk-secret")
    key.chmod(0o600)
    monkeypatch.setenv(e2e_run.KEY_FILE_ENV, str(key))
    calls, argv = _fake_run(monkeypatch, tmp)
    e2e_run.main(argv)
    (c,) = calls
    assert c["add_env"] == {"ANTHROPIC_API_KEY": "sk-secret"}
    assert c["creds"] is None
    assert not any("sk-secret" in a for a in c["cmd"])
    rec = json.loads((tmp / "out.jsonl").read_text())
    assert rec["auth"] == "key"
    # login mode binds the credentials and passes no key
    monkeypatch.delenv(e2e_run.KEY_FILE_ENV)
    e2e_run.main(argv + ["--seed", "2"])     # its own run dir
    assert calls[1]["creds"] == creds and calls[1]["add_env"] == {}


def test_effort_is_passed_to_claude_and_recorded(keyenv, monkeypatch):
    tmp, creds = keyenv
    creds.write_text("{}")
    calls, argv = _fake_run(monkeypatch, tmp)
    e2e_run.main(argv + ["--effort", "medium"])
    cmd = calls[0]["cmd"]
    assert cmd[cmd.index("--effort") + 1] == "medium"
    rec = json.loads((tmp / "out.jsonl").read_text())
    assert rec["effort"] == "medium"
    # unset: no flag, so claude keeps its own default
    e2e_run.main(argv + ["--seed", "2"])
    assert "--effort" not in calls[1]["cmd"]
    with pytest.raises(SystemExit):
        e2e_run.main(argv + ["--effort", "huge"])


def test_a_named_missing_key_file_starts_no_run(keyenv, monkeypatch):
    tmp, creds = keyenv
    creds.write_text("{}")
    monkeypatch.setenv(e2e_run.KEY_FILE_ENV, str(tmp / "nope"))
    calls, argv = _fake_run(monkeypatch, tmp)
    assert e2e_run.main(argv) == 2
    assert calls == []


def test_the_sandbox_strips_host_auth_from_the_environment(monkeypatch):
    seen = {}
    monkeypatch.setattr(subprocess, "run",
                        lambda argv, env=None, **kw: seen.update(env))
    monkeypatch.setattr(e2e_run, "sandbox_argv", lambda *a: [])
    e2e_run.sandbox_exec(["true"], env={"CLAUDE_CODE_OAUTH_TOKEN": "t",
                                        "ANTHROPIC_API_KEY": "host", "X": "1"})
    assert seen == {"X": "1"}


# --- stop rules ------------------------------------------------------------

def _seeds(monkeypatch, recs):
    started = []

    def fake(a):
        started.append(a.seed)
        return 0, recs[len(started) - 1]
    monkeypatch.setattr(e2e_run, "run", fake)
    monkeypatch.setattr(e2e_run, "paused", lambda repo="ai-ee": False)
    monkeypatch.setattr(e2e_run, "have_bwrap", lambda: True)
    return started


def test_max_total_usd_stops_before_a_run_could_pass_it(monkeypatch):
    rec = {"cost_usd": 40.0, "exit": 0, "budget_stopped": False}
    started = _seeds(monkeypatch, [rec] * 5)
    assert e2e_run.main(["--brief", "usbc_ldo", "--seeds", "5",
                         "--max-total-usd", "100"]) == 1
    assert started == [1, 2]                 # 80 spent + a 40 cap > 100
    started = _seeds(monkeypatch, [rec] * 5)
    assert e2e_run.main(["--brief", "usbc_ldo", "--seeds", "5"]) == 0
    assert started == [1, 2, 3, 4, 5]        # the default 200 fits 5 x 40
    started = _seeds(monkeypatch, [rec])
    assert e2e_run.main(["--brief", "usbc_ldo", "--max-budget-usd", "50",
                         "--max-total-usd", "40"]) == 1
    assert started == []


@pytest.mark.parametrize("bad", [
    {"cost_usd": None, "exit": 1, "budget_stopped": False},
    {"cost_usd": None, "exit": "timeout", "budget_stopped": False},
    {"cost_usd": 3.0, "exit": "timeout", "budget_stopped": False},
])
def test_a_run_with_no_readable_cost_stops_the_seeds(monkeypatch, bad):
    ok = {"cost_usd": 1.0, "exit": 0, "budget_stopped": False}
    started = _seeds(monkeypatch, [ok, bad, ok])
    assert e2e_run.main(["--brief", "usbc_ldo", "--seeds", "3"]) == 1
    assert started == [1, 2]


def test_a_capped_run_stops_the_seeds(monkeypatch):
    capped = {"cost_usd": 40.2, "exit": 1, "budget_stopped": True}
    started = _seeds(monkeypatch, [capped] * 3)
    assert e2e_run.main(["--brief", "usbc_ldo", "--seeds", "3"]) == 0
    assert started == [1]


def test_allowed_tools_scope_bash():
    """The nested run gets no unscoped Bash: each Bash grant names its
    command, and the hwde arm may run the skill's scripts with python3."""
    for arm, tools in e2e_run.ALLOWED_TOOLS.items():
        assert "Bash" not in tools, arm
        assert all(t.endswith(")") for t in tools if t.startswith("Bash")), arm
    assert ("Bash(python3 .claude/skills/hwde/scripts/*)"
            in e2e_run.ALLOWED_TOOLS["hwde"])
    assert not any("python3:" in t for t in e2e_run.ALLOWED_TOOLS["hwde"])


def test_the_bare_arm_gets_the_hwde_arms_tools_minus_the_skill():
    """Owner, 2026-10-06: the arms differ only by /hwde. Bare = hwde minus
    Skill and the skill-script grants, plus python on any script."""
    hwde, bare = e2e_run.ALLOWED_TOOLS["hwde"], e2e_run.ALLOWED_TOOLS["bare"]
    scripts = {t for t in hwde if t.startswith("Bash(")
               and any(sc in t for sc in e2e_run._SCRIPTS)}
    assert scripts
    assert (set(bare) - {"Bash(python3:*)", "Bash(python:*)"}
            == set(hwde) - {"Skill"} - scripts)
    assert "Agent" in bare and "Skill" not in bare


def test_paused_project_starts_no_run(monkeypatch):
    ok = {"cost_usd": 1.0, "exit": 0, "budget_stopped": False}
    started = _seeds(monkeypatch, [ok] * 3)
    monkeypatch.setattr(e2e_run, "paused", lambda repo="ai-ee": True)
    assert e2e_run.main(["--brief", "usbc_ldo", "--seeds", "3"]) == 1
    assert e2e_run.main(["--brief", "usbc_ldo"]) == 1
    assert started == []
    monkeypatch.setattr(e2e_run, "paused", lambda repo="ai-ee": False)
    assert e2e_run.main(["--brief", "usbc_ldo", "--seeds", "3"]) == 0
    assert started == [1, 2, 3]
