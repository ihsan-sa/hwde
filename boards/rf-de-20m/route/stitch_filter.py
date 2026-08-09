"""Filter stitch_vias' dry-run ops down to the vias that belong.

stitch_vias runs while only the GND pours exist (so its vias take the GND
net), which means its area grid also covers ground that the power pours will
claim in the next pass.  Vias left inside a power pour would punch antipads
through it for no benefit, so they are dropped here.  Everything stitch_vias
decided about candidate legality (layer contact, foreign copper, hole-to-hole)
is kept as-is.
"""
import json
import sys

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402
from shapely.geometry import Point, box                            # noqa: E402
from shapely.ops import unary_union                                # noqa: E402

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'
DRY = r'C:/dev/ai-ee3/boards/rf-de-20m/route/stitch_dry.json'
FULL = r'C:/dev/ai-ee3/boards/rf-de-20m/route/planes.json'
OUT = r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_stitch.json'
GUARD = 0.55                     # via pad radius 0.3 + the widest HV rule/2

bg = load_board(PCB)
power = unary_union(
    [box(*p['region']).buffer(GUARD)
     for p in json.load(open(FULL))['planes']
     if p['net'] != 'GND' and p['layer'] in ('F.Cu', 'B.Cu')]
    # ... and clear of the HV land tracks, which reach outside those rects
    + [t.shape.buffer(t.width / 2.0 + 0.8 + 0.3)
       for t in bg.tracks_of() if t.net not in ('GND',)])

ops = [o for o in json.load(open(DRY))['ops']
       if not power.contains(Point(*o['at']))]
dropped = len(json.load(open(DRY))['ops']) - len(ops)
json.dump({"version": 1, "ops": ops}, open(OUT, 'w'), indent=1)
print(f'stitch ops kept {len(ops)}, dropped {dropped} inside power pours '
      f'-> {OUT}')
