"""rf-de-20m P8-b (E5) - fill EVERY legal 0.3 mm GND thermal via around the
EPC2019 pair, without touching a rule.

Legality is the board's own rule set, read off the .kicad_dru, not a guess:
  * the 0.6 mm via land must sit inside the F.Cu GND island (a thermal via has
    to start in the copper the die's source bars pour into);
  * >= that net's clearance to every non-GND item - 0.8 mm to /SW (the rule
    that caps the field), 0.5 mm to +40V, 0.1016 mm otherwise;
  * hole_to_hole >= 0.5 mm to every existing drill (0.8 mm centre pitch for
    0.3 mm drills);
  * clear of the three new M2 clamp holes.
Nearest-die-first insertion: the lateral run in 35 um F.Cu is the expensive
leg, so barrels are packed inwards-out.
"""
import json, os, sys, math
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board
from shapely.geometry import Point
from shapely.ops import unary_union

PCB = os.environ.get('AIEE_PCB', r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
OUT = r'C:/dev/ai-ee3/boards/rf-de-20m/route/p8b/ops_thermal_vias.json'
VIA_D, VIA_DRILL, H2H = 0.6, 0.3, 0.5
CLR = {'/SW': 0.8, '/tank/TANK_A': 0.8, '/tank/TANK_B': 0.4,
       '/tank/RFOUT': 0.8, '+40V': 0.5}
DEF = 0.1016
CLAMP = [(26.50, 15.60, 2.2), (24.45, 28.75, 2.2), (33.50, 38.40, 2.2)]
DIES = (('Q201', 31.5, 22.9), ('Q202', 31.5, 27.1))
REACH = 5.0        # mm from the die centroid: past this the barrel is a
                   # lateral-spreading problem, not a thermal via

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

blk = []
for p in bg.pads_of():
    if p.net != 'GND':
        blk.append(p.poly.buffer(CLR.get(p.net, DEF)))
    if p.drill is not None:
        blk.append(p.drill_poly.buffer(H2H))
for t in bg.tracks_of():
    if t.net != 'GND':
        blk.append(t.shape.buffer(t.width / 2.0 + CLR.get(t.net, DEF)))
for z in bg.zones_of():
    if z.net == 'GND':
        continue
    for lay in bg.copper_layers:
        f = z.fill_on(lay)
        if f is not None and not f.is_empty:
            blk.append(f.buffer(CLR.get(z.net, DEF)))
for cx, cy, d in CLAMP:
    blk.append(Point(cx + OX, cy + OY).buffer(d / 2.0 + H2H))
blocked = unary_union(blk)
gnd = bg.net_copper('GND', 'F.Cu')
existing = [tuple(v.at) for v in bg.vias_of()]
placed = []
ops = []


def ok(ax, ay):
    pad = Point(ax, ay).buffer(VIA_D / 2.0, quad_segs=16)
    if not gnd.contains(pad):
        return False
    if blocked.intersects(pad):
        return False
    lim = (VIA_DRILL + H2H) ** 2
    for px, py in existing + placed:
        if (ax - px) ** 2 + (ay - py) ** 2 < lim - 1e-9:
            return False
    return True


for ref, cx, cy in DIES:
    cand = []
    n = int(REACH / 0.05)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = cx + i * 0.05, cy + j * 0.05
            if (x - cx) ** 2 + (y - cy) ** 2 <= REACH ** 2:
                cand.append((x + OX, y + OY))
    added = 0
    # nearest-die-first: lateral spreading in 35 um F.Cu is the expensive part
    # of the path, so a barrel 1.5 mm from the source bars is worth far more
    # than one at 5 mm. Pack inwards-out, not by max-min spacing.
    cand.sort(key=lambda q: (q[0] - cx - OX) ** 2 + (q[1] - cy - OY) ** 2)
    while True:
        best = None
        for ax, ay in cand:
            if not ok(ax, ay):
                continue
            best = (0.0, ax, ay)
            break
        if best is None:
            break
        _, ax, ay = best
        placed.append((ax, ay))
        ops.append({"op": "add_via", "at": [round(ax, 4), round(ay, 4)],
                    "size": VIA_D, "drill": VIA_DRILL, "net": "GND"})
        added += 1
    print(f'{ref}: +{added} new vias within {REACH} mm')

json.dump({"version": 1, "ops": ops}, open(OUT, 'w'), indent=1)
print(f'total +{len(ops)} -> {OUT}')
for ref, cx, cy in DIES:
    c = Point(cx + OX, cy + OY)
    old4 = sum(1 for v in existing if Point(v).distance(c) <= 4.0)
    new4 = sum(1 for v in existing + placed if Point(v).distance(c) <= 4.0)
    new227 = sum(1 for v in existing + placed if Point(v).distance(c) <= 2.27)
    near = min(Point(v).distance(c) for v in existing + placed)
    print(f'  {ref}: <=4.0 mm {old4} -> {new4} | <=2.27 mm (check window) {new227} | nearest {near:.3f} mm')
