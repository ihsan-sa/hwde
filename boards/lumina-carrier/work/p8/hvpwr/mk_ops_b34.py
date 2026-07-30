"""Cluster B items B3 and B4: widen the V48_RAW trunk 0.200 -> 0.500 mm.

Both pinches are the SAME pattern: a signal net hops to B.Cu to cross the
V48_RAW vertical trunk, and its two transition vias sit 1.050 mm either side of
the trunk centreline.  At w=0.200 that is a 0.650 mm gap (the HV_48V_clearance
rule wants 0.635, so it barely passes today); at w=0.500 it becomes 0.500 mm and
fails.  Nothing about the signal net needs to be where it is: pushing each via
0.200 mm further from the trunk restores 0.700 mm (margin +0.065) and the
V48_RAW segment then reaches its full 0.500 mm.

Two route_edit invocations are required (LEARNINGS / work-order note): the
V48_RAW segment keeps its exact geometry and only changes width, and
add_track dedups on geometry, so the remove must land in a separate call.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# --- pass 1: drop the two power segments whose width changes in place ---
pass1 = [{'op': 'remove', 'uuid': '14336a1a-96d7-46f7-9e56-4cd9c8bd6f6d'},
         {'op': 'remove', 'uuid': '7b8f3f07-04b7-4bd4-a53d-8c0fa8e2a1bc'}]

# --- pass 2: move the crossing vias out, re-add everything ---
B3_RM = ['d260095f', 'e5557c71', 'b77a0fae',        # vias
         '6aa8fe5e', '95f8d6db', '57b12116',        # F.Cu stubs
         'ca3a9520', '9770f59c']                    # B.Cu crossings
B4_RM = ['d2f1afc4', '348863bc', '22481719', '4c266a40', 'b029dcab']

ADD = [
    # ---- B3: V48_RAW trunk x=41.150, vias pushed 40.100->39.900 / 42.200->42.400
    dict(op='add_via', at=[39.900, 90.000], size=0.6, drill=0.3,
         net='/poe/APD'),
    dict(op='add_via', at=[39.900, 91.750], size=0.6, drill=0.3,
         net='/poe/T2P_OD'),
    dict(op='add_via', at=[42.400, 91.750], size=0.6, drill=0.3,
         net='/poe/T2P_OD'),
    dict(op='add_track', start=[39.900, 90.200], end=[39.900, 90.000],
         width=0.2, layer='F.Cu', net='/poe/APD'),
    dict(op='add_track', start=[39.900, 90.000], end=[52.300, 90.000],
         width=0.2, layer='B.Cu', net='/poe/APD'),
    dict(op='add_track', start=[39.850, 92.000], end=[39.900, 91.750],
         width=0.2, layer='F.Cu', net='/poe/T2P_OD'),
    dict(op='add_track', start=[42.400, 91.750], end=[42.450, 92.000],
         width=0.2, layer='F.Cu', net='/poe/T2P_OD'),
    dict(op='add_track', start=[39.900, 91.750], end=[42.400, 91.750],
         width=0.2, layer='B.Cu', net='/poe/T2P_OD'),
    dict(op='add_track', start=[41.150, 89.150], end=[41.150, 93.100],
         width=0.5, layer='F.Cu', net='V48_RAW'),
    # ---- B4: V48_RAW trunk x=27.400, vias 26.350->26.150 / 28.450->28.650
    dict(op='add_via', at=[26.150, 74.250], size=0.6, drill=0.3, net='/CDB'),
    dict(op='add_via', at=[28.650, 74.250], size=0.6, drill=0.3, net='/CDB'),
    dict(op='add_track', start=[26.150, 74.250], end=[25.750, 74.250],
         width=0.2, layer='F.Cu', net='/CDB'),
    dict(op='add_track', start=[28.650, 74.250], end=[30.150, 74.250],
         width=0.2, layer='F.Cu', net='/CDB'),
    dict(op='add_track', start=[26.150, 74.250], end=[28.650, 74.250],
         width=0.2, layer='B.Cu', net='/CDB'),
    dict(op='add_track', start=[27.400, 75.450], end=[27.400, 73.150],
         width=0.5, layer='F.Cu', net='V48_RAW'),
]

import sys                                                  # noqa: E402
sys.path.insert(0, HERE)
import board_model as bm                                     # noqa: E402
src, items, zones, edges = bm.load()
full = {}
for (L, n, c, t, u) in items:
    if u:
        full[u[:8]] = u
ops2 = list(ADD) + [{'op': 'remove', 'uuid': full[k]} for k in B3_RM + B4_RM]

# resolve the pass-1 uuids from the board rather than trusting the literals
p1 = []
for k in ('14336a1a', '7b8f3f07'):
    p1.append({'op': 'remove', 'uuid': full[k]})
json.dump({'version': 1, 'ops': p1},
          open(os.path.join(HERE, 'ops_b34_pass1.json'), 'w'), indent=1)
json.dump({'version': 1, 'ops': ops2},
          open(os.path.join(HERE, 'ops_b34_pass2.json'), 'w'), indent=1)
print('pass1: %d removes' % len(p1))
print('pass2: %d ops (%d adds, %d removes)'
      % (len(ops2), len(ADD), len(ops2) - len(ADD)))
