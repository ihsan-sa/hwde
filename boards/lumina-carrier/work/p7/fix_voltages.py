"""Add the magjack's cable-side nets to constraints.json `voltages`.

Second instance of the same class of bug as the DRC rule: the safety net was
watching the wrong nets, so it reported nothing.

`voltages` listed V48_RAW / V48_RTN / +48V_SW - all POST-bridge. But the
magjack's centre taps `/poe/POE_TAP_A1|A2|B1|B2` carry the full cable-side PoE
(up to 57 V) BEFORE rectification, and they were absent. Consequences:
  - P8 check_creepage could not see the 0.550 mm shield-to-tap gap;
  - it could not see tap-to-MDI proximity either.

Adding the taps at 57 V, and /poe/SHIELD at 0 V (it is tied to GND through the
1 M || 1 nF hybrid), makes check_creepage compute a 57 V pair across the
shield/tap boundary and REPORT the deviation instead of passing silently.

The goal here is visibility, not a green gate: the 0.550 mm is a property of the
part's land and cannot be fixed by pad sizing (both pads are already at JLC's
0.150 mm annular floor on 1.700 mm and 0.900 mm drills). It becomes an explicit
H4 accept-or-challenge item.

Writes the board-adjacent kicad/constraints.json AND the architecture source.
Idempotent.
"""
import io
import json

BOARD = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\constraints.json'
ARCH = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\constraints.json'

NEW = [
    {'net': '/poe/POE_TAP_A1', 'voltage': 57},
    {'net': '/poe/POE_TAP_A2', 'voltage': 57},
    {'net': '/poe/POE_TAP_B1', 'voltage': 57},
    {'net': '/poe/POE_TAP_B2', 'voltage': 57},
    {'net': '/poe/SHIELD', 'voltage': 0},
]

for path in (BOARD, ARCH):
    d = json.load(io.open(path, encoding='utf-8'))
    volt = d.setdefault('voltages', [])
    have = {v['net'] for v in volt}
    added = []
    for e in NEW:
        if e['net'] not in have:
            volt.append(e)
            added.append('%s=%dV' % (e['net'], e['voltage']))
    if added:
        io.open(path, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))
    print('%-14s %s' % (path.split('\\')[-2] + '/', added or 'already present'))
    print('   voltages now: %s' % [v['net'] for v in volt])
