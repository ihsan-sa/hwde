# P8 board review - sbuck-5v3a (fresh context, adversarial)

Reviewer did not place, route or fix this board. Every geometric number below was
re-measured from `kicad/sbuck-5v3a.kicad_pcb` with pcbnew + shapely, not read from a
prior phase's report. Renders regenerated at 2400 px: `reports/renders/sbuck-5v3a_{top,bottom,iso}.png`.

**Gate: 2 errors, 12 warnings. Both existing waiver groups upheld (9 findings), one with
a corrected justification. Two new items recommended for documented-deviation status
(W1 `/SW` length, W12 mounting-hole keepout).**

Independent re-runs (my own, not inherited):
- `verify_all` reproduces the gate exactly: 28 total, 9 error (all waived), 19 warning.
  Nothing was SKIPPED for missing inputs.
- `kc.py drc --parity --all-track-errors`: **0 violations, 0 unconnected**. Confirmed.
- `check_irdrop` / `check_pdn_z` / `check_thermal` re-read; arithmetic re-derived below.

---

## ERRORS

### E1. D2's cathode marker `K` is printed at the anode end - `F.SilkS`, `(41.720, 59.125)`

The board-level `gr_text "K"` added at P6 sits at x 41.72. D2 is at (43.620, 60.825) rot 180:

| | board x | net | role |
|---|---|---|---|
| pad 1 | 45.26 | `+VIN` | **cathode** |
| pad 2 | 41.98 | `/QGATE` | anode |

Evidence the cathode is pad 1, three ways: the symbol (`lib/aiee.kicad_sym`, BZT52C15)
declares pin 1 name `K`, pin 2 name `A`; the footprint
(`lib/aiee.pretty/SOD-123_L2.7-W1.6-LS3.7-RD.kicad_mod`) draws its band at local x -0.97
and its pin-1 dot at local (-1.85, 0.80), **both on the pad-1 side**; and the netlist puts
pad 1 on `+VIN`, which is where the cathode of a Vgs clamp belongs.

The `K` text is 0.26 mm from pad 2's x-span (it sits directly above the anode pad) and
3.54 mm from the cathode. **It contradicts the same part's own band and dot.** Two
conflicting cathode indications is worse than none.

Consequence, if a board is hand-built or reworked to the silk: D2 goes in backwards and
becomes a plain forward diode from `+VIN` to `/QGATE`, holding Vgs at about -0.7 V.
AO4407A's Vgs(th) is -1 to -3 V, so Q1 never enhances and the whole 2.6 A input current
runs in its body diode - roughly 0.8 V x 2.6 A = **2.1 W in an SO-8 with no heatsinking**.
Q1 dies and the reverse-polarity protection goes with it.

The circuit is correct; only the marker is wrong. Fix: `silk_place` the text to ~(45.6, 59.1),
or delete it and let the footprint band do the job. **domain: silk.**

Cross-check that this is an isolated slip, not a systematic one: D1's `K` at (64.770, 71.625)
IS correct - `LED0805-R-RD` puts pad 1 at local +1.05 (anode, net `/LEDA`) and pad 2 at
-1.05 with the chamfered cathode bracket, and the marker is at pad 2. Only D2 is wrong.

### E2. Eight refdes labels are attributed to the wrong part - `F.SilkS`

These are `check_silk`'s eight `silk_misattributed` **warnings**. They were neither fixed
nor waived - they simply fell through the P8 gate, which only fails on `error`. They are
real, and three of them are worse than "misattributed":

- **`R5` / `C2` / `R3` print as a left-to-right row above the parts C2 / R5 / C3**
  (x 40.22 / 43.22 / 46.22, all at y 55.025). Every label in that row names a different
  part from the one beneath it. `C2`'s text at (44.995, 53.025) is 0.47 mm from C3;
  `R3`'s at (46.72, 53.318) is 0.27 mm from R6 and 1.7 mm above C3, while the real R3 is
  4.6 mm away at (44.720, 57.425). Values involved: C2 = 3.3 nF, R5 = 75 k, C3 = 10 pF,
  R3 = 24.0 k - four different parts, three swappable 0603 bodies. Visible directly on
  `reports/renders/sbuck-5v3a_top.png`.
