# P3 Parts + Library - digest

- BOM 15 refdes / 11 LCSC lines, USD 5.70/board at qty 5. All five gain and
  pedestal resistors 0.1% 25 ppm/degC thin film - exactly what the P2 error
  budget assumed, no downgrade.
- R6 ADDED, overruling blocks.md B5: OPA2333 Fig.15 shows ~mid-30% overshoot
  into 1 nF and Q8 allows 1 nF of output cable. 100R provisional; the B4 bench
  settles it at P8.
- Connectors KF128-5.08, hand-soldered THT. J1 is a single 3-pole body so
  IN+/IN- junctions are identically built - the dominant 5 uV error term. The
  research's own witness was the CABLE half of a pluggable pair; caught here.
- Extractions validate (8 pins, land patterns, 10 layout_notes each). The
  AD8226 extraction independently cross-checked every number blocks.md cited -
  zero contradictions.
- Library: 11 symbols, 7 footprints, all catalog pulls, 33 pins retyped.
  fp_verify 4/4 PASS after one fix - J2/J3 pulled a 1.6 mm drill where the
  datasheet and J1's own entry both say 1.4 mm. Corrected.
- Coverage exit 0: 4 slots, 0 gaps; part slots covered, block slots
  provisional. 2 of 6 research budget unspent.
- Gaps recorded not smoothed: U1 pad size unverifiable (no vendor land pattern
  exists); B1's INL sim window is not a datasheet number.
