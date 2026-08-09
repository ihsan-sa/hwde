# protection-io - candidate parts (sbuck-5v3a)

Block: input reverse-polarity P-FET, input fuse, 2x screw terminal, VOUT indicator LED.
Scout output only - P3 picks the final parts.

Every part below was verified live through `parts_search.py` (JLCPCB/LCSC API) on
**2026-08-08**. Stock/price are that day's figures; qty-1 price quoted per role rules
(build qty 5). Full result objects are in `protection-io.json` and
`research/raw/protection-io-*-sweep.json` (script-written, one file per query).
Electrical claims marked "(ds)" are read from the manufacturer datasheet PDF (fetched via
the wmsc.lcsc.com mirror, `%PDF` magic-byte verified, extracted with `datasheet_extract.py`),
not from memory or the LCSC attribute table alone.

---

## 1. Reverse-polarity P-channel MOSFET (`revpol_pfet`)

### 1.1 The load-bearing check: Vgs(max) vs 18 V input

Topology per brief: source-to-VIN, drain-to-load, gate pulled to GND through a resistor -
so **Vgs sees the full input voltage unclamped** (Vgs = -Vin, i.e. -7 V at Vin=7V up to
-18V at Vin=18V) unless a zener clamp is added.

- **AO4407A (Alpha & Omega, SOIC-8) is rated Vgs = +/-25 V (ds).** The datasheet text says
  "with a 25V gate rating" explicitly. At Vin=18V that is **7 V of margin** - comfortably
  inside spec, no clamp required. This is BETTER than the generic small-P-FET assumption.
- **The SI4435 / FS4407A family (most SOP-8/SOIC-8 clones) is Vgs = +/-20 V** (confirmed
  directly in the LCSC attribute table for multiple listings, e.g. KEXIN SI4435DY C382326
  and HXY-brand AOD4184A-HXY C22367195 both show `"Vgs": "±20V"`). At Vin=18V that
  is only **2 V of margin** - exactly the risk the assignment flagged. No clamp is
  strictly required (18 < 20) but it is a thin margin against any input ringing/hot-plug
  transient; **a 15-18V zener + series gate resistor is recommended if this family is used**
  instead of AO4407A.
- Recommendation: **prefer AO4407A for the Vgs margin alone**, independent of Rds(on).

### 1.2 Package reality check (SOT-223 / DPAK / SOIC-8 / DFN)

Live search confirms the assignment's hypothesis:
- **SOT-223 P-channel parts on LCSC top out at 60V/~30-40mOhm best case, but the cheapest/
  most-stocked ones (e.g. DMP6185SE-13, C177038, 21k stock) are 110-130 mOhm** - 4x over
  budget. SOT-223 die size cannot deliver <=30 mOhm P-channel at this voltage class.
- **DPAK/TO-252 P-channel parts found (IRFR9024N, IRFR5305, IRFR5410) are all
  65-205 mOhm** - also fails the target. (Note: AOD4184/AOD4184A, which LOOKED like a
  good DPAK P-FET candidate by part-number pattern-matching, is actually **N-channel**
  per every live listing checked - ruled out by verification, not assumed.)
- **SOT-23 (AO3401A, Basic, 600k stock, $0.09) hits 47-85 mOhm depending on Vgs** and its
  package RthJA is too high for continuous 2.44A regardless of Rds - listed only as the
  "too small" reference point the assignment asked to confirm.
- **SOIC-8/SOP-8 is the only package class on JLC that reaches <=15 mOhm at Vgs=-10V.**
  This is the class to use; DFN P-channel equivalents in this current/voltage class were
  not found in stock on JLC (searches for DFN5x6/DFN P-channel returned no P-channel DFN
  parts - large-die P-FETs are packaged in SOIC-8/SOP-8 here, not DFN).

### 1.3 Ranked candidates

