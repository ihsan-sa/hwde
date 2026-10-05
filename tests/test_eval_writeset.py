"""evals/writeset_check.py: an eval-loop fix row may not touch scorers,
checks, bounds, fixtures or waivers; other branches are not checked."""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "evals"))
import writeset_check as wc  # noqa: E402

FIX = "track/eval-fix-check-current-fp"
# what an added test file reads as, for paths that don't exist on disk
PLAIN = "def test_x():\n    assert 1\n"


def _plain(path):
    return PLAIN


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
    assert wc.check(FIX, entries, read=_plain)["refused"] == []
    # the same new test file, edited after it exists, is a changed check
    assert wc.check(FIX, [("M", "tests/test_check_current_fp.py")])["refused"]
    assert wc.check(FIX, [("D", "tests/test_bench.py")])["refused"]


def test_new_pytest_hooks_and_config_are_refused_anywhere():
    """A new conftest.py or pytest config can skip or rewrite the suite, so
    adding one is refused like changing one, at the root or below."""
    paths = ["conftest.py", "tests/conftest.py", "tests/sub/conftest.py",
             ".claude/skills/hwde/scripts/conftest.py", "pytest.ini",
             ".pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml",
             "tests/pytest.ini", "evals/x/pyproject.toml", "pytest.toml",
             ".pytest.toml", "tests/pytest.toml"]
    for status in ("A", "M"):
        res = wc.check(FIX, [(status, p) for p in paths])
        got = {r["path"]: r["class"] for r in res["refused"]}
        assert got == {p: ("scorers" if p.startswith("evals/") else "checks")
                       for p in paths}, status
    # an ordinary new test file is still fine
    assert wc.check(FIX, [("A", "tests/test_new.py")],
                    read=_plain)["refused"] == []


def test_a_fix_row_may_not_change_the_check_itself():
    for status in ("A", "M", "D"):
        res = wc.check(FIX, [(status, "evals/writeset_check.py")])
        assert res["refused"] == [{"path": "evals/writeset_check.py",
                                   "status": status, "class": "rule"}]


def test_a_fix_row_may_not_change_the_writeset_workflow():
    for status in ("A", "M", "D"):
        res = wc.check(FIX, [(status, ".github/workflows/writeset.yml")])
        assert res["refused"] == [{"path": ".github/workflows/writeset.yml",
                                   "status": status, "class": "rule"}]


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


def test_an_added_test_that_cannot_be_read_is_refused():
    res = wc.check(FIX, [("A", "tests/test_missing.py")],
                   read=lambda p: None)
    assert res["refused"] == [{"path": "tests/test_missing.py", "status": "A",
                               "class": "checks", "why": "unreadable"}]


def test_parse_z_keeps_raw_paths_and_splits_renames():
    """-z output: non-ASCII paths come through as text, not git's quoted
    octal, and a rename or copy yields its two ends."""
    out = (b"M\0tests/sub_\xc3\xa9/conftest.py\0"
           b"A\0tests/fixtures/stages/e2e/n\xc3\xbc/bounds.yaml\0"
           b"R087\0tests/test_bench.py\0tests/test_renamed.py\0"
           b"C100\0src.py\0copy.py\0")
    assert wc.parse_z(out) == [
        ("M", "tests/sub_é/conftest.py"),
        ("A", "tests/fixtures/stages/e2e/nü/bounds.yaml"),
        ("D", "tests/test_bench.py"), ("A", "tests/test_renamed.py"),
        ("A", "copy.py")]
    assert wc.parse_z(b"") == []


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t",
                    "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def test_changed_reads_a_real_branch_with_non_ascii_paths(tmp_path):
    repo = tmp_path / "r"
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_old.py").write_text(PLAIN)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    _git(repo, "checkout", "-qb", FIX)
    for rel in ("tests/sub_é/conftest.py",
                "tests/fixtures/stages/e2e/nü/bounds.yaml"):
        (repo / rel).parent.mkdir(parents=True)
        (repo / rel).write_text("x = 1\n")
    _git(repo, "mv", "tests/test_old.py", "tests/test_new_é.py")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fix")
    entries = wc.changed(str(repo), "main")
    assert sorted(entries) == sorted([
        ("A", "tests/sub_é/conftest.py"),
        ("A", "tests/fixtures/stages/e2e/nü/bounds.yaml"),
        ("D", "tests/test_old.py"), ("A", "tests/test_new_é.py")])
    got = {r["path"]: r["class"]
           for r in wc.check(FIX, entries, repo=str(repo))["refused"]}
    assert got == {"tests/sub_é/conftest.py": "checks",
                   "tests/fixtures/stages/e2e/nü/bounds.yaml": "bounds",
                   "tests/test_old.py": "checks"}


