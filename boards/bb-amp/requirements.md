# bb-amp - requirements

Source: `brief/brief.md` (owner's verbatim brief). Written at P0 by the
requirements-analyst. Nothing here selects a part, a topology or a value: the
unknowns that would decide those are section 9, and they are for the owner.

## 1. Function

bb-amp is a sensor-amplifier signal chain on a bare board. It takes a
differential 0-20 mV signal from an OFF-BOARD bridge sensor (the sensor carries
its own excitation, so this board provides NO excitation circuitry), amplifies
it, and presents 0-3.3 V single-ended, referenced to board ground, over DC to
1 kHz. It is powered from an external 3.3 V rail. The nominal transfer is
165 V/V - that is 3.3 V / 20 mV restated, not a topology decision; the exact
gain follows from the answers to Q5, Q6 and Q10 and belongs to P2/P4.

**Build mode** (resolved at P0 by `state.py mode`; do not re-derive):

| dial | value |
|---|---|
| token | `learning block-basics:` |
| mode / target | `block-basics` |
| scope tier | `block-only` |
| binding level | `canonical` - geometry is an OUTPUT of the placement |
| stage under study | none |

Scope consequences every later phase and both reviewers should read from here:

- ON the board: the amplifier block's active part(s), exactly the support
  components their datasheets require for correct operation at the stated
  operating point (decoupling, the reference the amplifier's own single-supply
  operation needs, gain-setting components), plus one input interface, one
  output interface and the power entry - the three screw terminals the brief
  names.
- NOT on the board, and never a reviewer finding at `block-only`: protection
  (TVS/ESD, reverse polarity, fusing, OVP/OCP), filtering the datasheet does not
  require, indicators, test-points beyond the block's own measurement need,
  config straps or DNP options, any second rail or second IC the block does not
  need, mechanical and enclosure features beyond mounting the bare board.
- NOT relaxed by the mode: every electrical spec, every gate, the P2/P3
  coverage checks and the research they trigger, DFM, the datasheets' own
  requirements, and section 8. A mode relaxes geometry, cost and packaging only.

## 2. Interfaces

Three screw terminals, all named by the brief. They are the block's one input,
one output and its power entry - in scope at `block-only`.

| ref | interface | signal | electrical |
|---|---|---|---|
| J1 | input | differential from the off-board bridge sensor | 0-20 mV nominal full scale, DC to 1 kHz; common-mode level UNKNOWN -> Q1; pole count -> Q2 |
| J2 | output | single-ended, referenced to board GND | 0-3.3 V nominal full scale, DC to 1 kHz; achievable span -> Q6; load -> Q8 |
| J3 | power | external 3.3 V rail + GND | see section 3 |

- **J1**, recommended 3 poles (IN+, IN-, GND) pending Q2. Two poles only is a
  floating input: an amplifier needs a DC return for its input bias currents
  and a defined common-mode reference, and without them the output is not
  predictable. This is the single riskiest unknown on the board.
- **J2**, 2 poles (OUT, GND). The output terminal is also the block's
  measurement point, so no separate test points are added.
- **J3**, 2 poles (+3V3, GND). One ground node on the board; J1/J2/J3 grounds
  are the same net.
- No connector standard is imposed by the brief. ASSUMED: pluggable or fixed
  screw terminal blocks on a 3.5 mm or 5.08 mm pitch accepting roughly 24-16 AWG
  wire, top side, silkscreened IN+ / IN- / GND / OUT / +3V3. The exact part is
  P3's call.
- ASSUMED: IN+ above IN- gives a positive output (polarity convention).
- ASSUMED: no ESD/TVS, no series protection and no anti-alias or band-limiting
  filter beyond the amplifier's own response - protection and filtering are
  excluded at `block-only`. Response shape at the top end is Q9.
- ASSUMED: sensor cable 1 m or shorter, shielded twisted pair, shield landed on
  J1's GND pole if Q2's default holds. No cable is supplied with the board.
- The board does NOT excite the bridge and has no excitation output: the brief
  states the sensor brings its own.

## 3. Power

- Single external rail, 3.3 V, entering on J3. No on-board regulation, no second
  rail, no battery, no charging, no power switch (a second rail is excluded at
  `block-only`).
- Rail tolerance and the current this board may draw: UNKNOWN -> Q10. ASSUMED
  for planning: 3.3 V +-5%.
- **GUESS (not a spec):** total board current under 10 mA. A precision
  single-supply amplifier plus whatever sets its reference is typically a few
  mA; P2/P3 replace this guess with the real datasheet numbers.
- In scope as datasheet-required support, not as "filtering": local decoupling
  at every amplifier supply pin as its datasheet specifies, and the reference
  node a single-supply amplifier needs in order to define its output zero.
- Consequence that drives the design: with only 0 V and 3.3 V available, the
  rail bounds BOTH the input common-mode range (Q1) and the output swing (Q6).
  Those two questions are the single-supply headroom problem, and they are not
  relaxable - they are electrical specs.

## 4. Environment

- Bench use, indoors, 0-50 C operating (block-only default; taken, not asked).
- No enclosure. No ingress rating. No vibration, shock or drop requirement.
  Non-condensing humidity; no conformal coating.
- Storage/handling: ordinary lab conditions. No altitude or pollution-degree
  requirement follows from a 3.3 V board.
- Accuracy consequence: drift across 0-50 C, not initial error, is what the
  accuracy target in Q7 mostly has to buy.

## 5. Size and mounting

**No HARD cap. No dimension is stated in the brief, and none is imposed here.**
Under binding `canonical` the board size, aspect and outline are OUTPUTS of the
placement, so any number that appeared here would be a PREFERENCE only -
RELAXABLE (canonical) - and there is nothing to mark, because nothing is stated.

The canonical flow is mandatory and its order is load-bearing:

1. P5 `board_init --outline auto` - generous provisional room. `board_init`
   REFUSES a fixed outline under this binding; guessing a final size here binds
   placement to a number nobody has earned.
2. P6 place to the canonical layout for this block, gate `place`.
3. `board_edit --outline fit --margin M` - the board becomes what the placement
   needs. Re-run `planes_gen` if it GREW.
4. P7 route.

- Mounting: none required for bench use. Mechanical is excluded at
  `block-only` (mounting the bare board is all that is in scope), so the absence
  of mounting holes is not a reviewer finding; if the earned outline leaves
  corner room, plain M3 clearance holes may be added at P5/P6.
- Height: no limit - no enclosure. Terminal blocks are the tallest parts.
- Layer count is P2's decision under the "fewest honest layers" default; a
  ground reference under a 165 V/V DC signal chain is the reason to expect two.

## 6. Quantity and budget

- Build quantity 5 (block-only default; taken, not asked).
- No target unit cost is stated. Cost minimal, within the accuracy answered in
  Q7: a 12-bit-usable chain and a 16-bit chain are different part classes and
  different money, which is why Q7 is asked rather than assumed cheap.
- Standard JLC process only; no NRE beyond it; no exotic stackup, no controlled
  impedance, no gold fingers.

## 7. Assembly

- JLC PCBA, single-sided (top) assembly (block-only default; taken, not asked).
- ASSUMED: the SMT parts are placed by JLC; the three screw terminals are
  through-hole in most catalogs and JLC's standard SMT service does not place
  them - default is that the owner hand-solders three terminal blocks on the top
  side, unless P3 finds suitable SMD terminal blocks. Either resolution is
  acceptable; P3 records which.
- Lead-free process, fab-default finish and soldermask. No conformal coating, no
  potting, no cable assemblies, no enclosure.

## 8. Compliance and safety flags

Recorded plainly: **none of the flagged hazard classes apply to this board.**

| flag | applies? | why |
|---|---|---|
| mains voltage | no | powered from an external 3.3 V bench rail (SELV); nothing on the board is mains-referenced |
| battery / charging | no | no battery, no cell holder, no charge circuit |
| motors / inductive loads | no | output drives a measurement input, not a load |
| voltage above 30 V | no | 3.3 V is the highest potential anywhere on the board |
| current above 3 A | no | expected board current is milliamps (see section 3) |
| RF transmit | no | no radio, no intentional radiator |

Two conditions would re-open this section, and both hang off the off-board
sensor that this board cannot see:

- If the bridge excitation named in Q1 is above 30 V, J1 becomes a
  hazardous-voltage interface and section 8 must be re-answered before P2.
- If the sensor is mounted on equipment whose chassis sits at mains potential,
  the input cable carries that potential onto this board; that is an isolation
  requirement, not an amplifier requirement, and it is out of this board's
  current scope.

No mode grants silence here: if either condition is true, say so in the answers
and the pipeline stops to re-scope rather than guessing.

## 9. Open questions

Batched for one round of answers. Each is closed-form with a recommended
default; taking every default is a valid answer.

1. **What voltage excites the bridge, and does that excitation share this
   board's ground?** Recommended default: 3.3 V excitation, sharing this board's
   ground, so both input wires sit near 1.65 V - comfortably inside what a
   3.3 V-powered amplifier can accept. Why it matters: with 5 V or 10 V
   excitation (both common on load cells) the input wires sit near 2.5 V or 5 V;
   5 V is OUTSIDE the input range of anything powered from 3.3 V and forces a
   different front end. Above 30 V it also changes section 8.

2. **Does the sensor cable bring a ground wire to this board - i.e. should the
   input terminal have 3 poles (IN+, IN-, GND) rather than 2?** Recommended
   default: yes, 3 poles, with the cable shield landing on that GND pole. Why it
   matters: with only two wires the input has no DC path for the amplifier's
   input bias currents and no defined common-mode level, and the output drifts
   to a rail. Two poles is only safe if the sensor's excitation return is
   already tied to this board's ground somewhere else - if so, say where.

3. **What is the bridge's nominal resistance (the impedance seen looking back
   into each input)?** Recommended default: 350 ohm, the common load-cell value.
   Anything from 120 ohm to about 10 k is unremarkable for a high-impedance
   front end; above 10 k the amplifier's own input current starts to add error
   and narrows the part choice.

