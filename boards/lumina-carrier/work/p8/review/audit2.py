"""Audit 2: keepout vs rule areas, connectors vs ICD, tall parts, HV neighbours."""
import json, sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts"))
import sexpdata
from lib import geom as G
from shapely.geometry import box
from shapely.ops import unary_union

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
OUT = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "review"
bg = G.BoardGeom.from_file(PCB)
ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]
res = {}

# ---- 1. keepout vs authored rule areas ----
KO = box(109.58, 86.132, 119.58, 108.132)
ra_union = unary_union([r["outline"] for r in bg.rule_areas])
res["rule_area_union_area"] = round(ra_union.area, 3)
res["declared_keepout_area"] = round(KO.area, 3)
uncovered = KO.difference(ra_union)
res["keepout_area_NOT_covered_by_rule_area"] = round(uncovered.area, 3)
res["uncovered_bounds_rel"] = [[round(p.bounds[0]-ox,3), round(p.bounds[1]-oy,3),
                                round(p.bounds[2]-ox,3), round(p.bounds[3]-oy,3)]
                               for p in (uncovered.geoms if hasattr(uncovered,"geoms") else [uncovered])
                               if not p.is_empty]

per = {}
for lay in bg.copper_layers:
    cu = bg.layer_copper(lay)
    inside = cu.intersection(KO)
    per[lay] = {
        "copper_in_declared_keepout_mm2": round(inside.area, 4),
        "of_which_inside_a_rule_area_mm2": round(inside.intersection(ra_union).area, 4),
        "of_which_in_uncovered_sliver_mm2": round(inside.difference(ra_union).area, 4),
    }
res["keepout_breakdown"] = per

# which nets, and are they inside a rule area?
nets_in = {}
for lay in bg.copper_layers:
    for t in bg.tracks_of(layer=lay):
        i = t.poly.intersection(KO)
        if not i.is_empty:
            k = (t.net, lay)
            e = nets_in.setdefault(str(k), {"net": t.net, "layer": lay, "area": 0.0,
                                            "area_inside_rule_area": 0.0, "n": 0})
            e["area"] += i.area; e["n"] += 1
            e["area_inside_rule_area"] += i.intersection(ra_union).area
for v in bg._vias:
    i = v.poly.intersection(KO)
    if not i.is_empty:
        e = nets_in.setdefault("via:"+str(v.net)+str(v.at), {"net": v.net, "layer": "via "+"/".join(v.layers),
             "at_rel": [round(v.at[0]-ox,3), round(v.at[1]-oy,3)], "area": 0.0, "area_inside_rule_area": 0.0, "n": 0})
        e["area"] += i.area; e["n"] += 1
        e["area_inside_rule_area"] += i.intersection(ra_union).area
for p in bg._pads:
    i = p.poly.intersection(KO)
    if not i.is_empty:
        e = nets_in.setdefault("pad:"+str(p.ref)+"."+str(p.number), {"net": p.net, "layer": "pad "+"/".join(p.layers),
             "ref": p.ref, "num": p.number, "area": 0.0, "area_inside_rule_area": 0.0, "n": 0})
        e["area"] += i.area; e["n"] += 1
        e["area_inside_rule_area"] += i.intersection(ra_union).area
for e in nets_in.values():
    e["area"] = round(e["area"], 4); e["area_inside_rule_area"] = round(e["area_inside_rule_area"], 4)
res["keepout_occupants"] = sorted(nets_in.values(), key=lambda e: -e["area"])

# ---- 2. connector pin -> net maps ----
for ref in ("J3", "J4", "J1", "J2"):
    pads = sorted([p for p in bg._pads if p.ref == ref], key=lambda p: (str(p.number).zfill(3)))
    res[f"{ref}_pins"] = [{"num": p.number, "net": p.net,
                           "rel": [round(p.center[0]-ox,3), round(p.center[1]-oy,3)],
                           "size": list(p.size), "layers": len(p.layers)} for p in pads]

# ---- 3. bbox of every footprint pad-set (real extent) + refs of interest ----
byref = {}
for p in bg._pads:
    b = byref.setdefault(p.ref, [1e9, 1e9, -1e9, -1e9])
    x0, y0, x1, y1 = p.poly.bounds
    b[0] = min(b[0], x0); b[1] = min(b[1], y0); b[2] = max(b[2], x1); b[3] = max(b[3], y1)
res["pad_bbox_rel"] = {r: [round(b[0]-ox,3), round(b[1]-oy,3), round(b[2]-ox,3), round(b[3]-oy,3)]
                       for r, b in sorted(byref.items())}

# ---- 4. HV nets: nearest foreign net on the same outer layer (all layers) ----
HV = ["V48_RAW", "V48_RTN", "+48V_SW", "/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
      "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"]
allnets = sorted(bg.nets)
near = []
for lay in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
    hvg = {n: bg.net_copper(n, lay) for n in HV}
    hvg = {n: g for n, g in hvg.items() if not g.is_empty}
    for n, g in hvg.items():
        for o in allnets:
            if o in HV or o is None:
                continue
            og = bg.net_copper(o, lay)
            if og.is_empty:
                continue
            d = g.distance(og)
            if d < 0.635:
                pt = g.buffer(d + 1e-6).intersection(og)
                c = pt.centroid
                near.append({"layer": lay, "hv": n, "other": o, "dist_mm": round(d, 4),
                             "near_rel": [round(c.x-ox,3), round(c.y-oy,3)] if not pt.is_empty else None})
res["hv_vs_foreign_net_under_0p635mm"] = sorted(near, key=lambda e: e["dist_mm"])

# ---- 5. V48_RAW / +48V_SW closest point to board edge ----
edge = bg.outline.exterior
for n in ("V48_RAW", "+48V_SW", "V48_RTN"):
    parts = [bg.net_copper(n, l) for l in bg.copper_layers]
    parts = [p for p in parts if not p.is_empty]
    if not parts:
        continue
    g = unary_union(parts)
    d = g.distance(edge)
    from shapely.ops import nearest_points
    a, b = nearest_points(g, edge)
    res[f"{n}_closest_to_edge"] = {"dist_mm": round(d, 4),
                                   "copper_pt_rel": [round(a.x-ox,3), round(a.y-oy,3)],
                                   "edge_pt_rel": [round(b.x-ox,3), round(b.y-oy,3)],
                                   "per_layer": {l: round(bg.net_copper(n,l).distance(edge),4)
                                                 for l in bg.copper_layers
                                                 if not bg.net_copper(n,l).is_empty}}

Path(OUT / "audit2.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in ("pad_bbox_rel", "J1_pins", "J4_pins")}, indent=1))
