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
   the idle path is the OUTL pull-down.

   **TI's >= 2 ohm mandate is on the PIN, and TWO FETs share each pin.**
   (P4 review E1, fixed 2026-08-08.) The pre-review build put 2 x 3R9 in
   parallel on each of four legs, so OUTH saw 4 x 3R9 = 0.975 ohm and OUTL
   the same - less than half the floor, at 5.1 A of peak source current
   against only ~1.1 V of headroom to the EPC2019's +6 V VGS abs max. With
   N FETs on one pin the per-BRANCH value must be >= N x 2 ohm; at N = 2
   that is >= 4 ohm, so the bank is now ONE 4.7 ohm 0805 per leg per FET:

       OUTH (A2) --+-- R203 4R7 --> GATE_Q1     parallel at the pin:
                   +-- R204 4R7 --> GATE_Q2       4.7 / 2 = 2.35 ohm
       OUTL (B2) --+-- R205 4R7 --> GATE_Q1       (2.33 ohm at -1% tol)
                   +-- R206 4R7 --> GATE_Q2       vs TI's 2.00 ohm floor

   Peak drive current falls to 5.0 / 2.35 = **2.13 A** at each pin (was
   5.1 A), against 7 A source / 5 A sink capability. Per-FET branch current
   is 5.0 / (4.7 + 0.4 + 0.75) = 0.85 A.

   TWO CONSEQUENCES, BOTH RECORDED SO NOBODY RE-TIGHTENS THEM:
   * **The 0.48 nH gate-loop budget RELAXES to ~1.70 nH per FET.** EPC WP008
     Eq.1 is L <= R^2.C_GS/4; at the old R_G+R_src = 3.1 ohm and C_GS 199 pF
     that gave 0.478 nH, and at the new 4.7 + 0.4 + 0.75 = 5.85 ohm it gives
     1.70 nH. That 3.6x is what pays for the bigger 0805 body and for
     dropping to one resistor per leg. constraints.json still declares the
     tighter 0.48 nH - deliberately: it costs nothing to keep aiming there.
   * **Turn-off is slower and the stage pays for it.** decisions.md D6's
     sanctioned fallback was R_G = 3 ohm at +0.3 W / +1.6 C; scaling that
     fit (turn-off loss ~ R^2) to 5.85 ohm total gives roughly +1 W across
     the pair and ~+5 C of Tj - Tj ~119 C nominal / ~138 C at the
     max-datasheet corner, still inside the 150 C absolute maximum. This is
     the direction the TI floor forces and it is taken consciously.

   Per-resistor dissipation, which is why the package grew 0603 -> 0805:
   Qg 1.8 nC typ / 2.5 nC max, so P per FET = Qg.VDD.fSW = 0.18 / 0.25 W,
   half on each edge, of which the external resistor takes ~80% ->
   **0.072 W typ / 0.100 W max per part**. An 0603 is rated 0.100 W (65 mW
   once derated to a 90 C local board) and would have repeated the E6
   defect; the 0805 part here is rated 0.250 W (191 mW at 90 C) = 52 % used
   at the max-Qg corner.

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

   **THE TERMINATION IS 2 x 100 R in 2010, NOT 0805** (P4 review E6, fixed
   2026-08-08). The 0805 sizing was computed for a bipolar +/-2.5 V drive
   (0.125 W total); the MANDATED unipolar 0/+5 V square at 50 % duty puts
   **0.250 W** into the termination - P = (5^2/50) x 0.5 - i.e. 0.125 W per
   part, exactly 100 % of an 0805's 1/8 W rating at 70 C and ~154 % of its
   capability in the 100 C-class local environment blocks.md assumes. The
   2010 part is rated 0.750 W (0.485 W derated to 100 C), so each resistor
   now runs at **25.8 % of its derated capability - 3.9x margin**. Package
   parasitics are irrelevant at 20 MHz: ~1.5 nH per 2010, 0.75 nH for the
   pair, j0.09 ohm against 50 ohm.

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

THE +5 V RAIL IS SPLIT: +5V (buck) -> FB201 -> +5V_DRV (driver)
----------------------------------------------------------------
P4 review W4. `parts/C34355.json` layout_notes[7] deferred "filtering on the
+5V feed to LMG1020" to P4/P6, and P4 originally resolved only the decoupling,
leaving +5V one low-impedance node from L101 all the way to U201.A1. The
driver draws 2 x Qg x fSW = 72 mA typ / 100 mA max AT A 20 MHz REPETITION
RATE; with nothing in series that current returns across the whole board to
C108 (22 uF, on `hk`, at the far end of zone A by design) instead of staying
inside the driver's local 1.1 uF - a board-scale 20 MHz loop running past the
FB trace TI's own layout guideline 3 says to keep clear of switching nodes.

