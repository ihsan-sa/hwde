# Requirements: lumina-par (LUM-DTR-PAR-A / LUM-PAR-A)

Sources, in precedence order (later overrides earlier):
1. `brief/00-lumina-system-context.md` - shared system context.
2. `brief/03-rgbw-par-daughter-brief.md` - this board's brief.
3. `brief/01-carrier-board-brief.md` - the mating carrier, CONTEXT ONLY.
4. `brief/05-lumina-closed-decisions.md` - BINDING; supersedes the open-decision
   table in `00` s6 and corrects figures in `00` and `03`.
5. `brief/06-connector-icd.md` - FROZEN interface control document (ICD-01),
   owned by LUM-CAR-A. Hard input. Never redefined here.

Unstated low-risk items are marked `ASSUMED:` inline. Section 9 holds every
unknown that changes the design or touches safety. Section 8 flags one
>30 V condition that is unconditional (48 V is on the connector whether or
not this board taps it) and one conditional >3 A condition.

Two figures in the briefs are dead and are NOT used anywhere below: the
"~8.5 W sustained" daughter budget in `00` s5.1 and `03` PAR-REQ-11, and the
Si3402-B / AN956 "~10 W regulated" it derives from. The carrier uses a
TPS2378-class PD controller plus a 100 V buck; the re-derived budget is
**8.6-9.3 W (af) / 18.7-20.0 W (at)**. PAR-REQ-11 itself still holds hard.

---

## 0. Formal amendments (owner decision at H1, 2026-07-28)

These requirements were **changed by decision at the H1 checkpoint**, not quietly
failed. The original text is quoted in full so the record shows exactly what was
altered and why. Both amendments follow from the H1-Q4 decision: **same-reel
sourcing, with the EEPROM fitted but shipped empty**, because no colour-measuring
instrument exists for this build today.

### AMD-01 - PAR-REQ-16 changes from a binning specification to a same-reel sourcing requirement

> **Original (brief `03` s4, PAR-REQ-16):** "LED binning specified in the BOM for
> all four channels. Unbinned parts across 8 fixtures will not satisfy
> PAR-REQ-06."

**Amended to:** *All emitters for the whole build shall be procured in a single
transaction from a single reel per part number, and the reel/date code shall be
recorded in the build record. A chromaticity or flux bin shall be specified in the
BOM wherever the vendor publishes one; where the vendor publishes none, the
same-reel requirement stands in its place.*

**Why it could not be met literally:** LCSC/JLC does not generally expose a
chromaticity or flux bin as an orderable attribute, and the selected emitter
vendor publishes no bin data at all (`research/led-emitter.md` s9). A BOM line
demanding a bin that cannot be ordered is unbuildable. Parts from one reel are
same-batch and closely matched in practice, which is the outcome PAR-REQ-16 was
written to obtain. **This is a genuine reduction in guarantee, not an equivalent
substitution:** same-reel is an empirical correlation, whereas a published bin is
a contractual limit. PAR-REQ-06 (consistent colour across fixtures) is therefore
carried at **reduced confidence** and its verification moves to a bench comparison
of the assembled fixtures.

### AMD-02 - PAR-REQ-17's calibration data is deferred, not the hardware

> **Original (brief `03` s4, PAR-REQ-17):** "Provide for per-fixture calibration:
> measured per-channel scaling stored in the daughter board's ID EEPROM
> (CAR-REQ-07, EEPROM option) so firmware can normalise fixtures to each other.
> If the resistor-divider ID option is chosen instead, calibration has to live on
> the host, and that trade must be made deliberately."

**Amended to:** *The board shall fit the ID divider bottom leg AND a 24C32 I2C
EEPROM. The EEPROM ships **empty**: per-channel scaling coefficients are not
measured or populated for the first build. The provision is retained so that
calibration can be added later without a respin.*

**Why:** the premise that EEPROM and divider are alternatives is not what ICD-01
says - s2/s3.3 has them coexisting, the divider carrying board type and the
EEPROM per-unit calibration, which is why the second dedicated ID pin was deleted.
So the "deliberate trade" the original text asks for does not arise; both are
fitted. What is genuinely deferred is the **data**, because there is no
colorimeter or spectrometer in this project today (H1-P10). **Consequence to
carry:** until the EEPROM is populated, fixture-to-fixture matching rests entirely
on AMD-01's same-reel sourcing.

---

## 1. Function

The colour and mood workhorse of the LUMINA fixture set: an RGBW par daughter
board that stacks above the universal LUM-CAR-A carrier on the frozen ICD-01
expansion connector and turns four (possibly five) carrier PWM channels into
four independent constant-current LED drives. It runs continuously rather than
in bursts, so its problem is not peak power but quality of dimming and
consistency between the 6-8 fixtures in the room: visually stepless dimming at
low output, slow hue drift over tens of seconds with no banding, and no
per-fixture tint variation in a synchronised full-room wash. It carries LED
drivers, thermal sensing, an independent over-temperature shutdown, the ENABLE
gate, the board ID leg and the calibration store - and nothing else. It has no
MCU, no network interface, no external connector of any kind, and no energy
store for burst output (that is the strobe board's problem, not this one's).

---

## 2. Interfaces

**Every interface on this board is through ICD-01. There are no others.**
ICD-01 s9 is explicit: a daughter may not add an external connector of any
kind - no barrel jack, no DMX, no second Ethernet. Ethernet on the carrier is
the fixture's only external connection, and that is what makes the
non-isolated PoE topology compliant.

