# Requirements: bb-buck

## 1. Function
A bare step-down (buck) DC-DC converter, built as a study article. It takes
18-30 V DC (24 V nominal) from a bench power supply on a 2-pin screw
terminal and produces 5 V at up to 2 A (10 W) on a second 2-pin screw
terminal feeding a resistive load. Non-isolated, common ground in to out.
Nothing else is on the board: no MCU, no second rail, no digital interface,
no indicators.

BUILD MODE: **ultra-bare-bones** (declared by the brief's opening token,
recorded as a P0 decision; contract in `reference/build-modes.md`). The
block under study is the buck converter itself. Scope is that block plus
exactly the support parts its datasheet requires at the stated operating
point, one input and one output interface, and what the fab needs to build
the board and the bench needs to hold it. Protection, filtering,
indicators, spare rails and enclosure features are OUT by mode, not by
engineering judgment. The mode's defaults are applied below (quantity 5,
JLC PCBA single-sided, bench 0-50 C indoor, no enclosure, fewest honest
layers, smallest honest outline, stop at P9) instead of being asked.

Synchronous vs asynchronous rectification is deliberately NOT fixed here.
The brief leaves it open and it is a P1 architecture call, not a
requirement. Both are in scope as long as the block meets the stated
operating point.

## 2. Interfaces
Exactly two, both stated by the brief.
- Power input (J1): 2-pin screw terminal (stated). DC only, 18-30 V.
  ASSUMED: through-hole 2-pole terminal block, 5.08 mm pitch, rated
  >= 300 V and >= 10 A so it is never the limiting element against the
  ~0.7 A worst-case input current. Pitch was not stated; 5.08 mm is the
  common, well-stocked JLC/LCSC choice and accepts bench-supply lead wire
  comfortably. Polarity silkscreen-marked (+ / -). NOTE: the board has no
  reverse-polarity protection by mode, so the silk marking is the only
  defense against a swapped supply - see section 8.
- Power output (J2): 2-pin screw terminal (stated). 5 V, up to 2 A.
  ASSUMED: same terminal family and part as J1 for BOM consolidation,
  placed on a different board edge and silk-labelled distinctly (VIN vs
  5V OUT) so the two cannot be confused at the bench.
- No other external interface exists or is wanted: no USB, no header, no
  comms bus, no external enable, no power-good, no fault output, no LED.
  All excluded by mode.
- Measurement access ANSWERED (A4): exactly one switch-node probe pad with
  an adjacent ground pad. No other test points - VIN, VOUT and GND are
  reachable at the terminals.

## 3. Power
- Source: bench DC power supply, 18-30 V, 24 V nominal (STATED
  explicitly by the brief - not a guess, not a battery, not mains-derived
  on this board, not automotive). Section 8 depends on this being stated.
- Load: resistive, up to 2 A at 5 V (STATED). ASSUMED: the load range is
  0 to 2 A, i.e. the board must also be stable and safe with NO load
  connected (the realistic bench case of powering up before the resistor
  is attached). This is the conservative reading of "up to 2 A" and it
  constrains the converter's light-load behavior, so it is recorded rather
  than left silent.
- ASSUMED: 2 A is the absolute maximum output, continuous. A resistive
  load draws no surge beyond its steady value, so no peak allowance above
  2 A is carried. Inrush into the board's own output capacitance at
  startup is the converter's soft-start problem, not a load requirement.
- Output rail: one rail, fixed 5 V nominal. ASSUMED: fixed output, not
  adjustable, no trim, no sequencing. Accuracy and ripple ANSWERED (A3):
  +/-3 % DC (4.85-5.15 V) across the full 18-30 V input and 0-2 A load
  range, ripple <= 50 mV peak-to-peak.
- Input current (GUESS, for sizing only): 10 W out at an assumed 88-93 %
  efficiency -> 10.8-11.4 W in. At 18 V low line ~0.60-0.63 A; at 24 V
  ~0.45-0.47 A; at 30 V high line ~0.36-0.38 A. Size the input terminal,
  input copper and input capacitor RMS rating for >= 1 A continuous with
  a switched peak of ~2.5 A. Output terminal and copper for >= 2.5 A
  continuous.
- Board dissipation (GUESS): ~0.8-1.4 W typical, ~1.8 W at a pessimistic
  85 % efficiency. Worst case sits at the 30 V high-line corner where
  switching loss dominates. At the mode's 50 C maximum ambient with
  natural convection this is a real thermal driver on a small outline -
  copper area under the converter is a design input, not an afterthought.
