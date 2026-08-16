# P5 Board Setup - digest (2026-08-15)

- **Outline CUT 40x30 -> 35x25 mm (1200 -> 875 mm2, -27 %) on owner direction**
  ("priority is a tight layout"). Defensible because the facts moved: H1's 1200 mm2
  rested on the PLACEHOLDER 0.92 W vs a 0.95 W gate, and the real part came in at
  0.76 W worst-case. 875 mm2 keeps the pour above check_thermal's ~645 mm2
  saturation knee, so 0.76 W still gives ~56 C rise against the 70 C limit.
- **Mounting holes 4 -> 2 diagonal** (H1 bottom-left, H2 top-right). 4 x M3 with
  6.5 mm keepouts would claim ~170 mm2 of 875 - 19 %, all in corners the hot loop
  and output bank need. requirements.md s5 sanctions exactly this.
- Generator edited for the hole count; schematic regenerated; **erc re-gated 0/0**.
- CORRECTED an owner premise, verified by grep not by citing the doc: `--outline`
  exists ONLY on board_init.py and no other script writes Edge.Cuts, so the edge
  cut CANNOT be moved after placement - a resize rebuilds from the netlist and
  discards placement and routing. Strategy recorded instead: place -> measure ->
  resize + RE-PLACE if there is slack -> route ONCE at the final size.
- board_init: **parity 0** (the first run's 8 parity errors were duplicate H1-H4 -
  the schematic already carried them and --mounting-holes added a second set; flag
  dropped). 20 components, 8 nets, outline_bbox 35.00 x 25.00, profile 2layer_1oz.
  33 unconnected = expected pre-routing. ONE residual error: L1 pad 2 hangs over
  the bottom edge in the shelf-pack dump - a row-packer artifact, not a feasibility
  verdict; P6 replaces the entire placement and the `place` gate confirms.
- rules_gen: 12 rules, capability_class 2layer_1oz, **netclasses split per
  IPC-2152 width** - Pwr_0p56mm (+VIN, 1.1 A) and Pwr_1p52mm (/SW, +5V, GND,
  2.6 A). No flattening; no HV rules (30 V does not trip creepage).
- Separation J2/J1-to-L1 relaxed 8 -> 6 mm: the 8 mm was explicitly justified as
  "what a 40x30 outline can honestly give", i.e. outline-derived, not physical.
