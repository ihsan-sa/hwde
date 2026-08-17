# bb-ldo - requirements (P0)

Source: `brief/brief.md` (owner, verbatim). Mode resolved at P0 and recorded in
`state.json`. Contract: `reference/build-modes.md`.

## 1. Function

A single-block linear regulator bench board: it takes 5 V DC in on a screw
terminal and delivers a regulated 3.3 V rail at up to 500 mA out on a screw
terminal, holding regulation at full load in still air (no airflow, no
heatsink other than the board's own copper).

**Build mode.** Token `learning block-basics:` -> target **block-basics**,
scope tier **block-only**, binding **canonical**, stage under study: **none**
(the run teaches the block end to end, not one stage).

- Scope tier `block-only`: the board is the regulator, one input interface and
  one output interface, plus exactly the support parts the regulator's
  datasheet requires at this operating point. Excluded feature classes -
  protection, filtering (beyond what the datasheet requires), indicators,
  test-points, config, second-rail, mechanical, enclosure-fit - are SCOPE
  decisions, not engineering judgements, and their absence is not a finding.
  `thermal` is excluded by no tier: see sections 4 and 5.
- Binding `canonical`: the board geometry is an **OUTPUT** of the design, not
  an input. P5 runs `board_init --outline auto`, P6 places to the canonical
  thermal/loop layout, then `board_edit --outline fit` makes the board what
  the placement earned. No dimension in this document is a HARD cap.
- The mode relaxes geometry, cost and packaging only. Every electrical spec,
  gate, coverage check, research trigger, DFM check and safety question below
  is at full rigor.

## 2. Interfaces

| # | interface | direction | electrical | connector |
|---|---|---|---|---|
| J-in | DC input | in | 5 V DC nominal, ~505 mA max (see section 3) | screw terminal, 2 position (+5V, GND) - STATED by owner |
| J-out | 3.3 V rail | out | 3.3 V DC, 0 to 500 mA | screw terminal, 2 position (+3V3, GND) - STATED by owner |

- No other external interface: no USB, no RF, no signal I/O, no enable/config
  pin brought out, no status LED (indicators are excluded at `block-only`; a
  regulator enable/config strap is `config`, also excluded - the block runs
  always-on with EN tied to its always-on state as the datasheet requires).
- No test points beyond the two terminals: output voltage and load current are
  measurable at J-out, which satisfies the block's own measurement need.
- Screw terminal pitch, wire range and mounting technology are unstated -
  question 8. ASSUMED until answered: 2 position, 5.08 mm pitch, through-hole,
  wire 0.2-2.5 mm2, from the JLCPCB catalog.

## 3. Power

- **Input**: 5 V DC, single source, on J-in. Source identity and fault current
  are UNSTATED and safety-relevant - questions 1 and 2. Voltage tolerance is
  UNSTATED - question 4. ASSUMED until answered: 4.75-5.25 V (5 V +/- 5%),
  which sets the worst-case dropout headroom at 1.45 V at 500 mA.
- **Output rail (the only rail)**: 3.3 V, 0 to 500 mA. Accuracy UNSTATED -
  question 5. Continuous vs peak current UNSTATED - question 6. Load character
  and any load-step/transient requirement UNSTATED - question 7.
- **Derived budget (GUESS - derived arithmetic, not owner-stated)**:
  - Output power at full load: 3.3 V * 0.5 A = 1.65 W.
  - Regulator dissipation, worst case high line: (5.25 - 3.3) * 0.5 = **0.98 W**;
    nominal line: (5.0 - 3.3) * 0.5 = **0.85 W**. Plus quiescent, so call it
    ~1 W to be dissipated by the package and the board copper.
  - Input current at full load: ~505 mA (load + quiescent). Efficiency is
    inherently ~63-66% - a property of the topology the owner chose, not a
    requirement to meet.
- No second rail, no sequencing, no soft-start requirement, no power-good.
- No battery, no charging - subject to question 1.

## 4. Environment

- **Still air, no airflow** - STATED by owner ("must hold regulation at full
  load with no airflow"). No forced convection, no heatsink, no thermal
  interface to anything but the PCB.
- Ambient **0 to 50 C, indoor bench, no enclosure** - mode default for
  `block-only` (taken, not asked). The thermal design point is therefore
  **~1 W dissipated at 50 C ambient in still air**.
- No ingress rating, no vibration, no shock, no conformal coating, no altitude
  or humidity spec: bench use.
- Thermal is in scope at every tier. The regulator must stay within its own
  safe junction temperature at the design point above, with margin - i.e. the
  required theta_JA follows from the package's Tj(max) and that 1 W at 50 C
  (for a 125 C part this is roughly 75 C/W or better). Meeting it is a P2/P3
  decision (package choice, copper area, via stitching); it is a REQUIREMENT
  here, not an optimization.

## 5. Size & mounting

- **No HARD size cap. Board outline is RELAXABLE (canonical) - it is an OUTPUT
  of the design, not an input.** The owner stated no dimension, and under the
  `canonical` binding none would bind anyway: P5 opens with
  `board_init --outline auto` (generous provisional room), P6 places the
  canonical layout, `board_edit --outline fit --margin M` then makes the board
  what that placement earned, and P7 routes it. Re-run `planes_gen` if the
  board grew.
- The outline is the radiator. The copper area needed to hit the theta_JA in
  section 4 is a primary input to what the placement earns - it is exactly the
  mechanism that must not be pre-empted by a guessed number (the bb-buck
  defect: a stated size that bound, and placement optimizing to fit it).
- Height: unconstrained (no enclosure). The tallest part will be the screw
  terminals.
- Mounting: mechanical features beyond mounting the bare board are excluded at
  `block-only`. Mounting holes are UNSTATED - question 9. ASSUMED until
  answered: none.
- Layer count: mode default, "the fewest layers the block honestly needs".
  ASSUMED 2 layers, with thermal copper on both and stitching vias under the
  regulator's pad; confirmed or revised at P2 against the thermal requirement.

## 6. Quantity & budget

- Quantity **5** (mode default, taken not asked).
- Cost: **minimal** (mode default). No unit-cost target; the mode relaxes cost.
- Stop at **P9** (fab package + DFM). Ordering is a separate owner decision.

## 7. Assembly

- **JLCPCB PCBA, single-sided assembly** (mode default, taken not asked). All
  SMT parts on the top side.
- ASSUMED: if the chosen screw terminal is through-hole only, it is hand
  soldered after PCBA (JLC economy assembly is SMT-only) - a packaging
  detail the mode relaxes. An SMT-mount terminal in the JLC catalog is
  preferred if one exists at the required current and wire size.
- Standard JLCPCB 2-layer process, HASL or ENIG per default DFM, no special
  stackup, no controlled impedance, no thick copper unless P2's thermal work
  shows it is required (in which case it is a datasheet-driven requirement,
  not a feature).

## 8. Compliance/safety flags

Assessed against the brief; every flag here is at full rigor - no mode
relaxes any of it.

| flag | applies? | basis |
|---|---|---|
| Mains voltage | **NOT APPLICABLE as stated** - but the SOURCE of the 5 V is unstated (question 1). If it is a mains-derived adapter, isolation lives in the adapter and the board stays SELV. | brief says 5 V DC in |
| Battery / charging | **UNKNOWN - must be answered before P2** (question 1). No chemistry, charging or protection may be guessed. | source unstated |
| > 30 V anywhere | No. Max node is the 5 V input. | brief |
| High current (> 3 A) | No. 500 mA out, ~505 mA in. | brief |
| Motors / inductive loads | UNKNOWN - depends on the load (question 7). A motor or solenoid load changes the transient and reverse-EMF picture. | load unstated |
| RF transmit | No. | brief |
| Hot surfaces | **YES, advisory.** ~1 W in a small package in still air: the regulator and its copper will be hot to the touch (typically 80-110 C surface at the design point). Bench handling hazard, recorded so the owner and the reviewers see it; not a scope item to fix. | derived, section 3 |
| Fault behaviour | The `block-only` tier excludes reverse-polarity, over-voltage and fusing protection on the screw terminal. A screw terminal invites a miswire, and without protection a reversed or over-voltage input destroys the block and can dump the source's full fault current. This is a recorded SCOPE consequence - question 3 asks the owner to accept it explicitly, and questions 1-2 bound how bad the fault can get. | tier + brief |

The pipeline does not proceed past P2 on guessed answers to questions 1-3.

## 9. Open questions

Safety - must be answered (no default is taken without your word):

1. **What supplies the 5 V?** (a) bench power supply, (b) USB wall adapter or
   USB port, (c) a battery pack, (d) something else. *Default if you have no
   preference: (a) a bench supply.* If the answer is (c), we also need the
   battery chemistry, cell count and whether this board ever charges it -
   none of that can be assumed.
2. **How much current can that source push into a dead short?** i.e. what is
   its current limit or fuse rating. *Default: 2 A or less (typical bench
   supply limit / USB adapter).*
3. **Do you accept no input protection?** The block-only scope means no
   reverse-polarity, over-voltage or fuse protection on the screw terminal: if
   the input is wired backwards or fed the wrong adapter, the board dies (and
   the source dumps its fault current into it). *Default: yes, accepted - it
   is a bench block.* Say no and we add protection, which moves the board off
   the block-only scope.

Electrical - defaults offered, correct me if any is wrong:

4. **What is the input voltage range?** *Default: 4.75 to 5.25 V (5 V +/- 5%).*
   This matters: at 4.75 V there is only 1.45 V of headroom above 3.3 V, so a
   wider low end forces a low-dropout part; at 5.25 V the regulator gets
   hotter. Tell me the real minimum and maximum if the supply is loose.
5. **How accurate does the 3.3 V need to be?** *Default: +/-3% (3.20 to 3.40 V)
   including line, load and temperature drift.*
6. **Is 500 mA continuous, or a short peak?** *Default: continuous, 100% duty,
   forever - the thermal design is sized for that.* If it is a brief peak with
   a low average, say so; the board can be smaller.
7. **What is on the output?** *Default: a static resistive bench load - no
   load-step or transient-response requirement, and only the output capacitor
   the regulator's datasheet requires for stability.* If the load switches
   hard, or is a motor/solenoid, say so - that is a different set of
   requirements.

Packaging - answer only if you care, defaults apply otherwise:

8. **Screw terminal preference?** *Default: 2 position, 5.08 mm pitch,
   through-hole, accepting 0.2-2.5 mm2 wire, from the JLCPCB catalog (hand
   soldered after assembly).* Name a pitch, wire size or specific part if you
   have one.
9. **Mounting holes?** *Default: none - it is a bare bench block.* Say "two M3"
   or "four M3" if you want to bolt it down.

### Answers - owner, 2026-08-16 (P0 close)

All nine answered; each is recorded as a `state.py decision`. Nothing below is
a guess: questions 1-3 (safety) carry the owner's own word.

| # | answer | consequence |
|---|---|---|
| 1 | **Current-limited bench supply.** Not a battery, not mains-direct. | Section 8 battery flag closes NOT APPLICABLE on an owner answer. No chemistry/charging requirements enter the design. |
| 2 | Source fault current **<= 2 A**. | Bounds the miswire/short energy; still no fusing at this tier (question 3). |
| 3 | **No input protection accepted.** | Tier exclusion stands. Reviewers must not report absent protection as a finding. Advisory hazard recorded. |
| 4 | **4.75-5.25 V** (5 V +/- 5%). | 1.45 V worst-case headroom at 500 mA -> a standard (non-LDO) regulator is admissible. Worst-case dissipation **0.975 W** at high line. |
| 5 | **+/-3%** (3.20-3.40 V) over line, load, temperature. | Ordinary fixed-output regulator accuracy; no trim, no external divider needed if a fixed 3.3 V part is chosen. |
| 6 | **Continuous, 100% duty.** | The thermal design is sized for steady state, not bursts. This is what earns the outline at P6. |
| 7 | **Static resistive bench load.** No transient spec. | Only the datasheet's own stability capacitance. No bulk output capacitor is added for transients this board will never see. No motor/inductive load - section 8's motor flag closes NOT APPLICABLE. |
| 8 | Default taken: 2 position, **5.08 mm pitch, through-hole**, 0.2-2.5 mm2 wire, JLCPCB catalog. | Hand soldered after PCBA if the chosen part is THT-only. |
| 9 | **No mounting holes.** | Bare bench block; mechanical stays excluded. |

**Owner delegation (2026-08-16):** "Make decisions yourself based on what will
give the best learning for the basic system." Design judgment calls and the
H1-H4 checkpoint ceremony are delegated to the orchestrator, which presents
digests with its rulings instead of blocking questions. NOT delegated and
unchanged: every gate, the P2/P3 coverage checks and the research they
trigger, DFM, and any NEW safety question that arises.

**Design point, frozen here:** 0.975 W dissipated at Ta = 50 C in still air,
no heatsink, no airflow, continuous. The required theta_JA and the copper
area that buys it are the primary drivers of what the placement earns.
