# buck-5v3a - stackup and mechanical baseline

## Chosen stackup

**`JLC04162H-7628A`** - JLCPCB impedance-controlled 4-layer, 1.6 mm nominal,
2 oz outer / 0.5 oz inner copper, HASL. Read back live from JLC's own
`getImpedanceTemplateSettingList` on 2026-08-06 (template code
202410110444432104), `available: true` in `reference/stackups.yaml`.

### 1.1 Properties, rule class, fallback

*(Deliberately below its own heading: `order_submit.derive_copper_oz` scans only
the lines under the `Chosen` heading up to the next one, and its `_(\d+)oz` regex
takes precedence over the stackup-name lookup - so a `4layer_1oz`/`4layer_2oz`
class token or a second stackup id inside that window can silently decide the
copper weight this board is QUOTED at. Keep the window to the chosen name alone.)*

- Layers: **4**. Outer copper: **2 oz (0.070 mm)**. Inner: 0.5 oz (0.0152 mm).
- Lamination: 7628x2 prepreg 0.4284 mm / core 0.550 mm / 7628x2 prepreg 0.4284 mm.
- Design-rule class: `4layer_2oz` - min trace 0.1524 mm, min clearance 0.1016 mm,
  min via 0.45/0.2 mm.
- No controlled-impedance profile is used: there is no standards-bound or
  high-speed net on this board.
- Fallback if the H1/P10 cost answer rejects 2 oz: **`JLC04161H-1080B`**
  (4L, 1 oz outer / 0.5 oz inner) - see s4, and note the fallback is safe in that
  direction only.

## 2. The layer-count decision, and the theta_JA conflict

> **SUPERSEDED IN PART - read `reports/thermal-recheck.md` alongside this.**
> This section was written assuming U1 had an exposed thermal pad with a via
> array under it. It does NOT (`reports/u1-land-ruling.md`: 9 lands, no EP -
> the "13" in V-DFN3020-13 counts terminals). The recheck kept the CONCLUSION
> of this section (4 layers, JLC04162H-7628A, 2 oz outer, theta_JA 51.1 C/W,
> Tj ~95 C) but replaced its REASONING on three points:
> - The 4L-vs-2L thermal gap is ~3 C, not ~20 C. The via-depth argument in
>   2.3 (0.21 mm to In1 vs 1.6 mm to B.Cu through an EP) describes a heat path
>   that does not exist, and the repo's 73.8 C/W 2L figure is a 1 oz
>   calibration applied to a 2 oz board.
> - **4 layers are kept for the unbroken In1 GND return under the hot loop
>   (DS41948 rule 6, topologies/buck.md s3) and for the gate - NOT for Tj.**
> - The +10 C neighbour-heating allowance in 2.4 is retired as double
>   counting; the model already brackets it. Tj is ~95 C, not ~105 C.
> The heat exits are the VIN land (~1.16 mm2) and the GND land (~1.16 mm2),
> so the P6 prescription is vias in the pour AROUND the GND land, not under a
> pad: see the recheck for the quantified version.

### 2.1 The conflict

Two sources disagreed by 2x on the number that decides the whole board:

| Source | theta_JA | Test condition |
|---|---|---|
| **Diodes DS41948 Thermal Resistance table, Note 6** | **25 C/W** | V-DFN3020-13/SWP on **FR-4, four-layer, 2 oz copper, minimum recommended pad layout** (JEDEC-class board, 76.2 x 114.3 mm) |
| **Repo `check_thermal.py` calibrated model, >= 4 copper layers, pour saturated** | **51.1 C/W** | `theta_floor 45 + (140-45) x exp(-A/235)`, A capped at 645 mm^2; calibrated to JESD51 / SLOA122 anchors |
| same model, 2 copper layers, pour saturated | 73.9 C/W | 1 oz, bottom pour |

### 2.2 Ruling - the datasheet's 25 C/W LOSES, and it is not close

**The repo model's 51 C/W is the design number.** Three independent reasons:

1. **The datasheet figure is a JEDEC board measurement, not a board-design number.**
   A JESD51-7 four-layer test coupon is 76.2 x 114.3 mm = **8710 mm^2 - 4.4x this
   board's 2000 mm^2**, and its planes are unbroken and unloaded. TI publishes the
   same class of number for the LMR33630 (42.9 C/W) and states verbatim that it
   "can not be used for design purposes". Diodes does not carry that disclaimer, but
   the measurement has the same standing.
