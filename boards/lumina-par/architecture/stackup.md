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
- The **top-pick emitter carries a JLC "Wave Soldering" assembly flag** where the
  RGB 3-in-1 from the same body is "SMT Assembly / difficulty High". Since the
  emitters are on a separate MCPCB and hand-placed anyway (Q11/Q13), this does not
  bind this board - but it must not be forgotten if the module is ever ordered
  assembled.

---

## 5. Thermal architecture (a) - acceptance criteria on the ENCLOSURE

**These are not this board's deliverable.** They are criteria someone else must
meet **and measure**, and they are the reason the fixture works or does not. They
are written as pass/fail statements because D-T11's own conclusion is that the
right form is *"an acceptance criterion on the enclosure, not an assumed number"*.

| # | Criterion | Basis |
|---|---|---|
| **ENC-1** | **Internal air at the daughter shall not exceed 45 degC** with a 25 degC room and the fixture at its full sustained output, **measured**, not calculated. | D-T10: 45 degC leaves a 55 K junction budget, i.e. ~7 degC/W, i.e. genuinely buildable |
| **ENC-2** | The enclosure shall achieve ENC-1 by **either** (i) **ventilation** sized so internal air is within **15 K** of room ambient at full output, **or** (ii) **conducting the LED module's heat through the enclosure wall** to an external heatsink. **A fully sealed enclosure with the LED module inside does NOT close and must not be selected** - see s5.1. | D-T11 |
| **ENC-3** | Any heatsink, vent geometry or wall bridge shall keep live parts and the heatsink **non-touchable** (H1-Q5): no finger and no 4 mm probe reaches them. The heatsink shall be **shrouded behind a plastic guard**, shall **not share a mount with anything earthed**, and the ceiling mount shall be **non-conductive and bonded to nothing**. | ICD s9, H1-Q5, requirements Q7(b) |
| **ENC-4** | The LED module's metal substrate shall be **thermally coupled but electrically isolated** from board GND - dielectric thermal pad, insulating shoulder washers on the screws. | D-T14. Board GND is the floating PoE return; bonding the heatsink to it makes the heatsink a conductor at up to 57 V above earth, and then one accessibility failure breaks the whole compliance argument at once |
| **ENC-5** | **Junction-to-internal-air <= 38 K/W per emitter package** at 1.42 W of package heat (150 mA/die), for a red junction <= 100 degC at ENC-1's 45 degC air. Verified by thermocouple at the module's bare-copper pad during bring-up. | `power_tree.md` s6 |
| **ENC-6** | The enclosure shall carry the **photosensitive-epilepsy note** in its documentation (PAR-REQ-03/04 modulate deliberately in the 1-65 Hz band and breach IEEE 1789 RP3 by ~9x). | spec-dimming s3.3 item 4 |
| **ENC-7** | PAR-REQ-14 (wide wash from 2.5 m) and PAR-REQ-15 (diffusion sufficient that R/G/B/W mix before reaching a surface) are **carried as enclosure requirements**, not PCB requirements. The 4-in-1 emitter's 140-degree beam meets PAR-REQ-14 from 2.5 m without a secondary lens; PAR-REQ-15 is met by the 4-in-1 by construction and **requires a real diffuser if the C4 fallback (RGB 3-in-1 + separate white) is taken**. | requirements Q8(a), led-emitter s10 |

### 5.1 Why the sealed branch does not close, stated plainly

A sealed 120 x 100 x 60 mm non-metallic box is **3.6-4.3 degC/W** from internal air
to room air (Hoffman 4.34, Rittal 3.61 - the two bracket it). **Nothing done on
the PCB changes that number**: not copper weight, not via farms, not MCPCB, not a
bigger internal heatsink.

At 4.0 degC/W and a 45 degC internal-air target in a 25 degC room, **total box heat
must be <= 5.0 W. The carrier alone is 2.4 W (af). The emitters alone are 5.94 W.**

| Configuration | In-box heat | Internal air, 25 degC room | Verdict |
|---|---|---|---|
| Sealed, LED module inside | 9.15 W | **62 degC** | **fails ENC-1 by 17 K** |
| Sealed, LED heat conducted through the wall (ENC-2 ii) | **3.21 W** | **38 degC** | **passes with margin** |
| Vented, LED module inside (ENC-2 i) | 9.15 W, but the box is no longer the bottleneck | room + <= 15 K | passes if the vent is measured, not assumed |

The corollary is the useful one and it is why this board is not the obstacle:
**this daughter contributes 0.79-0.81 W to the box across its entire output
range** (`power_tree.md` s6). The enclosure problem is the emitter module, and the
emitter module is off this board.

At the `at` operating point nothing closes: 250 mA/die gives 2.36 W of heat per
package against a 25.4 K/W budget at 40 degC air, versus a 19-23 K/W MCPCB path.
**The `at` case is marginal at best and fails against the ICD's own internal-air
figures, at either rail choice.** That is the real blocker on requirements Q2(b),
not the rail.

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

**The one thing this board must NOT provide: on-board emitters.** At 1.42 W of
package heat the FR4 path is 33-52 K/W against a 42.3 K/W budget at 40 degC air and
31.0 K/W at the ICD's 56 degC - it straddles or fails, and the emitters' positions
would then be dictated by the connector and keepout geometry rather than by the
optics. On an aluminium MCPCB the path is 19-23 K/W and closes with 1.3-2.2x
margin. **This is D3 and it makes requirements Q5 an H1 question**
(`decisions.md` OPEN-3): an internal wire-to-board harness is not an external
connector on any reasonable reading of ICD s9 - which itself anticipates the
off-board case - but it needs confirming, not assuming.

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

**LED module and heatsink, per fixture, budgeted separately** (not this board's
BOM): 4x C53153006 at $0.3341 = $1.34; aluminium MCPCB ~$3-6; ballast, NTC,
connector ~$0.50; heatsink $2-5; harness ~$1 -> **~$8-14/fixture**.

**Par fixture total: ~$26-37, x8 = $210-300.** Against the $500-1000 system budget
that must also cover 8-12 carriers, the strobes, enclosures and a **PoE+** switch
(D-01's upgrade path implies PoE+, materially more expensive than the PoE switch
the original budget assumed) this is **tight, and it is a system-level flag rather
than a problem with this board** (requirements Q14).
