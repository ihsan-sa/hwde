# LUM-DTR-STROBE-A - RGBW light engine SPECIFICATION

P2 architect, 2026-07-28 (rev B, created at the H1 revision). **Authority:**
`requirements.md` s10.4 - *"The RGBW LED module is not designed by this run. This run produces a
specification complete enough that someone else can build the MCPCB."*

**This is a specification, not a design.** It is written as **24 numbered acceptance criteria
`LE-01 .. LE-24`, each independently checkable**, so that a third party can build the module and a
reviewer can sign off each line without reading the rest of the package.

Sources: `research/led-emitter.md` (the white-only survey - 33 live JLCPCB queries, 169 SKUs),
`research/refdesign-pulsed-led-driver.md` D9, `architecture/power_tree.md` s9 (per-colour light
output) and s10 (ambient sensitivity), `architecture/blocks.md` s2.3 (harness) and s6.2 (currents).

---

## 0. Scope, and the one thing that makes this specifiable at all

**The emitter array lives on its own single-layer aluminium MCPCB, bolted to a heatsink, wired back
to this board by a six-conductor power loom and a four-conductor sensor loom.** The MCPCB, its
heatsink, its optic, its emitters and its loom are a **separate deliverable** which the ai-ee run
does not design, does not source and does not verify.

The board's entire obligation to the module is the interface in s2 and the numbers in s3.

### 0.1 Two things this module is NOT constrained by, and one it now is

**NOT constrained by LCSC/JLCPCB stock.** The module is **off-board and specified rather than
designed**, so it is **not a JLC PCBA line item** and **not bound to the LCSC catalogue the way the
par's on-board emitters are.** It is a mechanical/optical BOM bought from **Digi-Key, Mouser,
RS/Farnell or LCSC retail**, and **every part named in this document shall carry its distributor**
alongside its MPN (LE-24). That is a real degree of freedom the par run did not have, and it should
be used: it dissolves `research/led-emitter.md`'s central constraint - *no JLC-stocked white LED is
DC-rated for 2.6 A* - and it is why LE-04 can demand a real DC rating instead of an over-driven one.
It also means **the par's finding that every Cree XLamp colour line is at zero stock at LCSC does
not bind this module** - the same parts are ordinarily stocked at Digi-Key and Mouser.

**NOT constrained by the absence of a pulsed derating curve.** There isn't one, in any colour, from
any vendor, at 5-200 ms. LE-26 makes recording that absence an acceptance criterion rather than a
blocker.

**NOW constrained by a closed enclosure decision.** The enclosure is **sealed, non-metallic and NOT
vented, with this heatsink bolted to or through the wall.** Both fixtures in the program share that
design; the par independently reached the same conclusion and **measured a sealed non-metallic box
at 3.6-4.3 K/W internal-air-to-room.** It closes **only** because the LED heat leaves through the
wall instead of into the box - which is why **LE-16 is now the load-bearing criterion in this
document** and why it carries an apportioned Rth budget rather than a description.

**The single most important fact carried from research, and it applies to all four colours:**

> **No LED vendor publishes a pulse allowance at 5-200 ms, in any colour.** Cree's application note
> CLD-AP60 REV 4A declines to publish a numeric pulsed limit at all and states that operating
> outside the published specification negates the warranty; ams-OSRAM's "surge current" is
> **10 microseconds at 0.5 % duty**; JNJ's and Xinglight's pulse footnotes are **100 us at 10 %
> duty**. This board's flashes are **50x to 2000x longer**. For a die whose thermal time constant is
> milliseconds, **a 5-200 ms pulse is thermally DC.** There is nothing to interpolate and no
> headroom to claim.

---

## 1. What the board provides - the fixed side of the interface

Not negotiable; stated so the module designer can design against it.

