# magnetics-caps.md - power-stage passives (inductor, Cin, Cout)

Block: buck inductor + input cap bank + output cap bank for sbuck-5v3a (5V/3A sync
buck, Vin 7-18V, fsw target 400-700kHz, IC not yet chosen). All parts verified live
via `parts_search.py` today; LCSC part numbers/stock as observed. Build qty 5, prices
quoted at the qty-1 break per the assignment's "quote qty-1 price" instruction.
Full JSON responses for every queried MPN are in `research/raw/magnetics-caps-sweep.json`
(script-written via `--out`, grouped by sub-function).

Two datasheets were pulled and read in full (TDK VLS6045EX, TDK SPM6530) plus one
molded-inductor datasheet (KOHERelec MDE0630) to get real Isat/Itemp basis and
operating-temperature ceilings - see "Temperature derating method" below.

**P1 CORRECTION PASS (this update):** the power-architect's budget (`power.json`)
landed after the above was written and invalidates two of its picks: the inductor
DCR ceiling (`<=25 mOhm max @ 20C`) rules out every part in section 1.5's original
top 4, and the Cin bulk/Cout dielectric picks conflict with the architect's damping
and X7R-only requirements. Sections 1-4 below are UNCHANGED (the ferrite-vs-
metal-composite finding in 1.2 is correct and still load-bearing - every new
inductor pick below is molded/alloy-composite, not ferrite). The ranked tables in
1.5, 2.4 and 3.4 have been updated in place to the corrected picks; **section 5 is
the new work and carries the full reasoning, search data and hot-DCR arithmetic.**

---

## 1. Inductor

### 1.1 Ripple current dI and Ipk, worst case Vin=18V (D=Vout/Vin=0.278)

dI = (Vin-Vout)*D/(L*fsw). Computed (not estimated) for each candidate L across the
400-700kHz band:

| L | fsw=400kHz | fsw=500kHz | fsw=600kHz | fsw=700kHz |
|---|---|---|---|---|
| 10.0uH | dI=0.903A (30.1%), Ipk=3.45A | dI=0.722A (24.1%), Ipk=3.36A | dI=0.602A (20.1%), Ipk=3.30A | dI=0.516A (17.2%), Ipk=3.26A |
| 8.2uH | dI=1.101A (36.7%), Ipk=3.55A | dI=0.881A (29.4%), Ipk=3.44A | dI=0.734A (24.5%), Ipk=3.37A | dI=0.629A (21.0%), Ipk=3.32A |
| 6.8uH | dI=1.328A (44.3%, over target), Ipk=3.66A | dI=1.062A (35.4%), Ipk=3.53A | dI=0.885A (29.5%), Ipk=3.44A | dI=0.759A (25.3%), Ipk=3.38A |
| 4.7uH | dI=1.921A (64%, over target) | dI=1.537A (51%, over target) | dI=1.281A (43%, over target) | dI=1.098A (36.6%), Ipk=3.55A |

**Recommendation per fsw** (dI centered in the 20-40%/0.6-1.2A band): 400kHz->10uH,
500kHz->8.2uH, 600-700kHz->6.8uH. 4.7uH only fits the band at 700kHz and is not a
good multi-fsw choice. **6.8uH is the best single SKU if the eventual IC could land
anywhere 500-700kHz** (dI stays in-band the whole way); 8.2uH is the best single SKU
if the IC could land 400-600kHz.

### 1.2 Temperature derating method (the assignment's required finding)

Both TDK datasheets define **Isat** (current at which L drops 20-30% of its 0-A
value) and **Itemp** (current that produces a 40C rise by self-heating) **at what
the datasheets imply is room-temperature test conditions** (~20-25C ambient) -
neither TDK sheet nor the KOHERelec MDE0630 sheet states the test ambient
explicitly, and none of the three publish a separate "Isat/Itemp at 50C ambient"
curve. This is exactly the trap the brief warned about. Two derating steps applied:

- **Itemp -> hot ambient**: the vendor's Itemp is the current that reaches the
  part's own Tmax (105C ferrite-wound VLS/FNR6045S families, 125C metal-composite
  SPM6530/MDE0630) from a ~20C test ambient via self-heating alone. At our 50C
  ambient the allowed self-heating budget shrinks, so the safe current scales by
  sqrt((Tmax-50)/(Tmax-20)) (self-heating ~ I^2*Rdc*Rth, constant Rth assumed - a
  standard, if approximate, derating method, not a vendor-published number).
- **Isat -> hot**: no vendor curve at all for any of these 3 families. Convention
  used (stated as an estimate, per the brief's "say so" instruction): **ferrite
  wound cores lose Bsat faster with temperature than metal-composite/molded
  cores** - applied ~25% Isat derating 25C->105C for the ferrite-wound VLS6045EX/
  FNR6045S families, ~10-12% for the metal-composite SPM6530/MDE0630 families.
  This is conventional MLCC-industry-adjacent knowledge (ferrite vs. metal-alloy
  powder core temperature behavior), not part-specific data.

| Part | Family/core | Tmax | Itemp(vendor,~20C) | **Itemp derated @ 50C ambient** | margin over 3.0A |
|---|---|---|---|---|---|
| VLS6045EX-6R8M | ferrite wound | 105C | 3.60A | **2.90A** | **-3.5% - FAILS** |
| VLS6045EX-100M | ferrite wound | 105C | 3.40A | **2.73A** | **-8.8% - FAILS** |
| FNR6045S6R8MT (cjiang) | "magnetic shielded" (ferrite-like) | assumed 105C | 3.30A | **2.65A** | **-11.5% - FAILS** |
| FNR6045S8R2MT (cjiang) | ferrite-like | assumed 105C | 2.80A | **2.25A** | **-24.9% - FAILS** |
| NR6045M4R7A (COILANK) | ferrite-like | assumed 105C | 3.40A | **2.73A** | **-8.8% - FAILS** |
| SPM6530T-100M (TDK) | metal composite | 125C | 3.60A | **3.04A** | +1.4% - razor thin |
| SPM6530T-6R8M (TDK) | metal composite | 125C | 4.00A | **3.38A** | +12.7% - workable |
| MDE0630-100M (KOHERelec) | molded metal | 125C | 4.50A | **3.80A** | +26.8% - good |
| MDE0630-8R2M (KOHERelec) | molded metal | 125C | 5.00A | **4.23A** | +40.9% - best |

**Finding**: every ferrite-wound candidate found (TDK VLS6045EX, cjiang FNR6045S,
COILANK NR6045) fails to cover the 3.0A continuous load once its own vendor-defined
Itemp is derated to a 50C, no-airflow ambient - despite VLS6045EX having the best
DCR on the shortlist. This is not a marginal call; it is a straight reject for this
brief's environment. The metal-composite/molded families (TDK SPM6530, KOHERelec
MDE0630) clear the load with real margin because their higher Tmax (125C vs 105C)
gives more thermal headroom at the same self-heating current.

