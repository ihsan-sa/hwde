# Interface research: USB-C as a POWER SINK carrying USB-PD (no USB data)

Board: `pd-trigger`. Role: **UFP / power sink only**. The USB-C receptacle carries
VBUS + GND + CC1/CC2. D+/D-, SBU and SuperSpeed pins are unused. Max negotiated
profile 20 V, design current 5 A uniform (requirements.md answers 1 and 2).

Companion machine-readable fragment: `interface-usbc-pd.json`.

Everything below is either quoted from a source (linked in section 9) or computed
from one; computed values say so. Numbers I could not source are called out in
section 10 rather than guessed.

---

## 1. Constraint table (what lands where)

| # | Constraint | Value | Lands in | Enforced by |
|---|---|---|---|---|
| C1 | CC1/CC2 trace class | no impedance control, no length match, no reference corridor | notes only | nothing (by design) |
| C2 | CC net total node capacitance | 200 pF min .. 600 pF max | notes / part selection | manual |
| C3 | Exactly one Rd path per CC line (integrated OR external 5.1k +/-20%, never both) | 5.1 kohm +/-20% | schematic (P4) | ERC/manual |
| C4 | Both CC pins wired straight through, no crossover, no series element | - | schematic (P4) | manual |
| C5 | Receptacle VBUS rating | 5.00 A **collectively** over A4/A9/B4/B9 = 1.25 A/contact | parts (P3) | manual |
| C6 | All four VBUS pins AND all four GND pins ganged | A4+A9+B4+B9 / A1+A12+B1+B12 | schematic (P4) | netlist_audit |
| C7 | VBUS/VOUT copper width at 5 A, dT 20 C | 2.383 mm @ 1 oz, 1.191 mm @ 2 oz | `power[].current_a/dt_c` | check_current (P8) |
| C8 | 5 A forward path stays on ONE layer (else 10 vias per transition) | via_amps default 0.5 A | `power[]` | check_current (P8) |
| C9 | Same-layer clearance on 20 V nets | IPC-2221 needs only 0.10 mm; use 0.3 mm as practice | `voltages[]` + rules_gen | check_creepage no-ops (see 4) |
| C10 | VBUS TVS working voltage | >= 22 V (24 V class), clamp <= 28-34 V | parts (P3) | manual |
| C11 | CC TVS (if fitted) working voltage | >= 20 V, and must keep C2 satisfied | parts (P3) | manual |
| C12 | PTC after the controller tap, Vmax >= 24 V, Ihold >= 5 A | see section 6 | schematic (P4) | manual |
| C13 | Sink bulk capacitance | >= 10 uF for load step, <= 100 uF (cSnkBulkPd) | parts (P3) | check_pdn (P8) |
| C14 | CH224K VDD dropper | 1 kohm, >= 0.28 W at 20 V | parts (P3) | manual + notes |
| C15 | CH224K VBUS sense pin needs its 10 kohm series resistor | pin abs max 13.5 V vs 20 V rail | schematic (P4) | manual |
| C16 | PD-only mode: DP/DM off the connector, shorted at the chip | - | schematic (P4) | manual |
| C17 | No `high_speed` / no `diff_pairs` entries | see section 8 | constraints.json | - |

---

## 2. CC1 / CC2

**Who owns Rd.** The sink controller owns the Rd pull-down and the PD BMC
transceiver. Type-C requires a receptacle sink to advertise Rd on **both** CC1
and CC2 (5.1 kohm +/-20% to GND) because only one CC line is wired through the
cable and the plug orientation is unknown [Renesas, Infineon FAQ].

Part-specific and load-bearing: **WCH's own reference schematics show the CH224K
with CC1/CC2 wired directly to the chip and NO external 5.1 kohm resistors**,
while the CH221K (fig 6.4) and CH224D (fig 6.1) figures DO show 5.1 kohm
pull-downs [CH224 datasheet v1F, section 6]. So Rd is integrated on the CH224K
and external on its siblings. Constraint: **exactly one Rd path per CC line**.
Fitting external 5.1k on a part that already integrates Rd puts ~2.55 kohm on
CC and shifts the source's Rd/Ra detection thresholds. Confirm against the exact
ordering part number at P3.

