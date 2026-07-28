# P8 digest (stm32-blinky)
verify gate: FAIL a1 (pdn_undecoupled /VIN + 2 pdn_no_bulk FPs) -> both were
CHECK defects: parse_farads multi-token bug fixed + "pdn: false" width-only
opt-out added (schema + tests). PASS a2, all 8 checks 0.
verify-reviewer (fable, fresh): 1 error (J1 polarity silk MISSING - a
requirements promise) + 4 warnings. Fix required silk text -> V17 CLOSED:
add_text/move_text ops built into place_swig/place_edit (idempotent,
independently verified, 9 tests). Fixer applied J1 "5V+"/"GND" legend, SWD
IO/CLK/3V3/GND pin-locked labels, 4 refdes disambiguations -> board fully
DRC-clean (0 violations of ANY kind), check_silk 0, drc_routed re-PASS 0/0.
BOM role drift + stale artifact fixed inline. H4 AUTO-approved; H3 render
folded here per P0 decision. Root-cause note: EasyEDA lib default puts cap
refdes at local (0,-4mm) - 4mm from its own body (library-level fix candidate).
