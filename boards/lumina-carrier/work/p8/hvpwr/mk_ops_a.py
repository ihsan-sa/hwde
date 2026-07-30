"""Emit route_edit ops for cluster A items 1-4: replace the 39-segment SHIELD
pad19->pad20 staircase with the optimised 6-segment polyline from solve_a.json.
Adds and removes are disjoint geometry, so one atomic ops file is safe.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
sol = json.load(open(os.path.join(HERE, 'solve_a.json')))
way = sol['polyline']
w = sol['width']
ops = []
for i in range(len(way) - 1):
    ops.append({'op': 'add_track', 'start': [round(way[i][0], 4),
                                             round(way[i][1], 4)],
                'end': [round(way[i + 1][0], 4), round(way[i + 1][1], 4)],
                'width': w, 'layer': 'F.Cu', 'net': '/poe/SHIELD'})
for u in sol['remove_uuids']:
    ops.append({'op': 'remove', 'uuid': u})
json.dump({'version': 1, 'ops': ops},
          open(os.path.join(HERE, 'ops_a.json'), 'w'), indent=1)
print('%d adds, %d removes' % (len(way) - 1, len(sol['remove_uuids'])))
