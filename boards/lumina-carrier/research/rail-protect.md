# rail-protect - candidate parts (LUM-CAR-A)

Block: 48 V daughter-rail gate/protection + 12 V -> 3.3 V stage + 48 V input protection +
small support parts. Scout output only - P3 picks the final parts.

- Every part below was verified live through `parts_search.py` (JLCPCB API) on **2026-07-28**.
  Stock/price are that day's figures. Full result objects with price breaks are in
  `rail-protect.json`.
- Electrical claims marked "(ds)" are read out of the manufacturer datasheet, not from memory:
  TPS1663 SLVSET9G rev Apr-2026, TPS2660 SLVSDG2G, LM5069 SNVS452G.
- Derating standard applied on the 48 V domain: worst case is **57 V steady state**
  (requirements section 8). Anything under 60 V rated is not listed.
- `PROVISIONAL:` = the human has not confirmed the number (Q6 defaults: 48 V raw 2 A continuous /
  3 A capability, 12 V 2 A, 3.3 V 0.5 A).

---

## 1. 48 V daughter-rail gate / protection (CAR-REQ-14, CAR-REQ-08) - the load-bearing one

### 1.1 Approach comparison

| Approach | Current limit | Fail-safe OFF w/o MCU | V margin over 57 V | Parts | Verdict |
|---|---|---|---|---|---|
| **(a) 60 V integrated eFuse** (TPS1663 / TPS2660) | yes, adjustable, fast-trip + thermal regulation | yes, **only with an added pulldown** - see the trap in 1.3 | thin: 60 V op / 67 V abs (ds) | 1 IC + ~6 passives | best protection per part; margin is the risk |
| **(b) 80-100 V hot-swap ctrl + ext N-FET** (LM5069) | yes, 55 mV shunt + SOA power limiting (ds) | yes, but needs the enable inverted or the VIN-UVLO function given up | wide: 80 V op / 100 V abs (ds) | IC + FET + shunt + timer cap + divider | best margin; most parts; FET SOA must be proven |
| **(c) fuse or PPTC + plain FET** | **no** | yes, natively (gate-source resistor) | FET 100 V; **fuse only 63 V** | FET + fuse + 2 R + 1 transistor | cheapest, and the weakest answer to CAR-REQ-14 - see 1.4 |

**Recommendation:** (a) **TPS16630PWPR** as the primary, (b) **LM5069 + AOD66923** as the fallback.
The ranking flips to (b) if the 48 V gate ends up sitting **directly on the rectified PoE input**
rather than downstream of the PD controller's own hot-swap FET and bulk capacitance - see the
TVS-clamp risk in section 5. That is a topology question owned by the PoE sibling agent, so treat
(b) as live, not discarded.

### 1.2 Ranked parts

