"""Audit 3: buck commutation loops, crystal, silk/fiducials, tall parts, HV hot spots."""
import json, sys, re
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts"))
import sexpdata
from lib import geom as G
from shapely.geometry import box, MultiPoint
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


# ---- net -> routed length per net, per layer ----
def netlen(net):
    tot = {}
    for lay in bg.copper_layers:
        L = sum(t.length for t in bg.tracks_of(net=net, layer=lay))
        if L:
            tot[lay] = round(L, 3)
    return tot


# ---- 1. all nets, so I can spot what exists ----
res["all_nets"] = sorted(n for n in bg.nets if n)

# ---- 2. crystal ----
xt = {}
for n in res["all_nets"]:
    if re.search(r"(XI|XO|XTAL|OSC|X1|X2)", n, re.I):
        xt[n] = {"len": netlen(n), "vias": len(bg.vias_of(net=n)),
                 "pads": [(p.ref, p.number, [round(p.center[0]-ox,3), round(p.center[1]-oy,3)])
                          for p in bg.pads_of(net=n)]}
res["crystal_nets"] = xt

# ---- 3. switch nodes / buck loops ----
sw = {}
for n in res["all_nets"]:
    if re.search(r"(SW|SWITCH|PH|LX)\b|/SW", n, re.I) and "SWD" not in n.upper():
        sw[n] = {"len": netlen(n), "vias": len(bg.vias_of(net=n)),
                 "pads": [(p.ref, p.number) for p in bg.pads_of(net=n)]}
res["switchnode_candidates"] = sw


def loop(ref_pads, label):
    """Convex-hull area of a set of (ref,padnum) pads -> proxy for loop area."""
    pts = []
    for ref, num in ref_pads:
        for p in bg._pads:
            if p.ref == ref and (num is None or str(p.number) == str(num)):
                pts.append(p.poly.centroid)
    if len(pts) < 3:
        return None
    h = MultiPoint(pts).convex_hull
    return {"label": label, "n_pads": len(pts), "hull_area_mm2": round(h.area, 3),
            "hull_bounds_rel": [round(h.bounds[0]-ox,3), round(h.bounds[1]-oy,3),
                                round(h.bounds[2]-ox,3), round(h.bounds[3]-oy,3)]}


# per-ref pad nets so I can identify VIN/SW/GND of each converter
for ref in ("U20", "U21", "U22", "L20", "L21", "D20", "C50", "C51", "C61", "C55",
            "C56", "C57", "C58", "C52", "C53", "C54", "U1", "Y10", "C30", "C31", "U10"):
    res.setdefault("pads_by_ref", {})[ref] = [
        {"num": p.number, "net": p.net,
         "rel": [round(p.center[0]-ox,3), round(p.center[1]-oy,3)], "size": list(p.size)}
        for p in sorted((q for q in bg._pads if q.ref == ref), key=lambda q: str(q.number).zfill(3))]

# ---- 4. SHIELD / LED nets ----
for n in ("/poe/SHIELD", "/poe/LED_Y_A", "/poe/LED_G_A", "/ETH_LED_LINK", "/ETH_LED_ACT"):
    if n in bg.nets:
        res.setdefault("net_detail", {})[n] = {
            "len": netlen(n), "vias": len(bg.vias_of(net=n)),
            "pads": [(p.ref, p.number, [round(p.center[0]-ox,3), round(p.center[1]-oy,3)])
                     for p in bg.pads_of(net=n)]}

# ---- 5. exact nearest points for the tight HV pairs ----
pairs = [("/poe/POE_TAP_A2", "/poe/LED_Y_A", "F.Cu"),
         ("/poe/POE_TAP_A1", "/poe/SHIELD", "F.Cu"),
         ("/poe/POE_TAP_B2", "/poe/SHIELD", "F.Cu"),
         ("/poe/POE_TAP_A1", "+3V3", "F.Cu"),
         ("/poe/POE_TAP_A1", "GND", "In1.Cu"),
         ("/poe/POE_TAP_A2", "+3V3", "In2.Cu"),
         ("/poe/POE_TAP_A1", "/poe/POE_TAP_A2", "F.Cu"),
         ("/poe/POE_TAP_B1", "/poe/POE_TAP_B2", "F.Cu")]
