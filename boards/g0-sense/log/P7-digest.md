# P7 Routing digest - g0-sense (2026-08-27)

- Gate **drc_routed PASS 0/0** on attempt 1, **completion 1.0** (0 unconnected).
  Independently re-verified with kicad-cli direct: 0 violations, 0 unconnected,
  0 schematic parity. erc / place / drc_routed all PASS and FRESH at the one
  board hash 0b12cafc.
- 2-layer chain, in the live-verified order: planes_gen (9 zones) ->
  route_critical -> route_auto (Freerouting 3 rungs, best rung 1 at fr 0.854;
  KRT finish generated and correctly discarded - it did not strictly improve
  DRC) -> stitch_vias (13 vias; 3 redundant removed, 1 moved for hole_to_hole)
  -> plane_repair -> gate. **route_cleanup skipped** by the S14 rule: this is
  exactly the 2L pour board class where its loop-breaker regressed twice.
- **The P6-carried VBUS item was RETIRED, not executed.** `route_critical
  --pad-window` - the premise check the role prompt demands before forcing a
  rule width at a connector - measured J1's A4B9/B4A9 escape windows at
  **1.315 mm**, above the 0.8 mm Pwr_0p8mm rule. P6's "impossible at any
  placement" was true of a 0.8 mm TRACK leaving the pad, not of the pad's
  escape corridor. VBUS is pour-carried at a ~1.45 mm fill band - wider than
  the rule asks - so neither costed option was needed: **no neck** (hence no
  ERROR-severity rule exception) and **no via-in-pad** (hence no unfilled via
  in a mechanically loaded connector pad, and no JLC wicking remark owed to
  fab/README). The two F.Cu VBUS pours are joined by a 0.8 mm B.Cu bridge on
  2+2 vias sited in open pour, holes clear of every pad edge.
- **The bridge's real risk was checked, not assumed.** That bridge crosses the
  layer that IS the GND pour - the playbook's "viasless pour-channel" blind
  spot - and the router's own plane_repair2 run was restricted to +3V3, so
  nothing had re-examined GND after the bridge landed. `plane_repair
  --flag-only` (never writes) on the final board: GND B.Cu = 1 group, split
  False, 813.2 mm2, 27 anchored components, 0 dead islands. Return path intact.
- **U3 sensor island contract met in full**: exactly 4 necked crossings (SDA
  0.127 / SCL 0.127 / GND 0.127 / +3V3 0.150, the lawful minimum for that net),
  zero copper and zero pour fill inside the tongue on both layers. Freerouting
  had laid a fifth crossing - SCL routed straight THROUGH the island - which
  was ripped and the I2C trunk rebuilt on B.Cu. The U-slot already existed from
  P6 (two 5.5 mm Edge.Cuts slots make a 3-sides-open tongue), so no new cut and
  Edge.Cuts is unchanged from the gated placement.
- **One router number corrected.** It reported the U1 tab pour at 158.0 mm2
  "connected". That is the CURRENT figure, not the HEAT figure: the +3V3 F.Cu
  pour is four components (113.2 + 24.3 + 18.4 + 1.6 mm2) merged into one
  electrical group by 0.25/0.5 mm bridge TRACKS, which carry 0.3 A at a 13 mV
  drop but conduct essentially no heat. The thermal spreader is **113.2 mm2**.
  It still passes on the board's own declared criterion: AMS1117 p5 Table 1
  gives 80 C/W for ~100 mm2 top plus a backside pour (B.Cu GND is 813 mm2
  under and around U1, and the record notes a spreader need not be
  electrically connected), so the rise is 0.51 x 80 = **40.8 K against the
  declared dt_c 45**; Tj 80.8 C rated, 60.8 C realistic, 106 C at the
  entitlement-abuse case, all under the 125 C limit. The 600-1000 mm2 figure
  was the architect's MEANS to Tj 71-76 C, not a separate requirement, and the
  earned 1014 mm2 outline cannot fund it. Buying pour area by shrinking the U3
  void was rejected outright - the B4 isolation contract outranks it.
- iter-2's `placement_adjust_request` (+3V3, SDA, GND, VBUS) was judged
  PREMATURE and not escalated to the P6 backward edge: it fired before
  stitch_vias and plane_repair, which own three of its four nets on the 2L
  chain. Finishing the chain closed all four.
- Nothing was weakened to pass: `.kicad_dru` and `.kicad_pro` are unmodified
  through all of P7 (git), and no zone, netclass or gate parameter was touched.
- Carried to P8: recompute the U1 thermal with **113 mm2**, not 158.
