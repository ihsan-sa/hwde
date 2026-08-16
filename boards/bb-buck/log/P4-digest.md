# P4 Schematic - digest (2026-08-15)

- ONE schematic agent (flat root sheet, recorded deviation). Generator
  `kicad/gen/root.py` is the source; the .kicad_sch is build output.
- **Gates: erc 0 errors / 0 warnings; netlist_audit exit 0; sim PASS
  (0 err / 0 warn, 10 bounds, 18 measures).** 22 components, 8 nets.
- Cleared by the reviewer on datasheet evidence: EN->+VIN direct (Table 6-1
  sanctions it, and EN abs-max is VIN+0.3 so it cannot be violated by
  construction), PG open no-connect, EP=AGND tied to GND (the datasheet
  REQUIRES the tie), CFF correctly open (confirmed three ways), full abs-max
  sweep at 30 V, ton 417 ns vs 108 ns, Isat 8 A vs the strict 5.05 A criterion.
- **Fix pass, 3 changes.** E1 (error): C_OUT 2 -> **4 x 22 uF** - 2x is outside
  the internal compensation's optimised range (Sec 9.2 p19, quantified only in
  Table 9-2 p20 whose 400 kHz/5 V row is 4x; every 400 kHz row is 4x). Failure
  would have been SILENT at DC, visible only on load/line steps. W1: input bulk
  2 -> **3 x 10 uF** (the 10 uF minimum is EFFECTIVE, and 2x fell to ~8.5 uF in
  the worst corner). A3: divider **100k/24.9k -> 102k/25.5k**, exact 4.000
  ratio, 5.000 V nominal. +$0.52/board.
- **A3 amended a second time and requirements.md updated.** Sec 7.7 gives
  -1.5/+2.5 % regulation for IOUT 0 A to max (vs +/-1.5 % above 1 A) - the same
  PFM root cause as the ripple carve-out. Stacked worst case was 5.161 V vs the
  5.15 V ceiling; recentring moved it to 5.144 V. My earlier "DC accuracy
  unaffected" statement was wrong and is retracted in requirements.md.
- Sim calibration proved the light-load warning bound is load-bearing: a revert
  to 100k/24.9k produces ZERO errors and is caught ONLY by `vout_ll0a`. All four
  single-E96-step mutations trip at error severity.
- constraints.json placement.groups repaired by the orchestrator (hotloop was
  missing C10, output was missing C8/C9 and still said "1206"); W2 carried into
  the feedback group note - R2's return must pin to the AGND/EP reference.
- Library: C861068 has NO EasyEDA CAD record at all (lib_pull reports that
  identically to a rate-limit) - symbol cloned from its same-family sibling.
