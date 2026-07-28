# LUM-CAR-A - hierarchical sheet plan

Five child sheets under a thin stitching root. ~110 components across five clearly separable
domains, so hierarchy buys parallel P4 sheet generation and keeps the PD front end's 48 V domain
visually and electrically isolated from the logic.

**The sheet NAMES below are contractual.** They appear verbatim in netlist net names
(`/pwr/SW`) and `constraints.json` already references sheet-crossing names; renaming a sheet
renames nets and breaks `netlist_audit --constraints`.

| Sheet | File | Blocks | Interface nets (sheet pins) | pwr_base |
|---|---|---|---|---|
| root `lumina-carrier` | `lumina-carrier.kicad_sch` | none (stitching only) | - | 1 (unused) |
| `poe` | `poe.kicad_sch` | RJ45 PoE magjack, TVS, PD interface, detect/class network, CBULK, T2P level shift, shield hybrid | `ETH_TXP`, `ETH_TXN`, `ETH_RXP`, `ETH_RXN`, `ETH_LED_LINK`, `ETH_LED_ACT`, `T2P` | 100 |
| `eth` | `eth.kicad_sch` | W5500, 25 MHz crystal group, EXRES1/TOCAP/1V2O, MDI TVS array, SPI series R | `ETH_TXP`, `ETH_TXN`, `ETH_RXP`, `ETH_RXN`, `ETH_LED_LINK`, `ETH_LED_ACT`, `ETH_SCLK`, `ETH_MOSI`, `ETH_MISO`, `ETH_CSn`, `ETH_INTn`, `ETH_RSTn` | 200 |
| `pwr` | `pwr.kicad_sch` | 48->12 buck, 12->3.3 buck, 48 V eFuse, bleed, PG/FLT LEDs | `ENABLE`, `FAULT`, `IMON` | 300 |
| `mcu` | `mcu.kicad_sch` | ESP32-S3-WROOM-1-N8, decoupling, EN/BOOT network, recovery header, status LED | everything below | 400 |
| `expansion` | `expansion.kicad_sch` | J3 power connector, J4 signal connector, I2C/FAULT pull-ups, ID divider, ADC/ID clamps, H5 | `PWM0..7`, `DSPI_*`, `I2C_SCL`, `I2C_SDA`, `ADC0`, `ADC1`, `ID_ADC`, `ENABLE`, `FAULT` | 500 |

---

## 1. Net naming - the CANONICAL final netlist names

Mechanism (verified in this repo: `tests/s7_regen/hierdemo/kicad/hierdemo.net`):

1. **Power SYMBOLS make a net global across the whole hierarchy** with a BARE name and need no
   sheet pin.
2. A child net merged with the root through a sheet pin takes the **root-side label**:
   `Project.add_sheet(child, ..., nets=["X"])` wires each sheet pin outward to a root local label
   `X`, so the net becomes `/X`.
3. A child-internal label becomes `/<sheet>/NAME`.

### 1.1 Global rails - power symbols, bare names

| Net | Present on | Driven by | PWR_FLAG? |
|---|---|---|---|
| `GND` | all five | U1 RTN pin (passive) | **yes** |
| `V48_RAW` | poe, pwr | J1 V+ pin (passive) | **yes** |
| `V48_RTN` | poe **only** | J1 V- pin (passive) | **yes** |
| `+48V_SW` | pwr, expansion | U22 OUT | yes (eFuse output is a passive/power-out pin depending on the symbol) |
| `+12V` | pwr, expansion | forms after L20 (passive) | **yes** |
| `+3V3` | pwr, eth, mcu, expansion | forms after L21 (passive) | **yes** |

All six PWR_FLAGs live on the sheet that owns the source (`poe` for `V48_RAW`/`V48_RTN`/`GND`,
`pwr` for the rest), at `#FLG0100+` / `#FLG0300+`. Power symbols being global, one flag each drives
the net hierarchy-wide.

**`V48_RTN` is deliberately confined to the `poe` sheet.** It is the raw PoE negative, upstream of
the hot-swap FET, and sits up to 57 V *below* board GND. Nothing outside the PD front end may touch
it. If it ever appears on another sheet, that is a design error, not a routing convenience.

**`V48_RAW` replaces both `VPOE` and `+48V` from `research/power.json`.** The PD interface switches
the *return*, not the positive rail, so there is only one positive 48 V node upstream of the eFuse.
`V48_SW` from `research/interface-poe-48v.json` is renamed **`+48V_SW`** for consistency with the
other rails.

### 1.2 Root-crossed signals - `/NAME`

These are the names `constraints.json` uses, and they are contractual.

