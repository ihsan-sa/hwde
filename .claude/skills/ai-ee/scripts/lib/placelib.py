"""placelib - placement model + metrics shared by place_seed/place_metrics/place_edit (S9).

Parses .kicad_pcb footprint blocks into a lightweight MOVABLE model that geom.py
deliberately does not keep (geom stores absolute pad geometry only):

  Footprint: ref, fpid, pos, angle (file convention), side, attr flags, locked,
             pads with LOCAL offsets, courtyard polygon in the LOCAL frame.

Absolute geometry is derived as  abs = fp_pos + R(-fp_angle) . local  (the
S3-verified transform, LEARNINGS [geometry][kicad]); a flipped footprint's flip
is baked into the file (locals mirrored, layers renamed B.*) so the same
transform covers both sides and the parser must NOT mirror anything.

Board outline / rule areas / net-indexed copper come from geom.load_board -
placelib does not duplicate that parsing.

Placement targeting works on the courtyard CENTER, not the footprint origin:
for asymmetric parts the origin can sit far outside the body (prior-attempt
fact: a 1x20 header's origin is ~24 mm off center), so seat placements compute
the origin from the desired center at the chosen rotation.

Everything is mm / mm^2; angles are file-convention degrees.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union

import geom
from geom import _head, _is_node, _kid, _kids, _nums, _pts, _rot, _strs, _tok
import checklib

SOURCE = "check.place"
EPS_AREA = 0.01  # mm^2 - below this an intersection is numerical noise


# ---------------------------------------------------------------- model

@dataclass
class FpPad:
    number: str
    net: str | None
    local: tuple[float, float]  # offset from fp anchor, pre-rotation frame
    size: tuple[float, float]
    through: bool


@dataclass
class Footprint:
    ref: str
    fpid: str
    pos: tuple[float, float]
    angle: float                # file-convention degrees
    side: str                   # "front" | "back"  (from (layer F.Cu/B.Cu))
    attrs: frozenset[str]       # tokens of (attr ...): smd/through_hole/board_only/...
    locked: bool
    pads: list[FpPad]
    courtyard_local: Polygon | None   # local frame, the part's own side
    courtyard_missing: bool = False   # True when extents fall back to pads

    # -- derived, local frame -------------------------------------------
    def extents_local(self) -> Polygon:
        """Courtyard, or the pad-bbox fallback (+0.25 mm) when absent."""
        if self.courtyard_local is not None:
            return self.courtyard_local
        if not self.pads:
            return box(-0.5, -0.5, 0.5, 0.5)
        xs, ys, hs, vs = zip(*((p.local[0], p.local[1],
                                p.size[0] / 2, p.size[1] / 2)
                               for p in self.pads))
        m = 0.25
        return box(min(x - h for x, h in zip(xs, hs)) - m,
                   min(y - v for y, v in zip(ys, vs)) - m,
                   max(x + h for x, h in zip(xs, hs)) + m,
                   max(y + v for y, v in zip(ys, vs)) + m)

    def center_local(self) -> tuple[float, float]:
        c = self.extents_local().centroid
        return (c.x, c.y)

    # -- derived, board frame -------------------------------------------
    def to_abs(self, local_xy: tuple[float, float]) -> tuple[float, float]:
        dx, dy = _rot(local_xy[0], local_xy[1], -self.angle)
        return (self.pos[0] + dx, self.pos[1] + dy)

    def extents_abs(self) -> Polygon:
        p = affinity.rotate(self.extents_local(), -self.angle, origin=(0, 0))
        return affinity.translate(p, self.pos[0], self.pos[1])

    def center_abs(self) -> tuple[float, float]:
        return self.to_abs(self.center_local())

    def pad_centers_abs(self) -> list[tuple[str, str | None, float, float]]:
        out = []
        for p in self.pads:
            x, y = self.to_abs(p.local)
            out.append((p.number, p.net, x, y))
        return out

    def place_center(self, center: tuple[float, float], angle: float) -> None:
        """Set angle and move the ORIGIN so the courtyard center lands on center."""
        self.angle = angle
        cx, cy = self.center_local()
        dx, dy = _rot(cx, cy, -angle)
        self.pos = (center[0] - dx, center[1] - dy)

    @property
    def is_movable(self) -> bool:
        return not (self.locked or "board_only" in self.attrs)


class PlaceModel:
    """The movable-footprint view of a board + the geom view for everything else."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.bg = geom.load_board(self.path)
        self.outline: Polygon = self.bg.outline
        self.rule_areas = self.bg.rule_areas
        self.footprints: dict[str, Footprint] = {}
        self._parse(self.path)

    # ------------------------------------------------------------ parsing
    def _parse(self, path: Path) -> None:
        import sexpdata
        tree = sexpdata.loads(path.read_text(encoding="utf-8"))
        for fp in _kids(tree, "footprint"):
            f = self._parse_fp(fp)
            if f is not None:
                self.footprints[f.ref] = f

    def _parse_fp(self, fp) -> Footprint | None:
        strs = _strs(fp)
        fpid = strs[0] if strs else ""
        at = _kid(fp, "at")
        nums = _nums(at) if at is not None else [0.0, 0.0]
        pos = (nums[0], nums[1])
        angle = nums[2] if len(nums) > 2 else 0.0
        layer = _kid(fp, "layer")
        side = "back" if (layer is not None and _strs(layer)
                          and _strs(layer)[0].startswith("B.")) else "front"

        ref = None
        for prop in _kids(fp, "property"):
            s = _strs(prop)
            if len(s) >= 2 and s[0] == "Reference":
                ref = s[1]
                break
        if not ref:
            return None

        attrs = set()
        attr = _kid(fp, "attr")
        if attr is not None:
            attrs = {_tok(t) for t in attr[1:] if not _is_node(t)}
        locked = False
        lk = _kid(fp, "locked")
        if lk is not None and (len(lk) < 2 or _tok(lk[1]) != "no"):
            locked = True
        if any(not _is_node(t) and _tok(t) == "locked" for t in fp[1:]):
            locked = True

        pads = []
        for pad in _kids(fp, "pad"):
            ps = _strs(pad)
            number = ps[0] if ps else ""
            toks = [_tok(t) for t in pad[1:4] if not _is_node(t)]
            through = any(t in ("thru_hole", "np_thru_hole") for t in toks)
            pat = _kid(pad, "at")
            pn = _nums(pat) if pat is not None else [0.0, 0.0]
            psz = _kid(pad, "size")
            sz = _nums(psz) if psz is not None else [0.0, 0.0]
            net = None
            pnet = _kid(pad, "net")
            if pnet is not None:
                ns = _strs(pnet)
                net = ns[-1] if ns else None
            pads.append(FpPad(number, net, (pn[0], pn[1]),
                              (sz[0] if sz else 0.0, sz[1] if len(sz) > 1 else 0.0),
                              through))

        want = "B.CrtYd" if side == "back" else "F.CrtYd"
        courtyard = _courtyard_poly(fp, want)
        return Footprint(ref=ref, fpid=fpid, pos=pos, angle=angle, side=side,
                         attrs=frozenset(attrs), locked=locked, pads=pads,
                         courtyard_local=courtyard,
                         courtyard_missing=courtyard is None)

    # ------------------------------------------------------------ queries
    def movable(self) -> list[Footprint]:
        return [f for f in self.footprints.values() if f.is_movable]

    def nets_with_pads(self) -> dict[str, list[tuple[float, float]]]:
        """net -> absolute pad centers (2+ pads only), sorted deterministically."""
        acc: dict[str, list[tuple[float, float]]] = {}
        for ref in sorted(self.footprints):
            for _num, net, x, y in self.footprints[ref].pad_centers_abs():
                if net:
                    acc.setdefault(net, []).append((round(x, 4), round(y, 4)))
        return {n: sorted(pts) for n, pts in sorted(acc.items()) if len(pts) >= 2}


