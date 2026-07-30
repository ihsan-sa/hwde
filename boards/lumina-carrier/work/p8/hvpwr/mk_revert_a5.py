"""Withdraw the item-5 edit entirely: re-add the 40 original segments and remove
the 12 that ops_a5.json put on the board.

The applied arrangement was geometrically invalid - two LED_Y_A/LED_G_A track
crossings that DRC caught and that my capsule model could not see (see
board_model.seg_cross).  The board must go back to the state that reads
drc_routed 0: cluster A items 1-4 plus cluster B B3/B4.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_model as bm    # noqa: E402

NEW = [  # the 12 segments ops_a5.json added
    ((50.250, 68.750), (47.976, 66.302)), ((47.976, 66.302), (46.159, 65.699)),
    ((46.159, 65.699), (44.452, 66.426)), ((44.452, 66.426), (43.984, 67.622)),
    ((43.984, 67.622), (43.760, 70.743)),
    ((47.210, 64.123), (48.225, 64.865)), ((48.225, 64.865), (49.700, 66.600)),
    ((58.100, 75.600), (52.0889, 67.0667)),
    ((52.0889, 67.0667), (47.420, 65.283)),
    ((47.420, 65.283), (45.877, 64.830)), ((45.877, 64.830), (44.564, 65.335)),
    ((44.564, 65.335), (36.490, 64.123)),
]
restore = json.load(open(os.path.join(HERE, 'ops_a5_restore.json')))['ops']
print('originals to re-add: %d' % len(restore))
assert len(restore) == 40, len(restore)

src, items, zones, edges = bm.load()
rm = []
for (L, n, c, t, u) in items:
    if L != 'F.Cu' or not t.startswith('segment'):
        continue
    for pair in NEW:
        if ((math.dist(c[0], pair[0]) < 2e-3 and math.dist(c[1], pair[1]) < 2e-3)
                or (math.dist(c[1], pair[0]) < 2e-3
                    and math.dist(c[0], pair[1]) < 2e-3)):
            rm.append(u)
print('found %d of the 12 applied segments' % len(rm))
assert len(rm) == 12, len(rm)

# sanity: no re-added original shares geometry with a segment being removed
for a in restore:
    for pair in NEW:
        s, e = tuple(a['start']), tuple(a['end'])
        if ((math.dist(s, pair[0]) < 1e-3 and math.dist(e, pair[1]) < 1e-3)
                or (math.dist(e, pair[0]) < 1e-3
                    and math.dist(s, pair[1]) < 1e-3)):
            raise SystemExit('geometry collision - needs two passes: %s' % a)
print('no add/remove geometry collision: single atomic call is safe')

ops = list(restore) + [{'op': 'remove', 'uuid': u} for u in rm]
json.dump({'version': 1, 'ops': ops},
          open(os.path.join(HERE, 'ops_a5_revert.json'), 'w'), indent=1)
print('wrote ops_a5_revert.json (%d adds, %d removes)' % (len(restore), len(rm)))
