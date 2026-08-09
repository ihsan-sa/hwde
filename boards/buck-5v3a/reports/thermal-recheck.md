# U1 thermal re-check after the exposed-pad refutation (P2 revisit, 2026-08-09)

Trigger: `reports/u1-land-ruling.md` proved the AP63356QZV-7 (V-DFN3020-13/SWP Type A1) has
**9 lands and NO exposed / thermal / belly pad**. The P2 thermal case was written around a
3x3 array of 0.3 mm vias in an exposed-pad land that does not exist. This document redoes the
numbers against the real part.

## 0. Headline - what actually changed

| | P2 (EP assumed) | Now (no EP) |
|---|---|---|
| Gate theta_JA, 4L | 51.1 C/W | **51.1 C/W - unchanged** |
| Gate Tj at the 7 V corner, 50 C amb | 95.0 C (0.881 W) / 98.6 C (0.95 W) | **95.0 / 98.6 C - unchanged** |
| Best physical estimate of theta_JA, 4L | not computed | **~36 C/W** (32-41 over the convection band) |
| Neighbour-heating allowance on top | +10 C (stackup.md s2.4) | **retired - it was double counting** |
| Why 4 layers | thermal: 51 vs 74 C/W = ~20 C | **return plane + the gate. Thermally worth ~3 C, not ~20 C** |
| Heat exits | 9 vias in a belly pad | **the GND land and the VIN land** |
| U1 via prescription | 3x3 in-pad array + 3 in the pour | **12 x 0.55/0.30 in the GND pour AROUND the land; NO via-in-pad; +VIN gets pour area, not vias** |
| Verdict on the part | pass | **pass, with 55 C to the 150 C recommended max** |

**The gate numbers did not move, and that is not a coincidence to be relieved about - it is the
finding.** `check_thermal`'s model never contained an exposed pad in the first place (s4). What
the refutation actually invalidated was the *layout prescription* and the *physical story* told
in `research/power.md` s4.3-4.4 and `architecture/stackup.md` s2.3. Those are corrected here.

## 1. What the vendor actually publishes (read off the PDF, not extracted text)

`parts/C3194571.pdf` p.4, "Thermal Resistance (Note 6)":

- theta_JA, V-DFN3020-13/SWP (Type A1) = **25 C/W**
- theta_JC, same package = **5 C/W** (plain junction-to-case; Diodes does NOT quote
  theta_JC(bottom), and 5 C/W is far too low to be a top-of-package path on a 0.85 mm plastic
  DFN - it is the die-to-land number)
- Note 6, verbatim: *"Test condition for V-DFN3020-13/SWP (Type A1): Device mounted on FR-4
  substrate, four-layer PC board, 2oz copper, with minimum recommended pad layout."*

p.5: RDS(on) 74 mohm HS / 40 mohm LS typ, **no maximum published**; fsw 450 kHz typ;
TSD +170 C typ with 25 C hysteresis. p.4 Recommended Operating Conditions: **TJ -40 to +150 C**.
Absolute Maximum Ratings: **TJ +170 C**.

p.25 "PCB Layout", the rules that matter here, verbatim:

> 1. ... 2oz copper for both the top and bottom layers is recommended.
> 6. If using four or more layers, use at least the 2nd and 3rd layers as GND to maximize thermal performance.
> 7. Add as many vias as possible around both the GND pin and under the GND plane for heat dissipation to all the GND layers.
> 8. Add as many vias as possible around both the VIN pin and under the VIN plane for heat dissipation to all the VIN layers.

Figure 47 draws it: a large VIN pour and a large GND pour, each carrying roughly 4-5 vias -
some inside the large land, most in the pour immediately outboard of it. There is no centre
land and no via array under the body. **Note the word in rules 7 and 8 is "around".**

## 2. Ruling between the three theta_JA figures

| # | Source | Value | Standing |
|---|---|---|---|
| 1 | DS41948 p.4 Note 6 | 25 C/W | **correct for Note 6's board, unreachable on ours.** Optimistic bound. |
| 2 | repo `check_thermal.py`, >= 4 copper layers, pour saturated | 51.1 C/W | **the design and gate number. Stands.** |
| 3 | first-principles recomputation, this document s3 | ~36 C/W (32-41) | **the honest best estimate.** Not the gate number. |

**Ruling: 51.1 C/W remains the design number. 25 C/W is rejected as a design input. 36 C/W is
recorded as the best estimate and as the reason 51.1 C/W is safe rather than arbitrary.**

