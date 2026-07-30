"""What does the board already keep away from J1's two netless board-lock pads?

If HV nets elsewhere already sit at 0.2-0.3 mm from them, then treating them as
shield-potential metal is not what this board does and 0.226 mm is not a
regression.  If everything is >=0.6 mm, it is.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

src, items, zones, edges = bm.load()
LOCKS = [((46.300, 68.173), (46.300, 68.173), 1.600),
         ((34.870, 68.173), (34.870, 68.173), 1.600)]
for i, lk in enumerate(LOCKS):
    print('=== board-lock pad %d at (%.3f,%.3f) r=1.600 ===' % (i, lk[0][0],
                                                                lk[0][1]))
    for L in bm.CU:
        rows = []
        for (lay, net, cap, tag, uu) in items:
            if lay != L or 'circle 3.20' in tag:
                continue
            g = cap_dist(lk, cap)
            if g < 1.5:
                rows.append((g, net or '(no net)', tag, uu[:8]))
        rows.sort()
        print('  %s:' % L)
        for r in rows[:8]:
            print('     %7.4f  %-22s %-26s %s' % r)