Isat-side check at Ipk (same conventional hot-derating, worst case = smallest L /
lowest fsw in the recommended range for that part):
- SPM6530T-6R8M @ 600kHz: Ipk=3.44A vs. est. hot Isat 4.0A*0.90=3.6A -> only ~4.6%
  margin. Tight; recommend running it at 700kHz (Ipk=3.38A) if selected, not 600kHz.
- MDE0630-8R2M @ 500kHz: Ipk=3.44A vs. est. hot Isat 5.5A*0.88=4.84A -> 41% margin.
  Comfortable at any fsw in the band.

### 1.3 DCR / efficiency-budget impact (P = 3.0^2 * DCR, budget = 2.05W total)

| Part | DCR | P at 3A | % of 2.05W budget |
|---|---|---|---|
| VLS6045EX-6R8M | 36.0 mOhm | 324 mW | 15.8% |
| NR6045M4R7A | 24.0 mOhm | 216 mW | 10.5% (but fails Itemp, see above) |
| VLS6045EX-100M | 47.0 mOhm | 423 mW | 20.6% |
| FNR6045S6R8MT | 40.0 mOhm | 360 mW | 17.6% (fails Itemp) |
| SPM6530T-6R8M | 53.3 mOhm max / 48.4 typ | 480/436 mW | 23.4% / 21.2% |
| **MDE0630-8R2M** | 60.0 mOhm max | 540 mW | 26.3% |
| SPM6530T-100M | 72.5 mOhm max / 65.9 typ | 652/593 mW | 31.8% / 28.9% |
| MDE0630-100M | 68.0 mOhm max | 612 mW | 29.9% |

**Real tradeoff for P2/P3**: the ferrite-wound parts have the best DCR but fail the
thermal-margin check outright; the parts that pass the thermal check (SPM6530,
MDE0630) all sit above the 44mOhm/~20%-budget guideline. MDE0630-8R2M spends 26.3%
of the loss budget vs. SPM6530T-6R8M's 21-23%, in exchange for ~3x the Itemp margin
(41% vs 12.7%) and ~9x the Isat margin (see above). Given 50C ambient with **no
airflow** is explicitly the binding constraint in this brief, thermal margin should
outweigh the extra ~60-100mW of DCR loss.

### 1.4 Shielded/height/footprint

All shortlisted parts are shielded (VLS6045EX = ferrite magnetic-shield wound;
SPM6530/MDE0630 = molded/composite, inherently self-shielding). Heights: VLS6045EX
4.5mm, SPM6530T 3.0mm, MDE0630 3.0mm - all far under the 15mm cap. Footprints:
VLS6045EX/NR6045 6.0x6.0mm (36mm^2), SPM6530T 7.1x6.5mm (46.2mm^2), MDE0630
7.0x6.6mm (46.2mm^2) - all small relative to the 50x40mm board.

### 1.5 Candidates (ranked)

**SUPERSEDED by the architect's `DCR <= 25 mOhm @ 20C` ceiling - see section 5.1 for
the full re-search.** Table below is the CORRECTED ranking; ranks 1-2 are the
picks, ranks 3-4 are two 400kHz-band parts that each clear only one of the two
hard filters (documented, not silently dropped), ranks 5-8 are the original
shortlist demoted to REJECT (DCR 2.1-2.9x over ceiling), ranks 9-10 are the
unchanged ferrite rejects from 1.2-1.4.