- **`C9` at (35.695, 48.060) prints ON C7** (0.00 mm). C9 is the 100 nF 0603 that sets the
  hot loop; C7 is a 4.7 uF 1206.
- **`R7` at (53.298, 55.725) prints ON C12.**

Plus `Q1`->C4 (0.65 mm), `TP1`->F1 (0.29 mm), `TP2`->R9 (0.25 mm), `TP7`->TP6 (0.70 mm).

Why this is an error and not cosmetics on this board specifically: `parts/parts.json`
records J1/J2 as **DNP for JLC assembly, hand-soldered on receipt**, so a human is
building part of this board from the silk; and TP1/TP2/TP7 mislabel probe points on a
live 18 V converter.

The **functional** test-point legends are fine and correctly placed - `+VIN`, `SW`, `EN`,
`GND`, `GND-S`, `FB`, `+5V` each sit adjacent to their own pad (verified on the render).
This finding is about the refdes layer only.

Scripted fix, no copper touched: `place_edit.py move_text` / `silk_place.py`. **domain: silk.**

---

## WAIVER AUDIT - the nine waived findings

### Waiver group 1: 7 x `check_silk` "silk circle covers pad TPn.1 (1.77 mm2)" - **UPHELD**

Verified on three independent legs. The first two are decisive; the third I had to prove
rather than accept.

**(a) The geometry, read straight out of the board file.** All seven TPs carry:
```
(fp_circle (center 0 0) (end 0 0.95) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS"))
(pad "1" smd circle (at 0 0) (size 1.5 1.5) (layers "F.Cu" "F.Mask"))
```
pcbnew reports `GetFillMode() = 1`, and `pcbnew.FILL_T_NO_FILL == 1` (KiCad's enum starts
at 1; `FILLED_SHAPE == 2`). Ring inner edge = 0.95 - 0.12/2 = **0.89 mm**; pad radius
= **0.75 mm**; clearance **0.14 mm**. The claim is exactly right.

**(b) The checker bug, located.** `check_silk.py:167-172`:
```python
if kind.endswith("circle"):
    c, e = _nums(_kid(node, "center")), _nums(_kid(node, "end"))
    r = math.hypot(e[0] - c[0], e[1] - c[1])
    return Point(xf((c[0], c[1]))).buffer(r + w2)      # <- FILLED disc
```
`_shape_geom` never reads the `(fill ...)` node at all, for any shape kind. So the ring
becomes a filled disc of radius 0.95 + 0.06 = 1.01 mm, which swallows the pad whole.
Reported overlap 1.7659 mm2 vs pi*0.75^2 = 1.76715 - a 0.07% shortfall that is just
shapely's polygon approximation of a circle. Exactly the signature the waiver claims.

**(c) The DRC cross-check is valid here, but its stated generality is not.** I did not
take "kicad-cli DRC reports 0 violations" on trust. On a scratch copy I shrank TP4's silk
ring to r = 0.30 - **entirely inside** the 0.75 mm pad - and `kicad-cli pcb drc
--severity-all` still reported **0 violations**. I then injected two fat silk segments
**crossing** TP3, U1.2, U1.9 and C9's pads and got 5 x `silk_over_copper` +
9 x `silk_overlap` warnings. So:

> KiCad's `silk_over_copper` fires on silk that crosses a pad's mask aperture, and stays
> silent on silk fully enclosed inside one.

A ring at r = 0.95 overlapping a 0.75 mm pad would be a *crossing*, so DRC's silence on
this board **is** real evidence and leg (c) stands. But the waiver's wider phrasing - "the
playbook itself directs that silk be verified with `kc.py drc` rather than `check_silk`" -
is too broad and should be narrowed in the record: `kc.py drc` is not a general substitute
for `check_silk`, and this board has no working automated check for enclosed-silk cases.

**Verdict: waiving the checker, not the geometry. Correct. Keep all seven.**

### Waiver group 2: 2 x `check_pdn` "+5V / GND has no decoupling capacitors" - **UPHELD, but the stated reason is wrong in a way that matters**

The **call** is right. The **reason** is not, and the difference changes what the human
should be told.

