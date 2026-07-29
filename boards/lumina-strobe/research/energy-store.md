# energy-store - the 48 V flash capacitor bank (LUM-DTR-STROBE-A)

Ranked candidates for the ~2,800 uF / 100 V bank. All parts verified live on LCSC/JLCPCB via
`parts_search.py` on 2026-07-28; stock figures are that day's. Machine-readable copy:
`energy-store.json`.

**Headline:** the bank is easy. Ripple and ESR - the two things STR-REQ-08 says are most likely
to be got wrong - come out with 7-9x and 70x margin respectively once the arithmetic is done.
What actually constrains this block is **endurance at 56-69 C, can height against an undefined
enclosure ceiling, and the fact that no JLC Basic part exists at 100 V in any capacitor
technology.**

---

## 1. The duty, computed (this drives everything below)

Peak discharge 2.6 A. Pulse width is not a free variable - it is set by the energy the rail can
replace, so it falls out of the ICD's own numbers.

| Case | Energy/flash | Charge Q | Pulse width | Rate | Duty | Cap RMS ripple |
|---|---|---|---|---|---|---|
| af, full window | 0.99 J | 22.5 mC | 8.65 ms | 8.6 Hz | 7.4% | **0.68 A** |
| af, governed at 25 Hz | 0.34 J | 7.7 mC | 2.97 ms | 25 Hz | 7.4% | **0.68 A** |
| at, full window | 0.99 J | 22.5 mC | 8.65 ms | 18.8 Hz | 16.3% | **0.96 A** |
| at, governed at 25 Hz | 0.74 J | 16.8 mC | 6.47 ms | 25 Hz | 16.2% | **0.96 A** |
| opening burst (bank full, governor not yet limiting) | 0.99 J | 22.5 mC | 8.65 ms | 25 Hz | 21.6% | 1.14 A, **< 1 s** |

`I_rms^2 = D*(I_pk - I_rail)^2 + (1-D)*I_rail^2`, with `I_rail = P_sustained / 48 V`
(0.177 A af, 0.385 A at). The RMS is rail-bounded, exactly as requirements section 4 says:
duty is ~7.4% (af) / ~16% (at) regardless of flash rate, because the governor trades rate
against energy. **Design number: 0.96 A rms.**

### The frequency correction is the trap

A 3-9 ms pulse repeating at 8.6-25 Hz puts essentially all of its RMS energy **below ~120 Hz**
(envelope corner `1/(pi*tp)` = 37-107 Hz). The sub-millisecond edges add spectrum above 1 kHz
but carry negligible RMS energy. So the datasheet's 100 kHz headline figure **must not** be used
directly - apply the 50 Hz coefficient:

| Frequency | Ymin LKM coefficient | Nichicon UHE (390-1000 uF) |
|---|---|---|
| 50 Hz | **0.40** | **0.65** |
| 120 Hz | 0.50 | 0.75 |
| 1 kHz | 0.80 | 0.98 |
| 10-50 kHz | 0.90 | 1.00 |
| 100 kHz | 1.00 | 1.00 |

Ymin also publishes an **ambient temperature** multiplier (LKM catalogue): 50 C x2.1, 70 C x1.8,
85 C x1.4, 105 C x1.0. At 69 C the interpolated factor is 1.81.

So the derating chain for a Ymin part is `rated_100kHz x 0.40 x 1.81` at the `at` ambient, and
`x 0.40 x 2.01` at the `af` ambient. The tables below quote both that and a
**zero-temperature-credit** figure (`x 0.40` only) so nothing rests on the temperature multiplier.

---

## 2. Radial-leaded (THT) aluminium electrolytic, 100 V - the answer

