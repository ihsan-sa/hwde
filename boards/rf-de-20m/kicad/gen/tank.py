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
    /SW --[ L301  L_s 164nH ]-- /tank/TANK_A --[ C301..C309  C_s ]--
        /tank/TANK_B --[ L302  L_m 110nH ]-- /tank/RFOUT --[ J301 ]
                                                  |
                                          [ C310..C319  C_m ] -- GND

TANK_A is the highest node on the board at **156 V pk**, 14 V ABOVE the drain -
ordinary series-resonant magnification at Q_L = 5, declared at 180 V in
constraints.json and silkscreened at P6 (sheets.md s6 note 8).

THE SPIRALS ARE REAL SCHEMATIC COMPONENTS WITH NO FOOTPRINT
------------------------------------------------------------
L301 and L302 are ETCHED PCB AIR-CORE SPIRALS, not purchasable parts
(decisions.md D3: no LCSC part class closes them - molded power inductors sit
at Q 20-40 at 20 MHz, i.e. 25-50 W in one part, and genuine high-Q RF chip
inductors are rated 120-140 mA against 6.96 A rms; paralleling rescues
neither because Q_total = Q_each exactly).

They are placed here as stock `Device:L` symbols with **the Footprint field
deliberately left BLANK** - P6 authors the copper and the custom footprint.
They must exist as components so their NETS are real: "copper that no tool
knows about gets routed over, poured under and placed on top of" is the whole
reason D3 calls them first-class layout objects. They carry no LCSC code and
are marked `in_bom = False`.

CONSEQUENCE FOR P5, FLAGGED NOT WORKED AROUND: a component with no footprint
cannot be placed by `board_init`. P6 must supply the footprint (or a
placeholder land) before the board is built, or L301/L302 will be absent from
the .kicad_pcb while their nets still exist in the netlist.

CAPACITOR BANK SIZING - AND THE ONE VALUE THAT CANNOT BE HIT EXACTLY
---------------------------------------------------------------------
Both banks use the SAME sourced part, CC1206JKNPOCBN560 (56 pF / 1 kV C0G
1206, C113875) - parts.json's stated "one part, three roles" intent. C0G,
never X7R: X7R's voltage and temperature coefficients detune a resonant tank,
which is the one place on this board where capacitance is a frequency-setting
quantity rather than a bypass.

    C_s  target 518 pF +/-5% (492-544)   built  9 x 56 pF = 504 pF  (-2.7%)  OK
    C_m  target 530 pF +/-3% (514-546)   built 10 x 56 pF = 560 pF  (+5.7%)  OUT