FB201 (Murata BLM21PG121SN1D, 120 ohm at 100 MHz, 0805) turns C108 || FB201
|| (C201+C202+C213) into a pi filter and contains the loop. The bead is
chosen for **DCR, not for peak impedance**: 30 mohm gives a 3 mV DC drop at
100 mA, which matters because E3's rail floor has only ~85 mV of margin to
the LMG1020's 4.75 V minimum - a 300 mohm 600-ohm-class bead would have
spent a third of it. NOT a protection part; no TVS/fuse/NTC is added.

Net-naming consequence: the driver side is a SEPARATE rail, `+5V_DRV`, and it
needs its OWN PWR_FLAG on this sheet. That does NOT contradict the "hk owns
every PWR_FLAG" rule, which exists because two flags on the SAME net collide
power_out <-> power_out; +5V_DRV is a different net and is undriven without
one (U201.A1 is a power_in pin). `+5V` on `hk` keeps its own single flag.

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
V5D = "+5V_DRV"            # driver side of FB201 - global bare rail, own FLAG
SW = "SW"                  # hier, out to `tank` via the root -> /SW
DRIVE = "DRIVE"            # -> /stage/DRIVE
GATE_ON = "GATE_ON"        # -> /stage/GATE_ON   (OUTH leg - NOT _H)
GATE_OFF = "GATE_OFF"      # -> /stage/GATE_OFF  (OUTL leg - NOT _L)
GATE_Q1 = "GATE_Q1"        # -> /stage/GATE_Q1
GATE_Q2 = "GATE_Q2"        # -> /stage/GATE_Q2
L_MID = "L201_MID"         # -> /stage/L201_MID  junction of the series chokes

# ------------------------------------------------------------------ symbols
S_SMA = "aiee:CONSMA001-SMD-G-T"          # default Reference "RF" -> J201
S_R100 = "aiee:201007F1000T4E"            # 100R 2010 1% 750mW (E6)
S_U201 = "aiee:LMG1020YFFR"
S_C100N_0402 = "aiee:CC0402KRX7R7BB104"   # 100nF 16V X7R 0402
S_C10N_0201 = "aiee:0201B103K250NT"       # 10nF 25V X7R 0201
S_C1U_0603 = "aiee:CC0603KRX7R7BB105"     # 1uF 16V X7R 0603
S_R4R7 = "aiee:RK73H2ATTD4R70F"           # 4R7 0805 1% 250mW (E1)
S_FB = "aiee:BLM21PG121SN1D"              # 120R@100MHz 0805 bead, 30mohm (W4)
S_Q = "aiee:EPC2019"
S_C56P = "aiee:CC1206JKNPOCBN560"         # 56pF 1kV C0G 1206
S_L201 = "aiee:FXL0630-R47-M"             # 470nH molded, 20A Isat
S_C10N_100V = "aiee:CC0603KRX7R0BB103"    # 10nF 100V X7R 0603
S_C1N_100V = "aiee:CC0603JRNPO0BN102"     # 1nF 100V C0G 0603

# --------------------------------------------------------------- footprints
F_SMA = "aiee:SMA-SMD_CONSMA001-SMD-G-T"
F_R2010 = "aiee:R2010"
F_R0805 = "aiee:R0805"
F_L0805 = "aiee:L0805"
F_U201 = "aiee:BGA-6_L1.3-W0.8-P0.40-TL_PTMAG3001A2YBGR"
F_C0402 = "aiee:C0402"
F_C0201 = "aiee:C0201"
F_C0603 = "aiee:C0603"
F_C1206 = "aiee:C1206"
F_Q = "aiee:TRS-SMD_EPC2019"
F_L201 = "aiee:IND-SMD_L7.0-W6.6_FXL0630"

# ------------------------------------------------------------------- values
V_SMA = "SMA jack 50R SMD (CONSMA001)"
V_R100 = "100R 2010 1% 750mW"
V_U201 = "LMG1020 5V GaN driver 7A/5A"
V_C100N = "100nF 16V X7R 0402"
V_C10N_0201 = "10nF 25V X7R 0201"
V_C1U = "1uF 16V X7R 0603"
V_R4R7 = "4R7 0805 1% 250mW"
V_FB = "120R@100MHz bead 3A 30mohm"
V_Q = "EPC2019 200V eGaN"
V_C56P = "56pF 1kV C0G 1206"
V_L201 = "470nH 20A 4.1mohm"
V_C10N = "10nF 100V X7R 0603"
V_C1N = "1nF 100V C0G 0603"

