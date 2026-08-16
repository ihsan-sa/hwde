# P9 DFM + fab package - digest (2026-08-16)

- **dfm gate PASS, all 8 legs RAN**: copper, copper_to_edge, drill, hole_to_edge,
  silk, polarity, bom, release. One warning only: 4 silk strokes at 0.12 mm vs
  JLC's 0.15 mm minimum, located at the TestPoint rings (stock KiCad width,
  advisory by design) - NOT the terminal polarity labels.
- **Coverage hole found and closed**: the first dfm run reported PASS with
  `coverage.skipped_error = {bom: "no parts.json"}`. The sidecar rule wants
  parts.json beside the BOARD from P5; I had copied constraints.json and
  decoupling.json but not parts.json, so the BOM/assembly leg - the one the recipe
  calls "not waivable paperwork" - silently did not run. Copied; all 8 legs now run.
- **Fab-package defect fixed**: J1/J2 were classified `smt_placed` and written into
  CPL.csv, but they are THT screw terminals. bom_cpl's auto-classifier keys on
  `exclude_from_pos_files`, not `attr through_hole`, and reported pass /
  bom_complete:true throughout. Set `assembly_class: hand_install` + refdes notes.
  Class split now smt_placed 14 / hand_install 2 / board_feature 4; CPL carries only
  the 14 machine placements. These two defects were one phase apart from catching
  each other.
- Package written: gerbers (10 files + job), drill, `bb-buck_gerbers.zip`, BOM.csv,
  BOM-full.csv, CPL.csv, pos.csv, and **README-fab-notes.md**.
- The fab note carries the owner's H4 ruling: request a **windowed EP paste stencil**
  (60-80 %, sub-apertures avoiding the 12 barrels; sink:source 1.36 vs 0.53 mm3),
  the hand-solder sequence and 60-80 W iron note for the solid-flooded terminal GND
  pins, the polarity legend, and the bench operating limits (30 V hard max, no
  hot-plug, PFM below ~200 mA is expected not a fault).
- Run close: 9 workspace learnings compiled to the promotion queue (pending, not
  promoted - the owner rules at a `promote` pass, and bring-up evidence is what
  retires the mode's maturity requirement).
