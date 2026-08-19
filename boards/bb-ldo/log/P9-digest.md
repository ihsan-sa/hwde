# P9 DFM - digest

- **Gate dfm: PASS, 0 violations** (gerbers re-exported to scratch from the
  board and graded there, per the gate contract).
- Fab package: 9 gerber layers + drill + job file, zipped
  (`fab/bb-ldo_gerbers.zip`, sha bb7d6fab...), plus `bb-ldo-pos.csv`.
- BOM/CPL split correct by assembly_class, not by what the position export
  happened to contain: BOM.csv + CPL.csv carry the 3 SMT parts (U1, C1, C2);
  both screw terminals appear in BOM-full.csv ONLY, marked `hand_install`
  with instructions - including the J2 preheat warning.
- No `cpl_polarity` finding: the two polarized tantalums' rotations survive
  the jlc_rotations correction, which is the mounted-backwards oracle.
- Assembly notes written (`reports/assembly-notes.md`): preheat for J2.1,
  tantalum polarity, the HOT SURFACE hazard, and the two first-article
  measurements (C2 ring count, tab temperature).
- JLCDFM (the fab's own 30+ checks) remains a human browser step at ordering.
