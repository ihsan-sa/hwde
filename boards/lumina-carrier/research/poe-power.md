# research: poe-power (PD controller + >= 60 V primary DC-DC) - LUM-CAR-A

Date 2026-07-28. Block owner: research-component-scout. Ranked as a **pair** because the two are
coupled: on JLC, the choice of PD controller *decides* whether you get a buck or a transformer.

All stock/price from live `parts_search.py` (JLCPCB anonymous parts endpoint), 2026-07-28.
Every electrical claim below is quoted from the part's own datasheet, fetched and grepped this
session. Values I computed rather than quoted are labelled **[calc]**.

Build qty per Q15 default = 14, so the `@30` column is the realistic tier; `@100` shown for trend.

---

## 0. Headline

**Recommend strategy (b): separate PD interface + external 100 V buck.**

| | Part | LCSC | Pkg | Stock | @1 | @30 | @100 |
|---|---|---|---|---|---|---|---|
| PD interface | **TPS2378DDAR** | C337500 | SO-8-EP | 10 899 | $1.359 | $1.083 | $0.991 |
| 48->12 V buck | **SCT2A25STER** | C5124114 | ESOP-8 | 3 160 | $2.104 | $1.614 | $1.399 |
| | **pair total** | | | | **$3.46** | **$2.70** | **$2.39** |

Second source for the PD interface: **TPS2379DDAR** C140293 (pins 1-7 identical, see 3.1).

**Two findings that change the brief's assumptions:**

1. **The brief's named part, Si3402-B, is disqualified by D-01.** It is IEEE 802.3af / Type 1
   only - it cannot present class 4 at all, so no resistor change upgrades it. Its newer sibling
   **Si3404** is the one part on JLC that is a PD interface *and* a non-isolated buck in one chip,
   but its datasheet says verbatim "The Si3404 is a Type 1 PD" and the rev-1.0 history records
   "Removed Type 2 signaling from diagram". Also disqualified. Skyworks' actual PoE+ parts
   (Si3406 / Si34061 / Si34062) are effectively **not stocked** (37 / 6 / 0 / 0 / 0 units).
   **Consequence: the AN956 "~10 W regulated" figure in requirements section 3.2 is a figure for
   a part this board cannot use.** The number should be re-derived, not inherited.

2. **Every 802.3at Type-2 PD IC on JLC that integrates a converter is transformer-based.**
   TPS23754/56, TPS23751, MP8009A and WS3204 are all isolated flyback / active-clamp-forward
   controllers - none of them has a buck mode. So if H1 confirms the PROVISIONAL **non-isolated
   buck**, strategy (a) "integrated PD + converter" is *not available at Type 2*, and the only
   way to satisfy both D-01 and the buck default is a two-chip solution.

---

## 1. Must-have check against the assignment

| Requirement | TPS2378 + SCT2A25 | Evidence |
|---|---|---|
| 25 kOhm detection signature | Yes, RDEN = 24.9 kOhm 1% from VDD to DEN | TPS2378 DS SLVSB99C 7.4.4 |
| Classification | Yes, single resistor CLS->VSS | DS Table 1 p.11 |
| **D-01 af->at by resistor only** | **Yes: 90.9 Ohm = class 3 (13 W, af build 1); 63.4 Ohm = class 4 (25.5 W, at). One 0603 change, no respin.** | DS Table 1 p.11 |
| Genuinely supports Type 2 | Yes - "all of the features needed to implement an IEEE802.3at type-2 powered device ... Type 2 Hardware Classification" | DS 7.1 Overview |
| Inrush limiting | Yes, 140 mA internal | DS 7.1 |
| Integrated hot-swap FET | Yes, 100 V / 0.5 Ohm, 0.85 A continuous | DS 7.1, 7.3.5 |
| MPS | Yes - see 4.3; met by the carrier's own always-on load + CBULK | DS 7.4.7 |
| Converter input >= 60 V **with margin** | **Yes: 5.5-100 V recommended, 110 V abs max, vs a 57 V rail = 1.9x margin** | SCT2A25 DS p.2-3 |
| 12 V out, at-case current | 2 A continuous / 4 A peak limit; datasheet has a literal 48 V -> 12 V @ 2 A design example | SCT2A25 DS Fig. 10 p.9 |
| Plain inductor (no transformer) | Yes - 68 uH inductor + 100 V Schottky | SCT2A25 DS p.9-11 |

