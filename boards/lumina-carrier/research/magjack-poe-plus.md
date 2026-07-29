# PoE+ (802.3at) RJ45 integrated connector module - re-sourcing J1

**Board:** LUM-CAR-A. **Task:** replace HanRun HY931147C (LCSC C91754) with a PoE+ integrated
connector module whose centre-tap / power ratings are **published**, so the magjack stops being the
component that pins the design to Type 1 and silently defeats D-01.

**Date of check:** 2026-07-28. All stock and price figures are as at that date.

---

## 0. Headline verdict - read this first

**Selected: Wurth Elektronik `7499410213` (WE-RJ45LAN, 10/100 Base-T PoE+).**
Digi-Key `732-10839-ND`, **$9.54 each at qty 14** (no price break between 1 and 100),
**2,304 in stock**, 14-week manufacturer lead time, tube packaging.

It publishes exactly the number the exercise exists to obtain:

> **"Power over Ethernet Properties: Designed to support applications up to 600 mA per centre tap.
> Compliant with IEEE 802.3at"**
> - datasheet 7499410213 rev 002.000 (2023-07-11), page 3, section "Power over Ethernet Properties"

**THIS IS NOT A DROP-IN. It is an ICD change, a schematic change and a layout change.**

Three structural differences, in descending order of cost:

1. **NO INTEGRATED BRIDGE.** The part brings out **four raw line-side power nodes**
   (V1+, V1-, V2+, V2-) instead of a rectified V+/V- pair. **Two external full-wave bridges are
   required.** This is new silicon, new nets, new area and new dissipation on the PCB.
2. **The TX and RX chip-side pins swap positions**, and there is only **one** chip-side centre tap
   (TX only), not two. Every `wire_pins` entry on J1 in `poe.py` changes.
3. **Pins 7 and 8 go from no-connect to live 48 V nodes**, which collapses the chip-side /
   line-side isolation barrier on the land pattern from **3.58 mm of copper gap to 1.05 mm**.

Good news, and it is worth a lot: **the land pattern is the same industry-standard 21.25 x 16.0 mm
magjack pattern**, matching the existing `RJ45-TH_HY931147C.kicad_mod` to within 0.03 mm on every
dimension. The footprint is reusable (with a pad-diameter review, s5.3), so this is not a board
outline or mechanical change.

This closes `decisions.md` **OPEN-A** in the way OPEN-A itself predicted:
*"Removing the risk at H1 means sourcing a raw-tap jack off-LCSC, which breaks the Q14 single-order
assumption."* That is precisely what happened.

---

## 1. Published ratings of the selected part, with citations

Source: `boards/lumina-carrier/work/mj/we-7499410213.pdf` (fetched from
`https://www.we-online.com/components/products/datasheet/7499410213.pdf`), rev 002.000, 2023-07-11,
6 pages, text-extractable. Raw text dump kept at `work/mj/we_text.txt`.

### 1.1 The PoE numbers - the point of the exercise

| Figure | Value | Source |
|---|---|---|
| **DC current per centre tap** | **600 mA** | p3, "Power over Ethernet Properties": *"Designed to support applications up to 600 mA per centre tap."* |
| **IEEE compliance** | **802.3at** | same block: *"Compliant with IEEE 802.3at"* |
| **Which nodes the 600 mA applies to** | **per channel VC1 or VC2** | Sibling part `7499410221` (same family, green/green LEDs), older-format datasheet 2016-01-29 p1 s.G: *"Compliant with IEEE 802.3at for 10/100 Base-T applications (600mA when using channel VC1 or VC2)"* / German *"Geeignet fuer 10/100 Base-T gemaess IEEE 802.3at (600mA ueber VC1 oder VC2)"*. VC1 = the V1+/V1- pair (Mode A data-pair taps); VC2 = the V2+/V2- pair (Mode B spare pairs). |
| **Operating temperature** | **-40 C to +85 C** | p3, "General Information" |
| **Thermal limit statement** | *"It is recommended that the temperature of the component does not exceed +85 C under worst case conditions"* | p3, "General Information" (second block) |
| Mating cycles | 750 | p3 |
| MSL | 1 | p3 |

