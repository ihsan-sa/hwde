# ICD-01 - LUMINA expansion connector interface control document

**Owner:** LUM-CAR-A (carrier board). **Status: frozen at H1. Rev A3** (A2 = 0.635 mm creepage + bank-charging contract; A3 = ID_ADC codes + PWM/timer contract; A4 = sealed-with-wall-conduction thermal budget + firmware requirements; A5 = thermal assumptions stated + at-ventilation closed; A6 = FAULT sink current + IMON accuracy caveat; A7 = s7.2 connector coordinates FROZEN at P6, s7.4 mech-3 corrected).
**Consumers:** LUM-STR-A (strobe daughter), LUM-PAR-A (RGBW par daughter), and every future LUMINA
daughter.

> **This document is a hard input to every daughter board.** A daughter that needs something
> different does **not** implement a variant. It raises a **blocking issue against LUM-CAR-A**, the
> carrier owner re-issues this ICD with a new revision, and every affected daughter re-baselines.
> Silent divergence here produces boards that mate mechanically and destroy each other electrically.

Everything in this document is derived in `blocks.md`, `power_tree.md` and `stackup.md`; where a
number appears in more than one place, this document is the one that governs.

---

## 1. Scheme: two connectors, not one

| | Carrier side (male header) | Daughter side (socket) |
|---|---|---|
| **POWER block** | **CONNFLY DS1021-2x7SF11-B** - 14 pos, 2.54 mm, 250 V, 3 A/contact, THT | **CONNFLY DS1023-2*7SF11** - 14 pos, 600 V, 3 A/contact, 8.5 mm body |
| **SIGNAL block** | **CONNFLY DS1021-2x12SF11-B** - 24 pos, 2.54 mm, 250 V, 3 A/contact, THT | **CONNFLY DS1023-2*12SF11** - 24 pos, 600 V, 3 A/contact, 8.5 mm body |

**38 positions total.** Carrier BOM cost $0.22/board at qty 50. Contacts are gold over copper alloy,
rated -40 to +105 C.

Both blocks are **JLC Extended** parts. A `--basic-only` search over the entire connector keyword
space returns **zero** rows: there is no JLC Basic part in any board-to-board family, so "prefer
Basic" is unachievable here and is not a selection error.

### 1.1 Why 2.54 mm and not a mezzanine connector

**Rated working voltage kills the fine-pitch families.** The requirement is >= 57 V (the PSE
maximum), preferably >= 100 V so the TVS clamp region is covered:

| Family | Pitch | Rated voltage | Verdict |
|---|---|---|---|
| Panasonic AXK | 0.5 / 0.4 mm | **60 V** | reject - 3 V above the worst case, no derating headroom |
| Hirose FX10 | 0.5 mm | **50 V** | reject |
| Hirose BM22 | - | **50 V** | reject |
| Molex 55560 / 505473 | 0.5 / 0.4 mm | **50 V** | reject |
| TE 3-1827253 | 0.5 mm | **50 V** | reject |
| HCTL SHD | 1.0 mm | **50 V** | reject |
| Samtec QTH/QSH | 0.5 mm | 175 V | passes voltage - **rejected on cost**: $15.30 per mated pair, over half the $30/board target |
| **CONNFLY DS1021/DS1023** | **2.54 mm** | **250 V (male) / 600 V (socket)** | **selected - 4.4x the 57 V worst case** |

Two further reasons the 2.54 mm answer is the right one rather than merely the available one:
- **Second sourcing.** This is a commodity footprint with at least four independent stocked vendors
  on the *same* land pattern (CONNFLY DS1021/DS1023, HanElectricity 2541WV/2541FV, Boomele
  2.54-2*nnP, HCTL HC-PZ254/HC-PM254). A mezzanine family's footprint is proprietary, so a stockout
  is a respin.
- **Land-pattern creepage.** See s5: 2.54 mm gives 0.84 mm of pad-to-pad copper gap against a
  0.635 mm requirement. 1.27 mm gives 0.47 mm and **fails**.

### 1.2 Why split and not one 2x20

Both schemes are electrically fine. The split wins on failure modes:

1. **Keying is free and mechanical** (s7).
2. **A one-position mis-seat is contained.** Offset a single 2x20 by one position and **48 V lands
   on an ESP32-S3 GPIO**. With the split, 48 V can only ever land on another *power* pin, and every
   such case is a fault the carrier's current limits already have to survive (s6.2).
3. **48 V is physically 24 mm away from logic**, so CAR-REQ-17 is solved by tens of millimetres of
   separation rather than by 1.9 mm of pin gap, and the 48 V group gets its own clearance zone
   without disturbing the signal fan-out.
4. Cost of the split: one extra part and one extra footprint. Alignment is a non-issue - 2.54 mm THT
   has ~0.3 mm of positional slack and a 6 mm lead-in.

**Position counts are not free parameters.** `2x17 male does not exist` in this family, `2x16` has
11 pcs in stock, `2x8` sockets have 47 pcs. The stocked counts are 2x7 (5575/3922), 2x12
(3652/2313), 2x15, 2x20 and 2x22. **Both selected counts are deeply stocked**, and the pin map below
was designed to land exactly on them.

---

## 2. Signal budget

| Signal | Pins | Block |
|---|---|---|
| `+48V_SW` (switched PD rail) | 3 | power |
| `+12V` | 2 | power |
| `+3V3` | 2 | power |
| `GND` (power returns) | 7 | power |
| `PWM0..7` | 8 | signal |
| `DSPI_SCK / MOSI / MISO / CSn` | 4 | signal |
| `I2C_SCL / SDA` | 2 | signal |
| `ADC0 / ADC1` | 2 | signal |
| `ID_ADC` | 1 | signal |
| `ENABLE` | 1 | signal |
| `FAULT` | daughter -> carrier | open-drain, **active low** | Pulled up on the CARRIER (10 k to +3V3). **A daughter asserting FAULT must sink >= 5 mA** - REVISED at rev A6. The carrier's own red fault indicator (D22 + its ballast) also hangs on this net, so the real load is ~4.3 mA, not the ~0.33 mA implied by the pull-up alone. Any ordinary open-drain FET or MCU pin meets this; the number is published so no daughter sizes a marginal device. Well inside the carrier eFuse's 10 mA FLT limit. |
| `GND` (signal returns) | 5 | signal |
| **Total** | **38** | |

Satisfies requirements s2.1 (">= 3 pins total across the power rails" - 7 here; ">= 4 GND" - 12
here) and CAR-REQ-13 (s4).

**`ID` is one pin, not two.** Q10's default keeps *both* an ID mechanism on an ADC divider *and* an
I2C EEPROM - but the EEPROM rides the shared I2C bus, so a second dedicated ID pin buys nothing. The
freed position became a fifth signal-block GND.

---

## 3. Pin assignment - COMPLETE, both blocks

Numbering is the standard dual-row convention: odd positions in row A, even in row B, with
position `n` and `n+1` directly across from each other on a 2.54 mm grid in both directions.
Position 1 is silkscreen-marked with a triangle on **both** boards.