**Trace class - be honest: there is nothing to control here.** PD communicates
BMC (biphase mark coding) on CC at 300 kbit/s half-duplex, with a specified
edge rate of 300 ns (10-90%) into a 520 pF load [ST TA0357; TI TUSB422 /
TPS25751 datasheets]. Critical length for transmission-line behaviour is roughly
t_rise * v_prop / 6 = 300 ns * 150 mm/ns / 6 ~= 7500 mm. The whole board is
~40 mm. CC is electrically DC at this scale:

- no controlled impedance (the 2-layer stackup has no reference plane anyway -
  `stackups.yaml` JLC2313_1.6 ships `controlled_impedance: []`),
- no length matching, no return-path corridor, no `high_speed` entry,
- just keep the routes short and direct, and do not neck them below the fab
  minimum (0.127 mm at 1 oz / 0.1524 mm at 2 oz per `jlc_capabilities.yaml`).
  0.25-0.3 mm is a sensible practical width.

**What the CONNECTOR needs.**

- Receptacle CC1 = pin **A5**, CC2 = pin **B5** [Semtech SI21-03 Table 1].
- Wire A5 -> controller CC1 and B5 -> controller CC2, **straight through, no
  crossover, no swap**. Orientation independence comes from the controller
  having two CC pins, not from board-level swapping. Crossing them is
  functionally symmetric for plain PD but breaks part features that name a
  specific pin - e.g. the CH224 E-Mark emulation is specified on CC2 only
  [CH224 datasheet 5.4].
- **No series elements on CC** (a series R adds directly to Rd, whose budget is
  only +/-20% = +/-1.02 kohm).
- The **capacitance budget is the real electrical constraint on CC**: USB PD
  spec section 5.8.6 puts the CC receiver capacitance at **200 pF min to 600 pF
  max** [onsemi AN-5086]. Note 200 pF is a *minimum*. Anything added to the node
  (a CC TVS, a filter cap) counts toward the 600 pF ceiling; some designs
  deliberately add ~390 pF to meet the floor. Do not add CC caps blind - check
  the controller's own pin capacitance first.
- CC pins can see up to VBUS (20 V) if a conductive particle or a partial insert
  shorts VBUS to CC/SBU - the pins are physically adjacent in the connector.
  Semtech therefore specifies a CC TVS with **>= 20 V working voltage** (their
  uClamp2411ZA: bidirectional, 24 V operating, 1 ohm dynamic resistance, 0201)
  [Semtech SI21-03]. This is optional for a bench tool but cheap insurance for
  the one part on the board that is not replaceable by hand.

**E-mark / VCONN, board side:** a *sink with a receptacle* neither sources nor
needs VCONN, and needs no e-marker of its own - the e-marker lives in the user's
cable. (The CH224 analog-E-Mark function with a 1 kohm on CC2 applies only to a
captive **male**-plug design [CH224 datasheet 5.4]; not our case.)

---

## 3. VBUS: 100 W, the receptacle, and pin ganging

**What makes a receptacle 5 A capable.** Not a spec class - a **manufacturer
nameplate rating verified by a temperature-rise test**. Two GCT product
specifications read identically:

> "Current rating: 5.00A collectively for VBUS pins (i.e. pins A4, A9, B4, and
> B9); 6.25A collectively for GND pins (i.e. pins A1, A12, B1, and B12); 1.25A
> for VCONN (i.e. A5/B5); 0.25A per pin, for all other pins."
> - GCT USB4085 rev B section 4.1 (24-pin THT), identical wording in GCT USB4105
>   rev A1 section 4.1 (16-pin USB2.0 SMT)

and the qualifying test:

> "6.1.5 Contact current rating: A current of 5 A shall be applied collectively
> to VBUS pins ... terminated through the corresponding GND pins ... The
> temperature rise shall not exceed 30 deg C at the outside surface of the shell."

So: **5 A is a collective rating across all four VBUS contacts = 1.25 A per
contact**, and it only holds if all four are actually landed and connected. A
part whose datasheet says 3.00 A collectively is a 3 A receptacle and is out.

