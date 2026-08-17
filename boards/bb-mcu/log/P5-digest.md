# P5 Board Setup - digest (2026-08-16)

- Run INLINE (no board-setup agent): no impedance work and no library repair.
- `board_init --outline auto --layers 2 --stackup JLC2313_1.6
  --mounting-holes 4`. Self-check: **parity 0, setup_violations 0**,
  unconnected 25 (expected, unrouted), clean true. It read the recorded build
  mode and honored geometry-as-OUTPUT - a fixed WxH would have been refused.
- Provisional outline **51.15 x 43.524 mm**. This is deliberately generous
  room, NOT a size: P6 places to the canonical layout and
  `board_edit --outline fit` then earns the real dimensions.
- `rules_gen` capability_class **2layer_1oz**, matching the stackup's own
  copper - 9 rules. Floors reported, not assumed: track and clearance
  0.127 mm, annular 0.150 mm, edge clearance 0.300 mm, hole-to-hole
  0.500 mm. J1's 0.40 mm and the header's 0.30 mm annulus both clear.
- Netclasses: Default only (track 0.2 mm, via 0.6/0.3). +3V3 at 0.1 A needs
  0.05 mm, so it buckets into Default - exactly what P2 predicted, and the
  reason GND was deliberately left undeclared in power[].
- diff_pairs [] and hv_rules [] - correct, nothing on this board needs either.
- Sidecars beside the board: constraints.json (re-synced after the P4
  amendments, byte-identical to architecture/) and decoupling.json.
