"""evals/writeset_check.py: an eval-loop fix row may not touch scorers,
checks, bounds, fixtures or waivers; other branches are not checked."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "evals"))
import writeset_check as wc  # noqa: E402

FIX = "track/eval-fix-check-current-fp"


def test_each_protected_class_is_refused_on_a_fix_row():
    cases = {
        ".claude/skills/hwde/scripts/bench.py": "scorers",
        ".claude/skills/hwde/scripts/lib/e2elib.py": "scorers",
        "evals/e2e_run.py": "scorers",
        "tests/test_bench.py": "checks",
        ".github/workflows/checks.yml": "checks",
        "tests/fixtures/stages/e2e/usbc_ldo/bounds.yaml": "bounds",
        "tests/fixtures/stages/baselines/p6.score.json": "bounds",
        "tests/fixtures/stages/manifest.yaml": "fixtures",
        "tests/golden/scorecard/triage.yaml": "fixtures",
        "boards-x/waivers.yaml": "waivers",
    }
    res = wc.check(FIX, [("M", p) for p in cases])
    assert res["fix_row"]
    assert {r["path"]: r["class"] for r in res["refused"]} == cases


def test_a_fix_row_may_change_hwde_and_add_a_test():
    entries = [("M", ".claude/skills/hwde/scripts/check_current.py"),
               ("A", "tests/test_check_current_fp.py")]
    assert wc.check(FIX, entries)["refused"] == []
    # the same new test file, edited after it exists, is a changed check
    assert wc.check(FIX, [("M", "tests/test_check_current_fp.py")])["refused"]
    assert wc.check(FIX, [("D", "tests/test_bench.py")])["refused"]


def test_new_pytest_hooks_and_config_are_refused_anywhere():
    """A new conftest.py or pytest config can skip or rewrite the suite, so
    adding one is refused like changing one, at the root or below."""
    paths = ["conftest.py", "tests/conftest.py", "tests/sub/conftest.py",
             ".claude/skills/hwde/scripts/conftest.py", "pytest.ini",
             ".pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml",
             "tests/pytest.ini", "evals/x/pyproject.toml"]
    for status in ("A", "M"):
        res = wc.check(FIX, [(status, p) for p in paths])
        got = {r["path"]: r["class"] for r in res["refused"]}
        assert got == {p: ("scorers" if p.startswith("evals/") else "checks")
                       for p in paths}, status
    # an ordinary new test file is still fine
    assert wc.check(FIX, [("A", "tests/test_new.py")])["refused"] == []


def test_the_workflow_runs_mains_copy_of_the_check():
    """The PR's own writeset_check.py could wave itself through, so the
    workflow pipes main's copy into python."""
    wf = (REPO / ".github" / "workflows" / "writeset.yml").read_text()
    assert "git show origin/main:evals/writeset_check.py" in wf
    assert "python3 evals/writeset_check.py" not in wf


def test_other_branches_are_not_checked():
    entries = [("M", ".claude/skills/hwde/scripts/bench.py")]
    res = wc.check("track/eval-driver", entries)
    assert res == {"fix_row": False, "refused": []}


def test_cli_exits_1_on_a_refused_path_and_0_otherwise():
    script = str(REPO / "evals" / "writeset_check.py")
    bad = subprocess.run([sys.executable, script, "--branch", FIX, "--paths",
                          "M:tests/fixtures/stages/manifest.yaml"],
                         capture_output=True, text=True)
    ok = subprocess.run([sys.executable, script, "--branch", FIX, "--paths",
                         "M:.claude/skills/hwde/scripts/gate.py"],
                        capture_output=True, text=True)
    assert (bad.returncode, ok.returncode) == (1, 0)
