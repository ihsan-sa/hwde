# Requirements: bb-adc

## 1. Function

A single-channel analog-to-digital converter, built as a study article. It
takes one DC analog voltage in the range 0 to 5 V on a screw terminal,
digitizes it to 12 bits or better at a rate up to 10 kSa/s, and hands the
result to a host over a 0.1 inch header. That same header feeds the board its
only supply, 3.3 V. DC accuracy is the dominant requirement; conversion speed
is secondary and explicitly subordinate to it. Nothing else is on the board:
no MCU, no display, no indicators, no second channel.

BUILD MODE: the brief opens with the token `learning block-basics:`. Resolved
at P0 (`state.py mode`, recorded as a P0 decision; contract in
`reference/build-modes.md`):

- mode / target: **block-basics**
- scope tier: **block-only**
- binding level: **canonical** - board geometry is an **OUTPUT** of the design,
  not an input to it
- stage under study: **none** (the block end to end, no single stage frozen as
  a bench fixture)

What that means here. The block under study is the ADC signal chain itself:
the converter, exactly the support parts its datasheet requires for correct
operation at the stated operating point, one input interface (the screw
terminal) and one output interface (the host header), plus what the fab needs
to build the board and the bench needs to hold it. Protection of every kind,
filtering the datasheet does not require, indicators, config straps, test
points beyond the block's own measurement need, any second rail or second IC
the block does not need in order to work, and mechanical/enclosure features
beyond mounting the bare board are OUT by MODE, not by engineering judgment -
and must never be recorded as generally unnecessary. The mode's defaults are
applied below (quantity 5, JLC PCBA single-sided, bench 0-50 C indoor, no
enclosure, fewest honest layers, geometry earned by the placement, stop at P9)
instead of being asked. The mode relaxes geometry, cost and packaging only:
every electrical spec, every gate, the coverage checks and the research they
trigger, DFM, the datasheet's own requirements and every safety question in
section 8 stand unchanged.

**Recorded requirement tension, NOT solved here (P1 owns it).** The stated
analog input span (0 to 5 V) sits ABOVE the board's only stated rail (3.3 V
from the host header). Every way out of that is an architecture decision -
which converter, which reference, whether the input is attenuated ahead of the
converter, whether the block honestly needs something the 3.3 V rail cannot
give it - and the architect decides it, not this document. Two consequences
that must travel with the tension:

- It touches a MODE BOUNDARY. `block-only` excludes "any second rail the block
  does not need in order to work"; if P1 concludes the block DOES need one to
  work at the stated operating point, that is support, not a feature, and the
  call belongs at H1 with the owner, recorded as a decision.
- It interacts with the accuracy answer (Open question 2). Whatever sits
  between the terminal and the converter is inside the DC error budget, so the
  topology choice and the accuracy number have to be settled together.

## 2. Interfaces

Exactly two external interfaces, which is what the scope tier allows and what
the brief states.

- **J1 - analog input.** Screw terminal (STATED). ASSUMED: 2-pole through-hole
  terminal block, 5.08 mm pitch - signal and its ground return - rated far
  above anything this board carries; pitch was not stated and 5.08 mm is the
  common, well-stocked JLC/LCSC choice that accepts bench lead wire. ASSUMED:
  single-ended input referenced to board ground, since the brief describes one
  channel of 0-5 V DC with no mention of a floating or differential source
  (confirm via Open question 4). Silkscreen-marked for signal and ground.
  NOTE: the board has no input protection by mode, so the silk marking and the
  owner's answer to Open question 5 are the only defenses against a wrong
  connection - see section 8.
- **J2 - host header.** 0.1 inch (2.54 mm) pitch header (STATED). It carries
  BOTH the digital output and the board's 3.3 V supply plus ground (STATED).
  ASSUMED: single-row, through-hole male pin header, one row, on a board edge.
  Pin count, pin order and protocol are NOT stated - see Open questions 3
  and 6.
- **Digital output signalling.** Protocol NOT stated (Open question 3).
  ASSUMED once the protocol is known: 3.3 V CMOS levels, referenced to the
  same ground the header supplies, host acts as the bus master and the board
  is a slave/peripheral - it never drives the interface unasked. ASSUMED:
  conversions are host-triggered (the host asks, the board answers); a
  dedicated data-ready or convert-start pin is added only if the chosen
  converter genuinely requires one, in which case it lands on J2 and the pin
  count in Open question 6 grows by that one line.
