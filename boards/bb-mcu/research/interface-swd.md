# interface-swd - ARM Serial Wire Debug on STM32F030F4P6TR (bb-mcu J2)

Interface: `swd`. Target: STM32F030F4P6TR, TSSOP-20, SWDIO = PA13 (pin 19),
SWCLK = PA14 (pin 20), NRST = pin 4 (DS DocID024849 Rev 3, Figure 8, p26).
Probe: any flying-lead ST-LINK / J-Link / DAPLink-class tool onto a
5-position 0.1 inch through-hole header. Board: 2-layer, bench-only, 3.3 V.

No canonical `reference/interfaces/swd.*` fragment exists in this repo, so this
is derived from primary sources, not adapted.

## VERDICT - what binds layout

**Nothing.** No controlled impedance, no differential pair, no length matching,
no series termination, no return-path rule. The JSON fragment therefore emits
an EMPTY `high_speed` and an EMPTY `diff_pairs`, deliberately. Sections 2-3
carry the arithmetic; section 10 says what would have to change for that to be
wrong.

The BOM consequences (sections 4-6) are the useful output of this research:
**SWD adds zero components to this board.** No pull-up and no pull-down (ST:
the internal ones "remove the need to add external resistors"), no series
resistor (a considered rejection of three probe vendors' recommendations - ARM
itself requires none), and no NRST capacitor (ST files it under *Optional
components*, for a reset button this board does not have).

## 1. Nets proposed

`SWDIO`, `SWCLK`, `NRST`, `+3V3`, `GND`. Proposals only - the architect
reconciles at P2, `netlist_audit` verifies at P4. Local-label nets will carry a
leading `/` in the final netlist (`/SWDIO`, `/SWCLK`, `/NRST`); `+3V3` and
`GND` are bare power nets. None of these names matches `check_diffpair`'s
auto-discovery suffixes (`_P`/`_N`, `DP`/`DM`, `D+`/`D-`), so no pair is
discovered by accident.

## 2. Speed - what this port actually runs at

| quantity | value | source |
|---|---|---|
| SWD/JTAG AC timing in the MCU datasheet | **does not exist** | DS DocID024849 Rev 3 has no JTAG/SWD AC characteristics table at all. The only serial-interface AC table in section 6.3 is Table 58 (SPI). ST publishes no f_max for SWCLK on this part. |
| SWCLK, **ST-LINK/V2 and V2-1** | **4 MHz** (default 1.8 MHz) | UM1075 Rev 9 section 1 Features: "Supports serial wire debug (SWD) **up to 4 MHz (default: 1.8 MHz)**" |
| **ST's own recommendation** | **use 4 MHz** | AN4989 Rev 4 section 5.2: "make sure that the higher SWD frequency possible is used with the probe... **On system with a core clock greater than 1 MHz, it is safe to use the highest 4 MHz SWD speed.**" |
| SWCLK, STLINK-V3 | 24 MHz | UM2448: "SWD with SWO (up to 24 MHz)"; "signals are 3.3-volt compatible and can perform up to 24 MHz" |
| SWCLK, J-Link BASE/PLUS | 15 MHz | SEGGER spec table: "Target interface speed Max. 15 MHz" |
| SWCLK, J-Link EDU Mini | 4 MHz | SEGGER spec table: "Max. 4 MHz" |
| SWCLK, CMSIS-DAP / DAPLink | 1 MHz default, no spec'd max | `DAP_DEFAULT_SWJ_CLOCK 1000000U`; RPi Debug Probe docs use `adapter speed 5000` (5 MHz) |
| **realistic bench maximum here** | **4 MHz** | it is the hard ceiling of the two probes people actually own (ST-LINK/V2 clones, J-Link EDU Mini) and ST's own recommended setting; DAPLink sits at 1-5 MHz |
| SWCLK-vs-core-clock rule | **none exists** | ST states no "SWCLK < N x HCLK" ratio anywhere. The only prerequisite (AN4989 4.2.1) is that FCLK/HCLK be enabled and GPIO clocked. |
| fastest edge the STM32F030 can produce on ANY GPIO | **tr = tf = 5 ns max**, OSPEEDR[1:0] = 11, CL = 30 pF, VDDIOx >= 2.7 V | DS Table 48 "I/O AC characteristics", p64. Other rows: 8 ns at CL = 50 pF, 25 ns at OSPEEDR = 01, 125 ns at OSPEEDR = x0. |
| knee frequency at that edge | 100 MHz | f_knee = 0.5 / t_r |

Two things follow that make the analysis robust:

- SWDIO is the only one of the two the MCU ever drives; **SWCLK is a target
  input** and its edge belongs to the probe, not to this part.