Bonus pins that fall out for free and are worth designing in:
- **CDB** (TPS2378 pin 6, open-drain, RTN-referenced converter-disable) wires straight to the
  SCT2A25 **EN** pin (pull below 1.23 V = disable, float = enable). Correct PoE start-up
  sequencing with one net and no glue.
- **T2P** (pin 7, open-drain, active low = "a Type-2 PSE was detected") is a free hardware flag.
  Route it to an ESP32-S3 GPIO and firmware knows at run time whether at power is actually
  available - this is the software half of D-01 and costs one pin.

---

## 2. Ranked candidates - primary DC-DC (48 V -> 12 V)

| # | MPN | LCSC | Vin | Iout | Pkg | B/E | Stock | @30 | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **SCT2A25STER** | C5124114 | 5.5-100 V (110 abs) | **2 A cont / 4 A peak** | ESOP-8 | Ext | 3 160 | $1.614 | Only shortlisted part that carries the **at** case at 100 V rating. Integrated 500 mOhm HS FET, COT 300 kHz, PFM at light load, RthetaJA 42 C/W. Datasheet ships the exact 48 V->12 V/2 A design. Asynchronous - needs a 100 V Schottky (DS recommends SS510). |
| 2 | LM5164DDAR | C477928 | 6-100 V | 1 A | SO-8-EP | Ext | 7 569 | $1.648 | **Synchronous** (no catch diode, best efficiency and least heat). But 1 A x 12 V = 12 W: covers af, fails at. D-01 says size for at, so this needs a respin at upgrade - which D-01 forbids. Keep as the fallback if the architect narrows the 12 V rail. |
| 3 | MP9486AGN-Z | C404013 | 4.5-100 V (95 rec) | ~1 A (3.5 A switch limit) | SOIC-8-EP | Ext | 2 772 | $2.922 | Same 100 V class, less current, ~2x the price of #1, and its efficiency curves are only given for Vout = 5 V. No reason to prefer it. |
| 4 | LM5146RGYR | C3188679 | 5.5-100 V | set by external FETs | VQFN-20 | Ext | 1 622 | $1.666 | 100 V **synchronous controller**. The efficiency-maximum answer and the escape hatch if thermals bite: any current, ~2-3 points better than an asynchronous buck. Costs 2 FETs + gate/sense network + a much bigger layout. Over-engineered for 20 W unless CAR-REQ-18 forces it. |
| 5 | TPS54360BDDAR | C524806 | 4.5-60 V | 3.5 A | SOIC-8-EP | Ext | 31 533 | $0.549 | Cheapest and deepest stock by far. **Only 60 V rated (65 V abs max) against a 57 V rail** - ~5 % margin with a hot-swap and cable transients upstream. Meets the letter of CAR-REQ-02, not its spirit. Not recommended as primary. |
| 6 | TPS54560DDAR | C31966 | 4.5-60 V | 5 A | SOIC-8-EP | Ext | 30 760 | $0.838 | Same 60 V objection, more current. |
| x | LM5017MRX | C34355 | 7.5-100 V | **0.6 A** | SOIC-8-EP | Ext | 1 393 | $0.970 | Closed out: 0.6 A x 12 V = 7.2 W, below even the af budget. The "LM5017-class" suggestion in the assignment cannot carry this rail. |

Excluded by the brief and not proposed: LM2596 (40 V), LMR33630 (36 V), LMR16006 (0.6 A),
MP4560 (55 V), SCT2432 (40 V), LM5160 (65 V, thin margin like the TPS543x0 pair).

