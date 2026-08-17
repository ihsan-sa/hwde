# P3 Parts + Library - digest

- BOM = 4 distinct parts / 5 placements, ~$1.05/board at qty 5: U1
  AMS1117-3.3 SOT-223 (C6186, Basic), C1 10 uF/16 V solid Ta (C7171, Basic),
  C2 22 uF/16 V solid Ta (C215872), J1=J2 WJ500V-5.08-2P (C8465).
- **C2 was the judgment call**: acceptance test is ESR INSIDE 0.3-22 ohm (too
  LITTLE ESR oscillates this part). Chose 800 mohm; rejected a 300 mohm
  polymer (window edge, 6.3 V) and a 90 mohm part (ceramic-class). Residual:
  LCSC parametric attribute, not a Vishay page. Not marginal, not blocking.
- J1/J2 THT is forced, not preferred - JLC has no SMT terminal at this pitch.
- C6186.json clean; it correctly REFUSED to invent a land pattern (the AMS
  datasheet has none, only package body dims).
- **Two findings that could have killed the board silently:**
  1. The pulled footprint gives the TAB its own pad 4 (KiCad's standard reuses
     pad 2). The schematic MUST wire pin 4 to +3V3, or the tab is netless, the
     pour never connects, and ERC passes on a board with no heatsink.
  2. easyeda2kicad drew courtyards around the PLASTIC BODY (U1 leads 2.57 mm
     outside). Hand-edited under approval to pad bbox + 0.25 mm on U1/C1/C2.
     Matters because `--outline fit` measures courtyards.
- fp_verify U1 pass post-edit; C1/C2 polarity confirmed pin 1 = positive.
