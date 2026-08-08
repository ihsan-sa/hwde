"""rf-de-20m `tank` sheet (blocks.md B7-B9): the series resonant tank, the
L-match and the RF output connector.

Refdes range 300-399, `#PWR` base 300 (architecture/sheets.md s4).
Zones B (magnetics, NO planes, NO heatsink) and C (output, planes restored).

Rebuild (writes <out>/tank.kicad_sch; the ROOT generator owns the project):
    .venv/Scripts/python boards/rf-de-20m/kicad/gen/tank.py [OUT_DIR]

GROUND TRUTH
------------
architecture/sheets.md s1/s4, architecture/blocks.md B7-B9 + s4.3 (SPIRAL-1..6),
architecture/decisions.md D3/D11 (the AMENDED values), constraints.json,
parts/parts.json, parts/C22418168.json (SMA), plus the library pin tables.

TOPOLOGY (one series chain, one shunt bank)
--------------------------------------------
    /SW --[ L301  L_s 164nH ]-- /tank/TANK_A --[ C301..C309 + C320/C321 ]--
        /tank/TANK_B --[ L302  L_m 110nH ]-- /tank/RFOUT --[ J301 ]
                                                  |
                                 [ C310..C319 + C322/C323  C_m ] -- GND

    (C320-C323 are DNP bench-trim sites - see the bank-sizing block below.)

TANK_A is the highest node on the board at **156 V pk**, 14 V ABOVE the drain -
ordinary series-resonant magnification at Q_L = 5, declared at 180 V in
constraints.json and silkscreened at P6 (sheets.md s6 note 8).

THE SPIRALS ARE REAL SCHEMATIC COMPONENTS WHOSE FOOTPRINT *IS* THE PART
------------------------------------------------------------------------
L301 and L302 are ETCHED PCB AIR-CORE SPIRALS, not purchasable parts
(decisions.md D3: no LCSC part class closes them - molded power inductors sit
at Q 20-40 at 20 MHz, i.e. 25-50 W in one part, and genuine high-Q RF chip
inductors are rated 120-140 mA against 6.96 A rms; paralleling rescues
neither because Q_total = Q_each exactly).

They are stock `Device:L` symbols carrying no LCSC code and marked
`in_bom = False`, but they DO carry a footprint: the copper is the component,
so the winding lives inside the footprint rather than being drawn by hand at
P6.  Authored 2026-08-08 by `kicad/gen/spirals.py`, derived and cross-checked
in `reports/spiral-design.md`:

    L301  aiee:SPIRAL_L164N   3 turns, OD 33.10 mm, 2.5 mm trace, 1.0 mm gap
    L302  aiee:SPIRAL_L110N   2 turns, OD 32.57 mm, 2.5 mm trace, 1.0 mm gap

Both are wound on F.Cu AND B.Cu in parallel (SPIRAL-2) with the inner terminal
escaping on an In1+In2 radial bridge (SPIRAL-4), and both are KiCad NET TIES:
pad 1 and pad 2 are deliberately joined by the winding, which is what an
inductor is at DC.  Each part also carries its own four-layer rule area, so
"no plane under a spiral" travels with the footprint.

This unblocks P5: `board_init` can now place them.  What it does NOT do is
place them well - SPIRAL-5 (>= 38 mm centre-to-centre) and SPIRAL-6 (no metal
within 15 mm in plan view, either face) are still P6's to enforce, and the
courtyard is 39.99 x 33.69 mm (L301) / 39.46 x 33.16 mm (L302), which fits
zone B's 40 mm width with ~0.01 mm to spare in the E-W orientation only.

CAPACITOR BANK SIZING - MIXED-VALUE C_m AND FOUR TRIM SITES (P4 review W1)
---------------------------------------------------------------------------
Both banks are built from 1 kV C0G 1206 parts. C0G, never X7R: X7R's voltage
and temperature coefficients detune a resonant tank, which is the one place
on this board where capacitance is a frequency-setting quantity rather than a
bypass. TWO values are now stocked - CC1206JKNPOCBN560 (56 pF, C113875) and
CC1206JKNPOCBN270 (27 pF, C541492, the same Yageo family/rating/package).

    C_s  target 518 pF +/-5% (492-544)   built 9 x 56           = 504 pF
    C_m  target 530.4 pF (ideal L-match) built 9 x 56 + 1 x 27  = 531 pF

The pre-review build was 10 x 56 = 560 pF for C_m, +5.7 % on the ideal match,
and the sheet argued that the high side was the recoverable one. The review
priced what that actually costs, and it is not free:

    build              Z seen by the tank   VSWR    series X/R   Pout at 40 V
    560 pF (was)       3.737 + j0.675       1.220      1.47        ~221 W
    531 pF (now)       4.122 + j0.072       1.018      1.19        ~200 W
    ideal 530.4 pF     4.136 + j0.050       1.012      1.18         200 W

Both errors pushed the same way: R_in 9.5 % low raised P_out to ~221 W and
with it I_dc, conduction loss and the 11.25 W / Tj 114 C two-FET thermal
budget the whole paralleling decision rests on; and total series reactance
moved to X/R 1.47 against the Class E optimum 1.1525, so ZVS was off and
switching loss appeared on top. ONE 27 pF part in place of one 56 pF fixes
both: X/R 1.19 (the residual comes from C_s at 504 pF, and 504 pF is within
1 % of the 499 pF that would put X/R exactly on 1.1525 - it is not worth a
second value to chase). Numbers computed at 20 MHz with L_s 164 nH,
C_s 504 pF, L_m 110 nH into 50 ohm.

TRIM SITES: C320/C321 (C_s) and C322/C323 (C_m), 27 pF, DNP
------------------------------------------------------------
Neither bank had a trim site - only C_shunt got DNP pads (C205/C206) - so the
tank could only be trimmed DOWN, in 56 pF (11 %) steps, by depopulation. Four
27 pF DNP sites give each bank a bidirectional bench trim:

    C_s   504 pF as built;  +27 / +54 pF by populating C320/C321
                            -56 pF per depopulated 56 pF site
                            FINE DOWN-TRIM: drop one 56 and populate both
                            27s -> 8 x 56 + 2 x 27 = 502 pF (-0.4 %)
    C_m   531 pF as built;  +27 / +54 pF by populating C322/C323
                            -27 pF by depopulating C319 (the 27 pF part)
                            -56 pF per depopulated 56 pF site

This matters because L301/L302 are ETCHED SPIRALS whose realised inductance
is the largest unknown in the tank - a +/-10 % spiral is ordinary, and the
capacitor banks are the only knob that answers it. C_s additionally carries
OPEN-12 (the P1 fragment's C_series coefficient is refuted; SIM-4 arbitrates),
which is why both banks stay PARALLEL ARRAYS rather than single parts.

Per-part duty, so nobody "simplifies" the split: C_s 0.77 A rms and ~105 mW
each; in C_m the current divides in proportion to capacitance, so each 56 pF
part carries 56/531 x 6.66 = 0.70 A rms and the 27 pF part 0.34 A - because
C_m carries 6.66 A rms, nearly the full tank current, NOT the 2.0 A load
current. The 1 kV rating is 6.6x the 151 V pk across the C_s bank.

NET NAMING (sheets.md s1 - BINDING)
------------------------------------
* `GND` is a POWER SYMBOL -> global and BARE, flag=False (`hk` owns the flags).
* `SW` is the ONLY hierarchical pin. It crosses the root (also exposed by
  `stage`), so the net comes out **`/SW`**.
* Three nets are sheet-internal and come out `/tank/<NAME>`: TANK_A, TANK_B,
  RFOUT - exactly the spellings constraints.json uses.
* `+40V` and `+5V` do not appear on this sheet at all.

NOT ON THIS SHEET
-----------------
No output TVS, no directional coupler, no VSWR sense, no DC block, no
harmonic filter. The harmonic windows (SIM-4: h2 <= -20 dBc, h3 <= -33 dBc)
are far short of any transmit compliance mask, which is why this board is
DUMMY-LOAD ONLY (blocks.md s5). A load that moves off the design point drives
peak drain stress toward 7x Vdd on a 200 V part.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
REPO = BOARD.parents[1]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402

import genlib  # noqa: E402

ksa = schlib.ksa
ksa.get_symbol_cache().add_library_path(str(BOARD / "lib" / "aiee.kicad_sym"))

# --------------------------------------------------------------------- nets
GND = "GND"
SW = "SW"              # hier, in from `stage` via the root -> /SW
TANK_A = "TANK_A"      # -> /tank/TANK_A   156 V pk - highest node on the board
TANK_B = "TANK_B"      # -> /tank/TANK_B
RFOUT = "RFOUT"        # -> /tank/RFOUT

# ------------------------------------------------------------------ symbols
S_L = "Device:L"                          # PCB spiral - stock symbol, no fp
S_C56P = "aiee:CC1206JKNPOCBN560"         # 56pF 1kV C0G 1206
S_C27P = "aiee:CC1206JKNPOCBN270"         # 27pF 1kV C0G 1206 (W1)
S_SMA = "aiee:CONSMA001-SMD-G-T"          # default Reference "RF" -> J301

# --------------------------------------------------------------- footprints
F_C1206 = "aiee:C1206"
F_SMA = "aiee:SMA-SMD_CONSMA001-SMD-G-T"
# The spirals - the copper IS the part. kicad/gen/spirals.py authors both.
F_SPIRAL_LS = "aiee:SPIRAL_L164N"
F_SPIRAL_LM = "aiee:SPIRAL_L110N"

# ------------------------------------------------------------------- values
V_C56P = "56pF 1kV C0G 1206"
V_C27P = "27pF 1kV C0G 1206"
V_SMA = "SMA jack 50R SMD (CONSMA001)"

# Bank membership. (ref, pF, dnp) - the ONLY place the banks are defined.
CS_BANK = [(f"C{n}", 56, False) for n in range(301, 310)]        # 504 pF
CM_BANK = ([(f"C{n}", 56, False) for n in range(310, 319)]
           + [("C319", 27, False)])                              # 531 pF
CS_TRIM = [("C320", 27, True), ("C321", 27, True)]
CM_TRIM = [("C322", 27, True), ("C323", 27, True)]

CS_REFS = CS_BANK + CS_TRIM
CM_REFS = CM_BANK + CM_TRIM

# The spiral symbols are stock Device:L, whose Description ("Inductor") does not
# match the rich `descr` the custom footprints carry. board_init's schematic
# parity check compares the two and reports footprint_symbol_field_mismatch,
# which is a P5 phase-gate failure. Carry the footprint text as an explicit
# Description field so symbol and footprint agree.
# MUST stay byte-identical to `(descr ...)` in lib/aiee.pretty/SPIRAL_*.kicad_mod
# - kicad/gen/spirals.py authors both, so change them together.
DESCR = {
    "L301": (
        "Etched PCB air-core planar spiral 164nH at 20MHz (rf-de-20m L_s, "
        "L301). 3 turns, OD 33.10mm, 2.5mm trace, 1.0mm gap, F.Cu||B.Cu "
        "parallel winding, In1+In2 inner-terminal bridge. NET TIE: pads 1-2 "
        "are joined by the winding. No plane or heatsink beneath - shorted turn."
    ),
    "L302": (
        "Etched PCB air-core planar spiral 110nH at 20MHz (rf-de-20m L_m, "
        "L302). 2 turns, OD 32.57mm, 2.5mm trace, 1.0mm gap, F.Cu||B.Cu "
        "parallel winding, In1+In2 inner-terminal bridge. NET TIE: pads 1-2 "
        "are joined by the winding. No plane or heatsink beneath - shorted turn."
    ),
}

LCSC = {"J301": "C22418168"}
for _r, _pf, _d in CS_REFS + CM_REFS:
    LCSC[_r] = "C113875" if _pf == 56 else "C541492"


def _pf_total(bank) -> int:
    return sum(pf for _, pf, dnp in bank if not dnp)


def _add(sh, ref, lib_id, value, at, footprint=None, expect=None, note=None,
         in_bom=True, rotation=0, dnp=False):
    fields = {}
    code = LCSC.get(ref)
    if code:
        fields["LCSC"] = code
    if dnp:
        # kicad-sch-api's writer hard-codes `(dnp no)`, so `Variant` is the
        # only do-not-populate marking reachable from a generator and it is
        # kept VISIBLE by genlib (LEARNINGS 2026-08-07). P9 filters by hand.
        fields["Variant"] = "DNP"
    if note:
        fields["Note"] = note
    descr = DESCR.get(ref)
    if descr:
        fields["Description"] = descr
    c = sh.add_component(lib_id, ref, value, at, rotation=rotation,
                         footprint=footprint, fields=fields or None,
                         expect=expect)
    if not in_bom:
        c.in_bom = False
    return c


def _note(sh, at, lines, dy=5.08):
    x, y = at
    for i, line in enumerate(lines):
        sh.sch.add_text(line, position=(x, round(y + i * dy, 4)))


def build() -> schlib.Sheet:
    sh = schlib.Sheet("tank",
                      title="rf-de-20m: tank - L_s/C_s series tank, L-match, "
                            "RF output",
                      paper="A2", date="2026-08-07", company="ai-ee",
                      pwr_base=300)

    # GND is consumed here; `hk` owns every PWR_FLAG.
    sh.power_flag(GND, at=(25.4, 25.4), sym="power:GND", flag=False)

    # /SW arrives from `stage`. Free-cluster hier pin: local label at one end,
    # hierarchical label at the other, joined by wire geometry.
    sh.hier_pin(SW, shape="input", at=(25.4, 50.8))

    # =====================================================================
    # B7 - series resonant tank
    # =====================================================================
    # L301 = L_s = 164 nH. ETCHED PCB SPIRAL: Device:L, custom footprint that
    # IS the copper, not in the BOM. As drawn: 3 turns, OD 33.10 mm, 2.5 mm
    # trace / 1.0 mm gap, F.Cu||B.Cu -> 164.0 nH, Q 388, 2.6 W over 860 mm2
    # (2.99 mW/mm2 against the 7 mW/mm2 SPIRAL-1 ceiling).
    _add(sh, "L301", S_L, "164nH", (114.3, 114.3), footprint=F_SPIRAL_LS,
         expect={"1": "1", "2": "2"}, in_bom=False,
         note="L_s - ETCHED PCB AIR-CORE SPIRAL (net tie, pads 1-2 joined by "
              "the winding). 3T OD 33.1mm F.Cu||B.Cu. NO plane or heatsink "
              "beneath - shorted turn. See reports/spiral-design.md")
    sh.wire_pins("L301", {"1": SW, "2": TANK_A})

    # C_s bank: 9 x 56 pF = 504 pF against a 518 pF +/-5% target, plus two
    # 27 pF DNP TRIM SITES (W1). C_s is a SERIES element and floats, which is
    # why it can live in zone B where there is no ground plane. Trim sites are
    # part of the bank and must be placed IN it, not on a stub.
    for i, (ref, pf, dnp) in enumerate(CS_REFS):
        _add(sh, ref, S_C56P if pf == 56 else S_C27P,
             V_C56P if pf == 56 else V_C27P,
             (88.9 + (i % 6) * 76.2, 190.5 + (i // 6) * 38.1),
             footprint=F_C1206, expect={"1": "1", "2": "2"}, dnp=dnp,
             note=("C_s TRIM SITE - DNP. Populate for +27pF; for a fine "
                   "DOWN-trim drop one 56pF and populate both (502pF)"
                   if dnp else
                   "C_s bank 9x56pF=504pF (target 518pF +/-5%, X/R-optimal "
                   "499pF). C0G, never X7R"))
        sh.wire_pins(ref, {"1": TANK_A, "2": TANK_B})

    # =====================================================================
    # B8 - L-match to 50 ohm
    # =====================================================================
    # L302 = L_m = 110 nH. SPIRAL-3: nearly as large as L301 despite being 67%
    # of the inductance, because the binding constraint is DISSIPATION AREA,
    # not L. Do not let a reviewer shrink it. As drawn: 2 turns, OD 32.57 mm,
    # same 2.5/1.0 trace -> 110.0 nH, Q 325, 2.1 W over 833 mm2.
    _add(sh, "L302", S_L, "110nH", (330.2, 114.3), footprint=F_SPIRAL_LM,
         expect={"1": "1", "2": "2"}, in_bom=False,
         note="L_m - ETCHED PCB AIR-CORE SPIRAL (net tie, pads 1-2 joined by "
              "the winding). 2T OD 32.57mm F.Cu||B.Cu. Centre-to-centre "
              ">=38mm from L301 (SPIRAL-5). See reports/spiral-design.md")
    sh.wire_pins("L302", {"1": TANK_B, "2": RFOUT})

    # C_m bank: 9 x 56 + 1 x 27 = 531 pF against the 530.4 pF ideal L-match
    # (W1 - the 10 x 56 = 560 pF build gave 3.74 ohm, VSWR 1.22 and ~221 W),
    # plus two 27 pF DNP TRIM SITES. C_m RETURNS TO GROUND and carries
    # 6.66 A rms, so it lives in zone C where the plane stack exists.
    for i, (ref, pf, dnp) in enumerate(CM_REFS):
        _add(sh, ref, S_C56P if pf == 56 else S_C27P,
             V_C56P if pf == 56 else V_C27P,
             (88.9 + (i % 6) * 76.2, 279.4 + (i // 6) * 38.1),
             footprint=F_C1206, expect={"1": "1", "2": "2"}, dnp=dnp,
             note=("C_m TRIM SITE - DNP. Populate for +27pF; depopulate C319 "
                   "for -27pF"
                   if dnp else
                   "C_m bank 9x56+1x27 = 531pF (ideal 530.4pF). Carries "
                   "6.66A rms, not the 2A load current"))
        sh.wire_pins(ref, {"1": RFOUT, "2": GND})

    # =====================================================================
    # B9 - RF output
    # =====================================================================
    # Same part as J201. Pins 1-4 are the four square ground lands, pin 5 the
    # centre RF contact (parts/C22418168.json). 100 Vrms / 2.0 A rms at
    # 20 MHz is electrically trivial for an SMA; mount style and stock drove
    # the choice. /tank/RFOUT must stay <= 15 mm from the C_m node (D7).
    _add(sh, "J301", S_SMA, V_SMA, (495.3, 114.3), footprint=F_SMA,
         expect={str(n): str(n) for n in range(1, 6)},
         note="RF out, 200 W. SILK: burn + RF-exposure hazard (sheets.md s6.8)")
    sh.wire_pins("J301", {"1": GND, "2": GND, "3": GND, "4": GND, "5": RFOUT})

    # =====================================================================
    # sheet notes
    # =====================================================================
    _note(sh, (88.9, 355.6), [
        "L301 AND L302 ARE ETCHED PCB AIR-CORE SPIRALS - THE COPPER IS",
        "THE PART. No LCSC code, excluded from the BOM. The winding",
        "lives inside the footprint (kicad/gen/spirals.py); see",
        "reports/spiral-design.md for both inductance derivations.",
        "  L301 aiee:SPIRAL_L164N  3T OD 33.10mm, 2.5/1.0 trace/gap",
        "  L302 aiee:SPIRAL_L110N  2T OD 32.57mm, 2.5/1.0 trace/gap",
        "Both are KiCad NET TIES: pads 1-2 are joined by the winding,",
        "  which is what an inductor is at DC. Do not 'fix' the short.",
        "SPIRAL-2 is TAKEN: F.Cu and B.Cu carry identical windings in",
        "  parallel, stitched 14 vias per terminal, inner terminal out",
        "  on a 5 mm In1+In2 radial bridge (SPIRAL-4). Q 388 / 325,",
        "  2.6 W / 2.1 W - not the 10 W the power tree budgeted.",
        "SPIRAL-5: centre-to-centre >= 38 mm. At 38 mm the computed",
        "  mutual is -2.0 nH (k 1.5%), i.e. -4.1 nH / -1.5% on the",
        "  series total. P8 folds it in; the trim sites cover it.",
        "SPIRAL-6: no metal within 15 mm in plan view on either face.",
        "  A conductive plate under a spiral is a SHORTED TURN and no",
        "  copper cutout prevents it - that includes the heatsink,",
        "  brackets, standoffs and fasteners.",
        "Each footprint carries its own 4-layer rule area (no pour on",
        "  F/B, no tracks or vias on In1/In2) out to 20.5 mm radius.",
        "  Zone B's blanket In1/In2 void is still required beyond that.",
    ])
    _note(sh, (88.9, 431.8), [
        "C_m IS 531 pF: 9 x 56 pF + 1 x 27 pF (C319), against the ideal",
        "L-match value of 530.4 pF. The 10 x 56 = 560 pF single-value bank",
        "was +5.7%: 3.74 + j0.68 ohm, VSWR 1.22, series X/R 1.47 against",
        "the Class E optimum 1.1525, and ~221 W not 200 W at a 40 V bus.",
        "As built: 4.12 + j0.07 ohm, VSWR 1.02, X/R 1.19, ~200 W.",
        "C_s stays 9 x 56 = 504 pF (target 518 +/-5%; 499 pF would put X/R",
        "exactly on 1.1525, so 504 is within 1% and needs no third value).",
        "TRIM SITES C320/C321 (C_s) and C322/C323 (C_m) are 27 pF DNP.",
        "Populate for +27/+54 pF; depopulate for -27 (C319) or -56 pF.",
        "Fine C_s down-trim: drop one 56 and populate both 27s -> 502 pF.",
        "The spirals' realised L is the tank's largest unknown - these",
        "sites are how bring-up answers it. SIM-4 still arbitrates C_s.",
    ])
    _note(sh, (88.9, 482.6), [
        "NO X7R ANYWHERE IN THE TANK. C0G/NP0 only - X7R's voltage and",
        "temperature coefficients detune a resonant network. (X7R IS",
        "correct on the DC bus, and is used there.)",
        "/tank/TANK_A REACHES 156 V pk - the highest node on the board,",
        "14 V ABOVE the drain. Silkscreen it at P6.",
    ])
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
        hidden = genlib.hide_aux_fields(path)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.tank", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.tank", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "internal_nets": sorted({TANK_A, TANK_B, RFOUT}),
        "c_s_pf": _pf_total(CS_REFS),
        "c_m_pf": _pf_total(CM_REFS),
        "dnp": sorted(r for r, _, d in CS_REFS + CM_REFS if d),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