Reasons, in order of weight:

1. **51.1 C/W is not a choice.** `check_thermal` derives theta_JA from the board itself -
   copper area of the heatsink net within a 14.3 mm reach, capped at 645 mm^2, plus a boolean
   layer count. On any 4-layer build with GND planes the area term saturates, so the gate will
   report **exactly 51.1 C/W** no matter what any document says. Machine-verified below.
   `constraints.json` cannot change it; it carries only `power_w`, `dt_c`, `net`, `min_vias`.
2. **Note 6's 25 C/W is a different board, and the dominant difference is AREA, not copper
   weight.** JESD51-7's 2s2p coupon is 2 oz outer / **1 oz inner** and 5806-8710 mm^2 against
   our 2000 mm^2 with 0.5 oz inners. Running the s3 model on the JEDEC geometry reproduces
   **24.6-26.3 C/W** against the vendor's 25; running it on ours gives ~36. Swapping only the
   inner copper (1 oz -> 0.5 oz) on the JEDEC board moves it by ~2 C/W. The 11 C/W gap between
   the vendor's board and ours is almost all board area.
3. **51.1 C/W is ~1.4x the best estimate, and that pessimism is doing useful work.** The s3
   model run with the *other* 0.60 W of board loss injected as well (L1, F1, Q1, copper) gives
   an effective 44-58 C/W at U1's junction - which brackets 51.1. So the gate's pessimism is
   very close to the neighbour heating that `check_thermal` structurally cannot see.
   **Consequence: the separate "+10 C for neighbours" allowance in `stackup.md` s2.4 is
   double counting and is retired.** Tj at the 7 V corner is ~95 C, not ~105 C.
4. Every number in this document carries the model's stated +/-30 %, and the h band in s3 is
   wider than the difference between several of the conclusions. Nothing here is a sign-off;
   the post-fab check is `Tj = T_case_top + psi_JT x P`, and DS41948 publishes no psi_JT, so
   the bench recipe is a case-top measurement plus the 5 C/W theta_JC as an upper bound on the
   die-to-case delta (0.881 W x 5 = 4.4 C).

## 3. First-principles recomputation

Method (`research/raw/theta_ja_model.py` - a board-local working script, not a shipped
pipeline script; run it with `.venv\Scripts\python.exe` to reproduce every table below):
a two-sheet 1-D radial finite-difference spreader.

- **Node A** = top copper (F.Cu). **All of U1's heat enters here**, because with no exposed pad
  the die reaches the board only through the VIN land, the GND land and the SW land - all F.Cu.
- **Node B** = the lumped inner + bottom copper.
- A and B are coupled everywhere by the dielectric (0.3 W/m.K over 0.4284 mm of 7628x2 prepreg
  on 4L; over 1.46 mm on 2L) and, near the part, by the thermal vias.
- Both sheets lose heat to ambient through a combined convection + radiation h.
- theta_JA = theta_JC (5 C/W, vendor) + T_A(source)/P.
- Stackup as built: F.Cu 0.070 mm (2 oz, 70 % coverage), In1/In2 0.0152 mm (0.5 oz),
  B.Cu 0.070 mm (90 % coverage). Board 2000 mm^2 as an equal-area disc.
- Via: 0.30 mm drill, 25 um plating -> barrel copper 0.0216 mm^2 ->
  **50.9 C/W per via F.Cu to In1**, 173 C/W per via F.Cu to B.Cu on a 2-layer board.
  A 0.20 mm drill (the rule-class minimum) is **79.9 C/W** - 1.6x worse. Use 0.30.

**Calibration against the vendor's own number** (JEDEC 2s2p, 76.2 x 114.3 mm, 2 oz outer /
1 oz inner, same part, same 5 C/W theta_JC):

| h (W/m^2K) | model theta_JA | vendor |
|---|---|---|
| 10 | 26.3 | 25 |
| 12 | 25.3 | **25** |
| 14 | 24.6 | 25 |

On the smaller JESD51-3 coupon (76.2 x 76.2) the model gives 26-29 C/W. Either way the method
reproduces Note 6 within its uncertainty, which is what licenses using it on our board.

**buck-5v3a, 50 x 40 mm, 4 layers, 2 oz outer / 0.5 oz inner, U1 = 0.881 W:**

