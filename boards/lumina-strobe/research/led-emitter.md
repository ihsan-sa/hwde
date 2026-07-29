# research: led-emitter - LUM-DTR-STROBE-A

White light engine for the strobe daughter. Ranked candidates verified live against JLCPCB
today (2026-07-28) via `parts_search.py`. Every stock/price figure below came off that live
search; nothing here is from memory.

Operating point this block is being sized to (given as CLOSED, not re-opened):
**2.6 A peak, string Vf <= 38 V at 2.6 A, ~99 W peak, ~7-8 W sustained (af), 5-200 ms
flashes at 1-25 Hz, 56 C (af) / 69 C (at) internal air.**

---

## 1. The reality check first, because it changes the answer

I swept 33 queries across every package family, brand and category that could hold a white
power emitter (3535 / 5050 / 3030 / 2835 / 6070 / 7070 / COB, plus Cree, Lumileds, Nichia,
Osram, Samsung, Seoul, Bridgelux, Everlight, Honglitronic, Xinglight, NationStar, JNJ,
Luminus, Epistar). 169 distinct in-stock white SKUs came back. Four findings, all checkable:

| Finding | Evidence |
|---|---|
| **No JLC Basic white LED exists above indicator class.** | `--basic-only` over every white query returns exactly 6 parts, all 5-25 mA 0603/0805 indicators (best: KT-0805W, C34499, 25 mA). Every candidate below is **Extended**. |
| **The highest continuous current rating in stock is 1500 mA.** | Only 7 in-stock white SKUs are rated >= 700 mA; only 3 reach 1000 mA+. Nothing is rated for 2.6 A. |
| **A 50-100 W white COB is not a JLCPCB part.** | The entire "Chip On Board (COB) Light Sources" white population in stock is **three SKUs**: CXA1507 (C510527, 36 V / 375 mA / 938 lm, **stock 5**), BXKE-30G0801 (C358080, 36 V / 100 mA / 3.6 W, **stock 7**, 3000 K warm - fails STR-REQ-14), BXKE-27G0801 (C358079, stock 5). All are 3.6-13.5 W class, i.e. one seventh of the operating point, and none can be bought in quantity. |
| **JLC stocks no LED optics of any kind.** | "Carclo" -> 55 hits, 0 in stock. "Ledil" -> 0 in stock. "LED reflector" -> 0 results. The only optic-adjacent parts are LED isolation columns/spacers. Optics are a **mechanical BOM line**, not a JLC line. |

### 1.1 STR-REQ-13: the pulsed derating curve, per candidate, verified

This is the most important result in this document. **Every published white-LED pulse rating
in this market is specified at roughly 100 us pulse width and 10 % duty. This board's flashes
are 5-200 ms - 50x to 2000x longer. Thermally, a 10 ms flash is DC.** No vendor pulse
allowance covers the operating point.

| Candidate | Pulsed rating published? | Exact wording / condition |
|---|---|---|
| Cree XP-G2 `XPGBWT-L1-0000-00H51` (C17401863) | **No.** | The string "pulse" appears **zero times** in all 44 pages of the datasheet LCSC ships for this SKU (CLD-DS51 REV 22). Only `DC forward current - Standard = 1500 mA`. |
| JNJ `JNJ-LTJW0115T140` (C19185883) | **Yes, but not at our pulse width.** | `Max Pulse Current IFP = 3000 mA`, footnote: `*Pulse condition: pulse width (tp) = 100 us, duty cycle = 10 %`. Also `Max Continuous Working Current IF = 1500 mA`, `Tj = 115 C` (low). |
| Xinglight `XL-HD3535UWC-A2` (C3646951) | **Yes, but not at our pulse width.** | `Peak Forward Current 700 mA`, footnote: `Pulse width <= 0.1 ms, Duty <= 1/10`. DC forward current 350 mA, abs max power 1000 mW, Tj 145 C. (Its datasheet literally lists "camera flash / strobe for mobile devices" as the application.) |
| Lumileds `L150-4080500600000` (C17242738) | **Not assessable.** | LCSC attaches **no datasheet** to this SKU. Lumileds DS174 must be pulled from the vendor before P3. |
| Honglitronic `EMC-5050D90W-...` (C49435773) | **Not assessable.** | No datasheet attached at LCSC, and no per-part datasheet found on the vendor site. |
| TONYU `DYWH-S353522-WD-FC-T700-1T` (C52125193) | **Not assessable.** | No datasheet attached at LCSC. |

