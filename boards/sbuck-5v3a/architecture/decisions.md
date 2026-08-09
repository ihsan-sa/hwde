# sbuck-5v3a - P2 architecture decisions

For the orchestrator to log. Every conflict is resolved by naming which source
loses and why. Nothing here is averaged.

---

## D1. Buck IC: **AP64350SP-13 class (Diodes, SO-8-EP)**. LMR33630ADDAR and SY8205FCC lose.

**This is the riskiest decision on the board and it is NOT decided on the
current-limit floor.** P1 handed P2 explicit authority to relax the 4.0 A
minimum-spec floor (it was a delegate tightening at Q5, not a user requirement,
and 3.375 A guaranteed would be 12.5% over the 3.0 A load - defensible). The
authority was not needed: AP64350's published MIN of 4.25 A clears the floor
outright. **The floor stands, unrelaxed, because the winning part meets it.**

The decision is made on **guaranteed conduction loss**, which on this board is
the same thing as junction temperature:

| | AP64350 | LMR33630A | SY8205 |
|---|---|---|---|
| Rds(on) HS / LS at 25 C | **75 / 45 mOhm, MAXIMUM** | 95 / 66 typ, **160 / 110 max** | 70 / 40 **typ, no max published** |
| HS+LS conduction at 12 V, hot | **0.725 W** | 0.984 W (typ) / 1.65 W (max) | 0.662 W (typ, unbounded) |
| vs the 0.653 W budget line | +0.072 W | **+0.331 W (typ)** | -0.009 W with no corner |
| in junction temperature | +1.4 C | **+6.3 C** | unknowable |

AP64350's **guaranteed maximum** beats TI's **typical**. On a design that closes
with 7 C of thermal margin, a part whose worst case is published and bounded
beats one whose typical is worse than the other's maximum. LMR33630's 260 mW
of extra typical conduction loss is 4.9 C of junction temperature, and its own
maximum column (1.65 W) would put Tj at ~112 C, over the 105 C design limit.

**SY8205 is rejected on documentation, not on price or thermals.** Its
datasheet is marked "Preliminary Specification" throughout, publishes Rds(on) as
typ-only with no maximum, publishes no min/max on the current limit, gives no
UVLO divider formula, never uses the word PFM (so light-load and 0 A behaviour
cannot be confirmed), documents no dropout or foldback mechanism, and needs an
external soft-start cap. Its one headline advantage - `theta_JA` 30-36 C/W vs
45 C/W - **does not exist in this thermal model**: the junction ladder is built
on `theta_JC(bottom)` plus the via array plus a whole-board `R_ba`, and only 7 C
of the 48 C rise is the IC's own local path. 37 C of it is board-to-ambient,
shared by every watt on the board regardless of package.

The two other differentiators P1 raised are both handled rather than accepted:
the UVLO penalty is removed by D2, and external compensation is a P4 design task
with a vendor-published Type-II procedure (Eqs 12-20) and a worked example at
exactly our operating point, plus it is the only one of the three that lets P4
*target* the crossover the 100 us load-step recovery needs.

**Residual risks accepted and named:**
- Rds(on) 75/45 exceeds the P1 part limits of 65/42; the +72 mW is paid for by
  the inductor's DCR saving (-72 mW). Net neutral, budget re-issued in
  `power_tree.md` s2.
- `theta_JA` 45 C/W sits exactly at the stated ceiling. **P3 verify-later:
  confirm `theta_JC(bottom) <= 5 C/W` from the datasheet.** If it is worse the
  ladder must be re-run.
- External compensation values must be re-derived, not copied (D6).

## D2. UVLO retargeted to **6.2 V rising / 5.3 V falling**. Delegate Q14's "6.5 / 6.0" is rejected.

Three independent reasons, any one sufficient:

1. **The 0.5 V hysteresis gap is what makes AP64350's divider pathological.**
   Its own equations carry a 0.924 coefficient that nearly cancels the numerator
   at a small gap, forcing R3 = 1.46k / R4 = 326 Ohm and a **7-10 mA continuous
   draw: 81 mW at 12 V, 181 mW at 18 V**, i.e. 4-9% of the entire loss budget
   and 1.5-3.4 C of junction temperature spent on a resistor divider. At a 0.9 V
   gap the same equations give 105k / 24.0k and 93 uA. The pathology is a
   property of the *target*, not of the part.