2. **The heat-spreading area saturates well below the JEDEC board.** The repo model
   caps effective copper at 645 mm^2 (~1 in^2) inside a 14.3 mm reach radius, which
   is the physics reason a bigger board keeps helping past the point our board runs
   out of. 51 C/W is ~19 % worse than TI's 4-layer JEDEC anchor - a consistent,
   physically-motivated penalty for a small board, not a made-up derate.
3. **51 C/W is the number the P8 gate will actually apply.** Designing against 25 C/W
   would produce a board that passes on paper and fails its own verification gate.

The datasheet's 25 C/W is not discarded - it is retained as the **optimistic bound**.
If the real board measures anywhere between the two, the design has margin it did not
count on. The bench check that settles it after fabrication is
`Tj = T_case_top + psi_JT x P`, measured on the package top, not theta_JA.

### 2.3 The answer to the question, machine-run

`check_thermal.py` needs a `.kicad_pcb`, and no board exists before P5. A synthetic
probe board was built for this merge that models the intended layout - 50 x 40 mm
outline, U1's real V-DFN3020-13 land pattern (DS41948 p.27, 2.30 x 2.825 mm) at
(18, 20), a ~250 mm^2 top GND pour joined to the exposed-pad land, a 3x3 array of
0.3 mm thermal vias plus 3 more in the surrounding pour (12 within 2.9 mm), solid GND
on In1/In2 and a full B.Cu GND pour - and the repo's real `check_thermal.py` was run
against it, unmodified, at both layer counts:

| Stack | Case | P_IC | Effective GND copper | theta_JA | Rise | Tj at 50 C amb | Gate |
|---|---|---|---|---|---|---|---|
| **4L** | **AP63356Q, 7 V corner (modelled)** | **0.88 W** | 645 mm^2 (saturated) | **51.1** | **45.0 C** | **95.0 C** | **pass** |
| **4L** | **AP63356Q + spread margin (the constraint)** | **0.95 W** | 645 mm^2 | 51.1 | **48.6 C** | 98.6 C | **pass, 6.4 C margin** |
| 4L | AP63356Q, 12 V / 18 V corners | 0.82 W | 645 mm^2 | 51.1 | 41.4 C | 91.4 C | pass |
| 4L | 95/66 mohm mainstream 3 A class | 1.21 W | 645 mm^2 | 51.1 | 61.8 C | 111.8 C | **FAIL** |
| **2L** | **AP63356Q, 7 V corner** | **0.88 W** | 645 mm^2 | **73.8** | **65.0 C** | **115.0 C** | **FAIL** |
| 2L | AP63356Q + spread margin | 0.95 W | 645 mm^2 | 73.8 | 70.2 C | 120.2 C | FAIL |
| 2L | 95/66 mohm mainstream class | 1.21 W | 645 mm^2 | 73.8 | 89.4 C | 139.4 C | FAIL |

> **ANSWER: yes - the AP63356QZV-7 clears the target at the 7 V low-line corner,
> 3 A, 50 C ambient, on the chosen 4-layer stackup, and ONLY on 4 layers.**
> 45 C rise against the 55 C allowed by a 105 C junction target. The same part on
> 2 layers is 65 C of rise and 115 C of junction - a fail with the pour already
> saturated, so no amount of copper rescues it. **The shortlist has a survivor, and
> the survivor requires 4 layers.** The 2-layer option is closed.

Note the 2L rows are generous: the probe gives 2L a saturated 645 mm^2 pour, which a
real 2-layer board would not have, because B.Cu is also the return path and gets cut
by the output routing. 2L is worse in practice than the table says.

### 2.4 The honest margin statement for the human

`check_thermal` models one hot part on a board that is otherwise at ambient. This
board is not: **0.37-0.60 W of L1, F1, Q1 and copper loss** sits on the same pours
(`power_tree.md` s3). `research/power.md` s4.2 allowed +10 C for that, and that
allowance is adopted here. So:

| | Gate number (`check_thermal`) | With the +10 C neighbour allowance |
|---|---|---|
| Tj at 50 C ambient, 4L, 7 V corner | 95 C | **~105 C** |
| Against the 105 C derated target (requirements s3, ASSUMED) | 10 C margin | **~0 C margin** |
| Against 150 C recommended max Tj (DS41948) | 55 C | **45 C** |
| Against 170 C thermal shutdown | 75 C | 65 C |

