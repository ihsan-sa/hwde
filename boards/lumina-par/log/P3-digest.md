# P3 Parts + Library digest - lumina-par

Artifact: `parts/parts.json` (47 lines), 18 datasheet extracts, `lib/` (91 sym /
23 fp), `reports/fp_verify_*`. Ran 2026-07-28; digest written at the resume.

- Emitters 4x C22434861 RGB + 4x C48586656 white, 2S2P, 150 mA/die.
- **OPEN-8 REFUTED**: no 140/120 deg beam mismatch - both datasheets say 140, the
  LCSC record is wrong. Diffuser spec and its 30-45 % flux cost must be re-derived.
- Sense 0.75 ohm (275 mA/ch); shunt FET SSM3K2615R (C22371361).
- **COFF network was MISSING, now fitted**: 12 parts, ROFF1 = 10k not TI's 8.2k;
  without it the shunt topology loses dimming linearity (TPS92515HV 8.3.4).
- CR-1 closed: R206 = 4.7 k 1 % (supersedes sheets.md "TBD"). CR-3 adopted:
  14-bit / 4.883 kHz PWM. CR-6 closed by ICD s7.7 A5. Emitter Rth still absent.
- fp_verify: 4 violations, all adjudicated (2 off-board emitter modules, thermal
  pad; L301/D501 approved KiCad-stock land deltas).
- **To H2**: shunt-FET switching UNVERIFIED at 3.3 V (toff 150 ns TYP > the 141 ns
  pulse; both gate-path ends ungrounded -> P8 bench); compounded light budget;
  power_tree.md quotes 300 mA where the board builds 275 mA.
- Tooling defects (central): lib_pull false-pass, fp_verify blind to drill,
  placelib ignores pad rotation -> hand to P6.