4. **Must the output track the excitation (ratiometric), or is a fixed
   amplifier enough (absolute)?** Recommended default: absolute - a fixed gain,
   with accuracy resting on the excitation being stable. Why it matters: a
   bridge's output is proportional to its excitation, so a 1% excitation drift
   is a 1% reading error in the absolute case. Ratiometric operation removes
   that, but needs a sense wire from the off-board excitation supply, which is a
   second input interface the `block-only` scope does not carry - answering
   "ratiometric" is a scope change, not a tweak.

5. **Beyond the nominal 0-20 mV, what can actually appear at the input?**
   Recommended default: down to about -1 mV (a real bridge rarely reads exactly
   zero at rest) and up to about +25 mV under overload, with the amplifier
   expected to clip gracefully and recover - no added protection parts, which
   are excluded at this scope. Why it matters: if slightly negative inputs are
   possible, the output must sit at a small positive pedestal (see Q6) or a
   negative zero reads as a hard 0 V and cannot be calibrated out.

6. **A board on a single 3.3 V rail cannot output exactly 0.000 V or exactly
   3.300 V - a real amplifier stops short at each end. Is a guaranteed usable
   output of roughly 0.05 V to 3.25 V acceptable, with full scale defined inside
   it?** Recommended default: yes, accept the reduced span, and place the
   0 mV point at a small positive pedestal (about 0.1 V) so Q5's negative
   readings stay visible. Why it matters: demanding the true rails requires a
   supply above 3.3 V or a negative rail - a second rail, which this scope
   excludes - so this is the one place where the brief's "0-3.3 V" and its
   "3.3 V rail" genuinely conflict, and the owner picks which one bends.