| | value |
|---|---|
| Drive topology | **Four independent linear constant-current sinks**, one per colour, each referenced to board GND. The **anode is common** (`/VBANK`) |
| Regulated current, per colour | **2.6 A**, commanded 0-100 % by a filtered DC setpoint. Regulation is closed-loop against a 200 mohm 1 % shunt |
| Bank voltage at the anode | **39.7 V (floor) to 48.0 V (armed ceiling)**, normally capped at **44.5 V** |
| Compliance headroom the sink needs | **1.7 V** above the string voltage, at 2.6 A, hot |
| Flash duration | **8.68 ms** at full current (headline); 50/100/150/200 ms long modes at 0.74/0.48/0.39/0.35 A |
| Flash rate | 1-25 Hz |
| Simultaneous colours | **Any combination, up to all four at 2.6 A each** (10.4 A total, 2.17 ms of bank window) |
| Sustained LED power, all colours together | **6.606 W** - fixed by the 802.3af budget, not by the module |
| Peak electrical, one colour | **98.8 W** for 8.68 ms |
| Peak electrical, four colours | **395 W** for 2.17 ms |
| Protection the board provides | Per-colour LED-short (Vds) trip in <20 us; module over-temperature trip; bank UVLO; ENABLE gating. **All firmware-independent** |
| Protection the board does NOT provide | Reverse polarity, ESD at the module, open-string detection in hardware (it is a firmware self-test) |

---

## 2. Acceptance criteria

### 2.1 Group A - strings and emitters

| ID | Criterion |
|---|---|
| **LE-01** | The module shall present **four electrically independent strings**, one each for **white, red, green and blue**, joined **only** at the common anode. No colour's cathode shall connect to any other colour's cathode or to the anode by any path, including a shared thermal pad. |
| **LE-02** | Each string shall be a **single series string with no parallel sub-strings**, unless LE-03 is satisfied. Rationale: a parallel path needs Vf-matched binning or ballast, and an unbinned pair mismatched by ~1.3 V needs ~5 ohm of ballast per string to hold the split inside +/-10 %, which is **8.45 W of peak ballast loss and 6.5 V of string voltage** - that destroys the LE-05 window. |
| **LE-03** | *Exception to LE-02.* If a colour has no die DC-rated to 2.6 A, parallel sub-strings are permitted **only** with (a) **single-Vf-bin ordering** for that colour, (b) a per-string ballast resistor sized to hold the current split inside **+/-10 %** at 2.6 A total, and (c) the ballast's voltage drop **counted inside** the LE-05 string-voltage window, not on top of it. Ballast dissipation shall be recorded and shall not exceed 2 W per string at peak. |
| **LE-04** | Every emitter shall be **DC-rated at or above the per-die current it will carry**, at the solder-point temperature of LE-15, taken from the manufacturer's **DC forward-current** specification. **Zero pulsed headroom shall be claimed - in red, green and blue exactly as in white.** A part whose datasheet gives only a pulse rating at 100 us / 10 % duty does **not** satisfy this criterion; see LE-26, which requires the absence of a 5-200 ms curve to be recorded rather than assumed away. |
| **LE-05** | Every string shall present **38.0 V +/- 1.0 V at its rated peak current, at 85 C solder point.** String length is the trim variable. *This is the single most load-bearing criterion in this document*: the bank window is shared, so the board's UVLO floor is `max(V_string) + 1.7 V` over all four colours - one long string steals window from every colour - and a **short** string burns the difference in its own pass FET, where a 35 V string alone at full rate puts **1.33 W** against a **1.35 W** allowance. |
| **LE-06** | Per-colour **forward voltage at the rated peak current, hot**, shall be taken from the emitter datasheet or measured, and **recorded in the module's data sheet**. The board's design uses estimates (`power_tree.md` s9.1: R ~2.5 V, G ~3.8 V, B ~3.5 V, W ~3.6 V per die at 2.6 A hot) and those estimates are **not** verified - `research/led-emitter` surveyed the white catalogue only, because D-04 was still open. |
| **LE-07** | Per-colour **luminous flux and luminous efficacy at the rated peak current, hot**, shall be recorded. The board's design uses estimates of **~100 lm/W white, ~70 green, ~50 red, ~35 blue**. If a measured figure differs by more than 20 %, `power_tree.md` s9 must be re-issued - **nothing on the board changes**, but the fixture's advertised output does. |
| **LE-08** | **No capacitance shall be fitted across any string, and none across the anode-to-cathode pair at the module end.** Any output capacitance recreates the decay tail STR-REQ-01 forbids. This includes "for EMC" bypass capacitors. |

