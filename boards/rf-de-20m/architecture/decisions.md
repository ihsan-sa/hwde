# rf-de-20m - P2 decisions, rejections, open items, and the P8 sim plan

**AMENDED 2026-08-07 (P2-A).** D1 and D2 are amended with a retraction and a new
basis; D3, D6, D9 carry re-derived numbers; a new **D11** records the operating
point correction. Full derivations: `blocks.md` s0.

---

## D0 - AMENDMENT P2-A: what was retracted, and two further errors found

**RETRACTED.** The P1 `research/power.json` fragment supplied **Coss(er) 156 pF**
and **Rds(on) 22 typ / 42 max mohm**. The orchestrator read the EPC2019 datasheet
(rev (c)2021) directly. **The datasheet publishes no Coss(er), no Coss(tr) and no
Eoss anywhere** - the 156 pF was invented - and Rds(on) is **36 typ / 50 max mohm**.
The original RULING 2 conclusion, *"2 x Coss(er) = 312 pF lands almost exactly on
the required 317 pF, so the external shunt cap disappears"*, is void.

**ENDORSED: the orchestrator's method is right.** The charge-equivalent
`Coss(tr) = Qoss/V` is the correct basis for Class E, and the reasoning is worth
recording because the wrong choice here is a common error. The Class E drain
waveform is produced by **integrating current into charge** (`v(t) = V(Q(t))`), so
the equivalent linear capacitance is the one carrying the **same charge at the same
voltage**. `Coss(er) = 2.Eoss/V^2` is the equivalent for *hard-switching turn-on
loss*, is systematically lower (this part: ~119 pF vs ~158 pF, a 25% error), and
would have under-sized the shunt. The small-signal 110 pF is wrong by more, being
quoted at VDS = 100 V where Coss has already fallen - a constant 110 pF would imply
Qoss = 11 nC against the datasheet's 18 nC, confirming a 1.64x nonlinearity.

**ERROR 1 - the range.** `18 nC/100 V = 180 pF` is the average over **0 -> 100 V**;
this drain swings **0 -> 142.5 V**, and Coss keeps falling above 100 V. Two
independent extrapolations - a power-law fit anchored on Coss(100 V) *and*
Qoss(100 V), and a "flat above 100 V" bound - **agree to 1.5%**:

> **Coss(tr) = 158 pF typ / 205 pF max per FET over the real swing.**
> A pair supplies **316 pF typ / 410 pF max**, not 360 pF.

**ERROR 2, and the bigger one - the Sokal coefficient.** `0.1836/(omega.R)` is the
**Q_L -> infinity** constant. This board runs **Q_L = 5**, and
`research/refdesign-classE-stage.json` D9 already supplied the finite-Q_L
coefficients and said the infinite-Q_L ones are superseded. Cross-checked against
Sokal's published continuous-function fits:

| Coefficient | Sokal fit at Q_L = 5 | P1 fragment | Agreement |
|---|---|---|---|
| `P.R/Vdd^2` | **0.51663** | 0.51659 | **0.008%** |
| `C_shunt.omega.R` | **0.20935** | 0.20907 | **0.13%** |
| `C_series.omega.R` | 0.26906 | 0.63467 | **2.4x apart - fragment wrong (D11)** |

Two of three agree to 0.13%, validating both. **The frozen operating point itself
was computed with Q_L -> infinity constants on a Q_L = 5 design.**

**NET RESULT - the two errors pull opposite ways and the second dominates:**

| | Frozen | Orchestrator's fix | **P2-A** |
|---|---|---|---|
| Vdd | 40 V | 37.5 V | **40 V - frozen input preserved** |
| R_opt | 4.614 ohm | 4.06 ohm | **4.13 ohm** |
| C_shunt required | 317 pF | 360 pF | **403 pF** (+38-46 pF finite-choke term) |
| Coss(tr)/FET | (invented 156) | 180 pF | **158 typ / 205 max** |
| Pair supplies | 312 pF | 360 pF | **316 typ / 410 max** |
| External C0G | 5 pF | 0 pF | **87 pF, with 0-133 pF of range** |

**The bus voltage does not need to change**, and - more valuable - **the external
trim capacitor comes back.** The original ruling treated its disappearance as
elegance. It is a **defect**: Coss spread on this part is 110-150 pF (+36%), and
the external capacitor is the **only** mechanism that absorbs it. At 100% device
shunt a max-Coss part is unfixable without reworking etched copper.

## D1 - Build the layout for TWO paralleled EPC2019 (AMENDED - REINFORCED)

