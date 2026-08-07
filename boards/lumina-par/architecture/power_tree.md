# lumina-par (LUM-PAR-A) - power tree and the sustained-power table

**REVISION B - P2 delta after the H1 checkpoint (2026-07-28).** Rebuilt against
the four directed changes recorded in `decisions.md` s0. The emitter package set
changed (H1-Q2: RGB 3-in-1 + separate white discrete, superseding the integrated
4-in-1), so **every row of s1-s3 has been re-derived from scratch rather than
carried forward**, and s5/s6 are re-derived for the new two-package thermal
topology and the sealed / wall-conducted enclosure (H1-Q1).

Baselined on **ICD-01 rev A2**. All figures are for **branch A (`+12V`)**, which
H1 confirmed and which is **not reopened**; branch B (`+48V_SW`) is tabulated in
s7 only so the record stays complete.

Every number below is arithmetic on live-verified part data or on the P1 research
constants. Nothing is lifted from a brief without being re-derived. Where a
datasheet does not publish a figure, this file says so.

---

## 1. The design point, and where the numbers come from

### 1.1 The new emitter set - live-verified this session

Both part numbers below were re-verified with `parts_search.py` in this session.
No LCSC code in this file is quoted from memory.

| Role | MPN | LCSC | Package | Stock | $ @1 / @30-50 / @100-150 | Dies |
|---|---|---|---|---|---|---|
| **RGB** | XINGLIGHT **XL-HD6070RGBC-A46L-BD** | **C22434861** | SMD8080-6P, 14.5 mm lead span, 5.15 mm tall | **6461** | 0.5288 / **0.3724** @30 / 0.3144 @100 | R + G + B, 1 W / 350 mA each |
| **WHITE** | XINGLIGHT **XL-HD6070UWC-A4-BD** | **C48586656** | SMD (HD6070 body, 6 x 7 mm lamp area) | **1790** | 0.2957 / **0.2332** @50 / 0.2062 @150 | 1 x white, 3 W / 700 mA |

Live-verified attributes that this design uses:

| Attribute | RGB 3-in-1 (C22434861) | White (C48586656) |
|---|---|---|
| Vf | **R 1.8-2.4 V, G 2.8-3.4 V, B 2.8-3.4 V** | **2.8-3.4 V** |
| Forward current, rated | 350 mA per die | 700 mA |
| Power, rated | 1000 mW per die | 3 W |
| Dominant wavelength | R 620-630, G 520-530, B 455-465 nm | 6000-6500 K |
| **Viewing angle** | **140 deg** | **120 deg** - see the TRAP below |
| Operating temperature | **-40 to +85 C** | **-40 to +85 C** |
| Junction temperature max | **125 C (PUBLISHED)** - P1 datasheet extraction | **120 C (PUBLISHED)** - P1 datasheet extraction |
| Thermal resistance Rth(j-s) | **NOT PUBLISHED** | **NOT PUBLISHED** |
| JLC assembly class | **SMT Assembly** (difficulty High) | discrete, hand-placed on the module |

**TRAP - the two packages do not share a beam angle, and this is live-verified,
not inferred.** LCSC lists the RGB 3-in-1 at **140 deg** and the white at
**120 deg**. This was cross-checked against three sibling parts in the same
session: `XL-HD6070UBC-A4-BD` (C48586653) and `XL-HD6070SURC-A4-BD` (C48586650)
are both **140 deg**, while `XL-HD6070WWC-A4-BD` (C48586655), the warm white, is
also **120 deg**. So the split is **white-versus-colour inside the family**, not a
single bad record, and P1's family-level claim that "the 6070 family is 140 deg"
(`research/led-emitter.md` s10) is **wrong for the white parts**. This design is
sized on the narrower 120 deg figure and the mismatch drives a first-order
PAR-REQ-15 problem - `stackup.md` s5.2 mechanism 3. **P3 must confirm both angles
from the datasheets.**

### 1.2 The new arrangement, derived from the Vf figures

The RGB package provides R, G and B; white is now a separate package. The die
count per channel is therefore a free choice for the first time, so it is derived
rather than inherited.

**Step 1 - what string lengths the `+12V` rail permits.** A buck cannot make an
output above its input, and the TPS92515HV-class driver needs headroom plus the
sense-resistor drop. Series string voltages at the published worst-case Vf:

| Series count | Red string | G / B / W string | Verdict on `+12V` |
|---|---|---|---|
| 2S | 2 x 2.4 = **4.8 V** | 2 x 3.4 = **6.8 V** | **fits, with 5.2 V of headroom on the worst channel** |
| 3S | 7.2 V | **10.2 V** | 1.8 V of headroom before the ballast and the sense resistor - too tight for a buck at 12 V nominal with the rail's own tolerance |
| 4S | 9.6 V | **13.6 V - above the rail** | impossible |

**So every channel is 2S, on both package types.** That result is forced by the
published Vf, and it is the same conclusion the 4-in-1 reached for the same
reason - the two packages publish **identical Vf ranges** (live-verified in s1.1),
so the string-voltage half of the design point is genuinely unchanged.

**Step 2 - how many dies per channel.** With a 2S string fixed, the channel is
either 2S (one branch) or 2S2P (two branches). Both give the same string voltage
and, for a given channel current, the same power - so **this is not an electrical
choice, it is an optical and thermal one**:

| | 2S - 2 dies/channel | **2S2P - 4 dies/channel** |
|---|---|---|
| Die current at 300 mA/channel | 300 mA | **150 mA** |
| Flux at the same watts | reference | **~7 % more** (less droop at half the current) |
| Heat per die | 2x | **1x** |
| Packages needed | 2 RGB + 2 white | **4 RGB + 4 white** |
| PAR-REQ-15 (fringing) | 2 colour sources, 2 white sources - a colour **dipole** the arrangement cannot cancel | **4 + 4, arranged so the RGB centroid and the white centroid coincide exactly** (`stackup.md` s5.2) |

**2S2P wins on PAR-REQ-15, which is the requirement the package change put at
risk.** With the white on a separate package, a 4+4 checkerboard is the only
arrangement that makes the two colour centroids coincide, and centroid coincidence
is what removes first-order shadow fringing. The 7 % flux gain and the halved heat
per die come free with it.

**Step 3 - the ballast.** Two parallel 2-die branches need Vf matching or
per-branch ballast. **1.5 ohm per branch, on the module's MCPCB, not on this
board.** At 150 mA that is a 0.225 V drop and 2 x (0.150^2 x 1.5) = **0.0675 W per
channel**, 0.27 W across four channels - 3.1 % of the af envelope. Same-reel
purchase (H1-Q4, AMD-01) plus 1.5 ohm against ~1-2 ohm of die dynamic resistance
holds branch imbalance to <= 10-20 %.

### 1.3 The design point

| Item | Value | Source |
|---|---|---|
| Emitter packages | **4x C22434861 (RGB 3-in-1) + 4x C48586656 (white)** = **8 packages** | s1.1, s1.2. Supersedes "4x 4-in-1" |
| String per channel | **2S2P**, 1.5 ohm ballast per parallel branch | s1.2 step 1-3 |
| Channel count | **FOUR - R, G, B, W. Unchanged.** | s1.4 |
| Design current | **150 mA/die = 300 mA/channel** | back-solved from the `+12V` 0.75 A sustained ceiling, s3 |
| Vf, typ | R 2.1 V, G/B/W 3.1 V | midpoint of the live-verified ranges |
| Vf, worst case | **R 2.4 V, G/B/W 3.4 V** | live-verified maxima - **this is the column the hardware backstop is sized on** |
| Ballast | 1.5 ohm per parallel branch, 0.225 V at 150 mA | s1.2 |
| Buck efficiency | **91 %** (conservative; the loss inventory computes 92.3 %) | derived |
| Idle (shunted) channel input | **0.20 W** | s2 - dominated by the catch diode |
| `+3V3` housekeeping | **<= 5 mA (0.017 W)** | s4 |

Load voltage per channel (string + ballast) at 300 mA:

| Channel | Dies | typ | **worst case** |
|---|---|---|---|
| Red (2S2P, in the RGB packages) | 4 | 2(2.1) + 0.225 = **4.425 V** | 2(2.4) + 0.225 = **5.025 V** |
| Green (2S2P, in the RGB packages) | 4 | 2(3.1) + 0.225 = **6.425 V** | 2(3.4) + 0.225 = **7.025 V** |
| Blue (2S2P, in the RGB packages) | 4 | **6.425 V** | **7.025 V** |
| **White (2S2P, in the 4 white discretes)** | 4 | **6.425 V** | **7.025 V** |

Per-channel power at 100 % duty. `P_load = V_load x 0.300`; `P_in = P_load / 0.91`;
`I = P_in / 12`:

| Channel | load W (typ) | in W (typ) | **load W (worst)** | **in W (worst)** | **`+12V` A (worst)** |
|---|---|---|---|---|---|
| Red | 1.328 | **1.459** | 1.508 | **1.657** | **0.1380** |
| Green | 1.928 | **2.118** | 2.108 | **2.316** | **0.1930** |
| Blue | 1.928 | **2.118** | 2.108 | **2.316** | **0.1930** |
| White | 1.928 | **2.118** | 2.108 | **2.316** | **0.1930** |
| **All four** | 7.110 | **7.813** | 7.830 | **8.604** | **0.7170** |

### 1.4 The channel count is confirmed at four, and the allocation holds unchanged

**Stated explicitly because the package change is the kind of change that
silently grows a channel.**

The RGB 3-in-1 carries three independently-wired dies (6 leads, live-verified
`SMD8080-6P`); the white discrete carries one. That is **four electrically
independent colours, exactly as the 4-in-1 provided** - the change moved a die
from one package to another, it did not add or remove a colour. Therefore, with
no change whatsoever:

- **Four driver channels** (`drivers` sheet, U301/U321/U341/U361), four shunt
  FETs, four sense resistors, four catch diodes, four inductors.
- **Four PWM lines**, `/PWM0` .. `/PWM3` on J4, one LEDC timer-0 group.
  `PWM4..PWM7` remain deliberate no-connects (`sheets.md` s2).
- **Four gating channels** from the single 74LVC00A quad NAND. One package still
  covers the board.
- **J5 stays 10-way**: 4 anodes + 4 per-channel returns + `/NTC_LED` +
  the dedicated NTC sense return. See `blocks.md` B6 for why the second package
  type does **not** add an eleventh conductor.