### 3.1 POWER block - J3, 2x7, 14 positions

| Col | Row A | net | Row B | net |
|---|---|---|---|---|
| 1 | **1** | `+48V_SW` | **2** | `GND` |
| 2 | **3** | `+48V_SW` | **4** | `GND` |
| 3 | **5** | `+48V_SW` | **6** | `GND` |
| 4 | **7** | `GND` *(guard column)* | **8** | `GND` |
| 5 | **9** | `+12V` | **10** | `GND` |
| 6 | **11** | `+12V` | **12** | `+3V3` |
| 7 | **13** | `GND` | **14** | `+3V3` |

Properties this map is built to have, each of which is checkable by eye:
- The 48 V group is at **one end** and is **bounded by GND on every side**: positions 2/4/6
  (across-row), 7 (along-row), and there is no fourth side.
- **Column 4 is an all-GND guard column** between the 48 V group and the 12 V group.
- **Every supply pin has an adjacent GND.**
- **Rail order along the connector is 48 -> 12 -> 3.3**, matching D-02's conversion chain, so
  adjacent pins are never more than one rail step apart.
- **No single-position mis-seat can put a higher rail on a lower rail's pin** (proof in s6.2).

### 3.2 SIGNAL block - J4, 2x12, 24 positions

| Col | Row A | net | Row B | net |
|---|---|---|---|---|
| 1 | **1** | `PWM0` | **2** | `PWM1` |
| 2 | **3** | `GND` | **4** | `GND` |
| 3 | **5** | `PWM2` | **6** | `PWM3` |
| 4 | **7** | `PWM4` | **8** | `PWM5` |
| 5 | **9** | `GND` | **10** | `GND` |
| 6 | **11** | `PWM6` | **12** | `PWM7` |
| 7 | **13** | `GND` | **14** | `DSPI_SCK` |
| 8 | **15** | `DSPI_MOSI` | **16** | `DSPI_MISO` |
| 9 | **17** | `DSPI_CSn` | **18** | `I2C_SCL` |
| 10 | **19** | `I2C_SDA` | **20** | `ADC0` |
| 11 | **21** | `ADC1` | **22** | `ID_ADC` |
| 12 | **23** | `ENABLE` | **24** | `FAULT` |

- **Every PWM pin has a GND within one position** - the returns for the fastest edges on the
  connector.
- `DSPI_SCK` (14) has a **direct across-row GND** (13). The daughter SPI bus is capped near 26 MHz
  (ESP32-S3 GPIO matrix), which is ample for an EEPROM or an LED driver.
- `ENABLE` and `FAULT` are at the **far end from the PWM group**, so a mis-seat pushes `ENABLE` off
  the connector rather than onto a driver line - and losing it de-asserts (s8.2).
- **No 48 V exists anywhere on this connector.**

### 3.3 Signal electrical definitions

| Signal | Direction | Type | Levels / rules |
|---|---|---|---|
| `PWM0..7` | carrier -> daughter | push-pull CMOS | 3.3 V, LEDC channels 0-7, low-speed mode only. **The carrier no longer hard-assigns timers** - see s3.5. Default profile is 13-bit at 9.766 kHz; 14-bit at 4.883 kHz is also offered. **Channels sharing a timer share frequency AND resolution** (CAR-REQ-11) |
| `DSPI_*` | bidirectional | SPI mode 0, MSB first | **<= 26 MHz.** Daughter drives no line except MISO, and only while `DSPI_CSn` is low. Shared bus, one CS - a daughter needing more devices decodes locally |
| `I2C_SCL/SDA` | bidirectional | open drain | **Pull-ups are on the carrier** (4.7 k to +3V3). **Daughters must not fit their own.** 400 kHz. Reserved address space is the daughter's, except that the carrier reserves nothing |
| `ADC0`, `ADC1` | daughter -> carrier | analogue, 0 - 3.3 V | ESP32-S3 ADC1 inputs, series-protected and clamped on the carrier. Source impedance **<= 10 kohm** |
| `ID_ADC` | daughter -> carrier | analogue, 0 - 3.3 V | The carrier fits the **top** leg of a divider (10 k to +3V3). The daughter fits the **bottom** leg to GND. Board-type codes are allocated by the carrier owner, not chosen by daughters |
| `ENABLE` | carrier -> daughter | push-pull CMOS, **active HIGH** | See s8. **The daughter must fit its own 100 kohm pull-down** and gate every output stage with it |
| `FAULT` | daughter -> carrier | **open drain, active low** | 10 k pull-up on the carrier. Shared, wire-OR'd with the carrier's own 48 V eFuse fault output. A daughter must **never** drive this high |

---

### 3.4 `ID_ADC` - daughter board type codes (CAR-REQ-07). NORMATIVE.

Added at rev A3 in response to CR-1. **The carrier owns this code space; daughters must use an
allocated code and must not invent one.**

**Circuit.** The carrier fits the **top** leg: **10 kOhm 1% from `ID_ADC` to +3V3**, plus the 1 kOhm
series protection resistor to the MCU ADC pin (no DC current flows in it, so it adds no divider
error). The **daughter fits the bottom leg**, `R_ID` from `ID_ADC` to `GND`.

`V_ID = 3.3 V x R_ID / (R_ID + 10k)`

| Code | `R_ID` (daughter, 1%) | Nominal `V_ID` | Board |
|---|---|---|---|
| **FAULT** | short to GND | < 0.15 V | Shorted connector or mis-seated daughter - firmware must NOT assert ENABLE |
| **1** | **2.7 kOhm** | 0.702 V | **LUM-STR-A** (strobe) |
| **2** | **4.7 kOhm** | 1.055 V | **LUM-PAR-A** (RGBW par) |
| **3** | 7.5 kOhm | 1.414 V | reserved |
| **4** | 12 kOhm | 1.800 V | reserved |
| **5** | 18 kOhm | 2.121 V | reserved |
| **6** | 30 kOhm | 2.475 V | reserved |
| **NONE** | open (no daughter) | > 2.9 V | No daughter fitted - firmware must NOT assert ENABLE |

**Why these values.** Minimum adjacent-code separation is **0.353 V** (code 1 to code 2), against a
worst-case divider error of about +/-0.05 V from 1 % resistors. A **+/-0.15 V** detection window per
code is therefore safe and is what carrier firmware shall use. The top code stops at 2.475 V because
the ESP32-S3 ADC saturates near 3.1 V at 12 dB attenuation, so a higher code could not be
distinguished from "open".

**Firmware contract.** The code selects the daughter profile that configures the LEDC timers (s3.5).
FAULT and NONE both mean **ENABLE stays de-asserted**.

### 3.5 PWM channel and timer allocation (CAR-REQ-11). NORMATIVE.

Revised at rev A3. **The previous statement that PWM0-3 sit on LEDC timer 0 and PWM4-7 on timer 1 is
withdrawn** - it was wrong for the strobe and would have mis-specified two boards.

