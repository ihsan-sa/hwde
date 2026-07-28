# Requirements - LUMINA Carrier Board (LUM-CAR-A)

**Board ID:** LUM-CAR-A | **Rev:** A (first spin) | **Date:** 2026-07-28
**Sources:** `brief/00-lumina-system-context.md` (v2.0), `brief/01-carrier-board-brief.md`,
`brief/05-lumina-closed-decisions.md` (binding; supersedes `00` section 6 for D-01/D-02/D-03).

Requirement IDs `CAR-REQ-nn` / `SYS-REQ-nn` are the briefs' own IDs and are quoted, not
invented. `ASSUMED:` marks a low-risk assumption taken without asking. Everything else that is
unknown is a numbered question in section 9.

---

## 0. Decisions of record (closed - do NOT re-open)

| ID | Decision | Consequence for this board |
|---|---|---|
| D-01 | **802.3at Type 2 power stage, classification programmed to Type 1 (af) for the first build.** | PD front end, DC-DC, magnetics and thermals sized for ~20 W usable. Class-program resistor set for af. Upgrade to PoE+ must be a **resistor change only - no respin**. No other component may pin the design to Type 1. Power budget table must show **both** af and at columns (review gate 2). Daughter power budgets are designed against the af figure: **~8.5 W sustained** to the light engine. |
| D-02 | **Expansion connector carries 48 V raw + 12 V regulated + 3.3 V logic.** | 48 V raw = the PD rail, switched/fused per CAR-REQ-14, exists for the strobe energy store (~2800 uF instead of ~33,000 uF). 12 V regulated for daughters needing a modest rail without duplicating a >=60 V converter. 3.3 V for daughter logic/sense only, never LED current. **CAR-REQ-17 is now active and binding:** connector needs creepage/clearance appropriate to 48 V; every 48 V-tapping daughter carries its own bleed path. Chain is 48 -> 12 -> 3.3. |
| D-03 | **UV bar: no board.** | Allocate **no** connector budget, PWM channels, enclosure provision or power budget for a UV daughter. |
| D-04 | **Strobe colour (white vs RGBW): still open, owned by the strobe board run.** | **Not this board's decision and must not be assumed here.** The carrier satisfies either answer by exposing the full 8-PWM hardware ceiling (CAR-REQ-10). |
| ICD-01 | Carrier owns the expansion connector and freezes it as an ICD at **H1**. | Deliverable `architecture/connector-icd.md`: connector part number, pin assignment, per-pin current rating, 48 V creepage scheme. Daughters treat it as a hard input. |
| MECH-01 | Rounded corners + mounting holes on every LUMINA board. | 4x M3 (3.2 mm) mounting holes via `board_init.py --mounting-holes 4` unless the outline forbids it. Corner radius via a `--corner-radius` flag being added centrally - **confirm with `board_init.py --help` at P5, do not assume a default**. |
| MECH-02 | Board outline in mm must be closed with the human at H1, before P5. | ai-ee has **no outline-shrink step**; `--outline WxH` at `board_init` is permanent. The carrier **proposes the common enclosure footprint and mounting-hole pattern that daughters inherit**. See Q2/Q3 - blocking. |
| DOC-01 | Design document is a required deliverable. | `report_gen.py --workspace boards/lumina-carrier` must exit 0 at end of run. |
| GIT-01 | Scoped commits only. | Never `gate.py --commit`, never `git add -A`. Use `git add boards/lumina-carrier && git commit -m "ai-ee lumina-carrier: <gate> pass"`. |

---

## 1. Function

LUM-CAR-A is the single universal carrier PCB used unmodified beneath every LUMINA fixture
type. It takes power and data off one Ethernet cable and presents a fixture-agnostic expansion
interface. On board: an IEEE 802.3 PD front end (detection signature, classification, inrush
limiting, hot-swap), DC-DC conversion from the 37-57 V PD rail down to a 12 V daughter rail and
a 3.3 V logic rail, an ESP32-S3 running the fixture firmware, a W5500 Ethernet controller on
SPI with a 25 MHz reference crystal, an RJ45 with integrated magnetics carrying both data and
PoE, and the expansion connector. It receives UDP control packets and generates the light
engine's PWM waveforms locally. It contains **no** LED drivers, no light-engine energy storage
and no fixture-specific circuitry - that separation is the point of the architecture and is to
be protected, not eroded (`01` section 1, section 6).