def _courtyard_poly(fp_node, layer_name: str) -> Polygon | None:
    """Union of courtyard graphics on layer_name, in the footprint-local frame."""
    areas, lines = [], []
    for head in ("fp_rect", "fp_line", "fp_circle", "fp_poly", "fp_arc"):
        for g in _kids(fp_node, head):
            lay = _kid(g, "layer")
            if lay is None or not _strs(lay) or _strs(lay)[0] != layer_name:
                continue
            if head == "fp_rect":
                s, e = _nums(_kid(g, "start")), _nums(_kid(g, "end"))
                areas.append(box(min(s[0], e[0]), min(s[1], e[1]),
                                 max(s[0], e[0]), max(s[1], e[1])))
            elif head == "fp_circle":
                c, e = _nums(_kid(g, "center")), _nums(_kid(g, "end"))
                r = math.hypot(e[0] - c[0], e[1] - c[1])
                if r > 0:
                    areas.append(Point(c[0], c[1]).buffer(r, quad_segs=16))
            elif head == "fp_poly":
                pts = _pts(_kid(g, "pts"))
                if len(pts) >= 3:
                    areas.append(Polygon(pts))
            elif head == "fp_line":
                s, e = _nums(_kid(g, "start")), _nums(_kid(g, "end"))
                lines.append(LineString([(s[0], s[1]), (e[0], e[1])]))
            else:  # fp_arc
                s = _nums(_kid(g, "start"))
                m = _nums(_kid(g, "mid"))
                e = _nums(_kid(g, "end"))
                pts = geom._arc_points((s[0], s[1]), (m[0], m[1]), (e[0], e[1]))
                lines.append(LineString(pts))
    if lines:
        rings = list(polygonize(unary_union(lines)))
        if rings:
            areas.extend(rings)
        elif not areas:
            hull = unary_union(lines).convex_hull
            if hull.geom_type == "Polygon" and hull.area > EPS_AREA:
                areas.append(hull)
    if not areas:
        return None
    u = unary_union(areas)
    if u.geom_type == "MultiPolygon":  # disjoint courtyard pieces: take hull
        u = u.convex_hull
    return u if (u.geom_type == "Polygon" and u.area > EPS_AREA) else None


