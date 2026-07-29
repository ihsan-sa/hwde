# Reference-design decisions: pulsed-led-driver (LUM-DTR-STROBE-A)

Block: capacitor-bank-fed pulsed white LED strobe. ~2800 uF / 100 V bank on the switched
48 V PoE rail; series white string (Vf_total <= 38 V at 2.6 A); current-regulated low-side
pass element; firmware-governed charge path that doubles as the inrush limiter.

Scope: topology decisions extracted from vendor primary sources. No files, layouts or
schematic fragments copied. Part selection is not decided here.

Every claim below is either (a) cited to a primary vendor document with a section, or
(b) explicitly labelled **DERIVED** (arithmetic done here from cited inputs) or
**OPINION** (uncited judgement, kept only where dropping it would lose a real risk).

---

## 0. Sources

| # | Document | URL |
|---|---|---|
| S1 | TI, *LED Lighting Control Reference Design for Machine Vision* (TIDA-01081), TIDUDB6, Dec 2017 | https://www.ti.com/lit/ug/tidudb6/tidudb6.pdf |
| S2 | TI, *TPS92515 / TPS92515HV* datasheet, SLUSBZ6A, Apr 2016 rev Aug 2016 | https://www.ti.com/lit/ds/symlink/tps92515.pdf |
| S3 | Infineon, *Linear Mode Operation and Safe Operating Diagram of Power-MOSFETs*, AN V1.1, May 2017 | https://www.infineon.com/dgdl/Infineon-ApplicationNote_Linear_Mode_Operation_Safe_Operation_Diagram_MOSFETs-AN-v01_00-EN.pdf?fileId=db3a30433e30e4bf013e3646e9381200 |
| S4 | Nexperia, *IAN50006 - Power MOSFETs in linear mode* (interactive app note) | https://www.nexperia.com/applications/interactive-app-notes/IAN50006_Power_MOSFETs_in_linear_mode |
| S5 | TI, *Robust Hot Swap Design*, SLVA673A | https://www.ti.com/lit/an/slva673a/slva673a.pdf |
| S6 | Cree LED, *Pulsed Over-Current Driving of XLamp LEDs: Information and Cautions*, CLD-AP60 Rev 4A | https://downloads.cree-led.com/files/da/x/XLamp-Pulsed-Current.pdf |
| S7 | Cree LED, *XLamp XHP70.3* datasheet, CLD-DS266 Rev 11A | https://downloads.cree-led.com/files/ds/x/XLamp-XHP70.3.pdf |
| S8 | ams-OSRAM, *GW CSSRM3.HW* datasheet, v1.2, 2025-12-09 | https://look.ams-osram.com/m/55c5480864548464/original/GW-CSSRM3-HW.pdf |
| S9 | TI, *TPS2378* PoE PD interface datasheet | https://www.ti.com/lit/ds/symlink/tps2378.pdf |
| S10 | Nichicon, *Application Guidelines for Aluminum Electrolytic Capacitors*, CAT.8100Z-2 | https://www.nichicon.co.jp/english/products/pdf/e-al_gui.pdf |
| S11 | TI, *Integrated-Resistor Current Sensors Simplify PCB Design*, SBOA197, May 2017 | https://www.ti.com/lit/pdf/sboa197 |
| S12 | LED professional, *LED Driver for High Power Machine Vision Flash* | https://www.led-professional.com/resources-1/articles/led-driver-for-high-power-machine-vision-flash |
| S13 | Dyble, Narendran et al., *Impact of dimming white LEDs: chromaticity shifts due to different dimming methods*, SPIE 5941 (2005) | https://ui.adsabs.harvard.edu/abs/2005SPIE.5941..291D/abstract |

S1 is the single closest prior art found. It solves structurally the same problem this
board solves - short, high-power LED pulses from a hard-limited input supply, using a
capacitor bank to buy the peak - and it is a full vendor design guide with measured
waveforms. Most of the load-bearing decisions below come from it, cross-checked against a
second source.

---

## 1. The closest prior art: TI TIDA-01081

**Same problem, same shape.** S1 s1: "The pre-boost is equipped with an adaptive average
input current limit and an energy storing bank of output capacitors. Those two features
together avoid overloading of the input power source of the reference design while enabling
a much higher instantaneous power level to drive the LEDs. The adaptive average input
current limit of the pre-boost results in an 8-W to 10-W input power limit while the LEDs
are driven with a peak pulse power of up to 40 W."

Mapping to this board: 8-10 W input limit -> our 8.5 W (af) rail; 40 W peak -> our ~99 W
peak at 2.6 A; energy-storing output capacitor bank -> our 2800 uF / 100 V bank; adaptive
average input current limit -> our firmware-governed charge path.

S1 Table 1 key specs, for calibration: LED string voltage up to 24 V, average LED current
200 mA - 2.4 A programmable, pulse width 200 ns - 4.9 s, **pulse rise/fall < 40 to 100 ns**,
pulse repetition 0.2 Hz - 10 kHz, duty cycle 1-100 %.

