"""Pick the final clamp-hole centres: inside each legal pocket, take the point
with the largest clearance margin (distance from the hole edge to the nearest
blocker) while staying inside the pocket."""
import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
HOLE, HEAD = 2.2, 4.5
SEEDS = {'H5 NW': (26.60, 15.70), 'H6 SW': (24.20, 28.70), 'H7 SE': (33.30, 38.40)}
DIE = (31.5, 25.0)
for name, (sx, sy) in SEEDS.items():
    best = None
    y = sy - 1.5
    while y <= sy + 1.5:
        x = sx - 1.5
        while x <= sx + 1.5:
            if F.legal(x + OX, y + OY, HOLE, HEAD):
                p = Point(x + OX, y + OY)
                m = min(F.copper.distance(p) - HOLE / 2.0,
                        F.courts.distance(p) - HEAD / 2.0)
                if best is None or m > best[0]:
                    best = (m, x, y)
            x += 0.05
        y += 0.05
    m, x, y = best
    p = Point(x + OX, y + OY)
    print(f'{name}: local ({x:.2f}, {y:.2f})  abs ({x+OX:.3f}, {y+OY:.3f})  '
          f'margin {m:.3f} mm  copper gap {F.copper.distance(p)-HOLE/2:.3f}  '
          f'courtyard gap {F.courts.distance(p)-HEAD/2:.3f}  d_die {math.dist((x,y),DIE):.2f}')
