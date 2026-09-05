# Brief: g0-sense (unattended container run, 2026-08-27)

A small 2-layer USB-C powered temperature/humidity sensor node - a product-scope
board (no mode token: design normally), meant to be sent to JLCPCB as-is.

- Power: USB-C receptacle used for POWER ONLY (5 V VBUS; 5.1 k CC pull-downs so
  any USB-C source or a legacy A-to-C cable enables VBUS; D+/D- unconnected).
  Sensible input protection for a USB-powered device (VBUS TVS, resettable
  fuse or equivalent, reverse/inrush as the architect sees fit).
- 3.3 V rail from a fixed LDO, >= 300 mA, JLC Basic/Preferred part if one fits
  (AMS1117-3.3 class is fine), with proper input/output capacitors.
- MCU: STM32G030F6P6 (TSSOP-20) on the internal oscillator - no crystal.
  Decoupling per the datasheet, NRST with a push button, BOOT0 handled.
- Sensor: Sensirion SHT40 (or the SHT4x family member in JLC stock) on I2C with
  pull-ups; give it a thermal isolation slot/cutout or at least keep it away
  from the LDO and MCU heat.
- Interfaces: 4-pin SWD header (0.1 in), 4-pin UART header (0.1 in: GND, 3V3,
  TX, RX) for readout/logging, one Qwiic/STEMMA-QT connector (JST SH 1.0 mm
  4-pin, GND/3V3/SDA/SCL) sharing the sensor I2C bus.
- One user LED (GPIO, series resistor) and one power LED.
- 2 layers, 1.6 mm FR-4, HASL, green; JLC economy PCBA for the SMD parts,
  prototype qty 5. Prefer JLC Basic parts; Extended parts only where the brief
  names the part (MCU, sensor, connectors).
- Size: whatever an honest layout wants, roughly 35 x 25 mm or smaller; four
  M2 mounting holes if they fit without hurting the layout.
- No battery, no mains, no USB data, no RF.