**Honest caveat on margin.** 802.3at Type 2 is **0.600 A DC / 0.686 A peak** at the PD input
(`connector-icd.md` s6.1). The Wurth rating is **600 mA, i.e. exactly 1.00x the DC figure and
0.87x the peak figure - there is no margin.** The task asked for "at least 600 mA per pair, ideally
with margin"; **no 10/100BASE-TX part found publishes more than 600 mA per centre tap.** Everything
rated higher in the surveyed catalogues is gigabit or PoE++ (bt). See s7 OPEN-2.

### 1.2 Magnetics - the 10/100 requirements

| Property | Value | vs HY931147C |
|---|---|---|
| Data rate | **100BASE-TX** (p3) | same |
| Turns ratio | **1:1, +/-2%** (p3) | same (HY marked 1CT:1) |
| OCL | **350 uH min @ 100 kHz / 100 mV** (p3) | same class. NB: the 7499410213 sheet does **not** print a DC-bias condition; the sibling `7499410221` sheet does: *"100kHz / 100mV @ 8mA DC-Bias"* - identical to the HY's 8 mA bias condition |
| Insulation test voltage | **2250 V (DC), 1 min** (p3) | HY: 1500 Vrms 1 min. 1500 Vrms is ~2121 V peak, so 2250 VDC is **comparable, not 1.5x better** - do not claim an improvement |
| Insertion loss | -1.2 dB max, 1-100 MHz | HY: -1.0 dB max. Slightly worse, irrelevant at 100BASE-TX |
| Return loss | -18 dB (1-30), -14 (30-60), -12 (60-80), -10 (80-100) | HY: -18 / -16 / -14 / -12 over slightly different bands. Comparable |
| CMRR | -35 (1-30), -32 (30-60), -30 (60-100) | HY: -35 dB min 1-100 MHz. Wurth is banded and slightly worse at the top |
| Crosstalk | -32 dB (1-60), -30 dB (60-100) | HY: -30 dB min 1-100 MHz. Comparable |
| Auto-MDIX | capable (sibling sheet, s.G) | Digi-Key lists 7499410213 as "AutoMDIX" |

### 1.3 LEDs

| Property | Value |
|---|---|
| Colours | **green (LEFT) - yellow (RIGHT)**, p3 "LED (Left-Right) green-yellow" |
| Forward voltage | **1.8 - 2.4 V @ 20 mA** (p3) |
| Pin assignment | **11 = green anode, 12 = green cathode, 13 = yellow anode, 14 = yellow cathode** (p2 schematic; the "+" marker sits on the odd-numbered side of each diode symbol) |

R7 / R8 = 330R from +3V3 give ~3.6 mA at Vf 2.1 V - unchanged, still inside the W5500's 8.6 mA IOL.

### 1.4 Mechanical

| Item | 7499410213 | HY931147C |
|---|---|---|
| Body W x D x H | 16.0 x 21.25 x 13.5 mm | 16.00 x 21.60 max x 13.95 max |
| Board-lock lead below PCB | 3.5 +/-0.5 mm | D 3.05 min |
| Housing | PA66 black, UL94 V-0 | - |
| Shield | brass, 50 uin nickel | - |
| Contacts | phosphor bronze, 30 uin gold over 50 uin nickel | - |
| Approvals | RoHS, REACh, cURus E472316 (UL-62368) | RoHS only |

Height 13.5 mm is **below** the ~15 mm assumed by `connector-icd.md` s7.6, so the RJ45 relief zone
`(6,0)-(36,26)` on daughters stays valid and stays conservative. **No ICD s7 mechanical change.**

---

## 2. Ranked comparison - why this part and not the others

Ranking criterion is the owner's stated one: **does the vendor publish current / power / thermal
numbers for the taps, or does it only claim a standard?**

