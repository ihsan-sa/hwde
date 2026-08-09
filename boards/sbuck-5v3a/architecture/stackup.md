# sbuck-5v3a - stackup selection

## 1. Choice

**`JLC04161H-1080B`** - 4 layer, 1.6 mm nominal, **1 oz outer / 0.5 oz inner**,
HASL. This is the name `board_init.py` must be given at P5 and it is the
`defaults[4]` entry in `reference/stackups.yaml`.

| | |
|---|---|
| Layer count | **4** (delegate Q18, recorded as a P0 decision - not re-opened) |
| Copper | **1 oz outer (0.035 mm) / 0.5 oz inner (0.0152 mm)** |
| Lamination | F.Cu / 0.2444 mm 1080x3 prepreg / In1.Cu / 1.065 mm core / In2.Cu / 0.2444 mm 1080x3 / B.Cu |
| Stack total | 1.6542 mm |
| Finish | HASL |
| Controlled impedance | **not used** - no high-speed or differential net exists on this board |
| Provenance | `jlc_open_api`, template_code 202601040426384154, live-verified 2026-08-06 |

It is also the **only** 4L / 1.6 mm / 1 oz outer / 0.5 oz inner lamination JLC
returned on 2026-08-06. There is no alternative in this class to weigh against
it, which makes the stackup choice a consequence of the copper-weight decision
(s3) rather than an independent one.

**Re-verify before ordering.** The offering churns: `JLC04161H-3313` never
existed and sized a real 100 ohm board anyway, and `JLC04161H-7628G` was live
on 2026-07-30 and gone by 2026-08-06. Both are carried in `stackups.yaml` as
`available: false` so `board_init` refuses them by name. Re-run the probe at
P5 and again at P9.

## 2. Why 4 layers (confirming, not re-deciding, Q18)

Three independent drivers, any one of which would be enough:

1. **The brief demands an uninterrupted ground plane on the layer directly
   under the switching components.** On 2 layers that plane is B.Cu, 1.53 mm
   away, and it is the same copper the thermal case needs; every return path and
   every bottom-side pour then competes for one layer. Here In1 is 0.2444 mm
   under F.Cu - a 6x closer image plane for the hot loop.
2. **Thermal.** The board *is* the heatsink and the model only works because the
   plane stack makes it near-isothermal: `k*t = 385 * (35 + 15.2 + 15.2 + 35) um
   * 0.83 = 0.0321 W/K`, so `lambda = sqrt(k*t / 2h) = 32 mm`, larger than the
   20-25 mm board half-dimension. Drop to 2 layers and `k*t` falls by a third
   while B.Cu also has to carry return current and routing.
3. **Two solid GND inners give a single low-impedance reference with no splits**,
   which is simultaneously the EMI answer, the thermal answer and the IPC-2152
   answer (s4).

Cost delta at 5 pieces is a few dollars per board. Not a factor.

## 3. Copper weight: 1 oz outer. The vendor reference layouts lose.

