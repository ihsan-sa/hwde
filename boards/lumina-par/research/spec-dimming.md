# spec-dimming - PWM dimming, flicker standards and the driver timing budget

Board: LUM-DTR-PAR-A (LUM-PAR-A). Phase P1, interface research.
Scope: normative + derived requirements that constrain THIS board's electrical design
and layout. No part selection, no circuit design.
All output ASCII. Every number below is either cited or derived from cited numbers with
the arithmetic shown.

---

## 0. Headline for the architect

1. **PAR-REQ-01 does NOT hold at 13-bit/9.766 kHz** under the reading a lighting person
   means ("5 % of perceived brightness"). At 5 % perceived with gamma 2.2 the duty is
   0.137 %, which is PWM code 11 of 8192. One code is a **8.9 % luminance step = 8.9 JND**.
   Required: <= 1 JND. **It fails by 8.9x.**
2. **No LEDC configuration fixes it.** 14-bit only halves the error (4.4 JND/code); 12-bit
   doubles it (17.8 JND/code). The requirement needs **16-17 bits** of PWM
   (72 823 codes at gamma 2.2, w = 1 %). ESP32-S3 LEDC is capped at 14 bits in silicon.
   So this is a **hardware or firmware-dither problem, not a frequency/resolution trade.**
3. **The single most useful number for the LED-driver scout:**
   the driver's total PWM response budget T = t_d(on) + t_r + t_d(off) + t_f must satisfy
   **T <= 141 ns** at 13-bit/9.766 kHz for the strict reading of PAR-REQ-01
   (**T <= 567 ns** if the CIE L* curve is adopted; **T <= 5.12 us** for the loose
   "5 % of duty" reading). See s5.
4. **Flicker at 9.766 kHz is a non-issue and is over-specified.** IEEE 1789-2015
   Recommended Practice 2 removes all restriction on modulation depth above 3000 Hz;
   9.766 kHz is 3.3x above that. The carrier could drop to 3 kHz and still be at the
   no-observable-effect level with 100 % modulation. That headroom is the cheapest
   available relief on item 3 (see s5.4).
5. **PAR-REQ-03 and PAR-REQ-04 breach IEEE 1789 Recommended Practice 3**, the one
   seizure-prevention rule the standard states as a "shall" with no "if it is desired"
   qualifier. This is a firmware/creative matter, not a hardware defect - but it produces
   three real hardware requirements (s4.4) and one documentation requirement.
6. **A driver that pulse-skips, bursts or hiccups at low duty converts a compliant
   9.766 kHz carrier into a non-compliant sub-90 Hz flicker.** This is the one place
   IEEE 1789 changes this board's BOM. Make it a hard driver-selection criterion.

---

## 1. Perceptual model and the JND figure

### 1.1 The model

Under PWM dimming at constant drive current, luminous flux is linear in duty D
(this is exactly why PAR-REQ-08 mandates PWM: the LED sees a fixed current whenever it
is on, so chromaticity is invariant). So relative luminance Y = D, and PWM code c at
resolution n bits gives D = c / 2^n.

Perceived brightness is not linear in Y. Three candidate curves, all in use:

| curve | forward (perceived -> luminance) | provenance |
|---|---|---|
| gamma 2.2 | Y = P^2.2 | display / sRGB convention; near-universal in RGB colour pipelines [S6a] |
| gamma 2.0 | Y = P^2.0 | "square law", the classic theatrical dimmer curve |
| CIE 1931 L* | Y = L*/903.3 for L* <= 8; Y = ((L*+16)/116)^3 above | CIE 1976 CIELAB lightness [S6] |

`JUDGEMENT:` the CIE L* piecewise **linear toe** below Y = 0.008856 exists to remove the
cube-root singularity at zero, not because the eye becomes 9x less sensitive down there.
Using it as the dimming curve therefore *understates* the requirement at 5 % output by
about 4x versus gamma 2.2. Design to gamma 2.2; report the L* answer so the architect can
see what relaxing to it buys.

### 1.2 The JND

Weber fraction w = dY/Y at the detection threshold.

- **Primary figure, w = 1 %.** "Threshold contrast is about 1 % for a wide range of
  targets, independent of size and luminance" [S5].
- **Independent standards-grade corroboration.** DICOM PS3.14 defines the Grayscale
  Standard Display Function from Barten's contrast-sensitivity model, and states that
  **1023 JNDs fall in the luminance range 0.05 to 4000 cd/m2** [S4]. That range is
  4.903 decades, so 1023 / 4.903 = **208.6 JNDs per decade**, hence one JND is a ratio of
  10^(1/208.6) = 1.0111, i.e. **w = 1.11 %**. Two independent routes give ~1 %.
- **Stress case, w = 0.5 %.** Barten's model is not flat: threshold contrast falls to
  roughly half the average near the top of the photopic range. Reported alongside.
- **Industry benchmark, w = 2.8 %.** DALI (IEC 62386-102) logarithmic curve: 254 levels
  spanning 0.1 % to 100 %, i.e. a constant **2.8 % ratio per step** [S7]
  (check: 1000^(1/253) = 1.02768). This is what general architectural dimming accepts as
  "smooth". PAR-REQ-01 says *visually stepless*, which is the 1 % criterion, not this one -
  but the gap between them is the cheapest negotiating room available (see OPEN).

### 1.3 Spatial JND vs the JND for a slow temporal ramp - and which applies

The 1 % figure above is a **spatial / side-by-side** discrimination threshold.
PAR-REQ-01 is a **temporal** requirement ("stair-stepping during slow fades"). These are
not the same measurement and it matters which way the difference runs:

- A stair-step in an otherwise smooth fade is a **step transient**, which is broadband in
  temporal frequency and therefore excites the peak of the temporal contrast sensitivity
  function (the de Lange / Kelly TCSF), which sits at roughly 5-20 Hz under photopic
  adaptation [S14]. Sensitivity at the TCSF peak is *higher* than the low-temporal-frequency
  asymptote. So a step during a fade is at least as detectable as the same step viewed
  side by side, and plausibly more so.
- Running the other way: at low adaptation luminance Weber's law breaks down into the
  de Vries-Rose regime (threshold ~ sqrt(L)), so w *rises* as the fixture dims, which
  relaxes the requirement. But with **6-8 fixtures washing one room**, the observer's
  adaptation field is set by the ensemble, not by the one fixture being watched, so the
  adaptation level does not fall with a single fixture's output. Weber holds.

`JUDGEMENT:` net of the two effects, **w = 1 % is the correct design figure and is not
conservative**; w = 0.5 % is the defensible stress case. Do not design to 2.8 % without an
explicit human decision (OPEN-1).

---

## 2. Deliverable 1 - dimming resolution at 5 % output

### 2.1 What "5-10 % of full output" actually is, in duty

Requirements.md question 9 already flags this ambiguity; here is the arithmetic.

| reading | duty | duty % | dimming ratio |
|---|---|---|---|
| 5 % of PWM duty (loose) | 5.0e-2 | 5.0000 % | 20:1 |
| 5 % perceived, gamma 2.2 | 1.3732e-3 | 0.1373 % | **728:1** |
| 5 % perceived, gamma 2.0 | 2.5000e-3 | 0.2500 % | 400:1 |
| 5 % perceived, CIE L* = 5 | 5.5353e-3 | 0.5535 % | 181:1 |
| 10 % perceived, gamma 2.2 | 6.3096e-3 | 0.6310 % | 158:1 |
| 10 % perceived, gamma 2.0 | 1.0000e-2 | 1.0000 % | 100:1 |
| 10 % perceived, CIE L* = 10 | 1.1260e-2 | 1.1260 % | 89:1 |

Arithmetic: 0.05^2.2 = e^(2.2 * ln 0.05) = e^(-6.5906) = 1.3732e-3.
L* = 5 is below 8, so Y = 5/903.3 = 5.5353e-3. L* = 10 is above 8, so
Y = (26/116)^3 = 1.1260e-2.

