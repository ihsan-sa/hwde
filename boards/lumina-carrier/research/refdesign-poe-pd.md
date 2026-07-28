# Reference-design decisions - block `poe-pd` (LUM-CAR-A PoE PD front end)

**Board:** LUM-CAR-A | **Block:** poe-pd | **Date:** 2026-07-28
**Scope:** topology decisions extracted from vendor reference designs. No schematic fragments,
no board files, no layouts copied. Every decision carries a primary-source citation; anything
uncited is marked `OPINION` or `DERIVED`.

---

## Headline: the brief's own named reference part cannot satisfy D-01

D-01 requires an 802.3at Type 2 power stage whose **only** Type-1 pin-down is the class
resistor. The **Skyworks Si3402-B (and its successor Si3402-C) are IEEE 802.3 Type 1 parts,
Class 3 and below.** There is no Class 4 setting, so no resistor change can upgrade an Si3402
design to Type 2 - the upgrade would be a respin. The family must be rejected for this board.

- "The Si3402 supports IEEE 802.3 Type 1 (Class 3 and below) Powered Device applications."
  - [Si3402-B data sheet, Rev 1.1](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si3402-B.pdf), p.1 Description
- Table 7 "Class Resistor Values" stops at Class 3 (48.7 ohm); there is no Class 4 row.
  - Si3402-B data sheet, section 3.2.3, Table 7
- Revision history records: **"Deleted references to Class 4 operation."** An earlier revision
  claimed Class 4 and the claim was withdrawn. Secondary sources still repeating "Class 4" are
  stale.
  - Si3402-B data sheet, Revision History
- Same restriction on the newer -C: "The Si3402-C supports IEEE 802.3 Type 1 (Class 3 and
  below) Powered Device applications."
  - [AN1050, Using the Si3402-C PoE PD Controller in Isolated and Non-Isolated Designs](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN1050.pdf), Introduction

The "~10 W regulated" figure the requirements quote (section 3.2) is real but is a **Type-1
statement**: "The powered device (PD) must not consume more than 12.95 W (PD input power for
class 3), which translates to no more than 350 mA (Type 1) of steady state input current,
allowing for 20 ohm of cabling resistance ... This means that with practical conversion
efficiencies, approximately 10 W of regulated power is available to PD applications."
([AN956 Rev 0.2](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN956.pdf), p.3).
It stays valid for the af build-1 column; it says nothing about the at column.

---

## Decisions

### D1 - Reject the Si3402-B/-C family; select a Type-2-capable PD interface IC
**Why:** Type 1 only (see above). Keeping it would make D-01's "resistor change only, no
respin" impossible, which is the single binding constraint on this block.
**Source:** Si3402-B DS p.1 + Table 7 + Revision History; AN1050 Introduction.

### D2 - Topology: separate PD interface IC + separate >=60 V buck, not an integrated PD+DC-DC part
**Why (two independent reasons):**
1. D-02 already requires the raw PD rail at the expansion connector. On a PD interface IC that
   rail *is* the VDD-to-RTN node after the hot-swap FET, so splitting the functions costs
   nothing and gives a clean tap point.
2. Using a PD controller's *integrated* single-switch PWM in a **non-isolated buck** is not a
   drop-in. Kinetic AN162: a low-side buck "requires level shifting two signals. The FET gate
   drive signal must be shifted from the IC controller to the floating source node of the
   switching FET, and the FET current signal must be shifted down to the IC controller"; the
   high-side buck instead needs the feedback signal level-shifted. Both need discrete
   transistor networks or a gate-drive transformer. A standalone wide-Vin buck IC with its own
   internal bootstrap high-side driver, referenced to RTN, avoids the whole problem.
