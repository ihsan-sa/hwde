"""Per-power-net: classify every undersized segment as TRUNK vs BRANCH-STUB,
and measure the max width it could be widened to without breaking clearance.

TRUNK  = lies on a shortest path from the net's source pad to a non-decoupling
         load pad -> must carry the full rail budget.
STUB   = only reachable through a load/decoupling pad -> carries that branch.

Max widenable width for a segment: 2 * (min distance from its centreline to
foreign copper on the same layer, minus the required clearance).
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8")
import geom  # noqa
import check_current  # noqa
from shapely.ops import unary_union  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
CONS = json.loads(Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\constraints.json").read_text())
bg = geom.load_board(PCB)

# clearance floor per net (DRU): 48 V nets 0.635, everything else 0.2
HV = {"V48_RAW", "V48_RTN", "+48V_SW"}
GEN_CLR = 0.2


def clr_for(net_a, net_b):
    if net_a in HV or net_b in HV:
        return 0.635
    return GEN_CLR


DECOUP = {a["cap"] for a in json.loads(
    Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\decoupling.json").read_text())["associations"]}

out = {}
for entry in CONS["power"]:
    net = entry["net"]
    budget = float(entry["current_a"])
    dt = float(entry.get("dt_c", 10))
    cu = bg.stackup.copper_thickness
    tracks = bg.tracks_of(net)
    pads = bg.pads_of(net)
    # foreign copper per layer (all other nets, incl. zones)
    rows = []
    for layer in sorted({t.layer for t in tracks}):
        req = check_current.required_width_mm(budget, dt, cu[layer])
        others = []
        for onet in bg.nets:
            if not onet or onet == net:
                continue
            c = bg.net_copper(onet, layer)
            if not c.is_empty:
                others.append((onet, c))
        for t in [x for x in tracks if x.layer == layer]:
            if t.width + 1e-3 >= req:
                continue
            # room: nearest foreign copper to the centreline
            best = (9e9, None)
            for onet, c in others:
                d = c.distance(t.shape)
                if d < best[0]:
                    best = (d, onet)
            d, onet = best
            maxw = 2.0 * (d - clr_for(net, onet)) if onet else 9e9
            # endpoints on pads?
            ep = []
            for pt in (t.shape.coords[0], t.shape.coords[-1]):
                hits = [f"{p.ref}-{p.number}" for p in pads
                        if layer in p.layers and p.poly.buffer(1e-3).contains(geom.Point(pt))]
                ep.append(hits)
            rows.append(dict(layer=layer, w=round(t.width, 3), req=round(req, 3),
                             length=round(t.length, 3),
                             start=[round(v, 3) for v in t.shape.coords[0]],
                             end=[round(v, 3) for v in t.shape.coords[-1]],
                             nearest=onet, gap=round(d, 4),
                             maxw=round(maxw, 3), pads=ep))
    out[net] = dict(budget=budget, undersized=len(rows), rows=rows)
    print(f"=== {net}  budget {budget} A  undersized {len(rows)}")
    hist = defaultdict(int)
    for r in rows:
        ok = "WIDENABLE" if r["maxw"] + 1e-3 >= r["req"] else "BLOCKED"
        hist[(ok, r["nearest"])] += 1
    for k, v in sorted(hist.items(), key=lambda x: -x[1]):
        print("   ", v, k)
Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\cur_rows.json").write_text(json.dumps(out, indent=1))
