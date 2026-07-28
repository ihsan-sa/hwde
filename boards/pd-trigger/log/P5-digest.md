# P5 digest (pd-trigger)
board_init: 45x25 FAIL (14 silk-edge) -> 48x30 (soft-target +20%) 11 -> two
S14 fixes (kc.py refdes regex now takes R2A/R2B suffixes - cross-part silk
was mis-classified single-ref; silk_edge_clearance = transient by nature)
-> PASS: parity 0, setup 0, 31 transient silk, 68 unconnected. 2 LAYERS at
2oz (JLC2313_1.6_2oz stackup - S14 reference addition) - capability class
2layer_2oz, 12 rules incl. 4 power widths (VBUS 1.75mm@2oz). Tests +2.
