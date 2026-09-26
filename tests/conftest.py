"""Suite-wide guards: no test may file a document in the real register, and a
test marked `kicad_recorded` runs only on the kicad-cli its numbers were
recorded on (RECORDED_KICAD). On any other version it is skipped with the
reason, because the numbers move for known reasons (LEARNINGS 2026-08-27,
"KiCad 10.0.5 vs 10.0.3 deltas") until someone re-baselines them on purpose.
"""
import functools
import os
import shutil
import sys
from pathlib import Path

import pytest

RECORDED_KICAD = (10, 0, 3)


@functools.cache
def _kicad_version() -> tuple[int, ...]:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude"
                           / "skills" / "hwde" / "scripts" / "lib"))
    import env
    cli = env.find_kicad_cli()
    return env.kicad_cli_version(cli) if cli else ()


def pytest_collection_modifyitems(config, items):
    marked = [i for i in items if i.get_closest_marker("kicad_recorded")]
    if not marked:
        return
    ver = _kicad_version()
    if ver[:3] == RECORDED_KICAD:
        return
    have = ".".join(map(str, ver)) or "no kicad-cli"
    skip = pytest.mark.skip(reason=(
        f"numbers recorded on KiCad {'.'.join(map(str, RECORDED_KICAD))}, "
        f"this is {have} (LEARNINGS 2026-08-27)"))
    for item in marked:
        item.add_marker(skip)


@pytest.fixture(autouse=True)
def _never_file_documents(monkeypatch):
    for k in [k for k in os.environ if k.startswith("DOC_")]:
        monkeypatch.delenv(k)
    dirs = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if d and not os.access(os.path.join(d, "cc-docs"), os.X_OK)]
    monkeypatch.setenv("PATH", os.pathsep.join(dirs))
    assert shutil.which("cc-docs") is None
