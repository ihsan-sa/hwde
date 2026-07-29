# LUM-DTR-STROBE-A - stackup, clearance scheme and mechanical

P2 architect, 2026-07-28. The stackup name below is the only source; it comes from
`.claude/skills/ai-ee/reference/stackups.yaml` and is passed to `board_init.py --stackup`.

> **REV B - H1 REVISION, 2026-07-28.** **The stackup conclusion is UNCHANGED**: 4 layers,
> `JLC04161H-3313`, In1 + In2 both solid GND. RGBW's four drain pours do not overturn it - they
> strengthen drivers 1 and 4 in s1.1. Two sections changed: **s4, which no longer describes a
> manual Edge.Cuts edit** because `board_init.py --cutout` exists (requirements s10.5), and
> **s5.1, the area budget, which is now the binding constraint of the design.**

---

## 1. Selection

**Board class: 4-layer. Stackup: `JLC04161H-3313`.**

| | |
|---|---|
| Layers | 4 (F.Cu / In1.Cu / In2.Cu / B.Cu) |
| Thickness | **1.6 mm** (ICD s7.1, inherited) |
| Copper | 1 oz outer, 0.5 oz inner |
| Finish | HASL |
| Dielectric F.Cu -> In1.Cu | 0.2104 mm prepreg, er 4.05 |
| Core In1.Cu -> In2.Cu | 1.065 mm |
| Controlled impedance | **not used** - this board has no controlled-impedance net |

### 1.1 Why 4 layers, confirmed rather than assumed

Four independent drivers, in the order that decides it:

1. **48 V routing is 5x denser on inner layers.** The binding outer-layer clearance is
   **0.635 mm** (s2); the inner-layer requirement is IPC-2221B column B1's 0.10 mm, which is
   below JLC's 0.127 mm fab minimum, **so the fab minimum dominates and the HV requirement is free
   on In1/In2.** On a crowded board carrying `+48V_SW`, `/VBANK`, **four** `/drive_*/LED_K` nets
   and `/charge/CHG_GATE` (64 V, the highest net on the board), that is the single largest routing
   lever available. A 2-layer board would have to buy every one of those clearances twice, on both
   faces, in a plan that has already lost 2,328 mm2 to keepouts.
2. **The 2.6 A sub-microsecond pulse loop needs a return plane directly beneath the outbound
   conductor.** `refdesign` L1 and L6 are explicit: minimise the discontinuous loop, and resolve
   the conflict with the 48 V clearance rule **vertically** (return on the adjacent layer) rather
   than by narrowing the in-plane gap. On 4L that return is In1.Cu at **0.2104 mm**; on 2L it would
   be B.Cu at **1.53 mm**, a 7x larger loop - and B.Cu is where the two bottom-side connectors and
   the FET thermal pours live, so a 2L return plane would be badly fragmented anyway.
3. **The analogue chain needs a quiet reference.** A Kelvin-sensed 200 mohm shunt whose 10 %
   setpoint is 52 mV, a ratiometric Vds-fault comparator, a bank UVLO and a bank ceiling all
   reference the same node. That wants a solid plane, not a 2L pour that the pulse loop has been
   cut through.
4. **Thermal.** `check_thermal`'s 4-layer model floors at **45 C/W** against the 2-layer model's
   **55 C/W** - the planes spread heat laterally. **[REV B]** Applying the `a_eff` clamp of
   `power_tree.md` s5 to both models: 4-layer bottoms out at **51.1 C/W** (1.35 W allowed at 56 C
   air), 2-layer at **`55 + 119 exp(-645/350)` = 73.8 C/W** (0.93 W allowed). Against a declared
   **0.81 W** per pass FET the 4-layer board passes at 1.64x and the 2-layer at 1.15x - **and the
   2-layer margin evaporates entirely the moment the charge FET's 0.82 W or any of the 85-90 C
   ambient cases of `power_tree.md` s10 is applied.** With four pass FETs now sharing the board,
   4 layers is not a close call.

**Cost of the choice: about $1-2/board at qty 5-10** against a ~$24.50 board. It is not a
consideration.

### 1.2 The one thing 4 layers makes harder, and the mandatory answer

