"""One-shot: re-issue connector-icd.md as rev A3.

CR-1 (ID_ADC code allocation), PWM/timer contract correction, and the
re-derived internal-air thermals the par run raised as blocking.
Idempotent: aborts if any anchor is missing or the edit is already applied.
"""
import io
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\connector-icd.md'
s = io.open(P, encoding='utf-8').read()

if 'rev A3' in s:
    print('already applied (rev A3 present) - no change')
    sys.exit(0)

OLD_PWM = ("| `PWM0..7` | carrier -> daughter | push-pull CMOS | 3.3 V, default "
           "**13-bit at 9.766 kHz**. PWM0-3 = LEDC timer 0, PWM4-7 = LEDC timer 1. "
           "**Channels on the same timer share frequency AND resolution** (CAR-REQ-11). "
           "LEDC timers 2 and 3 are unallocated and available on request |")
NEW_PWM = ("| `PWM0..7` | carrier -> daughter | push-pull CMOS | 3.3 V, LEDC channels 0-7, "
           "low-speed mode only. **The carrier no longer hard-assigns timers** - see s3.5. "
           "Default profile is 13-bit at 9.766 kHz; 14-bit at 4.883 kHz is also offered. "
           "**Channels sharing a timer share frequency AND resolution** (CAR-REQ-11) |")

OLD_HZ = ("| **DC-DC hot zone** | **(2, 46) - (36, 68)** | **No LED drivers and no aluminium "
          "electrolytics** in the corresponding region on the daughter. The carrier's 48->12 "
          "converter dissipates up to 1.25 W here in a sealed box whose internal air reaches "
          "56 C (af) / 69 C (at); electrolytic life halves per 10 C.")
NEW_HZ = ("| **DC-DC hot zone** | **(2, 46) - (36, 68)** | **No LED drivers and no aluminium "
          "electrolytics** in the corresponding region on the daughter. The carrier's 48->12 "
          "converter dissipates up to 1.25 W here. **Internal-air figures: see s7.7 (RE-DERIVED "
          "at rev A3 - the previous 56 C / 69 C pair was wrong).** Electrolytic life halves per 10 C.")

ID_SECTION = """### 3.4 `ID_ADC` - daughter board type codes (CAR-REQ-07). NORMATIVE.

Added at rev A3 in response to CR-1. **The carrier owns this code space; daughters must use an
allocated code and must not invent one.**

**Circuit.** The carrier fits the **top** leg: **10 kOhm 1% from `ID_ADC` to +3V3**, plus the 1 kOhm
series protection resistor to the MCU ADC pin (no DC current flows in it, so it adds no divider
error). The **daughter fits the bottom leg**, `R_ID` from `ID_ADC` to `GND`.

`V_ID = 3.3 V x R_ID / (R_ID + 10k)`

| Code | `R_ID` (daughter, 1%) | Nominal `V_ID` | Board |
|---|---|---|---|
| **FAULT** | short to GND | < 0.15 V | Shorted connector or mis-seated daughter - firmware must NOT assert ENABLE |
| **1** | **2.7 kOhm** | 0.702 V | **LUM-STR-A** (strobe) |
| **2** | **4.7 kOhm** | 1.055 V | **LUM-PAR-A** (RGBW par) |
| **3** | 7.5 kOhm | 1.414 V | reserved |
| **4** | 12 kOhm | 1.800 V | reserved |
| **5** | 18 kOhm | 2.121 V | reserved |
| **6** | 30 kOhm | 2.475 V | reserved |
| **NONE** | open (no daughter) | > 2.9 V | No daughter fitted - firmware must NOT assert ENABLE |

**Why these values.** Minimum adjacent-code separation is **0.353 V** (code 1 to code 2), against a
worst-case divider error of about +/-0.05 V from 1 % resistors. A **+/-0.15 V** detection window per
code is therefore safe and is what carrier firmware shall use. The top code stops at 2.475 V because
the ESP32-S3 ADC saturates near 3.1 V at 12 dB attenuation, so a higher code could not be
distinguished from "open".

**Firmware contract.** The code selects the daughter profile that configures the LEDC timers (s3.5).
FAULT and NONE both mean **ENABLE stays de-asserted**.

### 3.5 PWM channel and timer allocation (CAR-REQ-11). NORMATIVE.

Revised at rev A3. **The previous statement that PWM0-3 sit on LEDC timer 0 and PWM4-7 on timer 1 is
withdrawn** - it was wrong for the strobe and would have mis-specified two boards.

**Hardware ceiling (ESP32-S3 LEDC, not negotiable):** 8 channels, **4 timers**, low-speed mode only,
**14-bit maximum** duty resolution. Channels sharing a timer share **both** frequency and resolution.
At a timer's maximum resolution the duty value must clamp to `2^n - 1`.

| Mode | Resolution | Frequency | Levels |
|---|---|---|---|
| **Default** | 13-bit | **9.766 kHz** | 8192 |
| **Optional (CR-3, granted)** | 14-bit | **4.883 kHz** | 16384 |

The 14-bit mode is offered because it doubles low-end resolution; it costs camera-flicker margin, so
it is opt-in per daughter and must be re-tested against a phone camera on the first prototype.

**The carrier does not hard-assign timers.** Each daughter declares its own channel -> timer ->
frequency map in its design document; carrier firmware applies that map from the `ID_ADC` code.

| Board | Channels | Timer map |
|---|---|---|
| **LUM-PAR-A** | PWM0-3 (RGBW) | all four on **one** timer, 13-bit / 9.766 kHz. Three timers remain free. **90 degree phase stagger** across the four channels - see below |
| **LUM-STR-A** | PWM0-7 (RGBW strobe) | colour dimming on one timer at the default rate; **the flash gate is NOT a duty setting** - see below |
| No daughter / unknown code | - | all channels held low, ENABLE de-asserted |

**Strobe flash gating - correcting an ICD default.** A 5-200 ms flash cannot be expressed as a duty
value at 9.766 kHz, because one LEDC period is **102.4 us** and a 5 ms flash is only ~49 periods. The
strobe therefore either drives its flash line as a **GPIO / RMT one-shot**, or **re-programs the timer
it owns** to the flash rate. Both are legal on this connector - these pins are ordinary GPIOs and
nothing on the carrier forces them into LEDC. **It is therefore NOT true that all 8 channels sit at
the default frequency.**

**CR-4 granted - 90 degree phase stagger.** LEDC supports a per-channel phase offset (`hpoint`), so
staggering four channels by 90 degrees costs nothing in hardware and avoids a 4x larger input-current
step when all four switch together. Carrier firmware shall apply it for any daughter running four or
more channels on one timer. Firmware default, not a connector change.

"""