**Decision unchanged.** Mirrored pair, both populated, four 1206 C0G trim sites on
the drain node - **now populated (~87-133 pF), not DNP.**

**The real datasheet makes this ruling stronger.** With Rds(on) 36/50 mohm
(65/90 mohm hot) rather than the retracted 22/42:

```
ONE FET, nominal: P_FET = 11.17 W  ->  theta_JB rise alone = 84 C
Tj with a HYPOTHETICAL 0 C/W heatsink = 40 + 11.17 x 10.5 = 160 C
```

> **A single FET exceeds the 150 C ABSOLUTE MAXIMUM with a perfect heatsink.**

That is qualitatively stronger than the pre-amendment finding (138 C against a
125 C *target*). **There is no heatsink, TIM, via array or copper weight that saves
a one-FET build.** At the specified 0.7 C/W: **175 C nominal, 216 C at the
max-datasheet corner.**

**The pair closes** (theta_JB 3.75, theta_BS 1.5, theta_HS 0.7 C/W):

| Corner | P_FET pair | **Tj (2 FET)** | Tj (1 FET) |
|---|---|---|---|
| BEST | 5.75 W | **78 C** | 118 C |
| **NOM** | 11.25 W | **114 C** | **175 C** |
| **MAX-DATASHEET CORNER** (max Rds AND max Coss) | 14.56 W | **133 C** | 216 C |
| COMPOUNDED WORST | 20.19 W | 170 C | 260 C |

**11 C of margin at the design target, 17 C under the absolute maximum at the
max-datasheet corner.** The compounded worst exceeds abs max - mitigation below.

**RETRACTED sub-argument: "k = 2 is exactly the ZVS ceiling."** That rested on the
invented Coss(er); the real ceiling is `403/158 = 2.55`, so three FETs are not
forbidden outright (they would need R -> 3.5 ohm, Vdd -> 37 V). **k = 2 survives on
a stronger, quantitative argument:**

```
P_FET(N) = 5.48/N (conduction) + 2.42.N (Coss hysteresis) + turn-off + 2.52 + gate
  N=1: 11.17 W     N=2: 11.25 W     N=3: 13.16 W
```

**Paralleling does not reduce dissipation at all - total loss is flat between one
and two FETs, because conduction halves while Coss hysteresis doubles. What it
reduces is THERMAL RESISTANCE**, halving theta_JB and theta_BS at zero loss
penalty. N = 2 buys the full 2x for free; N = 3 pays +1.9 W for a further 1.5x
*and* a three-way gate-symmetry problem that cannot be solved by mirroring.

**A single larger LCSC GaN still cannot beat the pair.** Die area scales
Rds ~ 1/A, Coss ~ A, RthJB ~ 1/A, so a single 2x die is the same design point,
saving one package's thermal resistance and paying one part's extra hysteresis.
**P3 may reopen only with a part meeting all three of: Coss(tr) <= 300 pF over a
0-142.5 V swing (Qoss <= 43 nC at 142.5 V), Rds(on) <= 20 mohm typ, RthJB
<= 4.0 C/W.**

**Current-sharing and gate-ringing: unchanged and reinforced.** Static sharing
self-corrects via the positive Rds(on) tempco - and the real 36-50 mohm spread
makes the shared thermal island *more* important than the retracted 22-42 implied.
Dynamic sharing is far safer than the general paralleling case because **Class E is
soft-switched**: at turn-on the drain is at ~0 V so there is no discharge spike to
hog, GaN has no body-diode reverse recovery, and at turn-off the current commutates
into a shunt capacitance distributed across both dies. The residual risk is
differential-mode gate oscillation, mitigated by individual gate resistors per FET
per polarity, a shared symmetric source star, and the D6 loop budget.

**Cost:** +$3.93 BOM at the current LCSC price (**was $2.17 - the part is out of
stock and repriced**); -1.1 pt efficiency versus a one-FET build that does not
thermally exist; mirror-symmetry layout discipline that cannot be retrofitted.

**Residual risk, stated plainly.** With the pair, **Coss hysteresis is the dominant
FET loss term (4.83 W of 11.25 W)** and rests on an assumed **10% of stored energy
that EPC does not publish** - the same class of gap that produced the retracted
Coss(er). At 15% the pair reaches ~13.7 W and Tj ~127 C. **SIM-5 measures it.**

**FREE MITIGATION - the one genuinely new piece of engineering in this amendment.**
**ZVS in Class E is a property of the NETWORK, not of Vdd**: the design equations
are linear in Vdd and the ZVS/ZdVS conditions constrain only the *shape* of the
current waveform, fixed by L_s, C_s, C_shunt, R and f. So the bus can be backed
down at bring-up **without losing ZVS**, trading power for junction temperature at
zero rework:

| Vdd | P_out | Vds pk | P_FET (max-corner) | Tj @ 0.7 C/W |
|---|---|---|---|---|
| **40 V** | 200 W | 142 V | 14.56 W | **133 C** |
| 38 V | 180 W | 135 V | 13.43 W | 126 C |
| **36 V** | **162 W** | 128 V | 12.34 W | **119 C** |
| 34 V | 144 W | 121 V | 11.30 W | 112 C |

**If the delivered reel measures at the max corner, back the bus to 36 V and accept
~160 W.** The corollary matters as much: **Vdd is NOT a ZVS knob** - it cannot
correct a shunt-capacitance error. Duty cycle and the trim bank are for that.

**First bring-up step:** measure DC input power at 200 W out and thermal-image both
dies. Above ~14 W at 40 V, derate the bus per the table.

## D2 - C_shunt (AMENDED): 403 pF required, 316 pF from the pair, ~87 pF external

**All three prior positions are superseded.** `output-network.json`'s 224 pF (from
the brief's 110 pF Coss), the original ruling's "no external cap" (from the invented
156 pF Coss(er)), and the orchestrator's 360 pF (from Qoss/V at the wrong voltage
range with the wrong Sokal coefficient) are all withdrawn. The basis is now:

```
Required : C_shunt = 0.20907/(omega.R) = 403 pF at R = 4.13 ohm    [Sokal, Q_L = 5]
           + 38-46 pF if Sokal's finite-DC-feed term applies  ->  403-449 pF
Supplied : 2 x Qoss(142.5 V)/142.5 V = 316 pF typ / 410 pF max
External : ~87 pF nominal; C203-C206 give 0-133 pF in 33 pF steps
```

**C203-C206: four 1206 C0G 1 kV sites, nominal populate 3 x 33 pF, sited IN the
power loop.** No longer DNP. **The bank is load-bearing**: a max-Coss pair supplies
410 pF against a 403-449 pF requirement, so the bank simply empties.

**ZVS knobs, in order of preference:** (1) **duty cycle** - free, on the generator,
the correct first move; (2) the trim bank; (3) the tank copper - rework, and the
reason the spirals' trimmability is an architectural asset; (4) frequency - a
diagnostic only. **Not on the list: bus voltage** (D1).

## D11 - NEW: the frozen operating point was computed with the wrong Sokal constants

**R_opt moves from 4.614 to 4.13 ohm** and the whole tank moves with it. The frozen
brief used `P = 0.5768 Vdd^2/R` and `C_shunt = 0.1836/(omega.R)`, which are the
**Q_L -> infinity** values; at Q_L = 5 they are **0.51659** and **0.20907**.

| Quantity | Frozen | **P2-A** | Change |
|---|---|---|---|
| R_opt | 4.614 ohm | **4.13 ohm** | -10.5% |
| C_shunt | 317 pF | **403 pF** | +27% |
| L_s | 184 nH | **164 nH** | -11% |
| C_s | 447 pF | **518 pF +/-5%** | +16% |
| L_m | 115 nH | **110 nH** | -5% |
| C_m | 500 pF | **530 pF** | +6% |
| Q_m | 3.136 | **3.331** | |
| I_tank | 6.58 A rms | **6.96 A rms** | +5.8% |
| I_Cm | 6.27 A rms | **6.66 A rms** | |
| I_dc / I_sw,rms | 5.88 / 9.0 A | **5.96 / 9.17 A** | |
| Vds,pk | 142.5 V | **142.5 V** | unchanged (depends only on Vdd) |
| Magnetics loss | 1627/Q W | **1666/Q W** | +2.4% |

**The magnetics losses barely moved**, because `P_Ls = 200.Q_L/Q_ind` and
`P_Lm = 200.Q_m/Q_ind` are **independent of R** - the tank current rises exactly as
fast as the reactance falls. Tank conductor widths grow ~12% (7.2 mm, was 6.4).

**The lower L targets are geometrically helpful:** 164 nH at the same 30-34 mm OD
needs a *wider* spiral trace (~2.5-3 mm rather than 1.5 mm), which is exactly what
both Q and the thermal-area rule want.

