# P7 digest (usb-buck)
4L chain: planes (In1 GND + In2 +3V3) -> critical (VBUS trunked; +3V3
correctly plane-skipped; DIFF PAIR structurally unroutable by KRT route_diff
- far-apart flow-through terminals peel to a never-run SE follow-up ->
FR routed it) -> stitch 38/42 (+1 via removed: hole-to-hole vs J1 PTH drill
the floor MISSED) -> route_auto (no wedge, rung1, KRT finish) -> U1.9 escape
pocket fix (FR's own via in the lane; co-designed 0.45/0.2 via relocation)
-> 17 DUPLICATED VBUS segments removed (FR echoed route_critical's copper
through SES - S11-era silent hazard, invisible to DRC as same-net stacks)
-> plane_repair x2 clean -> cleanup SKIPPED on dry-run evidence (would have
removed 2 load-bearing DM segments - V13 on 4L too). Gate PASS 0/0,
completion 1.0. Diffpair: skew+asymmetry fixed, uncoupled 6.61 structural
-> constraint corrected to 8.0 (decision logged). Return path 0 errors.
