"""Cluster B ceilings: max width per item if the movable blockers (vias and
signal tracks of low-current nets) were moved out of the way entirely.

Answers the question the residual report never asked: 'cannot widen in place'
is not 'cannot fix' - so what IS the ceiling once the signal net is gone, and
what sets it then?  Anything set by a PAD is unfixable here (footprints frozen).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

ITEMS = [
    ('B1', '+12V', 1.1, (66.35, 112.05), (67.75, 113.45)),
    ('B2', '+12V', 1.1, (67.75, 113.45), (67.75, 114.20)),
    ('B3', 'V48_RAW', 0.5, (41.15, 89.15), (41.15, 93.10)),
    ('B4', 'V48_RAW', 0.5, (27.40, 75.45), (27.40, 73.15)),
    ('B5', '+48V_SW', 0.5, (50.45, 97.55), (47.40, 100.60)),
]
src, items, zones, edges = bm.load()


def blk(cap, net, layer, width, ignore=()):
    test = (cap[0], cap[1], width / 2.0)
    out = []
    for (L, onet, c, tag, uu) in items:
        if L != layer or onet == net or uu in ignore:
            continue
        g = cap_dist(test, c)
        req = bm.required(net, onet) or 0.20
        out.append((g - req, g, req, onet or '(no net)', tag, uu[:8]))
    for (L, znet, pts) in zones:
        if L != layer or znet == net:
            continue
        g = bm.poly_dist(test, pts)
        req = bm.required(net, znet) or 0.20
        out.append((g - req, g, req, 'ZONE ' + (znet or '?'), 'fill', ''))
    for (L, pnet, pts, tag, _u) in bm.PADS_POLY:
        if L != layer or pnet == net:
            continue
        g = bm.poly_dist(test, pts)
        req = bm.required(net, pnet) or 0.20
        out.append((g - req, g, req, pnet or '(no net)', tag, ''))
    out.sort()
    return out


def maxw(cap, net, layer, ignore=(), hi=2.5):
    lo = 0.10
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if blk(cap, net, layer, mid, ignore)[0][0] < 0:
            hi = mid
        else:
            lo = mid
    return lo


out = {}
for (name, net, need, s, e) in ITEMS:
    cap = None
    for (L, n2, c, tag, uu) in items:
        if L == 'F.Cu' and n2 == net and tag.startswith('segment'):
            if (math.dist(c[0], s) < 1e-3 and math.dist(c[1], e) < 1e-3) or \
               (math.dist(c[1], s) < 1e-3 and math.dist(c[0], e) < 1e-3):
                cap, myuu = c, uu
    assert cap, name
    print('=== %s %s  need %.3f mm  (now %.3f) ===' % (name, net, need,
                                                       cap[2] * 2))
    ign = {myuu}
    stages = []
    for step in range(8):
        w = maxw(cap, net, 'F.Cu', ign)
        b = blk(cap, net, 'F.Cu', min(w + 1e-6, need), ign)[0]
        movable = b[4].startswith('via') or (b[4].startswith('segment')
                                            and b[3] not in (net,))
        pad = b[4].startswith('pad') or b[4] == 'fill'
        stages.append((round(w, 4), b[3], b[4], b[5], pad))
        print('   ceiling %.4f mm  <- %-18s %-24s %-9s %s'
              % (w, b[3], b[4], b[5], 'PAD/POUR (immovable)' if pad
                 else 'movable'))
        if w >= need - 1e-4 or pad:
            break
        # remove every blocker of that same movable kind at this ceiling
        for r in blk(cap, net, 'F.Cu', need, ign):
            if r[0] < 0 and (r[4].startswith('via')
                             or r[4].startswith('segment')):
                for (L, onet, c, tag, uu) in items:
                    if uu[:8] == r[5]:
                        ign.add(uu)
        if len(ign) == 1:
            break
    out[name] = dict(net=net, need=need, now=round(cap[2] * 2, 4),
                     stages=stages, moved=len(ign) - 1)
    print('   -> would require moving %d foreign items\n' % (len(ign) - 1))
json.dump(out, open(os.path.join(HERE, 'ceilings.json'), 'w'), indent=1)