LCSC = {
    "J201": "C22418168",
    "R201": "C421954", "R202": "C421954",
    "U201": "C6423790",
    "FB201": "C79382",
    "C201": "C60474", "C202": "C285010", "C213": "C106248",
    "Q201": "C2836675", "Q202": "C2836675",
    "L201": "C167212", "L202": "C167212",
    "C203": "C113875", "C204": "C113875", "C205": "C113875", "C206": "C113875",
    "C207": "C107059", "C208": "C107059", "C209": "C107059", "C210": "C107059",
    "C211": "C113793", "C212": "C113793",
}
for _r in ("R203", "R204", "R205", "R206"):
    LCSC[_r] = "C160081"

# LMG1020 pin map (parts/C6423790.json + `--pins aiee:LMG1020YFFR`).
U201_PINS = {
    "A1": V5D,       # VDD, power_in - DRIVER side of the FB201 bead (W4)
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

# The four gate legs - ONE 4R7 0805 each (P4 review E1; see the docstring).
# An INDIVIDUAL resistor per FET per polarity is what damps the differential
# mode between the two gate loops - a shared resistor leaves the gates coupled
# through the driver output and free to oscillate against each other (B4).
# Q201's and Q202's branches are IDENTICAL by construction: same part, same
# value, same tolerance, one per leg, so static sharing and the differential
# damping stay symmetric.
GATE_LEGS = [
    ("R203", GATE_ON, GATE_Q1),
    ("R204", GATE_ON, GATE_Q2),
    ("R205", GATE_OFF, GATE_Q1),
    ("R206", GATE_OFF, GATE_Q2),
]

# C_shunt trim sites. See the module docstring for the 33 pF -> 56 pF ruling.
CSHUNT_SITES = [("C203", False), ("C204", False),
                ("C205", True), ("C206", True)]      # (ref, dnp)

RAILS = [                       # symbols only - `hk` owns THESE rails' flags
    (GND, "power:GND", (25.4, 25.4)),
    (V5, "power:+5V", (25.4, 40.64)),
    (V40, "power:+48V", (25.4, 55.88)),
]
# +5V_DRV exists only on this sheet (it is created here, by FB201), so its
# PWR_FLAG lives here too - U201.A1 is a power_in pin and nothing else on the
# net is a driver. Not a collision with `hk`: different net, one flag each.
RAIL_DRV_AT = (25.4, 71.12)


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
    # ...except +5V_DRV, which is BORN on this sheet and must carry its own
    # flag (W4). Symbol + flag: the symbol makes the net global and bare, the
    # flag drives U201.A1's power_in pin.
    sh.power_flag(V5D, at=RAIL_DRV_AT, sym="power:+5V", flag=True)

    # =====================================================================
    # B3 - RF drive input.  DC-COUPLED.  50 ohm AT THE CONNECTOR.
    # =====================================================================
    # J201 pin map from parts/C22418168.json: pins 1-4 are the four square
    # ground lands (connector body / shield), pin 5 is the centre RF contact.
    _add(sh, "J201", S_SMA, V_SMA, (114.3, 88.9), footprint=F_SMA,
         expect={str(n): str(n) for n in range(1, 6)},
         note="Drive in, 20 MHz unipolar 0/+5V. DC-COUPLED - no series cap")
    sh.wire_pins("J201", {"1": GND, "2": GND, "3": GND, "4": GND, "5": DRIVE})

    # 2 x 100 R in parallel = 50 ohm. The UNIPOLAR 0/+5 V drive this design
    # mandates puts 0.250 W into the termination, not the 0.125 W the 0805
    # was sized for (P4 review E6) - hence 2010, 750 mW, 25.8% used after
    # derating to 100 C. See the module docstring.
    for ref, x in (("R201", 203.2), ("R202", 266.7)):
        _add(sh, ref, S_R100, V_R100, (x, 88.9), footprint=F_R2010,
             expect={"1": "1", "2": "2"},
             note="50R termination = R201||R202 at the connector. 0.125W each "
                  "of 0.25W total (unipolar 0/+5V, 50% duty); 2010 750mW")
        sh.wire_pins(ref, {"1": DRIVE, "2": GND})

    # =====================================================================
    # B4 - gate driver
    # =====================================================================
    # FB201 FIRST: the driver's VDD ball hangs off +5V_DRV, not +5V (W4).
    _add(sh, "FB201", S_FB, V_FB, (25.4, 127.0), footprint=F_L0805,
         expect={"1": "1", "2": "2"},
         note="W4 series filter: +5V -> +5V_DRV. 30mohm DCR = 3mV at 100mA, "
              "chosen for DCR not peak Z (E3 rail floor has ~85mV of margin)")
    sh.wire_pins("FB201", {"1": V5, "2": V5D})

    # All three bypass caps are recorded as decoupling ASSOCIATIONS on VDD:
    # the rail is the global bare "+5V_DRV", so no rail_net override is
    # needed. max_loop_nh 0.3 is constraints.json's VDD-loop budget (a
    # DIFFERENT and tighter path than the GATE loop - one is
    # inductance-limited with no series resistor, the other resistance-limited
    # by R_G). The bead sits UPSTREAM of all three: they are the pi filter's
    # load-side capacitance and must stay at the ball.
    sh.place_ic_with_decoupling(
        "U201", S_U201, V_U201, at=(114.3, 177.8), pins=U201_PINS,
        footprint=F_U201,
        expect={"A1": "VDD", "A2": "OUTH", "B1": "GND", "B2": "OUTL",
                "C1": "IN+", "C2": "IN-"},
        decoupling=[
            {"cap": "C201", "pin": "A1", "rail": V5D, "value": V_C100N,
             "lib_id": S_C100N_0402, "footprint": F_C0402,
             "max_dist_mm": 0.5, "max_loop_nh": 0.3},
            {"cap": "C202", "pin": "A1", "rail": V5D, "value": V_C10N_0201,
             "lib_id": S_C10N_0201, "footprint": F_C0201,
             "max_dist_mm": 0.5, "max_loop_nh": 0.3},
            # TI s9 / s10.1.2: an ADDITIONAL 1 uF as close as practical.
            {"cap": "C213", "pin": "A1", "rail": V5D, "value": V_C1U,
             "lib_id": S_C1U_0603, "footprint": F_C0603, "max_dist_mm": 3.0},
        ],
        caps_at=(266.7, 177.8), caps_dx=63.5)
    # place_ic_with_decoupling takes no `fields`, so these four would ship
    # with no LCSC instance property and fall out of P9's BOM (review E5).
    genlib.stamp_lcsc(sh, LCSC, ["U201", "C201", "C202", "C213"])

    # Four legs, ONE 4R7 0805 each -> 2.35 ohm at each driver pin (E1).
    for i, (ref, src, dst) in enumerate(GATE_LEGS):
        x = 88.9 + i * 63.5
        _add(sh, ref, S_R4R7, V_R4R7, (x, 241.3), footprint=F_R0805,
             expect={"1": "1", "2": "2"},
             note="gate leg %s -> %s. 4R7 per branch; the TWO branches on "
                  "each pin give 2.35R >= TI's 2R floor" % (src, dst))
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
        "NO steering diode is needed or wanted.",
        "TI'S >=2 OHM MANDATE IS AT THE PIN, AND",
        "TWO FETs SHARE EACH PIN, so each branch",
        "must be >= 2 x 2 = 4 ohm. ONE 4R7 0805 per",
        "leg per FET -> 4.7/2 = 2.35R at OUTH and at",
        "OUTL (2.33R at -1%), peak drive 2.13 A.",
        "Do NOT parallel these back down.",
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
        "GATE LOOPS: aim for <= 0.48 nH per FET,",
        "matched +/-0.1 nH, geometrically MIRRORED",
        "about the U201 axis. The CRITICAL-DAMPING",
        "budget is now 1.70 nH (EPC WP008 Eq.1 at",
        "R = 4.7 + 0.4 + 0.75 = 5.85 ohm, C_GS 199",
        "pF) - 3.6x looser than the 0.48 nH solved",
        "at the old 3.1 ohm, which is what pays for",
        "the 0805 bodies. Keep aiming at 0.48 nH.",
        "Do NOT length-match electrically - FR4 is",
        "6.7 ps/mm and skew is benign in a soft-",
        "switched topology; matching damps the",
        "differential mode and equalises sharing.",
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
        "FB201 IS A FILTER, NOT PROTECTION.",
    ])
    _note(sh, (469.9, 396.24), [
        "+5V IS SPLIT AT FB201: +5V (buck) feeds the",
        "bead, +5V_DRV feeds U201.A1 and C201/C202/",
        "C213 only. That containment is the point -",
        "the 72-100 mA of gate charge at 20 MHz must",
        "return inside the local 1.1 uF, not across",
        "the board to C108. P6: bead and all three",
        "caps stay on the DRIVER side, at the ball.",
        "+5V_DRV carries its OWN PWR_FLAG here; that",
        "is not a duplicate of hk's - different net.",
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
        "rails_flagged": [V5D],
        "gate_r_per_branch_ohm": 4.7,
        "gate_r_per_driver_pin_ohm": 2.35,
        "dnp": sorted(r for r, d in CSHUNT_SITES if d),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
