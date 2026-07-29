# lumina-par (LUM-PAR-A) - P2 decisions, conflicts resolved, and the H1 questions

Baselined on **ICD-01 rev A2**. This file is the H1 checkpoint record: what was
decided and why, which research fragment lost each conflict and on what grounds,
what the human answered, what must be requested from the carrier owner, and
one blocking issue raised against LUM-CAR-A.

**REVISION B - 2026-07-28, P2 delta after the H1 checkpoint.** H1 was approved
with four directed changes. This file now records them, supersedes what they
invalidate, and marks what is closed.

---

## 0. The four changes directed at H1, and what each one invalidated

| # | H1 question | Owner decision | What it superseded | Where it is re-derived |
|---|---|---|---|---|
| **Q1** | Enclosure | **SEALED, with the LED module's heat conducted through the wall.** Not vented. 3.21 W internal -> 38 C air was the figure that made it close | ENC-1..ENC-7 as written; the vented branch; D3's rationale (off-board becomes structural, not preferential) | `stackup.md` s5 (rewritten, ENC-8/9/10 added), `power_tree.md` s6.2 |
| **Q2** | Emitter | **RGB 3-in-1 + a separate WHITE discrete.** Chosen knowingly against this run's recommendation, on the grounds that its thermal case rests on a **published 125 C Tj max** and **3.5x stock depth** rather than on an **assumed 12 K/W Rth from a sole-source vendor that publishes neither Rth nor Tj max** | **D3's package identity and D4 in full.** Every row of `power_tree.md` s1-s6 | `power_tree.md` s1-s6 (rebuilt), D10 below |
| **Q3** | PAR-REQ-01 | **The strict reading binds: 5 % of PERCEIVED brightness, gamma 2.2.** Carrier firmware has committed to **PWM-domain dithering of >= 3-4 bits** | The "renegotiate PAR-REQ-01" option; CR-5's status from *request* to *commitment* | D12 below |
| **Q4** | Sourcing | **Same-reel sourcing. The 24C32 is fitted but ships EMPTY** - no measurement instrument exists today, so colour matching rests on same-reel binning. The EEPROM stays because it keeps the decision reversible | PAR-REQ-16 and PAR-REQ-17 as written (amended centrally by the orchestrator - `requirements.md` s0, AMD-01 / AMD-02) | D13 below |

**Q2 is not re-litigated anywhere in this package and P3 must not re-propose the
4-in-1.** The single most useful result of the re-derivation is recorded in
`power_tree.md` s3.1: **the two packages publish identical forward-voltage ranges,
so the electrical design point survived the change unchanged and not one net,
part or constraint on this daughter moved.** What did move is the module, the
optics and the thermal topology.

---

## 1. Decisions taken

### D1 - The LED stage runs from `+12V` (branch A). CONFIRMED AT H1 - NOT REOPENED.

**Status at revision B: CLOSED.** The `+12V` decision stands and the P2 delta was
explicitly instructed not to reopen it. The argument below is retained unchanged
as the record of how it was reached, and s7 of `power_tree.md` keeps the branch-B
comparison auditable. **Branch B is no longer a live option and P3/P4 must not
carry the DNP front end as a decision - it is a footprint-only hedge.**

**This was H1 question P1.** The project's standing instruction is `+12V`; D-02
created that rail specifically so 6-8 par fixtures need not each duplicate a
>= 60 V converter. Three research findings push the other way. Each is engaged on
its numbers rather than waved through.

**(a) "48 V gives ~16x the LED-current slew" (led-driver s0) - DEFEATED, and the
algebra says the rail cannot buy slew rate at all.**

The cited table holds the inductor **and** the string length fixed while changing
the rail, which is not a fair comparison: the inductor is not a free parameter,
it is set by the ripple the design will accept. Do it properly. For a buck with
input `Vin`, string `Vs`, duty `D = Vs/Vin`, setpoint `I`, switching frequency
`f`, and an accepted ripple fraction `k = dI/I`:

```
  ripple:  dI = (Vin - Vs) * D / (f * L) = k * I   ->   L = (Vin - Vs) * D / (f * k * I)
  rise:    t_r = L * I / (Vin - Vs)  =  D / (f * k)
  fall:    t_f = L * I / Vs          =  (1 - D) / (f * k)
  SUM:     t_r + t_f = 1 / (f * k)          <- Vin has cancelled out entirely
```

**At equal switching frequency and equal ripple fraction, the total converter edge
budget is `1/(f*k)` on either rail. The rail voltage cancels. It cannot buy slew
rate; only `f` and the accepted ripple can.** Worked for this design at
f = 700 kHz, k = 0.30:

| Rail | String | D | L for 30 % ripple | t_r | t_f | **t_r + t_f** |
|---|---|---|---|---|---|---|
| `+12V` | 2S GBW, 6.8 V, 300 mA | 0.567 | **47 uH** | 2.70 us | 2.06 us | **4.76 us** |
| `+48V_SW` | 4S GBW, 13.6 V, 175 mA | 0.283 | **265 uH** | 1.35 us | 3.41 us | **4.76 us** |

Identical, as the algebra requires - 48 V is 2x faster on the rise and 1.65x
slower on the fall, and it needs a **5.6x larger inductor** to get there. The
"16x" in led-driver s0 is entirely an artifact of reusing 47 uH across a 4x change
in `Vin - Vs`.

**And then the whole argument becomes moot anyway**, because D2 adopts shunt-FET
dimming: the converter never slews the LED current, the shunt FET does, in ~13 ns.
Note that 1/(f*k) = 4.76 us is **34x** the 141 ns requirement - reaching it by
gating the converter would need `f*k = 7.1e6` (e.g. 7 MHz at 100 % ripple), which
is why no rail choice and no inductor choice gets there and why the shunt FET is
not optional. **The single biggest stated advantage of the 48 V rail is arithmetic
that does not survive being redone, and it would not matter if it did.**

**(b) "A 4S G/B/W string is 12.4 V typ / 13.6 V max, above the +12V rail"
(led-emitter s4) - TRUE, and it costs less than it looks.**

Correct: a buck cannot make 13.6 V from 12 V, so the 12 V branch runs **2S2P**.
Costed properly:

| Item | Cost |
|---|---|
| Parts | 8x 1R5 ballast resistors, **on the LED module's MCPCB, not on this board** |
| Efficiency | 0.27 W of ballast dissipation = **3.2 % of the af envelope** |
| Matching risk | Two parallel 2-die InGaN branches. With a same-reel Vf spread of ~0.1-0.2 V and 1R5 ballast plus ~1-2 ohm of die dynamic resistance, branch imbalance is **<= 10-20 %**. Same-reel purchase (already mandated by C4) is the mitigation, and the ballast is the backstop |
| Uniformity | **A gain**: 2S2P for *all four* channels, red included, means one topology and one passive set across every channel - which is exactly what spec-dimming R8 demands (common-mode drift cancels in the colour ratio, differential drift does not). The 48 V branch's 4S red / 4S GBW is also uniform, so this is a wash rather than a win, but 2S2P is not the compromise it appears to be |

**(c) "Stuck-PWM is ~10.2 W = 0.85 A on `+12V`, over the 0.75 A ceiling"
(led-emitter s4) - TRUE at 175 mA/die, and the stated fix is taken.**

led-emitter offers two clean fixes: drop to ~150 mA/die, or move the load to
48 V. **This design takes the first.** At 150 mA/die the worst-case-Vf stuck-PWM
draw is **0.718 A - 4 % under the sustained ceiling and 2.8x under the 2.0 A OCP**
(`power_tree.md` s3). The board becomes electrically incapable of exceeding its
own budget, which requirements s3.3 demands and calls not optional.

**(d) ICD s6.3's 0.67 W (af) / 1.30 W (at) conversion bonus - TRUE, and it is the
real cost of branch A.** Combined with (c), branch B runs 175 mA/die against
branch A's 150: **16.7 % more current, ~14-15 % more light after droop.**

