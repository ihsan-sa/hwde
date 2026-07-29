"""SCRATCH ONLY - P4 verification harness for the `pwr` sheet.

NOT part of the design. The real root is owned by another agent; this
throwaway root exists so the pwr sheet can be ERC'd and netlisted INSIDE a
real hierarchy (the only way to prove: +48V_SW / +12V / +3V3 come out as bare
GLOBAL nets, the four hier pins come out as /NAME, and the sheet-internal
labels come out as /pwr/NAME).

    .venv/Scripts/python boards/lumina-carrier/work/pwr_harness.py
writes boards/lumina-carrier/work/pwr_harness/{pwr_harness,pwr}.kicad_sch
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[1]
REPO = BOARD.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(BOARD / "kicad" / "gen"))

import schlib  # noqa: E402

import pwr  # noqa: E402

NETS = ["CDB", "ENABLE", "FAULT", "IMON"]


def main() -> int:
    out = HERE.parent / "pwr_harness"
    try:
        root = schlib.Sheet("pwr_harness", title="scratch", paper="A3")
        proj = schlib.Project(root)
        proj.add_sheet(pwr.build(), at=(101.60, 50.80), size=(50.80, 66.04),
                       nets=NETS)
        # Terminate every sheet pin so the scratch build carries no
        # dangling-endpoint noise; the real root wires them to its peers.
        for i, net in enumerate(NETS):
            root.power_flag(net, at=(25.40, 63.50 + i * 12.70), sym=None,
                            flag=True)
        # GND and V48_RAW are flagged on the `poe` sheet, which is absent
        # here. V48_RAW must be a RENAMED POWER SYMBOL, not a bare label: a
        # root label makes the root-local net /V48_RAW, which does not merge
        # with the pwr sheet's global bare V48_RAW (measured: U20 pin 3 then
        # reports power_pin_not_driven).
        root.power_flag("GND", at=(25.40, 152.40), sym="power:GND", flag=True)
        pwr._global_rail(root, "V48_RAW", (25.40, 165.10), "power:+48V",
                         flag=True)
        sch = proj.save(out, decoupling=out / "decoupling.json")
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"script": "pwr_harness", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({"script": "pwr_harness", "status": "pass",
                      "root": str(sch),
                      "decoupling": len(proj.decoupling)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
