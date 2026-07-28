# Interface research: Ethernet DATA half - 10/100BASE-TX MDI + PoE magjack + W5500 SPI

Board: `lumina-carrier` (LUM-CAR-A). Scope: the **data** half of the Ethernet
interface - W5500 MDI to the magjack, the magjack's dual role (data + PoE), the
W5500 <-> ESP32-S3 SPI link, the 25 MHz reference crystal, MDI ESD, and the
ESP32-S3 pin legality list that schematic sign-off gate 5 depends on.

**Out of scope here (sibling agent owns it):** the 48 V PD front end, the
classification/detection network, the >= 60 V converter, and the CAR-REQ-17
creepage work. Section 3.6 marks the one seam where the two halves meet.

Companion machine-readable fragment: `interface-ethernet.json`.

Every number below carries a source (section 10). Numbers I derived are marked
`computed`. Numbers I could not source carry a conservative default and an
`ASSUMED` marker.

---

## 1. Constraint table (what lands where)

| # | Constraint | Value | Lands in | Enforced by |
|---|---|---|---|---|
| E1 | MDI differential impedance | **100 ohm** | `diff_pairs[].impedance_ohm` | rules_gen (P5), check_diffpair (P8) |
| E2 | MDI single-ended impedance | 50 ohm to GND (<= 50 ohm per WIZnet) | notes only | manual |
| E3 | MDI reference plane | **solid GND, continuous, no plane split crossed** | `high_speed[].reference` | check_return_path (P8), planes_gen (P7) |
| E4 | MDI transmitter edge rate (sets stitch radius) | rise/fall **3.0-5.0 ns** (10/90), symmetry <= 0.5 ns | `high_speed[].t_rise_ns = 3.0` | check_return_path (P8) |
| E5 | Intra-pair length match | **2.5 mm** (`ASSUMED` value; physics allows ~45 mm) | `diff_pairs[].max_skew_mm` | check_diffpair (P8) |
| E6 | Intra-pair coupling / one-sided detour | 5.0 mm allowed uncoupled run | `diff_pairs[].max_uncoupled_mm` | check_diffpair (P8) |
| E7 | Nominal pair pitch (centre-to-centre) | **0.47 mm** on JLC04161H-3313 | `diff_pairs[].gap_mm` | check_diffpair (P8) |
| E8 | MDI total routed length | **<= 25 mm recommended, 75 mm absolute max** | placement, not a key | manual (see 9.2) |
| E9 | TX pair to RX pair separation | >= 0.508 mm (20 mil), 0.762 mm (30 mil) preferred, GND between | not expressible | manual / route_critical |
| E10 | MDI to any other signal | >= 7.5 mm (300 mil) or separated by GND | not expressible | manual |
| E11 | Vias on MDI | **zero preferred**, 2 per trace absolute max | not expressible | manual (route_critical) |
| E12 | W5500 SPI clock | **<= 33.3 MHz guaranteed** (80 MHz is design-theoretical only) | `high_speed` on SCLK | gate 5 sign-off + manual |
| E13 | W5500 SPI mode | **mode 0 or mode 3 only** | schematic/firmware | manual |
| E14 | W5500 SCSn high time between frames | >= 30 ns | firmware/driver | manual |
| E15 | Reference crystal | 25 MHz, **+/-30 ppm at 25 C**, CL 18 pF, shunt <= 7 pF, drive 59.12 uW, aging +/-3 ppm/yr | parts (P3) | manual |
| E16 | Crystal total budget vs standard | transmit clock must be 125 MHz **+/-50 ppm** | parts (P3) | manual - see 5.2 |
| E17 | Crystal load caps | **27 pF C0G** each (`computed` from CL 18 pF, Cstray 4 pF `ASSUMED`) | parts (P3) | manual |
| E18 | Crystal layout | ground land under the crystal tied to oscillator GND; no vias, no clock/digital lines near XI/XO | placement | manual |
| E19 | W5500 EXRES1 | 12.4 kohm **1%** to GND | schematic (P4) | manual |
| E20 | W5500 TOCAP | 4.7 uF | schematic (P4) | manual |
| E21 | W5500 1V2O | 10 nF | schematic (P4) | manual |
| E22 | W5500 RSVD pin 23 | must be tied to GND | schematic (P4) | netlist_audit |
| E23 | W5500 RSTn low time | >= 500 us; PLL lock <= 1 ms after release | schematic + firmware | manual |
| E24 | Magjack must be a **PoE type with the four power taps brought out** | 2x transformer centre taps (pairs 1-2, 3-6) + spare pairs 4/5, 7/8 | parts (P3) | manual - see 3 |
| E25 | Bob Smith 75 ohm DC termination on the powered taps | **must NOT be fitted** | schematic (P4) | manual - see 3.3 |
| E26 | Planes under the magjack | no signal-GND / power plane on any layer under the connector body | `planes[].region` partition | manual - see 3.5 |
| E27 | MDI ESD | low-capacitance TVS array, **<= 1 pF/line**, PHY side of the magnetics | parts (P3) | manual - see 6 |
| E28 | Stackup | **4-layer JLC04161H-3313** (2-layer cannot hold 100 ohm) | P2 stackup choice | rules_gen (P5) |
| E29 | ESP32-S3 pins clear of strapping / USB / flash-PSRAM | see section 7 | architecture | gate 5 |

---

## 2. 10/100BASE-TX MDI

### 2.1 What is actually on the board

The board carries **one** MDI section, not two: with an RJ45 that has
**integrated magnetics** (CAR-REQ-05), the transformer-to-RJ45-contact wiring is
**inside the part**. The only MDI copper on the PCB is

```
W5500 TXP/TXN (pins 2/1) --> magjack TD+/TD- (chip side)
W5500 RXP/RXN (pins 6/5) --> magjack RD+/RD- (chip side)
```

so the constraint set has exactly **two** differential pairs, both on the chip
side of the isolation barrier. There is nothing to route on the cable side; the
"magjack to RJ45 contacts" leg named in the assignment does not exist as board
copper.

10/100BASE-TX uses only cable pairs **1-2 (TX)** and **3-6 (RX)**. Pairs 4-5 and
7-8 carry no data - which is exactly why they are available as the PoE spare
pair (section 3).

### 2.2 Impedance

| Parameter | Value | Source |
|---|---|---|
| Differential | **100 ohm** | WIZnet HW design guide ("Impedance of +/- Differential signal should be maintained at 100 ohm"); TI SNLA079D 2.1 ("50 ohm to ground or 100 ohm differential"); Pulse layout note p.3 (same wording) |
| Single-ended | <= 50 ohm to GND | WIZnet HW design guide ("individual impedance of the TX+/- and RX+/- signals is kept below 50 ohm") |
| Cable/MDI tolerance | the standard's own transmitter return loss floor is 10 dB at the AOI | ANSI X3.263-1995 9.1.5 via UNH-IOL test 25.1.6 |

Note that 10 dB return loss corresponds to a reflection coefficient of 0.32,
i.e. roughly 100 ohm +/-45 ohm at the connector. **The 100 ohm target is not
knife-edge**; Pulse says explicitly that "short traces will have fewer problems
if the differential impedance is slightly off target" and that naive
2x-single-ended calculators under-read the coupled impedance by 5-20 ohm. This
is why the pipeline's own solver (`impedance.py`, which models edge coupling) is
the right source of geometry, and why V12 (confirm against JLC's calculator
before ordering controlled impedance) still applies.

**Geometry, from `stackups.yaml` + `impedance.py` (verified by running it):**

| Stackup | h (mm) | er | 100 ohm diff width | gap | pitch |
|---|---|---|---|---|---|
| **JLC04161H-3313 (4L)** | 0.2104 | 4.05 | **0.260 mm** | **0.210 mm** | **0.470 mm** |
| JLC2313_1.6 (2L, 1 oz) | 1.530 | 4.5 | 1.081 mm | 0.300 mm* | 1.381 mm |
| JLC2313_1.6_2oz (2L, 2 oz) | 1.460 | 4.5 | 1.000 mm | 0.300 mm* | 1.300 mm |