**What branch B costs**, against that ~15 %: the 0.635 mm clearance regime extends
from three connector pads into the front end and VIN bus; an SOA-critical hot-swap
FET (23 mJ at 56-72 C ambient, where SOA data is published at 25 C case); a
mandatory bleed path; 100 V capacitors and 0805-minimum resistors; a 100 V catch
Schottky whose higher Vf raises the standing shunt loss from 0.80 to 1.20 W; a
**15 % tighter** emitter thermal budget (26.7 vs 31.0 K/W at the ICD's 56 C); and
it leaves D-02's 12 V rail with no consumer anywhere in the system.

**What branch B buys beyond light: the full `at` envelope.** Branch A tops out at
250 mA/die = 72 % of the at emitter budget; branch B reaches 350 mA/die. But
`power_tree.md` s6 shows **the `at` case does not close thermally at either rail**
(25.4 K/W budget at 40 C air, 18.6 K/W at the ICD's 56 C, against a 19-23 K/W
MCPCB path). So branch B buys optionality on an upgrade that physics currently
blocks.

**RECOMMENDATION: branch A (`+12V`).** The strongest argument for 48 V dissolves
under the dimming topology; the remaining gain is ~15 % of light in a fixture
whose af output is already "a dark-room instrument"; the at path it protects is
thermally closed anyway; and choosing 48 V on the par - the 12 V rail's only
consumer - would make D-02 pointless system-wide.

**Both branches stay reachable, and the branch point is cheap if it lands at H1.**
Same driver family either way (TPS92515HV is a 65 V part), same gating, same
protection, same harness. Branch B is: populate 6-9 front-end footprints, change
4 sense resistors, change 4 TVS values, change 4 Schottkys to 100 V, and rewire
the module 2S2P -> 4S. **The one thing that is not a populate change is the
layout**: branch B needs the 0.635 mm regime across the driver VIN bus. **So the
decision must land at H1, before P5.** If the human wants to defer it past H1,
say so and the DNP front end plus a 48 V-rated VIN bus can be laid out on
branch A at a cost of ~9 footprints and the HV regime over the front end - but
that is a worse outcome than deciding now.

### D2 - Dimming: shunt FET per channel. The resolution wall is firmware and is not this board's to fix.

PAR-REQ-01 at 5 % of *perceived* brightness (gamma 2.2) has **two independent
walls**, and they need different answers.

**Wall 1, timing: `T = t_d(on) + t_r + t_d(off) + t_f <= 141 ns`** at
13-bit/9.766 kHz. **Closed by this board's hardware.**

- Direct PWM gating of the converter cannot do it. TPS92515HV's own datasheet
  works this exact case: *"if a 10 kHz PWM frequency is desired having a period of
  100 us, the minimum duty cycle is 200 ns/100 us = 0.2 %... 500:1 dimming"* -
  a **200 ns floor against a 141 ns requirement**.
- **A shunt FET across the string** decouples the dimming edge from the converter
  entirely. TPS92515HV specifies this mode: *"10,000:1 Shunt PWM Dimming Range"* =
  a **10.2 ns** minimum pulse at a 102.4 us period, 13.7x inside the requirement.
- Realistic T for the implemented circuit: 74LVC00 tPD 4.1 ns + FET gate transition
  (150 R into <= 3 nC) ~30 ns + string commutation through the harness
  (di/dt = V_string/L_loop = 6.8 V / 300 nH = 22.7 A/us, so 300 mA in **13 ns**)
  -> **T ~ 50-100 ns**. That clears 141 ns by **1.4-2.8x**. It does **not** clear
  spec-dimming's 3x-linearity margin (47 ns); the transfer function is
  *conducting* at the 5 % point, not provably *linear* there, and that is what the
  EEPROM's per-channel offset coefficient exists to absorb.
- Cost of the topology: the converter free-runs into the shunt FET, so a channel
  at 0 % still burns **0.20 W** - 0.8 W for four idle channels, ~10 % of the af
  envelope (`power_tree.md` s2). Mitigated by the optional converter-idle one-shot.
- Cost that must be verified, not assumed: while shunted, the converter regulates
  into a near-short, its duty collapses to ~0.5 % and it is driven to its minimum
  on-time, giving a 70 mA charge packet (23 % ripple) that appears in the LED for
  the first microseconds after the shunt opens. **TPS92515HV's dedicated
  shunted-output OFF-timer is the vendor's answer to exactly this, and it is the
  reason this part rather than a generic buck.** P3 must extract that behaviour
  from the datasheet; bring-up must measure it.

**Wall 2, resolution: 17 bits needed, LEDC gives 14. NOT closable on this board.**

At 13-bit/9.766 kHz, 5 % perceived is PWM code 11 of 8192; one code is an
**8.9 % luminance step = 8.9 JND** against a <= 1 JND requirement. **It fails by
8.9x.** 14-bit halves the error to 4.4x. The requirement needs 72 823 codes
(17 bits); **ESP32-S3 LEDC is capped at 14 bits in silicon.**

**The conflict two research fragments left standing, resolved: spec-dimming s2.7
rank 3 LOSES to led-driver s3.**

spec-dimming proposes *"a local >= 16-bit PWM generator IC with per-channel
current set"* as "an established product class". led-driver surveyed exactly that
class and found no part delivering >= 150 mA/ch **and** >= 10 kHz **and** useful
resolution **and** independent channels:

| Part | Fails on |
|---|---|
| TLC5947 | internal 4 MHz / 4096 = **~977 Hz** - 10x short on frequency |
| TLC59711 | 16-bit off a 7-12 MHz GS clock = **~150-180 Hz** - 50x short |
| PCA9685 | 12-bit, **24-1526 Hz** |
| IS31FL3236A | **8-bit**; 38 mA; 90 in stock |
| TLC5940 | needs a continuous external GSCLK the ICD does not carry; 12-bit at 30 MHz = 7.3 kHz max |
| LP5024 | best engine found (12-bit incl. 3-bit dither, 21-29 kHz) but outputs are **5.5 V abs-max linear sinks at 25-35 mA** - cannot drive any string here |

**A six-part survey against a general claim about a product class: the survey
wins.** The class-3 route is rejected, and with it the DSPI/I2C bus expansion, the
carrier firmware change to drive a serial port, and the "eight PWM lines then go
unused" divergence. LP5024 stays on file for one contingency only: if the carrier
ever withdraws its LEDC allocation. Note that even as a *PWM source* it buys
nothing - 12 bits at 29 kHz is worse than the carrier's 13 bits at 9.766 kHz, and
it does not touch the driver's own settling limit.

**So wall 2 is closed only by firmware**, and the fix is a package, not a menu:

| Fix | Owner | Effect |
|---|---|---|
| **PWM-domain temporal dithering, >= 3-4 bits** | **carrier firmware** | 14 + 4 = **18 effective bits**, clearing the 17-bit requirement. Must repeat >= ~300 Hz and must run in the PWM domain, **not** the 60 fps frame domain (a 4.4 % dither at 60 Hz breaches IEEE 1789's NOEL in its own right) |
| 14-bit at 4.883 kHz | **carrier owner** (LEDC timers 2/3, or reprogram timer 0) | one more bit, and doubles the on-time at the 5 % point from 141 to 281 ns - i.e. it buys **margin** over T, not LSB duration (the LSB is 12.5 ns at maximum resolution either way). Costs 2x camera band contrast |
| Shunt-FET dimming | **this board** | makes the dither physically reproducible: a 12.5 ns difference on a 141-281 ns fully-developed pulse is 4.5-9 % of charge, which T ~50-100 ns can render |

**Without firmware dithering, PAR-REQ-01 fails by 8.9x (13-bit) or 4.4x (14-bit)
and there is no hardware fix available on this board.** That is a named request
(CR-5), not an assumption.

Rejected outright, and why: **continuous analogue current dimming** and **thermal
foldback used as dimming** are banned by PAR-REQ-08 and the ban is correct
(dominant wavelength and phosphor CCT both shift with drive current). **Dual-rank
current switching** (spec-dimming rank 4) would buy 4 bits but needs per-fixture
characterisation of two chromaticities and explicit human sign-off; it is not
proposed. **Reducing the dies driven per channel** changes the emitter mix and is
rejected in spirit.

### D3 - The emitters are off-board on an aluminium MCPCB. AMENDED AT H1: now STRUCTURAL, not preferential; the package identity is SUPERSEDED by D10.

**Two amendments at revision B.**

**(i) The conclusion is strengthened by H1-Q1.** D3 was originally a thermal
preference with an on-board fallback. The selected enclosure conducts the emitter
heat **through the wall**, and an emitter soldered to this daughter cannot reach
the wall bridge at all. **The on-board fallback recorded below is therefore
dead** - it was already thermally marginal, and it is now incompatible with the
enclosure architecture. `stackup.md` s6 carries the consequence: OPEN-3 escalates,
because a strict reading of ICD s9 now reopens the *enclosure* decision, not just
the module design.

**(ii) The package identity below is SUPERSEDED by D10.** Wherever D3 says "each
package carries 1.42 W of heat" from a four-die 4-in-1, read D10's **1.035 W on
the RGB package and 0.383 W on the white**. The 33-52 K/W FR4 versus 19-23 K/W
MCPCB comparison is unaffected - it is a substrate property, not a package one -
and the conclusion is unchanged in direction and stronger in margin.

At 150 mA/die each package carried **1.42 W of heat** (pre-H1 figure). The FR4 path (package
~12 K/W + a 14-via array 5.4 K/W + in-plane spreading 10-25 K/W + interface +
heatsink) is **33-52 K/W** against a budget of 42.3 K/W at 40 C internal air and
**31.0 K/W at the ICD's own 56 C** - it straddles or fails. On an aluminium MCPCB
the path is **19-23 K/W** and closes with 1.3-2.2x margin (led-emitter s6,
[CREE-AP37] Table 6's measured 3.81 vs 9.39 degC/W board terms).

Two independent confirmations: [CREE-AP37] disclaims its own FR4 technique above
5 W per package, and D-T3 shows this board's own copper can shed 1-2 W total, not
7-8 W.

Consequences accepted: an internal wire-to-board harness (H1 question P4 - ICD s9
must be confirmed to permit it), a 10-way latched header, per-channel TVS clamps,
the emitter NTC and its two harness conductors, and the module's heat becoming an
*enclosure* problem rather than a PCB one - which is what makes the sealed branch
closable at all (`stackup.md` s5.1).

Fallback if ICD s9 is read strictly (no harness): on-board emitters on 14-via
arrays with an aluminium plate bolted across the board, clearing the antenna
column and the DC-DC hot zone. Cost: die current falls to **~115-160 mA** to close
on FR4, the emitters land wherever the keepouts allow rather than where the optics
want them, and this board's in-box heat rises from 0.8 W to ~6.7 W - which then
**fails ENC-1 in any sealed enclosure**.

### D4 - SUPERSEDED IN FULL BY D10.

> **Superseded text (revision A):** *"D4 - 150 mA/die, four packages, 2S2P per
> channel. Back-solved from the `+12V` 0.75 A sustained ceiling on the worst-case-Vf
> column. 145 mA/die is the alternative that also clears the ICD's 8.5 W total, at
> 3 % of light. This supersedes led-emitter's recommended 175 mA/die, which assumed
> the 48 V rail. Four packages rather than two is kept unchanged from led-emitter
> s1: same watts, 7 % more light (less droop), half the heat per thermal path, and
> four spatially separated already-mixed sources instead of two."*

**Why it is superseded rather than edited:** "four packages" no longer describes
the design (there are eight, in two families), and "four spatially separated
already-mixed sources" is precisely the property H1-Q2 traded away - each source
is now *either* colour *or* white, which is what makes PAR-REQ-15 live. The drive
current and the string topology survive, but they survive **because they were
re-derived**, not because they were carried forward. See D10.

### D5 - Two sensors, a window comparator, and NO thermal foldback

**A direct conflict between two research fragments, resolved in favour of
spec-dimming.** refdesign D-T16 ranks **analog thermal foldback into the driver's
current-set pin as protection layer 1** ("graceful, firmware-free, and it is the
layer that keeps the fixture lit"). spec-dimming R10 forbids it: *"thermal
foldback (a smooth current reduction) is also a PAR-REQ-08 problem independently:
it is analogue current dimming by another name and it shifts chromaticity"*, plus
an IEEE 1789 RP3 oscillation risk.

**spec-dimming wins, on the grounds that D-T16 is general-lighting reasoning
applied to a colour-matched fixture.** In a 6-8 fixture wash, one fixture silently
pulling its red channel's current down is worse than one that shuts down and
reports: it breaks PAR-REQ-06 (fixture-to-fixture consistency) invisibly, and
PAR-REQ-06 is this board's reason to exist. Under shunt dimming there is also no
IADJ modulation path to build foldback on without adding one.

**D-T16's intent is preserved, not deleted - it moves to firmware.** Both NTCs
reach the carrier on ADC0/ADC1, so firmware can roll *duty* back long before FAULT
asserts. Duty roll-back is chromaticity-safe (fixed current whenever conducting);
current roll-back is not. So: **layer 1 = firmware duty roll-off on measured
temperature; layer 2 = the hardware window comparator, firmware-independent, as
PAR-REQ-12 requires.**

Structure (`blocks.md` B4): one physical sensor per site; the emitter sensor feeds
a **window** detector (hot + open + short) because an open NTC or broken harness
wire **reads as cold in either divider orientation** and would silently disable
the protection (E-10); a second sensor on this board for the drivers, because the
module sensor says nothing about an inductor cooking inside the enclosure; one
quad open-drain comparator covers all four channels; wide hysteresis, never a
latch (ICD s8.2 forbids latching ENABLE locally; spec-dimming R10 forbids cycling
in 0.1-10 Hz).

### D6 - ENABLE gating: `/EN_OK = ENABLE AND FAULT`, `/SHUNTn = NOT(PWMn AND /EN_OK)`

One SN74LVC1G08 plus one 74LVC00A quad NAND covers all four channels, as the ICD
budget assumed. **A NAND, not an AND**, because the shunt FET is ON when the LED
is OFF. Full state table in `blocks.md` B2. 100 k pull-down on ENABLE at the
connector end; 100 k pull-downs on PWM0-3 so an undriven carrier cannot float a
gate input high; 100 k pull-downs on the shunt gates; combinational, never latched.

**How ICD rev A2 s8.4 changes this**, in both directions:

- It **simplifies branch B**: `+48V_SW` is hardware-guaranteed 0 V until firmware
  asserts ENABLE, so the hot-swap FET is gated purely from `/EN_OK` with no
  sequencing logic and no race against a live rail, and "48 V before or after
  3.3 V" becomes a mating-order concern only.
- It **exposes an asymmetry in branch A** that must be recorded: `+12V` comes from
  the carrier's always-on buck and is live whenever the fixture is powered,
  regardless of firmware. So ICD s8.3's rule - *"a daughter must not provide any
  path that energises its bank from `+12V` or `+3V3` while `+48V_SW` is off"* -
  is carried on branch A **entirely by the AND gate**, with no hardware rail
  interlock behind it. On branch B it is satisfied twice over.

### D7 - Fit both ID mechanisms; `ID_ADC`'s value is not chosen here

The premise "EEPROM *versus* divider" is not what the ICD says. **The divider says
what board type this is; the EEPROM stores per-unit calibration.** Both are fitted.
**R206's value is allocated by the carrier owner, not by this board** (ICD s3.3) -
CR-1, a P4 blocker. **24C32, not 24C02**: spec-dimming R12 needs per-channel gain
*and* offset plus ideally a bottom-decade LUT, and led-emitter s7 makes the whole
correction a function of measured temperature - a 2-D table. **No daughter-side
I2C pull-ups.** Address map recorded in `sheets.md` s2.

### D8 - No fifth (amber) channel on rev A

The PWM budget is free; the power budget is not. All four channels at 100 %
already draw 96 % of the `+12V` sustained ceiling, so a fifth channel takes ~20 %
from the other four in every mixed colour. If amber is later wanted, led-emitter
s8 **option B** is the right one: XL-HD6070YWC-A4-BD is Vf 2.8-3.4 V with a stated
CCT and CRI, i.e. **an InGaN blue die under a phosphor, not AlInGaP** - so
requirements Q4's thermal objection (-0.5 to -1 %/K) simply does not apply to it;
it behaves like the white channel at -0.1 to -0.2 %/K. Adding it is a respin.

### D9 - 4-layer, `JLC04161H-3313`; outline confirmed at 100.0 x 80.0 mm

Argued in `stackup.md` s1 and s2. Drivers: switch-node containment 11 mm above a
live 2.4 GHz antenna, a continuous GND reference under the jitter-sensitive PWM
lines, B.Cu consumed by two reverse-mounted THT sockets, and ~110-130 placements
in ~45 cm2 of usable area. **Not impedance** - no controlled-impedance net exists.

---

## 1b. Decisions added at the P2 delta (revision B)

### D10 - SUPERSEDES D4. The emitter set is 4x RGB 3-in-1 + 4x white discrete, 2S2P per channel at 150 mA/die.

**Directed by H1-Q2.** Both part numbers were re-verified live with
`parts_search.py` in this session; **no LCSC code in this package is quoted from
memory**.

| Role | MPN | LCSC | Stock | $ (break used) | Published Tj max | Published Rth |
|---|---|---|---|---|---|---|
| RGB | XINGLIGHT **XL-HD6070RGBC-A46L-BD** | **C22434861** | **6461** | $0.3724 @30 | **125 C** | **NOT PUBLISHED** |
| White | XINGLIGHT **XL-HD6070UWC-A4-BD** | **C48586656** | **1790** | $0.2332 @50 | **120 C** | **NOT PUBLISHED** |

**The white was selected by this run, not handed down.** The requirement was the
same 6070/5050-class body with a published Tj or Rth. `C48586656` is the same
HD6070 body as the RGB package (so it shares the land-pattern scale, the 5.15 mm
height and the mechanical stack), publishes **Tj 120 C**, matches the withdrawn
4-in-1's white on CCT (6000-6500 K) and on Vf (2.8-3.4 V), and holds 1790 in stock
against a need of 32 + spares. The alternatives considered and why they lose:

| Alternative | Live-verified | Why it loses |
|---|---|---|
| ams-OSRAM **GW PUSRA1.EM-N2N7-XX52-1-700-R33** | **C17664282, 395 stock, $0.8786** | The **only** in-stock white with a published Rth, but a **1515** body: different land pattern, different height, 120 deg from a 1.5 mm die instead of a 6 x 7 mm lamp area, and the whole `stackup.md` s5.2 geometry would need re-deriving. **Retained as the fallback if the XINGLIGHT white's unpublished Rth turns out to be the problem** |
| XINGLIGHT **XL-HD6070WWC-A4-BD** | C48586655, 1738 stock, $0.2894 | Warm white 2900-3100 K. Wrong CCT - the withdrawn part and SYS-REQ-07 both target a cool white |
| XINGLIGHT **XL-HD2525UWC-A2** | C3646945, 4530 stock, $0.1679 | Better ambient rating (+105 C) but a **~2 mm2** thermal pad against the 6070's ~28 mm2, and a body that does not match the RGB package at all |
| Cree **XPGBWT-L1-0000-00H51** | C17401863, 1060 stock, $3.2404 | 10x the price, 3535 body, white only. Kept on file as the reference point P1 recorded |

**Arrangement, re-derived rather than inherited** (`power_tree.md` s1.2): the
published Vf ranges force **2S** on `+12V` (4S G/B/W is 13.6 V, above the rail;
3S leaves 1.8 V before ballast and sense resistor). Given 2S, the die count is a
free choice, and **2S2P at 4 dies per channel wins on PAR-REQ-15**, not on
electricals - it is the only count that permits a **centroid-matched checkerboard**
(`stackup.md` s5.2.2). 150 mA/die -> 300 mA/channel -> **0.717 A on `+12V`**.

**The finding that matters most: the electrical design point is unchanged.** Both
packages publish **identical Vf ranges** (R 1.8-2.4 V, G/B/W 2.8-3.4 V,
live-verified), so string voltage, channel current, every row of the
sustained-power table, the driver count, the sense resistor, the harness rating
and `constraints.json` `power[]` all land exactly where they were.
**`power_tree.md` s3.1 states this explicitly so nobody mistakes it for a
copy-forward.**

**H1-P7 (145 vs 150 mA/die) was reopened and is re-derived in `power_tree.md`
s3.3. Recommendation: 150 mA/die, unchanged.** Every genuine *hardware* fault
ceiling passes at both currents and none is close (2.0 A `+12V` OCP: 2.8x; PD's
0.85 A **minimum** limit: 3.4x). The only figure 150 fails is the ICD's 8.5 W
total, which ICD s6.2 itself calls a **firmware-governed average**, not a trip.
The 3.3 % of light 145 mA/die costs now matters *more* than it did before H1,
because D14's mandatory diffuser removes a further 30-45 % of the flux from a
fixture already described as "a dark-room instrument".

### D11 - SUPERSEDES the ENC-1..ENC-7 set. Sealed enclosure, LED heat through the wall, and the wall path is a measured criterion.

**Directed by H1-Q1.** Rewritten in `stackup.md` s5 against this specific
configuration; the vented branch is withdrawn.

The load-bearing addition is **ENC-8: the conduction path from the LED module's
mounting face to ROOM air shall present <= 8.0 K/W, measured** - a <= 45.4 K rise
at 5.67 W, i.e. the mounting face at <= room + 46 K - with a full test method in
`stackup.md` s5.0 (thermocouple positions, drive condition, settling criterion,
pass thresholds, and what to do on failure). **ENC-5 restates the same physics as
a single number a builder can check: the module's thermocouple pad shall not
exceed room ambient + 50 K.**

**Why it may not be phrased as an assumption.** If the bridge does not work, the
fixture does not fail loudly - it silently reverts to sealed-with-the-module-inside,
which H1-Q1 rejected: in-box heat goes from 3.19 W to **8.86 W**, internal air
from 36.5-38.7 C to **56.9-63.1 C** in a 25 C room, and the daughter's own parts
then live in air 12-18 K over ENC-1 (`power_tree.md` s6.2). **ENC-8 is what stands
between the selected architecture and the rejected one.**

**The corresponding gain, stated because it is large:** under wall conduction the
emitters are cooled to *room* air, not to internal air, so **the emitter thermal
case is decoupled from the disputed ICD s7.6 figure** (`power_tree.md` s6.4). Red
Tj lands at **76.2 C** (25 C room) / **91.2 C** (40 C room) against a 100 C target
and a **published** 125 C maximum, and moves by only ~3 K even if the internal air
turns out to be 85-90 C. What still breaks at 85-90 C is the emitters' **+85 C
Topr ambient rating**, which no module design can fix - so **CR-6 remains
blocking**.

### D12 - PAR-REQ-01 is MET, by hardware PLUS a NAMED firmware dependency.

**Directed by H1-Q3: the strict reading binds - 5 % of PERCEIVED brightness,
gamma 2.2 - and carrier firmware has committed to PWM-domain dithering of
>= 3-4 bits.**

**Status: PAR-REQ-01 MET.** The two walls and who closes each:

| Wall | Requirement | Closed by | Margin |
|---|---|---|---|
| **Timing** | `T = t_d(on) + t_r + t_d(off) + t_f <= 141 ns` at 13-bit / 9.766 kHz | **THIS BOARD'S HARDWARE** - the shunt FET across each string (D2). Realistic T ~ 50-100 ns | **1.4-2.8x** |
| **Resolution** | 17 bits (72 823 codes) for <= 1 JND at the 5 % point; ESP32-S3 LEDC caps at 14 | **CARRIER FIRMWARE** - PWM-domain temporal dithering, >= 3-4 bits -> 17-18 effective bits | requirement met at >= 3 bits |

**The shunt-FET hardware half stands exactly as designed. Nothing in D2, B2, B3 or
`sheets.md` changes.**

**THE FIRMWARE DEPENDENCY, NAMED SO IT CANNOT BE SILENTLY DROPPED.** Carrier
firmware **shall** implement temporal dithering with all three properties:

1. **>= 3-4 bits of dither.** Without it PAR-REQ-01 **fails by 8.9x at 13-bit and
   4.4x at 14-bit**, and one PWM code is an 8.9 % luminance step against a <= 1 JND
   requirement.
2. **In the PWM domain, NOT the 60 fps frame domain.** A 4.4 % dither at 60 Hz is
   itself an IEEE 1789 NOEL breach - a frame-domain implementation trades one
   failure for another.
3. **Pattern repeat >= ~300 Hz.**

**There is no hardware remedy available on this board if the commitment lapses.**
D2's six-part survey already established that no PWM-engine driver IC in the class
delivers >= 150 mA/ch **and** >= 10 kHz **and** useful resolution **and**
independent channels, and even LP5024 as a bare PWM source is worse than the
carrier's own 13 bits at 9.766 kHz. **If the dither is dropped, PAR-REQ-01 must be
formally renegotiated (the CIE L* reading buys a 4x relaxation), not quietly
failed.** CR-5 accordingly changes from a *request* to a *tracked commitment* -
see s4.

### D13 - Same-reel sourcing; the 24C32 is fitted and ships EMPTY.

**Directed by H1-Q4**, and formalised centrally in `requirements.md` s0 (AMD-01
amends PAR-REQ-16 to a same-reel sourcing requirement; AMD-02 defers PAR-REQ-17's
*data*, not its hardware). **This board's hardware is unchanged: D7 stands in
full** - both ID mechanisms fitted, 24C32 at 0x50, WP to GND, no daughter-side I2C
pull-ups, R206's value still allocated by the carrier owner (OPEN-2).

Three consequences this run must carry:

1. **Buy all 8 fixtures' emitters plus spares in ONE TRANSACTION PER PART NUMBER
   before P5, and record both reel/lot codes on the build sheet.** There are now
   two reels, not one.
2. **Same-reel matching is now load-bearing for OPTICS as well as colour.**
   `stackup.md` s5.2.2's PAR-REQ-15 arrangement holds its 0.8 mm centroid
   tolerance only with **+/-5 % flux matching within each family**. If the
   same-reel purchase is not honoured, the fringing mitigation stops working -
   not just the fixture-to-fixture match. **This is a new coupling created by
   H1-Q2 and it did not exist before.**
3. **The two-reel white/colour ratio is a GLOBAL constant, not a per-fixture
   error.** RGB and white come from different reels so their relative flux is
   uncontrolled - but provided all 8 fixtures draw from the same two reels, every
   fixture inherits the *same* offset. PAR-REQ-06 is preserved and the offset
   becomes **one firmware constant**, which is exactly what an empty EEPROM can
   still accommodate. **The EEPROM stays fitted because it keeps the decision
   reversible at zero cost** (one SOIC-8 and two resistors) once an instrument
   exists.

### D14 - PAR-REQ-15 has a buildable specification: centroid-matched arrangement + a specified diffuser + a stated minimum throw.

**Created by H1-Q2**, which traded away the one property the integrated 4-in-1
gave for free: every colour leaving the same 6.2 mm slug. The full specification
with all arithmetic is **`stackup.md` s5.2**; the summary and the reason each
piece exists:

| Piece | Specification | Which failure mode it kills |
|---|---|---|
| **Arrangement** | 3 x 3 grid, **16.0 mm pitch** (the minimum the 14.5 mm land span allows), **RGB on the four corners, white on the four edge midpoints, centre vacant**. RGB centroid (16, 16); white centroid (16, 16) - **they coincide exactly** | **Shadow fringing (the mechanism PAR-REQ-15 names).** Removes the colour dipole entirely. Tolerance: residual centroid separation **<= 0.8 mm**, budgeted as 0.30 placement + 0.20 white flux + 0.28 RGB flux |
| **Diffuser** | Stand-off **>= 15 mm, 20 nominal**; aperture **>= 115 mm**; **Option A opal, haze >= 92 %, TT 55-70 %** (recommended) or **Option B LSD, >= 80 deg FWHM, TT 85-90 %** at `d >= 25 mm` | The residual 16 mm quadrupole, **and** the beam-angle mismatch below. Derived from a **>= 60 % patch-overlap** criterion on the *narrower* beam |
| **Minimum throw** | **1.5 m** from diffuser to any illuminated surface; no occluder within 0.5 m | The direct-wash colour gradient only. **1.46 m is the arrangement-FAILED case**; with the arrangement working the required throw is 0.07 m |
| **Bench test** | Test C centroid check with a ruler before power; Test A shadow photograph at 0.5 / 1.0 m; Test B on-axis vs 45 deg chromaticity, both **<= 0.010 u'v'** | acceptance |

**Three findings inside this that a reviewer should not miss.**

1. **The beam angles do not match, and it is live-verified, not inferred.** LCSC
   lists the RGB 3-in-1 at **140 deg** and the white at **120 deg**. Cross-checked
   this session against three siblings: the blue (C48586653) and red (C48586650)
   singles are 140 deg, and the *warm white* (C48586655) is also 120 deg - so the
   split is **white-versus-colour inside the family**, not one bad record, and
   P1's family-level "6070 = 140 deg" claim is wrong for the white parts. Fitting
   `cos^m`, white is Lambertian (m = 1.000) and RGB is broader (m = 0.646), so
   the mix is **-5.0 % white at 30 deg, -11.5 % at 45 deg, -33.5 % at 71.6 deg** -
   which is a wall 3 m away at 1.5 m height, squarely inside the PAR-REQ-14 wash.
   **The arrangement cannot fix this and firmware cannot fix this** (it is
   angle-dependent, not a scalar). Only a strong diffuser can, which is the
   second independent reason Option A is the safe specification. **P3 must
   confirm both angles from the datasheets.**
2. **Throw distance does not fix shadow fringing.** A shadow edge is a projected
   *image* of the source, so the fringe scales with the source's colour structure
   and the occluder geometry, not with `1/D`. The naive "make the sources
   angularly unresolvable from the wall" criterion gives **D >= 27.5 m** - absurd,
   and it is exactly the point: **the diffuser, not the throw, is the fix for
   shadows.** The throw number governs the direct wash only.
3. **The diffuser costs 30-45 % of the fixture's flux and was in no budget.**
   Against `research/led-emitter.md` s5's own ~41 lx baseline, Option A gives
   ~25 lx and Option B ~36 lx, in a fixture that document already called "a
   dark-room instrument, not room lighting". Budget **$2-5/fixture** for the panel
   and frame (`stackup.md` s7). **This is the largest hidden cost of H1-Q2.**

**Honesty statement, repeated here because it belongs in the decision record: this
is a PCB pipeline and it cannot verify a beam. Every number in D14 and in
`stackup.md` s5.2 is a design target with a stated bench test, not a verified
optical result.**

---

## 2. Rejected, with the reason (so P3 cannot re-propose them)

| Rejected | Reason |
|---|---|
| **The integrated RGBW 4-in-1, XL-HD6070RGBW-A5 / XL-HD6070RGBCW-A5, `C53153006`** | **WITHDRAWN BY OWNER DECISION AT H1-Q2.** Its thermal case rested on an **assumed 12 K/W Rth from a sole-source vendor that publishes neither Rth nor Tj max**; the selected RGB 3-in-1 publishes **Tj 125 C**, carries **3.5x the stock** and is JLC **SMT-assemblable** where the 4-in-1 is flagged "Wave Soldering". **Do not re-propose it at P3.** D10 |
| **Ventilating the enclosure** | Withdrawn at H1-Q1 in favour of sealed + wall conduction. `stackup.md` ENC-2 |
| **On-board emitters (the old D3 fallback)** | Was already thermally marginal on FR4 (33-52 K/W vs a 42.3 K/W budget); **H1-Q1 killed it outright** - an emitter on this daughter cannot reach the enclosure wall bridge. `stackup.md` s6 |
| **Renegotiating PAR-REQ-01 to a looser reading (5 % of duty, or CIE L*)** | H1-Q3 selected the **strict gamma-2.2** reading and the carrier committed to the dither. D12. The CIE L* relaxation is retained only as the fallback **if** the firmware commitment lapses |
| **2 white emitters instead of 4** (electrically identical: same string voltage, same channel current, same power) | Halves the white sources and destroys the centroid-matched checkerboard, which is the primary PAR-REQ-15 mitigation. `power_tree.md` s1.2 step 2 |
| Linear / LDO constant-current sinks as the primary topology | 11.8-14.0 W of dissipation for 1-die strings from 12 V - **over 100 % of the af envelope**. Even tuned string lengths spend 20-53 % of the budget as heat next to a red die that wants 85-100 C. Independently, TPS92638-Q1-class parts have T ~ 73 us, failing the timing spec by ~520x |
| Multi-channel PWM-engine driver ICs (TLC5947/59711, PCA9685, IS31FL3236A, TLC5940, LP5024) | s1 D2 - no part in the class delivers >= 150 mA/ch AND >= 10 kHz AND useful resolution AND independent channels |
| SN3350IP05E-01 | EC table: dimming ratio **1200:1 at 100 Hz but 13:1 at 10 kHz** = ~3.7 bits |
| AL8861/AL8860/AL8862, ZXLD1362, AL5809, AL5812, CAT4104 | "<500 Hz" application guidance / 100 us built-in soft-start / analogue-dimming behaviour above 300 Hz / 100-200 Hz / no PWM timing spec at all / one shared EN for four channels |
| HV9910B | datasheet: PWMD accepts *"a frequency of up to a few kilohertz"* - below 9.766 kHz on the vendor's own wording |
| AL8863SP-13 **on branch B** | 60 V operating / 65 V abs-max against a 57 V rail = 5 % margin, plus a self-contradicting datasheet. **Retained as the branch-A cost-down** (2.7x cheaper), with a bench-verification item |
| An output capacitor across any LED string | The shunt FET dumps it every PWM cycle: 1 uF at 6.8 V and 9.766 kHz is 0.23 W/channel |
| An RC filter on the PWM/DIM path | The reflex 1 k + 100 pF is tau = 100 ns and would swallow the 141 ns pulse. If any network is fitted, tau <= 14 ns |
| A MOV-to-earth surge network | ICD s9: an unearthed PD needs none and there is no earth to connect it to |
| Daughter-side I2C pull-ups | Carrier fits 4.7 k; a second pair is an ICD violation |
| 2 oz copper | Buys ~2 % (inside measurement noise) when the path is a via farm into a heatsink, and this board sheds 0.8 W over 80 cm2 anyway |
| 0.254 mm / 0.635 mm Cree via arrays on **this** board | That is the spec for a 5 W LED package and it escalates the JLC drill class. The parts needing arrays here are 0.15-0.20 W driver ICs. Reserve the Cree spec for the module's MCPCB |
| Trace-length matching between PWM0-3 | A common or differential propagation delay shifts pulse *phase*, not *width*, and duty is what sets flux. **Edge jitter** is the real routing constraint (1.4 ns = 1 % flux error at 141 ns) |

---

## 3. Questions for the HUMAN - STATUS AFTER H1

**H1 was approved with four directed changes.** This table now shows what is
closed and what still needs an answer. **Six of the thirteen are closed; one
(P7) was explicitly reopened and is re-derived; six remain open.**

| # | Status after H1 | Answer / where it now lives |
|---|---|---|
| **P1** rail | **CLOSED - branch A (`+12V`)** | Confirmed and explicitly not reopened at the P2 delta. D1 (amended). Branch B is a footprint-only hedge, not a live option |
| **P2** PAR-REQ-01 reading | **CLOSED - strict gamma 2.2** | H1-Q3. **PAR-REQ-01 recorded MET** by hardware + a named firmware dependency. D12 |
| **P3** enclosure | **CLOSED - sealed, LED heat through the wall** | H1-Q1. ENC-1..ENC-10 rewritten against this configuration; **ENC-8 is the new measured criterion**. D11, `stackup.md` s5 |
| **P4** ICD s9 / internal harness | **STILL OPEN, and now MORE urgent** | H1-Q1 made the off-board module structural, so the fallback is dead. A strict "no" now reopens the enclosure decision, not just the module. OPEN-3 |
| **P5** heatsink compliance | **CLOSED BY IMPLICATION - shrouded through the wall** | This is what H1-Q1's wall-conduction branch *is*. **Confirm the shroud explicitly**: ENC-3 is strictly harder now, because the architecture deliberately puts metal through the wall |
| **P6** firmware dithering | **CLOSED - YES, committed** | H1-Q3. Recorded as a tracked commitment in CR-5 and named in full in D12 |
| **P7** 150 or 145 mA/die | **REOPENED AT H1 - re-derived, recommendation 150** | `power_tree.md` s3.3. Every hardware fault ceiling passes at both; the only figure 150 fails is a firmware-governed average. **Still a sense-resistor value, decidable as late as P3** |
| **P8** converter-idle one-shot | **STILL OPEN** | Unchanged: saves 0.8 W (9 % of the envelope) at saturated colours for ~$0.30 and 12 passives. Recommendation: **yes**, laid out as a populate option either way |
| **P9** 240 fps capture in scope | **STILL OPEN** | Unchanged. Recommendation: declare 240 fps out of scope, which frees CR-3 to be taken purely on dimming margin |
| **P10** calibration instrument | **CLOSED - none exists** | H1-Q4. EEPROM fitted, ships empty (AMD-02). Colour matching rests on same-reel binning. D13 |
| **P11** emitter single-source risk | **CLOSED - the fallback was taken** | H1-Q2 selected the RGB 3-in-1 + separate white **over** this run's recommendation. D10. Still single-vendor (both parts XINGLIGHT); the ams-OSRAM 1515 white (C17664282, 395 stock) is the only published-Rth escape and is a body change |
| **P12** build quantity / BOM target | **STILL OPEN** | Revised: this board still **$18-23**, but the module rises to **$12-21/fixture** (8 packages + a diffuser that was in no budget), so **par fixture ~$30-44, x8 = $240-352**. `stackup.md` s7 |
| **P13** outline confirmation | **STILL OPEN** | Unchanged: 100.0 x 80.0 mm, R3.0, 5x M3, 30 x 26 mm notch at (6,0)-(36,26). ai-ee has no outline-shrink step, so the P5 outline is permanent. **New adjacent question: the enclosure must now accommodate a ~29-30 mm module stack plus an external heatsink** (ENC-10) |

### 3.1 The original question set, retained verbatim for the record

Each states the option, the number, the consequence and the recommendation as it
stood at H1. **Read s3 above for current status; nothing below is live.**

| # | Question | Options and numbers | Recommendation |
|---|---|---|---|
| **P1** | **Which rail feeds the LED stage?** | **A `+12V`**: 150 mA/die, 0.718 A / 96 % of ceiling, no HV regime in routing, 0.80 W standing loss, reaches 72 % of `at`. **B `+48V_SW`**: 175 mA/die, **~15 % more light**, full `at` reach, but the 0.635 mm regime across the VIN bus, an SOA-critical hot-swap FET, a mandatory bleed, 1.20 W standing loss, a 15 % tighter emitter thermal budget, and D-02's 12 V rail then has no consumer anywhere | **A.** Must land at H1, before P5 - the layout differs even though the parts do not |
| **P2** | **Which reading of "5-10 % of full output" binds (PAR-REQ-01)?** | 5 % of **duty**: T <= 5.12 us, routine. 5 % **perceived, gamma 2.2**: T <= 141 ns, met by shunt dimming with 1.4-2.8x margin but needing firmware dither for the resolution half. **CIE L***: T <= 567 ns and the resolution deficit falls 4x - a free 4x relaxation | **Gamma 2.2 (strict).** Ask explicitly whether CIE L* is acceptable: it costs nothing in hardware and is the cheapest relief available, but the L* toe is a numerical convenience, not a perceptual claim, so adopting it is a deliberate loosening |
| **P3** | **Enclosure: sealed, vented, or wall-conducted?** | **Sealed with the module inside: 9.15 W in a 4.0 K/W box = 62 C internal air. Fails ENC-1 by 17 K and must not be selected.** Vented (within 15 K of room): closes. Sealed with the LED heat conducted through the wall: **3.21 W = 38 C**, closes with margin | **Vented, or sealed-with-wall-conduction.** No ingress requirement is stated anywhere for an indoor basement/garage install, so convection is close to free |
| **P4** | **Does ICD s9 permit an internal LED harness?** (requirements Q5) | s9 bans "an external connector of any kind" but itself anticipates the off-board case ("if the LED module is on a separate heatsink... that heatsink and its wiring are at PoE potential too"). A harness that never leaves the enclosure is not an external connector on any reasonable reading - **but this needs confirming, not assuming**. A strict no forces on-board emitters, drops die current to ~115-160 mA and raises this board's in-box heat from 0.8 W to ~6.7 W | **Yes - confirm explicitly.** This is the single answer that most changes the board |
| **P5** | **Heatsink compliance** (requirements Q7) | Internal-only (thermally worst), shrouded-through-wall (works, needs a plastic guard), exposed metal (**breaks the non-isolated compliance argument**) | **Shrouded through the wall**, ceiling mount non-conductive and bonded to nothing, module substrate **thermally coupled but electrically floating** from board GND (dielectric pad, insulating shoulder washers) |
| **P6** | **Will firmware implement PWM-domain dithering?** | Without it **PAR-REQ-01 fails by 8.9x at 13-bit / 4.4x at 14-bit, and no hardware on this board can fix it.** With >= 3-4 bits of dither: 17-18 effective bits, requirement met | **Commit to it now**, before the schematic assumes PAR-REQ-01 is satisfiable. If the answer is no, PAR-REQ-01 must be renegotiated instead (P2 above) |
| **P7** | **150 or 145 mA/die?** | 150: 8.64 W, 0.718 A, 96 % of the per-rail ceiling but **1.6 % above the ICD's 8.5 W firmware-governed total** at worst-case Vf. 145: 8.33 W, 0.692 A, under both, **3 % less light** | **150**, with firmware's PAR-REQ-11 governor covering the total. It is a sense-resistor value and can move as late as P3 |
| **P8** | **Populate the converter-idle one-shot?** | Saves **0.8 W (10 % of the envelope)** whenever channels are fully off - the normal state of a saturated-colour wash. Costs one 74LVC14 + 12 passives, ~$0.30, and a bench item | **Yes.** Laid out as a populate option either way |
| **P9** | **Is 240 fps slow-motion capture in scope?** | At 9.766 kHz band contrast is 2.46 % at 240 fps (marginal); at 4.883 kHz it is 4.92 % (visible). 60 and 120 fps are clean at both. **960 fps is unreachable at any usable LEDC setting and should be declared out of scope** | Declare 240 fps **out of scope**, which frees the 4.883 kHz request (CR-3) to be taken purely on dimming margin |
| **P10** | **What instrument measures 6-8 fixtures for calibration?** (requirements Q10) | Colorimeter / spectrometer / phone-camera comparison / nothing. If nothing, the EEPROM ships empty, **the per-channel offset coefficients cannot be populated**, and colour matching falls back entirely on same-reel binning | Answer before P9. The hardware is fitted regardless; this decides whether it is usable |
| **P11** | **Accept the emitter single-source risk?** (C4, s5 OPEN-4) | One vendor, one MPN, 1819 in stock, **no published Rth and no published Tj max**, Topr max +85 C against a disputed 69 C internal air. Fallback: RGB 3-in-1 + separate white - 3.5x the stock, published 125 C Tj, JLC-SMT-assemblable, at the cost of PAR-REQ-15 white fringing and a diffuser | **Accept, and buy all 8 fixtures' emitters plus spares in one transaction before P5.** The risk is contained because the four driver channels are colour-agnostic - an emitter change is a module change, not a daughter respin |
| **P12** | **Confirm build quantity and BOM target** | 8 boards (6-8 deployed + spares). This board estimates **$18-23** delivered against the suggested $25-35 excluding module and heatsink; module + heatsink adds $8-14/fixture; **par fixtures total ~$210-300 of a $500-1000 system budget** that must also cover carriers, strobes, enclosures and a PoE+ switch | Confirm 8 and the $25-35 target. Flag the system budget as tight - that is a project-level issue, not this board's |
| **P13** | **Confirm the outline: 100.0 x 80.0 mm, R3.0, 5x M3, 30 x 26 mm notch at (6,0)-(36,26)** | ai-ee has **no outline-shrink step** - the P5 outline is permanent (MECH-02) | **Confirm as-is.** Also state whether the enclosure has any dimension this footprint must fit inside that has not yet been stated |

---

## 4. Requests to the CARRIER OWNER (LUM-CAR-A)

None of these may be assumed. Each carries the cost of not making it.

| # | Request | Cost of not making it |
|---|---|---|
| **CR-1** | **Allocate the `ID_ADC` board-type code for LUM-PAR-A** and publish the bottom-leg resistor value | **Blocks P4.** R206 cannot be placed. Picking a value here is exactly the silent divergence ICD-01's preamble forbids |
| **CR-2** | **Re-issue ICD s7.2 with the confirmed J3/J4/H5 coordinates after the carrier's P6** | **Blocks P5.** s7.2 is the one un-frozen section and daughters are explicitly blocked on it. This run proceeds through P4 and holds |
| **CR-3** | **Make 14-bit at 4.883 kHz available** (LEDC timers 2/3, or reprogram timer 0), selectable in firmware, with 13-bit/9.766 kHz kept as the default | Driver timing margin over T stays at 1.4-2.8x instead of 2.8-5.6x, and the dither operating point sits nearer the pulse-development knee. **Not a blocker** - shunt dimming clears 141 ns without it - but it is the cheapest margin available. Cost of granting it: 2x camera band contrast (see H1-P9) |
| **CR-4** | **90-degree `hpoint` phase stagger across PWM0-3** | Up to **4x** larger worst-case input-current step on `+12V`, more bulk capacitance, and a worse peak against the 0.75 A ceiling. Costs the carrier nothing - PWM0-3 share timer 0, so hpoint = 0, N/4, N/2, 3N/4 changes neither frequency nor duty |
| **CR-5** | **GRANTED AT H1-Q3, now a TRACKED COMMITMENT rather than a request.** Carrier firmware shall implement PWM-domain temporal dithering, **>= 3-4 bits**, pattern repeat **>= 300 Hz**, **in the PWM domain and NOT the 60 fps frame domain** | **PAR-REQ-01 is recorded MET on the strength of this commitment.** If it lapses the requirement fails by **4.4-8.9x** with **no hardware remedy on this board**, and it must then be formally renegotiated (the CIE L* reading is the fallback), not quietly failed. A frame-domain implementation is not a partial win - a 4.4 % dither at 60 Hz breaches IEEE 1789's NOEL on its own. **D12 names all three properties; verify them at integration, not by assertion** |
| **CR-6** | **STILL BLOCKING - see s5 OPEN-1.** Re-derive and re-issue ICD s7.6's internal-air figures, with an explicit room-ambient assumption | **Downgraded in scope but not closed.** H1-Q1's wall conduction decoupled the *emitter junctions* from this figure (`power_tree.md` s6.4: red Tj moves ~3 K between 38 C and 90 C internal air). **What is still keyed to it is the emitters' +85 C Topr AMBIENT rating**, which no module design can fix, plus this daughter's own component ratings (ENC-1b) |

---

## 5. OPEN

### OPEN-1 (BLOCKING ISSUE against LUM-CAR-A, raised under ICD s10)

**ICD s7.6's internal-air temperatures are internally inconsistent and
optimistic. A daughter may not absorb this.**

1. **The 69 C (at) figure contradicts the ICD's own 56 C (af) figure.** Convection
   is close to linear in delta-T at this scale, so roughly doubling the box heat
   must roughly double the rise. The ICD's own af point (31 K rise at ~9.9 W)
   scaled to the at point (~19.2 W) gives a **60 K rise, i.e. ~85 C, not 69 C**.
2. **An independent calculation is worse.** A sealed 120 x 100 x 60 mm non-metallic
   box is 3.6-4.3 degC/W (Hoffman 4.34 / Rittal 3.61, bracketing). At the at heat
   load that gives **89-115 C internal air in a 25 C room**. The ICD's at figure is
   **optimistic by 20-46 K**.
3. **The 56 C (af) figure survives only at a 25 C room.** At the requirements
   document's own ASSUMED 40 C external ambient it becomes **72-87 C**. The ICD
   states no room-ambient assumption.
4. **Direct consequence for this daughter, RESTATED AT REVISION B.** Two things
   changed the shape of this item without closing it:
   - **H1-Q2 fixed half of it.** Both selected parts now publish a maximum
     junction temperature (**RGB 125 C, white 120 C**), where the withdrawn 4-in-1
     published none. There is an absolute limit to check against for the first
     time.
   - **H1-Q1 fixed most of the rest.** Under wall conduction the emitters are
     cooled to *room* air, not internal air, so **red Tj moves by only ~3 K
     between a 38 C and a 90 C internal-air figure** (`power_tree.md` s6.4). The
     emitter thermal budgets are no longer keyed to the disputed number.
   - **What is NOT fixed, and it is why this stays blocking:** both parts are
     live-verified at **Topr -40 to +85 C**. At 85 C internal air they sit at
     their absolute *ambient* rating with zero margin; at 90 C they are out of
     specification, and **no module or heatsink design can fix an ambient
     rating**. This daughter's own components are also keyed to it (ENC-1b).

**Requested of the carrier owner:** re-derive s7.6 and re-issue with (a) an
explicit room-ambient assumption, (b) an at figure consistent with its own af
figure, and (c) a statement of whether the figures assume a sealed or a vented
enclosure - because s7.6 currently says "sealed box" while `stackup.md` s5.1 shows
sealed-with-the-module-inside does not close at all.

### OPEN-2 - `ID_ADC` code not allocated (CR-1). Blocks P4.

### OPEN-3 - ICD s9 and the internal LED harness (H1-P4). ESCALATED at revision B.

Previously: "blocks the module design, not this board's schematic." **That is no
longer true.** H1-Q1 selected wall conduction, so the emitters **must** be off the
daughter and on the enclosure wall - there is no path from an FR4 board in the
middle of a mezzanine stack to the outside of the box. The on-board fallback that
made this survivable is dead (`stackup.md` s6, D3 amendment (i)).

**So a strict reading of ICD s9 now reopens the ENCLOSURE decision, not just the
module design.** ICD s9 itself anticipates the off-board case ("if the LED module
is on a separate heatsink... that heatsink and its wiring are at PoE potential
too"), and a harness that never leaves the enclosure is not an external connector
on any reasonable reading - **but it still needs confirming, not assuming**, and
the cost of a "no" is now much higher than it was at H1.

### OPEN-4 - Emitter single-source and no published Rth (C4, H1-P11). PARTLY RETIRED at revision B.

**What H1-Q2 and H1-Q1 retired:**

- **Tj max is now published** for both parts (RGB **125 C**, white **120 C**),
  where the withdrawn 4-in-1 published none.
- **The unpublished Rth is now bounded in effect.** Under the wall-conducted
  model the die->slug term applies only to **one die's own heat** (red: 0.270 W),
  and the dominant 45 K term is ENC-8's *measured* wall path. Moving the assumed
  Rth from 12 to 20 K/W moves red Tj by **+2.2 K** and white Tj by **+3.0 K**
  (`power_tree.md` s6.3). It is no longer "the largest single uncertainty in the
  design".

**What remains open:**

- **Neither selected part publishes a thermal resistance.** The ~12 K/W is still
  `ASSUMED:`, extrapolated from ams-OSRAM's published 8.9-12 K/W.
- **Still single-vendor.** Both parts are XINGLIGHT and there is no
  pin-compatible alternate on LCSC. The only in-stock white with a published Rth
  is ams-OSRAM `C17664282` (**395 stock, $0.8786**, live-verified) and it is a
  **1515** body, so taking it re-derives the whole `stackup.md` s5.2 geometry.
- **Traps carried forward so they are not rediscovered:** the XINGLIGHT
  temperature-derating curve is **byte-identical (MD5-verified) across the red,
  green, blue and amber datasheets** - it is boilerplate and must not be designed
  to; the **"-A2" (non-BD) parts have Topr -35 to +60 C** and must not be
  substituted for the "-BD" parts under any circumstance; and vendor data quality
  in this family is low generally (a flux table mislabelled "mcd", a transposed
  IF/IFP row) - **treat every XINGLIGHT number as approximate and keep the margin
  in.**

### OPEN-5 - PAR-REQ-16 (binning): CLOSED by formal amendment.

**Closed at H1-Q4.** `requirements.md` s0 AMD-01 amends PAR-REQ-16 from a binning
specification to a **same-reel sourcing requirement**, and AMD-02 defers
PAR-REQ-17's *data* (the EEPROM ships empty) while keeping the hardware. Both
amendments quote the original text in full, so the record shows what changed.

**One consequence that must be carried rather than filed:** AMD-01 is a genuine
**reduction in guarantee**, not an equivalent substitution - same-reel is an
empirical correlation where a published bin is a contractual limit. **PAR-REQ-06
is therefore carried at reduced confidence**, its verification moves to a bench
comparison of assembled fixtures, and **D13 item 2 adds a second dependency that
did not exist at H1: the PAR-REQ-15 arrangement needs +/-5 % flux matching within
each family, which is same-reel's job.**

### OPEN-6 - PAR-REQ-03 / PAR-REQ-04 breach IEEE 1789 Recommended Practice 3

RP3 is the one seizure-prevention rule the standard states as a "shall" with no
"if it is desired" qualifier: below 90 Hz, modulation < 5 %. PAR-REQ-03's
pulse-and-decay (80 % -> 30 % per kick at ~2-5 Hz) is 45.5 % Michelson modulation -
**a 9.1x breach**; PAR-REQ-04's 20 Hz intensity tracking breaches it at any usable
depth. This is a **product decision, not an engineering defect** - the fixture's
purpose is to modulate - and it changes no hardware here beyond three requirements
already carried (no pulse-skip/burst/hiccup at any duty; no oscillating
over-temperature loop; no visible power-up flash sequence, covered by the ENABLE
gate). It should be a **recorded decision rather than an accident**, and it
carries ENC-6, the photosensitive-epilepsy note in the fixture documentation.

### OPEN-7 - P5 implementation risk: the notch has no pipeline support

Verified in this repo (`stackup.md` s2.1 TRAP 1): `board_init --outline` accepts
only `auto|WxH`; `kc.py` has no outline subcommand; `place_edit` ops are
place/move/rotate/flip/lock/add_text/move_text. The mandatory 30 x 26 mm relief
must be a **direct Edge.Cuts edit after `board_init`**, with every downstream
consumer re-verified. Compounded by TRAP 2 (`board_init` does not place the
outline at (0,0), so every rect in `constraints.json` must be translated) and by
the antenna column having **no automated check at all on F.Cu/B.Cu**.

**Revision B note:** the orchestrator is adding a `--cutout` flag centrally.
**Nobody is to hand-edit Edge.Cuts or shrink the outline in the meantime.** The
notch stays a hard keepout in `constraints.json` regardless of which mechanism
eventually cuts it.

---

### OPEN-8 (NEW) - The RGB and white beam angles do not match, and the datasheets have not been read

**Live-verified from LCSC this session:** the RGB 3-in-1 (`C22434861`) is
**140 deg** and the white (`C48586656`) is **120 deg**. Cross-checked against three
siblings in the same session - blue `C48586653` 140 deg, red `C48586650` 140 deg,
warm white `C48586655` **120 deg** - so the split is **white-versus-colour inside
the family**, not one bad record, and P1's family-level claim that "the 6070
family is 140 deg" (`research/led-emitter.md` s10) is **wrong for the white
parts**.

**Consequence:** fitting `cos^m` gives white `m = 1.000` (Lambertian) against RGB
`m = 0.646`, so the mix is **-5.0 % white at 30 deg off-axis, -11.5 % at 45 deg,
-33.5 % at 71.6 deg** (a wall 3 m away at 1.5 m height). **This is a first-order
PAR-REQ-15 defect that neither the arrangement nor firmware can correct**, and it
is the second independent reason the diffuser is mandatory (D14, `stackup.md`
s5.2.1 mechanism 3).

**Open because:** this run designed to the conservative published attribute but
**did not extract either datasheet** (the P2 delta was explicitly scoped to
exclude datasheet extraction). **P3 must confirm both angles from the datasheets
and re-check `stackup.md` s5.2.3's diffuser stand-off**, which was derived from
the narrower of the two.

### OPEN-9 (NEW) - The mandatory diffuser costs 30-45 % of the flux and was in no budget

`stackup.md` s5.2.3: the recommended Option A opal diffuser has a total
transmittance of 55-70 %. Against `research/led-emitter.md` s5's own baseline of
~41 lx direct average in the 5 x 7 m room, that gives **~25 lx** (Option A) or
**~36 lx** (Option B) - in a fixture that document already characterised as **"a
dark-room instrument, not room lighting"**.

**Three things follow and none of them is settled:**

1. **It is a real cost of H1-Q2** and the H2 record should show it next to the
   benefits, not buried.
2. **It changes the H1-P7 calculus**: 145 mA/die's 3.3 % of light is worth more
   than it was, which is why `power_tree.md` s3.3 recommends 150.
3. **There is nowhere to recover the light from.** The `+12V` sustained ceiling
   has 4.4 % of headroom; a higher drive current would reopen the rail decision
   that H1 just confirmed. **If the delivered light is judged inadequate after the
   s5.2.5 bench test, the answer is a lighting-design decision (more fixtures, or
   accept the level), not a hardware one.**

### OPEN-10 (NEW) - Nothing in this pipeline can verify ENC-8 or PAR-REQ-15

**ENC-8's 8.0 K/W wall path and every number in `stackup.md` s5.2 are design
targets with stated bench tests, not verified results.** ai-ee has no thermal
simulation and no optical simulation, and both criteria depend on an enclosure
that does not exist yet and that this run does not own.

**This is recorded as OPEN rather than as a closed criterion because two of the
design's load-bearing claims now rest on it:** ENC-1 (internal air) is downstream
of ENC-8, and PAR-REQ-15 is downstream of s5.2.5. **The mitigation is that both
have a written test method with pass/fail numbers and named failure actions**
(`stackup.md` s5.0 and s5.2.5), so whoever builds the enclosure can settle them
without re-deriving anything - which is exactly what H1 directed.
