# P2 Architecture digest - rf-de-20m (20 MHz Class E GaN stage, 200 W)

**AMENDED 2026-08-07 (P2-A)** after the orchestrator read the EPC2019 datasheet
(rev (c)2021) directly and retracted two P1 figures. This digest reflects the
amended package.

Artifacts: `architecture/blocks.md`, `power_tree.md`, `stackup.md`, `sheets.md`,
`constraints.json`, `decisions.md`.

---

## AMENDMENT P2-A - a retraction, plus two further errors found while re-deriving

**RETRACTED.** `research/power.json` supplied **Coss(er) 156 pF** and **Rds(on)
22 typ / 42 max mohm**. The datasheet publishes **no Coss(er), no Coss(tr) and no
Eoss anywhere** - the 156 pF was invented - and Rds(on) is **36 typ / 50 max mohm**.
The original ruling *"2 x Coss(er) = 312 pF lands on the required 317 pF, so the
external shunt cap disappears"* is void.

**ENDORSED.** The orchestrator's method is right: **`Coss(tr) = Qoss/V` (charge-
equivalent) is the correct basis for Class E**, because the drain waveform is
produced by integrating current into charge. `Coss(er)` is the *hard-switching
energy* equivalent (~119 pF here, 25% low) and the 110 pF small-signal figure is
quoted at 100 V where Coss has already fallen. Both would have under-sized the
shunt.

**ERROR 1 - wrong voltage range.** `18 nC/100 V = 180 pF` is the average over
0-100 V; this drain swings to **142.5 V** and Coss keeps falling. Two independent
extrapolations (power-law fit anchored on *both* published numbers, and a
flat-above-100 V bound) **agree to 1.5%: Coss(tr) = 158 pF typ / 205 pF max**.

**ERROR 2, the bigger one - wrong Sokal coefficient.** `0.1836/(omega.R)` is the
**Q_L -> infinity** constant; this board runs **Q_L = 5**, and
`refdesign-classE-stage.json` D9 already said so. Sokal's published fits reproduce
the fragment's power and shunt coefficients **to 0.008% and 0.13%**, confirming
both. **The frozen operating point itself was computed with Q_L -> infinity
constants on a Q_L = 5 design.**

| | Frozen | Orchestrator's fix | **P2-A** |
|---|---|---|---|
| Vdd | 40 V | 37.5 V | **40 V - frozen input preserved** |
| R_opt | 4.614 ohm | 4.06 ohm | **4.13 ohm** |
| C_shunt required | 317 pF | 360 pF | **403 pF** (+38-46 pF finite-choke term) |
| Coss(tr) per FET | (invented 156) | 180 pF | **158 typ / 205 max** |
| Pair supplies | 312 pF | 360 pF | **316 typ / 410 max** |
| External C0G trim | 5 pF | 0 pF | **87 pF, 0-133 pF of range** |

**The two errors pull opposite ways and the second dominates: the bus stays at
40 V, and the external trim capacitor comes back.** That last point is the most
valuable outcome - the original ruling treated its disappearance as elegance, but
it is a **defect**: Coss spread on this part is 110-150 pF (+36%), and the external
cap is the **only** absorber. At 100% device shunt a max-Coss part is unfixable
without reworking etched copper.

---

## The four rulings, as amended

1. **TWO EPC2019 - REINFORCED, and now absolute.** With the real Rds(on), a single
   FET reaches **Tj 160 C with a HYPOTHETICAL 0 C/W heatsink - above the 150 C
   absolute maximum.** There is no heatsink, TIM, via array or copper weight that
   saves a one-FET build (it was "138 C against a 125 C target" before). The pair:
   **114 C nominal / 133 C at the max-datasheet corner** at theta_HS 0.7 C/W.
   **The "k = 2 is exactly the ZVS ceiling" sub-argument is RETRACTED** (the real
   ceiling is 2.55) and replaced by a quantitative one:
   `P_FET(N) = 5.48/N + 2.42N + ...` gives **11.17 / 11.25 / 13.16 W at N = 1/2/3**.
   **Paralleling does not reduce dissipation at all - it halves thermal resistance.**
   N=3 pays +1.9 W and a three-way gate match that cannot be mirrored.
2. **C_shunt = 403 pF: 316 pF from the pair + ~87 pF external.** C203-C206 are four
   1206 C0G sites, **3 populated (99 pF), no longer DNP**, in the power loop.
3. **PCB spirals, re-derived: L_s 164 nH, L_m 110 nH.** The **losses barely moved**
   (1000/Q and 666/Q) because `P = 200.Q/Q_ind` is **independent of R** - the tank
   current rises exactly as fast as the reactance falls. The lower L is
   geometrically helpful: 164 nH at the same OD wants a *wider* trace, which is what
   Q and the thermal area want anyway.
4. **Two-zone floorplan - unchanged.** The power loop *ends* where the tank
   *begins*, so the two plane rules apply to disjoint regions.

## New findings at P2-A

- **The frozen tank was wrong for its own Q_L.** R 4.614 -> **4.13 ohm**;
  C_shunt 317 -> **403 pF**; L_s 184 -> **164 nH**; C_s 447 -> **518 pF +/-5%**;
  L_m 115 -> **110 nH**; C_m 500 -> **530 pF**; I_tank 6.58 -> **6.96 A rms**.
  Tank conductor widths grow ~12% (7.2 mm, was 6.4).
