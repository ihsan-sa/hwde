# P6 Placement digest - g0-sense (2026-08-27)

- Gate **place PASS 0/0** (all 5 legs: courtyard, outline, edges, keepouts,
  decoupler_distance). DRC: **0 non-unconnected violations**, 64 unconnected =
  the unrouted ratsnest. Route probe 0.969 (62/64).
- Size **EARNED 35.79 x 28.34 mm** (1014 mm2) from a 65.6 x 62.4 provisional.
  The 3.3 mm over the brief's soft 35 x 25 is the U3 isolation zone (8 mm
  separation + slits) - recorded as a relaxation, not drift.
- Hand layout beat the annealer 243 vs 468 mm HPWL (662.6 at seed). All three
  anneal candidates inherited the seed's 2 edge violations because at a
  geometry-OUTPUT binding the annealer pins edge clusters to the PROVISIONAL
  outline - the bb-buck trap. cand1's cluster structure was kept and rebuilt
  compactly by hand; gate ran AFTER `--outline fit`, per the bb-mcu defect.
- Judgment calls proven, not assumed: J1 mating direction two ways (WRL vertex
  occupancy + left orthographic render); U3 rotated so supply pads face C13
  (1.26 mm, 4.06 nH) and I2C faces the mainland - no island wraparound; D1
  first in the VBUS chain (J1->D1->F1->C2->VIN), corridor intrusion 0; C12 held
  1.5 mm from U2 pin 6 over silk. All four M2 holes KEPT - tucked in corner
  dead zones they add 0.0 mm to the fitted outline.
- Silk 13 -> 0. 12 were footprint-INTERNAL graphics, unreachable until
  `place_edit` gained a `silk_clear` op this phase: C12's 0603 outline could
  not be nudged clear (1.62 mm silk in a 1.29 mm corridor - a 0.33 mm
  position-invariant shortfall), so C0603's outline went from the library AND
  all 5 board instances; J1's 3 mouth-end segments (under the shell,
  unprintable) likewise. D1's refdes moved off J1's VBUS pad. `lib/EDITS.md`
  records both library edits.
- Carried to P7: the 0.8 mm VBUS netclass cannot escape J1's 0.60 mm pads on
  F.Cu at ANY placement - route_critical owns that entry, not Freerouting.
  `kicad/silk_ops.json` deleted: replaying it would UNDO the D1 fix.
