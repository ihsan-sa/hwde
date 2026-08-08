# Optical budget re-derivation - LUM-PAR-A

**Analysis only. No design file, generator, `parts.json` or `constraints.json` was
touched.** Date 2026-08-07, pre-P5. Every number below is re-derived from the
datasheet PDFs in `parts/` or from first principles; where a figure is inherited
it is named as inherited.

---

## 0. Bottom line

| | recorded (H2 package) | **re-derived** |
|---|---|---|
| Beam-angle mismatch (mech. 3) | RGB 140 / white 120 deg, -11.5 % at 45 deg | **does not exist. Both parts print 2Theta1/2 = 140 deg TYP** |
| Baseline flux, per fixture | 485 lm (~41 lx) | **447 lm (~37.7 lx)** - the recorded baseline is the *superseded* 4-in-1 emitter set |
| Sense-resistor multiplier | x0.917 | **x0.917 - confirmed unchanged** |
| Diffuser multiplier | x0.55 - x0.70 | **x0.60 - x0.75** as the module is drawn today |
| Compounded | 0.504 - 0.642 | **0.550 - 0.688** |
| Delivered, 8 fixtures all channels full, direct | **20.7 - 26.3 lx** | **20.7 - 25.9 lx** |

**The budget does not move.** Three corrections of similar size and opposite sign
cancel: the diffuser was over-charged (+9 %), the thermal derating was too harsh
(+6 %), and the flux baseline was stale by an emitter-set change nobody re-costed
(-13 %). The 140-deg correction is real and worth having, but the light it
recovers was already spent elsewhere in the record.

**What does move the number is not the beam angle.** The re-derivation found a
*different* first-order defect in the same specification - the emitter
arrangement matches the two families' centroids but not their radii, which leaves
a 17 % colour error at a shadow edge that no diffuser removes - and fixing that
(a free MCPCB placement change plus stand-off) is what licences a lighter
diffuser and takes the fixture to **24 - 29 lx**. Reverting the sense resistor
adds ~12 % on top (**27 - 33 lx**).

**None of that reaches the ~41 lx the fixture was already called a dark-room
instrument at.** Only the `at` upgrade does: 233 mA/die on a 0.47 ohm sense
resistor gives **41 - 50 lx** and, per `power_tree.md` s5, now closes thermally.

---

## 1. Optical ground truth, read from the datasheets

Both PDFs were opened and the optical-electrical tables and radiation plots read
directly. This confirms the P3 `open8_REFUTED` finding independently.

### 1.1 Viewing angle - CONFIRMED 140 / 140

| | C22434861 (RGB 3-in-1) | C48586656 (white) |
|---|---|---|
| Symbol | `2Theta1/2` | `2Theta1/2` |
| Page | p4 optical-electrical table | p4 optical-electrical table |
| Test condition | IF = 350 mA | IF = 700 mA |
| Min / **Typ** / Max | -- / **140** / -- deg | - / **140** / - deg |
| p1 headline | "Luminous Angle: 140 degrees" | "Luminous Angle: 140 degrees" |

Same symbol, same definition (full angle between the two 50 %-intensity
directions), same value, no tolerance published on either. **There is no
specified mismatch.** The 120 deg figure is an LCSC parametric attribute that
contradicts the datasheet LCSC itself hosts.

### 1.2 The radiation plots corroborate, and cannot be used to reinstate a mismatch

- **RGB, p7 "Beam Patter"**: a single polar plot, 0/30/60 deg gridlines, relative
  intensity 0-100. No test current is printed on it. Digitises to a ~60-62 deg
  half angle (120-125 deg full).
- **White, p6 "Intensity distribution curve (1000 mA test)"**: Cartesian
  relative-intensity-vs-angular-displacement pair plus a polar plot. 50 %
  crossings at roughly 24 deg and 152 deg on the 0-180 axis, i.e. **62-66 deg
  half angle (124-132 deg full)**.

Both plots read *narrower* than their own tabulated 140 deg, by about the same
margin. Two things follow, and they matter:

