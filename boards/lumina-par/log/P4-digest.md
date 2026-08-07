# P4 Schematic digest - lumina-par

Artifact: `kicad/lumina-par.kicad_sch` + 5 child sheets, built from
`kicad/gen/*.py`. **erc gate PASS 0 errors / 0 warnings; netlist_audit exit 0.**
155 components, 76 nets, 46 BOM lines, 152 placed parts (30 DNP), ~$17.44/board.

- 5 sheets written in parallel (power/control/drivers/thermal/led_if) + root
  stitch. ERC passed first attempt; one fix loop consumed for REVIEW findings.
- **The adversarial review found 3 errors the machine gates cannot see** - all
  fixed and re-verified: (E-1) COFF ROFF2 47k->30k, the off-timer could never
  trip while shunted so shunt-dimming linearity was dead in 176 of 243 corners;
  (E-2) `/NTC_LED` reached the comparator with no series R and no clamp on a
  harness carrying 6.8-24.4 V anodes - added R413/R415 + D401; (E-3) `/DRV_EN0..3`
  had no pull-down and latched all four drivers ON in the +12V-before-+3V3
  window - added R218-R221 at **10k, not 100k** (the enable pin's own 25 uA
  makes 100k sit at 2.5 V, above threshold).
- **Sheets found 3 more before review**: the BOOT network was allocated nowhere
  (converter cannot switch without it, 12 parts added); the LM339LV is a
  four-unit symbol that silently floated 9 pins; the allocated hysteresis was
  wrong in sign for 3 of 4 channels and made a broken harness CHATTER.
- All four protection bands now positive (+8.6/+17.3/+17.3/+18.7 K). ADC source
  impedance at a broken harness 10.18k -> 9.70k, inside the ICD ceiling for the
  first time - the old value was buying margin with the W-1 defect.
- `/PWM0..3` are `/control/PWM0..3`; constraints re-spelled to match after the
  root-level naming route was measured and rejected (4x label_dangling).
- To H2: emitter-hot band 8.6 K vs a 15 K aspiration; shunt-FET switching still
  unverified vs the 141 ns pulse; DNP marking still has no consumer (P5/P9).