Two traps worth carrying into P3:

1. **Voltage rating differs between otherwise-identical parts.** USB4085 is
   rated 48 V DC / 240 W; USB4105 is rated **20 V DC**. A 20 V nameplate is
   exactly our maximum with zero margin (a 20 V PDO is 20 V +/-5% = up to 21 V).
   Prefer a part rated >= 24 V, or accept the 20 V part knowingly.
2. **Power-only 6-pin receptacles** gang fewer contacts. If the part does not
   list all four VBUS pins in its 5 A clause, its per-contact current at 5 A is
   2.5 A, not 1.25 A. Check the clause, not the marketing line.

**Ganging (C6).** Tie A4+A9+B4+B9 into one VBUS net and A1+A12+B1+B12 into GND
at the pad, in copper, not through a neck. Losing one VBUS contact raises the
remaining three to 1.67 A each.

**Connector loss at 5 A (computed).** Contact resistance is 40 mohm max initial
per contact [GCT 6.1.1]; four in parallel = 10 mohm. VBUS drop = 50 mV, 0.25 W;
same again on GND. ~0.5 W dissipated in the mated connector at 5 A - this is
what the 30 C shell-rise test is measuring, and it is why the receptacle wants
copper on both sides of its pads rather than a thermally isolated island.

**5 A requires an e-marked CABLE - board side nothing.** A USB-C cable rated
above 3 A must carry an e-marker; a source queries the cable and will not offer
a >3 A PDO without one, falling back to 3 A / 60 W at 20 V [Renesas; USB-IF
requirement, widely restated]. Sources supporting >3 A must also be able to
distinguish Ra (800-1200 ohm, in the cable) from Rd. **Nothing on this board can
change that** - but it belongs in the user documentation, because a user with a
generic 3 A cable will silently get 60 W and blame the board. Recommend a silk
or doc line: "20 V @ 5 A requires a 5 A e-marked cable and a 100 W source."

**Board copper for 5 A (computed with the pipeline's own checker,
`check_current.required_width_mm`, IPC-2152 at dT):**

| dT | 1 oz (0.035 mm) | 2 oz (0.070 mm) |
|---|---|---|
| 10 C | 3.500 mm | 1.750 mm |
| **20 C** | **2.383 mm** | **1.191 mm** |
| 30 C | 1.871 mm | 0.935 mm |

Recommendation: **dt_c = 20**. Rationale: bench ambient assumed 0-40 C
(requirements section 4), so a 20 C rise puts copper at ~60 C worst case - well
inside FR-4 and consistent with the connector's own 30 C-rise qualification.
dt_c = 10 demands 3.5 mm at 1 oz, which does not fit sensibly on a 40x25 mm
board; dt_c = 30 is available if placement gets tight, at 1.871 mm.

Route the 5 A path as a **pour/wide track on F.Cu only** - see C8: check_current
requires ceil(5.0 / 0.5) = **10 vias** at any layer transition on a 5 A net. A
single-layer forward path has no transitions and costs nothing. (The GND return
is a pour and does need a via field at the connector - that is the
power-architect's entry, not this fragment's; flagged in section 10.)

Trace loss (computed): 25 mm of 2.383 mm-wide 1 oz copper = 5.2 mohm = 26 mV
and 0.13 W at 5 A. Negligible at 20 V, ~0.5% at 5 V.

---

## 4. 20 V on the board: creepage and spacing

**check_creepage will not engage, and that is correct.** `check_creepage.py`
only examines net pairs whose voltage difference **exceeds 30 V**
(`HV_THRESHOLD_V = 30.0`). With VBUS/VOUT at 20 V and everything else at 0 V,
the largest pair difference is 20 V, so zero pairs are checked and the report
comes back clean-and-empty. The `voltages` entries are still emitted because:

- they document the rail voltage for humans and for `check_creepage`'s report,
- they make the check engage **automatically** if the board is ever revised to
  EPR (28 / 36 / 48 V), where 48 V vs GND would cross the threshold,
- listing them is free: verified in the source, `check_creepage.run()` SKIPS a
  listed net that is absent from the board (`skipped_absent_nets`) rather than
  failing. (`check_current` does NOT - see section 10.)

