"""Pre-flight a route_edit ops file against the geometry model.

Builds the post-edit item set (removals applied, additions inserted) and reports
the worst clearance margin for every ADDED item against everything else, using
the same per-pair required table as the rest of this work order.  DRC is still
the oracle - this only avoids burning a route_edit + DRC cycle on an edit that
is already geometrically wrong.

Usage: verify_edit.py ops.json [near]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402  (kept for reference)

ops = json.load(open(sys.argv[1]))['ops']
NEAR = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
src, items0, zones, edges = bm.load()

# Name J1's two netless 3.20 mm board-lock pads so the required table can see
# them: they are the connector's shield-potential metal, and the pre-flight has
# to report the 57 V clearance to them rather than the bare 0.200 mm netclass
# number it would otherwise infer from "no net".
LOCK = 'J1-LOCK'
items = []
for (L, n, c, t, u) in items0:
    if not n and 'circle 3.20' in t:
        n = LOCK
    items.append((L, n, c, t, u))
_req = bm.required


def _required(a, b):
    if LOCK in (a, b):
        other = b if a == LOCK else a
        return 0.60 if other in bm.HV_ALL else 0.20
    return _req(a, b)


bm.required = _required

rm = {o['uuid'] for o in ops if o['op'] == 'remove'}
kept = [(L, n, c, t, u) for (L, n, c, t, u) in items if u not in rm]
kept_poly = [r for r in bm.PADS_POLY]

added = []
for o in ops:
    if o['op'] == 'add_track':
        cap = (tuple(o['start']), tuple(o['end']), o['width'] / 2.0)
        added.append(([o['layer']], o['net'], cap,
                      'NEW track w=%.3f' % o['width']))
    elif o['op'] == 'add_via':
        cap = (tuple(o['at']), tuple(o['at']), o['size'] / 2.0)
        added.append((list(bm.CU), o['net'], cap,
                      'NEW via d=%.3f' % o['size']))

print('ops: %d add, %d remove   (%d items kept)'
      % (len(added), len(rm), len(kept)))
overall = 9e9
for (layers, net, cap, tag) in added:
    worst = (9e9, None)
    for L in layers:
        for (L2, n2, c2, t2, u2) in kept:
            if L2 != L or n2 == net:
                continue
            g = bm.gap_of(cap, c2)
            req = bm.required(net, n2) or 0.20
            if g - req < worst[0]:
                worst = (g - req, (L, n2, t2, u2[:8], g, req))
        for (L2, n2, pts, t2, _u) in kept_poly:
            if L2 != L or n2 == net:
                continue
            g = bm.poly_dist(cap, pts)
            req = bm.required(net, n2) or 0.20
            if g - req < worst[0]:
                worst = (g - req, (L, n2, t2, '', g, req))
        for (L2, n2, pts) in zones:
            if L2 != L or n2 == net:
                continue
            g = bm.poly_dist(cap, pts)
            req = bm.required(net, n2) or 0.20
            if g - req < worst[0]:
                worst = (g - req, (L, 'ZONE ' + n2, 'fill', '', g, req))
    for (l3, n3, c3, t3) in added:
        if n3 == net or not set(l3) & set(layers):
            continue
        g = bm.gap_of(cap, c3)
        req = bm.required(net, n3) or 0.20
        if g - req < worst[0]:
            worst = (g - req, ('NEW', n3, t3, '', g, req))
    m, who = worst
    overall = min(overall, m)
    print('%-14s %-22s margin %+8.4f   vs %-7s %-14s %-24s %-9s gap %.4f req %.3f'
          % (net, tag, m, who[0], who[1], who[2], who[3], who[4], who[5]))
print('\nWORST MARGIN OVER ALL ADDED ITEMS: %+.4f mm  -> %s'
      % (overall, 'OK' if overall >= 0 else 'VIOLATION'))
sys.exit(0 if overall >= 0 else 1)
