"""Root generator for lumina-carrier (LUM-CAR-A): stitches the five sheets.

One generator per sheet (poe/eth/pwr/mcu/expansion) + this root, per SPEC P4.

The sheet-pin list for each child is read from that child's own
`Sheet.hier_pins` rather than hand-transcribed here. That matters: two sheets
independently discovered that `sheets.md` s1.3 mis-files `/poe/CDB` as
poe-internal while naming U20's EN (on the pwr sheet) as a member - which
cannot both be true. Both resolved it by exposing CDB, so reading the real
`hier_pins` picks that up automatically and the final net is `/CDB`.

Rails (GND, V48_RAW, V48_RTN, +48V_SW, +12V, +3V3) are GLOBAL power symbols
placed inside the sheets and need no root entry - see schlib.add_sheet's
docstring and poe.py's `_global_rail`.

Rebuild:  .venv/Scripts/python.exe boards/lumina-carrier/kicad/gen/root.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(HERE.parent))

import schlib  # noqa: E402

import eth as eth_sheet  # noqa: E402
import expansion as expansion_sheet  # noqa: E402
import mcu as mcu_sheet  # noqa: E402
import poe as poe_sheet  # noqa: E402
import pwr as pwr_sheet  # noqa: E402

GRID = 1.27
WIDTH = 76.2          # 60 grid units
GAP = 12.7            # vertical gap between stacked sheets
COL_X = (25.4, 152.4, 279.4)


def _snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


def _height(n_pins: int) -> float:
    """schlib needs h > 2*GRID*n_pins for the pin stack; add a margin."""
    return _snap(max(38.1, 2 * GRID * (n_pins + 3)))


def build() -> schlib.Project:
    root = schlib.Sheet("lumina-carrier",
                        title="LUMINA carrier LUM-CAR-A: root", paper="A2")
    proj = schlib.Project(root)

    children = [poe_sheet.build(), eth_sheet.build(), pwr_sheet.build(),
                mcu_sheet.build(), expansion_sheet.build()]

    # Pack top-down into columns, starting a new column when the next sheet
    # would run off the bottom of the A2 sheet.
    x_i, y = 0, 25.4
    for child in children:
        nets = sorted(child.hier_pins)
        h = _height(len(nets))
        if y + h > 400.0:
            x_i += 1
            y = 25.4
        if x_i >= len(COL_X):
            raise ValueError("ran out of columns on A2")
        proj.add_sheet(child, at=(COL_X[x_i], _snap(y)),
                       size=(WIDTH, h), nets=nets)
        y = _snap(y + h + GAP)
    return proj


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]  # .../kicad
    try:
        proj = build()
        sch = proj.save(out_dir, decoupling=out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.lumina-carrier", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.lumina-carrier",
        "status": "pass",
        "root": str(sch),
        "files": sorted(p.name for p in out_dir.glob("*.kicad_sch")),
        "sheet_pins": {c.name: sorted(c.hier_pins) for c in proj.children},
        "decoupling_associations": len(proj.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