---

## 3. Ranked candidates - PD front end

### 3.1 PD interface only (pairs with an external buck) - RECOMMENDED PATH

| # | MPN | LCSC | Pkg | B/E | Stock | @30 | Rationale |
|---|---|---|---|---|---|---|---|
| 1 | **TPS2378DDAR** | C337500 | SO-8-EP | Ext | 10 899 | $1.083 | 802.3at Type-2, 100 V / 0.5 Ohm hot-swap FET, 0.85 A cont, 140 mA inrush, single-resistor class (90.9 / 63.4 Ohm), CDB + T2P. Deepest stock of any at-capable PD part on JLC. RthetaJA 45.9 C/W. |
| 2 | TPS2379DDAR | C140293 | SOIC-8-EP | Ext | 1 755 | $1.525 | **True second source.** Pins 1-7 identical (VDD/DEN/CLS/VSS/RTN/CDB/T2P); only pin 8 differs - TPS2378 = APD (aux-adapter detect), TPS2379 = GATE (external FET driver). This board is PoE-only (requirements 3.1: "no barrel jack, no other input"), so APD is unused, pin 8 stays free, and either part drops into the same footprint. Design rule for P4: **leave pin 8 unconnected.** |

### 3.2 Integrated PD + converter (strategy a) - all transformer-based

