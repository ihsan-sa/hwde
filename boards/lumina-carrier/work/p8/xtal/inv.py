"""Inventory the eth_xtal island: positions, pads, net copper, uuids, edge distances."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import route_cleanup as rc  # noqa: E402
import sexpdata  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
NETS = ["/eth/XI", "/eth/XO", "/eth/XO_XTAL"]
ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
OTHERS = ["U10", "J1", "D10", "U20", "L20", "D20", "U21", "L21", "U30", "C35",
          "R30", "R31", "R32", "R33", "R34", "R37", "R38"]

bg = geom.load_board(PCB)
bx1, by1, bx2, by2 = bg.outline.bounds
ORG = (bx1, by1)


def rel(x, y):
    return (round(x - ORG[0], 3), round(y - ORG[1], 3))


out = {"outline_bounds": [round(v, 3) for v in bg.outline.bounds],
       "origin": [round(v, 3) for v in ORG]}

# ---- footprint origins (from raw sexp, since geom keeps only pads) ----
root = sexpdata.loads(PCB.read_text(encoding="utf-8"))


def tok(x):
    return x.value() if isinstance(x, sexpdata.Symbol) else x


def kid(node, name):
    for c in node[1:]:
        if isinstance(c, list) and c and tok(c[0]) == name:
            return c
    return None


def kids(node, name):
    return [c for c in node[1:]
            if isinstance(c, list) and c and tok(c[0]) == name]


def nums(node):
    return [float(x) for x in node[1:] if isinstance(x, (int, float))]


def first_str(node):
    for x in node[1:]:
        v = tok(x)
        if isinstance(v, str):
            return v
    return None


fps = {}
for fp in kids(root, "footprint"):
    ref = None
    for prop in kids(fp, "property"):
        pv = [tok(x) for x in prop[1:]]
        if len(pv) >= 2 and pv[0] == "Reference":
            ref = pv[1]
            break
    if ref is None:
        continue
    at = nums(kid(fp, "at"))
    lay = first_str(kid(fp, "layer"))
    fps[ref] = {"at": [round(at[0], 4), round(at[1], 4)],
                "deg": round(at[2], 3) if len(at) > 2 else 0.0,
                "layer": lay,
                "fpid": first_str(fp) or tok(fp[1]),
                "locked": kid(fp, "locked") is not None}

out["footprints"] = {}
for ref in ISLAND + OTHERS:
    f = fps.get(ref)
    if f is None:
        out["footprints"][ref] = None
        continue
    pads = [p for p in bg.pads_of(ref=ref)]
    ent = dict(f)
    ent["at_rel"] = rel(*f["at"])
    ent["pads"] = [{"n": p.number, "net": p.net,
                    "c": [round(p.center[0], 4), round(p.center[1], 4)],
                    "c_rel": rel(*p.center),
                    "size": [round(p.size[0], 3), round(p.size[1], 3)],
                    "ang": round(p.angle, 2),
                    "layers": list(p.layers)} for p in pads]
    # distance to outline boundary
    ring = bg.outline.exterior
    if pads:
        ent["min_pad_center_to_edge"] = round(
            min(ring.distance(__import__("shapely.geometry",
                                         fromlist=["Point"]).Point(p.center))
                for p in pads), 4)
        ent["min_pad_copper_to_edge"] = round(
            min(ring.distance(p.poly) for p in pads), 4)
    out["footprints"][ref] = ent

# ---- net copper ----
segs, vias = rc.parse_items(PCB, bg.copper_layers)
out["nets"] = {}
tot_len = 0.0
tot_via = 0
for net in NETS:
    ns = [s for s in segs if s.net == net]
    nv = [v for v in vias if v.net == net]
    bylayer = {}
    for s in ns:
        bylayer.setdefault(s.layer, 0.0)
        bylayer[s.layer] += s.length
    total = sum(bylayer.values())
    tot_len += total
    tot_via += len(nv)
    out["nets"][net] = {
        "len_by_layer": {k: round(v, 3) for k, v in sorted(bylayer.items())},
        "total_mm": round(total, 3),
        "n_segs": len(ns), "n_vias": len(nv),
        "segs": [{"uuid": s.uuid, "layer": s.layer, "w": s.width,
                  "a": [round(s.a[0], 4), round(s.a[1], 4)],
                  "b": [round(s.b[0], 4), round(s.b[1], 4)],
                  "a_rel": rel(*s.a), "b_rel": rel(*s.b),
                  "len": round(s.length, 3)} for s in ns],
        "vias": [{"uuid": v.uuid, "at": [round(v.at[0], 4), round(v.at[1], 4)],
                  "at_rel": rel(*v.at), "size": v.size, "drill": v.drill,
                  "layers": list(v.layers)} for v in nv],
        "pads": [{"ref": p.ref, "n": p.number,
                  "c": [round(p.center[0], 4), round(p.center[1], 4)],
                  "c_rel": rel(*p.center), "layers": list(p.layers)}
                 for p in bg.pads_of(net=net)],
    }
out["totals"] = {"routed_mm": round(tot_len, 3), "vias": tot_via}

# ---- island-wide min distance to outline ----
ring = bg.outline.exterior
from shapely.geometry import Point  # noqa: E402
isl_pads = [p for r in ISLAND for p in bg.pads_of(ref=r)]
out["island_min_pad_center_to_edge"] = round(
    min(ring.distance(Point(p.center)) for p in isl_pads), 4)
out["island_min_pad_copper_to_edge"] = round(
    min(ring.distance(p.poly) for p in isl_pads), 4)
# island copper (tracks/vias on the 3 nets) to edge
isl_cu = [ring.distance(s.poly) for s in bg.tracks_of()
          if s.net in NETS] + [ring.distance(v.poly) for v in bg.vias_of()
                               if v.net in NETS]
out["island_min_track_to_edge"] = round(min(isl_cu), 4) if isl_cu else None

# ---- key distances ----


def padof(ref, num):
    for p in bg.pads_of(ref=ref):
        if p.number == str(num):
            return p
    return None


def pads_on_net(ref, net):
    return [p for p in bg.pads_of(ref=ref) if p.net == net]


dist = {}
u10_xi = [p for p in bg.pads_of(ref="U10") if p.net == "/eth/XI"]
u10_xo = [p for p in bg.pads_of(ref="U10") if p.net == "/eth/XO"]
for lbl, a_list, b_list in [
        ("R36_to_U10_XO", bg.pads_of(ref="R36"), u10_xo),
        ("R35_to_U10_XI", bg.pads_of(ref="R35"), u10_xi),
        ("C30_to_Y10", bg.pads_of(ref="C30"), bg.pads_of(ref="Y10")),
        ("C31_to_Y10", bg.pads_of(ref="C31"), bg.pads_of(ref="Y10")),
        ("Y10_to_U10", bg.pads_of(ref="Y10"), bg.pads_of(ref="U10")),
        ("Y10_to_J1", bg.pads_of(ref="Y10"), bg.pads_of(ref="J1")),
]:
    if a_list and b_list:
        dist[lbl] = round(min(math.dist(a.center, b.center)
                              for a in a_list for b in b_list), 4)
# origin-to-origin separations (place_metrics style is courtyard-based; report both)
for a, b in [("Y10", "J1"), ("Y10", "U20"), ("Y10", "U21"), ("Y10", "L20"),
             ("Y10", "L21"), ("Y10", "D20"), ("J1", "Y10"), ("J1", "D10")]:
    if a in fps and b in fps:
        dist[f"origin_{a}_{b}"] = round(math.dist(fps[a]["at"], fps[b]["at"]), 4)
out["distances"] = dist

print(json.dumps(out, indent=1))