**The ambiguity is worth 40x in duty** (5 % duty vs 5 % perceived gamma 2.2), and it is
the difference between an easy driver spec and an impossible one. Both answers are given
everywhere below.

### 2.2 Codes per JND and steps available - the main table

For an n-bit word, code c = D * 2^n. One code is a relative luminance step of 1/c, i.e.
**(1/c)/w JNDs per code**, equivalently **c * w codes per JND**. Pass = codes/JND >= 1.

w = 1 %. On-time is at the maximum frequency for that resolution (80 MHz / 2^n).

| reading | bits | f (kHz) | period (us) | code | on-time | step % | **JND/code** | **codes/JND** | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 5 % duty | 12 | 19.531 | 51.20 | 204.8 | 2560 ns | 0.488 | 0.49 | 2.05 | PASS |
| 5 % duty | **13** | **9.766** | **102.40** | **409.6** | **5120 ns** | **0.244** | **0.24** | **4.10** | **PASS** |
| 5 % duty | 14 | 4.883 | 204.80 | 819.2 | 10240 ns | 0.122 | 0.12 | 8.19 | PASS |
| 5 % perc. g2.2 | 12 | 19.531 | 51.20 | 5.62 | 70.3 ns | 17.78 | 17.78 | 0.056 | FAIL 17.8x |
| 5 % perc. g2.2 | **13** | **9.766** | **102.40** | **11.25** | **140.6 ns** | **8.89** | **8.89** | **0.112** | **FAIL 8.9x** |
| 5 % perc. g2.2 | 14 | 4.883 | 204.80 | 22.50 | 281.2 ns | 4.45 | 4.44 | 0.225 | FAIL 4.4x |
| 5 % perc. g2.0 | 12 | 19.531 | 51.20 | 10.24 | 128.0 ns | 9.77 | 9.77 | 0.102 | FAIL 9.8x |
| 5 % perc. g2.0 | **13** | **9.766** | **102.40** | **20.48** | **256.0 ns** | **4.88** | **4.88** | **0.205** | **FAIL 4.9x** |
| 5 % perc. g2.0 | 14 | 4.883 | 204.80 | 40.96 | 512.0 ns | 2.44 | 2.44 | 0.410 | FAIL 2.4x |
| 5 % perc. L*=5 | 12 | 19.531 | 51.20 | 22.67 | 283.4 ns | 4.41 | 4.41 | 0.227 | FAIL 4.4x |
| 5 % perc. L*=5 | **13** | **9.766** | **102.40** | **45.34** | **566.8 ns** | **2.21** | **2.21** | **0.453** | **FAIL 2.2x** |
| 5 % perc. L*=5 | 14 | 4.883 | 204.80 | 90.69 | 1133.6 ns | 1.10 | 1.10 | 0.907 | FAIL 1.1x |
| 10 % perc. g2.2 | 12 | 19.531 | 51.20 | 25.84 | 323.1 ns | 3.87 | 3.87 | 0.258 | FAIL 3.9x |
| 10 % perc. g2.2 | **13** | **9.766** | **102.40** | **51.69** | **646.1 ns** | **1.94** | **1.93** | **0.517** | **FAIL 1.9x** |
| 10 % perc. g2.2 | 14 | 4.883 | 204.80 | 103.38 | 1292 ns | 0.97 | 0.97 | 1.034 | PASS (bare) |
| 10 % perc. L*=10 | 13 | 9.766 | 102.40 | 92.24 | 1153 ns | 1.08 | 1.08 | 0.922 | FAIL 1.1x |
| 10 % perc. L*=10 | 14 | 4.883 | 204.80 | 184.5 | 2306 ns | 0.54 | 0.54 | 1.845 | PASS |

Worked example for the headline row: 5 % perceived, gamma 2.2, 13-bit.
D = 0.05^2.2 = 1.3732e-3. c = 1.3732e-3 * 8192 = **11.25** -> nearest usable codes are 11
and 12. Going 11 -> 12 changes luminance by 1/11.25 = **8.89 %**, which at w = 1 % is
**8.89 JND**. Codes per JND = 11.25 * 0.01 = **0.112**. Fail by 8.9x.

### 2.3 "N codes per JND" and "M distinct perceptual steps between 0 and 5 %"

At 13-bit / 9.766 kHz:

| reading | **N = codes per JND** | **M = distinct codes in (0, 5 %]** | JNDs the range actually spans | deficit |
|---|---|---|---|---|
| 5 % of duty | 4.10 | 409 | 604 | 1.5x |
| 5 % perceived, gamma 2.2 | **0.112** | **11** | **243** | **22.1x** |
| 5 % perceived, gamma 2.0 | 0.205 | 20 | 304 | 15.2x |
| 5 % perceived, CIE L* = 5 | 0.453 | 45 | 383 | 8.5x |

JNDs spanned = ln(c) / ln(1 + w), counting from the lowest non-zero code (1 LSB) up to the
5 % code. For gamma 2.2: ln(11.25)/ln(1.01) = 2.4204/0.00995 = **243 JNDs**, delivered by
**11 hardware steps**. The fixture has to fake 243 perceptual levels with 11 real ones.

`JUDGEMENT:` this is the whole problem in one line. A *linear* PWM word is a bad fit to a
*logarithmic* perceptual scale: at 13-bit, codes 100..8191 are finer than a JND (wasted)
and codes 1..99 are coarser (visibly stepped).

### 2.4 The general result: the smoothness floor of a linear PWM word

Because one code is a step of 1/c, stepping is invisible exactly when c >= 1/w. At
w = 1 %, that is **c >= 100 regardless of resolution**. Every linear PWM has its lowest
100 codes visibly stepped; resolution only decides what brightness those 100 codes are.

| bits | c* = 1/w | duty at c* | perceived at c*, gamma 2.2 | perceived, gamma 2.0 | L* at c* |
|---|---|---|---|---|---|
| 12 | 100 | 2.441 % | **18.5 %** | 15.6 % | 17.7 |
| **13** | 100 | 1.221 % | **13.5 %** | 11.1 % | 10.7 |
| 14 | 100 | 0.610 % | **9.85 %** | 7.8 % | 5.5 |
| 16 | 100 | 0.153 % | **5.25 %** | 3.9 % | 1.4 |
| 17 | 100 | 0.076 % | **3.83 %** | 2.8 % | 0.7 |

Read the 13-bit row: **everything below 13.5 % perceived brightness is visibly stepped.**
PAR-REQ-01's window is 5-10 % perceived. The requirement sits entirely inside the broken
region, with no margin. 14-bit moves the floor to 9.85 %, which still does not clear 5 %.

At w = 0.5 % the floor rises to 18.5 % (13-bit), 13.5 % (14-bit), 7.2 % (16-bit).
At the DALI 2.8 % benchmark it falls to 8.45 % (13-bit), 6.2 % (14-bit).

### 2.5 Does PAR-REQ-01 hold? Yes/no with numbers

| configuration | 5 % of duty | 5 % perceived (gamma 2.2) | 5 % perceived (CIE L*) |
|---|---|---|---|
| **12-bit / 19.53 kHz** | YES (2.05 codes/JND) | **NO** - 17.8 JND per code | **NO** - 4.4 JND per code |
| **13-bit / 9.766 kHz (default)** | YES (4.10 codes/JND) | **NO** - 8.9 JND per code | **NO** - 2.2 JND per code |
| **14-bit / 4.883 kHz** | YES (8.19 codes/JND) | **NO** - 4.4 JND per code | **NO** (bare) - 1.1 JND per code |

Bits required for one code <= one JND:

| operating point | w = 1 % | w = 0.5 % | w = 2.8 % (DALI) |
|---|---|---|---|
| 5 % of duty | 2 000 codes -> **11 bits** | 4 000 -> 12 bits | 714 -> 10 bits |
| 5 % perceived, gamma 2.2 | **72 823 codes -> 17 bits** | 145 645 -> 18 bits | 26 008 -> 15 bits |
| 5 % perceived, gamma 2.0 | 40 000 -> 16 bits | 80 000 -> 17 bits | 14 286 -> 14 bits |
| 5 % perceived, CIE L* = 5 | 18 066 -> 15 bits | 36 132 -> 16 bits | 6 452 -> 13 bits |
| 10 % perceived, gamma 2.2 | 15 849 -> 14 bits | 31 698 -> 15 bits | 5 660 -> 13 bits |