### 2.1 J3 - POWER block, 2x7, daughter side

- Part: **CONNFLY DS1023-2*7SF11** socket (14 pos, 2.54 mm, 600 V,
  3 A/contact, 8.5 mm body). Second sources on the same land pattern:
  HanElectricity 2541FV, Boomele 2.54-2*7P, HCTL HC-PZ254. JLC Extended -
  there is no JLC Basic part in any board-to-board family, so "prefer Basic"
  is unachievable here and is not a selection error.
- **Reverse-mounted on the daughter's BOTTOM side, facing down** (ICD s7.3).
- Pin map (ICD s3.1), authoritative, do not re-derive:
  1/3/5 `+48V_SW`; 2/4/6/7/8/10/13 `GND`; 9/11 `+12V`; 12/14 `+3V3`.
  Position 1 silkscreen-marked with a triangle.
- Rail order along the connector is 48 -> GND -> 12 -> 3.3 so that no
  single-position mis-seat can put a higher rail on a lower rail's pin.

### 2.2 J4 - SIGNAL block, 2x12, daughter side

- Part: **CONNFLY DS1023-2*12SF11** socket (24 pos, 600 V, 3 A/contact,
  8.5 mm body), same mounting rules and same second-source situation.
- Pin map (ICD s3.2), authoritative: `PWM0..7` at positions 1,2,5,6,7,8,11,12;
  `GND` at 3,4,9,10,13; `DSPI_SCK` 14, `MOSI` 15, `MISO` 16, `CSn` 17;
  `I2C_SCL` 18, `SDA` 19; `ADC0` 20, `ADC1` 21; `ID_ADC` 22; `ENABLE` 23;
  `FAULT` 24. **No 48 V exists anywhere on this connector.**

### 2.3 Signal contract (ICD s3.3) - what this board must honour

| Signal | Requirement on this board |
|---|---|
| `PWM0..7` | 3.3 V push-pull, **13-bit at 9.766 kHz default** (CAR-REQ-12). PWM0-3 = LEDC timer 0, PWM4-7 = timer 1; channels on a timer share frequency AND resolution. `ASSUMED:` R,G,B,W map to PWM0-3 (timer 0); a 5th channel (question 4) takes PWM4 on timer 1, programmed identically. LEDC timers 2 and 3 are unallocated and available on request - that is the only sanctioned route to a different PWM frequency for this daughter, and it needs the carrier owner's agreement, not a unilateral change. |
| `I2C_SCL/SDA` | 400 kHz open drain. **Pull-ups are on the carrier (4.7 k). This board must NOT fit its own.** The daughter owns the whole address space; the carrier reserves nothing - so EEPROM and any digital temp sensor must be allocated non-colliding addresses here. |
| `ADC0`, `ADC1` | daughter -> carrier, 0-3.3 V, **source impedance <= 10 kohm**. This is the PAR-REQ-12 thermistor path; an NTC divider must be sized to meet the 10 kohm ceiling at every temperature of interest. |
| `ID_ADC` | The carrier fits the TOP leg (10 k to +3V3); **this board fits the BOTTOM leg to GND**. The code value is allocated by the carrier owner, not chosen here - see question 15. |
| `ENABLE` | carrier -> daughter, push-pull, **active HIGH**. This board must fit its own **100 kohm pull-down**, gate **every** output stage with it (driver EN pins, any gate driver, any charge path), and **never latch it locally**. A carrier PWM pin can glitch ~60 us at power-up; ENABLE is what makes that a no-op. |
| `FAULT` | daughter -> carrier, **open drain, active low**, 10 k pull-up on the carrier, wire-OR'd with the carrier's eFuse fault. **Never drive it high.** |
| `DSPI_*` | Available, <= 26 MHz, mode 0, shared bus with one CS. Not expected to be needed by a 4-channel PWM design; a daughter needing more devices decodes locally. |

### 2.4 LED interface

Emitters are the board's real load and their mounting is **not settled** - on-board
emitters versus an off-board module on a separate heatsink with an internal wiring
harness is question 5, and it interacts with ICD s9's external-connector ban
(an internal harness inside the enclosure is not an external connector, but
this needs confirming, not assuming). Optics (PAR-REQ-14 wide wash beam from a
2.5 m ceiling, PAR-REQ-15 diffusion sufficient that R/G/B/W mix before reaching
a surface) may or may not be in this run's scope - question 8.

### 2.5 Status / test points

No requirement stated. `ASSUMED:` no user-visible indicators on this board -
CAR-REQ-09 status indication lives on the carrier. Any test point fitted must
carry the ICD s9 bench-hazard warning: the entire fixture floats at PoE
potential, and an earthed scope probe or non-isolated USB-UART adapter does not
merely risk damage, it **breaks PD signature detection outright** (detection
currents are a few hundred microamps).

---

## 3. Power

### 3.1 The envelope (binding)

| | 802.3af (first build) | 802.3at (upgrade path) |
|---|---|---|
| **Sustained power to this daughter, all rails combined** | **8.6-9.3 W** | **18.7-20.0 W** |

D-01 is closed: the carrier's PD front end, converter, magnetics and thermal
design are sized for **Type 2 (at)**, but classification is programmed to
**Type 1 (af)** for the first build via a class resistor. The upgrade is a
resistor change plus a PoE+ switch, **no respin**. D-01 says explicitly: *do
not allow any other component to become the part that pins the design to
Type 1.* On this board that clause lands on the LED drivers, the emitters and
the heatsink - see question 2, which is the highest-consequence open item in
this document.

