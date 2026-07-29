# P1 component scout - constant-current LED driver (LUM-PAR-A)

Block: four (possibly five) independent PWM-dimmed constant-current channels, R/G/B/W.
Method: shortlist -> live `parts_search.py` (source `live`, all rows re-verified in one pass)
-> **datasheet timing pulled from the actual PDF** for every candidate that survived.
Machine-readable candidate list: `led-driver.json` (same rows, parts_search objects with
`lcsc`/`mpn`/`basic`/`stock`/`price`/`datasheet` intact, plus `rank`/`verdict`/`pwm_evidence`).

**There is no JLC Basic constant-current LED driver.** `parts_search --basic-only` over
"LED driver buck constant current" and "LED driver PWM dimming" both return zero rows.
Every candidate below is Extended. Same situation as the ICD connectors - not a selection error.

---

## 0. The number everything hangs on, and one arithmetic correction

PAR-REQ-09 at 13 bit / 9.766 kHz: period **102.4 us**, 1 LSB = **12.5 ns**
(`03` brief says 12.2 ns; 102.4/8192 = 12.5 ns - immaterial, both are far below any driver).

| Dimming floor asked for | duty | on-time |
|---|---|---|
| Q9 (a) 5-10 % of **duty** | 5.0-10.0 % | 5.12-10.2 us |
| Q9 (b) 5-10 % of **perceived** brightness, gamma 2.2 | 0.137-0.63 % | **0.140-0.65 us** |

> **Correction for the architect.** `requirements.md` s9 Q9(b) states "duty is 0.14-0.6 %,
> on-time **1.4-6.1 us**". The duty figures are right; the on-times are a factor of ten high.
> 0.137 % x 102.4 us = **140 ns**, 0.63 % x 102.4 us = **646 ns**. This matters: it moves
> Q9(b) from "several switching drivers manage it" to "only one part in this survey has a
> min-pulse spec below it, and only with a shunt FET".

**The IC's minimum on-time is necessary but not sufficient.** The binding limit in a buck
CC driver is the *inductor* slew, not the silicon:

```
  rise: di/dt = (Vin - Vstring)/L        fall: di/dt = Vstring/L   (freewheel through the LEDs)
```

| config | L | rise to 350 mA | fall from 350 mA |
|---|---|---|---|
| +12V, 3-die string 9.6 V | 47 uH | **6.9 us** (kills a 5 % pulse outright) | 1.7 us |
| +12V, 1-die string 3.2 V | 47 uH | 1.9 us | 5.1 us |
| +12V, 1-die string 3.2 V | 10 uH | 0.40 us | 1.1 us |
| **+48V_SW**, 3-die 9.6 V | 47 uH | **0.43 us** | 1.7 us |
| **+48V_SW**, 3-die 9.6 V | 22 uH | 0.20 us | 0.80 us |

Two consequences, both load-bearing for P2:

1. **`+48V_SW` is better for dimming *fidelity*, independently of watts** - ~16x the current
   slew rate for the same inductor and string. That is a new argument for the 48 V rail that
   the requirements' rail discussion does not contain.
2. **Q9(b) is not reachable by gating the converter, on either rail.** 140-650 ns on-times
   need a **shunt FET across the LED string** (converter free-runs, FET diverts). TPS92515HV
   is the only candidate that specifies this mode: *"10,000:1 Shunt PWM Dimming Range"*, with
   *"Shunt FET PWM dimming can out-perform PWM dimming"* and a dedicated OFF-timer behaviour
   for the shunted-output condition. Cost: one logic-level NFET + gate resistor per channel.

---

## 1. Ranked candidates - RAIL A: **+12 V** (preferred source)

Prices are LCSC unit @ qty 1 / qty 30. Build need is 8 boards x 4 ch = **32 pcs + spares**.

