# Regulator research - buck-5v3a (synchronous buck IC)

Block: 5V/3A continuous synchronous step-down regulator IC. Input 7-18V steady
state (bench/adapter, non-automotive per A1). No airflow, 50C ambient,
<=50x40mm board, no heatsink -> package thermal (theta-JA) is a first-class
ranking criterion, not an afterthought.

All candidates verified live via `parts_search.py` (source=live, today's
LCSC/JLC stock+price). Raw sweeps: `research/raw/regulator-sweep.json`.

## Method / must-haves derived from requirements.md section 10

- Synchronous rectification, integrated FET (both switches on-die) - REQUIRED,
  not "controller + external FET." No compelling reason found to shortlist a
  controller topology (integrated-FET Extended parts fully cover 3-5A/32V at
  reasonable cost - no need for the extra BOM/layout of external FETs).
- VIN abs-max >=25V (ideally 30-40V) for hot-plug/inductive-cable ringing
  margin above the 18V steady-state ceiling (A1: bench/adapter, no load-dump).
- Vout 5.0V, 3A continuous; want a part rated >=3.5A so 3A isn't the ragged
  edge (A2: 3A is the hard ceiling, no peak allowance - size current limit
  for ~4-5A, not for an external burst).
- Package theta-JA ranked explicitly; exposed-pad packages preferred.
- JLC Basic preferred, Extended acceptable for this IC (A11 exception).
- Hiccup current limit + thermal shutdown required (A5).
- Note bootstrap cap / compensation (internal vs external) / soft-start
  method per candidate, and switching frequency (drives inductor size).

## Ranked candidates

| Rank | MPN | LCSC | Pkg | theta-JA | VIN op / abs-max | Iout | fsw | Basic | Stock | Price@qty5* |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AP63357QZV-7 | C3194572 | VDFN-13 (2x3mm) | **25 C/W** (datasheet) | 3.8-32V / 35V DC, 40V/400ms | 3.5A | 450kHz | No (Ext) | 3246 | $1.08 |
| 2 | AP63356QZV-7 | C3194571 | VDFN-13 (2x3mm) | 25 C/W (same die/pkg) | 3.8-32V / 35V DC, 40V/400ms | 3.5A | 450kHz | No (Ext) | 2546 | $1.01 |
| 3 | MP2315GJ-Z | C45889 | TSOT-23-8 | **100 C/W** (datasheet) | 4.5-24V / 28V | 3A | 500kHz | No (Ext) | 225 | $2.26 |
| 4 | RT8293AHZSP | C116810 | SOP-8-EP | 75 C/W ->64 w/ Cu (datasheet) | 4.5-23V / n/a | 3A | 340kHz | No (Ext) | 6116 | $0.33 |
| 5 | MP2338GTL-Z | C7210174 | SOT-583 | unverified | 4.5-28V / 28V | 3A | 450kHz | No (Ext) | 2914 | $2.12 |

\*"Price@qty5" = the price-break tier that applies at our qty-5 prototype run
(the qty=1 tier in every row above; qty10+ breaks are cheaper still per JSON).

## #1/#2 - Diodes AP63357/AP63356 (recommended)

Datasheet DS41949 Rev.3 pulled and read in full (bootstrap: R5=20 EQV cap
0.1uF? no - **AP6335x needs only a single 100nF cap BST-SW**, no boot
resistor). Facts, all datasheet-confirmed (not inferred):

- 74mOhm HS / 40mOhm LS integrated FETs, peak current mode control.
- **theta-JA = 25 C/W, theta-JC = 5 C/W** (JEDEC, 4-layer FR-4, 2oz Cu, min
  recommended pad) - best in this shortlist by 3-4x. Datasheet layout guide
  explicitly calls out 2oz Cu both layers + GND/VIN via stitching under the
  pads for max thermal performance - directly actionable at P2/P6.
- Abs-max VIN -0.3 to +35V DC continuous, **+40V for 400ms transient** - this
  is exactly the hot-plug/inductive-ringing margin the requirement asks for,
  with 17V of steady-state headroom above our 18V ceiling.
