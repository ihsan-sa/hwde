# requirements.md - sbuck-5v3a

Source: `brief/brief.md` (sole input; no attached datasheets, drawings or reference
schematics were supplied).

Note on process: the brief carries an explicit DECISION POLICY - "Make every remaining
decision yourself. Do not ask clarifying questions. Where this brief is silent, take the
conventional, conservative option." Section 9 below therefore lists the unknowns as
questions WITH a recommended default each, so the orchestrator can rule on them as
delegate and record them in DECISIONS.md. Nothing in section 9 is blocking on the user.

Legend: `STATED` = written in the brief. `DERIVED` = arithmetic from stated numbers.
`GUESS` / `ASSUMED` = not in the brief, low risk, recorded so it can be overridden.
`HARD` = binds permanently at P5 board_init.

---

## 1. Function

A standalone, open-frame step-down DC-DC power module: it takes an unregulated 7-18 V DC
input (12 V nominal) on a 2-pin screw terminal and produces a regulated 5.0 V +/-2% output
at up to 3 A continuous (15 W) on a second 2-pin screw terminal, using a synchronous buck
topology built around an integrated buck IC (internal high-side and low-side switches)
rather than a controller plus discrete FETs. The board protects itself and its source
against reverse-polarity connection of the input, and protects itself against output
overcurrent and over-temperature. There is no MCU, no digital interface, no telemetry, and
no sequencing or remote control: the board regulates whenever a valid input is applied.
Scope is the converter only.

## 2. Interfaces

| # | Interface | Dir | Electrical | Connector |
|---|---|---|---|---|
| I1 | DC input | in | 7-18 V DC, 12 V nominal. Worst-case input current ~2.6 A at 7 V in / 3 A out (DERIVED). Reverse-polarity tolerant. | 2-pin 5.08 mm pitch screw terminal (STATED). Exact part/entry direction: Q9 |
| I2 | DC output | out | 5.0 V +/-2% (4.90-5.10 V), 3 A continuous. | 2-pin 5.08 mm pitch screw terminal (STATED) |
| I3 | Test point VIN | probe | post-reverse-polarity-FET input rail | test pad, see Q13 |
| I4 | Test point SW | probe | switch node, high dv/dt - short-stub tap only, must not extend SW copper | test pad, see Q13 |
| I5 | Test point VOUT | probe | regulated output, tapped at the output cap terminal | test pad, see Q13 |
| I6 | Test point FB | probe | feedback node - high impedance, probe loading must not shift setpoint | test pad, see Q13 |
| I7 | Test point EN | probe | enable / UVLO node | test pad, see Q13 |
| I8 | Test point GND | probe | general ground reference | test pad, see Q13 |
| I9 | Scope ground | probe | dedicated LOW-INDUCTANCE ground point adjacent to the VOUT test point, sized for a scope spring/bayonet ground rather than a ground lead (STATED) | see Q13 |

Non-connector interface items stated in the brief:
- RC snubber footprint across the low-side switch (i.e. SW to PGND), populated DNP by
  default. Footprint must exist and be routable with low inductance even though unstuffed.
- No indicator LED, no PG output, no external enable input, no adjustable-output feature,
  and no remote sense are stated. See Q11 (LED) and Q14 (EN control) for the defaults.

## 3. Power

### Input (STATED)
| Param | Value |
|---|---|
| Range | 7.0 - 18.0 V DC |
| Nominal | 12.0 V |
| Absolute max at connector | 18 V (no surge/load-dump spec given - see Q6) |
| Source impedance / cabling | not stated; brief requires bulk input capacitance for "the cable inductance", so a non-trivial cable run is implied |

### Output (STATED)
| Param | Value |
|---|---|
| Voltage | 5.0 V, +/-2% = 4.90-5.10 V (window scope: see Q1) |
| Current | 3.0 A continuous |
| Power | 15.0 W (DERIVED) |
| Ripple | < 50 mV pk-pk at full load (measurement bandwidth: see Q2) |
| Load step | 0 -> 3 A and 3 A -> 0: excursion < 200 mV, recovery within 100 us (slew rate of the step: see Q3) |
| Efficiency | > 88% at 12 V in, 3 A out (measurement points: see Q4) |

