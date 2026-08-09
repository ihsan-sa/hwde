# P9 DFM digest - sbuck-5v3a

Gate `dfm`: **PASS, 0 failing / 16 total** (16 warnings), measured on gerbers
re-exported after the fixes. 1 of 3 fix-loop attempts used.

## Two real findings, both invisible until the gerbers existed

**1. Silk over the solder-mask opening, 7 test points, 0.1798 mm^2 each.**
My diagnosis was WRONG and the fixer corrected it. I assumed an oversized mask
aperture (~0.92 mm radius). Measured: the aperture is **1.7664 mm^2 = exactly
pi*0.75^2, zero mask expansion**. The real cause is `lib/gerblib.py:read_gerber`
approximating drawn arcs **by their chord** - KiCad exports a full circle as two
180-degree arcs, so both chords collapse onto the DIAMETER, a phantom 1.5 x 0.12 mm
bar through the pad centre. 0.1798 = 1.5 x 0.12 exactly.
My proposed fallback (enlarge the ring) **could never have worked** - the chord runs
through the centre at any radius. Deletion of the 7 decorative rings was the only
board-side fix. The signal-name labels, which carry the actual information, are untouched.

This is a SECOND false positive on the same innocent ring, from a DIFFERENT tool
defect than the P8 `check_silk` one. **Two checkers agreeing was not corroboration.**

**2. Copper clearance 0.0127 mm at (39.67, 51.05).**
Both features were GND. The second was a **0.0029 mm^2 crumb of the priority-0 board
pour**, trapped in the 0.02 mm lane between zone 2's top (51.1) and the P8 Z2's bottom
(51.12). Mechanism: **KiCad deburrs a pour at min_thickness BEFORE subtracting
higher-priority zone outlines**, so a sub-min_thickness lane between two zone outlines
gets refilled and is never deburred away. The P8 "clears zone 2 by 0.02 mm" choice is
exactly what manufactured it. Fixed with a priority-6 GND bridge zone straddling the
seam; a second, longer 0.02 x 1.93 mm hair that nothing had flagged went with it.
F.Cu GND islands 5 -> 4. Min island gap 0.01267 -> **0.1021 mm**.

## Fab package

`fab/`: gerbers + zip, drill, `BOM.csv` (21 rows), `CPL.csv` (29 rows),
`BOM-all.csv` / `CPL-all.csv` (unfiltered, for audit), `DNP-NOT-ASSEMBLED.txt`.
One rotation correction applied against JLCPCB's convention: **Q1 SOIC-8, +270 deg**.
`bom_complete: true`, no missing LCSC codes.

**DNP filtering was done BY HAND** - no script in the pipeline reads a DNP mark, so
left alone JLC would have populated both hand-solder screw terminals and the snubber.
Excluded: J1, J2 (THT, hand-soldered on receipt per Q25), R9, C16 (snubber, populate
only if bring-up shows SW ringing).

## Disclosed, deliberately NOT fixed

- Two residual etch slivers (0.05 x 1.71 mm and 0.078 x 0.497 mm), fused to
  neighbouring copper so no gate fires, but a fab may query them.
- **Min F.Cu island gap is 0.1021 mm against JLC's 0.1016 floor - 0.5 um of margin.**
  Pre-existing and unchanged by this work, but it means ANY further pour edit risks
  tripping `dfm_clearance`. The risk of touching exceeds the risk of leaving.
- 16 dfm warnings remain (15 pin-1 dot slivers + 1 silk width), unchanged.

## Script defects found, recorded not fixed (skill work belongs in its own session)

- `lib/gerblib.py` chords drawn arcs - the S12 `approximate_arcs` fix reached
  `_flash_polys` only. **Every footprint drawing a silk ring around a pad will fail
  the dfm gate forever** until this is fixed in the tool.
- `planes_gen` should refuse or warn when a planned region edge lands within
  `min_thickness` of an existing same-layer zone outline - fully detectable at plan time.
- No script owns footprint-internal silk on a placed board.
