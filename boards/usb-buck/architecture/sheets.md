# usb-buck - hierarchical sheet plan

Three child sheets under a thin root, per the brief's request for a
hierarchical schematic. The board has ~28 components across three clearly
separable domains and exactly TWO nets that cross a sheet boundary, so
hierarchy costs almost nothing in net-name risk and buys parallel P4 sheet
generation.

**The sheet NAMES below are contractual.** They appear verbatim in netlist net
names (`/mcu/OSC_IN`) and `constraints.json` already references them; renaming
a sheet renames nets and breaks `netlist_audit --constraints`.

| Sheet | File | Blocks | Interface nets (sheet pins) | pwr_base |
|---|---|---|---|---|
| root `usb-buck` | `usb-buck.kicad_sch` | none (stitching only) | - | 1 (unused) |
| `usb` | `usb.kicad_sch` | USB port + ESD | `USB_DP`, `USB_DM` | 300 |
| `power` | `power.kicad_sch` | buck regulation | **none** | 100 |
| `mcu` | `mcu.kicad_sch` | MCU core + clock, user I/O, debug | `USB_DP`, `USB_DM` | 200 |

## 1. Net naming - the CANONICAL final netlist names

Mechanism (verified in this repo: `tests/s7_regen/hierdemo/kicad/hierdemo.net`
produces `+3V3`, `GND`, `/VIN`, `/CTL`, `/load/LED_K`):

1. **Power SYMBOLS make a net global across the whole hierarchy** with a BARE
   name and need NO sheet pin.
2. A child net merged with the root through a sheet pin takes the **root-side
   label**: `schlib.Project.add_sheet(child, ..., nets=["X"])` wires each sheet
   pin outward to a root local label `X`, so the net becomes `/X`.
3. A child-internal label becomes `/<sheet>/NAME`.

### Global rails (power symbols, no sheet pins) - bare names

| Net | Symbol | Present on | Driven by |
|---|---|---|---|
| `VBUS` | `power:VBUS` | usb, power | J1 pin 1 (passive) -> **needs PWR_FLAG** |
| `+3V3` | `power:+3V3` | power, mcu | L1 pin 2 (passive - the AP63203 has no VOUT pin, the rail forms after the inductor) -> **needs PWR_FLAG** |
| `GND` | `power:GND` | all | **needs PWR_FLAG** |

All three PWR_FLAGs live on the `power` sheet (`#FLG0100`+). Power symbols
being global, one flag each drives the net hierarchy-wide.

### Root-crossed signals - `/NAME`

| Final net | Root label | Exposed by | Members |
|---|---|---|---|
| `/USB_DP` | `USB_DP` | `usb` + `mcu` sheet pins | J1 pin 3, U3 channel-A I/O pads, U1 PA12, R4 |
| `/USB_DM` | `USB_DM` | `usb` + `mcu` sheet pins | J1 pin 2, U3 channel-B I/O pads, U1 PA11 |

Both children expose the same two names; the root's two local labels per name
merge by name on the root sheet. These are the names `constraints.json` uses
for `high_speed` and `diff_pairs` - matching the usbbuck4 golden precedent
(`/USB_DP` + `/USB_DM` with bare `VBUS`/`+3V3`/`GND`).

### Sheet-internal signals - `/<sheet>/NAME`

| Sheet | Final net | Members |
|---|---|---|
| power | `/power/SW` | U2 SW, L1 pin 1, C3 (BST cap) low side |
| power | `/power/BST` | U2 BST, C3 high side |
| mcu | `/mcu/OSC_IN` | U1 PD0/OSC_IN, Y1, C10 |
| mcu | `/mcu/OSC_OUT` | U1 PD1/OSC_OUT, Y1, C11 |
| mcu | `/mcu/SWDIO` | U1 PA13, J2 pin 4 |
| mcu | `/mcu/SWCLK` | U1 PA14, J2 pin 2 |
| mcu | `/mcu/NRST` | U1 NRST, C19 |
| mcu | `/mcu/BOOT0` | U1 BOOT0, R3 (to GND) |
| mcu | `/mcu/LED_A` | R1 (from +3V3) -> D1 anode |
| mcu | `/mcu/LED` | D1 cathode -> U1 PC13 (active low sink) |
| mcu | `/mcu/BTN` | U1 PB0, R2 (to +3V3), SW1 (to GND) |
| usb | - | none: the pair and the rails are all cross-sheet or global |