- HS peak current limit typ 5.0A (4.0-6.0A), LS valley limit typ 4.2A
  (3.2-5.2A) - matches A2's "~4-5A" current-limit target directly; hiccup
  mode trips after 512 cycles at limit, 8192-cycle cooldown, auto-restarts.
  Thermal shutdown TSD=170C typ, 25C hysteresis. Both A5 protections
  datasheet-confirmed present.
- **Internal fixed soft-start, ~4ms typ - no external SS cap needed** (fewer
  parts than every other candidate below, all of which need an external SS
  cap or resistor).
- Compensation: COMP pin is dual-mode - **ground it for internal loop comp**
  (simplest, fewest parts) or add an external RC network (R+2 optional caps)
  to tune the loop; architect's call, not forced into either.
- Output is **adjustable only** (0.8-31V via FB divider) per this datasheet's
  ordering table - needs R1/R2 divider (typical circuit: 157k/30k1 for 5V).
  **Discrepancy flag**: the JLC/LCSC catalog attribute for the sibling SKU
  AP63356DV-7 (C2157973) tags it "Output Type: Fixed," but the official
  Diodes DS41949 Rev.3 ordering-information table lists no fixed-voltage
  order code for either part. Treat the catalog "Fixed" tag as unverified/
  likely mis-tagged; design for adjustable + divider unless P3 finds a
  newer datasheet revision that adds a fixed-Vout SKU.
- Typical 5V/3A app circuit (from datasheet Fig. 1/44): L=6.8uH, Cin=10uF,
  Cout=2-3x22uF, Cboot=100nF, R1=157k/R2=30k1 (FB divider), external comp
  R5=42.2k/C5=1.2nF/C6=15pF(opt)/C4=10pF(opt) if using external comp.
- AP63357 adds PFM light-load mode (up to 86% eff @5mA) over AP63356's
  PWM-only; irrelevant at our always-loaded ~3A/15W point, so AP63356 is a
  legitimate, marginally-cheaper equal pick - listed as rank 2 rather than a
  true runner-up.
- Extended part (not Basic) - allowed per A11's explicit exception for the
  regulator IC. Stock (2500-3200) is far above the 5-board prototype need.

Sources: Diodes DS41949 Rev.3 datasheet (fetched and read directly, pages
1-6 and 24-29 of 29); parts_search live (2026-08-08).

## #3 - MPS MP2315GJ-Z (fallback / ecosystem diversity)

Datasheet (MonolithicPower.com, Rev 1.01) pulled directly. Confirmed:
theta-JA **100 C/W**, theta-JC 55 C/W, TSOT-23-8 (no exposed pad) - 4x worse
than AP6335x, and continuous power dissipation is rated only
Pd(max)=(150-TA)/theta_JA -> **~1.0W at 50C ambient**, a materially tighter
thermal budget than the VDFN parts above for the same board. Abs-max VIN is
28V but recommended/rated operating max is only 24V - below the requirement's
25V floor, leaving only 6V of headroom over our 18V steady-state ceiling.
Needs BST cap+series resistor (100nF+20 Ohm, one more part than AP6335x) and
an AAM-mode-select resistor (light-load efficiency pin, another extra part).
Internal soft-start (0.8-2.2ms), hiccup+OTP (150C/20C hyst) both confirmed.
500kHz fixed, sync 200kHz-2MHz external clock option, L=6.5uH typ for 5V.
Note: a fixed-5V-output sibling (MP2315SGJ-Z, C3031493) exists but shows only
2 units in stock today - not usable for even a 5-board run; watch-list only.
Good for MPS-ecosystem consistency or as a second source, not the top pick
here given the voltage-margin and thermal deltas.

## #4 - Richtek RT8293A/B (cheapest, exposed pad, but tightest voltage margin)