| rank | mpn | lcsc | package | stock | Basic/Ext | price@qty1 | fit |
|---|---|---|---|---|---|---|---|
| 1 | FAUL1050-6R8MT | C5298292 | SMD 11.5x10mm | 763 | Extended | $0.5593 | inductor - NEW PRIMARY: 6.8uH molded (Alloy Sponge Powder, Tmax 155C, AEC-Q200), DCR 18.5mOhm max @20C -> ~24.05mOhm hot (STILL clears the 25mOhm ceiling hot), fits 500-600kHz. See 5.1 |
| 2 | MDA1365-100M | C2847583 | SMD 13.5x12.6mm | 645 | Extended | $1.0912 | inductor - NEW 400kHz pick: 10uH alloy-molded (KOHERelec), DCR 19.2mOhm max @20C -> ~24.96-25.24mOhm hot (right AT the ceiling, near-zero hot margin - flagged). See 5.1 |
| 3 | FAUL1350-6R8MT | C5298322 | SMD 13.5x12.8mm | 519 | Extended | $1.0136 | inductor - backup/high-margin alt to rank 1: same 6.8uH cjiang family, bigger case (13.5x12.8mm), DCR 18mOhm max, Isat/Irms ~2x rank 1's. See 5.1 |
| 4 | SRP1265A-100M | C840531 | SMD 13.5x12.5mm | 418 | Extended | $1.0394 | inductor - 400kHz alt, CLEARS DCR (16.5mOhm, best of the whole shortlist) but 418<500 stock - 82pcs short, reorder-watch, not a hard pick today. See 5.1 |
| 5 | IHLP4040DZER100M11 | C845066 | SMD 10.8x10.2mm | 4208 | Extended | $1.0378 | inductor - 400kHz alt, deep stock but DCR 27.8mOhm MISSES the 25mOhm ceiling by 11% (2.8mOhm). Fallback only if MDA1365-100M/SRP1265A-100M both go unavailable. See 5.1 |
| 6 | MDE0630-8R2M | C2875732 | SMD 7.0x6.6mm | 1029 | Extended | $0.2579 | inductor - REJECT (was rank 1 before the architect's budget landed): 8.2uH, DCR 60mOhm max = 2.4x the 25mOhm ceiling, ~78mOhm hot -> 0.71W, blows the whole 0.335W efficiency margin alone. Temp-margin reasoning (+41% Itemp) still correct, DCR is now the disqualifier. See 5.1 |
| 7 | SPM6530T-6R8M | C138515 | SMD 7.1x6.5mm | 3719 | Extended | $0.1817 | inductor - REJECT (was rank 2): 6.8uH, DCR 53.3mOhm max = 2.1x the ceiling, ~69.3mOhm hot -> 0.63W. See 5.1 |
| 8 | MDE0630-100M | C842898 | SMD 7.0x6.6mm | 914 | Extended | $0.1897 | inductor - REJECT (was rank 3): 10uH, DCR 68mOhm max, ~88.4mOhm hot -> 0.80W. See 5.1 |
| 9 | SPM6530T-100M | C112288 | SMD 7.1x6.5mm | 2075 | Extended | $0.2070 | inductor - REJECT (was rank 4): 10uH, DCR 72.5mOhm max, ~94.25mOhm hot -> 0.85W. See 5.1 |
| 10 | VLS6045EX-6R8M | C415364 | SMD 6.0x6.0mm | 5306 | Extended | $0.1339 | inductor - REJECT (unchanged): best DCR (36mOhm, 15.8%) on the whole shortlist but Itemp derates to 2.90A @ 50C ambient, below the 3.0A load. Documents the "25C-Isat trap" the brief called out |
| 11 | VLS6045EX-100M | C360734 | SMD 6.0x6.0mm | 5809 | Extended | $0.1525 | inductor - REJECT (unchanged), same trap, 10uH: Itemp derates to 2.73A, -8.8% under load |

Not shortlisted further: cjiang FNR6045S family (worse Itemp than VLS at the same
package, same reject reason, DCR not competitive enough to compensate); COILANK
NR6045M4R7A (excellent 24mOhm DCR but 4.7uH only fits the band at 700kHz and still
fails Itemp at 50C, -8.8%); Bourns SRP1245A-8R2M (huge Isat/Itemp margin and lowest
DCR of anything found, 16.8mOhm, but 13.5x12.5mm footprint eats ~8% of the whole
board area for one part, and LCSC stock is only 60 pcs - fails the >=500pcs
threshold outright).

---

## 2. Input capacitors (Cin)

RMS ripple current on Cin peaks at **1.50A at D=0.5 (Vin=10V)**, inside the
operating range - sized for 1.5A RMS, not the 12V-nominal 1.48A figure. Ceramic
ESR/ripple-current capability is not published by LCSC for any MLCC in this
shortlist (typical for the category - vendors publish it only through their
online simulators, not the static datasheet); a few-mOhm ESR MLCC bank at these
values self-heats negligibly under 1.5A RMS shared across 4+ parts, so **ceramic
ripple-current rating is not the limiting variable here** - effective capacitance
after DC-bias derating is.

### 2.1 DC-bias derating - vendor curve NOT found, conventional estimate used

Pulled Murata's static GRM32ER71H106KA12L-family MLCC catalog PDF (10.7MB,
292 pages) specifically looking for a DC-bias reduction curve: **it is not in the
static datasheet** - page 291 points to Murata's "SimSurfing" web simulator
instead, which this offline research pass cannot query. Samsung/Yageo/FH static
sheets for the other shortlisted MLCCs are the same pattern (parametric table only,
no embedded bias curve). **Stating this plainly per the brief's instruction**:
no vendor DC-bias curve was obtained for any Cin/Cout candidate. Conventional
estimates used instead (general MLCC-industry knowledge, not part-specific):
X7R at <=36% of rated voltage in 1206/1210 case sizes typically loses roughly
10-25% of nameplate capacitance; X5R at the same package/voltage-fraction range
typically loses more (thinner dielectric layers for the same case size/voltage
rating), roughly 20-35%.

Applying that to the 50V-rated X7R shortlist at 12V (24% of rated) and 18V (36%):
**~12% loss at 12V, ~22% loss at 18V (estimate)**.

### 2.2 Ceramic bank

4x **1206B475K500NT** (4.7uF, 50V, X7R, 1206, Basic) = 18.8uF nameplate.
Effective (estimate): **~16.5uF @ 12V, ~14.7uF @ 18V**.

### 2.3 Bulk cap (screw-terminal cable-inductance damping)

Polymer aluminum recommended over plain electrolytic - same voltage margin
available, far lower ESR and far higher ripple-current rating, and electrolytic/
polymer capacitance (unlike ceramic) does **not** derate with applied DC bias, so
its 100uF nameplate holds at both 12V and 18V.

**MA35V100M6X8** (100uF, 35V, SMD polymer aluminum, D6.3xL7.7mm): ESR 30mOhm
@100kHz, ripple 2.9A @100kHz, endurance 2000h @105C, height 6.3mm. 35V rating
gives 1.94x margin over the 18V max (vs. only 1.39x for the cheaper 25V-rated
polymer parts also found - MA25V100M6x6/PH25V100M6X7), for the same performance
class and better LCSC stock (294,691 pcs). This is the clear pick over both the
25V polymer options and the plain 35V aluminum electrolytics found (which only
publish a 120Hz ripple figure of 87-230mA - no 100kHz figure - and ~600mOhm ESR,
i.e. ~20x worse than the polymer part at the switching frequency that matters here).

Total input bank effective capacitance: **~114.7uF @ 18V worst case / ~116.5uF
@ 12V** (bulk 100uF is bias-independent + ceramic bank derated as above).

### 2.4 Candidates (ranked)

