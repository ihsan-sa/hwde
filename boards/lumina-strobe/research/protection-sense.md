# protection-sense - candidate parts (LUM-DTR-STROBE-A)

Scout: research-component-scout, 2026-07-28. Every part below was re-verified live through
`parts_search.py` against JLCPCB on the date above; the machine-readable copy with untouched
`lcsc`/`mpn`/`basic`/`stock`/`price`/`datasheet` keys is `protection-sense.json` (45 parts).
Prices are unit price at the **qty-1** break (what a qty-6 build pays) and at the **qty-100**
break. Nothing here is a final selection - that is P3's job.

Sources used: `parts_search.py` live JLCPCB search (all stock/price figures) plus the LCSC-hosted
datasheet PDFs for TPS2490, LM5069, TPS26600, TMP709, TMP302, LM393/LM2903, IRF5210S,
IRF9540NS and NCE01P18K (fetched and text-searched, not recalled). No offline cache and no
web-search-only candidates were used.

**Headline: JLC has exactly one part class that solves the inrush problem properly, and it is
not a MOSFET and not an NTC - it is a power-limiting hot-swap controller driving an external
FET. TPS2490DGSR (C139631) is the pick.**

---

## 0. The arithmetic everything else is measured against

| Quantity | Value |
|---|---|
| Bank | 2800 uF, >=100 V rated |
| Energy 0 -> 48 V | **3.226 J** (0 -> 57 V: 4.55 J) |
| Energy 48 -> 40 V (one full flash) | 0.986 J |
| PD operating current limit (the number to size against) | **1.0 A** |
| Steady-state recharge the limiter must pass | 0.25 A (af) / 0.50 A (at) |
| Internal air | 56 C (af) / 69 C (at) |
| Sustained power budget, whole daughter | 8.5 W (af) |

Constant-current ramp into an empty 2800 uF bank (this is the `I = C dV/dt` line the brief asked
for; the **limiter element dissipates exactly the stored energy, 3.23 J, independent of ramp
rate** - only the peak and mean power move):

| Inrush current | dV/dt | 0 -> 48 V ramp | Peak power in limiter | Mean power in limiter | Energy |
|---|---|---|---|---|---|
| 0.25 A | 89 V/s | **0.538 s** | 12.0 W | 6.0 W | 3.23 J |
| 0.50 A | 179 V/s | 0.269 s | 24.0 W | 12.0 W | 3.23 J |
| 1.00 A (PD limit) | 357 V/s | 0.134 s | 48.0 W | 24.0 W | 3.23 J |

So the limiter is a **0.13-0.54 s** event, which is the single most important fact in this
document: it lands in the **dead zone between the last plotted SOA curve (10 ms) and the DC
line** on every discrete MOSFET datasheet JLC stocks.

---

## 1. Inrush / soft-start on `+48V_SW` (STR-REQ-09)

### Verdict on the four families

**(c) hot-swap / eFuse controller with programmable current limit + power limit - CORRECT, and
JLC stocks it.** The prompt asked whether the honest answer is "JLC has very little in the >=60 V
hot-swap class". It is not: JLC stocks TPS2490 (4942), TPS2491 (73), LM5069 clone (1919), genuine
LM5069 (1751), LM5060 (763), plus the 60 V integrated-FET eFuses TPS26600 (5075) and TPS16630
(2055). What JLC has **almost nothing of** is anything above 80 V and anything in the LTC4364 /
LTC4380 surge-stopper class at sane money (8-100 units, $7-17 each).