2. **0.5 V of hysteresis is less than the cable drop this board itself causes.**
   2.44 A through 0.2 Ohm of user input cable is 0.49 V. A converter that
   starts, drags its own supply below VOFF, stops, recovers and restarts is
   motorboating. 0.9 V is the fix.
3. **VON = 6.5 V is too close to the 7.0 V spec floor at the threshold corner.**
   VEN_H is 1.18 typ / 1.25 max (+5.9%); with 1% resistors the worst-case VON
   lands at ~7.0 V, meaning the converter could legally refuse to start at its
   own minimum rated input. 6.2 V nominal leaves >= 0.2 V of margin.

Delegate Q14's stated *intent* - "the converter refuses to start below the 7 V
spec floor, EN exposed as a test pad only" - is fully preserved. Only the
numbers move. **The falling threshold at 5.3 V means the board keeps regulating
down to 5.3 V input, where it is already in dropout and the output simply
sags.** That is benign and is the point of the wider hysteresis.

## D3. fsw = **500 kHz** with **6.8 uH FAUL1050-6R8MT class**. The 400 kHz slot is avoided, not solved.

fsw and the inductor are one decision. At 500 kHz (RT = 200k) the 6.8 uH
FAUL1050-6R8MT clears the DCR ceiling **after hot derating** (18.5 mOhm cold ->
24.05 mOhm hot vs a 25 mOhm limit), with conservative Max-column Isat and Irms
margins of 3.1x and 2.4x over what the circuit asks, on a 155 C alloy-composite
core.

Choosing LMR33630 would have forced 400 kHz (the "A" variant is fixed) and with
it the 10 uH slot, whose only stock-clearing part (MDA1365-100M) sits **at**
25.0-25.2 mOhm hot - zero DCR headroom, with its Isat/Itemp margins extrapolated
rather than datasheet-confirmed. The better-DCR alternative (SRP1265A-100M) is
82 pieces short of the >= 500 stock rule. So the IC choice bought the clean
inductor slot as well; that is a reinforcement of D1, not the reason for it.

500 kHz also sits **below the AM broadcast band** (530 kHz - 1.71 MHz) that
delegate Q32 asks to avoid where the part allows, whereas 600 kHz would land
inside it. And the loss budget holds to `fsw <= 550 kHz`, which is exactly the
AP64350's fsw max corner at RT = 200k (450/500/550 min/typ/max) - the 27 mW
that corner adds is absorbed by the 399 mW margin.

Backup inductor if FAUL1050-6R8MT stock moves: FAUL1350-6R8MT (same family,
13.5 x 12.8 mm, 18 mOhm). **Sourcing flag for P3: both sit at 519-763 pieces,
which clears the >= 500 rule but not comfortably, and both are small-brand
(cjiang / KOHERelec) parts that appear to share an OEM base design - the
single-source risk spans both brands, not just one.** Re-verify live at P3.

## D4. Copper weight: **1 oz outer**. Both vendor reference layouts lose.

AP64350's layout section recommends 2 oz top and bottom; LMR33630's specifies
2oz/1oz/1oz/2oz. Two independent vendors agreeing is a real signal. They still
lose, and the third reason is the decisive one:

1. **They answer a different question.** A vendor layout note addresses a board
   where pad-to-plane spreading is the bottleneck. Here the board is already
   isothermal at 1 oz (spreading length 32 mm > the 20-25 mm half-dimension),
   `R_ba` is set by area, convection coefficient and emissivity, and what the
   vendors actually want - copper area near the part - this board already
   provides at >= 1500 mm^2 on B.Cu plus two solid GND inners.
2. **JLC's only 4L / 1.6 mm 2 oz-outer lamination makes it worse.**
   `JLC04162H-7628A` has a **0.4284 mm L1-L2 prepreg against the 1080B's
   0.2444 mm**. That nearly doubles the thermal-via resistance to In1 (16-via
   array 2.16 -> 3.79 K/W, **+1.7 C of Tj**) and pushes the image plane 75%
   further from the hot loop - degrading the exact structure the brief's
   uninterrupted-plane requirement protects. Against a best case of ~2.5 C from
   improved spreading, the net is +0.8 C, inside the +/-30% uncertainty the
   convection/radiation correlations already carry.
