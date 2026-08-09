import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
from shapely.ops import unary_union
OX, OY = F.OX, F.OY
HOLE = float(sys.argv[1]); HEAD = float(sys.argv[2])
HS = (5.0, 10.0, 36.0, 70.0)
pts = []
y = HS[1]
while y <= HS[3] + 1e-9:
    x = HS[0]
    while x <= HS[2] + 1e-9:
        if F.legal(x + OX, y + OY, HOLE, HEAD):
            pts.append((round(x, 2), round(y, 2)))
        x += 0.2
    y += 0.2
print(f'hole {HOLE} head {HEAD}: {len(pts)} legal cells')
u = unary_union([Point(*p).buffer(0.15) for p in pts])
gs = u.geoms if u.geom_type == 'MultiPolygon' else [u]
DIE = (31.5, 25.0)
out = []
for g in sorted(gs, key=lambda g: -g.area):
    b = g.bounds
    c = g.representative_point()
    # deepest point of the island = pole of inaccessibility approx
    best = max([p for p in pts if g.buffer(0.01).contains(Point(*p))],
               key=lambda p: min(math.dist(p, q) for q in [(b[0], p[1]), (b[2], p[1]), (p[0], b[1]), (p[0], b[3])]))
    out.append((g.area, b, best, math.dist(best, DIE)))
for a, b, best, d in out:
    print(f'  area {a:6.1f} mm2  bbox local [{b[0]:6.2f},{b[1]:6.2f},{b[2]:6.2f},{b[3]:6.2f}]  centre-ish ({best[0]:.1f},{best[1]:.1f})  d_die {d:.1f}')