**Read that plainly: the board is comfortable against the PART's limits and exactly
at the assumed 105 C hotspot target.** The 105 C figure is an assumption the
requirements analyst wrote, not a user answer - which is precisely why
`research/power.md` open item 3 asks the human whether 105 C is a hard filter. It is
carried to H1 unchanged. Every number here also carries the model's stated +/-30 %.

Two things that would move it, if margin is wanted later: **AOD403 in DPAK instead of
AO4407A** for Q1 (-17 mW, and a large drain tab that spreads input-side heat), and
**a lower-DCR inductor** (each 5 mohm of DCR off L1 is 45 mW off the board total).
Neither touches U1's own dissipation, which is 60 % of the problem.

## 3. Layer assignment

| Layer | Net / role |
|---|---|
| **F.Cu** (2 oz) | All components (top-side SMT only, A11). The hot loop Cin -> VIN -> GND. The `/SW` polygon, kept as small as 0.78 mm of required width allows. The `+5V` output pour from L1/Cout to J2. GND pour joined to U1's exposed-pad land (>= 200 mm^2). |
| **In1.Cu** (0.5 oz) | **Solid GND.** Unbroken under U1 and under the entire Cin/VIN/GND loop. This is both the return plane and the primary heat spreader - it is 0.43 mm below the EP via array. |
| **In2.Cu** (0.5 oz) | **GND again, deliberately NOT +5V.** `+5V` travels ~20 mm on F.Cu and needs no plane; a second GND plane is worth more as thermal mass and lets the EP via array see copper on both inner layers. This overrides `planes_gen`'s 4-layer default (In2 = dominant power net), which is why `planes` is declared explicitly in `constraints.json`. |
| **B.Cu** (2 oz) | GND pour, kept clear of SMT parts (A11), acting as the bottom heat-radiating surface and via-array landing. |

## 4. Why 2 oz outer, and why the 1 oz fallback is one-way

`JLC04161H-1080B` (1 oz outer) is the repo's 4-layer default and is cheaper. It was
rejected for four reasons, in descending weight:

1. **Switch-node containment.** `/SW` carries 3.6 A peak. IPC-2152 (via the repo's
   own `check_current.required_width_mm`) wants **1.56 mm at 1 oz and 0.78 mm at
   2 oz** for dT 20. The switch node is the board's aggressor and buck.md s5 says
   keep it as small as electrically possible - 2 oz literally halves it. Same story
   on `+5V`: 2.31 mm -> 1.16 mm.
2. **The vendor's own layout rule 1** (DS41948, PCB Layout): *"2 oz copper on both
   top and bottom layers recommended"*, given verbatim for the 3.5 A load case. The
   25 C/W thermal figure is measured on a 2 oz board.
3. **`check_thermal`'s multilayer model is itself calibrated as "2 oz / 4-layer"**
   (`MODEL_ML` docstring). Applying it to a 1 oz outer board would be optimistic in a
   place where this design has ~0 C of margin (s2.4).
4. **Copper loss.** ~0.06 W off the board total, i.e. ~1 C of the neighbour-heating
   allowance, free.

**The fallback is safe in one direction only.** `4layer_2oz` demands a min trace of
0.1524 mm where `4layer_1oz` allows 0.1016 mm; clearances are 0.1016 mm in both. A
board routed to the 2 oz rule class therefore also passes the 1 oz class, so
retreating to `JLC04161H-1080B` at P10 costs nothing but a `board_init` re-run.
Going the other way (routing at 1 oz, then buying 2 oz) does not work.

**Cost caveat, stated because it is not quantified anywhere in this repo:**
`reference/jlc_pricing.yaml` has **no copper-weight term at all** and explicitly
forbids inventing one. A live 4-layer quote on a 1 oz/0.5 oz stackup came back with
`insideCuprumThicknessFee` at **48 % of the whole bare-PCB price** (LEARNINGS
2026-07-30), so copper weight is a first-order cost driver here and the 2 oz outer
adder is real but unpriced. **P10 `order_quote --api` is the only authority.** At
qty 5 the absolute number is small either way (s6).

## 5. Outline and mechanical baseline

**RECOMMENDED OUTLINE: 50 x 40 mm - take the cap in full.** This binds permanently at
P5 `board_init`; there is no outline-shrink step later.

Area accounting behind that (part footprints only, before clearances):

