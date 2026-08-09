import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
DIE = (31.5, 25.0)
HOLE = float(sys.argv[1]) if len(sys.argv) > 1 else 3.2
HEAD = float(sys.argv[2]) if len(sys.argv) > 2 else 5.5
print(f'ring probe, hole {HOLE}, head {HEAD}  (C=copper/HV-pour, Y=courtyard, E=edge, .=LEGAL)')
for r in (5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
    row = ''
    for i in range(72):
        a = math.radians(i * 5)
        x, y = DIE[0] + r * math.sin(a), DIE[1] - r * math.cos(a)   # 0 deg = north
        p = Point(x + OX, y + OY)
        if not F.outline.buffer(-(F.EDGE + HOLE / 2)).contains(p):
            row += 'E'
        elif F.copper.intersects(p.buffer(HOLE / 2)):
            row += 'C'
        elif F.courts.intersects(p.buffer(HEAD / 2)):
            row += 'Y'
        else:
            row += '.'
    print(f'r={r:4.1f} N{row[:18]}E{row[18:36]}S{row[36:54]}W{row[54:]}')
