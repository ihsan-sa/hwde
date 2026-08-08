# lumina-par (LUM-PAR-A) - hierarchical sheet plan

Five sheets under a root that contains nothing but the sheet symbols and the
inter-sheet wiring. Interface nets become hierarchical pins at P4 and placement
groups at P6.

**Net-naming contract (binding on P4).** KiCad names a net from a hierarchical
label alone as `/<sheet>/<LABEL>`. To produce the canonical names below, **P4 must
place a root-sheet local label on every inter-sheet wire**, spelled exactly as in
s2. `constraints.json` uses these names and P5-P8 will silently no-op on any net
whose name does not match. Power nets are bare global symbols (`+3V3`, `+12V`,
`+48V_SW`, `GND`); every other inter-sheet net carries a leading `/`.

---

## 1. Sheets, refdes ranges and contents

Refdes are unique across sheets by construction: each sheet owns a hundreds block
for every prefix, and each sheet has its own `#PWR` base.

| Sheet | Blocks | Refdes block | `#PWR` base |
|---|---|---|---|
| `power` | B1 - rail entry, bulk, branch-B front end (DNP), test points, H5 | **100-199** | **100** |
| `control` | B2 - ENABLE gating and fail-safe logic; B5 - ID and calibration | **200-299** | **200** |
| `drivers` | B3 - the four constant-current channels and their shunt FETs | **300-399** | **300** |
| `thermal` | B4 - NTC dividers, window comparator, FAULT driver | **400-499** | **400** |
| `led_if` | B6 - LED harness header, TVS clamps, thermocouple pads | **500-599** | **500** |

**Exception: J3, J4 and H5 keep the refdes the ICD assigns them** (ICD s7.2 / s7.5
name them J3, J4 and H5, and the carrier's placement tables refer to them by those
names). They are exempt from the hundreds blocks. J5 is this board's own harness
header and follows the same connector sequence.

### 1.1 `power` (100-199, `#PWR` 100)

| Ref | Part | Note |
|---|---|---|
| **J3** | CONNFLY DS1023-2*7SF11, 2x7 socket | **reverse-mounted, bottom side, facing down** (ICD s7.3). Pin 1 silkscreened with a triangle |
| **H5** | MountingHole_3.2mm_M3 | (46, 74), ICD s7.5. Not a `board_init` hole - added here so it carries a refdes |
| C101, C102 | 22 uF / 25 V X7R | `+12V` bulk |
| C103, C104 | 10 uF / 16 V X7R | `+3V3` bulk |
| C105 | 100 nF | `+3V3` HF |
| TP101-TP103 | test pads | `+12V`, `+3V3`, `+48V_SW`. **TP103 carries the ICD s9 bench-hazard silkscreen** |
| **Q101, Q102, R101-R104, C106-C108** | **branch-B front end - DNP on branch A** | 100 V P-FET hot-swap, Cgd dV/dt network, gate pull-down N-FET from `/EN_OK`, 100 k **0805** bleed, 2x 10 uF/100 V bulk. R104 is 0805 now so branch B needs no footprint change (ICD s5.4) |

### 1.2 `control` (200-299, `#PWR` 200)