- Duty cycle (derived, for P1): D ~ Vout/Vin = 0.28 at 18 V, 0.21 at
  24 V, 0.17 at 30 V. The 30 V corner sets the minimum on-time
  constraint, which bounds how high the switching frequency can go for a
  given part - a real P1/P2 selection constraint, flagged here, not
  decided here.
- No battery, no charging, no energy storage function, no backup rail.
  None stated and none implied by a bench supply source.
- Excluded by mode (SCOPE decisions, not engineering conclusions - do not
  record any of these as generally unnecessary): input TVS/clamp, reverse
  polarity protection, input fuse, pi/EMI input filter, OVP/OCP/UVLO
  beyond what lives inside the converter IC, output LC filter beyond what
  the datasheet requires.

## 4. Environment
Mode defaults - applied, not asked.
- Ambient: 0 to 50 C, indoor bench.
- Cooling: natural convection only. No forced airflow, no heatsink, no
  chassis thermal path.
- No enclosure. No ingress (IP) rating. No vibration or shock
  requirement. No humidity requirement. No conformal coating.
- No formal EMC/emissions campaign - this is a bench study article, not a
  product. Tight power-loop layout is still required because it is what
  makes the block correct, not because a test demands it.

## 5. Size & mounting
- Outline: **no HARD cap.** Nothing here binds permanently at P5
  board_init. The mode governs instead: the smallest outline that keeps
  the layout HONEST - never so tight that the power loop, the copper
  thermal area or the terminal spacing stop being representative of a
  real 24 V -> 5 V / 2 A buck, and never padded for features this board
  does not have.
- Non-binding expectation for planning only (NOT a cap): roughly
  30-40 mm x 20-28 mm, dominated by the two screw terminals plus the
  converter, inductor and capacitors. If the honest layout needs more,
  it takes more.
- Layers: ASSUMED 2, per the mode's "fewest layers the block honestly
  needs". If the P2/P4 thermal work shows 2 layers cannot carry ~1.2-1.8 W
  at 50 C ambient inside the honest outline, 4 layers is allowed under the
  same rule. Not fixed here either way.
- Mounting: ASSUMED 4 x M3 clearance holes (3.2 mm) inset from the
  corners, so the board can sit on standoffs at the bench. Mounting the
  bare board is explicitly in mode scope. If the honest outline turns out
  too small for four, two on opposite corners is acceptable.
- Height: ASSUMED no maximum. The board is open on a bench with no
  enclosure, and the screw terminals themselves stand ~10-12 mm tall with
  wire fitted, so a height cap would be arbitrary.
- Connector placement: ASSUMED both terminals on board edges with their
  wire openings facing outward, on different edges, so bench wiring does
  not cross the board. Which edges is the layout engineer's call.

## 6. Quantity & budget
Mode defaults - applied, not asked.
- Build quantity: 5.
- Cost: minimal, with no hard per-unit cap. Prefer JLC Basic/Preferred
  parts wherever a Basic part actually meets the electrical requirement;
  Extended is allowed for the converter IC and the power inductor, where
  Basic stock is thin in this class.

## 7. Assembly
Mode defaults - applied, not asked.
- JLCPCB PCBA, single-sided: all SMT parts on the top side only. The
  bottom side stays clear of SMT so it can serve as unbroken
  thermal/return copper.
- The two screw terminals are through-hole. ASSUMED: fitted by JLCPCB
  through-hole assembly if offered at acceptable cost for the chosen
  part, hand-soldered after SMT otherwise. Either path leaves the
  schematic and the footprint unchanged.
- Pipeline stops at P9 (fab package + DFM). Ordering is a separate owner
  decision and is not requested here.

## 8. Compliance/safety flags
No safety question is open on this board, and that conclusion is derived,
not assumed. The mode grants no silence here - it simply happens that the
brief states the two facts that would otherwise have to be asked.

- **Mains voltage: DOES NOT APPLY.** The board sees DC only. Generating
  that DC is out of scope; the brief names a bench supply as the source.
- **Batteries: DOES NOT APPLY.** The source is STATED as a bench power
  supply. This is the one question that has no default and must never be
  guessed, and the brief answers it explicitly, so it is not asked. No
  battery on the board, no charging function, no pack chemistry, no
  deep-discharge or UVLO behavior required. If the owner ever runs this
  board from a battery instead, that is a new requirement and this
  section must be re-opened.
- **Motors: DOES NOT APPLY.** The load is STATED as resistive. No
  inductive, stalling or regenerative load, therefore no reverse energy
  into the output and no startup surge beyond the resistor's own draw.
