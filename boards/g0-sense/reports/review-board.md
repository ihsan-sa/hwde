# Board review - g0-sense (P8 verify-reviewer, adversarial pass, 2026-08-27)

Board digest reviewed: sexpr_no_uuid:9fa76a1b (matches checks/summary.json and the
waiver binding). Renders made for this review: reports/renders/g0-sense_top.png,
reports/renders/g0-sense_bottom.png, reports/renders/g0-sense_iso.png (2400 px).
All 8 verify checks RAN (skipped_error empty - no coverage holes). kicad-cli DRC:
0 violations, 0 unconnected. Every measurement below was re-taken by me from the
board file with pcbnew, not inherited from the authors.

Verdict up front: NO error-severity findings. This board can go to fab once the
silk cleanup below is done (recommended, not blocking). The one waiver is honest
and should be ratified. Three new warnings, worst first.

## Findings (worst first)

### W-1 (warning, silk): J3/J4 per-pin function labels promised by the
### architecture are absent
blocks.md ("Headers + indicators") promises the SWD and UART headers
"silk-labeled per pin" with pin 1 silk-marked. The board delivers refdes J3/J4,
a pin-1 square pad plus a silk dot on each - and NO per-pin GND/3V3/SWDIO/SWCLK
or GND/3V3/TX/RX labels (verified: the only silk text items on the whole board
are refdes plus C3's "+"; see top render, top edge). These are the two headers
the owner hand-solders and hand-wires; they are visually identical 1x4 0.1 in
headers with the same GND-at-pin-1, 3V3-at-pin-2 convention. Consequence: the
mixup that convention was designed to prevent (wiring a UART dongle's 5 V or
swapping GND/3V3 by counting pins from the wrong end, or confusing SWD with
UART) is left to documentation the bare board does not carry. Cheap fix at P9:
eight small text items along the top edge; ample empty silk space exists there.
Cross-artifact drift: the architecture REQUIRED this; product scope makes its
absence a finding, not a nit.

### W-2 (warning, silk): 6 misattributed refdes labels, several of which are
### also COVERED by parts after assembly - fix, do not waive
check_silk's 6 warnings are all real, and four are worse than the checker says
because the text lands where a component body will be:
- R1 (24.82,40.55) and R2 (24.82,42.75): inside J1's shell region (J1 courtyard
  to x=26.32) - covered by the USB-C shield after assembly AND read as J1's
  label (top render: text on the connector).
- C10 (36.67,36.00): inside U2's silk body outline (35.51..39.20 x
  33.09..39.91) - under the TSSOP after assembly.
- D1 (35.60,42.60): inside U1's silk outline - reads as U1's label; the TVS
  itself is left with no visible refdes, which is exactly the part a rework
  tech must not confuse.
- D2 (43.25,42.92): 0.12 mm from C3 - reads as the tantalum's label (top
  render: "D2" sits over C3, whose own label is off to the right).
- R10 (47.03,35.90): reads as D10's label; D10's own text drifted to
  (49.98,39.50) at the slot mouth. Related uncounted case: C13's refdes sits at
  (52.60,36.23), separated from C13 (on the tongue at 52.60,39.60) by the top
  slot, and it crowds the H2 label.
Consequence: debugging and rework against the silk misidentify parts;
assembly itself is unaffected (JLC places from CPL). Severity warning is
correct. Disposition: one place_edit.py move_text batch at P9 - silk-only,
zero copper risk - NOT a waiver. (Per the rules I did not run silk_place.py or
edit anything.)

### W-3 (warning, fab): panelization tabs on the sensor tongue edge would
### stress the cantilever - put a remark on the JLC order
The tongue's outer face (x=54.75, y 38.05..44.95) is a board edge. JLC economy
panelizes internally; a break-off tab or mouse-bite row landed on the tongue
tip would transmit snap force through the 6.9 mm root while U3 rides the beam.
The tongue itself is stubby and strong (5.5 mm long, 6.9 mm wide root, 1.6 mm
FR-4 - aspect ratio < 1; it will survive normal handling and depanelization
fine), so this is only about where a tab lands. P9 disposition: add the JLC
order remark "no break-off tabs / mouse bites on the right-edge sensor tongue
(x 49.25-54.75 span)"; the same remark block already owed for the Sensirion
no-wash rule (blocks.md B4) is the natural place.

## The five load-bearing judgment calls, re-examined adversarially

### 1. Pour-carried VBUS at J1 - VERIFIED, acceptable
I rebuilt the VBUS copper union (fills + pads + tracks) per layer with pcbnew
and eroded it 0.4 mm myself:
- F.Cu: the corridor from J1's lower VBUS pad-pour (B4A9 zone) to F1 pin 1
  survives as ONE outline containing the bottom via cluster and the PTC input
  - the primary current path is >= 0.8 mm wide with no via dependency at all.
