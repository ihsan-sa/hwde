# refdesign-mcu - STM32F030F4P6TR minimum system

Block: `mcu`. Part is RULED (STM32F030F4P6TR, LCSC C89040, TSSOP-20, Cortex-M0)
- this is what has to be around it, and why, cited to primary ST sources.

**Topology reference check**: `reference/topologies/` contains only `buck.md`.
No fragment matches an MCU minimum system, so this is researched from scratch
against ST primary documents, not adapted from a canonical fragment.

**Sibling research**: `research/interface-swd.md` (same board) already covers
J2/SWD signal-integrity, connector-pin-order and the 3V3-sense-pin analysis in
depth, from the same primary datasheet passages used below (independent
cross-check: both land on the same NRST-cap and SWD-pull conclusions). This
file stays focused on the MCU's own datasheet-required minimum system; it does
not re-derive connector wiring or trace-length budgets.

**Network note**: `st.com` is unreachable from this research environment (curl
and WebFetch both time out identically - a network-level block, not a slow
page: a control fetch to example.com and to LCSC's mirror both succeeded in
under 2s). All four documents below were fetched from credible third-party
mirrors of the same primary ST PDFs (confirmed by content: DocID/Rev footers,
and each document's own "applicable products" table naming STM32F030F4). Each
is 1-3 revisions behind the current st.com-hosted version - see Errata.

## 1. Decoupling

TSSOP-20 pin facts (datasheet Figure 8, confirmed against Table 11): **VDD =
pin 16, VSS = pin 15, VDDA = pin 5, no separate VSSA pin on this package**
(Table 11 lists VSSA as "-" for the TSSOP20/LQFP32 columns).

Datasheet Figure 12 "Power supply scheme" (DocID024849 Rev 3, p.41/91) draws
**2x100nF + 1x4.7uF** across the family's VDD/VSS pins and **10nF + 1uF**
across VDDA/VSSA, captioned: *"Each power supply pair (VDD/VSS, VDDA/VSSA
etc.) must be decoupled with filtering ceramic capacitors as shown above."*
That figure is generic to the whole package family (largest package = 2 VDD +
2 VSS pins); TSSOP-20 has exactly **one** VDD pin and **one** VSS pin, so the
per-pin-pair set (1x100nF, one 4.7uF bulk on the net) applies once. AN4325's
own BOM (Table 4 "Mandatory components", DocID024966 Rev 1 p.23/27)
independently gives the same values: C1/C2=100nF (qty 2, one per VDD pin on
its 64-pin reference part), C6=4.7uF ("Used for VDD"), C3=10nF + C5=1uF ("Used
for VDDA").

**REQUIRED** (the datasheet's caution note has no hedging language - "must").
Since TSSOP-20 has no VSSA pin, the VDDA decoupling's return necessarily
shares the VSS/digital-ground net on this exact part - a package fact for
P6/P7, not a defect.

## 2. VDDA

- **Connection: REQUIRED.** Section 3.5.1: *"VDDA = from VDD to 3.6 V:
  external analog power supply ... The VDDA voltage level must be always
  greater or equal to the VDD voltage level and must be provided first."*
  AN4325 section 1.1 (p.6/27): *"When a single supply is used, VDDA must be
  externally connected to VDD."*
- **Filtering: RECOMMENDED, NOT required.** Same AN4325 sentence continues:
  *"It is recommended to use an external filtering circuit in order to ensure
  a noise free VDDA."* ST's own reference schematic (AN4325 Figure 9,
  p.24/27) shows VDDA wired to VDD with a **bare trace, no filter part** -
  concrete proof "recommended" means optional even in ST's own example. Per
  this board's `block-only` mode ("filtering the datasheet does not require"
  is excluded), no filter is added.
- The Schottky-diode option in the same AN4325 paragraph applies only to *"When
  VDDA is different from VDD"* - not this board's topology - so it does not
  apply and is not a gap.
- **Sequencing (VDDA >= VDD, VDDA arrives first): satisfied trivially.** Tying
  VDDA directly to VDD makes them the same net - zero possible delta,
  simultaneous arrival, no sequencing circuit needed or possible to omit.

## 3. NRST (pin 4)

- **Internal pull-up: permanent, always on.** *"The NRST pin input driver uses
  the CMOS technology. It is connected to a permanent pull-up resistor, RPU."*
  Table 49 "NRST pin characteristics" (DocID024849 Rev 3 p.65/91): RPU =
  25/40/55 kOhm (min/typ/max). **No external pull-up is needed** - directly
  answered by "permanent."