`check_pdn` does not model "a supply rail must have decoupling capacitors near its IC
pins". Reading the source: `rail_caps()` filters `decoupling.json["associations"]` by
`rail == <net>` and raises an error if that list is empty. **It never looks at the board.**
Near-pin geometry is `check_decoupling`'s job, and that check passed on its five `+VIN`
associations (loop 5.05-11.50 nH).

So the finding is not a category error about IC pins. It is a literal and true statement
about the project's own metadata: **no `decoupling.json` association names `+5V`, so no
automated check has ever looked at the output bank.** "Nothing is hidden" overstates it.

What I verified about the rails themselves, so the human knows the substance is sound:
- The `+5V` bank exists and is connected: C10-C14 (5 x 22 uF 1210) and C15 (4.7 uF 0805)
  all carry a `+5V` pad and a `GND` partner; `+5V` F.Cu is **one 198.93 mm2 island**;
  `kc.py drc --parity` is clean, so schematic and board agree.
- `check_irdrop` DID run on both nets with the real geometry (they were correctly NOT
  given `pdn:false`): `+5V` worst drop **8.96 mV**, `GND` **1.15 mV**, against a
  +/-100 mV output window. This is the leg that actually covers these two rails.
- `GND` is a return net; decoupling to itself is meaningless. Correct.

**Verdict: keep both waivers, but restate the reason as "check_pdn is a metadata
inventory and `+5V` has no association declared; coverage for this rail comes from
check_irdrop and P4 arithmetic, not from a PDN check". Also fix `decoupling.json`'s
`_note`, which still claims `+5V` is handled by `pdn=false` - `constraints.json` records
that as reverted.**

---

## THE SPECIFIC CLAIMS, RE-MEASURED

| claim | stated | my measurement | verdict |
|---|---|---|---|
| vias inside the hot-loop region x 38.87-43.02 / y 46.90-49.20 | 0 | **0**. Nearest are the EP thermal array at x 43.42, outside the region and inside the return path anyway | confirmed |
| In1 GND under that region | unbroken image plane | **100.00%** coverage - 9.545 of 9.545 mm2 | confirmed |
| `/SW` copper | 30.4431 mm2, F.Cu only, <= 40, >= 2.5 mm wide | **30.4422 mm2**, F.Cu only, **1 island**; conduction path U1.8 -> L1.1 survives a **1.5 mm** erosion, so it is **>= 3.0 mm wide throughout** | confirmed (area + width) |
| `/SW` length | <= 8 mm | **10.490 mm** | **exceeded - see W1** |
| `/SW` near an edge or connector | no | 5.704 mm to the outline, 16.63 mm to J2, 17.22 mm to J1 | confirmed |
| `/SW` inner-layer copper | none | **none** - the board has 28 vias total and every one is GND; every non-GND net is F.Cu-only | confirmed |
| FB senses at C12's `+5V` pad | ~2.21 mm, not the inductor pin | R6.1 taps the `+5V` node at (51.700, 52.997); copper path R6.1 -> node = 1.97 mm, node -> C12.1 = 2.03 mm. L1.2 is **13.3 mm** away. The divider taps the same node C12 does | confirmed |
| FB routed away from `/SW` and L1 | yes | FB copper -> SW copper **2.935 mm**; FB copper never overlaps L1's body (FB x 48.27-48.58, L1 body starts x 50.17 -> ~1.6 mm horizontal); R6<->L1 9.835 mm and R7<->L1 13.994 mm against the 5 mm constraint | confirmed |
| U1 EP thermal vias | 12 | **exactly 12**, 3 cols x 4 rows, **0.9 mm pitch both axes**, 0.3 mm drill -> **0.600 mm** hole-to-hole against JLC's 0.5 floor | confirmed |
| 16 geometrically impossible | yes | 4 columns inside the EP's **2.613 mm** need pitch <= (2.613-0.6)/3 = **0.671 mm** -> 0.371 mm hole gap, **under** the 0.5 floor. 4 at 1.0 mm pitch needs 3.55 mm. Impossible either way | confirmed |
| ring vias | 6 (3 of 9 deleted) | **6**, at y 45.700 and y 51.500, x {43.1, 44.1, 45.1} and {43.6, 44.6, 45.6} | confirmed |
| In1 solid GND | 444.4 mm2 within 12 mm, one piece, no split | **444.92 mm2** within 12 mm; **ONE island of 1850.07 mm2**; 14 voids, every one of them a mounting hole or a J1/J2 THT antipad, **none within 12 mm of U1** | confirmed |
| F.Cu GND island at U1 | >= 100 mm2, contiguous with the EP | **1340.60 mm2**, contains the EP | confirmed, 13x over |
| B.Cu GND | >= 1500 mm2 of 2000 | **1850.07 mm2 = 92.1%** of the 2009 mm2 outline | confirmed |
| L1 `+5V` pour | grown to 153.3 mm2 | **153.23 mm2** within 14.3 mm | confirmed |
| J1/J2 wire entry | off-board | **confirmed on the iso render**: J1 entry -x, J2 entry +x, screws top-accessible, bodies 0.325 mm inside their edges | confirmed |