**One coefficient in the P1 fragment is wrong and is NOT adopted.** Its
`C_series.omega.R = 0.63467` gives C_s = 1222 pF and a net series reactance of
**3.4 R** - not a Class E network. Sokal's published fit gives **0.26906 -> 518 pF**
and **1.283 R**, which is right and which also agrees within 3.5% with the
independent `X_net = 1.1525 R` relation. **C_s carries +/-5% until SIM-4 rules**;
keeping it a 9-part parallel bank means it can be trimmed by depopulation.

## D3 - L_s and L_m are etched PCB air-core spirals (values re-derived)

**Adopted in full.** No LCSC part class closes L_s: molded power inductors have the
current but Vishay's own datasheet caps that family at "up to 5.0 MHz" (Q 20-40 at
20 MHz = **25-50 W in one part**); genuine high-Q RF chip inductors have the
frequency but are rated **120-140 mA against 6.96 A**. **Paralleling rescues
neither** - `Q_total = Q_each` exactly. Total magnetics loss is **1666/Q watts**.

Re-derived: **L_s 164 nH, L_m 110 nH**; losses **1000/Q** and **666/Q**, essentially
unchanged (see D11).

**"First-class" is a pipeline instruction:** BOM line with no LCSC code marked
*PCB feature - do not place* (P3); a schematic symbol so its nets are real (P4); a
custom footprint carrying the copper, courtyard = thermal footprint (P4/P5); an
explicit `place_edit` + lock plus a hand-added four-layer keepout (P6); geometric
verification (P8). Copper no tool knows about gets routed over and poured under.

**SPIRAL-1..6 in `blocks.md` s4.3.** The three easiest to get wrong:
**SPIRAL-1** solves each spiral jointly for L, `Q >= 120`, **and copper area
`>= P / 7 mW.mm^-2`** (thermal, not electrical); **SPIRAL-3: L_m needs
>= 950 mm^2**, nearly as large as L_s despite being 67% of the inductance;
**SPIRAL-2 (recommended, verify-later)** parallels the winding on F.Cu *and* B.Cu -
**16.7 W -> ~10 W, ~+2 pts of board efficiency for zero BOM cost**, not banked, and
every number in `power_tree.md` is quoted for the conservative single-layer case.

**Fab consequence: high-Tg FR4, TG155+** - spiral copper runs 100-140 C. An
**order-time option, not expressible in `stackups.yaml`** - carry it to P10 or the
board is made in standard FR4.

## D4 - The two-zone floorplan: the conflict was an artefact (unchanged)

**The power loop ENDS at the drain node and the tank BEGINS there.** One boundary,
nothing straddles it, so "L2 unbroken under the power loop" and "no plane under the
spirals" apply to **disjoint regions**.

| Zone | x | In1 / In2 / B.Cu | Heatsink |
|---|---|---|---|
| **A** power / heatsink | 0 - 48 | **solid GND, all three** | **yes**, land [5,10,36,70] |
| **B** magnetics | 48 - 88 | **none** (SPIRAL-4 bridges only) | **NEVER** |
| **C** output | 88 - 100 | **solid GND, all three** | no |

`planes_gen` has **no void or keepout support**, so zone B is unpoured by
construction (six entries, three layers, two regions each). Two things must be hand
work: **KiCad rule areas over both spiral courtyards on all four layers** at P6,
verified at P8; and **HS-1/HS-2/HS-3** reaching whoever specifies the heatsink.

**Board outline 100 x 80 mm, and it must stay soft.** If P6 cannot fit both spirals
at their SPIRAL-1 areas, **grow the board in +x to 110-120 mm - do not shrink a
spiral.** Growing past 100 mm leaves JLC's cheapest 4L tier, ~+$3-6/board at qty 5.
**Do not pass a hard `--outline` cap at P5.**

## D5 - Stackup `JLC04161H-1080B`, 1 oz outer, TG155, ENIG, POFV (unchanged)

Chosen for **one number: the 0.2444 mm L1-L2 dielectric**, which is what makes
EPC's stacked self-cancelling power loop possible (~65% lower loop inductance;
1.6 -> 0.4 nH cut overshoot from 100% to 30% of Vin). On this board loop inductance
is the entire margin behind the 1.40x voltage derate. TI reaches the same
conclusion independently (LMG1020DS s10.1: four layers or more is *required*).

**1 oz, not 2 oz.** Skin depth at 20 MHz is 14.6 um, so 1 oz is already ~2.4 skin
depths and 2 oz buys ~15% - and the 2 oz lamination **doubles the L1-L2 dielectric
and therefore the power-loop inductance**. Strictly worse.

**Three order-time options that each buy a named failure mode out of the design:**
**TG155+**, **ENIG not HASL** (EPC AN009), **epoxy-filled-and-capped via-in-pad**
(LMG1020 GND/VDD). None should be traded for price.