- **That 5 ns is the real default, not just a bound.** RM0360 Rev 5
  section 8.4.3: GPIOA_OSPEEDR "Reset value: 0x0C00 0000 (for port A)" -
  bits 27:26 = 11, so **PA13 (SWDIO) comes out of reset at High speed**, the
  Table 48 row above; bits 29:28 = 00 leave PA14 (SWCLK) at Low speed, which is
  moot since the MCU never drives it. Using the fastest row therefore both
  matches the reset default and bounds anything firmware could later set.

ASSUMED: the probe's own output edge is of the same order (2-5 ns, ordinary
3.3 V CMOS buffer). No probe vendor publishes an edge-rate spec. This is the
only unsourced number in the speed analysis and section 3 tests it at 2 ns.

## 3. Why nothing binds - the arithmetic

ASSUMED propagation delay **6 ps/mm** - FR-4 microstrip at epsilon_r 4.5 (the
`JLC2313_1.6` value in `reference/stackups.yaml`) computes to 5.6 ps/mm by
85 * sqrt(0.475*er + 0.67) ps/inch, and a 2-layer 1.6 mm trace is weakly
coupled so the real figure is lower. 6 ps/mm is the conservative choice
(inflates delay, shortens critical length).

**Electrical length** - transmission-line treatment starts when one-way delay
exceeds ~t_r/6 (Johnson and Graham, *High-Speed Digital Design*, section 1.3);
t_r/10 is the strict form.

| t_r | critical length at t_r/6 | at t_r/10 |
|---|---|---|
| 5 ns (DS Table 48 max) | 139 mm | 83 mm |
| 2 ns (ASSUMED lightly-loaded worst case) | 56 mm | 33 mm |

At the 2 ns / strict corner 33 mm is not obviously long-and-safe, so electrical
length alone is NOT a sufficient argument. **Settling is the decisive one.**

Reflections on an unterminated 40 mm trace settle in ~3 round trips:
2 * 40 mm * 6 ps/mm * 3 = **~1.5 ns**. SWD samples mid-bit-cell, a half-period
away: **125 ns** at 4 MHz (margin ~80x), **20.8 ns** at STLINK-V3's 24 MHz
(margin ~14x). Ringing that has settled 14-80 times over before the sampling
edge cannot cause a bit error. Termination and impedance control buy nothing.

**Skew** - SWD is clock-forwarded (SWCLK + SWDIO). 30 mm of mismatch is 0.18 ns
against a 125 ns half-bit: **0.14 %** of budget. Length matching is three orders
of magnitude below anything that matters.

**And there is nothing to match to.** `reference/stackups.yaml` `JLC2313_1.6`
carries `controlled_impedance: []`, provenance: JLC's
`getImpedanceTemplateSettingList` returns **0 templates for stencilLayer=2**
(live-verified 2026-08-06). JLCPCB sells no impedance-controlled 2-layer
stackup; 50 ohm single-ended on this stack would need a ~2.7 mm trace. An
`impedance_ohm` key here would be a number no fab could honour.

## 4. Pull-up / pull-down - BOM decision: NONE

**No external resistor is required on SWDIO or SWCLK.**

**What ARM actually requires** - *Arm Debug Interface Architecture
Specification ADIv5.0-5.2*, ARM IHI 0031G, section B4.3.2 "Line pull-up",
p. B4-122:

> "To make sure that the line is in a known state when neither host nor target
> is driving the line, **a 100K pull-up is required at the target**. The pull-up
> is intended to prevent false detection of signals when no host is connected,
> and must be of a suitably high value to reduce current consumption from the
> target when the host actively pulls down the line."

Two precisions matter. **(a) The requirement is on SWDIO only.** ADIv5's only
other pull requirement is a TDI pull-down for JTAG-never-used; **there is no ARM
requirement for a SWCLK pull-down** - that is a vendor recommendation (SEGGER:
"It is recommended that this pin is pulled to a defined state"; Lauterbach:
1 k - 47 k, 10 k typical). **(b) 100K is ARM's value, and the STM32's internal
pull is stronger, not weaker:** R_PU = R_PD = **25 / 40 / 55 kohm** (DS
Table 46). A ~40 k pull sinks ~82 uA when the probe drives SWDIO low versus
~33 uA at 100 k - both negligible for any probe driver, and the "known state"
purpose is met with margin. Stronger is the safe direction to err.

The STM32F030 provides both on-chip at reset - DS Table 11 note 7: "the internal
pull-up on SWDIO pin and internal pull-down on SWCLK pin are activated";
RM0360 Rev 5 confirms it in the registers (GPIOA_PUPDR reset 0x2400 0000) and
in words (8.3.1). **ST then draws the conclusion explicitly, for this exact
family:**

