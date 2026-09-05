"""S0 acceptance tests (ai-ee-implementation-plan.md S0).

check_env.py must: exit 0 on this dev machine with pure-JSON stdout, and
exit 1 with actionable remediation when a dependency is missing (simulated
via the HWDE_* env overrides - a set-but-invalid override must fail loudly,
never fall through to discovery).

T6 (env-pin, ladder row 18): an explicit HWDE_KICAD_CLI/HWDE_KICAD_ROOT pin
below KiCad 10 is a stale-pin mistake (10-format boards are unreadable by
9.x) and must be rejected at run start, not deep in the run.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
CHECK_ENV = SCRIPTS / "check_env.py"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

from lib import env  # noqa: E402


def run_check_env(extra_env=None, *args):
    env = dict(os.environ)
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(CHECK_ENV), *args],
        capture_output=True, text=True, env=env, timeout=300, cwd=REPO,
    )


def test_passes_on_dev_machine():
    r = run_check_env()
    assert r.returncode == 0, f"stderr:\n{r.stderr}"
    report = json.loads(r.stdout)  # stdout must be pure JSON
    assert report["status"] == "pass"
    names = {c["name"] for c in report["checks"]}
    assert "kicad-cli" in names
    assert "package:kicad-python" in names
    assert report["resolved"]["kicad_cli"].lower().endswith(
        "kicad-cli.exe" if sys.platform == "win32" else "kicad-cli")


def test_missing_kicad_fails_with_remediation():
    r = run_check_env({"HWDE_KICAD_CLI": r"C:\nonexistent\kicad-cli.exe"})
    assert r.returncode == 1
    report = json.loads(r.stdout)
    assert report["status"] == "fail"
    kc = next(c for c in report["checks"] if c["name"] == "kicad-cli")
    assert kc["status"] == "fail"
    assert "HWDE_KICAD_CLI" in kc["detail"]
    assert "install" in kc.get("remediation", "").lower()


def test_validate_pin_rejects_pre10_versions(tmp_path):
    """Unit: the guard rejects 9.x-shaped pins and unknown versions, accepts
    10.x - no subprocess (stubbed version tuples)."""
    p = tmp_path / "kicad-cli.exe"
    p.write_bytes(b"x")
    assert env._validate_pin(p, "HWDE_KICAD_CLI", ver=(10, 0, 3)) == p
    assert env._validate_pin(p, "HWDE_KICAD_CLI", ver=(11, 1)) == p
    with pytest.raises(env.EnvError, match=r"pins KiCad 9\.0\.5"):
        env._validate_pin(p, "HWDE_KICAD_CLI", ver=(9, 0, 5))
    with pytest.raises(env.EnvError, match="HWDE_KICAD_ROOT"):
        env._validate_pin(p, "HWDE_KICAD_ROOT", ver=(9, 0, 5))
    with pytest.raises(env.EnvError, match="could not be determined"):
        env._validate_pin(p, "HWDE_KICAD_CLI", ver=())


@pytest.mark.skipif(sys.platform != "win32", reason="batch-file stub")
def test_stale_9x_pin_fails_check_env(tmp_path):
    """Integration: a pin that reports 9.0.5 fails the kicad-cli check with
    the stale-pin remediation instead of sailing through >= MIN_KICAD."""
    stub = tmp_path / "kicad-cli.bat"
    stub.write_text("@echo 9.0.5\n", encoding="ascii")
    r = run_check_env({"HWDE_KICAD_CLI": str(stub)})
    assert r.returncode == 1
    report = json.loads(r.stdout)
    kc = next(c for c in report["checks"] if c["name"] == "kicad-cli")
    assert kc["status"] == "fail"
    assert "pins KiCad 9.0.5" in kc["detail"]
    assert "10" in kc["detail"]          # remediation names the pipeline major
    assert kc.get("remediation")


def test_unpinned_discovery_still_resolves_10x():
    """The guard must not touch plain discovery: unset pins resolve 10.x."""
    e = {k: v for k, v in os.environ.items()
         if k not in ("HWDE_KICAD_CLI", "HWDE_KICAD_ROOT")}
    r = subprocess.run([sys.executable, str(CHECK_ENV)],
                       capture_output=True, text=True, env=e, timeout=300,
                       cwd=REPO)
    assert r.returncode == 0, r.stderr
    report = json.loads(r.stdout)
    assert report["resolved"]["kicad_version"].startswith("10.")


def test_missing_java_fails_with_remediation():
    r = run_check_env({"HWDE_JAVA": r"C:\nonexistent\java.exe"})
    assert r.returncode == 1
    report = json.loads(r.stdout)
    j = next(c for c in report["checks"] if c["name"] == "java-for-freerouting")
    assert j["status"] == "fail"
    assert "HWDE_JAVA" in j["detail"]
    rem = j.get("remediation", "").lower()
    assert "adoptium" in rem or "temurin" in rem


def test_out_file_and_quiet():
    out = REPO / "_scratch" / "test_env_report.json"
    if out.exists():
        out.unlink()
    r = run_check_env(None, "--out", str(out), "--quiet")
    assert r.returncode == 0
    assert r.stdout.strip() == ""
    assert r.stderr.strip() == ""
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
