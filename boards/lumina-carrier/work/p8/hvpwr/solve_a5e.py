"""Cluster A item 5, corrective pass after DRC caught 2 "Tracks crossing".

WHAT WENT WRONG.  capsule.seg_seg_dist is a minimum-over-endpoints formula.
It is exact for disjoint segments but returns a POSITIVE number for two
segments that properly cross, so neither the solver nor the pre-flight could
see a short.  The optimiser exploited that: it put LED_Y_A's first bend at
(52.089,67.067), i.e. s = 10.59 - BELOW LED_G_A - and the run back up crossed
both LED_G_A's new arm and its long y=66.600 horizontal.  board_model.gap_of()
now returns -1.0 on a crossing and every query goes through it.

WHAT THE CROSSING TEST REVEALS.  The three nets must stay ORDERED
LED_G_A | LED_Y_A | POE_TAP_A2 at every x, and LED_Y_A has to thread the fixed
corner at (49.700,66.600) where LED_G_A turns east onto the retained 20948199.
That corner sits 0.4243 mm from LED_Y_A's original centreline, so LED_Y_A can
only drop 0.0743 mm in s before touching it - and it only NEEDS to drop
0.0429 mm to reach 0.750 mm from A2 once it is necked to 0.100 mm.  The window
is delta in [0.0429, 0.0743].  It closes, and it closes with LED_G_A LEFT
ALONE: no reason to move it, so its original diagonal 30824bca is restored.

A2 keeps the geometry already applied (it was not party to either crossing).
Solve is therefore LED_Y_A alone: 4 free waypoints, everything else fixed.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402

LEDY, LEDG, A2N = '/poe/LED_Y_A', '/poe/LED_G_A', '/poe/POE_TAP_A2'
LOCK = 'J1-LOCK'
WY = 0.100

# the 2 new LED_G_A segments and the 5 new LED_Y_A segments now on the board
LEDG_NEW = [((47.210, 64.123), (48.225, 64.865)),
            ((48.225, 64.865), (49.700, 66.600))]
LEDY_NEW = [((58.100, 75.600), (52.0889, 67.0667)),
            ((52.0889, 67.0667), (47.420, 65.283)),
            ((47.420, 65.283), (45.877, 64.830)),
            ((45.877, 64.830), (44.564, 65.335)),
            ((44.564, 65.335), (36.490, 64.123))]
LEDG_ORIG = ((47.200, 64.100), (49.700, 66.600), 0.200)   # 30824bca, restored

src, items0, zones, edges = bm.load()
items = []
for (L, n, c, t, u) in items0:
    if not n and 'circle 3.20' in t:
        n = LOCK
    items.append((L, n, c, t, u))
_req = bm.required


def required(a, b):
    if LOCK in (a, b):
        other = b if a == LOCK else a
        return 0.60 if other in bm.HV_ALL else 0.20
    return _req(a, b)


bm.required = required


def matches(cap, pair):
    return ((math.dist(cap[0], pair[0]) < 2e-3 and
             math.dist(cap[1], pair[1]) < 2e-3) or
            (math.dist(cap[1], pair[0]) < 2e-3 and
             math.dist(cap[0], pair[1]) < 2e-3))


DROP, uuids = [], {}
for (L, n, c, t, u) in items:
    if L != 'F.Cu' or not t.startswith('segment'):
        continue
    for pair in LEDG_NEW + LEDY_NEW:
        if matches(c, pair):
            DROP.append(u)
            uuids[pair] = u
print('found %d of the 7 segments to retire' % len(DROP))
assert len(DROP) == 7, 'expected 7 (2 LED_G_A + 5 LED_Y_A) on the board'

CX, CY, RAD = 46.0, 67.0, 14.0
WIN = [(L, n, c, t, u) for (L, n, c, t, u) in items
       if u not in DROP and L == 'F.Cu'
       and min(abs(c[0][0] - CX), abs(c[1][0] - CX)) < RAD
       and min(abs(c[0][1] - CY), abs(c[1][1] - CY)) < RAD]
# LED_G_A's restored diagonal is not on the board yet - add it by hand
WIN.append(('F.Cu', LEDG, (LEDG_ORIG[0], LEDG_ORIG[1], LEDG_ORIG[2] / 2.0),
            'segment w=0.200 (restored 30824bca)', 'restored'))
WPOLY = [(L, n, pts, t, u) for (L, n, pts, t, u) in bm.PADS_POLY
         if L == 'F.Cu'
         and abs(sum(p[0] for p in pts) / len(pts) - CX) < RAD
         and abs(sum(p[1] for p in pts) / len(pts) - CY) < RAD]
print('window: %d F.Cu items (incl. restored LED_G_A), %d rect pads'
      % (len(WIN), len(WPOLY)))

Y_E = (58.100, 75.600)      # junction with 768b1b7e (kept)
Y_W = (36.490, 64.123)      # pad J1-17 centre


def build(p):
    return [Y_E, (p[0], p[1]), (p[2], p[3]), (p[4], p[5]), (p[6], p[7]), Y_W]


def score(p, detail=False):
    way = build(p)
    caps = bm.path_caps(way, WY)
    worst, who, rows = 9e9, None, []
    for (L2, n2, c2, t2, u2) in WIN:
        if n2 == LEDY:
            continue
        gg = min(bm.gap_of(c, c2) for c in caps)
        rq = required(LEDY, n2) or 0.20
        rows.append((gg - rq, n2, t2, u2[:8], gg, rq))
        if gg - rq < worst:
            worst, who = gg - rq, (n2, t2, u2[:8], gg, rq)
    for (L2, n2, pts, t2, u2) in WPOLY:
        if n2 == LEDY:
            continue
        gg = min(bm.poly_dist(c, pts) for c in caps)
        rq = required(LEDY, n2) or 0.20
        rows.append((gg - rq, n2, t2, '', gg, rq))
        if gg - rq < worst:
            worst, who = gg - rq, (n2, t2, '', gg, rq)
    if detail:
        return worst, who, sorted(rows)
    return worst, who, []


# seed: stay on the original diagonal dropped ~0.06 mm in s (y-x = 17.415),
# then into the corridor between pad J1-15 and the applied A2 run
SEED = [51.000, 68.415, 47.500, 65.300, 46.100, 64.870, 44.600, 65.330]
SPREAD = [1.0, 0.25, 0.6, 0.25, 0.6, 0.25, 0.5, 0.25]
N = 8


def climb(start, s0=0.08):
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


random.seed(23)
best, bw, bwho = climb(SEED)
print('analytic seed -> %+.4f  %s' % (bw, bwho))
for t in range(26):
    st = [SEED[i] + random.uniform(-SPREAD[i], SPREAD[i]) for i in range(N)]
    c, w, who = climb(st)
    if w > bw:
        best, bw, bwho = c, w, who
        print('  trial %2d -> %+.4f  %s' % (t, w, who))
best, bw, bwho = climb(best, 0.015)
w, who, rows = score(best, detail=True)
way = build(best)
print('\nLED_Y_A (w=%.3f): %s' % (WY, ['(%.3f,%.3f)' % q for q in way]))
print('\nworst margin %+.4f mm   binding %s' % (w, who))
seen = set()
print('\n%-22s %8s %6s %9s  %s' % ('against', 'gap', 'req', 'margin', 'item'))
for r in rows:
    if r[1] in seen:
        continue
    seen.add(r[1])
    print('%-22s %8.4f %6.3f %+9.4f  %s' % (r[1], r[4], r[5], r[0], r[2]))
    if len(seen) >= 12:
        break

# pass 1: retire the 7 segments.  pass 2: add the restored LED_G_A diagonal
# and the corrected LED_Y_A chain (separate calls so no add can collide with a
# not-yet-removed item's geometry).
json.dump({'version': 1, 'ops': [{'op': 'remove', 'uuid': u} for u in DROP]},
          open(os.path.join(HERE, 'ops_a5fix_pass1.json'), 'w'), indent=1)
adds = [dict(op='add_track', start=list(LEDG_ORIG[0]), end=list(LEDG_ORIG[1]),
             width=LEDG_ORIG[2], layer='F.Cu', net=LEDG)]
for i in range(len(way) - 1):
    adds.append(dict(op='add_track',
                     start=[round(way[i][0], 4), round(way[i][1], 4)],
                     end=[round(way[i + 1][0], 4), round(way[i + 1][1], 4)],
                     width=WY, layer='F.Cu', net=LEDY))
json.dump({'version': 1, 'ops': adds},
          open(os.path.join(HERE, 'ops_a5fix_pass2.json'), 'w'), indent=1)
print('\nwrote ops_a5fix_pass1.json (%d removes) / pass2.json (%d adds)'
      % (len(DROP), len(adds)))