Control contract the firmware must honour (hardware-relevant extract, `00` section 3): UDP over
IPv4 port 5568; 60 fps target / 44 fps floor; packet-to-PWM latency < 100 us; mDNS discovery or
static IP; watchdog fades all outputs to zero over 500 ms after 2 s without a valid packet.
Because a 60 fps command stream cannot express modulation above ~30 Hz, fast effects (1-25 Hz
strobe, ~20 Hz bass-tracking wobble, 50-200 ms accent flashes - SYS-REQ-01/02/03/05/06) are
**parameterised by the host and generated locally from the carrier's own timers**. Hardware
consequence: the PWM peripheral and its fade hardware are the mechanism, not the packet rate.

---

## 2. Interfaces

| Interface | Requirement | Source |
|---|---|---|
| **Ethernet / PoE** | RJ45 with **integrated magnetics**, carrying both 10/100 data and PoE power. Board-edge or panel-mount, consistent with one enclosure design across all fixture types (Q12). | CAR-REQ-05, CAR-REQ-20 |
| **Ethernet MAC/PHY** | W5500 on SPI, 25 MHz reference crystal. SPI clock must be inside the W5500 datasheet maximum (verified at schematic sign-off). | CAR-REQ-04, gate 5 |
| **MCU** | ESP32-S3 with SPI flash, boot/reset provisions, and a programming interface. Chosen ESP32-S3 pins must **not** be strapping, USB, or SPI-flash pins (verified at schematic sign-off). Module vs bare chip is open - Q7. | CAR-REQ-03, gate 5 |
| **Expansion connector** | Signal set below is fixed; pin *assignment* is the designer's call. Frozen as an ICD at H1. | CAR-REQ-06, section 4, ICD-01 |
| **PWM to daughter** | **8 channels maximum** - the ESP32-S3 LEDC hardware ceiling (8 channels, 4 timers, low-speed mode only, max 14-bit duty resolution). More channels on a daughter require an external PWM/LED driver over SPI or I2C. | CAR-REQ-10 |
| **PWM frequency domains** | 4 timers -> at most 4 distinct frequency/resolution domains per fixture; channels sharing a timer share both. Allocate deliberately when a daughter mixes fast strobe switching with slow colour dimming. Explicit per-daughter channel/timer/frequency allocation is a schematic sign-off artifact. | CAR-REQ-11, gate 3 |
| **PWM default** | **13-bit at 9.77 kHz** (8192 levels, satisfies SYS-REQ-04 with gamma correction; ~10 kHz avoids rolling-shutter banding that ~1.2 kHz would show). Duty must clamp to 2^n - 1 at a timer's max resolution. Hardware fading (`ledc_set_fade_with_time`) is available and is the intended mechanism for smooth transitions. *The camera-flicker threshold is flagged in the brief as a judgement call - verify on the first prototype with a phone camera.* The previously recorded "16-bit at 1.2 kHz" is **not achievable on this MCU** and must not be carried forward. | `01` section 3 |
| **PWM vs driver bandwidth** | ~10 kHz must be checked against each daughter's LED driver dimming bandwidth (many constant-current modules accept only ~1 kHz). If a driver cannot take it, that is a **daughter-board driver selection problem** - do not silently drop the carrier to 1.2 kHz without re-testing camera flicker. | CAR-REQ-12 |
| **SPI (expansion)** | 4 pins, shared bus, separate CS per daughter device. | section 4.1 |
| **I2C (expansion)** | 2 pins - ID EEPROM, temperature sensors, current monitors. | section 4.1 |
| **ADC (expansion)** | 2 pins - thermistor, current sense, rail sag monitoring. | section 4.1 |
| **ENABLE** | 1 pin. Fail-safe global enable to the daughter: **de-asserted by default, actively asserted by firmware only after successful boot**. Fail-safe analysis (MCU held in reset, mid firmware update, brownout) is a schematic sign-off artifact. | CAR-REQ-08, gate 4 |
| **FAULT** | 1 pin, daughter -> carrier, open-drain, pulled up on the carrier. | section 4.1 |
| **Daughter ID** | 1-2 pins. Resistor divider to an ADC pin (cheapest, adequate for 4-6 types) or I2C EEPROM (type, revision, channel map, per-unit calibration - preferred if the BOM allows). Open - Q10. | CAR-REQ-07, section 4.3 |
| **Status indication** | Link, power-good, fault - visible **without opening the enclosure** (flagged as judgement in the brief; justified by commissioning 8-12 fixtures). Mechanism open - Q11. | CAR-REQ-09 |
| **Programming / field update** | Required, strategy open: USB-C on every fixture, pogo-pin jig, or Ethernet OTA only. Affects connector count and enclosure design. | `01` section 8 Q5 -> Q9 |
| **Wireless** | **Out of scope as a control path.** The ESP32-S3 radio is a debugging fallback only; Ethernet is the control path. Whether it must work in the field is open - Q8. | `01` section 6 |
| **Audio** | **None.** Fixtures never hear music. No audio input of any kind. | `01` section 6 |