### 3.2 Per-rail ceilings (ICD s6.2) - individual ceilings, the TOTAL binds

| Rail | Sustained af | Sustained at | Peak (ms, local bulk) | Hardware fault ceiling |
|---|---|---|---|---|
| `+48V_SW` | 0.25 A (12.0 W) | 0.50 A (24.0 W) | 1.0 A | 1.0 A eFuse, **latch off** |
| `+12V` | 0.75 A (9.0 W) | 1.25 A (15.0 W) | 2.0 A | 2.0 A converter OCP |
| `+3V3` | 0.25 A (0.83 W) | 0.25 A | 0.50 A | 1.0 A converter, limit >= 1.3 A |

**Derived, and load-bearing: the +12V rail alone cannot cover this board's
envelope at either class.** At af it needs 0.72-0.78 A against a 0.75 A ceiling
(right at the edge); at at it needs 1.56-1.67 A against a **1.25 A** ceiling,
which it misses by 3.7-5.0 W. ICD s6.3 is unambiguous: *anything above 1.25 A
at the at operating point must be taken on `+48V_SW`*, and the 1.25 A ceiling
is a thermal limit on the carrier's 48->12 converter in a sealed box, not a
current rating that can be argued with. Taking power on `+48V_SW` instead of
`+12V` is also worth **0.67 W (af) / 1.30 W (at)** of extra delivered power
because it skips a conversion.

`ASSUMED:` for an **af-sized** board, LED power is taken from `+12V`, which is
D-02's stated purpose for that rail (so 6-8 fixtures do not each duplicate a
>= 60 V converter). If question 2 answers "size for at", that assumption is
void and P1 must take at least part of the load from `+48V_SW`, inheriting the
bleed path, the 0.60 mm creepage regime, 100 V capacitors, 0805-or-larger
resistors across the 48 V domain, and the inrush obligation below.

### 3.3 Hard rules inherited from the ICD

- **Hardware backstop for PAR-REQ-11.** The clamp is a firmware rule, but
  firmware fails. With ENABLE asserted and every PWM stuck at 100 % (hung MCU;
  the 2 s watchdog fade cannot help if the MCU is the thing that hung), the
  board's total draw must remain **below the carrier's hardware fault
  ceilings** - 12 V OCP 2.0 A, 48 V eFuse 1.0 A latch-off, PSE overload timer
  ~50-75 ms. A board that can only meet the budget when firmware is healthy
  will brown out or latch off the whole fixture. This sizes the per-channel
  drive current and is not optional.
- **`+48V_SW` is dead at power-up and stays dead for hundreds of ms.** The
  carrier's load switch is a compliance part (802.3 caps PD port capacitance at
  ~180 uF); it closes only after firmware asserts ENABLE. Design for it.
- **No first-mate/last-mate sequencing exists.** The board must tolerate 48 V
  arriving before or after 3.3 V, in either order.
- **No path may energise anything on this board from `+12V` or `+3V3` while
  `+48V_SW` is off**, or the 802.3 inrush compliance is defeated behind the
  switch's back.
- **Inrush is this board's responsibility** (CAR-REQ-14). Size the limiter
  against the **PD's 1.0 A operating current limit**, not the connector's
  5.4 A rating; sizing against the connector is the classic way to trip the
  PD's 800 us foldback deglitch and brown out the fixture.
- **If any 48 V net is tapped: a bleed path is mandatory** (CAR-REQ-17 /
  STR-REQ-10). The carrier deliberately fits no series diode on `+48V_SW`, so
  the daughter's bleed is not stranded above the carrier's 100 k.
- **0.60 mm outer-layer copper clearance around every 48 V net, board-wide,
  is NOT inherited automatically** - this board's DRC must be set up for it at
  P5 (IPC-2221B B2, 51-100 V band, 57 V worst case). The 0.13 mm coated column
  is not claimable: LPI soldermask is not a qualified conformal coating and
  `check_creepage.py` implements only the uncoated columns, so a layout
  designed to 0.13 mm fails P8 with no waiver mechanism.

### 3.4 LED-side budget (ESTIMATES, clearly marked as such)

GUESS, for question sharpening only, to be replaced by a real power table at
the P1/P2 design gate (`03` review gate 1):

- Daughter housekeeping (driver quiescent, ID/EEPROM, sense): **~0.3-0.5 W**.
- Switching CC driver efficiency: **~88-92 %**.
- Therefore electrical power reaching the emitters: **~7.6-8.5 W (af)** /
  **~16.5-18.4 W (at)**.
- A typical 4-in-1 RGBW multi-die emitter (R AlInGaP ~2.1-2.9 V, G/B InGaN
  ~3.0-3.6 V, W ~2.9-3.4 V) draws roughly **4.0-4.7 W at 350 mA/die** and
  **8.4-9.8 W at 700 mA/die** with all four dies on. So **one** such emitter at
  ~600-700 mA/die consumes the entire af envelope by itself; the at envelope
  buys roughly double.
- Note for P1, not a decision here: PAR-REQ-10 forbids burning the R-vs-GBW
  forward-voltage spread in a shared linear element, and a 12 V rail against a
  2.1-3.6 V single die is a 3.3-5.7x step-down. That combination rules out
  shared linear current control and points at either per-channel switching
  regulators or multi-die series strings per channel. It also interacts with
  question 3 (package choice).