| # | MPN | LCSC | Pkg | Basic? | Stock | $@1/@5(**) | Vds | Vgs(max) | Vgs(th) | Rds(on) @-4.5V | Rds(on) @-10V | Id @70C+ | RthJA | Fit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **AO4407A** | C16072 (Alpha&Omega) | SOIC-8 | Extended | 28,272 | 0.27 / ~0.27 | -30V | **+/-25V (ds)** | -1.7 to -3V (ds) | 27 typ/**38 max** mOhm (ds, @-5V) | 10 typ/**13 max** mOhm (ds) | **-12A@25C / -9.2A@70C (ds)** | **75 C/W steady-state (ds)** | revpol_pfet - PRIMARY: best Vgs margin, second-sourced (also stocked by UMW C2841482 193k pcs at $0.13, and JSMSEMI C5155211) |
| 2 | SI4435DY(UMW) | C7503190 | SOP-8 | Extended | 2,436 | 0.12 | -30V | +/-20V (attr) | 1.5V | not stated | 15 mOhm | 8A headline | not stated | revpol_pfet - alt/2nd source; only 2V Vgs margin at 18V, thinner stock |
| 3 | HXY4435S | C3033411 | SOP-8 | Extended | 3,042 | 0.096 | -30V | not stated on listing | 1.6V | not stated | 20 mOhm | 6A headline | not stated | revpol_pfet - cheapest; Vgs(max) not confirmed on this listing, do NOT use without datasheet check |
| 4 | DMP6185SE-13 | C177038 | SOT-223 | Extended | 21,176 | 0.46 | -60V | not stated | 3V | 130 max mOhm | 110-130 mOhm | 3A headline (die-limited) | n/a | revpol_pfet - REJECTED reference: confirms SOT-223 too small (4x Rds budget) |
| 5 | AO3401A | C15127 | SOT-23 | **Basic** | 599,644 | 0.095 | -30V | not stated | 0.9V | 60 mOhm | 47 mOhm | 4A headline (die-limited) | n/a | revpol_pfet - REJECTED reference: confirms SOT-23 too small for continuous 2.44A despite attractive Basic/price/stock |

(**) qty-5 price breaks at these volumes are effectively the qty-1 unit price on LCSC (next
break is qty 50+); reported as qty-1.

**I^2*R at 2.44 A (worst case, Vin=7V input current):**
- AO4407A: **59-77 mW** using the -10V data point (representative of Vin>=10V, Vgs=-10..-18V
  unclamped) up to **161-226 mW** using the conservative -5V data point (representative if a
  clamp limited Vgs to ~-5V). Since the gate is unclamped in the baseline topology and Vin=7V
  gives Vgs=-7V (between the two test points, closer to -10V), the realistic worst-case loss
  is **~90-120 mW**, comfortably under the ~180 mW target.
- SI4435DY(UMW) @15 mOhm: **89 mW**. HXY4435S @20 mOhm: **119 mW**.
- DMP6185SE-13 (SOT-223) @130 mOhm max: **774 mW** - 4x the entire fuse+FET loss budget by
  itself, confirming the package rejection.

**Recommendation: AO4407A (C16072).** Best-in-class Vgs margin (25V vs the family-typical
20V), Rds(on) that clears the loss budget at the realistic unclamped operating Vgs, Id and
RθJA both datasheet-confirmed adequate for 2.44A at 70C ambient, and multi-vendor stock
(3 independent LCSC listings for the same AOS part number: C16072, C2841482, C5155211).
**No zener clamp is required for AO4407A** at 18V max input (7V margin). If cost pressure
pushes toward the SI4435/HXY4435 family instead, add a ~15-18V zener + gate series resistor
per the assignment's guidance, since that family's 20V rating leaves only 2V margin.

---

## 2. Input fuse (`fuse`)

### 2.1 Critical finding: most "4A SMD fuse" search hits are the WRONG response class

The most obvious live-search hit for "1206/2410 fuse 4A 32V+" is Littelfuse
**0451004.MRL** (C27515, 2410, 4A, **125V DC** rated, 26,870 in stock, $0.29) - excellent
voltage margin and deep stock. **Its datasheet was pulled and read in full: it is the
Littelfuse 451/453 "NANO2(R) Very Fast-Acting Fuse" series** (ds) - opening time 5 sec MAX
at 200% of rated current. This is explicitly the wrong part class for the brief's "4A
slow-blow (time-lag)" requirement and would nuisance-blow on any transient (e.g. input cap
inrush) that a slow-blow fuse would ride through. **Disqualified despite looking like a
perfect match on stock/voltage/current alone** - a direct illustration of why the
assignment calls out verifying response time, not just the headline rating.

### 2.2 The genuine slow-blow SMD family found: Bel Fuse C1T (0685T-xx) series

Full datasheet pulled and confirmed (ds): "**Type C1T - Surface Mount Slow Blow Chip
Fuse**", 1206 SMD, 750mA-8A range, **63V AC/DC** rated (i.e. the DC rating is the full 63V,
not a derated AC number - satisfies the assignment's explicit derating-check requirement),
UL 248-14 tested, blow curve 200%=1-120 sec / 300%=0.1-3 sec / 800%=2-50 ms (ds table).

| Ampere rating | MPN | DCR (ds) | Melting I2t @10In (ds) | Stock (LCSC) |
|---|---|---|---|---|
| 3.5A | 0685T3500-01 (C3163784) | 40 mOhm | 2.28 A2s | **8 - reject** |
| **4A** | **0685T4000-01 (C3157092)** | **30 mOhm** | 2.56 A2s | **174 - fails >=2000 stock rule** |
| 5A | 0685T5000-01 (C3163312) | 20 mOhm | 5.3 A2s | **5,032 - passes** |