### 2.2 Group B - the board-to-module interface

| ID | Criterion |
|---|---|
| **LE-09** | The module shall present exactly **two looms**: a **six-conductor power loom** to `J200` and a **four-conductor sensor loom** to `J300`. No other electrical connection to the module is permitted, and **no connector may leave the enclosure** (ICD s9). |
| **LE-10** | The four string anodes shall be **joined on the MCPCB**, and the joint shall be brought out on **two** conductors (LE-12 positions 1 and 2). The joint must be sized for **10.4 A** - all four colours can fire simultaneously at 2.6 A. |
| **LE-11** | Both looms shall terminate in **polarised, latching** housings mating with the board-side connectors of LE-12 and LE-14. A 180-degree or one-position mis-insertion shall be **mechanically impossible**, not merely marked. |
| **LE-12** | **`J200` power connector pinout - JST VH series, 3.96 mm, 6 positions, 10 A / 250 V per contact.** Position 1 is silkscreen-marked on the board. <br><br>`1` = `/VBANK` anode (**red**, 18 AWG) &nbsp;&nbsp; `2` = `/VBANK` anode (**red**, 18 AWG) <br>`3` = `LED_K_W` white cathode (**white**, 20 AWG) &nbsp;&nbsp; `4` = `LED_K_R` red cathode (**brown**, 20 AWG) <br>`5` = `LED_K_G` green cathode (**green**, 20 AWG) &nbsp;&nbsp; `6` = `LED_K_B` blue cathode (**blue**, 20 AWG) <br><br>The two anode contacts are adjacent so they may be joined at the housing. |
| **LE-13** | **Loom conductors: anodes 2 x 18 AWG minimum, cathodes 4 x 20 AWG minimum, total loom length <= 0.30 m.** Each cathode shall be run **alongside an anode conductor as a tight pair** to minimise the `L di/dt` loop; the board clamps 13-52 V of harness inductive kick with a drain-source TVS per colour, and the clamp is sized for **0.5-2 uH** of loom inductance. A longer or looser loom invalidates that sizing. **Total loom resistance shall not exceed 15 mohm per colour path** (anode + cathode). |
| **LE-14** | **`J300` sensor connector pinout - 4 positions, 2.5 mm pitch or finer.** <br><br>`1` = `NTC_TRIP+` &nbsp; `2` = `NTC_TRIP-` (board GND) &nbsp; `3` = `NTC_TEL+` &nbsp; `4` = `NTC_TEL-` (board GND) <br><br>**Two separate 10 kohm NTC thermistors**, B25/85 = 3380 K nominal, are required - not one thermistor shared between the two circuits. Rationale: the trip circuit is on `+12V` and the telemetry circuit is on `+3V3`; two thermistors cost ~$0.08 and mean **a shorted telemetry wire cannot defeat the over-temperature trip.** `NTC_TRIP` sits in the **top** leg of the board's divider, so **an open harness wire trips the fault** - a broken sensor wire is fail-safe by construction. |

### 2.3 Group C - thermal

