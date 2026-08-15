# buck-regulator - candidate research

Block: the converter IC only (support passives are P2's job). Source: `parts_search.py`
(live JLC/LCSC) for every stock/price figure below, cross-checked against manufacturer
datasheets for every electrical figure. Full JLC sweep: `research/raw/buck-regulator-sweep.json`.

## Requirement recap (must-haves this ranking is judged against)
- Vin operating 18-30V (24V nom); **abs-max Vin >= 36V-class is a hard filter**, not a preference.
- Vout 5V fixed, 0-2A continuous, must stay in regulation with **0A load**.
- +/-3% DC (4.85-5.15V) across the full Vin/Iout range, <=50mV pp ripple.
- D = 0.17 at the 30V/5V corner -> **minimum controllable on-time** vs the part's chosen
  switching frequency is a real disqualifier for some parts - checked per candidate below.
- JLCPCB PCBA, single-sided SMT only; thermal pad preferred (~0.8-1.8W dissipation @ 50C
  ambient, natural convection, no heatsink).
- Qty 5; Extended library explicitly allowed for this IC.

## Ranked candidates

| Rank | MPN | LCSC | Sync | Package | Vin abs-max | FB ref (tol) | Peak I-limit | Min on-time | Fsw | Comp | Stock | $@qty5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LMR33630ADDAR | C841384 | **Yes** | SOIC-8-EP/ESOP-8 (PowerPAD) | 38V | 1.00V, +/-1.5% | 3.85-5.05A (HS) | 75/108ns (nom/max) | 400kHz fixed | **Internal** | 6,885 | $0.74 |
| 2 | AOZ1284PI | C48060 | No | SOIC-8-EP | **40V** | 0.80V, +/-1.5% | 5-6A | 150ns typ | 200kHz-2MHz adj | External RC | 14,336 | $0.85 |
| 3 | TPS54560BDDAR | C1850354 | No | HSOIC-8 PowerPAD | **65V** | 0.80V, +/-1% | 6.3-9.5A | ~135ns typ* | 100kHz-2.5MHz adj | External RC | 80,670 | $1.06 |
| 4 | TPS54360BDDAR | C524806 | No | SOIC-8-EP | ~60V-class* | 0.80V, +/-1% (family) | ~3.5A rated | ~135ns-class* | 100kHz-2.5MHz adj | External RC | 29,926 | $0.81 |
| 5 | XL1509-5.0E1 | C61063 | No | SOIC-8, no pad | 45V | fixed 5V, **+/-4%** | 4A typ | n/a (150kHz fixed) | 150kHz fixed | Internal | 280,842 | $0.23 |

`*` TPS54560B abs-max (65V) and current limit (6.3-9.5A) are confirmed directly from TI's
DDA/HSOIC datasheet pages (Abs Max + Electrical Characteristics tables); the 135ns min-on-time
figure is corroborated by public search citing the same datasheet's applications text but was
not independently re-read off the specific subsection - re-verify before final part lock.
TPS54360B numbers are inferred from the shared TI 60-V process family (same package, same
architecture) via its LCSC-listed 4.5-60V operating range; not independently page-confirmed
the way #1-3 were. Treat #4 as the value alternative to #3, not a fully independent data point.

## Why this order (fits requirements > Basic > stock > price > ecosystem)

**#1 LMR33630ADDAR (top pick).** Only synchronous candidate that clears every filter with
margin: abs-max 38V gives 8V/27% headroom over the 30V ceiling; the datasheet's own
*Recommended Operating Conditions* lists output current as 0-3A, i.e. 0A is explicitly inside
spec, not just "should work." It is internally compensated - no COMP pin exists on this part at
all - which is the leanest BOM of the five (no external RC network to size). The "A" (400kHz)
device option's own minimum-on-time spec (75ns nom/108ns max) leaves a ~4x margin against the
340ns actual on-time this design needs at 30V-in/5V-out. Cheapest of the five real candidates.
One caveat: TI also sells "B" (1.4MHz) and "C" (2.1MHz) device options in the same SOIC-8-EP
package at the same LCSC listing family - **the 2.1MHz "C" option computes to only 81ns actual
on-time at the 30V corner against its own 108ns max min-on-time spec, i.e. it would pulse-skip
at high line.** Only the 400kHz "A" option (LMR33630ADDAR, this LCSC row) is safe here; P2 must
not substitute the higher-Fsw sibling for board-size reasons without redoing this check.

**#2 AOZ1284PI.** Best raw voltage headroom of any candidate (40V abs-max vs the 36V-class
ask), and the largest current-limit margin (typ 6A vs a ~2.6A worst-case peak inductor current -
over 2x). Needs an external COMP RC network (visible in the datasheet's own typical application
circuit as CC+RC), which #1 avoids. Its adjustable-Fsw range (200kHz-2MHz via an RFSW resistor)
is wide enough to run well clear of its 150ns min-on-time spec, but only if kept under roughly
600kHz at this duty cycle - the datasheet's own max-duty-cycle spec (87% @ 1MHz) already hints
the part is not meant to run at 1MHz+ into a low-duty application like this one.

**#3 TPS54560BDDAR.** The most bulletproof headroom in the set (65V abs-max, >3x current-limit
margin) and the only candidate where the light-load behavior was confirmed in the *Feature
Description* prose, not just inferred: "Pulse Skip Eco-mode... As the load current approaches
zero, the device enters a pulse-skip mode during which it draws only 146uA input quiescent
current" - a direct, explicit statement that 0A is a designed-for operating point, not an edge
case. Needs external RC compensation. Priciest of the well-margined group, but the gap is a few
cents per unit at qty 5.