- `constraints.json` `power[]` keeps four `/LEDn_A` entries at **0.30 A** each.

**No fifth channel on rev A.** D8's reasoning is unchanged and is in fact
reinforced: s3 row 1 still consumes ~96 % of the `+12V` sustained ceiling, so a
fifth channel still takes ~20 % from the other four in every mixed colour.

---

## 2. Where the 0.20 W idle term comes from, and why it matters

Unchanged by the package swap - this term is set by the driver stage, not by the
emitter - but re-stated because s3 depends on it.

Under shunt-FET dimming (`blocks.md` D2) the converter **free-runs at its current
setpoint whatever the commanded duty**; the shunt FET diverts current away from
the string. A channel commanded to 0 % therefore still burns power.

Loss inventory for one channel at 0 % duty, 300 mA, 12 V in, 47 uH:

| Element | Loss |
|---|---|
| Catch Schottky (60 V, Vf 0.45 V at 0.3 A), conducting ~100 % of the cycle because the duty collapses to ~0.5 % | **135 mW** |
| Inductor DCR (0.3 ohm) | 27 mW |
| Driver IC quiescent (~2 mA at 12 V) | 24 mW |
| Switching loss at ~700 kHz | ~30 mW |
| Shunt FET (50 mohm at 0.3 A) | 4 mW |
| **Total per idle channel** | **~0.22 W - 0.20 W used below** |

Three consequences, all load-bearing:

1. **Four idle channels cost 0.8 W, ~9 % of the af envelope**, and that is the
   state a saturated-colour wash spends most of its time in. This is the
   quantitative case for the **converter-idle one-shot** in `blocks.md` B3.
2. **The one-shot does not help at the dimming floor** (row 8), because pulses are
   still arriving.
3. **The idle term never makes a partial-colour point worse than full white**,
   because 0.20 W is smaller than the 1.66-2.32 W a lit channel draws. **Full
   white remains the worst case in every operating mode.**

**Specify a 60 V Schottky on branch A, not a 100 V one** (100 V parts run
0.6-0.7 V at 0.3 A and would push the idle term to ~0.3 W/channel).

---

## 3. Sustained-power table at realistic mixed-colour operating points

**af column.** Duty-weighted: `P_in(d) = d x P_full + (1 - d) x 0.20 W` per
channel, on the worst-case-Vf column. `+3V3` adds 0.017 W to every row and is
shown only in the total. Percentages are against the `+12V` **0.75 A** sustained
ceiling and the **2.0 A** converter OCP (ICD s6.2).

| # | Operating point | R | G | B | W | `+12V` W | **`+12V` A** | vs **0.75 A** | vs **2.0 A OCP** | total W |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Full white - all four at 100 %. The stuck-PWM hardware backstop** | 100 | 100 | 100 | 100 | 8.604 | **0.717** | **96 %** | **36 %** | **8.62** |
| **2** | **Full-room warm wash, high intensity (R + G + W heavy) - the worst case the profiles actually call for** | 100 | 80 | 20 | 100 | 6.488 | **0.541** | **72 %** | 27 % | 6.51 |
| 3 | Full-room warm wash, saturated gold | 100 | 60 | 10 | 100 | 5.854 | 0.488 | 65 % | 24 % | 5.87 |
| 4 | Saturated red | 100 | 0 | 0 | 0 | 2.257 | 0.188 | 25 % | 9 % | 2.27 |
| 5 | Saturated green | 0 | 100 | 0 | 0 | 2.916 | 0.243 | 32 % | 12 % | 2.93 |
| 6 | Saturated blue | 0 | 0 | 100 | 0 | 2.916 | 0.243 | 32 % | 12 % | 2.93 |
| 7 | Deep magenta | 100 | 0 | 100 | 0 | 4.373 | 0.364 | 49 % | 18 % | 4.39 |
| 8 | **PAR-REQ-01 dimming floor** - all four at 5 % perceived, gamma 2.2 (duty 0.05^2.2 = **0.137 %**) | 0.137 | 0.137 | 0.137 | 0.137 | 0.811 | 0.068 | 9 % | 3 % | 0.83 |
| 9 | ENABLE de-asserted (fixture powered, dark) | - | - | - | - | 0.01 | 0.001 | <1 % | <1 % | 0.03 |

Worked example for row 2, so the method is checkable:
`R = 1.657` (100 %); `G = 0.8(2.316) + 0.2(0.20) = 1.853 + 0.040 = 1.893`;
`B = 0.2(2.316) + 0.8(0.20) = 0.463 + 0.160 = 0.623`; `W = 2.316`.
Sum `= 6.488 W`; `/12 = 0.541 A`.

With the converter-idle one-shot fitted, rows 4-7 become **1.657 / 2.316 / 2.316 /
3.973 W** (0.138 / 0.193 / 0.193 / 0.331 A). Rows 1-3 and 8-9 are unchanged.

Typical-Vf column, as the expected-case reality:

| # | `+12V` W (typ Vf) | `+12V` A (typ Vf) |
|---|---|---|
| 1 | 7.813 | 0.651 |
| 2 | 5.895 | 0.491 |
| 3 | 5.320 | 0.443 |
| 7 | 3.977 | 0.331 |