| Ref | Part | Note |
|---|---|---|
| **J4** | CONNFLY DS1023-2*12SF11, 2x12 socket | reverse-mounted, bottom side, facing down |
| U201 | SN74LVC1G08 (SOT-23-5) | `/EN_OK = ENABLE AND FAULT` |
| U202 | 74LVC00A quad NAND (SO-14) | `/SHUNTn = NOT(PWMn AND /EN_OK)` - one package covers all four channels |
| U203 | 24C32-class I2C EEPROM | **address 0x50**, WP to GND. **No I2C pull-ups on this board** |
| R201 | 100 k | **ENABLE pull-down at the connector end, before any series element** (ICD s8.2) |
| R202-R205 | 4x 100 k | PWM0-3 pull-downs at J4 - an undriven carrier must not float a gate input high |
| R206 | **VALUE TBD** | `ID_ADC` bottom leg. **Allocated by the carrier owner, not chosen here** (ICD s3.3). P4 blocker - `decisions.md` OPEN-2 |
| R207 | 100 k | local `FAULT` pull-up to `+3V3`, so the node is defined when unmated |
| R208, R209 | 0 R / 10 k | EEPROM A0-A2 and WP strapping |
| R214-R217 | 4x 0 R | `/EN_OK -> /DRV_ENn` links, **fitted by default** |
| **U204, R210-R213, C210-C213, D201-D204** | **converter-idle one-shot - DNP option** | 74LVC14 hex Schmitt + retriggerable RC + diode per channel. Populate to save ~0.8 W at saturated colours (`power_tree.md` s2); if populated, remove R214-R217 |
| C201-C205 | decoupling + `ID_ADC` 100 nF | |

### 1.3 `drivers` (300-399, `#PWR` 300)

Four identical channels; channel `n` is based at `300 + 20n`. Channel 0 shown;
channels 1-3 are U321/U341/U361 and so on.

| Ref | Part | Note |
|---|---|---|
| U301 | TPS92515HVDGQR class (MSOP-10-EP) | 5.5-65 V, 2 A internal FET, shunt-PWM capable. Exposed pad on a >= 9-via array |
| L301 | 47 uH shielded | sized for **ripple, not slew** - 90 mA (30 %) at ~700 kHz |
| D301 | **60 V** Schottky, 1 A | branch A. Low Vf matters: it dominates the 0.20 W idle loss. Branch B needs a 100 V part |
| R301 | sense resistor | sets 300 mA (af, branch A). **The at upgrade is this value** |
| Q301 | 60 V logic-level N-FET | shunt across the string. **60 V now, not 30 V**, so the branch-B / `at` 8S string (27.2 V) needs no change |
| R302 | 150 R | shunt gate series - bounds the 74LVC00 output to 22 mA, ~30 ns edges |
| R303 | 100 k | shunt gate pull-down - an unpowered gate IC must not leave a FET half-on |
| C301 | 4.7 uF / 25 V | VIN local (100 V on branch B) |
| C302 | 100 nF | VIN HF, at the pin |
| C303, R304 | **DNP** | SW-node RC snubber footprint |

**There is no output capacitor across any LED string** - a shunt FET dumps it
every PWM cycle (`blocks.md` B3 rule 1). Do not let a reviewer add one.

### 1.4 `thermal` (400-499, `#PWR` 400)

| Ref | Part | Note |
|---|---|---|
| U401 | quad open-drain comparator, LMV339 / TLV3704 class | rail-to-rail input, <= 50 uA/channel. **Open-drain outputs are mandatory** - they wire-OR onto `FAULT`, which must never be driven high |
| RT401 | 10 k B3950 NTC, 0603 | **on the copper of the hottest driver stage, outside the DC-DC hot zone (2,46)-(36,68)** |
| R401, R403 | 2x 10 k | NTC divider top legs (board, module) |
| R402, R404 | <= 1 k | ADC series - keeps total source impedance <= 6 kohm against the ICD's 10 kohm |
| R405-R412 | reference ladder + hysteresis | ratiometric off `+3V3`, so thresholds track the carrier's ADC reference |
| C401-C403 | decoupling + NTC filter | filter caps sized so R402/R404 x C stays a slow-signal filter, not a pulse filter |

Four comparator channels: **emitter hot (90 C, release 75 C) / emitter open /
emitter short / board hot (110 C, release 95 C)**. The window (open + short)
converts the most likely fault in an off-board module - a broken harness wire,
which reads as *cold* in either divider orientation - from fail-dangerous to
fail-safe (D-T17, E-10).

