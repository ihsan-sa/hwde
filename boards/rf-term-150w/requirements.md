# requirements.md - rf-term-150w

Single-port 50 ohm / 150 W CW RF termination (dummy load head), DC - 25 MHz.

Source: `brief/user-brief.md` (user's words, verbatim) + `brief/brief.md` (orchestrator standing
assumptions A1-A9). The user instructed: **do not ask clarifying questions - assume and record.**
Every gap is therefore closed inline as `ASSUMED:` and section 9 is `none`.

**A1-A9 are decided answers, not proposals.** They are reproduced in section 11 for traceability
and must all appear in the final README.

---

## 1. Function

A passive, single-port 50 ohm RF termination head. One SMA female jack accepts up to 150 W of
continuous-wave RF power from DC to 25 MHz over a standard male-terminated coax cable and
dissipates all of it as heat in a bolt-down termination element. The board itself is the RF
launch and the mechanical interface only: it carries the connector, the resistive element's
electrical connection, and one operator-adjustable reactance null. It is NOT in the thermal
path - the termination element bolts through its own flange directly to an external heatsink or
coldplate that the user supplies and that is out of scope for this design (A4). There is no
active circuitry, no DC supply, no control, no telemetry, and no signal path other than the
single RF port.

Design point (A1): Fc = 25 MHz taken as worst case (highest residual-reactance mismatch);
the DC-25 MHz band means every frequency below 25 MHz is easier. Duty is CW / 100% (A2).

### Derived electrical operating point (arithmetic, stated per assignment)

At 150 W into 50 ohm:

| Quantity | Formula | Value |
|---|---|---|
| Port voltage, rms | V = sqrt(P*R) = sqrt(150 * 50) = sqrt(7500) | **86.6 Vrms** |
| Port voltage, peak | V * sqrt(2) | **122.5 Vpeak** |
| Port voltage, pk-pk | 2 * Vpeak | **244.9 Vpp** |
| Port current, rms | I = sqrt(P/R) = sqrt(3) | **1.732 Arms** |
| Port current, peak | I * sqrt(2) | **2.449 Apeak** |

Consequences that bind every later phase:

- **Any component at the port node sees 86.6 Vrms / 122.5 Vpeak / 244.9 Vpp continuously.**
  That includes the adjustment element of A6. A 100 V-rated trimmer capacitor is DISQUALIFIED.
  Minimum acceptable rating: **>= 250 V working**, and the part must be rated for continuous RF
  (not just DC) at 25 MHz. See section 8 flag F1.
- Current is 1.732 Arms - **below the 3 A high-current threshold**, so the high-current
  compliance flag does NOT apply (section 8). Conductor sizing is driven by the voltage/clearance
  case and by skin effect at 25 MHz (skin depth in Cu at 25 MHz = 13.1 um; 1 oz = 35 um is
  ~2.7 skin depths), not by DC ampacity.
- **Electrically small board.** Free-space wavelength at 25 MHz is 12 m; in FR4 microstrip
  (eps_eff ~ 3.3) it is ~6.6 m. The 30 mm outline is ~0.005 lambda. Transmission-line behaviour is
  negligible and the design is purely lumped. This is why the brief's "no controlled-impedance
  service" constraint costs nothing - it is not a risk. Record it; do not spend budget on it.

### Derived match budget (arithmetic)

| Spec | Reflection coefficient | VSWR | Max residual series reactance |
|---|---|---|---|
| RL >= 26 dB at 25 MHz | \|G\| <= 10^(-26/20) = **0.0501** | <= **1.106** | \|X\| <= **5.0 ohm** = 31.9 nH at 25 MHz |
| RL >= 20 dB, 22.5-27.5 MHz | \|G\| <= **0.100** | <= **1.222** | \|X\| <= **10.05 ohm** = 71.1 nH at 22.5 MHz / 58.2 nH at 27.5 MHz |

Derivation: for Z = R + jX with R = 50, \|G\| = X / sqrt(100^2 + X^2), so \|G\| = 0.0501 -> X = 5.02 ohm.
The +/-2% DC resistance tolerance alone costs \|G\| = 1/101 = 0.0099 (RL 40 dB); taken in quadrature
it leaves 4.92 ohm of reactive budget instead of 5.02 - i.e. **~0.1 dB**. Resistance tolerance is
NOT the binding constraint; **residual series inductance is**. The whole point of the adjustment
element is to cancel it.

