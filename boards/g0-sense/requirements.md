# requirements - g0-sense

P0 requirements distilled from `brief/brief.md` (2026-08-27, unattended container run).

## 1. Function

Mode declaration: the brief carries NO mode token, so mode = none - design
normally. Scope = product-scope per the brief's own words ("a product-scope
board ... meant to be sent to JLCPCB as-is"): protection, filtering,
connectors, thermal and enclosure-fit are all in scope, and their absence is a
reviewer finding. Binding: the stated ~35 x 25 mm size is a SOFT preference,
not a hard cap (see section 5). Stage under study: none.

The board is a small 2-layer USB-C powered temperature/humidity sensor node.
A USB-C receptacle supplies 5 V (power only, no data); a fixed 3.3 V LDO
powers an STM32G030F6P6 MCU running on its internal oscillator, which reads a
Sensirion SHT4x sensor over I2C. The same I2C bus is exposed on a
Qwiic/STEMMA-QT connector; readout/logging is over a 4-pin UART header;
programming/debug is over a 4-pin SWD header. One user LED and one power LED.
Prototype quantity 5, JLC economy PCBA, meant to be ordered as-is.

## 2. Interfaces

- USB-C receptacle, POWER ONLY: 5 V VBUS input; 5.1 k pull-downs on CC1 and
  CC2 (so any USB-C source or a legacy A-to-C cable enables VBUS); D+/D-
  unconnected; no USB data.
- SWD header: 4-pin, 0.1 in pitch. ASSUMED: pins GND, 3V3, SWDIO, SWCLK
  (exact order per architect; brief states only "4-pin SWD header (0.1 in)").
- UART header: 4-pin, 0.1 in pitch: GND, 3V3, TX, RX - for readout/logging.
  ASSUMED: TX/RX are named from the MCU's perspective (TX = MCU transmit).
- Qwiic/STEMMA-QT connector: JST SH 1.0 mm 4-pin, GND/3V3/SDA/SCL, sharing
  the sensor I2C bus. I2C pull-ups required on the board (values per
  architect).
- User LED: one, driven from a GPIO through a series resistor.
- Power LED: one (which rail it indicates - VBUS or 3V3 - is per architect;
  the brief does not say).
- NRST push button (momentary reset).
- BOOT0: handled (method - strap, option bits, or jumper - per architect; the
  brief requires only that it is handled).
- Four M2 mounting holes, CONDITIONAL: only if they fit without hurting the
  layout (see section 5).

## 3. Power

- Input: USB-C VBUS, 5 V nominal, device draws < 1 A total. No battery, no
  charging, no mains.
- VBUS input protection required (product scope, brief-stated): TVS,
  resettable fuse or equivalent; reverse/inrush handling as the architect
  sees fit - the brief delegates the exact topology.
- 3.3 V rail: fixed LDO, >= 300 mA. JLC Basic/Preferred part preferred;
  AMS1117-3.3 class acceptable. Proper input/output capacitors per the chosen
  part's datasheet.
- Rail budget (GUESSES - to be replaced by the architect's numbers):
  - STM32G030F6P6 on internal oscillator: ~5-15 mA (guess)
  - SHT4x: < 1 mA average, single-digit mA peaks during measurement (guess)
  - LEDs: ~2-5 mA total (guess)
  - Qwiic downstream devices: not budgeted by the brief - see open
    question 2 (recommended default: reserve 100 mA).
  - On-board total is tens of mA; the brief's >= 300 mA LDO floor leaves the
    headroom for Qwiic loads.

## 4. Environment

Not stated in the brief. ASSUMED: indoor, room-ambient use (roughly 0-40 C),
bare board, no ingress or vibration requirements (see open question 1). The
one stated thermal/environmental requirement is layout-level: the SHT4x gets
a thermal isolation slot/cutout, or at minimum is kept away from LDO and MCU
heat, so self-heating does not corrupt the measurement.

## 5. Size & mounting

- Outline: "whatever an honest layout wants, roughly 35 x 25 mm or smaller".
  This is a SOFT preference - no HARD cap. It must NOT bind at P5
  board_init; the layout earns the final outline, and ~35 x 25 mm is a
  target to aim for, not a box to squeeze into (see open question 5).
- Mounting: four M2 mounting holes, CONDITIONAL - "if they fit without
  hurting the layout". The brief itself allows dropping or reducing them in
  favor of layout honesty; record that decision if taken.
- Height: no limit stated.

## 6. Quantity & budget

- Quantity: 5 boards, prototype run, assembled.
- Unit cost: no target stated (see open question 3). Cost posture from the
  brief: JLC economy PCBA; prefer JLC Basic parts; Extended parts only where
  the brief names the part (MCU, sensor, connectors).

## 7. Assembly

- JLC economy PCBA for the SMD parts.
- ASSUMED: single-sided SMD assembly (economy PCBA norm, and this part count
  does not need the second side).
- Through-hole parts: economy PCBA assembles SMD only, so the two 0.1 in
  headers are ASSUMED to ship unpopulated for owner hand-soldering (see open
  question 4).
- ASSUMED: NRST push button and the USB-C / JST SH connectors are SMD,
  JLC-assemblable variants where stock allows, so they ride the PCBA run.
- Board: 2 layers, 1.6 mm FR-4, HASL, green (brief-stated).

## 8. Compliance/safety flags

Each flag checked against the brief; none applies:

- Mains voltage: NOT APPLICABLE - brief states "no mains"; input is USB 5 V.
- Battery: NOT APPLICABLE - brief states "no battery"; no charging circuitry
  anywhere in scope.
- Motors: NOT APPLICABLE - no motor or actuator in the brief's scope.
- >30 V: NOT APPLICABLE - the highest voltage on the board is USB VBUS at
  5 V nominal.
- High current (>3 A): NOT APPLICABLE - the brief describes a USB 5 V,
  < 1 A device.
- RF transmit: NOT APPLICABLE - brief states "no RF"; no radio, and no USB
  data either ("D+/D- unconnected").

## 9. Open questions

Closed-form, each with a recommended default. Unattended run: the
orchestrator answers these on the owner's behalf and records the answers.

1. Operating environment: is indoor, room-ambient use (about 0-40 C, bare
   board, no ingress/vibration requirements) correct?
   Recommended default: YES.
2. Qwiic 3.3 V budget: how much current may external Qwiic/STEMMA-QT devices
   draw from the 3.3 V rail?
   Recommended default: reserve 100 mA (fits under the >= 300 mA LDO floor
   together with the on-board load).
3. Unit cost: is there a hard per-board cost cap?
   Recommended default: NO hard cap - minimize via economy PCBA and Basic
   parts as the brief already directs.
4. Header population: should the two 0.1 in headers (SWD, UART) ship
   unpopulated for hand-soldering, given economy PCBA assembles SMD only?
   Recommended default: YES - footprints and holes present, headers not
   populated at assembly.
5. Size confirmation: is ~35 x 25 mm truly a soft preference (the layout may
   exceed it if honesty demands), not an enclosure-driven hard cap?
   Recommended default: SOFT preference, per the brief's own wording
   ("whatever an honest layout wants").