**Spacing good practice at 20 V / 5 A.** IPC-2221 Table 6-1 B2 (external,
uncoated) for 0-30 V is only **0.10 mm** - below JLC's manufacturing minimum of
0.127 mm (1 oz) / 0.1524 mm (2 oz) [`jlc_capabilities.yaml`], so the fab limit
dominates and the electrical requirement is not binding. Recommendation anyway:
**0.3 mm minimum clearance from the 20 V power nets to everything else**, which
costs nothing on a board this sparse and buys margin against flux residue,
bench dust, and a slipped probe on an exposed board. This is a `rules_gen`
clearance setting, not a constraints.json key.

---

## 5. `power` entries

Three entries, in the JSON fragment. Net names are **provisional** - see the
hard warning in section 10.

1. **`VBUS`** - connector VBUS pins -> TVS -> bulk -> controller taps -> PTC in.
   5.0 A, dt_c 20. Carries decoupling (bulk lives here, see section 6), so it is
   NOT marked `"pdn": false`.
2. **`VOUT`** - PTC out -> screw terminal + aux header. 5.0 A, dt_c 20, marked
   **`"pdn": false`**: it is declared purely so `rules_gen` sizes its copper and
   `check_current` checks it; its reservoir is upstream of the PTC by design, so
   `check_pdn` would otherwise warn about a missing bulk cap on a rail that is
   deliberately not decoupled locally.
3. **`+3V3`** - the CH224-class controller's own VDD tap. **0.02 A**, dt_c 20,
   `pdn` left true so `check_pdn` enforces the datasheet-mandated 1 uF.

### The VDD tap is not a trivial stub (C14)

The CH224K has **no separate supply pin**. Pin 1 VDD is described as "power
working power input, external 1uF decoupling capacitor, **series resistance to
VBUS**", and the reference schematics feed it from the VBUS rail through
**1 kohm** with **1 uF** to GND [CH224 datasheet v1F sections 4.3, 6.1-6.3].
Section 7.5 makes the topology explicit: VDD is a **shunt** ("parallel") regulator,
3.24 / 3.30 / 3.36 V, with a **parallel sink current capability of 0 .. 30 mA**.
Absolute max VDD is 3.0-3.6 V (7.2), and total chip dissipation is capped at
400 mW.

Consequences (computed from those numbers):

- Dropper current at 20 V: (20 - 3.3) / 1 kohm = **16.7 mA**; at 22 V, 18.7 mA -
  both inside the 30 mA shunt capability.
- **Minimum dropper resistance**: R >= (22 - 3.24) / 0.030 = **625 ohm**. Anything
  below ~680 ohm overruns the shunt at the top of the CH224's 4-22 V input range.
- **Maximum dropper resistance** is bounded by the chip having to run at the
  *pre-negotiation* 5 V default: 1 kohm delivers only (5 - 3.3)/1k = 1.7 mA
  there. WCH's choice of 1 kohm therefore implies IDD < ~1.7 mA and leaves
  little room to raise it. **Use 1 kohm; do not "optimize" this resistor.**
- **Dissipation in that resistor at 20 V: (16.7 mA)^2 * 1 kohm = 0.28 W**
  (0.35 W at 22 V). This is the finding most 5 V/12 V CH224 reference layouts
  never hit. An 0402/0603 (0.1 W) will cook. Use **2x 510 ohm in series**
  (0.14 W each) or a single 1 kohm in 2010/2512. It is also a continuous ~0.3 W
  heat source: keep it off the CH224K's exposed-pad thermal island and away from
  the connector.
- Suggested (not emitted here - needs a refdes): a `thermal` entry
  `{"ref": "R_VDD", "power_w": 0.3, "net": "GND", "dt_c": 40}` once the
  schematic assigns designators.

**Do not confuse VDD with a usable 3.3 V rail.** `+3V3` here is a shunt node
whose entire budget is the dropper current minus IDD - about 15 mA at 20 V but
effectively **zero at 5 V**. Nothing else (LEDs, pull-ups beyond the CFG
network) may hang off it. If the design needs a real logic rail, that is a
separate regulator and a separate power-architect entry.