> **P8 SPICE AMENDMENT 2026-08-08 - the fault window has THREE functionally
> distinct channels, not four.** An independent SPICE bench (which reproduced
> the hand MNA solve to within 0.4 K on every channel) measured **CMP3
> (emitter short) as functionally redundant with CMP1**: its tap sits at
> 0.311 V, BELOW CMP1's 0.427 V, and both detect "sense node low", so CMP1
> always asserts `/FAULT` first. CMP3 measured a degenerate **1.1 mV band** and
> can never define a `/FAULT` edge. This is a leftover from the inverted-
> orientation spec that the blocks.md B4 amendment already corrected.
> It is harmless and free - worth keeping as redundancy against a single
> comparator failing - but **no document should claim four independent fault
> detectors.** Measured trip/release: emitter hot 89.67/81.26 C (+8.41 K),
> emitter open -22.30/-3.82 C (+18.47 K), board hot 109.80/92.90 C (+16.90 K).

### 1.5 `led_if` (500-599, `#PWR` 500)

| Ref | Part | Note |
|---|---|---|
| J5 | 10-way latched wire-to-board, 2.0 mm (JST PH class) | 4 anode + 4 per-channel GND return + `/NTC_LED` + dedicated NTC sense return |
| D501-D504 | TVS, SOD-123 | **15 V standoff on branch A, 33 V on branch B** - same footprint, a BOM value change |
| TP501, TP502 | bare-copper thermocouple pads | bring-up thermal verification (L-13). ICD s9 bench-hazard silkscreen |

**No 48 V net reaches this sheet, ever** (D-T13). That is what keeps the 0.635 mm
clearance rule, the 100 V capacitor rule and the 0805-minimum resistor rule off
the harness and the module.

---

## 2. Interface nets - canonical names

These are the names the schematic **must** produce. `constraints.json` and every
P5-P8 check key off them.

| Net | Type | From -> to | Note |
|---|---|---|---|
| `+48V_SW` | power | `power` (J3 1/3/5) | **landed, not tapped** on branch A. Declared in `voltages` at 57 V so `check_creepage` enforces the clearance |
| `+12V` | power | `power` -> `drivers` | 0.717 A max (`power_tree.md` s3, revision B) |
| `+3V3` | power | `power` -> `control`, `thermal` | <= 5 mA |
| `GND` | power | everywhere | In1 plane |
| `/PWM0` .. `/PWM3` | in | `control` (J4) internal | 3.3 V CMOS. **No RC filter; if any network, tau <= 14 ns** |
| `/ENABLE` | in | `control` (J4) internal | 100 k pull-down here |
| `/FAULT` | bidir, open drain | `thermal` -> `control` -> J4 | **never driven high**; wire-OR'd with the carrier eFuse fault |
| `/EN_OK` | internal | `control` -> `power` (branch-B gate) | `ENABLE AND FAULT` |
| `/DRV_EN0` .. `/DRV_EN3` | out | `control` -> `drivers` | driver PWM/EN pins. Tied to `/EN_OK` through 0 R by default; driven by the one-shot if populated |
| `/SHUNT0` .. `/SHUNT3` | out | `control` -> `drivers` | shunt-FET gates. `NOT(PWMn AND /EN_OK)` |
| `/LED0_A` .. `/LED3_A` | out | `drivers` -> `led_if` | channel anodes, 0.30 A each |
| `/NTC_LED` | in | `led_if` -> `thermal` | module NTC divider node |
| `/NTC_BRD` | internal | `thermal` | board NTC divider node |
| `/ADC0` | out | `thermal` -> `control` -> J4 | emitter temperature to the carrier. Source impedance <= 6 kohm |
| `/ADC1` | out | `thermal` -> `control` -> J4 | board temperature to the carrier |
| `/ID_ADC` | out | `control` -> J4 | divider bottom leg; value allocated by the carrier owner |
| `/I2C_SCL`, `/I2C_SDA` | bidir | `control` (J4) -> U203 | **no daughter-side pull-ups** |