7. **How finely does the reading need to be resolved, and is the system
   calibrated?** Recommended default: usable to 12 bits over the output span
   (about 0.8 mV at the output, about 5 microvolts referred to the sensor), with
   zero and span calibrated by whatever reads the output, so initial offset and
   gain error are trimmed and only noise and 0-50 C drift remain. Why it
   matters: 8 bits makes almost any amplifier acceptable and cheap; 16 bits
   changes the part class, the error budget and the cost.

8. **What will the 0-3.3 V output drive, and over how much cable?** Recommended
   default: a high-impedance input (bench meter or ADC input, above 100 k) on a
   lead under 1 m and under about 1 nF of capacitance. Why it matters: a
   capacitive cable or a load that draws real current changes the output stage
   and can make an otherwise fine amplifier ring.

9. **"DC to 1 kHz" - should the response still be flat (within about 1%) at
   1 kHz, or is 1 kHz where it has already fallen by about 30% (-3 dB)?**
   Recommended default: flat within about 1% at 1 kHz, which means designing the
   amplifier's bandwidth several times higher. Why it matters: it sets how fast
   the amplifier has to be at a gain of 165, which is a part-selection
   constraint.

10. **How accurate is the external 3.3 V rail, and how much current may this
    board draw from it?** Recommended default: 3.3 V +-5% and a 10 mA budget.
    Why it matters: a rail that sags to 3.0 V shrinks the usable output span in
    Q6, and a tight current budget rules out some precision parts.