- **Sample rate.** ASSUMED: "up to 10 kSa/s" is a MAXIMUM capability, not a
  sustained obligation. Any rate from single-shot on demand up to 10 kSa/s
  must work; nothing requires gap-free streaming at the top rate. Low risk to
  assume, since a lower rate never makes a DC-accurate converter harder.
- **No other external interface exists or is wanted**: no USB, no second
  channel, no LED, no button, no jumper, no config strap, no external
  reference input connector, no test points beyond the block's own measurement
  need. All excluded by mode.

## 3. Power

- **Only rail: 3.3 V, supplied BY the host through J2 (STATED).** The board
  generates no rail of its own by default. Nominal 3.3 V; tolerance NOT stated
  - ASSUMED 3.3 V +/-5 % (3.135 to 3.465 V) at the header pin, which is the
  ordinary tolerance of a regulated host rail. Confirm with Open question 7.
- **Rail quality is an accuracy input, not a detail.** If the design ends up
  referencing the converter to its own supply, the host's rail noise and
  tolerance land directly in the measurement error. Whether that is acceptable
  depends on the answer to Open question 2 and is a P1/P2 decision; it is
  flagged here so the choice is deliberate.
- **Current budget (GUESS, for sizing and for Open question 7 only).**
  Converter 0.5 to 5 mA depending on class and rate; a precision voltage
  reference, if the accuracy answer requires one, 0.1 to 1.5 mA; an input
  buffer, if the source-impedance answer requires one, 0.5 to 2 mA; leakage
  and bias elsewhere well under 1 mA. Total GUESS: under 10 mA typical, under
  15 mA worst case. Marked as a guess: no part is chosen yet.
- **No battery, no charging, no energy storage, no backup rail, no second
  rail** on the board as specified. A second rail is excluded by the scope
  tier unless P1 shows the block cannot work without one - see the tension
  recorded in section 1.
- **Board dissipation**: negligible (GUESS: under 50 mW). This board has no
  thermal problem to solve. Temperature still matters, but as a DRIFT term in
  the accuracy budget over the 0-50 C ambient (section 4), not as a cooling
  requirement.
- **Excluded by mode (SCOPE decisions - do not record any of these as
  generally unnecessary)**: input TVS/ESD clamp, series/reverse protection,
  fusing, local rail filtering beyond the decoupling the converter's datasheet
  requires, and any supply sequencing or supervisor.

## 4. Environment

Mode defaults - applied, not asked.

- Ambient: 0 to 50 C, indoor bench.
- Cooling: natural convection only. No heatsink, no forced airflow, no chassis
  thermal path. Nothing on this board needs one.
- No enclosure. No ingress (IP) rating. No vibration or shock requirement. No
  humidity requirement. No conformal coating.
- No formal EMC/emissions campaign - this is a bench study article, not a
  product. Clean analog return geometry is still required because it is what
  makes the block correct, not because a test demands it.
- **Consequence that binds the electrical spec:** the 0-50 C range is what
  turns reference tempco, amplifier offset drift and (if an attenuator is
  used) resistor TCR mismatch into real, budgetable error terms. The accuracy
  answer in Open question 2 is therefore stated at 25 C AND across 0-50 C.

## 5. Size & mounting

- **Outline: no HARD cap. RELAXABLE (canonical).** The binding level is
  `canonical`, so board size, aspect and outline are OUTPUTS of the placement.
  Nothing in this section binds at P5 `board_init`. No planning dimension is
  written here on purpose: bb-buck recorded a "for planning only" figure, a
  number reached the CLI two checkpoints later, and placement optimized to fit
  it - the board ended up with 0.05 mm of slack on all four edges and taught
  the wrong lesson. This board will not repeat that.
- **The flow that earns the outline** (`reference/build-modes.md`, binding
  levels):
  1. P5 `board_init --outline auto` - generous provisional room. A fixed
     `--outline WxH` is REFUSED under this mode, and that refusal is correct.
  2. P6 place to the canonical layout, gate `place`.
  3. P6 close: `board_edit --outline fit --margin M` - the board becomes what
     the placement needs. Re-run `planes_gen` if it GREW.
  4. P7 route.
- **Layers**: ASSUMED 2, per the mode's "fewest layers the block honestly
  needs". If P2/P6 shows that an honest analog return and reference layout
  cannot be had on 2 layers, 4 is allowed under the same rule. Not fixed here
  either way.
