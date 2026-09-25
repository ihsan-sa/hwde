"""board_rename.py and redoc_boards.py: the boards repo's move to <PN>_<name>
directories, run here on a copy of the golden blinky2 project in a scratch
boards root (never the boards repo)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import board_rename  # noqa: E402
import redoc_boards  # noqa: E402
from lib import env  # noqa: E402

REG = """# the register's own comment survives
products:
  PCB-0001:
    title: blinky
    revs:
      A: {dir: blinky2, date: 2026-09-01, bom: blinky2/fab/BOM.csv}
  PCB-0002:
    title: other
    revs:
      A: {dir: other, date: 2026-09-02}
"""


def scratch(tmp_path: Path) -> Path:
    root = tmp_path / "boards"
    ws = root / "blinky2"
    shutil.copytree(REPO / "tests" / "golden" / "blinky2", ws / "kicad")
    (ws / "fab").mkdir()
    (ws / "fab" / "blinky2_gerbers.zip").write_bytes(b"zip")
    (ws / "state.json").write_text(json.dumps({
        "board": "blinky2", "workspace": "boards/blinky2",
        "artifacts": {
            "pcb": {"path": "kicad/blinky2.kicad_pcb", "kind": "pcb"},
            "gerbers": {"path": "fab/blinky2_gerbers.zip", "kind": "gerbers"},
            "constraints": {"path": "kicad/constraints.json",
                            "kind": "constraints"}}}), encoding="utf-8")
    (root / "other").mkdir()
    (root / "stray").mkdir()
    (root / "register.yaml").write_text(REG, encoding="utf-8")
    return root


def rename(capsys, *argv) -> tuple[int, dict]:
    code = board_rename.main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_dry_run_writes_nothing(tmp_path, capsys):
    root = scratch(tmp_path)
    code, out = rename(capsys, "--all", "--dry-run", "--root", str(root))
    assert code == 0
    assert [(b["from"], b["to"]) for b in out["boards"]] == [
        ("blinky2", "PCB-0001-A_blinky2"), ("other", "PCB-0002-A_other")]
    assert (root / "blinky2").is_dir()
    assert (root / "register.yaml").read_text(encoding="utf-8") == REG


def test_rename_moves_dir_files_state_and_register(tmp_path, capsys):
    root = scratch(tmp_path)
    code, out = rename(capsys, "blinky2", "--no-verify", "--root", str(root))
    assert code == 0, out
    ws = root / "PCB-0001-A_blinky2"
    assert not (root / "blinky2").exists()
    new = "PCB-0001-A_blinky2"
    names = {p.name for p in (ws / "kicad").iterdir()}
    assert {f"{new}.kicad_pro", f"{new}.kicad_sch", f"{new}.kicad_pcb",
            "constraints.json"} <= names
    assert not any(n.startswith("blinky2.") for n in names)
    pro = json.loads((ws / "kicad" / f"{new}.kicad_pro").read_text())
    assert pro["meta"]["filename"] == f"{new}.kicad_pro"
    sch = (ws / "kicad" / f"{new}.kicad_sch").read_text(encoding="utf-8")
    assert '(project "blinky2"' not in sch
    assert f'(project "{new}"' in sch
    assert out["boards"][0]["project_refs_rewritten"] > 0
    st = json.loads((ws / "state.json").read_text())
    assert st["board"] == "blinky2"                 # the human name stays
    assert st["workspace"] == f"boards/{new}"
    assert st["artifacts"]["pcb"]["path"] == f"kicad/{new}.kicad_pcb"
    assert st["artifacts"]["gerbers"]["path"] == f"fab/{new}_gerbers.zip"
    assert st["artifacts"]["constraints"]["path"] == "kicad/constraints.json"
    assert (ws / "fab" / f"{new}_gerbers.zip").is_file()
    reg = (root / "register.yaml").read_text(encoding="utf-8")
    assert f"A: {{dir: {new}, date: 2026-09-01, bom: {new}/fab/BOM.csv}}" \
        in reg
    assert "{dir: other," in reg and reg.startswith("# the register's own")
    # a second run is a no-op for a board already renamed
    code, out = rename(capsys, "PCB-0001-A", "--no-verify", "--root", str(root))
    assert code == 0 and out["boards"][0]["done"] is True


def test_refusals(tmp_path, capsys):
    root = scratch(tmp_path)
    (root / "PCB-0002-A_other").mkdir()
    code, out = rename(capsys, "stray", "other", "--no-verify",
                       "--root", str(root))
    assert code == 1
    why = [b["refused"] for b in out["boards"]]
    assert "stray is not in" in why[0]
    assert "already exists" in why[1]
    assert (root / "other").is_dir()


def test_kicad_cli_opens_the_renamed_project(tmp_path, capsys):
    if env.find_kicad_cli() is None:
        pytest.skip("no kicad-cli (set HWDE_KICAD_CLI)")
    root = scratch(tmp_path)
    code, out = rename(capsys, "blinky2", "--root", str(root))
    assert code == 0, out
    assert out["boards"][0]["result"] == {"verified": True, "problems": []}
    prl = {p.name for p in (root / "PCB-0001-A_blinky2" / "kicad").glob(
        "*.kicad_prl")}
    assert prl == set()   # the check's own .kicad_prl files are cleaned up


def test_redoc_dry_run_names_the_part_number(tmp_path, capsys):
    root = scratch(tmp_path)
    code = redoc_boards.main(["--root", str(root), "--dry-run"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out
    [row] = out["boards"]          # `other` has no workspace: not listed
    args = row["cc_docs"]
    assert row["pn"] == "PCB-0001-A"
    assert args[args.index("--describes") + 1] == "PCB-0001-A"
    code = redoc_boards.main(["nope", "--root", str(root), "--dry-run"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1 and out["boards"][0]["error"] == "no workspace"
