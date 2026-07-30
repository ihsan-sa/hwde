"""ASCII occupancy map of the region north of U10, board-relative mm."""
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import sexpdata  # noqa: E402
from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
import placelib  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
NETS = {"/eth/XI", "/eth/XO", "/eth/XO_XTAL"}
ISLAND = {"Y10", "C30", "C31", "R35", "R36"}

bg = geom.load_board(PCB)
ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]

X0, X1 = float(sys.argv[1]) if len(sys.argv) > 1 else 62.0, \
    float(sys.argv[2]) if len(sys.argv) > 2 else 88.0
Y0, Y1 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0, \
    float(sys.argv[4]) if len(sys.argv) > 4 else 20.0
STEP = 0.5

LAYER = "F.Cu"
foreign, isl, gnd = [], [], []
for t in bg.tracks_of(layer=LAYER):
    (isl if t.net in NETS else (gnd if t.net == "GND" else foreign)).append(t.poly)
for v in bg.vias_of():
    if v.spans(LAYER):
        (isl if v.net in NETS else
         (gnd if v.net == "GND" else foreign)).append(v.poly)
for p in bg.pads_of(layer=LAYER):
    if p.ref in ISLAND:
        isl.append(p.poly)
    elif p.net == "GND":
        gnd.append(p.poly)
    else:
        foreign.append(p.poly)
U_F = unary_union(foreign) if foreign else None
U_G = unary_union(gnd) if gnd else None
U_I = unary_union(isl) if isl else None

# courtyards of NON-island footprints
model = placelib.PlaceModel(PCB)
cyd = []
for ref, fp in model.footprints.items():
    if ref in ISLAND:
        continue
    cp = fp.extents_abs()
    if cp is not None and not cp.is_empty:
        cyd.append((ref, cp))
U_C = unary_union([c for _, c in cyd]) if cyd else None

ny = int((Y1 - Y0) / STEP)
nx = int((X1 - X0) / STEP)
print("region rel x[%.1f,%.1f] y[%.1f,%.1f] step %.2f   "
      "#=foreign F.Cu  g=GND F.Cu  o=osc-net F.Cu  c=courtyard  .=free"
      % (X0, X1, Y0, Y1, STEP))
hdr = "     " + "".join(
    str(int(X0 + i * STEP) % 10) if abs((X0 + i * STEP) % 1.0) < 1e-9 else " "
    for i in range(nx))
print(hdr)
for j in range(ny):
    y = Y0 + j * STEP
    row = []
    for i in range(nx):
        x = X0 + i * STEP
        cell = box(ox + x, oy + y, ox + x + STEP, oy + y + STEP)
        ch = "."
        if U_C is not None and U_C.intersects(cell):
            ch = "c"
        if U_I is not None and U_I.intersects(cell):
            ch = "o"
        if U_G is not None and U_G.intersects(cell):
            ch = "g"
        if U_F is not None and U_F.intersects(cell):
            ch = "#"
        row.append(ch)
    print("%5.1f%s" % (y, "".join(row)))