**Hardware ceiling (ESP32-S3 LEDC, not negotiable):** 8 channels, **4 timers**, low-speed mode only,
**14-bit maximum** duty resolution. Channels sharing a timer share **both** frequency and resolution.
At a timer's maximum resolution the duty value must clamp to `2^n - 1`.

| Mode | Resolution | Frequency | Levels |
|---|---|---|---|
| **Default** | 13-bit | **9.766 kHz** | 8192 |
| **Optional (CR-3, granted)** | 14-bit | **4.883 kHz** | 16384 |

The 14-bit mode is offered because it doubles low-end resolution; it costs camera-flicker margin, so
it is opt-in per daughter and must be re-tested against a phone camera on the first prototype.

**The carrier does not hard-assign timers.** Each daughter declares its own channel -> timer ->
frequency map in its design document; carrier firmware applies that map from the `ID_ADC` code.

| Board | Channels | Timer map |
|---|---|---|
| **LUM-PAR-A** | PWM0-3 (RGBW) | all four on **one** timer, 13-bit / 9.766 kHz. Three timers remain free. **90 degree phase stagger** across the four channels - see below |
| **LUM-STR-A** | PWM0-7 (RGBW strobe) | colour dimming on one timer at the default rate; **the flash gate is NOT a duty setting** - see below |
| No daughter / unknown code | - | all channels held low, ENABLE de-asserted |

**Strobe flash gating - correcting an ICD default.** A 5-200 ms flash cannot be expressed as a duty
value at 9.766 kHz, because one LEDC period is **102.4 us** and a 5 ms flash is only ~49 periods. The
strobe therefore either drives its flash line as a **GPIO / RMT one-shot**, or **re-programs the timer
it owns** to the flash rate. Both are legal on this connector - these pins are ordinary GPIOs and
nothing on the carrier forces them into LEDC. **It is therefore NOT true that all 8 channels sit at
the default frequency.**

**CR-4 granted - 90 degree phase stagger.** LEDC supports a per-channel phase offset (`hpoint`), so
staggering four channels by 90 degrees costs nothing in hardware and avoids a 4x larger input-current
step when all four switch together. Carrier firmware shall apply it for any daughter running four or
more channels on one timer. Firmware default, not a connector change.

---

## 4. Current rating per pin, and the CAR-REQ-13 margin proof

### 4.1 Derating arithmetic - show your work

Manufacturer rating: **3.0 A per contact.** That figure is the usual *single-circuit-energised*
number. For a fully populated two-row connector with every contact carrying current, an adjacent-pin
derate applies. Two conventional factors:

```
  conservative   3.0 A x 0.60 = 1.80 A per pin      <- USED THROUGHOUT THIS ICD
  optimistic     3.0 A x 0.70 = 2.10 A per pin
```

**1.80 A/pin is the number every table below uses.**

### 4.2 Per-rail capacity vs CAR-REQ-13 (>= 50 % margin over worst-case daughter draw)

Worst case is Q6's provisional default: 48 V raw 2 A continuous with **3 A capability**, 12 V 2 A,
3.3 V 0.5 A. Per the assignment wording, the 50 % margin is taken against the **3 A capability**
figure, not the 2 A continuous figure.

| Rail | Q6 worst case | x1.5 (CAR-REQ-13) | Pins needed @1.80 A | **Pins allocated** | Capacity | **Margin over worst case** |
|---|---|---|---|---|---|---|
| `+48V_SW` | 3.0 A | 4.50 A | 2.50 -> 3 | **3** | **5.40 A** | **+80 %** |
| `+12V` | 2.0 A | 3.00 A | 1.67 -> 2 | **2** | **3.60 A** | **+80 %** |
| `+3V3` | 0.5 A | 0.75 A | 0.42 -> 1 | **2** | **3.60 A** | **+620 %** |
| `GND` (all three at worst case simultaneously) | **5.5 A** | **8.25 A** | 4.58 -> 5 | **7** (power block) **+ 5** (signal block) | **12.60 A** (power block alone) | **+129 %** |

**GND is the binding rail, not 48 V.** The brief's ">= 4 GND" is *below* what CAR-REQ-13 requires
once all three rails are at worst case at once; 5 is the minimum and 7 in the power block is what is
allocated, plus 5 more in the signal block for signal returns.

Every rail clears CAR-REQ-13's 50 % bar, and the tightest is 80 %.

**Sensitivity:** every additional 1.8 A of 48 V requirement costs exactly one more pin, and a 2x7
has no spare - a Q6 answer above 3 A pushes the power block to 2x8 or 2x9, where socket stock is
47 pcs and 4609 pcs respectively. **Get Q6 answered before H1**, because after H1 two daughters are
blocked on this document.

---

## 5. The 48 V creepage and clearance scheme

### 5.1 The number and its source

**0.635 mm minimum copper-to-copper spacing on outer layers, board-wide, around every 48 V net.**

> **REVISED at P3, rev A2 (2026-07-28).** The original figure was 0.60 mm from IPC-2221B alone.
> The TPS2378 datasheet's own layout section recommends **0.025 in = 0.635 mm** between VSS and
> high-voltage signals such as VDD. Rather than waive a vendor recommendation on the board's most
> safety-critical IC, the LARGER number is adopted board-wide. The delta is 0.035 mm and costs no
> routing area - the binding connector geometry still clears it at 1.32x. Daughters inherit 0.635 mm.

| Item | Value | Source |
|---|---|---|
| Worst-case voltage on the board | **57 V DC** | IEEE 802.3 PSE maximum output |
| IPC-2221B Table 6-1, column **B2** (external conductors, uncoated, sea level to 3050 m), 51-100 V band | 0.60 mm - **the FLOOR, not the requirement** | IPC-2221B. This is the table `check_creepage.py` transcribes. Superseded board-wide by the 0.635 mm vendor figure below |
| IPC-2221B column B1 (internal conductors), 51-100 V | 0.10 mm | below JLC's 0.127 mm minimum, so the fab minimum dominates on In1/In2 and the HV requirement is free there |
| **BINDING board-wide requirement** | **0.635 mm** (0.025 in) between VSS and high-voltage signals such as VDD | TPS2378 datasheet layout section. Exceeds IPC and is therefore the governing number. `check_creepage.py` demands only 0.60 mm, so a 0.635 mm layout passes the checker by construction; the 0.635 mm figure is enforced by the hand-written `.kicad_dru` rule at P5 (TRAP-1) |
| Insulation class | **functional only** | 57 V DC is below the IEC 62368-1 **ES1** limit of 60 V DC, so no basic/supplementary/reinforced safeguard is required. IPC-2221 does not separate creepage from clearance; 0.635 mm covers both |

**The 0.13 mm "permanent polymer coating" column (B4) is NOT claimed.** Standard LPI soldermask is
not a qualified conformal coating, and `check_creepage.py` implements only the uncoated columns -
a layout designed to 0.13 mm fails P8 with no waiver mechanism.

### 5.2 How the pin map physically realises it

The binding geometry is the **PCB land pattern**, not the connector body - `check_creepage` measures
copper, not air.