**The antenna column `(88,25)-(100,55)` forbids copper on ANY layer** (ICD s7.6): no traces, no
pour, no plane. A 4-layer board has two internal planes that `planes_gen` will otherwise pour to the
full board outline, so **the plane regions must be authored to void that column explicitly.** A
single positive rectangle cannot have a hole, so each plane layer needs three rectangles. See s7.

If that step is skipped, the ESP32-S3's PCB antenna 11 mm below sits under two solid ground planes
and is detuned. H1-Q8 made Wi-Fi a supported control path, so this zone is live, not vestigial.

### 1.3 Layer assignment

| Layer | Contents |
|---|---|
| **F.Cu** | All components (single-sided top SMD assembly per requirements s7). The pulse loops' outbound paths. **[REV B] FIVE FET drain thermal pours** - four pass FETs (`/drive_w/LED_K`, `/drive_r/LED_K`, `/drive_g/LED_K`, `/drive_b/LED_K`) and the charge FET (`+48V_SW`), **all five 48 V-domain nets needing 0.635 mm around their entire perimeter, including from each other**. All 48 V-domain routing that must reach a top-side pad |
| **In1.Cu** | **Solid GND**, voided at the antenna column. The pulse-loop return, the analogue reference, and the guaranteed reference for the two `high_speed` entries |
| **In2.Cu** | **Solid GND**, voided at the antenna column. Second return path for the 2.6 A pulse, reference for B.Cu, and the lateral heat spreader that earns the 4-layer `check_thermal` model |
| **B.Cu** | J3, J4 (reverse-mounted, facing down) and their escapes; **[REV B] mirrored drain pours for all FIVE power FETs, >= 350 mm2 each**, tied through the thermal via fields; short escape routing. **The mirrors are not optional decoration - they are half of the `a_eff` that reaches the 51.1 C/W clamp** (`power_tree.md` s5). **B.Cu carries copper only; requirements s7 fixes single-sided top SMD assembly, so no component may be moved here to relieve F.Cu density** |

**In2 is a second GND, not a `/VBANK` power plane.** A 48 V inner plane would force an antipad on
every through-hole on the board (six radial bank footprints, two connectors, five mounting holes,
two thermal via fields) and buys nothing: `/VBANK`'s only high-current run is bank(+) to the harness
connector, which is short and lives on F.Cu with In1 GND beneath it. `planes_gen`'s 4-layer default
is In1 GND + In2 dominant-power, so **this is a deliberate override.**

---

## 2. The 48 V clearance scheme - rev A2 numbers

### 2.1 The binding number is 0.635 mm, and `check_creepage` does not enforce it

| Item | Value | Source |
|---|---|---|
| Worst-case voltage on the board | **57 V DC** | IEEE 802.3 PSE maximum |
| IPC-2221B Table 6-1 column **B2** (external, uncoated), 51-100 V band | 0.60 mm - **the floor, not the requirement** | the table `check_creepage.py` transcribes |
| IPC-2221B column **B1** (internal), 51-100 V | 0.10 mm | below JLC's **0.127 mm** fab minimum, so the fab minimum dominates on In1/In2 |
| **BINDING board-wide requirement** | **0.635 mm** (0.025 in) on outer layers, around every 48 V net, board-wide, from the connector pads to the cap bank | **ICD s5.1 rev A2**: the TPS2378 datasheet's own layout section recommends 0.025 in between VSS and high-voltage signals; the larger of the vendor figure and IPC governs, and daughters inherit it |
| Insulation class | **functional only** | 57 V DC is below IEC 62368-1 **ES1** (60 V DC). No basic/supplementary/reinforced safeguard and no safety-mandated creepage. IPC-2221 does not separate creepage from clearance; 0.635 mm covers both |

**`check_creepage.py` demands only 0.60 mm.** A 0.635 mm layout therefore passes the P8 checker
**by construction** - the checker cannot fail a compliant board, but it also cannot catch a
0.61 mm one. **The 0.635 mm figure must be enforced by a hand-written `.kicad_dru` rule at P5.**

Two facts about that rule, carried from the carrier's `decisions.md` TRAP-1 and verified here by
reading the script:

- **`rules_gen` never reads the `voltages` key.** Nothing in the generated ruleset makes the P7
  router honour any 48 V clearance. The rule must be added by hand at P5 or P7 will route to the
  global clearance and P8 will hand back a rework loop.
- The rule must key on **`A.NetName`** - `A.Net` silently matches nothing.

Sketch for P5 (net names per `sheets.md` s2):