> "The reset states of the GPIO control registers put the I/Os in the equivalent
> states: SWDIO: alternate function pull-up; SWCLK: alternate function
> pull-down. **Having embedded pull-up and pull-down resistors removes the need
> to add external resistors.**"
> - AN4325 Rev 2 section 4.3.3

**Know about ST's internal contradiction before a reviewer finds it.** RM0360
Rev 5 section 26.5.1 says "For SWDIO bidirectional management, the line must be
pulled-up on the board (100 kohm recommended by Arm)" - which reads like a
board requirement. Section 26.3.3 of the same manual, and AN4325 section 4.3.3
above, are ST's explicit counter-statement: the on-die ~40 kohm pull-up on PA13
satisfies it. That resolution holds **only while PA13 stays a dedicated debug
pin**, which on this board it does (requirements.md section 2: the debug
interface must not be multiplexed away). If a later phase ever repurposes PA13,
this reopens.

Under the `block-only` tier ("exactly the support components its datasheet
requires"), an external pull duplicating a working internal one is not
datasheet-required and is out of scope. It would also load the probe's driver
for no gain.

## 5. Series termination - BOM decision: NONE (but three probe vendors do ask)

**ARM's ADIv5 requires nothing** - the spec says nothing about series resistors.
**ST is silent too**: no recommendation in AN4989, AN4325, AN4488, AN5967,
RM0360 or UM2448 (checked negative).

**Three probe vendors do recommend one, and this must be stated fairly:**

| vendor | value | where |
|---|---|---|
| Raspberry Pi, RP-003139-SP debug connector spec | **100 ohm** | source termination on SC and SD at **both** ends, "very close to the IC pins" |
| Lauterbach, Arm Debug and Trace Interface Spec | **47 ohm** | "near the processor... on the TDO line (JTAG) or SWDIO and SWO line (SWD)... if the chip's output driver are not impedance matched" - **never on SWCLK** |
| SEGGER Signal Smoothing Adapter | **47 ohm** default | an accessory, for "overshoot and ringing" on capacitive/long-cable targets |

Note none of them says 22R or 33R - those common numbers have no vendor source.
And they only ever go on the **target-driven** line (SWDIO), never on SWCLK,
which the target does not drive.

**Why it is still omitted here, taking each stated rationale in turn.** RPi
gives three: "slew limiting (better for signal integrity and EMC), short-circuit
and ESD current limiting", and adds that target-side resistors "are not strictly
required but highly recommended unless the platform is very low cost and/or
space constrained".

- *Reflections / ringing*: section 3 - they settle in ~1.5 ns against a 125 ns
  half-bit. Nothing to damp.
- *EMC slew limiting*: requirements.md section 4 - "No formal EMC/emissions
  campaign - this is a bench study article, not a product."
- *Short-circuit and ESD current limiting*: this is **protection**, the first
  class `block-only` excludes by mode. Not an engineering conclusion, a scope
  one - and per build-modes.md, an excluded class is never a reviewer finding.

Decision: **omit** - a considered rejection of real vendor recommendations, on
three separately-sourced grounds, not an oversight. If a reviewer raises it, the
answers above are the answer; "no source asks for it" is NOT (they do).

## 6. NRST on the header - REQUIRED for the standard flow, needs nothing electrically

**Connect it - and ST says so.** AN4325 Rev 2 section 6.1.4 "SWD interface":
"**It is recommended to connect the reset pin in order to be able to reset the
application from the tool.**" AN4325's Figure 7 "SWD port connection" then shows
the connector carrying exactly NRST, SWCLK, SWDIO, VDD and GND - **the same five
signals the owner fixed for J2**, so the owner's pin SET is the vendor's own
reference connection, not an invention.

For the standard flow it is stronger than "recommended". AN4989 Rev 4 section
4.2.1: "ConnectUnderReset: Debugger takes control while asserted NRST pin ...
**This is required in case of a reconnection to a system in Low-Power mode or
which has changed SWD pin to alternate functions.**" Section 4.2.5 adds that the
reset pin of the connector "must be connected to the device reset pin" for
hardware reset, and that without it the tools **silently fall back** to a
software system reset - which cannot recover a part whose firmware has already
released the SWD pins.

This repo has already paid for that: `stm32-blinky` shipped a 4-pin header
without NRST and its P4 review recorded the cost verbatim:

> "with no NRST at the header, connect-under-reset is unavailable; first flash
> must attach to a powered, running chip ... any future firmware that remaps
> PA13/PA14 or stops the core can brick-until-boot0-bodge."
> - `boards/stm32-blinky/reports/review-schematic.md`

bb-mcu has **no reset button** (excluded by mode), so NRST on J2 is the board's
only reset control and its only recovery path.

**Electrically it needs nothing added:**

- Permanent internal pull-up - "It is connected to a permanent pull-up
  resistor, RPU", R_PU = 25/40/55 kohm (DS Table 49, p65).
- Internal glitch filter - pulses up to **V_F(NRST) = 100 ns** are filtered out;
  **V_NF(NRST) >= 300 ns** (2.7 V < VDD < 3.6 V) is guaranteed to reset (DS
  Table 49). NRST already rejects short noise on its own.
- Probes drive reset **open drain** - "The nRESET signal is open drain, and
  consideration should be taken where multiple sources may drive it" (Hitex).
  Open-drain driver + internal 25-55 kohm pull-up is a complete reset circuit.

**The 0.1 uF capacitor - SETTLED, omit it.** DS Figure 21 p66 "**Recommended**
NRST pin protection" shows 0.1 uF to ground; note 1: "The external capacitor
protects the device against parasitic resets." (Value read from the rendered
figure, not from mangled text extraction. Its `(3)` superscript has no matching
note text in Rev 3 or Rev 5 - an ST doc defect, not a missing requirement.)

