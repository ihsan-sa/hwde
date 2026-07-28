# P7 digest (stm32-blinky)
Attempt 1: 44/45 connections; U1.8 GND sealed by neighbour escapes; router
refused 0.009mm-margin fix; returned placement_adjust_request (sanctioned).
Backward edge: budget consumed, pre-route restore, U1 cluster +1.0mm east
(placement agent; router's raw suggestions geometrically corrected), place
gate re-PASS. Attempt 2: full chain re-run -> drc_routed PASS 0 err/0 warn,
completion 1.0 (45/45), 207 tracks/20 vias/single GND pour intact.
route_cleanup regressed BOTH attempts (union-find/fill edge, V13) - restored
+ continued without, per design; now flagged unambiguous-bug for hardening.
stitch_impossible advisory FP on track-connected pads noted.
