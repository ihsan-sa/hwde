"""rf-de-20m P8 - 2-D resistive-sheet solve of the +40V bus: J101 -> L201.

Written for the P8 verify fix because check_current cannot see a pour's
REAL neck: pour_neck only tests a zone that contains >= 2 via attachments,
and it tests each zone separately, so a multi-branch bus poured as several
abutting rectangles is invisible to it.

Rasterises the +40V copper on F.Cu and B.Cu at 0.25 mm, ties the layers at
the net's vias, injects 5.96 A at J101.1 and draws it at L201.1, solves for
the potential, then reports the bus resistance and the per-cell linear
current density with its IPC-2152-equivalent conductor width and dT.

Usage: bus_solve.py [pcb]   (default: the workspace board)
"""
import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.sparse.csgraph as csg
sys.path.insert(0, r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts\lib")
import geom
from shapely.geometry import box
from shapely.prepared import prep

PCB = Path(sys.argv[1] if len(sys.argv) > 1
           else r"C:\dev\ai-ee3\boards\rf-de-20m\kicad\rf-de-20m.kicad_pcb")
BG = geom.BoardGeom.from_file(PCB)
OX, OY = BG.outline.bounds[0], BG.outline.bounds[1]

RES = 0.25
NET = "+40V"
I_TOT = 5.96
I_DECL = 7.0
RHO20 = 1.72e-8
T_CU = 100.0
RHO = RHO20 * (1 + 0.00393 * (T_CU - 20))
CU = BG.stackup.copper_thickness
X0, X1, Y0, Y1 = 0.0, 53.0, 0.0, 80.0
NX = int((X1 - X0) / RES)
NY = int((Y1 - Y0) / RES)
LAYERS = ["F.Cu", "B.Cu"]

masks = {}
for lay in LAYERS:
    cu = BG.net_copper(NET, lay)
    pc = prep(cu)
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
    ys, xs = np.nonzero(masks[lay])
    for j, i in zip(ys, xs):
        idx[k, j, i] = n
        n += 1

rows, cols, vals = [], [], []
def add(a, b, g):
    rows.append(a); cols.append(b); vals.append(-g)
    rows.append(b); cols.append(a); vals.append(-g)
    rows.append(a); cols.append(a); vals.append(g)
    rows.append(b); cols.append(b); vals.append(g)

for k, lay in enumerate(LAYERS):
    g_sq = CU[lay] * 1e-3 / RHO
    m = masks[lay]
    for j in range(NY):
        for i in range(NX - 1):
            if m[j, i] and m[j, i + 1]:
                add(idx[k, j, i], idx[k, j, i + 1], g_sq)
    for j in range(NY - 1):
        for i in range(NX):
            if m[j, i] and m[j + 1, i]:
                add(idx[k, j, i], idx[k, j + 1, i], g_sq)

G_VIA = 1.0 / (RHO * 1.6e-3 / (np.pi * 0.3e-3 * 25e-6))
nv = 0
for v in BG.vias_of(NET):
    i = int((v.at[0] - OX - X0) / RES)
    j = int((v.at[1] - OY - Y0) / RES)
    if 0 <= i < NX and 0 <= j < NY and idx[0, j, i] >= 0 and idx[1, j, i] >= 0:
        add(idx[0, j, i], idx[1, j, i], G_VIA)
        nv += 1

A = sp.coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr()
ncomp, lab = csg.connected_components(A, directed=False)

def pad_nodes(ref, num, layers=("F.Cu",)):
    out = []
    for p in BG.pads_of(ref=ref):
        if p.number != num:
            continue
        b = p.poly.bounds
        for j in range(max(0, int((b[1] - OY - Y0) / RES)), min(NY, int((b[3] - OY - Y0) / RES) + 1)):
            for i in range(max(0, int((b[0] - OX - X0) / RES)), min(NX, int((b[2] - OX - X0) / RES) + 1)):
                for k, lay in enumerate(LAYERS):
                    if lay in layers and lay in p.layers and idx[k, j, i] >= 0:
                        out.append(idx[k, j, i])
    return sorted(set(out))

src = pad_nodes("J101", "1")
snk = pad_nodes("L201", "1")
main = lab[snk[0]]
src = [s for s in src if lab[s] == main]
snk = [s for s in snk if lab[s] == main]
sel = np.nonzero(lab == main)[0]
print(f"F.Cu {masks['F.Cu'].sum()*RES*RES:.0f} mm2, B.Cu {masks['B.Cu'].sum()*RES*RES:.0f} mm2, "
      f"nodes {n}, components {ncomp}, main {len(sel)} nodes; vias tied {nv}")
print(f"source cells {len(src)}, sink cells {len(snk)}")

remap = -np.ones(n, dtype=np.int64)
remap[sel] = np.arange(len(sel))
As = A[sel][:, sel].tolil()
bs = np.zeros(len(sel))
bs[remap[src]] = I_TOT / len(src)
bs[remap[snk]] = -I_TOT / len(snk)
gnd = remap[snk[0]]
As[gnd, :] = 0
As[:, gnd] = 0
As[gnd, gnd] = 1.0
bs[gnd] = 0.0
Vs = spla.spsolve(As.tocsc(), bs)
V = np.zeros(n)
V[sel] = Vs
res_ok = np.allclose((A[sel][:, sel] @ Vs)[np.arange(len(sel)) != gnd],
                     np.array([I_TOT / len(src) if k in set(remap[src]) else
                               (-I_TOT / len(snk) if k in set(remap[snk]) else 0.0)
                               for k in range(len(sel))])[np.arange(len(sel)) != gnd],
                     atol=1e-9)
Vsrc = V[src].mean(); Vsnk = V[snk].mean()
R = (Vsrc - Vsnk) / I_TOT
print(f"KCL residual ok: {res_ok}")
print(f"bus resistance J101 -> L201 = {R*1e3:.3f} mOhm at {T_CU:.0f} C "
      f"-> {R*I_TOT*1e3:.1f} mV drop, {R*I_TOT**2*1e3:.0f} mW at {I_TOT} A")

IPC = [(0.0, 0.0), (0.5, 0.25), (1.0, 0.50), (2.0, 1.10), (3.0, 1.80),
       (5.0, 3.50), (7.0, 5.50), (10.0, 9.0)]
def width_for(cur):
    for (i0, w0), (i1, w1) in zip(IPC, IPC[1:]):
        if cur <= i1:
            return w0 + (cur - i0) / (i1 - i0) * (w1 - w0)
    (i0, w0), (i1, w1) = IPC[-2], IPC[-1]
    return w1 + (cur - i1) / (i1 - i0) * (w1 - w0)
K10_OUTER = I_DECL / width_for(I_DECL)

for k, lay in enumerate(LAYERS):
    m = masks[lay]
    g_sq = CU[lay] * 1e-3 / RHO
    k10 = K10_OUTER * (CU[lay] / 0.035)
    Vg = np.full((NY, NX), np.nan)
    ys, xs = np.nonzero(m)
    Vg[ys, xs] = V[idx[k, ys, xs]]
    jx = np.zeros((NY, NX)); jy = np.zeros((NY, NX))
    dv = np.diff(Vg, axis=1); ok = ~np.isnan(dv)
    jx[:, :-1][ok] = np.abs(dv[ok]) * g_sq / RES
    dv = np.diff(Vg, axis=0); ok = ~np.isnan(dv)
    jy[:-1, :][ok] = np.abs(dv[ok]) * g_sq / RES
    jj = np.hypot(jx, jy) * (I_DECL / I_TOT)
    jj[~m] = 0
    order = np.argsort(-jj, axis=None)
    print(f"\n{lay}: hot spots (declared {I_DECL} A; {k10:.3f} A/mm allowed at dT=10 C)")
    seen, shown = [], 0
    for f in order:
        j, i = np.unravel_index(f, jj.shape)
        if jj[j, i] <= 0:
            break
        x = X0 + (i + 0.5) * RES; y = Y0 + (j + 0.5) * RES
        if any(abs(x - sx) < 3 and abs(y - sy) < 3 for sx, sy in seen):
            continue
        seen.append((x, y))
        dt = 10.0 * (jj[j, i] / k10) ** 2.27
        print("   local (%6.2f,%6.2f)  J = %6.3f A/mm  equiv width %5.2f mm  dT ~ %5.1f C"
              % (x, y, jj[j, i], I_DECL / jj[j, i], dt))
        shown += 1
        if shown >= 10:
            break
