# LEARNINGS - rf-de-20m (20 MHz Class DE GaN inverter, 200 W)

Workspace-local (deliberately NOT root LEARNINGS.md - concurrent runs in flight 2026-08-07).
Promote to root only after this board's run settles.

## PROMOTION QUEUE - skill-level, not board-level

Three P7 findings are properties of the TOOLCHAIN and of the skill's own remediation advice,
not of this board. They are tagged `[PROMOTE-TO-ROOT]` below and should be moved to the root
`LEARNINGS.md` verbatim (with their numbers) once the concurrent runs settle. Whoever promotes
them: they belong together, because 1 and 2 are cause and consequence and 3 is the trap you hit
while working around 1.

1. **Freerouting 2.2.4 wedges on a pre-routed wire whose WIDTH rivals its LENGTH** - bisected,
   with a JFR profile naming the method. Line 863.
2. **The worst offenders are exactly the pour fan-in land tracks that
   `reference/remediations/track_width.md` step 4 MANDATES** - so the skill's own advice arms
   the trap for the next phase. Line 863 (same entry), and restated in reports/route-notes.md s9.1.
3. **`ImportSpecctraSES` REPLACES the board's wiring, it does not add to it** - 209 -> 89
   tracks, 24 -> 44 unconnected, measured. Line 901.

Also promotion-worthy but lower value: `lib_pull --project` re-normalising every footprint in
the library (line 1006), and the `.kicad_pro` netclass wipe on schematic regeneration (already
recorded at line 815 and flagged there as a skill-level defect).

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

## 2026-08-08 [P7][kicad][zones] A `.kicad_dru` rule BEATS a zone's local clearance during fill - so a pour can never reach a fine-pitch HV die

Measured on this board, both directions, same run:

- A **GND** zone with `(connect_pads yes (clearance 0.35))` next to the EPC2019 filled to
  **0.8006 mm** from every `/SW` pad - i.e. KiCad used `aiee_hv_143v_SW` (0.8 mm), not the
  zone's own 0.35 mm. The consequence is not cosmetic: the fill stops **0.20 mm short of the
  source bumps and 0.66 mm short of pin4**, so *no pour of any clearance setting can connect
  the die*.
- The same is true for a **/SW** zone: three fan-in lobes authored at clearance 0.35 over the
  drain bars filled **0.0 / 0.85 / 2.08 mm2** - all of it pushed 0.8 mm away.

**Practical rule: `SetLocalClearance` only ever LOOSENS a zone against nets that no custom rule
names.** If a per-net `.kicad_dru` clearance rule exists, the zone obeys the rule. To attach a
pad the rule holds a pour away from, you need a TRACK or a VIA - the filler is not negotiable.

Corollary for this board: the EPC2019's 7 bumps are on a 0.6 mm pitch with 0.35 mm drain-to-
source gaps, so the whole die fan-in (4 source escapes + 2 drain escapes + 1 rung per FET) is
0.25 mm hand track. GND carries no per-net width rule so those cost no `track_width` findings;
`/SW` does, so the two drain escapes and their rung are `track_width` findings by construction.

## 2026-08-08 [P7][kicad][swig] A via added into an ALREADY-FILLED zone takes the ZONE's net, not the op's

`route_edit`/`stitch_vias` set the net explicitly (`v.SetNet(...)`) and the worker reports
`added`, but the saved board carries a different net and the post-apply verify then fails with
`via at (x, y) (+40V) not in saved board`. Grepping the board shows the via present with
`(net "GND")`.

Cause: KiCad re-derives a via's net from connectivity, and a board whose zones are already
filled has **no antipad yet** at the new hole - so the via is electrically inside the GND plane
at the moment it is added. Verified by placing the identical via on the bare board (net kept)
and on the poured board (net stolen), same coordinates.

This never bit the pipeline before because it only ever stitches GND (or a power net whose
plane is that net) - the "stolen" net is the one it wanted. It bites the moment a **power net
needs a bridge on a layer the plane owns**.

