# P9 DFM - digest

- `fab_export` PASS: 9 layers, Protel-extension gerbers + drill, zipped
  (`fab/bb-adc_gerbers.zip`, sha recorded), plus the position export.
- `bom_cpl` PASS: BOM of record + JLC upload pair + CPL. 21 parts, ALL placed,
  `bom_complete` true, class split 21 `smt_placed` / 4 `board_feature` (the mounting
  holes). No missing LCSC, no unsourced, no off-LCSC, no unplaced SMT, no qty mismatch.
  **2 rotation corrections applied** from `jlc_rotations.csv` - the catcher for a
  polarized part mounted backwards, which net-level parity is blind to by construction.
- Gate `dfm` PASS 0/0. Note what it graded: gerbers RE-EXPORTED to scratch from the
  board, plus the sibling schematic as the CPL polarity oracle and parts.json for the
  BOM leg. The shipped zip is an ordering artifact and is NOT a gate input.
- Board 54.750 x 34.920 mm, 2 layers, 1 oz, HASL, no impedance control - the cheapest
  class JLC sells. ~$31/board of parts at qty 5, 84 % of it U1 + U2.
- Stops here by mode: `block-only` defaults end at P9 with the fab package. Ordering is
  a separate owner decision and no money has been committed.
