"""rf-de-20m P7 - solve the four spiral-terminal tracks.

All four spiral lands sit INSIDE their footprint's `copperpour not_allowed`
rule area, so no pour can reach them; only a track can.  For each land this
searches (start, end, width) for the widest DRU-legal track that touches both
the land and the net's pour, and reports the binding neighbour when the DRU
width floor cannot be met.
"""
import json
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import LineString, Point                     # noqa: E402
from shapely.ops import unary_union                                # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_lands.json'

# DRU clearance in force per net (rules_gen aiee_hv_* + the 0.1016 floor)
CLR = {'+40V': 0.5, '/SW': 0.8, '/tank/TANK_A': 0.8, '/tank/TANK_B': 0.8,
       '/tank/RFOUT': 0.8, '/tank/TANK_B_pair': 0.8}
FLOOR = {'/SW': 11.8942, '/tank/TANK_A': 8.4123, '/tank/TANK_B': 8.4123,
         '/tank/RFOUT': 8.4123}

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
EDGE = bg.outline.buffer(-0.3)


def clr_between(a, b):
    return max(CLR.get(a, 0.1016), CLR.get(b, 0.1016))


def stadium(p0, p1, w):
    return LineString([p0, p1]).buffer(w / 2.0, quad_segs=32)


def worst(net, geom, layers=('F.Cu',)):
    """(min slack, offender) against foreign PADS + the board edge.

    Zone fills are deliberately excluded: every pour on this board is
    regenerated after the tracks land (add tracks -> refill), so a pour is
    not an obstacle - it backs off the track by its own clearance."""
    slack, who = 1e9, None
    for lay in layers:
        for p in bg.pads_of(layer=lay):
            if p.net == net:
                continue
            need = clr_between(net, p.net)
            d = geom.distance(p.poly)
            if d - need < slack:
                slack, who = d - need, (f'{p.ref}.{p.number}[{p.net}] '
                                        f'd={d:.3f} need={need:.3f}')
    if not EDGE.contains(geom):
        slack, who = min(slack, -1.0), (who or '') + ' +EDGE'
    return slack, who


def wmax_for(net, p0, p1, cap):
    lo, hi, best = 0.3, cap, 0.0
    for _ in range(26):
        mid = (lo + hi) / 2.0
        if worst(net, stadium(p0, p1, mid))[0] >= 0.0:
            best, lo = mid, mid
        else:
            hi = mid
        if hi - lo < 0.002:
            break
    return best


def land_poly(ref, num):
    return unary_union([p.poly for p in bg.pads_of(ref=ref)
                        if p.number == num and 'F.Cu' in p.layers])


def solve(name, net, ref, num, xs, ys):
    """search (start, end, width) over a small grid; keep the widest legal
    track that still overlaps the terminal land."""
    floor = FLOOR[net]
    land = land_poly(ref, num)
    best = None
    for yc in ys:
        for x0, x1 in xs:
            p0 = (x0 + OX, yc + OY)
            p1 = (x1 + OX, yc + OY)
            w = wmax_for(net, p0, p1, floor + 0.05)
            if w < 0.3 or not stadium(p0, p1, w).intersects(land):
                continue
            if best is None or w > best[0]:
                best = (w, p0, p1)
            if w >= floor:
                break
        if best and best[0] >= floor:
            break
    w, p0, p1 = best
    w = floor if w >= floor else round(w - 0.002, 3)
    s, who = worst(net, stadium(p0, p1, w))
    tag = 'meets floor' if w + 1e-9 >= floor else 'UNDER FLOOR'
    print(f'{name:4s} {net:14s} w={w:8.4f} floor={floor:8.4f}  {tag}')
    print(f'      start=({p0[0]-OX:.3f},{p0[1]-OY:.3f}) '
          f'end=({p1[0]-OX:.3f},{p1[1]-OY:.3f})  binding: {who}')
    return w, p0, p1


LANDS = [
    # name, net, land ref/pad, candidate (x0,x1) spans, candidate y centres
    ('T1', '/SW', 'L301', '1',
     [(51.40, 52.60), (51.60, 52.40)], [17.60]),
    ('T2', '/tank/TANK_A', 'L301', '2',
     [(91.90, 92.60), (91.95, 92.40)], [17.60]),
    ('T3', '/tank/TANK_B', 'L302', '1',
     [(64.70, 65.90), (64.80, 65.70)], [62.60]),
    ('T4', '/tank/RFOUT', 'L302', '2',
     [(104.10, 104.50), (104.20, 104.40), (104.25, 104.35),
      (104.30, 104.32)], [62.50, 62.60, 62.40, 62.70]),
]

ops = []
for name, net, ref, num, xs, ys in LANDS:
    w, p0, p1 = solve(name, net, ref, num, xs, ys)
    ops.append({"op": "add_track", "start": [round(p0[0], 4), round(p0[1], 4)],
                "end": [round(p1[0], 4), round(p1[1], 4)],
                "width": round(w, 4), "layer": "F.Cu", "net": net})

# EPC2019 drain-bar escapes.  The bars are 0.25 mm wide and sit 0.35 mm from
# the source bars, so NO copper of any width can reach them without breaking
# the 0.8 mm aiee_hv_143v_SW rule - the same die geometry as the 12 approved
# pad-to-pad findings.  A zone cannot do it either (a .kicad_dru rule beats a
# zone's local clearance during fill, measured on this board), so the escape
# is two 0.25 mm tracks down the drain columns plus one 0.45 mm rung that
# ties them into the /SW pour.
for x in (30.90, 32.10):
    ops.append({"op": "add_track",
                "start": [round(x + OX, 4), round(22.90 + OY, 4)],
                "end":   [round(x + OX, 4), round(27.10 + OY, 4)],
                "width": 0.25, "layer": "F.Cu", "net": "/SW"})
ops.append({"op": "add_track",
            "start": [round(31.00 + OX, 4), round(25.00 + OY, 4)],
            "end":   [round(32.10 + OX, 4), round(25.00 + OY, 4)],
            "width": 0.45, "layer": "F.Cu", "net": "/SW"})

json.dump({"version": 1, "ops": ops}, open(OPS, 'w'), indent=1)
print(f'\nwrote {len(ops)} ops -> {OPS}')
