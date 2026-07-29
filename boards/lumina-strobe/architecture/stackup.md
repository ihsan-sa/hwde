# LUM-DTR-STROBE-A - stackup, clearance scheme and mechanical

P2 architect, 2026-07-28. The stackup name below is the only source; it comes from
`.claude/skills/ai-ee/reference/stackups.yaml` and is passed to `board_init.py --stackup`.

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
   on In1/In2.** On a crowded board carrying `+48V_SW`, `/VBANK`, `/drive/LED_K` and
   `/charge/CHG_GATE` (64 V, the highest net on the board), that is the single largest routing
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
   **55 C/W** - the planes spread heat laterally. At the pass FET's declared 1.45 W that is the
   difference between an allowed rise of 65 C and 80 C at the same copper area, against a 69 C
   budget. **On 2 layers the pass FET does not pass P8 at any pour size.** That alone closes it.

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
| **F.Cu** | All components (single-sided top SMD assembly per requirements s7). The pulse loop's outbound path. The two FET drain thermal pours (**48 V-domain nets - 0.635 mm around their entire perimeter**). All 48 V-domain routing that must reach a top-side pad |
| **In1.Cu** | **Solid GND**, voided at the antenna column. The pulse-loop return, the analogue reference, and the guaranteed reference for the two `high_speed` entries |
| **In2.Cu** | **Solid GND**, voided at the antenna column. Second return path for the 2.6 A pulse, reference for B.Cu, and the lateral heat spreader that earns the 4-layer `check_thermal` model |
| **B.Cu** | J3, J4 (reverse-mounted, facing down) and their escapes; **mirrored drain pours for Q200 and Q100**, tied through the thermal via fields; short escape routing. Otherwise clear |

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

