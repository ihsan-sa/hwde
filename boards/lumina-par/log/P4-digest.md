# P4 Schematic digest - lumina-par

Artifact: `kicad/lumina-par.kicad_sch` + 5 child sheets, built from
`kicad/gen/*.py`. **erc PASS 0/0; netlist_audit exit 0.** 155 components,
76 nets, 46 BOM lines, 152 placed (30 DNP), ~$17.44/board. H2 approved.

- ERC passed first attempt; the one fix loop went on REVIEW findings (2 of 3 left).
- **Adversarial review found 3 errors the gates cannot see**, all fixed: COFF
  ROFF2 47k->30k (off-timer could never trip while shunted - dead in 176/243
  corners); `/NTC_LED` unprotected into 6.8-24.4 V harness (added R413/R415 +
  D401); `/DRV_EN0..3` no pull-down, latching all drivers ON in the
  +12V-before-+3V3 window (added R218-R221 at **10k, not 100k** - the enable
  pin's own 25 uA puts 100k at 2.5 V, above threshold).
- **Sheets found 3 more first**: BOOT network allocated nowhere (12 parts, the
  converter cannot switch without it); LM339LV is a 4-unit symbol that silently
  floated 9 pins; hysteresis wrong in SIGN on 3 of 4 channels - a broken harness
  chattered. All four bands now positive (+8.6/+17.3/+17.3/+18.7 K).
- ADC source impedance at a broken harness 10.18k -> 9.70k, inside the ICD
  ceiling for the first time (the old value bought margin with the defect).
- `/PWM0..3` are `/control/PWM0..3`; root-level naming measured and rejected.
- Open to P5+: DNP marking has no consumer (~30 parts); shunt-FET switching and
  tLEB unverified vs the 141 ns pulse (P8 bench).
