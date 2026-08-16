# power_tree.md - bb-buck rails, budgets, losses, thermal

P2 architect. Lifts `research/power.json` and reconciles it against the final
block choices (400 kHz part, 15 uH, 2 layers, 40 x 30 mm outline). Where a
number here differs from P1's, the reason is stated - nothing is averaged.

Design point: **Vin 18-30 V (24 V nom, 30 V HARD max operating, A1), Vout
5.0 V +/-3 % (4.85-5.15 V) over the FULL line and 0-2 A load with <= 50 mVpp
ripple (A3), synchronous integrated-FET buck, fsw 400 kHz, L 15 uH, 50 C max
ambient, natural convection, no enclosure.**

---

## 1. Rail tree

| Rail | Source | Topology | Current declared | Where the number comes from | Diss @30 V/2 A |
|---|---|---|---|---|---|
| `+VIN` | bench PSU 18-30 V | direct (J1 + Cin, no series element) | **1.1 A** | hot-loop **rms**, not the 0.62 A DC average (see s2) | 0.03 W |
| `/SW` | `+VIN` | switch node | **2.6 A** | `I_L,pk 2.35 A`; width floor only, nothing decouples it | in U1/L1 |
| `+5V` | `+VIN` via B1 | synchronous buck | **2.6 A** | 2.0 A stated load x 1.3 design ceiling; also covers the 2.01 A rms L1->Cout segment | 1.20 W total board |
| `GND` | - | B.Cu pour | **2.6 A** | output return = load current; input return is smaller (0.62 A) | 0.008 W |

There is **no on-board consumer to itemise and inventing one would be
dishonest**: requirements s3 states an external resistive bench load of
0-2 A at 5 V behind J2, and the mode excludes every other load. The rail
budget IS the stated 2 A plus the two currents the converter's own passives
carry (Cin 0.90 A rms, Cout 0.20 A rms).

Input current is a RESULT of the loss budget, not an input:
`I_in = (10 W + P_loss)/Vin` = **0.62 A at 18 V, 0.47 A at 24 V, 0.38 A at
30 V**.

## 2. The one number most likely to be mis-sized: +VIN at 1.1 A

The DC average input current is 0.62 A. **The copper from Cin to the U1 VIN
pin does not carry the average.** The high-side switch chops the input, so
that segment carries `sqrt(D) x I_L,rms`: `sqrt(0.278) x 2.010 = 1.06 A` at
18 V. Heating goes as rms^2, so sizing on 0.62 A under-sizes it by 1.7x.
**`+VIN` is therefore declared at 1.1 A and stays there.** IPC-2152 at
dT = 10 C on 1 oz outer copper gives 0.56 mm - but that is a FLOOR, not a
target: the same segment is the hot loop, so route it as short wide copper
(>= 1.5 mm), because loop inductance, not temperature rise, is what it is
being sized against.

`I_Cin,rms` peaks at **0.903 A at LOW line** (`sqrt(D(1-D))` grows toward
D = 0.5, never reached here), hence the >= 1.0 A rms requirement on the bank.

## 3. Loss budget at the worst corner (30 V, 2 A) - and why high line is worst

| Line | D | Board loss | Efficiency | of which U1 |
|---|---|---|---|---|
| 18 V | 0.278 | 1.11 W | 90.0 % | 0.76 W |
| 24 V | 0.208 | 1.16 W | 89.6 % | 0.80 W |
| **30 V** | **0.167** | **1.20 W** | **89.3 %** | **0.85 W** |

Split at 30 V / 2 A: **U1 0.854 W + L1 0.27 W (DCR 0.211 + core ~0.06) +
copper/terminals 0.071 W + cap ESR 0.003 W = 1.20 W.**

**The worst corner is HIGH line, which is the opposite of the usual case and
easy to get backwards.** Input current is only 0.38-0.62 A so input-side I^2R
is negligible; what grows with Vin is switching loss (~Vin) and the low-side
conduction time (`1-D` rises 0.72 -> 0.83).