| # | Part | 10/100? | Published PoE rating | Bridge | Op temp | Verdict |
|---|---|---|---|---|---|---|
| **1** | **Wurth 7499410213** (WE-RJ45LAN PoE+) | yes, 100BASE-TX, 1:1, 350 uH | **600 mA per centre tap, IEEE 802.3at**, explicit, plus an explicit +85 C component-temperature statement | **no** - V1+/V1-/V2+/V2- raw | **-40..+85** | **SELECTED** |
| 2 | Wurth **7499410221** (same family, G/G LEDs) | yes | **600 mA when using channel VC1 or VC2, IEEE 802.3at** (older 2016 datasheet, arguably clearer wording) | no | -40..+85 | Electrically the same part. **Rejected on LEDs only**: green/green loses the yellow ACT indicator the board drives. Keep as the second source |
| 3 | HALO FastJack 10/100 PoE, `HFJ11-RPE44E-L21RL` family | yes | Publishes a **"Current" column: 350 mA** for every catalogued variant, and only **IEEE802.3af**. Note 7 says "Higher current parts available" - not catalogued, not buyable | no (pins 9/10 power feed, pin 8 NC for separation) | -40..+85 (RPE) | **Reject - af only.** Numbers are published, but they are the wrong numbers |
| 4 | Bel Fuse / Stewart `SI-52003-F` and the SI-50000/SI-60000 10/100 line | yes | Bel publishes a coarse **"PoE Rating: PoE 15W"** class only. **No mA per tap, no thermal figure.** 15 W is af | varies | **0..+70** on the PoE 10/100 parts | **Reject.** Repeats the defect being fixed (a claim, not a number), and 0-70 C is worse than the HY. Bel's PoE+/30 W and 60 W MagJacks exist but are **1G/10G only** |
| 5 | Pulse / Yageo PulseJack `JK0-*` / `JXD*` | mixed | The PoE+ documented parts (`JK0-0177NL`, J432) are **single-port GIGABIT** | varies | - | **Reject - wrong data rate.** The 10/100 PoE parts in the family are af |
| 6 | LINK-PP `LPJP4155CNL` / `LPJ0155HENL` (10/100, 802.3at, **integrated rectifier bridge**) | yes | Product page publishes **a drawing only** - no electrical specification table, no mA per tap, no bridge rating. Op temp **0..+70 C** | **yes** | 0..+70 | **Reject.** This is the one family that would have been a near drop-in, and it fails on **exactly the same defect as the HY931147C** - an 802.3at claim with no numbers. Also not a mainstream-distributor part |
| 7 | Molex "PDJack" | no (gigabit) | integrates a **PD controller** as well as bridges | yes | - | **Reject** - gigabit, and it would displace the TPS2378 and all of D-01's class-resistor lever |

**Conclusion on the bridge question, stated plainly as instructed:** the best-documented option has
**no integrated bridge**. Every integrated-bridge 10/100 PoE+ part found is from the same class of
vendor as the HY931147C and publishes no ratings, so choosing one would be a lateral move that
achieves nothing. **The external bridge is the price of getting published numbers, and it is a
schematic change, not a BOM swap.**

---

## 3. Pin-by-pin diff against the frozen interface

Ground truth for the incumbent: `parts/C91754.json` and `kicad/gen/poe.py` `sh.wire_pins("J1", ...)`.
Ground truth for the candidate: 7499410213 datasheet p2 "Schematic".

### 3.1 The table

| Pin | HY931147C (frozen) | net today | **Wurth 7499410213** | net required | Same? |
|---|---|---|---|---|---|
| **1** | RX_P1, RX chip winding, <-> contact J3 | `ETH_RXP` | **TD+**, TX chip winding, <-> J1 | `ETH_TXP` | **NO - RX/TX swap** |
| **2** | RX_P2, RX chip winding, <-> J6 | `ETH_RXN` | **TD-**, <-> J2 | `ETH_TXN` | **NO - RX/TX swap** |
| **3** | RX_CT, chip-side RX centre tap | `NC` | **CTD**, chip-side **TX** centre tap | `+3V3` | **NO - different winding, and now used** |
| **4** | TX_CT, chip-side TX centre tap | `+3V3` | **RD+**, RX chip winding, <-> J3 | `ETH_RXP` | **NO** |
| **5** | TX_P5, TX chip winding, <-> J1 | `ETH_TXP` | **RD-**, <-> J6 | `ETH_RXN` | **NO** |
| **6** | TX_P6, TX chip winding, <-> J2 | `ETH_TXN` | **absent from the schematic** - hole present in the pattern, no internal connection | `NC` | **NO - becomes the NC** |
| **7** | absent from schematic (SKU NC) | `NC` | **V1+** - line-side centre tap of the **TX / pair 1,2** transformer (Mode A leg) | `POE_TAP_A1` (new) | **NO - NC becomes a 48 V node** |
| **8** | absent from schematic (SKU NC) | `NC` | **V1-** - line-side centre tap of the **RX / pair 3,6** transformer (Mode A leg) | `POE_TAP_A2` (new) | **NO - NC becomes a 48 V node** |
| **9** | **V+**, common cathode of BOTH internal bridges | `V48_RAW` | **V2+** - the tied spare pair **J4+J5** (Mode B leg) | `POE_TAP_B1` (new) | **NO - rectified output becomes a raw AC tap** |
| **10** | **V-**, common anode of BOTH internal bridges | `V48_RTN` | **V2-** - the tied spare pair **J7+J8** (Mode B leg) | `POE_TAP_B2` (new) | **NO - as above** |
| **11** | **YELLOW** anode | `LED_Y_A` (R7 to +3V3) | **GREEN** anode | anode, R7/R8 to +3V3 | anode/cathode **same**, **colour swapped** |
| **12** | yellow cathode | `ETH_LED_ACT` | green cathode | `ETH_LED_LINK` | **colour swap - net must move** |
| **13** | **GREEN** anode | `LED_G_A` (R8 to +3V3) | **YELLOW** anode | anode | anode/cathode **same**, **colour swapped** |
| **14** | green cathode | `ETH_LED_LINK` | yellow cathode | `ETH_LED_ACT` | **colour swap - net must move** |
| GND1/GND2 | shield tabs | `SHIELD` | shield tabs | `SHIELD` | **same** |

