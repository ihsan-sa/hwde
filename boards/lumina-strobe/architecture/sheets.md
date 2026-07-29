# LUM-DTR-STROBE-A - hierarchical sheet plan

> **REV B - H1 REVISION, 2026-07-28.** RGBW. **The single `drive` sheet becomes FOUR sibling
> sheets, one per colour** - see the decision in s0 below. Everything else keeps its rev A
> structure; `conn`, `charge` and `protect` are edited, not rebuilt.

**Seven child sheets under a thin stitching root.** ~140 components across cleanly separable
domains, so hierarchy buys parallel P4 sheet generation and keeps the 48 V energy store visually
and electrically isolated from the analogue loops and the ICD boundary.

**The sheet NAMES below are contractual.** They appear verbatim in netlist net names
(`/charge/CHG_GATE`, `/drive_w/LED_K`) and `architecture/constraints.json` references them;
renaming a sheet renames nets and breaks `netlist_audit --constraints`.

## 0. Four sibling sheets, not one sheet instantiated four times  **[REV B]**

**Decision: four distinct sheet files - `drive_w`, `drive_r`, `drive_g`, `drive_b` - each with its
own refdes band and its own `pwr_base`.** Rejected: one `drive.kicad_sch` instantiated four times.

Three reasons, in the order that decides it:

1. **Refdes uniqueness is trivially guaranteed** by disjoint bands, with no dependence on KiCad's
   per-instance annotation data surviving a pipeline round-trip. Every P4/P8 check in this pipeline
   keys on refdes.
2. **Net names come out readable and distinct**: `/drive_w/LED_K` vs `/drive_r/LED_K`. A repeated
   instance produces path-qualified duplicates of the same local name, and `constraints.json`
   declares four *different* 2.6 A / 57 V nets that P8 must resolve individually.
3. **P6 wants four independent placement groups anyway** - each stage clusters tightly around its
   own pass FET and drain pour, and those pours must be >= 16 mm apart (`power_tree.md` s11).

Cost of the choice: four near-identical sheet files instead of one. **They must be generated from
one parameterised routine at P4 so they cannot drift** - a hand-edited copy of a drive stage is
exactly the kind of divergence that shows up as an intermittent single-colour fault on the bench.

| Sheet | File | Blocks | Interface nets (sheet pins) | refdes range | `pwr_base` |
|---|---|---|---|---|---|
| root `lumina-strobe` | `lumina-strobe.kicad_sch` | none (stitching only) | - | - | 1 (unused) |
| **`conn`** | `conn.kicad_sch` | J3 POWER, J4 SIGNAL, ENABLE pull-down, ID divider bottom leg, ADC RC filters, rail decoupling, mounting holes, test points | `ENABLE`, `FAULT`, `PWM0`-`PWM7`, `ADC0`, `ADC1`, `ID_ADC`, `I2C_SCL`, `I2C_SDA`, `VBANK_SENSE` | **1-99** | **100** |
| **`charge`** | `charge.kicad_sch` | input TVS, hot-swap controller, charge FET, sense shunt, 2720 uF bank, passive + active bleed, bank divider | `ENABLE`, `VBANK`, `VBANK_SENSE`, `CHG_EN_n` | **100-199** | **200** |
| **`drive_w`** | `drive_w.kicad_sch` | white stage: error amp, setpoint RC + SPDT, pass FET, current shunt, gate clamp, drain TVS, Vds divider | `VBANK`, `PWM0`, `PWM4`, `ENABLE`, `OT_TRIP`, `UVLO_n`, `VDS_SENSE_W`, `LED_K_W` | **200-249** | **300** |
| **`drive_r`** | `drive_r.kicad_sch` | red stage, identical | `VBANK`, `PWM1`, `PWM5`, `ENABLE`, `OT_TRIP`, `UVLO_n`, `VDS_SENSE_R`, `LED_K_R` | **250-299** | **400** |
| **`drive_g`** | `drive_g.kicad_sch` | green stage, identical | `VBANK`, `PWM2`, `PWM6`, `ENABLE`, `OT_TRIP`, `UVLO_n`, `VDS_SENSE_G`, `LED_K_G` | **300-349** | **500** |
| **`drive_b`** | `drive_b.kicad_sch` | blue stage, identical | `VBANK`, `PWM3`, `PWM7`, `ENABLE`, `OT_TRIP`, `UVLO_n`, `VDS_SENSE_B`, `LED_K_B` | **350-399** | **600** |
| **`protect`** | `protect.kicad_sch` | 2x **quad** comparator on `+12V` (board OT, LED OT, bank UVLO, bank ceiling, **4x Vds fault latch**), NTC dividers, TMP112, **I2C I/O expander**, `BANK_ARM_n` fail-safe stage, harness connector J200, off-board NTC landing J300 | `VBANK`, `VBANK_SENSE`, `VDS_SENSE_*` x4, `LED_K_*` x4, `ENABLE`, `OT_TRIP`, `UVLO_n`, `CHG_EN_n`, `FAULT`, `ADC1`, `I2C_SCL`, `I2C_SDA` | **400-499** | **700** |

