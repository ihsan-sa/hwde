# Interface: USB 2.0 full-speed DEVICE (micro-B, bus-powered, STM32F103C8T6)

P1 research fragment. Machine-readable half: `research/interface-usb.json`.
Every number below carries a source; unsourced choices are marked `ASSUMED`.

## Sources

| Tag | Document |
|-----|----------|
| USB2.0 | Universal Serial Bus Specification Revision 2.0, April 2000 (full PDF read locally; sections/tables cited inline) |
| DS5319 | ST STM32F103x8/xB datasheet, DS5319 Rev 18 (cached at `boards/stm32-blinky/parts/C8734.pdf`) |
| AN4879 | ST AN4879 Rev 5 "USB hardware and PCB guidelines using STM32 MCUs", 30-May-2022 |
| AN11392 | NXP AN11392 Rev 1.1 "Guidelines for full-speed USB on NXP's LPC microcontrollers" (FS-specific layout guidance; ST removed its own FS layout section at AN4879 Rev 3 - see revision history) |
| STACKUP | `reference/stackups.yaml` -> JLC04161H-3313 `diff_90` profile |

## 1. Signal-integrity budget (the numbers that bind layout)

| Quantity | Value | Source |
|---|---|---|
| Signalling rate | 12 Mb/s, +/-0.25% for a non-HS-capable device (T_FDRATE 11.9700-12.0300 Mb/s) | USB2.0 Table 7-9 |
| Driver rise/fall time (10-90%, C_L = 50 pF) | **4 ns min, 20 ns max** | USB2.0 Table 7-9 + 7.1.2.1; DS5319 Table 45 (same 4/20 ns for the F103 PHY) |
| Rise/fall matching | 90-111.11% (USB2.0), 90-110% (F103) | USB2.0 Table 7-9 (T_FRFM); DS5319 Table 45 (trfm) |
| Driver output impedance Z_DRV (non-HS-capable) | 28-44 ohm, already embedded in the STM32 pad | USB2.0 Table 7-9; AN4879 Rev 5 FAQ |
| Cable / board differential impedance | 90 ohm +/-15%; "D+ and D- circuit board traces ... should also have a nominal differential impedance of 90 ohm" | USB2.0 7.1.1.3 |
| Upstream-port line capacitance (detachable cable) | C_INUB <= 100 pF per line; D+ vs D- must match within 10% | USB2.0 7.1.6.1 |
| ESD-diode capacitance for FS | <= 50 pF recommended | AN11392 2.6 |
| Bus pull-up | R_PU 1.5 kohm +/-5% on D+ to V_TERM 3.0-3.6 V | USB2.0 7.1.5.1 + Table 7-7 |
| VBUS load at the device end of the cable | <= 10 uF in parallel with 44 ohm, else inrush limiting required | USB2.0 7.2.4.1 |
| Suspend current (incl. pull-up/pull-down current) | 500 uA for a low-power device | USB2.0 7.2.3 |

`t_rise = 4 ns` is the number the pipeline gets: it is the FASTEST edge a
compliant FS driver may produce, so it is the conservative choice. Do not
substitute the 500 ps HS figure (USB2.0 Table 7-8) - this design has no HS path.

### Derived (computed with the pipeline's own `lib/impedance.py`, JLC04161H-3313)

Outer-layer microstrip over In1.Cu: h = 0.2104 mm, er = 4.05, t = 0.035 mm.
`diff_pair(90 ohm)` -> w = 0.314 mm, s = 0.2104 mm (matches STACKUP `diff_90`).

- er_eff = 3.03 -> v = 172 mm/ns -> **5.81 ps/mm** propagation delay.
- Edge spatial length at t_r = 4 ns: 689 mm.
- Critical (transmission-line) length, t_r/6 criterion: **115 mm**; the stricter
  t_r/10 criterion: 69 mm. The connector-to-MCU run on a 55x45 mm board is
  ~20-40 mm, i.e. **3-6x below** the point where the trace behaves as a
  transmission line.
- Intra-pair skew: 5 mm = 29 ps = 0.7% of the 4 ns edge. Physical budget
  (10% of t_r, the usual common-mode-conversion bar) = 400 ps = **69 mm**.

