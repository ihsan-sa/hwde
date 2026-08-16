# P7 Routing - digest (2026-08-16)

- **drc_routed PASS, 0 violations (err+warn, parity + all track errors, refilled);
  completion 1.00 (33/33 ratsnest, 0 unconnected_items).**
- **route_critical REVERTED and re-done by hand.** KRT put /SW, +VIN and +5V copper
  on B.Cu, slicing the ground shield through the hot loop and the switch node - the
  one thing recovering this board's 2L deviation. Restored from git, routed
  deliberately: 36 tracks, **ALL F.Cu, zero B.Cu tracks board-wide**, zero vias on
  +VIN / /SW / +5V.
- **route_auto NOT run (accepted deviation)**: the board already measured DRC 0 /
  completion 1.00, and exporting a DSN of a fully-coppered board is the documented
  Freerouting wedge case whose KRT finish can ADD B.Cu - the failure just reverted.
  route_cleanup skipped per the standing 2L-pour advice.
- Binding constraints, all MEASURED not asserted: B.Cu GND one unbroken 783.3 mm2
  island with 100 % coverage under U1, /SW and L1; **18 GND vias within 4.6 mm of U1**
  (9 in-pad + 7 ring + 1 grid) vs the >= 16 requirement; dedicated 1.52 mm AGND spine
  R2.2 -> EP that never touches PGND (W2 closed); +5V under J2 with **0.0000 mm2**
  inside H2's TRANSLATED washer rect; /SW 27.02 mm2 vs the 40 mm2 ceiling, F.Cu only.
- +5V reaches the left cap bank through an 18.3 mm2 pour bridge (neck 1.00 mm) - the
  sanctioned pour-fan-in remedy, since placement split the bank and the R1.2/TP2/C5.2
  pinch caps any track at ~0.95 mm. DC load path untouched at 1.8 mm; only cap ripple
  crosses, and FB senses on the no-DC side.
- Two new tool findings (workspace LEARNINGS): planes_gen's default THERMAL-RELIEF pad
  connection stranded U1's PGND on a 1.2 mm2 island in a 0.79 mm corridor - fixed with
  `connect: solid` via a planes-only sidecar; and pad extents must come from
  `geom.pads_of().poly.bounds`, since L1's land is 2.9 x 5.4, not the raw (size 5.4 2.9).
- Carry-forwards to P8 (not blockers): +VIN hot-loop widths geometry-capped at 1.30 mm
  (C1->VIN) and 0.66 mm (bulk feed) vs the 1.5 mm wish - both above the 0.56 mm floor;
  H1/H2 washer keepouts still carry GND pour (planes_gen has no void support, all
  copper and vias are clear); plane_repair mislabels the +5V bridge a dead_island.