No battery, no charging, no mains anywhere in this system.

---

## 4. Environment

- Deployment: indoor, basement/garage room ~5 m x 7 m x 2.5 m, 8-12 fixtures,
  ceiling-mounted at ~2.5 m. `ASSUMED:` ceiling mount, beam pointing into the
  room; no vibration or shock requirement; no ingress rating (question 6
  decides sealed vs vented, which is a thermal question, not an IP one).
- `ASSUMED:` external ambient 0-40 C. Not stated anywhere in the briefs.
- **Internal enclosure air reaches 56 C (af) / 69 C (at)** per ICD s7.6. This
  is the ambient the emitters and drivers actually see, not room temperature.
- **Continuous duty with no relief.** Unlike the strobe, this board runs hot
  all the time (`03` review gate 4, and H1-Q5 restates it). Every thermal
  number must be a steady-state number.
- Heat this board must reject (ESTIMATE: LEDs convert ~20-35 % of electrical
  input to light, the rest to heat): **~6.5-8.4 W (af)** / **~14-17 W (at)**,
  plus the carrier's own 2.4 W (af) / 3.7 W (at) in the same box.
- **This is the riskiest number in the document.** With internal air at 69 C
  and a red-die junction that wants to stay near 85-100 C for colour and
  lifetime stability, the junction-to-internal-air thermal budget at the at
  operating point is roughly **1.0-1.1 C/W**, and at af roughly 2.3 C/W. A
  sealed plastic box has no convective path out. Questions 6 and 7 exist
  because the at case very likely does not close without either ventilation or
  an external heat path, and H1-Q5 constrains both (non-conductive enclosure,
  heatsink NOT user-accessible).
- Connector contacts are rated -40 to +105 C, so they are not the limit.

---

## 5. Size & mounting

All of the following is the **common LUMINA footprint** from ICD s7.1, which
every board inherits. It is proposed, not yet confirmed with the human -
MECH-02 requires the outline to be closed at H1 **before P5**, because
`board_init.py` binds the outline permanently and ai-ee has no outline-shrink
step. See question 12.

| Item | Value |
|---|---|
| Outline | **100.0 x 80.0 mm** |
| Corner radius | **3.0 mm**, all four corners |
| Mounting holes | **4x M3 (3.2 mm) at 5 mm inset** (a 90 x 70 mm rectangle) **plus a 5th M3 at (46, 74)** |
| Thickness | 1.6 mm |
| Coordinate origin | board top-left, x right, y down |
| Mated board-to-board height | **11.0 mm** hard-seated |
| Standoffs | 5x M3 female-female, 11.0 mm |

### 5.1 The RJ45 notch - hard requirement from P2 onward

**A 30 x 26 mm notch in the TOP edge, region (6, 0) - (36, 26).** The carrier's
board-edge magjack is ~15 mm tall against an 11.0 mm stack, so it protrudes
~4 mm above this board's underside. The outline rectangle, corner radius and
5-hole pattern are unchanged; only this local relief differs. It is also the
**primary anti-180-degree interlock** (CAR-REQ-16): rotated, the notch lands at
the bottom edge and the board presents solid material over the jack, so the
boards cannot be forced flat. That is a mechanical stop, not a warning.

### 5.2 Exclusion zones (ICD s7.6) - all four apply to this board

| Zone | Region | Rule |
|---|---|---|
| RJ45 relief | (6, 0) - (36, 26) | cut away entirely (s5.1) |
| DC-DC hot zone | (2, 46) - (36, 68) | **no LED drivers and no aluminium electrolytics** - the carrier's 48->12 converter dissipates up to 1.25 W directly below, and in a stacked mezzanine this board's parts sit vertically over it |
| Antenna column | (88, 25) - (100, 55) | **no copper on any layer, no metal component** - the carrier's ESP32-S3 PCB antenna is 11 mm below and Wi-Fi is a supported control path (H1-Q8) |
| Recovery header | (76, 0) - (98, 20) | keep clear enough for a 6-way jumper lead with this board fitted, or accept board removal for firmware recovery |

### 5.3 Connector positions - PROVISIONAL, and this board is blocked on them

ICD s7.2 gives J3 body (14, 68)-(34, 78) with position 1 at (15.3, 69.3), H5 at
(46, 74), J4 body (56, 68)-(88, 78) with position 1 at (57.3, 69.3). **ICD s7.2
is the one section not frozen at H1**: the carrier owner must compare placed
positions after its own P6, correct them, and re-issue. Daughters are
explicitly blocked on that re-issue. See question 16.

Mating geometry to verify at P4/P6, not to re-derive: this board's sockets are
**bottom-side, facing down**, and mate with a top-side header on the carrier.
Plan-view (x, y) coordinates are shared between the two boards, but pin
numbering mirrors across the row on a bottom-side footprint - pin 1 alignment
must be checked in the mated view, not assumed from the footprint.

### 5.4 Pipeline facts that constrain P5 (verified in this repo, not assumed)

- `board_init.py --mounting-holes N` places holes at **inset = margin / 2**
  (confirmed in the script). The ICD's 5 mm inset therefore requires
  **`--margin 10`**, not the default 6. The corner radius is separately clamped
  in the worker; read the report's `corner_radius` field and `worker_notes`
  rather than assuming the requested 3.0 mm was honoured.
