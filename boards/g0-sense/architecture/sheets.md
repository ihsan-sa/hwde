# sheets - g0-sense hierarchical plan (P2)

Small board: root + TWO child sheets. One sheet would also fit, but the
power/main split gives P6 its natural placement groups (power entry corridor
vs logic/sensor), keeps the Type-C + protection cluster reviewable in one
frame, and costs nothing. Refdes are unique ACROSS sheets by disjoint
ranges; every range includes a #PWR base.

## Root: `g0-sense.kicad_sch`

Holds the two sheet symbols only. Global power nets (power symbols, bare
netlist names): `VBUS`, `+5V`, `+3V3`, `GND`. Power symbols make these
names bare in the final netlist; all constraints.json net references use
the bare forms.

## Sheet 1: `power.kicad_sch` (blocks B1 usb-input+protection, B2 ldo-3v3)

- Contents: J1 USB-C receptacle; R1, R2 (5.1k Rd); D1 (TVS); F1 (PTC);
  C1 (100 nF VBUS); U1 (AMS1117-3.3); C2 (10 uF X5R, +5V at VIN);
  C3 (22 uF tantalum, +3V3); D2 (power LED red) + R3 (620 Ohm).
- Interface nets (hier pins -> placement groups at P6): `+3V3` (out),
  `GND`. VBUS and +5V stay sheet-local (they leave via power symbols, so
  their netlist names are still bare `VBUS` / `+5V`).
- Sheet-local labels: `CC1`, `CC2` (final names `/power/CC1`, `/power/CC2`).
- Refdes ranges: J1; U1; F1; D1-D9; R1-R9; C1-C9; SW none; #PWR pwr_base=100
  (#PWR0100-#PWR0199).

## Sheet 2: `main.kicad_sch` (blocks B3 mcu, B4 sht4x + I2C/Qwiic, headers)

- Contents: U2 (STM32G030F6P6); U3 (SHT40-AD1B class); C10 (100 nF U2),
  C11 (4.7 uF U2), C12 (100 nF NRST), C13 (100 nF U3); R10, R11 (1.5k I2C
  pull-ups), R12 (220 Ohm user LED), R13 (10k BOOT0 pull-down); D10 (user LED green); SW1 (NRST
  button); J2 (Qwiic JST SH); J3 (SWD 1x4 DNP); J4 (UART 1x4 DNP);
  H1-H4 (M2 mounting holes, conditional).
- Interface nets: `+3V3` (in), `GND`.
- Sheet-local labels (final names `/main/<label>`): `SDA`, `SCL`, `SWDIO`,
  `SWCLK`, `UART_TX`, `UART_RX`, `NRST`, `LED_USER`.
- Refdes ranges: U2-U9; J2-J9; D10-D19; R10-R19; C10-C19; SW1-SW9; H1-H9;
  #PWR pwr_base=200 (#PWR0200-#PWR0299).

## Interface-net contract (P4 must produce exactly these)

| Net (netlist form) | Class | From | To |
|---|---|---|---|
| VBUS | power (bare) | J1 | D1, F1, C1 |
| +5V | power (bare) | F1 | U1 VIN, C2 |
| +3V3 | power (bare) | U1 VOUT | C3, D2/R3, U2, U3, R10, R11, J2, J3.2, J4.2 |
| GND | power (bare) | all | all + J1 shield |
| /power/CC1, /power/CC2 | signal | J1 CC pins | R1, R2 |
| /main/SDA, /main/SCL | signal | U2 PA10/PA9 | U3, J2, R10/R11 |
| /main/SWDIO, /main/SWCLK | signal | U2 PA13/PA14 | J3.3/J3.4; SWCLK also R13 -> GND |
| /main/UART_TX, /main/UART_RX | signal | U2 PA2/PA3 | J4.3/J4.4 |
| /main/NRST | signal | U2 pin 6 | C12, SW1 |
| /main/LED_USER | signal | U2 PA5 | R12 -> D10 |

Header pinouts (canonical): J3 SWD = 1:GND, 2:3V3, 3:SWDIO, 4:SWCLK.
J4 UART = 1:GND, 2:3V3, 3:TX (MCU transmit), 4:RX (MCU receive). Pin 1
marked on silk on both; no vendor standard exists for a 4-pin SWD header,
so the silk labels are the contract.
