# Requirements: LUM-DTR-STROBE-A (LUMINA strobe daughter board)

Sources, in precedence order (later overrides earlier where they conflict):

1. `brief/00-lumina-system-context.md` - shared system context.
2. `brief/01-carrier-board-brief.md` - the mating carrier. CONTEXT ONLY, not this board.
3. `brief/02-strobe-daughter-brief.md` - this board's brief.
4. `brief/05-lumina-closed-decisions.md` - BINDING. Supersedes `00` section 6 and corrects
   several figures in `00` section 5 and `02` section 3.
5. `brief/06-connector-icd.md` - the frozen expansion connector ICD. A HARD input. Never
   redefined by this board. Per its own preamble, where a number appears in more than one
   place the ICD is the one that governs.

Unstated low-risk items are marked `ASSUMED:` inline. Section 9 holds every design-changing
or safety-relevant unknown. D-01, D-02 and D-03 are CLOSED and are recorded here as settled
requirements, not questions.

---

## 1. Function

A fixture-specific daughter board that stacks above the universal LUMINA carrier
(LUM-CAR-A) on 11.0 mm standoffs and mates through the frozen 38-position expansion
connector. It contains the entire light engine for a strobe fixture: a local energy store on
the 48 V raw PD rail, an inrush limiter, a mandatory bleed path, a drive stage that dumps
that store into a series white LED string in short high-current bursts with hard optical
edges, sense outputs (bank voltage, LED temperature) back to the carrier's ADCs, an
over-temperature shutdown that acts independently of firmware, and the board-ID mechanism
that lets one firmware image recognise this as a strobe.

It carries no MCU, no network interface, no power conversion from mains, and no external
connector of any kind. Strobe pattern generation, the average-energy governor and colour
algorithms are host/firmware, not hardware - the hardware's job is to expose what the
governor needs and to fail safe without it.

Quantity: 4-6 boards, part of a first build of 8-12 fixtures.

**The board exists to solve one problem:** turn a ~8.5 W sustained power budget into short,
violent bursts of light with sub-millisecond edges, and degrade gracefully (dimmer flashes,
never missed flashes, never a reset) when the music asks for more than the rail can deliver.

---

## 2. Interfaces

All external electrical connection is through two board-to-board sockets on the **bottom**
side of this board. **No other connector may be added** (ICD s9): no barrel jack, no DMX, no
second Ethernet, no USB. The only permitted additional wiring is internal to the enclosure
(the LED string - see open question 4).

### 2.1 J3 - POWER block

- Part: **CONNFLY DS1023-2*7SF11**, 14 positions, 2.54 mm, 600 V, 3.0 A/contact, 8.5 mm body.
- Orientation: **faces downward** - reverse-mounted THT on the bottom side, or a bottom-side
  SMD equivalent (ICD s7.3). See open question 6.
- Position 1 silkscreen-marked with a triangle.
- Nominal body extent **(14, 68) - (34, 78)**; position 1 at (15.3, 69.3), long axis along +x.
  **Provisional until the end of the carrier's P6** (ICD s7.2) - see open question 9.

| Col | Row A | net | Row B | net |
|---|---|---|---|---|
| 1 | 1 | `+48V_SW` | 2 | `GND` |
| 2 | 3 | `+48V_SW` | 4 | `GND` |
| 3 | 5 | `+48V_SW` | 6 | `GND` |
| 4 | 7 | `GND` (guard column) | 8 | `GND` |
| 5 | 9 | `+12V` | 10 | `GND` |
| 6 | 11 | `+12V` | 12 | `+3V3` |
| 7 | 13 | `GND` | 14 | `+3V3` |

Design properties this map is built to have, each checkable by eye (ICD s3.1): the 48 V group
is at one end and bounded by GND on every side; **column 4 is an all-GND guard column**;
every supply pin has an adjacent GND; rail order along the connector is **48 -> GND -> 12 ->
3.3**, so no single-position mis-seat can put a higher rail on a lower rail's pin.

### 2.2 J4 - SIGNAL block

- Part: **CONNFLY DS1023-2*12SF11**, 24 positions, 2.54 mm, 600 V, 3.0 A/contact, 8.5 mm body.
- Orientation, marking and provisional-coordinate status: as J3.
- Nominal body extent (56, 68) - (88, 78); position 1 at (57.3, 69.3), long axis along +x.

| Col | Row A | net | Row B | net |
|---|---|---|---|---|
| 1 | 1 | `PWM0` | 2 | `PWM1` |
| 2 | 3 | `GND` | 4 | `GND` |
| 3 | 5 | `PWM2` | 6 | `PWM3` |
| 4 | 7 | `PWM4` | 8 | `PWM5` |
| 5 | 9 | `GND` | 10 | `GND` |
| 6 | 11 | `PWM6` | 12 | `PWM7` |
| 7 | 13 | `GND` | 14 | `DSPI_SCK` |
| 8 | 15 | `DSPI_MOSI` | 16 | `DSPI_MISO` |
| 9 | 17 | `DSPI_CSn` | 18 | `I2C_SCL` |
| 10 | 19 | `I2C_SDA` | 20 | `ADC0` |
| 11 | 21 | `ADC1` | 22 | `ID_ADC` |
| 12 | 23 | `ENABLE` | 24 | `FAULT` |

