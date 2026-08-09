# rf-de-20m P8 - the SPICE bench, and what it says about ZVS

Authored 2026-08-08 by the sim-analyst. Six testbenches in `kicad/sims/`,
run by `scripts/gate.py --gate sim kicad/sims`.

---

## STATUS 2026-08-08: **THE FIX IN s1 HAS BEEN APPLIED. THIS IS FIX a3.**

**Everything below this block describes the board BEFORE the fix, and is the
evidence FOR it. Do not read it as a description of what ships.**

The generators now build the recommended populate. `kicad/gen/tank.py` and
`kicad/gen/stage.py` are the source of truth and both carry the derivation:

| site | was | **now** | effect |
|---|---|---|---|
| C308, C309 | 56 pF | **DNP** | |
| C320 | DNP | **27 pF populated** (`C541492`) | **C_s 504 -> 419 pF** |
| C203 | 56 pF | **DNP** | **C_shunt bank 83 -> 27 pF** |

Nothing else changed. No new part, no new land, **no netlist change at all** -
the three sites already existed and only their `Variant=DNP` field moved, so
the board's copper, placement and DRC residual are untouched. `parts.json`
quantities follow: the 56 pF line goes 18 -> 15 populated of 21 sites, the
27 pF line 2 -> 3 of 6.

The benches were re-based onto the new populate and re-run. **"As built" in
every deck now means C_s 419 pF / bank 27 pF**, and the retired 504/83 pair is
kept as a GATED NEGATIVE CONTROL in `cshunt_sweep.cir` (variant C) and
`tank_match.cir` (variant C) - it must still fail, or the decks have lost the
ability to see the failure they were written to find.

    gate sim: FAIL (1 failing / 4 total) - 1 error, 3 warning, 6 testbenches
    was       FAIL (8 failing / 11 total)

