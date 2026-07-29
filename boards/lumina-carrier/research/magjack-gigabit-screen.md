# Gigabit PoE+ ICM screen - does anything publish MORE than 600 mA per centre tap?

**Board:** LUM-CAR-A (LUMINA carrier). **Date of check:** 2026-07-28. All stock/price as at that date.
**Question:** the previous pass (`magjack-poe-plus.md`) rejected gigabit PoE+ ICMs on data rate, which
was a category error. A 4-pair 1000BASE-T ICM is electrically fine for a W5500 at 100BASE-TX. This
pass screens gigabit PoE+ parts for a **published centre-tap current STRICTLY ABOVE 600 mA**.

---

## 0. Answer

**Yes. Two parts publish a number above 600 mA. One of them is on LCSC.**

**Recommended: LINK-PP `LPJG0926HENL`, LCSC `C22457393`.**
1000BASE-T PoE+ magjack, **3,109 in stock, $3.7852 each at the qty-10 break ($52.99 for 14)**,
type Extended, **JLCPCB Assembly Type = Wave Soldering** (i.e. JLC places it - no DNP, no hand-solder,
single order), exactly the same assembly class as the incumbent C91754.

It publishes, verbatim, in `ELECTRICAL SPECFICATIONS @25C` on page 1 of drawing `LP18022610` rev A
(2018-02-26):

> **`7. DC Current/Voltage Rating pse Pins:  720mA MAX @57VDC(Continuous)`**

**720 mA > 600 mA.** Against 802.3at Type 2 at the PD input (0.600 A DC / 0.686 A peak,
`connector-icd.md` s6.1) that is **1.20x the DC figure and 1.05x the peak figure** - the first
candidate found anywhere in this exercise that covers the 0.686 A peak with margin instead of
falling under it.

Second place, and the highest number found: **HALO `HFJT1-1GH4PE-L12RL`, 1 A per pair, published**.
Rejected on mechanics and availability, not on the number - see s3.

**The bridge answer, stated plainly: NO integrated bridge.** LPJG0926HENL brings out four raw
line-side centre taps VC1..VC4. **Two external full-wave bridges are still required**, exactly as the
Wurth 7499410213 plan already assumed - so this is not new cost relative to the current plan, it is
the same cost with a better number and an LCSC part number.

**The isolation answer, stated plainly: it does NOT fix the 1.05 mm collapse.** Minimum chip-side to
line-side hole spacing is **2.56 mm centre-to-centre**, which with the incumbent 1.50 mm pads is
**1.06 mm of copper gap** - within rounding of the Wurth part's 1.05 mm and far short of HALO's
55 mil / 1.40 mm guidance. There is a real mitigation the Wurth part does not offer (s4.2).

---

## 1. The screen - what was checked and what it published

