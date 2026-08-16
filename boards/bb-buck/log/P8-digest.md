# P8 Verification - digest (2026-08-16)

- **All gates PASS**: verify 0 failing / 27 (2 waived), drc_routed 0/0, sim 0/0,
  place 0/0. check_irdrop 0 violations (+VIN 6.97 mV, +5V 12.68 mV, GND 0.61 mV
  at 0.233 mOhm); check_pdn_z 0 violations.
- Round 1, five script errors, THREE different resolutions - only one a waiver:
  pour neck -> constraints `overrides` (rung 4) after the fixer PROVED no copper fix
  exists (0.523 mm ceiling at the DRC floor, 1.134 mm deleting every foreign F.Cu
  track); silk-over-pad -> **fixed check_silk**, which drew every circle as a filled
  disc ignoring `(fill no)` (stock TestPoint ring clears its pad by 0.140 mm; the
  reported 1.77 mm2 was exactly the whole pad); check_pdn x2 -> waived per P2's D7.
- Round 2, fresh-context board review: **2 errors + 11 warnings**, both errors real.
  E1 the terminals carried NO polarity or function silk at all - the P0 requirement
  ("silk is the only defense against a swapped supply") was written and never reached
  copper. E2 only **9 in-pad EP vias vs the datasheet's 12**, correcting MY OWN P3
  decision, which had wrongly treated ">= 16 within 4.6 mm" as clearing a minimum
  that counts only vias UNDER the pad.
- E2 fixed: array re-spaced 3x3 -> **3x4**, barrel conductance 87.4 -> 116.5 % of the
  datasheet floor, **-4.91 K Tj**. E1 fixed: 4 of 6 labels placed (J1 "+"/"VIN",
  J2 "-"/"5V OUT"); on a 2-pin terminal one glyph determines the pinout, so the
  requirement is met. The fixer declined the 2 it could not place unambiguously.
- **GATE BLIND SPOT, measured**: check_thermal margin is 2.0623 C BEFORE and AFTER
  adding three vias - theta_ja() reads copper area and layer count only, and
  `vias_near_part` is reported but never used. On a 2L board whose whole heat path is
  the EP array, the thermal gate cannot see the array. This is what let 9-vs-12 pass.
- **NEW RISK to H4**: the EP is a single 100 % paste aperture over 12 open barrels -
  sink:source 2.59x. Bottom ends ARE tented, so it wicks rather than drips through.
  Owner decision at H4: accept / fab note requesting a windowed stencil / footprint
  edit + U1 re-place.