**SUPERSEDED for the bulk cap and the X5R ceramic - see section 5.2/5.3.** The
architect requires the bulk cap ESR IN the 50-300mOhm window (damping, not loss)
and every MLCC to be X7R (board runs 83-87C, X5R is 85C-rated). Ranks 1, 4 and 6
are unchanged; ranks 2-3 and 5 are corrected.

| rank | mpn | lcsc | package | stock | Basic/Ext | price@qty1 | fit |
|---|---|---|---|---|---|---|---|
| 1 | 1206B475K500NT | C29823 | 1206 | 1,027,183 | **Basic** | $0.2697 | cin - PRIMARY ceramic (unchanged), 4.7uF/50V X7R, use x4 for ~18.8uF nameplate / ~14.7-16.5uF effective |
| 2 | KNM2100UF35V149EC0055 | C2982822 | SMD D6.3xL7mm | 11,986 | Extended | $0.1963 | cin - NEW PRIMARY bulk (KNSCHA "Polymer Aluminum", likely hybrid): 100uF/35V, ESR 80mOhm@100kHz - INSIDE the 50-300mOhm damping window, 1.516A ripple@100kHz, 2000h@105C. See 5.2 |
| 3 | JBLM2101M035C077RTM | C19270709 | SMD D6.3xL7.7mm | 4,913 | Extended | $0.2028 | cin - NEW bulk alt (DMBJ): same 80mOhm@100kHz ESR, 100uF/35V, 2000h@105C, drop-in footprint match for the old MA35V100M6X8 pick (D6.3xL7.7mm). See 5.2 |
| 4 | GRM32ER71H106KA12L | C77102 | 1210 | 199,910 | Extended | $0.3735 | cin - alt ceramic (Murata, unchanged), 10uF/50V X7R, fewer/bigger parts than 1206B475K500NT if board area allows (1210 footprint) |
| 5 | CGA0805X7R225M500MT | C23692980 | 0805 | 45,796 | Extended | $0.0466 | cin - NEW replacement for the X5R part below: 2.2uF/50V X7R, same 0805 footprint, cheaper than the X5R part it replaces. See 5.3 |
| 6 | CC0603KRX7R9BB104 | C14663 | 0603 | 37,743,265 | **Basic** | $0.0190 | cin - 100nF/50V X7R high-freq bypass at the IC VIN pin (unchanged), standard practice alongside the bank |
| 7 | MA35V100M6X8 | C46550467 | SMD D6.3xL7.7mm | 294,691 | Extended | $0.2276 | cin - REJECT (was rank 2/PRIMARY): 100uF/35V polymer Al, ESR 30mOhm@100kHz - BELOW the architect's 50-300mOhm damping floor. Architect: "no low-ESR polymer" - a low-ESR bulk cap removes cable-LC damping and pushes hot-plug ringing toward 25.4V. See 5.2 |
| 8 | CL21A225KBQNNNE | C377773 | 0805 | 1,716,209 | **Basic** | $0.0899 | cin - REJECT: 2.2uF/50V X5R. Board surface runs 83-87C, X5R is 85C-rated - not acceptable anywhere on this board. Replaced by rank 5. See 5.3 |
| 9 | RVT100UF35V67RV0034 | C2836442 | SMD D6.3xL7.7mm | 226,614 | Extended | $0.0372 | cin - REJECT (unchanged position, reasoning reinforced): plain Al electrolytic 100uF/35V, only 120Hz ripple spec published. A same-family sibling (RVE100UF35V67RV0072, same KNSCHA brand/footprint) DOES publish a 100kHz figure: 600mOhm - ABOVE the 300mOhm damping ceiling, confirming this whole plain-electrolytic sub-family is out of the window on the high side, not just under-specified. See 5.2 |

---

## 3. Output capacitors (Cout)

### 3.1 Ripple-only vs. load-step - which binds (assignment explicitly asks)

Ripple model dV = dI/(8*fsw*Cout) + dI*ESR. With MLCC-class ESR (few mOhm) the ESR
term contributes <1mV at these dI/fsw combinations - negligible. Solving the
capacitive term for dV=50mV at dI~0.9A (representative mid-band ripple):

| fsw | Cout_min for 50mV ripple alone |
|---|---|
| 400kHz | 5.6uF |
| 500kHz | 4.5uF |
| 600kHz | 3.75uF |
| 700kHz | 3.2uF |

Load-step formula (energy/charge balance, standard buck sizing method): with the
inductor current ramping at its duty-limited slew (Vin-Vout)/L, the charge deficit
during the ramp sets Cout = Iout_step^2 * L / (2*(Vin-Vout)*dV_target). **Worst
case is Vin=7V** (smallest Vin-Vout=2V => slowest inductor ramp => biggest Cout
requirement) - not Vin=18V, which is worst case for ripple. This is a real,
non-obvious distinction the brief's phrasing invites missing.

| L (from section 1) | Cout_min for 200mV load-step recovery, Vin=7V worst case |
|---|---|
| 10.0uH | 112.5uF |
| 8.2uH | 92.2uF |
| 6.8uH | 76.5uF |
| 4.7uH | 52.9uF |

**Finding, confirms the brief's warning**: load step drives Cout by roughly
15-20x over what ripple alone needs (92-112uF vs. 3.2-5.6uF for the primary
inductor candidates). Design the bank to the load-step number; ripple is then
satisfied by a wide margin with capacitance to spare. The 100us recovery-time
spec is loop-bandwidth/compensation dependent (IC choice, P2/P3 territory, not
resolvable from passives alone) - low-ESR MLCC bank supports whatever bandwidth
the eventual IC's compensation achieves; this research does not size for it
beyond "keep ESR low," which the MLCC choice already does.

### 3.2 DC-bias derating at 5V (again: no vendor curve found, estimate used)

Same caveat as section 2.1. 22uF/16V X5R 1206 at 5V (31% of rated): estimate
~25% loss. 22uF/25V X7R 1210 at 5V (20% of rated): estimate ~12% loss (X7R, larger
case, lower voltage fraction all push toward less loss).

### 3.3 Bank sizing (two worked examples, scale with whichever L the eventual IC needs)