1. **The plots cannot settle a mismatch in either direction.** Fitting
   `I = I0 cos^m(theta)` to the digitised extremes: RGB half 60.0 / white half
   66.0 gives white **+30 % brighter** than RGB at the 3 m wall; RGB half 62.5 /
   white half 62.0 gives **-2.2 %**. The digitising error is larger than the
   effect. Only the tabulated number is spec-grade, and it is identical.
2. **The plots are not comparable anyway** - the white plot is explicitly at
   1000 mA (a pulse-only condition: IFP 1000 mA, pulse width <= 0.1 ms, duty
   <= 1/10) and the RGB plot states no current at all.

### 1.3 What the corrected mechanism-3 cost actually is

`stackup.md` s5.2.1 fitted `m = 0.646` (140 deg) against `m = 1.000` (120 deg)
and produced the -11.5 % / -33.5 % table. With both families at 140 deg the
exponent difference is exactly zero:

| Off-axis | recorded (140/120) | **corrected (140/140)** |
|---|---|---|
| 30 deg | -5.0 % | **0.0 %** |
| 45 deg (2.5 m out on the floor) | -11.5 % | **0.0 %** |
| 71.6 deg (3 m wall at 1.5 m) | -33.5 % | **0.0 %** |

**Second finding, worth recording because it changes how the original was
weighted.** Converting those channel-ratio errors into the units the acceptance
test actually uses (`stackup.md` s5.2.5 Test B: <= 0.010 in u'v'), with the mix
at the hot design point:

| W/colour ratio error | delta u'v' | MacAdam steps |
|---|---|---|
| 2 % | 0.0007 | 0.3 |
| 11.5 % (the 45 deg case) | **0.0043** | 1.7 |
| 17.3 % | 0.0066 | 2.7 |
| 33.5 % (the 3 m wall case) | **0.0138** | 5.5 |

So even if the 140/120 split had been real, it would have **passed Test B over
most of the wash** and failed only at the extreme edge. The diffuser was charged
30-45 % of the fixture's flux against a defect that does not exist *and* that,
had it existed, was marginal. (Method: monochromatic 625/525/460 nm primaries at
the design-point flux ratio against a 6250 K white at u'v' derived from
x=0.315/y=0.330; 1 MacAdam step ~ 0.0025 u'v'. Approximate - the LED lines have
20-30 nm half-widths - but the ratio between rows is robust.)

### 1.4 Flux at the design point, derated to the actual drive

150 mA/die is **43 % of the RGB part's rating and 21 % of the white part's**, so
the headline bins cannot be used directly.

Datasheet flux, Ta = 25 C:

| Part | Condition | min / typ / max |
|---|---|---|
| C22434861 red | 350 mA | 45 / **55** / 60 lm |
| C22434861 green | 350 mA | 80 / **90** / 100 lm |
| C22434861 blue | 350 mA | 13 / **20** / 27 lm |
| C48586656 white | 700 mA | 220 / **--** / 300 lm (no typ column; bins L3-L5 span 225-300) - **260 lm used** |

**Current derating.** The white part's own p6 "Forward current - luminous
intensity" curve is normalised to IF = 350 mA and is **linear through the origin
to 400 mA**, so flux is proportional to current in this range with no measurable
droop. The RGB part's p6 flux-vs-current curve **cannot be used**: its y-axis is
labelled 0/20/40/60/80/100/150/200/250 at uniform spacing, i.e. it is drawn on a
non-uniform scale. It does show clear saturation above the rating.

**Strict proportionality is therefore used.** It is conservative: any low-current
efficacy bonus makes the real figure higher. Note that `power_tree.md` s1.2
step 2 claims 2S2P buys "~7 % more light (less droop at half the current)" - that
claim is **not supported by either datasheet** and is not taken here.

| Drive | RGB pkg, cold | White pkg, cold | Fixture (4+4), cold |
|---|---|---|---|
| 137.5 mA/die (as-built, 0.75R) | 64.8 lm | 51.1 lm | **464 lm** |
| **150.0 mA/die (design point)** | **70.7 lm** | **55.7 lm** | **506 lm** |
| 233 mA/die (`at`, 0.47R) | 109.8 lm | 86.5 lm | 785 lm |