| # | MPN | LCSC | Pkg | B/E | Stock | $ @1 / @30 | Vin | Iout | **PWM timing from the datasheet** | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **TPS92515HVDGQR** | C213553 | MSOP-10-EP | Ext | 919 | 2.19 / 1.69 | 5.5-65 V | 2 A int. FET | `tPWM(uvlo)` PWM rise->SW rise **75 ns typ / 130 ns max**; PWM fall->SW fall **100/170 ns**; `tLEB` min ON-time **75/195/275 ns**. s8.3.11 works our exact case: *"if a 10 kHz PWM frequency is desired having a period of 100 us, the minimum duty cycle is 200 ns/100 us = 0.2 %... 500:1 dimming"*. Features: 1000:1 PWM / **10,000:1 shunt PWM**. Caveat in the same paragraph: *"Standard PWM frequency ranges can also be used (100 Hz to 2 kHz)"*. | **PICK** |
| 2 | **LM3414HVMRX/NOPB** | C12651 | SOIC-8-EP | Ext | 2250 | 2.13 / 1.60 | 4.5-65 V | 1 A int. FET | `tON-MIN` **400 ns**; fSW 250 k-1 MHz. s7.3.4: *"allows the inductor current to slew up to the preset regulated level at full speed instead of charging the inductor with multiple restrained switching duty cycles... high-speed dimming and very fine dimming control"*; *"dimming frequency not higher than 1/10 of the switching frequency"* (=100 kHz at 1 MHz fSW); *"minimum dimming duty cycle is limited by the 400 ns minimum ON time"*. Typ. Char. **Figure 13 is "LED Current With PWM Dimming (9-us dimming pulse)"** - i.e. TI characterised almost exactly our 5 %-duty pulse. | runner-up |
| 3 | **AL8863SP-13** | C2157845 | ESOP-8 | Ext | 1645 | 0.58 / 0.42 | 4.5-60 V | 5 A, **ext. NFET** | EC block *PWM DIMMING (DIM)*: **fPWM recommended 0.1-20 kHz**; VDIM_HIGH 2.6-5.5 V (3.3 V logic OK); tPD 100 ns; gate tRISE 100 ns / tFALL 60 ns; tON_REC 500 ns for 4 % accuracy. *"The AL8863 does not have in-built soft-start action - this provides very fast turn on"*. **Contradiction to resolve:** the application text on the same page still says *"the PWM frequency is recommended to be lower than 500 Hz"*. | cheap alt. |
| 4 | **LM3409MYX/NOPB** | C473394 | MSOP-10-EP | Ext | 1670 | 1.33 / 1.05 | 6-42 V | ext. PFET | Features **"10,000:1 PWM Dimming Range"**; `tON-MIN` 115 ns typ / 211 ns max. s8.3.6: EN is *"a TTL compatible input for PWM dimming"*, and *"while EN is low the support circuitry (driver, bandgap, VCC regulator) remains active to minimize the time needed to turn the LED array back on"*. Typ. Char. contain **"20 kHz 50 % EN Pin PWM Dimming"** and its rising-edge detail. Honest about the real limit: *"LED current rise and fall times... are limited by the slew rate of the inductor"*. | candidate |
| 5 | **PT4115EE89E** | C126161 | SOT-89-5 | Ext | 11427 | 0.230 / 0.230 | 6-50 V | 1.5 A int. | EC *DIM Input*: **FDIM_MIN 0.1 kHz, FDIM_MAX 20 kHz**; off below 0.3 V, full current at >=2.5 V. **No min on-time, no turn-on/off delay given.** | budget, capped |
| 6 | **PT4115** (UMW) | C347356 | SOT-89-5 | Ext | 179854 | 0.110 / 0.110 | 6-30 V | 1.2 A int. | Same family, and its EC table supplies the number the EE variant omits: `fDIM` max **20 kHz**; `DPWM_LF` min duty **0.02 % at 100 Hz -> 5000:1**; `DPPWM_HF` min duty **4 % at 20 kHz -> 25:1**. 4 % of 50 us = **2 us minimum on-time**, so at 9.766 kHz the floor is ~2 % duty, ~50:1, i.e. **~5.6 usable bits, not 13**. | budget, capped |