### Derived operating points (arithmetic from the stated spec; not guesses)
| Param | At Vin = 7 V | At Vin = 12 V | At Vin = 18 V |
|---|---|---|---|
| Duty D = Vout/Vin (ideal) | 0.714 | 0.417 | 0.278 |
| Input current at 3 A out, 88% eff | 2.44 A | 1.42 A | 0.95 A |
| Input cap RMS current, Iout*sqrt(D(1-D)) | 1.36 A | 1.48 A | 1.34 A |

- Worst-case input capacitor RMS current over the whole input range is 1.50 A, at D = 0.5,
  i.e. Vin = 10 V - which is INSIDE the operating range. Size the input ceramics for 1.5 A
  RMS, not for the 1.48 A at the 12 V nominal point.
- Board dissipation at the efficiency floor: Pin = 15.0/0.88 = 17.05 W, so Ploss = 2.05 W
  total at 12 V/3 A. This is the thermal budget the 50 C ambient case must close against.
- Reverse-polarity P-FET conducts the full input current (2.44 A worst case at 7 V) and its
  I^2*Rds(on) loss counts against the 88% number if efficiency is measured terminal to
  terminal (Q4).

### Rails
Single output rail. No auxiliary rails, no bias rail, no battery, no charging, no
energy storage beyond the converter's own input/output capacitance.

### Protection (all STATED as requirements)
| P | Requirement | Notes |
|---|---|---|
| P1 | Input reverse polarity | Brief directs a P-channel FET in the supply path (not a series diode) and requires its Vgs rating be confirmed against max Vin. Vgs clamp/divider needed if |Vgs| rating < 18 V. |
| P2 | Output overcurrent | Mechanism not specified - see Q7 |
| P3 | Thermal shutdown | Not specified whether IC-internal is sufficient - see Q8 |

## 4. Environment

| Param | Value | Status |
|---|---|---|
| Max operating ambient | 50 C | STATED |
| Airflow | none - natural convection only | STATED |
| Min operating ambient | not stated | Q15, default 0 C |
| Storage range | not stated | ASSUMED: -40 to +85 C, standard commercial part ratings |
| Enclosure | not stated | Q16 - drives whether 50 C is ambient-air or inside-a-box |
| Ingress protection | not stated | ASSUMED: none (open frame, indoor, dry) |
| Vibration / shock | not stated | ASSUMED: none beyond normal handling; no staking or conformal coat |
| Altitude | not stated | ASSUMED: <= 2000 m, no creepage derating |

Note: the thermal requirement is the one that bites. 2.05 W into natural convection at
50 C ambient on a board of at most 50x40 mm, with no heatsink, is the binding constraint
of this design, and the brief explicitly forbids assuming the exposed pad alone closes it.

## 5. Size and mounting

| Param | Value | Status |
|---|---|---|
| Max outline | 50.0 x 40.0 mm | **HARD** (STATED as "<=50x40mm"). Binds at P5 board_init. Smaller is permitted but see Q17 - recommended default is to use the full area for thermal copper. |
| Layer count | 2 or 4, designer's call, must be justified | STATED as a delegated decision - see Q18 |
| Mounting holes | 4x M3 | **HARD** on count and thread size (STATED). Positions, plating and keepout: Q19 |
| Max component height | not stated | Q20, default 15 mm |
| Board thickness | not stated | ASSUMED: 1.6 mm FR4, JLCPCB standard |
| Copper weight | not stated | Q21 - 1 oz outer default, 2 oz escalation path if thermals do not close |
| Keepouts / connector clearance | not stated | ASSUMED: screw terminals at board edges with wire entry clear of the mounting hardware |

## 6. Quantity and budget

| Param | Value | Status |
|---|---|---|
| Build quantity | not stated | Q22, default 5 (JLCPCB minimum prototype run) |
| Target unit cost | not stated | Q23, default: no hard cap; keep BOM under ~$12/board at qty 5 and flag anything that would push a single line item over ~$3 |
| Lifetime / production intent | not stated | ASSUMED: prototype / low-volume bench module, not a mass-production cost-down exercise |

