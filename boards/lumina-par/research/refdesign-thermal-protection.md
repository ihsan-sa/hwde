# refdesign-thermal-protection - LUM-PAR-A

Block: continuous-duty LED thermal management on FR4 inside a sealed
non-conductive enclosure, plus the protection chain (over-temperature,
ENABLE gating, 48 V bleed, inrush).

Scope note: this file contains TOPOLOGY and SIZING DECISIONS with citations.
No parts are selected here and no circuits are drawn. Every number is either
quoted from a cited primary source, or is arithmetic performed on cited
constants (marked `DERIVED:`), or is unsourced engineering opinion
(marked `JUDGEMENT:`).

## Sources used (all primary unless noted)

| Tag | Document | Where |
|---|---|---|
| **[CREE-AP37]** | Cree LED, *Optimizing PCB Thermal Performance for XLamp LEDs*, **CLD-AP37 REV 4A**, (c) 2010-2025 | https://downloads.cree-led.com/files/da/x/XLamp-PCB-Thermal.pdf |
| **[TI-2020]** | Texas Instruments, *AN-2020 Thermal Design By Insight, Not Hindsight*, **SNVA419C**, Apr 2010 rev Apr 2013 | https://www.ti.com/lit/an/snva419c/snva419c.pdf |
| **[OSRAM-AN052]** | ams-OSRAM, *Thermal management of LED light sources*, **AN052**, 2022-08-18 | https://look.ams-osram.com/m/5d74cfe57b5f9c6a/original/Thermal-management-of-LED-light-sources.pdf |
| **[HOFFMAN]** | Pentair / Hoffman, *Technical Information: Thermal Management - Heat Dissipation in Electrical Enclosures*, **Spec-00488 D**, (c) 2011 | https://safe.nrao.edu/wiki/pub/CICADA/GreenBankSpectrometer/Hoffman_Heat_Dissipation_Document.pdf |
| **[RITTAL]** | Rittal, *The Perfect Climate Inside Your Enclosure - Basic Climate Control Principles*, US573-WP-TR | https://www.rittal.com/us_en/apps/download/img/uploads/US573-WP-TR%20Perfect%20Climate%20Inside%20Your%20Enclosure.pdf |
| **[TI-SNIA037]** | Texas Instruments, *Analog Thermal Foldback With LED Drivers*, **SNIA037**, Jun 2020 | https://www.ti.com/lit/pdf/snia037 |
| **[TI-TMP390]** | Texas Instruments, *TMP390 Resistor-Programmable Temperature Switch* datasheet | https://www.ti.com/product/TMP390 |
| **[TI-2378]** | Texas Instruments, *TPS2378 IEEE 802.3at PoE High-Power PD Interface*, **SLVSB99C**, Mar 2012 rev Jul 2015 | https://www.ti.com/lit/ds/symlink/tps2378.pdf |
| **[TI-673]** | Texas Instruments, *Robust Hot Swap Design*, **SLVA673A**, Nov 2014 | https://www.ti.com/lit/an/slva673a/slva673a.pdf |
| **[TI-3409]** | Texas Instruments, *LM3409/HV P-FET Buck Controller for High-Power LED Drivers*, **SNVS602L**, Mar 2009 rev Jun 2016 | https://www.ti.com/lit/ds/symlink/lm3409.pdf |
| **[IEEE-1789]** | IEEE Std 1789-2015, *Recommended Practices for Modulating Current in High-Brightness LEDs for Mitigating Health Risks to Viewers* | https://ieeexplore.ieee.org/document/7118618 |
| **[BJB]** | Bridgelux + BJB, poke-in wire connectivity for Vero arrays (vendor press release, secondary) | https://www.bridgelux.com/bridgelux-and-bjb-announce-poke-availability-vero-series-arrays-0 |
| **[MOLEX]** | Molex Pico-EZmate harness for Bridgelux Vero (vendor/distributor, secondary) | https://www.digikey.com/en/product-highlight/m/molex-connector/pico-ezmate-harness |

---

## 0. The two numbers that decide this board

**D-T1. The enclosure wall, not the PCB, is the bottleneck.** A sealed
120 x 100 x 60 mm non-metallic box is a **~3.6 to 4.3 degC/W** thermal
resistance from internal air to room air. Nothing done on the PCB - copper
weight, via farms, MCPCB, a bigger internal heatsink - changes that number.

**D-T2. Therefore a fully sealed enclosure caps the fixture at roughly
3-4 W of LED electrical power**, i.e. **less than half the af envelope**
and about **one fifth of the at envelope**. The af case only "closes" on
the ICD's own 56 degC figure by simultaneously accepting a junction
temperature that the same requirements document rejects (s4). The at case
does not close by any margin at all.

Everything else in this file is subordinate to those two.

---

## 1. Getting LED heat off FR4 - what the numbers actually say

### 1.1 The board-to-still-air constant (this is the one that kills on-board emitters)

[TI-2020] section 3.1, Equation 9:

> Board Area (cm2) = 500 degC*cm2/W / (theta_JA - theta_JC)

i.e. **theta_CA = 500 degC*cm2/W divided by the board area, for a two-sided
PCB with solid copper fills on both sides convecting and radiating into
still air.** In imperial the same constant is **77.5 degC*in2/W**. The
underlying assumption is stated in [TI-2020] Table 1: the surface-to-air
heat transfer coefficient is taken as **h = 0.001 W/(cm2 degC) = 10 W/m2K**
(convection plus radiation), giving **1000 degC/W per 1 cm2 per side**.

[TI-2020] section 3.1 states the same thing as a rule of thumb:

> With only natural convection (i.e. no airflow), and no heat sink, a typical
> two sided PCB with solid copper fills on both sides, needs at least
> 15.29 cm2 (~2.37 in2) of area to dissipate 1 watt of power for a 40 degC
> rise in temperature.

Two explicit caveats from the same section, both of which this board
violates: "any enclosure for the PCB does not restrict the natural
convection of either side of the PCB", and the copper must run unbroken to
the board edges.

