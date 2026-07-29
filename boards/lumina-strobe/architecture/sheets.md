# LUM-DTR-STROBE-A - hierarchical sheet plan

Four child sheets under a thin stitching root. ~65 components across four cleanly separable
domains, so hierarchy buys parallel P4 sheet generation and keeps the 48 V energy store visually
and electrically isolated from the analogue loop and the ICD boundary.

**The sheet NAMES below are contractual.** They appear verbatim in netlist net names
(`/charge/CHG_GATE`) and `architecture/constraints.json` already references sheet-crossing names;
renaming a sheet renames nets and breaks `netlist_audit --constraints`.

| Sheet | File | Blocks | Interface nets (sheet pins) | refdes range | `pwr_base` |
|---|---|---|---|---|---|
| root `lumina-strobe` | `lumina-strobe.kicad_sch` | none (stitching only) | - | - | 1 (unused) |
| **`conn`** | `conn.kicad_sch` | J3 POWER, J4 SIGNAL, ENABLE pull-down, ID divider bottom leg, ADC RC filters, rail decoupling, mounting holes, test points | `ENABLE`, `FAULT`, `PWM0`, `PWM1`, `PWM4`, `ADC0`, `ADC1`, `ID_ADC`, `I2C_SCL`, `I2C_SDA`, `VBANK_SENSE` | **1-99** | **100** |
| **`charge`** | `charge.kicad_sch` | input TVS, hot-swap controller, charge FET, sense shunt, 2720 uF bank, passive + active bleed, bank divider | `ENABLE`, `VBANK`, `VBANK_SENSE`, `CHG_EN_n` | **100-199** | **200** |
| **`drive`** | `drive.kicad_sch` | error amp, setpoint RC + SPDT, pass FET, current shunt, gate clamp, drain TVS, Vds divider, harness connector | `VBANK`, `PWM0`, `PWM4`, `ENABLE`, `OT_TRIP`, `UVLO_n`, `VDS_SENSE` | **200-299** | **300** |
| **`protect`** | `protect.kicad_sch` | 2x dual comparator on `+12V` (board OT, LED OT, Vds fault latch, bank UVLO + ceiling), NTC dividers, TMP112, off-board NTC landing | `VBANK_SENSE`, `VDS_SENSE`, `ENABLE`, `PWM1`, `OT_TRIP`, `UVLO_n`, `CHG_EN_n`, `FAULT`, `ADC1`, `I2C_SCL`, `I2C_SDA` | **300-399** | **400** |

**Exception to the refdes ranges:** `J3`, `J4` and `H5` keep the designators the ICD assigns them
(ICD s7.2). Everything else follows the decade scheme, which is what keeps refdes unique across
sheets without coordination.

---

## 1. Net naming - the CANONICAL final netlist names

Mechanism (verified in this repo at `tests/s7_regen/hierdemo/kicad/hierdemo.net`):

1. **Power SYMBOLS make a net global across the whole hierarchy** with a **bare** name and need no
   sheet pin.
2. A child net merged with the root through a sheet pin takes the **root-side label**:
   `Project.add_sheet(child, ..., nets=["X"])` wires each sheet pin outward to a root local label
   `X`, so the net becomes **`/X`**.
3. A child-internal label becomes **`/<sheet>/NAME`**.

**These are the names `constraints.json` uses and they are contractual.** Getting one wrong makes
`check_creepage` hard-error (it raises on a declared voltage net that is not on the board) and makes
`check_current` / `check_thermal` silently no-op.

### 1.1 Global rails - power symbols, bare names

| Net | Present on | Driven by | PWR_FLAG? |
|---|---|---|---|
| `GND` | all four | J3 pins 2/4/6/7/8/10/13 (passive) | **yes**, on `conn` |
| `+48V_SW` | conn, charge | J3 pins 1/3/5 (passive) | **yes**, on `conn` |
| `+12V` | conn, drive, protect | J3 pins 9/11 (passive) | **yes**, on `conn` |
| `+3V3` | conn, protect | J3 pins 12/14 (passive) | **yes**, on `conn` |

All four PWR_FLAGs live on `conn`, the sheet that owns the connector, at `#FLG0100+`. Power symbols
being global, one flag each drives the net hierarchy-wide.