| GND vias | h=20 | h=30 | h=40 |
|---|---|---|---|
| 0 | 46.1 | 37.8 | 33.6 |
| 4 | 42.7 | 34.3 | 30.1 |
| 8 | 41.5 | 33.1 | 28.9 |
| **12** | **40.8** | **32.5** | **28.3** |
| 16 | 40.4 | 32.1 | 27.9 |

**Same board on 2 layers (2 oz outers, no inner planes):**

| GND vias | h=20 | h=30 | h=40 |
|---|---|---|---|
| 0 | 48.8 | 40.4 | 36.1 |
| 12 | 44.1 | 35.7 | 31.5 |

Hand-checked h for a 50 x 40 board in still air at ~85 C: natural convection ~10 W/m^2K facing
up / ~5 facing down (Nu = 0.54 Ra^1/4 and 0.27 Ra^1/4, L_c = A/P = 11.1 mm), plus ~8.3 W/m^2K
of radiation at eps = 0.9 both faces -> **h_total ~28-31**. So **h = 30 is the central case and
h = 20 the conservative one: theta_JA = 32.5 to 40.8 C/W, call it 36 C/W.**

Three things fall out of the table that the old analysis got wrong:

- **Vias are worth ~5 C/W total, and the first four buy most of it** (46.1 -> 42.7 -> 40.8).
  Going from 12 to 16 vias is worth 0.4 C/W. The old "9 vias in the EP land are worth 17 C/W"
  arithmetic (power.md s4.3) compared a via bundle against nothing at all; it ignored that the
  2 oz top pour couples to In1 through 0.43 mm of prepreg over its whole area in parallel.
- **The 4L-vs-2L thermal gap is ~3.3 C/W, not 23 C/W.** With 2 oz outers the board is already
  near-isothermal at 2 layers: the two 0.5 oz inner planes add only 0.030 mm of copper against
  0.140 mm on the outers - **18 % more lateral sheet conductance**. The repo model's 74 C/W is
  a *1 oz* 2-layer number (`MODEL_2L` docstring) applied to a 2 oz board, and its only 4L input
  is a boolean, so it cannot see that our inners are half weight.
- **The board is not 90 C.** With all 1.483 W on it, mean board rise is +24.7 C at h=30 and
  +37.1 C at h=20 -> a **75-87 C board**, not the ~90 C assumed in power.md s5. That does not
  change any conclusion drawn from it (X5R's 85 C ceiling is still disqualifying, the SMD fuse
  still derates ~30 %), so those rulings stand unchanged.

## 4. The machine run - and what the gate can and cannot see

No `.kicad_pcb` exists (board is at P3), so `check_thermal` was run against a probe board built
for this document with the **real 9-land pattern and no exposed pad**: 50 x 40 outline, U1 at
(18,20) with all nine lands on their footprint coordinates, 271 mm^2 of F.Cu GND pour joined to
the GND land, a +VIN pour on the Cin side, solid GND on In1/In2/B.Cu, and 13 GND vias in and
around the GND land. A 2-layer twin drops In1/In2. The generator is kept at
`research/raw/thermal_probe_board.py` so this run is reproducible (P2's probe was not kept,
which is why it had to be rebuilt here).

```
.venv\Scripts\python.exe boards\buck-5v3a\research\raw\thermal_probe_board.py
.venv\Scripts\python.exe .claude\skills\ai-ee\scripts\check_thermal.py \
    --pcb probe4l.kicad_pcb --constraints boards\buck-5v3a\architecture\constraints.json
```

| Probe | P_IC | a_eff | theta_JA | rise | Tj at 50 C | status |
|---|---|---|---|---|---|---|
| 4L, 13 vias | 0.881 W | 645 mm^2 | **51.106** | **45.02 C** | **95.0 C** | pass |
| 4L, 13 vias | 0.95 W (the constraint) | 645 mm^2 | 51.106 | **48.55 C** | 98.6 C | **pass, 6.4 C margin** |
| 4L, 13 vias | 1.10 W | 645 mm^2 | 51.106 | 56.22 C | 106.2 C | fail (dt 55) |
| 2L, 13 vias | 0.881 W | 645 mm^2 | 73.845 | 65.06 C | 115.1 C | **fail** |
| 2L, 13 vias | 0.95 W | 645 mm^2 | 73.845 | 70.15 C | 120.2 C | fail |
| **4L, ZERO vias, ZERO top GND pour** | **0.95 W** | **645 mm^2** | **51.106** | **48.55 C** | 98.6 C | **pass** |