**No 48 V exists anywhere on J4.**

### 2.3 Signal electrical contract (ICD s3.3) - binding

| Signal | Direction | Rules this board must honour |
|---|---|---|
| `PWM0..7` | carrier -> daughter | 3.3 V push-pull CMOS. Default **13-bit at 9.766 kHz**. `PWM0-3` = LEDC timer 0, `PWM4-7` = LEDC timer 1. Channels on one timer share frequency AND resolution (CAR-REQ-11). Max 8 channels total (CAR-REQ-10) |
| `DSPI_*` | bidirectional | SPI mode 0, MSB first, <= 26 MHz. This board drives no line except MISO, and only while `DSPI_CSn` is low. Shared bus, one CS |
| `I2C_SCL/SDA` | bidirectional | Open drain, 400 kHz. **Pull-ups are on the carrier (4.7 k). This board must NOT fit its own** |
| `ADC0`, `ADC1` | daughter -> carrier | Analogue 0-3.3 V. **Source impedance <= 10 kohm** |
| `ID_ADC` | daughter -> carrier | Carrier fits the top leg (10 k to +3V3); **this board fits the bottom leg to GND**. Code allocated by the carrier owner - see open question 8 |
| `ENABLE` | carrier -> daughter | Push-pull CMOS, **active HIGH**. This board fits its own **100 kohm pull-down**, gates **every** output stage with it (including the cap-bank charge path), and **never latches it locally** |
| `FAULT` | daughter -> carrier | **Open drain, active low**, 10 k pull-up on the carrier, wire-OR'd with the carrier's eFuse fault. **Never drive it high** |

### 2.4 Carrier-facing functional requirements (from `02` section 6)

- **STR-REQ-17** - PWM channel count within the 8-channel ceiling. White-only needs 1-2;
  RGBW needs 4-5. Resolved by open question 1.
- **STR-REQ-18** - report bank voltage to a carrier ADC pin (feeds the governor, STR-REQ-06).
- **STR-REQ-19** - report LED thermistor temperature to a carrier ADC or I2C pin.
- **STR-REQ-20** - assert FAULT on over-temperature and shut down **independently of
  firmware**. Do not rely on the network or the MCU to prevent a thermal event.
- **STR-REQ-21** - honour the fail-safe ENABLE: outputs off with ENABLE de-asserted,
  including during MCU reset and firmware update.
- **STR-REQ-22** - populate the board-ID mechanism (CAR-REQ-07).

`ASSUMED:` bank voltage on `ADC0`, LED thermistor on `ADC1`, board ID on `ID_ADC`. If open
question 1 closes as RGBW and per-channel sense is wanted, the sense budget re-opens and the
extra channels must go on I2C.

`ASSUMED:` no SPI device on this board; `DSPI_*` left unconnected at the socket. Revisit only
if open question 1 closes as RGBW and the PWM budget forces an external LED driver.

### 2.5 LED string interface

- Series LED string driven from the 48 V bank (STR-REQ-12): ~2.6 A at roughly 38 V string
  voltage, versus ~8.3 A at 12 V. This is a closed consequence of D-02.
- Whether the emitters sit on this PCB or on a remote heatsink wired to it is **not settled**
  - see open question 4. Either way the string, its wiring and its heatsink are at PoE
  potential (section 8).

---

## 3. Power

### 3.1 What the connector delivers - ICD s6.2, binding

| Rail | Sustained (af) | Sustained (at) | Peak, ms-scale, from local bulk | Hardware fault ceiling | Connector pin capacity |
|---|---|---|---|---|---|
| `+48V_SW` | **0.25 A** | 0.50 A | 1.0 A (eFuse limit, until it latches) | 1.0 A, **latch off** | 5.40 A |
| `+12V` | 0.75 A | 1.25 A | 2.0 A | 2.0 A converter, OCP | 3.60 A |
| `+3V3` | 0.25 A | 0.25 A | 0.50 A | 1.0 A converter | 3.60 A |
| **TOTAL, all three rails** | **8.5 W** | **18.5 W** | - | PSE overload timer ~50-75 ms | - |

**The per-rail ceilings do not add up and are not meant to. The TOTAL is what binds.**
`05` states the closed-decision budget as 8.6-9.3 W (af) / 18.7-20.0 W (at) after 2.4/3.7 W
carrier overhead; the ICD's 8.5 W / 18.5 W governs where they differ. Design against **af**.

**Superseded, do not use:** the "~10 W regulated / ~8.5 W to the light engine" chain in `00`
section 5.1 and `02` section 3.1 derives from a Skyworks Si3402-B PD part this system does
not use. The carrier uses a TPS2378-class PD controller plus a 100 V buck (`05`).

**D-01 closed:** 802.3**at** power stage, **af** classification for the first build (resistor
change + a PoE+ switch upgrades it, no respin). **Daughter budgets are designed against af.**
Nothing on this board may become the part that pins the fixture to Type 1.

**ICD s6.3:** take power on `+48V_SW`, not `+12V`, wherever possible - it skips the 48->12
conversion and is worth 0.67 W (af) / 1.30 W (at) of extra delivered power, and it removes
the carrier's only real hot spot.