`constraints.json` references `/mcu/OSC_IN` and `/mcu/OSC_OUT` in
`high_speed`. That is deliberate (see decisions.md item 8) and is the reason
the sheet name `mcu` is contractual.

## 2. Refdes allocation (unique ACROSS sheets - contractual for P4)

| Sheet | Assigned | Reserved for growth | pwr_base |
|---|---|---|---|
| `power` | U2, L1, C1-C5 | C6-C9, R5-R9 | 100 (`#PWR0100`+, `#FLG0100`+) |
| `mcu` | U1, Y1, J2, D1, SW1, R1-R4, C10-C19 | C20-C29, R10-R19 | 200 |
| `usb` | J1, U3 | C30-C39, R30-R39 | 300 |

### power sheet

| Ref | Part | Note |
|---|---|---|
| U2 | AP63203WU-7, TSOT-26 | fixed 3.3 V; FB ties to the +3V3 sense point (NOT a divider - that is the adjustable AP6320x); EN -> VBUS; no PG pin |
| L1 | 4.7 uH, Isat >= 1 A, DCR < 100 mohm, shielded | DS41326 Table 2 says 3.9 uH; 4.7 uH is nearer standard and better at light load |
| C1 | 10 uF X5R/X7R >= 16 V, 0805 | C_IN - the USB-limited one, see power_tree.md s3 |
| C2 | 100 nF >= 16 V | HF bypass at VIN, tight to the pin |
| C3 | 100 nF >= 16 V | C_BST, between BST and SW |
| C4, C5 | 22 uF X5R >= 10 V, 0805 | C_OUT, ceramic mandatory (internal compensation assumes it) |

### mcu sheet