That last row is the honest limitation statement, and it was run deliberately: **strip every
thermal via and the entire top GND pour, and the gate returns the identical number and still
passes.** `check_thermal` is an area-and-layer-count screen. It sums heatsink-net copper inside
a 14.3 mm radius over all layers and caps it at 645 mm^2; three solid GND planes saturate that
on their own. It has no term for the die-to-copper coupling - which, now that there is no belly
pad, is the only part of the problem the layout can still get wrong.

**How that was compensated, rather than faked:** the probe was not given fictional geometry.
The gate result is reported as what it is - a layer-count screen that this board passes - and
the die-to-land coupling that the gate cannot see is bounded separately by the s3 model and
turned into the hard, countable layout prescription in s7. The gate's via warning
(`need_vias`) does not fire here either: it triggers only when `dt/power < 51.1`, and
55/0.95 = 57.9. So **no automated check on this board tests the via array. P6/P7 review is the
only enforcement**, which is why s7 is written as numbers and not adjectives.

## 5. Junction temperature at the worst corner

Worst corner is **7 V low line, 3 A out, 50 C ambient, natural convection** (duty 0.71 parks
the conduction loss in the high-side FET). P_IC = **0.881 W** modelled
(`architecture/power_tree.md` s3, RDS(on) 92/48 mohm at ~105 C), constraint value 0.95 W.

| Basis | theta_JA | Tj at 50 C ambient |
|---|---|---|
| **Gate (`check_thermal`, 4L), P = 0.881 W** | 51.1 | **95.0 C** |
| Gate, P = 0.95 W (constraint, incl. spread margin) | 51.1 | 98.6 C |
| s3 model, central (h = 30), 12 vias, U1 alone | 32.5 | 78.6 C |
| s3 model, conservative (h = 20), 12 vias, U1 alone | 40.8 | 85.9 C |
| **s3 model, h = 30, 12 vias, WITH the other 0.60 W on the board** | 43.9 eff | **88.7 C** |
| **s3 model, h = 20, 12 vias, WITH the other 0.60 W** | 58.0 eff | **101.1 C** |
| s3 model, h = 20, ZERO vias, with neighbours | 63.2 eff | 105.7 C |
| Datasheet 25 C/W (not applicable to this board) | 25 | 72.0 C |

**Against the part's own limits (DS41948 p.4):**

| Limit | Value | Margin at the 95 C gate number | Margin at the 101 C worst modelled case |
|---|---|---|---|
| TJ recommended operating max | **150 C** | **55 C** | 49 C |
| TJ absolute max | **170 C** | 75 C | 69 C |
| Thermal shutdown (typ) | 170 C, 25 C hysteresis | 75 C | 69 C |
| Soft design target (H1-d, NOT binding) | 105 C | 10 C | 4 C |

Sensitivity that matters more than any of the above: **DS41948 publishes no maximum RDS(on).**
At 1.3x typ the conduction term goes 0.721 -> 0.937 W and P_IC to ~1.10 W, giving a 56.2 C rise
and **Tj ~106 C** - still 44 C under the recommended max, but it would trip the P8 gate at
`dt_c` 55. That is the intended sensitivity and the reason `power_w` carries margin.

## 6. Does the 4-layer decision still stand?

**Yes - but the reason has changed, and the record must say so.**

- **Thermally, 4L is now worth ~3 C, not ~20 C** (s3: 40.8 vs 44.1 C/W at h=20; 32.5 vs 35.7 at
  h=30). On a 2 oz-outer board the inner 0.5 oz planes are 18 % of the copper and the board is
  near-isothermal either way. A 2-layer build would land at Tj ~92-104 C - **inside the part's
  150 C recommended max with ~46 C to spare.** Honest answer: *the junction temperature does not
  require four layers.*
- **What does require four layers is the return plane.** DS41948 rule 6 asks for GND on the 2nd
  and 3rd layers explicitly; buck.md s3 wants a solid unbroken GND directly under the
  Cin -> VIN -> GND hot loop of a 450 kHz, 3.6 A-peak converter. On 2 layers that return shares
  B.Cu with the output routing and gets cut. That is an EMI and switching-loss argument, and it
  is untouched by the EP refutation.
- **And the gate closes it anyway**: a 2-layer build scores 73.8 C/W and fails
  `check_thermal` by construction at `dt_c` 55.
