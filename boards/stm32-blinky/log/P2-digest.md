# P2 digest (stm32-blinky)
6 blocks: J1 5V -> D1 SS34 Schottky -> U2 AMS1117-3.3 -> U1 STM32F103C8T6
(LQFP-48) + Y1 8MHz crystal + D2 LED on PC13 (1k, 1.3mA sink) + J2 SWD.
Stackup JLC2313_1.6 2L, target 35x30mm, B.Cu GND pour. Single flat sheet.
J1 left edge, J2 right edge (constraints placement.edges). Nets canonical.
Cost ~$35-50 for 5 assembled; STM32 is the one Extended part.
Risk: Schottky headroom at 4.5V low-line+100mA abuse (fine at real ~40mA);
P-FET AO3401A is the drop-in escalation.
