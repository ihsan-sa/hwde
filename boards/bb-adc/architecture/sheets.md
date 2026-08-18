# sheets.md - bb-adc sheet plan, refdes ranges, CANONICAL net names

## 1. Sheet plan: ONE FLAT ROOT SHEET

| Sheet | File | Blocks it carries | Interface nets at its boundary | Refdes ranges | `pwr_base` |
|---|---|---|---|---|---|
| root (only) | `kicad/bb-adc.kicad_sch` | B1 attenuator, B2 buffer, B3 converter, B4 reference, J1 input, J2 host header, H1-H4 mounting | none - the board's only interfaces are the two physical connectors (`/AIN_RAW` + `GND` at J1; `+3V3`, `GND`, `/CS`, `/SCLK`, `/DOUT` at J2) | `U1-U9`, `R1-R19`, `C1-C19`, `J1-J9`, `H1-H9` | **1** (`#PWR01..`, `#FLG01..`) |

**A hierarchical split is deliberately REJECTED, and this is a considered
deviation from the architect role's default instruction.** The reason is
recorded, machine-verified and has already cost two boards on this project:
a wiring label inside a CHILD sheet exports to the netlist as
`/<sheet>/<LABEL>`, not `/<LABEL>` (LEARNINGS 2026-07-22, kicad-sch-api 0.5.6
hierarchy semantics: child-internal nets become `/<sheet>/NAME`; only nets
merged to the root through a sheet pin keep the root-side name). Every
`constraints.json` entry that spells the net `/<LABEL>` then silently no-ops -
`check_current` finds no copper on a net that does not exist and reports
nothing. That is the P4 amendment class that cost `lumina-par`, and the reason
`bb-buck` and `sbuck-5v3a` are also flat.

This board has 20 electrical parts and 14 nets (s2's table is the count; the
earlier "12" was already one short of its own table). It fits one A4 page with room
to draw the guard ring symbolically. The cost of hierarchy here is real and its
benefit is zero.

Refdes ranges are therefore trivially unique. They are stated anyway because
the rule is "unique ACROSS sheets": **if a later amendment ever splits this
sheet, the natural cut is `afe` (J1, R1-R6, U3, C6, C7) and `digital` (U1, U2,
R7, J2, C1-C5, C8), which take `pwr_base = 40` and `80` and keep the prefix
ranges above** - and every net name in s2 must then be re-checked against the
new export.

## 2. CANONICAL NET NAMES - these are now binding

`research/power.json` proposed `+3V3 / VREF / GND` and left the signal names
open. P2 fixes all of them here. These are the names the schematic MUST
produce and the names `constraints.json` uses.

| Canonical net | KiCad mechanism | Spans | Declared in constraints.json as |
|---|---|---|---|
| **`+3V3`** | power symbol (VALUE = net name) -> exports BARE | J2.1 -> C1 -> **R7** , U2 IN, U3 V+ | `power` 11 mA |
| **`VDD_ADC`** | power symbol with **Value = `VDD_ADC`** -> exports BARE | **R7 -> C2 -> C8 -> U1 VDD.** The converter's supply pin ONLY | `power` 3 mA |
| **`GND`** | power symbol -> exports BARE | everything; B.Cu pour; J2.2 and J2.6 | `power` 11 mA `plane_fed` `pdn:false`, `planes` B.Cu |
| **`VREF`** | power symbol with **Value = `VREF`** -> exports BARE | U2 OUT -> C5 -> C3 -> U1 VREF pin | `power` 1 mA |
| **`/AIN_RAW`** | root-sheet LOCAL LABEL -> ONE leading slash | J1.1 -> R1 | `voltages` 5 V |
| **`/ATT_A`** | root local label | R1 -> R2 | not declared (see s4) |
| **`/ATT_B`** | root local label | R2 -> R3 | not declared |
| **`/AIN_DIV`** | root local label | R3 -> R4 -> U3 `+IN`. **THE high-Z tap, 240 kohm Thevenin** | not declared - it is a placement/routing constraint, not a width rule (s4) |
| **`/ATT_C`** | root local label | R4 -> R5 | not declared |
| **`/AIN_BUF`** | root local label | U3 OUT -> U3 `-IN` (follower) -> R6 -> **and the GUARD RING copper** | not declared |
| **`/AIN_ADC`** | root local label | R6 -> C7 -> U1 `+IN` | not declared |
| **`/CS`** | root local label | J2.3 -> U1 CS (active low; the bar is documentation, not part of the net name) | `high_speed` ref GND |
| **`/SCLK`** | root local label | J2.4 -> U1 DCLOCK | `high_speed` ref GND |
| **`/DOUT`** | root local label | U1 DOUT -> J2.5 | `high_speed` ref GND |