**Thermal derating.** `power_tree.md` s6.3 supersedes P1's Tj ~ 100 C placeholder
with a real model: **red/green/blue Tj = 76.2 C at a 25 C room, 91.2 C at 40 C**,
white 75.9 / 90.9 C, conditional on ENC-8 (module base -> room <= 8.0 K/W). Using
`research/led-emitter.md` s7's per-chemistry rates (red -0.53 to -0.73 %/K,
InGaN -0.067 to -0.147 %/K, white -0.107 to -0.20 %/K):

| Basis | 150 mA/die | as-built 137.5 mA/die |
|---|---|---|
| Record's Tj ~ 100 C (dT 75 K) | 420 lm | 385 lm |
| **`power_tree` s6.3, 25 C room (dT 51 K)** | **447 lm** | **410 lm** |
| `power_tree` s6.3, 40 C room (dT 66 K) | 430 lm | 394 lm |

The vendor derating curves are **not** used: `research/led-emitter.md` s11 records
them as MD5-identical boilerplate across four different-colour datasheets.

---

## 2. What PAR-REQ-15 actually requires now

**Exact wording** (`brief/03` s4, unamended - `requirements.md` s0 amends only
PAR-REQ-16 and -17):

> **PAR-REQ-15** - Diffusion sufficient that the four emitter colours mix before
> reaching a surface. Visible R/G/B/W shadow fringing on a wall is a failure.

The requirement names **shadow fringing** as the failure. That is a
source-separation problem and it is untouched by the beam-angle correction.

### 2.1 Geometry assumed (all inherited from `stackup.md` s5.2 and stated so it is checkable)

| Item | Value | Source |
|---|---|---|
| Emitter arrangement | 3 x 3 grid, **16.0 mm pitch**, RGB on the four corners, white on the four edge midpoints, centre vacant | s5.2.2 |
| Pitch floor | 16.0 mm - set by the 14.5 mm lead span, not chosen | s5.2.2, confirmed against both land-pattern extracts |
| Radius from centroid | RGB **22.6 mm**, white **16.0 mm** | derived |
| Stand-off, emitter dome to diffuser | **>= 15 mm, 20 mm nominal** | s5.2.3 |
| Diffuser aperture | >= 115 mm at d = 20 mm | s5.2.3 |
| Throw | 2.5 m ceiling; walls 2-4 m; stated minimum 1.5 m | s5.2.4 |
| Acceptable non-uniformity | **<= 0.010 u'v' (~4 MacAdam)** penumbra vs field, and no fringe distinguishable at 2 m by three observers | s5.2.5 Test A/B |
| Occluder geometry | 50 mm disc at 0.5-1.0 m; worst case a = 1.0 m, b = 1.5 m, observer L = 2.0 m | s5.2.4/5 |

### 2.2 Mechanism by mechanism, after the correction

| # | Mechanism | Status now |
|---|---|---|
| 1 | Direct-wash colour gradient | **Killed by the arrangement.** Centroids coincide exactly; the required throw falls to 0.07 m. Unaffected by the correction |
| 2 | **Shadow fringing** | **FULLY SURVIVES.** This is the requirement's own named failure and it is a source-separation problem |
| 3 | Beam-angle mismatch | **DEAD** (s1.3). Test B now passes by construction: identical far-field shapes convolved with any common kernel stay identical |

### 2.3 The diffuser is still mandatory, but not for the reason it was priced

A shadow edge images the source, so what governs the fringe is the **colour
uniformity of the lit aperture as seen from a penumbra point**. Model: a
straight-edge occluder projects a half-plane cut across the lit panel; sweep the
cut in position and azimuth and take the worst white-to-colour ratio error while
at least 25 % of the flux is still visible. Emitter footprint on the panel is
`cos^1.646(theta)/(d^2+r^2)` for a 140 deg source.

