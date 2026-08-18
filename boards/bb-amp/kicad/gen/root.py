"""bb-amp root generator - THE WHOLE SCHEMATIC (one flat root sheet).

Bridge front end: J1 -> U1 AD8226 in-amp (G1 = 39.90) -> U2B OPA2333 half
(G2 = 3.49) -> J2, on ONE 3.3 V rail, with a buffered 0.252 V pedestal
that U1's REF pin AND the stage-2 gain return BOTH sit on.

    Rebuild:  .venv\\Scripts\\python.exe boards/bb-amp/kicad/gen/root.py
    Outputs:  ../bb-amp.kicad_sch  ../bb-amp.kicad_pro  ../decoupling.json

The Python is the SOURCE; the .kicad_sch is build output.  Every pin number
below comes from the datasheet extracts `parts/C34250.json` (AD8226) and
`parts/C38732.json` (OPA2333) cross-checked against the project library's own
pin table (`schlib.py --pins aiee:<SYM> --lib lib/aiee.kicad_sym`), never from
memory.  `expect=` on both ICs is pin-name insurance.

`architecture/sheets.md` rules ONE sheet, no hierarchy: 15 parts on one signal
path plus a two-resistor reference.  A hierarchy would buy navigation at the
cost of sheet pins, sheet instances and netlist names carrying sheet paths -
and would hide the one thing a reader of this board must see at a glance, that
`/VREF` is a single node touching U1 pin 6, U2A's output and the stage-2 gain
return.

=====================================================================
1.  NET CONTRACT (architecture/sheets.md s2 - BINDING, do not "tidy")
=====================================================================
BARE global nets, made bare by a POWER SYMBOL whose Value names the net (a
power symbol's exported net name is its VALUE, and the symbol WINS over a
coincident local label - LEARNINGS 2026-07-28):

    +3V3   GND

Root-sheet LOCAL labels, which KiCad exports with ONE leading slash:

    /IN_P /IN_N /RG_A /RG_B /VREF_SET /VREF /AMP1_OUT /FB2 /VOUT

*** The label TEXT written below is BARE ("IN_P", "VREF", ...).  The leading
`/` is the ROOT SHEET PATH that KiCad prepends on export.  Typing the slash
into the label instead yields the escaped net `/{slash}IN_P` - silently, with
a clean build and a clean ERC - and every constraints.json match then fails
(measured on sbuck-5v3a, LEARNINGS 2026-08-09).  Verify with the EXPORTED net
names, never by reading the schematic. ***

Two nets are named here that sheets.md's table does not list:

  /RG_A, /RG_B  the two ends of the gain resistor R1 across U1 pins 2 and 3.
      Internal to block B2, so sheets.md (which tabulates only the nets that
      LEAVE a block) never named them.  A node still needs a name.

/VOUT is exactly sheets.md s2's row - U2B's output pin straight to J2 pin 1,
one node carrying U2.7, R4.1 (the feedback tap) and J2.1.  P3's R6 briefly
split it in two; that resistor is GONE (see s5), so the split is gone with it
and the sheet is back on sheets.md's own net table with no deltas at all.

=====================================================================
2.  THE CIRCUIT, AND THE ONE WIRE THAT MUST BE RIGHT
=====================================================================
    Vout = Vref + G1*G2*Vdiff     G1*G2 = 39.90 * 3.49 = 139.2 V/V
    Vref = 3.3 * R3/(R2+R3) = 3.3 * 10.0k/131.0k = 0.2519 V

R5 RETURNS TO /VREF, NOT TO GROUND.  U2B's + input sits at
V1 = Vref + G1*Vdiff; with R5 to /VREF the output is
V1 + (V1 - Vref)*R4/R5 = Vref + G1*G2*Vdiff, so the output pedestal is
EXACTLY Vref with no matched network and no second reference node, and a
shift of Vref appears at U1 REF and at the stage-2 return with opposite sign
- reference drift and noise cancel to first order.  With R5 to GND the
pedestal becomes G2*Vref and every bit of reference error is amplified by G2.
That is a different, worse board (blocks.md s2).

U1's REF pin is DRIVEN, never grounded: with REF = 0 V the AD8226's own
guaranteed output floor (+0.10 V, Table 3) kills the bottom 2 mV of a 20 mV
span in FIRST-stage saturation, and no downstream pedestal can recover
information stage 1 already clipped (blocks.md Ruling 1).  Driving REF from a
bare divider is equally forbidden - Figure 59 crosses that exact schematic out
and marks it INCORRECT, because source impedance at REF must stay below
2 ohm.  Hence U2A, the buffer, and hence a DUAL op-amp doing both jobs.

How well the buffer holds that rule is a MEASURED, FREQUENCY-DEPENDENT
answer, not a flat one - bench B9 reads U2A's closed-loop Zout as 0.43 mohm
at DC, 0.17 ohm at 60 Hz, 2.86 ohm at 1 kHz and 116 ohm at 41 kHz, so the
2 ohm rule is met through DC and the low frequencies where the AD8226
specifies CMRR and is exceeded above about 700 Hz (350 Hz on the pessimistic
ro = 2 kohm bracket).  It does not bite on THIS board because Q1 fixes the
common mode at a STATIC 1.65 V with nothing at 1 kHz to convert, and the
residual common-mode gain error is 90.8 dB - at or above the part's own
90 dB minimum at 5 kHz.  A board with a moving common mode would have to
rederive it.  Wherever this file or the sheet says "< 2 ohm", that is the
qualified claim it means.

=====================================================================
3.  PIN HANDLING - every pin of every part is wired; there are NO no-connects
=====================================================================
U1 AD8226ARZ (parts/C34250.json):
    1 -IN  -> /IN_N      5 -VS  -> GND   (single supply: -VS IS the return)
    2 RG   -> /RG_A      6 REF  -> /VREF (buffer-driven; see s2 for the
                                          measured Zout-vs-frequency claim)
    3 RG   -> /RG_B      7 VOUT -> /AMP1_OUT
    4 +IN  -> /IN_P      8 +VS  -> +3V3  (C1 100 nF + shared C2 10 uF bulk)
  The library names pin 2 "RG/2" and pin 3 "RG"; the data sheet calls both
  RG ("place a gain resistor between these two pins").  `expect` asserts the
  substring "RG" on both so a library refresh cannot silently move them.

U2 OPA2333AIDR (parts/C38732.json) - TWO UNITS, and the units are NOT
interchangeable here:
    unit A (U2A, the /VREF buffer)      unit B (U2B, the G2 = 3.49 stage)
      1 OUT A -> /VREF                    7 OUT B -> /VOUT
      2 -IN A -> /VREF  (follower)        6 -IN B -> /FB2
      3 +IN A -> /VREF_SET                5 +IN B -> /AMP1_OUT
      4 V-    -> GND
      8 V+    -> +3V3   (C3 100 nF)
  *** V+ (8) and V- (4) live on UNIT 1 ONLY in this symbol - they are not
  duplicated on unit 2.  Unit 1 must be placed for the part to have power
  pins on the sheet at all.  Unit 1 = U2A = the buffer, which this design
  places anyway, so it works out - but it is placed deliberately, not by
  luck. ***
  See `_place_unit` for the two ksa multi-unit traps and the workaround.

Passives, by pin: R1 (1,2) across U1 pins 2-3; R2 +3V3 -> /VREF_SET; R3
/VREF_SET -> GND; C4 /VREF_SET -> GND; R4 /VOUT -> /FB2; R5 /FB2 -> /VREF;
C1/C2/C3 +3V3 -> GND.
Connectors: J1 (1 /IN_N, 2 /IN_P, 3 GND), J2 (1 /VOUT, 2 GND),
J3 (1 +3V3, 2 GND) - J2/J3 per sheets.md s2; J1's two signal poles are
DELIBERATELY the reverse of sheets.md's order, see below.

*** J1 POLE ORDER IS IN- / IN+ / GND, NOT IN+ / IN- / GND. ***
sheets.md s2 tabulated J1 pin 1 = /IN_P, pin 2 = /IN_N.  P6 found that this
forces the differential pair to CROSS: J1's poles would run (IN+, IN-) while
the AD8226's input pins run (-IN, RG, RG, +IN) - opposite orders - and the
placement agent verified the crossing survives ALL EIGHT rotation and
edge-assignment combinations of the two parts.  It is structural, not a
placement artifact.  Uncrossed, P7 pays 2 vias on ONE leg of the pair: about
0.6 pF of imbalance, -123 dB at 1 kHz - inside the declared 1 pF budget and
33 dB under the part's own 90 dB spec, so it was never a defect.  But those
vias punch the B.Cu reference directly under the input pair and put
asymmetric junctions on the one net whose symmetry is this board's dominant
error term (blocks.md s5 item 2).  Swapping the two poles makes the pair
fully planar and mirror-symmetric with ZERO vias, for the price of a legend.

Nothing electrical moves: IN+ still reaches U1 pin 4 (+IN) and IN- still
reaches U1 pin 1 (-IN), so requirements.md s2's polarity CONVENTION - "IN+
above IN- gives a positive output" - is unchanged.  Only which physical pole
carries IN+ moves, from pole 1 to pole 2.

*** CONSEQUENCE FOR THE BOARD: the J1 silk legend must read IN- / IN+ / GND
in pole order.  The board is wired by whatever the silk says. ***

J1's third pole is not a convenience: it is the input-bias-current return
path both cited data sheets require (blocks.md B1).  The 350 ohm bridge gives
each input a ~175 ohm DC path to it, so no bleeder resistors exist here.

=====================================================================
4.  DECOUPLING METADATA (three associations; C4 is deliberately NOT one)
=====================================================================
C1 -> U1 pin 8 and C3 -> U2 pin 8 are the 0.1 uF-per-supply-pin caps both
data sheets demand (AD8226 Layout/Power Supplies, printed p.21, verbatim: "A
0.1 uF capacitor should be placed as close as possible to each supply pin";
OPA2333 p15: "Place a 0.1-uF capacitor closely across the supply pins", i.e.
a SHORT LOOP from pin 8 to pin 4 - which is why C3's return is recorded).

C2 -> U1 pin 8 as the BULK member: AD8226 Figure 61's "10 uF ... farther away
from the part.  In most cases, it can be shared by other precision integrated
circuits."  Recorded once, against the part whose data sheet asks for it;
shared with U2 by that same sentence, and placed at J3 per blocks.md s5.4.
The bulk value class (>= 1 uF -> 20/30 mm) is what "farther away" means to
check_decoupling, so no per-association override is needed.

C4 is NOT an association and must never become one - it is the pedestal
divider's filter cap on the /VREF_SET node (Thevenin 9.24k -> 172 Hz corner),
not a supply-pin cap.  parts.json says the same in as many words: "do not
relocate to U2A's output" - a follower into a capacitive load peaks.

No `role: "reg_input"` anywhere: there is no switching regulator on this
board, and the role exists to force an HF member into a switch-current loop.

=====================================================================
5.  THERE IS NO OUTPUT ISOLATION RESISTOR, AND THAT IS A RESULT
=====================================================================
P3 added a 100 ohm series R6 between U2B and J2 on the reading that OPA2333
Figure 15 shows ~mid-30 % overshoot into 1 nF, which Q8 allows.  The owner has
REVERSED that decision on the P8 bench's evidence and R6 is removed here:

  - Figure 15 is a UNITY-GAIN curve.  U2B runs at noise gain 3.49.  The
    macromodel that reproduces Figure 15 exactly (32 % at 1 nF at unity gain)
    gives 6.6 % for the as-built stage with NO isolation resistor at all -
    about 63 deg of phase margin, 50 deg on the pessimistic ro = 2 kohm
    bracket.  The stage never needed one.
  - 100 ohm would not have worked anyway: an OUT-OF-LOOP isolation resistor
    has authority R6/ro, so against ro = 1-2 kohm it buys 0.3-1.3 points
    (6.60 -> 6.28 % calibrated, 17.94 -> 16.68 % pessimistic).  Real
    isolation would take 470 ohm or more, and that drops the -5 %-rail full
    scale below blocks.md B6's own 3.02 V figure.
  - At `block-only` scope, conditioning the data sheet does not require is
    EXCLUDED by the tier.  The bench has now shown it is not required.

So U2B drives J2 directly and /VOUT is one node again.  The BOM removal
landed separately and is already done: parts.json carries 10 lines / 14
refdes with no C22775 entry, checked against this netlist at build time.
What still mentions R6 is evidence and history, not design - kicad/sims/'s
b10/b11 bounds (the measurements above), the workspace LEARNINGS entry, the
P3 logs, and the now-unused 0603WAF1000T5E symbol in lib/aiee.kicad_sym.

Values are P2's and P3's and are FIXED here (sheets.md s4).  No mounting
holes: requirements.md s5 excludes mechanical at `block-only` and sheets.md
s3 makes H1-H4 conditional on an outline that does not exist until P6 earns
it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]                 # boards/<b>/kicad/gen/root.py -> repo
WORKSPACE = HERE.parents[2]            # boards/bb-amp
sys.path.insert(0, str(REPO / ".claude" / "skills" / "ai-ee" / "scripts"))
sys.path.insert(0, str(HERE.parent))

import kicad_sch_api as ksa            # noqa: E402
import schlib                          # noqa: E402

# kicad-sch-api's GLOBAL symbol cache never reads kicad/sym-lib-table, so the
# project library must be registered before any `aiee:` symbol is placed, and
# before save() re-serialises lib_symbols from that same cache
# (LEARNINGS 2026-07-28 and 2026-08-06).
PROJECT_LIB = WORKSPACE / "lib" / "aiee.kicad_sym"
ksa.get_symbol_cache().add_library_path(str(PROJECT_LIB))

# ------------------------------------------------------------------ symbols
S_U1 = "aiee:AD8226ARZ"                 # U1  in-amp, SOIC-8, single unit
S_U2 = "aiee:OPA2333AIDR"               # U2  dual op-amp, SOP-8, TWO units
S_R1K27 = "aiee:RT0603BRD071K27L"       # R1  1.27k  0.1% 25ppm
S_R121K = "aiee:RT0603BRD07121KL"       # R2  121k   0.1% 25ppm
S_R10K = "aiee:RT0603BRD0710KL"         # R3, R5  10.0k 0.1% 25ppm
S_R24K9 = "aiee:RT0603BRD0724K9L"       # R4  24.9k  0.1% 25ppm
S_C100N = "aiee:CC0603KRX7R9BB104"      # C1, C3, C4  100nF 50V X7R
S_C10U = "aiee:CL21A106KAYNNNE"         # C2  10uF 25V X5R 0805
S_J3P = "aiee:KF128-5.08-3P"            # J1
S_J2P = "aiee:KF128-5.08-2P"            # J2, J3

# --------------------------------------------------------------- footprints
F_SOIC8 = "aiee:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL"
F_SOP8 = "aiee:SOP-8_L4.9-W3.9-P1.27-LS6.0-BL"
F_R0603 = "aiee:R0603"
F_C0603 = "aiee:C0603"
F_C0805 = "aiee:C0805"
F_J3P = "aiee:CONN-TH_3P-P5.08_KF128-5.08-3P"
F_J2P = "aiee:CONN-TH_P5.08_KF128-5.08-2P"

# ref -> LCSC, straight from parts/parts.json (10 distinct codes, 14 refdes -
# an exact match; R6/C22775 is gone from both, see the module docstring s5).
# parts.json is the S6 per-DISTINCT-part shape (no `ref` keys), which
# `bom_cpl.load_parts_map` CANNOT map, so P9's only ref->LCSC source is the
# per-component `LCSC` field stamped here (bom_cpl.board_lcsc_map matches
# pname.upper() == "LCSC" only - the symbol's inherited "LCSC Part" property
# does NOT satisfy it).
LCSC = {
    "U1": "C34250",
    "U2": "C38732",
    "R1": "C861195",
    "R2": "C861095",
    "R3": "C95204", "R5": "C95204",
    "R4": "C136967",
    "C1": "C14663", "C3": "C14663", "C4": "C14663",
    "C2": "C15850",
    "J1": "C474953",
    "J2": "C474952", "J3": "C474952",
}

# Fields KiCad should keep visible on the plot; everything else is hidden
# after save (the codes and notes must EXIST - P9 reads LCSC off them - but
# kicad-sch-api gives every generator-written field VISIBLE effects, which
# prints them on top of the parts they belong to).
VISIBLE_FIELDS = {"Reference", "Value"}

# ------------------------------------------------------------------ layout
# sheets.md s2: "J1 / input pair at the far left; U1 with R1 across its RG
# pins; the reference cluster (R2, R3, C4, U2A) below U1; U2B with R4/R5 to
# the right of U1; J2 at the far right; J3 and C2 along the bottom with C1/C3
# drawn at their IC supply pins."  Rows run left-to-right along the signal
# chain so P6's placement groups read straight off the drawing.
#
# All anchors are multiples of 1.27 mm (schlib raises otherwise) and rows are
# spaced so no stub label anchor can land on a foreign wire run (schlib's
# _assert_label_clear guard; LEARNINGS 2026-07-22 [erc]).
Y_CHAIN = 76.20     # J1 -> U1 -> U2B -> J2
Y_REF = 114.30      # reference cluster: R2, R3, C4, U2A   (below U1)
Y_GAIN = 152.40     # stage-2 gain set: R4, R5             (below U2B)
Y_PWR = 190.50      # J3, C2 bulk, C1 at U1 pin 8, C3 at U2 pin 8
Y_RAIL = 228.60     # the two rail clusters (power symbol + PWR_FLAG)

X_U2 = 152.40       # both halves of U2 share this column: U2B on the chain
X_U2A = 127.00      # row, U2A in the reference cluster below U1

# U2 unit 2 is built under a temporary reference and merged onto "U2" in the
# SAVED file - see merge_unit_refs.
UNIT2_TMP_REF = "U2B"
UNIT_MERGE = {UNIT2_TMP_REF: "U2"}

# The design-equations text box (task: "this board exists to be studied").
# It grew when the P8 benches landed (the B9 Zout table, the corrected Eq.2
# rows and the B6 rail term), so it is sized from a line pitch MEASURED off
# the plotted PDF rather than guessed: KiCad renders this box at about
# 1.45 x the font size per line, so 75 lines at font 1.27 need ~140 mm.  The
# column is clear from y = 96.52 (just under the chain note) down to
# y = 252.73 (just above the title block) - 156 mm, which fits with margin.
# J2 at y = 76.2 is what stops the top edge going higher.
TEXTBOX_AT = (215.90, 96.52)
TEXTBOX_SIZE = (177.80, 156.21)
TEXTBOX_FONT = 1.27

EQUATIONS = """bb-amp - BRIDGE FRONT END ON ONE 3.3 V RAIL   (architecture/blocks.md)

