"""Ground facts: J1 pad table, SHIELD net inventory, zones present per layer."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402

src, items, zones, edges = bm.load()

print('--- zones (filled polys) per layer/net ---')
z = {}
for (L, n, pts) in zones:
    z[(L, n)] = z.get((L, n), 0) + 1
for k in sorted(z):
    print('  %-8s %-24s %d polys' % (k[0], k[1] or '(none)', z[k]))

print('\n--- J1 pads (F.Cu) ---')
for (L, net, cap, tag, uu) in items:
    if L == 'F.Cu' and tag.startswith('pad J1-'):
        print('  %-30s net=%-22s spine (%.3f,%.3f)-(%.3f,%.3f) r=%.3f'
              % (tag, net or '(none)', cap[0][0], cap[0][1],
                 cap[1][0], cap[1][1], cap[2]))

for want in ('/poe/SHIELD', '/poe/LED_Y_A'):
    print('\n--- net %s, all layers ---' % want)
    for L in bm.CU:
        rows = [(cap, tag, uu) for (lay, net, cap, tag, uu) in items
                if lay == L and net == want]
        print('  %s: %d items' % (L, len(rows)))
        for (cap, tag, uu) in rows:
            print('     %-26s (%.3f,%.3f)-(%.3f,%.3f) r=%.3f %s'
                  % (tag, cap[0][0], cap[0][1], cap[1][0], cap[1][1],
                     cap[2], uu[:8]))

print('\n--- Edge.Cuts near J1 (x 28..52, y 60..80) ---')
for (a, b) in edges:
    if min(a[0], b[0]) > 52 or max(a[0], b[0]) < 28:
        continue
    if min(a[1], b[1]) > 80 or max(a[1], b[1]) < 60:
        continue
    print('  (%.3f,%.3f)-(%.3f,%.3f)' % (a[0], a[1], b[0], b[1]))
