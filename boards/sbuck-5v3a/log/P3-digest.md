# P3 Parts + Library digest - sbuck-5v3a

- 24 distinct parts -> 33 refdes. 11 Basic / 13 Extended. $6.34/board at qty 1 breaks.
- fp_verify 3 passed / 0 failed / 2 pad_size warnings. 59/59 pins retyped, all
  13 footprints carry courtyards, lib tables registered under ${KIPRJMOD}.
- U1 theta_JC confirmed EXACTLY 5.0 C/W (p.4 table) - the architect's ceiling was
  <=5, so the junction ladder holds with zero margin. RT=200k -> 500 kHz confirmed
  from the datasheet's own formula. HS current limit 4.25/5.0/5.75 A.
- TWO library defects found and fixed, both approved as hand-edits (lib/EDITS.md):
  U1 EP was pulled 12.6% undersized (3.200x2.500 vs vendor 3.502x2.613 mm) on a
  zero-margin thermal design; and KiCad's stock 1206 fuse land differs materially
  from Bel's own (30% narrower in the pitch axis) on a 2.44 A part.
- F1's EasyEDA record genuinely 404s (probed - a real not-found, not the 403 rate
  limit). Filled from KiCad stock + vendor land rather than re-sourcing, because
  C3163312 is the only listing for a fuse confirmed ACTUALLY slow-blow.
- R6 116k -> 115k: 116k is not E96 and has zero 0603 stock; 115k/22.1k is what the
  AP64350 datasheet's own 5 V reference design specifies.
- Recorded as unknowns rather than guesses: FB bias current (not stated anywhere in
  the datasheet), minimum off-time (not stated), thermal-via count (vendor is only
  qualitative - our 16x0.3mm array is a derivation). Vendor thermal data is on 2 oz
  copper against our 1 oz build -> deferred to P8 check_thermal on real geometry.
- Single-source risks: L1 (763 pcs, no true second source), U1 (no pin-compatible
  alternate - differs from LMR33630 on 4 of 8 pins).
- Carried to P4: C4 polarity must come from the footprint silk mark, not its
  generic 1/2 symbol pins.
