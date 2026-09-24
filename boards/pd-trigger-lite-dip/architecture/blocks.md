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

## B3 voltage select (SW1, R1-R5)
- SW1 = 5-position 1.27 mm SMD DIP switch (C7421518), used one-hot. One side of every switch
  is CFG1; the other goes to that position's resistor.
- Pos1 5 V: R5 100k to VHV pulls CFG1 high (I/O mode, manual table 5-2 + 6.1.2; CFG2/3 don't care).
- Pos2-5 9/12/15/20 V: 6.8k / 24k / 56k / 120k to GND (single-resistor mode, table 5-1).
- CFG2/CFG3 float (internal pull-ups). Exactly one switch ON, set before plugging in. All off
  leaves CFG1 floating; two on at once is not allowed (pos1 with an Rset can push CFG1 past
  its 3.8 V max once VHV rises).

## B4 indicator (D1, R6)
- D1 red 0603 LED + R6 10k from VBUS: 0.3 mA at 5 V (dim = no PD contract), 1 mA at 12 V,
  1.8 mA / 33 mW at 20 V. Brightness itself tells a 5 V fallback from a negotiated rail.