## D6 - Gate-loop budget (AMENDED): 0.48 nH per FET

`power.md` s8.3 said <= 0.3 nH; `refdesign-classE-stage.json` D4 gives EPC's
criterion `L_G <= 1/4 (R_G + R_src)^2 C_GS`. **The refdesign criterion wins** - the
0.3 nH figure assumes a zero-resistance loop, and TI's mandatory >= 2 ohm resistor
makes it resistance-limited (peak gate current **1.6 A per FET, not 7 A**).

**The amendment TIGHTENS the number.** The retracted Qg of 2.4 nC implied
C_GS ~ 350 pF; the datasheet gives **Ciss 200 pF and Crss 0.7 pF -> C_GS ~ 199 pF**:

```
L_G <= 0.25 x 3.1^2 x 199 pF = 0.48 nH        (was 0.84 nH)
```

**This is the tightest layout spec on the board.** Two 0603s in parallel contribute
~0.15-0.2 nH, leaving ~0.3 nH for vias and interconnect - achievable with via-in-pad
and a <= 2 mm gate run, but without slack. **Stated fallback: raise R_G to 3 ohm,
relaxing the budget to 0.84 nH**, at ~+0.3 W turn-off loss and ~+1.6 C of Tj. Take
it consciously.

**Matching is +/-0.1 nH and is NOT a timing spec.** Skew is benign here: at turn-on
the drain is at ~0 V so an early device has nothing to hog; at turn-off a 100 ps
skew costs ~0.04 W and the drain is held near 0 V by whichever FET is still on.
**Matching exists to damp the differential mode and equalise static sharing**, and
mirroring delivers it free. Do not length-match electrically - FR4 is ~6.7 ps/mm.

**Four legs, 2 x 4.0 ohm 0603 in parallel each.** The real Qg of 1.8 nC drops the
pair's gate-loop energy to **0.36 W** (was 0.58 W), so each 0603 sees 0.029 W -
comfortable even derated at 100 C - and the parallel pair halves the leg inductance,
which matters more now.

## D7 - RULING: do not build the 50 ohm microstrip to the SMA (unchanged)

`se_50` for this lamination is **0.4332 mm on F.Cu over In1 at h = 0.2444 mm,
er 4.05 (assumed)**. Stated for the record and **deliberately not built**:
`/tank/RFOUT` is a ~3.2 A DC-equivalent conductor at the AC/DC factor of 2.5, which
IPC-2221's external curve puts at a **50-75 C rise**, while at 20 MHz a 15 mm run
is **lambda/550** and perturbs the load by **< 2%** - inside a trimmable L-match.

**Route as a wide F.Cu pour (>= 3 mm) over solid In1 GND, <= 15 mm.** Declared under
`power` (7.0 A), not `high_speed` with `impedance_ohm` - `rules_gen` **only solves
impedance for differential pairs**, so a lone single-ended `impedance_ohm` emits no
width rule at all. **Contradicts a frozen requirement; raised as OPEN-2.**

## D8 - The drive input is DC-coupled, and that is a ruling (unchanged, reinforced)

AC coupling's DC restore pins the waveform's average at the bias point, so at
D = 0.4 with a 2.5 V bias both logic levels sit above the ~1.4 V threshold and
**the FETs never turn off.** Duty is the primary Class E tuning knob - and after
P2-A it is also the **primary ZVS trim** (D2), which makes protecting it more
important, not less. The generator must output **unipolar 0 to +5 V** (**OPEN-1**).
Termination is **2 x 100 R 0805 in parallel** at the connector.

## D9 - Node voltages (re-derived at R = 4.13)

The brief's "tank L/C see ~215 V peak" is the voltage **across L_s**, not a node
voltage. Node peaks: `/SW` **142.5 V** (unchanged - depends only on Vdd),
**`/tank/TANK_A` 156 V (still the highest node, 14 V above the drain)**,
`/tank/RFOUT` 141 V, `/tank/TANK_B` 41 V. Element-across values, which node
arithmetic cannot express and which go into **`voltage_pairs`**: **L_s 203 V pk,
C_s 151 V pk, L_m 135 V pk**. Node arithmetic would give 37 V for the L_s pair -
5.5x too low.

## D10 - Sheets and net names (unchanged)

Three sheets (`hk` / `stage` / `tank`) mapped 1:1 onto the floorplan zones - on a
~60-part board with one function, the floorplan is the only organising principle
that earns its keep. Refdes 100/200/300 blocks, `#PWR` bases 100/200/300.