**Rejected on the 12 V rail, with the quote that kills each** (kept in the JSON so P3 cannot
re-propose them):

| MPN | LCSC | Why rejected |
|---|---|---|
| **SN3350IP05E-01** | C336596 | Cleanest kill in the survey. EC table: dimming ratio **1200:1 at fPWM = 100 Hz** but **13:1 at fPWM = 10 kHz**. 13:1 is ~3.7 bits. (The silicon is fast - TPD 50 ns, TONmin 200 ns - it is the ADJ control path that is slow.) |
| **AL8861MP-13** (+ AL8860 C500782, AL8862 C526360) | C155534 | *"the PWM frequency is recommended to be lower than 500 Hz"*; pin table *"1 % to 100 % of IOUTNOM for f < 500 Hz"*; and **built-in soft-start "Default soft-start time = 0.1 ms"** = 100 us = essentially the whole 102.4 us period. |
| **ZXLD1362ET5TA** | C154735 | PWM duty spec exists only *"during low frequency PWM dimming mode, PWM frequency <300 Hz"*. Shutdown needs *"ADJ below 0.2 V for more than approximately 100 us"* - never satisfied at 9.766 kHz below ~98 % duty, so the internal filter turns PWM into **analogue current dimming**, which also violates PAR-REQ-08. tSS 2 ms. |
| **AL5809-xx** | C332295 etc. | *"applying a PWM signal with a frequency range between 100 Hz and 200 Hz"*; 2-terminal, max 150 mA, current fixed by part number. |
| **AL5812MP-13** | C460648 | Linear, 150 mA. Dimming is by switching RSET through an external FET; datasheet characterises **only 100 Hz and 500 Hz** and states **no** frequency limit, min pulse width or delay. Per the brief's rule: **RISK, not a candidate**. |
| **CAT4104V-GT3** | C236266 | 4-ch linear sink, 175 mA/ch, LED pins to 25 V - but **one shared EN/PWM pin for all four outputs**, so it cannot give four independent colours. (Timing not verified: onsemi PDF blocked.) |

---

## 2. Ranked candidates - RAIL B: **+48V_SW** (>= 60 V input)

The good news: **the top two picks are already 65 V parts**, so choosing the rail does not
change the driver family, only the passives, creepage and clamping.

| # | MPN | LCSC | Pkg | Stock | $ @1 / @30 | Vin | Margin at 57 V worst case | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | **TPS92515HVDGQR** | C213553 | MSOP-10-EP | 919 | 2.19 / 1.69 | 5.5-65 V, abs max **65 V** on VIN/DRN/CSN/SW | 8 V (14 %) | Same part as rail A. Wants a TVS/clamp - 8 V is thin for a switching node with a 57 V rail. |
| 2 | **LM3409HVMYX/NOPB** | C529298 | HVSSOP-10-EP | 3597 | 2.58 / 2.08 | 9-75 V | **18 V (32 %) - best margin here** | External PFET + Schottky + sense R per channel: ~4 extra parts x 4 channels. |
| 3 | **LM3414HVMRX/NOPB** | C12651 | SOIC-8-EP | 2250 | 2.13 / 1.60 | 4.5-65 V, transient 67 V/500 ms | 8 V | Same part as rail A. |
| 4 | **AL8863SP-13** | C2157845 | ESOP-8 | 1645 | 0.58 / 0.42 | op 4.5-60 V, **abs max 65 V** | **3 V of operating margin** | Cheapest 20 kHz-rated part by 4x, but 57 V against a 60 V operating limit is 5 % - I would not ship it on 48 V without a clamp and a written waiver. Fine on +12 V. |
| - | **HV9910BLG-G** | C9099 | SOIC-8 | 4256 | 1.21 / 0.92 | 8-450 V | huge | **REJECTED**: datasheet says the PWMD input accepts *"a duty ratio of 0-100 % and a frequency of up to a few kilohertz"*. Below 9.766 kHz on the manufacturer's own wording. (Verified from datasheet text via web; the Microchip PDF download was blocked, so this one line is not PDF-parsed like the rest.) |
| - | MP4689AGN-Z | C3199753 | SOIC-8-EP | **35** | 2.86 | 4.5-100 V | huge | Stock too thin to plan 32+ pcs around; not evaluated further. |

