# lumina-par (LUM-PAR-A) - power tree and the sustained-power table

This file is `03` design review gate 1 and a required H1 deliverable. All figures
are for **branch A (`+12V`)**, the recommended baseline; branch B (`+48V_SW`) is
tabulated in s7 for the H1 comparison.

Every number below is arithmetic on the P1 research constants. Nothing is lifted
from a brief without being re-derived.

---

## 1. The design point, and where the numbers come from

| Item | Value | Source |
|---|---|---|
| Emitter packages | **4x** XINGLIGHT XL-HD6070RGBCW-A5 class, 4 dies each | led-emitter s1 (only in-stock RGBW 4-in-1) |
| String per channel | **2S2P** (2 series x 2 parallel), 1R5 ballast per branch | led-emitter s4: a 4S G/B/W string is 12.4 V typ / **13.6 V max - above the +12V rail**, so a buck cannot make it. 2S2P is the 12 V arrangement |
| Design current | **150 mA/die**, i.e. **300 mA/channel** | back-solved from the `+12V` 0.75 A sustained ceiling (s3) |
| Vf, typ | R 2.1 V, G/B/W 3.1 V | led-emitter s4 |
| Vf, worst case | R 2.4 V, G/B/W 3.4 V | led-emitter s4 - **this is the column the hardware backstop is sized on** |
| Ballast | 1.5 ohm per parallel branch, 0.225 V drop at 150 mA | s2 |
| Buck efficiency | **91 %** (conservative; the loss inventory computes 92.3 %) | derived |
| Idle (shunted) channel input | **0.20 W** | s2 - dominated by the catch diode |
| `+3V3` housekeeping | **<= 5 mA (0.017 W)** | s4 |

Load voltage per channel (string + ballast) at 300 mA:

| Channel | typ | **worst case** |
|---|---|---|
| Red (2S2P) | 4.2 + 0.225 = **4.43 V** | 4.8 + 0.225 = **5.03 V** |
| Green / Blue / White (2S2P) | 6.2 + 0.225 = **6.43 V** | 6.8 + 0.225 = **7.03 V** |

Per-channel power at 100 % duty:

| Channel | load W (typ) | in W (typ) | **load W (worst)** | **in W (worst)** | **`+12V` A (worst)** |
|---|---|---|---|---|---|
| Red | 1.33 | **1.46** | 1.51 | **1.66** | **0.138** |
| Green | 1.93 | **2.12** | 2.11 | **2.32** | **0.193** |
| Blue | 1.93 | **2.12** | 2.11 | **2.32** | **0.193** |
| White | 1.93 | **2.12** | 2.11 | **2.32** | **0.193** |
| **All four** | 7.12 | **7.82** | 7.83 | **8.62** | **0.718** |

---

## 2. Where the 0.20 W idle term comes from, and why it matters

Under shunt-FET dimming (`blocks.md` D2) the converter **free-runs at its current
setpoint whatever the commanded duty**; the shunt FET diverts current away from
the string. A channel commanded to 0 % therefore still burns power. This is a real
architectural cost of the topology that PAR-REQ-01 forces, and it is not in any
research fragment.

Loss inventory for one channel at 0 % duty, 300 mA, 12 V in, 47 uH:

| Element | Loss |
|---|---|
| Catch Schottky (60 V, Vf 0.45 V at 0.3 A), conducting ~100 % of the cycle because the duty collapses to ~0.5 % | **135 mW** |
| Inductor DCR (0.3 ohm) | 27 mW |
| Driver IC quiescent (~2 mA at 12 V) | 24 mW |
| Switching loss at ~700 kHz | ~30 mW |
| Shunt FET (50 mohm at 0.3 A) | 4 mW |
| **Total per idle channel** | **~0.22 W - 0.20 W used below** |

Three consequences, all load-bearing:

1. **Four idle channels cost 0.8 W, ~10 % of the af envelope**, and that is the
   state a saturated-colour wash spends most of its time in. This is the
   quantitative case for the **converter-idle one-shot** in `blocks.md` B3: fit it
   and rows 4-7 below drop by 0.4-0.6 W each.
