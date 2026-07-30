"""Audit 5: settle U30 antenna geometry and courtyard transform; measure antenna-area copper."""
import json, sys, math
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts"))
import sexpdata
from lib import geom as G
from shapely.geometry import box, Polygon
from shapely.ops import unary_union, nearest_points

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
OUT = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "review"
bg = G.BoardGeom.from_file(PCB)
ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]
root = sexpdata.loads(PCB.read_text(encoding="utf-8"))
res = {}


def kids(n, name):
    return [k for k in n[1:] if G._is_node(k) and G._head(k) == name]


def kid(n, name):
    k = kids(n, name)
    return k[0] if k else None


fpU30 = None
for fp in kids(root, "footprint"):
    for p in kids(fp, "property"):
        s = G._strs(p)
        if s and s[0] == "Reference" and len(s) > 1 and s[1] == "U30":
            fpU30 = fp
at = kid(fpU30, "at")
fx, fy = G._nums(at)[0], G._nums(at)[1]
fang = G._nums(at)[2] if len(G._nums(at)) > 2 else 0.0
res["U30_at_abs"] = [fx, fy]
res["U30_at_rel"] = [round(fx - ox, 3), round(fy - oy, 3)]
res["U30_rot"] = fang

# graphics per layer, transformed both ways
def xf_geom(x, y, ang, sign):
    a = math.radians(sign * ang)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


layers_seen = {}
for gname in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
    for g in kids(fpU30, gname):
        ln = kid(g, "layer")
        lay = G._strs(ln)[0] if ln else "?"
        pts = []
        for tag in ("start", "end", "center", "mid"):
            nn = kid(g, tag)
            if nn:
                pts.append(G._nums(nn)[:2])
        if kid(g, "pts"):
            pts += [list(p) for p in G._pts(g)]
        e = layers_seen.setdefault(lay, {"local": [], "n": 0})
        e["local"] += pts
        e["n"] += 1

out = {}
for lay, e in layers_seen.items():
    loc = e["local"]
    row = {"n_prims": e["n"],
           "local_bbox": [round(min(p[0] for p in loc), 3), round(min(p[1] for p in loc), 3),
                          round(max(p[0] for p in loc), 3), round(max(p[1] for p in loc), 3)]}
    for sign, tag in ((+1, "rot_plus"), (-1, "rot_minus")):
        g = [xf_geom(a, b, fang, sign) for a, b in loc]
        g = [(fx + a - ox, fy + b - oy) for a, b in g]
        row[tag + "_bbox_rel"] = [round(min(p[0] for p in g), 3), round(min(p[1] for p in g), 3),
                                  round(max(p[0] for p in g), 3), round(max(p[1] for p in g), 3)]
    out[lay] = row
res["U30_graphics"] = out

# pads (geom's own, trusted) in LOCAL frame too
pads = [p for p in bg._pads if p.ref == "U30"]
res["U30_pad_bbox_rel"] = [round(min(p.poly.bounds[0] for p in pads) - ox, 3),
                           round(min(p.poly.bounds[1] for p in pads) - oy, 3),
                           round(max(p.poly.bounds[2] for p in pads) - ox, 3),
                           round(max(p.poly.bounds[3] for p in pads) - oy, 3)]
res["U30_pin1_rel"] = [[round(p.center[0]-ox,3), round(p.center[1]-oy,3)]
                       for p in pads if str(p.number) == "1"]
res["U30_pin40_rel"] = [[round(p.center[0]-ox,3), round(p.center[1]-oy,3)]
                        for p in pads if str(p.number) == "40"]
# raw local pad positions from the file
rawpads = []
for p in kids(fpU30, "pad"):
    num = G._strs(p)[0] if G._strs(p) else None
    pat = kid(p, "at")
    rawpads.append((num, G._nums(pat)[:2]))
res["U30_pad_local_bbox"] = [round(min(a[1][0] for a in rawpads), 3), round(min(a[1][1] for a in rawpads), 3),
                             round(max(a[1][0] for a in rawpads), 3), round(max(a[1][1] for a in rawpads), 3)]