The deciding evidence is **AN4325's split of its own BOM**: Table 5 is
"Mandatory components" and the cap is not in it; it appears in **Table 6
"Optional components"** as "Capacitor C4 100 nF 1 Ceramic capacitor for **RESET
button**". **bb-mcu has no reset button.** ST's optional cap is tied to the very
thing this board lacks, its stated job is a class `block-only` excludes, and the
die already carries the answer - a filter rejecting everything up to 100 ns.
`stm32-blinky` fit one (C9, 100 nF), but a shipped board does not outrank a
checked "optional" in the vendor's own table.

Decision: **omit**. If kept anyway, keep it at 0.1 uF - larger slows the probe's
reset edge.

## 7. The 3V3 pin - a SENSE input, and what it can and cannot do

It is a **reference, not a rail**, and ST states the direction outright:
UM2448 Rev 9 calls STDC14 pin 3 `T_VCC`, "**Input for STLINK-V3SET**". ARM's
10-pin connector names pin 1 `VCC`; Hitex: "Note: The VCC is a reference not a
supply." The probe reads the target's supply, sets its level shifters to match,
and typically refuses to connect if it reads 0 V. Nucleo's VDD_TARGET is the
same and does not power an external target. (**Naming:** ST never says "VTREF"
for its own connectors - it is `T_VCC` or `VDD_TARGET`. Matters when
reconciling silk against the schematic.)

SEGGER states the function and forbids a series element outright (UM08001
section 13.5):

> "VTref is the target reference voltage. It is used by the J-Link to check if
> the target has power, to create the logic-level reference for the input
> comparators and to control the output logic levels to the target. It is
> normally fed from Vdd of the target board and **must not have a series
> resistor**."

So: wire it straight to +3V3, which is what the owner ruled. Nothing to size.

**Current drawn - now sourced, not assumed:**

| probe | VTref current |
|---|---|
| J-Link BASE / PLUS | "**< 25 uA**" |
| J-Link EDU Mini | "**< 170 uA**" |
| J-Link **before hardware v9.2** | mA class - UM08001 Table 1.2 notes that from v9.2 "Buffers on J-Link side are no longer powered through this pin" |
| any ST-LINK | **ST publishes no figure** |

Worst sourced case 170 uA, i.e. **0.17 %** of the board's < 100 mA budget. No
`power[]` entry is warranted; the power architect just needs to know the rail
has one more consumer. An antique pre-v9.2 J-Link would draw more, still
trivially inside budget.

**Back-powering - answered per probe, with vendor wording. No probe can
back-power this board through J2.**

| probe | sense pin | can it source power? |
|---|---|---|
| ST-LINK/V2 | pins 1/2 `VAPP` = "Target VCC", an input | 20-pin **pin 19** reads "VDD (3.3 V)" in ST's own table but its *target connection* column says "Not connected" - ST does not specify it as a target supply |
| ST-LINK/V2-1 (Nucleo CN4) | `VDD_TARGET` = "VDD from application" | No. Power pins live on the morpho headers, not the debug connector |
| STLINK-V3 | `T_VCC`, "Input for STLINK-V3SET" | **No** - UM2448 section 1 Note: "The STLINK-V3SET product **does not provide power supply to the target application**." |
| J-Link | VTref | **Not on VTref** - SEGGER: "VTref is only a voltage reference... **It is not intended to power the target system**." Power is on **20-pin pin 19 only**: "5V, max. current is 300mA", off by default via the `Power` command (KS/Kickstart models ship with it ON) |
| RPi Debug Probe / DAPLink | **no VTref pin at all** (3-pin SC/GND/SD, fixed 3.3 V I/O) | no power pin on the connector |

