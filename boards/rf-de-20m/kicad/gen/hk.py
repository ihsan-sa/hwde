"""rf-de-20m `hk` sheet (blocks.md B1 + B2): 40 V bus entry, bulk, and the
+5 V housekeeping buck.

Refdes range 100-199, `#PWR`/`#FLG` base 100 (architecture/sheets.md s2).
THIS SHEET OWNS ALL THREE PWR_FLAGs (GND, +40V, +5V) - see below.

Rebuild (writes <out>/hk.kicad_sch; the ROOT generator owns the project):
    .venv/Scripts/python boards/rf-de-20m/kicad/gen/hk.py [OUT_DIR]

GROUND TRUTH
------------
architecture/sheets.md s1/s2, architecture/blocks.md B1/B2,
architecture/constraints.json, parts/parts.json, parts/C34355.json
(LM5017 datasheet extract) and the LM5017 datasheet itself
(parts/C34355.pdf, SNVS783H) sections 7.3.1 / 7.3.9 / 7.3.11 / 8.2.1.2,
plus the library pin tables printed by
`schlib.py --pins "aiee:<SYMBOL>" --lib lib/aiee.kicad_sym`.

THE ONE REAL DESIGN ADDITION AT P4: TYPE 3 RIPPLE INJECTION
------------------------------------------------------------
The LM5017 is a constant-on-time (COT) regulator. Its off-time ends when FB
falls back through the 1.225 V reference, so **FB must carry at least 25 mV
of IN-PHASE (resistive) ripple that decreases monotonically during the
off-time** (datasheet s7.3.1 and s7.3.11). C108 is a 22 uF X7R ceramic with
milliohms of ESR: the ripple it produces is CAPACITIVE, 90 degrees out of
phase, and does not satisfy the condition. Left as P3 shipped it (R101/R102
divider + C105-C109 and nothing else) this regulator multi-pulses and bursts.

Datasheet Table 1 offers three fixes. **Type 3 is chosen** - "minimum ripple
configuration" - because it synthesises the ramp from the SW node instead of
from the output, so the +5 V rail keeps its low ripple. That matters here:
+5 V feeds a 7 A gate driver whose VDD abs max is 5.75 V, and Type 1/Type 2
both work by deliberately putting resistive ripple ON the output.

Topology, read off the datasheet's own Table 1 / Type 3 cell (p.12) rather
than from memory - note Cr returns to VOUT, NOT to ground:

      /hk/BUCK_SW --[ R104 Rr 100k ]--+--[ C110 Cr 1nF ]-- +5V
                                      |
                                      +--[ C111 Cac 100nF ]-- /hk/FB

During the on-time SW sits at VIN and the Rr/Cr node sits at VOUT, so Cr
integrates (VIN - VOUT) into a triangular ramp; Cac ac-couples it into FB
without disturbing the divider's DC bias.

Sizing, against datasheet Equation 7  `Rr.Cr <= (VIN(MIN) - VOUT).TON / 25mV`:

C106 IS 2.2 uF 50 V, NOT 1 uF 16 V (P4 review W3)
---------------------------------------------------
The datasheet asks for 1.0 uF of REAL capacitance on VCC, and VCC regulates
to 7.6 V typ (up to 8.55 V over temperature). A 1 uF 16 V X7R 0603 sits at
48-53 % of its rated bias there and loses 35-50 % of its value, landing at
0.5-0.65 uF - and that same cap sources the internal-diode recharge of the
bootstrap cap every cycle, so the shortfall compounds C107. The replacement
is 2.2 uF 50 V X7R in 0805 (C125847): 8.55 V is 17 % of rating, where an
0805 X7R loses ~15-25 %, so >= 1.65 uF effective - comfortably over the 1 uF
requirement instead of half of it. VCC's ~26 mA internal current limit
charges 2.2 uF to 7.6 V in ~0.6 ms, so startup is unaffected; the datasheet
sets no upper bound on CVCC.

    fSW   = VOUT/(K.RON) = 5.06/(9e-11 x 100k)          = 562 kHz
    TON   = K.RON/VIN    = 9e-6/40                      = 225 ns  (>= 100 ns floor)
    TOFF  = (1-D)/fSW    = 0.8735/562k                  = 1.55 us (>= 144 ns floor)
    Rr.Cr = 100k x 1nF                                  = 1.0e-4
    limit at the worst bus corner (VIN 34 V, TON 265 ns) = 3.06e-4
        -> 3.1x inside the limit, and TI explicitly says to pick a value
           SMALLER than the calculated one to absorb TON/COUT spread.
    FB ripple = (VIN-VOUT).TON/(Rr.Cr) = 78.6 mV pk-pk at 40 V, 76.8 mV at
        34 V -> ~3x the 25 mV floor across the whole documented bus range.

All three ripple parts are values ALREADY on this board's BOM (Rr = the RON
part, Cr = the C211/C212 part, Cac = the C105/C109 part), so the network
costs three placements and ZERO new BOM lines.

TWO OTHER P3 PLACEHOLDERS RESOLVED HERE (parts.json asked P4 to size them)
--------------------------------------------------------------------------
  * **R103 (RON) = 100 k stands, but the PACKAGE moved 0402 -> 0805.**
    (P4 review W2.) RON sits from the RON pin - held near ground by the
    on-timer - to +40V, so the FULL bus stands across one chip resistor
    continuously. A thick-film 0402's maximum WORKING voltage is 50 V, so
    40 V DC is 80 % of it with nothing left for the ~51 V LC turn-on
    overshoot P1 predicted on this bus, which exceeds it outright. The 0805
    part is rated 150 V: 3.8x on the 40 V steady state, 2.9x on the 51 V
    ring. Power was never the issue (16 mW). R104 (Rr) MOVED TOO, for the
    same reason and it is not a free-lunch extension: Rr spans BUCK_SW to
    RINJ, so it stands off VIN - VOUT = 35 V normally and ~46 V on the same
    turn-on ring, i.e. 92 % of an 0402's working voltage. Moving both onto
    one 0805 part also DELETES a BOM line (the 100 k 0402 disappears).
  * **L101 = 22 uH stands** (sheets.md's 15-47 uH window). Ripple is
    dI = (VIN-VOUT).TON/L = 357 mA pk-pk, so the peak inductor current at the
    declared 0.3 A rail budget is 479 mA against the 700 mA MINIMUM current
    limit - 1.46x. The ripple is large relative to the load (the real load is
    99 mA average), but the LM5017 has NO diode emulation and stays in CCM at
    any load by design (s7.3.8), and for a COT part ripple is signal.
  * **C107 (bootstrap) CHANGED 2.2 nF -> 10 nF.** parts.json flagged its own
    2.2 nF as a placeholder; the datasheet is explicit (s8.2.1.2.6 "A good
    value for CBST = 0.01 uF", and the pin table repeats it). The 10 nF
    100 V X7R 0603 already on the BOM for C207-C210 is used, so this is a
    quantity bump, not a new line. BST-to-SW abs max is 13 V.
  * **R101/R102 = 30.9k/10.0k, BOTH 1 %** (was 30.0k 5 % / 10.0k 1 %).
    P4 review E3, and the one place where this generator does NOT do exactly
    what the reviewer asked - see the next block for why.

THE +5 V DIVIDER: TWO MODELS, ONE DIVIDER THAT SATISFIES BOTH (E3)
-------------------------------------------------------------------
The defect is real and is fixed: **R101 was a 5 % part** (LCSC C25553 =
`0402WG*J*0303TCE`; the J code is +/-5 %) while R102/R103/R104 were all 1 %.
The top leg is the dominant term, so a 5 % top leg alone drags the rail's low
corner under the LMG1020's 4.75 V minimum. R101 is now `0402WGF3092TCE`
(C270615) - same Uniroyal family as R102, F = +/-1 %, 30.9 k.

The reviewer and this sheet disagree about where the rail actually SITS, and
the divider below is chosen to be in-spec under BOTH readings rather than to
pick a winner:

  * VALLEY model (the review's table): a COT part regulates the FB valley to
    VREF, so VOUT = VREF x N with N = 1 + R101/R102. Injected ripple is
    treated as not shifting DC.
  * RAMP model (this generator's, since P4): the Type 3 ramp is AC-coupled
    into FB through C111, so its mean is zero and the VALLEY of FB is
    VOUT/N - Vramp/2. Setting that equal to VREF gives
    **VOUT = N x (VREF + Vramp/2)**, i.e. the injected ripple RAISES the DC
    output by half its amplitude, referred through the divider.

The ramp model is the one the physics supports (C111 is 100 nF into a 7.5 k
Thevenin divider - tau 750 us against a 1.8 us period, so DC is blocked and
the mean really is zero) and it is why this sheet has always quoted 5.06 V
rather than 4.90 V. But the difference is only 3.2 % of VREF, the ramp
amplitude itself carries Rr/Cr/K tolerance, and being wrong in the high
direction costs VGS headroom on a $3.93 GaN part. So the divider is solved
against the UNION of both: effective reference in [1.200 V, 1.296 V], where
1.200 is VFB(min) with no ramp offset and 1.296 is VFB(max) + the largest
credible Vramp/2 (46 mV: 40 V bus, Cr -5 %, Rr/RON ratio +2 %, K spread).

    N nominal = 1 + 30.9/10.0 = 4.090      (N_min 4.0288, N_max 4.1524 at 1%)

    rail low  corner  1.200 x 4.0288 = 4.835 V   >= 4.75 V  (+85 mV)
    rail high corner  1.296 x 4.1524 = 5.381 V   <= 5.40 V  (-19 mV)
    valley-model nominal 1.225 x 4.09 = 5.010 V
    ramp-model   nominal 1.264 x 4.09 = 5.171 V   -> "~5.05 V" re-centred

    LMG1020 VDD recommended 4.75-5.40 V     both corners inside
    LMG1020 VDD abs max     5.75 V          0.37 V of margin at the high corner
    LMG1020 IN+ abs max     VDD + 0.3 V     = 5.135 V at the LOW corner, vs a
                                              5.0 V drive -> +135 mV (was
                                              -114 mV, i.e. a violation)
    EPC2019 VGS abs max     +6.0 V          0.62 V of margin at the high corner
    LM5017 FB OVP           1.62 V          FB peak = VFB + Vramp = 1.34 V max

For the record, why not a bigger re-centre: the reviewer's suggested 31.6k
gives N = 4.16, which is fine under the valley model but pushes the ramp
model's high corner to ~5.46 V, outside the LMG1020's recommended range.
E96 ratios quantise to ~3.01 or ~3.09 here (ratios of E96 values are
themselves E96 values), and 3.01 fails the low corner by 10 mV, so 30.9k/10k
is the only two-resistor E96 divider that clears both models.
    A note on the -19 mV of high-corner margin: it is a TRIPLE worst case
    (VFB max AND every ramp tolerance stacked high AND both resistors at
    their 1 % extremes in the same direction), and 5.40 V is a RECOMMENDED
    operating limit, not an absolute maximum - 5.75 V is, and there is
    0.37 V to that.

UVLO
----
Pin 3 is tied DIRECTLY TO +40V. Datasheet s7.3.9: "If the UVLO pin is
connected directly to the VIN pin, the regulator will begin operation once
the VCC undervoltage is satisfied." No bus-undervoltage threshold is
specified anywhere in the architecture and P3 sourced no divider, so a
divider would be an invented requirement. Abs max on UVLO is 100 V.

NET NAMING (sheets.md s1 - BINDING)
------------------------------------
* `GND` / `+40V` / `+5V` are POWER SYMBOLS -> global and BARE. `power:+40V`
  does not exist in the stock library, so `power:+48V` is placed and schlib
  re-VALUEs it to "+40V" - a power symbol's exported net name is its VALUE
  field (LEARNINGS 2026-07-28 [kicad]).
* Six nets are sheet-internal and come out `/hk/<NAME>`: VCC, BST, BUCK_SW,
  FB, RON, RINJ. No constraint references any of them.
* **The buck's switch node is called BUCK_SW, not SW.** `/SW` is the RF drain
  node on `stage`/`tank` and is named in six constraints.json entries; a
  second net called SW anywhere would be a different net with a colliding
  intent, and if it ever crossed the root it would merge with the drain.

WHO OWNS THE PWR_FLAGS
----------------------
All three rails are flagged HERE and nowhere else. +40V and GND enter through
J101, whose pins are `passive`; +5V is produced by L101, also passive. Every
stock power symbol contributes a `power_in` pin, and the LM5017's RTN/VIN and
the LMG1020's GND/VDD are `power_in` too, so without a flag each rail raises
`pin_not_driven`. A SECOND flag on another sheet is not harmless - PWR_FLAG's
pin is `power_out` and two collide as `power_out <-> power_out`. `stage` and
`tank` place consuming symbols only (flag=False).

NOT ON THIS SHEET
-----------------
No TVS, no fuse, no NTC, no reverse-polarity FET, no inrush limiter. Owner
acknowledged at P0 Q11 (blocks.md s5); the response to a reviewer is
"waived, owner-acknowledged at P0". The ~51 V turn-on ring is handled by
component VOLTAGE RATING (every +40V part is >= 63 V) and by MORE bulk, not
by a clamp - blocks.md B1 is explicit that shrinking the bulk makes the
overshoot worse.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]          # boards/rf-de-20m
REPO = BOARD.parents[1]          # repo root
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))

import schlib  # noqa: E402

import genlib  # noqa: E402

# kicad-sch-api resolves lib_ids through its GLOBAL cache, which never reads
# kicad/sym-lib-table (LEARNINGS 2026-07-28) - register the pulled library.
# Reuse the module schlib already imported under a stdout redirect; importing
# kicad_sch_api bare here would put its library-scan noise on our JSON stdout.
ksa = schlib.ksa
ksa.get_symbol_cache().add_library_path(str(BOARD / "lib" / "aiee.kicad_sym"))

# --------------------------------------------------------------------- nets
GND = "GND"
V40 = "+40V"
V5 = "+5V"
VCC = "VCC"            # -> /hk/VCC   LM5017 internal 7.6 V linear reg output
BST = "BST"            # -> /hk/BST   bootstrap, floats on BUCK_SW
BUCK_SW = "BUCK_SW"    # -> /hk/BUCK_SW   NOT "SW" - see module docstring
FB = "FB"              # -> /hk/FB
RON = "RON"            # -> /hk/RON
RINJ = "RINJ"          # -> /hk/RINJ  Type 3 ripple-injection ramp node

# ------------------------------------------------------------------ symbols
S_J101 = "aiee:KF128-5.08-2P"            # default Reference "U" -> J101
S_CBULK = "aiee:RVT63V100M10X10"         # 100uF 63V alu electrolytic, POLARIZED
S_C2U2_100V = "aiee:CC1206KKX7R0BB225"   # 2.2uF 100V X7R 1206 (ref "U")
S_U101 = "aiee:LM5017MRX_NOPB"
S_L101 = "aiee:SWPA4030S220MT"
S_C100N_100V = "aiee:CC0603KRX7R0BB104"  # 100nF 100V X7R 0603
S_C2U2_50V = "aiee:CC0805KKX7R9BB225"    # 2.2uF 50V X7R 0805 (VCC, W3)
S_C10N_100V = "aiee:CC0603KRX7R0BB103"   # 10nF 100V X7R 0603
S_C22U_16V = "aiee:TCC1206X7R226K160HT"  # 22uF 16V X7R 1206
S_C1N_100V = "aiee:CC0603JRNPO0BN102"    # 1nF 100V C0G 0603
S_R30K9 = "aiee:0402WGF3092TCE"          # 30.9k 0402 1% (E3)
S_R10K = "aiee:0402WGF1002TCE"
S_R100K = "aiee:0805W8F1003T5E_C149504"  # 100k 0805 1%, 150V working (W2)

# --------------------------------------------------------------- footprints
F_J101 = "aiee:CONN-TH_P5.08_KF128-5.08-2P"
F_CBULK = "aiee:CAP-SMD_BD10.0-L10.3-W10.3-LS11.0-FD_1"
F_C1206 = "aiee:C1206"
F_C0805 = "aiee:C0805"
F_C0603 = "aiee:C0603"
F_R0805 = "aiee:R0805"
F_R0402 = "aiee:R0402"
F_U101 = "aiee:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL-EP2.0"
F_L101 = "aiee:IND-SMD_L4.0-W4.0_SLW4010S"

# ------------------------------------------------------------------- values
V_J101 = "KF128-5.08-2P 2pos 5.08mm 24A/250V"
V_CBULK = "100uF 63V alu electrolytic"
V_C2U2 = "2.2uF 100V X7R 1206"
V_U101 = "LM5017 100V sync COT buck"
V_L101 = "22uH 1A shielded"
V_C100N = "100nF 100V X7R 0603"
V_C2U2_VCC = "2.2uF 50V X7R 0805"
V_C10N = "10nF 100V X7R 0603"
V_C22U = "22uF 16V X7R 1206"
V_C1N = "1nF 100V C0G 0603"
V_R30K9 = "30.9k 0402 1%"
V_R10K = "10.0k 0402 1%"
V_R100K = "100k 0805 1% 150V"

# LCSC codes from parts/parts.json. Stamped on every purchased component:
# KiCad 10 DRC raises footprint_symbol_field_mismatch without them, and P9's
# bom_cpl reads the board's per-footprint LCSC field as its primary source.
LCSC = {
    "J101": "C474952",
    "U101": "C34355",           # placed by place_ic_with_decoupling - stamped
    "C101": "C51953411", "C102": "C51953411",
    "C103": "C577211", "C104": "C577211",
    "U101": "C34355",
    "L101": "C83472",
    "C105": "C113803", "C109": "C113803", "C111": "C113803",
    "C106": "C125847",          # W3: 1uF 16V -> 2.2uF 50V (DC-bias derating)
    "C107": "C107059",          # CHANGED from the 2.2nF placeholder - see docstring
    "C108": "C22392398",
    "C110": "C113793",
    "R101": "C270615",          # E3: was C25553, a 5% part
    "R102": "C25744",
    "R103": "C149504", "R104": "C149504",   # W2: 0402 -> 0805 (working voltage)
}

# LM5017 pin map. Numbers/names from parts/C34355.json, cross-checked against
# the library pin table (`--pins aiee:LM5017MRX_NOPB`): 1 RTN / 2 VIN /
# 3 UVLO / 4 RON / 5 FB / 6 VCC / 7 BST / 8 SW / 9 PAD.
U101_PINS = {
    "1": GND,        # RTN - ground, and the EP must tie here
    "2": V40,        # VIN - 40 V bus, abs max 100 V
    "3": V40,        # UVLO tied to VIN (s7.3.9) - see docstring
    "4": RON,        # on-time programming resistor -> R103 -> +40V
    "5": FB,         # 1.225 V regulation comparator input
    "6": VCC,        # internal 7.6 V linear regulator output
    "7": BST,        # bootstrap, referenced to SW
    "8": BUCK_SW,    # switch node
    "9": GND,        # exposed pad -> RTN / system ground (extract: connect_to RTN)
}

RAILS = [
    (GND, "power:GND", (25.4, 25.4)),
    # power:+40V does not exist in the stock library; any power symbol works
    # because the exported net name is the symbol's VALUE, which schlib sets
    # to the net (LEARNINGS 2026-07-28 [kicad]).
    (V40, "power:+48V", (25.4, 40.64)),
    (V5, "power:+5V", (25.4, 55.88)),
]


def _add(sh, ref, lib_id, value, at, footprint=None, expect=None, note=None,
         rotation=0):
    """add_component + this board's identity fields."""
    fields = {}
    code = LCSC.get(ref)
    if code:
        fields["LCSC"] = code
    if note:
        fields["Note"] = note
    return sh.add_component(lib_id, ref, value, at, rotation=rotation,
                            footprint=footprint, fields=fields or None,
                            expect=expect)