| # | MPN | LCSC | Pkg | Stock | @30 | Verdict |
|---|---|---|---|---|---|---|
| 3 | TPS23754PWPR | C181651 | HTSSOP-20-EP | 8 210 | $1.511 | Type 2, single-resistor class (90.9/63.4), 100 V/0.5 Ohm FET, RthetaJA 44.4 C/W, dual gate drivers + programmable dead time. **"DC-DC control optimized for isolated converters"; application section covers active-clamp forward and flyback only, with a "Switching Transformer Considerations" step. No buck mode.** Best-documented isolated option. |
| 4 | WS3204 | C2691431 | TSSOP-20-EP | 4 001 | $1.256 | NJGW/GEC clone of TPS23754 - same pin names, same class table incl. 63.4 Ohm = class 4. 85 V / 0.4 Ohm FET (vs TI's 100 V). **Datasheet is Chinese-only.** Cheapest at-capable integrated part. Also transformer-based. |
| 5 | MP8009AGV-Z | C5676296 | QFN-28 (4x5) | 990 | $2.194 | 802.3af/at PD + flyback/forward, 100 V/0.48 Ohm FET, 840 mA limit, 250 kHz with EMI dithering, RthetaJA 37-40 C/W. Its class table is *different*: 41.2 Ohm = class 3, 28.7 Ohm = class 4. Stock under 1 k. Transformer required. |
| 6 | TPS23751PWPR | C473395 | HTSSOP-16-EP | 679 | $0.602 | Cheapest TI at-capable part by a mile, flyback-optimised. Stock 679 is the problem, not the price. |
| X | SI3402-B-GMR | C510771 | QFN-20-EP (5x5) | 1 538 | $1.811 | **DISQUALIFIED - 802.3af / Type 1 only.** The brief's named part. Cannot present class 4; no resistor upgrades it. |
| X | SI3404-A-GMR | C461934 | QFN-20-EP (4x4) | 3 094 | $1.633 | **DISQUALIFIED - Type 1 only** ("The Si3404 is a Type 1 PD", DS 2.2.3). Painful, because it is the *only* stocked chip that is a PD interface + non-isolated buck in one 4x4 QFN, with an integrated hot-swap AND switching FET and 120 V abs max. If D-01 were ever reopened to af-forever, this is the part. Also capped at 600 mA continuous. |

---

## 4. Analysis the architect asked for

### 4.1 Strategy (a) vs (b) - recommendation and why

**Recommend (b).** Not on cost - on availability of the required topology.

| | (a) integrated PD + converter | (b) PD interface + external buck |
|---|---|---|
| Topology available at Type 2 | **isolated flyback/forward only** | non-isolated buck **or** isolated |
| IC cost @30 | $1.26 - $2.19 (one IC) | $2.70 (two ICs) |
| Magnetics | **transformer - see 4.4, not stocked in the right ratio** | plain 68 uH inductor |
| Extra parts | optocoupler + TL431 + secondary rectifier + bias winding | 100 V Schottky |
| Realistic BOM delta | (a) ends up **dearer** once magnetics + feedback isolation are counted | - |
| Board area | comparable IC, but transformer ~18 x 15 mm + secondary side | inductor ~7 x 7 mm + SMC diode |
| Efficiency | Skyworks integrated parts document ~75-77 % (see 4.2) | ~92 % **[calc]** |
| Part count | fewer ICs, more passives | 2 ICs, fewest total parts |
| JLC availability | good for the ICs, **bad for the transformer** | good for everything |

The single deciding fact: **JLC does not stock a 12 V-secondary PoE PD flyback transformer**, so
(a) forces an off-catalog magnetic part into a build that section 7 assumes is a single JLCPCB
PCBA order.

### 4.2 Efficiency, and why it is worth more than the BOM delta

| Path | Efficiency | Source |
|---|---|---|
| Si3402-B integrated (the brief's basis) | ~77 % implied (10 W regulated out of 12.95 W in) | AN956, quoted in requirements 3.2 |
| Si3404 integrated | 75 % typ | LCSC parametric on SI3404-A-GM |
| **TPS2378 + SCT2A25 buck** | **~92 % [calc]** | loss budget below |

**[calc]** SCT2A25 at 48 Vin -> 12 Vout, 1.7 A (= 20 W, the at case): D ~ 0.26; HS FET conduction
1.7^2 x 0.5 x 0.26 = 0.38 W; switching + quiescent ~0.2 W; SS510 Schottky 0.55 V x 1.7 A x 0.74 =
0.69 W; inductor DCR (68 uH, ~0.1 Ohm) 0.29 W. Total ~1.6 W -> 20/(20+1.6) = **93 %**. At the af
case (0.85 A) losses fall to ~0.6 W -> ~94 %. Call it 92 % with margin.

**What that buys, af build 1 [calc]:** 12.95 W at the PI, minus input bridge (2 x 0.7 V x 0.27 A =
0.38 W) minus hot-swap (0.5 Ohm x 0.27^2 = 0.04 W) = 12.5 W into the buck; x 0.92 = 11.5 W at 12 V;
minus the 1.5 W carrier overhead = **~10 W to the light engine, against the brief's 8.5 W**.
That is ~18 % more light for a $1.40 buck. Using a Schottky input bridge instead of PN adds
another ~0.2 W.

**This is a claim for the P4 power-budget table to prove, not a promise.** It also means the
af/at two-column table required by D-01 and gate 2 should be built from the *selected* converter's
numbers, not from AN956.

**Datasheet caveat, stated plainly:** SCT2A25's efficiency-vs-load family for Vout = 12 V at
24/36/48/60/72 Vin is Figure 2 on p.5 of the datasheet, but it is vector art whose data points do
not extract as text. I could not read an exact datasheet number at 1.7 A; the 92-93 % above is my
loss budget from the datasheet's own component values. **Read the curve (or measure) before the
power-budget table is signed off.**

### 4.3 MPS (Maintain Power Signature)

None of the shortlisted parts contains an "auto-MPS" current injector, and none needs one here.
A valid MPS is >= 10 mA DC (or 10 mA pulsed 75 ms in every 325 ms) **and** AC impedance below
26.3 kOhm || 0.05 uF; the AC half is satisfied by the mandatory CBULK >= 5 uF (TPS2378 DS 7.4.7).
The carrier's own always-on load is the 1.5 W overhead allocation = **~31 mA at 48 V, ~3x the
10 mA floor**, present whenever the ESP32-S3 and W5500 are running. So DC MPS holds even with the
daughter fully dark, which is exactly the low-load case the assignment worried about.

**Design rule that must not be broken:** the TPS2378 datasheet warns that forcing the hot-swap off
via APD or DEN kills DC MPS and the PSE will drop the port. So **do not** wire any "sleep" or
"power save" feature to DEN/APD. Firmware must never be able to take the board below 10 mA.

### 4.4 Isolated flyback option and its price

If H1 answers Q5 = **isolated**, the design changes as follows:

- **Controller:** TPS23754PWPR C181651, 8 210 stock, $1.511@30. Type 2, same single-resistor class
  lever (90.9 -> 63.4 Ohm), so D-01 survives the switch. TPS23756 (C2863581, 526 stock, $1.967@30)
  is the same part with a 9 V converter start-up instead of 15 V.
- **Transformer: this is the problem.** Searching JLC for PoE PD flyback transformers returns
  essentially nothing usable. The only stocked family is Pulse PA3855: **PA3855.005NLT** C17526143,
  459 in stock, $1.538@30, SMD 17.7 x 14.5 mm, 2.25 kV isolation - **but its secondary is 5 V /
  2.2 A (~11 W)**, wrong rail and wrong power. The 12 V variants (PA3855.001/.002) are at 0-20
  units. Wurth 750313638 shows 0 stock. Generic EE13 bobbin transformers exist but are through-hole
  and have arbitrary inductances.
- **Cost/size delta vs the recommended buck, per board:**

| Item | Non-isolated buck | Isolated flyback |
|---|---|---|
| PD/controller IC | TPS2378 $1.083 | TPS23754 $1.511 |
| Converter IC | SCT2A25 $1.399 | (in the controller) |
| Magnetics | 68 uH inductor, ~7 x 7 mm, ~$0.30 | transformer ~18 x 15 mm, **$1.5-6, not stocked in the right ratio** |
| Rectifier | 1x SS510 SMC | secondary diode/sync FET + snubber |
| Feedback | resistor divider | **optocoupler + TL431** (~$0.35) |
| **IC+magnetics delta** | baseline | **~ +$1.5 to +$4 and roughly 2x the converter footprint** |
| Schedule risk | none | **off-JLC part -> hand-fit or customer-supplied-part flow; breaks the section 7 single-order assumption** |

**The honest answer to "what does isolation cost":** not the ~$2 of BOM. It costs the ability to
order the board as one JLCPCB PCBA job, plus a transformer selection/qualification task that has no
in-catalog answer today. Recommend the architect push Q5 to the human with that framing.

### 4.5 Thermal (sealed unventilated enclosure, 0-40 C ambient, natural convection)

| Part | Pkg | RthetaJA | Dissipation, **at** case | Tj at 40 C ambient |
|---|---|---|---|---|
| TPS2378 | SO-8 PowerPAD | 45.9 C/W (RthetaJC-bot 6.7) | **[calc]** worst case 25.5 W / 37 V = 0.69 A; 0.69^2 x 0.5 Ohm = **0.24 W** | ~51 C |
| SCT2A25 | ESOP-8 | 42 C/W | **[calc]** ~0.6 W in-package at 1.7 A | ~65 C |
| SS510 Schottky | SMC/DO-214AB | (board dependent) | **[calc]** ~0.69 W - the single biggest heat source in the converter | needs its own copper |
| 68 uH inductor | ~7 x 7 mm | - | **[calc]** ~0.29 W | - |

Total converter-block dissipation ~**1.6 W at the at case, ~0.6 W at af**. Both ICs have big
margin to their 125-150 C junction limits, so **the carrier's own converter is not the CAR-REQ-18
problem** - the daughter's LED drivers are. Notes for the layout gate:
- The catch diode dissipates more than the buck IC. Do not let placement treat the IC as "the hot
  part" and starve the diode of copper.
- Both ICs are exposed-pad parts; both datasheets require the pad tied to a ground plane with vias.
- The 100 V-class parts run cooler than a 60 V part at the same load, which is another reason to
  reject the TPS543x0 options.
- Isolated alternative would be *worse* here: a flyback at ~87 % dumps ~2.6 W instead of ~1.6 W in
  the same sealed box.

### 4.6 Magnetics / sourcing per candidate

| Candidate | Needs | Sourcing risk |
|---|---|---|
| SCT2A25 (rec.) | plain 68 uH power inductor + 100 V Schottky | **Low** - both are commodity JLC parts |
| LM5164 | plain inductor, no diode (synchronous) | Low |
| LM5146 | plain inductor + 2 external FETs | Low, more parts |
| TPS23754 / WS3204 / MP8009A / TPS23751 | **flyback or active-clamp-forward transformer** | **High** - see 4.4 |
| Si3402-B / Si3404 | inductor (buck mode) or transformer (flyback) | Low, but both disqualified by D-01 |

### 4.7 Single-source risk

| Part | Risk | Mitigation |
|---|---|---|
| TPS2378 | **Low** | TPS2379 C140293 is pin-1-to-7 identical in the same SO-8-EP footprint; leave pin 8 free and either part builds. 1 755 units of backup on top of 10 899. |
| SCT2A25 | **Medium-high** | SCT is a single Chinese vendor; its ESOP-8 pinout (FB/NC/VIN/BST/SW/TM/EN/GND) is **not** the TPS5450 or MP9486A pinout, so there is **no pin-compatible alternate**. 3 160 units covers 14 boards ~200x over, but a re-spin would be needed if SCT exits. Accept for a 14-unit build; flag for any volume follow-on. |
| TPS23754 (isolated path) | Low-medium | WS3204 C2691431 is a functional clone with the same pin names and class table, 4 001 units - but the datasheet is Chinese-only, so treat it as a fallback to be re-verified, not a drop-in. |
| PoE transformer (isolated path) | **High** | No in-catalog 12 V-secondary part. See 4.4. |

---

## 5. Risks and open items

1. **The 8.5 W light-engine budget is anchored to a disqualified part.** Requirements 3.2 takes
   "~10 W regulated" from AN956 / Si3402-B. That part fails D-01. The two-column af/at table
   (gate 2) must be rebuilt from the selected converter; on my numbers it comes out better
   (~10 W to the light engine at af, not 8.5 W). Do not silently keep 8.5 W and do not silently
   promise 10 W - measure it.
2. **12 V @ 2 A (Q6 default) is 24 W, which exceeds the 20 W available even at 802.3at.** The
   connector rating and the sustained power budget are two different numbers. SCT2A25's 2 A
   continuous / 4 A peak is exactly right for this: it can *serve* a 2 A connector spec while the
   firmware average-energy governor (requirements 3.2) keeps the average inside the PoE budget.
   The architect should state this explicitly rather than let 2 A read as 24 W of headroom.
3. **48 V raw to the connector bypasses this converter.** The strobe cap-bank charging current
   (D-02) does not flow through the buck, so the buck does not need to be sized for it - but
   CAR-REQ-14 survivability for that path needs its own high-side switch/e-fuse, which is a
   separate block from this one.
4. **Efficiency figure not read off the curve.** See 4.2 caveat.
5. **DEN/APD must never be used for power-saving** or the PSE drops the port (4.3).
6. **SCT2A25 is asynchronous.** If the layout thermal review or a future higher-power daughter
   pushes back, the upgrade path is LM5146 (synchronous controller, same 100 V class, C3188679) -
   worth reserving mental footprint, not board space.
7. **Si3404 is the part that should have existed.** If D-01 is ever reopened, revisit it - it is
   the only single-chip PD + non-isolated buck in stock, and it would halve this block.

---

## Files

- `boards/lumina-carrier/research/poe-power.md` (this file)
- `boards/lumina-carrier/research/poe-power.json` (16 candidates, parts_search result objects with
  `lcsc` / `mpn` / `basic` / `stock` / `price` / `price_breaks` / `datasheet` intact, plus
  `role` / `rank` / `verdict` / `note`)
