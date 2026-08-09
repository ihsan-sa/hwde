# sbuck-5v3a - answers to the brief's "BEFORE DECLARING DONE" checklist

Synchronous buck: 7-18 V DC in (12 V nom) -> 5.0 V +/-2% at 3 A. 50 x 40 mm, 4 layer.

---

## 1. DRC and ERC clean, zero unrouted nets

| Gate | Result |
|---|---|
| `erc` | **PASS** - 0 errors, 0 warnings |
| `place` | **PASS** - 0 violations |
| `drc_routed` | **PASS** - 0 errors, 0 warnings, **0 unrouted (71/71, completion 1.00)** |
| `verify` (8-check suite) | **PASS** - 0 failing, 2 waivers |
| `dfm` (on exported gerbers) | **PASS** - 0 failing, 16 warnings |

Two waivers remain, both `check_pdn`, both audited by a fresh-context reviewer who
confirmed the call and corrected my reasoning: check_pdn never inspects the board, it
filters `decoupling.json` and errors on an empty list, so it is a true statement that no
association named +5V or GND. Coverage comes from `check_irdrop` instead (below).

## 2. Recomputed from the parts actually chosen

### Inductor peak current - L1 = FAUL1050-6R8MT, 6.8 uH, 500 kHz
dI = (Vin - Vout) * D / (L * fsw), D = Vout/Vin. Worst at the HIGHEST input:

| Vin | D | dI | dI as % of Iout | Ipk = 3.0 + dI/2 |
|---|---|---|---|---|
| 7 V | 0.7143 | 0.420 A | 14.0% | 3.210 A |
| 12 V | 0.4167 | 0.858 A | 28.6% | 3.429 A |
| **18 V** | **0.2778** | **1.062 A** | **35.4%** | **3.531 A** |

**Ipk = 3.531 A at Vin = 18 V.** Ripple lands at 35.4% at the high line, inside the
brief's 20-40% target band. L1's Isat was qualified at 50 C AMBIENT, not 25 C - every
ferrite-wound candidate failed that test and was rejected on it.

### Input capacitor RMS current
Icin_rms = Iout * sqrt(D * (1-D)), maximised at D = 0.5:

| Vin | D | Icin_rms |
|---|---|---|
| 7 V | 0.7143 | 1.355 A |
| **10 V** | **0.5000** | **1.500 A** |
| 12 V | 0.4167 | 1.479 A |
| 18 V | 0.2778 | 1.344 A |

**Worst = 1.500 A at Vin = 10 V - INSIDE the operating range, not at the 12 V nominal
point.** Shared across 4x 4.7 uF/50 V X7R 1206 (C29823) plus the 100 nF close-in cap.

### Output ripple - dV = dI/(8 * fsw * Cout) + dI * ESR

| Cout (effective) | capacitive | ESR (2 mOhm) | total pk-pk |
|---|---|---|---|
| 75.0 uF (low corner) | 3.54 mV | 2.12 mV | **5.66 mV** |
| 85.2 uF (geo mean) | 3.12 mV | 2.12 mV | **5.24 mV** |
| 96.8 uF (high corner) | 2.74 mV | 2.12 mV | **4.87 mV** |

**~5 mV pk-pk against a 50 mV limit - about 10x margin.** Cout is quoted as a BAND, not
a point, because no vendor DC-bias curve exists for any MLCC on this board (see
"honest limits" below).

### Junction temperature at 50 C ambient, natural convection
**Tj ~ 98.7 C, margin 6.3 C** against a 105 C design limit (125 C spec floor minus
20 C). Model band at the tool's own +/-30%: **87.5 - 108.4 C**. AP64350 abs max is 150 C.

Two models disagree and the difference matters:
- `check_thermal` reports 54.17 C rise vs 55 allowed - "0.83 C of headroom". **This is
  not a property of this layout.** a_eff measures 2137 mm^2 and clamps to A_SAT 645, so
  theta is a constant for any 4-layer board above 645 mm^2; the 12 vias and three
  ground planes move it by 0.00 C.
- The P1/P2 board-level ladder (h_conv 7.41, h_rad 8.08, R_ba 19.0 C/W, independently
  reproduced to ~2% by the reviewer) is the believable one, corrected for 12 vias
  rather than 16 (2.16 -> 2.88 K/W, +0.76 C).

**The dominant thermal lever is MOUNTING, not layout: 53% of cooling is radiation from
two faces.** An enclosure that blocks one face invalidates this number.

Efficiency at 12 V / 3 A: **90.1% modelled** (1.646 W loss of the 2.045 W allowed by
the >88% floor).

## 3. LCSC stock - all 24 distinct parts confirmed in stock

`bom_complete: true`, zero missing LCSC codes. Full table in `parts/parts.json` and
`fab/BOM.csv`. Notable lines:

