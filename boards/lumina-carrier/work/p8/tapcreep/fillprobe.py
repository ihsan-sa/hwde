"""How close does each inner-layer plane FILL come to the tap-via pocket?

Zone outlines cover the pocket (zone9 In1, zone10 In2), but a fill is cut back
around foreign copper, so the outline says nothing about the real gap. This
walks every filled_polygon edge and reports the nearest fill copper to a probe
point, per layer and per zone net - which tells me whether moving a via inside
this pocket can disturb a pour (and therefore whether refill can produce new
sliver warnings).
"""
import io
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capsule import blocks   # noqa: E402

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
PROBES = [('A2 via new', (49.200, 73.275)), ('A1 via new', (49.675, 74.325)),
          ('A2 via old', (49.200, 73.400)), ('A1 via old', (49.650, 74.213))]

src = io.open(PCB, encoding='utf-8').read()


def pt_seg(p, s1, s2):
    vx, vy = s2[0] - s1[0], s2[1] - s1[1]
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return math.hypot(p[0] - s1[0], p[1] - s1[1])
    t = max(0.0, min(1.0, ((p[0] - s1[0]) * vx + (p[1] - s1[1]) * vy) / L2))
    return math.hypot(p[0] - (s1[0] + t * vx), p[1] - (s1[1] + t * vy))


results = {}
zi = 0
for (s, e) in blocks(src, 'zone'):
    b = src[s:e]
    zi += 1
    nt = re.search(r'\(net_name\s+"([^"]*)"\)', b)
    net = nt.group(1) if nt else '(none)'
    lay = re.search(r'\(layers?\s+"([^"]+)"', b)
    lay = lay.group(1) if lay else '?'
    for (fs, fe) in blocks(b, 'filled_polygon'):
        fb = b[fs:fe]
        lm = re.search(r'\(layer\s+"([^"]+)"\)', fb)
        L = lm.group(1) if lm else lay
        pts = [(float(x), float(y)) for x, y in
               re.findall(r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)', fb)]
        if len(pts) < 2:
            continue
        for (name, P) in PROBES:
            best = 9e9
            for i in range(len(pts)):
                d = pt_seg(P, pts[i], pts[(i + 1) % len(pts)])
                if d < best:
                    best = d
            k = (name, L, net)
            if k not in results or best < results[k]:
                results[k] = best

for (name, P) in PROBES:
    print('probe %s at (%.3f, %.3f)' % (name, P[0], P[1]))
    rows = sorted([(v, k) for k, v in results.items() if k[0] == name])
    for (v, k) in rows[:6]:
        print('   %-8s net=%-10s nearest fill edge %.4f mm  -> copper gap to a '
              '0.25 mm-radius via pad = %.4f' % (k[1], k[2], v, v - 0.25))
    print()