(N_required = 1/(w * D). For gamma 2.2 at 5 %: 1/(0.01 * 1.3732e-3) = 72 823.)

**ESP32-S3 LEDC tops out at 14 bits.** The strict requirement needs 17. The gap is
3 bits = 8x and cannot be closed by any frequency/resolution choice on the carrier.

### 2.6 PAR-REQ-02 (slow hue drift over 8-16 bars) uses the same numbers

PAR-REQ-02 is PAR-REQ-01 applied to three channels at once, over tens of seconds. At
120 BPM, 16 bars = 32 s. A hue drift across 2-3 adjacent hues moves each channel over a
significant fraction of its range, so at 60 fps command rate there are ~1920 frames to
interpolate across - far more frames than there are codes at the bottom of the range.
Banding in PAR-REQ-02 is therefore **code-limited, not frame-rate-limited**: the same
11-codes-for-243-JNDs deficit. Nothing about the 60 fps / 44 fps command stream helps.
Additionally, a hue drift is a *chromaticity* trajectory, so a step in one channel while
the others move smoothly reads as a **hue jump**, which is more objectionable than a
brightness step. `JUDGEMENT:` treat PAR-REQ-02 as needing at least the same resolution as
PAR-REQ-01, not less.

### 2.7 If 13-bit is marginal - the fixes, ranked

It is not marginal; it fails by 8.9x. Ranked by (does it actually solve it) / (cost):

**Rank 1 - lower the PWM frequency while holding 14-bit. Firmware + carrier agreement. Free.**
The "80 MHz / 2^n" figure is the *maximum* frequency for that resolution, not the only one.
ESP-IDF computes the LEDC timer divisor as a 10.8 fixed-point value from
`(src_clk << 8) / (freq * 2^duty_resolution)`, bounded by `LEDC_TIMER_DIV_NUM_MAX = 0x3FFFF`
(= divisor 1023.996) [S3]. So **f = f_src / (div * 2^bits)** and 14-bit is available at any
frequency down to 80e6/(1024*16384) = 4.8 Hz. This does **not** add codes - it multiplies
the physical duration of every code, which is what makes ranks 2 and 3 possible. Cost:
camera banding (s4.2) and, per ICD s3.3, it requires LEDC timers 2/3 and the carrier
owner's agreement - it is not a unilateral change.

**Rank 2 - temporal dithering in firmware. Free, host/firmware only, +3 to 4 effective bits.**
Alternate the duty register between adjacent codes so the time-average lands between them.
14-bit + 4-bit dither = 18 effective bits, which clears the 17-bit requirement.
Two constraints, both quantified:
- *IEEE 1789.* The dither is a real low-frequency modulation of depth 1/c. At c = 22.5
  (14-bit, 5 % perceived gamma 2.2) that is **4.4 % modulation**. To stay inside the NOEL
  the dither pattern must repeat above 4.4/0.0333 = **133 Hz**; inside the low-risk region,
  above 4.4/0.08 = 55 Hz. A 16-step dither clocked at the PWM rate repeats at f_pwm/16,
  so any f_pwm above ~2.2 kHz is safe by a wide margin. Not a real constraint, but it must
  be checked rather than assumed - and it *is* a real constraint if firmware dithers at the
  60 fps command rate instead (60 Hz NOEL limit = 2.0 % modulation; 4.4 % fails it).
  **Rule: dither in the PWM domain, not the frame domain.**
- *The driver.* Dithering only works if the driver can reproduce the difference between
  adjacent codes. At 13-bit/9.766 kHz one code is **12.5 ns** of on-time - no
  constant-current driver resolves that (s5). **Rank 2 is defeated by the hardware unless
  rank 1 is applied first.** At 14-bit/1.221 kHz one code is 50 ns on a 1.12 us pulse,
  which is tractable. Ranks 1 and 2 are a package, not alternatives.

**Rank 3 - a local PWM generator IC with >= 16-bit PWM plus per-channel current set.
Hardware, this board's problem.**
Solves the requirement outright and decouples this board from the carrier's LEDC
entirely. 16-bit constant-current LED drivers with separate global/dot-correction current
control are an established product class (this run's LED-driver scout selects; not named
here). Consequences: needs an ICD bus - DSPI (<= 26 MHz, mode 0, shared CS) or I2C
(400 kHz) are both available, and this board owns the whole I2C address space; adds a
carrier-firmware change (the carrier must drive a serial port instead of, or as well as,
PWM0-3); and the eight PWM lines may then be unused, which is a visible divergence from
the brief that needs stating rather than doing quietly.
`JUDGEMENT:` this is the answer if the human confirms the strict reading of PAR-REQ-01 and
will not accept the frequency change.

**Rank 4 - dual-rank / coarse-fine current. Hardware, and it rubs against PAR-REQ-08.**
Two (or more) fixed, calibrated current ranks, e.g. 16:1, with PWM inside each rank.
Buys 4 bits. PAR-REQ-08's argument survives *within* a rank (current is fixed while on, so
chromaticity is constant) but **not across ranks** - the two ranks have genuinely different
chromaticity and must be characterised and compensated per fixture from the PAR-REQ-17
EEPROM. Also introduces a rank-change discontinuity that must be hidden below the JND, and
a hysteresis band so a slow fade does not chatter across the boundary.
Compatible with the letter of PAR-REQ-08, arguably not its spirit -> needs explicit human
sign-off before it goes in the architecture.

**Rank 5 - 14-bit at 4.883 kHz alone. Free, but it does not solve the problem.**
2x improvement on an 8.9x deficit. Worth taking anyway because it also doubles the driver
timing budget (s5), but it is a mitigation, not a fix. State it as such so it is not
mistaken for a solution.

**Rank 6 - renegotiate the requirement.** Adopt the CIE L* curve (relaxes 4x) and/or the
DALI 2.8 %/step benchmark (relaxes 2.8x). Together at 14-bit: 5 % perceived on the L* curve
gives 1.10 JND/code = 0.39 DALI-steps/code, which passes the DALI criterion with margin.
Costs nothing and is a legitimate engineering answer, but it is a **human decision about
what the fixture should look like**, not a decision this run can take. -> OPEN-1.

Firmware-only / free: ranks 1, 2, 5, 6. Hardware, this board's problem: ranks 3, 4.

---

## 3. Deliverable 2a - IEEE 1789-2015

### 3.1 The normative boundaries, verbatim

IEEE Std 1789-2015, **Clause 8.1.1 "Simple recommended practices"** [S1], with
Modulation (%) = Mod% = 100 * (Lmax - Lmin) / (Lmax + Lmin) (Michelson contrast):

> **Recommended Practice 1:** If it is desired to limit the possible adverse biological
> effects of flicker, then flicker Modulation (%) should satisfy the following goals:
> - Below 90 Hz, Modulation (%) is less than 0.025 * frequency.
> - Between 90 Hz and 1250 Hz, Modulation (%) is below 0.08 * frequency.
> - **Above 1250 Hz, there is no restriction on Modulation (%).**
>
> **Recommended Practice 2:** If it is desired to operate within the recommended NOEL of
> flicker, then flicker Modulation (%) should be reduced by 2.5 times below the limited
> biological effect level given in Recommended Practice 1:
> - Below 90 Hz, Modulation (%) is less than 0.01 * frequency.
> - Between 90 Hz and 3000 Hz, Modulation (%) is below 0.0333 * frequency.
> - **Above 3000 Hz, there is no restriction on Modulation (%).**
>
> **Recommended Practice 3:** (seizure prevention) For any lighting source, under all
> operating scenarios, flicker Modulation (%) **shall** satisfy the following goal:
> - Below 90 Hz, Modulation (%) is less than 5%.

