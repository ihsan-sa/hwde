# P2 Architecture digest - sbuck-5v3a

- IC AP64350SP-13 at 500 kHz (RT=200k). Decided on MAX Rds(on) 75/45 mOhm vs
  LMR33630 TYPICAL 95/66; TI max column gives Tj ~112 C, over the 105 C limit.
  SY8205 rejected on a Preliminary datasheet with typ-only Rds.
- Stackup JLC04161H-1080B, 4 layer, 1 oz outer / 0.5 oz inner. F.Cu + In1 + In2 +
  B.Cu ALL GND - the single most load-bearing entry in constraints.json.
- 1 oz beats 2 oz here: JLC's only 4L/1.6mm 2oz-outer lamination has a 0.4284 mm
  L1-L2 prepreg vs 1080B 0.2444 mm, nearly doubling thermal-via resistance. Both
  vendor reference layouts (2 oz) lose on the real stackup.
- Budget 1.646 W at 12 V = 90.1% (spec >88%). Worst Tj 97.9 C at 7 V vs 105 C,
  7.1 C margin. Every extra 100 mW anywhere costs 1.9 C.
- ONE flat root sheet, 33 placed parts - hierarchy rejected to eliminate the
  /<sheet>/<LABEL> net-name mismatch class.
- Overrode delegate answer Q14: UVLO 6.5/6.0 V retargeted to 6.2/5.3 V. A 0.5 V
  hysteresis is LESS than this board own 0.49 V cable drop at 2.44 A
  (motorboating), and VON at the max corner lands ~7.0 V - at the minimum rated
  input. Side benefit: UVLO divider draw falls from 81-181 mW to 1-2 mW.
- Corrected three P1 numbers rather than inheriting them: thermal-via arithmetic
  had used a retired phantom stackup dielectric; spreading length 33 -> 32 mm;
  U1 power 1.001 -> 1.058 W. Re-run closes 64 mW BETTER than P1.
- BOM ~6.35 USD/board. Flagged: delivered cost at qty 5 is 13-16 USD/board once
  PCBA setup and Extended feeder fees amortise - NRE, not parts.
- Riskiest decision: the IC. Riskiest TASK: the compensation (vendor Rcomp/Ccomp
  are quoted for 2x22uF, this board has 5x22uF).
