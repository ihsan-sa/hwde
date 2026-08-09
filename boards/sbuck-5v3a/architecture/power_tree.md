# sbuck-5v3a - power tree and loss budget (P2 reconciled)

Lifted from `research/power.json` and **re-run against the parts this
architecture actually chooses**. Where a number differs from the P1 fragment it
is marked and explained. Net names are the canonical ones from `sheets.md`.

Design point: `fsw = 500 kHz`, `L = 6.8 uH`, `Vout = 5.0 V`, `Iout = 3.0 A`.

---

## 1. Rail tree

| Rail | Source | Topology | Design current | Consumers | Diss (worst) |
|---|---|---|---|---|---|
| `/VIN` | J1 | direct | 2.6 A (2.44 A at 7 V) | F1, Q1 | 0.27 W at 7 V |
| `+VIN` | Q1 source | direct | 2.6 A | U1 2.42 A, C4-C9 1.5 A rms, R2/R3 140 uA | - |
| `/SW` | U1 | buck node | 3.6 A pk | L1 3.53 A pk | 0.45 W at 18 V |
| `+5V` | L1 | buck | 3.3 A ceiling (3.0 A spec) | J2 3.0 A, D1 1 mA, Cout 0.31 A rms | 0.005 W |
| `GND` | - | plane (F.Cu island + In1 + In2 + B.Cu) | 3.3 A return | all | 0.009 W |

No auxiliary rail, no bias rail, no sequencing. The board regulates whenever
`+VIN` clears the UVLO. Topology tradeoffs are settled and not re-litigated
here: an LDO would burn 21 W, a Schottky instead of the P-FET would burn 1.10 W
(54% of the whole budget), and a controller + discrete FETs is the escape hatch
only if no stocked integrated part met the s2 limits - one does.

---

## 2. Loss budget at the efficiency spec point (Vin = 12 V, Iout = 3 A)

`Pout = 15.0 W`; `> 88%` terminal-to-terminal (Q4) allows `Ploss <= 2.045 W`.
`D = 0.4167`, `dI = 0.858 A pk-pk`, `Iin = 1.42 A`, `I_L,rms^2 = 9.06 A^2`.
Silicon derated x1.4 and copper x1.30 for a ~100 C junction / hot board.

| # | Contributor | Expression | P1 budget | **P2 actual** | delta |
|---|---|---|---|---|---|
| 1 | Q1 rev-pol P-FET | `1.42^2 * 13 mOhm` (Vgs = -12 V, AO4407A max) | 0.071 | **0.030** | -0.041 |
| 2 | F1 input fuse | `2.016 * 20 mOhm` (5 A part, not 4 A) | 0.061 | **0.040** | -0.021 |
| 3 | U1 HS conduction | `9 * 0.4167 * 105 mOhm` (75 max x1.4) | 0.338 | **0.394** | +0.056 |
| 4 | U1 LS conduction | `9 * 0.5833 * 63 mOhm` (45 max x1.4) | 0.315 | **0.331** | +0.016 |
| 5 | U1 switching | `0.5*12*3*20n*500k` | 0.180 | 0.180 | - |
| 6 | U1 gate drive | `Qg*Vin*fsw` | 0.036 | 0.036 | - |
| 7 | U1 Coss | | 0.004 | 0.004 | - |
| 8 | U1 dead-time diode | | 0.036 | 0.036 | - |
| 9 | U1 quiescent | | 0.012 | 0.012 | - |
| 10 | L1 DC copper | `9.06 * 24.05 mOhm` (18.5 cold x1.30) | 0.290 | **0.218** | -0.072 |
| 11 | L1 core | allowance at 0.86 A pk-pk, 500 kHz | 0.150 | 0.150 | - |
| 12 | Cout ESR | | 0.001 | 0.001 | - |
| 13 | Cin ESR | ceramic bank only | 0.020 | 0.020 | - |
| 14 | PCB copper | | 0.077 | 0.077 | - |
| 15 | Screw terminals | | 0.110 | 0.110 | - |
| 16 | Bias: LED + UVLO + Zener + FB | 5.0 + 1.1 + 0.5 + 0.2 mW | 0.010 | **0.007** | -0.003 |
| | **TOTAL** | | 1.710 | **1.646** | **-0.064** |
| | **Efficiency** | `15 / 16.646` | 89.8% | **90.1%** | |
| | **Margin to 2.045 W** | | 0.335 (16%) | **0.399 (20%)** | |