| Final net | Exposed by | Members |
|---|---|---|
| **`/ETH_TXP`** | poe + eth | J1 TD+, U10 TXP (pin 2), D10 | 
| **`/ETH_TXN`** | poe + eth | J1 TD-, U10 TXN (pin 1), D10 |
| **`/ETH_RXP`** | poe + eth | J1 RD+, U10 RXP (pin 6), D10 |
| **`/ETH_RXN`** | poe + eth | J1 RD-, U10 RXN (pin 5), D10 |
| `/ETH_LED_LINK` | poe + eth | J1 LED cathode, U10 LINKLED (active low) via R7 |
| `/ETH_LED_ACT` | poe + eth | J1 LED cathode, U10 ACTLED (active low) via R8 |
| `/T2P` | poe + mcu | U1 T2P through its level-shift network, U30 GPIO47 |
| **`/ETH_SCLK`** | eth + mcu | U10 SCLK (pin 29), R31, U30 GPIO12 |
| `/ETH_MOSI` | eth + mcu | U10 MOSI (pin 28), R32, U30 GPIO11 |
| `/ETH_MISO` | eth + mcu | U10 MISO (pin 27), U30 GPIO13 |
| `/ETH_CSn` | eth + mcu | U10 SCSn (pin 32), R33 pull-up, U30 GPIO10 |
| `/ETH_INTn` | eth + mcu | U10 INTn (pin 33), U30 GPIO14 |
| `/ETH_RSTn` | eth + mcu | U10 RSTn (pin 37), R34 pull-up, U30 GPIO21 |
| `/ENABLE` | pwr + mcu + expansion | U22 SHDN, R69 10k pull-down, J4 pin 23, U30 GPIO36 |
| `/FAULT` | pwr + mcu + expansion | U22 FLT (open drain), J4 pin 24, R132 10k pull-up, U30 GPIO37 |
| `/IMON` | pwr + mcu | U22 IMON, R68, U30 GPIO8 |
| `/PWM0` .. `/PWM7` | mcu + expansion | U30 GPIO4/5/6/7/15/16/35/38, J4 pins 1/2/5/6/7/8/11/12 |
| `/DSPI_SCK` `/DSPI_MOSI` `/DSPI_MISO` `/DSPI_CSn` | mcu + expansion | U30 GPIO39/40/41/42, J4 pins 14/15/16/17 |
| `/I2C_SCL` `/I2C_SDA` | mcu + expansion | U30 GPIO17/18, R130/R131 4k7 pull-ups, J4 pins 18/19 |
| `/ADC0` `/ADC1` | mcu + expansion | U30 GPIO1/2 via R136/R137 + D41/D42 clamps, J4 pins 20/21 |
| `/ID_ADC` | mcu + expansion | U30 GPIO9 via R135 + D40 clamp, R134 divider top, J4 pin 22 |

The five names in **bold** appear in `constraints.json` (`high_speed`, `diff_pairs`). Their sheet
routing is therefore contractual: **any change that stops one of them crossing the root renames it
and breaks the constraint file**, and `check_return_path` raises `CheckError` -> exit 2 on a
`high_speed` net that is not on the board.

### 1.3 Sheet-internal signals - `/<sheet>/NAME`

| Sheet | Final net | Members |
|---|---|---|
| poe | `/poe/DEN_TAP` | R1/R2 junction, brought to a test pad - grounding it disables the PD |
| poe | `/poe/CLS` | U1 CLS pin, R3 (the D-01 lever) |
| poe | `/poe/CDB` | U1 CDB (converter disable, RTN-referenced) -> U20 EN |
| poe | `/poe/SHIELD` | J1 shield tabs, R6 1M, C3 1nF/2kV hybrid to GND |
| eth | `/eth/XI`, `/eth/XO` | Y10, C30, C31, U10 pins 30/31 |
| eth | `/eth/EXRES` | U10 pin 10, R30 12.4k 1 % |
| eth | `/eth/1V2O`, `/eth/TOCAP` | U10 pins 22/20 with C33 / C32 |
| pwr | `/pwr/SW` | U20 SW, L20 pin 1, D20 cathode, C54 low side |
| pwr | `/pwr/BST` | U20 BST, C54 high side |
| pwr | `/pwr/FB48` | R60/R61 junction -> U20 FB |
| pwr | `/pwr/SW33` | U21 SW, L21 pin 1 |
| pwr | `/pwr/FB33` | R63/R64 junction -> U21 FB |
| pwr | `/pwr/PGOOD` | U22 PGOOD -> D21 power-good LED via R71 (**no GPIO** - see mcu s4) |
| mcu | `/mcu/EN` | U30 EN pad, R100 10k to +3V3, C85 1uF, J2 pin 5 |
| mcu | `/mcu/BOOT` | U30 GPIO0, R101 10k to +3V3, SW1, J2 pin 6 |
| mcu | `/mcu/TXD0`, `/mcu/RXD0` | U30 GPIO43/44, J2 pins 3/4 |
| mcu | `/mcu/STATUS` | U30 GPIO48 -> R102 -> D30 |