**The single real hazard is pin 19 of a 20-pin header - and J2 does not have
one.** A 5-position header carrying a VTREF-class sense pin has no back-power
path from any probe class checked. That is a stronger result than "low risk".

The bench rule in requirements.md section 3 still stands (power from J1 only,
never from the probe) because the board has no ORing and no protection by mode -
but the reason to keep it is procedure hygiene and the reversed-plug case in
section 9, not a documented back-drive path.

## 8. Layout guidance that genuinely exists

**First, the checked negative: ST publishes NO SWD-specific layout rule.**
Verified absent across AN4989 Rev 4, AN4325 Rev 2 section 5 "Recommendations",
AN4488 Rev 7 section 8 "Recommended PCB routing guidelines", AN5967 Rev 5
section 14, RM0360 and UM2448. AN4488 section 8.4 and AN5967 section 14.4 cover
SDMMC, FMC, QuadSPI/XSPI and **ETM** - SWD is simply not in them.

> **TRAP for a later phase: do not cite the 25 mm number as an SWD rule.**
> AN5967 Rev 5 section 14.4.5 says "Trace impedance: 50 ohm +/- 10 %. All the
> data traces must be as short as possible (<= 25 mm)" - that is the **ETM
> parallel trace port** (TRACECLK + D[0:3], running near HCLK/2), not SWD.
> Applying it to SWDIO/SWCLK would import a controlled-impedance requirement
> this interface does not have, onto a stackup that cannot deliver it.

What genuinely exists:

- **Keep the header near the MCU** - Lauterbach: "A direct and short connection
  (no buffer or level shifter) between the probe connector and the processor is
  recommended"; Hitex: "worth trying to keep the connector relatively close to
  the micro to maintain good signal integrity". **No vendor gives a number** -
  and none gives a maximum cable length either (the nearest quantitative
  statement anywhere is RPi's "over a few 10s of CM of cable and PCB ~30 MHz
  performance should still be achievable", *with* their 100 ohm terminations).
  ASSUMED bound **<= 50 mm** of SWDIO/SWCLK trace: inside section 3's strictest
  critical length with margin, trivially met at this size.
- **Ground the lead properly; do not rely on a long single ground wire** -
  SEGGER, on signal integrity: "**long ground leads can significantly worsen
  ringing and distortion**", and UM08001 requires at least one GND pin of the
  connector be connected. This is the flying lead's problem, but J2's ground pin
  placement is the board's half of it (section 9).
- **Ground adjacent to the clock** - ARM's 10-pin connector interleaves grounds
  with the debug signals (pin 3 GND beside pin 4 SWDCLK; pin 5 GND beside pin 6
  SWO), and ST's Nucleo 6-pin header does the same (1 VDD_TARGET, 2 SWCLK,
  3 GND, 4 SWDIO, 5 NRST, 6 SWO). Section 9 applies this to J2's pin ORDER.
- **Keep SWCLK clean; do not run it long and parallel to a net you care about**
  - it carries the fastest edge on the board (100 MHz knee) and is the only
  aggressor of note. The consequence of getting it wrong is sourced, from
  Lauterbach: "The debug interfaces are **not fault tolerant. A spike on the
  TCK/TMSC/SWCLK clock will most likely cause communication to fail**, requiring
  a re-initialization of the debug interface and a restart of the debug
  session." ST's nearest words are generic (AN4325 section 5.5: "a surrounding
  ground trace, shorter lengths and the absence of noisy and sensitive traces
  nearby (crosstalk effect) improve EMC performance", stated for
  interrupt/handshake signals). The only victims here are four plain digital
  GPIO. ASSUMED - no source gives an SWD spacing number.
- **Package geometry constrains placement more than any of the above** - on the
  TSSOP-20 SWDIO (19) and SWCLK (20) are adjacent at one corner and VSS/VDD
  (15/16) are on the same side, but **NRST is pin 4, on the opposite side**
  (DS Figure 8). J2 cannot take all four signals off one face; NRST comes around
  or under. A P6 placement fact, the architect's to set - not this fragment's.
- **The flying lead, not the PCB, is the transmission line** - a 100-200 mm
  unshielded lead with one ground return dominates everything on-board. No
  layout choice changes it; slowing SWCLK is the only lever and it is the
  probe's setting.

