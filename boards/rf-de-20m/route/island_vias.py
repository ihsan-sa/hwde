"""Give every orphaned F.Cu GND island a via down to the In1/In2/B.Cu planes.

stitch_vias' area grid works on a rectangular lattice, so the small lobes it
cannot land a lattice point in (the EPC2019 source fan-ins, thin slivers
between the HV pours) stay orphaned.  This walks the ACTUAL fill islands and
drops one via per island at the point furthest from any obstacle.
"""
import json
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import Point                                 # noqa: E402
from shapely.ops import unary_union                                # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_island.json'
VIA_D, VIA_DRILL, CLR, H2H = 0.6, 0.3, 0.1016, 0.5

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

# a via here must clear foreign pads/tracks/vias; foreign FILLS re-flow.
blk = [p.poly.buffer(max(CLR, 0.35 if p.net == '/SW' else CLR))
       for p in bg.pads_of() if p.net != 'GND']
blk += [t.shape.buffer(t.width / 2.0 + CLR)
        for t in bg.tracks_of() if t.net != 'GND']
blk += [Point(*v.at).buffer(v.drill / 2.0 + H2H) for v in bg.vias_of()]
blk += [p.drill_poly.buffer(H2H) for p in bg.pads_of() if p.drill is not None]
blocked = unary_union(blk)

cu = bg.net_copper('GND', 'F.Cu')
islands = list(cu.geoms) if cu.geom_type == 'MultiPolygon' else [cu]
have = [Point(*v.at) for v in bg.vias_of(net='GND')]

ops, done, skipped = [], 0, []
for g in sorted(islands, key=lambda g: -g.area):
    if g.area < 0.05:
        continue
    if any(g.contains(p) or g.distance(p) < 0.05 for p in have):
        continue
    # densest interior point: maximise distance to the island edge, then
    # require the via pad to sit inside the island and clear of obstacles
    best = None
    x0, y0, x1, y1 = g.bounds
    step = 0.05
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            pt = Point(x, y)
            if g.contains(pt):
                d = g.exterior.distance(pt)
                pad = pt.buffer(VIA_D / 2.0, quad_segs=12)
                if g.contains(pad) and not blocked.intersects(pad) \
                        and all(pt.distance(h) >= VIA_DRILL + H2H
                                for h in have):
                    if best is None or d > best[0]:
                        best = (d, x, y)
            x += step
        y += step
    if best is None:
        skipped.append((round(g.area, 3),
                        [round(v - o, 2) for v, o in
                         zip(g.bounds, (OX, OY, OX, OY))]))
        continue
    _, x, y = best
    have.append(Point(x, y))
    ops.append({"op": "add_via", "at": [round(x, 4), round(y, 4)],
                "size": VIA_D, "drill": VIA_DRILL, "net": "GND"})
    done += 1

json.dump({"version": 1, "ops": ops}, open(OPS, 'w'), indent=1)
print(f'{done} island vias -> {OPS}')
for a, b in skipped:
    print(f'  SKIPPED island area={a} mm2 bbox_local={b} (no room for a via)')
