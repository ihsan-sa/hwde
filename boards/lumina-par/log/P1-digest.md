# P1 Research digest - lumina-par

Roster: 2x component-scout (LED driver, RGBW emitter), 1x reference-design
(continuous thermal + protection chain), 1x interface-spec (PWM dimming /
flicker / perceptual resolution). No power-architect: the rail tree is fixed by
ICD-01 s6.2 and the only open variable was which rail feeds the LED stage, which
became conflict C1 for the architect.

- **Thermal is the binding constraint, not the power budget.** A sealed
  120x100x60 mm non-metallic box is 3.6-4.3 K/W internal-air-to-room (Hoffman
  ~4.6 W/m2K, cross-checked vs Rittal k=5.5). Nothing on the PCB changes that
  number. Sealed caps total box heat at ~5.0 W for 45 C internal air in a 25 C
  room; minus the carrier's 2.4 W that leaves ~2.6 W of daughter heat = ~3-4 W of
  LED electrical power, **under half the af envelope**.
- **ICD s7.6's internal-air figures do not hold.** Its 69 C (at) is internally
  inconsistent with its own 56 C (af): convection is near-linear in dT at this
  scale, so ~2x the heat must give ~2x the rise (31 K -> ~60 K -> ~85 C), and the
  independent calculation gives 89-115 C. Optimistic by 20-46 K. Raised as a
  blocking issue against LUM-CAR-A under ICD s10 (OPEN-1).
- **PAR-REQ-01 at 5 % perceived fails at 13-bit by 8.9x** and needs ~17 bits;
  ESP32-S3 LEDC caps at 14. Two independent walls: resolution (17 bits) and
  driver settling (T <= 141 ns). New fact, verified from ESP-IDF source: LEDC does
  NOT rigidly couple frequency to resolution - "80 MHz / 2^n" is a maximum, so
  14-bit is available well below 4.88 kHz. Widens the trade space.
- **Flicker is over-specified.** IEEE 1789-2015 RP2 removes all modulation-depth
  restriction above 3 kHz; 9.766 kHz sits 3.3x above it. The 10 kHz-over-1.2 kHz
  camera call is confirmed (8.1x lower band contrast) but bounded: clean to
  120 fps, marginal at 240 fps, 960 fps unreachable at any usable LEDC setting.
- **No CC LED driver has an enable pin separate from its PWM pin.** On all five
  surviving candidates the dimming pin IS the enable, so ENABLE must be gated with
  each PWM line externally. The brief's "driver with an EN pin strongly preferred"
  is not achievable in this performance class.
- **Emitter is single-source.** The XINGLIGHT 4-in-1 is the only in-stock RGBW
  power emitter above 50 mA on the whole LCSC catalogue (318-part sweep; every
  Cree XLamp colour line at 0 stock), with no published Rth and no published Tj
  max. Fallback is RGB 3-in-1 + separate white at the cost of PAR-REQ-15.
- Orchestrator correction applied to `requirements.md`: s9 Q9(b) on-times were 10x
  high (1.4-6.1 us -> 141-646 ns), verified by independent recompute. Load-bearing:
  it moved the strict reading of PAR-REQ-01 from "several drivers manage it" to
  "no surveyed CC driver manages it by gating the converter".
