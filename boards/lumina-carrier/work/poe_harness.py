"""SCRATCH ONLY - P4 verification harness for the `poe` sheet.

NOT part of the design. The real root is owned by another agent; this throwaway
root exists so the poe sheet can be ERC'd and netlisted INSIDE a real hierarchy
(the only way to prove: power symbols come out as bare global nets, hier pins
come out as /NAME, and sheet-internal labels come out as /poe/NAME).

    .venv/Scripts/python boards/lumina-carrier/work/poe_harness.py
writes boards/lumina-carrier/work/poe_harness/{poe_harness,poe}.kicad_sch
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

import poe  # noqa: E402

NETS = ["ETH_TXP", "ETH_TXN", "ETH_RXP", "ETH_RXN", "ETH_LED_LINK",
        "ETH_LED_ACT", "T2P", "CDB"]


def main() -> int:
    out = HERE.parent / "poe_harness"
    try:
        root = schlib.Sheet("poe_harness", title="scratch", paper="A3")
        proj = schlib.Project(root)
        proj.add_sheet(poe.build(), at=(101.60, 50.80), size=(50.80, 132.08),
                       nets=NETS)
        # The harness root terminates every sheet pin so the scratch build is
        # not full of dangling-endpoint noise; the real root wires them on.
        for i, net in enumerate(NETS):
            root.power_flag(net, at=(25.40, 63.50 + i * 12.70), sym=None,
                            flag=True)
        # +3V3 is produced by the `pwr` sheet, which does not exist here.
        root.power_flag("+3V3", at=(25.40, 190.50), sym="power:+3V3",
                        flag=True)
        sch = proj.save(out, decoupling=out / "decoupling.json")
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"script": "poe_harness", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({"script": "poe_harness", "status": "pass",
                      "root": str(sch),
                      "decoupling": len(proj.decoupling)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
