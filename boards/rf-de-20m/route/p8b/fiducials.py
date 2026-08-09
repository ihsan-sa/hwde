"""W3 - three global fiducials, Fiducial_1mm_Mask2mm (1 mm Cu / 2 mm mask).

Legality: the pad is NETLESS copper, so it needs >= 0.6 mm (its own footprint
clearance, and more than the 0.1016 mm floor) to every track/pad/via, plus its
own 1.25 mm courtyard clear of every other courtyard, plus edge clearance.
A GND pour simply voids around it - that is not a violation.
SPIRAL-6 hygiene: >= 15 mm from either spiral's outer copper edge.
"""
import sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
sys.path.insert(0, r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b')
import freespace as F
from shapely.geometry import Point
from shapely.ops import unary_union

OX, OY = F.OX, F.OY
PADR, CLR, CYR = 0.5, 0.6, 1.25
MASKR = 1.0
SPIRAL = [(72.0, 17.6, 19.70), (87.6, 62.6, 19.70)]   # centre + outer Cu radius
CLAMP = [(26.25, 11.35), (26.15, 36.80), (34.50, 49.70)]
HS = (5.0, 10.0, 36.0, 70.0)


def legal(x, y):
    p = Point(x + OX, y + OY)
    if not F.outline.buffer(-(2.0 + MASKR)).contains(p):
        return False
    # F.copper is already buffered by each item's own clearance, so 1.0 mm here
    # is ~1.1 mm to real copper - the fiducial pad's 0.5 mm radius plus its
    # footprint clearance of 0.6 mm. That is also what keeps foreign copper out
    # of the 2 mm mask window, which is what the vision system reads.
    if F.copper.distance(p) < 1.0:
        return False
    if F.courts.distance(p) < CYR + 0.05:
        return False
    for cx, cy in CLAMP:
        if math.dist((x, y), (cx, cy)) < 3.0:
            return False
    for cx, cy, r in SPIRAL:
        if math.dist((x, y), (cx, cy)) < r + 15.0:
            return False
    # HS-2 is a BOTTOM-face constraint; an F.Cu/F.Mask fiducial does not touch
    # it. Only the three new clamp holes are excluded above.
    return True


pts = []
y = 3.0
while y <= 77.0:
    x = 3.0
    while x <= 117.0:
        if legal(x, y):
            pts.append((round(x, 1), round(y, 1)))
        x += 0.5
    y += 0.5
print(f'{len(pts)} legal fiducial cells')
corners = {'NW': (3, 3), 'NE': (117, 3), 'SW': (3, 77), 'SE': (117, 77)}
for lab, c in corners.items():
    q = sorted(pts, key=lambda p: math.dist(p, c))[:3]
    print(f'  {lab}: ' + '  '.join(f'({a},{b})' for a, b in q))
