"""lib/boardreg.py: a workspace's part number comes from the register.yaml
beside it (the boards repo root), matched on the rev's `dir`; hwde never
invents one."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".claude" / "skills" / "hwde" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

from lib import boardreg, env  # noqa: E402

REG = """products:
  PCB-0001:
    title: USB-C PD trigger
    revs:
      A: {dir: pd-lite, date: 2026-09-24, bom: pd-lite/fab/BOM.csv}
      B: {dir: pd-lite-dip, date: 2026-09-24, change: "DIP switch"}
  PCB-0002:
    title: buck
    revs:
      A: {dir: buck, date: 2026-09-01}
"""


def boards(tmp_path: Path, reg: str | None = REG) -> Path:
    root = tmp_path / "root"
    for d in ("pd-lite", "pd-lite-dip", "buck", "stranger"):
        (root / d).mkdir(parents=True)
    if reg is not None:
        (root / "register.yaml").write_text(reg, encoding="utf-8")
    return root


def test_listed_board_gets_product_and_rev(tmp_path):
    root = boards(tmp_path)
    pn, why = boardreg.part_number(root / "pd-lite-dip")
    assert why == ""
    assert (pn["pn"], pn["product"], pn["rev"], pn["title"]) == (
        "PCB-0001-B", "PCB-0001", "B", "USB-C PD trigger")
    assert boardreg.part_number(root / "buck")[0]["pn"] == "PCB-0002-A"


def test_unlisted_board_has_no_number(tmp_path):
    root = boards(tmp_path)
    pn, why = boardreg.part_number(root / "stranger")
    assert pn is None and "stranger is not in" in why


def test_no_register_has_no_number(tmp_path):
    root = boards(tmp_path, reg=None)
    pn, why = boardreg.part_number(root / "pd-lite")
    assert pn is None and "no register.yaml" in why


def test_duplicate_or_malformed_entry_has_no_number(tmp_path):
    root = boards(tmp_path, REG + """  PCB-0003:
    title: copy
    revs:
      A: {dir: buck}
  PCB-12:
    title: bad
    revs:
      O: {dir: pd-lite}
""")
    pn, why = boardreg.part_number(root / "buck")
    assert pn is None and "listed 2 times" in why
    pn, why = boardreg.part_number(root / "pd-lite")   # listed twice too
    assert pn is None
    root2 = boards(tmp_path / "b", """products:
  PCB-12:
    revs:
      O: {dir: buck}
""")
    pn, why = boardreg.part_number(root2 / "buck")
    assert pn is None and "not a PCB-NNNN-R" in why


def test_unreadable_register_has_no_number(tmp_path):
    root = boards(tmp_path, "products: [unclosed")
    pn, why = boardreg.part_number(root / "buck")
    assert pn is None and "unreadable" in why


def test_boards_root_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HWDE_BOARDS_ROOT", str(tmp_path / "elsewhere"))
    assert env.boards_root() == tmp_path / "elsewhere"
    assert env.is_boards_dir(tmp_path / "elsewhere")
    assert not env.is_boards_dir(tmp_path)
    assert env.is_boards_dir(tmp_path / "x" / "boards")    # fixture layout
    monkeypatch.delenv("HWDE_BOARDS_ROOT")
    monkeypatch.delenv("AIEE_BOARDS_ROOT", raising=False)
    assert env.boards_root() == Path.home() / "dev" / "boards"
