"""rf-de-20m P7 - stitch the B.Cu +40V bus bridge to the F.Cu bus.

WHY THE BRIDGE: on F.Cu the x 39..51 / y 12..34 channel is a single corridor
that BOTH /SW (FET drains -> L301) and +40V (bulk -> HF bank/choke) have to
cross, and two nets cannot cross on one layer.  /SW keeps F.Cu (its loop area
is the whole design); the DC bus takes B.Cu.

WHY THIS RUNS FIRST: a via added into an ALREADY-FILLED plane takes the
plane's net, not the net the op asked for - KiCad re-derives it from
connectivity because the fill has no antipad yet.  Measured on this board:
identical ops gave `(net "GND")` on a poured board and `(net "+40V")` on a
bare one.  So the bridge vias are placed on the BARE board, before
planes_gen, and the pours flow around them.
"""
import json
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import Point, LineString, box                # noqa: E402
from shapely.ops import unary_union                                # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_bridge.json'
VIA_D, VIA_DRILL = 0.6, 0.3
CLR = {'+40V': 0.5, '/SW': 0.8, '/tank/TANK_A': 0.8, '/tank/TANK_B': 0.8,
       '/tank/RFOUT': 0.8}
HOLE2HOLE = 0.5

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

# blockers: foreign pads at their rule clearance, own pads at 0.15 (no
# via-in-pad on an SMD land), and the /SW land track that lands later.
blk = []
for p in bg.pads_of():
    need = 0.15 if p.net == '+40V' else max(CLR['+40V'], CLR.get(p.net, 0.1016))
    blk.append(p.poly.buffer(need + VIA_D / 2.0))
    if p.drill is not None:
        blk.append(p.drill_poly.buffer(HOLE2HOLE + VIA_DRILL / 2.0))
sw_track = LineString([(51.40 + OX, 17.60 + OY),
                       (52.60 + OX, 17.60 + OY)]).buffer(11.8942 / 2.0)
blk.append(sw_track.buffer(CLR['/SW'] + VIA_D / 2.0))
blocked = unary_union(blk)

# the two pour footprints the via must land inside on BOTH outer layers
F_CU = box(37.4 + OX, 0.4 + OY, 51.0 + OX, 13.5 + OY).union(
    box(16.2 + OX, 31.0 + OY, 51.0 + OX, 34.2 + OY))
B_CU = box(42.5 + OX, 6.0 + OY, 51.3 + OX, 33.0 + OY)
region = F_CU.intersection(B_CU).buffer(-(VIA_D / 2.0 + 0.3))

placed, ops = [], []


def grid(x0, y0, x1, y1, step, tag):
    n = 0
    y = y0
    while y <= y1 + 1e-9:
        x = x0
        while x <= x1 + 1e-9:
            ax, ay = x + OX, y + OY
            pt = Point(ax, ay)
            if region.contains(pt) and not blocked.contains(pt) \
                    and not blocked.intersects(pt.buffer(1e-9)) \
                    and all((ax - px) ** 2 + (ay - py) ** 2
                            >= (VIA_DRILL + HOLE2HOLE) ** 2
                            for px, py in placed):
                placed.append((ax, ay))
                ops.append({"op": "add_via",
                            "at": [round(ax, 4), round(ay, 4)],
                            "size": VIA_D, "drill": VIA_DRILL, "net": "+40V"})
                n += 1
            x += step
        y += step
    print(f'  {tag}: {n} vias')


grid(42.9, 6.4, 50.7, 13.2, 0.9, 'north cluster (F.Cu bus L201<->L202 band)')
grid(42.9, 31.3, 50.7, 32.9, 0.9, 'south cluster (F.Cu crossing band y 31-34)')

json.dump({"version": 1, "ops": ops}, open(OPS, 'w'), indent=1)
print(f'{len(ops)} bridge vias -> {OPS}')