| # | Part | Data rate | **Published tap current?** | Bridge | Verdict |
|---|---|---|---|---|---|
| **1** | **LINK-PP LPJG0926HENL** (LCSC C22457393) | 1000BASE-T | **YES - 720 mA MAX @57VDC continuous** | no | **SELECTED** |
| **2** | **HALO HFJT1-1GH4P / -1GH4PE** long body | 1000BASE-T | **YES - 1 A per pair** | no | strongest number, **rejected on body size + no distributor stock** (s3) |
| 3 | HALO HFJT1-1GHP / -1GHPE long body | 1000BASE-T | YES - **600 mA** per pair | no | ties the Wurth, does not beat it |
| 4 | HALO HFJT1-1GP / -1GPE long body | 1000BASE-T | YES - 350 mA per pair | no | reject, below af+ needs |
| 5 | Pulse/Yageo **JK0-0177NL**, **JXK0-0190NL** (J432, "Single-Port Gigabit PoE+") | 1000BASE-T | **NO number at all.** J432.C 10/20 has columns for insertion loss, return loss, crosstalk, CMR and hipot (2250 VDC) and **no current column**. Text says only "with the addition of Power over Ethernet, according to IEEE 802.3at" | - | **reject - criterion 1.** This is the exact defect being fixed |
| 6 | Bel Fuse / Stewart **SI-60062-F** | 10/100BASE-T | Bel's own product page lists **PoE Rating = "Non PoE"**. It is not a PoE part at all | - | **reject** - the family named in the task brief is a dead end |
| 7 | Bel Fuse **SI-52009-F** (a real PoE+ ICM) | 10/100BASE-T | **Class only: "PoE+ 30W"**. No mA, no per-tap figure. 0..+70 C | - | **reject - criterion 1.** Confirms the prior pass's read of Bel |
| 8 | Wurth **7499111001A** (WE-RJ45LAN gigabit) | 1000BASE-T | **No "Power over Ethernet Properties" block exists in the datasheet.** Only "Compliant with IEEE 802.3ab" | - | **reject - Wurth's gigabit RJ45 jacks are not PoE parts.** Wurth's PoE block only appears on the 10/100 PoE SKUs |
| 9 | HALO **HFJ11-1Gxx / HFJT1-1Gxx short body** | 1000BASE-T | Not PoE - "IEEE802.3ab Compliant", no current column | - | reject |
| 10 | HanRun **HR861153C** (C19724782), **HR871150C** (C19724786) | **10/100BASE-TX** despite the "861" part code - both datasheet title blocks read "for 10/100Base-TX PoE application" | HR871150C: 350 mA per centre tap (already on record in `state.json`). HR861153C: image-only sheet, no number | HR871150C raw taps | **reject** - not gigabit, and 350 mA is below the target |

**LCSC coverage note.** A 600-result sweep of LCSC's RJ45 category returns only **six** parts whose
`PoE` attribute is not "Non-PoE": C91754 (incumbent), **C22457393 (LPJG0926HENL)**, C19724782,
C19724786, C54863526 (G-Switch, no datasheet), C9900008492 (JLC-internal, 0 stock).
**C22457393 is the only gigabit PoE part LCSC stocks, and it is the only LCSC part that publishes a
tap current above 600 mA.**

---

## 2. LPJG0926HENL - published specification, with citations

Source: `boards/lumina-carrier/work/mj2/lpjg.pdf`, fetched from
`https://omo-oss-file110.thefastfile.com/portal-saas/new2023111719244971110/cms/file/lpjg0926henl.pdf`
(linked from `https://www.link-pp.com/products/2637.html`; the host 403s without a Referer header).
2 pages, text-extractable. Drawing `LP18022610`, **rev A, 2018-02-26**, title
*"RJ45 Connector with 1000 Base-T Integrated Magnetics For PoE+ Application"*.

### 2.1 The PoE number - the point of the exercise

| Figure | Value | Source |
|---|---|---|
| **DC current rating, power pins** | **720 mA MAX @ 57 VDC, continuous** | p1, `ELECTRICAL SPECFICATIONS @25C`, item **7**: *"DC Current/Voltage Rating pse Pins: 720mA MAX @57VDC(Continuous)"* (sic - "pse" for PSE). The only current-bearing pins on the part are VC1..VC4, so this is the per-tap rating |
| IEEE compliance | **802.3at** | p2 NOTES item 2: *"Meets IEEE802.3at specification."* Title block: *"For PoE+ Application"* |
| **Margin vs 802.3at Type 2** | **1.20x the 0.600 A DC max, 1.05x the 0.686 A peak** | vs `connector-icd.md` s6.1 |
| Hipot | **1500 Vrms MIN** | p1 item 8 |
| Operating temperature | **0 C to +70 C** | p1 item 9 (also LCSC attribute) |
| UL | File **E484635** | p2 NOTES item 5 |

**Honest caveats.**
- The wording is "**pse Pins**", not "per centre tap". The internal schematic has exactly four power
  pins (VC1..VC4), each of which is one transformer's line-side centre tap, so 720 mA per VC pin is
  the only reading that makes sense - but the vendor did not use the words "per centre tap", and
  Wurth did. If the orchestrator wants a bulletproof phrasing, that is a vendor question.