### 3.2 Point-by-point against the interface facts the task listed

| Frozen interface fact | Wurth 7499410213 | Verdict |
|---|---|---|
| **P9 = V+, P10 = V-** (rectified) | P9 = V2+, P10 = V2- : **raw spare-pair taps, unrectified** | **DIFFERENT.** Both `V48_RAW` and `V48_RTN` move to the output of a new external bridge pair |
| **Two internal bridges onto common V+/V-** | **none** | **DIFFERENT.** External |
| **Spare pairs tied internally** (J7+J8, J4+J5) | **yes, identical** - J4/J5 tied to V2+, J7/J8 tied to V2- | **SAME** |
| **P7/P8 no-connect** | P7 = V1+, P8 = V1- : **live line-side 48 V nodes** | **DIFFERENT, and it is the load-bearing layout change (s5.4)** |
| **LED anodes 11/13, cathodes 12/14; cathodes driven active-low through 330R from +3V3** | **anode/cathode order identical** (odd = anode). **Colours swapped**: 11/12 green, 13/14 yellow | **PARTIALLY SAME.** Fix = swap `ETH_LED_ACT` / `ETH_LED_LINK` between pins 12 and 14. R7/R8 unchanged |
| **T568B MDI mapping; TX winding on P5/P6, RX on P1/P2** | T568B mapping **preserved** (TX <-> J1/J2, RX <-> J3/J6, spares 4/5 and 7/8), but **TX is now on P1/P2 and RX on P4/P5** | **MAPPING SAME, PIN POSITIONS SWAPPED** |
| **Land pattern**: 10x dia-0.89 in 2 staggered rows of 5 @ 2.54 pitch (rows 2.54 apart), 4x dia-1.02 LED, 2x dia-1.63 board-lock, 2x dia-3.25 NPTH | **10x dia-0.90, 4x dia-1.03, 2x dia-1.6, 2x dia-3.25**; 2.54 pitch, 1.27 stagger; shared dims 11.43 / 13.25 / 15.49 / 16.0 / 8.89 / 8.17 / 4.08 / 3.05 all match | **SAME to within 0.03 mm** |

### 3.3 One extra internal feature the HY does not have

The Wurth part contains an **internal Bob Smith / AC termination network**: `4 x 22 nF / 100 V` in
series with `4 x 75 ohm`, one leg on each of V1+, V1-, V2+, V2-, commoned and taken to **Shield
through 0.001 uF / 2 kV** (p2 schematic). It is DC-blocked by the 22 nF caps, so it does **not**
load the PoE rail and is PoE-safe.

Consequence: **`poe.py`'s docstring claim "NO Bob Smith network ... on a Mode A + Mode B PD there is
no unpowered tap left to terminate" becomes wrong for the new part** - the termination is inside
the connector and cannot be removed. The external shield hybrid **R6 (1M) || C3 (1 nF / 2 kV) stays**
(it bridges Shield to GND, and is now in *series* with the internal 1 nF, not in parallel with it),
but the rationale paragraph must be rewritten and P8 EMC review should note the new internal AC path
from each PoE node to Shield.

---

## 4. What must change - enumerated

### 4.1 Schematic (`kicad/gen/poe.py`)