# ---------------------------------------------------------------- clusters

@dataclass
class Satellite:
    ref: str
    target_pin: tuple[str, str] | None  # (anchor_ref, pad_number) or None


@dataclass
class Cluster:
    anchor: str
    satellites: list[Satellite] = field(default_factory=list)
    edge: dict | None = None    # placement.edges entry pinned to this cluster

    @property
    def refs(self) -> list[str]:
        return [self.anchor] + [s.ref for s in self.satellites]


def build_clusters(model: PlaceModel, decoupling: dict | None,
                   placement: dict | None) -> tuple[list[Cluster], list[str]]:
    """Satellite clusters from decoupling associations + explicit placement
    groups; every remaining movable footprint is a singleton. Returns
    (clusters sorted by anchor, warnings). Missing refs warn, never raise."""
    warnings: list[str] = []
    fps = model.footprints
    owner: dict[str, str] = {}          # satellite ref -> anchor ref
    sat_of: dict[str, list[Satellite]] = {}

    def claim(sat: str, anchor: str, pin: str | None, src: str) -> None:
        if sat not in fps or anchor not in fps:
            missing = sat if sat not in fps else anchor
            warnings.append(f"{src}: ref {missing} not on board - ignored")
            return
        if not fps[sat].is_movable:
            return
        if sat in owner:
            if owner[sat] != anchor:
                warnings.append(f"{src}: {sat} already satellite of {owner[sat]}"
                                f" - keeping first association")
            return
        if anchor in owner:
            warnings.append(f"{src}: anchor {anchor} is itself a satellite of "
                            f"{owner[anchor]} - {sat} ignored")
            return
        owner[sat] = anchor
        sat_of.setdefault(anchor, []).append(
            Satellite(sat, (anchor, pin) if pin else None))

    for a in (decoupling or {}).get("associations", []):
        cap, ic, pin = a.get("cap"), a.get("ic"), a.get("pin")
        if cap and ic:
            claim(cap, ic, str(pin) if pin is not None else None, "decoupling")
    for g in (placement or {}).get("groups", []):
        anchor = g.get("anchor")
        for m in g.get("members", []):
            claim(m, anchor, None, f"group {g.get('name', anchor)}")

    edges = {e["ref"]: e for e in (placement or {}).get("edges", [])
             if e.get("ref")}
    fixed_extra = set((placement or {}).get("fixed", []))

    clusters, fixed = [], []
    for ref in sorted(fps):
        f = fps[ref]
        if not f.is_movable or ref in fixed_extra:
            fixed.append(ref)
            continue
        if ref in owner:
            continue
        c = Cluster(anchor=ref, satellites=sorted(
            sat_of.get(ref, []), key=lambda s: s.ref))
        anchor_edge = edges.get(ref)
        for s in c.satellites:
            if s.ref in edges and anchor_edge is None:
                anchor_edge = edges[s.ref]
                warnings.append(f"edge for satellite {s.ref} pins its cluster "
                                f"anchor {ref}")
        c.edge = anchor_edge
        clusters.append(c)
    for ref in sorted(edges):
        if ref not in fps:
            warnings.append(f"placement.edges: ref {ref} not on board - ignored")
    return clusters, warnings


# ---------------------------------------------------------------- legality

