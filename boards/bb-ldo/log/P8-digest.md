# P8 Verification - digest

- **Gate verify: PASS** with 3 recorded waivers (commit e0e416d); drc_routed
  0/0 after every copper edit; all 8 checks ran. Advisory legs clean:
  check_irdrop 12.1 mV worst on +5V, check_pdn_z pass.
- Fresh reviewer: 1 error, 7 warnings. It upheld both existing waivers after
  checking what would have voided the thermal one - whether the tab was
  relieved rather than solidly poured (`connect_pads yes`, all 8.424 mm2 in).
- **The error came from my own P7 instruction**: swapping KRT traces for
  stitch_vias put 3 barrels INSIDE SMT pads on an economy PCBA that neither
  fills nor plugs vias. Follow-on: U1's ground was that ONE barrel - open it
  and the regulator loses its ground reference, output rising toward 5 V.
- Fixed: 3 vias moved 0.55 mm past their pad edges with 4 authored F.Cu GND
  stubs (they were BARE - stitch_vias emits none, and GND has no top copper);
  redundant 2nd barrels on U1.1 and C2.2. C1.2 left single deliberately - its
  return is input bypass, not a functional failure path. Added HOT SURFACE silk.
- **NOT fixed, tooling block**: J2.1 per-pad thermal relief. No script sets a
  pad zone connection; planes_gen refuses the two-zone workaround on a poured
  board. Mitigated by assembly note (preheat + >= 60 W iron).
- **Third tooling gap this board found**: planes_gen ignores min_vias;
  stitch_vias rings from the pad CENTRE and its via_check only tests FOREIGN
  copper, so it cannot see its own error; no pad_zone_connect op exists.
- Pour across all edits: 1199.221 -> **1196.210 mm2**, ONE island, 0 orphaned,
  **1083.167 mm2 within 25 mm** (floor 1000).