### 3.1 THE HEADLINE, RECOMPUTED

**Full white at worst-case Vf draws 0.717 A on `+12V`: 95.6 % of the 0.75 A
sustained ceiling and 35.9 % of the 2.0 A converter OCP. The headline is
95.6 %, and it rounds to the same 96 % the pre-H1 package produced.**

**That coincidence is a result, not an oversight, and it must be read correctly.**
The two packages publish **identical forward-voltage ranges** (R 1.8-2.4 V,
G/B/W 2.8-3.4 V - live-verified for both in s1.1), and the derivation in s1.2
lands on the same 2S2P / 150 mA/die arrangement for reasons that are independent
of which package carries the white die. So the **electrical** design point
survives the package change essentially unchanged, and that is the useful finding:

- **What did NOT move:** string topology, per-channel voltage, per-channel current,
  every row of the sustained-power table, the driver channel count, the sense
  resistor value, the harness current rating, `constraints.json` `power[]`.
- **What DID move:** the package count (4 -> 8), the number of thermal paths
  (1 -> 2), per-package heat, the module MCPCB, the optics (s5.2 of
  `stackup.md`), the emitter BOM cost, and the sourcing risk profile.

The 0.02 W difference against revision A's 8.62 W / 0.718 A is rounding in the
per-channel intermediates, not a design change; this revision carries the
per-channel values to four figures and totals them before rounding.

### 3.2 The four findings this table produces

1. **The worst case the music profiles actually call for (row 2) is 72 % of the
   hardware maximum**, and the saturated-gold variant (row 3) is 65 %. A warm wash
   drops blue, and blue is a full 2.316 W channel. So PAR-REQ-11's firmware clamp
   **rarely bites for warm content**; it bites for white and for pastels.
2. **Full white is the worst case in every mode.** No mixed colour, no dimming
   level and no fault state exceeds row 1. Verified against all nine rows.
3. **Row 1 is the stuck-PWM case by construction.** With ENABLE asserted and every
   PWM stuck at 100 % (hung MCU - the 2 s watchdog fade cannot help if the MCU is
   what hung), the current setpoint is fixed by the sense resistors, so the draw is
   bounded at **0.717 A: 4.4 % under the 0.75 A sustained ceiling and 2.8x under
   the 2.0 A OCP.** The board is electrically incapable of exceeding its own
   budget, which requirements s3.3 demands and calls not optional.
4. **The >3 A conditional flag (requirements s8) is NOT triggered and is closed.**
   Maximum per-channel current is **0.30 A** (af), 0.51 A (at, branch A). Nothing
   on this board, on its harness or on the module approaches 3 A.

### 3.3 H1-P7 RE-DERIVED: 150 or 145 mA/die

**H1 explicitly reopened this and the pre-H1 answer does not carry forward.** The
constraint that makes it matter: **the PAR-REQ-11 total-power clamp is firmware,
and firmware hangs**, so the board must sit under the carrier's *hardware* fault
ceilings with every PWM stuck at 100 % and no firmware alive.

At 145 mA/die (290 mA/channel): ballast drop `1.5 x 0.145 = 0.2175 V`; ballast
loss `2(0.145^2 x 1.5) = 0.0631 W/channel`.

- Red: `4.8(0.290) + 0.0631 = 1.4551 W` load -> `/0.91 = 1.599 W` -> 0.1332 A
- G/B/W: `6.8(0.290) + 0.0631 = 2.0351 W` load -> `/0.91 = 2.236 W` -> 0.1864 A
- Total: `1.599 + 3(2.236) = 8.308 W` -> **0.6923 A**; with `+3V3`, **8.325 W**

| | **150 mA/die** | **145 mA/die** |
|---|---|---|
| `+12V` worst-Vf draw | **8.604 W / 0.7170 A** | **8.308 W / 0.6923 A** |
| vs `+12V` **0.75 A sustained ceiling** (ICD s6.2) | **95.6 % - PASS, 4.4 % margin** | **92.3 % - PASS, 7.7 % margin** |
| vs `+12V` **2.0 A converter OCP** (hardware trip) | **35.9 % - PASS, 2.8x** | 34.6 % - PASS, 2.9x |
| vs ICD s6.2 **8.5 W total** (firmware-governed average, NOT a hardware trip) | 8.62 W - **1.4 % over** | 8.325 W - **2.1 % under** |
| Reflected PD input current at 48 V, incl. carrier 2.4 W housekeeping, 90 % carrier conversion | (8.62/0.90 + 2.4)/48 = **0.250 A** | (8.325/0.90 + 2.4)/48 = **0.243 A** |
| vs **TPS2378 current limit 0.85 A MINIMUM** (E-6 - the real hardware trip, not the 1.0 A typical) | **3.4x margin - PASS** | 3.5x margin - PASS |
| Relative light | 1.000 | **0.967 (-3.3 %)** |

**Every genuine HARDWARE fault ceiling passes at both currents, and neither is
close.** The 2.0 A OCP has 2.8x margin; the PD's 0.85 A minimum limit has 3.4x.
The only figure 150 mA/die fails is the **8.5 W ICD total**, and ICD s6.2 states
in its own words that the total *"is enforced by firmware's average-energy
governor"* - it is not a trip, and the correct hardware comparator for a
firmware-dead case is the per-rail ceiling.

