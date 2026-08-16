# P3 Parts + Library - digest (2026-08-15)

- parts.json: 10 distinct parts / 13 refdes, ~$1.63/board, 1 Basic + 9 Extended
  (expected at this voltage/dielectric/case class). U1 has NO drop-in alternate:
  async candidates are D1-rejected, frequency siblings cascade into L/C_OUT re-derivation.
- **D4 CONDITION MET - 2 LAYERS CONFIRMED.** Real Rds_LS 66 typ / 110 max mOhm over
  full temp -> P_U1 0.57 W typ / 0.76 W worst-case vs the 0.95 W gate (~20 % margin,
  not the placeholder model's 2 C). D3 met (15 uH + 2x22 uF inside both windows);
  D11 met (Isat 8 A vs the 6.6 A floor, DCR 27 mOhm, 12.3 mm body).
- **A3 AMENDED by owner**: ripple <= 50 mV holds 200 mA - 2 A; larger PFM burst ripple
  accepted below that. The DDA package has no MODE pin and is auto-mode only (8.4.1),
  so none of the three accept criteria was satisfiable. DC accuracy unchanged at 0-2 A.
- Extraction C841384.json validated (exit 0, 9 pins incl. EP). Two traps caught: the
  68 ns min-on-time headline is the RNX part's (DDA is 75-108 ns; we need 417 ns, so
  ~3.9x margin), and the datasheet contradicts itself on thermal vias (10.1.1 text
  says 4x3 = 12, Fig 10-2 draws ~6) - our own >= 16 governs. EP confirmed **AGND**.
- Library: 10/10 pulled, tables created, load-check 6/6, 27 pins retyped, no B.Cu
  lands (single-sided holds), no netless PTH inside the EP (the LM5017 precedent did
  NOT repeat). RULED: accept the vendor U1 land (warning-level, and it is the
  footprint JLC's own process is built around) and the library-wide
  courtyard-cuts-pads class (placelib already unions pad bbox).
- **Coverage P3: 2 slots, 1 covered (part/datasheet-layout), 1 provisional (inrush),
  0 gaps.** No new research opened - block:B1 is the slot already researched at P2.
- OPEN RISK to P4 review: C_OUT 2x22 uF vs TI's 4x22 uF reference BOM - is ~32 uF
  effective inside the STABILITY window, or only the ripple budget?