Hard commercial constraint that IS stated: every part must be in stock at LCSC with its
part number recorded; an out-of-stock part is a failed design. Stock threshold: Q24.

## 7. Assembly

| Param | Value | Status |
|---|---|---|
| Assembly method | not stated | Q25, default: JLCPCB PCBA for all SMT |
| Sides assembled | not stated | Q26, default: single-sided (top) SMT assembly |
| Through-hole parts | the two 5.08 mm screw terminals are inherently THT | Q25 covers whether to buy JLC's THT service or hand-solder the two connectors |
| Footprint rotation | must be checked against JLCPCB's CPL convention, NOT the KiCad default | STATED |
| Process class | must respect JLCPCB minimum trace/space, annular ring and hole size for the selected class | STATED; class choice: Q27 |
| Part tier | LCSC Basic vs Extended not stated | Q28, default: prefer Basic/Preferred for passives, accept Extended where the function demands it (buck IC, inductor, P-FET) |

## 8. Compliance / safety flags

Applicable:
- **High current (>= 3 A).** The output is specified at exactly 3.0 A continuous, which sits
  on the brief's own high-current threshold, and the input side draws up to ~2.6 A at low
  line. This is the flag that drives copper sizing (IPC-2152, with the 10-20 C rise the
  brief permits), connector current rating, and the fusing question. Per role rules this is
  NOT guessed: see Q5 (is 3 A the true worst case, or is there a peak/inrush above it),
  Q7 (overcurrent mechanism and whether an input fuse is required) and Q29 (fault behaviour
  the board must survive: sustained short circuit on the output).
- **Undefined fault energy.** The brief does not state whether the input source is current
  limited, so the power available into a fault is unbounded as specified: a 4 A input fuse
  at 18 V still passes ~72 W. Behaviour under a bolted output short, and under a reversed
  or swapped input, must be defined rather than assumed - Q7, Q29, Q30.
- **Switching EMI.** A hard-switching buck is a deliberate broadband noise source. The brief
  imposes layout-level EMI requirements (loop area, SW node away from edges/connectors, no
  plane splits) but names no standard - Q31.

Not applicable (confirmed against the brief):
- No mains voltage anywhere on the board. Maximum potential is 18 V.
- No battery of any chemistry, no charging circuit, no cell balancing.
- No motors, relays, solenoids or other inductive actuator loads driven by this board.
- No node above 30 V under normal operation (18 V max input; switch-node ringing must
  still be kept below the chosen IC's absolute max, which is a design check, not a
  safety-agency flag).
- No intentional RF transmission.

Consequence: no agency-certification path (UL/IEC mains safety, battery transport, RF
type approval) applies to this board. The safety work is entirely thermal, fault-current
and connector-rating engineering.

## 9. Open questions

Each has a recommended default. The orchestrator answers all of them at once as delegate,
per the brief's DECISION POLICY, and each answer becomes a DECISIONS.md line.

1. **Does the +/-2% output window include ripple and load-step transients, or only DC
   accuracy?** Default: +/-2% is the DC setpoint over line, load and temperature; the
   50 mV ripple and the 200 mV load-step excursion are separate, additional allowances.
2. **How is the <50 mV ripple measured?** Default: at the output screw terminal, scope in
   20 MHz bandwidth-limited mode with a short spring ground (the standard method) - so
   high-frequency switching spikes above 20 MHz are excluded from the number.
3. **How fast is the 0-3 A load step?** Default: 2.5 A/us electronic-load slew (a common
   bench setting), applied at 12 V in. A faster step would be dominated by output-cap ESL
   rather than by the control loop.
4. **Is the >88% efficiency measured at the screw terminals (including the reverse-polarity
   FET and terminal resistance) or across the IC only?** Default: terminal to terminal,
   i.e. the reverse-polarity FET loss counts against the budget. This is the conservative
   reading.
