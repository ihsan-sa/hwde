# Requirements: stm32-blinky

Source: `brief/brief.md` (S14 run a). No other attachments.
Unstated low-risk items are marked `ASSUMED:` inline; design-changing unknowns
are in section 9.

## 1. Function

A minimal 2-layer STM32 development "blinker" board: an STM32F103C8T6 MCU
clocked from an 8 MHz crystal, driving one user LED from a GPIO. Programmed
and debugged over a 4-pin SWD header. Powered from an external 5 V supply via
a 2-pin header, regulated to 3.3 V by an AMS1117-class LDO. No USB, no
battery, no radio. Firmware (the blink program) is out of scope for the
hardware pipeline; the board must be flashable by the user over SWD.

## 2. Interfaces

| Interface | Details |
|---|---|
| 5 V power input | 2-pin pin header. ASSUMED: 2.54 mm male header, polarity marked on silkscreen. |
| SWD debug | 4-pin header (SWDIO, SWCLK, 3V3, GND). ASSUMED: 2.54 mm single-row male, ST-Link-compatible pin order. Programming interface for the user; no NRST pin on a 4-pin header (reset via SWD/power cycle). |
| User LED | 1x LED on an MCU GPIO, with series resistor. ASSUMED: any standard-color LED available as a JLC Basic part; GPIO chosen at architecture stage. |
| None else | No USB, no RF, no buttons stated (see Q2 to confirm the omissions are intentional). |

## 3. Power

- Input: 5 V nominal on the 2-pin header. ASSUMED: pre-regulated external
  supply, 4.5-5.5 V; no wider input range required.
- Regulation: single 3.3 V rail from an AMS1117-class LDO (stated).
- Rail budget (GUESS, to be confirmed at architecture): MCU worst-case
  ~40-60 mA, LED ~2-10 mA, total under 100 mA on 3.3 V. AMS1117-class parts
  (~800 mA) give ample margin; dissipation at 5 V -> 3.3 V, 100 mA is
  ~0.17 W - trivial, no thermal concern.
- No battery, no charging (stated).
- Reverse-polarity protection on the unkeyed 2-pin input: not stated - see Q1.

## 4. Environment

Not stated. ASSUMED: indoor bench/prototype use, commercial ambient
(0-70 C), no enclosure, no ingress/vibration/condensation requirements.

## 5. Size & mounting

- Outline: 50 x 40 mm maximum ("roughly 50x40 mm or smaller"); treat 50 x 40
  as the hard limit and smaller as preferred.
- Height: no limit stated. ASSUMED: none (pin headers dominate height).
- Mounting holes: not stated - see Q2 (default: none).

## 6. Quantity & budget

- Build quantity: 5 prototypes (stated). ASSUMED: all 5 assembled, not
  bare-PCB-only.
- Target unit cost: not stated. ASSUMED: no hard cap; the stated economy
  PCBA + Basic-parts preference already expresses "minimize cost".

## 7. Assembly

- JLCPCB, 2-layer board, JLC economy PCBA (stated).
- ASSUMED: single-sided (top) SMT assembly, consistent with the economy
  service.
- ASSUMED: the two THT pin headers may be shipped loose / hand-soldered by
  the user if JLC economy through-hole assembly is unavailable or adds
  disproportionate cost for qty 5.
- Parts: prefer JLC Basic parts throughout (stated). ASSUMED: the explicitly
  specified STM32F103C8T6 overrides the Basic-parts preference if it is only
  stocked as an Extended part; the preference applies to all passives and
  support parts.

## 8. Compliance/safety flags

None apply: no mains, no battery, no motors, maximum voltage on board is
5 V (< 30 V), currents well under 3 A, no RF transmitter.

## 9. Open questions

1. Reverse-polarity protection: the 2-pin 5 V header is unkeyed and can be
   plugged in backwards, which would likely destroy the board. Add a
   protection diode? It adds one cheap Basic part and slightly reduces
   regulator headroom (still fine from a 5 V supply at this load).
   Default: yes, add it.
2. The brief reads as deliberately minimal. Confirm that NONE of the
   following commonly-added extras are wanted: reset button, BOOT0/bootloader
   jumper, power-indicator LED, mounting holes. Default: none of them (keep
   the board minimal as briefed). If you do want any, name them.

## Answers (P0 batch, user-approved 2026-07-27)

1. Reverse-polarity protection: YES - add a series protection element (Schottky
   diode or P-FET, JLC Basic part) on the 5V input before the LDO.
2. Extras: NONE - no reset button, no BOOT0 jumper, no power LED, no mounting
   holes. Board stays as briefed.
Checkpoint policy note: H3 (placement render) folds into H4 for this run.
