# Board review: usb-buck (adversarial, P8)

Reviewer stance: machine gates are green (DRC 0/0 incl. warnings, verify 8/8
checks 0 findings, ERC 0/0); hunt only for what those checks cannot see.
Evidence: fresh renders reports/renders/usb-buck_{top,bottom,iso}.png at
2400 px plus close-up crops (crop_usb.png, crop_buck.png, crop_u1.png,
crop_right.png, crop_bottomui.png); SWIG geometry interrogation of
kicad/usb-buck.kicad_pcb (pads, tracks, vias, zones, silk inventory,
collinear-overlap scan); requirements.md, architecture/*, constraints.json,
reports/erc-waivers.md, reports/review-schematic.md, kicad/decoupling.json.

Verdict: 1 error, 4 warnings. The electrical design is delivered and the
layout fundamentals (buck hot loop, ESD flow-through, plane discipline,
decoupling ring) are genuinely good. The error and two of the warnings are
"assembly/field reality" defects invisible to every script in the suite.

## Findings, worst first

### E1 - J2 SWD header has no silkscreen pin labels (error)

The board's ONLY silk text is 28 refdes strings. requirements.md s2 promises
the SWD pinout is "silkscreen label[ed]"; architecture/blocks.md (Debug)
orders "Silkscreen every pin" and explains why: pin 1 carries +3V3 as a
REFERENCE OUTPUT and "powering the board from the debugger would back-drive
the buck output". As built (crop_right.png), pin 1 is marked only by a square
THT pad - invisible once the header is soldered - and nothing identifies
SWCLK/GND/SWDIO. A user with a clone ST-Link (whose 3.3V pin SUPPLIES power)
has a 50% chance of connecting the ribbon reversed: SWDIO->3V3 backfeeds the
rail, debug fails, and the AP63203 output is back-driven. Minutes to fix
(four silk labels + a pin-1 tick), and check_silk can never see it - it
checks geometry, not meaning.

### W1 - USB mouth recessed ~0.5 mm behind the board edge (warning)

J1's mating face sits at board x=11.0 vs edge x=10.54 (courtyard/silk front
transformed from the footprint; no F.Fab body outline exists to be more
precise). crop_usb.png shows the PCB lip clearly in front of the connector
mouth. A micro-B plug must insert ~4.85 mm and compliant plugs expose ~6.5 mm
of shell, so ~1.5 mm of slack absorbs this for most cables - but short-shell
or chunky-overmold cables will bottom on the lip before the latch engages:
intermittent contact, cable falls out. Standard practice is mouth flush to
+0.5..1 mm proud. Shift J1 -0.5..-0.8 mm in x at the next spin (the placer
respected courtyard-to-edge clearance where a connector wants overhang).

### W2 - J1 shield pegs and J2 leave JLC economy assembly unsoldered (warning)

JLC economy PCBA is SMT-only. J2 (THT header) is planned as hand-solder
per architecture - fine, bottom side is bare and access is excellent
(usb-buck_bottom.png). But J1's four shield legs are PTH pads (2x round
0.7 mm, 2x slot 1.3x0.5 mm, all net GND) and NO document calls out soldering
them. Fresh from assembly, the shield-to-GND bond (decision 5) and nearly all
of the jack's rip-off retention hang on unsoldered pegs in plated holes; the
SMD signal pads alone will not survive cable side-loads for long. Failure:
shield ground goes intermittent, then the jack tears off. Needs one line in
the bring-up/assembly instructions: hand-solder J1's 4 pegs + J2's 4 pins.
(The two 0.5 mm-wide slots sit exactly at JLC's minimum slot width - inside
capability, zero margin; dfm_check in S12 must confirm.)

### W3 - diff-pair constraint relaxation is defensible; its justification is flattering (warning)

max_uncoupled_mm 5.0->8.0 was corrected to pass the measured 6.61 mm
uncoupled span. Geometry audit: the USBLC6-2SC6 traverse genuinely forces
~3.4-3.6 mm of separation (GND pin 2 sits BETWEEN D-/D+ on the entry side;
pads 1.9 mm apart > the 1.56 mm coupling window) - unavoidable with this
part, as claimed. The "2.9 mm D+ pull-up stub" measures 3.16 mm
junction->R4.1, and ~1.5 mm of it IS avoidable: R4's D+ pad is currently the
FAR pad (y38.35); rotating R4 180 deg puts it at y36.85. Additionally the
"coupled" remainder runs at 0.71-1.25 mm centre-to-centre against the 0.52 mm
90-ohm geometry (gap_min 0.50 exists only near J1), so blocks.md's "90 ohm
pair" is nominal, not delivered. Verdict: ACCEPT for USB full-speed - 12 Mbps
/ 4 ns edges over a ~12 mm run above an unbroken In1 GND plane makes all of
this immaterial (skew 1.93 mm = 13 ps is noise). Keep 8.0 mm for THIS board;
do not let this constraints.json travel to any high-speed design, and drop
the "zero avoidable meander" framing - R4's orientation was avoidable.

### W4 - D1 interior silk glyph contradicts the correct chamfer cathode cue (warning)

LED-SMD_L1.6-W0.8-R-RD footprint: the outline chamfer correctly marks the
cathode end (pad 2, matches netlist - cathode to PC13 sink, anode via R1 to
+3V3; crop_bottomui.png), and it remains visible after assembly. But the
interior glyph draws its polarity bar at local x=+0.09 with the tick toward
-x - it reads as "cathode at the ANODE end". The glyph hides entirely under
the 1.6 mm body once placed, so machine assembly (CPL-driven) and post-
assembly inspection are safe. The exposure is hand-rework: with D1 removed, a
tech who trusts the interior bar mounts the replacement backwards - LED dead
(no damage, diode blocks). Low risk at qty 10; fix the glyph in the footprint
at next touch. (fp_verify's 0.8 vs 0.7 mm pad-size warning is a deliberate,
benign enlargement - triaged, no action.)

## Positively verified (not just "no finding")

- ESD sequencing: J1 (x16.3) -> U3 (x19.1-21.4) -> U1 (x26.75); true
  flow-through (entry/exit trace runs pad-to-pad under the SOT-23-6 body);
  U3 GND drops to the In1 plane via at (18.45,34.25), 0.65 mm from pin 2 -
  exactly the architecture's promise.
- Buck hot loop (crop_buck.png): C2 100nF 1.6 mm from VIN pin 3 with its GND
  via 0.65 mm away; C1 10uF immediately behind; loop closes into In1 within
  ~2x2.5 mm. SW node is one 2.15 mm trace to L1 plus the 3.4 mm BST-cap leg -
  tight and short for a 1.1 MHz sync buck. Output caps C4/C5 flank L1
  symmetrically. C2 placement matches the layout note in blocks.md/power_tree.
- Planes: In1 = solid GND, In2 = +3V3, both filled, only 3 tracks on B.Cu
  (SWDIO run, VBUS underpass) - the underpass's two vias sit 0.7 mm from the
  D- line but two planes below it; return-path check (radius 2.0) green.
- Crystal: Y1 (HC-49S) is 7.6+ mm from the buck bbox and >16 mm from edges;
  load caps C10/C11 at the crystal pads with GND vias 0.65 mm out; OSC_IN/
  OSC_OUT diverge immediately (no long parallel run); SWCLK passes no closer
  than ~1.3 mm north of the can. OSC traces are 11.9/12.6 mm - long-ish, the
  price of the physically huge HC-49S; acceptable at 8 MHz over solid GND.
- Placement contracts: J1/J2 on left/right edge at pos 0.5; buck group vs
  USB group separation 9.8 mm (>= 8 required); board 50.1 x 40.1 mm inside
  the 55 x 45 cap; single-sided SMT assembly delivered (bottom bare).
- VBUS after P7 dedup: zero exact duplicates board-wide; VBUS itself also
  free of partial overlaps. (22 micro-overlaps of 0.2-0.34 mm remain at
  via junctions on GND/+3V3/D- - source-file cosmetics; copper unions in
  gerbers, no fab impact.)
- Pin-1 cues: silk dots present and post-assembly-visible for U1, U2, U3;
  refdes all 1.0 mm, none obscured by parts (renders).
- U1.8/U1.9 escape co-design at (36.3-36.4, 32.9-33.2): VSSA drops to plane
  at (36.35,33.17), VDDA exits at y32.67 - 0.3 mm edge gap, no sliver.
- Decoupling ring: C12/C13/C14 hug their VDD pins, C16+C17 on VDDA by pin 9,
  C18 on VBAT, C15 bulk 6.6 mm off pin 48 (fine for bulk), C19 NRST cap
  7.5 mm from pin 7 (filter still effective; cosmetic).
- Cross-artifact: every requirements.md interface exists on copper (USB
  device w/ ESD, SWD, LED, button, crystal, AP63203 buck); every blocks.md
  block placed; VBUS carries exactly the "only capacitance allowed" set.

## Warnings triage (every non-green anywhere gets a verdict)

- Schematic review W1 (SW1 pairing unverified): layout is consistent with
  the assumed {1,2}/{3,4} pairing (top row = BTN + R2, bottom row = GND
  vias); if pairing is actually left/right the button reads stuck-pressed -
  exactly the waived failure mode. Waiver SOUND; bring-up continuity check
  pins 1-3 remains MANDATORY.
- Schematic review W2 (UMW USBLC6 clone VRWM 5.0 V vs 5.25 V): unchanged by
  layout; waiver SOUND for qty 10; ST original (C7519) swap remains the
  order-time option - carry to S12 BOM.
- fp_verify D1 pad-size warning: deliberate 0.05 mm/side enlargement,
  benign (see W4 for the real D1 issue).
- Historical diffpair error (6.61 > 5.0): superseded by the corrected
  constraint - judged in W3.
- Skipped checks: none within the P8 suite (8/8 board checks ran). The
  remaining hole is downstream: dfm_check / BOM-CPL validation (S12) has not
  run - slot-width minimum, Extended-part status of J1/U2/U3, and CPL
  rotation for the polarized D1 are all still machine-unverified.

## Open (could not judge from renders/geometry alone)

- Whether JLC will place J1 (C2939564, Extended SMD) on economy PCBA and
  whether any paste-in-hole occurs on its peg holes - S12 territory.
- Actual latch engagement of a worst-case micro-B cable against the 0.5 mm
  lip (W1) - needs a physical plug test on the v1 article.
- SW1 internal pairing (W1 waiver) - electrical bring-up only.
