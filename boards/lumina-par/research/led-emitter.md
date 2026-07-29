# Research: LED emitter (light engine) - LUM-PAR-A

**Block:** the RGBW emitter(s) themselves. **Phase:** P1. **Date:** 2026-07-28.
**Source:** live JLCPCB/LCSC search via `scripts/parts_search.py` (network up, no cache
fallback used), plus manufacturer datasheets fetched and parsed. Every part below was
seen with today's stock and price. Companion data: `led-emitter.json`.

---

## 1. Verdict

**Integrated 4-in-1 RGBW wins, but for a different reason than the requirements doc
assumes, and the recommended sizing is 4 emitters run soft, not 2 run hard.**

**Top pick: XINGLIGHT XL-HD6070RGBW-A5 / XL-HD6070RGBCW-A5, `C53153006`, 1819 in stock,
$0.3341 @100 ($0.4422 @10).** 4 fully independent dies on one slug, 1 W/die, 350 mA/die,
140 deg, Vf R 1.8-2.4 V / G,B,W 2.8-3.4 V, flux @350 mA R 45-60 / G 80-100 / B 13-27 /
W 100-120 lm, white 6000-6500 K.

**Runner-up: XINGLIGHT XL-HD6070RGBC-A46L-BD, `C22434861`, 6461 in stock, $0.3147 @100** -
the RGB 3-in-1 from the same body, paired with a separate white discrete. 3.5x the stock
depth, a published Tj (125 C), and JLC classifies it as SMT-assemblable where the RGBW part
is flagged "Wave Soldering". You give up PAR-REQ-15 (white now fringes against RGB).

**Recommended sizing (af): 4 x C53153006 at ~175 mA/die** = 7.98 W typ / 8.82 W worst-case
Vf, ~588 lm/fixture cold, ~485 lm/fixture hot. That is 7 % more light than 2 packages at
350 mA for identical watts (less droop), halves the heat per thermal path, and gives four
spatially separated mixed-white sources instead of two - better for PAR-REQ-14/15.
It also **keeps the at upgrade alive with no respin**: the same 4 packages at 350 mA/die
draw 15.96 W typ, which lands inside the at emitter budget. That directly answers D-01's
"do not let any component pin the design to Type 1".

**Two findings that override the requirements doc's assumptions:**

1. **The 4-in-1 is the ONLY in-stock RGBW power emitter on the whole LCSC catalogue.** A
   full sweep of the RGBW category (318 parts, all pages) plus targeted sweeps for RGBWC /
   RGBCW / RGBWA / 3535RGBW / 5050RGBW / 7070 / 8080 returns exactly one part above 50 mA.
   Everything else is a 20 mA indicator or a WS2812-class addressable. There is no Cree,
   Lumileds, Everlight or Nichia 4-in-1 in stock; **every Cree XLamp XP-E/XP-E2/XM-L colour
   line on LCSC shows 0 stock**, and the OSRAM "RGBW-looking" part (KRTBAELPS1.32) turns out
   to be a 20 mA automotive RGB sidelooker, not a wash emitter. So this is a
   **single-source, single-vendor decision** with no pin-compatible alternate.
2. **Amber is not the thermal trap the requirements doc thinks it is - and red is worse than
   it thinks.** See sections 7 and 8.

---

## 2. Ranked table

Prices are the qty-100 break unless noted. Nothing here is JLC **Basic**; there is no Basic
part in any power-LED family, so "prefer Basic" is unachievable for this block and is not a
selection error. All are Extended.

### 2a. INTEGRATED (multi-die on one slug)

| # | MPN | LCSC | Package | Stock | $ @100 / @1 | Basic | Dies | Rationale |
|---|---|---|---|---|---|---|---|---|
| 1 | XL-HD6070RGBW-A5 (dsheet: RGBCW-A5) | C53153006 | 6070 round, dia 9.0 mm, 8 leads | 1819 | 0.3341 / 0.5503 | No | R+G+B+W, 1 W each | **Top pick.** Only in-stock RGBW 4-in-1. Solves PAR-REQ-15 by construction. Risks: no Rth, no Tj, Topr max +85 C, JLC "Wave Soldering" flag |
| 2 | XL-HD6070RGBC-A46L-BD | C22434861 | 8080/6070 round, dia 8.0 mm, 6 leads | 6461 | 0.3147 / 0.5294 | No | R+G+B, 1 W each | Runner-up topology. Tj 125 C published, JLC SMT-assemblable, 3.5x stock. Needs a separate white -> W/RGB fringing |