| Geometry | Value | vs 0.635 mm |
|---|---|---|
| Pitch, both directions | 2.540 mm | - |
| Pin-to-pin air gap (0.64 mm square pin across flats) | 1.90 mm | 3.0x |
| **PCB pad-to-pad copper gap, 1.70 mm annulus on a 1.10 mm drill** | **0.84 mm** | **1.32x - this is the binding number** |
| PCB pad-to-pad gap, 1.60 mm annulus | 0.94 mm | 1.48x |
| Connector rated working voltage (pair bound by the lower of male 250 V / socket 600 V) | **250 V** | 4.4x the 57 V worst case |

For contrast: at **1.27 mm pitch** the pad gap is 0.47-0.65 mm and **fails or has zero margin**.
Anything at or below 1.00 mm pitch is out. That, plus the 50-60 V ratings of s1.1, is why the
fine-pitch route is closed.

**P3 library note (rev A2):** the pulled DS1021 footprints use a **1.10 mm** drill, not the
1.02 mm assumed when this table was first written. Pad-to-pad gap is `pitch - annulus` and is
therefore unaffected - 0.84 mm and 1.32x both stand. The 2x7 power header J3 was pulled with a
1.80 mm annulus (0.74 mm gap, 1.165x) and has been **normalised to 1.70 mm to match J4**, so both
frozen connectors now share one land pattern. Annular ring is 0.300 mm/side, above JLC's PTH
minimum. Daughters must use the 1.70 mm annulus.

**Annular ring is a layout lever, not a free choice**: if P6/P7 needs more margin, shrink the
annulus on the 48 V pads to 1.60 mm before moving anything else.

### 5.3 The guard scheme, in order of strength

1. **The signal field is on a physically separate connector, ~24 mm away.** This is the primary
   guard and it is worth more than any pin-level measure. The research recommendation of "at least
   one GND pin plus, budget permitting, one empty position between the 48 V group and the first
   logic pin" is satisfied by ~9.5 empty positions' worth of board.
2. **GND on every side of every 48 V pin** (positions 2, 4, 6 across-row; position 7 along-row).
   A solder bridge, conductive debris or flux tracking from a 48 V pin then produces a
   **48 V-to-GND short**, which is exactly the fault the carrier's current-limited high-side switch
   is already required to survive under CAR-REQ-14. It converts an unbounded fault into a bounded
   one.
3. **An all-GND guard column** (column 4) between the 48 V group and the 12 V group.
4. **Rail order 48 -> GND -> 12 -> 3.3** along the connector.

### 5.4 Requirements this places on the daughter's own layout

- **0.635 mm outer-layer clearance around every 48 V net on the daughter too**, board-wide, from the
  connector pads to the cap bank. This is not inherited automatically - the daughter's DRC must be
  set up for it.
- **Any resistor sitting across the 48 V domain must be 0805 or larger** (0402/0603 parts are
  typically 50-75 V working) or split into two in series. This bites the mandatory bleed resistor
  and any 48 V rail-sense divider.
- **Capacitors on the 48 V domain must be 100 V rated** (63 V is not enough at a 57 V worst case
  once ceramic DC bias derating is applied).
- The clearance applies **through the board too**: a signal on an inner layer or the opposite face
  passing under a 48 V pin's antipad needs the same 0.10 mm inner / 0.635 mm outer.

---

## 6. Rail limits - sustained, peak, and fault

### 6.1 The three different numbers, and why all three are real

The provisional Q6 default reads "48 V raw 2 A continuous with 3 A capability". **2 A at 48 V is
96 W on a 12.95 W (af) / 25.5 W (at) supply.** It is not a rail specification. It is a *connector
pin* specification, and it is a good one - cheap, thermally generous, and it clears CAR-REQ-13.

The arithmetic that separates the three numbers:

```
  what the PoE SOURCE can ever deliver, at the PD input:
      802.3af : 0.350 A DC, 0.400 A peak      (12.95 W at 37 V)
      802.3at : 0.600 A DC, 0.686 A peak      (25.50 W at 42.5 V)
  anything above that comes from local capacitance, and the carrier deliberately
  holds only 44 uF of it (bounded by the ~180 uF 802.3 port-capacitance ceiling).

  what the CARRIER HARDWARE permits on +48V_SW:
      eFuse ILIM = 1.0 A, MODE = latch off
      (PD interface's own hot-swap: 0.85 A continuous, ~1.0 A limit, foldback to
       140 mA if V(RTN-VSS) exceeds ~12.3 V for 800 us)

  what the CONNECTOR PINS carry:
      3 pins x 1.80 A derated = 5.40 A
```

### 6.2 The table daughter designers must design against

| Rail | **Sustained (af)** | **Sustained (at)** | **Peak, ms-scale, from local bulk** | Hardware fault ceiling | Connector pin capacity |
|---|---|---|---|---|---|
| `+48V_SW` | **0.25 A** | **0.50 A** | 1.0 A (the eFuse limit, until it latches) | 1.0 A, **latch off** | 5.40 A |
| `+12V` | **0.75 A** | **1.25 A** | 2.0 A | 2.0 A converter rating, OCP | 3.60 A |
| `+3V3` | **0.25 A** | **0.25 A** | 0.50 A | 1.0 A converter, limit >= 1.3 A | 3.60 A |
| **TOTAL across all three rails** | **8.5 W** | **18.5 W** | - | PSE overload timer, ~50-75 ms | - |

**The per-rail ceilings do not add up to the total and are not meant to.** 0.25 A x 48 V +
0.75 A x 12 V + 0.25 A x 3.3 V = 21.6 W against an 8.5 W af envelope. They are individual ceilings;
**the total is what binds**, and it is enforced by firmware's average-energy governor - now
closed-loop, because the carrier's eFuse has an analogue current-monitor output wired to an MCU ADC.

Two consequences daughter designers get wrong if this is not spelled out:
- **A cap bank sized against "2 A of continuous 48 V" is sized against current that cannot arrive.**
- **A burst is not free.** 1 J dumped in 10 ms is 100 W for 10 ms, but repeating at 12 Hz still draws
  12 W continuously. Any cap-bank daughter needs its own average-energy governor cooperating with
  the carrier's.

#### 6.2.1 IMON accuracy - REVISED at rev A6. Read before relying on the governor.

The carrier's eFuse provides an analogue current-monitor output (`IMON`) to an MCU ADC, and s6.2
describes the average-energy governor as closed-loop on the strength of it. **That claim is now
qualified.**

The TPS16630 specifies `GAIN(IMON)` accuracy only for **I(OUT) >= 0.6 A** (25.66-30.14 uA/A over
0.6-2 A, and a second band 2-6 A). The rail's published sustained limits are **0.25 A (af) / 0.50 A
(at)** - **both below that floor**. So at the current the governor actually regulates against, the
transfer function has **no datasheet-guaranteed accuracy**.

What this does and does not mean:

- The measurement is still **monotonic and useful** - it is a real current monitor, not noise. It is
  fine for detecting gross overdraw, a stuck-on daughter, or a shorted rail.