### Was deleting 3 of the 9 ring vias right?

Yes, on the evidence. The ring vias sit 1.12-1.17 mm outside the EP edges and serve
secondary spreading; the 12-via EP array is the primary junction-to-plane path and is
untouched. The stated reason (they sat in 1.06-1.58 mm GND fingers) is the right kind of
reason, because a 0.6 mm via in a 1.06 mm finger leaves 0.23 mm each side. And the check
that would catch the consequence is armed: `GND` is declared `plane_fed: true`, which
keeps **pour-neck findings at ERROR severity at the full 3.3 A budget**, and
`check_current` reports **zero** pour-neck errors - only the ten leaf-tap advisories.
Thermal cost of 9 -> 6 in the ring is second-order against the EP array.

### The mounting-hole keepout that was never built

`constraints.json` placement note (3) asked for a 6.5 mm mask/copper keepout at each M3
hole, hand-added as rule areas after the pours. **There are no rule areas on this board.**
I checked the consequence rather than assuming it: all four layers are GND at every hole
(In1/In2/B.Cu each void a 3.7 mm circle around the 3.2 mm NPTH, so no inner copper is
exposed at the barrel), and the nearest **non-GND** copper to any hole is **5.38 mm**
(H2, F.Cu) against an M3 washer radius of 3.25 mm - **2.13 mm clear**. Benign. Record it
as a knowingly-dropped constraint rather than leaving it silently unmet.

---

## U1's THERMAL NUMBER - which model to believe

**Do not report "54.17 C against 55 allowed, 0.83 C of headroom" as this board's tightest
number. It is not a measurement of this board at all.**

`check_thermal` computes `a_eff = min(A_SAT = 645, sum over layers of heatsink-net copper
within 14.3 mm)`. I measured that sum: **2137.56 mm2**. So `a_eff` **clamps** to 645, and

```
theta = 45 + 95 * exp(-645/235) = 45 + 95*0.06427 = 51.1055 C/W
rise  = 1.06 * 51.1055 = 54.17 C
```

At the clamp, `theta` is a **universal constant** for any 4-layer board with >= 645 mm2 of
heatsink copper. The 12 thermal vias, the three 1850 mm2 planes, U1's position near board
centre - every one of them moves this result by exactly **0.00 C**. What "54.17 vs 55"
measures is the distance between two *declared inputs*: `power_w = 1.06` and `dt_c = 55`.

`check_thermal` is also **not additive**: U1's 54.17 C and L1's 42.51 C are each computed
as if that part were the only heat source on the board. They cannot both be "the rise".

**Believe the P1/P2 board-level ladder.** I re-derived its inputs from scratch before
looking at its answer:

```
h_conv = 1.42*(dT/L)^0.25 = 1.42*(37/0.05)^0.25            = 7.41 W/m2K
h_rad  = 0.9*sigma*(358^2+323^2)*(358+323)                 = 8.08 W/m2K   (they used 8.2)
h_tot  = 15.5 W/m2K over A_eff 3.4e-3 m2  ->  R_ba         = 19.0 C/W
```

That reproduces their `R_ba = 19 C/W` to about 2%, from textbook flat-plate correlations,
and the ladder `Tj = Ta + P_board*R_ba + dT_local + P_IC*(theta_JC,bot + R_via)` is the
correct physics for a near-isothermal board (spreading length 32 mm > the 20-25 mm board
half-dimension). Worst **Tj = 97.9 C at 7 V**.

