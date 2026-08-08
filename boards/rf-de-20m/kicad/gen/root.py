"""Root generator for rf-de-20m: stitches the three sheets.

    .venv/Scripts/python boards/rf-de-20m/kicad/gen/root.py

WHAT THE ROOT IS FOR, ELECTRICALLY
----------------------------------
Nothing on this sheet is a part - `architecture/sheets.md` opens by saying so
("a root that contains nothing but the sheet symbols and the inter-sheet
wiring"). Its whole job is NAMING. `Project.add_sheet` stacks each child's
hierarchical pins on the sheet symbol's left edge and wires each one out to a
ROOT-LOCAL LABEL of the same name, and a root-crossed net is the only thing
KiCad spells `/NAME`. A net named by a sheet-local label alone comes out
`/<sheet>/NAME`.

**Exactly one signal net crosses a sheet boundary: `/SW`**, the drain node.
sheets.md s1 and s6 note 2 make this a P4 obligation in the strongest terms:
"P4 must place a root-sheet local label spelled SW on the inter-sheet wire",
because six `constraints.json` entries (high_speed, power, voltages, and both
voltage_pairs sides) name it `/SW`, and every P5-P8 consumer silently no-ops
on a net whose name does not match.

That label is exactly what `add_sheet(..., nets=["SW"])` writes, once per
child. **BOTH children expose it**, so the root subgraph for `/SW` is
wire + label + TWO sheet pins. That matters and is not incidental: a
root-crossed net exposed by only ONE child gives wire + label + one sheet pin,
which KiCad 10.0.3 flags as `label_dangling` ("Label not connected") - the
lumina-par run measured it, proved a second same-named label does NOT satisfy
the rule, and had to fall back to re-spelling its constraints
(LEARNINGS 2026-08-07 [erc]). Here the net genuinely spans two sheets, so the
bare `/SW` spelling is available and is taken.

RAILS ARE NOT STITCHED HERE. `GND`, `+40V` and `+5V` are global power SYMBOLS
placed inside the sheets, so they are already global and bare and need no root
entry. All three PWR_FLAGs live on `hk` and nowhere else - a second flag on
the same net raises `power_out <-> power_out`.

Everything else is sheet-internal ON PURPOSE and carries its sheet prefix:
`/stage/DRIVE`, `/stage/GATE_ON`, `/stage/GATE_OFF`, `/stage/GATE_Q1`,
`/stage/GATE_Q2`, `/stage/L201_MID`, `/tank/TANK_A`, `/tank/TANK_B`,
`/tank/RFOUT`, `/hk/{VCC,BST,BUCK_SW,FB,RON,RINJ}`. sheets.md s1 is explicit
that these must NOT be "tidied" into bare names: promoting a sheet-internal
net to a root-crossing name is exactly the label_dangling case above, and
buying the bare name would mean adding a PART to the root.

The sheet-pin list for each child is read from that child's own
`Sheet.hier_pins`, never hand-transcribed here.

SHEET GEOMETRY
--------------
Three boxes stacked in one A3 column, in signal-flow order (hk -> stage ->
tank). Cosmetic only; the netlist is identical either way.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/rf-de-20m
REPO = BOARD.parents[1]          # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(HERE.parent))   # sibling sheet generators

import schlib  # noqa: E402

import genlib  # noqa: E402
import hk as hk_sheet        # noqa: E402
import stage as stage_sheet  # noqa: E402
import tank as tank_sheet    # noqa: E402

GRID = 1.27
WIDTH = 88.9          # 70 grid units
GAP = 19.05
COL_X = 63.5
TOP_Y = 38.1


def _snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


def _height(n_pins: int) -> float:
    """schlib needs h > 2*GRID*n_pins for the left-edge pin stack."""
    return _snap(max(38.1, 2 * GRID * (n_pins + 3)))


def build() -> schlib.Project:
    root = schlib.Sheet("rf-de-20m",
                        title="rf-de-20m: root - 20 MHz Class E GaN stage, "
                              "200 W into 50 ohm",
                        paper="A3", date="2026-08-07", company="ai-ee",
                        pwr_base=1)
    proj = schlib.Project(root)

    # Signal-flow order: rail entry and housekeeping, the switch, the tank.
    children = [hk_sheet.build(), stage_sheet.build(), tank_sheet.build()]

    y = TOP_Y
    for child in children:
        nets = sorted(child.hier_pins)
        h = _height(len(nets))
        proj.add_sheet(child, at=(COL_X, _snap(y)), size=(WIDTH, h), nets=nets)
        y = _snap(y + h + GAP)

    # A human opening the root must be told what the root does and does not do.
    for i, line in enumerate([
        "ROOT SHEET - NO PARTS BY DESIGN (sheets.md s1).",
        "---",
        "The ONLY inter-sheet signal net is /SW (the drain node,",
        "142.5 V pk, 9.17 A rms). Its bare /SW spelling comes from",
        "the root-local labels written by add_sheet, and six",
        "constraints.json entries depend on it. Both `stage` and",
        "`tank` expose it, which is what keeps the root label",
        "connected - a root label with only ONE sheet pin raises",
        "label_dangling in KiCad 10.",
        "---",
        "GND / +40V / +5V are global POWER SYMBOLS inside the",
        "sheets and are deliberately absent here. All three",
        "PWR_FLAGs live on `hk`; a second flag anywhere else",
        "collides power_out <-> power_out.",
        "---",
        "Every other net is sheet-internal on purpose and carries",
        "its /<sheet>/ prefix. Do not 'tidy' them into bare names.",
    ]):
        root.sch.add_text(line, position=(190.5, round(38.1 + i * 5.08, 4)))

    return proj


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        proj = build()
        sch = proj.save(out_dir, decoupling=out_dir / "decoupling.json")
        hidden = sum(genlib.hide_aux_fields(p)
                     for p in sorted(out_dir.glob("*.kicad_sch")))
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.rf-de-20m", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.rf-de-20m",
        "status": "pass",
        "root": str(sch),
        "files": sorted(p.name for p in out_dir.glob("*.kicad_sch")),
        "sheet_pins": {c.name: sorted(c.hier_pins) for c in proj.children},
        "components": {c.name: len(list(c.sch.components))
                       for c in proj.children},
        "decoupling_associations": len(proj.decoupling),
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
