"""verify-reviewer independent geometry audit for LUM-CAR-A. Read-only."""
import json, math, sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts"))
import sexpdata
from lib import geom as G
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
OUT = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "review"

bg = G.BoardGeom.from_file(PCB)
root = sexpdata.loads(PCB.read_text(encoding="utf-8"))

res = {}
ox, oy, mx, my = bg.outline.bounds
res["outline_bbox"] = [round(v, 3) for v in (ox, oy, mx, my)]
res["outline_size"] = [round(mx - ox, 3), round(my - oy, 3)]
res["copper_layers"] = bg.copper_layers


def rel(x, y):
    return (round(x - ox, 3), round(y - oy, 3))


# ---------------- footprints ----------------
def kids(n, name):
    return [k for k in n[1:] if G._is_node(k) and G._head(k) == name]


def kid(n, name):
    k = kids(n, name)
    return k[0] if k else None


fps = []
for fp in kids(root, "footprint"):
    lib = G._strs(fp)[0] if G._strs(fp) else "?"
    at = kid(fp, "at")
    x, y = G._nums(at)[0], G._nums(at)[1]
    ang = G._nums(at)[2] if len(G._nums(at)) > 2 else 0.0
    ref = val = None
    layer = None
    ln = kid(fp, "layer")
    if ln:
        layer = G._strs(ln)[0]
    for p in kids(fp, "property"):
        s = G._strs(p)
        if s and s[0] == "Reference":
            ref = s[1] if len(s) > 1 else None
        if s and s[0] == "Value":
            val = s[1] if len(s) > 1 else None
    for t in kids(fp, "fp_text"):
        s = G._strs(t)
        if s and s[0] == "reference":
            ref = s[1] if len(s) > 1 else ref
        if s and s[0] == "value":
            val = s[1] if len(s) > 1 else val
    # courtyard polygon
    cy = []
    for gname in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
        for g in kids(fp, gname):
            lnode = kid(g, "layer")
            lay = G._strs(lnode)[0] if lnode else ""
            if "CrtYd" not in lay:
                continue
            for tag in ("start", "end", "center", "mid"):
                nn = kid(g, tag)
                if nn:
                    cy.append(G._nums(nn)[:2])
            pts = kid(g, "pts")
            if pts:
                cy += [list(p) for p in G._pts(g)]
    models = [G._strs(m)[0] for m in kids(fp, "model") if G._strs(m)]
    ent = {"ref": ref, "val": val, "lib": lib, "layer": layer,
           "at": [round(x, 3), round(y, 3)], "rel": list(rel(x, y)),
           "rot": ang, "models": models}
    if cy:
        cx = [c[0] for c in cy]
        cyy = [c[1] for c in cy]
        # rotate local courtyard to board frame
        pts = [G._rot(a, b, ang) for a, b in zip(cx, cyy)]
        gx = [x + a for a, b in pts]
        gy = [y + b for a, b in pts]
        ent["cy_bbox_abs"] = [round(min(gx), 3), round(min(gy), 3), round(max(gx), 3), round(max(gy), 3)]
        ent["cy_bbox_rel"] = [round(min(gx) - ox, 3), round(min(gy) - oy, 3),
                              round(max(gx) - ox, 3), round(max(gy) - oy, 3)]
    fps.append(ent)
res["n_footprints"] = len(fps)
res["footprints"] = sorted(fps, key=lambda e: (e["ref"] or "zz"))

# ---------------- antenna keepout ----------------
KO = (109.58, 86.132, 119.58, 108.132)  # constraints.json
ICD_KO = (ox + 88, oy + 25, ox + 100, oy + 55)  # ICD s7.6 antenna column
ko_poly = box(*KO)
icd_poly = box(*ICD_KO)
res["keepout_constraints_abs"] = list(KO)
res["keepout_constraints_rel"] = [KO[0] - ox, KO[1] - oy, KO[2] - ox, KO[3] - oy]
res["keepout_icd_abs"] = [round(v, 3) for v in ICD_KO]

