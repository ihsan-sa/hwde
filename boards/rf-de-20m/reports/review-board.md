# rf-de-20m P8 - adversarial board review

Authored 2026-08-08 by the P8 `verify-reviewer` (fresh context, no routing or
fixing history inherited). Inputs: `kicad/rf-de-20m.kicad_pcb` as committed,
`reports/gate-verify.json` (31 err / 159 warn), `reports/gate-drc_routed.json`
(55, 0 unconnected), `reports/route-notes.md`, `reports/spiral-design.md`,
`reports/verify-waivers.md`, `architecture/*`, `parts/*`, and renders re-made
from the CURRENT board (`reports/renders/rf-de-20m_{top,bottom,iso}.png` -
the pre-existing set was 7 h older than the P8 copper edits).

Everything below was measured on the actual board geometry with
`lib/geom.py`, or re-derived from the datasheets. Scripts are quoted so the
numbers can be reproduced.

**Result: 5 errors, 3 warnings.** All 8 existing waiver classes are
recommended for approval, **six of them unconditionally and two with
conditions** (s3). The errors are things no check on this board can see.

---

## 1. The audit you asked for first: is a real creepage violation hiding?

**No. Verified item-by-item, and the waiver's claim is exactly right.**

`check_creepage` was re-run standalone and its full per-pair summary read (not
just the failing list). Across **all 5 declared HV nets, all 3 `voltage_pairs`,
all 4 copper layers and every other net on the board, only THREE (net, net,
layer) combinations produce a single item pair closer than the largest
applicable IPC-2221 requirement**:

| primary | other | layer | min gap | raw pairs under req |
|---|---|---|---|---|
| `/SW` | `/stage/GATE_Q1` | F.Cu | 0.350 mm | 3 |
| `/SW` | `/stage/GATE_Q2` | F.Cu | 0.350 mm | 4 |
| `/SW` | `GND` | F.Cu | 0.350 mm | 40 |

Every other pair - including `/tank/TANK_A` at 180 V against all 16 other nets,
`/tank/RFOUT` at 145 V, `+40V` at 51 V, and the three `voltage_pairs`
(`/SW`-`TANK_A` at **203 V**, `TANK_A`-`TANK_B` 151 V, `TANK_B`-`RFOUT` 135 V)
- reports `min_gap_mm: null`, i.e. **no copper anywhere on the board is even
within the requirement distance**. The 47 raw hits dedupe (0.1 mm spatial) to
the 21 errors + 3 warnings reported.

Then, per finding, the two colliding items were dumped by TYPE:

- **21 of 21 involve only EPC2019 pads and the 0.25/0.45 mm die-escape tracks.**
  Not one involves a **zone fill**. The composition is 8 pad-to-track,
  11 track-to-track (drain column vs source/gate escape) and 2 pad-to-track at
  0.389/0.391 mm.
- **All 21 gap midpoints lie strictly inside the two die pad bounding boxes**
  (Q201 `[36.810, 61.885, 39.460, 62.585]`, Q202 `[36.810, 66.085, 39.460,
  66.785]`), split **Q201 x10 / Q202 x11** - the split `verify-waivers.md`
  claims.
- The 0.350 mm figure is the land pattern's own arithmetic: 0.600 mm column
  pitch minus the 0.250 mm bar width. 0.375/0.389/0.391 are the round-bump
  diagonals.

**And the pour is clean, measured directly.** The `/SW` zone fill's minimum
distance to *any* GND copper on F.Cu is **0.8004 mm** (to pads 0.8005, to
tracks 0.8005, to GND zone fill 0.8004) - the `aiee_hv_143v_SW` rule honoured
to 0.4 um. There is no board-copper creepage violation hiding in the set.

**Verdict: waiver entry 1 (21 `check_creepage`) and the matching
`drc_routed` clearance class (48) are sound. Approve.** The caveat
`verify-waivers.md` already carries - 10 of the 21 have empty `refs`, so the
subset matcher cannot exclude a future empty-refs finding elsewhere - is the
correct compensating control and should be kept: **if the count ever exceeds
21, read the delta, do not waive it.**