**Post-tune residual series inductance must land under ~32 nH at 25 MHz.** For scale: ~20 nH per
25 mm of thin wire/lead. The mechanical layout of the launch is therefore the primary performance
lever, and the trimmer only has to absorb the leftovers.

## 2. Interfaces

| # | Interface | Direction | Standard / detail | Connector |
|---|---|---|---|---|
| I1 | RF port | in (absorbs) | 50 ohm nominal, DC - 25 MHz, up to 150 W CW. 86.6 Vrms / 1.732 Arms. DC-continuous to ground through the termination element (the "DC resistance 50 ohm +/-2%" spec is measured here). | **SMA female (jack)**, stated in brief; mates a standard SMA male cable end |
| I2 | Tuning access | mechanical | Operator-adjustable reactance null, reachable by a hand tuning tool **from the top, with the board bolted down and the SMA cable mated** - no desoldering, no unbolting (A6, brief). | trimmer screw / slot |
| I3 | Thermal / mechanical ground | mechanical | Termination element flange bolts DIRECTLY to the user's heatsink or coldplate through its own flange holes (A4). PCB sits on the same surface, not in the thermal path. | user-supplied fasteners, out of scope |

Notes binding the interfaces:

- **This is the only electrical interface on the board.** No DC input, no bias tee, no monitor/
  detector tap, no LEDs, no test points are called for. `ASSUMED:` none wanted - the brief's
  <= 4 BOM lines / <= 6 placements budget forbids scope creep anyway.
- `ASSUMED:` **RF ground reference is the SMA jack body plus the ground pour**, tied to the
  termination element's cold end. No separate ground lug or chassis screw is specified. Bonding
  to the heatsink happens incidentally through the resistor flange and any mounting hardware.
- `ASSUMED:` **SMA jack is a through-hole, PCB-mount part** (edge-launch or vertical), hand-
  solderable per A5. Exact style (edge vs vertical vs 4-hole flange) is left to P1/P2 parts
  selection; the binding constraint is that the ground return around the launch be short and
  wide, since launch inductance eats the 32 nH budget of section 1.
- **SMA power handling check (record, do not re-open):** SMA is rated ~335 Vrms breakdown; at
  86.6 Vrms it has ~3.9x voltage margin, and at 25 MHz there is no meaningful connector loss.
  SMA is electrically adequate for 150 W CW here. The real SMA caveat is mechanical - mating-cycle
  wear and centre-pin heating under repeated hot connects - which is a usage note for the README,
  not a design change (the user specified SMA).
- **No isolation, no protection.** An open or shorted port, or drive above 150 W, is outside the
  design envelope; nothing on the board detects or survives it. README must say so.

## 3. Power

**There is no DC supply and there are no power rails on this board.** It is fully passive.

The only "power" is the RF drive absorbed at I1:

| Param | Value | Status |
|---|---|---|
| RF input power | 150 W **CW, 100% duty, continuous** | A2 (user left duty blank; CW is the thermal worst case - any pulsed spec is strictly easier) |
| Frequency range | DC - 25 MHz; design point 25 MHz | A1 |
| Port voltage / current | 86.6 Vrms / 1.732 Arms (section 1) | derived |
| Power dissipated on-board | ~150 W, essentially all of it in the termination element | derived |
| Power dissipated in the PCB | intended ~0 W. No heat is intentionally conducted through FR4 (A4) | A4 |
| Battery / charging | **none** | N/A |
| Mains | **none** | N/A |

Secondary dissipation to budget at P2/P3 (small but not zero):

- The adjustment element carries RF current at the port node. For a shunt trimmer of value C,
  I = V * 2*pi*f*C; e.g. 10 pF at 25 MHz and 86.6 Vrms -> 0.136 Arms, and with Q = 200
  (Xc = 637 ohm, ESR = 3.2 ohm) that is ~60 mW. Small - but it means the trimmer's **voltage**
  rating, not its power rating, is the gate. Re-check against the actual chosen part at P2.
- Connector and solder-joint I^2R at 1.73 Arms is negligible (<< 1 W) but the joints must not be
  the mechanical support for a heavy flange part.

### Thermal requirement derived from the derating curve (drives part selection at P1)

