"""Cluster A item 5, scope-amended pass (LED_G_A in scope).  FINAL attempt.

WHY THE FIRST TRY WITH LED_G_A STILL FAILED.  Adding LED_G_A opens the 45 deg
diagonal budget but NOT the corridor west of it, because the floor there is
pad J1-15 itself (LED_G_A's own land, 1.60 mm circle, immovable) - not
LED_G_A's trace.  At x = 47.21 (pad 15's x):
    LED_Y_A floor  = 64.123 + 1.100 = 65.223   (0.200 + 0.800 pad + 0.100 half)
    A2 ceiling     = 68.173 - 2.300 = 65.873   (0.600 + 1.600 lock + 0.100 half,
                                                the 0.6608 mm board-lock floor)
    A2 must clear LED_Y_A by 0.800  ->  A2 >= 66.023  >  65.873.  Short 0.150 mm.

WHAT MAKES IT FIT.  LED_Y_A is a magjack LED cathode fed from +3V3 through a
resistor: ~10 mA.  Necking it to 0.100 mm - the board minimum, already used on
this board (the old SHIELD escape d75c652d and ILIM's 81073fca are both
0.100 mm) - buys 0.050 mm on each of its two flanks:
    LED_Y_A floor  = 64.123 + 1.050 = 65.173
    A2 >= 65.173 + 0.750 = 65.923,  ceiling 66.061 at x = 47.21  ->  fits, 0.138.
It also all but closes the diagonal: A2<->LED_Y_A needs 0.750 instead of 0.800
against a present 0.7071, so LED_Y_A drops ~0.05-0.22 mm in s and LED_G_A takes
a small bow to keep its own 0.200 mm.

A2 moves ONLY its corner and corridor run, and it moves AWAY from the board
lock: the new corner (47.700,66.150) sits 2.4159 mm from the lock centre vs
2.3608 mm today, i.e. the 57 V lock clearance IMPROVES 0.6608 -> ~0.7159 mm.
Nothing touches the A1<->A2 pair or the MDI barrier.

LED_Y_A's divergence V (out to (41.500,68.950) and back) is replaced by a
straight run to pad J1-17, which also retires the 0.2596 mm pinch against A2's
corner without that corner having to move into the lock.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

A2N, LEDY, LEDG = '/poe/POE_TAP_A2', '/poe/LED_Y_A', '/poe/LED_G_A'
LOCK = 'J1-LOCK'
WA, WY, WG = 0.200, 0.100, 0.200

A2_DEL = """da026f35 6ef53dbd d56c3578 3d8d74db f8c3bda3 d217df38 5c2d7cea
6c109b5f e35a3eca 96a96a7f c626ae1d a4b5b92c 500f3452 ededae9a 91c7baf5
59d678a0 a55a8cca 8e539d26 bc8f688e 9cc7f2b5""".split()
LEDG_DEL = ['30824bca']
LEDY_DEL = """824ffcaf 54553a8d 75474148 b552c40e 3a4f33ef 20079056 406f647c
5b6faa1d c5362baf c2b8e47a 0e90eb3d 01505436 3a0044ae 59795f66 cd06eff3
b134bb9a bb9c3527 da72c997 84c3970e""".split()

src, items0, zones, edges = bm.load()
items = []
for (L, net, cap, tag, uu) in items0:
    if not net and 'circle 3.20' in tag:
        net = LOCK
    items.append((L, net, cap, tag, uu))
_req = bm.required


def required(a, b):
    if LOCK in (a, b):
        other = b if a == LOCK else a
        return 0.6608 if other in bm.HV_ALL else 0.20   # measured as-built floor
    return _req(a, b)


bm.required = required
BY = {}
for (L, net, cap, tag, uu) in items:
    if uu:
        BY.setdefault(uu[:8], []).append((L, net, cap, tag, uu))
DEL = {}
for k in A2_DEL + LEDG_DEL + LEDY_DEL:
    assert k in BY, 'missing %s' % k
    DEL[k] = BY[k][0]
IGN = set(v[4] for v in DEL.values())

CX, CY, RAD = 46.0, 67.0, 14.0
WIN = [(L, n, c, t, u) for (L, n, c, t, u) in items
       if u not in IGN and L == 'F.Cu'
       and min(abs(c[0][0] - CX), abs(c[1][0] - CX)) < RAD
       and min(abs(c[0][1] - CY), abs(c[1][1] - CY)) < RAD]
WPOLY = [(L, n, pts, t, u) for (L, n, pts, t, u) in bm.PADS_POLY
         if L == 'F.Cu'
         and abs(sum(p[0] for p in pts) / len(pts) - CX) < RAD
         and abs(sum(p[1] for p in pts) / len(pts) - CY) < RAD]
print('window: %d F.Cu items, %d rect pads' % (len(WIN), len(WPOLY)))

A_E = (50.250, 68.750)      # junction with d47e9eac (kept)
A_W = (43.760, 70.743)      # pad J1-12
G_0 = (47.210, 64.123)      # pad J1-15 centre
G_2 = (49.700, 66.600)      # junction with 20948199 (kept)
Y_E = (58.100, 75.600)      # junction with 768b1b7e (kept)
Y_W = (36.490, 64.123)      # pad J1-17 centre


def build(p):
    a = [A_E, (p[0], p[1]), (p[2], p[3]), (p[4], p[5]), (p[6], p[7]), A_W]
    g = [G_0, (p[8], p[9]), G_2]
    y = [Y_E, (p[10], p[11]), (p[12], p[13]), (p[14], p[15]),
         (p[16], p[17]), Y_W]
    return a, g, y


def score(p, detail=False):
    a, g, y = build(p)
    paths = [(A2N, a, WA), (LEDG, g, WG), (LEDY, y, WY)]
    caps = [bm.path_caps(w, wid) for (_n, w, wid) in paths]
    worst, who, rows = 9e9, None, []
    for ((net, _w, _wid), cp) in zip(paths, caps):
        for (L2, n2, c2, t2, u2) in WIN:
            if n2 == net:
                continue
            gg = min(cap_dist(c, c2) for c in cp)
            rq = required(net, n2) or 0.20
            rows.append((gg - rq, net, n2, t2, u2[:8], gg, rq))
            if gg - rq < worst:
                worst, who = gg - rq, (net, n2, t2, u2[:8], gg, rq)
        for (L2, n2, pts, t2, u2) in WPOLY:
            if n2 == net:
                continue
            gg = min(bm.poly_dist(c, pts) for c in cp)
            rq = required(net, n2) or 0.20
            rows.append((gg - rq, net, n2, t2, '', gg, rq))
            if gg - rq < worst:
                worst, who = gg - rq, (net, n2, t2, '', gg, rq)
    for (i, j) in ((0, 1), (0, 2), (1, 2)):
        rq = required(paths[i][0], paths[j][0])
        gg = min(cap_dist(x, z) for x in caps[i] for z in caps[j])
        rows.append((gg - rq, paths[i][0], paths[j][0] + '(new)', 'new', '',
                     gg, rq))
        if gg - rq < worst:
            worst, who = gg - rq, (paths[i][0], paths[j][0] + '(new)', 'new',
                                   '', gg, rq)
    if detail:
        return worst, who, sorted(rows)
    return worst, who, []


SEED = [47.700, 66.150, 46.300, 65.800, 44.900, 66.300, 44.100, 67.300,
        48.400, 64.700,
        50.500, 67.680, 47.200, 65.200, 46.300, 64.900, 44.750, 65.220]
SPREAD = [0.4, 0.30, 0.5, 0.20, 0.5, 0.25, 0.4, 0.35,
          0.7, 0.30,
          1.2, 0.60, 0.4, 0.20, 0.5, 0.25, 0.4, 0.20]
N = len(SEED)


def climb(start, s0=0.10):
    cur, step = start[:], [s0] * N
    cw, cwho, _ = score(cur)
    for _ in range(90):
        imp = False
        for i in range(N):
            for d in (+1, -1):
                c = cur[:]
                c[i] += d * step[i]
                w, who, _ = score(c)
                if w > cw + 1e-7:
                    cur, cw, cwho = c, w, who
                    imp = True
        if not imp:
            step = [s * 0.5 for s in step]
            if max(step) < 0.002:
                break
    return cur, cw, cwho


random.seed(17)
best, bw, bwho = climb(SEED)
print('analytic seed -> %+.4f  %s' % (bw, bwho))
for t in range(22):
    st = [SEED[i] + random.uniform(-SPREAD[i], SPREAD[i]) for i in range(N)]
    c, w, who = climb(st)
    if w > bw:
        best, bw, bwho = c, w, who
        print('  trial %2d -> %+.4f  %s' % (t, w, who))
best, bw, bwho = climb(best, 0.02)
w, who, rows = score(best, detail=True)
a, g, y = build(best)
for (nm, poly, wid) in (('POE_TAP_A2', a, WA), ('LED_G_A', g, WG),
                        ('LED_Y_A', y, WY)):
    print('\n%s (w=%.3f): %s' % (nm, wid, ['(%.3f,%.3f)' % q for q in poly]))
print('\nworst margin %+.4f mm   binding %s' % (w, who))
print('\n%-12s %-24s %8s %6s %9s  %s'
      % ('net', 'against', 'gap', 'req', 'margin', 'item'))
seen = set()
for r in rows:
    k = (r[1], r[2])
    if k in seen:
        continue
    seen.add(k)
    print('%-12s %-24s %8.4f %6.3f %+9.4f  %s'
          % (r[1].split('/')[-1], r[2], r[5], r[6], r[0], r[3]))
    if len(seen) >= 18:
        break

ops = []
for (net, poly, wid) in ((A2N, a, WA), (LEDG, g, WG), (LEDY, y, WY)):
    for i in range(len(poly) - 1):
        ops.append(dict(op='add_track',
                        start=[round(poly[i][0], 4), round(poly[i][1], 4)],
                        end=[round(poly[i + 1][0], 4), round(poly[i + 1][1], 4)],
                        width=wid, layer='F.Cu', net=net))
ops += [{'op': 'remove', 'uuid': DEL[k][4]}
        for k in A2_DEL + LEDG_DEL + LEDY_DEL]
json.dump({'version': 1, 'ops': ops},
          open(os.path.join(HERE, 'ops_a5_floor.json'), 'w'), indent=1)
inv = [dict(op='add_track', start=list(DEL[k][2][0]), end=list(DEL[k][2][1]),
            width=round(DEL[k][2][2] * 2, 4), layer=DEL[k][0], net=DEL[k][1])
       for k in DEL]
json.dump({'version': 1, 'ops': inv, '_note': 'restore-half; removes of the '
           'new tracks must be added by uuid after reading the board'},
          open(os.path.join(HERE, 'ops_a5_restore.json'), 'w'), indent=1)
print('\nwrote ops_a5.json (%d adds, %d removes) + ops_a5_restore.json'
      % (len(ops) - len(DEL), len(DEL)))