| ID | Criterion |
|---|---|
| **LE-15** | **Emitter solder-point temperature shall not exceed 85 C in any operating case**, including continuous flashing at the sustained budget. 85 C rather than the datasheet maximum because AlInGaP (red) loses flux steeply with temperature and because LE-04's DC rating is itself a function of solder point. |
| **LE-16** | **THE WALL-CONDUCTION PATH. The heatsink shall be bolted to or through the enclosure wall so that the wall is the radiator, and the LED's 6.606 W shall leave the fixture through that wall WITHOUT entering the enclosure's internal air.** This is the single load-bearing criterion in this document and it is now a closed enclosure decision, not a preference (s0.1). It is met by an **apportioned Rth budget**, every line of which is separately measurable: <br><br>`solder point -> MCPCB back face` **<= 0.5 C/W** <br>`MCPCB -> heatsink interface` (LE-19) **<= 1.0 C/W** <br>`heatsink base spreading` **<= 0.5 C/W** <br>**`heatsink -> enclosure wall joint`** **<= 0.5 C/W** <br>`wall + external surface -> outside air` **<= 3.5 C/W** <br>**TOTAL `solder point -> outside air`** **<= 6.0 C/W** <br><br>At the 6.606 W sustained total against outside air at <= 35 C that is a solder point of **~74.6 C**, and LE-15 passes with 10 K to spare. <br><br>**The wall joint shall achieve its 0.5 C/W by construction, checkably:** contact area **>= 1,000 mm2** (e.g. 32 x 32 mm); thermal interface material **>= 3 W/mK and <= 0.5 mm compressed**; **>= 4 fasteners of M3 or larger** with **no unsupported span greater than 40 mm** across the joint; **spring or Belleville washers** so the clamp force cannot relax over thermal cycles. A joint held by adhesive alone does not satisfy this criterion. <br><br>**What happens if this path is not achieved is the whole point of the criterion:** all 6.606 W then enters the sealed box on top of the board's own 1.894 W, and `power_tree.md` s10.7 shows that this is precisely the difference between the board seeing **~32-48 C** internal air and seeing **56-77 C** - i.e. between a comfortable design and the 85-90 C case in which two of the board's five power packages fail on average power. **A free-standing heatsink inside the box is not a degraded version of this design. It is a different, failing one.** |
| **LE-17** | **Junction rise during a flash shall be recorded and shall keep Tj below the emitter's rated maximum.** Worked example for guidance: a colour's 98.8 W peak across an 11-die string is 9.0 W per die; at `Rth(j-sp)` = 2.4 C/W that is a **21.6 C junction rise for the duration of the flash**, on top of LE-15's 85 C solder point - i.e. Tj ~107 C peak. That is comfortable for InGaN (Tj max 150 C) and acceptable for AlInGaP (125 C), **but it must be computed for the parts actually chosen** - a shorter string means more watts per die and the rise scales linearly. |
| **LE-18** | Both thermistors shall be mounted **on the MCPCB within 10 mm of the hottest emitter's solder point**, with the same thermal path to the substrate as an emitter. A thermistor on the heatsink instead of the MCPCB reads 10-20 C low and defeats the trip. |
| **LE-19** | The MCPCB-to-heatsink interface shall use a **thermal interface material of <= 1.0 C/W for the joint area**, and the joint shall be mechanically clamped (screws, not adhesive alone) so the interface cannot degrade over thermal cycles. The interface resistance counts inside LE-16's 6.0 C/W budget. |

### 2.4 Group D - optical

| ID | Criterion |
|---|---|
| **LE-20** | **No narrow TIR optic.** The room is 5 x 7 m with a 2.5 m ceiling and the fixture sits ~2.3 m above the floor; a bare 120-degree FWHM emitter already gives a **4.0 m half-intensity radius**, i.e. an ~8 m pool, wider than the room's short dimension. Every off-the-shelf TIR lens for this package class narrows that to 10-45 degrees = a 0.4-1.9 m spot, which is exactly the failure STR-REQ-16 warns about. **Use a flat diffuser or a clear window in the enclosure.** If more punch is ever wanted the correct class is a **60-90 degree wide/frosted TIR** from Carclo or Ledil through Mouser - **JLC stocks zero optics of any kind.** |
| **LE-21** | **The four colours shall be co-located so that no colour's optical centroid is more than 15 mm from the array centroid**, and a **diffuser shall be fitted**, so that STR-REQ-14's colour-mixing requirement is met optically rather than by distance. An RGBW array that shows four separate coloured shadows at 2.3 m fails this criterion regardless of what the flux numbers say. |
| **LE-22** | Per-colour flux shall be **verified on a bench once**, at 2.6 A and at 10 % of 2.6 A, and the results recorded as **four firmware amplitude scale factors**. The board does **not** measure per-colour current at runtime (`blocks.md` s4.5); colour mixing is a calibrated open-loop quantity and this is where the calibration comes from. |