**Exactly one signal net crosses a sheet boundary (`/SW`), and P4 must place a
root-sheet local label spelled `SW`** or six `constraints.json` entries silently
stop matching. **The OUTH/OUTL legs are named `_ON`/`_OFF`, not `_H`/`_L`**, because
`detect_diff_pairs` auto-pairs `high_speed` nets ending `_H`/`_L`.

---

## Rejected, with reasons (do not re-explore)

| Rejected | Reason |
|---|---|
| **Class DE half-bridge** | No LCSC/JLC gate driver can switch a 20 MHz half-bridge. **Owner ruled Class E at P0.** |
| **A single EPC2019** | **Tj 160 C with a HYPOTHETICAL 0 C/W heatsink - above the 150 C abs max.** No heatsink saves it. **D1.** |
| **Three or more paralleled FETs** | Total FET loss RISES (13.16 W vs 11.25 W): conduction halves but Coss hysteresis multiplies. Also needs R -> 3.5 ohm / Vdd -> 37 V and a three-way gate match that cannot be mirrored. **D1.** |
| **A single larger LCSC GaN** | Same design point as the pair; qualifying window in **D1** if P3 wants to try. |
| **Coss(er), or Coss at 100 V, as the Class E shunt basis** | Coss(er) is the hard-switching *energy* equivalent (~119 pF here, 25% low); the 110 pF small-signal figure is quoted at 100 V where Coss has already fallen. Class E is charge-driven. **D0.** |
| **Qoss/V evaluated at 100 V (180 pF)** | The drain swings to 142.5 V and Coss keeps falling; over the real swing it is **158 pF**. **D0.** |
| **Lowering the bus to 37.5 V** | Was driven by the two errors above. With them fixed, two FETs fit at **40 V** with 87 pF of external trim - and a lower bus would have *removed* trim range. **D0/D11.** |
| **Sokal's Q_L -> infinity constants (0.5768 / 0.1836)** | This board runs Q_L = 5. **D11.** |
| **The P1 fragment's `C_series.omega.R = 0.63467`** | Gives a net series reactance of 3.4 R - not a Class E network. **D11.** |
| **4 x 56 pF = 224 pF external C_shunt** | From the brief's refuted 110 pF Coss. **D2.** |
| **"No external shunt capacitor" (the original ruling)** | Rested on the invented Coss(er), and would have been a defect anyway - the external cap is the only absorber of the 110-150 pF Coss spread. **D0/D2.** |
| **Catalog inductors for L_s / L_m** | Q 20-40 at 20 MHz, or 120-140 mA rated. Paralleling cannot fix a Q ceiling. **D3.** |
| **A PCB spiral for the RF choke L201** | Its loss is `I_dc^2 x DCR`; a 4-turn 25 mm spiral is ~100 mohm = 3.6 W against a 0.89 W budget. |
| **A smaller RF choke to ease sourcing** | Below 0.82 uH the ideal Class E equations stop holding, *and* Sokal's finite-DC-feed term raises the required shunt. **Escape is 2 x 0.47 uH in series.** |
| **2 oz outer copper** | +15% on AC resistance, and it forces a lamination with **twice** the L1-L2 dielectric. **D5.** |
| **The 0.4332 mm 50 ohm microstrip** | 50-75 C rise for an impedance that perturbs the load <2%. **D7.** |
| **AC-coupling the drive input** | Destroys duty-cycle control, which is now also the primary ZVS trim. **D8.** |
| **THT bulkhead SMA jacks / leaded electrolytics** | Bottom-face solder joints break the flat heatsink land. |
| **Any protection part** | Owner-acknowledged at P0 Q11. Response: *"waived, owner-acknowledged at P0"*. |
| **A negative gate bias or clamp scheme** | EPC's own guidance is 5 V ON / 0 V OFF; the fix path is loop inductance plus the >= 2 ohm floor. |

---

## OPEN - items needing a human ruling or a later phase

**OPEN-1 (owner, before bring-up).** *What DC offset does the generator put out?*
The design requires **unipolar 0 to +5 V**; bipolar +/-2.5 V violates the LMG1020's
-0.3 V input abs max. AC coupling is not an option (**D8**). Confirm and silkscreen.

**OPEN-2 (owner, checkpoint 1).** *Hold the frozen "controlled-impedance 50 ohm to
the connector" requirement?* **Recommend relaxing it** (**D7**). Tradeoff: met in
substance, not literally, and no pipeline check reports a 50 ohm number. If wanted
literally, the implementation is a **grounded coplanar waveguide** hand-solved and
verified against **JLC's own calculator** (the pipeline's `impedance.py` solves
surface microstrip only and would give a silently wrong CPWG number).

