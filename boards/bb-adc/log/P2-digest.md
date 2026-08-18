# P2 Architecture + coverage research - digest

- Chain: screw terminal -> 5x 200k 0.02%/10ppm equal string tapped 3:2 (K = 0.400,
  Rtot 1.00 Mohm, guarded tap) -> RRIO CMOS buffer -> ADS8326-class 16-bit SPI SAR,
  VREF 2.048 V from an ADR4520-class reference. FS 5.12 V. 2L JLC2313_1.6, ~$30/board.
- Budget RSS 3.23 mV @25 C / 3.36 mV over 0-50 C vs 5.0/12.0; worst case 8.35/10.29.
  Claimed on RSS, worst case published beside it.
- Converter overruled from P1: MCP3201 gain error +/-5 LSB MAX = 6.10 mV = 1.22x the
  whole budget. LSB-denominated DC specs shrink 16x from 12 to 16 bits.
- Q9 narrowed (owner-visible): source <= 200 ohm, board 1.00 Mohm, both on silk. As
  answered the two specs were jointly impossible at 0.1 % (Rs/Rtot = 1 % = 50 mV).
- Key move: -IN is a dedicated remote sense to the string's bottom node. A divider
  passes ground offset at UNITY while dividing signal by K, so 1 mV = 2.5 mV
  input-referred; the sense line cancels it. sheets.md said "-IN = GND" and was fixed.
- Buffer OPA320-class: OPA333 fails at t_acq 9 us (GBW floor 849 kHz vs 350 kHz; own
  settling 40.4 us). A buffer AT ALL is unconditional - switched-cap R_eq =
  1/(f_s*C_SH) ~ 2.08 Mohm vs 240 kohm Thevenin is ~10 % gain error.
- Series R at the converter rail entry REINSTATED: the datasheet's own recommended
  circuit shows it, so it is required support, not excluded filtering.
- Research: 4 tasks, 16 sources, 32 verified records + 4 checklists, 3 correction
  rounds each. Coverage now provisional everywhere except B1 constraints-emission,
  recorded as a designed-under gap. Promotion deferred (shared library, live siblings).