- It is **not** a calibrated energy meter at 0.25-0.5 A. **Do not design a daughter that depends on
  the carrier metering its average power to better than roughly +/-20 % in that range** unless one of
  the following is done:
  1. **per-unit characterisation at build** (measure and store a correction in the daughter's
     I2C EEPROM - the ID scheme already provides somewhere to put it), or
  2. move the governor to a **shunt + amplifier** on a future carrier revision, or
  3. keep the governor conservative and treat IMON as a guard rather than a meter.

`R(IMON)` = 30 k is TI's own 1 A worked example and is otherwise correct; the issue is the operating
point, not the component.

### 6.3 Where the cheap watts are

**Take power on `+48V_SW`, not `+12V`, wherever the daughter can.** It skips the 48 V -> 12 V
conversion entirely and is worth **0.67 W (af) / 1.30 W (at)** of extra delivered power - and it
removes the carrier's only real hot spot. The `+12V` at-ceiling of 1.25 A exists *because* of that
converter's thermal budget: above 1.25 A the 48->12 stage exceeds its `check_thermal` allowance in a
sealed enclosure. **Anything above 1.25 A at the at operating point must be taken on `+48V_SW`.**

### 6.4 Strobe cap-bank arithmetic, for LUM-STR-A

2800 uF over the 48 -> 40 V window stores **0.99 J**; a full 0 -> 48 V charge is **3.23 J**.

| | af | at |
|---|---|---|
| Max full-window (48 -> 40 V) flash rate the rail can sustain | 8.6 Hz | 18.8 Hz |
| Energy per flash at SYS-REQ-03's 25 Hz ceiling | 0.34 J | 0.74 J |
| Bank droop per flash at 25 Hz | 48 -> 45.4 V | 48 -> 42.1 V |
| **Cold-start charge time at the ICD sustained limit** | **0.54 s** | **0.27 s** |

SYS-REQ-03's 1-25 Hz range is reachable on af, at reduced per-flash energy above ~8.6 Hz.

### 6.5 Mis-seat behaviour of the power block (the design property, proved)

Shifting the power block by one full position (one column) in either direction produces, per pin,
either a same-net connection or a short between two rails:

| Shift | Worst case produced | Who handles it |
|---|---|---|
| right +1 col | 48 V -> GND; GND -> 12 V; GND -> 3.3 V; 12 V -> GND | eFuse latch-off / 12 V OCP / 3.3 V current limit |
| left -1 col | GND -> 48 V; 12 V -> GND; 3.3 V -> GND | same |

**No case puts a higher rail onto a lower rail's pin, and no case puts 48 V anywhere near logic.**
Every outcome is a short-to-a-different-rail that a current limit already has to survive. That is
the design property the pin ordering in s3.1 exists to produce, and it is why the rails are ordered
48 -> GND -> 12 -> 3.3 rather than by convenience.

Row-swapping (row A meeting row B) is not a reachable failure mode: it would require the daughter to
be inverted about the connector's long axis, which a board-to-board mating cannot do.

---

### 6.6 Bank-charging contract - BINDING on every daughter that taps +48V_SW

Added at P3 (rev A2) after datasheet extraction of the carrier's load switch. **The strobe run must
design its soft-start to these numbers.**

| Parameter | Value |
|---|---|
| Carrier switch | TPS16630 eFuse, HTSSOP-20 |
| Carrier current limit | **1.0 A** (R(ILIM) = 18 kOhm, per R = 18/I(OL)) |
| Carrier fault response | **MODE open = LATCH-OFF after 162 ms of continuous current limiting.** Recovery needs an ENABLE (SHDN) toggle or a PD power cycle |
| Carrier thermal backstop | thermal regulation at TJ 145 C, 1.25 s timeout |
| **Daughter charge-current ceiling** | **<= 0.25 A (af build) / <= 0.5 A (at build)** - identical to the sustained rail rating in s6.2 |
| Daughter absolute ceiling | never exceed 1.0 A; never sit above 1.0 A for > 162 ms |

**The daughter's soft-start must be CURRENT-limited, not merely slew-limited.**

Why this is binding, with the arithmetic:

- The carrier eFuse is a **fault protector, not a charging regulator**. If a daughter presents its
  raw bank, the eFuse limits at 1.0 A and charging 2800 uF across 48 V takes
  `t = C x V / I = 2800e-6 x 48 / 1.0 =` **134 ms** against the **162 ms** latch-off timer. That is
  17 % margin before any thermal derating - not a design margin, a coincidence.
- **Energy is invariant.** Charging 2800 uF to 48 V dissipates `C x V^2 / 2 =` **3.2 J** in whichever
  element limits the current. That heat must land in the **daughter's** inrush limiter, not in the
  carrier's HTSSOP-20. This is the physical reason CAR-REQ-14 puts inrush limiting on the daughter -
  it is not an arbitrary division of labour.
- At <= 0.25 A the bank charges in ~538 ms; at <= 0.5 A, ~269 ms. **Both keep the carrier eFuse out
  of current limit entirely**, so the 162 ms timer never starts and the thermal loop never engages.

---

## 7. Mechanical and mating scheme

### 7.1 The common LUMINA footprint - every board inherits this

| Item | Value |
|---|---|
| **Board outline** | **100.0 x 80.0 mm** (derivation: `stackup.md` s4.1) |
| **Corner radius** | **3.0 mm**, all four corners |
| **Mounting holes** | **4x M3 (3.2 mm) at 3.0 mm inset** = a **94.0 x 74.0 mm** hole rectangle, **plus a 5th M3 at (46, 74)**. **REVISED at rev A7 - see 7.1.1.** |
| **Board thickness** | 1.6 mm |
| Coordinate origin for this ICD | board top-left corner, x right, y down |
| **RJ45 position on the carrier** | **top edge**, body (10, 0) - (32, 22) |

#### 7.1.1 Mounting-hole inset - REVISED at rev A7. Read before drilling any daughter.

Rev A6 and earlier froze **5 mm inset / 90 x 70 mm**. The carrier as built is
**3.0 mm inset / 94.0 x 74.0 mm**, and this section is the ICD moving to match the
board rather than the board moving to match the ICD.

| | rev A6 (withdrawn) | **rev A7 (binding)** |
|---|---|---|
| Inset from board edge | 5.0 mm | **3.0 mm** |
| Hole rectangle | 90 x 70 mm | **94.0 x 74.0 mm** |
| Hole positions, board-relative | (5,5) (95,5) (95,75) (5,75) | **(3,3) (97,3) (97,77) (3,77)** |
| Hole diameter | 3.2 mm | 3.2 mm (unchanged) |
| 5th hole | (46, 74) | (46, 74) (unchanged, correct as built) |

**Why the ICD moved and not the board.** `board_init` derives the mounting inset as
`margin / 2` (closed-decisions MECH-01), so the default `--margin 6` produced a 3 mm
inset; reaching 5 mm needs `--margin 10`. P5 asserted MECH-01 satisfied having checked
only the corner radius, and nothing compared the inset to this table. By the time a
P8 review caught it the board was placed and routed, and re-running `board_init`
discards the entire P6 placement and P7 routing. **Both daughters (`lumina-par` at P0,
`lumina-strobe` not started) are pre-P5 and inherit this table at no cost**, so the
cheap and safe correction is here. Owner decision at H4: **no rebuild.**

