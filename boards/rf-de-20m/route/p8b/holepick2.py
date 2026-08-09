"""Final clamp-hole choice. Objective is mechanical, not aesthetic: get the die
pair as far INSIDE the bolt polygon as the copper allows, so maximise x on the
north side and on the south side (the die sits at local x 31.5) subject to a
>= 0.15 mm margin beyond every DRU clearance."""
import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
HOLE, HEAD = 2.2, 4.5
MARGIN = 0.15
DIE = (31.5, 25.0)
HS = (5.0, 10.0, 36.0, 70.0)

cells = []
y = HS[1]
while y <= HS[3] + 1e-9:
    x = HS[0]
    while x <= HS[2] + 1e-9:
        if F.legal(x + OX, y + OY, HOLE, HEAD):
            p = Point(x + OX, y + OY)
            m = min(F.copper.distance(p) - HOLE / 2.0, F.courts.distance(p) - HEAD / 2.0)
            if m >= MARGIN:
                cells.append((round(x, 2), round(y, 2), m))
        x += 0.05
    y += 0.05
print(f'{len(cells)} cells with margin >= {MARGIN} mm')
bands = {'north  y<22': lambda c: c[1] < 22.0,
         'south  y>28, y<42': lambda c: 28.0 < c[1] < 42.0,
         'south2 y>42': lambda c: c[1] > 42.0}
for lab, f in bands.items():
    q = [c for c in cells if f(c)]
    if not q:
        print(f'  {lab}: none'); continue
    q.sort(key=lambda c: (-c[0], abs(c[1] - DIE[1])))
    for c in q[:4]:
        print(f'  {lab}: ({c[0]:.2f},{c[1]:.2f}) margin {c[2]:.3f}  d_die {math.dist(c[:2],DIE):.2f}')