5. **Is 3 A the true worst case, or must the board survive brief peaks above it (e.g. a
   capacitive or lamp load at turn-on)?** Default: 3.0 A is the continuous maximum and the
   design target; the IC's own current limit is allowed to be the only headroom above it,
   with the current limit set no lower than 4 A to avoid nuisance foldback.
6. **Any input surge above 18 V (automotive load dump, hot-plug ringing on a long cable)?**
   Default: no formal surge requirement, but select the IC and input caps for a minimum
   28 V rating (>1.5x the 18 V max) so hot-plug ringing on an inductive cable does not
   destroy the part.
7. **Overcurrent protection mechanism, and is an input fuse required?** Default: rely on the
   buck IC's internal cycle-by-cycle current limit with hiccup-mode short-circuit
   protection (auto-recovering), AND fit a slow-blow input fuse or PTC sized ~4 A as a
   fail-safe against a shorted high-side switch, which the IC cannot protect against.
8. **Is the IC's internal thermal shutdown sufficient, or is an independent thermal cutout
   required?** Default: internal TSD is sufficient given the low power and the absence of
   any agency requirement; no separate thermistor or cutout.
9. **Screw terminal part and wire entry direction.** Default: 5.08 mm pitch, 2-pin,
   horizontal (side) wire entry facing outward from the board edge, rated >= 10 A / 300 V,
   accepting 12-24 AWG; choose whichever LCSC-stocked family (KF128/KF301-class or
   equivalent) is in stock in quantity with a verified footprint.
10. **Input and output on opposite board edges, or the same edge?** Default: opposite
    short edges (input left, output right), giving a straight-through power flow, maximum
    separation between the noisy input loop and the output terminal, and no chance of a
    user swapping the two identical connectors... which leads to Q30.
11. **Any indicator LED?** Default: yes, one low-current green LED on VOUT (~1 mA, ~5 mW),
    as an at-a-glance "output is live" indicator. Cost to efficiency at 3 A is negligible
    (0.03%). Say no if the pure-efficiency reading is preferred.
12. **Any power-good (PG) output brought out?** Default: no external PG connector; if the
    chosen IC has a PG pin, bring it to a test pad only.
