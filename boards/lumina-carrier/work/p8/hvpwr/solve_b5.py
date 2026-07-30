"""Cluster A item 5: POE_TAP_A2 <-> LED_Y_A, 0.2031 mm (and 222 sibling pairs).

MEASURED extent (pair_extent.py): 17 of 36 LED_Y_A F.Cu segments and 21 of 27
POE_TAP_A2 F.Cu segments sit under 0.600 mm.  The two nets run PARALLEL for
~10 mm under J1: a 45 deg diagonal pair at 0.5071, a horizontal pair at 0.2500,
a staircase pair at 0.2031 and a final diagonal pair at 0.2596.

Why LED_Y_A alone cannot be moved (measured, in the 45 deg perpendicular
coordinate s = (y-x)/sqrt2):
    LED_G_A diagonal   s = 11.9502
    LED_Y_A diagonal   s = 12.3745   (0.4243 from LED_G_A; needs 0.400)
    POE_TAP_A2 diag    s = 13.0815   (0.7071 from LED_Y_A; needs 0.800)
    board-lock centre  s = 15.4667   (2.3852 from A2; needs 1.900)
LED_Y_A has only 0.0243 mm of room toward LED_G_A, while A2 has 0.4852 mm of
unused room toward the netless board-lock pad.  Span LED_G_A -> board lock is
3.5165 mm against 3.100 mm required, so the corridor DOES fit - the shift has
to come out of A2's side.  A2 is a tap route (not a switching loop), it keeps
its topology, length and layer, and it moves AWAY from every other net it is
gated against.

Both polylines are optimised jointly; the objective is the WORST margin
(gap - required) over every foreign item, so one gap is never robbed to pay
another.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

A2 = '/poe/POE_TAP_A2'
LED = '/poe/LED_Y_A'
W = 0.200

# A2 F.Cu segments replaced: the vertical, the diagonal, the 16-step staircase,
# the corner diagonal and the escape to pad 12.
A2_DEL = """d47e9eac da026f35 6ef53dbd d56c3578 3d8d74db f8c3bda3 d217df38
5c2d7cea 6c109b5f e35a3eca 96a96a7f c626ae1d a4b5b92c 500f3452 ededae9a
91c7baf5 59d678a0 a55a8cca 8e539d26 bc8f688e 9cc7f2b5""".split()
# LED_Y_A F.Cu segments replaced: horizontal + 14-step staircase
LED_DEL = """54553a8d 75474148 b552c40e 3a4f33ef 20079056 406f647c 5b6faa1d
c5362baf c2b8e47a 0e90eb3d 01505436 3a0044ae 59795f66 cd06eff3 b134bb9a""".split()

src, items, zones, edges = bm.load()
BY = {}
for (L, net, cap, tag, uu) in items:
    if uu:
        BY.setdefault(uu[:8], []).append((L, net, cap, tag, uu))
DEL = {}
for k in A2_DEL + LED_DEL:
    assert k in BY, 'missing %s' % k
    DEL[k] = BY[k][0]
IGN = set(v[4] for v in DEL.values())

FIX_A0 = (50.250, 72.250)       # junction with 6d2b4ff1 (kept)
FIX_A5 = (43.760, 70.743)       # pad J1-12
FIX_L0 = (47.850, 65.350)       # junction with 824ffcaf (kept)
FIX_L3 = (44.450, 66.000)       # junction with bb9c3527 (kept)


def build(p):
    a = [FIX_A0, (p[0], p[1]), (p[2], p[3]), (p[4], p[5]), (p[6], p[7]),
         FIX_A5]
    ledw = [FIX_L0, (p[8], p[9]), (p[10], p[11]), FIX_L3]
    return a, ledw


def score(p, detail=False):
    a, ledw = build(p)
    ca = bm.path_caps(a, W)
    cl = bm.path_caps(ledw, W)
    worst, who = 9e9, None
    rows = []
    for (name, caps, net) in (('A2', ca, A2), ('LED', cl, LED)):
        per, eg = bm.eval_path(items, zones, edges, [c[0] for c in caps]
                               + [caps[-1][1]], W, net, ignore=IGN, near=2.2)
        if eg < 0.55:
            return -9e9, ('edge', eg, 0, ''), []
        for k, (g, tag, req) in per.items():
            if req <= 0:
                req = 0.20           # netless / unclassified still owes DRC min
            m = g - req
            rows.append((m, name, k, g, req, tag))
            if m < worst:
                worst, who = m, (name, k, g, req, tag)
    # the two new paths against each other (57 V vs 10 mA -> 0.600)
    gab = min(cap_dist(x, y) for x in ca for y in cl)
    rows.append((gab - 0.60, 'A2', 'LED_Y_A(new)', gab, 0.60, 'new polyline'))
    if gab - 0.60 < worst:
        worst, who = gab - 0.60, ('A2', 'LED_Y_A(new)', gab, 0.60, 'new')
    if detail:
        return worst, who, sorted(rows)
    return worst, who, []


import random    # noqa: E402

CENTRE = [50.550, 70.000, 47.000, 66.200, 45.100, 66.600, 44.350, 67.800,
          46.500, 65.250, 45.150, 65.500]
SPREAD = [0.5, 1.2, 0.8, 0.4, 0.8, 0.6, 0.5, 0.8, 0.8, 0.3, 0.8, 0.4]


def climb(start, s0=0.30):
    cur = start[:]
    step = [s0] * 12
    cw, cwho, _ = score(cur)
    for _ in range(60):
        improved = False
        for i in range(12):
            for d in (+1, -1):
                c = cur[:]
                c[i] += d * step[i]
                w, who, _ = score(c)
                if w > cw + 1e-7:
                    cur, cw, cwho = c, w, who
                    improved = True
        if not improved:
            step = [s * 0.5 for s in step]
            if max(step) < 0.003:
                break
    return cur, cw, cwho


random.seed(7)
best, bw, bwho = climb(CENTRE)
print('seed climb -> %.4f  %s' % (bw, bwho))
for trial in range(24):
    st = [CENTRE[i] + random.uniform(-SPREAD[i], SPREAD[i]) for i in range(12)]
    c, w, who = climb(st)
    if w > bw:
        best, bw, bwho = c, w, who
        print('  trial %2d -> %.4f  %s' % (trial, w, who))
best, bw, bwho = climb(best, 0.06)
print('final -> %.4f  %s' % (bw, bwho))

a, ledw = build(best)
w, who, rows = score(best, detail=True)
print('\n=== optimised ===')
print('POE_TAP_A2 polyline:')
for q in a:
    print('   (%.3f, %.3f)' % q)
print('LED_Y_A polyline:')
for q in ledw:
    print('   (%.3f, %.3f)' % q)
print('\nworst margin %.4f mm  binding %s' % (w, who))
print('\n%-4s %-24s %8s %6s %8s  %s' % ('net', 'against', 'gap', 'req',
                                        'margin', 'item'))
for (m, name, k, g, req, tag) in rows[:22]:
    print('%-4s %-24s %8.4f %6.3f %+8.4f  %s' % (name, k, g, req, m, tag))

json.dump({'a2': a, 'led': ledw, 'width': W, 'worst_margin': w,
           'a2_del': [DEL[k][4] for k in A2_DEL],
           'led_del': [DEL[k][4] for k in LED_DEL],
           'restore': {k: {'net': DEL[k][1], 'layer': DEL[k][0],
                           'start': list(DEL[k][2][0]),
                           'end': list(DEL[k][2][1]),
                           'width': DEL[k][2][2] * 2, 'uuid': DEL[k][4]}
                       for k in DEL}},
          open(os.path.join(HERE, 'solve_b5.json'), 'w'), indent=1)
print('\nwrote solve_b5.json')