### 2.5 Group E - safety and marking

| ID | Criterion |
|---|---|
| **LE-23** | **The MCPCB, its heatsink and every conductor of both looms float at PoE potential.** They shall be **electrically isolated from earth, from any earthed chassis, and from anything a user can touch** (ICD s9, H1-Q5). Bonding the heatsink to an earthed enclosure part breaks PD signature detection outright, because detection currents are only a few hundred microamps. **Do not earth the heatsink "for safety" - it is the unsafe option here.** |
| **LE-24** | The module shall be marked **`FLOATING AT PoE POTENTIAL - DO NOT EARTH`** and **`HOT SURFACE`**, and its data sheet shall record: the four measured string voltages (LE-05/06), the four measured fluxes (LE-07/22), the emitter MPNs, **distributors** and bins, the string topologies, the ballast values if LE-03 was invoked, and the measured `Rth(solder point -> outside air)` **broken down against LE-16's five budget lines**. **That data sheet is an input to DOC-01.** |

### 2.6 Group F - sourcing  **[added at the H1 follow-up]**

| ID | Criterion |
|---|---|
| **LE-25** | **Published thermal data beats optical convenience whenever a part is sole-source.** Any emitter selected for this module shall publish **both `Rth(junction -> solder point)` and `Tj max`**. A part that publishes neither shall not be selected **if it is also sole-source**, regardless of how convenient its optical arrangement is. <br><br>*This is the owner's demonstrated preference, applied as a rule.* The par run swept **318 RGBW emitter parts** across the LCSC catalogue and found that the only in-stock 4-in-1 RGBW above 50 mA is sole-source **and publishes neither figure**; the owner **rejected it on exactly those grounds**, choosing RGB 3-in-1 plus a separate white emitter instead - accepting white/colour fringing risk to get published thermal data and 3.5x the stock depth. **LE-15, LE-16 and LE-17 cannot be evaluated at all for a part with no `Rth(j-sp)` and no `Tj max`**, so the rule is not a preference so much as a precondition for this document being checkable. |
| **LE-26** | **Zero pulsed headroom applies to colour exactly as it does to white, and the absence of a published curve shall be RECORDED as absence rather than treated as permission.** For each of the four colours, the module data sheet shall state either (a) the vendor's pulsed derating curve covering **5-200 ms**, or (b) the explicit statement that **no such curve is published**, together with the DC rating used instead under LE-04. <br><br>**The expected answer for all four colours is (b).** This run's P1 established that no *white* LED vendor publishes a pulse allowance in this range - Cree's CLD-AP60 REV 4A declines to publish one at all, ams-OSRAM's surge current is 10 us at 0.5 % duty, JNJ's and Xinglight's footnotes are 100 us at 10 % duty - and **nothing about a red, green or blue die changes that**; the market's pulse ratings are written for camera-flash timescales two to four orders of magnitude shorter than this board's. **Recording it as (b) is the correct outcome and is not a gap in this specification.** |

---

## 3. Design guidance the criteria do not mandate

Not acceptance criteria - the module designer may solve these any way that satisfies s2.

### 3.1 Indicative string topologies

From `power_tree.md` s9.1's typical values, at 2.6 A hot, to hit LE-05's 38.0 V +/- 1.0 V:

| colour | chemistry | typical Vf/die at 2.6 A hot | **indicative series count** | string V |
|---|---|---|---|---|
| white | InGaN + phosphor | ~3.6 V | **11S** (or **3S** of a 12 V-configuration multi-die emitter at ~12.7 V) | 39.6 V / 38.0 V |
| red | **AlInGaP** | **~2.5 V** | **15S** | 37.5 V |
| green | InGaN | ~3.8 V | **10S** | 38.0 V |
| blue | InGaN | ~3.5 V | **11S** | 38.5 V |

