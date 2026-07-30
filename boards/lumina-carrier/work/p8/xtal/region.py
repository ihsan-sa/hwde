"""List all copper items intersecting a board-relative region, per layer.
usage: region.py X0 X1 Y0 Y1 [LAYER...]"""
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import placelib  # noqa: E402
from shapely.geometry import box  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
X0, X1, Y0, Y1 = (float(a) for a in sys.argv[1:5])
LAYERS = sys.argv[5:] or ["F.Cu", "B.Cu"]

bg = geom.load_board(PCB)
ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]
R = box(ox + X0, oy + Y0, ox + X1, oy + Y1)


def rel(x, y):
    return (round(x - ox, 3), round(y - oy, 3))


for lay in LAYERS:
    print("=== %s ===" % lay)
    rows = []
    for t in bg.tracks_of(layer=lay):
        if t.poly.intersects(R):
            a, b = list(t.shape.coords)[0], list(t.shape.coords)[-1]
            rows.append((t.net, "trk", rel(*a), rel(*b), t.width,
                         round(t.length, 3)))
    for r in sorted(rows, key=lambda r: (r[0], r[2])):
        print("  %-22s %s %s -> %s w%.3f len%.3f" % r)
    for v in bg.vias_of():
        if v.spans(lay) and v.poly.intersects(R):
            print("  %-22s via %s d%.2f" % (v.net, rel(*v.at), v.diameter))
    for p in bg.pads_of(layer=lay):
        if p.poly.intersects(R):
            print("  %-22s pad %s.%s %s %s" % (p.net, p.ref, p.number,
                                               rel(*p.center), p.size))
print("=== footprints (extents overlapping region) ===")
model = placelib.PlaceModel(PCB)
for ref, f in sorted(model.footprints.items()):
    e = f.extents_abs()
    if e.intersects(R):
        b = e.bounds
        print("  %-6s %-8s at %s deg %.1f extents rel [%.2f,%.2f]-[%.2f,%.2f]"
              % (ref, f.side, rel(*f.pos), f.angle,
                 b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy))