**[REV B] `J200` moves from `drive` to `protect`.** With four colours it is a single 6-way
connector fed by four different sheets, so it cannot live inside any one of them. `protect` is the
sheet that already sees all four `LED_K_*` nets (the Vds comparators) and already owns `J300`, so
it owns the harness boundary too.

**Exception to the refdes ranges:** `J3`, `J4` and `H5` keep the designators the ICD assigns them
(ICD s7.2). Everything else follows the band scheme, which is what keeps refdes unique across
sheets without coordination.

**`pwr_base` values are 100 apart and disjoint across all seven sheets** (100 / 200 / 300 / 400 /
500 / 600 / 700), so `#PWR` designators never collide even where a component band and another
sheet's power band share a decade - `R400` and `#PWR0400` are different namespaces, but two sheets
both emitting `#PWR0400` would not be.

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
| `+12V` | conn, **all four drive sheets**, protect | J3 pins 9/11 (passive) | **yes**, on `conn` |
| `+3V3` | conn, protect | J3 pins 12/14 (passive) | **yes**, on `conn` |

All four PWR_FLAGs live on `conn`, the sheet that owns the connector, at `#FLG0100+`. Power symbols
being global, one flag each drives the net hierarchy-wide.

**`+48V_SW` deliberately does not appear on any `drive_*` sheet or on `protect`.** The only
48 V-domain net that crosses into a drive sheet is `/VBANK`, and it does so through the harness
connector and the pass FET. If `+48V_SW` ever appears on a drive sheet or on `protect`, that is a
design error, not a routing convenience - it would be a path that could energise something ahead of
the charge FET.

### 1.2 Root-crossed signals - `/NAME`  **[REV B]**

| Net | Direction | Notes |
|---|---|---|
| `/ENABLE` | conn -> charge, all four drive, protect | Active HIGH. **100 k pull-down on `conn`** (ICD s8.2, mandatory). Gates the charge path's EN, **all four** pass-FET gate clamps, and the active bleed's disarm. **Never latched locally** |
| `/FAULT` | protect -> conn | **Open drain, active low.** No pull-up on this board - the carrier's 10 k owns it. **Never driven high.** With four stages it is a single wire-OR: **which** colour faulted is read over I2C, not from this pin |
| `/PWM0` | conn -> drive_w | **FLASH_GATE_W.** 5-200 ms one-shot at 1-25 Hz. LEDC timer 0 or GPIO/RMT - `blocks.md` s4.3 |
| `/PWM1` | conn -> drive_r | **FLASH_GATE_R.** As above. **[REV B] This pin carried `BANK_ARM` in rev A; `BANK_ARM` has moved to I2C** (`blocks.md` s4.4) |
| `/PWM2` | conn -> drive_g | **FLASH_GATE_G** |
| `/PWM3` | conn -> drive_b | **FLASH_GATE_B** |
| `/PWM4` | conn -> drive_w | **AMP_SET_W.** 13-bit at 9.766 kHz, LEDC timer 1, RC-filtered into the regulator reference |
| `/PWM5` | conn -> drive_r | **AMP_SET_R** |
| `/PWM6` | conn -> drive_g | **AMP_SET_G** |
| `/PWM7` | conn -> drive_b | **AMP_SET_B** |
| `/ADC0` | conn (local) | Bank voltage telemetry, from `/VBANK_SENSE` through an RC at the pin. Rth 9.43 k, inside the ICD's 10 kohm. **Also the open-string self-test channel** (`blocks.md` s4.5) |
| `/ADC1` | protect -> conn | LED-module thermistor telemetry, independent `+3V3`-referenced leg |
| `/ID_ADC` | conn (local) | Board-type ID, **bottom leg only** - the carrier fits the 10 k top leg. **Placeholder value; the code is allocated by the carrier owner and must be confirmed before P8** |
| `/I2C_SCL`, `/I2C_SDA` | protect <-> conn | **Two devices: TMP112 and the I/O expander.** 400 kHz. **No pull-ups on this board** - the carrier's 4.7 k own the bus. Addresses must not collide; both selectable at P3 |
| `/VBANK` | charge -> all four drive, protect | Bank positive. **57 V, up to 10.4 A** with four colours firing. **Must be poured, not routed** |
| `/VBANK_SENSE` | charge -> conn, protect | Divided bank voltage (2 x 82 k + 10 k). Three consumers: `ADC0`, the UVLO and ceiling comparators, and **all four** Vds comparators' reference leg |
| `/VDS_SENSE_W`, `_R`, `_G`, `_B` | drive_* -> protect | Divided pass-FET drain voltage, one per colour (2 x 82 k + 10 k each, identical ratio to the bank divider so each trip is ratiometric) |
| `/LED_K_W`, `_R`, `_G`, `_B` | drive_* -> protect | Pass-FET drain = string cathode, one per colour. **57 V, 2.6 A each.** They cross to `protect` only because `J200` lives there (s0); the thermal pour for each belongs to its own drive sheet's FET |
| `/OT_TRIP` | protect -> all four drive, conn | Wire-OR of **seven** open-collector outputs (board OT, LED OT, 4x Vds fault, spare). Pulls **all four** gate clamps **and** `FAULT` |
| `/UVLO_n` | protect -> all four drive | Bank undervoltage lockout. Inhibits the drive stages only - it must **not** assert `FAULT` (an empty bank at power-up is not a fault) |
| `/CHG_EN_n` | protect -> charge | Bank-ceiling comparator output, pulls the hot-swap controller's `EN` low above the ceiling |