**Had this not been caught, every daughter drilled to rev A6 would have missed all
four standoffs by 2 mm in x and 2 mm in y** - unfixable daughter-side, and only
discoverable at mechanical assembly.

**WASHER AND STANDOFF WARNING - this is the real cost of the 3 mm inset.** At a 3.0 mm
inset against the 3.0 mm corner radius, the hole wall sits **1.3966 mm** from the board
edge. Consequences for whoever assembles this:

- A standard **M3 washer (7.0 mm OD) overhangs the rounded corner** and will not seat
  flat. Use a **5.0-5.5 mm OD** washer, or none.
- A **5.5 mm A/F standoff flange** likewise overhangs. Use a round standoff of
  **<= 5.0 mm OD** at these four positions.
- Do not substitute a larger flanged fastener without re-checking this dimension.
- The 5th hole at (46, 74) is inboard and takes ordinary M3 hardware.

### 7.2 Connector positions - **FROZEN at P6**

Board-relative to the top-left corner, x right / y down. Absolute board origin is
(19.58, 57.132); subtract it from any absolute coordinate read off the .kicad_pcb.

| Item | Origin | Rot | Position 1 | Even-row y | Land extent |
|---|---|---|---|---|---|
| **J3** POWER 2x7 | **(23.00, 76.00)** | 0 | **(15.380, 77.270)** | 74.730 | (14.11, 73.50) - (31.89, 78.50) |
| **J4** SIGNAL 2x12 | **(71.00, 76.00)** | 0 | **(57.030, 77.270)** | 74.730 | (55.76, 73.50) - (86.24, 78.50) |
| **H5** support hole | **(46.00, 74.00)** | - | - | - | exactly the s7.1 normative value, unchanged |
| **J1** RJ45 body | (11.88, 0.00) - (30.12, 21.74) | - | - | - | see note |

**What moved from the provisional values, and why.** x is within +/-0.3 mm of the
provisional figures. **y moved DOWN 7.97 mm**: the provisional y = 69.3 left the connector
courtyards 6.9 mm off the bottom edge, which fails placelib's 2.5 mm declared-edge tolerance -
the connectors have to sit at the edge they are declared on.

**J1 moved 5.75 mm left** onto the ICD's nominal (10,0)-(32,22) envelope. That is a real
improvement for the daughters: the previous position left only **0.13 mm** of margin inside the
30 x 26 mm notch, which is not a margin. It now has room.

**Daughters may now design to these numbers.** They were provisional until P6 because placement
had not run; they are frozen now.

### 7.3 Stack height and standoffs

| Item | Value |
|---|---|
| Arrangement | **Stacked mezzanine, daughter above the carrier** (Q4 option a) |
| **Mated board-to-board height** | **11.0 mm** hard-seated (2.5 mm male insulator + 8.5 mm socket body), against a positive mechanical stop |
| Male mating pin length | 6.0 mm |
| **Standoffs** | **5x M3 female-female, 11.0 mm** - the four corners plus H5 |
| Daughter socket orientation | **Faces downward** - a reverse-mounted THT part on the daughter's bottom side, or a bottom-side SMD equivalent. This is a daughter assembly instruction, but it is mating geometry and so it lives here |
| First-mate / last-mate control | **none.** A dual-row header has no sequencing, so **the daughter must tolerate 48 V arriving before or after 3.3 V, in either order** |

**Q4's provisional 15 mm standoff is not achievable.** No stocked 2.54 mm header/socket pair reaches
it; the only 15 mm route is a PC/104 stackthrough, which exists in 2x20/2x40 only (forcing the
single-connector scheme and giving up the keying of s7.4) and **publishes no working-voltage
rating**, which CAR-REQ-17 cannot accept. See `stackup.md` s5.

### 7.4 CAR-REQ-16 - reverse-insertion proofing, four independent mechanisms

The known weakness this has to answer: **MECH-01's 4x M3 pattern is rotationally symmetric**, so a
daughter *can physically be bolted down rotated 180 degrees*. All four mechanisms below exist to
make sure it cannot then be **mated**, and the first one is a hard mechanical stop.

1. **The RJ45 notch is a physical interlock.** Every daughter carries a 30 x 26 mm relief at the
   **top** edge, `(6, 0) - (36, 26)`, over the carrier's magjack (s7.6). Rotated 180 degrees, that
   notch is at the bottom edge and the daughter presents **solid board** over a jack that stands
   ~15 mm above a carrier whose stack height is 11.0 mm. **The boards cannot be forced flat.** This
   is a stop, not a warning.
2. **Different position counts at fixed asymmetric coordinates.** A 2x7 socket cannot mate a 2x12
   header. Cross-mating is impossible.
3. **180-degree rotation does not align either connector.** About the board centre (50, 40): J3's
   centre (24, 73) maps to (76, 7) and J4's (72, 73) maps to (28, 7). Neither lands on the other or
   on any carrier connector.
4. **The 5th mounting hole breaks the rotational symmetry of the hole pattern.** H5 at (46, 74) maps
   to (54, 6), so a rotated daughter cannot take the 5th standoff - a visible, pre-power tell that
   needs no instrument.
5. **Silkscreen.** A pin-1 triangle at position 1 of both blocks on **both** boards, plus a
   `^^ RJ45` edge arrow on the carrier and a matching arrow on every daughter.

### 7.5 CAR-REQ-15 - mechanical support

The two connectors span 74 mm of the bottom edge, with their inner ends 34 mm and 44 mm from the
nearest corner standoff. A mated 38-position pair is stiff, so board flex would otherwise be carried
by the pins. **H5 at (46, 74), directly between J3 and J4, is the required support point** and is
part of the common footprint.

Note that `board_init --mounting-holes` generates corner holes only (0..4); H5 is added at P4 as a
`MountingHole_3.2mm_M3` symbol so it carries a refdes and a deterministic placement.

### 7.6 Exclusion zones every daughter must respect

Board-relative, in the shared footprint's coordinates:

| Zone | Region | Requirement |
|---|---|---|
| **RJ45 relief** | **(6, 0) - (36, 26)** | **The daughter must be cut away here** - a 30 x 26 mm notch in the **top** edge. The carrier's board-edge magjack is ~15 mm tall and the stack is 11.0 mm, so the jack protrudes ~4 mm above the daughter's underside. The outline rectangle, corner radius and 5-hole pattern are **unchanged** - only this local relief differs. It is also the primary keying interlock (s7.4) |
| **DC-DC hot zone** | **(2, 46) - (36, 68)** | **No LED drivers and no aluminium electrolytics** in the corresponding region on the daughter. The carrier's 48->12 converter dissipates up to 1.25 W here. **Thermal budget: see s7.7 (rev A5 - box-air heat budget; the rev A2 af figure was correct under an unstated assumption, the at figure was not, and no venting is required).** Electrolytic life halves per 10 C. This is the CAR-REQ-18 answer, and it has to be a keepout rather than an in-plane separation rule because in a stacked mezzanine the daughter's parts sit *vertically over* the carrier's |
| **Antenna column** | **(88, 25) - (100, 55)** | **No copper on any layer, and no metal component**, while Q8 keeps the radio functional. The carrier's ESP32-S3 PCB antenna is directly below and a ground plane 11 mm above it will detune it. **Void if Q8 closes as "radio permanently dead"** |
| **Recovery header** | **(76, 0) - (98, 20)** | Keep clear enough that a 6-way jumper lead can be attached with the daughter fitted, or accept that the daughter must be removed to recover firmware |