**RECOMMENDATION: 150 mA/die, unchanged.** The 3.3 % of light that 145 mA/die
costs buys margin only against a number that is not a hardware limit, in a fixture
that `research/led-emitter.md` s5 already calls "a dark-room instrument"; and
the diffuser that H1-Q2 now makes mandatory (`stackup.md` s5.2) costs a further
**30-45 % of the delivered flux**, which makes every remaining lumen worth more
than it was before H1.

**Two things that would flip this recommendation, stated so they are not lost:**
(a) if the carrier owner declares the 8.5 W total a *hardware* limit rather than
a firmware governor, 145 mA/die becomes mandatory; (b) if the diffuser bench test
(`stackup.md` s5.2) shows the fixture needs the high-transmission diffuser and the
light budget is still short, the answer is a *higher* current, not a lower one,
and there is no room for it on `+12V` - it would reopen the rail. **This is a
sense-resistor value and remains changeable as late as P3.**

---

## 4. Rail-by-rail budget

| Rail | J3 pins | af ceiling | **design max (af)** | headroom | at ceiling | **design max (at)** | Fault ceiling |
|---|---|---|---|---|---|---|---|
| `+48V_SW` | 1, 3, 5 | 0.25 A | **0 A - landed, not tapped** | n/a | 0.50 A | 0 A | 1.0 A eFuse, latch off |
| `+12V` | 9, 11 | 0.75 A | **0.717 A** | **4.4 %** | 1.25 A | **1.250 A** (the ceiling itself - s5 solves for it) | 2.0 A converter OCP |
| `+3V3` | 12, 14 | 0.25 A | **0.005 A** | 98 % | 0.25 A | 0.005 A | 1.0 A converter |
| **Total** | - | 8.5 W (ICD) / 8.6-9.3 W (req) | **8.62 W** | see s3.3 | 18.5 / 18.7-20.0 W | **15.02 W** | PSE overload ~50-75 ms |

**Connector pin loading** (ICD s4.1 derate: 1.80 A/pin): `+12V` at 0.717 A over
2 pins is **0.359 A/pin, 5.0x margin**. GND at 0.722 A over 7 power-block pins is
0.103 A/pin, 17x. Neither is near a limit, and this board consumes none of the
48 V pin allocation.

### `+3V3` housekeeping inventory

Unchanged by the package swap - nothing on `+3V3` touches the emitters.

| Load | Current |
|---|---|
| Quad open-drain comparator, 4 channels | 0.20 mA |
| 2x NTC divider (10 k + 10 k) | 0.35 mA |
| `ID_ADC` bottom leg (worst case) | 0.33 mA |
| 74LVC00A + SN74LVC1G08, dynamic at 9.766 kHz + static | 0.13 mA |
| Comparator reference ladder | 0.10 mA |
| Pull-downs: ENABLE, 4x PWM, 4x shunt gate; FAULT pull-up (all 100 k) | 0.30 mA |
| 24C32 EEPROM standby | 1 uA |
| **4x `/DRV_ENn` fail-safe pull-downs (10 k) - ADDED AT P4** | **1.22 mA** |
| **Total** | **~2.7 mA; budget <= 5 mA (0.017 W)** |

**P4 amendment.** The row above is new and it is the single largest `+3V3`
line item. Original total read "~1.4 mA". The pull-downs are **10 k, not the
board's usual 100 k, and the value is load-bearing**: the TPS92515HV enable
pin sources up to 25 uA, so 100 k would sit at 2.5 V - above the 1.0 V
threshold - and would leave the fail-safe defect it was added to fix
(adversarial review E-3: with +12V up and +3V3 not yet, the four enable pins
are undriven and latch all four drivers on, a full-current LED flash). Of the
1.32 mA total only 1.22 mA comes off `+3V3`; the remaining 0.10 mA is the
drivers' own hysteresis current, sourced from their +12V-derived VCC. The
rail table's `+3V3` design-max of 0.005 A still holds, with 46 % headroom.

`+3V3` is **logic and sense only, never LED current** (D-02).

---

## 5. The `at` upgrade on branch A - re-derived, and it now closes thermally

The `+12V` at-ceiling is **1.25 A = 15.0 W**, a thermal limit on the carrier's
48->12 converter (ICD s6.3). With 2S2P on all four channels at die current `x`:

```
  P_load(R)   = (2 x 2.4 + 1.5x)(2x) = 9.6x  + 3x^2
  P_load(GBW) = (2 x 3.4 + 1.5x)(2x) = 13.6x + 3x^2
  P_load(all) = 9.6x + 3(13.6x) + 4(3x^2) = 50.4x + 12x^2
  Solve (50.4x + 12x^2)/0.91 <= 15.0  ->  12x^2 + 50.4x - 13.65 <= 0
  x = (-50.4 + sqrt(50.4^2 + 4 x 12 x 13.65)) / 24 = (-50.4 + 56.528)/24
  x = 0.2553 A
```

**Max die current at `at` = 255 mA** (revision A quoted 250 mA from the same
equation; 255 is the exact root). The equation is **identical to revision A's**,
which is an independent confirmation that the package change did not move the
electrical topology.

