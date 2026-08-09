import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
DIE = (31.5, 25.0)
HOLE, CY, SLACK = 2.2, 2.05, 0.05
def scan(x0, x1, y0, y1, step=0.05):
    out = []
    y = y0
    while y <= y1 + 1e-9:
        x = x0
        while x <= x1 + 1e-9:
            p = Point(x + OX, y + OY)
            if F.outline.buffer(-(F.EDGE + HOLE / 2)).contains(p):
                cg = F.copper.distance(p) - HOLE / 2
                cy = F.courts.distance(p)
                if cg >= SLACK and cy >= CY:
                    out.append((round(x, 2), round(y, 2), cg, cy))
            x += step
        y += step
    return out
print('NORTH pocket (26.5,11.5):')
for c in sorted(scan(25.5, 27.5, 10.5, 12.5), key=lambda c: -min(c[2], c[3] - CY))[:4]:
    print(f'   ({c[0]:.2f},{c[1]:.2f}) cu+{c[2]:.3f} cy {c[3]:.3f} d {math.dist(c[:2],DIE):.2f}')
print('SOUTH, closest to the die:')
for c in sorted(scan(17.9, 35.9, 35.9, 40.0), key=lambda c: math.dist(c[:2], DIE))[:4]:
    print(f'   ({c[0]:.2f},{c[1]:.2f}) cu+{c[2]:.3f} cy {c[3]:.3f} d {math.dist(c[:2],DIE):.2f}')
print('SOUTH-EAST, x >= 33, closest to the die:')
for c in sorted(scan(33.0, 35.9, 35.9, 42.0), key=lambda c: math.dist(c[:2], DIE))[:4]:
    print(f'   ({c[0]:.2f},{c[1]:.2f}) cu+{c[2]:.3f} cy {c[3]:.3f} d {math.dist(c[:2],DIE):.2f}')
print('SOUTH-WEST, x <= 22, closest to the die:')
for c in sorted(scan(17.9, 22.0, 35.9, 44.0), key=lambda c: math.dist(c[:2], DIE))[:4]:
    print(f'   ({c[0]:.2f},{c[1]:.2f}) cu+{c[2]:.3f} cy {c[3]:.3f} d {math.dist(c[:2],DIE):.2f}')
