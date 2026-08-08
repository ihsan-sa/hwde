# rf-de-20m - stackup, outline, zones, fab class, clearance regime

**AMENDED 2026-08-07 (P2-A).** The stackup, outline, zones and fab class are
**unchanged**. What changed: the declared node voltages (re-solved at the corrected
**R = 4.13 ohm**), the `/tank/RFOUT` current, the heatsink specification
(**HS-1 tightened from <= 1.4 to <= 0.7 C/W** by the real Rds(on) and Coss), and
the cost table (EPC2019 is **out of stock and repriced $2.17 -> $3.93**). See
`blocks.md` s0 and `decisions.md` D11.

---

## 1. Chosen stackup

**`JLC04161H-1080B`** - JLCPCB impedance-controlled 4-layer, 1.6 mm nominal,
**1 oz outer / 0.5 oz inner**, HASL as supplied (**overridden to ENIG at order
time** - s4). **Board class: 4L.**

```
  F.Cu       0.035 mm   1 oz     all components; power loop; both spiral windings; tank pours
  prepreg    0.2444 mm  FR4 1080x3, er 4.05 (ASSUMED)
  In1.Cu     0.0152 mm  0.5 oz   SOLID GND - the power-loop return.  ZONES A + C ONLY
  core       1.065 mm   FR4, er 4.6
  In2.Cu     0.0152 mm  0.5 oz   SOLID GND - second thermal spreader. ZONES A + C ONLY
  prepreg    0.2444 mm  FR4 1080x3, er 4.05 (ASSUMED)
  B.Cu       0.035 mm   1 oz     heatsink land + GND (zone A/C); spiral winding (zone B)
```

`stack_total_mm` 1.6542. Provenance: **read back live from JLC's own
`getImpedanceTemplateSettingList`** on 2026-08-06 (template code
202601040426384154) - every thickness is JLC's number; `epsilon_r` is not.

`available: true`. The two `available: false` entries in `reference/stackups.yaml`
(`JLC04161H-3313`, a template JLC never offered, and `JLC04161H-7628G`, withdrawn
between 2026-07-30 and 2026-08-06) are **refused by name by `board_init` and
`rules_gen`** and are not candidates. **Re-run the live probe before ordering** -
the offering churns, and one of those two sized a real 100 ohm board that turned
out never to have existed.

### 1.1 Why 4 layers, and why this lamination in particular

Layer count is not a density decision on this board - it is set by **one number**.

1. **The L1-L2 dielectric is 0.2444 mm, and that is the whole point.** EPC's
   "optimal" stacked self-cancelling power loop puts the F.Cu loop
   `drain -> C_shunt -> source` directly over an In1.Cu return of the same shape.
   EPC measured **~65% lower loop inductance** than the best conventional layout,
   and quantified the device-level payoff: 1.6 nH -> 0.4 nH cut overshoot from 100%
   to 30% of Vin and gained ~4% efficiency. **On this board that loop inductance is
   the entire margin behind the 1.4x voltage derate** on a 200 V part swinging to
   142.5 V by design. A 2-layer board would put the return 1.53 mm away - 6.3x
   further - and the derate would be spent on ringing.
   *Both* EPC (WP010) and TI (LMG1020DS s10.1, which states 4 layers or more is
   **required**, not recommended) reach this independently.
2. **The same 0.2444 mm serves the gate-drive return.** Do not treat the FET power
   loop and the driver's gate loop as separate stackup asks - they are one physical
   requirement.
3. **Thermal.** In1 + In2 + B.Cu give three copper planes between the FET source
   lands and the heatsink face. `theta_BS = 1.5 C/W` for the pair
   (`power_tree.md` s4.1) assumes that stack.
4. **Not impedance.** The `controlled_impedance` table is used only as a reference
   number, and the `se_50` geometry is **deliberately not built** - s5.
5. **Not density.** ~58 placements on 80 cm^2 would route on two layers. Nothing
   here is about routing channels.

**Copper weight: 1 oz outer as supplied. Do not order 2 oz.** At 20 MHz the skin
depth in copper is **14.6 um**, so 1 oz (35 um) is already ~2.4 skin depths and
2 oz buys only ~15% on the AC resistance that dominates every conductor on this
board. **Width buys Q and low loss roughly linearly; weight does not.** The 2 oz
alternative (`JLC04162H-7628A`) would also double the L1-L2 dielectric to
0.4284 mm and *double the power-loop inductance* - it is strictly worse here.