- B.Cu: the 0.8 mm bridge survives 0.395 mm erosion as one outline containing
  all 6 VBUS vias (3-via cluster each end, 0.6/0.3 mm), and vanishes at
  exactly 0.400 mm - it is exactly the netclass width, no more.
- The only sub-0.8 necks are the 0.6 mm vendor pads themselves and the C1
  decoupling stub - unavoidable pad geometry and a no-current stub.
check_current PASS concurs (min B.Cu 0.8, +5V F.Cu 1.2, 2 via clusters).
Nothing else about the connector entry worries me: mating face proud of the
outline by 0.08 mm (courtyard 18.88 vs edge 18.96), the 4 THT shield legs are
on GND net into the B.Cu pour, D+/D-/SBU have no nets, CC1/CC2 land on
independent 5.1k R1/R2, and the ~13 mm swath at the left edge holds only
sub-1.5 mm-tall passives (iso render). Pour-carried VBUS on a 1.5 A-fault
budget with a fill saved in the file that DRC checks is sound engineering
here, not a dodge.

### 2. The check_thermal waiver on U1 - HONEST; recommend RATIFY at checkpoint 4
I recomputed the checker's own model at the two vendor anchor points:
theta_JA(100 mm2) = 55 + 119*exp(-100/350) = 144.4 C/W where AMS measured 80;
theta_JA(194 mm2) = 123.3 C/W where TI measured 84. The model is 40-64 C/W
pessimistic exactly where measured data exists, and it credits nothing for
backside spreading - while I verified 810.9 mm2 of solid B.Cu GND copper
(713.7 main + 47.5 + 49.7 strips) sits directly under and around U1. The Tj
arithmetic checks: 40 C + 0.51 W x 84 C/W = 82.8 C governing case, 109.7 C at
the 0.83 W entitlement-abuse case, both under the 125 C limit. The
"unreachable by construction" claim is internally consistent: passing needs
>= 446.8 mm2 credited (my recomputation of the model inverse; waiver says
446.4) against a measured 439.9 mm2 whole-board ceiling. The waiver also did
real work instead of hiding (pour grown 171 -> 250 mm2 credited) and refused
copper that would have carved the B.Cu return plane or walked heat to the
sensor tongue - the right priority order. Binding to digest 9fa76a1b and
checker_version 1 is correct hygiene. One residual honesty note: at sustained
heavy Qwiic load the LDO pour runs warm and its annex reaches x=48.55, 0.7 mm
from the tongue root strip - the isolation contract still holds (slots + FR-4
gap + 0.15 mm neck), but a firmware-side sanity check of RH readings under
sustained 300 mA load is a sensible bring-up item, not a layout defect.

### 3. SHT40 isolation tongue - REAL, adequate, mechanically sane
Measured myself: pour fill intersecting the tongue rectangle (49.25..54.75 x
38.05..44.95) = 0.0 mm2 on every layer. Exactly 4 tracks cross the root:
+3V3 0.150 mm (y=38.45), GND 0.127 mm (y=40.82), SDA 0.127 mm (y=43.95),
SCL 0.127 mm (y=44.30). Electrical adequacy of 0.127/0.150 mm for the sensor:
worst load is the 75 mA heater pulse; a ~4 mm 0.15 mm 1 oz feed is ~13 mOhm
-> ~1 mV drop, and C13 100 nF sits on the tongue. Fine. Fab floor: 0.127 mm
IS the JLC minimum - deliberate (isolation) and DRC-clean, but zero width
margin; that is the recorded trade, and I accept it. Edge clearances of the
necked tracks to the slots: the +3V3 feed runs 4.8 mm along the top slot at
0.325 mm copper-to-edge (floor 0.30); even JLC's +/-0.2 mm routing tolerance
leaves copper untouched (0.125 mm residual). Within rule; a free 0.1-0.2 mm
inboard nudge at P9 would add margin if a fixer is in the file anyway.
Mechanics: 1.2 mm slots (>= JLC 1.0 mm mill), tongue aspect < 1 - this is a
stub, not a diving board; depanelization/handling risk is W-3's tab-placement
remark, nothing more. B.Cu GND strip islands (y <= 36.5 and y >= 46.5) stay
clear of the tongue and overlap the main pour by 0.4 mm - merged, not orphans.

