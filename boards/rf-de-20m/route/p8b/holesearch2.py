import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
OX, OY = F.OX, F.OY
DIE = (31.5, 25.0)
HS = (5.0, 10.0, 36.0, 70.0)


def scan(hole, head, step=0.1):
    pts = []
    y = HS[1]
    while y <= HS[3] + 1e-9:
        x = HS[0]
        while x <= HS[2] + 1e-9:
            if F.legal(x + OX, y + OY, hole, head):
                pts.append((round(x, 2), round(y, 2)))
            x += step
        y += step
    return pts


for hole, head, name in ((2.2, 4.5, 'M2 h4.5'), (2.2, 5.0, 'M2 h5.0'),
                         (2.7, 5.0, 'M2.5 h5.0'), (2.7, 4.7, 'M2.5 h4.7')):
    pts = scan(hole, head)
    print(f'--- {name}: {len(pts)} cells')
    for qx, qy, lab in ((-1, -1, 'NW'), (1, -1, 'NE'), (-1, 1, 'SW'), (1, 1, 'SE')):
        q = [p for p in pts if (p[0] - DIE[0]) * qx > 0 and (p[1] - DIE[1]) * qy > 0]
        if not q:
            print(f'   {lab}: none'); continue
        q.sort(key=lambda p: math.dist(p, DIE))
        print(f'   {lab}: ' + '  '.join(f'({a:.2f},{b:.2f}) d={math.dist((a,b),DIE):.2f}' for a, b in q[:4]))