Cree's own application note **CLD-AP60 REV 4A, "Pulsed Over-Current Driving of LEDs"**,
declines to publish a pulsed limit at all. It says over-driving "may adversely affect
efficiency, chromaticity and long-term reliability", that customers must run their own
lifetime testing, and (footnote 2) that "operating XLamp LEDs outside the published
specifications negates the warranty". The widely-quoted rule of thumb from older revisions
(100 % / 200 % / 300 % of rated current at >50 % / 10-50 % / <10 % duty) **was tested at
1 kHz, i.e. ~1 ms pulses** and has been removed from the current revision. It does not
transfer to 5-200 ms.

**Design rule that follows, and it is the single most useful output of this block:**
size the string so that **peak current stays inside each die's DC maximum**, and budget
**zero** extra headroom for "it's only pulsed". That forces parallel sub-strings, which is
a message for the drive-stage design: parallel strings need per-string ballast resistors or
Vf-matched binning, or one string hogs the current.

---

## 2. Ranked candidates

Prices are the qty-6-build price break (i.e. the break covering pcs/board x 6). Basic/Extended:
**all Extended**, no Basic option exists.

| # | MPN | LCSC | Pkg | DC max | CCT | Stock | Price @ break | Rationale |
|---|---|---|---|---|---|---|---|---|
| 1 | **XPGBWT-L1-0000-00H51** | C17401863 | 3535 | **1500 mA** | 6200 K cool | 1060 | $2.2125 @100 | Only candidate with an engineering-grade datasheet: Vf table at 350/700/1000/1500 mA at Tj=85 C, **Rth j-sp 1.4 C/W**, Tj max 150 C, relative-flux-vs-current and delta-CCx/CCy-vs-current curves. That is precisely what STR-REQ-13/14/15 need. Expensive. |
| 2 | **JNJ-LTJW0115T140/63MIL/5500-6500K** | C19185883 | 3535 | **1500 mA** | 5500-6500 K | 2764 | $0.3486 @100 | Same 1500 mA DC max at **1/6 the price**, deepest stock of any 1.5 A white part, publishes an explicit (if inapplicable) pulse spec. Costs: **Tj max only 115 C**, no Rth, no flux-vs-current or chromaticity-vs-current data. |
| 3 | JNJ-LTJW0115W120/63MIL/6500-7000K | C19185884 | 3535 | 1500 mA | 6000-7000 K | 2481 | $0.3131 @100 | The only near-pin-compatible alternate to #2 (different CCT bin, same package and ratings). Listed to answer the single-source question. |
| 4 | XL-HD6070UWC-A4-BD | C48586656 | 6070 | 700 mA / 3 W | 6000-6500 K | 1790 | $0.2065 @150 | Cheapest per watt, big emitting area (good for glare), but 700 mA means 48 dies for 2.6 A. |
| 5 | XL-HD3535UWC-A2 | C3646951 | 3535 | 350 mA / 1 W | 5500-7500 K | **22438** | $0.2248 @150 | Deepest stock of any real white power LED at JLC and the only one whose datasheet targets strobe use - but 350 mA DC max needs ~88 dies. Impractical; listed as the fallback if 1.5 A parts vanish. |
| 6 | L150-4080500600000 (LUXEON 5050) | C17242738 | 5.2x5 mm | ~640 mA nom | 4000 K neutral | 390 | $0.8102 @100 | 6 V-class (2 dies in series) so 6 in series = 36.6 V - the tidiest string topology on offer. Rth 2.4 C/W (distributor data). Blocked by **no datasheet at LCSC** and thin stock. |
| 7 | EMC-5050D90W-B4C2-S1-...(4750-5300K) | C49435773 | 5050 | 850 mA / 5.1 W | 4750-5300 K | 1000 | $0.1351 @150 | 6 V-class (Vf 5.8-6.8 V), cheapest per watt of all, decent stock. Blocked by **no datasheet**, and the "Frosted Yellow Lens" phosphor cap is a colour-cast risk under STR-REQ-14. |
| 8 | DYWH-S353522-WD-FC-T700-1T | C52125193 | 3535 | 700 mA / 2.2 W | white (unbinned) | 980 | $0.1789 @150 | Shows the depth of the 700 mA tier. Fails STR-REQ-13 on documentation alone. |
| 9 | CXA1507-0000-000N0HG440G | C510527 | COB 15.9 mm | 375 mA @ 36 V | 4000 K, CRI 93 | **5** | $5.05 | The **only true white COB in stock at JLC**. 938 lm, ~13.5 W class. Stock of 5 cannot supply a 4-6 board build with spares. Evidence, not a candidate. |
| 10 | BXKE-30G0801-A-23 | C358080 | COB 12.5 mm | 100 mA @ 36 V | 3000 K warm | **7** | $1.02 | Warm white fails STR-REQ-14 outright; 3.6 W and stock 7. Evidence, not a candidate. |
| 11 | B2P-VH(LF)(SN) | C160315 | JST VH 3.96 THT | 10 A / 250 V | - | 121391 | $0.0631 | The 2-pin internal wire-to-board interface for the off-board arrangement. See section 4. |

