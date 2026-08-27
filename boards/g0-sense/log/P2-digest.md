# P2 Architecture digest - g0-sense (2026-08-27)

- architect (fable/high) wrote blocks.md / power_tree.md / stackup.md /
  sheets.md / constraints.json / decisions.md. constraints_lint exit 0.
- 4 blocks: B1 usbc-sink, B2 ldo, B3 mcu, B4 sht4x. Stackup JLC2313_1.6
  (2L, 1 oz, HASL). Two sheets (power / main), disjoint refdes + #PWR 100/200.
- No diff pairs, no high-speed nets, no sim bench (recorded, with reasons).
- P2 coverage exit: FIRST run 4 slots / 4 GAP (no checklist existed for any of
  usbc-sink, ldo, mcu, sht4x). research.py open --all -> 4 tasks (per_run cap
  6, 2 left for P3). 4 researchers -> 16 quarantined sources, 4 new checklists,
  23 draft records. 4 fresh second readers refuted 6. 5 were repaired against
  ledger pages and re-read; the NRST record took three repair/re-read cycles
  (each refutation narrower than the last) before verifying.
- FINAL: 22 of 23 records verified. Re-run coverage: 4 slots, 0 gap,
  4 provisional, 1 draft_unverified.
- The one unverifiable record (mcu boot-strap) is a container limit, not a
  research failure: st.com times out, so RM0454/AN2606 cannot be acquired.
  Its claim was load-bearing, so the DESIGN was changed to not need it.
- Two research-forced design changes vs the architect's plan: I2C pull-ups
  2.2k -> 1.5k (Rp ceiling arithmetic), BOOT0 no-strap -> R13 10k pull-down.
  architecture/{blocks,sheets,decisions}.md updated to match.
- H1 written to log/H1.md, approved as delegated. report_gen exit 0 (10 pp).