def test_a_new_path_that_shadows_a_scoring_module_is_refused():
    paths = [".claude/skills/hwde/scripts/lib/e2elib/__init__.py",
             "tests/benchlib.py", "tools/evalcard.cpython-314.so"]
    res = wc.check(FIX, [("A", p) for p in paths], repo=str(REPO),
                   read=_plain)
    assert {r["path"]: (r["class"], r["why"]) for r in res["refused"]} == {
        paths[0]: ("scorers", "shadows the scoring module e2elib"),
        paths[1]: ("scorers", "shadows the scoring module benchlib"),
        paths[2]: ("scorers", "shadows the scoring module evalcard")}
    ok = ".claude/skills/hwde/scripts/lib/currentlib.py"
    assert wc.check(FIX, [("A", ok)], repo=str(REPO))["refused"] == []


def test_a_new_py_named_like_stdlib_or_an_installed_package_is_refused():
    paths = [".claude/skills/hwde/scripts/json.py", "tests/yaml/__init__.py",
             "tools/os/x.py"]
    res = wc.check(FIX, [("A", p) for p in paths], repo=str(REPO),
                   read=_plain)
    got = {r["path"]: r["why"] for r in res["refused"]}
    assert got[paths[0]] == "shadows the scoring module json"
    assert got[paths[2]] == "shadows the scoring module os"
    assert paths[1] in got  # yaml is installed in the venv
    ok = ["docs/json/notes.md", "tests/test_new.py"]
    assert wc.check(FIX, [("A", p) for p in ok], repo=str(REPO),
                    read=_plain)["refused"] == []


def test_the_scoring_list_holds_evalcard_checklib_and_the_scorecard():
    mods = wc.scoring_modules(str(REPO))
    lib = wc.SK + "scripts/lib/"
    assert {lib + "evalcard.py", lib + "checklib.py", lib + "e2elib.py",
            lib + "benchlib.py", wc.SK + "scripts/bench.py"} <= mods
    # the pipeline bench.py scores stays fixable
    assert wc.SK + "scripts/gate.py" not in mods
    paths = [lib + "evalcard.py", lib + "checklib.py",
             "docs/check-scorecard.jsonl", "docs/check-scorecard.md"]
    res = wc.check(FIX, [("M", p) for p in paths], repo=str(REPO))
    assert {r["path"]: r["class"] for r in res["refused"]} == \
        {p: "scorers" for p in paths}


ORDINARY = '''import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "evals"))
import writeset_check as wc  # noqa: E402


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("HWDE_X", str(tmp_path))
    monkeypatch.setattr(wc, "FIX_PREFIX", "x/")
    return tmp_path


def test_it(env):
    assert os.environ.get("HWDE_X") == str(env)
    assert json.loads("[1]") == [1]
'''


def test_an_ordinary_new_test_file_passes_the_scan():
    assert wc.scan_test(ORDINARY) is None
    res = wc.check(FIX, [("A", "tests/test_ordinary.py")], repo=str(REPO),
                   read=lambda p: ORDINARY)
    assert res["refused"] == []


def test_a_new_test_that_reaches_into_pytest_or_globals_is_refused():
    bad = {
        "import _pytest\n": "imports _pytest",
        "from _pytest.monkeypatch import MonkeyPatch\n":
            "imports from _pytest.monkeypatch",
        "def pytest_collection_modifyitems(items):\n    items.clear()\n":
            "defines the pytest hook pytest_collection_modifyitems",
        "import sys\nsys.modules['bench'] = None\n":
            "assigns into the imported sys",
        "import sys\nb = sys.modules.get('bench')\n": "uses sys.modules",
        "import builtins\n": "imports builtins",
        "import bench\nbench.score = lambda *a: 1\n":
            "assigns into the imported bench",
        "import os\nos.environ['X'] = '1'\n": "assigns into the imported os",
        "import sys\nsys.path.insert(0, '/tmp/x')\n":
            "changes sys.path to a path not built from __file__",
    }
    for src, why in bad.items():
        assert wc.scan_test(src) == why, src
        res = wc.check(FIX, [("A", "tests/test_x.py")], repo=str(REPO),
                       read=lambda p, s=src: s)
        assert res["refused"] == [{"path": "tests/test_x.py", "status": "A",
                                   "class": "checks", "why": why}], src