```
(rule "hv_48v_outer"
  (constraint clearance (min 0.635mm))
  (condition "A.NetName == '+48V_SW' || A.NetName == '/VBANK' ||
              A.NetName == '/drive/LED_K' || A.NetName == '/charge/CHG_GATE'")
  (layer outer))
```

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
board_init.py --stackup JLC04161H-3313 --outline 100x80 --corner-radius 3 --mounting-holes 4 ...
```

Per MECH-01 the radius defaults to 0 and must be passed explicitly, and it is **clamped to the
mounting-hole inset (`margin / 2`)**, so 3.0 mm works at the default `--margin 6`. **Read
`corner_radius` and `worker_notes` in the board_init report - do not assume the requested value was
honoured.** H5 at (46, 74) is added at P4 as a `MountingHole_3.2mm_M3` symbol so it carries a
refdes; `--mounting-holes` makes corner holes only.

Per MECH-02 there is **no outline-shrink step - the P5 outline is final.**

---

## 4. OPEN MECHANICAL ISSUE - the RJ45 notch cannot be produced by this pipeline

**This is a known tooling gap. It is documented here for the human, not solved.**

ICD s7.6 and H1-Q4 require **a 30 x 26 mm relief in the TOP edge, region (6,0)-(36,26)** - 780 mm2
of board material removed. It is load-bearing twice over:

1. The carrier's board-edge magjack is ~15 mm tall against an 11.0 mm stack, so the jack protrudes
   ~4 mm above this board's underside. **Without the notch the boards cannot be forced flat.**
2. It is the **primary reverse-insertion interlock** (CAR-REQ-16). The 4x M3 pattern is
   rotationally symmetric, so a daughter can be bolted down rotated 180 degrees; rotated, the notch
   lands at the bottom edge and the board presents solid material over the jack. **A mechanical
   stop, not a warning.**

**The gap, verified against the scripts:** `board_init.py` writes Edge.Cuts as a rectangle with an
optional corner fillet (`--outline WxH --corner-radius R`) and nothing else. **No pipeline script
writes Edge.Cuts geometry afterwards** - the other modules that touch that layer (`planes_gen`,
`dfm_check`, `fab_export`, `order_quote`, `geom`, `gerblib`, `board_swig`) only *read* it to derive
the board boundary. **ai-ee cannot cut this notch.**

**Consequence and the recommended resolution, for the human at H1:**

- The board this run produces will have a **plain 100 x 80 mm filleted rectangle** on Edge.Cuts.
- **Nothing will be placed or routed in the notch region** - it is declared as a hard placement
  keepout on both sides in `constraints.json` (s7), so the region is empty copper and empty
  silkscreen and the fabricated board is *electrically* correct.
- The notch must therefore be added **by hand to the Edge.Cuts layer in KiCad after P5 and before
  P9 fab export**, or requested as a fab-side routing note on the JLC order. Either way it is a
  **manual step outside the pipeline**, and it must be captured in DOC-01 and in the order package.
- **Do not defer it to "we will file it later".** MECH-02 makes the P5 outline final inside the
  tool, and the notch is an interlock, not a cosmetic relief.

**Recommendation: accept the manual Edge.Cuts edit, and add a P9 pre-order checklist item that the
notch is present in the exported Gerbers.** The alternative - teaching `board_init` arbitrary
outline polygons - is a skill change, not a board change, and is out of scope for this run.

---

## 5. Exclusion zones

Board-relative, ICD s7.6, all declared as `placement.keepouts` in `constraints.json`.

| Zone | Region | Area | Requirement |
|---|---|---|---|
| **RJ45 relief** | **(6,0)-(36,26)** | 780 mm2 | Board material removed (s4). Hard keepout for parts and copper on **every** layer, both sides |
| **DC-DC hot zone** | **(2,46)-(36,68)** | 748 mm2 | **No LED drivers and no aluminium electrolytics.** The carrier's 48->12 converter dissipates up to 1.25 W directly below in a sealed box; electrolytic life halves per 10 C. A *vertical* keepout, not an in-plane separation rule. **Declared as a full keepout** - the pass FET *is* an LED driver and the bank *is* aluminium electrolytic, which is most of what would otherwise want that area |
| **Antenna column** | **(88,25)-(100,55)** | 360 mm2 | **No copper on any layer, no metal component.** Placement keepout both sides **plus** the plane-region carve-out of s7 |
| **Recovery header** | **(76,0)-(98,20)** | 440 mm2 | Keep clear both sides so a 6-way jumper lead can be attached with this board fitted |

### 5.1 Area budget - the tightest thing in this design

```
  board                                        8,000 mm2
  - RJ45 notch                                  -780
  - antenna column                              -360
  - recovery header                             -440
  - DC-DC hot zone                              -748
  - J3 + J4 footprints (THT, both faces lost)   -520
  ----------------------------------------------------
  usable                                       5,152 mm2

  claims:
    bank, 4 radial D18 populated of 6 footprints  1,214 mm2
    Q200 drain pour (>= 900, target 1000)         1,000 mm2
    Q100 drain pour (>= 645)                        645 mm2
    hot-swap, drive, protect, bleed, dividers,
      test points, ~50 small parts                ~700 mm2
  ----------------------------------------------------
  claimed                                      ~3,559 mm2   = 69 % occupancy
```

**69 % before routing channels is the riskiest number in this package.** It is feasible - pours flow
around parts, and the two drain pours are copper rather than components - but it is the thing most
likely to force a change at P6. **The declared mitigations, in the order they should be reached
for:** (1) mirror more of each drain pour onto B.Cu, which is nearly empty; (2) drop Q200's pour to
the 900 mm2 floor (`theta_JA` 47.1 C/W, still 1.03x on the armed worst case, and the bank ceiling of
`power_tree.md` s6 means the *normal* case only needs 0.82 W); (3) fall back to the six-footprint
bank populated at 4 x 470 uF from a shorter can. **Do not reach for the DC-DC hot zone** - it is a
vertical keepout over a 1.25 W hot spot in a sealed box, and the bank is the most
lifetime-sensitive part on the board.

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