### VBUS sense pin (C15)

Pin 8 VBUS is an **analog voltage-detection input**, abs max **13.5 V**
(VIOHV, section 7.2) on a rail that reaches 21 V. The datasheet says it
"requires series resistor to external input VBUS"; the reference circuit uses
**10 kohm**. That resistor is mandatory, not optional. The datasheet does permit
the pin to be NC in PD-only mode (5.5), but keeping the sense connected is what
lets the controller do output-voltage detection and drive PG - which
requirements answer 6 depends on for the "profile achieved vs fallback"
indication. Keep it, with the 10 kohm.

### Placement note that keeps check_current quiet

Both taps (1 kohm to VDD, 10 kohm to sense) branch off the 5 A VBUS net.
`check_current` checks **every track segment** of a net against the full budget,
so a thin VBUS spur to those resistor pads will be flagged as an undersized
2.383 mm-wide track carrying 20 mA. Two clean fixes:

- **Preferred:** place the tap resistors so their VBUS-side pads land *inside*
  the VBUS pour. Pads in a pour are not tracks; no violation, no override.
- **Fallback:** add a `power[].overrides` region once coordinates exist (P5+):
  `{"near": [x, y], "radius_mm": 3, "current_a": 0.02}`.

---

## 6. Protection

Ordering, connector to terminal:

```
Rcpt VBUS (A4,A9,B4,B9) --+-- TVS ->GND --+-- bulk 22uF + 100nF --+-- 1k  -> VDD (+1uF)
                          |               |                      +-- 10k -> VBUS sense
                          |               |
                          +---------------+-- PTC --+-- screw terminal (VOUT)
                                                    +-- aux header (low-current)
                                                    +-- 100nF
```

**TVS (C10).** Unidirectional, on VBUS, at the connector. Required working
(standoff) voltage is **>= 22 V**: "protecting VBus pin requires a TVS diode with
a minimum 22V working voltage" [Semtech SI21-03], echoed by the common
"VRWM >= 24 V for a 20 V charging port" guidance. Semtech's own example part is
**TDS2221PW: 22 V operating, 23 V min breakdown, 28 V max clamping, 22 A peak
pulse (8/20 us), DFN 1.6 x 1.0 mm**, and other sources put the ceiling for
clamping voltage around 34 V so as not to exceed the downstream OVP part.
Low capacitance is explicitly NOT a consideration on VBUS [Semtech].

Honest tension worth stating: a 24 V-standoff SMAJ/SMBJ-class TVS clamps around
**38-39 V**, which is above both the 34 V guidance and the CH224's stated 4-22 V
operating range. A part in the TDS2221PW class (28 V clamp) is materially better
here. The CH224K's own pin protection is the reference circuit's **series 1 kohm
and 10 kohm** - which is the second reason not to omit them.

Why the TVS is not optional: a published teardown of exactly this class of board
(CH224 trigger, no TVS, no fuse) reports the chip **failing at 20 V under load,
attributed to an inductive spike through the USB cable** [beyondlogic]. Cable
inductance x a 5 A interrupt is the fault we are protecting against, and the
2 m of cable is on the source side - so the TVS belongs **at the connector**,
before the PTC, with a short wide return and multiple GND vias.

Optionally add a second TVS on VOUT: the output is a bench terminal that will
meet inductive loads and hot-unplugs from the *load* side. Not mandatory.

**PTC placement - AFTER the controller tap (C12).** Reasoning, not preference:

- The controller must keep its VBUS reference and its supply at the *connector*
  node. Putting the PTC upstream of the tap means an output fault sags VDD, the
  contract drops, the source returns to vSafe5V, the PTC cools, and the board
  hiccups in a loop - and the sense pin no longer reads what the connector sees.
- With the PTC downstream, a fault at the terminal trips the PTC while the
  controller stays alive and can *indicate* the condition (requirements answer 6).
- The tap draws ~17 mA, so it costs nothing against the PTC's hold budget either
  way; there is no counter-argument on the current side.
