# P2 Architecture - digest (2026-08-15)

- One block (B1 sync buck) + J1/J2 screw terminals + TP1/TP2 SW probe pair + 4x M3.
  14 parts, 6 nets, ONE FLAT ROOT SHEET. Canonical nets: +VIN /SW +5V GND.
  Stackup JLC2313_1.6 2L 1 oz CONDITIONAL (trigger: P_U1 > 0.95 W = Rds_LS > ~110
  mOhm at 400 kHz). **Outline 40 x 30 mm FINAL** - owner-confirmed at H1.
- fsw 400 kHz / L 15 uH. P1's fixed-output preference LOST to stock reality ->
  adjustable + 0.1 %/25 ppm divider, closing A3 on worst-case SUM. lint 0/0.
- Architect corrected 3 briefing premises, all verified (rules_gen already buckets
  per IPC-2152 width; planes[] REPLACES defaults and rejects `_note`; pdn:false also
  skips check_irdrop) -> LEARNINGS.md entry, incl. a latent sbuck-5v3a defect.
- Coverage at the mode floor: 1 slot / 10 classes all gap (8 maturity-only, 3
  substantive). Mapper skipped as a provable no-op. Research block-buck-1: 3 TI
  sources, 12+ pages read visually, 9 records. Reader REFUTED 1 (record said 0.3 uH,
  figure prints **9.3 uH** - 31x, mis-sized the damping criterion); corrected,
  re-read fresh -> **9 verified / 0 refuted**. Re-run: 9 covered / 1 provisional
  (inrush) / 0 gap.
- Design-relevant: hot-plug at 30 V rings to 45-49 V vs 38 V abs-max (A2 is what
  makes the clamp-free mode safe); the EP is **AGND**, so the via array is a
  loop-accuracy item; 2L is a documented deviation from the datasheet's layout rule 5
  at ~5 dBuV/m -> P6/P7 must keep the bottom pour unbroken under hot loop, SW and L.
- H1 APPROVED. Promotion of the 9 records deferred to run close with bring-up.
