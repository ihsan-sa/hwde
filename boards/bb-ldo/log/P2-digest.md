# P2 Architecture + coverage research - digest

- 3 blocks, one rail, zero signal nets. Stackup **JLC2313_1.6** (2L, 1 oz).
  ONE flat sheet. No sim bench (loop stability is IC-internal compensation).
- Coverage at the learning floor (`proven` + `--research-provisional`): 1 slot,
  1 GAP - the library had no linear-regulator checklist and no records.
- Research `block-linear-regulator-1`: 4 sources (AMS1117 vendor-layout; TI
  LM1117 / AN-1028 / SLVA115A cross-vendor), 20 pages read VISUALLY, 6 records
  + the topology's first checklist.
- **3 reader passes, 2 refutations, both the SAME defect**: an unsourced
  part-selection instruction (first as a PMOS/PNP-scoped ESR-vs-frequency
  basis in `rule`, then as "MLCC and polymer are low-ESR by construction" in
  prose). A third instance was caught in the CHECKLIST - the artifact that
  propagates to future boards - and rewritten to mechanism + acceptance test.
  Final 6/6 verified.
- Two findings CHANGED the board: **R1 deleted** (minimum load is the
  ADJUSTABLE variant's spec -> 5 parts) and **backside copper counts** (AMS p5:
  the spreading layer need not connect to the tab; ~5 C/W at 1000 mm2). Taken
  as margin, not licence to shrink the top pour.
- Coverage re-run: 0 gaps, 1 **provisional** (owner approval -> covered).
- Carried to P8: every TI number here sits inside LM1117 section 9, which TI
  disclaims; AMS Table 1 self-describes as "a rough guideline".
