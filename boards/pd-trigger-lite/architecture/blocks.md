# pd-trigger-lite - blocks

One flat sheet, three blocks. No regulation and no series element in the power path:
the receptacle's VBUS IS the output pad's VBUS (one net end to end).

## B1 input + output (J1, J2)
- J1 USB-C receptacle, 6-pin power-only (C2798175, USAKRO TYPE-C-6M-001, 3 A / 20 V
  rated): VBUS A9+B9, GND A12+B12, CC1 A5, CC2 B5, 4 shell stakes to GND. No D+/D-
  contacts exist on a 6P part, so the controller's DP/DM stay unconnected (PD needs CC only).
- J2 two plated 2.54 mm-pitch through-holes: pin 1 VBUS, pin 2 GND. Not assembled
  (board feature); the owner solders wires or a 1x2 header.
- VBUS path rated 3 A continuous (no e-marker; the cable caps the contract at 3 A).

## B2 PD sink controller (U1, C1)
- U1 CH224A (C42459160, WCH manual V2.1): pin 1 VHV straight from VBUS (32 V abs max) with
  C1 1 uF/50 V X5R at the pin; pin 8 VBUS sense shorted to VHV (table 4-1: "short to VHV");
  CC1/CC2 direct to J1 (Rd integrated); DP/DM, PG, CFG2, CFG3 unconnected (5.2.1: CFG2/3
  may float in single-resistor mode; they have internal pull-ups). Pad 11 = baseplate = GND.

## B3 voltage select (R1-R4, R5, JP1-JP3)
- Single-resistor (Rset) mode, table 5-1: CFG1 to GND through 6.8k = 9 V, 24k = 12 V,
  56k = 15 V, 120k = 20 V. Each Rset sits in series with its own link to GND:
  9 V JP1, 12 V R5 (0R, fitted), 15 V JP2, 20 V JP3. Exactly one link closed.
  To change voltage: remove R5 with an iron, bridge one solder jumper.
- CFG1 abs max is 3.8 V; nothing on the net exceeds the chip's own bias.

## B4 indicator (D1, R6)
- D1 red 0603 LED + R6 10k from VBUS: 0.3 mA at 5 V (dim = no PD contract), 1 mA at 12 V,
  1.8 mA / 33 mW at 20 V. Brightness itself tells a 5 V fallback from a negotiated rail.