**Unused ICD signals**, landed on J4 and left unconnected on this board:
`PWM4..PWM7` (no fifth channel on rev A), `DSPI_SCK/MOSI/MISO/CSn` (a 4-channel
PWM design needs no serial device beyond the EEPROM, and `decisions.md` D2 rejects
a local PWM generator). Leave them as no-connects with an explicit `~` ERC
directive so P4's ERC does not flag them and so a reviewer can see the decision.

**I2C address map** (this board owns the whole space; the carrier reserves
nothing): **0x50 = 24C32 EEPROM; 0x51-0x57 reserved for its own address pins;
nothing else on the bus.** The comparator and both NTCs are analogue.

---

## 3. Placement groups for P6

Declared in `constraints.json` under `placement.groups`. Each buck channel is one
tight cluster; the loop that matters is `+12V` -> C301 -> U301 -> L301 -> D301.

| Group | Anchor | Members |
|---|---|---|
| `ch0` | U301 | L301, D301, R301, R302, R303, C301, C302, Q301 |
| `ch1` | U321 | L321, D321, R321, R322, R323, C321, C322, Q321 |
| `ch2` | U341 | L341, D341, R341, R342, R343, C341, C342, Q341 |
| `ch3` | U361 | L361, D361, R361, R362, R363, C361, C362, Q361 |
| `ntc_brd` | U301 | RT401 - the board NTC must sit **on** the hottest driver stage (T-3) |
| `gate` | U202 | R202-R205, C202 - keep the NAND next to J4's PWM pins to keep the jitter-sensitive run short |
| `analog` | U401 | R401-R412, C401-C403 - **separated from every inductor by >= 10 mm** |

`placement.fixed`: **H5**, positioned by an explicit `place_edit` op at (46, 74)
in board-local coordinates (translated - see `stackup.md` TRAP 2).

`placement.edges`:

| Ref | Edge | pos | Why |
|---|---|---|---|
| J3 | bottom | 0.24 | ICD s7.2 nominal centre x = 24 mm. **Hint only** |
| J4 | bottom | 0.72 | ICD s7.2 nominal centre x = 72 mm. **Hint only** |
| J5 | **top** | 0.56 | x ~ 56 mm - the only clear span of the top edge (the notch occupies x 6-36, the recovery-header keepout x 76-98), and it sits directly above the driver band so the LED anode runs stay short |

**J3 and J4's entries are hints to the annealer, not final positions.** Both must
be placed with explicit `place_edit` ops at the re-issued ICD s7.2 coordinates and
then **locked**, before the annealer runs. Both are **bottom-side, facing down** -
set the side at P4 in the footprint or with a `place_edit` `flip` op, and check
pin 1 in the mated view, not from the footprint (pin numbering mirrors across the
row on a bottom-side part).

---

## 4. Sheet-level P4 notes

1. **The DNP option sets must be in the netlist**, not added later: the branch-B
   front end (`power` Q101/Q102/R101-R104/C106-C108) and the converter-idle
   one-shot (`control` U204/R210-R213/C210-C213/D201-D204). A DNP part still has
   pads, so its clearance and area are accounted for at P6/P7 and the option
   stays a populate change rather than a respin. Mark them `DNP` in the BOM
   variant field so `bom_cpl` at P9 excludes them.
2. **`FAULT` is open drain.** ERC will want a driving pin somewhere; the comparator
   outputs plus R207 are it. Do not let a fix loop add a push-pull driver.
3. **No I2C pull-ups.** Fitting them is an ICD violation, and P4's reflex is to add
   them. Record it on the schematic.
4. **`PWM4..7` and `DSPI_*` are deliberate no-connects.**
5. **R206's value is unknown until the carrier owner allocates it.** Place the part
   with a `TBD` value field and a schematic note; do not guess a value - that is
   exactly the silent divergence ICD-01's preamble forbids.

---

## 5. P4 AMENDMENTS (2026-08-07)

This file was written at P2. The items below were settled during P4 schematic
capture and its adversarial review, and **they supersede the sections above**.
`architecture/p4-wiring-notes.md` remains binding for wiring rules.

