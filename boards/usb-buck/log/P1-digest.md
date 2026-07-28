# P1 digest (usb-buck)
Roster: interface-spec(USB-FS) + power-architect, both ran (parallel, opus).
USB: 90R diff on JLC04161H-3313 (w0.314/s0.2104), gap_mm=0.52 PITCH, t_rise
4ns but explicit return_via_radius 2.0 (4ns radius=120mm would be vacuous),
external 1.5k DP pull-up MANDATORY (F103 has none), NO series R (AN4879),
USBLC6-2SC6 ESD at connector, shell->GND direct (proposed), fragment
smoke-tested against rules_gen/check_return_path/check_diffpair/stitch_vias.
Power: VBUS(direct) -> +3V3 (AP63203 buck) 57mA peak +30% -> 0.1A declared;
C_IN capped 10uF (USB inrush 7.2.4.1); no thermal flags; buck-vs-LDO stated,
buck stands per brief. Architect to settle: LED R value, DP pull-up
hardwired-vs-GPIO, VBUS sense omit, shield bond, hierarchy net naming.
