# P6 Placement - digest

- Hand-placed canonical layout; EVERY anneal candidate rejected. Root cause recorded:
  place_anneal RE-DERIVES satellite slots from place_seed rather than inheriting the
  placement handed to it, so a 0.7 % hpwl win cost a 60 % violation of a declared
  decoupling distance (C3 3.97 mm against a 2.5 mm limit). hpwl 327.23 -> 223.47 mm.
- Gate `place` PASS 0/0; route probe completion 1.00 (41/41); 25/25 front, 25/25 locked
  (the guard room, tap stub, sense tie and string order are specifications no gate can
  re-verify - locking is what stops a later pass optimising them away).
- Geometry EARNED: 63.95 x 66.03 provisional -> 54.750 x 34.920 mm, 1911.9 mm2. The
  J1-to-R1 span decomposes as 4.5 mm connector body + 2.0 mm screwdriver access +
  0.8 mm pad approach = 7.3 mm. The earlier 16.5 mm was not merely unearned, it was
  WORSE: every record touching that net says leakage and pickup scale with length.
  H1/H2 - not J1 - had been defining the west edge.
- Silk 0 warnings after silk_place (2 refdes moved, no residual).
- Handed to P7: the SPI fan needs exactly 2 crossings (J2 CS,SCLK,DOUT vs converter
  CS,DOUT,SCLK is a 3-cycle), and the guard ring cannot close through the 0.35 mm
  U3 pin2/pin3 channel, so it must encircle V- together with the input pin.