### 2.1 Expansion connector signal set (fixed)

| Signal | Pin count | Notes |
|---|---|---|
| 48 V raw (PD rail) | see Q6 | Switched/fused per CAR-REQ-14; 48 V creepage per CAR-REQ-17. |
| 12 V regulated | >= 3 pins total across the power rails, current-shared | D-02. |
| GND | >= 4 | Distributed; return paths adjacent to the PWM lines. |
| 3.3 V logic | 1-2 | Daughter logic/sense only, not LED current. |
| PWM | up to 8 | CAR-REQ-10. |
| SPI | 4 | Shared, separate CS per device. |
| I2C | 2 | |
| ADC | 2 | |
| ENABLE | 1 | Fail-safe, CAR-REQ-08. |
| FAULT | 1 | Open-drain, pulled up on carrier. |
| ID | 1-2 | Per section 4.3 / Q10. |

**Note:** `01` section 4.1 lists ">= 3 pins, current-shared" for a single "daughter power rail";
D-02 then split that rail into 48 V raw + 12 V regulated. Pin counts per rail are therefore a
carrier design decision constrained by Q6, not a quoted requirement.

### 2.2 Connector electrical/mechanical requirements

| ID | Requirement |
|---|---|
| CAR-REQ-13 | Current rating with **>= 50 % margin** over worst-case daughter draw, including strobe cap-bank charging current. Worst case is not yet supplied - Q6. |
| CAR-REQ-14 | Inrush limiting is the **daughter's** responsibility (the bulk capacitance lives there), but the carrier **must survive a shorted or mis-seated daughter without damage to the PD front end**. |
| CAR-REQ-15 | Mechanical support - mounting hole or standoff between the boards near the connector, so board flex is not carried by the pins. |
| CAR-REQ-16 | Keyed or otherwise reverse-insertion-proof. |
| CAR-REQ-17 | **Active/binding** (D-02): creepage and clearance appropriate to 48 V across the connector; every daughter tapping 48 V carries a bleed path for stored energy. |

`ASSUMED:` the PD front end supports both Mode A (data-pair) and Mode B (spare-pair) power and
either polarity, via input bridges - this is mandatory for an 802.3-compliant PD, not a choice.

`ASSUMED:` the 48 V raw output to the daughter is gated by a current-limited high-side switch
(or equivalent fuse + FET) so that CAR-REQ-14 survivability is a carrier-side function; exact
topology is P2 architecture's call, not a requirement input.

---

## 3. Power

### 3.1 Input

- Source: **PoE only.** Single Ethernet cable, no barrel jack, no other input.
- PD input voltage: **37-57 V nominal at the PD** (`00` section 5.3).
- Class: **802.3at Type 2 power stage, af classification for build 1** (D-01). Class-program
  resistor is the single upgrade lever.
- **No battery, no charging, no supercapacitor on the carrier.** Light-engine energy storage
  lives on the daughter (`01` section 6).

### 3.2 Budget (all figures from `00` section 5.1 and D-01)

