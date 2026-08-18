# P9 DFM - digest (2026-08-17)

- Gate **dfm PASS 0/0**, attempt 2, commit 4471864. All EIGHT legs RAN and
  passed with no skips and no waivers: copper, copper_to_edge, drill,
  hole_to_edge, silk, polarity, bom, release.
- Acted on a prior run's recorded learning before gating: `gate.py --gate dfm`
  resolves `parts.json` from the BOARD's directory, so the BOM-completeness
  leg silently never runs when the file lives only at `parts/parts.json`.
  Copied it beside the board and VERIFIED the fix took - the coverage block
  shows `bom` in `ran` and `passed`, so the leg genuinely executed rather
  than being quietly absent.
- Fab package written: gerbers + zip, drill, `bb-mcu-pos.csv`, and the
  assembly trio `BOM-full.csv` / `BOM.csv` / `CPL.csv` with the per-package
  rotation corrections applied. Not hand-filtered.
- **P8 review F2 resolved by evidence**: the 0.582 mm2 zero-anchor copper
  island STAYS. DFM did not flag it with all 8 legs running, which is exactly
  the fab-process answer the reviewer said a render could not give. Deferring
  that call from P8 to P9 was the right order.
- Run STOPS here by mode - `block-only` defaults stop at P9 (fab package +
  DFM) and ordering is a separate owner decision. No attestation was built
  and no money step was approached.