---

## 2. The five errors

### E1 - the thermal budget rests on theta_BS = 1.5 C/W for the pair, and that number is optimistic by 2.5-4x. At my estimate the EPC2019 exceeds its 150 C absolute maximum. (error)

This is the worst thing on the board and it is the one thing
`verify-waivers.md` entry 6 asserts rather than measures.

**The waiver's premise is correct.** I read `check_thermal.theta_ja()`:
`tfloor + (t0 - tfloor)*exp(-A/tau)` with `A_SAT_MM2 = 645.0`. Copper area is
its only input; there is no heatsink, TIM or airflow term. The "645 mm2" in the
message is the model's **saturation cap**, not a measurement of this board's
island. So yes - the check is heatsink-blind and its 288 C is meaningless here.

**The substitute numbers are what fail.** The claimed path is
`theta_JB 3.75 + theta_BS 1.5 + theta_HS 0.7 = 5.95 C/W` for the pair.
`theta_JB` is right (EPC2019 `RthJB_typ` 7.5 C/W per die, halved for two in
parallel - `parts/C2836675.json`). `theta_HS <= 0.7` is a hard, measured,
external requirement (HS-1) and is out of my scope. **`theta_BS` - F.Cu under
the dies through the board to B.Cu - is assumed, and the board's own stackup
says it cannot be 1.5.**

Stackup read off the board: F.Cu 35 um / **0.2444 mm** / In1 **15.2 um** /
**1.065 mm** / In2 15.2 um / 0.2444 mm / B.Cu 35 um. The 1.065 mm core between
two **half-ounce** planes is the dominant term and it is crossed by only
**18 vias** (9 per FET, measured - see E5).

Two bounding estimates, FR4 through-plane k = 0.3-0.4 W/mK, copper 400 W/mK:

| model | R(F.Cu->B.Cu), pair |
|---|---|
| **optimistic** - heat magically spread over the full 645 mm2 island at every layer, k = 0.4, in parallel with 18 barrel vias (12.4 C/W incl. lateral access) | **4.05 C/W** |
| **realistic** - exponential spreading length per layer (`lambda = sqrt(k_cu.t_cu.h/k_fr4)` = 3.38 / 4.65 / 2.23 mm), effective areas 110 / 392 / 589 mm2, k = 0.3 | **7.3 C/W** |

Even the optimistic bound is **2.7x** the assumed 1.5 C/W. Feeding it back:

| theta_BS | theta_JA(pair) | Tj at 11.25 W nom | Tj at 14.6 W max-corner |
|---|---|---|---|
| 1.5 (assumed) | 5.95 | ~123 C (as claimed) | ~142 C |
| **4.0 (optimistic)** | 8.45 | **~151 C** | **~180 C** |
| **7.3 (realistic)** | 11.75 | **~188 C** | **~228 C** |

(Ambient 40 C, and the +9 C the waiver's own 6R8 gate-loss adder carries over
the `constraints.json` baseline. EPC2019 `TJ_range` absolute maximum is
**150 C**.)

`verify-waivers.md` s3 already names this as **OPEN-10** - "theta_BS = 1.5 C/W
for the pair is assumed, not simulated, and carries 17 C of the 85 C junction
budget". That is the right instinct but the wrong magnitude: it carries far
more than 17 C, and it is the term that decides whether this board survives
its own design point. **The `check_thermal` waiver must not be approved as
"waivable, real numbers are fine" - it should be approved as "the gate is
blind, AND the real number is unresolved and blocking."**

Levers, cheapest first, all of which move this materially:
1. **Order 1 oz inner layers** instead of 0.5 oz - halves the In1/In2 lateral
   spreading resistance, an order-time option, no layout change.
2. **Build the missing B.Cu mask-opened land** (E3) and get the vias fixed (E5).
3. **Derate the bus to 36 V / 162 W** - already costed by the architecture at
   **-14 C**.
