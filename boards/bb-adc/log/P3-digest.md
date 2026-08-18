# P3 Parts + Library - digest

- BOM 16 lines / 20 refdes, 7 Basic + 9 Extended, $155.16 at qty 5 ($31.03/board);
  U1 + U2 are 84 % of it. U1 single-source with an explicitly EMPTY alternates list.
- All three verification items CLOSED from primary sources: acquisition is a
  CLOCK-CYCLE COUNT (tSMPL 4.5-5.0 DCLOCKs) -> OPA320 final, OPA333 demoted; the -IN
  window is an ABSOLUTE -0.3/+0.5 V constant; ADR4520 still Rev 0 confirmed via a
  second independent channel, so the 87 mV margin stands.
- 3 extractions schema-valid; library 13 parts / 11 footprints loading clean; -IN
  typed as a signal pin, not power.
- BOARD-KILLER CAUGHT: J1 drilled 1.30 mm where the vendor specifies 1.50 mm. These
  terminals carry ~1.0 mm SQUARE pins (1.41 mm diagonal) - the part could not have
  entered its holes, and 1.30 mm CLEARS the annulus floor so every check passed.
  Corrected and re-verified.
- MAJOR OPEN RISK for P8: TI's own circuit for this converter+amplifier pair warns
  single-supply "loses codes near ground" and our span starts at 0 V. DC says ~61 uV;
  the transient is unproven. `zero-scale-swing` + `acquisition-settling` decide it.
  A -0.3 V generator is pre-ruled datasheet-required support but still a second rail.
- OPA320 passes the isolation screen OPA333 failed and publishes the flat 90 ohm R_O
  the method assumes; its settling is uncharacterised at our supply and load.
- Coverage 3/3 part slots COVERED; B2/B3/B4 provisional (maturity, not mapping);
  B1 gap on constraints-emission only. No research spent, 2 tasks remain.