**OPEN-3 (owner, checkpoint 1).** *Accept 100 x 80 mm with the outline soft, and
pre-authorise P6 to grow to 120 x 80 if a spiral cannot reach its SPIRAL-1 area?*
**Recommend yes.** ~+$3-6/board past JLC's cheap 4L tier. **No hard `--outline` cap.**

**OPEN-4 (owner, NEW at P2-A - informational, low stakes).** The amended operating
point predicts **200 W at a bus somewhere in 38-40 V** rather than exactly 40.0 V,
because the two Sokal power coefficients bracket the output at 200-223 W for
R = 4.13 ohm at 40 V. **Bring-up sets the bus to hit exactly 200 W.** No board
change; recorded so nobody treats a 38.5 V bench setting as a fault.

**OPEN-5 (P3, blocking the footprint).** **EPC2019 land pattern and stencil
dimensions verbatim from the datasheet.** The package is **2.77 x 0.95 mm with a
7-bar solder-bar row**; the bars are ~0.2 mm wide, **too narrow for in-pad vias**,
so the >= 10-via array goes *beside* the lands. SMD (solder-mask-defined), not NSMD.

**OPEN-6 (P3/P10, NEW at P2-A).** **EPC2019 is OUT OF STOCK at LCSC (stock 0,
price $2.17 -> $3.93).** Owner approved continuing the design and **holding the
order**; P10 re-verifies stock. Two units per board x 5 boards = 10 needed. If it
does not return, the D1 qualifying window is the search specification.

**OPEN-7 (P3).** **L201 is the hardest part on the BOM**: >= 0.82 uH, SRF >= 80 MHz,
DCR <= 25 mohm, I_sat >= 12 A, >= 8 A rms. Escape: **2 x 0.47 uH in series.** Do not
silently drop below the floor.

**OPEN-8 (P9/P11).** **LCSC brands the LMG1020YFFR "Tokmas", not TI.** Authenticity
check on receipt; Tokmas parts recur across this BOM.

**OPEN-9 (mechanical, off-board).** **HS-1 tightened to theta_HS <= 0.7 C/W**
(from 1.4) **measured**, plus HS-2 and HS-3. If the heatsink fails HS-2 and reaches
a spiral, that spiral becomes a shorted turn and the magnetics loss roughly doubles
- **a mechanical error presenting as an electrical failure.**

**OPEN-10 (P5/P6, verify-later).** `theta_BS = 1.5 C/W` for the pair is **assumed,
not simulated**, and carries 17 C of the 85 C junction budget.

**OPEN-11 (P8, verify-later).** **SPIRAL-2** (paralleled F.Cu + B.Cu windings) is a
computed, unmeasured claim: ~1.6-1.8x Q, 16.7 -> ~10 W. Upside, not a dependency.

**OPEN-12 (P8, NEW at P2-A).** **C_s = 518 pF carries +/-5%** because the P1
fragment's `C_series` coefficient is refuted and the replacement rests on Sokal's
published fit. **SIM-4 is the arbiter.** Keep the bank a parallel array so it is
trimmable by depopulation.

---

## P8 `sim` gate - benches with numeric pass windows (AMENDED)

Class E is entirely about whether the drain reaches zero before turn-on, and after
P2-A **two load-bearing inputs are derived rather than published** (Coss(tr) by
extrapolation, the Sokal coefficients by cross-checked fit). The sim gate is where
that is settled. Each bench is an ngspice `.cir` in `kicad/sims/` with a
`<name>.bounds.json` sidecar of `{measure, min, max, severity}` per `sim_run.py`.

### SIM-1 `classe_zvs_nominal` - the bench that decides whether the board works (error)

Time-domain: **Vdd 40 V, 20 MHz, D = 50%, R_load 50 ohm, C_shunt = 2 x EPC2019
nonlinear Coss + 87 pF C0G, L_s 164 nH at its computed Q, C_s 518 pF, L_m 110 nH,
C_m 530 pF, choke 0.9 uH.** 200 cycles; measure over the last 10.

| measure | min | max |
|---|---|---|
| `vds_at_turnon_v` | -2.0 | **5.0** |
| `dvds_dt_at_turnon_v_per_ns` | -0.2 | +0.2 |
| `pout_w` | **190** | 210 |
| `vds_peak_v` | - | **155** |
| `idc_a` | - | 6.5 |

