"""rf-de-20m P7 - the EPC2019 thermal via field.

constraints.json thermal[] asks for >= 10 x 0.3 mm copper-filled vias per FET,
"BESIDE the source lands, not in them - the EPC2019's solder bars are ~0.2 mm
wide and cannot take a via" (parts/C2836675.json layout_notes).  They carry the
whole board-side thermal path (RthJB 7.5 C/W is inside the package) and the
source return into In1/In2/B.Cu.

They go in the GND landing lobes immediately above Q201 and below Q202, which
is the closest copper the 0.8 mm /SW rule allows.
"""
import json
import os
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import Point                                 # noqa: E402
from shapely.ops import unary_union                                # noqa: E402

PCB = os.environ.get('AIEE_PCB',
                     r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_thermal.json'
VIA_D, VIA_DRILL, H2H = 0.6, 0.3, 0.5
CLR = {'/SW': 0.8, '/tank/TANK_A': 0.8, '/tank/TANK_B': 0.8,
       '/tank/RFOUT': 0.8, '+40V': 0.5}

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

blk = []
for p in bg.pads_of():
    if p.net != 'GND':
        blk.append(p.poly.buffer(CLR.get(p.net, 0.1016)))
    if p.drill is not None:
        blk.append(p.drill_poly.buffer(H2H))
for t in bg.tracks_of():
    if t.net != 'GND':
        blk.append(t.shape.buffer(t.width / 2.0 + CLR.get(t.net, 0.1016)))
for v in bg.vias_of():
    blk.append(Point(*v.at).buffer(v.drill / 2.0 + H2H))
blocked = unary_union(blk)
gnd = bg.net_copper('GND', 'F.Cu')

placed, ops = [], []


def field(x0, y0, x1, y1, tag):
    n, step = 0, 0.05
    cand = []
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            cand.append((x + OX, y + OY))
            x += step
        y += step
    # greedy: take the candidate furthest from everything already placed
    while True:
        best = None
        for ax, ay in cand:
            pad = Point(ax, ay).buffer(VIA_D / 2.0, quad_segs=16)
            if not gnd.contains(pad) or blocked.intersects(pad):
                continue
            if any((ax - px) ** 2 + (ay - py) ** 2 < (VIA_DRILL + H2H) ** 2
                   for px, py in placed):
                continue
            d = min((((ax - px) ** 2 + (ay - py) ** 2) ** .5
                     for px, py in placed), default=1e9)
            if best is None or d > best[0]:
                best = (d, ax, ay)
        if best is None:
            break
        _, ax, ay = best
        placed.append((ax, ay))
        ops.append({"op": "add_via", "at": [round(ax, 4), round(ay, 4)],
                    "size": VIA_D, "drill": VIA_DRILL, "net": "GND"})
        n += 1
    print(f'  {tag}: {n} vias')
    return n


print('EPC2019 thermal via fields:')
n1 = field(29.95, 19.55, 33.55, 22.85, 'above Q201')
n1 += field(32.55, 20.45, 33.55, 23.05, 'east flank Q201')
n2 = field(29.95, 27.15, 33.55, 30.45, 'below Q202')
n2 += field(32.55, 26.95, 33.55, 29.55, 'east flank Q202')
json.dump({"version": 1, "ops": ops}, open(OPS, 'w'), indent=1)
print(f'Q201 {n1} / Q202 {n2} (constraints ask >= 10 each) -> {OPS}')
