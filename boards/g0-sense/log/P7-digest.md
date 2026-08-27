# P7 Routing digest - g0-sense (2026-08-27)

- **drc_routed PASS 0/0, attempt 1, completion 1.0.** Re-verified with kicad-cli
  direct: 0 violations, 0 unconnected, 0 parity. Nothing weakened - .kicad_dru
  and .kicad_pro unmodified (git).
- 2L chain in the verified order: planes_gen (9 zones) -> route_critical ->
  route_auto (FR 3 rungs, best rung 1; KRT finish correctly discarded) ->
  stitch_vias (13) -> plane_repair -> gate. route_cleanup SKIPPED (S14 rule).
- **The P6-carried VBUS item was RETIRED, not executed**: `--pad-window` measured
  J1's escape at 1.315 mm vs the 0.8 mm rule, so P6's "impossible" applied only to
  a track leaving the pad. VBUS is pour-carried at a ~1.45 mm band - no neck, no
  rule exception, no via-in-pad, no JLC wicking remark owed.
- Its real risk was checked, not assumed: the 0.8 mm B.Cu bridge crosses the GND
  pour layer, and plane_repair2 had been restricted to +3V3. Re-ran plane_repair
  --flag-only: GND B.Cu = 1 group, 813.2 mm2, 27 anchors, 0 dead islands.
- U3 island contract met: exactly 4 necked crossings, 0 copper and 0 fill in the
  tongue on both layers. FR's fifth crossing (SCL through the island) was ripped
  and the I2C trunk rebuilt on B.Cu. U-slot pre-existed from P6.
- Corrected the router's own number: the U1 tab spreader is **113.2 mm2**
  contiguous, not the 158 mm2 it reported (0.25/0.5 mm bridge tracks carry
  current, not heat). Full detail in log/run-journal.md.
