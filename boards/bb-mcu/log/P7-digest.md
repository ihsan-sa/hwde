# P7 Routing - digest (2026-08-16)

- Gate **drc_routed PASS 0/0** (errors AND warnings), attempt 2,
  commit e01fdc1. Completion **1.0**, 0 unrouted nets.
- 2-layer chain as verified: planes_gen -> route_critical -> route_auto ->
  stitch_vias -> plane_repair -> gate. route_cleanup deliberately SKIPPED
  (2L pour board is exactly its regression class; board was already clean).
- planes_gen: 1 zone, GND on B.Cu, 627 mm2. route_critical did NOT no-op as
  I expected - it routed +3V3 fully, 8/8 pads at 0.3 mm via KRT.
- route_auto: Freerouting ladder 3 rungs, best FR completion 0.857; KRT
  finish closed /NRST /SWCLK /SWDIO and GND to reach 1.0. FR's own success
  signal stays untrusted - only kicad-cli DRC gated it.
- stitch_vias: 5 pad-stitch GND vias, one per pad, matching
  `mcu-decoupler-is-the-local-source`. 0 area-stitch, expected on 2L.
- **The hard constraint held**: plane_repair splits_found 0, the GND pour is
  ONE component at 627.14 mm2 with 8 anchors. Neither the anticipated
  SWDIO x SWCLK crossing nor the +3V3 wrap needed B.Cu at all - both
  resolved on F.Cu - so `mcu-supply-return-continuity` was never at risk.
- Carried to P8/P9: planes_gen's fill leaves a 0.582 mm2 ZERO-ANCHOR copper
  island 0.34 mm from the main pour near J3's GND pad. plane_repair correctly
  ruled it not a split; DRC is clean with it present. It is floating copper,
  so watch whether any P8 check or the P9 DFM leg flags an isolated region.
