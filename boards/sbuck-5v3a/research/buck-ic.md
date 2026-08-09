# Component scout: synchronous buck IC (main power stage) - boards/sbuck-5v3a

Source: `boards/sbuck-5v3a/requirements.md` s3 + assignment hard constraints (Vin 7-18V cont.,
abs max >=28V; 5.0V out, 3A cont. @ 50C no airflow; current-limit MIN >=4.0A; INTEGRATED sync
buck only; fsw 400-700kHz preferred; EN usable with a VIN divider for ~6.5V UVLO; exposed-pad
non-QFN preferred).

Method: `parts_search.py --query <MPN or family>` (live JLCPCB endpoint, verified reachable all
runs, `source: "live"` every query) for stock/price/package truth. Datasheets pulled via the
`wmsc.lcsc.com` PDF mirror and read with `pypdf` (text) + the `Read` tool (page-image render for
graphs/pin diagrams) - **every spec below is quoted from the actual manufacturer datasheet I
opened, not from memory.** Full sweeps: `research/raw/buck-ic-sweep.json` (AP64350),
`-sweep2` (LMR33630), `-sweep3` (SY8205), `-sweep4` (TPS54360), `-sweep5` (MP1584EN), `-sweep6`
(MP2315), `-sweep7` (AP63357).

**Two "commonly-remembered as synchronous" 30-60V-class parts turned out to be ASYNCHRONOUS on
datasheet check - a hard disqualifier per the assignment, not a preference call.** See s3.

---

## 1. Ranked candidates

| Rank | MPN | LCSC | Package | Tier | Stock | Price@1 | Fit |
|---|---|---|---|---|---|---|---|
| 1 | **AP64350SP-13** | C2071691 | SO-8-EP | Extended | 11,849 | $1.8832 | Cleanly passes every hard spec incl. the 4.0A current-limit floor; internal SS; RT-set 500kHz on the nose |
| 2 | **LMR33630ADDAR** | C841384 | ESOP-8 | Extended | 5,558 | $0.7404 | Best-documented part (mature TI datasheet, explicit hiccup spec), but current-limit MIN is 3.85A - misses the 4.0A floor by 150mA |
| 3 | **SY8205FCC** | C111875 | SOIC-8-EP | Extended | 10,163 | $0.4527 | Best RthJA (~30-36 C/W) and cheapest, but "Preliminary Specification" doc gives no MIN current-limit figure (typ 5A only) and needs an external SS cap |
| 4 | TPS54360DDAR | C44377 | SOIC-8-EP | Extended | 16,197 | $0.8293 | **REJECTED - asynchronous.** TI's own datasheet: "integrated high side MOSFET" only, external comp network required. Named family (TPS54xxx), documented as a trap |
| 5 | MP1584EN-LF-Z | C15051 | SOIC-8-EP | Extended | 4,706 | $2.9097 | **REJECTED - asynchronous.** Datasheet: "non-synchronous... requires external Schottky diode to ground." Named family (MP15xx), documented as a trap |
| 6 | MP2315GJ-Z | C45889 | TSOT-23-8 | Extended | 225 | $2.2646 | **REJECTED - stock 225 < 500pcs threshold**, and Vin only 4.5-24V (least headroom of any candidate toward the 28V abs-max ask) |

All Extended tier (acceptable per requirements Q28 for the buck IC). Price is the qty-1 break
per assignment instructions; qty is 5 (below every price-break qty on every part, so qty-1 is
also the effective build price).

---

## 2. Top 3 - full datasheet-verified spec table

Op point for on-time/duty checks: Vin=18V -> D=0.278; Vin=7V -> D=0.714 (Vout=5V ideal).