| Item | 802.3af (build 1) | 802.3at (upgrade) |
|---|---|---|
| PD input limit | 12.95 W | 25.5 W |
| Regulated power available to the application | ~10 W (Skyworks AN956 / Si3402-B figure) | ~20 W |
| Carrier overhead (ESP32-S3 + W5500 + magnetics + regulator losses) | **1.5 W allocation** | 1.5 W allocation |
| **Sustained power to the light engine** | **~8.5 W** | ~18.5 W |

- The **1.5 W carrier overhead is flagged as judgement in `00` and must be measured on the first
  prototype.** Treat as a budget, not a fact.
- **12.95 W is the PD input limit, not usable output** - budget against the ~10 W regulated
  figure. This correction is explicit in the brief.
- The power budget table (PD input limit -> converter efficiency -> carrier overhead -> power at
  the expansion connector), **with both af and at columns**, is a schematic sign-off deliverable
  and is the artifact proving D-01 was decided rather than assumed (gate 2, D-01).
- Burst vs sustained: a cap bank solves peak power, not average. 1 J dumped in 10 ms is 100 W for
  10 ms, but repeating at 12 Hz still draws 12 W continuously. Any cap-bank daughter needs an
  **average-energy governor in firmware**. This bounds what the carrier's rails must sustain
  (`00` section 5.2).

### 3.3 Rails

| Rail | Purpose | Requirement |
|---|---|---|
| 48 V raw | Pass-through to connector for the strobe energy store | Switched/fused, 48 V creepage (D-02, CAR-REQ-14/17). |
| 12 V regulated | Daughter rail for par and future low-power daughters | Converter **input rating >= 60 V with margin** (CAR-REQ-02). |
| 3.3 V logic | Carrier MCU/PHY + daughter logic/sense | Derived via 48 -> 12 -> 3.3 (D-02). |

**Part exclusion, stated as a correction not an open question (`00` section 5.3):** the
**LM2596** (40 V) and **LMR33630** (3.8-36 V) named in Project Plan v1.0 section 6.2 **cannot be
used** on the PD rail. Any converter on that rail needs >= 60 V rating with margin.

---

## 4. Environment

Nothing in the briefs states a temperature range, ingress rating, or vibration spec. What is
known:

- **Deployment:** indoor, basement/garage room ~5 m x 7 m x 2.5 m, 8-12 fixtures (`00` section 1).
- **Enclosure:** a fixture enclosure **common to all fixture types**; dimensions **not yet
  defined**, explicitly flagged by the brief as "an input the design needs and does not have"
  (CAR-REQ-19). See Q1/Q2.
- **Thermal (CAR-REQ-18):** the carrier's DC-DC converter and the daughter's LED drivers are two
  separate heat sources inside one enclosure. The design must **either physically separate them
  or specify the enclosure airflow that makes stacking acceptable**. A thermal review against
  CAR-REQ-18 is a layout sign-off gate. Ambient/ventilation unknown - Q13.
- Ingress, vibration, altitude, humidity: **not stated**. `ASSUMED:` dry indoor use, no ingress
  rating, no vibration requirement, 0-40 degC ambient - confirm via Q13.

---

## 5. Size and mounting

**This section is a blocking input, not a design output.** MECH-02: the P5 outline binds
permanently (`board_init.py --outline WxH`, no shrink step exists), and the carrier proposes the
**common footprint and mounting-hole pattern that every daughter inherits**. It must be closed
with the human at H1, before P5.

| Item | Status |
|---|---|
| Board outline (mm) | **UNKNOWN - blocking.** Q2. |
| Corner radius | Rounded corners required (MECH-01). Value open - Q3. Confirm the `--corner-radius` flag exists at P5 via `board_init.py --help`. |
| Mounting holes | 4x M3 (3.2 mm) at the outline corners unless the outline forbids it (MECH-01); native to P5, board-only, ignored by schematic parity. Exact pattern/inset open - Q3. |
| Board-to-board arrangement and stack height | **UNKNOWN.** Q4. Also drives CAR-REQ-15 (standoff near the connector). |
| Enclosure internal height budget | **UNKNOWN.** Q4. |
| RJ45 mounting style | Board-edge vs panel-mount, must be consistent across fixture types (CAR-REQ-20). Q12. |
| Where the LEDs physically live | **UNKNOWN** and thermally load-bearing for CAR-REQ-18. Q4a. |

