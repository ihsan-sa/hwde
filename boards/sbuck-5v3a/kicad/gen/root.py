"""sbuck-5v3a root generator - THE WHOLE SCHEMATIC (one flat root sheet).

7-18 V -> 5.0 V / 3.0 A synchronous buck module.  Architecture decision D8
(`architecture/decisions.md`): ONE flat root sheet, no hierarchy, so every
local label exports as `/NAME` and every power symbol exports BARE - the
`/<sheet>/<LABEL>` mismatch class that cost lumina-par a P4 amendment cannot
exist here.

    Rebuild:  .venv\\Scripts\\python.exe boards/sbuck-5v3a/kicad/gen/root.py
    Outputs:  ../sbuck-5v3a.kicad_sch  ../sbuck-5v3a.kicad_pro
              ../decoupling.json

The Python is the SOURCE; the .kicad_sch is build output.  Every pin number
below comes from a datasheet-extract JSON (`parts/C2071691.json` for U1,
`parts/C16072.json` for Q1) or from the project symbol library's own pin
table, never from memory.  `expect=` entries are pin-name insurance.

=====================================================================
1.  NET CONTRACT (architecture/sheets.md s2 - BINDING, do not "tidy")
=====================================================================
BARE global nets, made bare by a POWER SYMBOL whose Value names the net
(LEARNINGS 2026-07-28: a power symbol's exported net name is its VALUE, and
the symbol WINS over a coincident local label):

    +VIN   +5V   GND

Root-sheet LOCAL labels, which KiCad exports with the single leading slash:

    /VIN  /SW  /EN  /FB  /COMP  /BST  /RT  /QGATE

*** The label TEXT below is written BARE ("VIN", "SW", ...).  The leading `/`
is the ROOT SHEET PATH that KiCad prepends on export.  Typing the slash into
the label instead produces the escaped net `/{slash}VIN` - silently, with a
clean build and a clean ERC - and every constraints.json match then fails.
Measured on this very board before the fix (LEARNINGS 2026-08-09): `/VIN` and
`/SW`, the two highest-current nets here, both came out `/{slash}...` and
netlist_audit raised missing_net on both.  Verify by dumping the exported
names, never by reading the schematic. ***

Three series elements need an internal node that sheets.md's chain notation
("A -> B -> C") does not name.  These are ADDITIONS, not renames, and none of
them ends in _P/_N/_H/_L/DP/DM/+/- so `rules_gen.detect_diff_pairs` and
`check_diffpair.discover_pairs` cannot pair them (their bare "P"/"N" family
would need a partner net that does not exist here anyway, and
`constraints.json.diff_pairs` is an explicit empty list):

    /VIN_RAW  J1.1 -> F1.1        (connector to fuse, UNFUSED)
    /COMPZ    R5.2 -> C2.1        (Type-II series-RC internal node)
    /SNUBZ    R9.2 -> C16.1       (DNP snubber internal node)
    /LEDA     R8.2 -> D1.1        (LED anode)

`/VIN` is the FUSED side (F1.2 -> Q1 drain) because that is the endpoint
`constraints.json.power[/VIN]` names ("J1 -> F1 -> Q1 drain, BEFORE the
reverse-polarity element") and the node `voltages[/VIN]` rates at 26 V for
the hot-plug ring.  See OPEN in the P4 report: `/VIN_RAW` carries the same
2.44-2.6 A and currently has NO constraints.json width entry.

=====================================================================
2.  COMPENSATION RE-DERIVATION  (the P2/D6 task; U1 is EXTERNALLY comp'd)
=====================================================================
Vendor procedure: AP64350 DS41976 Rev.5-2 pp.16-21, Eqs 12-20, as extracted
into `parts/C2071691.json` (pin 6 COMP notes).  Constants ALL from that
extract: error-amp gm = 0.15 mS, current-sense gain RT(sense) = 0.089 V/A,
VFB = 0.8 V, fsw = 500 kHz (R4 = 200k, Eq.7).

  Eq.17  R5 = 2*pi*fc*VOUT*COUT*RTsense / (gm*VFB) = 4659.9 * fc*VOUT*COUT
  Eq.18  C5 = VOUT*COUT / (IOUT*R5)            (comp zero at the load pole)
  Eq.19  C6 = max(Rc*COUT/R5, 1/(pi*fsw*R5))   (optional COMP HF pole)
  Eq.20  C4 in [1/(10*pi*fc*R1), 1/(4*pi*fc*R1)]   (optional FB feedforward,
                                                    i.e. zero at 2x..5x fc)
  Datasheet design targets (p.17): phase margin > 45 deg, gain margin
  < -10 dB, crossover fc < 10% of fsw (= 50 kHz here).

--- 2.1 WHY THE VENDOR'S WORKED EXAMPLE CANNOT BE COPIED -------------
The vendor's worked example (p.19-21: R5=14k, C5=3.3nF, C6=47pF, C4=33pF)
is quoted for a 2x22uF bank which it treats as COUT ~= 30 uF.  This board
has FIVE 22 uF parts.  Copied verbatim onto this bank the loop crosses at
6.9-8.6 kHz and the 3 A load-step excursion is 715-795 mV against a 200 mV
limit.  That is the failure P2 predicted (decisions.md D6) and it is why
this block exists.

--- 2.2 EFFECTIVE COUT (DC-bias derated, NOT nameplate) --------------
C10-C14 = 5x TCC1210X7R226K250MT, 22 uF / 25 V X7R 1210, at 5 V bias =
20% of rated.  Nameplate sum 110 uF.  Two independent derating estimates,
and BOTH are conventional estimates, NOT vendor data:

  (a) house estimate, `research/magnetics-caps.md` s3.2: ~12% loss for this
      exact part class at 5 V  ->  96.8 uF.  That file states explicitly
      (s2.1 and OPEN item 2) that "no vendor DC-bias curve was obtainable
      for any MLCC on this board; every effective-capacitance figure is a
      conventional estimate".  It is repeated here as such.
  (b) the vendor's OWN derating ratio inside the worked example: 30 uF from
      44 uF nameplate = 68.2%  ->  75.0 uF on our bank.  Applying the
      vendor's own ratio is what `parts/C2071691.json` recommends
      ("this derating RATIO is worth reusing when re-deriving").

Neither is measured.  So the design is closed over the BAND [75.0, 96.8] uF
with the geometric mean 85.2 uF as the nominal, rather than pretending to a
single number.  Hot X7R (board runs 83-87 C) and aging both push toward the
low end, which is the reason (b) is not dismissed.

--- 2.3 THE ARITHMETIC ----------------------------------------------
  Eq.17 at fc = 38 kHz, VOUT = 5 V, COUT = 85.2 uF:
      R5 = 4659.9 * 38e3 * 5 * 85.2e-6 = 75_434 ohm   ->  R5 = 75 k (E24)

  Eq.18 at R5 = 75k, IOUT = 3.0 A, COUT = 75.0 / 85.2 / 96.8 uF:
      C5 = 1.67 / 1.89 / 2.15 nF   ->  E24 snap would be 2.2 nF.
      CHOSEN 3.3 nF, which is the part ALREADY SOURCED (C1613, parts.json).
      3.3 nF puts the comp zero at 1/(2*pi*75k*3.3n) = 643 Hz against a
      full-load output pole at 1/(2*pi*(5/3)*85.2u) = 1121 Hz - i.e. the
      zero sits BELOW the pole, which is the stability-conservative
      direction, and the modelled cost is 0.3-0.5 deg of phase margin
      (see 2.5).  Avoiding a new BOM line for a 0.4 deg effect is the
      trade taken; 2.2 nF is a drop-in if a later phase prefers Eq.18
      exactly.

  Eq.19 at R5 = 75k, Rc ~ 2 mohm (5x MLCC in parallel), fsw = 500 kHz:
      C6 = max(2.27 pF, 8.49 pF) = 8.5 pF   ->  10 pF (E24, C0G)
      HF pole 1/(2*pi*75k*10p) = 212 kHz.

  Eq.20 at fc = 38 kHz, R6 = 105k:  C4 in [8.0, 19.9] pF.

--- 2.4 THE ONE SPARE CAP: Eq.19 IS FITTED, Eq.20 IS NOT -------------
*** DELIBERATE DEVIATION FROM sheets.md s3, FLAGGED FOR THE ORCHESTRATOR ***
sheets.md gives C3 as "47 pF C0G 0603, optional feedforward across R6"
(the datasheet's C4 / Eq.20 position).  The vendor's procedure has TWO
optional caps and this board's refdes map has exactly ONE spare, so P4 must
choose which one C3 becomes.  Measured on the loop model below (validated
in 2.5), at R5 = 75k over the whole COUT band:

    C3 as Eq.20 feedforward, 10-22 pF : PM 91-105 deg, |T| at fsw/2 falls
        to -7.8 .. -0.9 dB.  It SPENDS margin the design already has (PM was
        already ~80 deg with no third cap) and BREAKS the vendor's own
        gain-margin target, because with no COMP-side pole the feedforward
        zero flattens the loop above 69-152 kHz.
    C3 as Eq.19 COMP HF pole, 10 pF   : PM 65.0-72.2 deg (20+ deg over the
        45 deg floor) and |T| at fsw/2 = -15.0 .. -17.0 dB, comfortably
        inside the < -10 dB target.

(Both rows re-measured on the FINAL 105k/20.0k divider; the verdict is
unchanged from the 115k/22.1k measurement the orchestrator approved.)

The P4 reviewer put the feedforward variant STRONGER still: with no
COMP-side pole to roll the compensator off, the loop is CONDITIONALLY
UNSTABLE, not merely low-margin - |T| is still at or above unity where the
phase reaches -180 deg.  The high phase margin it shows at crossover is
exactly the trap: it is measured at the wrong frequency.

So C3 is fitted as the Eq.19 COMP-to-GND pole.  Second reason: Eq.19's own
answer (8.5 pF) is the same order as the COMP node's unavoidable stray
(pin + trace, ~3-8 pF), so this pole exists whether or not a part is fitted
- a 10 pF part makes it a DESIGNED 212 kHz instead of an uncontrolled
parasitic, next to a 3.5 A / 500 kHz SW pour.  The 47 pF value sheets.md
names would put the pole at 45 kHz, ~1.2x fc, and eat ~35 deg of phase.

Net/placement impact of the move: NONE.  C3 goes from (+5V, /FB) to
(/COMP, GND); both endpoints are existing contract nets, no new net, and
constraints.json's `fbcomp` group (anchor R6; members R7, C3, R5, C2) is
unchanged and still correct - C3 still belongs tight to U1's FB/COMP corner.

--- 2.5 RESULT, and an HONEST account of what the model is worth ----
Model: peak-current-mode plant Zout(s)/RTsense with the Ridley sampling term
He(s) = 1 - (2f/fs)^2 - j*pi*f/fs, Type-II gm compensator, FB divider with
its optional feedforward.

*** CORRECTION, P4 REVIEW 2026-08-09.  An earlier version of this file
claimed the model was "validated against the vendor's own Bode plot" to
~3 deg of phase, and carried an "x0.83 realisation factor" derived from that
claim.  BOTH ARE WITHDRAWN.  The comparison was not like-for-like: it ran
the model with the feedforward cap ABSENT, while the reviewer read Fig.29's
plotted schematic and found C4 = 33 pF IS fitted there.  The x0.83 factor
therefore had no evidence behind it and must not be reused. ***

The like-for-like comparison, on the vendor's Fig.29-31 circuit with BOTH
optional caps fitted (R5=14k, C5=3.3n, C6=47p, C4=33p, COUT=30u, IOUT=3.5A):

                    this model      vendor published     model error
    fc                22.3 kHz          16.6 kHz         +35%
    phase margin     101.0 deg          81.6 deg         +19.4 deg
    gain margin       -8.3 dB          -26.8 dB          +18.5 dB

So the model is OPTIMISTIC on all three metrics against the only vendor data
point available.  The table below is therefore a BEST CASE, and the
"corrected" row applies those measured offsets (fc x0.743, PM -19.4 deg).
Treat that row as a plausibility band, NOT as a second measurement: it
extrapolates a one-point calibration taken at a different operating point
(COUT 30 uF, IOUT 3.5 A, R5 14k, both optional caps fitted) onto a different
circuit.  What IS established is the DIRECTION and the rough size of the
error, which is what the design has to survive.

  CHOSEN: R5 = 75 k, C2 = 3.3 nF, C3 = 10 pF (COMP->GND).  IOUT 0.3-3.0 A.
  Measured on the FINAL feedback divider, R6 = 105k / R7 = 20.0k:

    COUT (uF)          75.0        85.2        96.8   <- derating band
    fc   (model)      42.2 kHz    37.3 kHz    32.9 kHz
    fc   (corrected)  31.4 kHz    27.7 kHz    24.4 kHz
    PM   (model)      65.0-66.6   68.0-69.6   70.7-72.2  deg
    PM   (corrected)  45.6-47.2   48.6-50.2   51.3-52.8  deg
    |T| at fsw/2      -15.0 dB    -16.0 dB    -17.0 dB   (model)
    with +5 pF COMP stray: fc 32.4-41.3 kHz model, PM 62.0-68.3 deg model

  >>> PHASE MARGIN PASSES ON BOTH READINGS: 62.0-72.2 deg on the model,
  >>> 45.6-52.8 deg corrected, against the >= 45 deg floor.  That is the
  >>> requirement this task was set to meet and it is met either way.
  >>> fc is 32.9-42.2 kHz on the model (inside 25-50 kHz) and 24.4-31.4 kHz
  >>> corrected - i.e. the corrected floor lands 2.4% UNDER the 25 kHz
  >>> target, at the 96.8 uF corner.  Called out rather than rounded away.
  >>> See 2.5a for why this is not worth a value change.

  Load step, 0 -> 3.0 A:  dV = dI/(2*pi*fc*COUT), and 2*pi*fc*COUT =
  R5*gm*VFB/(RTsense*VOUT) is INVARIANT in COUT, so the excursion is set by
  R5 alone: dV = 148 mV on the model, and 148/0.743 = 200 mV applying the
  correction consistently - i.e. AT the 200 mV limit, not inside it.
  (The vendor's 14k would give 795 mV / 1070 mV.)  Settling 5/(2*pi*fc) =
  23-33 us against the 100 us recovery spec, which passes with room on both
  readings.  TWO CAVEATS ON THIS NUMBER, neither resolvable here: the 0 A
  starting point is in PFM, which this CCM model does not describe at all;
  and dV assumes the loop, not the capacitor, limits the excursion.

--- 2.5a WHY R5 = 75 k STANDS ANYWAY -------------------------------
The obvious reflex - raise R5 to lift fc and cut dV - makes the design
WORSE, because a higher fc buys more sampling-pole lag.  Swept on the
corrected reading (fc floor / PM floor / dV):

    R5 = 75 k : 24.4 kHz / 45.6 deg / 200 mV    <- chosen
    R5 = 82 k : 26.6 kHz / 44.1 deg / 183 mV    PM now FAILS the 45 floor
    R5 = 91 k : 29.3 kHz / 39.9 deg / 165 mV    PM fails badly
    R5 = 100 k: 31.9 kHz / 35.7 deg / 150 mV    PM fails badly

No value of R5 clears fc, PM and dV simultaneously on the corrected
reading; 75 k is the closest and is the only one that keeps phase margin -
the binding requirement - above its floor.  Raising R5 trades a 2.4% fc
miss for a phase-margin failure, which is the wrong direction.

Two further reasons the residual is acceptable rather than a defect.
(a) The dominant uncertainty on this board is NOT the loop model, it is the
COUT derating estimate itself: section 2.2 is explicit that no vendor
DC-bias curve exists for any MLCC here, and the [75.0, 96.8] uF band is a
+/-13% spread around its own mean.  A 2.4% fc miss and a 0% dV miss sit well
inside that.  (b) The corrected fc floor occurs at the 96.8 uF corner, i.e.
where the bank is LARGEST - the benign direction for a load step - while dV
is invariant in COUT.  The two marginal readings do not stack at one corner.

Escalation path if bring-up disagrees: R5 is one 0603 resistor and C2/C3 sit
beside it, so the network is re-tunable on the bench without a respin - which
is exactly why the DNP snubber and this network were kept as discrete parts.

  EFFECT OF THE 115k/22.1k -> 105k/20.0k DIVIDER CHANGE (P3 re-source, to
  put VOUT nominal on exactly 5.0000 V): the loop sees ONLY the DC feedback
  factor, which moves 22.1/137.1 = 0.161196 -> 20.0/125.0 = 0.160000, i.e.
  -0.742% or -0.065 dB.  Re-measured, not assumed: fc drops 0.2-0.3 kHz
  (<= 0.8%), phase margin RISES 0.1-0.2 deg, |T| at fsw/2 moves <= 0.1 dB,
  and dV is untouched (it depends on R5 only).  Negligible, as expected.
  Small bonus: 0.160000 is EXACTLY the VFB/VOUT that Eq.17 assumes, so the
  compensator is now matched to the vendor equation instead of 0.75% off,
  and C3 is the COMP-side pole so R6/R7 do not enter the compensator's own
  zero/pole at all - only this DC factor.

--- 2.6 THE 4x22uF ESCAPE HATCH WAS **NOT** NEEDED ------------------
The bank stays at 5x 22 uF (C10-C14).  For the record, the same network on
a 4x bank still closes (COUT 60.0/68.2/77.4 uF -> fc 52.9/46.7/41.3 kHz,
PM 60.2/63.9/67.2 deg), so the authorised reduction remains available to a
later phase - but only the top corner would sit slightly over fsw/10.

--- 2.7 PARTS CONSEQUENCE (all sourced by P3, no invented codes) -----
  R5  75 k  1% 0603      -> C23242,  replaces the 14k placeholder C22803.
  C3  10 pF 50 V C0G 0603 -> C106245, replaces the 47pF placeholder C1671.
  C2  3.3 nF 50 V X7R 0603 -> UNCHANGED, keeps C1613.
P4 shipped these two as `Sourcing`-flagged gaps with NO `LCSC` field rather
than guessing a code; P3 has since sourced both and the codes above are the
real ones.  The `add()` helper now RAISES on any purchased part with no code,
so the gap class cannot come back silently.

Also re-sourced by P3 and adopted here (see section 5): the feedback divider
R6/R7, 115k/22.1k -> 105k/20.0k.

=====================================================================
3.  UVLO DIVIDER - re-checked against the datasheet's own equations
=====================================================================
`parts/C2071691.json` pin 3 (EN), Sec 5 p.11 Fig.23.  The internal pull-ups
ARE in the equations - a naive two-resistor divider is simply wrong here
(decisions.md D2).  Datasheet R3 = VIN-to-EN = our R2; datasheet R4 =
EN-to-GND = our R3:

  Eq.2  R3 = (0.924*VON - VOFF) / 4.114uA
  Eq.3  R4 = 1.1*R3 / (VOFF - 1.09 V + 5.5uA*R3)

  Target VON = 6.2 V, VOFF = 5.3 V (D2; NOT the delegate's 6.5/6.0, whose
  0.5 V gap is under this board's own 0.49 V cable drop at 2.44 A and
  motorboats):
      R3 = (0.924*6.2 - 5.3)/4.114e-6 = 0.4288/4.114e-6 = 104.2 k -> 105 k
      R4 = 1.1*104229/(5.3-1.09+5.5e-6*104229) = 114652/4.7833 = 23.97 k
                                                                 -> 24.0 k
  Back-solved with the SNAPPED E96 values R2 = 105k, R3 = 24.0k:
      VOFF = 1.09 + 1.1*105k/24.0k - 5.5uA*105k = 1.09 + 4.8125 - 0.5775
           = 5.33 V
      VON  = (VOFF + 4.114uA*105k)/0.924 = (5.325+0.43197)/0.924 = 6.23 V
      hysteresis 0.90 V; divider current 12 V/129 k = 93 uA (1.1 mW).
  Both VON > 3.7 V and VOFF > 3.3 V, the datasheet's stated validity floors.
  Architecture values CONFIRMED unchanged.  P8 SIM-2 still owes the
  tolerance sweep (VEN_H 1.18-1.25, VEN_L 1.03-1.09, 1% resistors).

=====================================================================
4.  OTHER BINDING WIRING FACTS
=====================================================================
Q1 AO4407A (parts/C16072.json): pins 1,2,3 = Source, 4 = Gate,
5,6,7,8 = Drain.  ALL three sources and ALL four drains are wired.
DRAIN to the input side (/VIN), SOURCE to the load side (+VIN): the body
diode conducts input->load before the channel enhances, and Vgs = -Vin
enhances it.  R1 100k gate->GND is the enhancement pull AND the
polarity-reversal turn-off path.  D2 BZT52C15 15 V zener clamps Vgs with
its CATHODE at the source (+VIN) and ANODE at the gate (/QGATE), because
the 25.4 V hot-plug ring would otherwise exceed the +/-25 V Vgs rating.

*** NO series gate resistor and NO gate capacitor. ***  This is an explicit
architecture DECISION, not an omission: blocks.md B1 and sheets.md s5 item 4
both state it and sheets.md adds "do not let ERC or a reviewer add one".
The rationale is that Q1's body diode already bypasses the channel during
inrush (57 A for ~10 us, 1-2 orders inside the SO-8 SOA), so a gate RC
cannot limit inrush at all, and a gate cap would DELAY turn-off on a
polarity reversal while running.  There is also no refdes and no part for
one anywhere in the P2/P3 package.  The P4 assignment text asked for "the
series gate resistor the architecture specifies"; the architecture specifies
none, so none is fitted - flagged in the P4 report rather than silently
resolved either way.

C4 polarity: the KNM2100UF35V149EC0055 symbol has GENERIC pin names ("1",
"2") with NO polarity semantics, so the polarity is keyed off the FOOTPRINT,
whose +/- silk puts PIN 1 = POSITIVE.  pin 1 -> +VIN, pin 2 -> GND.  The
`expect` entry below asserts the symbol really does carry generic names, so
a future library refresh that gave it A/K names would fail loudly instead of
silently reversing an electrolytic.

C1 100 nF BST->SW is required, not optional (datasheet pin 1).  It is NOT a
rail decoupler (it spans /BST and /SW, not rail+GND) so it cannot appear in
decoupling.json, whose schema requires rail+gnd.

C4 is deliberately NOT a decoupling association either: constraints.json
requires C4 to sit >= 12 mm AWAY from U1 (its life is set by local board
temperature), which is the exact opposite of what check_decoupling enforces.

U1 exposed pad (pin 9) is a real net-capable pad and the datasheet requires
it tied to GND - wired to GND here; the 16-via thermal array is a P6/P7
review gate (constraints.json says check_thermal will NOT catch its absence).

=====================================================================
5.  FEEDBACK DIVIDER - 105k / 20.0k, BOTH 0.1%
=====================================================================
    VOUT = VFB * (1 + R6/R7) = 0.8 * (1 + 105.0/20.0) = 0.8 * 6.2500
         = 5.0000 V EXACTLY.  Divider current 5.0/125k = 40 uA.

This supersedes the 115k/22.1k pair (the AP64350 datasheet's own Table-1 row
for 5.0 V, which P3 had rounded from the table's 115.8k).  That pair is
electrically fine but lands VOUT nominal at 4.9629 V, and its worst-case LOW
corner - VFB at its 792 mV minimum plus both resistors at their 0.1% limits -
sits at 4.9034 V, only 3.4 mV inside the 4.90 V floor.  105k/20.0k is an
EXACT 5.2500 ratio, so the same corner moves to ~4.94 V (~40 mV of margin)
and the nominal lands on 5.0000 V.  P8 SIM-1 still owes the formal sweep.

BOTH RESISTORS MUST STAY 0.1% (0.5% is the absolute floor).  The 0.8 V
reference tolerance alone (792-808 mV) already spends -1.2%/+0.84% of the
+/-2% window, i.e. 60% of the budget, before any resistor error; 1% parts
stack +/-2% of ratio error on top and miss the 4.90-5.10 V window at the
corner.  This is the constraint SIM-1 exists to defend - do not let a later
phase substitute 1% parts to save cents.

The divider is also the ONLY path by which R6/R7 touch the control loop
(C3 is the COMP-side pole, not a feedforward across R6), and that path is
the DC feedback factor alone - see the re-measurement in section 2.5.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[4]                 # boards/<b>/kicad/gen/root.py -> repo
WORKSPACE = HERE.parents[2]            # boards/sbuck-5v3a
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
S_U1 = "aiee:AP64350SP-13"
S_Q1 = "aiee:AO4407A"
S_J = "aiee:DB128L-5.08-2P"
S_D2 = "aiee:BZT52C15"
S_LED = "aiee:0805G"
S_L1 = "aiee:FAUL1050-6R8MT"
S_CBULK = "aiee:KNM2100UF35V149EC0055"
S_C47U = "aiee:1206B475K500NT"          # C5-C8, 4.7uF/50V 1206
S_C100N = "aiee:CC0603KRX7R9BB104"      # C1, C9
S_C33N = "aiee:CL10B332KB8NNNC"         # C2 (Ccomp)
S_C22U = "aiee:TCC1210X7R226K250MT"     # C10-C14
S_C47U8 = "aiee:CC0805KKX7R7BB475"      # C15
S_R100K = "aiee:0603WAF1003T5E"
S_R200K = "aiee:0603WAF2003T5E"
S_R105K = "aiee:0603WAF1053T5E"
S_R24K = "aiee:0603WAF2402T5E"
S_R2K2 = "aiee:0603WAF2201T5E"
# DNP snubber, UPSIZED TO 1206 at P4 review (see the R9/C16 block below).
S_R22R = "aiee:1206W4F220JT5E"          # 22R 1% 1206, 0.25 W
S_C470P = "aiee:CC1206JKNPOCBN471"      # 470 pF C0G/NP0 1206, 1 kV
S_FUSE = "Device:Fuse"                  # EDITS.md edit 2: stock symbol
# Generic stock symbols for the four parts P4/P3 re-valued after the library
# pull (R5, C3 re-derived here; R6, R7 re-sourced by P3).  The project lib has
# no symbol for their MPNs, and re-using a neighbouring aiee: symbol would
# carry that symbol's OWN embedded MPN / "LCSC Part" properties onto the part
# - a stale wrong code sitting on the instance.  The correct code is stamped
# as an explicit `LCSC` field instead, which is the only name bom_cpl reads.
# aiee:ARG03BTC1153 (115k) and aiee:RT0603BRD0722K1L (22.1k) are consequently
# unused; the librarian can prune them, they are not referenced here.
S_R = "Device:R"
S_C = "Device:C"
S_TP = "Connector:TestPoint"
S_HOLE = "Mechanical:MountingHole"      # ZERO pins, unplated -> GND-isolated

# --------------------------------------------------------------- footprints
F_R0603 = "aiee:R0603"
F_R1206 = "aiee:R1206"                  # new at P4 review, for the upsized R9
F_C0603 = "aiee:C0603"
F_C0805 = "aiee:C0805"
F_C1206 = "aiee:C1206"
F_C1210 = "aiee:C1210"
F_LED = "aiee:LED0805-R-RD"
F_SOD123 = "aiee:SOD-123_L2.7-W1.6-LS3.7-RD"
F_SOIC8 = "aiee:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL"
F_SO8EP = "aiee:SO-8_L4.9-W3.9-P1.27-LS6.0-BL-EP"
F_CONN = "aiee:CONN-TH_2P-P5.08_DB128L-5.08-2P"
F_IND = "aiee:IND-SMD_L11.5-W10.0"
F_CBULK = "aiee:CAP-SMD_BD6.3-L6.5-W6.5-LS7.2-FD"
F_FUSE = "aiee:Fuse_1206_C1T_BelVendorLand"     # EDITS.md edit 2
F_TP = "TestPoint:TestPoint_Pad_D1.5mm"
F_HOLE = "MountingHole:MountingHole_3.2mm_M3"

# ref -> LCSC, straight from parts/parts.json.  parts.json is the S6
# per-DISTINCT-part shape (no `ref` keys), which `bom_cpl.load_parts_map`
# CANNOT map, so P9's only ref->LCSC source is the per-component `LCSC`
# field stamped here (bom_cpl.board_lcsc_map matches pname.upper()=="LCSC"
# only - the symbol's inherited "LCSC Part" property does NOT satisfy it).
LCSC = {
    "J1": "C395868", "J2": "C395868", "F1": "C3163312", "Q1": "C16072",
    "R1": "C25803", "D2": "C173427", "C4": "C2982822",
    "C5": "C29823", "C6": "C29823", "C7": "C29823", "C8": "C29823",
    "C9": "C14663", "C1": "C14663", "U1": "C2071691", "R4": "C25811",
    "C2": "C1613", "R2": "C16840", "R3": "C23352", "L1": "C5298292",
    "C10": "C49118556", "C11": "C49118556", "C12": "C49118556",
    "C13": "C49118556", "C14": "C49118556", "C15": "C277499",
    "D1": "C2297", "R8": "C4190",
    # DNP snubber, upsized to 1206 at the P4 review (was C23345 / C1588,
    # both 0603 - the 0603 R9 would have burned if ever populated):
    "R9": "C17958",          # 22R 1% 1206 0.25W  (1206W4F220JT5E)
    "C16": "C107177",        # 470pF C0G/NP0 1206 (CC1206JKNPOCBN471)
    # P4 re-derivations (s2), sourced by P3 after the first P4 pass:
    "R5": "C23242",          # 75k 1% 0603   (was placeholder 14k C22803)
    "C3": "C106245",         # 10pF 50V C0G  (was placeholder 47pF C1671)
    # P3 re-source of the feedback divider for an exact 5.0000 V (s5):
    "R6": "C491109",         # 105k 0.1%     (was 115k C1509621)
    "R7": "C723637",         # 20.0k 0.1%    (was 22.1k C723484)
}

# Fields KiCad should keep visible on the plot; everything else is hidden
# after save.  Variant stays visible because Variant=DNP is the ONLY
# do-not-populate marking reachable from a generator (kicad-sch-api's writer
# hard-codes `(dnp no)`) and a human must see it - LEARNINGS 2026-08-07.
VISIBLE_FIELDS = {"Reference", "Value", "Variant"}

# ------------------------------------------------------------------ layout
# All anchors are multiples of 1.27 mm (schlib raises otherwise).  Rows are
# spaced so no stub label anchor can land on a foreign wire run (schlib's
# _assert_label_clear guard; LEARNINGS 2026-07-22 [erc]).
Y_MAIN, Y_IN, Y_CONV, Y_OUT, Y_TP, Y_PWR = 88.90, 127.00, 158.75, 190.50, 222.25, 250.19
DX = 25.40                                   # discrete pitch within a row
X0 = 44.45                                   # first column of every row


def _col(i: float) -> float:
    return round(X0 + i * DX, 4)


def build() -> schlib.Sheet:
    sh = schlib.Sheet(
        "sbuck-5v3a", paper="A3", rev="A", date="2026-08-09",
        company="ai-ee",
        title="sbuck-5v3a  7-18V -> 5.0V 3.0A synchronous buck (AP64350)")

    def add(lib_id, ref, value, at, footprint, pins, expect=None,
            dnp=False, note=None):
        """Place a purchased part, stamp its LCSC code, wire every pin.

        Every ref routed through here is a BOM line, so a missing code is a
        defect, not a default: parts.json is the S6 per-DISTINCT-part shape
        with no `ref` keys, so `bom_cpl.load_parts_map` maps nothing and this
        field is P9's ONLY ref->LCSC source.  Fail loudly at build time.
        """
        code = LCSC.get(ref)
        if not code:
            raise KeyError(f"{ref}: no LCSC code in the parts map - a "
                           f"purchased part cannot ship unsourced")
        fields = {"LCSC": code}
        if note:
            fields["Note"] = note
        if dnp:
            fields["Variant"] = "DNP"
        sh.add_component(lib_id, ref, value, at=at, footprint=footprint,
                         fields=fields, expect=expect)
        sh.wire_pins(ref, pins)

    # ================================================================ B1
    # Input entry and reverse polarity.  J1 -> F1 -> Q1(D..S) -> +VIN.
    # J1/J2 are DNP for JLC assembly (sheets.md s5.8) and hand-soldered;
    # they must still carry pads, a BOM line and a CPL line.
    add(S_J, "J1", "SCREW_5.08_2P", (X0, Y_MAIN), F_CONN,
        {"1": "VIN_RAW", "2": "GND"}, dnp=True,
        note="DC INPUT 7-18V, LEFT short edge. DNP for assembly (Q25)")
    # F1: KiCad-stock Device:Fuse + hand-built vendor land (lib/EDITS.md #2).
    # 5 A slow-blow, 63 V, 20 mohm; sized for a shorted HS switch (D5).
    add(S_FUSE, "F1", "5A slow-blow", (_col(1.25), Y_MAIN), F_FUSE,
        {"1": "VIN_RAW", "2": "VIN"})
    # Q1: pin map from parts/C16072.json (Top View: 1,2,3=S / 4=G / 5..8=D).
    # DRAIN -> input, SOURCE -> load.  All 3 S and all 4 D pins wired.
    add(S_Q1, "Q1", "AO4407A", (_col(2.75), Y_MAIN), F_SOIC8,
        {"1": "+VIN", "2": "+VIN", "3": "+VIN", "4": "QGATE",
         "5": "VIN", "6": "VIN", "7": "VIN", "8": "VIN"},
        expect={"1": "S", "2": "S", "3": "S", "4": "G",
                "5": "D", "6": "D", "7": "D", "8": "D"},
        note="reverse-polarity P-FET: D=input, S=load, Vgs=-Vin")

    # ================================================================ B3/B5
    # U1 + its hot-loop decoupling.  Pin map from parts/C2071691.json.
    # C5-C8 (4x 4.7uF/50V X7R 1206, 1.50 A rms shared four ways) and C9
    # (100 nF at the pin, innermost element of the hot loop) are recorded as
    # decoupling associations against U1 pin 2; C4 is NOT (it must stay
    # >= 12 mm away, constraints.json separation) and C1 is NOT (BST->SW is
    # not a rail+gnd pair).
    sh.place_ic_with_decoupling(
        "U1", S_U1, "AP64350SP-13", at=(190.50, Y_MAIN), footprint=F_SO8EP,
        pins={"1": "BST", "2": "+VIN", "3": "EN", "4": "RT", "5": "FB",
              "6": "COMP", "7": "GND", "8": "SW", "9": "GND"},
        expect={"1": "BST", "2": "VIN", "3": "EN", "4": "RT", "5": "FB",
                "6": "COMP", "7": "GND", "8": "SW", "9": "EP"},
        decoupling=[
            {"cap": "C5", "pin": "2", "rail": "+VIN",
             "value": "4.7uF 50V X7R", "lib_id": S_C47U, "footprint": F_C1206},
            {"cap": "C6", "pin": "2", "rail": "+VIN",
             "value": "4.7uF 50V X7R", "lib_id": S_C47U, "footprint": F_C1206},
            {"cap": "C7", "pin": "2", "rail": "+VIN",
             "value": "4.7uF 50V X7R", "lib_id": S_C47U, "footprint": F_C1206},
            {"cap": "C8", "pin": "2", "rail": "+VIN",
             "value": "4.7uF 50V X7R", "lib_id": S_C47U, "footprint": F_C1206},
            {"cap": "C9", "pin": "2", "rail": "+VIN",
             "value": "100nF 50V X7R", "lib_id": S_C100N,
             "footprint": F_C0603},
        ],
        caps_at=(_col(3.25), Y_IN), caps_dx=DX)
    # place_ic_with_decoupling takes no `fields`, so stamp LCSC afterwards
    # (rf-de-20m P4 review E5: the IC and its decouplers otherwise reach P9
    # with no ref->LCSC mapping at all).
    for ref in ("U1", "C5", "C6", "C7", "C8", "C9"):
        sh.sch.components.get(ref).set_property("LCSC", LCSC[ref])

    # L1: 6.8 uH molded alloy-composite, DCR 18.5 mohm max at 20 C
    # (24.05 mohm hot, under the 25 mohm ceiling).  /SW -> +5V.
    add(S_L1, "L1", "6.8uH", (266.70, Y_MAIN), F_IND,
        {"1": "SW", "2": "+5V"})
    add(S_J, "J2", "SCREW_5.08_2P", (317.50, Y_MAIN), F_CONN,
        {"1": "+5V", "2": "GND"}, dnp=True,
        note="DC OUTPUT 5V 3A, RIGHT short edge. DNP for assembly (Q25)")

    # ============================================================ B1/B2 row
    # C4 bulk: ESR 50-300 mohm is a REQUIREMENT, not a loss - it damps the
    # hot-plug LC ring at U1's VIN pin from 25.4 V to ~20 V.  Do NOT swap for
    # a low-ESR polymer.  POLARITY: symbol pins are generic "1"/"2"; the
    # FOOTPRINT silk carries +/- with PIN 1 = POSITIVE.
    add(S_CBULK, "C4", "100uF 35V 80mOhm", (X0, Y_IN), F_CBULK,
        {"1": "+VIN", "2": "GND"}, expect={"1": "1", "2": "2"},
        note="pin1=+ per FOOTPRINT silk; symbol pin names are non-polar")
    add(S_R100K, "R1", "100k 1%", (_col(1), Y_IN), F_R0603,
        {"1": "QGATE", "2": "GND"},
        note="Q1 gate pull to GND + polarity-reversal turn-off path")
    # D2 zener: CATHODE (pin 1, name K) at the SOURCE (+VIN), ANODE (pin 2,
    # name A) at the GATE.  Clamps |Vgs| to 15 V against the 25.4 V ring and
    # the +/-25 V Vgs rating.
    add(S_D2, "D2", "BZT52C15 15V", (_col(2), Y_IN), F_SOD123,
        {"1": "+VIN", "2": "QGATE"}, expect={"1": "K", "2": "A"},
        note="Vgs clamp: K at source (+VIN), A at gate (/QGATE)")

    # ============================================================ B3/B4 row
    add(S_C100N, "C1", "100nF 50V X7R", (X0, Y_CONV), F_C0603,
        {"1": "BST", "2": "SW"},
        note="bootstrap, BST->SW; required (datasheet pin 1), not optional")
    add(S_R200K, "R4", "200k 1%", (_col(1), Y_CONV), F_R0603,
        {"1": "RT", "2": "GND"},
        note="RT[kOhm]=100000/fsw[kHz] (Eq.7) -> 500 kHz")
    # ---- Type-II compensation, re-derived: see section 2 of this file ----
    add(S_R, "R5", "75k 1%", (_col(2), Y_CONV), F_R0603,
        {"1": "COMP", "2": "COMPZ"},
        note="Rcomp, Eq.17 at fc=38kHz/COUT=85.2uF -> 75.4k. RE-DERIVED "
             "from the vendor's 14k (which was for a 2x22uF bank)")
    add(S_C33N, "C2", "3.3nF 50V X7R", (_col(3), Y_CONV), F_C0603,
        {"1": "COMPZ", "2": "GND"},
        note="Ccomp, Eq.18 gives 1.9nF; 3.3nF is the sourced part and puts "
             "the zero 643Hz BELOW the 1121Hz load pole (conservative)")
    add(S_C, "C3", "10pF 50V C0G", (_col(4), Y_CONV), F_C0603,
        {"1": "COMP", "2": "GND"},
        note="Eq.19 COMP HF pole (8.5pF -> 10pF, fp=212kHz). NOT the Eq.20 "
             "feedforward sheets.md names - see gen/root.py s2.4")
    # ---- EN / UVLO: 6.23 V rising, 5.33 V falling.  See section 3. -------
    add(S_R105K, "R2", "105k 1%", (_col(5), Y_CONV), F_R0603,
        {"1": "+VIN", "2": "EN"},
        note="UVLO top, datasheet Eq.2 -> VON 6.23V")
    add(S_R24K, "R3", "24.0k 1%", (_col(6), Y_CONV), F_R0603,
        {"1": "EN", "2": "GND"},
        note="UVLO bottom, datasheet Eq.3 -> VOFF 5.33V, 0.90V hysteresis")
    # ---- B9 DNP snubber: must EXIST in the netlist so its pads, clearance
    # ---- and routing are accounted at P6/P7 (sheets.md s5 item 5).
    #
    # UPSIZED TO 1206 AT THE P4 REVIEW.  An RC snubber dissipates C*V^2*fsw
    # in its RESISTOR, all of it, every cycle - the R value does not appear.
    # As first drawn (1 nF, 0603 rated 0.1 W) that is 1e-9 * 18^2 * 500e3 =
    # 162 mW at the 18 V line and 1e-9 * 26^2 * 500e3 = 338 mW against the
    # 26 V hot-plug ring: 1.6x and 3.4x over the part's own rating, i.e. the
    # DNP part would burn if anyone ever populated it, which is the whole
    # point of fitting the footprint.  Both parts move to 1206.
    #
    #   R9  22 R 1% 1206, 0.25 W   - SAME 22 R (geometric mean of blocks.md
    #                                B9's documented 10-33 R range)
    #   C16 470 pF C0G/NP0 1206    - LOW END of blocks.md B9's documented
    #                                470 pF - 2.2 nF range, not a new value
    #
    # Now 470e-12 * 18^2 * 500e3 = 76 mW (30% of the 0.25 W rating) and
    # 470e-12 * 26^2 * 500e3 = 159 mW on the transient.  C0G/NP0 matters as
    # much as the value: an X7R here would lose capacitance under exactly
    # the DC bias the snubber sees.  Both stay DNP.
    add(S_R22R, "R9", "22R 1% 0.25W", (_col(7), Y_CONV), F_R1206,
        {"1": "SW", "2": "SNUBZ"}, dnp=True,
        note="DNP snubber R across SW-PGND, 1206 0.25W. 10-33R if ever "
             "fitted. No vendor publishes a value - general practice only")
    add(S_C470P, "C16", "470pF 1kV C0G", (_col(8), Y_CONV), F_C1206,
        {"1": "SNUBZ", "2": "GND"}, dnp=True,
        note="DNP snubber C across SW-PGND, 1206 C0G/NP0. 470pF is the low "
             "end of the 470pF-2.2nF range; sets R9 dissipation to 76mW@18V")

    # ============================================================ B5/B6/B7
    # C10-C14: 5x 22uF/25V X7R 1210.  The LOAD STEP sizes this bank, not the
    # ripple.  The 4x floor is authorised, 3x is not - and 5x is what the
    # re-derived loop above is closed against.
    for i, ref in enumerate(("C10", "C11", "C12", "C13", "C14")):
        add(S_C22U, ref, "22uF 25V X7R", (_col(i), Y_OUT), F_C1210,
            {"1": "+5V", "2": "GND"})
    add(S_C47U8, "C15", "4.7uF 16V X7R", (_col(5), Y_OUT), F_C0805,
        {"1": "+5V", "2": "GND"}, note="output HF bypass at the terminal")
    # FB divider, BOTH 0.1% (see section 5).  105k/20.0k is an EXACT 5.2500
    # ratio -> VOUT 5.0000 V nominal, replacing the datasheet Table-1 pair
    # 115k/22.1k whose low corner sat 3.4 mV inside the 4.90 V floor.  The
    # 0.8 V reference tolerance alone (792-808 mV) already spends 60% of the
    # +/-2% window, so 0.1% is mandatory, not gold-plating (SIM-1).
    add(S_R, "R6", "105k 0.1%", (_col(6), Y_OUT), F_R0603,
        {"1": "+5V", "2": "FB"},
        note="FB top, 0.1% MANDATORY. Vout=0.8*(1+105/20.0)=5.0000V exactly")
    add(S_R, "R7", "20.0k 0.1%", (_col(7), Y_OUT), F_R0603,
        {"1": "FB", "2": "GND"},
        note="FB bottom, 0.1% MANDATORY. Divider current 40uA")
    # B7 indicator: ~1 mA.  (5 V - 2.8 V Vf)/2.2k = 1.0 mA.
    add(S_R2K2, "R8", "2.2k 1%", (_col(8), Y_OUT), F_R0603,
        {"1": "+5V", "2": "LEDA"}, note="LED series, ~1mA")
    add(S_LED, "D1", "GREEN", (_col(9), Y_OUT), F_LED,
        {"1": "LEDA", "2": "GND"}, expect={"1": "A", "2": "K"},
        note="output-live indicator, anode=pin1")

    # ================================================================ B8
    # Test pads are REAL nets.  TP7 is a SECOND ground pad placed ~5 mm from
    # TP3 for a scope spring ground - not a duplicate of TP6 (sheets.md s5.6).
    for i, (ref, net, why) in enumerate((
            ("TP1", "+VIN", "protected input rail"),
            ("TP2", "SW", "switch node - stub counts against the 40mm2 "
                           "SW area ceiling"),
            ("TP3", "+5V", "output"),
            ("TP4", "FB", "feedback - HIGH-Z, probe loading shifts the "
                           "setpoint"),
            ("TP5", "EN", "enable - test pad only, never user-driven"),
            ("TP6", "GND", "ground reference"),
            ("TP7", "GND", "DEDICATED low-inductance scope-ground pad, "
                           "~5 mm from TP3"))):
        sh.add_component(S_TP, ref, net, at=(round(X0 + i * 15.24, 4), Y_TP),
                         footprint=F_TP, fields={"Note": why})
        sh.wire_pin(ref, "1", net)

    # Mounting holes: unplated 3.2 mm M3, ISOLATED from GND (sheets.md s3),
    # so the ZERO-pin symbol, not MountingHole_Pad.
    for i, ref in enumerate(("H1", "H2", "H3", "H4")):
        sh.add_component(S_HOLE, ref, "M3_3.2mm",
                         at=(round(171.45 + i * 19.05, 4), Y_TP),
                         footprint=F_HOLE)

    # =========================================================== power rails
    # Power SYMBOLS make these nets GLOBAL and BARE.  A local label would
    # export "/+VIN" and silently break five constraints.json matches
    # (sheets.md s2 rule 1).  The symbol's VALUE is what names the net, and
    # schlib.power_flag sets it from the net argument, so `power:VBUS` with
    # Value "+VIN" exports a bare "+VIN" (LEARNINGS 2026-07-28).
    #
    # PWR_FLAG on all three: every power symbol's own pin is power_in, so
    # each of these nets needs a driver ERC can see.  GND additionally
    # carries U1's GND pin and exposed pad (both power_in), +VIN carries
    # U1 VIN (power_in), and +5V's only source is L1, a passive.
    sh.power_flag("GND", at=(X0, Y_PWR), sym="power:GND", flag=True)
    sh.power_flag("+VIN", at=(101.60, Y_PWR), sym="power:VBUS", flag=True)
    sh.power_flag("+5V", at=(158.75, Y_PWR), sym="power:+5V", flag=True)
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


# Q1 is the only part on the sheet with several pins stubbing the SAME way at
# the symbol's own 2.54 mm pin pitch (4 drains up, 3 sources down).
# `schlib.wire_pin` writes every local label at rotation 0, so those seven
# horizontal texts print on top of each other.  Rotating them to run ALONG the
# stub (schlib._label_rotation's convention: up-stub 90, down-stub 270) is a
# text-angle change only - the anchor, and therefore the connectivity, is
# untouched.  Coordinates are derived from Q1's anchor so they follow it.
Q1_AT = (_col(2.75), Y_MAIN)
Q1_LABEL_ANGLES = (
    [((round(Q1_AT[0] + dx, 4), round(Q1_AT[1] - 10.16, 4)), 90.0)
     for dx in (-2.54, 0.0, 2.54, 5.08)]                       # drains, up
    + [((round(Q1_AT[0] + dx, 4), round(Q1_AT[1] + 10.16, 4)), 270.0)
       for dx in (-2.54, 0.0, 2.54)])                          # sources, down


def rotate_labels(path: Path, targets) -> int:
    """Set the text angle of the local labels anchored at `targets`."""
    re_ = __import__("re")
    text = path.read_text(encoding="utf-8")
    want = {(round(x, 4), round(y, 4)): a for (x, y), a in targets}
    done = 0

    def sub(m):
        nonlocal done
        key = (round(float(m.group(2)), 4), round(float(m.group(3)), 4))
        if key not in want:
            return m.group(0)
        done += 1
        return f'{m.group(1)}(at {m.group(2)} {m.group(3)} {want[key]:.4f})'

    text = re_.sub(r'(\(label "[^"]+"\s*)\(at ([\d.]+) ([\d.]+) [\d.]+\)',
                   sub, text)
    if done != len(want):
        raise ValueError(f"rotate_labels: matched {done} of {len(want)} "
                         f"label anchors - the layout moved")
    path.write_text(text, encoding="utf-8")
    return done


def align_variant_fields(path: Path) -> int:
    """Park every instance `Variant` field one line BELOW its own Value.

    `schem_refdes` (run inside Sheet.save) re-places Reference and Value only,
    so `Variant` keeps the library's default offset - which for the DB128L
    connector symbol coincides with the re-placed Value and prints
    "SCREW_5DNE_2P" on the plot.  Variant=DNP is the only do-not-populate
    marking a generator can emit and J1/J2's DNP status is load-bearing
    (hand-soldered on receipt), so it must be legible.  Electrically inert -
    field positions do not reach the netlist.  Idempotent.
    """
    text = path.read_text(encoding="utf-8")
    at_re = __import__("re").compile(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)')
    out, pos, moved = [], 0, 0
    needle = '(property "Variant"'
    while True:
        i = text.find(needle, pos)
        if i < 0:
            break
        v = text.rfind('(property "Value"', 0, i)
        if v < 0:
            raise ValueError("Variant field with no preceding Value field")
        m = at_re.search(text, v, _match(text, v))
        if not m:
            raise ValueError("Value field carries no (at ...)")
        x, y, ang = float(m.group(1)), float(m.group(2)), m.group(3)
        end = _match(text, i)
        node = text[i:end]
        new = at_re.sub(f"(at {x:g} {y + 2.54:g} {ang})", node, count=1)
        moved += new != node
        out.append(text[pos:i] + new)
        pos = end
    out.append(text[pos:])
    new_text = "".join(out)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return moved


def hide_aux_fields(path: Path) -> int:
    """`(hide yes)` on every non-VISIBLE property.  The fields must EXIST
    (P9 reads LCSC off them) but kicad-sch-api gives every generator-written
    field VISIBLE effects, which prints ~30 LCSC codes and ~25 notes on top
    of the parts they belong to and makes the plot unreadable.  Hiding is a
    plot property only - exactly the form KiCad itself writes for Footprint
    and Datasheet.  Idempotent."""
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
    out_dir = Path(argv[0]) if argv else HERE.parents[1]      # .../kicad
    try:
        sh = build()
        sch = sh.save(out_dir, project=True)
        rotated = rotate_labels(sch, Q1_LABEL_ANGLES)
        variants = align_variant_fields(sch)
        hidden = hide_aux_fields(sch)
        meta = sh.emit_decoupling(out_dir / "decoupling.json")
    except Exception as exc:                # noqa: BLE001 (SPEC 6: error -> 2)
        print(json.dumps({"script": "gen.sbuck-5v3a", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}))
        return 2
    print(json.dumps({
        "script": "gen.sbuck-5v3a", "status": "pass",
        "files": [str(sch), str(out_dir / "sbuck-5v3a.kicad_pro"), str(meta)],
        "components": len(sh.sch.components),
        "decoupling_associations": len(sh.decoupling),
        "fields_hidden": hidden,
        "variant_fields_aligned": variants,
        "labels_rotated": rotated,
        "field_placement": sh.place_report,
    }, indent=1, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
