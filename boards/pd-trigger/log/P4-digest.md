# P4 digest (pd-trigger)
Flat sheet, 30 refs/24 lines, generator + retype (only U1 VDD/GND power_in).
ERC 0/0; audit pass (3 structural power_no_consumers on pass-through nets).
Agent corrected 3 orchestrator-brief errors from file authorities; edited
architecture constraints for R2A/R2B split (retro-approved; finding 31:
anneal silently drops absent separation refs). Fable reviewer 0 err/2 warn:
DP/DM short-at-chip RULED safer than datasheet wiring (W1, PD-only doc);
VDD corner math verified 0.979mA@4.4V (W2, bring-up measure). Window
detector verified at 4.4/5.25/6.7/9/20V corners; Q1 pin map from primary
source; TVS protects every downstream rating; 5A path has nothing in series.
H2 AUTO-approved.
