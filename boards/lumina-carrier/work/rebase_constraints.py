"""P5 mandatory step: re-base the antenna keepout and the six plane regions.

board_init does NOT place the outline at (0,0) - the origin comes from the
packed component bbox - so architecture/constraints.json deliberately ships
`planes` without regions and no `keepouts` at all. Recipe: stackup.md s7.1.

Skipping this leaves the ESP32-S3 antenna sitting over a solid ground plane.
That is not cosmetic: H1 closed Q8 as "Wi-Fi is a supported control path", so
the antenna is a functional requirement.

Writes the board-adjacent kicad/constraints.json (the copy the P6/P7/P8 scripts
resolve), leaving architecture/constraints.json as the un-based source.
Idempotent.
"""
import io
import json

SRC = r'C:\dev\ai-ee3\boards\lumina-carrier\architecture\constraints.json'
DST = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\constraints.json'
RPT = r'C:\dev\ai-ee3\boards\lumina-carrier\work\board_init3.json'

rpt = json.load(io.open(RPT, encoding='utf-8'))
ex1, ey1, ex2, ey2 = rpt['outline_bbox']
print('outline_bbox: [%.3f, %.3f, %.3f, %.3f]  (%.1f x %.1f mm)'
      % (ex1, ey1, ex2, ey2, ex2 - ex1, ey2 - ey1))

d = json.load(io.open(SRC, encoding='utf-8'))
pl = d.setdefault('placement', {})

# --- antenna keepout ---------------------------------------------------------
pl['keepouts'] = [{
    'rect': [round(ex2 - 10, 3), round(ey1 + 29, 3), round(ex2, 3), round(ey1 + 51, 3)],
    'side': 'front',
    'reason': ('ESP32-S3-WROOM-1 antenna keepout - no copper on ANY layer. '
               'Wi-Fi is a supported control path (H1-Q8), so this is functional, '
               'not cosmetic. Espressif HDG wants the antenna overhanging the edge '
               'or a 6 mm-deep relief with >=15 mm lateral clearance; the fixed '
               '100x80 outline cannot overhang, so this band is the substitute.')}]

# --- six plane regions (a positive rect cannot have a hole) ------------------
d['planes'] = [
    {'layer': 'In1.Cu', 'net': 'GND',
     'region': [round(ex1, 3), round(ey1, 3), round(ex2, 3), round(ey1 + 29, 3)]},
    {'layer': 'In1.Cu', 'net': 'GND',
     'region': [round(ex1, 3), round(ey1 + 29, 3), round(ex2 - 10, 3), round(ey1 + 51, 3)]},
    {'layer': 'In1.Cu', 'net': 'GND',
     'region': [round(ex1, 3), round(ey1 + 51, 3), round(ex2, 3), round(ey2, 3)]},
    {'layer': 'In2.Cu', 'net': '+3V3',
     'region': [round(ex1 + 26, 3), round(ey1, 3), round(ex2, 3), round(ey1 + 29, 3)]},
    {'layer': 'In2.Cu', 'net': '+3V3',
     'region': [round(ex1 + 26, 3), round(ey1 + 29, 3), round(ex2 - 10, 3), round(ey1 + 51, 3)]},
    {'layer': 'In2.Cu', 'net': '+3V3',
     'region': [round(ex1 + 26, 3), round(ey1 + 51, 3), round(ex2, 3), round(ey2, 3)]},
]

d['_comment'] = (d.get('_comment', '') +
                 ' P5: keepout and plane regions RE-BASED from board_init outline_bbox '
                 'per stackup.md s7.1 - this file is the board-adjacent copy; '
                 'architecture/constraints.json stays un-based.')

io.open(DST, 'w', encoding='utf-8').write(json.dumps(d, indent=1, ensure_ascii=True))

print('\nantenna keepout : %s' % pl['keepouts'][0]['rect'])
print('plane regions   :')
for p in d['planes']:
    print('   %-8s %-6s %s' % (p['layer'], p['net'], p['region']))
print('\nwrote %s' % DST)
