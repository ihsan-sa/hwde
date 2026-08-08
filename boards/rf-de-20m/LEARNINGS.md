# LEARNINGS - rf-de-20m (20 MHz Class DE GaN inverter, 200 W)

Workspace-local (deliberately NOT root LEARNINGS.md - concurrent runs in flight 2026-08-07).
Promote to root only after this board's run settles.

---

## 2026-08-07 [sourcing][jlcpcb][gan] There is NO JLC/LCSC-stocked gate driver that can do a 20 MHz HALF-BRIDGE

The single hardest constraint on this board, found before any schematic work. Machine-checked
against LCSC + JLC catalogs and TI datasheets:

| Part | Where | Verdict at 20 MHz half-bridge |
|---|---|---|
| **LMG1210** (200 V HB, 0-20 ns adj. dead time, 3.4 ns HS/LS match, 50 MHz) | **NOT at LCSC/JLC** - searched part + suffixes (RVRR) + clone vendors. Digikey/Mouser only, ~$5, 19-pin 4x3 mm WQFN | The *correct* part. Unobtainable under full-JLC-PCBA. |
| **LMG1205** (100 V HB GaN, integ. bootstrap diode) | LCSC C2653814, in stock | **Too slow.** TI states typical use 1-2 MHz and it "would not be appropriate for 10 MHz". Also no interlock -> needs >=8 ns dead time floor. Rejected. |
| **LMG1020** (low-side only, 5 V, 7 A/5 A, 3 ns delay, 1 ns min pulse, 60 MHz) | **LCSC C6423790**, in stock, $0.36, 0.8x1.2 mm WCSP. NB: LCSC brands it **"Tokmas"**, not TI - verify authenticity on receipt | Speed is ideal. **Low-side only** - cannot drive the DE high side alone. |
| UCC27714 / IR2304 / IR21844 / FAN73932 / SLM2101 | LCSC, in stock | All bootstrap HB drivers in the 100s-of-kHz class. Orders of magnitude too slow. |

**Consequence:** the triangle {20 MHz, Class DE half-bridge, full-JLC-PCBA} does not close.
Exactly one corner must give. Do not spend another research pass re-confirming this.

## 2026-08-07 [gan][class-de] Class DE sizing at 20 MHz closes comfortably on EPC2019 at a 100 V bus

Worked before part selection so the FET choice was driven by numbers, not familiarity.

- **EPC2019**: 200 V, 36 mohm, Coss **110 pF**, Qoss **18 nC @ 100 V**. JLC C2836675, ~$2.17, in stock.
  (Beware: a web summary quoted "0.7 pF Coss" - that is Crss/Cgd, NOT Coss. Always confirm from
  the datasheet table; the Coss number is what decides whether DE closes.)
- Half-bridge fundamental: `V1_pk = (2*Vdc/pi) * sin(pi*D)`.
- At Vdc = 100 V, converged operating point: D ~ 36.6%, V1_pk ~ 58 V,
  **R_opt ~ 8.5 ohm**, I_pk ~ 6.9 A, dead time **~6.5 ns** (13% of the 50 ns period).