- **`board_init.py` has NO notch/cutout option** (`--outline` takes only `auto`
  or `WxH`), and `kc.py` exposes no outline-editing subcommand. The mandatory
  30 x 26 mm relief must therefore be produced by a direct Edge.Cuts edit of
  the `.kicad_pcb` after `board_init`, with every downstream consumer
  (`place_*`, `planes_gen`, `dfm_check`, `fab_export`) re-verified against the
  modified outline. **Flagged as an implementation risk for P5**, not a
  requirements question - the notch itself is non-negotiable.
- Placement keepouts ARE supported: `constraints.json` accepts
  `placement.keepouts: [{"rect": [x1,y1,x2,y2], "reason": ...}]` and the
  annealer treats them as fixed obstacles. All four ICD s7.6 zones plus the
  notch region must be declared there.

### 5.5 Height

Board-to-board is 11.0 mm. **Total height above this board is unknown** and
depends on the emitter/heatsink/optic stack (questions 5-8). Not stated
anywhere in the briefs.

---

## 6. Quantity & budget

- **Quantity: 6-8** par fixtures out of 8-12 total (`03` s1). Exact count and
  spares not stated - question 14.
- System budget: **$500-1000 for fixtures + switch + enclosures** (`00` s1).
  ICD s1.1 rejects a Samtec pair at $15.30 "over half the $30/board target",
  so a **$30/board** figure exists in the carrier run - but no unit cost target
  has been stated for *this* board. With 8-12 fixtures, a managed PoE+ switch
  (note: D-01's upgrade path implies PoE+, which is materially more expensive
  than the PoE switch the original budget assumed), enclosures, carriers,
  strobes and pars all inside $500-1000, this is tight. Question 14.

---

## 7. Assembly

- `ASSUMED:` JLCPCB fabrication and PCBA, consistent with every other board in
  this repo. Not stated in the LUMINA briefs.
