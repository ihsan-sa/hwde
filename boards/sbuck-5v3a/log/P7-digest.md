# P7 Routing digest - sbuck-5v3a

Gate `drc_routed`: **PASS, exit 0** - 0 errors, 0 warnings, 0 unrouted, parity clean,
`--all-track-errors` on. Completion **1.00** (71/71 connections closed).
Board: 115 tracks (all F.Cu), 31 vias (all GND), 14 zones, 0 unfilled.

## The numbers the brief demanded

| Deliverable | Result | Limit |
|---|---|---|
| /SW copper, F.Cu | **30.44 mm^2** (22.94 main node + 7.51 tap arm) | <= 40 mm^2 |
| /SW min cross-section, U1.8 -> L1.1 | **3.50 mm** | >= 2.5 mm |
| /SW main-node length U1.8 -> L1.1 | **5.97 mm** (bbox incl. BST/TP2/snubber arm 10.49) | <= 8 mm |
| /SW on inner or bottom copper | **0.000 mm^2** on In1/In2/B.Cu | zero |
| Thermal vias in U1 exposed pad | **12** (3 x 4 at 0.90 mm pitch, 0.6/0.3) | 12 |
| Stitch vias within 6 mm of U1 EP | **11** | >= 8 |
| F.Cu GND island contiguous with U1 EP | **1395.2 mm^2** | >= 100 mm^2 |
| In1 GND within 12 mm of U1 | **444.9 mm^2, ONE piece** (99.0% of the disc) | >= 400, no split |
| B.Cu GND total | **1850.1 mm^2** | >= 1500 mm^2 |
| GND within 14.3 mm of U1, summed over layers | **2169.7 mm^2** | 529 pass / 650 A_sat |
| Vias inside the C9 -> U1 hot loop | **0** | 0 |
| GND tracks anywhere | **0** - all return is plane/pour | 0 |

Min via hole-to-hole 0.600 mm (JLC floor 0.500). `/FB` 13.34 mm total, 3.13 mm from
/SW copper, 3.52 mm from L1, still sensing at C12's +5V terminal. In2.Cu came out
**GND**, not +5V - checked explicitly. No placement was touched; all 25 locks intact.

## Chain that ran

`planes_gen` (7 zones) -> 12 in-pad thermal vias (`route_edit`) -> 9 hand-placed U1
ring vias -> `stitch_vias` (6 area vias, 15 mm auto pitch) -> `route_auto`
(`--power-layers In1.Cu,In2.Cu,B.Cu` so every track lands on F.Cu; FR rung 1, 124
tracks, KRT finish rejected on merit) -> pour fan-in pass B + 9 rips -> 4 island-bond
vias -> `plane_repair` (no repair needed: 0 split, 0 dead islands) -> gate.
`route_cleanup` **skipped** - DRC was already 0/0 and its loop-breaker has regressed
twice on pour boards; nothing to gain, a real regression risk.

## Three findings (all in LEARNINGS)

- **`planes_gen` rejects `_note`.** `_PLANE_KEYS` is a strict whitelist, so
  `constraints.planes[]` - which carries this file's most load-bearing note - cannot be
  fed to the documented step-0 invocation at all. Used planes-only sidecars
  (`kicad/planes_p7.json`, `kicad/planes_p7b.json`) instead of stripping the notes.
- **A clean `--pad-window` does not predict Freerouting's width.** All 61 power pads
  probed `ok` (R6.1/R8.1 reported 6.97/8.00 mm against a 2.055 mm floor); FR then routed
  those 0402 taps at **0.8058 mm - the pad width** - and necked +5V to 1.6348 (1210 pad)
  and +VIN to 1.4848 (0805 pad). 9 `track_width` errors, fixed by pour fan-in per the
  remediation ladder step 4, not by necking or by weakening a rule.
- **`planes_gen`'s via grid can only be odd x odd.** It is centroid-centred and
  pitch-stepped, so U1's 2.613 x 3.502 mm pad yields 3 x 3 = 9, never the 12 that fits.
  Hand-placed the 3 x 4 array with a half-pitch y stagger.

## Judgment calls

- **Power is poured, not trunked.** +VIN (2 rects), +5V (3 rects) and /SW (2 rects) are
  F.Cu zones at priority above the GND pours. This is the only way to satisfy net-wide
  `aiee_pwr_width_*` floors at 0402/0603 stubs without touching the `.kicad_dru`. The
  `.kicad_dru`, `.kicad_pro` netclasses and `constraints.json` are byte-unchanged.
- **All four GND planes kept solid; every track on F.Cu.** `--power-layers` was forced to
  include B.Cu (the `auto` heuristic only ever considers INNER layers, so B.Cu would have
  been fair game for Freerouting and the second radiating face would have been cut).
- **F.Cu GND uses thermal relief except where it must not.** Board pour is priority 0
  thermal (J1/J2 screw terminals stay hand-solderable); a priority-3 `connect: solid`
  island covers U1's EP, PGND pin and C9's return, and two priority-4 solid patches clear
  the `starved_thermal` on R1.2 / C3.2.
- **M3 washer keepouts not added as rule areas.** All four planes are GND, so a screw or
  washer bridging pour to pour is a GND-to-GND short. Verified instead that the nearest
  non-GND copper to each hole is 5.38 / 6.89 / 10.18 / 11.60 mm - all well past the
  3.25 mm washer radius. Flagged for P8 to confirm the reasoning rather than the rule.

## Handed to P8

- 2 `/SW` tracks at exactly 2.31 mm survive inside the pour (FR's U1.8 -> L1.1 legs).
  Legal and load-bearing; they are counted in the 30.44 mm^2.
- The `/SW` bbox is 10.49 mm end to end because P6 put the BST cap, TP2 and the DNP
  snubber on the west side of the node. The switching current path is the 5.97 mm leg;
  the arm is 7.51 mm^2 of quiet tap copper. Judge the ceiling on area, which holds.
- `+5V`, `+VIN` fan-in pours mean check_current will see pour necks, not tracks;
  `pour_neck` only measures between via attachments and these pours are via-free.
