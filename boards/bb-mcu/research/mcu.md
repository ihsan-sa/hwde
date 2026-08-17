# mcu - candidate research

Block: the MCU only (this board's whole job - support passives, connectors are P2's job).
Source: `parts_search.py` (live JLC/LCSC, confirmed `"source": "live"` on every call below) for
every stock/price figure; primary manufacturer datasheets (fetched and read directly, see
Sources) for every pin/electrical fact. Full JLC sweep: `research/raw/mcu-sweep.json`.

## Requirement recap (must-haves this ranking is judged against)

1. Single supply, correct 3.0-3.6 V operation (no on-board regulator).
2. Standard hardware debug/programming interface on DEDICATED pins, usable with a common
   third-party probe (brief names ST-LINK/J-Link/DAPLink class), not multiplexed away from
   the 4 GPIO.
3. >=4 free ordinary GPIO after debug pins and any datasheet-reserved pins.
4. Runs AND debugs on internal oscillator - no mandatory external crystal.
5. No mandatory external components beyond decoupling and whatever NRST/boot-mode needs.
6. In stock at JLCPCB today, Basic/Preferred preferred, package the PCBA line places on top.

Board-specific tiebreakers after the must-haves, in order: (a) debug-interface standardness/
documentation (SWD beats vendor-proprietary single-wire unless the proprietary part wins
decisively elsewhere), (b) Basic/Preferred over Extended, (c) visible/probeable package
(TSSOP/SOIC/SSOP/LQFP) over leadless, (d) stock depth, (e) price (not a driver at qty 5).

## Ranked candidates

| Rank | MPN | LCSC | Package | Debug | Basic | Stock | $@qty5 |
|---|---|---|---|---|---|---|---|
| 1 | STM32F030F4P6TR | C89040 | TSSOP-20 | SWD (PA13/PA14) | No | 19,015 | $0.96 |
| 2 | PY32F030F28P6TU | C3018716 | TSSOP-20 | SWD (PA13/PA14) | No | 2,536 | $0.41 |
| 3 | STM32C011F4P6 | C5452432 | TSSOP-20 | SWD (PA13/PA14) | No | 1,371 | $1.29 |
| 4 | CH32V003F4P6 | C5187096 | TSSOP-20-175mil | SWIO (PD1, 1-wire) | No | 16,813 | $0.29 |
| 5 | STM32G031F4P6 | C529332 | TSSOP-20 | SWD (PA13/PA14) | No | 68 | $2.06 |