**Three changes worth naming.** (a) Lines 3-4 went UP: AP64350's guaranteed
maximum Rds(on) is 75/45 mOhm, above the P1 fragment's 65/42 part limit, so the
limit is revised to the real part and the +72 mW is paid out of margin. That
sounds like a loss until it is compared: the same two lines with LMR33630's
*typical* 95/66 mOhm come to 0.984 W, +0.331 W over budget, which is the entire
margin (see `decisions.md` D1). (b) Line 10 went DOWN by the same 72 mW because
FAUL1050-6R8MT clears the DCR ceiling hot, not just cold. (c) Line 2 went down
because the 5 A fuse has *lower* DCR than the 4 A one.

Net effect: the budget closed 64 mW better than P1 predicted, and the margin
grew from 16% to 20%.

Model caveats carried forward unchanged from `research/power.md` s2: line 5
assumes linear V/I crossover (+/-40% on that line); line 6 charges from Vin
(a BST-referred model gives 15 mW); line 13 is the ceramic bank only, since the
bulk can's ESL means it carries almost none of the 1.5 A rms at 500 kHz - its
ESR is wanted for damping, not conduction.

---

## 3. Line extremes

| Line | Vin = 7 V | Vin = 12 V | Vin = 18 V |
|---|---|---|---|
| `D`, `dI pk-pk` | 0.714, 0.420 A | 0.417, 0.858 A | 0.278, 1.062 A |
| Q1 + F1 | 0.120 + 0.149 | 0.030 + 0.040 | 0.012 + 0.018 |
| U1 HS / LS conduction | 0.675 / 0.162 | 0.394 / 0.331 | 0.263 / 0.409 |
| U1 sw + gate + Coss + td + Iq | 0.170 | 0.268 | 0.386 |
| L1 DCR + core | 0.218 + 0.050 | 0.218 + 0.150 | 0.218 + 0.230 |
| Cin + Cout ESR | 0.017 | 0.021 | 0.018 |
| PCB Cu + terminals + bias | 0.105 + 0.150 + 0.010 | 0.077 + 0.110 + 0.007 | 0.070 + 0.099 + 0.008 |
| **TOTAL board loss** | **1.826 W** | **1.646 W** | **1.735 W** |
| Efficiency | **89.1%** | **90.1%** | **89.6%** |
| **U1 alone** | 1.007 | 0.993 | **1.058** |
| **L1 alone** | 0.268 | 0.368 | **0.448** |

**Worst total dissipation is still Vin = 7 V** (every input-side `I^2R` term
scales as `Iin^2`, 2.42 A vs 0.93 A) and it improved by 143 mW versus P1,
mostly from the lower-DCR fuse and the better P-FET operating point.
**Worst part dissipation is still Vin = 18 V**: U1 1.058 W (was 1.001) and L1
0.448 W (was 0.521). Those two numbers are what `constraints.json.thermal`
declares.

The 88% floor is specified at 12 V only and is met with 2.1 points. At 7 V the
same parts give 89.1% - low line is no longer the knife-edge it was in P1.

---

## 4. Thermal case - 50 C ambient, natural convection, no heatsink

Model unchanged from `research/power.md` s4 (whole-board, near-isothermal,
`R_ba = 19 C/W`, radiation 53% of the path). Two inputs corrected against the
real stackup, neither of which changes a conclusion:

- spreading length `lambda` = **32 mm** (JLC's inner copper is 0.0152 mm, not
  the 0.0175 mm assumed) instead of 33 mm - still larger than the 20-25 mm
  board half-dimension, so the whole outline is still the heatsink.
- thermal-via path F.Cu -> In1 is **0.2444 mm** of 1080x3 prepreg, not the
  0.21 mm the P1 fragment used (that figure belongs to the RETIRED phantom
  stackup JLC04161H-3313). `R_1via` = 29.4 K/W, a 16-via array at 0.85 crowding
  = **2.16 K/W**, against the 2.0 K/W the ladder assumed. Costs 0.2 C.