**Source:** [Kinetic Technologies AN162 Rev 04a (Jan 2022)](https://www.kinet-ic.com/AN162-04a),
"System Design Considerations / The Buck Topology", "Low-Side Buck", "High-Side Buck", Figs 3-7;
[TPS2378 DS SLVSB99C](https://www.ti.com/lit/gpn/TPS2378) section 9 Power Supply Recommendations
("will typically be followed by a power supply such as an isolated flyback or active clamp
forward converter or a non-isolated buck converter").

### D3 - Class programming is ONE resistor: RCLS 90.9 ohm (Class 3, af) -> 63.4 ohm (Class 4, at)
This is the decision D-01 turns on. Values are for the TI single-CLS parts.

| Class | Power at PD (min-max) | RCLS (TPS2378) | RCLSA/RCLSB (TPS2372/73) |
|---|---|---|---|
| 0 | 0.44 - 12.95 W | 1270 | 1210 |
| 1 | 0.44 - 3.84 W | 243 | 249 |
| 2 | 3.84 - 6.49 W | 137 | 140 |
| 3 | 6.49 - 12.95 W | **90.9** | 90.9 |
| 4 | 12.95 - 25.5 W | **63.4** | 63.4 |

The datasheet states the build-1/build-2 relationship explicitly: "The TPS2378 implements
two-event classification. Selecting an RCLS of 63.4 ohm provides a valid type 2 signature.
TPS2378 may be used as a compatible type 1 device simply by programming class 0-3 per Table 1."
That sentence is the primary-source proof that D-01's requirement is achievable with one part.

**Tolerance:** 1 %. TI's table is 1 % E96 values; Skyworks specifies "RCL Resistor (1 %, 1/16 W)".
**Placement:** CLS pin to VSS, one 0603, adjacent to the PD IC. Keep it as a standalone, clearly
silkscreened pad pair so the af/at variant is a one-line BOM swap.
**Source:** TPS2378 DS Table 1 + section 8.2.2.5; cross-checked against
[TPS2373 DS SLUSCD1C](https://www.ti.com/lit/ds/symlink/tps2373.pdf) Table 1 (Class 3 = 90.9,
Class 4 = 63.4 - same values, independently published part) and Si3402-B DS Table 7 (1 %, 1/16 W).

**Warning that changes the part choice:** TPS2372 and TPS2373 use **two** class resistors,
RCLSA (first/second class event) and RCLSB (third and subsequent). Selecting one of those makes
the af->at upgrade a **two**-part change, weakening D-01. Prefer a single-CLS part
(TPS2378, or TPS23730/TPS23731 which also have a single RCLS).
**Source:** TPS2373 DS section 7.3.3; TPS2372 DS pin table (CLSA pin 3, CLSB pin 6);
TPS23731 DS Table 8-1 (single RCLS: Class 3 = 46.4, Class 4 = 32).

### D4 - Detection signature: 24.9 kohm +/-1 % from VDD to DEN
IEEE window is 23.75 - 26.25 kohm (25 k +/-5 %). TI recommends 24.9 kohm +/-1 %. Skyworks uses
24.3 kohm +/-1 % on the Si3402 because its bridges are internal and sit inside the measured path.
The value is not portable between architectures.
**Also:** split RDEN into two roughly equal halves and bring the tap out - grounding the tap
disables the PD *and* spoils the detection signature, which is the clean way to make a
hardware/firmware PD-disable.
**Source:** TPS2378 DS sections 7.3.4 and 8.2.2.4; TPS2373 DS section 7.3.4; AN956 section 3.7.

### D5 - Non-isolated buck is compliant, but only under exactly the Q5-default conditions
The requirements mark this PROVISIONAL. The vendor statement of the rule is unambiguous:

> "The 802.3af/at/bt PoE standards require isolation between any accessible conductor,
> including frame ground if present, and all MDI leads, whether used by the PD or not.
> Furthermore, any non-MDI connections must be isolated from the MDI leads and all accessible
> conductors ... Many low-cost applications, such as VoIP telephones, CCTV cameras, and Wi-Fi
> access points, use the non-isolated Buck topology. They achieve compliance by having only a
> single Ethernet cable connection, no other connectors, and no accessible non-isolated
> conductors."  - AN162, System Design Considerations

Consequences the carrier must accept, all traceable to that paragraph:
- **No second external connector of any kind.** This kills Q9 option (a) "USB-C on every
  fixture". A USB-C port is an accessible non-isolated conductor with a shield/ground.
- **No exposed metal, no chassis earth.** Plastic enclosure, as the Q5 default assumes.
- **The whole board, including the expansion connector and the daughter, floats at PoE
  potential.** The daughter inherits the constraint; the ICD must say so.
- **Ground loops break detection, not just safety:** "Even small ground currents circulating in
  a multi-point ground system will interfere with PoE Signature Detection due to low signaling
  currents that are only a few hundred micro-amps." (AN162, same section)
- **Bring-up hazard:** "Woe betide the individual who mistakenly connects both grounds together
  with test equipment or ground leads." (AN162, High-Side Buck) - the Q9 recovery UART header
  must be used with a galvanically isolated USB-UART adapter, or with PoE unplugged. Same for
  scope probes.

AN162 also carries a **Type 2 PD, 12 V 2 A, non-isolated buck** reference schematic (Fig 8,
KTA1137A) - i.e. a published Type-2 non-isolated 12 V design at exactly this board's operating
point, which is the existence proof that the Q5 default is buildable.
**Source:** AN162 Rev 04a, System Design Considerations; Figures 8 and 9; Conclusion.

Skyworks agrees the topology is legitimate: "It supports PD designs that require isolation
between the Ethernet cables and powered equipment as well as the lower-cost option without
isolation for fully-enclosed devices." (AN956 p.3) - note "fully-enclosed".

### D6 - Input bridges: two full 4-diode bridges, 100 V, PN-junction preferred over Schottky
Mode A power arrives on the data-pair centre taps of the magnetics; Mode B on the spare pairs
(4/5 and 7/8, genuinely spare at 10/100). Each path gets its own full bridge, which handles
either polarity automatically. This is mandatory, not optional: "The PD uses input diode or
active bridges to accept power from any of the possible PSE configurations."

**Rating:** TPS2378 (up to 25.5 W): "use 1 A or 2 A, 100 V rated discrete or bridge diodes for
the input rectifiers." The higher-power TPS2373 says 3 A to 5 A, 100 V. 100 V is the floor in
both.

**Schottky vs PN - three vendor-stated reasons to default to PN:**
1. Backfeed: "The IEEE standard specifies a maximum backfeed voltage of 2.8 V ... Schottky
   diodes often have a higher reverse leakage current than PN diodes, making this a harder
   requirement to meet."
2. Detection: "Schottky diode leakage currents and lower dynamic resistances can impact the
   detection signature."
3. ESD: "Schottky diodes have proven less robust to the stresses of ESD transients than PN
   junction diodes. After exposure to ESD, Schottky diodes may become shorted or leak."
Mitigation if Schottky is needed for the at power budget: "match leakage and temperatures by
using packaged bridges."

**Diode drop cost:** two diodes conduct at all times. TI quantifies only the relative gain -
Schottky "will reduce the power dissipation in these devices by about 30 %". `DERIVED`: at
~0.7 V per PN diode the bridge costs ~1.4 V (~2.9 % of a 48 V rail); at the at build's ~0.6 A
that is ~0.85 W, which is a real fraction of the 1.5 W carrier-overhead allocation and should
be a line item in the two-column power budget.
**Source:** TPS2378 DS sections 7.4 (PoE Overview) and 8.2.2.1; TPS2373 DS section 8.2.2.1.

### D7 - Hot-swap and inrush: use the PD IC's integrated 100 V FET; do not add a discrete series FET
All credible modern candidates integrate it, and that removes the SOA problem from the design.
TPS2378 numbers as the worked example:
- 100 V pass MOSFET, 0.5 ohm typ (0.2/0.42/0.75 min/typ/max), continuous handling 0.85 A
- inrush current limit 140 mA typ (100/140/180)
- operating current limit 1 A typ (0.85/1/1.2 A)
- foldback: if V(RTN-VSS) exceeds ~12.3 V for ~800 us the limit reverts to the inrush value
- OTSD 135-145 degC, auto-restart into the inrush limit
- auto-retry fault protection; hot-swap forced off by APD high, DEN low, over-temperature, or
  VDD below the ~32 V UVLO falling threshold

The IEEE-side constraints these must satisfy: PSE inrush limit is 400-450 mA for Class 0-4 for
up to 75 ms after power-up, and "The operational current for Type 2 and 3, and preferably Type
4, cannot exceed 400 mA for a period of 80 ms." A Type 2 PSE may source "as high as 50 A for
10 us or 1.75 A for 75 ms", which "makes robust protection of the PD device even more important".
`OPINION`: a discrete hot-swap would have to survive 57 V at 0.14-1 A for up to 80 ms of SOA -
a large, expensive FET for no benefit. Integrate.
**Source:** TPS2378 DS sections 6.5 (Electrical Characteristics), 7.3.5, 7.4.9;
TPS2373 DS sections 7.3.5, 7.4.6.

### D8 - CAR-REQ-14: the 48 V raw connector feed needs its own current limit and must be gated OFF during PD inrush
This is the block's biggest system-level trap.
- The PD IC charges its own CBULK at the **inrush limit (140 mA on TPS2378)**, and only releases
  the converter-enable once inrush ends.
- `DERIVED`: the strobe daughter's ~2800 uF at 48 V charged at 140 mA takes t = C*V/I =
  ~960 ms - more than 10x the 80 ms operational-current window, and far outside any PSE
  start-up template.
- A shorted or mis-seated daughter drives V(RTN-VSS) up; past ~12.3 V for 800 us the PD folds
  back to the inrush limit and the entire board, MCU included, browns out. TI illustrates
  exactly this case ("Figure 22. Response to PD Output Short Circuit").

**Decision:** the 48 V raw pin(s) must be fed through a separate current-limited high-side
switch / eFuse, enabled only after the PD's power-good (PG on TPS2373, CDB deassertion on
TPS2378) *and* the firmware ENABLE per CAR-REQ-08. The daughter's own inrush limiter
(CAR-REQ-14 assigns the bulk capacitance to the daughter) must hold its charge current below
the PD's operating current limit, not merely below the connector rating.
**Source:** TPS2378 DS sections 7.3.5, 7.4.8, 7.4.9 and Figure 22; TPS2373 DS section 7.3.5;
arithmetic marked DERIVED.

### D9 - The Type-2 build's PD input voltage window is 42.5-57 V, not 37-57 V
Requirements section 3.1 states 37-57 V. The vendor tables qualify that: the 37-57 V window
applies to **PD power <= 13 W**; for **PD power > 13 W** the static PD input voltage range is
**42.5 - 57 V** (802.3at Type 2, 12.5 ohm power loop, PSE 30 W / 50 V min).
Consequence: build 1 (af, <=12.95 W) must regulate from 37 V; build 2 (at) only needs 42.5 V but
at double the power. `OPINION`: design the buck for 37 V minimum input at full load so one part
covers both builds - it costs only duty-cycle headroom. 57 V remains the rating driver, which is
why every PD hot-swap FET in this class is 100 V and why CAR-REQ-02 asks for >=60 V.
**Source:** TPS2378 DS Table 2; TPS2373 DS Table 6 (same table, independently published).

### D10 - MPS: DC MPS is met by the carrier's own overhead, but only above ~10 mA; add a floor
Vendor statement of the requirement: "For a Type 1 or Type 2 PD, a valid MPS consists of a
minimum dc current of 10 mA, or a 10-mA pulsed current for at least 75 ms every 325 ms, and an
AC impedance lower than 26.3 kohm in parallel with 0.05 uF. Only Type 1 and Type 2 PSEs monitor
the AC MPS. A Type 1 or Type 2 PSE that monitors only the AC MPS may remove power from the PD."
- **AC MPS** is satisfied by the bulk capacitance: "impedance is usually accomplished by the
  minimum operating CBULK requirement of 5 uF" (TPS2378); "the input filter capacitor must be
  >5 uF, and the load must be such that the input current is >10 mA" (AN956 3.5).
- **DC MPS:** `DERIVED` - the 1.5 W carrier overhead at 48 V is ~31 mA, comfortably above the
  10 mA floor, so a running board holds the port up. The risk is any firmware state that drops
  board draw below ~0.5 W (10 mA at 48 V): ESP32-S3 deep sleep with the W5500 idle could do it.
- **Design rule:** either guarantee a >=0.5 W minimum load, or select a controller with
  automatic MPS. TPS2372/TPS2373 do this natively - the AMPS_CTL pin generates the pulses "as
  long as the current through the RTN-to-VSS path is not high enough (< ~28 mA)", with a
  "typical resistor value of 1.3 kohm ... in applications where the load current may go below
  ~20 mA". TPS23730/31 have automatic MPS with auto-stretch. **TPS2378 has no automatic MPS.**
- Independent corroboration of the same numbers (10 mA / 75 ms / <=250 ms dropout) from
  Microchip's 802.3bt material.
**Source:** TPS2373 DS section 7.4.7 and 7.3.8 + Table 4/Table 5; TPS2378 DS section 7.4.x
(CBULK 5 uF); AN956 section 3.5; TPS23731 DS section 1 Features;
[Microchip, Next-Generation PoE: IEEE 802.3bt White Paper](https://www.mouser.com/pdfDocs/Microchip_BT_White_Paper-March14,2019-3.pdf).

### D11 - Transient protection: SMAJ58A TVS across the rectified input + 0.1 uF/100 V bypass. Mandatory.
- "A TVS, D1, across the rectified PoE voltage per Figure 30 must be used. TI recommends a
  SMAJ58A, or equivalent ... for general indoor applications ... Outdoor transient levels or
  special applications require additional protection." The LUMINA deployment is indoor
  basement, so SMAJ58A-class is the right level - no extra outdoor surge stage.
- Input bypass: "The IEEE 802.3at standard specifies an input bypass capacitor (from VDD to
  VSS) of 0.05 uF to 0.12 uF. Typically a 0.1 uF, 100 V, 10 % ceramic capacitor is used."
  X7R, since it must hold value over temperature and bias.
- The surge the standard actually asks for (useful for sizing): "IEEE 802.3 specifies a 1000 V
  surge with 0.3 usec rise time and 50 usec fall time applied to each conductor through a series
  resistance of 402 ohm"; a compliant PD is designed to handle "a 50 usec, 5 A pulse". Also
  telephony ringing: "56 V dc + 175 V peak ringing applied through 400 ohm source impedance at
  a frequency of 20 to 60 Hz."
- System ESD: Skyworks notes that with a powered input, ESD above 4 kV at the output terminals
  can damage the input bridges unless output-side bypass capacitors are fitted; with them, >16 kV
  system-level ESD is achievable. TPS2378 claims 15 kV / 8 kV system-level ESD capability.
**Source:** TPS2378 DS section 8.2.2.2 and 8.2.2.3, section 1 Features; TPS2373 DS sections
8.2.2.2/8.2.2.3; AN956 section 6.

### D12 - Route T2P (Type-2 PSE indication) to an MCU GPIO
The same PD IC serves both builds; T2P (open-drain) pulls low only "after 2-event classification
and inrush is complete", i.e. only when a Type 2 PSE has actually allocated 25.5 W. Bringing it
to a GPIO lets firmware read the allocation it really got and enforce the correct average-energy
governor limit (requirements section 3.2) instead of trusting a build-time constant. Costs one
pin and one pull-up. Note the pin is referenced to RTN and can sit at up to 57 V when
high-impedance, so it needs the vendor's LED/level-shift network, not a bare GPIO connection.
**Source:** TPS2378 DS section 7.3.x (T2P) and Electrical Characteristics (T2P output low,
leakage at VT2P = 57 V); TPS2373 DS section 7.3.6 and Table 2.

### D13 - Class 3 (not Class 0) for build 1
Class 0 (1270 ohm) also permits up to 12.95 W but tells the PSE nothing about the real demand;
Class 3 (90.9 ohm) declares 6.49-12.95 W. Both give the same 12.95 W allocation, but Class 3 is
the honest signature and is what a managed PoE switch's budgeting expects. It also makes the
af->at delta a clean single-step 90.9 -> 63.4.
**Source:** TPS2378 DS Table 1; TPS2373 DS Table 2 (Class 3 -> 12.95 W allocated, 1 class cycle).

---

## Candidate summary

| Part | Type | Class resistors | Integrated DC-DC | Auto MPS | Fit for D-01 |
|---|---|---|---|---|---|
| Skyworks Si3402-B / -C | **Type 1 only** | 1 (RCL) | yes (buck or flyback) | no | **NO - no Class 4** |
| TI TPS2378 | at Type 2 | **1 (RCLS)** | no | **no** | **Best fit** |
| TI TPS2372 / TPS2373 | at/bt Type 1-4 | 2 (CLSA+CLSB) | no | yes | Works, but 2-part change |
| TI TPS23730 / TPS23731 | bt Type 3, Cl 1-4 | 1 (RCLS) | yes (flyback, PSR) | yes | Works; flyback half unused |
| Kinetic KTA1137A | at Type 2 | n/v | yes | n/v | Has a published 12 V 2 A non-isolated buck refdes |

n/v = not verified from a primary source in this pass.

Availability sighted but **not verified** (component-scout owns this): TPS2378DDAR appears in
the JLCPCB parts library as C337500; TPS2373-3RGWR / TPS2373-4RGWR are listed at LCSC as
C2860885 / C470963. Si3402-B is LCSC-listed but is the wrong part per D1.

---

## Layout constraints the vendors call out (hand to interface-spec)

1. **Point-to-point power flow, in this order:** RJ-45 -> Ethernet transformer -> diode bridges
   -> TVS and 0.1 uF capacitor -> PD IC. "Parts placement must be driven by power flow in a
   point-to-point manner". (TPS2378 10.1; TPS2373 10.1)
2. **No crossovers:** "There should not be any crossovers of signals from one part of the flow
   to another." `INTERPRETATION`: this makes the PD front end a contiguous keepout zone between
   the magjack and the PD IC - Ethernet differential pairs, SPI and PWM must not be routed
   across it. (TPS2373 10.1)
3. **All leads as short as possible, wide power traces, paired signal and return.** (TPS2373 10.1)
4. **Split local ground planes:** the PD IC "should be located over split, local ground planes
   referenced to VSS for the PoE input and to RTN for the switched output." (TPS2373 10.1)
5. **Spacing:** "Spacing consistent with safety standards like IEC60950 must be observed between
   the 48-V input voltage rails and between the input and an isolated converter output."
   Concrete number: "maintain a clearance of 0.025 in [0.635 mm] between VSS and high-voltage
   signals such as VDD." (TPS2373 10.1 and 7.3.11)
6. **Thermal pad:** tie the exposed pad to VSS; "Nine vias are recommended on the Exposed
   Thermal Pad ... connect to all layers of a copper plane ... Ensure 80 % printed solder
   coverage by area." (TPS2373 10.1)
7. **Thermal calibration data point** (Si3402, still useful for any QFN PD front end):
   2 in^2 outer-layer plane -> 44 degC/W; 1 in^2 inner-layer plane -> 54 degC/W; thermal vias at
   1 to 1.2 mm pitch, 0.3 to 0.33 mm diameter. "It is not unusual for the Si3402-B junction
   temperature to rise 70 degC." (AN956 8.1)
8. **Layer count:** "In general, four-layer PCB designs yield the most robust design ...
   Two-layer PCB designs must be carefully considered." Skyworks offers pre-fab layout review
   for 2-layer PD designs. (AN956 8)
9. **Trace widths at PD currents** (Si3402 data point, scale for 25.5 W): 12 mil for pins
   carrying up to 325 mA dc; 25 mil for switching nodes carrying multi-amp spikes. (AN956 8.3)
10. **EMI:** "Use compact loops for dv/dt and di/dt circuit paths (power loops and gate drives)"
    and "minimal, yet thermally adequate, copper areas for heat sinking of components tied to
    switching nodes". (TPS2373 10.3)
11. **Magjack must be a PoE variant with the data-pair centre taps brought out to pins.** Mode A
    power is extracted at the transformer centre taps; Mode B comes straight off the spare pairs.
    The TI power-flow list assumes the transformer sits between the RJ-45 and the bridges.
    (TPS2373 10.1; corroborated by
    [Bel Fuse MagJack ICM](https://www.belfuse.com/lp/magjack) - "The isolation transformer in
    MagJack ICMs has a center tap on the secondary side that is used in pairs to transmit or
    receive power over the data lines" - **secondary/marketing source, confirm against the
    chosen magjack's own datasheet**.)
12. **CAR-REQ-18 interaction:** the PD front end is a heat source (bridges + hot-swap FET) that
    is separate from the DC-DC. The layout must not stack the PD front end, the buck, and the
    daughter's drivers in one thermal column. (`INTERPRETATION` of AN956 8.1 "Due to heating of
    the ambient air from the Schottky diode etc., the effective thermal impedance can be
    considerably higher".)

---

## Errata and footguns

1. **Si3402-B/-C are Type 1 only** and the -B datasheet's revision history explicitly *deleted*
   its former Class 4 claim. Distributor pages and blogs still say "802.3at" because -B is
   at-*compatible* as a Type 1 device. Do not read that as Class 4. (Si3402-B DS Rev History)
2. **Si3402-C drops the PLOSS (early power-loss) output** that -A/-B had. Not a drop-in if
   anything used it. (AN1050 Introduction)
3. **Si3402-B runs hot:** rated TJ 140 degC, thermal shutdown ~160 degC, and "it is not unusual
   for the ... junction temperature to rise 70 degC". Mitigation is to bypass the on-chip diode
   bridges with external Schottkys at Class 3. (AN956 8.1)
4. **Si3402-B pulse-skips at no load.** "If the switcher is operated with no load, the switcher
   tends to pulse on and off ... it is recommended that a 250 mW load always be present."
   (AN956 3.5, 8.4)
5. **Si3402 detection is capacitance-sensitive:** the input signature capacitance must stay in
   the IEEE 0.05-0.12 uF window; too much port capacitance lengthens the detection-pulse rise
   time and the PD is not detected. (Si3402-B DS 3.7 / AN956 3.7)
6. **Schottky input bridges are a triple hazard** - backfeed >2.8 V, corrupted detection
   signature, and poor ESD robustness that can leave them shorted or leaky after an event.
   (TPS2378 8.2.2.1)
7. **TPS2378 has no automatic MPS.** If the fixture can ever idle below ~10 mA of input current
   the PSE will drop the port. TPS2372/73/23730/23731 add AMPS_CTL. (TPS2378 DS feature list vs
   TPS2373 7.3.8)
8. **TPS2372/TPS2373 need two class resistors** (CLSA and CLSB), which breaks D-01's
   "single-part change" wording. (TPS2373 7.3.3)
9. **Foldback deglitch is short:** 800 us (TPS2378) / 1.65 ms (TPS2373) above ~12-14.5 V of
   V(RTN-VSS). Any daughter hot-plug or cap-bank charge event that holds RTN high for longer
   resets the whole PD to the inrush limit. Sizing the daughter's inrush limiter against the
   *connector* rating instead of the *PD's* operating current limit is the classic way to get
   this wrong. (TPS2378 6.5, 7.4.9; TPS2373 7.3.5)
10. **DEN-low is not a usable soft-off.** "When DEN is used to force the hotswap switch off, the
    DC MPS will not be met. A PSE that monitors the DC MPS will remove power from the PD when
    this occurs." (TPS2373 7.4.7)
11. **The input bridge sits in series with the detection resistor.** "The input diode bridge's
    incremental resistance may be hundreds of ohm at the low currents drawn when 2.7 V is
    applied to the PI." Do not port 24.9 kohm blindly to an unusual bridge; TI notes
    "Increasing RDET slightly may also help meet the requirement." (TPS2378 7.4.x; TPS2373 7.4.x)
12. **Non-isolated debug hazard.** Grounded scope probes or a non-isolated USB-UART tie the
    floating PoE return to earth. Beyond the shock/damage risk, the resulting ground currents
    break signature detection outright (detection currents are "only a few hundred
    micro-amps"). (AN162, System Design Considerations and High-Side Buck)
13. **No formal TI errata sheet exists for TPS2378 / TPS2373** - checked; the items above come
    from datasheet body text and application notes, not from an errata document. Treat that as
    "none published", not "none exist".

---

## Sources

Primary (vendor PDFs, read in full):
- Skyworks, *Si3402-B Data Sheet*, Rev 1.1, 6 Aug 2021 - https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si3402-B.pdf
- Skyworks, *AN956: Using the Si3402-B PoE PD Controller in Isolated and Non-Isolated Designs*, Rev 0.2, 8 Nov 2021 - https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN956.pdf
- Skyworks, *AN1050: Using the Si3402-C PoE PD Controller in Isolated and Non-Isolated Designs* - https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN1050.pdf
- TI, *TPS2378 IEEE 802.3at PoE High-Power PD Interface*, SLVSB99C, Mar 2012 rev Jul 2015 - https://www.ti.com/lit/gpn/TPS2378
- TI, *TPS2373 High-Power PoE PD Interface with Advanced Startup*, SLUSCD1C, Jun 2017 rev Nov 2018 - https://www.ti.com/lit/ds/symlink/tps2373.pdf
- TI, *TPS2372* datasheet - https://www.ti.com/lit/gpn/TPS2372
- TI, *TPS23731 IEEE 802.3bt Type 3 Class 1-4 PoE PD with No-Opto Flyback DC-DC Controller*, SLVSER7, Oct 2020 - https://www.ti.com/lit/ds/symlink/tps23731.pdf
- Kinetic Technologies, *AN162: Using PoE PD DC-DC Controllers in the Non-Isolated Buck Configuration*, Rev 04a, Jan 2022 - https://www.kinet-ic.com/AN162-04a

Corroborating / secondary:
- Microchip, *Next-Generation PoE: IEEE 802.3bt White Paper*, Mar 2019 - https://www.mouser.com/pdfDocs/Microchip_BT_White_Paper-March14,2019-3.pdf
- Bel Fuse, *MagJack ICM* product page - https://www.belfuse.com/lp/magjack