| # | MPN | LCSC | Package | Basic? | Stock | $ @1 / @30 / @100 | Rating | Fail-safe OFF? | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **TPS16630PWPR** | C1849461 | HTSSOP-20 (PowerPAD) | Extended | 2 057 | 2.55 / 1.86 / 1.60 | 4.5-60 V, **67 V abs max** (75 V/10 ms), 31 mohm typ / 53 mohm max @125C, ILIM **0.6-6 A** +-7% (ds) | **YES with a 10k pulldown on SHDN** (mandatory, see 1.3) | Only stocked 60 V eFuse that can actually pass 3 A. Integrated FET, adjustable ILIM, adjustable UVLO **and** adjustable OVP cutoff, dV/dT inrush ramp, latch-or-retry MODE pin, PGOOD, open-drain FLT, and an **IMON analog current monitor** that feeds the average-energy governor of section 3.2 straight into an ESP32 ADC. |
| 2 | **LM5069MM-2/NOPB** + FET | C111822 | VSSOP-10 | Extended | 1 751 | 6.34 / 5.43 / 5.01 | 9-80 V op, **100 V abs max** on VIN/GATE/SENSE/OUT/UVLO, 55 mV sense threshold, PWR pin sets max FET dissipation (ds) | **YES**, but the enable must be inverted or the VIN-derived UVLO given up (1.3) | The margin answer. Real SOA-aware power limiting (the PWR pin bounds FET dissipation during a short - the one feature no eFuse has). -2 = auto-retry, -1 = latch off. Costs a FET + shunt + timer cap and ~5x the eFuse price. |
| 3 | **LM5069MMX-2 (TOKMAS)** | C52940995 | MSOP-10 | Extended | 1 919 | 0.92 / 0.79 / 0.73 | 9-90 V, external FET, 55 mV sense (per LCSC listing; **clone - datasheet not cross-checked**) | as #2 | Makes #2 affordable and gives the LM5069 socket a genuine second source. Do **not** ship a clone on a 48 V protection function without a datasheet read + bench check. |
| 4 | **TPS26600PWPR** | C544399 | HTSSOP-16-EP | Extended | 5 075 | 1.63 / 1.18 / 1.00 | 4.2-60 V, **62 V abs max**, 150 mohm, ILIM **0.1-2.23 A** only (ds) | same family/pin trap as #1 - **verify** | Best stock and price of the eFuses, plus integrated reverse-polarity protection to -60 V. **Fails the 3 A capability requirement** (ILIM tops out at 2.23 A) and dissipates 0.6 W at 2 A. Demote unless Q6 comes back <= 1.5 A. |
| 5 | LTC4368IMS-2#TRPBF | C688403 | MSOP-10 | Extended | 24 | 6.57 / 5.22 / 4.79 | 2.5-60 V, external FET | not evaluated | 24 pcs in stock and $6.57 each. Rejected on stock depth. |
| 6 | MAX17608ATC+T | C2155884 | TDFN-12-EP | Extended | 30 | 5.12 / 4.03 / 3.62 | 4.5-60 V, **1 A** integrated FET | not evaluated | 1 A part, 30 pcs. Rejected on current and stock. |

Support parts for the (b)/(c) paths:

| Role | MPN | LCSC | Package | Stock | $ @1 / @100 | Note |
|---|---|---|---|---|---|---|
| Pass FET for LM5069 | **AOD66923** | C485687 | TO-252 | 24 985 | 0.507 / 0.408 | 100 V, 58 A, **11 mohm@10V** -> 0.04 W at 2 A. Modern trench part: low Rds, but trench FETs have weak single-pulse SOA - the LM5069 PWR pin is what makes it safe, and the SOA curve must be checked against the fault-timer value. |
| Pass FET, SOA-friendlier | IRLR3410TRPBF | C3017 | TO-252 | 27 808 | 0.505 / 0.331 | 100 V, 17 A, 155 mohm@4V -> 0.62 W at 2 A. Older planar geometry, better linear-mode SOA. The classic hot-swap tradeoff: pick on the SOA plot, not on Rds. |
| P-FET for approach (c) | NCE01P18K | C115990 | TO-252 | 16 465 | 0.718 / 0.416 | 100 V, 18 A, 120 mohm@10V -> 0.48 W at 2 A. Needs a Zener gate clamp (Vgs is only ~+-20 V against a 48 V rail). |
| Sense shunt | HoYLR2512-3W-20mR-1% | C5375467 | 2512 | 89 546 | 0.056 / 0.046 | 20 mohm 3 W. LM5069 trips at 55 mV -> 2.75 A. 5 mohm-ish for a 6 A trip; 20 mohm dissipates 0.08 W at 2 A. |
| Series fuse | 0466002.NRHF | C3105 | 1206 | 78 493 | 0.065 / 0.053 | 2 A, **63 V only** - 6 V of margin at 57 V. See 1.4. |
| PPTC (rejected) | mSMD050-60V | C70113 | 1812 | 149 170 | 0.087 / 0.072 | Best 60 V-rated PPTC in stock holds **0.5 A**. There is no 2 A / 60 V PPTC in a sane SMD size. PPTC is not an option on this rail. |