---

## 2. Refdes allocation - unique ACROSS sheets, contractual for P4

`constraints.json` references `U20` (thermal), `J1`/`U30`/`J3`/`J4`/`H5` (edges),
`U20`/`L20`/`D20`/`U21`/`L21`/`U10`/`Y10`/`J1` (separation), and five group anchors. **Renumbering
any of those without editing `constraints.json` silently drops the constraint** - `place_anneal`
skips separation refs that are not on the board, and it does so without an error.

| Sheet | U | J / H | R | C | D | L | Y | SW | pwr_base |
|---|---|---|---|---|---|---|---|---|---|
| `poe` | U1-U9 | J1 | R1-R19 | C1-C19 | D1-D9 | - | - | - | 100 |
| `eth` | U10-U19 | - | R30-R59 | C30-C49 | D10-D19 | - | Y10 | - | 200 |
| `pwr` | U20-U29 | - | R60-R99 | C50-C79 | D20-D29 | L20-L29 | - | - | 300 |
| `mcu` | U30-U39 | J2 | R100-R129 | C80-C119 | D30-D39 | - | - | SW1 | 400 |
| `expansion` | U40-U49 | J3, J4, H5 | R130-R159 | C120-C139 | D40-D49 | - | - | - | 500 |

### 2.1 `poe` sheet

| Ref | Part class | Note |
|---|---|---|
| J1 | RJ45 PoE magjack, THT right-angle shielded, integrated magnetics **and integrated bridge** | HanRun HY931147C class. **P3 must confirm from the datasheet that BOTH the data-pair centre taps and the spare pairs feed the internal rectifier** - a Mode-A-only or Mode-B-only jack is not 802.3 compliant. See `decisions.md` OPEN-B |
| U1 | 802.3at Type 2 PD interface, SO-8-EP | TPS2378 class. **Pin 8 stays unconnected** so the TPS2379 second source drops into the same footprint |
| D1 | 58 V unidirectional TVS, SMB, 600 W | across `V48_RAW`/`V48_RTN`, physically first |
| C1 | 0.1 uF / 100 V X7R | VDD-VSS bypass; the standard's 50-120 nF window |
| C2, C4 | 22 uF / 100 V ceramic (x2 = 44 uF CBULK) | >= 5 uF for AC MPS, << 180 uF port ceiling |
| R1, R2 | 12.4 k 1 %, **0805 or larger** | split RDEN = 24.9 k with the tap out at `/poe/DEN_TAP` |
| R3 | **90.9 ohm 1 % (af) -> 63.4 ohm 1 % (at)**, 0603 | **THE D-01 LEVER.** Standalone, clearly silkscreened pad pair, no neighbours in the same silk box |
| R4, R5 | T2P level-shift network | T2P is RTN-referenced and reaches 57 V when high-Z - never a bare GPIO connection |
| R6, C3 | 1 Mohm + 1 nF / 2 kV | shield hybrid, with a fitted-by-default 0 ohm alternate footprint |
| R7, R8 | magjack LED series resistors | W5500 LED outputs are active-low, IOL >= 8.6 mA. **Confirm the jack's LED polarity at P3** |

### 2.2 `eth` sheet

