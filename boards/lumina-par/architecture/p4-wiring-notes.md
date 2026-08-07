# P4 wiring notes - binding facts that SUPERSEDE sheets.md

`architecture/sheets.md` was written at P2. P3 closed several items and the
datasheet extractions found errata. Where this file and sheets.md disagree,
**this file wins**. Every fact here is traceable to `state.json` history or to
`parts/<lcsc>.json`. Wire against the extract JSONs and the symbol pin table
(`scripts/schlib.py --pins`), never from memory.

## 1. Values closed since sheets.md

| Item | sheets.md said | Binding value |
|---|---|---|
| R206 (`/ID_ADC` bottom leg) | "VALUE TBD - P4 blocker" | **4.7 kohm, 1 % REQUIRED** (not merely preferred). CR-1 CLOSED: LUM-PAR-A is ID_ADC code 2, V_ID = 1.055 V. Not a blocker any more. |
| R301/R321/R341/R361 sense | "sets 300 mA" | **0.75 ohm** (not 0.68) -> nominal **275 mA/channel**. The compliant value is the default. 0.68 alternate = C2934269. |
| Q301/Q321/Q341/Q361 shunt FET | "60 V logic-level N-FET" | **SSM3K2615R,LXGF** (C22371361), **SOT-23F** land. |
| PWM timing | 13-bit / 9.766 kHz | **14-bit / 4.883 kHz** (CR-3 granted and adopted as this board's declared timer map). |

## 2. COFF network - NEW parts, not in sheets.md s1.3

TPS92515HV sec 8.3.4: with a shunt FET across the string the output falls below
the 1 V VOFT threshold, the OFF-timer never trips, every cycle stretches to
tOFF(max), and ripple + dimming linearity are LOST (datasheet Figure 43). This
network is what makes the shunt-FET topology work at all.

Per channel (channel 0 shown; ch n = base 300 + 20n): **C304** = COFF at pin 1,
**R305** = ROFF1, **R306** = ROFF2. Figure 14 topology.

- **R305 (ROFF1) connects to VLED**, which on THIS board is the `/LEDn_A` anode
  net running out to J5. Do NOT mistake it for a local node.
- **R306 (ROFF2) MUST come from the device's own VCC pin (pin 2).** Do NOT
  re-source it from `+3V3` or any external rail: there is an internal COFF-to-VCC
  diode that can pull VCC up and start the device with VIN unpowered.
- **ROFF1 = 10 k, NOT TI's literal 8.2 k.** ROFF1 and ROFF2 sit permanently in
  parallel, so ROFF2 also charges COFF in normal operation; the TI text ignores
  that and the ripple would land 12 % low. E96 exact root 9.53 k has zero LCSC
  stock. Reverting is a one-line change if disputed.
- **The TPS92515HV PWM pin abs max is 5.5 V - it is NOT 12 V tolerant.** Fine
  from 3.3 V logic, but never route 12 V near it.
- **Do NOT place a PWR_FLAG on any driver's VCC node.** The P4 retype pass typed
  TPS92515HV **pin 2 (VCC) as `power_out`** - correct, because it is the internal
  LDO's output, and it is what stops the VCC net raising `pin_not_driven`. Adding
  a flag there raises a `power_out <-> power_out` ERC conflict instead. Each
  channel's VCC is a LOCAL node (decoupler + ROFF2), not a board rail.
  Pins 3/8/11 are `power_in`; every logic IC's supply pins are `power_in`.

## 3. Datasheet errata - wire from the package diagram, not the tables

- **LM339LV / U401 (quad comparator): wire by PIN NUMBER, never by channel
  name.** The datasheet transposes OUT labels between Fig 5-3 and Table 5.2.
  Correct groupings: `out1 <-> in6/7`, `out2 <-> in4/5`, `out13 <-> in10/11`,
  `out14 <-> in8/9`.
  - Outputs ARE open-drain, sinking-only, explicitly wire-OR-able (4 independent
    datasheet statements) - the `/FAULT` architecture is SAFE. Inputs ARE
    rail-to-rail.
  - **No internal hysteresis** - external hysteresis is mandatory; sheets.md
    R405-R412 already allocates it.
  - POR: outputs are Hi-Z for up to 30 us after V+ crosses 1.5 V, so `/FAULT`
    reads no-fault in that window. Note it; do not try to fix it in hardware.
- **SN74LVC00A / U202 erratum**: the Pin Functions table's TYPE/DESCRIPTION
  columns are shifted one row from 3Y down (it prints 3Y as a power pin and VCC
  as the gate-3 output). **Pin numbers and the package diagram are correct -
  wire from the diagram.** VCC is 1.65-3.6 V ONLY (not 5 V rated; inputs are
  5.5 V tolerant) - fine at 3.3 V.
- **M24C32 / U203**: tie **E0/E1/E2 (pins 1/2/3) to VSS** for address 0x50. **WC
  (pin 7) is ACTIVE-HIGH** write protect, so **tie it to VSS** to allow writes.
  (Datasheet publishes no recommended land pattern - standard IPC-7351 SOIC-8.)
- Logic drive at 3.3 V: all three parts +-24 mA, VIH 2.0 / VIL 0.8. tpd LVC00A
  3.5 ns typ / 4.3 max, LVC14A 3.2 typ / 6.4 max.

## 4. Connectors

- **J3/J4 (CONNFLY DS1023) carry NO pin numbers in the datasheet** - numbering
  comes from **ICD-01 s3.1/s3.2** and nowhere else.
- The DS1023 part code offers only `S` = straight, drawn as a TOP-side THT
  socket; **no down-facing land pattern, keep-out or standoff is published**. The
  hole grid is symmetric so the land pattern is unchanged, but **pin-1 mirroring,
  silkscreen side and courtyard are the designer's call and must be handled
  explicitly** - check pin 1 in the MATED view, not from the footprint.
- Connector pads use a **1.70 mm annulus / 1.10 mm drill** (0.300 mm/side ring)
  per the re-synced ICD. Already applied to the J3/J4 footprints.
- **J5 entry direction is an OPEN P4 action.** The extract flags
  S10B-PH-SM4-TB as side entry while the B-prefix convention reads as top entry.
  J5 sits on the top edge feeding a module ABOVE the board. Settle it from
  `parts/C265014.json` + the datasheet and REPORT the answer in OPEN - do not
  silently pick. A wrong call here is a swap-part, not a respin.

## 5. Unchanged but easy to get wrong (from sheets.md s4)

1. **No output capacitor across any LED string** - a shunt FET dumps it every
   PWM cycle. Do not add one.
2. **`/FAULT` is open drain and must never be driven high.** ERC will want a
   driver; the comparator outputs plus R207 are it.
3. **No I2C pull-ups on this board** - fitting them is an ICD violation.
4. **`PWM4..7` and `DSPI_*` are deliberate no-connects** - land them on J4 and
   flag with an explicit `~` no-connect so ERC stays clean and the decision is
   visible.
5. **DNP option sets must be in the netlist**: branch-B front end (Q101/Q102/
   R101-R104/C106-C108) and the converter-idle one-shot (U204/R210-R213/
   C210-C213/D201-D204). Mark them DNP in the BOM variant field.
6. **Net-naming contract**: place a root-sheet local label on every inter-sheet
   wire, spelled exactly as in sheets.md s2. Power nets are bare global symbols
   (`+3V3`, `+12V`, `+48V_SW`, `GND`); every other inter-sheet net leads with `/`.
   P5-P8 silently no-op on any net whose name does not match.
