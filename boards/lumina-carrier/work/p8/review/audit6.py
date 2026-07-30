"""Audit 6: mounting-hole pattern vs ICD, hole-to-edge, HV-to-hole distances (all holes)."""
import json, sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts"))
from lib import geom as G
from shapely.ops import unary_union

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
OUT = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "review"
bg = G.BoardGeom.from_file(PCB)
ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]
edge = bg.outline.exterior
res = {}

holes = {}
for p in bg._pads:
    if p.ref and p.ref.startswith("H") and len(p.ref) <= 3:
        holes[p.ref] = p
res["holes"] = {r: {"rel": [round(p.center[0]-ox,3), round(p.center[1]-oy,3)],
                    "size": list(p.size), "net": p.net,
                    "hole_wall_to_board_edge_mm": round(p.poly.distance(edge), 4)}
                for r, p in sorted(holes.items())}
xs = sorted(set(round(p.center[0]-ox,2) for r, p in holes.items() if r in ("H1","H2","H3","H4")))
ys = sorted(set(round(p.center[1]-oy,2) for r, p in holes.items() if r in ("H1","H2","H3","H4")))
res["corner_hole_rectangle_mm"] = [round(xs[-1]-xs[0],3), round(ys[-1]-ys[0],3)] if len(xs) > 1 else None
res["corner_hole_inset_mm"] = [xs[0], ys[0]] if xs else None
res["icd_s7_1_says"] = {"inset_mm": 5, "rectangle_mm": [90, 70], "h5": [46, 74], "dia_mm": 3.2}

HV = ["V48_RAW", "V48_RTN", "+48V_SW", "/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
      "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"]
hvg = {}
for n in HV:
    parts = [bg.net_copper(n, l) for l in bg.copper_layers]
    parts = [p for p in parts if not p.is_empty]
    if parts:
        hvg[n] = unary_union(parts)
allhv = unary_union(list(hvg.values()))
res["min_dist_any_48V_copper_to_each_M3_hole_mm"] = {
    r: round(allhv.distance(p.poly), 4) for r, p in sorted(holes.items())}

# outline arcs -> corner radius
import sexpdata
root = sexpdata.loads(PCB.read_text(encoding="utf-8"))
arcs = []
for g in [k for k in root[1:] if G._is_node(k) and G._head(k) == "gr_arc"]:
    s = G._nums(G._kid(g, "start"))[:2]
    m = G._nums(G._kid(g, "mid"))[:2]
    e = G._nums(G._kid(g, "end"))[:2]
    import math
    # circumradius from 3 points
    ax, ay = s; bx, by = m; cx, cy = e
    d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d) < 1e-9:
        continue
    ux = ((ax**2+ay**2)*(by-cy)+(bx**2+by**2)*(cy-ay)+(cx**2+cy**2)*(ay-by))/d
    uy = ((ax**2+ay**2)*(cx-bx)+(bx**2+by**2)*(ax-cx)+(cx**2+cy**2)*(bx-ax))/d
    arcs.append(round(math.hypot(ax-ux, ay-uy), 3))
res["outline_arc_radii_mm"] = arcs

# ICD s7.2 frozen connector datums vs actual
icd = {"J3_pos1": [15.380, 77.270], "J3_even_row_y": 74.730,
       "J3_land": [14.11, 73.50, 31.89, 78.50],
       "J4_pos1": [57.030, 77.270], "J4_even_row_y": 74.730,
       "J4_land": [55.76, 73.50, 86.24, 78.50],
       "J1_body": [11.88, 0.00, 30.12, 21.74]}
act = {}
for ref in ("J3", "J4"):
    p1 = [p for p in bg._pads if p.ref == ref and str(p.number) == "1"][0]
    p2 = [p for p in bg._pads if p.ref == ref and str(p.number) == "2"][0]
    act[ref + "_pos1"] = [round(p1.center[0]-ox,3), round(p1.center[1]-oy,3)]
    act[ref + "_even_row_y"] = round(p2.center[1]-oy, 3)
res["icd_s7_2_frozen"] = icd
res["icd_s7_2_actual"] = act

# J1 body from silk/courtyard, correct KiCad transform (rot 180 -> sign-agnostic)
import math
for fp in [k for k in root[1:] if G._is_node(k) and G._head(k) == "footprint"]:
    r = None
    for p in [k for k in fp[1:] if G._is_node(k) and G._head(k) == "property"]:
        s = G._strs(p)
        if s and s[0] == "Reference":
            r = s[1] if len(s) > 1 else None
    if r != "J1":
        continue
    at = G._kid(fp, "at")
    fx, fy = G._nums(at)[0], G._nums(at)[1]
    ang = G._nums(at)[2] if len(G._nums(at)) > 2 else 0.0
    pts = []
    for gn in ("fp_line", "fp_rect", "fp_poly"):
        for g in [k for k in fp[1:] if G._is_node(k) and G._head(k) == gn]:
            ln = G._kid(g, "layer")
            if not ln or "CrtYd" not in G._strs(ln)[0]:
                continue
            for tag in ("start", "end"):
                nn = G._kid(g, tag)
                if nn:
                    pts.append(G._nums(nn)[:2])
    a = math.radians(90.0 if False else ang)
    tp = [(fx + (x*math.cos(-a) - y*math.sin(-a)) - ox,
           fy + (x*math.sin(-a) + y*math.cos(-a)) - oy) for x, y in pts]
    res["J1_courtyard_rel"] = [round(min(p[0] for p in tp),3), round(min(p[1] for p in tp),3),
                              round(max(p[0] for p in tp),3), round(max(p[1] for p in tp),3)]
    res["J1_rot"] = ang

# daughter RJ45 notch (6,0)-(36,26): does anything of J1 poke out?
notch = (6.0, 0.0, 36.0, 26.0)
res["notch"] = notch
res["J1_inside_notch"] = (res["J1_courtyard_rel"][0] >= notch[0] and
                          res["J1_courtyard_rel"][2] <= notch[2] and
                          res["J1_courtyard_rel"][3] <= notch[3])
# what other footprints intrude into the notch region (they'd be under the daughter's cut-away: fine)
# and which parts sit OUTSIDE the notch but are tall THT (fouling risk)
tht = {}
for p in bg._pads:
    if len(p.layers) == len(bg.copper_layers) and p.ref:
        tht.setdefault(p.ref, []).append(p)
res["tht_refs_outside_notch"] = sorted(
    r for r, ps in tht.items()
    if not (min(q.poly.bounds[0] for q in ps)-ox >= notch[0] and
            max(q.poly.bounds[2] for q in ps)-ox <= notch[2] and
            max(q.poly.bounds[3] for q in ps)-oy <= notch[3]))

Path(OUT / "audit6.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))
