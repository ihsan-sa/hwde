# P6 Placement - digest (2026-08-16)

- **place gate PASS 0/0** (all five legs ran); kc.py drc clean but for the 33
  expected pre-routing unconnected; silk_place 0 residual. hpwl 306.7 -> **125.0 mm**.
  Route probe **completion 1.00** (33/33 bare, 19/19 with pours, re-verified by
  importing the session and re-running DRC).
- **SCRAP AVERTED: both provisional connector rotations were wrong** - J1 0 -> 270,
  J2 90 -> 0. The WRL carries (rotate 0 0 180), the documented coincidence trap, so
  the agent resolved native entry on a 3D test board and confirmed on orthographic
  left/front renders. As declared, BOTH wire openings faced inward = scrap.
- Hot loop hand-placed and **locked before anneal**: C1 220 nF 1.72 mm from BOTH
  VIN(2) and PGND(1), pads UNCROSSED, ~2.2 mm2. A rotation-sign error that mirrored
  C1/C6 into a self-crossing loop was caught and fixed mid-run.
- **All annealer candidates rejected on structure** (each put the FB divider against
  L1's SW pad and TP1/TP2 outside the switch-node copper - what the cost function
  cannot see). The hand placement also won on hpwl, 125.0 vs 130.3-130.8.
- Cin/Cout ground separation 10.49 mm (record wants 1-2 cm). W2 satisfied by
  geometry: R2's GND pad ~4.1 mm on a clear straight path to the EP/AGND island.
  TP1 inside the /SW copper; /SW ~30 mm2 vs the 40 mm2 ceiling. Bottom pour
  unbroken under hot loop, /SW and L1 (only J1/J2 THT pads + 2 M3 holes penetrate).
- **OUTLINE FINAL AT 35x25, measured**: occupied 34.90 x 24.90, 0.05 mm slack all
  round, fill 72.7 %, largest inscribed empty rectangle 4 x 4 mm - one more 1210
  does not fit anywhere. Best conceivable shrink 34x24 (-7 %) would eat the
  0.15-0.40 mm gaps this layout runs on. Owner's place-measure-resize plan ANSWERED:
  no resize. H3 approved; 7 refdes under bodies accepted (no free silk area).
- **Toolchain: fixed routelib's score regex** (crashed route_auto ON SUCCESS - the
  no-unrouted log line ends in a full stop that `[\d.]+` swallowed). Also recorded
  two silently-non-enforcing constraint mechanisms: keepouts are never translated
  from board-local, and separation is centre-to-centre and skipped when either ref
  is locked - all four declared pairs here were unchecked. Verified by hand instead.
- Carried to P7: planes_gen made only **10** EP thermal vias vs our >= 16 (datasheet
  text minimum 12; its Fig 10-2 draws ~6 - do not copy the figure).
