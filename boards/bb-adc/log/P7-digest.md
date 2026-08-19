# P7 Routing - digest

- 2-layer chain, one deliberate substitution: `route_critical` SKIPPED (no diff pairs,
  no RF, no high-current net, and its 0.3 mm POWER_WIDTH_FLOOR would have forced widths)
  and replaced by a hand pre-route of the analog-critical nets. planes_gen ->
  route_auto (rung 1, 4 passes, completion 1.00, 73 SES items) -> stitch_vias DRY ONLY
  -> plane_repair (0 splits) -> route_cleanup SKIPPED (2L pour board, S14).
- Gate `drc_routed` PASS 0/0. GND pour 1745.23 mm2, single polygon.
- Guard ring CLOSED and PROVEN geometrically, not eyeballed: the whole /AIN_BUF F.Cu
  net is one polygon with one interior hole that contains() all /AIN_DIV copper, min
  ring width 0.612 mm, guard-to-node gap 0.127 mm. It closes ONLY at the 0.127 mm
  floor - at 0.2 mm the south leg is culled, the pour drops 19.03 -> 8.68 mm2 and there
  are ZERO holes, yet it still fills and still looks like a ring in a render.
- +3V3 widened 0.2 -> 0.5 mm per constraints (impedance to the decoupling caps, not
  current - my brief had argued from current and was wrong), with a `Power3V3` netclass
  added so a future re-route cannot silently revert it. R 0.108 -> 0.043 ohm.
- Two pipeline defects found: stitch_vias models hole-to-hole CENTRE spacing while
  KiCad measures EDGE to edge (unsafe band 0.5-0.8 mm for 0.3 mm drills); and
  geom._refill_copy stages the .kicad_pro but NOT the .kicad_dru, so --verify-fill
  refills without the 0.127 mm floor and reports a false stale fill on EVERY board.