2. **The one-shot does not help at the dimming floor** (row 8), because pulses are
   still arriving. 0.8 W of shunt loss at 0.14 % duty is unavoidable with this
   topology and is part of the price of reaching 141 ns at all.
3. **The idle term never makes a partial-colour point worse than full white**,
   because 0.20 W is smaller than the 1.66-2.32 W a lit channel draws. **Full
   white remains the worst case in every operating mode** - which is what makes it
   a valid hardware backstop.

The catch diode dominates, so **specify a 60 V Schottky on branch A, not a 100 V
one** (100 V parts run 0.6-0.7 V at 0.3 A and would push the idle term to
~0.3 W/channel). Branch B needs the 100 V part and pays that penalty.

---

## 3. Sustained-power table at realistic mixed-colour operating points

**af column.** Duty-weighted: `P_in(d) = d x P_full + (1 - d) x 0.20 W`, on the
worst-case-Vf column. `+3V3` adds 0.017 W to every row and is shown only in the
total.

| # | Operating point | R | G | B | W | `+12V` W | **`+12V` A** | vs **0.75 A** af ceiling | vs 2.0 A OCP | total W |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **Full white - all four at 100 %. This is the stuck-PWM hardware backstop** | 100 | 100 | 100 | 100 | 8.62 | **0.718** | **96 %** | 36 % | **8.64** |
| 2 | Full-room warm wash, high intensity | 100 | 80 | 20 | 100 | 6.50 | 0.542 | 72 % | 27 % | 6.52 |
| 3 | Full-room warm wash, saturated gold | 100 | 60 | 10 | 100 | 5.86 | 0.489 | 65 % | 24 % | 5.88 |
| 4 | Saturated red | 100 | 0 | 0 | 0 | 2.26 | 0.188 | 25 % | 9 % | 2.28 |
| 5 | Saturated green | 0 | 100 | 0 | 0 | 2.92 | 0.243 | 32 % | 12 % | 2.94 |
| 6 | Saturated blue | 0 | 0 | 100 | 0 | 2.92 | 0.243 | 32 % | 12 % | 2.94 |
| 7 | Deep magenta | 100 | 0 | 100 | 0 | 4.38 | 0.365 | 49 % | 18 % | 4.40 |
| 8 | **PAR-REQ-01 dimming floor** - all four at 5 % perceived (duty 0.137 %) | 0.14 | 0.14 | 0.14 | 0.14 | 0.81 | 0.067 | 9 % | 3 % | 0.83 |
| 9 | ENABLE de-asserted (fixture powered, dark) | - | - | - | - | 0.01 | 0.001 | <1 % | <1 % | 0.03 |

With the converter-idle one-shot fitted, rows 4-7 become 1.66 / 2.32 / 2.32 /
3.98 W (0.138 / 0.193 / 0.193 / 0.332 A). Rows 1-3 and 8 are unchanged.

Typical-Vf column, as the expected-case reality:

| # | `+12V` W (typ Vf) | `+12V` A (typ Vf) |
|---|---|---|
| 1 | 7.82 | 0.652 |
| 2 | 5.90 | 0.492 |
| 3 | 5.32 | 0.443 |
| 7 | 3.98 | 0.332 |

### The four findings this table produces

1. **The worst case the music profiles actually call for (rows 2-3) is 65-72 % of
   the hardware maximum.** A warm wash drops blue, and blue is a full 2.32 W
   channel. So PAR-REQ-11's firmware clamp **rarely bites for warm content**; it
   bites for white and for pastels. Requirements Q1's recommendation (uniform
   hue-preserving scaling) is therefore cheap in practice.
2. **Full white is the worst case in every mode.** No mixed colour, no dimming
   level and no fault state exceeds row 1.
3. **Row 1 is the stuck-PWM case by construction.** With ENABLE asserted and every
   PWM stuck at 100 % (hung MCU - the 2 s watchdog fade cannot help if the MCU is
   what hung), the current setpoint is fixed by the sense resistors, so the draw
   is bounded at **0.718 A: 4 % under the 0.75 A sustained ceiling and 2.8x under
   the 2.0 A OCP.** The board is electrically incapable of exceeding its own
   budget, which is what requirements s3.3 demands and is not optional.