| Spec | **AP64350SP-13** (Diodes, DS41976 Rev.5, Dec 2024) | **LMR33630ADDAR** (TI, ZHCSHQ3F, rev Nov 2020) | **SY8205FCC** (Silergy, "Preliminary Specification") |
|---|---|---|---|
| Topology | Synchronous, confirmed: "fully integrated synchronous buck converter" | Synchronous, confirmed: "The LMR33630 is a synchronous peak-current-mode buck regulator" | Synchronous, confirmed: "integrates main switch and synchronous switch" |
| Vin operating | 3.8-40V | 3.8-36V | 4.5-30V |
| Vin abs max | **42.0V DC** (45V for 400ms transient) | **38V** (VIN to PGND -0.3 to 38V) | **33V** (PVIN/SVIN/LX/BS/EN/PG abs max) |
| Iout rated | 3.5A continuous | 3.5A continuous | 5A continuous, 6A peak |
| Current limit (HS/peak) | **MIN 4.25A**, typ 5A, max 5.75A - **passes >=4.0A floor** | **MIN 3.85A**, typ 4.5A, max 5.05A - **misses 4.0A floor by 150mA** | typ 5A only - **no min/max published** (doc is marked "Preliminary Specification") |
| Effective guaranteed Iout,max | n/a (single peak-limit spec) | `(ILIMIT_min+ISC_min)/2` = (2.9+3.85)/2 = **3.375A worst-case** per TI's own Eq.1 - only 12% above our 3.0A load | n/a - not derivable from published data |
| Rds(on) HS / LS | 75 / 45 mOhm (max only, no typ given) | 95/160 typ/max HS; 66/110 typ/max LS (DDA pkg) | 70 / 40 mOhm (typ only, no min/max) |
| Reference / FB tolerance | VFB 0.8V, **792-808mV = +/-1%** | VFB 1.0V, **985mV-1.015V = +/-1.5%** | VREF 0.6V, **591-609mV = +/-1.5%** |
| Quiescent current | 22uA typ (PFM, no load) | 24 typ / 34 max uA (non-switching) | 200uA typ (Iout=0) |
| Switching frequency | **RT-set, 100kHz-2.2MHz range; RT=200k -> 450/500/550kHz min/typ/max** - dead center of the 400-700kHz band | **Fixed, "A" version: 340/400/460kHz min/typ/max** - in-band | **Fixed 500kHz typ** (pseudo-constant, CCM) - in-band |
| EN threshold / VIN-tolerant | VEN_H 1.18-1.25V precision; "Connect to VIN or leave floating for automatic startup" - **tolerates VIN directly** | VEN-H rising 1.2/1.231/1.26V precision, 100mV hysteresis; abs max = VIN+0.3V, pin description: "Can be connected directly to VIN; Do not float" - **tolerates VIN directly** | VENL falling 1.1-1.3V (typ 1.2V), 0.1V hysteresis; abs max shared with PVIN row (33V) - **tolerates VIN directly** |
| Thermal shutdown + OCP | TSD 160C, 25C hysteresis; "Cycle-by-Cycle Peak Current Limit" explicit feature | TSD 165C shutdown / 148C recovery; explicit **hiccup mode**: FB<0.4V trips it, 94ms burst-off, retries with soft-start | TSD 160C, 20C hysteresis; "Output short circuit protection with current fold back" + "auto recovery" (foldback, not a documented hiccup burst-off like the other two) |
| Package / RthJA | SO-8-EP, **theta_JA 45 C/W** (4L, 2oz Cu, min recommended pad) | HSOIC-8 PowerPAD, **theta_JA 42.9 C/W** (4L JEDEC board) | SO8E, **theta_JA 30 or 36 C/W** - datasheet table lists DFN4x3-12 and SO8E together without a clean per-package split; treat as ~30-36 C/W pending confirmation |
| Min on-time / max duty check | tON_MIN ~100ns typ. At 18V/D=0.278/500kHz: on-time 556ns (>>100ns, fine). At 7V/D=0.714: on-time 1.43us (fine, Vin_min 3.8V gives huge margin) | tON-MIN 75/108ns typ/max (DDA), tON-MAX 7-9us. At 18V/D=0.278/400kHz: 695ns (fine). At 7V/D=0.714: 1.79us, DMAX 98% via freq foldback if ever needed - **explicitly confirmed to hold regulation near dropout** (VDROP spec: 150mV @ Iout=1A, fsw folds to 140kHz) | tON_MIN 80ns, tOFF_MIN 120ns typ, 500kHz. At 18V/D=0.278: 556ns (fine). At 7V/D=0.714: 1.43us, well under the ~1.88us on-time ceiling implied by period-tOFF_MIN (fine); Vin_min 4.5V gives margin |
| Soft-start | **Internal, fixed 2ms** - no external cap | **Internal, 2.9-6ms** - no external cap | **External** - SS pin + cap, `Tss = Css*0.6V/10uA` |
| Efficiency @ 12Vin/5Vout/3A | Read from datasheet Fig.4 (VIN=12V, VOUT=5V curve, exact op point): peaks ~94% near 1-2A, **~90-92% at 3A** (graph-read, no printed table value) | Not printed as text or found as a labeled point on the pages checked; Rds(on)-based estimate (duty-weighted ~78mOhm effective) suggests low-90s%, **unverified - flag for bench/sim** | Not found as text; "Up to X% efficiency" claims not printed for full load either - **flag for bench/sim** |
| DNP snubber / EMI note | RT/CLK-programmable freq gives layout flexibility if 500kHz proves noisy | Fixed-freq "A" version avoids RT resistor tolerance stack but removes tuning freedom | Fixed 500kHz, no freq trim option |

---

## 3. Why TPS54360 and MP1584EN are disqualified (not passed over on preference)

Both are named-family parts (`TI TPS54xxx`, `MPS MP15xx`) that are **widely assumed synchronous**
by part number alone. Datasheet text, read directly, says otherwise:

- **TPS54360** (TI, SLVSBB4E): "The TPS54360 is a 60V, 3.5A, step down regulator **with an
  integrated high side MOSFET**." Terminal table: SW is "the source of the internal **high-side**
  power MOSFET" - no low-side FET mentioned anywhere in the terminal/functional description, and
  the part exposes a COMP pin requiring external compensation (current-mode control, but
  externally compensated - matches the async SWIFT family pattern, not a COT/D-CAP synchronous
  part). LCSC's own "Synchronous Rectifier" attribute independently says "No" for every
  TPS54360-family row searched. **Disqualified: not integrated synchronous.**
