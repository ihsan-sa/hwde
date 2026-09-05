"""route_cleanup - post-route hygiene: dangling copper, loops, 90-deg corners
(S11, SPEC P7.4).

Runs AFTER route_auto / stitch_vias / plane_repair and BEFORE the drc_routed
gate. Three ordered passes, each a pure analysis over the parsed board that
emits route_edit ops:

  1. DANGLING: iteratively (fixpoint, cap 20) remove track segments and vias
     with a free end - an endpoint touching NO other same-net item (segment,
     via, pad copper, or same-net zone fill on that layer). "Touches" is
     COPPER-BODY overlap, not centerline proximity (T6/V13 root cause: two
     VBUS stubs ending 1.0 mm from a 3.0 mm trunk's centerline sit 0.5 mm
     INSIDE its copper - KiCad-connected, DRC 0 unconnected - and the old
     centerline test called them free and cut the net). On a DRC-clean board
     real gaps keep centerline distance >= (w1+w2)/2 + clearance, so the
     widened test cannot join across a legal gap.
     A free end INSIDE same-net fill is a legal pour termination (kept); a via
     is kept when it joins 2+ same-net items or sits in same-net fill on any
     layer it spans. Our own graph analysis is the source of truth; DRC's
     track_dangling/via_dangling warnings are reported as a cross-check only.
  2. LOOPS: per net, graph of rounded endpoints (vias merge nodes across their
     spanned layers); cycles made ONLY of track segments lose their single
     longest segment (connectivity preserved); fixpoint, cap 10. Paths through
     zone fill or pad copper never form edges, so parallel drops to a plane
     are NOT treated as loops. Guard (T6): a victim whose netconn edge is a
     BRIDGE of the net's full copper graph (tracks+vias+pads+zones) is load-
     bearing by definition and is vetoed, never removed. After loop removal
     the dangling sweep re-runs once (a broken loop can orphan a stub).
  3. CORNERS (skip with --no-smooth): same-net/layer/width segment pairs
     meeting at 88-92 deg with both legs >= 3*width get a 45-deg chamfer:
     both legs shortened by c = min(min_leg/3, 2*width, 1.0 mm) plus the
     connecting diagonal - only when the diagonal's corridor (width/2 +
     0.2 mm) is clear of foreign copper and of pad copper of ANY net, and the
     corner is not at a pad center/via (0.05 mm) or near other attachments.

The full op list is generated from the parse BEFORE anything is applied
(--dry-run stops there and needs no toolchain). Otherwise: DRC before,
route_edit.apply_ops (atomic), zone refill iff an op touched a layer carrying
fill, DRC after. There is no rollback after apply: if connectivity degraded
(unconnected_items grew) or new DRC errors appeared, the report says so
LOUDLY (violation kind "cleanup_regression", exit 1) - the orchestrator can
git-restore the board.

Contract (SPEC section 6):
  route_cleanup.py --pcb B.kicad_pcb [--dry-run] [--no-smooth]
                   [--out-report r.json]
  JSON to stdout or --out-report; exit 0 pass / 1 violations / 2 error.
  Deterministic: stable sorts (uuid order) everywhere, no RNG.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import sexpdata  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402

import checklib  # noqa: E402
import geom  # noqa: E402
import kc  # noqa: E402
import netconn  # noqa: E402
import route_edit  # noqa: E402
from checklib import CheckError  # noqa: E402

TOL = 0.01              # mm: "touches" tolerance for connectivity
PAD_VIA_KEEPOUT = 0.05  # mm: corners this close to a pad center/via stay
SMOOTH_MIN_LEG = 3.0    # legs must be >= 3*width to chamfer
SMOOTH_MAX_C = 1.0      # mm: chamfer cut ceiling
SMOOTH_CLEAR = 0.2      # mm: clearance margin around the chamfer corridor
DANGLING_CAP = 20       # fixpoint iteration caps
LOOP_CAP = 10


# ============================================================ data model

@dataclass(frozen=True)
class Seg:
    uuid: str
    net: str
    layer: str
    width: float
    a: tuple[float, float]
    b: tuple[float, float]

    @property
    def length(self) -> float:
        return math.dist(self.a, self.b)


@dataclass(frozen=True)
class ViaItem:
    uuid: str
    net: str
    at: tuple[float, float]
    size: float
    drill: float
    layers: tuple[str, ...]  # spanned copper layers (inclusive)


@dataclass(frozen=True)
class PadItem:
    net: str | None
    layers: tuple[str, ...]
    center: tuple[float, float]
    poly: object  # shapely polygon


# ============================================================ local parser
# geom.py deliberately hides uuids; op generation needs them, so this small
# sexpdata walk extracts JUST (segment ...) and (via ...) nodes + uuids.

def parse_items(pcb: Path, copper_layers: list[str]) -> tuple[list[Seg],
                                                              list[ViaItem]]:
    try:
        root = sexpdata.loads(Path(pcb).read_text(encoding="utf-8"))
    except Exception as exc:
        raise CheckError(f"cannot parse {pcb}: {exc}") from exc

    def tok(x):
        return x.value() if isinstance(x, sexpdata.Symbol) else x

    def kid(node, name):
        for c in node[1:]:
            if isinstance(c, list) and c and tok(c[0]) == name:
                return c
        return None

    def nums(node):
        return [float(x) for x in node[1:] if isinstance(x, (int, float))]

    def first_str(node):
        for x in node[1:]:
            v = tok(x)
            if isinstance(v, str):
                return v
        return None

    net_table = {}
    for c in root[1:]:
        if isinstance(c, list) and c and tok(c[0]) == "net":
            n = nums(c)
            if n:
                net_table[int(n[0])] = first_str(c) or ""

    def net_of(item):
        node = kid(item, "net")
        if node is None:
            return ""
        s = first_str(node)
        if s is not None:
            return s
        n = nums(node)
        return net_table.get(int(n[0]), "") if n else ""

    def uuid_of(item):
        node = kid(item, "uuid") or kid(item, "tstamp")
        return (first_str(node) or "") if node is not None else ""

    cu = set(copper_layers)
    segs: list[Seg] = []
    vias: list[ViaItem] = []
    for c in root[1:]:
        if not (isinstance(c, list) and c):
            continue
        h = tok(c[0])
        if h == "segment":
            s, e = kid(c, "start"), kid(c, "end")
            w, l = kid(c, "width"), kid(c, "layer")
            if not (s and e and w and l) or first_str(l) not in cu:
                continue
            a, b = nums(s), nums(e)
            segs.append(Seg(uuid_of(c), net_of(c), first_str(l), nums(w)[0],
                            (a[0], a[1]), (b[0], b[1])))
        elif h == "via":
            at, size = kid(c, "at"), kid(c, "size")
            if not (at and size):
                continue
            lnode = kid(c, "layers")
            names = [tok(x) for x in lnode[1:]] if lnode is not None else []
            names = [n for n in names if isinstance(n, str) and n in cu]
            if len(names) >= 2:  # from/to SPAN, expanded like geom does
                i, j = sorted((copper_layers.index(names[0]),
                               copper_layers.index(names[-1])))
                span = tuple(copper_layers[i:j + 1])
            elif names:
                span = (names[0],)
            else:
                span = tuple(copper_layers)  # default through-via
            p = nums(at)
            d = kid(c, "drill")
            vias.append(ViaItem(uuid_of(c), net_of(c), (p[0], p[1]),
                                nums(size)[0],
                                nums(d)[0] if d and nums(d) else 0.0, span))
    return segs, vias


# ============================================================ geometry helpers

def _pt_seg_dist(p, a, b) -> float:
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    l2 = dx * dx + dy * dy
    if l2 <= 1e-18:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def _node(layer: str, p) -> tuple:
    """Snap a point to the TOL grid; node identity for graph passes."""
    return (layer, round(p[0] * 100), round(p[1] * 100))


def _fill_touches(fillfn, net, layer, p, tol) -> bool:
    g = fillfn(net, layer)
    return (g is not None and not g.is_empty
            and g.distance(Point(p)) <= tol)


# ============================================================ pass 1: dangling

def _endpoint_free(seg: Seg, p, segs, vias, pads, fillfn, arcs, tol) -> bool:
    """True if endpoint p of `seg` touches no other same-net item.

    "Touches" is COPPER overlap, not centerline proximity (T6/V13 fix): the
    endpoint's round cap (radius seg.width/2) overlapping another item's
    body counts as connected - exactly KiCad's connectivity model. On a
    DRC-clean board this cannot join across a real gap (centerline distance
    of legally separated copper >= (w1+w2)/2 + clearance > every reach used
    here)."""
    pt = Point(p)
    half = seg.width / 2.0
    for o in segs:
        if o is seg or o.net != seg.net or o.layer != seg.layer:
            continue
        if _pt_seg_dist(p, o.a, o.b) <= (seg.width + o.width) / 2.0 + tol:
            return False
    for net, layer, line, aw in arcs:
        if net == seg.net and layer == seg.layer \
                and line.distance(pt) <= (seg.width + aw) / 2.0 + tol:
            return False
    for v in vias:
        if (v.net == seg.net and seg.layer in v.layers
                and math.dist(p, v.at) <= v.size / 2.0 + half + tol):
            return False
    for pd in pads:
        if (pd.net == seg.net and seg.layer in pd.layers
                and pd.poly.distance(pt) <= half + tol):
            return False
    return not _fill_touches(fillfn, seg.net, seg.layer, p, tol)


def _via_keep(v: ViaItem, segs, pads, fillfn, tol) -> bool:
    """Keep a via if it sits in same-net fill on any spanned layer or joins
    2+ same-net items (tracks/pads); otherwise it has a free end. Track
    contact is copper overlap (barrel + track half-width, T6/V13 fix)."""
    for layer in v.layers:
        if _fill_touches(fillfn, v.net, layer, v.at, tol):
            return True
    r = v.size / 2.0 + tol
    contacts = 0
    for s in segs:
        if (s.net == v.net and s.layer in v.layers
                and _pt_seg_dist(v.at, s.a, s.b) <= r + s.width / 2.0):
            contacts += 1
            if contacts >= 2:
                return True
    pt = Point(v.at)
    for pd in pads:
        if (pd.net == v.net and set(pd.layers) & set(v.layers)
                and pd.poly.distance(pt) <= r):
            contacts += 1
            if contacts >= 2:
                return True
    return False


def find_dangling(segs, vias, pads, fillfn, arcs=(), tol=TOL,
                  cap=DANGLING_CAP) -> tuple[list[str], list[str]]:
    """Fixpoint removal of free-ended segments/vias. Returns uuid lists
    (segments, vias) in removal order. Items without a uuid are anchors only
    (they can never be removed)."""
    alive_s = list(segs)
    alive_v = list(vias)
    gone_s: list[str] = []
    gone_v: list[str] = []
    for _ in range(cap):
        drop_s = [s for s in alive_s if s.uuid and (
            _endpoint_free(s, s.a, alive_s, alive_v, pads, fillfn, arcs, tol)
            or _endpoint_free(s, s.b, alive_s, alive_v, pads, fillfn, arcs,
                              tol))]
        drop_v = [v for v in alive_v
                  if v.uuid and not _via_keep(v, alive_s, pads, fillfn, tol)]
        if not drop_s and not drop_v:
            break
        ds = {id(x) for x in drop_s}
        dv = {id(x) for x in drop_v}
        alive_s = [s for s in alive_s if id(s) not in ds]
        alive_v = [v for v in alive_v if id(v) not in dv]
        gone_s += sorted(s.uuid for s in drop_s)
        gone_v += sorted(v.uuid for v in drop_v)
    return gone_s, gone_v


# ============================================================ pass 2: loops

def _via_canon(vias):
    """Canonical-node mapper: vias merge (layer, pos) nodes across their
    span. Finalized before segment processing, so lookups are stable."""
    parent: dict = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for v in sorted(vias, key=lambda v: (v.uuid, v.at)):
        keys = [_node(l, v.at) for l in v.layers]
        for k in keys[1:]:
            ra, rb = find(keys[0]), find(k)
            if ra != rb:
                parent[ra] = rb
    return lambda k: find(k) if k in parent else k


def _bfs_path(adj, src, dst):
    """Edge path src->dst in the (segment-only) adjacency, or None."""
    if src == dst:
        return []
    prev = {src: None}
    queue = [src]
    while queue:
        nxt = []
        for n in queue:
            for m, e in adj.get(n, ()):
                if m in prev:
                    continue
                prev[m] = (n, e)
                if m == dst:
                    path, cur = [], m
                    while prev[cur] is not None:
                        n2, e2 = prev[cur]
                        path.append(e2)
                        cur = n2
                    return path
                nxt.append(m)
        queue = nxt
    return None


def _loop_sweep(segs, canon) -> list[Seg]:
    """One sweep: the longest segment of each independent pure-track cycle.
    Cycles touching a segment already picked this sweep are deferred to the
    next fixpoint iteration."""
    parent: dict = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    adj: dict = {}
    victims: list[Seg] = []
    tainted: set[int] = set()
    for s in sorted(segs, key=lambda s: (s.uuid, s.layer, s.a, s.b)):
        ka = canon(_node(s.layer, s.a))
        kb = canon(_node(s.layer, s.b))
        ra, rb = find(ka), find(kb)
        closes = ra == rb
        if not closes:
            parent[ra] = rb
        if closes:
            path = _bfs_path(adj, ka, kb)
            if path is None:  # connected through a dropped edge only
                continue
            cycle = path + [s]
            if any(id(e) in tainted for e in cycle):
                continue
            with_uuid = [e for e in cycle if e.uuid]
            if not with_uuid:
                continue
            victim = max(with_uuid, key=lambda e: (e.length, e.uuid))
            victims.append(victim)
            tainted.add(id(victim))
            if victim is s:
                continue  # s dropped; keep it out of the adjacency
        adj.setdefault(ka, []).append((kb, s))
        adj.setdefault(kb, []).append((ka, s))
    return victims


def find_loops(segs, vias, cap=LOOP_CAP) -> tuple[list[str], int]:
    """Break pure track-segment cycles (vias merge nodes across layers; pads
    and zone fill never form edges). Returns (uuids removed, loops broken)."""
    alive = list(segs)
    canon = _via_canon(vias)
    removed: list[str] = []
    loops = 0
    for _ in range(cap):
        victims = _loop_sweep(alive, canon)
        if not victims:
            break
        ids = {id(v) for v in victims}
        alive = [s for s in alive if id(s) not in ids]
        removed += sorted(v.uuid for v in victims)
        loops += len(victims)
    return removed, loops


def loop_bridge_veto(bg: geom.BoardGeom, victims: list[Seg]
                     ) -> tuple[list[str], list[str]]:
    """Split loop victims into (removable_uuids, vetoed_uuids).

    A victim whose netconn edge is a BRIDGE (cut edge) of the net's FULL
    copper connectivity graph (tracks + vias + pads + zones) is load-bearing
    by definition - the loop model disagreed with real connectivity, so the
    removal is vetoed (T6/V13 guard; the veto can only prevent removals).
    Victims that cannot be matched to a netconn edge are vetoed too (never
    remove what cannot be verified)."""
    removable: list[str] = []
    vetoed: list[str] = []
    by_net: dict[str, list[Seg]] = {}
    for s in victims:
        by_net.setdefault(s.net, []).append(s)
    for net in sorted(by_net):
        g = netconn.build(bg, net, include_zones=True)
        bridges = netconn.bridge_tracks(g)
        tracks = bg.tracks_of(net)

        def edge_of(s: Seg):
            for i, t in enumerate(tracks):
                if t.layer != s.layer or len(t.shape.coords) != 2:
                    continue
                c0 = t.shape.coords[0]
                c1 = t.shape.coords[-1]
                if ((math.dist(c0, s.a) <= 1e-3 and math.dist(c1, s.b) <= 1e-3)
                        or (math.dist(c0, s.b) <= 1e-3
                            and math.dist(c1, s.a) <= 1e-3)):
                    return i
            return None

        for s in by_net[net]:
            eid = edge_of(s)
            if eid is None or eid in bridges:
                vetoed.append(s.uuid)
            else:
                removable.append(s.uuid)
    return sorted(removable), sorted(vetoed)


# ============================================================ pass 3: corners

def _r4(p) -> list[float]:
    return [round(p[0], 4), round(p[1], 4)]


def find_corners(segs, vias, pads, foreign_fn, tol=TOL) -> tuple[list[dict],
                                                                 list[dict]]:
    """45-deg chamfer plans for clean ~90-deg corners. foreign_fn(layer, net)
    -> copper of every OTHER net on that layer. Returns (ops, corners)."""
    ends: dict = {}
    for s in sorted(segs, key=lambda s: s.uuid):
        if not s.uuid or not s.net:
            continue
        ends.setdefault(_node(s.layer, s.a), []).append((s, 0))
        ends.setdefault(_node(s.layer, s.b), []).append((s, 1))
    ops: list[dict] = []
    corners: list[dict] = []
    consumed: set[str] = set()
    for key in sorted(ends):
        pair = ends[key]
        if len(pair) != 2:
            continue  # only clean 2-segment elbows are smoothable
        (s1, e1), (s2, e2) = pair
        if (s1 is s2 or s1.net != s2.net
                or abs(s1.width - s2.width) > 1e-3
                or s1.uuid in consumed or s2.uuid in consumed):
            continue
        w = s1.width
        c1, f1 = ((s1.a, s1.b)[e1], (s1.a, s1.b)[1 - e1])
        c2, f2 = ((s2.a, s2.b)[e2], (s2.a, s2.b)[1 - e2])
        v1 = (f1[0] - c1[0], f1[1] - c1[1])
        v2 = (f2[0] - c2[0], f2[1] - c2[1])
        la, lb = math.hypot(*v1), math.hypot(*v2)
        if min(la, lb) < SMOOTH_MIN_LEG * w:
            continue
        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (la * lb)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
        if not (88.0 <= ang <= 92.0):
            continue
        c = min(min(la, lb) / 3.0, 2.0 * w, SMOOTH_MAX_C)
        corner = c1
        # corners at pad centers / vias stay
        if any(math.dist(corner, pd.center) <= PAD_VIA_KEEPOUT
               for pd in pads):
            continue
        if any(math.dist(corner, v.at)
               <= max(PAD_VIA_KEEPOUT, c + v.size / 2.0 + tol)
               for v in vias):
            continue
        # nothing else may attach inside the region the chamfer removes
        if any(s1.layer in pd.layers
               and pd.poly.distance(Point(corner)) <= c + tol
               for pd in pads):
            continue
        if any(o is not s1 and o is not s2
               and o.net == s1.net and o.layer == s1.layer
               and _pt_seg_dist(corner, o.a, o.b) <= c + tol
               for o in segs):
            continue
        p1 = (c1[0] + v1[0] / la * c, c1[1] + v1[1] / la * c)
        p2 = (c2[0] + v2[0] / lb * c, c2[1] + v2[1] / lb * c)
        corridor = LineString([p1, p2]).buffer(w / 2.0 + SMOOTH_CLEAR,
                                               quad_segs=8)
        foreign = foreign_fn(s1.layer, s1.net)
        if (foreign is not None and not foreign.is_empty
                and corridor.intersects(foreign)):
            continue
        if any(s1.layer in pd.layers and corridor.intersects(pd.poly)
               for pd in pads):  # pad copper of ANY net blocks the chamfer
            continue
        consumed.update((s1.uuid, s2.uuid))
        wid = round(w, 4)
        ops += [
            {"op": "remove", "uuid": s1.uuid},
            {"op": "remove", "uuid": s2.uuid},
            {"op": "add_track", "start": _r4(f1), "end": _r4(p1),
             "width": wid, "layer": s1.layer, "net": s1.net},
            {"op": "add_track", "start": _r4(f2), "end": _r4(p2),
             "width": wid, "layer": s1.layer, "net": s1.net},
            {"op": "add_track", "start": _r4(p1), "end": _r4(p2),
             "width": wid, "layer": s1.layer, "net": s1.net},
        ]
        corners.append({"corner": _r4(corner), "layer": s1.layer,
                        "net": s1.net, "chamfer_mm": round(c, 4),
                        "uuids": [s1.uuid, s2.uuid]})
    return ops, corners


# ============================================================ plan + driver

def build_plan(bg: geom.BoardGeom, segs, vias, smooth: bool = True) -> dict:
    """All three passes over one parse -> {ops, op_layers, facts...}."""
    pads = [PadItem(p.net, tuple(p.layers), p.center, p.poly)
            for p in bg.pads_of()]
    arcs = tuple((t.net, t.layer, t.shape, t.width) for t in bg.tracks_of()
                 if len(t.shape.coords) > 2)  # arcs anchor, never removed
    cache: dict = {}

    def fillfn(net, layer):
        key = (net, layer)
        if key not in cache:
            cache[key] = bg.zone_fill(net, layer)
        return cache[key]

    gone_s, gone_v = find_dangling(segs, vias, pads, fillfn, arcs)
    dead = set(gone_s) | set(gone_v)
    alive_s = [s for s in segs if s.uuid not in dead]
    alive_v = [v for v in vias if v.uuid not in dead]
    loop_uuids, _loops = find_loops(alive_s, alive_v)
    # T6/V13 guard: a victim that is a bridge of the net's FULL connectivity
    # graph is load-bearing - veto its removal (the loop stays, warning-level
    # outcome; the veto can only PREVENT copper loss).
    victim_segs = [s for s in alive_s if s.uuid in set(loop_uuids)]
    loop_uuids, loop_vetoed = loop_bridge_veto(bg, victim_segs)
    dead |= set(loop_uuids)
    alive_s = [s for s in alive_s if s.uuid not in dead]
    # a broken loop can orphan a stub: one more dangling sweep on the
    # remainder (counted separately - orphaned_after_loops)
    orphan_s: list[str] = []
    orphan_v: list[str] = []
    if loop_uuids:
        orphan_s, orphan_v = find_dangling(alive_s, alive_v, pads, fillfn,
                                           arcs)
        dead |= set(orphan_s) | set(orphan_v)
        alive_s = [s for s in alive_s if s.uuid not in dead]
        alive_v = [v for v in alive_v if v.uuid not in dead]
    corner_ops: list[dict] = []
    corners: list[dict] = []
    if smooth:
        corner_ops, corners = find_corners(
            alive_s, alive_v, pads,
            lambda layer, net: bg.layer_copper(layer, exclude=net))
    ops = ([{"op": "remove", "uuid": u} for u in gone_s]
           + [{"op": "remove", "uuid": u} for u in gone_v]
           + [{"op": "remove", "uuid": u} for u in loop_uuids]
           + [{"op": "remove", "uuid": u} for u in orphan_s]
           + [{"op": "remove", "uuid": u} for u in orphan_v]
           + corner_ops)
    layer_of = {s.uuid: (s.layer,) for s in segs}
    layer_of.update({v.uuid: v.layers for v in vias})
    op_layers: set[str] = set()
    for op in ops:
        if op["op"] == "remove":
            op_layers.update(layer_of.get(op["uuid"], ()))
        else:
            op_layers.add(op["layer"])
    return {
        "ops": ops, "op_layers": op_layers,
        "dangling_segments": len(gone_s), "dangling_vias": len(gone_v),
        "dangling_removed": len(gone_s) + len(gone_v),
        "loops_broken": len(loop_uuids), "loop_bridge_vetoed": len(loop_vetoed),
        "orphaned_after_loops": len(orphan_s) + len(orphan_v),
        "corners_smoothed": len(corners),
        "corners": corners,
    }


def _drc_facts(report: dict) -> dict:
    counts = report["counts"]
    return {
        "unconnected": counts["by_source"].get("unconnected", 0),
        "errors": counts["by_severity"].get("error", 0),
        "warnings": counts["by_severity"].get("warning", 0),
        "dangling_flagged": sum(
            1 for v in report["violations"]
            if v.get("check") in ("track_dangling", "via_dangling")),
    }


def run(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="generate + report ops only; board untouched, "
                         "no toolchain needed")
    ap.add_argument("--no-smooth", action="store_true",
                    help="skip pass 3 (corner smoothing)")
    ap.add_argument("--out-report", default=None)
    args = ap.parse_args(argv)

    pcb = Path(args.pcb).resolve()
    if not pcb.is_file():
        raise CheckError(f"board not found: {pcb}")
    bg = geom.BoardGeom.from_file(pcb)
    # dangling detection reads zone fills as legal terminations - a stale/
    # unfilled pour would make live pour-terminated stubs look dangling
    # (S11 review finding; plane_repair has the same guard).
    bg.assert_fresh()
    segs, vias = parse_items(pcb, bg.copper_layers)
    plan = build_plan(bg, segs, vias, smooth=not args.no_smooth)
    facts = {k: plan[k] for k in (
        "dangling_removed", "dangling_segments", "dangling_vias",
        "loops_broken", "loop_bridge_vetoed", "orphaned_after_loops",
        "corners_smoothed", "corners")}

    if args.dry_run:
        payload = checklib.report(
            "route_cleanup", pcb, [], dry_run=True, ops_applied=0,
            refilled=False, drc_before=None, drc_after=None,
            ops=plan["ops"], **facts)
        return payload, args.out_report

    cli = kc.resolve_cli()
    before = kc.run_drc(cli, pcb, all_track_errors=True)
    b = _drc_facts(before)
    applied = 0
    refilled = False
    if plan["ops"]:
        route_edit.apply_ops(pcb, plan["ops"])
        applied = len(plan["ops"])
        fill_layers = {l for z in bg.zones_of()
                       for l, polys in z.fills.items() if polys}
        refilled = bool(fill_layers & plan["op_layers"])
        try:
            after = kc.run_drc(cli, pcb, all_track_errors=True,
                               refill=refilled, save_board=refilled)
        except Exception as exc:  # noqa: BLE001
            raise CheckError(
                "cleanup ops were APPLIED but the refill/DRC step failed - "
                "the board HAS been modified; re-run 'kicad-cli pcb drc "
                "--refill-zones --save-board' and re-check. "
                f"Cause: {exc}") from exc
        a = _drc_facts(after)
    else:
        a = b

    violations = []
    if a["unconnected"] > b["unconnected"] or a["errors"] > b["errors"]:
        violations.append(checklib.violation(
            "cleanup_regression", "error", None, None, None, [],
            f"cleanup DEGRADED the board: unconnected {b['unconnected']}"
            f"->{a['unconnected']}, DRC errors {b['errors']}->{a['errors']}."
            " The board file HAS been modified - restore it from git before"
            " continuing.", "route_cleanup",
            kind="cleanup_regression", drc_before=b, drc_after=a))
    payload = checklib.report(
        "route_cleanup", pcb, violations, dry_run=False, ops_applied=applied,
        refilled=refilled, drc_before=b, drc_after=a, ops=plan["ops"],
        **facts)
    return payload, args.out_report


def main(argv: list[str] | None = None) -> int:
    return checklib.cli_wrap("route_cleanup", lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
