# Requirements: bb-mcu

## 1. Function

A bare microcontroller board, built as a study article. It takes a
ready-made 3.3 V rail from an external supply on a screw terminal - there is
no regulation, no conversion and no second rail on this board - and gives
that MCU three things and nothing else: power in, the MCU's own standard
debug/programming interface brought out to a header, and four general-purpose
I/O brought out to a 0.1 inch header. The board's whole job is to hold one
MCU, let it be programmed and debugged, and let four of its pins be reached.

BUILD MODE (declared by the brief's opening token, resolved and recorded as
the P0 decision in `state.json`; contract in `reference/build-modes.md`):

- token: `learning block-basics:`
- target learning outcome: **block-basics** - the block end to end
- scope tier: **block-only**
- binding level: **canonical**
- stage under study: **none** (no single stage is being taught; the whole
  P0-P9 run is the lesson)
- geometry: **OUTPUT** - the brief states no size, none is invented here, and
  the placement earns the outline at P6 (see section 5)

The block under study is the MCU itself. In scope: the MCU, plus exactly the
support components its datasheet requires for correct operation at the stated
operating point (decoupling, and whatever the part needs on NRST / boot-mode /
supply pins to run and to be debugged), plus the interfaces named below, plus
what the fab needs to build the board and the bench needs to hold it. Out by
mode - a SCOPE decision, not an engineering conclusion, and never a reviewer
finding: protection of every kind, filtering the datasheet does not require,
indicators (no LEDs), buttons (no reset button), test points, config straps
and jumpers, any second rail or second IC, and mechanical/enclosure features
beyond mounting the bare board. The mode's defaults are APPLIED below
(quantity 5, JLC PCBA single-sided, indoor bench 0-50 C, no enclosure, fewest
honest layers, size earned by the layout, stop at P9) instead of being asked.

On "one input interface, one output interface": the input interface is the
3.3 V power in on the screw terminal, and the output interface is the 4-way
GPIO header. The debug interface is the third connector and it STAYS - it is
not a test point and not scope creep. An MCU that cannot be programmed is not
a working MCU, so its standard debug/programming access is part of the block
under study, and the brief names it explicitly. All three connectors below
are stated by the brief; nothing beyond them is added.

ASSUMED: this pipeline delivers hardware only. No firmware, no bootloader
image and no application program is a deliverable here; "programmable" is a
property of the board, not a software requirement on the run.

## 2. Interfaces

Three, all stated by the brief.

- **J1 - power input, screw terminal (STATED).** 2-pin, DC only, 3.3 V from
  an external rail. ASSUMED: through-hole 2-pole terminal block, 5.08 mm
  pitch, the well-stocked JLC/LCSC choice that takes bench lead wire (pitch
  was not stated; packaging is relaxable under this mode, so it is assumed
  rather than asked). Polarity silkscreen-marked (+ / -). NOTE: there is no
  reverse-polarity protection by mode, so the silk marking is the only
  defense against a swapped supply.
