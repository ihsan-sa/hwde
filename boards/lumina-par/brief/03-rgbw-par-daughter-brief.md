# Design Brief — LUMINA RGBW Par Daughter Board

**Board ID:** LUM-DTR-PAR-A | **Rev:** A | **Date:** 2026-07-28
**Read first:** `00-lumina-system-context.md`, then `01-carrier-board-brief.md`
**Blocked on:** `D-01` (PoE class)

---

## 1. Mandate

The colour and mood workhorse. Where the strobe is a percussion instrument, the par is the
sustained voice — slow washes, saturated colour, breathing intensity envelopes. It runs
continuously rather than in bursts, so its problem is not peak power but **quality of
dimming** and **consistency between fixtures**.

Quantity: 6–8 of 8–12 total fixtures.

RGBW rather than RGB is settled. Mixing white from R+G+B produces a tinted, low-CRI white
that reads as wrong next to a real white emitter, and the profiles use white as a distinct
colour (SYS-REQ-07).

---

## 2. Behavioural spec

| ID | Requirement | Source |
|---|---|---|
| PAR-REQ-01 | Visually stepless dimming at 5–10 % of full output, with no perceptible stair-stepping during slow fades. | P2 outro (1–2 fixtures at 5–10 %), P6 intro (single fixture, low intensity) |
| PAR-REQ-02 | Slow colour drift across 2–3 adjacent hues over 8–16 bars — i.e. tens of seconds — without visible banding at the transitions. | P2 verse |
| PAR-REQ-03 | Pulse-and-decay envelope: rise to 80 %, decay to 30 % over ~200 ms, repeating per kick. | P2 São Paulo funk lock (SYS-REQ-05) |
| PAR-REQ-04 | Intensity tracking a continuously varying control signal at up to ~20 Hz. | P8 wobble bass (SYS-REQ-06) |
| PAR-REQ-05 | Deep saturated colour at medium brightness — purple, cyan, magenta, hot pink, neon blue, steel blue, mint. | P2, P5, P8 |
| PAR-REQ-06 | Consistent colour across all fixtures in the room. A synchronised full-room wash must not show per-fixture tint variation. | Every profile that uses all fixtures at once |

PAR-REQ-01 and PAR-REQ-06 are where cheap par fixtures fail and where this design earns its
existence.

---

## 3. Electrical requirements

| ID | Requirement |
|---|---|
| PAR-REQ-07 | Four independent constant-current channels: R, G, B, W. |
| PAR-REQ-08 | **PWM dimming, not analogue current dimming.** PWM holds the LED at a fixed drive current whenever it is on, so chromaticity stays constant across the dimming range; reducing drive current instead shifts hue and colour temperature, which breaks PAR-REQ-02 and PAR-REQ-06. |
| PAR-REQ-09 | Driver PWM dimming bandwidth must accept the carrier's PWM frequency (see CAR-REQ-12 — the default recommendation is ~10 kHz, and many constant-current modules do not go that high). Verify before selection, not after. |
| PAR-REQ-10 | Per-channel forward voltages differ substantially between red and blue/green/white emitters. The driver topology must accommodate that spread without wasting the difference as heat in a shared linear element. |
| PAR-REQ-11 | **Total-power clamp.** With ≈ 8.5 W sustained available (per `D-01`), four channels cannot all run at 100 %. Hardware must not be sized on the assumption that they can, and firmware must clamp the channel sum with a defined priority rule. Define that rule during design: naive clamping desaturates colours at high intensity, which is a visible artifact, not a graceful degradation. |
| PAR-REQ-12 | Thermistor to a carrier ADC or I²C pin; over-temperature shutdown independent of firmware. |
| PAR-REQ-13 | Honour the carrier's fail-safe ENABLE and populate the board ID mechanism (CAR-REQ-07, CAR-REQ-08). |

---

## 4. Optical requirements

| ID | Requirement |
|---|---|
| PAR-REQ-14 | Wide beam suitable for wash coverage from a 2.5 m ceiling. Adjacent fixtures should overlap; the room is 5 × 7 m with 6–8 pars. |
| PAR-REQ-15 | Diffusion sufficient that the four emitter colours mix before reaching a surface. Visible R/G/B/W shadow fringing on a wall is a failure. |
| PAR-REQ-16 | LED binning specified in the BOM for all four channels. Unbinned parts across 8 fixtures will not satisfy PAR-REQ-06. |
| PAR-REQ-17 | Provide for per-fixture calibration: measured per-channel scaling stored in the daughter board's ID EEPROM (CAR-REQ-07, EEPROM option) so firmware can normalise fixtures to each other. If the resistor-divider ID option is chosen instead, calibration has to live on the host, and that trade must be made deliberately. |

---

## 5. Out of scope

- Colour space conversion, gamma correction, and palette logic — host and firmware.
- Strobe behaviour. If a par needs to flash, it does so through its normal channels; it is not
  a strobe and should not be designed to compete with one.
- Moving head / pan-tilt. Phase 3 at the earliest, different board.

---

## 6. Design review gates

1. Sustained power table: four channels at realistic mixed-colour operating points, against
   the `D-01` budget, including the worst case the profiles actually call for (full-room warm
   wash at high intensity).
2. Dimming resolution analysis: PWM bits available at the chosen frequency, after gamma
   correction, at 5 % output — does PAR-REQ-01 hold?
3. Driver dimming bandwidth verified against the carrier PWM frequency.
4. Thermal analysis at continuous rated power. Unlike the strobe, this board runs hot
   continuously and has no duty-cycle relief.
5. Colour consistency plan: binning specification plus the calibration path.

---

## 7. Questions to resolve before starting

1. `D-01` — sets the total power available and therefore the LED and driver sizing.
2. Total-power clamp policy (PAR-REQ-11): preserve hue and sacrifice brightness, or preserve
   brightness and let colour drift? This is a lighting-design decision with a hardware
   consequence and it has not been made.
3. LED package: four discrete emitters, or an integrated RGBW multi-die package? Integrated
   packages mix better optically and simplify PAR-REQ-15; discrete emitters allow independent
   thermal management and cheaper sourcing.
4. Is a fifth channel (amber, or UV) worth the connector budget? P3 French melodic leans
   heavily on gold/amber, and RGBW amber is a mix rather than a true emitter. There are 8 PWM
   channels available and the par only uses 4.