Reconciliation with P1: power.json's headline is 1.289 W board / 0.924 W U1
at **500 kHz / 10 uH**. The lead part is a fixed **400 kHz** device, and
power.md s8b states the coupling explicitly: at 400 kHz L must be 15 uH
(10 uH would give 52 % ripple) and `P_U1` falls to 0.854 W. The inductor
gives most of that saving back (15 uH costs ~90 mW of DCR at constant package
size) - but it gives it back **in the part that has thermal headroom, not in
the part that does not**, so the trade is worth taking on top of the ripple
argument. Board total moves 1.29 -> 1.20 W; `P_U1` moves 0.92 -> 0.85 W.

Model limits carried from P1, unchanged: switching loss +/-30 %, core loss
+/-40 %, R_ba +/-30 %. These are limits on a TYPICAL 36 V-class part, not on
a part. P3 re-runs them against the real datasheet numbers.

## 4. Part-level requirements this budget imposes (P1, reconciled to 400 kHz)

- **`P_U1 <= 0.95 W` at 30 V / 2 A. This is the binding number and it does
  not move.** It is not a physics limit (the thermal ladder would allow
  ~1.1 W) - it is the P8 gate: `check_thermal` gives 73.8 C/W on 2 layers at
  a saturated pour, so `dt_c = 70` errors above `70/73.8 = 0.948 W`.
- The `Rds_LS` proxy MOVES with frequency. At 500 kHz it was <= 85 mOhm at
  25 C. At 400 kHz the switching and gate terms drop ~45 mW and ~15 mW, so
  the same 0.95 W ceiling maps to **`Rds_LS <= ~110 mOhm at 25 C`**
  (LS conduction = `I^2 x 1.4 Rds_LS x (1-D)` = 426 mW at 90 mOhm; the
  94 mW of headroom buys ~20 mOhm). Prefer <= 85 mOhm; treat 110 mOhm as the
  wall, and **verify against the real datasheet number, not this arithmetic.**
- `Rds_HS <= 200 mOhm`, `(tr+tf) x fsw <= 0.0075` (18.75 ns at 400 kHz),
  `Qg <= 5 nC`, `Iq <= 1 mA` switching, `t_on,min <= 250 ns` at 400 kHz
  (2.5x margin against the 417 ns available at 30 V; the lead part's 108 ns
  max clears by ~4x), **`Tj_max = 150 C`** (a 125 C part fails outright, see
  `stackup.md`).
- **Exposed pad required.** A non-pad SOT-23-6 or SOIC-8 is excluded outright
  at ~0.85 W.
- **Light load is the requirement most likely to be missed.** A3 binds
  <= 50 mVpp at NO load. Accept a forced-CCM part, a MODE/FCCM pin strappable
  to CCM, or a PFM part whose datasheet shows <= 50 mVpp at 5 V with a
  comparable Cout. A preload resistor is NOT available (mode excludes
  conditioning the datasheet does not require) - **the fix has to be
  selection.** Forced CCM at 0 A costs 0.15-0.25 W and ~8 C of board, which
  is affordable here. If no stocked 36 V-class candidate satisfies any of the
  three, that is an owner question, not a silent burst-mode part.

## 5. The +/-3 % DC budget - and why the divider tightens to 0.1 %

Contributors: FB reference over temperature (+/-1.0-1.5 %), divider
tolerance, load regulation (~0.5 %), line regulation (~0.2 %), ripple half
amplitude (~0.1 %).

| Divider | worst-case SUM | RSS | verdict |
|---|---|---|---|
| 1 % | ~3.7 % | ~2.2 % | fails the SUM - P1 rejected it |
| 0.5 % (P1 floor) | ~3.1 % | ~1.8 % | closes on RSS only |
| **0.1 % / 25 ppm** | **~2.5 %** | **~1.7 %** | **closes on the SUM** |

**Decision: specify 0.1 % / 25 ppm-per-C, same family, both resistors.** It
costs a few cents, changes nothing in the part COUNT, and turns a
statistical argument into a deterministic one on a board whose whole purpose
is to be a trustworthy study article. P1's 0.5 % is retained as the absolute
floor if 0.1 % is not stocked. TCR matters because the divider sits on an
85-90 C board; same-family tracking cancels most of it.

Two traps carried forward for P3/P4:
- **The FB trap.** Fixed-output family members tie FB straight to the output
  sense point. Do NOT copy the adjustable variant's divider out of a shared
  datasheet figure, and do not copy a fixed variant's FB wiring onto an
  adjustable part.
