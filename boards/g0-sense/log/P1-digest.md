# P1 Research digest - g0-sense (2026-08-27)

Roster (8 agents): 4x research-component-scout (ldo, protection, connectors,
mcu-sensor), research-interface-spec (usbc-power-sink), 2x
research-reference-design (sht4x, stm32g030-minimal), research-power-architect.

Load-bearing findings
- USB-C CC-blind sink (fixed 5.1k Rd on CC1 AND CC2, independent - never one
  shared resistor) is entitled to DEFAULT USB power only: budget <= 500 mA.
  Sink capacitance at the receptacle <= 10 uF (TC2.0 Table 4-3).
- Rail tree: VBUS -> TVS -> PTC -> +5V -> LDO -> +3V3. +3V3 peak 185 mA
  (incl. 100 mA Qwiic reserve + 75 mA SHT4x heater), 240 mA with 30% headroom.
  VBUS worst draw 196 mA = 39% of entitlement.
- LDO: AMS1117-3.3 SOT-223 (C6186, Basic) beats SOT-23-5 low-Iq parts on the
  only axis that decides: Tj 71-86 C vs 134 C at 40 C ambient, 0.51 W case.
  Needs a 22 uF TANTALUM-class output cap (not plain ceramic) - carry to P3/P4.
  Dropout closes at the 4.75 V corner with +0.11 V worst-case margin.
- STM32G030F6P6 TSSOP-20: VDD/VDDA bonded to pin 4, VSS/VSSA pin 5, no separate
  VREF+. BOOT0 needs NO strap - factory nBOOT_SEL=1/nBOOT0=1 always boots main
  flash, and BOOT0 shares pin 19 with SWCLK anyway. NRST needs only 100 nF + the
  button (internal pull-up 40k typ). Pin map: SWD PA13/PA14, USART2 PA2/PA3,
  I2C1 PA9/PA10 (5 V tolerant, Fm+), LED PA5. 9 of 20 pins used, no conflicts.
- SHT4x: 100 nF at VDD, 2.2k I2C pull-ups (sized for a 0.5 m Qwiic leg), copper
  conduction is the dominant self-heating path -> distance + necked traces +
  no pour under the part + a milled slot. NO BOARD WASH (Sensirion forbids it)
  -> must appear in the fab/assembly notes. Fixed I2C address per variant.
- MCU + sensor are both JLC EXTENDED (no Basic exists in either family):
  STM32G030F6P6 C724040 $1.37, SHT40-AD1B-R2 C2909890 $1.90 (addr 0x44).

7 OPEN questions answered and recorded as decisions (LDO design point + part;
TVS clamp ceiling dropped as an over-tight derived spec; no reverse-polarity
element; USB-C THT legs verified OK in JLC Economic tier; heater budgeted;
button size vs Basic; LED colours). Gates: none due at P1.