**A single-value 56 pF bank cannot land inside C_m's +/-3% window**: 9 parts
give 504 pF (-4.9%) and 10 give 560 pF (+5.7%), and 530 pF sits between the
steps. 10 sites is taken, deliberately, because the two directions are NOT
symmetric in consequence:

  * C_m HIGH  -> Q_m 3.519, R_in 3.74 ohm -> ~221 W at a 40 V bus. Recoverable
    for free by backing the bus down to ~38 V, which is exactly the knob
    decisions.md D1/OPEN-4 already documents ("bring-up sets the bus to hit
    exactly 200 W", 38-40 V).
  * C_m LOW   -> R_in 4.53 ohm -> ~182 W at 40 V, and the bus is already at
    its ceiling on a 200 V part, so there is no knob left.

Depopulating one site returns the 504 pF option at bring-up. If SIM-4 wants
530 pF literally, the fix is one added BOM line (a 51 pF or 27 pF 1 kV C0G
1206): 4 x 56 + 6 x 51 = 530 pF exactly, or 9 x 56 + 1 x 27 = 531 pF. That is
a P3 re-source, not something to invent here.

C_s carries the largest single uncertainty in the tank (OPEN-12: the P1
fragment's C_series coefficient is refuted and SIM-4 is the arbiter), which is
why both banks stay PARALLEL ARRAYS - they trim by depopulation.

Per-part duty, so nobody "simplifies" the split: C_s 0.77 A rms and ~105 mW
each; C_m 0.67 A rms each, because C_m carries 6.66 A rms - nearly the full
tank current, NOT the 2.0 A load current. The 1 kV rating is 6.6x the 151 V pk
across the C_s bank.

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
S_SMA = "aiee:CONSMA001-SMD-G-T"          # default Reference "RF" -> J301

# --------------------------------------------------------------- footprints
F_C1206 = "aiee:C1206"
F_SMA = "aiee:SMA-SMD_CONSMA001-SMD-G-T"
# L301/L302: NO footprint - see the module docstring.

# ------------------------------------------------------------------- values
V_C56P = "56pF 1kV C0G 1206"
V_SMA = "SMA jack 50R SMD (CONSMA001)"

LCSC = {"J301": "C22418168"}
for _i in range(301, 320):
    LCSC[f"C{_i}"] = "C113875"

CS_REFS = [f"C{n}" for n in range(301, 310)]    # C_s : 9 x 56 pF = 504 pF
CM_REFS = [f"C{n}" for n in range(310, 320)]    # C_m : 10 x 56 pF = 560 pF


def _add(sh, ref, lib_id, value, at, footprint=None, expect=None, note=None,
         in_bom=True, rotation=0):
    fields = {}
    code = LCSC.get(ref)
    if code:
        fields["LCSC"] = code
    if note:
        fields["Note"] = note
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
    # L301 = L_s = 164 nH. ETCHED PCB SPIRAL: Device:L, NO footprint, not in
    # the BOM. SPIRAL-1: >= 1430 mm2 of copper at Q 100 (10.0 W, the hottest
    # single item on the board and 70 C of rise BY DESIGN, not a defect).
    _add(sh, "L301", S_L, "164nH", (114.3, 114.3), footprint=None,
         expect={"1": "1", "2": "2"}, in_bom=False,
         note="L_s - PCB AIR-CORE SPIRAL, do not place. P6 authors the copper "
              "and the footprint. >=1430mm2 at Q100, no plane beneath")
    sh.wire_pins("L301", {"1": SW, "2": TANK_A})

    # C_s bank: 9 x 56 pF = 504 pF against a 518 pF +/-5% target. C_s is a
    # SERIES element and floats, which is why it can live in zone B where
    # there is no ground plane.
    for i, ref in enumerate(CS_REFS):
        _add(sh, ref, S_C56P, V_C56P, (88.9 + (i % 5) * 76.2,
                                       190.5 + (i // 5) * 38.1),
             footprint=F_C1206, expect={"1": "1", "2": "2"},
             note="C_s bank 9x56pF=504pF (target 518pF +/-5%). C0G, never X7R")
        sh.wire_pins(ref, {"1": TANK_A, "2": TANK_B})

    # =====================================================================
    # B8 - L-match to 50 ohm
    # =====================================================================
    # L302 = L_m = 110 nH. SPIRAL-3: >= 950 mm2 at Q 100 - nearly as large as
    # L301 despite being 67% of the inductance, because the binding constraint
    # is DISSIPATION AREA, not L. Do not let a reviewer shrink it.
    _add(sh, "L302", S_L, "110nH", (330.2, 114.3), footprint=None,
         expect={"1": "1", "2": "2"}, in_bom=False,
         note="L_m - PCB AIR-CORE SPIRAL, do not place. >=950mm2 at Q100. "
              "Centre-to-centre >=38mm from L301 (SPIRAL-5)")
    sh.wire_pins("L302", {"1": TANK_B, "2": RFOUT})

    # C_m bank: 10 x 56 pF = 560 pF against a 530 pF +/-3% target - see the
    # module docstring for why the high side of the step is the safe one.
    # C_m RETURNS TO GROUND and carries 6.66 A rms, so it lives in zone C
    # where the plane stack exists, unlike C_s.
    for i, ref in enumerate(CM_REFS):
        _add(sh, ref, S_C56P, V_C56P, (88.9 + (i % 5) * 76.2,
                                       279.4 + (i // 5) * 38.1),
             footprint=F_C1206, expect={"1": "1", "2": "2"},
             note="C_m bank 10x56pF=560pF (target 530pF). Carries 6.66A rms, "
                  "not the 2A load current")
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
        "L301 AND L302 ARE ETCHED PCB AIR-CORE SPIRALS.",
        "They are real components with real nets and NO FOOTPRINT -",
        "P6 authors the copper. No LCSC code, excluded from the BOM.",
        "SPIRAL-1: L +/-3%, Q >= 120 at 20 MHz, copper area >= P/7 mW.mm-2",
        "  (L301 >= 1430 mm2 at Q 100, L302 >= 950 mm2 at Q 100).",
        "SPIRAL-5: centre-to-centre >= 38 mm, and P8 must compute the",
        "  residual mutual coupling k and fold it into the tank solve -",
        "  the two spirals are NOT independent components.",
        "SPIRAL-6: no metal within 15 mm in plan view on either face.",
        "  A conductive plate under a spiral is a SHORTED TURN and no",
        "  copper cutout prevents it - that includes the heatsink,",
        "  brackets, standoffs and fasteners.",
        "Zone B carries no plane on In1/In2/B.Cu by construction, and a",
        "  four-layer KiCad rule area must be hand-added over each",
        "  courtyard at P6 after the spirals are placed and LOCKED.",
    ])
    _note(sh, (88.9, 431.8), [
        "C_m IS 560 pF, NOT 530 pF. A single-value 56 pF bank cannot",
        "land inside the +/-3% window (9 parts = 504, 10 parts = 560).",
        "The HIGH side is chosen because it is the recoverable one:",
        "high C_m raises P_out to ~221 W at 40 V, and the bus is already",
        "a documented derating knob (38-40 V, OPEN-4). Low C_m would give",
        "~182 W with no knob left - the bus is at its ceiling on a 200 V",
        "part. Depopulate one site for 504 pF; a literal 530 pF needs one",
        "added BOM line (4x56 + 6x51 = 530 exactly). SIM-4 arbitrates.",
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
        "c_s_pf": 56 * len(CS_REFS),
        "c_m_pf": 56 * len(CM_REFS),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