- **External capacitor (~0.1uF): RECOMMENDED, NOT required.** Figure 21
  "**Recommended** NRST pin protection" (p.66/91) draws it inside a dashed
  circle labelled "External reset circuit", footnoted *"The external capacitor
  protects the device against parasitic resets."* Protective framing, not a
  functional requirement. AN4325's BOM ties the equivalent part (C4, 100nF)
  explicitly to *"Ceramic capacitor for RESET button"* (Table 5, p.23/27) -
  this board has no reset button (excluded by mode), which independently
  removes the cap's own stated purpose. **Excluded.**
- Internal glitch filter is a bonus fact, not a design input: pulses <=100ns
  are filtered, >=300ns (2.7-3.6V) are guaranteed recognized as reset (same
  Table 49) - the datasheet's own answer to the "parasitic reset" concern the
  optional cap addresses.

Cross-checked against `research/interface-swd.md` section 6, which reaches the
identical required-vs-recommended conclusion independently.

## 4. BOOT0 (pin 1)

- **Level for boot-from-flash: LOW (0).** Boot mode table - BOOT0=0 (nBOOT1 =
  don't-care) -> "Main Flash memory is selected as boot area." Cross-checked
  in two independent documents with matching tables: AN4325 Table 2
  (DocID024966 Rev 1, p.17/27) and RM0360 section 2.5 Table 3 (DocID025023
  Rev 4). Latched on the 4th SYSCLK rising edge after reset - before any
  software runs.
- **No internal pull exists on this pin** - unlike NRST. Table 11's pin-type
  legend (p.30-31/91) defines I/O structure "B" as simply *"Dedicated BOOT0
  pin"*, with no pull language at all - directly contrasted, in the SAME
  legend, against "RST": *"Bidirectional reset pin with embedded weak pull-up
  resistor."* The presence of pull wording for one type and its total absence
  for the other, in one legend, is the datasheet's own basis for "BOOT0 has no
  documented internal pull."
- **If left floating: the boot-mode-selection level is undefined** at the
  instant it's hardware-sampled. This is a distinct, more acute case than the
  general "floating GPIO wastes power" guidance (section 6 below) because
  BOOT0 cannot be configured by software before it's latched - there is no
  window in which firmware could fix a bad level.
- **Resistor value: 10 kOhm**, ST's own value from AN4325's reference design:
  Table 5 "Optional components" (p.23/27), R2, captioned *"Used for BOOT0
  pin"* with the caveat *"This value is given only as a typical example."* -
  ST does not claim precision, just a small, safe, conventional pull.
- **This board's topology**: a plain 10 kOhm pull-down, BOOT0-to-GND, no
  switch. AN4325's reference design wires R2 between a user-selectable switch
  (SW1) and BOOT0, letting a dev board toggle into system-bootloader mode; this
  board only ever wants flash-boot, so the switch is dropped (an excluded
  config strap) and R2 becomes a fixed pull-down. **The value and the
  requirement are taken from ST; the switch topology is not** - this board
  designs from the decision, not the reference file, per this role's rule.
- **In scope**: requirements.md section 2 point 5 makes a datasheet-required
  boot-mode resistor in-scope support, not an excluded config strap. The chain
  above (no internal pull -> undefined level if floating -> boot-mode
  correctness at stake) is exactly that case.

## 5. SWD (PA13 = SWDIO = pin 19, PA14 = SWCLK = pin 20)

- **Reset state: dedicated immediately, no software needed.** Table 11
  footnote 7 (p.31-32/91): *"After reset, these pins are configured as SWDIO
  and SWCLK alternate functions, and the internal pull-up on SWDIO pin and
  internal pull-down on SWCLK pin are activated."* AN4325 section 4.3.2
  (p.18-19/27): *"After reset ... the pins used for the SWD are assigned as
  dedicated pins which are immediately usable by the debugger host."*
- **Internal pulls**: SWDIO = pull-up, SWCLK = pull-down, both 25/40/55 kOhm
  (min/typ/max) - the same generic weak-pull spec block (Table 46, "I/O static
  characteristics", p.60-61/91) every alternate-function pin uses; no separate
  table exists for the debug pins specifically.
- **Series resistors: not needed, not recommended by ST.** AN4325 section
  4.3.3: *"Having embedded pull-up and pull-down resistors removes the need to
  add external resistors."* Figure 7's SWD-connector schematic draws direct
  pin-to-connector traces, no series parts.
- **Repurposing**: *"the MCU offers the possibility to disable the SWD,
  therefore releasing the associated pins for general-purpose I/O (GPIO)
  usage. For more details ... refer to the RM0360 section on I/O pin
  alternate function multiplexer and mapping"* (AN4325 section 4.3.2). Not
  used on this board - J2 needs PA13/PA14 as SWD permanently, and the
  schematic must not also route them to J3.
- Pin assignment cross-checked two ways: datasheet Figure 8 (pinout image) and
  AN4325 Table 3 "SWD port pins" (p.18/27) independently agree SWDIO=PA13,
  SWCLK=PA14. (One RM0360 text-extraction artifact briefly appeared to swap
  them - a pdftotext column-order garble on a multi-row table cell, not a real
  third source; resolved by the two clean, mutually consistent sources.)

## 6. Unused pins

**RECOMMENDED (EMC/power), not required** - excluded by mode. AN4325 section
5.6, verbatim: *"To increase EMC performance and avoid extra power
consumption, unused clocks, counters or I/Os, should not be left free. I/Os
should be connected to a fixed logic level of 0 or 1 by an external or
internal pull-up or pull-down on the unused I/O pin. The other option is to
configure GPIO as output mode using software."* The datasheet's own I/O
current-consumption discussion (p.47-48/91 area) uses the same framing:
*"Any floating input pin can also settle to an intermediate voltage level or
switch inadvertently, as a result of external electromagnetic noise. To avoid
current consumption related to floating pins, they must either be configured
in analog mode, or forced internally to a definite digital value."* Both
motivate the practice by efficiency/EMC, never by correctness or damage risk -
this is the required/recommended line this board's scope tier draws, so no
pull resistors are added on unused pins. This general guidance covers ordinary
software-configurable GPIOs; it does NOT govern BOOT0 (section 4), which is
sampled before software can act.

## 7. Oscillator

- **Runs on HSI, zero external components.** Section 3.6 "Clocks and
  startup": *"System clock selection is performed on startup, however the
  internal RC 8 MHz oscillator is selected as default CPU clock on reset."*
  AN4325 section 2.3 "HSI clock" (p.14/27): *"The HSI RC oscillator has the
  advantage of providing a clock source at low cost (no external
  components)."*
- **Debugs without a crystal too** - a reasoned conclusion, not a single ST
  quote (flagged as such): RM0360 describes SW-DP as a 2-pin (clock+data)
  interface, clocked by SWCLK which the probe drives externally; nothing in
  the datasheet, RM0360 or AN4325 conditions debug-port availability on
  HSE/HSI selection. This board's own scout research and this repo's
  stm32-blinky precedent both already run/program STM32 parts without issue;
  no source contradicts debug-on-HSI.
- **OSC_IN/OSC_OUT (PF0=pin2, PF1=pin3) when unused: ordinary floating-input
  GPIOs.** Table 11's general note: *"Unless otherwise specified by a note,
  all I/Os are set as floating inputs during and after reset"* - no override
  note is attached to the PF0/PF1 rows. AN4325's HSE-bypass paragraph (section
  2.1, p.14/27) independently confirms the mechanism: *"the OSC_OUT pin can be
  used a GPIO"* whenever the oscillator block isn't consuming it - reinforcing
  the same conclusion for the always-off (HSI-default) case this board uses.

## Layout notes (for P6/P7)

- Decoupling caps *"must be placed as close as possible to, or below, the
  appropriate pins on the underside of the PCB"* - datasheet Figure 12
  caution, DocID024849 Rev 3 p.41/91.
- AN4325 Figure 8 "Typical layout for VDD/VSS pair" (DocID024966 Rev 1 section
  5.4, p.20-21/27): a via to the VDD plane and a via to the VSS plane
  straddle the decoupling cap, tight to the pin.
- No VSSA pin on TSSOP-20 (Table 11) - VDDA's decoupling necessarily returns
  to the shared VSS/GND pour on this exact part/package.
- AN4325 section 5.3 (general EMC guidance): separate VDD/VDDA routing,
  single-point ground return, minimized supply-loop area recommended for
  analog performance - informational, since VDDA is tied straight to VDD here
  (section 2 above).
- AN4325 sections 5.1/5.2: a multilayer board with dedicated GND/VDD layers is
  preferred "for technical reasons" but explicitly not always economical -
  informational; this board's layer count is earned by the layout, not fixed
  by this note.
- On TSSOP-20, SWDIO(19)/SWCLK(20) sit adjacent at one corner with VSS(15)/
  VDD(16) on the same side, while NRST is pin 4, on the opposite side
  (Figure 8) - J2 cannot take all its MCU-side signals off one package edge.
  Flagged for P6 placement, not decided here.

## Errata

Source: STM32F030x4/x6/x8/xC errata sheet, ST DocID025065 Rev 3, October
2016 (Table 1 explicitly lists STM32F030F4 as covered). Full contents (System,
USART, GPIO x2, I2C, SPI, RTC, ADC, IWDG - 16 items total) read in full.

- **No errata items affect NRST, BOOT0, VDDA, or SWD/debug** for this device
  family in the revision reviewed.
- **GPIO erratum 2.3.1** ("Extra consumption on GPIOs PC0..5 on 48-pin and PB0
  on 20-pin devices") names STM32F030F4 specifically, but is **hardware-
  irrelevant here**: it triggers only if software reconfigures PB0 to analog
  mode, and PB0 is not bonded to any external pin on the TSSOP-20 package
  (checked against Table 11/Figure 8 - no PB0 anywhere in the 20-pin list;
  it exists only at the silicon level on this package). This pipeline also
  delivers no firmware. Recorded and dismissed, not silently dropped.
- **Revision-currency caveat**: this errata sheet is 3 revisions behind the
  current st.com-hosted ES0219 Rev 6 (March 2024, per web search) - the
  largest gap of the four documents used, and the type most likely to gain new
  entries over time. st.com was unreachable from this environment to confirm.
  Worth a re-check before this board's BOM locks if that becomes gating.

## Sources

- **STM32F030x4/x6/x8/xC datasheet**, ST DocID024849 Rev 3 (production data).
  Section 3.5.1 (p.13), 3.6 (p.13-14), Table 11 pin definitions + legend +
  footnote 7 (p.27-32), Figure 8 TSSOP20 pinout (p.26), Figure 12 power supply
  scheme (p.41), Table 46 I/O static characteristics (p.60-61), Table 49 NRST
  characteristics + Figure 21 (p.65-66), Table 18 abs-max voltages (p.42).
  Fetched via LCSC mirror (same URL the component scout used):
  <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf>
- **AN4325**, "Getting started with STM32F030xx hardware development", ST
  DocID024966 Rev 1, November 2014. Sections 1.1 (p.6), 2.1/2.3 (p.13-14), 4.2-
  4.3.4 (p.18-19), 5.3-5.6 (p.20-21), 6.1-6.2 (p.22-23) + Table 2 boot modes
  (p.17), Table 3 SWD pins (p.18), Table 4/5 component tables (p.23), Figure 9
  reference schematic (p.24). Applicable-products table (Table 1) names
  STM32F030F4 explicitly. Fetched via a third-party mirror (st.com
  unreachable): <http://comm.eefocus.com/media/download/index/id-1001900>
  (content verified against the document's own DocID/title page).
- **RM0360**, "STM32F030x4/x6/x8/xC and STM32F070x6/xB advanced ARM-based
  32-bit MCUs, Reference manual", ST DocID025023 Rev 4, April 2017. Section
  2.5 Boot configuration + Table 3 (cross-check for BOOT0), SWD-DP description
  (debug chapter). Fetched via a third-party OSS mirror (st.com unreachable):
  `oksht-mall.oss-cn-shenzhen.aliyuncs.com` (content verified against the
  document's own title page and DocID footer).
- **Errata sheet**, "STM32F030x4/x6/x8/xC device limitations", ST DocID025065
  Rev 3, October 2016. Section 2.3.1 GPIO erratum; full summary table (Section
  1) read for NRST/BOOT0/VDDA/SWD relevance. Fetched via Octopart mirror
  (st.com unreachable): `datasheet.octopart.com` (content verified: Table 1
  device summary explicitly lists STM32F030F4).
- **This board**: `research/mcu.md` / `research/mcu.json` (component scout's
  shortlist, already-vetted TSSOP20 pin facts this file cross-checked and
  confirmed independently against the primary datasheet). `boards/stm32-
  blinky/architecture/decisions.md` (read-only precedent - BOOT0 pulldown,
  Extended-MCU acceptance; different STM32 family/package, not re-derived
  from). `research/interface-swd.md` (sibling P1 research, same board -
  independent cross-check on NRST/SWD electrical facts, deeper on connector-
  level signal integrity and pin ordering, not duplicated here).

## Not fetched / not needed

- ST's `AN2606` (embedded bootloader protocol details) - referenced in AN4325
  but out of scope: this board never uses the system bootloader, only
  flash-boot.
- ARM's ADIv5 spec and AN4989 - already logged as unreachable by the sibling
  `interface-swd.md`; not re-attempted here since this file's SWD claims rest
  on ST's own datasheet/AN statements, which are the stronger source for a
  silicon-specific pull/reset-state question anyway.
