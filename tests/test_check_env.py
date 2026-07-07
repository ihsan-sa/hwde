"""S0 acceptance tests (ai-ee-implementation-plan.md S0).

check_env.py must: exit 0 on this dev machine with pure-JSON stdout, and
exit 1 with actionable remediation when a dependency is missing (simulated
via the AIEE_* env overrides - a set-but-invalid override must fail loudly,
never fall through to discovery).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECK_ENV = REPO / ".claude" / "skills" / "ai-ee" / "scripts" / "check_env.py"


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
    assert report["resolved"]["kicad_cli"].lower().endswith("kicad-cli.exe")


def test_missing_kicad_fails_with_remediation():
    r = run_check_env({"AIEE_KICAD_CLI": r"C:\nonexistent\kicad-cli.exe"})
    assert r.returncode == 1
    report = json.loads(r.stdout)
    assert report["status"] == "fail"
    kc = next(c for c in report["checks"] if c["name"] == "kicad-cli")
    assert kc["status"] == "fail"
    assert "AIEE_KICAD_CLI" in kc["detail"]
    assert "install" in kc.get("remediation", "").lower()


def test_missing_java_fails_with_remediation():
    r = run_check_env({"AIEE_JAVA": r"C:\nonexistent\java.exe"})
    assert r.returncode == 1
    report = json.loads(r.stdout)
    j = next(c for c in report["checks"] if c["name"] == "java-for-freerouting")
    assert j["status"] == "fail"
    assert "AIEE_JAVA" in j["detail"]
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