### 4. Connector reality at 35.79 x 28.34 mm - CLEAN
Verified from renders + geometry: USB-C mates leftward off the board, nothing
in the plug swath; Qwiic J2 opening faces the bottom edge (mech pads at
y=53.54 forward of signal pads at 49.66), opening ~1.3 mm inboard - a JST SH
plug slides over bare mask, acceptable; J3/J4 along the top edge with 2.05 mm
edge setback, hand-solder access unobstructed on both faces; SW1 (5.1 mm,
1.5 mm tall) is 2.3 mm clear of J2 and pressable; U3's aperture faces up with
open air on three sides and nothing tall near the tongue. All four M2 holes
survive with sane screw-head clearance (nearest silk ~0.9 mm at H1/J4).
Simultaneous use of USB + Qwiic + both headers works - three different edges.

### 5. Polarity marks after assembly (feeds the carried P9 CPL obligation) -
### ALL VISIBLE AND CORRECT-SIDED
- C3 tantalum: "+" text at x=40.65, outboard-left of the body; pad 1 (+3V3)
  is the left pad (42.15). Correct side, visible after assembly.
- D1 TVS: cathode double-bar plus dot at the LEFT (x 28.9..29.5), outboard of
  the body; pad 1 = VBUS = left (29.16) = cathode, matching the journal's
  two-way P4 verification. Visible.
- D2 / D10 LEDs: vendor cathode brackets extend beyond both package ends
  (D2 40.16..40.41 left / 43.33..43.58 right; D10 44.63..44.88 / 48.84..49.09)
  - visible after assembly. Nets check: D2 anode=+3V3, D10 cathode=GND.
- U1/U2/U3/J2 pin-1 dots all sit outboard of their bodies. U3's dot pair is
  below-left of the 1.5 mm DFN, off-body.
So nothing here blocks P9; the CPL rotation check for D1/D2/D10/C3 (and I
would add U3 - a rotated DFN-4 swaps SDA/VDD) remains P9's to run, but the
silk it will be checked against is trustworthy.

## Triage of all 7 verify_all warnings (verdict on every one)

1-6. check_silk silk_misattributed (R2, C10, D2, R10, R1, D1): REAL cosmetic
defects - see W-2. Verdict: warning severity stands; FIX at P9 via
place_edit.py move_text; do not waive. Not escalated to error: assembly is
CPL-driven and no electrical consequence exists.

7. check_pdn pdn_no_bulk on VBUS (C1 only, no >= 1 uF): JUSTIFIED WAIVER.
The absence of bulk on VBUS is a binding design rule, not an oversight:
Type-C TC2.0 Table 4-3 caps attach capacitance at 10 uF, and constraints.json
CAP RULE puts the 10 uF (C2) one series element downstream at the LDO input
(F1 out -> C2 is ~4.7 mm of 1.2 mm track; PTC Ri 70 mOhm barely decouples
it). Nothing draws current from VBUS itself - its only consumers are the TVS
and the PTC input. The checker heuristic cannot see the attach-limit rule.
Verdict: justified, document-only, no fix wanted.

## Checked and clear (so the next reviewer does not re-plow)
- Requirements section 2 interface sweep: every promised interface exists and
  is correctly netted (J3 = GND/3V3/SWDIO/SWCLK, J4 = GND/3V3/TX/RX, J2 =
  Qwiic-standard GND/3V3/SDA/SCL, R13 BOOT0 pull-down present, NRST button
  with C12, CC pulldowns independent). U3 pads match the SHT40 pinout
  (SDA/SCL/VDD/GND).
- Value drift vs blocks.md (R12 100R vs 220R, R3 680R vs 620R, D10 0805 vs
  0603): all carried recorded decisions (R12 carries a do-not-delete comment
  per the run journal); LED currents stay in-rating either way. Not drift.
- SW1 internal contact pairing (the classic held-in-reset killer): pads 1+2 =
  NRST row, 3+4 = GND row; the P4 schematic reviewer settled the A/B vs C/D
  pairing against the live-fetched XKB TS-1187A datasheet. Evidence cited in
  the journal; I found no geometry that contradicts it.
- SDA/SCL B.Cu jumpers (~11 mm, paired) carve the return plane locally;
  check_return_path PASS, 400 kHz I2C - harmless on this board.
- Fiducials: none on board; JLC adds panel fiducials for economy PCBA -
  justified omission at this service tier.
- Earned size 35.79 x 28.34 mm compared against the RECORDED decision (soft
  ~35x25 brief preference, extra is the isolation tongue) - not drift, per
  build-mode rules.
- No enclosure is in scope (bare board recorded at requirements Q1), so no
  enclosure-fit comparison exists to fail.

## Recommendations for checkpoint 4 (human verdicts; unattended run records)
1. RATIFY the check_thermal U1 waiver (evidence re-verified independently).
2. ACCEPT pdn_no_bulk as justified-by-design (no waiver file entry needed for
   a warning; this md is the record).
3. ORDER at P9 only after the W-1/W-2 silk batch and with the W-3 order
   remark; none of the three blocks fab if the owner chooses speed over polish,
   but W-1 is the one I would not skip on a product-scope board.