RP1 = "low-risk level"; RP2 = "no observable effect level (NOEL)". Illustrated in
Figure 18 and Figure 20 of the standard. Clause 8 items (b)-(e) give the same lines as
derived conclusions.

**Clause 8.1.2.3 "Example 3: PWM dimming"** is directly on point [S1]:

> Using Figure 20, the recommended practice for PWM dimming at 100% modulation depth is
> that the frequency satisfies f > 1.25 kHz. This can also be derived using Recommended
> Practice 1 and solving 100% = 0.08 * fFlicker. [...] The recommended NOEL for PWM
> dimming is 3 kHz, which can be seen in Figure 18 and can also be derived by using
> Recommended Practice 2 and solving 100% = 0.03333 * fFlicker.

**Clause 8.1.1.3 Comment 3** matters for a 4-channel fixture: the practices "describe the
boundary functions of operation for the entire LED light source and not for the individual
modulation of a single LED within the light source" - so the assessment is on the mixed
output of R+G+B+W after diffusion (PAR-REQ-15), not per channel.

**Clause 8.1.1.1 Comment 1**: the practices "should be adhered to in all operating
conditions, that is, in normal operation as well as failure modes". That reaches the
over-temperature and ENABLE behaviour on this board.

### 3.2 Where this design sits

PWM dimming is 100 % modulation depth by construction (the standard's own Figure 11 makes
this point: "the PWM current has 100% flicker").

| f_pwm | low-risk limit (RP1) | NOEL limit (RP2) | verdict at 100 % modulation |
|---|---|---|---|
| 1 200 Hz | 96.0 % | 40.0 % | fails both (marginally on low-risk) |
| 1 250 Hz | 100 % | 41.6 % | low-risk boundary exactly |
| 2 441 Hz | unrestricted | 81.3 % | low-risk OK, NOEL fails |
| 3 000 Hz | unrestricted | 100 % | **NOEL boundary exactly** |
| 4 883 Hz (14-bit) | unrestricted | unrestricted | **NOEL, 1.6x margin** |
| **9 766 Hz (13-bit, default)** | **unrestricted** | **unrestricted** | **NOEL, 3.3x margin** |
| 19 531 Hz (12-bit) | unrestricted | unrestricted | NOEL, 6.5x margin |

**Answer: at 9.766 kHz with 100 % modulation depth this design is in the unrestricted
region above the NOEL threshold of Recommended Practice 2 (Clause 8.1.1), with 3.3x
frequency margin.** IEEE 1789 imposes **no constraint whatsoever** on the PWM carrier of
this board.

**Consequence the architect should act on:** the 9.766 kHz choice buys 3.3x more flicker
margin than IEEE 1789 asks for, while costing 3.3x in the driver timing budget (s5). The
standard's own PWM recommendation is 3 kHz. That is the cheapest available relief.

Two adjacent metrics, checked and found not to bind:
- **SVM** (stroboscopic visibility measure, CIE TN 006:2016 / IEC TR 63158) is defined for
  modulation **up to 2 kHz** and illuminance above 100 lx [S8]. At 9.766 kHz the SVM
  weighting is zero; SVM = 0. Acceptance criteria seen in the field (SVM <= 0.4) are
  satisfied trivially.
- **PstLM** (IEC 61000-4-15) addresses direct-view flicker at line-frequency scale; it does
  not reach a 9.766 kHz carrier either.

### 3.3 What IEEE 1789 says about deliberate low-frequency effects (PAR-REQ-03/04)

**Nothing exempting them.** Checked directly: the standard contains no entertainment,
theatrical, effect-lighting or "intentional modulation" carve-out. **Clause 8.5** is
explicit that it declines to make application-specific practices at all:

> Therefore, IEEE Std 1789 does not provide application-specific recommended practices
> but, instead, gives recommended practices that can be used to help mitigate the risk of
> possible adverse biological health effects in all types of LED lighting.

**Clause 8.1.1.2 Comment 2** draws the distinction that matters here: RP1 and RP2 begin
"If it is desired", but **RP3 does not** - "Recommended Practice 3 is a strict rule for
seizure prevention and should be adhered to at all times for all operating conditions."

Evaluating the requirements as written:

| requirement | modulation | frequency | RP3 limit (5 %) | RP1 low-risk limit | verdict |
|---|---|---|---|---|---|
| PAR-REQ-03 pulse-and-decay 80 % -> 30 % per kick | Michelson = 100*(0.8-0.3)/(0.8+0.3) = **45.5 %** | ~2 Hz @ 120 BPM, up to ~5 Hz | 5 % | 0.05-0.125 % | **breaches RP3 by 9.1x** |
| PAR-REQ-04 intensity tracking to ~20 Hz | depth unspecified; any depth > 5 % breaches | up to 20 Hz | 5 % | 0.50 % | **breaches RP3 for any usable depth** |

Clause 8 item (a) puts the seizure-risk band at "~1 Hz to ~65 Hz" - which is exactly where
a musical envelope lives.