- **Hipot 1500 Vrms is the same as the incumbent HY931147C** and is nominally weaker than Wurth's
  2250 VDC (1500 Vrms is ~2121 V peak, so they are comparable, not 1.5x apart).
- **Operating temperature 0..+70 C is worse than Wurth's -40..+85 C.** If the brief carries an
  extended-temp requirement, this part fails it and the Wurth does not.

### 2.2 Magnetics - and where it is worse than the incumbent

| Property | LPJG0926HENL (p1) | HY931147C | Wurth 7499410213 |
|---|---|---|---|
| Data rate | **1000BASE-T**, 4 x 1CT:1CT, +/-5% | 100BASE-TX, 2 x 1CT:1 | 100BASE-TX, 1:1 +/-2% |
| OCL | **350 uH min @100 kHz/0.1 V, 8 mA DC bias** *plus* **120 uH min @ 18 mA DC bias** | 350 uH min @ 8 mA bias only | 350 uH min, no bias condition printed |
| Insertion loss | -1.0 dB max 1-100 MHz; -1.2 dB max 100-125 MHz | -1.0 dB max | -1.2 dB max |
| Return loss | **-16 (1-40), -12 (40-60), -10 (60-80), -8 (80-100) dB** | -18 / -16 / -14 / -12 | -18 / -14 / -12 / -10 |
| Crosstalk | -30 dB min 1-100 MHz | -30 dB min | -32 / -30 dB |
| CMRR | **-30 dB min 1-100 MHz** | **-35 dB min** | -35 / -32 / -30 dB |

**Two honest negatives:** return loss and CMRR are **worse on paper than the incumbent HY931147C**
(-16 vs -18 dB at the low end; -30 vs -35 dB CMRR). At 100BASE-TX using 2 of 4 pairs this is not a
functional risk, but it is a real de-spec and P8 EMC should know. The **second OCL point at 18 mA DC
bias is a genuine gain** - it is the only OCL-under-PoE-bias number any candidate in this exercise
publishes, and DC bias de-biasing the core is the actual PoE magnetics failure mode.

### 2.3 Internal topology (traced from the p1 schematic at 300 dpi)

- **Four transformers, 1CT:1CT each.** Chip side: TD1+/- = pins 1/2 -> J1/J2 (T568B pair 1,2 = TX);
  TD2+/- = pins 3/6 -> J3/J6 (pair 3,6 = RX); TD3+/- = pins 7/8 -> J4/J5 (spare); TD4+/- = pins 9/10
  -> J7/J8 (spare). Standard T568B - **MDI mapping is identical to the HY931147C**.
- **Pins 4 and 5 (`CT`) are the SAME NET.** A single internal bus commons **all four chip-side centre
  taps** and brings that one node out on both pin 4 and pin 5 (verified: junction dots on the bus at
  all four transformer taps and at both pins). There is no separate TX-CT and RX-CT.
- **Line side: VC1 = pair(J1,J2) CT, VC2 = pair(J3,J6) CT, VC3 = pair(J4,J5) CT, VC4 = pair(J7,J8) CT.**
  So **VC1+VC2 = Mode A** (data pairs) and **VC3+VC4 = Mode B** (spare pairs). Correct arrangement
  for a PD front end; two external bridges commoned onto V48_RAW / V48_RTN restore exactly the
  topology the HY had internally, and nothing downstream of V48_RAW/V48_RTN changes.
- **NO diode bridge.** Confirmed on the schematic and by l-p.com's parametric field `Diodes: No`.
- **Internal Bob Smith / AC termination:** 4 x 22 nF/100 V in series with 4 x 75 ohm, one leg on each
  VC node, commoned to **SHIELD through 1000 pF / 2 kV**. Same as the Wurth part, and the same
  consequence: **`poe.py`'s docstring claim that there is no Bob Smith network becomes wrong**, and
  the external shield hybrid R6 (1M) || C3 (1 nF/2 kV) ends up in *series* with the internal 1 nF.
