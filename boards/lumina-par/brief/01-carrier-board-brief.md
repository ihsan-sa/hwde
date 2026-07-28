# Design Brief — LUMINA Carrier Board (universal)

**Board ID:** LUM-CAR-A | **Rev:** A (first spin) | **Date:** 2026-07-28
**Read first:** `00-lumina-system-context.md`

---

## 1. Mandate

One board, used unmodified under every fixture type. It takes power and data off a single
Ethernet cable and presents a fixture-agnostic expansion interface: regulated power, PWM,
serial buses, sense inputs, and a fail-safe enable.

It contains **no** LED drivers, no energy storage for the light engine, and no
fixture-specific circuitry. If a requirement is specific to strobes or pars, it belongs on the
daughter board, not here. This constraint is the whole point of the architecture — protect it.

Target: 8–12 units built for the first deployment, so it must be assemblable in small
quantity without exotic processes.

---

## 2. Functional block requirements

| ID | Requirement |
|---|---|
| CAR-REQ-01 | IEEE 802.3 PD front end: detection signature, classification, inrush limiting, hot-swap. Class per `D-01`. |
| CAR-REQ-02 | DC-DC conversion from the PD rail to the daughter-board power rail and a 3.3 V logic rail. Input rating ≥ 60 V (PD rail is 37–57 V nominal). |
| CAR-REQ-03 | ESP32-S3 with SPI flash, boot/reset provisions, and a programming interface. |
| CAR-REQ-04 | W5500 Ethernet controller on SPI, 25 MHz reference crystal. |
| CAR-REQ-05 | RJ45 with integrated magnetics carrying both data and PoE. |
| CAR-REQ-06 | Expansion connector per §4. |
| CAR-REQ-07 | Daughter-board identification readable by firmware at boot (§4.3). |
| CAR-REQ-08 | Fail-safe global enable to the daughter board: de-asserted by default, actively asserted by firmware only after successful boot. |
| CAR-REQ-09 | Status indication: link, power-good, fault. Visible without opening the enclosure — *flagged as judgement*, useful for commissioning 12 fixtures. |

---

## 3. PWM generation — corrected specification

**The previously recorded "16-bit PWM at 1.2 kHz" is not achievable on this MCU and should
not be carried forward.**

Per the ESP-IDF LEDC documentation for the ESP32-S3 target:

- The LEDC peripheral has **8 channels** and **4 timers**, all **low-speed mode only**
  (the high-speed channel group exists on the original ESP32, not the S3).
- Maximum duty resolution is **14 bits** (`LEDC_TIMER_14_BIT` is the top enumerator).
  16-bit is not offered.
- Frequency and resolution trade off against the source clock. With APB at 80 MHz:

| Duty resolution | Max PWM frequency (80 MHz / 2ⁿ) |
|---|---|
| 14 bit | 4.88 kHz |
| 13 bit | 9.77 kHz |
| 12 bit | 19.53 kHz |
| 11 bit | 39.06 kHz |

- At a timer's maximum duty resolution the duty value cannot be set to 2ⁿ (hardware counter
  overflow) — firmware must clamp to 2ⁿ−1.
- Hardware fading is supported (`ledc_set_fade_with_time` and related), which offloads smooth
  transitions from the packet stream.

**Recommendation: 13-bit at 9.77 kHz as the default.** Reasoning: 1.2 kHz was chosen partly
for "camera-safe flicker," but ~1.2 kHz is low enough to band visibly on rolling-shutter
sensors, especially in slow-motion capture — and people film parties. Roughly 10 kHz removes
that concern while retaining 8192 levels, which satisfies SYS-REQ-04 with gamma correction.
*Flagged as judgement:* the camera-flicker threshold is a design margin call, not a cited
figure. Verify against a phone camera on the first prototype.

**Constraints this places on the design:**

| ID | Requirement |
|---|---|
| CAR-REQ-10 | Expansion connector shall expose **8 PWM channels maximum** — the hardware ceiling. Any daughter board needing more requires an external PWM/LED driver over SPI or I²C; do not plan around 8+ native channels. |
| CAR-REQ-11 | Channels sharing a timer share frequency and resolution. With 4 timers, a fixture can run at most 4 distinct PWM frequency domains. Allocate deliberately if a daughter board mixes fast strobe switching with slow colour dimming. |
| CAR-REQ-12 | The chosen PWM frequency must be verified against the daughter board's LED driver dimming bandwidth. Many constant-current driver modules accept PWM dimming only up to ~1 kHz. If the selected driver cannot accept ~10 kHz, that is a driver selection problem to solve on the daughter board — do not silently drop the carrier back to 1.2 kHz without re-testing camera flicker. |

---

## 4. Expansion connector

The single most important interface in the system. Once daughter boards exist, changing it is
expensive. Pin *assignment* is the designer's call; the signal set is not.