def _note(sh, at, lines, dy=5.08):
    """A block of sheet text, ONE add_text per line (an embedded newline in a
    quoted s-expression is not a form kicad-sch-api round-trips reliably)."""
    x, y = at
    for i, line in enumerate(lines):
        sh.sch.add_text(line, position=(x, round(y + i * dy, 4)))


def build() -> schlib.Sheet:
    sh = schlib.Sheet("hk",
                      title="rf-de-20m: hk - 40 V bus entry, bulk, +5 V buck",
                      paper="A2", date="2026-08-07", company="ai-ee",
                      pwr_base=100)

    # =====================================================================
    # Rails - the ONLY PWR_FLAGs on this board
    # =====================================================================
    for net, sym, at in RAILS:
        sh.power_flag(net, at=at, sym=sym, flag=True)

    # =====================================================================
    # B1 - DC bus entry and bulk
    # =====================================================================
    # J101 is the only THT part on the board (parts.json: pre-approved
    # exception). Pin 1 = +40V, pin 2 = GND; P6 silkscreens the polarity AND
    # the bus RANGE "40 V max, 34-40 V" (sheets.md s6 note 9 - a 36 V bench
    # setting is a valid derated operating point, not a fault).
    _add(sh, "J101", S_J101, V_J101, (88.9, 88.9), footprint=F_J101,
         expect={"1": "1", "2": "2"},
         note="THT, left edge x<5mm, clear of the heatsink land (HS-3)")
    sh.wire_pins("J101", {"1": V40, "2": GND})

    # C101/C102 - 100 uF 63 V ALUMINIUM ELECTROLYTIC (parts.json re-sourced
    # the unpullable polymer part). POLARIZED: the symbol draws its "+" beside
    # pin 1 and its curved (cathode) plate at pin 2, so pin 1 is the anode -
    # CONFIRMED 2026-08-08 against the JIERR RVT-series drawing now committed
    # at parts/C51953411.pdf (p.2 labels the chamfered-corner terminal
    # "Positive"; the footprint's chamfers are on the pad-1 side). P4 review
    # E2 closed. The missing SILK mark is still a P6 obligation.
    # Every +40V part is >=63 V because a live bench supply into 220 uF through
    # ~1 uH of cable inductance rings the bus to ~51 V (blocks.md B1). The
    # high ESR of an electrolytic is acceptable and is checked, not assumed:
    # this cap is DC hold-up only. L201 (0.94 uH, |Z| 118 ohm at 20 MHz)
    # isolates the bus from the RF loop and the HF bank (C207-C212, |Z| 0.19
    # ohm at 20 MHz) shunts what gets through, so essentially no 20 MHz ripple
    # current reaches here - and the ESR actively DAMPS the turn-on ring.
    for ref, x in (("C101", 190.5), ("C102", 254.0)):
        _add(sh, ref, S_CBULK, V_CBULK, (x, 88.9), footprint=F_CBULK,
             expect={"1": "1", "2": "2"},
             note="POLARIZED - pin 1 = +. Footprint carries NO silk polarity "
                  "mark; P6 must add one")
        sh.wire_pins(ref, {"1": V40, "2": GND})

    # C103/C104 - mid-frequency tier, 100 kHz-5 MHz. X7R is correct HERE and
    # nowhere else on this board (blocks.md B1); its DC-bias derating costs
    # only capacitance because this tier sets no resonance. 1206 not 0805:
    # P3 substituted the package for stock, and zone A has the room.
    for ref, x in (("C103", 317.5), ("C104", 381.0)):
        _add(sh, ref, S_C2U2_100V, V_C2U2, (x, 88.9), footprint=F_C1206,
             expect={"1": "1", "2": "2"})
        sh.wire_pins(ref, {"1": V40, "2": GND})

    # =====================================================================
    # B2 - the +5 V buck
    # =====================================================================
    # C105 (VIN local bypass) and C106 (VCC decoupler) are the two entries the
    # datasheet's own decoupling table names for a pin, so they are the two
    # recorded as S4 decoupling ASSOCIATIONS. C107 is a BOOTSTRAP cap - it
    # spans BST to SW, not a rail to ground - and is wired plainly below;
    # recording it as "decoupling" would put a false rail/gnd pair into
    # check_decoupling.
    sh.place_ic_with_decoupling(
        "U101", S_U101, V_U101, at=(152.4, 190.5), pins=U101_PINS,
        footprint=F_U101,
        expect={"1": "RTN", "2": "VIN", "3": "UVLO", "4": "RON", "5": "FB",
                "6": "VCC", "7": "BST", "8": "SW", "9": "PAD"},
        decoupling=[
            # Datasheet Layout Guideline 1: 0.1-0.47 uF directly across
            # VIN/RTN with minimised loop area, 100 V X7R.
            {"cap": "C105", "pin": "2", "rail": V40, "value": V_C100N,
             "lib_id": S_C100N_100V, "footprint": F_C0603, "max_dist_mm": 3.0},
            # Guideline 2 / s8.2.1.2.6: CVCC = 1 uF, as close as possible.
            # The wiring label is "VCC" but the FINAL netlist name is
            # /hk/VCC (sheet-internal), so rail_net carries the real name -
            # netlist_audit --decoupling checks exactly this.
            # 2.2 uF 50 V 0805, NOT 1 uF 16 V: at VCC's 7.6-8.55 V the 16 V
            # part derates to 0.5-0.65 uF against a 1.0 uF requirement (W3).
            {"cap": "C106", "pin": "6", "rail": VCC, "rail_net": "/hk/VCC",
             "value": V_C2U2_VCC, "lib_id": S_C2U2_50V, "footprint": F_C0805,
             "max_dist_mm": 3.0},
        ],
        caps_at=(304.8, 190.5), caps_dx=63.5)
    # place_ic_with_decoupling takes no `fields`, so these three would ship
    # with no LCSC instance property and fall out of P9's BOM (review E5).
    genlib.stamp_lcsc(sh, LCSC, ["U101", "C105", "C106"])

    # Rails become global on THIS sheet through the flagged clusters above;
    # the IC pins already carry the rail labels, so no extra symbol is needed.

    # L101 - buck inductor, BUCK_SW -> +5V. 22 uH: see docstring.
    _add(sh, "L101", S_L101, V_L101, (152.4, 279.4), footprint=F_L101,
         expect={"1": "1", "2": "2"})
    sh.wire_pins("L101", {"1": BUCK_SW, "2": V5})

    # C107 - BOOTSTRAP, BST to SW. 10 nF per datasheet s8.2.1.2.6 (P3's
    # 2.2 nF was explicitly a placeholder). Must withstand BST-to-SW abs max
    # 13 V; the 100 V part is 7.7x that.
    _add(sh, "C107", S_C10N_100V, V_C10N, (228.6, 279.4), footprint=F_C0603,
         expect={"1": "1", "2": "2"},
         note="Bootstrap BST-SW, 0.01uF per LM5017 s8.2.1.2.6")
    sh.wire_pins("C107", {"1": BST, "2": BUCK_SW})

    # Output bulk + HF on +5V. C108 is the COUT the ripple-injection network
    # exists to compensate for (its ESR is far below the 25 mV COT floor).
    _add(sh, "C108", S_C22U_16V, V_C22U, (304.8, 279.4), footprint=F_C1206,
         expect={"1": "1", "2": "2"})
    sh.wire_pins("C108", {"1": V5, "2": GND})
    _add(sh, "C109", S_C100N_100V, V_C100N, (381.0, 279.4), footprint=F_C0603,
         expect={"1": "1", "2": "2"})
    sh.wire_pins("C109", {"1": V5, "2": GND})

    # Feedback divider. BOTH LEGS 1 % (E3 - R101 was a 5 % part), ratio
    # re-centred 30.0k -> 30.9k so the rail clears the LMG1020's 4.75-5.40 V
    # window under BOTH the valley and the ramp reading (see docstring).
    _add(sh, "R101", S_R30K9, V_R30K9, (88.9, 355.6), footprint=F_R0402,
         expect={"1": "1", "2": "2"},
         note="FB divider top leg (RFB2). 1% - a 5% top leg put the rail's "
              "low corner at 4.59V, under the driver's 4.75V minimum")
    sh.wire_pins("R101", {"1": V5, "2": FB})
    _add(sh, "R102", S_R10K, V_R10K, (152.4, 355.6), footprint=F_R0402,
         expect={"1": "1", "2": "2"}, note="FB divider bottom leg (RFB1)")
    sh.wire_pins("R102", {"1": FB, "2": GND})

    # RON sets the on-time and therefore fSW. The datasheet puts this resistor
    # from the RON pin TO VIN (s5 pin table) - not to ground - because the
    # on-time is programmed as a function of VIN. 0805, NOT 0402: the whole
    # bus stands across it continuously and an 0402 tops out at 50 V (W2).
    _add(sh, "R103", S_R100K, V_R100K, (215.9, 355.6), footprint=F_R0805,
         expect={"1": "1", "2": "2"},
         note="RON to VIN - fSW = VOUT/(K.RON) = 562 kHz. 0805/150V: 40V "
              "continuous, ~51V on the turn-on ring")
    sh.wire_pins("R103", {"1": RON, "2": V40})

    # ---------------- Type 3 ripple injection (datasheet Table 1) ----------
    # SW --Rr-- RINJ --Cr-- VOUT, and RINJ --Cac-- FB. Cr returns to the
    # OUTPUT, not to ground: that is what the datasheet figure shows and what
    # makes the ramp equal to (VIN - VOUT).TON/(Rr.Cr).
    _add(sh, "R104", S_R100K, V_R100K, (279.4, 355.6), footprint=F_R0805,
         expect={"1": "1", "2": "2"},
         note="Rr - Type 3 ripple injection (LM5017 s7.3.11). 0805/150V: it "
              "stands off VIN-VOUT = 35V, ~46V on the turn-on ring")
    sh.wire_pins("R104", {"1": BUCK_SW, "2": RINJ})
    _add(sh, "C110", S_C1N_100V, V_C1N, (342.9, 355.6), footprint=F_C0603,
         expect={"1": "1", "2": "2"}, note="Cr - ramp integrator, returns to VOUT")
    sh.wire_pins("C110", {"1": RINJ, "2": V5})
    _add(sh, "C111", S_C100N_100V, V_C100N, (406.4, 355.6), footprint=F_C0603,
         expect={"1": "1", "2": "2"}, note="Cac - ac couples the ramp into FB")
    sh.wire_pins("C111", {"1": RINJ, "2": FB})

    # =====================================================================
    # sheet notes
    # =====================================================================
    _note(sh, (444.5, 63.5), [
        "THIS SHEET OWNS THE PWR_FLAGS for GND,",
        "+40V and +5V. Every rail enters through",
        "passive pins (J101) or a passive inductor",
        "(L101). Do NOT add a second flag on another",
        "sheet: PWR_FLAG is a power_out pin and two",
        "of them collide as power_out <-> power_out.",
    ])
    _note(sh, (444.5, 106.68), [
        "TYPE 3 RIPPLE INJECTION IS MANDATORY, NOT",
        "OPTIONAL. LM5017 is a COT regulator and",
        "needs >=25 mV of IN-PHASE ripple at FB",
        "(s7.3.1/s7.3.11). A 22 uF ceramic COUT gives",
        "almost none, and the regulator multi-pulses.",
        "R104/C110/C111 synthesise the ramp from the",
        "SW node so the +5 V rail keeps low ripple -",
        "which matters, because +5V feeds a driver",
        "whose VDD abs max is 5.75 V.",
        "FB ripple 78.6 mV pk-pk at 40 V bus (3.1x",
        "the floor); Rr.Cr is 3.1x inside Eq 7.",
    ])
    _note(sh, (444.5, 172.72), [
        "THE BUCK SWITCH NODE IS /hk/BUCK_SW.",
        "It is NOT called SW: /SW is the RF drain",
        "node and is named in six constraints.json",
        "entries.",
    ])
    _note(sh, (444.5, 200.66), [
        "UVLO (pin 3) IS TIED TO VIN. Datasheet",
        "s7.3.9 sanctions it explicitly; no bus-",
        "undervoltage threshold is specified anywhere",
        "in the architecture, so a divider would be",
        "an invented requirement. Abs max 100 V.",
    ])
    _note(sh, (444.5, 233.68), [
        "C101/C102 ARE POLARIZED: pin 1 = ANODE (+).",
        "SETTLED 2026-08-08 against the manufacturer",
        "drawing (JIERR RVT series, parts/C51953411",
        ".pdf p.2): the 'Positive' leader points at",
        "the CHAMFERED-corner end of the base, and",
        "the footprint's two chamfers are on the",
        "pad-1 side. The symbol's '+' at pin 1 is",
        "therefore CORRECT. (The usual 'cut corner =",
        "cathode' rule does NOT hold on this family;",
        "the can's black top stripe sits on the",
        "SQUARE-cornered end. Cross-checked against",
        "Lumimax SMDGP/RVT, same conclusion.)",
        "The footprint still carries NO silk polarity",
        "marker - P6 MUST add a '+' outside the",
        "10.46 mm body square (the base hides it) and",
        "an F.Fab body outline with a marker.",
    ])
    _note(sh, (444.5, 271.78), [
        "NO PROTECTION PARTS ON THIS BOARD.",
        "No TVS, fuse, NTC, OVP, OCP or thermal",
        "shutdown. Owner-acknowledged at P0 Q11.",
        "The ~51 V turn-on ring is handled by",
        "VOLTAGE RATING (every +40V part >=63 V)",
        "and by MORE bulk - shrinking the bulk makes",
        "the overshoot WORSE (blocks.md B1).",
    ])
    return sh


def main(argv=None) -> int:
    # project=False: the ROOT generator owns <root>.kicad_pro.
    out_dir = Path(argv[0]) if argv else BOARD / "kicad"
    try:
        sh = build()
        path = sh.save(out_dir, project=False)
        hidden = genlib.hide_aux_fields(path)
    except Exception as exc:  # noqa: BLE001  (SPEC 6: any error -> exit 2)
        print(json.dumps({"script": "gen.hk", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.hk", "status": "pass",
        "sheet": str(path),
        "components": len(list(sh.sch.components)),
        "hier_pins": sorted(sh.hier_pins),
        "rails_flagged": [net for net, _, _ in RAILS],
        "internal_nets": sorted({VCC, BST, BUCK_SW, FB, RON, RINJ}),
        "decoupling_associations": len(sh.decoupling),
        "field_placement": sh.place_report,
        "aux_fields_hidden": hidden,
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