**#4 TPS54360BDDAR.** Same TI 60V-class family as #3 at a lower switch-current rating (3.5A
vs 5A) and a lower price; still ~1.75x margin over the ~2A/2.6A-peak load, the thinnest margin
of the top four but still comfortable. Listed because it is a genuinely cheaper same-family
alternative to #3 if P2 wants to save the ~$0.25/unit and doesn't need the extra current
headroom; flagged above as less independently verified than #3.

**#5 XL1509-5.0E1 (not recommended, listed for completeness).** The only JLC **Basic** part
found and by far the cheapest (Basic + huge stock + $0.23), but it fails the accuracy
requirement on its own datasheet numbers: the fixed-5V version's guaranteed output window is
**4.8-5.2V (+/-4%)** at Vin 7-40V / Iload 0.2-2A - that alone is wider than this board's entire
+/-3% budget before line/load stacking or ripple are even added. Its `VCE`-labeled output
saturation-voltage spec (1.2-1.4V typ at 2A) indicates a bipolar, not MOSFET, output switch,
which will run hottest and least efficient of any candidate exactly at the 30V high-line corner
that the requirements doc already flags as the board's thermal worst case. Its own accuracy
table is characterized starting at 0.2A load, not 0A, so true no-load behavior is unconfirmed.
Do not pick this part to hit the accuracy or thermal requirement; it only wins on sticker price.

## Considered and excluded (didn't make the ranked table)

- **AP63357Q / AP63357QZV-7 (Diodes Inc, synchronous, C3194572/C2158014)** - otherwise
  excellent: 0.8V +/-1% FB, 4-6A current limit, 25 C/W thermal (best of anything checked), and
  a genuine PFM light-load mode (86% eff @ 5mA). **Fails the hard Vin-headroom filter**: its
  Absolute Maximum Ratings table gives VIN = -0.3 to +35.0V DC (40V is only a <=400ms transient
  rating), i.e. 1V short of the required >=36V-class abs-max on a continuous basis. Excluded on
  that filter, not on any other merit - worth a second look if the 36V-class rule is ever
  relaxed. [datasheet: diodes.com/datasheet/download/AP63356_AP63357.pdf]
- **MP4560 / MPQ4560 / LM5160 / LM5161 (MPS/TI) family** - all rate their switch/output
  current at 1-2A, i.e. at or below this board's 2A average load with no margin left for the
  ~15-30% ripple current a real inductor choice will add on top (peak inductor current
  guessed at 2.3-2.6A in requirements.md). Dominated by #1-4 above, which cost the same or less
  and carry 2-3x current headroom instead of ~0. Not re-verified against primary datasheets
  given the clear dominance; flagged here so P1/P2 knows they were seen and why they were passed
  over, not missed.
- **TPS54331 family** - live stock confirmed (C9865 etc.) but operating range tops out at 28V,
  which doesn't even reach this board's 30V requirement. Excluded outright, not a headroom
  judgment call.
- Through-hole modules (XP Power `DC-DC Power Modules` category, various) - excluded by mode
  (single-sided SMT only); not evaluated further.

## Cross-cutting risks for P2

1. **Min-on-time vs Fsw is a live constraint on every adjustable-frequency part above**
   (#1's B/C siblings, #2, #3, #4) - the RT/RFSW resistor choice must be checked against the
   part's own min-on-time spec at the 30V/5V/D=0.17 corner, not just left at a textbook default.
   #1's specific LCSC-listed "A" (400kHz) SKU is pre-cleared; the others need the resistor value
   picked with this margin in mind.
2. **External compensation** (COMP pin + RC network) is required by #2, #3, and #4 - 2-3 extra
   passives each, plus more design math (loop compensation) for P2 to carry through. #1 has no
   COMP pin at all (internally compensated) and #5 is fixed-output with no FB divider either -
   both are leaner on parts count if "ultra-bare-bones" parts-count matters as a tiebreaker.
3. **Bootstrap capacitor** (100nF, X7R/X5R, >=10V) is required by all five candidates alike -
   trivial, not a differentiator, but not optional either (all are high-side-NMOS designs).
4. **No-load stability** is explicitly confirmed in the primary source for #1 (0-3A recommended
   operating range includes 0A) and #3 (Eco-mode text explicitly describes approach-to-zero-load
   behavior). #2 has no stated light-load mode but is asynchronous, so it cannot suffer the
   negative-inductor-current light-load failure mode synchronous parts can - regulation at 0A is
   expected but not explicitly spec'd. #5's accuracy table starts at 0.2A, not 0A - unconfirmed.
5. Every candidate here is single-source at its exact LCSC row (no second listed distributor
   checked); MPN-level second-sourcing risk is normal for these commodity buck ICs (all five
   families are pin-compatible-ish within their own SOIC-8/EP footprint class, but not
   drop-in interchangeable across brands without a re-check of FB reference and compensation).

## Sources
- [LMR33630 datasheet (TI)](https://www.ti.com/lit/ds/symlink/lmr33630.pdf)
- [AOZ1284PI datasheet (AOS)](https://www.aosmd.com/res/datasheets/AOZ1284PI.pdf)
- [TPS54560B datasheet (TI)](https://www.ti.com/lit/ds/symlink/tps54560.pdf)
- [TPS54360BDDAR datasheet (LCSC-hosted copy)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2005111633_Texas-Instruments-TPS54360BDDAR_C524806.pdf)
- [XL1509 datasheet (XLSEMI)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_XLSEMI-XL1509-5-0E1_C61063.pdf)
- [AP63356Q/AP63357Q datasheet (Diodes Inc)](https://www.diodes.com/datasheet/download/AP63356_AP63357.pdf)
- LCSC/JLCPCB live search: `parts_search.py` (this repo), raw sweep saved to
  `research/raw/buck-regulator-sweep.json`
