# Reference-design research: stm32g030-minimal

Block: minimum-correct STM32G030F6P6 (TSSOP-20) subsystem, 3.3 V rail, internal
oscillator (no crystal), SWD header, UART header, I2C bus, one user LED, NRST
button, BOOT0 handled. Sources are primary ST documents, fetched and text-
extracted (pypdf) from mirror hosts after st.com itself timed out in this
sandbox; content verified as the genuine ST document by title/rev/date on
page 1 of each PDF. Local KiCad symbol library used as an independent
cross-check of the pin-table transcription.

Primary sources used:
- **[DS]** STMicroelectronics, *STM32G030x6/x8* datasheet, **DS12991 Rev 4**
 (Jan 2022). Canonical URL: st.com/resource/en/datasheet/stm32g030c6.pdf
 (fetched via resources.ampheo.com mirror, content verified as DS12991 R4).
- **[RM]** STMicroelectronics, *RM0454 - STM32G0x0 advanced Arm-based 32-bit
 MCUs* reference manual, **Rev 2** (Apr 2019). Canonical URL:
 st.com/resource/en/reference_manual/rm0454-stm32g0x0-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
 (fetched via an aliyuncs.com mirror). Note: st.com's current copy is Rev 5
 (Nov 2020); the boot-configuration mechanism (Section 2.5, Table 5) and the
 option-byte layout (Section 3.4.1) are architectural and unchanged across
 revisions - cross-checked against the errata sheet and a community thread
 below, both consistent with Rev 2's text.
- **[ES]** STMicroelectronics, *STM32G030x6/x8 device errata*, **ES0486 Rev 2**
 (Jan 2020), full 15 pages read (fetched via datasheet.sisoog.com mirror).
- **[KiCad]** `/usr/share/kicad/symbols/MCU_ST_STM32G0.kicad_sym`, symbol
 `STM32G030F6Px` (ships with KiCad 10, sourced from ST data) - used only to
 cross-check the pin-number/pin-name transcription from [DS] Table 12; not
 used as a design-decision source.
- **[Community]** community.st.com thread "STM32G030 ... does not enter
 bootloader when boot0 is 3.3V" - secondary, corroboration only, cited where
 used.

**Not obtained**: AN5096 "Getting started with STM32G0 Series hardware
development". st.com timed out for every document in this session; AN5096
specifically also 403'd on two mirrors (electrodragon, manuals.plus) and
scribd only exposed a content-free preview. Everything AN5096 would normally
provide for this block (decoupling, NRST, BOOT0) was independently obtained
from [DS]/[RM]/[ES] instead (see below); the one gap is a board-level SWD
4-pin header convention and an explicit "large NRST cap vs SWD" warning - 
flagged as OPEN, not blocking.

## Decisions

### Decoupling
[DS] Section 3.7.1: on packages without a separate VDDA pin, "VDDA voltage
level is identical to VDD ... provided externally through VDD/VDDA pin"; and
explicitly for VREF+: "On packages without VREF+ pin, VREF+ is internally
connected with VDD." [DS] Table 12 confirms TSSOP-20 has **no separate VDDA or
VREF+ pin** - pin 4 is the single bonded `VDD/VDDA` pin, pin 5 is the single
bonded `VSS/VSSA` pin (SO8N/LQFP32 also bond these; only LQFP48 has separate
VDDA(pin6)/VREF+(pin5)/VBAT(pin4) pins).

[DS] Section 5.1.6 "Power supply scheme" (Figure 9) + its Caution note is ST's
own recommended decoupling network: **1x 100 nF ceramic + 1x 4.7 uF** across
the VDD/VDDA-to-VSS/VSSA pin pair, "placed as close as possible to, or below,
the appropriate pins on the underside of the PCB". Section "General PCB design
guidelines" (p.70) repeats: "The 100 nF capacitor should be ceramic (good
quality) and it should be placed as close as possible to the chip."

Because TSSOP-20 has exactly one VDD/VDDA pin pair, this reduces to **one**
100 nF + one 4.7 uF network total (not per-pin-pair multiplication as on the
LQFP48 variant, which has separate VBAT/VREF+ pins with their own decoupling
in Figure 9). No VREF+ decoupling cap is needed on this package since VREF+
doesn't exist as a separate pin here.

### NRST
[DS] Section 5.3.15 + Table 52: "The NRST input driver ... is connected to a
permanent pull-up resistor, RPU" - internal, always present, RPU = 25-55 kOhm
(typ 40 kOhm). **No external pull-up resistor is required or useful.**

