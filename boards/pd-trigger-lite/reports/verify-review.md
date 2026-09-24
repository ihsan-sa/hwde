# pd-trigger-lite - P8 verify review (H4), 2026-09-24

Verdict: **approved**. 0 errors, 0 warnings raised by this review; the 17
check_current advisories are waived below. No design files changed.

Renders: `reports/pd-trigger-lite_top.png`, `reports/pd-trigger-lite_bottom.png`.

## 1. 3 A path (J1 -> J2)

- VBUS: a solid-connected F.Cu pour band (y 33.09-37.49) from both J1 VBUS
  pads to J2 pad 1. Measured filled cross-section along x: >= 4.06 mm from
  x 26.65 to 40.4 mm; 2.2-2.8 mm at J1, where it splits round the CC pads into
  two ~1.2 mm strips, one per VBUS pad (~1.5 A each, < 1.5 mm long); 2.4 mm
  past the J2 hole. The only 1.25 mm track is R7's feed to /VHV (mA). Adequate.
- GND: a B.Cu plane over almost the whole board. J1 A12/B12 reach the four
  plated shell pads through 0.8 mm x 1.2 mm tracks (~1.5 A each), and the
  shell pads join the plane with 3-4 x 0.5 mm thermal spokes each. J2 pad 2
  joins with 4 x 0.5 mm spokes (2 mm of copper, 0.5 mm long). The plane is
  continuous between the rear shell pads and J2; the CFG1 bottom track at
  x 22.97 only fences off the front shell pads, which carry no extra load
  current.
- Warning triage (all waived): 10 x 0.25 mm GND stubs to the JP1-3/R5
  lands (CFG1 current, uA), the D1 cathode (~1.8 mA) and C1 (mA); 2 x 0.8 mm
  J1 GND tracks (1.5 A each over 1.2 mm; IPC wants ~0.5 mm); 5 via-count
  advisories on those same mA taps and U1's EP. None sits on the 3 A path.

## 2. CPL / BOM

- U1, J1 and D1 footprints are easyeda2kicad imports of JLC's own library,
  so JLC rotation = KiCad rotation. U1 at 90: pin 1 bottom-right, matching
  the silk dot. J1 at 270: mouth faces -x, flush with the left edge
  (courtyard front at x 18.42 = board edge). D1 at 180: pad 2 (K, symbol pin 2)
  on GND at the right and pad 1 (A) fed by R6. Correct.
- BOM and CPL both list the same 11 placed parts (C1, D1, J1, R1-R7, U1).
  Footprint names match the PCB. J2 (wire holes) and JP1-3 (open links) are
  correctly left out.

## 3. Silk and voltage table

- Schematic/PCB nets: R1 6.8k/SEL9/JP1, R2 24k/SEL12/R5, R3 56k/SEL15/JP2,
  R4 120k/SEL20/JP3, all from CFG1 to GND. That matches CH224 manual
  table 5-1 (6.8k=9 V, 24k=12 V, 56k=15 V, 120k=20 V). The "9 12 15 20 V"
  labels sit under the x = 27.27/29.27/31.27/33.27 columns, which are
  JP1/R5/JP2/JP3.
- "+" is beside the square pad 1 (VBUS) and "-" beside pad 2 (GND). Correct.
- The CH224A pinout (1 VHV, 8 VBUS tied to VHV, 9 CFG1, 6/7 CC2/CC1, EP GND)
  matches the manual.

## 4. Other arrival risks (none blocking)

- JP1-3 use R0603 lands with paste, so they arrive pre-tinned. That helps a
  solder bridge.
- The three EP vias under U1 are untented via-in-pad and may wick a little
  solder. That's common at this size and not a failure.
- The guide already tells the user to remove R5 before choosing another
  voltage. Leaving R5 fitted with a second link bridged would request an
  undefined Rset.