- **Both ICD connectors are 2.54 mm THT sockets that must be reverse-mounted on
  the bottom side.** That is not a normal JLC PCBA process, so the realistic
  routes are hand-soldering them post-PCBA or finding a bottom-side SMD
  equivalent on the same land pattern (ICD s7.3 permits "a bottom-side SMD
  equivalent"). Question 13.
- High-power emitters, if on-board, need a large thermal pad and a via farm on
  1.6 mm FR4 - or an MCPCB, which the common footprint does not provide.
  Interacts with questions 5 and 13.
- Sidedness: bottom side already carries the two sockets, so the board is
  double-sided by construction. Question 13 confirms the process.

---

## 8. Compliance / safety flags

| Flag | Status |
|---|---|
| Mains voltage | **No.** PoE only. |
| Batteries | **No.** No battery, no charging anywhere in the system. |
| Motors | **No.** |
| **> 30 V** | **YES, unconditionally.** `+48V_SW` is present on J3 whether or not this board taps it. PD rail 37-57 V nominal, **57 V worst case** (IEEE 802.3 PSE maximum). Consequences: 0.60 mm outer-layer clearance around every 48 V net board-wide; 100 V capacitors (63 V is not enough at 57 V once ceramic DC-bias derating applies); any resistor across the 48 V domain must be 0805 or larger, or split in series; the clearance applies through the board (inner 0.10 mm / outer 0.60 mm under any 48 V antipad); mandatory bleed path if tapped. **Insulation class is functional only** - 57 V is below the IEC 62368-1 ES1 limit of 60 V DC, so no personnel safeguard and no safety-mandated creepage applies, and an unearthed PD needs **no MOV-to-earth surge network** (do not copy one from a reference design). |
| High current (> 3 A) | **Conditional - architecture must report and re-flag.** No connector rail exceeds 1.25 A. But LED-side per-channel current is unbounded by the ICD: a single low-Vf red channel sized near the whole envelope (e.g. 8 W into a ~2.4 V string) would be ~3.3 A. P1/P2 must publish per-channel drive currents; if any exceeds 3 A this flag becomes unconditional. |
| RF transmit | **No radio on this board** - but the carrier's ESP32-S3 radio is a *supported control path* (H1-Q8), so the (88, 25)-(100, 55) antenna column is a hard keepout (no copper on any layer, no metal component) and switching LED drivers 11 mm above a 2.4 GHz PCB antenna are a desense risk that layout sign-off must address. |
| **Floating PoE potential** | **Applies to everything this board touches.** The entire fixture is non-isolated and floats at PoE potential: this board, its drivers, its LED wiring, and any heatsink the LED module sits on. 802.3 compliance is achieved *only* by there being no accessible external conductor. This is ICD s9 / `decisions.md` OPEN-C and it is **unresolved** - questions 5 and 7. |
| **Continuous hot surface** | High-power LEDs at 8.6-20 W continuous inside a non-conductive enclosure whose internal air already reaches 56-69 C. Enclosure touch temperature and plastic deformation are real; H1-Q5 requires the heatsink to be non-user-accessible. |
| **Photobiological (IEC 62471)** | A high-power RGBW source with a wash optic is plausibly Risk Group 1-2 at close range (blue-light hazard). Not a certification requirement for a private installation, but worth a note in the design doc rather than discovering it by looking into a fixture. |
| Certification | `ASSUMED:` private installation, own use - no CE/FCC/UL conformity assessment path required. |

**Nothing in section 8 is guessed.** The >30 V condition and the floating-PoE
condition are stated facts from the ICD; the >3 A condition is explicitly left
open for the architecture to answer.

---

## 9. Open questions

Questions 1-4 are the four the orchestrator already queued, sharpened with the
numbers above. Questions 5-16 are everything else this design genuinely needs.
Each offers a recommendation. Questions **2, 6, 7 and 12** are the ones that
change the board most, and 12 and 16 must be answered before P5 regardless.

**1. Total-power clamp policy (PAR-REQ-11).** Four channels cannot all run at
100 % - the sum of four channels at full drive exceeds the 8.6-9.3 W (af)
envelope by roughly 30-60 % on any sane sizing. When the host asks for more
than the fixture can deliver, what should the fixture protect?
(a) **Preserve hue**: scale all four channels by the same factor. The colour is
exactly right; the fixture is simply dimmer. White (all four on) is the worst
case and gets dimmest.
(b) **Preserve brightness**: hold the total at the cap and reallocate between
channels. Brightness is stable; the hue drifts toward whichever channel is
cheapest in watts, and drifts *differently* per fixture, which is exactly the
artifact PAR-REQ-06 exists to prevent.
(c) Hybrid: preserve hue, let the white channel absorb the deficit - this
desaturates at high intensity, the "visible artifact, not graceful
degradation" the brief warns about.
**RECOMMEND (a).** Uniform hue-preserving scaling. Colour consistency across
6-8 fixtures washing one wall is this board's reason to exist; a uniform
brightness loss is invisible, a hue split across fixtures is not. Note that
whichever answer is chosen, the **hardware backstop in s3.3 is still required**
- the board must be electrically incapable of exceeding the carrier's fault
ceilings with every PWM stuck at 100 %.

**2. Size the LED engine for af or at?** D-01 kept the *carrier* at-capable and
af-classified, and told us not to let any component pin the design to Type 1.
Does that clause bind this board's LED engine too?
(a) **Size for af (8.6-9.3 W)**: smaller emitter, smaller heatsink, cheaper,
thermally plausible in a plastic box - but a PoE+ upgrade then buys nothing on
the par because the emitters and heatsink cannot use the extra ~10 W, and
getting it later is a respin of this board.
(b) **Size for at (18.7-20.0 W), run clamped at af**: the upgrade is a firmware
constant. But it roughly doubles heatsink area and emitter cost per fixture,
and - derived above - **it forces at least 3.7-5.0 W to be taken from
`+48V_SW`** because the +12V rail tops out at 15.0 W, which means a >= 60 V
input stage on this board after all, the thing D-02's 12 V rail was created to
avoid on 6-8 fixtures.
**RECOMMEND (a) for the first build, with a written note in the design doc that
the par does not follow the carrier's at upgrade.** The par is a sustained
wash, not the fixture that needs the headroom; the strobe is. Spending the at
budget on the par costs money and heatsink on all 6-8 units to buy brightness
the profiles ask of the strobe. But this is a lighting-design call, not an
engineering one - if a 9 W par reads as underwhelming, (a) is a respin.

**3. LED package: four discrete emitters or an integrated RGBW multi-die?**
(a) **Integrated 4-in-1** (single package, four dies on one thermal slug):
mixes better optically and largely solves PAR-REQ-15 fringing; one thermal
interface; one binning transaction. All four dies share one junction
temperature, so the hottest channel heats the others, and red (AlInGaP) is both
the most thermally sensitive and the one that gets cooked.
(b) **Four discrete emitters**: independent thermal management, cheaper and
easier sourcing, per-channel binning - but four separate optical sources need
real diffusion to avoid visible R/G/B/W shadow fringing on a wall (PAR-REQ-15),
and four packages spread over the board is four thermal paths to solve.
**RECOMMEND (a) integrated 4-in-1**, on the grounds that PAR-REQ-15 is a hard
optical requirement and mixing is the one thing an integrated package gives for
free. Note the interaction with s3.4: a 12 V rail against a single 2.1-3.6 V
die is a 3.3-5.7x step-down, which pushes toward per-channel switching drivers
either way.

**4. A fifth channel (amber)?** PWM budget is free - the connector carries 8
channels and the par uses 4, and PWM4 sits on LEDC timer 1 which can be
programmed to the same 13-bit/9.766 kHz. So the cost is not connector budget,
it is: one more driver, and a fifth channel drawing from the **same** 8.6-9.3 W
envelope, making the question-1 clamp bite harder in every mixed colour.
P3 French melodic leans on gold/amber and RGBW amber is a mix rather than a
true emitter. Caveat worth weighing: amber AlInGaP loses output at roughly
-0.5 to -1 %/C of junction temperature, roughly twice as badly as the InGaN
channels, in a box whose internal air is already at 56-69 C continuously - so a
calibrated amber will drift visibly as the fixture warms up unless it is
temperature-compensated in firmware.
**RECOMMEND: no fifth channel on rev A.** Add it only if question 2 answers
"size for at" (where there is power to spare). At af it dilutes the envelope
across five channels and adds the most thermally unstable emitter in the
catalogue to a board that already has a thermal problem.

**5. LED mounting and wiring: on-board emitters, or an off-board LED module on
a separate heatsink?**
(a) **On-board**: emitters on this PCB's top side, heat through thermal vias
into a heatsink bolted to the board. No wiring at all, so ICD s9 is trivially
satisfied - but 1.6 mm FR4 is a poor thermal path, the common footprint gives
no MCPCB, and the emitters' position is then dictated by the connector/keepout
geometry rather than by the optics.
(b) **Off-board module** on its own MCPCB/heatsink, connected by an internal
wiring harness (5-9 conductors). Best thermal and optical freedom. **ICD s9
bans a daughter from adding "an external connector of any kind" - a harness
that never leaves the enclosure is not an external connector on any reasonable
reading, but this needs confirming, not assuming**, because if it is read
strictly then option (b) is illegal and option (a) is the only route.
**RECOMMEND (b), with explicit confirmation that an internal wire-to-board
connector (e.g. a JST-family header) is permitted** on the grounds that ICD s9's
intent is "nothing penetrates the enclosure wall", and s9 itself already
anticipates the off-board case ("if the LED module is on a separate heatsink
(Q4a default), that heatsink and its wiring are at PoE potential too"). If the
answer is a strict no, please say so plainly - it forces (a) and changes the
thermal design completely.

**6. Is the enclosure sealed, or vented?** ICD s7.6 says "sealed box" with
internal air at 56 C (af) / 69 C (at); H1-Q5 says plastic, non-conductive, with
the heatsink not user-accessible. No ingress requirement is stated anywhere.
This matters more than any other mechanical question: from s4, a *sealed*
plastic box gives a junction-to-internal-air budget of ~2.3 C/W at af and
~1.0 C/W at at, and the at case very likely does not close.
(a) Fully sealed (no openings at all).
(b) **Vented** - louvres or a labyrinth sized so no finger or 4 mm probe
reaches live parts or the heatsink, preserving H1-Q5's non-accessibility while
allowing convection.
(c) Sealed but with the heatsink forming part of the enclosure wall (see
question 7).
**RECOMMEND (b) vented with a finger-guard geometry.** It is an indoor
basement/garage installation with no stated dust or moisture requirement, and
convection is close to free. Sealing costs real money in heatsink area and
caps the fixture's output.

**7. Is an external or enclosure-integrated heat path allowed?** ICD s9 and
`decisions.md` OPEN-C leave this open and it is the sharp end of the
non-isolated topology: any heatsink bonded to this board's ground **floats at
PoE potential**, and "if the heatsink is touchable, metal, or shares a mount
with anything earthed, the non-isolated topology is non-conformant."
(a) Heatsink entirely internal, no metal reaches the outside. Thermally worst,
compliance-simplest.
(b) Heatsink forms part of the enclosure but is shrouded behind a plastic
guard - not touchable, and not sharing a mount with anything earthed.
(c) Exposed metal heatsink - **would break the compliance argument** unless the
whole fixture is re-isolated, which is out of scope.
**RECOMMEND (b)**, plus a hard rule that the ceiling mount is non-conductive
and bonded to nothing. Also please confirm: should the LED module's metal
substrate be electrically tied to board GND, or thermally coupled but
electrically floating? (Recommend: floating from board GND, on a dielectric,
so a single insulation failure does not put 48 V-referenced potential on the
heatsink.)

**8. Does this run own the optics?** PAR-REQ-14 (wide wash beam from 2.5 m,
overlapping coverage from 6-8 fixtures) and PAR-REQ-15 (diffusion sufficient
that the colours mix before reaching a surface) are stated as requirements on
this board, but a PCB run can only choose the emitter and provide mechanical
provision for a lens or diffuser.
(a) This run selects the emitter and provides lens-holder mounting provision;
the diffuser/lens is an enclosure item chosen later.
(b) This run owns the full optical chain including the lens/diffuser part
numbers and beam-angle verification.
**RECOMMEND (a)** - a PCB pipeline cannot verify a beam angle, and PAR-REQ-14 /
15 should be carried as enclosure requirements in the design doc so they are
not silently lost.

**9. What does "5-10 % of full output" mean in PAR-REQ-01?** This changes the
required driver PWM bandwidth by roughly 40x and it is the single most likely
reason this board fails its own review gate 2.
At 13-bit / 9.766 kHz the period is 102.4 us and one LSB is **12.5 ns** - no
constant-current driver on the market resolves that, so the real dimming floor
is the driver's PWM settling time, not the PWM word length.
(a) **5-10 % of PWM duty**: on-time 5.1-10.2 us. Most switching CC drivers
manage this at 10 kHz with some amplitude error.
(b) **5-10 % of perceived brightness** (i.e. after gamma ~2.2): duty is
0.137-0.63 %, on-time **141-646 ns**, which is at or below the settling time of
essentially every CC driver and is where "visible stair-stepping during slow
fades" is actually born.
`CORRECTED 2026-07-28 (orchestrator, verified):` this line previously read
"on-time 1.4-6.1 us", a 10x error. The duties were right; the on-times were
not. 0.05^2.2 x 102.4 us = 140.6 ns and 0.10^2.2 x 102.4 us = 646.1 ns. The
correction is load-bearing: it moves (b) from "several drivers manage it" to
"no surveyed CC driver manages it with PWM alone" - the best part found in P1
(TPS92515HV) specs a 0.2 % minimum duty at 10 kHz, i.e. a 200 ns floor, which
is above the 141 ns that 5 % perceived requires. See `research/led-driver.md`
and `research/spec-dimming.md`.
**RECOMMEND: assume (b)**, because that is what a lighting person means by
"dim to 5 %", and it is the harder requirement - designing for (b) satisfies
(a) automatically. Please confirm, because it materially narrows the driver
shortlist and is the requirement PAR-REQ-09 is really about.

**10. Calibration path (PAR-REQ-17) - and who does the measuring?** The premise
that this is EEPROM *versus* the resistor divider is **not what the ICD says**.
ICD s2 and s3.3: the carrier fits the top leg of the `ID_ADC` divider and the
daughter fits the bottom leg **and** an I2C EEPROM may ride the shared I2C bus;
a second dedicated ID pin was deleted precisely because the EEPROM does not
need one. So the two mechanisms coexist: **the divider says what board type
this is, the EEPROM stores per-unit calibration.** A 24C02/24C32-class part is
a few cents and one address allocation (this board owns the whole I2C address
space - the carrier reserves nothing - so EEPROM and any digital temp sensor
must be allocated non-colliding addresses).
**RECOMMEND: fit both.** The real open question is downstream: PAR-REQ-06
requires measured per-channel scaling, so **what instrument measures 6-8
fixtures?** (colorimeter / spectrometer / phone-camera comparison / none). If
the answer is "nothing", the EEPROM ships empty and colour matching falls back
entirely on binning (question 11), which changes the sourcing strategy.

**11. LED binning versus the assembly route.** PAR-REQ-16 requires binning
specified in the BOM for all four channels; "unbinned parts across 8 fixtures
will not satisfy PAR-REQ-06". But JLC's catalogue does not generally let you
specify a chromaticity/flux bin, so binned high-power emitters usually mean
hand-sourcing from a distributor and hand-placing them.
(a) Hand-source binned emitters and place them by hand (or as a separate LED
sub-assembly), everything else JLC PCBA.
(b) Accept whatever bin JLC ships and rely entirely on per-fixture calibration
(question 10) to match the fixtures.
(c) Both: loose binning plus calibration.
**RECOMMEND (c)** - buy the tightest bin available from a distributor for one
batch of 6-8 fixtures (they will then be same-reel and closely matched anyway)
**and** fit the calibration EEPROM. Note (b) alone is only viable if question
10 has a real measurement instrument behind it.

**12. Confirm the board outline - MECH-02, needed before P5.** The ICD proposes
the common footprint: **100.0 x 80.0 mm, 3.0 mm corner radius, 1.6 mm thick,
4x M3 at 5 mm inset plus a 5th M3 at (46, 74), and the mandatory 30 x 26 mm
notch at (6, 0)-(36, 26)**. ai-ee has **no outline-shrink step** - whatever is
passed to `board_init` at P5 is permanent, so this must be confirmed, not
inherited silently.
**RECOMMEND: confirm 100.0 x 80.0 mm as-is.** The carrier and daughters share
one enclosure and mate through the connector, so the outlines are not
independent, and after the four exclusion zones and the notch this board has
roughly 60 x 74 mm of genuinely usable area for drivers plus whatever the LED
scheme needs. Please confirm explicitly, including whether the enclosure has
any dimension this footprint must fit inside that has not been stated.

**13. Assembly method and process.** Not stated anywhere in the LUMINA briefs.
(a) JLCPCB fabrication + PCBA, JLC Basic parts preferred where they exist
(note: the ICD connectors are Extended, unavoidably - there is no Basic
board-to-board part).
(b) Hand assembly.
Two sub-questions that need answering with it: **are the two 2.54 mm sockets
hand-soldered post-PCBA** (they are THT and must be reverse-mounted on the
bottom side, which is not a normal JLC process), and **are high-power emitters
hand-placed** (question 11)?
**RECOMMEND: JLC PCBA for everything it can do, with the two sockets and the
emitters hand-soldered afterward.** 6-8 boards is a quantity where two hand
operations per board is a couple of hours total, and it removes both awkward
processes from the critical path.

**14. Build quantity and unit cost target for THIS board.** The brief says 6-8
pars of 8-12 fixtures; no per-board cost target is stated (the $30/board figure
in ICD s1.1 belongs to the carrier). The $500-1000 system budget also predates
D-01's at-capable power stage, and the upgrade path implies a **PoE+** switch,
which is materially more expensive than the PoE switch that budget assumed.
**RECOMMEND: confirm 8 boards built (6-8 deployed plus spares) and set an
explicit BOM target for this board.** A defensible starting number is
**$25-35/board** excluding the LED module and heatsink, with the emitter and
heatsink budgeted separately because question 2 can double them.

**15. `ID_ADC` code allocation.** ICD s3.3: "Board-type codes are allocated by
the carrier owner, not chosen by daughters." This board needs its allocated
bottom-leg resistor value (and the resulting ADC code) before P4 can place the
part. **RECOMMEND: request the LUM-PAR-A code from the carrier owner now**; if
none exists yet, ask for one to be allocated rather than picking a value here -
picking one is exactly the silent divergence ICD-01's preamble forbids.

**16. Sequencing against ICD s7.2 (the one un-frozen section).** The J3/J4
coordinates in s7.2 are provisional until the carrier owner confirms them after
its own P6 and re-issues the ICD, and daughters are explicitly blocked on that.
Everything else in the ICD is frozen.
(a) Wait for the re-issued ICD before starting this run.
(b) **Proceed through P1-P4 (architecture and schematic, which do not depend on
mm coordinates) and hold at P5**, where the outline and connector placement are
bound permanently.
**RECOMMEND (b)**, with the s7.2 coordinates treated as unconfirmed everywhere
they appear, and an explicit re-check against the re-issued ICD before
`board_init` is run. Please confirm this is acceptable, and if the carrier's P6
has already completed, point this run at the re-issued ICD instead of the
DRAFT-A copy in `brief/`.