The brief's README deliverable demands the required heatsink thermal resistance computed **from
the actual datasheet derating curve**. The arithmetic and its consequence are a requirement, not
an implementation detail, because it determines whether a candidate part is admissible at all:

    T_flange_allowed = T_max - (P_op / P_rated) * (T_max - T_ref)
    Rth_sink_max     = (T_flange_allowed - T_ambient) / P_op        [includes the interface]

With the **generic** flange-resistor derating curve (`ASSUMED:` P_rated at T_ref = 25 C flange,
derating linearly to zero at T_max = 150 C), T_ambient = 25 C (A3), P_op = 150 W:

| Part's rated power | Allowed flange temp at 150 W | Max total Rth (sink + interface) |
|---|---|---|
| 150 W | 25 C | **0.00 C/W - IMPOSSIBLE** |
| 250 W | 75 C | 0.333 C/W |
| 300 W | 87.5 C | 0.417 C/W |
| 400 W | 103.1 C | 0.521 C/W |

**Binding conclusion: a part rated exactly 150 W cannot dissipate 150 W with ANY finite heatsink
at 25 C ambient.** The termination element must be rated **>= 250 W** at its datasheet reference
flange temperature (or carry an equivalent curve that leaves a non-zero allowed flange rise at
150 W). P1 MUST re-derive this table from the real datasheet curve of the part actually chosen
and put the result in the README; the table above is a screening filter, not the answer.

Consequence for A3's "derated air-cooled power" figure: the same equation solved for natural
convection at 25 C ambient with a realistic bare-flange Rth. Expect it to be a small fraction of
150 W - i.e. **the board is unusable at rated power without the external heatsink**, which the
README must state plainly.

## 4. Environment

| Item | Value | Status |
|---|---|---|
| Ambient temperature | **25 C** for all thermal numbers | A3 |
| Cooling | natural convection for the "derated air-cooled power" figure; forced air / coldplate covered by quoting the required Rth instead | A3 |
| Enclosure | **none** - open bench / bolted to a user heatsink | `ASSUMED:` (brief describes a bolt-on heatsink or coldplate, no enclosure) |
| Ingress protection | **none required** | `ASSUMED:` indoor bench use |
| Vibration / shock | **none** - stationary bench use | `ASSUMED:` |
| Altitude / humidity | ordinary indoor lab conditions | `ASSUMED:` |
| Hot surfaces | the termination element and its flange WILL run far above touch-safe temperature at 150 W CW - see section 8 flag F3 | derived |

`ASSUMED:` no storage/operating temperature range beyond the above was stated; standard FR4
(Tg 130-150 C) and standard-tolerance passives are acceptable. Note the PCB sits on the same
surface as a flange that may exceed 100 C, so the board WILL be heated by proximity even though
it is not intentionally in the thermal path (A4). P6 should keep FR4 and any polymer-bodied part
away from the flange footprint where the outline allows.

## 5. Size & mounting

| Item | Value | HARD / soft |
|---|---|---|
| Board outline | **<= 30 x 30 mm** | **HARD** - stated as a constraint in the brief. Binds permanently at P5 `board_init`; cannot be relaxed later without restarting layout. |
| Layer count | **2 layers**, JLCPCB standard FR4 process only. No upcharge options, no controlled-impedance service. | **HARD** - stated in the brief |
| PCB thickness | 1.6 mm | `ASSUMED:` JLCPCB standard, no upcharge (brief forbids upcharge options) |
| Copper weight | 1 oz outer | `ASSUMED:` JLCPCB standard; adequate - see the skin-depth note in section 1 |
| Mounting holes | none specified | `ASSUMED:` the termination element's own flange screws are the primary mechanical anchor (A4). Add PCB clearance/mounting holes only as the mechanical stack-up demands. |
| Height limit | none stated | `ASSUMED:` unconstrained. The tallest parts will be the SMA jack and the trimmer, both of which must stay accessible per I2. |

Mechanical items that later phases MUST resolve (recorded here because they can invalidate the
HARD outline):

1. **Flange bolt pattern vs the 30 x 30 mm outline.** A >= 250 W flange resistor is a physically
   large part; its flange holes bolt to the heatsink, not to the PCB. The outline must therefore
   accommodate a notch, cutout, or edge-relief for the flange and its screws, alongside an SMA
   jack, inside 30 x 30 mm. `ASSUMED:` this fits; **if P1's chosen part makes it impossible, that
   is a HARD-constraint conflict and must be escalated, not silently resized.**