4. **Revert R205/R206 to 4R7** - **-4 C**, and W1 below shows the threat that
   bought 6R8 was over-estimated ~5x.
5. Close OPEN-10 with a 3-D thermal solve or a first-article measurement
   **before ordering**, not after.

### E2 - the C_m bank ships 8.8 % high because the mandated RFOUT pour capacitance was never folded in. The as-built match is WORSE than the 560 pF bank P4 explicitly rejected. (error)

P7 measured the pours' added capacitance to GND (`route-notes.md` s7) and
handed the populate decision to P8. `verify-waivers.md` s16 records the
outcome: *"the s7 populate recommendation is untouched."* It was never taken.

**I re-derived the number independently** rather than trusting it: the
`/tank/RFOUT` F.Cu pour is **371.5 mm2**, of which **84.5 % (313.9 mm2)** sits
over In1 GND at 0.2444 mm. Parallel plate at the board's declared
`epsilon_r = 4.05` gives **46.1 pF** (48.9 pF at 4.3). P7's figure was 46.06 pF.
Confirmed.

That 46.1 pF is a lumped shunt at the RFOUT node at 20 MHz - **directly in
parallel with C_m and the 50 ohm load**. So:

| C_m | Z presented to the tank | series X/R | P_out at 40 V |
|---|---|---|---|
| 484 pF physical + 46 stray = **530** (the ideal) | 4.13 + j0.00 | 1.153 | 200 W |
| **531 pF populated, stray ignored** (the BOM's own solve) | 4.12 + j0.07 | 1.19 | ~200 W |
| 560 pF - **rejected at P4 review W1** | 3.74 + j0.67 | 1.47 | ~221 W |
| **531 + 46.1 = 577 pF, AS SHIPPED** | **3.53 + j1.01** | **1.65** | **~233 W** |

(`omega L_s` 20.607 - `1/omega C_s` 15.790 + X_load, R_load from
`50 || 1/jwC_m` + `jwL_m`; reproduces both published anchors exactly.)

**P4 review W1 added a whole new BOM line (`C541492`, 27 pF) for the sole
purpose of getting the bank off 560 pF**, on the argument that 221 W *"inflated
I_dc, FET conduction loss and the 11.25 W / Tj 114 C two-FET thermal budget the
whole paralleling decision rests on"* (`parts/parts.json`, C541492 role note).
The board as it stands lands **past** that rejected point: ~233 W, +17 % I_dc,
**+37 % FET conduction loss**, on the board of E1 above.

**Fix is one BOM line and it is already specified:** depopulate one 56 pF site
from C_m (C310-C318 -> 8 populated), keep C319. 8x56 + 27 = 475 pF + 46.1 =
**521 pF, -1.8 % on the ideal** - exactly P7's recommendation. Domain `parts`.

Two smaller siblings, folded in for completeness and NOT separately reported:
the `/tank/TANK_A` pour adds 13.4 pF from the mid-node to GND (shunts ~2.7 % of
the tank current - reactive, so it detunes rather than dissipates), and the
two spirals' mutual at the as-placed 46.8 mm centres is about **-1.1 nH each,
-0.8 % on the 274 nH series tank** (`spiral-design.md` s6, which asks P8 to
"fold the number in rather than ignore it" - also not done).

### E3 - there is no mask-opened heatsink land on B.Cu. There is no solder-mask aperture on B.Cu anywhere. (error)

`architecture/stackup.md` ("Thermal vias under the FETs") and
`constraints.json:thermal[Q201]` both require *"mask-opened land on B.Cu"*.

Measured on the board: the **only** layer sets that reach a mask layer are
`"F.Cu" "F.Mask" "F.Paste"` (161 component pads) and `"*.Cu" "*.Mask"`
(6 items = J101's two THT pins + the four NPTH mounting holes). **Zero B.Cu-only
mask apertures exist.** `reports/renders/rf-de-20m_bottom.png` confirms it
visually - the whole bottom face is green, including the entire HS-2 rect
`[5, 10, 36, 70]` board-local.

So the sink presently bolts onto **solder mask**, which nobody decided. This is
a fork the owner has to rule, not something to silently accept:

- **Keep the mask** - then say so, and add the mask term (~25 um at
  k ~0.25 W/mK; 0.05 C/W if the contact really is 1860 mm2, **0.5 C/W** if the
  effective spreading area is only ~200 mm2) to the E1 budget explicitly.
- **Open it** - then the **HASL -> ENIG override already in `stackup.md` becomes
  load-bearing, not a nicety**: HASL on a 31 x 60 mm bare-copper land leaves
  5-25 um of solder relief and destroys the flatness the whole thermal case
  assumes.

Either way, this is an unimplemented, explicitly-stated architecture
requirement on the path that carries most of the junction budget.

### E4 - nothing on this board can clamp the heatsink over the FETs. (error)

HS-1 requires **theta_HS <= 0.7 C/W measured, in forced air, over a ~31 x 60 mm
base**, and E1 shows the interface resistance is where this design's margin
lives. The board provides no way to make that interface.

- Mounting holes are `4x M3 (3.2 mm) at corners`, board-local (3,3), (117,3),
  (117,77), (3,77) - the P0 Q4 default, chosen before the heatsink existed.
- **H2 and H3 are at x = 117.** HS-2 forbids the sink past x = 40 mm, so they
  cannot hold it.
- That leaves **H1 and H4 only, both at x = 3, collinear on the west edge** -
  two bolts on one line, 28-30 mm away in x from the dies at (31.5, 22.9) and
  (31.5, 27.1). A base clamped on one edge cannot control contact pressure at
  the far corner of a 31 x 60 mm face, and pressure is what sets the TIM
  bondline.
- There are **no holes inside the HS-2 rect** and nothing in `blocks.md`,
  `stackup.md` or `requirements.md` specifies a fastening scheme at all -
  "fastener" appears once, in SPIRAL-6, only as a thing to keep away.

I checked that adding holes is geometrically legal: with the sink confined to
`x <= 40`, SPIRAL-6 (no metal within 15 mm of a spiral's outer copper edge) is
satisfied with 19.4 mm to spare, and the existing corner holes are 18.8 mm and
30.8 mm clear of L302/L301. Recommendation: **2-4 M3 NPTH holes inside or on
the boundary of `[5, 10, 36, 70]`**, placed to miss the power loop and the
In1/In2 planes' critical area, or an explicit clamp-bar/spring-clip scheme
recorded as a mechanical deliverable. Owner decision at H4.

### E5 - 9 thermal vias per FET against a required >= 10, none nearer than 1.1 mm to a source land, and "copper-filled" is not a JLC process. (error)

Measured from each die centroid:

| | vias <= 2.27 mm | vias <= 4.0 mm | nearest |
|---|---|---|---|
| Q201 | 3 | **9** | 1.581 mm |
| Q202 | 3 | **9** | 1.598 mm |

The `check_thermal` `thermal_vias` warning's triage in `verify-waivers.md` s3
is **arithmetically correct** - the check's window really is 2.27 mm and the
real count really is 9 - but it then argues 9-vs-10 is worth "<0.1 C". Under
E1's numbers the via array is not a "parallel helper worth a few percent": with
the 1.065 mm core in the bulk path, **18 barrel vias at ~187 C/W each carry
roughly half the total heat flow.** Two things follow:

1. `blocks.md` s4.1 and `stackup.md` require **">= 10 x 0.3 mm COPPER-FILLED
   vias per FET, in and immediately around the source lands"**. The board has 9,
   and the nearest is 1.58 mm from the centroid (~1.1 mm from the nearest source
   pad) because `aiee_hv_143v_SW` at 0.8 mm caps the landing area. Neither the
   count nor the "immediately around" is met.
2. **JLC does not sell copper-filled vias.** The order-time option in
   `stackup.md` is **POFV - epoxy filled and capped** (specified there for the
   LMG1020 balls). Resin fill is not copper: the "filled, not plated-barrel-only
   (~2.5x worse)" factor the thermal budget assumes **is not purchasable on this
   vendor**, and no one has said so. Carry to P10 as a hard constraint on the
   thermal case, not as a nice-to-have.

Note also that the LMG1020 via-in-pad that POFV was requested for **was never
built** - the nearest GND via to U201 is at (30.777, 63.315), 0.3 mm outside the
ball array, not in a pad. That is consistent with, and part of the cause of, the
`check_decoupling` loop warnings (s3).

---

## 3. Warnings

### W1 - common-source inductance was escalated from P7 to P8 and was never closed; my estimate says it is survivable, and that the 4R7 -> 6R8 change was bought against a ~5x over-estimate (warning)

`route-notes.md` s14 raises it explicitly - *"This deserves a P8 SIM item - it
was never modelled by the architecture"* - and `verify-waivers.md` does not
mention it anywhere. Closing it here.

The source escapes were measured (all 0.25 mm wide, F.Cu, over In1 at
0.2444 mm, `mu0.h/w` = 1.23 nH/mm):

| pad | escape | L |
|---|---|---|
| 2 (gate-return star point) | 0.400 mm west | 0.49 nH |
| 6 | 0.450 mm east | 0.55 nH |
| 7 | 0.450 mm east | 0.55 nH |
| 4 | 1.200 mm outward | 1.47 nH |

The die's internal source metal ties all four, and **all four land on the same
F.Cu GND island** (one 311.7 mm2 island that also carries U201's ground and
C203/C204's ground - verified). So the inductance common to the gate loop and
the power loop is the **parallel combination, ~0.157 nH**, not the 0.768 nH
single escape P7 used. That changes the answer by 5x:

- turn-off, per FET: `I_off ~5 A / t_f ~2.1 ns` -> `di/dt 2.4 A/ns` ->
  **+0.38 V** on VGS (worst case at P7's 8 A/ns pair figure: **+0.63 V**);
- Miller: `Crss 0.7-1.0 pF x dV/dt 24.8 V/ns` = 17-25 mA into ~8 ohm ->
  **+0.14-0.20 V**;
- total **+0.5 to +0.8 V** against `VGSth_min` **0.8 V** (typ 1.4 V).

**Not a destruct path, but only ~1.3x margin at the datasheet minimum**, and it
is the mechanism a second-order RLC model cannot contain. It should be a named
bring-up measurement (VGS at the die during the turn-off edge), not an
assumption. There is also a layout answer if it ever bites: pad 2's escape is
currently merged into the shared GND pour 0.4 mm from the die, i.e. **there is
no Kelvin source** - routing pad 2 separately to U201's ground would remove the
term entirely, at the cost of a re-place.

**Consequence for R205/R206.** P7 chose 6R8 over 4R7 partly on *"a
`L_common.di/dt` term of the order of volts"*. At 0.157 nH it is 0.4-0.6 V, not
volts. On the published numbers 4R7 already passes both rails (-0.85 V against
-4 V; +5.005 V against +6 V). **Reverting to 4R7 recovers ~4 C of the E1 budget
for no new risk** - worth taking if E1 stays tight. This is a recommendation,
not a defect; the 6R8 decision was ruled twice and is the owner's.

### W2 - C_shunt ships at 455 pF, 1.4 % above the top of the design's own 403-449 pF band (warning)

Same root cause as E2 and the same abandoned P7 handoff. `stage.py`'s recorded
deviation solves `316 (pair Coss) + 112 (2 x 56 pF) = 428 pF`, "the MIDDLE of
the 403-449 pF requirement". It predates P7's measurement of **+27.4 pF** of
`/SW` pour capacitance to In1. As shipped: **455.4 pF**, above the band, and
13 % above the ideal-choke value.

Much less serious than E2, because the trim is real and downward: depopulating
C204 gives 316 + 56 + 27.4 = **399 pF**. **Ship it as a bring-up instruction**
("if ZVS lands late, pull C204 first"), or take P7's ~60 pF recommendation now.
Domain `parts`.

### W3 - no fiducials anywhere on the board (warning)

`grep -i fiducial` over the .kicad_pcb returns nothing; the renders confirm it.
This board carries a **0.4 mm-pitch WCSP** (U201, 1.0 x 0.6 mm ball array) and
**two bare passivated die** whose lands are 0.23 mm solder-mask-defined
openings with 0.25 mm bumps - the three finest-pitch things a JLC PCBA line
will see on this order. JLC will use panel fiducials, but local fiducials are
the standard mitigation below 0.5 mm pitch and cost nothing. Recommend
**3 x 1 mm copper / 2 mm mask fiducials** on F.Cu, in the empty area around
board-local (10, 10) / (110, 10) / (10, 70), all outside the HS-2 rect and
>= 15 mm from either spiral. Domain `fab`.

---

## 4. Verdicts on the rest of the machine output

Every residual class, with a verdict. Nothing here needs re-work.

| class | count | verdict |
|---|---|---|
| `check_creepage` 21 err + 3 warn | 24 | **Waiver sound - independently verified, s1.** Approve, keep the "count is fixed at 21" control. |
| `drc_routed` clearance, Q20x | 48 | Same geometry, same evidence. **Approve.** |
| `check_current` `undersized_track` `/SW` | 3 | **Waiver sound, and the consequence is benign - I measured it.** The 0.25 mm drain escapes are only ~1.0 mm long: the `/SW` **pour reaches x = 37.42 into the inter-die gap and is 9.58 mm wide continuous from y 63.4 to 65.0**, so the constricted section is 2 x 0.25 mm x ~1.0 mm per FET, 1.31 mOhm, ~55 mW, and a both-ends-clamped fin gives **dT ~2 C** (`P.L/(8.k.A)`). IPC-2152 does not apply to a 1 mm neck. Approve. |
| `check_current` `undersized_track` `/tank/RFOUT` | 1 | Geometrically unmeetable (9.106 mm corridor, 0.8 mm HV each side). **Approve.** |
| `check_current` `pour_neckdown` `+40V` | 1 | Per-zone erosion artefact at 3 of 30 vias; the P8 resistive-sheet solve is the better evidence. **Approve.** |
| `check_return_path` `/SW` | 1 | **Waiver sound - re-measured independently.** `/SW` pour 191.30 mm2, of which **183.90 mm2 = 96.13 % over continuous In1 GND** (matches the claim to 2 dp), and the whole loop sits on **one** In1 island (In1 has 3 islands - zone A 3931 mm2, zone C 1637 mm2, a 0.3 mm2 sliver - and the drain node, C_shunt, U201 and the gate legs are all on zone A). GATE_Q1/GATE_Q2/GATE_ON/GATE_OFF are **100.0 %** imaged; DRIVE 96.9 %. The deficit is the L301 land at the zone-B boundary, exactly as argued. **Approve.** |
| `check_thermal` Q201/Q202 | 2 | **Approve the waiver on its premise (the check is heatsink-blind - confirmed in source), but NOT on its numbers.** See E1. |
| `check_thermal` L301/L302 | 2 | **Approve.** The winding is a pad, so the check measures the tank pour, not the conductor; `spiral-design.md` s4 is authoritative and its 2.99 / 2.48 mW.mm-2 against SPIRAL-1's 7 is 2.3x clear. Independently sane: `P = 200.Q_L/Q_ind` reproduces 2.58 / 2.05 W. |
| `check_current` 119 `insufficient_transition_vias` + 13 `pour_neckdown` + 8 `undersized_track`, all derived-GND | 140 | Synthesised return-net entry at the largest rail's 7.0 A. Documented labelled worst case. **Waive.** |
| `check_decoupling` 4 distance + 2 loop (C201 6.1 nH, C202 3.1 nH vs 0.3 nH) | 6 | **Real, correctly attributed to the P6 backward edge, and low-consequence HERE - which the waiver does not say and should.** I traced C202's link: 2.49 mm of 0.2 mm track, no vias, ~3.8 nH by `mu0.h/w`, so the estimator is right. But the VDD loop is only in the **turn-ON** path (turn-off sinks through OUTL to GND), and Class E turn-on is ZVS - the drain is already at 0 V, so a ~2.3 ns edge (zeta 0.85 at L 5.55 nH, R 9 ohm, C_GS 199 pF) costs almost nothing. **Waive, with that reason recorded.** |
| `check_creepage` 3 warnings | 3 | Pad-to-pad inside one EPC2019 land pattern; the check labels them itself. **Waive.** |
| `check_thermal` `thermal_vias` | 2 | Count triage correct; conclusion wrong. **See E5.** |
| `check_silk` `silk_misattributed` | 6 | Real, unfixable for R203 (0 legal positions found by the P8 grid search), and JLC places from the CPL. **Waive.** |
| `check_pdn` `pdn_no_bulk` `+40V` | 1 | Sidecar scope artefact; C101/C102 are the bulk. **Waive.** |
| `verify_all` `constraints_drift` | 1 | Records question. **Waive, and take the P8 recommendation to retire `architecture/constraints.json`** - a second copy in a different coordinate frame is how the P6 bug happened. |
| `padstack` x2, `copper_sliver` x1 | 3 | Deliberate inner-only bridge pad; unlocatable sliver. **Waive.** |

**No check was SKIPPED.** All 8 `verify_all` members ran (`by_check` in
`gate-verify.json` lists every one, `check_diffpair` legitimately 0).

**But a different hole exists, and no gate can see it: none of SIM-1..SIM-6 has
ever been run.** There is no `kicad/sims/`, no sim report, nothing in
`state.json` (`open_issues: []`, `gates: {}`, phase still `P7`).
`decisions.md` declares **SIM-4 `tank_match` at ERROR severity** and calls it
*"the C_s arbiter"* (OPEN-12); SIM-1/SIM-2 are the arbiters of the 403-449 pF
C_shunt band. `verify_all` has no `sim_run` member, so a board can reach a green
verify gate with every declared simulation gate unexecuted. **E2 and W2 are
exactly the questions SIM-4 and SIM-2 exist to answer.** Recommend the owner
treat "SIM-4 unrun" as blocking alongside E1/E2 at checkpoint 4.

---

## 5. Things I checked that are FINE (so nobody re-checks them)

- **Tank capacitor family and rating.** `CC1206JKNPOCBN560` / `CC1206JKNPOCBN270`
  - **1 kV C0G (NP0), 1206, no X7R anywhere in the tank** (X7R appears only on
  the buck rails and the driver VDD, where it belongs). 1 kV against the 151 V
  pk across the C_s bank is 6.6x; against TANK_A's 180 V node, 5.5x.
- **Tank current sharing.** The banks are parallel arrays of identical parts, so
  sharing follows capacitance: 0.77 A rms per 56 pF part in C_s, 0.70 A in C_m,
  0.34 A in the 27 pF. The C_s column is 24 mm long, but its series inductance
  (~0.7 nH, j0.09 ohm) is 0.06 % of each cap's 142 ohm - **sharing is not
  degraded by the column geometry.** Bank ESR loss is ~1.0-1.1 W each at C0G
  Q ~700, which is real and is not itemised in `power_tree.md`; it is inside the
  27-39 W envelope, so noted not reported.
- **Gate-leg symmetry.** GATE_Q1 and GATE_Q2 are **identical to the micron**:
  three segments, 1.000 + 0.989 + 1.451 = 3.440 mm each, widths 0.400 / 1.000 /
  1.000, mirrored about y = 64.110 - which is exactly the midpoint of the two
  **gate pads** (62.010, 66.210), so the mirror lands correctly despite the two
  dies being translated rather than mirrored. Both legs are **100 % over In1
  GND**. The die-local return geometry is identical (pad 2 at +0.450 mm from
  pad 1 on both, 0.400 mm west escape on both). The +/-0.1 nH matching spec is
  met by construction.
- **The drain escape** - see s4; measured, ~2 C, benign.
- **The `/SW` power loop.** One 263 mm2 F.Cu island, 96.13 % imaged on In1, the
  C_shunt bank and L202.1 100 % imaged, In1 unbroken beneath the whole loop.
  The C203/C204-populated / C205/C206-DNP asymmetry costs Q202 about **4 mm of
  extra travel in a 9.58 mm-wide pour = ~0.13 nH** - immaterial, because the
  stacked-loop architecture is doing its job.
- **Spiral encoding.** All spiral pads are copper-only (`"F.Cu"`, `"B.Cu"`,
  `"In1.Cu" "In2.Cu"`, and 84 `"*.Cu"` plated holes) - **no F.Mask and no
  F.Paste anywhere on either spiral.** The windings are fully mask-covered and
  no stencil aperture will ever be cut over them. This was the failure mode I
  went looking for; it is not present.
- **B.Cu spiral vs the sink.** SPIRAL-6 holds: the heatsink land ends at
  x = 36 board-local and L301's outer copper starts at 55.45 - 19.4 mm clear.
  The corner mounting holes are 18.8 mm (H3/L302) and 30.8 mm (H2/L301) clear.
- **HS-3.** J101 is the only THT part, at board-local x = 3.7, outside the
  `[5, 10, 36, 70]` rect. Its two `"*.Cu" "*.Mask"` pads are the only B.Cu
  copper the sink could touch, and they are clear.
- **Via tenting.** No pad or via on the board declares a B.Mask aperture, so
  the six non-GND vias inside the heatsink land (2 x `+5V`, 2 x `+5V_DRV`,
  2 x `/stage/DRIVE`) are tented by construction. The P7/P8 FAB NOTE
  ("do not enable via-tenting-off at plot time") remains the right control -
  carry it to P9.
- **EPC2019 land pattern.** Copper = bump size, mask -0.01 mm/side giving the
  datasheet's 0.23 / 0.23 x 0.68 mm openings, paste the same. Pad-4 escapes run
  **away** from the inter-die gap (north from Q201, south from Q202), which is
  why the gap is clean. A pin-1 dot exists on F.SilkS at (-1.40, -0.63).
- **LMG1020 input abs-max** with a bench generator - already found and fixed at
  P4 (review E3). Not re-reported.
- **Minor, prose only:** the EPC2019 courtyard is `2.76 x 0.94 mm` - **exactly
  the die envelope, zero IPC-7351 excess.** Nothing collides today (nearest
  neighbour C203 is 1.3 mm away), but any future re-place gets no warning.
  Also, the round 0.23 mm pads' stencil area ratio is 0.58 at 0.1 mm foil,
  under the usual 0.66 - acceptable **only** because the EPC2019 arrives with
  its own solder bars and the paste is largely a flux carrier. Worth knowing at
  first article, not worth a finding.

---

## 6. Reproduce

    .venv/Scripts/python .claude/skills/ai-ee/scripts/check_creepage.py \
        --pcb boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb \
        --constraints boards/rf-de-20m/kicad/constraints.json --out creep.json
    # then read checked[].pairs[].min_gap_mm - only 3 pairs are non-null

    .venv/Scripts/python .claude/skills/ai-ee/scripts/render.py \
        boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb --views top,bottom,iso \
        --w 2400 --out-dir boards/rf-de-20m/reports/renders

Geometry measurements (pad bboxes, zone-fill distances, the inter-die pour
probe, In1/In2 island split, the RFOUT-over-In1 area) were made with
`.claude/skills/ai-ee/scripts/lib/geom.py` `load_board()` +
`net_copper(net, layer)` / `zones_of()` / `pads_of()`; the exact probes are
quoted inline above.