13. **Test point physical form.** Default: 1.5 mm bare round SMD pads for VIN, SW, FB, EN
    and GND; the VOUT test point paired with a dedicated scope-ground pad at ~5 mm spacing
    so a scope spring ground reaches both (this satisfies the brief's "low-inductance scope
    ground point near the output"). No THT loop test points - they add inductance and
    height and cost a hand-solder step.
14. **Is EN to be user-controllable (jumper/header), or purely an internal UVLO node?**
    Default: internal only - a resistor divider from VIN sets UVLO at approximately 6.5 V
    rising / 6.0 V falling, so the converter refuses to start below the 7 V spec floor, and
    EN is exposed as a test pad only.
15. **Minimum operating ambient?** Default: 0 C operating, with all parts rated -40 C or
    lower so the limit is the specification and not the silicon.
16. **Enclosure: is the 50 C figure free-air ambient or inside a sealed box?** Default:
    open-frame, free-air 50 C, mounted on standoffs with unobstructed convection on both
    faces. If it is ever boxed, the internal air temperature must be re-stated - a sealed
    enclosure would likely break the thermal budget.
17. **May the board use the full 50 x 40 mm, or should it be as small as possible?**
    Default: use the full 50 x 40 mm envelope. Copper area is the free variable that closes
    the thermal case, and the brief caps the size rather than asking for minimum size.
18. **2-layer or 4-layer?** Default: 4-layer. The brief's own layout section demands "an
    uninterrupted ground plane on the layer directly under the switching components", a
    single low-impedance ground reference, and enough copper to sink ~2 W by convection -
    all three are materially easier and lower-risk on 4 layers, and the JLCPCB cost delta
    at prototype quantity is small. Justification to be recorded at P5.
19. **Mounting hole geometry.** Default: 3.2 mm holes, non-plated (NPTH), one at each
    corner inset 3.5 mm from both edges, 6.5 mm diameter copper/mask keepout for an M3
    washer, isolated from GND (no chassis-ground bond, avoiding an uncontrolled ground
    loop through the standoffs).
20. **Maximum component height?** Default: 15 mm above the top surface, which comfortably
    fits a 5.08 mm screw terminal (~10 mm) and any shielded power inductor likely to be
    chosen (<7 mm).
21. **Copper weight?** Default: JLCPCB standard stackup - 1 oz (35 um) outer, 0.5 oz inner
    on 4-layer (the brief explicitly warns to check this). Escalate to 2 oz outer only if
    the IPC-2152 sizing or the junction-temperature calculation fails at 1 oz; record the
    escalation if it happens.
22. **Build quantity?** Default: 5 boards (JLCPCB prototype minimum).
23. **Target unit cost?** Default: no hard cap; keep the BOM under roughly $12/board at
    qty 5 and flag any single line item over ~$3 for a conscious decision.
24. **LCSC stock threshold to call a part "available"?** Default: >= 500 pcs in stock for
    the buck IC, inductor and P-FET; >= 2000 pcs for passives; and no part whose LCSC page
    shows an end-of-life or "last stock" state.
25. **Assembly method, including the two THT screw terminals?** Default: JLCPCB PCBA for
    all SMT parts; the two screw terminals hand-soldered on receipt (avoids JLC's THT
    surcharge on a 5-board run and keeps the connector choice free of JLC's THT part list).
    Both connector footprints must still be documented in the BOM/CPL as DNP-for-assembly.
26. **Single- or double-sided assembly?** Default: single-sided, top only. All active and
    passive parts on top; bottom reserved for ground plane, thermal copper and the test
    pads' ground stitching. This halves assembly cost and keeps the bottom face free to
    conduct heat.
27. **JLCPCB process class?** Default: the standard/economic class (typically 5 mil (0.127
    mm) minimum trace and space, 0.3 mm minimum drill, 0.13 mm annular ring). Nothing in
    this design needs finer, and staying standard keeps cost and yield where they should
    be. Actual limits to be confirmed against JLC's published capability table at P5, not
    from memory.
28. **LCSC Basic vs Extended parts?** Default: prefer Basic/Preferred for R, C, L and the
    LED; accept Extended for the buck IC, the power inductor and the P-channel FET where
    the requirement demands a specific part. Extended parts add a per-line feeder fee -
    acceptable at these quantities.
29. **Required behaviour under a sustained output short circuit?** Default: the board must
    survive indefinitely and recover automatically when the short is removed (hiccup-mode
    current limit), without exceeding component ratings and without the input fuse blowing
    unless a genuine hard failure has occurred.
30. **Required behaviour if the OUTPUT terminal is back-driven, or if input and output
    connectors are swapped by the user (they are identical 2-pin 5.08 mm parts)?**
    Default: no active output reverse-current or back-drive protection is required, but the
    silkscreen must unambiguously mark IN/OUT and polarity on both connectors, and the
    board should not be destroyed by a brief 5 V back-feed into the output. A swapped
    connection driving 12 V into the 5 V output is NOT required to be survivable - it will
    be prevented by labelling. Flag if survivability is actually wanted.
31. **Any EMI standard to meet (CISPR 32 / EN 55032 class B conducted or radiated)?**
    Default: no formal standard and no compliance testing; apply the brief's layout rules
    as best practice, leave the DNP snubber footprint as the mitigation hook, and add no
    input EMI filter beyond the bulk plus ceramic input capacitance already required.
32. **Switching frequency preference?** Default: no hard requirement - choose whatever the
    selected IC family supports in the roughly 400-800 kHz range, trading inductor size
    against switching loss and the >88% efficiency floor. If a specific band must be
    avoided (e.g. AM broadcast, 530-1710 kHz), say so, since that would rule out several
    otherwise-suitable 1 MHz-class parts. Note the requirement interacts with Q31.
33. **Silkscreen content?** Default: board name "sbuck-5v3a", revision "A", date, input and
    output voltage/current markings at each terminal, polarity (+/-) on both connectors,
    pin-1/polarity marks on every polarised part, and every test point labelled. No logo.
