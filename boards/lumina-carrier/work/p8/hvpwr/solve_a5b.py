"""Cluster A item 5, scope-amended pass: /poe/LED_G_A added to scope.

WHAT CHANGED THE PROBLEM.  With LED_G_A movable, the 45 deg pinch budget opens
up, and - the important part - POE_TAP_A2 DOES NOT HAVE TO MOVE AT ALL.  In the
45 deg perpendicular coordinate s = (y-x)/sqrt2:

    ETH_LED_LINK escape (b78b3788)  s = 10.8188   <- hard floor below
    LED_G_A diagonal    (30824bca)  s = 11.9502
    LED_Y_A diagonal    (824ffcaf)  s = 12.3745
    POE_TAP_A2 diagonal (da026f35)  s = 13.0815
    J1 board-lock centre            s = 15.4667   <- hard ceiling above

Span floor->ceiling = 4.6479 mm.  Required chain, all tracks 0.200 mm:
    0.400 (LINK->G) + 0.400 (G->Y) + 0.800 (Y->A2) + 2.300 (A2->lock)  = 3.900
so the slack is 0.7479 mm, ~0.187 mm per gap.  A2 sits at 13.0815 and only needs
s_y <= 12.2815; dropping LED_Y_A to ~11.99 and LED_G_A to ~11.41 satisfies
everything with A2 untouched.  A2 therefore keeps its measured 0.6608 mm to the
board lock, and poe_tap_differential_pair / magjack_isolation_barrier are not
even in play.

SECOND FIX, the divergence pinch.  The old LED_Y_A took a V (out to
(41.500,68.950) then back to pad 17) which ran 0.2596 mm past A2's corner at
(43.750,67.350) - and that corner could not move, because moving it toward the
larger (x+y) needed to clear pad 16 walks it into the board lock (2.0805 mm from
the lock centre vs the 2.300 mm the 0.6608 mm floor demands).  Straightening
LED_Y_A from the corridor directly to pad 17 removes the pinch instead of
negotiating it: the straight run measures 1.2747 mm from that corner.

Polylines (A2 not listed - it is unchanged):
  LED_G_A : pad J1-15 centre -> free bow -> (49.700,66.600) junction
  LED_Y_A : (52.000,69.500) on the old diagonal -> 3 free -> pad J1-17 centre
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

LEDY, LEDG, A2N = '/poe/LED_Y_A', '/poe/LED_G_A', '/poe/POE_TAP_A2'
LOCK = 'J1-LOCK'
W = 0.200

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
        return 0.60 if other in bm.HV_ALL else 0.20
    return _req(a, b)


bm.required = required

BY = {}
for (L, net, cap, tag, uu) in items:
    if uu:
        BY.setdefault(uu[:8], []).append((L, net, cap, tag, uu))
DEL = {}
for k in LEDG_DEL + LEDY_DEL:
    assert k in BY, 'missing %s' % k
    DEL[k] = BY[k][0]
IGN = set(v[4] for v in DEL.values())

# window (centroid uses len(pts): a roundrect carries 20 points, not 4)
CX, CY, RAD = 45.0, 66.5, 13.0
WIN = [(L, n, c, t, u) for (L, n, c, t, u) in items
       if u not in IGN
       and min(abs(c[0][0] - CX), abs(c[1][0] - CX)) < RAD
       and min(abs(c[0][1] - CY), abs(c[1][1] - CY)) < RAD]
WPOLY = [(L, n, pts, t, u) for (L, n, pts, t, u) in bm.PADS_POLY
         if abs(sum(p[0] for p in pts) / len(pts) - CX) < RAD
         and abs(sum(p[1] for p in pts) / len(pts) - CY) < RAD]
print('window: %d items, %d rect pads' % (len(WIN), len(WPOLY)))

G0 = (47.210, 64.123)       # pad J1-15 centre
G2 = (49.700, 66.600)       # junction with 20948199 (kept)
Y0 = (52.000, 69.500)       # split point on the old 824ffcaf line (y-x=17.5)
Y4 = (36.490, 64.123)       # pad J1-17 centre
YEAST = (58.100, 75.600)    # junction with 768b1b7e (kept)


def build(p):
    g = [G0, (p[0], p[1]), G2]
    y = [Y0, (p[2], p[3]), (p[4], p[5]), (p[6], p[7]), Y4]
    return g, y


def score(p, detail=False):
    g, y = build(p)
    paths = [(LEDG, g), (LEDY, [YEAST, Y0] + y[1:])]
    caps = [bm.path_caps(w, W) for (_n, w) in paths]
    worst, who, rows = 9e9, None, []
    for ((net, w), cp) in zip(paths, caps):
        for (L2, n2, c2, t2, u2) in WIN:
            if n2 == net or L2 != 'F.Cu':
                continue
            gg = min(cap_dist(c, c2) for c in cp)
            rq = required(net, n2) or 0.20
            rows.append((gg - rq, net, n2, t2, u2[:8], gg, rq))
            if gg - rq < worst:
                worst, who = gg - rq, (net, n2, t2, u2[:8], gg, rq)
        for (L2, n2, pts, t2, u2) in WPOLY:
            if n2 == net or L2 != 'F.Cu':
                continue
            gg = min(bm.poly_dist(c, pts) for c in cp)
            rq = required(net, n2) or 0.20
            rows.append((gg - rq, net, n2, t2, '', gg, rq))
            if gg - rq < worst:
                worst, who = gg - rq, (net, n2, t2, '', gg, rq)
    gg = min(cap_dist(a, b) for a in caps[0] for b in caps[1])
    rq = required(LEDG, LEDY)
    rows.append((gg - rq, LEDG, LEDY + '(new)', 'new', '', gg, rq))
    if gg - rq < worst:
        worst, who = gg - rq, (LEDG, LEDY + '(new)', 'new', '', gg, rq)
    if detail:
        return worst, who, sorted(rows)
    return worst, who, []


SEED = [48.500, 64.630,          # LED_G_A bow
        48.600, 65.561,          # LED_Y_A region-D bow
        46.300, 64.950,
        44.900, 65.350]
SPREAD = [0.8, 0.35, 1.0, 0.4, 0.8, 0.35, 0.7, 0.35]
N = 8


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


random.seed(5)
best, bw, bwho = climb(SEED)
print('analytic seed -> %+.4f  %s' % (bw, bwho))
for t in range(30):
    st = [SEED[i] + random.uniform(-SPREAD[i], SPREAD[i]) for i in range(N)]
    c, w, who = climb(st)
    if w > bw:
        best, bw, bwho = c, w, who
        print('  trial %2d -> %+.4f  %s' % (t, w, who))
best, bw, bwho = climb(best, 0.02)
w, who, rows = score(best, detail=True)
g, y = build(best)
print('\nLED_G_A: %s' % ['(%.3f,%.3f)' % q for q in g])
print('LED_Y_A: %s' % ['(%.3f,%.3f)' % q for q in [YEAST, Y0] + y[1:]])
print('\nworst margin %+.4f mm   binding %s' % (w, who))
print('\n%-12s %-22s %8s %6s %9s  %s'
      % ('net', 'against', 'gap', 'req', 'margin', 'item'))
for r in rows[:16]:
    print('%-12s %-22s %8.4f %6.3f %+9.4f  %s'
          % (r[1].split('/')[-1], r[2], r[5], r[6], r[0], r[3]))

ops = []
for (net, poly) in ((LEDG, g), (LEDY, [YEAST, Y0] + y[1:])):
    for i in range(len(poly) - 1):
        ops.append(dict(op='add_track',
                        start=[round(poly[i][0], 4), round(poly[i][1], 4)],
                        end=[round(poly[i + 1][0], 4), round(poly[i + 1][1], 4)],
                        width=W, layer='F.Cu', net=net))
ops += [{'op': 'remove', 'uuid': DEL[k][4]} for k in LEDG_DEL + LEDY_DEL]
json.dump({'version': 1, 'ops': ops},
          open(os.path.join(HERE, 'ops_a5.json'), 'w'), indent=1)
json.dump({'worst_margin': w, 'ledg': g, 'ledy': [YEAST, Y0] + y[1:],
           'restore': {k: {'net': DEL[k][1], 'layer': DEL[k][0],
                           'start': list(DEL[k][2][0]),
                           'end': list(DEL[k][2][1]),
                           'width': round(DEL[k][2][2] * 2, 4)}
                       for k in DEL}},
          open(os.path.join(HERE, 'solve_a5b.json'), 'w'), indent=1)
print('\nwrote ops_a5.json (%d adds, %d removes)'
      % (len(ops) - len(DEL), len(DEL)))