- Cost: at qty 5 inside JLC's 100 x 100 promo tier the 4L delta is a few dollars per run and is
  swamped by the assembly NRE (`stackup.md` s7). There is no real money on the table here.

**No change to the stackup. `JLC04162H-7628A` stands, 2 oz outer / 0.5 oz inner.** The 2 oz
outer choice is now *more* important than P2 thought, not less: on this board the outer copper
is 82 % of the lateral spreading and it is the layer the die actually touches.

## 7. Does the part still stand?

**Yes, comfortably, and no alternative is worth evaluating.** 95 C junction against a 150 C
recommended operating maximum is 55 C of margin; even the pessimistic corner of the s3 model
with neighbour heating and zero vias is 106 C. Nothing about the missing exposed pad hurts this
part: 2.3 mm^2 of large-land copper plus theta_JC = 5 C/W is a good die-to-board path for a
0.88 W dissipation, and the vendor measured 25 C/W on that same 9-land pattern.

For the record, the options that were NOT needed: more copper (the gate's area term is already
saturated - additional pour buys nothing the model will score, and s3 says it buys ~2 C in
reality); a different package class (an SO-8EP / HSOIC PowerPAD part would improve theta_JC by
maybe 1 C/W - irrelevant against a 55 C margin); a different part class (the 45/20 mohm filter
that `research/power.json` proposed was already deleted at P2 for rejecting the whole real
shortlist).

The residual risk on U1 is **not thermal**. It is (a) no published max RDS(on), (b) no published
tr/tf, so the 0.071 W switching term at the 7 V corner is a class estimate. Both are covered by
the 0.95 W constraint against a 0.881 W model.

## 8. Layout prescription for P6/P7 - quantified

The two heat exits are the **GND land** (pad 8, 1.500 x 0.750 mm as drawn = 1.13 mm^2) and the
**VIN land** (pad 1, same size). There is no belly pad. Everything below replaces
`research/power.md` s4.4 and `research/power.json layout_notes[3]`.

**GND side - vias (the one lever that is worth real degrees):**

- **>= 12 GND vias, 0.55 mm pad / 0.30 mm drill, through (F.Cu to B.Cu)**, so each one picks up
  In1, In2 and B.Cu. Not the 0.45/0.20 rule-class minimum: the 0.30 barrel is 50.9 C/W to In1
  against 79.9 C/W for a 0.20 barrel, for one drill-size step.
- **>= 8 of the 12 with their centres within 2.0 mm of the GND land edge**; all 12 within
  **4.0 mm of the U1 centroid**. Place them as a field in the top GND pour immediately outboard
  of the land, ~1.0 mm pitch (do not go below 0.85 mm: 0.55 mm pads at the 0.1016 mm clearance
  of `4layer_2oz` need 0.65 mm centre-to-centre, and the pour must stay connected between them).
- **NO via-in-pad on the GND land.** Two in-pad vias are worth ~0.2 C/W (s3: 12 vs 16 vias =
  0.4 C/W) and would put open 0.30 mm holes in the part's only thermal and mechanical joint.
  In-pad is acceptable ONLY if resin-plugged-and-capped (JLC POFV) is separately ordered and
  priced at P10, and it is not recommended. Figure 47 draws in-pad vias; rules 7 and 8 say
  "around"; at 0.88 W the "around" reading wins.
- Vias tented on B.Cu (mask-covered), consistent with A11's clear bottom side.

**VIN side - area, because vias have nowhere to go:**

- **>= 60 mm^2 of contiguous F.Cu `+VIN` pour joined to the VIN land**, sitting over unbroken
  In1 GND. This is the substitute for DS41948 rule 8: the board has **no VIN plane** (In1 and
  In2 are both GND per rule 6, which outranks rule 8 on a single-rail converter), so the VIN
  land's only exit is lateral spreading in 2 oz top copper and then 0.4284 mm of prepreg down
  into In1. 60-80 mm^2 of pour is ~18-20 C/W of dielectric coupling; less than 40 mm^2 starts to
  bite. The Cin bank plus the Q1 drain supply this naturally - the instruction is to pour it,
  not to route it as a track.
