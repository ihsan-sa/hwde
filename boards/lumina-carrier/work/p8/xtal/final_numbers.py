"""Exact before/after numbers for the eth_xtal collapse report."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
WORK = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "xtal"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import route_cleanup as rc  # noqa: E402

NETS = ["/eth/XI", "/eth/XO", "/eth/XO_XTAL"]
ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
PAIRS = [("R36", "1", "U10", "31", "R36.1(XO) -> U10.31 XO driver pin"),
         ("R35", "1", "U10", "30", "R35.1(XI) -> U10.30 XI pin"),
         ("C30", "1", "Y10", "1", "C30.1 -> Y10.1  (XI load cap to its pin)"),
         ("C31", "1", "Y10", "3", "C31.1 -> Y10.3  (XO_XTAL load cap to pin)"),
         ("R36", "2", "Y10", "3", "R36.2 -> Y10.3  (series R to crystal)")]


def net_path_len(bg, net, a, b, tol=0.02):
    """Shortest copper path a->b over track endpoints + via co-location."""
    segs, vias = rc.parse_items(bg.path, bg.copper_layers)
    segs = [s for s in segs if s.net == net]
    vias = [v for v in vias if v.net == net]
    nodes, idx = [], {}

    def nid(p, layer):
        for i, (q, la) in enumerate(nodes):
            if la == layer and math.dist(q, p) <= tol:
                return i
        nodes.append((p, layer))
        return len(nodes) - 1
    edges = []
    for s in segs:
        i, j = nid(s.a, s.layer), nid(s.b, s.layer)
        edges.append((i, j, s.length))
    for v in vias:
        ids = [nid(v.at, la) for la in v.layers]
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                edges.append((ids[x], ids[y], 0.0))
    # pads: bridge every node inside the pad polygon
    for p in bg.pads_of(net=net):
        grp = [i for i, (q, la) in enumerate(nodes)
               if la in p.layers and p.poly.buffer(tol).contains(
                   geom.Point(q) if hasattr(geom, "Point") else None) is None]
    src = [i for i, (q, la) in enumerate(nodes) if math.dist(q, a) <= 0.35]
    dst = [i for i, (q, la) in enumerate(nodes) if math.dist(q, b) <= 0.35]
    if not src or not dst:
        return None
    INF = float("inf")
    dist = {i: INF for i in range(len(nodes))}
    for i in src:
        dist[i] = 0.0
    adj = {}
    for i, j, w in edges:
        adj.setdefault(i, []).append((j, w))
        adj.setdefault(j, []).append((i, w))
    import heapq
    pq = [(0.0, i) for i in src]
    heapq.heapify(pq)
    seen = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        for v, w in adj.get(u, []):
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(pq, (dist[v], v))
    best = min(dist[i] for i in dst)
    return None if best == INF else round(best, 3)


out = {}
for tag, pcb in (("before", WORK / "pre_xtal.kicad_pcb"),
                 ("after", ROOT / "boards" / "lumina-carrier" / "kicad"
                  / "lumina-carrier.kicad_pcb")):
    bg = geom.load_board(pcb)
    ox, oy = bg.outline.bounds[0], bg.outline.bounds[1]
    ring = bg.outline.exterior
    pads = {(p.ref, p.number): p for p in bg.pads_of()}
    ent = {"pad_pairs": {}, "nets": {}, "edge": {}}
    for ra, na, rb, nb, lbl in PAIRS:
        A, B = pads.get((ra, na)), pads.get((rb, nb))
        if A and B:
            ent["pad_pairs"][lbl] = {
                "centre_mm": round(math.dist(A.center, B.center), 4),
                "copper_mm": round(A.poly.distance(B.poly), 4)}
    segs, vias = rc.parse_items(pcb, bg.copper_layers)
    tot, tv = 0.0, 0
    for net in NETS:
        by = {}
        for s in segs:
            if s.net == net:
                by[s.layer] = by.get(s.layer, 0.0) + s.length
        nv = len([v for v in vias if v.net == net])
        ent["nets"][net] = {"by_layer": {k: round(v, 3)
                                        for k, v in sorted(by.items())},
                            "total_mm": round(sum(by.values()), 3),
                            "vias": nv}
        tot += sum(by.values())
        tv += nv
    ent["total_mm"] = round(tot, 3)
    ent["total_vias"] = tv
    # island (parts + their three nets' copper) to outline
    cu = [ring.distance(p.poly) for r in ISLAND for p in bg.pads_of(ref=r)]
    cu += [ring.distance(t.poly) for t in bg.tracks_of() if t.net in NETS]
    cu += [ring.distance(v.poly) for v in bg.vias_of() if v.net in NETS]
    ent["edge"]["min_island_copper_to_outline_mm"] = round(min(cu), 4)
    ent["edge"]["min_island_pad_copper_to_outline_mm"] = round(
        min(ring.distance(p.poly) for r in ISLAND for p in bg.pads_of(ref=r)), 4)
    # routed trace length from the XO driver pin to R36 pad 1
    A, B = pads.get(("U10", "31")), pads.get(("R36", "1"))
    if A and B:
        ent["routed_xo_driver_to_R36_mm"] = net_path_len(
            bg, "/eth/XO", A.center, B.center)
    out[tag] = ent
print(json.dumps(out, indent=1))
