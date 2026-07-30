"""Per-segment min gap between two nets on one layer - the extent of the
conflict, not just the worst pair."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402
from capsule import cap_dist    # noqa: E402

na, nb = sys.argv[1], sys.argv[2]
th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.60
L = sys.argv[4] if len(sys.argv) > 4 else 'F.Cu'

src, items, zones, edges = bm.load()
A = [(c, t, u) for (l, n, c, t, u) in items if l == L and n == na]
B = [(c, t, u) for (l, n, c, t, u) in items if l == L and n == nb]
for (label, X, Y) in ((na, A, B), (nb, B, A)):
    print('=== %s segments, min gap to the other net (%s) ===' % (label, L))
    rows = []
    for (c, t, u) in X:
        g = min([cap_dist(c, d) for (d, _t, _u) in Y] or [9e9])
        rows.append((g, t, u, c))
    rows.sort()
    for (g, t, u, c) in rows:
        flag = 'FAIL' if g < th else '    '
        print('  %s %7.4f  %-9s %-16s (%.3f,%.3f)-(%.3f,%.3f)'
              % (flag, g, u[:8], t, c[0][0], c[0][1], c[1][0], c[1][1]))
    print('  -> %d of %d under %.3f' % (sum(1 for r in rows if r[0] < th),
                                        len(rows), th))