- **Mounting**: ASSUMED 4 x M3 clearance holes (3.2 mm) inset from the
  corners, so the board can sit on standoffs at the bench. Mounting the bare
  board is explicitly in scope; enclosure fit is not. If the earned outline is
  too small for four, two on opposite corners is acceptable.
- **Height**: ASSUMED no maximum. The board is open on a bench with no
  enclosure, and the screw terminal itself stands roughly 10-12 mm tall with
  wire fitted, so a height cap would be arbitrary.
- **Connector placement**: ASSUMED the screw terminal and the host header sit
  on different board edges with their openings facing outward, so the analog
  input wiring does not have to cross the digital header to reach the bench.
  Which edges, and the geometry inside the board, is the layout engineer's
  call at P6 - that is the whole point of a canonical binding.

## 6. Quantity & budget

Mode defaults - applied, not asked.

- Build quantity: 5.
- Cost: minimal, with no hard per-unit cap. Prefer JLC Basic/Preferred parts
  wherever a Basic part actually meets the electrical requirement; Extended is
  allowed for the converter and for a precision voltage reference, where Basic
  stock in the required accuracy class is thin. Cost is one of the three
  things this mode may relax, and accuracy is not - if the accuracy answer and
  a Basic part conflict, accuracy wins and the choice is recorded.

## 7. Assembly

Mode defaults - applied, not asked.

- JLCPCB PCBA, single-sided: all SMT parts on the top side only. The bottom
  side stays clear of SMT so it can serve as unbroken return copper.
- The screw terminal and the 0.1 inch header are through-hole. ASSUMED: fitted
  by JLCPCB through-hole assembly if offered at acceptable cost for the chosen
  parts, hand-soldered after SMT otherwise. Either path leaves the schematic
  and the footprints unchanged.
- Pipeline stops at P9 (fab package + DFM). Ordering is a separate owner
  decision and is not requested here.

## 8. Compliance/safety flags

The mode grants no silence in this section. One safety-relevant fact is
genuinely missing from the brief and is asked as Open question 1; it is not
guessed, and the pipeline should not proceed past H1 without it.

- **Mains voltage: DOES NOT APPLY to anything ON this board** - the highest
  voltage on any board net at the stated operating point is 5 V. **BUT the
  source of the 0-5 V input is NOT stated**, and that is the one thing that
  could make this section wrong. A 0-5 V signal is very often the low side of
  something much larger: a shunt amplifier in a mains-referenced circuit, a
  divider off a high-voltage bus, an isolated sensor's output that turns out
  not to be isolated. This board has no isolation and no input protection by
  mode, and its input ground is the HOST's ground through J2, so a hazardous
  or merely elevated source ties the host to that source directly. ASKED, not
  assumed - Open question 1.
- **Batteries: DOES NOT APPLY.** No battery, no charging function, no pack, no
  cell chemistry, no deep-discharge behavior anywhere on this board. The board
  is fed by the host's 3.3 V rail, which it does not generate. Whatever powers
  the host is off-board and out of scope, with one caveat folded into Open
  question 1: if the measured source is a battery pack above 30 V, the answer
  changes this section.
- **Motors: DOES NOT APPLY as specified**, with the same caveat. Measuring a
  motor drive's current-sense or bus-divider output would put inductive
  transients and a large common-mode component on the input of a board with no
  protection. Covered by Open question 1.
- **RF transmit: DOES NOT APPLY.** No radio function of any kind.
- **High current (>3 A): DOES NOT APPLY.** The entire board draws an estimated
  10 mA and carries no power path. The threshold is not approached.
- **>30 V: DOES NOT APPLY at the stated numbers** - 5 V is the maximum on any
  net, 3.3 V is the only rail, so `check_creepage`'s derived spacing check is a
  clean no-op. This too is contingent on Open question 1: a source that puts a
  higher potential on the terminal, whether by fault or by design, engages it
  for real.
- **No input protection - noted, not flagged.** The scope tier excludes
  protection of every kind, so an over-range input, a reversed input, or a
  static discharge into the terminal can destroy the converter. On a bench
  article with a low-voltage source that is an accepted consequence of the
  declared scope, not a hazard to a person, and not a finding for a reviewer to
  raise. It is recorded so the consequence is visible rather than implicit, and
  it is why Open question 5 asks the owner to accept it knowingly.
- **No isolation - noted, not flagged.** Input ground and host ground are the
  same node. Any ground potential difference between the measured source and
  the host appears directly across the input and is measured as signal.
  Isolation is not in the scope tier and is not proposed; the owner should know
  the input must share the host's ground reference.

