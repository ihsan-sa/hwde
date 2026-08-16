# P2 Architecture - digest (2026-08-15)

- One block (B1 sync buck) + J1/J2 screw terminals + TP1/TP2 SW probe pair + 4x M3.
  14 parts, 6 nets, ONE FLAT ROOT SHEET (a child-sheet label exports as
  /<sheet>/<LABEL> and silently unhooks constraints - the class that cost lumina-par).
  Canonical nets now binding: +VIN /SW +5V GND (/FB, /BST undeclared by design).
- Stackup JLC2313_1.6, 2L, 1 oz - CONDITIONAL, escalation trigger named numerically
  (P_U1 > 0.95 W = Rds_LS > ~110 mOhm at 400 kHz). Outline **40 x 30 mm FINAL**.
- fsw 400 kHz / L 15 uH (part is fixed-400 kHz, inside P1's band). P1's fixed-output
  preference LOST to stock reality -> adjustable + FB divider at 0.1 %/25 ppm, which
  closes A3 on worst-case SUM (2.5 %) not just RSS. constraints_lint 0/0 (verified).
- Architect corrected 3 premises in its own brief, all verified: rules_gen already
  buckets power nets per IPC-2152 width (no flattening defect); planes[] REPLACES
  layer defaults and rejects unknown keys incl. `_note`; `pdn:false` also skips
  check_irdrop/check_pdn_z so it was dropped from GND. -> LEARNINGS.md entry.
- **Coverage (mode floor `proven` + --research-provisional): 1 slot, 10 classes, all
  gap** - 8 blocked only on maturity, 3 substantive (inrush outside on source_kind,
  snubber outside on rectifier_kind, COT outside on control_kind). Mapper skipped as
  a provable no-op (every record already keyed; edges cannot move maturity/envelope).
- Research task block-buck-1: 3 sources (LMR33630 SNVSAN3F vendor-layout + 2 TI app
  notes), 12+ pages read visually, **9 records, 9 verified / 0 refuted**, depth 3/4.
  Second reader REFUTED one on first pass (record read Li as 0.3 uH; the figure prints
  **9.3 uH** - a 31x error that mis-sized the damping criterion). Corrected, re-read
  fresh-context with gridline-calibrated vector measurement, verified.
- **Re-run coverage: 9 covered / 1 provisional (inrush) / 0 gap, exit 0.** Research
  narrowed the only genuine library hole; the owner's promotion ruling closes it.
- Design-relevant findings: (a) hot-plug at 30 V would ring to 45-49 V vs the part's
  38 V abs-max - A2 (no live hot-plug) is what makes the clamp-free mode safe;
  (b) the EP is **AGND**, the reference all electrical parameters are measured to, so
  the thermal via array is a loop-accuracy item; (c) 2L is a DOCUMENTED deviation from
  the datasheet's own layout rule 5, measured ~5 dBuV/m - binds P6/P7 to keep the
  bottom pour unbroken under hot loop, SW and inductor.
