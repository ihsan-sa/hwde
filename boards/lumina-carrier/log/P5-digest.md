# P5 Board Setup digest - LUMINA carrier (LUM-CAR-A)

Artifacts: `kicad/lumina-carrier.kicad_pcb`, `kicad/lumina-carrier.kicad_pro`,
`kicad/lumina-carrier.kicad_dru`, `work/board_init*.json`, `kicad/constraints.json`
(patched with real outline-derived rectangles), `kicad/decoupling.json`.

- **Outline 100.0 x 80.0 mm**, read back from the report rather than assumed:
  `outline_bbox` = [19.58, 57.132, 119.58, 137.132]. `corner_radius` **3.0 mm
  honoured** (not clamped), `mounting_holes` 4 x M3 plus the 5th at (46,74) for
  CAR-REQ-15. MECH-01 and the MECH-02 H1 proposal both satisfied.
- **Stackup JLC04161H-3313**, 4 layer, 1 oz outer. **In1.Cu = GND, In2.Cu = +3V3**,
  each as three rectangles that route around the mounting holes; the ESP32-S3
  antenna keepout is authored from the real bbox per the P2 recipe (skipping it
  would have left the antenna over solid GND).
- **Setup violations 92 -> 36**, and the 36 are all pre-placement artifacts
  (27 `copper_edge_clearance`, 3 `courtyards_overlap`, 3 mask bridges,
  1 npth-in-courtyard from components still stacked at the origin) plus 2 benign
  warnings. **Zero library defects remained.**
- **Named `.kicad_dru` HV rules added** (P2 trap 1: `rules_gen` never reads
  `voltages`, so nothing otherwise makes the router honour 48 V clearance):
  `HV_48V_clearance`, `HV_48V_to_HV_48V`, `HV_48V_raw_to_rtn` at 0.635 mm, keyed on
  `A.NetName` (`A.Net` silently matches nothing), plus `magjack_isolation_barrier`
  at 1.30 mm.
- **Netclasses split** before routing (P2 trap 3) so +12V's 1.10 mm is not applied
  to V48_RTN's 0.6 A stub or pushed into Freerouting's DSN.

## Three library defects found here that placement could never have resolved

1. **ESP32-S3 thermal-land vias-in-pad** at 0.075 mm ring / 0.25 mm drill, failing
   both min-annular and min-hole. Enlarging them to 0.60/0.30 fixed those two and
   created **24 clearance + 24 mask-bridge** errors instead, because the via pads
   then touched the thermal sub-pads. They were **removed entirely**: thermal vias
   under a ground land belong to the board, not the footprint - P7 stitching places
   them against the real GND pour with correct net assignment, and that also
   removes the via-in-pad solder-wicking risk already on the P9 list.
2. **D1 SMBJ58A self-intersecting courtyard** from zero-length `fp_line` segments
   (easyeda2kicad artifact). Scanned board-wide: 5 removed across 2 footprints.
3. Sidecars (`constraints.json`, `decoupling.json`, `parts.json`) relocated beside
   the board so every later script resolves them.