1. **New symbol + new part JSON.** `aiee:HY931147C` -> a new `aiee:7499410213` symbol with pin names
   TD+/TD-/CTD/RD+/RD-/NC/V1+/V1-/V2+/V2-/LED pins. New `parts/C5525705.json` grounding file.
2. **Every `wire_pins("J1", ...)` entry changes** per s3.1.
3. **NEW: two external full-wave bridges.** Mode A bridge across P7/P8; Mode B bridge across
   P9/P10; both commoned onto `V48_RAW` / `V48_RTN`. This restores exactly the topology the
   HY931147C had internally (all eight diodes onto one rail pair), so **nothing downstream of
   `V48_RAW`/`V48_RTN` changes** - D1 TVS, U1 TPS2378, CBULK, RDEN, RCLS, the T2P network and the
   whole `pwr` sheet are untouched.
4. **Bridge sizing is NOT a trivial pick.** It must carry **600 mA continuous** with two diodes in
   conduction. At Vf ~1.1-1.2 V per diode that is **~1.3-1.4 W in one package at the `at` operating
   point** (~0.7-0.8 W at af). Candidate off-the-shelf parts confirmed on LCSC:
   - `MB6S-50MIL` (LCSC **C2487**), 600 V / 1 A, MBS/SOIC-4, 436,704 in stock, **$0.0284** each,
     Vf 1.1 V @ 400 mA. **Cheap and stocked, but the MBS package cannot dissipate 1.4 W** - this
     needs a thermal check, not a datasheet-current check.
   - `HD01-T` (LCSC **C52151**), MBS, 10,735 in stock, $0.2752.
   **P2/P4 must size this against 600 mA continuous AND a `check_thermal` pass**, and should
   consider a larger-body bridge (SMA/DFN) or a low-Vf part. Do not just pick a "1 A" bridge.
5. **RDEN detection arithmetic must be redone.** `poe.py` currently argues that TI's 24.9 k already
   assumes an input bridge and that the HY bridge's incremental resistance at the 200-400 uA
   detection current is ~0.35 k, giving ~25.1 k inside IEEE's 23.7-26.3 k window. **That number was
   for the HY's unspecified internal diodes.** With a chosen bridge the incremental resistance is
   computable from a real I-V curve and must be recomputed; R1+R2 may need to move off 24.8 k.
6. **LED nets swap**: pin 12 <- `ETH_LED_LINK`, pin 14 <- `ETH_LED_ACT` (so green still means link
   and yellow still means activity). R7/R8 unchanged.
7. **Pin 3 -> `+3V3`** (chip-side TX centre tap). **The open item "P3 floating RX centre tap, may
   need a 0.1 uF to GND for EMC" disappears** - the part has no chip-side RX tap at all.
8. Refdes budget: the `poe` sheet's allocated range is `D1-D9` (`sheets.md` s2.1). Two bridges fit
   (D2, D3) with room to spare.

### 4.2 ICD (`architecture/connector-icd.md`)

The ICD is **frozen at H1**, so this needs a **rev A7** issued by the carrier owner:

- **s7.6 "RJ45 relief"** - the text says the jack is "~15 mm tall". The Wurth part is **13.5 mm**.
  The 30 x 26 mm relief and the "protrudes ~4 mm" figure remain **valid and conservative** (real
  protrusion ~2.5 mm). **Recommend: update the number, keep the zone.** No daughter re-baseline.
- **s7.1 "RJ45 position ... body (10,0)-(32,22)"** - 16.0 x 21.25 still fits the 22 x 22 envelope.
  **No change.**
- **s6.1** quotes "802.3at: 0.600 A DC, 0.686 A peak". **A new sentence is needed**: the connector's
  published rating is 600 mA per centre tap, i.e. it does **not** cover the 0.686 A peak. See s7
  OPEN-1.
- **s9 / isolation** - the insulation figure changes from 1500 Vrms to 2250 VDC, and s5's creepage
  section acquires the new chip-side/line-side barrier constraint of s5.4 below.

**Daughters are not affected.** Nothing on J3/J4 changes. This is a carrier-internal rev.

### 4.3 Architecture (`architecture/blocks.md`)

`blocks.md` s2.1 states three consequences of choosing the integrated-bridge jack. **Two of them
now reverse**, and the document says so itself:

> *"1. There are no external bridges and no `POE_TAP_*` nets on the board. The 48 V domain enters
> on two pins instead of four, which removes the hardest creepage region (48 V within millimetres
> of the MDI pads) and about 550 mm2 of PD front-end area."*

