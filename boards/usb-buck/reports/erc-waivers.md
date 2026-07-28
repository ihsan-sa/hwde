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
