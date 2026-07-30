"""Feasibility map for placing one island part at grid positions.

Legal = (a) every pad polygon >= CLR from foreign F.Cu copper (foreign =
all copper except the 3 oscillator nets and the 5 island parts' own pads),
(b) footprint extents (pads+0.25) do not overlap any other footprint's
extents, (c) extents inside the outline and >= EDGE mm from it.

usage: feas.py REF DEG X0 X1 Y0 Y1 [STEP] [CLR] [EDGE]
'.' legal   'c' courtyard overlap   'x' clearance fail   'e' edge/outline fail
"""
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import placelib  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
NETS = {"/eth/XI", "/eth/XO", "/eth/XO_XTAL"}
ISLAND = {"Y10", "C30", "C31", "R35", "R36"}

bg = geom.load_board(PCB)
model = placelib.PlaceModel(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]

_foreign = {}
_tree = {}


def foreign(layer):
    if layer not in _foreign:
        polys = []
        for t in bg.tracks_of(layer=layer):
            if t.net not in NETS:
                polys.append(t.poly)
        for v in bg.vias_of():
            if v.spans(layer) and v.net not in NETS:
                polys.append(v.poly)
        for p in bg.pads_of(layer=layer):
            if p.ref not in ISLAND:
                polys.append(p.poly)
        _foreign[layer] = polys
        _tree[layer] = STRtree(polys)
    return _foreign[layer], _tree[layer]


OTHER_EXT = unary_union([f.extents_abs() for r, f in model.footprints.items()
                         if r not in ISLAND])


def part_geo(ref, deg, x, y, side=None):
    """(pad polys, extents poly) for footprint `ref` placed at abs x,y / deg."""
    f = model.footprints[ref]
    sd = side or f.side
    pads = []
    for p in f.pads:
        lx, ly = p.local
        # pcbnew: abs = pos + R(-deg).local  (geom._rot convention)
        pol = box(lx - p.size[0] / 2, ly - p.size[1] / 2,
                  lx + p.size[0] / 2, ly + p.size[1] / 2)
        pol = affinity.rotate(pol, -deg, origin=(0, 0))
        pads.append((p.number, p.net, affinity.translate(pol, x, y)))
    ext = affinity.rotate(f.extents_local(), -deg, origin=(0, 0))
    ext = affinity.translate(ext, x, y)
    return pads, ext


def legal(ref, deg, x, y, clr, edge, layer="F.Cu"):
    pads, ext = part_geo(ref, deg, x, y)
    if not bg.outline.contains(ext):
        return "e"
    if bg.outline.exterior.distance(ext) < edge:
        return "e"
    if OTHER_EXT.intersects(ext):
        return "c"
    polys, tree = foreign(layer)
    for _n, _net, pol in pads:
        for k in tree.query(pol.buffer(clr)):
            if polys[k].distance(pol) < clr:
                return "x"
    return "."


if __name__ == "__main__":
    REF, DEG = sys.argv[1], float(sys.argv[2])
    X0, X1, Y0, Y1 = (float(a) for a in sys.argv[3:7])
    STEP = float(sys.argv[7]) if len(sys.argv) > 7 else 0.25
    CLR = float(sys.argv[8]) if len(sys.argv) > 8 else 0.25
    EDGE = float(sys.argv[9]) if len(sys.argv) > 9 else 3.0
    nx = int(round((X1 - X0) / STEP))
    ny = int(round((Y1 - Y0) / STEP))
    print("%s deg %g  x[%.2f,%.2f] y[%.2f,%.2f] step %.2f clr %.2f edge %.2f"
          % (REF, DEG, X0, X1, Y0, Y1, STEP, CLR, EDGE))
    per = int(round(1.0 / STEP))
    print("      " + "".join((str(int(X0 + i * STEP) % 10) + " " * (per - 1))
                             for i in range(nx + 1) if i % per == 0))
    for j in range(ny + 1):
        y = Y0 + j * STEP
        row = "".join(legal(REF, DEG, OX + X0 + i * STEP, OY + y, CLR, EDGE)
                      for i in range(nx + 1))
        print("%5.2f %s" % (y, row))