| | 7 V | 12 V | 18 V |
|---|---|---|---|
| Ambient | 50.0 | 50.0 | 50.0 |
| `P_board * 19` | +34.7 | +31.3 | +33.0 |
| board non-uniformity near U1 | +6.0 | +6.0 | +6.0 |
| `P_IC * (5 + 2.16)` junction -> plane | +7.2 | +7.1 | +7.6 |
| **Tj** | **97.9 C** | **94.4 C** | **96.6 C** |
| T_board surface | 84.7 C | 81.3 C | 83.0 C |
| T_L1 surface | 100.7 C | 103.3 C | 106.5 C |

**Worst Tj = 97.9 C at 7 V against the 105 C derated design limit: 7.1 C of
margin**, up from P1's 5.0 C. The limit is 125 C junction spec (the floor
across the candidate families; AP64350 specs 150 C, which would make the real
margin 52 C) minus 20 C of design margin.

Sensitivity is unchanged and is the single most important number for P3-P7:
**`dTj/dP_board = 19 C/W`. Every extra 100 mW anywhere on the board costs
1.9 C of junction temperature.** The 0.399 W efficiency margin is also 7.6 C of
thermal margin. Do not spend it.

L1's surface reaches ~106 C at 18 V, which is why the part must be rated
>= 125 C (FAUL1050 is 155 C, including self-heating).

### 4.1 Package rule (already met by U1)

Exposed pad mandatory, `theta_JC(bottom) <= 5 C/W`, datasheet
`theta_JA (JESD51-7 2s2p) <= 45 C/W`. Non-pad packages are excluded outright -
6 mm^2 of F.Cu alone gives `theta_JA = 138 C/W` and `Tj = 188 C`, which
quantitatively confirms the brief's warning that the pad does not close it.

AP64350 publishes `theta_JA = 45 C/W` (4L, 2 oz, minimum recommended pad),
exactly at the ceiling. **This is less binding than it looks**: the ladder above
does not use `theta_JA` at all - it uses `theta_JC(bottom)` plus the via array
plus a whole-board `R_ba`, and the IC's own local path is only 7 C of the 48 C
rise. **P3 verify-later: confirm `theta_JC(bottom) <= 5 C/W` from the AP64350
datasheet.** If it comes back above 5 C/W the ladder must be re-run.

The same argument disposes of SY8205's headline 30-36 C/W advantage: in this
thermal model a lower datasheet `theta_JA` buys almost nothing, because 37 of
the 48 C of rise is board-to-ambient shared by every watt on the board.

### 4.2 Copper area (P6/P7 act on this)

| Layer | Requirement | Why |
|---|---|---|
| F.Cu | GND island contiguous with U1's pad, **>= 100 mm^2**, not fragmented by SW or +VIN | first spreading hop |
| In1.Cu | **solid GND, no split within 12 mm of U1** (>= 400 mm^2) | the brief's uninterrupted plane under the switches; 0.2444 mm below the pad |
| In2.Cu | **GND as well, NOT a power plane**, >= 400 mm^2 under U1 | doubles inner spreading; 0.5 oz is useless as a power plane anyway |
| B.Cu | GND pour **>= 1500 mm^2** of 2000 | the second radiating face |
| all | GND within 14.3 mm of U1 summed over layers **>= 650 mm^2** | exactly what `check_thermal` measures (`A_sat = 645`); 529 mm^2 is the bare pass. With U1 near board centre each of In1/In2/B.Cu contributes ~640 mm^2, so this passes ~3x over |
| Q1 | >= 50 mm^2 of drain + source copper | 0.12 W on an 85 C board |
| F1 | >= 20 mm^2 per pad, kept off the U1/L1 zone | fuses run hot by design |

### 4.3 Thermal via array under U1

**0.3 mm drill, 0.55 mm land, 1.0 mm pitch, filling the exposed pad; minimum 9,
target 16**, plus a ring of 8-12 stitching vias at 1.2 mm pitch in the
surrounding F.Cu island. Tent with soldermask on the **bottom** side to stop
wicking; do not buy filled-and-capped via-in-pad. Windowpane U1's paste aperture
(4-9 sub-apertures, 60-70% area) so the array cannot float the part.