- Corollary: **bulk capacitance goes on the connector side, before the PTC.**
  On an output short, upstream bulk dumps *through* the PTC (which is rated for
  it); downstream bulk would dump straight into the fault with no protection.

**PTC sizing - and a sourcing conflict the architect must see.** For a 20 V rail
the PTC needs Vmax >= 24 V, and requirements answer 1 commits to a uniform 5 A,
so Ihold >= 5 A. Mainstream **SMD** PPTC series do not reach that combination:
Littelfuse 2920L is 0.30-3.00 A at 60 V; 1812L is 0.10-2.60 A at 30 V. The
usable parts are **radial through-hole**: e.g. Littelfuse **RUEF500** - 5 A hold
/ 10 A trip / **30 VDC** / 100 A Imax / 3 W / ~0.01 ohm - but it is a ~11 x 24 mm
radial disc, which presses hard on the ~40 x 25 mm size target (requirements
open question 5, answered "soft, up to ~20% over"). Options for the architect:

- (a) radial PPTC (RUEF500 class) - meets the spec, hand-soldered like the screw
  terminal already is, costs board area;
- (b) an eFuse / OVP+OCP load switch instead of a PPTC - smaller, adds a part
  class and a gate-drive rail, and would also satisfy requirements answer 6
  option (b) if that is ever revisited;
- (c) derate the PTC below 5 A - contradicts answer 1, not recommended.

Loss at 5 A through RUEF500: 0.01 ohm -> 50 mV / 0.25 W nominal, up to ~0.7 W at
post-trip resistance. Add that to the ~0.5 W in the connector when budgeting.

**Inrush / bulk vs the PD spec (C13).** The binding number is **cSnkBulkPd =
100 uF**, the maximum bulk capacitance allowed on a sink's VBUS once a PD
contract is in place; above that, VBUS surge-current limiting is required
[TI TPS25730 / TPS25751 datasheets, citing the USB PD spec]. (The familiar 10 uF
figure is the *USB 2.0* attach limit, i.e. 50 uC of inrush, not a PD number.)
Recommendation: **10-22 uF total** on the connector-side VBUS plus 100 nF at
each node. Rationale, computed: a PD source's positive slew is capped at
**vSrcSlewPos = 30 mV/us** [USB PD spec, per Allion / Microchip AN3265], so
22 uF draws C*dV/dt = 22 uF * 30 000 V/s = **0.66 A** of charging current during
a 5 V -> 20 V transition - comfortably inside both the contract and the PTC hold
current, while 100 uF would draw 3 A and eat most of a 3 A contract. Small is
correct here; this is a pass-through board with no converter to hold up.

---

## 7. Not needed on this connector

- **D+/D- (A6/A7/B6/B7): leave unconnected at the receptacle.** For PD-only
  operation the CH224 datasheet (5.5) is explicit: disconnect DP/DM from the
  Type-C interface and **short DP and DM together at the chip**. (This disables
  the BC1.2 / legacy fast-charge protocols we do not want on a PD trigger.)
- **SBU1/SBU2 (A8/B8): unconnected.** No alt mode.
- **SuperSpeed pairs (A2/A3/A10/A11/B2/B3/B10/B11): unconnected** - and prefer a
  16-pin or power-only receptacle that does not have them, which also removes
  eight fine-pitch pads from a 5 A board.
- **Shell / shield:** tie to GND directly for a bench tool with no chassis and
  no enclosure. (The 1 Mohm || 4.7 nF hybrid tie exists for chassis-ground
  isolation cases; not this board.)

---

## 8. `high_speed`: intentionally absent

No key is emitted, and none should be added, because there is no high-speed net
on this board:

- there are no data pairs at all (section 7),
- CC is 300 kbit/s BMC with 300 ns edges - three to four orders of magnitude
  slower than anything needing a return-path corridor (section 2 computes the
  critical length at ~7.5 m),
- the 2-layer stackup has no reference plane to build a corridor against.

`check_return_path` and `rules_gen` impedance rules therefore no-op cleanly.

