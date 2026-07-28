# P4 digest (usb-buck)
3-sheet hierarchy (usb/power/mcu + thin root) from 5 generators; full
delete-rebuild reproducible. ERC 0/0; netlist_audit pass (28 comps, 16 nets,
9 decoupling associations); contractual net names exact. Fable reviewer:
0 errors / 2 warnings (SW1 pairing no-datasheet -> bring-up check waiver;
UMW clone VRWM 5.0 vs 5.25 -> order-time ST swap option). H2 AUTO-approved.
Facts: hierarchical netlists drop unconnected-* nets (P5 watch); schlib
--pins blind to project libs (finding 22); LCSC fields visible cosmetic.
