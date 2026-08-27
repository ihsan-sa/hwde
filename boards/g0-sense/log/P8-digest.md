# P8 Verification digest - g0-sense (2026-08-27)

- **verify PASS: 0 failing** (from 5 errors), 8/8 checks ran, no coverage holes.
  erc / place / drc_routed / verify all PASS and FRESH at digest 9fa76a1b.
- **Four of five errors fixed on their merits, one waived.** Nothing edited to
  quiet a gate: constraints.json, .kicad_dru, .kicad_pro, netclasses and
  gates.yaml untouched across P7 and P8 (git).
- check_pdn "VBUS undecoupled" was a DATA gap - C1 (the 100 nF the Type-C 10 uF
  attach limit permits ahead of the PTC) was missing from decoupling.json.
  Completed the inventory after measuring 5.52 mm to J1's pad; error -> the
  intended pdn_no_bulk warning. Two via clusters fixed in copper, 2 -> 3 vias.
- **pour_neckdown "0.10 mm" was a per-zone checker artifact, proved not assumed**:
  eroding the UNION of the VBUS fills + J1 pad copper by 0.4 mm (the full 0.8 mm
  test at the 1.5 A fault basis) leaves each pad reaching all 3 of its vias. Real
  minimum 0.680 mm, gating a 0.33 mm2 dead lobe. So the current-basis lever was
  deliberately NOT pulled - the board meets 1.5 A physically.
- **One durable waiver: check_thermal on U1**, bound to digest 9fa76a1b +
  checker_version 1. The model credits only same-net top copper (144 C/W where AMS
  measured 80; 123 where TI measured 84) against an uncredited 810.9 mm2 B.Cu
  spreader. At 84 C/W the rise is 42.8 C, inside the declared 45; Tj 82.8 C rated,
  109.7 C abuse, limit 125. Also unreachable: needs 446.4 mm2, board can fund 439.9.
  Pour still grown 171 -> 250 mm2. B.Cu island/thermal vias rejected - they carve
  the ground return, trading a PASSING check_return_path for unneeded margin.
- **verify-reviewer (fresh context): 0 errors, 3 warnings**, ratified both the
  waiver and pdn_no_bulk - and overruled me correctly on silk: 4 of the 6
  misattributed refdes also sit UNDER part bodies, so they are invisible rather
  than ambiguous. Reclassified as a required P9 move_text fix.
