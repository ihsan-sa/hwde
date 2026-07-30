"""For a cluster-B item: everything that must move to reach the target width,
with full geometry, plus every track segment attached to each blocker via
(a via move drags its stubs with it)."""
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

TARGET = {'B3': ('V48_RAW', 0.500, (41.15, 89.15), (41.15, 93.10)),
          'B4': ('V48_RAW', 0.500, (27.40, 75.45), (27.40, 73.15)),
          'B5': ('+48V_SW', 0.500, (50.45, 97.55), (47.40, 100.60))}
which = sys.argv[1]
net, w, s, e = TARGET[which]
src, items, zones, edges = bm.load()

cap = None
for (L, n, c, tag, uu) in items:
    if L == 'F.Cu' and n == net and tag.startswith('segment'):
        if (math.dist(c[0], s) < 1e-3 and math.dist(c[1], e) < 1e-3) or \
           (math.dist(c[1], s) < 1e-3 and math.dist(c[0], e) < 1e-3):
            cap, myuu = c, uu
assert cap
test = (cap[0], cap[1], w / 2.0)
print('%s: %s %s w->%.3f  seg uuid %s' % (which, net, cap[:2], w, myuu[:8]))

must = []
for (L, onet, c, tag, uu) in items:
    if L != 'F.Cu' or onet == net or uu == myuu:
        continue
    g = cap_dist(test, c)
    req = bm.required(net, onet) or 0.20
    if g < req:
        must.append((g, req, onet, tag, uu, c))
for (L, pnet, pts, tag, _u) in bm.PADS_POLY:
    if L != 'F.Cu' or pnet == net:
        continue
    g = bm.poly_dist(test, pts)
    req = bm.required(net, pnet) or 0.20
    if g < req:
        must.append((g, req, pnet, tag, '', None))
must.sort()
print('\nITEMS BLOCKING w=%.3f (gap < required):' % w)
for (g, req, onet, tag, uu, c) in must:
    extra = '' if c is None else ' (%.3f,%.3f)-(%.3f,%.3f) r=%.3f' % (
        c[0][0], c[0][1], c[1][0], c[1][1], c[2])
    print('   gap %7.4f  req %.3f  deficit %6.4f  %-14s %-22s %-9s%s'
          % (g, req, req - g, onet, tag, uu[:8], extra))

# vias among them -> list every track segment landing on the via centre
raw = io.open(bm.PCB, encoding='utf-8').read()
print('\nVIA DETAIL + attached stubs:')
for (g, req, onet, tag, uu, c) in must:
    if not tag.startswith('via'):
        continue
    for (bs, be) in bm.blocks(raw, 'via'):
        b = raw[bs:be]
        if uu not in b:
            continue
        at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
        sz = re.search(r'\(size\s+([\d.]+)\)', b)
        dr = re.search(r'\(drill\s+([\d.]+)\)', b)
        ly = re.search(r'\(layers\s+"([^"]+)"\s+"([^"]+)"\)', b)
        vx, vy = float(at.group(1)), float(at.group(2))
        print('  via %s net=%s at (%.4f,%.4f) size %s drill %s layers %s-%s'
              % (uu[:8], onet, vx, vy, sz.group(1), dr.group(1),
                 ly.group(1), ly.group(2)))
        for (L2, n2, c2, t2, u2) in items:
            if not t2.startswith('segment') or n2 != onet:
                continue
            for end in (c2[0], c2[1]):
                if math.dist(end, (vx, vy)) < 1e-3:
                    print('      stub %-9s %-7s w=%.3f (%.3f,%.3f)-(%.3f,%.3f)'
                          % (u2[:8], L2, c2[2] * 2, c2[0][0], c2[0][1],
                             c2[1][0], c2[1][1]))
                    break

print('\nNEARBY (any net, within 1.6 mm of the widened track) for move room:')
rows = []
for (L, onet, c, tag, uu) in items:
    if onet == net or uu == myuu:
        continue
    g = cap_dist(test, c)
    if g < 1.6:
        rows.append((g, L, onet or '(no net)', tag, uu[:8],
                     '(%.3f,%.3f)-(%.3f,%.3f)' % (c[0][0], c[0][1],
                                                  c[1][0], c[1][1])))
for (L, pnet, pts, tag, _u) in bm.PADS_POLY:
    if pnet == net:
        continue
    g = bm.poly_dist(test, pts)
    if g < 1.6:
        rows.append((g, L, pnet or '(no net)', tag, '', ''))
rows.sort()
for r in rows[:40]:
    print('   %7.4f %-7s %-14s %-24s %-9s %s' % r)