[DS] Figure 19 "Recommended NRST pin protection" shows ST's own minimal
network: internal RPU + a single **0.1 uF (100 nF)** filter capacitor
NRST-to-GND, with an optional "external reset circuit" block (a push button or
supervisor IC) in parallel. Notes on the figure: (2) the external circuit
must be able to pull NRST below VIL(NRST)max or "the reset will not be taken
into account", (3) "the external capacitor on NRST must be placed as close as
possible to the device." A momentary push button from NRST to GND, plus the
100 nF cap, is exactly this recommended circuit - no other components needed.

**Footgun (partially unverified)**: ST's own recommended value is small
(100 nF); that value is unlikely to interact with a debug probe's reset
control. The much-discussed community failure mode - oversized NRST caps
(1-10 uF, sometimes added for extra debounce/EMI margin) slowing the RC decay
enough that ST-Link/J-Link "connect under reset" or rapid flash-cycle resets
time out - is real and widely reported in the STM32 community, but I could
not find it stated in an ST primary source in this session (AN5096 likely
covers it; unreachable - see OPEN). **Recommendation: use ST's own 100 nF
value on NRST; do not oversize it.**

### BOOT0 (highest-value item; cross-checked against 3 independent sources)
[DS] Table 12: on TSSOP-20, **pin 19** is a bonded `PA14-BOOT0 / PA15` pin.
PA14's alternate functions are `SWCLK, USART2_TX`; its "Additional functions"
column lists `ADC_IN18, BOOT0` - **BOOT0 is sampled on the same physical pin
as SWCLK**, not a dedicated pin (confirmed independently in the KiCad
`STM32G030F6Px` symbol: pin 19 name `PA14/PA15`, alternates include
`SYS_SWCLK (PA14)`).

[RM] Section 2.5 "Boot configuration", Table 5 "Boot modes" (the authoritative
table) - boot area is selected by `nBOOT1`, the `BOOT0 pin`, `nBOOT_SEL`, and
`nBOOT0` (all bits live in the FLASH option byte, Section 3.4.1, Table 9,
address `0x1FFF7800`):

| nBOOT1 | BOOT0 pin | nBOOT_SEL | nBOOT0 | Boot area |
|---|---|---|---|---|
| x | 0 | 0 | x | Main Flash |
| 1 | 1 | 0 | x | System memory |
| 0 | 1 | 0 | x | Embedded SRAM |
| x | x | **1** | **1** | **Main Flash** |
| 1 | x | 1 | 0 | System memory |
| 0 | x | 1 | 0 | Embedded SRAM |

[RM] Section 3.4.1 states ST's production (factory) value of this option byte
is `0xDFFF E1AA`. Decoding bits 26/25/24 (nBOOT0/nBOOT1/nBOOT_SEL) from that
word: **nBOOT_SEL=1, nBOOT0=1, nBOOT1=1** - i.e. the factory-default row is
the 4th one above: **boot always goes to Main Flash memory, and the physical
BOOT0 pin/PA14 state is completely ignored.**

[ES] Section 2.2.3 independently reinforces the same conclusion from the
opposite direction - it is an erratum, but its "workaround" line is the
load-bearing fact: *"Under Level 1 read protection, booting from Main Flash
memory selected through PA14-BOOT0 pin is not functional ... Booting from Main
Flash memory operates correctly if selected through option bits (nBOOT_SEL and
nBOOT0 both set)."* I.e. ST's own errata sheet says the option-bit path (the
factory default) is the *more* robust one, not just the default one.

A community thread **[Community]** (secondary, corroboration only) states the
same in plain language for STM32G0: "the Boot0 pin functionality is disabled
by default... the microcontroller will always boot from the main flash memory
regardless of the Boot0 pin state."

**RECOMMENDED minimal handling for this board (SWD-only, never needs the
system bootloader): do nothing.** Leave the option bytes at ST's factory
default (`nBOOT_SEL=1, nBOOT0=1`). PA14/pin 19 is wired only as SWCLK (see
SWD below) with no pull resistor, no jumper, no strap - none is needed because
the boot-area decision no longer consults that pin. This is also the
electrically simpler choice on this package, since pin 19 is *already* shared
with SWCLK and PA15; adding a strap to it would fight the SWD function.