TRANSFER FUNCTION
    Vout = Vref + G1*G2*Vdiff      G1*G2 = 139.2 V/V,  Vref = 0.252 V
    Vout(-1 mV) = 0.113 V     Vout(0) = 0.252 V     Vout(+20 mV) = 3.037 V
    +25 mV overload clips at (V+) - 0.05 V and recovers, no fold-back.

GAIN SPLIT   G1 * G2 = 39.90 * 3.49
    G1 = 1 + 49.4k/RG = 1 + 49.4k/1.27k = 39.90   U1 AD8226, R1 across pins 2-3
    G2 = 1 + R4/R5    = 1 + 24.9k/10.0k = 3.49    U2B, OPA2333 half B
  WHY IT IS SPLIT: the AD8226's INPUT VOLTAGE RANGE section (Eq.1-3, Table 8)
  limits the internal 1st/2nd-stage nodes, not the pins.  Eq.2 ceiling on
  |G*Vdiff| and the gain it allows at 20 mV FS (blocks.md Ruling 2) - note
  which Vcm each row belongs to:
      Vcm 1.65 V (Q1), rail -5 %, 0 degC .............. 1.49 V   G <= 75
      Vcm 1.7325 V, rail -5 % AND excitation +5 % ..... 1.33 V   G <= 66
  1.65 V is the stated operating point; the 1.33 V / G <= 66 pair is the
  WORST CORNER, not the nominal common mode.  Either way a single stage at
  G = 139 saturates INSIDE the part while its input and its output both
  still look legal.  The data sheet's own remedy: less gain in the in-amp,
  the rest later in the chain.