**Honest read on 90 ohm:** FS at these lengths does not NEED controlled
impedance - AN11392 3.2 states it plainly ("Although it is recommended to
implement 45 ohm signal traces, for full-speed USB, it is not critical for
obtaining good results. Keep your signal traces as short as possible"). But on
JLC04161H-3313 the 90 ohm geometry is FREE (it is a published profile, no extra
fab cost, and the width 0.314 mm is routable), so target it as good practice and
for cable-match/EMI margin. If the architect drops to a 2-layer stackup, 90 ohm
becomes unachievable (no adjacent plane) and should be dropped rather than
faked - keep the pair short and coupled instead.

**Honest read on skew:** at FS the 5 mm bar is a tidiness bar, not physics.
`check_diffpair` warns above `max_skew_mm` and errors above 2x it, so 5.0 gives
warning 5-10 mm / error >10 mm - both an order of magnitude inside the 69 mm
physical budget. A skew warning on this board is cosmetic; do not spend fix
loops chasing it beyond a trivial reroute.

## 2. Emitted constraints (see interface-usb.json)

```
high_speed: /USB_DP, /USB_DM  reference GND, k 3, t_rise_ns 4.0,
                              return_via_radius_mm 2.0
diff_pairs: /USB_DP + /USB_DM  impedance_ohm 90, gap_mm 0.52,
                               max_skew_mm 5.0, max_uncoupled_mm 5.0
voltages:   [] (max on-board potential is 5 V VBUS - nothing near the 30 V
                creepage trigger; requirements.md 8)
```

Per-key justification:

- `reference: "GND"` - the pair must run over an unbroken ground plane; this
  also makes `planes_gen` guarantee a GND pour on the reference layer and makes
  `check_return_path` flag any plane gap crossed by the pair. Required by
  every SI source; USB2.0 does not mandate a plane but 7.1.1.3's 90 ohm target
  is only meaningful against one.
- `k: 3` - pipeline default corridor (3x trace width) for the plane-continuity
  check. ASSUMED (no standard sets this); default retained deliberately.
- `t_rise_ns: 4.0` - USB2.0 Table 7-9 min FS rise time (see above).
- `return_via_radius_mm: 2.0` - **ASSUMED** (good practice: a GND return via
  within ~2 mm of any layer transition on the pair). Needed because the
  t_rise-derived radius at 4 ns is `c/(f_knee*20)` = 119.9 mm, i.e. larger than
  the board - the check would become vacuous. `check_return_path.net_entry_radius`
  gives an explicit `return_via_radius_mm` precedence over `t_rise_ns`, so both
  keys are emitted on purpose. Best outcome is still ZERO vias on the pair.
- `impedance_ohm: 90` - USB2.0 7.1.1.3. Consumed by `rules_gen` as the
  DIFFERENTIAL target; it resolves to w 0.314 / gap 0.2104 mm on the chosen
  stackup and becomes the `Diff90` net class + `aiee_diff_gap_USB` DRC rule.
- `gap_mm: 0.52` - nominal CENTRE-TO-CENTRE pitch = 0.314 + 0.2104. NOT the
  edge-to-edge gap: `check_diffpair` measures centreline-to-centreline distance
  (shapely `distance()` between track centrelines) and uses this value only to
  derive the coupling threshold `max(3*pitch, pitch+0.5)` = 1.56 mm.
  **Stackup-dependent** - recompute (or drop the key and let the script
  auto-derive from the routed median) if P2 picks a different stackup.
- `max_skew_mm: 5.0` / `max_uncoupled_mm: 5.0` - pipeline defaults retained;
  ASSUMED as good practice (USB2.0 sets no PCB skew number for FS; the
  standard's only matching requirement is the driver's 90-111.11% edge
  matching, which is internal to the PHY). Rationale above.

## 3. STM32F103-specific facts (verified, not assumed)

**DP pull-up is NOT internal on the F103. An external 1.5 kohm to 3.3 V is
mandatory.** Three independent confirmations:

- AN4879 Rev 5 Table 3, column "Embedded pull-up resistor on USB_DP line":
  the STM32F102/F103 line row reads `-`, with footnote 2 - "To be compliant
  with the USB 2.0 full-speed electrical specification, the USB_DP (D+) pin
  must be pulled up to a voltage in the 3.0 to 3.6 V range with a 1.5 kohm
  resistor."
- AN4879 Rev 5 Table 4 (mainstream products), row "Pull-up resistor on USB_DP
  line", STM32F102/STM32F103 column: "1.5 kohm resistor must be added".
- DS5319 Rev 18 Table 44 note 2: same sentence for the USBDP pin.

AN4879 Figure 5/7 specify **1.5 kohm +/-1%** (tighter than USB2.0's +/-5%).
Recommend 1.5 k 1% to +3V3. Note the widespread "Blue Pill" clone bug: many
carry 10 k here and fail enumeration - do not copy that value.

Soft-connect (GPIO/PNP switched pull-up) is NOT needed: USB2.0 7.1.5.1 only
requires that the pull-up supply be "derived from or controlled by the power
supplied on the USB cable", and on a bus-powered board +3V3 comes from VBUS
through the buck, so a direct 1.5 k to +3V3 satisfies it. (AN4879 3.1.1 requires
the switched pull-up only for SELF-powered designs; AN11392 2.2 gives the same
rule and cites the 400 mV back-voltage compliance test as the reason.)

**No series resistors on D+/D-.** AN4879 Rev 5 FAQ: "On the internal USB PHYs,
the matching output impedance is already embedded in the pad transceiver and is
in line with the USB specification. No external resistors are needed." AN4879
3.1 repeats it: "The USB FS impedance driver is always managed internally to
avoid the need to add external serial resistors on the data line path." The
22R/33R series resistors seen on LPC (AN11392 2.1, whose PHY is under-impedance)
and on many F103 clone boards would push Z_DRV outside the 28-44 ohm window.

**Pins.** DS5319 Rev 18 pin table: PA11 = USBDM (D-), PA12 = USBDP (D+), both
`I/O FT` where footnote 2 defines `FT = 5 V tolerant`. LQFP48 pins 32 (PA11) and
33 (PA12) - adjacent, so the pair breaks out matched with no crossover.

**Clock.** AN4879 2.4: the FS USB device requires a precise 48 MHz clock; when
generated from the main PLL "the clock source must use an HSE crystal
oscillator". AN4879 FAQ: "HSE ON with an external crystal or HSE in bypass mode
are required, but HSI cannot be used." AN4879 Table 4 shows "Crystal-less USB:
-" for the F102/F103. The requirements' 8 MHz crystal is therefore mandatory,
not optional. Data rate tolerance +/-0.25% (USB2.0 Table 7-9) is loose for a
crystal: any +/-30 to +/-50 ppm part clears it by ~50x.

**Supply.** USB transceiver operating range 3.0-3.6 V (AN4879 2.5); the F103 USB
is functional down to 2.7 V but "the full USB electrical characteristics are
degraded in the 2.7 to 3.0 V VDD voltage range" (DS5319 Table 44 note 3) and
certification tests such as the eye diagram fail there (AN4879 FAQ). The 3.3 V
buck rail must therefore hold >= 3.0 V under load - a real constraint on the
AP63203's output tolerance + droop, which the power architect should honour.
F103 USB is USB-IF certified FS (AN4879 Table 13, TID 40000455).

## 4. VBUS handling

- **VBUS sensing is not required here.** AN4879 2.6: "The USB device is
  bus-powered. VBUS sensing is not mandatory (USB is always connected when the
  device is powered)". Recommend omitting it (saves 2 parts). Note also that the
  F103's USB peripheral has no OTG VBUS-sense block at all - any VBUS sense
  would be a plain GPIO/ADC read.
- If firmware wants it anyway: AN4879 2.6 recommended divider for VDD 3.0-3.6 V
  is **33 kohm to VBUS / 82 kohm to GND** into a 5 V-tolerant GPIO (all F103
  `FT` pins qualify). Constraints from the same section: the divided voltage
  must stay below 4 V and above 0.7 x VDD, and a 5 V-tolerant pin must never
  exceed VDD + 4 V - which is why raw VBUS must not touch a GPIO directly, and
  matters most when VBUS is live while the MCU is unpowered.
- Cost of the divider: ~43 uA continuous from VBUS. It counts against the
  500 uA USB suspend budget (USB2.0 7.2.3 - "the current from VBUS through the
  bus pull-up and pull-down resistors must be included"), alongside the ~200 uA
  the 1.5 k pull-up draws against the host's 15 k pull-down. 243 uA of the
  500 uA budget spent before the MCU's own suspend current: fine for a bench
  dev board, worth knowing if suspend compliance is ever wanted.
- **VBUS bulk capacitance <= 10 uF** including capacitance visible through the
  regulator (USB2.0 7.2.4.1: "The maximum load (C_RPB) that can be placed at the
  downstream end of a cable is 10 uF in parallel with 44 ohm ... If more bypass
  capacitance is required in the device, then the device must incorporate some
  form of VBUS surge current limiting"). Hands the power architect a hard cap on
  the AP63203 input capacitor stack.

## 5. Connector, ESD, shield

**Micro-B pinout** (KiCad `Connector:USB_B_Micro`, verified in the 10.0 symbol
library): 1 VBUS, 2 D-, 3 D+, 4 ID, 5 GND, `SH` Shield. The pipeline's
`sch_build._apply_pin_number_fixups` renumbers `SH` -> `6` to match footprints
(LEARNINGS 2026-07-11 [python] entry). Mapping: pin 2 -> `/USB_DM` -> PA11,
pin 3 -> `/USB_DP` -> PA12.

**ID pin: leave unconnected.** Device-only, no OTG. AN4879 3.3: "The ID pin is
required in dual role only."

**ESD.** AN4879 2.3 requires compliance with JESD22-A114D (HBM, 2 kV on the USB
pins - the STM32 already meets this) and IEC 61000-4-2 for lines exposed at a
receptacle, and says the protection "has to be placed as close as possible to
the receptacle". AN4879 Table 11 recommends for USB FS: **USBLC6-2SC6** on
D+/D- (+ **ESDA7P60-1U1M** on VBUS), or USBLC6-2P6 for minimum area. Design
rules that follow from the standard:

- put the TVS in-line at the connector so the pair passes THROUGH it (no
  stubs), with its GND pin dropping straight into the plane;
- use a matched 2-channel array rather than two singles, because USB2.0 7.1.6.1
  requires D+ / D- capacitance to match within 10%;
- capacitance headroom is generous at FS: <= 50 pF per line is the FS
  recommendation (AN11392 2.6) and USB2.0 7.1.6.1 caps the whole upstream port
  at 100 pF/line, so any USB-rated array clears it. No need to pay for an
  ultra-low-Cj HS part.

**Do not add** ferrite beads on D+/D- (USB2.0 7.1.6.1: "Use of ferrite beads on
the D+ or D- lines of full-speed devices is discouraged"; AN11392 2.6 agrees) or
edge-rate capacitors (optional per USB2.0 7.1.6.1 / AN11392 2.6 at <= 50 pF and
only next to the MCU - not needed for an ST PHY that already meets the eye).

**Shield / GND.** USB2.0 6.8 deliberately leaves the device-side scheme open:
"The shield must be terminated to the connector plug for completed assemblies.
The shield and chassis are bonded together. The user selected grounding scheme
for USB devices, and cables must be consistent with accepted industry practices
and regulatory agency standards for safety and EMI/ESD/RFI." For a bare,
bus-powered board with a single ground system and no chassis, the accepted
practice is a **direct shell-to-GND bond** at the connector (shortest ESD path,
no floating metal). ASSUMED as the recommendation. The alternative - ferrite
bead (AN11392 2.6 Figure 2, component L1) or a 1 Mohm || 4.7 nF snubber between
shell and GND - only pays off when the board has a separate chassis ground, and
it requires the shield pads to sit on their own copper island, so P2 must decide
before layout rather than after.

## 6. Layout rules to carry into P5-P7

Sourced from AN11392 3.1/3.2 (the FS-specific guidance; ST removed its
equivalent section at AN4879 Rev 3 per that document's revision history) plus
USB2.0 7.1.1.3:

1. Keep D+/D- parallel and tightly coupled over their whole run; match lengths
   as closely as possible.
2. Keep the run SHORT and direct - this matters more at FS than impedance does.
3. Minimise right-angle corners and vias (each via is an impedance and
   return-path discontinuity).
4. Solid GND reference under the entire pair; no split, slot or plane gap
   crossed.
5. Keep the pair away from the switching node and inductor of the AP63203 buck,
   and route VBUS away from D+/D- (AN4879 3.3 gives the same advice for its OTG
   layout).
6. Place the micro-B receptacle at a board edge (mechanical: the plug must
   seat) - the architect's `placement.edges` entry, not a signal constraint.

## 7. ASSUMED items (no standard number exists)

| Item | Value | Why |
|---|---|---|
| `return_via_radius_mm` | 2.0 | good practice; t_rise-derived value (119.9 mm) would disable the check |
| `max_skew_mm` | 5.0 | tidiness bar; physical FS budget is ~69 mm |
| `max_uncoupled_mm` | 5.0 | pipeline default; USB2.0 has no PCB coupling number |
| `k` | 3 | pipeline default corridor width |
| Shield bond | direct to GND | USB2.0 6.8 defers to industry practice |
| Pull-up tolerance | 1.5 k 1% | AN4879 figures say 1%; USB2.0 allows 5% |