### 1.3 ENABLE fail-safe (CAR-REQ-08) - schematic sign-off gate

Requirement: **de-asserted by default, asserted by firmware only after successful boot**; must hold
OFF with the MCU in reset, mid-update, or browned out (i.e. GPIO high-Z).

- **TPS16630 - PASS, but there is a trap.** `SHDN` is active-low shutdown, and the datasheet
  electrical table gives `V(SHDN)` **open-circuit voltage = 2.48 / 2.7 / 3.3 V** with a 10 uA
  source (ds). Rising threshold is <= 2.0 V. So **an unconnected SHDN floats HIGH and the device
  powers up ON**. A 10 k pulldown to GND holds it at ~0.1 V (10 uA x 10 k), well under the 0.8 V
  falling threshold, and a 3.3 V GPIO drives it high (SHDN rec. max 5 V, abs max 5.5 V). The
  pulldown is not optional - it *is* the fail-safe, and it must be called out on the schematic.
- **TPS26600 - same family architecture (SHDN pin), pin behaviour NOT verified here.** Read
  SLVSDG2G before relying on it.
- **LM5069 - PASS with a caveat.** `UVLO` is a 2.5 V active-high input with only 1 uA of bias
  current and no internal pull-up, and the datasheet says it "can also be used for remote shutdown
  control" (ds). Driven straight from a GPIO with a pulldown it defaults OFF - but that consumes
  the pin, so the VIN-derived undervoltage lockout is lost unless an inverting transistor is added
  (default-OFF wants MCU-low = FET-off, while an N-FET pulling UVLO down gives MCU-low = FET-on).
  One extra transistor, or accept that the PD controller already owns UVLO.
- **Discrete P-FET (approach c) - PASS natively.** Gate returned to source through a resistor; a
  small NPN/N-FET pulls the gate down only when ENABLE is asserted. Nothing to get wrong.
- Recommended wiring for #1: one MCU GPIO -> SHDN (with the 10 k pulldown) **and** the connector
  ENABLE pin, so the 48 V rail and the daughter's global enable cannot disagree. `FLT` (open drain)
  -> MCU input + fault LED; `PGOOD` -> MCU input; `IMON` -> ADC. Set `MODE` open = **latch off**, so
  a shorted daughter stays off until firmware deliberately cycles SHDN.

### 1.4 Why "fuse + FET" is not the primary answer

A plain fuse gives no current limit, so under a bolted short the FET must survive the full 57 V at
whatever current the PD front end can source until the fuse's I2t is met - that is a pure SOA bet,
and the fuse is the slowest element in the system. On top of that, the only 2 A SMD fuses in stock
in a small package are **63 V** rated (6 V of margin at 57 V); moving to 125 V costs $0.75-1.90 and
stock drops below ~1 400 pcs (0154003.DRT, 0157003.DR). PPTC is worse: the best 60 V PPTC in stock
holds 0.5 A. Keep a fuse as a **backstop in series with** (a) or (b) if the architect wants a
non-semiconductor last line, not as the protection itself.

---

## 2. 12 V -> 3.3 V regulator

### 2.1 The arithmetic that settles buck vs LDO

`PROVISIONAL:` 3.3 V load = ESP32-S3 Wi-Fi TX peak (~0.35-0.5 A) + W5500 (~0.15 A) + daughter
logic/sense (Q6 default 0.5 A) -> **budget 1.2 A peak, ~0.7 A typical**.

| Option | Dissipation in the regulator | Against the budget |
|---|---|---|
| LDO from 12 V @ 1.2 A | (12 - 3.3) x 1.2 = **10.4 W** | The entire 802.3af *regulated* budget is ~10 W (section 3.2). The LDO alone would eat it. |
| LDO from 12 V @ 0.7 A | (12 - 3.3) x 0.7 = **6.1 W** | 4x the whole **1.5 W carrier overhead allocation**. |
| Sync buck @ ~88 %, 1.2 A | 3.3 x 1.2 = 3.96 W out -> **~0.54 W** loss | fits inside the 1.5 W allocation alongside the 48->12 stage. |
| Non-sync buck @ ~82 %, 1.2 A | **~0.87 W** loss (catch diode conducts ~72 % of the period at D = 3.3/12) | eats most of the allocation on its own. |