def _forbidden(model: PlaceModel, placement: dict | None, side: str):
    """Keepout polygons for footprints on side: constraints keepouts + board
    rule areas whose layers include that side's copper (conservative)."""
    polys = []
    for k in (placement or {}).get("keepouts", []):
        ks = k.get("side", "both")
        if ks not in ("both", side):
            continue
        if "rect" in k:
            x1, y1, x2, y2 = k["rect"]
            polys.append((box(min(x1, x2), min(y1, y2), max(x1, x2),
                              max(y1, y2)), k.get("reason", "keepout")))
        elif "poly" in k:
            polys.append((Polygon([tuple(p) for p in k["poly"]]),
                          k.get("reason", "keepout")))
    want = "F.Cu" if side == "front" else "B.Cu"
    for ra in model.rule_areas:
        lays = ra.get("layers") or []
        if want in lays or "*.Cu" in lays or not lays:
            polys.append((ra["outline"], f"rule area '{ra.get('name') or '?'}'"))
    return polys


# A declared-edge part's courtyard must come within this of its edge. 2.5 mm
# accepts a sensibly-inboard THT header (the usbbuck4 golden sits ~2 mm in)
# while still failing a connector stranded mid-board.
EDGE_TOL = 2.5  # mm

# Minimum courtyard fraction that must stay on the board for a declared-edge
# part. Calibrated on the rf4 golden: its edge-mount SMA (which CLAMPS the
# board edge) keeps only 35% of its courtyard on-board by design.
ON_BOARD_MIN = 0.25


def edge_line(outline: Polygon, edge: str) -> LineString:
    minx, miny, maxx, maxy = outline.bounds
    return {
        "left": LineString([(minx, miny), (minx, maxy)]),
        "right": LineString([(maxx, miny), (maxx, maxy)]),
        "top": LineString([(minx, miny), (maxx, miny)]),
        "bottom": LineString([(minx, maxy), (maxx, maxy)]),
    }[edge]


def legality_violations(model: PlaceModel, placement: dict | None) -> list[dict]:
    """Normalized violations (S2 schema): courtyard overlaps, outline
    containment, keepouts, declared-edge compliance, missing courtyards."""
    v: list[dict] = []
    placement = placement or {}
    edges = {e["ref"]: e for e in placement.get("edges", []) if e.get("ref")}
    fps = [model.footprints[r] for r in sorted(model.footprints)]
    ext = {f.ref: f.extents_abs() for f in fps}

    def collides(a: Footprint, b: Footprint) -> bool:
        if a.side == b.side:
            return True
        thru = ("through_hole" in a.attrs or any(p.through for p in a.pads)
                or "through_hole" in b.attrs or any(p.through for p in b.pads))
        return thru

    for i, a in enumerate(fps):
        for b in fps[i + 1:]:
            if not collides(a, b):
                continue
            inter = ext[a.ref].intersection(ext[b.ref])
            if inter.area > EPS_AREA:
                c = inter.centroid
                v.append(checklib.violation(
                    "place", "error", (c.x, c.y), None, None, [a.ref, b.ref],
                    f"courtyard overlap {a.ref}/{b.ref} ({inter.area:.2f} mm2)",
                    SOURCE, kind="courtyard_overlap",
                    overlap_mm2=checklib.rnd(inter.area)))

    for f in fps:
        e = ext[f.ref]
        outside = e.difference(model.outline)
        decl = edges.get(f.ref)
        if decl:
            line = edge_line(model.outline, decl["edge"])
            if e.distance(line) > EDGE_TOL:
                c = e.centroid
                v.append(checklib.violation(
                    "place", "error", (c.x, c.y), None, None, [f.ref],
                    f"{f.ref} declared on edge '{decl['edge']}' but is "
                    f"{e.distance(line):.1f} mm away", SOURCE,
                    kind="edge_violation", edge=decl["edge"],
                    dist_mm=checklib.rnd(e.distance(line))))
            if outside.area > EPS_AREA:
                # overhang across the declared edge is allowed (connector
                # bodies legitimately hang off), but the part must still
                # meaningfully sit on the board
                if e.intersection(model.outline).area < ON_BOARD_MIN * e.area:
                    c = e.centroid
                    v.append(checklib.violation(
                        "place", "error", (c.x, c.y), None, None, [f.ref],
                        f"{f.ref} mostly outside the board outline", SOURCE,
                        kind="outside_outline",
                        outside_mm2=checklib.rnd(outside.area)))
        elif outside.area > EPS_AREA and f.is_movable:
            # board_only/locked infrastructure (mounting holes) may kiss the
            # outline by design - obstacles, not placement subjects
            c = e.centroid
            v.append(checklib.violation(
                "place", "error", (c.x, c.y), None, None, [f.ref],
                f"{f.ref} extends {outside.area:.2f} mm2 outside the board "
                f"outline", SOURCE, kind="outside_outline",
                outside_mm2=checklib.rnd(outside.area)))

        if f.is_movable:
            for poly, why in _forbidden(model, placement, f.side):
                inter = e.intersection(poly)
                if inter.area > EPS_AREA:
                    c = inter.centroid
                    v.append(checklib.violation(
                        "place", "error", (c.x, c.y), None, None, [f.ref],
                        f"{f.ref} intersects {why} ({inter.area:.2f} mm2)",
                        SOURCE, kind="keepout_violation",
                        overlap_mm2=checklib.rnd(inter.area)))
        if f.courtyard_missing and f.is_movable:
            v.append(checklib.violation(
                "place", "warning", f.center_abs(), None, None, [f.ref],
                f"{f.ref} has no courtyard - pad bbox +0.25 mm used", SOURCE,
                kind="courtyard_missing"))
    return v