The one place TI's design differs from our assigned topology is the regulator: TI uses a
switching buck LED driver, we use a linear pass element. See OPEN-1.

---

## 2. Decisions

### D1 - Storage sits on the supply side of the regulator, never across the LED string

The bank is the *input* capacitance of the drive stage, not an output filter. TI's energy
bank is the pre-boost's output capacitor bank feeding the LED buck's input (S1 s2.4.1.3,
bullet 5: "Energy storage in the pre-boost output capacitors enables the LED buck to
generate LED pulses with higher peak power (up to 40 W and more) than the 8-W to 10-W input
power limit of the pre-boost").

Corollary, and this is the decay-tail decision: **there must be essentially no capacitance
across the LED string.** S2 s9.2.1.7: "Because current is being regulated and is continuous,
no output capacitance is required to supply the load and maintain output voltage. This
regulation helps when designing a high-frequency PWM dimming on the LED load." S1 s2.4.1.1
picks the buck topology specifically because it "ensures a continuous current flow through
the load (LEDs) on its output, even without the need for an energy storing output
capacitor", and S1 Figure 15 is captioned "No Output Capacitor".

S2 s9.2.1.7 also documents the tradeoff honestly: a parallel output capacitor lets you
shrink the inductor or drop the switching frequency, and covers poor inductor/Vin tolerance
- but it is exactly the part that produces a decay tail. On this board it must not be
fitted.

**Source:** S1 s2.4.1.1 and s2.4.1.3; S2 s9.2.1.7.

### D2 - The decay tail of a switching CC driver is the inductor, not the LED

S1 s2.4.1.1 states it directly: "this reference design cannot fulfill the fast rise and fall
time requirements for the LED current given in Table 1 based on the hysteretic operation
alone. The buck inductor and its physical property of slowing down any change in current
flow through the inductor is the reason for it. This challenge can be addressed in theory by
reducing the inductor value or increasing the voltage VL applied across the inductor."

Three tail/ramp mechanisms are therefore named by the sources, in order of size:

1. **Inductor freewheel** - the inductor keeps pushing current after the control loop asks
   for zero (S1 s2.4.1.1).
2. **Output capacitance across the string** - discharges through the LEDs after turn-off
   (S2 s9.2.1.7, by implication of "no output capacitance is required").
3. **Converter soft-start / loop settling on turn-on** - S1 s2.4.1.1 credits the
   TPS92515HV's "dedicated PWM dimming input to switch the buck instantaneously ON and OFF
   without the delay or soft-start phases found in other DC/DC converters and LED drivers".
   That is the fade-in mechanism STR-REQ-01 forbids.

**A linear low-side pass element has none of the three.** No inductor, no output cap, and
the pass element's gate is the control. **DERIVED:** this is the strongest argument for the
assigned linear topology, and it is worth writing down because it is the reason to accept
the linear stage's efficiency penalty rather than reach for a switching CC driver.

Phosphor persistence is not a limit at this timescale: YAG:Ce emission decays in tens of
nanoseconds (multiple published measurements put the Ce3+ lifetime near 60 ns), four orders
below the 1 ms optical fall STR-REQ-11 asks for. **OPINION on the exact number** - not
sourced from a vendor datasheet, but the order of magnitude is not in dispute.

**Source:** S1 s2.4.1.1; S2 s9.2.1.7.

### D3 - Fast edges in the switching case are bought with two extra FETs; note what each does

S1 s2.4.1.2 documents the mechanism used to reach 40-100 ns rise/fall, and it is worth
understanding even though we do not need it:

- **Q4 = QSHORT_LED, a shunt FET across the LED string.** The buck's inductor is pre-charged
  to the target peak current with the string *shorted*, then the shunt FET opens: "When this
  FET is switched off, the inductor current IL is steered immediately through the five LEDs,
  switching them on instantaneously" (S1 s2.4.1.2). This is the classic instant-on trick.
- **Q3 = QDISCHG, a series-parallel discharge path (diode + resistors + FET) beside the
  string.** "The voltage drop across this parallel path (at the same current as the LED
  current) is much lower than the forward voltage of the LED string. This is why the LED
  current is instantaneously steered away from the LEDs towards this parallel path"
  (S1 s2.4.1.2). This is the instant-off trick.
- Both FETs sit "in close proximity to the LEDs" with dedicated gate drivers (UCC27511),
  using separate OUTH/OUTL driver outputs so turn-on and turn-off speed can be tuned
  independently (S1 s2.4.1.2).

### D4 - Shunt-FET dimming is REJECTED for this board, on the power budget

