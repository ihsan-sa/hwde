# P1 Research - digest (2026-08-16)

- Roster: component-scout, then reference-design + interface-spec off its
  shortlist. power-architect skipped (one external rail = trivially powered).
- MCU RULED **STM32F030F4P6TR** (C89040, TSSOP-20, 19k stock, $0.96). Rejected
  CH32V003 (SWIO needs a WCH-Link, rewrites J2), PY32 (puya.com not on the
  fetch allowlist), C011 (hides BOOT0 on SWCLK), G031 (68 in stock).
- Minimum system, cited: REQUIRED = 100 nF VDD + 4.7 uF bulk, 10 nF + 1 uF
  VDDA, 10k BOOT0 pull-down. RECOMMENDED-ONLY and so excluded by mode = VDDA
  filter, NRST cap. SWD adds zero parts. Nine parts total.
- SWD binds nothing on layout (5 ns edge settles ~1.5 ns vs a 125 ns half-bit;
  JLC has no impedance-controlled 2L stackup). Guidance stays advisory.
- Ruled: J2 order **GND/SWCLK/3V3/SWDIO/NRST** (3V3-at-centre is the unique
  reversal-safe arrangement); no SWD series R (overruling RPi/Lauterbach/
  SEGGER); no NRST cap (diverges from stm32-blinky); omit the diff_pairs key.
- ENV: st.com unreachable from this host (HTTP 000 after 20 s); fetch ST
  primaries via wmsc.lcsc.com. AN4325/RM0360/errata are on NO allowlisted
  host - name the host in OPEN if a record needs one. See log/env-notes.md.