### 2b. DISCRETE - budget set (XINGLIGHT 6070, same body as above)

One package per colour. 3 W / 700 mA "-A4-BD" variants; 1 W / 350 mA "-A2-BD" siblings exist.

| # | MPN | LCSC | Colour | Stock | $ @100 / @1 | Flux @700 mA | Vf | Rationale |
|---|---|---|---|---|---|---|---|---|
| 3 | XL-HD6070SURC-A4-BD | C48586650 | Red 620-630 nm | 917 | ~0.2279 @150 / 0.3302 | 100-120 lm | 2.0-2.6 V | AlInGaP; the thermally fragile channel |
| 4 | XL-HD6070UGC-A4-BD | C48586649 | Green 515-530 nm | 845 | ~0.2137 @150 / 0.3096 | 180-250 lm | 2.8-3.4 V | InGaN, benign |
| 5 | XL-HD6070UBC-A4-BD | C48586653 | Blue 455-470 nm | 1763 | ~0.1995 @150 / 0.2889 | 45-60 lm | 2.8-3.4 V | InGaN, benign |
| 6 | XL-HD6070UWC-A4-BD | C48586656 | White 6000-6500 K, Ra 72 | 1790 | ~0.2065 @150 / 0.2960 | 220-300 lm | 2.8-3.4 V | Real white emitter (SYS-REQ-07) |
| 7 | XL-HD6070WWC-A4-BD | C48586655 | Warm white 2900-3100 K | 1738 | ~0.2003 @150 / 0.2897 | (not extracted) | 2.8-3.4 V | Warm alternative to #6 |

**Do NOT use the "-A2" (non-BD) 1 W parts C5349974 / C5349976: their Topr is -35 to +60 C,
below the 69 C at internal air and with zero margin at the 56 C af internal air.** Only the
"-BD" variants are rated -40 to +85 C. This trap is only visible in the LCSC description
string, not in the datasheet headline.

### 2c. DISCRETE - better ambient rating (XINGLIGHT 2525)

2.5 x 2.5 x 1.85 mm, 3 W, 1000 mA max, Tj 125 C, ESD 3 kV, **Topr -40 to +105 C** (best of
any XINGLIGHT candidate), 120 deg.

| # | MPN | LCSC | Colour | Stock | $ @1 | Flux @700 mA | Vf |
|---|---|---|---|---|---|---|---|
| 8 | XL-HD2525SURC-A4 | C49237857 | Red 615-625 nm | 2700 | 0.2799 | 80-110 lm | 1.8-2.4 V |
| 9 | XL-HD2525UGC-A4 | C49237859 | Green 515-530 nm | 1815 | 0.2836 | 160-225 lm | 2.6-3.4 V |
| 10 | XL-HD2525UBC-A4 | C49237860 | Blue 450-460 nm | 1896 | 0.1414 | 27-45 lm | 2.8-3.4 V |
| 11 | XL-HD2525UWC-A2 | C3646945 | White 5500-7500 K | 4530 | 0.1681 | (2 W / 350 mA part) | 3.4 V |

**Caveat that decides it: the 2525's thermal pad is ~1.0 x 2.0 mm (about 2 mm2), versus a
dia 6.2 mm slug (about 30 mm2) on the 6070.** Pushing 3 W through 2 mm2 is a heat flux of
~1.5 W/mm2; that is an aluminium-MCPCB part, full stop, and it will not work on 1.6 mm FR4.

### 2d. DISCRETE - premium (ams-OSRAM). The only parts with real published thermal data.

