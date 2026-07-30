"""Cluster A items 1-4: find a SHIELD pad19->pad20 polyline that holds 0.60 mm
to all four PoE tap pads, and MEASURE how much room actually exists.

Topology forced by geometry (all measured, see report at bottom):
  * pads 12/13 escape SOUTH on F.Cu (POE_TAP_A2 9cc7f2b5 x=43.750 y 67.35-70.75,
    POE_TAP_B1 b3506609 x=37.400 y 67.35-70.75) so SHIELD cannot pass south of
    pads 12/13 without crossing them on the same layer.
  * the +3V3 via at (45.800,73.450) d=0.600 blocks the corridor north of pad 11:
    pad11 centre -> via centre is 1.5215 mm and the two required half-gaps are
    1.300 + 0.600 = 1.900 mm; via -> pad2 centre is 1.3207 mm vs 0.600 + 0.900.
  * therefore SHIELD must enter through the pad11/pad12 gate and run west in the
    corridor between the tap row and the y=74.523 pad row.

Gate arithmetic (exact): |P11 P12| = 2.8398 mm.  SHIELD centreline needs
1.462 mm from P12 (0.600 + 0.762 + 0.100) and 1.300 mm from P11
(0.600 + 0.600 + 0.100) -> 2.762 mm of the 2.8398 mm axis. Slack 0.0778 mm.
"""
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402

NET = '/poe/SHIELD'
W = 0.200
# the 39 F.Cu SHIELD segments forming the pad19 -> pad20 leg
LEG = """0d643914 1164d69e 1396f6c7 162cf5f9 173fafc0 1d606e55 20e85cc9
23cee16d 24853671 2732ce88 2ae7a063 2bf7f39e 349247fd 352828e3 4504c244
4e080d7c 505c63bb 5160fe5a 54786110 6eb7ba2d 7353d027 7e34f331 82917658
851d264d 95ee0371 96c72c2d 9ceb1e9a a75f3dc8 b3b213e6 c757b00d c8914adc
cded7cc0 d75c652d e1ac4c22 e2ae1517 e3207b40 e6104f5f e8e6cd1c f1f15d1b""".split()

src, items, zones, edges = bm.load()
UUID = {}
for (L, net, cap, tag, uu) in items:
    if uu:
        UUID.setdefault(uu[:8], []).append((L, net, cap, tag, uu))
FULL = {}
for k in LEG:
    rows = UUID.get(k, [])
    assert rows, 'uuid prefix %s not found' % k
    FULL[k] = rows[0][4]

IGN = set(FULL.values())


def worst(way, width=W, near=2.5):
    per, eg = bm.eval_path(items, zones, edges, way, width, NET,
                           ignore=IGN, near=near)
    m = 9e9
    who = None
    for k, (g, tag, req) in per.items():
        if req <= 0:
            continue
        if g - req < m:
            m, who = g - req, (k, g, req, tag)
    return m, who, per, eg


def build(p):
    ylow, x2, x3, y3, x4, ycor, xw, xl, yl = p
    return [(48.450, 71.225), (47.900, ylow), (x2, ylow), (x3, y3),
            (x4, ycor), (xw, ycor), (xl, yl)]


base = [70.400, 45.700, 44.700, 72.219, 44.300, 73.350, 34.100, 33.300, 71.900]
step = [0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20]
best = base[:]
bm_, bwho, _, beg = worst(build(best))
print('start margin %.4f  binding %s  edge %.3f' % (bm_, bwho, beg))

for it in range(14):
    improved = False
    for i in range(len(best)):
        for d in (+1, -1):
            cand = best[:]
            cand[i] += d * step[i]
            m, who, _, eg = worst(build(cand))
            if eg < 0.55:
                continue
            if m > bm_ + 1e-6:
                best, bm_, bwho, beg = cand, m, who, eg
                improved = True
    if not improved:
        for i in range(len(step)):
            step[i] *= 0.5
        if max(step) < 0.004:
            break

way = build(best)
m, who, per, eg = worst(way, near=3.0)
print('\n=== optimised SHIELD pad19->pad20 polyline (w=%.3f) ===' % W)
for p in way:
    print('   (%.3f, %.3f)' % p)
print('worst margin %.4f mm   binding: %s' % (m, who))
print('board-edge clearance %.3f mm (min 0.5)' % eg)
print('\nper-net worst gap / required / margin:')
for k in sorted(per, key=lambda k: per[k][0] - per[k][2]):
    g, tag, req = per[k]
    print('  %-24s gap %7.4f  req %.3f  margin %+7.4f  %s'
          % (k, g, req, g - req, tag))

# --- how much room does each of the four tap pads actually have? ---
print('\n=== available-room measurement, per cluster-A item ===')
PADS = {'/poe/POE_TAP_A1': (46.300, 72.013, 0.600, 'J1-11'),
        '/poe/POE_TAP_A2': (43.760, 70.743, 0.762, 'J1-12'),
        '/poe/POE_TAP_B1': (37.410, 70.743, 0.762, 'J1-13'),
        '/poe/POE_TAP_B2': (34.870, 72.013, 0.600, 'J1-14')}
caps = bm.path_caps(way, W)
for net, (px, py, pr, ref) in PADS.items():
    pc = ((px, py), (px, py), pr)
    from capsule import cap_dist
    g = min(cap_dist(c, pc) for c in caps)
    print('  %-22s pad %-6s new gap %.4f mm (req 0.600)' % (net, ref, g))

out = {'polyline': way, 'width': W, 'worst_margin': m,
       'binding': who, 'edge_clearance': eg,
       'per_net': {k: {'gap': per[k][0], 'req': per[k][2], 'item': per[k][1]}
                   for k in per},
       'remove_uuids': [FULL[k] for k in LEG]}
json.dump(out, open(os.path.join(HERE, 'solve_a.json'), 'w'), indent=1)
print('\nwrote solve_a.json (%d uuids to remove)' % len(LEG))
