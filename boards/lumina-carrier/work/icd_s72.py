"""Freeze ICD s7.2 connector coordinates from the P6 placement, and correct
s7.4 mechanism 3, which the y-shift made literally untrue.

Idempotent.
"""
import io
import sys

P = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\connector-icd.md'
s = io.open(P, encoding='utf-8').read()

if 'FROZEN at P6' in s:
    print('already applied - no change')
    sys.exit(0)

BLOCK = """### 7.2 Connector positions - **FROZEN at P6**

Board-relative to the top-left corner, x right / y down. Absolute board origin is
(19.58, 57.132); subtract it from any absolute coordinate read off the .kicad_pcb.

| Item | Origin | Rot | Position 1 | Even-row y | Land extent |
|---|---|---|---|---|---|
| **J3** POWER 2x7 | **(23.00, 76.00)** | 0 | **(15.380, 77.270)** | 74.730 | (14.11, 73.50) - (31.89, 78.50) |
| **J4** SIGNAL 2x12 | **(71.00, 76.00)** | 0 | **(57.030, 77.270)** | 74.730 | (55.76, 73.50) - (86.24, 78.50) |
| **H5** support hole | **(46.00, 74.00)** | - | - | - | exactly the s7.1 normative value, unchanged |
| **J1** RJ45 body | (11.88, 0.00) - (30.12, 21.74) | - | - | - | see note |

**What moved from the provisional values, and why.** x is within +/-0.3 mm of the
provisional figures. **y moved DOWN 7.97 mm**: the provisional y = 69.3 left the connector
courtyards 6.9 mm off the bottom edge, which fails placelib's 2.5 mm declared-edge tolerance -
the connectors have to sit at the edge they are declared on.

**J1 moved 5.75 mm left** onto the ICD's nominal (10,0)-(32,22) envelope. That is a real
improvement for the daughters: the previous position left only **0.13 mm** of margin inside the
30 x 26 mm notch, which is not a margin. It now has room.

**Daughters may now design to these numbers.** They were provisional until P6 because placement
had not run; they are frozen now.

"""

start = s.find('### 7.2 ')
if start < 0:
    print('ABORT - s7.2 heading not found')
    sys.exit(1)
nxt = s.find('### 7.3', start)
if nxt < 0:
    print('ABORT - s7.3 heading not found')
    sys.exit(1)
s = s[:start] + BLOCK + s[nxt:]

# --- s7.4 mechanism 3 is no longer literally true after the y shift ---------
old_hits = 0
for cand in ("neither lands on", "neither land on"):
    if cand in s:
        old_hits += 1
if old_hits:
    s = s.replace(
        "neither lands on",
        "(CORRECTED at P6 - about the board centre (50, 40), J4's centre (71, 76) now maps to "
        "(29, 4), which falls inside the RJ45's own footprint region (10,0)-(32,22) rather than "
        "on empty board. Mechanisms 1, 2 and 4 are unaffected and the interlock still holds; "
        "only this sentence's claim that neither lands on", 1)

s = s.replace('A6 = FAULT sink current, IMON accuracy caveat).',
              'A6 = FAULT sink current + IMON accuracy caveat; '
              'A7 = s7.2 connector coordinates FROZEN at P6, s7.4 mech-3 corrected).', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('ICD s7.2 frozen; s7.4 mechanism-3 corrected (%d site)' % old_hits)
print('non-ascii bytes:', sum(1 for c in s if ord(c) > 127))