| # | LCSC | MPN | Brand | Cap | Case (DxL) | Height max | Basic? | Stock | $ @6 | $ @100 | Ripple rating | ESR 120 Hz / 100 kHz | Endurance | Rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **C443164** | **LKMJ2502A681MF** | Ymin | 680 uF | D18 x 25, 7.5 mm | **27.0 mm** | Extended | 9,472 | **$0.7472** | $0.5374 | **2860 mA @105 C/100 kHz** | 176 / 30 mohm | **10,000 h @105 C**, AEC-Q200 | **TOP PICK.** Shortest 680 uF/100 V can with both a published ripple figure and 10,000 h. 4 of them = 2,720 uF for $2.99. |
| 2 | C443161 | LKMJ2002A471MF | Ymin | 470 uF | D18 x 20, 7.5 mm | **22.0 mm** | Extended | 3,001 | $0.7634 | $0.5487 | 2270 mA @105 C/100 kHz | 254 / 42 mohm | 10,000 h @105 C, AEC-Q200 | **RUNNER-UP.** 5 mm shorter; 6 hit 2,820 uF exactly. Same series, same footprint family. |
| 3 | C22388844 | OLKJ2502A681MF | Ymin | 680 uF | D18 x 25, 7.5 mm | 27.0 mm | Extended | 290 | $0.6956 | $0.4955 | 2050 mA @105 C/100 kHz | 176 / - | 8,000 h @105 C | Drop-in second source for #1 on the identical footprint. Stock too thin to be first choice. |
| 4 | C18164658 | NXH100VB470M16*31.5 LO | SamYoung | 470 uF | D16 x 31.5, 7.5 mm | 33.5 mm | Extended | 4,556 | $0.8828 | $0.5907 | 2400 mA @105 C/100 kHz | 254 / 33 mohm | 10,000 h @105 C | Smaller diameter, good stock - but **33.5 mm busts the 30 mm ceiling**. |
| 5 | C340710 | UHE2A681MHD | Nichicon | 680 uF | D18 x 31.5, 7.5 mm | 33.5 mm | Extended | 403 | $1.4637 | $0.9893 | 1890 mA @105 C/100 kHz | 156 / 40 mohm | 10,000 h @105 C | Best-documented part here (full catalogue tables, used above for the cross-check). 2x price, 6.5 mm taller, thin stock. Reference, not the buy. |
| x | C721247 | ERS1KM471L25OT | AISHI | 470 uF | D16 x 25 | 27.0 mm | Extended | 11,520 | $0.4955 | $0.2744 | **not published** | not published | **not published** | **REJECTED.** Cheapest with deepest stock, but no ripple and no endurance figure - fails STR-REQ-08's "ripple current must appear explicitly in the BOM". |
| x | C1579637 | UVR2A102MHD | Nichicon | 1000 uF | D18 x 40 | 42.0 mm | Extended | 1,522 | $1.7607 | $1.1991 | 1380 mA @85 C/120 Hz | - | **2,000 h @85 C** | **REJECTED - the worked bad example.** An 85 C part in a 69 C box extrapolates to ~6,100 h (8 months continuous). Also 42 mm tall. No 85 C-rated part belongs on this board. |

**Volumetric reality check.** From the Nichicon UHE and Ymin LKM 100 V tables, a 105 C / 10,000 h
part at 100 V tops out at ~680 uF in D18x25 and ~1000 uF in D18x35.5. Every **1500 uF / 100 V**
part searched (TDK, Nichicon, Cornell Dubilier, Rubycon, Panasonic - 92 hits) is **zero stock**.
So 680 uF in a 25 mm can is close to the practical ceiling, and 4-6 parts is the right count.

**THT cost implication.** These are through-hole. Per requirements section 7 / open question 6
(default = hand-solder the reverse-mounted sockets locally), the bank rides along in the same
process for free: 8 extra hand joints on a 4-6 board build. If open question 6 instead resolves
to full JLC assembly, the bank needs JLC's THT service or must move to section 3's SMD parts.

---

## 3. SMD (V-chip) aluminium electrolytic, 100 V - it exists, but thinly

**Does the combination exist in SMD at all?** Yes, but the ceiling is 470 uF and there are
exactly **four** 470 uF/100 V SMD parts on LCSC, three of which have <200 in stock.