| Configuration | worst ratio error | delta u'v' |
|---|---|---|
| No diffuser (clear window - the source stays 8 points) | **100 %** | off scale |
| Diffuser, d = 15 mm | 23.5 % | 0.0093 |
| **Diffuser, d = 20 mm (as specified)** | **17.3 %** | **0.0066** |
| Diffuser, d = 25 mm | 12.5 % | 0.0047 |
| Diffuser, d = 30 mm | 9.5 % | 0.0035 |
| d = 20 mm, plus 3 mm of diffuser lateral blur | 16.8 % | 0.0064 |
| d = 20 mm, plus 6 mm of diffuser lateral blur | 15.1 % | 0.0058 |

**Three results, and the second and third are new.**

1. **The diffuser is required and cannot be deleted.** Without a panel that
   converts incident irradiance into direction-independent exit radiance, the
   source stays eight discrete points and the fringe is total. This is the
   property that must be bought, and it is *hiding power* (the emitters must not
   be individually visible through the panel), not low transmittance.
2. **The mixing is done by the STAND-OFF, not by the diffuser's scattering.**
   A bulk opal 2-3 mm thick spreads light laterally by about its own thickness -
   3 mm of blur moves the fringe from 17.3 % to 16.8 %, i.e. nothing, against a
   16 mm pitch. Every useful millimetre of mixing comes from `d`. Stand-off is
   free in flux; diffuser transmittance is not. **`stackup.md` s5.2.3's claim
   that Option A "kills mechanism 2" by re-Lambertianising is wrong about the
   physics** - it kills mechanism 2 by making the panel an area source at all,
   which any high-hiding-power diffuser does.
3. **The arrangement spec has a hole the tolerance budget cannot see.**
   s5.2.2 matches the two families' **first** moment (centroids coincide, 0.8 mm
   budget) but not their **second**: RGB sits at radius 22.6 mm and white at
   16.0 mm. A cut that removes the outer part of the array removes
   proportionally more colour than white. That is the whole of the residual
   17.3 %, and it is invisible to Test C (a centroid check with a ruler passes).

### 2.4 The arrangement fix, and it is free

Put all eight packages on **one ring, alternating RGB / white**. Both families
then share centroid *and* radius; only a 45 deg azimuthal phase remains.

| d | current 3x3 checkerboard | **alternating ring, r = 21 mm** |
|---|---|---|
| 15 mm | 23.5 % | **11.2 %** |
| **20 mm** | **17.3 %** | **5.8 %** (delta u'v' 0.0022, < 1 MacAdam) |
| 25 mm | 12.5 % | 3.2 % |
| 30 mm | 9.5 % | 1.8 % |

r = 21 mm is the minimum the 16 mm pitch floor allows on eight positions
(`2 r sin(22.5 deg) = 16.07 mm`). Aperture at d = 20 mm is **111 mm**, slightly
*less* than the checkerboard's 115 mm. The MCPCB grows from ~55 x 55 mm to
~62 x 62 mm. **Zero flux cost, zero board cost, ~3x less residual fringe.**

This is a module-BOM / `stackup.md` s5.2.2 change and it revises `decisions.md`
D14. It is not a change to this PCB and I have not made it.

---

## 3. Re-costing the diffuser

**No diffuser part is pinned anywhere in the workspace and no diffuser datasheet
exists in `parts/`.** Everything in this section is an engineering band, not a
verified transmittance, and it is the weakest link in the whole budget.

What the part must now do, versus what it was priced to do:

| Property | Priced for (Option A) | **Required now** |
|---|---|---|
| Hiding power (no visible emitter image at d = 20 mm over a 16 mm pitch) | required | **required - unchanged** |
| Re-Lambertianise the far field to erase a 140-vs-120 deg mismatch | required, and this is what forced the dense end of the range | **not required - the mismatch does not exist** |
| Pass Test B (wash chromaticity vs angle) | at risk; Option B gated behind it | **passes by construction** |
| Total transmittance | **0.55 - 0.70**, 0.60 nominal | see below |

The correction removes the reason to shop at the dense end of the volume-diffuser
range and removes the reason Option B was conditional. It does **not** licence a
thin surface-scattering film: those have 10-30 deg scattering, which at d = 20 mm
is a 4-11 mm blur against a 16 mm pitch, so the source structure survives and
result 1 of s2.3 bites.