4. **The >3 A conditional flag (requirements s8) is NOT triggered and is closed.**
   Maximum per-channel current is **0.30 A** (af), 0.51 A (at, branch A), 0.35 A
   (branch B at `at`). Nothing on this board or its harness approaches 3 A.

### One number that does not reconcile, resolved explicitly

Row 1's total (8.64 W) is **1.6 % above ICD s6.2's TOTAL row (8.5 W af)** and at
the low edge of requirements s3.1's re-derived 8.6-9.3 W. Both figures are real
and they measure different things:

- ICD s6.2's total is a **firmware-governed average** - the ICD says so: *"the
  total is what binds, and it is enforced by firmware's average-energy governor -
  now closed-loop, because the carrier's eFuse has an analogue current-monitor
  output wired to an MCU ADC."*
- 0.718 A is the **hardware backstop**: the worst-case-Vf draw with firmware dead.
  Its correct comparator is the **per-rail sustained ceiling** (met with 4 %) and
  the OCP (met with 2.8x).
- At **typical** Vf the backstop is 7.82 W, **8 % under** the ICD total.

**Resolution: size against the per-rail ceiling, which is a hardware number, and
let firmware's PAR-REQ-11 governor hold the average under 8.5 W.** If the human
wants zero firmware reliance on the total as well, **145 mA/die puts the
worst-case-Vf backstop at 8.33 W / 0.692 A - under the ICD total with 2 % margin -
at the cost of 3 % of light.** Recommendation: 150 mA/die. Either is a
sense-resistor value, decidable at H1 or as late as P3.

---

## 4. Rail-by-rail budget

| Rail | J3 pins | af ceiling | **design max (af)** | headroom | at ceiling | **design max (at)** | Fault ceiling |
|---|---|---|---|---|---|---|---|
| `+48V_SW` | 1, 3, 5 | 0.25 A | **0 A - landed, not tapped** | n/a | 0.50 A | 0 A | 1.0 A eFuse, latch off |
| `+12V` | 9, 11 | 0.75 A | **0.718 A** | **4 %** | 1.25 A | **1.222 A** | 2.0 A converter OCP |
| `+3V3` | 12, 14 | 0.25 A | **0.005 A** | 98 % | 0.25 A | 0.005 A | 1.0 A converter |
| **Total** | - | 8.5 W (ICD) / 8.6-9.3 W (req) | **8.64 W** | see s3 | 18.5 / 18.7-20.0 W | **14.69 W** | PSE overload ~50-75 ms |

**Connector pin loading** (ICD s4.1 derate: 1.80 A/pin): `+12V` at 0.718 A over
2 pins is **0.36 A/pin, 5.0x margin**. GND at 0.723 A over 7 power-block pins is
0.10 A/pin, 17x. Neither is anywhere near a limit, and this board consumes none of
the 48 V pin allocation.

### `+3V3` housekeeping inventory

| Load | Current |
|---|---|
| Quad open-drain comparator, 4 channels | 0.20 mA |
| 2x NTC divider (10 k + 10 k) | 0.35 mA |
| `ID_ADC` bottom leg (worst case) | 0.33 mA |
| 74LVC00A + SN74LVC1G08, dynamic at 9.766 kHz + static | 0.13 mA |
| Comparator reference ladder | 0.10 mA |
| Pull-downs: ENABLE, 4x PWM, 4x shunt gate; FAULT pull-up (all 100 k) | 0.30 mA |
| 24C32 EEPROM standby | 1 uA |
| **Total** | **~1.4 mA; budget <= 5 mA (0.017 W)** |

`+3V3` is **logic and sense only, never LED current** (D-02). At 2 % of its
ceiling it constrains nothing.

---

## 5. The `at` upgrade on branch A - what it does and does not buy

The `+12V` at-ceiling is **1.25 A = 15.0 W**, a thermal limit on the carrier's
48->12 converter in a sealed box (ICD s6.3), not a current rating that can be
argued with. Solving `(50.4x + 12x^2) / 0.91 <= 15.0` for die current x:

| | branch A at `at` | branch B at `at` |
|---|---|---|
| Max die current | **250 mA/die** | 350 mA/die (the package maximum) |
| Emitter electrical power | **12.60 W** | 17.64 W |
| Ballast | 0.75 W | none (series 4S) |
| Rail draw | 14.67 W = **1.222 A on `+12V`** | 19.60 W = **0.408 A on `+48V_SW`** |
| vs the at emitter budget 16.5-18.4 W | **68-76 %** | 96-107 % |
| vs the 18.7-20.0 W envelope | 14.69 W - **4.0-5.3 W unreachable** | 19.62 W - fits |

**Branch A is not pinned to Type 1; it reaches ~72 % of the `at` emitter power.**
Requirements s3.2 predicted the 12 V rail would "miss by 3.7-5.0 W" at `at`;
confirmed at 4.0-5.3 W. Against D-01's *"do not allow any other component to
become the part that pins the design to Type 1"*, the honest statement is that
branch A **degrades** the at upgrade by roughly a quarter rather than killing it -
and s6 shows the at case is already blocked thermally at any rail choice.

The at upgrade on branch A is a **sense-resistor value change plus a firmware
constant**. No respin, no module rewire.

---

## 6. Heat budget - what goes where

Splitting row 1 (full white, worst-case Vf, 8.62 W in):

| Destination | Power | Note |
|---|---|---|
| **This PCB** - driver conduction, switching, diode, quiescent | **0.79 W** | 8.62 in minus 7.83 delivered |
| **This PCB** - `+3V3` logic | 0.02 W | |
| **LED module** - emitter dies | 7.56 W electrical -> **5.67 W heat** (75 % to heat, 25 % to light) | on the MCPCB |
| **LED module** - ballast resistors | **0.27 W**, all heat | on the MCPCB |

**This board dissipates 0.79-0.81 W across the entire output range**, because the
shunt loss at the dimming floor (0.80 W) is almost exactly the converter loss at
full output (0.79 W). That flatness is a gift for the enclosure analysis:

| Enclosure scenario | In-box heat | Rise at 4.0 K/W | Internal air, 25 C room | vs D-T10's 45 C criterion |
|---|---|---|---|---|
| **Sealed, LED module heat conducted out through the wall** | carrier 2.4 + this board 0.81 = **3.21 W** | 12.8 K | **38 C** | **closes, with margin** |
| **Sealed, LED module inside the box** | 3.21 + 5.94 = **9.15 W** | 36.6 K | **62 C** | **does not close** |
| Vented, LED module inside | acceptance criterion, not a calculation | - | room + <= 15 K | `stackup.md` s6 |

That is C3's headline in one table, and it matches D-T2/D-T10: **the sealed box
caps total heat at ~5.0 W for 45 C internal air, and the emitters alone are
5.94 W.** The corollary is the useful one - **this board is not the problem; the
emitter module is.** Whatever the enclosure decision, this daughter contributes
under 1 W to the box.

**Per-package emitter thermal budget** at 150 mA/die (1.89 W electrical,
**1.42 W of heat**), red junction target <= 100 C:

| Internal air | Allowed junction-to-air | MCPCB path (19-23 K/W) | FR4 path (33-52 K/W) |
|---|---|---|---|
| 40 C (vented, per the acceptance criterion) | **42.3 K/W** | **closes, 1.8-2.2x** | straddles - closes only at the optimistic end |
| 45 C (D-T10 criterion) | **38.7 K/W** | closes, 1.7-2.0x | fails at the pessimistic end |
| 56 C (ICD s7.6 af) | **31.0 K/W** | closes, 1.3-1.6x | **fails** |
| 69 C (ICD s7.6 at - **disputed**, `decisions.md` OPEN-1) | 21.8 K/W | marginal | fails |

At `at` (250 mA/die, 2.36 W heat/package) the budget falls to **25.4 K/W** at 40 C
air and **18.6 K/W** at 56 C. **The at case is marginal on MCPCB at best and fails
against the ICD's own numbers.** That is the thermal blocker s5 refers to, and it
is independent of the rail choice.

Every emitter thermal figure rests on an **assumed** package Rth(j-solder) of
~12 K/W extrapolated from ams-OSRAM's published 8.9-12 K/W, because **no
XINGLIGHT datasheet in this family publishes a thermal resistance and the 4-in-1
publishes no maximum junction temperature at all.** If the real figure is 20 K/W,
even the MCPCB path is marginal at af. This is the largest single uncertainty in
the design and it is not recoverable before P5.