Why the power-limiting controller wins specifically here: it does not just limit current, it
regulates `PLIM = VDS x ID` to a programmed constant. Set `PLIM = 3 W` and the FET is pinned at
3 W for the whole charge - input current starts at 3/48 = **62 mA** and rises as VDS collapses,
so the PD's 1.0 A limit is never approached, the charge completes in roughly `3.23 J / 3 W =
1.1 s`, and the fault timer (programmed longer than that) catches any case where it does not.
FET stress becomes a number you *choose*, not a number you *hope* is inside an unpublished curve.

**(b) discrete soft-start MOSFET with a gate RC ramp - workable but undocumented.** The SOA answer
the prompt asked for, verified in the PDFs:

| Part | SOA curves actually plotted | 100 ms SOA | 1 s SOA | RthJC | RthJA (PCB, steady state) | DC capability at 56 C air |
|---|---|---|---|---|---|---|
| IRF5210S (C2622, D2PAK) | 100 us, 1 ms, 10 ms @ Tc=25 C, Tj=150 C | **not published** | **not published** | 0.75 C/W max | 40 C/W | (150-56)/40 = **2.35 W** |
| IRF9540NS (C33903, D2PAK) | 100 us, 1 ms, 10 ms @ Tc=25 C, Tj=150 C | **not published** | **not published** | 1.1 C/W | 40 C/W | **2.35 W** |
| NCE01P18K (C115990, DPAK) | **no SOA figure at all** | none | none | 1.79 C/W | not given | not derivable |

Both Infineon parts do publish a *single-pulse transient thermal impedance* (`Zthjc`) curve out to
1 s (IRF5210S) / 10 s (IRF9540NS), with the note `Peak Tj = Pdm x Zthjc + Tc` - so 100 ms and 1 s
capability has to be **derived**, and the derivation only covers bulk heating, not the linear-mode
hot-spotting that the SOA plot exists to bound. Two consequences:

- A 0.25 A ramp (12 W peak, 6.0 W mean, 0.538 s) is **~2.6x the 2.35 W steady-state PCB-mount
  capability** but far under the 10 ms SOA line. It almost certainly survives on transient thermal
  grounds. It is not *certified* to, by anyone, on any datasheet JLC sells.
- **Repeat rate is the real trap.** Mean FET power = 3.23 J x (ENABLE cycles/s). At **0.72 Hz of
  ENABLE cycling the mean hits the 2.35 W PCB steady-state limit** and the FET cooks. Since
  ENABLE is a normal firmware-driven control on this system, a discrete limiter needs an
  architect-imposed re-arm interval; the controller-based one gets its fault timer for free.

Rank inside family (b): **IRF5210S** (biggest die: -100 V, 60 mohm, -38 A, 170 W @Tc=25) >
**IRF9540NS** (-100 V, 117 mohm, -23 A, 110 W) > **NCE01P18K** (cheapest, no SOA data - do not
put an undocumented part in the one place on this board that eats 3.23 J).

**(a) NTC inrush thermistor - REJECT, with numbers.** The failure is not marginal, it is
structural, and it is caused by this system's own architecture:

| | NTC 5D-9 (C332361) | NTC47D-15 (C12398) |
|---|---|---|
| R25 | 5 ohm | 47 ohm |
| Cold inrush at 48 V | **9.6 A** (9.6x the PD limit) | **1.02 A** (already at the limit) |
| Cold inrush at 57 V | 11.4 A | 1.21 A (**over** the limit) |
| Body temp / R / burn, 0.25 A @56 C air | - | **86 C / 8.7 ohm / 0.54 W** |
| Body temp / R / burn, 0.50 A @69 C air | - | **124 C / 4.0 ohm / 0.99 W** |
| **Hot re-strike current** (ENABLE re-asserted before it cools) | - | **5.5 A (af) / 12.1 A (at)** |

(Self-heating solved from `I^2 R(T) = D (T - Tamb)` with B = 2950 K and D = 18 mW/C, the
dissipation constant JLC lists for the same 15 mm disc family.)

Three independent kills: (1) even the *largest sane* value is at or over the PD limit cold;
(2) it burns **0.54-0.99 W, i.e. 6-12% of the 8.5 W budget**, permanently, for nothing;
(3) the hot re-strike is 5.5-12 A - and on this board a hot re-strike is not an abuse case, it is
what happens every time firmware toggles ENABLE, because 802.3 compliance forces the carrier's
48 V switch to be firmware-controlled (ICD s8.3). Secondary: it is a THT 7.5 mm-pitch plugin part
(same hand-solder question as the connectors) and an 86-124 C hot spot in a sealed box whose
aluminium electrolytics halve their life every 10 C.

**(d) resistor bypassed by a relay/FET - NOT CREDIBLE at JLC.** `relay SPST 12V 1A SMD` returns
**zero** stocked results. The only stocked switch-like alternatives are photoMOS SSRs
(KAQY214, 400 V/130 mA, 977 in stock, $0.87) which cannot carry even the 0.5 A steady-state
recharge. A FET bypass is just family (b) with an extra resistor and an extra sequencing bug.

### Candidate table - inrush

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | The rating that makes it fit |
|---|---|---|---|---|---|---|---|---|
| **1** | **C139631** | **TPS2490DGSR** | MSOP-10 | ext | 4942 | 2.800 | 1.893 | **9-80 V; independent programmable current limit AND constant-power limit + fault timer = explicit SOA protection. EN pin is GND-referenced, takes 3V3 ENABLE directly. Latch-off on fault.** |
| 2 | C52940995 | LM5069MMX-2 (TOKMAS) | MSOP-10 | ext | 1919 | 0.920 | 0.731 | 9-90 V, 55 mV current-limit sense, PWR-pin power limit, UVLO/EN, internal charge pump for a high-side N-ch. 1/7 the price of TI silicon. |
| 3 | C111822 | LM5069MM-2/NOPB | VSSOP-10 | ext | 1751 | 6.337 | 5.014 | Genuine TI LM5069-2, same function. Use if the Tokmas clone is unacceptable; $6.34 is 25% of the whole $25 board target. |
| 4 | C544399 | TPS26600PWPR | HTSSOP-16-EP | ext | 5075 | 1.630 | 1.002 | 4.2-**60 V** op / **62 V abs max**, 150 mohm integrated FET, programmable ILIM + dV/dt, 157 C TSD, open-drain FLT. One part instead of three. |
| 5 | C1849461 | TPS16630PWPR | HTSSOP-20 | ext | 2055 | 2.545 | 1.596 | 4.5-60 V, 30.4 mohm integrated FET, 0.6-6 A programmable limit. |
| 6 | C74456 | LM5060MM/NOPB | VSSOP-10 | ext | 763 | 1.766 | 1.114 | 5.5-65 V high-side driver with charge pump and dV/dt inrush control - **but no power-limit engine**, so inrush energy is bounded only by the unpublished FET SOA. |
| P1 | C2622 | IRF5210STRLPBF | D2PAK | ext | 38830 | 1.033 | 0.660 | Pass FET, P-ch: -100 V, 60 mohm, -38 A, 170 W @Tc=25, 3.1 W @Ta=25, RthJC 0.75 C/W. Largest die -> best linear-mode margin. |
| P2 | C33903 | IRF9540NSTRLPBF | D2PAK | ext | 10479 | 1.015 | 0.668 | Pass FET, P-ch: -100 V, 117 mohm, -23 A, 110 W @Tc=25, 3.1 W @Ta=25, RthJC 1.1 C/W. |
| P3 | C115990 | NCE01P18K | TO-252 | ext | 16465 | 0.718 | 0.416 | Pass FET, P-ch: -100 V, 120 mohm, -18 A, 70 W @Tc=25, RthJC 1.79 C/W. **No SOA curve published.** |
| N1 | C23982 | IRF540NSTRLPBF | D2PAK | ext | 20833 | 0.752 | 0.500 | Pass FET, N-ch for the controller's charge-pump gate drive: 100 V, 44 mohm, 33 A, 130 W @Tc=25, Tj 175 C. |
| N2 | C537985 | IRFR540ZTRPBF | DPAK | ext | 1018 | 1.281 | 0.854 | Pass FET, N-ch: 100 V, 28.5 mohm, 35 A, 91 W @Tc=25. Smaller die, only 1018 in stock. |
| S | C459687 | RLP25FEGR050 | 2512 | ext | 263424 | 0.065 | 0.052 | Sense shunt 50 mohm 3 W 1% = 50 mV/A; puts a 0.5 A limit on TPS2490's 50 mV threshold and 25 mV power-limit threshold. |
| a1 | C12398 | NTC47D-15 | Plugin P=7.5 | ext | 23577 | 0.324 | 0.255 | 47 ohm/3 A/15 mm - the *least bad* NTC. Numbers above. Listed as evidence, not as a recommendation. |
| a2 | C332361 | 5D-9 | Plugin P=7.5 | ext | 184929 | 0.043 | 0.036 | 5 ohm - 9.6 A cold inrush. Listed only to document why the common 5D-9 class is wrong here. |

**Recommendation: TPS2490DGSR + IRF540NS (N-ch high side) + 50 mohm shunt, ~$3.62 at qty 6.**
Fallback if that busts the budget: LM5069MMX-2 clone, same topology, ~$1.74.

---

## 2. Bleed path (STR-REQ-10 / CAR-REQ-17, mandatory)

### RC arithmetic - passive backstop (always present, cannot be defeated)

Standing burn is charged against the 8.5 W budget only while `+48V_SW` is live.
"Combined" is with the carrier's own 100 kohm bleed in parallel (no series diode, ICD).

| R | Standing burn @48 V | tau | 48 -> 10 V, this board alone | 48 -> 10 V, combined with carrier 100 k |
|---|---|---|---|---|
| 47 k | 49 mW (0.58% of 8.5 W) | 132 s | 206 s (3.4 min) | 141 s (2.4 min) |
| **100 k** | **23 mW (0.27%)** | **280 s** | **439 s (7.3 min)** | **220 s (3.7 min)** |
| 200 k | 12 mW (0.14%) | 560 s | 878 s (15 min) | 293 s (4.9 min) |

100 k is the sweet spot: 0.27% of budget, and the combined time constant with the carrier means a
board pulled off the stack is under 10 V in under 4 minutes with no active help at all.

### RC arithmetic - active fast bleed (enabled when ENABLE is de-asserted)

When ENABLE is low the carrier's 48 V switch is already open, so **this power comes out of the
bank, not out of the 8.5 W budget** - the active bleed costs zero budget, which is why the split
passive/active scheme is right.

| R | Peak power (t=0) | tau | 48 -> 10 V | Total energy | Mean power over the event |
|---|---|---|---|---|---|
| 220 | 10.5 W | 0.62 s | 1.0 s | 3.23 J | 3.2 W |
| 470 | 4.9 W | 1.32 s | 2.1 s | 3.23 J | 1.6 W |
| **1 k** | **2.30 W** | **2.8 s** | **4.4 s** | **3.23 J** | **0.73 W** |
| 2.2 k | 1.05 W | 6.2 s | 9.7 s | 3.23 J | 0.33 W |

### On "single-pulse energy rating", which is what the prompt asked for

**No thick-film chip resistor JLC stocks publishes a joule rating.** The parameter simply does not
exist for this part class; what you get is continuous power, working voltage, and (in the vendor
datasheet, not in JLC's parametrics) a short-time overload allowance - typically 2.5x rated power
for 5 s for 2512 thick film, i.e. ~12.5 J for a 1 W part. Dedicated pulse-withstanding series
(Vishay PWR/CRCW-P, KOA SG73P) that *do* publish J ratings returned **zero** stocked hits.

The clean way out, and the reason 1 kohm is ranked first: **size the bleed so peak power is below
the resistor's continuous rating**, and the pulse question disappears. At 1 kohm the peak is
2.30 W; a 2512 2 W part is 1.15x under at t=0 and falling, and a 1 W part is at 2.3x - inside the
usual overload allowance but with no margin and no published number to lean on.

### Candidate table - bleed

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | The rating that makes it fit |
|---|---|---|---|---|---|---|---|---|
| **P1** | **C149504** | **0805W8F1003T5E** | 0805 | **BASIC** | 6.34 M | 0.0103 | 0.0103 | Passive backstop 100 k 1%: 125 mW rating vs 23 mW actual, **150 V working voltage** = 2.6x on the 57 V worst case. Single 0805 satisfies the 0805-or-split rule outright. |
| P2 | C17900 | 1206W4F1003T5E | 1206 | **BASIC** | 2.02 M | 0.0233 | 0.0233 | Same value, 250 mW, **200 V working** = 3.5x. Take this if a reviewer wants more than 2.6x on a safety-mandated part. |
| P3 | C17539 | 0805W8F2003T5E | 0805 | **BASIC** | 989 k | 0.0130 | 0.0130 | 200 k, 150 V working. Halves the burn to 12 mW but 15 min unaided discharge. |
| **A1** | **C2793988** | **PS122WJ0102T4E** | 2512 | ext | 5743 | 0.0925 | 0.0740 | Active bleed 1 k, **2 W, 500 V working**. 2.30 W peak / 0.73 W mean / 3.23 J - peak is under the continuous rating, so no pulse rating is needed. Best voltage margin (8.8x). |
| A2 | C52175204 | FRP2512F1001TS | 2512 | ext | 24166 | 0.0672 | 0.0578 | 1 k 1%, 2 W, 200 V working. Same energy case, 3.5x voltage margin. |
| A3 | C54315 | 25121WF1001T4E | 2512 | ext | 105388 | 0.0559 | 0.0559 | 1 k 1%, **1 W**, 200 V. 2.30 W peak = 2.3x continuous; relies on the unpublished overload allowance. Rank 3 for that reason. |
| **Q1** | **C94389** | **MMBTA42LT1G** | SOT-23 | ext | 241161 | 0.0462 | 0.0365 | Active bleed switch: NPN, **Vceo 300 V** (5.3x), Ic 500 mA, saturates at 48 mA dissipating ~25 mW itself. Base-driven from inverted ENABLE - no gate-threshold problem. |
| Q2 | C81507 | CJT04N15 | SOT-223 | ext | 16476 | 0.1913 | 0.1503 | N-ch, 150 V (2.6x), 4 A, 160 mohm @Vgs=10 V. **Vgs(th) up to 2.5 V makes 3.3 V gate drive marginal** - needs a logic-level part or a gate boost. |
| Q3 | C534596 | BSS126H6327 | SOT-23 | ext | 5531 | 0.1935 | 0.1567 | 600 V but only **21 mA Id and 700 ohm Rds(on) @Vgs=10 V**. Cannot carry the 48 mA a 1 k bleed needs. Listed as evidence that "just use a high-voltage SOT-23 FET" fails. |

**Recommendation: 100 k 0805 (C149504) permanently across the bank, plus 1 k 2 W 2512
(C2793988) in series with an MMBTA42 (C94389) driven from inverted ENABLE. ~$0.15 at qty 6.**

---

## 3. Fail-safe ENABLE gating (STR-REQ-21)

### The supply-rail question, answered first because it changes the ranking

ICD s3.3 says there is **no mate sequencing** - 48 V can arrive before or after 3.3 V. So:

- **+3V3 present, +48V_SW absent:** any logic gate works. Nothing to energise anyway.
- **+48V_SW present, +3V3 absent:** the gate has **no Vcc**. Its output is not defined - it sits
  near 0 V only through parasitic input-protection paths. **The fail-safe therefore cannot rest on
  a logic gate.** The safety element must be passive: the ICD-mandated 100 k pull-down on ENABLE
  *plus* a pull-down directly on every gate/base node in the power path, so the bank-charge FET
  and the LED drive FET are held off by resistors regardless of what is powered.
- **Best structural answer:** gate the bank-charge path at the hot-swap controller's own `EN` /
  `UVLO` pin. Verified on the TPS2490 datasheet: **EN is GND-referenced, threshold 1.350 V rising /
  1.250 V falling, absolute maximum 100 V** - so ENABLE (3.3 V push-pull) drives it directly
  through a series resistor with a pull-down to GND, **and it works with no +3V3 rail at all.**
  The controller also holds GATE low until VCC clears its own POR (~6 V) and UVLO (~8 V), which
  matches ICD s8.3's "`+48V_SW` is dead at power-up" case for free.
  That removes the logic gate from the safety argument entirely and leaves it doing only the job
  it is good at: killing the ~60 us power-up PWM glitch on the drive stage.

**Never latch ENABLE locally** is satisfied by all of these. One caveat worth an architect
decision: a *latching* hot-swap controller (TPS2490, LM5069-**2**) latches on an **overcurrent
fault**, not on ENABLE, and clears on an EN cycle. That is a fault latch, not an ENABLE latch, but
a strict reading of STR-REQ-21 may want the auto-retry variants - and those are thinly stocked
(TPS2491DGS 73 units, LM5069MM-1 960 units at $9.53).

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | The rating that makes it fit |
|---|---|---|---|---|---|---|---|---|
| **1** | **C434068** | **SN74LVC1G08DBVR (UMW)** | SOT-23-5 | ext | 91922 | 0.0412 | 0.0318 | 2-input AND, 1.65-5.5 V, 32 mA, **-40..+105 C** (covers 69 C internal air). PWM AND ENABLE in one part. Push-pull - must never touch FAULT. |
| 2 | C7832 | SN74LVC1G08DCKR | SC-70-5 | ext | 89987 | 0.0598 | 0.0465 | Same function, genuine TI, **-40..+125 C**, 90 k stock. Take this if the 105 C grade is felt to be tight. |
| 3 | C529281 | SN74LVC1G11DCKR | SC-70-6 | ext | 6823 | 0.1298 | 0.1040 | **3-input** AND: PWM AND ENABLE AND /OVERTEMP in one gate, -40..+125 C. Saves a part if the thermal trip is gated in logic rather than at the FET. |
| 4 | C46388 | TS5A3159DCKR | SC-70-6 | ext | 37122 | 0.2920 | 0.2370 | SPST analogue switch, 1.65-5.5 V, 1 ohm on, break-before-make. Only if the gated signal must stay analogue. |
| R | C25803 | 0603WAF1003T5E | 0603 | **BASIC** | 7.68 M | 0.0079 | 0.0079 | The ICD-mandated 100 k ENABLE pull-down. 75 V working is irrelevant here - this net never exceeds 3.3 V. |

Discrete transistor gating (a second MMBTA42 / small N-FET pulling the drive gate to GND) is
ranked *above* all of these for the **power path**, because it needs no supply rail at all.
The logic gate's job is the signal path only.

---

## 4. Firmware-independent over-temperature + FAULT (STR-REQ-20)

### The architectural fork

Open question 4's default is **LED off-board on its own heatsink**. If that stands, every
integrated temperature-switch IC is out: they sense their **own die**, which is board air, not the
LED. The only architecture that survives is **remote NTC -> comparator on this board**.

Worse for the integrated route: TMP302's fixed thresholds sit in the **50-65 C** band, which is
**inside** this board's own 56-69 C internal-air range (ICD s7.6). A board-mounted TMP302 will
nuisance-trip on 802.3at ambient alone. TMP709 is resistor-programmable so it can be set clear of
that (e.g. 100 C), but it still measures board air.

FAULT compliance: LM393/LM2903 and LMV331 have **open-collector** outputs and TMP709/TMP302 have
**open-drain** outputs - none of them can drive FAULT high, which is the ICD's hard rule. The
carrier owns the 10 k pull-up; **this board fits none**. LM393/LM2903 being dual is a bonus: one
section can pull FAULT low *and* pull the drive-gate node low simultaneously, leaving the second
section free for bank-undervoltage or a second thermal channel.

**Temperature-grade trap:** the only **JLC BASIC** comparator, LM393DR2G (C7955), is graded
**0 to +70 C** - the datasheet's own grade table confirms it (LM393 0..+70, LM2903 -40..+105,
LM2903V -40..+125). 70 C is **1 C above** the 69 C 802.3at internal air, before any self-heating.
Do not take the Basic part for this. LM2903DR2G is the same die, same pinout, Extended, and
**$0.0635 vs $0.0654 - the industrial grade is actually cheaper.**

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | The rating that makes it fit |
|---|---|---|---|---|---|---|---|---|
| **C1** | **C57474** | **LM2903DR2G** | SOIC-8 | ext | 289513 | 0.0635 | 0.0507 | **Dual comparator, open collector, 2-36 V, -40..+105 C.** Ratiometric trip from a 3V3 divider = supply-independent threshold. One part covers FAULT assert + drive shutdown. |
| C2 | C7955 | LM393DR2G | SOIC-8 | **BASIC** | 385020 | 0.0654 | 0.0530 | The only JLC **Basic** comparator - but **0..+70 C**, below the 69 C at-ambient. Flagged, not recommended. |
| C3 | C34731 | LMV331IDBVR | SOT-23-5 | ext | 43420 | 0.1627 | 0.1283 | Single, open collector, 2.7-5.5 V, **-40..+125 C**, 7 mV offset. Half the area when only one trip is needed. |
| **T1** | **C22396387** | **TMP709AIDBVR (UMW)** | SOT-23-5 | ext | 9148 | 0.3270 | 0.2547 | **Open-drain active-low OT**, trip set 0-125 C by one 1% resistor, 2/10 C selectable hysteresis, 33 uA, -40..+125 C. Best integrated option - **but senses its own die.** |
| T2 | C2877557 | TMP302ADRLR | SOT-563 | ext | 40114 | 0.2035 | 0.1579 | Open-drain active-low, factory-fixed threshold in the **50-65 C** band = inside this board's own ambient range. Will nuisance-trip. Evidence, not a candidate. |
| **I1** | **C28927** | **TMP112AIDRLR** | SOT-563 | ext | 14063 | 0.3301 | 0.2618 | I2C telemetry: 13-bit, 1.4-3.6 V, -40..+125 C, 4 addresses, +-0.5 C. **Fit no pull-ups - the carrier's 4.7 k own the bus.** |
| I2 | C99269 | TMP102AIDRLR | SOT-563 | ext | 5649 | 0.5616 | 0.3599 | 12-bit, same footprint/protocol, +-0.5 C. Pin-compatible fallback. |
| I3 | C2837470 | LM75BDP (UMW) | MSOP-8 | ext | 23230 | 0.3974 | 0.3038 | 11-bit, 2.8-5.5 V, -55..+125 C, 8 addresses, and has its **own OS/ALERT open-drain output** that could drive FAULT directly - a second, independent firmware-free trip for free. |
| **N1** | **C13564** | **NCP18XH103F03RB** | 0603 | ext | 396408 | 0.0410 | 0.0338 | Board-mount NTC: 10 k +-1% @25 C, B25/85 = 3380 K, -40..+125 C, 100 mW. With a 10 k top leg the ADC1 source impedance peaks at **5 k, half the 10 k ICD limit**. |

**GAP - flag to the architect: JLCPCB stocks no leaded / probe / ring-lug NTC.** Queries for
`MF52A 10K`, `NTC 10K 3950 leaded` and `thermistor 10K B3950` return only chip resistors. JLC's
entire NTC catalogue is (i) SMD chip thermistors like the NCP18 above and (ii) THT power inrush
discs (5D-9, 47D-15). If the LED sits on a remote heatsink, the sensing thermistor is **not a JLC
PCBA line item** - it must be sourced elsewhere and hand-terminated, and this board must provide
2 pads or an internal wire-to-board landing for it (which is permitted: the ICD only forbids
connectors that leave the enclosure).

**Recommendation: LM2903DR2G + off-board NTC on dedicated pads, open-collector output wired
straight to FAULT and to the drive-gate pull-down. TMP112 as the I2C telemetry companion.
~$0.43 at qty 6.**

---

## 5. Telemetry dividers, board ID and clamp (STR-REQ-18/19)

### Bank sense to ADC0 - the two constraints barely fight

Required: `Vout(57 V) <= 3.3 V` (ratio >= 17.27) and `Rth = R1||R2 <= 10 k`. Because `Rth =
R2 x k/(k+1)` with `k = 16.27`, **the source-impedance limit alone fixes `R2 <= 10.6 k` and
therefore `R1+R2 <= 183 k`, so the standing current can never go below ~262 uA / 12.6 mW at 48 V**
regardless of how the ratio is split. That 12.6 mW floor is **0.15% of the 8.5 W budget** - so the
"these two pull against each other" tension is real arithmetically but immaterial in practice.
The trap is the other direction: raising both legs to save current **violates the 10 k limit**.

| Divider | Vout @57 V | Vout @48 V | Rth | I @48 V | P @48 V | Verdict |
|---|---|---|---|---|---|---|
| 150 k / 10 k | 3.562 V | 3.000 V | 9.38 k | 300 uA | 14.4 mW | **Over 3.3 V at worst case - reject** unless deliberately clipped |
| **2 x 82 k (=164 k) / 10 k** | **3.276 V** | **2.759 V** | **9.43 k** | **276 uA** | **13.2 mW** | **Recommended** |
| 150 k / 9.1 k | 3.260 V | 2.745 V | 8.58 k | 302 uA | 14.5 mW | Fine; single 0805 top leg |
| 200 k / 12 k | 3.226 V | 2.717 V | **11.32 k** | 226 uA | 10.9 mW | **Violates the 10 k ICD limit - reject** |

The 2 x 82 k split is recommended because it satisfies **both halves** of the HV rule at once:
0805 *and* series-split, with each resistor seeing only **22.6 V at 48 V / 26.9 V at 57 V** against
a 150 V working rating (**6.6x margin** vs 2.6x for a single 0805). Add ~10 nF at the ADC pin -
9.43 k is right at the ICD ceiling and SAR sampling charge wants the local reservoir.

### Board ID on ID_ADC

Carrier fits the **top** leg (10 k to +3V3); this board fits the **bottom** leg to GND. Value
class only - the code is allocated by the carrier owner (requirements open question 8). A 1 k -
100 k E24 1% ladder against a 10 k top gives well-separated codes (2k2 -> 0.60 V, 4k7 -> 1.06 V,
10 k -> 1.65 V, 22 k -> 2.27 V, 47 k -> 2.75 V). `C23162` (0603 4.7 k 1%, BASIC) is listed as a
**placeholder**; it must be confirmed before P8. Source impedance is <= 5 k, comfortably inside
the ICD's 10 k.

### TVS on the 48 V input

Must stand off > 57 V and clamp < 100 V (the bank rating). All four below satisfy that; ranked by
clamping margin to the 100 V cap rating. Note there is **no MOV-to-earth network** anywhere - the
PD is unearthed (requirements s8.4) and this board must not copy one out of a reference design.

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | Standoff / Vbr(min) / Vclamp | Margin to 100 V |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **C2891331** | **SMBJ58A (GOODWORK)** | SMB | ext | 12903 | 0.0441 | 0.0354 | 58 V / 64.4 V / **93.6 V @6.4 A**, 600 W 10/1000 us | 6.4 V |
| 2 | C126829 | P6SMB68A (Littelfuse) | SMB | ext | 5647 | 0.1292 | 0.1028 | 58.1 V / 71.4 V / **92.0 V @6.5 A**, 600 W | **8.0 V - lowest clamp** |
| 3 | C110521 | SMAJ58A-13-F | SMA | ext | 18246 | 0.1316 | 0.1054 | 58 V / 71.2 V / 93.6 V @4.3 A, **400 W** | 6.4 V, 2/3 the surge energy |
| 4 | C2989905 | SMBJ60A | SMB | ext | 5791 | 0.0410 | 0.0323 | 60 V / 66.7 V / 96.8 V @6.2 A, 600 W | **3.2 V - too close** |

### Candidate table - divider resistors

| # | LCSC | MPN | Package | B/E | Stock | $ @6 | $ @100 | The rating that makes it fit |
|---|---|---|---|---|---|---|---|---|
| **1** | **C17840** | **0805W8F8202T5E** | 0805 | ext | 136945 | 0.0113 | 0.0113 | 82 k 1%, 125 mW, **150 V working**. Two in series = 164 k; each sees 22.6 V -> 6.6x margin. |
| 2 | C17470 | 0805W8F1503T5E | 0805 | **BASIC** | 956854 | 0.0129 | 0.0129 | 150 k 1%, 150 V working, Basic. Single-part top leg (2.6x margin) - pair with a 9.1 k bottom. |
| **B** | **C17414** | **0805W8F1002T5E** | 0805 | **BASIC** | 15.8 M | 0.0110 | 0.0110 | 10 k 1% bottom leg, Basic, 15.8 M in stock. |
| ID | C23162 | 0603WAF4701T5E | 0603 | **BASIC** | 4.25 M | 0.0117 | 0.0117 | ID_ADC bottom leg, **placeholder value only**. |

Confirmed working-voltage ladder from JLC's own parametrics, which is what the 0805 rule rests on:
**0402 = 50 V, 0603 = 75 V, 0805 = 150 V, 1206 = 200 V, 2010/2512 = 200 V** (500 V variants exist
in 2512). A single 0805 at 57 V has 2.6x margin and is compliant; the series split buys 6.6x.

---

## Risks and single-source flags

1. **TPS2490 / LM5069 are single-source in function.** No pin-compatible second source exists at
   JLC in the 80-90 V power-limiting class. The mitigations are (a) footprint-compatible fallback:
   TPS2490DGSR and LM5069MMX-2 are both MSOP-10/VSSOP-10 but the **pinouts differ** - they are not
   drop-in for each other, so the schematic commits to one; (b) the discrete P-ch soft-start
   (IRF5210S) as a documented plan B on the same board footprint if a P8 respin is acceptable.
2. **LM5069MMX-2 (C52940995) is a Tokmas clone**, not TI silicon. 1919 in stock, one vendor, no
   JLC-visible second source at that price. TI's own part is available (1751) at 6.9x the cost.
   **LCSC carries no datasheet for it** - the only characterisation available is TI's LM5069
   datasheet plus LCSC's parametric line (9-90 V, 55 mV sense, MSOP-10, -40..+125 C). For the
   part that owns the highest-risk function on the board, that is a real objection; C111822
   (genuine TI) exists precisely for this. C52175204 (2512 1 k 2 W) likewise has no LCSC
   datasheet - harmless for a resistor, noted for completeness.
3. **60 V eFuses (TPS26600 / TPS16630) have 3 V of headroom** over the 57 V worst case and 5 V to
   abs max. They will work, but a single 802.3 overshoot event puts them out of spec, and they
   have no power-limit engine - only ILIM + dV/dt + thermal shutdown, so their SOA behaviour into
   2800 uF is set by an internal die whose transient thermal impedance is not published either.
4. **No discrete MOSFET on JLC publishes SOA at 100 ms or 1 s.** Best case (Infineon HEXFETs) you
   get 100 us / 1 ms / 10 ms curves plus a Zthjc single-pulse curve to 1-10 s; worst case
   (NCE01P18K, and most Chinese-brand 100 V P-ch) there is no SOA figure at all. This is the
   single largest technical risk in the block and it is why family (c) is ranked first.
5. **No pulse/surge-rated chip resistor with a published joule rating is stocked** in the values
   the active bleed needs. Design around it (peak power under continuous rating) rather than
   specifying a J number that cannot be sourced.
6. **No leaded/probe NTC at JLC at all** (see section 4). Off-board LED thermal sense is not a
   JLC PCBA line item.
7. **No stocked SMD signal relay** - the relay-bypass inrush option is not buildable here.
8. **The only JLC Basic comparator is 0..+70 C**, under this board's own 69 C at-ambient. The
   whole block ends up with **zero JLC Basic active parts**; only the passives (100 k, 150 k,
   10 k, 4.7 k) are Basic. Budget the Extended-part setup fee accordingly at qty 6.
9. **TPS2490 latches on fault.** If a strict reading of STR-REQ-21 forbids any local latch, the
   auto-retry alternatives are thin: TPS2491DGS 73 units, LM5069MM-1 960 units at $9.53.

## Rough BOM cost of the recommended set, qty 6

TPS2490 $2.80 + IRF540NS $0.75 + 50 mohm shunt $0.06 + 100 k bleed $0.01 + 1 k 2 W $0.09 +
MMBTA42 $0.05 + LVC1G08 $0.04 + LM2903 $0.06 + TMP112 $0.33 + NTC $0.04 + divider/ID/TVS ~$0.09
= **~$4.32/board**, or **~$3.26/board** with the LM5069 clone in place of TPS2490. Against the
$25 board target (open question 7), the protection-sense block is 13-17% of the budget - the bank
and the LED are still the expensive items.
