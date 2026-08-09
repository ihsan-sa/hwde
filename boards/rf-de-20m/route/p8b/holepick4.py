"""Final M2 clamp-hole placement.

Hard constraints, all from the board's own rules and the stock
MountingHole_2.2mm_M2 footprint:
  hole 2.2 mm NPTH -> hole edge >= that net's DRU clearance + 0.10 mm slack
  courtyard radius 2.00 mm (ISO 7380 button head, 3.8 mm) -> >= 2.05 mm centre-to-courtyard, i.e.
  0.05 mm of courtyard air, so no courtyards_overlap is introduced.
Objective: minimise distance to the Q201/Q202 centroid within each pocket.
"""
import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
DIE = (31.5, 25.0)
HOLE, CY = 2.2, 2.05   # MountingHole_2.2mm_M2_ISO7380: courtyard r = 2.00 mm
SLACK = 0.10
SEEDS = {'H5 north': (26.45, 15.45), 'H6 south-west': (24.05, 29.15),
         'H7 south-east': (33.15, 38.60)}
for name, (sx, sy) in SEEDS.items():
    best = None
    y = sy - 3.0
    while y <= sy + 3.0:
        x = sx - 3.0
        while x <= sx + 3.0:
            p = Point(x + OX, y + OY)
            if F.outline.buffer(-(F.EDGE + HOLE / 2)).contains(p) \
                    and F.copper.distance(p) >= HOLE / 2 + SLACK \
                    and F.courts.distance(p) >= CY:
                d = math.dist((x, y), DIE)
                if best is None or d < best[0]:
                    best = (d, x, y, F.copper.distance(p) - HOLE / 2,
                            F.courts.distance(p))
            x += 0.05
        y += 0.05
    if best is None:
        print(f'{name}: NONE'); continue
    d, x, y, cg, cyd = best
    print(f'{name}: local ({x:.2f}, {y:.2f})  abs ({x+OX:.3f}, {y+OY:.3f})  '
          f'd_die {d:.2f}  copper slack {cg:.3f}  courtyard {cyd:.3f}')
