# P2 Architecture - digest

- J1 3-pole -> U1 AD8226 G1=39.9 (RG 1.27k, REF on a buffered 0.252 V node)
  -> U2B OPA2333-class G2=3.49, gain resistor RETURNED TO /VREF -> J2; U2A
  buffers the divider. Vout = 0.252 + 139.2*Vdiff. 14 parts, 2 ICs, one sheet.
- f-3dB 41 kHz (5.9x spec), 0.65 mA, 2.3 mW, JLC2313_1.6 2L, ~USD 6.6/board.
- The split is forced by the DIAMOND PLOT and the claim was VERIFIED on the
  page: printed p.19 gives Vout = G*Vdiff + Vref, so Eq.2 becomes
  Vcm + |Vout-Vref|/2 < Vs - V+LIMIT with NO gain term - Fig.9 (G=1) and
  Fig.12 (G=100) are the same hexagon. Max single-stage gain 66-95, not 147.
- ACCURACY MISSED AND RECORDED: 13.9 uV typ / 56.4 uV max offset drift over
  +-25 C vs a 5 uV budget, plus 30-87 uV gain drift at FS. That budget is
  10 ppm/degC of full scale; no 3.3 V-capable part reaches it. INA333
  alternative costed and rejected on evidence. Mode relaxed nothing.
- Research: 4 tasks, 2 rounds, 6/6 budget. Round 1 seeded a domain the library
  did not hold, but was witnessed by the wrong part - 7 of 13 refuted. Round 2
  re-witnessed from the AD8226 via an allowlisted Farnell mirror - 9 of 9
  verified. Net 16 verified records + 2 new checklists (`inamp`, `in`).
- Coverage exit 0: 2 slots, 0 gaps, 11 classes provisional (the correct
  ceiling - owner promotion makes approved, bring-up makes proven).
- 8 sim benches specified with numeric windows for the P8 `sim` gate.
