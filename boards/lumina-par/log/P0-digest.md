# P0 Intake digest - lumina-par (LUM-DTR-PAR-A / LUM-PAR-A)

- Board: RGBW par daughter for LUM-CAR-A. 4 (maybe 5) PWM-dimmed constant-current LED
  channels, stacked 11.0 mm above the carrier on the frozen ICD-01 connector pair.
  Continuous duty; the design problem is dimming quality and fixture-to-fixture colour
  consistency, not peak power.
- Inherited as CLOSED (05-lumina-closed-decisions.md): D-01 (at-capable stage, af-classified;
  budget 8.6-9.3 W af / 18.7-20.0 W at to this daughter - the "~8.5 W" and "~10 W regulated"
  figures in briefs 00/03 are dead), D-02 (48 V + 12 V + 3.3 V on the connector), D-03 (no UV).
- ICD-01 is a frozen hard input. All interfaces are ICD-only: J3 2x7 power, J4 2x12 signal.
  ICD s9 forbids adding an external connector of any kind. Common footprint 100 x 80 mm,
  R3.0, 5x M3, 1.6 mm, plus a mandatory 30 x 26 mm RJ45 notch at (6,0)-(36,26).
- Safety flags: >30 V unconditional (48 V present on J3 whether tapped or not - 0.60 mm outer
  clearance, 100 V caps, 0805+ resistors across the 48 V domain); whole fixture floats at PoE
  potential including LED wiring and any heatsink; >3 A conditional on per-channel LED current
  that P1/P2 must publish.
- Riskiest unknowns, in order: (1) af-vs-at sizing - +12V tops out at 15.0 W so at-sizing forces
  a >=60 V stage on THIS board, the exact thing D-02's 12 V rail existed to avoid; (2) continuous
  thermal in a non-conductive enclosure at 56-69 C internal air; (3) PAR-REQ-01's "5-10 % of full
  output" is ambiguous and changes the required driver settling time by ~40x.
- Hard derived requirement recorded: the board must be electrically incapable of exceeding the
  carrier's fault ceilings (12 V OCP 2.0 A, 48 V eFuse 1.0 A latch-off) with every PWM stuck at
  100 %, because the PAR-REQ-11 clamp is firmware and firmware hangs.
- Pipeline risk logged for P5: `board_init.py` has no notch/cutout option and `kc.py` has no
  outline editor, so the mandatory RJ45 relief needs a direct Edge.Cuts edit after board_init;
  and `--mounting-holes` places holes at margin/2, so the ICD's 5 mm inset needs `--margin 10`.
- Artifact: `requirements.md` (9 sections, 16 open questions, all with recommendations).