**Deleted from rev A:** `/VDS_SENSE` (unqualified) and `/drive/LED_K` - both are replaced by the
four colour-qualified nets above. **`BANK_ARM` no longer exists as a root-crossed net at all**: it
is `/protect/BANK_ARM_n`, an expander output that never leaves the `protect` sheet.

### 1.3 Sheet-internal nets that `constraints.json` names

| Net | Sheet | Why it is declared |
|---|---|---|
| `/charge/CHG_GATE` | charge | **64 V - the highest-voltage net on the board** (V_GATE-OUT is 12-16 V above VCC). Declared in `voltages` so the clearance rule covers it |
| `/drive_w/LED_K`, `/drive_r/LED_K`, `/drive_g/LED_K`, `/drive_b/LED_K` | drive_* | **[REV B]** Pass-FET drain = string cathode. **57 V, 2.6 A each**, and the thermal-pour net for that colour's FET. **Four independent 48 V-domain pours that also need 0.635 mm from each other** |
| `/drive_w/ISNS`, `/drive_r/ISNS`, `/drive_g/ISNS`, `/drive_b/ISNS` | drive_* | Pass-FET source to shunt high side. **2.6 A each**, but low-voltage nodes - deliberately **not** in `voltages`, so `check_creepage` treats them as 0 V and demands the full clearance from the matching `LED_K` across the FET |
| `/protect/BANK_ARM_n` | protect | **[REV B]** I2C expander output -> bank-ceiling comparator. Active LOW to arm; 100 k to `+12V` through a 2N7002 holds it disarmed with `+3V3` dead. Never leaves the sheet, so it is not in `constraints.json` |

### 1.4 A merge decision worth recording

**`research/power.json` declares `/VBANK` and `/LED_A` as separate power constraint entries. They
are one net here, `/VBANK`.** Nothing sits between the bank's positive terminal and the harness
connector's pin 1 - no fuse, no series element - so `/LED_A` would be an alias, and a declared net
that does not exist in the netlist makes `check_creepage` hard-error at P8. **`/LED_A` is deleted,
not renamed.** `/LED_K` survives - **[REV B] as four nets, `/drive_w/LED_K` .. `/drive_b/LED_K`** -
because there genuinely is a device (a string) between each of them and `/VBANK`.

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
| `TP1`-`TP6` | test points: `+48V_SW`, `/VBANK`, `GND`, `/OT_TRIP`, `/UVLO_n`, `/ENABLE` | **every one carries the floating-PoE silkscreen warning.** **[REV B]** the per-colour `ISNS` probe points are now `TP<N+0>` on each drive sheet, so the shared `/drive/ISNS` test point is gone |

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