- **8.2uH/500kHz case (needs ~92uF effective)**: 6x TCC1206X5R226K160HT (22uF/16V
  X5R 1206) = 132uF nameplate -> **~99uF effective @ 5V** (estimate). Clears the
  92uF target with ~8% margin.
- **10uH/400kHz case (needs ~113uF effective)**: 7x same part = 154uF nameplate ->
  **~116uF effective** (estimate). Or 6x TCC1210X7R226K250MT (22uF/25V X7R 1210,
  better bias linearity) = 132uF nameplate -> **~116uF effective** at only 12%
  estimated loss instead of 25% - fewer parts needed for the same effective C if
  1210 footprint is affordable, at ~1.5x the per-part cost and area.

Recommend confirming the exact part count against the final chosen L/fsw at P2
(circuit-designer) stage; this research fixes the sizing method and the per-part
effective-capacitance numbers, not a single final count, since the IC/fsw is not
yet chosen.

### 3.4 Candidates (ranked)

**SUPERSEDED - the architect requires every MLCC to be X7R (see section 5.3).**
The former rank 1 (X5R) is demoted to REJECT; the former rank-2 X7R alt is
promoted to PRIMARY. Section 5.3 recounts the bank size against the X7R's lower
DC-bias derating (~12% vs ~25% for X5R) for each candidate inductance value.

| rank | mpn | lcsc | package | stock | Basic/Ext | price@qty1 | fit |
|---|---|---|---|---|---|---|---|
| 1 | TCC1210X7R226K250MT | C49118556 | 1210 | 123,041 | Extended | $0.2181 | cout - PROMOTED TO PRIMARY (was rank 2): 22uF/25V X7R, ~12% est. bias loss @5V. Use x4-6 depending on final L/fsw - FEWER parts than the old X5R plan for the same effective C. See 5.3 for the recount |
| 2 | TCC0805X7R106K160FT | C380347 | 0805 | 262,101 | Extended | $0.0844 | cout - smaller-footprint fill-in value (unchanged), 10uF/16V X7R, for trimming the bank to an exact effective-C target without a full extra 22uF part |
| 3 | CC0805KKX7R7BB475 | C277499 | 0805 | 193,542 | Extended | $0.1279 | cout - small high-freq bypass near the FB/output test point (unchanged), 4.7uF/16V X7R |
| 4 | TCC1206X5R226K160HT | C5448976 | 1206 | 408,657 | Extended | $0.1412 | cout - REJECT (was rank 1/PRIMARY): 22uF/16V X5R. Board surface runs 83-87C, X5R is 85C-rated - not acceptable anywhere on this board. Replaced by rank 1 above. See 5.3 |

None of the Cout shortlist is Basic tier - JLC's 16V/25V-rated 10-22uF X5R/X7R
0805-1210 range is Extended-only on this search; acceptable per requirements
Q28 ("Extended acceptable where the function demands it").

---

## 4. Risks / flags for P2-P3

1. **Ferrite-wound shielded inductors (TDK VLS6045EX, cjiang FNR6045S, COILANK
   NR6045) all fail the 50C-ambient/no-airflow Itemp check** despite having the
   best DCR on the shortlist - do not let a later stage re-pick one of these on
   DCR/price alone without re-checking section 1.2.
2. No vendor DC-bias curve was found for any MLCC candidate (Cin or Cout) within
   this research pass - all bias-derated capacitance numbers in this file are
   conventional-industry estimates, not vendor-cited. If P2/P3 needs firmer
   numbers, Murata's SimSurfing tool (web, not fetchable by this offline method)
   or a direct vendor characterization request would be the next step.
3. Inductor DCR vs. thermal-margin is a real tradeoff, not a clean win: the
   safest-margin part (MDE0630-8R2M) costs ~60-100mW more DCR loss than the
   tighter-margin TDK SPM6530T-6R8M. Recommend keeping MDE0630-8R2M as primary
   given the "no airflow" environment is explicit and binding in the brief.
   **SUPERSEDED (P1 correction pass): the architect's `DCR<=25 mOhm` ceiling makes
   this whole tradeoff moot - MDE0630-8R2M's 60mOhm is 2.4x over the ceiling
   regardless of its thermal margin. See section 5.1; FAUL1050-6R8MT clears BOTH
   the DCR ceiling and the thermal margin with room to spare.**
4. Single-source risk: KOHERelec (MDE0630 family, top inductor pick) is a smaller
   brand than TDK/Murata/Samsung; no pin-compatible Basic-tier alternate exists at
   the same Itemp margin. TDK SPM6530T-6R8M is the best-pedigree fallback if
   KOHERelec sourcing is a concern, accepting the tighter thermal margin noted above.
   **UPDATE: the new inductor primary (FAUL1050-6R8MT) is cjiang, a different
   smaller brand; the new 400kHz pick (MDA1365-100M) IS KOHERelec again. Both
   cjiang and KOHERelec parts in this size class are electrically near-identical
   sibling designs (compare FAUL1040-6R8MT vs MDE1040-6R8M in 5.1: 25mOhm/12A/8.5A
   both), consistent with a shared/OEM base design - single-source risk is real
   across BOTH brands for this footprint class, not just KOHERelec. TDK
   SPM6530T-6R8M remains the best-pedigree fallback but no longer meets the DCR
   ceiling (see item 3).**
5. Output-cap bank part count is not finalized (6 vs 7 x 22uF, or a 1210 X7R swap)
   because it depends on the L/fsw the chosen buck IC ends up using - flagged as
   an open item for whoever picks the IC, not resolved here.
   **UPDATE: X5R TCC1206X5R226K160HT is now a hard REJECT (X7R-only rule, see 5.3),
   which resolves half the open item - the bank is TCC1210X7R226K250MT only. Count
   is still fsw/L-dependent; section 5.3 gives the recount per L value.**
6. **[NEW] Inductor core-loss curves were not found for ANY molded/alloy-composite
   candidate in this pass either** (FAUL1050/1350, MDA1365) - same "no vendor
   curve" gap the prior pass hit for DC-bias. The `150mW core allowance` in
   `power.json` (`l1_inductor.core_loss_mw_max`) is carried forward as an
   assumption regardless of which inductor P3 picks; it is not part-specific data.