| Ref | Part | Note |
|---|---|---|
| U1 | STM32F103C8T6, LQFP-48 | |
| Y1 | 8 MHz crystal, +/-30..50 ppm, CL 20 pF class | HSE mandatory for USB FS |
| C10, C11 | crystal load caps, C0G | value = 2 x (CL - C_stray); ~22 pF for a CL 20 pF part. No series damping resistor |
| C12, C13, C14 | 100 nF | one per VDD/VSS pair (pins 24/36/48) |
| C15 | 4.7 uF | +3V3 bulk at the MCU |
| C16 | 100 nF | VDDA (pin 9) HF |
| C17 | 1 uF | VDDA bulk - kept, not waived: VDDA sits on a 1.1 MHz switching rail |
| C18 | 100 nF | VBAT (pin 1) |
| C19 | 100 nF | NRST (pin 7) |
| R1 | 1 k, 0603 | LED series, sets 1.4 mA (PC13's 3 mA limit) |
| R2 | 10 k | button pull-up to +3V3 |
| R3 | 10 k | BOOT0 pull-down to GND |
| R4 | **1.5 k 1%** | USB D+ pull-up to +3V3 - MANDATORY, the F103 has none internally. NOT 10 k (the Blue Pill clone bug) |
| D1 | red LED, 0603 | active low |
| SW1 | SMD tactile switch | to GND |
| J2 | 1x4 2.54 mm THT pin header | SWD, hand-soldered |

### usb sheet

| Ref | Part | Note |
|---|---|---|
| J1 | USB micro-B receptacle, SMD | `Connector:USB_B_Micro`; pipeline renumbers `SH` -> 6 |
| U3 | USBLC6-2SC6, SOT-23-6 | 2-channel USB TVS array + VBUS clamp pin |

`constraints.json` references J1, J2 (edges), U2/L1/J1/U3 (separation), and
Y1/C10/C11 + U2/L1/C1-C5 (groups). `decoupling.json` (P4-emitted) will
reference C1, C2, C12-C18 against U1/U2 pins. These assignments are
contractual, not suggestions.

## 3. Interface pinouts (silk-labeled, canonical)

- **J1 micro-B**: 1 VBUS, 2 D- (`/USB_DM`), 3 D+ (`/USB_DP`), 4 ID
  (**no-connect** - device only, no OTG), 5 GND, 6/SH shield -> **GND
  directly** (decision 5).
- **J2 SWD**: 1 = +3V3 (reference OUT), 2 = SWCLK, 3 = GND, 4 = SWDIO. ST
  Nucleo CN4 debug-row order minus NRST/SWO. Silkscreen all four.

## 4. U1 pin commitments (P4 wiring contract, LQFP-48)

Pin numbers below are from the verified DS5319 pin table used by the
stm32-blinky sheet plan plus the USB research (PA11 = 32, PA12 = 33);
**P4 re-confirms every number against the `parts/` datasheet extract** before
wiring - PB0's number in particular is not pinned here.

- VBAT (1) -> `+3V3` (no battery) + C18. VDD 24/36/48 -> `+3V3` + C12/C13/C14
  + C15 bulk. VDDA (9) -> `+3V3` + C16 + C17. VSS 23/35/47 -> `GND`,
  VSSA (8) -> `GND`.
- PC13 (2) -> `/mcu/LED` (sink only; ST limits PC13-15 to 3 mA).
- PD0/OSC_IN (5) -> `/mcu/OSC_IN`, PD1/OSC_OUT (6) -> `/mcu/OSC_OUT`.
- NRST (7) -> `/mcu/NRST`.
- PB0 -> `/mcu/BTN` (active low; PA0/WKUP left free for a future active-high
  wake-up function).
- PA11 (32) -> `/USB_DM`, PA12 (33) -> `/USB_DP`. **No series resistors** -
  the F103 PHY's output impedance is internal; 22R/33R would push it outside
  the USB 28-44 ohm window.
- PA13 (34) -> `/mcu/SWDIO`, PA14 (37) -> `/mcu/SWCLK` (SWD is the reset
  default on these pins).
- BOOT0 (44) -> `/mcu/BOOT0` -> R3 10 k -> GND (fixed strap; the user button
  is explicitly NOT a boot selector).
- PB2/BOOT1 (20) and every unused GPIO: no-connect flag so ERC is clean.

## 5. P4 generator notes (schlib specifics that bite)

1. **`power` sheet has no sheet pins**: `proj.add_sheet(power_sheet.build(),
   at=..., size=..., nets=[])`. All three of its rails are power symbols and
   are global already. Do not invent sheet pins for rails.
2. **Use the free-cluster `hier_pin(net, at=...)` variant** on both the `usb`
   and `mcu` sheets for `USB_DP`/`USB_DM`. Each net has 2+ components on it,
   and that variant places a LOCAL label plus the hierarchical label on one
   stub so the hier label joins by wire geometry rather than relying on
   hier-label/local-label name merging.
3. **Root-side labels sit 7.62 mm to the LEFT of each sheet pin** (add_sheet's
   `label_stub = 3 * STUB`), and sheet pins stack down the sheet symbol's
   LEFT edge. Leave that strip clear when placing the `usb` and `mcu` sheet
   symbols on the root, and give both sheets the same `nets=` order.
4. **PWR_FLAGs**: `power_flag("VBUS", sym="power:VBUS", flag=True)`,
   same for `+3V3` and `GND`, all on the `power` sheet. Without them ERC
   reports the rails as undriven (every driver on this board is a passive
   pin - connector, inductor).
5. **U3 in-line wiring**: the array's two same-channel I/O pads are internally
   common - wire BOTH pads of a channel to the same net so layout can pass
   the trace through the part with no stub. Its VBUS/supply pin ties to
   `VBUS`. Confirm the pin table from the P3 datasheet extract; do not wire
   from memory.
6. **Decoupling metadata**: rails on the `mcu` and `power` sheets are power
   symbols, so the wiring label and the final net name agree (`+3V3`, `GND`)
   and no `rail_net`/`gnd_net` override is needed anywhere on this board.
7. `Sheet.add_component(..., expect={...})` on U1, U2, U3 - pin-name insurance
   against a wrong symbol.

## 6. Board-edge placement (mirrors constraints.json)

- **J1 (micro-B) on the LEFT edge**, pos 0.5 - the plug must seat, and this
  puts the pair's origin on the short axis with a straight shot to U1 in the
  middle of the board (usbbuck4 golden precedent).
- **J2 (SWD header) on the RIGHT edge**, pos 0.5 - opposite the USB cable so
  a debug ribbon and a USB cable do not fight, and PA13/PA14 sit on the
  LQFP's right flank.
- `separation` pushes U2/L1 at least 8 mm from J1/U3, keeping the 1.1 MHz
  switch node out of the corner where the USB pair starts.
- `groups`: `xtal` (Y1 + C10/C11) and `buck` (U2 + L1 + C1-C5) so the
  annealer moves each as a unit until P4's decoupling metadata takes over.
