# P3 Parts + Library - digest (2026-08-15)

- parts.json: 10 distinct parts / 13 refdes, ~$1.63/board, 1 Basic + 9 Extended.
  U1 has NO drop-in alternate (async candidates D1-rejected; frequency siblings
  cascade into L/C_OUT re-derivation).
- **D4 MET - 2 LAYERS CONFIRMED**: real Rds_LS 66 typ / 110 max mOhm over full temp
  -> P_U1 0.57 typ / 0.76 W worst-case vs the 0.95 W gate, ~20 % margin (the
  placeholder model predicted 2 C). D3 met (15 uH + 2x22 uF inside both windows).
  D11 met (Isat 8 A vs 6.6 A floor, DCR 27 mOhm, 12.3 mm body).
- **A3 AMENDED by owner**: <= 50 mV holds 200 mA - 2 A, PFM burst ripple accepted
  below. DDA has no MODE pin, auto-mode only (8.4.1). DC accuracy unchanged.
- Extraction validated (9 pins, EP = **AGND**). Traps: the 68 ns min-on-time headline
  is the VQFN part's (DDA 75-108 ns vs our 417 ns need); 10.1.1's 4x3=12 vias
  contradicts Fig 10-2's ~6 - our >= 16 governs. Two DDA revs with different EP sizes.
- Library 10/10 pulled, 6/6 load-check, 27 pins retyped, no B.Cu lands, no netless PTH
  in the EP (LM5017 precedent did not repeat). RULED: accept the vendor U1 land
  (warning-level; it is what JLC's process is built around) and the library-wide
  courtyard-cuts-pads class (placelib unions pad bbox).
- **Coverage P3: 1 covered (part slot) / 1 provisional (inrush) / 0 gaps.**
- OPEN RISK to P4 review: C_OUT 2x22 uF vs TI's 4x22 uF reference - stability or only
  ripple?
