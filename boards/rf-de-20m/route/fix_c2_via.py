"""Relocate the U201.C2 GND via: 0.6/0.3 at (23.35, 24.85) -> 0.45/0.20 at
(23.45, 24.80).

The first placement cleared COPPER (0.1016 mm) but not HOLE clearance: the
board's 0.25 mm hole-to-copper floor was 0.175 mm to the GATE_OFF feed track.
At a 0.6 mm pad there is no position that both overlaps C2 (a 0.2 mm WCSP
ball) and keeps the pad 0.1016 mm off C1 one ball to the north, so the via
drops to the fab floor size.
"""
import json
import math
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_c2via.json'

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
old = (23.35 + OX, 24.85 + OY)
new = (23.45 + OX, 24.80 + OY)

ops = []
for v in bg.vias_of(net='GND'):
    if math.dist(v.at, old) < 0.02:
        ops.append({"op": "remove", "uuid": v.uuid})
        print(f'removing old C2 via {v.uuid} (size {v.diameter}/{v.drill})')
ops.append({"op": "add_via", "at": [round(new[0], 4), round(new[1], 4)],
            "size": 0.45, "drill": 0.2, "net": "GND"})
json.dump({"version": 1, "ops": ops}, open(OPS, 'w'), indent=1)
print(f'{len(ops)} ops -> {OPS}')
