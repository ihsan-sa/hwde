# Design Brief — LUMINA Strobe Daughter Board

**Board ID:** LUM-DTR-STROBE-A | **Rev:** A | **Date:** 2026-07-28
**Read first:** `00-lumina-system-context.md`, then `01-carrier-board-brief.md`
**Blocked on:** `D-01` (PoE class), `D-02` (energy store voltage), `D-04` (colour capability)

---

## 1. Mandate

The hardest board in the system and the one that defines whether LUMINA reads as a real
lighting rig or as bright LEDs. It converts a modest average power budget into short, violent
bursts of light, and it must switch them with hard edges.

Quantity: 4–6 of 8–12 total fixtures.

---

## 2. What "strobe" means here — behavioural spec

From the genre profiles (see `00` §4). These are not aspirational; they are the acceptance
criteria.

| ID | Requirement | Why |
|---|---|---|
| STR-REQ-01 | Full-output flash, 100–200 ms, with **instant** blackout either side. No visible decay tail, no fade-in ramp. | P1 rage trap: the visual gap between maximum and zero is the entire effect. |
| STR-REQ-02 | Repetitive flashing, continuously variable 1–25 Hz, rate settable per packet and generated locally between packets. | P1 build ramps 2 → 12 Hz; P7 drop runs at maximum rate. |
| STR-REQ-03 | Short accent flashes down to 50 ms. | P1 ad-lib flashes. |
| STR-REQ-04 | Sub-flash intensity control — a "10–20 % barely-visible slow pulse" is a real profile requirement, not just full-or-off. | P1 verse: near-darkness with a 1–2 Hz pulse. |
| STR-REQ-05 | Survive a sustained drop section: 8–16 bars of maximum-rate flashing without thermal or electrical failure, then return to normal behaviour. | P7 drop. This is the worst-case duty cycle in the whole system. |

---

## 3. The power problem — solve this before anything else

### 3.1 Budget

Per `00` §5, sustained power available to the light engine is **≈ 8.5 W on 802.3af**
(≈ 20 W if `D-01` resolves to 802.3at). The "100 W strobe" in Project Plan v1.0 is a
**peak** figure achievable only through energy storage at low duty cycle.

### 3.2 Worked example (verify, do not inherit)

Target: 100 W optical drive for 10 ms per flash → **1 J per flash**.

| Flash rate | Sustained draw at 1 J/flash | Fits 8.5 W budget? |
|---|---|---|
| 4 Hz | 4 W | Yes |
| 8 Hz | 8 W | Marginal |
| 12 Hz | 12 W | **No** |
| 25 Hz | 25 W | No |

So either flash energy scales down as rate goes up, or the fixture browns out during exactly
the moments the music demands most. This is a **firmware requirement expressed as a hardware
constraint**:

| ID | Requirement |
|---|---|
| STR-REQ-06 | Implement an average-energy governor — a leaky-bucket budget that permits full-energy flashes in short bursts (drops, 808 hits) and automatically reduces per-flash energy under sustained high-rate strobing. The hardware must expose what the governor needs: rail voltage sense on the storage bank via the carrier's ADC. |
| STR-REQ-07 | Rail sag must degrade gracefully — dimmer flashes, never missed flashes or a reset. A dropped beat is more visible than a slightly dimmer one. |

This maps well onto the music: drops are short and want maximum output; verses and grooves are
long and want less. *Flagged as judgement* — the governor's exact curve is a tuning problem for
the simulator, not a hardware parameter.

### 3.3 Energy storage sizing

For a target of 1 J per flash:

| Bank voltage | Usable window | Required capacitance | Notes |
|---|---|---|---|
| 12 V | 12 → 9 V | ≈ 33,000 µF | Three or four 10,000 µF/16 V electrolytics. Physically large. |
| ~48 V (PD rail) | 48 → 40 V | ≈ 2,800 µF | ~3,300 µF at 63 V. Roughly 10× less capacitance. |

Stored energy scales with V², which is why the high-voltage option collapses the bank size.
This is `D-02` and it is the single highest-leverage decision on this board.

| ID | Requirement |
|---|---|
| STR-REQ-08 | Capacitor selection must account for pulse ripple current and ESR, not capacitance alone. An 8 A pulse into a bank with poor ESR sags harder than the ideal energy calculation predicts and softens the flash edge. Specify ripple current rating explicitly in the BOM. |
| STR-REQ-09 | Inrush limiting at the expansion connector — NTC thermistor or soft-start MOSFET. An empty bank on hot-plug will otherwise pull a damaging spike through the connector and trip the PD front end. |
| STR-REQ-10 | Bleed resistor across the bank. At 48 V and 3,300 µF the board holds several joules with the cable unplugged; it must be safe to handle during assembly and service. |

---

## 4. Drive topology — open