**Trap for the merged file (C17):** `diff_pairs` **omitted** means
`check_diffpair` **auto-discovers** pairs by name suffix, including `DP`/`DM`.
If the schematic ends up with two distinct nets named `/DP` and `/DM` joined at
the chip (section 7), the checker will discover them as a differential pair and
report skew/gap violations on what is deliberately a shorted stub. The architect
should either give that node a single net name with no DP/DM token, or set an
**explicit `"diff_pairs": []`** in the merged constraints.json to disable the
check. This fragment cannot do it (an explicit empty list here would be
overwritten or, worse, silently disable the check for the whole board without
the architect having decided).

---

## 9. Sources

Primary (quoted above):

- GCT **USB4085** rev B (dated 05/04/23) USB Type-C receptacle, through-hole,
  product specification - ratings 4.1-4.4, contact resistance 6.1.1,
  current-rating test 6.1.5: https://gct.co/files/specs/usb4085-spec.pdf
- GCT **USB4105** rev A1 (dated 24/10/19) USB Type-C receptacle for USB2.0, SMT -
  ratings 4.1-4.3 (note: 20 V DC voltage rating):
  https://www.farnell.com/datasheets/3187780.pdf
- Semtech **SI21-03** "ESD Protection of USB Type-C Interfaces" rev 2024-05-27 -
  pin table, VBUS TVS >= 22 V working voltage, TDS2221PW 22/23/28 V / 22 A,
  CC+SBU exposed to 20 V, uClamp2411ZA:
  https://www.semtech.com/uploads/design-support/TVS_App_Notes-SI21-03-ESD_Protection_of_USB_Type-C_Interfaces_New_Template.pdf
- WCH **CH224 datasheet v1F** (machine-translated) - pin functions 4.3, CFG
  tables 5.2, E-Mark 5.4, PD-only mode 5.5, reference schematics 6.1-6.4,
  absolute maximums 7.2, electrical parameters 7.5:
  https://components101.com/sites/default/files/component_datasheet/WCH_CH224K_ENG.pdf
- onsemi **AN-5086** "USB Type-C, CC Pin Design Considerations" - CC receiver
  capacitance 200-600 pF per USB PD spec 5.8.6 (retrieved via search; direct
  fetch 403s): https://www.onsemi.com/pub/Collateral/AN-5086-D.PDF
- TI **TPS25730** / **TPS25751** datasheets - cSnkBulkPd = 100 uF max sink bulk
  after contract: https://www.ti.com/lit/ds/symlink/tps25730.pdf
- TI **TUSB422** datasheet - BMC tRise/tFall 300 ns into 520 pF:
  https://www.ti.com/lit/gpn/TUSB422
- ST **TA0357** "Overview of USB Type-C and Power Delivery" - CC half-duplex
  300 kbit/s BMC, Rd 5.1 kohm +/-20% on both CC pins:
  https://www.st.com/resource/en/technical_article/ta0357-overview-of-usb-typec-and-power-delivery-technologies-stmicroelectronics.pdf
- Renesas "USB Power Delivery: The Technology 2" - sink Rd on CC1 and CC2, Ra
  800-1200 ohm, >3 A / EPR sources must supply VCONN:
  https://www.renesas.com/en/support/engineer-school/usb-power-delivery-03
- beyondlogic "Review: USB-C Power Delivery Trigger Board (CH224)" - failure at
  20 V under load attributed to a cable inductive spike on a board with no TVS
  or fuse; CFG pull-up values:
  https://www.beyondlogic.org/review-usb-c-power-delivery-trigger-board-ch224/
- Allion Labs "VBus Slew Rate Testing" / Microchip **AN3265** - vSrcSlewPos
  30 mV/us maximum positive VBUS slew:
  https://www.allion.com/tech_syst_usbc_slew_rate/
- Littelfuse PPTC selection data - 2920L 0.30-3.00 A / 60 V, 1812L
  0.10-2.60 A / 30 V, RUEF500 5 A / 10 A trip / 30 V / 100 A:
  https://www.littelfuse.com/products/fuses-overcurrent-protection/polyswitch-resettable-pptc-devices
  https://www.newark.com/littelfuse/ruef500/fuse-ptc-reset-30v-5a-radial/dp/04H8001