**That 550 mm2 and that creepage region both come back.** P6 placement must find the area on a board
that is already laid out to a 100 x 80 outline.

> *"2. The bridge Vf is no longer a design variable. ~1.4 V of drop at the at operating point
> (~0.84 W) is dissipated inside a plastic connector body with no heatsink path..."*

It **is** a design variable again. Note that s3.1's power budget already books
**-0.51 W (af) / -1.18 W (at)** of "magjack DCR + internal bridge + hot-swap FET" loss, so the
**box-air total in ICD s7.7 does not change** - the heat merely moves from inside the connector body
onto the PCB, where it is easier to sink but where `check_thermal` will now see it as new components
needing copper.

`decisions.md` **OPEN-A closes** (the at magjack-qualification dependency is discharged).

### 4.4 Footprint / library

- `RJ45-TH_HY931147C.kicad_mod` is **dimensionally reusable**: pads at the same coordinates, drills
  0.900 / 1.100 / 1.630 / 3.25 NPTH against the Wurth 0.90 / 1.03 / 1.6 / 3.25. Board-lock pins are
  1.6 vs a 1.63 drill (0.03 mm looser - fine); LED pins 1.03 vs a 1.10 drill (fine).
- **Rename** to a part-neutral name (e.g. `RJ45-TH_MAGJACK_21x16`) since it now serves both parts.
- **Pad diameters must be revisited** - see s5.4.
- **MUST VERIFY, NOT ASSUMED:** the mapping of pin *number* to physical *hole*. Both vendor drawings
  label 1/2 at one end, 9/10 at the other, 11-14 on the LED row, on identical dimensioning, which is
  strong evidence of the same convention - but the Wurth drawing's pin-number glyphs could not be
  read at sufficient resolution to *prove* it. **Run `fp_verify` against the Wurth drawing before
  release.** Getting this wrong swaps the whole connector end-for-end.

---

## 5. Layout consequences

### 5.1 New nets in the 48 V domain

Four new line-side nets (`POE_TAP_A1/A2/B1/B2`) run from J1 pins 7/8/9/10 to the bridges. They are
**48 V nets** and inherit the board-wide **0.635 mm** outer-layer clearance rule (ICD s5.1), the
`.kicad_dru` hand rule (TRAP-1) and `check_creepage`.

### 5.2 Area

~550 mm2 of PD front-end area returns (blocks.md s2.1). Two SOIC-4-class bridges plus their
clearance is the dominant part of it.

### 5.3 Thermal

0.7 W (af) / 1.3-1.4 W (at) of bridge dissipation lands on the PCB. It is inside the existing box-air
budget (s4.3), but it is a **new local hot spot** that `check_thermal` will evaluate and that needs
copper. It must not be placed inside ICD s7.6's DC-DC hot zone `(2,46)-(36,68)` argument by
accident - the RJ45 is at the top edge, so the natural bridge location is near `(10..32, 0..26)`,
clear of that zone.

### 5.4 The isolation barrier - the one genuinely uncomfortable finding

On the **existing** land pattern (from `RJ45-TH_HY931147C.kicad_mod`: 1.500 mm pads on 0.900 mm
drills, 2.54 mm within-row pitch, rows 2.54 mm apart, 1.27 mm stagger):

| | chip-side pads | line-side pads | nearest pair | centre-to-centre | **copper gap** |
|---|---|---|---|---|---|
| **HY931147C today** | 1-6 | 9, 10 (7, 8 empty) | pad 5 - pad 9 | 5.08 mm | **3.58 mm** |
| **Wurth 7499410213** | 1-5 (6 empty) | **7, 8**, 9, 10 | **pad 5 - pad 7** | **2.54 mm** | **1.05 mm** |