7. **[NEW] MDA1365-100M's hot DCR sits AT the 25mOhm ceiling, not comfortably
   under it** (24.96mOhm using the architect's `x1.30` shorthand, 25.24mOhm using
   the more precise `1+0.00393*80` factor - see 5.1). Unlike the 500/600kHz
   primary (FAUL1050-6R8MT, ~24.05mOhm hot with real margin), a 400kHz design
   using MDA1365-100M has essentially zero DCR headroom once hot-derated; treat
   the L1 DCR loss-budget line as fully spent, not a source of margin, if this
   part is used.
8. **[NEW] The cjiang FAUL-series datasheet's Isat/Itemp table has a "Max"/"Typ"
   column pair where "Max" is the LOWER (conservative/guaranteed-worst-tolerance)
   number, not the higher one** - e.g. FAUL1050-6R8MT: Isat Max=12.3A/Typ=14A,
   Irms Max=8.0A/Typ=9.0A. `parts_search`'s single-value LCSC attributes pull the
   Typ column (14A/9.0A), NOT the conservative Max column - confirmed by
   cross-referencing the pulled cjiang PDF directly (`FAUL1050-6R8MT.pdf`, page
   17 table). All margin arithmetic in section 5.1 uses the conservative
   Max-column values, not the LCSC attribute values. **This risk likely applies
   to every inductor MPN in this file sourced via `parts_search` attributes
   alone (sections 1.2-1.4's original TDK/KOHERelec numbers were not
   cross-checked against a Max/Typ split in this pass) - re-verify against the
   underlying datasheet before treating any Isat/Itemp margin in this file as
   final.**
9. **[NEW] SLF12565T-100M4R8-PF (TDK, 10uH, DCR 20.2mOhm, stock 747) was found
   and REJECTED for two independent reasons**: (a) it is TDK "Wound ferrite"
   (Tmax 105C, same failure family as VLS6045EX/FNR6045S - see item 1), AND (b)
   its own datasheet header states `Discontinue Issue Date May.14, 2024 / Last
   Shipment Date December.31, 2026` - it is EOL and fails requirements Q24's "no
   EOL, no last-stock" rule outright regardless of its electricals. Documented as
   a second, independent instance of the ferrite trap plus a new EOL trap -
   `parts_search`'s live stock figure does not surface EOL status, so an EOL part
   can still show healthy stock; check the datasheet header, not just the stock
   count.

---

## 5. P1 CORRECTION PASS - power-architect budget landed after this research

New sweeps for this pass are `research/raw/magnetics-caps-v2-*.json` (one file per
query, script-written via `--out`; ~50 queries run - see the JSON filenames for the
full search trail). Two datasheets pulled and read in full: cjiang FAUL-series
catalog (`FAUL1350-6R8MT.pdf`, 28pp, covers the whole FAUL0412-FAUL1770 family) and
TDK SLF12565 (5pp, led to the item-9 reject above).

### 5.1 Inductor - is the 25 mOhm DCR ceiling reachable? YES, for 500/600kHz. Tight but yes at 400kHz.

**Root cause of the original gap, confirmed**: the first pass only searched
6x6mm-and-smaller packages. Re-searching 7x7 (7030), 8x8 (8040), 10x10 (1040/1050)
and up (13.5x12.5-13.5x12.8mm - footprint is cheap, DCR is not, per the brief)
across cjiang/KOHERelec/Bourns/Vishay/TDK/Wurth/Taiyo Yuden/Sunlord found parts
that clear the ceiling; none of the originally-searched small packages do.

**Ripple/dI at Vin=18V (worst case, unchanged formula from 1.1)**, at the two
inductances actually found to clear the ceiling:

| L | 400kHz | 500kHz | 600kHz |
|---|---|---|---|
| 10.0uH (MDA1365-100M) | dI=0.903A (30.1%), Ipk=3.45A | dI=0.722A (24.1%), Ipk=3.36A | dI=0.602A (20.1%), Ipk=3.30A |
| 6.8uH (FAUL1050-6R8MT) | dI=1.328A (44.3%, over the ~40% target) | dI=1.062A (35.4%), Ipk=3.53A | dI=0.885A (29.5%), Ipk=3.44A |

6.8uH does not fit the ripple band at 400kHz - use the 10uH pick there. AP64350SP-13
(rank-1 IC, `RT=200k -> 500kHz`) makes 500kHz the primary case, so **FAUL1050-6R8MT
(6.8uH) is the primary recommendation; MDA1365-100M (10uH) is the 400kHz answer**.

**Cold and hot DCR for every candidate that reached the ceiling search, plus the
original (now-rejected) shortlist for comparison** (hot = `x1.30` at 100C, the
architect's own shorthand in `power.md` s2; `P = I_L,rms^2 * DCR`, using the
architect's own 12V-spec-point `I_L,rms^2 = 9.06 A^2` from `power.json`
`loss_budget_w.at_12v.l1_dcr` basis, so these numbers are directly comparable to
the `0.290W` budget line for L1 DCR):