| Ref | Part class | Note |
|---|---|---|
| U10 | W5500, LQFP-48 | RSVD pin 23 to GND; pins 38-42 NC; VBG (18) NC; DNC (7) NC; PMODE[2:0] NC |
| Y10 | 25 MHz, **CL 18 pF**, AT-cut fundamental, SMD3225-4P | select on the **total** ppm budget (initial + temp + ageing) staying under +/-50 ppm, not on the +/-30 ppm initial alone |
| C30, C31 | **27 pF C0G** | `C = 2 x (CL - Cstray)`, Cstray ~4 pF. **Expect to trim on the first prototype.** Most W5500 module schematics use 22 pF, which back-solves to CL 15 pF - wrong for an 18 pF part |
| R30 | **12.4 k 1 %** | EXRES1 - sets the MDI drive current and therefore the 950-1050 mV output amplitude |
| C32 | 4.7 uF | TOCAP |
| C33 | 10 nF | 1V2O |
| C34-C40 | 100 nF x n + 4.7 uF bulk | VDD/AVDD decoupling |
| D10 | 4-channel low-capacitance TVS array, **<= 1 pF/line** | PHY side of the magnetics, at the J1 end of the pairs. **Fitted, not DNP** |
| R31, R32 | 22-33 ohm series, at the driver pin | `/ETH_SCLK` and `/ETH_MOSI`, placed at U30's end. Footprint fitted so the value can be tuned if EMC bites |
| R33 | 10 k to +3V3 | `/ETH_CSn` pull-up. **Mandatory**: GPIO10 has a 60 us low glitch at power-up and low = W5500 selected |
| R34 | 10 k to +3V3 | `/ETH_RSTn` pull-up (belt and braces - the W5500's own is internal) |

### 2.3 `pwr` sheet

| Ref | Part class | Note |
|---|---|---|
| U20 | 100 V-class buck, 2 A, ESOP-8 | SCT2A25 class. Exposed pad to In1 GND, >= 9 vias. `EN` driven from U1's `/poe/CDB` for correct PoE start-up sequencing with no glue |
| L20 | 68 uH power inductor, Isat >= 3 A | ~7 x 7 mm |
| D20 | 100 V Schottky, SMC | SS510 class. **Dissipates more than U20** - give the cathode >= 100 mm2 of F.Cu |
| C50-C53 | 2.2 uF / 100 V x2 in, 22 uF x2 out | 100 V ceramics; **no aluminium electrolytic on this board** |
| C54 | BST cap | |
| R60, R61 | FB divider for 12 V | |
| U21 | 3 A synchronous buck, 4.5-17 V, SOT-23-THIN-6 | TPS563201 class. **LDO disqualified**: 6.1 W at 0.7 A |
| L21 | 4.7 uH | |
| C55-C58, R63, R64 | in/out caps + FB divider | |
| U22 | 60 V eFuse, HTSSOP-20-EP | TPS16630 class. **MODE open = LATCH OFF.** ILIM set to 1.0 A |
| **R69** | **10 k pull-down on `/ENABLE`** | **THE CAR-REQ-08 FAIL-SAFE.** SHDN's open-circuit voltage is 2.48-3.3 V with a 10 uA source, so an unconnected SHDN floats HIGH and the device powers up ON. Must be called out on the schematic |
| R65-R68, C59 | ILIM, UVLO/OVP divider (**0805 or larger**), IMON scaling, dV/dT | dV/dT sized **fast** - the daughter owns the inrush ramp |
| R70 | **100 k bleed on `+48V_SW`**, 0805 or larger | de-energises the connector pins whenever ENABLE is low |
| D21, R71 | green power-good LED from U22 PGOOD | **hardware-driven, no GPIO** |
| D22, R72 | red fault LED from U22 FLT | **hardware-driven, no GPIO** |

### 2.4 `mcu` sheet

| Ref | Part class | Note |
|---|---|---|
| U30 | **ESP32-S3-WROOM-1-N8** | SKU frozen non-octal-PSRAM and non-R16V (GPIO35-37 and 47/48 are in use). Compatible: -N4, -N8R2, -N16R2 |
| C80-C84 | 22 uF + 3x 100 nF + 1 uF | module supply must sustain a 500 mA Wi-Fi TX burst without browning out |
| J2 | 6-pin 2.54 mm header: GND, +3V3, TXD0, RXD0, EN, BOOT | Q9 default (b). **Inside the enclosure, no panel cutout.** Silkscreen: "PoE OFF or ISOLATED ADAPTER ONLY" |
| R100, C85 | 10 k + 1 uF EN RC | |
| R101, SW1 | 10 k pull-up + optional BOOT tactile | GPIO0 |
| D30, R102 | status LED from GPIO48 | Q11 default: this plus the two magjack LEDs, all visible through the RJ45 cutout |

**Not on this sheet by design:** no USB-C. A non-isolated PD achieves 802.3 compliance by having
**only** the Ethernet connection and no accessible non-isolated conductor. **Q9 option (a) "USB-C on
every fixture" is therefore not available** unless Q5 flips to isolated.

### 2.5 `expansion` sheet

| Ref | Part class | Note |
|---|---|---|
| J3 | 2x7 2.54 mm THT male header, 250 V / 3 A | expansion **POWER**. Pin map: `connector-icd.md` s3 |
| J4 | 2x12 2.54 mm THT male header, 250 V / 3 A | expansion **SIGNAL**. Pin map: `connector-icd.md` s3 |
| H5 | `MountingHole_3.2mm_M3` | CAR-REQ-15 support point between J3 and J4; also a keying feature |
| R130, R131 | 4.7 k I2C pull-ups | carrier-side, per requirements s2.1 |
| R132 | 10 k `/FAULT` pull-up | open-drain net shared with U22's FLT |
| R134 | ID divider top leg to +3V3 | the daughter supplies the bottom leg (CAR-REQ-07 / Q10) |
| R135-R137, D40-D42 | series resistors + 3.3 V clamps on `/ID_ADC`, `/ADC0`, `/ADC1` | **part of the CAR-REQ-14 survivability story, not just ESD hygiene**: a mis-seated daughter can bridge a neighbouring pin onto these |

---

## 3. P4 generator notes (schlib specifics that bite)

1. **Six PWR_FLAGs.** Every rail on this board is driven by a *passive* pin - a connector pin, an
   inductor, an eFuse output. Without flags, ERC reports all six as undriven.
2. **`V48_RTN` needs its own power symbol** and must appear only on `poe`. If schlib has no 48 V
   power symbol, use a generic power symbol with the name set explicitly - do **not** fall back to a
   local label, or the net becomes `/poe/V48_RTN` and `constraints.json.voltages` misses it
   (`netlist_audit` raises `missing_net` at **error** severity).
3. **Use the free-cluster `hier_pin(net, at=...)` variant** for every net in s1.2 - each has 2+
   components on it, and that variant places a local label plus the hierarchical label on one stub
   so the hier label joins by wire geometry rather than by name merging.
4. **Root-side labels sit 7.62 mm left of each sheet pin**, and sheet pins stack down the sheet
   symbol's left edge. Leave that strip clear and give sheets sharing a net the same `nets=` order.
5. **`expect={...}` on U1, U10, U20, U21, U22, U30, J1, J3, J4** - pin-name insurance against a
   wrong symbol on the parts where a wrong pin is a dead board.
6. **Decoupling metadata**: `Project.save(decoupling=...)` must associate C80-C84 with U30's 3V3
   pins, C34-C40 with U10's VDD/AVDD, C50/C51 with U20 VIN, C1 with U1 VDD (rail `V48_RAW`, gnd
   `V48_RTN` - **not** GND; this one needs an explicit `gnd_net` override).