**Does this change a hardware requirement on this board? Yes - three of them, plus one
documentation item.** Note the framing: the hardware must *not* prevent the intentional
effect (that is the fixture's purpose and it is a firmware/creative decision). What the
hardware must prevent is **unintentional** sub-90 Hz modulation.

1. **No pulse-skipping, burst mode, hiccup mode or audio-band-avoidance modulation in the
   LED driver, anywhere in the 0-100 % commanded duty range.** Many switching CC drivers
   enter a light-load burst/skip mode below some duty; that converts a compliant 9.766 kHz
   carrier into a burst envelope in the tens-of-Hz band - straight into RP3's forbidden
   region, and visible as flutter at exactly the 5-10 % output PAR-REQ-01 cares about.
   This is a **hard driver-selection criterion** and it is the one place IEEE 1789 changes
   this board's BOM.
2. **Over-temperature protection (PAR-REQ-12) must not oscillate.** A thermal foldback or
   thermal-shutdown loop that cycles at 0.1-10 Hz in a continuously-hot enclosure
   (56-69 C internal air) produces a large-depth sub-90 Hz modulation in a failure mode -
   and Clause 8.1.1.1 Comment 1 explicitly extends the practices to failure modes. Require
   either a latching shutdown or a hysteresis band wide enough that cycling cannot occur
   at the steady-state operating point. Note that thermal *foldback* (a smooth current
   reduction) is also a PAR-REQ-08 problem independently: it is analogue current dimming
   by another name and it shifts chromaticity.
3. **Power-up must not produce a visible low-frequency flash sequence.** The ICD notes a
   carrier PWM pin can glitch ~60 us at power-up, `+48V_SW` is dead for hundreds of ms,
   and there is no mate sequencing. The ENABLE gate (100 k pull-down, gating every output
   stage, never latched locally) already covers this; record it as an IEEE 1789 rationale
   as well as an ICD one, so it does not get value-engineered away.
4. **Documentation:** IEEE 1789 Clause 8.5 itself cites the video-game industry's
   photosensitivity warning-label practice as the precedent for a product that
   deliberately modulates. A photosensitive-epilepsy note belongs in the fixture
   documentation. Not a PCB requirement; record it so it is not lost.

---

## 4. Deliverable 2b - stroboscopic / rolling-shutter camera banding

### 4.1 The physics, with the formula

A rolling-shutter sensor exposes each row over a window of length T_exp, with successive
rows offset by the line time t_line. Row n integrates the PWM waveform over
[t_n, t_n + T_exp].

Write T_exp = (k + phi) * T_pwm, k integer. The complete periods contribute identically to
every row; only the fractional part phi carries row-to-row variation. Over all phases the
worst-case peak-to-peak variation of integrated on-time is min(D, 1-D) * T_pwm, while the
mean is D * T_exp. Hence

> **worst-case band contrast = min(D, 1-D) * T_pwm / (D * T_exp) = T_pwm / T_exp for D <= 0.5**

Two properties worth stating explicitly:
- **Band contrast is independent of duty below 50 % duty.** Dimming does not help.
- It is **zero** when T_exp is an exact integer multiple of T_pwm, and worst when the
  fractional part is near D. PWM and shutter are unsynchronised and drift, so the
  worst case is the design figure.

Band *spatial period* in scan lines = T_pwm / t_line, which sets how coarse the bands look.

### 4.2 The numbers

Worst-case band contrast T_pwm / T_exp, in percent:

| f_pwm | T_pwm | 1/60 s (60 fps) | 1/120 s | 1/240 s (240 fps) | 1/480 s | 1/1000 s |
|---|---|---|---|---|---|---|
| **1 200 Hz** (the rejected option) | 833.3 us | **5.00 %** | 10.00 % | **20.00 %** | 40.00 % | 83.33 % |
| 2 441 Hz | 409.7 us | 2.46 % | 4.92 % | 9.83 % | 19.66 % | 40.97 % |
| 4 883 Hz (14-bit) | 204.8 us | 1.23 % | 2.46 % | 4.92 % | 9.83 % | 20.48 % |
| **9 766 Hz (chosen)** | 102.4 us | **0.61 %** | 1.23 % | **2.46 %** | 4.92 % | 10.24 % |
| 19 531 Hz (12-bit) | 51.2 us | 0.31 % | 0.61 % | 1.23 % | 2.46 % | 5.12 % |
| 39 063 Hz (11-bit) | 25.6 us | 0.15 % | 0.31 % | 0.61 % | 1.23 % | 2.56 % |

Visibility threshold: periodic bands on a smooth surface are detectable at roughly the
same ~1 % Weber contrast as any other luminance difference [S5], and the visual system is
if anything better at periodic patterns than at isolated steps. Use **1-2 % as the
banding-visible threshold**.

Independent cross-check from the trade: "aim for PWM at least 30x your camera frame rate"
[S12] - 60 fps -> 1.8 kHz, 120 fps -> 3.6 kHz, 240 fps -> 7-8 kHz, 1000 fps -> ~30 kHz.
That heuristic is algebraically the same statement as the formula above with
T_exp = 1/fps, implying an accepted contrast of 1/30 = **3.3 %**. It is a looser threshold
than the 1-2 % perceptual figure, which is the expected direction for trade guidance.

### 4.3 Confirm or challenge the 10 kHz choice

**Confirmed, with a number: 9.766 kHz is 8.1x better than 1.2 kHz** (833.3/102.4), and the
qualitative gap is larger than 8.1x because the 1.2 kHz bands are also **8.1x coarser**
(at 240 fps / 1080 lines, t_line = 4167/1080 = 3.86 us, so bands are 216 lines wide at
1.2 kHz versus 26.5 lines at 9.766 kHz - coarse high-contrast bands are far more
objectionable than fine low-contrast ones). The carrier brief's reasoning is sound.

**Challenged, on scope:** 9.766 kHz does not *eliminate* banding, it defers it.
- Up to and including **120 fps** it is clean (0.61-1.23 %, at or below the visibility
  threshold). This covers essentially all phone video and normal "people film parties".
- At **240 fps** it is **marginal** (2.46 %, above the 1-2 % threshold, below the 3.3 %
  trade heuristic). Expect faint banding in 240 fps slow motion.
- At **480 fps and above, or any short shutter in a bright scene**, it bands (4.9 %+).
- **960 fps super-slow-motion is unreachable.** It would need ~29 kHz [S12] or, for a 1 %
  contrast target with T_exp = 1/960 s, f_pwm > 96 kHz. LEDC cannot deliver that at any
  usable resolution: 11-bit/39 kHz would need spending 2 more bits of an already-failing
  resolution budget. **Declare 960 fps out of scope rather than pretend.**

**The direct conflict the architect must arbitrate:** camera banding wants the PWM
frequency HIGH; the driver timing budget (s5) and the dimming resolution both want it LOW.
IEEE 1789 permits going down to 3 kHz at NOEL and 1.25 kHz at low-risk. Every halving of
f_pwm doubles the driver's tolerable T and doubles the LSB duration (making dithering
work), at the cost of doubling the band contrast. The trade points:

| f_pwm | driver budget T at 5 % perc. g2.2 | band contrast @ 60 fps | @ 240 fps | IEEE 1789 |
|---|---|---|---|---|
| 9 766 Hz (13-bit) | 141 ns | 0.61 % | 2.46 % | NOEL, 3.3x margin |
| 4 883 Hz (14-bit) | 281 ns | 1.23 % | 4.92 % | NOEL, 1.6x margin |
| 2 441 Hz (14-bit, div 2) | 563 ns | 2.46 % | 9.83 % | low-risk only |
| 1 221 Hz (14-bit, div 4) | 1.12 us | 4.92 % | 19.7 % | below both lines |

`JUDGEMENT:` **4.883 kHz (14-bit, divider 1) is the defensible compromise** - it keeps the
NOEL with 1.6x margin, stays under the visibility threshold at 60 fps, doubles the driver
budget, and gains a bit of resolution. Below that the camera cost rises faster than the
driver benefit. Going below 3 kHz should not be done without a human decision because it
leaves the standard's PWM recommendation.

---

## 5. Deliverable 3 - the LED-driver timing budget

### 5.1 On-time table at 13-bit / 9.766 kHz

Period = 1/9765.625 Hz = **102.4 us**. 1 LSB = 102.4 us / 8192 = **12.5 ns**
(equivalently 1/80 MHz - at maximum resolution for the frequency the LSB is always one
source-clock tick).

| commanded level | duty | on-time | code (13-bit) |
|---|---|---|---|
| 100 % | 100 % | 102.40 us | 8192 (clamped to 8191, see s5.6) |
| 50 % | 50 % | 51.20 us | 4096 |
| 10 % | 10 % | 10.24 us | 819.2 |
| 5 % | 5 % | **5.12 us** | 409.6 |
| 1 % | 1 % | 1.024 us | 81.9 |
| 0.1 % | 0.1 % | 102.4 ns | 8.2 |
| **1 LSB (code 1 of 8191)** | 0.01221 % | **12.5 ns** | 1 |
| 5 % perceived, CIE L* = 5 | 0.5535 % | 566.8 ns | 45.3 |
| 5 % perceived, gamma 2.0 | 0.2500 % | 256.0 ns | 20.5 |
| **5 % perceived, gamma 2.2** | 0.1373 % | **140.6 ns** | 11.3 |
| 10 % perceived, gamma 2.2 | 0.6310 % | 646.1 ns | 51.7 |

### 5.2 The linearity model, and what "T" actually bounds

Model the LED current pulse as trapezoidal: after the PWM rising edge, current stays at
zero for t_d(on), then ramps linearly to I over t_r; after the falling edge it stays at I
for t_d(off), then ramps to zero over t_f. For a commanded on-time t_c, the delivered
charge (and hence the light, since flux is linear in charge at fixed current) is

> Q(t_c) = I * [ t_c - t_d(on) + t_d(off) + (t_f - t_r)/2 ]  =  I * [ t_c + Delta ]

with **Delta = t_d(off) - t_d(on) + (t_f - t_r)/2**.

Two consequences that decide the whole spec:

- **Above the knee, the transfer function is exactly linear with a fixed offset Delta.**
  A fixed offset is a calibration coefficient, not a stepping artifact. So a large but
  *matched and stable* T is not, by itself, fatal.
- **Below the knee the pulse never fully develops** and Q becomes sub-linear, then zero.
  The knee is at t_c ~ t_d(on) + t_r - t_d(off). Worst-casing t_d(off) -> 0 and bounding
  t_d(on) + t_r by the full budget T = t_d(on) + t_r + t_d(off) + t_f gives
  **knee <= T**. So requiring **t_c(min) >= T** is a conservative but checkable criterion,
  and that is the criterion used below.

### 5.3 The number: maximum tolerable T

**Criterion: T <= the on-time at the lowest commanded output level that PAR-REQ-01 covers.**

