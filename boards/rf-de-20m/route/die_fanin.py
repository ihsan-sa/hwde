"""rf-de-20m P7 - EPC2019 source fan-in tracks.

`aiee_hv_143v_SW` (0.8 mm, from /SW's 143 V peak) governs the zone filler and
therefore holds every pour 0.20-0.66 mm clear of the die's source bumps.  The
bumps are on a 0.6 mm pitch with 0.35 mm gaps to the drain bars, so the only
conductor that fits is the bump's own 0.25 mm width - which is what the 12
pre-approved intra-EPC2019 clearance findings already describe.

GND carries no per-net width rule, so these add no track_width findings; they
add clearance findings at 0.35 mm, i.e. exactly the land pattern's own pitch,
never tighter.
"""
import json
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import LineString                            # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
OPS = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_fanin.json'
DY = 4.20                        # Q201 -> Q202 (translated, not mirrored)
W = 0.25

bg = load_board(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
PADS = bg.pads_of(layer='F.Cu')
TRACKS = bg.tracks_of(layer='F.Cu')

# (x0, y0, x1, y1) for the Q201 half, board-local; Q202 = +DY in y
SEGS = [
    (30.30, 23.12, 29.90, 23.12),    # pin2 (source) -> west lobe
    (32.70, 23.12, 33.15, 23.12),    # pin6 (source) -> east lobe
    (32.70, 22.67, 33.15, 22.67),    # pin7 (substrate=source) -> east lobe
]
# pin4, the centre source bar: escapes AWAY from the other die
SEGS_Q1 = [(31.50, 22.90, 31.50, 21.70)]
SEGS_Q2 = [(31.50, 27.10, 31.50, 28.30)]


def check(seg):
    g = LineString([(seg[0] + OX, seg[1] + OY),
                    (seg[2] + OX, seg[3] + OY)]).buffer(W / 2.0, quad_segs=24)
    worst, who = 1e9, None
    for p in PADS:
        if p.net == 'GND':
            continue
        need = 0.8 if p.net == '/SW' else 0.1016
        d = g.distance(p.poly)
        if d - need < worst:
            worst, who = d - need, f'{p.ref}.{p.number}[{p.net}] d={d:.4f}'
    for t in TRACKS:
        if t.net == 'GND':
            continue
        need = 0.8 if t.net == '/SW' else 0.1016
        d = g.distance(t.shape.buffer(t.width / 2.0))
        if d - need < worst:
            worst, who = d - need, f'track[{t.net}] d={d:.4f}'
    return worst, who


ops = []
for seg in SEGS:
    for dy in (0.0, DY):
        ops.append((seg[0], seg[1] + dy, seg[2], seg[3] + dy))
ops += SEGS_Q1 + SEGS_Q2

out = []
for seg in ops:
    slack, who = check(seg)
    tag = 'ok ' if slack >= 0 else ('INTRA-EPC' if slack > -0.5 else 'VIOL')
    print(f'{tag:10s} ({seg[0]:6.2f},{seg[1]:6.2f})->({seg[2]:6.2f},'
          f'{seg[3]:6.2f}) w={W}  slack={slack:+.4f}  {who}')
    out.append({"op": "add_track",
                "start": [round(seg[0] + OX, 4), round(seg[1] + OY, 4)],
                "end": [round(seg[2] + OX, 4), round(seg[3] + OY, 4)],
                "width": W, "layer": "F.Cu", "net": "GND"})

# U201.C2 (driver GND return): a 0.2 mm ball boxed in by C1 north and B2
# east, with no room for a track to the pour - one via whose pad overlaps it.
# 0.45/0.20 (the fab floor), not 0.6/0.3: at 0.6 there is no position that
# both overlaps C2 and keeps a 0.6 mm pad 0.1016 mm off C1 one ball north.
out.append({"op": "add_via", "at": [round(23.45 + OX, 4), round(24.80 + OY, 4)],
            "size": 0.45, "drill": 0.2, "net": "GND"})
print('  + U201.C2 GND via at local (23.45, 24.80), 0.45/0.20')

json.dump({"version": 1, "ops": out}, open(OPS, 'w'), indent=1)
print(f'{len(out)} die fan-in tracks -> {OPS}')
