"""Post-rip clearance map: distance (mm) from each grid point to the nearest
FOREIGN copper on a layer, where foreign = everything except the three
oscillator nets and the five island footprints' own pads.

usage: clearmap.py LAYER X0 X1 Y0 Y1 [STEP]
digits: 0 = <0.25, 1 = <0.5, 2 = <0.75, 3 = <1.0, 4 = <1.5, 5 = <2, 6 = <3,
        7 = <4, 8 = <5, 9 = >=5 mm ; 'C' = inside another part's courtyard
"""
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import placelib  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
NETS = {"/eth/XI", "/eth/XO", "/eth/XO_XTAL"}
ISLAND = {"Y10", "C30", "C31", "R35", "R36"}

LAYER = sys.argv[1]
X0, X1, Y0, Y1 = (float(a) for a in sys.argv[2:6])
STEP = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5

bg = geom.load_board(PCB)
ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]

polys = []
for t in bg.tracks_of(layer=LAYER):
    if t.net not in NETS:
        polys.append(t.poly)
for v in bg.vias_of():
    if v.spans(LAYER) and v.net not in NETS:
        polys.append(v.poly)
for p in bg.pads_of(layer=LAYER):
    if p.ref not in ISLAND:
        polys.append(p.poly)
tree = STRtree(polys)

model = placelib.PlaceModel(PCB)
cyd = unary_union([f.extents_abs() for r, f in model.footprints.items()
                   if r not in ISLAND])

BANDS = [(0.25, "0"), (0.5, "1"), (0.75, "2"), (1.0, "3"), (1.5, "4"),
         (2.0, "5"), (3.0, "6"), (4.0, "7"), (5.0, "8")]
ring = bg.outline.exterior


def ch(d):
    for lim, c in BANDS:
        if d < lim:
            return c
    return "9"


nx = int(round((X1 - X0) / STEP))
ny = int(round((Y1 - Y0) / STEP))
print(__doc__.strip().splitlines()[-3].strip())
print("layer %s  region rel x[%.1f,%.1f] y[%.1f,%.1f] step %.2f"
      % (LAYER, X0, X1, Y0, Y1, STEP))
per = int(round(1.0 / STEP))
print("      " + "".join(
    (str(int(X0 + i * STEP) % 10) if per == 1 else
     (str(int(X0 + i * STEP) % 10) + " " * (per - 1)))
    for i in range(nx) if (i % per) == 0))
for j in range(ny + 1):
    y = Y0 + j * STEP
    row = []
    for i in range(nx + 1):
        x = X0 + i * STEP
        pt = Point(ox + x, oy + y)
        idx = tree.query_nearest(pt)
        d = min(polys[k].distance(pt) for k in (
            idx if hasattr(idx, "__iter__") else [idx]))
        c = ch(d)
        if cyd.contains(pt):
            c = "C" if c not in "01" else c
        de = ring.distance(pt)
        if not bg.outline.contains(pt):
            c = "X"
        row.append(c)
    print("%5.1f %s" % (y, "".join(row)))