| Part | Package | DCR cold(20C) | DCR hot(100C) | P_hot | vs 0.290W budget line | Stock | DCR<=25 ceiling? |
|---|---|---|---|---|---|---|---|
| **FAUL1050-6R8MT** | 11.5x10mm | 18.5mOhm | 24.05mOhm | **0.218W** | -0.072W (25% under) | 763 | PASS, even hot |
| FAUL1350-6R8MT | 13.5x12.8mm | 18.0mOhm | 23.40mOhm | 0.212W | -0.078W (27% under) | 519 | PASS, even hot |
| SRP1265A-100M | 13.5x12.5mm | 16.5mOhm | 21.45mOhm | 0.194W | -0.096W (33% under) | 418 (FAILS >=500) | PASS, even hot |
| **MDA1365-100M** | 13.5x12.6mm | 19.2mOhm | 24.96-25.24mOhm | 0.226-0.229W | -0.061/-0.064W (21-22% under) | 645 | PASS cold, AT the line hot (see risk 7) |
| IHLP4040DZER100M11 | 10.8x10.2mm | 27.8mOhm | 36.14mOhm | 0.327W | +0.037W (13% OVER) | 4208 | FAIL cold already |
| MDE0630-8R2M (old #1) | 7.0x6.6mm | 60.0mOhm | 78.0mOhm | 0.707W | +0.417W (144% OVER) | 1029 | FAIL, 2.4x over |
| SPM6530T-6R8M (old #2) | 7.1x6.5mm | 53.3mOhm | 69.29mOhm | 0.628W | +0.338W (117% OVER) | 3719 | FAIL, 2.1x over |
| MDE0630-100M (old #3) | 7.0x6.6mm | 68.0mOhm | 88.40mOhm | 0.801W | +0.511W (176% OVER) | 914 | FAIL, 2.7x over |
| SPM6530T-100M (old #4) | 7.1x6.5mm | 72.5mOhm | 94.25mOhm | 0.854W | +0.564W (194% OVER) | 2075 | FAIL, 2.9x over |

**FAUL1050-6R8MT clears the ceiling even AFTER hot-derating** (24.05mOhm vs the
25mOhm limit, which the architect stated at 20C) - a genuinely better result than
the literal requirement asks for, and it improves the overall efficiency margin:
using it instead of the budget's assumed 32mOhm-hot / 0.290W allocation frees
~0.07W, moving the s2 total margin from 0.335W (16%) toward ~0.41W (~20%) if P2/P3
carry that saving through. MDA1365-100M (400kHz case) clears the ceiling cold with
real margin (19.2 vs 25mOhm, 23%) but sits almost exactly AT the ceiling once hot
(see risk item 7) - a real but tighter win.

**Core**: cjiang FAUL-series datasheet confirms "Wire Wound Molded SMD Power
Inductors" / **Alloy Sponge Powder core**, `-55C to +155C` (including
self-heating) - metal-composite/molded, not ferrite, consistent with the 1.2
preference. Tmax=155C is higher than either prior metal-composite family (TDK
SPM6530/KOHERelec MDE0630, both 125C), giving more Itemp headroom than anything
in the original shortlist. Height: FAUL1050 H(typ)=4.1mm, FAUL1350 H(typ)=5.5mm
(both from the datasheet's dimension table) - far under the 15mm cap.

**Isat/Itemp derating, same method as 1.2, applied to FAUL1050-6R8MT (conservative
Max-column values per risk item 8: Isat=12.3A, Irms/Itemp=8.0A)**:
- Itemp @ 50C ambient = `8.0 * sqrt((155-50)/(155-20))` = `8.0*0.882` = **7.06A**.
  Margin over the 3.0A continuous load: **+135%**.
- Isat hot (metal-composite ~11% convention from 1.2) = `12.3*0.89` = **10.95A**.
  Margin over Ipk (3.53A @ 500kHz, 3.44A @ 600kHz): **+210% / +218%**.

Both margins are 5-15x the tightest margins in the original (now-rejected)
shortlist (e.g. SPM6530T-100M's +1.4% Itemp margin) - this is not a marginal
call, the new part is comfortably better on every axis except unit price
($0.56 vs $0.21-0.26 for the old picks - still well inside the ~$3/line-item
flag threshold at qty 5).

**MDA1365-100M (400kHz pick) under the same method**, correcting its LCSC-attribute
values (13A/10A) by the same ~11-12% Typ-to-conservative gap found in the FAUL
datasheet (risk item 8 - KOHERelec's own Max/Typ split was not independently
confirmed, so this is an extrapolated, flagged estimate: conservative Isat~11.4A,
Irms~8.9A), and assuming Tmax=125C (KOHERelec's other metal-composite parts in
this file all spec 125C; not independently confirmed for MDA1365 specifically):
- Itemp @ 50C = `8.9*sqrt((125-50)/(125-20))` = `8.9*0.845` = **7.52A**, margin
  over 3.0A: **+151%**.
- Isat hot = `11.4*0.89` = **10.15A**, margin over Ipk (3.45A @ 400kHz): **+194%**.

Comfortable even under doubly-conservative assumptions - the risk with this part
is the DCR headroom (item 7), not the current margins.

**The 400kHz slot could not be cleanly closed**: SRP1265A-100M has the best DCR
found (16.5mOhm, PASS with room even hot) but its LCSC stock is 418, 82 pieces
short of the >=500 rule; IHLP4040DZER100M11 has the deepest stock (4208) but
misses the ceiling by 11%. MDA1365-100M threads the needle (passes both) but only
by clearing DCR with room and the hot-DCR line with almost none - report this
plainly rather than picking whichever number looks better: **the 400kHz case is
real-but-tight; the 500/600kHz case (FAUL1050-6R8MT) is a clean pass.**

**Answer to the architect: yes, 25 mOhm is reachable** - the >88% efficiency
requirement does not need to be re-cut. The gap was a search-radius problem (parts
this good exist only above 10x10mm), not a physics problem.

### 5.2 Input bulk cap - the 50-300 mOhm damping window

The architect's requirement (`power.json` `cin.bulk_esr_mohm_range: [50,300]`,
`power.md` s6) is explicit: the prior primary (MA35V100M6X8, 30mOhm polymer) is
BELOW the window and would remove the cable-LC damping that keeps the hot-plug
ring off the IC's VIN pin (would push it toward the 25.4V worst case instead of
the 18-20.3V the architect's damped cases show); the prior alternate
(RVT100UF35V67RV0034) only published a 120Hz ripple figure - no 100kHz ESR - so
its fit for the window was genuinely unknown, not just "probably high."

**This pass found the 100kHz ESR for that whole plain-electrolytic sub-family
directly**: a same-brand (KNSCHA), same-footprint (D6.3xL7.7mm) sibling,
RVE100UF35V67RV0072, publishes **600mOhm@100kHz** - confirming the family sits
ABOVE the 300mOhm ceiling, not just under-specified. Neither the too-low (30mOhm
polymer) nor the too-high (600mOhm plain electrolytic) end of KNSCHA's own product
line lands in the window - the window is occupied by a third, distinct KNSCHA SKU
line (`KNM` prefix, LCSC-categorized "Polymer Aluminum" but with ESR an order of
magnitude above the pure-polymer `MA`/`PA` lines - almost certainly a hybrid
polymer/liquid-electrolyte construction, though the datasheet does not use the
word "hybrid" explicitly):

| mpn | lcsc | brand | package | ESR@100kHz | ripple@100kHz | life | stock |
|---|---|---|---|---|---|---|---|
| **KNM2100UF35V149EC0055** | C2982822 | KNSCHA | SMD D6.3xL7mm | **80mOhm** | 1.516A | 2000h@105C | 11,986 |
| JBLM2101M035C077RTM | C19270709 | DMBJ | SMD D6.3xL7.7mm | **80mOhm** | 1.87A | 2000h@105C | 4,913 |
| SPZ1VM101E08O00RAXXX | C122240 | - | Plugin(THT) D6.3xL8mm | 50mOhm | 2.35A | 2000h@105C | 135,629 |
| MA35V100M6X8 (rejected) | C46550467 | KNSCHA | SMD D6.3xL7.7mm | 30mOhm (BELOW window) | 2.9A | 2000h@105C | 294,691 |
| RVE100UF35V67RV0072 (rejected) | C2836437 | KNSCHA | SMD D6.3xL7.7mm | 600mOhm (ABOVE window) | 230mA@120Hz only | 2000h@105C | 385,327 |

SPZ1VM101E08O00RAXXX is excluded despite its ESR fitting (50mOhm, at the very
floor of the window) and enormous stock: it is a THT/Plugin part, which conflicts
with requirements Q26 (single-sided top-only SMT assembly).

**KNM2100UF35V149EC0055 is the pick**: both electrical requirements are cleanly
inside the window (80mOhm vs the 50-300mOhm range, not at either edge), 100uF/35V
(1.94x margin over the 18V max, same as the old pick), 105C/2000h (same life
figure the architect's 4.3 note already accepted, ~11,300h at the ~80C input-edge
placement), and ripple current (1.516A@100kHz) is far above what it actually
carries (power.md 4.3: "the bulk aluminum's ESL means it carries almost none of
the 1.5A rms at 500kHz"). Height 7mm, under the 15mm cap. JBLM2101M035C077RTM is
kept as the alternate specifically because its D6.3xL7.7mm footprint is a drop-in
match for the old MA35V100M6X8 footprint if P5/P6 already laid out around that
size.

No vendor datasheet PDF was fetched for either KNM2100UF35V149EC0055 or
JBLM2101M035C077RTM in this pass (ESR/ripple/life came directly from
`parts_search`'s structured LCSC attributes, which is the same source the prior
pass trusted for MA35V100M6X8's numbers) - flagged per the file's existing
discipline, not independently re-verified against a PDF the way the inductor
picks were.

### 5.3 X7R-only MLCCs - drop every X5R, recount the Cout bank

Two X5R parts existed in the prior shortlist; both replaced:

- **Cout PRIMARY, TCC1206X5R226K160HT (X5R) -> TCC1210X7R226K250MT (X7R)**. This
  was already the prior scout's rank-2 alternate (22uF/25V, ~12% est. bias loss at
  5V vs ~25% for the X5R part) - promoted, not newly found.
- **Cin alt, CL21A225KBQNNNE (2.2uF/50V X5R, 0805) -> CGA0805X7R225M500MT
  (2.2uF/50V X7R, 0805)**. Same value, voltage and footprint; live search
  (`2.2uF 50V X7R`) found no Basic-tier 2.2uF/50V X7R part (only a 1uF/50V X7R
  0805 Basic part, CL21B105KBFNNNE, exists at that combination) - the replacement
  is Extended-tier, same as the part it replaces was Basic-tier. Stock (45,796)
  is far above the >=2000 passives threshold and it is CHEAPER than the X5R part
  it replaces ($0.0466 vs $0.0899).

**Cout bank recount** (load-step formula unchanged from 3.1/3.3:
`Cout = Iout_step^2 * L / (2*(Vin-Vout)*dV_target)`, worst case Vin=7V, verified
by reproducing the 3.3 table's 76.5/92.2/112.5uF targets exactly), now against
the X7R part's ~12% est. bias loss instead of the X5R part's ~25%, and against
the corrected inductor values from 5.1:

| L (fsw case) | Load-step target | X5R plan (25% loss, OLD) | X7R plan (12% loss, NEW) | Recommended |
|---|---|---|---|---|
| 6.8uH (500-600kHz, NEW primary) | 76.5uF | not previously sized for this L | 4x = 88uF nameplate -> 77.4uF eff (1.2% margin, thin) OR 5x = 110uF -> 96.8uF eff (26.5% margin) | **5x TCC1210X7R226K250MT** |
| 8.2uH (500kHz alt, no longer the primary L) | 92.2uF | 6x = 132uF -> 99uF eff (8% margin) | 5x = 110uF -> 96.8uF eff (5% margin) OR 6x = 132uF -> 116uF eff (26% margin) | 5-6x, per available board area |
| 10uH (400kHz, MDA1365-100M) | 112.5uF | 7x = 154uF -> 116uF eff (3% margin) | 6x = 132uF -> 116.2uF eff (3.2% margin) | **6x TCC1210X7R226K250MT** (matches the prior scout's own 3.3 finding, now confirmed as the X7R count) |

**Net effect of the X7R switch**: same or FEWER parts than the X5R plan (5-6 vs
6-7) for equal or better margin, on top of fixing the 85C-vs-83-87C-board latent
failure that was the actual reason for the mandate. The 6.8uH/500-600kHz row is
new work (the X5R-era file never sized Cout against 6.8uH because that L wasn't
identified as the likely band until 5.1 above); 8.2uH is carried forward for
reference only since FAUL1050-6R8MT (6.8uH) is now the primary inductor pick, not
an 8.2uH part.
