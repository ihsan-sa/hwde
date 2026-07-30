"""For each check_creepage violation, find the two closest copper ITEMS and
classify: same-footprint-courtyard (package escape) vs open-board routing."""
import json
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
import geom  # noqa
import placelib  # noqa
from shapely.ops import nearest_points  # noqa
from shapely.geometry import Point  # noqa
from shapely import affinity  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
REP = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\creepage.json")
bg = geom.load_board(PCB)

# DECLARED courtyards (the DRU's intersectsCourtyard semantics)
pm = placelib.PlaceModel(PCB)
COURT = {}
for f in pm.footprints.values():
    if f.courtyard_local is not None and not f.courtyard_local.is_empty:
        g = affinity.rotate(f.courtyard_local, -f.angle, origin=(0, 0))
        COURT[f.ref] = affinity.translate(g, f.pos[0], f.pos[1])


def items_on(net, layer):
    """(label, geometry) for every copper item of net on layer."""
    out = []
    for p in bg.pads_of(net):
        if layer in p.layers:
            out.append((f"PAD {p.ref}-{p.number}", p.poly))
    for t in bg.tracks_of(net, layer):
        a, b = t.shape.coords[0], t.shape.coords[-1]
        out.append((f"TRACK ({a[0]:.3f},{a[1]:.3f})-({b[0]:.3f},{b[1]:.3f}) w{t.width:.2f}",
                    t.poly))
    for v in bg.vias_of(net):
        if v.spans(layer):
            out.append((f"VIA ({v.at[0]:.3f},{v.at[1]:.3f}) d{v.diameter:.2f}", v.poly))
    for z in bg.zones_of(net, layer):
        f = z.fill_on(layer)
        if not f.is_empty:
            out.append((f"ZONE {z.net} {layer}", f))
    return out


def fps_at(pt, tol=0.0):
    """refdes whose DECLARED courtyard contains pt."""
    return sorted(ref for ref, cy in COURT.items()
                  if cy.buffer(tol).contains(Point(pt)))


rep = json.loads(REP.read_text())
rows = []
for v in rep["violations"]:
    net, other, layer = v["net"], v["other_net"], v["layer"]
    ia, ib = items_on(net, layer), items_on(other, layer)
    best = None
    for la, ga in ia:
        for lb, gb in ib:
            d = ga.distance(gb)
            if best is None or d < best[0]:
                pa, pb = nearest_points(ga, gb)
                best = (d, la, lb, (pa.x, pa.y), (pb.x, pb.y))
    d, la, lb, pa, pb = best
    fa, fb = fps_at(pa), fps_at(pb)
    shared = sorted(set(fa) & set(fb))
    rows.append(dict(net=net, other=other, layer=layer, spacing=round(d, 4),
                     required=v["required_mm"], a=la, b=lb,
                     at=[round(pa[0], 3), round(pa[1], 3)],
                     bt=[round(pb[0], 3), round(pb[1], 3)],
                     fp_a=fa, fp_b=fb, shared_fp=shared))
    print(f"{net:18s} <-> {other:18s} {layer:5s} {d:.4f} (need {v['required_mm']})")
    print(f"    A: {la:52s} @ ({pa[0]:.3f},{pa[1]:.3f}) fp={fa}")
    print(f"    B: {lb:52s} @ ({pb[0]:.3f},{pb[1]:.3f}) fp={fb}")
    print(f"    shared courtyard: {shared}")
Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\creep_located.json").write_text(
    json.dumps(rows, indent=1))
