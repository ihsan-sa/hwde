"""Root (and only) generator for rf-term-150w.

    .venv/Scripts/python boards/rf-term-150w/kicad/gen/rf-term-150w.py

ONE SHEET, TWO NETS, SIX FOOTPRINTS
-----------------------------------
`architecture/sheets.md` opens with "ONE SHEET. P4 SPAWNS A SINGLE SCHEMATIC
AGENT." - the whole design is three electrical parts and two nets, so there is
no hierarchy, no sheet symbol and no hierarchical label anywhere in this file.

    J1 centre pin ---+--- R1 pin 1 (RF tab lap pad)
                     |
                    C1 pin 2 (insulated lead)
                    C1 pin 1 (threaded case) --- GND
    J1 shield legs --- GND
    R1 pin 2 (flange straps) --- GND
    H1..H3 pad --- GND

NET NAMING IS A CONTRACT (sheets.md s1, restated in constraints.json)
---------------------------------------------------------------------
* `/RF` must come from a ROOT-SHEET LOCAL LABEL spelled `RF`. A root local
  label is exported as `/LABEL`, so the label text here is bare `RF` and the
  netlist name is `/RF` - which is what constraints.json's high_speed, power
  and voltages entries all spell. Any other spelling makes check_current,
  check_creepage, check_return_path, rules_gen's HV/width rules and
  planes_gen's reference guarantee silently match an EMPTY set: they pass, and
  nothing is checked.
* `GND` must come from the GLOBAL POWER SYMBOL, bare, never `/GND`. Every GND
  connection here is `wire_pin(..., "GND")` immediately followed by
  `power_symbol_at_pin(..., "power:GND")`; schlib takes the symbol's VALUE
  (= the exported global net name) from the net the pin was wired to, so the
  label and the symbol cannot diverge.

WHY THERE IS EXACTLY ONE PWR_FLAG
---------------------------------
This board has no active part and no DC rail at all (`power_tree.md` s1), so
nothing drives anything. `Mechanical:MountingHole_Pad`'s pad pin is type
INPUT, and the `power:GND` symbols are power_in, so without a driver KiCad
raises both "input pin not driven" and "power input pin not driven". One
PWR_FLAG (power_out) on GND satisfies both. There is no second rail, so there
is no second flag - a duplicate would raise power_out <-> power_out.

WHY H1-H3 CARRY A PAD AND ARE STILL NOT A BOM LINE
--------------------------------------------------
`sheets.md` s2 originally specified `board_only` M3 holes. The orchestrator
superseded that for this build: the holes take `MountingHole_Pad` and their
pads are tied to GND, because each M3 screw head is a grounded metal object
sitting on the top surface anyway (`blocks.md` s2.4) and a real GND pad is
better than an accidental one. The BOM budget is unchanged because
`in_bom = False` is set at the SYMBOL - LEARNINGS 2026-07-29 [drc][gates]:
lumina-carrier's H5 had `exclude_from_bom` on the FOOTPRINT and `(in_bom yes)`
on the symbol and drew a `footprint_symbol_mismatch` at the first --parity
DRC. `MountingHole:MountingHole_3.2mm_M3_Pad` carries
`(attr exclude_from_pos_files exclude_from_bom)`, so the symbol must agree.
Result: BOM stays at 3 lines / 3 placements, 6 footprints total.

PIN MAPPING - THE TWO CALLS THAT MATTER
---------------------------------------
* **C1 pin 1 (threaded case/hex collar) -> GND, pin 2 (insulated lead) -> RF.**
  DECIDED (state.json P3, 2026-08-09; parts/5602.json) on physical grounds and
  NOT on rotor/stator identity, which no source for this part publishes: the
  case is the only terminal a hand or a tuning tool brushes, at 122.5 Vpeak,
  while transmitting - so the case is grounded whatever its internal role is.
  The symbol's pin NAMES ("STATOR" on 1, "ROTOR" on 2) are mechanical
  descriptors only; do not read a net assignment out of them.
* **R1 pin 2 = the flange, and it reaches GND only through two hand-soldered
  copper straps** to the footprint's two F.Cu lands. The bolted
  flange-to-heatsink joint is a thermal/mechanical path ONLY (418 pF =
  15.2 ohm at 25 MHz on an anodised sink - blocks.md s2.3). That fact is on
  the sheet as text as well, because it is an assembly requirement no netlist
  can express.

LAYOUT OF THE SHEET
-------------------
A4, signal left to right: J1 (its "In" pin points left, i.e. out to the mating
cable) -> C1 shunt -> R1. Every GND stub points down. Cosmetic only; the nets
are formed by label name, not by geometry.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]              # boards/rf-term-150w
REPO = BOARD.parents[1]              # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402
from schlib import ksa  # noqa: E402

NAME = "rf-term-150w"
OUT = BOARD / "kicad"
LIB = BOARD / "lib"

RF = "RF"          # root-sheet LOCAL label -> netlist "/RF"
GND = "GND"        # global power symbol   -> netlist "GND"

# --------------------------------------------------------------- part fields
# Datasheets: repo-relative paths for the two parts whose datasheet is a local
# PDF (no public stable URL), a URL for the one that has one. MPN + the
# distributor field feed P9's BOM directly (bom_cpl reads the LCSC field as its
# primary key; R1 and C1 are DigiKey-only, so they carry "DigiKey" instead and
# P9 must take them from parts/*.json or this field).
J1_FIELDS = {
    "MPN": "SMA-KWE",
    "Manufacturer": "Lian Xin Technology",
    "LCSC": "C7498154",
    "Datasheet": "boards/rf-term-150w/research/SMA-KWE_LianXin_datasheet.pdf",
}
R1_FIELDS = {
    "MPN": "T50R0-250-12X",
    "Manufacturer": "Vishay Intertechnology (Barry Industries)",
    "DigiKey": "4353-T50R0-250-12X-ND",
    "Datasheet":
        "boards/rf-term-150w/research/T50R0-250-12X_Vishay-Barry_datasheet.pdf",
}
C1_FIELDS = {
    "MPN": "5602",
    "Manufacturer": "Johanson Manufacturing Corp. (Knowles Precision Devices)",
    "DigiKey": "1956-1000-ND",
    "Datasheet": "https://mm.digikey.com/Volume0/opasdata/d220001/medias/"
                 "docus/6592/KnowlesTrimmersCatalogueweb177409287.pdf",
    # Byte-identical to the footprint's own Description property
    # (lib/aiee.pretty/CAP-ADJ-TH_2P-BD7.5_5602.kicad_mod) so DRC --parity's
    # footprint_symbol_field_mismatch clears; kept concise on purpose (see
    # the footprint's much longer `descr` for the full derivation).
    "Description": "Johanson 5602 air trimmer, 1-30pF 250VDC -65/+125C, "
                    "top-adjust panel-mount. Pad 1=CASE/THREAD -> GND, "
                    "Pad 2=LEAD -> RF (physical assignment, state.json P3 "
                    "decision 2026-08-09).",
}

# ------------------------------------------------------------- sheet notes
# Assembly/safety facts a netlist cannot carry. They are on the SHEET (not in
# properties) because the schematic PDF is what a builder reads.
# Rows are (kind, text): "h" heading, "n" body line, "b" blank spacer.
NOTES_AT = (25.4, 111.76)     # top-left of the block; text is left-justified
NOTES = [
    ("h", "ASSEMBLY AND SAFETY NOTES - BUILD REQUIREMENTS, NOT COMMENTARY"),
    ("b", ""),
    ("n", "1. R1's cold end reaches GND ONLY via the two soldered flange "
          "straps (footprint pad 2, x2)."),
    ("n", "   The bolted heatsink joint is NOT an electrical path: on an "
          "anodised finish it is 418 pF"),
    ("n", "   = 15.2 ohm at 25 MHz. Solder both straps to the loose flange "
          "BEFORE bolting R1 down."),
    ("b", ""),
    ("n", "2. The PCB rides on three 1.0 mm shims so that top copper "
          "(2.635 mm above the heatsink"),
    ("n", "   mounting plane) meets R1's tab underside (2.667 mm). Nominal "
          "solder gap 0.032 mm."),
    ("b", ""),
    ("n", "3. C1's threaded case is GND BY DESIGN - it is the metal a hand or "
          "a tuning tool touches."),
    ("n", "   Tune at reduced drive or with a VNA. NEVER tune at 150 W. "
          "Tool: Johanson 8764."),
    ("b", ""),
    ("n", "4. R1 is a +/-5% catalogue part. The 50 ohm +/-2% requirement is "
          "met by SELECT ON TEST at"),
    ("n", "   incoming inspection: measure each part, accept "
          "49.00-51.00 ohm, reject outside."),
    ("b", ""),
    ("n", "5. R1's substrate is BeO (beryllium oxide). DO NOT machine, drill, "
          "grind or break the part."),
    ("n", "   The dust is the hazard, not the intact part. Scrap it whole."),
]
NOTE_STEP = {"h": 5.08, "n": 4.445, "b": 2.54}
NOTE_SIZE = {"h": 1.6, "n": 1.4}


def build() -> schlib.Sheet:
    """The single root sheet. Returns it unsaved."""
    cache = ksa.get_symbol_cache()
    cache.add_library_path(str(LIB / "aiee.kicad_sym"))
    cache.add_library_path(str(LIB / f"{NAME}.kicad_sym"))

    # Title kept short: anything longer runs past the right edge of the A4
    # title block on the plot (measured).
    sh = schlib.Sheet(NAME, title="50 ohm / 150 W CW RF termination",
                      paper="A4", pwr_base=1)

    # ---- J1: SMA female jack, right-angle THT. pin 1 centre -> RF, pin 2
    # (all four shield legs, one net) -> GND.
    # Value is short ("SMA", not the MPN) on purpose: at rot 0 the Value field
    # lands beside the #PWR GND symbol's own VALUE text and a 7-character
    # string overprints it on the plot. The MPN lives in its own field.
    # footprint is aiee's own clone of the stock Connector_Coaxial part
    # (lib/aiee.pretty/SMA_BAT_Wireless_BWSMA-KWE-Z001.kicad_mod - identical
    # geometry, only the Datasheet property populated) so DRC --parity's
    # footprint_symbol_field_mismatch clears; stock library footprints must
    # not be edited in the KiCad install (LEARNINGS 2026-07-27 (b)).
    sh.add_component("Connector:Conn_Coaxial", "J1", "SMA", (63.5, 76.2),
                     footprint="aiee:SMA_BAT_Wireless_BWSMA-KWE-Z001",
                     fields=J1_FIELDS, expect={"1": "In", "2": "Ext"})
    sh.wire_pins("J1", {"1": RF, "2": GND})
    sh.power_symbol_at_pin("J1", "2", "power:GND")

    # ---- C1: air trimmer, shunt from the RF node to GND at the PORT end.
    # rot 180 puts pin 2 (insulated lead, RF) to the LEFT, facing J1, and
    # pin 1 (threaded case, GND) to the right. It is drawn horizontally on
    # purpose: at rot 90/270 KiCad renders the Reference and Value VERTICALLY
    # (it adds the symbol rotation to the field angle) while schem_refdes
    # separates the two fields along Y as if they were horizontal, so they
    # overprint each other - measured on the first plot of this sheet.
    sh.add_component("aiee:5602", "C1", "1-30pF", (101.6, 76.2), rotation=180,
                     footprint="aiee:CAP-ADJ-TH_2P-BD7.5_5602",
                     fields=C1_FIELDS,
                     expect={"1": "STATOR", "2": "ROTOR"})
    sh.wire_pins("C1", {"1": GND, "2": RF})
    sh.power_symbol_at_pin("C1", "1", "power:GND")

    # ---- R1: 50 ohm 250 W BeO flanged termination, body off-board on the
    # user's heatsink. pin 1 = RF tab lap pad, pin 2 = the two flange-strap
    # GND lands (one symbol pin, two footprint pads on the same number).
    sh.add_component(f"{NAME}:R_Flange", "R1", "50R 250W", (139.7, 76.2),
                     footprint="aiee:R_LapPad_T50R0-250-12X",
                     fields=R1_FIELDS, expect={"1": "RF", "2": "GND"})
    sh.wire_pins("R1", {"1": RF, "2": GND})
    sh.power_symbol_at_pin("R1", "2", "power:GND")

    # ---- H1-H3: M3 mounting holes WITH a pad, tied to GND. Not BOM lines
    # (in_bom False below) - see the module docstring.
    for i, x in enumerate((177.8, 196.85, 215.9), start=1):
        ref = f"H{i}"
        c = sh.add_component("Mechanical:MountingHole_Pad", ref, "M3",
                             (x, 71.12),
                             footprint="MountingHole:"
                                       "MountingHole_3.2mm_M3_Pad",
                             expect={"1": "1"})
        c.in_bom = False        # a mounting hole is not a BOM line
        c.on_board = True       # ... but it IS a placement (6 footprints)
        sh.wire_pin(ref, "1", GND)
        sh.power_symbol_at_pin(ref, "1", "power:GND")

    # ---- the single PWR_FLAG. Nothing on this board drives anything.
    sh.power_flag(GND, at=(63.5, 101.6), sym="power:GND", flag=True)

    # ---- sheet text
    x, y = NOTES_AT
    for kind, line in NOTES:
        if kind != "b":
            sh.sch.add_text(line, position=(x, y), size=NOTE_SIZE[kind],
                            bold=(kind == "h"), grid_units=False)
        y += NOTE_STEP[kind]
    return sh


# --------------------------------------------------------------- field hiding
# ksa gives every extra property VISIBLE effects, so MPN/Datasheet/LCSC strings
# would print on top of the parts they belong to and make the checkpoint PDF
# unreadable. Hiding is a plot property only - the fields must still EXIST
# (P9's bom_cpl reads them). Same helper as rf-de-20m's genlib, inlined here so
# this board's generator has no cross-board import.
VISIBLE = {"Reference", "Value"}


def _match(text: str, open_idx: int) -> int:
    """Index just past the paren opened at `open_idx`, quote-aware."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced s-expression at {open_idx}")


