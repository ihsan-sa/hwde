"""Cluster A item 5, attempt 2: A2 <-> LED_Y_A 0.2031 mm, corridor re-spacing.

Attempt 1 (solve_b5.py) reached +0.0243 mm worst margin but bought it by pulling
POE_TAP_A2 to 0.2259 mm from J1's netless board-lock pad, down from 0.7065 mm.
lock_probe.py shows every 57 V tap on this board holds >= 0.6608 mm from those
pads (A2 0.6608, B1 0.6614), i.e. the standoff is a deliberate shield-metal
clearance, so that was a 57 V clearance regression traded for a creepage number.
Rejected.

With the board locks pinned at 0.600 mm the corridor is 0.0078 mm SHORT if only
A2 and LED_Y_A move (perp distance lock-centre -> LED_Y_A line = 3.0922 mm vs
0.800 + 2.300 = 3.100 required), so LED_G_A - the other 10 mA magjack LED
cathode, which owns 0.5 mm of unused room toward the ETH_LED_LINK escape - is
re-spaced as well.  Order across the pinch:
    ETH_LED_LINK escape | LED_G_A | LED_Y_A | POE_TAP_A2 | J1 board lock
with 0.200 / 0.200 / 0.600 / 0.600 mm required between neighbours.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

A2N, LEDY, LEDG = '/poe/POE_TAP_A2', '/poe/LED_Y_A', '/poe/LED_G_A'
LOCK = 'J1-LOCK'
W = 0.200

A2_DEL = """d47e9eac da026f35 6ef53dbd d56c3578 3d8d74db f8c3bda3 d217df38
5c2d7cea 6c109b5f e35a3eca 96a96a7f c626ae1d a4b5b92c 500f3452 ededae9a
91c7baf5 59d678a0 a55a8cca 8e539d26 bc8f688e 9cc7f2b5""".split()
LEDY_DEL = """824ffcaf 54553a8d 75474148 b552c40e 3a4f33ef 20079056 406f647c
5b6faa1d c5362baf c2b8e47a 0e90eb3d 01505436 3a0044ae 59795f66 cd06eff3
b134bb9a""".split()
LEDG_DEL = ['30824bca']

src, items0, zones, edges = bm.load()
# rename the two netless J1 3.20 mm board-lock pads so required() can see them
items = []
for (L, net, cap, tag, uu) in items0:
    if not net and 'circle 3.20' in tag:
        net = LOCK
    items.append((L, net, cap, tag, uu))
_orig_required = bm.required


def required(a, b):
    if LOCK in (a, b):
        other = b if a == LOCK else a
        return 0.60 if other in bm.HV_ALL else 0.20
    return _orig_required(a, b)


bm.required = required

BY = {}
for (L, net, cap, tag, uu) in items:
    if uu:
        BY.setdefault(uu[:8], []).append((L, net, cap, tag, uu))
DEL = {}
for k in A2_DEL + LEDY_DEL + LEDG_DEL:
    assert k in BY, 'missing %s' % k
    DEL[k] = BY[k][0]
IGN = set(v[4] for v in DEL.values())

F_A0 = (50.250, 72.250)      # junction with 6d2b4ff1 (kept)
F_A5 = (43.760, 70.743)      # pad J1-12
F_Y0 = (58.100, 75.600)      # junction with 768b1b7e (kept)
F_Y4 = (44.450, 66.000)      # junction with bb9c3527 (kept)
F_G0 = (47.210, 64.123)      # pad J1-15 centre
F_G2 = (49.700, 66.600)      # junction with 20948199 (kept)


def build(p):
    a = [F_A0, (p[0], p[1]), (p[2], p[3]), (p[4], p[5]), (p[6], p[7]), F_A5]
    y = [F_Y0, (p[8], p[9]), (p[10], p[11]), (p[12], p[13]), F_Y4]
    g = [F_G0, (p[14], p[15]), F_G2]
    return a, y, g


def score(p, detail=False):
    paths = build(p)
    nets = (A2N, LEDY, LEDG)
    caps = [bm.path_caps(w, W) for w in paths]
    worst, who, rows = 9e9, None, []
    for (w, net, cp) in zip(paths, nets, caps):
        per, eg = bm.eval_path(items, zones, edges, w, W, net,
                               ignore=IGN, near=2.2)
        if eg < 0.55:
            return -9e9, ('edge', eg), []
        for k, (g, tag, req) in per.items():
            req = req if req > 0 else 0.20
            m = g - req
            rows.append((m, net.split('/')[-1], k, g, req, tag))
            if m < worst:
                worst, who = m, (net, k, g, req, tag)
    for (i, j) in ((0, 1), (0, 2), (1, 2)):
        req = required(nets[i], nets[j])
        gg = min(cap_dist(x, y) for x in caps[i] for y in caps[j])
        rows.append((gg - req, nets[i].split('/')[-1],
                     nets[j].split('/')[-1] + '(new)', gg, req, 'new-new'))
        if gg - req < worst:
            worst, who = gg - req, (nets[i], nets[j] + '(new)', gg, req, 'new')
    if detail:
        return worst, who, sorted(rows)
    return worst, who, []


CENTRE = [50.700, 70.100, 47.300, 66.500, 45.300, 66.700, 44.400, 67.900,
          52.000, 69.500, 47.400, 65.500, 45.200, 65.500, 48.400, 64.900]
SPREAD = [0.4, 1.0, 0.7, 0.5, 0.7, 0.6, 0.4, 0.8,
          1.5, 1.5, 0.7, 0.4, 0.7, 0.4, 0.6, 0.5]
N = len(CENTRE)


def climb(start, s0=0.30):
    cur, step = start[:], [s0] * N
    cw, cwho, _ = score(cur)
    for _ in range(80):
        improved = False
        for i in range(N):
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


random.seed(11)
best, bw, bwho = climb(CENTRE)
print('seed -> %.4f  %s' % (bw, bwho))
for t in range(30):
    st = [CENTRE[i] + random.uniform(-SPREAD[i], SPREAD[i]) for i in range(N)]
    c, w, who = climb(st)
    if w > bw:
        best, bw, bwho = c, w, who
        print('  trial %2d -> %.4f  %s' % (t, w, who))
best, bw, bwho = climb(best, 0.05)
print('final -> %.4f  %s' % (bw, bwho))

a, y, g = build(best)
w, who, rows = score(best, detail=True)
for (nm, poly) in (('POE_TAP_A2', a), ('LED_Y_A', y), ('LED_G_A', g)):
    print('\n%s:' % nm)
    for q in poly:
        print('   (%.3f, %.3f)' % q)
print('\nworst margin %.4f mm  binding %s' % (w, who))
print('\n%-10s %-24s %8s %6s %8s  %s'
      % ('net', 'against', 'gap', 'req', 'margin', 'item'))
for r in rows[:26]:
    print('%-10s %-24s %8.4f %6.3f %+8.4f  %s'
          % (r[1], r[2], r[3], r[4], r[0], r[5]))

json.dump({'a2': a, 'ledy': y, 'ledg': g, 'width': W, 'worst_margin': w,
           'del': {n: [DEL[k][4] for k in ks] for (n, ks) in
                   (('a2', A2_DEL), ('ledy', LEDY_DEL), ('ledg', LEDG_DEL))},
           'restore': {k: {'net': DEL[k][1], 'layer': DEL[k][0],
                           'start': list(DEL[k][2][0]),
                           'end': list(DEL[k][2][1]),
                           'width': round(DEL[k][2][2] * 2, 4),
                           'uuid': DEL[k][4]} for k in DEL}},
          open(os.path.join(HERE, 'solve_b5b.json'), 'w'), indent=1)
print('\nwrote solve_b5b.json')
