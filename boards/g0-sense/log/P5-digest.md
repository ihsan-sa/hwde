# P5 Board Setup digest - g0-sense (2026-08-27)

- Run INLINE (no board-setup agent): no impedance work, no library repair planned.
- `board_init --layers 2 --stackup JLC2313_1.6 --outline auto --margin 6
  --mounting-holes 4 --mounting-hole-fp MountingHole:MountingHole_2.2mm_M2`.
  Self-check **PASS: parity 0, setup_violations 0**, 26 components, 16 nets,
  unconnected 64 (expected, unrouted). Provisional outline bbox 9,9 -> 74.61,71.40
  - generous ROOM, not a size: P6 places canonically and `--outline fit` earns it.
- `rules_gen` capability_class **2layer_1oz** (matches the stackup's own copper),
  11 rules. Floors reported not assumed: track/clearance 0.127, via dia 0.6,
  annular 0.15, hole-to-hole 0.5, edge clearance 0.3 mm. Netclasses: **Pwr_0p8mm**
  for VBUS and +5V (0.8 mm, the 1.5 A PTC-dwell case); +3V3 needs 0.15 mm so it
  buckets into Default (0.2 mm) - exactly what P2 predicted. diff_pairs [] and
  hv_rules [] are correct here.
- **Real defect found and fixed at P5**: J1's pulled USB-C footprint had its ganged
  GND and VBUS pads 0.100 mm apart, BELOW the 0.127 mm fab floor, on the two nets a
  solder bridge shorts hardest. Cause was a converter artifact, not a vendor
  deviation - a 0.1 mm outline stroke on the custom-pad polygons inflated each wide
  pad from the vendor's 0.60 mm to 0.70 mm effective. Restored to the manufacturer's
  own land pattern; gap now 0.200 mm, fillet allowance unchanged at 0.20 mm/side.
- Two toolchain bugs fixed to get parity to 0 (both committed separately, both
  regression-tested against the goldens): board_init now mirrors a symbol's native
  `dnp` onto the footprint, and it MEASURES whether KiCad wants the netlist's
  `unconnected-(...)` pseudo-nets on the pads instead of guessing.
- Sidecars beside the board: constraints.json (byte-identical to architecture/) and
  decoupling.json. Remaining DRC: 2 transient silk_edge_clearance warnings on the
  H1/H2 mounting-hole refdes text - P6's silk sweep owns them.