res["U30_pin1_local"] = [a[1] for a in rawpads if a[0] == "1"]
res["U30_pin40_local"] = [a[1] for a in rawpads if a[0] == "40"]

# ---- derive the Antenna Area from the datasheet rule and measure copper ----
# datasheet: module 18 x 25.5; antenna area = 18 x 6 at the pin-1/pin-40 end;
# 7.49 mm from module antenna edge to the near edge of the first pads.
p1 = [p for p in pads if str(p.number) == "1"][0]
p40 = [p for p in pads if str(p.number) == "40"][0]
res["p1_bounds_rel"] = [round(v, 3) for v in
                        (p1.poly.bounds[0]-ox, p1.poly.bounds[1]-oy, p1.poly.bounds[2]-ox, p1.poly.bounds[3]-oy)]
res["p40_bounds_rel"] = [round(v, 3) for v in
                         (p40.poly.bounds[0]-ox, p40.poly.bounds[1]-oy, p40.poly.bounds[2]-ox, p40.poly.bounds[3]-oy)]
# antenna end is +x (pin1 at max x). module antenna edge:
pad_start_x = max(p1.poly.bounds[2], p40.poly.bounds[2])   # abs
mod_edge_x = pad_start_x + 7.49
ant = box(mod_edge_x - 6.0, min(p.poly.bounds[1] for p in pads),
          mod_edge_x, max(p.poly.bounds[3] for p in pads))
res["derived_module_antenna_edge_x_rel"] = round(mod_edge_x - ox, 3)
res["derived_antenna_area_rel"] = [round(ant.bounds[0]-ox,3), round(ant.bounds[1]-oy,3),
                                   round(ant.bounds[2]-ox,3), round(ant.bounds[3]-oy,3)]
res["board_right_edge_rel"] = round(bg.outline.bounds[2]-ox, 3)
res["antenna_area_overhangs_board_by_mm"] = round(ant.bounds[2] - bg.outline.bounds[2], 3)

cu = {}
for lay in bg.copper_layers:
    c = bg.layer_copper(lay)
    inter = c.intersection(ant)
    d = c.distance(ant) if inter.is_empty else 0.0
    cu[lay] = {"copper_in_antenna_area_mm2": round(inter.area, 4),
               "nearest_copper_to_antenna_area_mm": round(d, 4)}
res["antenna_area_copper"] = cu

# nearest copper item to the antenna area, per layer, with identity
ident = []
for lay in bg.copper_layers:
    best = None
    for t in bg.tracks_of(layer=lay):
        d = t.poly.distance(ant)
        if best is None or d < best[0]:
            best = (d, "track", t.net)
    for v in bg._vias:
        if lay in v.layers:
            d = v.poly.distance(ant)
            if best is None or d < best[0]:
                best = (d, "via", v.net)
    for p in bg._pads:
        if lay in p.layers:
            d = p.poly.distance(ant)
            if best is None or d < best[0]:
                best = (d, "pad " + str(p.ref) + "." + str(p.number), p.net)
    for z in bg.zones_of(layer=lay):
        f = z.fill_on(lay)
        if not f.is_empty:
            d = f.distance(ant)
            if best is None or d < best[0]:
                best = (d, "zone", z.net)
    ident.append({"layer": lay, "dist_mm": round(best[0], 4), "what": best[1], "net": best[2]})
res["nearest_copper_to_antenna_area"] = ident

# ---- also: the two 4-layer vias in the declared keepout: distance to antenna area ----
for v in bg._vias:
    if v.poly.intersects(box(109.58, 86.132, 119.58, 108.132)):
        res.setdefault("keepout_vias", []).append(
            {"net": v.net, "at_rel": [round(v.at[0]-ox,3), round(v.at[1]-oy,3)],
             "dia": v.diameter, "drill": v.drill, "layers": list(v.layers),
             "dist_to_antenna_area_mm": round(v.poly.distance(ant), 4)})

Path(OUT / "audit5.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))
