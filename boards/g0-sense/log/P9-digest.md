# P9 DFM digest - g0-sense (2026-08-27)

- **dfm gate PASS: 0 failing, 1 advisory warning.** fab package exported
  (11 files: gerbers + drill + zip), BOM/BOM-full/CPL written from
  assembly_class, 26 parts / 24 SMT-placed (J3/J4 are DNP hand-install THT).
- **The carried CPL rotation obligation is discharged, part by part.** dfm_check
  ran with the schematic as the polarity oracle: status checked, refs_checked 26,
  ZERO cpl_polarity findings and no rotation_delta_deg anywhere. The five carried
  refs: C3 0.0, D1 0.0, D2 180.0, D10 180.0, U3 0.0 (J1 270.0, U1 0.0, U2 180.0).
  This proves the CPL angle agrees with the schematic pin assignment for every
  part; it does not replace the owner's first-article check.
- The single warning is `dfm_silk_width`: 4 strokes under JLC's 0.15 mm floor
  (narrowest 0.060 mm). Located, not counted - **all four are inside U3's own
  DFN-4 footprint** (0.06/0.08 mm body outline and pin-1 marker on a 1.5 mm
  part). The four labels added earlier at P9 are NOT implicated: they sit at
  exactly 0.150 mm, same as every refdes, which I checked precisely because
  "4 new labels, 4 thin strokes" is too neat a coincidence to assume.
- Accepted rather than fixed: widening 0.06 mm strokes on a 1.5 mm body risks
  silk-over-pad (a real DRC error from an advisory warning), and silk_clear would
  delete the pin-1 marker outright. U3's orientation is controlled by the
  oracle-verified CPL rotation; the silk is a human cross-check. Goes in
  fab/README so a faint U3 outline is not misread as a placement error.
- Silk pass earlier in P9: check_silk 6 -> 4 misattributed, DRC still 0/0/0.
  Thermal waiver re-issued against digest 78f20b4b; verify re-run PASS.