def hide_aux_fields(path: Path) -> int:
    """Add `(hide yes)` to every non-VISIBLE property. Returns the count."""
    text = path.read_text(encoding="utf-8")
    out = []
    pos = 0
    hidden = 0
    needle = '(property "'
    while True:
        i = text.find(needle, pos)
        if i < 0:
            break
        j = text.index('"', i + len(needle))
        name = text[i + len(needle):j]
        end = _match(text, i)
        node = text[i:end]
        if name in VISIBLE or "(hide yes)" in node:
            out.append(text[pos:end])
            pos = end
            continue
        e = node.find("(effects")
        if e >= 0:
            e_end = _match(node, e)
            indent = " " * (len(node[:e]) - len(node[:e].rstrip(" \t")) - 1)
            node = (node[:e_end - 1] + f"\t{indent}(hide yes)\n{indent}"
                    + node[e_end - 1:])
        else:
            node = node[:-1] + "(effects (hide yes))"
        hidden += 1
        out.append(text[pos:i] + node)
        pos = end
    out.append(text[pos:])
    new = "".join(out)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return hidden


def left_justify_texts(path: Path) -> int:
    """Left-justify the sheet's free text. kicad-sch-api's `add_text` has no
    justify parameter and KiCad CENTRES text on its `at` point by default, so
    a 90-character note line centred at x = 25.4 runs off the left edge of the
    page (measured on the first plot). Returns the count changed."""
    text = path.read_text(encoding="utf-8")
    out = []
    pos = 0
    n = 0
    needle = '\n\t(text "'
    while True:
        i = text.find(needle, pos)
        if i < 0:
            break
        start = i + 1
        end = _match(text, start)
        node = text[start:end]
        if "(justify" not in node:
            e = node.index("(effects")
            e_end = _match(node, e)
            node = node[:e_end - 1] + "(justify left)\n\t\t" + node[e_end - 1:]
            n += 1
        out.append(text[pos:start] + node)
        pos = end
    out.append(text[pos:])
    new = "".join(out)
    if new != text:
        path.write_text(new, encoding="utf-8")
    return n


def main() -> int:
    sh = build()
    path = sh.save(OUT)
    hidden = hide_aux_fields(path)
    justified = left_justify_texts(path)
    print(json.dumps({
        "script": "gen/rf-term-150w",
        "status": "pass",
        "sheet": str(path.relative_to(REPO)).replace("\\", "/"),
        "components": sorted(c.reference for c in sh.sch.components),
        "nets": ["/RF", "GND"],
        "hidden_fields": hidden,
        "justified_texts": justified,
        "place_fields": sh.place_report,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