---

## 7. Branch B (`+48V_SW`) - the same tables, for the H1 comparison

Same driver family (TPS92515HV is a 65 V part), same four channels, same PWM,
gating and protection scheme. Differences: 4S series strings (no ballast, no
parallel matching), a hot-swap inrush limiter, a mandatory bleed path, 100 V
capacitors, 0805-minimum resistors across the 48 V domain, and the 0.635 mm
clearance regime extended from the J3 pads to the whole front end and VIN bus.

| | branch A (`+12V`) af | **branch B (`+48V_SW`) af** |
|---|---|---|
| String | 2S2P + 2x 1R5 ballast | 4S, no ballast |
| Die current | 150 mA | **175 mA** |
| Channel current | 300 mA | 175 mA |
| String voltage, worst | 5.03 / 7.03 V | 9.6 / 13.6 V |
| Emitter electrical | 7.56 W | **8.82 W** |
| Buck efficiency | 91 % | ~90 % (deeper step-down) |
| Rail draw | 8.62 W = **0.718 A** on `+12V` (ceiling 0.75) | 9.80 W = **0.204 A** on `+48V_SW` (ceiling 0.25) |
| Envelope | 8.64 W vs 8.6-9.3 W | 9.82 W vs 9.3-10.0 W (incl. the ICD s6.3 conversion bonus) |
| **Light, relative** | **1.00** | **~1.15** (16.7 % more current, ~14 % more flux after droop) |
| Emitter heat/package | 1.42 W | 1.65 W |
| Junction-to-air budget at 56 C | 31.0 K/W | **26.7 K/W - 15 % tighter** |
| Inductor for the same 30 % ripple at 700 kHz | **47 uH** | **265 uH** - 5.6x larger, because `Vin - Vs` is 34.4 V instead of 5.2 V at a lower setpoint current. A real board-area and cost difference |
| Converter edge budget `t_r + t_f = 1/(f*k)` | 4.76 us | **4.76 us - identical; the rail cancels out** (`decisions.md` D1) |
| Idle (shunted) channel | 0.20 W (60 V Schottky) | ~0.30 W (100 V Schottky, 0.7 V) |
| Standing loss, 4 idle channels | 0.80 W | 1.20 W |
| `at` reach | 250 mA/die, 72 % of the at emitter budget | **350 mA/die, full at** |
| Extra parts on this board | none | hot-swap P-FET + Cgd + gate network + bleed 0805 + 2x 10 uF/100 V (~6-9 parts, ~$0.60-0.90) |
| HV clearance regime | J3 pads only, satisfied by the 0.84 mm land pattern | front end + VIN bus, board-wide 0.635 mm in routing |

**Branch B buys ~15 % more light at af and the full `at` envelope. It costs the HV
regime in routing, an SOA-critical hot-swap FET, a mandatory bleed path, 0.4 W
more standing loss, a 15 % tighter emitter thermal budget, and it leaves D-02's
12 V rail with no consumer anywhere in the system.** The decision is
`decisions.md` D1 and it belongs to the human.

---

## 8. What this board does NOT do

- **No energy store.** No cap bank, no burst output - that is the strobe's
  problem. Total `+12V` capacitance is ~40 uF nameplate (~25 uF effective after
  ceramic DC-bias derating): decoupling, not storage. Well inside the 802.3
  ~180 uF PD port-capacitance ceiling, and it sits behind the carrier's converter
  rather than on the PD rail in any case.
- **No 48 V load on branch A**, therefore no bleed obligation (CAR-REQ-17 is
  conditioned on tapping), no 100 V capacitors, no hot-swap SOA analysis, and the
  0.635 mm regime is satisfied by the J3 land pattern's own 0.84 mm gap (1.32x).
- **No `+3V3` power path to anything but logic and sense** (D-02).
- **No path that energises anything from `+12V` or `+3V3` while `+48V_SW` is
  off** - carried by the ENABLE AND gate, since ENABLE is the same net that closes
  the carrier's 48 V switch. See `blocks.md` B1 for the residual asymmetry ICD
  rev A2 s8.4 exposes here.
