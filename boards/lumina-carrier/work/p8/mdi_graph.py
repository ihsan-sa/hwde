"""Analyse the MDI pair net graphs: components, terminals, true path lengths."""
import math
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
import check_diffpair as cd  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
bg = geom.load_board(PCB)

NETS = ["/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"]


def comps(adj):
    seen = set()
    out = []
    for nd in adj:
        if nd in seen:
            continue
        stack = [nd]
        c = set()
        while stack:
            u = stack.pop()
            if u in c:
                continue
            c.add(u)
            for v, w in adj.get(u, ()):
                if v not in c:
                    stack.append(v)
        seen |= c
        out.append(c)
    return out


for net in NETS:
    tks = bg.tracks_of(net)
    total = sum(t.length for t in tks)
    adj = cd.net_graph(bg, net)
    cc = comps(adj)
    print("=" * 70)
    print(f"{net}: {len(tks)} segs, total {total:.3f} mm, "
          f"{len(adj)} nodes, {len(cc)} components, vias {len(bg.vias_of(net))}")
    # per-layer
    from collections import Counter
    print("   layers:", dict(Counter(t.layer for t in tks)))
    print("   len by layer:", {l: round(sum(t.length for t in tks if t.layer == l), 3)
                               for l in set(t.layer for t in tks)})
    pads = bg.pads_of(net)
    print(f"   pads ({len(pads)}):")
    for p in pads:
        nd = cd.nearest_node(adj, p.center)
        ci = next((i for i, c in enumerate(cc) if nd in c), None) if nd else None
        d = math.hypot(nd[0] - p.center[0], nd[1] - p.center[1]) if nd else None
        print(f"     {p.ref}-{p.number} at ({p.center[0]:.3f},{p.center[1]:.3f}) "
              f"layers={p.layers if len(p.layers) < 4 else 'thru'} "
              f"nearest_node={nd} d={None if d is None else round(d, 3)} comp={ci}")
    for i, c in enumerate(cc):
        seg_len = 0.0
        for t in tks:
            a = cd._node(t.shape.coords[0])
            if a in c:
                seg_len += t.length
        xs = [nd[0] for nd in c]
        ys = [nd[1] for nd in c]
        print(f"     comp{i}: {len(c)} nodes, {seg_len:.3f} mm, "
              f"bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]")
    # degree histogram -> branch points
    deg = Counter(len(v) for v in adj.values())
    print("   node degree hist:", dict(sorted(deg.items())))
    br = [nd for nd, v in adj.items() if len(v) > 2]
    print("   branch nodes (deg>2):", [(round(a, 3), round(b, 3)) for a, b in br])
