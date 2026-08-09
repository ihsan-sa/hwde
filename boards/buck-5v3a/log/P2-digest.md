# P2 Architecture - digest

- 6 blocks, 25 parts, ONE FLAT SHEET (one function/one rail; also dodges the
  /<sheet>/<LABEL> net-prefix trap). Lead parts: AP63356QZV-7, 6.8 uH shielded
  inductor, AO4407A-class P-FET, SMBJ20A TVS, fuse, WJ500V-5.08-2P terminals.
- Stackup JLC04162H-7628A: 4L, 2 oz outer / 0.5 oz inner, 1.6 mm.
  Outline 50x40 (full cap - 45x35 does not fit ~557 mm2 of parts + pour).
- Thermal machine-run (check_thermal, real 74/40 mohm Rds(on)): 0.88 W at the
  7 V corner -> 45.0 C rise / Tj 95 C on 4L PASS; 65.0 C / Tj 115 C on 2L FAIL.
- Conflicts ruled: datasheet 25 C/W LOSES to repo 51 C/W (JEDEC coupon vs our
  2000 mm2; 51 is what P8 applies). power.json's <=90 mohm filter DELETED - it
  rejected the whole real shortlist. Loss retabled 1.48 W / 91.0 % at 7 V.
- Cost ~$2.60 parts/board, ~$75-85 for qty 5. Riskiest: 2 oz outer (unpriced
  fab adder; fallback to the 1 oz class is one-way safe).
- H1 APPROVED. Rulings: Tj<=105 C soft; fuse -> 5 A time-lag (supersedes A5);
  height cap DROPPED (A8 clause void, M3 holes stand); +/-3% DC-only + fit an
  optional 100 uF polymer C7.
- P3 gaps to close: 6.8 uH inductor (none in any P1 sweep), 50 V X7R 10 uF,
  gate zener, 0.5 % FB resistors, UMW AO4407A Vgs(max)/Rds(on) confirmation.