| # | MPN | LCSC | Colour | Stock | $ @1 | Key data |
|---|---|---|---|---|---|---|
| 12 | LJ CRBP.01-JZLX-27-3A4A-350-R18 | C17590353 | Red 625 nm | 689 | 1.7994 | **RthJS 8.9 K/W typ, 12.0 max**; Tj max 135 C; Topr -40..+125 C; IF 30-1000 mA; Vf 1.90/2.10/2.35 V; 61-130 lm @350 mA; ESD 8 kV HBM 3B with integral back-to-back ESD diode; isolated thermal pad |
| 13 | LB CRBP.01-HYKX-7B-Y474-350-R18 | C17351064 | Blue 472 nm | 170 | 1.2717 | 350 mA, Vf 2.65-2.85 V, 110 deg |
| 14 | LT CRBP.01-KZLZ-36-Q525-350-R18 | C17352925 | True green 528 nm | **19** | 1.4169 | **STOCK BLOCKER** - see below |
| 15 | GW PUSRA1.EM-N2N7-XX52-1-700-R33 | C17664282 | White 5700 K | 395 | 0.8796 | OSLON Pure 1515, 700 mA, Vf 2.8 V |

**The all-OSRAM set is not buildable today.** The only deep-stock OSRAM green (C17387904,
685 pcs) is 503 nm *cyan*, not green; the true 528 nm green has 19 pieces. 19 covers 8
fixtures but leaves no spares and no second build.

### 2e. FIFTH CHANNEL (amber) - see section 7

| # | MPN | LCSC | Type | Stock | $ @1 | Data |
|---|---|---|---|---|---|---|
| 16 | XL-HD2525UYC-A4 | C49237858 | **True AlInGaP amber 587-595 nm** | 2150 | 0.2499 | 3 W, 52-80 lm @700 mA, Vf 1.8-2.4 V, Tj 125 C, Topr -40..+105 C |
| 17 | XL-HD6070YWC-A4-BD | C48586652 | **Phosphor-converted "amber"** 1800-2000 K, Ra 70 | 830 | 0.2917 | 3 W / 700 mA, **Vf 2.8-3.4 V -> InGaN blue die + phosphor** |
| 18 | XL-HD6070YWC-A2-BD | C48586651 | PC amber, 1 W | 1513 | 0.2374 | 90-110 lm @350 mA |

### 2f. Reference point (not recommended)

| # | MPN | LCSC | Stock | $ @1 | Why it is here |
|---|---|---|---|---|---|
| 19 | XPGBWT-L1-0000-00H51 (Cree XP-G) | C17401863 | 1060 | 3.2437 | The only in-stock Cree emitter of any relevance - white only, ~10x the XINGLIGHT white. Every Cree/Wolfspeed **colour** line (XP-E, XP-E2, XM-L Color) shows 0 stock. Included so nobody re-runs this search |

---

## 3. Integrated vs discrete - the numbers behind the recommendation

Both options were costed and power-tabled at the same af envelope (7.6-8.5 W to the
emitters). Typ Vf, typ flux, Tj = 25 C.

| | **A: 4 x RGBW 4-in-1 @175 mA/die** | **B: 4 discrete 3 W 6070, one per colour @700 mA** |
|---|---|---|
| Emitter power, typ Vf | 7.98 W | 8.12 W |
| Emitter power, worst-case Vf | 8.82 W | 8.96 W |
| Flux, cold (Tj 25 C) | 588 lm | 637 lm |
| Flux, hot (Tj ~100 C, real derating) | ~485 lm | ~530 lm |
| Optical sources per fixture | 4, each already colour-mixed | 4, each a single colour |
| PAR-REQ-15 (no R/G/B/W fringing) | satisfied by construction | **requires a real diffuser to pass** |
| Heat per package | 1.5 W | 1.2-1.6 W |
| Thermal paths to solve | 4 identical | 4 identical |
| Independent per-die thermal management | no (shared slug) | yes |
| BOM cost per fixture (qty 8 build) | $1.55 | $1.22 |
| Per-colour binning | one transaction, one bin set | four transactions, four bin sets |

**Conclusion.** The discrete option is 9 % brighter and $0.33/board cheaper. Both are
noise. It is *not* thermally better here - because in the recommended arrangement the
integrated packages are run at half current, per-package heat is the same either way. And
it loses the one thing that matters: PAR-REQ-15 says visible R/G/B/W shadow fringing on a
wall is a **failure**, and four single-colour point sources 20-40 mm apart, 2.5 m from a
wall, will fringe unless a diffuser is specified, characterised, and bought - which
requirements Q8 says is probably out of this run's scope.

The requirements doc's stated advantages for discrete - "cheaper sourcing" and "independent
thermal management" - do not survive contact with the catalogue at this quantity. The
sourcing advantage is $0.33/board; the thermal advantage disappears once you run four
integrated packages instead of two.

