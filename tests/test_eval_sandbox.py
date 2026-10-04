"""evals/e2e_run.py's sandbox: a design run cannot read the hidden bounds,
the repo's tests/ or results/, its .git, ~/dev/boards or the box state, and
can read its /work and the toolchain.  Linux with bwrap only."""
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "evals"))
import e2e_run  # noqa: E402

pytestmark = pytest.mark.skipif(
    sys.platform != "linux" or not shutil.which("bwrap"),
    reason="the e2e sandbox is bwrap, Linux only")


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


def test_work_and_system_are_readable():
    seen = e2e_run.probe(["/work", "/usr/bin/env"])
    assert seen == {"/work": True, "/usr/bin/env": True}


def test_allowed_tools_scope_bash():
    """The nested run gets no unscoped Bash: each Bash grant names its
    command, and the hwde arm may run the skill's scripts with python3."""
    for arm, tools in e2e_run.ALLOWED_TOOLS.items():
        assert "Bash" not in tools, arm
        assert all(t.endswith(")") for t in tools if t.startswith("Bash")), arm
    assert ("Bash(python3 .claude/skills/hwde/scripts/*)"
            in e2e_run.ALLOWED_TOOLS["hwde"])
    assert not any("python3:" in t for t in e2e_run.ALLOWED_TOOLS["hwde"])