**[REV B]** Updated for the four per-colour drain nets:

```
(rule "hv_48v_outer"
  (constraint clearance (min 0.635mm))
  (condition "A.NetName == '+48V_SW' || A.NetName == '/VBANK' ||
              A.NetName == '/charge/CHG_GATE' ||
              A.NetName == '/drive_w/LED_K' || A.NetName == '/drive_r/LED_K' ||
              A.NetName == '/drive_g/LED_K' || A.NetName == '/drive_b/LED_K'")
  (layer outer))
```

**The rule is symmetric, so it also enforces 0.635 mm BETWEEN the four drain pours**, which is
required - they are four independent nets at up to 57 V, tiled next to each other on F.Cu.

### 2.2 `check_creepage` is same-layer only - which is what makes 4 layers work

Verified by reading `check_creepage.py`: it iterates `for layer in bg.copper_layers` and compares
`net_copper(hv, layer)` against `net_copper(other, layer)`. **It does not check vertical
face-to-face separation.** So a solid GND plane on In1.Cu sitting 0.2104 mm below a 57 V trace on
F.Cu is not a violation - correctly, because IPC-2221 conductor spacing is an in-plane rule and
0.21 mm of FR4 stands off kilovolts. The ICD's "the clearance applies through the board too" clause
is satisfied by the **inner-layer** number (0.10 mm IPC / 0.127 mm fab), which the stackup meets by
5x.

### 2.3 What is NOT claimed

**The 0.13 mm "permanent polymer coating" column (B4) is NOT claimed.** Standard LPI soldermask is
not a qualified conformal coating, and `check_creepage.py` implements **only the uncoated columns**
- a layout designed to 0.13 mm fails P8 with **no waiver mechanism**. Do not reach for it if the
layout gets tight; shrink the annular ring on the 48 V pads instead (ICD s5.2 names that as the
intended lever).

### 2.4 Part-level consequences

- **Any resistor across the 48 V domain must be 0805 or larger, or split into two in series.**
  0402/0603 are typically 50-75 V working; 0805 is 150 V, 1206 is 200 V, 2512 is 200-500 V. This
  bites the passive bleed (single 0805 100 k, 2.6x margin - and its own pad-to-pad gap of ~0.80 mm
  clears 0.635 mm) and both rail-sense dividers (**2 x 82 k series-split**, each part seeing 26.9 V
  at the 57 V worst case = 6.6x margin, while also satisfying the <= 10 kohm ADC source-impedance
  limit at Rth 9.43 k).
- **Every capacitor on the 48 V domain must be 100 V rated.** 63 V is not enough at 57 V once
  ceramic DC-bias derating is applied - and note that a 10 uF / 100 V X7S 1210 reads **2.7 uF at
  48 V and 2.1 uF at 57 V**, so any calculation using the nameplate value is out by 3.7x.
- **P5 pad-geometry check, not a P8 discovery:** the D2PAK tab-to-lead gap on both power FETs is a
  57 V-to-0 V pair inside a single footprint. Confirm the chosen footprint clears 0.635 mm before
  routing; if it does not, the fix is a footprint variant, not a DRC waiver.

---

## 3. Mechanical - the common LUMINA footprint

Inherited from ICD s7.1, not chosen by this board. Origin: board top-left, x right, y down.

| Item | Value |
|---|---|
| Outline | **100.0 x 80.0 mm** |
| Corner radius | **3.0 mm**, all four corners |
| Thickness | **1.6 mm** |
| Mounting holes | **4x M3 (3.2 mm) at 5 mm inset** (a 90 x 70 mm rectangle) **plus a 5th M3 at (46, 74)** |
| Stack | Stacked mezzanine, daughter above the carrier, **11.0 mm** hard-seated |
| Standoffs | 5x M3 female-female, 11.0 mm |
| Socket orientation | **Faces downward** |

`board_init.py` invocation for P5:

```
board_init.py --stackup JLC04161H-3313 --outline 100x80 --corner-radius 3 \
              --cutout 6,0,30,26 --mounting-holes 4 ...
```

**[REV B] `--cutout` is outline-relative, so it needs no re-basing** - unlike `placement.keepouts`,
which do (s7). See s4.