| Ref | Part | LCSC | Tier | Stock |
|---|---|---|---|---|
| U1 | AP64350SP-13 | C2071691 | Extended | 11,849 |
| **L1** | **FAUL1050-6R8MT** | **C5298292** | Extended | **763** |
| Q1 | AO4407A | C16072 | Extended | 28,272 |
| F1 | 0685T5000-01 | C3163312 | Extended | 5,032 |
| J1/J2 | DB128L-5.08-2P-GN-S | C395868 | Extended | 27,058 |
| C10-C14 | TCC1210X7R226K250MT | C49118556 | Extended | 123,041 |

**L1 at 763 pcs is the thinnest line on the board and has no true second source** - no
non-cjiang part meets 6.8 uH / <=25 mOhm-hot / stock together. Re-check before ordering.
U1 also has no pin-compatible alternate (AP64350 and LMR33630 differ on 4 of 8 pins).

## 4. The four geometry numbers

| Deliverable | Measured | Requirement |
|---|---|---|
| **Input loop enclosed area** | **2.57 mm^2**, and **ZERO vias inside it** | minimise |
| **Switch node copper** | **30.44 mm^2**, F.Cu only (0.000 on In1/In2/B.Cu), >=3.0 mm wide, 5.70 mm from the nearest edge, 16.6 mm from J2 | <=40 mm^2 ceiling, >=2.5 mm floor |
| **Feedback trace** | **2.03 mm** from C12's +5V pad to the tap; 2.21 mm R6->U1 pin 5; **13.3 mm from L1**, 2.94 mm from /SW | short, away from SW/L1, tapped at the OUTPUT CAP |
| **Thermal vias** | **12** in U1's exposed pad (3x4 at 0.90 mm, hole-gap 0.600 vs JLC's 0.500 floor) **+ 6 ring vias** | 12 (16 is geometrically impossible - see below) |

FB senses at the output capacitor terminal, not the inductor pin, so it regulates the
right node. C9 (100 nF) sits 0.7 mm off U1's VIN pad with its return through a 0.67 mm
inter-pad slot - no vias in the loop.

**16 thermal vias cannot fit.** The exposed pad is 3.502 x 2.613 mm; four 0.55 mm lands
at 1.0 mm pitch need 3.55 mm, and JLC's 0.5 mm hole-to-hole floor caps the array at
3 x 4 = 12. Cost is +0.5 C. The 16 figure was our own derivation - the datasheet says
only "add as many vias as possible".

### IR drop measured on the real copper

| Net | Current | Resistance | Worst drop | jmax |
|---|---|---|---|---|
| +VIN | 2.60 A | 5.36 mOhm | 14.0 mV | 2.65 A/mm |
| +5V | 3.30 A | 2.71 mOhm | **9.0 mV** (0.18% of 5 V) | 2.41 A/mm |
| GND | 3.30 A | **0.34 mOhm** | **1.1 mV** | 0.46 A/mm |

---

## Honest limits - what is NOT proven

1. **Load step sits AT the 200 mV limit, not inside it.** 148 mV modelled; 200 mV on
   the corrected reading after the model's vendor calibration was withdrawn (the
   vendor's published Bode plot has C4 = 33 pF fitted, so the original comparison used
   the wrong circuit variant). No R5 value clears fc, PM and dV together, and dV is
   mathematically invariant in Cout, so more capacitance would be pure cost.
2. **Loop phase margin is UNBOUNDED BY ANALYSIS at the true Cout floor.** PM 45.6-52.8
   deg on the DC-bias-only band, but stacking hot-X7R derating and aging gives ~62.7 uF
   and PM ~42-44 deg, under the 45 deg floor. Only a network analyser closes this.
   **R5/C2/C3 are three adjacent 0603 parts - re-tunable without a respin. Bench item #1.**
3. **No vendor DC-bias curve exists for ANY MLCC on this board.** Every effective-
   capacitance figure is a conventional-industry estimate. This is the dominant
   uncertainty and it propagates into every loop number above.
4. **Q1's dv/dt immunity and body-diode single-pulse rating cannot be bounded** - the
   AO4407A datasheet publishes no Ciss/Crss/Coss and no body-diode pulse curve.
5. **Hot-plug inrush peak is not closed from published data.** Screw terminals are a
   wire-then-power connector, and C4's 80 mOhm ESR is a stated damping requirement.
6. **3 of 11 refdes labels still name a neighbouring part** (C9->C7, R7->C12, C2->C3).
   No clean position exists at 1.0 mm text against a 2.5-3.0 mm passive pitch. All
   FUNCTIONAL legends are correct: "VIN 7-18V", "VOUT 5V 3A", polarity marks, and the
   TP1-TP7 signal names.
7. **Min F.Cu island gap is 0.1021 mm against JLC's 0.1016 floor - 0.5 um of margin.**
   Any future pour edit risks tripping `dfm_clearance`.
8. **No SPICE was run.** Both nominated benches were DC-tolerance fragments already
   verified twice analytically; house policy forbids simming the buck switching for
   lack of vendor models.
9. **JLCDFM and payment are human steps** - this package is order-READY, not ordered.