| bench | result |
|---|---|
| `coss_charge` | **pass** |
| `classe_zvs_nominal` | **pass** (1 warning: the architecture's own +/-0.2 V/ns) |
| `cshunt_sweep` | **pass** |
| `tank_match` | **pass** (2 warnings, both documented deviations) |
| `gate_symmetry` | **pass** |
| `bus_derating` | 1 **error**: `vds_pk_40v_v` 172.5 V - see below |

**The ZVS answer, measured on the board as it now ships, at the 30 V bench:**

| measure | window | **measured** | was |
|---|---|---|---|
| `vds_at_turnon_v` | -2.0 .. 5.0 | **1.36 V** | 15.60 **FAIL** |
| `dvds_dt_at_turnon_v_per_ns` | -2.0 .. 2.0 | **-1.21 V/ns** | -5.89 **FAIL** |
| `pout_w` | 90 .. 140 | **113.8 W** | 53.40 **FAIL** |
| `vds_peak_v` | <= 155 | **122.3 V** | 102.5 |
| `x_net_series_over_r` | 1.0 .. 1.6 | **1.285** (target 1.283) | 2.00 **FAIL** |
| `h2_dbc` / `h3_dbc` | <= -20 / <= -33 | **-28.4 / -44.1** | -27.8 / -49.9 |
| `id_corner_imbalance_pct` | <= 40 | **10.6 %** | 62.4 **FAIL** |
| `idc_a` | <= 5.0 | 3.93 A | 1.86 |

and the negative controls still fire: the retired populate re-measures
**15.47 V** at turn-on and **53.4 W** (`cshunt_sweep` variant C), and
**X_net/R 2.002** (`tank_match` variant C).

Two second-order results worth carrying:

* **The gate loop got BETTER, because ZVS got better.** With the fixed tank,
  `gate_symmetry` measures VGS max **4.907 V** (was 5.037), VGS min **-0.167 V**
  (was -0.193) and off-state VGS **0.057 V** (was 0.122) against a 0.8 V
  threshold - 14x margin. The 6R8 variant now buys **0.0005 V** of undershoot
  margin instead of 0.063 V, so the 4R7 revert is settled twice over.
* **The C_s bank's per-part duty rose.** Current divides in proportion to
  capacitance, so seven populated 56 pF parts carry **0.93 A rms** each instead
  of nine carrying 0.77 A (+21 %, ~150 mW instead of ~105 mW). Inside a 1 kV
  C0G 1206's capability; the bank's temperature rise is a **bring-up
  measurement**, not an assumption.

**The one remaining error is a BENCH CONSTRAINT, not a board defect.**
`vds_pk_40v_v` = 172.5 V against the 155 V (1.29x) derate line. It is the
s4/SIM-7 finding, unchanged and unfixed on purpose: a populate trimmed at 30 V
is under-shunted at 40 V, so **one populate cannot serve both bus points**. At
the owner's declared 25-30 V bench the peak is 98.2-122.2 V and the point is
moot; at the H4-ruled 36 V it is 152.1 V, still inside. The bound was NOT
weakened to make the gate green - **the owner should either declare the bus
ceiling at 36 V (a bench setting, zero board change) or re-populate C203 at
56 pF and re-run this bench before ever running 40 V.**

    reports/sim.json      full sim_run report: every bench, every measured value
    reports/gate-sim.json the gate's own report (failing findings only)

---

## The original analysis follows, unedited. It is the evidence for the fix.

    gate sim: FAIL (8 failing / 11 total) - 8 error, 3 warning, 6 testbenches
    (the state of the board BEFORE fix a3)

| bench | bounds | result | run |
|---|---|---|---|
| `coss_charge` | 8 | **pass** | 0.9 s |
| `classe_zvs_nominal` | 10 | 3 error, 1 warning | 2.9 s |
| `cshunt_sweep` | 12 | 2 error | 14.5 s |
| `tank_match` | 16 | 1 error, 2 warning | 0.6 s |
| `gate_symmetry` | 14 | 1 error | 15.0 s |
| `bus_derating` | 13 | 1 error | 9.6 s |

The eight errors are **five distinct facts**, not eight:

1. the as-built board misses ZVS - 3 errors (`vds_at_turnon_v` and
   `dvds_dt_at_turnon_v_per_ns` in SIM-1, `vds_ton_asbuilt_v` in the sweep, which
   re-measures the baseline so the sweep cannot drift away from SIM-1);
2. the network is detuned by the zone-B tank bridge - 1 (`x_net_series_over_r`);
3. that detune costs half the output power - 2 (`pout_w` on the board, and
   `pout_bank0_w` on the bring-up move `review-board.md` W2 recommends);
4. the lost soft-switching breaks two-die sharing at the datasheet device corner
   - 1 (`id_corner_imbalance_pct`);
5. a populate trimmed at 30 V over-stresses the drain at 40 V - 1
   (`vds_pk_40v_v`).

Items 1-4 are all fixed by the single populate change in s1. Item 5 is a
consequence OF that change and is a bring-up constraint, not a board defect: at
the owner's 25-30 V bench it does not arise.

Before this pass `kicad/sims/` did not exist. `verify_all` has no `sim_run`
member, so the P8 verify gate went green with every declared simulation
unexecuted - `review-board.md` s5 names that hole explicitly.

Bus is **30 V**, the owner's bench point (2026-08-08 reprioritisation: 25-30 V
into a 100-150 W load, fans on it; ZVS, loops, and "does it work at all").
Maximum power and thermals are out of scope, so **SIM-5 (loss split) and SIM-6
(gate-loop advisory) were not authored** - see s9.

---

## 1. The answer