**An LDO on this rail is disqualified, not merely inefficient.** A SOT-223 AMS1117 cannot shed
6-10 W under any thermal scheme, and the 0-40 degC sealed-enclosure default (Q13) makes it worse.
Synchronous buck, and specifically synchronous rather than non-synchronous, is the answer.

Note also that D-02 fixes the chain as 48 -> 12 -> 3.3, so a second >= 60 V converter direct to
3.3 V is out of scope here.

### 2.2 Ranked parts

| # | MPN | LCSC | Package | Basic? | Stock | $ @1 / @100 | Vin | Iout | Rationale |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **TPS563201DDCR** | C116592 | SOT-23-THIN-6 | Extended | 105 187 | 0.074 / 0.060 | 4.5-17 V | 3 A sync | Synchronous, 580 kHz, EN pin, 7 cents, and 105 k in stock - the deepest-stocked credible part in the whole block. 12 V sits at 71 % of the 17 V ceiling, which is the one thing to check against 12 V-rail transients. |
| 2 | **TPS5430DDAR** | C9864 | SOIC-8-EP | **Basic** | 151 433 | 0.98 / 0.66 | 5.5-36 V | 3 A | The only **JLC Basic** buck that suits this rail, and 36 V of input headroom kills the transient worry. But it is **non-synchronous** - it needs an external Schottky and costs ~0.3 W more (table above) out of a 1.5 W budget, plus 13x the IC price. Basic status is worth ~$3 of one-off Extended-part setup at 14 boards; the 0.3 W is worth more. |
| 3 | **SY8113BADC** | C78989 | TSOT-23-6 | Extended | 22 979 | 0.246 / ~0.198 @50 | 4.5-18 V | 3 A sync | Straight second source for #1 with 1 V more input headroom. Different pinout - not a drop-in. |
| 4 | MP2315GJ-Z | C45889 | TSOT-23-8 | Extended | 474 | 2.26 / 1.84 | 4.5-24 V | 3 A sync | Most input headroom of the synchronous options, but 474 pcs and $2.26. Rejected on stock/price. |
| - | AMS1117-3.3 | C6186 | SOT-223 | Basic | 1 554 395 | 0.20 / 0.13 | <= 15 V | 1 A | **Disqualified** - listed only so the LDO question stays closed (2.1). |

---

## 3. 48 V input protection (bridges + TVS)

Parts only - the PD topology is the sibling agent's deliverable.