| LCSC | MPN | Brand | Cap | Case | Height | Stock | $ @6 | $ @100 | Ripple | Endurance | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C249675 | VEJ471M2ATR-1821 | Lelon | 470 uF | SMD D18 x 21.5 | 21.5 mm | 621 | $1.3492 | $0.8860 | **not on LCSC** | 2,000 h @105 C | Largest 100 V SMD in stock. 6 needed = **$8.10 @qty6** - blows the ~$8 bank budget on its own. Ripple must be pulled from the Lelon datasheet before BOM release. |
| C487445 | VKML2102A221MV | Ymin | 220 uF | SMD D12.5 x 21 | 21.0 mm | 1,349 | $0.7601 | $0.5552 | **1620 mA @105 C/100 kHz** | **10,000 h @105 C** | Only SMD candidate with both a published ripple figure and 10,000 h. But **13 needed** for 2,860 uF: $9.88 @qty6, 1,861 mm2, 26 terminals. |
| C249884 | VZH221M2ATR-1816 | Lelon | 220 uF | SMD D18 x 16.5 | **16.5 mm** | 1,704 | $1.0199 | $0.7488 | not on LCSC | 5,000 h @105 C | Shortest 100 V electrolytic found anywhere. The escape hatch if the enclosure ceiling collapses to ~20 mm. |
| C53050029 | EFVH100ADA471M16N0 | FOLLON | 470 uF | SMD D16 x 21.5 | 21.5 mm | 196 | $1.6574 | $1.0780 | not on LCSC | 2,000 h @105 C | Stock too thin for a 6-board build with spares. |

**Verdict:** SMD is JLC-PCBA-friendly and 5-6 mm shorter, but costs 2.7-3.3x the THT bank and
either sacrifices endurance (Lelon, 2,000 h) or triples the part count (Ymin 220 uF x13). Only
worth it if open question 6 closes as "no hand soldering at all".

---

## 4. Aluminium polymer / hybrid, 100 V - **does** stock, but not as bulk

Contrary to the usual assumption, JLC **does** carry 100 V polymer aluminium - 88 hits, several
with deep stock. The limit is capacitance per part.

| LCSC | MPN | Cap | Case | Height | Stock | $ @6 | $ @100 | Ripple | ESR | Endurance |
|---|---|---|---|---|---|---|---|---|---|---|
| C54915544 | PA100V220M12X17 (jieerrui) | **220 uF** | D12.5 x 17 THT | 19.0 mm | 2,814 | $0.9086 | $0.6552 | 3500 mA @100 kHz | 30 mohm | 2,000 h @105 C |
| C53120975 | PA100V150M10X17 (jieerrui) | 150 uF | D10 x 17 THT | 19.0 mm | 8,267 | $1.1813 | $0.8715 | 3100 mA @100 kHz | 40 mohm | 2,000 h @105 C |
| C46550452 | PA100V100M10x12 (jieerrui) | 100 uF | D10 x 12.5 THT | 14.5 mm | **136,792** | $0.6004 | $0.4454 | 2600 mA @100 kHz | 40 mohm | 2,000 h @105 C |
| C48970690 | RYHV100V68UF10*10 (Honor) | 68 uF | SMD D10 x 10.5 | 10.5 mm | 7,515 | - | - | - | - | 2,000 h @105 C |

**Verdict: not for bulk.** 220 uF is the largest 100 V polymer part in stock, so 2,800 uF costs
**13 parts, $11.81/board and 1,861 mm2** - 4x the money and 1.6x the area of the aluminium bank,
buying ESR the design does not need (see section 6). Worse, these 100 V polymer parts are rated
only **2,000 h @105 C**, so polymer's usual life advantage is absent in this vendor's 100 V line.
Keep 1-2 in the back pocket only if the drive stage later demands lower loop impedance than
MLCC can give.

---

## 5. Bulk MLCC, 100 V - the fast-edge companion, with the DC-bias number

| LCSC | MPN | Brand | Nominal | Case | Stock | $ @6 | $ @100 | DC bias at 48 V | Note |
|---|---|---|---|---|---|---|---|---|---|
| **C576517** | **GRM32EC72A106KE05L** | Murata | 10 uF 100 V X7S | 1210, 3.2 x 2.5 x **2.5 mm** | 281,142 | $0.7972 | $0.6052 | **-73% -> 2.7 uF** | **PICK.** The only one with a published, readable DC-bias curve. -55 to +125 C. |
| C5156756 | FS32X106K101EGG | PSA | 10 uF 100 V X7R | 1210 | 290,274 | $0.6665 | $0.4632 | no published curve | $0.13 cheaper for an unsourced derating. Not worth it. |
| C342614 | C3225X7S2A475KT000N | TDK | 4.7 uF 100 V X7S | 1210 | 7,748 | $1.2959 | $0.9925 | not read | Half the CV at 1.6x price. Second source for the footprint only. |

### DC-bias derating - read off Murata's own chart, not assumed