**`+48V_SW` deliberately does not appear on `drive` or `protect`.** The only 48 V-domain net that
crosses into `drive` is `/VBANK`, and it does so through the harness connector and the pass FET.
If `+48V_SW` ever appears on `drive` or `protect`, that is a design error, not a routing
convenience - it would be a path that could energise something ahead of the charge FET.

### 1.2 Root-crossed signals - `/NAME`

| Net | Direction | Notes |
|---|---|---|
| `/ENABLE` | conn -> charge, drive, protect | Active HIGH. **100 k pull-down on `conn`** (ICD s8.2, mandatory). Gates the charge path's EN, the pass-FET gate clamp, and the active bleed's disarm. **Never latched locally** |
| `/FAULT` | protect -> conn | **Open drain, active low.** No pull-up on this board - the carrier's 10 k owns it. **Never driven high** |
| `/PWM0` | conn -> drive | **FLASH_GATE.** A 5-200 ms one-shot at 1-25 Hz, LEDC timer 0. See `blocks.md` s4 |
| `/PWM1` | conn -> protect | **BANK_ARM.** Static DC level, 0 % = 44.5 V ceiling, 100 % = 48.0 V. Timer 0, frequency-agnostic |
| `/PWM4` | conn -> drive | **AMP_SET.** 13-bit at 9.766 kHz, LEDC timer 1, RC-filtered into the regulator reference |
| `/ADC0` | conn (local) | Bank voltage telemetry, from `/VBANK_SENSE` through an RC at the pin. Rth 9.43 k, inside the ICD's 10 kohm |
| `/ADC1` | protect -> conn | LED-module thermistor telemetry, independent `+3V3`-referenced leg |
| `/ID_ADC` | conn (local) | Board-type ID, **bottom leg only** - the carrier fits the 10 k top leg. **Placeholder value; the code is allocated by the carrier owner and must be confirmed before P8** |
| `/I2C_SCL`, `/I2C_SDA` | protect <-> conn | TMP112. **No pull-ups on this board** - the carrier's 4.7 k own the bus |
| `/VBANK` | charge -> drive | Bank positive. **57 V, 2.6 A pulse** |
| `/VBANK_SENSE` | charge -> conn, protect | Divided bank voltage (2 x 82 k + 10 k). Three consumers: `ADC0`, the UVLO/ceiling comparator, the Vds comparator's reference leg |
| `/VDS_SENSE` | drive -> protect | Divided pass-FET drain voltage (2 x 82 k + 10 k, identical ratio) |
| `/OT_TRIP` | protect -> drive, conn | Wire-OR of three open-collector outputs (board OT, LED OT, Vds fault). Pulls the gate clamp **and** `FAULT` |
| `/UVLO_n` | protect -> drive | Bank undervoltage lockout. Inhibits the drive stage only - it must **not** assert `FAULT` (an empty bank at power-up is not a fault) |
| `/CHG_EN_n` | protect -> charge | Bank-ceiling comparator output, pulls the hot-swap controller's `EN` low above the ceiling |

### 1.3 Sheet-internal nets that `constraints.json` names

| Net | Sheet | Why it is declared |
|---|---|---|
| `/charge/CHG_GATE` | charge | **64 V - the highest-voltage net on the board** (V_GATE-OUT is 12-16 V above VCC). Declared in `voltages` so the clearance rule covers it |
| `/drive/LED_K` | drive | Harness return = pass-FET drain. **57 V, 2.6 A**, and the thermal-pour net for Q200 |
| `/drive/ISNS` | drive | Pass-FET source to shunt high side. **2.6 A**, but a low-voltage node - deliberately **not** in `voltages`, so `check_creepage` treats it as 0 V and demands the full clearance from `/drive/LED_K` across the FET |

### 1.4 A merge decision worth recording

**`research/power.json` declares `/VBANK` and `/LED_A` as separate power constraint entries. They
are one net here, `/VBANK`.** Nothing sits between the bank's positive terminal and the harness
connector's pin 1 - no fuse, no series element - so `/LED_A` would be an alias, and a declared net
that does not exist in the netlist makes `check_creepage` hard-error at P8. **`/LED_A` is deleted,
not renamed.** `/LED_K` survives as `/drive/LED_K` because there genuinely is a device (the string)
between it and `/VBANK`.