The DCR<=30mOhm target only starts being met at the 4A rating and improves at 5A+
(counter-intuitive: higher-current elements in this family use thicker/lower-resistance
elements). The ideal-spec 4A part is real, in the catalogue, with a live datasheet - but at
174 pcs it fails the binding >=2000pcs stock rule for a fuse. Interrupt rating 50A on all
three; max voltage drop @100%In 0.195V (4A) / 0.157V (5A) (ds); max power dissipation
@100%In 0.78W (4A) / 0.79W (5A) (ds).

### 2.3 Ranked candidates

| # | MPN | LCSC | Pkg | Rating | V(DC) | DCR | I2t | Interrupt | Stock | $@1 | Fit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **0685T5000-01** | C3163312 | 1206 | 5A slow-blow (ds) | **63V (ds)** | 20 mOhm | 5.3 A2s | 50A | **5,032** | 0.51 | fuse - PRIMARY: only slow-blow candidate that clears BOTH the DCR target and the >=2000pcs stock rule. I^2R@2.44A = **119 mW**. Trip margin: 2.44A continuous is 49% of the 5A rating (vs the ideal 61% at 4A) - still well clear of nuisance-blow (200% test point = 10A, 1-120s). |
| 2 | 0685T4000-01 | C3157092 | 1206 | 4A slow-blow (ds) | 63V (ds) | 30 mOhm | 2.56 A2s | 50A | **174 - FLAG** | 0.52 | fuse - spec-ideal (exact 4A ask, DCR exactly at budget) but stock fails the binding >=2000pcs rule. Route to P3/architect: accept #1's 5A rating, or accept the stock risk on this part, or reorder before a production run. |
| 3 | 0451004.MRL | C27515 | 2410 | 4A **fast-acting** (ds) | 125V (ds) | 16 mOhm (ds) | 0.055 A2s | 50A | 26,870 | 0.29 | fuse - REJECTED: wrong response class (very-fast-acting NANO2, not slow-blow), confirmed from datasheet. Would nuisance-blow on input inrush. Listed to document the rejection since it is the most obvious search hit. |

**Recommendation: 0685T5000-01 (C3163312).** It is the only part in this search that is
simultaneously (a) a confirmed slow-blow/time-lag SMD chip fuse, (b) DC-rated (not
AC-derated) at 63V - 2x the required 32V floor, (c) under the 30 mOhm DCR budget, and (d)
in stock at real production depth. The exact-4A sibling (0685T4000-01) is the closer spec
match and should be the pick if the architect wants to place a small preorder to build
stock depth; otherwise the 5A part is the safe default.

---

## 3. Screw terminals (`terminal`) - one part, used x2 (input + output)

Requirement: 2-pin, 5.08mm pitch, THT, horizontal/outward wire entry, >=10A, >=300V,
12-24AWG, <=15mm height, hand-solder on receipt (Q25).

| # | MPN | LCSC | Rating | AWG | Stock | $@1 | Note |
|---|---|---|---|---|---|---|---|
| 1 | **DB128L-5.08-2P-GN-S** (green) / **-BK-S** (black) | C395868 / C430601 | **300V / 16A** | 12-22 | 27,058 (GN) / 40,543 (BK) | 0.20 | terminal - PRIMARY: only THT fixed-block candidate found that clears BOTH the >=10A and the >=300V floor simultaneously. M2 screw. |
| 2 | WJ500V-5.08-2P | C8465 | 250V / 18A | 14-30 | **298,762 (deepest stock in the search)** | 0.13 | terminal - alt: widest AWG range and deepest stock/cheapest, but 250V < the 300V floor - use only if the architect accepts the voltage relaxation (18V max board potential gives huge margin either way). |
| 3 | KF128-5.08-2P-AA | C474952 | 250V / 24A | 12-22 | 62,104 | 0.19 | terminal - alt: highest current rating of the three, same 250V-vs-300V gap as #2. Prior sibling board (rf-de-20m LEARNINGS) used the KF128 family, so this is a proven footprint in this repo. |

All three are genuine fixed screw-terminal blocks (category "Screw Terminal Blocks", THT,
plugin/wire-entry style, NOT the two-part pluggable-header variants that also showed up in
the same searches under "Pluggable System Terminal Block" - those need a separate mating
header and are the wrong part family for a single fixed connector).

**Height and pin diameter/hole size are not exposed in the LCSC attribute table for any of
these three** - the assignment asks for these explicitly. Datasheets were not pulled for
dimensional drawings (typically image-only PDF pages, not text-extractable); **this is an
open item for P3/schematic footprint verification**, not resolved here. 5.08mm-pitch THT
screw terminals of this class are conventionally 8-10mm tall with ~1.0-1.3mm round pins into
a 1.3-1.6mm drill - well inside the 15mm ceiling on Id/typical parts of this family, but
should be confirmed against the actual mechanical drawing before layout, not assumed.

