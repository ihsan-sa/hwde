# P9 DFM + run close - digest

- Gate `dfm` PASS, 0 violations at any severity. Re-run standalone with the
  polarity oracle (schematic) and the BOM leg (parts.json) both supplied so it
  did not pass vacuously: still 0.
- Fab package written to fab/: gerbers + drill (zipped), bb-amp-pos.csv,
  BOM.csv, BOM-full.csv, CPL.csv.
- Assembly split checked, not assumed: 11 SMT parts in CPL.csv; J1/J2/J3 absent
  from both CPL and the assembler BOM because they are `hand_install`, and
  present only in BOM-full.csv with per-part instructions. U1/U2 rotations came
  through as 180 deg against 270 in the raw position file - the jlc_rotations
  correction, which is the catcher for a part mounted backwards.
- BOM-full carries the notes that stop a future reader "fixing" the design:
  C4 marked "NOT a supply-pin cap - do not relocate to U2A's output", and J1
  marked that the bias-current return runs through the 350 ohm sensor source
  itself so no bleeder resistors belong there.
- LEARNINGS: 17 entries compiled to learnings/queue.yaml, all `pending` - 14
  from the agents, 3 orchestrator-level (the diff_pairs conflation across four
  phases; a late pin change must sweep every artifact that states pin order;
  KiCad draws text-box overflow instead of clipping it). 0 orphans,
  0 malformed. Promotion is a separate owner pass.
- RUN STOPS HERE. block-only default: ordering is a separate owner decision.
  No H5, no release attestation, no money. Everything needed to order is in
  boards/bb-amp/fab/.
