"""fwelib/fwenv.py - where /fwe's pinned tools live, and hwde's helpers it reuses.

Tools install under FWE_TOOLS_DIR (default ~/.local/fwe-tools) from
reference/toolchain.lock.json: tarballs into <dir>/<name>-<version>/, pinned
sources into <dir>/src/<name>-<version>/. Nothing here needs root.

hwde's lib (env.boards_root, simlib.parse_netlist) is imported read-only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
LOCK = SKILL / "reference" / "toolchain.lock.json"
HWDE_SCRIPTS = SKILL.parent / "hwde" / "scripts"
if str(HWDE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HWDE_SCRIPTS))

from lib import env as hwde_env  # noqa: E402  (hwde's lib; fwe's own is fwelib so the names never clash)


def tools_dir() -> Path:
    return Path(os.environ.get("FWE_TOOLS_DIR") or Path.home() / ".local" / "fwe-tools")


def lock() -> dict:
    return json.loads(LOCK.read_text(encoding="utf-8"))


def tool_root(entry: dict) -> Path:
    return tools_dir() / f"{entry['name']}-{entry['version']}"


def source_root(entry: dict) -> Path:
    return tools_dir() / "src" / f"{entry['name']}-{entry['version']}"


def bin_dirs() -> list[Path]:
    """The bin directory of every pinned tarball, lock order."""
    return [tool_root(t) / t["bin"] for t in lock()["tarballs"]]


def tool_env() -> dict:
    """os.environ with the pinned tools first on PATH."""
    e = dict(os.environ)
    e["PATH"] = os.pathsep.join([str(p) for p in bin_dirs()] + [e.get("PATH", "")])
    return e


def source(name: str) -> Path:
    for s in lock()["sources"]:
        if s["name"] == name:
            return source_root(s)
    raise KeyError(name)


def boards_root() -> Path:
    return hwde_env.boards_root()


def workspace(arg: str) -> Path:
    """A board workspace from a path, or a name under the boards root."""
    ws = Path(arg).expanduser()
    return ws if ws.is_dir() else boards_root() / arg


def emit(res: dict, out: str | None) -> None:
    """The SPEC contract's output: JSON to --out when given, else stdout."""
    text = json.dumps(res, indent=2)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