Cross-check from a second vendor: [OSRAM-AN052] Figure 18 models a TOPLED
on a 50 x 50 mm, 1.5 mm FR4 board, 35 um copper, still air, 25 degC, emissivity
0.9, 0.1 W. **Rth solder-point-to-ambient falls from ~350 K/W to ~150 K/W
as the cooling pad grows to ~35 mm2 per lead, and then flattens.**
150 K/W means that emitter can shed about **0.4 W** for a 60 K rise. That is
the honest ceiling for "SMT LED on bare FR4 in still air with no heatsink".

**DERIVED (from [TI-2020] 500 degC*cm2/W):**

| Configuration | Area | theta to internal air | Power for a 15 K copper rise |
|---|---|---|---|
| Whole 100 x 80 mm board, both faces free | 80 cm2 | **6.3 degC/W** | **2.4 W** |
| Whole board, bottom face blocked by the 11 mm mezzanine gap | 80 cm2, one side | **12.5 degC/W** | **1.2 W** |
| A generous 40 x 40 mm local pour, both faces | 16 cm2 | 31 degC/W | 0.48 W |

**D-T3. The daughter's own copper can shed on the order of 1-2 W total, not
7-8 W.** On-board emitters with no dedicated heatsink are fantasy at this
power by a factor of 4 to 8. This is not a marginal call.

### 1.2 Thermal vias - real numbers, and what they are actually for

All of [CREE-AP37]'s FR4 numbers are **"solder point THROUGH BOARD"** with
the board bolted to a heat sink; its footnote 2 states the simulation
assumes "the PCB is mounted to an infinite heat sink that maintains the back
side of the board at 25 degC". **Via arrays move heat through the laminate to
a heatsink. They do not create a heatsink.** Quoting them without a
heatsink on the back is the single most common way to talk yourself into an
impossible design.