- **`+VIN` stays VIA-FREE** (check_current's net-wide via rule, `constraints.json` power entry).
  A VIN via would land on GND-planed inner layers and buy nothing thermally anyway.

**Copper and planes:**

- **>= 200 mm^2 of contiguous F.Cu GND pour joined to the GND land** (unchanged in value, changed
  in reason: it is joined to the GND *land*, not to an EP land).
- **In1 and In2 solid GND, unbroken under U1 and under the entire Cin -> VIN -> GND loop.**
  No signal, no `+5V`, no plane split within **6 mm** of the U1 centroid. This is the single
  requirement that both rule 6 and the return-path argument depend on.
- **B.Cu GND pour under U1**, clear of SMT parts (A11); it is the via landing and the bottom
  radiating surface.
- `/SW` is also a heat exit but its area is bounded by EMI, not thermal: keep it small per
  buck.md s5. Do not grow the switch node for thermal reasons.

**Keepout / separation:** nothing new. `U1 <-> L1` 8 mm and `U1 <-> F1` 15 mm centroid
separations in `constraints.json placement.separation` stand and are unaffected.

**What P6/P7 must verify by review, because no gate tests it:** the 12-via count and their
radius, the 60 mm^2 `+VIN` pour, the 200 mm^2 F.Cu GND pour, and the unbroken In1/In2 under U1.
`check_thermal` will pass a board with none of these (s4).

## 9. Files changed by this re-check

| File | Change |
|---|---|
| `research/power.md` | s0 headline 1, s4 rewritten; old EP-based s4.3/s4.4 preserved inline as SUPERSEDED |
| `research/power.json` | `_headline[0]`, `thermal_constraints`, `_constraint_rationale`, `stackup_recommendation.why`, `layout_notes[3]`, `open[2]` |
| `architecture/constraints.json` | `thermal[0]._vias_basis` and `_dt_basis` rewritten (values `power_w` 0.95 / `dt_c` 55 / `min_vias` 12 UNCHANGED) |
| `architecture/stackup.md` | not edited by this task - s2.3/s2.4 are superseded by this document; see OPEN 1 |

## 10. OPEN

1. **`architecture/stackup.md` s2.3 and s2.4 still carry the EP story** ("the EP thermal-via
   array only has to reach In1", the +10 C neighbour allowance, "the 2-layer option is closed"
   on thermal grounds). They are superseded by s3/s6 of this document but were not edited -
   stackup.md is P2 architecture, not P1 research, and rewriting it is the architect's call.
   The conclusion it reaches (4L, 2 oz outer, JLC04162H-7628A) is unchanged and correct.
2. **h is the widest uncertainty in s3**, not the copper: 20 vs 40 W/m^2K moves theta_JA from
   40.8 to 28.3 C/W. Nothing in the verdicts turns on it - every case passes the part's limits -
   but no claim tighter than "Tj is 79-101 C at the 7 V corner" is supportable pre-bench.
3. **No psi_JT is published for this part**, so the usual post-fab verification
   (`Tj = T_top + psi_JT x P`) cannot be run as written. The fallback is a case-top thermocouple
   plus theta_JC = 5 C/W as an upper bound on the die-to-case delta (+4.4 C at 0.881 W).

## Sources

- `boards/buck-5v3a/parts/C3194571.pdf` - AP63356Q/AP63357Q, DS41948 Rev. 1-2, Sept 2020.
  Pages read visually for this document: p.4 (Absolute Maximum Ratings, Thermal Resistance +
  Note 6, Recommended Operating Conditions), p.5 (Electrical Characteristics: RDS(on), fsw,
  TSD), p.25 (Layout rules 1-9 + Figure 47).
- `boards/buck-5v3a/reports/u1-land-ruling.md` - the 9-land / no-EP ruling this document acts on.
- `boards/buck-5v3a/architecture/power_tree.md` s3 - the 0.881 W / 1.483 W loss table.
- `.claude/skills/ai-ee/scripts/check_thermal.py` - model source; `MODEL_2L` is documented as a
  1 oz / 2-layer calibration, `MODEL_ML` as 2 oz / 4-layer.
- JESD51-7 2s2p construction (2 oz outer trace layers, 1 oz solid inner planes; 1.6 mm total)
  and JESD51-3 coupon sizes (76.2 x 76.2 for bodies < 27 mm, 76.2 x 114.3 above) - used only to
  bound what Note 6's board was.
- Natural-convection correlations for a horizontal plate (Nu = 0.54 Ra^1/4 up, 0.27 Ra^1/4 down,
  L_c = A/P) and grey-body radiation at eps = 0.9, for the h band.
