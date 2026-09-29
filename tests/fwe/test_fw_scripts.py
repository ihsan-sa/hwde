"""/fwe router, scaffold, host-test runner and cross build.

Each case builds its own workspace under tmp_path. The cross build runs on
the real motor-driver board and skips when the boards repo or the pinned
toolchain is absent.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "fwe" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fw_build  # noqa: E402
import fw_scaffold  # noqa: E402
import fw_test  # noqa: E402
import task_router  # noqa: E402
from _boards import board_path, need_board  # noqa: E402
from test_pinmap import motor_fixture  # noqa: E402

BOARD = "bldc-motor-driver"


def run(mod, argv, tmp_path):
    out = tmp_path / "out.json"
    rc = mod.main([*argv, "--out", str(out)])
    return rc, json.loads(out.read_text())


def test_router_table_is_complete():
    assert task_router.validate() == []


@pytest.mark.parametrize("task,verb", [
    ("build it with warnings as errors", "build"),
    ("run the host unit tests", "test"),
    ("regenerate the pin map", "pinmap"),
    ("scaffold the firmware", "scaffold"),
    ("write sensored six-step", "stage"),
    ("install the toolchain", "setup"),
])
def test_router_picks_one_verb(task, verb):
    assert task_router.match(task) == [verb]


def test_router_asks_for_a_board_and_rejects_nonsense(tmp_path):
    rc, res = run(task_router, ["--verb", "build"], tmp_path)
    assert (rc, res["status"]) == (1, "needs_args")
    rc, res = run(task_router, ["--task", "make coffee"], tmp_path)
    assert (rc, res["status"]) == (1, "unknown")
    rc, res = run(task_router, ["--verb", "setup"], tmp_path)
    assert rc == 0 and res["steps"][0]["cmd"].endswith("fwe_setup.py")


def test_scaffold_copies_missing_files_and_keeps_existing(tmp_path):
    ws = motor_fixture(tmp_path)
    mine = ws / "firmware" / "config" / "fw_config.h"
    mine.parent.mkdir(parents=True)
    mine.write_text("/* the board's own */\n")
    rc, res = run(fw_scaffold, ["--workspace", str(ws)], tmp_path)
    assert rc == 0, res
    assert "config/fw_config.h" in res["kept"]
    assert mine.read_text() == "/* the board's own */\n"
    assert "CMakeLists.txt" in res["copied"]
    assert (ws / "firmware" / "gen" / "board_pins.h").is_file()
    rc, res = run(fw_scaffold, ["--workspace", str(ws)], tmp_path)
    assert rc == 0 and res["copied"] == []


def _fw(tmp_path, test_src: str) -> Path:
    fw = tmp_path / "ws" / "firmware"
    (fw / "control").mkdir(parents=True)
    (fw / "tests").mkdir()
    (fw / "control" / "twice.c").write_text("int twice(int x) { return 2 * x; }\n")
    (fw / "tests" / "test_twice.c").write_text(
        "int twice(int x);\nint main(void) { return " + test_src + "; }\n")
    return fw.parent


@pytest.mark.parametrize("expr,status,rc", [
    ("twice(2) == 4 ? 0 : 1", "pass", 0),
    ("twice(2) == 5 ? 0 : 1", "fail", 1),
    ("undeclared_thing", "compile_error", 1),
])
def test_host_tests_pass_fail_and_compile_error(tmp_path, expr, status, rc):
    if not (shutil.which("cc") or shutil.which("gcc")):
        pytest.skip("no host C compiler")
    got_rc, res = run(fw_test, ["--workspace", str(_fw(tmp_path, expr))], tmp_path)
    assert got_rc == rc
    assert [t["status"] for t in res["tests"]] == [status]


def test_build_refuses_a_workspace_without_firmware(tmp_path):
    (tmp_path / "ws").mkdir()
    rc, res = run(fw_build, ["--workspace", str(tmp_path / "ws")], tmp_path)
    assert rc == 2 and "fw_scaffold" in res["error"]


def _toolchain_or_skip():
    env = fw_build.fwenv.tool_env()
    if not shutil.which("arm-none-eabi-gcc", path=env["PATH"]):
        pytest.skip("pinned arm toolchain not installed (fwe_setup.py)")


def test_motor_driver_scaffolds_builds_and_passes_host_tests(tmp_path):
    need_board(BOARD)
    _toolchain_or_skip()
    ws = tmp_path / board_path(BOARD).name
    shutil.copytree(board_path(BOARD) / "kicad", ws / "kicad")
    rc, res = run(fw_scaffold, ["--workspace", str(ws)], tmp_path)
    assert rc == 0, res
    rc, res = run(fw_build, ["--workspace", str(ws)], tmp_path)
    assert rc == 0, res.get("log_tail") or res
    assert res["size"]["text"] < 128 * 1024
    assert set(res["artifacts"]) == {"elf", "bin", "hex"}
    rc, res = run(fw_test, ["--workspace", str(ws)], tmp_path)
    assert rc == 0, [t for t in res["tests"] if t["status"] != "pass"]
    # a board re-spin the firmware has not seen fails the build at the pin map
    net = next((ws / "kicad").glob("*.net"))
    net.write_text(net.read_text().replace('LED_STATUS"', 'LED_STAT2"', 1))
    rc, res = run(fw_build, ["--workspace", str(ws)], tmp_path)
    assert (rc, res["step"]) == (1, "pinmap")