\* the 2-layer gap is the solver's manufacturability clamp
(`clamp(h, 0.13, 0.30)`), not an impedance solution - so the 2-layer widths are
"what it takes at a forced 0.30 mm gap", and are indicative only.

**Conclusion: 4-layer is required.** See section 8.

### 2.3 Edge rate, and why it sets the return-path radius

100BASE-TX is MLT-3 at 125 Mbaud. The **transmitter rise/fall time is specified
as 3.0 ns to 5.0 ns (10%/90%), with rise/fall symmetry <= 0.5 ns**
[ANSI X3.263-1995 9.1.6, per UNH-IOL Clause 25 PMD test 25.1.2]. Other AOI
numbers worth carrying: differential output 950-1050 mV with 98-102% amplitude
symmetry [9.1.4 / test 25.1.1]; duty-cycle distortion within +/-0.25 ns of a
16 ns grid [9.1.8]; transmit jitter <= 1.4 ns pk-pk [9.1.9].

`t_rise_ns = 3.0` (the fastest edge the standard permits) is what goes into
`high_speed`. What the pipeline does with it:

- `check_return_path` computes `f_knee = 0.5 / t_rise = 167 MHz` and
  `r = c / (f_knee * 20) = 2.998e11 / 3.33e9 = ` **89.9 mm** `computed`.
  That is one twentieth of a wavelength at the knee and it is a genuinely
  loose number - **stitching-via spacing is not a real constraint on
  100BASE-TX**. Say so out loud rather than pretending it is a fast interface.
- What *is* a real constraint, and what the same check enforces, is **corridor
  continuity**: the GND reference under the MDI pairs must be unbroken. See the
  trap in 9.1.

### 2.4 Length, skew and spacing

**Total length.** WIZnet: "Recommended signal length is less than 25 mm
(1000 mil)", "in worst case, MDI maximum routing length is 75 mm (3000 mil)".
Pulse, for EMI, wants the opposite bound: "Isolate the PHY from the Ethernet
magnetic; the distance between them needs to be 25 mm (approx. 1 inch) or
greater", and "keep the PHY device and the differential transmit pairs at least
25 mm from the edge of the PCB, up to the Ethernet magnetic". The two rules
**meet at 25 mm**, which is the number to design to: put the W5500 about 25 mm
behind the magjack, and keep it and the pairs 25 mm clear of the *other* board
edges. There is no `length` key in constraints.json - this is a placement
constraint (9.2).

**Intra-pair skew.** No vendor and no clause of the standard gives a number;
WIZnet, TI and Pulse all say only "matched in length" / "same length as
possible". Deriving a defensible bound `computed`:

- fastest permitted edge 3.0 ns; the usual engineering bound is skew < 10% of
  t_rise -> 300 ps;
- `check_diffpair` converts mm to ps with the board's stackup epsilon:
  `skew_ps = skew_mm * sqrt(4.05) / 0.2998 = 6.71 ps/mm`;
- 300 ps / 6.71 = **44.7 mm** of allowed skew.

So the electrical budget is enormous. **`max_skew_mm = 2.5` is chosen as a
conservative, easily-routed default** (17 ps, 0.6% of the edge) on a pair whose
whole length is <= 25 mm - not because 2.5 mm is a sourced limit. Marked
`ASSUMED`. What actually degrades with mismatch is differential-to-common-mode
conversion and hence radiated EMI, which is why every vendor phrases it as
"match it", not "match it to X".

**Uncoupled run.** `max_uncoupled_mm = 5.0` (the pipeline default), kept
explicit. Rationale: `check_diffpair` calls a segment uncoupled when the
partner is farther than `max(3 * pitch, pitch + 0.5)` = **1.41 mm** at a
0.47 mm nominal pitch. A THT magjack's MDI pins sit on a ~2.0 mm grid, so the
fan-out at the connector is *inherently* wider than the coupling threshold for
1-2 mm on each leg. A tight value here would false-positive on correct layout.
Pulse's own rule - "keep maximum separation within differential pairs to
10 mils" - is a routing instruction for the coupled run, not a gate value.

**Pair-to-pair and pair-to-everything-else.** WIZnet gives `W >= 20 mil`
(0.508 mm) between TX and RX with a GND pattern between them, showing 30 mil
(0.762 mm) in the example, and `K >= 20 mil` to other signals/power "separate by
GND". Pulse is stricter on digital: "no digital signal should be located within
300 mils (7.5 mm) of the differential pairs", and digital signals on other
layers that cannot be separated by a ground plane must cross **at right
angles**. **None of this is expressible in constraints.json** - there is no
inter-pair spacing key. It is a route_critical / manual constraint (9.3).

**Vias.** WIZnet: "TX+/- and RX+/- signals prohibit Via or Layer changes."
TI: "Ideally there should be no crossover or via on the signal paths ... Route
an entire trace pair on a single layer if possible." Pulse allows "at most two
vias per trace". Design target: **zero vias**, which is achievable because the
W5500 and the magjack are both on F.Cu, ~25 mm apart, with In1 GND underneath.

**Stubs.** TI 2.1: "Stubs should be avoided on all signal traces, especially the
differential signal pairs." Relevant because `check_diffpair` measures skew on
the branch-free *trunk* - a stub will not inflate the reported skew but will
still be a defect.

### 2.5 No Auto-MDIX

The W5500 datasheet section 5.5.6 (MDIX) states the part does **not** support
Auto-MDIX, and instructs a straight-through cable to a router/switch and a
crossover cable to a PC/workstation/another W5500. The deployment is a managed
PoE switch (`00` section 1), so straight-through is correct - but it is a
**documentation item** for the fixture, and it means the MDI pin order at the
magjack is not free: TX must land on cable pair 1-2 and RX on pair 3-6.

---

## 3. The magjack: data + PoE through one part (CAR-REQ-05)

This is the section with the real content, because carrying both changes the
part, the termination network and the plane strategy.

### 3.1 How the PoE taps come out

A PD needs four power access points, and 802.3 allows the PSE to use either:

- **Mode A** - power on the *data* pairs, common-mode. Accessed at the
  **cable-side centre taps of the two signal transformers**: the pair-1-2
  centre tap and the pair-3-6 centre tap. Usually labelled TCT / RCT, or
  CT1 / CT2 on the PD controller side.
- **Mode B** - power on the *spare* pairs 4-5 and 7-8. On a 10/100 magjack
  these four contacts have no transformer at all; they pass straight from the
  RJ45 contacts to package pins (SP1 / SP2 on the PD side).

