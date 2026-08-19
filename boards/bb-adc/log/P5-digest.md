# P5 Board Setup - digest

- `board_init` PASS: parity 0, setup_violations 0, 41 unconnected (expected, unrouted).
  25 components, 20 nets. Stackup `JLC2313_1.6`, 2 layers, 1 oz, profile `2layer_1oz`.
- Outline `auto` -> provisional 63.95 x 66.03 mm. Deliberately generous: geometry is an
  OUTPUT at this binding, and P6 places to the canonical layout, not to fill this.
- First run FAILED on duplicate footprints: the schematic already carries H1-H4, and
  `--mounting-holes 4` added its own. Re-run with `--mounting-holes 0`.
- Fab floors written at ERROR severity: clearance 0.127, track 0.127, via dia 0.6,
  hole 0.3, annulus 0.15, hole-to-hole 0.5, edge clearance 0.3.
- `rules_gen` PASS, capability_class `2layer_1oz`, 12 rules. NO netclass split: every
  rail's IPC-2152 width (max 5.5 um for +3V3 at 11 mA) is far under the 0.2 mm Default,
  so all four power nets stay Default. No HV rules - 5 V is the highest net on the board.
- Sidecars `constraints.json` + `decoupling.json` now sit beside the board, as every
  later gate resolves them from the board's own directory.