---

### 7.7 Thermal budget - rev A5. NORMATIVE.

**Configuration of record (owner decision): SEALED, non-metallic enclosure, with LED heat conducted
OUT through the enclosure wall.** Not vented. Consistent with H1-Q5.

#### 7.7.1 What was actually wrong with the rev A2 figures

Rev A2 published "56 C (af) / 69 C (at)". Rev A3 called both figures wrong. **That was unfair to the
af figure and is corrected here.** The strobe run applied the par's measured sealed-box resistance to
its own heat sources and reproduced both numbers from a single binary - whether the LED heat leaves
through the wall or stays inside the box:

| LED wall path | Heat into box air | Rise at 3.6-4.3 K/W | 25 C room | 35 C room | 40 C room |
|---|---|---|---|---|---|
| **works** | 1.894 W | 6.8-8.1 K | **32-33 C** | 42-43 C | 47-48 C |
| **fails** | 8.500 W | 30.6-36.6 K | **56-62 C** | 66-72 C | 71-77 C |

**Row B at a 25 C room is 56 C - the rev A2 af figure, to the degree.** So that figure was never
miscalculated. It was the *LED-heat-stays-in-the-box* case, at a 25 C room, and **neither assumption
was written down**. That omission is the whole defect: it made a correct number look arbitrary, and it
silently assumed exactly the arrangement the owner's enclosure decision has since ruled out.

**The `at` figure was a genuine error.** 69 C does not follow from the af point under *either* row -
convection is near-linear in delta-T at this scale, so roughly doubling box heat roughly doubles the
rise. 56 C implies ~3.13 K/W; 69 C implies ~2.29 K/W. They cannot both be true.

The par's independent Hoffman/Rittal calculation of **89-115 C** sits above even the LED-in-box case at
a 40 C room. It is the **conservative bound**, not a competing estimate - **do not average it** with
anything here.

#### 7.7.2 The budget (configuration of record)

Sealed non-metallic enclosure, internal-air-to-room **3.6-4.3 K/W**. Holding internal air to **70 C**,
i.e. 15 K below the +85 C limit shared by the ESP32-S3 module and the par's emitter family:

| Room ambient | Allowable air rise | **Allowable box-air heat (4.3 K/W worst case ... 3.6 K/W)** |
|---|---|---|
| **25 C** | 45 K | **10.5 ... 12.5 W** |
| **30 C** | 40 K | **9.3 ... 11.1 W** |
| **40 C** | 30 K | **7.0 ... 8.3 W** |

Spending against it, with the wall path working:

| Contributor | af (build 1) | at (upgrade) |
|---|---|---|
| Carrier overhead (PD + both converters + MCU + PHY) | ~2.4 W | ~3.7 W |
| Daughter into box air (strobe, measured) | ~1.9 W | ~1.9 W |
| **Total box-air heat** | **~4.3 W** | **~5.6 W** |
| LED junction heat | through the wall | through the wall |

#### 7.7.3 Conclusions - binding on every LUMINA board

1. **A sealed enclosure closes for BOTH af and at, and does so up to a 40 C room.** At 40 C the
   allowable budget is 7.0-8.3 W against ~5.6 W spent at `at`: internal air reaches
   40 + 5.6 x 4.3 = **64 C worst case**, under the 70 C target and well under the +85 C part limit.
   **The at upgrade therefore does NOT require enclosure ventilation** - the rev A3 conclusion that it
   did is withdrawn, and the carrier's open ventilation item is closed.
2. **This rests entirely on the LED heat leaving through the wall.** If that path is not built, the
   numbers revert to row B of s7.7.1 and the margin disappears. **The wall-conduction path is a
   mechanical requirement, not a nicety.**
3. **Every daughter must declare, in its design document, how its dissipation splits between box air
   and the enclosure wall.** The strobe's ~1.9 W is the number this budget is built on.
4. **Every internal-air figure in this ICD carries an explicit room ambient.** A figure quoted without
   one is incomplete - that is the exact defect that produced the rev A2 confusion.

### 7.8 Carrier firmware requirements of record

These are firmware commitments the carrier makes to its daughters. They are recorded here because a
daughter's requirements depend on them and they must not be silently dropped when firmware is written.

| ID | Requirement |
|---|---|
| **FW-01 (CR-5, granted)** | Carrier firmware **shall** apply **PWM-domain dithering of at least 3-4 bits**. This is the mechanism by which the par's PAR-REQ-01 is met - no hardware on that board can close it. **The dither must be in the PWM domain, NOT the 60 fps frame domain**: a 4.4 % dither at 60 Hz breaches IEEE 1789's no-effect level by itself, so frame-domain dithering would create the very flicker it is meant to avoid. |
| **FW-02 (CR-4, granted)** | Where a daughter runs four or more channels on one LEDC timer, firmware **shall** apply a **90 degree phase stagger** (`hpoint`) across them, to avoid a 4x larger input-current step when all channels switch together. Free in hardware. |
| **FW-03** | Firmware **shall** read `ID_ADC` at boot (s3.4) and **shall not** assert `ENABLE` on a FAULT (short) or NONE (open) reading. |
| **FW-04** | Firmware **shall** apply the daughter's declared channel -> timer -> frequency map (s3.5) from the `ID_ADC` code, rather than assuming all channels sit at the default rate. |
| **FW-05** | Firmware **shall** maintain the PD's MPS: valid MPS needs >= 10 mA DC, so the board must never idle below it (ESP32-S3 deep sleep is therefore forbidden while powered from PoE). |

---

## 8. ENABLE, FAULT and the fail-safe contract

### 8.1 What ENABLE is

`ENABLE` is **active HIGH**, driven push-pull from an ESP32-S3 GPIO chosen specifically because it
is in the pin band with **no documented power-up glitch**. It is **one net** that reaches both the
carrier's 48 V eFuse shutdown input and connector pin J4-23, so the 48 V rail and the daughter's
global enable can never disagree.

**A single 10 kohm pull-down on the carrier is the fail-safe** (CAR-REQ-08). It is passive, so it
cannot be defeated by firmware, a reset, a brownout or a reboot.

### 8.2 What the daughter must do