---

## 2. Board outline

| Item | Value | Source |
|---|---|---|
| Outline | **100.0 x 80.0 mm** | P0 Q3 soft guidance, honoured |
| Thickness | 1.6 mm | stackup |
| Corner radius | 2.0 mm | cosmetic; no mechanical driver |
| Mounting holes | **4 x M3 (3.2 mm)** at corners, `--margin 10` -> 5 mm inset | P0 Q4 |
| Origin for every coordinate in this package | board **top-left**, x right, y down | convention |

P5 recipe:

```
board_init.py --outline 100x80 --corner-radius 2 --mounting-holes 4 --margin 10
```

**`--outline` is SOFT here and must stay soft in spirit.** P0 Q3 deliberately
refused a hard cap so the PCB spiral fallback stayed reachable, and the spirals are
now the primary implementation. 100 x 80 closes on the zone budget in s3 with
little slack. **If P6 cannot fit both spirals at their SPIRAL-1 areas, the correct
response is to grow the board in +x to 110-120 mm, not to shrink a spiral.**
Shrinking a spiral trades board area (a few dollars) for dissipation (watts) and
copper temperature (degrees) - the wrong currency in every direction.

Cost of growing: past 100 mm in either dimension JLC leaves its cheapest 4-layer
tier, so 120 x 80 costs roughly **+$3-6/board at qty 5** rather than the ~$0 that
100 x 80 costs. Cheap insurance, and there is no cost ceiling on this board
(P0 Q2). Recorded so nobody treats the outline as sacred.

### 2.1 Coordinate trap - MANDATORY P5 STEP

