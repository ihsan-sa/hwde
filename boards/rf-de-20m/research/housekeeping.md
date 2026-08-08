# research: housekeeping (5 V rail + connectors + bulk input caps) - rf-de-20m

Date 2026-08-07. Block owner: research-component-scout. Four sub-blocks, one file per the
assignment. All stock/price from live `parts_search.py` (JLCPCB anonymous endpoint), 2026-08-07.
Build qty = 5 boards (requirements.md sec 6, answer 1). Datasheet URLs are pre-rewritten to the
`wmsc.lcsc.com` mirror (the `www.lcsc.com/datasheet/...` form serves an HTML viewer, not a PDF).

---

## 0. Headline

| Sub-block | Pick | LCSC | Price @ build qty | Note |
|---|---|---|---|---|
| 5 V buck | **LM5017MRX/NOPB** | C34355 | $1.353 (5 needed, qty-1 tier) | 100 V-class, sync, COT (no comp network) |
| SMA x2 | **BWSMA-KE-P001** | C496550 | $0.299 @ qty10 | genuine **SMD** edge-launch, both I1+I2 |
| Screw terminal | **KF128-5.08-2P-AA** | C474952 | $0.190 (5 needed) | 24 A/250 V, already proven on pd-trigger |
| Bulk (40 V rail) | **MA63V100M10X10** (polymer) | C54321630 | $0.328 @ qty10 | SMD can, low ESR |
| HF decoupling | **CC0603JRNPO0BN102** | C113793 | $0.026 (20 needed) | 1 nF C0G/NP0, 100 V, 0603 |

**Cross-cutting finding that changes the brief's assumption:** section 10's "single-sided top
assembly, bottom copper stays clear and flat as a heatsink face" (owner answer 6) is in tension
with the *default* JLC SMA connector, which is a through-hole bulkhead jack (4 ground legs + a
center pin, all soldered on whichever face they poke through). **A genuine SMD/reflow SMA edge
connector exists and is well stocked** (BWSMA-KE-P001 and two second sources, sec 2) - use it, not
the more commonly-searched through-hole "positive pin" SMA jacks, to keep the bottom face solder-free
for the heatsink. Same logic argues for SMD-package bulk caps over leaded electrolytics (sec 4). The
screw terminal (sec 3) is the one part in this block that is unavoidably through-hole - a >=10 A
clamp connector does not come in SMD - but it sits away from the FET/heatsink area so this is a
placement constraint for P5, not a rule violation.

---

## 1. 5 V buck regulator (40 V bus -> 5 V, ~0.3 A load)