| Role | MPN | LCSC | Package | Basic? | Stock | $ @1 / @100 | Rating | Note |
|---|---|---|---|---|---|---|---|---|
| Input bridge, Mode A + Mode B (**x2**) | **MB10S-50MIL** | C2488 | MBS (SOP-4) | **Basic** | 757 204 | 0.027 / 0.021 | 1000 V, **1 A**, VF 1.1 V @ 400 mA | JLC Basic, 757 k in stock, 2.7 cents. Default choice for the af build. |
| Bridge with at headroom (**x2**) | **ABS210** | C123897 | ABS | Extended | 382 688 | 0.047 / 0.038 | 1000 V, **2 A**, VF 1.0 V @ 2 A | 2 A means the 802.3at upgrade stays a resistor change (D-01) instead of a bridge swap. 2 cents more. **Recommended.** |
| Bridge, alt | ABS10 | C65028 | ABS | Extended | 198 026 | 0.030 / 0.024 | 1000 V, 1 A | Same footprint as ABS210 - lets the 1 A / 2 A choice be a BOM-only decision. |
| Bridge, classic PoE BOM part | HD01-T | C52151 | MBS | Extended | 10 745 | 0.276 / 0.212 | 100 V, 0.8 A | 10x the price of MB10S for less current. Only reason to pick it is drop-in parity with a reference design. |
| TVS on the rectified rail | **SMBJ58A** | C2891331 | SMB (DO-214AA) | Extended | 12 903 | 0.044 / 0.035 | 58 V standoff, 64.4 V Vbr min, **93.6 V Vclamp**, 600 W | Recommended: 58 V standoff clears 57 V worst case, and 600 W gives real surge headroom on a cable-fed port. |
| TVS, smaller | SMAJ58A | C123816 | SMA | Extended | 15 468 | 0.045 / 0.037 | same, 400 W | Same price, smaller body, less energy. Only if board area is tight. |
| TVS, biggest | SMCJ58A | C4154627 | SMC | Extended | 2 999 | 0.108 / ~0.089 @50 | same, 1500 W | If the PoE run leaves the building or the surge spec hardens. |
| TVS ahead of the bridge | SMAJ58CA | C2943847 | SMA | Extended | 18 684 | 0.033 / 0.027 | **bidirectional**, 58 V, 400 W | Polarity is unknown before rectification, so anything placed across the pairs must be bidirectional. |
| Ideal-diode bridge (rejected) | LT4321IUF#TRPBF | C580183 | QFN-16-EP | Extended | **126** | 6.96 / 4.78 | 20-80 V, 2 bridges, ext FETs | Would recover the ~0.7-1.5 W the diode bridges burn, but $7 + 8 external FETs + 126 pcs in stock. Not for 14 boards. |

**Bridge loss is a real line item in the 1.5 W carrier overhead.** Two diodes conduct at all times:
at 802.3af worst case (12.95 W at the 37 V minimum -> ~0.35 A) that is 2 x ~1.0 V x 0.35 A =
**~0.7 W**, i.e. roughly half the entire carrier overhead allocation before the converters have done
anything. At 802.3at (~0.69 A) it is **~1.5 W** and the allocation is gone. Section 3.2 already flags
the 1.5 W as judgement to be measured - this is the single biggest reason it may not hold.

---

## 4. Support parts (short, per brief)

| Role | MPN | LCSC | Package | Basic? | Stock | $ @1 | Note |
|---|---|---|---|---|---|---|---|
| Daughter ID EEPROM | **M24C02-RMN6TP** | C83836 | SOIC-8 | Extended | 53 223 | 0.133 | 2 Kbit I2C, **1.8-5.5 V** (so 3.3 V is comfortably inside), 400 kHz, ST. |
| EEPROM, cheaper | BL24C02F-PARC | C176653 | SOP-8 | Extended | 39 939 | 0.074 | 1.7-5.5 V, 1 MHz, half the price. Fine for an ID/calibration store. |
| Fault LED | **KT-0603R** | C2286 | 0603 | **Basic** | 7 593 490 | 0.0074 | Red, Basic, 0.7 cents. |
| Power-good / link LED | **KT-0805G** | C2297 | 0805 | **Basic** | 2 975 409 | 0.016 | Green, Basic. The only Basic green is 0805 - mixing 0603 red with 0805 green is the cheapest route. |
| Green, 0603 uniformity | KT-0603G | C12624 | 0603 | Extended | 427 844 | 0.012 | If the layout wants one LED size everywhere, this costs Extended status. |
| I2C pull-ups | 0603WAF4701T5E | C23162 | 0603 | **Basic** | 4 249 416 | 0.012 | 4.7 k. Two of them, carrier-side (section 2.1 puts the pull-ups on the carrier). |
| SHDN pulldown / general | 0603WAF1002T5E | C25804 | 0603 | **Basic** | 4 257 809 | 0.008 | 10 k. This is the part that implements the CAR-REQ-08 fail-safe (1.3). |

Scoping notes:

