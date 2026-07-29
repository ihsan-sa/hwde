"""Re-issue connector-icd.md as rev A6 - two schematic-reviewer findings that
change what daughters must design against.

F6: /FAULT carries the carrier's own indicator LED as well as the pull-up, so
    a daughter asserting FAULT sinks ~4.3 mA, not the ~0.33 mA the ICD implied.
F3: the closed-loop energy governor reads IMON at 0.25-0.5 A, BELOW the pin's
    specified accuracy floor of 0.6 A - the ICD overclaims its precision.

Idempotent.
"""
import io
import re
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\connector-icd.md'
s = io.open(P, encoding='utf-8').read()

if 'rev A6' in s:
    print('already applied (rev A6 present) - no change')
    sys.exit(0)

# ---- F6: FAULT sink current ------------------------------------------------
# The s3.3 signal table row for FAULT. Match it loosely, then rewrite the row.
m = re.search(r'^\| `FAULT` \|.*$', s, re.M)
if not m:
    print('ABORT - could not find the FAULT row in s3.3')
    sys.exit(1)
old_row = m.group(0)
new_row = ("| `FAULT` | daughter -> carrier | open-drain, **active low** | Pulled up on the CARRIER "
           "(10 k to +3V3). **A daughter asserting FAULT must sink >= 5 mA** - REVISED at rev A6. The "
           "carrier's own red fault indicator (D22 + its ballast) also hangs on this net, so the real "
           "load is ~4.3 mA, not the ~0.33 mA implied by the pull-up alone. Any ordinary open-drain "
           "FET or MCU pin meets this; the number is published so no daughter sizes a marginal "
           "device. Well inside the carrier eFuse's 10 mA FLT limit. |")
s = s.replace(old_row, new_row, 1)

# ---- F3: IMON accuracy caveat ---------------------------------------------
anchor = "### 6.3 Where the cheap watts are"
if anchor not in s:
    print('ABORT - could not find s6.3 anchor')
    sys.exit(1)

CAVEAT = """#### 6.2.1 IMON accuracy - REVISED at rev A6. Read before relying on the governor.

The carrier's eFuse provides an analogue current-monitor output (`IMON`) to an MCU ADC, and s6.2
describes the average-energy governor as closed-loop on the strength of it. **That claim is now
qualified.**

The TPS16630 specifies `GAIN(IMON)` accuracy only for **I(OUT) >= 0.6 A** (25.66-30.14 uA/A over
0.6-2 A, and a second band 2-6 A). The rail's published sustained limits are **0.25 A (af) / 0.50 A
(at)** - **both below that floor**. So at the current the governor actually regulates against, the
transfer function has **no datasheet-guaranteed accuracy**.

What this does and does not mean:

- The measurement is still **monotonic and useful** - it is a real current monitor, not noise. It is
  fine for detecting gross overdraw, a stuck-on daughter, or a shorted rail.
- It is **not** a calibrated energy meter at 0.25-0.5 A. **Do not design a daughter that depends on
  the carrier metering its average power to better than roughly +/-20 % in that range** unless one of
  the following is done:
  1. **per-unit characterisation at build** (measure and store a correction in the daughter's
     I2C EEPROM - the ID scheme already provides somewhere to put it), or
  2. move the governor to a **shunt + amplifier** on a future carrier revision, or
  3. keep the governor conservative and treat IMON as a guard rather than a meter.

`R(IMON)` = 30 k is TI's own 1 A worked example and is otherwise correct; the issue is the operating
point, not the component.

"""
s = s.replace(anchor, CAVEAT + anchor, 1)

s = s.replace('A5 = thermal assumptions stated, at-ventilation item closed).',
              'A5 = thermal assumptions stated + at-ventilation closed; '
              'A6 = FAULT sink current, IMON accuracy caveat).', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('ICD rev A6 written OK')
print('non-ascii bytes:', sum(1 for c in s if ord(c) > 127))
for k in ('rev A6', 'must sink >= 5 mA', '6.2.1 IMON accuracy'):
    print('  contains %-24s %s' % (k, k in s))