---

## 2. Sheet contents and refdes allocation

### 2.1 `conn` - refdes 1-99, `pwr_base` 100

| Refdes | Part | Note |
|---|---|---|
| `J3` | POWER socket, 2x7, 2.54 mm, CONNFLY DS1023-2\*7SF11 class | **bottom side, faces DOWN.** Pin map = ICD s3.1 verbatim |
| `J4` | SIGNAL socket, 2x12, CONNFLY DS1023-2\*12SF11 class | **bottom side, faces DOWN.** Pin map = ICD s3.2 verbatim |
| `H1`-`H4` | M3 3.2 mm mounting holes | generated by `board_init --mounting-holes 4`, board-only |
| `H5` | `MountingHole_3.2mm_M3` symbol at (46, 74) | **added at P4 as a symbol so it carries a refdes** - `--mounting-holes` makes corner holes only |
| `R1` | 100 k 0603 | **ENABLE pull-down, ICD-mandated** |
| `R2` | ID_ADC bottom leg, 0603 1 % | **placeholder value - confirm with the carrier owner before P8** |
| `R3`, `C3` | ADC0 RC (1 k + 10 nF) | 9.43 k source impedance is at the ICD ceiling; SAR sampling charge wants a local reservoir |
| `R4`, `C4` | ADC1 RC | same |
| `C1` | `+12V` local bulk, **<= 4.7 uF** | deliberately small so the error amp dies promptly on unplug |
| `C2`, `C5` | `+3V3` and `+12V` 100 nF | |
| `TP1`-`TP6` | test points: `+48V_SW`, `/VBANK`, `GND`, `/drive/ISNS`, `/OT_TRIP`, `/ENABLE` | **every one carries the floating-PoE silkscreen warning** |

### 2.2 `charge` - refdes 100-199, `pwr_base` 200

| Refdes | Part | Note |
|---|---|---|
| `D100` | TVS, SMBJ58A class, SMB | 58 V standoff / 93.6 V clamp, under the 100 V cap rating |
| `U100` | Hot-swap / power-limiting controller, TPS2490 class, MSOP-10 | **ILIM 0.20 A, PLIM 12 W, fault timer > 653 ms.** EN is GND-referenced |
| `Q100` | Charge FET, D2PAK N-channel 100 V, IRF540N class | Tab = drain = `+48V_SW`. **>= 645 mm2 pour** |
| `R100` | Sense resistor, 0805 or 1206, value from the controller's threshold at P3 | ~250 mohm if the threshold is 50 mV |
| `R101`, `R102`, `R103`, `C100`, `C101`, `C102`, `R104` | PROG/PLIM divider, TIMER, VCC bypass, dv/dt gate cap, EN series | |
| `C110`-`C113` | Bank HF: 4 x 10 uF / 100 V X7S 1210 | **2.7 uF each effective at 48 V** |
| `C120`-`C125` | Bank bulk: **six D18 / 7.5 mm radial footprints, four populated** at 680 uF / 100 V | Second-sources the bank at 470 uF across four vendors; 2720 -> 4080 uF knob with no respin |
| `R110` | Passive bleed, 100 k 0805, 150 V working | 23 mW, 272 s. **Un-defeatable** |
| `R111`, `R112` | Active bleed, 2 x 470 ohm 2512 2 W | 1.23 W peak each, inside the continuous rating - **no joule rating needed, and none is published** |
| `Q110` | Bleed switch, 150 V N-ch SOT-223, CJT04N15 class | |
| `Q111`, `R113`, `D110` | Disarm 2N7002, 1 M bias from `/VBANK`, 10 V zener clamp | **Bias UP from the bank, pull DOWN to disarm** - so "every rail dead" is the ON state |
| `R120`, `R121`, `R122` | Bank divider, 2 x 82 k + 10 k, 0805 | Rth 9.43 k. Satisfies the 0805 rule *and* the series-split rule at once |

### 2.3 `drive` - refdes 200-299, `pwr_base` 300

