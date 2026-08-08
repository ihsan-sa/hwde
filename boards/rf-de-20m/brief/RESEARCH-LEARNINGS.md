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