| Case | transmittance | note |
|---|---|---|
| Recorded charge | x0.55 - x0.70 | dense opal, bought for certainty against mechanism 3 |
| **Module as drawn today (checkerboard, d = 20 mm)** | **x0.60 - x0.75, nominal x0.68** | still needs strong hiding power because the residual fringe is 17 % before the diffuser contributes anything |
| **Ring arrangement and/or d >= 30 mm** | **x0.70 - x0.85, nominal x0.78** | the geometry has already done the work; the panel only has to hide the sources |

**Net change against the phantom mismatch: +9 % (as drawn) to +21 % (fixed
geometry).** It is not the 30-45 % that "the diffuser costs 30-45 % of the flux"
might suggest is on the table, because most of that cost was always buying
source-mixing, which is real.

Cost of the d >= 30 mm option, stated because it is not free in mechanics:
aperture grows from 115 mm to **149 mm** (146 mm for the ring), and ENC-10's
module stack height grows from ~29-30 mm to **~40 mm**. The ring arrangement at
d = 20 mm gets 5.8 % without either penalty and is the better buy.

---

## 4. The compounded budget, recomputed

Basis, identical to the record so the numbers are comparable: **8 fixtures, all
four channels at 100 %, direct average illuminance over 95 m2** (35 m2 floor +
24 m perimeter x 2.5 m = 60 m2 wall), no inter-reflection.

### 4.1 The baseline itself was stale

The recorded ~41 lx is `research/led-emitter.md` s5's figure for **4 x integrated
RGBW 4-in-1 at 175 mA/die** - the emitter set **H1-Q2 superseded**. Nobody
re-derived the flux after the package change; `power_tree.md` s3.1 explicitly
records that the *electrical* design point survived unchanged, and the light
figure was carried across with it.

| Baseline | lm/fixture (hot) | lx |
|---|---|---|
| P1, 4 x 4-in-1 @ 175 mA/die, Tj ~ 100 C - **the number the record compounds against** | 485 | **40.8** |
| H1-Q2 set @ 150 mA/die, Tj ~ 100 C (like for like) | 420 | 35.4 |
| **H1-Q2 set @ 150 mA/die, `power_tree` s6.3 Tj 76 C, 25 C room - the correct baseline** | **447** | **37.7** |
| same, 40 C room (Tj 91 C) | 430 | 36.2 |

The package change cost **13 %** of the baseline at equal thermal assumptions;
the improved thermal model gives **6.5 %** back.

### 4.2 The compounded number

| | recorded | **re-derived, module as drawn** | **re-derived, ring or d >= 30 mm** |
|---|---|---|---|
| Baseline | 41 lx (stale) | **37.7 lx** | 37.7 lx |
| Sense resistor 0.75R | x0.917 | **x0.917** | x0.917 |
| Diffuser | x0.55 - 0.70 | **x0.60 - 0.75** | **x0.70 - 0.85** |
| **Compounded** | **0.504 - 0.642** | **0.550 - 0.688** | **0.642 - 0.779** |
| **Delivered** | **20.7 - 26.3 lx** | **20.7 - 25.9 lx** | **24.2 - 29.4 lx** |

At a 40 C room instead of 25 C, subtract ~4 %: 19.9 - 24.9 lx and 23.2 - 28.2 lx.

**Read the middle column plainly: the correction recovers nothing.** It is
arithmetically identical to what is on record, because the diffuser over-charge
was cancelled by a baseline that was too generous. The right-hand column is real
and is worth ~+17 %, but it is bought by fixing the emitter arrangement, not by
the beam-angle finding.

Reference points, unchanged: lit living room 100-200 lx; bar/restaurant mood
~40 lx; `research/led-emitter.md` s5 already called this "a dark-room instrument,
not room lighting" at 41 lx.

---

## 5. Remaining levers and their real cost