Per MECH-01 the radius defaults to 0 and must be passed explicitly, and it is **clamped to the
mounting-hole inset (`margin / 2`)**, so 3.0 mm works at the default `--margin 6`. **Read
`corner_radius` and `worker_notes` in the board_init report - do not assume the requested value was
honoured.** H5 at (46, 74) is added at P4 as a `MountingHole_3.2mm_M3` symbol so it carries a
refdes; `--mounting-holes` makes corner holes only.

Per MECH-02 there is **no outline-shrink step - the P5 outline is final.**

---

## 4. The RJ45 notch - RESOLVED, `--cutout` exists  **[REV B]**

> **BLOCKING-01 is the coordinator's, not this run's** (`requirements.md` s10.5). A `--cutout` flag
> was added to `board_init.py` centrally because both daughters need the notch. **This run does not
> implement a workaround, does not shrink the outline, and does not hand-edit Edge.Cuts.**
>
> **CONFIRMED RESOLVED by the coordinator: the flag exists, is tested, is committed (`18613d3`),
> and was verified end-to-end on this exact geometry.**

**The P5 invocation, verbatim:**

```
--outline 100x80 --corner-radius 3 --mounting-holes 4 --cutout 6,0,30,26
```

**Four properties of the flag that this board depends on, recorded so a later change cannot break
them silently:**

1. **Cutout coordinates are mm relative to the outline's top-left corner**, and the flag is
   **repeatable**. Being outline-relative it needs **no re-basing** - unlike `placement.keepouts`,
   which do (s7). This board uses exactly one cutout.
2. **The notch must touch an outline edge to be a notch.** Ours does: `y = 0` puts it on the top
   edge, which is what ICD s7.6 requires anyway.
3. **It must not overlap a corner radius**, or the outline self-intersects and `polygonize` fails
   downstream; the tool skips the cutout with a note rather than drawing it. **At `r = 3` a notch
   starting at `x = 6` clears comfortably - re-check if either number changes.** The 3 mm radius
   and the 6 mm notch inset are both inherited from ICD s7.1/s7.6, so neither should move, but a
   change to either is a re-check trigger.
4. **Interior windows are refused outright (exit 2), by design.** `geom._parse_outline` returns on
   the first `gr_rect` it finds on Edge.Cuts, so an inner rectangle would silently *become* the
   board outline - a 10x10 window on a 100x80 board parses as area 100.0, and DFM, plane
   generation and quoting would all see a 10x10 board with no error raised anywhere.
   **Edge notches are the supported path; do not try to express anything on this board as an
   interior window.**

> **The notch region stays a hard placement keepout in `constraints.json` regardless**, so the board
> is electrically correct whether or not the cut lands.

**P5 coordinate-translation trap - read the report, do not trust the flag silently.**
`board_init` now reports **`outline_origin`** and **absolute `cutouts`**. In fixed-outline mode
**the origin derives from the packed component bounding box, so it is NOT (0,0)**, and every
keepout rect in `constraints.json` needs translating into board space by that origin (s7 step 2).
At P5, read **`outline_origin`, `corner_radius`, `cutouts` and `worker_notes`** out of
`reports/board_init.json`, and confirm `geom` reads a **non-empty outline whose area matches
expectation** (100 x 80 less the 780 mm2 notch = **7,220 mm2**, not 8,000). A silently-skipped
cutout shows up as an area of 8,000 and nothing else. **Confirm again at P9 that the notch is
present in the exported Gerbers' outline layer.**

ICD s7.6 and H1-Q4 require **a 30 x 26 mm relief in the TOP edge, region (6,0)-(36,26)** - 780 mm2
of board material removed. It is load-bearing twice over:

1. The carrier's board-edge magjack is ~15 mm tall against an 11.0 mm stack, so the jack protrudes
   ~4 mm above this board's underside. **Without the notch the boards cannot be forced flat.**
2. It is the **primary reverse-insertion interlock** (CAR-REQ-16). The 4x M3 pattern is
   rotationally symmetric, so a daughter can be bolted down rotated 180 degrees; rotated, the notch
   lands at the bottom edge and the board presents solid material over the jack. **A mechanical
   stop, not a warning.**

**[REV B] `board_init.py` invocation for P5, complete:**

```
board_init.py --stackup JLC04161H-3313 --outline 100x80 --corner-radius 3 \
              --cutout 6,0,30,26 --mounting-holes 4 ...
```