**`check_thermal` will NOT enforce this.** Its via warning fires only when
`dt_c/power_w < 51.1`; at the declared values (55 / 1.06 = 51.9) it stays
silent. The array is a **P6/P7 requirement enforced by review**. A clean
`check_thermal` is not proof the array exists.

---

## 5. Copper sizing (IPC-2152 at dT = 10 C)

`dT = 10 C`, not the brief's 20 C upper bound: IPC-2152's rise is above the
*local board* temperature, and s4 puts that at 81-85 C. A 20 C rise would put
copper at 105 C. The 10 C widths route fine here, so there is no reason to take
the looser number.

| Net | Design current | **1 oz OUTER, dT = 10** | 0.5 oz INNER, dT = 10 | route |
|---|---|---|---|---|
| `/VIN`, `+VIN` | 2.6 A | **1.52 mm** | 3.50 mm | 1.8 mm |
| `/SW` | 3.6 A | **2.31 mm** | 5.32 mm | 2.5 mm pour |
| `+5V` | 3.3 A | **2.06 mm** | 4.73 mm | 2.5 mm |
| `GND` return | 3.3 A | **2.06 mm** at any neck | 4.73 mm | plane, no neck < 2.1 mm |

Signal nets (`/FB`, `/EN`, `/BST`, `/COMP`, `/RT`, test taps): 0.25 mm.

The inner-layer column is computed at the **real** 0.0152 mm JLC inner copper
rather than a nominal 0.5 oz, which makes the widths 15% worse than the P1
fragment quoted. 3.5-5.3 mm per net is 7-13% of the board width each: **0.5 oz
inners cannot carry these rails, so In1 and In2 are both solid GND and no power
net touches an inner layer.** All of `/VIN`, `+VIN`, `/SW` and `+5V` stay on
F.Cu, which single-sided assembly (Q26) makes natural.

**SW width-vs-EMI, resolved:** IPC-2152 constrains *width*, EMI constrains
*area*. `/SW` is a **short wide pour - 2.5 mm wide, <= 8 mm long, <= 40 mm^2,
F.Cu only**, never inner, never near a board edge or a connector.

**Vias:** at 0.5 A/via a layer transition would need 6 on `/VIN`, 8 on `/SW`,
7 on `+5V`. **Design so there are none.** GND is plane-fed through the
stitching field.

Trace resistance targets at 85 C (1 oz sheet resistance 0.61 mOhm/sq):
`R_VIN <= 7 mOhm`, `R_+5V <= 4`, `R_SW <= 2`, `R_GND <= 1`. These are budget
line 14; a longer route spends junction temperature at 19 C/W per watt.

---

## 6. Fault behaviour

| Fault | Response | Bounded by |
|---|---|---|
| Reversed input | Q1 blocks; no current flows | AO4407A -30 V Vds, |Vgs| clamped at 15 V |
| Hot-plug of 18 V | ring to ~20 V at U1 VIN (0.10 Ohm path with the 80 mOhm bulk); 57 A / 10 us through Q1's body diode | IC abs max 42 V, MLCC 50 V, Q1 SOA 1-2 orders clear, fuse `I^2t` 0.058-0.19 vs 5.3 A^2s |
| Output overload | cycle-by-cycle peak limit, MIN 4.25 A | AP64350 OCP |
| Sustained output short | 512 cycles at limit -> hiccup 8192 cycles -> restart with soft-start; survives indefinitely, auto-recovers | Q29 satisfied by the IC alone; fuse stays intact |
| Shorted high-side FET | F1 opens (fault current is far above 5 A, so opening is in ms) | the only fault the IC cannot cover - this is why the fuse exists |
| Over-temperature | internal TSD at 160 C, 25 C hysteresis | Q8: no discrete cutout |
| Output over-voltage | >110% trips HS-off / LS-on independent of the FB loop | free extra layer, relevant to Q30 back-drive |
| In/out connectors swapped | **not survivable, by decision (Q30)** | silkscreen only |