- **LEDs: pin 15 = GREEN anode, 16 = GREEN cathode (LEFT LED); pin 17 = YELLOW anode, 18 = YELLOW
  cathode (RIGHT LED).** Odd = anode, same convention as the HY. Green 565 nm / yellow 585 nm,
  Vf 1.8-2.6 V @ 20 mA, IR 10 uA max @ 5 V. R7/R8 = 330R from +3V3 are unchanged.

### 2.4 Mechanical

| Item | LPJG0926HENL | HY931147C |
|---|---|---|
| Body D x W x H | **21.25 x 15.93 x 13.30 mm** | 21.60 max x 16.00 x 13.95 max |
| Housing | PBT +30% GF, UL94 V-0 | - |
| Shield | SUS 304-1/2H, 0.2 mm | - |
| Contacts | phosphor bronze C5210R-EH, **gold 6 uin min** in contact area | gold (LCSC attr) |
| Wave solder | 250 C, 5 s | - |

**Smaller than the incumbent in all three axes.** The `connector-icd.md` s7.6 RJ45 relief zone
`(6,0)-(36,26)` on daughters stays valid and stays conservative. **No ICD s7 mechanical change.**
Contact plating is only **6 uin gold** vs HALO/Pulse's 30 uin - low-cost plating, worth noting for a
14-board run but not a blocker.

---

## 3. HALO HFJT1-1GH4P - the 1 A part, and why it is not the pick

Source: `boards/lumina-carrier/work/mj2/halo_gpoe.pdf`,
`https://www.haloelectronics.com/pdf/fastjack-longbody-poe-gigabit.pdf`, revised 03/2024, 2 pages,
text-extractable. Title: *"FastJack 1x1 Tab-Up Gigabit PoE and PoE+ Long Body RJ45"*.

The datasheet has an explicit **"Current Per Pair"** column. Three tiers:

| Family | Std temp (0..70) | Ext temp (-40..+85) | **Current per pair** |
|---|---|---|---|
| HFJT1-1GP-* | HFJT1-1GP-L12RL | HFJT1-1GPE-L12RL | 350 mA |
| HFJT1-1GHP-* | HFJT1-1GHP-L12RL | HFJT1-1GHPE-L12RL | **600 mA** |
| **HFJT1-1GH4P-*** | **HFJT1-1GH4P-L12RL** | **HFJT1-1GH4PE-L12RL** | **1 A** |

Features block: *"IEEE802.3af/at/bt Compliant"*, *"1500Vrms Hi-Pot"*, 30 uin gold, 100% compliance
testing. Circuit A brings out **PW1..PW4 = four raw line-side taps on pins 13-16 - no bridge**, plus
an internal Bob Smith (4 x 75R + 0.1 uF, shield via 1000 pF/2 kV). LED pins 17-20.

**Why it loses, in order of severity:**

1. **"Long Body" = 1.300 in / 33.02 mm deep.** The `connector-icd.md` s7 RJ45 relief zone is 30 mm
   deep. This is a **mechanical/ICD change**, not a BOM swap. All three PoE gigabit HALO families are
   long-body; HALO's short-body gigabit parts (`HFJ11-1Gxx`, `HFJT1-1Gxx`) are **802.3ab only, not
   PoE**, and publish no current column.
2. **20-pin land, not 14.** `16X d0.89` + `4X d1.02` + `2X d3.20` + `2X d1.60`, envelope
   **20.32 x 16.13 mm**. The chip side carries 12 pins (4 pairs + 4 separate chip-side CTs) plus 4
   power pins. **Nothing about the HY931147C footprint is reusable.**
3. **Tab-Up.** The incumbent land has pin 1 adjacent to the left LED in a tab-down body; this is the
   tab-up family. Would need confirming against the mechanical drawing before committing.