**Rev A's analysis (superseded):** rev A read `board_init.py` as writing Edge.Cuts as a filleted
rectangle and nothing else, found that no other pipeline script writes Edge.Cuts geometry
afterwards, and concluded the notch had to be a manual KiCad edit or a fab-side routing note. **That
conclusion was correct at the time and is now obsolete** - the `--cutout` flag was added centrally
in response to exactly this finding, from both daughters. **Do not carry the manual-edit
recommendation forward into DOC-01.**

---

## 5. Exclusion zones

Board-relative, ICD s7.6, all declared as `placement.keepouts` in `constraints.json`.

| Zone | Region | Area | Requirement |
|---|---|---|---|
| **RJ45 relief** | **(6,0)-(36,26)** | 780 mm2 | Board material removed by `--cutout 6,0,30,26` (s4). **Hard keepout for parts and copper on every layer, both sides, kept in `constraints.json` regardless of the cut** |
| **DC-DC hot zone** | **(2,46)-(36,68)** | 748 mm2 | **No LED drivers and no aluminium electrolytics.** The carrier's 48->12 converter dissipates up to 1.25 W directly below in a sealed box; electrolytic life halves per 10 C. A *vertical* keepout, not an in-plane separation rule. **Declared as a full keepout** - the pass FET *is* an LED driver and the bank *is* aluminium electrolytic, which is most of what would otherwise want that area |
| **Antenna column** | **(88,25)-(100,55)** | 360 mm2 | **No copper on any layer, no metal component.** Placement keepout both sides **plus** the plane-region carve-out of s7 |
| **Recovery header** | **(76,0)-(98,20)** | 440 mm2 | Keep clear both sides so a 6-way jumper lead can be attached with this board fitted |

### 5.1 Area budget - THE binding constraint of this design  **[REV B]**

Full derivation and the mitigation ladder are `blocks.md` s6.3. Summary:

```
  usable F.Cu (8,000 less 2,328 keepout less 520 connector)   5,152 mm2

  rev A as written  (Q200 1000 + Q100 645 pours)             ~3,559 mm2  = 69 %
  rev A corrected   (both pours 350 F.Cu, per the a_eff clamp) 2,614 mm2  = 51 %
  REV B, RGBW       (4 pass pours + 1 charge pour, all 350)    4,199 mm2  = 81 %
```

**Two facts have to be read together.** RGBW costs **30 points** of F.Cu occupancy - and the
`check_thermal` `a_eff` clamp, once read properly, **gave 18 of them back first** by showing that
rev A's 1000 mm2 pour was 2.9x larger than anything the model scores (`power_tree.md` s5,
`blocks.md` s6.1). **Without that correction this revision would not fit.**

**81 % before routing channels is the riskiest number in this package**, and it is worse than it
looks because **both inner layers are solid GND, so every signal route lands on F.Cu or B.Cu**, and
**B.Cu cannot take components** (requirements s7: single-sided top SMD assembly). It is feasible -
pours flow around parts, and five of the largest claims are copper rather than components - but it
is the thing most likely to force a change at P6.

**Declared mitigations, in the order they must be reached for:**

1. **Drop the two unpopulated bank footprints** (6 -> 4 D18 lands): **-400 mm2 -> 73 %.** Costs the
   2720 -> 4080 uF knob and the four-vendor 470 uF second source. Pure optionality, so it goes first.
2. **Hold every drain pour at exactly 350 mm2 on F.Cu and put all further copper on B.Cu.** Free.
3. **Two quad op-amps in place of four duals**: -30 mm2, two fewer packages, at the cost of the
   "each stage is a self-contained placement group" property.
4. **0402 for passives outside the 48 V domain** (the 48 V domain is locked at 0805 minimum by
   s2.4 and cannot shrink): ~-60 mm2.

**Do not reach for the DC-DC hot zone** - it is a vertical keepout over a 1.25 W hot spot in a
sealed box, and the bank is the most lifetime-sensitive part on the board (`power_tree.md` s10.5
already cuts its rated life 10x if the internal air is really 85-90 C). **And do not shrink any
pour below 350 mm2 F.Cu + 350 mm2 B.Cu** - that comes straight off the thermal margin, which s10
shows has none to give. **If P6 cannot place it after 1-4, the finding is that the RGBW strobe
wants a bigger board than the common LUMINA 100 x 80 footprint, which is an ICD s7.1 change and a
program decision.**

