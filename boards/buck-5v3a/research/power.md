# Power architecture - buck-5v3a

P1 research fragment, `research-power-architect`. Source of record:
`requirements.md` (section 10 "Answers" is binding). Machine twin:
`research/power.json`.

This board **is** the power stage. The rail tree is one line long; the
engineering is the energy and thermal budget, which is what this document is.
No part numbers here - component classes only (part-sourcer owns parts).

## 0. Headline

1. **4 layers are required**, and the deciding number is junction temperature at
   the **7 V low-line corner** (not 12 V, not 18 V - high duty parks the loss in
   the high-side FET). Recommended part class: T_j ~ 91 C on 4L, ~109 C on 2L.
   Mainstream 3 A-class part: ~121 C on 4L, ~152 C on 2L (over the 150 C
   absolute max). Only 4L + low-RDS(on) leaves margin.
2. **The regulator's RDS(on) is a thermal decision, not a cost decision.**
   `RDS(on)_HS + RDS(on)_LS <= 90 mohm typ @25 C` is the selection filter; it is
   worth ~0.55 W and ~30 C of junction temperature against the 95/66 mohm parts.
3. **Efficiency 92.6 / 93.6 / 93.6 %** at 7 / 12 / 18 V in, 3 A out. Board loss
   **1.20 / 1.03 / 1.03 W**. Input power 16.0-16.2 W, input current **2.31 A**
   worst case.
4. **Input-cap RMS ripple peaks at 1.51 A at Vin = 10 V - inside the window**,
   not at either end (I_rms maximises at D = 0.5). Ceramics must be **X7R**: the
   board's own hotspot is ~90 C and X5R stops at 85 C.
5. **Output ripple is a non-problem** (~10 mV modelled vs a 50 mV budget). The
   real output-cap question is the load transient of an unknown external load.
6. **The 4 A fuse (A5) is thermally marginal**: SMD fuses derate ~30 % at
   85-95 C, giving ~2.8 A effective against 2.31 A operating. 5 A time-lag
   recommended - see OPEN 2.

## 1. Rail tree

```mermaid
graph LR
    SRC["Bench PSU / AC-DC adapter<br/>7-18 V DC, 12 V nom (A1)"]
    SRC -->|"2.31 A worst case (7 V)"| J1["J1 screw terminal<br/>5.08 mm, 2-pin"]
    J1 --> F1["F1 fuse<br/>4-5 A time-lag<br/>0.118 W"]
    F1 --> Q1["Q1 reverse-polarity P-FET<br/><= 15 mohm @ Vgs -4.5 V<br/>0.080 W"]
    Q1 --> VIN["+VIN protected rail<br/>TVS 20-24 V + Cin 2x10uF/50V X7R<br/>+ 100 nF at the VIN pin"]
    VIN --> U1["U1 synchronous buck<br/>40 V, >=4 A, 500 kHz<br/>0.60-0.63 W"]
    U1 -->|"/SW"| L1["L1 6.8 uH<br/>Isat >= 6 A, DCR <= 25 mohm<br/>0.24-0.28 W"]
    L1 --> V5["+5V rail<br/>5.00 V +/-3 %, 3.0 A<br/>Cout 2-3 x 22uF/25V X7R"]
    V5 --> J2["J2 screw terminal<br/>EXTERNAL LOAD 3.0 A = 15 W"]
    V5 --> D1["D1 green LED + 1k<br/>1.9 mA"]
    V5 --> TP["TP1-3 test points<br/>0 A"]
```

There are no on-board consumers worth budgeting: the load is external
(3.000 A, stated + bounded by A2), the power LED is 1.9 mA, and the regulator's
own bias is 24 uA. Everything below is about what the board turns into heat.

## 2. Topology and operating points