Shunt-FET dimming is the standard automotive matrix-LED answer to the tail problem, and S2
supports it explicitly (S2 features: "10,000:1 Shunt PWM Dimming Range", "High Contrast
Shunt FET Dimming"; S2 s8.3.4 describes the COFF workaround needed when the output is
shorted). It works because the converter never stops: the inductor current stays continuous
through the shunt, so there is no ramp on either edge.

That continuity is exactly why it is disqualified here. S1 s2.4.1.2, on why TI added the
active discharge path: "A fast inductor discharge reduces the average power dissipation in
the freewheeling diode and inductor compared to a pure shunt-FET dimming implementation."
i.e. under pure shunt-FET dimming the full current keeps circulating and burning during the
LED-off period.

**DERIVED:** on this board that current comes out of a 0.99 J bank refilled from an 8.5 W
rail. Shunting the string instead of interrupting it would draw the same average energy from
the bank whether the LED is lit or not, collapsing the achievable flash rate. The pass
element must **interrupt the string in series**, which is what the assigned topology already
does. Recording it because "use a shunt FET, that is how matrix LED does it" is the obvious
wrong turn here.

**Source:** S1 s2.4.1.2; S2 features / s8.3.4.

### D5 - Sub-flash intensity (STR-REQ-04) is analogue amplitude control, and that is safe for colour

The pass element is already a current source; setting its reference sets the amplitude. S1
does the same thing with a DAC on the driver's IADJ pin (S1 s2.4.1.1: "The TPS92515HV
provides additionally a specific IADJ input for setting the IL-Peak threshold by an analog
voltage VIADJ applied to that input pin"), and S2 rates analogue dimming at 200:1 range.

The known objection to analogue dimming is chromaticity shift with current, because the
operating point moves along the LED's colour-vs-current curve. Both major vendors publish
that curve - Cree S7 has "Relative Chromaticity vs Current"; ams-OSRAM S8 plots
"Chromaticity Coordinate Shift, dCx, dCy = f(IF)" over 100-1800 mA on a +/-0.03 axis - so it
is a checkable acceptance criterion, not a guess.

Cross-check on magnitude: S13 measured phosphor-converted white LED systems shifting **less
than a 4-step MacAdam ellipse from 100 % down to 3 % output, under both analogue and PWM
dimming**. For a white-only strobe (requirements open question 1 default) that is
acceptable. Note S13 is academic, not a vendor datasheet.

STR-REQ-14 constrains full output specifically, which is the *other* end of the curve - see
D8.

**Source:** S1 s2.4.1.1; S2 features; S7 Relative Chromaticity vs Current; S8 dCx,dCy =
f(IF); S13.

### D6 - Linear-mode pass element: SOA is the selection criterion, not Rds(on)

S3 s1.1 (fan-controller / current-source case, which is ours): "As the MOSFET is operated
exclusively in linear mode, the RDS(on) of the MOSFET is completely irrelevant when
calculating the power dissipation. The power dissipation in the MOSFET depends only on the
voltage drop across the MOSFET and the current flow: Pdiss = VDS * IDS."

S3 s2.1 names the five SOA limit lines: Rds(on) limit, package (current) limit, maximum
power limit, **thermal instability limit**, and breakdown voltage limit. The thermal
instability line is the one that bites a pulsed linear stage.

The instability criterion, from S3 s2.1:

```
VDS * ZthJC(tpulse) * dIDS/dT  >  1      ->  thermally unstable
```

Since VDS > 0 and ZthJC > 0, instability requires a **positive** temperature coefficient of
drain current, which happens only for VGS below the Zero Temperature Coefficient (ZTC)
point. S3: "thermal instability can occur only for VGS below the VGS of the ZTC point."

Failure mechanism, S3 s2.1: below ZTC "local hot spots will draw more current as they heat
up. This will lead to increased local power dissipation and further heating. Ultimately this
results in thermal runaway and local destruction of the chip." S4 names this the **Spirito
effect** and adds that "wider pulses activate Spirito effects at lower voltages than
narrower pulses" - directly relevant, our pulses are 5-200 ms, which is wide.

### D7 - Pass-element selection rules (both sources agree)

S3 s3, continuous-linear-mode case: "Thermal design is most important and therefore MOSFETs
with low ZthJC are most suitable... Thermal instability can be avoided by utilizing MOSFETs
with low ZTC point. **This means that MOSFETs of previous technology generations and/or
higher voltage classes will be more suitable for this kind of application.**"

S3 s2.1 explains why: "Modern power MOSFETs exhibit ever increasing transconductances and
therefore also ZTC-points at higher VGS", and higher-voltage-class parts (150 V vs 25 V)
have their ZTC at lower current and VGS because "the increase of RDS(on) over temperature
will dominate the transconductance behavior".

S4 corroborates independently: "Newer technologies show generally worse linear mode
capability", mitigated by "devices with lower junction-to-base thermal resistance, larger
packages, older-generation technologies, or Nexperia's ASFET portfolio with enhanced SOA
ratings". Infineon markets Linear FET and IXYS markets Linear L2 for the same reason.