> **No. As built, this board does not achieve ZVS, and that is the smaller half
> of the problem: it also delivers 53 W where the design says 113 W.**
>
> At the 30 V bench the drain is at **15.6 V and still falling at 5.9 V/ns** when
> the channel starts to conduct, against a 5 V window. Output is **53.4 W**
> against 112.6 W. Both have one cause: **~30 nH of stray series inductance in
> the TANK_A -> TANK_B run between the two spirals**, which pushes the network's
> series reactance ratio X_net/R from the design's 1.283 to a measured **2.00**.
>
> **It is fixable with a soldering iron and no new parts.** Fit this:
>
> | site | as built | **FIT** | note |
> |---|---|---|---|
> | **C308, C309** | 56 pF | **DNP - remove both** | C_s bank 9 x 56 -> 7 x 56 |
> | **C320** | DNP | **populate 27 pF** (`C541492`) | C_s trim site, already on the board |
> | **C203** | 56 pF | **DNP - remove** | C_shunt trim bank |
> | C204 | 27 pF | 27 pF, unchanged | |
> | C205, C206 | DNP | DNP, unchanged | |
> | C310-C317, C319 | populated | **unchanged** | C_m is already correct - s5 |
> | C318, C321, C322, C323 | DNP | DNP, unchanged | |
>
> Net effect: **C_s 504 -> 419 pF** and **C_shunt bank 83 -> 27 pF**. Every part
> is already on the BOM and every site already exists; nothing is added.
>
> Measured after the change, same deck, same bus: **Vds at turn-on 1.41 V**
> (was 15.6), **dVds/dt -1.21 V/ns** (was -5.9), **P_out 113.8 W** (was 53.4),
> **Vds,pk 122.2 V** against a 200 V part, **X_net/R 1.285** against the design's
> 1.283. Harmonics unchanged and passing (h2 -28.4 dBc, h3 -44.1).
>
> **Then trim duty at bring-up.** D = 48 % measures Vds at turn-on **0.53 V** and
> dVds/dt **-0.40 V/ns** - the true ZdVS optimum sits between D = 45 and 48 %.
> Duty is free, it is on the generator, and `decisions.md` D2 already calls it
> the correct first move.

---

## 2. Why you should believe the deck before you believe that answer

The bench was calibrated against closed-form Class E *before* any as-built
conclusion was drawn. Same deck, pours and bridge removed, tank at its design
values, and a **linear** 403 pF shunt - i.e. Sokal's Q_L = 5 design point from
`decisions.md` D11:

| quantity | closed form | this deck | error |
|---|---|---|---|
| P_out at 30 V | `0.51663.Vdd^2/R` = 112.6 W | **112.3 W** | **+0.3 %** |
| I_dc | P/Vdd = 3.75 A | **3.79 A** | +1.1 % |
| Vds,pk | 3.56 x Vdd = 106.9 V | **109.2 V** | +2.2 % |
| Vds at turn-on | 0 (ZVS by construction) | **-1.87 V** (clamped) | ZVS |

`tank_match.cir` carries a second, independent known-answer check that is gated
on every run: variant E is the design network with C_s 518 pF, and it must
return R = 4.13 ohm and X_net/R = 1.283. It returns **4.1332** and **1.2836**.
A sign error, a wrong node or a broken extraction shows up there first.

And every bench trips on a seeded defect (s8).

---

## 3. Root cause: the zone-B tank bridge

`decisions.md` D4 forbids In1/In2/B.Cu pour under the magnetics zone - correctly,
because a plane under a spiral is a shorted turn. The consequence nobody costed
is that the **TANK_A -> C_s bank -> TANK_B run has no return image**, so its
partial self-inductance is free-space-like rather than microstrip-like:
`(mu0.l/2pi)(ln(2l/w)+0.5)` is ~23 nH for 40 mm of 8 mm strip, and the real path
is longer than that. The handoff to this pass gives **25-35 nH**; 30 nH is used
as nominal and both ends are swept.

At 20 MHz that is **j3.77 ohm = 0.91 R** dropped into a network whose whole
design reactance is 1.283 R. `tank_match.cir` isolates it:

| | X_net/R | Re(Z) |
|---|---|---|
| as built, 30 nH bridge | **2.00** | 4.19 |
| as built, bridge removed | **1.158** | 4.14 |
| **fix: C_s 419 pF, 30 nH bridge** | **1.285** | 4.15 |
| fix at the 25 nH corner | 1.144 | 4.14 |
| fix at the 35 nH corner | 1.426 | 4.15 |

Removing the bridge alone restores the network, which is what identifies it as
the sole cause - no component value is wrong on its own. The fix holds across
the whole 25-35 nH uncertainty band, which matters because **the 30 nH is an
estimate, not a measurement**. It is also the largest remaining uncertainty in
this report: see s9.

Note the direction. Extra series **L** is cancelled by **less** C_s (more
capacitive reactance), so the correct move is to REMOVE capacitors from the C_s
bank, not add them. 419 pF is reachable exactly (7 x 56 + 1 x 27) and lands
0.2 % from the design target of 1.283.

