"""rf-de-20m P8-b - free-space search for heatsink clamping holes (E4).

Legality model, all measured on the actual board:
  * NPTH hole of diameter D: hole EDGE must clear every non-zone copper item
    (pads, tracks, vias) by that item's net clearance, and must clear every
    other drill by hole_to_hole 0.5 mm.  Zone FILL is not a blocker: KiCad
    voids a pour around an NPTH hole (the four existing corner holes sit
    inside the zone-A plane and raise no DRC).
  * board edge clearance 0.3 mm.
  * component courtyards (F.CrtYd/B.CrtYd) must not be touched by the SCREW
    HEAD envelope, not merely by the hole.
"""
import sys, os, json, math
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board
from shapely.geometry import Point, box
from shapely.ops import unary_union

PCB = os.environ.get('AIEE_PCB', r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
CLR = {'/SW': 0.8, '/tank/TANK_A': 0.8, '/tank/TANK_B': 0.4,
       '/tank/RFOUT': 0.8, '+40V': 0.5}
DEF = 0.25    # board-setup HOLE clearance, not the 0.1016 mm copper floor:
              # KiCad checks an NPTH pad against copper at 0.25 mm
H2H = 0.5
EDGE = 0.3

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

# --- non-zone copper (pads + tracks + vias), buffered by its own clearance
blk = []
for p in bg.pads_of():
    blk.append(p.poly.buffer(CLR.get(p.net, DEF)))
    if p.drill is not None:
        blk.append(p.drill_poly.buffer(H2H))
for t in bg.tracks_of():
    blk.append(t.shape.buffer(t.width / 2.0 + CLR.get(t.net, DEF)))
for v in bg.vias_of():
    blk.append(Point(*v.at).buffer(max(v.diameter, v.drill) / 2.0 + max(H2H, DEF)))
# HV zone FILL is a blocker too. A zone voids around an NPTH hole, so a hole in
# a pour is not a DRC error - but a grounded steel screw 0.8 mm from a 128 V pk
# RF pour is not something to introduce silently, and it erodes the pour. Only
# GND pour (and bare board) is an acceptable landing area.
for z in bg.zones_of():
    if z.net == 'GND':
        continue
    for lay in bg.copper_layers:
        f = z.fill_on(lay)
        if f is not None and not f.is_empty:
            blk.append(f.buffer(CLR.get(z.net, DEF)))
copper = unary_union(blk)

# --- courtyards (parsed straight from the file: geom has no courtyard API)
import sexpdata
raw = sexpdata.loads(open(PCB, encoding='utf-8').read())


def _sym(x):
    return x.value() if hasattr(x, 'value') else x


def walk(node, out, ctx=None):
    if not isinstance(node, list) or not node:
        return
    head = _sym(node[0])
    if head == 'footprint':
        at = [0, 0, 0]
        ref = '?'
        for c in node[1:]:
            if isinstance(c, list) and _sym(c[0]) == 'at':
                at = [float(v) for v in c[1:]]
            if isinstance(c, list) and _sym(c[0]) == 'property' and _sym(c[1]) == 'Reference':
                ref = _sym(c[2])
        ctx = (at, ref)
    if head in ('fp_line', 'fp_rect', 'fp_circle', 'fp_poly') and ctx:
        lay = None
        for c in node[1:]:
            if isinstance(c, list) and _sym(c[0]) == 'layer':
                lay = _sym(c[1])
        if lay in ('F.CrtYd', 'B.CrtYd'):
            pts = []
            for c in node[1:]:
                if isinstance(c, list) and _sym(c[0]) in ('start', 'end', 'center', 'mid'):
                    pts.append((float(c[1]), float(c[2])))
                if isinstance(c, list) and _sym(c[0]) == 'pts':
                    for q in c[1:]:
                        if isinstance(q, list) and _sym(q[0]) == 'xy':
                            pts.append((float(q[1]), float(q[2])))
            out.append((ctx, head, lay, pts))
    for c in node:
        walk(c, out, ctx)


items = []
walk(raw, items)

# Courtyard model. fp_circle courtyards (every MountingHole) are DISCS - the
# first cut took the convex hull of (centre, end), i.e. a line segment, and
# silently let a fiducial land 3.16 mm from H2's 3.45 mm courtyard.
import math as _m
from shapely.geometry import LineString, MultiPoint
_by = {}
for (at, ref), head, lay, pts in items:
    ax, ay = at[0], at[1]
    ang = _m.radians(-(at[2] if len(at) > 2 else 0.0))

    def T(p, ax=ax, ay=ay, ang=ang):
        x, y = p
        return (ax + x * _m.cos(ang) - y * _m.sin(ang),
                ay + x * _m.sin(ang) + y * _m.cos(ang))
    g = [T(p) for p in pts]
    if head == 'fp_circle' and len(g) >= 2:
        shp = Point(*g[0]).buffer(_m.dist(g[0], g[1]), quad_segs=64)
    elif head == 'fp_rect' and len(g) >= 2:
        shp = box(min(g[0][0], g[1][0]), min(g[0][1], g[1][1]),
                  max(g[0][0], g[1][0]), max(g[0][1], g[1][1]))
    elif head == 'fp_poly' and len(g) >= 3:
        shp = MultiPoint(g).convex_hull
    elif len(g) >= 2:
        shp = LineString(g).buffer(0.005)
    else:
        continue
    _by.setdefault(ref, []).append(shp)
byref = _by
# per footprint: the convex hull of its courtyard strokes (an open polyline
# courtyard has to be closed before it means anything)
courts = unary_union([unary_union(v).convex_hull for v in _by.values()])

outline = bg.outline

def legal(x, y, hole_d, head_d):
    p = Point(x, y)
    if not outline.buffer(-(EDGE + hole_d / 2.0)).contains(p):
        return False
    if copper.intersects(p.buffer(hole_d / 2.0)):
        return False
    if courts.intersects(p.buffer(head_d / 2.0)):
        return False
    return True


if __name__ == '__main__':
    HOLE = float(sys.argv[1]) if len(sys.argv) > 1 else 3.2
    HEAD = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    x0, y0, x1, y1 = 5.0, 8.0, 44.0, 46.0
    step = 0.25
    rows = []
    y = y0
    while y <= y1:
        row = ''
        x = x0
        while x <= x1:
            row += '.' if legal(x + OX, y + OY, HOLE, HEAD) else '#'
            x += step
        rows.append((y, row))
        y += step
    print(f'hole {HOLE} mm, head envelope {HEAD} mm; region local x {x0}..{x1} y {y0}..{y1}, {step} mm')
    print('      ' + ''.join(str(int((x0 + i * step) // 5 % 10)) if (x0 + i * step) % 5 < step else ' '
                             for i in range(len(rows[0][1]))))
    for y, row in rows:
        print(f'{y:5.1f} {row}')