2. **Terminal-height stack-up.** The PCB sits on the same surface as the flange (A4), so the
   board's top copper sits ~1.6 mm above the flange plane while the resistor's terminals sit at or
   near flange level. `ASSUMED:` the terminal tabs are formed/bridged to the PCB pads with a short
   solder connection or strap. Whatever bridges that gap adds series inductance against the 32 nH
   budget of section 1 - **keep it short and wide.** Resolve concretely at P2/P6.
3. **Tuning-tool access cone.** Per I2/A6 the adjustment must be reachable from the top with the
   SMA cable mated and the board bolted down. That forbids placing the trimmer under the SMA
   barrel or hard against the flange body. This is a placement constraint at P6, not a preference.

## 6. Quantity & budget

| Item | Value | Status |
|---|---|---|
| Build quantity | **5** | brief |
| Total budget | **<= $40 for the build of 5** = **$8.00 per board**, covering BOM at qty-5 pricing + bare PCB | brief |
| Excluded from the cap | PCB shipping and tax - order-time costs, not design costs | A8 |
| Sourcing | all parts **in stock at LCSC or DigiKey**; no NRND, no obsolete | brief (HARD) |
| Cap behaviour | if the cap cannot be met, **report the real number - do not degrade the design** | A8 |

**KNOWN BUDGET RISK - record now, resolve at P1, do not paper over.** Section 3 concludes the
termination element must be rated >= 250 W. Flange-mount RF terminations in that class routinely
cost $20-60 each in single quantities, i.e. **one part could exceed the entire $40 build-of-5
cap by several times.** Levers available to P1, in preference order:

1. A non-RF-specific bolt-down thick-film power resistor (TO-220/TO-247/flanged) of the right
   value and power class. Admissible here *only because* the +/-10 ohm reactance budget of
   section 1 plus the adjustment element of A6 tolerate a part that is not characterised for RF -
   at 25 MHz on an electrically tiny board that is a real option, whereas at 500 MHz it would not
   be. P1 must verify parasitic inductance against the 32 nH budget before committing.
2. Accept the overrun and report the true number per A8.

Do **not** resolve this by dropping the power rating back to 150 W - section 3 proves that is
thermally unsatisfiable.

## 7. Assembly

| Item | Value | Status |
|---|---|---|
| Method | **hand-solder / bench build of 5.** NOT JLC PCBA - the flange resistor and the SMA jack are through-hole/mechanical parts, and PCBA of a 5-off with a bolt-down power part is not sensible | A5 |
| Deliverables regardless | BOM and CPL are still produced as fab deliverables | A5, brief |
| Assembly sides | **single-sided (top) only** | `ASSUMED:` derived from A4 - the bottom face sits flat on the heatsink surface, so it must carry no components |
| Unique BOM lines | **<= 4** | brief (HARD) |
| Total placements | **<= 6** | brief (HARD) |
| Layers | 2, JLCPCB standard FR4, no upcharge options | brief (HARD) |

Budget headroom note: the function needs roughly a jack + a termination element + an adjustment
element = ~3 lines / ~3 placements. The caps are not tight; they exist to forbid scope creep.
Mounting holes and cutouts are not placements and do not consume BOM lines.

## 8. Compliance / safety flags

Flags that **APPLY**:

**F1. >30 V present - 86.6 Vrms / 122.5 Vpeak / 244.9 Vpp at the RF port, continuously.**
This is well above the 30 V flag threshold and above the 60 VDC / 30 Vrms conventional
touch-safe limit. Consequences that bind later phases:
- Every component on the port node - explicitly including the A6 adjustment trimmer - must be
  rated for continuous service at >= 250 V working. **A 100 V-rated trimmer is disqualified.**
- Creepage/clearance on the port net must be sized for 245 Vpp, not for a signal-level net.
  This is a 2-layer board with an exposed top side; a trimmer screw the operator touches while
  the port is live is a live-part-access question, so the tuning access of I2 must be designed to
  keep fingers off the hot node (insulated tuning tool, grounded rotor orientation).
- **Tuning while transmitting at 150 W is the intended use case** (adjust for minimum reflected
  power). The README's tuning procedure must therefore state the shock precaution explicitly, or
  prescribe tuning at reduced drive power.