---

## 4. Bench by bench

### SIM-2a `coss_charge.cir` - the model, gated first

Every other bench rests on one agent-authored card, so it is measured before it
is used. `Coss(v) = CJ0/(1+v/VJ)^MM`, VJ pinned at 1 V, CJ0 and MM **solved** from
the only two output-capacitance facts the EPC2019 datasheet publishes. Charge is
then obtained by integrating the current under a 0 -> 142.5 V ramp, which is
exact however nonlinear C(v) is.

| measure | datasheet / `decisions.md` | measured |
|---|---|---|
| `qoss_100v_nc` | 18 nC typ | **17.99** |
| `coss_100v_pf` | 110 pF typ | **109.96** |
| `qoss_100v_max_nc` | 23 nC | **23.04** |
| `coss_100v_max_pf` | 150 pF | **149.93** |
| `coss_tr_per_fet_pf` | D0's extrapolated **158 pF** | **156.65** (-0.8 %) |
| `coss_tr_maxcorner_pf` | D0's **205 pF** | **203.48** |
| `cshunt_from_pair_pf` | D0's **316 pF** | **313.31** |
| `coss_q_over_v_at100_pf` | D0 ERROR 1's **180 pF** | **179.92** |

**D0's amendment is confirmed, including its own error analysis.** Two datasheet
numbers and one exponent reproduce the extrapolated Coss(tr), the max corner,
and the 180 pF figure D0 identifies as the wrong one to use - so the amendment's
arithmetic is right and the operating point in D11 does not need re-solving.

### SIM-1 `classe_zvs_nominal.cir` - the board as it ships, at 30 V

| measure | window | measured | |
|---|---|---|---|
| `vds_at_turnon_v` | -2.0 .. 5.0 | **15.60** | **FAIL** |
| `dvds_dt_at_turnon_v_per_ns` | -2.0 .. 2.0 | **-5.89** | **FAIL** |
| `pout_w` | 90 .. 140 | **53.40** | **FAIL** |
| `vds_peak_v` | <= 155 | 102.5 | pass |
| `h2_dbc` | <= -20 | -27.83 | pass |
| `h3_dbc` | <= -33 | -49.90 | pass |
| `idc_a` | <= 5.0 | 1.86 | pass |