**The one genuine discrete advantage is spectral freedom** (a 470-475 nm royal blue for
"neon blue", a 500-505 nm cyan for "mint", a true amber). The 4-in-1 fixes you at
R 620-630 / G 520-530 / B 457-465 / W 6000-6500 K. That is a competent saturated-colour
gamut and should reach purple, magenta, hot pink, cyan and steel blue; "mint" and
"neon blue" are the two PAR-REQ-05 targets most likely to disappoint, because both sit
between the green and blue primaries where a 3-primary mix desaturates.

**A hybrid is worth pricing:** 4 x RGBW 4-in-1 + 1 x discrete cyan/amber "spice" emitter.
The 4-in-1 carries the mixing burden, the fifth adds gamut where the primaries are thin.

---

## 4. Power tables (feed the P1 power table and the driver scout)

Per package, XL-HD6070RGBCW-A5, typ Vf 2.1 / 3.1 / 3.1 / 3.1 V, worst-case 2.4 / 3.4 x3.

| Drive | R | G | B | W | Package total (typ) | Package total (worst Vf) | Flux (cold) |
|---|---|---|---|---|---|---|---|
| 350 mA/die (max) | 0.735 W | 1.085 W | 1.085 W | 1.085 W | **3.99 W** | 4.41 W | 272 lm |
| 175 mA/die (af rec.) | 0.368 W | 0.543 W | 0.543 W | 0.543 W | **1.995 W** | 2.21 W | 147 lm |

| Configuration | Emitter power (typ) | Emitter power (worst Vf, all 4 ch at 100 %) | Against budget |
|---|---|---|---|
| 4 pkg @175 mA (af) | 7.98 W | 8.82 W | af emitter budget 7.6-8.5 W - **fits typ, 4 % over at worst Vf** |
| 4 pkg @350 mA (at) | 15.96 W | 17.64 W | at emitter budget 16.5-18.4 W - **fits** |
| 2 pkg @350 mA (af alt) | 7.98 W | 8.82 W | same watts, 7 % less light, 2x the heat per path |

**Hardware backstop (requirements s3.3).** The clamp is set by the driver's current-sense
resistors, not by firmware, so with every PWM stuck at 100 % the draw is bounded at the
worst-Vf row. At af that is 8.82 W of emitter + ~1.0 W driver loss + 0.4 W housekeeping =
~10.2 W. On +12V alone that is 0.85 A - **over the 0.75 A sustained rail ceiling, well under
the 2.0 A OCP**. So the fixture will not latch off, but the sustained ceiling is exceeded in
the stuck-PWM case. Two clean fixes exist: drop to ~150 mA/die, or take the LED load from
`+48V_SW`. Flagged for the architect, not decided here.

**String topology (this is load-bearing for the driver scout).** With 4 packages, each
colour channel drives 4 dies:

- Red 4S @175 mA: 8.4 V typ / 9.6 V max. Clean buck from +12V.
- **G / B / W 4S @175 mA: 12.4 V typ, 13.6 V max - above the +12V rail.** A 4S series
  string of the InGaN channels cannot be driven by a buck from 12 V. Either take LED power
  from `+48V_SW` (buck), or use 2S2P (6.2-6.8 V @350 mA, buck from 12 V, but parallel
  strings need Vf matching or per-string ballast).
- Max channel current in any sane arrangement: 700 mA (4P). **The requirements s8
  conditional >3 A flag is NOT triggered by any candidate emitter here.**

---

## 5. Is ~8 W of LED enough light for a 5 x 7 m room?

Room: 5 x 7 m floor (35 m2) + 24 m perimeter x 2.5 m walls (60 m2) = **95 m2 of lit
surface**. 8 fixtures. Hot flux from section 3 (Tj ~100 C, real AlInGaP derating).

| Case | lm / fixture | lm total (8 fix) | Direct average illuminance |
|---|---|---|---|
| af, all 4 channels full | ~485 | ~3,880 | **~41 lx** |
| at, all 4 channels full | ~899 | ~7,190 | **~76 lx** |
| af, saturated green only | ~176 | ~1,410 | ~15 lx |
| af, saturated red only | ~62 | ~493 | ~5 lx |
| af, saturated blue only | ~40 | ~317 | ~3 lx |