**Which rail I would pick: `+48V_SW`, for both channels of reasoning - and this contradicts
the `ASSUMED:` in `requirements.md` s3.2, so it needs the architect's decision, not mine.**

- Dimming fidelity: ~16x faster LED-current slew (table in s0) is the single biggest lever on
  PAR-REQ-09 available anywhere in this survey, and it costs nothing in parts.
- Headroom: at af the `+48V_SW` ceiling is 0.25 A = **12.0 W**, comfortably above the
  8.6-9.3 W envelope; `+12V` is 0.75 A = 9.0 W, i.e. *at* the envelope (requirements s3.2
  already calls this "right at the edge"). ICD s6.3 also gives 0.67 W (af) / 1.30 W (at) back
  by skipping the conversion.
- Price of admission (all already in requirements s3.3, none of it new): 0.60 mm creepage
  board-wide, 100 V caps, 0805+ resistors across the 48 V domain, mandatory bleed path,
  daughter-owned inrush sized against the PD's 1.0 A limit, and the rail being **dead for
  hundreds of ms after power-up** - the drivers must tolerate that and not glow.
- The 1.0 A eFuse **latches off**: with four channels this needs the PAR-REQ-11 hardware
  backstop to be sized against 1.0 A at 48 V, not just against the 12 V OCP.