| Lever | Gain | Delivered (ring, d=20) | Real cost |
|---|---|---|---|
| **Fix the emitter arrangement** (3x3 checkerboard -> alternating ring r = 21 mm) | licences the x0.70-0.85 diffuser | 20.7-25.9 -> **24.2-29.4 lx** | MCPCB 55 -> 62 mm. Revises `stackup.md` s5.2.2 and `decisions.md` D14. No board change, no power change |
| **Revert 0.75R -> 0.68R** sense | **x1.120** (275 -> 308 mA/ch typ) | **27.1 - 32.9 lx** | see below - the compliance excursion |
| **`at` upgrade, 0.47R** (233 mA/die) | **x1.553** | **41.0 - 49.7 lx** | PoE+ switch + carrier class resistor + 4 sense resistors. No respin |
| Raise die current at `af` beyond 0.68R | - | - | **No headroom.** 0.68R already exceeds the ceiling |
| More emitter packages at lower current | ~0 | - | Flux is set by electrical power, and power is capped. The white part's own F-I curve is linear below 400 mA, so running softer buys no efficacy |

### 5.1 The sense resistor - the arithmetic, from the TPS92515HV datasheet

`ILED = (V_IADJ/10)/R_SENSE - dIL_pp/2`, IADJ tied to VCC so the threshold band is
224 / 240 / 251 mV, `dIL_pp = 90 mA`:

| R | ILED typ | ILED max | +12V draw at max | vs 0.75 A sustained ceiling |
|---|---|---|---|---|
| **0.75 (as built)** | 275 mA | 290 mA | 0.692 A | **92 % - compliant by construction** |
| **0.68 (the revert)** | **308 mA** | 324 mA | **0.775 A** | **103 % - over the sustained ceiling** |
| 0.47 (`at`) | 466 mA | 489 mA | 1.194 A | 96 % of the 1.25 A `at` ceiling |

**The trade, honestly.** The excursion is against the ICD s6.2 **sustained** rail
ceiling under the compound worst case (worst-case Vf *and* worst-case sense
threshold *and* every PWM stuck at 100 % with no firmware alive). It is **not**
against a hardware trip: the +12V OCP is 2.0 A (2.6x away) and the PD's minimum
current limit is 0.85 A against a reflected 0.265 A at the input (3.2x away). `requirements.md` s3.3 makes
the hardware-backstop obligation non-optional, and 0.75R is what makes the board
*electrically incapable* of exceeding budget. 0.68R gives that up for **+12 %
light**. It is a BOM value with zero layout impact and stays changeable to P9.
The record already logs it as live; nothing found here changes the balance.

### 5.2 Die current - and why the thermal headroom is an assumption

- **In BOTH parts the rated current IS the absolute maximum**: 350 mA/die RGB,
  700 mA white, and the published photometry is measured at that maximum. There
  is no headroom above it by construction; 150 mA/die is where the margin comes
  from.
- **The RGB part's real ceiling is 294 mA/die, not 350.** Its own PD abs max is
  1000 mW/die, and the green/blue dies at their 3.4 V max hit 1000 mW at
  **294 mA**. At 350 mA they draw 1.19 W - the datasheet contradicts itself. The
  `at` point of 233 mA/die (0.79 W) is inside it; 255 mA/die (0.87 W) still is.
- **Neither datasheet publishes any thermal resistance** - no Rth j-s, j-c or
  j-a. Tj max (125 C RGB / 120 C white) is published but is not computable from
  board temperature. `power_tree.md` s6.3's Tj 76 C rests on an **assumed**
  12 K/W die-to-slug extrapolated from ams-OSRAM OSLON, and on **ENC-8
  (module base -> room <= 8.0 K/W), which is an acceptance criterion, not a
  measurement**. s6.3 bounds the Rth sensitivity at ~3 K, which is genuinely
  reassuring; the ENC-8 term is 45 K of the 51 K rise and is not bounded at all.
  If the wall bridge is badly built, `power_tree.md` s6.2's failure row puts
  internal air at 57-63 C and this whole flux table moves down.
- Both parts are Topr -40 to +85 C. Reliability data on both is quoted at
  Tj = 140 C, above their own abs-max Tj - treat vendor lifetime claims with
  suspicion.

### 5.3 What it would take to make the fixture not dim

To deliver ~41 lx *after* the diffuser needs ~475 lm/fixture delivered, i.e.
~610 lm emitted at x0.78. That is **1.36x** the 447 lm the af design point
produces, and flux tracks current, so it needs ~205 mA/die - **0.90 A on +12V
against a 0.75 A af ceiling**. There is no af answer.

