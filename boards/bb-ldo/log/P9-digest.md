# P9 DFM - digest (re-run after the square re-place)

- **Gate dfm: PASS, 0 violations.** Fab package re-exported for the new
  34.655 x 34.655 mm outline: 9 gerber layers + drill + job, zipped, plus
  the position file. BOM/CPL regenerated.
- BOM/CPL split unchanged and still correct by assembly_class: BOM.csv +
  CPL.csv carry the 3 SMT parts; both screw terminals appear in BOM-full.csv
  ONLY, `hand_install`, with the J2 preheat instruction.
- No `cpl_polarity` finding - the two polarized tantalums' rotations survive
  the jlc_rotations correction after the cluster's 270 deg rotation.
- Assembly notes updated with the new dimensions and C2's 3D-model caveat.
- **release_disposition: engineering-validated** (was `blocked`): all five
  gates fresh and passing, all seven issues terminal, no human holds.
- JLCDFM remains a human browser step at ordering.
