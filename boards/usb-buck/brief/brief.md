# Brief: usb-buck (S14 run b)

A 4-layer STM32 USB device board:
- STM32F103C8T6 MCU, 8 MHz crystal, SWD header (4-pin)
- USB micro-B connector, USB 2.0 full-speed DEVICE on the MCU's USB pins
- Powered from USB VBUS (5V) through an AP63203 buck converter to 3.3V
- One status LED on a GPIO; one user button
- JLCPCB 4-layer, economy PCBA, max 55x45 mm, prototype qty 10
- Prefer JLC Basic parts; hand-solderable connectors acceptable
- Structure the schematic hierarchically (e.g. power / mcu / usb sheets)
  unless the architect judges flat clearly better