Two families, both viable. Choose with analysis, not preference.

**(a) Switched discharge from the bank.** Series MOSFET plus current limiting, fed directly
from the storage bank. Fast edges by construction, few parts, no output inductor or bulk
output capacitance to bleed the tail. Cost: dissipation in the pass element during the flash,
and current regulation is only as good as the limiting scheme.

**(b) Constant-current switching driver with PWM dimming.** Well-behaved current regulation
and efficient. Risk: output capacitance and control-loop response can produce exactly the
decay tail that STR-REQ-01 forbids, and many CC driver modules accept PWM dimming only to
~1 kHz, which conflicts with CAR-REQ-12.

*Flagged as judgement:* topology (a) looks better suited to this application because the duty
cycle is low and edge quality dominates efficiency. Verify against measured rise/fall on a
prototype before committing.

| ID | Requirement |
|---|---|
| STR-REQ-11 | Measured optical rise and fall must be fast enough that a 50 ms flash reads as square. Define the acceptance number during design; Project Plan v1.0 states < 1 ms response as the target. |
| STR-REQ-12 | Driving a **series LED string** from a high-voltage bank is strongly preferred over a low-voltage/high-current arrangement: 100 W at ~38 V string voltage is ~2.6 A, versus ~8.3 A at 12 V. Lower current means smaller connectors, thinner copper, and less I²R loss. This is a further argument for `D-02` option (b). |

---

## 5. LED selection — an open gap

There is no LED of record. The project plan names CREE/Lumileds families as a direction only.

| ID | Requirement |
|---|---|
| STR-REQ-13 | Verify the candidate LED's **pulsed** forward current derating curve, not just its DC maximum. The operating point here is short high-current pulses at low duty cycle; manufacturers specify this explicitly and the allowance is usually well above the DC rating. |
| STR-REQ-14 | Neutral or cool white with no colour cast at full output. The profiles use white blasts as a percussive element (SYS-REQ-07); a green or pink tint at peak current is a defect. |
| STR-REQ-15 | Thermal path sized for the **sustained** average (≈ 8.5 W), with junction temperature during peak pulses checked against the pulsed derating curve. Both cases must pass. |
| STR-REQ-16 | Beam angle and optic selection appropriate to a 2.5 m ceiling in a 5 × 7 m room. A narrow beam that lights one square metre of floor fails the room, regardless of its lumen figure. |

`D-04` decides whether this board is white-only or RGBW. White-only is simpler, cheaper, and
covers the dominant use (rage trap and hard French rap both call for white blasts). RGBW adds
the coloured blasts that P8 UK bass asks for — "all fixtures fire red or green at 80–100 %" —
though the RGBW pars may already cover that.

---

## 6. Interface to the carrier

| ID | Requirement |
|---|---|
| STR-REQ-17 | PWM channel count within the 8-channel ceiling (CAR-REQ-10). White-only needs 1–2; RGBW needs 4–5. |
| STR-REQ-18 | Report bank voltage to a carrier ADC pin (feeds STR-REQ-06). |
| STR-REQ-19 | Report LED thermistor temperature to a carrier ADC or I²C pin. |
| STR-REQ-20 | Assert FAULT on over-temperature and shut down independently of firmware. Do not rely on the network or the MCU to prevent a thermal event. |
| STR-REQ-21 | Honour the carrier's fail-safe ENABLE: outputs off with ENABLE de-asserted, including during MCU reset and firmware update. |
| STR-REQ-22 | Populate the board ID mechanism (CAR-REQ-07) so one firmware image identifies this as a strobe. |

---

## 7. Out of scope

- Colour mixing algorithms and strobe pattern generation — host and firmware, not hardware.
- Any energy storage on the carrier board.
- Sound-to-light of any kind.

---

## 8. Design review gates

1. Energy budget table: flash energy, flash rate, resulting sustained draw, against the
   available budget from `D-01`. Must show the worst case (STR-REQ-05) explicitly.
2. Capacitor bank calculation with the assumed voltage window stated, plus ripple current and
   ESR justification.
3. Inrush analysis at the connector with the limiting element sized.
4. Thermal analysis at sustained average power **and** at peak pulse.
5. Simulated or measured rise/fall at the LED, against STR-REQ-11.
6. Fail-safe walkthrough: MCU held in reset, brownout, and cable unplug mid-flash.

---

## 9. Questions to resolve before starting

1. `D-02` — bank voltage. Everything else on this board follows from it.
2. `D-04` — white-only or RGBW.
3. Target flash energy and the maximum sustained flash rate the fixture promises. Currently
   assumed as 1 J and unbounded rate; the second half of that is unachievable and needs a real
   number before parts are chosen.
4. LED family and optic (STR-REQ-13 to STR-REQ-16) — no candidate has been evaluated yet.