### 2.3 `drive_w` / `drive_r` / `drive_g` / `drive_b` - ONE TEMPLATE, FOUR INSTANCES  **[REV B]**

**All four sheets are generated from a single parameterised routine at P4.** The only inputs are
the colour suffix, the refdes base and the two PWM pins. Nothing else differs - not a value, not a
part, not a footprint.

| sheet | suffix | refdes base `N` | `pwr_base` | gate pin | amplitude pin |
|---|---|---|---|---|---|
| `drive_w` | `W` | **200** | 300 | `/PWM0` | `/PWM4` |
| `drive_r` | `R` | **250** | 400 | `/PWM1` | `/PWM5` |
| `drive_g` | `G` | **300** | 500 | `/PWM2` | `/PWM6` |
| `drive_b` | `B` | **350** | 600 | `/PWM3` | `/PWM7` |

| Refdes | Part | Note |
|---|---|---|
| `Q<N+0>` | Pass FET, D2PAK planar HEXFET-5, 200 V / 18 A, IRF640N class | Tab = drain = `/drive_x/LED_K`. **>= 350 mm2 F.Cu pour + >= 350 mm2 B.Cu mirror + >= 12 thermal vias** - `power_tree.md` s5 |
| `R<N+0>` | Shunt, 200 mohm 3 W 2512 1 % | 520 mV FS. **Kelvin layout** - sense traces to the pad ends |
| `U<N+0>` | Dual op-amp, LM2904 class, SOIC-8, **on `+12V`** | A = error amp / gate driver; B = setpoint buffer, free. **-40..+125 C grade is mandatory** |
| `U<N+1>` | SPDT analogue switch, SGM3157 class, SC-70-6 | Steers the **reference**, not the gate. **[REV B] P3 must confirm a +125 C part number or substitute** - the stock SGM3157 is -40..+85 C and `power_tree.md` s10.5 puts the air at up to 90 C |
| `R<N+1>`, `R<N+2>`, `C<N+0>` | Setpoint RC + divider: 10 k + 100 nF, 5k36/1k00 (6.35:1) | tau 1 ms, 4.6 ms to 1 %, 2.6 % ripple at 9.766 kHz |
| `R<N+3>` | Gate pull-down 4k7 | **The interlock of record** - off with *everything* dead |
| `R<N+4>` | Gate series | |
| `Q<N+1>`, `Q<N+2>` | 2 x 2N7002 (JLC **Basic**) | One inverts ENABLE, one clamps gate-to-source. Also the landing point for `/OT_TRIP` and `/UVLO_n` |
| `D<N+0>` | Drain-source TVS, SMBJ58A class | Harness `L di/dt` clamp. **NOT a freewheel diode across the string** |
| `R<N+5>`, `R<N+6>`, `R<N+7>` | Vds divider, 2 x 82 k + 10 k, 0805 | Identical ratio to the bank divider, so the fault trip is ratiometric |
| `C<N+1>` | `+12V` decoupling, 100 nF | |
| `TP<N+0>`, `TP<N+1>` | shunt Kelvin probe point, gate | short-return probe point at the shunt - a standard ground lead cannot measure this edge |

Instantiated: **`Q200`/`Q250`/`Q300`/`Q350`** are the four pass FETs; `R200`/`R250`/`R300`/`R350`
the four shunts; and so on. ~18 components per sheet, 72 across the four.

### 2.4 `protect` - refdes 400-499, `pwr_base` 700  **[REV B]**