`vds_at_turnon <= 5 V` is ZVS; the `dvds/dt` window is ZdVS, which separates true
optimum operation from a lucky zero-crossing. `vds_peak <= 155 V` holds a 1.29x
derate on the 200 V part.

### SIM-2 `cshunt_sweep` - validates the whole amended basis (error)

**First measure validates the extrapolation the amendment rests on**, then sweeps.

| measure | min | max |
|---|---|---|
| `coss_tr_per_fet_pf` (from the vendor nonlinear model, integrated 0 -> 142.5 V) | **140** | **180** |
| `vds_at_turnon_worst_v` across a **300 -> 430 pF** device sweep, untuned | - | 25.0 |
| `trim_pf_needed` to restore SIM-1 across the sweep | **0** | **133** |
| `duty_adjust_needed_pct` | - | 6.0 |

**Must pass before P4 fixes any tank value.** If `coss_tr_per_fet_pf` lands outside
140-180 pF, the operating point in D11 must be re-solved. If `trim_pf_needed`
exceeds the bank's 133 pF range, the bank needs more sites.

### SIM-3 `gate_symmetry` - validates the D1 layout requirement (error)

Two-FET model, **gate-loop mismatch +/-0.15 nH** (1.5x the design tolerance),
2 ohm per leg, **Ciss 200 pF**.

| measure | min | max |
|---|---|---|
| `id_imbalance_pct` (peak drain current, FET-to-FET) | - | **15.0** |
| `vgs_max_v` | - | **5.75** |
| `vgs_min_v` | **-4.0** | - |
| `vgs_ring_residual_pct_at_2ns` | - | 10.0 |

The Vgs window is the **EPC2019's** -4 / +6 V rating, not the LMG1020's 5.75 V pin
rating - the FET is the tighter limit, with 1 V of headroom at 5 V drive.

### SIM-4 `tank_match` - AC transfer, harmonics, spiral coupling, and the C_s arbiter (error)

AC sweep 1-200 MHz from the drain into the load network plus a time-domain harmonic
measurement at the load. **Include the L301-L302 mutual coupling k** from the placed
geometry (SPIRAL-5).

| measure | min | max |
|---|---|---|
| `zin_mag_20m_ohm` (target 4.13 +/-10%) | **3.72** | **4.54** |
| `zin_phase_20m_deg` | 25 | 45 |
| `x_net_series_over_r` (the C_s arbiter: 1.283 expected, 3.4 refutes) | **1.0** | **1.6** |
| `h2_dbc` | - | **-20** |
| `h3_dbc` | - | **-33** |

`x_net_series_over_r` **settles OPEN-12**. Harmonic windows come from Sokal's own
Q_L ~ 5.1 figures; they are far short of any transmit compliance mask, which is why
this board is **dummy-load only**.

### SIM-5 `loss_split` - feeds the thermal model and closes D1's stated risk (error)

Extract the loss allocation (conduction / Coss hysteresis / turn-off overlap / ZVS
residual) rather than carrying the bracket.

| measure | min | max |
|---|---|---|
| `p_fet_pair_typ_w` | - | **13.0** |
| `p_fet_pair_maxcorner_w` | - | **16.0** |
| `p_coss_hysteresis_w` | - | **7.0** |

**13.0 W and 16.0 W are the numbers the 0.7 C/W heatsink and the 125 C Tj target
were solved against.** `p_coss_hysteresis_w` carries D1's stated risk: it rests on
an assumed 10% of stored energy that EPC does not publish, and with the pair it is
the **dominant** FET loss term.

### SIM-6 `gate_loop` - the +5 V rail is an inductance spec (warning)

VDD loop 0.3 nH / gate loop 0.48 nH, 100 nF + 10 nF bypass, Ciss 200 pF, Qg 1.8 nC.

| measure | min | max |
|---|---|---|
| `vdd_sag_mv` | - | 250 |
| `vgs_rise_10_90_ns` | - | 1.5 |

Advisory: it validates the decoupling and placement choice rather than a value.

### SIM-7 `bus_derating` - NEW at P2-A, confirms the free mitigation (warning)

Re-run SIM-1 at **Vdd = 40 / 38 / 36 / 34 V with the network unchanged**, to confirm
the claim that **ZVS is Vdd-independent** and that the bus is a clean power/thermal
derating knob (D1).

| measure | min | max |
|---|---|---|
| `vds_at_turnon_v` at every bus point | -2.0 | **5.0** |
| `pout_w` at 36 V | **150** | 175 |

If ZVS degrades with Vdd, the derating ladder in D1 is void and the thermal
worst-case mitigation must be re-planned.
