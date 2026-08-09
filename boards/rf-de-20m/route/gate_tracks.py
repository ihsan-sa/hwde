"""rf-de-20m P7 - the four gate legs, mirrored about the U201 output axis.

Everything is authored for the Q201 half in board-local mm and reflected to
the Q202 half about y = MIRROR (= the y of U201's OUTH/OUTL row), so the two
FETs' gate loops are congruent by construction.

TOPOLOGY NOTE (reported to the orchestrator): U201's OUTH (A2) and OUTL (B2)
sit side by side on one row with OUTL to the WEST, while OUTL's resistors
(R205/R206) are the OUTER pair and OUTH's (R203/R204) the INNER pair.  A net
whose targets straddle another net's targets, with its source on the far
side, has no planar routing: OUTL has to wrap around OUTH.  The wrap is taken
on the west of U201 so that both OUTL legs stay exact mirrors of each other.
"""
import json
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import LineString                            # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_gates.json'
MIRROR = 24.775
CLR = {'+40V': 0.5, '/SW': 0.8, '/tank/TANK_A': 0.8, '/tank/TANK_B': 0.8,
       '/tank/RFOUT': 0.8}

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
PADS = bg.pads_of(layer='F.Cu')

# COMMON: drawn once (feeds, and the axis bar that lands on BOTH resistors)
COMMON = [
    # --- GATE_ON (OUTH, U201.A2): one bar down the axis.  At w >= 1.024 it
    #     touches R203.1 and R204.1 simultaneously, so the two legs ARE the
    #     same copper and are identical by construction.
    ('/stage/GATE_ON', 24.52, MIRROR, 24.95, MIRROR, 0.30),
    ('/stage/GATE_ON', 24.95, MIRROR, 25.70, MIRROR, 0.70),
    ('/stage/GATE_ON', 25.70, MIRROR, 26.60, MIRROR, 1.30),
    # --- GATE_OFF (OUTL, U201.B2) feed: south out of B2, west past U201,
    #     then back onto the axis from the WEST so the split point at
    #     (22.55, axis) is fed symmetrically, and U201.C2 keeps an escape east of it.
    ('/stage/GATE_OFF', 24.08, MIRROR, 24.08, 25.45, 0.30),
    ('/stage/GATE_OFF', 24.08, 25.45, 22.55, 25.45, 0.55),
    ('/stage/GATE_OFF', 22.55, 25.45, 22.55, MIRROR, 0.55),
    # GATE_Qn die escape.  Q201 and Q202 are TRANSLATED, not mirrored (same
    # die angle - LEARNINGS 2026-08-08 [placement][gate-drive]), so this
    # segment is authored twice rather than reflected: in both dies the gate
    # bump sits 0.19 mm ABOVE its source bump, and the stub has to sit high
    # enough in y to leave that source pad reachable by the GND lobe.
    ('/stage/GATE_Q1', 30.20, 22.55, 29.20, 22.55, 0.40),
    ('/stage/GATE_Q2', 30.20, 26.76, 29.20, 26.76, 0.40),
]

# MIRRORED: drawn for the Q201 half and reflected about y = MIRROR
SEGS = [
    # --- GATE_OFF legs from the axis split at (22.55, MIRROR) -------------
    ('/stage/GATE_OFF', 22.55, MIRROR, 22.55, 22.425, 0.55),
    ('/stage/GATE_OFF', 22.55, 22.425, 26.20, 22.425, 0.55),
    ('/stage/GATE_OFF', 26.20, 22.425, 26.50, 21.500, 0.55),
    # --- GATE_Q1: Q201.1 -> R203.2 and R205.2 -----------------------------
    # the die escape (above, in COMMON) is 0.40 mm - the widest the die
    # admits, since the gate bump is 0.35 mm from the drain bar.  From the
    # junction outward the legs run 1.00 mm for the inductance budget.
    ('/stage/GATE_Q1', 29.20, 22.67, 28.80, 23.575, 1.00),
    ('/stage/GATE_Q1', 29.20, 22.67, 28.80, 21.275, 1.00),
]

MIRROR_NET = {'/stage/GATE_OFF': '/stage/GATE_OFF',
              '/stage/GATE_Q1': '/stage/GATE_Q2'}


def stadium(x0, y0, x1, y1, w):
    return LineString([(x0 + OX, y0 + OY),
                       (x1 + OX, y1 + OY)]).buffer(w / 2.0, quad_segs=24)


def check(net, seg):
    g = stadium(*seg)
    worst, who = 1e9, None
    for p in PADS:
        if p.net == net:
            continue
        need = max(CLR.get(net, 0.1016), CLR.get(p.net, 0.1016))
        d = g.distance(p.poly)
        if d - need < worst:
            worst, who = d - need, (f'{p.ref}.{p.number}[{p.net}] '
                                    f'd={d:.3f} need={need:.3f}')
    return worst, who


def mirror(seg):
    x0, y0, x1, y1, w = seg
    return (x0, 2 * MIRROR - y0, x1, 2 * MIRROR - y1, w)


ops, bad = [], 0
emit = [(net, tuple(seg)) for net, *seg in COMMON]
for net, *seg in SEGS:
    emit.append((net, tuple(seg)))
    emit.append((MIRROR_NET[net], mirror(tuple(seg))))

for n, s in emit:
    slack, who = check(n, s)
    flag = 'ok ' if slack >= 0 else 'INTRA-EPC' if slack > -0.5 else 'VIOL'
    if slack < 0:
        bad += 1
    print(f'{flag:10s} {n:18s} ({s[0]:6.2f},{s[1]:6.2f})->({s[2]:6.2f},'
          f'{s[3]:6.2f}) w={s[4]:.2f}  slack={slack:+.3f}  {who}')
    ops.append({"op": "add_track",
                "start": [round(s[0] + OX, 4), round(s[1] + OY, 4)],
                "end": [round(s[2] + OX, 4), round(s[3] + OY, 4)],
                "width": s[4], "layer": "F.Cu", "net": n})

json.dump({"version": 1, "ops": ops}, open(OPS, 'w'), indent=1)
print(f'\n{len(ops)} ops, {bad} clearance violations -> {OPS}')