- **RF transmit: DOES NOT APPLY.** No radio function.
- **High current (>3 A): DOES NOT APPLY.** Maximum continuous current
  anywhere on the board is the 2 A output. Input current peaks at ~0.63 A
  continuous at the 18 V low-line corner. The largest instantaneous
  current is the inductor peak, GUESSED at ~2.3-2.6 A depending on the
  ripple ratio P1 chooses - still under 3 A. The threshold is not
  approached closely enough to be a judgment call.
- **>30 V: DOES NOT APPLY at the stated number, but the range's top edge
  is genuinely under-defined.** Reasoning, explicitly:
  - The stated maximum is 30 V, and the threshold is *greater than* 30 V.
    30 is not >30, so the flag does not trip on the stated figure. This
    is a boundary case, so it is reasoned about rather than waved past.
  - No real hazard exists at 30 V DC. It is well below the 60 V DC limit
    for a non-hazardous DC source under IEC 62368-1 (ES1), so there is no
    shock hazard to a person handling the board. Fault energy is bounded
    by the bench supply's own current limit, and at <= 1 A input there is
    no arc or energy hazard at the terminals. No safety question follows
    from the voltage itself.
  - Downstream consequence worth noting: at exactly 30 V, the VIN-to-GND
    net pair is 30 V apart, which the pipeline's `check_creepage` treats
    as a clean no-op (its derived check engages only above 30 V). If the
    answer to Open question 1 lifts the ceiling above 30 V, that check
    engages for real and IPC-2221 spacing starts binding the layout. The
    boundary is therefore not cosmetic.
  - What WAS genuinely ambiguous - whether 30 V is the *operating* or the
    *survival* ceiling, and what the input does on a live connection - is
    now ANSWERED (A1, A2): 30 V is a hard maximum OPERATING input, and
    there is no live hot-plug. The converter carries >= 36 V absolute-max
    as its own headroom; no clamp is added. The flag therefore stays
    DOES-NOT-APPLY on settled requirements, not merely on the boundary
    reading.
- **Reverse polarity: noted, not flagged.** The mode excludes reverse
  polarity protection, so connecting the bench supply backwards will
  destroy the converter. This is an accepted consequence of the declared
  scope on a bench article with silk-marked polarity, not a safety hazard
  to a person, and not a finding for a reviewer to raise. It is recorded
  so the consequence is visible rather than implicit.

## 9. Open questions - ALL FOUR ANSWERED 2026-08-15 (owner)

STATUS: **closed.** The owner took the stated DEFAULT on all four. Each
answer is recorded as a P0 `state.py decision` and is now a REQUIREMENT,
not a question. P1/P2 read the ANSWERED block below; the original question
text is kept underneath it for provenance only.

### Answers (binding)

- **A1 - Input ceiling.** 30 V is a HARD maximum operating input. Choose a
  converter whose absolute-maximum input rating is >= 36 V class (~20 %
  headroom above 30 V). The headroom lives in the PART, not in added
  components - no clamp, no TVS. Consequence retained: VIN-to-GND stays at
  or below 30 V, so `check_creepage` remains a no-op and IPC-2221 spacing
  does not bind the layout.
- **A2 - No live hot-plug.** The input is never connected while the supply
  is live: wires land first, then the supply ramps from zero. The ~2x
  lead-inductance ringing case (~60 V from a 30 V setting) is therefore OUT
  of the requirement set. The datasheet-required bulk input capacitance
  stays fitted and damps the incidental case; no damping component is
  added. A 36 V-class part is sufficient under this answer.
