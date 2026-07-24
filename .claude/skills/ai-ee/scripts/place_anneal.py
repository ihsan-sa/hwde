"""place_anneal - simulated-annealing placement refinement (S10, SPEC P6 stage 2).

SA over rigid CLUSTER positions/rotations (clusters = placelib.build_clusters
+ place_seed satellite slots - the same move unit and transform math as the
seed), starting from the board's current placement (normally place_seed
--apply output). The board file is never touched unless --apply-best; results
are emitted as ABSOLUTE op lists for place_edit.py.

Cost (raw term totals maintained incrementally, recombined with weights at
accept time):
  w_hpwl    * sum_net class_weight(net) * hpwl(net)     [gnd 0.25/pwr 0.6/sig 1]
  w_overlap * mm^2 of courtyard overlap + keepout overlap + outside-outline
              (ramped by sqrt(T0/T) so late epochs are effectively legal-only)
  w_cong    * congestion overflow (MST flight-line demand above --cong-cap
              per 2 mm cell; gnd-class nets excluded - they ride planes)
  w_cross   * weighted MST flight-line crossings (pair weight = w(a)*w(b))
  w_rule    * rule terms: high-current path length (current_a * hpwl of each
              constraints.power net), separation groups
              (placement.separation), thermal spreading (constraints.thermal)

Adaptive schedule: T0 from sampled uphill deltas; per-epoch cooling and move
window scaled by the epoch acceptance ratio (TimberWolf-style). Deterministic
per --seed: random.Random(seed) is the only entropy source; wall-clock is
reported but never steers the search.

Top-N: distinct best states are kept during the search; each candidate is
applied to the in-memory model, greedily repaired if it left minor illegality,
legality-checked (placelib), and emitted as cand<k>.ops.json + metrics.

Routability feedback (SPEC P6.2): --route-feedback needs the S11 DSN/
Freerouting path and exits 2 until S11 lands. The blending logic is BUILT and
testable now: anneal(..., route_probe=fn) probes the current best state every
--feedback-every epochs; completion c in [0,1] boosts congestion/crossing
weights by (1 + fb_gain*(1-c)) and candidate scores rank by
cost * (1 + w_feedback*(1-c)). S11 wires the real probe.

Exit 0 best candidate legal / 1 no legal candidate (best one's violations
reported) / 2 error.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from shapely import affinity
from shapely.prepared import prep

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))

import checklib  # noqa: E402
import placelib  # noqa: E402
import place_seed  # noqa: E402
from checklib import CheckError  # noqa: E402
from placelib import PlaceModel  # noqa: E402

EPS = placelib.EPS_AREA

DEFAULT_WEIGHTS = {
    "hpwl": 1.0,
    "overlap": 30.0,     # per mm^2 (before the T-ramp)
    "cong": 2.0,         # per overflow unit
    "cross": 2.0,        # per weighted crossing
    "rule": 1.0,
    "feedback": 0.5,     # candidate-score blend per (1 - completion)
}

# hpwl class weights (S9 spring precedent: planes carry gnd; power matters
# less than signal for wirelength but more than gnd)
W_GND, W_PWR, W_SIG = 0.25, 0.6, 1.0
# MST-term weights (crossings/congestion): gnd excluded entirely
MST_PWR, MST_SIG = 0.5, 1.0

FB_GAIN = 2.0            # cong/cross boost per (1 - completion)


def _class_sets(constraints: dict, decoupling: dict):
    power = {p.get("net") for p in (constraints or {}).get("power", [])}
    power |= {a.get("rail") for a in (decoupling or {}).get("associations", [])}
    power.discard(None)
    gnd = {"GND"} | {a.get("gnd", "GND")
                     for a in (decoupling or {}).get("associations", [])}
    return gnd, power


# ---------------------------------------------------------------- bodies

@dataclass
class Body:
    """A rigid cluster: anchor + slotted satellites, in the cluster frame
    (origin = anchor courtyard center, angle 0 = anchor local frame)."""
    cid: int
    cluster: placelib.Cluster
    slots: dict
    rel_poly: object              # shapely Polygon about the cluster origin
    pads: list                    # [(net, qx, qy), ...] cluster-frame coords
    side: str
    thru: bool
    kind: str                     # "free" | "edge" | "edge_fixed"

    @property
    def refs(self):
        return self.cluster.refs


def _build_bodies(model: PlaceModel, clusters, warnings) -> list[Body]:
    bodies = []
    for cid, c in enumerate(clusters):
        slots = place_seed.layout_satellites(model, c, warnings)
        rel_poly, ac = place_seed.cluster_rel_poly(model, c, slots)
        anchor = model.footprints[c.anchor]
        pads = []
        for p in anchor.pads:
            if p.net:
                pads.append((p.net, p.local[0] - ac[0], p.local[1] - ac[1]))
        thru = "through_hole" in anchor.attrs or any(p.through
                                                     for p in anchor.pads)
        for s in c.satellites:
            fp = model.footprints[s.ref]
            sc = fp.center_local()
            slot, rel = slots[s.ref]
            thru = thru or "through_hole" in fp.attrs or any(p.through
                                                             for p in fp.pads)
            for p in fp.pads:
                if not p.net:
                    continue
                lx, ly = _sat_pad_q(slot, ac, rel, p.local, sc)
                pads.append((p.net, lx, ly))
        kind = "free"
        if c.edge:
            kind = "edge_fixed" if c.edge.get("pos") is not None else "edge"
        bodies.append(Body(cid, c, slots, rel_poly, pads, anchor.side, thru,
                           kind))
    return bodies


def _sat_pad_q(slot, ac, rel, pad_local, sc):
    """Cluster-frame pad coord: (slot - ac) + R(-rel).(pad_local - sc)."""
    from geom import _rot
    dx, dy = _rot(pad_local[0] - sc[0], pad_local[1] - sc[1], -rel)
    return (slot[0] - ac[0] + dx, slot[1] - ac[1] + dy)


def _apply_state(model: PlaceModel, bodies: list[Body], centers, angles):
    for b in bodies:
        place_seed.apply_cluster(model, b.cluster, b.slots,
                                 centers[b.cid], angles[b.cid])


# ---------------------------------------------------------------- engine

class Engine:
    """Incremental cost evaluation over the cluster state.

    Raw term totals are maintained on every set_state(); cost() recombines
    them with the current weights. All updates are pure functions of the
    coordinates, so reverting a move restores the same values up to float
    accumulation - full_sync() (called every epoch) re-derives every total
    from scratch and kills the drift.
    """

    def __init__(self, model: PlaceModel, bodies: list[Body],
                 constraints: dict, decoupling: dict, *,
                 cell_mm: float = 2.0, cong_cap: int = 4,
                 weights: dict | None = None):
        self.model = model
        self.bodies = bodies
        self.weights = dict(DEFAULT_WEIGHTS)
        self.weights.update(weights or {})
        self.cell_mm = cell_mm
        self.cong_cap = cong_cap
        self.ov_ramp = 1.0        # annealer raises this as T falls
        self.fb_boost = 1.0       # route-feedback steering multiplier

        self.outline = model.outline
        self._outline_prep = prep(self.outline)
        placement = (constraints or {}).get("placement") or {}
        gnd, power = _class_sets(constraints, decoupling)
        self._wnet = {}
        self._wmst = {}
        self._gnd, self._power = gnd, power

        # --- pad registry: net -> [(cid | None, qx|x, qy|y), ...]
        in_cluster = {r for b in bodies for r in b.refs}
        entries: dict[str, list] = {}
        for b in bodies:
            for net, qx, qy in b.pads:
                entries.setdefault(net, []).append((b.cid, qx, qy))
        for ref in sorted(model.footprints):
            if ref in in_cluster:
                continue
            for _n, net, x, y in model.footprints[ref].pad_centers_abs():
                if net:
                    entries.setdefault(net, []).append((None, x, y))
        self.entries = {n: v for n, v in sorted(entries.items())
                        if len(v) >= 2}
        self.nets = sorted(self.entries)
        for n in self.nets:
            self._wnet[n] = W_GND if n in gnd else \
                W_PWR if n in power else W_SIG
            self._wmst[n] = 0.0 if n in gnd else \
                MST_PWR if n in power else MST_SIG
        self.mst_nets = [n for n in self.nets if self._wmst[n] > 0]
        self.nets_of_body = {
            b.cid: sorted({net for net, _x, _y in b.pads
                           if net in self.entries}) for b in bodies}

        # --- rule terms
        self.current_of = {p["net"]: float(p.get("current_a", 0.0))
                           for p in (constraints or {}).get("power", [])
                           if p.get("net") in self.entries}
        ref2cid = {r: b.cid for b in bodies for r in b.refs}
        self.sep_pairs = []
        for s in placement.get("separation", []):
            ca = sorted({ref2cid[r] for r in s.get("a", []) if r in ref2cid})
            cb = sorted({ref2cid[r] for r in s.get("b", []) if r in ref2cid})
            for i in ca:
                for j in cb:
                    if i != j:
                        self.sep_pairs.append(
                            (min(i, j), max(i, j),
                             float(s.get("min_mm", 5.0))))
        self.th_pairs = []
        th = [(ref2cid[t["ref"]], float(t.get("power_w", 0.0)))
              for t in (constraints or {}).get("thermal", [])
              if t.get("ref") in ref2cid]
        for a in range(len(th)):
            for b_ in range(a + 1, len(th)):
                (i, pa), (j, pb) = th[a], th[b_]
                if i != j and pa > 0 and pb > 0:
                    self.th_pairs.append((min(i, j), max(i, j), pa * pb))
        self.th_spread_mm = 10.0

        # --- obstacles / keepouts (fixed for the whole run)
        fixed_extra = set(placement.get("fixed", []))
        self.obstacles = []      # [(poly, side, thru)]
        for ref in sorted(model.footprints):
            f = model.footprints[ref]
            if ref in in_cluster:
                continue
            if not f.is_movable or ref in fixed_extra:
                thru = "through_hole" in f.attrs or any(p.through
                                                        for p in f.pads)
                self.obstacles.append((f.extents_abs(), f.side, thru))
        self.forbidden = {
            side: [p for p, _w in placelib._forbidden(model, placement, side)]
            for side in ("front", "back")}

        # --- congestion grid
        minx, miny, maxx, maxy = self.outline.bounds
        self._gx0, self._gy0 = minx, miny
        self._cols = max(1, math.ceil((maxx - minx) / cell_mm))
        self._rows = max(1, math.ceil((maxy - miny) / cell_mm))

        # --- state from the board's current placement
        self.centers, self.angles = [], []
        for b in bodies:
            anchor = model.footprints[b.cluster.anchor]
            self.centers.append(anchor.center_abs())
            self.angles.append(anchor.angle % 360.0)
        self._poly_cache: dict[tuple[int, float], object] = {}
        self.out_base = [0.0] * len(bodies)   # edge bodies' seed overhang
        self.full_sync()
        for b in bodies:
            if b.kind != "free":
                self.out_base[b.cid] = self.out_ov[b.cid]
        self._resync_overlap_totals()

    # ------------------------------------------------------------ helpers
    def poly_at(self, cid: int, center=None, angle=None):
        c = center if center is not None else self.centers[cid]
        a = angle if angle is not None else self.angles[cid]
        key = (cid, round(a % 360.0, 3))
        base = self._poly_cache.get(key)
        if base is None:
            base = affinity.rotate(self.bodies[cid].rel_poly, -a,
                                   origin=(0, 0))
            self._poly_cache[key] = base
        return affinity.translate(base, c[0], c[1])

    def _pair_collides(self, i: int, j: int) -> bool:
        a, b = self.bodies[i], self.bodies[j]
        return a.side == b.side or a.thru or b.thru

    def _outside_area(self, cid: int, poly) -> float:
        if self._outline_prep.contains_properly(poly):
            return 0.0
        out = poly.difference(self.outline).area
        return out if out > EPS else 0.0

    def _coords(self, net: str) -> list[tuple[float, float]]:
        pts = []
        for cid, qx, qy in self.entries[net]:
            if cid is None:
                pts.append((qx, qy))
            else:
                cx, cy = self.centers[cid]
                co, si = self._trig[cid]
                pts.append((cx + co * qx - si * qy, cy + si * qx + co * qy))
        return pts

    def _set_trig(self, cid: int) -> None:
        r = math.radians(-self.angles[cid])
        self._trig[cid] = (math.cos(r), math.sin(r))

    # ------------------------------------------------------------ MST bits
    def _mst_segs(self, net: str):
        return placelib._mst_edges(sorted(self.coords[net]))

    def _cells_of_segs(self, segs) -> dict:
        cell = self.cell_mm
        counts: dict[tuple[int, int], int] = {}
        for (ax, ay), (bx, by) in segs:
            length = math.dist((ax, ay), (bx, by))
            steps = max(1, math.ceil(length / (cell / 2)))
            cells = set()
            for s in range(steps + 1):
                t = s / steps
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                i = min(self._cols - 1, max(0, int((x - self._gx0) / cell)))
                j = min(self._rows - 1, max(0, int((y - self._gy0) / cell)))
                cells.add((i, j))
            for c in cells:
                counts[c] = counts.get(c, 0) + 1
        return counts

    def _cross_count(self, sa, sb) -> int:
        n = 0
        for (a1, a2) in sa:
            abx0 = min(a1[0], a2[0]); abx1 = max(a1[0], a2[0])
            aby0 = min(a1[1], a2[1]); aby1 = max(a1[1], a2[1])
            for (b1, b2) in sb:
                if min(b1[0], b2[0]) > abx1 or max(b1[0], b2[0]) < abx0 \
                        or min(b1[1], b2[1]) > aby1 \
                        or max(b1[1], b2[1]) < aby0:
                    continue
                if _seg_cross(a1, a2, b1, b2):
                    n += 1
        return n

    # ------------------------------------------------------------ full sync
    def full_sync(self) -> None:
        """Recompute every raw total from the current state."""
        self._trig = {}
        for b in self.bodies:
            self._set_trig(b.cid)
        self.coords = {n: self._coords(n) for n in self.nets}
        self.hpwl_raw = {n: _bbox_hp(self.coords[n]) for n in self.nets}
        self.hpwl_raw_total = sum(self.hpwl_raw.values())
        self.hpwl_w_total = sum(self._wnet[n] * v
                                for n, v in self.hpwl_raw.items())
        self.segs = {n: self._mst_segs(n) for n in self.mst_nets}
        self.cross: dict[tuple[str, str], int] = {}
        self.cross_total = 0.0
        for i, a in enumerate(self.mst_nets):
            for b in self.mst_nets[i + 1:]:
                c = self._cross_count(self.segs[a], self.segs[b])
                if c:
                    self.cross[(a, b)] = c
                    self.cross_total += c * self._wmst[a] * self._wmst[b]
        self.netcells = {n: self._cells_of_segs(self.segs[n])
                         for n in self.mst_nets}
        self.demand: dict[tuple[int, int], int] = {}
        for n in self.mst_nets:
            for c, k in self.netcells[n].items():
                self.demand[c] = self.demand.get(c, 0) + k
        self.overflow = sum(max(0, d - self.cong_cap)
                            for d in self.demand.values())
        self.polys = {b.cid: self.poly_at(b.cid) for b in self.bodies}
        self.pair_ov = {}
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                a = self._pair_overlap(i, j)
                if a > 0:
                    self.pair_ov[(i, j)] = a
        self.obst_ov = [self._obst_overlap(b.cid) for b in self.bodies]
        self.keep_ov = [self._keep_overlap(b.cid) for b in self.bodies]
        self.out_ov = [self._outside_area(b.cid, self.polys[b.cid])
                       for b in self.bodies]
        self._resync_overlap_totals()
        self.rule_total = self._rule_full()

    def _resync_overlap_totals(self) -> None:
        self.overlap_total = (
            sum(self.pair_ov.values()) + sum(self.obst_ov)
            + sum(self.keep_ov)
            + sum(max(0.0, o - b) for o, b in zip(self.out_ov, self.out_base)))

    def _pair_overlap(self, i: int, j: int) -> float:
        if not self._pair_collides(i, j):
            return 0.0
        pa, pb = self.polys[i], self.polys[j]
        (ax0, ay0, ax1, ay1) = pa.bounds
        (bx0, by0, bx1, by1) = pb.bounds
        if bx0 > ax1 or bx1 < ax0 or by0 > ay1 or by1 < ay0:
            return 0.0
        a = pa.intersection(pb).area
        return a if a > EPS else 0.0

    def _obst_overlap(self, cid: int) -> float:
        b = self.bodies[cid]
        poly = self.polys[cid]
        x0, y0, x1, y1 = poly.bounds
        tot = 0.0
        for opoly, oside, othru in self.obstacles:
            if not (b.side == oside or b.thru or othru):
                continue
            ox0, oy0, ox1, oy1 = opoly.bounds
            if ox0 > x1 or ox1 < x0 or oy0 > y1 or oy1 < y0:
                continue
            a = poly.intersection(opoly).area
            if a > EPS:
                tot += a
        return tot

    def _keep_overlap(self, cid: int) -> float:
        b = self.bodies[cid]
        poly = self.polys[cid]
        x0, y0, x1, y1 = poly.bounds
        tot = 0.0
        for k in self.forbidden[b.side]:
            kx0, ky0, kx1, ky1 = k.bounds
            if kx0 > x1 or kx1 < x0 or ky0 > y1 or ky1 < y0:
                continue
            a = poly.intersection(k).area
            if a > EPS:
                tot += a
        return tot

    def _rule_full(self) -> float:
        cur = sum(c * self.hpwl_raw.get(n, 0.0)
                  for n, c in self.current_of.items())
        sep = sum(max(0.0, m - math.dist(self.centers[i],
                                         self.centers[j])) ** 2
                  for i, j, m in self.sep_pairs)
        th = sum(pp * max(0.0, self.th_spread_mm
                          - math.dist(self.centers[i], self.centers[j]))
                 for i, j, pp in self.th_pairs)
        return cur + sep + th

    # ------------------------------------------------------------ moves
    def set_state(self, cid: int, center, angle) -> None:
        """Move one body and update every affected raw total."""
        self.centers[cid] = (center[0], center[1])
        self.angles[cid] = angle % 360.0
        self._set_trig(cid)

        for net in self.nets_of_body[cid]:
            pts = self._coords(net)
            self.coords[net] = pts
            new = _bbox_hp(pts)
            old = self.hpwl_raw[net]
            if new != old:
                self.hpwl_raw[net] = new
                self.hpwl_raw_total += new - old
                self.hpwl_w_total += self._wnet[net] * (new - old)
                c = self.current_of.get(net)
                if c:
                    self.rule_total += c * (new - old)

        changed = [n for n in self.nets_of_body[cid] if self._wmst[n] > 0]
        if changed:
            chset = set(changed)
            for net in changed:
                segs = self._mst_segs(net)
                self.segs[net] = segs
                old_cells = self.netcells[net]
                new_cells = self._cells_of_segs(segs)
                for c, k in old_cells.items():
                    d0 = self.demand[c]
                    d1 = d0 - k
                    self.demand[c] = d1
                    self.overflow += (max(0, d1 - self.cong_cap)
                                      - max(0, d0 - self.cong_cap))
                for c, k in new_cells.items():
                    d0 = self.demand.get(c, 0)
                    d1 = d0 + k
                    self.demand[c] = d1
                    self.overflow += (max(0, d1 - self.cong_cap)
                                      - max(0, d0 - self.cong_cap))
                self.netcells[net] = new_cells
            for net in changed:
                for other in self.mst_nets:
                    if other == net or (other in chset and other < net):
                        continue
                    key = (net, other) if net < other else (other, net)
                    old = self.cross.pop(key, 0)
                    if old:
                        self.cross_total -= old * self._wmst[net] \
                            * self._wmst[other]
                    c = self._cross_count(self.segs[net], self.segs[other])
                    if c:
                        self.cross[key] = c
                        self.cross_total += c * self._wmst[net] \
                            * self._wmst[other]

        poly = self.poly_at(cid)
        self.polys[cid] = poly
        for j in range(len(self.bodies)):
            if j == cid:
                continue
            key = (min(cid, j), max(cid, j))
            old = self.pair_ov.pop(key, 0.0)
            a = self._pair_overlap(*key)
            if a > 0:
                self.pair_ov[key] = a
            self.overlap_total += a - old
        for arr, fn in ((self.obst_ov, self._obst_overlap),
                        (self.keep_ov, self._keep_overlap)):
            old = arr[cid]
            new = fn(cid)
            arr[cid] = new
            self.overlap_total += new - old
        old_out = max(0.0, self.out_ov[cid] - self.out_base[cid])
        self.out_ov[cid] = self._outside_area(cid, poly)
        self.overlap_total += max(0.0, self.out_ov[cid]
                                  - self.out_base[cid]) - old_out

        if self.sep_pairs or self.th_pairs:
            self.rule_total = self._rule_partial_resync()

    def _rule_partial_resync(self) -> float:
        cur = sum(c * self.hpwl_raw.get(n, 0.0)
                  for n, c in self.current_of.items())
        sep = sum(max(0.0, m - math.dist(self.centers[i],
                                         self.centers[j])) ** 2
                  for i, j, m in self.sep_pairs)
        th = sum(pp * max(0.0, self.th_spread_mm
                          - math.dist(self.centers[i], self.centers[j]))
                 for i, j, pp in self.th_pairs)
        return cur + sep + th

    # ------------------------------------------------------------ cost
    def cost(self) -> float:
        w = self.weights
        return (w["hpwl"] * self.hpwl_w_total
                + w["overlap"] * self.ov_ramp * self.overlap_total
                + w["cong"] * self.fb_boost * self.overflow
                + w["cross"] * self.fb_boost * self.cross_total
                + w["rule"] * self.rule_total)

    def terms(self) -> dict:
        return {"hpwl_raw_mm": checklib.rnd(self.hpwl_raw_total),
                "hpwl_weighted": checklib.rnd(self.hpwl_w_total),
                "overlap_mm2": checklib.rnd(self.overlap_total),
                "cong_overflow": self.overflow,
                "crossings_weighted": checklib.rnd(self.cross_total),
                "rule": checklib.rnd(self.rule_total)}


def _bbox_hp(pts) -> float:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))


def _seg_cross(a1, a2, b1, b2) -> bool:
    """Proper crossing (interiors intersect); touches/collinear -> False."""
    d1 = _orient(b1, b2, a1)
    d2 = _orient(b1, b2, a2)
    if d1 == 0 or d2 == 0 or (d1 > 0) == (d2 > 0):
        return False
    d3 = _orient(a1, a2, b1)
    d4 = _orient(a1, a2, b2)
    return d3 != 0 and d4 != 0 and (d3 > 0) != (d4 > 0)


def _orient(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


# ---------------------------------------------------------------- annealer

@dataclass
class Params:
    seed: int = 1
    candidates: int = 3
    moves_per_cluster: int = 80
    max_epochs: int = 140
    stall: int = 15
    grid: float = 0.25
    cell_mm: float = 2.0
    cong_cap: int = 4
    edge_margin: float = 0.8
    feedback_every: int = 10
    weights: dict | None = None


class Annealer:
    def __init__(self, engine: Engine, params: Params, route_probe=None):
        self.e = engine
        self.p = params
        self.rng = random.Random(params.seed)
        self.route_probe = route_probe
        self.free = [b.cid for b in engine.bodies if b.kind == "free"]
        self.edge = [b.cid for b in engine.bodies if b.kind == "edge"]
        minx, miny, maxx, maxy = engine.outline.bounds
        self.w0 = 0.35 * math.hypot(maxx - minx, maxy - miny)
        self.window = self.w0
        self.completion = None
        self.trace: list[dict] = []

    # --------------------------------------------------------- proposals
    def _snap(self, v: float) -> float:
        g = self.p.grid
        return round(v / g) * g

    def _propose(self):
        """-> list of (cid, new_center, new_angle) or None."""
        e, rng = self.e, self.rng
        r = rng.random()
        if self.edge and r < 0.10:
            if len(self.edge) >= 2 and rng.random() < 0.35:
                i, j = rng.sample(self.edge, 2)
                bi, bj = e.bodies[i], e.bodies[j]
                if bi.cluster.edge["edge"] != bj.cluster.edge["edge"]:
                    return None
                axis = 1 if bi.cluster.edge["edge"] in ("left", "right") else 0
                ci, cj = e.centers[i], e.centers[j]
                ni = list(ci)
                nj = list(cj)
                ni[axis], nj[axis] = cj[axis], ci[axis]
                return [(i, tuple(ni), e.angles[i]),
                        (j, tuple(nj), e.angles[j])]
            cid = rng.choice(self.edge)
            return self._slide(cid)
        if not self.free:
            return None
        if r < 0.30:
            cid = rng.choice(self.free)
            ang = (e.angles[cid] + rng.choice((90.0, 180.0, 270.0))) % 360.0
            return [(cid, e.centers[cid], ang)]
        if r < 0.50 and len(self.free) >= 2:
            i, j = rng.sample(self.free, 2)
            return [(i, e.centers[j], e.angles[i]),
                    (j, e.centers[i], e.angles[j])]
        cid = rng.choice(self.free)
        cx, cy = e.centers[cid]
        w = max(self.p.grid, self.window)
        nx = self._snap(cx + (rng.random() * 2 - 1) * w)
        ny = self._snap(cy + (rng.random() * 2 - 1) * w)
        minx, miny, maxx, maxy = e.outline.bounds
        nx = min(maxx, max(minx, nx))
        ny = min(maxy, max(miny, ny))
        return [(cid, (nx, ny), e.angles[cid])]

    def _slide(self, cid: int):
        e, rng = self.e, self.rng
        b = e.bodies[cid]
        edge = b.cluster.edge["edge"]
        axis = 1 if edge in ("left", "right") else 0
        minx, miny, maxx, maxy = e.outline.bounds
        lo, hi = (miny, maxy) if axis == 1 else (minx, maxx)
        poly = e.polys[cid]
        px0, py0, px1, py1 = poly.bounds
        half = (py1 - py0) / 2 if axis == 1 else (px1 - px0) / 2
        c = list(e.centers[cid])
        t = c[axis] + (rng.random() * 2 - 1) * max(self.p.grid, self.window)
        t = min(hi - self.p.edge_margin - half,
                max(lo + self.p.edge_margin + half, self._snap(t)))
        c[axis] = t
        return [(cid, tuple(c), e.angles[cid])]

    # --------------------------------------------------------- mechanics
    def _try(self, moves) -> tuple[bool, float]:
        e = self.e
        before = e.cost()
        olds = [(cid, e.centers[cid], e.angles[cid]) for cid, _c, _a in moves]
        for cid, c, a in moves:
            e.set_state(cid, c, a)
        delta = e.cost() - before
        if delta <= 0 or (self.t > 0 and delta / self.t < 700
                          and self.rng.random() < math.exp(-delta / self.t)):
            return True, delta
        for cid, c, a in reversed(olds):
            e.set_state(cid, c, a)
        return False, delta

    def _estimate_t0(self) -> float:
        ups = []
        self.t = 0.0  # metropolis off: only downhill accepted during probe
        n = max(30, 4 * (len(self.free) + len(self.edge)))
        for _ in range(n):
            moves = self._propose()
            if not moves:
                continue
            e = self.e
            olds = [(cid, e.centers[cid], e.angles[cid])
                    for cid, _c, _a in moves]
            before = e.cost()
            for cid, c, a in moves:
                e.set_state(cid, c, a)
            d = e.cost() - before
            for cid, c, a in reversed(olds):
                e.set_state(cid, c, a)
            if d > 0:
                ups.append(d)
        base = sum(ups) / len(ups) if ups else max(1.0, 0.01 * self.e.cost())
        return 20.0 * base

    def snapshot(self):
        return (tuple(self.e.centers), tuple(self.e.angles))

    def _distinct(self, s1, s2) -> bool:
        for (c1, c2) in zip(s1[0], s2[0]):
            if abs(c1[0] - c2[0]) > 2.0 or abs(c1[1] - c2[1]) > 2.0:
                return True
        for (a1, a2) in zip(s1[1], s2[1]):
            if abs((a1 - a2) % 360.0) > 1.0:
                return True
        return False

    # --------------------------------------------------------- main loop
    def run(self) -> dict:
        e, p = self.e, self.p
        n_mov = len(self.free) + len(self.edge)
        if n_mov == 0:
            return {"pool": [(e.cost(), self.snapshot(), None)],
                    "moves": 0, "accepted": 0, "epochs": 0,
                    "t0": 0.0, "t_end": 0.0,
                    "note": "no movable clusters - nothing to anneal"}
        t0 = self._estimate_t0()
        e.full_sync()   # kill the apply/revert float drift from sampling
        self.t = t0
        moves_per_epoch = p.moves_per_cluster * n_mov
        best_cost = e.cost()
        best = self.snapshot()
        pool: list[tuple[float, tuple, float | None]] = [
            (best_cost, best, self.completion)]
        total_moves = total_acc = 0
        stall = 0
        epoch = 0
        for epoch in range(1, p.max_epochs + 1):
            e.ov_ramp = min(8.0, math.sqrt(t0 / max(self.t, 1e-9))) \
                if t0 > 0 else 1.0
            acc = 0
            tried = 0
            improved = False
            for _ in range(moves_per_epoch):
                moves = self._propose()
                if not moves:
                    continue
                tried += 1
                ok, _d = self._try(moves)
                if ok:
                    acc += 1
                    c = e.cost()
                    if c < best_cost - 1e-9:
                        best_cost = c
                        best = self.snapshot()
                        improved = True
                        self._pool_add(pool, c, best)
            total_moves += tried
            total_acc += acc
            alpha = acc / tried if tried else 0.0
            e.full_sync()   # kill float drift epoch by epoch
            if self.route_probe and epoch % p.feedback_every == 0:
                self._probe(best)
            self.trace.append({"epoch": epoch, "t": checklib.rnd(self.t, 6),
                               "alpha": checklib.rnd(alpha, 3),
                               "best": checklib.rnd(best_cost, 3),
                               "window": checklib.rnd(self.window, 2)})
            # stall only counts in the cold regime: at high T "best" rarely
            # improves and the counter would kill the run before the cold
            # phase where SA does its real work
            stall = 0 if (improved or alpha >= 0.2) else stall + 1
            if stall >= p.stall:
                break
            if self.t < t0 * 1e-4 and alpha < 0.02:
                break
            if alpha > 0.9:
                self.t *= 0.6
            elif alpha > 0.5:
                self.t *= 0.9
            elif alpha > 0.2:
                self.t *= 0.95
            elif alpha > 0.05:
                self.t *= 0.9
            else:
                self.t *= 0.75
            self.window = min(self.w0, max(2 * p.grid,
                                           self.window * (0.56 + alpha)))
        # quench: greedy descent from the best state
        t_end = self.t
        for cid, c, a in zip(range(len(e.bodies)), best[0], best[1]):
            e.set_state(cid, c, a)
        e.full_sync()
        e.ov_ramp = 8.0
        self.t = 0.0
        q_moves = 4 * n_mov * p.moves_per_cluster // 8
        self.window = max(2 * p.grid, 4 * p.grid)
        for _ in range(q_moves):
            moves = self._propose()
            if not moves:
                continue
            total_moves += 1
            ok, _d = self._try(moves)
            if ok:
                total_acc += 1
                c = e.cost()
                if c < best_cost - 1e-9:
                    best_cost = c
                    best = self.snapshot()
                    self._pool_add(pool, c, best)
        e.full_sync()
        self._pool_add(pool, e.cost(), self.snapshot())
        return {"pool": pool, "moves": total_moves, "accepted": total_acc,
                "epochs": epoch, "t0": t0, "t_end": t_end}

    def _pool_add(self, pool, cost, state) -> None:
        pool.append((cost, state, self.completion))
        pool.sort(key=lambda x: x[0])
        del pool[4 * self.p.candidates:]

    def _probe(self, best_state) -> None:
        _apply_state(self.e.model, self.e.bodies, best_state[0],
                     best_state[1])
        c = float(self.route_probe(self.e.model))
        self.completion = min(1.0, max(0.0, c))
        self.e.fb_boost = 1.0 + FB_GAIN * (1.0 - self.completion)


# ---------------------------------------------------------------- repair

def _repair(model: PlaceModel, engine: Engine, placement: dict | None,
            grid: float = 0.25, max_r_mm: float = 6.0) -> bool:
    """Greedy spiral nudge for clusters left in minor illegality. Mutates the
    model AND engine state so caller reads consistent ops. Returns True if
    anything moved."""
    viol = placelib.legality_violations(model, placement)
    ref2cid = {r: b.cid for b in engine.bodies for r in b.refs}
    bad = sorted({ref2cid[r] for v in viol if v["severity"] == "error"
                  for r in v.get("refs", []) if r in ref2cid})
    if not bad:
        return False
    moved = False
    for cid in bad:
        b = engine.bodies[cid]
        if b.kind == "edge_fixed":
            continue
        cur = engine.centers[cid]
        ang = engine.angles[cid]
        axis = None
        if b.kind == "edge":
            axis = 1 if b.cluster.edge["edge"] in ("left", "right") else 0
        found = None
        steps = int(max_r_mm / grid)
        for r in range(1, steps + 1):
            cands = []
            if axis is None:
                for i in range(-r, r + 1):
                    for j in range(-r, r + 1):
                        if max(abs(i), abs(j)) != r:
                            continue
                        cands.append((cur[0] + i * grid, cur[1] + j * grid))
            else:
                for s in (r, -r):
                    c = list(cur)
                    c[axis] += s * grid
                    cands.append(tuple(c))
            for cand in sorted(cands, key=lambda c_: (
                    (c_[0] - cur[0]) ** 2 + (c_[1] - cur[1]) ** 2,
                    c_[1], c_[0])):
                if _spot_legal(engine, cid, cand, ang):
                    found = cand
                    break
            if found:
                break
        if found:
            engine.set_state(cid, found, ang)
            moved = True
    if moved:
        engine.full_sync()
        _apply_state(model, engine.bodies, engine.centers, engine.angles)
    return moved


def _spot_legal(engine: Engine, cid: int, center, angle) -> bool:
    poly = engine.poly_at(cid, center, angle)
    b = engine.bodies[cid]
    if b.kind == "free" and engine._outside_area(cid, poly) > 0:
        return False
    x0, y0, x1, y1 = poly.bounds
    for j, other in enumerate(engine.bodies):
        if j == cid or not engine._pair_collides(cid, j):
            continue
        ox0, oy0, ox1, oy1 = engine.polys[j].bounds
        if ox0 > x1 or ox1 < x0 or oy0 > y1 or oy1 < y0:
            continue
        if poly.intersection(engine.polys[j]).area > EPS:
            return False
    for opoly, oside, othru in engine.obstacles:
        if not (b.side == oside or b.thru or othru):
            continue
        if poly.intersection(opoly).area > EPS:
            return False
    for k in engine.forbidden[b.side]:
        if poly.intersection(k).area > EPS:
            return False
    return True


# ---------------------------------------------------------------- driver

def anneal(pcb: Path, constraints: dict, decoupling: dict, params: Params,
           route_probe=None):
    """-> (candidates, facts, model). Candidates: list of dicts sorted by
    blended score; each carries state ops + legality. Board file untouched."""
    t_start = time.perf_counter()
    model = PlaceModel(pcb)
    placement = (constraints or {}).get("placement") or {}
    hpwl_input = placelib.hpwl(model)["total_mm"]

    clusters, warnings = placelib.build_clusters(model, decoupling, placement)
    bodies = _build_bodies(model, clusters, warnings)
    engine = Engine(model, bodies, constraints, decoupling,
                    cell_mm=params.cell_mm, cong_cap=params.cong_cap,
                    weights=params.weights)
    ann = Annealer(engine, params, route_probe=route_probe)
    start_terms = engine.terms()
    result = ann.run()

    # distinct top-N
    chosen: list[tuple[float, tuple, float | None]] = []
    for cost, state, comp in result["pool"]:
        if any(not ann._distinct(state, s) for _c, s, _f in chosen):
            continue
        chosen.append((cost, state, comp))
        if len(chosen) >= params.candidates:
            break
    if not chosen:
        chosen = result["pool"][:1]

    candidates = []
    for k, (cost, state, comp) in enumerate(chosen):
        # snapshots taken before the first probe carry no completion; the
        # last probe is the best estimate for all near-final states
        if comp is None:
            comp = ann.completion
        for cid in range(len(bodies)):
            engine.set_state(cid, state[0][cid], state[1][cid])
        engine.full_sync()
        _apply_state(model, bodies, engine.centers, engine.angles)
        repaired = _repair(model, engine, placement, grid=params.grid)
        viol = placelib.legality_violations(model, placement)
        errors = [v for v in viol if v["severity"] == "error"]
        ops = []
        for b in bodies:
            for ref in b.refs:
                fp = model.footprints[ref]
                ops.append({"op": "place", "ref": ref,
                            "x": checklib.rnd(fp.pos[0]),
                            "y": checklib.rnd(fp.pos[1]),
                            "deg": checklib.rnd(fp.angle % 360.0),
                            "side": fp.side})
        terms = engine.terms()
        final_cost = engine.cost()
        score = final_cost * (1.0 + engine.weights["feedback"]
                              * (1.0 - comp)) if comp is not None \
            else final_cost
        candidates.append({
            "rank": k + 1,
            "cost": checklib.rnd(final_cost, 3),
            "score": checklib.rnd(score, 3),
            "hpwl_mm": terms["hpwl_raw_mm"],
            "terms": terms,
            "legal": not errors,
            "repaired": repaired,
            "completion": comp,
            "violations": viol,
            "ops": ops,
        })
    candidates.sort(key=lambda c: (not c["legal"], c["score"]))
    for k, c in enumerate(candidates):
        c["rank"] = k + 1

    best = candidates[0]
    facts = {
        "seed": params.seed,
        "clusters": len(bodies),
        "movable_clusters": len(ann.free) + len(ann.edge),
        "hpwl_input_mm": hpwl_input,
        "hpwl_start_mm": start_terms["hpwl_raw_mm"],
        "hpwl_best_mm": best["hpwl_mm"],
        "improvement_pct": checklib.rnd(
            100.0 * (hpwl_input - best["hpwl_mm"]) / hpwl_input, 2)
        if hpwl_input else None,
        "start_terms": start_terms,
        "epochs": result["epochs"],
        "moves": result["moves"],
        "accepted": result["accepted"],
        "t0": checklib.rnd(result["t0"], 4),
        "t_end": checklib.rnd(result["t_end"], 6),
        "feedback_used": route_probe is not None,
        "last_completion": ann.completion,
        "runtime_s": checklib.rnd(time.perf_counter() - t_start, 2),
        "warnings": warnings,
    }
    if "note" in result:
        facts["note"] = result["note"]
    return candidates, facts, model


def make_route_probe(pcb: Path, *, passes: int = 4, timeout_s: int = 180):
    """S11 routability probe for --route-feedback (PROGRESS S10 -> S11).

    Returns fn(model: PlaceModel) -> completion fraction [0, 1]: snapshot the
    model's placement onto a scratch copy of the board (place_edit absolute
    ops), then run route_auto.route_probe (DSN export + capped-effort
    Freerouting, no SES import). A probe failure returns 0.0 - the annealer
    treats an unprobeable placement as unroutable rather than crashing the
    run.
    """
    import shutil

    import place_edit  # noqa: PLC0415 - lazy, only with --route-feedback
    import route_auto  # noqa: PLC0415

    pcb = Path(pcb).resolve()
    work = pcb.parent / "route_probe_anneal"

    def probe(model) -> float:
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        staged = work / pcb.name
        for src in pcb.parent.glob(pcb.stem + ".*"):
            if src.is_file() and not src.name.endswith(".lck"):
                shutil.copy2(src, work / src.name)
        ops = [{"op": "place", "ref": ref, "x": fp.pos[0], "y": fp.pos[1],
                "deg": fp.angle, "side": fp.side}
               for ref, fp in sorted(model.footprints.items())]
        try:
            place_edit.apply_ops(staged, ops)
            facts = route_auto.route_probe(
                staged, passes=passes, timeout_s=timeout_s,
                work_dir=work / "probe")
        except CheckError:
            return 0.0
        c = facts.get("completion")
        return float(c) if c is not None else 0.0

    return probe


def run(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--constraints", default=None,
                    help="constraints.json (default: next to the board)")
    ap.add_argument("--decoupling", default=None,
                    help="decoupling.json (default: next to the board)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--out-dir", default=None,
                    help="candidate ops dir (default: <board dir>/anneal)")
    ap.add_argument("--apply-best", action="store_true",
                    help="apply the best legal candidate via place_edit")
    ap.add_argument("--route-feedback", action="store_true",
                    help="blend fast-route completion into cost (S11 probe: "
                         "place_edit snapshot -> DSN -> capped Freerouting)")
    ap.add_argument("--feedback-every", type=int, default=10)
    ap.add_argument("--probe-passes", type=int, default=4,
                    help="Freerouting passes per feedback probe")
    ap.add_argument("--probe-timeout-s", type=int, default=180)
    ap.add_argument("--moves-per-cluster", type=int, default=80)
    ap.add_argument("--max-epochs", type=int, default=140)
    ap.add_argument("--stall", type=int, default=15)
    ap.add_argument("--grid-mm", type=float, default=0.25)
    ap.add_argument("--cell-mm", type=float, default=2.0)
    ap.add_argument("--cong-cap", type=int, default=4)
    ap.add_argument("--edge-margin-mm", type=float, default=0.8)
    for name in ("hpwl", "overlap", "cong", "cross", "rule", "feedback"):
        ap.add_argument(f"--w-{name}", type=float, default=None)
    ap.add_argument("--out-report", default=None)
    args = ap.parse_args(argv)

    pcb = Path(args.pcb)
    if not pcb.is_file():
        raise CheckError(f"board not found: {pcb}")

    route_probe = None
    if args.route_feedback:
        route_probe = make_route_probe(pcb, passes=args.probe_passes,
                                       timeout_s=args.probe_timeout_s)

    def sidecar(explicit, name):
        if explicit:
            return checklib.load_json(explicit, name)
        p = pcb.parent / name
        return checklib.load_json(p, name) if p.is_file() else {}

    constraints = sidecar(args.constraints, "constraints.json")
    decoupling = sidecar(args.decoupling, "decoupling.json")

    weights = {}
    for name in ("hpwl", "overlap", "cong", "cross", "rule", "feedback"):
        v = getattr(args, f"w_{name}")
        if v is not None:
            weights[name] = v
    params = Params(seed=args.seed, candidates=args.candidates,
                    moves_per_cluster=args.moves_per_cluster,
                    max_epochs=args.max_epochs, stall=args.stall,
                    grid=args.grid_mm, cell_mm=args.cell_mm,
                    cong_cap=args.cong_cap, edge_margin=args.edge_margin_mm,
                    feedback_every=args.feedback_every,
                    weights=weights or None)

    candidates, facts, _model = anneal(pcb, constraints, decoupling, params,
                                       route_probe=route_probe)

    out_dir = Path(args.out_dir) if args.out_dir else pcb.parent / "anneal"
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in candidates:
        f = out_dir / f"cand{c['rank']}.ops.json"
        f.write_text(json.dumps({"version": 1, "ops": c["ops"]}, indent=1),
                     encoding="utf-8")
        c["ops_file"] = str(f)
    best = candidates[0]

    if args.apply_best:
        if not best["legal"]:
            raise CheckError("no legal candidate to apply "
                             f"({len(best['violations'])} violations on best)")
        import place_edit
        place_edit.apply_ops(pcb, best["ops"])
        facts["applied"] = True
        facts["hpwl_applied_mm"] = placelib.hpwl(
            PlaceModel(pcb))["total_mm"]

    slim = [{k: v for k, v in c.items() if k not in ("ops", "violations")}
            | {"n_violations": len(c["violations"])}
            for c in candidates]
    payload = checklib.report("place_anneal", str(pcb), best["violations"],
                              candidates=slim, **facts)
    return payload, args.out_report


def main(argv: list[str] | None = None) -> int:
    return checklib.cli_wrap("place_anneal", lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
