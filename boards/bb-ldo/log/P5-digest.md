# P5 Board Setup - digest

- `board_init --outline auto --margin 15` -> provisional **86.29 x 65.82 mm**.
  Deliberately generous: geometry is an OUTPUT at this binding, so P5 must not
  guess the size. board_init read the recorded mode and would have REFUSED a
  fixed WxH here.
- Self-check: parity **0**, setup_violations **0**, unconnected **9**
  (expected - the board is unrouted). 5 components, 3 nets.
- Stackup JLC2313_1.6, 2 layers, 1 oz. Fab profile `2layer_1oz` written into
  the .kicad_pro at ERROR severity: clearance/track 0.127, via dia 0.6,
  drill 0.3, annular 0.15, hole-to-hole 0.5, copper-to-edge 0.3.
- `rules_gen`: 11 rules, capability_class `2layer_1oz`. Power widths from
  IPC-2152 at dT 10 C - +5V/GND 0.2575 mm, +3V3 0.255 mm - in netclasses
  Pwr_0p2575mm / Pwr_0p255mm. No diff pairs, no HV rules (nothing above 5 V).
- Sidecars beside the board: constraints.json, decoupling.json.
- Planes declared: F.Cu = +3V3 (solid connect - the heatsink pour),
  B.Cu = GND (continuous, NO vias through it).
- **P6 plan note**: `--outline fit` counts courtyards, copper and keepout rule
  areas but NOT zones, and nothing in the toolchain can script a rule area.
  So the size will be earned by DERIVING it from the thermal requirement
  (>=1000 mm2 of contiguous F.Cu +3V3) after placement, then MEASURING the
  delivered pour with check_thermal's area_mm2 - not by trusting fit.
