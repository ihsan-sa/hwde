# P2 Architecture digest - lumina-par

Artifact: `architecture/` (blocks.md, power_tree.md, stackup.md, sheets.md,
constraints.json, decisions.md). This is the H1 checkpoint package.

- **6 blocks**: rail entry (48 V landed on J3 but NOT tapped), ENABLE gating,
  4x TPS92515HV-class CC buck with a shunt FET per channel, window-comparator
  over-temperature protection, ID divider + I2C EEPROM, 10-way LED harness.
  Emitters off-board on an aluminium MCPCB.
- **Stackup JLC04161H-3313, 4 layers**, 100.0 x 80.0 mm, 1.6 mm. Drivers: switch-node
  containment 11 mm above a live 2.4 GHz antenna, a continuous GND reference under
  jitter-sensitive PWM, B.Cu consumed by two reverse-mounted sockets, ~120 parts in
  ~45 cm2. No controlled-impedance net exists on this board.
- **Design point 150 mA/die, 4 packages, 2S2P per channel.** Full white (the
  stuck-PWM hardware backstop) = 0.718 A on +12V: 4 % under the sustained ceiling
  and 2.8x under OCP. The board is electrically incapable of exceeding its budget.
  The >3 A conditional flag is CLOSED - max per-channel current is 0.30 A.
- **C1 arbitrated to +12V**, and the P1 argument for 48 V was withdrawn rather than
  overruled. The "48 V gives 16x faster slew" claim held the inductor fixed across a
  4x change in (Vin - Vs). With L sized for the same ripple fraction, t_r + t_f =
  1/(f*k) - the rail voltage cancels out of the algebra. Verified independently by
  the orchestrator: 4.762 us on BOTH rails at 700 kHz / k=0.30 (48 V only
  redistributes 3.81/0.95 us between rise and fall). That is 33.8x the 141 ns
  budget, so no rail or inductor choice reaches PAR-REQ-01 by gating the converter.
- **C2 resolved: shunt-FET dimming closes the timing wall (T ~ 50-100 ns vs 141 ns,
  1.4-2.8x margin); the resolution wall is NOT closable on this board** and needs
  carrier firmware dithering (CR-5). spec-dimming's "local >=16-bit PWM IC" class
  LOSES to led-driver's six-part survey of that exact class - no part delivers
  >=150 mA/ch AND >=10 kHz AND useful resolution AND independent channels.
- **Cost ~$18-23/board** delivered (BOM ~$12.9, driver silicon 52 %) against a
  $25-35 target; module + heatsink adds $8-14/fixture.
- **Sealed enclosure does not close** with the module inside (9.15 W -> 62 C air
  against a 45 C criterion). It closes vented, or sealed with LED heat conducted
  through the wall (3.21 W -> 38 C). Seven ENC-x acceptance criteria written for
  whoever owns the enclosure, since it is not this board's deliverable.
- Riskiest decision: **emitters off-board on MCPCB (D3)** - the thermal argument
  rests on an ASSUMED 12 K/W package Rth, because the vendor publishes neither Rth
  nor Tj max, and it is the only in-stock RGBW power emitter on LCSC. At 20 K/W even
  MCPCB is marginal at af.
- Two P5 traps recorded: fixed-outline board_init derives its origin from the packed
  component bbox (every rect in constraints.json needs a P5 translation), and the
  antenna column has no automated checker on F.Cu/B.Cu.