| reading of "5 % output" | 12-bit / 19.53 kHz | **13-bit / 9.766 kHz** | 14-bit / 4.883 kHz | 14-bit / 2.441 kHz | 14-bit / 1.221 kHz |
|---|---|---|---|---|---|
| 5 % of PWM duty (loose) | 2.56 us | **5.12 us** | 10.24 us | 20.48 us | 40.96 us |
| **5 % perceived, gamma 2.2** | 70.3 ns | **141 ns** | 281 ns | 563 ns | 1.12 us |
| 5 % perceived, gamma 2.0 | 128 ns | **256 ns** | 512 ns | 1.02 us | 2.05 us |
| 5 % perceived, CIE L* = 5 | 283 ns | **567 ns** | 1.13 us | 2.27 us | 4.53 us |
| 10 % perceived, gamma 2.2 | 323 ns | **646 ns** | 1.29 us | 2.58 us | 5.17 us |

> ### THE SPEC
> **At the carrier's default 13-bit / 9.766 kHz, and the strict reading of PAR-REQ-01
> (5 % of perceived brightness, gamma 2.2), the LED driver's total PWM response budget
> t_d(on) + t_r + t_d(off) + t_f must not exceed 141 ns.**
>
> Relaxations, in order of how likely the human is to grant them:
> - adopt the CIE L* curve: **567 ns**
> - move to 14-bit / 4.883 kHz: **281 ns** (both together: **1.13 us**)
> - accept the loose "5 % of duty" reading: **5.12 us**
> - "5-10 %" read at the 10 % end, gamma 2.2, 14-bit: **1.29 us**
>
> Add a **3x margin** for real (non-trapezoidal, ringing) current waveforms, output-cap
> recharge and the LED's own optical settling if the driver is to be *linear* rather than
> merely *conducting*: 141 ns -> **47 ns**, 567 ns -> **189 ns**, 1.13 us -> **377 ns**.

Sanity check against real silicon, as an existence proof (these are evidence that the
spec is or is not reachable - not a part selection):

| device class | figure | source | verdict against 141 ns |
|---|---|---|---|
| 8-channel **linear** CC driver (TPS92638-Q1) | PWM turn on/off delay **25 us typ, 45 us max**; current slew 6 mA/us typ, so t_r at 70 mA ~ 11.7 us -> **T ~ 73 us** | [S9] | fails by ~520x; would be non-linear below 71 % duty at 102.4 us period. Rules out this whole class. |
| Buck CC driver with fast direct PWM (TPS922050/51 "D1") | "PWM input signals with ultra-narrow pulse width down to **50-ns**"; EC table t(PWM_IN_ON), t(PWM_OUT_ON) minimum on time **100 ns** | [S10] | meets 141 ns bare; meets 567 ns and 1.13 us with margin |
| Buck CC driver, shunt-FET-dimming compatible (TPS92520-Q1) | "over a 1000:1 PWM dimming ratio", "compatible with shunt FET dimming" | [S11] | 1000:1 at 102.4 us period = 102 ns minimum pulse; meets 141 ns bare |

`JUDGEMENT:` **141 ns is at the very edge of what exists**, and only for buck drivers with
a dedicated fast-PWM path or a shunt-FET arrangement. 567 ns and above is comfortable.
Anything derived from a linear multi-channel driver is dead on arrival, which independently
corroborates PAR-REQ-10's ban on burning the Vf spread in a shared linear element.

### 5.4 The frequency lever

T scales exactly with the PWM period, so the driver spec is directly purchasable with PWM
frequency. Each halving of f_pwm doubles the tolerable T and doubles the LSB duration
(which is what makes firmware dithering physically reproducible - s2.7 rank 2). IEEE 1789
permits 3 kHz at NOEL, so there is 3.3x available on this axis. The cost is camera banding
(s4.3) and, per ICD s3.3, the carrier owner's agreement to use LEDC timers 2/3.
This is the highest-leverage single decision in this document.

### 5.5 Channel matching - what PAR-REQ-02/06 need

From s5.2, each channel's transfer function is Q_i(t_c) = I_i * (t_c + Delta_i). A
**mismatch in Delta between channels is a pure on-time offset**, so the relative flux error
between two channels at commanded on-time t_c is (Delta_i - Delta_j) / t_c - which grows
without bound as t_c falls. That is precisely the region PAR-REQ-01 and PAR-REQ-02 live in.

Matching required for a 1 % inter-channel flux match (13-bit / 9.766 kHz):

| operating point | on-time | dDelta for 1 % | dDelta for 0.3 % |
|---|---|---|---|
| 5 % of duty | 5.12 us | 51.2 ns | 15.4 ns |
| 5 % perceived, CIE L* = 5 | 567 ns | 5.7 ns | 1.7 ns |
| **5 % perceived, gamma 2.2** | **141 ns** | **1.4 ns** | **0.42 ns** |

**1.4 ns of inter-channel delay matching is not achievable by construction.** Therefore:

1. **Inter-channel matching at the bottom of the range must be calibrated, not built.**
   PAR-REQ-17's EEPROM is the mechanism. But note: **a single per-channel gain scalar
   cannot correct an offset.** The calibration record must carry, per channel, at minimum
   a gain **and an offset** (2 coefficients), and ideally a short LUT (8-16 points) over
   the bottom decade to capture the knee where the model stops being linear. This is a
   concrete requirement on the EEPROM contents and therefore on its size - state it in the
   architecture so the part is not chosen too small.
2. **Delta must be stable, not small.** The enclosure runs at 56-69 C internal air
   continuously, and the emitters' Vf drifts with junction temperature. If Delta drifts,
   the calibration goes stale and the fixtures diverge over the first hour of a set -
   exactly the PAR-REQ-06 failure. Specify: driver PWM delay/rise/fall stability over
   -0 to +85 C, and over the Vf range each channel actually sees.
3. **All four channels must use the same driver part, the same topology and the same
   passive values wherever the Vf spread allows.** Common-mode drift cancels in the colour
   *ratio*; differential drift does not. This is a real constraint even though PAR-REQ-10's
   Vf spread invites treating the red channel differently. If red must differ, its Delta
   drift must be characterised separately and the EEPROM must carry a temperature
   coefficient, not just a constant.
4. **The knee is not calibratable with a scalar.** Below the knee the transfer function is
   sub-linear and channel-specific; only a LUT helps, and even then monotonicity must be
   guaranteed by the hardware. **Require the driver's duty-to-flux transfer to be monotonic
   and single-valued over the whole commanded range** - no dropout, no hysteresis, no
   discontinuity. This is a separate criterion from T and it is the one that actually
   protects PAR-REQ-01 against stair-stepping.

### 5.6 One LEDC artifact to record

At maximum duty resolution for the chosen frequency, the LEDC duty register cannot be set
to 2^n: "the internal duty counter in the hardware will overflow and be messed up" [S2].
Firmware clamps to 2^n - 1, so maximum duty is 8191/8192 = **99.988 %**, a 0.012 %
shortfall. Irrelevant to output (PAR-REQ-11's total-power clamp means four channels never
reach 100 % anyway) and it costs one code out of 8192. No hardware consequence. Note that
the clamp is a consequence of running the timer's divider at 1, so it does not apply if
14-bit is run at a divided-down frequency.

### 5.7 If the driver cannot meet T - mitigations, and PAR-REQ-08 compatibility