**Build order that works:** place power-net vias on the BARE board -> pour GND -> stitch GND ->
pour the power nets last. `route_edit` is atomic, so a mixed batch rolls back entirely; the
retry driver in `route/apply_ops.py` parses the verify message and drops the rejects (note
`route_edit` truncates that list to 10 per attempt, so it needs several passes).

## 2026-08-08 [P7][routing][placement] U201's OUTH/OUTL fan-out is NOT planar - OUTL has to wrap around OUTH

`sheets.md`/P6 put OUTH (A2) and OUTL (B2) side by side on U201's output row with **OUTL to the
WEST**, and gave OUTL the **outer** resistor pair (R205/R206 at +/-3.5 mm) and OUTH the **inner**
pair (R203/R204 at +/-1.2 mm). Both outputs can only escape SOUTH (the other three sides are
U201's own balls at 0.2 mm gaps).

That ordering has no planar solution: OUTH's fan-out is a "Y" whose apex is A2, and OUTL - whose
targets straddle it - would have to pass between B2 and A2 (a 0.2 mm gap) to get around it.
Swapping which pair is inner does not help; it mirrors the same conflict.

What was built: **OUTL wraps west around U201** to a split point back ON the mirror axis at
(23.15, 24.775), so its two legs stay exact mirrors of each other. Cost: the OUTL feed is
~3.2 mm of 0.30-0.55 mm track before the split, i.e. the turn-OFF loop is ~2x the turn-ON loop's
length. OUTH is a single 1.30 mm bar down the axis that lands on R203.1 and R204.1
simultaneously - its two legs are literally the same copper, so they are identical by
construction.

**If this board is ever re-placed: give U201 its own y-offset from the resistor column, or put
the OUTL resistors on the far side, so both fan-outs nest without a wrap.**

## 2026-08-08 [P7][routing][krt][freerouting] Never hand KRT a PLANE-CARRIED net - GND alone blew a 1800 s budget

Freerouting 2.2.4 **wedges reading this design** (rung 1 log stops after the
version banner; no pass lines, no SES, no completion) - the documented failure
mode on a board that already carries router-generated copper, and this one is
almost entirely pours + hand tracks. So the whole remainder falls to the KRT
mop-up, and two things had to be fixed before it would do anything:

1. **`route_auto`'s KRT pass inherits `grading_floors`, which takes the
   LOOSEST netclass clearance as KRT's base.** The HV power classes had been
   raised to 0.8 mm in the `.kicad_pro` so Freerouting would honour them in
   the DSN; KRT then tried to route the buck's 0.4 mm-pitch signals at 0.8 mm
   and produced nothing, which `route_auto` correctly reported as "not
   strictly better". **Keep HV clearance OUT of the netclass and pass it in
   `--net-clearances`** (which `route_critical.build_net_clearances` builds
   from the `.kicad_pro` AND the `.kicad_dru`) - the LEARNINGS 1522 rule, now
   confirmed from the other side.
2. **`route_auto` derives KRT's net list from the DRC's unconnected items,
   which includes GND** whenever a single GND pad is open. GND here has
   hundreds of pads on four layers, and KRT spent the full 1800 s on it
   without emitting a board. Excluding GND (it is plane-carried; the one open
   pad was a 0.2 mm WCSP ball that a single via closes) is what makes the pass
   finish.

Generalisation: the mop-up router's net list must be **the nets that are
actually meant to be tracks**. A plane-carried net that shows up unconnected
means "this pad needs a via", not "route this net".

## 2026-08-08 [P7][pipeline][rules_gen] Re-generating the schematic WIPES rules_gen's netclasses out of the .kicad_pro

Found at P7 start: `kicad/rf-de-20m.kicad_pro` had **no `net_settings` at all**
and an empty `board.design_settings.rules`, even though `log/P5-rules_gen.json`
reports it wrote three power netclasses (`Pwr_5p5mm`, `Pwr_8p4123mm`,
`Pwr_11p8942mm`) and the fab floors.

Cause: `schlib.write_project()` writes a **whole minimal `.kicad_pro` from
scratch** (deliberately - "keep it MINIMAL; unexpected keys can make KiCad
reject the whole file"), and `Sheet.save(..., project=True)` calls it. So any
schematic regeneration after P5 - here the P4-FIX review pass - silently
deletes rules_gen's work. `rules_gen` is a P5 step and nothing re-runs it.

Consequences if it is not caught: the DSN handed to Freerouting carries no
per-net widths or clearances at all, and `route_critical.grading_floors`
(which reads the pro) falls back to KiCad stock defaults, so the mop-up
router grades against the wrong floors too.

**Check `net_settings` in the `.kicad_pro` at the start of P7**, and re-run
`rules_gen.py --constraints ... --out-dru ... --pro ...` if it is missing.
Re-running is safe: the `.kicad_dru` it regenerates was byte-identical here.

## 2026-08-08 [P7][BLOCKER][krt] KRT `route.py` does not scale to a 120 x 80 mm board - it cannot finish ONE net

Not a wedge, not a bad input: it simply never returns. Measured on rf-de-20m,
every configuration, each on a fresh stage with the correct floors and an
explicit `--net-clearances` map:

| grid | scope | budget | result |
|---|---|---|---|
| 0.05 | 11 nets incl. GND | 1800 s | no board emitted |
| 0.05 | 10 signal nets | 3000 s | no board emitted |
| 0.1 | per net | 300 s | `+5V` alone did not finish |
| 0.1 | per net, **zone-free board** | 240 s | `+5V` alone did not finish |
| 0.2 | per net, zone-free board | 240 s | `+5V` alone did not finish |

The zone-free run is the one that settles it: with NO pours on the board at
all (placement + a handful of hand tracks), a single 5-connection 0.2 mm
signal net still does not complete. So it is not the pours, not the HV
clearance map, and not the net count - it is the search space. 120 x 80 mm at
grid 0.05 is 2400 x 1600 x 4 nodes; every prior board in this pipeline ran KRT
as a mop-up for a few short nets on a smaller outline.

**Consequence: on a board this size, `route_auto` has no working fallback** -
Freerouting wedges on pre-existing copper and KRT cannot finish. Plan for
hand-routing the signal remainder, or route BEFORE any copper exists (FR's
wedge is triggered by existing router copper, not by the placement).

## 2026-08-08 [P7][freerouting][BLOCKER-RESOLVED][PROMOTE-TO-ROOT] Freerouting's DSN reader wedges on a pre-routed WIRE whose WIDTH rivals its LENGTH - not on big pads, keepouts or vias

Supersedes the earlier "FR wedges on a board that already carries router-generated copper"
entry, which named the symptom and guessed the cause. Bisected on this board with
`route/fr_spiral_probe.py` and `route/fr_wire_bisect.py`. A healthy run prints
`Job '...' started` ~1.5 s in and finishes in ~10 s, so a MISSING `started` line is the wedge
signature and a 90 s budget is enough to classify a variant.

| DSN variant | result |
|---|---|
| as exported | wedges |
| both spiral winding padstacks (1116/828 pts, exported as 55-pt concave hulls) -> plain rects | **still wedges** |
| + the four r=20.3/20.55 mm polygon keepouts dropped | **still wedges** |
| `(wiring)` emptied (34 wires + 160 vias) | **runs**, 4 passes |
| wires kept, all 160 vias dropped | **wedges** |
| vias kept, all 34 wires dropped | **runs**, 5 passes |
| only the 4 land tracks > 2 mm wide dropped | **wedges** |
| the 9 highest width/length wires dropped (aspect >= 0.81) | **runs** |

A JFR profile of a wedged run (`-XX:StartFlightRecording`, then `jfr print --events
jdk.ExecutionSample`) puts every hot sample under `app.freerouting.io.specctra.parser.
Wiring.read_scope` -> `ShapeSearchTree.insert` -> `Simplex.intersects` /
`Simplex.remove_redundant_lines` (which is O(n^2) in half-planes), with 279 GCs in 70 s. It
never reaches pass 1. The trigger is the convex decomposition of a wire whose rectangle is
nearly degenerate - here **7.651 mm wide x 0.020 mm long (aspect 382)**, plus an
8.412 x 0.700, an 11.894 x 1.200, an 8.412 x 1.200 and five gate bars at aspect 0.81-1.44.

**This is a PIPELINE-LEVEL trap, not a board quirk.** `remediations/track_width.md` step 4
mandates pour fan-in - a short, full-width land track into a pour - whenever a net's DRU
width floor exceeds what its pad can take. That remedy PRODUCES wires of exactly this shape.
So does a wide gate bar landing on two resistors at once. Any board that follows the
remediation will wedge Freerouting on its next pass, and the failure looks like a hang with
no diagnostic at all.

**Working recipe** (`route/fr_signals.py`): export the DSN, delete every wire with
width/length >= 0.8 FROM THE DSN ONLY (the copper stays on the real board), run Freerouting,
then FILTER the SES to the nets that actually needed routing.

## 2026-08-08 [P7][kicad][swig][PROMOTE-TO-ROOT] ImportSpecctraSES REPLACES the board's wiring - it does not add to it

Measured, and it silently deleted this board: `tracks_before 209, tracks_after 89`, and
unconnected went **24 -> 44**. `lib/route_swig.py`'s docstring says "adds copper only;
footprints/zones untouched" - the second half is true, the first is not.

`route_auto` gets away with `import_ses` only because the DSN it feeds Freerouting carries
every pre-existing track as a guide wire, so the SES echoes them all back and the round trip
is lossless (hence its `ses_echo_dups_removed` dedup step). The moment you hand Freerouting a
THINNED DSN, or filter the SES down to a subset of nets, the import becomes destructive.

**Fix: convert the session to `route_edit` ops instead** (`route/ses_to_ops.py`). route_edit
is additive, atomic and post-verified. SES geometry: `(resolution um 10)` -> 1 unit = 0.1 um,
and y is Specctra-up, so `board_y_mm = -y/10000`.

## 2026-08-08 [P7][freerouting][clearance] Per-net DRU clearances never reach Freerouting - and pushing them into the netclasses re-wedges it

KiCad writes the DSN's clearance rules from the `.kicad_pro` NETCLASSES only. This board's
HV rules (`aiee_hv_51v_40V` 0.5 mm, `aiee_hv_143v_SW` 0.8 mm, ...) live in the `.kicad_dru`,
so Freerouting routed at the netclass 0.2 mm and produced `/hk/BST` 0.26 mm from a +40V pad
and `+5V_DRV` 0.62 mm from a /SW pad.

The obvious fix - raise the three `Pwr_*` classes to 0.5/0.8/0.8 in the STAGED `.kicad_pro`
before export - **re-wedges the DSN reader** (no `Job started` line in 600 s), the same
failure mode as the degenerate wires. So there is no way to give Freerouting this board's
real clearances. Route with the netclass values and fix the HV-adjacent legs afterwards with
`route_edit`; that was 2 legs out of 15 nets here.

Related and still true from the other side: KRT must NOT get the HV clearance in its
netclass either (it then tries to route 0.4 mm-pitch buck signals at 0.8 mm and produces
nothing). Pass it in `--net-clearances`.

## 2026-08-08 [P7][routing][placement] The OUTL wrap around U201 is a WALL - it makes DRIVE and +5V_DRV unroutable on F.Cu

The consequence of the earlier "U201's OUTH/OUTL fan-out is NOT planar" entry, and the reason
BOTH autorouters left `/stage/DRIVE` and `+5V_DRV` open. The wrap is a 0.55 mm **U**:
vertical at x 28.91..29.46 spanning y 61.485..66.735, horizontals at y 61.485..62.035 and
66.185..66.735 running east to x 33.11. It ENCLOSES U201's ball array, C202 and the inner
gate resistors, and there is no gate in it:

- the only open side is east of x = 33.11 - the gate-resistor column - and the 1.30 mm
  `GATE_ON` bar (y 63.46..64.76) plugs the R203/R204 gap;
- the corridor between the wrap's bottom edge and C202's pads is **0.138 mm**.

`U201.C1` and the `C201.1 -> C202.1` link both have to cross it. Built as two short **In2**
hops under the wrap (In2, not In1: In1 at 0.2444 mm is the gate loops' and the drive input's
return image and must stay whole; In2 is the third GND layer). Cost: 4 through vias inside
the bottom-heatsink land, which HS-2 allows only while they stay TENTED on B.Cu.

**Generalisation: a "wrap" routed to preserve a mirror match can enclose the very pins it is
wrapping.** Check reachability of every enclosed pad BEFORE committing a wrap, not after.

## 2026-08-08 [P7][drc][gotcha] A track can SWALLOW an existing via and steal its net; and check hole-to-hole against vias you did not place

Two traps hit within minutes of each other while hand-routing, both found by DRC and neither
visible by inspection:

- a `/hk/BUCK_SW` track centred at x = 52.086 ran within 0.182 mm of a GND stitch via at
  (51.904, 93.17) - inside the via's 0.225 mm radius - so KiCad re-derived the via's net as
  BUCK_SW and reported `via_dangling`, not a short. The GND island it was stitching went
  quietly open.
- a new signal via at (29.85, 63.60) landed 0.584 mm centre-to-centre from a GND via at
  (30.085, 64.135): `hole_to_hole` needs 0.4995 mm plus both radii = 0.6995 mm.

This board carries 185 vias, most of them auto-placed GND stitching, so **scan
`bg.vias_of()` over the corridor before choosing a lane** - pads and tracks are not enough.

## 2026-08-08 [P7][zones][gotcha] A 0.2 mm signal track routed past a WCSP ball can starve the ball's only pour access

`U201.B1` is a 0.2 mm GND ball whose ONLY pour access is the band north of U201's ball row
(south is B2 at 0.4 mm pitch, leaving a 0.098 mm sliver; west is C1 at 0.2 mm). Freerouting's
`A1 -> C202.1` link dived diagonally through that band and squeezed it to **0.25 mm**, below
the zone's minimum width, so it stopped filling and B1 read `unconnected_items` against
`Zone [GND]`. Nothing else changed and no clearance rule fired.

Re-routing the same link along a constant y = 62.75 restored a 0.76 mm band and B1
reconnected. **Neither a via nor a jumper could rescue it**: a via needs 0.45 mm + 2 x 0.1016
and the pocket is 0.775 mm wide but already holds a GND via; a diagonal jumper across the
2x2 ball square clears the neighbouring balls only at <= 0.034 mm width.

Rule: when a fine-pitch BGA/WCSP pad is fed by POUR rather than by track, treat the feeding
band as a routing keepout of at least the zone's minimum width plus clearance.

## 2026-08-08 [P7][footprint][drc] Netless PTH thermal vias inside an exposed pad: give them the EP's PAD NUMBER, not a mask change

The easyeda2kicad `SOIC-8 ... EP2.0` pull for the LM5017 shipped four `(pad "" thru_hole ...)`
inside pad 9. Their `*.Paste`/`*.Mask` layers had ALREADY been removed at P3 (tented both
faces, mandatory here because the bottom copper is the heatsink mounting face) and KiCad
STILL raised 4 `solder_mask_bridge` ("Front solder mask aperture bridges items with different
nets") plus 4 `clearance` errors at 0.25 mm against pad 9. Tenting the hole does not help: the
hole sits inside pad 9's mask aperture and carries no net, so the aperture bridges pad-9
copper to no-net copper.

**Renumbering them from `""` to `9` clears all eight at once** - same-net items neither bridge
nor violate clearance - and it is also what an EP thermal via IS. Verified on a scratch copy
of the board first (93 -> 85 violations) before touching the library.

Propagating a footprint change under a LOCKED part: rename the footprint, point the generator
at the new name, rebuild the netlist, and let `board_update` classify it as `swap_new_fp`
(rip and re-place at the recorded pos/deg/side, pads re-netted from the netlist). Two things
the swap does NOT preserve and that must be redone afterwards: **the lock** (re-assert with
`place_edit --ops` `lock`) and **any moved Reference/Value field**, which reverts to the
library default position - here straight on top of C106, producing 3 `silk_overlap` + 1
`silk_over_copper` until it was moved back with `place_edit` `move_text`.

## 2026-08-08 [P7][pipeline][lib_pull][PROMOTE-TO-ROOT] lib_pull --project re-normalises EVERY footprint in the library, not just the one you asked for

`lib_pull.py --lcsc C2479122 --project ...` pulled the one 10R resistor as asked, and then its
`--refdes-norm` pass silently rewrote the Reference-text position of BOTH spiral footprints
(`SPIRAL_L110N`, `SPIRAL_L164N`) from `(at 0 -18.1)` to `(at 0 -4.825)` - i.e. from outside the
33 mm winding to on top of it. The board's placed copies are unaffected (they carry their own
geometry), so nothing DRCs differently, but a later re-import would have moved silk onto
copper.

`git status` on `lib/` after any `lib_pull` and revert what you did not intend. Use
`--no-refdes-norm` when adding a single part to a library that already contains hand-built
footprints.

## 2026-08-08 [P7][gan][gate][thermal] Damping a gate loop with R_G is NOT free in Class E - cost it in Tj BEFORE choosing the value

P7 was instructed to fit 10R on the OUTL legs to close the gate-loop budget, measured what it
cost, and the instruction was overruled on the numbers. Worth keeping because the reflex
"the loop is too big, raise R_G" is exactly right in a hard-switched converter and wrong here.

Class E turn-off is CAPACITIVELY SNUBBED - the shunt capacitor takes the switch current while
the channel opens - so `E_off = I_off^2 . t_f^2 / (24 . C_shunt)` and t_f is proportional to
the gate-loop R. **Turn-off loss therefore scales as R_loop^2**, i.e. quadratically in the very
knob you are reaching for. At L = 7.03 nH, C_GS = 199 pF, R_crit = 2.sqrt(L/C_GS) = 11.89 ohm:

| R_ext | R_loop | zeta | overshoot | VGS min | pair P_off | Tj max-datasheet corner |
|---|---|---|---|---|---|---|
| 4R7 | 5.85 | 0.49 | 16.9 % | -0.85 V | ~1.0 W | ~138 C |
| **6R8** | **7.95** | **0.67** | **5.9 %** | **-0.30 V** | **~1.85 W** | **~142 C** |
| 10R | 11.15 | 0.94 | 0.02 % | ~0 V | ~3.6 W | **~151 C** |

150 C is the EPC2019 absolute maximum. So the "clean edge" costs the whole remaining thermal
margin on the part whose thermal path was already this board's hardest problem - to suppress a
ring that was never a destruct risk: **-0.85 V against a -4 V floor is 4.7x of margin**, and
the first positive recovery of that ring is only +0.14 V, far below the ~1.4 V threshold, so
spurious re-turn-on is not in play either.

TWO THINGS THAT ARE EASY TO GET WRONG HERE, BOTH CHECKED:

- **The turn-OFF resistor does nothing for the +6 V rail.** OUTL damps the NEGATIVE edge. The
  positive rail is set by the OUTH loop, which is 2.05 nH at 4R7 -> zeta 0.91, 0.1 % overshoot,
  VGS peaking at ~5.005 V against +6 V. Do not justify a bigger OUTL resistor with +6 V
  headroom; they are different loops.
- **Overshoot collapses far faster than zeta rises.** `exp(-pi.zeta/sqrt(1-zeta^2))` takes
  16.9 % -> 5.9 % -> 0.02 % for zeta 0.49 -> 0.67 -> 0.94, so most of the ring reduction is
  bought by the FIRST step and the rest is paid for at quadratic cost. Take the knee.

WHAT DID justify moving off 4R7 at all - and it is NOT the ring number: margin against what the
second-order model does not contain. (a) The 7.03 nH is a microstrip estimate, not a
measurement; at 10 nH the 4R7 ring would be 24 %. (b) **Common-source inductance**: the 0.768 nH
die escape is shared between the gate loop and a 16 A power loop with ~2 ns transitions
(~8 A/ns), so `L_common.di/dt` injects volts straight into the gate loop, a larger series R
attenuates it, and NO ring model contains it. That is a P8 SIM item the architecture never
raised.

**Sourcing footnote that nearly forced the value:** LCSC has exactly ONE 6R8 0805 at 1 % and
>= 250 mW in stock (ROHM ESR10EZPF6R80, C5639707, 400 mW anti-surge, stock 360). Every other
1 % 6R8 reads stock 0 behind a 451-3317 piece MOQ, and the Stackpole RNCP thin-film family that
supplied the 10R candidate has no 6R8 at all. **Check availability at the value you are about
to choose, not after** - the E24 gap between 4R7 and 10R is thinly stocked in the 250 mW class,
and a 125 mW 0805 does not qualify either (it derates to ~96 mW at a 90 C local board, against
0.107 W of actual dissipation).

## 2026-08-08 [P8][check_current][pipeline] `pour_neck` tests ONE zone at a time and only where vias land - so it can miss the bus entirely and flag a dead-end stub instead

The worst finding of the P8 verify pass, and the check pointed the fixer at the wrong copper.

`check_current.pour_neck` erodes **`z.fill_on(layer)` - a single zone's own fill** - and only
runs at all when that fill contains **>= 2 vias of the net** (`len(pts) < 2 -> return None`).
Both halves bite on any real power bus:

1. **Per-zone, not per-net.** `planes_gen` decomposes a bus into abutting rectangles. Each is
   eroded on its own, so a 4.7 mm column abutting a 3.2 mm strip abutting a 24 mm block reports
   whichever rectangle happens to hold vias, at ITS width - not the width of the conductor.
2. **Only where vias land.** On rf-de-20m the true bottleneck was the x 46..51 / y 34..56
   corridor, pinched to **2.295 mm** by R104 and to 2.25 mm by a `/hk/BUCK_SW` horizontal.
   Those zones hold no vias, so `check_current` said nothing about them. What it DID flag was a
   3.16 mm neck in the y 31..34.2 strip - which was carrying **zero current**, because a single
   0.200 mm `+5V` track crossed it diagonally and cut the fill in two. The finding was real
   arithmetic about copper that did not conduct.
3. **No parallel-path awareness.** `undersized_track` carries a `bridge` (cut-edge) label;
   `pour_neckdown` carries nothing equivalent, so a neck in one of two parallel branches reads
   the same as a neck in a sole path.

**What to do instead when a pour_neckdown fires on a bus that matters:** solve the copper.
`route/bus_solve.py` + `route/bus_cuts.py` in this workspace rasterise the net's copper on both
outer layers at 0.25 mm, tie the layers at the net's vias, inject the rail current at its source
pad and draw it at its sink pad, and report bus resistance, the current in each branch, and the
section-average A/mm with its IPC-2152-equivalent width. It is ~60 lines of scipy on top of
`lib/geom` and it runs in 8 s on a 120 x 80 mm board. It found a 10.4 mOhm / 369 mW bus with a
60-76 C hot spot that the gate had scored as one 3.16 mm neck in a stub, and it proved the fix:
5.5 mOhm, 196 mW, every section at 1.19-1.32 A/mm against the 1.273 A/mm that IS 5.500 mm at
7.0 A. **This is skill-level, not board-level** - promote with the numbers.

**Corollary, and it is the cheapest lesson here:** a single 0.2 mm signal track laid across a
poured power bus severs it, silently. Nothing in the pipeline reports it - the net stays
"connected" through the long way round, DRC is clean, `plane_repair` passes (each fill is
electrically whole), and the island count does not change because the bus reconnects elsewhere.
**After any signal-routing pass, re-check that each power pour's fill is still ONE piece between
its source and its load** (`zones_of(net)` -> per-zone fill part count is the cheap version).

## 2026-08-08 [P8][kicad][swig] The "via takes the zone's net" trap is NON-DETERMINISTIC when the outer layers already carry the via's own net

Extends the P7 entry above. There the case was clean - a `+40V` via into a board where GND owned
every plane - and it failed every time. At P8 the new bridge vias landed where **F.Cu and B.Cu
were both already `+40V` fill** and only In1/In2 were GND, i.e. 3 of 4 layers agreed with the op.
It still failed, and it failed *differently each time*:

| batch | vias | lost |
|---|---|---|
| 8 vias at local x 50.1..43.8, y 31.3 | 8 | 1 (the x 50.1 one, whose centre sat 0.005 mm OUTSIDE the +40V fill) |
| the same 8 shifted one pitch west (49.2..42.9) | 8 | **4**, three of them at x-positions that had just SUCCEEDED |

So "is the via inside the target fill?" is necessary but not sufficient, and a passing attempt
does not predict the next one. `route_edit` is atomic and post-verifies every add, so both
attempts rolled back with the board byte-identical - the trap costs a retry, never a board.

**Only reliable procedure, and it is cheap:** strip every `(filled_polygon ...)` block from the
`.kicad_pcb` (paren-matched delete; the outlines in `(polygon ...)` stay), apply the ops on the
bare board, then `kicad-cli pcb drc --refill-zones --save-board`. That is the P7 build order
(`route/rebuild.sh` step 1) reached from the other direction: **you do not need the whole board
bare, you need the FILLS gone.**

Second-order, worth knowing before choosing via positions: a via whose CENTRE is 0.005 mm outside
the pour still reads as "connected" by eye and in DRC (its pad merges with the fill), but KiCad's
net derivation does not use the pad - it uses the centre. Check `net_copper(net, layer).contains(
Point(via.at))`, not `.intersects(via_pad)`.

## 2026-08-08 [P8][check_thermal][check_silk] Two P8 checks whose WINDOW, not whose model, produces the finding

Both cost a fixer a wrong conclusion if the source is not read.

- **`check_thermal` counts thermal vias inside `max(2.0, sqrt(pad_hull_area/pi) + 1.5)` of the
  footprint CENTROID.** For an EPC2019 the pad convex hull is 1.84 mm2, so the window is
  **2.27 mm** - smaller than the via array it is asking for. It reported "found 3 via(s), want
  >= 10"; the board actually carries **9 within 4.0 mm of each FET centroid**. Measure the array
  yourself before believing the count. (Its theta_JA model is separately heatsink-blind by
  design - `theta_floor + (theta_0-theta_floor).exp(-A/tau)`, copper area is the only input, no
  heatsink/TIM/airflow term exists in the module. Its own docstring says "a screen, not a
  sign-off ... +/-30 %".)
- **`check_silk`'s attribution rule is a two-sided constraint** (> 1.0 mm from its own pads AND
  < 1.0 mm from another part's) and on a dense cluster it can be **unsatisfiable**. A grid search
  over every position within 4 mm of each part found **zero** legal positions for R203 here, 3
  for C202 and 6 for R204 - so "scripted fix: place_edit.py move_text" is not always available,
  and moving the five that CAN move would leave the sixth flagged while risking new
  `silk_over_copper` on a board whose DRC residual is signed off. Run the feasibility search
  before promising the fix.

## 2026-08-08 [P8][check_return_path] `k x trace_width` makes a POUR FAN-IN LAND look like a 71 mm-wide return-path defect

`check_return_path` buffers a net's centreline by `k x width` (k = 3 by default). That is the
right model for a trace whose length greatly exceeds its width. It is the wrong model for the
short, full-width land track that `remediations/track_width.md` step 4 MANDATES to fan a pour
into a pad - the same construct that wedges Freerouting (entry above).

Here /SW's L301 terminal land is **11.894 mm wide and 1.200 mm long**, so its corridor is
1.2 x 71.4 mm: **27 % of the reported 81.29 mm2 deficit is off the board entirely** (the corridor
runs 18 mm past the north edge), and the rest is the deliberately plane-free magnetics zone.
Meanwhile the check never looks at the /SW **pour** at all - `corridor_on` reads `tracks_of()`
only - which is where the switching loop actually lives and which measured **96.13 % imaged on
In1**, with C203-C206 and L202.1 at 100 %.

**Practical rule: before treating a `corridor_void` as a defect, check the aspect ratio of the
track that produced it.** If width >= length, the corridor is a modelling artefact; measure the
real thing instead - `net_copper(sig, layer).difference(net_copper(ref, ref_layer))` over the
POUR, and the partial-inductance increment of the unimaged section
(`mu0.h.l/w` with an image vs `(mu0.l/2pi)[ln(2l/(w+t)) + 0.5 + 0.2235(w+t)/l]` without). Here
that was 0.031 nH vs 0.268 nH, i.e. **+0.24 nH on a 164 nH inductor - 0.15 %**.