Add roughly 1.5-2x for inter-reflection at typical wall reflectance.

**Honest answer: at the af operating point this is a dark-room instrument, not room
lighting.** ~41 lx direct is bar/restaurant-mood level (a lit living room is 100-200 lx).
For the stated use - a music-driven light show in a basement/garage with the lights off -
it will read well, and deep saturated colour will look strong because the photopic lumen
figures badly understate how blue and red *appear* in the dark. With daylight or normal
room lighting on, the wash will be barely visible.

**This is a direct argument for keeping the at path open**, which the 4-package sizing does
for free. If the lighting-design answer to requirements Q2 is "9 W reads as underwhelming",
the recommended arrangement upgrades by changing a current-sense resistor value, not by a
respin - provided the thermal design in section 6 is built for it, which is the hard part.

---

## 6. Thermal - the section that decides the architecture

**No XINGLIGHT datasheet in this whole family publishes a thermal resistance. The 4-in-1
does not even publish a maximum junction temperature.** That is the single biggest data gap
in this block, and it is not recoverable by measurement before P5.

What IS published:

| Part | Tj max | Topr | Slug / pad area |
|---|---|---|---|
| XL-HD6070RGBCW-A5 (4-in-1) | **not stated** | -40 to +85 C | dia 6.2 mm (~30 mm2) |
| XL-HD6070RGBC-A46L-BD (3-in-1) | 125 C | -40 to +85 C | dia 6.0 mm (~28 mm2) |
| XL-HD6070 single-colour -BD | 120 C | -40 to +85 C | dia 6.0 mm |
| XL-HD2525 single-colour | 125 C | -40 to +105 C | ~2 mm2 |
| ams-OSRAM LJ CRBP.01 | 135 C (175 short) | -40 to +125 C | **RthJS 8.9 typ / 12.0 max K/W** |

**Reverse thermal budget.** Target red Tj <= 100 C (colour and lifetime stability). LEDs
convert 20-35 % of input to light, so use 75 % to heat.

| Case | Heat / package | Tj target - internal air | Allowed Rth (junction -> internal air) |
|---|---|---|---|
| af, 4 pkg @175 mA | 1.50 W | 100 - 56 = 44 K | **29 K/W per package** |
| at, 4 pkg @350 mA | 3.00 W | 100 - 69 = 31 K | **10.3 K/W per package** |

**What the path actually costs.** Calculated for a dia 6.2 mm slug on 1.6 mm FR4 with a
30-via farm (dia 0.3 mm, 25 um barrel copper): each via is L/(k.A) = 1.6 mm / (385 W/mK x
0.0255 mm2) = 163 K/W, so 30 in parallel = **5.4 K/W**; the FR4 in parallel contributes
nothing (190 K/W). In-plane spreading into a 1 oz copper pour on FR4 is typically another
10-25 K/W for a pour of this size. Package Rth(j-s) is unpublished; the closest data point
with real numbers (OSLON Signal, one small die) is 8.9-12 K/W, and four dies sharing one
slug plausibly sits at 10-20 K/W per die - **an assumption, not data**.

| Path | af, on 1.6 mm FR4 | af, on aluminium MCPCB |
|---|---|---|
| Package j->solder (assumed) | ~12 K/W | ~12 K/W |
| Solder -> other side of substrate | 5.4 K/W (via farm) | ~1.5 K/W (2 mm Al, 100 um dielectric) |
| In-plane spreading | 10-25 K/W | ~0 (substrate is the spreader) |
| Interface to heatsink | ~2 K/W | ~1 K/W |
| Heatsink -> internal air (vented) | 4-8 K/W | 4-8 K/W |
| **Total** | **33-52 K/W** | **19-23 K/W** |
| **vs 29 K/W af budget** | **does NOT close** | **closes** |
| **vs 10.3 K/W at budget** | does not close | **does NOT close** |

**Consequences, stated plainly:**

1. **These emitters effectively require an aluminium MCPCB.** On 1.6 mm FR4, even with an
   aggressive via farm, the af case does not close and the at case is not remotely close.
   This board is FR4 and the enclosure is plastic, so that is an architecture-level result:
   it pushes requirements Q5 to **(b) off-board LED module on its own MCPCB/heatsink with an
   internal harness**, and Q7 to **(b) heatsink shrouded behind a plastic guard**.
