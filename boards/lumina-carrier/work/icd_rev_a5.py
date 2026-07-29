"""Re-issue connector-icd.md s7.7 as rev A5.

Corrects rev A3/A4's characterisation of the rev A2 thermal figures. The
strobe run reproduced BOTH disputed numbers from a single binary - whether
the LED heat leaves through the enclosure wall or stays in the box - so the
56 C af figure was never miscalculated; its ASSUMPTION was simply never
written down. Only the `at` figure was a genuine error.

Also folds in the strobe's measured ~1.894 W of daughter heat into box air
with the wall path working, which lets the carrier's at-upgrade ventilation
question (open item D) be closed. Idempotent.
"""
import io
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\connector-icd.md'
s = io.open(P, encoding='utf-8').read()

if 'rev A5' in s:
    print('already applied (rev A5 present) - no change')
    sys.exit(0)

START = "### 7.7 Thermal budget - RE-DERIVED at rev A4. NORMATIVE."
END = "### 7.8 Carrier firmware requirements of record"
i, j = s.find(START), s.find(END)
if i < 0 or j < 0:
    print('ABORT - could not locate the s7.7 block')
    sys.exit(1)

NEW = """### 7.7 Thermal budget - rev A5. NORMATIVE.

**Configuration of record (owner decision): SEALED, non-metallic enclosure, with LED heat conducted
OUT through the enclosure wall.** Not vented. Consistent with H1-Q5.

#### 7.7.1 What was actually wrong with the rev A2 figures

Rev A2 published "56 C (af) / 69 C (at)". Rev A3 called both figures wrong. **That was unfair to the
af figure and is corrected here.** The strobe run applied the par's measured sealed-box resistance to
its own heat sources and reproduced both numbers from a single binary - whether the LED heat leaves
through the wall or stays inside the box:

| LED wall path | Heat into box air | Rise at 3.6-4.3 K/W | 25 C room | 35 C room | 40 C room |
|---|---|---|---|---|---|
| **works** | 1.894 W | 6.8-8.1 K | **32-33 C** | 42-43 C | 47-48 C |
| **fails** | 8.500 W | 30.6-36.6 K | **56-62 C** | 66-72 C | 71-77 C |

**Row B at a 25 C room is 56 C - the rev A2 af figure, to the degree.** So that figure was never
miscalculated. It was the *LED-heat-stays-in-the-box* case, at a 25 C room, and **neither assumption
was written down**. That omission is the whole defect: it made a correct number look arbitrary, and it
silently assumed exactly the arrangement the owner's enclosure decision has since ruled out.

**The `at` figure was a genuine error.** 69 C does not follow from the af point under *either* row -
convection is near-linear in delta-T at this scale, so roughly doubling box heat roughly doubles the
rise. 56 C implies ~3.13 K/W; 69 C implies ~2.29 K/W. They cannot both be true.

The par's independent Hoffman/Rittal calculation of **89-115 C** sits above even the LED-in-box case at
a 40 C room. It is the **conservative bound**, not a competing estimate - **do not average it** with
anything here.

#### 7.7.2 The budget (configuration of record)

Sealed non-metallic enclosure, internal-air-to-room **3.6-4.3 K/W**. Holding internal air to **70 C**,
i.e. 15 K below the +85 C limit shared by the ESP32-S3 module and the par's emitter family:

| Room ambient | Allowable air rise | **Allowable box-air heat (4.3 K/W worst case ... 3.6 K/W)** |
|---|---|---|
| **25 C** | 45 K | **10.5 ... 12.5 W** |
| **30 C** | 40 K | **9.3 ... 11.1 W** |
| **40 C** | 30 K | **7.0 ... 8.3 W** |

Spending against it, with the wall path working:

| Contributor | af (build 1) | at (upgrade) |
|---|---|---|
| Carrier overhead (PD + both converters + MCU + PHY) | ~2.4 W | ~3.7 W |
| Daughter into box air (strobe, measured) | ~1.9 W | ~1.9 W |
| **Total box-air heat** | **~4.3 W** | **~5.6 W** |
| LED junction heat | through the wall | through the wall |

#### 7.7.3 Conclusions - binding on every LUMINA board

1. **A sealed enclosure closes for BOTH af and at, and does so up to a 40 C room.** At 40 C the
   allowable budget is 7.0-8.3 W against ~5.6 W spent at `at`: internal air reaches
   40 + 5.6 x 4.3 = **64 C worst case**, under the 70 C target and well under the +85 C part limit.
   **The at upgrade therefore does NOT require enclosure ventilation** - the rev A3 conclusion that it
   did is withdrawn, and the carrier's open ventilation item is closed.
2. **This rests entirely on the LED heat leaving through the wall.** If that path is not built, the
   numbers revert to row B of s7.7.1 and the margin disappears. **The wall-conduction path is a
   mechanical requirement, not a nicety.**
3. **Every daughter must declare, in its design document, how its dissipation splits between box air
   and the enclosure wall.** The strobe's ~1.9 W is the number this budget is built on.
4. **Every internal-air figure in this ICD carries an explicit room ambient.** A figure quoted without
   one is incomplete - that is the exact defect that produced the rev A2 confusion.

"""

s = s[:i] + NEW + s[j:]
s = s.replace('A4 = sealed-with-wall-conduction thermal budget, firmware requirements).',
              'A4 = sealed-with-wall-conduction thermal budget + firmware requirements; '
              'A5 = thermal assumptions stated, at-ventilation item closed).', 1)
s = s.replace('**Thermal budget: see s7.7 (rev A4 - box-air heat budget; the rev A2 '
              '56 C / 69 C pair was wrong and the rev A3 "must vent" conclusion is superseded).**',
              '**Thermal budget: see s7.7 (rev A5 - box-air heat budget; the rev A2 af figure was '
              'correct under an unstated assumption, the at figure was not, and no venting is '
              'required).**', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('ICD rev A5 written OK')
print('non-ascii bytes:', sum(1 for c in s if ord(c) > 127))
for k in ('rev A5', '7.7.1 What was actually wrong', '7.7.3 Conclusions', 'does NOT require enclosure ventilation'):
    print('  contains %-40s %s' % (k, k in s))