Per-via thermal resistance, 1.588 mm board ([CREE-AP37] "Open Vias vs.
Filled Vias"):

| Via, 0.6 mm diameter | degC/W per via |
|---|---|
| Open, 35 um (1 oz) plating | **64** |
| Solder-filled | **42** |
| Copper-filled (solid) | **14** |
| Open, 70 um (2 oz) plating | **34** |

[TI-2020] section 3.2 gives an independent set for a 0.3 mm (12 mil) via:
**261 degC/W** at 0.5 oz plating, **140 degC/W** at 1 oz plating, **128 degC/W**
plated closed at 8 mil. The two vendors are not directly comparable
(different diameters and plating), but they agree on the ordering and on
the conclusion that plating thickness is worth roughly 2x.

Recommended array geometry, quoted verbatim from [CREE-AP37] "Recommended
Board Layouts":

> Cree LED recommends creating areas of 10-mil (0.254-mm) vias arranged on a
> 25-mil (0.635-mm) rectilinear grid. ... According to several PCB
> manufacturers, 10-mil holes and 25-mil spacing are reasonable and
> repeatable production choices when used with a 2-oz. plating solution.

Diminishing returns, [CREE-AP37] Chart 5: "increasing the number of vias
beyond **fourteen** shows little improvement. (This is the maximum
achievable density of the area normal to the LED thermal pad.)"
[TI-2020] section 3.2 says the same thing differently: "Place as many
thermal vias as will fit underneath the exposed pad to form an array, with
1 mm spacing."

**D-T4. Via array spec, if a thermal pad exists on this board at all:
0.254 mm drill on a 0.635 mm grid, 2 oz plating, >= 14 vias under the pad,
tented on the bottom side.** Open vias larger than 0.3 mm are a defect
generator, not a thermal improvement (see errata E-2).

### 1.3 Copper pour area - where it saturates

[CREE-AP37] Chart 1 (no vias): "for the 1.6-mm thick board, increasing the
thermal pad width beyond **12 mm** provides little improvement".
[CREE-AP37] Chart 6 (14 vias): "beyond a **6-mm** width, there is little
improvement in thermal resistance." [CREE-AP37] Chart 2 (MCPCB): "little
benefit to extending the thermal pad width beyond **6 mm**".

Reason, [CREE-AP37] "Summary Results" point 3: "adding additional vias and
increasing the width of the thermal pad beyond a certain point have
diminishing returns because of **thermal spreading resistance**."

**D-T5. Copper pour saturates at ~12 mm across on bare 1.6 mm FR4 and at
~6 mm across once a 14-via array is present. Pouring copper past that is
free weight, not free cooling.** Note this saturation is about getting heat
*into* the board; the 500 degC*cm2/W constant of s1.1 is about getting it
*out to air*, and that one does not saturate - it just needs area this board
does not have.

### 1.4 2 oz versus 1 oz - the answer depends on which path you are on

[CREE-AP37] Table 6 - measured, five XP-E LEDs per board, 700 mA, star
boards mounted to a heat sink with thermal adhesive:

| Board | Avg theta_pcb (solder point to heat sink), degC/W |
|---|---|
| 1 oz | **9.39** |
| 2 oz | **9.61** |
| 2 oz, filled | **9.65** |
| 4 oz | **8.40** |
| MCPCB (1.6 mm Al-clad) | **3.81** |

[TI-2020] section 3.3 - two 3 x 3 in two-layer boards, solid bottom
copper, spreading heat to their own surface, no heatsink:

> theta_JA = 28.3 degC/W for the first board [1 oz] and 21.2 degC/W for the
> board with thicker copper [2 oz]. This is a 25% improvement

and the same section's rule: "At least one ounce copper is recommended for
all DC-DC converter designs. Two ounce copper is recommended for designs
that dissipate more than 3 watts. Four ounce copper is recommended for
designs that dissipate more than 6 watts."

**D-T6. Copper weight buys ~25% when the board must spread heat laterally to
its own surface (TI). It buys essentially nothing (2% - inside measurement
noise) when the path is a via farm straight into a heatsink (Cree
measured).** Specify 2 oz only if the architecture ends up relying on the
board itself as the radiator - which, per D-T3, it must not.

### 1.5 Where FR4 stops being viable

[CREE-AP37] "Thermal Management Principles", first line:

> The technique in this application note is **not recommended for XLamp LEDs
> that consume more than 5 W of power**, such as MT-G2. This technique can
> be used for low-power applications.

That is Cree drawing the line at **5 W per LED package, on FR4, bolted to a
heat sink**. [OSRAM-AN052] s4.2 is softer but points the same way: "IMS
technology with improved dielectrics is preferable for many heat-intensive
applications (e.g. LED), especially for higher power classes."

**D-T7. With ~7.6-8.5 W (af) of emitter electrical power:**

- **Fantasy:** emitters on this 1.6 mm FR4 daughter with copper pour and vias
  and no heatsink. Off by 4-8x (s1.1).
- **Fantasy:** a single 7.5 W emitter package on FR4 with vias, even bolted
  to a heatsink - [CREE-AP37] disclaims its own technique above 5 W, and the
  board term alone (9.4 degC/W measured) eats the entire junction budget
  (s2.3).
- **Credible:** the emitters live on a separate MCPCB (measured 3.81 degC/W
  board term, [CREE-AP37] Table 6), bolted to a real heatsink, off this
  board, wired in by an internal harness. This is the standard LED-fixture
  answer and it is the one that has margin.
- **Credible-but-marginal:** emitters on this FR4 board, split into >= 4
  packages of <= 2 W each, each on a 14-via array, with an aluminium plate
  bolted across the top of the board. Buys nothing optically (the emitters
  are then wherever the connectors and keepouts allow), and the enclosure
  bottleneck of D-T1 still applies unchanged.

---

## 2. Sealed vs vented plastic enclosure

### 2.1 The vendor figure

[HOFFMAN] Spec-00488 D, "Heat Dissipation in Sealed Electrical Enclosures":

- Applies to "gasketed and unventilated enclosures".
- **"Non-metallic enclosures have similar heat transfer characteristics to
  painted metallic enclosures, so the graph can be used directly despite the
  difference in material."** This is the sentence that lets a plastic
  LUMINA box use this data at all.
- Surface area = 2[(A x B) + (A x C) + (B x C)] / 144 (inches -> ft2), all six
  faces, minus any face that cannot transfer heat.
- Worked example: "48 x 36 x 16 in. painted steel enclosure with 300 W ...
  Surface Area = 42 ft2 ... Input Power = 7.1 W/ft2 ... **Temperature Rise =
  approximately 30 F (16.7 C)**".
- "A safety margin of 25% is recommended."

**DERIVED from that example: 2.35 degC of internal-air rise per (W/ft2),
equivalently an overall heat-transfer coefficient of about 4.6 W/m2K over
the full six-face area.**

Cross-check, [RITTAL]: "k = heat transfer coefficient [W/m2K] **for steel
sheet, k = 5.5 W/m2K**; A = effective, heat loss-dissipating enclosure
surface area [m2]". Rittal's 5.5 is for steel and uses an *effective* area
that excludes mounted faces; Hoffman's implied ~4.6 is for painted metal and
non-metallic and uses all six faces. The two bracket the answer.

### 2.2 Applied to this fixture

Assumed box 120 x 100 x 60 mm (as given to this agent). All six faces free
(ceiling-mounted on standoffs).
Surface area A = 2(0.12*0.10 + 0.12*0.06 + 0.10*0.06) = **0.0504 m2 = 0.5425 ft2**.

**DERIVED enclosure thermal resistance, internal air to room air:**
- Hoffman coefficient: 2.35 / 0.5425 = **4.34 degC/W**
- Rittal k=5.5: 1 / (5.5 x 0.0504) = **3.61 degC/W**
- Working range: **3.6 - 4.3 degC/W** (Rittal is the optimistic end, and it
  is a steel figure).

Heat actually inside the box (requirements s4): af **8.9 - 10.8 W**
(6.5-8.4 W daughter + 2.4 W carrier); at **17.7 - 20.7 W** (14-17 + 3.7).

| Case | Box heat | Internal-air rise | Internal air @ 25 degC room | Internal air @ 40 degC room |
|---|---|---|---|---|
| **af** | 8.9-10.8 W | **32 - 47 K** | **57 - 72 degC** | **72 - 87 degC** |
| **at** | 17.7-20.7 W | **64 - 90 K** | **89 - 115 degC** | **104 - 130 degC** |

### 2.3 Verdict on the ICD's 56 degC / 69 degC

**D-T8. ICD s7.6's 56 degC (af) is plausible but sits at the optimistic edge,
and only survives if room ambient is 25 degC.** It implies a 31 K rise, which
matches the Rittal-optimistic end of the bracket. At the requirements'
own ASSUMED 40 degC external ambient it becomes 72-87 degC, not 56 degC.

**D-T9. ICD s7.6's 69 degC (at) is not plausible and is internally
inconsistent with its own af figure.** Convection is close to linear in
delta-T at this scale, so roughly doubling the box heat must roughly double
the rise. The ICD's own af point (31 K rise at ~9.9 W) scaled to the at
point (~19.2 W) gives a **60 K rise, i.e. ~85 degC**, not 69 degC. The
independent Hoffman/Rittal calculation is worse still (89-115 degC at 25 degC
room). **The ICD's at figure is optimistic by 20-46 K.** This is a blocking
issue to raise against LUM-CAR-A (ICD s10 change process), not something a
daughter can absorb.

### 2.4 The junction budget, and why sealed does not close

Target: red AlInGaP junction <= 100 degC for colour and lifetime stability
(requirements s4). LED heat ~7.5 W (af).

**DERIVED**, using the ICD's own (optimistic) 56 degC internal air:
total junction-to-internal-air budget = (100 - 56) / 7.5 = **5.9 degC/W**.

Split it:
- Die-to-slug inside a 4-in-1 package, ~1.9 W/die at a per-die Rth_j-sp of
  roughly 6-10 degC/W (`JUDGEMENT:` - the component-scout owns the real
  number): **11 - 19 K**, leaving **25 - 33 K** for everything downstream.
- At 7.5 W that is **3.3 - 4.4 degC/W from solder point to internal air.**
- [CREE-AP37] Table 6 measured **MCPCB alone = 3.81 degC/W** (solder point to
  heat sink). **The board alone consumes the whole remaining budget and
  leaves zero for the heatsink.**
- On 1.6 mm FR4 with a 14-via array the board term is **9.4 - 9.6 degC/W**
  ([CREE-AP37] Table 6) - it misses on its own by 2-3x.

And the heatsink term cannot be bought cheaply either. **DERIVED from
[TI-2020]'s 500 degC*cm2/W:** a 2.0 degC/W natural-convection surface needs
**~250 cm2** of two-sided exposed area. The whole enclosure's external
surface is 504 cm2. An internal heatsink of half the enclosure's total
surface area, inside a box that then cannot get rid of the heat anyway, is
not an answer.

**D-T10. Sealed-box power ceiling (DERIVED).** Hold internal air at 45 degC
(which leaves a 55 K junction budget, i.e. ~7 degC/W, i.e. genuinely
buildable) with a 25 degC room and a 4.0 degC/W box: total box heat <= 5.0 W.
Minus the carrier's 2.4 W leaves **~2.6 W of daughter heat, i.e. roughly
3-4 W of LED electrical power.** That is **less than half the af envelope**.

**D-T11. Therefore only two architectures close, and both are enclosure
decisions, not PCB decisions:**
1. **Vent the enclosure** (requirements Q6 option b) so internal air tracks
   room ambient within ~10-20 K instead of ~35-45 K. `JUDGEMENT:` no cited
   figure was found for vented small-box performance; the correct way to
   write this is as an *acceptance criterion on the enclosure* ("internal
   air within 15 K of room ambient at full output, measured"), not as an
   assumed number.
2. **Conduct the LED heat through the enclosure wall** to a shrouded,
   non-touchable, non-earthed heatsink (requirements Q7 option b). This
   bypasses the internal-air bottleneck entirely and is the only sealed
   option that works.

Doing neither, and instead spending money on MCPCB, 2 oz copper and via
farms, moves numbers that are not the binding constraint.

---

## 3. Remote LED module on a heatsink - the wiring interface

### 3.1 What LED fixtures actually do

Standard practice for connecting a heatsink-mounted LED module (COB or
multi-die array) to a driver board, in rough order of prevalence in
production luminaires:

1. **Poke-in / push-in wire terminals integrated into the LED holder.**
   Bridgelux and BJB co-developed exactly this for the Vero COB family:
   "with poke-in connectivity, customers benefit from simplified
   manufacturing and assembly processes, with secondary connector and holder
   components not required and integration of arrays into fixtures more
   streamlined without the need for soldering" [BJB]. WAGO sells the same
   idea as back-side wiring for LED modules.
2. **Low-profile wire-to-board harness.** Molex Pico-EZmate harnesses mate
   with an integrated header on select LED arrays [MOLEX]; JST PH/PA-class
   2.0 mm parts are the generic equivalent.
3. **Solder pads on the module** with flying leads - lowest cost, worst
   serviceability.

**D-T12. For LUM-PAR-A the interface is an internal wire-to-board header on
the daughter (2.0-2.54 mm pitch, latched), 6-10 conductors:** 4 LED drive
pairs (or 4 anodes + common cathode, depending on the driver topology the
architect picks) **plus the 2-wire NTC pair from the module.** A poke-in
terminal on the *module* end is normal; the *daughter* end wants a latched
header so the harness cannot be pulled off in a ceiling fixture.

### 3.2 Consequences of the floating-PoE heatsink

ICD s9 is unambiguous and this block inherits all of it:

- The daughter, its drivers, its LED wiring **and any heatsink the module
  sits on are at PoE potential** (up to 57 V above earth).
- "If the heatsink is touchable, metal, or shares a mount with anything
  earthed, the non-isolated topology is non-conformant."

**D-T13. Keep +48V_SW off the LED harness entirely.** There is no reason to
put it there. With only LED drive (<= ~12 V string voltage) and the NTC on the
harness, the ICD s5.4 **0.60 mm** outer-copper rule (IPC-2221B B2, 51-100 V,
57 V worst case) does **not** apply to the harness or its header - only the
standard fab minimum does. Tapping 48 V onto the harness would drag the
0.60 mm regime, 100 V capacitors and the 0805-minimum resistor rule out to
the end of a wire, for no benefit.

**D-T14. Couple the LED module's metal substrate thermally but isolate it
electrically from board GND** (dielectric thermal pad, insulating shoulder
washers on the screws), matching the requirements' own Q7 recommendation.
Rationale: board GND is the floating PoE return; bonding the heatsink to it
makes the heatsink a live conductor at up to 57 V above earth, and then a
single accessibility failure (a cracked shroud, an earthed ceiling bracket)
breaks the whole compliance argument at once. An MCPCB's own dielectric
already provides isolation between the emitter and the aluminium base; the
exposure is the mounting hardware, not the laminate.

**D-T15. ICD s9's "no external connector of any kind" is about the enclosure
wall, not about wires.** s9 itself anticipates the off-board module ("if the
LED module is on a separate heatsink ... that heatsink and its wiring are at
PoE potential too"), which is only meaningful if wiring to an off-board
module is expected. **This still needs an explicit human confirmation
(requirements Q5) and is carried in OPEN below** - it is not this agent's to
close.

---

## 4. Over-temperature protection independent of firmware (PAR-REQ-12)

### 4.1 What the proven topologies are, and what each one actually protects

| Topology | Protects | Fit here? |
|---|---|---|
| **Driver IC internal thermal shutdown.** [TI-3409] s8.4.2: "The threshold for thermal shutdown is 160 degC with 15 degC of hysteresis". | The **driver die**, nothing else | **Not sufficient for PAR-REQ-12.** 160 degC is far above any temperature the emitter survives, and it senses the wrong part |
| **Analog thermal foldback via the driver's current-set pin.** [TI-SNIA037]: NTC in the bottom leg of a divider into the driver's IADJ pin; the knee point is set by the bias resistor (worked example: 16.9 kohm sets a 115 degC knee, current derating from 1.2 A at 115 degC to 1.1 A at 150 degC) | The **emitters**, gracefully, with no firmware | **Yes - as the first layer.** It reduces output rather than killing it, which is what a lighting fixture should do first |
| **Dedicated temperature-switch IC.** [TI-TMP390]: dual-channel, hot and cold trips, thresholds and hysteresis (5/10/20 degC) set by two E96 resistors, open-drain outputs, 0.5 uA | Whatever the **IC's own package** is soldered next to | **Yes - for the on-board drivers.** Useless for a remote emitter, because it senses its own die |
| **NTC + comparator with hysteresis pulling driver EN low** | Whatever the **NTC** is bonded to | **Yes - as the hard backstop for the emitters** |

**D-T16. Three layers, in this order:**
1. **Analog foldback** into the drivers' current-set pin from the module NTC
   ([TI-SNIA037] topology). Graceful, firmware-free, and it is the layer
   that keeps the fixture lit.
2. **Hard shutdown**: the same NTC into a **window comparator** whose output
   pulls every driver's enable low (details in s4.3).
3. **On-board over-temperature** for the drivers themselves: either a
   resistor-programmed switch IC ([TI-TMP390] class) or a second NTC into a
   second comparator channel. Its output joins the same enable-kill node and
   pulls `FAULT` low.

### 4.2 One sensor or two - resolved

**The two duties of the emitter NTC are electrically compatible; the
failure modes are not.**

- **Compatible.** The comparator's input bias current is nA-to-pA, so
  paralleling a comparator input onto the divider node adds no meaningful
  load. The ADC-facing requirement (ICD s3.3: source impedance <= 10 kohm) is
  unchanged. **DERIVED sizing:** with a 10 kohm fixed leg and a 10 kohm NTC,
  the divider Thevenin impedance is R_fixed || R_ntc, maximum **5.0 kohm** at
  25 degC and falling monotonically as the NTC heats. Comfortably inside the
  10 kohm ceiling at every temperature of interest. A series RC filter at the
  ADC pin must be counted into that budget (keep the series R <= ~1 kohm).
- **Not compatible - the failure mode.** In *either* divider orientation, an
  **open NTC or a broken harness conductor reads as "cold"** and silently
  disables the protection. A single-comparator over-temperature trip is
  therefore fail-dangerous against the most likely fault in an off-board
  module (a wire).

**D-T17. One physical sensor is enough for the emitters, but it must feed a
WINDOW comparator, not a single-threshold one.** Trip on over-temperature
**and** on out-of-range (implausibly cold = open circuit, or rail-pinned =
short). That single change converts the fail-dangerous case into a
fail-safe one and removes the need for a redundant emitter sensor.

**D-T18. A second, independent sensor is still required - but for the
drivers, not for redundancy on the emitters.** The emitter NTC is on the
module, downstream of a harness; it tells you nothing about a driver
inductor cooking inside the enclosure. This is the [TI-TMP390]-class part,
placed next to the hottest driver stage. So: **two sensors, two jobs, not
two sensors for one job.**

### 4.3 Where the sensors physically sit

[CREE-AP37] "Temperature Verification Measurements" defines the reference
point the whole LED industry uses: a thermocouple attached "to the top
copper layer **close to the thermal pad**", with the ambient sensor placed
"at least 2 mm away from the heat sink and/or illumination source and not in
the path of illuminance".

**D-T19. Sensor placement:**
- **Emitter NTC: on the LED module, on or immediately adjacent to the emitter
  thermal pad copper, within a few mm.** Not on the daughter. A sensor on
  the daughter measures internal air plus driver self-heating - a lagging,
  wrong-magnitude proxy that will either trip late (emitters already cooked)
  or trip on a hot day with cold LEDs.
- **Driver sensor: on the daughter, on the copper of the hottest switching
  stage**, and outside the ICD s7.6 DC-DC hot zone (2,46)-(36,68) so it reads
  this board's drivers and not the carrier's converter radiating from below.
- Plan a bare-copper thermocouple pad next to the emitter thermal pad for
  the P8/bring-up verification measurement.

### 4.4 Trip-point sizing - and the uncomfortable finding

**DERIVED:** with internal air at the ICD's 56 degC (af) and a healthy
solder-point-to-air chain, the emitter solder point sits somewhere around
85-95 degC in **normal** operation. A useful over-temperature trip must sit
above worst-case-normal plus margin and below the emitter's rated maximum
solder-point temperature. **That leaves a very narrow band** - typically a
trip near 105-110 degC with 10-15 K of hysteresis, against a normal operating
point only 10-20 K below it. **A protection threshold that close to the
normal operating point is a nuisance-trip generator, and it is a direct
symptom of D-T8/D-T10, not of the protection design.** Fixing the enclosure
widens this band; nothing in the protection circuit can.

---

## 5. The 48 V bleed path and the inrush limiter

### 5.1 What the PD actually does (this is the number to size against)

[TI-2378] Electrical Characteristics, the TPS2378-class part the carrier
uses:

| Parameter | Min | Typ | Max | Unit |
|---|---|---|---|---|
| Current limit (V_RTN = 1.5 V) | **0.85** | **1.0** | 1.2 | A |
| Inrush current limit | 100 | **140** | 180 | mA |
| Foldback threshold, V_RTN rising | 11 | **12.3** | 13.6 | V |
| **Foldback deglitch time** | **500** | **800** | 1500 | **us** |
| Pass MOSFET rDS(on) | 0.2 | 0.42 | 0.75 | ohm |

Mechanism, [TI-2378] s7.3.5 and the overload description:

> An overload on the pass MOSFET engages the current limit, with
> V(RTN-VSS) rising as a result. If V(RTN-VSS) rises above approximately
> 12 V for longer than approximately 800 us, the current limit reverts to
> the inrush value.

That is the ICD's warning, with the datasheet behind it: exceed ~1 A for
longer than the deglitch and the PD drops to **140 mA**, which browns out
the whole fixture.

**D-T20. Size the daughter's inrush so that total PD input current never
approaches the 0.85 A *minimum* current limit - not the 1.0 A typical, and
emphatically not the connector's 5.4 A rating.**
**DERIVED budget at 48 V:** carrier housekeeping 2.4-3.7 W = 50-77 mA;
daughter af steady 8.6-9.3 W = 180-195 mA. Total steady ~230-270 mA.
**Headroom to the 0.85 A min limit is therefore ~0.58 A**, and a sane design
target is **<= 0.3 A of daughter inrush**, leaving ~2x margin. Alternatively
(worse, but valid): if a transient does hit the limit it must be shorter
than the **500 us minimum** deglitch - designing against the 800 us typical
is a mistake.

Also from [TI-2378] revision history, a footgun worth quoting: "Additional
loading applied between V_VDD and V_RTN during the inrush state may prevent
successful PD and subsequent converter start up."

### 5.2 Inrush limiter topology

[TI-673] s2.2.2, the standard answer:

> An alternative is to limit the inrush current with a dv/dt control circuit
> shown in Figure 6. Cdv/dt limits the slew rate of the gate and the output
> voltage, which in turn limits the inrush current.

**D-T21. Topology: series N-channel MOSFET (low side) or P-channel
(high side) with a gate-to-drain capacitor setting the output slew rate**,
gate driven from ENABLE through a resistor. Inrush = C_bulk x dV/dt.

**DERIVED sizing rule:** dV/dt = I_target / C_bulk. For I_target = 0.3 A:
- C_bulk = 10 uF -> 30 V/ms -> 48 V ramp in **1.6 ms**
- C_bulk = 47 uF -> 6.4 V/ms -> **7.5 ms**
- C_bulk = 100 uF -> 3.0 V/ms -> **16 ms**

**MOSFET stress must be checked against SOA, not just Rds(on)** ([TI-673]
s2.3): during the ramp the FET dissipates V_DS x I_inrush, worst case at
t=0 (48 V x 0.3 A = **14.4 W**, decaying linearly to zero), so the energy is
~ (1/2) x 14.4 W x t_ramp, i.e. **12 mJ at 1.6 ms, 115 mJ at 16 ms**. [TI-673]
s2.3.1 warns that SOA at high V_DS is much worse than the DC ratings suggest
("the MOSFET can handle 80 A at 10 V (800 W) or 4 A at 70 V (280 W)" on the
10 ms curve) and that SOA data is at T_case = 25 degC and must be derated -
inside a 56-69 degC box that derating is severe.

**D-T22. Two soft-starts must not fight.** ICD s8.2: "The carrier's eFuse
dV/dT is set *fast* and its limit sits **above** the daughter's inrush
level, deliberately". So the daughter's ramp is the slow one and must
dominate. Do not add a second slow ramp inside the daughter's own DC-DC or
LED drivers on top of the hot-swap ramp; the composite start time then
lands unpredictably against the PSE's 80 ms window.

### 5.3 Bleed path

ICD s8.2 / CAR-REQ-17: mandatory if any 48 V net is tapped, because "the
carrier deliberately fits no series diode on `+48V_SW`, so the daughter's
bleed path is not stranded above the carrier's".

**D-T23. Topology: a fixed resistor permanently across the daughter's own
48 V bulk capacitance, on the daughter side of any series element.** It is a
defined-state requirement, not a safety requirement: 57 V DC is below the
IEC 62368-1 ES1 limit of 60 V (requirements s8, ICD s9), and a 10 uF bulk at
48 V stores only 11.5 mJ (**DERIVED**).

**DERIVED sizing:** pick R for the discharge time constant, then check
dissipation and the ICD's package rule.
- 100 kohm across 10 uF -> tau = 1.0 s, ~5 s to fully collapse,
  P = 57^2/100k = **32 mW**.
- 47 kohm across 47 uF -> tau = 2.2 s, P = **69 mW**.
- ICD s5.4 is binding on the part: **"Any resistor sitting across the 48 V
  domain must be 0805 or larger (0402/0603 parts are typically 50-75 V
  working) or split into two in series. This bites the mandatory bleed
  resistor"**. Two 0603s in series is the cheaper route if board area is
  tight; one 0805 is the simpler route.

### 5.4 If the architecture takes power ONLY from +12 V

**D-T24. What disappears:**
- The **bleed path** obligation (CAR-REQ-17 is conditioned on tapping a 48 V
  net). Gone.
- **100 V capacitors** and the **0805-minimum resistor** rule. Gone - there
  are no components on a 48 V net.
- The 48 V **hot-swap MOSFET and its SOA analysis**. Gone.

**D-T25. What does NOT disappear:**
- **The 0.60 mm outer-layer clearance.** requirements s8 calls the >30 V
  condition "**YES, unconditionally**" because `+48V_SW` is present on J3
  pins 1/3/5 whether or not this board taps it. The pads exist, the DRC rule
  applies, and `check_creepage.py` will fail P8 if it is not set up at P5.
- **The inrush obligation.** It changes limit, not existence. The +12 V rail
  is produced by the carrier's 48->12 converter, whose input is the PD.
  **DERIVED:** a 2.0 A step on +12 V is 24 W, which reflects to roughly
  **0.55 A at 48 V** at 90% efficiency - most of the PD budget by itself -
  and it also hits the carrier's **2.0 A converter OCP** (ICD s6.2). So an
  inrush limiter (or a genuinely soft-starting driver) is still required,
  sized against 2.0 A on the 12 V side and against the same ~0.85 A PD limit
  once reflected.
- **"No path may energise anything on this board from `+12V` or `+3V3` while
  `+48V_SW` is off"** (ICD s3.3 / s8.3). This is *more* binding in a
  12 V-only architecture, not less, because +12 V and +3V3 are live hundreds
  of ms before `+48V_SW` closes. See s6.
- **The ENABLE gating obligation** (ICD s8.2). Entirely unaffected.

---

## 6. ENABLE gating of the LED driver output stages

### 6.1 The contract

ICD s8.2, verbatim requirements on the daughter: fit a **100 kohm pull-down**
on ENABLE; **"Gate every output stage with ENABLE - LED driver EN pins, gate
drivers, the cap-bank charge path"**, because **"a carrier PWM pin can
produce a ~60 us glitch at power-up. ENABLE is the thing that makes that a
no-op"**; and **"Never latch ENABLE locally"**. ENABLE is push-pull active
high, driven from a GPIO chosen for having no documented power-up glitch,
with a 10 kohm pull-down on the carrier as the passive fail-safe (CAR-REQ-08).

### 6.2 The footgun that decides the topology

**On a large fraction of buck LED-driver ICs, the EN pin *is* the PWM
dimming input.** [TI-3409] is the canonical example: its typical
characteristics are titled "Internal EN Pin PWM Dimming", "20 kHz 50% EN Pin
PWM Dimming", and s8.4.1 defines EN as the shutdown control
("low-power shutdown (typically 110 uA) by grounding the EN terminal (any
voltage below 0.5 V) ... During normal operation this terminal should be
tied to a voltage above 1.74 V"). There is no second, independent enable.

**D-T26. Do not plan on "wire PWM to the dim pin and ENABLE to the EN pin".
On many candidate drivers those are the same pin, and the ones that do have
both often make EN the slow path.** The ENABLE gate must therefore be a
separate element in front of the driver.

### 6.3 The proven pattern

**D-T27. Gate the PWM in logic: `DRIVER_IN = PWM AND ENABLE`, one 2-input
AND gate per channel (or a dual/quad), powered from +3V3.**

Why this satisfies every clause at once:
- The ~60 us power-up PWM glitch is a **no-op**: with ENABLE low the AND
  output is low regardless of what PWM does, and the driver never starts.
- It is **combinational** - no latch, no state, nothing to clear. "Never
  latch ENABLE locally" is satisfied by construction, and the whole chain
  de-asserts within one carrier reset.
- The +3V3 rail is live before `+48V_SW`, so the gate is already holding the
  drivers off during the hundreds of ms while the 48 V switch is open. This
  is what makes the ICD s3.3 rule ("no path may energise anything from +12V
  or +3V3 while `+48V_SW` is off") hold **even in a 12 V-only
  architecture**: ENABLE is the same signal that closes the carrier's 48 V
  switch, so gating on ENABLE makes the LED stage and the 48 V rail come up
  together by definition.

**D-T28. Supporting rules:**
- **100 kohm pull-down at the daughter's ENABLE pin**, at the connector end,
  before any series element (ICD s8.2 verbatim). Combined with the carrier's
  10 kohm this is ~9.1 kohm to GND; the carrier's push-pull driver must source
  ~0.36 mA - trivial, but note it if the architect adds further loads.
- **The AND gate's own input must be pulled down too**, or specify a gate
  with defined behaviour on a floating input; an unpowered/undriven carrier
  must not float the gate input high.
- **The over-temperature comparator kills the same node**, by pulling the
  gated-enable line low (open-drain wire-OR onto the AND output side, or a
  third AND input). If the architect wants over-temperature to *latch*, the
  latch must clear when ENABLE de-asserts - a latch that survives an ENABLE
  cycle violates "the whole chain must de-assert within one carrier reset".
- **`FAULT` is open drain, active low, never driven high** (ICD s3.3) - the
  over-temperature detector's output type must match.
- Do **not** implement the gate by switching the drivers' supply rail with a
  load switch as the *only* mechanism: that adds a second soft-start
  (conflicts with D-T22) and a rail collapse time that is not bounded by the
  ENABLE edge.

---

## 7. Flicker - does 9.766 kHz survive scrutiny?

[IEEE-1789] Clause 8, Recommended Practice 1 (Low-Risk Level), verbatim:

> Below 90 Hz, Modulation (%) is less than 0.025 x frequency.
> Between 90 Hz and 1250 Hz, Modulation (%) is below 0.08 x frequency.
> **Above 1250 Hz, there is no restriction on Modulation (%).**

Recommended Practice 2 (NOEL) uses Mod% < 0.0333 x f above 90 Hz, and
[IEEE-1789] s8.1.2.3 works the PWM case explicitly:

> Using Figure 20, the recommended practice for PWM dimming at 100%
> modulation depth is that the frequency satisfies f > 1.25 kHz. ... The
> recommended NOEL for PWM dimming is 3 kHz, which can be seen in Figure 18
> and can also be derived by using Recommended Practice 2 and solving
> 100% = 0.03333 x f_Flicker.

The empirical basis for the 3 kHz ceiling, [IEEE-1789] s7.4.5: phantom-array
discrimination during saccades persisted to 2000-2500 Hz mean threshold and
"fell to chance (random guessing) at 3000 Hz".

**D-T29. The carrier's 9.766 kHz default is 3.25x above the NOEL breakpoint
and 7.8x above the low-risk breakpoint. It is compliant with IEEE 1789-2015
at 100% modulation depth with no conditions attached, and there is no
flicker-health argument for changing it.** Since ICD s3.3 makes changing the
PWM frequency a negotiation with the carrier owner (LEDC timers 2/3), this
closes that question in the "leave it alone" direction.

**D-T30. Flicker compliance is not the dimming problem.** [IEEE-1789] bounds
*modulation depth versus frequency*; it says nothing about whether a
constant-current driver can reproduce a 1.4-6.1 us on-time cleanly
(requirements Q9). The real low-end dimming limit is the driver's PWM
settling time, and that is a driver-selection question for the
component-scout, not a flicker-standard question.

---

## 8. Layout constraints for interface-spec

| # | Constraint | Source |
|---|---|---|
| L-1 | **0.60 mm outer-layer copper clearance around every 48 V net, board-wide** (IPC-2221B B2, 51-100 V, 57 V worst case), including through the board under any 48 V antipad (0.10 mm inner). Applies even if 48 V is never tapped, because the J3 pads exist. Set up in DRC at P5; `check_creepage.py` implements only the uncoated columns, so 0.13 mm is not claimable | ICD s5.1, s5.4; requirements s3.3 |
| L-2 | **Any resistor across the 48 V domain: 0805 or larger, or two in series.** Bites the bleed resistor and any 48 V rail-sense divider | ICD s5.4 |
| L-3 | **100 V capacitors on the 48 V domain** (63 V insufficient at 57 V after ceramic DC-bias derating) | ICD s5.4 |
| L-4 | **Thermal via array (if any thermal pad exists on this board): 0.254 mm drill on a 0.635 mm rectilinear grid, 2 oz plating, >= 14 vias under the pad.** More than ~14 buys nothing | [CREE-AP37] Recommended Board Layouts; Chart 5 |
| L-5 | **Tent thermal vias with soldermask on the bottom side** to stop solder wicking, or hold via inner diameter to 0.25-0.30 mm | [CREE-AP37] "Solder voiding in open PTH vias" |
| L-6 | **Thermal pad width: no benefit beyond ~6 mm with a via array, ~12 mm without, on 1.6 mm FR4** | [CREE-AP37] Charts 1 and 6 |
| L-7 | **Unbroken ground pour from the heat source to the board edges; keep trace breaks parallel to heat flow, never perpendicular.** TI measured a 5.5 degC penalty for a perpendicular break vs 1.5 degC for a parallel one on otherwise identical boards | [TI-2020] s3.4 |
| L-8 | **Do not specify 2 oz copper for a via-farm-into-heatsink path** (measured 9.39 vs 9.61 degC/W, 1 oz vs 2 oz - no benefit). Specify it only if the board itself is the radiator | [CREE-AP37] Table 6; [TI-2020] s3.3 |
| L-9 | **Any heatsink or metal bracket bolted to this board must clear the ICD s7.6 antenna column (88,25)-(100,55), which forbids metal components and copper on every layer**, and must clear the DC-DC hot zone (2,46)-(36,68) | ICD s7.6 |
| L-10 | **Keep the driver over-temperature sensor outside the DC-DC hot zone**, or it reads the carrier's converter 11 mm below rather than this board's drivers | ICD s7.6 |
| L-11 | **NTC sense pair: route as a differential-ish pair away from switching nodes; total series R at the ADC pin <= ~1 kohm so the divider's 5 kohm Thevenin plus filter stays under the ICD's 10 kohm ceiling** | ICD s3.3; DERIVED |
| L-12 | **Keep +48V_SW off the LED harness and off the harness header** - otherwise L-1/L-2/L-3 propagate to the connector and the module | D-T13 |
| L-13 | **Provide a bare-copper thermocouple pad adjacent to the emitter thermal pad** (and one on the heatsink) for the bring-up thermal verification | [CREE-AP37] "Temperature Verification Measurements" |
| L-14 | **Hot-swap MOSFET (if 48 V is tapped): SOA-check at full V_DS, derated for 56-69 degC ambient, not at 25 degC case** | [TI-673] s2.3.1 |
| L-15 | **Any test point carries the ICD s9 bench-hazard warning**: an earthed probe breaks PD signature detection (detection currents are a few hundred uA) | ICD s9; requirements s2.5 |

---

## 9. Errata / footguns

- **E-1. Cree's FR4 thermal numbers assume a heatsink on the back.**
  [CREE-AP37] footnote 2: "we assume the PCB is mounted to an infinite heat
  sink that maintains the back side of the board at 25 degC". Every theta_pcb
  in that document is board-to-heatsink. Quoting 9.4 degC/W as if it were
  board-to-air is off by more than an order of magnitude.
- **E-2. Open thermal vias larger than 0.3 mm wick solder during reflow.**
  [CREE-AP37]: voids under the package raise interface resistance, and
  "the solder may overfill the hole leading to bumps on the bottom of the
  board that can reduce the contact area between the board and the heat
  sink" - i.e. the defect degrades the *heatsink* joint too, not just the
  via.
- **E-3. Cree's own technique is disclaimed above 5 W per LED package.**
- **E-4. Plating vias closed is expensive.** [TI-2020] s3.2: "Plating closed
  the thermal vias can double or triple the cost of your PCB design. A more
  economical option is to ask for 1 oz plating on standard 12 mil vias, with
  perhaps a 10-20% cost adder." At JLC, POFV (resin-filled, copper-capped
  via-in-pad) is free on 6-20 layer boards but is a paid option on 4-layer -
  which matters if this board ends up 4-layer with via-in-pad.
- **E-5. TPS2378 foldback is a 500 us worst case, not 800 us.**
  [TI-2378] Electrical Characteristics: min 500 / typ 800 / max 1500 us.
  Designing to 800 us leaves no margin.
- **E-6. TPS2378 current limit minimum is 0.85 A, not 1.0 A.** The ICD's
  "1.0 A operating current limit" is the *typical*. Size against 0.85 A.
- **E-7. Loading during the PD inrush phase can prevent start-up entirely.**
  [TI-2378] revision history: "Additional loading applied between V_VDD and
  V_RTN during the inrush state may prevent successful PD and subsequent
  converter start up."
- **E-8. On common buck LED drivers the EN pin IS the PWM dim pin**
  ([TI-3409]). Any architecture assuming a spare, independent enable input
  on the driver needs that verified per candidate part.
- **E-9. Driver internal thermal shutdown does not protect the LEDs.**
  [TI-3409] s8.4.2: 160 degC with 15 degC hysteresis - far above any survivable
  emitter temperature, and it senses the driver die.
- **E-10. A single-threshold NTC comparator is fail-dangerous against the
  most likely fault.** An open NTC or a broken harness wire reads "cold" in
  both divider orientations. Use a window comparator (D-T17).
- **E-11. Do not copy a MOV-to-earth surge network out of a PoE reference
  design.** ICD s9: an unearthed PD needs none, and there is no earth to
  connect it to.
- **E-12. The board is a mezzanine.** Its bottom face convects into an 11 mm
  gap above another dissipating board. Halving the effective radiating area
  (s1.1) is the optimistic reading; the carrier's 2.4-3.7 W radiating up into
  that gap is the pessimistic one.