ko = {}
for lay in bg.copper_layers:
    for name, poly in (("constraints", ko_poly), ("icd", icd_poly)):
        cu = bg.layer_copper(lay)
        inter = cu.intersection(poly) if not cu.is_empty else cu
        ko.setdefault(name, {})[lay] = round(inter.area, 4)
res["keepout_copper_area_mm2"] = ko

# what copper is in the ICD-wider zone (per item detail)
detail = []
for lay in bg.copper_layers:
    for t in bg.tracks_of(layer=lay):
        if t.poly.intersects(icd_poly):
            detail.append({"kind": "track", "layer": lay, "net": t.net,
                           "area_in_icd": round(t.poly.intersection(icd_poly).area, 4),
                           "in_constraints": t.poly.intersects(ko_poly)})
    for z in bg.zones_of(layer=lay):
        f = z.fill_on(lay)
        if not f.is_empty and f.intersects(icd_poly):
            detail.append({"kind": "zone", "layer": lay, "net": z.net,
                           "area_in_icd": round(f.intersection(icd_poly).area, 4),
                           "area_in_constraints": round(f.intersection(ko_poly).area, 4)})
for v in bg._vias:
    if v.poly.intersects(icd_poly):
        detail.append({"kind": "via", "net": v.net, "at": list(v.at),
                       "in_constraints": v.poly.intersects(ko_poly)})
for p in bg._pads:
    if p.poly.intersects(icd_poly):
        detail.append({"kind": "pad", "ref": p.ref, "net": p.net,
                       "area_in_icd": round(p.poly.intersection(icd_poly).area, 4),
                       "in_constraints": p.poly.intersects(ko_poly)})
res["icd_zone_copper_detail"] = detail

# rule areas (keepout zones actually authored in the pcb)
res["rule_areas"] = [
    {"name": ra.get("name"), "layers": list(ra.get("layers") or []),
     "bounds": [round(v, 3) for v in ra["outline"].bounds] if hasattr(ra.get("outline"), "bounds") else None,
     "bounds_rel": [round(ra["outline"].bounds[0] - ox, 3), round(ra["outline"].bounds[1] - oy, 3),
                    round(ra["outline"].bounds[2] - ox, 3), round(ra["outline"].bounds[3] - oy, 3)]
     if hasattr(ra.get("outline"), "bounds") else None,
     "keys": [k for k in ra if k != "outline"]}
    for ra in bg.rule_areas]

# ---------------- 48 V copper vs edge / holes ----------------
HV = ["V48_RAW", "V48_RTN", "+48V_SW", "/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
      "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"]
edge = bg.outline.exterior
hv_geo = {}
for n in HV:
    parts = []
    for lay in bg.copper_layers:
        c = bg.net_copper(n, lay)
        if not c.is_empty:
            parts.append(c)
    if parts:
        hv_geo[n] = unary_union(parts)
res["hv_nets_present"] = sorted(hv_geo)
res["hv_min_dist_to_board_edge_mm"] = {
    n: round(g.distance(edge), 4) for n, g in hv_geo.items()}

# mounting holes / NPTH / board locks: every pad with no net or hole-only
holes = []
for p in bg._pads:
    holes.append(p)
mh = [p for p in bg._pads if (p.net in (None, "") or p.ref and p.ref.startswith("H"))]
res["hole_pads"] = [{"ref": p.ref, "net": p.net, "at": [round(p.center[0], 3), round(p.center[1], 3)],
                     "rel": list(rel(p.center[0], p.center[1])), "layers": list(p.layers)}
                    for p in bg._pads if p.net in (None, "")]

# distance from each 48V net to each netless (unpotentialed) hole pad
netless = [p for p in bg._pads if p.net in (None, "")]
dist = []
for p in netless:
    for n, g in hv_geo.items():
        d = g.distance(p.poly)
        if d < 6.0:
            dist.append({"hole_ref": p.ref, "hole_at": [round(p.center[0], 3), round(p.center[1], 3)],
                         "hv_net": n, "dist_mm": round(d, 4)})
res["hv_to_netless_hole_lt6mm"] = sorted(dist, key=lambda d: d["dist_mm"])

Path(OUT / "audit1.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in
                  ("footprints", "icd_zone_copper_detail")}, indent=1))
