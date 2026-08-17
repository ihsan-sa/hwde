# P2 Architecture + coverage research - digest (2026-08-16)

- Architecture written, `constraints_lint` exit 0: 2 blocks (`mcu`,
  `swd-debug-port`), stackup JLC2313_1.6 2L, one flat root sheet, 9 parts.
  Nothing relaxed by the mode - the brief stated no size to lose.
- Coverage fired as designed: first call at floor `proven` with
  `--research-provisional` -> both blocks gap, no checklist existed for either.
- 2 research tasks -> 13 records + the library's FIRST `mcu` and
  `swd-debug-port` checklists. 3 sources each, no forum sources, caps not hit.
  All 13 verified by fresh readers.
- The refute loop caught 3 real defects: a decoupling envelope bounded on the
  wrong axis (twice - now correctly `level: principle`), a false "every Min
  cell is blank" claim (tEXTIpw has Min 10 ns), and a family-level
  `external_series_required: false` contradicting its own sibling record.
- Re-run coverage: `block:B1` provisional on all 5 rows; `block:B2` gap on
  esd / decoupling / constraints-emission -> explicit designing-under-gap
  decision (riskless: two are classes block-only excludes).
- Key design finding: VDDA carries the internal RC oscillators and the PLL
  (DS Fig 12), so on this crystal-less board VDDA IS the clock supply and a
  filter into it would be a FAULT, not merely out of scope.