out = []
for a, b, lay in pairs:
    ga, gb = bg.net_copper(a, lay), bg.net_copper(b, lay)
    if ga.is_empty or gb.is_empty:
        continue
    pa, pb = nearest_points(ga, gb)
    out.append({"a": a, "b": b, "layer": lay, "dist_mm": round(ga.distance(gb), 4),
                "a_rel": [round(pa.x-ox,3), round(pa.y-oy,3)],
                "b_rel": [round(pb.x-ox,3), round(pb.y-oy,3)]})
res["hv_pair_locations"] = out

# ---- 6. silkscreen: pin-1 markers, polarity, fiducials, refdes on/off part ----
silk = []
for fp in kids(root, "footprint"):
    ref = None
    for p in kids(fp, "property"):
        s = G._strs(p)
        if s and s[0] == "Reference":
            ref = s[1] if len(s) > 1 else None
    at = kid(fp, "at")
    fx, fy = G._nums(at)[0], G._nums(at)[1]
    fang = G._nums(at)[2] if len(G._nums(at)) > 2 else 0.0
    lay = G._strs(kid(fp, "layer"))[0] if kid(fp, "layer") else None
    nsilk = 0
    for gname in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
        for g in kids(fp, gname):
            ln = kid(g, "layer")
            if ln and "SilkS" in G._strs(ln)[0]:
                nsilk += 1
    # reference text: hidden? on which layer?
    reftxt = None
    for t in kids(fp, "fp_text"):
        s = G._strs(t)
        if s and s[0] == "reference":
            tl = kid(t, "layer")
            hide = "hide" in [str(x) for x in G._strs(t)] or any(
                G._head(k) == "hide" for k in t[1:] if G._is_node(k))
            tat = kid(t, "at")
            reftxt = {"layer": G._strs(tl)[0] if tl else None, "hidden": bool(hide),
                      "at": G._nums(tat)[:2] if tat else None}
    silk.append({"ref": ref, "side": lay, "n_silk_prims": nsilk, "reftext": reftxt})
res["silk_per_fp"] = silk
res["fps_with_no_silk"] = [s["ref"] for s in silk if s["n_silk_prims"] == 0]
res["fps_with_hidden_ref"] = [s["ref"] for s in silk if s["reftext"] and s["reftext"]["hidden"]]

# board-level silk/graphics text
btext = []
for g in kids(root, "gr_text") + kids(root, "gr_text_box"):
    s = G._strs(g)
    ln = kid(g, "layer")
    at = kid(g, "at")
    btext.append({"text": s[0] if s else None, "layer": G._strs(ln)[0] if ln else None,
                  "rel": [round(G._nums(at)[0]-ox,3), round(G._nums(at)[1]-oy,3)] if at else None})
res["board_texts"] = btext

# ---- 7. 3D models / footprint libs for height inference ----
libs = {}
for fp in kids(root, "footprint"):
    ref = None
    for p in kids(fp, "property"):
        s = G._strs(p)
        if s and s[0] == "Reference":
            ref = s[1] if len(s) > 1 else None
    libs[ref] = {"lib": G._strs(fp)[0] if G._strs(fp) else None,
                 "models": [G._strs(m)[0] for m in kids(fp, "model") if G._strs(m)],
                 "attrs": [str(x) for k in kids(fp, "attr") for x in G._strs(k)]}
res["fp_libs"] = libs

# ---- 8. THT parts (pads spanning all copper with a drill) = hand-solder / tall risk ----
tht = {}
for p in bg._pads:
    if len(p.layers) == len(bg.copper_layers):
        tht.setdefault(p.ref, 0)
        tht[p.ref] += 1
res["tht_pad_counts"] = dict(sorted(tht.items()))

Path(OUT / "audit3.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: res[k] for k in ("crystal_nets", "hv_pair_locations", "net_detail",
                                      "fps_with_no_silk", "board_texts", "tht_pad_counts")}, indent=1))
