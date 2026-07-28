# stm32-blinky - sheet plan

## One flat root sheet

Single root sheet (`stm32-blinky.kicad_sch`), no hierarchy. Justification:
18 components / 6 blocks fit one readable page; hierarchical sheets would add
sheet-pin/label drift risk (LEARNINGS 2026-07-22: child nets rename to
"/<sheet>/NAME", root-side names win at pins) for zero navigational gain. The
proven blinky2 golden is flat. Placement grouping at P6 comes from
constraints.json + decoupling.json, not from sheets, so hierarchy buys
nothing there either.

Consequence for net names: power nets are bare (`+5V`, `+3V3`, `GND`), every
labeled signal net is a root local label and lands in the netlist as
`/NAME`. The names below are CANONICAL - P4 must produce exactly these and
constraints.json already references them.

## Refdes plan (canonical assignment - single sheet, one range)

| Refdes | Part | Block |
|---|---|---|
| U1 | STM32F103C8T6, LQFP-48 | MCU core |
| U2 | AMS1117-3.3, SOT-223 | Regulation |
| J1 | 1x2 2.54 mm header (5 V in) | Power input |
| J2 | 1x4 2.54 mm header (SWD) | Debug |
| D1 | SS34 Schottky, SMA | Reverse protection |
| D2 | Red LED 0603/0805 | User LED |
| Y1 | 8 MHz crystal, HC-49S SMD | Clock |
| R1 | 1 k 0603 (LED series) | User LED |
| R2 | 10 k 0603 (BOOT0 pulldown) | MCU core |
| C1-C3 | 100 nF 0603 (VDD 48/24/36) | MCU core |
| C4 | 100 nF 0603 (VDDA pin 9) | MCU core |
| C5 | 10 uF 0805 (LDO out) | Regulation |
| C6 | 10 uF 0805 (LDO in) | Regulation |
| C7, C8 | 22 pF C0G 0603 (xtal load) | Clock |
| C9 | 100 nF 0603 (NRST) | MCU core |

Power-symbol refs: `pwr_base=1` (#PWR001 upward, single range - no other
sheet to collide with).

constraints.json references J1, J2 (edges) and Y1, C7, C8 (xtal group);
decoupling.json (P4-emitted) will reference C1-C6 against U1/U2 pins as in
the table above. These assignments are therefore load-bearing, not
suggestions.

## Canonical nets

| Net | From -> to | Notes |
|---|---|---|
| `/VIN` | J1.1 -> D1 anode | raw unprotected 5 V stub; no caps here |
| `+5V` | D1 cathode -> C6, U2.VIN(3) | protected rail; needs PWR_FLAG (diode-fed) |
| `+3V3` | U2.VOUT(2/tab) -> C5, C1-C4, U1 VDD/VDDA/VBAT, R1, J2.3 | driven by LDO power output |
| `GND` | J1.2, U2.GND(1), all cap returns, R2, J2.4, Y1 can (if 4-pad) | needs PWR_FLAG; B.Cu pour at P7 |
| `/SWDIO` | U1 PA13 (pin 34) -> J2.1 | |
| `/SWCLK` | U1 PA14 (pin 37) -> J2.2 | |
| `/LED_A` | R1 -> D2 anode | R1 top side ties to +3V3 |
| `/LED` | D2 cathode -> U1 PC13 (pin 2) | ACTIVE-LOW, PC13 sinks ~1.3 mA |
| `/OSC_IN` | U1 PD0/OSC_IN (pin 5) -> Y1, C7 | high_speed w/ GND reference |
| `/OSC_OUT` | U1 PD1/OSC_OUT (pin 6) -> Y1, C8 | high_speed w/ GND reference |
| `/NRST` | U1 NRST (pin 7) -> C9 | no header pin, no button (P0 answer) |
| `/BOOT0` | U1 BOOT0 (pin 44) -> R2 -> GND | fixed strap, not a jumper |

## U1 pin commitments (P4 wiring contract, LQFP-48)

- VBAT (1) -> +3V3 (no battery). VDD: 24/36/48, VDDA: 9 -> +3V3.
  VSS: 23/35/47, VSSA: 8 -> GND.
- PC13 (2) = /LED sink. PD0 (5)//OSC_IN, PD1 (6)//OSC_OUT. NRST (7) = /NRST.
- PA13 (34) = /SWDIO, PA14 (37) = /SWCLK. BOOT0 (44) = /BOOT0.
- PB2/BOOT1 (20): floating is electrically fine (don't-care with BOOT0=0) but
  give it a no-connect flag like every other unused GPIO so ERC is clean.

## Interface pinouts (silk-labeled, canonical)

- J1: 1 = +5 V in (/VIN), 2 = GND. Polarity marked on silk (requirements).
- J2: 1 = SWDIO, 2 = SWCLK, 3 = 3V3, 4 = GND (requirements' listed order).

## Board-edge placement (mirrors constraints.json)

- J1 on the LEFT edge (power enters beside the D1 -> U2 chain; U1's
  crystal/LED pins face left-top too, keeping the left half analog-quiet-ish).
- J2 on the RIGHT edge (PA13/PA14 sit on the LQFP right/top-right flank).