## 9. Open questions

Nine questions, all closed-form, each with a default. Question 1 is
safety-relevant and has no safe default for the hazardous case - it must be
answered, not defaulted past. The rest can be taken as the stated default if
the owner has no preference.

### ANSWERED by the owner 2026-08-16 (P0 batch) - these are now requirements

| Q | Answer | Effect |
|---|---|---|
| 1 | Low-voltage bench source (owner ruled "simplest option", which is this) | See the validity envelope below. RE-CONFIRMED AT H1. |
| 2 | **0.1 % class** | +/-5 mV of a 5 V reading at 25 C; +/-12 mV across 0-50 C, at the terminal, uncalibrated |
| 3 | **SPI** | 10 kSa/s is a maximum, not gap-free streaming (sub-part at default) |
| 4 | Single-ended to ground (default) | One signal wire + one ground wire at J1 |
| 5 | No protection ACCEPTED (default) | Input stays strictly inside 0-5 V; no negative excursion to resolve |
| 6 | Header per default | Single-row 0.1 in male, one edge: 3V3, GND, then SPI, +1 if the part needs DRDY/CONVST |
| 7 | Host rail per default | >=50 mA available, 3.3 V +/-5 %, tens of mV noise, no sub-3.0 V operation |
| 8 | **3.3 V only** | The 0-5 V span MUST be scaled into the 3.3 V domain; the attenuator is inside the error budget |
| 9 | Source <=1 kohm, board >=100 kohm (default) - **NARROWED AT P2, see below** | The board must not load the source appreciably |

**Q9 REVISED at P2 (orchestrator ruling, owner-delegated):** the contract is now
**source <= 200 ohm** (narrowed 5x from the answered 1 kohm) and **board presents
1.00 Mohm** (strengthened 10x from the answered 100 kohm). Both numbers go on the
silkscreen. Reason: as answered the two specs are jointly impossible at 0.1 % -
loading error is Rs/Rtot, so 1 kohm into 100 kohm is 1 % = 50 mV against a 5 mV
budget. Holding Rs <= 1 kohm instead is possible (a 5 Mohm 0.1 % divider closes RSS
at 4.27 mV) but publishes an 18.7 mV worst case against a 12 mV target and makes the
board's dominant uncertainty an ESTIMATED surface-leakage term on a megohm node
rather than a vendor-guaranteed maximum. This narrowing restricts what may be
connected and is therefore a visible H1 item.

**Q1 validity envelope - the design is valid ONLY for a source of this kind.**
Nothing anywhere in the source circuit above 30 V; no mains connection; no
motor drive or other inductive load; no battery pack above 30 V; already
referenced to the same ground as the host; lead about a metre or less. If the
real source ever falls outside that envelope, section 8 is wrong and the board
must not be connected to it: it has no isolation and no protection, and its
input ground is the host's ground. The owner delegated this to the default
rather than describing an actual source, so it is re-presented at H1 for
explicit confirmation before any money or copper is committed.

**Consequence of 2 + 8 together (the design problem this board actually
teaches).** A 0.1 % class result must be delivered through an attenuator that
brings 0-5 V into a 3.3 V domain, so the attenuator's ratio error and its
tempco are first-class terms in the error budget alongside the reference. That
combination - not the converter's bit count - is what P1/P2 have to solve.

1. **What actually produces the 0-5 V signal you want to measure, and can any
   part of that circuit reach a dangerous or elevated voltage?** This is the
   safety question. Say what it is in plain terms - a sensor, a potentiometer,
   the output of another bench instrument, a divider across a battery or a
   power supply, a current-shunt amplifier on a motor drive - and roughly how
   high the voltage goes ANYWHERE in that circuit, not just at the two wires
   coming to this board. This board has no isolation and no protection, and it
   shares the host's ground, so its terminal is electrically part of whatever
   it is connected to.
   DEFAULT (usable only if it is true): a low-voltage bench source - nothing
   in it above 30 V, no mains connection, no motor or other inductive load, no
   battery pack above 30 V - already referenced to the same ground as the
   host, connected by a lead of about a metre or less.
   If mains, a motor drive, or anything above 30 V is involved anywhere in
   that circuit, say so plainly. It does not necessarily stop the board, but
   it changes the requirements and this section has to be rewritten before the
   design proceeds.
