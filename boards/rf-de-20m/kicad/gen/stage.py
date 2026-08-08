"""rf-de-20m `stage` sheet (blocks.md B3-B6): drive input, LMG1020 gate
driver, the MIRRORED EPC2019 PAIR, the C_shunt trim bank, the RF choke and
the bus HF bank. This sheet is the board.

Refdes range 200-299, `#PWR` base 200 (architecture/sheets.md s3).
Rails are CONSUMED here; all PWR_FLAGs live on `hk` (flag=False below).

Rebuild (writes <out>/stage.kicad_sch; the ROOT generator owns the project):
    .venv/Scripts/python boards/rf-de-20m/kicad/gen/stage.py [OUT_DIR]

GROUND TRUTH
------------
architecture/sheets.md s1/s3/s6, architecture/blocks.md B3-B6 + s3 + s4.1/4.2,
architecture/decisions.md D1/D2/D6/D8/D11, architecture/constraints.json,
parts/parts.json, parts/C2836675.json (EPC2019), parts/C6423790.json
(LMG1020), parts/C22418168.json (SMA), and the library pin tables printed by
`schlib.py --pins "aiee:<SYMBOL>" --lib lib/aiee.kicad_sym`.

THE FOUR WIRING FACTS THAT CANNOT BE GOT FROM MEMORY
-----------------------------------------------------
1. **EPC2019 pin 7 is SUBSTRATE and MUST be netted to SOURCE.** The datasheet
   says so three times (parts/C2836675.json: die-outline note, land-pattern
   note, and the "all measurements were done with substrate connected to
   source" footnote). It is NOT expressible in the footprint, so the SCHEMATIC
   is the only place it can be enforced. The pulled symbol already names pin 7
   "SOURCE", which is why `expect` below asserts SOURCE and not SUBSTRATE -
   the library encoded the requirement and this sheet must not undo it.
   Pin map: 1 GATE / 2 SOURCE / 3 DRAIN / 4 SOURCE / 5 DRAIN / 6 SOURCE /
   7 SUBSTRATE(=SOURCE). All SOURCE pins tie together (GND, the common-source
   star); both DRAIN pins tie together (/SW).

2. **LMG1020 OUTH and OUTL are SEPARATE, SINGLE-DIRECTION outputs.** OUTH
   sources only (7 A) and goes high-Z when not driving; OUTL sinks only (5 A)
   and is held low in every other state (parts/C6423790.json, Table 1). That
   is why each gets its OWN series resistor and why NO steering diode is
   needed - the two resistors independently set turn-on and turn-off slew and
   the idle path is the OUTL pull-down. TI mandates >= 2 ohm on each; the BOM
   part is 3.9 ohm (4.0 ohm is not an E24 value), two in parallel per leg =
   1.95 ohm per leg, which with the EPC2019's own 0.4 ohm RG puts the loop at
   R_G + R_src = 3.1 ohm - exactly the number decisions.md D6's 0.48 nH
   gate-loop budget was solved at. Both resistors of a leg land on the FET
   gate net.

3. **IN- ties to GND and the drive goes to IN+.** From the truth table
   (parts/C6423790.json layout_notes, datasheet Table 1):
       (IN-, IN+) -> (OUTH, OUTL):  (L,L)->(OPEN,L)  (L,H)->(H,OPEN)
                                    (H,L)->(OPEN,L)  (H,H)->(OPEN,L)
   ONLY the IN-=L, IN+=H state drives the gate high, so IN- MUST be low or the
   stage never switches - and IN- carries an internal 100-250 k pull-UP to
   VDD, so leaving it floating would hold the driver off. IN+ carries an
   internal pull-DOWN, so an open drive input fails SAFE (gates off).
   TI's s8.2.2.1 ground-bounce alternative (drive IN-, tie IN+ to VDD) is
   deliberately NOT taken: it INVERTS the drive, and duty cycle is both the
   primary Class E tuning knob and - after P2-A - the primary ZVS trim
   (decisions.md D2/D8), so the generator's duty must map 1:1 onto the FET's.
   This matches sheets.md s6 note 7 ("IN- on U201 ties to GND. No bias
   divider, no buffer.").

4. **The drive input is DC-COUPLED. There is no series blocking capacitor**
   and adding one is a ruling violation, not a tidy-up (decisions.md D8): AC
   coupling's DC restore pins the waveform average at the bias point, so at
   D = 0.4 both logic levels sit above the ~1.4 V threshold and the FETs never
   turn off. The generator must therefore supply UNIPOLAR 0 to +5 V - the
   LMG1020's input abs max is -0.3 V to VDD+0.3 V, so a bipolar +/-2.5 V
   generator violates it (OPEN-1, owner, before bring-up). Termination is
   R201||R202 = 50 ohm to GND AT THE CONNECTOR.

VALUE DEVIATION RECORDED HERE: THE C_shunt TRIM BANK IS 56 pF, NOT 33 pF
------------------------------------------------------------------------
blocks.md/sheets.md describe C203-C206 as "4x 33 pF, populate 3 = 99 pF".
**No 33 pF part exists on this board.** parts/parts.json (the BOM of record)
maps C203-C206 onto the SAME 56 pF 1 kV C0G 1206 part as the tank banks -
one part number in three roles, which is that entry's stated intent. Rather
than invent an unsourced BOM line, the bank is built from the sourced part
and the POPULATE COUNT is re-solved:

    required C_shunt      403 pF (449 pF if Sokal's finite-choke term applies)
    supplied by the pair   316 pF typ / 410 pF max  (2 x Coss(tr))
    external needed        87 pF typ, 0-133 pF of range
    THIS BANK             2 x 56 pF = 112 pF populated  ->  total 428 pF
                          which is the MIDDLE of the 403-449 pF requirement
    trim range            0 / 56 / 112 / 168 / 224 pF by populate

C205/C206 carry `Variant=DNP`. A max-Coss pair (410 pF) is absorbed by
emptying the bank, which is the whole reason D2 calls the bank load-bearing.
The cost of the coarser step is 56 pF instead of 33 pF of resolution; if
SIM-2's `trim_pf_needed` lands between the steps, P3 adds a 33 pF 1 kV C0G
1206 line and the sites take it unchanged.

TWO OTHER DELIBERATE DEVIATIONS FROM parts.json
------------------------------------------------
  * **The choke pair is L201 + L202, not L201A + L201B.** Letter-suffixed
    refdes are a known pipeline hazard (place_anneal silently drops refs it
    does not recognise - LEARNINGS 2026-07-28), and constraints.json names
    "L201" in `thermal[]` and in the `switch` placement group, where a
    missing ref is a netlist_audit ERROR. kicad/constraints.json is amended
    to carry L202 as well; architecture/constraints.json and parts.json need
    the same edit (reported, not silently assumed).
  * **C213 is ADDED: the 1 uF local reservoir TI requires.** parts/C6423790.json
    s9/s10.1.2 is unambiguous - "the combination of a 0.1 uF ... (closest to
    LMG1020) and a 1 uF 0603 capacitor is recommended" and "an additional
    1 uF capacitor MUST be placed as close to the IC as practical". The
    architecture's C201 (100 nF) + C202 (10 nF) pair is the low-ESL half of
    that and is kept verbatim; the reservoir half was missing, and the only
    +5 V bulk on the board (C108, 22 uF) sits on `hk` at the far end of zone
    A by design. C213 reuses the 1 uF 16 V X7R 0603 already on the BOM.

NET NAMING (sheets.md s1 - BINDING)
------------------------------------
* `GND` / `+40V` / `+5V` are POWER SYMBOLS -> global and BARE. flag=False:
  `hk` owns every PWR_FLAG.
* `SW` is the ONLY hierarchical pin. It crosses the root (also exposed by
  `tank`) and therefore comes out **`/SW`**, which is what six
  constraints.json entries require.
* Six nets are sheet-internal and come out `/stage/<NAME>`: DRIVE, GATE_ON,
  GATE_OFF, GATE_Q1, GATE_Q2, L201_MID. The first five are named in
  constraints.json with exactly those prefixes.
* **The OUTH/OUTL legs are GATE_ON / GATE_OFF, never GATE_H / GATE_L.**
  rules_gen.detect_diff_pairs auto-pairs high_speed nets ending _H/_L and
  would emit a 100 ohm diff-pair rule plus an inner-layer track ban on the
  two most inductance-critical nets on the board. Do not rename them.

NOT ON THIS SHEET
-----------------
No gate-clamp, no negative bias, no Miller clamp, no TVS on /SW, no series
input capacitor. All ruled out at P0/P2 (blocks.md s5, decisions.md rejected
table). The 1.40x voltage derate on /SW is protected by POWER LOOP AREA at
P6/P7, not by a part.
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
V40 = "+40V"
V5 = "+5V"
SW = "SW"                  # hier, out to `tank` via the root -> /SW
DRIVE = "DRIVE"            # -> /stage/DRIVE
GATE_ON = "GATE_ON"        # -> /stage/GATE_ON   (OUTH leg - NOT _H)
GATE_OFF = "GATE_OFF"      # -> /stage/GATE_OFF  (OUTL leg - NOT _L)
GATE_Q1 = "GATE_Q1"        # -> /stage/GATE_Q1
GATE_Q2 = "GATE_Q2"        # -> /stage/GATE_Q2
L_MID = "L201_MID"         # -> /stage/L201_MID  junction of the series chokes

# ------------------------------------------------------------------ symbols
S_SMA = "aiee:CONSMA001-SMD-G-T"          # default Reference "RF" -> J201
S_R100 = "aiee:0805W8F1000T5E"
S_U201 = "aiee:LMG1020YFFR"
S_C100N_0402 = "aiee:CC0402KRX7R7BB104"   # 100nF 16V X7R 0402
S_C10N_0201 = "aiee:0201B103K250NT"       # 10nF 25V X7R 0201
S_C1U_0603 = "aiee:CC0603KRX7R7BB105"     # 1uF 16V X7R 0603
S_R3R9 = "aiee:0603WAF390KT5E"
S_Q = "aiee:EPC2019"
S_C56P = "aiee:CC1206JKNPOCBN560"         # 56pF 1kV C0G 1206
S_L201 = "aiee:FXL0630-R47-M"             # 470nH molded, 20A Isat
S_C10N_100V = "aiee:CC0603KRX7R0BB103"    # 10nF 100V X7R 0603
S_C1N_100V = "aiee:CC0603JRNPO0BN102"     # 1nF 100V C0G 0603

# --------------------------------------------------------------- footprints
F_SMA = "aiee:SMA-SMD_CONSMA001-SMD-G-T"
F_R0805 = "aiee:R0805"
F_R0603 = "aiee:R0603"
F_U201 = "aiee:BGA-6_L1.3-W0.8-P0.40-TL_PTMAG3001A2YBGR"
F_C0402 = "aiee:C0402"
F_C0201 = "aiee:C0201"
F_C0603 = "aiee:C0603"
F_C1206 = "aiee:C1206"
F_Q = "aiee:TRS-SMD_EPC2019"
F_L201 = "aiee:IND-SMD_L7.0-W6.6_FXL0630"

# ------------------------------------------------------------------- values
V_SMA = "SMA jack 50R SMD (CONSMA001)"
V_R100 = "100R 0805 1%"
V_U201 = "LMG1020 5V GaN driver 7A/5A"
V_C100N = "100nF 16V X7R 0402"
V_C10N_0201 = "10nF 25V X7R 0201"
V_C1U = "1uF 16V X7R 0603"
V_R3R9 = "3R9 0603 1%"
V_Q = "EPC2019 200V eGaN"
V_C56P = "56pF 1kV C0G 1206"
V_L201 = "470nH 20A 4.1mohm"
V_C10N = "10nF 100V X7R 0603"
V_C1N = "1nF 100V C0G 0603"

LCSC = {
    "J201": "C22418168",
    "R201": "C17408", "R202": "C17408",
    "U201": "C6423790",
    "C201": "C60474", "C202": "C285010", "C213": "C106248",
    "Q201": "C2836675", "Q202": "C2836675",
    "L201": "C167212", "L202": "C167212",
    "C203": "C113875", "C204": "C113875", "C205": "C113875", "C206": "C113875",
    "C207": "C107059", "C208": "C107059", "C209": "C107059", "C210": "C107059",
    "C211": "C113793", "C212": "C113793",
}
for _r in ("R203", "R204", "R205", "R206", "R207", "R208", "R209", "R210"):
    LCSC[_r] = "C23020"

# LMG1020 pin map (parts/C6423790.json + `--pins aiee:LMG1020YFFR`).
U201_PINS = {
    "A1": V5,        # VDD, power_in
    "A2": GATE_ON,   # OUTH - source-only, high-Z when idle
    "B1": GND,       # GND - single-point tie to the source star (TI s10.1.1)
    "B2": GATE_OFF,  # OUTL - sink-only, held low in every non-drive state
    "C1": DRIVE,     # IN+ - the PWM input (internal 150k pull-DOWN, fails off)
    "C2": GND,       # IN- - MUST be low; internal 150k pull-UP to VDD
}

# EPC2019 pin map, identical for both FETs. Pin 7 SUBSTRATE -> SOURCE is the
# hard datasheet requirement the footprint cannot express.
def _fet_pins(gate: str) -> dict:
    return {"1": gate, "2": GND, "3": SW, "4": GND, "5": SW, "6": GND,
            "7": GND}


FET_EXPECT = {"1": "GATE", "2": "SOURCE", "3": "DRAIN", "4": "SOURCE",
              "5": "DRAIN", "6": "SOURCE", "7": "SOURCE"}

# The four gate legs. Two 0603s in parallel per leg: it roughly halves the
# leg's parasitic inductance and keeps each part at 0.029 W (blocks.md s3).
# An INDIVIDUAL resistor per FET per polarity is what damps the differential
# mode between the two gate loops - a shared resistor leaves the gates coupled
# through the driver output and free to oscillate against each other (B4).
GATE_LEGS = [
    ("R203", GATE_ON, GATE_Q1), ("R204", GATE_ON, GATE_Q1),
    ("R205", GATE_ON, GATE_Q2), ("R206", GATE_ON, GATE_Q2),
    ("R207", GATE_OFF, GATE_Q1), ("R208", GATE_OFF, GATE_Q1),
    ("R209", GATE_OFF, GATE_Q2), ("R210", GATE_OFF, GATE_Q2),
]

# C_shunt trim sites. See the module docstring for the 33 pF -> 56 pF ruling.
CSHUNT_SITES = [("C203", False), ("C204", False),
                ("C205", True), ("C206", True)]      # (ref, dnp)

RAILS = [                       # symbols only - `hk` owns every PWR_FLAG
    (GND, "power:GND", (25.4, 25.4)),
    (V5, "power:+5V", (25.4, 40.64)),
    (V40, "power:+48V", (25.4, 55.88)),
]


def _add(sh, ref, lib_id, value, at, footprint=None, expect=None, note=None,
         dnp=False, rotation=0):
    fields = {}
    code = LCSC.get(ref)
    if code:
        fields["LCSC"] = code
    if dnp:
        # KiCad's native DNP flag is unreachable from kicad-sch-api (its
        # writer hard-codes `(dnp no)`) - LEARNINGS 2026-08-07. `Variant` is
        # the only marking available inside build(), and NOTHING in the skill
        # reads any DNP mark today, so P9 must filter these by hand.
        fields["Variant"] = "DNP"
    if note:
        fields["Note"] = note
    return sh.add_component(lib_id, ref, value, at, rotation=rotation,
                            footprint=footprint, fields=fields or None,
                            expect=expect)


def _note(sh, at, lines, dy=5.08):
    x, y = at
    for i, line in enumerate(lines):
        sh.sch.add_text(line, position=(x, round(y + i * dy, 4)))


def build() -> schlib.Sheet:
    sh = schlib.Sheet("stage",
                      title="rf-de-20m: stage - drive, LMG1020, EPC2019 pair, "
                            "C_shunt trim, choke, bus HF",
                      paper="A2", date="2026-08-07", company="ai-ee",
                      pwr_base=200)

    # rails: consuming symbols only (flag=False) - see module docstring
    for net, sym, at in RAILS:
        sh.power_flag(net, at=at, sym=sym, flag=False)

    # =====================================================================
    # B3 - RF drive input.  DC-COUPLED.  50 ohm AT THE CONNECTOR.
    # =====================================================================
    # J201 pin map from parts/C22418168.json: pins 1-4 are the four square
    # ground lands (connector body / shield), pin 5 is the centre RF contact.
    _add(sh, "J201", S_SMA, V_SMA, (114.3, 88.9), footprint=F_SMA,
         expect={str(n): str(n) for n in range(1, 6)},
         note="Drive in, 20 MHz unipolar 0/+5V. DC-COUPLED - no series cap")
    sh.wire_pins("J201", {"1": GND, "2": GND, "3": GND, "4": GND, "5": DRIVE})

    # 2 x 100 R in parallel = 50 ohm. ~0.125 W total in the termination, which
    # is over a single 0603's derated rating in a 100 C-class environment, so
    # the split is a rating decision and not decoration (blocks.md B3).
    for ref, x in (("R201", 203.2), ("R202", 266.7)):
        _add(sh, ref, S_R100, V_R100, (x, 88.9), footprint=F_R0805,
             expect={"1": "1", "2": "2"},
             note="50R termination = R201||R202, at the connector")
        sh.wire_pins(ref, {"1": DRIVE, "2": GND})

    # =====================================================================
    # B4 - gate driver
    # =====================================================================
    # All three bypass caps are recorded as decoupling ASSOCIATIONS on VDD:
    # the rail is the global bare "+5V", so no rail_net override is needed.
    # max_loop_nh 0.3 is constraints.json's VDD-loop budget (a DIFFERENT and
    # tighter path than the 0.48 nH GATE loop - one is inductance-limited with
    # no series resistor, the other is resistance-limited by R_G).
    sh.place_ic_with_decoupling(
        "U201", S_U201, V_U201, at=(114.3, 177.8), pins=U201_PINS,
        footprint=F_U201,
        expect={"A1": "VDD", "A2": "OUTH", "B1": "GND", "B2": "OUTL",
                "C1": "IN+", "C2": "IN-"},
        decoupling=[
            {"cap": "C201", "pin": "A1", "rail": V5, "value": V_C100N,
             "lib_id": S_C100N_0402, "footprint": F_C0402,
             "max_dist_mm": 0.5, "max_loop_nh": 0.3},
            {"cap": "C202", "pin": "A1", "rail": V5, "value": V_C10N_0201,
             "lib_id": S_C10N_0201, "footprint": F_C0201,
             "max_dist_mm": 0.5, "max_loop_nh": 0.3},
            # TI s9 / s10.1.2: an ADDITIONAL 1 uF as close as practical.
            {"cap": "C213", "pin": "A1", "rail": V5, "value": V_C1U,
             "lib_id": S_C1U_0603, "footprint": F_C0603, "max_dist_mm": 3.0},
        ],
        caps_at=(266.7, 177.8), caps_dx=63.5)

    # Four legs, two 0603 in parallel each. Both OUTH resistors of a FET and
    # both OUTL resistors of the same FET land on that FET's gate net.
    for i, (ref, src, dst) in enumerate(GATE_LEGS):
        x = 88.9 + (i % 4) * 63.5
        y = 241.3 + (i // 4) * 25.4
        _add(sh, ref, S_R3R9, V_R3R9, (x, y), footprint=F_R0603,
             expect={"1": "1", "2": "2"},
             note="gate leg %s -> %s (TI floor >=2R; pair = 1.95R)"
                  % (src, dst))
        sh.wire_pins(ref, {"1": src, "2": dst})

    # =====================================================================
    # B5 - the GaN switch: TWO EPC2019, MIRRORED PAIR, both populated
    # =====================================================================
    # A one-FET build is NOT survivable at any heatsink (decisions.md D1:
    # Tj 160 C with a hypothetical 0 C/W sink, above the 150 C absolute
    # maximum), so neither device is DNP.
    for ref, gate, y in (("Q201", GATE_Q1, 241.3), ("Q202", GATE_Q2, 292.1)):
        _add(sh, ref, S_Q, V_Q, (393.7, y), footprint=F_Q,
             expect=FET_EXPECT,
             note="pin 7 SUBSTRATE tied to SOURCE (datasheet, 3x). "
                  "Mirror pair about the U201 axis - locked at P6")
        sh.wire_pins(ref, _fet_pins(gate))

    # C_shunt trim bank, IN the power loop (a trim cap on a stub adds
    # inductance instead of capacitance). See the module docstring.
    for i, (ref, dnp) in enumerate(CSHUNT_SITES):
        _add(sh, ref, S_C56P, V_C56P, (88.9 + i * 63.5, 317.5),
             footprint=F_C1206, expect={"1": "1", "2": "2"}, dnp=dnp,
             note=("C_shunt trim site - DNP, populate to raise C_shunt"
                   if dnp else
                   "C_shunt trim, POPULATED (2 x 56pF = 112pF external)"))
        sh.wire_pins(ref, {"1": SW, "2": GND})

    # =====================================================================
    # B6 - drain feed and bus decoupling
    # =====================================================================
    # L201 + L202 in SERIES = 0.94 uH: the architecture's own PRE-AUTHORISED
    # escape (blocks.md B6, "2 x 0.47 uH in series"), taken because no single
    # LCSC part meets L>=0.82uH AND SRF>=80MHz AND DCR<=25mohm AND Isat>=12A.
    # NOT authorised, and not taken: a smaller single choke - below the
    # omega.L/R floor the ideal Class E equations stop holding AND Sokal's
    # finite-DC-feed term RAISES the required shunt capacitance.
    # P6 must place the two physically separated (parts.json role note).
    _add(sh, "L201", S_L201, V_L201, (88.9, 355.6), footprint=F_L201,
         expect={"1": "1", "2": "2"},
         note="RF drain choke 1 of 2 in SERIES (0.94uH total, 8.2mohm)")
    sh.wire_pins("L201", {"1": V40, "2": L_MID})
    _add(sh, "L202", S_L201, V_L201, (177.8, 355.6), footprint=F_L201,
         expect={"1": "1", "2": "2"},
         note="RF drain choke 2 of 2 - place PHYSICALLY SEPARATED from L201")
    sh.wire_pins("L202", {"1": L_MID, "2": SW})

    # Bus HF bank: 4 x 10 nF + 2 x 1 nF, within 3 mm of the choke's bus-side
    # pad, sized for |Z| < 1 ohm at 20 MHz. X7R is acceptable on the DC bus
    # (P3 substitution - genuine 100 V/10 nF C0G is unstocked) and NEVER in
    # the tank; the 1 nF parts are real C0G and terminate the bank's own
    # self-resonance.
    for i, ref in enumerate(("C207", "C208", "C209", "C210")):
        _add(sh, ref, S_C10N_100V, V_C10N, (88.9 + i * 63.5, 393.7),
             footprint=F_C0603, expect={"1": "1", "2": "2"},
             note="bus HF bank - within 3mm of L201's bus-side pad")
        sh.wire_pins(ref, {"1": V40, "2": GND})
    for i, ref in enumerate(("C211", "C212")):
        _add(sh, ref, S_C1N_100V, V_C1N, (342.9 + i * 63.5, 393.7),
             footprint=F_C0603, expect={"1": "1", "2": "2"},
             note="terminates the HF bank's self-resonance")
        sh.wire_pins(ref, {"1": V40, "2": GND})

    # =====================================================================
    # sheet interface - ONE hierarchical pin
    # =====================================================================
    # Free-cluster variant: local label at one end, hierarchical label at the
    # other, joined by wire GEOMETRY. `output` because this sheet drives the
    # node (the child-side label always writes as `input` - kicad-sch-api
    # drops the shape - but the ROOT sheet pin, which is the side that lands,
    # gets it right).
    sh.hier_pin(SW, shape="output", at=(25.4, 88.9))

    # =====================================================================
    # sheet notes
    # =====================================================================
    _note(sh, (469.9, 25.4), [
        "EPC2019 PIN 7 IS SUBSTRATE AND IS TIED TO",
        "SOURCE. The datasheet states it three times.",
        "It is NOT expressible in the footprint - this",
        "schematic is the only place it is enforced.",
        "All SOURCE pins (2/4/6/7) -> GND; both DRAIN",
        "pins (3/5) -> /SW.",
    ])
    _note(sh, (469.9, 63.5), [
        "OUTH AND OUTL ARE SEPARATE OUTPUTS.",
        "OUTH sources only and floats when idle;",
        "OUTL sinks only and is held low otherwise.",
        "Each gets its OWN >=2 ohm resistor (TI",
        "mandate). NO steering diode is needed or",
        "wanted. 2 x 3R9 per leg = 1.95R; with the",
        "FET's own 0.4R that is the 3.1 ohm the",
        "0.48 nH gate-loop budget was solved at.",
    ])
    _note(sh, (469.9, 111.76), [
        "IN- IS TIED TO GND, DRIVE GOES TO IN+.",
        "Truth table: only (IN-=L, IN+=H) drives the",
        "gate high. IN- has an internal pull-UP to",
        "VDD, so floating it holds the stage OFF;",
        "IN+ has an internal pull-DOWN, so an open",
        "drive input fails SAFE. TI's ground-bounce",
        "alternative (drive IN-, IN+ to VDD) is NOT",
        "used: it inverts, and duty cycle is the",
        "primary ZVS trim.",
    ])
    _note(sh, (469.9, 165.1), [
        "THE DRIVE INPUT IS DC-COUPLED - RULING D8.",
        "Do not add a series blocking capacitor 'for",
        "safety': AC coupling's DC restore pins the",
        "average at the bias point and at D=0.4 both",
        "logic levels sit above the 1.4 V threshold,",
        "so the FETs never turn off.",
        "Generator MUST be unipolar 0 to +5 V - the",
        "input abs max is -0.3 V to VDD+0.3 V, so",
        "+/-2.5 V bipolar violates it (OPEN-1).",
    ])
    _note(sh, (469.9, 218.44), [
        "C203-C206 ARE 56 pF, NOT 33 pF.",
        "No 33 pF part exists on this BOM; parts.json",
        "maps these sites onto the same 56 pF 1 kV",
        "C0G part as the tank banks. Populate count",
        "re-solved: 2 x 56 = 112 pF external, giving",
        "316 + 112 = 428 pF against a 403-449 pF",
        "requirement - mid-band. C205/C206 are DNP",
        "headroom; the bank EMPTIES for a max-Coss",
        "pair, which is the point of it existing.",
    ])
    _note(sh, (469.9, 271.78), [
        "GATE LOOPS ARE THE TIGHTEST SPEC ON THE",
        "BOARD: <= 0.48 nH per FET, matched +/-0.1 nH,",
        "and geometrically MIRRORED about the U201",
        "axis. Do NOT length-match electrically -",
        "FR4 is 6.7 ps/mm and skew is benign in a",
        "soft-switched topology. Matching exists to",
        "damp the differential mode and equalise",
        "static sharing. Fallback if P7 cannot meet",
        "it: R_G = 3 ohm -> 0.84 nH, at +0.3 W and",
        "+1.6 C. Take it consciously.",
    ])
    _note(sh, (469.9, 330.2), [
        "L201 + L202 ARE ONE CHOKE, IN SERIES.",
        "0.94 uH total - the architecture's own",
        "pre-authorised escape. A smaller single",
        "choke is NOT authorised: it breaks the",
        "ideal Class E equations and RAISES the",
        "required shunt capacitance.",
    ])
    _note(sh, (469.9, 368.3), [
        "NO PROTECTION PARTS. No TVS on /SW, no gate",
        "clamp, no negative bias. Owner-acknowledged",
        "at P0 Q11. The 1.40x derate on a 200 V part",
        "is protected by POWER LOOP AREA at P6/P7.",
    ])
    return sh


def main(argv=None) -> int:
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
        hidden = genlib.hide_aux_fields(path)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.stage", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.stage", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "internal_nets": sorted({DRIVE, GATE_ON, GATE_OFF, GATE_Q1, GATE_Q2,
                                 L_MID}),
        "dnp": sorted(r for r, d in CSHUNT_SITES if d),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