2. **A sealed enclosure (Q6a) does not close at all.** The 4-8 K/W heatsink-to-air term
   above already assumes vents. Sealed, that term is 15-25 K/W for an internal sink and
   nothing closes.
3. **The at case does not close at 4 packages even on MCPCB.** To keep the at upgrade real
   you need either ~8 packages at 175 mA each (heat per path back to 1.5 W), or a
   substantially better heat path, or a relaxed red Tj target (which costs PAR-REQ-06).
   Worth deciding now, because package count is a layout decision.
4. **Topr max +85 C on the 6070 family is uncomfortably close to the 69 C at internal air.**
   The 2525 family (+105 C) and OSLON (+125 C) are better on this axis. If the at path is
   taken seriously, the 6070 family is a poor bet on ambient rating alone.
5. **Do not design to XINGLIGHT's temperature-derating curve.** The "Temperature vs Relative
   Luminous Flux" chart, which shows only about -0.08 %/K, is **byte-identical (verified by
   MD5) across the red, green, blue and amber datasheets**. It is boilerplate and carries no
   colour-specific information. For a 620-630 nm AlInGaP red, -0.08 %/K contradicts the
   physics by an order of magnitude.

---

## 7. Red (and amber) temperature behaviour - the real PAR-REQ-06 threat

Using published behaviour for the die chemistries involved, since the vendor curves are
boilerplate:

| Channel | Chemistry | Flux vs Tj | Dominant wavelength vs Tj | Over a 75 K rise |
|---|---|---|---|---|
| Red 620-630 nm | AlInGaP | -0.5 to -0.9 %/K | +0.03 to +0.09 nm/K | flux -40 to -55 %, lambda +2 to +7 nm |
| Amber 587-595 nm | AlInGaP | **-0.5 to -1.4 %/K** | +0.03 to +0.09 nm/K | flux -40 to -70 % |
| Green / Blue | InGaN | -0.05 to -0.15 %/K | < +0.01 nm/K | flux -5 to -11 %, negligible shift |
| White | InGaN + phosphor | -0.1 to -0.2 %/K | CCT drift, small | flux -8 to -15 % |

**The consequence is bigger than fixture-to-fixture tint.** Between a cold start and steady
state, the red/GBW ratio inside a *single* fixture changes by roughly 2x. A fixed per-fixture
scalar in the calibration EEPROM (PAR-REQ-17) cannot correct that - **the correction has to
be a function of measured temperature.** Two design consequences for the architect:

- The PAR-REQ-12 thermistor is promoted from "over-temperature protection" to
  "colour-correction sensor". It must sit next to the emitter (on the MCPCB, if the module
  goes off-board), not next to the drivers, and its accuracy and ADC resolution now matter.
  If the LED module is off-board, **the thermistor must go on the module and its two wires
  must be in the harness** - that changes the harness conductor count in requirements Q5.
- PAR-REQ-06 fixture-to-fixture consistency now depends on the 6-8 fixtures reaching
  similar steady-state temperatures. One fixture in a still corner and one in an air path
  will not match unless the correction is temperature-referenced.

---

## 8. The fifth (amber) channel - the requirements doc's caveat is wrong for one option

Requirements Q4 warns that amber AlInGaP loses -0.5 to -1 %/K "roughly twice as badly as
the InGaN channels" and will drift visibly. Two in-stock options split that concern:

**Option A - true saturated amber: XL-HD2525UYC-A4, `C49237858`, 587-595 nm AlInGaP,
2150 stock, $0.2499.** Vf 1.8-2.4 V confirms direct AlInGaP emission. This IS the worst die
in the document thermally: at 590 nm AlInGaP is closer to the direct/indirect bandgap
crossover than 625 nm red, so it is *more* temperature-sensitive than the red channel, not
merely comparable. No derating data published. If chosen, it needs the same
temperature-referenced correction as red, and it will be the first channel to visibly drift.