- **The COT trap.** If P3 lands a constant-on-time part with Type-3 ripple
  injection instead, `Vout = (1 + Rt/Rb)(VREF + Vramp_pkpk/2)` - the loop
  regulates the FB VALLEY, worth +3 % on an LM5017 and enough to blow 5.15 V
  on its own. That would change `control_kind` in `constraints.json` and
  re-open this budget. The lead part is peak-current-mode, so the trap does
  not apply as chosen.

Transient note, not a spec: disconnecting a 2 A resistive load overshoots
`sqrt(Vout^2 + L I^2/C) - Vout` ~ 130 mV for tens of microseconds. A3 is a
DC window; this is normal and is recorded so a bring-up scope shot is not
mistaken for a regulation failure.

## 6. Output ripple - a layout budget, not a capacitance budget

`dI/(8 fsw C) + dI x ESR` at 30 V with `dI = 0.694 A` and 26 uF effective:
**8.3 + 2.1 = 10.4 mVpp**. The fundamental is a fifth of A3's 50 mV. The
other ~37 mV is switch-node ringing coupled into the output and ESL spikes -
spent by hot-loop area, the Cout ground return, and the A4 probe pad's extra
SW copper. **Adding capacitance cannot buy back a bad loop.**

If P3's datasheet window forces 10 uH at 400 kHz instead of 15 uH:
`dI = 1.042 A`, ripple 15.6 mVpp, `I_L,pk 2.52 A` - still inside A3 and still
under the part's current limit, at the cost of ~40 mW more AC loss. It is the
acceptable fallback, not an equal choice.

## 7. Thermal - 40 x 30 mm on 2 layers

Worst case **1.20 W board / 0.85 W in U1 at 30 V, 2 A, 50 C ambient**,
natural convection, no enclosure, single-sided assembly (B.Cu clear of SMT =
a free second radiating face).

**The board IS the heatsink and it is near-isothermal even on 2 layers.**
Spreading length `sqrt(k t / 2h)` = 26 mm on 2 x 1 oz against a board
half-dimension of 15-20 mm, so the whole outline participates and the correct
model is whole-board, not a local patch.

| outline | area | R_ba | rise @1.20 W | surface | P1 ladder Tj (2L) |
|---|---|---|---|---|---|
| 35 x 25 | 875 mm^2 | 39 C/W | 47 C | 97 C | - |
| 38 x 28 | 1064 mm^2 | 34 C/W | 41 C | 91 C | 115 C @16 vias / 111 @25 |
| **40 x 30** | **1200 mm^2** | **31 C/W** | **37 C** | **87 C** | **107 C @25 vias** |

Junction ladder: `Tj = 50 + board rise + ~5 C local + P_U1 x (theta_JC,bot +
R_via)`. One 0.3 mm via with 25 um plating through 1.6 mm is **192 K/W**;
P1's array figures (which carry a spreading term this file does not
re-derive) are **14.1 K/W at 16 vias and 9.1 K/W at 25** - on 2 layers
**that array IS the heat path**, and 8 vias instead of 16 costs ~10 C of
junction. At 40 x 30 with 25 vias and `P_U1 = 0.85 W`, **Tj ~ 103 C** against
a design limit of 120 C (`Tj_max 150 - 30 C margin`). P1's ladder row for the
same geometry at 0.92 W is 107 C; the two agree.

Consequences, all binding:
- **All MLCCs X7R (125 C) minimum. X5R (85 C) is not acceptable anywhere** -
  the board surface is 85-90 C.
- L1 rated >= 125 C. No aluminium electrolytic fitted or needed.
- **L1 at 0.27 W gets NO `thermal` entry** - it is below the 0.5 W threshold
  in `buck-constraints-emission`. Recorded here with the number so the
  omission is visible rather than silent. It still wants >= 40 mm^2 of pad
  copper per terminal.
- `check_thermal` will NOT verify the via array (it warns only when
  `dt_c/power_w < 73.8` on 2 layers, and `70/0.92 = 76`). **A clean
  check_thermal is not proof the array exists** - the array is a P6/P7
  requirement enforced by review.
