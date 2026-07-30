"""Audit 4: board-level silk graphics, pin-1 markers, part identities/heights, buck loop area."""
import json, sys, re
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts"))
import sexpdata
from lib import geom as G
from shapely.geometry import box, MultiPoint, LineString
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


# ---- 1. board-level graphics on silk / user layers ----
gl = []
for gname in ("gr_line", "gr_rect", "gr_poly", "gr_circle", "gr_arc", "gr_curve"):
    for g in kids(root, gname):
        ln = kid(g, "layer")
        lay = G._strs(ln)[0] if ln else None
        pts = []
        for tag in ("start", "end", "center", "mid"):
            nn = kid(g, tag)
            if nn:
                pts.append(G._nums(nn)[:2])
        if kid(g, "pts"):
            pts += [list(p) for p in G._pts(g)]
        if pts:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            gl.append({"type": gname, "layer": lay,
                       "bbox_rel": [round(min(xs)-ox,3), round(min(ys)-oy,3),
                                    round(max(xs)-ox,3), round(max(ys)-oy,3)]})
from collections import Counter
res["board_graphics_by_layer"] = dict(Counter(g["layer"] for g in gl))
res["board_silk_graphics"] = [g for g in gl if g["layer"] and "SilkS" in g["layer"]]

# ---- 2. pin-1 markers on J3/J4/J1/J2: any silk prim near pin 1 ----
for ref in ("J1", "J2", "J3", "J4", "U30", "U10", "U1", "U20", "U21", "U22",
            "D1", "D2", "D3", "D20", "D23", "C50", "C51", "C52", "C53", "C61"):
    for fp in kids(root, "footprint"):
        r = None
        for p in kids(fp, "property"):
            s = G._strs(p)
            if s and s[0] == "Reference":
                r = s[1] if len(s) > 1 else None
        if r != ref:
            continue
        at = kid(fp, "at")
        fx, fy = G._nums(at)[0], G._nums(at)[1]
        fang = G._nums(at)[2] if len(G._nums(at)) > 2 else 0.0
        prims = []
        for gname in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
            for g in kids(fp, gname):
                ln = kid(g, "layer")
                lay = G._strs(ln)[0] if ln else ""
                if "SilkS" not in lay:
                    continue
                pts = []
                for tag in ("start", "end", "center", "mid"):
                    nn = kid(g, tag)
                    if nn:
                        pts.append(G._nums(nn)[:2])
                if kid(g, "pts"):
                    pts += [list(p) for p in G._pts(g)]
                gp = [G._rot(a, b, fang) for a, b in pts]
                gp = [(fx + a, fy + b) for a, b in gp]
                prims.append({"type": gname, "n": len(gp),
                              "pts_rel": [[round(a-ox,3), round(b-oy,3)] for a, b in gp][:6]})
        p1 = [q for q in bg._pads if q.ref == ref and str(q.number) == "1"]
        p1c = [round(p1[0].center[0]-ox,3), round(p1[0].center[1]-oy,3)] if p1 else None
        # closest silk prim to pin 1
        best = None
        if p1:
            from shapely.geometry import Point
            pt = Point(p1[0].center)
            for pr in prims:
                for a, b in [(x[0]+ox, x[1]+oy) for x in pr["pts_rel"]]:
                    d = pt.distance(Point(a, b))
                    if best is None or d < best[0]:
                        best = (round(d, 3), pr["type"])
        res.setdefault("silk_near_pin1", {})[ref] = {
            "pin1_rel": p1c, "n_silk_prims": len(prims),
            "closest_silk_prim_to_pin1_mm": best[0] if best else None,
            "closest_type": best[1] if best else None,
            "value": (lambda: [G._strs(p)[1] for p in kids(fp, "property")
                               if G._strs(p) and G._strs(p)[0] == "Value"])()}

# ---- 3. footprint value/lib for every ref, plus footprint name (height proxy) ----
info = {}
for fp in kids(root, "footprint"):
    r = val = None
    for p in kids(fp, "property"):
        s = G._strs(p)
        if s and s[0] == "Reference":
            r = s[1] if len(s) > 1 else None
        if s and s[0] == "Value":
            val = s[1] if len(s) > 1 else None
    info[r] = {"fp": G._strs(fp)[0] if G._strs(fp) else None, "value": val}
res["fp_info"] = info

# ---- 4. buck commutation loops ----
def hull(refnums, label):
    pts = []
    for ref, num in refnums:
        for p in bg._pads:
            if p.ref == ref and (num is None or str(p.number) == str(num)):
                pts.append(p.poly.centroid)
    if len(pts) < 3:
        return {"label": label, "err": "too few pads", "n": len(pts)}
    h = MultiPoint(pts).convex_hull
    return {"label": label, "n_pads": len(pts), "hull_area_mm2": round(h.area, 3),
            "bounds_rel": [round(h.bounds[0]-ox,3), round(h.bounds[1]-oy,3),
                           round(h.bounds[2]-ox,3), round(h.bounds[3]-oy,3)]}

# identify VIN/SW/GND pads by net
def pads_on(ref, net):
    return [(p.ref, p.number) for p in bg._pads if p.ref == ref and p.net == net]

res["u20_pad_nets"] = {p.number: p.net for p in bg._pads if p.ref == "U20"}
res["u21_pad_nets"] = {p.number: p.net for p in bg._pads if p.ref == "U21"}
res["u22_pad_nets"] = {p.number: p.net for p in bg._pads if p.ref == "U22"}
for r in ("L20", "L21", "D20", "C50", "C51", "C61", "C55", "C56", "C57", "C58", "C52", "C53", "C54"):
    res.setdefault("cap_ind_nets", {})[r] = {p.number: p.net for p in bg._pads if p.ref == r}

# ---- 5. SW node geometry: routed length + area of SW copper (loop proxy) ----
for n in sorted(bg.nets):
    if n and re.search(r"SW|/pwr/", n) and "48" not in n:
        L = {l: round(sum(t.length for t in bg.tracks_of(net=n, layer=l)), 3)
             for l in bg.copper_layers if bg.tracks_of(net=n, layer=l)}
        if L:
            g = unary_union([bg.net_copper(n, l) for l in bg.copper_layers
                             if not bg.net_copper(n, l).is_empty])
            res.setdefault("pwr_nets", {})[n] = {
                "len": L, "vias": len(bg.vias_of(net=n)),
                "copper_area_mm2": round(g.area, 3),
                "bbox_rel": [round(g.bounds[0]-ox,3), round(g.bounds[1]-oy,3),
                             round(g.bounds[2]-ox,3), round(g.bounds[3]-oy,3)],
                "pads": [(p.ref, p.number) for p in bg.pads_of(net=n)]}

Path(OUT / "audit4.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: res[k] for k in ("board_graphics_by_layer", "board_silk_graphics",
                                      "u20_pad_nets", "u21_pad_nets", "cap_ind_nets")}, indent=1)[:6000])
