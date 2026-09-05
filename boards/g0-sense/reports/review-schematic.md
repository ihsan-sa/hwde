# Schematic review - g0-sense (adversarial, P4 fresh-context)

Reviewer: schematic-reviewer subagent, 2026-08-27.
Inputs: reports/schematic.pdf (re-rendered from kicad/g0-sense.kicad_sch),
reports/top.net (re-exported), parts/*.json datasheet extracts,
architecture/constraints.json, architecture/decisions.md,
reference/checklists/{power,mcu,connector,interface-usb}.md,
reports/erc.json (green). Scope: product-scope per requirements.md section 1
(no build-mode token; protection/filtering/connectors/thermal/enclosure-fit
all in scope). Result: 0 errors, 3 warnings.

## What was hunted and cleared (the would-be bring-up killers)

- TVS D1 polarity: symbol cathode bar is on the pin-1 side and pin 1 lands
  on VBUS, anode (pin 2) on GND - correct clamp orientation for a positive
  rail. Footprint SOD-123 silk carries the cathode band at pad 1,
  consistent with the symbol. (A reversed TVS would have shorted VBUS at
  ~0.7 V - checked first, correct.)
- SW1 (TS-1187A-B-A-B) internal contact pairing: the vendor datasheet
  (fetched live from LCSC during this review; not on file in parts/) shows
  terminals A-B internally common and C-D internally common. Netlist puts
  NRST on pins 1/2 (A/B, top pad row of the aiee footprint) and GND on
  pins 3/4 (C/D, bottom row) - matches the drawing's lettering. No
  permanent NRST-to-GND short; button works. (This was the single highest
  dead-board risk left unverifiable from on-file docs.)
- LED polarity: D2 (power) anode on +3V3, cathode via R3 680R to GND;
  D10 (user) anode fed from PA5 via R12 100R, cathode to GND (active
  high). Both netlist pinfunctions are explicit A_1/K_2. Correct.
- C3 tantalum polarity: + pin on +3V3, - pin on GND. Correct. Type is
  22 uF solid tantalum (3 ohm ESR) exactly as the AMS1117 datasheet's
  stability requirement demands (per-datasheet extract, Application
  Hints > Stability); 10 V rating = 3x derating on 3.3 V.
- AMS1117 pinout: pin 1 GND, pin 2 VOUT, pin 3 VIN, pin 4 (tab) on +3V3 -
  matches the C6186 datasheet extract. Input cap C2 10 uF at VIN, output
  C3 22 uF tant. Dropout chain re-checked: 4.75 V min line - PTC drop -
  1.3 V max dropout leaves positive margin (power_tree.md math holds; no
  series reverse element to erase it).
- STM32G030F6P6 pin map vs DS12991 extract: SWDIO=PA13 (pin 18),
  SWCLK/BOOT0=PA14 (pin 19), USART2 TX/RX = PA2/PA3 (pins 9/10),
  I2C SCL on pin 16 (PA11[PA9], AF I2C2_SCL / remap I2C1_SCL) and SDA on
  pin 17 (PA12[PA10], AF I2C2_SDA / remap I2C1_SDA) - SDA/SCL are NOT
  swapped, both FT_fa (FM+ capable). User LED on PA5 (pin 12). All match.
- BOOT0: R13 10 k pull-down on pin 19 boots main flash under either
  option-byte state (decisions.md #20); also correct idle polarity for
  SWCLK. Populated in netlist. Correct.
- NRST: C12 100 nF + button, internal 25-55 k pull-up per DS, no external
  pull needed, no accidental permanent reset. Correct.
- Decoupling per-pin vs datasheets: U2 single bonded VDD/VDDA pin 4 gets
  100 nF (C10) + 4.7 uF (C11) - exactly ST's Fig. 9 scheme for TSSOP20
  (VREF+/VBAT internally bonded, no extra caps applicable). U3 gets
  100 nF (C13) per Sensirion Fig. 1. kicad/decoupling.json agrees.
- USB-C sink: independent 5.1 k Rd on CC1 and CC2 (never shared), all
  four VBUS pads and all four GND pads ganged, shield legs EH1-4 on GND,
  DP/DN/SBU properly NC. Cap topology honors the Type-C 10 uF attach
  limit: only C1=100 nF ahead of the PTC; C2=10 uF after it. TVS ahead of
  the PTC. All per constraints/knowledge records. Correct.
- Header pin orders vs their recorded contracts (decisions.md #13):
  J3 SWD 1:GND 2:3V3 3:SWDIO 4:SWCLK; J4 UART 1:GND 2:3V3 3:TX(=PA2, MCU
  TX) 4:RX(=PA3). J2 Qwiic 1:GND 2:3V3 3:SDA 4:SCL = the published Qwiic
  standard. All match the netlist.
- SHT40 pinout vs datasheet Fig. 11: SDA=1, SCL=2, VDD=3, VSS=4, EP
  unconnected; the aiee DFN-4 footprint deliberately omits the die pad
  per Sensirion's land-pattern mandate (librarian note embedded in the
  footprint). Correct.
- Abs-max on every IC: U1 in 15 V abs vs 5 V applied (9.2 V TVS clamp
  transient - fine); U2 VDD 3.6 V vs 3.3 V; U3 rail-relative rule
  honored; exposed UART/SWD pins on U2 are 5 V-tolerant classes anyway.
- Unused U2 pins are NC-flagged; STM32G0 GPIOs reset to analog mode, so
  floating is safe by silicon design.
- I2C pull-ups 1.5 k: above both recorded floors (967 ohm bus / 390 ohm
  sensor, decisions.md #19 with UM10204 math); ~2.2 mA sink is inside the
  3 mA I2C VOL test current. Considered and recorded - not drift.
- ERC: green at 0/0. No separate netlist_audit report existed in
  reports/; this review audited the exported netlist pin-by-pin instead.

## Findings

### WARNING 1 - No ESD protection or recorded waiver on the Qwiic connector (J2)

J2 is a populated, user-facing, hot-pluggable connector by design (that is
what Qwiic is for). SDA/SCL/+3V3 leave the board with no ESD clamps and no
series impedance; a strike on a dangling cable discharges directly into
U2 PA11/PA12 and U3 (2 kV HBM per its datasheet extract). The connector
checklist requires this expectation "met or waived" at product scope, and
decisions.md records no waiver. Mitigation context (why warning, not
error): the Qwiic ecosystem norm (SparkFun/Adafruit) also omits arrays,
and the MCU pins carry internal clamps. The same observation applies in
weaker form to the DNP bench headers J3/J4 (owner-facing, normal practice
to leave bare). Fix is either a recorded waiver citing ecosystem norm, or
a 4-channel ESD array on SDA/SCL at J2.

### WARNING 2 - Carried SHT4x VDD-slew verify item was assigned to P4 and is still unclosed

power_tree.md and decisions.md carry: "Verify at P3/P4: SHT4x VDD slew
<= 20 V/ms vs AMS1117 startup ramp". Nothing on file closes it. Two facts
from this review: (a) the on-file SHT4x datasheet PDF contains no slew
spec at all (grepped; the 20 V/ms figure's provenance is not on-file
ground truth), and (b) simple worst-case arithmetic - AMS1117 current
limit (~1 A) charging the ~27 uF on +3V3 - allows ~40 V/ms, which would
EXCEED the carried limit if the input step is fast (USB attach). C3's
3-ohm tantalum ESR and the source's own soft-start slow the real edge,
and the sensor is recoverable by soft-reset/power-cycle in firmware, so
this is a warning: close it with the Sensirion design-in guide number or
an explicit accepted-risk record before order.

### WARNING 3 - J3/J4 DNP intent is not KiCad-native

The headers carry "(DNP)" in the value string and a custom "Variant=DNP"
field, but the symbols have no native (dnp) attribute and are in_bom yes.
Any KiCad-native BOM/POS export (kicad-cli bom, stock plugins) will emit
them as populate lines; only pipeline steps that honor the custom field
will DNP them. Economy PCBA is SMT-only so JLC would likely just error or
quote hand-soldering on THT lines - order friction, not a bring-up
failure. Either set the native dnp attribute (belt and braces, keeps
in_bom for the documentation BOM if wanted) or confirm P9's BOM writer
filters on the Variant field.

## Open / could not verify

- AMS1117 SOT-223 tab electrical identity: the on-file datasheet only
  labels "TAB IS OUTPUT" against the TO-252 drawing (extract's own note).
  The schematic ties pin 4 (tab) to +3V3; SOT-223 construction fuses the
  tab to pin 2's lead frame in every 1117-family part, so risk is
  negligible, but it remains formally unconfirmed from this PDF alone.
- SW1 pairing was verified against a LIVE-fetched XKB datasheet
  (LCSC URL), not a file in parts/; suggest archiving it to parts/ so the
  verification is reproducible offline.
- D1 physical-body orientation at assembly (CPL rotation for polarized
  SOD-123) is a P6/P8 concern; decisions.md carries a rotation check for
  J1 only - extend it to D1 and D2/D10.
- SHT4x 20 V/ms slew figure provenance (see WARNING 2).