All Extended (no JLC Basic MCU was found meeting the must-haves in anything searched - normal
for this category; this repo's own stm32-blinky board also accepted Extended for its MCU).

## Debug / boot / power facts per candidate (source: primary datasheets, pin tables read directly)

| MPN | Debug pins | Dedicated? | GPIO after debug | Boot-mode pin | Supply pins | Ext. crystal |
|---|---|---|---|---|---|---|
| STM32F030F4P6 | PA13=SWDIO, PA14=SWCLK | Yes - internal pull-up(SWDIO)/pull-down(SWCLK) activated at reset, no other AF listed on either pin | 13 of 15 | **BOOT0 = dedicated pin 1** (type "B", input-only, no GPIO alt-function at all). No internal pull documented -> needs an **external pull-down** to guarantee boot-from-flash (this repo's stm32-blinky board added exactly this: "R2 10k BOOT0 pulldown") | VDD(16)+VSS(15)+VDDA(5), no separate VSSA on TSSOP20 | Not required - internal 8 MHz HSI runs and debugs fine; OSC_IN/OUT (PF0/PF1) stay free GPIO if unused |
| PY32F030F28P6TU | PA13=SWDIO, PA14=SWCLK | Yes - internal pull-up/pull-down activated at reset (datasheet note 2) | 16 of 18 | PF4-BOOT0: datasheet states explicitly "PF4-BOOT0 defaults to digital input mode, pull-down enabled" -> **no external resistor needed** | VCC + VSS (single pair; exact TSSOP20 pin numbers carry two documented sub-pinouts F1/F2 in Puya's own table - functional assignment confirmed, physical numbering not independently reconciled here) | Not required - internal HSI (4/8/16/22.12/24 MHz selectable) |
| STM32C011F4P6 | PA13=SWDIO, PA14=SWCLK | Yes - internal pull-up(PA13)/pull-down(PA14) activated at reset (Table 12 note 2) | 16 of 18 | PA14 doubles as **BOOT0** ("PA14-BOOT0" pin name, ADC_IN14/BOOT0 additional functions) - same pin as SWCLK. Internal pull-down (same note 2) defaults the sense to boot-from-flash -> **no external resistor**. NRST (PF2) is itself GPIO-shareable (alt functions MCO/TIM1_CH4 listed) - a real architectural difference from classic F0/G0 | **VDD/VDDA merged (1 pin) + VSS/VSSA merged (1 pin)** - leanest ST candidate | Not required - internal 48 MHz HSI48 (+-1%) runs and debugs fine |
| CH32V003F4P6 | **PD1 = SWIO, single wire** (semi-proprietary WCH interface) | Shared - PD1 also carries T1CH3N/AETR2 timer/ADC alt-function; datasheet: "using the single-wire debug interface requires HSI enabled" (internal osc, not external) | 16 of 18 (17 if NRST left on its GPIO pin instead of used as reset) | **No BOOT0 pin exists at all** - simplest of any candidate; programs directly via SWIO regardless of any pin strap | **VDD(1)+VSS(1), single pair** - leanest of all 5; datasheet's own test circuit shows a single 0.1 uF cap | Not required - internal 24 MHz HSI RC; HSI must stay enabled for SWIO debug (still internal, not external) |
| STM32G031F4P6 | PA13=SWDIO, PA14=SWCLK/BOOT0 | Yes, same internal-pull scheme as C011 (note 4) | Headline 18, but **this exact TSSOP20 pinout doubles up physical pads** - Figure 8 shows pin1="PB7/PB8" and pin19="PA15/PA14-BOOT0", i.e. fewer pins are simultaneously usable than the headline count suggests (mechanism not further verified - stock alone already excludes this part) | Same internal-pull-down-on-SWCLK scheme as C011 - no external resistor needed | VDD/VDDA merged (1) + VSS/VSSA merged (1) | Not required - internal 16 MHz HSI16 |

Every candidate clears requirement 3 (>=4 free GPIO) with wide margin; the binding constraints
turn out to be requirement 2 (CH32V003's single-wire debug) and stock/complexity (G031).

## Why this order

**#1 STM32F030F4P6 (top pick).** Ties every other SWD candidate on debug standardness,
Extended-library status, and package (TSSOP-20) - wins the next tiebreaker, stock depth, by a
wide margin (19,015 vs. 1,371-2,536 for the others). Its NRST and BOOT0 are **both genuinely
dedicated pins** - no GPIO alternate function listed on either in the datasheet's own pin
table - the cleanest, most "textbook STM32" pinout of the set, which matters on a board whose
whole point is teaching the canonical case. The one cost: BOOT0 has no documented internal
pull, so it needs one external pull-down resistor to guarantee boot-from-flash with no probe
attached. That resistor is explicitly in-scope per requirements.md section 2 point 5, and this
exact fix is already precedented in this repo: the stm32-blinky board (STM32F103, same
classic-family BOOT0 behavior) carries "R2 10k BOOT0 pulldown (run from flash)".

**#2 PY32F030F28P6TU.** Genuine ARM SWD (ties #1/#3 on the debug tiebreaker), pin-compatible
with STM32 so it teaches the same canonical layout, and its BOOT0 pin (PF4) has a documented
internal pull-down - zero extra boot-strap parts, better than #1 on that one point. Cheapest of
the ARM candidates and comfortably stocked (2,536). Weighed down only by thinner official
documentation and a smaller install base than genuine STMicro parts - Puya's own datasheet
carries two different TSSOP20 sub-pinout tables (F1/F2) for what should be one physical part,
which this research could not fully reconcile; re-verify the exact pin-1 orientation before
layout if this part is chosen.

**#3 STM32C011F4P6.** The current-generation Cortex-M0+ value line, and the part already
smoke-tested live on this host. Its debug pin (PA14/SWCLK) doubles as the BOOT0 sense pin, and
that pin's own internal pull-down (activated automatically at reset, per the datasheet's pin
table note) defaults the part to boot-from-flash with **zero external boot-strap parts** - the
leanest BOM of any SWD candidate. Also has the leanest power pins of any ST part here: VDD/VDDA
and VSS/VSSA are each merged into one physical pin. Ranked below #1/#2 only because its stock
(1,371) is the thinnest of the three healthy SWD candidates - still >270x the build quantity,
not a real risk, just the tiebreaker that settles a close call. NRST (PF2) is itself
GPIO-reassignable on this part (alt functions MCO/TIM1_CH4 exist) - worth knowing, not
disqualifying, since the requirement only demands the *debug* pins be non-multiplexed.

**#4 CH32V003F4P6 (the required non-ARM entry).** Wins outright on every axis *except* the
debug-standardness tiebreaker: best stock of any candidate here (16,813), cheapest ($0.29),
and the leanest BOM of all five - a single VDD/VSS pin pair, and no BOOT0 pin exists at all
(it isn't excluded by mode, it simply isn't part of this chip's architecture). The cost is
exactly what the assignment asked to be stated plainly: its debug interface is WCH's **single-
wire SWIO**, not 2-wire SWD, on PD1 - a pin that also carries a timer/ADC alternate function.
Programming it needs a **WCH-Link-class probe** (a real, cheap, JLC/AliExpress-common tool,
but not the ST-Link/J-Link/DAPLink class the brief names by name). Community alternatives exist
(PicoRVD on a Raspberry Pi Pico, `minichlink`, an OpenOCD build with WCH's changes, even a
Flipper Zero app) but none of them is the turnkey mainline-OpenOCD/pyOCD experience the ARM
parts get for free - see Sources. **Choosing this part also changes J2**: the owner's answer to
requirements.md open question 2 assumes a 2-signal SWDIO+SWCLK header; CH32V003 would need J2
redrawn as 3V3/SWIO/NRST/GND (4 positions, one debug signal, not two) - a real downstream
consequence for P2 if this part is picked. Ranked above #5 because it wins decisively on stock,
price, and BOM leanness in a way #5 does not - per the tiebreaker rule's own escape clause.

**#5 STM32G031F4P6 (not recommended, listed for completeness).** The most capable part
electrically (64 MHz, 8 KB RAM vs. 4-6 KB on the others) and shares C011's clean zero-extra-
part BOOT0 story. Excluded from serious contention by two independent facts: **stock is only
68 units** at JLCPCB today - not zero, but near-zero margin over a 5-board build once panel
scrap and any respin are considered, versus 1,300-19,000 for every other candidate; and this
specific TSSOP20 package's own pinout diagram shows physical pads shared between unrelated
signals (PB7/PB8 on pin 1, PA15/PA14-BOOT0 on pin 19) in a way none of the other candidates'
20-pin packages do, meaning the headline "18 GPIO" figure overstates what is simultaneously
available on this exact part/package combination. Listed so the architect can see that the
same-vendor upgrade path exists and why it isn't the pick here.

## Considered and excluded (didn't make the shortlist)

- **STM32C011F4U6 (UFQFPN20, leadless)** - same silicon as #3, live-checked, but QFN loses
  tiebreaker (c) to every TSSOP candidate already ranked above it on a board that will be
  probed and possibly reworked on the bench. Not separately tabled.
- **STM32F103C8T6 (LQFP-48, C8734)** - this repo's own stm32-blinky board's MCU. Not
  reconsidered here: 37 GPIO / LQFP-48 is far more part and pin count than a 4-GPIO
  block-only board needs, and it was the prior board's accepted-Extended precedent, not a
  competing candidate for this smaller job.
- **CH32V203-class WCH parts** (more capable RISC-V, USB, more GPIO) - not shortlisted; the
  assignment asked for one credible non-ARM alternative, and CH32V003 already demonstrates
  the same SWIO probe-compatibility tradeoff at a better price/stock point for a 4-GPIO board
  that needs none of the extra capability.
- **STM8S-family (SWIM debug)** - not shortlisted; SWIM is a different single-wire debug
  scheme from a different core family (8-bit, not the ARM/RISC-V split the assignment asked
  to contrast), and would not have added a materially different tradeoff than CH32V003 already
  shows.

## Cross-cutting risks for P2/P3

1. **CH32V003's debug interface reshapes J2.** If this part is picked, J2 becomes a 4-position
   header (3V3/SWIO/NRST/GND) instead of the 5-position SWDIO+SWCLK header the owner's answer
   assumed - flag this explicitly if P3 selects it, it is not a drop-in swap.
2. **STM32F030F4P6's BOOT0 pull-down is a real, small, in-scope addition** - one resistor,
   already precedented in this repo (stm32-blinky R2). Not a reason to disqualify the part
   (requirements.md section 2 point 5 says exactly this is in scope) - just don't drop it.
3. **Every candidate is single-source at its exact LCSC row** here; no second-distributor check
   was run (out of scope for this script). Pin-compatible alternates exist within each family
   (e.g. STM32F030 vs the extended F0 lineup; PY32F030 vs PY32F002A) but were not independently
   re-verified.
4. **PY32's TSSOP20 pin table carries two sub-variants (F1/F2)** in Puya's own datasheet that
   this research could not fully reconcile to one physical pin-1 orientation - re-verify against
   the exact ordering-code datasheet page before footprint lock if PY32 is chosen.
5. **G031's stock (68) should be re-checked at part-lock time** if it is ever reconsidered -
   it is the kind of number that can hit zero between research and order.

## Sources

- [STM32C011x4/x6 datasheet (ST, DS13866 Rev 3)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2305191757_STMicroelectronics-STM32C011F4P6_C5452432.pdf)
- [STM32F030x4/x6/x8/xC datasheet (ST, DocID024849 Rev 3)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf)
- [STM32G031x4/x6/x8 datasheet (ST, DS12992 Rev 2)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32G031F4P6_C529332.pdf)
- [PY32F030 datasheet (Puya, Rev J.3)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2205171716_PUYA--PY32F030F28P6TU_C3018716.pdf)
- [CH32V003 datasheet (WCH, V1.8, Chinese)](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2403131352_WCH-Jiangsu-Qin-Heng-CH32V003F4P6_C5187096.pdf)
- [ch32v003fun wiki - Features](https://github.com/cnlohr/ch32v003fun/wiki/Features) and
  [PicoRVD](https://github.com/aappleby/picorvd) / [wch_swio_flasher](https://github.com/sukvojte/wch_swio_flasher) -
  community SWIO probe-alternative evidence (WebSearch, this session)
- LCSC/JLCPCB live search: `parts_search.py` (this repo), raw sweep saved to
  `research/raw/mcu-sweep.json`; this repo's own `boards/stm32-blinky/parts/parts.json` cited
  above for the BOOT0-pulldown and Extended-MCU precedents.