- Dead time from `t_d = 2*Qoss / (~0.85*I_pk)` = 36 nC / 5.9 A. Well inside LMG1210's 0-20 ns range.
- Conduction loss is a **non-issue** (~0.3 W/FET). This is the key insight: at 20 MHz the design is
  Coss/switching-limited, so pick the **small low-Coss die, not the low-Rds(on) one**. Choosing a
  fat low-Rds(on) GaN here actively makes the design worse (Coss won't commutate in the dead time).

**Bus voltage sweep** (why 100 V, recorded so it is not re-litigated):

| Vbus | R_opt | I_pk | Match Q (to 50 ohm) | Verdict |
|---|---|---|---|---|
| 48 V | 1.9 ohm | 14.5 A | ~5.0 (~7 W match loss, ~3.7 W/FET cond.) | Rejected - needs paralleled FETs, ~80% eff. |
| **100 V** | **8.5 ohm** | **6.9 A** | **~2.2 (~1.5% loss)** | **Chosen.** 2x derate on a 200 V part. |
| 150 V | 19 ohm | 4.4 A | ~1.2 | Best match, but only 1.33x derate - risky with switch-node ringing. |

## 2026-08-07 [class-e][topology] Class E is the only topology that closes fully-JLC - at a real cost

If "full JLC PCBA" is held as the hard constraint, the high-side driver problem is not solvable
cheaply; the escape is a **single ground-referenced switch** (Class E), driven directly by the
LMG1020. Sizing check, so the option is costed rather than hand-waved:

- Class E peak drain voltage is **~3.6 x Vdc** -> on a 200 V EPC2019 the bus is capped at
  ~55 V, derate to **45-50 V**. That is the whole price of the topology swap.
- At Vdc = 45 V: `P = 0.577*Vdc^2/R` -> **R_opt ~ 5.8 ohm**, Idc 4.9 A, **I_pk ~ 14 A**,
  conduction ~1.8 W. Then match 5.8 -> 50 ohm.
- Class E requires shunt C >= Coss: needed C_shunt ~ **252 pF** vs EPC2019 Coss **110 pF**.
  Coss is absorbed with room to spare -> **Class E is feasible at 20 MHz on this FET.**
- Costs vs DE: 3.6x voltage stress, higher peak current, narrowband + load-sensitive
  (no ZVS across load pull), ~88-90% vs ~92% efficiency. Gains: one FET, one $0.36 driver,
  no high-side/bootstrap/level-shift at all, no wound parts. Genuinely "bare bones".

## 2026-08-07 [topology] Rejected high-side workarounds (do not re-explore)

- **Gate drive transformer (GDT)** - classic for MHz Class DE, but a wound part; not
  JLC-assemblable. Violates the same constraint it is trying to rescue.
- **Push-pull with output transformer** - both FETs ground-referenced (nice), but again a wound
  RF transformer on a binocular core. Same violation.
- **Capacitive level shift into a floating LMG1020** (bootstrapped rail + DC restore clamp) -
  preserves DE and stays all-SMD, but is finicky at 20 MHz and is the opposite of "bare bones".
  Keep only as a fallback if the user insists on DE *and* full-JLC.
- **Digital isolator to the high side** - needs <2 ns part-to-part skew at 20 MHz. Nothing
  affordable qualifies.

## 2026-08-07 [driver][isolation] NO isolated gate driver IC runs at 20 MHz - the barrier is bandwidth, not skew

Follow-up after LMG1210 was confirmed unobtainable *globally* (not just at LCSC). Checked every
fast isolated driver family; all are rated for at most a few MHz regardless of their CMTI number:

| Part | Prop delay | Why it fails |
|---|---|---|
| UCC21520 (dual, one package -> good ch-ch matching) | 19 ns | Max switching freq nowhere near 20 MHz |
| Si827x | 60 ns | Far too slow |
| ADuM4121 | 39 ns | Far too slow |

**Key correction to intuition:** a large propagation delay is NOT itself fatal for Class DE -
a delay common to both channels merely time-shifts the whole drive and preserves dead time.
What kills it is (a) part-to-part/channel skew comparable to the ~6.5 ns dead time, and
(b) plain insufficient bandwidth. (b) is the actual wall here.

**Direct capacitive level-shift into a floating driver also fails on physics:** the DE switch node
slews ~100 V in ~2 ns = **~50 V/ns**. Common-mode current through the barrier is `C*dV/dt`, so even
a modest 100 pF of coupling injects **~5 A** of CM current and completely swamps the gate signal.
This is exactly the problem the LMG1210's monolithic level shifter existed to solve.

**Therefore: 20 MHz Class DE requires transformer-coupled gate drive.** Not a preference - the only
remaining mechanism. This is how MHz Class DE was built pre-LMG1210. Bonus: driving HS and LS
through identical windings on identical cores makes skew common-mode and cancels it to ~100s of ps,
which beats any IC solution. (Owner independently asked for exactly this symmetry - it is correct.)

Transformer sourcing options, none fully JLC-assemblable:
- Hand-wound GDT on small RF ferrite (type 61/67), ~$1 of core+wire, THT. Cheapest, 1-2 parts
  outside JLC PCBA.
- COTS SMD RF transformer (Mini-Circuits TX-2-5-1 / Coilcraft wideband) - Digikey, ~$3-5 ea,
  **not stocked at LCSC** (searched).
- PCB-embedded coreless transformer (two coupled spirals, adjacent layers). Zero BOM cost, 100%
  JLC-compatible since it is only copper - but unproven coupling/volt-second margin here. Only
  attempt with a deliberate prototype, not on a first article.

AC-coupled GDT drive needs DC restore: at D=36.6%, secondary swings +V*(1-D) / -V*D. Size drive
amplitude so the positive peak lands ~5 V (V~7.9 V -> +5.0 V / -2.9 V). EPC2019 Vgs range is
-4 V to +6 V, so that fits, but there is little headroom - do not overdrive.

## 2026-08-07 [tradeoff] The real decision is Class E (fully JLC, high current) vs Class DE (better stage, 2 parts off-catalog)

Only **Class E is achievable 100% within JLC PCBA** - EPC2019 (C2836675) + LMG1020 (C6423790) are
both stocked, single ground-referenced switch, no isolation of any kind. That is its whole appeal.
Its cost at 200 W is current: **15.9 A peak vs 6.9 A** for DE (2.3x), from the 3.56x peak-voltage
stress capping the bus at ~40 V on a 200 V part.

Unexplored avenue if Class E is ever revisited at higher power: a **650 V** GaN would let Class E
run a ~120 V bus -> `R_opt ~ 41.5 ohm` (nearly 50 ohm, almost no matching network!) and only 5.3 A
peak. Blocker to verify first: required `C_shunt` falls to ~35 pF, so the part's Coss(er) must be
**below** ~35 pF or ZVS is unreachable. Typical 650 V GaN sits at 50-60 pF - would need a small-die
high-Rds(on) part. Not yet checked against LCSC stock.

## 2026-08-07 [DECISION] Owner chose Class E, 100% JLC PCBA (2026-08-07)

Owner ruled after being shown the full DE-vs-E costing: **Class E, zero off-catalog parts.**
Class DE + GDT is NOT to be re-proposed unless the owner reopens it. Frozen operating point:

    f 20 MHz | P_out 200 W | Vdd 40 V | load 50 ohm via SMA
    R_opt 4.614 ohm  (P = 0.5768*Vdd^2/R)
    Vds,pk 142.5 V   (3.562*Vdd) on a 200 V EPC2019 -> 1.4x margin
    I_dc ~5.8 A @ 85% | Ids,pk ~16 A
    C_shunt 317 pF total; Coss 110 pF -> ~200 pF external C0G (>=250 V)
    Q_L = 5 -> L_series 184 nH, C_series ~447 pF
    L-match 4.614 -> 50 ohm: Q_m 3.14, L_m ~115 nH, C_m ~500 pF

## 2026-08-07 [thermal][rf] The output INDUCTOR is the hottest part, not the GaN - inherent to a low-Z Class E

Non-obvious and it drives the whole layout. In a SERIES-resonant tank the circulating current IS
the load current, so loaded Q sets the *voltage* across L and C, **not** the current through them.
At R_opt 4.614 ohm the tank carries **6.6 A rms** no matter what Q is chosen.

    P_L = I^2 * ESR = 43.6 * ESR,   ESR = omega*L/Q_inductor

- Q_L = 7 -> L 257 nH, ESR@Q150 = 0.32 ohm -> **14 W in one inductor.** Rejected.
- Q_L = 5 -> L 184 nH, ESR@Q150 = 0.154 ohm -> ~6.7 W. **Chosen.**
- Needs inductor Q > ~200 (thick-wire air-core territory) to get meaningfully below that.

Consequences: headline "86% efficiency" is optimistic; **budget 80-85%**, i.e. ~35-50 W of loss,
most of it in the passives rather than the semiconductor. Do not size the output network by
current rating alone - size it by dissipation and Q.

**Open BOM risk (resolve during build):** LCSC-stocked RF inductors that carry 6.6 A rms at
20 MHz with high Q are scarce. Fallbacks in order: (1) multiple SMD wirewound in parallel -
splits current AND halves ESR, (2) PCB air-core spiral - free, JLC-native, wide traces carry the
current, costs board area and gives moderate Q. Same story for the series C: 6.6 A rms through a
single C0G is too much, **parallel several** to split ripple current. Series L/C see
I*X = 6.6*23.1 = 152 V rms (~215 V pk) -> specify >=250 V, ideally 500 V C0G.

## 2026-08-07 [RETRACTED] The P1 "EPC2019 correction" was WRONG - the ORIGINAL brief numbers were right

**RETRACTED IN FULL.** A P1 agent (research-power-architect) reported Coss(er) 156 pF, Rds(on)
22/42 mohm, Qg 2.4/2.9 nC as "datasheet-verified" and this file recorded them. They are not in the
datasheet. The orchestrator later read the actual PDF pages (EPC2019 rev. (c)2021, pages 1-2)
directly. **Authoritative values:**

| Parameter | Value (datasheet, read directly) |
|---|---|
| Rds(on) | **36 typ / 50 max mohm** (cover headline is literally "R_DS(on), 50 mohm") |
| Coss | **110 typ / 150 max pF** @ VGS=0, VDS=100 V |
| Qoss | **18 typ / 23 max nC** @ VDS=100 V |
| Qg | **1.8 typ / 2.5 max nC** |
| Ciss / Crss | 200/270 pF, 0.7/1 pF |
| VGS abs max | **+6 / -4 V** |
| Thermal | RthJC **2.7**, RthJB **7.5**, RthJA **72** C/W (the one thing P1 got right) |
| ID | 8.5 A cont. (Ta 25 C), 42 A pulsed |
| Package | passivated **die with solder bars**, 7-bar row (P1's package correction WAS right) |

**There is NO Coss(er) or Coss(tr) figure anywhere in this 6-page datasheet.** Any design that
needs an effective Coss must derive it, and say so.

**Method lessons (two, both expensive):**
1. Never let a web-summary spec into a frozen operating point (the original sin).
2. **An agent asserting "datasheet-verified" is not verification.** Two agents contradicted each
   other; only reading the PDF settled it. For any number the whole design hangs on, the
   orchestrator reads the primary source itself. Cost of not doing so here: a whole P2
   architecture built on an invented capacitance.

## 2026-08-07 [class-e][gan] Charge-equivalent Coss, not small-signal Coss, sets the Class E device budget

Falls out of the retraction above and drives the FET-count decision.

- Small-signal `Coss = 110 pF` is quoted AT VDS=100 V. Coss is strongly nonlinear (far larger near
  0 V), so 110 pF is NOT the number to compare against the Class E shunt requirement.
- The right estimate is the **charge-equivalent** value: `Coss_eff = Qoss/V = 18 nC / 100 V
  = ~180 pF per FET`.
- Required total shunt at the nominal point is `C_shunt = 1/(omega*R*5.4466) = 317 pF`.
- Therefore **N x 180 <= 317 -> N <= 1.76**: at Vdd = 40 V only ONE FET fits the ZVS budget, and
  the architect's "2 x Coss(er) = 312 pF lands on 317 pF" result was an artefact of the invented
  156 pF number.

**The escape is a slightly lower bus, and it is a good trade.** Solving for the bus at which two
FETs' own capacitance exactly equals the requirement:

    need C_shunt = 2 x 180 = 360 pF
    R = 1/(omega * 360pF * 5.4466) = 4.06 ohm
    R = 0.5768 * Vdd^2 / P  ->  Vdd = sqrt(4.06 * 200 / 0.5768) = ~37.5 V

At **Vdd 37.5 V**: R_opt 4.06 ohm, **zero external shunt cap** (device Coss IS the shunt),
Vds peak `3.562*37.5 = 134 V` (better margin on a 200 V part than the 142.5 V at 40 V), I_dc ~6.5 A,
and per-FET conduction `4.45^2 * 0.036 = 0.71 W` typ / 0.99 W at max Rds - roughly half the
single-FET figure. Two FETs remain the right call; the BUS moves, not the FET count.

## 2026-08-07 [CORRECTION][magnetics] Paralleling inductors does NOT reduce loss - Q_total = Q_each exactly

Directly corrects the "parallel several - splits current AND halves ESR" claim written earlier in
this file. Two agents derived the refutation independently.

For N inductors in parallel each of `L_each = N*L_target` (so the combination equals L_target):
- `ESR_each = omega*L_each/Q = N*omega*L_target/Q`
- current splits to `I/N`, so loss per part = `(I/N)^2 * N*omega*L/Q = I^2*omega*L/(N*Q)`
- **total over N parts = `I^2*omega*L/Q`** - identical to a single inductor of L at the same Q.

Paralleling is a **heat-spreading** measure only. It buys thermal area, never efficiency. The only
lever on magnetics loss is **Q**: total magnetics dissipation here is a clean **`1627/Q` watts**.

## 2026-08-07 [magnetics][layout] No LCSC inductor closes L_s - the PCB air-core spiral is PRIMARY, not a fallback

Exhaustive sweep (13 inductor searches). The catalog splits into two useless halves:
- **Molded/shielded power inductors** (Sunlord, Vishay IHLP): current is fine (12-25 A) but Vishay's
  own datasheet caps the family at "up to 5.0 MHz"; reading Q-vs-F past that gives **Q ~20-40 at
  20 MHz -> 25-50 W in one part** against a ~6.7 W budget.
- **Genuine high-Q RF inductors** (Murata LQW, Q>=25 at 100 MHz): frequency is fine but rated
  **120-140 mA** - roughly 47x short of 6.6 A rms.

Nothing bridges the gap, and per the correction above, paralleling cannot rescue it. Therefore:
**etch L_s (and L_m) as PCB air-core spirals.** Top pick 2 turns, 25 mm mean diameter, computed
**Q ~130-150**, ~900 mm2, **zero BOM cost**. Expect 100-140 C copper -> specify **high-Tg FR4
(TG155+)**.

Capacitors are the good news: **8x YAGEO CC1206JKNPOCBN560** (56 pF / 1 kV C0G, **C113875**,
stock ~8100) = 448 pF for C_s; same part x3-4 for C_shunt. Loss is tanD-limited (~0.8-1.2 W for the
whole bank, ~145 mW/part), NOT a paralleling-count problem.

## 2026-08-07 [thermal][BLOCKER] The EPC2019 thermal path does not close at 200 W with ONE FET

The most serious P1 finding. Uses EPC2019's own datasheet R-th (JC 2.7, JB 7.5, JA 72 C/W), not a
generic family estimate:

- At the nominal **8.9 W** in Q1, the **junction-to-BOARD rise alone is ~66 C** of an 85 C budget.
  This is unfixable by layout or heatsink - it is inside the package.
- Tj lands **~138 C vs a 125 C target even with a hypothetical 0 C/W heatsink**; a max-Rds(on) part
  out of JLC's reel reaches **~204 C**. EPC implicitly rates this part around 2.9 W; we are asking 3x.
- Required heatsink <=0.3 C/W forced air (100x60x30 extrusion + 25-40 CFM). A passive bolt-on
  (0.8-1.5 C/W) is **insufficient**. Removing 1 W from Q1 beats any heatsink improvement 3:1.

**Proposed fix (P1 recommendation, needs owner ruling): parallel TWO EPC2019.** Conduction halves,
RthJB halves per die, Tj falls **138 -> ~103 C**, and elegantly **2 x Coss(er) = 312 pF lands almost
exactly on the required 317 pF C_shunt, so the external shunt cap disappears entirely.** Costs
~0.7 pt efficiency (hysteresis loss doubles as shunt C becomes GaN rather than C0G) and imposes a
symmetric-gate-drive layout problem. Gate charge doubles to 116 mA - still inside the 0.3 A rail.

## 2026-08-07 [floorplan][CONFLICT] A metal heatsink under a PCB spiral inductor is a SHORTED TURN

Emergent collision between two independently-correct decisions (bottom-side heatsink + PCB spiral
magnetics). Forces a **two-zone floorplan**, which is now a hard layout constraint:

- **Heatsink zone:** Q1, the RF choke L1, bulk caps, the driver. Gets the bottom-side sink.
- **Magnetics zone:** L_s, L_m, tank caps. **No heatsink coverage, and an L2 ground-plane keepout
  under the spirals** (a solid plane under a spiral is also a shorted turn and destroys its Q).

The L2 keepout directly contradicts the otherwise-mandatory "unbroken L2 GND" rule - the plane stays
unbroken under the POWER LOOP, and is deliberately cut out under the SPIRALS only.

**Also missed in the original loss list: L_m (the match inductor) dissipates ~6.3 W** - it carries
the same 6.58 A rms as L_s, making it the second-hottest item on the board. Total board loss
35.0 W @ 85.1% nominal / 50.5 W @ 79.8% worst.

## 2026-08-07 [CORRECTION][class-e] The FROZEN operating point was wrong: Sokal's 5.4466 is the Q_L -> infinity constant

The single most consequential numeric error in this whole run, and it was in the original brief.

`C_shunt = 1/(omega*R*5.4466)` is Sokal's coefficient for **Q_L -> infinity**. This board runs
**Q_L = 5**, which has its own published finite-Q_L coefficients (reproduced from Sokal's fits to
0.008% and 0.13%). Using the wrong constant mis-sized both the load resistance and the shunt:

| | Frozen (WRONG) | Corrected (Q_L = 5) |
|---|---|---|
| R_opt | 4.614 ohm | **4.13 ohm** |
| C_shunt | 317 pF | **403 pF** (+38-46 pF if Sokal's finite-choke term applies) |
| L_s | 184 nH | **164 nH** |
| C_s | 447 pF | **518 pF +/-5%** (pending SIM-4) |
| L_m | 115 nH | **110 nH** |
| C_m | 500 pF | **530 pF** |
| I_tank | 6.58 A rms | **6.96 A rms** (conductor widths +12%) |

Magnetics loss barely moved, for a non-obvious reason: `P = 200*Q_L/Q_ind` is **R-independent**.
Board loss 38.6 W, **83.8% efficiency** nominal - still inside the frozen 80-85% band.

## 2026-08-07 [CORRECTION][class-e] Coss(tr) must be evaluated over the ACTUAL drain swing, and Vdd is not a ZVS knob

Two further corrections to the orchestrator's own mid-run analysis:

1. **`Qoss/V = 18 nC/100 V = 180 pF` is the average over 0->100 V only.** This drain swings to
   142.5 V, where Coss has fallen further. Two independent extrapolations (a power law anchored on
   both published points; a flat-above-100 V bound) agree to 1.5%:
   **Coss(tr) = 158 pF typ / 205 pF max**, so the pair is 316/410 pF.
   Note `Coss(er)` (energy-equivalent, ~119 pF here) is the **hard-switching** figure and is the
   WRONG basis for Class E - the Class E waveform is charge-driven, so `Coss(tr)` is correct.
2. **Vdd is NOT a ZVS knob.** The Class E equations are linear in Vdd, so lowering the bus cannot
   fix a shunt-capacitance error (the orchestrator's 37.5 V proposal was misconceived on this
   point). Vdd IS a free **thermal derating** knob with zero rework:
   `40 V/200 W -> 133 C` vs `36 V/162 W -> 119 C` at the max corner.

## 2026-08-07 [class-e][design] An external shunt trim cap is a FEATURE - "it disappears" was a defect

Counterintuitive and worth keeping. The architecture briefly celebrated that paralleled-FET Coss
exactly met C_shunt so no external cap was needed. That is backwards: **EPC2019 Coss spreads
110-150 pF (+36%) part to part.** If device capacitance is the entire shunt, that spread lands
directly on ZVS with nothing to absorb it. The external C0G cap is the only trim element.
Now **populated at 3 x 33 pF (~87 pF), NOT DNP.**

## 2026-08-07 [thermal][gan] Paralleling FETs does not reduce dissipation - it halves thermal RESISTANCE

Same shape as the inductor-paralleling correction earlier in this file, and just as easy to get
wrong. Total FET dissipation vs count: `P_FET(N) = 5.48/N + 2.42N + ...`

| N | P_FET total | Verdict |
|---|---|---|
| 1 | 11.17 W | **Tj 160 C with a hypothetical 0 C/W heatsink - ABOVE the 150 C abs max. No heatsink saves it.** |
| 2 | 11.25 W | **Chosen.** 114 C nominal / 133 C at the max-datasheet corner, needs theta_HS <= 0.7 C/W |
| 3 | 13.16 W | +1.9 W and a three-way gate match that cannot be mirrored |

Dissipation is essentially flat from N=1 to N=2 - **the entire win is RthJB halving per die.** The
earlier "k=2 is exactly the ZVS ceiling" argument was retracted by its own author (real ceiling
2.55); the correct argument is thermal and quantitative.

Gate-loop budget tightened to **0.48 nH/FET** (Ciss 200 pF -> C_GS ~199 pF, not the ~350 pF the
retracted Qg implied). This is now the tightest layout spec on the board. Fallback if unachievable:
R_G = 3 ohm -> 0.84 nH at +0.3 W turn-off loss.

## 2026-08-07 [footprint][gan] EPC2019: the 0.68-0.70 mm figure is the OUTER ENVELOPE, not a pad centre spacing

A fixer was instructed (by the orchestrator, on a librarian report) to widen EPC2019 column 1 from
0.46 to ~0.68-0.70 mm. It refused, extracted the datasheet's vector geometry, and proved
**both end columns are 0.45 mm centre-to-centre.** The 680/700 numbers are the envelope:
`450 + 230 (mask dia) = 680`; `450 + 250 (bump dia) = 700` = dim `c` = bar-pad length.
Cross-check: `(B-h)/2 = (950-450)/2 = 250` = dim `i`, which only closes if h applies to both ends.

**Applying the "fix" would have shifted the GATE pad 0.11 mm off a 0.25 mm pad** - the dead-board
failure the task existed to prevent. Correct action taken: 0.46 -> 0.450 exact, copper to bump size
with -0.01 mask margins (a genuine mask-defined land).

**Lesson: a land-pattern dimension read out of a report, not off the drawing, is a rumour.**

## 2026-08-07 [sourcing][jlcpcb] LCSC's package/type fields are USELESS for connector mount style - check pad layers

The part-sourcer marked an SMA "CONFIRMED genuine SMD board-side-launch". The manufacturer drawing
showed a vertical **through-hole** screw-thread panel jack. Both good and bad parts read
"Board Side ... SMA SMD" in LCSC's fields; `package: "Plugin"` (Chinese for plug-in/THT) is the
only tell, and it is not always present. **"Board Side" is a connector TYPE, not a mount style.**

Reliable two-step screen, now proven:
1. Pull the EasyEDA footprint and **inspect which layers its pads are on.** Any **B.Cu land** means
   it protrudes/needs bottom copper - fatal for a flat bottom-side heatsink face.
2. Confirm against the **manufacturer's customer drawing**, not the LCSC listing text.

Result: 4 of 4 orchestrator-suggested candidates were THT; 5 of 7 SMD-labelled alternates carried
B.Cu lands. Winner **C22418168 / CONSMA001-SMD-G-T** (TE/Linx) - drawing sheet 1 states verbatim
"Termination: PCB Surface Mount", centre-contact standoff 0.00-0.10 mm (nothing below the board).
**Cost of correctness: $0.39 -> $2.97 each** (+$25.86 on a 5-board build). 100% SMT preserved.

Also: pulled footprints carried two other latent fab defects worth checking for generally -
an `attr through_hole` on a surface-land cap (would have put it in the P9 CPL's THT column), and
courtyards that cut through their own pads. And **tent EP thermal vias on both faces** when a
bottom heatsink is involved - a mask-opened via there takes solder and breaks flatness.

## 2026-08-07 [layout][gan] Layout constraints to honour when this board is built

Not yet verified on hardware - carry into the layout step:

- 4-layer is mandatory, not a nicety: L2 must be an unbroken GND directly under the power loop so
  the HF return image sits ~0.2 mm below the forward path. Loop area, not trace width, sets the
  ringing that the 2x voltage derate is protecting against.
- Skin depth in Cu at 20 MHz is **14.6 um** - 1 oz (35 um) is only ~2.4 skin depths. Tank and
  power-loop conductors must be wide/poured; do not size them by DC current alone.
- EPC2019 is a 1.35 mm chip-scale LGA, **bottom-cooled through its solder balls** - the thermal
  path is vias straight into plane copper. At ~92% efficiency, 200 W means ~16 W to remove.
- Input decoupling must be multiple small-case (0402/0603) C0G/NP0 right at the FET pair; bulk
  electrolytic does nothing at 20 MHz. Avoid X7R for the tank (voltage/temp coefficient); use C0G.

## 2026-08-08 [driver][gan][gate] TI's ">=2 ohm at each output" is a PER-PIN floor, and paralleled FETs multiply it

The LMG1020 datasheet (s8.2 Typical Application) says "use at least a 2-ohm resistor at each OUTH and
OUTL". Read as a per-LEG spec that is easy to satisfy and easy to get wrong. This board hangs BOTH
paralleled EPC2019 off the same OUTH/OUTL pins, so the pin sees the PARALLEL combination of every
branch on it: 2 x 3R9 per leg x 2 FETs = 4 x 3R9 = **0.975 ohm**, less than half the floor, while
each individual leg looked like a compliant-ish 1.95 ohm and the schematic note said so. Nothing in
ERC, netlist_audit or check_* can see it - it is arithmetic over a net, not a rule violation.

The general form: with N devices on one driver pin, **each branch must be >= N x (the datasheet
floor)**. Here N=2 -> 4 ohm/branch minimum; 4R7 was taken (2.35 ohm/pin, 2.13 A peak instead of
5.1 A). The floor exists to bound gate-loop di/dt, and on an eGaN part the consequence of ringing is
not degradation but destruction: VGS abs max is +6 V against a 5 V drive, ~1 V of headroom, no
avalanche margin, gone on the first pulse.

TWO SECOND-ORDER EFFECTS THAT BOTH POINT THE SAME WAY, and are worth knowing BEFORE choosing R:
- **The gate-loop inductance budget scales as R^2.** EPC WP008 Eq.1 is L <= R^2.C_GS/4, so going
  3.1 -> 5.85 ohm total moved "the tightest layout spec on the board" from 0.48 nH to 1.70 nH. Raising
  R_G to fix a driver-floor violation BUYS layout margin; do not also keep treating the old
  inductance number as binding when picking package sizes.
- **Per-resistor dissipation goes UP even though total gate power does not.** Total is Qg.VDD.fSW per
  FET regardless of R; what changes is the split between the driver's internal impedance and the
  external resistor, and collapsing 2 parallel parts into 1 doubles the per-part share on top. Here
  0.029 W/part -> 0.100 W/part at Qg_max, which an 0603 (100 mW, 65 mW derated to a 90 C local board)
  cannot take. Size the package from Qg_max x VDD x fSW / 2 x R_ext/R_total, derated to the LOCAL
  board temperature, not the 70 C datasheet point.

## 2026-08-08 [lm5017][cot][power] Type 3 ripple injection RAISES the DC output by half the injected FB ripple

A constant-on-time regulator ends its off-time when FB falls back through VREF, i.e. it regulates the
**valley** of FB, not its average. With Type 3 injection the ramp is AC-coupled into FB (Cac 100 nF
into a ~7.5k Thevenin divider = tau 750 us against a 1.8 us period, so DC is genuinely blocked and the
ramp's mean is zero), which means FB_dc = VREF + Vramp/2 and therefore

    VOUT = (1 + R_top/R_bot) x (VREF + Vramp_pkpk / 2)

NOT VREF x the divider ratio. At 78.6 mV of injected ripple that is +3.2 % - 5.06 V where a naive
valley calculation says 4.90 V. A P4 reviewer computed the rail's min/nom/max entirely without the
term and concluded the nominal was 100 mV low; the sheet's own docstring had it right. Both readings
matter in practice because Vramp carries Rr, Cr and K tolerance, so the honest thing is to solve the
divider against the UNION - effective reference in [VREF_min, VREF_max + Vramp_max/2] - and check
both corners. Doing that here forced 30.9k/10.0k rather than the reviewer's suggested 31.6k, which
is fine under the valley reading and ~60 mV over the driver's recommended VDD max under the ramp one.
Also check the FB OVERVOLTAGE comparator against FB's PEAK (VREF + full Vramp), not its average: the
LM5017 trips at 1.62 V and terminates the on-time pulse.

## 2026-08-08 [footprint][sourcing][polarity] On the RVT (JIERR/Lumimax) V-chip electrolytic family the CHAMFERED corners mark the ANODE

The usual reading of a chamfered/bevelled base corner on an SMD aluminium electrolytic is "cathode",
and a P4 review flagged C101/C102 as unadjudicated on exactly that basis: the EasyEDA symbol puts "+"
at pin 1 while the footprint's only asymmetric feature - two chamfers - sits on the PAD-1 side, so
symbol and footprint appeared to contradict each other. The manufacturer drawing settles it the other
way. JIERR "RVT series" (LCSC C51953411, now committed at parts/C51953411.pdf) page 2 labels the two
terminals "Positive" and "Negative" with leaders, and **"Positive" lands on the chamfered end**;
Lumimax's SMDGP/RVT drawing agrees from the opposite face, putting the black negative top-stripe on
the SQUARE-cornered side. So the pull was self-consistent and correct all along.

Two transferable points. (1) LCSC's product page is HTML at `lcsc.com/datasheet/C<code>.pdf`; the
real PDF link is inside it (`datasheet.lcsc.com/datasheet/pdf/<hash>.pdf`) - an empty `datasheet`
field in parts.json usually means nobody followed the redirect, not that no datasheet exists. Fill it
at P3; a blank one on a POLARIZED part is what turned this into an unresolvable review finding.
(2) A chamfer is a BODY-OUTLINE feature, not a marking: this footprint's silk body square is +/-5.23 mm
and the part's plastic base is 10.3 mm, so once assembled the cue is invisible for inspection. Even
when the geometry is right, a polarized part still needs a real silk "+" placed OUTSIDE the body.

## 2026-08-08 [kicad][footprint][connectivity] Footprint copper GRAPHICS are not in KiCad 10 connectivity - an etched-copper part must be made of PADS

(Relocated from root LEARNINGS.md - this workspace keeps its own file while concurrent runs are in
flight. Discovered building the PCB spiral inductors, `kicad/gen/spirals.py`.)

KiCad's own `NetTie.pretty` draws its shorting bar as an `fp_poly` on F.Cu, so `fp_poly` on a copper
layer looks like the natural way to author an etched component (spiral inductor, PCB antenna,
current shunt, coplanar structure). **It is not.** Measured on 10.0.3 with a scratch board
(`CreateEmptyBoard` + `FootprintLoad` + pad nets + `kc.py drc`):

- an `fp_poly` on F.Cu joining two same-net pads 18 mm apart leaves them **`unconnected_items`** -
  the graphic carries no net and conducts nothing as far as connectivity is concerned;
- it additionally raises **`shorting_items`** ("nets <blank> and NA") against every netted pad it
  touches, because it is netless copper;
- `(net_tie_pad_groups "1, 2")` suppresses the `shorting_items` half but NOT the unconnected half.

The stock NetTie footprints get away with it only because each of their nets has exactly one pad, so
nothing is left to be unconnected to. Easy to misdiagnose: a footprint whose winding is a graphic
DRCs "clean" apart from an unconnected count that reads like a placement problem.

**Correct encoding for copper-is-the-component parts, all verified on 10.0.3:**
- winding/antenna body = `(pad "N" smd custom ... (primitives (gr_poly ...)))`, one per copper
  layer; ~440-point primitives load, round-trip and plot fine;
- `(net_tie_pad_groups "1, 2")` for the deliberate pad1-pad2 short (an inductor IS a DC short);
  pads of DIFFERENT numbers may overlap inside a tie with no violation;
- footprint-level rule areas `(zone ... (keepout (tracks not_allowed) (vias not_allowed)
  (pads allowed) (copperpour not_allowed)))` ARE supported, round-trip through pcbnew
  (`fp.Zones()` -> `GetIsRuleArea() True`), and are how a "no plane under this part" rule travels
  with the footprint;
- an SMD pad on inner layers only (In1+In2 bridge) works but costs one **`padstack` WARNING**
  ("SMD pad has no outer layers") that must be waived;
- duplicate pad numbers mixing `smd custom`, `smd rect` and `thru_hole` in one footprint are legal
  and connect correctly wherever they share a layer - `thru_hole` is the ONLY thing that ties an
  F.Cu pad to an In1/In2 pad at the same x,y.

**Second-order trap: DRC cannot check clearances INSIDE a net tie.** The tie exempts pad1<->pad2
entirely, so the inner-land-to-adjacent-turn gap (0.014 mm in the first cut of this part - a shorted
turn that would have collapsed the inductance) reports nothing at all. Any critical spacing between
tied pads must be enforced in the generator and measured out-of-band; **a scratch-board DRC pass is
NOT evidence that a net-tie part is geometrically sound.**

## 2026-08-08 [placement][p6] Locking a group ANCHOR silently orphans the whole group in place_seed/place_anneal

`constraints.json.placement.fixed` on this board holds Q201, U201, R203-R206, L301, L302, J101,
J301 - i.e. the anchors of `switch`, `tank_ls`, `tank_lm`, `drive_in`, `bus_in`. `placelib.
build_clusters` sends any footprint that is `not is_movable or ref in placement.fixed` to the
**fixed** list, so a group whose anchor is fixed produces **no cluster at all**: place_seed's report
listed only 4 clusters (C110, C111, R104, U101) out of 6 declared groups, and C101-C104, C207-C212,
L201, L202, R201, R202 were left untouched at their P5 shelf coordinates (they then read as
`outside_outline` / `courtyard_overlap`). The same mechanism drops `separation` entries -
place_anneal reported `separation_unknown_refs: ["L301","L302","U201"]`, so the declared
"U101 >= 30 mm from either spiral" was never enforced and had to be checked by hand.

**Consequence for any board with a hand-built floorplan: everything in a group whose anchor you
lock is yours to place.** Here that meant hand-placing 50 of 70 parts and leaving only the `hk`
cluster (the one anchor NOT in `fixed`) to seed+anneal.

## 2026-08-08 [drc][gan][footprint] The EPC2019 land pattern cannot meet this board's own /SW HV clearance rule

`rules_gen` emits `aiee_hv_143v_SW (clearance min 0.8mm)` from `constraints.json.voltages` for the
142.5 V drain node. The EPC2019's datasheet land pattern is a 0.6 mm-pitch solder-bar row, so
drain-to-source pad gaps are **0.35 mm** by construction -> **12 intra-footprint clearance errors
(6 per FET) that no placement can fix**. Same class: the easyeda2kicad `SOIC-8 ... EP2.0` used for
U101 carries **4 netless PTH holes inside the exposed pad**, giving 4 more clearance errors + 4
`solder_mask_bridge`. Both need a DRU exception or a P8 waiver, not moves.

**And the U101 holes are a floorplan constraint, not just a DRC nuisance**: they pierce the board,
so they violate HS-2 ("no through-hole pins, no untented vias" in the bottom heatsink land
[5,10,36,70]). The buck had to be moved out of that rect (+14 mm in x) - which is the *opposite*
of `blocks.md` B2's "place at the DC-input end", because the DC-input end IS the heatsink land.

## 2026-08-08 [placement][routing] The spiral's 20.55 mm pour keepout vs the tank nets' 8.4-11.9 mm DRU width floor

`aiee_pwr_width_SW` = 11.89 mm, `aiee_pwr_width_tank_TANK_A/B/RFOUT` = 8.41 mm - those apply to
**tracks only**; a zone is not a track (see root LEARNINGS, pd-trigger). But the spiral footprints
carry `copperpour not_allowed` (tracks/vias/pads allowed) on F.Cu+B.Cu out to r = 20.55 mm, so
**inside a 41 mm circle around each spiral the tank nets can only be tracks, and a track there must
be >= 8.41 mm wide.** Placement consequence: every tank pour must live OUTSIDE both keepout circles
and reach the terminal lands with a short, full-width track (2-3 mm long, which fits: the lands are
8 mm tall). The pour-legal channel between the two circles is the binding dimension - at L301
(72,18) / L302 (85,62) it is **~5.0 mm at its narrowest (x ~ 79)**, which is why the spirals are
offset 13 mm in x rather than stacked on the same centre line (same-x would pinch it to 3.9 mm).

## 2026-08-08 [placement][gate-drive] LMG1020 at 270 deg is the only rotation that makes four gate legs exact mirrors

The YFF0006 has OUTH (A2) and OUTL (B2) in the SAME COLUMN at 0/180 deg, so they can never both sit
on a horizontal mirror axis. At **270 deg** the map is local (lx,ly) -> (-ly, lx), which puts
OUTH and OUTL on the same y row (`Yu+0.2`) with the inputs on the other row - so both outputs land
ON the axis and the four legs are congruent by reflection. Measured on this board: OUTH->R203 and
OUTH->R204 both **2.332 mm**, R203->gate(Q201) and R204->gate(Q202) both **2.012 mm**, OUTL legs
both 4.244 / 2.280 mm. Put the OUTH (7 A source) pair on the INNER slots - the outer pair is
~2.4 mm longer and that difference should be spent on the 5 A sink, not the fast edge.

Corollary on die orientation: the EPC2019's gate (pin 1) and its nearest source (pin 2) share the
-x end column 0.45 mm apart, so **both FETs must be at the SAME angle and stacked in y**, drains
escaping inward into a shared /SW channel and sources outward into two GND islands. A 180 deg
"mirror" of one die swaps its drain and source sides and forces /SW and GND to cross.

## 2026-08-08 [kicad][silk] place_edit `add_text` is idempotent only at the SAME coordinates - and there is no delete op

`add_text` matches an existing text by (string, layer, position within 0.01 mm). Emitting the same
string at a *new* position therefore ADDS a second copy, and no `del_text` op exists. A misplaced
silk mark cannot be un-done through the ops interface. On this board the C101/C102 polarity "+"
landed on pad 1; the fix was to **move the capacitors** 1 mm instead of moving the text.

## 2026-08-08 [placement][mech] J101 (KF128 at the left edge) cannot satisfy HS-3 and silk_edge_clearance at once

The KF128's F.SilkS body outline spans local y -5.40..+5.30; at 270 deg (opening out the left edge,
confirmed by an orthographic `--views left` render) that is abs x -5.30..+5.40 about the centre.
HS-3 requires the THT pads clear of the heatsink rect x >= 5, i.e. centre x <= 3.8 -> the silk
overhangs the board edge by 1.6 mm -> **6 `silk_edge_clearance` warnings**. Centre x = 5.65 makes
the silk clean but puts the 2.4 mm pads 1.85 mm into the heatsink land. Structure wins: J101 stays
at x = 3.7 and the silk overhang is a P7 footprint trim (or a P8 waiver).

Also confirmed from the same render: **`SMA-SMD_CONSMA001-SMD-G-T` is a VERTICAL (top-mount) jack,
not an edge launch** - 4-fold symmetric GND pads with the signal pin at the footprint origin, barrel
standing perpendicular to the board. `blocks.md` B3/B8 call it "SMD edge-launch"; that description
is wrong, though the choice is still correct (no bottom-face solder joints). Rotation is
electrically irrelevant for J201/J301, and neither actually needs to be at a board edge.

## 2026-08-08 [drc][creepage][gan] A qualified die's OWN terminal pitch is not a board creepage violation - the "part choice is the defect" rule has an exception

Refines the root-LEARNINGS entry "a voltage-class DRU rule only protects the nets you NAMED, and the
ICD's own part-size policy can violate its own creepage rule", whose conclusion was: *if a creepage
rule is tighter than a land pattern's own pad gap, the PART choice is the defect.*

That holds when the part was chosen by policy and a larger one exists (lumina-par's 0805 -> 1206).
**It does not hold here.** P6 on rf-de-20m produced 12 `clearance` errors that are all intra-EPC2019:
its 0.6 mm solder-bar pitch leaves ~0.35 mm drain-to-source gaps, against the board's own
`aiee_hv_143v_SW` rule of 0.8 mm (IPC-2221, derived from /SW's 143 V peak).

Why this one is a waiver and not a part-selection defect:
- The 0.35 mm gap is **die geometry** on a manufacturer-qualified **200 V** device. EPC rates the
  part at 200 V *with that pitch*; the spacing is internal to a passivated die, not board copper.
- **IPC-2221 creepage/clearance governs board-level conductor spacing**, not the terminal geometry
  of a qualified component. Applying it inside a footprint is a category error.
- There is **no alternative part**: EPC2019 is the only 200 V GaN that closes this design, and every
  eGaN FET in this class has comparable bar pitch. "Choose a bigger part" has no referent.

**Practical rule:** when an HV DRU rule fires *inside* a single footprint, first ask whether the
pads belong to a qualified component or to board copper. Component-internal -> document and waive
with the vendor's own voltage rating as evidence. Board copper (including two discrete parts placed
close, or one part's pads on a land YOU specified) -> the original rule applies and it is a real defect.

Same board, same class, DIFFERENT verdict: U101's 4 `solder_mask_bridge` errors come from netless
PTH holes inside the LM5017's exposed pad. Those ARE ours (a pulled-footprint artefact), so they get
fixed or re-drawn, not waived.

## 2026-08-08 [constraints][COORDINATE TRAP] P5 never translated the board-local rects - `planes` and the heatsink keepout were pouring/checking the WRONG PART OF THE BOARD

`stackup.md` s2.1 calls this out as a **MANDATORY P5 step** and it was missed. Verified by reading
the consumers: `planes_gen._region_rect` takes `planes[].region` **verbatim as board coordinates**
(no translation anywhere in the module) and `placelib._forbidden` builds `box(*k["rect"])` the same
way. `board_init` put this outline at **origin (6.635, 39.335)** (`log/P5-board_init.json.
outline_origin`), so the untranslated rects landed like this:

| declared (board-local) | what the script actually used | effect |
|---|---|---|
| zone A `[0,0,48,80]` | absolute (0,0)-(48,80) | poured only board-local x 0-41.4, **y 0-40.7** - the bottom half of zone A, including the buck and half the FET thermal island, would have had NO plane |
| zone C `[88,0,100,80]` | absolute (88,0)-(100,80) | landed at board-local x 81.4-93.4, **on top of L301** - nowhere near the C_m bank |
| heatsink keepout `[5,10,36,70]` | absolute (5,10)-(36,70) | board-local [-1.6,-29.3,29.4,30.7] |

**Why nothing caught it:** `constraints_lint` does not know the outline; `place_metrics` never fired
the keepout because it is declared `side: "back"` while every part is front-side **and** because
`_forbidden` is gated on `f.is_movable` (everything was locked by then). A bad rect is silent until
P7 pours copper in the wrong place.

Fixed at P6: every rect in `kicad/constraints.json` is now **absolute**, with `_coord_note` /
`_planes_note` recording the translation and the board-local equivalent. **Check this on any board
whose `board_init` outline does not start at (0,0) - which is all of them.**

## 2026-08-08 [planes][rf] Zone B split the GND plane in two - the tank's 6.96 A return had no path at all

Two 41 mm keepout discs (r = 20.55 mm) stacked across an 80 mm board leave no route around either
edge: at y=0 L301 blocks x 61-83, at y=80 L302 blocks x 79-91. With `planes` declaring only zone A
and zone C, In1/In2/B.Cu GND are **two disjoint islands** and the return from C_m + J301's shell to
the Q201/Q202 sources does not exist.

**The corridor is 5.0 mm, not 2.8 mm** - 2.8 mm is the answer for a *straight horizontal strip*
(the intersection over all x of the two circles' y-spans); a pour may bend, and the true minimum is
the perpendicular gap `d - 2R` projected onto the corridor direction. Nudging the centres to
(72,17.6) / (85,62.6) takes d from 45.88 to 46.84 mm and the channel from 5.01 to **6.02 mm**,
costing 0.4 mm of copper-to-edge margin each (1.05 / 1.11 mm remain) and *reducing* mutual coupling.

**Carry the bridge on B.Cu, not the inner layers.** B.Cu is 1 oz against the inner layers' 0.5 oz
(0.64 vs 1.13 mOhm/sq at 20 MHz) and sits 1.554 mm below F.Cu, so a TANK_A pour crossing it couples
~4.7 pF instead of ~29 pF on In1 - and In1/In2 stay completely unpoured in zone B exactly as the
architecture specifies. Verified geometrically after the fix: **B.Cu = one 6393 mm2 island spanning
x 0-120; In1 and In2 = two islands each, deliberately.**

**Numbers, so the corridor width is not argued by adjective.** 6.96 A rms, pinch ~16 mm long:
at 6 mm wide R = 1.7 mOhm (82 mW, 0.85 mW/mm2 - 8x under the 7 mW/mm2 rule) and partial L = 7.2 nH;
at 10 mm wide, 1.0 mOhm (49 mW) and 5.8 nH. **Widening 6 -> 10 mm buys 33 mW and 1.4 nH** - 0.5 %
of the 274 nH series tank, against the ~25-35 nH the TANK_A/TANK_B bridge already contributes. That
is why the r=20.55 keepout was NOT cut: it is an undocumented 4.0 mm guard band (no derivation
exists in `spiral-design.md`), cutting it is an un-analysed magnetics change to the board's
highest-value component, and it would need both footprints regenerated and re-imported onto a board
carrying 66 locked placements.

## 2026-08-08 [PIPELINE BUG][planes][constraints] constraints rects are consumed as ABSOLUTE board coords, but board_init does not place the outline at the origin

**This is a skill-level defect, not a board-level one - it should be promoted to root LEARNINGS.md
once the concurrent runs settle.** Found at rf-de-20m P6 while chasing a missing GND return.

`planes_gen._region_rect` and `placelib._forbidden` consume `constraints.planes[].region` and
`placement` `rect` **verbatim as absolute board coordinates**. But `board_init` placed this 120x80
outline at origin **(6.635, 39.335)**, not (0,0). Architecture authors rects in the natural
board-local frame, so every rect silently lands displaced by the outline origin:

| Declared (board-local) | What it actually meant | Consequence |
|---|---|---|
| zone A `[0,0,48,80]` | poured only board-local x 0-41, **y 0-41** | buck + half the FET thermal island get **NO plane** |
| zone C `[88,0,100,80]` | landed **on top of L301** | plane over a spiral = shorted turn |
| heatsink keepout `[5,10,36,70]` | equally displaced | keepout guarding nothing |

**Nothing in the pipeline catches this:** `constraints_lint` does not know the board outline, and
`place_metrics` never fires the keepout (it is declared `side:"back"` and gated on `is_movable`).
`stackup.md` s2.1 documents translation as a mandatory P5 step - and it is simply skippable, with no
gate behind it. The failure is silent and survives to fab: you get a board that DRCs clean with no
plane where you thought you had one.

**Practical rules:**
1. After `board_init`, read the outline origin and translate EVERY rect in `constraints.json`
   (`planes[].region`, `placement` rects/keepouts) into absolute coordinates before `planes_gen`.
2. Record the translation in the file (`_coord_note` / `_planes_note` with the board-local
   equivalent) so the next reader cannot mistake the frame.
3. **After the P7 pour, re-run a geometric island check** - the FILL is the authority, not the
   planned rectangle. Verify each plane net forms the island count you intended.

## 2026-08-08 [layout][rf] A pour can bend: the "corridor width" between two keepout discs is the perpendicular gap, not the straight-strip intersection

Orchestrator error worth keeping. Given two circular keepouts, I computed the clear corridor as the
intersection over all x of their y-spans - the widest straight horizontal strip - and got 2.8 mm,
concluding the ground return was unroutable.

That is the wrong measure, because **copper pours are not required to be straight**. The real
constraint is the perpendicular gap `d - 2R` between the disc edges, projected onto the corridor:
`45.88 - 41.10 = 4.78 mm` perpendicular = **5.01 mm** measured as a vertical section. Scanning the
actual clearance along x: 80 mm at x=48, 45 at x=60, 9.5 at x=70, **5.0 at x=78** (the pinch),
14 at x=90, 44 at x=95.

The underlying concern was still valid (and the real cause was the coordinate bug above), but the
number was wrong by 1.8x. **Measure a routing corridor as the minimum perpendicular gap along the
path, not as the largest inscribed rectangle.**
