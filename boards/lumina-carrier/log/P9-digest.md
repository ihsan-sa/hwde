# P9 DFM digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `fab/gerbers/` (12 files), `fab/lumina-carrier_gerbers.zip`,
`fab/BOM.csv`, `fab/CPL.csv`, `fab/lumina-carrier-pos.csv`,
`fab/assembly-manual-work.md`, `work/p9/*`.

- **`dfm` gate: PASS - 0 errors, 87 warnings.** Entered the phase at **5 errors**.
- **`drc_routed` still 0/0** after the DFM repair, and the four owner-accepted waiver
  counts are byte-identical: `check_current` 94, `check_creepage` 10,
  `check_return_path` 13, `check_decoupling` 2 warnings.

## The 5 errors were 2 physical defects, both generator output

Each defect produced one `hole-to-hole` plus one or two `copper clearance` findings,
because the annular rings were 0.0136-0.0505 mm apart.

1. **Two same-net +3V3 through-vias 0.3136 mm apart** at (98.09, 84.35) and
   (98.65, 84.10), both 0.300 mm drill / 0.600 mm copper. Deleted the first; the
   surviving via's nearest drill is now **1.1469 mm** (copper gap 0.8469 mm). No legal
   relocation existed for either - the site is fenced by `/ETH_MISO` on B.Cu, U10's
   0.65 mm pin row and an `/ETH_RSTn` diagonal - which was **measured, not assumed**.
   Deleting orphaned U10.8's stub, replaced with two 0.500 mm F.Cu segments at the
   `PWR_3V3` netclass width so no new `undersized_track` appeared. Which via to delete
   mattered: removing this one leaves a 2-via cluster that still passes
   `check_current`'s 1 A / 2-via rule, whereas removing the other would have split it
   into two 1-via clusters and **added** two violations.
2. **A GND stitch via 0.3505 mm from a footprint thermal-via drill** - the documented
   blind spot, verbatim. The via sat inside U22's HTSSOP-20 exposed pad, which carries
   its own array of 15 plated thermal vias on a 1.3 mm grid. **Moved** rather than
   deleted, to the centroid of the surrounding cell -> **0.6192 mm** hole-to-hole
   (copper gap 0.3192 mm). Moving held the via count constant, so no `check_current`
   cluster changed and `check_thermal`'s `nearest_via_mm` shifted only 0.27 mm.

Board-wide minimum hole-to-hole is now **0.5016 mm** across 440 drills.

## Why P7 did not catch either, and what was changed so it will

The shipped `.kicad_pro` carried **`min_hole_to_hole: 0.25` at severity `warning`** -
below **every** JLC profile, all of which specify 0.5 mm. Both defects were above
0.25 mm and therefore never fired. **This is the second sub-fab floor found in the
generated project file**, the first being `min_track_width: 0.1` against JLC's
0.1016 mm (188 tracks, fixed at H4). Raised to **0.5 mm at severity `error`**, and
`drc_routed` still reads 0/0 - so it cost nothing and would have caught defect 1 at P7.

**The general lesson, and it is the important one: `drc_routed` 0/0 does not imply
manufacturable, because DRC checks the board against rules the pipeline itself wrote.**

## Fab package

12 gerbers + drill, `setLength 100.0 x setWidth 80.0` confirmed **by JLC's own audit**,
not just by us. BOM 56 lines / 111 placements, CPL with **5 rotation corrections**.
Manual work totalled in `fab/assembly-manual-work.md`: **6 THT parts, 72 THT joints**,
and the "hand-fitted magjack" is corrected there - J1 is **wave-soldered** by JLC.