Resulting selection rules for this board:

1. Pick a **100 V-class or higher** N-channel part (the 57 V worst-case rail plus margin
   forces it anyway per requirements s8.1) - which also helps the ZTC.
2. Choose on **published SOA curves and low ZthJC**, in a large package. Prefer a part whose
   datasheet actually plots a 10 ms and a 100 ms SOA line; many low-Rds(on) trench parts
   stop at 1 ms or omit the DC line entirely.
3. Prefer an explicitly linear-mode-qualified family (Infineon Linear FET, Nexperia ASFET,
   IXYS Linear L2) over a generic switching FET at the same Rds(on).
4. **Do not select on Rds(on).**

### D8 - SOA derating method (two independent sources, same recipe)

Datasheet SOA curves are single-pulse at Tc = 25 C. Ours is repetitive at a case temperature
set by 56-69 C internal air (requirements s4). Three corrections are required and all three
are documented:

- **Case temperature.** S5 eq. 5: `SOA(Tc) = SOA(25 C) * (Tj,max - Tc) / (Tj,max - 25 C)`.
  S3 s2.1 gives the same physics via `IDS = dTmax / (ZthJC(tpulse) * VDS)`.
- **Repetition.** S3 s2.1: "The SOA diagram in the datasheet is given at dutycycle D=0 for
  various pulse lengths. Exposing the MOSFET to repetitive pulses results in D!=0. In that
  case the thermal impedance diagram ZthJC = f(tp, D) has to be used." The single-pulse curve
  is not valid for a 25 Hz strobe.
- **Intermediate pulse widths.** S5 s2.3.2: SOA vs time is a straight line on log-log, so
  interpolate with a power law `SOA(t) = a * t^m`, fitting a and m from two datasheet points.
  S5 Table 1 shows the shape for a 100 V part (PSMN4R8-100BSE at VDS = 60 V): 6000 W at
  0.1 ms, 1800 W at 1 ms, 360 W at 10 ms, 120 W at 100 ms.
- **Non-square pulses.** S5 s2.3.3 converts a non-square power pulse to an equivalent square
  pulse before comparing against the curve. S4 offers three derating conventions (current
  scaling, voltage scaling, power scaling) and states that **current scaling is the best
  Spirito approximation and the most conservative against measured data** - use current
  scaling.

**DERIVED - the operating points that must be checked.** Two, not one:

| Case | Vds | Id | Duration | Pdiss | Note |
|---|---|---|---|---|---|
| Flash, worst instant | ~10 V (bank at 48 V, string 38 V) | 2.6 A | up to ~8.6 ms at full current | **26 W** decaying to ~5 W as the bank droops to 40 V | repetitive, D set by the governor |
| Cold-start bank charge | 48 V falling to ~0 | 0.25 A (af sustained limit) | ~0.54 s (requirements s3.2) | **12 W peak, ~6 W average** | single event, but 540 ms long |

The cold-start charge event is the larger SOA problem of the two, and it is easy to miss
because it is not the flash. Both must land inside the derated curve.

**Source:** S3 s2.1, s3; S4; S5 s2.3.1-2.3.3, Table 1.

### D9 - Pulsed LED derating: treat a 5-200 ms pulse as DC

This is the finding most likely to change the LED choice.

**Cree's official position (S6) gives no numeric allowance at all.** S6 "Repetitive Pulsing":
"A particular device subjected to repeated transients at an amplitude some percentage above
the data-sheet limits but below the threshold required for single-pulse failure will still
eventually fail. The failure mechanism will most likely be due to electromigration."
S6 Summary: "It is possible to operate LEDs in a continuous pulsed mode at higher levels,
but there are trade-offs that may adversely affect efficiency, chromaticity and long-term
reliability... Cree LED cannot make any guarantees regarding reliability or performance when
using our products outside the published specification limits." Footnote 2: "Operating XLamp
LEDs outside the published specifications negates the warranty."

**ams-OSRAM's numeric pulse rating is a microsecond rating, not a licence to pulse for
milliseconds.** S8 Maximum Ratings, GW CSSRM3.HW: DC forward current max **1800 mA**; Surge
Current IFS max **2000 mA at t <= 10 us, D = 0.005**. That is +11 % for 10 microseconds at
0.5 % duty. Reading "surge current 2 A" as headroom for a 50 ms flash at 2.6 A is off by
four orders of magnitude in time.

**DERIVED:** LED junction thermal time constants are milliseconds; a 5-200 ms pulse is
thermally a DC event for the die. Therefore **select an emitter whose DC forward-current
rating covers 2.6 A at the derated solder-point temperature, and do not rely on pulsed
over-current at all.** This also disposes of STR-REQ-13 cleanly: the pulsed derating curve is
checked, and the answer is that it does not help at these pulse widths.