- **A3 - Output spec. AMENDED TWICE AT P3/P4 - read the amendment below, not
  just this paragraph.** As originally answered: +/-3 % DC, i.e. 4.85-5.15 V,
  held across the FULL 18-30 V input range and the FULL 0-2 A load range,
  with <= 50 mV peak-to-peak output ripple.

  **A3 AS AMENDED (this is the binding version).** A3 now has a TWO-REGION
  shape, and both amendments have the same root cause: the chosen part runs
  PFM / diode-emulation at light load and has no MODE pin to defeat it.

  | Load | DC accuracy | Ripple |
  |---|---|---|
  | ~200 mA to 2 A | +/-3 % (4.85-5.15 V) BINDING | <= 50 mV pk-pk BINDING |
  | 0 to ~200 mA | PFM light-load rise ACCEPTED | PFM burst ripple ACCEPTED |

  - *Amendment 1 (P3, owner-ruled).* The DDA package has no MODE/FCCM pin and
    is auto-mode only (datasheet 8.4.1, which states outright that PFM
    "yields larger output voltage ripple"). None of the three accept criteria
    - forced-CCM, a strappable MODE pin, or a datasheet figure at this
    operating point - was satisfiable. The mode excludes the usual fix (a
    preload resistor is excluded conditioning), so the owner relaxed ripple
    below ~200 mA rather than override the mode or re-source the part.
  - *Amendment 2 (P4, owner-ruled).* The SAME PFM behaviour also raises the
    output VOLTAGE at light load: datasheet Sec 7.7 specs regulation as
    -1.5/+1.5 % for IOUT >= 1 A but **-1.5/+2.5 % for IOUT 0 A to max**, a
    +1.0 % adder confirmed by Fig 9-19. Stacked on the worst 0-50 C divider
    corner that gave 5.161 V against the 5.15 V ceiling - outside. So the
    carve-out extends to DC accuracy below ~200 mA. An earlier statement that
    DC accuracy was unaffected at all loads was WRONG and is retracted here.
  - *Paid for, not merely relaxed.* The owner took the recentring remedy as
    well: the feedback divider moved from 100k/24.9k (5.016 V nominal, TI's
    own Table 9-2 pair) to **102k/25.5k**, an exact 4.000 ratio giving
    **5.000 V nominal**. That moved the stacked 0 A worst case from 5.161 V
    to 5.144 V - inside the original window even though it no longer has to
    be. Both parts are E96, 0.1 %/25 ppm, same Yageo RT family (TCR tracking
    preserved).

  The P8 simulation bounds encode this: error bounds stay on the full
  4.85-5.15 V window (the divider ratio is load-independent, so the carve-out
  relaxes the CONVERTER, not the divider), plus a warning-severity bound
  carrying the +1.0 % light-load stack so it stays visible in the gate. That
  warning bound is the ONLY check that catches a revert to 100k/24.9k.
- **A4 - Probe access.** Exactly ONE switch-node probe pad with an adjacent
  ground pad. Nothing else: VIN, VOUT and GND are already reachable at the
  two screw terminals. Mode-boundary ruling by the owner - the switch node
  counts as the block's own measurement need on a study article. Keep the
  pad minimal and inside the switch-node copper that already exists, so it
  adds as little area as possible to the noisiest node.

### Original question text (provenance)

1. **Is 30 V truly the highest the supply will ever be set to, or should
   the board survive a bit more?** A bench supply set to "30 V" may
   actually sit at 30.5 V, and a knob can be nudged. This board has no
   input clamp by design, so the converter chip's own maximum rating is
   the only thing standing between an overshoot and a dead board.
   DEFAULT: 30 V is a hard maximum operating input, and the converter is
   chosen with an absolute-maximum input rating at least ~20 % above it
   (36 V class or better) purely as selection headroom. No extra parts are
   added.
2. **Will you ever connect the input wires while the bench supply is
   already switched on and at voltage?** Connecting live through a metre
   of lead wire makes the input voltage ring up to roughly twice the
   supply setting for a few microseconds - about 60 V from a 30 V supply -
   because the lead inductance rings against the board's ceramic input
   capacitors. That transient is well beyond what a 36-40 V part
   tolerates, and the mode excludes the clamp that would normally absorb
   it, so the answer changes which parts are even eligible.
   DEFAULT: no live hot-plug. You connect the wires first, then bring the
   supply up from zero. The bulk input capacitance the datasheet already
   requires stays fitted and damps the incidental case; nothing extra is
   added. If you answer "yes, I will hot-plug it", say so - it will force
   either a much higher-voltage part or a damping component the mode would
   otherwise exclude, and that is an owner call.
3. **How tight does the 5 V output need to be?** Two numbers: how far
   from exactly 5.00 V is acceptable, and how much high-frequency ripple
   can ride on top of it.
   DEFAULT: +/-3 % DC (4.85-5.15 V) across the full 18-30 V input range
   and the full 0-2 A load range, and <= 50 mV peak-to-peak output
   ripple. Ordinary, honest numbers for a study article - not a precision
   rail, not a loose one.
4. **Do you want one probe point on the switching node?** That means a
   small pad on the switch node with a ground pad right beside it, so a
   scope probe with a short ground can measure switch-node ringing and
   efficiency properly at bring-up. This is the one place the mode's
   boundary needs an owner ruling: the mode excludes test points "beyond
   the block's own measurement need", and for a board whose purpose is to
   be studied - and whose bring-up evidence is what proves out the
   knowledge records it exists to seed - that need is arguable either way.
   The tradeoff is real: a pad hangs extra copper on the noisiest node on
   the board.
   DEFAULT: yes - exactly one switch-node probe pad with an adjacent
   ground pad, and nothing else. VIN, VOUT and GND are already reachable
   at the two screw terminals, so no other test points are added.
