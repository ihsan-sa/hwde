"""Generator for the usb-buck ROOT schematic (thin stitching sheet).

The schematic SOURCE is this package of Python generators; every
`kicad/*.kicad_sch`, the `.kicad_pro` and `kicad/decoupling.json` are BUILD
OUTPUT. Rebuild the whole design from scratch:

    .venv/Scripts/python boards/usb-buck/kicad/gen/root.py

(run kicad/gen/lib_pin_types.py first after any library refresh - the pulled
symbols' electrical pin types are junk and ERC cannot pass on them.)

Hierarchy (architecture/sheets.md - the sheet NAMES are contractual, they
appear verbatim in netlist net names and in constraints.json):

    usb-buck (root, this file)
      +- usb    J1 micro-B + U3 USBLC6      -> USB_DP, USB_DM sheet pins
      +- power  U2 AP63203 buck + L/C       -> no sheet pins (rails only)
      +- mcu    U1 STM32F103 + clock/IO/SWD -> USB_DP, USB_DM sheet pins

Net-name mechanism (verified in tests/s7_regen/hierdemo): power SYMBOLS make
a net global with a BARE name and need no sheet pin (VBUS, +3V3, GND); a
child net merged with the root through a sheet pin takes the ROOT-side label
(/USB_DP, /USB_DM); a child-internal label becomes /<sheet>/NAME. Both
children expose the same two names, and the root's two local labels per name
merge by name on this sheet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/usb-buck
REPO = HERE.parents[4]           # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(HERE.parent))    # sibling sheet generators

import schlib  # noqa: E402
import mcu_sheet  # noqa: E402
import power_sheet  # noqa: E402
import usb_sheet  # noqa: E402

PAIR = ["USB_DP", "USB_DM"]


def build() -> schlib.Project:
    root = schlib.Sheet("usb-buck",
                        title="usb-buck: USB-powered STM32F103 bench board",
                        paper="A3", date="2026-07-28", company="ai-ee",
                        pwr_base=1)
    proj = schlib.Project(root)
    # Sheet pins stack down each symbol's LEFT edge and are wired 7.62 mm
    # further left to the root labels, so the strip left of x=152.40 stays
    # clear. Both children get the same `nets` order.
    proj.add_sheet(usb_sheet.build(), at=(152.40, 63.50),
                   size=(50.80, 25.40), nets=PAIR)
    proj.add_sheet(power_sheet.build(), at=(152.40, 114.30),
                   size=(50.80, 25.40), nets=[])
    proj.add_sheet(mcu_sheet.build(), at=(152.40, 165.10),
                   size=(50.80, 25.40), nets=PAIR)
    return proj


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else HERE.parents[1]  # .../kicad
    try:
        proj = build()
        sch = proj.save(out_dir, decoupling=out_dir / "decoupling.json")
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.usb-buck", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.usb-buck", "status": "pass",
        "root": str(sch),
        "files": sorted(str(p) for p in out_dir.glob("*.kicad_sch")),
        "project": str(out_dir / "usb-buck.kicad_pro"),
        "decoupling": str(out_dir / "decoupling.json"),
        "decoupling_associations": len(proj.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