**Red is the awkward one** - low Vf means the longest string and the most dies, and AlInGaP is the
chemistry most sensitive to LE-15's solder-point limit. **Expect red to size the MCPCB.**

### 3.2 Candidate emitter families, and the topology the owner has already chosen once

**None of these has been priced or datasheet-verified for this application** - `research/led-emitter`
surveyed the *white* catalogue only, on JLCPCB, while D-04 was still open. They are starting points
for the module designer's own search, and **LE-04/05/06/25/26 are what actually decides**.
**Name the distributor with every part** (s0.1, LE-24) - LCSC stock levels are not this module's
constraint.

**The credible starting topology: RGB 3-in-1 plus a SEPARATE white emitter.** This is what the
owner selected for the par on essentially this evidence, and it satisfies LE-25 where a 4-in-1 does
not:

| | RGBW 4-in-1 | **RGB 3-in-1 + separate white** |
|---|---|---|
| Optical mixing (LE-21) | best - one optical centre | **good, but a white/colour fringe is possible at the diffuser** |
| Published `Rth(j-sp)` and `Tj max` | **the only in-stock part above 50 mA publishes NEITHER** | available across several families |
| Sourcing | **sole-source** | multi-source, and the par measured **3.5x the stock depth** |
| **LE-25 verdict** | **fails when sole-source** | **passes** |

**The owner has already made this trade once, knowingly**: accept fringing risk, get published
thermal data and stock depth. Nothing here overrules it - but note the difference in leverage:
**this module is not bound to LCSC**, so a 4-in-1 with published thermal data from another
distributor would also satisfy LE-25. The rule is about *data and sourcing*, not about package
count.

- **Multi-die, high-current colour emitters** (the topology LE-02 wants): Luminus SST-90 / SBM-160
  class, Osram OSLON Boost HX class - Digi-Key and Mouser. These reach 2.6 A DC in colours, which is
  the property that makes a single series string possible.
- **Single-die 1-2 A colour emitters** (Cree XP-E2 / XQ-E colour, Osram OSLON SSL): cheaper and far
  more available, but at 2.6 A they force LE-03's parallel-plus-ballast route. **The par found every
  Cree XLamp colour line at zero stock at LCSC; check Digi-Key and Mouser, where they are ordinarily
  stocked, before treating that as a constraint.**
- **White**: `research/led-emitter` verified two 1500 mA-class parts live at JLC (Cree XP-G2
  `XPGBWT-L1-0000-00H51`, LCSC C17401863, and JNJ `JNJ-LTJW0115T140`, LCSC C19185883); at 2.6 A both
  need LE-03. The Cree XHP70-class 12 V-configuration emitter - **Digi-Key or Mouser, not LCSC** -
  is the part that makes white a 3S single string.
- **What does not exist**: a bought RGBW COB at this power level, and any white COB at JLC above
  13.5 W (the entire in-stock population is three SKUs totalling 17 pieces).

### 3.3 The dimming behaviour the module will show

**Pulsing costs about 30 % of the lumens the same average watts would give run continuously**
(efficacy droop). That is a lever, not a defect: STR-REQ-07's graceful degradation works by
**stretching the pulse**, which recovers efficacy *and* avoids a missed beat. Expect measured flux
at 2.6 A to be below the datasheet's `lm/W` at 350 mA by 20-35 % in every colour, and worse in
green (the "green gap") and in red at temperature.

---

## 4. Verification matrix