**`board_init` does NOT place the outline at (0,0).** In fixed-outline mode the
origin is derived from the packed component bounding box (the existing pd-trigger
board's Edge.Cuts starts at 9.80, 27.51). **Every rect in this package and in
`constraints.json` is board-local. After `board_init`, read
`reports/board_init.json.outline_bbox` and translate every rect by (x0, y0) before
P6 or P7 consumes it.**

Skipping this puts the plane voids, the heatsink land and the spiral keepouts
somewhere else entirely. `planes_gen`'s region-coverage check gives partial cover
for a forgotten translation; `placement.keepouts` has **none**. Do it as an
explicit, recorded P5 step.

---

## 3. Zones and layer assignment

The board is three vertical bands. The full derivation is `blocks.md` s4.4.

| Zone | x (board-local) | F.Cu | In1.Cu | In2.Cu | B.Cu | Heatsink |
|---|---|---|---|---|---|---|
| **A - power / heatsink** | 0 - 48 | parts, power loop, gate loop, bus | **solid GND** | **solid GND** | **GND + heatsink land** | **yes** |
| **B - magnetics** | 48 - 88 | spirals + C_s bank | **none** (SPIRAL-4 bridges only) | **none** (bridges only) | spiral winding only | **NEVER** |
| **C - output** | 88 - 100 | RFOUT pour, C_m bank, J301 | **solid GND** | **solid GND** | **GND** | no |

`constraints.json.planes` declares six entries - GND on In1.Cu, In2.Cu and B.Cu
over `[0,0,48,80]` and again over `[88,0,100,80]`. **Zone B is left unpoured by
construction**, because `planes_gen` supports a pour *region* but **has no void or
keepout support** (verified by reading the script).

### 3.1 The three things `constraints.json` cannot do here

1. **F.Cu and B.Cu copper inside a spiral courtyard is governed by nothing.** After
   L301 and L302 are placed and **locked** at P6, hand-add **KiCad rule areas
   (keepouts) over both courtyards on all four layers**, and verify geometrically
   at P8. No ai-ee check enforces "no other copper here". Put it on the P5/P6
   checklist - this is exactly the class of requirement that silently disappears.
2. **The heatsink is off-board.** HS-1/HS-2/HS-3 in `blocks.md` s4.4 are acceptance
   criteria on a mechanical part nobody in this pipeline builds. They must reach
   whoever specifies the heatsink.
3. **`placement.keepouts` cannot say "only these parts here".** Zone discipline is
   carried by `placement.groups` (which pull the right parts together), by the
   plane regions, and by explicit `place_edit` + `lock` on L301, L302, Q201, Q202,
   U201, J101, J201 and J301 before the annealer runs.

---

## 4. Fab class and process

| Item | Value | Note |
|---|---|---|
| Layers / size / thickness | 4L, 100.0 x 80.0 mm, 1.6 mm | |
| Copper | **1 oz outer, 0.5 oz inner** | as the stackup supplies; do not upgrade |
| **Base material** | **high-Tg FR4, TG155 or better** | **MANDATORY.** Spiral copper runs 100-140 C; JLC's standard FR4 is Tg 130-150 C. An **order-time option**, not a BOM part and **not expressible in `stackups.yaml`** - carry it to P10 explicitly or it will be ordered as standard FR4. |
| **Surface finish** | **ENIG, not the stackup's HASL** | EPC AN009 specifies ENIG for eGaN assembly; HASL's bumpy, uneven finish is wrong under a 2.77 x 0.95 mm solder-bar LGA and wrong under a 0.4 mm-pitch WCSP. ~+$10-20 at qty 5. **Order-time override.** |
| **Via-in-pad** | **epoxy-filled and capped (POFV)** | Needed for the **LMG1020 GND and VDD balls only** (2-4 vias) so the gate/VDD return can be a via-in-pad. Without it the escape adds ~0.3 nH and blows the VDD-loop budget. JLC's POFV is a board-wide process adder, ~+$10-20 at qty 5. |
| Thermal vias under the FETs | **>= 10 x 0.3 mm copper-filled per FET**, in and immediately around the source lands, mask-opened land on B.Cu | Filled, not plated-barrel-only (~2.5x worse). **The EPC2019's own bars are ~0.2 mm wide, so vias go BESIDE the lands, not in them** - see the verify-later item below. |
| Min trace / space | JLC standard (0.0889 mm) | covers the 0.4 mm-pitch WCSP escape; no fine-pitch upcharge |
| Blind / buried vias | none | |
| Outline | plain rectangle + R2.0 corners, no cutouts | |
| Assembly | **JLC PCBA, TOP SIDE ONLY** | one THT part (J101 screw terminal), which JLC PCBA handles as a standard catalog process |

**VERIFY-LATER (P3/P5, blocking the footprint):** the EPC2019's physical package is
**2.77 x 0.95 mm with a 7-bar solder-bar row**, not the "1.35 mm chip-scale LGA"
the brief carried. The bars are far too narrow for in-pad vias, so the >= 10-via
array must sit alongside them. **Take the land pattern and stencil dimensions
verbatim from the EPC2019 datasheet** (published there, solder-mask-defined, in um)
rather than re-deriving from EPC's general LGA guidance, and note that **SMD
(solder-mask-defined), not NSMD, is mandatory** for this land pattern.

**EPC AN009 also specifies, for 200 V-class parts:** >= 12 mil core thickness
between L1-L2 (and mirrored L3-L4) for creepage - the chosen lamination gives
**0.2444 mm = 9.6 mil**, which is **below** that recommendation. Assessment: AN009's
12 mil figure is written for boards where the 200 V appears *between adjacent
layers*. Here In1 immediately under the drain is **GND** and the full 142.5 V does
appear across that 0.2444 mm prepreg. 0.2444 mm of FR4 stands off ~5 kV - the
recommendation is a manufacturing/creepage margin, not a breakdown limit, and
0.2444 mm of laminated prepreg is not a creepage path. **Accepted as-is**, recorded
so a reviewer does not re-open it. There is no thicker JLC 4L/1.6 mm/1 oz
lamination available anyway.

---

## 5. RULING: the 50 ohm output trace

**`reference/stackups.yaml` gives, for this lamination:**

| Profile | Layer | Reference | Geometry |
|---|---|---|---|
| **`se_50`** | **outer (F.Cu)** | nearest inner plane, **h = 0.2444 mm, er 4.05 (assumed)** | **width 0.4332 mm** |
| `diff_90` | outer | nearest inner plane | 0.3718 mm / 0.2444 mm gap |
| `diff_100` | outer | nearest inner plane | 0.3087 mm / 0.2444 mm gap |

**That is the number the requirement asks for. It should not be built.**

`requirements.md` s2 freezes *"the 50 ohm output trace must be controlled-impedance
all the way to the output connector"*. At 20 MHz over the ~15 mm this board needs,
that requirement is **counterproductive**, and the numbers are one-sided:

*The 50 ohm geometry is thermally unacceptable.* `/tank/RFOUT` carries **2.0 A rms
into the load** (and 6.96 A rms on the L302 side of the C_m node). With the AC/DC
resistance factor of 2.5 at 20 MHz, a 0.4332 mm x 1 oz external trace is an
~3.2 A DC-equivalent conductor. IPC-2221's external curve puts that at a **50-75 C
rise** on top of a board already running warm. Even at 2.0 A flat it is ~27 C.

*And the impedance it buys is electrically immaterial.* At 20 MHz in FR4 microstrip
(er_eff ~3.3) a wavelength is **~8.2 m**. A 15 mm run is **lambda/550, i.e. 0.65
degrees.** Modelled as lumped elements, a 15 mm run contributes ~2.5-5 nH of series
inductance (X_L = 0.3-0.6 ohm, **0.6-1.3% of 50 ohm**) and ~3.4 pF of shunt
capacitance (**~2%**) - both **entirely inside the L-match's tuning range**, and
this board's L-match is trimmable copper.

**THE RULING**

> **Route `/tank/RFOUT` as a wide F.Cu pour (>= 3 mm, ideally the full ~6.4 mm the
> tank current wants) over solid In1 GND, held to <= 15 mm from the C_m node into
> the J301 centre pad. Do NOT build the 0.4332 mm `se_50` microstrip.**
>
> `constraints.json` therefore declares `/tank/RFOUT` under **`power`** (6.6 A,
> which sizes it) and **not** under `high_speed` with an `impedance_ohm`.

**Two independent reasons this is the right shape for `constraints.json`, not just
for the copper.** First, `rules_gen` **only solves impedance for differential
pairs** (verified by reading the script: `detect_diff_pairs` pairs `high_speed`
nets by `_P/_N`-style suffix, and `diff_pair_rules` is the only consumer of
`impedance.py`). A lone single-ended `high_speed` entry with `impedance_ohm: 50`
would emit **no width rule at all** - it would look declared and do nothing.
Second, `check_current` on a `power` entry is a real, enforced check.

**If the owner wants the frozen requirement met literally**, the correct
implementation is **not** a thin microstrip but a **grounded coplanar waveguide**:
a 1.5-2.0 mm centre conductor with symmetric F.Cu ground pours either side over
In1, gap hand-solved and **verified against JLC's own impedance calculator before
ordering** (the pipeline's `impedance.py` solves surface microstrip only - it
cannot solve CPWG, and using it here would produce a silently wrong number). That
gets 50 ohm *and* enough copper. Cost: a hand solve, an order-time verification,
and no pipeline check can confirm it. **See `decisions.md` OPEN-2** - this is a
checkpoint-1 question with a recommendation, not something to decide silently.

---

## 6. Clearance and DRC regime

Every pair on this board more than 30 V apart is declared in
`constraints.json.voltages`, from which `rules_gen` emits named `aiee_hv_*`
clearance rules and `check_creepage` audits the routed copper at P8.
`coating: "soldermask"` selects IPC-2221 Table 6-1's B4 row for masked traces and
tented vias, A6 for exposed lands. **Never hand-author HV clearance rules** - emit
them from `voltages`.

| Net | Declared | Why |
|---|---|---|
| `/SW` | **143 V** | drain, 142.5 V pk by design. **Unchanged at P2-A** - it depends only on Vdd, which stays at 40 V |
| **`/tank/TANK_A`** | **180 V** | **156 V pk - the highest node on the board**, 14 V above the drain (was 170 V pk at the frozen R = 4.614). Series-resonant voltage magnification at Q_L 5. Nobody had flagged it; see `blocks.md` s2/B9 |
| `/tank/RFOUT` | **145 V** | 141 V pk = sqrt(200 x 50) x sqrt(2). Set by P_out and the load, so unmoved by the R correction |
| `/tank/TANK_B` | **50 V** | 41 V pk = I x R_opt |
| `+40V` | **51 V** | turn-on ring, not the 40 V nominal |

Element-across differentials go into `voltage_pairs`, where node arithmetic cannot
reach them: **across L_s 203 V pk, across C_s 151 V pk, across L_m 135 V pk.**

`+5V`, `GND` and the gate nets are under 30 V and are not declared.

**Known trap, carried from the lumina runs: `rules_gen` reads `voltages` for
clearance rules, but nothing makes the P7 router honour a clearance the *netclass*
does not carry.** Verify at P8 that `check_creepage` actually ran against the
routed copper and did not simply find nothing to check.

**Turn-to-turn on the spirals is not a creepage problem.** 203 V pk across L_s over
2 turns is ~102 V turn-to-turn against a 1 mm gap - two orders of magnitude of
margin. It is a *voltage across an element*, not a node voltage; do not let it
propagate into a node-clearance rule.

---

## 7. Cost picture for checkpoint 1

Rough part cost from the P1 research prices at qty 5. **`order_quote` does real
numbers at P10** - these are for the go/no-go, not for a purchase order.

| Block | Parts | ~$ |
|---|---|---|
| **2x EPC2019** @ **$3.93** (was $2.17 - **OUT OF STOCK at LCSC, repriced**) | 2 | **7.86** |
| LMG1020YFFR @ $0.36 | 1 | 0.36 |
| LM5017-class buck + inductor + its ~9 passives | 11 | 1.75 |
| 2x SMD edge-launch SMA @ $0.299 | 2 | 0.60 |
| 2-pos screw terminal | 1 | 0.19 |
| 2x 100 uF/63 V SMD polymer + 2x 2.2 uF/100 V | 4 | 0.70 |
| **C_s bank** 9x 56 pF 1 kV C0G 1206 @ $0.052 | 9 | 0.47 |
| **C_m bank** 10x 1206 C0G 1 kV | 10 | 0.52 |
| **C_shunt trim** 4x 33 pF 1 kV C0G 1206 - **3 POPULATED at P2-A**, no longer DNP | 4 | 0.16 |
| RF choke L201 (0.82-1.0 uH, SRF >= 80 MHz, I_sat >= 12 A) | 1-2 | 0.30-1.00 |
| Bus HF bank 4x 10 nF + 2x 1 nF 100 V C0G 0603 | 6 | 0.16 |
| Gate resistors 8x 4.0 R 0603, term 2x 100 R 0805, misc R/C | ~14 | 0.20 |
| **L301 + L302 - etched PCB spirals** | 2 | **0.00** |
| **BOM subtotal** | **~60** | **~$13.2** |
| +25% small-quantity uplift | | **~$16.5** |
| PCB: 4L, 100x80, **TG155**, **ENIG**, **POFV**, qty 5 | | **$5-9/board** |
| PCBA: setup + ~60 placements + ~10 extended-part fees, amortised over 5 | | **$10-14/board** |
| **This board, delivered** | | **~$32-40/board, ~$160-200 for 5** |

**The BOM rose ~$4/board at P2-A**, essentially all of it the EPC2019 repricing
($2.17 -> $3.93 x 2 parts). **The part is currently OUT OF STOCK at LCSC (stock 0);
the owner approved continuing the design and holding the order, and P10
re-verifies** (`decisions.md` OPEN-6). Ten units are needed for a 5-board build.

**Off-board and budgeted separately: heatsink + fan, ~$15-30 per board.**
**HS-1 tightened at P2-A to <= 0.7 C/W** (from 1.4) at the design airflow -
roughly a 31 x 60 mm base with 30-40 mm fins plus a 40-60 mm fan. The real
Rds(on) (36/50 mohm, not the retracted 22/42) and the real Coss cost the
difference. **A passive bolt-on will not do it.**

**The comparison that justifies the second FET still holds, and is now absolute
rather than economic:** a single-FET build reaches **Tj 160 C with a hypothetical
0 C/W heatsink**, i.e. above the 150 C absolute maximum. There is no heatsink to
price against it - the architecture simply does not exist. The second FET buys a
board that works.

There is **no cost ceiling** on this board (P0 Q2: "minimise spend by reducing
scope, never by reducing quality"). The three fab options that cost real money -
TG155, ENIG, POFV - are each buying a specific, named failure mode out of the
design and none should be traded away for price.