Skyworks AN956 shows exactly this on the Si3402-B EVB: the RJ-45 symbol carries
`MX0+ / CT / MX0- / MX1+ / CT-MX1- / MX1-` plus `PWR1..PWR5`, feeding the
controller's `CT1, CT2, SP1, SP2` pins, and note 2 to the schematic requires
that "at least one pair of the CTx and SPx pins be connected to the PoE voltage
input terminals". Both mode pairs go into diode bridges, which is what makes the
PD polarity- and mode-agnostic (the requirements' own `ASSUMED` in section 2.2).

### 3.2 What this means for part selection (E24) - the trap

**A plain 10/100 magjack will not work.** The common low-cost magjack integrates
the Bob Smith network *inside* the package and does **not** bring the centre
taps out to pins; there is physically nowhere to take PoE from. The part must be
specified as a **PoE / PD magjack whose datasheet pinout shows the two centre
taps and the two spare pairs on package pins** (Bel's 0826 / SI-5xxxx PoE
MagJack families and Pulse's PoE ICMs are the reference classes). This is a
hard P3 filter, not a preference, and it is the single most likely place for a
first-spin to fail.

Second filter: the magjack's own **isolation and voltage rating**. IEEE 802.3
isolation is 1500 Vrms; TI's magnetics requirements table (SNLA079D Table 4)
lists turns ratio 1:1 +/-2%, insertion loss -1 dB (1-100 MHz), return loss
-16 dB (1-30 MHz), differential-to-common rejection -30 dB (1-50 MHz), crosstalk
-35 dB at 30 MHz, isolation 1500 Vrms HPOT. The W5500's own transformer
requirement is narrower: **1:1 turns ratio, 350 uH inductance, both transmit and
receive ends** (W5500 datasheet 5.5.5).

Third filter, PoE-specific: the taps and the spare-pair contacts must be rated
for the PD current. At 802.3af that is <= 350 mA steady state (AN956 section 1)
- trivial for any magjack - but the **at upgrade path (D-01)** doubles it, so
check the tap current rating against 802.3at even though build 1 classifies as
af. This is a resistor-change-only upgrade by D-01, and a magjack that cannot
carry Type 2 current would silently break that promise.

### 3.3 Bob Smith termination with PoE (E25) - the direct answer

**Standard Bob Smith:** the cable-side centre tap of each pair goes through a
**75 ohm resistor** to a common node, and that node goes to chassis ground
through a **1000 pF capacitor rated >= 2 kV** [TI SNLA079D 2.3]. Its job is to
present a common-mode-matched termination so common-mode currents and the noise
picked up by the unused pairs have a defined return, rather than radiating.

**With PoE it does not apply to the powered taps.** TI states it flatly:

> "Note: Bob-Smith termination does not apply for Power Over Ethernet (PoE)
> applications." - SNLA079D 2.3

The reason is not subtle. Those centre taps now sit at 37-57 V DC and feed the
PD bridges. A 75 ohm DC path from them to chassis would (a) burn ~40 W into the
termination network if it ever completed a circuit, (b) present a DC load that
corrupts PSE detection (the 25 kohm signature) and classification, and (c) give
the PSE a leakage path that can look like a disconnect. **Do not fit 75 ohm
resistors on any tap that feeds the PD front end.**

**What survives, and the honest tension.** Pulse's PoE best-practice list says
the opposite-sounding thing:

> "Using Bob Smith Termination (BST - 75 ohm resistors and high voltage cap to
> chassis ground) to terminate cable side centre taps is advisable for best EMI
> performance (included in most connector solutions)."

The two are reconciled by *which* taps and *which* element:

- the **AC** half of the idea is still correct and still needed - the PD's own
  input node wants a high-voltage capacitor to the enclosure/shield reference so
  common-mode energy has a path;
- the **DC** half (the 75 ohm resistor) is what PoE removes, on the taps that
  carry power;
- on a PD where **all four** access points are used (Mode A + Mode B, which an
  802.3-compliant PD must support), **there is no unpowered tap left to
  Bob-Smith**.

AN956's reference design shows what a PD actually fits in that place instead:
**330 ohm ferrite beads in series with the RJ45 conductor paths and 1 nF
capacitors** (C10-C17) to the Vpos/Vneg planes, annotated "Capacitors C10-C17
are for ESD immunity", plus a note that Vpos is "an EMI and ESD plane, use top
layer". That is the PoE-era replacement for the 75 ohm/1000 pF network, and it
is the topology to copy.

### 3.4 Chassis ground vs signal ground - unresolved, and it is Q5's fault

The classic layout is: chassis ground island under the RJ45, signal ground for
everything else, a **moat** between them crossed only by the transformer-isolated
pairs, and a controlled bridge across the moat -

> "Do not overlap the circuit and chassis ground planes, keep them isolated.
> Connect chassis ground and system ground together using two size 1206 zero
> ohm resistors across the void between the ground planes on either side of the
> RJ-45." - TI SNLA079D 2.4

**On this board that construction may have nothing to bridge to.** Under the Q5
default (non-isolated buck PD, plastic enclosure, Ethernet the only external
connection) the board's GND *is* the PD's Vneg and floats at PoE potential;
there is no earth, no metal enclosure, and no second connection. In that case:

- a **shielded** RJ45's shield is the only "outside" node. Tie it to a dedicated
  chassis pad, and connect that pad to board GND through the usual hybrid
  (1 Mohm || 1 nF/2 kV) with a fitted-by-default 0 ohm alternative, so EMC
  testing can move the strap without a respin;
- an **unshielded** jack removes the question entirely and is defensible for an
  indoor plastic fixture.

If Q5 comes back as *isolated flyback*, the moat becomes real and load-bearing
and this section must be redone. **Flagged as OPEN-1.**

### 3.5 Planes and keepout under the magjack (E26) - a real vendor conflict

Two sources disagree, and the disagreement is about part type, not about
physics:

- **WIZnet** (hardware design guide): "All PCB layers under the Transformer and
  RJ45 Connector must have no power and GND plane."
- **TI** (SNLA079D 10.2): "do not run signals under the magnetics ... void the
  planes under discrete magnetics."
- **Pulse** (layout note p.4): "There should be no ground planes beneath a
  discrete LAN magnetics package ... **For integrated connector modules, the
  chassis ground plane should run under the component to connect with the
  shield of the connector.** Within the connector module, all magnetic
  components are far enough away from the PCB to prevent any unwanted coupling."

**Resolution for this board:** the part is an integrated connector module, so
the coupling argument that motivates the blanket void is weakened - but WIZnet's
rule is the one written for *this PHY*, and the chassis-plane exception only
applies if there is a chassis ground (3.4, unresolved). Recommendation:

1. **Void the signal-GND pour and every power pour on all four layers under the
   connector body**, from the magjack's PHY-side pad row outward to the board
   edge.
2. If a shielded jack is chosen, put a **separate chassis-ground island** under
   the shield tabs only, in that voided region, isolated from GND except through
   the hybrid strap of 3.4.
3. Do **not** rely on FR-4 dielectric under the magjack as an isolation
   barrier: Pulse says "To maintain 1500 Vrms isolation between two adjacent
   layers of a NEMA FR-4 multi-layer PCB, a minimum of 15 mils isolation
   thickness is recommended", and on JLC04161H-3313 the F.Cu-to-In1 prepreg is
   **0.2104 mm = 8.3 mil** - roughly half that. This is precisely why In1 and
   In2 must both be voided under the connector rather than just F.Cu/B.Cu.

### 3.6 The seam with the PoE agent

The PoE tap traces run from the magjack pins to the PD bridge at 37-57 V and
pass within a few millimetres of the MDI pads and (if fitted) the shield island.
**That pin field is where this fragment's diff pairs and the PoE agent's
`voltages` entries physically meet**, and it is where `check_creepage` will do
its work. This fragment deliberately emits **no `voltages` entries** so the two
fragments do not collide - but the architect must confirm that the PoE agent's
`voltages` list covers the magjack tap nets, not only the downstream bus.

---

## 4. W5500 SPI link to the ESP32-S3 (gate 5, half one)

### 4.1 The datasheet maximum - the number gate 5 needs

W5500 datasheet v1.1.0, section **5.5.4 SPI Timing**, Table `FSCK`:

| Symbol | Description | Min | Max | Units |
|---|---|---|---|---|
| FSCK | SCK Clock Frequency | - | **80 / 33.3** | MHz |
| TWH / TWL | SCK high / low time | 6 | - | ns |
| TCS | SCSn high time | 30 | - | ns |
| TCSS / TCSH | SCSn setup / hold | 5 | - | ns |
| TDS / TDH | Data in setup / hold | 3 | - | ns |
| TOV | Output valid time | - | 5 | ns |
| TOH | Output hold time | 0 | - | ns |
| TCHZ | SCSn high to output Hi-Z | - | 2.16 | ns |

and the footnote that makes the "80" meaningless as a design number:

> "Even though theoretical design speed is 80MHz, the signal in the high speed
> may be distorted because of the circuit crosstalk and the length of the signal
> line. **The minimum guaranteed speed of the SCLK is 33.3 MHz** which was
> tested and measured with the stable waveform."

**Gate 5's binding number is therefore 33.3 MHz, not 80 MHz.** Any sign-off that
cites 80 MHz has cited the wrong figure.

### 4.2 What the ESP32-S3 can actually deliver

Espressif's SPI-master documentation for the ESP32-S3:

> "Typical maximum frequency communicating with an ideal slave without data
> output delay: **80 MHz (IOMUX pins)** and **26 MHz (GPIO matrix pins)**."

and the driver re-derives the requested clock to a hardware-compatible value
(the SPI source clock is 80 MHz, so the reachable settings near our range are
80/3 = 26.67 MHz and 80/4 = 20 MHz).

**Recommendation:** put the W5500 on **SPI2 (FSPI) using its IO_MUX pins** and
run **20 MHz for rev A**, with headroom to 26.67 MHz once the board is measured.

| Option | Clock | Inside W5500 33.3 MHz? | Inside ESP32-S3 path limit? |
|---|---|---|---|
| **20 MHz (recommended)** | 80/4 | yes, 40% margin | yes on either path |
| 26.67 MHz | 80/3 | yes, 20% margin | yes on IO_MUX; **at the edge** on GPIO matrix |
| 33.3 MHz | not reachable exactly (80/2 = 40 MHz overshoots) | boundary | IO_MUX only |
| 40 MHz+ | 80/2 | **no - outside the guaranteed spec** | - |

Sanity check that 20 MHz is not throughput-limited `computed`: the control
contract is 60 fps of small UDP packets (`00` section 3). At 20 MHz an
8-channel PWM update payload is a few hundred bytes, i.e. tens of microseconds
of SPI - three orders of magnitude inside the 16.7 ms frame. **Speed is not the
constraint here; margin is.** Do not trade the margin for a number nobody needs.

### 4.3 Mode, and the two timing details that bite in firmware

- **SPI mode 0 or 3 only** (W5500 datasheet chapter 2: mode 0 and mode 3 both
  idle SCLK low/high respectively and sample MOSI/MISO on the rising edge,
  toggle on the falling edge; MSB first). Mode 0 is the conventional choice.
- **`TCS` = SCSn high time >= 30 ns between frames.** At 20 MHz that is 0.6 SCLK
  periods, so any driver that deasserts CS for a full clock is fine - but a
  driver configured for `cs_ena_posttrans = 0` with back-to-back transactions
  can violate it. Firmware note, not a layout constraint.
- **Variable Length Data Mode** (host drives SCSn) is the mode to use; Fixed
  Length Data Mode requires SCSn tied to GND, which forfeits the ability to
  share the bus (W5500 datasheet 2.3 / 2.4, figures 4 and 5). Since CAR-REQ-06
  puts a **shared** SPI bus on the expansion connector, VDM is mandatory.

### 4.4 Does SPI need a `high_speed` entry? Yes - for SCLK only

`computed`: an ESP32-S3 GPIO at `PAD_DRIVER = 3` has an edge on the order of
2 ns into a short trace (`ASSUMED` - Espressif does not specify output slew in
the datasheet). Critical length for transmission-line behaviour is
`t_rise * v_prop / 6 = 2 ns * 173 mm/ns / 6 =` **58 mm**. On a 100 x 80 mm board
with the W5500 near the RJ45 edge and the module elsewhere, a 40-60 mm SCLK run
is entirely plausible - i.e. **borderline**, which is the honest answer.

What that justifies:

- **One `high_speed` entry on `/ETH_SCLK`** with `reference: GND` and
  `t_rise_ns: 2.0`. The value is not the stitch radius (60 mm, meaningless) -
  it is that `check_return_path` will then verify the clock has a **continuous
  GND reference and never crosses a plane split**. On a board with a 48 V PD
  region, a 12 V rail and a 3.3 V rail, In2 will be partitioned, and a clock
  crossing that partition is the classic EMI failure. This entry is cheap
  insurance that a P8 script, not a human, catches it.
- **No entries for MOSI / MISO / CS / INT / RESET.** They are not periodic, so
  they do not build a spectrum, and the same corridor discipline follows for
  free if they are routed with SCLK.
- **No impedance control on any SPI net** and no `impedance_ohm` in the SCLK
  entry (see the rules_gen note in 9.4).
- **Series termination:** fit **22-33 ohm** at the ESP32-S3 end of SCLK (and
  optionally MOSI), placed at the driver pin, footprint fitted so the value can
  be tuned. `ASSUMED` value - neither Espressif nor WIZnet publishes an SPI
  source-termination number; TI's analogous MII rule is 50 ohm series on all
  outputs [SNLA079D 5.1], which is the right order of magnitude for a ~35-50 ohm
  microstrip. A series R also gives a place to slow the edge if EMC bites.
- **Length:** keep the whole SPI group under ~60 mm and route it as a group over
  unbroken GND. No length matching is required - the interface is not
  source-synchronous in a way that cares, and the timing budget at 20 MHz
  (25 ns half-period vs TOV 5 ns + ~0.35 ns flight for 60 mm) is enormous
  `computed`.

### 4.5 W5500 support components that must not be forgotten

From the W5500 datasheet pin table (Table 2) and figures 2-3:

| Pin | Symbol | Requirement |
|---|---|---|
| 10 | EXRES1 | **12.4 kohm 1%** external reference resistor to GND (Figure 2). Sets the MDI drive current - a wrong or wide-tolerance part shifts the 950-1050 mV output amplitude. |
| 20 | TOCAP | **4.7 uF** external reference capacitor |
| 22 | 1V2O | 1.2 V internal regulator output, **10 nF** |
| 18 | VBG | band-gap output, 1.2 V at 25 C - **leave NC** (datasheet: "Note: NC") |
| 7 | DNC | do not connect |
| 23 | RSVD | **must be tied to GND** |
| 38-42 | RSVD | internal pull-down, leave NC |
| 32 | SCSn | internal pull-up 50-112 kohm (Table, RPU) |
| 37 | RSTn | internal pull-up; hold low **>= 500 us** (TRC); PLL lock within 1 ms after release (TPL) |
| 43-45 | PMODE[2:0] | internal pull-ups -> default **111 = all-capable, auto-negotiation enabled**, which is what we want. Leave NC; do not accidentally pull one low. |
| 24-27 | SPDLED / LINKLED / DUPLED / ACTLED | **active low** outputs, IOL >= 8.6 mA at VOL 0.4 V - can sink a magjack LED directly through a series resistor if the jack's LEDs are common-anode. Check the jack's LED polarity before committing (CAR-REQ-09 / Q11 default (b) depends on it). |

Supply: VDD/AVDD 2.97-3.63 V; **IDD 132 mA typ while transmitting at 100M**
(datasheet 5.4) = 0.44 W on 3.3 V `computed`. That is ~29% of the entire 1.5 W
carrier overhead allocation before the ESP32-S3 is counted - worth handing to
the power architect. Inputs are 5 V tolerant (VIH max 5.5 V, 5.3).

---

## 5. 25 MHz reference crystal (CAR-REQ-04)

### 5.1 The datasheet requirement

W5500 datasheet **5.5.3 Crystal Characteristics**:

| Parameter | Range |
|---|---|
| Frequency | 25 MHz |
| Frequency tolerance (at 25 C) | **+/-30 ppm** |
| Shunt capacitance | 7 pF max |
| Drive level | 59.12 uW |
| Load capacitance | **18 pF** |
| Aging (at 25 C) | +/-3 ppm/year max |

XI/CLKIN (pin 30) also accepts a **single-ended 3.3 V TTL oscillator**, in which
case XO (pin 31) is left floating - a fallback worth remembering if the crystal
turns out to be the yield problem.

### 5.2 The ppm budget is tighter than it looks (E16)

IEEE 802.3 clause 25 requires the transmit clock to be **125 MHz +/-6.25 kHz**
[per UNH-IOL test 25.1.8, referencing 802.3 subclause 24.2.3.4] - that is
**+/-50 ppm total**, and everything has to fit inside it:

| Contributor | Budget |
|---|---|
| Crystal initial tolerance at 25 C | +/-30 ppm (W5500 spec) |
| Aging | +/-3 ppm/year |
| Temperature drift over 0-40 C ambient | typically +/-10 to +/-20 ppm for an AT-cut part `ASSUMED` |
| Load-capacitance error (wrong Cload caps) | +/-10 ppm or worse |
| **Total** | **at or over the +/-50 ppm ceiling** |

Consequences for P3 part selection, and this is the load-bearing finding of the
section: **do not buy a +/-50 ppm crystal**. Specify **+/-30 ppm initial or
better, +/-30 ppm or better over the operating temperature range, AT-cut
fundamental, CL = 18 pF**, and treat the total (initial + temp + aging) as the
number that must stay under +/-50 ppm. A +/-10/+/-20 ppm part costs cents more
and removes an entire class of "link comes up but drops under load" failure.

### 5.3 Load capacitors (E17)

Standard relation: `CL = (C1 * C2) / (C1 + C2) + Cstray`, so with `C1 = C2 = C`,
`C = 2 * (CL - Cstray)`.

`computed` with `Cstray = 4 pF` (`ASSUMED` - a typical pin + short-trace figure;
Atmel AVR186 quotes XTALIN-to-GND 1 pF, XTALOUT-to-GND 2 pF, XTALIN-to-XTALOUT
0.5 pF as *package* parasitics, to which trace capacitance adds):

| Cstray | C1 = C2 |
|---|---|
| 3 pF | 30 pF |
| **4 pF** | **28 pF -> use 27 pF** |
| 5 pF | 26 pF |

**Specify 27 pF C0G/NP0, and expect to trim it on the first prototype** by
measuring the actual link frequency. Note that most W5500 module schematics in
the wild use 22 pF, which back-solves to CL ~ 15 pF - fine for a crystal
specified at 15 pF, wrong for the datasheet's 18 pF. Check the crystal's own
CL spec against this table rather than copying a module.

Drive level 59.12 uW is low; if the chosen crystal specifies a lower maximum
drive than the oscillator delivers, a series resistor between XO and the crystal
is the standard fix (TI SNLA079D 6.2 describes the same technique).

### 5.4 Crystal layout keepout (E18)

Sourced rules:

- WIZnet HW design guide: "Place the Crystal and Oscillator as close as
  possible"; "Because it is a high-frequency signal, it is recommended to design
  without Via in layers such as Chip during Artwork"; "only one chip connected
  to one oscillating element"; and for MDI, "It is not good to have a high
  frequency device around (OSC, etc.)" - i.e. **the crystal must be kept away
  from the MDI pairs**, which fights the "crystal close to the chip" rule and
  has to be resolved by putting XI/XO on the opposite side of the W5500 from
  TXP/TXN/RXP/RXN.
- Atmel AVR186 (oscillator PCB layout): place away from high-frequency devices
  and traces; keep clock and frequently-switching lines as far from the crystal
  connections as possible; load-capacitor ground connection short and clear of
  USB/PWM/power return currents; **load caps NP0/C0G**, placed close to each
  other with the XTALIN cap first and closest; keep parasitic capacitance
  minimal; "**A ground area should be placed under the crystal oscillator area.
  This ground land should be connected to the oscillator ground**"; connect the
  crystal housing to the ground plane; guard ring around the oscillator
  components if there is only one layer.

Practical constraint set for P6/P7:

1. **Crystal + both load caps as one placement group**, anchored on the crystal,
   with XI/XO traces <= 5 mm `ASSUMED`.
2. **Solid GND land on F.Cu directly under the crystal**, stitched to In1 GND,
   with the crystal can tied to it.
3. **No traces of any kind on F.Cu or In1 under or beside the crystal group** -
   a local keepout of ~2 mm around the group `ASSUMED` (no vendor gives a
   number; this is the smallest ring that reliably fits between an 3225 crystal
   and neighbouring parts).
4. **Crystal group >= 7.5 mm from the MDI pairs**, borrowing Pulse's
   digital-to-MDI separation figure, and on the far side of the W5500 from the
   magjack.

Constraints.json expression: this is a `placement.groups` entry
(`{"name": "eth_xtal", "anchor": "Y1", "members": ["C..", "C.."]}`) plus a
`placement.separation` entry between the crystal group and the magjack /
MDI parts. **Neither key is in this fragment's four-key contract** - handed to
the architect as a merge suggestion (9.5).

---

## 6. ESD and protection on the MDI (E27)

**What the W5500 gives you.** Device-level only: HBM 2000 V (class 2), MM 200 V
(class B), CDM 500 V (class III), latch-up class I +/-200 mA (datasheet 5.2).
These are *handling* ratings and say nothing about a cable strike.

**What the magjack gives you.** 1500 Vrms of 50/60 Hz isolation. That blocks DC
and mains-frequency faults; it does **not** block a fast ESD event, which
couples straight through the interwinding capacitance. Integrated magnetics
change the *geometry* of the problem (no exposed cable-side copper on the board,
shorter exposed run) but do not remove it.

**What PoE adds.** The PD front end is itself a large ESD/surge target and the
PD controller is usually the part that owns the clamp. AN956 section 6: the
Si3402-B "has an input clamp that will protect it against surges as spelled out
in IEEE 802.3", which specifies "a 1000 V surge with 0.3 usec rise time and
50 usec fall time applied to each conductor through a series resistance of
402 ohm", and the part is designed to handle the resulting 50 us / 5 A pulse.
The EVB is stated to meet up to 16 kV system-level ESD. **The PD side of this
board is protected by the sibling agent's controller choice, not by anything in
this fragment** - which is worth stating explicitly so nobody double-fits.

**Recommendation for the MDI (my half):**

- Fit a **4-channel low-capacitance TVS array on the PHY side of the
  magnetics**, across TXP/TXN and RXP/RXN, at the magjack end of the pairs.
  Placement rule from Semtech's Ethernet protection guidance: TVS on the PHY
  side of the transformer, across each signal-line pair, as close to the strike
  entry point as possible.
- **Capacitance <= 1 pF per line** is the binding parameter: the transmitter
  must still meet 10 dB return loss (2.2), and MDI-grade arrays in the 0.9 pF
  class exist precisely for this. A general-purpose ESD array at 20-50 pF/line
  will visibly degrade the eye.
- **Fit it, do not DNP it.** The counter-argument (indoor fixture, plastic
  enclosure, permanently-connected cable) is real, but the fixtures get handled
  during commissioning of 8-12 units, the cable is a 100 m antenna into a
  basement, and the part is one 6-pin package. This is a judgement call, stated
  as such.
- Also copy AN956's **1 nF capacitors on the RJ45 conductor paths for ESD
  immunity** (C10-C17) and its 330 ohm ferrite beads - but coordinate with the
  PoE agent, since those sit on the *power* taps and are that agent's schematic.

---

## 7. ESP32-S3 pin constraints (gate 5, half two)

Requirements section 2 is explicit: "Chosen ESP32-S3 pins must **not** be
strapping, USB, or SPI-flash pins (verified at schematic sign-off)". This
section is the legality list the architect needs. Written against the **Q7
default: ESP32-S3-WROOM-1, 8 MB flash, no PSRAM** - and flagging where a
different SKU changes the answer.

### 7.1 The module pinout (41 pins) - what exists at all

Available IO on ESP32-S3-WROOM-1 [datasheet v1.8 Table 3-1]:
GPIO0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
21, 35, 36, 37, 38, 39, 40, 41, 42, 43 (TXD0), 44 (RXD0), 45, 46, 47, 48.
GPIO33 and GPIO34 are **not brought out**.

### 7.2 Forbidden and constrained pins

| Class | Pins | Why | Verdict |
|---|---|---|---|
| **Strapping - boot mode** | **GPIO0** | Weak pull-up, default 1. `1` = SPI Boot, `0` + GPIO46 `0` = Joint Download Boot | **Do not use.** Reserve for a BOOT button (Q9 default (b) header) |
| **Strapping - boot + ROM print** | **GPIO46** | Weak pull-down, default 0 | **Do not use.** |
| **Strapping - VDD_SPI voltage** | **GPIO45** | Weak pull-down, default 0 = VDD_SPI 3.3 V. **Pulled high at reset = 1.8 V flash rail = the module does not boot.** | **Do not use.** The most dangerous of the four. |
| **Strapping - JTAG source** | **GPIO3** | **Floating, no internal pull.** Datasheet: "this pin does not have any internal pull resistors and the strapping value must be controlled by the external circuit that cannot be in a high impedance state" | **Avoid.** Usable only if nothing loads it during the 3 ms hold window |
| **USB** | **GPIO19 (USB_D-), GPIO20 (USB_D+)** | Default-connected to the USB Serial/JTAG controller. Also: GPIO19 has a low-level glitch + two 60 us high-level glitches (3.2 ms total window); GPIO20 has a pull-down glitch + high-level glitches (2 ms total) [S3 datasheet Table 2-2] | **Do not use**, whatever Q9 decides. The power-up glitches alone disqualify them for CS or RESET |
| **SPI flash / PSRAM (bare chip)** | GPIO26 (SPICS1), 27 (SPIHD), 28 (SPIWP), 29 (SPICS0), 30 (SPICLK), 31 (SPIQ), 32 (SPID) | "It is not recommended to use the pins connected to flash/PSRAM for any other purposes" [S3 datasheet 2.7, Table 2-14] | **Not applicable on WROOM-1** - these are internal to the module and not on the pinout. Listed because gate 5 names them, and because they come back if Q7 flips to a bare chip |
| **Octal PSRAM (SKU-dependent)** | **GPIO35, GPIO36, GPIO37** | "For modules with Octal SPI PSRAM, i.e., modules embedded with ESP32-S3R8 or ESP32-S3R16V, pins IO35, IO36 and IO37 are connected to the Octal SPI PSRAM and are not available for other uses" [WROOM-1 datasheet Table 3-1 note b] | **Free on the -N8 (no-PSRAM) SKU, forbidden on -N8R8 / -N16R8V.** Use only if the SKU is frozen. GPIO33/34 (the other octal lines) are not on the module at all |
| **1.8 V on one SKU** | GPIO47, GPIO48 | On ESP32-S3R16V, VDD_SPI is 1.8 V so GPIO47/48 run at 1.8 V [note c] | Avoid unless the SKU is frozen as non-R16V |
| **JTAG** | GPIO39 (MTCK), 40 (MTDO), 41 (MTDI), 42 (MTMS) | Usable, but using them forfeits hardware JTAG | Usable, low priority |
| **UART0** | GPIO43 (TXD0), GPIO44 (RXD0) | Default ROM/console UART | **Reserve** for the Q9 default recovery header |
| **ADC2** | GPIO11-20 | "ADC2 analog functions cannot be used with Wi-Fi simultaneously" [S3 datasheet 2.3.3] | Fine for **digital** use; never assign the CAR-REQ-07 ID divider or a thermistor here. Analogue must live on **ADC1 = GPIO1-10** |
| **Power-up glitches** | GPIO1-14, 15/16 (XTAL_32K), 17, 18, 19, 20 | ~60 us glitches at power-up [Table 2-2] | Harmless for SPI; **relevant to CAR-REQ-08 ENABLE (gate 4): the daughter ENABLE must be active-HIGH so a low-level glitch is a no-op** |
| Timing | all strapping pins | `tH` = **3 ms** hold after EN goes high before straps become normal IO [Table 4-2] | Anything sharing a strapping pin must be high-Z for 3 ms after reset |

### 7.3 One legal set for the W5500 (recommendation, architect reconciles)

Chosen to (a) avoid every row above, (b) land on the **SPI2/FSPI IO_MUX** pins
so the 26 MHz GPIO-matrix ceiling does not apply, and (c) leave all of ADC1
free for the ID divider / thermistor:

| Signal | GPIO | Module pin | Function | Legality |
|---|---|---|---|---|
| `/ETH_SCLK` | **GPIO12** | 20 | FSPICLK (IO_MUX) | not strapping/USB/flash |
| `/ETH_MOSI` | **GPIO11** | 19 | FSPID (IO_MUX) | " |
| `/ETH_MISO` | **GPIO13** | 21 | FSPIQ (IO_MUX) | " |
| `/ETH_CSn` | **GPIO10** | 18 | FSPICS0 (IO_MUX) | " |
| `/ETH_INTn` | **GPIO14** | 22 | FSPIWP, unused in 4-wire | " |
| `/ETH_RSTn` | **GPIO21** | 23 | plain GPIO, no ADC, **no power-up glitch listed** | " |

Two schematic details that follow from the pin choice:

- **GPIO10 has a 60 us low-level glitch at power-up**, and low = W5500
  *selected*. Fit a **10 kohm pull-up from `/ETH_CSn` to +3V3** so the W5500 is
  deselected while the ESP32-S3 is in reset. The W5500's own SCSn pull-up is
  50-112 kohm (datasheet 5.3) - present, but weak, and it does not fight an
  actively-driven glitch.
- **`/ETH_RSTn` fails safe** because the W5500's RSTn has an internal pull-up:
  a floating ESP32-S3 pin during MCU reset leaves the W5500 *out* of reset,
  which is the behaviour we want. Still add an explicit 10 kohm pull-up so the
  state is not a datasheet-footnote dependency.

The four remaining SPI pins for the **expansion connector** (CAR-REQ-06, a
separate shared bus with per-device CS) must not collide with this set; SPI3 is
the natural home, and it is GPIO-matrix-routed, so the daughter bus is capped
around 26 MHz - fine for EEPROMs and LED drivers. **Flagged as OPEN-4.**

---

## 8. Stackup: 2-layer is not viable (E28)

**Recommendation: `JLC04161H-3313` (JLC standard impedance-controlled 4-layer,
1.6 mm, 1 oz outer / 0.5 oz inner).**

Three independent reasons, in order of strength:

1. **Impedance.** It is the only stackup in `stackups.yaml` that publishes a
   100 ohm differential profile (`diff_100`: 0.260 mm width, 0.210 mm gap,
   outer microstrip referenced to the nearest inner plane). `JLC2313_1.6` ships
   `controlled_impedance: []`, and the file's own comment explains why: a
   2-layer board has no adjacent reference plane. Running the solver anyway
   (2.2) gives **1.081 mm per leg** at a forced 0.30 mm gap - a 2.4 mm-wide
   differential pair, on a board that also has to fit a PD front end, a
   >= 60 V converter, a module and an expansion connector.
2. **Vendor guidance, from both silicon vendors involved.** TI SNLA079D section
   8: "To meet signal integrity and performance requirements, **at minimum a
   four layer PCB is recommended**". Skyworks AN956 section 8, for the PD half:
   "In general, **four-layer PCB designs yield the most robust design** ...
   Two-layer PCB designs must be carefully considered [and] Skyworks Solutions
   strongly recommends all two-layer PCB designs be reviewed before
   fabrication."
3. **Reference-plane discipline.** E3, the SCLK corridor (4.4), the plane void
   under the magjack (3.5) and the PD's plane partitioning all need independent
   GND and power planes. On 2 layers, B.Cu is simultaneously the MDI reference,
   the SCLK reference, the PD return and the 12 V/3.3 V distribution. There is
   no arrangement of that which survives P8.

Layer assignment that this fragment assumes when it says `reference: "GND"`:
**F.Cu signal (MDI, SPI, crystal), In1.Cu solid GND, In2.Cu power (split), B.Cu
signal/pour** - i.e. the `planes_gen` 4-layer default (In1 GND + In2 dominant
power). The MDI and SCLK stay on F.Cu referenced to In1 GND, which is the
0.2104 mm microstrip the `diff_100` profile is computed for.

---

## 9. What lands in constraints.json, and five traps

### 9.1 Trap: `high_speed` on the MDI vs the deliberate plane void

`check_return_path` (P8) raises an **error** (not a warning) for any corridor
deficit where >= 0.01 mm of trace centreline crosses missing reference copper,
and **`gate.py` has no waiver mechanism** (verified: no `waiv*` in `gate.py`).
Section 3.5 deliberately voids the planes under the magjack. If the void is
drawn so that it reaches *under* the MDI traces, P8 will fail and there will be
no way to sign it off.

**Mitigation, and it is a layout instruction, not a constraint:** the plane void
must begin **at the magjack's PHY-side pad row and extend away from the board
interior** - the MDI pairs terminate on those pads and must never cross the
plane edge. `planes_gen` supports only rectangular positive `region`s per plane
(no keepouts, no voids - verified in the source), so the void has to be created
by *sizing the GND/power `region` rectangles to stop short of the connector*,
not by declaring a keepout. **Flagged as OPEN-2.**

### 9.2 Trap: net names must exist, and one check is unforgiving

- `check_return_path` **raises `CheckError` -> exit 2** on a `high_speed` net
  that is not on the board ("high-speed net 'X' not on board"). This gates P8
  hard.
- `check_diffpair` is gentler: a named pair whose nets are missing degrades to
  a **warning** (`diffpair_missing_net`), and other pairs still get judged.

All net names in the JSON fragment are **proposals** using the standard's and
the datasheet's conventional names. They must be reconciled with the sheet plan
at P2 and verified by `netlist_audit` at P4.

### 9.3 Not expressible in constraints.json

There is no key for: MDI total length (E8), inter-pair spacing (E9), MDI-to-
digital separation (E10), via count (E11), or "no stubs". These are
`route_critical` / manual constraints and must be carried in the routing plan,
not silently dropped because the schema has no slot.

### 9.4 `impedance_ohm` in `high_speed` is dead for explicitly-declared pairs

Verified in `rules_gen.detect_diff_pairs`: `high_speed[].impedance_ohm` is only
consulted for pairs that are **auto-discovered by name suffix**; an explicit
`diff_pairs` entry wins and takes its impedance from `diff_pairs[].impedance_ohm`.
This fragment therefore **omits `impedance_ohm` from the `high_speed` entries**
so a single-ended 50 and a differential 100 cannot end up fighting each other in
the merged file. The 100 ohm target lives in `diff_pairs` only.

Also note `diff_pairs[].gap_mm` is **centre-to-centre pitch**, not edge-to-edge
gap (`check_diffpair` docstring: "nominal centre-to-centre pitch"; it samples
distance between track *centrelines*). 0.470 mm = 0.260 width + 0.210 gap.
`rules_gen` ignores this value entirely and recomputes width/gap from the
impedance target - it only sets `check_diffpair`'s coupling threshold.

### 9.5 Keys this fragment does not emit but the merged file needs

Suggested `placement` entries, handed to the architect rather than emitted
(outside the four-key contract):

```jsonc
"placement": {
  "edges":  [{"ref": "J_RJ45", "edge": "left", "pos": 0.5}],
  "groups": [{"name": "eth_xtal", "anchor": "Y_ETH", "members": ["C_X1", "C_X2"]}],
  "separation": [{"a": ["Y_ETH"], "b": ["J_RJ45", "U_W5500"], "min_mm": 7.5}]
}
```

and, once the magjack outline is known, the GND/power `planes[].region`
rectangles of 9.1.

---

## 10. Sources

Primary (quoted above):

- **WIZnet W5500 datasheet v1.1.0** - pin table (EXRES1 12.4k 1%, TOCAP 4.7 uF,
  1V2O 10 nF, VBG NC, RSVD pin 23 to GND, PMODE defaults, LED polarity), 5.2
  ESD ratings, 5.3 DC characteristics, 5.4 power dissipation, 5.5.1 reset
  timing, 5.5.3 crystal characteristics, 5.5.4 SPI timing + the 80/33.3 MHz
  footnote, 5.5.5 transformer characteristics, 5.5.6 MDIX (no Auto-MDIX),
  chapter 2 SPI modes 0/3 and VDM/FDM:
  https://docs.wiznet.io/img/products/w5500/W5500_ds_v110k.pdf
- **WIZnet Hardware Design Guide** - 100 ohm differential / <50 ohm
  single-ended, 25 mm recommended / 75 mm max MDI length, W >= 20 mil TX-to-RX
  with 30 mil example, K >= 20 mil to other signals, "TX+/- and RX+/- signals
  prohibit Via or Layer changes", "All PCB layers under the Transformer and
  RJ45 Connector must have no power and GND plane", crystal placement:
  https://docs.wiznet.io/Design-Guide/hardware_design_guide
- **WIZnet Ethernet Design Guide (ENG)** - AGND vs system GND for TCT/RCT
  returns, GND pattern between TX and RX, "the impedance of Ethernet is 100
  ohms", oscillator without vias, one chip per oscillator:
  https://docs.wiznet.io/img/design_guide/Wiznet%20Ethernet%20Design%20Guide_ENG.pdf
- **TI AN-1469 / SNLA079D, "PHYTER Design & Layout Guide"** (Apr 2013) - 2.1
  layout rules and "50 ohm to ground or 100 ohm differential"; 2.3 Bob Smith
  (75 ohm + 1000 pF, cap >= 2 kV) **and the note that it does not apply to
  PoE**; 2.4 shielded RJ45 to chassis ground, do not overlap chassis and circuit
  ground planes, two 1206 zero-ohm resistors across the void; Table 2 crystal
  requirements; Table 4 magnetics requirements (1:1 +/-2%, 1500 Vrms); section 8
  "at minimum a four layer PCB is recommended"; 10.2 void planes under
  magnetics: https://www.ti.com/lit/an/snla079d/snla079d.pdf
- **Pulse Electronics, "Layout Considerations for Pulse Ethernet Magnetics and
  Connector Modules" v7** - PHY-to-magnetic >= 25 mm, PHY and pairs >= 25 mm
  from the board edge, no digital signal within 300 mil (7.5 mm) of the pairs,
  <= 10 mil separation within a pair, at most two vias per trace, "no ground
  planes beneath a discrete LAN magnetics package" but "for integrated connector
  modules the chassis ground plane should run under the component", the 5-20 ohm
  edge-coupling error in naive calculators, PoE best practices (BST advisable
  for EMI, "included in most connector solutions"), 15 mil minimum FR-4
  isolation thickness for 1500 Vrms:
  https://yageogroup.com/content/Resource%20Library/Technical%20Article/Pulse_Layout-Considerations-v7.pdf
- **UNH-IOL Fast Ethernet Consortium, Clause 25 PMD Test Suite v3.5** - test
  25.1.1 output amplitude 950-1050 mV and 98-102% symmetry [X3.263 9.1.4];
  25.1.2 rise/fall **3-5 ns**, symmetry <= 0.5 ns [9.1.6]; 25.1.3 DCD +/-0.25 ns
  on a 16 ns grid [9.1.8]; 25.1.4 transmit jitter <= 1.4 ns pk-pk [9.1.9];
  25.1.6 return loss >= 10 dB [9.1.5]; 25.1.8 transmit clock **125 MHz
  +/-6.25 kHz** [802.3 24.2.3.4]:
  https://www.iol.unh.edu/sites/default/files/testsuites/ethernet/CL25_PMD/PMD_Test_Suite_v3.5.pdf
- **Skyworks AN956, "Using the Si3402-B PoE PD Controller in Isolated and
  Non-Isolated Designs"** rev 0.2 - section 1 the ~10 W regulated-power figure
  and 350 mA Type 1 current; section 2 figures 3/4 with the RJ45 centre-tap and
  spare-pair wiring into CT1/CT2 and SP1/SP2, the 330 ohm beads and 1 nF ESD
  capacitors; section 6 the IEEE 802.3 1000 V / 0.3 us / 50 us / 402 ohm surge
  and 16 kV system ESD; section 8 four-layer recommendation:
  https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN956.pdf
- **Espressif ESP32-S3-WROOM-1 & WROOM-1U datasheet v1.8** - Table 3-1 pin
  definitions with notes b (IO35/36/37 on octal-PSRAM SKUs) and c (1.8 V
  GPIO47/48 on R16V); Table 4-1 strapping defaults; Table 4-2 tH = 3 ms;
  Table 4-3 boot mode; Table 4-4 VDD_SPI voltage; Table 6-2 IVDD >= 0.5 A:
  https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf
- **Espressif ESP32-S3 Series datasheet v1.6** - Table 2-1 pin overview,
  Table 2-2 power-up glitches (incl. GPIO19/20 3.2 ms / 2 ms windows), 2.3.3
  restrictions for GPIOs, 2.6 strapping pins, Table 2-14 pin mapping between
  chip and in-package flash/PSRAM:
  https://www.espressif.com/documentation/esp32-s3_datasheet_en.pdf
- **Espressif ESP-IDF, SPI Master driver (ESP32-S3)** - "Typical maximum
  frequency ... 80 MHz (IOMUX pins) and 26 MHz (GPIO matrix pins)"; SPI2 IO_MUX
  pins CS0 = GPIO10, MOSI = GPIO11, SCLK = GPIO12, MISO = GPIO13; driver
  re-derives the clock to a hardware-compatible value:
  https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/spi_master.html
- **Atmel AVR186, "Best Practices for the PCB Layout of Oscillators"**
  (Atmel-8128B, 09/2016) - keep away from high-frequency devices and traces,
  clock lines far from the crystal, short load-cap ground clear of USB/PWM/power
  returns, NP0/C0G load caps placed close together with XTALIN first, package
  parasitics 1 pF / 2 pF / 0.5 pF, ground area under the crystal tied to
  oscillator ground, guard ring on single-layer boards:
  https://ww1.microchip.com/downloads/en/Appnotes/Atmel-8128-Best-Practices-for-the-PCB-Layout-of-Oscillators_ApplicationNote_AVR186.pdf
- **Semtech, "Ethernet Protection Methodology"** - TVS on the PHY side of the
  magnetics across each pair, low capacitance for 10/100/1000:
  https://blog.semtech.com/ethernet-protection-methodology

In-repo (used for the numbers that land in constraints.json):

- `.claude/skills/ai-ee/reference/stackups.yaml` - `JLC04161H-3313`
  `diff_100` profile (0.260 / 0.210), `JLC2313_1.6` `controlled_impedance: []`.
- `.claude/skills/ai-ee/scripts/lib/impedance.py` - `diff_pair()`; the 2-layer
  widths in 2.2 were produced by running it, as was the 0.30 mm gap clamp.
- `.claude/skills/ai-ee/scripts/check_diffpair.py` - `gap_mm` is centre-to-centre
  pitch; `coupling_max = max(3 * pitch, pitch + 0.5)`; epsilon-based ps
  conversion; missing-net -> warning.
- `.claude/skills/ai-ee/scripts/check_return_path.py` - `r = c / (f_knee * 20)`;
  `CROSSING_ERROR_MM = 0.01`; missing net -> `CheckError` -> exit 2.
- `.claude/skills/ai-ee/scripts/rules_gen.py` - `detect_diff_pairs`
  (explicit `diff_pairs` wins; `high_speed[].impedance_ohm` only used for
  auto-discovery), `diff_pair_rules` recomputes width/gap from impedance.
- `.claude/skills/ai-ee/scripts/planes_gen.py` - rectangular positive `region`
  only; no keepout/void expression.
- `.claude/skills/ai-ee/scripts/gate.py` - no waiver mechanism.

---

## 11. Open items for the architect

1. **OPEN-1 (blocks 3.4): Q5 is unanswered and this fragment cannot close it.**
   Isolated vs non-isolated PD, and enclosure material, decide whether a chassis
   ground plane exists at all. Under the Q5 default (non-isolated, plastic,
   Ethernet-only) there is no chassis ground to moat against and the classic
   TI/Pulse split-plane construction is inapplicable. If Q5 returns "isolated
   flyback" or "metal enclosure", section 3.4 and 3.5 must be redone before P5.
2. **OPEN-2 (blocks P7/P8): how to express the plane void under the magjack.**
   `planes_gen` has no keepout key; the void must be produced by sizing the
   GND/power `region` rectangles. If the MDI pairs end up crossing the plane
   edge, `check_return_path` errors and there is no waiver. Decide the plane
   partition geometry at P5, not at P7.
3. **OPEN-3 (blocks P3): the magjack must be a PoE part with the four power taps
   on package pins**, rated for 802.3at tap current (not just af, per D-01's
   "resistor change only" promise), 1:1 / 350 uH per the W5500, 1500 Vrms
   isolation, LED polarity compatible with the W5500's active-low outputs, and
   available at JLCPCB under the Q14 assumption. This is a narrow part class;
   confirm availability before freezing the board outline (MECH-02), because a
   panel-mount fallback (Q12) changes the outline.
4. **OPEN-4: expansion-connector SPI vs W5500 SPI.** This fragment recommends
   SPI2 IO_MUX (GPIO10-13) for the W5500. The CAR-REQ-06 shared daughter bus
   then needs SPI3 through the GPIO matrix, capped near 26 MHz. Confirm that is
   acceptable for whatever a daughter's LED driver needs, and that the two buses
   do not share a CS.
5. **OPEN-5: ESP32-S3 SKU freeze.** GPIO35/36/37 are legal on -N8 (Q7 default)
   and forbidden on any octal-PSRAM SKU; GPIO47/48 run at 1.8 V on -N16R8V. If
   the design uses any of those five pins, the SKU becomes part of the ICD.
   Recommendation: **do not use GPIO35-37 or GPIO47/48 at all**, so the module
   SKU stays a stocking decision rather than a design dependency.
6. **OPEN-6: crystal ppm budget (5.2).** +/-30 ppm initial is the datasheet
   floor, but the standard's total budget is +/-50 ppm including temperature and
   aging. P3 must select on the *total* figure. This is the kind of number that
   passes on the bench and fails in a cold garage.
7. **OPEN-7: `voltages` deliberately empty here.** The PoE agent owns them.
   Confirm that its list covers the **magjack tap nets**, which is where 48 V
   comes closest to the MDI copper (3.6).
8. **OPEN-8: MDI TVS is a judgement call (section 6).** Recommended fitted;
   if the architect prefers DNP footprints, record it as a decision rather than
   an omission, and keep the capacitance spec (<= 1 pF/line) in the BOM note so
   a later "just fit any ESD array" does not break return loss.
9. **Documentation item:** the W5500 has **no Auto-MDIX** (2.5). A
   straight-through cable to the managed switch is required; a direct
   PC-to-fixture connection needs a crossover. Worth one line in the fixture
   manual.
