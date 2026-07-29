# lumina-par (LUM-PAR-A) - stackup, outline, clearance regime, thermal architecture

---

## 1. Chosen stackup

**`JLC04161H-3313`** - JLCPCB standard 4-layer, 1.6 mm, 1 oz outer / 0.5 oz
inner, HASL. **Board class: 4L.**

```
  F.Cu     0.035 mm  1 oz    components + signal + power routing
  prepreg  0.2104 mm  FR4 7628, er 4.05
  In1.Cu   0.0175 mm 0.5 oz  SOLID GND - the reference plane
  core     1.065 mm   FR4, er 4.6
  In2.Cu   0.0175 mm 0.5 oz  +12V pour (branch A) / +48V + GND islands (branch B)
  prepreg  0.2104 mm  FR4 7628, er 4.05
  B.Cu     0.035 mm  1 oz    J3 / J4 reverse-mounted sockets + fanout + short routing
```

### Why 4 layers

Layer count is driven by **plane needs and density, not by impedance**.

1. **Switch-node containment toward the carrier's 2.4 GHz antenna.** Four buck
   converters run at ~700 kHz with nanosecond switch-node edges, **11 mm above an
   ESP32-S3 PCB antenna that H1-Q8 made a supported control path**, with RF review
   in scope at layout sign-off. In1 as a solid GND **0.2104 mm** below F.Cu gives
   every switch node an unbroken return **7.3x closer** than a 2-layer board's
   1.53 mm core would - a ~7x reduction in radiating loop area for the one
   structure on this board that actually radiates. This is the strongest single
   driver.
2. **A continuous GND reference under the PWM and gate lines.** spec-dimming s7.3:
   trace-length matching between PWM0-3 is *not* required, but **edge jitter is** -
   at a 141 ns pulse, 1.4 ns of jitter is a 1 % flux error, and PAR-REQ-06 is a
   1 %-class requirement. That means short, continuously ground-referenced traces
   with no split or void underneath. On 2 layers the reference plane and the
   routing compete for the same copper.
3. **B.Cu is already spoken for.** J3 and J4 are **reverse-mounted THT sockets on
   the bottom side** (ICD s7.3) - 38 through-hole pads plus their fanout. A
   2-layer board would have to make F.Cu simultaneously the only signal layer and
   the only pour.
4. **Density.** After the four ICD s7.6 exclusion zones and the notch, roughly
   **45 cm2** of the 80 cm2 board is usable (s4.3). It has to hold four
   independent switching channels (~9 parts each), the gating logic, a quad
   comparator with its ladder, the EEPROM/ID block, three connectors and ~20
   decouplers: **~110-130 placements**. That is routable on 2 layers only by
   carving up the pour.
5. **Not impedance.** **No controlled-impedance net exists on this board.** PWM is
   4.9-9.8 kHz, I2C is 400 kHz, DSPI is unused, the ADC paths are DC. The
   `JLC04161H-3313` `controlled_impedance` table (se_50 / diff_90 / diff_100) is
   **not used**, and `constraints.json` declares no `impedance_ohm` anywhere.
   This stack is simply JLC's standard 4-layer 1.6 mm offering.

Cost of the fourth and fifth copper layers at qty 8-10 of 100 x 80 mm is roughly
**+$1-3/board** against a $25-35 target (s7). It is not a real trade.

**Copper weight: 1 oz outer, as supplied. Do not specify 2 oz.** D-T6/L-8: 2 oz
buys ~25 % only when the board must spread heat laterally to its own surface, and
essentially nothing (9.39 vs 9.61 degC/W measured) when the path is a via farm
into a heatsink. This board dissipates **0.8 W over 80 cm2** and is neither of
those cases.

### 1.1 Layer assignment and the antenna void

| Layer | Content |
|---|---|
| **F.Cu** | all active components; driver switch nodes; PWM/gate routing; `+12V` distribution |
| **In1.Cu** | **solid GND**, poured over `[0, 0, 88, 80]` only |
| **In2.Cu** | **`+12V`** pour, `[0, 0, 88, 80]` only; local GND islands under the analogue block |
| **B.Cu** | J3/J4 socket pads and fanout, J5, short escapes, GND stitching |

**The antenna column (88, 25)-(100, 55) forbids copper on EVERY layer and any
metal component** (ICD s7.6; live, because H1-Q8 closed Wi-Fi as functional).

`planes_gen` supports a `region` (where to pour) but has **no void or keepout
support** - verified by reading the script. Therefore:

- `constraints.json` declares both inner planes with `region: [0, 0, 88, 80]`,
  which removes inner copper from the whole `x >= 88` strip by construction. This
  over-voids by 12 x 50 mm of otherwise-usable plane; that strip is a board-edge
  sliver with nothing on it, so the cost is zero.
- **F.Cu and B.Cu are not covered by any tool.** A KiCad **rule area (keepout
  zone) covering (88, 25)-(100, 55) on all four layers must be added by hand at
  P5**, immediately after the outline work, and **verified geometrically at P8** -
  no ai-ee check enforces "no copper here". Record it on the P5 checklist; it is
  the kind of requirement that silently disappears.
- No metal component and no mounting hardware may enter the column either (L-9).
  This includes any bracket for the LED module.

---

## 2. Board outline

| Item | Value | Source |
|---|---|---|
| Outline | **100.0 x 80.0 mm** | ICD s7.1 common footprint |
| Corner radius | **3.0 mm**, all four corners | ICD s7.1 / MECH-01 |
| Thickness | 1.6 mm | ICD s7.1 |
| Mounting holes | **4x M3 (3.2 mm) at 5 mm inset** (a 90 x 70 mm rectangle) **+ a 5th M3 at (46, 74)** | ICD s7.1 / s7.5 |
| Notch | **30 x 26 mm in the TOP edge, region (6, 0) - (36, 26)** | ICD s7.6 / H1-Q4 |
| Origin for every coordinate in this package | board **top-left**, x right, y down | ICD s7.1 |

The outline is **confirmed as-is** (requirements Q12). The carrier and daughters
share one enclosure and mate through the connector, so the outlines are not
independent; ai-ee has no outline-shrink step, and `--outline WxH` at
`board_init` binds permanently.

