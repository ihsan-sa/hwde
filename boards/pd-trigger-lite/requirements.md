# Requirements: pd-trigger-lite

Source: `brief/brief.md`. Written inline by the orchestrator (no requirements-analyst
spawn: a one-block board, recorded as a decision). Unattended run: every open item below
was answered by the orchestrator as the owner's delegate and recorded with
`state.py decision`. Mode: none (the brief carries no mode token) - design normally.

## 1. Function

A low-cost USB-C Power Delivery trigger. A PD sink controller negotiates a fixed voltage
from a USB-C PD charger and passes VBUS straight through to two output pads. No regulation,
no conversion, no switching element in the power path. The requested voltage is chosen by
solder links on the board: 9, 12, 15 or 20 V, shipped at 12 V.

## 2. Interfaces

- Input: USB-C receptacle, power-only use, PD SINK. CC1/CC2 to the controller; D+/D- to
  the controller's DP/DM per the datasheet reference (no USB data function).
- Output: VBUS and GND on two 2.54 mm-pitch plated through-holes (take a 1x2 header or
  wires). No screw terminal (cost).
- Voltage selection: one solder link per voltage (9/12/15/20 V), exactly one closed.
  The 12 V link ships fitted as a 0 ohm resistor; the others are open pads.

## 3. Power

- Input: USB-C PD source, 5 V default, negotiated 9/12/15/20 V.
- Output current rating: 3 A continuous at any voltage (a non-e-marked cable caps the
  contract at 3 A; the board makes no 5 A claim).
- Controller supply: from VBUS directly (CH224A VHV pin is rated 32 V).

## 4. Environment

Bench use, indoor, 0-50 C ambient. No enclosure, no battery, no mains.

## 5. Size & mounting

Target <= 25 x 15 mm (soft; grow only if DRC needs it). No mounting holes (cost/size;
the board hangs off its cable and output wires).

## 6. Quantity & budget

Quantity 5, JLCPCB PCB + economy PCBA, lowest cost. JLC Basic parts wherever possible.

## 7. Assembly

Single-sided SMT at JLC. The 1x2 output header is optional and hand-fitted by the owner.

## 8. Compliance/safety flags

- >3 A: NO (3 A max). Mains: NO. Battery: NO.
- Protection: no TVS/fuse - the controller datasheet requires none (decision recorded).

## 9. Open questions

None open. Every question was answered by the orchestrator as delegate (see
state.json decisions): controller part, selection method, default voltage, output
format, current rating, LED, bulk cap, protection.