| Refdes | Part | Note |
|---|---|---|
| `Q200` | Pass FET, D2PAK planar HEXFET-5, 200 V / 18 A, IRF640N class | Tab = drain = `/drive/LED_K`. **>= 900 mm2 pour, target 1000 mm2, >= 12 thermal vias** |
| `R200` | Shunt, 200 mohm 3 W 2512 1 % | 520 mV FS. **Kelvin layout** - sense traces to the pad ends |
| `U200` | Dual op-amp, LM2904 class, SOIC-8, **on `+12V`** | A = error amp / gate driver; B = setpoint buffer, free |
| `U210` | SPDT analogue switch, SGM3157 class, SC-70-6 | Steers the **reference**, not the gate |
| `R201`, `R202`, `C200` | Setpoint RC + divider: 10 k + 100 nF, 5k36/1k00 (6.35:1) | tau 1 ms, 4.6 ms to 1 %, 2.6 % ripple at 9.766 kHz |
| `R203` | Gate pull-down 4k7 | **The interlock of record** - off with *everything* dead |
| `R204` | Gate series | |
| `Q210`, `Q211` | 2 x 2N7002 (JLC **Basic**) | One inverts ENABLE, one clamps gate-to-source. Also the landing point for `/OT_TRIP` and `/UVLO_n` |
| `D200` | Drain-source TVS, SMBJ58A class | Harness `L di/dt` clamp. **NOT a freewheel diode across the string** |
| `R210`, `R211`, `R212` | Vds divider, 2 x 82 k + 10 k, 0805 | Identical ratio to the bank divider, so the fault trip is ratiometric |
| `J200` | Harness, JST VH 2-pin THT, 10 A / 250 V | `/VBANK` and `/drive/LED_K` to the off-board module. **Top edge** |
| `TP200`-`TP202` | shunt Kelvin probe point, gate, `/drive/LED_K` | short-return probe point at the shunt - a standard ground lead cannot measure this edge |

### 2.4 `protect` - refdes 300-399, `pwr_base` 400

| Refdes | Part | Note |
|---|---|---|
| `U300` | Dual comparator, LM2903 class, SOIC-8, **on `+12V`** | A = board OT, B = LED-module OT |
| `U301` | Dual comparator, LM2903 class, SOIC-8, **on `+12V`** | A = Vds fault (latched), B = bank UVLO + ceiling |
| `RT300` | NTC 10 k 0603, **in Q200's drain pour** | |
| `RT301` | NTC 10 k 0603, **in Q100's drain pour** | **In parallel with RT300** as one divider's bottom leg - the hotter device dominates, so one comparator section ORs both |
| `R300`-`R309` | OT dividers and ratiometric references from `+12V` | supply-independent trip |
| `R310`-`R315`, `C300` | Vds threshold (~0.45), arming RC (10 k + 10 nF = 100 us blank) | |
| `Q300` | 2N7002, fault latch | **Cleared only by `ENABLE` going low** - a fault latch, not an ENABLE latch |
| `R320`-`R323` | Bank UVLO and ceiling thresholds, hysteresis | UVLO trip = `V_string + 1.7 V`, **set by one 1 % resistor at P3 from the measured string** |
| `U310` | TMP112 class, SOT-563, **on `+3V3`** | I2C telemetry. **Fit no pull-ups** |
| `J300` | 4-way internal landing for the two off-board thermistors | LED-module NTC (trip, `+12V`) and LED-module NTC (telemetry, `+3V3`). **JLC stocks no leaded/probe NTC at all** - these are hand-terminated, not a PCBA line |
| `R330`, `R331` | LED-module NTC divider, **NTC as the TOP leg** | an open harness wire pulls the node low and **trips** - fail-safe on a broken wire |

---

## 3. What P4 must review before generating

Three items that are invisible on the bench and expensive at P8:

1. **The 48 V domain boundary.** No component may bridge `+12V` or `+3V3` to `+48V_SW`, `/VBANK` or
   `/drive/LED_K` (ICD s8.3 point 2). The only nets crossing are `ENABLE`/`PWM` into GND-referenced
   inputs and the two divider taps, which run **out** of the 48 V domain into high-impedance
   inputs. Violating this re-creates the 802.3 port-capacitance problem behind the compliance
   switch's back and shows up only as a PD compliance failure.
2. **`FAULT` has no pull-up on this board and is never driven by a push-pull output.** Every device
   touching it is open collector or open drain.
3. **No I2C pull-ups.** The carrier's 4.7 k own the bus.