**Top pick: #1 Cree XP-G2 (C17401863).** Not because it is cheap - it is not - but because it
is the only part on JLC that lets P3 and P8 *prove* STR-REQ-13, -14 and -15 from paper.
**Runner-up: #2 JNJ (C19185883)** if the $46/board difference matters more than the data.

---

## 3. String arithmetic - both arrangements

Rule from section 1.1: every die stays inside its DC maximum, so 2.6 A is split across
parallel sub-strings.

| Candidate | Per-die current | Vf/die at that current | Series x parallel | Total dies | String V @ 2.6 A | Peak power | Headroom at the 40 V floor | LED $/board @ qty 6 |
|---|---|---|---|---|---|---|---|---|
| **XP-G2 (C17401863)** | 1.30 A | **2.94 V** (interpolated from the datasheet's 2.90 V @1.0 A / 3.02 V @1.5 A, Tj=85 C) | **12 x 2** | 24 | **35.3 V** | 91.8 W | **4.7 V** (need 1.5 V) | **~$53.10** |
| JNJ (C19185883) | 1.30 A | ~3.5 V (est., spec spread 3.0-3.8 V, no per-current table) | 10 x 2 | 20 | ~35.0 V | 91 W | ~5.0 V | ~$6.97 |
| XL-HD6070 (C48586656) | 0.65 A | ~3.1 V (spec 2.8-3.4 V) | 11 x 4 | 44 | ~34.1 V | 89 W | ~5.9 V | ~$9.09 |

13 x XP-G2 in series would be 38.2 V and breaks the <= 38 V limit, so **12 is the number**.
Stock covers it comfortably: 1060 in stock vs 144 needed for six boards.

If the architect instead accepts vendor-unwarranted over-drive - 11 x XP-G2 in a single
series string at the full 2.6 A, ~3.35 V/die, 36.9 V, 96 W, **~$27.44/board** (66 pcs for six
boards falls on the qty-30 break, $2.4949) - that is 173 %
of the DC maximum with no vendor data at this pulse width and an explicit warranty
disclaimer. It halves the LED cost and the part count. **That is a judgement call for the
human, not for this scout.** My recommendation is the 12 x 2 arrangement.

---

## 4. (a) on this PCB, or (b) off-board? - verdict and why

**Verdict: off-board, but NOT as a bought COB. Put the emitter array on its own small
aluminium MCPCB, bolt that to a heatsink, and wire it back to this board with two wires.**

### (a) Series string of discretes on LUM-DTR-STROBE-A - reject

- **Thermal.** ~8 W sustained into 1.6 mm FR4 with no airflow, in a sealed plastic box at
  56 C (af) / 69 C (at). Even with a dense thermal-via farm the FR4-to-still-air path for a
  patch of this size is on the order of 15-25 C/W, so 8 W is 120-200 C of rise. It does not
  close, and STR-REQ-15 demands both the sustained and the peak case pass.
- **Area.** The 100 x 80 mm outline already loses the 30 x 26 mm RJ45 notch (780 mm2), the
  34 x 22 mm DC-DC hot zone (no LED drivers, no aluminium electrolytics), the 12 x 30 mm
  all-layer-copper-free antenna column, and a 22 x 20 mm recovery-header keepout - and the
  2800 uF / 100 V bank has to fit in what is left. 20-24 emitters plus a bolted heatsink do
  not.
- One thing (a) is not: an electrical problem. 12 x 2 fits the bank window fine.

### (b) Off-board module on its own heatsink - accept, with a correction

The requirements' recommendation ("off-board module") is right, but **the off-the-shelf COB
version of it is not purchasable**: JLC has three white COB SKUs totalling 17 pieces, all
under 13.5 W. A 50-100 W COB (typically 30-36 V at 2-3 A, which lands beautifully on the
bank window) is a general-market / AliExpress item, not an LCSC line, and it would arrive
with no pulsed data and no binning guarantee - failing STR-REQ-13 and STR-REQ-14 on paper.

So the workable form of (b) is **(b') an emitter array on a 1-layer aluminium MCPCB**
(JLCPCB does aluminium PCB as a separate cheap order), bolted to a heatsink, wired to
LUM-DTR-STROBE-A. This keeps every emitter an LCSC part with real data, moves 8 W onto
metal, and leaves this PCB with nothing but a 2-pin interface.

**Cost in connector terms** (permitted: internal wire-to-board is allowed, only
enclosure-piercing connectors are banned):

- **JST VH 2-pin THT header, `B2P-VH(LF)(SN)`, C160315, 10 A / 250 V, $0.0631, stock 121391.**
  2.6 A peak and ~0.25 A average is a ~4x derate; the 250 V rating makes the 0.60 mm 48 V
  clearance rule trivial to meet. Mating half is a VHR-2N housing plus SVH-21T-P1.1 crimps -
  loose hardware, not JLC-assembled.
- **Caveat:** it is a THT part, so it lands in the same assembly-process question as the two
  board-to-board sockets (requirements open question 6). If the answer there is
  "top-side SMD at JLC + hand-finish", this connector is free of consequence. If the board
  must be SMD-only, substitute solder pads sized for 18 AWG, which costs $0.
- Total interface cost either way: **under $0.10/board**, plus two wires. This is not a
  reason to prefer (a).

---

## 5. Efficacy and what 8.5 W actually looks like in that room

XP-G2 cool white, 24 dies at 1.3 A each (values marked *est.* are read off the datasheet's
relative-flux curve, which stops at 1500 mA - they are not table values):

| Point | Per die | Whole engine |
|---|---|---|
| Reference, 350 mA, Tj 85 C | ~139 lm at 0.95 W -> ~146 lm/W | - |
| **Peak flash, 1.30 A/die** | ~415 lm *est.* at 3.82 W -> **~109 lm/W** | **~10,000 lm at 91.8 W** |
| Sustained average, 8 W electrical, ~9 % duty (0.99 J flash at 8.6 Hz) | - | **~930 lm time-averaged** |
| Same 8 W run as DC instead of pulsed | ~115 mA/die -> ~55 lm | ~1,320 lm |

That last row is worth reading twice: **pulsing costs about 30 % of the lumens you would get
from the same average watts run continuously** (efficacy droop). It is the price of the hard
optical edge STR-REQ-11 wants, and it is a lever the firmware governor could use for
STR-REQ-07's graceful degradation - stretching the pulse rather than dropping it recovers
efficacy as well as avoiding a missed beat.

**Illuminance, to judge whether it reads as a strobe.** Treating the array as Lambertian,
I0 = 10,000/pi = ~3180 cd. Fixture at ~2.3 m above the floor:

- **Peak, directly beneath one fixture: ~600 lux.** With 4-6 fixtures spread over the room, a
  floor point sees roughly 1,000-1,500 lux at the instant of a synchronised flash.
- **Time-averaged: ~56 lux per fixture beneath, ~150-250 lux room-average with 5 fixtures.**

Against a dark party room at 1-20 lux ambient, the flash is 50-1000x ambient. It is
unmistakably a strobe. The honest framing for the human: **the peak is genuinely violent; the
time-average is dim room lighting.** That is exactly what an 8.5 W-fed strobe should be, and
it is the answer to "does 8.5 W read as a real strobe in that room" - yes, at 10 ms; no, if
someone expects a 150 ms flash to be equally blinding (requirements open question 2 already
says as much).

---

## 6. Optic and beam angle (STR-REQ-16)

Room 5 x 7 m, **2.5 m ceiling**, fixture ~2.3 m above the floor.

- **A bare XP-G2 is 120 deg FWHM** (datasheet, Standard variant; the HE variant is 125 deg).
  Half-intensity radius at 2.3 m = 2.3 x tan(60 deg) = **4.0 m**, i.e. an ~8 m diameter pool -
  wider than the room's short dimension and comparable to its long one.
- **Therefore the right optic is no optic.** Every off-the-shelf TIR lens for a 3535 emitter
  narrows this to roughly 10-45 deg, which at 2.3 m is a 0.4-1.9 m spot: exactly the failure
  mode STR-REQ-16 warns about ("a narrow beam lights one square metre of floor and fails the
  room regardless of its lumen figure").
- If more punch is wanted later, the correct class is a **wide/frosted TIR or a shallow
  reflector in the 60-90 deg band**. Carclo publishes a standard optic + holder range
  explicitly for the Cree XP-G family (single, 3-up and 4-up), and Ledil has equivalents.
  These are the reason to prefer an XP-G-footprint emitter over an unbranded 3535: the optic
  ecosystem only exists for the branded footprints.
- **Availability: LCSC/JLC stock zero optics** (verified: "Carclo" 55 hits / 0 in stock;
  "Ledil" 0 in stock; "LED reflector" 0 results). Optics are a **mechanical BOM line**,
  sourced from Carclo/Ledil through Mouser/DigiKey, roughly $1-3 per lens plus holder.
- **Practical recommendation:** no optic on the emitters; use a flat diffuser or a clear
  window in the enclosure. A 24-die array is already an extended source, it mixes well, and a
  diffuser also takes the edge off the point-source glare hazard of a 10,000 lm flash at eye
  level.

---

## 7. Thermal (STR-REQ-15)

Both cases have to pass. They fail for completely different reasons, and only one of them is
hard.

**Peak-pulse case - not the problem.**
Per-die peak dissipation 1.30 A x 2.94 V = **3.82 W**. XP-G2 Rth junction-to-solder-point is
**1.4 C/W**, so the steady-state junction rise above the solder point is **5.4 C**. The
ceramic package's thermal time constant is a few ms, so a 10 ms flash essentially reaches
that steady state - and 5.4 C is nothing against a 150 C Tj limit. Confirmed: **the pulse is
not the thermal problem; the average is.**

**Sustained case - the real constraint.**
~8 W electrical into the engine; at ~109 lm/W a cool white is roughly 33 % radiant, so
**~5.4 W of heat**, and I would size to the full 8 W for margin and for the `at` upgrade path.

| Ambient | Target solder point | Delta T | **Required Rth(sink -> air) at 8 W** |
|---|---|---|---|
| 56 C (af) | 100 C | 44 C | **<= 5.5 C/W** |
| 69 C (at) | 100 C | 31 C | **<= 3.9 C/W** |

A ~4 C/W natural-convection, no-airflow heatsink is roughly **300-400 cm2 of surface** - a
black-anodised extrusion of order **90 x 90 x 25-30 mm**. That is a real object and it is why
(a) fails: there is nowhere on a 100 x 80 mm board, already carrying a 2800 uF / 100 V bank
and three keepouts, to put it.

**Two flags for the architect, both outside my block but caused by it:**

1. **The 56 C / 69 C internal-air figures (ICD s7.6) predate this 8 W load.** If the heatsink
   sits *inside* the sealed plastic box, that box has to shed 8 W to outside air through
   plastic, and the internal air will not stay at 56 C. The only arrangement that closes is
   bolting the heatsink to (or through) the enclosure wall so the wall is the radiator - and
   per section 8.4 that heatsink is at PoE potential and must stay non-user-accessible.
2. **The JNJ part's Tj max is 115 C**, not 150 C. At 69 C ambient that leaves 46 C of total
   budget for everything from air to junction. It is survivable but it is thin, and it is a
   second, quieter reason to pay for the Cree part.

---

## 8. Risks

1. **The 2.6 A operating point has no single-die answer at JLC.** Every arrangement is a
   parallel string. Parallel strings need per-string ballast or Vf-matched binning or one
   string takes most of the current - a drive-stage requirement that originates here.
2. **Single-source risk, and it is real.** For #1 (Cree XP-G2) there is **no pin-compatible
   alternate in stock at JLC** - it is the only white XP-G-class part with stock, and the
   next-nearest Cree white parts are 150-350 mA mid-power. For #2 (JNJ) there is exactly one
   alternate, C19185884, which is the same part in a different CCT bin from the same vendor -
   so it is a bin second-source, not a supply second-source.
3. **Cost.** The top pick is ~$53/board of emitters at qty 6 against a "$25/board excluding
   the LED module" default in requirements open question 7. The LED is explicitly outside
   that $25, but it is still the most expensive line in the fixture. The runner-up drops it
   to ~$7 by giving up the datasheet.
4. **All Extended, no Basic.** Every candidate carries JLC's Extended-part handling, and at
   20-48 pcs per board across a 6-board run the loose-part attrition matters.
5. **Nobody warrants this operating point.** Even inside DC max, the combination of 5-200 ms
   pulses at 1-25 Hz with a 56-69 C ambient is outside every vendor's characterisation. The
   mitigation is the one already recommended: stay inside DC max so there is nothing to
   warrant.
6. **Colour cast (STR-REQ-14) is only verifiable on paper for the Cree part**, which publishes
   delta-CCx / delta-CCy against both current and temperature. The JNJ, Xinglight, TONYU and
   Honglitronic parts publish neither. Note the mitigating fact: the large green/pink shifts
   Cree describes happen at 2-3x over-drive, so keeping peak inside DC max removes most of
   this risk regardless of which part is chosen.
7. **(b') adds a second PCB order** (1-layer aluminium MCPCB) plus wiring plus a heatsink -
   none of it in this board's BOM, all of it in the fixture's cost and lead time.

---

## Sources

- Live JLCPCB parts search via `parts_search.py` (33 queries, 2026-07-28) - all stock and
  price figures; raw records in `led-emitter.json`.
- [Cree XLamp XP-G2 datasheet CLD-DS51 REV 22 (as shipped by LCSC for C17401863)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2311040049_Wolfspeed-XPGBWT-L1-0000-00H51_C17401863.pdf)
- [Cree app note CLD-AP60 REV 4A, "Pulsed Over-Current Driving of LEDs"](https://downloads.cree-led.com/files/da/x/XLamp-Pulsed-Current.pdf)
- [DigiKey, "Pulsed Over-Current Driving of XLamp LEDs: Information and Cautions"](https://www.digikey.com/en/articles/pulsed-over-current-driving-of-xlamp-leds-information-and-cautions) - 1 kHz test conditions, efficacy droop and chromaticity shift at over-current
- [JNJ-LTJW0115T140/63MIL/5500-6500K datasheet (C19185883)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2311032118_JNJ-OPTOELECTRONICS-JNJ-LTJW0115T140-63MIL-5500-6500K_C19185883.pdf)
- [Xinglight XL-HD3535UWC-A2 datasheet (C3646951)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2406281201_XINGLIGHT-XL-HD3535UWC-A2_C3646951.pdf)
- [Cree CXA1507 COB datasheet (C510527)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Wolfspeed-CXA1507-0000-000N0HG440G_C510527.pdf)
- [Carclo optics for the Cree XP-G family](http://www.carclo-optics.com/optics-for-leds/cree/xp-g/) - off-the-shelf optic + holder range
- [Lumileds LUXEON 5050 product page](https://lumileds.com/products/high-power-leds/luxeon5050/) - DS174 must be pulled before C17242738 can be considered
