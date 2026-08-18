# bb-amp - P4 waivers

The `erc` gate itself is 0 errors / 0 warnings, so nothing is waived there. This file
records the disposition of the fresh-context `schematic-reviewer`'s findings
(`reports/review-schematic.md`, 0 errors / 5 warnings).

## Fixed, not waived (4 of 5)

| # | finding | disposition |
|---|---|---|
| W1 | The recorded error budget counted the R2/R3 ratio TCR (1.1 uV) but omitted the rail term that ratio multiplies. | FIXED in documentation. The pedestal is 0.2519/3.3 = 7.63 % of the rail and reaches the output at gain 1, so dVout/dVs = 0.0763 V/V (bench B6 measures exactly that) = 548 uV RTI per volt. The on-sheet accuracy note now states it and names it the DOMINANT post-calibration term, ahead of the 1.1 uV the table did count. |
| W2 | The sheet claimed U2A buffers the pedestal to "< 2 ohm at U1 REF", unqualified, which this board's own B9 bench contradicts. | FIXED. The sheet now carries the measured four-point Zout table (0.43 mohm DC / 0.17 ohm at 60 Hz / 2.86 ohm at 1 kHz / 116 ohm at 41 kHz), says the rule is EXCEEDED above ~700 Hz (350 Hz on the pessimistic ro=2k bracket), and states both why it does not bite here and what would invalidate that. |
| W3 | The equations box attributed "Eq.2 allows 1.33 V, G <= 66" to Vcm = 1.65 V; Eq.2 at 1.65 V actually gives 1.49 V and G <= 75. | FIXED. Two labelled rows now, with the 1.33 V / G <= 66 pair correctly attributed to the Vcm = 1.7325 V worst corner (rail -5 % AND excitation +5 %). |
| W4 | `KF128-5.08-2P` carried reference prefix "U" while its 3P sibling carried "J" - a re-annotate-with-reset would have renamed J2/J3 and broken constraints.json, parts.json and the P9 CPL. | FIXED in `lib/aiee.kicad_sym`. The librarian audited all 11 symbols; this was the only instance. |

## Waived (1 of 5)

**W5 - the connector checklist's "if destructive, flag" item is unmet for J3.**

Waived. J3 is the +3V3 power entry on a screw terminal, and the concern is a user wiring
it backwards or to the wrong supply. The mitigations the checklist has in mind - reverse
polarity protection, a keyed or polarized connector - are PROTECTION, which the
`block-only` scope tier excludes outright, so they are not available to this board and
their absence is not a finding here. What the board does carry is a silkscreen legend
naming the polarity at the terminal. Recorded rather than silently dropped: on a
`product`-tier version of this block, reverse-polarity protection at J3 would be REQUIRED,
not optional.

## Standing limitations noted by the reviewer (not findings)

- AD8226 Table 8's constants are interpolated linearly to 0 C / 50 C from the datasheet's
  -40 / +25 / +85 rows; the vendor publishes no bench-range values, so the diamond margins
  (>= 264 mV at full scale) inherit that interpolation.
- OPA2333's DC and low-frequency open-loop output impedance is not published (only 2 kohm
  at 350 kHz), so bench B9's Zout figures rest on a calibrated model bracket rather than a
  specification. Already flagged in the part extraction's own OPEN.
- Silkscreen legends, C1/C3 short-loop placement, and the unbroken B.Cu reference under
  the input pair are P6/P7 items and were not assessable at P4.