- **A third P1 coefficient is refuted and NOT adopted.** The fragment's
  `C_series.omega.R = 0.63467` implies a net series reactance of **3.4 R** - not a
  Class E network. Sokal's fit gives **0.26906 -> 518 pF and 1.283 R**, which also
  agrees within 3.5% with the independent `X_net = 1.1525 R` relation.
  **SIM-4 gained a measure (`x_net_series_over_r`) specifically to arbitrate it.**
- **Vdd is NOT a ZVS knob - but it IS a free thermal derating knob.** ZVS in Class E
  is a property of the *network*: the equations are linear in Vdd and the ZVS/ZdVS
  conditions constrain only the current waveform shape. So the bus can be backed
  down at bring-up without losing ZVS: **40 V/200 W/Tj 133 C -> 36 V/162 W/Tj 119 C**
  at the max corner, zero rework. This is the mitigation for the compounded worst
  case (170 C), and it corrects the orchestrator's framing - lowering the bus alone
  cannot fix a shunt-capacitance error.
- **The gate-loop budget TIGHTENED to 0.48 nH per FET** (was 0.84). The datasheet's
  Ciss 200 pF / Crss 0.7 pF give C_GS ~ 199 pF, not the ~350 pF the retracted Qg
  implied. **Now the tightest layout spec on the board**, with a stated fallback
  (R_G 3 ohm -> 0.84 nH, at +0.3 W turn-off loss).
- **The real Qg of 1.8 nC IMPROVED the +5 V rail**: 143 -> **99 mA**, 3.0x headroom,
  and gate-resistor dissipation 0.047 -> 0.029 W per part.
- **HS-1 tightened: theta_HS <= 0.7 C/W** (was 1.4). A passive bolt-on will not do it.
- **BOM +$4/board**: EPC2019 is **OUT OF STOCK at LCSC (stock 0), repriced
  $2.17 -> $3.93**. Owner approved continuing and **holding the order**; P10
  re-verifies. Delivered estimate **~$32-40/board (~$160-200 for 5)**.

## Unchanged

Stackup `JLC04161H-1080B` (chosen for its 0.2444 mm L1-L2 gap), 1 oz outer,
TG155 + ENIG + POFV, 100 x 80 mm with pre-authorised growth to 120 x 80, the
two-zone floorplan and plane regions, the relaxed controlled-Z output (D7),
DC-coupled unipolar drive (D8), no protection parts, three sheets and the
net-naming contract. **Vds,pk stays 142.5 V** - it depends only on Vdd.

## Pipeline traps - two carried, one retired

1. **`rules_gen` only solves impedance for DIFFERENTIAL pairs.** A single-ended
   `high_speed` entry with `impedance_ohm: 50` emits **no width rule at all**.
   `/tank/RFOUT` is declared under `power` instead - which is also the right physics
   (**OPEN-2**).
2. **`detect_diff_pairs` auto-pairs `high_speed` nets ending `_H`/`_L`**, hence
   `/stage/GATE_ON` / `_OFF`.
3. **`planes_gen` has no void or keepout support**; zone B is unpoured by
   construction and the spiral courtyards need hand-added rule areas at P6.
   **`board_init` does not origin the outline at (0,0)** - translate every rect by
   `outline_bbox` at P5.
4. **RETIRED:** "`rules_gen` puts every power net in ONE class at the widest width"
   is **fixed** in the current script (one class per required width).

## Riskiest decision

**Coss hysteresis is now the dominant FET loss term (4.83 W of 11.25 W) and rests
on an assumed 10% of stored energy that EPC does not publish** - the same class of
gap that produced the retracted Coss(er). At 15% the pair reaches ~13.7 W and Tj
~127 C. Mitigations are in the architecture at zero cost: the trim bank, the
bus-derating ladder, and a first bring-up step that settles it in an afternoon
(measure DC input power at 200 W out, thermal-image both dies).

## `constraints.json`

**Lint-clean: 0 errors, 0 warnings.** 4 high_speed, 6 power, explicit empty
diff_pairs, 5 voltages, 3 voltage_pairs, 7 thermal, 6 planes, placement
edges/groups/keepouts/separation/fixed. Every current, voltage and power figure
re-derived at R = 4.13 ohm.

## Sim gate - SEVEN benches (SIM-7 added at P2-A)

**SIM-1** `classe_zvs_nominal` (Vds@turn-on <= 5 V, dVds/dt +/-0.2 V/ns, Pout
190-210 W, Vds pk <= 155 V). **SIM-2** `cshunt_sweep` - **now validates the whole
amended basis**, with `coss_tr_per_fet_pf` bounded to **140-180 pF** from the vendor
nonlinear model plus a 300-430 pF sweep and `trim_pf_needed <= 133`; must pass
before P4 fixes any tank value. **SIM-3** `gate_symmetry` (Id imbalance <= 15% at
+/-0.15 nH, Vgs inside -4.0/+5.75 V). **SIM-4** `tank_match` (Zin 3.72-4.54 ohm,
H2 <= -20 dBc, H3 <= -33 dBc, **plus `x_net_series_over_r` in 1.0-1.6 to arbitrate
C_s**, and the spiral-to-spiral mutual k). **SIM-5** `loss_split` (pair <= 13.0 W
typ / <= 16.0 W max-corner - the numbers the 0.7 C/W heatsink was solved against).
**SIM-6** `gate_loop` (advisory). **SIM-7** `bus_derating` **(new)** - re-run SIM-1
at 40/38/36/34 V with the network unchanged, to confirm ZVS is Vdd-independent and
the derating ladder is real.