7. **`J2` silkscreen** must carry the non-isolated warning (s2.4).
8. **`R3` silkscreen** must carry `af=90R9 / at=63R4` so the D-01 lever is visible on the bare board.

---

## 4. Interface pinouts (silk-labelled, canonical)

- **J1 magjack** (10 signal + 4 LED positions): TD+/TD-/RD+/RD- to `/ETH_TXP` `/ETH_TXN`
  `/ETH_RXP` `/ETH_RXN`; V+ (P9) -> `V48_RAW`; V- (P10) -> `V48_RTN`; shield tabs -> `/poe/SHIELD`.
  **P3 confirms P7/P8 from the datasheet** - they differ between HY931147C and HR861153C.
- **J2 recovery header** (1x6, 2.54 mm): 1 GND, 2 +3V3, 3 TXD0, 4 RXD0, 5 EN, 6 BOOT.
- **J3 / J4 expansion**: `connector-icd.md` s3. That document is the ICD; this table must never
  disagree with it.

---

## 5. Board-edge placement (mirrors `constraints.json.placement.edges`)

| Ref | Edge | pos | Why |
|---|---|---|---|
| `J1` | **top** | 0.21 | the plug must seat through an enclosure cutout; 58 mm from the antenna, on a different edge |
| `J2` | **top** | 0.87 | recovery header reachable with the lid off, far from the 48 V domain |
| `U30` | **right** | 0.50 | antenna at a board edge, away from the shielded jack, and clear of both right-hand mounting holes |
| `J3` | **bottom** | 0.24 | expansion power, near the eFuse and the DC-DC |
| `H5` | **bottom** | 0.46 | CAR-REQ-15 support point between J3 and J4 |
| `J4` | **bottom** | 0.72 | expansion signal, near the module |

Orientation is **not** specified via `rot`, because it depends on each footprint's native
orientation. Two P6 checks that must be done by looking, not by assuming
(see `LEARNINGS.md` 2026-07-28 "Connector mating direction"):
- **J1's opening must face -y** (out of the top edge). Render an orthographic **side** view; the
  WRL bounding box is a known trap.
- **J3 and J4's long axes must be parallel to the bottom edge**, pin 1 at the left end of each.

**J3 and J4's final board coordinates are an ICD deliverable.** After P6, compare them against the
nominal positions in `connector-icd.md` s7 and correct with `place_edit` if the annealer has moved
them. **This must be done before any daughter run starts.**
