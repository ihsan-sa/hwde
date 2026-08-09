import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
HOLE, HEAD = 2.2, 4.5
DIE = (31.5, 25.0)
def best(x0, x1, y0, y1, key):
    out = []
    y = y0
    while y <= y1 + 1e-9:
        x = x0
        while x <= x1 + 1e-9:
            if F.legal(x + OX, y + OY, HOLE, HEAD):
                p = Point(x + OX, y + OY)
                m = min(F.copper.distance(p) - HOLE / 2.0, F.courts.distance(p) - HEAD / 2.0)
                out.append((x, y, m))
            x += 0.05
        y += 0.05
    out.sort(key=key)
    return out[:6]
print('SOUTH-EAST, x >= 31.5, maximise margin:')
for x, y, m in best(31.5, 36.0, 33.0, 42.0, lambda c: -c[2]):
    print(f'   ({x:.2f},{y:.2f}) margin {m:.3f} d_die {math.dist((x,y),DIE):.2f}')
print('SOUTH-WEST pocket, maximise margin near (24.05,29.15):')
for x, y, m in best(22.5, 25.5, 28.0, 31.0, lambda c: -c[2]):
    print(f'   ({x:.2f},{y:.2f}) margin {m:.3f} d_die {math.dist((x,y),DIE):.2f}')
print('NORTH, y<=20, maximise margin with x>=25.5:')
for x, y, m in best(25.5, 30.0, 12.0, 20.0, lambda c: -c[2]):
    print(f'   ({x:.2f},{y:.2f}) margin {m:.3f} d_die {math.dist((x,y),DIE):.2f}')