**The barrier loses 2.53 mm.** HALO publishes an application note on exactly this geometry
(`fastjack-poe-100baset.pdf`, "Solder Pad Design Considerations for FastJack with Power Feed
Terminals"):

> *"IEEE802.3 requires a system to meet 1500VAC or 2250VDC isolation between cable side and chip
> side circuits... the concern for the designer is the spacing between pin9 and pin7 solder pads.
> **Minimum separation required between solder pads is 55mils to avoid electron arcing at 1500VAC
> voltage.** Terminal holes are approximately 35mils diameter at 100mils pitch (column to column).
> Therefore, the 55mils separation is achievable."*

55 mils = **1.40 mm**. The current 1.500 mm pad gives **1.05 mm (41 mils) and misses it.** HALO's own
arithmetic implies a **1.14 mm pad** (45 mil) on a 0.89 mm hole, which is a 0.12 mm annular ring -
**below JLC's PTH minimum**.

Practical resolution, for the owner to rule on:
- Shrink pads 5, 6, 7, 8 (or all ten signal pads) from 1.500 mm to **1.20 mm** - JLC's minimum
  annular ring on a 0.90 mm drill. Gap becomes **1.34 mm (52.8 mils)**, just under HALO's 55 mils.
- Note that `check_creepage` will **not** catch this: it enforces 0.635 mm for a 57 V **working**
  voltage, and 1.05 mm passes that comfortably. The 1500 Vrms / 2250 VDC figure is a **component
  type test**, not a board working voltage, and the board is not required to pass it. So this is an
  engineering judgement, not a gate failure.
- Every raw-tap PoE magjack in the industry has this geometry. It is not a defect of this part; it
  is the cost of not having the bridge inside the connector.

---

## 6. Assembly consequences - this board no longer ships fully populated

### 6.1 It cannot come from JLCPCB assembly

`parts_search` on the live LCSC catalogue returns the part - **LCSC `C5525705`, Wurth Elektronik
7499410213, Extended, min qty 1** - but:

```
stock: 0
price: $14.97 (qty 1 / 10 / 12 all the same)
```

**Zero stock, and 57 % more expensive than Digi-Key even if it were in stock.** It cannot be bought
into a JLC assembly order. Confirmed at 2026-07-28.

### 6.2 What that forces

1. **J1 becomes a hand-fitted / not-fitted BOM line.** It must be marked
   **`exclude_from_pos` / DNP** on the footprint so kicad-cli's pos export drops it - `bom_cpl.py`
   then omits it from both `BOM.csv` and `CPL.csv` automatically (bom_cpl docstring: *"The pos file
   already omits parts flagged exclude-from-pos/DNP ... so BOM and CPL cover exactly the assembled
   set"*). `board_init` already uses this mechanism for mounting holes, so the machinery exists.
2. **The board ships from JLC PARTIALLY POPULATED.** Everything else is assembled; the RJ45 hole
   pattern arrives bare.
3. **The human assembly step:** hand-solder one 16-terminal THT right-angle magjack (10 signal +
   4 LED + 2 board-lock tabs) per board, 14 boards. The two 1.63 mm board-lock tabs are the
   mechanical retention and must be soldered, not just the signal pins. This is straightforward
   hand work but it is ~15 minutes per board and it is the **last** step - the connector body
   blocks access to nothing, but it stands 13.5 mm proud at the top edge.
4. **The part must be ordered separately from Digi-Key**, breaking Q14's single-order assumption
   (exactly as `decisions.md` OPEN-A warned). 14 pcs, 14-week manufacturer lead time if Digi-Key's
   2,304 units go.

### 6.3 A tooling gap the orchestrator must know about

**`order_quote.py` will over-count the assembly.** `_assembly_counts()` derives `n_parts` and
`n_joints` from **every pad on the board that has a net**:

```python
for pad in bg.pads_of():
    if pad.net is None:
        continue
    refs[pad.ref] = refs.get(pad.ref, 0) + 1
```

It **does not read the DNP / exclude-from-pos flag**. So a DNP'd J1 will still be billed as ~16 THT
joints and one Extended feeder in the quote, even though JLC will not place it. That is roughly
`$0.0173 x 16 = $0.28/board` of THT surcharge plus one feeder fee counted in error - small in money,
but it means the P10 package **silently claims a fully-assembled board**.

**Recommendation:** either teach `_assembly_counts` to skip DNP footprints, or carry an explicit
"hand-fitted parts" list into the P10 package and the design document so the partial population is
visible to whoever receives the boards. **This is an orchestrator decision - not made here.**

---

## 7. Cost

| | HY931147C (C91754) | **Wurth 7499410213** |
|---|---|---|
| Unit price at qty 14 | **$2.148** (LCSC qty-10 break) | **$9.54** (Digi-Key, no break between 1 and 100) |
| Extended for 14 | $30.07 | **$133.56** |
| Distributor | LCSC / JLC (in the assembly order) | Digi-Key 732-10839-ND, 2,304 in stock, separate order |
| External bridges | none | 2 x ~$0.03-0.28 = **+$0.06 to $0.56/board** |
| JLC THT joints saved | - | -16 joints (~-$0.28/board) |
| **Net BOM delta** | - | **about +$7.2 / board** |

`blocks.md` s6 puts the BOM subtotal at **$17.56** and the total per assembled carrier at
**~$26-32 against a <= $30 target, "at the target, with no room."**

**This swap pushes the carrier to roughly $33-39 per board, i.e. over the Q15 target by ~$7.**
14 boards = **+$103** on the programme. That is a real number the owner should see, and it is the
price of the published rating.

---

## 8. Open items for the orchestrator / owner

| ID | Item | Recommendation |
|---|---|---|
| **OPEN-1** | The 600 mA rating equals the 802.3at **DC** maximum exactly and is **below** the 0.686 A **peak**. Worse, the carrier's own TPS16630 eFuse limits at **1.0 A** and the TPS2378 hot-swap at ~1.0 A - so at the `at` build **the magjack becomes the lowest-rated element in the 48 V path and neither protection device protects it.** Under a downstream fault the centre tap sees up to 1.0 A for up to 162 ms before latch-off | Either accept (the PSE also limits, and 162 ms of 1.67x on a magnetics winding is survivable), or **reduce R(ILIM) at the `at` build so the eFuse limit sits at or below 600 mA**. Note this would make D-01 a **two**-resistor upgrade instead of one, which D-01 explicitly avoids. **Owner decision.** |
| **OPEN-2** | **No 10/100BASE-TX part found publishes more than 600 mA per centre tap.** Higher-rated modules are all gigabit / PoE++ | Accept 600 mA, or accept a gigabit magjack (wasteful with a W5500 but they exist with higher published ratings). Recommend: **accept 600 mA** |
| **OPEN-3** | **Bridge part not selected.** Needs 600 mA continuous **and** a `check_thermal` pass at 1.3-1.4 W | Dispatch a part-sourcer pass for a low-Vf bridge in a package that can take 1.4 W, or two, at P2 |
| **OPEN-4** | **Pin-number-to-hole mapping unproven** (s4.4). Everything else about the land pattern matches to 0.03 mm | **Mandatory `fp_verify` against the Wurth drawing before P4 freezes the symbol** |
| **OPEN-5** | **Tab orientation** - the HY931147C is tab-down (`blocks.md` s2.1). The Wurth drawing shows front-face LEDs at the bottom and contacts at the top, which reads as tab-down, but Digi-Key's parametric field says "User Selectable" (probably a data error) | Confirm from the Wurth drawing before the panel cutout is drawn. Cosmetic if wrong, but it flips which LED is physically left |
| **OPEN-6** | **Isolation-barrier pad shrink** (s5.4): 1.05 mm gap vs HALO's published 1.40 mm guidance | Recommend shrinking the 10 signal pads to 1.20 mm (gap 1.34 mm). Owner to accept the residual 2 mil shortfall |
| **OPEN-7** | **`order_quote` counts DNP parts** (s6.3), so the partial population is invisible to P10 | Orchestrator to decide: patch `_assembly_counts`, or carry an explicit hand-fit list into the package |
| **OPEN-8** | **Cost overrun ~$7/board** against a target already "at the target, with no room" | Owner decision - this is the price of the exercise |

---

## 9. Files

| File | What |
|---|---|
| `work/mj/we-7499410213.pdf` | Selected part datasheet, rev 002.000 2023-07-11 |
| `work/mj/we-7499410221.pdf` | Sibling PoE+ part, 2016 datasheet with the clearer "600mA when using channel VC1 or VC2" wording |
| `work/mj/we-7499211121A.pdf` | Wurth **af** part (350 mA per centre tap) - the contrast case |
| `work/mj/halo-fastjack-poe.pdf` | HALO 10/100 PoE FastJack family - the 350 mA table and the 55-mil isolation app note |
| `work/mj/we_text.txt` | Extracted text of the two Wurth 2023-format sheets |

Distributor: Digi-Key `732-10839-ND` -
`https://www.digikey.com/en/products/detail/wurth-elektronik/7499410213/6598161`
LCSC (zero stock, informational): `C5525705` -
`https://www.lcsc.com/product-detail/ethernet-connectors-modular-connectors-rj45-rj11_wurth-elektronik-7499410213_C5525705.html`
