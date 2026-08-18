"""bb-adc root generator - THE WHOLE SCHEMATIC (one flat root sheet).

0-5 V precision analog front end -> 16-bit SPI SAR, 0.1 % uncalibrated.
J1 -> 5 x 200 k equal string tapped 3:2 (K = 0.400) -> OPA320 unity follower
-> R6/C7 -> ADS8326IB, ADR4520B 2.048 V reference, SPI out at J2.

    Rebuild:  .venv\\Scripts\\python.exe boards/bb-adc/kicad/gen/root.py
    Outputs:  ../bb-adc.kicad_sch  ../bb-adc.kicad_pro  ../decoupling.json

The Python is the SOURCE; the .kicad_sch is build output.  Every pin number
below comes from the datasheet extracts `parts/C544731.json` (ADS8326),
`parts/C579305.json` (ADR4520) and `parts/C92494.json` (OPA320) or from the
project symbol library's own pin table, never from memory.  `expect=` on all
three ICs is pin-name insurance.

=====================================================================
0.  THE ONE REQUIREMENT NO GATE CATCHES: U1 -IN IS A SENSE RUN
=====================================================================
`U1` pin 3 (-IN) is wired by an EXPLICIT WIRE to `R5`'s bottom pad - the
attenuator string's bottom node - and reaches `GND` only at that one point.
It is NOT a `GND` power symbol dropped next to the converter, and it carries
no `GND` label of its own.  See `sense_run()` below, which draws the wire and
proves it touches nothing but its two endpoints.

Why, in one line of arithmetic: a divider passes a ground offset at UNITY
while dividing the signal by K = 0.400, so an offset between the string
bottom and the converter's negative reference is referred to the input
multiplied by 1/K = 2.5.  **1 mV of copper offset = 2.5 mV at the terminal**,
half the entire 25 degC error budget.  Sensing at the string bottom cancels
it exactly: +IN carries V_tap + (GND_A - GND_C), -IN carries (GND_A - GND_C),
and the difference is V_tap.  (blocks.md s8.1, decisions 23/24/32/33/53.)

Nothing downstream can find this if it is lost.  ERC sees one net either way;
DRC sees copper either way; `netlist_audit` sees `U1.3` on `GND` either way -
which is CORRECT, because electrically there IS one net.  What the schematic
can carry is the WIRE and the intent, and what carries it into copper is
`constraints.json placement.corridors` (`R5` -> `U1`, 3 mm, net `GND`) at P7.

BOUNDED, not open-ended: the ADS8326 specifies -IN at **-0.3 V to +0.5 V**
relative to device ground (Recommended Operating Conditions, p.3; an absolute
constant, no VDD/VREF dependence - decision 55).  The sense point must be a
node whose offset stays in the millivolts, which R5's pad is and a distant or
shared-return ground is not.

=====================================================================
1.  NET CONTRACT (architecture/sheets.md s2 - BINDING, do not "tidy")
=====================================================================
BARE global nets, made bare by a POWER SYMBOL whose Value names the net (a
power symbol's exported net name is its VALUE and the symbol WINS over a
coincident local label - LEARNINGS 2026-07-28):

    +3V3   VDD_ADC   VREF   GND

`VDD_ADC` exists because R7 splits the converter's supply off `+3V3` and
KiCad cannot put one net on both pins of a resistor.  `VREF` and `VDD_ADC`
have no stock power symbol; `power:VBUS` carries each with its Value set to
the net name, which is what `schlib.power_flag` does.

Root-sheet LOCAL labels, which KiCad exports with ONE leading slash:

    /AIN_RAW  /ATT_A  /ATT_B  /AIN_DIV  /ATT_C  /AIN_BUF  /AIN_ADC
    /CS  /SCLK  /DOUT

*** The label TEXT written below is BARE ("AIN_RAW", "CS", ...).  The leading
`/` is the ROOT SHEET PATH that KiCad prepends on export.  Typing the slash
into the label yields the escaped net `/{slash}AIN_RAW` - silently, with a
clean build and a clean ERC - and every constraints.json match then fails.
Measured on sbuck-5v3a before the fix (LEARNINGS 2026-08-09).  Verify with
the exported net names, never by reading the schematic. ***

=====================================================================
2.  PIN-HANDLING JUDGMENTS, each resolved from an extraction
=====================================================================
U1 pin 3 (-IN)     -> the sense run above.  No label, no ground symbol.
U1 pin 5 (CS/SHDN) -> `/CS`, driven by the host at all times the board is
    powered.  NO pull-up: "conditioning the datasheet does not require" is
    excluded by the scope tier and the one hot-plug hazard a pull-up would
    not fix is recorded and accepted (answered Q5, sheets.md s3).
U2 pins 1/3/5/7 (NIC) and pin 8 (DNC/TP) -> EXPLICIT NO-CONNECT.
    Table 11, p.10: pins 1/3/5/7 are "not connected internally"; pin 8 is the
    factory ATE test node, "Do not connect."  The library types all five
    `no_connect` (a P3 hand-edit that must survive any re-pull - decision 69a)
    and KiCad 10.0.3 ERC is 0/0 either with or without the markers (probed on
    a 1-part scratch sheet this session).  The markers are placed anyway so
    "do not connect" is IN THE FILE rather than inferred from absence.
U3 pin 4 (-IN)     -> `/AIN_BUF`, the same net as pin 1 (OUT).  THE FOLLOWER'S
    FEEDBACK IS A WIRE: no resistor.  A gain-setting network there would add
    two tolerances and two leakage nodes to the budget for no benefit - the
    attenuation is already done, precisely, upstream (sheets.md s3).
U3 pin 2 (V-)      -> `GND`.  Single supply.  Known, bounded risk (decision
    63): TI's own "Driving ADS8326" figure for this exact amplifier/converter
    pair warns that single-supply operation loses a few codes near ground and
    shows a -0.3 V generator as the fix.  That would be a second rail, so it
    is a pre-authorised P8 contingency and an owner decision (64), not a
    schematic addition here.

=====================================================================
3.  WHAT IS DELIBERATELY ABSENT (scope tier block-only)
=====================================================================
No protection, no filtering beyond the datasheet-required networks, no
indicators, no test points, no reference buffer, no series R at the
reference, no pull-up on /CS, no series damping on /SCLK, no ferrite.
The GUARD RING is P7 COPPER, not a schematic element, and it belongs on
`/AIN_BUF` (the buffer OUTPUT), never on `/AIN_DIV` - a ring on the same net
as the node it surrounds is not a guard, it IS the node (decision 72).

=====================================================================
4.  DECOUPLING METADATA
=====================================================================
Six associations.  All four rails are power symbols, so the wiring labels and
the final netlist names are identical and no `rail_net`/`gnd_net` override is
needed.  `role: "reg_input"` is NOT set on any of them: that role marks a
SWITCHING regulator's input pin, and this board has none (U2 is a linear
series reference).  Two distance overrides carry the numbers
`constraints.json` actually states - C3 within 2.5 mm of the VREF pin, C2
within 2 mm of the VDD pin; every other cap keeps its class default rather
than an invented number.

C1 gets NO association on purpose: it is the bulk reservoir at the RAIL ENTRY
(constraints group `entry`, anchor J2), not at an IC pin, and associating it
with U2 or U3 would impose a distance limit that contradicts that group.
`+3V3` is still covered by C4 and C6.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]                 # boards/<b>/kicad/gen/root.py -> repo
WORKSPACE = HERE.parents[2]            # boards/bb-adc
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import kicad_sch_api as ksa            # noqa: E402
import schlib                          # noqa: E402

# kicad-sch-api's GLOBAL symbol cache never reads kicad/sym-lib-table, so the
# project library must be registered before any `aiee:` symbol is placed, and
# before save() re-serialises lib_symbols from that same cache
# (LEARNINGS 2026-07-28 and 2026-08-06).
PROJECT_LIB = WORKSPACE / "lib" / "aiee.kicad_sym"
ksa.get_symbol_cache().add_library_path(str(PROJECT_LIB))

# ------------------------------------------------------------------ symbols
S_U1 = "aiee:ADS8326IBDGKR"             # U1  16-bit SAR, MSOP-8
S_U2 = "aiee:ADR4520BRZ-R7"             # U2  2.048 V reference, SOIC-8
S_U3 = "aiee:OPA320AIDBVR"              # U3  RRIO CMOS follower, SOT-23-5
S_R200K = "aiee:PTFR0805Q200KN9"        # R1-R5  200k 0.02% 10ppm 0805
S_R49R9 = "aiee:0603WAF499JT5E"         # R6  49.9 ohm 1% 0603
S_R10R = "aiee:0603WAF100JT5E"          # R7  10 ohm 1% 0603
S_C10U = "aiee:CL21A106KAYNNNE"         # C1, C8  10uF 25V X5R 0805
S_C100N = "aiee:CL05B104KO5NNNC"        # C2, C4, C6  100nF 16V X7R 0402
S_C47U = "aiee:CS3225X7R476K160NRL"     # C3  47uF 16V X7R 1210
S_C2U2 = "aiee:CC0603KRX7R6BB225"       # C5  2.2uF 10V X7R 0603
S_C1N = "aiee:CC0603JRNPO9BN102"        # C7  1nF 50V C0G/NP0 0603
S_J1 = "aiee:WJ500V-5.08-2P-14-00A"     # J1  2-pole 5.08 mm screw terminal
S_J2 = "aiee:Header-Male-2.54_1x6"      # J2  1x6 2.54 mm male header
S_HOLE = "Mechanical:MountingHole"      # H1-H4  ZERO pins, unplated M3

# --------------------------------------------------------------- footprints
F_U1 = "aiee:VSSOP-8_L3.0-W3.0-P0.65-LS5.0-BL"
F_U2 = "aiee:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL"
F_U3 = "aiee:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR"
F_R0805 = "aiee:R0805"
F_R0603 = "aiee:R0603"
F_C0402 = "aiee:C0402"
F_C0603 = "aiee:C0603"
F_C0805 = "aiee:C0805"
F_C1210 = "aiee:C1210"
F_J1 = "aiee:CONN-TH_2P-P5.00_WJ500V-5.08-2P"   # pads at +/-2.54 = 5.08 pitch
F_J2 = "aiee:HDR-TH_6P-P2.54-V-M-1"
F_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ref -> LCSC, straight from parts/parts.json.  parts.json is the S6
# per-DISTINCT-part shape (no `ref` keys), which `bom_cpl.load_parts_map`
# CANNOT map, so P9's only ref->LCSC source is the per-component `LCSC` field
# stamped here (bom_cpl.board_lcsc_map matches pname.upper() == "LCSC" only -
# the symbol's inherited "LCSC Part" property does NOT satisfy it).
LCSC = {
    "U1": "C544731", "U2": "C579305", "U3": "C92494",
    "R1": "C23067436", "R2": "C23067436", "R3": "C23067436",
    "R4": "C23067436", "R5": "C23067436",
    "R6": "C23185", "R7": "C22859",
    "C1": "C15850", "C2": "C1525", "C3": "C5440143", "C4": "C1525",
    "C5": "C513691", "C6": "C1525", "C7": "C106246", "C8": "C15850",
    "J1": "C8465", "J2": "C37208",
}

# Fields KiCad should keep visible on the plot; everything else is hidden
# after save (the codes and notes must EXIST - P9 reads LCSC off them - but
# kicad-sch-api gives every generator-written field VISIBLE effects, which
# prints them on top of the parts they belong to).
VISIBLE_FIELDS = {"Reference", "Value"}

# ------------------------------------------------------------------ layout
# A4 (297 x 210), per sheets.md s1.  All anchors are multiples of 1.27 mm
# (schlib raises otherwise).  Rows are spaced so no stub label anchor can land
# on a foreign wire run (schlib's _assert_label_clear guard).
X_A, X_B, X_C, X_D = 25.40, 76.20, 116.84, 157.48
X_CAPS = 127.00                 # decoupling-cap row start (dx 25.40)
X_RAIL = 215.90                 # the four rail clusters, right margin
X_HOLE = 266.70                 # mounting holes, far right

Y_IN = 25.40                    # attenuator TOP arm (R1 R2 R3); J1 sits below
                                # it at (38.10, 38.10) - see the rot-90 note
Y_ATT = 50.80                   # attenuator BOTTOM arm (R4 R5) + buffer
Y_RC = 76.20                    # ADC input RC (R6 C7)
Y_SENSE = 95.25                 # *** RESERVED: the -IN sense run channel ***
Y_ADC = 114.30                  # U1 + its rail entry and bypasses
Y_NOTE = 123.19                 # the sheet's note block
Y_REF = 152.40                  # U2 + its bypasses
Y_HOST = 177.80                 # J2 + the bulk cap at the rail entry


# ------------------------------------------------------------- the sense run
def _label_anchors(sh: schlib.Sheet) -> set:
    """Every local-label anchor placed so far.  `wire_pin` records the pin it
    wired in `_pin_nets` and puts the label one STUB outward from it."""
    out = set()
    for (ref, pad) in sh._pin_nets:
        p = sh.pin_pos(ref, pad)
        d = sh._pin_out_dir(ref, pad)
        out.add((round(p[0] + d[0] * schlib.STUB, 4),
                 round(p[1] + d[1] * schlib.STUB, 4)))
    return out


def _pin_points(sh: schlib.Sheet) -> set:
    out = set()
    for ref in sh._lib_ids:
        for pin in sh.sch.components.get(ref).pins:
            out.add(sh.pin_pos(ref, pin.number))
    return out


def sense_run(sh: schlib.Sheet, path: list) -> None:
    """Draw the U1 -IN sense wire as an explicit orthogonal run and PROVE it
    touches nothing but its two endpoints.

    schlib's own guard runs the other way - it rejects a LABEL that lands on
    an existing wire - so a hand-drawn wire needs the mirror check: a segment
    crossing a foreign label anchor or a foreign pin would merge two nets
    silently, and this is the one net on the board where a silent merge is
    the whole failure mode.  Every label added AFTER this call is covered by
    schlib's guard, so the two directions together are complete.
    """
    hazards = (_label_anchors(sh) | _pin_points(sh)) - {path[0], path[-1]}
    for a, b in zip(path, path[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            raise ValueError(f"sense run segment {a}-{b} is not orthogonal")
        for p in hazards:
            if schlib._point_on_segment(p, a, b):
                raise ValueError(
                    f"sense run segment {a}-{b} passes through {p} - it would "
                    f"merge the -IN sense net into another net")
        sh._add_wire(a, b)


# ------------------------------------------------------------------ the note
NOTES = [
    "NOTE 1  U1 -IN IS A DEDICATED SENSE RUN, NOT A GROUND SYMBOL.  It is wired"
    " by the explicit wire below to R5's bottom pad - the attenuator string's",
    "        bottom node - and meets GND only there.  A divider passes a ground"
    " offset at UNITY while dividing the signal by K = 0.400, so 1 mV of",
    "        offset between the string bottom and the converter is 2.5 mV at the"
    " terminal: half the 25 degC budget.  Bound: -IN must stay within",
    "        -0.3 V to +0.5 V of U1's GND pin (ADS8326, absolute).  P7 keeps it"
    " a dedicated run - constraints.json corridor R5 -> U1, 3 mm.",
    "NOTE 2  The guard ring around /AIN_DIV and U3 +IN is P7 COPPER on /AIN_BUF"
    " (the buffer OUTPUT), never on /AIN_DIV itself.  No schematic element.",
    "NOTE 3  R7 + C2 + C8 are the ADS8326's own recommended rail entry (figs"
    " 44/45): R7 upstream of both caps, C2 the smaller and closest to the pin.",
    "        It isolates U1 ALONE - U2 and U3 stay on +3V3 upstream of R7.  No"
    " ferrite anywhere.",
    "NOTE 4  NO series resistor between U2 VOUT and C3 / U1 REF (recorded"
    " ruling): a SAR's reference current varies with input code, so a series R",
    "        becomes a code-dependent nonlinearity.  C5 >= 1 uF is MANDATORY -"
    " the ADR4520's 1-100 uF load-capacitance window is two-ended.",
    "NOTE 5  R1-R5 are FIVE EQUAL 200 k elements in ONE string tapped 3:2"
    " (K = 0.400, Rtot 1.00 Mohm, tap Thevenin 240 kohm).  Do not collapse.",
]


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "bb-adc", paper="A4", rev="A", date="2026-08-17", company="ai-ee",
        pwr_base=1,
        title="bb-adc  0-5V precision front end -> 16-bit SPI SAR (ADS8326IB)")

    def add(lib_id, ref, value, at, footprint, pins, expect=None, note=None,
            rotation=0):
        """Place a purchased part, stamp its LCSC code, wire every pin.

        Every ref routed through here is a BOM line, so a missing code is a
        defect, not a default.  Fail at build time.
        """
        code = LCSC.get(ref)
        if not code:
            raise KeyError(f"{ref}: no LCSC code in the parts map - a "
                           f"purchased part cannot ship unsourced")
        fields = {"LCSC": code}
        if note:
            fields["Note"] = note
        sh.add_component(lib_id, ref, value, at=at, footprint=footprint,
                         fields=fields, expect=expect, rotation=rotation)
        sh.wire_pins(ref, pins)

    # ======================================================== input + string
    # J1: 1 = signal, 2 = its return.  Screw terminal, silk-marked SIG/GND at
    # P6.  The board contracts to Rs <= 200 ohm at this terminal (decision 19).
    # rotation=90 turns J1's two pins sideways so their stubs land 2.54 mm
    # apart VERTICALLY: at rotation 0 both labels sit on one line 2.54 mm
    # apart horizontally and the two net names print on top of each other,
    # which is a readability defect on the board's signal entry.
    # The Value is the MPN rather than parts.json's prose ("2-pos 5.08mm screw
    # terminal"): KiCad rotates a rot-90 symbol's field TEXT but schem_refdes
    # does not (LEARNINGS 2026-08-09), so a long Value renders as a vertical
    # string and a 27-character one runs off the A4 border.
    add(S_J1, "J1", "WJ500V-5.08-2P", (38.10, 38.10), F_J1,
        {"1": "AIN_RAW", "2": "GND"}, rotation=90,
        note="ANALOG IN 0-5V: 1=SIG (Rs<=200ohm), 2=GND. LEFT edge, "
             "opening outward")

    # R1-R5: ONE part number in all five positions, ONE series string from
    # J1's signal pin to the string bottom, tapped between R3 and R4 - THREE
    # elements above the tap and TWO below, so K = 2/5 = 0.400 exactly.
    # The five equal elements ARE the design: 0.02%-grade resistance stops at
    # 200 kohm in stock and the design needs Rtot = 1.00 Mohm, and equal
    # elements make the RATIO depend on relative tolerance, not absolute
    # (blocks.md s3.2/s3.3, decisions 18/22).  Do not collapse to two parts.
    string = (("R1", X_B, Y_IN, "AIN_RAW", "ATT_A"),
              ("R2", X_C, Y_IN, "ATT_A", "ATT_B"),
              ("R3", X_D, Y_IN, "ATT_B", "AIN_DIV"),   # <- the 3:2 tap
              ("R4", X_B, Y_ATT, "AIN_DIV", "ATT_C"),
              ("R5", X_C, Y_ATT, "ATT_C", "GND"))      # <- the bottom node
    for ref, x, y, top, bot in string:
        add(S_R200K, ref, "200K 0.02% 10ppm/C", (x, y), F_R0805,
            {"1": top, "2": bot},
            note="attenuator string element 1 of 5, all one part number; "
                 "K = 0.400 comes from 3 above the tap and 2 below")

    # THE REFERENCE TIE.  The string's bottom node is where the signal chain
    # meets GND, and it is a REFERENCE tie, not a return: it must not share
    # copper with any return carrying other current, because that copper's IR
    # drop adds to the signal at FULL weight.  The GND symbol is placed HERE,
    # on R5's own pad, so the drawing says where ground enters the chain.
    sh.power_symbol_at_pin("R5", "2", "power:GND")

    # ============================================================== buffer
    # U3 OPA320 unity-gain follower.  +IN from the tap, OUT tied to -IN by
    # the shared /AIN_BUF label (the feedback is a WIRE - no resistor).
    # Pin map from parts/C92494.json: 1 OUT, 2 V-, 3 +IN, 4 -IN, 5 V+.
    # C6 is its supply bypass and its placement is a specification, not a
    # habit: a precision amplifier's PSRR falls from ~110-130 dB at DC to
    # roughly 20 dB by 100 kHz, and what gets through a follower appears as a
    # VARYING DC OFFSET, not as noise.
    sh.place_ic_with_decoupling(
        "U3", S_U3, "OPA320", at=(198.12, Y_ATT), footprint=F_U3,
        pins={"1": "AIN_BUF", "2": "GND", "3": "AIN_DIV", "4": "AIN_BUF",
              "5": "+3V3"},
        expect={"1": "OUT", "2": "V-", "3": "IN+", "4": "IN-", "5": "V+"},
        decoupling=[
            {"cap": "C6", "pin": "5", "rail": "+3V3",
             "value": "100nF 16V X7R", "lib_id": S_C100N,
             "footprint": F_C0402},
        ],
        caps_at=(X_HOLE - 25.40, Y_ATT), caps_dx=25.40)

    # ========================================================= ADC input RC
    # R6 + C7 between the buffer output and U1's +IN.  PROVISIONAL values
    # (49.9 ohm / 1 nF) inside the stated windows (20-100 ohm, 1-2.2 nF, and
    # above the 20 x C_SH = 960 pF floor); the P8 sim benches
    # (acquisition-settling, buffer-stability) set the final numbers, and a
    # resim-driven change is a like-for-like Basic-tier swap.
    add(S_R49R9, "R6", "49.9 ohm 1%", (X_B, Y_RC), F_R0603,
        {"1": "AIN_BUF", "2": "AIN_ADC"},
        note="PROVISIONAL 20-100 ohm window; P8 benches set the value")
    add(S_C1N, "C7", "1nF 50V C0G/NP0", (X_D, Y_RC), F_C0603,
        {"1": "AIN_ADC", "2": "GND"},
        note="PROVISIONAL 1-2.2nF window; C0G/NP0 - no DC-bias or "
             "temperature drift")

    # ============================================================ converter
    # U1 ADS8326IB.  Pin map from parts/C544731.json:
    #   1 REF -> VREF        5 CS/SHDN -> /CS
    #   2 +IN -> /AIN_ADC    6 DOUT    -> /DOUT
    #   3 -IN -> SENSE RUN   7 DCLOCK  -> /SCLK
    #   4 GND -> GND         8 VDD     -> VDD_ADC (behind R7)
    # Pin 3 is DELIBERATELY ABSENT from `pins`: wiring it here would give it a
    # label, and a "GND" label at the converter is exactly the failure this
    # board is built to avoid.  It is wired by sense_run() below, after R5
    # and U1 both exist.
    sh.place_ic_with_decoupling(
        "U1", S_U1, "ADS8326IB", at=(X_B, Y_ADC), footprint=F_U1,
        pins={"1": "VREF", "2": "AIN_ADC", "4": "GND", "5": "CS",
              "6": "DOUT", "7": "SCLK", "8": "VDD_ADC"},
        expect={"1": "REF", "2": "+IN", "3": "-IN", "4": "GND", "5": "CS",
                "6": "DOUT", "7": "DCLOCK", "8": "VDD"},
        decoupling=[
            # C2 is the SMALLER of the VDD pair, so it sits closest to the
            # pin; 2 mm is constraints.json's own number, and that loop is
            # the SPI drivers' current loop (D3, < 20 mm^2).
            {"cap": "C2", "pin": "8", "rail": "VDD_ADC",
             "value": "100nF 16V X7R", "lib_id": S_C100N,
             "footprint": F_C0402, "max_dist_mm": 2.0},
            {"cap": "C8", "pin": "8", "rail": "VDD_ADC",
             "value": "10uF 25V X5R", "lib_id": S_C10U,
             "footprint": F_C0805},
            # C3 is NOT decoupling - it is the reservoir the conversion draws
            # from at every bit trial and the reference recharges between bit
            # decisions.  What binds is the LOOP (C3 -> REF pin -> the
            # internal array -> U1 GND -> back), hence 2.5 mm, same layer, no
            # via between pad and cap, and nothing in series.
            {"cap": "C3", "pin": "1", "rail": "VREF",
             "value": "47uF 16V X7R", "lib_id": S_C47U,
             "footprint": F_C1210, "max_dist_mm": 2.5},
        ],
        caps_at=(X_CAPS, Y_ADC), caps_dx=25.40)

    # *** THE SENSE RUN.  U1 pin 3 (-IN) -> R5 pin 2 (the string bottom). ***
    # An explicit orthogonal wire, drawn through the reserved Y_SENSE channel,
    # with every segment proved clear of every existing label anchor and pin.
    # It is drawn HERE, before the remaining labels are placed, so schlib's
    # own guard covers the other direction for everything that follows.
    u1_in = sh.pin_pos("U1", "3")
    r5_bot = sh.pin_pos("R5", "2")
    x_drop = round(u1_in[0] - 4 * schlib.STUB, 4)     # clear of U1's stubs
    sense_run(sh, [u1_in,
                   (x_drop, u1_in[1]),
                   (x_drop, Y_SENSE),
                   (r5_bot[0], Y_SENSE),
                   r5_bot])

    # ================================================== converter rail entry
    # R7 between +3V3 and U1's VDD pin, UPSTREAM of C2/C8.  Datasheet-required
    # (ADS8326 LAYOUT p.26 and figs 44/45 p.27), not "filtering the datasheet
    # does not require" - the distinction the scope tier actually draws.  A
    # SAR has no supply rejection at the instant that matters, because the
    # spikes that hurt land just before the comparator latches.  Cost: ~0.6 mV
    # of DC drop at ~60 uA, which the error budget does not feel because the
    # conversion is referenced to VREF, not to VDD.
    add(S_R10R, "R7", "10 ohm 1%", (X_A, Y_ADC), F_R0603,
        {"1": "+3V3", "2": "VDD_ADC"},
        note="ADS8326 rail-entry isolation, upstream of C2/C8; U2 and U3 "
             "stay on +3V3")

    # ============================================================ reference
    # U2 ADR4520B.  Pin map from parts/C579305.json: 2 VIN, 4 GND, 6 VOUT;
    # 1/3/5/7 NIC and 8 TP are NOT connected (see s2 of this file's header).
    # C5 is MANDATORY and >= 1 uF: the output cap is a compensation element
    # inside the loop and the stable window is two-ended, 1 uF to 100 uF.
    # 2.2 uF on a 10 V part keeps margin above the 1 uF floor after ceramic
    # DC-bias derating at 2.048 V.  NOT a DNP candidate.
    sh.place_ic_with_decoupling(
        "U2", S_U2, "ADR4520B", at=(X_B, Y_REF), footprint=F_U2,
        pins={"1": "NC", "2": "+3V3", "3": "NC", "4": "GND", "5": "NC",
              "6": "VREF", "7": "NC", "8": "NC"},
        expect={"1": "NIC", "2": "VIN", "3": "NIC", "4": "GND", "5": "NIC",
                "6": "VOUT", "7": "NIC", "8": "DNC"},
        decoupling=[
            {"cap": "C4", "pin": "2", "rail": "+3V3",
             "value": "100nF 16V X7R", "lib_id": S_C100N,
             "footprint": F_C0402},
            {"cap": "C5", "pin": "6", "rail": "VREF",
             "value": "2.2uF 10V X7R", "lib_id": S_C2U2,
             "footprint": F_C0603},
        ],
        caps_at=(X_CAPS, Y_REF), caps_dx=25.40)

    # ========================================================== host header
    # J2 is 6 pins and the SIXTH IS GND, not a spare: this converter's SPI is
    # read-only (CS, DCLOCK, DOUT - no MOSI), so the block needs 5, and
    # spending the sixth on a second ground puts a return reference at BOTH
    # ends of the digital group (D3/D4) instead of leaving a pin floating.
    add(S_J2, "J2", "1x6P 2.54mm male header", (X_A, Y_HOST), F_J2,
        {"1": "+3V3", "2": "GND", "3": "CS", "4": "SCLK", "5": "DOUT",
         "6": "GND"},
        note="HOST SPI: 1=+3V3 2=GND 3=/CS 4=/SCLK 5=/DOUT 6=GND. RIGHT "
             "edge, opening outward")

    # C1: bulk reservoir at the RAIL ENTRY, not at the converter.  Earned by
    # arithmetic - a 1 mA step in 100 ns across the host lead's ~1 uH is 10 mV
    # on the rail; into a 10 uF local reservoir the same step is 10 uV.
    add(S_C10U, "C1", "10uF 25V X5R", (X_B, Y_HOST), F_C0805,
        {"1": "+3V3", "2": "GND"},
        note="bulk at the J2 rail entry (constraints group `entry`), NOT at "
             "the converter")

    # ======================================================== geometry-only
    # M3 clearance holes, 3.2 mm NPTH.  ZERO-pin symbol: unplated, no net.
    # Four per requirements.md s5; if the EARNED outline turns out too small
    # for four, two on opposite corners is sanctioned there and is a P6 edit.
    # Both stock mounting-hole footprints declare `exclude_from_bom`, so the
    # symbol instances must agree or KiCad DRC raises "Footprint attributes
    # don't match symbol" once board_init pairs them.
    for i, ref in enumerate(("H1", "H2", "H3", "H4")):
        sh.add_component(S_HOLE, ref, "M3_3.2mm",
                         at=(X_HOLE, round(Y_IN + i * 19.05, 4)),
                         footprint=F_HOLE)
        sh.sch.components.get(ref).in_bom = False

    # =========================================================== power rails
    # Power SYMBOLS make these four nets GLOBAL and BARE; a local label would
    # export "/+3V3" and silently break every constraints.json match.  The
    # symbol's VALUE names the net and schlib sets it from the net argument,
    # so `power:VBUS` with Value "VREF" exports a bare "VREF".
    #
    # PWR_FLAG on three of the four.  A power symbol's own pin is power_in, so
    # a rail whose only other pins are power_in or passive has no driver ERC
    # can see: +3V3 arrives from off-board through a passive header, VDD_ADC
    # sits behind a resistor (which propagates nothing), and GND's pins are
    # all power_in.  VREF needs NO flag - U2 pin 6 is a real power_out.
    # The four clusters stack in the right margin, each on its own row and
    # none of them on Y_SENSE - the sense run owns that channel.
    sh.power_flag("GND", at=(X_RAIL, 82.55), sym="power:GND", flag=True)
    sh.power_flag("+3V3", at=(X_RAIL, 101.60), sym="power:+3V3", flag=True)
    sh.power_flag("VDD_ADC", at=(X_RAIL, 120.65), sym="power:VBUS", flag=True)
    sh.power_flag("VREF", at=(X_RAIL, 139.70), sym="power:VBUS", flag=False)

    # ============================================================ the record
    # add_text is CENTRE-justified with no justify parameter, so the note
    # block uses add_text_box, which has one.
    sh.sch.add_text_box("\n".join(NOTES), position=(12.70, Y_NOTE),
                        size=(190.50, 22.86), font_size=1.0,
                        stroke_width=0.254, stroke_type="solid",
                        fill_type="none", justify_horizontal="left",
                        justify_vertical="top")
    sh.sch.add_text("U1 -IN SENSE RUN to R5 bottom pad - NOT a GND symbol "
                    "at U1", position=(93.98, 90.17), size=1.27)
    return sh


# ------------------------------------------------------- field-visibility
def _match(text: str, open_idx: int) -> int:
    """Index just past the paren opened at `open_idx`, quote-aware."""
    depth, i, n = 0, open_idx, len(text)
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
    """`(hide yes)` on every non-VISIBLE property.  The fields must EXIST
    (P9 reads LCSC off them) but kicad-sch-api gives every generator-written
    field VISIBLE effects, which prints the codes and notes on top of the
    parts they belong to.  Hiding is a plot property only - exactly the form
    KiCad itself writes for Footprint and Datasheet.  Idempotent."""
    text = path.read_text(encoding="utf-8")
    out, pos, hidden = [], 0, 0
    needle = '(property "'
    while True:
        i = text.find(needle, pos)
        if i < 0:
            break
        j = text.index('"', i + len(needle))
        name = text[i + len(needle):j]
        end = _match(text, i)
        node = text[i:end]
        if name in VISIBLE_FIELDS or "(hide yes)" in node:
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


def main(argv=None) -> int:
    args = [a for a in (argv or []) if not a.startswith("--")]
    out_dir = Path(args[0]) if args else HERE.parents[1]      # .../kicad
    try:
        sh = build()
        # LCSC codes on the caps place_ic_with_decoupling created (it takes no
        # fields argument), so every BOM line carries its code.
        for ref in ("C2", "C3", "C4", "C5", "C6", "C8", "U1", "U2", "U3"):
            sh.sch.components.get(ref).set_property("LCSC", LCSC[ref])
        missing = sorted(r for r in LCSC
                         if not sh.sch.components.get(r).get_property("LCSC"))
        if missing:
            raise ValueError(f"refs without an LCSC field: {missing}")
        sch = sh.save(out_dir, project=True)
        hidden = hide_aux_fields(sch)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:                # noqa: BLE001 (SPEC 6: error -> 2)
        print(json.dumps({"script": "gen.bb-adc", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.bb-adc", "status": "pass",
        "files": [str(sch), str(out_dir / "bb-adc.kicad_pro"), str(meta)],
        "components": len(sh.sch.components),
        "decoupling_associations": len(sh.decoupling),
        "fields_hidden": hidden,
        "field_placement": sh.place_report,
    }, indent=1, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