Datasheet (Richtek DS8293B) confirms exposed-pad SOP-8: theta-JA 75 C/W,
improvable to 64 C/W with added copper under the pad - decent, though well
behind AP6335x's 25 C/W. **VIN abs-max is only 23V** - the tightest margin of
the entire shortlist (5V over our 18V ceiling), which is exactly the failure
mode the requirement calls out (hot-plug/inductive-cable ringing). Needs an
external SS cap (0.1uF -> 13.5ms, 6uA charge) and external compensation
network (more parts than AP6335x's internal-comp option). "A" variant =
340kHz, "B" variant = 1.2MHz (smaller inductor, more switching loss). Very
cheap and very well stocked (6116 units). Ranked below MP2315 despite better
thermal and much lower price because the input-voltage margin is the
single most safety-relevant spec in this brief, and this part has the least
of it in the shortlist.

## #5 - MPS MP2338GTL-Z (smallest footprint, thermal unverified)

28V abs-max (meets the 25V floor, below the 30-40V ideal), 3A, 450kHz, sync,
adjustable soft-start (external cap) + hiccup limit confirmed via
parts_search attributes. Smallest package in the shortlist (SOT-583,
leadless ~1.6x2mm class) - attractive for the 50x40mm area budget, but no
theta-JA figure could be found in any accessible source (Diodes/MPS/Mouser/
Farnell fetches all blocked or timed out; alldatasheet/scribd mirrors did not
surface the number either). A package this small, without a confirmed large
exposed pad, is a thermal unknown at 3A/15W - flagged as unverified risk
rather than assumed safe. Ranked last: it doesn't out-perform AP6335x on any
verified axis and under-performs it on the one axis (thermal) that matters
most here.

## Excluded (non-synchronous - violates the hard constraint)

- **TI TPS54540 family** (all genuine TI SKUs, e.g. TPS54540DDAR C95286):
  JLC catalog attribute "Synchronous Rectifier: No" on every TI-branded row,
  independently confirmed via TI's own product page - it has an internal
  high-side FET but rectifies through an external/internal diode, not a
  low-side FET. Despite excellent voltage margin (42V abs-max) and low price
  at the lowest SKU, this fails the SYNCHRONOUS hard requirement outright -
  excluded, not shortlisted. (One Tokmas-remarked clone SKU, C6423791,
  claims "Yes" in the catalog; Tokmas is a remark/clone house and this
  contradicts every genuine-TI row plus TI's own datasheet, so it is not
  trusted as a synchronous option.)
- **MPS MP4560**: non-synchronous (JLC attribute "No" on all 3 SKUs found)
  AND only 2A rated - double-disqualified (fails both the sync requirement
  and the 3A current requirement).
- **Silergy SY8208**: zero rows returned from a live `parts_search` query -
  cannot verify current stock/price/attributes, so it is not listed per the
  "only parts parts_search can see, with stock today" rule. (Live source,
  not a cache fallback - the query is a real zero, not an offline gap.)

## Risks / open items for the architect (P2)

1. **AP63356DV-7 catalog "Fixed" attribute is unverified/likely wrong** - the
   authoritative Diodes datasheet ordering table shows adjustable-only for
   this family; design the feedback divider assuming adjustable output.
2. **Single-source risk on the top pick**: no pin-compatible alternate exists
   for the exact VDFN-13 AP6335x footprint at this theta-JA tier within
   today's LCSC stock; AP63356 <-> AP63357 are pin-identical die twins
   (same package, same pin-out) and count as the same footprint risk, not an
   independent second source. MP2315/RT8293/MP2338 are genuine alternates
   but each trades away either voltage margin or thermal performance.
3. MP2338's theta-JA could not be confirmed from any reachable source in
   this pass; if it becomes a serious candidate later, re-attempt the
   Monolithic Power datasheet fetch (direct fetches of diodes.com and
   several mirrors 403'd or timed out during this research pass - not a
   dead end, just blocked today).
4. All shortlisted candidates need an external LC filter, feedback divider
   (adjustable parts), and either a bootstrap cap (all) and/or SS cap/comp
   network (MP2315, RT8293, MP2338) - none of that BOM is captured in this
   file; it belongs to P2/P4 schematic capture.
