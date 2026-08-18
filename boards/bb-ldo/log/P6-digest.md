# P6 Placement - digest

- **Board size EARNED: 50.000 x 26.420 mm** (1321 mm2). Gate place pass, all 5
  checks ran, commit b8d5678. HPWL 173.3 -> 103.4. Route probe 1.00 (planes).
- Anneal cand1 (best HPWL) OVERRULED on a measurement: it fits to
  88.29 x 12.42 mm with only 517 mm2 of pour inside a decay length. HPWL is
  near-fiction here - +3V3 is plane_fed, so its trunk IS the pour.
- U1 rot 180, tab (pin 4) facing open field; caps on the pin side. Pour =
  **1210.78 mm2, ONE island, 0 orphaned**; 1071 mm2 within 25 mm of the tab.
- **The width was nearly inherited, not earned**: placement.edges is graded
  against whatever outline is on the board, so J1/J2 got pinned to
  board_init's provisional 86.29 mm - the bb-buck defect mirrored (a STATED
  size bound bb-buck; an unearned PROVISIONAL one bound this). Fixed by moving
  the connectors in, then fitting: board -38.7%, effective copper within
  25 mm -0.8%, within 20 mm +6.8%.
- Width derived by sweeping BOTH axes - squarer captures more of the decay
  disc, so 50 x 26.42 beats the 55 x 24.42 first proposed on size AND thermal.
  48 mm clears 1000 mm2 by only 2.0%, inside the +5V route assumption's error.
- Silk legend added (J1 +5V/GND/IN, J2 +3V3/GND/OUT) + a "+" over C2's anode,
  whose only marks were hidden under its own body.
- **Order finding**: silk_place solves against the outline ON the board, so at
  a canonical binding it must run AFTER the fit, or it reports an empty
  residual while leaving labels off the final board.