| Requirement | Why |
|---|---|
| **Fit a 100 kohm pull-down on the daughter's ENABLE input** | So the daughter fails de-energised if the connector is unmated, mis-seated by one position (ENABLE lands on ADC1 or falls off the end), or a pin is unsoldered |
| **Gate every output stage with ENABLE** - LED driver EN pins, gate drivers, the cap-bank charge path | A carrier PWM pin can produce a ~60 us glitch at power-up. ENABLE is the thing that makes that a no-op |
| **Never latch ENABLE locally** | The whole chain must de-assert within one carrier reset |
| **Fit the CAR-REQ-17 bleed path on the 48 V rail** | The carrier bleeds its own side through 100 kohm, but the daughter holds the stored energy. **The carrier deliberately fits no series diode on `+48V_SW`**, so the daughter's bleed path is not stranded above the carrier's |
| **Own the inrush ramp** | The carrier's eFuse dV/dT is set *fast* and its limit sits **above** the daughter's inrush level, deliberately, so the two soft-starts do not fight. Size the limiter against the **PD's 1.0 A operating current limit**, not against the connector's 5.4 A rating - sizing against the connector is the classic way to trip the PD's 800 us foldback deglitch and brown out the entire fixture |
| **Never drive FAULT high** | It is open drain and wire-OR'd with the carrier's own eFuse fault output |

### 8.3 The 802.3 compliance clause daughters must know about

**IEEE 802.3 caps PD port capacitance at roughly 180 uF.** LUM-STR-A's ~2800 uF bank is 15 times
that. Charged at the PD interface's own 140 mA inrush limit it would take ~960 ms - more than ten
times the standard's 80 ms operational-current window, and outside any PSE start-up template.

**Therefore the carrier's 48 V load switch is a compliance part, not merely a CAR-REQ-14 protection
feature.** It is OFF through detection, classification, inrush and the 80 ms window, and it closes
only after firmware asserts ENABLE. Two consequences for daughters:
- **`+48V_SW` is dead at power-up and stays dead for hundreds of milliseconds.** Design for it.
- **A daughter must not provide any path that energises its bank from `+12V` or `+3V3`** while
  `+48V_SW` is off, or it re-creates the compliance problem behind the switch's back.

---

### 8.4 How ENABLE actually de-asserts the rail - CAR-REQ-08 realisation (P3-verified)

The carrier switch is a **TPS16630**. It has **no EN pin**. Its only control is **SHDN (pin 13),
active-low shutdown with an INTERNAL PULL-UP**: open-circuit 2.48 V min / 2.7 V typ, enable
threshold 2.0 V rising, shutdown 0.8 V falling. **Left alone the part DEFAULTS ON** - the internal
pull-up sits above its own enable threshold.

CAR-REQ-08 is therefore satisfied by a **mandatory external pull-down**, not by the part's own
behaviour:

- **R(SHDN) = 10 kOhm, SHDN to GND.** The datasheet requires a pull-down able to sink >= 10 uA while
  holding < 0.8 V; the internal pull-up sources <= 10 uA, so 10 kOhm holds the pin at ~0.1 V -
  **8x margin below the 0.8 V shutdown threshold**.
- **ENABLE** (carrier net, driven by an ESP32-S3 GPIO) drives SHDN **HIGH** to enable. SHDN abs max
  is 5.5 V, so it is a 3.3 V logic pin and must **never** be exposed to 48 V. The eFuse GND and logic
  GND are the same node, so no level shifting is required.

**Review gate 4 - the three demanded cases:**

| Case | GPIO state | SHDN | +48V_SW |
|---|---|---|---|
| **MCU held in reset** | Hi-Z (ESP32-S3 GPIOs are high-impedance in reset) | ~0.1 V via the pull-down | **OFF** |
| **Mid firmware update** | Hi-Z through the resets that bracket flashing | ~0.1 V | **OFF** |
| **Brownout** | GPIO cannot source; the pull-down dominates. Independently the eFuse's own programmed UVLO on the 48 V side opens the FET below threshold | ~0.1 V | **OFF** |

**No part substitution and no added series gate.** The TPS16630 stays; the 10 kOhm pull-down is the
fail-safe element. A daughter may therefore assume that an unprogrammed, crashed, or unpowered
carrier presents **0 V**, not 48 V, at J3.

---

## 9. Isolation, safety and the things daughters inherit

**The entire fixture is non-isolated and floats at PoE potential.** The carrier uses a non-isolated
buck (Q5 default), which achieves 802.3 compliance **only** by there being no accessible external
conductor. Every one of these is load-bearing and every one lands on the daughter as much as the
carrier:

- **Non-conductive (plastic / 3D-printed) enclosure.**
- **No chassis earth**, no earthed mounting hardware bonded to board GND.
- **Ethernet is the only external connection.** This is why there is **no USB-C on the carrier**
  (Q9 option (a) is unavailable), and it means **a daughter may not add an external connector of any
  kind** - no barrel jack, no DMX, no second Ethernet.
- **The daughter, its LED drivers and its LED wiring are all at PoE potential.** If the LED module
  is on a separate heatsink (Q4a default), that heatsink and its wiring are at PoE potential too.
  **If the heatsink is touchable, metal, or shares a mount with anything earthed, the non-isolated
  topology is non-conformant.** This is `decisions.md` OPEN-C and it is unresolved.
- **Bench hazard.** An earthed scope probe or a non-isolated USB-UART adapter ties the floating PoE
  return to earth. Beyond the shock and damage risk, the resulting ground currents **break PD
  signature detection outright** - detection currents are only a few hundred microamps. The
  carrier's recovery header is silkscreened accordingly; daughters must carry the same warning on
  any test point.

Positive side: 57 V DC is below the IEC 62368-1 **ES1** limit of 60 V, so no safety-mandated
creepage applies anywhere - s5's 0.635 mm is **functional insulation** protecting the silicon, not a
personnel safeguard. And an unearthed PD needs **no MOV-to-earth surge network**; do not copy one
out of a reference design.

---

## 10. Revision control

| Field | Value |
|---|---|
| Revision | **DRAFT-A** |
| Frozen at | **H1** (checkpoint 1), except s7.2 connector coordinates, confirmed at end of P6 |
| Owner | LUM-CAR-A |
| Change process | A daughter that cannot meet this document raises a **blocking issue against LUM-CAR-A**. The carrier owner issues rev B and every daughter re-baselines. **No daughter implements a local variant.** |

### 10.1 Open items that could still move this document before it freezes

| ID | Item | What moves |
|---|---|---|
| **Q6** | worst-case daughter draw per rail | every +1.8 A of 48 V requirement is one more pin; above 3 A the power block becomes a 2x8 (socket stock 47 pcs) or 2x9. **The whole of s3.1 and s4** |
| **Q4** | stack height | s7.3. If the human rejects the daughter relief in s7.6, the answer is a panel-mount RJ45, which also changes the carrier outline - so it must land **before P5** |
| **Q5** | isolated vs non-isolated | all of s9, and a 2.0 mm barrier spacing requirement would appear |
| **Q8** | radio functional | s7.6's antenna column, and the carrier's board edge |
| **Q10** | ID mechanism | s3.3's `ID_ADC` definition (currently divider + shared-I2C EEPROM) |
| **D-04** | strobe colour | **nothing.** s3.3's timer allocation works for both answers - that is deliberate |