- **J2 - debug / programming header (STATED as "the MCU's standard debug
  interface").** ASSUMED: 0.1 inch pin header, single row, straight,
  through-hole, carrying whatever the chosen MCU's standard interface is -
  for a Cortex-M part that is SWD (SWDIO + SWCLK), with GND, and with NRST
  brought out if the part's standard programming flow expects it. ASSUMED: no
  trace/SWO pin and no UART bootloader header - the standard debug interface
  alone is what the brief asked for. Whether the header also carries 3.3 V as
  a probe reference pin is open question 2. ASSUMED: any common flying-lead
  SWD probe (ST-LINK / J-Link / DAPLink class) is the tool; no vendor-specific
  10-pin or 20-pin box connector, since packaging is relaxable here.
- **J3 - GPIO header (STATED: "four GPIO brought out to a 0.1 inch
  header").** 0.1 inch pitch, single row, through-hole. ASSUMED: 5 positions
  - the 4 GPIO plus one GND - because a signal with no return is not usable
  at the bench; this is the return path of the stated interface, not an added
  feature. Electrical expectations for the four pins are open question 3.
- **No other external interface exists or is wanted**: no USB, no comms
  connector, no LED, no button, no jumper, no test point, no external
  reset, no expansion header. All excluded by mode.

**What the MCU choice must satisfy** (the brief says "any MCU sourceable at
JLCPCB is acceptable", so the part number is a P1/P3 selection job, not an
owner question - these are the constraints the selection is bound by, and
they are recorded here so the selection is checkable):

1. Single supply, runs correctly across at least 3.0-3.6 V (see section 3);
   no internal or external regulator needed on this board.
2. A standard hardware debug/programming interface on dedicated pins, usable
   with a common third-party probe, and NOT one that has to be multiplexed
   away from the four GPIO.
3. At least four free general-purpose I/O left over after the debug pins and
   any pins the datasheet reserves.
4. Runs and debugs on its internal oscillator - ASSUMED no external crystal,
   because nothing in the brief needs timing accuracy. A part that mandates
   an external clock to be programmed is disqualified rather than accompanied
   by a crystal.
5. No mandatory external components beyond decoupling and whatever the
   datasheet requires on NRST / boot-mode pins. IMPORTANT: if the chosen part
   needs a boot-mode pin held at a defined level to run or to be debugged,
   that resistor is datasheet-required SUPPORT and is in scope - it is not an
   excluded "config strap".
6. Sourceable and assemblable at JLCPCB: in stock, JLC Basic or Preferred
   where one meets the above, and in a package their PCBA line places on the
   top side.

## 3. Power

- **Source: an external 3.3 V rail on J1 (STATED).** What generates that rail
  is NOT stated by the brief - see section 8 and open question 1. There is no
  regulation, conversion, sequencing or power switching on this board
  (STATED), and no second rail (also excluded by mode).
- ASSUMED: the rail is 3.3 V nominal at +/-5 % (3.14-3.47 V), and the part
  selection must tolerate at least 3.0-3.6 V so an ordinary "3.3 V" bench or
  dev-board rail is always inside range. Confirmed or corrected by the answer
  to question 1.
- **Rail budget (GUESS, for sizing only):** a small MCU on its internal clock
  draws roughly 5-30 mA active at 3.3 V, under ~100 mA even for a large part
  running flat out with peripherals on. Board total GUESSED at < 100 mA, i.e.
  < 0.35 W. Nothing on this board is a thermal problem, and the terminal, the
  headers and the copper are all trivially oversized for this current at any
  sane geometry.
- Decoupling per the chosen MCU's datasheet (per-supply-pin ceramics plus any
  bulk it specifies) is datasheet-required support and is IN scope. Filtering
  the datasheet does not require - ferrite beads, pi filters, a separate
  analog supply network the part does not ask for - is excluded by mode.
- No battery on this board, no charging function, no energy storage, no backup
  rail, no supercap, no RTC coin cell. None is stated and none is implied by
  "an external 3.3 V rail".
- Back-feed note (not a safety flag, a bench fact): if question 2 is answered
  "yes, put 3.3 V on the debug header", then the board has two ways in and no
  ORing or protection by mode. Powering it from the probe and the screw
  terminal at the same time is prevented by bench procedure only - the board
  will not enforce it.
- Excluded by mode (SCOPE decisions - do not record any of these as generally
  unnecessary): input TVS/ESD, reverse-polarity protection, fuse, UVLO/OVP,
  input EMI filter, power-good indicator, supply sequencing.

## 4. Environment

Mode defaults - applied, not asked.

- Ambient: 0 to 50 C, indoor bench.
- Cooling: natural convection. No forced airflow, no heatsink, no chassis
  thermal path. Nothing on this board dissipates enough to need one.
- No enclosure. No ingress (IP) rating. No vibration, shock, humidity or
  conformal-coating requirement.
- No formal EMC/emissions campaign - this is a bench study article, not a
  product. Sane decoupling and return-path layout are still required because
  they are what make the block correct, not because a test demands them.

## 5. Size & mounting

- **Outline: no HARD cap, and none may be introduced later.** The brief
  states no dimension, and none is invented here. Under binding `canonical`
  the board size, aspect and outline are OUTPUTS of the placement:
  **RELAXABLE (canonical)** applies to every geometric preference on this
  board, and any dimension that appears at a later checkpoint is a preference
  that LOSES to the canonical layout, with the loss recorded as a
  `state.py decision`.
- Flow that follows from that binding: `board_init --outline auto` at P5
  (generous provisional room - it must NOT be given a fixed size; it will
  refuse one), place to the canonical layout at P6 and pass the `place` gate,
  then `board_edit --outline fit --margin M` so the board becomes what the
  placement needs (re-run `planes_gen` if it grew), then route at P7.
- The honest layout here is driven by the three through-hole connectors and
  by keeping the MCU's decoupling tight to its supply pins - not by heat and
  not by any stated dimension. No planning number is offered deliberately:
  on this board a number would be an anchor with nothing behind it.
- Layers: ASSUMED 2, per the mode's "fewest layers the block honestly needs".
  An MCU with decoupling, three connectors and a ground pour is a genuine
  2-layer board. Not fixed here - if the P2/P4 work shows otherwise, 4 layers
  is allowed under the same rule.
- Mounting: ASSUMED four M3 clearance holes (3.2 mm) inset from the corners
  so the board can sit on standoffs at the bench; two on opposite corners is
  acceptable if the earned outline is too small for four. Mounting the bare
  board is in mode scope; anything beyond it (standoffs, brackets, enclosure
  bosses) is not.
- Height: ASSUMED no maximum. The board is open on a bench with no enclosure,
  and the screw terminal itself stands ~10-12 mm with wire fitted.
- Connector placement: ASSUMED all three connectors on board edges with their
  openings facing outward, power on a different edge from the two signal
  headers, so bench wiring and the probe do not cross the board. Which edges
  is the layout engineer's call at P6.

## 6. Quantity & budget

Mode defaults - applied, not asked.

- Build quantity: 5.
- Cost: minimal, no hard per-unit cap. Prefer JLC Basic/Preferred parts
  wherever one actually meets the requirement; Extended is allowed for the
  MCU if that is where the honest choice lives.

## 7. Assembly

Mode defaults - applied, not asked.

- JLCPCB PCBA, single-sided: all SMT parts on the top side only. The bottom
  side stays clear of SMT so it can carry unbroken return copper.
- The screw terminal and both 0.1 inch headers are through-hole. ASSUMED:
  fitted by JLCPCB through-hole assembly if offered at acceptable cost for
  the chosen parts, hand-soldered after SMT otherwise. Either path leaves the
  schematic and the footprints unchanged.
- Pipeline stops at P9 (fab package + DFM). Ordering is a separate owner
  decision and is not requested here.

## 8. Compliance/safety flags

The mode grants no silence in this section. One flag is genuinely OPEN and
must be answered before the pipeline proceeds; the rest are closed by facts
the brief states.

- **Batteries: CLOSED 2026-08-16 by owner answer to question 1 - NOT a
  battery** (bench supply or another board's 3.3 V rail). The reasoning that
  made it a question is kept below because it is what the answer closed.
  The brief names the
  supply as "an external 3.3 V rail" but never says what generates it. A
  bench supply, a dev board's 3.3 V pin and a battery pack all present that
  way, and battery chemistry/charging is the one thing this pipeline will not
  proceed on as a guess. There is no charging circuit and no cell on this
  board under any answer; the answer decides whether the source has to be
  treated as a battery (discharge behaviour, current limit, deep-discharge)
  in later phases. Answer it and this flag closes.
- **Mains voltage: DOES NOT APPLY.** The board sees 3.3 V DC only and has no
  connection to anything mains-referenced. Generating the 3.3 V is off this
  board and out of scope; if the answer to question 1 is "an off-line
  supply", the isolation lives in that supply, not here - but say so, because
  it changes nothing on this board and everything about how it is handled.
- **High current (>3 A): DOES NOT APPLY.** Maximum current anywhere on the
  board is the MCU's own supply current, GUESSED under 100 mA (section 3),
  more than an order of magnitude below the threshold. Note for question 1:
  the SOURCE may be able to deliver far more than the board draws, and this
  board has no fuse or current limit by mode. At 3.3 V that is not a hazard
  to a person; it is a bench fact worth stating, so it is stated.
- **>30 V: DOES NOT APPLY.** Nothing on the board exceeds 3.3 V. Not a
  boundary case. `check_creepage` stays a clean no-op.
- **Motors: DOES NOT APPLY as specified.** Nothing on this board drives a
  load. If the owner intends one of the four GPIO to drive a motor, a relay
  or any other inductive load (see question 3), this flag re-opens - a GPIO
  driving an inductive load off-board needs a conversation about what comes
  back up that wire, and this board has no protection by mode.
- **RF transmit: DOES NOT APPLY.** No radio function, no antenna, no
  transmitter. An MCU with an unused integrated radio would not change this,
  but a wireless MCU should not be chosen for that reason alone.

## 9. Open questions

Three. Each has a default that is a sensible answer - reply "defaults" and
the pipeline proceeds on all three as written.

1. **What actually supplies the 3.3 V?** (This is the safety question - it is
   the one thing here that will not be guessed.) A bench power supply set to
   3.3 V, the 3.3 V pin of another powered board, a USB-powered breakout, or
   a battery pack? If it is a battery of any kind, say which chemistry and
   how many cells, and whether anything charges it - nothing on this board
   would.
   DEFAULT: a bench supply or another board's 3.3 V rail, indoors, current
   limited to roughly 0.5 A or less, and NOT a battery. On that default the
   rail is taken as 3.3 V +/-5 % and the MCU is chosen to accept at least
   3.0-3.6 V.
2. **Should the debug header carry the board's 3.3 V as a reference pin?**
   Most debug probes want to sense the target's supply voltage before they
   talk to it, and that sense pin is normally wired to the target's own rail.
   Including it costs one header position and creates a second path to the
   power rail on a board that has no protection: if the probe is one that can
   OUTPUT power on that pin, having the screw terminal connected at the same
   time is a bench-procedure rule the board cannot enforce.
   DEFAULT: yes - one 3.3 V pin on the debug header, wired to the same rail,
   for the probe to SENSE only. The board is always powered from the screw
   terminal, never from the probe. Say no if you would rather have the header
   carry only the debug signals and ground.
3. **What are the four GPIO for - do any of them need a particular
   capability?** Whether they are plain on/off pins or need to be, say, a
   UART transmit/receive pair, a PWM-capable output, or an analog input
   decides WHICH pins they are on the chip, and can decide which chip. The
   same question covers what gets connected to them: a scope probe or a logic
   analyser needs nothing extra, but driving an LED, a relay or a motor from
   one of these pins changes section 8 (see the motors flag).
   DEFAULT: four plain digital I/O, 3.3 V logic, no alternate-function
   requirement, no 5 V tolerance, each loaded no harder than the MCU's own
   per-pin current limit (a few mA - a scope probe, a logic analyser, or an
   LED with its resistor sitting off-board). Nothing inductive is driven.

### ANSWERS (owner, 2026-08-16) - all three defaults taken

All three questions are CLOSED. Each answer is also a `state.py decision` in
`state.json`; this section is the design-facing copy. Nothing below is an
assumption any more - later phases treat these as stated requirements.

1. **3.3 V source: a bench supply or another board's 3.3 V rail. NOT a
   battery.** Indoors, current-limited to roughly 0.5 A or less; nothing
   charges and nothing stores energy on this board. The rail is 3.3 V +/-5 %
   and the MCU must accept at least 3.0-3.6 V. Section 8's battery flag is
   closed; the motors and mains flags stay closed too.
2. **Debug header carries 3.3 V, SENSE-only.** J2 is a 5-position 0.1 inch
   single-row header carrying `3V3`, `SWDIO`, `SWCLK`, `NRST`, `GND`. The
   owner fixed the SET; the ORDER was left to the layout engineer and was
   RULED at P1 as **`GND / SWCLK / 3V3 / SWDIO / NRST`** (position 1 to 5) -
   see the P1 decision in `state.json`. 3V3 sits at the centre because that is
   the only arrangement in which a 180 degree reversal of a 5-way shell lands
   the probe's high-Z VTref input on the board's 3.3 V rail instead of a probe
   OUTPUT; GND and NRST take the ends so a reversed probe ground clamps reset
   rather than a data line. The pinout must still be silk-labelled per pin -
   the header has no keying, and the labels are what a hand-wired flying lead
   is read from. The probe senses the rail to set its I/O level. The board is
   powered from J1 only, never from the probe - a bench-procedure rule the
   board does not enforce, as section 3's back-feed note says.
3. **The four GPIO are plain digital I/O.** 3.3 V logic, no alternate-function
   requirement, no 5 V tolerance, no inductive load, each loaded no harder
   than the MCU's own per-pin limit. Pin selection at P4 is therefore free to
   pick whichever four ordinary GPIO give the cleanest escape from the
   package - that is now a LAYOUT criterion, not an electrical one.

### DELEGATION (owner, 2026-08-16)

"Make decisions yourself based on what will give the best learning for the
basic system." Design judgment calls in this run are ruled by the orchestrator
against that criterion and recorded as decisions; H1-H4 are presented as
digests rather than blocking approvals. This delegation relaxes NOTHING that
makes the board true: every gate, the P2/P3 coverage checks and the research
they trigger, DFM, the datasheet's own requirements and every section 8 safety
question stand exactly as written. Money and irreversible steps still go to
the owner - and this board stops at P9 by mode anyway.
