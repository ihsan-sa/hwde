# P5 Board Setup digest - sbuck-5v3a

- `board_init`: 50 x 40 mm exactly (bbox 22.72,37.225 -> 72.72,77.225), 4 layer,
  stackup JLC04161H-1080B, 1 oz outer / 0.5 oz inner, 44 components, 15 nets.
- **parity = 0** after two fixes. Both were real:
  (a) 11 x "Exclude from BOM settings differ" on H1-H4 + TP1-TP7 - the footprints
      declare exclude_from_bom, the symbols did not. Fixed at the generator
      (`in_bom = False`), not by loosening anything.
  (b) 2 x duplicate/value mismatch on H1 - caused by MY passing `--mounting-holes 4`
      when the schematic already carries H1-H4. Re-run with `--mounting-holes 0`.
      The 4x M3 now come from the schematic as real parts; P6 must place them at
      the corners, inset 3.5 mm.
- Fab floors at ERROR severity from profile `4layer_1oz`: clearance 0.1016, track
  0.1016, via dia 0.45, hole 0.2, annular 0.1, hole-to-hole 0.5, edge 0.3 mm.
  Stated explicitly because "DRC 0/0" is meaningless if the floors sit under the fab's.
- `rules_gen`: 14 rules, capability_class 4layer_1oz, copper derived from the stackup.
  Netclasses split PER REQUIRED WIDTH (not flattened to one max-width Power class):
  Pwr_1p52mm (/VIN_RAW, /VIN, +VIN @ 2.6 A), Pwr_2p055mm (+5V, GND @ 3.3 A),
  Pwr_2p31mm (/SW @ 3.6 A). Matches the architect's IPC-2152 numbers exactly.
- `diff_pairs` is an explicit empty list and stayed empty - that is what stops /SW,
  the highest-current node, from silently acquiring differential-pair gap rules and
  an inner-layer track ban. `hv_rules` empty (no pair reaches the 30 V IPC-2221 trigger).
- Residual, NOT resolved at P5: 22 copper_edge_clearance errors + 2 silk_over_copper
  warnings, all from the naive shelf pack at the outline origin corner, plus 71
  unconnected. P6 placement and P7 routing own these respectively.
- Sidecars (constraints.json, decoupling.json) sit beside the board as required.