THERMAL = """### 7.7 Internal-air temperature - RE-DERIVED at rev A3. NORMATIVE.

**The rev A2 figures (56 C af / 69 C at) were wrong and are withdrawn.** The par run raised this as a
blocking issue and was correct: the two numbers were mutually inconsistent. Natural convection is
close to linear in delta-T at this scale, so roughly doubling the box heat roughly doubles the rise -
56 C and 69 C cannot both be true. The 56 C point implies ~3.13 K/W; the 69 C point implies ~2.29 K/W.

**Corrected basis.** A sealed non-metallic enclosure of this size is **3.6-4.3 K/W** (the par's
independently derived figure, which supersedes the ~3.13 K/W implied by the old af point - the
original carrier figure was optimistic).

| Case | Box heat | Rise at 3.6-4.3 K/W | Internal air, **25 C room** | Internal air, **40 C room** |
|---|---|---|---|---|
| **802.3af (build 1)** | ~9.9 W | 36-43 K | **61-68 C** | **76-83 C** |
| **802.3at (upgrade)** | ~19.2 W | 69-83 K | **94-108 C** | **109-123 C** |

**Conclusions, binding on every LUMINA board:**

1. **A sealed enclosure does NOT close for the 802.3at upgrade.** 94-108 C internal air at a 25 C room
   exceeds the ESP32-S3 module's +85 C ambient limit and the par's emitter family's +85 C `Topr` max.
   **The at upgrade requires a vented enclosure.** This confirms and hardens the flag raised by the P1
   power architect ("the at upgrade needs enclosure vents OR a confirmed ambient below ~30 C") - that
   flag never reached the rev A2 numbers, which is how the error survived.
2. **802.3af closes only at a room ambient near 25 C**, and is already marginal at 40 C (76-83 C
   against +85 C parts). **Stated room ambient for the af build: 25 C nominal, 30 C maximum.** The Q13
   provisional answer of "0-40 C ambient, sealed" is **not** compatible with the af build either and
   must be revisited by the owner.
3. **Every internal-air figure in this ICD now carries an explicit room ambient.** A daughter quoting
   an internal-air number without one is quoting an incomplete figure.

**This is an owner decision, not a board decision** - it concerns the enclosure, which no board run
owns. Escalated at the carrier's H2.

"""

A1 = "## 4. Current rating per pin, and the CAR-REQ-13 margin proof"
A2 = "## 8. ENABLE, FAULT and the fail-safe contract"

for anchor, label in ((OLD_PWM, 'PWM row'), (OLD_HZ, 'hot-zone row'), (A1, 's4 heading'), (A2, 's8 heading')):
    if anchor not in s:
        print('ABORT - anchor missing: %s' % label)
        sys.exit(1)

s = s.replace(OLD_PWM, NEW_PWM, 1)
s = s.replace(OLD_HZ, NEW_HZ, 1)
s = s.replace(A1, ID_SECTION + '---\n\n' + A1, 1)
s = s.replace(A2, THERMAL + '---\n\n' + A2, 1)
s = s.replace('**Status: DRAFT, frozen at H1.**',
              '**Status: frozen at H1. Rev A3** '
              '(A2 = 0.635 mm creepage + bank-charging contract; '
              'A3 = ID_ADC codes, PWM/timer contract, re-derived thermals).', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('ICD rev A3 written OK')
print('non-ascii bytes:', sum(1 for c in s if ord(c) > 127))
for k in ('3.4 `ID_ADC`', '3.5 PWM channel', '7.7 Internal-air'):
    print('  contains %-22s %s' % (k, k in s))