## 9. Connector convention and the reversal hazard

Field conventions for bringing SWD to 0.1 inch:

| convention | order | note |
|---|---|---|
| ARM Cortex Debug (the standard) | 1 VCC, 2 SWDIO/TMS, 3 GND, 4 SWDCLK/TCK, 5 GND, 6 SWO/TDO, 7 KEY, 8 NC/TDI, 9 GNDDetect, 10 nRESET | 0.05 inch 2x5, **shrouded and keyed** (pin 7 blocked) |
| **ST's own flying-lead SWD connector** (STLINK-V3SET CN6, UM2448 Rev 9 Table 11) | 1 T_VCC, 2 T_SWCLK, 3 GND, 4 T_SWDIO, 5 T_NRST, 6 T_SWO | 6 positions; Nucleo CN4/CN3 uses the same order |
| ST STDC14 (UM2448 Table 6) | ...3 T_VCC, 4 SWDIO, 5 GND, 6 SWCLK, 7 GND, 8 SWO... 11 GNDDetect, 12 T_NRST | pins 3-12 "respecting the ARM10 pinout" |
| informal 4-pin (this repo's stm32-blinky J2) | 1 SWDIO, 2 SWCLK, 3 3V3, 4 GND | no NRST |
| bb-mcu J2 (owner-fixed SET, order open) | 3V3, SWDIO, SWCLK, NRST, GND | 5 positions, no keying |

The owner-fixed **set** is sane: the ARM 10-pin minus SWO, TDI and the spare
grounds - exactly what a 2-wire SWD session on a Cortex-M0 needs.

**The order is still open** (requirements.md: "order is the layout engineer's
call") and it is not cosmetic. A 5-position unkeyed header can be plugged
180 degrees out; position i then meets 6-i, and **position 3 maps to itself**.

- `3V3 / SWDIO / SWCLK / NRST / GND` reversed puts **3V3 onto the probe's GND
  wire** - a hard short of the 3.3 V rail through the flying lead into a 0.5 A
  bench supply. This repo's reviewer already found exactly this on the shipped
  board: "ST-Link clones are wired pin-by-pin; swapping 3V3/GND shorts the
  debugger's 3.3 V rail to ground" (`stm32-blinky/reports/review-board.md`,
  WARNING 1).
- **`3V3 / SWCLK / GND / SWDIO / NRST`** puts GND on the centre pin, so a
  reversed plug maps **GND to GND** - no rail short - and puts GND immediately
  beside both debug signals. The residual reversed-plug fault is the probe's
  open-drain reset driving the board's 3V3 net: current-limited, recoverable,
  not a short.

**RECOMMENDATION: `3V3 / SWCLK / GND / SWDIO / NRST`.** This is not an invention
- it is **exactly ST's own STLINK-V3SET CN6 flying-lead order with SWO dropped**
(UM2448 Rev 9 Table 11: 1 T_VCC, 2 T_SWCLK, 3 GND, 4 T_SWDIO, 5 T_NRST, 6
T_SWO), which is also the Nucleo CN4/CN3 order. So it costs nothing, removes the
one destructive failure mode, puts ground between the debug signals as ARM's and
ST's connectors both do, and lets anyone wiring from ST's published pinout get
it right by reading straight down. A proposal, not a constraint; the owner gave
the order to the layout engineer.

**P6 silk (this is the one that gets forgotten).** With no keying, per-pin silk
is the ONLY thing preventing a reversed plug. `stm32-blinky` promised
silk-labelled pins in its architecture and **shipped without them**; WARNING 1
also records that its lone pin-1 square pad is covered by the header body after
assembly. So: label all five pins, text outside the connector body footprint,
plus a pin-1 marker that survives assembly.

## 10. What this fragment emits - and what would change it

Emitted: `high_speed: []`, `diff_pairs: []`, `voltages: []`, plus `notes`.

- **`high_speed` empty is an engineering call, not an omission.** This repo's
  shipped STM32 board agrees: `stm32-blinky`'s `architecture/constraints.json`
  declares only `/OSC_IN` and `/OSC_OUT` - **its SWD nets are not declared**.
  LEARNINGS.md 2026-07-30 `[check_return_path][stackup]` states the cost of
  declaring anyway: "declaring a net can only ever raise the finding count". On
  2 layers the B.Cu pour is unavoidably cut by through-hole pads and any
  bottom-side route, so a declared SWD net yields `corridor_void` findings that
  are unfixable by construction and meaningless at a 125 ns half-bit. Ground
  reference under the debug traces stays *guidance* (section 8), not a rule.
- **`diff_pairs: []` is EXPLICIT and that has semantics**: per
  `constraints_schema.md` an explicit empty list DISABLES `check_diffpair`
  board-wide; omitting the key lets it auto-discover by suffix. bb-mcu has no
  pair anywhere so both are no-ops, and `stm32-blinky` shipped `[]` - but merge
  it consciously. See OPEN.
- **`voltages` empty** (nothing exceeds 3.3 V); **no `power` entry** for the
  VTREF sense current; **no `placement` entry** - J2's edge and the
  NRST-crosses-the-package fact are the architect's to set at P2/P6.

**What would overturn the verdict:** SWCLK above ~50 MHz (no probe in this class
does it), SWO trace output added to J2 (excluded - owner fixed 5 pins, no SWO),
or SWDIO/SWCLK exceeding ~80 mm of trace. None is in play.

## Sources

- **ST datasheet DocID024849 Rev 3** (STM32F030x4/x6/x8/xC) - every MCU number:
  Table 11 note 7, Table 46 (25/40/55 kohm, C_IO 5 pF), Table 48 p64 (5 ns),
  Table 49 p65 (NRST R_PU, V_F 100 ns, V_NF 300 ns), Figure 21 p66 (0.1 uF),
  Figure 8 p26 (TSSOP20), 3.16. No JTAG/SWD AC table exists - checked negative.
  <https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_STMicroelectronics-STM32F030F4P6TR_C89040.pdf>
- **ARM IHI 0031G** *Arm Debug Interface Architecture Specification ADIv5.0-5.2*
  - **the normative source.** Section B4.3.2 "Line pull-up" p. B4-122 (the 100K
  SWDIO requirement); by full-document check, no SWCLK pull-down and no
  series-resistor requirement exist.
  <https://documentation-service.arm.com/static/622222b2e6f58973271ebc21>
- **ST AN4325 Rev 2** (DocID024966) *Getting started with STM32F030xx/F070xx
  hardware development* - the hardware AN for this family: 4.3.3, 6.1.4,
  Figure 7, Table 5 Mandatory vs **Table 6 Optional**, 5.5 EMC.
  <https://www.st.com/resource/en/application_note/an4325-getting-started-with-stm32f030xx-and-stm32f070xx-series-hardware-development-stmicroelectronics.pdf>
- **ST AN4989 Rev 4** *Introduction to debug toolbox for STM32 MCUs* - 4.1,
  4.2.1 ConnectUnderReset, 4.2.5 hardware reset + silent fallback, 5.2 SWD
  frequency. Contains **no** schematic, pinout, resistor, capacitor or layout
  content (full-text scan).
  <https://www.st.com/resource/en/application_note/an4989-stm32-microcontroller-debug-toolbox-stmicroelectronics.pdf>
- **ST RM0360 Rev 5** - 8.4.3 OSPEEDR reset 0x0C00 0000, 8.4.4 PUPDR reset
  0x2400 0000, 8.3.1, 26.3.2, and 26.3.3 vs **26.5.1** (section 4's
  contradiction).
  <https://www.st.com/resource/en/reference_manual/dm00091010-stm32f030x4x6x8xc-and-stm32f070x6xb-advanced-armbased-32bit-mcus-stmicroelectronics.pdf>
- **ST UM2448** *STLINK-V3SET* - Table 6 STDC14 (T_VCC "Input for
  STLINK-V3SET", GNDDetect), **Table 11 CN6 flying-lead order**, "up to
  24 MHz", section 1 Note "does not provide power supply to the target
  application". **ST UM1075 Rev 9** *ST-LINK/V2* - "SWD up to 4 MHz (default:
  1.8 MHz)", VAPP = "Target VCC" (input), pin 19 "Not connected".
  <https://www.st.com/resource/en/user_manual/um2448-stlinkv3set-debuggerprogrammer-for-stm8-and-stm32-stmicroelectronics.pdf>
  <https://www.st.com/resource/en/user_manual/um1075-stlinkv2-incircuit-debuggerprogrammer-for-stm8-and-stm32-stmicroelectronics.pdf>
- **ARM *Cortex-M Debug Connectors*** - 10/20-pin pinouts, KEY, GNDDetect,
  legacy IDC. Self-described as "for general information only and should not be
  used as a specification"; normative text is the CoreSight TRM appendix C.
  <https://documentation-service.arm.com/static/5fce6c49e167456a35b36af1>
- **SEGGER** - UM08001 section 13.5 (VTref definition, "must not have a series
  resistor", GND-pin requirement); J-Link BASE/PLUS "< 25 uA" and EDU Mini
  "< 170 uA" VTref current and 15 MHz / 4 MHz interface speeds (product spec
  tables); `kb.segger.com/VTref` ("not intended to power the target system");
  `kb.segger.com/20-pin_J-Link_Connector` (pin 19, 5 V / 300 mA, off by
  default); `kb.segger.com/Signal_Integrity` ("long ground leads can
  significantly worsen ringing and distortion"); `kb.segger.com/SWD`.
- **Raspberry Pi RP-003139-SP** *3-pin Debug Connector Specification* - the
  100 ohm source-termination recommendation and its three rationales, the
  "not strictly required but highly recommended" qualifier, and the "few 10s of
  CM ... ~30 MHz" cable statement. 3-pin SC/GND/SD, no VTref pin.
  <https://datasheets.raspberrypi.com/debug/debug-connector-specification.pdf>
- **Lauterbach** *Arm Debug and Trace Interface Specification* - SWCLK
  pull-down 1 k - 47 k (10 k recommended), the 47 ohm series resistor on
  target-driven lines only, "not fault tolerant... a spike on the
  TCK/TMSC/SWCLK clock will most likely cause communication to fail", and
  "A direct and short connection... is recommended".
  <https://repo.lauterbach.com/pdfnew/app_arm_target_interface.pdf>
- **Hitex, Andy Davison, *Selecting a debug header for Arm Cortex-M devices***
  - "The VCC is a reference not a supply"; "The nRESET signal is open drain";
  keep the connector close to the micro; keying is worth the cost.
  <https://www.hitex.co.uk/fileadmin/assets/Hitex_UK/Knowledgebase/Hitex_Tech_Tip_Selecting_Debug_Connector_for_Arm.pdf>
- **ST AN4488 Rev 7 section 8 / AN5967 Rev 5 section 14** - consulted only to
  establish section 8's NEGATIVE result and to identify the 25 mm ETM trap.
  (AN4488 section 6.3.3 independently repeats AN4325's "removes the need to add
  external resistors" for the F4 family.)
- **This repo** - `reference/stackups.yaml` (`JLC2313_1.6`), `build-modes.md`
  (`block-only`), `LEARNINGS.md` 2026-07-30 `[check_return_path][stackup]`,
  `boards/stm32-blinky/` constraints.json + both review reports + parts.json.
- **Johnson and Graham, *High-Speed Digital Design*** 1.3 - the t_r/6 rule.

**Retrieval provenance (about fetching, not content).** `st.com` refuses direct
fetches from this host; `developer.arm.com` / `support.arm.com` serve an empty
JS shell. Which is which matters:

- **First-hand:** the datasheet (LCSC's mirror of ST's PDF, rendered
  page-by-page to read Figure 21's 0.1 uF and Table 48's 5 ns), ARM **IHI 0031G**
  (downloaded as PDF from `documentation-service.arm.com`, B4.3.2 extracted
  locally), and ARM *Cortex-M Debug Connectors*. So the one normative ARM
  requirement here is first-hand.
- **Second-hand but revision-verified:** all ST app notes and user manuals
  (AN4325, AN4989, RM0360, UM2448, UM1075, UM1724), read via text-extraction
  proxies / byte-identical distributor mirrors against the canonical st.com
  URLs shown.
- **NOT obtained - do not cite without fetching:** ARM **DUI0499** (JS shell
  only). An earlier draft cited it for a pull-up range and a VTREF
  series-resistor limit; both were **removed** and replaced by IHI 0031G and
  SEGGER UM08001. Also **UM2237's** verbatim frequency list - nothing depends
  on it, since 4 MHz / 24 MHz come from UM1075 and UM2448 Features text.

## ASSUMED markers (everything above that is not sourced)

Down to four - the ST/ARM/SEGGER/RPi round of research retired three
(VTref current, J-Link pin 19, and the ARM pull-up value are now all sourced).

1. Probe output edge 2-5 ns - no vendor publishes one. Tested at 2 ns in
   section 3; conclusion holds.
2. Propagation delay 6 ps/mm - computed 5.6 ps/mm, rounded conservatively.
3. Max SWDIO/SWCLK trace 50 mm - no vendor number exists (checked); derived to
   sit inside the strictest critical length with margin.
4. SWCLK crosstalk spacing - no source gives an SWD number. The *consequence*
   of getting it wrong IS sourced (Lauterbach, section 8).

Not an ASSUMED but the judgement most worth re-reading: **section 5's rejection
of the vendor-recommended series resistors.** Three vendors recommend them
(47-100 ohm, target-driven line); the rejection rests on this fragment's own
settling arithmetic plus two explicit mode exclusions. It is the one place where
a defensible engineer could decide differently.