| Item | Choice | Tradeoff (one line) |
|---|---|---|
| Conversion | Integrated-FET **synchronous** buck | Required by spec; also the only topology that fits the thermal budget - an async catch diode would add ~1.0 W at low line (0.5 V x 3 A x (1-D)). |
| Switching freq | **400-600 kHz** (design at 500 kHz) | Lower f = less switching loss and a smaller thermal problem; higher f = smaller L. At 500 kHz t_on at 18 V is 556 ns, far above the 75-108 ns minimum on-time; an MHz-class part would trade the 18 V corner and ~0.2 W of heat for board area we do not need to save. |
| Reverse polarity | Series **P-FET** (A4) | 0.080 W vs ~1.1 W for a Schottky; costs 2 extra parts (gate resistor + zener). Settled by A4. |
| Fuse | SMD **time-lag**, input side (A5) | One-shot; protects against a shorted FET/cap, not against output overload (the regulator's hiccup limit does that). |
| Output regulation | **Fixed 5 V** part preferred over adjustable | A fixed part meets A3's +/-3 % on its own (class reference: -1.5/+1.5 % over 7-36 V, 1 A to max load). An adjustable part stacks divider tolerance on a +/-1.5 % reference - needs 0.5 % resistors to stay inside. buck.md s4 FB trap applies. |

Operating points at 3 A out (D = Vout/Vin, L = 6.8 uH, f = 500 kHz):

| Vin | D | Inductor ripple | Peak I_L | Input current |
|---|---|---|---|---|
| 7 V | 0.714 | 0.42 A (14 %) | 3.21 A | 2.31 A |
| 12 V | 0.417 | 0.86 A (29 %) | 3.43 A | 1.34 A |
| 18 V | 0.278 | 1.06 A (35 %) | 3.53 A | 0.89 A |

Duty and input current agree with the P0 digest of the sibling run
(`boards/sbuck-5v3a/log/P0-digest.md`: D = 0.71/0.42/0.28, Iin = 2.44/1.42/0.95
at an 88 % efficiency floor) - that run assumed a worse efficiency, which is
why its input currents are ~6 % higher.

## 3. Loss breakdown at the three line corners (3 A out)

Model inputs, all stated so they can be challenged:

- **RDS(on)** 45 mohm HS / 20 mohm LS typ @25 C (Diodes AP64500 class, DS41979),
  scaled **x1.35** for a ~110 C junction (+0.4 %/C, class typical).
  P_cond = Io^2 x [D x R_HS + (1-D) x R_LS]; the ripple term (dI^2/12) adds <1 %.
- **Switching** 0.5 x Vin x Io x (tr+tf) x f with tr+tf = 15 ns at 500 kHz.
- **Gate + IQ + dead-time + Coss + unmodelled** = 0.09 W flat. Dead-time loss is
  tiny for this class (LMR33630 SNVSAN3F: t_D = 2 ns -> ~4 mW).
- **Inductor** DCR 22 mohm; core loss estimated at 0.04/0.06/0.08 W (rises with
  ripple). **Fuse** 22 mohm cold. **P-FET** 15 mohm. **Cin** ~4 mohm bank ESR.
- **Copper + screw-terminal contacts**: ~8 mohm in the input path, ~9 mohm in the
  output path + GND return (2 mohm/contact, 1 oz pours at the widths of s7).

| Loss term | 7 V in | 12 V in | 18 V in |
|---|---|---|---|
| Regulator conduction | 0.461 W | 0.370 W | 0.328 W |
| Regulator switching | 0.079 W | 0.135 W | 0.203 W |
| Regulator gate/IQ/misc | 0.090 W | 0.090 W | 0.090 W |
| **Regulator subtotal** | **0.630 W** | **0.595 W** | **0.621 W** |
| Inductor DCR | 0.198 W | 0.199 W | 0.200 W |
| Inductor core | 0.040 W | 0.060 W | 0.080 W |
| Reverse-polarity P-FET | 0.080 W | 0.027 W | 0.012 W |
| Fuse | 0.118 W | 0.039 W | 0.017 W |
| Cin ESR (1.36/1.48/1.34 A rms) | 0.007 W | 0.009 W | 0.007 W |
| Cout ESR | ~0 W | ~0 W | ~0 W |
| Copper + terminal contacts | 0.127 W | 0.098 W | 0.090 W |
| **BOARD TOTAL** | **1.200 W** | **1.028 W** | **1.027 W** |
| Pin / efficiency | 16.20 W / **92.6 %** | 16.03 W / **93.6 %** | 16.03 W / **93.6 %** |

Reading of the table:

- **Low line is the worst corner.** Conduction loss scales with D (0.46 W into
  the FETs at 7 V) and input current is 2.6x the high-line value, which triples
  the P-FET and fuse loss.
- Switching loss triples from 7 V to 18 V while conduction falls by as much, so
  the regulator's own dissipation is nearly flat (0.60-0.63 W). The *board* loss,
  not the IC loss, is what makes low line the worst thermal case.
- Everything outside the regulator sums to 0.41-0.57 W - not noise: it raises the
  local ambient the regulator sits in (s4).
- Substituting a mainstream 95/66 mohm 3 A-class part makes the regulator
  subtotal **1.21 / 1.15 / 1.15 W** and efficiency ~88-89 % - the difference
  between passing and failing the thermal case.

## 4. Thermal: junction temperature at 50 C ambient, no airflow

### 4.1 theta_JA - what number, and where it comes from

| Source | Value | Condition |
|---|---|---|
| TI LMR33630 SNVSAN3F thermal table, HSOIC-8/DDA | **42.9 C/W** | JESD51-7, simulated **4-layer JEDEC board** (76.2 x 114.3 mm). TI states verbatim that this value "can not be used for design purposes". |
| same table | RthetaJC(bot) **4.3 C/W**, psi_JT **4.3 C/W**, RthetaJB 13.6 C/W | useful for bench verification, see 4.4 |
| repo `check_thermal.py` calibrated model, >= 4 copper layers, pour saturated (>= 645 mm^2 within a 14.3 mm radius) | **51.1 C/W** | 4-layer, planes; ~19 % worse than the JEDEC board, consistent with our board being 4.4x smaller |
| same model, 2 layers, pour saturated | **73.9 C/W** | 1 oz, bottom pour |

I use the repo model's **51 C/W (4L)** and **74 C/W (2L)** as the design
numbers - they are the ones P8 will apply, and they are the pessimistic side of
the JEDEC anchor, which is correct for a 50 x 40 mm board. Every number in this
section carries the model's stated +/-30 %.

### 4.2 Junction temperature, both stackups, both part classes

T_j = 50 C ambient + P_IC x theta_JA + ~10 C for neighbour heating (the other
0.40-0.57 W of board loss raises the local air/board the regulator sees; theta_JA
assumes the rest of the board is at ambient, which it is not).

| Case | P_IC (7 V corner) | 2 layers | 4 layers |
|---|---|---|---|
| Recommended class (45/20 mohm) | 0.63 W | 96.6 + 12 = **~109 C** | 82.1 + 9 = **~91 C** |
| Mainstream 3 A class (95/66 mohm) | 1.21 W | 139.5 + 12 = **~152 C** | 111.7 + 9 = **~121 C** |

Against the targets: requirements s3 assumes a **105 C** derated hotspot; the
class absolute maximum is **150 C** with thermal shutdown at ~165 C, and TI
notes that operating above **125 C** "degrades the lifetime of the device".

- 2L + mainstream part: **fails outright** (over absolute max).
- 2L + best part: 109 C - over the 105 C target, under the 125 C knee, and with
  no margin for the RDS(on) max spec (~1.7x typ), which alone passes 125 C.
- 4L + mainstream part: 121 C - at the lifetime knee, no margin.
- **4L + <= 90 mohm class: ~91 C, 14 C under the target.** Recommended.

As ambient headroom, the more useful form: the recommended design runs at
**T_j = T_amb + 41 C** and hits the 125 C knee at an **83 C** ambient (33 C of
overshoot, or room for an enclosure). The mainstream part runs at **T_amb +
71 C** and hits 125 C at **54 C** ambient - no margin against the 50 C spec.

### 4.3 Why 4 layers wins - two independent mechanisms

1. **Via path length.** The exposed pad's thermal vias only have to reach In1 at
   ~0.21 mm depth on a JLC 1.6 mm 4-layer stackup. A 0.3 mm drill, 25 um plated
   via has a barrel cross-section of 0.0236 mm^2, so R = L/(k x A) =
   **22 C/W to In1** vs **176 C/W** for the full 1.6 mm to B.Cu on a 2-layer
   board. Nine vias: **2.4 C/W vs 19.6 C/W**. That is ~11 C of junction
   temperature at 0.63 W, free.
2. **Spreader area.** Two full-area inner planes roughly double the copper inside
   the ~14 mm radius that actually participates (the model's `REACH_MM`), and
   they are unbroken - unlike a 2-layer bottom pour that is also the return path
   and gets cut by the output routing.

Recommended stackup: **4 layers, 1 oz outer / 0.5 oz inner (JLC standard
1.6 mm)**. F.Cu components + hot loop + /SW + the +5V pour; **In1 = solid GND**
(unbroken under U1 and the entire Cin->VIN->GND loop); **In2 = GND again, not
+5V** (the +5V rail travels ~15 mm and needs no plane; a second GND plane is
worth more as thermal mass); B.Cu = GND pour, clear of SMT parts per A11.

### 4.4 Copper and via prescription for U1

- Exposed-pad land >= EP size, with a **3x3 array of 0.3 mm vias at 1.0 mm
  pitch** (tented on B.Cu; epoxy-filled via-in-pad is not needed at 0.6 W).
- **>= 200 mm^2 of contiguous F.Cu GND pour** joined to that land, plus **>= 3
  more GND vias** in it, for **>= 12 GND vias within 4 mm** of the part.
- In1/In2 GND solid under the part; do not let a signal or the +5V pour cut them.
- Total GND copper within a 14.3 mm radius must exceed 645 mm^2 summed over
  layers - two inner planes satisfy this on their own, so the constraint really
  binds the *top* pour and the via array.
- Keep **L1 >= 5 mm from U1** (0.24-0.28 W, its own hot spot) and put **F1 in the
  coolest corner** near J1 - fuse ratings derate ~30 % at 90 C.
- **No aluminium electrolytic anywhere.** At a ~90 C board temperature a 105 C
  2000 h part lasts ~5.7 kh. Cin/Cout are all-ceramic; any added bulk is polymer.
- Bench verification recipe: measure the case top and use **T_j = T_top +
  psi_JT x P** (4.3 C/W x 0.63 W = +2.7 C) rather than trusting theta_JA.

## 5. Input capacitor - RMS ripple requirement

I_rms(Cin) = sqrt( D x (Io^2 + dI^2/12) - (D x Io)^2 ), maximal at **D = 0.5**,
i.e. **Vin = 10 V, inside the operating window** - not at 7 V or 18 V.

| Vin | 7 V | **10 V** | 12 V | 18 V |
|---|---|---|---|---|
| I_rms | 1.36 A | **1.51 A** | 1.48 A | 1.34 A |

(The sibling P0 digest independently derived 1.50 A at Vin = 10 V.)

Requirement: **>= 1.5 A RMS at 500 kHz at 100 C**, X7R or better. The RMS rating
itself is easy for ceramics (1.5^2 x 4 mohm = 9 mW of self-heating); the traps
are the other three:

- **Temperature class**: the board hotspot is ~90 C. **X5R (85 C) is
  disqualified**; use X7R (125 C) or X6S.
- **Voltage rating**: 50 V, for two reasons. DC-bias derating (a 25 V 10 uF 1210
  keeps ~50 % at 12 V; a 50 V part keeps ~75 %), and the hot-plug ring below.
- **Hot-plug ring**: ~1 uH of supply lead against ~13 uF of low-ESR ceramic is a
  0.28 ohm characteristic impedance and rings to ~2x the step - **~36 V from an
  18 V plug-in**. Hence a **20-24 V standoff TVS on +VIN** (after the P-FET, so a
  reverse connection does not short it) clamping <= 33 V, and 40 V-rated silicon.

Sizing: **2 x 10 uF 50 V X7R 1210 + 100 nF 50 V 0603 at the VIN pin**
(~13 uF effective) gives 115 mV of input ripple at the D = 0.5 worst case. Leave
an unpopulated footprint pair for the optional input filter A7 asks room for.

## 6. Output capacitor - 50 mV pk-pk and the transient question

dV_pp = dI x ESR + dI / (8 x f x C). Worst dI = 1.06 A at the 18 V corner.

With **2 x 22 uF 25 V X7R 1210** (~30 uF effective after 5 V DC bias, ~2 mohm):
8.9 mV capacitive + 2.1 mV ESR = **~11 mV** modelled, ~15-25 mV measured at
20 MHz. **Against a 50 mV budget that is settled with 2x margin** - ripple is not
what sizes Cout here. Confirm the value sits inside the chosen part's stated
C/ESR stability window (buck.md s4); internal compensation assumes it.

What does size Cout is the **load transient**, and the load is external and
unspecified. A 0 -> 3 A step against 30-40 uF and a ~40 kHz loop dips the rail
~**300-340 mV (6-7 %)**, outside A3's +/-3 % window if that window is read
dynamically. A3 says "DC accuracy", so the steady-state reading is defensible -
the cheap hedge is one **100 uF polymer at J2** (135 uF total -> ~88 mV, 1.8 %),
which also damps the load cable. See OPEN 1.

Inrush is a non-issue the other way: 66 uF through a ~4 ms internal soft-start
draws 82 mA. A large *external* load capacitance is the risk - >1000 uF needs
>1.25 A of extra charging current and can trip the limit into hiccup retry,
which is correct behaviour, not a fault.

## 7. Inductor, protection chain, sequencing

- **L1: 6.8 uH +/-20 %, Isat >= 6 A, DCR <= 25 mohm, shielded composite, 125 C.**
  Isat must beat the part's **peak current limit** (4.5-5.5 A class), not the 3 A
  load (buck.md s2). 6.8 uH holds ripple to 35 % at 18 V; 4.7 uH would need
  ~700 kHz to match, buying nothing and costing switching loss. DCR is real
  money: 22 mohm = 0.20 W = 20 % of the loss budget.
- **Q1 P-FET: RDS(on) <= 15 mohm specified AT Vgs = -4.5 V.** The non-obvious
  one - at the 7 V corner the gate only has 7 V, so a part characterised at -10 V
  may not be in that state. Vds >= -40 V (hot-plug ring), Id >= 6 A, exposed-pad
  SO-8/DFN. Gate: 100 kohm + a 12-15 V zener to hold Vgs inside its -20 V limit
  at 18 V in; optional 10-100 nF gate cap = hot-plug soft-start. Loss 0.080 W at
  2.31 A, inside A4's 100 mW target.
- **F1: time-lag (slow-blow)** so Cin inrush does not open it; 4 A per A5 but see
  OPEN 2; cold resistance <= 25 mohm (0.118 W at low line). Output short and
  overload are handled by the regulator's hiccup limit + thermal shutdown (A5) -
  the fuse only covers a shorted FET or cap.
- **Sequencing: none** (single rail). EN can tie to +VIN (class parts
  auto-start); a 2-resistor EN divider at a ~6.3 V rising threshold is worth
  fitting so the converter does not try to run below its 7 V spec on a slow ramp.

## 8. What the later phases must carry (see power.json)

- `power_constraints`: /VIN, /VIN_F, +VIN at 3.0 A dT 10 (1.80 mm at 1 oz outer -
  the same width carries the fuse's 4 A non-blow current at ~19 C rise); /SW at
  3.5 A dT 20 (1.51 mm, deliberately narrower to keep the switch node small);
  +5V at 3.5 A dT 10 (2.23 mm, = peak inductor current); GND at 3.5 A
  `plane_fed`, declared explicitly so pour necks are errors and not the advisory
  findings the derived-return synthesis would produce.
- **/SW and +5V must have ZERO vias.** check_current's via rule is net-wide: one
  via on a 3.5 A net demands 7 vias in that cluster (LEARNINGS 2026-07-28); a
  via-free pour is also exempt from the pour-neck test. F.Cu only, both nets.
- `thermal_constraints`: U1 at **0.8 W** (0.63 W modelled + 27 % RDS(on) spread),
  `dt_c` **55** (105 C junction at 50 C ambient), `min_vias` 12 - an entry that
  encodes the stackup decision: 40.9 C rise on 4 layers (pass, 14 C margin) vs
  59.1 C on 2 layers (fail). Re-derive `power_w` if the chosen part's typ RDS(on)
  sum exceeds ~90 mohm.
- P6/P7 must add `overrides` for the D1 LED tap and thin test-point stubs once
  placement exists, or every 0.25 mm branch reads as an undersized 3.5 A track.

## 9. OPEN

1. **Load transient profile of the external load** - step size and rate. Ripple
   is met with 2x margin, but a 0 -> 3 A step dips the rail ~300 mV (6 %). Either
   confirm A3's +/-3 % is a DC/line-load-regulation spec only (as written), or
   accept one 100 uF polymer at J2 as the hedge.
2. **Fuse rating: 4 A (A5) or 5 A?** At the 85-95 C local board temperature a 4 A
   SMD fuse derates to ~2.8 A against 2.31 A of worst-case operating current -
   22 % margin, with nuisance-opening risk at the 7 V corner. 5 A time-lag is the
   engineering recommendation; it needs an explicit yes because it relaxes a
   binding answer.
3. **Is <= 105 C junction a hard part-selection filter?** It is what eliminates
   mainstream 95/66 mohm 3 A-class parts (~121 C on 4 layers) and forces the
   45/20 mohm 5 A class (~91 C). If 125 C is acceptable instead, the part field
   widens and cost drops slightly - at the cost of all thermal margin.

## Sources

- TI **LMR33630** SNVSAN3F (Nov 2020) - thermal table (RthetaJA 42.9 C/W DDA per
  JESD51-7 on a 4-layer JEDEC board, RthetaJC(bot) 4.3, psi_JT 4.3), RDS(on) DDA
  95/66 mohm typ (160/110 max), fsw 400 kHz "A", t_ON_MIN 75 ns, D_MAX 98 %,
  I_SC 4.5 A typ, t_SS 4 ms, dead time 2 ns, T_SD 165 C, Vout +/-1.5 % at 5 V,
  and the note that operating above 125 C degrades lifetime.
- Diodes **AP64500** (DS41979) - 3.8-40 V, 5 A, SO-8EP sync buck, 45/20 mohm,
  100 kHz-2.2 MHz programmable, 25 uA IQ in PFM. Low-RDS(on) class exemplar; its
  thermal table was NOT read (vendor PDF returns 403) - only the 4-layer/2 oz
  test condition from the summary page.
- Repo `check_thermal.py` calibrated theta_JA model (JEDEC JESD51 / TI SLOA122
  anchors) and `check_current.py` IPC-2152 width table.
- House reference `.claude/skills/ai-ee/reference/topologies/buck.md` (s2 Isat
  rule, s3 hot loop, s4 FB trap and Cout window, s5 SW containment).
- `boards/sbuck-5v3a/log/P0-digest.md` - independent cross-check of D, Iin and
  the 1.50 A Cin ripple peak at Vin = 10 V.