PEDESTAL   Vref = 3.3 V * R3/(R2+R3) = 3.3 * 10.0k/131.0k = 0.2519 V
    C4 filters the DIVIDER node (Thevenin 9.24k -> 172 Hz corner), never the
    buffer output - a follower into a capacitive load peaks.
    U2A buffers it.  AD8226 Fig.59 draws a bare divider into REF, crosses it
    out and marks it INCORRECT: source impedance at REF must stay below
    2 ohm, or the +IN path is amplified by 2(50k + Rref)/(100k + Rref) and
    CMRR collapses (9.24k there = ~8.5 % error = ~21 dB of CMRR left).

  HOW WELL THE BUFFER MEETS THAT RULE IS MEASURED, NOT FLAT (bench B9):
      DC 0.43 mohm    60 Hz 0.17 ohm    1 kHz 2.86 ohm    41 kHz 116 ohm
  Met through DC and the low frequencies where the AD8226 specifies CMRR;
  EXCEEDED above ~700 Hz (350 Hz on the pessimistic ro = 2 kohm bracket).
  Not a defect here - Q1 fixes the common mode at a STATIC 1.65 V with
  nothing at 1 kHz to convert, and the residual common-mode gain error is
  90.8 dB, at or above the part's own 90 dB min at 5 kHz.  A board with a
  MOVING common mode would have to rederive this.