`ASSUMED:` this board's own housekeeping (gate drive bias, comparator, thermistor bias) is a
small fraction of the budget and is taken from `+3V3` and/or `+12V`; all LED energy comes
from the 48 V bank.

### 3.2 Energy store - D-02 closed

**The energy store runs off the 48 V raw rail from the connector.** Not 33,000 uF at 12 V.

| Item | Value | Source |
|---|---|---|
| Bank capacitance | **~2,800 uF** | D-02 closed, ICD s6.4 |
| Capacitor voltage rating | **>= 100 V** (63 V is NOT enough at 57 V worst case once ceramic DC-bias derating applies) | ICD s5.4 |
| Energy over the 48 -> 40 V window | **0.99 J** | ICD s6.4 |
| Energy at full 0 -> 48 V charge | **3.23 J** | ICD s6.4 |
| Max full-window flash rate the rail sustains | **8.6 Hz (af)** / 18.8 Hz (at) | ICD s6.4 |
| Energy per flash at SYS-REQ-03's 25 Hz ceiling | **0.34 J (af)** / 0.74 J (at) | ICD s6.4 |
| Bank droop per flash at 25 Hz | 48 -> 45.4 V (af) / 48 -> 42.1 V (at) | ICD s6.4 |
| Cold-start charge time at the ICD sustained limit | **0.54 s (af)** / 0.27 s (at) | ICD s6.4 |

SYS-REQ-03's 1-25 Hz range is reachable on af, at reduced per-flash energy above ~8.6 Hz.

- **STR-REQ-08** - select capacitors on **pulse ripple current and ESR**, not capacitance
  alone. A high-ESR bank sags harder than the ideal energy calculation predicts and softens
  the flash edge. **Ripple current rating must appear explicitly in the BOM.**
- **STR-REQ-09 / CAR-REQ-14** - inrush limiting is **this board's** responsibility (NTC or
  soft-start MOSFET). **Size it against the PD's 1.0 A operating current limit, not against
  the connector's 5.4 A rating** (ICD s8.2). Sizing against the connector is the classic way
  to trip the PD's 800 us foldback deglitch and brown out the entire fixture. The carrier's
  eFuse dV/dT is deliberately set fast and its limit sits above this board's inrush level so
  the two soft-starts do not fight.
- **STR-REQ-10 / CAR-REQ-17** - **bleed path across the bank is mandatory.** The carrier
  bleeds its own side through 100 kohm but **deliberately fits no series diode on
  `+48V_SW`**, so this board's bleed path is not stranded above the carrier's.

### 3.3 802.3 compliance clause - ICD s8.3, binding

IEEE 802.3 caps PD port capacitance at roughly 180 uF; this board's ~2,800 uF is 15x that.
The carrier's 48 V load switch is therefore a **compliance part**, off through detection,
classification, inrush and the 80 ms window, closing only after firmware asserts ENABLE.

1. **`+48V_SW` is DEAD at power-up and stays dead for hundreds of milliseconds.** Design for it.
2. **This board must provide NO path that energises its bank from `+12V` or `+3V3` while
   `+48V_SW` is off.** Doing so re-creates the compliance problem behind the switch's back.
3. **No mate sequencing exists.** A dual-row header has no first-mate/last-mate control, so
   this board must tolerate 48 V arriving **before or after** 3.3 V, in either order.

### 3.4 The governor, and a derived tension worth reading

- **STR-REQ-06** - firmware implements a leaky-bucket average-energy governor; the hardware's
  obligation is to expose bank rail voltage to the carrier ADC.
- **STR-REQ-07** - rail sag must degrade **gracefully**: dimmer flashes, never missed flashes
  or a reset. A dropped beat is more visible than a slightly dimmer one.

Derived arithmetic from the closed bank size (this is the substance of open question 2):

| Flash duration | Energy available (0.99 J bank, full window) | Implied drive power | Implied string current at ~38 V |
|---|---|---|---|
| 10 ms | 0.99 J | ~99 W | ~2.6 A (the closed figure) |
| 50 ms (STR-REQ-03) | 0.99 J | ~20 W | ~0.52 A |
| 100 ms (STR-REQ-01) | 0.99 J + rail | ~11-15 W | ~0.3-0.4 A |
| 200 ms (STR-REQ-01) | 0.99 J + rail | ~7-11 W | ~0.2-0.3 A |

At the closed 2.6 A drive current the bank holds full output for **~8.6 ms**
(`dt = C*dV/I = 2800 uF * 8 V / 2.6 A`), not the 100-200 ms STR-REQ-01 asks for. The "100 W
strobe" in Project Plan v1.0 and the worked example in `02` section 3.2 are a **10 ms**
operating point. **STR-REQ-01's 100-200 ms full-output flash and the closed bank size are not
consistent at 100 W** - a 150 ms flash lands near 15 W, roughly 6x below the 2.6 A peak the
drive stage is built for. This is not a blocker (the drive stage is still sized for 2.6 A
peak for short accents) but it fixes what "full output" means optically, and therefore fixes
the LED choice. Put to the human as open question 2.

---

## 4. Environment

| Item | Value | Source |
|---|---|---|
| Enclosure | **Plastic / 3D-printed, non-conductive.** Sealed (no forced airflow) | H1-Q5, ICD s9 |
| Internal air temperature | **56 C (af) / 69 C (at)** | ICD s7.6 |
| Connector contact rating | -40 to +105 C | ICD s1 |
| Room | ~5 x 7 x 2.5 m basement/garage, 8-12 fixtures | `00` section 1 |
| Ingress / vibration | Not stated | - |