4. **Not stocked.** Mouser/Digi-Key list the 350 mA (`1GP`) and 600 mA (`1GHPE`) variants; the 1 A
   `1GH4P` variants do **not** appear in distributor stock. Factory order / MOQ territory. No qty-14
   price obtainable.

So: **the highest published number in this space is HALO's 1 A, and it is unbuyable at qty 14 and
would force an ICD mechanical change.** Recorded for completeness; not recommended.

---

## 4. LPJG0926HENL vs the frozen interface

Ground truth: incumbent = `parts/C91754.json` + `lib/aiee.pretty/RJ45-TH_HY931147C.kicad_mod`
+ `kicad/gen/poe.py`. Candidate = the p1 schematic and p2 "Suggested PCB Layout (Top View)".

### 4.1 Pin-by-pin delta

| Pin | HY931147C (frozen) | net today | **LPJG0926HENL** | net required | Same? |
|---|---|---|---|---|---|
| 1 | RX_P1 (RX winding, <-> J3) | `ETH_RXP` | **TD1+** (TX winding, <-> J1) | `ETH_TXP` | **NO - RX/TX swap** |
| 2 | RX_P2 (<-> J6) | `ETH_RXN` | **TD1-** (<-> J2) | `ETH_TXN` | **NO - RX/TX swap** |
| 3 | RX_CT (chip-side RX tap) | `NC` | **TD2+** (RX winding, <-> J3) | `ETH_RXP` | **NO** |
| 4 | TX_CT (chip-side TX tap) | `+3V3` | **CT** - the common chip-side tap of **all four** transformers | `+3V3` | **function same, meaning changed** (now one node for all 4 pairs) |
| 5 | TX_P5 (TX winding, <-> J1) | `ETH_TXP` | **CT** - **same net as pin 4** | `+3V3` | **NO - becomes a second CT pin** |
| 6 | TX_P6 (<-> J2) | `ETH_TXN` | **TD2-** (<-> J6) | `ETH_RXN` | **NO** |
| 7 | absent from schematic (NC) | `NC` | **TD3+** - chip side of the J4/J5 spare pair | `NC` (unused at 100BASE-TX) | **NO - now a real winding end** |
| 8 | absent from schematic (NC) | `NC` | **TD3-** | `NC` | **NO - as above** |
| 9 | **V+** (common cathode of both internal bridges) | `V48_RAW` | **TD4+** - chip side of the J7/J8 spare pair | `NC` | **NO - rectified output becomes a chip-side winding** |
| 10 | **V-** (common anode) | `V48_RTN` | **TD4-** | `NC` | **NO - as above** |
| **11** | (does not exist) | - | **VC1** - line-side CT of pair J1/J2 (**Mode A**) | `POE_TAP_A1` (new) | **NEW PIN** |
| **12** | (does not exist) | - | **VC2** - line-side CT of pair J3/J6 (**Mode A**) | `POE_TAP_A2` (new) | **NEW PIN** |
| **13** | (does not exist) | - | **VC3** - line-side CT of pair J4/J5 (**Mode B**) | `POE_TAP_B1` (new) | **NEW PIN** |
| **14** | (does not exist) | - | **VC4** - line-side CT of pair J7/J8 (**Mode B**) | `POE_TAP_B2` (new) | **NEW PIN** |
| 11->15 | YELLOW anode | `LED_Y_A` (R7 to +3V3) | **GREEN anode** | anode via R7/R8 | **colour swapped** |
| 12->16 | yellow cathode | `ETH_LED_ACT` | **GREEN cathode** | `ETH_LED_LINK` | **net must move** |
| 13->17 | GREEN anode | `LED_G_A` (R8 to +3V3) | **YELLOW anode** | anode | **colour swapped** |
| 14->18 | green cathode | `ETH_LED_LINK` | **YELLOW cathode** | `ETH_LED_ACT` | **net must move** |
| GND1/2 | shield tabs | `SHIELD` | shield tabs | `SHIELD` | **same** |

