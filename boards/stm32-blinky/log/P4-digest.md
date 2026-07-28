# P4 digest (stm32-blinky)
Generator kicad/gen/root.py -> stm32-blinky.kicad_sch, ERC 0 err/0 warn
(severity-all), netlist_audit pass (20 components, 44 nets, 8/8 decoupling
associations, 0 value drift). Adversarial review: 1 error + 3 warnings.
Fixed pre-board: C5 -> 22uF tantalum C8020 (AMS1117 stability, anode on +3V3
verified), VDDA -> 1uF//10nF (C4/C10), VDD_3 bulk 10uF added (C11).
Waived: pintypes-vacuous (erc-waivers.md; hardening item). H2 AUTO-approved.
Refdes grew to C11 (sheets.md C1-C9 table stale - P2 doc drift, noted).
Interventions this phase: lib pin-type retype (kicad/gen/lib_pin_types.py).