Existence proof that this is achievable (**not a part recommendation** - that is the
component-scout's call): Cree XHP70.3, S7 Characteristics - DC forward current **3600 mA in
the 12 V configuration**, Vf 11.2-12.2 V at 1050 mA / 85 C, thermal resistance junction to
solder point **0.2 C/W**. Three such emitters in series sit near the <= 38 V string budget at
2.6 A, inside the DC rating, with no over-drive.

Two more constraints from the same datasheets:

- **Efficacy droop.** S7 publishes "Relative Flux vs Current (TJ = 85 C)". Flux is
  sub-linear in current, so 2.6 A does not buy 2.6x the lumens of 1.0 A. Size the optical
  claim off that curve, not off a linear extrapolation.
- **Temperature derating of the current itself.** S8 plots "Max. Permissible Forward Current
  IF = f(Ts)" against solder-point temperature. Requirements s4 puts internal air at
  56-69 C; the permissible current at that Ts is materially below the 25 C headline number.
  STR-REQ-15's "both cases must pass" is exactly this.

**Source:** S6 Repetitive Pulsing / Summary / fn 2; S7 Characteristics, Relative Flux vs
Current; S8 Maximum Ratings, IF = f(Ts).

### D10 - Charge path is a hot-swap with dv/dt (constant-inrush) control, not power-limit-only

S5 s2.2.2: "For designs with large load currents and output capacitances, using a
power-limit-based start-up can be impractical... Using a larger output capacitor will result
in a longer start-up time and require a longer timer. Thus, a longer timer and a larger power
limit setting are required, which places more stress on the MOSFET during a hot-short or a
start into short. Eventually, there will be no FETs that can support such a requirement. An
alternative is to limit the inrush current with a dv/dt control circuit... Cdv/dt limits the
slew rate of the gate and the output voltage, which in turn limits the inrush current."

S5 Figure 7: with dv/dt control "the inrush current is constant and the MOSFET power
decreases as the VOUT goes up and VDS decreases" - the right shape for charging 2800 uF from
a fixed 48 V rail.

Precedent for making the limit **settable by firmware**: S1 s1 - "The dual DAC of the common
power block controls the adaptive current limit of the eFuse and of the pre-boost." TIDA-01081
has a firmware-adjustable input current limit for exactly the reason this board needs one.

### D11 - The PD foldback numbers, and why 1.0 A is the wrong design target

Requirements s3.2 / ICD s8.2 says size against the PD's 1.0 A operating current limit. The
carrier uses a TPS2378-class PD controller (requirements s3.1). S9 Electrical
Characteristics gives the real distribution:

| Parameter | Min | Typ | Max |
|---|---|---|---|
| Current limit (VRTN = 1.5 V) | **0.85 A** | 1.0 A | 1.2 A |
| Inrush current limit | 100 mA | **140 mA** | 180 mA |
| Foldback threshold (VRTN rising) | **11 V** | 12.3 V | 13.6 V |
| Foldback deglitch time | **500 us** | 800 us | 1500 us |

S9 s7.4.6: "Inrush limiting prevents the RTN current from exceeding about 140 mA until the
bulk capacitance is fully charged... **If RTN ever exceeds about 12 V for longer than 800 us,
then the TPS2378 returns to inrush limiting.**"

**DERIVED, and this is a correction worth carrying forward:** the trip is *not* a current
threshold, it is the voltage across the PD's internal pass FET held above the foldback
threshold for longer than the deglitch. Holding the PD in current limit is what raises VRTN.
So the charge path must be designed against the **min** numbers - current limit **0.85 A**,
deglitch **500 us** - not the typicals. A charge path set at 0.9 A is inside the ICD's stated
1.0 A ceiling and still capable of folding a worst-case PD back to 140 mA, browning out the
whole fixture. Recommend the charge-path limit be set at or below **0.6 A** to leave margin
for the carrier's own load, with the total daughter draw (charge current + housekeeping)
checked against 0.85 A.

Compliance context (requirements s3.3 / ICD s8.3): IEEE 802.3 caps PD port capacitance near
180 uF; our 2800 uF is 15x that and sits behind the carrier's 48 V compliance load switch.
The daughter's charge path is therefore a hot-swap into a large capacitive load whose
*upstream* supply has a hard limit and a fast foldback - the S5 problem exactly.

**Source:** S9 Electrical Characteristics, s7.4.6; S5 s2.2.2.

### D12 - Linear charging is cheap here only because the top-up window is narrow

The standard objection to linear/resistive capacitor charging is the 50 % energy penalty:
charging C from 0 to Vsrc through any dissipative element burns exactly as much energy in the
element as ends up in the capacitor. S1 s2.4.1.3 makes the same point in the vendor's own
terms, contrasting its switching pre-boost - which implements the average input current limit
"in a quasi-lossless manner" - with the eFuse, which "limits the current by controlling the
ON-resistance of the internal pass FET. There is therefore an increase of losses and power
dissipation in the eFuse as soon as the eFuse enters the current limit region."

**DERIVED arithmetic for this board.** The pass element burns the fraction
`(Vsrc - Vc_mean) / Vsrc` of the delivered energy:

| Case | Window | Vc_mean | Loss fraction |
|---|---|---|---|
| Steady-state top-up | 40 -> 48 V | 44 V | **~8.3 %** |
| Cold start | 0 -> 48 V | 24 V | **50 %** |

So a switching pre-regulator is **not** worth its parts cost, board area or the DC-DC hot
zone conflict (requirements s5.2) for the steady-state duty - the narrow 48 -> 40 V usable
window is what makes linear charging acceptable. But the cold start does pay the full 50 %
(3.23 J stored, 3.23 J burnt) and, spread over the 0.54 s cold-start time from requirements
s3.2, is a ~6 W average / 12 W peak linear-mode event in the pass element. That is a genuine
SOA case, not a rounding error - see D8.

**Source:** S1 s2.4.1.3 (qualitative); arithmetic derived.

### D13 - Bank capacitor technology: this is photo-flash duty, and vendors say so explicitly

S10 s1(5): "**For a circuit that repeats rapid charging / discharging of electricity, an
appropriate capacitor that is capable of enduring such a condition must be used. Welding
machines and photo flash are a few examples of products that contain such a circuit**... For
appropriate choice of capacitors for circuit that repeat rapid charging / discharging, please
consult Nichicon."

A 1-25 Hz strobe bank is squarely in that clause. A general-purpose 105 C aluminium
electrolytic selected on capacitance and voltage alone is the wrong part, which is what
STR-REQ-08 is already warning about ("select capacitors on pulse ripple current and ESR, not
capacitance alone").

Two more usable constraints from the same document:

- **Polymer aluminium is viable at our current.** S10 s1(5): "If excess a rush current due to
  drastic charge/dis-charge was applied to conductive polymer aluminum solid electrolytic
  capacitors, it may cause a short circuit or an increase in leakage current. Therefore,
  Please do not apply a rush current that is larger than 10 A." Our discharge peak is 2.6 A,
  well inside 10 A - so polymer aluminium (an SMD technology, which helps requirements open
  question 6 on assembly side) is not excluded by pulse current.
- **Series stacking needs balancing.** S10 s1(6)w: two or more electrolytics in series need a
  balancing resistor in parallel with each. Relevant only if a 100 V bank is built from
  series-connected lower-voltage parts - which requirements s8.1 already discourages.

**Source:** S10 s1(5), s1(6).

---

## 3. Layout constraints the sources call out - flag these for interface-spec

### L1 - Minimise the discontinuous / high-di/dt current loop

S2 s11.1 (Layout Guidelines): "Minimize discontinuous current loops"; the switch-node loop
"should be only large enough to connect the components without excessive heating from the
current it carries."

**DERIVED mapping:** this board's discontinuous loop is `bank(+) -> LED string -> sense
resistor -> pass FET -> bank(-)`. It carries the full 2.6 A and it is the loop that is
interrupted, so it sets the di/dt. Treat it with the same discipline a buck's switch-node
loop gets: minimum enclosed area, return directly under the outbound path.

### L2 - Kelvin the shunt, and do not tap the sense amp onto the current-carrying trace

S11 (layout section, Figure 2): "To achieve accurate current measurements there must be 4
connections to the current sense resistor. Two connections should handle the current flow,
while the other two sense the voltage drop across the resistor... **One of the most common
mistakes in laying out the current sense resistor is connecting the current sense amplifier
inputs to the current carrying trace instead of directly to the current sense resistor** (as
shown in Figure 2a)." Full four-wire Kelvin is called out as most needed below 0.5 mOhm; S11
also notes many resistor datasheets do not state the measurement point used in manufacture,
so sense-pad placement (inner vs side) is a real accuracy variable.

S2 s11.1: "The most sensitive loop contains the sense resistor (RSENSE). Place the sense
resistor as close as possible to the CSN and VIN pins to maximize noise rejection", and "the
IADJ, COFF, CSN and VIN pins are all high-impedance control inputs, therefore minimize the
loops containing these high impedance nodes."

**DERIVED:** the sense pair must be routed as a tight differential pair from the shunt pads
to the regulating amplifier, must not run parallel to the pulse path, and the analogue return
must meet the pulse return only at the shunt's low side. The bank-voltage divider going to
ADC0 has to reference the same quiet point.

### L3 - Gate drive and its return

S1 s2.4.1.2: the switching FETs are "located in close proximity to the LEDs to steer the
current flow" with "dedicated MOSFET drivers (U18 and U20) [that] provide the needed gate
drive current for a fast switching of the FETs. Separate outputs (OUTH and OUTL) on those
drivers allow a separate fine tuning for the speed with which the MOSFETs are switched on and
off."

**DERIVED for a linear stage:** the pass element is not switched hard, but its gate node is
still the control input of a 26 W element sitting in a 2.6 A loop. Keep the gate driver /
error amplifier next to the FET, return its ground to the FET source (shunt low side) and not
to the general plane, and keep the gate loop out of the pulse loop's field.

### L4 - Remote LED module: the harness is in the pulse loop

S2 s11.1: "In some applications the LED load can be far away (several inches or more) from
the device, or on a separate PCB connected by a wiring harness. When an output capacitor is
used and the LED load is large or separated from the main converter, the output capacitor
should be placed close to the LEDs to reduce the effects of parasitic inductance on the AC
impedance of the capacitor."

Requirements open question 4 defaults to an off-board LED module on its own heatsink, so this
applies. **DERIVED:** run the two harness conductors as a tight pair (twisted or ribbon-
adjacent) to hold the loop inductance down, and do **not** add a bulk capacitor at the module
- per D1 that capacitor is a decay tail. Any local capacitance at the module must be small
enough that its discharge through the string is invisible.

### L5 - EMI parts on the pulse path are an explicit tradeoff against the optical edge

S1 s2.4.1.2: "The ferrite beads L6 and L7 and the snubber R130/C95 are used to improve EMI;
however, these parts slow down the speed of switching the LEDs on and off. This speed is
critical when using the design for ultra-short LED pulses."

Nothing may be added to the LED path for EMI reasons without re-measuring the optical edge
against STR-REQ-11.

### L6 - Interaction with this project's 48 V clearance rule

Requirements s8.1 imposes **0.60 mm minimum outer-layer copper-to-copper clearance around
every 48 V net, board-wide**, and notes it applies through the board (an inner-layer or
opposite-face signal under a 48 V antipad needs the same).

**DERIVED conflict, flag it now:** L1 wants the pulse loop tight, and the bank(+) node *is* a
48 V net. Do not resolve this by narrowing the gap. Resolve it by putting the loop's return
directly beneath the outbound conductor on an adjacent layer - vertical coupling shrinks the
loop area without violating the in-plane clearance, and inner-layer clearance is governed by
JLC's 0.127 mm minimum anyway (requirements s8.1), so the vertical dimension is free.

### L7 - Probing

S1 s3 warns that these edges cannot be measured with a standard probe lead: "the ground lead
and alligator clip must be replaced by a ground spring... The small ground spring reduces
significantly the noise, which can couple otherwise into the long ground lead of a standard
probe configuration."

Compounding it, requirements s8.4: the whole fixture floats at PoE potential, an earthed
scope probe breaks PD detection outright, and every test point carries the same silkscreen
warning as the carrier's recovery header. Provide a proper short-return probe point at the
shunt if the optical/electrical edge is to be verified at all.

---

## 4. Errata and footguns

**E1 - Leakage glow defeats "instant blackout".** S2 s8.3.11: "The high-side FET driver has a
small leakage path to the output. Although very small (<<100 uA), the LEDs could glow if the
current was not eliminated. The 100-uA (typical) pulldown is activated and held ON while PWM
is low and ensures no light output." A high-power white LED at tens of microamps is visible in
a dark room. Budget the pass element's Idss, the bank bleed path and the ADC divider so no
sub-milliamp path exists through the string when off - and if one does, add a deliberate
shunt across the string that is switched on during blackout.

**E2 - The first flash after a long gap is the one that fades in.** S12 reports that in
machine-vision flash drivers the problem with long off-times is "output capacitor charge loss
due to leakage, preventing a quick response when the LED is turned back on", fixed by
"trickle-charging these components during long off-times". STR-REQ-01 goes down to 1 Hz, so
this board has ~1 s off-times. Any sample-held or AC-coupled current reference, or any
soft-start on the regulating loop, will show up as a fade-in on the first flash of a phrase -
the most visible flash there is. Keep the reference DC-coupled and always alive under ENABLE.

**E3 - "Surge current" is a microsecond rating.** S8: IFS 2000 mA at **t <= 10 us, D = 0.005**
against a 1800 mA DC rating. Do not read a surge line as pulse headroom for a millisecond
flash.

**E4 - Over-driving the LED voids the warranty.** S6 fn 2: "Operating XLamp LEDs outside the
published specifications negates the warranty as published in Cree LED's Sales Terms and
Conditions." S6 Summary also puts the burden of lifetime testing on the customer. For a
4-6 unit build there is no lifetime-test budget, so stay inside the published DC ratings.

**E5 - Do not pick the pass element on Rds(on).** S3 s3 and S4 both say modern low-Rds(on)
trench parts are the *worst* choice for linear mode (higher transconductance -> ZTC at higher
VGS -> more of the operating range is thermally unstable). S3 s1.1: in continuous linear mode
Rds(on) is "completely irrelevant" to power dissipation.

**E6 - Datasheet SOA curves do not apply as printed.** They are single-pulse, Tc = 25 C. This
board is repetitive at Tc well above 25 C. Both derations are mandatory (S3 s2.1, S5 eq. 5),
and S4 adds that longer pulses trigger Spirito at *lower* voltages, so the 200 ms case is not
simply a scaled 5 ms case.

**E7 - Design the charge path to the PD's minimum limits, not its typicals.** S9: current
limit min 0.85 A, foldback deglitch min 500 us, foldback threshold min 11 V. See D11.

**E8 - A pass element in regulation can never charge the bank to the rail.** DERIVED: while
the charge FET is regulating current it must hold some VDS, so the bank asymptotes below
48 V and flash energy is lost. The charge path must terminate by driving the FET fully
enhanced (ohmic) once the current falls below the limit, exactly as a hot-swap does (S5
s2.2.1 / S3 s1.1's third operating state). Do not build a charge path that stays in linear
regulation forever.

**E9 - Cold start is an SOA event, and it is bigger than the flash.** DERIVED, see D8/D12:
~12 W peak, ~6 W average, ~540 ms, in linear mode. Easy to overlook because it is not the
flash the board was designed around.

**E10 - Repetitive charge/discharge needs a photo-flash-class capacitor.** S10 s1(5) names
photo flash and welding as the examples and asks the designer to consult the vendor. A
general-purpose electrolytic chosen on uF and volts will not survive the duty, and STR-REQ-08
already requires the ripple-current rating to appear in the BOM.

**E11 - Shunt-FET dimming does not reduce source current.** See D4. It is the standard
automotive answer and it is the wrong answer on an 8.5 W budget.

**E12 - EMI parts kill the edge.** S1 s2.4.1.2, see L5.

**E13 - The reference designs are efficiency-optimised, we are edge-optimised.** S1 s2.4.1.1
opens by choosing a switching regulator for "less power dissipation compared to any linear
regulator approach", then spends two extra FETs, two gate drivers and a discharge network
undoing the inductor's effect on the edges. Reading S1 as an endorsement of the buck for
*this* board would be a misread - see OPEN-1.

---

## 5. Open questions / source conflicts

**OPEN-1 - TI recommends a switching regulator; this board is assigned a linear pass element.**
S1 s2.4.1.1: "Using this switching regulator has the clear advantage of less power dissipation
compared to any linear regulator approach. This holds especially true when considering the huge
variation in the LED string voltage over forward current, temperature, and binned forward
voltage groups." Against that, S1 s2.4.1.1 also concedes the inductor prevents it from meeting
its own rise/fall spec without two extra steering FETs. The two situations are not identical:
TI regulates from a **fixed** 48.5 V rail into a 24 V string (~24 V of headroom to burn),
whereas this board's bank droops 48 -> 40 V into a 38 V string (2-10 V of headroom, **DERIVED**
~14 % average loss). The linear stage is therefore far less wasteful here than TI's sentence
implies, and it removes the inductor that STR-REQ-01/STR-REQ-11 make expensive. But the SOA
burden (D6-D8) is real and is the price. **This is a genuine source-vs-assignment conflict and
should be surfaced to the architect rather than silently resolved.**

**OPEN-2 - Vendors disagree on whether a millisecond pulse rating exists at all.** Cree (S6)
publishes no numeric pulse allowance and disclaims warranty outside spec. ams-OSRAM (S8)
publishes a surge rating that is microseconds-only. Yet S1 s2.4.1.2 reports that the OSLON
Black Flat it uses is specified for 1.5 A DC and "even data for the permissible pulse handling
capability up to peak pulses of 2.5 A" - a 1.67x pulse allowance that *is* published, on a
different part. Conclusion: the availability of a millisecond-scale pulse curve is per-part,
not per-vendor. **Resolution rule for the component-scout: either select a part whose datasheet
publishes a pulse-handling curve covering 5-200 ms, or stay inside the DC rating. Do not
interpolate between the two.**

**OPEN-3 - Is the PD ceiling 1.0 A (ICD) or 0.85 A (TPS2378 min)?** Requirements s3.2 / ICD
s8.2 states 1.0 A. S9 gives 0.85 A min / 1.0 A typ / 1.2 A max, and the foldback deglitch is
500 us min against the 800 us the requirement quotes. Designing to the typicals leaves no
margin on a worst-case PD. Needs confirming with the carrier owner; until then design to
0.85 A / 500 us (D11).

**OPEN-4 - Analogue-dimming chromaticity evidence is academic, not vendor.** D5 leans on S13
(SPIE, 2005) for the "<4-step MacAdam from 100 % to 3 %" figure. The vendor datasheets (S7,
S8) publish the chromaticity-vs-current curve but do not state an acceptance limit. Once a
specific emitter is chosen, re-check STR-REQ-14 against *that* part's curve rather than against
S13's general result.