If the architect keeps `+12V` (D-02's stated intent, and one fewer compliance regime), then
**use single-die strings, not 3-die**, and a small inductor (10-22 uH) at high fSW - see s0.
3-die strings on 12 V give a 6.9 us rise time and destroy the 5 % point on their own.

---

## 3. Class 3 - multi-channel driver ICs with their own PWM engine

Evaluated as a genuine option (it would sidestep the carrier PWM entirely). **It does not work
at this power level.** No part in the class delivers >= 150 mA/ch *and* >= 10 kHz *and* useful
resolution *and* independent channels.

| Part | LCSC | I/ch | PWM engine | Verdict |
|---|---|---|---|---|
| **LP5024RSMR** | C427525 (7774 stk, $1.23/$0.94) | 25.5 mA (35 mA if VCC >= 3.3 V) | **21-29 kHz**, *"12 bits of control accuracy... 9 bits of pure PWM resolution and 3 bits of digital dithering"* | Best PWM engine found anywhere - but outputs are abs-max 5.5 V linear sinks with 0.25-0.4 V VSAT. Cannot drive our strings. **Only role: a local 12-bit/29 kHz PWM *source* into four driver DIM pins.** That does not fix the driver's own settling limit, so it buys nothing the carrier's 13-bit/9.766 kHz does not already provide. |
| TLC5947 (C181402) | 24 ch, 30 mA | internal 4 MHz osc / 4096 = **~977 Hz** | fails frequency by 10x |
| TLC59711 (C1554176) | 12 ch, 60 mA | 16-bit off a 7-12 MHz GS clock = **~150-180 Hz** | fails frequency by 50x |
| PCA9685 (C2678753) | 16 ch, 25 mA | 12-bit, **24-1526 Hz** | fails frequency |
| IS31FL3236A (C3198350) | 36 ch, 38 mA | 3 kHz / 22 kHz selectable, **8-bit** | 8-bit and 38 mA; also only 90 in stock |
| TLC5940 (C181653) | 16 ch, **120 mA** | 12-bit off an *external* GSCLK; 12-bit at 30 MHz = 7.3 kHz max, and the ICD offers no free-running clock | fails frequency + needs a continuous clock the connector does not carry |

**Rank: below classes 1 and 2.** Keep LP5024 on file only as a fallback if the carrier's LEDC
allocation is ever taken away (requirements s2.3 note about timers 2/3).

---

## 4. Class 2 - linear / LDO constant-current sinks: the dissipation, quantified

PWM speed is a non-issue here (a logic-level NFET switches in ns). **Power is the issue**, and
this is the PAR-REQ-10 test. Per channel from a 12 V rail: `P_lin = (12 - Vstring) x I`.

| String per channel | Vstring | drop | P at 350 mA | x4 channels | share of the 8.6-9.3 W af envelope |
|---|---|---|---|---|---|
| 1 die (R 2.0-2.6 / G,B,W 2.9-3.6) | 2.0-3.6 V | 8.4-10.0 V | 2.9-3.5 W | **11.8-14.0 W** | **>100 % - fatal** |
| 3 die G/B/W | 9.0-10.8 V | 1.2-3.0 V | 0.42-1.05 W | | |
| 4 die R | 8.0-10.4 V | 1.6-4.0 V | 0.56-1.40 W | **1.8-4.6 W** (3xGBW + 1xR) | **20-53 %** |

So linear is only survivable with **per-colour string counts tuned so every string sits near
10-11 V**, at the *bottom* of the current range (150-350 mA), and it still spends a fifth to
half of the whole af budget as heat - inside a box whose internal air is already 56 C, next to
a red die that wants to stay at 85-100 C. At 700 mA-1 A it is not viable at all.

PAR-REQ-10 forbids burning the R-vs-GBW spread **in a shared linear element**; four independent
per-colour sinks with per-colour string lengths satisfies the letter of that. But it converts
this board's hardest problem (thermal) into its only problem, so:

**Recommendation: do not use class 2 as the primary topology.** Keep it as the documented
fallback if Q9 answers (b) *and* the architect rejects shunt-FET dimming - it is the only
topology that reaches 140 ns on-times with no cleverness at all.

No single IC is recommended for it: AL5812 has no PWM timing spec (RISK), AL5809 is 100-200 Hz
and 150 mA, CAT4104 cannot do independent channels. A discrete sink (op-amp + logic-level NFET
+ sense resistor per channel, PWM into the op-amp reference or the gate) is the only clean
implementation, and that is a P2 design decision, not a part choice.

---

## 5. Cost, at 8 boards x 4 channels (+ the 5th channel if Q4 says yes)

| Option | per channel | per board (4 ch) | 32 pcs total |
|---|---|---|---|
| TPS92515HV | $1.69 | $6.78 | $54.2 |
| LM3414HV | $1.60 | $6.38 | $51.1 |
| LM3409(HV) + PFET + Schottky + sense R | ~$1.05-2.08 + ~$0.40 passives | ~$5.8-9.9 | - |
| AL8863 + NFET + sense R | ~$0.42 + ~$0.20 | ~$2.5 | $13.4 |
| PT4115 / PT4115EE | $0.11 / $0.23 | $0.44 / $0.92 | $3.5 / $7.4 |

Against requirements s9 Q14's suggested $25-35/board excluding emitter and heatsink,
**TPS92515HV at ~$6.80/board is ~20-27 % of the board target for the driver silicon alone**
before inductors, diodes, caps and the ENABLE gate. Affordable, but it is the single biggest
line on this board's BOM. AL8863 is 2.7x cheaper and is the fallback if the BOM target bites.

---

## 6. Risks

1. **Single-source, and the top pick is the thinnest line.** TPS92515HVDGQR: TI only, **919 in
   stock**, no pin-compatible second source anywhere (LM3414HV is a different pinout, LM3409HV a
   different topology). 32-40 pcs is 4 % of stock, so this is a schedule risk, not a supply
   risk - but there is no drop-in alternate, so a stock-out means a schematic change. Buy the
   whole build's worth plus spares in one order.
2. **Every candidate's dimming pin *is* its enable pin.** None of TPS92515 / LM3414 / LM3409 /
   AL8863 / PT4115 has an EN or SHDN pin separate from PWM/DIM. The ICD's active-HIGH `ENABLE`
   therefore **must** be AND-ed with each PWM line externally. Verified support part:
   **74LVC08AD,118 (C6052, SOP-14, 2727 stk, $0.21)** - one package covers all four channels,
   tPD 4.1 ns is nothing against 102.4 us; single-gate alternative SN74LVC1G08DBVR (C7666,
   $0.054). This contradicts the brief's "a driver with an EN/SHDN pin is strongly preferred" -
   no such driver exists in this performance class, so budget the gate.
   (Note: on TPS92515 the PWM pin is *also* UVLO/enable and has a 100 uA pulldown that
   guarantees no LED glow when low - which is exactly the ENABLE fail-safe behaviour wanted.)
3. **The 20 kHz claims are not all equal.** AL8863's own datasheet contradicts itself
   (EC table 0.1-20 kHz vs application text "<500 Hz"); PT4115 *quantifies* its 20 kHz as
   25:1 dimming ratio. Only TPS92515 and LM3414 back the claim with delay/min-pulse numbers
   and with characterisation figures at our pulse width. Treat a bare "20 kHz PWM dimmable"
   line as marketing.
4. **Per-channel current is not yet fixed and the answer is modest.** Back-solving the af
   envelope (requirements s3.4: ~7.6-8.5 W reaching the emitters, 4 channels): ~1.9-2.1 W per
   channel = **~200-220 mA into a 3-die 9.6 V string, or ~600-650 mA into a single 3.2 V die**.
   Nothing here needs the 1 A / 2 A end of the range; the 1 A parts are comfortable and the 2 A
   TPS92515 is oversized (which is fine). **P2 must publish this number** - requirements s8
   leaves the >3 A flag conditional on it, and none of these configurations approaches 3 A.
5. **Thermal.** TPS92515 HVSSOP-10 RthJA 56.2 C/W, RthJC(bot) 5.3 C/W - the pad must be
   soldered to a via farm. At ~0.2-0.3 W per driver and 56-69 C internal air the junction rise
   is ~15 C, so the drivers are not the thermal problem; the emitters are. But requirements
   s5.2 bans LED drivers from the DC-DC hot zone (2,46)-(36,68), and four buck channels plus
   the antenna keepout (88,25)-(100,55) leaves a genuinely tight placement problem for P4.
6. **Switching drivers 11 mm above a 2.4 GHz PCB antenna** (requirements s8). Four buck
   converters at 250 kHz-1 MHz with harmonics into the GHz. Not a part-selection issue, but it
   argues for the *lowest* switching frequency that still meets the slew-rate table in s0 -
   which pulls against the fidelity argument. Flagging the tension; P2/P5 own it.
7. **HV9910B's rejection is the only line in this report not parsed from a local PDF.** The
   Microchip PDF download was blocked; the "up to a few kilohertz" wording came from the
   datasheet text via web search. If 450 V capability ever matters, re-verify it properly.

---

## 7. What I would tell P3 to buy, if forced to choose today

- **+12 V build:** TPS92515HVDGQR (C213553) x4, single-die strings, 10-22 uH, plus one
  74LVC08AD (C6052) for the ENABLE gate. Expect ~0.4-2 % duty floor (~8-9 bits usable).
- **+48V_SW build (my preference):** the same TPS92515HVDGQR, with a 3-4 die string per
  channel, 22-47 uH, a clamp on VIN, and one shunt NFET per channel if Q9 answers (b).
  Expect sub-microsecond edges and the datasheet's 500:1 without the shunt, 10,000:1 with it.
- **If the BOM target bites:** AL8863SP-13 (C2157845) on +12 V only, and accept the
  self-contradicting datasheet as a bench-verification item.