| Item | Area |
|---|---|
| J1 + J2 screw terminals, ~10.2 x 10.0 mm each, on opposite edges (depth 10.0 mm and height 14.07 mm are read off the vendor drawing; the ~10.2 mm width is inferred from 2 x 5.08 mm pitch and is NOT drawing-confirmed) | 204 mm^2 |
| 4 x M3 mounting-hole keep-clear (6 mm dia each) | 113 mm^2 |
| L1 (8 x 8 mm class) | 64 mm^2 |
| Q1 SO-8 + D2 SMB + F1 1206 + D3 SOD-123 + R6 | 65 mm^2 |
| U1 + hot loop (C1, C2, C3, C4) + FB + EN divider | 40 mm^2 |
| Cout (2 x 1210) + C7 reserved area beside J2 | 56 mm^2 |
| LED + R5 + 3 test points | 15 mm^2 |
| **Total part area** | **~557 mm^2** |

At the 25-35 % area utilisation a power board with wide copper and terminal
clearances actually achieves, that needs **1600-2200 mm^2**. 50 x 40 = 2000 mm^2 fits;
45 x 35 = 1575 mm^2 does not, with anything left for the GND pour that the thermal
argument depends on. And the board is inside JLC's 100 x 100 mm promo tier either
way, so **shrinking it saves no money at all** - it only costs thermal margin the
design does not have.

Other mechanical facts that bind:

- **Height: 14.07 mm (WJ500V) / 14.10 mm (KF128) against A8's 15 mm cap - 0.90-0.93
  mm of margin**, both read off vendor drawings. That is the tightest mechanical
  number on the board, it is consumed entirely by the terminal, and it does not
  include the wire or any tolerance stack. Nothing else on the board is near it
  (the inductor is 4.2-4.7 mm). **If the 15 mm cap is real and firm, this needs a
  second look before P3 commits to a terminal** - it is noted for H1 as an
  observation, not an open question, because A8 was accepted as a default.
- **Both terminals are through-hole**; every SMT part is top side (A11). The bottom
  side stays clear as a thermal/return plane - encoded as a `placement.keepouts`
  entry with `side: back`.
- **4 x M3 (3.2 mm) holes**, inset 4.0 mm from each corner, i.e. at (4,4), (46,4),
  (46,36), (4,36) relative to the outline. 4.0 mm (not the 3.0 mm that
  `--margin 6` would give) keeps the M3 washer/screw-head keep-clear inside the board
  edge.
- **J1 on the left edge, J2 on the right edge**, wire entry facing outward, so field
  wiring never crosses the board and the power path runs left to right:
  J1 -> F1 -> Q1 -> Cin/U1 -> L1 -> Cout -> J2. **P6 must set the terminal rotation
  from the 3D model, not the silk outline** (LEARNINGS 2026-07-28: the WRL bbox is a
  coincidence trap - fit the below-board pins or render an orthographic side view).

## 6. What `board_init` must be called with (P5)

```
board_init.py --netlist kicad/buck-5v3a.net --name buck-5v3a --out kicad \
    --layers 4 --stackup JLC04162H-7628A \
    --outline 50x40 --margin 8 --mounting-holes 4
```

`--margin 8` exists only to set the mounting-hole inset (`inset = margin/2 = 4.0 mm`)
- the outline is explicit, so margin does nothing else. `--copper-oz` is not passed:
board_init takes 2.0 from the stackup's own `stack[0].copper_oz`, which is also what
`dfm_check.derive_copper_oz` will read back out of the board to pick the
`4layer_2oz` rule class. A `--corner-radius 1` is cosmetic and optional.

## 7. Cost picture for checkpoint 1 (rough - `order_quote` at P10 is the authority)

| Line | qty 5 run | per board |
|---|---|---|
| BOM (qty-1 price tier from the P1 sweeps; U1 $1.01, terminals $0.27/pair, Cout $0.48, everything else < $0.20 each) | ~$13 | **~$2.60** |
| Bare PCB, 4L, 50 x 40 (inside the 100 x 100 promo tier) | $15-25 | $3-5 |
| JLC SMT assembly: $8 setup + $8 stencil + ~10 Extended-part feeders at $3 + joints | ~$47 | ~$9 |
| **Total** | **~$75-85** | **~$15-17** |

Caveats that matter more than the numbers: the repo estimator has **no copper-weight
term** and measured **1.9-3.6x low** on real 4-layer boards, so treat the PCB line as
a lower bound; almost every part here is JLC **Extended** (Basic stock does not cover
3 A-class buck ICs, shielded power inductors or 50 V X7R 1210s), so the feeder fees
dominate at qty 5; and the whole run is NRE-dominated - the marginal board is ~$3.