**F2. RF transmit / high-power RF at the port - 150 W CW, DC-25 MHz.**
The board is a *load*, not a source, so it does not itself radiate by design; but it is
permanently connected to a 150 W HF transmitter and it is unshielded and unenclosed.
- A well-matched termination radiates little, but any residual mismatch, an unmated port, or a
  poorly made cable connection turns the assembly into an accidental HF radiator at 150 W. The
  README must state: **never key the transmitter with the port unmated.**
- 25 MHz sits just below the 27.12 MHz ISM allocation and inside HF spectrum used by licensed
  services. This assembly is a test load, not a certifiable product; it is not intended for
  connection to an antenna.
- RF burn / RF exposure hazard exists at the port at 150 W independently of the thermal hazard
  below. Do not handle the centre conductor or an unmated connector while keyed.

**F3. Burn / touch-temperature hazard - the intended, normal operating condition.**
Section 3 shows the flange must sit at 75-103 C for the derating curve to close at 150 W, and the
resistor's own body will be hotter still. The heatsink it bolts to will also be hot. This is not
a fault condition; it is what "working correctly" looks like.
- Requires a "HOT SURFACE" warning in the README and, budget permitting within the 30 x 30 mm
  outline, on the silkscreen.
- Cool-down time before handling must be stated in the README.
- The PCB (FR4, and any polymer-bodied part on it) sits on the same hot surface - see section 4.

Flags that do **NOT** apply, stated explicitly:

- **Mains voltage: none.** Nothing on this board connects to mains. The user's brief fixed this.
- **Battery: none.** No cell, no charger, no chemistry decision anywhere.
- **Motors: none.**
- **High current (>3 A): does not apply.** Port current is 1.732 Arms (section 1), below the
  threshold.

**Why these are documented and not asked:** the user's brief already fixed the safety-relevant
architecture - external heatsink supplied by the user, no mains, no battery, passive board. The
normal P0 rule "ask, never guess, for anything in section 8" is satisfied because nothing in
section 8 is *guessed*: F1 and F2 follow arithmetically from the user's own 150 W / 50 ohm /
25 MHz numbers, and F3 follows from the user's own external-heatsink architecture. There is no
open safety decision left to make, so there is nothing safety-blocking to ask.

## 9. Open questions

**none.**

The user instructed: "Do not ask clarifying questions. Make assumptions, record them in the
README, and proceed." Every gap is closed as an `ASSUMED:` above or by standing assumption
A1-A9 (section 11). Nothing remaining is safety-blocking - see the closing note in section 8.

The three assumptions with the largest downstream leverage, flagged for the README rather than
asked: (a) CW duty per A2 - if the real use is pulsed, the whole thermal case relaxes;
(b) the generic derating curve in section 3 - P1 must replace it with the real datasheet curve;
(c) the mechanical stack-up items in section 5, which are the only route by which the HARD
30 x 30 mm outline could be found infeasible.

## 10. Acceptance criteria (measurable, testable)

Pass/fail list for the finished board. Each is measurable with bench equipment or from the fab
artifacts.

1. **DC resistance.** Measured port centre-to-shell DC resistance = **50 ohm +/-2%**, i.e.
   **49.00 to 51.00 ohm** inclusive. Measured with a 4-wire ohmmeter at the mated SMA interface,
   at room temperature, unpowered. Met by the termination element's own tolerance; **no DC
   trimming is provided or required** (A7).
2. **Return loss at the design point.** **>= 26 dB at 25.0 MHz** after adjustment
   (\|G\| <= 0.0501, VSWR <= 1.106). Measured on a calibrated VNA at the SMA port with the board
   bolted to its heatsink and the trimmer set per the documented procedure.
3. **Return loss across the band.** **>= 20 dB at every frequency from 22.5 to 27.5 MHz**
   (\|G\| <= 0.100, VSWR <= 1.222), with the trimmer left at its criterion-2 setting - i.e. one
   adjustment satisfies both 2 and 3. Per A1 the design targets this from DC to 27.5 MHz, a
   superset of the specified window; verify the superset, report the specified window.
4. **Residual reactance (diagnostic for 2 and 3).** Post-tune equivalent series reactance at
   25 MHz **\|X\| <= 5.0 ohm** (equivalently <= 31.9 nH residual series inductance), and
   **\|X\| <= 10.05 ohm** at both band edges. This is the internal budget that criteria 2 and 3
   test from outside; record it so a failure is diagnosable.