| Refdes | Part | Note |
|---|---|---|
| `U400` | **Quad** comparator, LM2901 class, SOIC-14, **on `+12V`** | A = board OT, B = LED-module OT, C = bank UVLO, D = bank ceiling. **LM2901 (-40..+125 C), NOT LM339/LM393 (0..+70 C)** |
| `U401` | **Quad** comparator, LM2901 class, SOIC-14, **on `+12V`** | A-D = **the four per-colour Vds fault detectors**, each latched |
| `RT400`-`RT404` | 5 x NTC 10 k 0603 | **One in each of the five power-FET drain pours** (four pass + charge). **All five in parallel as one divider bottom leg** - the hottest device dominates, so a single comparator section ORs all of them. Sheet-owned here because they form one divider; **placement puts each inside a different pour** (`constraints.json` groups) |
| `R400`-`R409` | OT dividers and ratiometric references from `+12V` | supply-independent trip |
| `R410`-`R425`, `C400`-`C403` | **4 x** Vds threshold (~0.45) + arming RC (10 k + 10 nF = 100 us blank) | one set per colour |
| `Q400`-`Q403` | **4 x** 2N7002 fault latch | **Cleared only by `ENABLE` going low** - fault latches, not ENABLE latches. Each latch state also goes to `U420` bits 0-3 |
| `R430`-`R433` | Bank UVLO and ceiling thresholds, hysteresis | UVLO trip = `max(V_string) + 1.7 V` over all four colours, **set by one 1 % resistor at P3 from the measured strings** |
| `U410` | TMP112 class, SOT-563, **on `+3V3`** | I2C telemetry. **Fit no pull-ups** |
| `U420` | **I2C 8-bit I/O expander**, PCF8574 / TCA9534 class, **on `+3V3`** | **[REV B]** bits 0-3 = four fault latch states, 4 = board OT, 5 = LED OT, **6 = `/protect/BANK_ARM_n` (output)**, 7 = spare. **Fit no pull-ups.** Address must not collide with `U410` |
| `Q410`, `R434`, `R435` | `BANK_ARM_n` fail-safe stage: 2N7002 + 100 k to `+12V` + gate series | **[REV B]** With `+3V3` dead, the expander output floats, the 2N7002 is off, and 100 k to `+12V` holds the ceiling comparator **disarmed**. Fail-safe to the lower-energy state |
| `J200` | **Harness, JST VH 6-pin THT, 10 A / 250 V per contact** | **[REV B] moved here from `drive`.** 2 x `/VBANK` anode (10.4 A total) + 4 x `/drive_*/LED_K` cathode (2.6 A each). **Top edge.** Pinout fixed by `light-engine-spec.md` LE-12. **P3 must confirm a +105/+125 C housing** or record a derating exception (`power_tree.md` s10.5) |
| `J300` | 4-way internal landing for the two off-board thermistors | LED-module NTC (trip, `+12V`) and LED-module NTC (telemetry, `+3V3`). **JLC stocks no leaded/probe NTC at all** - these are hand-terminated, not a PCBA line |
| `R440`, `R441` | LED-module NTC divider, **NTC as the TOP leg** | an open harness wire pulls the node low and **trips** - fail-safe on a broken wire |
| `C410`-`C413` | Decoupling for `U400`, `U401` (`+12V`), `U410`, `U420` (`+3V3`) | |
| `TP400`, `TP401` | `/OT_TRIP`, `/UVLO_n` | |

---

## 3. What P4 must review before generating  **[REV B]**

Six items that are invisible on the bench and expensive at P8:

1. **The 48 V domain boundary.** No component may bridge `+12V` or `+3V3` to `+48V_SW`, `/VBANK` or
   **any** `/drive_*/LED_K` (ICD s8.3 point 2). The only nets crossing are `ENABLE`/`PWM` into
   GND-referenced inputs and the **five** divider taps, which run **out** of the 48 V domain into
   high-impedance inputs. Violating this re-creates the 802.3 port-capacitance problem behind the
   compliance switch's back and shows up only as a PD compliance failure.
2. **`FAULT` has no pull-up on this board and is never driven by a push-pull output.** Every device
   touching it is open collector or open drain.
3. **No I2C pull-ups**, on either device. The carrier's 4.7 k own the bus.
4. **[REV B] The four drive sheets must be byte-identical apart from suffix, refdes base and the
   two PWM pins.** Generate them from one routine and diff them. A hand-edited divergence in one
   colour is the classic source of an intermittent single-channel fault that only appears on the
   bench.
5. **[REV B] `U420` bit 6 is an OUTPUT and everything else on the expander is an INPUT.** A
   PCF8574's quasi-bidirectional I/O powers up **high** on every pin; the design depends on that
   being the *disarmed* state, which is why the signal is `BANK_ARM_n` and not `BANK_ARM`. Getting
   the polarity backwards means the bank charges to 48 V whenever firmware is not looking.
6. **[REV B] `/VBANK` must be a pour, not a net the router is free to trace.** 10.4 A. Flag it to
   P6/P7 explicitly - `check_current` will fail a routed trace and the rework loop is expensive.