**The conflict.** The power architect computed that 2 oz outer copper does not
help thermally. Both vendor reference layouts say otherwise: AP64350's layout
section recommends 2 oz top *and* bottom explicitly ("3.5 A load... heat
dissipation is a major concern") and LMR33630's specifies 2oz/1oz/1oz/2oz. Two
independent vendors pointing the same way is a real signal, not coincidence, and
delegate Q21 authorises the escalation if 1 oz fails.

**Ruling: 1 oz outer. The vendor recommendations lose,** for three reasons in
increasing order of force.

1. **They answer a different question.** A vendor layout section addresses a
   designer dropping the part onto an arbitrary board where the pad-to-plane
   spreading resistance *is* the bottleneck. Here it is not: `R_ba` is set by
   area, `h_conv` and emissivity, and the board is already isothermal at 1 oz
   (`lambda` 32 mm > half-dimension). Doubling the outer copper raises total
   `k*t` by 1.70x and `lambda` to 42 mm - a larger number for a condition that
   was already satisfied. What the vendors are really asking for is copper
   *area* near the part, and this board gives them >= 1500 mm^2 on B.Cu plus two
   solid GND inners, far more than any vendor EVB.
2. **The escalation does not survive contact with the real stackup.** JLC's only
   4L / 1.6 mm 2 oz-outer lamination is `JLC04162H-7628A`, whose L1-L2 prepreg is
   **0.4284 mm - 1.75x the 1080B's 0.2444 mm**. That single change:
   - nearly doubles the thermal-via resistance to In1 (`R_1via` 29.4 -> 51.5 K/W;
     a 16-via array 2.16 -> 3.79 K/W), costing **+1.7 C of junction temperature**;
   - pushes the image plane 75% further from the hot loop, which is the exact
     structure the brief's uninterrupted-plane requirement exists to protect.
   The best case for 2 oz is halving the +6 C local non-uniformity term, i.e.
   ~ +2.5 C of relief. Net: **+0.8 C, inside the +/-30% uncertainty the
   convection/radiation correlations already carry.** It is not a real gain.
3. **Q21's own condition is not met.** The escalation is authorised "ONLY if
   IPC-2152 sizing or the Tj calculation fails at 1 oz". Neither fails:
   IPC-2152 at dT = 10 C needs 1.52 / 2.31 / 2.06 mm for VIN / SW / +5V, all
   routable on a 50 x 40 mm straight-through floorplan, and worst-case
   `Tj = 97.9 C` against a 105 C limit.

Secondary costs avoided: 2 oz outer carries a JLC price adder, a coarser
minimum trace/space than the standard class this design is targeting (Q27), and
worse etch tolerance on the 0.25 mm signal traces.

**If a later phase discovers this was wrong** - `check_thermal` failing, or the
IPC widths refusing to route - the escape is `JLC04162H-7628A` plus a re-run of
the via ladder at 0.4284 mm, and it must be recorded as a decision, not drifted
into.

## 4. Inner layers: In1 AND In2 are both solid GND. The rule survives.

The architect's binding rule was "no power net may use an inner layer, because
0.5 oz inner copper needs 3.0-4.6 mm widths". Checked against the real
lamination: **JLC's inner copper on this stackup is 0.0152 mm, thinner than the
nominal 0.5 oz (0.0175 mm) the rule was computed against**, so the required
inner widths are ~15% *worse* than stated:

| Net | current | inner width at 0.0152 mm, dT = 10 C | % of board width |
|---|---|---|---|
| `+VIN` | 2.6 A | 3.50 mm | 7% |
| `+5V` | 3.3 A | 4.73 mm | 9% |
| `/SW` | 3.6 A | 5.32 mm | 11% |

**The rule survives with room to spare.** In1.Cu and In2.Cu are both **solid
GND**, declared explicitly in `constraints.json.planes` because the pipeline
default for a 4-layer board is In1 GND + In2 *dominant power net*, which here
would pour In2 as `+5V` - an unroutable power plane that also halves the
thermal spreading and splits the reference. That one `planes` entry is the most
load-bearing line in the whole constraint file.

B.Cu is also declared GND (the pipeline does not pour B.Cu by default at 4
layers) because it is the second radiating face and carries half the cooling.
F.Cu is declared GND too, for the thermal island around U1's pad.

## 5. Consequences for other phases

- **P5 `board_init`**: `--stackup JLC04161H-1080B`, outline **50.0 x 40.0 mm
  HARD**, 4 layers, 1.6 mm. 4x 3.2 mm NPTH at the corners inset 3.5 mm.
- **P5 `rules_gen`**: JLC standard/economic class (confirm the live capability
  numbers, do not design to remembered minimums). No impedance rules -
  `diff_pairs` is an explicit empty list and no `impedance_ohm` is declared
  anywhere, so the 1080B `controlled_impedance` table is unused by design.
- **P7 `planes_gen`**: four GND pours (F.Cu, In1, In2, B.Cu), no regions.
  `planes_gen` has **no void support**, so the 6.5 mm mask/copper keepout around
  each M3 hole must be hand-added as a KiCad rule area after the pours and
  verified geometrically at P8.
- **P9 fab**: 0.3 mm drill is JLC standard-class minimum. Tent the U1 via array
  with soldermask on the **bottom** side only. No filled-and-capped via-in-pad,
  no controlled impedance, no ENIG required.