5. **Adjustment range, documented and demonstrated.** The trimmer must move the port reactance
   at 25 MHz over a **continuous range that spans at least 0 to 10 ohm** (0 to ~64 nH equivalent)
   so it can absorb the as-built residual with margin at both ends. The achieved range must be
   **measured and stated as a number in the README**, not asserted.
6. **Adjustment is operator-accessible as specified.** Demonstrated: the trimmer can be turned
   through its full range with a hand tuning tool while the board is bolted down AND the SMA
   cable is mated, **without desoldering and without unbolting anything** (A6, I2).
7. **Adjustment-element voltage rating.** Every component on the port node is rated
   **>= 250 V working**, verified against its datasheet, versus the computed 122.5 Vpeak /
   244.9 Vpp. Checked from the BOM, not the bench.
8. **BOM line count.** **<= 4 unique BOM line items.** Counted from the delivered BOM file.
9. **Placement count.** **<= 6 total placements.** Counted from the delivered CPL file.
10. **Outline.** Board fits within **30.0 x 30.0 mm** - HARD. Verified from the delivered gerbers
    / board edge-cut extents.
11. **Process.** **2 layers, JLCPCB standard FR4**, no upcharge options, no controlled-impedance
    service on the order. Verified from the fab notes and the delivered stackup.
12. **Cost.** **<= $40.00 total for a build of 5**, computed as BOM at qty-5 pricing + bare PCB,
    excluding shipping and tax (A8). If exceeded, the **actual** figure is reported and the design
    is NOT degraded to meet the cap.
13. **Sourcing.** Every BOM line is **in stock at LCSC or DigiKey** at the time of the BOM, and
    no line is NRND or obsolete. Verified per line with a stock figure and a date.
14. **Thermal documentation (README deliverable).** The README states, computed from the **actual
    datasheet derating curve** of the part actually chosen: (a) the allowed flange temperature at
    150 W, (b) the required total heatsink-plus-interface thermal resistance to hold it at 25 C
    ambient, and (c) the **derated air-cooled power** achievable with no heatsink under natural
    convection at 25 C. All three as numbers with the curve they came from.
15. **Gate cleanliness.** ERC clean and DRC clean against the JLCPCB 2-layer rule set. Verified by
    the pipeline gates, not by inspection.
16. **Fab artifacts complete.** Gerbers, drill, BOM, CPL, plus the one-page README containing the
    tuning procedure, the measured tuning range (criterion 5), and the thermal numbers
    (criterion 14). Per A9, the pipeline stops at fab artifacts; **no order is placed.**

## 11. Traceability - standing assumptions A1-A9

Reproduced verbatim in substance from `brief/brief.md`. These are **decided answers**. All of
them must appear in the final README.

| # | Assumption | Where it binds |
|---|---|---|
| A1 | Band DC - 25 MHz; Fc = 25 MHz as worst case; Fc +/-10% = 22.5-27.5 MHz; design targets >= 20 dB DC-27.5 MHz (a superset) | sections 1, 10 (criteria 2, 3) |
| A2 | Duty (left blank by user) = **CW, 100%, continuous** - thermal worst case; a pulsed spec can only be easier | sections 3, 4 |
| A3 | 25 C ambient; natural convection for the "derated air-cooled power" figure; forced air / coldplate handled by quoting required Rth | sections 3, 4, 10 (criterion 14) |
| A4 | Resistor bolts DIRECTLY to the user's heatsink/coldplate through its own flange holes; PCB is a launch/interface carrier on the same surface, not in the thermal path; no heat intentionally through FR4 | sections 1, 3, 4, 5, 7 |
| A5 | Hand-solder / bench build of 5, not JLC PCBA; BOM + CPL still produced | section 7 |
| A6 | Adjustment element = shunt trimmer capacitor at the launch; reachable by a tuning tool with the board bolted down and the SMA cable mated (top access, no desoldering, no unbolting) | sections 2, 5, 8, 10 (criteria 5, 6) |
| A7 | "DC resistance 50 ohm +/-2%" met by the element's own tolerance (+/-1% or +/-2% part); no DC trimming provided or required | section 10 (criterion 1) |
| A8 | $40 / build-of-5 cap = BOM + bare PCB; shipping and tax excluded; if the cap cannot be met, report the real number rather than degrading the design | sections 6, 10 (criterion 12) |
| A9 | No ordering. Deliverables stop at fab artifacts (gerbers, drill, BOM, CPL) + README. Pipeline runs P0-P9; P10/ordering not requested | section 10 (criterion 16) |