- **MP1584EN** (MPS): datasheet explicitly: "**non-synchronous**, step-down switching regulator
  with an integrated high-side high voltage power MOSFET," and pin 1 (SW) description: "**A low
  forward drop Schottky diode to ground is required.**" This directly contradicts the common
  assumption that "MP1584 = synchronous" (true of some other MPS parts, not this one).
  **Disqualified: not integrated synchronous, requires an external catch diode.**

MP2315 (MP23xx family) is synchronous per its own datasheet-adjacent LCSC attributes, but its
real LCSC listing sits at **225pcs stock - under the 500pcs "in stock" floor** this assignment
sets for the buck IC, and its Vin band (4.5-24V) gives the least margin of any candidate toward
the 28V abs-max requirement (no verified abs-max figure found >24V in the pulled listing).
Rejected on sourcing + margin grounds, not a functional defect.

AP63357 (an actual `AP63xxx`-named Diodes part, not just the AP64xxx sibling AP64350) was also
checked: 3.8-32V, 3.5A, sync, 450kHz, **but VDFN-13(2x3) - leadless**, unlike AP64350's SO-8-EP.
Since AP64350 meets every spec at least as well from a non-leadless package, AP63357 was not
carried forward as a separate candidate.

---

## 4. Recommendation

**Lead: AP64350SP-13** (C2071691, Diodes Inc, SO-8-EP). Only candidate whose datasheet publishes
a MINIMUM current-limit spec (4.25A) that clears the assignment's 4.0A floor; RT resistor lands
exactly on 500kHz (dead center of the 400-700kHz band, and tunable if 500kHz proves noisy at
layout); internal fixed soft-start (no extra SS cap); EN pin explicitly rated for a direct-to-VIN
or divider connection; deepest stock of the three (11,849pcs). Highest per-unit price of the
three ($1.88 @ qty1) but at build qty 5 that's a ~$5 total delta against SY8205 - immaterial
against the ~$12/board target.

**Alternate: LMR33630ADDAR** (C841384, TI, ESOP-8/HSOIC-8 PowerPAD). Best-documented part (mature,
non-preliminary TI datasheet with an explicit hiccup-mode spec: FB<0.4V trip, 94ms burst,
auto-restart with soft-start - the cleanest match to requirements-answers #7/#29's "hiccup restart"
language of the three). **Real gap: ISC (peak) current-limit MIN is 3.85A, and TI's own worst-case
formula for guaranteed max output current, (ILIMIT_min+ISC_min)/2, gives only 3.375A** - just
12% above the 3.0A continuous load, not the >=4.0A the assignment asks for. Typ values (4.5A ISC)
are comfortable; it is specifically the MIN-spec (production-corner) number that falls short.
Use if AP64350's RT-resistor-set frequency proves fragile in practice, or if the hiccup behavior
is preferred explicitly, but flag the current-limit margin for P2/P4 re-verification if selected.

**Third: SY8205FCC** (C111875, Silergy, SOIC-8-EP). Cheapest ($0.45 @ qty1) and best RthJA
(~30-36 C/W vs 42.9-45 C/W for the other two) - meaningful given the board's binding thermal
constraint is 2.05W into natural convection at 50C ambient. **Two real gaps**: (1) the datasheet
on file is explicitly marked **"Preliminary Specification"** and its current-limit row gives only
a typical value (5A) with no MIN/MAX - cannot confirm the >=4.0A floor from this document; (2)
soft-start is **external** (SS pin + cap), a small BOM/layout addition the other two avoid. Keep
as the value option if a production-grade SY8205 datasheet (or a bench/vendor confirmation of the
current-limit corner) becomes available at P2/P3 - the thermal margin it offers is the largest
lever on this board's binding constraint.

---

## Citations (datasheets actually opened this session)

- AP64350 datasheet, DS41976 Rev. 5-2, Diodes Incorporated, December 2024.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210280930_Diodes-Incorporated-AP64350SP-13_C2071691.pdf
- LMR33630 datasheet, ZHCSHQ3F, Texas Instruments, Aug 2017 - rev Nov 2020.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2410121900_Texas-Instruments-LMR33630ADDAR_C841384.pdf
- SY8205 "Preliminary Specification" / AN_SY8205, Silergy Corp.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1809050154_Silergy-Corp-SY8205FCC_C111875.pdf
- TPS54360 datasheet, SLVSBB4E, Texas Instruments, Aug 2012 - rev Mar 2014 (read to confirm
  async disqualification). https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1810261107_Texas-Instruments-TPS54360DDAR_C44377.pdf
- MP1584EN datasheet, Monolithic Power Systems (read to confirm async disqualification).
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2401301656_Monolithic-Power-Systems-MP1584EN-LF-P_C7304223.pdf
  (same base part as the recommended-against MP1584EN-LF-Z, C15051, whose own LCSC listing has
  no direct datasheet link)
- Live JLCPCB parts search via `parts_search.py`, all queries `source: "live"`, this session.
