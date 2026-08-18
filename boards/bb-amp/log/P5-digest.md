# P5 Board setup - digest

- Ran INLINE. Sidecars placed beside the board (constraints, decoupling, parts).
- `board_init --outline auto --margin 2 --mounting-holes 0`: parity 0,
  setup_violations 0, clean true. 14 components, 11 nets, stackup
  JLC2313_1.6 2L. The 30 unconnected are P7's.
- Fab floors REPORTED not assumed (2layer_1oz, all ERROR): clearance 0.127,
  track 0.127, via 0.6, hole 0.3, annular 0.15, hole-hole 0.5, edge 0.3 mm.
- Provisional outline 41.0 x 57.7 mm - generous and NOT the board. Geometry is
  an OUTPUT: P6 places, then `board_edit --outline fit` earns the size.
- DEFECT CAUGHT BEFORE IT SHIPPED: rules_gen defaults a diff_pairs entry with
  no `impedance_ohm` to 90 ohm and solves the netclass WIDTH from it - this
  DC-1 kHz 20 mV sensor pair would have routed at 1.3743 mm on a board with no
  controlled impedance anywhere, and the router traces at class width. Fixed by
  declaring the impedance the pair ACTUALLY HAS at the width we want (150 ohm
  -> 0.3089 mm), with an in-file note that it is a consequence, not a target.
  Deleting the entry was rejected: knowledge retrieval keys the 8 verified
  interface records off diff_pairs[].base (confirmed - P6 select pulled 16).
- `rules_gen`: 11 rules, netclass Diff150, +3V3 stays Default 0.2 mm.
