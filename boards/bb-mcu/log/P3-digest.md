# P3 Parts + Library - digest (2026-08-16)

- `parts.json`: 9 lines (8 orderable + 1 footprint-only hole). 2 Basic /
  6 Extended, ~1.35 USD/board. U1 stock re-verified 18,977; alt C32908.
- Kept ST's stated cap values though 4.7uF/10nF/1uF are all Extended at 0603
  (verified: JLC's Basic list carries none of them up to 1206).
- U1 extraction validated: 20 pins, 5 layout notes, land from Figure 37. Its
  pinout agrees independently with the P1 scout and P2 architect.
- **DEFECT FOUND AND FIXED**: J1's pulled footprint drilled 1.30 mm where the
  vendor recommends 1.50 mm; the 0.90 mm pin's square diagonal is 1.273 mm =
  0.027 mm clearance, a terminal that does not seat. Approved hand edit to
  1.50 mm drill / 2.30 mm pad. fp_verify now 3/3 pass, 0 failed.
  Nothing in the pipeline would have caught it: fp_verify had no land pattern
  to diff until I ordered the connector extractions, and it has no
  drill-vs-pin check at all.
- U1 land deviation ACCEPTED on worked geometry (the pulled land still
  captures the lead foot, with more toe and a wider inter-pad gap than ST's).
- Coverage: 3 part slots covered, B1 provisional, B2 gap on the 3 classes
  already recorded at P2. No new research opened.