Why `VREF` and not `+2V048`: it is a rail feeding a power pin and decoupled at
both ends, so it is a power symbol, and a power symbol's exported name is bare.
`VBUS` sets the precedent for a bare non-numeric power net. `VDD_ADC` follows
the same rule for the same reason - a rail feeding a power pin, bypassed at
that pin - and it exists because **R7 splits the converter's supply off
`+3V3`**, and KiCad cannot put one net on both pins of a resistor. **A power
symbol WINS over a coincident local label** (LEARNINGS 2026-07-28), so P4 must
not mix the two mechanisms on one node, and `component.value = x` is the only
way to set a power symbol's Value (`set_property("Value", ...)` is a silent
no-op on kicad-sch-api 0.5.6) - which now applies to TWO symbols, `VREF` and
`VDD_ADC`.

**Enforcement, not hope:** at P4 run
`netlist_audit.py --net kicad/bb-adc.net --constraints architecture/constraints.json`.
A net spelled differently in the schematic surfaces as `missing_net` (error).

## 3. Contents of the root sheet

| Refdes | Part class | Net attachments |
|---|---|---|
| `U1` | 16-bit SAR, SPI peripheral, VDD 2.7-3.6 V, external VREF pin 0.1 V..VDD, input range includes 0 V, offset AND gain specified as MAXIMA (**ADS8326IB** class) | VDD=**`VDD_ADC`** (behind R7), GND=`GND`, VREF=`VREF`, `+IN`=`/AIN_ADC`, **`-IN`=`GND` AT R5's BOTTOM PAD - read the note below before wiring it**, CS=`/CS`, DCLOCK=`/SCLK`, DOUT=`/DOUT` |
| `U2` | 2.048 V series voltage reference, <= 0.02 % initial max, <= 2 ppm/degC max, Vin_min <= 3.035 V (**ADR4520B** class) | IN=`+3V3`, GND=`GND`, OUT=`VREF` |
| `U3` | unity-gain follower, CMOS input, RRIO, Vos <= 100 uV max, Ib <= 400 pA over temp (**OPA333** class; **OPA320** the same-footprint alternate) | V+=`+3V3`, V-=`GND`, `+IN`=`/AIN_DIV`, `-IN`=`/AIN_BUF`, OUT=`/AIN_BUF` |
| `R1` `R2` `R3` | attenuator TOP arm, 3 x 200 kohm 0.02 % / 10 ppm, ONE part number with `R4`/`R5` | `/AIN_RAW`-`/ATT_A`-`/ATT_B`-`/AIN_DIV` |
| `R4` `R5` | attenuator BOTTOM arm, 2 x the same 200 kohm part | `/AIN_DIV`-`/ATT_C`-`GND` |
| `R6` | ADC input isolation, 20-100 ohm (sim benches 2/3 set it) | `/AIN_BUF` / `/AIN_ADC` |
| `R7` | **converter rail-entry isolation, 5-10 ohm (10 ohm class), 0402/0603 thick film** - per the ADS8326's own recommended application circuit | `+3V3` / `VDD_ADC` |
| `C1` | 10 uF X7R bulk, **at the J2 entry, not at the converter** | `+3V3` / `GND` |
| `C2` | 100 nF X7R, converter VDD - **the SMALLER of the pair, so it sits closest to the pin** | `VDD_ADC` / `GND` |
| `C3` | converter VREF bypass - **47 uF class low-ESR** per the ADS8326's reference-input section, which is inside the ADR4520's 1-100 uF stable window (see `C5`) | `VREF` / `GND` |
| `C4` | 100 nF X7R, reference IN | `+3V3` / `GND` |
| `C5` | reference OUT cap - **MANDATORY and >= 1 uF.** NOT a DNP candidate | `VREF` / `GND` |
| `C6` | 100 nF X7R, buffer V+ | `+3V3` / `GND` |
| `C7` | 1-2.2 nF **C0G/NP0** at the converter input pin | `/AIN_ADC` / `GND` |
| `C8` | **10 uF X7R at the converter VDD pin**, beside `C2` and behind `R7` | `VDD_ADC` / `GND` |
| `J1` | 2-pole 5.08 mm THT screw terminal, silk-marked SIG and GND | 1=`/AIN_RAW`, 2=`GND` |
| `J2` | 6-pin 2.54 mm single-row male THT header | 1=`+3V3`, 2=`GND`, 3=`/CS`, 4=`/SCLK`, 5=`/DOUT`, 6=`GND` |
| `H1`-`H4` | M3 clearance holes, 3.2 mm | mechanical (no net) |