Source: Murata Product Search Data Sheet for `GRM32EC72A106KE05#`, "DC bias characteristics"
chart (fetched via <https://www.farnell.com/datasheets/3412500.pdf>, chart image read directly).

| DC bias | Cap change | Effective C |
|---|---|---|
| 0 V | +3% | 10.3 uF |
| 20 V | -40% | 6.0 uF |
| 40 V | -68% | 3.2 uF |
| **48 V (nominal rail)** | **-73%** | **2.7 uF** |
| **57 V (802.3 worst case)** | **-79%** | **2.1 uF** |
| 100 V (rated) | -90% | 1.0 uF |

**So "4 x 10 uF of ceramic" = 40 uF nominal = ~11 uF effective at 48 V.** Anyone who budgets the
nameplate value is out by 3.7x. This is exactly the effect the ICD cites in rejecting 63 V parts.

ESR from the same datasheet's R-vs-frequency chart: ~1.5 ohm at 100 Hz, ~100 mohm at 1 kHz,
~5 mohm at 100 kHz, ~2 mohm at 300 kHz-1 MHz. That shape is the whole point: **the MLCCs are
invisible at the pulse repetition rate and dominant at the edge.** They contribute ~0.4% of the
bank energy and ~all of the sub-microsecond source impedance. Murata's temp-rise-from-ripple
chart shows ~2 A rms at 80 kHz for ~4 C rise, so 4 of them are not stressed.

**Placement caution:** 1210 is a large body and this board has a 30 x 26 mm notch cut into it.
Keep the MLCCs away from the board edge, the notch edge and the mounting holes, and orient the
long axis perpendicular to the likely flex direction.

---

## 6. Film - not credible, stated plainly

| LCSC | MPN | Cap | Case | Stock | $ @6 |
|---|---|---|---|---|---|
| C49215602 | MEB106K2A1501 (KYET) | 10 uF 100 V metallised polyester | P = 15 mm THT box | 972 | $1.0571 |

This is the **only** 100 V / 10 uF film part on LCSC with real stock. Every 22 uF / 100 V
polypropylene part (WIMA MKP4D and MKP1D families, 11 variants) is **zero stock**.

2,800 uF of film would take **280 of these**, roughly $296 and several litres of volume. Film is
~100x worse than aluminium in volumetric efficiency at 100 V. **It is not an option for the
energy store.** Film's only legitimate role on this board is a 0.1-1 uF snubber across the drive
stage - that is the drive stage's decision, not this block's.

---

## 7. Recommended bank composition

### Primary: 4 x C443164 + 4 x C576517

| Property | Value |
|---|---|
| Bulk | 4 x Ymin **LKMJ2502A681MF** (C443164), 680 uF / 100 V, D18 x L25, 7.5 mm pitch |
| HF | 4 x Murata **GRM32EC72A106KE05L** (C576517), 10 uF / 100 V X7S 1210 |
| Total capacitance | **2,720 uF** (-2.9% vs the closed 2,800 uF; inside the +/-20% tolerance band) plus ~10.8 uF effective ceramic |
| Energy 48 -> 40 V | **0.957 J** (vs 0.99 J spec, -3.3%) |
| Energy 0 -> 48 V | **3.13 J** |
| Bank ESR | **43.9 mohm at 120 Hz** (worst case, from tan d <= 0.09) / **7.5 mohm at 100 kHz** |
| **IR sag at 2.6 A** | **0.114 V** = **1.43% of the 8 V usable window** |
| **Ripple capability** | **4.58 A** with zero temperature credit, **8.31 A** at 69 C, 9.20 A at 56 C |
| **Ripple margin** | **8.7x** against the 0.96 A `at` design case (4.8x even with no temperature credit) |
| Self-heating | 5-10 mW per can; core temperature = ambient within ~0.5 C |
| Height | **27.0 mm** (25 mm can + 2.0 mm sleeve tolerance per the LKM dimension table) |
| Board area | **1,214 mm2** = 15.2% of the 100 x 80 board |
| Part count | 8 (4 THT cans / 8 holes, 4 MLCC) |
| Cost @ qty-6 price break | **$6.18 / board** ($2.99 electrolytic + $3.19 MLCC) |
| Cost @ qty-100 break | **$4.57 / board** |
| Real 6-board build (24 pcs -> qty-10 break) | **$5.28 / board** |
| Endurance | 10,000 h @105 C -> **299,000 h at 56 C** (34 yr) / **121,000 h at 69 C** (13.8 yr) |
| Stock headroom | 9,472 cans = 2,368 boards; 281k MLCC |

### Runner-up: 6 x C443161 + 4 x C576517

2,820 uF exactly (0.993 J), **22.0 mm tall**, bank ESR 42.3 mohm / 7.0 mohm, IR sag 0.110 V,
ripple capability 9.89 A at 69 C, 1,781 mm2, 10 parts, **$7.77 @qty6 / $5.71 @qty100**.
Same series, same endurance. **Take this one if the enclosure ceiling is under ~28 mm**, or if
hitting 2,800 uF on the nose matters more than $1.60 and two extra solder joints.

### The layout recommendation that matters more than the part choice

**Lay out six D18 / 7.5 mm-pitch radial footprints and populate four.** That:
- second-sources the whole bank (the D18x25 footprint at 470 uF is available from Ymin,
  SamYoung C2835738, Rubycon C1582113 and NCC C705509 - four vendors - whereas 680 uF at that
  size is Ymin-only);
- gives the architect a 2,720 -> 4,080 uF capacitance knob with no respin;
- costs 4 unpopulated footprints of board area and nothing else.

Placement constraints for P6: **no aluminium electrolytics in (2,46)-(36,68)** (748 mm2 of
otherwise-prime central area), nothing in the antenna column (88,25)-(100,55), clear of the
notch (6,0)-(36,26) and the recovery header (76,0)-(98,20). A 2x2 array of D18 cans on 22 mm
centres needs ~44 x 44 mm; that fits comfortably in what remains, but the D18 cans and the
DC-DC keepout together mean the bank wants the right-centre of the board.

---

## 8. Answer to the architect's bounded question: what does 4x (~12,000 uF) cost?

Numbers only, no recommendation.

| | Option G1: more of the same | Option G2: bigger cans |
|---|---|---|
| Part | 18 x C443164 (680 uF, D18x25) | 12 x C724666 (AISHI 1000 uF/100 V, D18x35, 2,000 h @105 C, stock 8,043) |
| Capacitance | 12,240 uF | 12,000 uF |
| Energy 48 -> 40 V | 4.31 J | 4.22 J |
| **Cost / board** | **$13.45 @qty6, $8.42 @qty100** | **$10.53 @qty6, $7.51 @qty100** |
| **Board area** | **5,104 mm2 = 64% of the whole board** | **3,402 mm2 = 43% of the board** |
| **Height** | 27.0 mm | **37.0 mm - busts the 30 mm ceiling** |
| **Part count** | 18 cans, 36 THT holes | 12 cans, 24 THT holes |
| Endurance at 69 C | 121,000 h | 24,300 h |
| **Verdict** | Does not fit. An 18 mm can on 22 mm pitch needs a 6x3 grid = 132 x 66 mm; the board is 100 x 80 with 2,328 mm2 already removed by the notch, the DC-DC keepout, the antenna column and the recovery header. | Marginally fits the raw outline (4x3 grid = 88 x 66 mm) but not around the keepouts, and it is 7 mm over the height ceiling. |

Three further consequences the architect should have in front of them:

1. **12,000 uF does not buy the flash STR-REQ-01 asks for.** At 2.6 A over the 8 V window,
   12,000 uF holds full output for `C*dV/I` = **36.9 ms**, not 100-200 ms. Reaching 100 ms needs
   **32,500 uF**; 200 ms needs **65,000 uF**. Neither is buildable inside 100 x 80 x 30 mm at
   100 V - that is a second board or a different enclosure, and it confirms open question 2's
   "roughly 10x" estimate rather than the 4x framing.
2. **It changes nothing about sustained rate.** The rail still delivers 8.5 W (af). A 4x bank
   buys one longer accent, then recharges 4.3x more slowly. Cold-start charge time goes from
   0.54 s to ~2.3 s at the ICD sustained limit.
3. **It moves three other blocks.** Inrush limiting (STR-REQ-09) must hold the PD under 1.0 A
   against 4.3x the charge; the mandatory bleed path's time constant grows 4.3x; and the stored
   energy hazard goes from **3.23 J to 13.8 J**, which is a section 8.3 silkscreen and
   service-procedure change, not just a BOM change.

---

## 9. Risks

1. **Standard electrolytic datasheets explicitly exclude this duty.** SamYoung's NXH sheet
   (page 4, item 5) - and most general-purpose aluminium electrolytic sheets - state: *"The
   electrolytic capacitor is not suitable for circuits in which charge and discharge are
   frequently repeated. If used in such circuits, the capacitance value may drop, or the
   capacitor may be damaged. Please consult our engineering department."* This board **is** a
   repetitive charge/discharge circuit. Mitigating facts, in order of weight: the bank swings
   only 48 -> 40 V (17% of rating, never to zero, unlike a photoflash cap); peak is 2.6 A into
   >=2,720 uF, i.e. **0.65 A per can, ~0.96 mA per uF**, versus the amps-per-uF a photoflash duty
   implies; and the computed RMS sits 5-9x below the fully derated rating. **This is the
   caveat to put in front of the human**, and the reason to buy the 10,000 h AEC-Q200 part
   rather than the 2,000 h generic when they cost the same.
2. **No JLC Basic part exists.** Verified: `--basic-only` returns **zero** results for both
   "100 V aluminium electrolytic" and "100 V 1210 X7R". Every part in this block is Extended,
   so JLC's per-part setup fee applies - and on a 4-6 board build that fee can exceed the
   component cost. This strengthens the case for hand-fitting the bank (open question 6 default).
3. **THT vs assembly process.** Radial cans land in the same question as the reverse-mounted
   sockets. Default (a) - top-side SMD at JLC, hand-solder the THT locally - makes the bank
   process-free. Any move toward full JLC assembly forces section 3's SMD parts and costs either
   endurance (Lelon, 2,000 h) or part count (13 x 220 uF).
4. **Height against an undefined ceiling.** Open question 5's default is 30 mm; the primary bank
   spends 27.0 mm of it, leaving 3 mm. That is tight for a not-yet-designed enclosure. Fallbacks
   in order: 22.0 mm (runner-up, 6 x C443161), 21.0 mm (13 x C487445 SMD), 16.5 mm
   (13 x C249884 SMD). Below ~16 mm nothing in the 2,800 uF / 100 V class exists and the energy
   budget has to come down.
5. **Single source at 680 uF / D18x25.** Only Ymin makes it (LKM and OLKJ, and OLKJ stock is
   290). Mitigated by the six-footprint layout in section 7 - the D18 / 7.5 mm footprint at
   470 uF is four-vendor.
6. **MLCC DC bias is not optional arithmetic.** 10 uF reads 2.7 uF at 48 V and 2.1 uF at 57 V.
   Any downstream calculation that uses the nameplate value is wrong by ~3.7x.
7. **Keepout interaction.** Aluminium electrolytics are banned from (2,46)-(36,68). MLCC and
   polymer are not aluminium electrolytics by the letter of the rule, but the rule exists because
   1.25 W dissipates 11 mm below in a sealed box - keep life-sensitive parts out of that zone
   regardless of technology.
8. **No datasheet URL on LCSC** for C54915544 / C46550452 (jieerrui 100 V polymer) or C49215602
   (KYET film). Their figures above come from the LCSC parametric attributes only. None is
   recommended, but P3 must obtain a real datasheet before any of them enters a BOM.
9. **Vent orientation.** D18 cans have a top-face pressure-relief vent. In a sealed plastic
   enclosure a vent event dumps electrolyte inside the box. Point the vents away from the LED
   wiring and the connectors. Pair this with the section 8.3 stored-energy silkscreen warning
   (3.13 J with the cable unplugged) and the defined bleed time constant.

---

## 10. What this block did NOT do

Did not pick the final parts (P3's part-sourcer), did not size the inrush limiter or the bleed
resistor (STR-REQ-09 / STR-REQ-10, drive/protection blocks), did not place anything, and did not
design the drive stage whose loop inductance - not the bank's ESR - actually sets the optical
edge rate for STR-REQ-11.

**Sources:** Ymin LKM series catalogue (pp. 99, 101-102; ripple/impedance tables and both
correction-factor tables); Nichicon UHE series datasheet CAT.8100H (pp. 221-225; frequency
coefficient table and the 100 V ratings table); SamYoung NXH series approval sheet 710-002;
Murata Product Search Data Sheet GRM32EC72A106KE05# (DC bias, ESR-vs-frequency and
temp-rise-from-ripple charts). All stock, pricing and Basic/Extended status from live
`parts_search.py` queries against LCSC/JLCPCB on 2026-07-28.