### 5.2 Height

- **Bottom side:** the two 8.5 mm socket bodies inside the 11.0 mm stack. Nothing else may protrude
  below - B.Cu carries copper pours and escapes only.
- **Top side:** the bank is the tallest part at **27.0 mm** (25 mm can + 2.0 mm sleeve tolerance)
  against open question 5's default ceiling of **30 mm**. That leaves 3 mm for a not-yet-designed
  enclosure. **Fallbacks in order if the ceiling collapses: 22.0 mm (6 x 470 uF radial),
  21.0 mm (13 x 220 uF SMD), 16.5 mm (13 x 220 uF short SMD).** Below ~16 mm nothing in the
  2,800 uF / 100 V class exists and the energy budget has to come down.
- **Vent orientation:** D18 cans have a top-face pressure-relief vent. In a sealed plastic enclosure
  a vent event dumps electrolyte inside the box - point the vents away from the LED wiring and the
  connectors.

---

## 6. Silkscreen the board must carry

- **Pin-1 triangle** at position 1 of both J3 and J4 (ICD s7.4.5).
- **`^^ RJ45` edge arrow** on the top edge, matching the carrier's.
- **`STORED ENERGY 3.1 J / 48 V - WAIT 5 s AFTER UNPLUG`** near the bank (requirements s8.3; the
  active bleed reaches 10 V in 4.0 s, the passive backstop alone takes 7 minutes).
- **`FLOATING AT PoE POTENTIAL - DO NOT EARTH-REFERENCE`** at every test point (requirements s8.4:
  an earthed probe or a non-isolated USB-UART breaks PD signature detection outright, because
  detection currents are only a few hundred microamps).

---

## 7. MANDATORY P5 STEP - re-basing the keepouts and authoring the plane regions

**`board_init` does not place the outline at (0,0).** The outline origin is derived from the packed
component bounding box, so every rectangle in this document is in the **ICD frame** (board top-left
= origin) and must be translated into the board frame before it means anything.

`constraints.json` ships `placement.keepouts` **in the ICD frame** because the assignment for this
board requires the regions to be declared, and an absent keepout would let a part land in the
antenna column or the notch. **They are therefore correct only if `board_init` happens to place the
outline at the origin.** At P5, after `board_init` and before `place_seed`:

1. Read `reports/board_init.json` -> `outline_bbox = [ex1, ey1, ex2, ey2]` (and check
   `corner_radius` and `worker_notes` while you are there).
2. If `(ex1, ey1) != (0, 0)`, **add `(ex1, ey1)` to every rect in `placement.keepouts`** in
   `kicad/constraints.json`.
3. **Author the plane regions**, which `architecture/constraints.json` deliberately ships without -
   a placeholder region in the wrong place is worse than an absent one, but an *absent* region here
   means solid copper in the antenna column, so this step is not optional:

```jsonc
"planes": [
  {"layer": "In1.Cu", "net": "GND", "region": [ex1, ey1,      ex2,      ey1+25]},
  {"layer": "In1.Cu", "net": "GND", "region": [ex1, ey1+25,   ex1+88,   ey1+55]},
  {"layer": "In1.Cu", "net": "GND", "region": [ex1, ey1+55,   ex2,      ey2   ]},
  {"layer": "In2.Cu", "net": "GND", "region": [ex1, ey1,      ex2,      ey1+25]},
  {"layer": "In2.Cu", "net": "GND", "region": [ex1, ey1+25,   ex1+88,   ey1+55]},
  {"layer": "In2.Cu", "net": "GND", "region": [ex1, ey1+55,   ex2,      ey2   ]}
]
```

Three rectangles per plane layer, because a single positive rectangle cannot have a hole. The middle
band stops at `ex1 + 88` so the antenna column `(88,25)-(100,55)` carries **no plane copper on
either inner layer**.

4. **F.Cu and B.Cu**: the antenna column is kept copper-free by the `side: "front"` and
   `side: "back"` placement keepouts plus the router's own avoidance of an empty region. **Add a P8
   manual check that no outer-layer pour, trace or via lands in `(88,25)-(100,55)` on any layer** -
   this is the one ICD clause with no automated checker behind it.
5. **Add the `hv_48v_outer` `.kicad_dru` rule of s2.1** at the same time. `rules_gen` will not
   produce it.
