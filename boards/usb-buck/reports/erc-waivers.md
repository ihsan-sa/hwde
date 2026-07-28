# Schematic review waivers (usb-buck)

W1 sw1-pairing-unverified: SW1 (C49023761) has no manufacturer datasheet;
{1,2}/{3,4} pairing follows the vendor symbol's internal bars. Failure mode
if wrong: button reads permanently pressed (feature dead, NO damage; USB/
SWD/LED unaffected). WAIVED with a mandatory bring-up step: continuity-check
SW1 pins 1-3 unpressed before firmware relies on the button. 
W2 usblc6-clone-vrwm: UMW USBLC6-2SC6 rated VRWM 5.0V vs USB legal 5.25V
(top 0.25V unspecified). WAIVED for prototype qty 10; ORDER-TIME OPTION:
swap to ST original (C7519, rated 5.25V, listed alternate in parts.json) -
noted for H5.

## P8 board-review waivers (usb-buck)
W3 j1-mouth-recess: micro-B mouth 0.46mm behind board edge (silk-edge
clearance tradeoff). Most cables latch at <=0.5mm recess. WAIVED for
prototype; respin note: make flush/proud + trim mouth-end footprint silk.
W4 economy-smt-tht: J1 4 shield pegs (2x 0.5mm slots) + J2 header arrive
UNSOLDERED on economy SMT-only assembly. Mandatory hand-solder step -> in
order human_steps at P10.
W5 uncoupled-relaxation-scope: max_uncoupled 8.0 is FS-THIS-BOARD-only
(structural span; ~1.5mm was recoverable by flipping R4 - respin nicety).
Never reuse on HS designs.
W6 d1-glyph: interior silk bar contradicts (correct) chamfer; hidden under
body post-assembly; rework-doc note only.
