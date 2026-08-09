"""rf-de-20m P8 - branch currents and section-average current density.

Same solve as bus_solve.py, but reports how the bus current DIVIDES between
its parallel branches and the section-average A/mm across each named cut -
the honest ampacity number, where bus_solve.py's per-cell peaks include
corner crowding at 0.25 mm resolution.

Usage: bus_cuts.py [pcb]   (default: the workspace board)
"""
import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.sparse.csgraph as csg
sys.path.insert(0, r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts\lib")
import geom
from shapely.geometry import box, LineString
from shapely.prepared import prep

PCB = Path(sys.argv[1] if len(sys.argv) > 1
           else r"C:\dev\ai-ee3\boards\rf-de-20m\kicad\rf-de-20m.kicad_pcb")
BG = geom.BoardGeom.from_file(PCB)
OX, OY = BG.outline.bounds[0], BG.outline.bounds[1]
RES = 0.25
NET = "+40V"
I_TOT, I_DECL = 5.96, 7.0
RHO = 1.72e-8 * (1 + 0.00393 * 80)
CU = BG.stackup.copper_thickness
X0, X1, Y0, Y1 = 0.0, 53.0, 0.0, 80.0
NX, NY = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
LAYERS = ["F.Cu", "B.Cu"]
masks = {}
for lay in LAYERS:
    pc = prep(BG.net_copper(NET, lay))
    m = np.zeros((NY, NX), dtype=bool)
    for j in range(NY):
        y = OY + Y0 + (j + 0.5) * RES
        for i in range(NX):
            x = OX + X0 + (i + 0.5) * RES
            m[j, i] = pc.contains_properly(box(x - 1e-6, y - 1e-6, x + 1e-6, y + 1e-6))
    masks[lay] = m
idx = -np.ones((len(LAYERS), NY, NX), dtype=np.int64)
n = 0
for k, lay in enumerate(LAYERS):
    for j, i in zip(*np.nonzero(masks[lay])):
        idx[k, j, i] = n; n += 1
rows, cols, vals = [], [], []
def add(a, b, g):
    rows.extend([a, b, a, b]); cols.extend([b, a, a, b]); vals.extend([-g, -g, g, g])
for k, lay in enumerate(LAYERS):
    gsq = CU[lay] * 1e-3 / RHO
    m = masks[lay]; a = idx[k]
    for j, i in zip(*np.nonzero(m[:, :-1] & m[:, 1:])):
        add(a[j, i], a[j, i + 1], gsq)
    for j, i in zip(*np.nonzero(m[:-1, :] & m[1:, :])):
        add(a[j, i], a[j + 1, i], gsq)
G_VIA = 1.0 / (RHO * 1.6e-3 / (np.pi * 0.3e-3 * 25e-6))
for v in BG.vias_of(NET):
    i, j = int((v.at[0] - OX - X0) / RES), int((v.at[1] - OY - Y0) / RES)
    if 0 <= i < NX and 0 <= j < NY and idx[0, j, i] >= 0 and idx[1, j, i] >= 0:
        add(idx[0, j, i], idx[1, j, i], G_VIA)
A = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
_, lab = csg.connected_components(A, directed=False)
def pad_nodes(ref, num):
    out = []
    for p in BG.pads_of(ref=ref):
        if p.number != num:
            continue
        b = p.poly.bounds
        for j in range(max(0, int((b[1] - OY - Y0) / RES)), min(NY, int((b[3] - OY - Y0) / RES) + 1)):
            for i in range(max(0, int((b[0] - OX - X0) / RES)), min(NX, int((b[2] - OX - X0) / RES) + 1)):
                if "F.Cu" in p.layers and idx[0, j, i] >= 0:
                    out.append(idx[0, j, i])
    return sorted(set(out))
src, snk = pad_nodes("J101", "1"), pad_nodes("L201", "1")
main = lab[snk[0]]
src = [s for s in src if lab[s] == main]; snk = [s for s in snk if lab[s] == main]
sel = np.nonzero(lab == main)[0]
remap = -np.ones(n, dtype=np.int64); remap[sel] = np.arange(len(sel))
As = A[sel][:, sel].tolil(); bs = np.zeros(len(sel))
bs[remap[src]] = I_TOT / len(src); bs[remap[snk]] = -I_TOT / len(snk)
g = remap[snk[0]]; As[g, :] = 0; As[:, g] = 0; As[g, g] = 1.0; bs[g] = 0
V = np.zeros(n); V[sel] = spla.spsolve(As.tocsc(), bs)
R = (V[src].mean() - V[snk].mean()) / I_TOT
print(f"bus R = {R*1e3:.3f} mOhm @100C, {R*I_TOT*1e3:.1f} mV, {R*I_TOT**2*1e3:.0f} mW at {I_TOT} A")

CUTS = [
    ("west column -> strip aperture (x=16.4 local, vertical cut)", "v", 16.4, 28.0, 38.0),
    ("bus strip mid (x=30 local, vertical cut)", "v", 30.0, 28.0, 38.0),
    ("bus strip east of R104 lane (x=40 local)", "v", 40.0, 27.0, 38.0),
    ("R104 pinch (y=41.5 local, horizontal cut)", "h", 41.5, 40.0, 53.0),
    ("BUCK_SW crossing (y=56.2 local)", "h", 56.2, 40.0, 53.0),
    ("south block -> east column (y=50 local)", "h", 50.0, 38.0, 53.0),
]
IPC = [(0.0, 0.0), (0.5, 0.25), (1.0, 0.50), (2.0, 1.10), (3.0, 1.80), (5.0, 3.50), (7.0, 5.50), (10.0, 9.0)]
def wf(c):
    for (i0, w0), (i1, w1) in zip(IPC, IPC[1:]):
        if c <= i1:
            return w0 + (c - i0) / (i1 - i0) * (w1 - w0)
    return IPC[-1][1]
K10 = I_DECL / wf(I_DECL)
print("\ncut                                                   width  I(decl 7A)  A/mm   dT(C)")
for name, ax, t, b0, b1 in CUTS:
    # current crossing the cut on F.Cu (sum of edge currents through it)
    gsq = CU["F.Cu"] * 1e-3 / RHO
    m = masks["F.Cu"]
    I = 0.0
    width = 0.0
    if ax == "v":
        i = int((t - X0) / RES)
        for j in range(int((b0 - Y0) / RES), int((b1 - Y0) / RES)):
            if m[j, i] and m[j, i + 1]:
                I += (V[idx[0, j, i]] - V[idx[0, j, i + 1]]) * gsq
                width += RES
    else:
        j = int((t - Y0) / RES)
        for i in range(int((b0 - X0) / RES), int((b1 - X0) / RES)):
            if m[j, i] and m[j + 1, i]:
                I += (V[idx[0, j, i]] - V[idx[0, j + 1, i]]) * gsq
                width += RES
    Id = abs(I) * I_DECL / I_TOT
    if width > 0 and Id > 1e-6:
        dens = Id / width
        print("%-52s %6.2f %8.2f A %7.3f %7.1f" % (name, width, Id, dens, 10.0 * (dens / K10) ** 2.27))
    else:
        print("%-52s %6.2f  (no net flow)" % (name, width))