Must-haves derived from the assignment: Vin >=50 V abs max (40 V-max parts rejected outright, per
the task's explicit instruction), NOT an LDO (LDO would burn 3.5 W per requirements.md sec 3), load
~0.1-0.3 A, small/cheap/few external parts.

| # | MPN | LCSC | Vin | Iout | Pkg | B/E | Stock | Price@5 | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **LM5017MRX/NOPB** | C34355 | 7.5-100 V | 600 mA | SOIC-8-EP | Ext | 435 | $1.353 | **Top pick.** 100 V-class (2.5x margin over 40 V nominal - the deepest margin of any candidate). **Synchronous** (no catch diode) and **constant-on-time control** ("requires no loop compensation" per TI's own description) - fewer external parts than a peak-current-mode part with an RC comp network. Built-in LDO self-bias. Current (600 mA) is a 2x-headroom match to the ~0.3 A load, not 10x overkill. Stock 435 covers a 5-board build ~87x over; not a real risk at this quantity. |
| 2 | TPS54360BDDAR | C524806 | 4.5-60 V | 3.5 A | SOIC-8-EP | Ext | 27 727 | $0.8147 | Cheaper, far deeper stock, genuine TI (this board already has one Tokmas-branded authenticity flag on the LMG1020 - a second genuine-TI part here is a plus). 60 V op / **65 V abs max = 1.6x margin at 40 V** - meets the ">=50 V abs max" bar but with less headroom than #1. **Asynchronous** (needs an external catch diode) and peak-current-mode (**needs an external RC compensation network** - the datasheet attribute literally flags "External compensation"). 3.5 A rating is ~11x the actual load - works fine, just not "few external parts." Good fallback if LM5017's thinner stock or SOIC-8-EP pad-to-plane thermal via count becomes a P4/P5 issue. |
| 3 | TPS54560DDAR | C31966 | 4.5-60 V | 5 A | SOIC-8-EP | Ext | 51 975 | $1.1332 | Same family as #2, 5 A instead of 3.5 A - strictly more overkill for a 0.3 A load, no reason to prefer over #2. Listed for completeness only. |
| x | TPS54360BDDAR (Tokmas) | C55019284 | - | - | ESOP-8 | Ext | 2 188 | $0.607 | Cheaper clone, but **no datasheet/attributes returned** - same brand (Tokmas) already flagged for authenticity risk on this board's LMG1020YFFR. Do not select without independent datasheet verification. |
| x | MSMP2451DJ-LF-Z | C49375219 | 4.5-60 V | 600 mA | SOT-23-6 | Ext | 506 | $0.377@10 | Smallest package, current well-matched - but brand "MSKSEMI" is obscure, no datasheet link, and stock (506) is the thinnest of any candidate. Worth a second look only if board area is desperately tight; not recommended given #1 exists with a real TI datasheet. |

**Inductor for the LM5017 (or #2/#3):** exact L depends on the switching frequency chosen at P4
(LM5017 runs ~1 MHz; TPS543x0 up to 2.5 MHz), but a small shielded power inductor in the 15-47 uH
range at >=0.5-1 A is standard for this class of low-current high-voltage buck and is cheaply
JLC-stocked - verified example: **SWPA4030S220MT** (Sunlord, C83472), 22 uH, 1 A rated / 1.3 A
saturation, 292 mOhm DCR, SMD 4x4 mm, stock 97 164, **$0.061 @ qty1**. This is a placeholder value
for the research stage, not a final selection - P4 sizes L against the actual chosen Fsw and ripple
target.

**Second source for LM5017:** none found with an identical pinout on JLC (this is TI's own part,
not widely cloned like the TPS543x0 family) - flag as **single-source, low risk at qty 5** (435
units in stock is 87x the build need).

---

## 2. SMA connectors x2 (I1 drive input, I2 200 W RF output), genuine 50 ohm

Must-haves: 50 ohm impedance (explicit LCSC attribute, not inferred from the "SMA" name alone -
cheap clones exist that don't declare 50R), JLC-placeable without breaking the 100%-PCBA / single-
sided-assembly rules.

**Key finding:** every SMA part that shows up on a bare "SMA connector" search is a through-hole
**"Plugin"** bulkhead jack (4 ground legs + center pin, "Positive Pin" = straight or "Bent tip" =
right-angle). These ARE JLC-placeable (through-hole assembly is a standard JLC PCBA service, not an
exception), but their pins/legs solder through to whichever face they protrude on - a real
mechanical conflict with "bottom copper stays clear and flat as a heatsink face" if any of that
lands on the bottom. Searching specifically for the `Offset Pin` / `SMD` style surfaced a genuine
reflow-solderable edge-launch family that avoids this entirely:

| # | MPN | LCSC | Pkg | Impedance | Freq | B/E | Stock | Price@10 | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **BWSMA-KE-P001** | C496550 | **SMD** | 50 ohm | - | Ext | 65 417 | $0.2991 | **Top pick for both I1 and I2.** Genuine SMD package (`package: "SMD"` in the LCSC record, not "Plugin"), 50 ohm explicit, "Offset Pin" style = center pin offset to land on a top-layer microstrip at the board edge - exactly the edge-launch geometry the controlled-impedance-trace requirement (I2) wants. No pins through the board, so it places in the same top-side reflow pass as everything else and leaves the bottom fully clear. Deepest stock of any SMA part found (65k). |
| 2 | A-SMA-KE-13.5A | C22467594 | SMD | 50 ohm | 6 GHz | Ext | 1 200 | $0.6935 | Second source, different brand (MyAntenna). Explicit **335 V rated voltage** attribute - useful cross-check: at 50 ohm / 200 W, Vrms = sqrt(200x50) = 100 Vrms, so 335 V rating is >3x margin. Costs ~2.3x #1. |
| 3 | SMA-KE-347-H13.5-1.2 | C5723199 | SMD | 50 ohm | 3 GHz | Ext | 3 479 | $0.3815 | Third source (XUNPU). 3 GHz spec is irrelevant here (fundamental is 20 MHz, harmonics to ~100 MHz per the EMC note) but confirms the part is a real RF connector, not a generic pin header mislabeled SMA. |
| x | BWSMA-JE / KH-SMA-KE-Z / SMA-KWE (THT bulkhead family) | C5250062 / C504007 / C7498154 | Plugin (THT) | 50 ohm (some) | 6 GHz | Ext | 6-28k | $0.25-0.73 | **Do not use** given the bottom-heatsink constraint. Kept as a documented fallback only if the SMD family's stock evaporates before order - electrically identical at 20-100 MHz, just mechanically wrong for this board's single-sided assembly answer. |

**Electrical note:** at 20 MHz (and harmonics to ~100 MHz per requirements.md sec 8.3), SMA
connector transition parasitics are negligible regardless of THT vs SMD mount - wavelength is
meters. The SMD-vs-THT choice here is driven entirely by the assembly/heatsink mechanical
constraint, not RF performance.

**Power handling:** requirements.md sec 10 (owner answer 10) already confirms "100 Vrms / 2 Arms
at 20 MHz is within SMA HF limits" - not re-derived here, just carried forward. None of the LCSC
records give an explicit wattage rating (connectors are rated in V/A/GHz, not W), so the 335 V
rating on candidate #2 is the closest direct cross-check and it clears the 100 Vrms figure with
margin.

**Same part for both I1 and I2?** Recommended - one BOM line, one footprint, halves the
qualification burden. Nothing about I1 (low-level 20 MHz PWM drive) or I2 (200 W RF out) needs a
different physical connector; the electrical difference is entirely on the board side (drive vs
output matching network).

---

## 3. 2-position screw terminal, 40 V bus, >=10 A

Must-have: >=10 A continuous rating against a 5.8 A DC average / 6 A spec load - the assignment
default from requirements.md sec 10 (owner answer 5).

| # | MPN | LCSC | Pitch | Rating | B/E | Stock | Price@5 | Rationale |
|---|---|---|---|---|---|---|---|---|
| 1 | **KF128-5.08-2P-AA** | C474952 | 5.08 mm | **24 A / 250 V** | Ext | 62 369 | $0.1903 | **Top pick.** 2.4x the >=10 A requirement, 6x the 40 V bus voltage. **Already used and verified on this repo's pd-trigger board** (research/power.md: "Catalog check: KF128-5.08-2P-AA (C474952) is rated 24 A / 250 V") - reusing a part with in-repo precedent lowers qualification risk. Through-hole, standard JLC catalog screw terminal - THT assembly here is routine, not an exception. |
| 2 | KF128-7.5-2P | C474954 | 7.5 mm | 24 A / 450 V | Ext | 3 729 | $0.1546@50 | Same family, wider pitch (more board area, easier hand-wiring clearance) and a higher voltage rating that is unnecessary headroom for a 40 V bus. Fallback if #1's 5.08 mm pitch turns out too tight for the wire gauge chosen. |
| 3 | KF128-5.0-2P | C474950 | 5.0 mm | 24 A / 250 V | Ext | 6 311 | $0.1473@50 | Near-identical to #1 at a slightly different pitch (5.0 vs 5.08 mm) - not a meaningful difference, #1's deeper stock wins. |

**JLC-placeability caveat (per the assignment):** through-hole screw terminals are a completely
standard JLC PCBA catalog item - not hand-solder-only, not off-catalog, not a 100%-PCBA rule risk.
The only caveat worth carrying forward is mechanical: its pins protrude through to the bottom face,
so P5 layout should keep it clear of wherever the bottom-side heatsink footprint lands (it's a
board-edge part by nature, so this is normally not a conflict, just worth stating explicitly since
this board's bottom face is a controlled zone).

---

## 4. Bulk + decoupling capacitors, 40 V input rail

Must-haves per the assignment: bulk (electrolytic or polymer, >=63 V) for the 5.8 A DC feed, plus
small-case C0G/NP0 HF decoupling near the FET - **not** the frozen output-network tank caps
(C_shunt/C_s/C_m, 250-500 V, owned by the power-stage refdesign block already in this workspace)
this is the DC rail feed itself, upstream of the RF choke.

### 4.1 Bulk (holds up the 5.8 A DC feed - does nothing for RF)

| # | MPN | LCSC | Type/Pkg | Rating | ESR/Ripple | B/E | Stock | Price@10 | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **MA63V100M10X10** | C54321630 | Polymer, **SMD** can D10.3xL10.5mm | 63 V, 100 uF | 30 mOhm @100kHz, 3.1 A ripple | Ext | 13 807 | $0.3282 | **Top pick.** SMD polymer - no leads through the board (same single-sided-assembly logic as sec 2). Low ESR and a high 3.1 A ripple rating give real margin against the switching-frequency ripple current the choke doesn't fully filter. |
| 2 | RVT63V100M10X10 | C51953411 | Al-elec, **SMD** can D10xL10.5mm | 63 V, 100 uF | 200 mA ripple @120Hz (not switching-freq rated) | Ext | 23 372 | $0.1069@500(qty10->tier1 $0.1806) | Cheaper, also SMD, but ordinary Al-elec ripple specs are only given at 120 Hz - no basis to compare against a 20 MHz-adjacent switching ripple duty. Use if BOM cost pressure appears; polymer #1 is the safer default given "minimise spend by reducing scope, never quality." |
| x | ERA63V100M8X12 / ERF1JM101F12OT | C49256821 / C106531 | Al-elec, **Plugin (THT)** D8xL12mm | 63 V, 100 uF | 215 mA ripple @120Hz | Ext | 73k / 43k | $0.05-0.07 | Cheapest option by far, but through-hole leads solder on the bottom face - same heatsink-clearance conflict as the THT SMA jacks in sec 2. **Not recommended** unless P5 places bulk caps well clear of the heatsink zone and the architect explicitly accepts bottom-side solder there. |

Multiple smaller bulk caps in parallel (2-4x) is the usual practice to split ripple current and
reduce single-point ESR - final count/value is a P4 power-budget call, not fixed here.

### 4.2 HF decoupling (right at the FET / choke feed point - C0G/NP0 only, per the assignment)

| # | MPN | LCSC | Value | Voltage | Pkg | B/E | Stock | Price@20 | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **CC0603JRNPO0BN102** | C113793 | 1 nF | 100 V | 0603 | Ext | 147 212 | $0.0227 | **Top pick.** C0G/NP0 (matches the assignment's explicit "not X7R" logic that already governs the tank caps), 100 V = 2.5x margin over the 40 V rail, 0603 is small and cheap, YAGEO genuine brand, deepest stock of any decoupling candidate found. |
| 2 | CC1210JKNPO0BN103 | C2310521 | 10 nF | 100 V | 1210 | Ext | 96 | $0.1751@150(qty20->tier1 $0.2147) | Larger value for a slightly lower corner frequency, but 1210 is a bigger case (works against "small-case" from the assignment) and stock is thin (96 units). Only worth it if the P4 decoupling-network sim calls for more capacitance than several 1 nF units in parallel provide. |
| 3 | 0603N102J101CT | C388030 | 1 nF | 100 V | 0603 | Ext | 1 540 | $0.009@500(qty20->tier1 $0.0112) | Walsin second source for #1, same value/voltage/package, even cheaper - good backup if YAGEO stock ever runs thin (it won't at qty 20, but flagging per the "second source" rule). |

Per the same tank-cap practice noted in requirements.md sec 3 ("parallel several C0G caps... to
split ripple current"), several 1 nF units in parallel at the DC feed point is the recommended
pattern rather than one larger part - also keeps everything on the cheap, deep-stock 0603 C0G line.

---

## 5. Risks and open items

1. **SMA mount style is a real finding, not a formality.** The obvious/commonly-searched SMA parts
   on JLC are through-hole bulkhead jacks. Using them would put solder joints on whichever face the
   legs protrude through - a genuine conflict with the owner-locked "bottom copper stays clear and
   flat as a heatsink face" answer (requirements.md sec 10, answer 6). The SMD "Offset Pin" family
   in sec 2 avoids this. **P4/P5 should use BWSMA-KE-P001 (C496550), not a THT SMA part**, unless a
   reviewer overrides this for a reason not visible at research stage.
2. **LM5017 is single-source at 435 units** (no pin-compatible clone found on JLC, unlike the
   TPS543x0 family which has Tokmas/JSMSEMI clones). Not a real risk at a 5-board build (87x
   cover), but flag for any volume follow-on - TPS54360BDDAR (#2, sec 1) is the fallback with the
   deepest stock (27.7k) if a respin is ever needed.
3. **Tokmas-branded clones appear again in this block** (TPS54360BDDAR-Tokmas, C55019284) - same
   brand already flagged for the LMG1020YFFR in requirements.md sec 3 ("LCSC brands it 'Tokmas',
   not TI - flag for an authenticity check on receipt"). Not selected here, but worth a standing
   note: this board's BOM will likely need an authenticity check pass regardless of which
   candidates P3 finalizes, since Tokmas parts keep surfacing as the cheapest option across
   multiple sub-blocks.
4. **Bulk cap ripple-current sizing not closed here.** I picked polymer over plain Al-elec on ESR/
   ripple-spec grounds, but the actual ripple current the bulk cap sees (a function of the RF
   choke's filtering and the FET's pulsed drain draw) is a P4 power-budget calculation, not
   something `parts_search` attributes can answer. Treat sec 4.1's pick as directionally right, not
   as a verified-sufficient value.
5. **Inductor for the buck is a placeholder value (22 uH example), not a final part** - correct
   value depends on the switching frequency P4 chooses for the buck regulator.
6. **"10K"-style value-token search trap** (documented in this repo's LEARNINGS.md) cost some
   round-trips during this research - queries like "buck converter 60V" or generic voltage/value
   tokens return zero rows that look like a stock-out but aren't. Worked around by searching
   specific MPNs and voltage-in-context phrases instead; no candidate here was excluded because of
   it, but P3 should keep the same workaround in mind when re-verifying these picks.

---

## Files

- `boards/rf-de-20m/research/housekeeping.md` (this file)
- `boards/rf-de-20m/research/housekeeping.json` (17 candidates across 5 sub-blocks)
- `boards/rf-de-20m/research/raw/housekeeping-buck-sweep.json` (LM5017MRX)
- `boards/rf-de-20m/research/raw/housekeeping-buck2-sweep.json` (TPS54360BDDAR family)
- `boards/rf-de-20m/research/raw/housekeeping-sma-sweep.json` (BWSMA family, SMD+THT)
- `boards/rf-de-20m/research/raw/housekeeping-screwterm-sweep.json` (KF128-2P family)
- `boards/rf-de-20m/research/raw/housekeeping-inductor-sweep.json` (22 uH power inductors)
- `boards/rf-de-20m/research/raw/housekeeping-bulkcap-sweep.json` (SMD Al-elec/polymer 63V 100uF)
- `boards/rf-de-20m/research/raw/housekeeping-decouple-sweep.json` (1nF C0G 100V 0603)
