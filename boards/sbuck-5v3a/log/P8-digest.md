# P8 Verification digest - sbuck-5v3a

Gates: `verify` PASS (0 failing, 2 waivers), `drc_routed` PASS 0/0. 2 of 3 fix-loop
attempts used. Fresh-context review: 2 errors / 12 warnings, both errors FIXED.

## The review found two errors that every gate had passed

- **CRITICAL - D2's `K` cathode marker was on the ANODE end.** Silk said pad 2
  (`/QGATE`); the cathode is pad 1 (`+VIN`). The netlist was always right. Fitted per
  that silk, the 15 V Zener reverses to a forward diode holding Vgs at -0.7 V, Q1
  never enhances, 2.6 A runs in its body diode at ~2.1 W in an SO-8 - Q1 and the
  reverse-polarity protection both destroyed. Moved to (45.900, 59.000): 0.640 mm from
  pad 1, 3.036 mm from pad 2, agreeing with the footprint band and pin-1 dot.
- **8 refdes labels named the wrong part** (`silk_misattributed` WARNINGS, so the
  error-only gate passed them). 8 fixed, 3 residual - at 1.0 mm text the label is
  2.6-3.2 mm wide against a 2.5-3.0 mm passive pitch, so no clean position exists.

## Machine findings, and what they turned out to be

- `check_thermal` L1: REAL. 100.7 mm^2 of +5V copper -> 48.10 C rise vs 45 allowed.
  Grew a +5V pour around L1's body -> 153.3 mm^2, **42.51 C**.
- `check_current` GND x2: a MEASUREMENT ARTIFACT over three real defects. `pour_neck`
  erodes each zone fill in isolation, so a pour split across zone objects reports a
  phantom 0.00 mm neck. Underneath were three genuine sub-2.055 mm via attachments in
  1.06-1.58 mm fingers. Repartitioned the zones; 3 unhomeable ring vias deleted.
- `check_silk` x7: CHECKER DEFECT (check_silk.py:172 buffers an unfilled circle into a
  filled disc). Waived, then the underlying rings were deleted at P9 anyway.
- `check_pdn` x2: waived. Corrected reason - it never looks at the board, it filters
  decoupling.json and errors on an empty list, so it is a TRUE statement that no
  association named those rails. Coverage comes from check_irdrop instead.

## IR drop on the real copper (all three power nets)

| Net | I | R | worst drop | jmax |
|---|---|---|---|---|
| +VIN | 2.60 A | 5.36 mOhm | 14.0 mV | 2.65 A/mm |
| +5V | 3.30 A | 2.71 mOhm | **9.0 mV** | 2.41 A/mm |
| GND | 3.30 A | 0.34 mOhm | **1.1 mV** | 0.46 A/mm |

`check_pdn_z` passes. Richardson deltas 0.03-0.05, so the grids converged.

## Self-correction worth recording

Setting `pdn: false` on +5V and GND silenced check_pdn's finding but ALSO excluded
both nets from check_irdrop - the two highest-current nets on the board. Reverted and
waived instead: a waiver says "this check does not apply" without disabling unrelated
analysis.

## Thermal, restated honestly

check_thermal's "0.83 C headroom" on U1 is NOT a layout property: a_eff measures
2137 mm^2 and clamps to A_SAT 645, so theta is constant for any 4L board above
645 mm^2 - the 12 vias and three planes move it by 0.00 C. The believable figure is
the P1/P2 board ladder, corrected for 12 vias rather than 16 (2.16 -> 2.88 K/W):
**Tj ~98.7 C, margin 6.3 C** against the 105 C design limit, with a +/-30% band of
87.5-108.4 C. Spec floor is 125 C and abs max 150 C. The dominant lever is MOUNTING,
not layout - 53% of cooling is radiation from two faces.
