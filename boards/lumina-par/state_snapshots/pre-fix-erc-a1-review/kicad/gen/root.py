"""Root generator for lumina-par (LUM-PAR-A): stitches the five sheets.

One generator per sheet (power/control/drivers/thermal/led_if) + this root,
per SPEC P4.  The Python is the source; `kicad/*.kicad_sch` is build output.

    .venv/Scripts/python.exe boards/lumina-par/kicad/gen/root.py

WHAT THE ROOT IS FOR, ELECTRICALLY
----------------------------------
Nothing on this sheet is a part.  Its whole job is NAMING: `add_sheet` stacks
each child's hier pins on the sheet symbol's left edge and wires each one out
to a ROOT-LOCAL LABEL of the same name, and a root-crossed net is the only
thing KiCad spells `/NAME`.  A net named by a sheet-local label alone comes
out `/<sheet>/NAME` (measured on the sibling board's shipped netlist:
boards/lumina-carrier/work/board.net).  sheets.md s2 + p4-wiring-notes s5.6
require the bare `/NAME` spelling because P5-P8 silently no-op on any net
whose name does not match constraints.json.

The sheet-pin list for each child is read from that child's own
`Sheet.hier_pins`, never hand-transcribed here - the same discipline the
carrier root uses.  Hier pins carry BARE names (`EN_OK`, `LED0_A`, ...); the
root label of the same name is what adds the leading `/`.

RAILS ARE NOT STITCHED HERE.  `GND` / `+12V` / `+3V3` / `+48V_SW` are global
power SYMBOLS placed inside the sheets, so they are already global and bare
and need no root entry (schlib.add_sheet's docstring).  All four PWR_FLAGs
live on `power` and nowhere else; adding one here would raise
`power_out <-> power_out`.

/PWM0../PWM3 - THE ONE NAMING DECISION THIS STITCH SETTLES
-----------------------------------------------------------
`constraints.json.high_speed` names the four PWM nets `/PWM0`..`/PWM3`, but
sheets.md s2 files them as `control`-internal, which would have produced
`/control/PWM0..3` - a `netlist_audit` missing_net, and a silent drop from
all seven high_speed consumers (check_return_path, planes_gen,
route_critical, rules_gen, stitch_vias, constraints_lint, netlist_audit) on
the board whose hardest requirement is PAR-REQ-01's 141 ns wall.  Per the
orchestrator's ruling the four `("PWM<n>", "input")` tuples were appended to
`control.HIER_NETS`, so they cross the root here and take the `/PWM0..3`
spelling.  They have no consumer on the root side - the crossing exists to
NAME the net, which is legal and electrically inert.  Verified, not assumed:
project ERC 0/0 and the exported netlist carries `/PWM0`..`/PWM3`.

`/ENABLE`, `/ID_ADC`, `/I2C_SCL`, `/I2C_SDA` remain `control`-internal and
come out `/control/NAME`.  No constraint names any of them; reported, not
changed.

SHEET GEOMETRY
--------------
Boxes are packed top-down into A2 columns, starting a new column when the
next sheet would pass COL_MAX_Y.  COL_MAX_Y is 200 mm rather than the
carrier's 400: five boxes fit in one 277 mm column, but that leaves two
thirds of a 594 mm sheet blank, and 200 splits them 3 / 2.  Cosmetic only -
the netlist is identical either way.
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

import control as control_sheet  # noqa: E402
import drivers as drivers_sheet  # noqa: E402
import led_if as led_if_sheet  # noqa: E402
import power as power_sheet  # noqa: E402
import thermal as thermal_sheet  # noqa: E402

GRID = 1.27
WIDTH = 76.2          # 60 grid units
GAP = 12.7            # vertical gap between stacked sheets
COL_X = (25.4, 152.4, 279.4)
COL_MAX_Y = 200.0
TOP_Y = 25.4


def _snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


def _height(n_pins: int) -> float:
    """schlib needs h > 2*GRID*n_pins for the pin stack; add a margin."""
    return _snap(max(38.1, 2 * GRID * (n_pins + 3)))


def build() -> schlib.Project:
    root = schlib.Sheet("lumina-par",
                        title="LUMINA par LUM-PAR-A: root", paper="A2",
                        date="2026-08-07")
    proj = schlib.Project(root)

    # Signal-flow order: rail entry, then the logic that gates it, then the
    # converters, then the two sensing blocks.
    children = [power_sheet.build(), control_sheet.build(),
                drivers_sheet.build(), thermal_sheet.build(),
                led_if_sheet.build()]

    x_i, y = 0, TOP_Y
    for child in children:
        nets = sorted(child.hier_pins)
        h = _height(len(nets))
        if y + h > COL_MAX_Y and y > TOP_Y:
            x_i += 1
            y = TOP_Y
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
        print(json.dumps({"script": "gen.lumina-par", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.lumina-par",
        "status": "pass",
        "root": str(sch),
        "files": sorted(p.name for p in out_dir.glob("*.kicad_sch")),
        "sheet_pins": {c.name: sorted(c.hier_pins) for c in proj.children},
        "decoupling_associations": len(proj.decoupling),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