# ---------------------------------------------------------------- metrics

def hpwl(model: PlaceModel) -> dict:
    per = {}
    for net, pts in model.nets_with_pads().items():
        xs, ys = zip(*pts)
        per[net] = checklib.rnd((max(xs) - min(xs)) + (max(ys) - min(ys)))
    return {"total_mm": checklib.rnd(sum(per.values())), "by_net": per}


def _mst_edges(pts: list[tuple[float, float]]):
    """Prim MST over points; deterministic for a sorted input list."""
    n = len(pts)
    if n < 2:
        return []
    in_tree = [False] * n
    best = [(math.inf, -1)] * n
    in_tree[0] = True
    for j in range(1, n):
        best[j] = (math.dist(pts[0], pts[j]), 0)
    edges = []
    for _ in range(n - 1):
        j = min((j for j in range(n) if not in_tree[j]),
                key=lambda j: (best[j][0], j))
        edges.append((pts[best[j][1]], pts[j]))
        in_tree[j] = True
        for k in range(n):
            if not in_tree[k]:
                d = math.dist(pts[j], pts[k])
                if d < best[k][0]:
                    best[k] = (d, j)
    return edges


def flight_lines(model: PlaceModel) -> dict[str, list]:
    return {net: _mst_edges(pts)
            for net, pts in model.nets_with_pads().items()}


def crossings(model: PlaceModel) -> dict:
    """Pairs of MST flight-line segments of DIFFERENT nets that cross."""
    segs = [(net, LineString(e)) for net, edges in flight_lines(model).items()
            for e in edges if LineString(e).length > 1e-6]
    count, worst = 0, {}
    for i, (na, sa) in enumerate(segs):
        for nb, sb in segs[i + 1:]:
            if na != nb and sa.crosses(sb):
                count += 1
                key = tuple(sorted((na, nb)))
                worst[key] = worst.get(key, 0) + 1
    pairs = [{"nets": list(k), "crossings": c}
             for k, c in sorted(worst.items(), key=lambda kv: (-kv[1], kv[0]))]
    return {"count": count, "pairs": pairs[:20]}


def congestion(model: PlaceModel, cell_mm: float = 2.0) -> dict:
    minx, miny, maxx, maxy = model.outline.bounds
    cols = max(1, math.ceil((maxx - minx) / cell_mm))
    rows = max(1, math.ceil((maxy - miny) / cell_mm))
    demand: dict[tuple[int, int], int] = {}
    for _net, edges in flight_lines(model).items():
        for (ax, ay), (bx, by) in edges:
            length = math.dist((ax, ay), (bx, by))
            steps = max(1, math.ceil(length / (cell_mm / 2)))
            cells = set()
            for s in range(steps + 1):
                t = s / steps
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                i = min(cols - 1, max(0, int((x - minx) / cell_mm)))
                j = min(rows - 1, max(0, int((y - miny) / cell_mm)))
                cells.add((i, j))
            for c in cells:
                demand[c] = demand.get(c, 0) + 1
    hot = sorted(demand.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return {"cell_mm": cell_mm, "cols": cols, "rows": rows,
            "max": max(demand.values()) if demand else 0,
            "mean_nonzero": checklib.rnd(sum(demand.values()) / len(demand))
            if demand else 0.0,
            "hotspots": [{"cell": list(c),
                          "center": [checklib.rnd(minx + (c[0] + .5) * cell_mm),
                                     checklib.rnd(miny + (c[1] + .5) * cell_mm)],
                          "demand": d} for c, d in hot]}
