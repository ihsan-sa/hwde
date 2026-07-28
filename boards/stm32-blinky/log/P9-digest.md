# P9 digest (stm32-blinky)
dfm a1 FAIL 14: 12 silk slivers (0.003-0.02mm2, EasyEDA body outlines) +
2 copper "gaps". ALL FOUR root causes were CHECKER defects, fixed w/ tests:
(1) dfm silk sliver warn band <0.05mm2 (golden mutant 0.344 stays error);
(2) gerblib FLAT trace caps vs KiCad's circular apertures -> phantom island
splits (2 FP errors) AND w/2 copper-to-edge understatement (FN direction) -
router diagnosed, refused to greenwash, one-line round-cap fix;
(3) bom_cpl ref->LCSC unmappable from S6 parts.json shape -> board_lcsc_map
reads per-footprint LCSC fields (exist since the P5 field fix);
(4) parts.json role drift synced. dfm a2 PASS 0 err/13 warn (non-gating).
BOM complete, 2 CPL rotation corrections (SOT-223, LQFP per jlc_rotations).