---

## 6. Quantity and budget

- **Build quantity:** 8-12 carriers for the first deployment (`00` section 1, `01` section 1).
  Exact order quantity and spares not fixed - Q15.
- **Budget:** $500-1000 for the whole first build - fixtures **plus** the managed PoE switch
  **plus** enclosures (`00` section 1). **No per-carrier target cost is stated anywhere in the
  briefs.** Q15.
- Manufacturability constraint that is stated: must be "assemblable in small quantity without
  exotic processes" (`01` section 1).

---

## 7. Assembly

**Not stated in any brief.** The only constraint is "no exotic processes at 8-12 units".
Open - Q14. `ASSUMED:` pending the answer, design for JLCPCB PCBA with single-sided (top)
assembly and prefer Basic/Standard library parts; this assumption must be confirmed before P2
part selection, because it constrains package choice for the PD controller, the >= 60 V
converter and the ESP32-S3 decision (Q7).

---

## 8. Compliance / safety flags

| Flag | Applies | Detail |
|---|---|---|
| **> 30 V present** | **YES** | PD rail is 37-57 V nominal; 57 V is the worst case for component rating. This is the dominant safety/derating driver on the board. Converters need >= 60 V input rating with margin. |
| **> 30 V leaves the board** | **YES** | 48 V raw is passed to the daughter connector (D-02). CAR-REQ-17 is binding: **48 V creepage/clearance across the connector**, and every 48 V-tapping daughter needs a bleed path. Connector selection is constrained by spacing, not just current. |
| **Stored energy hazard** | **YES (system-level)** | The strobe daughter holds ~2800 uF charged to ~48 V (~3 J). It lives off-board, but the carrier supplies it and freezes the connector that carries it. Bleed-path requirement is placed on daughters by D-02; the carrier must not defeat it. |
| **High current (> 3 A)** | **UNRESOLVED - must be answered, not guessed** | 8.5 W sustained on 48 V is only ~0.2 A average, but CAR-REQ-13 sizes the connector against **worst-case draw including cap-bank charging current**, which no brief supplies. The strobe's ~2.6 A drive figure (D-02 / STR-REQ-12) is bank-to-LED, not connector current. **Q6.** |
| **Fault tolerance** | **YES** | CAR-REQ-14: the carrier must survive a shorted or mis-seated daughter with no damage to the PD front end. |
| **Isolation / earthing** | **UNRESOLVED - must be answered, not guessed** | Whether the PD converter is isolated (flyback) or non-isolated (buck) determines whether the whole board floats at PoE potential. Non-isolated is cheaper and normal for a PD, but it requires a non-conductive or fully floating enclosure and no second earthed connection. Enclosure material and any other external connection are unknown. **Q5.** |
| **RF transmit** | **CONDITIONAL** | Ethernet is the control path and wireless is out of scope, but an ESP32-S3 module physically contains a 2.4 GHz transmitter. If the radio must be usable, antenna keep-out and enclosure material become constraints; if it is permanently disabled, they are not. **Q8.** A pre-certified module also removes RF layout from the critical path - **Q7.** |
| Mains voltage | NO | No mains anywhere on this board. |
| Battery / charging | NO | No battery, no cells, no charger on the carrier. |
| Motors / inductive loads | NO | None. |

Per the analyst rules, the pipeline does **not** proceed on guessed safety requirements: **Q5 and
Q6 must be answered by the human before P2 architecture commits a converter topology or a
connector part.**

---

## 9. Open questions

Answer these in one batch. Defaults are marked `[default: ...]` - replying "defaults" to any
question is a valid answer.

**Blocking for H1 / P5 (MECH-02 - the outline is permanent once set):**

1. **Is there a physical enclosure already chosen, or do we choose the board size and have the
   enclosure follow?**
   (a) Off-the-shelf enclosure already picked - give make/model or internal dimensions;
   (b) custom 3D-printed / laser-cut, so the board size leads;
   (c) undecided, treat as (b) for now.
   `[default: (b) - the board size leads and the enclosure is built around it]`

