"""Full net-pair sweep: EVERY item pair on a layer closer than a threshold.

Exists because a worst-pair-only report hides siblings (the adjacent work order
fixed a 0.3292 mm gap and only then found a 0.5500 mm pair on the same nets).

Usage: sweep.py NET_A NET_B [thresh] [layer]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

na, nb = sys.argv[1], sys.argv[2]
th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.60
layers = [sys.argv[4]] if len(sys.argv) > 4 else bm.CU

src, items, zones, edges = bm.load()
for L in layers:
    A = [(c, t, u) for (l, n, c, t, u) in items if l == L and n == na]
    B = [(c, t, u) for (l, n, c, t, u) in items if l == L and n == nb]
    rows = []
    for (ca, ta, ua) in A:
        for (cb, tb, ub) in B:
            g = cap_dist(ca, cb)
            if g < th:
                rows.append((g, ta, ua, ca, tb, ub, cb))
    rows.sort()
    print('=== %s : %s vs %s  (nA=%d nB=%d)  %d pairs under %.3f'
          % (L, na, nb, len(A), len(B), len(rows), th))
    for (g, ta, ua, ca, tb, ub, cb) in rows:
        print('  %.4f  A %-16s %-9s (%.3f,%.3f)-(%.3f,%.3f)'
              % (g, ta, ua[:8], ca[0][0], ca[0][1], ca[1][0], ca[1][1]))
        print('          B %-16s %-9s (%.3f,%.3f)-(%.3f,%.3f)'
              % (tb, ub[:8], cb[0][0], cb[0][1], cb[1][0], cb[1][1]))