| # | mitigation | effect | PAR-REQ-08 compatible? |
|---|---|---|---|
| 1 | **Lower f_pwm** (s5.4) | T scales 1:1 with period; free | **Yes** - still pure PWM at fixed current |
| 2 | **Shunt-FET dimming**: a FET across the LED string, converter left running in steady state | decouples the dimming edge from the converter's control loop; reaches sub-100 ns. The established automotive answer [S11] | **Yes** - the LED sees the same regulated current whenever it conducts |
| 3 | **Series-FET dimming** with the converter held in regulation and the output cap sized so it does not slow the edge | fast edges; simpler than 2 | **Yes** |
| 4 | **Longer LED strings per channel** (more dies in series, lower current) | raises Vf, moves the converter to a duty that recovers faster; also eases the 12 V -> 2.1-3.6 V step-down problem in requirements.md s3.4 | **Yes** - no change to the dimming mechanism |
| 5 | **Dual-rank current switching** (s2.7 rank 4) | 4 bits of relief and raises the minimum on-time by the rank ratio | **Partially** - fixed current within each rank preserves the chromaticity argument; the inter-rank chromaticity step must be calibrated per fixture. **Needs explicit human sign-off**, it is an exception to PAR-REQ-08's intent |
| 6 | Continuous analogue current dimming | would solve the timing problem entirely | **NO** - explicitly banned by PAR-REQ-08, and the ban is correct: dominant wavelength and phosphor CCT both shift with drive current, breaking PAR-REQ-02 and PAR-REQ-06 |
| 7 | Thermal foldback used as a dimming mechanism | - | **NO** - analogue current dimming by another name; also an IEEE 1789 RP3 risk if it oscillates (s3.3) |
| 8 | Reducing the number of dies driven per channel | - | **NO in spirit** - changes the emitter mix and therefore the chromaticity |

Preferred order: 1, then 2/3, then 4, then 5 with sign-off. Never 6, 7, 8.

---

## 6. Requirements this hands to the architect

**Resolution and dimming**
- R1. The strict reading of PAR-REQ-01 needs **17 bits** of PWM (72 823 codes); LEDC gives
  14. Close the gap with (lower f_pwm + firmware PWM-domain dithering) or a local >=16-bit
  PWM generator, or renegotiate the reading. Do not ship 13-bit linear and hope.
- R2. Firmware dithering must run in the **PWM domain** (pattern repeat >= ~300 Hz), not
  the 60 fps frame domain, or it becomes an IEEE 1789 NOEL violation in its own right.
- R3. Dithering is only physically reproducible if one LSB is longer than the driver can
  resolve. At 13-bit/9.766 kHz one LSB is 12.5 ns - it is not. Ranks 1 and 2 of s2.7 are a
  package.

**Driver**
- R4. **T = t_d(on) + t_r + t_d(off) + t_f <= 141 ns** at 13-bit/9.766 kHz, strict reading.
  See s5.3 for the relaxed values under each alternative reading and frequency.
- R5. Duty-to-flux transfer **monotonic and single-valued** over 0-100 % commanded duty.
  No dropout, no hysteresis, no discontinuity.
- R6. **No pulse-skipping / burst / hiccup / audio-band-avoidance mode at any duty.**
  (IEEE 1789 RP3 - Clause 8.1.1 - plus visible flutter at the PAR-REQ-01 operating point.)
- R7. Rules out linear multi-channel CC drivers on timing alone (T ~ 73 us for a
  representative part, s5.3), independent of PAR-REQ-10's thermal argument.
- R8. All four channels: same driver part, same topology, same passives where the Vf
  spread allows. Common-mode drift cancels in the colour ratio; differential drift does not.
- R9. PWM delay/rise/fall stability specified over the enclosure's 56-69 C internal air
  and over each channel's Vf range - the calibration is only as good as Delta's stability.

**Protection**
- R10. Over-temperature shutdown (PAR-REQ-12) must be latching or wide-hysteresis; it must
  not cycle in the 0.1-10 Hz band. Thermal foldback (smooth current reduction) is doubly
  disallowed: analogue current dimming (PAR-REQ-08) and an RP3 risk.
- R11. ENABLE gating of every output stage is also the IEEE 1789 power-up argument, not
  only the ICD's.

**Calibration**
- R12. The PAR-REQ-17 EEPROM record must carry per channel a **gain and an offset**
  (minimum), ideally plus a short LUT over the bottom decade. A gain-only record cannot
  correct the on-time offset that dominates below ~1 us. Size the EEPROM for it.

**Flicker**
- R13. No hardware requirement flows from the PWM carrier: 9.766 kHz at 100 % modulation is
  unrestricted under IEEE 1789 RP2 with 3.3x margin. There is 3.3x of frequency available
  to spend on R4 before the standard's own PWM recommendation (3 kHz) is reached.
- R14. Photosensitive-epilepsy note in the fixture documentation (PAR-REQ-03/04 breach
  RP3; IEEE 1789 Clause 8.5 cites the video-game warning-label precedent).

---

## 7. Layout / schematic notes that fall out of this

1. **Do not put an RC filter on the PWM/DIM lines.** The reflex "noise immunity" network
   (1 k + 100 pF, tau = 100 ns) would swallow a 141 ns pulse entirely and silently destroy
   the bottom of the dimming range. If any series/shunt network is fitted, require
   **tau <= t_on(min)/10**, i.e. **<= 14 ns** at the strict operating point (e.g. 33 ohm +
   100 pF = 3.3 ns; 33 ohm + 390 pF = 12.9 ns). Record the constraint on the schematic.
2. **Trace-length matching between PWM0..3 is NOT required.** A common or differential
   propagation delay shifts the pulse's *phase*, not its *width*, and duty is what sets
   flux. Do not spend routing effort on it. What must be matched is the *driver's*
   t_d/t_r/t_f (part selection, s5.5), not the copper.
3. **Edge jitter is the routing constraint instead.** At a 141 ns pulse, 1.4 ns of jitter
   is a 1 % flux error. Route PWM/DIM as short, continuously ground-referenced traces; no
   long parallel runs alongside a driver switch node or inductor; keep them off the
   split/void regions of the reference plane.
4. **Request 90-degree phase stagger across the four PWM channels from the carrier owner.**
   LEDC exposes a per-channel `hpoint`, and PWM0-3 share timer 0, so channels can be
   staggered at hpoint = 0, N/4, N/2, 3N/4 without changing frequency or duty. Interleaving
   four in-phase channels reduces the worst-case input-current step by up to 4x, which
   directly relieves this board's bulk capacitance and its draw against the 0.75 A +12 V
   sustained ceiling. Costs nothing; it is a carrier firmware constant. Ask early - it is
   the same conversation as the LEDC timer 2/3 request.
5. **The eight ICD PWM lines are 3.3 V CMOS with fast edges** (nanosecond-class GPIO edges,
   not 9.766 kHz-class). Their harmonic content reaches into the tens of MHz, well below
   2.4 GHz, so they are **not** the antenna-column desense threat - the driver switch nodes
   are. Do not over-engineer the PWM routing at the expense of switch-node containment.
6. **If a local PWM generator IC is chosen (s2.7 rank 3)**, its I2C address must be
   allocated alongside the EEPROM and any digital temperature sensor - this board owns the
   whole address space and the carrier reserves nothing, so collisions are this board's
   fault. If DSPI is used instead, note that the ICD provides only one CS.
7. **Decoupling at each driver's DIM/EN pin** must not be a bulk part; the same tau <= 14 ns
   rule applies to anything hung on those nodes.

---

## Sources

