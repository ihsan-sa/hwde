# Requirements: usb-buck

## 1. Function
USB-powered STM32 device board. STM32F103C8T6 MCU (clocked from an 8 MHz
crystal) runs USB 2.0 full-speed device firmware, talking to a host over a
micro-B USB connector that also supplies board power. Onboard status LED and
user button give minimal local UI/debug feedback; a 4-pin SWD header supports
programming and debugging. Compact prototype/dev board, build qty 10.
Note: brief requests a hierarchical schematic (e.g. power/mcu/usb sheets)
unless the architect judges a flat schematic clearly better - carried
forward as a directive for the architecture stage, not a board requirement.

## 2. Interfaces
- USB: USB 2.0 full-speed DEVICE (stated). Connector: micro-B (stated).
  D+/D- wired to the MCU's fixed USB pins - PA11 (D-) / PA12 (D+) on the
  STM32F103C8T6 (verified against part datasheet references). Device only:
  no host, hub, or OTG function.
- SWD: 4-pin header for programming/debug (stated). ASSUMED: standard
  minimal SWD-only pinout - SWCLK, SWDIO, GND, 3V3 reference (no NRST, no
  SWO); 2.54 mm pitch, unshrouded pin header. Low risk - architect picks
  exact pin order and silkscreen labels it.
- User I/O (onboard, no external connector):
  - 1x status LED, GPIO-driven. ASSUMED: color/pin is architect's choice,
    cosmetic only.
  - 1x user button, GPIO input. ASSUMED: generic application input (not
    BOOT0/bootloader select, not NRST/reset) - brief calls it "user
    button" distinctly from any programming function.

## 3. Power
- Source: USB VBUS only. No battery, no charging, no mains input.
- Input: 5V nominal (USB spec range ~4.75-5.25V). Budget: 500mA-class
  (standard USB downstream port; no PD/QC negotiation implied or needed).
- Regulation: AP63203 buck converter, VBUS (5V) -> 3.3V rail (stated,
  named part). NOTE: this explicit part name overrides the general
  "prefer JLC Basic parts" preference for this one IC; architect verifies
  sourcing (JLC Basic/Extended/LCSC) and applies the Basic-parts
  preference to every other part.
- Rail budget (GUESS, for architect sizing only): MCU active ~50mA, LED
  ~5-10mA, misc pull-ups/passives ~5mA -> well under 150mA on the 3.3V
  rail. Comfortably inside both the buck converter's and the USB port's
  capability.

## 4. Environment
Not stated. ASSUMED: indoor bench/lab prototype use, ordinary room ambient
(roughly 0-40C), no enclosure, no ingress protection, no vibration/shock
requirement. Low risk - qty-10 prototype board, easy to revisit.

## 5. Size & mounting
- Outline: max 55x45 mm (stated).
- Mounting holes: not stated. ASSUMED: none required (bare board, no
  enclosure per Environment).
- Height limit: not stated. ASSUMED: no restriction (open board, no
  enclosure).

## 6. Quantity & budget
- Build quantity: prototype qty 10 (stated). ASSUMED: one-off prototype
  run - no follow-on production volume implied or planned for.
- Target unit cost: no number stated. ASSUMED: no hard cap; cost is
  minimized via the stated strategy (JLC Basic parts preference + JLCPCB
  economy PCBA tier) rather than a fixed target.

## 7. Assembly
- JLCPCB PCBA, economy tier (stated).
- Parts: prefer JLC Basic library (stated), except AP63203 which is
  explicitly named (see Power note).
- Connectors: "hand-solderable connectors acceptable" (stated). ASSUMED
  interpretation: USB micro-B and/or the SWD header may be hand-soldered
  post-PCBA instead of placed by JLC assembly, if that is cheaper or
  simplifies sourcing; architect decides per part availability.
- Sidedness: not stated. ASSUMED: single-sided (top-only) SMT assembly -
  small part count and board size make this the simpler/cheaper default;
  architect may move to double-sided if placement requires it.

## 8. Compliance/safety flags
None apply:
- Mains voltage: no - USB-powered only, 5V max input.
- Batteries: no.
- Motors: no.
- >30V: no - max voltage on board is 5V (VBUS), stepped down to 3.3V.
- High current (>3A): no - USB 500mA-class budget; actual estimated draw
  well under 150mA.
- RF transmit: no - USB device function only, no radio.

## 9. Open questions
1. Target unit cost: is there a hard per-unit cost cap, or is "minimize
   via JLC Basic parts + economy PCBA" (the stated strategy) sufficient
   without a specific number?
   DEFAULT: no hard cap; stated strategy stands.
2. Enclosure / mounting: will this board be mounted in an enclosure or
   chassis (needing mounting holes and/or a height limit), or is it a
   bare bench-use board?
   DEFAULT: bare board, no mounting holes, no height limit.

## Answers (P0 batch, AUTO-approved defaults per user directive)
1. Unit cost: no hard cap; JLC Basic + economy PCBA strategy stands.
2. Bare bench-use board: no mounting holes, no height limit.