## 9a. ANSWERS (owner, 2026-08-16) - these are now REQUIREMENTS

Every question above is answered. Each is also a `state.py decision` at P0.
Downstream phases design to THIS section, not to section 9's defaults.

| Q | answer |
|---|---|
| 1 | Excitation **3.3 V, sharing this board's ground**. Input common-mode sits at **~1.65 V**. |
| 2 | **3-pole input terminal**: IN+, IN-, GND. Cable shield lands on that GND pole. |
| 3 | Bridge **350 ohm** nominal. |
| 4 | **Absolute** gain (NOT ratiometric). No excitation-sense input. |
| 5 | Input range to design for: **-1 mV to +25 mV**; beyond that the amplifier clips gracefully and recovers. No added protection parts. |
| 6 | **Reduced span with a pedestal.** Guaranteed usable output ~**0.05 V to 3.25 V**; 0 mV input maps to a small positive pedestal of about **0.1 V**. The brief's literal 0.000-3.300 V LOSES to the single 3.3 V rail. |
| 7 | **12-bit usable** over the output span: ~0.8 mV at the output, ~**5 uV referred to the input**. Zero and span calibrated downstream, so 0-50 C drift and noise are the real error budget. |
| 8 | Output drives **>100 kohm**, lead **<1 m**, **<1 nF**. |
| 9 | Response **flat within ~1% at 1 kHz** (1 kHz is inside the flat band, not the corner). |
| 10 | Rail **3.3 V +-5%**, board current budget **10 mA**. |

### What those answers make binding

- **Transfer function**: `Vout = Vped + G * Vin_diff`, with `Vped ~= 0.1 V`, and
  `Vin_diff = 20 mV` (full scale) landing INSIDE the guaranteed usable output
  top (~3.25 V). The gain follows from those two endpoints and is P2's to fix;
  it is close to but NOT equal to the brief's nominal 165 V/V, because the
  pedestal and the swing limit both eat span.
- **Pedestal source**: the ~0.1 V reference is a real circuit node. Whatever
  drives an instrumentation amplifier's REF input must be LOW impedance (or the
  amplifier must have a high-impedance REF by construction) - a bare resistor
  divider on a classic 3-op-amp in-amp REF pin degrades CMRR directly, and CMRR
  is the whole point of this block. P2 must say which mechanism it is using.
- **Bandwidth**: for a single-pole rolloff, 1% droop at 1 kHz puts the -3 dB
  corner near **7 kHz**. At a gain around 150-165 that is roughly **1 MHz of
  gain-bandwidth** in the gain path. Verify the rolloff-shape assumption; this
  is the dominant part-selection constraint and it disqualifies the lowest-power
  zero-drift in-amps.
- **Error budget** (12-bit usable, calibrated, 0-50 C): offset and gain error
  are trimmed out, so what must fit in ~5 uV RTI is **offset drift x 50 C**,
  gain drift, CMRR error against the 1.65 V common mode, and integrated noise
  from DC to the amplifier's own bandwidth. Noise density and 1/f corner matter
  here; initial offset does not.
- **Common mode**: 1.65 V, mid-rail, on a 3.3 V supply - benign, and the reason
  a single-supply in-amp front end stays viable. The input range is unipolar
  (0-20 mV nominal, -1 mV worst case), so the pedestal, not a mid-rail
  reference, sets the output zero.

### Delegated authority

The owner delegated the remaining engineering judgment for this run: decide
in-run, optimizing for the LEARNING value of a basic sensor front end. H1-H4
are presented as records rather than blocking holds. The run stops at P9 per the
`block-only` default - ordering stays a separate owner decision, so no
irreversible or money-spending step is reached.