2. **How accurate does "DC accuracy matters" actually have to be?** The brief
   says 12 bits or better, but bits are resolution, not accuracy - a 16-bit
   converter with a sloppy reference is less accurate than a 12-bit one with a
   good one, and this number is the single biggest driver of the parts on this
   board. Answer as an error at the terminal, with no user calibration
   assumed. Pick one:
   (a) **0.1 % class (DEFAULT)** - total error within about +/-5 mV of a 5 V
   reading at 25 C, and within about +/-12 mV across the full 0-50 C range.
   An honest, ordinary instrument-grade number.
   (b) 1 % class - about +/-50 mV. Cheaper, allows a converter's internal
   reference, and makes the board mostly about the conversion rather than the
   precision.
   (c) 0.01 % class - about +/-0.5 mV. This is a precision-metrology
   requirement: it forces a high-grade external reference, 16 bits or more,
   and low-drift resistors, and it will dominate the parts cost.
3. **Which digital interface should the host speak: SPI or I2C?**
   DEFAULT: **SPI** - it is what precision converters in this class almost
   always offer, it costs no throughput at 10 kSa/s, and it needs no address
   management. Choose I2C only if the host has no free SPI port or already
   runs an I2C bus you want this board to join; at 10 kSa/s continuous, I2C
   would need to run at 400 kHz or faster.
   Related, answer only if it is not the default: is gap-free streaming at the
   full 10 kSa/s required, or is 10 kSa/s a maximum the host will rarely
   sustain? DEFAULT: a maximum, not an obligation.
4. **Is the input a single voltage measured against ground, or a differential
   / floating measurement?**
   DEFAULT: **single-ended** - one signal wire and one ground wire, the signal
   measured with respect to the same ground the host supplies. Answer
   "differential" only if the two wires from your source do not share the
   host's ground, or if you need to reject a voltage common to both.
5. **What happens if the input goes outside 0 to 5 V - and do you accept that
   the board has no protection against it?** There is no clamp, no series
   resistor beyond what the converter needs, and no reverse protection on this
   board, because the study scope excludes protection. A 12 V bench supply
   clipped onto the terminal by mistake, or the wires swapped, will most
   likely destroy the converter.
   DEFAULT: **accepted.** The board is rated 0 to 5 V, survives only what the
   chosen converter inherently survives, and nothing is added to protect it.
   Also DEFAULT: the signal stays strictly within 0 to 5 V in normal use - it
   never sits slightly below zero (as some sensors do at their zero point),
   so the design does not have to resolve negative inputs. Tell us if either
   default is wrong; a small negative excursion in particular changes the
   converter choice more than it sounds like it should.
6. **What should the host header look like physically?** Pin count, pin order
   and orientation were not stated, and the host presumably already exists.
   DEFAULT: a single-row 0.1 inch male pin header on one board edge, pins in
   the order 3.3 V, GND, then the digital signals for whichever interface
   answer 3 selects (4 signal pins for SPI, 2 for I2C), so 6 pins for SPI or
   4 for I2C - plus one more pin if the chosen converter needs a data-ready or
   convert-start line. If your host expects a particular pinout or a
   particular connector, give it and it will be matched exactly.
7. **How much current can the host's 3.3 V rail supply to this board, and how
   clean is it?** The board's own draw is small (an estimated 10 mA), but if
   the design ends up measuring against that rail, its noise and tolerance
   become part of the measurement error.
   DEFAULT: at least 50 mA available, an ordinarily regulated 3.3 V +/-5 %
   rail with tens of millivolts of noise on it, and no requirement for the
   board to work below 3.0 V.
8. **Does the host header also have 5 V available, or is 3.3 V genuinely all
   there is?** The brief says 3.3 V, and that is being taken at face value -
   but the input span is 0-5 V, so the answer changes the shape of the design
   more than any other question here.
   DEFAULT: **3.3 V only**, exactly as the brief states. The board will be
   designed to measure a 0-5 V input from a 3.3 V-only supply.
9. **What is driving the terminal, electrically - can it supply a little
   current, or is it a high-impedance source that must not be loaded?** A
   potentiometer wiper or a long-settling sensor output can be loaded down by
   the converter's own input, and the fix (a buffer) is a part on the board.
   DEFAULT: the source can drive at least a light load - source impedance of
   1 kohm or less - and the board presents at least 100 kohm at the terminal.
   Tell us if your source is high-impedance (say, above 10 kohm) or if you
   need the board to be effectively invisible to it.
