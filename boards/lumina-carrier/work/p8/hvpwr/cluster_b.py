"""Cluster B survey: for each of the 5 undersized power-trunk segments report
  1. whether a PARALLEL same-net path exists (bridge test on the net graph)
  2. the exact max width the segment can hold in place (bisection, per-pair
     required clearance from the .kicad_dru + IPC-2221B creepage)
  3. every blocker inside the required-clearance envelope of the target width,
     and how far each would have to move
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..'))
import board_model as bm    # noqa: E402
from capsule import cap_dist, seg_seg_dist    # noqa: E402

ITEMS = [
    dict(n='B1', net='+12V', I=2.0, req=1.1, start=(66.35, 112.05),
         end=(67.75, 113.45), layer='F.Cu'),
    dict(n='B2', net='+12V', I=2.0, req=1.1, start=(67.75, 113.45),
         end=(67.75, 114.20), layer='F.Cu'),
    dict(n='B3', net='V48_RAW', I=1.0, req=0.5, start=(41.15, 89.15),
         end=(41.15, 93.10), layer='F.Cu'),
    dict(n='B4', net='V48_RAW', I=1.0, req=0.5, start=(27.40, 75.45),
         end=(27.40, 73.15), layer='F.Cu'),
    dict(n='B5', net='+48V_SW', I=1.0, req=0.5, start=(50.45, 97.55),
         end=(47.40, 100.60), layer='F.Cu'),
]

src, items, zones, edges = bm.load()


def find(it):
    for (L, net, cap, tag, uu) in items:
        if L != it['layer'] or net != it['net'] or not tag.startswith('segment'):
            continue
        (a, b, r) = cap
        if ((abs(a[0] - it['start'][0]) < 1e-3 and abs(a[1] - it['start'][1]) < 1e-3
             and abs(b[0] - it['end'][0]) < 1e-3 and abs(b[1] - it['end'][1]) < 1e-3)
            or (abs(b[0] - it['start'][0]) < 1e-3 and abs(b[1] - it['start'][1]) < 1e-3
                and abs(a[0] - it['end'][0]) < 1e-3
                and abs(a[1] - it['end'][1]) < 1e-3)):
            return cap, uu
    return None, None


def blockers(cap, net, layer, width, near=3.0):
    """(gap, margin, othernet, tag, uuid) for items inside/near the envelope."""
    test = (cap[0], cap[1], width / 2.0)
    out = []
    for (L, onet, c, tag, uu) in items:
        if L != layer or onet == net or uu == cap_uuid:
            continue
        g = cap_dist(test, c)
        req = bm.required(net, onet) or 0.20
        if g - req < near:
            out.append((g, g - req, onet or '(no net)', tag, uu[:8], req))
    for (L, znet, pts) in zones:
        if L != layer or znet == net:
            continue
        g = bm.poly_dist(test, pts)
        req = bm.required(net, znet) or 0.20
        if g - req < near:
            out.append((g, g - req, 'ZONE ' + (znet or '?'), 'fill', '', req))
    out.sort(key=lambda r: r[1])
    return out


def maxwidth(cap, net, layer, lo=0.10, hi=2.0):
    for _ in range(40):
        mid = (lo + hi) / 2.0
        bad = any(m < 0 for (g, m, n, t, u, rq) in
                  blockers(cap, net, layer, mid, near=0.0))
        if bad:
            hi = mid
        else:
            lo = mid
    return lo


# ---------- parallel-path (bridge) test ----------
SCRIPTS = r'C:\dev\ai-ee3\.claude\skills\ai-ee\scripts'
sys.path.insert(0, os.path.join(SCRIPTS, 'lib'))
sys.path.insert(0, SCRIPTS)
import geom    # noqa: E402
from shapely.geometry import LineString, Point    # noqa: E402
from shapely.ops import unary_union    # noqa: E402

bg = geom.load_board(r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb',
                     refresh=True)


def parallel_path(net, cap, uuid):
    """Rebuild the net's connectivity WITHOUT the target segment; are the two
    endpoints still connected?  (uses per-layer noding + vias + pads)"""
    tracks = [t for t in bg.tracks_of(net)]
    keep = []
    for t in tracks:
        cs = list(t.shape.coords)
        s, e = cs[0], cs[-1]
        same = (math.dist(s, cap[0]) < 1e-3 and math.dist(e, cap[1]) < 1e-3) or \
               (math.dist(s, cap[1]) < 1e-3 and math.dist(e, cap[0]) < 1e-3)
        if same:
            continue
        keep.append(t)
    adj = {}

    def ed(a, b):
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    def k(layer, p):
        return (layer, round(p[0], 4), round(p[1], 4))
    for layer in sorted({t.layer for t in keep}):
        lines = [t.shape for t in keep if t.layer == layer]
        u = unary_union(lines)
        for g in getattr(u, 'geoms', [u]):
            cs = list(g.coords)
            for p, q in zip(cs, cs[1:]):
                ed(k(layer, p), k(layer, q))
    for v in bg.vias_of(net):
        sp = [l for l in bg.copper_layers if v.spans(l)]
        prev = None
        for l in sp:
            nd = ('V', round(v.at[0], 4), round(v.at[1], 4), l)
            r = v.diameter / 2.0 + 1e-3
            for cand in [n for n in list(adj) if n[0] == l]:
                if math.dist((cand[1], cand[2]), v.at) <= r:
                    ed(nd, cand)
            if prev:
                ed(prev, nd)
            prev = nd
    for p in bg.pads_of(net):
        prev = None
        for l in p.layers:
            if l not in bg.copper_layers:
                continue
            nd = ('P', p.ref, p.number, l)
            for cand in [n for n in list(adj) if n[0] == l]:
                if p.poly.buffer(1e-3).contains(Point(cand[1], cand[2])):
                    ed(nd, cand)
            if prev:
                ed(prev, nd)
            prev = nd
    # BFS from a node at one endpoint to a node at the other
    def near_nodes(pt, layer):
        return [n for n in adj if n[0] == layer
                and math.dist((n[1], n[2]), pt) < 1e-3]
    A = near_nodes(cap[0], LAY)
    B = near_nodes(cap[1], LAY)
    if not A or not B:
        return None, 'endpoint node vanished with the segment (dangling stub)'
    seen, stack = set(A), list(A)
    while stack:
        u = stack.pop()
        for v in adj.get(u, ()):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return (bool(set(B) & seen)), ''


report = []
for it in ITEMS:
    cap, uu = find(it)
    cap_uuid = uu
    LAY = it['layer']
    print('=== %s  %s  %.1f A  need %.3f mm ===' % (it['n'], it['net'],
                                                    it['I'], it['req']))
    if cap is None:
        print('  SEGMENT NOT FOUND'); continue
    w0 = cap[2] * 2
    print('  uuid %s  (%.3f,%.3f)-(%.3f,%.3f)  w=%.3f  len=%.3f mm'
          % (uu[:8], cap[0][0], cap[0][1], cap[1][0], cap[1][1], w0,
             math.dist(cap[0], cap[1])))
    par, note = parallel_path(it['net'], cap, uu)
    print('  parallel same-net path without this segment: %s %s'
          % ({True: 'YES', False: 'NO (bridge - carries all the current)',
              None: 'n/a'}[par], note))
    mw = maxwidth(cap, it['net'], LAY)
    print('  max width in place: %.4f mm  (report said %.3f)' % (mw, w0))
    print('  blockers within the %.3f mm envelope:' % it['req'])
    for (g, m, onet, tag, u8, rq) in blockers(cap, it['net'], LAY,
                                              it['req'], near=0.35)[:8]:
        print('     gap %7.4f  req %.3f  margin %+7.4f  %-18s %-22s %s'
              % (g, rq, m, onet, tag, u8))
    report.append(dict(item=it['n'], net=it['net'], uuid=uu, w=w0,
                       parallel=par, maxwidth=round(mw, 4),
                       required=it['req']))
    print()

json.dump(report, open(os.path.join(HERE, 'cluster_b.json'), 'w'), indent=1)