*** R5 RETURNS TO /VREF, NOT TO GROUND ***
    U2B's + input sits at   V1 = Vref + G1*Vdiff.
    With R5 to /VREF:  Vout = V1 + (V1 - Vref)*R4/R5 = Vref + G1*G2*Vdiff.
    The output pedestal is therefore EXACTLY Vref - no matched network, no
    second reference node - and a shift of Vref lands on U1 REF and on the
    stage-2 return with OPPOSITE sign, so the reference's own drift and noise
    cancel to first order and survive only as the gain-1 pedestal term.
    With R5 to GND the pedestal would become G2*Vref and every bit of
    reference error would be amplified by G2.  A different, worse board.

/VREF IS ONE NODE WITH THREE LOADS: U2A OUT (1), U1 REF (6), R5.

J1 POLE ORDER IS IN- / IN+ / GND - LAYOUT DROVE THE PIN ASSIGNMENT.  J1 as
(IN+, IN-) against the AD8226's (-IN ... +IN) crosses the pair structurally
(P6 checked all 8 rotation/edge combinations).  Uncrossed costs 2 vias in
ONE leg - 0.6 pF, -123 dB at 1 kHz, inside budget - but they break the B.Cu
reference under the pair and unbalance the net whose symmetry is this
board's dominant error term.  Swapped: planar, symmetric, zero vias.
NOTHING ELECTRICAL MOVED - IN+ still lands on U1 pin 4 and "IN+ above IN-
gives positive out" holds.  THE SILK MUST SAY IN- / IN+ / GND.

