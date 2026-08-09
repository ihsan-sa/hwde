# components.md - rf-term-150w (P1 component research)

Scope: 3 functions only - termination resistor, SMA female jack, shunt trimmer capacitor.
No schematic/footprint/layout design here (P2+). Sourced live against LCSC (`parts_search.py`)
and DigiKey product pages (web); every price/stock figure below is cited with the page read.

**HEADLINE FINDING - read this first:** the $40/build-of-5 budget cannot be met. The cheapest
verified-in-stock, spec-compliant termination resistor alone costs **$122.00 for 5 units**
(3x the entire cap), and the cheapest spec-compliant trimmer adds another **$44.42 for 5**.
`requirements.md` section 6 predicted this ("$20-60 each... could exceed the entire $40 cap by
several times") - this research confirms it and supplies the real number. See "Budget roll-up."

**Requirements-vs-assignment note:** my task brief said trimmer voltage `>= 200 V`;
`boards/rf-term-150w/requirements.md` (the approved requirements doc, section 1/8/10-crit.7) is
stricter: **`>= 250 V working, and rated for continuous RF (not just DC) at 25 MHz`**. I used the
250 V floor from requirements.md as the binding one (it's the more authoritative, more specific,
arithmetically-derived source) and flag every candidate against it below. No in-stock LCSC/DigiKey
trimmer clears 250 V with margin - the best available sits exactly at the 250 V floor. Architect/P3
must decide if that's acceptable or if the design needs a different adjustment topology.

---

## 1. Termination resistor - 50 ohm, >=250 W (not 150 W - see note), flange bolt-down

**Why >=250 W, not 150 W:** `requirements.md` section 3 derives this from the derating-curve
arithmetic: a part rated exactly 150 W has **zero** allowed flange temperature rise at 150 W
operation with a 25 C ambient (`T_flange_allowed = T_max - (150/150)*(T_max-T_ref)` collapses to
`T_ref` itself if `P_op = P_rated`, which leaves `Rth_max = 0`, i.e. no finite heatsink works).
The termination element must be rated **>=250 W** at its datasheet reference flange temperature.
This is corroborated by every real derating curve found below (all "100% power" plateaus end at
100 C flange, and 150 W-rated parts leave zero headroom at 150 W dissipation, 25 C ambient).

### Recommendation (PRIMARY): Vishay / Barry Industries T50R0-250-12X

250 W BeO flanged **termination** (RF-tuned, not just a bare resistor element), 50 ohm.

| Field | Value | Source |
|---|---|---|
| MPN / mfr | T50R0-250-12X / Vishay Intertechnology (Barry Industries brand) | datasheet, DigiKey |
| Distributor | **DigiKey** PN `4353-T50R0-250-12X-ND` | https://www.digikey.com/en/products/detail/vishay-barry/T50R0-250-12X/22111433 (read 2026-08-08) |
| Stock | **139 units** (live page read) | same URL |
| Price | qty 1 = **$24.40**; next break qty 16 = $20.56. Qty-5 falls in the qty-1 tier -> **$24.40/ea** | same URL |
| **Qty-5 extended** | **5 x $24.40 = $122.00** | computed |
| Resistance / tolerance | 50 ohm **+/-5%** | datasheet (Barry PN T50R0-250-12X) |
| Power rating | **250 W**, rated at flange temperature <=100 C constant | datasheet p.1 |
| Derating curve | Flat 100% from 25-100 C flange, linear to 0% at 150 C. Slope = -250 W / 50 C = **-5 W/C**. Zero-power temp = **150 C**. Implied Rth (element-to-flange, back-calculated from the slope, NOT a published Rth spec) = (150-100)/250 = **0.20 C/W** | datasheet derating chart, read + transcribed |
| Frequency / return loss | DC - 4 GHz; Return Loss (typical) >=16 dB in a matched 50 ohm system | datasheet |
| Construction | Thick film on **BeO** (beryllium oxide) ceramic; silver-plated copper flange and leads | datasheet |
| Operating temp | -55 to +150 C | datasheet |
| Mechanical (L x W x H) | 24.77 x 9.53 x 3.56 mm max (0.975 x 0.375 x 0.140 in) | datasheet dimension drawing |
| Flange holes | 2x, Ø3.30 mm (0.130 in), hole-center spacing 18.42 mm (0.725 in) along the long axis, holes on the width centerline (4.75 mm from each long edge) | datasheet dimension drawing |
| Lead / tab | 3.05 mm wide x 0.127 mm thick, positioned 2.67 mm ("0.105 in") from the bottom (mounting) face per the side-view callout - read as the closest available proxy for tab height above the mounting plane; **P2 should confirm from the vendor STEP model before committing to the co-planarity detail** | datasheet dimension drawing |
| Datasheet saved | `research/T50R0-250-12X_Vishay-Barry_datasheet.pdf` | fetched from https://barryind.com/pdf/Terminations/Power_Flange/T50R0-250-12X.pdf |

**Flags against requirements:**
- **FAILS the <=2% DC-resistance-tolerance intent** (A7 / task brief): only +/-5% is a catalog,
  in-stock item. Tighter tolerances are "contact factory" special-order on every RF-flange part
  found in this whole category (see section 4) - not available "in stock now" anywhere searched.
  Per `requirements.md` criterion 1, the +/-2% target is met by resistance tolerance alone; a
  +/-5% part pushes that criterion out of spec on paper, though section 1's own reflection-budget
  math shows resistance tolerance was never the binding constraint (residual inductance is) -
  **this is an architect call, not something I can resolve as P1.**
- **BeO substrate hazard**: beryllium oxide ceramic is toxic if ground, machined, or the sealed
  element is broken/crushed. This is a standard, sealed, "Covered Resistor Element" commercial/mil
  part (safe under normal handling and mounting) but the README/build docs should carry a
  do-not-machine-or-crush note and normal e-waste handling caution.
- **Working voltage not explicitly published** for the T-series (termination) SKU. The sibling
  R/RA-series (bare resistor element, same materials/construction) publishes "Max. Rated Voltage:
  950 VDC" (see `RA50R0-150-8X` datasheet, disqualified-on-tolerance copy saved in this folder) -
  reasonable to infer similar headroom for T-series, but **unconfirmed for this exact part;
  P2/P3 should get written confirmation from Vishay if this becomes load-bearing.**
- Oversized relative to the *task brief's* "150 W (or more)" framing, but *exactly* the class
  `requirements.md` section 3 proves is the **minimum** viable power rating - not gold-plating.

### Backup: Vishay / Barry Industries T50R0-500-10X (same family, more margin, pricier)

| Field | Value | Source |
|---|---|---|
| MPN | T50R0-500-10X | DigiKey |
| Distributor | DigiKey PN (Vishay Barry listing) | https://www.digikey.com/en/products/detail/vishay-barry/T50R0-500-10X/22111440 (read 2026-08-08) |
| Stock | 49 units | same URL |
| Price | qty 1 = $65.74; qty 10 = $59.52 | same URL |
| **Qty-5 extended** | **5 x $65.74 = $328.70** | computed |
| Resistance / tolerance | 50 ohm +/-5% | listing |
| Power | 500 W (2x the 250 W floor - more thermal headroom, same family/construction as primary) | listing |

Only useful if the primary goes out of stock - it is not cheaper. Included because it's the next
confirmed-in-stock, correctly-constructed part in the same product family, not because it's a
good value.

**Other family members checked and ruled out:**
- `R50R0-1200-1X` (1200 W, BeO): in stock 12 @ DigiKey, but **$233.10/ea** - far worse value, only
  useful if 500 W is somehow insufficient (it will not be).
- `R50R0-800-1X` (800 W, BeO): **0 stock** at DigiKey, 14-week lead time - disqualified ("in stock
  now").
- `RA50R0-150-8X` (150 W, AlN, Barry Industries, ±5%): full datasheet pulled (saved in this
  folder) - clean derating curve (flat to 100 C flange, linear to 0 at 150 C, i.e. -3 W/C,
  implied Rth 0.33 C/W) and dimensions, but **not listed at DigiKey at all** (search + direct
  product-ID probing both came up empty) and **not on LCSC** (0 stock under every query tried).
  Also fails the >=250 W floor per requirements.md section 3. Kept in `research/` for reference
  only - do not use.

### Disqualified candidates (checked, rejected, with reason)

| Candidate | Why rejected |
|---|---|
| Kyocera AVX / ATC **FT10870N0050J01/J02/J03** (150 W, thin film on AlN, tantalum-nitride element, ±5% std / ±2% "consult factory") | Best-matched electrically (150 W is under the >=250 W floor anyway) but **0 units in stock at DigiKey, 20-week lead time**; not listed at LCSC at all. Full 30-page catalog (`TDS-HPRES-0007`) read for every dash-number 20 W-250 W in the FT series - none are stocked today. |
| Kyocera AVX **FR10975N0050J01** (250 W, AlN, ±5%) | Same family/fab as FT series - **0 stock, 20-week lead time** at DigiKey (confirmed via the sibling `FR10975N0100J01`, same pattern). Only available with real stock at a European reseller (rf-microwave.com, 89 units, EUR18.96 ea) which is neither LCSC nor DigiKey - out of policy. |
| Anaren/TTM **RFP-150N50TE** / LCSC listings `E150N50X4`, `E150N50X4E`, `A150N50X4*` | **0 stock at LCSC** (every SKU checked). Also its only public datasheet excerpt (via a reseller page) states **no derating curve, no Rth published** - would be disqualified on that alone per the assignment's hard rule even if stock existed. |
| Vishay Dale **NH-250 / BC20-00204** ("Non-Inductive" 50R, 250 W, ±1%) | The NH/RH product family is fundamentally a **wirewound** resistor line (bifilar/Ayrton-Perry "non-inductive" winding). Even the best non-inductive windings retain hundreds of nH to low-uH of residual inductance at this power/size class - `requirements.md`'s post-tune budget is **<=32 nH total**. A winding-based element would consume the entire reactance budget by itself before the trimmer does anything. Rejected on construction, not on the marketing label. |
| Vishay **RPS0250** series (thick film, chassis mount, screw terminal) | Real family, genuinely thick-film/non-inductive, but **no 50 ohm SKU found** in the values checked (68R, 220R, 270mR, 1000R only) across DigiKey/RS/Mouser search. Would be worth a manufacturer-direct check if this path is pursued further; not resolved in this pass. |
| Caddock **MP9100-50.0-1%** | Real, in-stock-class part, ±1% tolerance, but **capped at 100 W** - fails the >=250 W floor outright. |
| Murata / general LCSC chip & TO-220 power resistors ("50W", "TO-220-50W-*") | Wirewound aluminum-case/porcelain-tube construction (Milliohm brand) - same inductance objection as the Vishay Dale NH series; also mostly below 250 W. |

### Datasheet-derived thermal numbers (README deliverable, computed here for P1 hand-off)

Using T50R0-250-12X's actual curve (25 C ambient per A3, P_op = 150 W):

- Allowed flange temperature at 150 W: `T_flange = 150 - (150/250)*(150-100) = 150 - 30 = 120 C`
  (derating curve is 100% flat to 100 C, so at 150 W = 60% of the 250 W rating, allowed flange
  temp interpolates on the linear 100-150 C leg: `100 + (1 - 150/250)*50 = 100 + 20 = 120 C` -
  **use this figure, not the naive formula above; shown both for auditability**).
- Required total Rth (sink + interface) at 25 C ambient: `(120 - 25) / 150 = 0.633 C/W`.
- Derated air-cooled (no heatsink) power: needs a bare-flange natural-convection Rth estimate,
  which is a P2/P3-level thermal exercise (flange area, orientation, still-air correlation) -
  **out of scope for this research pass; flag for P2.**

---

## 2. SMA female (jack) PCB connector - 50 ohm, board-side/edge-launch

Both candidates are edge-launch ("K(hole)" = female receptacle), right-angle, through-hole,
4-pin THT footprint - cheaper and better-stocked than every straight 4-hole flange ("KFD")
alternative checked (those ran $0.92-$5.30/ea vs <$0.60/ea here).

### Recommendation (PRIMARY): SMA-KWE, Lian Xin Technology

| Field | Value | Source |
|---|---|---|
| MPN / mfr | SMA-KWE / Lian Xin Technology ("STARF") | LCSC |
| LCSC | **C7498154** | https://www.lcsc.com/product-detail/coaxial-connectors-rf_lian-xin-technology-sma-kwe_C7498154.html (parts_search.py, read 2026-08-08) |
| Package | Plugin (THT), Extended (not JLC Basic) | parts_search |
| Stock | 11,802 | parts_search live query |
| Price | qty 1 = $0.561; qty 10 = $0.4769. Qty 5 falls in the qty-1 tier -> **$0.561/ea** | parts_search |
| **Qty-5 extended** | **5 x $0.561 = $2.81** | computed |
| Impedance / freq | 50 ohm, DC - 6 GHz | datasheet |
| **Working voltage** | **335 V RMS max**, withstand voltage 1000 V RMS (sea-level min) | datasheet (explicit, in Chinese + English units on the drawing) |
| Contact resistance | center <=3 mOhm, outer <=2 mOhm | datasheet |
| Insertion loss | <=0.15 dB @ 6 GHz | datasheet |
| Insulation resistance | >=5000 Mohm | datasheet |
| Operating temp | -65 to +165 C (PE cable variant -40 to +85 C) | datasheet |
| Mechanical | Overall length 14.6 mm, thread 1/4-36 UNS, body 8.6 mm; 4-pin THT footprint 6.0 x 4.2 mm with Ø0.9 mm pin holes - clean, fully-dimensioned drawing, good for a KiCad footprint | datasheet drawing |
| Datasheet saved | `research/SMA-KWE_LianXin_datasheet.pdf` | fetched |

Power check (per `requirements.md`'s own note, reproduced here): 150 W into 50 ohm = 86.6 Vrms;
335 Vrms rating gives **~3.9x voltage margin**; connector loss at 25 MHz is negligible. Adequate.

### Backup: BWSMA-KWE-Z001, BAT WIRELESS

| Field | Value | Source |
|---|---|---|
| MPN / mfr | BWSMA-KWE-Z001 / BAT WIRELESS (Shenzhen) | LCSC |
| LCSC | **C496551** | https://www.lcsc.com/product-detail/coaxial-connectors-rf_bat-wireless-bwsma-kwe-z001_C496551.html (parts_search.py, read 2026-08-08) |
| Stock | **126,876** (far higher than primary) | parts_search |
| Price | qty 1 = $0.5222; qty 10 = $0.4074. Qty 5 -> **$0.5222/ea** | parts_search |
| **Qty-5 extended** | **5 x $0.5222 = $2.61** (cheapest of the two) | computed |
| Impedance / freq | 50 ohm, 0-6000 MHz | datasheet |
| Working voltage | **Not explicitly published** - datasheet lists "DC Voltage: -" (blank) and "RF leakage: 1000 V" (ambiguous label, likely a withstand-voltage figure analogous to primary's 1000 Vrms) | datasheet |
| Mechanical | 14.5 x 13 x 6 mm; datasheet includes an explicit "PCB Layout" footprint drawing: 4x Ø1.0 mm mounting holes at 2.55/5.1 mm spacing plus a center Ø0.9 mm pin hole - very clean, arguably the better of the two for a KiCad footprint | datasheet drawing (page 6) |
| Datasheet saved | `research/BWSMA-KWE-Z001_BatWireless_datasheet.pdf` | fetched |

**Flag:** cheaper and far better stocked than the primary, but its datasheet does not state an
explicit working-voltage number the way SMA-KWE's does. General SMA engineering practice (per
`requirements.md`'s own note: "SMA is rated ~335 Vrms breakdown") supports adequacy, but this is
an inference, not a citation, for this specific part. Recommend primary unless price/stock forces
a switch, in which case get written voltage confirmation from BAT WIRELESS first.

---

## 3. Trimmer / variable capacitor - shunt reactance null at the launch

**Binding voltage requirement (see note at top of file): >=250 V working, RF-continuous, not just
a DC rating** (`requirements.md` F1 + criterion 7), stricter than my task brief's 200 V floor.
Every part below is screened against 250 V.

### Recommendation (PRIMARY): Vishay BCcomponents BFC280811339 (BFC2 808 ..... 11339)

Ø7.5 mm film-dielectric trimmer, vertical, round head, **top-adjustable**.

| Field | Value | Source |
|---|---|---|
| MPN / mfr | BFC280811339 (catalog "BFC2 808 11339") / Vishay Intertechnology (BCcomponents) | LCSC + datasheet |
| LCSC | **C3273212** | https://www.lcsc.com/product-detail/trimmers-variable-capacitors_vishay-intertech-bfc280811339_C3273212.html (parts_search.py, read 2026-08-08) |
| Stock | **9 units** - thin, see risk note | parts_search live query |
| Price | qty 1 = $8.8842; qty 10 = $7.6039. Qty 5 -> **$8.8842/ea** | parts_search |
| **Qty-5 extended** | **5 x $8.8842 = $44.42** | computed |
| Capacitance | **3 pF (guaranteed max Cmin) to 33 pF (Cmax)** - matches the assignment's ~1-30 pF target almost exactly (slightly short at the very bottom end) | datasheet ordering table |
| **Working voltage** | **250 VDC rated**, 500 VDC test/proof for 1 min. Sits exactly at the requirements.md 250 V floor with **no margin above it** - see flag below | datasheet Quick Reference Data |
| Dielectric | **PP (polypropylene) film** | datasheet electrical-data table |
| Adjustment | **Top and bottom adjustment**, screwdriver or trimming key, round head with a Ø1.6 mm slotted rotor. Confirmed reachable from the top per I2/A6 | datasheet ordering table + Detail Z drawing |
| Adjustment life | **Max 10 cycles (180 deg rotation)** - electrical/mechanical performance not guaranteed beyond that | datasheet |
| Q / loss | tan delta <=10x10^-4 @ 1 MHz (Cmax=33pF row: 1 MHz spec only, no 100 MHz spec published for this row) | datasheet electrical-data table |
| Self-resonance | min f_res @ Cmax = **300 MHz** - >>25 MHz operating frequency, no resonance risk in-band | datasheet electrical-data table |
| Mounting | THT radial, Ø7.5 mm housing, 10 mm max height (vertical version), 2.50/2.54 mm hole grid, min hole dia 1.25 mm | datasheet dimension drawing |
| Operating temp | -40 to +70 C (PP category) | datasheet |
| Datasheet saved | `research/BFC2808-series_Vishay-BCcomponents_trimmer_datasheet.pdf` (covers the whole BFC2808 family, all catalog numbers in this section) | fetched from LCSC's wmsc mirror |

**Flags:**
- **250 V rated vs a 250 V floor = zero margin**, not "with margin" as the task brief asked
  (which used a 200 V floor, comfortably cleared). Against `requirements.md`'s own stricter
  language ("must be rated for continuous RF (not just DC) at 25 MHz"), this part's published
  rating is a **DC/proof-test rating** (250 VDC continuous, 500 VDC for 1 min), not an RF-power
  voltage rating. At 25 MHz, far below this part's own self-resonant frequency (300 MHz) and
  with negligible real power in the trimmer branch (~60 mW per requirements.md section 3's own
  calc), treating the DC rating as a reasonable proxy for peak-RF withstand is a defensible
  engineering judgment - dielectric breakdown responds to peak field, not waveform - but it is a
  **judgment call, not a datasheet-cited fact, and it is architect/P3's to accept or reject.**
- **Stock = 9 units** is barely enough for a 5-unit build plus a few spares/rework margin; no
  headroom for a second batch without a LCSC reorder/lead-time hit.
- No candidate found anywhere in this search (LCSC or DigiKey, any dielectric) publishes an
  explicit RF/peak-voltage rating distinct from a DC rating - this is a category-wide gap, not
  a defect specific to this part.

### Backup: Vishay BCcomponents BFC280800016 (BFC2 808 ..... 00016)

Same Ø7.5 mm family, **PTFE dielectric** (the assignment's most-preferred dielectric after air).

| Field | Value | Source |
|---|---|---|
| LCSC | **C3273343** | https://www.lcsc.com/product-detail/trimmers-variable-capacitors_vishay-intertech-bfc280800016_C3273343.html |
| Stock | **2 units** - critically thin, cannot alone supply a 5-unit build | parts_search |
| Price | qty 1 = $5.5268 -> **qty-5 extended $27.63** (cheaper than primary, if enough stock existed) | parts_search |
| Capacitance | **2-18 pF** - narrower range than primary, misses the top third of the 1-30 pF target (covers roughly up to ~41 nH cancellation instead of ~75 nH) | datasheet |
| Voltage | Same **250 VDC / 500 VDC proof** rating and the same "no RF-specific rating, no margin over the 250 V floor" flag as primary | datasheet |
| Dielectric | **PTFE** | datasheet |
| Adjustment | Top + bottom, same mechanism as primary | datasheet |

**Not usable as a standalone build source at 2 units in stock** - listed as a backup/second-source
family member, not a drop-in qty-5 substitute. If pursued, combine with primary (9+2=11 units
total across two catalog numbers, still thin) or plan a reorder.

### Disqualified candidates (checked, rejected, with reason)

| Candidate | Why rejected |
|---|---|
| Vishay BFC2808**32659** / **31659** (5.5-65 pF, **150 V**, 802 / 42 in stock, $7.54 / $11.08) | Best-stocked, good range, but **150 V < the 250 V floor** - the exact trap the task brief warned about ("do not hand me a 25 V or 50 V trimmer" - this is the same failure mode one tier up). Flagged explicitly so nobody reaches for the well-stocked option by mistake. |
| Murata **LXRW0YV600-054** (30-60 pF, **50 V**, SMD 0.6x0.6mm) | Exactly the disqualification example named in the assignment ("ceramic e.g. Murata TZ-series only if the voltage rating genuinely clears 200 V") - it does not clear 200 V, let alone 250 V. Also wrong form factor (SMD chip, not top-adjustable with the board bolted down). |
| Knowles/Voltronics glass-piston **A1J4, AE5, AT5, AF5, AC5, AB5** (0.45-5 pF, **250 V**, Q 3000-5000 @ 100 MHz) | Electrically excellent (true glass/piston construction, published RF Q, sits exactly at the 250 V floor like the Vishay film parts) but **0 stock at LCSC**, every SKU, and capacitance tops out at 5 pF - far short of the ~30 pF target. Worth a DigiKey check in a follow-up pass if the film trimmers' zero-margin voltage rating is rejected by the architect. |
| Sprague Goodman **GZC43112** (30-430 pF, 100 V) | Range overshoots on the high end and undershoots on voltage (100 V) - also 0 stock at LCSC. |

---

## Budget roll-up (build of 5, primary picks)

| Line | Part | Qty-5 price | LCSC / DigiKey |
|---|---|---:|---|
| Termination resistor | T50R0-250-12X | **$122.00** | DigiKey 4353-T50R0-250-12X-ND |
| SMA female jack | SMA-KWE | **$2.81** | LCSC C7498154 |
| Trimmer capacitor | BFC280811339 | **$44.42** | LCSC C3273212 |
| **BOM subtotal (3 lines, 3 placements)** | | **$169.23** | |
| Bare PCB x5 (2L, <=30x30mm, JLCPCB std) | not priced in this pass - P2/fab territory | ~$2-10 typical for a board this small, excl. shipping | out of scope here |
| **Estimated total vs. $40 cap** | | **~$172-177**, i.e. **~4.3-4.4x over budget** | |

**This is not a substitutable-part problem.** The resistor alone (73% of BOM cost) is priced by
its material class (BeO/AlN ceramic, silver-plated copper, RF-tested), not by vendor markup -
every genuinely non-inductive, flange-mount, >=250 W candidate found across LCSC and DigiKey
clustered in the same $20-65/unit range `requirements.md` itself predicted. Swapping to a cheaper
wirewound "non-inductive" part (Vishay Dale NH-250) fails the reactance budget outright (see
disqualified table). Per A8 / requirements.md criterion 12: **report the real number, do not
degrade the design to hit the cap.** That is what this file does; the $40 vs. ~$175 gap is an
architect/P0-level decision (accept the overrun, or reopen the brief's budget assumption),
not something resolvable by re-searching parts.

Cheapest technically-defensible combination found, if the trimmer's zero-margin 250 V rating is
rejected and stock depth on both trimmer SKUs is combined: resistor $122.00 (fixed, no cheaper
compliant option exists) + trimmer $27.63 (backup, PTFE, but only 2 in stock) + SMA $2.61 (backup)
= **$152.24** for 5 - still ~3.8x the cap, and still short one trimmer's worth of stock.

## Risks / follow-ups for P2/P3

1. Resistor tolerance is +/-5%, not the +/-2% implied by A7 - architect call on whether the
   reflection-budget arithmetic (which shows resistance tolerance was never binding) makes this
   acceptable.
2. Trimmer voltage rating (250 VDC) sits exactly at, not above, requirements.md's 250 V floor,
   and is a DC/proof rating rather than a published RF rating - architect call.
3. Trimmer stock (9 units primary, 2 backup) is thin; if this design proceeds past a single
   prototype build of 5, plan a reorder or re-source before committing.
4. Resistor T-series working-voltage is inferred from a sibling R/RA-series datasheet, not
   published for the exact SKU - get written confirmation before treating it as verified.
5. BeO substrate handling/disposal note needed in the README (hazard flag, not a technical
   failure).
6. Mechanical stack-up (flange-to-PCB terminal height, tab bridging, flange-vs-30x30mm-outline
   fit) is explicitly out of scope for this file per the role prompt - see requirements.md
   section 5 items 1-3 for what P2/P6 must resolve using the dimensions captured above.

---

## Re-check (2nd pass, single-issue focus: A tolerance, B AlN substrate, C trimmer stock, D LCSC
resistor sweep). Original findings above are unchanged and NOT deleted. **Bottom line: none of
the four items dethrones a primary pick** - every credible alternative found is either not
stocked at LCSC/DigiKey, or is mechanically disqualified for this specific 30x30mm board. The
useful yield is: one genuinely better/cheaper resistor found and rejected on hard mechanical
grounds (worth recording so nobody re-discovers it), one exact-footprint AlN twin confirmed to
exist but unstocked, and one trimmer that actually solves the stock-depth risk if price is not
binding. Every figure below was read from a live page or a downloaded datasheet on 2026-08-08.

### A. Termination resistor tolerance - still no in-stock <=2% part beats the primary

**T50R0-250-12X's own ordering-info table** (re-read from the saved datasheet, page 1): the
catalog P/N decomposes as `T - 50R0(value) - 250(power) - 12X(factory-assigned)` - **there is no
tolerance digit in the ordering scheme at all**. "+/-5% Resistor Tolerance" is a fixed feature
bullet, not a selectable option; the only lever is footnote ***: "Other values and tolerances
available. Contact factory" - true special order, no SKU, no published price. Same pattern
confirmed on sibling **TA50R0-300-2X** (AlN, see B below) - identical ordering-code structure,
identical footnote. Barry/Vishay does not sell a tighter-tolerance flanged termination as a
catalog part at any distributor.

| Candidate | Tolerance | Power | Stock | Qty-5 price | Verdict |
|---|---:|---:|---:|---:|---|
| **RESI SOTC0227F50R0KZ** (LCSC `C53455401`) | **+/-1%** | 300W | **10** | **$105.58** | Real, in-stock, cheaper than primary - **but mechanically disqualified**, see D below |
| Kyocera AVX FR10975N0050**G** (2% suffix, TDS-HPRES-0006 p.1 "How To Order": G=2%, J=5%) | 2% (catalog code exists) | 250W | **0 results at DigiKey** (searched both `FR10975N0050` bare and `...G` suffix - zero hits, not even a 0-stock listing) | n/a - not orderable | Real catalog tolerance code, but the 50 ohm value isn't listed by any distributor found |
| Kyocera AVX FT10870N0050J01/02/03 (prior scout, re-confirmed) | 5% std / 2% "consult factory" | 150W | 0, 20-wk lead | n/a | Below power floor anyway |
| Florida RF Labs 32A7023F | not confirmed | not confirmed | not checked live (mfr/reseller page only) | - | No tolerance spec surfaced in available sources; not pursued further, no DigiKey/LCSC listing found |
| EMC Technology/Smiths Interconnect flange termination family | 5% (documented) | up to 250W | not checked for a specific 50R SKU at a distributor | - | Family datasheet confirms 5%-class parts only in what's accessible; no tighter-tolerance SKU surfaced |
| Mini-Circuits | - | - | - | - | Does not appear to sell a 250W-class flanged 50 ohm termination at all (their high-power line tops out differently); nothing found |

**Verdict:** no in-stock LCSC or DigiKey part clears <=2% at >=250W without a disqualifying
mechanical problem. The RESI part is the closest real, priced, in-stock number for "what does
tighter tolerance cost" ($105.58/5, actually *cheaper* than the primary's $122.00/5) - report it
as that reference point, not as an adoptable pick. True special-order tolerance (Barry-custom or
Kyocera FR-G) has **no obtainable price** through LCSC/DigiKey research; would require a direct
factory RFQ, out of scope for this pass.

### B. AlN substrate - an exact-footprint twin exists, but is not stocked anywhere checked

Barry Industries makes an AlN version of the exact primary family, confirmed via
`barryind.com/flanged_terminations.html`:

| MPN | Power | Substrate | Freq / RL | Tolerance | Dimensions (L x W x H) | Stock | Price |
|---|---:|---|---|---:|---|---:|---|
| **TA50R0-300-2X** | 300W | Thick film on **AlN** | DC-1.2GHz, RL >=20dB | +/-5% | **24.77 x 9.53 x 3.56mm - identical to the primary BeO pick's footprint** | **0** at DigiKey (0 results) and LCSC (0 results) | not obtainable |
| TA50R0-250-21X | 250W | Thick film on **AlN** | DC-2.5GHz, RL >=19dB | +/-5% | 22.10 x 14.22 x 3.56mm | **0** at DigiKey (0 results) | not obtainable |
| Kyocera AVX FR10975N0050 (either tolerance) | 250W | Thin film (Ta-N) on **AlN**, alumina cover | - | 5% or 2% | ~24.77 x 18.4(min) x 5.72mm | **0 results at DigiKey**, both suffixes | not obtainable |
| Kyocera AVX RP9 series | "4-250W" per DigiKey product-highlight page | AlN, "BeO-free" | - | 2% (chip-size SKUs only confirmed) | not confirmed at the 250W tier - verified SKUs (`RP92010T0050GTTR` etc.) are 10W chip-size parts, not the flanged 250W tier | not checked at 250W tier | - |
| Innovative Power Products "AlN Resistors and Terminations" | up to 650W (marketed) | AlN | - | - | category landing page only, no SKU table reachable | - | - |

Datasheets for TA50R0-300-2X and TA50R0-250-21X pulled and read in full (both saved this pass,
see file list): both publish real derating curves (flat 100% to 100C flange, linear to 0% at
150C - same shape/slope family as the BeO primary) and real dimensions. **Substrate reported
explicitly for every candidate above, per the assignment.**

**Verdict:** the *exact* mechanical answer to "AlN in this footprint" exists
(TA50R0-300-2X - literally the same L x W x H as the primary) but fails the requirements.md HARD
sourcing rule (in stock at LCSC or DigiKey) - it is special-order-only with no price obtainable
through the channels this pass is scoped to. Recommend it as the first RFQ target if BeO
toxicity is judged material enough to accept lead time/custom pricing; otherwise the BeO primary
stands (with the handling/disposal caution the prior pass already flagged).

### C. Trimmer stock - the >=250V + >=100-stock combination exists, at ~7x the price

Re-swept the entire Vishay BFC2808 family at LCSC (33 SKUs, full dump in
`research/raw/` via this session's scratch, not re-saved to the workspace since nothing changed
the pick): **exactly one member clears >=100 stock** - `BFC280832659`, 802 units, but **150V**
(same disqualification the prior scout already recorded). Every >=250V member in the family
sits at stock <=9. Confirmed: no combination inside this one family solves both constraints.//
Broadened to a plain "trimmer" sweep at LCSC (1769 total hits, filtered to stock>=100 -> 7 rows):
all are 50-150V ceramic SMD chip trimmers (Murata, SEHWA, Knowles `JZ060`) - **none reach 250V**.

DigiKey (Sprague-Goodman, Johanson/Knowles) is where the >=250V + >=100-stock combination
actually lives:

| MPN | Mfr | Range | Voltage | Dielectric | Adjust | Stock | Qty-5 price | Note |
|---|---|---|---:|---|---|---:|---:|---|
| **5602** (DigiKey `1956-1000-ND`) | Johanson Mfg (Knowles) | **1-30pF** | 250VDC (500V test) | **Air** | **Top**, panel-mount, needs Johanson tool P/N **8764** | **373** | **$316.85** (5 x $63.37, qty-1 tier) | Best all-round: clears both binding thresholds with margin, covers the ~8pF null point, Q>800@100MHz (beats the PP-film primary's Q) |
| 8052 | Johanson Mfg (Knowles) | 0.8-10pF | 250VDC | Air | Top (side-entry can style per family sheet) | **2263** (highest found) | ~$313.50 | Narrower range, still covers 8pF; check side- vs top-access on this specific case style before swapping in |
| 5502 | Johanson Mfg (Knowles) | 1-20pF | 250VDC | Air | Top, panel-mount | 92 (just under the 100 floor) | ~$263.00 | Close miss on stock |
| 5201 | Johanson Mfg (Knowles) | 0.8-10pF | 250VDC | Air | **Side** (CAN case) | 1121 | ~$199.25 | Excluded: side-adjust fails I2's top-access-with-board-bolted-down requirement |
| GAA3R513 | Sprague-Goodman | 0.35-3.5pF | 250V | - | Top panel mount | 436 | ~$170.10 | Stock clears, but range tops out at 3.5pF - can't reach the ~8pF null point |
| GDT20026 | Sprague-Goodman | 1.5-20pF | 250V | - | Top panel mount | 81 | ~$210.50 | Range good, stock just short of 100 |
| GKU10020 / GAA10001 / SGC3 series | Sprague-Goodman | various | 250-500V | - | Top | **discontinued at DigiKey** (checked live, "no longer available") | - | Dead ends |

Family datasheet (Johanson "AIR Capacitors" sell sheet, downloaded and read) confirms: Working
Voltage 250 VDC (500 VDC test) for every 52xx/54xx/55xx/56xx/57xx/58xx member - **same DC/proof-
rating-not-RF-rating caveat as the film-dielectric primary applies identically here**, this is
not new margin, just a different dielectric. Torque spec 1-5 oz-in, tuning tool "8764"
(Johanson's own non-standard tool, not a generic screwdriver) for the 52xx/54xx/56xx series.

**Verdict:** Johanson **5602** is the real answer if stock depth must be solved regardless of
price - it resolves the 9-piece thinness risk outright (373 vs 9, a 41x improvement) and is
confirmed top-adjustable. It costs **$316.85 for 5 vs the current pick's $44.42 for 5** (~7.1x).
Per the assignment's own priority order (voltage and stock are binding, price is "nice to have"),
this is the technically correct answer to "find one" - but given the build is already ~4.3x over
the stated $40 cap per the original pass, adding another 7x line-item cost is an architect/P3
call, not something to silently swap in. Recommending it as a documented alternative; the
BFC280811339 primary is left in place in the JSON with 5602 added alongside it.

### D. LCSC sweep for the resistor - one real find, disqualified on mechanical grounds

Search strings tried per the assignment (`parts_search.py --query "..."`): `50 ohm RF termination
flange`, `dummy load resistor flange`, `RF resistor flange 250W`, `flange resistor`, `flange
resistor 50` all returned **0 results** - confirmed this is a JLC-search quirk with multi-word
phrases (not proof of stock-out, per the tool's own hint), not a dead end. Alphanumeric
value-token queries work: `50R 250W`, `250W 50R`, `300W 50R`, `500W 50R` (10 results each,
verified live) surface the same pool of wirewound "Aluminum Case/Porcelain Tube" parts
(Ohmite/Arcol/Riedon/NTE/Hongda/Stackpole/TTM) already the wrong construction class (wirewound,
inductive - same objection as the already-disqualified Vishay Dale NH-250) and **0 stock across
every single SKU checked** at every wattage tier (250/300/500W) except one:

**RESI SOTC0227F50R0KZ** - LCSC `C53455401`, 300W, 50 ohm **+/-1%**, "Planar Non-Inductive Power
Resistor," SOT-227 package. Full datasheet pulled and read (10 pages, saved to scratch this
session, not copied into the workspace since the part is disqualified - re-fetch URL:
`https://datasheet.lcsc.com/datasheet/pdf/f498d11bfaf61676f7eba88b5e3c0767.pdf` if needed again).

| Field | Value |
|---|---|
| Substrate/construction | Thick film chip resistor(s) inside a molded SOT-227 shell, copper/Ni-plated flange, Sn-plated Cu leads (not a ceramic-substrate RF part like the primary) |
| Tolerance | +/-1% (F code); +/-0.5% (D) and +/-5% (J) also exist in the family but the "常备/standard-stock" table lists only F and J at the 50 ohm value |
| Power / flange temp ref | 300W, rated at <=25C flange (not 100C like the primary - see derating below) |
| Max voltage | 1000V |
| Insulation | 4000VAC, >=1G ohm |
| **Inductance** | **<=0.1uH published** - but measured at a 1kHz-1MHz test frequency per the datasheet's own footnote ("higher frequency needs actual verification or contact us"), **not validated at 25MHz**. 0.1uH = 15.7 ohm of reactance at 25MHz - by itself this ceiling would blow the whole 31.9nH post-tune budget several times over if the real part sits anywhere near its published max. Real risk, not just a mechanical one. |
| Rth (published) | **0.32 C/W** (chip-to-flange, explicit datasheet figure - better data than the primary's back-calculated 0.20 C/W estimate, though numerically a bit worse) |
| Derating curve | Flat 100% from -55C to +25C flange (no plateau above room temp - stricter than the primary's flat-to-100C plateau), linear to 0% at +155C. Slope = -300/130 = -2.31 W/C |
| Stock | **10** at LCSC |
| Price | $21.116/ea qty 1-5 -> **$105.58 for 5** (cheaper than the primary's $122.00) |
| Datasheet | derating curve + Rth both present -> passes the "no datasheet = disqualified" screen |

**Disqualified for this board on two independent, hard grounds:**
1. **Size.** Body ~38 x 25-30mm (standard SOT-227 outline, confirmed against the datasheet's own
   dimension drawing) - the 38mm long dimension alone exceeds the entire 30x30mm HARD board
   outline. There is no room left for the SMA jack or trimmer once this part is placed, even
   before any cutout/notch treatment.
2. **Terminal style.** Electrical connection is **4x M4 screw terminals** (datasheet: "电气端子
   4XM4"), not solder tabs/leads like the primary. This requires ring-lug wire jumpers bolted to
   the board, which works directly against the "short and wide, low-inductance" launch mandate
   of requirements.md sections 1 and 5 - the opposite of what a reactance-budget-constrained
   design needs, and not a PCB-mount interface at all in the normal sense.

Both objections are independent of tolerance/price/stock and would apply to any SOT-227-class
part in this power range - noted for the record so nobody re-discovers this part expecting a win.

**No other candidate in the entire D sweep has stock > 0** at LCSC across the 250/300/500W
tolerance/wattage tokens tried. This reconfirms (does not merely repeat) the original pass's
conclusion: this component class is priced and stocked by material/construction, not vendor -
LCSC does not have a cheaper back door into it.

### Re-check summary for P2/P3/architect

| Item | Resolved? | Action |
|---|---|---|
| A. Tolerance | No in-stock fix found | Primary stays +/-5%; $105.58/5 is the real-world cost reference for +/-1% if ever revisited |
| B. AlN | Exists, not stocked | RFQ Barry `TA50R0-300-2X` directly if BeO toxicity becomes a blocking concern - it's a drop-in footprint match |
| C. Trimmer stock | **Yes, if price is not binding** | Johanson `5602` (DigiKey `1956-1000-ND`) added to `trimmer-cap.json` as an alternative; costs 7.1x the current pick |
| D. LCSC resistor | No cheaper compliant option | RESI `SOTC0227F50R0KZ` documented and rejected (size + terminal style) in `termination-resistor.json` |

No line-item in the original budget roll-up changes as a result of this pass (primaries all
unchanged); the ~4.3x-over-cap conclusion from the first pass stands.

---

## Trimmer temperature re-selection (3rd pass - binding constraint changed)

**Trigger:** the chosen trimmer, Vishay BFC280811339, is rated **-40 to +70 C category
temperature (PP dielectric)** - confirmed again this pass, datasheet p.1, re-read in full. The
board bolts to a heatsink running 74-88 C base / 120 C at the resistor flange 0.5 mm away under
150 W CW. **The part is outside its rating at the rated operating condition.** Temperature is now
the binding parameter, superseding the earlier voltage-margin flag as the reason this family is
disqualified. New requirement floor: **>=100 C, 125 C strongly preferred**; voltage floor
unchanged at **>=250 V**; capacitance need re-scoped down to **~2.8-4.3 pF null point, useful
authority to ~10 pF** (a small range is now explicitly preferred, not 3-33 pF).

**Bottom line: requirement fully met, no derating/no-margin compromise needed.** Two Johanson
Manufacturing (Knowles Precision Devices) **air-dielectric** trimmers, both **-65 C to +125 C**
and **250 VDC**, both **in stock today at DigiKey in >2x-3x the required 20-piece quantity**, at
**$62-63/ea (qty 5) - inside the $85-125/trimmer contingency band already flagged, not above it.**
Air dielectric (metal/PTFE-spacer construction, no polymer film to derate) is why the whole family
clears +125 C where every film/ceramic part checked tops out at +70 to +85 C or fails on voltage.

### A. BFC280811339 (current pick) - re-confirmed DISQUALIFIED, temperature now the reason

Re-read `research/BFC2808-series_Vishay-BCcomponents_trimmer_datasheet.pdf` in full this pass
(p.1 Quick Reference Data table, verbatim):

| Dielectric | Category temperature range |
|---|---|
| PP (this part, 3/33 pF row) | **-40 C to +70 C** |
| PE, PTFE, PET (every other dielectric in the same BFC2808 family, incl. the PTFE backup
`BFC280800016` already in `trimmer-cap.json`) | **-40 C to +85 C** |

**No dielectric in the entire BFC2808 Ø7.5mm family clears +100 C** - PTFE, the family's best,
still falls 15 C short. This is a hard, published, family-wide ceiling, not a per-SKU quirk -
**every BFC2808 catalog number is disqualified for this board**, not just the PP primary.
Confirms the task brief's framing was correct; no "swap dielectric within the same family" escape
exists.

### B. PRIMARY (new): Johanson 8052

Ø7.49mm (0.295"/0.275") air-dielectric trimmer, THT, top screwdriver-slot adjust, threaded
.234-64 UNS-2A bushing.

| Field | Value | Source |
|---|---|---|
| MPN / mfr | 8052 / Johanson Manufacturing Corp. (Knowles Precision Devices) | DigiKey |
| Distributor | **DigiKey** PN `1956-8052-ND` | https://www.digikey.com/en/products/detail/johanson-manufacturing/8052/9094309 (live page, read this pass) |
| Stock | **2,263 units** - deepest of any candidate found, LCSC or DigiKey, in either pass | same URL |
| Price | qty 1-19 = **$62.70/ea** flat (next break qty 20 = $50.81) -> qty-5 falls in the qty-1 tier | same URL |
| **Qty-5 extended** | **5 x $62.70 = $313.50** | computed |
| Capacitance | **0.8 pF (min) to 10 pF (max)** - brackets the 2.8-4.3 pF null point with margin on both
  sides and reaches the requirement's own stated "~10 pF" authority ceiling almost exactly. This is
  the small-range fit the brief asked for, not another 1-30 pF part | DigiKey parametric table + Knowles combined trimmer catalog p.13/18 (cross-checked, consistent) |
| **Working voltage** | **250 VDC (500 VDC test)** - matches the requirements floor with the same
  margin as every part in this whole product category (no candidate anywhere, this pass or the
  last, publishes a distinct RF/peak rating above its DC rating - a category-wide gap, not a
  defect of this part) | DigiKey + catalog |
| **Temperature** | **-65 C to +125 C** - explicit "Operating Temperature" field on the DigiKey
  parametric page, and independently confirmed as a whole-family characteristic bullet
  ("Temperature range: -65 C to +125 C") on the Johanson "AIR Capacitors" family sell sheet
  (`farnell.com/datasheets/35551.pdf`, read in full this pass - covers the 52/53/54/55/56/58-series
  siblings of this part). **Clears the 125 C stretch goal outright**, not just the 100 C floor | DigiKey + Johanson family datasheet |
| Dielectric | **Air** (PTFE spacer for rotor guidance only, not the working dielectric) - inherently
  immune to the polymer-softening failure mode that caps every film/ceramic part in this search at
  +70 to +85 C | Johanson family datasheet |
| Q | **>5000 @ 100 MHz** (vs. the current PP pick's untested-at-100MHz 1 MHz-only tan-delta spec) | DigiKey + Knowles combined catalog p.13 |
| Adjustment | **Top**, screwdriver slot, self-locking constant-drive mechanism (transverse-slot
  spring design per the family sheet - "uniform torque, high Q, low dynamic tuning noise") | DigiKey ("Adjustment Type: Top / Screwdriver Slot") + family datasheet |
| Mounting | **Through-hole**, threaded **.234-64 UNS-2A** bushing, body diameter 0.295"/0.275"
  (7.49/6.99 mm) - confirmed on both the DigiKey parametric page and the Knowles combined catalog
  dimension table (p.18, "8052" row, Fig. 5). Full mechanical drawing (body length, pin pitch) is
  in the saved catalog PDF for P2/P6 to pull exact footprint numbers from - not re-transcribed here
  per this role's scope (no footprint design in P1) | Knowles combined trimmer catalog, `KnowlesTrimmersCatalogueweb177409287.pdf` p.18 |
| Tuning tool | **Not explicitly listed for the 80xx sub-family** in the catalog's "Johanson Tuning
  Tools" table (that table only enumerates 5200/5300/5400/5500/5600/5700 -> tool **8764** (.130"
  shank) and 5800 -> tool **8777** (.078" shank) - the 80xx series shares the same .234-64 thread
  family as 5600/5700 but is not itself named in the tool cross-reference table found. **Flag for
  P2/P3: confirm tool P/N with Johanson before committing**, or default to the 5602 alternate below
  which has a citation-grade tool number if that becomes load-bearing | Knowles combined catalog p.2 (table present but incomplete for this sub-family) |
| Part status | Active (not NRND/EOL) | DigiKey |
| LCSC | **Not carried** - confirmed via `parts_search.py --query "8052"` and `"Johanson trimmer capacitor"` (0 relevant results both times); this whole product category (>=250V RF trimmers) is a DigiKey-only channel, consistent with every prior pass | parts_search.py, this session |

### C. Strong alternate (wider range, same temp/voltage): Johanson 5602

The prior scout's original find, now fully verified with the missing temperature spec filled in.

| Field | Value | Source |
|---|---|---|
| MPN / mfr | 5602 / Johanson Manufacturing (Knowles) | DigiKey |
| Distributor | DigiKey PN `1956-1000-ND` | https://www.digikey.com/en/products/detail/knowles-johanson-manufacturing/5602/9094387 (live page, re-read this pass) |
| Stock | **373 units** (unchanged from the last pass, re-verified live) | same URL |
| Price | qty 1-19 = **$63.37/ea** flat -> **5 x $63.37 = $316.85** for 5 | same URL |
| Capacitance | **1 pF to 30 pF** - wider than the brief now wants (it explicitly says "do NOT insist
  on 3-33 pF"; 1-30 pF is the same shape of problem, just shifted down). Still brackets 2.8-4.3 pF
  correctly, just with more unused range/turns than necessary | DigiKey + catalog |
| Voltage | **250 VDC (500 VDC test)** - same as 8052, same category-wide DC-vs-RF caveat | DigiKey |
| **Temperature** | **-65 C to +125 C** - same family spec as 8052, confirmed on the same Johanson
  "AIR Capacitors" family sheet (this part's row is literally on the same page) | Johanson family datasheet |
| Dielectric | Air | family datasheet |
| Q | **>800 @ 100 MHz** - 6x worse than 8052's >5000, the tradeoff for the much wider capacitance
  span (more turns/plate travel = lower achievable Q at a given frequency) | Knowles catalog p.13 |
| Adjustment | Top, panel-mount, threaded **.234-64 UNS-2A** bushing + hex nut, body 0.295"/0.275" | catalog |
| **Tuning tool** | **Johanson 8764**, **.130" (3.3 mm) shank diameter**, non-metallic tip -
  explicitly listed in the "Johanson Tuning Tools" table for the 5200/5300/5400/5500/5600/5700
  family (5602's "56" prefix matches the 5600 row) | Knowles combined catalog p.2 |
| Part status | Active | DigiKey |
| LCSC | Not carried (same as 8052) | parts_search.py |

**8052 vs. 5602 recommendation:** 8052 wins on every axis that matters here - tighter/better-fit
capacitance bracket (0.8-10 pF vs. 1-30 pF), 6x the stock (2263 vs. 373), 6x the Q (>5000 vs.
>800), same price (~$63/ea either way) - **except** the tuning tool P/N, which is citation-grade
for 5602 (8764) and unconfirmed for 8052. Recommending **8052 as primary**; if a firm tool P/N is
required before committing and Johanson can't confirm it quickly for the 80xx case style, **5602
is the fallback with an identical temperature/voltage rating and a confirmed tool.**

### D. Whole-family sweep confirms both A and C are representative, not lucky picks

Re-swept the Johanson air-trimmer catalog (`farnell.com/datasheets/35551.pdf` full family sheet +
`KnowlesTrimmersCatalogueweb177409287.pdf` combined Knowles catalog, both read in full this pass).
**Every member of the 52xx/53xx/54xx/55xx/56xx/57xx/58xx/80xx/90xx air-trimmer families shares the
same -65 C to +125 C rating and (mostly) 250 VDC/500 VDC-test voltage** - this is a platform-level
characteristic of Johanson's air-dielectric construction, not a per-SKU fluke. That means the
capacitance-range choice is essentially free within this family once temperature/voltage are
satisfied - picked 8052 for the closest bracket match to the ~2.8-4.3 pF null point. Other
family members checked and available as further fallbacks if 8052/5602 go out of stock (all same
-65/+125 C, 250 V, DigiKey-only, not LCSC):

| MPN | Range | Q@100MHz | Notes |
|---|---|---:|---|
| 5850/5851/5852/5853 | 0.5-5 pF | >7500 | Tightest bracket around the 2.8-4.3 pF target of any part found, but authority tops out at 5 pF, short of the brief's "~10pF" stretch goal - not checked for live DigiKey stock this pass |
| 5700/5701/5702, 8050 | 0.6-6 pF | >10000 | Highest Q in the whole family; not checked for live stock this pass |
| 5200/5201/5202, 5750-5753 | 0.8-10 pF | >5000-7500 | Same electrical bracket as 8052 in a different case style/lead configuration; 5201/5202 are marked **side**-adjust in some listings (per the original pass's finding) - verify top-access per catalog drawing before substituting |
| **5301/5302 (500 VDC / 1000 V test)** | 1-10 pF | >2000 | **Best voltage margin found in this entire search (2x the 250V floor)**, same -65/+125C family rating, but DigiKey shows PN `1956-5302-ND` as **"not kept in stock" (0 on hand), 10-week manufacturer lead time**, price only quoted at a qty-20 break ($60.23/ea, $1204.60/20). **Disqualified against the ">=20 pcs in stock TODAY" requirement**, not against any electrical spec - flag as the RFQ target if a 10-week lead is ever acceptable in exchange for 2x voltage margin |

### E. Other families checked this pass, per the assignment's explicit list

| Family | Verdict |
|---|---|
| **Knowles Voltronics "A series" air trimmers** (A_5: 1-5pF/250V, A_10: 1-10pF/250V, A_14: 1-14pF/**125V**) | Same **-65 C to +125 C** rating (Voltronics catalog p.15, explicit table), but this is a **PTFE-spacer-guided air trimmer in a different mechanical family** (screw-in bushing, not the Johanson can style) - electrically viable (A_5/A_10 clear 250V) but not pursued to a DigiKey stock check since the Johanson 8052/5602 answer already dominates on every axis (higher Q, already-verified stock). Noted as a second-source family if Johanson goes out of stock. |
| **Murata TZ-series** (TZC3, TZB4, TZ03) | **Confirmed 100 VDC** across every SKU found this pass (TZC3P200A110B00, TZC3P300A110B00, TZB4 family, TZ03P600YR169, TZ03Z050ER169, etc.) - **fails the 250V floor by 2.5x**, exactly the trap the brief warned about. No Murata TZ SKU found anywhere clears 250V. Disqualified, confirmed again. |
| **Comdel / Temex / Exxelia** | Exxelia (which absorbed Temex) sells a "Temex Exxelia AT-5202" listed at a UK reseller as "0.8/10pF 250V Top Adjust" - **this appears to be a rebadge/cross-license of the same Johanson/Voltronics 5202 electrical part**, not an independently-engineered alternative (same capacitance range, same voltage, same "AT" Voltronics-style prefix). Exxelia's own PTFE-dielectric trimmer catalog (`exxelia.com/storage/exxelia-assets/datasheets/ptfe-dielectric-v1.pdf`) was located but not read in full this pass - the Johanson air-dielectric answer already fully satisfies the requirement (125C vs PTFE's typical 85-125C ceiling depending on grade) with confirmed live stock, so this branch was not pursued further. Flag as unexplored, not as ruled out, if Johanson stock ever runs dry. |
| **Vishay BFC2808 non-PP siblings** | **Re-confirmed disqualified on temperature** (see section A) - PTFE tops at +85 C, the family's own best case. No sibling clears +100 C. This closes out the one item the original pass left as "-40/+85C, might be worth a look" - it doesn't clear the new floor either. |

### Answer to "if nothing clears +100 C" - moot, but stated for completeness

**Not triggered.** Two in-stock, Active, DigiKey-sourced parts (8052 primary, 5602 alternate) clear
**+125 C**, not just the +100 C floor, at **$62-63/ea (qty 5) - inside, not above, the $85-125
contingency band** already flagged as acceptable. No derating of the board's CW power and no
$85-125-class compromise is required. If this recommendation is rejected for some other reason
(e.g., the unconfirmed 8052 tuning tool, or a preference to stay inside the original PP-film form
factor), the fallback ladder is: 5602 (same temp/voltage, confirmed tool, wider range, still
~$63/ea) -> 5301/5302 (2x voltage margin, same temp, but 0 stock/10-week lead) -> Voltronics A_10
(same temp/voltage, different mechanical family, not stock-checked) - not a +85 C compromise part,
because none was needed.

### Updated risks for P2/P3/architect

1. **8052's tuning tool P/N is unconfirmed** - the Knowles catalog's tool cross-reference table
   doesn't name the 80xx sub-family explicitly. Get written confirmation from Johanson, or switch
   to 5602 (tool 8764, .130" shank, confirmed) if this must be locked down before layout.
2. Price jumps from $44.42/5 (disqualified PP pick) to **$313.50/5 (8052)** - a further ~7x on top
   of the budget overrun the original pass already reported (~4.3x over the $40 cap). This pass
   does not change the resistor or SMA lines; the trimmer alone is now the single largest BOM line
   item, larger even than the resistor.
3. Neither 8052 nor 5602 is on LCSC - DigiKey-only sourcing for this line, same constraint as the
   PP-film part it replaces (which was LCSC-only) - **the distributor for this one line changes**,
   worth flagging for P4/ordering logistics (two distributors now needed for one BOM instead of
   one).
4. No candidate anywhere in this product category (Vishay film, Johanson/Voltronics air, Murata
   ceramic) publishes an RF/peak-voltage rating distinct from a DC rating - this remains a
   category-wide documentation gap, unchanged from the prior pass's finding, and applies equally
   to 8052/5602.
5. 5301/5302's 500V/2x-margin option is real and same-temperature-rated but 0-stock/10-week lead -
   worth an RFQ if the project timeline has slack and voltage margin is valued over lead time.
