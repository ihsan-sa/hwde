# P7 Routing - digest

- **Gate drc_routed: PASS, 0 violations, completion 1.00**, commit e0b2d2d.
  Chain: planes_gen --no-thermal-vias -> route_critical -> route_auto ->
  route_edit (rip) -> stitch_vias -> plane_repair --flag-only.
  route_cleanup SKIPPED (2L pour board, V13 defect).
- **planes_gen would have DRILLED THE LIVE TAB**: its exposed-pad heuristic
  grids vias under any netted SMD pad >= 4 mm2 on a plane net (U1's tab is
  8.4 mm2 on +3V3) and does NOT read constraints.thermal.min_vias. The
  constraint saying "no vias here" and the script that drills them never meet.
- **The autorouter paid for connectivity with heatsink copper**: FR stalled at
  0.60, and KRT closed GND by daisy-chaining 3 F.Cu GND pads across the +3V3
  pour, slitting it 7 mm from the tab (-2.6% effective). Ripped; replaced with
  3 pad-stitch vias - the mechanism route_critical's own report names.
- stitch_vias: 3 pad vias, **0 area vias** (63/66 rejected single_layer_contact
  - there is no F.Cu GND pour to stitch to). Closest via to the tab 6.9 mm.
- +5V ran the intended BOTTOM edge, slitting the pour rather than crossing it.
- **FINAL pour: 1199.221 mm2, 1 island, 0 orphaned, 1085.679 mm2 within 25 mm
  of the tab.** Routing cost 0.95%.
- 3 check_current `insufficient_transition_vias` ACCEPTED: the heuristic
  charges each via 0.515 A, but the load return goes J2 pin -> B.Cu plane ->
  J1 pin, both THROUGH-HOLE. These vias carry quiescent + ripple only.
