# P1 Research - digest

- Roster: power-architect, scout(regulator), scout(powerpath), refdesign(buck).
  No interface-spec agent - no standards-bound interface on this board.
- Regulator: AP63356QZV-7 / AP63357QZV-7 (VDFN-13 2x3, sync, 3.5 A, 3.8-32 V,
  450 kHz, hiccup+OTP, ~$1.08@5). Family is ADJUSTABLE-ONLY (catalog "Fixed"
  is a scrape artifact). 5V/3A table: L 6.8 uH, Cin 10 uF, Cout 2x22 uF,
  Cbst 100 nF, FB 157k/30k. EN self-starts, SS internal 4 ms. refdesign
  prefers the PWM-only 356Q for the 50 mV ripple spec.
- power: 4 LAYERS REQUIRED, deciding corner 7 V low line. Eff 92.6/93.6/93.6 %
  at 7/12/18 V, loss 1.03-1.20 W, Iin 2.31 A. Cin RMS ripple peaks 1.51 A at
  Vin=10 V. X7R only, no electrolytics. GND on In1+In2.
- powerpath: PMOS AOD403/AO4407A both <100 mW at 2.4 A. TVS floor SMBJ20A
  (32.4 V clamp). Inductors single-OEM (CENKER/XR). Terminals 14.1 mm vs 15 cap.
- CONFLICT for P2: thermal model used generic classes, never saw AP6335x
  (datasheet 25 C/W vs repo calibrated 51 C/W 4L) - run check_thermal for real.
- Held for H1: fuse 4 vs 5 A, load transient/polymer cap, Tj<=105 C hard?