- **The ID EEPROM lives on the daughter, not the carrier** (section 4.3 / Q10: "route I2C to a
  daughter EEPROM"). The carrier's BOM contribution is the two pull-ups plus the ADC-side divider
  input. The EEPROM is listed here so the ICD can name a reference part for daughter designers.
- **Protect the ID/ADC pin.** Q10's default keeps *both* a resistor divider on an ADC pin and the
  I2C EEPROM. A mis-seated daughter can bridge 48 V onto a neighbouring connector pin, so the ID
  and ADC lines want a series resistor plus a clamp to 3.3 V - that is part of the CAR-REQ-14
  survivability story, not just ESD hygiene.
- **0603 resistors are 75 V working voltage** (100 mW parts above). Anything sitting across the
  48 V rail - bleed resistors, UVLO/OVP dividers, ID dividers referenced to 48 V - should be 1206
  (200 V) or two 0603s in series, which also helps CAR-REQ-17 creepage.

---

## 5. Risks

1. **60 V eFuse vs the TVS clamp voltage - the biggest open risk.** SMBJ58A clamps at up to
   **93.6 V**, and the TPS16630's absolute maximum is **67 V** (75 V for 10 ms) (ds). If the 48 V
   gate sits directly on the rectified input, a surge that puts the TVS into clamping exceeds the
   eFuse's abs max. If it sits downstream of the PD controller's hot-swap FET and bulk capacitance
   (normal for a PD), the bulk rail absorbs the event and 60 V is defensible. **Placement decides
   whether candidate #1 or #2 is correct.** Route to the PoE topology agent.
2. **Inrush ownership must be assigned to exactly one side.** CAR-REQ-14 puts inrush limiting on
   the daughter, but the carrier switch is in series with it. 2800 uF to 48 V is
   0.5 x 2800u x 48^2 = **3.2 J**. If the daughter limits the current, the carrier eFuse should have
   a *fast* dV/dT and a current limit above the daughter's inrush level; if the eFuse also ramps,
   two soft-starts fight, the eFuse rides thermal regulation (145 degC set point, ds) and may trip
   its own fault timer on every plug-in. TI advertises "charges large and unknown capacitive loads
   through thermal regulation" (ds) - that is a designed behaviour, not a free one, and it must be
   checked against the SOA/inrush calculation for the chosen dV/dT cap.
3. **Single source.** TPS16630 is TI-only with no pin-compatible alternate; the TPS26600 is a
   different pinout *and* cannot pass 3 A, so it is a redesign, not a drop-in. The LM5069 socket is
   the only one in this block with a genuine second source (TI + the TOKMAS clone), which is an
   argument for (b) beyond voltage margin.
4. **Stock depth.** TPS16630PWPR is 2 057 pcs - ample for 14 boards, thin for a reorder if a batch
   is consumed. TPS26600PWPR (5 075) and the LM5069 pair (1 751 + 1 919) are the deeper sockets.
5. **Carrier overhead budget (1.5 W) looks optimistic.** Diode bridges ~0.7 W at af, 3.3 V buck
   ~0.5 W, eFuse ~0.2 W at 2 A, plus the 48->12 stage and magnetics. Section 3.2 already says this
   must be measured - the bridge number above is the first hard input to that measurement.
6. **Nothing here is JLC Basic except the bridge, the LEDs and the passives.** The eFuse, the
   3.3 V buck and the EEPROM are all Extended. The section 7 assumption "prefer Basic/Standard
   library parts" is not achievable on this board at any sane performance point; at 14 units the
   extra Extended-part setup cost is a few dollars total and should not drive part choice.
7. **Clone risk.** LM5069MMX-2 (TOKMAS) and the various AT24C02 clones are cheap and deeply
   stocked, but a clone on a 48 V protection function needs its own datasheet review.

## 6. Method / provenance

`parts_search.py` live JLCPCB search (the anonymous EasyEDA-backed endpoint), 2026-07-28, no
offline fallback used - every row above came back from a live query and is reproducible with
`--query <MPN>`. Web search was used only to pull the three TI datasheets (TPS1663 SLVSET9G,
TPS2660 SLVSDG2G, LM5069 SNVS452G), whose absolute-maximum, ILIM and enable-pin numbers are quoted
above; every candidate was then re-verified through `parts_search` for stock and price.