Notes:
- The **spare pairs are NOT tied together internally** the way the HY ties J7+J8 and J4+J5. Here they
  are transformer-coupled and their CTs are brought out separately as VC3/VC4. **This is the correct
  gigabit arrangement and works for a Mode B PD**, but it is a topology change from the HY.
- **Pins 7-10 (TD3+/-, TD4+/-) are chip-side winding ends of pairs the W5500 does not use.** Standard
  practice is to leave them open; the line side of those pairs is already terminated by the internal
  Bob Smith network. **No specific incompatibility found** - the part does not require all four pairs
  to be driven or terminated on the chip side.
- **Pins 4 and 5 being one net is the only genuinely new schematic constraint.** It means the
  chip-side taps of the unused pairs sit at +3V3 as well. Harmless (their winding ends float), but
  ERC will see two pins on one net and `poe.py` must wire both to `+3V3`.

### 4.2 Land pattern delta, and the isolation gap

Measured off the p2 "Suggested PCB Layout (Top View)" (render at 300 dpi:
`work/mj2/lpjg_layout.png`, `work/mj2/lpjg_holes.png`).

| Feature | HY931147C (as built, `RJ45-TH_HY931147C.kicad_mod`) | LPJG0926HENL | Delta |
|---|---|---|---|
| Signal holes | 10 x d0.90 (drill 0.900024), two staggered rows of 5, **2.54 pitch, rows 2.54 apart, 1.27 stagger**, 11.43 span | **identical geometry**: 10 x d0.90 rows at 2.54 / stagger 1.27 / span `1.27x9=11.43` | **SAME** |
| Power holes | none | **4 x d0.90 (VC1..VC4)** on two new rows **2.56 mm** and **3.83 mm** below the second signal row; VC1/VC4 aligned with pins 1/10 (span 11.43), VC2/VC3 inboard (span ~6.35) | **+4 NEW PADS** in a band that is empty on the HY footprint |
| LED holes | 4 x d1.10 pads 1.60, outer pair +/-6.63, inner +/-4.09 (spans 13.26 / 8.18) | 4 x **d1.02**, spans **13.26 / 8.18** | **positions SAME**, drill 1.10 -> 1.02 |
| Board lock | 2 x d1.63 (pads 2.029), span 15.50 | 2 x **d1.70**, span **15.75** | **+0.25 mm span, +0.07 drill** - small footprint edit |
| Mounting NPTH | 2 x d3.25, span 11.40, 8.89 below signal row A | 2 x **d3.20**, **8.89** below row A, **3.05** below the board-lock row | **SAME to 0.05 mm** |
| Land envelope | ~16.1 x 15.5 mm | 15.75 wide x 12.95 tall (row A to LED row) | comparable |

**Verdict on the land: the HY footprint is a correct starting point but is NOT reusable unmodified.**
Every existing feature lands within 0.25 mm, but **four pads must be added**. This is a footprint
edit, not a new footprint - and much less work than the HALO part, which shares nothing.

**Isolation gap - the number asked for.**

| Measure | Value |
|---|---|
| HY931147C, live chip-side (P6) to live line-side (P10) | 5.09 mm c-c -> **3.59 mm copper gap** at 1.50 mm pads |
| Wurth 7499410213, P5 (RD-) to P7 (V1+) | 2.54 mm c-c -> **1.05 mm** |
| **LPJG0926HENL, pin 10 (TD4-) to pin 14 (VC4)** | **2.56 mm c-c -> 1.06 mm** at 1.50 mm pads |
| **LPJG0926HENL, nearest *live* chip pin (pin 2, TD1-) to VC1** | **2.86 mm c-c -> 1.36 mm** at 1.50 mm pads |
| HALO app-note guidance at this pitch | 55 mil = **1.40 mm** |

