"""Rigorous per-net electrical path length: per-layer noding, vias + pads join layers.

Graph:
  - nodes = (layer, x, y) snapped to 1 um
  - edges = track segments, split at every intersection with same-layer copper
  - a via adds zero-length edges between all copper layers it spans, at its centre
  - a pad adds zero-length edges between the layers it occupies, and connects any
    node lying inside the pad polygon on that layer to the pad node
Path length = Dijkstra between two pad nodes.
"""
import math
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
from shapely.geometry import Point, LineString  # noqa
from shapely.ops import unary_union  # noqa
import heapq  # noqa

SNAP = 4


def key(layer, pt):
    return (layer, round(pt[0], SNAP), round(pt[1], SNAP))


class NetGraph:
    def __init__(self, bg, net):
        self.bg = bg
        self.net = net
        self.adj = {}
        self.tracks = bg.tracks_of(net)
        self.pads = bg.pads_of(net)
        self._build()

    def _edge(self, a, b, w):
        self.adj.setdefault(a, []).append((b, w))
        self.adj.setdefault(b, []).append((a, w))

    def _build(self):
        layers = sorted({t.layer for t in self.tracks})
        # 1. per-layer noding of the track set
        for layer in layers:
            lines = [t.shape for t in self.tracks if t.layer == layer]
            u = unary_union(lines)          # splits at every intersection
            geoms = list(getattr(u, "geoms", [u]))
            for g in geoms:
                cs = list(g.coords)
                for p, q in zip(cs, cs[1:]):
                    d = math.dist(p, q)
                    if d > 0:
                        self._edge(key(layer, p), key(layer, q), d)
        # 2. vias join layers at their centre; snap to nearest node on each layer
        for v in self.bg.vias_of(self.net):
            spanned = [l for l in self.bg.copper_layers if v.spans(l)]
            prev = None
            for l in spanned:
                nd = key(l, v.at)
                # connect the via node to any track node within the via radius
                r = v.diameter / 2.0 + 1e-3
                for cand in [n for n in self.adj if n[0] == l]:
                    if math.dist((cand[1], cand[2]), v.at) <= r:
                        self._edge(nd, cand, 0.0)
                if prev is not None:
                    self._edge(prev, nd, 0.0)
                prev = nd
        # 3. pads: join their own layers, and swallow nodes inside the pad copper
        for p in self.pads:
            poly = p.poly
            prev = None
            for l in p.layers:
                if l not in self.bg.copper_layers:
                    continue
                nd = ("PAD", p.ref, p.number, l)
                for cand in [n for n in list(self.adj) if n[0] == l]:
                    if poly.buffer(1e-3).contains(Point(cand[1], cand[2])):
                        self._edge(nd, cand, 0.0)
                if prev is not None:
                    self._edge(prev, nd, 0.0)
                prev = nd

    def pad_nodes(self, ref, number=None):
        return [n for n in self.adj if isinstance(n[0], str) and n[0] == "PAD"
                and n[1] == ref and (number is None or n[2] == number)]

    def dij(self, src):
        dist = {src: 0.0}
        prev = {}
        pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, math.inf):
                continue
            for v, w in self.adj.get(u, ()):
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        return dist, prev

    def path_len(self, a, b):
        dist, _ = self.dij(a)
        return dist.get(b)

    def total_union_len(self):
        out = {}
        for layer in sorted({t.layer for t in self.tracks}):
            lines = [t.shape for t in self.tracks if t.layer == layer]
            u = unary_union(lines)
            out[layer] = (sum(t.length for t in self.tracks if t.layer == layer),
                          u.length)
        return out