- The 56-69 C internal ambient is a **capacitor selection constraint**: aluminium
  electrolytic life halves per 10 C, and the bank is the board's largest and most
  lifetime-sensitive part.
- **STR-REQ-15** - thermal path sized for the **sustained** average, with junction
  temperature during peak pulses checked against the pulsed derating curve. **Both cases must
  pass.**
- **STR-REQ-05** - survive 8-16 bars of maximum-rate flashing, then return to normal.
  `ASSUMED:` at typical tempos this is ~20-35 s. **Duration is not actually a free variable**
  for the thermal steady state: the rail caps sustained input at 8.5 W (af) regardless of how
  long the drop runs, so the steady-state thermal case is bounded by the rail, not by the
  bar count.
- `ASSUMED:` indoor, dry, benign. No ingress rating, no vibration or shock requirement, no
  condensation. Low risk - the fixture shares an enclosure with a PoE carrier already
  designed for the same conditions.

---

## 5. Size and mounting

Common LUMINA footprint (ICD s7.1) - **inherited, not chosen by this board**:

| Item | Value |
|---|---|
| Board outline | **100.0 x 80.0 mm** |
| Corner radius | **3.0 mm**, all four corners |
| Board thickness | **1.6 mm** |
| Mounting holes | **4x M3 (3.2 mm) at 5 mm inset** (a 90 x 70 mm hole rectangle) **plus a 5th M3 at (46, 74)** |
| Coordinate origin | board top-left corner, x right, y down |
| Stack arrangement | **Stacked mezzanine, daughter above the carrier** |
| Mated board-to-board height | **11.0 mm** hard-seated, against a positive mechanical stop |
| Standoffs | 5x M3 female-female, 11.0 mm |
| Socket orientation | **Faces downward** |

Per MECH-01, `board_init.py` needs `--corner-radius 3` explicitly (default is 0) and
`--mounting-holes 4`; the radius is clamped to the mounting-hole inset (`margin / 2`), so
3.0 mm works at the default `--margin 6`. Read `corner_radius` and `worker_notes` in the
board_init report - do not assume the requested value was honoured. H5 at (46, 74) is added
at P4 as a `MountingHole_3.2mm_M3` symbol so it carries a refdes.

Per MECH-02, **ai-ee has no outline-shrink step - the P5 outline is final.** The outline,
radius and hole pattern above are already closed by the ICD, so there is nothing to negotiate
here; but the notch below must be in the P5 outline, not retrofitted.

### 5.1 The RJ45 notch - HARD requirement from P2 onward

**A 30 x 26 mm relief in the TOP edge, region (6, 0) - (36, 26).** The outline rectangle,
corner radius and 5-hole pattern are unchanged; only this local relief differs.

Two independent reasons, both load-bearing:

1. The carrier's board-edge magjack is ~15 mm tall and the stack is 11.0 mm, so the jack
   protrudes ~4 mm above this board's underside. Without the notch the boards **cannot be
   forced flat**.
2. It is the **primary reverse-insertion interlock** (CAR-REQ-16). MECH-01's 4x M3 pattern is
   rotationally symmetric, so a daughter can be bolted down rotated 180 degrees; rotated, the
   notch lands at the bottom edge and the board presents solid material over the jack. This is
   a mechanical stop, not a warning.

### 5.2 Exclusion zones - ICD s7.6, all board-relative

| Zone | Region | Requirement |
|---|---|---|
| **DC-DC hot zone** | **(2, 46) - (36, 68)** | **No LED drivers and no aluminium electrolytics.** The carrier's 48->12 converter dissipates up to 1.25 W directly below in a sealed box. This is a vertical keepout, not an in-plane separation rule |
| **Antenna column** | **(88, 25) - (100, 55)** | **No copper on ANY layer** (no traces, no pour, no plane) **and no metal component.** The carrier's ESP32-S3 PCB antenna is directly below; a ground plane 11 mm above detunes it. Wi-Fi is a supported control path per H1-Q8, so this zone is live, not void |
| **Recovery header** | **(76, 0) - (98, 20)** | Keep clear enough that a 6-way jumper lead can be attached with this board fitted |

Note the interaction: the **DC-DC hot zone forbids aluminium electrolytics** exactly where a
large bank would otherwise like to live, and the **notch removes 780 mm2** from the top edge,
and the **antenna column removes a 12 x 30 mm strip** of all-layer copper from the right
edge. The 2,800 uF / 100 V bank must be placed around all three.

Reverse-insertion proofing also relies on: different position counts at fixed asymmetric
coordinates (a 2x7 socket cannot mate a 2x12 header); 180-degree rotation aligning neither
connector; the 5th mounting hole breaking the hole pattern's rotational symmetry; and
silkscreen - **a pin-1 triangle at position 1 of both blocks, plus a `^^ RJ45` edge arrow**
matching the carrier's.

### 5.3 Height

- Bottom side: the 8.5 mm socket bodies inside the 11.0 mm stack. `ASSUMED:` the two sockets
  are the only bottom-side parts; anything else must clear the carrier's top-side components
  in the same footprint region.
