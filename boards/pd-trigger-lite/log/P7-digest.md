P5-P7 (2026-09-24): board_init 25x15 r1, parity 0; rules_gen VBUS 1.248 mm class. Manual placement
(place_p6.ops.json): J1 left edge mouth out, VBUS as F.Cu zone band y 5.3-9.7 to J2, Rset row top,
U1 + VHV/LED bottom. Freerouting routed all signals on F.Cu straight through the VBUS band (split the
zone, CFG1 under J1 on F.Cu), so it was discarded; hand-routed with route_edit (route_edit_manual.json:
CC and CFG1 cross on B.Cu, 11 vias). VBUS zone switched to solid pad connection (3 starved thermals).
Refdes silk hidden, passive outlines cleared, labels added. drc_routed PASS 0/0.
route_critical skipped: KRT not installed; nothing critical to route (VBUS is a plane).