| | branch A at `at` |
|---|---|
| Max die current | **255 mA/die** (RGB dies rated 350 mA, white rated 700 mA - both fine) |
| Emitter electrical power | `50.4 x 0.2553` = **12.87 W** |
| Ballast | `12 x 0.2553^2` = **0.78 W** |
| Rail draw | 15.00 W = **1.250 A on `+12V`** (the ceiling, by construction) |
| vs the at emitter budget 16.5-18.4 W | **70-78 %** |
| **RGB package heat at `at`** | `(2.4 + 3.4 + 3.4) x 0.255 x 0.75` = **1.76 W** |
| **White package heat at `at`** | `3.4 x 0.255 x 0.75` = **0.65 W** |

**What changed at `at`, and it is a real improvement.** The withdrawn 4-in-1 put
all four dies on one slug: at the same 255 mA/die that is
`(2.4 + 3.4 + 3.4 + 3.4) x 0.255 x 0.75` = **2.41 W** on one package. The split
puts **1.76 W** on the hottest package - a **27 % reduction on the binding thermal
path**. Against the lumped budget at 40 C air the at case moves from 24.9 K/W
(marginal against a 19-23 K/W MCPCB path) to **(100 - 40)/1.76 = 34.1 K/W**, which
closes with **1.5-1.8x margin**. Under the wall-conducted enclosure (s6) it closes
with more.

