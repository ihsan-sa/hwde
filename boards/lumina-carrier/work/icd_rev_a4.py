"""Re-issue connector-icd.md as rev A4.

Owner decisions landed after rev A3:
  - enclosure is SEALED with LED heat conducted through the wall (not vented)
  - CR-5 granted: PWM-domain dithering is a firmware requirement of record

Rev A3's "the at upgrade requires a vented enclosure" conclusion is therefore
withdrawn and replaced with a box-air heat BUDGET, which is the number a
daughter can actually design against. Idempotent.
"""
import io
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\connector-icd.md'
s = io.open(P, encoding='utf-8').read()

if 'rev A4' in s:
    print('already applied (rev A4 present) - no change')
    sys.exit(0)

START = "### 7.7 Internal-air temperature - RE-DERIVED at rev A3. NORMATIVE."
END = "---\n\n## 8. ENABLE, FAULT and the fail-safe contract"
i, j = s.find(START), s.find(END)
if i < 0 or j < 0:
    print('ABORT - could not locate s7.7 block')
    sys.exit(1)

NEW = """### 7.7 Thermal budget - RE-DERIVED at rev A4. NORMATIVE.

**Supersedes rev A3.** Rev A2's figures (56 C af / 69 C at) were internally inconsistent and were
withdrawn at A3 after the par raised it as a blocking issue - correctly. Rev A3 then concluded "the at
upgrade requires a vented enclosure". **That conclusion is now also withdrawn**, because the owner has
since decided the enclosure configuration, and it changes the arithmetic.

**Configuration of record (owner decision): SEALED, non-metallic, with LED heat conducted OUT through
the enclosure wall.** Not vented. Consistent with H1-Q5 (plastic enclosure, heatsink not
user-accessible).

**Why this changes the answer.** Rev A3 charged essentially the whole PoE budget to box air (~9.9 W af
/ ~19.2 W at) and unsurprisingly did not close. But the light engine is the large term, and in the
configuration of record the LED's heat (~6 W on the par) leaves through the wall rather than into the
box. Only the *electrical* losses that occur inside the box heat the air.

**The right number to publish is therefore a box-air heat BUDGET, not a temperature.** Sealed
non-metallic enclosure, internal-air-to-room resistance **3.6-4.3 K/W** (the par's independently
derived figure). Holding internal air to **70 C**, i.e. 15 K of margin below the +85 C limit shared by
the ESP32-S3 module and the par's emitter family:

| Room ambient | Allowable air rise | **Allowable box-air heat (4.3 K/W worst case ... 3.6 K/W)** |
|---|---|---|
| **25 C** | 45 K | **10.5 ... 12.5 W** |
| **30 C** | 40 K | **9.3 ... 11.1 W** |
| **40 C** | 30 K | **7.0 ... 8.3 W** |

**Spending against that budget:**

| Contributor | af (build 1) | at (upgrade) |
|---|---|---|
| Carrier overhead (PD + both converters + MCU + PHY) | ~2.4 W | ~3.7 W |
| Daughter driver + connector losses | daughter declares | daughter declares |
| LED junction heat | **through the wall, not into box air** | **through the wall** |

**Conclusions, binding on every LUMINA board:**

1. **A sealed enclosure closes for BOTH af and at**, provided the light engine's heat genuinely leaves
   through the wall and total box-air heat stays inside the table above. The carrier spends ~2.4 W
   (af) / ~3.7 W (at) of it.
2. **Every daughter must declare, in its design document, how its dissipation splits between box air
   and the enclosure wall.** A daughter that dumps its LED heat into box air instead of through the
   wall will breach the budget on its own - this is now the load-bearing assumption of the whole
   thermal case, so it must be stated, not assumed.
3. **The wall-conduction path is a mechanical requirement, not a nicety.** If the LED thermal path to
   the wall is not actually built, the numbers revert to the rev A3 case, which does not close at at.
4. **Stated room ambient: 25 C nominal, 30 C maximum for the at upgrade.** At a 40 C room the budget
   falls to 7.0-8.3 W and at becomes marginal again.
5. Every internal-air figure in this ICD carries an explicit room ambient. A figure quoted without one
   is incomplete.

### 7.8 Carrier firmware requirements of record

These are firmware commitments the carrier makes to its daughters. They are recorded here because a
daughter's requirements depend on them and they must not be silently dropped when firmware is written.

| ID | Requirement |
|---|---|
| **FW-01 (CR-5, granted)** | Carrier firmware **shall** apply **PWM-domain dithering of at least 3-4 bits**. This is the mechanism by which the par's PAR-REQ-01 is met - no hardware on that board can close it. **The dither must be in the PWM domain, NOT the 60 fps frame domain**: a 4.4 % dither at 60 Hz breaches IEEE 1789's no-effect level by itself, so frame-domain dithering would create the very flicker it is meant to avoid. |
| **FW-02 (CR-4, granted)** | Where a daughter runs four or more channels on one LEDC timer, firmware **shall** apply a **90 degree phase stagger** (`hpoint`) across them, to avoid a 4x larger input-current step when all channels switch together. Free in hardware. |
| **FW-03** | Firmware **shall** read `ID_ADC` at boot (s3.4) and **shall not** assert `ENABLE` on a FAULT (short) or NONE (open) reading. |
| **FW-04** | Firmware **shall** apply the daughter's declared channel -> timer -> frequency map (s3.5) from the `ID_ADC` code, rather than assuming all channels sit at the default rate. |
| **FW-05** | Firmware **shall** maintain the PD's MPS: valid MPS needs >= 10 mA DC, so the board must never idle below it (ESP32-S3 deep sleep is therefore forbidden while powered from PoE). |

"""

s = s[:i] + NEW + s[j:]
s = s.replace('A3 = ID_ADC codes, PWM/timer contract, re-derived thermals).',
              'A3 = ID_ADC codes + PWM/timer contract; '
              'A4 = sealed-with-wall-conduction thermal budget, firmware requirements).', 1)
s = s.replace('**Internal-air figures: see s7.7 (RE-DERIVED at rev A3 - the previous '
              '56 C / 69 C pair was wrong).**',
              '**Thermal budget: see s7.7 (rev A4 - box-air heat budget; the rev A2 '
              '56 C / 69 C pair was wrong and the rev A3 "must vent" conclusion is superseded).**', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('ICD rev A4 written OK')
print('non-ascii bytes:', sum(1 for c in s if ord(c) > 127))
for k in ('7.7 Thermal budget', '7.8 Carrier firmware', 'FW-01', 'rev A4'):
    print('  contains %-24s %s' % (k, k in s))