In-repo (used for the numbers that land in constraints.json):

- `.claude/skills/ai-ee/scripts/check_current.py` - IPC-2152 table and
  `required_width_mm()`; the width table in section 3 was produced by running it.
- `.claude/skills/ai-ee/scripts/check_creepage.py` - `HV_THRESHOLD_V = 30.0`,
  absent-net skip behaviour.
- `.claude/skills/ai-ee/scripts/check_pdn.py` - bulk >= 1 uF rule behind `pdn`.
- `.claude/skills/ai-ee/reference/jlc_capabilities.yaml` - `2layer_1oz` /
  `2layer_2oz` minimums.
- `.claude/skills/ai-ee/reference/stackups.yaml` - JLC2313_1.6 (1 oz,
  `controlled_impedance: []`).
- `C:/dev/ai-library/usb-pd-trigger-ics/` - prior CH224K/HUSB238/AP33772 pull.

---

## 10. Open items and warnings for the architect

1. **Net names are provisional and `check_current` is not forgiving.**
   `check_current.check_net()` raises on a `power` net absent from the board
   (`power net 'X' not on board`) -> **exit 2**, which gates P8. `VBUS`, `VOUT`
   and `+3V3` must be reconciled with the final netlist before P5.
   `check_creepage` is safe (it skips absent nets).
2. **`VOUT` overlaps the power-architect's fragment.** The post-PTC rail is
   emitted here at 5 A because the interface owns the current number, but the
   architect must de-duplicate rather than merge two `power` entries for the
   same net.
3. **`GND` is deliberately NOT in this fragment.** Listing GND at 5 A would make
   `check_current` demand 10 vias in *every* GND via cluster on the board, which
   fails everywhere. If GND is budgeted, it needs `overrides` regions or a
   different treatment - power-architect's call.
4. **Copper weight is unresolved and `stackups.yaml` cannot express 2 oz.**
   `jlc_capabilities.yaml` has a `2layer_2oz` DFM profile, but `stackups.yaml`
   has **no 2-layer 2 oz stackup** - board_init will write 1 oz and
   `check_current` (which reads copper thickness from the board stackup) will
   compute against 0.035 mm. So choosing 2 oz requires adding a stackup entry
   first. Recommendation: **1 oz + dt_c 20 (2.383 mm)** unless placement proves
   it does not fit, then 2 oz + a new stackup entry.
5. **dt_c = 20 is my recommendation, not a derived requirement.** It follows from
   the assumed 0-40 C bench ambient (requirements section 4, itself an ASSUMED).
   If the architect wants more margin, dt_c 10 costs 3.5 mm at 1 oz.
6. **PTC vs the size target (section 6).** A 5 A / >=24 V PPTC is a radial
   through-hole part in the RUEF500 class. Requirements answer 2 committed to a
   resettable PTC and answer 5 allows ~20% over on size - but the architect
   should confirm that trade explicitly rather than discovering it at placement.
   An eFuse is the smaller alternative if the PTC commitment can be revisited.
7. **CH224K CC pin absolute maximum is not legible** in the machine-translated
   datasheet (the VIOCC max cell OCRs as "s"; the sibling CH224D row reads 20 V).
   Verify at P3 before deciding whether the CC TVS (C11) is needed.
8. **Rd integration is part-specific** (section 2). If the architect picks
   HUSB238 or AP33772 instead of a CH224, re-check whether external 5.1 kohm
   pull-downs are required - and if the part changes, the whole of section 5
   (VDD dropper, sense resistor, DP/DM handling) changes with it.
9. **Placement hint not emitted as a key** (this fragment writes only
   `power` / `voltages` / `notes`). The receptacle is an edge part; suggested
   entry for the merged file:
   `"placement": {"edges": [{"ref": "J1", "edge": "left", "pos": 0.5}]}` with
   the screw terminal on the opposite edge, so the 5 A path is one straight
   short run and the two hot connectors are not adjacent.
10. **User documentation item:** 20 V @ 5 A needs a 5 A e-marked cable AND a
    source advertising a 20 V/5 A PDO. Neither is in the board's control, and a
    3 A cable silently caps the board at 60 W.