### `U1 -IN` IS A DEDICATED SENSE RUN, NOT A GROUND SYMBOL

Electrically `-IN` is on `GND`, so a netlist cannot tell the difference - which
is exactly why this note exists. **Wire `U1 -IN` to the point where `R5`'s
bottom pad meets `GND`** (the attenuator string's bottom node), as its own
connection. Do NOT drop a `GND` power symbol next to the converter and call it
done: that deletes the board's largest error-cancellation mechanism silently
and nothing downstream will report it.

The reason: **a divider passes a ground offset at UNITY while dividing the
signal by K = 0.400**, so any offset between the string's bottom node and the
converter's negative reference is referred to the input multiplied by
1/K = 2.5. **1 mV of copper offset = 2.5 mV at the terminal**, half the 25 degC
budget. Sensing at the string bottom cancels it exactly: `+IN` carries
`V_tap + (GND_A - GND_C)`, `-IN` carries `(GND_A - GND_C)`, difference
`V_tap`. **Bounded:** the ADS8326 specifies `-IN` at **-0.3 V to +0.5 V**
relative to device ground, so the sense point must be a node whose offset stays
in the millivolts - which R5's pad is, and which a distant or shared-return
ground is not. The bottom of the string is a *reference tie*, not a ground
connection: it must not share copper with a return carrying other current.
Carried in `constraints.json` as the `R5`->`U1` corridor; see `blocks.md` s8.1.

### `R7` + `C2` + `C8`: the converter's rail entry, and it is datasheet-required

`R7` (5-10 ohm) goes between `+3V3` and `U1`'s VDD pin, **upstream of both
caps**, with `C2` (0.1 uF, smaller, closest to the pin) and `C8` (10 uF) on the
`VDD_ADC` side. This is the ADS8326's own recommended application circuit, so
it is what the datasheet REQUIRES, not "filtering the datasheet does not
require" - the distinction the scope tier actually draws. A SAR has no supply
rejection at the instant that matters, because the spikes that hurt land just
before the comparator latches.

**It isolates `U1` alone.** `U2` and `U3` stay on `+3V3` upstream of `R7`, for
the same reason the source figures put the reference and the op amps on the
analog rail rather than behind the converter's RC. Cost: ~0.6 mV of DC drop at
a ~60 uA typical draw, which costs the error budget nothing (the conversion is
referenced to `VREF`, not to VDD) and leaves VDD inside 2.7-3.6 V on the worst
-case rail. **No ferrite anywhere** - that one is still the reflex addition
nothing here requires.

### `C5` is mandatory, and it is why there is no reference buffer on the BOM

The ADR4520 specifies a stable output-capacitance **WINDOW of 1 uF min to
100 uF max**, two-ended, and the 2.048 V member is one of the two that need the
full 1 uF (the >= 3.0 V members need only 0.1 uF). The output cap is a
compensation element inside the loop, so **both ends bind and `C5` cannot be
DNP**. That same window contains the ADS8326's 47 uF-class REF bypass (`C3`),
which is what closed the open risk that this board might need a reference
buffer or a series isolation resistor between the reference and `C3`:
**neither is fitted, and the reference drives the converter's bypass directly.**
If a current-limiting resistor were ever needed there it goes between the
reference SOURCE and `C3` - never between `C3` and the VREF pin, where it would
sit in the per-bit pulse path.

**J2 is 6 pins, and the sixth is GND, not a spare.** The chosen converter's SPI
is read-only (CS, DCLOCK, DOUT - no MOSI), so the block needs 5 pins. The
answered Q6 default reserved 6. Spending the sixth on a second GND puts a
return reference at BOTH ends of the digital group, which is the return-path
requirement D3/D4 already impose, rather than leaving a floating pin. It is
support for the interface, not a feature.

**No series damping on `/SCLK` or `/CS`, no pull-up on `/CS`.** Both are
"conditioning the datasheet does not require" and the scope tier excludes them;
`/CS` is driven by the host at all times the board is powered, and the one
hot-plug hazard that a pull-up would not fix is already recorded and accepted
(answered Q5).

**The follower's feedback is a WIRE.** `U3 -IN` ties directly to `U3 OUT`, no
resistor. A gain-setting network there would put two more tolerances and two
more leakage nodes into the budget for no benefit - the attenuation is already
done, precisely, upstream.

## 4. Nets deliberately left OUT of `constraints.json`

`/AIN_RAW` is declared only in `voltages` (5 V, which makes `check_creepage` a
clean, visible no-op). `/ATT_A`, `/ATT_B`, `/AIN_DIV`, `/ATT_C`, `/AIN_BUF`
and `/AIN_ADC` are declared nowhere, on purpose:

- A `power` entry on any of them would give a high-impedance sense node a
  minimum-width rule and pull it into `check_pdn`'s decoupling inventory.
  `/AIN_DIV` in particular wants to be SHORT and THIN and nowhere near
  anything, which is the opposite of what a width rule expresses.
- A `high_speed` entry would be a lie: they are DC nodes. Their sensitivity is
  to LEAKAGE and to CAPACITIVE COUPLING FROM the SPI nets, which is why the
  three SPI nets ARE declared `high_speed` (that check verifies THEIR return
  path is continuous, which is the mechanism that keeps their return current
  out of the analog region) and why the protections for the analog nodes live
  in `placement.corridors`, `placement.separation` and the prose rules D1-D5.

The rules that DO apply to them are layout rules, carried in
`constraints.json` `placement` and in s5 below.

## 5. Placement groups this sheet implies (they become P6 groups)

- **`attenuator`** (anchor `U3`; `R1`-`R5`, `R6`, `C6`, `C7`): the five string
  elements in physical order R1->R5 with the R3/R4 junction adjacent to `U3`'s
  `+IN` pad. `/AIN_DIV` is the SHORTEST high-impedance run on the board - a few
  millimetres, not the most convenient route. **The guard ring is part of this
  group's geometry:** `/AIN_BUF` copper encircles the `/AIN_DIV` trace and
  `U3 +IN` on F.Cu with clearance on both sides, and solder-mask relief over
  the ring. An annealer optimising a cost function cannot discover a guard
  ring; this cluster is placed by explicit `place_edit` and LOCKED before
  `place_anneal` runs.
- **`reference`** (anchor `U2`; `C4`, `C5`): sits beside `U1`'s VREF pin.
- **`converter`** (anchor `U1`; `C2`, `C3`, `C8`, `R7`): `C3` within 2.5 mm of
  the VREF pin, SAME layer, no via between pad and cap - and what binds is the
  charge LOOP (`C3` -> REF pin -> the internal array -> the converter's GND pin
  -> back), so wide copper out AND back, and nothing in series between cap and
  pin. `C2` within 2 mm of VDD with its ground via within 1 mm of its own pad -
  that loop is the SPI drivers' current loop and must stay under 20 mm^2 (D3).
  `R7` upstream of `C2`/`C8`, `C2` (the smaller) closest to the VDD pin.
- **`entry`** (anchor `J2`; `C1`): the bulk cap at the rail entry, not at the
  converter.

Spatial order across the board, from D4: **`J1` -> `attenuator` -> `converter`
+ `reference` -> `J2`**, with `J1` and `J2` on DIFFERENT edges, openings
outward. Everything is on the FRONT side - single-sided assembly, and a part
moved to the back would also cut the B.Cu return pour that D1 requires
unbroken, so every ref carries an explicit `sides: front`.

## 6. Handover to P4

1. Build the root sheet flat. Power symbols for `+3V3`, `GND`, `VREF` (the last
   one with its Value edited); root local labels for everything else.
2. `netlist_audit.py --net ... --constraints ...` must come back clean before
   P5 touches the board.
3. Any net whose exported name differs from s2 is reconciled IN
   `constraints.json` at that moment, not later - an entry naming a net that
   does not exist fails silently, which is the whole reason this board is flat.
