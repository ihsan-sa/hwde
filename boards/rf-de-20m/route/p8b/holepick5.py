import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
from shapely.ops import unary_union
OX, OY = F.OX, F.OY
DIE = (31.5, 25.0)
HOLE, CY, SLACK = 2.2, 2.05, 0.05
HS = (5.0, 10.0, 36.0, 70.0)
pts = []
y = HS[1]
while y <= HS[3] + 1e-9:
    x = HS[0]
    while x <= HS[2] + 1e-9:
        p = Point(x + OX, y + OY)
        if F.outline.buffer(-(F.EDGE + HOLE / 2)).contains(p) \
                and F.copper.distance(p) >= HOLE / 2 + SLACK \
                and F.courts.distance(p) >= CY:
            pts.append((round(x, 2), round(y, 2)))
        x += 0.1
    y += 0.1
print(f'{len(pts)} legal M2/ISO7380 cells in HS-2')
u = unary_union([Point(*p).buffer(0.08) for p in pts])
gs = u.geoms if u.geom_type == 'MultiPolygon' else [u]
for g in sorted(gs, key=lambda g: -g.area)[:14]:
    b = g.bounds
    inside = [p for p in pts if g.buffer(0.01).contains(Point(*p))]
    near = min(inside, key=lambda p: math.dist(p, DIE))
    print(f'  area {g.area:6.2f}  bbox [{b[0]:6.2f},{b[1]:6.2f},{b[2]:6.2f},{b[3]:6.2f}]'
          f'  closest ({near[0]:.2f},{near[1]:.2f}) d_die {math.dist(near,DIE):5.2f}')