**Option B - phosphor-converted "amber": XL-HD6070YWC-A4-BD, `C48586652`, 1800-2000 K,
Ra 70, 830 stock, $0.2917.** **Vf 2.8-3.4 V plus a stated CCT and CRI means this is an InGaN
blue die under a phosphor, not AlInGaP.** It therefore does *not* carry the -0.5 to -1 %/K
penalty at all - it behaves like the white channel (-0.1 to -0.2 %/K). The requirements
doc's thermal objection simply does not apply to it. The trade is colour: 1800-2000 K reads
as candle/gold, not as a saturated amber-orange, and Ra 70 means it is a broad, desaturated
source. For "P3 French melodic leans on gold/amber", gold is arguably exactly what is
wanted; for a saturated amber accent it is not.

**Power price of a fifth channel at af.** One 2525 amber at 350 mA (Vf ~2.1 typ) = 0.74 W,
which is **9 % of the 7.98 W emitter budget**. One per package (4 amber emitters) would be
2.9 W = 36 %, which is not affordable at af. Recommendation to the architect: if amber is
wanted, fit **one** amber emitter per fixture as a spice channel, not one per package, and
budget the firmware temperature-compensation term.

---

## 9. Binning (PAR-REQ-16) - what LCSC/JLC actually publishes

Being blunt, because this is the requirement most likely to be quietly failed.

| Vendor | Bins defined in datasheet? | Bin selectable in the orderable MPN? |
|---|---|---|
| XINGLIGHT (all candidates) | **Yes, fully.** Brightness in lm (codes H8, H9, J1, J2, J6, J7, K1-K4), forward voltage (N12-7 ... N13-5), dominant wavelength (HB03/HB04 blue, HG03/HG04 green, HR02/HR03 red) | **No.** The LCSC/JLC MPN carries no bin suffix. You receive whatever is on the reel |
| ams-OSRAM (OSLON, KRTB) | Yes | **Yes - the bin groups are IN the order code.** Verified against the KRTB AELPS1.32 datasheet's Ordering Information and the LJ CRBP.01 ordering code. The LCSC MPN `LJ CRBP.01-JZLX-27-3A4A-350-R18` encodes brightness groups JZ..LX, wavelength group 27, Vf groups 3A/4A |

**So PAR-REQ-16 is literally satisfiable only with the OSRAM parts, and even there the
specified group is wide**: JZ..LX spans 61-130 lm, a 2.1:1 flux ratio. That is not tight
enough on its own to satisfy PAR-REQ-06 either.

**Practical recommendation (matches requirements Q11 option c):**
1. Buy all 8 fixtures' emitters in **one LCSC transaction**, so they come from one reel and
   one production lot. Same-reel matching is empirically far tighter than the datasheet bin
   width and is the only lever available with XINGLIGHT.
2. Fit the calibration EEPROM regardless, and make the stored correction
   **temperature-dependent** (section 7), not a fixed scalar.
3. Record the reel/lot code on the build sheet, so a later fixture can be matched or
   knowingly recalibrated.

---

## 10. Assembly and mounting

- **Package (top pick):** dia 9.0 mm round body, 5.15 mm tall (2.4 mm dome), 8 gull-wing
  leads with a 14.5 mm span, 0.25 mm lead thickness, central dia 6.2 mm thermal slug.
  Recommended soldering pattern: dia 6.0 mm centre pad + 8 x 2.5 x 1.0 mm wing pads.
  Reflow <= 220 C / 6 s, MSL 3.
- **On-board-mountable?** Physically yes, thermally no on FR4 (section 6). Treat as an
  **off-board module on an MCPCB**.
- **JLC PCBA flag to resolve at P3:** JLCPCB lists `C53153006` assembly type as **"Wave
  Soldering"**, while the RGB 3-in-1 `C22434861` from the same body is **"SMT Assembly"
  with Assembly Difficulty: High**. For a gull-wing SMD emitter that reads like a JLC
  data-entry error, but it is what governs the order. If it is real, the RGBW part cannot be
  SMT-placed and must be hand-soldered - which the requirements doc's Q13 recommendation
  already assumes for emitters anyway.
- **Height:** 5.15 mm above its own substrate, plus MCPCB and any optic. Feeds requirements
  s5.5 (total height above this board is currently unknown).
- **Beam:** 140 deg (2 x theta-1/2) for the 6070 family, 120 deg for 2525 and OSLON. The
  published spatial radiation curve is a broadened Lambertian with ~50 % relative intensity
  still present at +/-70 deg. From a 2.5 m ceiling a 140 deg emitter floods a ~13 m diameter
  patch at floor level, so PAR-REQ-14's overlapping wash is comfortably met **without** a
  secondary lens - but a diffuser is still needed for PAR-REQ-15 if the discrete option is
  chosen.