### 5.1 s1.2 `control` - new parts

| Ref | Part | Note |
|---|---|---|
| **R218-R221** | 4x **10 k** | `/DRV_EN0..3` fail-safe pull-downs, one per channel, on the `/DRV_ENn` side of the R214-R217 links. **10 k is load-bearing - do NOT "harmonise" these to the board's usual 100 k.** The TPS92515HV enable pin sources up to 25 uA, so 100 k sits at 2.5 V, above the 1.0 V threshold. Without them, every power-up window with `+12V` up and `+3V3` not yet (and any 12 V-only bench bring-up) leaves all four drivers undriven and latching ON - a full-current LED flash, defeating ICD s8.2. Placed with their DRIVER, not with the links. |

`R206` is **4.7 k 1 %** (CR-1), not "VALUE TBD". parts.json is re-issued.

### 5.2 s1.3 `drivers` - new parts and one changed value

The COFF network (C304/R305/R306 per channel, s1.3 had none of it) is joined by
the **BOOT network, which s1.3 also omitted and without which the converter
cannot switch at all**:

| Ref (ch0; +20/channel) | Part | Note |
|---|---|---|
| **C305** | 100 nF | BOOT capacitor at pin 4 - the high-side FET's gate supply |
| **D302** | 1N4148W | BOOT diode, anode on the device's own VCC (pin 2), cathode on BOOT |
| **C306** | 4.7 uF | VCC decoupler at pin 2, datasheet sec 8.3.6 |

**ROFF2 (R306 etc) is 30 k, NOT 47 k.** The original 47 k was sized from TI
Equation 9, which assumes VCC charges COFF through ROFF2 alone - false at
ROFF1 = 10 k. The shunted COFF node then asymptotes **below** the 1.00 V VOFT at
every corner, the off-timer never trips, and shunt-dimming linearity is lost -
the exact Figure-43 failure the network was added to prevent. 30 k is solved
jointly (`dIL_shunt == dIL_normal`); 0 of 243 corners now fail. **Do not
re-derive this from TI's text alone**: Eq 1 and Eq 8 disagree about the
freewheel diode drop and lead to an unsafe ~38 k.

### 5.3 s1.4 `thermal` - range extended, values changed

- Ladder + hysteresis is **R405-R416**, not R405-R412.
- **R402/R404 are 150 R, not "<= 1 k"**, and C402/C403 are **4.7 uF 0805, not
  100 nF 0603** (footprint change) so the filter stays slow at the lower R.
- **R413/R415** (10 k) series-protect the comparator inputs and **D401**
  (1N4148W) clamps the PROTECTED comparator node `/thermal/CMP_LED` to
  `+3V3` - NOT `/NTC_LED` itself. (Corrected at P8 from the netlist, which is
  authoritative: R413 sits between them and limits the clamp current to
  2.03 mA.) The LM339LV inputs are diode-clamped
  to GND **only**, with no clamp to V+, so a series resistor alone does not
  protect them from a harness fault that puts an LED anode (6.8 V nominal,
  16.7-24.4 V at the TVS clamp) onto the sense line.
- Hysteresis is returned to the **protected comparator nodes**, not the sensor
  dividers. See the blocks.md B4 amendment for the solved thresholds.

### 5.4 s2 net table - `/PWM0..3` correction

**The s2 table's `/PWM0`..`/PWM3` spelling is not what the netlist produces.**
Those nets are `control`-internal and come out **`/control/PWM0..3`**;
`constraints.json.high_speed` was re-spelled to match, so all seven high_speed
consumers bind correctly. Promoting them to root-crossing names was tried and
measured: it is electrically correct but raises 4x `label_dangling`, because
such a net reaches the root as wire + label + exactly ONE sheet pin, and buying
the bare name would mean adding four PARTS to the root. `/ENABLE`, `/ID_ADC`,
`/I2C_SCL` and `/I2C_SDA` are in the identical position and are also
`/control/NAME`. No constraint references those four.