**`at` is no longer thermally blocked at the emitter.** It remains gated on
OPEN-1 (the carrier's internal-air figures) and on the enclosure meeting ENC-8,
and reaching it is still a sense-resistor value plus a firmware constant - no
respin, no module rewire.

---

## 6. Thermal - re-derived for two packages and a wall-conducted enclosure

### 6.1 Heat inventory at row 1 (full white, worst-case Vf, 8.604 W in)

| Destination | Power | Note |
|---|---|---|
| **This PCB** - driver conduction, switching, diode, quiescent | **0.774 W** | 8.604 in minus 7.830 delivered |
| **This PCB** - `+3V3` logic | 0.017 W | |
| **LED module** - emitter dies | 7.560 W electrical -> **5.670 W heat** | 75 % to heat, 25 % to light - **ASSUMED** (requirements s4 says 20-35 % to light) |
| **LED module** - ballast resistors | **0.270 W**, all heat | on the MCPCB |

**This board dissipates 0.79-0.81 W across the entire output range**, because the
shunt loss at the dimming floor (0.811 W) is almost exactly the converter loss at
full output (0.791 W incl. logic). That flatness is unchanged by the package swap
and it is what makes the enclosure analysis tractable.

Per-package heat at 150 mA/die, worst-case Vf:

| Package | Dies | Electrical | **Heat (75 %)** | Was (4-in-1) |
|---|---|---|---|---|
| **RGB 3-in-1** | R + G + B | `(2.4 + 3.4 + 3.4) x 0.150 = 1.380 W` | **1.035 W** | 1.418 W |
| **White discrete** | W | `3.4 x 0.150 = 0.510 W` | **0.383 W** | (in the same package) |
| 4 RGB + 4 white | 16 | 7.560 W | **5.670 W** | 5.670 W - identical total |

### 6.2 The enclosure, under the H1-Q1 decision (sealed, LED heat through the wall)

H1-Q1 selected **sealed with the LED module's heat conducted through the enclosure
wall**. That removes the emitter heat from the box entirely:

| Enclosure scenario | In-box heat | Rise at 3.6-4.3 K/W | Internal air, 25 C room | vs ENC-1 (45 C) |
|---|---|---|---|---|
| **SELECTED: sealed, LED heat through the wall** | carrier 2.4 + this board 0.791 = **3.19 W** | **11.5 - 13.7 K** | **36.5 - 38.7 C** | **passes, 6-8 K margin** |
| Same, at the requirements' ASSUMED 40 C room | 3.19 W | 11.5 - 13.7 K | **51.5 - 53.7 C** | fails the literal 45 C - see ENC-1b |
| Same, at `at` (carrier 3.7 + this board 1.32 W) | 5.02 W | 18.1 - 21.6 K | **43.1 - 46.6 C** | marginal |
| **FAILURE MODE: the wall bridge does not work** | 3.19 + 5.67 = **8.86 W** | **31.9 - 38.1 K** | **56.9 - 63.1 C** | **fails by 12-18 K** |
| REJECTED: sealed, module inside | 8.86 W | as above | 57 - 63 C | fails |

**The failure-mode row is the entire reason H1 directed that the wall-conduction
path become a testable criterion rather than an assumption.** If the bridge is
badly built the fixture does not fail loudly - it silently reverts to the sealed
configuration that H1-Q1 rejected, and the daughter's own components then sit in
57-63 C air. ENC-8 in `stackup.md` s5 is that criterion.

### 6.3 The emitter thermal model, re-derived

Wall conduction changes the model's shape, not just its numbers. Under the
rejected sealed-inside configuration every package fought internal air
independently. Under wall conduction the packages share **one** path to room air:

```
  T_j(die) = T_room
           + P_module x Rth(module base -> room air)     <- SHARED, all 8 packages
           + P_pkg    x Rth(slug -> module base)         <- per package
           + P_die    x Rth(die -> slug)                 <- per die
```

| Term | Value | Status |
|---|---|---|
| `P_module` | 5.670 W | derived, s6.1 |
| `Rth(module base -> room air)` | **<= 8.0 K/W** | **the ENC-8 acceptance criterion** - specified and measured, not assumed |
| `Rth(slug -> module base)` | ~**2.5 K/W** (1.5 MCPCB dielectric + spreading, 1.0 mount interface) | `ASSUMED:` from `research/led-emitter.md` s6 |
| `Rth(die -> slug)` | ~**12 K/W** | `ASSUMED:` extrapolated from ams-OSRAM OSLON's published RthJS 8.9 typ / 12.0 max. **NEITHER XINGLIGHT DATASHEET PUBLISHES A THERMAL RESISTANCE** |
| Red die heat | `2.4 x 0.150 x 0.75` = **0.270 W** | derived |
| White die heat | `3.4 x 0.150 x 0.75` = **0.383 W** | derived |

**Red junction (the binding die), 25 C room, ENC-8 met:**

```
  T_j = 25 + 5.670(8.0) + 1.035(2.5) + 0.270(12)
      = 25 + 45.36 + 2.59 + 3.24  =  76.2 C
```

**White junction, same conditions:**

```
  T_j = 25 + 45.36 + 0.383(2.5) + 0.383(12) = 25 + 45.36 + 0.96 + 4.60 = 75.9 C
```

| Die | Tj at 25 C room | Tj at 40 C room | Design target | **PUBLISHED Tj max** | Margin to published max, 40 C room |
|---|---|---|---|---|---|
| **Red (in the RGB package)** | **76.2 C** | **91.2 C** | 100 C (colour + lifetime) | **125 C** | **34 K** |
| Green / Blue | 76.2 C | 91.2 C | - | **125 C** | 34 K |
| **White (discrete)** | **75.9 C** | **90.9 C** | - | **120 C** | **29 K** |

**Sensitivity to the unpublished Rth(die->slug).** If the real figure is 20 K/W
rather than the assumed 12:

```
  Red:   25 + 45.36 + 2.59 + 0.270(20) = 78.4 C   (+2.2 K)
  White: 25 + 45.36 + 0.96 + 0.383(20) = 79.0 C   (+3.1 K)
```

**OPEN-4's largest single uncertainty is now bounded at ~3 K.** That is a genuine
structural improvement, and its cause is worth stating precisely: the die->slug
term applies only to **one die's own heat**, and the dominant 45 K term is now an
**ENC-8 criterion with a test method**. It is *not* caused by the package split -
see the honesty note below.

**HONESTY NOTE - what the package split did and did not buy thermally.** Running
the pre-H1 4-in-1 through the same model at the same conditions gives
`25 + 45.36 + 1.418(2.5) + 0.270(12) = 77.2 C` against the new set's 76.2 C.
**The package split is worth about 1 K under wall conduction**, because the module
total heat is unchanged and the shared wall path dominates. Under the *conservative
lumped* model that revision A used (whole package heat x whole 19-23 K/W path) it
looks worth 8-9 K, but that model double-counts the package term. **So the H1
record should not claim the split as a thermal win.** What it actually bought is
epistemic and is exactly what the owner said: a **published 125 C Tj max where the
4-in-1 published none**, so for the first time there is an absolute limit to check
against - plus 3.5x the stock depth and an SMT-assemblable JLC class.

### 6.4 REQUIRED FOR H2 - how the margins move if internal air is 85-90 C

ICD s7.6's internal-air figures are disputed (OPEN-1 / CR-6): the ICD's own af
point scaled to `at` gives ~85 C, and an independent Hoffman/Rittal calculation
gives 89-115 C, against the ICD's stated 69 C. Until the carrier re-issues s7.6,
**69 C is provisional**. This section states what happens at 85 C and at 90 C.

**Finding 1 - the emitter junctions barely move, and that is a structural
consequence of H1-Q1.** Under wall conduction the emitters are cooled to **room
air**, not to internal air. Internal air reaches them only through a weak
parallel path (the package top surface and the module's exposed faces). At the
selected configuration the module base sits at 25 + 45 = 70 C while internal air
is 38 C, so the box is currently a small *help*. If internal air were 85-90 C the
module would instead gain a little heat from the box.

`ASSUMED:` the module's parasitic coupling to internal air is >= 25 K/W (a
~50 x 50 mm module face into still air, from [TI-2020]'s 500 K*cm^2/W with one
face free is 20 K/W; 25 K/W is the conservative direction here because a *weaker*
coupling means the box heats the module less). Reversing the sign of a 32 K
difference through 25 K/W adds at most `(90 - 70)/25 = 0.8 W` into the module,
raising the whole stack by `0.8 x 8.0 = 6.4 K`.

| Internal air | Red Tj (25 C room) | Red Tj (40 C room) | vs 100 C target | vs **published 125 C** |
|---|---|---|---|---|
| 38 C (this design's own calculation) | **76.2 C** | 91.2 C | PASS | PASS, 34 K |
| 56 C (ICD s7.6 af) | ~76 C | ~91 C | PASS | PASS |
| **85 C (the disputed re-derivation)** | **~79 C** | **~94 C** | **PASS, 6 K** | **PASS, 31 K** |
| **90 C** | **~83 C** | **~98 C** | **PASS, 2 K - no margin left** | PASS, 27 K |

**Finding 2 - what actually breaks at 85-90 C is the AMBIENT rating, not the
junction.** Both new parts are live-verified at **Topr -40 to +85 C**. At 85 C
internal air they are at their absolute ambient rating with **zero margin**; at
90 C they are **out of specification** and no thermal design on the module fixes
it, because the rating is on the air around the package, not on the junction.
This is unchanged from the 4-in-1 and is why **CR-6 stays a blocking issue.**

**Finding 3 - but the disputed figure does not apply to the selected
configuration.** ICD s7.6's 69 C is stated for a sealed box **with the load
inside**. H1-Q1 removed 5.67 W from that box. This design's own calculation for
the selected configuration is **36.5-38.7 C at af** and **43-47 C at `at`** in a
25 C room (s6.2), using the *pessimistic* end of the Hoffman/Rittal bracket. Even
scaling that by the 1.15-1.37x optimism factor the ICD's own af point implies
still lands at 42-53 C. **For 85-90 C to be real at the daughter under the
selected configuration, the wall bridge would have to have failed - which is the
ENC-8 failure-mode row in s6.2.**

**Consolidated verdict for H2:** the emitter thermal case now closes with 24 K
(25 C room) / 9 K (40 C room) of margin against the 100 C red target and 34 K
against the **published** 125 C maximum, and it is insensitive to the disputed
ICD figure by construction. **The case rests on exactly two things: ENC-8's
8.0 K/W wall path being measured rather than assumed, and the emitters' +85 C
ambient rating not being breached** - which under the selected configuration it
is not, and under the ENC-8 failure mode it is.

### 6.5 Cross-check against the lumped budget, for continuity with revision A

Revision A tabulated an allowed junction-to-air resistance per package. That model
is conservative (it applies the package term to the whole package heat) but it is
what previous reviews saw, so it is carried:

| Internal air | RGB package budget (P = 1.035 W, red 100 C) | White package budget (P = 0.383 W, 100 C) | MCPCB path 19-23 K/W |
|---|---|---|---|
| 38 C (selected config) | **59.9 K/W** | 161.9 K/W | **closes 2.6-3.2x / 7.0-8.5x** |
| 45 C (ENC-1) | 53.1 K/W | 143.6 K/W | closes 2.3-2.8x / 6.2-7.6x |
| 56 C (ICD af) | 42.5 K/W | 114.9 K/W | closes 1.8-2.2x / 5.0-6.0x |
| 85 C (disputed) | 14.5 K/W | 91.4 K/W | **RGB fails** / white closes 4.0-4.8x |

Revision A's equivalent RGB-path figure at 38 C was 43.7 K/W (1.9-2.3x). **The
white path is a non-issue at every internal-air figure including 90 C; the RGB
package is the only binding emitter thermal path on this design.** That is the
practical meaning of "two thermal paths now": one of them can be stopped worrying
about.

---

## 7. Branch B (`+48V_SW`) - retained for the record only

**H1 confirmed branch A. This section is not a live option and is kept only so the
comparison that produced the decision remains auditable.** With 2S2P forced on
`+12V` and the same 8-package set, branch B would run 4S strings (9.6 V red /
13.6 V G/B/W worst-case) at 175 mA/die with no ballast, for ~15 % more light, at
the cost of the 0.635 mm clearance regime across the whole front end and VIN bus,
an SOA-critical hot-swap FET, a mandatory bleed path, 100 V capacitors, a 100 V
catch Schottky (0.30 W/channel idle instead of 0.20 W), a 265 uH inductor instead
of 47 uH for the same ripple fraction, and leaving D-02's 12 V rail with no
consumer anywhere in the system. The converter edge budget `t_r + t_f = 1/(f*k)`
is **identical on both rails** - the rail voltage cancels out of the algebra
(`decisions.md` D1) - so 48 V buys no dimming speed.

---

## 8. What this board does NOT do

- **No energy store.** No cap bank, no burst output - that is the strobe's
  problem. Total `+12V` capacitance is ~40 uF nameplate (~25 uF effective after
  ceramic DC-bias derating): decoupling, not storage.
- **No 48 V load on branch A**, therefore no bleed obligation (CAR-REQ-17 is
  conditioned on tapping), no 100 V capacitors, no hot-swap SOA analysis, and the
  0.635 mm regime is satisfied by the J3 land pattern's own 0.84 mm gap (1.32x).
- **No `+3V3` power path to anything but logic and sense** (D-02).
- **No path that energises anything from `+12V` or `+3V3` while `+48V_SW` is
  off** - carried by the ENABLE AND gate. See `blocks.md` B1 for the residual
  asymmetry ICD rev A2 s8.4 exposes here.
- **No emitters on this board.** D3 stands: the module is off-board on an
  aluminium MCPCB, and H1-Q1's wall-conduction decision makes that **mandatory
  rather than merely preferred** - an on-board emitter cannot reach the wall
  bridge at all. See `decisions.md` D3 (amended).
- **No optics.** The diffuser that H1-Q2 makes mandatory is an enclosure
  deliverable with a specification in `stackup.md` s5.2, a design target and a
  bench test. **This pipeline cannot verify a beam and does not claim to.**
