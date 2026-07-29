"""antenna_check.py - measure copper inside the ESP32-S3 antenna keepout.

Reports, per copper layer, the copper area inside
  CORE   = the true Espressif 6 x 18 mm antenna zone + margin to the board edge
  BAND   = the full declared 10 x 22 mm keepout (constraints.placement.keepouts)
and lists what the copper belongs to. Run from the repo root.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import box, Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

BAND = box(109.58, 86.132, 119.58, 108.132)
CORE = box(112.6, 86.132, 119.58, 108.132)

pcb = sys.argv[1] if len(sys.argv) > 1 else str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
bg = geom.BoardGeom.from_file(pcb)

for lay in bg.copper_layers:
    items = []
    for t in bg.tracks_of(layer=lay):
        g = geom.LineString([t.start, t.end]).buffer(t.width / 2.0, quad_segs=8)
        items.append(("track " + (t.net or "?"), g))
    for v in bg.vias_of():
        if lay in v.layers:
            items.append(("via " + (v.net or "?"),
                          Point(*v.at).buffer(v.diameter / 2.0, quad_segs=8)))
    for p in bg.pads_of():
        if lay in p.layers:
            items.append(("pad %s.%s %s" % (p.ref, p.number, p.net), p.poly))
    for net in sorted(bg.nets):
        f = bg.zone_fill(net, lay)
        if not f.is_empty:
            items.append(("fill " + net, f))
    for rect, name in ((CORE, "CORE"), (BAND, "BAND")):
        hits = [(w, g.intersection(rect)) for w, g in items
                if g.intersects(rect)]
        hits = [(w, g) for w, g in hits if g.area > 1e-6]
        area = round(sum(g.area for _w, g in hits), 4)
        who = sorted({w for w, _ in hits})
        print("%-7s %-6s copper %8.4f mm2  %s" % (lay, name, area,
                                                  ", ".join(who) or "-"))