- [S1] **IEEE Std 1789-2015**, *IEEE Recommended Practices for Modulating Current in
  High-Brightness LEDs for Mitigating Health Risks to Viewers.* Clause 8 (conclusions a-e),
  **8.1.1 Recommended Practices 1/2/3**, 8.1.1.1 Comment 1, 8.1.1.2 Comment 2,
  8.1.1.3 Comment 3, **8.1.2.3 Example 3: PWM dimming**, 8.3, **8.5**, Figures 18 and 20.
  Text verified verbatim from a public copy of the standard PDF:
  https://www.lisungroup.com/wp-content/uploads/2020/02/IEEE-2015-STANDARDS-1789-Standard-Free-Download.pdf
  (standard itself: https://standards.ieee.org/ieee/1789/4479/)
- [S2] Espressif, **ESP-IDF Programming Guide - LED PWM Controller (LEDC), ESP32-S3**:
  low-speed mode only; 4 timers / 8 channels; duty cannot be set to 2^duty_resolution at
  maximum resolution; new parameters take effect at the next PWM cycle;
  `ledc_set_fade_with_time` / `ledc_set_fade_with_step`.
  https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/ledc.html
- [S3] Espressif, **esp-idf `components/esp_driver_ledc/src/ledc.c`** (master):
  `ledc_calculate_divisor()` = `((src_clk_freq << LEDC_LL_FRACTIONAL_BITS) + freq*precision/2) / (freq*precision)`
  with `precision = 2^duty_resolution` and `LEDC_TIMER_DIV_NUM_MAX = 0x3FFFF`.
  Establishes f = f_src / (div * 2^bits) with div up to ~1024 - i.e. resolution and
  frequency are decoupled by the divider.
  https://raw.githubusercontent.com/espressif/esp-idf/master/components/esp_driver_ledc/src/ledc.c
- [S4] **DICOM PS3.14**, *Grayscale Standard Display Function*: GSDF is a mathematical
  interpolation of 1023 luminance levels derived from Barten's model; **1023 JNDs fall in
  the luminance range 0.05 to 4000 cd/m2**. https://dicom.nema.org/medical/dicom/current/output/html/part14.html
- [S5] **Pelli & Bex, "Measuring contrast sensitivity", Vision Research (2013)**:
  "Threshold contrast is about 1% for a wide range of targets, independent of size and
  luminance." https://pmc.ncbi.nlm.nih.gov/articles/PMC3744596/
- [S6] **CIE 1931/1976 lightness (CIELAB) L***: L* = 116*(Y/Yn)^(1/3) - 16 for
  Y/Yn > 0.008856, L* = 903.3*(Y/Yn) otherwise.
  [S6a] gamma 2.2 as the display/RGB pipeline convention (sRGB, IEC 61966-2-1).
- [S7] **IEC 62386-102 (DALI)** logarithmic dimming curve: 254 levels spanning 0.1 % to
  100 % of output, constant **2.8 % ratio between successive levels**.
  https://www.upowertek.com/what-are-dimming-curves-and-how-to-choose/
- [S8] **CIE TN 006:2016** / **IEC TR 63158** - stroboscopic visibility measure (SVM),
  defined for modulation up to **2 kHz** and illuminance above **100 lx**; SVM < 1 = not
  visible. https://www.gigahertz-optik.com/en-us/service-and-support/knowledge-base/flicker-measurement-with-the-bts256-ef/
- [S9] **TI TPS92638-Q1** datasheet SLVSCK5C (8-channel linear LED driver):
  "Turn ON/OFF Delay Time: 25 us (typ.), 45 us"; current slew rate 6 mA/us typ at 70 mA.
  https://www.ti.com/lit/ds/symlink/tps92638-q1.pdf
- [S10] **TI TPS922050 / TPS922051** datasheet: "Fast PWM dimming (50ns pulse width)";
  "The TPS922050D1 and TPS922051D1 support PWM input signals with ultra-narrow pulse width
  down to 50-ns"; EC table t(PWM_IN_ON) / t(PWM_OUT_ON) minimum on time **100 ns** (D1).
  https://www.ti.com/lit/gpn/TPS922050
- [S11] **TI TPS92520-Q1** datasheet: "capable of achieving over a 1000:1 PWM dimming
  ratio"; "compatible with shunt FET dimming".
  https://www.ti.com/lit/ds/symlink/tps92520-q1.pdf
- [S12] Trade guidance (NOT a standard), UKing stage-lighting knowledge hub, *Adjusting PWM
  Refresh Rates for High-Speed Cameras*: "aim for PWM at least 30x your camera frame rate";
  240 fps -> 7 000-8 000 Hz; 1 000 fps -> ~30 kHz.
  https://www.uking-online.com/blogs/stage-lighting-dmx-knowledge-hub/adjusting-pwm-refresh-rates-for-high-speed-cameras
- [S13] Internal: `boards/lumina-par/requirements.md`,
  `brief/03-rgbw-par-daughter-brief.md`, ICD-01 s3.3 / s6 / s7.
- [S14] **de Lange (1958) / Kelly (1961)** temporal contrast sensitivity function, as
  surveyed and refitted in *elaTCSF: A Temporal Contrast Sensitivity Function for Flicker
  Detection* (SIGGRAPH Asia 2024): Kelly's TCSF measured at 9 300 td (photopic); TCSF peaks
  in the mid temporal frequencies. https://arxiv.org/html/2503.16759v1

---

## OPEN - questions and conflicts

**OPEN-1 (BLOCKING, and it is requirements.md question 9).** Which reading of "5-10 % of
full output" is binding? It is worth **40x in duty** and it is the difference between a
141 ns driver spec (near the edge of what exists) and a 5.12 us one (routine). This
document answers both, but the LED-driver scout cannot shortlist without it.
**Recommendation: 5 % of *perceived* brightness on a gamma-2.2 curve** (the strict reading;
designing for it satisfies the loose one automatically). If the human will accept the
CIE L* curve instead, the spec relaxes 4x to 567 ns at no cost - ask explicitly, since the
L* toe is a numerical convenience rather than a perceptual claim and adopting it is a
deliberate loosening, not a neutral choice.

**OPEN-2 (BLOCKING for P2).** Requesting the PWM frequency change (and/or LEDC timers 2/3,
and/or the 90-degree channel phase stagger) is a **carrier-owner decision**, per ICD s3.3 -
"that is the only sanctioned route to a different PWM frequency for this daughter, and it
needs the carrier owner's agreement, not a unilateral change". Recommend raising all three
in one request now: (a) 14-bit at 4.883 kHz, (b) hpoint stagger across PWM0-3,
(c) confirmation that timers 2/3 remain available. Without (a) the driver spec stays at
141 ns and the shortlist may be empty.

**OPEN-3.** Do PAR-REQ-03 / PAR-REQ-04 stand as written, given they breach IEEE 1789
Recommended Practice 3 (the seizure-prevention "shall", 5 % modulation below 90 Hz) by
roughly 9x? This is a human decision about the product, not an engineering one. It changes
no hardware here except through R6/R10/R14, but it should be a recorded decision rather
than an accident.

**OPEN-4.** Is 240 fps slow-motion capture in scope? 9.766 kHz gives 2.46 % band contrast
there (marginal); 4.883 kHz gives 4.92 % (visible). 960 fps is unreachable at any usable
LEDC setting and should be declared out of scope. This directly trades against OPEN-2(a).

**OPEN-5 - source conflict, resolved but recorded.** AZoM's summary of IEEE PAR1789
(https://www.azom.com/article.aspx?ArticleID=14729) **swaps the NOEL and low-risk labels**,
giving "NOEL: Max % Modulation <= f x 0.025" below 90 Hz and "low-risk: f x 0.01", and
"NOEL: f x 0.08" / "low-risk: f x 0.033" above 90 Hz. That is inconsistent - the NOEL must
be the *stricter* limit - and it contradicts the standard's own text quoted in s3.1, which
is unambiguous (RP2/NOEL = 0.01 and 0.0333; RP1/low-risk = 0.025 and 0.08). **The standard
text is used throughout; AZoM is wrong.** Flagged because that page ranks highly and a
reviewer may hit it.

**OPEN-6.** The requirements doc's derivation of the flicker frequency ("80 MHz / 2^n")
presents frequency and resolution as rigidly coupled. Verified from the ESP-IDF driver
source [S3] that they are **not**: the LEDC timer divisor decouples them, so 14-bit is
available at any frequency at or below 4.883 kHz. This widens the trade space and should be
corrected wherever the coupling is stated as a constraint.

**OPEN-7 (not blocking, but it sizes a part).** R12 requires per-channel gain **and**
offset in the calibration EEPROM, plus ideally a bottom-decade LUT. Confirm the EEPROM is
sized for that (a 24C02 at 256 B is adequate for 4-5 channels with a 16-point LUT; a 24C32
gives headroom) before the part is fixed. This interacts with requirements.md question 10
- if no instrument exists to measure 6-8 fixtures, the offset coefficients cannot be
populated and the whole low-end matching argument falls back on binning alone.