Read that honestly: **the gigabit part does not fix the isolation collapse. 1.06 mm is the Wurth's
1.05 mm.** What it does offer that the Wurth does not is a **mitigation**: the two pads nearest the
48 V nodes (pins 9/10 = TD4+/TD4-) are chip-side windings of a pair the W5500 never uses. If they are
left as isolated no-connect pads with no attached copper - and, better, shrunk from 1.50 mm to 1.30 mm
- the barrier to any *energised* chip-side net rises to **2.86 mm c-c / 1.36-1.56 mm of copper**,
which lands at or above the 1.40 mm guidance. **That is an achievable fix; on the Wurth part it is
not, because there the 2.54 mm neighbour (P5 = RD-) is a live differential signal.**

---

## 5. Cost and availability

| Option | Source | Qty-14 unit | Qty-14 total | Stock | Order/assembly consequence |
|---|---|---|---|---|---|
| **LPJG0926HENL** | **LCSC C22457393** | **$3.7852** (qty-10 break) | **$52.99** | **3,109** | Extended, **Assembly Type = Wave Soldering**. Placed by JLC. **No DNP, no hand solder, single order** |
| HY931147C (incumbent) | LCSC C91754 | $2.1457 | $30.04 | 7,693 | baseline |
| Wurth 7499410213 (current plan) | Digi-Key 732-10839-ND | $9.54 | $133.56 | 2,304 | **off-LCSC: second order + DNP + hand solder x14**, 14-week mfr lead time |
| HALO HFJT1-1GH4PE-L12RL | none found | - | - | **not stocked** at Mouser/Digi-Key | factory order / MOQ |

**Delta vs the current Wurth plan: -$80.57 on parts, minus a second purchase order, minus 14
hand-soldered connectors** - and the tap rating goes from 600 mA to 720 mA.
**Delta vs the incumbent HY: +$22.95** for a published number.

---

## 6. What is unchanged / still owed

- **External bridges are still required** (Mode A across VC1/VC2, Mode B across VC3/VC4, commoned onto
  `V48_RAW`/`V48_RTN`). Same silicon, same ~1.3-1.4 W at the 802.3at operating point, same sizing work
  as the Wurth plan already carries. Nothing downstream of V48_RAW/V48_RTN changes.
- New symbol + new `parts/C22457393.json` grounding file (18 pins).
- Footprint edit: +4 pads, LED drill 1.10 -> 1.02, board-lock 1.63 -> 1.70 at +/-7.875.
- `poe.py`: every `wire_pins("J1", ...)` entry changes; LED nets swap between the 16 and 18 pins;
  the "no Bob Smith network" docstring becomes wrong.
- **Not verified, would need the vendor or a sample:** whether "pse Pins ... 720 mA" is per-pin or
  per-pair-of-pins; and the VC2/VC3 horizontal offset (inferred as +/-3.175 mm from the drawing's
  6.35 dimension - re-measure at footprint-build time).

---

## 7. Files

- `work/mj2/lpjg.pdf` - LINK-PP LPJG0926HENL drawing LP18022610 rev A (the 720 mA source)
- `work/mj2/lpjg_s-1.png`, `lpjg_sch.png`, `lpjg_sch_l.png`, `lpjg_led2.png` - p1 schematic renders
- `work/mj2/lpjg_p-2.png`, `lpjg_layout.png`, `lpjg_holes.png`, `lpjg_dims.png` - p2 land pattern renders
- `work/mj2/halo_gpoe.pdf`, `halo_p-2.png` - HALO long-body gigabit PoE FastJack (the 1 A source)
- `work/mj2/pulse_j432.pdf` - Pulse J432 gigabit PoE+ (no current column - the rejection evidence)
- `work/mj2/we_gig.pdf` - Wurth 7499111001A gigabit (no PoE block at all)
- `work/mj2/hr861153c.pdf`, `hr871150c.pdf` - HanRun "gigabit-looking" parts that are 10/100
- `work/mj2/fastjack-gigabit.pdf`, `fastjack-tabup-gigabit.pdf` - HALO short-body gigabit, non-PoE
- `work/mj2/rj_*.json` - the 600-part LCSC RJ45 sweep