SINGLE SUPPLY: U1 pin 5 (-VS) and U2 pin 4 (V-) go to GND.  The RRIO OPA2333
(30 mV typ from either rail) is the part that faces the rails, not the AD8226
(0.10 V guaranteed floor) - the same spec that makes a grounded REF unusable.

ACCURACY, RECORDED NOT SMOOTHED (blocks.md Ruling 3): Q7's 5 uV RTI over
0-50 degC is 10 ppm of full scale per degC and is NOT met - 13.9 uV typ /
56.4 uV max offset drift, plus 30-87 uV of gain drift at full scale.  No
3.3 V-capable part reaches it; zero and span are calibrated downstream.
  THE TERM blocks.md's TABLE OMITS - RAIL SENSITIVITY.  The pedestal is a
  RATIO of the rail (0.2519/3.3 = 7.63 %) and reaches the output at gain 1,
  so dVout/dVs = 0.0763 V/V (bench B6 measures exactly that) = 548 uV RTI
  per volt of rail.  So 0.28 % of rail movement AFTER calibration - about
  9.1 mV on 3.3 V - eats the whole 5 uV budget on its own, the DOMINANT
  post-calibration term, ahead of the 1.1 uV R2/R3 ratio-TCR the table does
  count.  Not an error and not a scope miss (a static pedestal calibrates
  out; a voltage reference is excluded at block-only) - it is a requirement
  on the +3V3 SOURCE, stated here so it is not lost.