Two corrections to that ladder that nobody has applied:

1. **It still carries the 16-via array at 2.16 K/W.** The board has 12. `R_1via = 29.4 K/W`
   -> 12 in parallel at the same 0.85 crowding factor is ~2.88 K/W, so
   `+1.058 * (2.88 - 2.16) = +0.76 C`. **Worst Tj ~= 98.7 C, margin 6.3 C, not 7.1 C.**
   The P2 digest table was not updated for the P6 16 -> 12 change.
2. **The honest band.** `R_ba` is stated at +/-30%, and only the `P_board*R_ba` term
   scales: `50 + 34.7*0.7 + 6 + 7.2 = 87.5 C` to `50 + 34.7*1.3 + 6 + 7.2 = 108.4 C`.
   The upper edge crosses the 105 C *design* limit but stays **17 C below the 125 C
   conservative spec floor** and **51 C below AP64350's actual 150 C Tj max**.

**What to say to the human.** The thermal risk on this board is dominated by **mounting,
not layout**. 53% of the cooling path is radiation from two faces. Boxing this board,
conformal-coating it, or bolting it flat against a surface removes a large share of that
and costs tens of degrees - far more than any 0.83 C. That belongs in the assembly note
in bold. The layout side is already 3x over its copper criteria and cannot be improved
meaningfully.

L1's 42.51 C / 45 C is conservative for the same structural reason: `a_eff` counts only
the 153.23 mm2 of `+5V` copper, excluding the 30.44 mm2 `/SW` pad and the 1838.91 mm2 of
GND under the part. Counting `/SW` too gives 39.8 C. The number that matters for L1 is the
board-level `T_L1 surface 100.7-106.5 C` against the part's 155 C rating.

---

## RECOMPUTED ELECTRICALS (the brief's closing checklist)

| quantity | recomputed | spec | margin |
|---|---|---|---|
| inductor ripple, Vin 18 V | `5(18-5)/(18*6.8u*500k)` = **1.062 A** p-p | - | - |
| inductor peak | 3 + 0.531 = **3.531 A** | Isat 14 A (12.3 A max-col) | **3.5x**; constraints declare 3.6 A, conservative |
| Cin RMS | `3*sqrt(D(1-D))` maximises at D=0.5 -> Vin 10 V (inside range) = **1.500 A** | C5-C8 share 375 mA each, ~0.7 mW each at 5 mOhm ESR | large |
| output ripple, Vin 18 V | `1.062/(8*97u*500k)` = 2.74 mV + ESR 1.062*~1 mOhm = 1.1 mV -> **~3.8 mV** p-p | 50 mV | **13x** |
| setpoint | `0.8*(1+105/20.0)` = **5.0000 V** nominal; corners with VFB 792/808 mV and 0.1% parts = **4.942 / 5.058 V (+/-1.16%)** | 4.90-5.10 V | see below |
| Tj worst | **~98.7 C** (ladder, 12-via corrected); band 87.5-108.4 C | 105 C design / 125 C spec floor / 150 C actual | 6.3 C to design |

**Setpoint stack - one term is missing from the record.** `root.py` quotes the VFB
tolerance and the resistor tolerance but not resistor **tempco**. ERA3AEB1053V and
RT0603BRD0720KL are both +/-25 ppm/K; worst-case differential drift over the 55 K rise
from 50 C to the ~105 C board is `2*25e-6*55 = 0.275%` = **14 mV**. Adding that plus
load regulation and the uncompensated C12 -> J2 IR drop (`check_irdrop` worst `+5V` drop
8.96 mV) to the +/-58 mV corner gives **~82 mV worst case against the 100 mV window** -
still passing, with ~18 mV left. Worth adding the term to the record.

**SPICE: I agree it can be skipped.** SIM-1 (the setpoint sweep) is a four-term
worst-case sum, closed above in closed form. A sweep would add no information. The bench
item that actually matters is the loop, and no SPICE model of this board closes that
either - it needs a network analyser.

---

## WARNINGS - full list with verdicts

Every `verify_all` warning gets a verdict here.