**What changes if the user wants the UART bootloader** (relevant - this board
has a UART header): the system bootloader is entered by making the boot area
"System memory". With the factory-default `nBOOT_SEL=1` in place, that only
requires setting `nBOOT0=0` - a **pure option-byte rewrite over the existing
SWD connection** (e.g. via STM32CubeProgrammer's Option Bytes tab), with zero
extra hardware. No jumper or pull-down needs to be designed onto the board for
this. (The alternative - reverting to legacy pin mode, `nBOOT_SEL=0`, and
strapping PA14 - is deliberately NOT recommended here: it would contend with
PA14's SWCLK duty and gains nothing the option-byte route doesn't already
give for free.) [RM] Section 2.5 also confirms the bootloader's own USART
pins are `PA2/PA3` or `PA9/PA10` (STM32G070xx adds PC10/PC11) and I2C pins are
`PB6/PB7` or `PB10/PB11` - see UART decision below for why `PA2/PA3` was
chosen for the header, which is not a coincidence.

### SWD
[DS] Table 12: **SWDIO = PA13 (pin 18)**, standalone/unbonded pin.
**SWCLK = PA14 (pin 19)**, bonded with PA15 and with BOOT0 (see above) - using
this pin as SWCLK is the *only* use it needs; PA15's alternate functions
(SPI1_NSS, USART2_RX) are simply not used on this board.

Footnote (5) on Table 12 is directly useful: *"Upon reset, these pins are
configured as SW debug alternate functions, and the internal pull-up on PA13
pin and the internal pull-down on PA14 pin are activated."* **No external
pull-up/pull-down or series resistor is required on SWDIO/SWCLK** - the
silicon does it automatically, on every reset, unconditionally.

Header convention: **OPEN / opinion, not a cited vendor standard.** ST's own
debug connectors (e.g. Nucleo boards' CN4) are 6-pin and include NRST + SWO,
which this board's 4-pin (GND/3V3/SWDIO/SWCLK only, per requirements.md's
existing ASSUMED set) does not carry - I found no ST document defining a bare
4-pin 0.1" SWD header pinout, and could not retrieve AN5096 to check whether
it defines one. Recommendation (opinion): keep the requirements.md ASSUMED
signal set (GND, 3V3, SWDIO, SWCLK - no NRST, no SWO); most third-party SWD
probes (ST-LINK, J-Link, Black Magic Probe) support 4-wire SWD without a
dedicated NRST wire (the target's own power-on reset and the debugger's
software reset-via-AIRCR are normally sufficient), so dropping NRST/SWO from
the header is not a functional problem. Silkscreen pin 1 clearly since there
is no external standard to rely on.

### UART
[DS] Table 12 / KiCad symbol: **USART2 on PA2 (pin 9, TX) / PA3 (pin 10, RX)**
is the natural choice - both are standalone, unbonded pins with no conflict
against SWD (PA13/14) or the I2C pins chosen below (PA9-11/PA10-12). This
also lines up with [RM] Section 2.5's statement that the embedded bootloader's
USART interface listens on `PA2/PA3` (or `PA9/PA10`) - picking `PA2/PA3` for
the header means the *same* 4-pin UART header doubles as the system-bootloader
UART interface with zero extra hardware, directly answering the "what if the
user wants the UART bootloader" question from a different angle than BOOT0
alone. TX/RX naming follows requirements.md's existing ASSUMED convention
(MCU-perspective: header TX = PA2 = MCU transmit).

### I2C
[DS] Table 12: TSSOP-20 pin 16 is bonded `PA9/PA11`, offering `I2C1_SCL (PA9)`
or `I2C2_SCL (PA11)`; pin 17 is bonded `PA10/PA12`, offering `I2C1_SDA (PA10)`
or `I2C2_SDA (PA12)`. **Recommend I2C1 on PA9 (SCL, pin 16) / PA10 (SDA, pin
17)** - I2C1 is the peripheral the datasheet's feature list calls out as
"supporting SMBus/PMBus and wakeup from Stop mode" (feature list, p.1), the
more capable of the two instances for a bus that's also exposed off-board via
Qwiic.

I/O structure column in Table 12 for these pins is `FT_f` / `FT_fa`: per
Table 11's legend, `FT` = 5 V-tolerant, `_f` = "I/O, Fm+ capable" (Fast-mode
Plus, 1 Mbit/s). So **PA9/PA10 (and the PA11/PA12 alternate) are 5 V-tolerant
and Fm+-capable.** When configured for the I2C alternate function, firmware
sets the pin's output type to open-drain (standard STM32 GPIO architecture,
`GPIOx_OTYPER`) - genuine open-drain, correct for a shared/multi-drop bus with
external pull-ups (the Qwiic connector's downstream devices).

**Errata to flag for firmware, not hardware** (do not change the topology):
[ES] 2.8.1 wrong SDA sampling if the transmitter's data setup time is shorter
than one I2C kernel-clock period (has a minimum-I2CCLK-frequency workaround);
2.8.2 spurious BERR in master mode (software must just clear the flag); 2.8.3
spurious master transfer on own-slave-address-match in a multi-master
scenario (not applicable here - this board is the only master on its local
I2C1 bus; only matters if a Qwiic downstream device also masters the bus,
which the Qwiic spec doesn't do).

### Pin budget check (TSSOP-20, all 20 pins - [DS] Table 12, cross-checked
against the KiCad `STM32G030F6Px` symbol pin-for-pin)

| Pin | Name (bonded group) | Assignment |
|---|---|---|
| 1 | PB7 / PB8 | spare (unused) |
| 2 | PB9 / PC14-OSC32_IN | spare (unused - no crystal on this board) |
| 3 | PC15-OSC32_OUT | spare (unused - no crystal) |
| 4 | VDD/VDDA | **power in** (3.3 V + 100 nF + 4.7 uF) |
| 5 | VSS/VSSA | **power in** (GND) |
| 6 | NRST | **NRST** (100 nF + push button to GND; internal RPU) |
| 7 | PA0 | spare (unused) |
| 8 | PA1 | spare (unused) |
| 9 | PA2 | **USART2_TX** (UART header TX) |
| 10 | PA3 | **USART2_RX** (UART header RX) |
| 11 | PA4 | spare (unused) |
| 12 | PA5 | **user LED** GPIO, via series resistor |
| 13 | PA6 | spare (unused) |
| 14 | PA7 | spare (unused) |
| 15 | PA8 / PB0 / PB1 / PB2 | spare (unused) |
| 16 | PA9 / PA11 | **I2C1_SCL** (I2C bus to sensor + Qwiic) |
| 17 | PA10 / PA12 | **I2C1_SDA** |
| 18 | PA13 | **SWDIO** |
| 19 | PA14 / PA15 | **SWCLK** (= BOOT0 pin, unstrapped - see BOOT0) |
| 20 | PB3 / PB4 / PB5 / PB6 | spare (unused) |

**No conflicts.** Required functions (power x2, NRST, SWD x2, UART x2,
I2C x2, LED x1 = 9 pins) fit comfortably with 10 physical pins/groups spare
for margin - e.g. a future feature, a test point, or (per [RM] 2.5) the
alternate I2C-bootloader pins PB6 (pin 20) / PB7 (pin 1) if the I2C bootloader
is ever wanted instead of the UART one.

## Errata (full list read; only hardware/topology-relevant ones summarized above are actionable for this block)
See [ES] ES0486 Rev 2 for the complete list (15 pages, all read). Items with
no hardware implication for this block (DMA, DMAMUX, ADC channel-sequencing,
TIM16/17 clocking, RTC init timing, SPI BSY flag) are omitted here as
out-of-scope for a minimal MCU subsystem with no DMA/ADC/RTC/SPI usage.

## Layout notes
- Decoupling: 100 nF + 4.7 uF on the single VDD/VDDA-to-VSS/VSSA pin pair
 (pins 4/5), placed as close as possible to those pins, ideally on the
 underside of the board directly beneath them [DS Fig. 9 + caution note].
- NRST 100 nF cap: placed as close as possible to the device [DS Fig. 19
 note 3].
- SWD/UART/I2C header traces: no length/topology constraint found in the
 sources retrieved this session (no AN5096); keep them short as ordinary
 good practice, no vendor number to cite.

## Open questions / conflicts between sources
1. AN5096 (ST's own hardware-development app note, explicitly named in this
 block's brief) could not be retrieved this session - st.com timed out
 for every fetch; two mirrors 403'd; scribd showed no content; archive.org
 is blocked in this environment. Does not block the decisions above (all
 independently sourced from DS12991 + RM0454 + ES0486), but AN5096 may
 contain a stated 4-pin-header convention or an explicit large-NRST-cap
 warning that a later step should check for if time permits.
2. RM0454 Rev 2 (Apr 2019) was the only revision this session could fetch;
 st.com's current listing is Rev 5 (Nov 2020). No conflict found - the
 errata sheet (independently dated 2020) and a 2023-era community thread
 both corroborate Rev 2's boot-configuration text - but a later step
 should treat Rev 5 as authoritative if it is ever consulted and differs.