2. **What common board outline, in mm, should the carrier and every daughter use?** This is
   permanent - there is no shrink step later, and daughters inherit it.
   (a) **100 x 80 mm** - comfortable for the carrier (PD front end + >= 60 V DC-DC + ESP32-S3 +
   W5500 + RJ45 with the DC-DC separated from the daughter's drivers per CAR-REQ-18), and leaves
   the strobe daughter enough area for a ~2800 uF / 63 V bank;
   (b) **100 x 100 mm** - maximum headroom, same JLCPCB low-cost size tier, bigger enclosure;
   (c) **80 x 60 mm** - compact, but likely too tight once 48 V creepage and the strobe cap bank
   are accounted for.
   `[default: (a) 100 x 80 mm]`

3. **Corner radius and mounting-hole pattern for the common footprint?**
   `[default: 3 mm corner radius; 4x M3 (3.2 mm) holes inset 5 mm from each edge, i.e. a
   90 x 70 mm hole rectangle on a 100 x 80 mm board - identical on every LUMINA board so any
   daughter bolts to the same standoffs]`

4. **How do the carrier and daughter sit relative to each other, and how much internal height is
   available?**
   (a) Stacked mezzanine, daughter above the carrier, board-to-board standoffs;
   (b) stacked, daughter below;
   (c) side by side / coplanar, joined by a cable.
   Also state the usable internal height of the fixture, since the strobe's electrolytics are
   likely 20-25 mm tall.
   `[default: (a) stacked mezzanine, daughter above, 15 mm board-to-board standoff, >= 45 mm
   internal height available]`

4a. **Are the LEDs mounted on the daughter board itself, or on a separate LED module/star wired
   to it?** This decides whether the enclosure has one hot zone or two and drives the CAR-REQ-18
   thermal argument.
   `[default: separate LED module on its own heatsink, wired to the daughter]`

**Safety-relevant - will not be guessed (section 8):**

5. **Isolated or non-isolated PD converter, and what is the enclosure made of?** A non-isolated
   buck is cheaper and smaller, but then the entire board floats at PoE potential and the
   enclosure must be non-conductive (or metal with no second earthed connection). An isolated
   flyback costs more and is bigger. Also: **does the fixture have any electrical connection to
   anything other than the Ethernet cable** (chassis earth, DMX, a mains-powered fan, a shared
   LED supply)?
   `[default: non-isolated buck, plastic/3D-printed enclosure, Ethernet is the only external
   connection]`

6. **What is the worst-case current the daughter board will draw from each connector rail?**
   CAR-REQ-13 requires >= 50 % margin above this, and it decides the connector part. Needed as
   three numbers: 48 V raw peak (cap-bank charging), 12 V continuous, 3.3 V continuous.
   `[default: size the connector for 48 V raw 2 A continuous with 3 A capability, 12 V 2 A,
   3.3 V 0.5 A - this covers the strobe's charging current with margin while staying inside the
   ~8.5 W average PoE budget, which firmware enforces via the average-energy governor]`

**Design-of-record questions carried over from `01` section 8:**

7. **ESP32-S3: pre-certified module or bare chip?** A module removes RF layout and SPI-flash
   routing from the critical path on a first spin; a bare chip is cheaper per unit at volume but
   adds RF layout, flash routing and certification risk. If a module: how much flash?
   `[default: pre-certified ESP32-S3-WROOM-1 module, 8 MB flash, no PSRAM - lowest risk for a
   first spin and consistent with 8-12 units]`
   *(This is `01` section 8 question 4, still open.)*

8. **Must Wi-Fi/BLE actually work on the deployed fixture, or is the radio permanently unused?**
   If it must work, the module needs an antenna keep-out at a board edge and the enclosure must
   not be metal near it; if unused, neither constraint applies and the enclosure is freer.
   `[default: radio unused in normal operation but keep it functional - place the module with a
   proper edge keep-out, and keep the enclosure non-metallic (consistent with Q5 default)]`

9. **How do firmware updates happen, in the workshop and in the field?**
   (a) USB-C connector on every fixture;
   (b) Ethernet OTA as the normal path, plus a small on-board UART/boot header for recovery;
   (c) pogo-pin jig against test pads, plus Ethernet OTA;
   (d) Ethernet OTA only, no recovery path.
   This affects connector count, panel cutouts and enclosure design.
   `[default: (b) - Ethernet OTA normally, plus a 6-pin 1.27 mm or 2.54 mm UART/BOOT/EN header
   inside the enclosure for recovery; no USB-C cutout on 8-12 fixtures]`
   *(This is `01` section 8 question 5, still open.)*

10. **Daughter identification: resistor divider, I2C EEPROM, or both?** The brief prefers EEPROM
   "if the BOM allows" because it also stores per-unit colour calibration; the divider is
   cheaper and coarser. Supporting both costs ~2 connector pins and one pull-up.
   `[default: both - reserve 1 ADC-capable ID pin for a divider AND route I2C to a daughter
   EEPROM, so a cheap daughter can use the resistor and the par/strobe can use the EEPROM]`

11. **How should link / power-good / fault be visible without opening the enclosure?**
   (a) Board-edge LEDs plus a light pipe or window in the enclosure;
   (b) the RJ45 jack's own integrated LEDs only, visible through the Ethernet cutout;
   (c) LEDs on the board only, accepted as not externally visible.
   `[default: (b) plus one status LED beside the RJ45 cutout - re-uses the connector opening and
   needs no extra enclosure feature]`

12. **RJ45: board-edge jack sticking through a cutout, or panel-mount jack on a short pigtail?**
   Must be the same across all fixture types (CAR-REQ-20).
   `[default: board-edge THT magjack through a cutout - fewer parts, no pigtail]`

**Programme / commercial:**

13. **What ambient temperature and ventilation should the design assume?**
   `[default: 0-40 degC ambient, sealed (unventilated) enclosure, natural convection only -
   which forces the CAR-REQ-18 answer to be physical separation of the DC-DC from the daughter's
   drivers rather than airflow]`

14. **Assembly method: JLCPCB PCBA or hand solder, and single- or double-sided assembly?**
   `[default: JLCPCB PCBA, single-sided (top) assembly, prefer Basic/Standard library parts;
   this is currently an ASSUMED in section 7 and needs confirming before P2 part selection]`

15. **How many carriers to build, and what is the target cost per assembled carrier?** The
   $500-1000 figure covers fixtures + switch + enclosures together, so the carrier's share is not
   derivable from it.
   `[default: build 14 (12 fixtures + 2 spares); target <= $30 per assembled carrier at that
   quantity, PCB + parts + assembly]`

16. **Which daughter boards must the frozen connector ICD serve?** D-03 removed the UV bar, so
   the known set is strobe + RGBW par. The future STM32F4 laser/galvo daughter is out of Phase 1
   and undefined - do we reserve anything for it now?
   `[default: freeze the ICD for strobe + RGBW par only; no extra reservation - the existing SPI
   and I2C lines already let a future daughter carry its own MCU or driver]`

---

## 10. Notes for downstream phases

- **P2 architecture must not commit** a converter topology (Q5) or a connector part (Q6, Q2/Q3)
  until those answers land.
- **H1 deliverables** are the frozen `architecture/connector-icd.md` (ICD-01) **and** the agreed
  board outline in mm (MECH-02).
- **Schematic sign-off gates** (`01` section 7): PD topology matched to the selected controller's
  reference design with detection/classification values justified against D-01; the two-column
  power budget table; explicit PWM channel/timer/frequency allocation per planned daughter;
  ENABLE fail-safe analysis (MCU in reset, mid update, brownout); W5500 SPI clock inside spec and
  ESP32-S3 pins clear of strapping/USB/SPI-flash functions.
- **Layout sign-off gates:** Ethernet differential pair routing and magnetics isolation review,
  DC-DC switching-node loop area review, thermal review against CAR-REQ-18.
- **End of run:** `report_gen.py` must exit 0 (DOC-01); commits are scoped to
  `boards/lumina-carrier` only (GIT-01).