Turn-on is sampled at **channel conduction onset** (gate through the real 5.85
ohm / 199 pF leg reaching the switch model's 1.5 V), not at the command edge. At
the command edge the same waveform reads 25.19 V; both are reported so the two
definitions can never be confused. The conduction-onset number is the one that
is gated, and it is the more generous of the two.

At 15.6 V the pair dumps roughly `0.5.C.V^2.f` ~ 1 W into its own channel every
cycle - unpleasant but not a destruct path. **The 53 W is the real damage**: the
stage is not doing what it was designed to do.

### SIM-2b `cshunt_sweep.cir` - which populate, and does the trim bank reach

Six independent copies of the whole stage in one deck (own bus, choke, dice,
tank and 50 ohm load), so one run returns the whole sweep. `.step` is NOT usable
here: `sim_run.py` parses measures from ngspice stdout and a stepped run silently
leaves only the last point.

| variant | Vds at turn-on | P_out | |
|---|---|---|---|
| **A** as built, C_s 504, bank 83 pF | **15.47 V** | **53.4 W** | FAIL |
| **B** as built, bank EMPTIED | 1.34 V | **59.2 W** | **the trap - FAIL on power** |
| **C** **RECOMMENDED**: C_s 419, bank 27 pF | **1.41 V** | **113.8 W** | pass |
| F  C_s 419, bank 56 pF | 3.94 V | | pass (the next step up also works) |
| D  C_s 419, bank 27 pF, **max-Coss dice** | 12.15 V | 102.6 W | ZVS lost, untuned |
| E  C_s 419, bank **emptied**, max-Coss dice | 8.87 V | 105.3 W | bank spent |

**Variant B is why this bench gates power as well as ZVS.** `review-board.md` W2
ships the bring-up instruction *"if ZVS lands late, pull C204 first"*. Doing that
DOES restore ZVS - and leaves the amplifier at 59 W, because the tank is still
detuned. A ZVS-only bound would have blessed it.

**The max-Coss corner is the one place the trim bank runs out.** Emptying it
takes the corner from 12.15 to 8.87 V, still short of 5 V. The remaining knob is
duty: measured, **D = 46 % gives 4.87 V and D = 42 % gives 4.78 V** at that
corner, i.e. a 4-8 % duty reduction closes it, against `decisions.md` SIM-2's
own `duty_adjust_needed_pct <= 6` window. So the corner is recoverable, but
**only with the generator, not with parts** - worth knowing before a reel that
measures high arrives.

### SIM-4 `tank_match.cir` - impedance, harmonics, and two arbitrations

AC, 1-200 MHz, nine independent copies of the load network. See s3 for the
X_net/R table and s5 for the two arbitrations.

Harmonic terminations at the recommended populate: |Z| **60.1 ohm at 2f0** and
**113.7 ohm at 3f0** against 4.15 ohm at f0 - which is the mechanism behind the
h2/h3 numbers SIM-1 measures at the load.

### SIM-3 `gate_symmetry.cir` - VGS at the die, and common-source

Three self-driven copies of the gate loop + stage: matched dice with the
architecture's +/-0.15 nH gate-loop mismatch; datasheet-corner dice; and a 6R8
turn-off variant. VGS is measured **at the die** as `v(g)-v(s)`, with the source
tied to ground through the **0.157 nH** common-source inductance
`review-board.md` W1 re-measured.

| measure | limit | matched | corner dice |
|---|---|---|---|
| VGS max | 5.75 V (SIM-3) / 6.0 V (EPC2019) | **5.037** | **5.583** |
| VGS min | -4.0 V (EPC2019) | **-0.193** | **-0.257** |
| VGS max during OFF | 0.8 V (`VGSth_min`) | **0.122** | |
| peak Id imbalance | 15 % matched / 40 % corner | **0.07 %** | **62.4 % FAIL** |
| RMS Id imbalance | 15 % / 25 % | **0.39 %** | 5.94 % |
| LMG1020 OUTH pin | 5.75 V | 5.040 | |

**The gate loop is fine.** VGS never approaches either rail; the turn-off
undershoot is -0.19 V against -4 V (21x); off-state VGS is 0.12 V against a
0.8 V minimum threshold (6.5x); and with mirrored copper the two dice share to
0.07 %. The +/-0.15 nH mismatch spec is met with enormous room - the mirror is
worth far more than the tolerance implies.

**The one failure is a ZVS failure wearing a sharing costume.** With
datasheet-corner dice (Q1 typ against Q2 at Rds 90 mohm hot AND Coss max) the
peak-current split is 62.4 %. Re-run with nothing changed except the recommended
populate, it is **10.6 %**. `decisions.md` D1 justifies paralleling on exactly
this: *"Class E is soft-switched: at turn-on the drain is at ~0 V so there is no
discharge spike to hog."* True - and the as-built board is not soft-switched, so
the low-Rds die hogs the Coss discharge. Fix ZVS and the argument holds.

**4R7 vs 6R8, settled.** `route-notes.md` s14 ruled this twice on estimates and
asked P8 to close it; `review-board.md` W1 recommended the revert, which
`parts.json` has already taken.

| | VGS min | VGS max | off-state VGS max |
|---|---|---|---|
| **4R7 (as built)** | **-0.193 V** | 5.037 V | 0.122 V |
| 6R8 (P7's value) | -0.130 V | 5.110 V | 0.139 V |

6R8 buys **0.063 V** of undershoot margin on a rail that already has 21x, and
costs ~4 C of junction temperature (`route-notes.md` s14). **4R7 is correct.
Do not go back.** One caution for whoever reads the earlier estimate: a window
that starts 0.4 ns after the falling edge measures the *tail of the turn-off
edge*, not a spurious-turn-on threat, and reads 0.79 V at 6R8 purely because
6R8 discharges the gate more slowly. The bench measures 13-23 ns after the edge.

### SIM-7 `bus_derating.cir` - and a correction to D1

Four copies at 40 / 36 / 30 / 25 V, recommended populate, network unchanged.

| Vdd | Vds at turn-on | P_out | Vds,pk | Vds,pk/Vdd |
|---|---|---|---|---|
| 40 V | **-1.18 V** | 211.4 W | **172.5 V** | 4.31 |
| 36 V | -0.22 V | 168.5 W | 152.1 V | 4.23 |
| **30 V** | **+1.41 V** | 113.8 W | 122.2 V | 4.07 |
| 25 V | **+3.12 V** | 76.7 W | 98.2 V | 3.93 |

**ZVS holds across the whole 25-40 V range, so D1's derating ladder is usable -
but the claim behind it is not exact, and it errs in the unhelpful direction.**
D1 says *"the design equations are linear in Vdd ... the bus can be backed down
at bring-up without losing ZVS."* That is true for a LINEAR shunt. Here more than
70 % of C_shunt is EPC2019 Coss(v), and the charge-equivalent `Qoss(V)/V` RISES
as the swing shrinks (156.7 pF/FET over 0-142.5 V, ~175 pF over 0-107 V). A
lower bus is therefore a LARGER effective shunt, and ZVS arrives LATE:
**4.30 V of drift from 40 V down to 25 V**, all of it against the operator.
P scales as Vdd^2.09 rather than Vdd^2.00, and Vds,pk/Vdd moves 9 % over the
range. Practical consequence: **tune the populate at the bus you intend to run**,
and re-check ZVS after any large bus change rather than assuming it travels.

**One genuine finding at 40 V: `vds_pk_40v_v` = 172.5 V FAILS the 155 V bound.**
A populate trimmed at 30 V is under-shunted at 40 V for exactly the reason above,
and 172.5 V leaves only a 1.16x derate on the 200 V part instead of 1.29x. **One
populate cannot serve both 30 V and 40 V.** If the bus ever goes back to 40 V,
add C_shunt (populate C203 at 56 pF again) and re-run this bench. At the owner's
25-30 V the peak is 98-122 V and the point is moot.

---

## 5. Arbitrations asked of this pass

### OPEN-12 - SETTLED. Sokal's coefficient is right; the P1 fragment is refuted.

`decisions.md` D11 refuted the P1 fragment's `C_series.omega.R = 0.63467` on the
argument that it implies a net series reactance of 3.4 R, which is not a Class E
network. **That is now measured rather than argued**, on the design network with
no pours and no bridge:

| | C_s | measured X_net/R |
|---|---|---|
| P1 fragment, `0.63467` | 1222 pF | **3.425** |
| **Sokal fit, `0.26906`** | **518 pF** | **1.284** (target 1.283) |

**Adopt 0.26906. OPEN-12 closes.** Both numbers are gated on every run, so the
arbitration cannot silently rot. Note that this settles the *coefficient*, not
the board: the as-built C_s of 504 pF was a correct implementation of the right
coefficient, and it is the 30 nH of copper - not the coefficient - that makes
419 pF the right value to fit.

### C_m (review-board.md E2) - the P8 fix was right. Change nothing.

Only three C_m populates are reachable. Measured Re(Z) at 20 MHz against
R_opt 4.13 ohm, with the recommended C_s:

| C_m populate | total with the 46.1 pF RFOUT pour | Re(Z) | |
|---|---|---|---|
| **475 pF - 8 x 56 + C319 27, AS BUILT** | 521.1 pF | **4.146** | **+0.4 %, best** |
| 502 pF (populate C322) | 548.1 pF | 3.795 | -8.1 % |
| 448 pF (depopulate C319) | 494.1 pF | 4.548 | +10.1 %, at the window edge |

**E2's fix (C318 DNP) landed the match essentially exactly and the board should
ship as it is.** The two 27 pF trim sites C322/C323 stay DNP and remain available
as bench trim.

### C_shunt (review-board.md W2) - the band's top was right, its bottom was not deep enough

W2 flagged the bank shipping 455 pF against a 403-449 pF band; the P8 fix took
C204 to 27 pF, giving 316 + 83 + 27.4 = **426 pF**, mid-band. That arithmetic is
correct. What the band could not see is that **the ZVS-optimal shunt depends on
the tank**, and once C_s comes down to 419 pF the optimum bank drops to 27 pF
(total ~370 pF at the 30 V bench, where the pair's own charge-equivalent Coss is
~350 pF, not the 313 pF quoted for a 142.5 V swing). Removing C203 is part of the
same single fix, not a separate finding.

---

## 6. Model policy, and what these models cannot tell you

No vendored vendor models anywhere. Every card is agent-authored from
`parts/C2836675.json` and `parts/C6423790.json`, with the fit written into the
`.cir` headers.

- **EPC2019 output capacitance** - `Coss(v) = CJ0/(1+v/VJ)^MM`, two parameters
  solved from two datasheet numbers, validated in `coss_charge.cir` (s4). The
  positive-part argument is softened (`0.5(v+sqrt(v^2+0.01))`) so the drain can
  ring below zero without an unintegrable kink at v = 0.
- **EPC2019 channel** - voltage-controlled switch, 65 mohm/FET hot (36 mohm typ
  x the 1.8x factor behind D1's own 65/90 mohm figures), conduction onset at
  1.5 V. Third-quadrant conduction is a generic diode fitted to the single
  published point (VSD 1.8 V at IS 0.5 A). Qrr = 0 per datasheet.
- **LMG1020** - Tier-B boundary model only: PULSE + 0.714 ohm sourcing
  (IOH 7 A at 5 V), PULSE + 1.000 ohm sinking (IOL 5 A at 5 V), each made
  unidirectional by a diode, 0.4 ns edges. No IC internals.

**What is NOT in these models, stated so nobody reads past it:**

1. **Coss hysteresis.** A single-valued C(v) is lossless by construction. The
   4.83 W that D1 budgets as the dominant FET loss term **cannot appear here**.
   `eff_ceiling_pct` (95.8 %) is a bookkeeping check, **not an efficiency
   result**, and SIM-5's `p_coss_hysteresis_w` remains unmeasured. D1's stated
   residual risk is still open.
2. **Gate charge.** C_GS is constant, so there is no Miller plateau. The VGS
   numbers are a *loop* result (L, R, common-source injection), not a Qg result.
3. **Self-heating and dynamic Rds(on).** The positive Rds tempco that D1 relies
   on to equalise static sharing cannot act, so the RMS-sharing figures are
   pessimistic; equally, nothing here predicts a junction temperature.
4. **Distributed copper.** Pours are lumped at one node. Deliberately: the
   lumping is why an ESR of 50 mohm sits in series with each Coss and 20 mohm
   with the shunt bank, to damp the 14-38 GHz artefacts lumping creates.
5. **The 30 nH bridge itself is an estimate**, not a measurement. See s9.

---

## 7. Deviations from the architecture's declared SIM windows

Three, all deliberate, all visible in the sidecars.

1. **SIM-4's `zin_phase_20m_deg` 25-45 deg is arithmetically impossible** next to
   its own `x_net_series_over_r` 1.0-1.6, because phase = atan(X/R): 1.0 -> 45.0
   deg and 1.6 -> 58.0 deg. Re-derived as **45-58 deg**, severity warning, since
   it is redundant with the x_net bound it is derived from. Related: SIM-4's
   `zin_mag_20m_ohm target 4.13` must mean the REAL part - at the optimum
   |Z| = R.sqrt(1+1.283^2) = 6.3 ohm. The bench measures `zin_re_20m_ohm`.
2. **SIM-1's ZdVS window of +/-0.2 V/ns is not reachable with the board's
   discrete trim set** at a fixed 50 % duty: the best reachable populate measures
   -1.21 V/ns. It IS reachable with the generator (-0.40 V/ns at D = 48 %). The
   error bound is re-derived at **+/-2.0 V/ns** - `|dV/dt| x C_shunt = 0.85 A`
   against a ~6 A peak switch current, i.e. <= 15 % of the current the channel
   takes in a step - and the architecture's +/-0.2 V/ns is kept as a **warning**
   so the promise stays visible.
3. **SIM-5, SIM-6, and the SIM-2 measures `trim_pf_needed` /
   `duty_adjust_needed_pct` are not authored as bounds.** SIM-5/6 are the loss
   and decoupling questions the owner deprioritised, and SIM-5 is not honestly
   simmable with a lossless Coss model anyway (s6). The two SIM-2 measures are
   *conclusions* rather than measurements - a bound must gate something the
   engine produced - so they are reported in s4 (27 pF of trim at the typ
   corner, 0 pF plus a 4-8 % duty reduction at the max corner) and gated
   indirectly through `vds_ton_fix_maxcoss_bank0_v`.

---

## 8. Calibration: every bench trips on a seeded defect

Required by the sim-analyst contract and re-runnable. One value mutated per
bench, in a scratch copy; the workspace files are never touched.

| bench | seeded defect | bound that tripped | value |
|---|---|---|---|
| `coss_charge` | Coss exponent 0.427 -> 0.30 | `qoss_100v_nc`, `coss_tr_per_fet_pf` | 27.36 nC, 247.9 pF |
| `classe_zvs_nominal` | C_m 475 -> 560 pF (the bank P4 W1 rejected) | `pout_w` | 65.7 W |
| `tank_match` | calibration variant C_s 518 -> 447 pF | `x_net_open12_sokal` | 0.693 |
| `cshunt_sweep` | recommended variant reverts to C_s 504 pF | `vds_ton_fix_v`, `pout_fix_w` | 5.20 V, 57.0 W |
| `gate_symmetry` | **R204 mis-stuffed 4R7 -> 47R** | `id_imbalance_pct` | 52.4 % |
| `bus_derating` | recommended C_s 419 -> 504 pF | `vds_ton_30v_v`, `pout_30v_w` | 5.20 V, 57.0 W |

The `gate_symmetry` entry is worth reading twice: neither a 5x error in the
common-source inductance (0.157 -> 0.768 nH, the figure P7 used) nor a badly
non-mirrored gate loop (2.2 -> 8 nH) trips any bound. The gate loop is genuinely
robust. What DOES trip it is the wrong-value class it exists for - a single
mis-stuffed gate resistor.

---

## 9. What is still open

- **OPEN-13 (NEW, and the biggest one).** The **25-35 nH zone-B tank bridge is an
  estimate**, and the recommended C_s populate is a direct function of it. The
  fix holds across the whole band (X_net/R 1.144 at 25 nH, 1.426 at 35 nH), so it
  is safe to fit - but **measure it on the first article** before finalising the
  bank. The cheap measurement: with the board unpowered, resonate TANK_A-to-
  TANK_B against a known capacitor and read f0, or sweep S11 into the drain node
  and fit. If it lands outside 25-35 nH, re-run `cshunt_sweep.cir` with `lbr`
  changed - it is one number in one file.
- **OPEN-11 stays open** and it interacts. `spiral-design.md` s9 item 1 warns
  that methods A and B disagree by 14-17 % on the spiral inductances and that
  **L must be measured on the first article**. A 15 % error on L_s + L_m is
  +/-41 nH, which is *larger* than the bridge stray, and it moves the same knob.
  **Measure the spirals and the bridge in the same session, then set C_s once.**
- **D1's Coss-hysteresis risk is untouched** (s6 item 1). SIM-5 was not authored;
  the 4.83 W remains an assumption, and it is the dominant FET loss term.
- **`verify_all` still has no `sim_run` member.** This gate has to be run
  explicitly. Until that changes, a green `verify` gate says nothing about ZVS.
- The **max-Coss reel corner** needs the generator, not the trim bank (s4).
- **40 V is no longer a drop-in bus** with the recommended populate (s4, SIM-7).

## 10. Reproduce

    .venv/Scripts/python .claude/skills/ai-ee/scripts/gate.py --gate sim \
        boards/rf-de-20m/kicad/sims --out boards/rf-de-20m/reports/sim.json

One bench at a time, with the raw measure dump:

    .venv/Scripts/python .claude/skills/ai-ee/scripts/sim_run.py \
        --exec-one boards/rf-de-20m/kicad/sims/<bench>.cir \
        --dll "C:/Program Files/KiCad/10.0/bin/ngspice.dll"