**The `at` path is the only one that closes**, and `power_tree.md` s5 says it now
closes thermally at the emitter (RGB package heat 1.76 W at 255 mA/die, 34.1 K/W
allowed against a 19-23 K/W MCPCB path, 1.5-1.8x margin). Taking the compliant
E24 value:

- **0.47 ohm sense -> 466 mA/channel typ = 233 mA/die**, worst case 489 mA/ch =
  1.194 A on +12V against the 1.25 A `at` ceiling. Compliant by construction, the
  same way 0.75R is at af.
- Fixture flux **695 lm hot** (25 C room) -> **58.5 lx before the diffuser** ->
  **41.0 - 49.7 lx delivered** with the fixed geometry.
- Cost: a PoE+ switch (system-level, and D-01's upgrade already implies it), one
  class resistor on the carrier, four 0.47 ohm resistors here. **No respin, no
  module rewire, no layout change.** It is gated on OPEN-1 and ENC-8, not on this
  board.

---

## 6. Documents that are now wrong on disk

Not edited - flagged for whoever owns the H2 package.

| File | What is stale |
|---|---|
| `architecture/power_tree.md` s1.1 | the "TRAP" block asserting white = 120 deg, "live-verified", cross-checked against three siblings. All four figures are catalogue records; the datasheets say 140 |
| `architecture/stackup.md` s5.2.1 | mechanism 3 and its -5.0 / -11.5 / -21.8 / -33.5 % table |
| `architecture/stackup.md` s5.2.3 | Option A/B split and the "30-45 % of delivered flux" cost; Option B's gating rationale |
| `architecture/decisions.md` OPEN-8, OPEN-9, D14 | OPEN-8's premise; OPEN-9's ~25 / ~36 lx figures |
| `architecture/blocks.md` D14 line and s(H1-Q2) table | "a 140-vs-120 deg beam mismatch" as a real first-order defect |
| `research/led-emitter.md` s5 | the ~41 lx / 485 lm baseline is for the superseded 4-in-1 set |
| `architecture/power_tree.md` s1.2 step 2 | "2S2P gives ~7 % more light (less droop)" - unsupported by either datasheet |

---

## 7. What is verified, assumed, and unverifiable

| Claim | Status |
|---|---|
| 2Theta1/2 = 140 deg TYP on both parts, same symbol and condition class | **VERIFIED** - both p4 tables and both p1 headlines read directly |
| Radiation plots read 120-132 deg full and cannot settle a mismatch | **VERIFIED** by digitising, with the stated uncertainty |
| Flux tables, bins, Vf, abs max, the RGB PD contradiction | **VERIFIED** from the PDFs |
| White flux linear in current below 400 mA | **VERIFIED** from its p6 curve |
| RGB flux-vs-current | **UNUSABLE** - non-uniform y axis. Proportionality assumed (conservative) |
| White flux typ | **NOT PUBLISHED** - 260 lm used, mid of the 220-300 range and of bins L3-L5 |
| Per-chemistry %/K derating | **ASSUMED** (`research/led-emitter.md` s7). Vendor curves are boilerplate |
| Tj 76.2 / 91.2 C | **ASSUMED**, and conditional on ENC-8 which is a criterion, not a measurement. No Rth is published on either part |
| Shadow half-plane model and the 17.3 % / 5.8 % figures | **MY DERIVATION**, first-order, ideal Lambertian panel and straight-edge occluder. Not bench-verified. The limiting cases check out (point sources -> 100 %, large d -> 0) |
| u'v' / MacAdam conversion | **APPROXIMATE** - monochromatic primaries, assumed white chromaticity |
| Diffuser transmittance bands (x0.55-0.85) | **NOT DATASHEET-VERIFIED. No diffuser part is pinned anywhere in this workspace.** This is the weakest number in the budget and it is a procurement outcome |
| Illuminance basis (8 fixtures / 95 m2 / direct only) | Inherited from `research/led-emitter.md` s5 so the numbers stay comparable |