(The "no output isolation resistor" result is recorded on the sheet itself,
beside the U2B -> J2 run where the part would have gone.)"""

# One-line annotations, one per row, in the gap below it.  Kept short so a
# centred KiCad text item stays inside its row's own horizontal span.
ROW_NOTES = [
    ((152.40, 92.71),
     "SIGNAL CHAIN   J1 -> U1 (G1 = 39.90) -> U2B (G2 = 3.49) -> J2"),
    ((63.50, 100.33),
     "J1 POLE ORDER: IN- / IN+ / GND - the silk legend must read that way"),
    ((63.50, 105.41),
     "IN+ still drives U1 pin 4; the polarity convention is unchanged (P6)"),
    ((203.20, 55.88),
     "NO OUTPUT ISOLATION RESISTOR: OPA2333 Fig.15's mid-30 % overshoot into "
     "1 nF is a UNITY-GAIN figure."),
    ((203.20, 60.96),
     "This stage runs at noise gain 3.49 - simulated 6.6 % into the 1 nF of "
     "Q8, ~63 deg phase margin."),
    ((243.84, 66.04),
     "Nothing needs isolating; block-only scope excludes conditioning anyway."),
    ((88.90, 135.89),
     "PEDESTAL   R2/R3 off +3V3 = 0.2519 V, C4 on the DIVIDER node, "
     "U2A buffers it for U1 REF"),
    ((88.90, 140.97),
     "AD8226's 2 ohm REF rule: met at DC and low frequency (B9: 0.43 mohm DC, "
     "0.17 ohm at 60 Hz),"),
    ((88.90, 146.05),
     "crossed above ~700 Hz - harmless, Q1's common mode is STATIC. Numbers "
     "in the box."),
    ((127.00, 171.45),
     "STAGE-2 GAIN SET   R5 RETURNS TO /VREF, NOT GND - that is what makes "
     "the pedestal EXACT"),
    ((114.30, 209.55),
     "POWER   +3V3 arrives at J3; C2 10uF bulk at J3; C1/C3 100nF at pin 8 "
     "of U1/U2 (AD8226 Fig.61, OPA2333 p15)"),
]


# ----------------------------------------------------------- multi-unit help
def _place_unit(sh: schlib.Sheet, tmp_ref: str, unit: int, at, pins: dict,
                expect: dict, lib_id: str, value: str, footprint: str,
                fields: dict | None = None):
    """Place ONE unit of a multi-unit symbol and wire that unit's pins.

    OPA2333AIDR is the only multi-unit symbol in lib/aiee.kicad_sym (unit 1 =
    amplifier A plus BOTH supply pins, unit 2 = amplifier B and nothing else).
    Two facts follow, and both are load-bearing (LEARNINGS 2026-08-07):

      1. A single ksa component covers ONE unit.  Place only unit 1 and
         kicad-cli ERC raises `missing_unit` ("unplaced units [B]") plus an
         `unconnected_wire_endpoint` for every wire drawn at a unit-2 pin.
      2. ksa reports EVERY pin of EVERY unit on any instance, each at its own
         sub-symbol offset from that instance's anchor.  Both units of this
         symbol are the same triangle, so stacking them on one anchor would
         put unit 2's OUT B exactly on unit 1's OUT A and short /VOUT to
         /VREF - with ERC reporting it as a legitimate connection.  Each unit
         gets its own anchor and only the pads listed in `pins` are wired.

    ksa refuses a duplicate reference in BOTH `components.add` and the
    `reference` setter, so unit 2 is added under a temporary ref; the merge
    onto the real one happens after save() (see merge_unit_refs).
    """
    schlib.assert_on_grid(at[:2], f"{tmp_ref} anchor")
    with schlib._quiet():
        c = sh.sch.components.add(lib_id, reference=tmp_ref, value=value,
                                  position=tuple(at[:2]), unit=unit)
    c.footprint = footprint
    for key, val in (fields or {}).items():
        c.set_property(key, val)
    sh._lib_ids[tmp_ref] = lib_id
    sh._rotations[tmp_ref] = 0
    sh._anchors[tmp_ref] = (at[0], at[1])
    names = {p.number: p.name for p in c.pins}
    for pad, want in expect.items():
        if want not in names.get(pad, "<missing>"):
            raise ValueError(f"{tmp_ref} unit {unit} pin {pad}: expected name "
                             f"~'{want}', got '{names.get(pad)}'")
    sh.wire_pins(tmp_ref, pins)
    return c


def merge_unit_refs(path: Path, renames: dict) -> int:
    """Rename a temporary unit ref onto the real one IN THE SAVED FILE.

    lumina-par's `_merge_units` did this in memory, before `Sheet.save()`.
    That is one step too early here, because save() ends with the
    schem_refdes field-placement pass and `schem_refdes.write_placements`
    indexes the sheet as `{c.reference: c for c in sch.components}` - a dict.
    Two units sharing a reference collapse to ONE entry, so both computed
    placements are applied to the SAME instance and the other unit's
    Reference/Value land wherever the first unit's body wanted them.
    Measured on the first build of this sheet: U2's unit-1 fields ended up at
    (153.95, 64.77) and (140.97, 64.77) - beside U2B on the CHAIN row, ~50 mm
    from U2A's own symbol, with U2A left unlabelled.  ERC and the netlist are
    both blind to it (fields are cosmetic), so only the plot shows it.

    Keeping the refs distinct until after save() gives schem_refdes two real
    components to place, and the merge afterwards is two exact string
    substitutions per unit - the Reference PROPERTY (what KiCad draws) and
    the `instances` entry (what the netlist reads).  A `Note` field that
    happens to mention "U2B" is untouched by both patterns, and the count
    assertions fail the build if either pattern ever stops matching exactly
    once.
    """
    text = path.read_text(encoding="utf-8")
    for old, new in renames.items():
        for pat, rep in ((f'(property "Reference" "{old}"',
                          f'(property "Reference" "{new}"'),
                         (f'(reference "{old}")', f'(reference "{new}")')):
            n = text.count(pat)
            if n != 1:
                raise ValueError(f"unit merge {old}->{new}: pattern {pat!r} "
                                 f"matched {n} times, expected exactly 1")
            text = text.replace(pat, rep)
    path.write_text(text, encoding="utf-8")
    return len(renames)


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "bb-amp", paper="A3", rev="A", date="2026-08-16", company="ai-ee",
        pwr_base=100,                  # sheets.md s3 #PWR range
        title="bb-amp  bridge front end  AD8226 x OPA2333, G=139.2, 3.3V")

    def add(lib_id, ref, value, at, footprint, pins, expect=None, note=None):
        """Place a purchased part, stamp its LCSC code, wire every pin.

        Every ref routed through here is a BOM line, so a missing code is a
        defect, not a default (see the LCSC map above).  Fail at build time.
        """
        code = LCSC.get(ref)
        if not code:
            raise KeyError(f"{ref}: no LCSC code in the parts map - a "
                           f"purchased part cannot ship unsourced")
        fields = {"LCSC": code}
        if note:
            fields["Note"] = note
        sh.add_component(lib_id, ref, value, at=at, footprint=footprint,
                         fields=fields, expect=expect)
        sh.wire_pins(ref, pins)

    # ======================================================= B1 input (J1)
    # 3-pole: IN- / IN+ / GND, in that pole order.  The two signal poles are
    # the REVERSE of sheets.md s2 on purpose - see the module docstring s3:
    # J1 (IN+, IN-) against U1 (-IN ... +IN) is a structural crossing that
    # costs 2 vias in one leg of the pair and punches the B.Cu reference
    # under it; swapping the poles makes the pair planar and symmetric.
    # Electrically identical - IN+ still lands on U1 pin 4.
    # Pole 3 is the input-bias-current return for BOTH inputs and the landing
    # for the cable shield - not a convenience pole (blocks.md B1; refdesign
    # D12).  No series R, no RC, no TVS: the AD8226's inputs are internally
    # protected to +-40 V beyond the rails and the bridge is inherently
    # current limited.
    add(S_J3P, "J1", "KF128-5.08-3P", (38.10, Y_CHAIN), F_J3P,
        {"1": "IN_N", "2": "IN_P", "3": "GND"},
        note="SENSOR IN, silk legend IN-/IN+/GND: 1=IN- (U1 pin 1), "
             "2=IN+ (U1 pin 4), 3=GND (bias-current return + shield). "
             "Pole order reversed vs sheets.md at P6 to uncross the pair.")

    # ==================================================== B2 in-amp (U1, R1)
    # Pin map: parts/C34250.json.  REF (6) is DRIVEN from /VREF - see the
    # module docstring s2 for why grounding it breaks the bottom of the span
    # and why a bare divider there breaks CMRR.
    # C1 (100 nF at pin 8) and C2 (10 uF bulk, shared) are the whole of
    # Figure 61's supply decoupling for a single-supply part: pin 5 is -VS,
    # and on this board -VS IS the ground pour, so it takes no cap of its own.
    sh.place_ic_with_decoupling(
        "U1", S_U1, "AD8226ARZ-R7", at=(88.90, Y_CHAIN), footprint=F_SOIC8,
        pins={"1": "IN_N", "2": "RG_A", "3": "RG_B", "4": "IN_P",
              "5": "GND", "6": "VREF", "7": "AMP1_OUT", "8": "+3V3"},
        expect={"1": "-IN", "2": "RG", "3": "RG", "4": "+IN", "5": "-VS",
                "6": "REF", "7": "VOUT", "8": "+VS"},
        decoupling=[
            {"cap": "C1", "pin": "8", "rail": "+3V3", "gnd": "GND",
             "value": "100nF 50V X7R", "lib_id": S_C100N,
             "footprint": F_C0603},
            # Figure 61's shared bulk.  "farther away from the part ... can be
            # shared by other precision integrated circuits" - the bulk value
            # class (20/30 mm) is exactly that sentence, so no override.
            {"cap": "C2", "pin": "8", "rail": "+3V3", "gnd": "GND",
             "value": "10uF 25V X5R", "lib_id": S_C10U,
             "footprint": F_C0805},
        ],
        caps_at=(76.20, Y_PWR), caps_dx=38.10)      # -> C1 76.20, C2 114.30
    # place_ic_with_decoupling takes no `fields`, so the IC and its caps are
    # stamped here.  P9's ONLY ref->LCSC source is this field; without it the
    # BOM/CPL export silently drops the part.
    for ref in ("U1", "C1", "C2"):
        sh.sch.components.get(ref).set_property("LCSC", LCSC[ref])

    # R1 = RG, across U1 pins 2 and 3.  This single resistor IS the stage-1
    # gain law (G = 1 + 49.4k/RG); its own TCR adds directly to the AD8226's
    # -100 ppm/degC gain drift, which is why it is 0.1 % / 25 ppm thin film.
    add(S_R1K27, "R1", "1.27k 0.1% 25ppm", (88.90, 50.80), F_R0603,
        {"1": "RG_A", "2": "RG_B"},
        note="RG across U1 pins 2-3: G1 = 1 + 49.4k/1.27k = 39.90")

    # ============================================ B4 output gain stage (U2B)
    # Unit 2 of U2.  Non-inverting, + input on /AMP1_OUT, gain set by R4/R5
    # with R5 returned to /VREF.  Placed under a TEMPORARY ref; unit 1 (U2A,
    # below) takes the real "U2" and merge_unit_refs joins them after save().
    _place_unit(
        sh, UNIT2_TMP_REF, 2, (X_U2, Y_CHAIN),
        pins={"5": "AMP1_OUT", "6": "FB2", "7": "VOUT"},
        expect={"5": "INB+", "6": "INB-", "7": "OUTB"},
        lib_id=S_U2, value="OPA2333AIDR", footprint=F_SOP8,
        fields={"LCSC": LCSC["U2"],
                "Note": "U2B = second gain stage, G2 = 1 + R4/R5 = 3.49"})

    # NOTE the empty space between U2B and J2: P3's 100 ohm R6 lived here and
    # was REMOVED on the P8 bench's evidence (module docstring s5).  U2B's
    # output pin drives J2 directly; /VOUT is one node.

    # ====================================================== B5 output (J2)
    # Also the block's measurement point - no separate test point exists
    # (blocks.md B5).
    add(S_J2P, "J2", "KF128-5.08-2P", (241.30, Y_CHAIN), F_J2P,
        {"1": "VOUT", "2": "GND"},
        note="SIGNAL OUT: 1=OUT (0.113-3.037 V), 2=GND. Load >=100k, <=1nF")

    # ================================= B3 reference / pedestal (below U1)
    # R2/R3 off +3V3 -> 0.2519 V; C4 bypasses the DIVIDER node; U2A buffers.
    add(S_R121K, "R2", "121k 0.1% 25ppm", (38.10, Y_REF), F_R0603,
        {"1": "+3V3", "2": "VREF_SET"},
        note="pedestal divider top leg; 121k/10.0k off +3V3 -> 0.2519 V")
    add(S_R10K, "R3", "10.0k 0.1% 25ppm", (63.50, Y_REF), F_R0603,
        {"1": "VREF_SET", "2": "GND"},
        note="pedestal divider bottom leg; ratio TCR mismatch = 1.1 uV RTI")
    add(S_C100N, "C4", "100nF 50V X7R", (88.90, Y_REF), F_C0603,
        {"1": "VREF_SET", "2": "GND"},
        note="filters the DIVIDER node (9.24k -> 172 Hz). NOT a supply cap "
             "and NOT to be moved onto U2A's output.")

    # U2A - unit 1, and therefore the unit that carries V+ (8) and V- (4).
    # Unity follower: OUT A and -IN A are the same node, /VREF.
    _place_unit(
        sh, "U2", 1, (X_U2A, Y_REF),
        pins={"1": "VREF", "2": "VREF", "3": "VREF_SET",
              "4": "GND", "8": "+3V3"},
        expect={"1": "OUTA", "2": "INA-", "3": "INA+", "4": "V-", "8": "V+"},
        lib_id=S_U2, value="OPA2333AIDR", footprint=F_SOP8,
        fields={"LCSC": LCSC["U2"],
                "Note": "U2A = /VREF buffer; UNIT 1 also carries V+ (8) and "
                        "V- (4) for the whole package"})

    # C3, the OPA2333's own 0.1 uF.  p15 asks for it "closely across the
    # supply pins" - a short pin-8-to-pin-4 loop.  The association is written
    # by hand because place_ic_with_decoupling is a per-IC call and U2 is
    # built unit by unit; the return net is the default GND, which
    # netlist_audit still checks the cap actually spans.
    add(S_C100N, "C3", "100nF 50V X7R", (X_U2, Y_PWR), F_C0603,
        {"1": "+3V3", "2": "GND"},
        note="0.1uF ACROSS U2 pins 8 and 4 (OPA2333 p15), short loop")
    sh.decoupling.append({"cap": "C3", "ic": "U2", "pin": "8",
                          "rail": "+3V3", "value": "100nF 50V X7R"})

    # ================================= B4 gain set (R4, R5) - below U2B
    # *** R5 returns to /VREF.  See the module docstring s2. ***
    add(S_R24K9, "R4", "24.9k 0.1% 25ppm", (X_U2, Y_GAIN), F_R0603,
        {"1": "VOUT", "2": "FB2"},
        note="stage-2 feedback; G2 = 1 + 24.9k/10.0k = 3.49")
    add(S_R10K, "R5", "10.0k 0.1% 25ppm", (190.50, Y_GAIN), F_R0603,
        {"1": "FB2", "2": "VREF"},
        note="stage-2 gain return to /VREF, NOT GND - makes the pedestal "
             "exact and cancels reference drift to first order")

    # ==================================================== B6 power entry (J3)
    # External 3.135-3.465 V rail; no regulator, no protection, no second
    # rail (all excluded at block-only).  C1/C2 were placed with U1 above.
    add(S_J2P, "J3", "KF128-5.08-2P", (38.10, Y_PWR), F_J2P,
        {"1": "+3V3", "2": "GND"},
        note="POWER IN: 1=+3V3 (3.135-3.465 V, 0.65 mA), 2=GND")

    # =========================================================== power rails
    # Power SYMBOLS make these two nets GLOBAL and BARE; a local label would
    # export "/+3V3" and silently break constraints.json's power[0].net match.
    # PWR_FLAG on both: every supply pin on this board is typed power_in and
    # the rail arrives from OFF-BOARD through a passive screw terminal, so
    # without a flag ERC has no driver to point at (sheets.md s3 #FLG row).
    sh.power_flag("GND", at=(38.10, Y_RAIL), sym="power:GND", flag=True)
    sh.power_flag("+3V3", at=(88.90, Y_RAIL), sym="power:+3V3", flag=True)

    # ================================================= the study apparatus
    sh.sch.add_text_box(EQUATIONS, position=TEXTBOX_AT, size=TEXTBOX_SIZE,
                        font_size=TEXTBOX_FONT, stroke_width=0.254,
                        stroke_type="solid", fill_type="none",
                        justify_horizontal="left", justify_vertical="top")
    for at, line in ROW_NOTES:
        sh.sch.add_text(line, position=at)

    # NOTE: U2's two halves are still two components here, "U2" (unit 1) and
    # the temporary "U2B" (unit 2).  They become ONE component in the SAVED
    # FILE - see merge_unit_refs for why the merge cannot happen any earlier.
    # A caller that uses build() directly must run that merge after saving or
    # ERC will (correctly) report `missing_unit` on both halves.
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
        sch = sh.save(out_dir, project=True)
        merged = merge_unit_refs(sch, UNIT_MERGE)   # AFTER save - see above
        hidden = hide_aux_fields(sch)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:                # noqa: BLE001 (SPEC 6: error -> 2)
        print(json.dumps({"script": "gen.bb-amp", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.bb-amp", "status": "pass",
        "files": [str(sch), str(out_dir / "bb-amp.kicad_pro"), str(meta)],
        "components": len(sh.sch.components),
        "decoupling_associations": len(sh.decoupling),
        "units_merged": merged,
        "fields_hidden": hidden,
        "field_placement": sh.place_report,
    }, indent=1, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