- Top side: **unknown.** The 100 V bank is the tallest thing on this board and radial parts in
  this class are tens of mm tall. See open question 5.

---

## 6. Quantity and budget

- **4-6 strobe daughter boards**, of 8-12 total fixtures in the first build.
- Also in the program: the universal carrier (8-12), the RGBW par daughter (6-8). **The UV bar
  is out of scope - D-03 closed as "no board"; allocate it no connector budget, no PWM
  channels, no power budget, no enclosure provision.**
- System budget: **$500-1000** for fixtures + switch + enclosures (`00` section 1). A managed
  8-16 port PoE switch takes a substantial share of that, so the per-fixture allowance is
  tight once the carrier, the daughter, the LED and its heatsink are counted.
- The ICD references a **"$30/board target"** (s1.1, in rejecting a $15.30 mated connector
  pair). Whether that figure is the carrier's or applies to this board is not stated. See
  open question 7.

---

## 7. Assembly

- Vendor: **JLCPCB PCBA**.
- `ASSUMED:` **single-sided (top) SMD assembly**, plus THT for the two connectors.
- The complication: the ICD requires the sockets to **face downward** - "a reverse-mounted THT
  part on the daughter's bottom side, or a bottom-side SMD equivalent." Reverse-mounted THT is
  not a standard JLC PCBA process, and a bottom-side SMD socket would make the assembly
  double-sided. **Open question 6.**
- Related: if the bank is built from radial aluminium electrolytics, those are THT parts too,
  which lands in the same process question.
- 4-6 boards is a hand-finishable quantity, so hand-soldering two connectors per board is a
  live option rather than a fallback.

---

## 8. Compliance and safety flags

Five apply. None can be guessed; the ones that need a human answer are in section 9.

### 8.1 48 V domain - exceeds 30 V

- Worst case **57 V DC** (IEEE 802.3 PSE maximum). Below the IEC 62368-1 **ES1** limit of
  60 V DC, so **functional insulation only** - no basic/supplementary/reinforced safeguard,
  and no safety-mandated creepage.
- **0.60 mm minimum outer-layer copper-to-copper spacing around every 48 V net, board-wide,
  from the connector pads to the cap bank** (IPC-2221B Table 6-1 column B2, 51-100 V band).
  **This is NOT inherited automatically - this board's DRC must be set up for it.**
- Inner layers: IPC gives 0.10 mm, below JLC's 0.127 mm minimum, so the fab minimum dominates
  and the HV requirement is free there. The clearance applies **through the board too** - an
  inner-layer or opposite-face signal passing under a 48 V antipad needs the same.
- **The 0.13 mm "permanent polymer coating" column (B4) is NOT claimed.** Standard LPI
  soldermask is not a qualified conformal coating, and `check_creepage.py` implements only the
  uncoated columns - a layout designed to 0.13 mm fails P8 with no waiver mechanism.
- **Any resistor across the 48 V domain must be 0805 or larger** (0402/0603 are typically
  50-75 V working) or split into two in series. **This bites the mandatory bleed resistor and
  the 48 V rail-sense divider** - which also has to present <= 10 kohm to the carrier ADC.
- **Capacitors on the 48 V domain must be 100 V rated.**

### 8.2 High pulse current - ~2.6 A LED drive

Series-string drive at ~2.6 A peak from a ~48 V bank (STR-REQ-12). Below the 3 A continuous
threshold, but pulsed and with deliberately fast edges, so it is flagged: trace width and
copper weight, gate drive, current-limit accuracy and switching loop area all have to be
sized against the pulse, not the average. The superseded 12 V topology would have been 8.3 A;
avoiding that is the whole point of D-02.

**STR-REQ-13** - verify the candidate LED's **pulsed** forward current derating curve, not
its DC maximum. The operating point is short high-current pulses at low duty cycle.

### 8.3 Stored energy hazard - up to ~3.23 J

- ~2,800 uF charged to 48 V holds **3.23 J**, and it holds it **with the cable unplugged**.
- **Bleed path is mandatory** (STR-REQ-10, CAR-REQ-17), and the carrier fits no series diode
  on `+48V_SW`, so this board's bleed path is not stranded above the carrier's.
- The board must be **safe to handle during assembly and service**. Silkscreen warning and a
  defined bleed time constant are part of the deliverable.
- A short across a charged bank is a large, fast fault current independent of any rail limit.

### 8.4 Non-isolated topology floating at PoE potential

**The entire fixture is non-isolated and floats at PoE potential.** Every one of these is
load-bearing and lands on this board as much as on the carrier:

- **Non-conductive enclosure**, no chassis earth, no earthed mounting hardware bonded to
  board GND.
- **Ethernet is the only external connection. This board may not add an external connector of
  any kind.**
- **This board, its drive stage, its LED string and its LED wiring are all at PoE potential.**
  If the LED module sits on a separate heatsink, **that heatsink and its wiring are at PoE
  potential too.** The heatsink must not be user-accessible (H1-Q5) and must not share a mount
  with anything earthed - if it is touchable, metal and earthed, the non-isolated topology is
  non-conformant. (ICD notes this as carrier `decisions.md` OPEN-C, unresolved there;
  H1-Q5 closes it for this program as "plastic enclosure, heatsink enclosed".)