| # | finding | verdict |
|---|---|---|
| W1 | **`/SW` pour is 10.490 mm long vs the 8 mm ceiling** (bbox 10.490 x 4.421). Excess is entirely the C1(BST)/TP2/R9 stub, 5.32 mm to -x of the SW pin; the load-carrying run U1.8 -> L1.1 is 3.73 mm. Physics benign: `C = e0*er*A/d = 4.85 pF`, `I = C*dV/dt = 17.5 mA` at 18 V / 5 ns, returning into the plane 0.244 mm below. **Undisclosed anywhere.** | document as accepted deviation; do not move the BST cap |
| W2 | **check_thermal's 0.83 C is not a layout property** (clamped `a_eff`, non-additive) - full analysis above | escalate to a documentation correction |
| W3 | **L1's 42.51/45 C measures the wrong path** (excludes `/SW` pad and all GND) | conservative, no action |
| W4 | **The PM floor is not actually bounded.** The dV COUT-invariance argument is correct and I do not re-litigate it (`2*pi*fc*COUT = R5*gm*VFB/(RTsense*VOUT)` is COUT-free). But PM is *not* invariant: root.py's own table gives PM(corrected) 45.6-47.2 deg at COUT 75.0 uF vs 51.3-52.8 at 96.8 - 0.6 deg over the floor at the low corner. And [75.0, 96.8] uF is a **DC-bias band**: the low end IS the vendor's DC-bias-only ratio (68.2%), so root.py 2.2's remark that hot X7R and aging "push toward the low end" *names* those effects without stacking them. Stack X7R hot-end loss (~-10% at the board's own stated 83-87 C) and 1000 h aging (~-5%) on 75.0 uF -> **~62.7 uF**, ~20% below the swept corner; on the sweep's own slope (75k -> 82k = +9% fc for -1.5 deg PM) that is roughly **-3 deg -> PM ~42-44 deg, under the 45 floor** | no respin (R5/C2/C3 are three adjacent 0603s, already bench item #1) - but the disclosure must say COUT_min is DC-bias-only, so PM reads as unbounded, not 0.6 deg clear |
| W5 | **DNP snubber loop ~12 mm.** `/SW` -> R9.1 (47.420,43.905) -> R9.2 (47.420,40.945) -> C16.1 (44.310,40.425) -> C16.2 GND (41.130,40.425). `L' = mu0*h/w = 0.256 nH/mm` at w 1.2 / h 0.2444 -> ~3.1 nH + ~2 nH component ESL = ~5 nH; with 470 pF that self-resonates at **~104 MHz**, inside the band a SW snubber exists to damp. C16's GND pad is 6.7 mm from U1's EP | record; DNP, do not respin |
| W6 | **C12's ground leg is one via into a 4.41 mm2 orphan F.Cu island.** Four GND pads sit on orphans - C12.2, C2.2 (16.65), R1.2 (14.20), R4.2 (3.60) - each with exactly one stitching via, so nothing floats and three are small-signal. C12 is a 22 uF output bulk cap; one 0.3 mm via adds ~0.6-1 nH, comparable to its own impedance at 500 kHz. C10/C11/C13 (4.84 / 6.79 / 8.10 mm from L1.2) are on the main island so the bank still works | add a second via at ~(54.7, 54.6): one op, zero risk, clears one advisory |
| W7 | **J1 and J2 carry `+` on opposite edges.** J1 pin1 (`/VIN_RAW`) upper at y 54.685, J2 pin1 (`+5V`) lower at y 59.765. Forced by the wire-entry requirement (both verified off-board on the iso render), so the mirror is not an accident. Silk does mark it: `+`/`-` at (34.12, 54.685)/(34.12, 59.625) and `-`/`+` at (61.22, 54.685)/(61.22, 59.765), plus `VIN 7-18V` and `VOUT 5V 3A`, all clear of the connector bodies and still visible after assembly. Residual: this silk is the ONLY mitigation for delegate Q30, and getting `+` onto the same physical edge needs J2's pin/net assignment swapped in the **schematic** | confirm as a decision at checkpoint 4; not a P8 defect |
| W8 | **Every power net is routed at exactly its IPC-2152 minimum.** `check_current` min_track == required on all of them: 1.52 mm (`/VIN_RAW`, `/VIN`, `+VIN`), 2.055 mm (`+5V`), 2.31 mm (`/SW`). At JLC's ~+/-0.05 mm etch that is -2.4% on `+5V` -> dT ~10.5 C instead of 10 | acceptable; state that dT=10 C is nominal, not worst case |
| W9 | **Two verification legs are hollow.** `check_pdn_z` checked **zero pairs** (skipped `+VIN` for "no plane pair detected", attempted nothing else) - a direct and expected consequence of the deliberate 4 x GND stackup, so it is not coverage. And `kc.py drc` has no silk test for **enclosed** silk: proved by shrinking TP4's ring to r=0.30 inside its pad (0 violations) versus injecting crossing segments (14 violations) | say so; do not count either as a pass |
| W10 | **`constraints_drift`.** I diffed both files leaf by leaf: the ONLY differences are the 16 numbers of the four mounting-hole keepout rects - the documented board-local -> absolute translation. Everything else identical; checks ran against the correct `kicad/` copy | justified waiver; annotate or delete the `architecture/` twin |
| W11 | **`decoupling.json`'s `_note` is stale** - it says `+5V` is handled by `pdn=false`, which `constraints.json` records as reverted. Two files, opposite statements, and the stale one is what feeds `check_pdn` and `check_decoupling` | one-line documentation fix |
| W12 | **The 6.5 mm mounting-hole mask/copper keepout was never built** (no rule areas exist). Benign: all four layers are GND at every hole and the nearest non-GND copper is 5.38 mm vs an M3 washer radius of 3.25 mm - see the section above | record as a knowingly-dropped constraint |
| - | **10 x `check_current insufficient_transition_vias`** (all `GND`, all "1 via, 3.30 A needs 7") | **justified.** Every one is a leaf tap: five are perimeter stitching vias at x/y 30.72/45.72/60.72 carrying no net current, and four are the sole vias of the orphan islands above (of which only C12's carries meaningful current - see W6). `GND` is `plane_fed`, which keeps **pour necks at ERROR** at the full 3.3 A, and there are **zero** pour-neck errors. Advisory is the right severity |

---

## THINGS I CHECKED AND FOUND CLEAN

- `kc.py drc --parity --all-track-errors`: 0 violations, 0 unconnected, schematic/PCB
  parity clean. Re-run by me at P8, not inherited from P7.
- `check_return_path` 0, `check_decoupling` 0 (five `+VIN` associations, loop 5.05-11.50 nH,
  C9 closest at 2.14 mm / 5.05 nH), `check_diffpair` 0, `check_creepage` 0.
- `check_irdrop`: `+VIN` 13.96 mV, `+5V` 8.96 mV, `GND` 1.15 mV. Against a +/-100 mV
  output window the sense-point-to-terminal error is ~0.2%. No concern.
- No copper on any inner layer for any non-GND net (28 vias, all GND).
- B.Cu is a bare, uninterrupted 1850 mm2 GND face with only the four J1/J2 THT annular
  rings and the vias breaking it - exactly what the radiation budget needs. Note for the
  assembly doc: J1.1 (`+VIN`) and J2.1 (`+5V`) are exposed on B.Cu, so insulating
  standoffs are required if the board is mounted over metal.
- No fiducials. JLC's SMT service does not require board fiducials and the connectors are
  DNP/hand-soldered, so this is a note for P9, not a finding.
- LCSC stock present for all 24 BOM lines. **L1 (FAUL1050-6R8MT, C5298292) at 763 pcs is
  the only thin line** - single-source, no like-for-like alternate that clears
  DCR <= 25 mOhm hot at 6.8 uH. Every other line clears its floor by >= 4x. Schedule
  risk for P9, not a board defect.

## OPEN - not judgeable from the artifacts

- Loop phase margin at the true COUT floor (W4). Needs a network-analyser measurement;
  no model available to this project closes it.
- AO4407A dv/dt immunity - no Ciss/Crss/Coss published (already disclosed as P4 W4).
- Whether the enclosure preserves the two radiating faces (W2). The single largest
  thermal lever on this board and it lives outside the board.
- Whether a human ever reads the silk on this board. E2's severity depends on it; I
  graded it as an error because `parts.json` says J1/J2 are hand-soldered on receipt.
