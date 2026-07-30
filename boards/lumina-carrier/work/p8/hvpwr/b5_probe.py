"""B5: the +48V_SW diagonal (50.45,97.55)-(47.40,100.60).  At w=0.500 the
binding item is pad U22-11 (roundrect 1.57x0.40, /pwr/ILIM) at 0.6162 mm vs the
0.635 mm HV_48V_clearance rule - a 0.0188 mm deficit against an IMMOVABLE pad.

Two questions:
  1. is U22-11 on the same side as everything else, i.e. can the diagonal shift
     perpendicular by ~0.03 mm to clear it, and what binds on the other side?
  2. is the segment inside U22's courtyard (which would exempt it from the DRU
     rule, leaving only the 0.600 mm creepage number that 0.6162 already meets)?
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

S, E = (50.45, 97.55), (47.40, 100.60)
NET = '+48V_SW'
src, items, zones, edges = bm.load()

# perpendicular unit of the 45 deg diagonal
dx, dy = E[0] - S[0], E[1] - S[1]
L = math.hypot(dx, dy)
ux, uy = dx / L, dy / L
nx, ny = -uy, ux        # left normal


def caps(shift, w):
    a = (S[0] + nx * shift, S[1] + ny * shift)
    b = (E[0] + nx * shift, E[1] + ny * shift)
    return (a, b, w / 2.0)


print('F.Cu + via neighbours of the diagonal at w=0.500, with the side they '
      'are on (+ = left normal (%.3f,%.3f)):' % (nx, ny))
c0 = caps(0.0, 0.500)
rows = []
for (Ly, n2, c2, t2, u2) in items:
    if n2 == NET:
        continue
    if Ly != 'F.Cu' and not t2.startswith('via'):
        continue
    g = cap_dist(c0, c2)
    if g > 1.4:
        continue
    mid = ((c2[0][0] + c2[1][0]) / 2, (c2[0][1] + c2[1][1]) / 2)
    side = (mid[0] - S[0]) * nx + (mid[1] - S[1]) * ny
    req = bm.required(NET, n2) or 0.20
    rows.append((g - req, g, req, 'L' if side > 0 else 'R', n2 or '(none)',
                 t2, u2[:8], Ly))
for (Ly, n2, pts, t2, _u) in bm.PADS_POLY:
    if Ly != 'F.Cu' or n2 == NET:
        continue
    g = bm.poly_dist(c0, pts)
    if g > 1.4:
        continue
    mid = (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4)
    side = (mid[0] - S[0]) * nx + (mid[1] - S[1]) * ny
    req = bm.required(NET, n2) or 0.20
    rows.append((g - req, g, req, 'L' if side > 0 else 'R', n2 or '(none)',
                 t2, '', 'F.Cu'))
rows.sort()
for r in rows[:18]:
    print('  margin %+8.4f gap %7.4f req %.3f  side %s  %-14s %-26s %-9s %s'
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))

print('\nshift sweep (perpendicular, w=0.500): worst margin per side')
for sh in [round(-0.20 + 0.02 * i, 3) for i in range(21)]:
    c = caps(sh, 0.500)
    wl = wr = 9e9
    for (Ly, n2, c2, t2, u2) in items:
        if n2 == NET or (Ly != 'F.Cu' and not t2.startswith('via')):
            continue
        g = cap_dist(c, c2) - (bm.required(NET, n2) or 0.20)
        mid = ((c2[0][0] + c2[1][0]) / 2, (c2[0][1] + c2[1][1]) / 2)
        side = (mid[0] - S[0]) * nx + (mid[1] - S[1]) * ny
        if side > 0:
            wl = min(wl, g)
        else:
            wr = min(wr, g)
    for (Ly, n2, pts, t2, _u) in bm.PADS_POLY:
        if Ly != 'F.Cu' or n2 == NET:
            continue
        g = bm.poly_dist(c, pts) - (bm.required(NET, n2) or 0.20)
        mid = (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4)
        side = (mid[0] - S[0]) * nx + (mid[1] - S[1]) * ny
        if side > 0:
            wl = min(wl, g)
        else:
            wr = min(wr, g)
    print('  shift %+6.3f  left %+8.4f  right %+8.4f  worst %+8.4f'
          % (sh, wl, wr, min(wl, wr)))

# courtyard test
print('\nU22 courtyard polygons:')
for (fs, fe) in bm.blocks(src, 'footprint'):
    fb = src[fs:fe]
    rm = re.search(r'\(property "Reference" "U22"\)', fb)
    if not rm:
        continue
    for tok in ('fp_poly', 'fp_line', 'fp_rect'):
        for (ps, pe) in bm.blocks(fb, tok):
            pbb = fb[ps:pe]
            if 'CrtYd' not in pbb:
                continue
            xs = [(float(a), float(b)) for (a, b) in
                  re.findall(r'\((?:xy|start|end)\s+(-?[\d.]+)\s+(-?[\d.]+)\)',
                             pbb)]
            print('   %s %s' % (tok, xs))
    fat = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)', fb)
    print('   footprint at %s' % (fat.groups(),))
    break