### 2.1 P5 recipe, and the three traps

```
board_init.py --outline 100x80 --corner-radius 3 --mounting-holes 4 --margin 10
```

**`--margin 10` is mandatory, not a default.** `board_init.py` places mounting
holes at **inset = margin / 2** (confirmed in the script, line 289), so the ICD's
5 mm inset requires margin 10. The default 6 would give a 3 mm inset and miss the
ICD footprint. MECH-01 additionally clamps the corner radius to that inset, so
margin 10 allows R up to 5 and honours the requested 3.0. **Read the board_init
report's `corner_radius` field and `worker_notes`; do not assume the requested
value was applied.**

**TRAP 1 - the notch has NO pipeline support and must be a hand edit.** Verified
in this repo, not assumed:

- `board_init.py --outline` accepts only `auto` or `WxH` (script line 239-282).
- `kc.py` subcommands are `erc drc gerbers drill pos step render sch-pdf netlist`
  - **there is no outline editor**.
- `place_edit.py` operations are exactly `place / move / rotate / flip / lock /
  add_text / move_text` (script lines 49-56) - **no outline op**.

So the mandatory 30 x 26 mm relief must be produced by a **direct Edge.Cuts edit
of the `.kicad_pcb` after `board_init` and before P6**, and **every downstream
consumer must then be re-verified against the modified outline**: `place_seed`,
`place_anneal`, `place_metrics`, `planes_gen` (which intersects pours with the
outline), `stitch_vias`, `dfm_check`, `fab_export`, and `kc drc`. Note that with
`--corner-radius` the outline is emitted as lines plus arcs, not a single
`gr_rect`, so the edit must splice into that geometry consistently. **This is a
P5 implementation risk, not a requirements question - the notch itself is
non-negotiable** (it is the primary anti-180-degree mechanical interlock,
CAR-REQ-16: rotated, the daughter presents solid board over a ~15 mm magjack on
an 11.0 mm stack and cannot be forced flat).

**TRAP 2 - `board_init` does not put the outline at the origin.** The existing
`pd-trigger` board's Edge.Cuts rect runs `(9.799999, 27.509999)` to
`(57.799999, 57.509999)` - i.e. the outline sits at an arbitrary offset in PCB
coordinates. **Every rectangle in `constraints.json` and every ICD s7.2 connector
coordinate in this package is in ICD board-local coordinates (top-left origin).**
Before P6 consumes them, read `outline_bbox` from the `board_init` report and
**translate all keepout rects and plane regions by (x0, y0)**, or the keepouts
land somewhere else entirely and the antenna column is not protected. Do this as
an explicit, recorded P5 step.

**TRAP 3 - H5 is not a `board_init` hole.** `--mounting-holes` generates corner
holes only (0..4). **H5 at (46, 74)** is added at P4 as a
`MountingHole_3.2mm_M3` symbol so it carries a refdes, is listed in
`placement.fixed`, and is positioned with an explicit `place_edit` op at P6. It is
mechanically required (ICD s7.5: the two connectors span 74 mm of the bottom edge
with their inner ends 34 and 44 mm from the nearest corner standoff) and it is the
fourth anti-rotation mechanism (rotated, it maps to (54, 6) and cannot take a
standoff - a visible, pre-power tell).

### 2.2 Connector positions - provisional, and this board is blocked on them

ICD s7.2 gives J3 body (14, 68)-(34, 78) with position 1 at (15.3, 69.3), H5 at
(46, 74), J4 body (56, 68)-(88, 78) with position 1 at (57.3, 69.3). **ICD s7.2
is the one section not frozen at H1**: the carrier owner must compare placed
positions after its own P6, correct them, and re-issue. Daughters are explicitly
blocked on that re-issue.

Consequences carried into this package:

- `constraints.json` declares J3/J4 as `placement.edges` on the **bottom** edge at
  `pos` 0.24 and 0.72, which is a hint to the annealer, **not** the final
  position. At P6 both connectors must be placed with explicit `place_edit` ops at
  the re-issued mm coordinates and then **locked**.
- P1-P4 do not depend on mm coordinates, so this run proceeds and **holds at P5**
  (requirements Q16 option b). Re-check against the re-issued ICD before
  `board_init` runs.
- Mating geometry to verify at P4/P6, not to re-derive: these sockets are
  **bottom-side, facing down**, and mate with a top-side carrier header. Plan-view
  (x, y) is shared between the boards, but **pin numbering mirrors across the row
  on a bottom-side footprint** - check pin 1 alignment in the mated view, never
  from the footprint alone.

### 2.3 Usable area after the exclusion zones

| Zone | Region (ICD coords) | Rule |
|---|---|---|
| RJ45 relief / **the notch** | (6, 0) - (36, 26) | cut away entirely - 780 mm2 removed from the board |
| DC-DC hot zone | (2, 46) - (36, 68) | **no LED drivers, no aluminium electrolytics** - 748 mm2 barred to the drivers |
| Antenna column | (88, 25) - (100, 55) | no copper on any layer, no metal component - 360 mm2 |
| Recovery header | (76, 0) - (98, 20) | keep clear for a 6-way jumper lead - 440 mm2 |
| Connector band | y 68-78, x 14-88 | J3, H5, J4 |

**Roughly 45 cm2 of the 80 cm2 board is genuinely usable for the driver stages**,
against an estimated 40-48 cm2 of need. **Placement is tight and is the main P6
risk on this board.** The mitigation is structural, not fiddly: the four buck
channels go in the **y = 0..46 band above the DC-DC hot zone**, x = 36..88,
keeping switch nodes as far from the antenna column as the board allows; the
analogue block (comparator, ladder, NTC divider) sits at x = 40..70, y = 46..66,
between the hot zone and the connector band; the logic and EEPROM go next to J4.
No aluminium electrolytics anywhere on this board - all bulk is ceramic - which
disposes of half the DC-DC-hot-zone rule by construction.

---

## 3. Clearance and DRC regime

