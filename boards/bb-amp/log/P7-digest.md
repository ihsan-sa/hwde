# P7 Routing - digest

- Gate `drc_routed` PASS, 0 failing. DRC 0 errors / 0 warnings at any severity,
  0 unconnected, all 30 connections closed. Completion 1.00. Committed.
- Freerouting rung 1 only (mp:20, 2 passes, 0 unrouted of 23), **0 of the
  2-retry budget used**, no KRT fallback, no placement_adjust_request.
- INPUT PAIR HELD, measured on the final board: /IN_N and /IN_P both
  10.808963 mm, delta 0.000000 mm, width 0.3089 mm both, **0 vias**, one F.Cu
  segment each, mirror deviation about y=30.0000 of 0.000000 mm. Neighbourhood
  mirror-identical item by item. Zero vias in the input corridor (nearest
  7.13 mm). check_diffpair PASS, skew 0.0.
- Router OVERRULED `route_critical --only diff`: that path requires a COUPLED
  pair at 0.3 mm gap and would have converged both legs onto y=30.0 into R1's
  pads. Laid two straight segments instead; Freerouting preserved them
  byte-exact. Third sighting of the diff_pairs symmetry-vs-impedance conflation.
- Reference is intact, measured not inferred: bottom pour is ONE component,
  1236.8224 mm2, split false, **bit-identical to what planes_gen created before
  any copper was laid**. Zero B.Cu tracks anywhere - every signal on F.Cu.
  7 vias total, all GND pad-stitches; stitch_vias added 0 (57 of 65 area
  candidates rejected single_layer_contact - a stitch via on a one-sided 2L
  pour is an antenna).
- `route_cleanup`: dry-run 0 ops, live 0 ops, drc_before == drc_after. The V13
  dangling-pass defect did NOT recur on its exact signature (7 GND stubs whose
  connectivity runs through the pour).
- Aggressor separation held: /VOUT to /IN_N 13.51 mm, to /IN_P 12.98 mm;
  J1 to J2 terminals 35.82 mm - no routing detour undid P6.
- Two errors of mine in the brief, both caught: I cited the REFUTED
  in-aggressor-separation record as governing, and I named /AMP2_OUT, a net
  deleted with R6 at P4.