3. **Delegate Q21's own condition is not met.** Escalation is authorised only if
   IPC-2152 sizing or the Tj calculation fails at 1 oz. Neither fails:
   1.52 / 2.31 / 2.06 mm route fine on a straight-through 50 x 40 mm floorplan,
   and worst-case Tj is 97.9 C against 105 C.

## D5. Fuse: **5 A slow-blow (Bel Fuse C1T class)**, not the 4 A sibling. Delegate Q7's "~4 A" is relaxed.

The exact-4 A part (0685T4000-01) is electrically ideal and sits at **174 pieces
in stock**, failing the binding stock rule outright. The 5 A sibling has
5,032 pieces, and three of the four consequences favour it:

- **Lower DCR** (20 vs 30 mOhm) - saves 21 mW at 12 V and 90 mW at 7 V, which is
  1.7 C of junction temperature on the binding constraint.
- **Better nuisance-blow margin**: 2.44 A worst-case input current is 49% of a
  5 A rating vs 61% of a 4 A one.
- **Its job is unaffected.** The fuse exists for exactly one fault - a shorted
  high-side switch, which the IC's own protection cannot cover (Q7). The fault
  current in that case is set by the source and the copper, far above 5 A, so
  the opening time is milliseconds either way. The IC's cycle-by-cycle limit and
  hiccup restart handle every overcurrent the fuse is not for.
- Cost: a 5 A element passes more energy into a fault before opening than a 4 A
  one. Accepted, because no fault this board can experience sits between 4 and
  5 A for long enough to matter.

## D6. Cout = **5x 22 uF 25 V X7R 1210**, and the compensation must be RE-DERIVED.

The load step sizes the bank, not the ripple: 50 mV of ripple needs 4.5 uF; a
3 A step at the 7 V worst-case line needs 76.5 uF. 5x gives ~97 uF effective and
26% margin. **4x (77.4 uF eff, 198 mV against the 200 mV limit) is the
authorised floor; 3x is not authorised** (264 mV).

Note the specified load-step test condition is 12 V (delegate Q3), where only
22 uF would be needed. Sizing to the 7 V worst case instead is the conservative
reading the brief's decision policy asks for, and it is recorded here as a
choice rather than an accident.

**Consequence, and the biggest open design task:** AP64350's published Type-II
values (Rcomp 14k, Ccomp 3.3 nF) are quoted for **2x 22 uF**. Copying them at
2.5x the capacitance drops the crossover to roughly 6.6 kHz, which will not
recover a 3 A load step within the specified 100 us. P4 must re-derive against
the real bank with the datasheet's Eqs 12-20, targeting **fc 25-50 kHz with
phase margin >= 45 deg**, and record the numbers. If the loop cannot be closed
there, drop to 4x 22 uF and record that instead.

## D7. Stackup: **JLC04161H-1080B**, 4 layer, In1 and In2 both solid GND.

Layer count was already fixed at P0 (delegate Q18) and is not re-opened. The
specific lamination is the only 4L / 1.6 mm / 1 oz outer / 0.5 oz inner product
JLC returned on 2026-08-06, and it is `stackups.yaml`'s `defaults[4]`.

The architect's binding rule - "no power net on an inner layer" - **survives
contact with the real stackup and is reinforced**: JLC's inner copper here is
0.0152 mm, thinner than the nominal 0.5 oz the rule was computed against, so the
required inner widths are ~15% worse (3.50 / 4.73 / 5.32 mm for +VIN / +5V /
/SW, i.e. 7-11% of the board width per net). In1 and In2 are both solid GND,
declared explicitly in `constraints.json.planes` because the 4-layer default
would pour In2 as the dominant power net.

**Re-verify the template before ordering.** `JLC04161H-3313` never existed and
still sized a real 100 ohm board; `JLC04161H-7628G` was live on 2026-07-30 and
gone a week later.

## D8. Sheet plan: **one flat root sheet**, no hierarchy.

