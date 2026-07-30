"""Cluster B item B5: +48V_SW 0.200 -> 0.500 mm on (50.45,97.55)-(47.40,100.60).

This is the ONLY neck in an otherwise all-0.500 mm +48V_SW trunk (every other
segment of the net is already 0.500, see the net inventory), so fixing it
completes the rail.

The diagonal threads the U22 eFuse pin-escape field: FOUR transition vias sit
inside its 0.635 mm envelope, two on each side (ILIM e5d95c55 + ENABLE 666c0251
on one side, ILIM 47f3476f + PGOOD 3cabe9ef on the other), so no shift alone can
open it - all four have to move outward.  Once they are gone the binding item is
pad U22-11 (ILIM, roundrect) at 0.6162 mm, 0.0188 mm short, and pad C59-1
(DVDT) on the far side has +0.065 mm spare - so the run also takes a small
perpendicular shift, absorbed by the two abutting 0.500 mm segments (47c5e92f,
6f468527) rather than by adding jogs.

Free parameters: the perpendicular shift of the run, and one outward offset per
via.  Objective: maximise the WORST margin so no gap is robbed to pay another.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

NET = '+48V_SW'
W = 0.500
S, E = (50.450, 97.550), (47.400, 100.600)
A_FIX = (50.450, 97.450)        # far end of 47c5e92f
B_FIX = (46.800, 100.600)       # far end of 6f468527
RM_SEG = ['34fafcf0', '47c5e92f', '6f468527']

# via, net, its two stubs (uuid, layer, other endpoint), outward sign
VIAS = [
    ('e5d95c55', '/pwr/ILIM', (47.525, 99.000)),
    ('666c0251', '/ENABLE', (48.150, 98.350)),
    ('47f3476f', '/pwr/ILIM', (49.000, 100.475)),
    ('3cabe9ef', '/pwr/PGOOD', (50.750, 98.800)),
]
# stubs that must follow a via: (stub uuid, layer, width, fixed end, via key)
STUBS = [
    ('d19ef28c', 'B.Cu', 0.2, None, ('e5d95c55', '47f3476f')),   # via-to-via
    ('378144b9', 'F.Cu', 0.2, (48.000, 98.200), ('666c0251',)),
    ('a36e89f1', 'B.Cu', 0.2, (49.700, 99.900), ('666c0251',)),
    ('0be1333e', 'F.Cu', 0.2, (51.100, 99.150), ('3cabe9ef',)),
    ('2df3fb35', 'B.Cu', 0.2, (48.450, 96.500), ('3cabe9ef',)),
    # these two connected to their via only by pad OVERLAP; re-anchor them
    # explicitly so a via move cannot silently open the net
    ('81073fca', 'F.Cu', 0.1, (46.850, 98.925), ('e5d95c55',)),
    ('5307e461', 'F.Cu', 0.2, (49.150, 100.350), ('47f3476f',)),
]
MAXMOVE = 0.40          # keep a via move to something a human would accept
BEND = {'d19ef28c': 9, '2df3fb35': 11}   # param index of that stub's bend dx,dy
PAD_KEEPOUT = 0.35      # no via-in-pad, even on its own net

src, items, zones, edges = bm.load()
FULL = {}
for (L, n, c, t, u) in items:
    if u:
        FULL[u[:8]] = u
RM = set(FULL[k] for k in RM_SEG + [v[0] for v in VIAS]
         + [s[0] for s in STUBS])

dx, dy = E[0] - S[0], E[1] - S[1]
LEN = math.hypot(dx, dy)
ux, uy = dx / LEN, dy / LEN
nx, ny = -uy, ux


def side_of(pt):
    return 1.0 if (pt[0] - S[0]) * nx + (pt[1] - S[1]) * ny > 0 else -1.0


SIGN = {k: side_of(p) for (k, _n, p) in VIAS}

# local window of everything that could matter
WIN = [(L, n, c, t, u) for (L, n, c, t, u) in items
       if u not in RM and min(abs(c[0][0] - 49), abs(c[1][0] - 49)) < 8
       and min(abs(c[0][1] - 99), abs(c[1][1] - 99)) < 8]
WPOLY = [(L, n, pts, t, u) for (L, n, pts, t, u) in bm.PADS_POLY
         if abs(sum(p[0] for p in pts) / len(pts) - 49) < 8
         and abs(sum(p[1] for p in pts) / len(pts) - 99) < 8]
print('window: %d items, %d rect pads' % (len(WIN), len(WPOLY)))


def build(p):
    s = p[0]
    S2 = (S[0] + nx * s, S[1] + ny * s)
    E2 = (E[0] + nx * s, E[1] + ny * s)
    new = [('t', 'F.Cu', NET, (A_FIX, S2, W / 2.0)),
           ('t', 'F.Cu', NET, (S2, E2, W / 2.0)),
           ('t', 'F.Cu', NET, (E2, B_FIX, W / 2.0))]
    vpos = {}
    for i, (k, vn, pos) in enumerate(VIAS):
        q = (pos[0] + p[1 + 2 * i], pos[1] + p[2 + 2 * i])
        vpos[k] = q
        new.append(('v', None, vn, (q, q, 0.300)))
    for (su, lay, w, fixed, keys) in STUBS:
        if len(keys) == 2:
            a, b = vpos[keys[0]], vpos[keys[1]]
        else:
            a, b = vpos[keys[0]], fixed
        vn = [n for (L, n, c, t, u) in items if u == FULL[su]][0]
        if su in BEND:                     # one free bend on the long B.Cu runs
            i = BEND[su]
            mid = ((a[0] + b[0]) / 2 + p[i], (a[1] + b[1]) / 2 + p[i + 1])
            new.append(('t', lay, vn, (a, mid, w / 2.0)))
            new.append(('t', lay, vn, (mid, b, w / 2.0)))
        else:
            new.append(('t', lay, vn, (a, b, w / 2.0)))
    return new


def score(p, detail=False):
    for i in range(4):
        if math.hypot(p[1 + 2 * i], p[2 + 2 * i]) > MAXMOVE:
            return -9e9, ('via move > %.2f mm' % MAXMOVE,), []
    new = build(p)
    # No via-in-pad on a FOREIGN pad.  Same-net pads are exempt: the board
    # already lands ILIM via e5d95c55 inside U22-11's own pad, and that is the
    # existing design intent, not something this order gets to re-litigate.
    for (kind, lay, net, cap) in new:
        if kind != 'v':
            continue
        for (L2, n2, pts, t2, u2) in WPOLY:
            if L2 != 'F.Cu' or n2 == net:
                continue
            if bm.poly_dist(cap, pts) < PAD_KEEPOUT - 0.30:
                return -9e9, ('via inside/near foreign pad %s' % t2,), []
    worst, who, rows = 9e9, None, []
    for (kind, lay, net, cap) in new:
        layers = bm.CU if kind == 'v' else [lay]
        for L in layers:
            for (L2, n2, c2, t2, u2) in WIN:
                if n2 == net:
                    continue
                if kind == 't' and L2 != L:
                    continue
                if kind == 'v' and L2 != L:
                    continue
                g = cap_dist(cap, c2)
                req = bm.required(net, n2) or 0.20
                if g - req < worst:
                    worst, who = g - req, (net, n2, t2, u2[:8], g, req)
                rows.append((g - req, net, n2, t2, u2[:8], g, req))
            for (L2, n2, pts, t2, u2) in WPOLY:
                if n2 == net or L2 != L:
                    continue
                g = bm.poly_dist(cap, pts)
                req = bm.required(net, n2) or 0.20
                if g - req < worst:
                    worst, who = g - req, (net, n2, t2, '', g, req)
                rows.append((g - req, net, n2, t2, '', g, req))
        for (k2, l2, n2, c2) in new:
            if n2 == net or (kind == 't' and k2 == 't' and l2 != lay):
                continue
            g = cap_dist(cap, c2)
            req = bm.required(net, n2) or 0.20
            if g - req < worst:
                worst, who = g - req, (net, n2 + '(new)', 'new', '', g, req)
            rows.append((g - req, net, n2 + '(new)', 'new', '', g, req))
    if detail:
        return worst, who, sorted(rows)
    return worst, who, []


import random    # noqa: E402
N = 13


def climb(start, s0=0.06):
    cur, step = start[:], [s0] * N
    cw, cwho, _ = score(cur)
    for _ in range(80):
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


seed0 = [0.0]
for (k, _n, pos) in VIAS:
    seed0 += [nx * 0.15 * SIGN[k], ny * 0.15 * SIGN[k]]
seed0 += [0.0, 0.0, 0.0, 0.0]
random.seed(3)
best, bw, bwho = climb(seed0)
print('seed -> %.4f %s' % (bw, bwho))
for t in range(45):
    st = [random.uniform(-0.10, 0.10)]
    for _ in range(4):
        st += [random.uniform(-0.34, 0.34), random.uniform(-0.34, 0.34)]
    st += [random.uniform(-0.6, 0.6) for _ in range(4)]
    c, w, who = climb(st)
    if w > bw:
        best, bw, bwho = c, w, who
        print('  trial %2d -> %.4f %s' % (t, w, who))
best, bw, bwho = climb(best, 0.015)
w, who, rows = score(best, detail=True)
print('\nshift %+.4f   via deltas %s' % (best[0],
                                         ['%+.3f' % v for v in best[1:]]))
print('worst margin %+.4f  binding %s' % (w, who))
print('\ntightest 12:')
for r in rows[:12]:
    print('  %+8.4f  %-12s vs %-14s %-24s %-9s gap %.4f req %.3f'
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
new = build(best)
out = {'params': best, 'worst_margin': w, 'removes': sorted(RM), 'adds': []}
for (kind, lay, net, cap) in new:
    if kind == 't':
        out['adds'].append(dict(op='add_track',
                                start=[round(cap[0][0], 4), round(cap[0][1], 4)],
                                end=[round(cap[1][0], 4), round(cap[1][1], 4)],
                                width=round(cap[2] * 2, 4), layer=lay, net=net))
    else:
        out['adds'].append(dict(op='add_via',
                                at=[round(cap[0][0], 4), round(cap[0][1], 4)],
                                size=0.6, drill=0.3, net=net))
json.dump(out, open(os.path.join(HERE, 'solve_b5cur.json'), 'w'), indent=1)
json.dump({'version': 1, 'ops': out['adds']
           + [{'op': 'remove', 'uuid': u} for u in sorted(RM)]},
          open(os.path.join(HERE, 'ops_b5.json'), 'w'), indent=1)
print('\nwrote ops_b5.json (%d adds, %d removes)' % (len(out['adds']), len(RM)))