- **Bench hazard.** An earthed scope probe or a non-isolated USB-UART adapter ties the
  floating PoE return to earth. Beyond shock and damage risk, the resulting ground currents
  **break PD signature detection outright** (detection currents are only a few hundred
  microamps). **Every test point on this board carries the same silkscreen warning the
  carrier's recovery header does.**
- **No MOV-to-earth surge network.** An unearthed PD does not need one; do not copy one out of
  a reference design.

### 8.5 Thermal - independent of firmware

**STR-REQ-20** - over-temperature must shut the output down and assert FAULT **without the
MCU and without the network**. ~8.5 W sustained inside a sealed plastic box at 56-69 C
internal air, with the LED junction also seeing peak pulses, is the case that has to fail
safe on its own.

### 8.6 Not applicable

No mains voltage. No battery of any chemistry, no charging circuit. No motors. No RF
transmitter on this board (the radio is on the carrier; this board's only RF obligation is
the antenna column keepout in section 5.2).

---

## 9. Open questions

Nine. Questions 1-4 change what gets designed; 5-9 are narrower but still block a decision.
Defaults are offered where a sensible one exists - answering "default" to any of them is a
valid answer.

---

**1. White-only or RGBW? (D-04 - this board owns it)**

Does the strobe fire only white, or can it also fire saturated colour?

- **White-only** covers the dominant use: rage trap and hard French rap both call for white
  blasts, and SYS-REQ-07 wants clean neutral white rather than RGB-mixed white. Needs 1-2 PWM
  channels and one drive stage.
- **RGBW** adds the coloured blasts P8 (UK bass) asks for - "all fixtures fire red or green at
  80-100%". Needs 4-5 PWM channels, four drive stages, four times the LED selection and
  thermal work, and it splits the same 0.99 J bank four ways.

**Recommendation: white-only.** **The one tradeoff that matters:** the 6-8 RGBW pars already
produce coloured light, but they cannot strobe as hard as this board can - so choosing
white-only means coloured *blasts* are as fast as the pars allow, not as fast as the strobe
allows. If the coloured-blast moments in P8 are meant to be percussive rather than atmospheric,
that is the argument for RGBW.

*Default if you have no strong feeling: white-only.*

---

**2. How much light per flash, and what is the fastest sustained flash rate the fixture
promises?**

Currently assumed 1 J per flash at an unbounded rate. **Unbounded is not achievable** - the
rail delivers 8.5 W and nothing stores more than the bank holds. The arithmetic (ICD s6.4):

- Bank stores **0.99 J** per full flash (48 -> 40 V).
- **8.6 Hz** is the fastest rate at which every flash can be a full 0.99 J flash.
- Above that, energy per flash must fall. At the 25 Hz ceiling (SYS-REQ-03) it is **0.34 J**.
- A PoE+ switch later (the D-01 upgrade, resistor change only) roughly doubles both: 18.8 Hz
  full-energy, 0.74 J at 25 Hz.

**And a second half to this question that the briefs have not reconciled:** STR-REQ-01 asks
for a **100-200 ms** full-output flash, but 0.99 J spread over 150 ms is only about **15 W**
of drive - the "100 W strobe" figure is a **10 ms** operating point, and at the closed 2.6 A
drive current the bank holds full output for only ~8.6 ms. So:

- Short accents (10-50 ms, STR-REQ-03) can be genuinely violent: ~20-99 W.
- Long flashes (100-200 ms, STR-REQ-01) land at ~7-15 W.

*Default: accept it. Per-flash energy capped at 0.99 J; full-energy flashes up to 8.6 Hz,
tapering to 0.34 J at 25 Hz, enforced by the firmware governor; "full output" for a 150 ms
flash means ~15 W of LED drive, and the LED is chosen so that this reads as bright in a 5 x
7 m room with 4-6 strobes firing together.*

*If you instead want a 100-200 ms flash that is blinding at 100 W, the bank has to grow by
roughly 10x, which means re-opening D-02's sizing with the carrier owner - a blocking issue
against LUM-CAR-A, not something this board can decide.*

---

**3. LED family and beam angle**

No candidate has been evaluated (STR-REQ-13 to STR-REQ-16). Two parts:

- **(a) Vendor/family preference?** The project plan names CREE and Lumileds as a direction
  only. *Default: no preference - the architect picks on availability at JLCPCB, pulsed
  derating data, and neutral/cool white with no colour cast at full current (a green or pink
  tint at peak is a defect, STR-REQ-14).*
- **(b) Beam angle?** The room is 5 x 7 m with a **2.5 m ceiling** - low. A narrow beam lights
  one square metre of floor and fails the room regardless of its lumen figure (STR-REQ-16).
  *Default: a wide beam, roughly 60-90 degrees, with an off-the-shelf lens or reflector rather
  than a custom optic.*

---

**4. Is the LED on this board, or on a separate heatsink wired to it?**

This changes the thermal design, the board area, and whether an internal wire-to-board
connection is needed. (Internal wiring is permitted - the ICD only forbids connectors that
leave the enclosure.)

- **On-board**: emitters soldered to this PCB with a heatsink bolted through it. Fewer parts,
  no wiring - but ~8.5 W sustained into a 1.6 mm FR4 board sandwiched 11 mm above the carrier
  in a sealed box is a poor thermal path, and it competes for area with the cap bank.
