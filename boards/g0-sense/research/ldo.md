# research: ldo (fixed 3.3 V regulator)

Block: fixed 3.3 V LDO from USB-C VBUS. Must-haves derived from
`requirements.md` + assignment: Vin 4.5-5.5 V nominal (transients to ~6 V),
Vout 3.3 V fixed, Iout rating >= 300 mA, SMD/single-sided top assembly, JLC
Basic/Preferred strongly preferred (AMS1117-3.3 class explicitly acceptable),
qty-5 economy PCBA. Worst-case dissipation used throughout: P = (5.0 - 3.3) V
x 0.3 A = **0.51 W** (the brief's own number for "rated for the full 300 mA+
case"); realistic on-board+Qwiic load is ~150 mA / 0.26 W.

All rows verified live via `parts_search.py` (source: live JLCPCB, today).
Full first-pass sweep: `research/raw/ldo-sweep.json`.

## Ranked candidates

| Rank | MPN | LCSC | Pkg | Basic | Stock | Price@qty5 | Iout max | Dropout | Iq | theta-JA (no HS) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AMS1117-3.3 | C6186 | SOT-223 | **Basic** | 1,144,285 | $0.2019 | 1 A | 1.1 V typ / 1.3 V max @0.8A | 5 mA typ / 11 mA max | 90 C/W min-copper, 45-55 C/W w/ recommended copper |
| 2 | AP2112K-3.3TRG1 | C51118 | SOT-25-5 | Extended | 71,461 | $0.1761 | 600 mA | 125 mV typ/200 mV max @300mA | 55 uA typ / 80 uA max | 184 C/W |
| 3 | RT9013-33GB-MS | C7434207 | SOT-23-5 | Extended | 142,919 | $0.0583 | 500 mA (claimed) | 300 mV @200mA (not spec'd @300mA) | 60 uA typ | not published (Pd=300mW is the only rating given) |
| 4 | TLV70233DBVR | C26833 | SOT-23-5 (DBV) | Extended | 6,853 | $0.1837 | 300 mA | 260 mV typ/375 mV max @300mA | 35 uA typ / 55 uA max | 200 C/W |

Price = qty-5 build break (all four have their qty>=1 tier still active at
qty 5; no break until qty 50-100).

## Per-candidate detail

### 1. AMS1117-3.3 (C6186, Basic) - TOP PICK per fit+Basic+thermal
Datasheet: Advanced Monolithic Systems AMS1117, `research/raw` citation above.
- Current limit 900 mA min / 1500 mA max; guaranteed load reg. spec to 0.8 A.
  Comfortably covers the >=300 mA floor and the 150 mA realistic load.
- Dropout 1.1 V typ / 1.3 V max at 0.8 A (worse above 0.8 A, better below);
  at Vin=4.5 V this still clears Vout=3.3 V with margin. Iq 5 mA typ / 11 mA
  max - the highest quiescent draw of the four, worth flagging per the
  assignment brief but not disqualifying (30-150 mA on-board load dwarfs it).
- **Output cap: datasheet explicitly requires >=22 uF SOLID TANTALUM** for
  stability "under all operating conditions" (Application Hints, Stability
  section) - ceramic alone is not the datasheet's endorsed path. This is
  load-bearing for P3/P4: do not substitute a 22 uF ceramic without
  re-checking, ESR characteristics differ from tantalum. Input cap value is
  NOT stability-critical per this datasheet (no explicit CIN spec found);
  a 10 uF ceramic bypass is standard practice on a 5 V rail.
- Thermal: SOT-223 has a metal tab bonded to pin 2 (VOUT). Thermal
  resistance junction-to-tab = 15 C/W; theta-JA = 90 C/W at minimum copper,
  falling to **45-55 C/W** with a "reasonable sized" copper pour (datasheet
  Table 1: e.g. 1000 mm^2 top-side + 1000 mm^2 back-side plane -> 60 C/W;
  2500/2500 mm^2 -> 55 C/W). At the 0.51 W worst case and 55 C/W: Tj = 40 C
  ambient + 28 C rise = **68 C** - large margin to the 125 C max junction
  spec (165 C thermal shutdown). Even the no-copper 90 C/W case (46 C rise)
  stays under 90 C. This is the only candidate with real thermal headroom
  at the stated worst case.
- **JLC economics note**: the identical AMS1117-3.3 MPN also exists as an
  Extended SKU (C347222, $0.0484, stock 1.58M) at ~4x lower unit price -
  but Extended parts carry a one-time JLC assembly setup fee (~$3) that
  dominates total cost at qty 5. The Basic SKU C6186 is very likely cheaper
  delivered despite the higher catalog unit price; P3/order phase should
  confirm against current JLC fee schedule.

### 2. AP2112K-3.3TRG1 (C51118, Extended)
Datasheet: Diodes Inc. AP2112, DS39724 Rev 2-2 (18pp, full elec. tables read).
- 600 mA min continuous rating (spec'd to 0.985/1.015 Vout at 3.3 V,
  IOUT<=30mA condition; load reg. table covers 1-600 mA). Comfortably above
  the 300 mA floor.
- Dropout 125 mV typ / 200 mV max @300 mA, 250 mV typ / 400 mV max @600 mA -
  far better than AMS1117. Iq 55 uA typ / 80 uA max, standby (EN low)
  0.01 uA typ / 1 uA max - the low-Iq alternative the assignment flagged.
- Caps: CIN = COUT = 1.0 uF ceramic, **X5R/X7R dielectric recommended**
  (Note 4) "if 1.0uF ceramic capacitor is selected" - no separate ESR floor
  given in the sections read; ceramic-stable design (no AMS1117-style
  tantalum requirement).
- Thermal: **theta-JA (no heatsink) = 184 C/W** for the SOT25/SOT-23-5
  package (junction-to-case only 96 C/W, but no exposed pad to exploit it
  from the top side). At the 0.51 W worst case: 184 x 0.51 = 94 C rise ->
  Tj = 40 + 94 = **134 C** at 40 C ambient - only ~16 C below the 150 C
  absolute-max junction rating, i.e. thin-to-no safety margin under
  continuous full load. At the realistic 150 mA / 0.26 W load: 48 C rise,
  Tj = 88 C - fine. **Risk**: this part is thermally solid for the
  realistic load but marginal for the brief's literal "rated for the full
  300 mA+ case" requirement in this small package.
- A same-die SOT-89-5 variant (theta-JA 120 C/W, better tab) exists in the
  Diodes family, but the only matching LCSC SKU found (AP2112R5-3.3TRG1,
  C5564063) shows **stock = 1** - not usable at qty 5, noted for
  completeness only.
- Extended part: JLC one-time setup fee applies.

### 3. RT9013-33GB-MS (C7434207, Extended)
Datasheet: MSK Semi 2nd-source datasheet for RT9013-33GB-MS (thin, ~9pp,
Chinese-language, full text read).
- Claims 500 mA max output current (VIN=VOUT+1V condition) and 60 uA typ
  quiescent current (1 uA in shutdown) - matches catalog attributes.
- **Data gap**: the electrical table only characterizes dropout at 100 mA
  (100 mV) and 200 mA (300 mV) - it does NOT give a dropout number at
  300 mA or 500 mA despite claiming a 500 mA max rating. Treat the 500 mA
  claim as unverified until cross-checked against Richtek's original
  RT9013 datasheet at P3 (this is a second-source clone, not the original
  IDM's datasheet).
- Caps: test condition is Cin=Cout=1 uF (implies ceramic-stable CMOS
  topology like AP2112K/TLV70233), but no explicit ESR range or dielectric
  recommendation is given anywhere in this datasheet - another gap to
  close at P3.
- Thermal: the ONLY rating given is a flat **Pd (package dissipation) =
  300 mW** for the SOT-23-5L package (ambient condition not stated). The
  0.51 W worst case is **70% over this rating even in the best case** -
  on the numbers this datasheet publishes, the part does not clear the
  brief's literal 300 mA+/0.51 W thermal requirement. At the realistic
  150 mA / 0.26 W load it is under the 300 mW figure with modest margin.
- Cheapest of the four and deepest stock (142,919) - attractive if the
  architect decides the realistic 150 mA case (not the literal 300 mA+
  case) is the governing thermal design point.

### 4. TLV70233DBVR (C26833, Extended)
Datasheet: Texas Instruments TLV702xx, SLVSAG6B (29pp, full elec./thermal/
app-info tables read via pdftotext - genuine TI-authored datasheet, best
documentation quality of the four).
- Output current limit spec'd at exactly 300 mA (ICL min -2/typ 500/max
  860 mA is the FAULT current limit, not a continuous rating - the device
  is only characterized/guaranteed as a "300-mA" part per its own name and
  dropout table). This clears the floor with **zero headroom** versus the
  other three candidates' higher rated currents.
- Dropout 260 mV typ / 375 mV max @300 mA - second-best of the four. Iq
  35 uA typ / 55 uA max - the lowest of the four (best for the Qwiic-idle
  case). Shutdown current ~400 nA.
- Caps: 1.0 uF X5R/X7R ceramic recommended in+out; datasheet states the
  device is stable down to 0.1 uF EFFECTIVE output capacitance, and gives
  an explicit numeric floor: **output cap max ESR < 200 mOhm**. Input cap
  not required for stability but recommended (0.1-1.0 uF, low ESR).
- Thermal: **theta-JA = 200 C/W** (DBV/SOT-23-5), and TI publishes an
  explicit dissipation-vs-ambient table rather than leaving it to a
  theta-JA calc: **500 mW @ TA<25C, 275 mW @ 70C, 200 mW @ 85C**.
  Interpolating to a 40 C ambient (this board's assumed max): ~425 mW
  allowable. The 510 mW worst case **exceeds TI's own published allowable
  dissipation at 40 C ambient** - the most concretely-documented thermal
  shortfall of the four (not an estimate, TI's own curve). At the
  realistic 150 mA / 0.26 W load it sits comfortably under every point on
  the curve.
- Lowest stock (6,853) and highest unit price of the Extended options.

## Risks / notes for the architect (not decided here)

1. **Thermal vs. the literal "300 mA+ / 0.51 W" requirement is the real
   discriminator, not current rating** - all four parts nominally support
   >=300 mA, but only AMS1117's SOT-223 tab keeps junction temperature
   comfortable at that dissipation on a 2-layer board with no heatsink; the
   three SOT-23-5-class low-Iq parts are either thin-margin (AP2112K) or
   documented as already over their own rated/allowable dissipation at
   40 C ambient (RT9013, TLV70233) for the FULL worst case. All three are
   fine at the realistic ~150 mA / 0.26 W load. This is the tradeoff for
   the architect: AMS1117's thermal margin vs. the others' far better Iq
   and dropout, contingent on whether the true worst case is 300 mA
   sustained or the realistic ~150 mA is the actual design point.
2. **AMS1117 output cap must be 22 uF tantalum-class**, not a same-value
   ceramic - explicit datasheet requirement, load-bearing for P3/P4 cap
   selection and P4 stability.
3. **Basic-vs-Extended cost crossover**: AMS1117-3.3 exists as both a Basic
   ($0.20, C6186) and Extended ($0.048, C347222) SKU; at qty 5 the Basic
   part likely wins on total delivered cost once the Extended setup fee is
   included - confirm against the live JLC fee schedule at order time.
4. **RT9013-33GB-MS and the SOT-23-5L "L-TLV70233DBVR"/"(MS)" suffix SKUs
   are second-source/clone datasheets** (MSK Semi, plus assorted
   "TP-"/"L-"/"(MS)" prefixed LCSC listings across all four searches) with
   thinner or missing electrical/thermal characterization versus the
   original IDM (Richtek for RT9013, TI for TLV70233, Diodes for AP2112K).
   Whichever part the architect/part-sourcer picks, prefer the
   IDM-branded SKU (e.g. TLV70233DBVR over TLV70233DBVR(MS)) when stock
   allows, and re-verify any second-source part's numbers before relying
   on them.
5. **Rejected for failing the hard >=300 mA floor** (found during the
   sweep, not carried forward as candidates): HT7533-1 (C14289, Basic,
   SOT-89-3, only 100 mA) and XC6206P332MR-G (C5446, Basic, SOT-23-3,
   only 200 mA) - both are otherwise attractive Basic/cheap/high-stock
   parts and worth remembering if a lower-current secondary rail is ever
   needed on this board, but they do not meet this block's current floor.
6. Datasheet URLs above are the `wmsc.lcsc.com` mirror form (the
   `www.lcsc.com/datasheet/...` form served by parts_search for some rows
   serves an HTML shell, not a PDF, per prior LEARNINGS) - all four were
   fetched and confirmed to open as real PDFs during this research pass.