33 placed parts, one function, one straight-through floorplan. The decisive
argument is that hierarchical labels produce `/<sheet>/<LABEL>` net names and
every P5-P8 consumer matches those strings *silently* - the trap that cost
lumina-par a P4 amendment. A flat sheet removes the class entirely.

---

## Corrections made to P1 material (recorded, not silently applied)

1. **The thermal-via arithmetic used a 0.21 mm L1-L2 dielectric**, which belongs
   to the RETIRED phantom stackup `JLC04161H-3313`. The real 1080B prepreg is
   0.2444 mm: `R_1via` 25.3 -> 29.4 K/W, a 16-via array 1.9 -> 2.16 K/W. Costs
   0.2 C. Conclusion unchanged.
2. **Spreading length recomputed at the real 0.0152 mm inner copper**: 33 ->
   32 mm. Still larger than the board half-dimension, so the near-isothermal
   whole-board model still holds. Conclusion unchanged.
3. **Inner-layer IPC-2152 widths recomputed at 0.0152 mm** rather than a nominal
   0.5 oz: ~15% wider than P1 quoted. Strengthens the "no power net on an inner
   layer" rule.
4. **U1's declared dissipation raised 1.001 -> 1.058 W** to match AP64350's real
   maximum Rds(on); **L1's lowered 0.521 -> 0.448 W** to match FAUL1050's real
   DCR. Both flow into `constraints.json.thermal`.
5. **Net names reconciled**: `VIN` -> `/VIN` and `SW` -> `/SW` (root-sheet local
   labels carry a leading slash); `+VIN`, `+5V`, `GND` stay bare. `power.json`'s
   proposed names would not have matched the netlist.

## Sim candidates for P8 (house policy: buck SWITCHING is NOT simulated)

Two static/small-signal benches earn their keep, both with numeric pass
windows and both decision-relevant rather than confirmatory.

| # | Bench | Pass window | Why it is worth running |
|---|---|---|---|
| SIM-1 | **FB divider setpoint over tolerance.** Worst-case / Monte-Carlo of `Vout = Vref * (1 + R6/R7)` with Vref 792-808 mV and the divider at its specified tolerance | **4.90 - 5.10 V at every corner** | This is the bench that PROVES the 0.1% resistor requirement rather than asserting it. Reference tolerance alone spends -1.2%/+0.84%; 0.1% parts land at 4.93-5.05 V (passes), 1% parts land at 4.84 V (fails). If a later phase tries to substitute 1% resistors to save cents, this is the gate that stops it |
| SIM-2 | **EN/UVLO thresholds over tolerance.** AP64350's divider equations INCLUDING the 4.114 uA and 5.5 uA internal pull-ups, swept over VEN_H 1.18-1.25 V, VEN_L 1.03-1.09 V and 1% resistors | **VON in [5.6, 6.8] V, VOFF in [4.6, 6.0] V, VON - VOFF >= 0.6 V** | A naive two-resistor divider calculation is simply wrong for this part - the pull-ups are what make the pathology in D2 exist. The upper VON bound protects the 7.0 V spec floor; the lower protects against running below dropout (~5.4 V); the hysteresis floor protects against motorboating on a 0.2 Ohm input cable |

**Not worth a bench:** the reverse-polarity gate clamp (R1 + 15 V Zener). Its
worst case is `|Vgs| = min(Vin, ~15 V)` over Vin 7-25.4 V with 30-104 uA of
bias - algebra, not a simulation, and the answer is already in
`power_tree.md` s6.

## Open for P3 / P4 (not blocking checkpoint 1)

- **P3:** confirm `theta_JC(bottom) <= 5 C/W` for AP64350 from the datasheet -
  the whole junction ladder rests on it.
- **P3:** re-verify FAUL1050-6R8MT stock live (763 today, >= 500 rule) and pull
  the DB128L screw terminal's mechanical drawing - height and pin/hole diameter
  are not in the LCSC attribute table and were never confirmed.
- **P3:** no vendor DC-bias curve was obtainable for any MLCC on this board;
  every effective-capacitance figure is a conventional estimate, and the Cout
  bank count depends on it.
- **P4:** re-derive the compensation (D6). This is the one number in the design
  that cannot be checked before fab.