- **Off-board**: an LED module on its own heatsink, connected by two internal wires.

**Recommendation: off-board module on its own heatsink** - it is the arrangement the ICD
already assumes in section 9, and it decouples the LED's thermal problem from a crowded board.
Either way the heatsink is at PoE potential and must not be user-accessible.

*Default: off-board, connected by a 2-pin internal wire-to-board connector or solder pads
(architect's choice).*

---

**5. How much room is there above this board inside the enclosure?**

The 2,800 uF / 100 V bank is the tallest part on the board and parts in that class run to tens
of millimetres. The enclosure is not yet designed, so this is a number that needs setting
rather than discovering - and once P5 fixes the outline there is no shrink step.

*Default: state a ceiling of **30 mm** above the board's top face. If the intended enclosure
is shallower, say so now - it forces the bank toward a larger number of shorter cans or a
different capacitor technology, which changes the BOM cost and the board area.*

---

**6. Does the downward-facing socket force double-sided assembly at JLCPCB?**

The ICD requires the two sockets on the **bottom** side facing down. Three ways to build it:

- **(a)** Top-side SMD assembly at JLC, and hand-solder the two reverse-mounted THT sockets
  (and any THT electrolytics) locally. Cheapest, and 4-6 boards is a hand-finishable quantity.
- **(b)** Bottom-side SMD sockets, i.e. genuine double-sided assembly at JLC. Higher setup
  cost, but nothing to hand-solder.
- **(c)** Full JLC assembly including THT service.

*Default: (a).* *Answer changes: the board's assembly-side constraint from P4 onward, and the
capacitor technology (radial THT vs SMD).*

---

**7. What is the BOM cost target for one strobe daughter board, at quantity 6?**

The system budget is $500-1000 for 8-12 fixtures plus a managed PoE switch plus enclosures.
Once the carrier, the daughter, the LED and its heatsink are counted, the per-fixture
allowance is tight, and the LED plus the 100 V bank are the two expensive items on this board.
The ICD mentions a "$30/board target" but does not say whether that is the carrier's figure.

*Default: **$25 per board** for the PCB and its BOM at qty 6, **excluding** the LED module and
heatsink, which are budgeted separately with the fixture.*

---

**8. What board-type ID code is allocated to LUM-STR-A, and does this board carry an I2C
EEPROM?**

The carrier fits the top leg of the ID divider (10 k to +3V3); this board fits the bottom leg
to GND, and **the ICD says board-type codes are allocated by the carrier owner, not chosen by
daughters**. This board cannot pick its own value. The ICD also notes the Q10 default keeps an
I2C EEPROM alongside the divider, without saying whether the daughter or the carrier holds it.

*Default: request an allocation from the carrier owner and design to a placeholder value that
must be confirmed before P8; **divider only, no EEPROM on this board** (an EEPROM buys per-unit
calibration storage, which matters more for the colour-matched pars than for a white strobe).*

---

**9. Proceed on the ICD's provisional connector coordinates, or wait for the carrier's P6?**

ICD section 7.2's connector positions - J3 at (14, 68), J4 at (56, 68), H5 at (46, 74) - are
explicitly **provisional until the end of the carrier's P6**, and the ICD says daughters are
blocked on them. Everything else in the ICD is frozen.

*Default: proceed on the provisional coordinates, and re-check them against the re-issued ICD
before this board's own P6 completes. If they have moved, the fix is a `place_edit`, not a
respin. Waiting for the carrier's P6 serialises the two runs for no design benefit.*

---

## Traceability

Requirement IDs referenced and where they land in this document:

| ID | Section |
|---|---|
| SYS-REQ-01..08 | 1, 3.4 (behavioural spec, inherited via STR-REQ-01..05) |
| STR-REQ-01..05 | 1, 3.4, 4 |
| STR-REQ-06, 07 | 2.4, 3.4 |
| STR-REQ-08, 09, 10 | 3.2, 8.3 |
| STR-REQ-11 | 1 (`ASSUMED:` acceptance number is < 1 ms optical rise/fall per Project Plan v1.0; the brief leaves it to be defined during design) |
| STR-REQ-12 | 2.5, 8.2 |
| STR-REQ-13..16 | 4, 8.2, open questions 3 and 4 |
| STR-REQ-17..22 | 2.3, 2.4 |
| CAR-REQ-07, 08, 10..17 | 2.3, 2.4, 3.2, 5 |
| D-01, D-02, D-03 | 3.1, 3.2, 6 (all CLOSED) |
| D-04 | open question 1 (OPEN, owned by this board) |
| MECH-01, MECH-02 | 5 |
| ICD-01 | 2, 5 (hard input, never redefined) |
| DOC-01 | design document is a required deliverable at the end of this run |
| GIT-01 | scoped commits only - never `gate.py --commit`, never `git add -A` |

---

# 10. H1 amendments - BINDING, supersede everything above

**Authority:** project owner, H1 checkpoint verdict, 2026-07-28. Recorded in `state.json`
(`human --checkpoint 1 --status approved`). These entries supersede the corresponding text
earlier in this document and in `brief/02-strobe-daughter-brief.md`.

## 10.1 D-04 CLOSED - RGBW, four colour channels

Open question 1 is closed as **RGBW**. This is **against this run's recommendation** of
white-only, and was chosen knowingly with the full costed delta in front of the owner
(+$4-6 board BOM, +$40-80 LED module, all 8 PWM channels consumed against a baseline of 3,
and **no additional light** - RGBW divides the same ~6.6 W of sustained output into colours
rather than adding to it). **Not to be re-litigated.**

Consequences this run now owns:
- Four drive stages, not one. Per-colour sense moves to I2C - the 2-ADC budget does not
  stretch to four colours.
- **Per-colour output is roughly a quarter of the white figure.** The 10,000 lm headline
  from the white-only baseline must not be carried forward; light numbers are re-derived
  per channel in `architecture/power_tree.md`.
- All 8 PWM channels are consumed across 4 LEDC timers (CAR-REQ-11). The flash gate is a
  5-200 ms one-shot, **not** a 9.766 kHz duty setting, and the white-only baseline could
  only treat that as free because it owned LEDC timer 0 exclusively. **That assumption no
  longer holds and the timer allocation is re-checked and reported at H2.**

## 10.2 STR-REQ-01 AMENDED - dual-mode flash

> **Original text (superseded):** "STR-REQ-01 | Full-output flash, 100-200 ms, with
> **instant** blackout either side. No visible decay tail, no fade-in ramp. | P1 rage trap:
> the visual gap between maximum and zero is the entire effect."

**Why it was amended, not met:** 0.99 J of usable bank energy over 150 ms is ~15 W of drive,
not the ~99 W the brief's "100 W strobe" implies. Reaching ~99 W for 150 ms needs 13.8 J,
i.e. **32,500-65,000 uF**. Measured against this board: 12,000 uF alone is 5,104 mm2
(**64 % of a 100 x 80 mm board**) and 37 mm tall, and even that holds full output for only
36.9 ms. This is a consequence of the closed 8.5 W (af) budget and D-02's closed bank
sizing - **physics, not a tooling limit or an oversight.**

**STR-REQ-01 (amended): the fixture provides two flash modes.**

| Mode | Duration | LED drive power | String current | Notes |
|---|---|---|---|---|
| **Headline / blast** | **8.68 ms** | **98.8 W** (white-only figure; ~1/4 per colour) | 2.6 A | 0.858 J to the LED, 0.990 J from the bank. This is "full output" |
| **Long, mode 1** | 50 ms | 28.1 W | 0.74 A | bank + rail during the flash |
| **Long, mode 2** | 100 ms | 18.2 W | 0.48 A | |
| **Long, mode 3** | 150 ms | 14.9 W | 0.39 A | |
| **Long, mode 4** | 200 ms | 13.3 W | 0.35 A | max ~2.9 Hz repetition at 58 % duty |

**Unchanged and still binding:** instant blackout either side, no visible decay tail, no
fade-in ramp, and STR-REQ-11's <1 ms optical rise/fall. The amendment changes only the
*amplitude available at long durations*, never the edge quality.

## 10.3 802.3at - this board is af-ONLY

**BLOCKING-03 accepted.** LUM-DTR-STROBE-A is designed, built and documented for
**802.3af only**. **No board area and no cost is spent preserving an at path.**

An at build puts 4.67 W across two linear pass elements in sealed-box air; the best case is
1.91 W per D2PAK against a 1.40 W allowance - **it fails by 1.5x**. Capping the governor to
keep it inside thermals yields ~12.1 W of the 18.5 W available = **+45 % light, not the
+120 % D-01 implies**. A real at build for this daughter needs an off-board or heatsinked
pass element, i.e. a respin.

**D-01's hedge ("resistor change plus a PoE+ switch, no board respin") continues to hold for
the carrier and for the par. It does not hold for this daughter.** This is a disclosure to
the carrier owner, not an ICD change request - nothing this board needs from the carrier
moves.

## 10.4 Light engine - SPECIFY, do not design

The RGBW LED module is **not designed by this run**. This run produces a specification
complete enough that someone else can build the MCPCB: emitter selection, string topology,
thermal path, and the board-to-module connector, written as explicit numbered acceptance
criteria (`LE-xx`) in `architecture/light-engine-spec.md`. **That spec now covers four
colour channels, not one.**

## 10.5 BLOCKING-01 (RJ45 notch) - owned by the coordinator, not this run

`board_init.py` is gaining a `--cutout` flag centrally, because both daughters need the
30 x 26 mm notch. **This run must NOT implement a workaround, must NOT shrink the outline,
and must NOT hand-edit Edge.Cuts.** The notch region (6,0)-(36,26) stays a hard keepout in
`architecture/constraints.json` regardless, so the board is electrically correct either way.
The flag is assumed present by P5 and will be confirmed before this run reaches it.

## 10.6 CARRY - ICD s7.6 internal-air figures are PROVISIONAL

The par run raised a blocking issue against ICD s7.6: the internal-air figures are not
self-consistent (69 C at cannot coexist with 56 C af), and an independent calculation gives
**89-115 C**, i.e. the ICD is optimistic by **20-46 K**.

**This board's entire thermal case is built on 56 C (af) internal air.** Treat s7.6 as
provisional until the carrier re-issues it. **How every margin moves at 85-90 C air rather
than 69 C must be derived and reported at H2.**