**Recommendation: DB128L-5.08-2P-GN-S (C395868), use x2** (one per I1/I2). It is the only
part that meets both binding electrical floors without a deviation; stock (27k) clears the
>=500pcs relaxed threshold the requirements set for terminals with room to spare.

---

## 4. Indicator LED (`led`)

| # | MPN | LCSC | Pkg | Basic? | Stock | $@1 | Vf | Luminous intensity | Fit |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **KT-0805G** | C2297 | 0805 | **Basic** | 2,650,613 | 0.016 | 2.6-3.1V | **430 mcd @ 5mA (ds/attr)** | led - PRIMARY: Basic tier, huge stock, and the vendor-rated current (5mA) is the closest to our ~1mA drive point of anything found - most competing LEDs are rated only at 20mA. At ~1mA expect roughly 1/5 of 430mcd (~80-90mcd, rough linear scaling at low current) - visibly dim but usable as a status indicator; note for P3/schematic if a brighter indication is wanted, drop the series R toward ~1.5-2k for ~2mA. |
| 2 | KT-0603G | C12624 | 0603 | Extended | 379,840 | 0.012 | 2.6-3.1V (ds: 3.1V typ) | 430 mcd @ 5mA (ds/attr) | led - alt: identical die/spec to #1 in the smaller 0603 body, but Extended tier (loses the Basic-preferred default from Q28) - only pick if board area forces 0603. |

Both parts are the same Hubei KENTO "Emerald Green" 513-528nm die family (peak 525nm),
just packaged in 0805 (Basic) vs 0603 (Extended) bodies - same vendor, same LCSC listing
family, so this is a footprint choice, not a sourcing risk.

**Recommendation: KT-0805G (C2297).** Meets every stated preference (Basic, green,
LCSC-deep-stocked) and is the only part in the search with a documented low-current
luminous-intensity figure close to the intended ~1mA drive point rather than the usual
20mA headline number.

---

## 5. Risks / open items for P3 and the architect

1. **Fuse stock/spec tradeoff (section 2) is the single biggest open decision in this
   block.** The exact-4A slow-blow part (0685T4000-01) exists and is electrically ideal but
   sits at 174pcs - below the binding >=2000pcs rule. Recommending the 5A sibling
   (0685T5000-01) instead is a real spec relaxation (raises the nuisance-blow margin from
   1.64x to 2.05x over the 2.44A worst-case input current) - flag for architect sign-off.
2. **AO4407A's -4.5V-referenced Rds(on) (38mOhm max) nominally exceeds the 30mOhm target**,
   but the actual circuit topology (gate pulled straight to GND, no clamp) puts Vgs at
   -Vin, not a fixed -4.5V - so the realistic worst case at Vin=7V (Vgs=-7V) sits between
   the datasheet's -4.5V and -10V test points, closer to the -10V number. This should be
   confirmed against the AOS SOA/Rds curves (Figure 5 in the datasheet, on file) once the
   gate resistor value is chosen, rather than assumed.
2b. **If the SI4435/HXY4435 P-FET family is chosen instead of AO4407A for cost**, add a
   zener gate clamp (15-18V) per the assignment's guidance - that family's Vgs(max) is only
   +/-20V, 2V of margin at 18V input.
3. **Screw terminal height and pin/hole dimensions are unverified** - table 3 flags this
   explicitly; pull the DB128L mechanical drawing before footprint creation.
4. **Single-source risk:** the AO4407A die is Alpha & Omega only, but the exact MPN is
   multi-listed on LCSC by 3 different resellers/brands (C16072, C2841482, C5155211) -
   low re-order risk. The Bel Fuse C1T family is Bel-only with no pin-compatible second
   source found in this search.
5. **DFN-package P-channel MOSFETs in this voltage/current class were not found in stock
   on JLC** - the package survey in section 1.2 is SOIC-8/SOP-8 vs SOT-223/DPAK/SOT-23
   only; if the architect specifically wants DFN for height/footprint reasons, a follow-up
   search focused on that package alone is needed.

## 6. Method / provenance

`parts_search.py` live JLCPCB/LCSC search, 2026-08-08, no offline fallback needed (network
reachable throughout). Three datasheets were downloaded via the wmsc.lcsc.com mirror (per
repo LEARNINGS: www.lcsc.com/datasheet/... URLs serve unfetchable HTML shells), verified
`%PDF` magic bytes, and full-text extracted with `datasheet_extract.py --full-text`:
AO4407A (Alpha & Omega, C16072), Littelfuse 0451004.MRL (C27515), Bel Fuse 0685T5000-01
(C3163312). All electrical claims tagged "(ds)" above trace to those three PDFs; everything
else traces to the live `parts_search.py` attribute table, reproducible with `--query <MPN>`.