| Criterion | How it is checked | When |
|---|---|---|
| LE-01, LE-02, LE-03 | Continuity and topology inspection against the MCPCB netlist | module build |
| LE-04, LE-06, LE-07 | Datasheet review + bench measurement at 2.6 A | before first mate |
| **LE-05** | **Measure each string's voltage at 2.6 A at 85 C solder point. This must pass BEFORE the module is mated to a live board** - a string outside the window either steals the bank window from the other three or overheats its pass FET | **gating** |
| LE-08 | Capacitance meter across each string, < 100 pF | module build |
| LE-09 .. LE-14 | Loom continuity, gauge, length and resistance measurement; mis-insertion attempt | module build |
| LE-15, LE-17 | Thermocouple at the solder point, continuous flashing at the sustained budget for >= 30 min (the D2PAK/pour time constant is 60-120 s, the heatsink's is longer) | fixture integration |
| **LE-16** | **Two thermocouples, not one: solder point AND enclosure internal air, logged together over the same >= 30 min run, with the room temperature recorded.** The pass condition is *both* `solder point <= 85 C` **and** `internal air rise <= ~8 K above room` - the second is what proves the LED heat actually left through the wall rather than into the box (`power_tree.md` s10.7). A solder point that passes while the internal air climbs 30 K means the wall joint is not working and the board is in the 85-90 C case | **gating** |
| LE-18, LE-19 | Physical inspection + the LE-16 measurement; confirm fastener count, span and washer type | fixture integration |
| LE-25 | Datasheet review: `Rth(j-sp)` and `Tj max` present for every emitter; second source identified or the part rejected | before purchase |
| LE-26 | Datasheet review; record the curve or record its absence, per colour | before purchase |
| LE-20, LE-21 | Beam photo at 2.3 m; check for separated colour shadows | fixture integration |
| LE-22 | Photometer at 2.6 A and 0.26 A per colour; record four scale factors | fixture integration |
| LE-23 | Insulation test module-to-earth; confirm PD detection still passes with the module mated | **gating** |
| LE-24 | Document review | before shipment |

---

## 5. Cost estimate, per fixture

Indicative only - none of it is a JLCPCB line and `order_quote` at P10 will not see any of it.

| item | estimate | note |
|---|---|---|
| Emitters, 4 colours, ~45-55 dies total | **$60-110** | The dominant line, and the widest uncertainty. Colour dies at 1-2 A are ~$1-2 each; high-current multi-die colour emitters are $4-8 each and need fewer |
| Aluminium MCPCB, ~60 x 60 mm | $8-12 | JLCPCB does aluminium PCB as a separate cheap order |
| Heatsink, <= 6.0 C/W with the enclosure wall as radiator | $8-15 | LE-16 |
| Diffuser / window | $3-5 | LE-20 |
| 2 x NTC, both looms, connectors, ferrules | $5 | LE-14, LE-13 |
| Thermal interface + mounting hardware | $3 | LE-19 |
| **Total per fixture** | **~$95-165** | against **~$46-65** for the white-only baseline |

**The light engine is ~5x the cost of the board that drives it** (`blocks.md` s7: ~$29.25/board),
and RGBW roughly doubles it. That ratio was visible at H1 and was accepted.

---

## 6. Open items the module designer must close

| # | Item | Owner |
|---|---|---|
| **LE-OPEN-1** | **Per-colour emitter selection.** No colour emitter has been priced or datasheet-checked - the P1 survey covered white only, because D-04 was open. LE-04/05/06/25/26 are the acceptance gates; s3.2 is a starting list, not a shortlist. **Search Digi-Key and Mouser, not only LCSC** (s0.1) | module designer |
| **LE-OPEN-2** | **Whether any colour can meet LE-02 (single string) at 2.6 A.** If not, LE-03's binning-plus-ballast route applies and the string voltage budget tightens | module designer |
| **LE-OPEN-3** | ~~The enclosure~~ **CLOSED: sealed, non-metallic, NOT vented, heatsink bolted to or through the wall**, shared with the par fixture. **What remains open is not the decision but the execution** - LE-16's wall joint (>= 1,000 mm2, >= 3 W/mK, >= 4 fasteners, no span > 40 mm) and LE-23's requirement that the wall mount must **not** make the heatsink touchable, per H1-Q5. Those two pull against each other at the wall and are the fixture owner's to resolve | fixture owner |
| **LE-OPEN-4** | **Whether the fixture's advertised output should be quoted per colour or mixed.** `power_tree.md` s9.3 shows mixed-colour operation is ~36 % dimmer than the white channel alone, and RGB-only white is 42 % of W-channel white. **Quote the white channel and quote the colours separately; do not quote a single number** | fixture owner |