### 4.1 Required signals

| Signal | Count | Notes |
|---|---|---|
| Daughter power rail | ≥ 3 pins | Current-shared. Voltage per `D-02`. |
| GND | ≥ 4 pins | Distributed; return paths adjacent to PWM lines. |
| 3.3 V logic | 1–2 | For daughter-board logic/sense only, not for LED current. |
| PWM | up to 8 | Per CAR-REQ-10. |
| SPI | 4 | Shared bus, separate CS per daughter device. |
| I²C | 2 | ID EEPROM, temperature sensors, current monitors. |
| ADC | 2 | Thermistor, current sense, rail sag monitoring. |
| ENABLE | 1 | Fail-safe, per CAR-REQ-08. |
| FAULT | 1 | Daughter → carrier, open-drain, pulled up on carrier. |
| ID | 1–2 | Per §4.3. |

### 4.2 Electrical and mechanical requirements

| ID | Requirement |
|---|---|
| CAR-REQ-13 | Connector current rating with ≥ 50 % margin over the worst-case daughter draw, including the strobe cap-bank charging current. |
| CAR-REQ-14 | Inrush limiting is the **daughter board's** responsibility (that is where the bulk capacitance lives), but the carrier must survive a shorted or mis-seated daughter board without damage to the PD front end. |
| CAR-REQ-15 | Mechanical support: mounting hole or standoff between the boards near the connector so board flex is not carried by the pins. |
| CAR-REQ-16 | Keyed or otherwise reverse-insertion-proof. |
| CAR-REQ-17 | If `D-02` resolves in favour of carrying the ~48 V PD rail to the daughter board, the connector requires creepage/clearance appropriate to 48 V and the brief for every daughter board must be revised to include a bleed path for stored energy. |

### 4.3 Daughter board identification

Firmware ships as one image for all fixture types and discovers what it is driving at boot.
Two acceptable implementations:

- **Resistor divider to an ADC pin.** Cheapest. Coarse but sufficient for 4–6 board types.
- **I²C EEPROM.** Carries type, revision, channel map, and per-unit calibration data.
  Preferred if the BOM allows — calibration storage becomes valuable once fixtures are
  colour-matched against each other.

---

## 5. Thermal and mechanical

| ID | Requirement |
|---|---|
| CAR-REQ-18 | The carrier's DC-DC converter and the daughter's LED drivers are two separate heat sources in one enclosure. Physically separate them, or specify the enclosure airflow that makes stacking acceptable. |
| CAR-REQ-19 | The board must fit a fixture enclosure common to all fixture types. Enclosure dimensions are **not yet defined** — this is an input the design needs and does not have. Flag it early rather than designing to an assumed outline. |
| CAR-REQ-20 | Panel-mount or board-edge RJ45 consistent with a single enclosure design across fixture types. |

---

## 6. Out of scope

- LED drivers, current sense for LEDs, energy storage for the light engine.
- Galvo/laser control (future STM32F4 daughter board with its own MCU).
- Wireless operation. The ESP32-S3's radio is a debugging fallback only; Ethernet is the
  control path and the system is designed around it.
- Audio input of any kind. Fixtures never hear music.

---

## 7. Design review gates

Schematic sign-off requires:

1. PD front-end topology matching the reference design of the selected controller, with the
   detection and classification component values justified against the class chosen in `D-01`.
2. A power budget table: PD input limit → converter efficiency → measured/estimated carrier
   overhead → power available at the expansion connector. This table is the artifact that
   proves `D-01` was decided rather than assumed.
3. Explicit PWM allocation: which channels, which timers, which frequency domains, for each
   planned daughter board.
4. Fail-safe analysis of ENABLE: what the daughter board does with the MCU held in reset, mid
   firmware update, and during brownout.
5. Confirmation that the W5500 SPI clock is within its datasheet maximum and that the ESP32-S3
   pins chosen are not strapping, USB, or SPI-flash pins.

Layout sign-off requires: Ethernet differential pair routing and magnetics isolation review,
switching-node loop area review on the DC-DC, and a thermal review against CAR-REQ-18.

---

## 8. Questions to resolve before starting

1. `D-01` (af vs at) — this sets the DC-DC power rating and therefore the whole board. Do not
   start without an answer, even a provisional one.
2. `D-02` (daughter rail voltage) — sets the connector definition.
3. Enclosure outline and mounting scheme (CAR-REQ-19) — genuinely unknown, needs a decision.
4. ESP32-S3 as a pre-certified module versus a bare chip. A module is the low-risk choice for
   a first spin and removes RF layout and flash routing from the critical path — but it is not
   a decision of record yet.
5. Programming and field-update strategy: USB-C on every fixture, a pogo-pin jig, or
   Ethernet OTA only. This affects connector count and enclosure design.
