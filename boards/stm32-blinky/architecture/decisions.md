# stm32-blinky - P2 architect decisions (for the orchestrator log)

1. Stackup `JLC2313_1.6` (JLC standard 2-layer 1.6 mm, 1 oz, HASL); board
   class 2L economy; target outline 35 x 30 mm inside the 50 x 40 limit.
   No controlled impedance (nothing on the board needs it; 2L offers none).
2. Reverse protection = series Schottky SS34 (SMA, Basic). REJECTED: P-FET
   (AO3401A) - extra headroom not needed at real loads and the diode has no
   orientation/gate subtleties; documented residual risk: at 4.5 V low-line
   AND the 100 mA abuse envelope, LDO margin is typ-only. Escalation is a
   drop-in footprint swap to the P-FET.
3. User LED on PC13, ACTIVE-LOW sink, R1 = 1 k (~1.3 mA): honors ST DS5319's
   3 mA / no-sourcing limit on PC13 while keeping the Blue Pill firmware
   convention. REJECTED: sourcing from a regular GPIO (breaks the ecosystem
   convention for no electrical gain).
4. Single flat root sheet; hierarchy rejected as pure drift risk at 18
   components. Full refdes map pinned in sheets.md (U1/U2, J1/J2, D1/D2, Y1,
   R1/R2, C1-C9) because constraints.json and decoupling.json reference
   specific refdes - these are contractual for P4.
5. Canonical nets locked: +5V (post-diode), +3V3, GND bare; /VIN, /SWDIO,
   /SWCLK, /LED, /LED_A, /OSC_IN, /OSC_OUT, /NRST, /BOOT0 local. J2 pin
   order 1=SWDIO 2=SWCLK 3=3V3 4=GND; J1 1=+5V 2=GND.
6. Crystal nets declared high_speed with GND reference (golden-blinky2
   precedent): buys the return-path check plus a guaranteed B.Cu GND pour
   under the oscillator for free.
7. Decoupling set matched to the proven blinky2 golden (3x100nF VDD + 100nF
   VDDA + 2x10uF LDO + 100nF NRST + 2x22pF load). AN2586's extra 1 uF VDDA
   pair and dedicated 4.7 uF bulk WAIVED: no analog use, tiny board, LDO
   output cap doubles as bulk. Revisit only if a spin uses the ADC.
8. Lead parts: STM32F103C8T6 LQFP-48 (C8734, the single Extended part -
   brief-specified override), AMS1117-3.3 SOT-223 (C6186), SS34 (C8678),
   8 MHz HC-49S SMD CL=20pF (C32828 candidate), red LED + generic Basic
   passives, 2.54 mm THT headers (hand-solder fallback). LCSC codes are
   candidates for P3 verification - research phase was skipped by recorded
   P1 decision.
9. Copper sizing current_a = 0.3 A on all supply nets (3x envelope; floor
   widths anyway). No thermal/voltages/planes constraint entries - budgets
   in power_tree.md show they would no-op (max 5 V, worst dissipation
   ~0.08 W design).