- **ESD:** XINGLIGHT 4-in-1 and 3-in-1 are **2000 V** (HBM Class 2); the single-colour
  6070/2525 parts are **3000 V HBM**. All are handleable with normal JLC ESD control and
  need no on-board TVS for operation. The OSLON parts are 8 kV HBM Class 3B **with an
  integral back-to-back ESD diode**, which also gives them reverse-voltage tolerance the
  XINGLIGHT parts lack (VR 5 V max, and a reverse-connected die is destroyed).
  **If the module goes off-board on a harness, add a per-channel clamp**: an unmated
  connector puts a switching CC driver into open-circuit and its compliance voltage lands on
  the emitter when the connector re-mates. That is a driver-scout item, flagged here.

---

## 11. What is verified vs what is assumed

| Claim | Status |
|---|---|
| Stock, price breaks, package, brand, LCSC/JLC type for all 19 parts | **Verified live today** via `parts_search.py` |
| Vf, flux, wavelength, Tj, Topr, ESD, package outline, bin tables | **Verified** - datasheets downloaded and parsed (`wmsc.lcsc.com` / `datasheet.lcsc.com` mirrors; the `www.lcsc.com/datasheet/` URLs returned HTML, not PDF) |
| C53153006 is a genuine 4-in-1 RGBW | **Verified** - LCSC exposes no datasheet for it via the API; the PDF was recovered from the product page and is titled XL-HD6070RGBCW-A5 with a 4-die (8-lead) outline |
| "Only in-stock RGBW power emitter on LCSC" | **Verified** - full-catalogue sweep of RGBW (318 parts) plus 10 targeted sweeps |
| OSRAM bin groups are in the order code | **Verified** against the KRTB AELPS1.32 datasheet Ordering Information section |
| XINGLIGHT derating curve is boilerplate | **Verified** - MD5-identical image across red/green/blue/amber datasheets |
| Package Rth(j-s) for XINGLIGHT parts | **NOT PUBLISHED.** The ~12 K/W used in section 6 is an assumption extrapolated from OSLON's 8.9-12 K/W |
| Red/amber %/K derating figures | **Assumed** from AlInGaP/InGaN chemistry, not from these datasheets |
| Heat fraction 75 % | **Assumed** (requirements s4 says 20-35 % to light) |
| Illuminance estimates in section 5 | **Calculated** from verified flux, with assumed thermal derating |

---

## 12. Risks

1. **Single source, no alternate.** One vendor, one MPN, no pin-compatible second source
   anywhere on LCSC. If XINGLIGHT delists C53153006 the design falls back to the RGB 3-in-1
   plus a discrete white, which costs PAR-REQ-15. **Buy all 8 fixtures' emitters in one
   order, plus spares, before P5.**
2. **No published Rth and no published Tj on the top pick.** The whole thermal argument in
   section 6 rests on an assumed 12 K/W. If the real figure is 20 K/W, even the MCPCB path
   is marginal at af.
3. **Topr max +85 C vs 69 C at internal air.** 16 K of margin, on a part whose junction
   limit is unstated.
4. **JLC "Wave Soldering" flag** on the top pick (section 10).
5. **Bin not orderable** from XINGLIGHT (section 9). PAR-REQ-16 cannot be met literally
   without switching to OSRAM, and the OSRAM set has a green stock blocker.
6. **The at upgrade does not close thermally at 4 packages** even on MCPCB. Deciding
   package count for at now avoids a respin later.
7. **Vendor data quality is low.** Boilerplate derating curves, a flux table mislabelled
   "mcd" where the bin table says "LM", an absolute-maximum table whose IF/IFP row labels are
   transposed (R shown as 50 mA where 500 mA is clearly meant). Treat every XINGLIGHT number
   as approximate and design margin in.

---

## 13. Files

- `research/led-emitter.md` (this file)
- `research/led-emitter.json` - 19 candidates as `parts_search` result objects with
  `lcsc` / `mpn` / `basic` / `stock` / `price` / `price_breaks` / `datasheet` intact, plus
  added `rank`, `role` and `scout_notes` fields for P3.