**Board-wide 0.635 mm outer-layer copper clearance around every 48 V net**
(ICD rev A2 s5.1: the TPS2378 vendor layout figure, 0.025 in, adopted board-wide
in preference to IPC-2221B B2's 0.60 mm). Inner layers: 0.10 mm required, which is
below JLC's 0.127 mm minimum, so the fab minimum dominates and the HV requirement
is free on In1/In2.

**On branch A this rule costs this board nothing.** The only 48 V copper is the
three J3 pads (1/3/5) plus a short stub to a DNP bleed footprint and one test pad.
The ICD s5.2 land pattern already gives **0.84 mm** of pad-to-pad copper gap -
**1.32x** the requirement - so the regime is satisfied by the connector footprint
and never reaches the driver area. On branch B it extends to the whole front end
and the driver VIN bus.

Rules to set at P5, in the hand-written `.kicad_dru`:

| # | Rule | Note |
|---|---|---|
| 1 | 0.635 mm clearance, `+48V_SW` to everything, F.Cu and B.Cu | `check_creepage.py` demands only 0.60 mm, so a 0.635 mm layout passes the checker by construction; the extra 0.035 mm is enforced only by this DRU rule. **Do not skip it because P8 goes green.** |
| 2 | The 0.13 mm coated column (IPC-2221B B4) is **NOT claimable** | LPI soldermask is not a qualified conformal coating and `check_creepage.py` implements only the uncoated columns - a 0.13 mm layout fails P8 with no waiver mechanism |
| 3 | Any resistor across the 48 V domain: **0805 or larger**, or two in series | ICD s5.4. On branch A this bites only the DNP bleed footprint - specify it 0805 now so branch B needs no change |
| 4 | Capacitors on the 48 V domain: **100 V** rated | ICD s5.4. Branch B only |
| 5 | Rule area (keepout) on all four layers over (88, 25)-(100, 55) | antenna column - hand-added, s1.1 |

**No MOV-to-earth surge network.** ICD s9: an unearthed PD needs none and there is
no earth to connect one to. Do not copy one out of a PoE reference design (E-11).

---

## 4. Fab class and process

| Item | Value |
|---|---|
| Layers / size / thickness | 4L, 100.0 x 80.0 mm, 1.6 mm |
| Copper | 1 oz outer, 0.5 oz inner (stack as supplied) |
| Finish | HASL (no fine-pitch BGA; MSOP-10-EP and SOT-23-5 are the finest parts) |
| Min trace / space | JLC standard - nothing on this board needs better |
| Vias | standard through-hole; **no blind/buried, no via-in-pad, no POFV** |
| Thermal vias under the driver exposed pads | **0.30 mm drill on a 1.0 mm grid, >= 9 vias, tented on B.Cu** |
| Outline | one non-rectangular feature (the 30 x 26 mm notch) + R3.0 corners |
| Assembly | JLC PCBA top side; **J3, J4 and the LED module hand-soldered** (Q13) |

**On the via spec, deliberately *not* the Cree recommendation.** [CREE-AP37]
recommends 0.254 mm drills on a 0.635 mm grid with 2 oz plating - that is the spec
for a **5 W LED package**, and it pushes JLC into a finer drill class. The parts
that need a via array on *this* board are four **0.15-0.20 W driver ICs**, where a
9-via 0.30 mm array is already far more than sufficient (TPS92515HV RthJC(bot)
5.3 degC/W, RthJA 56.2 degC/W - at 0.2 W the junction rise is ~11 K). **Reserve the
Cree array spec for the emitter pads on the LED module's MCPCB**, where it belongs
and where the fab class is a separate purchase. Keep open vias at or below 0.30 mm
and tent them on the bottom side, or solder wicks during reflow and leaves bumps
that degrade the joint (E-2, L-5).

Assembly notes carried to P3/P9:

- **Both ICD connectors are 2.54 mm THT sockets reverse-mounted on the bottom
  side.** That is not a normal JLC PCBA process. Route: JLC PCBA for everything it
  can do, then hand-solder J3 and J4. Eight boards x two hand operations is a
  couple of hours and it removes both awkward processes from the critical path.
- **The JLC "Wave Soldering" assembly flag is GONE with the H1-Q2 package change.**
  The withdrawn 4-in-1 (`C53153006`) carried it; the selected **RGB 3-in-1
  `C22434861` is classified "SMT Assembly / difficulty High"**, so if the module
  is ever ordered assembled rather than hand-built, the RGB packages can be
  machine-placed. The white discrete `C48586656` is a plain SMD discrete. This
  was one of the three stated reasons for the H1-Q2 decision and it should be
  recorded as banked, not re-litigated.

---

## 5. Thermal architecture (a) - acceptance criteria on the ENCLOSURE

**REVISION B - rewritten at the P2 delta after H1.** H1-Q1 selected **a SEALED
enclosure with the LED module's heat conducted through the wall**. The criteria
below are written against **that specific configuration** and no other; the vented
branch and the sealed-with-module-inside branch are gone.

**These are not this board's deliverable.** They are criteria someone else must
meet **and measure**, and they are the reason the fixture works or does not. They
are written as pass/fail statements because D-T11's own conclusion is that the
right form is *"an acceptance criterion on the enclosure, not an assumed number"*.

**"Sealed" here means UNVENTED. It does not mean IP-rated**: no ingress
requirement is stated anywhere in the brief set for an indoor basement/garage
install, so no ingress test is specified and none should be invented.

| # | Criterion | Basis |
|---|---|---|
| **ENC-1** | **Internal air at the daughter shall not exceed 45 degC** with a **25 degC room** and the fixture at its full sustained output, **measured**, not calculated. Expected under the selected configuration: **36.5-38.7 degC** (`power_tree.md` s6.2), i.e. 6-8 K of margin. | D-T10: 45 degC leaves a 55 K junction budget for anything still cooled by internal air |
| **ENC-1b** | **At the requirements document's ASSUMED 40 degC room ambient, ENC-1 relaxes to internal air <= 60 degC**, and every part on this daughter shall be rated for it. Already satisfied by construction: all bulk is X7R ceramic and **no aluminium electrolytic exists anywhere on this board** (T-8). | The ICD states no room-ambient assumption at all - that omission is part of OPEN-1 |
| **ENC-2** | The enclosure shall be **sealed (unvented), with the LED module's heat conducted through the enclosure wall** to an external heatsink. **A sealed enclosure with the LED module inside does NOT close and must not be selected** (s5.1). Ventilation is no longer an accepted alternative: H1-Q1 chose the wall-conducted branch and the ENC-8 path is now load-bearing for ENC-1. | H1-Q1, D-T11 |
| **ENC-3** | The wall bridge and its external heatsink shall keep live parts **non-touchable**: no finger and no 4 mm probe reaches them. The heatsink shall be **shrouded behind a plastic guard**, shall **not share a mount with anything earthed**, and the ceiling mount shall be **non-conductive and bonded to nothing**. **This criterion is strictly harder than it was before H1-Q1**, because the selected architecture deliberately puts metal through the enclosure wall - the heatsink is now touchable by default and must be made non-touchable by the guard, not by being inside a box. | ICD s9, H1-Q5, requirements Q7(b) |
| **ENC-4** | The LED module's metal substrate shall be **thermally coupled but electrically isolated** from board GND - dielectric thermal pad, insulating shoulder washers on the screws. **Isolation is thermally free at this interface and there is no excuse to skip it**: a 0.2 mm, 3 W/mK dielectric pad over a 30 cm2 module face is `t/(kA) = 0.0002/(3 x 0.003)` = **0.022 K/W = 0.13 K at 5.67 W**. Even over a small 15 x 15 mm boss it is 0.30 K/W = 1.7 K. | D-T14. Board GND is the floating PoE return; bonding the heatsink to it makes the heatsink a conductor at up to 57 V above earth, and then one accessibility failure breaks the whole compliance argument at once |
| **ENC-5** | **The module's bare-copper thermocouple pad, adjacent to an RGB package's thermal pad, shall not exceed room ambient + 50 K at full sustained output in steady state** (i.e. **<= 75 degC in a 25 degC room**). **Measured**, per the ENC-8 test method. This is the single number that stands in for the whole emitter thermal case. | `power_tree.md` s6.3. It implies red Tj = T_pad + 0.270 x 12 = **78.2 degC**, 22 K under the 100 degC colour/lifetime target and **47 K under the emitter's PUBLISHED 125 degC Tj max** |
| **ENC-6** | The enclosure shall carry the **photosensitive-epilepsy note** in its documentation (PAR-REQ-03/04 modulate deliberately in the 1-65 Hz band and breach IEEE 1789 RP3 by ~9x). | spec-dimming s3.3 item 4 |
| **ENC-7** | PAR-REQ-14 (wide wash from 2.5 m) and PAR-REQ-15 (R/G/B/W mix before reaching a surface) are **carried as enclosure requirements**, not PCB requirements. **PAR-REQ-15 is now the live risk**: H1-Q2 replaced the integrated 4-in-1, which met it by construction, with **RGB 3-in-1 + a spatially separate white**. The buildable specification - emitter arrangement, diffuser numbers, minimum throw, and the bench test - is **s5.2 below**, and it is mandatory, not advisory. PAR-REQ-14 is still met without a secondary lens (140 deg RGB / 120 deg white from 2.5 m floods well past the fixture spacing). | H1-Q2, s5.2 |
| **ENC-8** | **NEW, and load-bearing. The conduction path from the LED module's mounting face to ROOM air shall present <= 8.0 K/W, measured.** At `P_module = 5.67 W` that is a **<= 45.4 K rise**, i.e. the module mounting face <= **room + 46 K**. Test method below. **This may not be phrased as an assumption**: if the bridge fails, 5.67 W reverts into the box, internal air becomes 57-63 degC in a 25 degC room, and the fixture silently degrades into exactly the configuration H1-Q1 rejected (`power_tree.md` s6.2, failure-mode row). | `power_tree.md` s6.3. 8.0 K/W in natural convection is ~60-70 cm2 of finned surface, i.e. a ~60 x 60 x 25 mm extrusion - inside the $2-5 heatsink budget |
| **ENC-9** | The wall penetration for the bridge shall maintain the unvented seal (gasket, O-ring or potting) and shall not create a creepage path from the module's PoE-potential metal to any exterior surface a user can touch. **No IP rating is specified and none should be invented** - see the note above. | ICD s9, H1-Q1 |
| **ENC-10** | **Module stack height.** The module assembly is now **MCPCB 1.6 + package 5.15 + diffuser stand-off >= 15 (20 nominal) + diffuser 2-3 = ~29-30 mm** above the module mounting face, plus the wall bridge and external heatsink outside it. requirements s5.5 records this as previously unknown; **this is the number**. The enclosure must accommodate it and it must clear this board entirely (the module does not mount to the daughter - T-7). | s5.2, `research/led-emitter.md` s10 |

### 5.0 ENC-5 / ENC-8 TEST METHOD - so a builder can measure pass/fail

Both criteria are measured in one run. **Nothing here needs an instrument more
exotic than a two-channel type-K thermocouple meter and a bench supply.**

1. **Configuration.** Fixture fully assembled in its intended enclosure, in its
   intended orientation, at its intended mounting height, in still air, in a room
   whose temperature is recorded. Diffuser fitted. Guard fitted.
2. **Instrumentation.** Type-K thermocouples, bonded with thermally conductive
   adhesive or aluminium tape:
   - **TC1 - the module's bare-copper thermocouple pad**, which T-6 / L-13
     already require adjacent to an emitter thermal pad. **It must be adjacent to
     an RGB package, not to a white one** - the RGB package carries 1.035 W and
     the white 0.383 W, so the white pad reads ~2.7x cooler and would pass a
     broken build.
   - **TC2 - room air**, 1.0 m horizontally from the fixture, out of the beam and
     out of the fixture's convection plume ([CREE-AP37] verification practice).
   - **TC3 - internal air at the daughter** (for ENC-1).
   - **TC4 - the external heatsink base**, at the bridge (for ENC-8).
3. **Drive.** ENABLE asserted, all four channels at 100 % duty, sustained. Record
   the `+12V` input voltage and current; `P_module = V x I x 0.91 - 0.27 W`
   (buck efficiency, less the ballast, which is on the module and counts as module
   heat - so add it back for ENC-8's denominator: `P_module = V x I x 0.91`).
   Nominal at the af design point: **5.67 W of heat, 7.83 W delivered.**
4. **Settling.** Run until `dT/dt < 1 K per 15 min` on TC1. Expect **45-90 min**:
   the module's own time constant is 30-120 s, but the enclosure and heatsink are
   tens of minutes.
5. **Record** TC1-TC4 and the room temperature.
6. **PASS, all three:**
   - **ENC-5:** `TC1 - TC2 <= 50 K`
   - **ENC-8:** `(TC4 - TC2) / P_module <= 8.0 K/W`
   - **ENC-1:** `TC3 - TC2 <= 20 K`
7. **FAIL actions.** If TC1 exceeds room + 50 K, **the wall bridge is the fault**
   - re-work the interface (pad thickness, flatness, screw torque, heatsink size)
   before changing anything electrical. **Do not compensate by lowering the drive
   current without re-running `power_tree.md` s3**; a quiet current reduction
   changes flux, changes the colour mix, and hides a mechanical defect.

### 5.1 Why the sealed-with-module-inside branch does not close, stated plainly

A sealed 120 x 100 x 60 mm non-metallic box is **3.6-4.3 degC/W** from internal air
to room air (Hoffman 4.34, Rittal 3.61 - the two bracket it). **Nothing done on
the PCB changes that number**: not copper weight, not via farms, not MCPCB, not a
bigger internal heatsink.

At 4.0 degC/W and a 45 degC internal-air target in a 25 degC room, **total box heat
must be <= 5.0 W. The carrier alone is 2.4 W (af). The emitters alone are 5.67 W.**

| Configuration | In-box heat | Internal air, 25 degC room | Verdict |
|---|---|---|---|
| **SELECTED (ENC-2): sealed, LED heat through the wall** | **3.19 W** | **36.5 - 38.7 degC** | **passes ENC-1 with 6-8 K** |
| Same, at `at` | 5.02 W | 43.1 - 46.6 degC | marginal against ENC-1 |
| **The ENC-8 failure mode: bridge does not work** | **8.86 W** | **56.9 - 63.1 degC** | **fails ENC-1 by 12-18 K** |
| REJECTED: sealed, LED module inside | 8.86 W | 56.9 - 63.1 degC | fails |
| Withdrawn at H1: vented, module inside | - | - | no longer an option |

The corollary is the useful one and it is why this board is not the obstacle:
**this daughter contributes 0.79-0.81 W to the box across its entire output
range** (`power_tree.md` s6.1). The enclosure problem is the emitter module, and
the emitter module is off this board and now off the box's air entirely.

**The `at` case is no longer thermally blocked at the emitter.** Splitting the
white onto its own package drops the hottest package's heat at `at` from 2.41 W
to **1.76 W** (at the same 255 mA/die), and the wall-conducted path removes the internal-air term
altogether. `power_tree.md` s5 and s6.5 carry the arithmetic. What still gates
`at` is OPEN-1 and ENC-8, not the emitter thermal path.

### 5.2 PAR-REQ-15 - the buildable specification

**This section exists because H1-Q2 traded away the one thing the integrated
4-in-1 gave for free.** In the 4-in-1 every colour left the same 6.2 mm slug, so
"R/G/B/W mix before reaching a surface" was true by construction. With RGB in one
package and white in another, **white is now a spatially separate source and
shadow fringing is a real failure mode**. What follows is a specification with
numbers, not a hope that "the diffuser will sort it out".

**Scope honesty, stated up front: this is a PCB pipeline and it cannot verify a
beam. Every number below is a DESIGN TARGET with a stated bench test (s5.2.5).
None of it is a verified optical result.**

#### 5.2.1 The three mechanisms, separated

| # | Mechanism | Fixed by |
|---|---|---|
| **1** | **Direct-wash colour gradient.** The white and RGB families illuminate the surface from laterally offset positions, so the mix drifts across the beam. | **Arrangement** (centroid matching), then throw distance |
| **2** | **Shadow fringing.** A shadow edge is a projected *image* of the source. Two colour families at different positions cast two displaced shadows with coloured edges. **This is the mechanism PAR-REQ-15 actually names.** | **Arrangement**, then **diffuser**. **NOT by throw distance** - see s5.2.4 |
| **3** | **Beam-angle mismatch.** Live-verified: the RGB 3-in-1 is **140 deg** and the white is **120 deg** (`power_tree.md` s1.1, cross-checked against three sibling parts). The two families have *different far-field shapes*, so the mix is angle-dependent. | **Diffuser only.** The arrangement cannot fix it and firmware cannot fix it |

Mechanism 3, quantified. Fitting `I(theta) = I0 cos^m(theta)` to each published
half-intensity angle:

```
  RGB:   cos^m(70 deg) = 0.5  ->  m = ln0.5 / ln(0.34202) = 0.646
  White: cos^m(60 deg) = 0.5  ->  m = ln0.5 / ln(0.50000) = 1.000  (Lambertian)
  Ratio white/RGB = cos^(1.000 - 0.646)(theta) = cos^0.354(theta)
```

| Off-axis angle | White relative to RGB | Where that lands from a 2.5 m ceiling |
|---|---|---|
| 0 deg | 1.000 (reference) | directly below |
| 30 deg | 0.950 (**-5.0 %**) | 1.4 m out on the floor |
| 45 deg | 0.885 (**-11.5 %**) | 2.5 m out on the floor |
| 60 deg | 0.782 (**-21.8 %**) | 4.3 m out |
| 71.6 deg | 0.665 (**-33.5 %**) | **a wall 3 m away, at 1.5 m height** - i.e. squarely in the PAR-REQ-14 wash |

**The wash gets progressively less white and more saturated toward its edges, by
a third at the wall.** An 11.5 % channel-ratio error is roughly 2-3 MacAdam
steps for a mid-CCT mix; 33.5 % is unmistakable. **This is a first-order defect that
only a strong diffuser removes**, and it is the second independent reason the
diffuser is mandatory. It is also the finding most likely to be missed, because it
comes from a single LCSC attribute rather than from any calculation.

#### 5.2.2 Emitter arrangement on the MCPCB - the primary mitigation

**Layout: a 3 x 3 grid on a 16.0 mm pitch, RGB on the four corners, white on the
four edge midpoints, centre cell VACANT.** Coordinates in mm, module-local:

```
     x=0        x=16       x=32
  y=0   [RGB]     [ W ]     [RGB]
  y=16  [ W ]   (vacant)    [ W ]
  y=32  [RGB]     [ W ]     [RGB]
```

| Property | Value | Why it matters |
|---|---|---|
| Pitch | **16.0 mm** | Set by package geometry, not chosen: the land pattern is **14.5 mm** across the lead span (live-verified `Length 14.5mm` on C22434861), leaving a 1.5 mm gap. **16 mm is the minimum feasible pitch**, so the sources are as close as the parts allow |
| **RGB centroid** | `x = (0+32+0+32)/4 = 16`, `y = (0+0+32+32)/4 = 16` -> **(16, 16)** | |
| **White centroid** | `x = (16+0+32+16)/4 = 16`, `y = (0+16+16+32)/4 = 16` -> **(16, 16)** | **They COINCIDE EXACTLY.** The fixture has **no colour dipole**: no first-order colour gradient across the beam and no first-order coloured shadow displacement |
| Nearest unlike neighbour | **16.0 mm** | the separation the diffuser must bridge (s5.2.3) |
| Nearest like neighbour | RGB-RGB 32.0 mm; W-W `sqrt(16^2+16^2)` = 22.6 mm | |
| Radius from centroid | RGB **22.6 mm**; white **16.0 mm** | drives the flux-matching tolerance below |
| Array extent | 32 x 32 mm centre-to-centre, **46.5 x 46.5 mm** including land patterns | MCPCB **~55 x 55 mm** with border and mounting |

**Why this and not the alternatives.** *Clustered* (4 RGB together, 4 white
together) gives a colour dipole of 25-35 mm - the worst possible case, ~40x the
tolerance derived below. *Interleaved in a line* (RGB-W-RGB-W-RGB-W-RGB-W) also
gives coincident centroids but is 112 mm long, needs a 180 mm diffuser, and wastes
the whole benefit of a compact source. **The checkerboard is the arrangement that
gets centroid coincidence in the smallest possible aperture**, and small aperture
is what keeps the diffuser affordable.

**Tolerance budget - and it is a number a builder can check with a ruler.** The
requirement derived in s5.2.4 is a **residual colour-centroid separation
`s_res <= 0.8 mm`**:

| Contributor | Allocation | Derivation |
|---|---|---|
| Placement error, both families | **0.30 mm** | +/-0.3 mm per package, 4 packages -> `0.3/sqrt(4)` = 0.15 mm per family, 0.30 mm combined |
| White-family flux mismatch | **0.20 mm** | one white `e` brighter shifts the white centroid by `e x 16/(4+e)` ~ `4e` mm. **`e <= 5 %` -> 0.20 mm** |
| RGB-family flux mismatch | **0.28 mm** | radius 22.6 mm, so shift ~ `5.66e` mm. **`e <= 5 %` -> 0.28 mm** |
| **Total** | **0.78 mm** | **inside the 0.8 mm requirement, with nothing to spare** |

**+/-5 % flux matching within each family is exactly what H1-Q4's same-reel
mandate delivers**, and it is the direct mechanical link between H1-Q4 and
H1-Q2's fringing risk: **if the same-reel purchase is not honoured, this
arrangement stops working.** Record it as such in the build sheet.

**The two-reel consequence, stated because it is easy to get wrong.** RGB and
white now come from two different reels, so the *white-to-colour ratio* is
uncontrolled between the reels. That is **not** a fixture-to-fixture problem:
provided all 8 fixtures' emitters come from **one transaction per part number**,
every fixture inherits the *same* ratio offset, so PAR-REQ-06 is preserved and the
offset becomes a **single global firmware constant** rather than 8 per-fixture
corrections. With the EEPROM shipping empty (AMD-02) that global constant is the
only correction available, and it is sufficient.

#### 5.2.3 Diffuser specification, with numbers

**Geometry.** Each emitter, at stand-off `d` behind the diffuser, lights a patch
of radius `R = d x tan(theta_half)`. Size on the **narrower** of the two beams -
the white at 120 deg full, `theta_half = 60 deg`:

```
  R = d x tan(60 deg) = 1.732 d
```

**Criterion: the patches of nearest-unlike neighbours (s = 16 mm) shall overlap
by >= 60 % of patch area.** For two equal discs of radius `R` at separation `s`,
overlap fraction `f(u) = [2 acos(u/2) - (u/2) sqrt(4 - u^2)] / pi` with `u = s/R`.
Solving `f = 0.60` gives `u = 0.64`, so:

```
  R >= s / 0.64 = 16 / 0.64 = 25.0 mm
  d >= 25.0 / 1.732 = 14.4 mm
```

| Parameter | **Specification** | Check |
|---|---|---|
| **Emitter-dome-apex to diffuser inner face, `d`** | **>= 15 mm; 20 mm NOMINAL** | at `d = 20`: `R = 34.6 mm`, `u = 0.462`, **overlap 71 %** |
| **Diffuser aperture** | **>= 115 mm across** (diameter, or 115 x 115 mm square) at `d = 20 mm` | outermost emitter is 22.6 mm from centre; needs `22.6 + R = 22.6 + 34.6 = 57.2 mm` half-width, or the edge emitters clip and the fixture grows a **coloured rim**. At `d = 15 mm` the minimum is 97 mm |
| **Option A - RECOMMENDED** | **Bulk / volume opal diffuser**, PMMA or PC, **haze >= 92 %**, total transmittance **55-70 % (60 % nominal)**, 2-3 mm thick | Re-Lambertianises the exit, so it kills mechanism 2 **and** mechanism 3. This is the option that is certain to work |
| **Option B - light-preserving** | **Surface light-shaping diffuser**, **>= 80 deg FWHM (>= 40 deg half-angle)** scattering, transmittance **85-90 %** | Requires `d >= 25 mm`. Convolving both families with the same 40 deg kernel reduces mechanism 3's 45 deg error from -11.5 % to roughly **-5 to -7 %** but does **not** eliminate it. **Only acceptable if it passes s5.2.5 Test B** |

**COST, stated because it is the largest hidden price of H1-Q2 and it is in no
budget.** Option A costs **30-45 % of the delivered flux**. Against
`research/led-emitter.md` s5's own baseline of ~41 lx direct average in the
5 x 7 m room, Option A gives **~25 lx** and Option B **~36 lx**. The fixture set
was already characterised there as "a dark-room instrument, not room lighting";
Option A makes it materially darker. **The diffuser is also not in the
$8-14/fixture module budget** (`s7`) - budget **$2-5/fixture** for a cut opal
panel plus its retaining frame.

#### 5.2.4 Minimum throw distance, and why it is the LESS important number

**The key insight, stated first because it is counter-intuitive: throw distance
does not fix shadow fringing.** A shadow edge is a projected *image* of the
source, so the fringe scales with the source's own colour structure and with the
occluder geometry - **not** with `1/D`. Moving the wall further away moves the
shadow further away with it. **Only making the source large and colour-uniform -
the arrangement plus the diffuser - fixes shadows.** The throw number governs
mechanism 1 only.

**The wrong criterion, shown so nobody re-derives it.** If one demands that the
two source families be angularly *unresolvable* from the wall, with a chromatic
detection threshold `alpha = 2 arcmin = 5.82e-4 rad`:

```
  D >= s / alpha = 0.016 / 5.82e-4 = 27.5 m       <- absurd
```

That is the criterion for resolving two **point** sources - which is exactly what
a shadow edge does, and exactly why the diffuser rather than the throw is the fix.

**Mechanism 2, the shadow criterion (this is where `s_res <= 0.8 mm` comes
from).** Occluder at distance `a` from the fixture, surface at `a + b`, observer
at `L` from that surface. The two coloured shadow edges are displaced by
`delta = s_res x b/a`, subtending `delta/L` at the eye. Worst realistic geometry
under a 2.5 m ceiling: `a = 1.0 m` (a standing person's head/shoulder),
`b = 1.5 m` (to the floor), `L = 2.0 m`:

```
  delta / L = s_res x (1.5 / 1.0) / 2.0 = 0.75 s_res  <=  alpha = 5.82e-4 rad
  s_res <= 7.8e-4 m = 0.78 mm   ->   SPECIFY 0.8 mm  (s5.2.2 tolerance budget)
```

Sanity check on the failure case: a clustered layout with `s_res = 30 mm` gives
`delta/L = 22.5 mrad = 77 arcmin`, **39x the threshold** - plainly visible. The
arrangement is doing real work here, not decoration.

**Mechanism 1, the throw criterion.** For a `cos^m` source at throw `D`, the
maximum fractional illuminance gradient on the surface is
`|d lnE/dr| = (m+3)/(2D)`, at 45 deg off-axis. With the RGB family's `m = 0.646`
that is `1.82/D`. A colour-mix error of **2 %** (roughly 1-2 MacAdam steps for a
typical mix) is the acceptance limit:

```
  colour error = s_res x 1.82 / D  <=  0.02
  D >= 1.82 x s_res / 0.02 = 91 x s_res
```

| `s_res` | Required minimum throw |
|---|---|
| **0.8 mm** (arrangement working) | **0.07 m** - irrelevant |
| **16 mm** (arrangement failed: a builder mirrored the checkerboard, or the flux match is out) | **1.46 m** |

**STATED MINIMUM THROW: 1.5 m from the diffuser to any illuminated surface**, and
**no occluding object closer than 0.5 m to the diffuser**. 1.5 m is chosen to
cover the arrangement-failed case, and it is comfortably inside the fixture's
actual geometry (2.5 m ceiling, walls 2-4 m away, PAR-REQ-14's 2.5 m wash).

#### 5.2.5 Bench acceptance test for PAR-REQ-15

**Test C is done first, with a ruler, before anything is lit.**

- **Test C - centroid check (build inspection).** Measure the eight package
  centres on the assembled MCPCB. **PASS: the RGB centroid and the white centroid
  coincide within 0.8 mm** (s5.2.2). A mirrored or rotated placement that breaks
  the checkerboard fails here and is caught before the module is potted.
- **Setup for A and B.** Assembled fixture with the diffuser fitted, mounted at
  2.5 m, aimed at a matt white wall or screen **2.5 m away**. All four channels at
  100 % duty on a nominal white mix.
- **Test A - shadow fringing.** Hold a 50 mm opaque disc at **0.5 m** and again at
  **1.0 m** from the diffuser. Photograph the shadow with a colour-managed camera,
  fixed white balance. **PASS: no coloured fringe distinguishable at the shadow
  edge by three observers standing 2 m from the surface, AND chroma difference
  <= 0.010 in u'v' between the penumbra and the umbra in the photograph.**
- **Test B - wash uniformity (this is the mechanism-3 test).** Sample the
  illuminated field on axis and at 45 deg off-axis. **PASS: chromaticity varies by
  <= 0.010 u'v' between the two** (~4 MacAdam steps - the practical limit for "not
  noticed on a wall"). **Option B diffusers must be tested here specifically**;
  Option A is expected to pass by construction.
- **Record** which diffuser option passed, its measured transmittance (integrating
  sphere, or an A/B lux-meter reading at fixed geometry), and the resulting
  fixture flux, and feed that back into the light budget.

**If Test A or Test B fails with Option B, fit Option A and accept the flux
loss.** Do not attempt to fix fringing by raising the drive current - the
`+12V` sustained ceiling has 4.4 % of headroom (`power_tree.md` s3.1) and there is
nowhere to go.

---

## 6. Thermal architecture (b) - what THIS board must provide

| # | Provision | Detail |
|---|---|---|
| **T-1** | **Exposed-pad via arrays under all four driver ICs** | 0.30 mm drill, 1.0 mm grid, >= 9 vias, tented on B.Cu, dropping into the In1 GND plane. Declared as `thermal` entries in `constraints.json` with `min_vias: 9` |
| **T-2** | **1 oz copper, unbroken GND pour from each driver's pad to the board edges** | L-7: TI measured a 5.5 degC penalty for a copper break perpendicular to heat flow vs 1.5 degC for a parallel one. Do **not** specify 2 oz (L-8) |
| **T-3** | **Board over-temperature sensor RT401 on the copper of the hottest driver stage** | And **outside the DC-DC hot zone (2, 46)-(36, 68)**, or it reads the carrier's converter 11 mm below rather than this board's drivers (L-10) |
| **T-4** | **Emitter sensor provision: two harness conductors** (`/NTC_LED` + a dedicated sense return) | The emitter NTC is **on the module**, within a few mm of the emitter thermal-pad copper. A sensor on the daughter measures internal air plus driver self-heating - a lagging, wrong-magnitude proxy (D-T19) |
| **T-5** | **NTC routing**: total series R at the ADC pin <= 1 kohm including any filter | Keeps the divider's 5.0 kohm Thevenin plus filter under the ICD's 10 kohm ceiling (L-11). Route the sense pair away from switch nodes |
| **T-6** | **Bare-copper thermocouple pads**: two on this board next to J5, one specified on the module beside the emitter pad | [CREE-AP37]'s verification reference point. Both carry the ICD s9 bench-hazard silkscreen (L-13, L-15) |
| **T-7** | **Mounting provision: the common 5x M3 pattern only** | The heatsink is on the module, not on this board. Any bracket that does mount here must clear the antenna column and the DC-DC hot zone (L-9) |
| **T-8** | **No aluminium electrolytics anywhere** | All bulk is ceramic. Disposes of half the DC-DC-hot-zone rule by construction, and electrolytic life halves per 10 degC in a 56-69 degC box |

**The one thing this board must NOT provide: on-board emitters.** This was already
D3's conclusion on thermal grounds; **H1-Q1 has now made it structural rather than
preferential.** The selected enclosure conducts the emitter heat **through the
wall**, and an emitter soldered to this daughter cannot reach the wall bridge at
all - there is no path from an FR4 daughter in the middle of a mezzanine stack to
the outside of the box. On top of that, s5.2's PAR-REQ-15 arrangement needs a
55 x 55 mm MCPCB with a 16 mm checkerboard and a 115 mm diffuser 20 mm in front of
it; none of that fits on a board whose usable area is already 45 cm2 and whose
emitter positions would be dictated by the connector band, the DC-DC hot zone and
the antenna column rather than by the optics.

**The consequence is that OPEN-3 escalates.** The fallback "if ICD s9 is read
strictly, put the emitters on-board" is **dead** - it was already thermally
marginal, and it is now incompatible with the enclosure architecture the human
selected. **The internal LED harness is no longer a preference; it is the only
remaining architecture**, so ICD s9's reading must be confirmed rather than
assumed, and a "no" answer now reopens the enclosure decision, not just the
module. See `decisions.md` OPEN-3.

---

## 7. Cost picture for H1

Rough part cost from the P1 research prices; `order_quote` does real numbers at
P10.

**This board, per unit at a qty-8-10 build** (LCSC qty-30 breaks where they exist,
+25 % for the parts bought in single-digit quantities):

| Block | Parts | ~$ |
|---|---|---|
| 4x TPS92515HVDGQR (C213553, $1.69 @30) | 4 | 6.76 |
| 4x 47 uH shielded inductor, 4x 60 V Schottky, 4x sense R | 12 | 0.95 |
| 4x shunt N-FET (60 V logic level) + gate R + pull-down | 12 | 0.55 |
| 74LVC00A + SN74LVC1G08 (C6052-class, C7666) | 2 | 0.15 |
| Quad open-drain comparator + reference ladder | ~10 | 0.35 |
| 24C32 EEPROM + ID leg + NTC + dividers | ~8 | 0.20 |
| 4x TVS + J5 10-way latched header | 5 | 0.35 |
| J3 + J4 CONNFLY sockets | 2 | 0.30 |
| ~30 ceramics, ~20 resistors, test pads | ~55 | 0.70 |
| **BOM subtotal** | **~110-130** | **~$10.3** |
| +25 % small-quantity uplift | | **~$12.9** |
| PCB, 4L 100x80 mm, qty 10 | | $1.5-3.0 |
| PCBA setup + placement, amortised over 8-10 | | $4-7 |
| **This board, delivered** | | **~$18-23** |

Against requirements Q14's suggested **$25-35/board excluding the LED module and
heatsink**, this is **inside target with margin**. The driver silicon is 52 % of
the BOM and is the only line worth attacking: **AL8863SP-13 is 2.7x cheaper and
viable on branch A** (it is only rejected on branch B, for margin), which would
take the BOM to ~$8. It is the documented cost-down if the target bites - at the
cost of a datasheet that contradicts itself on PWM frequency and would need a
bench-verification item.

**LED module, optics and heatsink, per fixture, budgeted separately** (not this
board's BOM). **REVISED at the P2 delta - H1-Q2 doubled the package count and
H1-Q2 + s5.2 added a diffuser that was in no previous budget.** All emitter prices
live-verified this session:

| Item | Was (pre-H1) | **Now** |
|---|---|---|
| Emitters | 4x `C53153006` @ $0.3341 = **$1.34** | 4x **`C22434861`** @ $0.3724 (qty-30 break, buy 50) = $1.49 **+** 4x **`C48586656`** @ $0.2332 (qty-50 break) = $0.93 -> **$2.42** |
| Aluminium MCPCB | ~$3-6 (small) | **~$4-7** (55 x 55 mm, 8 packages, s5.2.2) |
| Ballast, NTC, module connector | ~$0.50 | ~$0.50 (unchanged - still 8x 1.5 ohm + one NTC) |
| Heatsink | $2-5 (internal) | **$2-5** (external, through-wall, ~60 x 60 x 25 mm for ENC-8's 8.0 K/W) |
| Harness | ~$1 | ~$1 (still 10-way) |
| **Diffuser + retaining frame** | **not budgeted** | **$2-5 - NEW, mandatory (ENC-7 / s5.2.3)** |
| **Module total per fixture** | **~$8-14** | **~$12-21** |

**Par fixture total: ~$30-44, x8 = $240-352** (was ~$26-37, $210-300). Against the
$500-1000 system budget that must also cover 8-12 carriers, the strobes,
enclosures and a **PoE+** switch (D-01's upgrade path implies PoE+, materially
more expensive than the PoE switch the original budget assumed) this is **tighter
than it was, and it is a system-level flag rather than a problem with this board**
(requirements Q14). **This board itself is unchanged at ~$18-23** - the H1-Q2
decision costs money on the module, not on the daughter.
