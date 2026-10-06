"""check_current.py - trace width vs current per power net (SPEC 6.3).

Per net in constraints.json["power"] with a budgeted current:
 - every track segment's width is compared against the IPC-2152 minimum for
   the full budget at dT (worst case: no per-branch current attribution -
   the whole rail may flow through any segment; override per region below);
 - pour neckdowns: each zone fill is eroded by required_width/2 - if the
   net's via attachment points then fall in separate components, the pour
   necks below the requirement between them (polygon-erosion equivalent of
   the spec's medial-axis min-width);
 - layer transitions: net vias are clustered (<= 2 mm) and each cluster needs
   ceil(I / via_amps) vias (default 0.5 A per via, per spec).

Pad-exit necks (PCB-0019-A SW_L1/SW_L2: 0.30 mm off a TPS63001's 0.24 mm
pads at 0.5 mm pitch, where a 0.5 mm track breaks clearance to the next pin,
so no layout clears the finding). A run of undersized same-net, same-layer
segments touching end to end is accepted, not reported, when all hold:
 1. one of its segments ends on a same-net pad on that layer;
 2. every segment is at least min(required, w_pad) wide, where w_pad is the
    short side of the narrowest pad the run touches - the pad already
    constricts the current to w_pad, so a track no narrower than the copper
    it leaves adds no tighter section (a pad as wide as the requirement
    leaves nothing to excuse, so the full rule applies);
 3. the run's centerline outside the net's other copper on that layer (pads,
    vias, zone fill, the tracks not in the run) totals <= PAD_EXIT_MAX_MM.
    This bounds the neck to the pad's escape: a sub-millimetre neck between
    wide copper at both ends is heat-sunk by it, which IPC-2152's
    long-conductor charts do not describe; a longer one is a routed trace
    and must meet the full width.
Accepted runs are listed in facts["pad_exit_necks"] for the reviewer.

Pour connectivity is judged across layers (PCB-0017-B GND: the F.Cu fill is
split into islands, each stitched to one unbroken B.Cu pour). When a fill on
one layer is eroded, the net's fills on every other layer are eroded by
their own required_width/2, and the pieces are joined through every same-net
via and plated through-hole whose layers both pieces sit on. The attachment
vias of the fill under test must all land in one joined component. Pieces on
the SAME layer are never joined through a via alone (a via touching two
same-layer pieces and nothing else is not a path), so a single-layer pour is
judged exactly as before. Via ampacity at those stitches stays the
transition-via rule's job.

Override reach (LEARNINGS 2026-07-28/29: overrides used to feed only track
widths, making the via rule net-wide and unsatisfiable for branch taps):
 - a via CLUSTER whose centroid falls inside an override region is judged at
   the override current (need = ceil(override / via_amps));
 - a pour NECK is first evaluated at the full budget; if the failing neck's
   reported position falls inside an override region the fill is re-tested at
   the override requirement - passing drops the violation, failing re-emits
   the re-test's neck at the override current. Approximation: the re-test's
   neck position may itself land outside the region (the reported point is a
   representative sample of the split, not the whole neck).

Every undersized_track violation carries extras "bridge": true|false - true
when the segment is a cut edge of the net's connectivity graph (tracks + vias
+ pads + zone fills, lib/netconn.py), i.e. the sole path: the whole judged
current really crosses it. false = a parallel same-net path exists (which may
still be jointly undersized - severity is NOT reduced; the label is for the
fixer, LEARNINGS 2026-07-29 "no bridge awareness").

Two non-bridge cases are dropped instead (PCB-0018-A: signal taps that
leave FET pins sitting in the PHASE/LS_SRC pour that carries the phase
current), and listed by position in facts["pour_taps"]:
 - pour-shunted: both ends sit on the net's pour - inside its fill on the
   track's layer, or on a same-net pad or via whose copper touches a
   same-net fill on any layer. The track is in parallel with that pour, so
   the pour carries the current, and the pour-neck pass judges the pour;
 - inside pad copper: the track lies wholly inside same-net pad and via
   copper on its layer (a stub drawn over a pad adds no section).
A bridge is never dropped: when it is the sole path, the whole judged
current may cross it, and only a declared override can say otherwise.

Plane-fed rails ("plane_fed": true on the entry): the rail's trunk is its
zone fill, so every via is a single-pin leaf tap by construction and the
net-wide budget is unattributable per cluster/segment (LEARNINGS 2026-07-29:
27 one-via clusters on +3V3, doubling infeasible). Semantics:
 - no zone fill anywhere on the net -> error "plane_missing", then the entry
   is checked as if plane_fed were false;
 - pour necks: unchanged, error at the full budget (a trunk neck is real);
 - via clusters / track segments OUTSIDE any override region: still checked
   at the full budget but downgraded to severity "warning" with extras
   advisory=true (a labeled worst-case screen);
 - INSIDE an override region: error at the override current (a declared
   regulator-feed tap stays enforceable).

IPC-2152 basis: 10 degC chart readings at 1 oz outer copper (interpolation
table vendored from kicad-happy, MIT), converted to copper cross-section so
inner layers scale by their (thinner) copper thickness from geom's stackup.
Below the first table row the requirement interpolates linearly to (0, 0),
consistent with published chart readings (~0.20 mm at 0.4 A). dT != 10 scales
the equivalent current by (10/dT)^0.44 (IPC curve-family approximation).

Derived return-net coverage (T6; the pd-trigger 5A GND choke class): no board
ever declares its return net, so return-path ampacity went unchecked - the
worst real defect of any run (5A return choked through 0.2 mm GND necks rated
0.80 A, caught only by the reviewer AFTER verify passed 8/8). When the largest
declared rail is >= RETURN_SYNTH_MIN_A (3.0 A) and the return net (optional
per-entry "return_net", default "GND") exists on the board with a zone fill
and is not itself declared, ONE entry is synthesized for it at the max rail's
budget with plane-fed semantics. ALL derived findings - pour necks included -
are advisory warnings with extras derived=true: the budget is a heuristic
(max of declared rails), so error severity is not justified (measured: the
SHIPPED pd-trigger board necks 0.86 mm vs the 1.75 mm 5 A requirement on a
plane fed from multiple directions). Below the threshold the screen is noise:
the rf4 golden fires a 0.07 mm sliver neck at a 0.15 A budget.

CLI: --pcb board.kicad_pcb --constraints constraints.json [--out report.json]
     exit 0/1/2 per SPEC section 6.

constraints.json["power"] entries:
    {"net": "+3V3",              # required, exact board net name
     "current_a": 0.4,           # required, budgeted rail current
     "dt_c": 10,                 # optional temperature rise (default 10)
     "via_amps": 0.5,            # optional per-via ampacity (default 0.5)
     "plane_fed": true,          # optional, see plane-fed semantics above
     "overrides": [              # optional per-region current attribution
        {"near": [x, y], "radius_mm": 2.0, "current_a": 0.1}]}
Segments whose midpoint (via clusters: centroid; pour necks: reported neck
position) falls in an override region are checked against the override
current instead of the full budget (branch traces / taps).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from shapely import STRtree
from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
import geom  # noqa: E402
import netconn  # noqa: E402
from checklib import CheckError, violation  # noqa: E402

SCRIPT = "check_current"
# IPC-2152 minimum trace width (mm) at 1 oz outer copper, dT = 10 degC.
# Chart-reading interpolation table vendored from kicad-happy (MIT).
IPC2152_1OZ_10C = [(0.0, 0.0), (0.5, 0.25), (1.0, 0.50), (2.0, 1.10),
                   (3.0, 1.80), (5.0, 3.50), (7.0, 5.50), (10.0, 9.0)]
OZ1_MM = 0.035                 # 1 oz copper thickness the table assumes
VIA_AMPS_DEFAULT = 0.5         # spec: >= 1 via per 0.5 A at transitions
VIA_CLUSTER_MM = 2.0           # vias within this distance share current
WIDTH_TOL_MM = 1e-3
RETURN_SYNTH_MIN_A = 3.0       # derive return-net coverage at/above this rail
PLANE_HINT_SINGLE_VIA_FRAC = 0.8  # plane_fed_candidate hint threshold
PAD_EXIT_MAX_MM = 1.0          # longest accepted pad-exit neck (docstring)
TOUCH_MM = 1e-3                # end-to-end / end-on-pad contact tolerance


def width_1oz_10c(current_a: float) -> float:
    """Table interpolation; linear extrapolation beyond the last row."""
    pts = IPC2152_1OZ_10C
    if current_a <= 0:
        return 0.0
    for (i0, w0), (i1, w1) in zip(pts, pts[1:]):
        if current_a <= i1:
            return w0 + (current_a - i0) / (i1 - i0) * (w1 - w0)
    (i0, w0), (i1, w1) = pts[-2], pts[-1]
    return w1 + (current_a - i1) / (i1 - i0) * (w1 - w0)


def required_width_mm(current_a: float, dt_c: float, cu_mm: float) -> float:
    """Minimum width on a layer with `cu_mm` copper for current at dT."""
    i_equiv = current_a * (10.0 / dt_c) ** 0.44 if dt_c > 0 else current_a
    area_mm2 = width_1oz_10c(i_equiv) * OZ1_MM
    return area_mm2 / cu_mm


def cluster_vias(vias: list, max_gap: float = VIA_CLUSTER_MM) -> list[list]:
    """Union-find grouping of vias by center distance <= max_gap."""
    parent = list(range(len(vias)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            d = math.hypot(vias[i].at[0] - vias[j].at[0],
                           vias[i].at[1] - vias[j].at[1])
            if d <= max_gap:
                parent[find(i)] = find(j)
    groups: dict[int, list] = {}
    for i, v in enumerate(vias):
        groups.setdefault(find(i), []).append(v)
    return list(groups.values())


def region_current(entry: dict, pos) -> float | None:
    """Override current for a position, or None when no region covers it."""
    for ov in entry.get("overrides", []):
        near = ov.get("near")
        if near and math.hypot(pos[0] - near[0],
                               pos[1] - near[1]) <= ov.get("radius_mm", 2.0):
            return float(ov["current_a"])
    return None


def segment_current(entry: dict, midpoint) -> float:
    ov = region_current(entry, midpoint)
    return float(entry["current_a"]) if ov is None else ov


def pad_exit_necks(bg: geom.BoardGeom, net: str, thin: list) -> dict:
    """Accepted pad-exit necks (module docstring). `thin` lists
    (Track, required_mm) for every undersized segment of `net`; returns
    {id(Track): info} for the segments of each accepted run."""
    accepted: dict[int, dict] = {}
    by_layer: dict[str, list] = {}
    for t, req in thin:
        by_layer.setdefault(t.layer, []).append((t, req))
    for layer, items in by_layer.items():
        # runs = undersized segments touching end to end (union-find)
        parent = list(range(len(items)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][0].shape.distance(items[j][0].shape) <= TOUCH_MM:
                    parent[find(i)] = find(j)
        runs: dict[int, list] = {}
        for i, it in enumerate(items):
            runs.setdefault(find(i), []).append(it)
        pads = bg.pads_of(net, layer)
        for run in runs.values():
            ends = [Point(c) for t, _ in run
                    for c in (t.shape.coords[0], t.shape.coords[-1])]
            touched = [p for p in pads
                       if any(p.poly.distance(e) <= TOUCH_MM for e in ends)]
            if not touched:
                continue                        # 1. not a pad exit
            w_pad = min(min(p.size) for p in touched)
            if any(t.width + WIDTH_TOL_MM < min(req, w_pad) for t, req in run):
                continue                        # 2. narrower than the pad
            ids = {id(t) for t, _ in run}
            anchor = [p.poly for p in pads] + \
                [v.poly for v in bg.vias_of(net, layer)] + \
                [t.poly for t in bg.tracks_of(net, layer) if id(t) not in ids] + \
                [z.fill_on(layer) for z in bg.zones_of(net, layer)]
            line = unary_union([t.shape for t, _ in run])
            free = line.difference(unary_union(anchor)).length
            if free > PAD_EXIT_MAX_MM + WIDTH_TOL_MM:
                continue                        # 3. longer than an escape
            pad = min(touched, key=lambda p: min(p.size))
            info = {"pad": f"{pad.ref}.{pad.number}", "layer": layer,
                    "pad_width_mm": checklib.rnd(w_pad),
                    "neck_mm": checklib.rnd(min(t.width for t, _ in run)),
                    "length_mm": checklib.rnd(free)}
            for t, _ in run:
                accepted[id(t)] = info
    return accepted


def pour_shunted(bg: geom.BoardGeom, net: str, t) -> bool:
    """True when both ends of track `t` sit on the net's pour: inside its
    fill on t's layer, or on a same-net pad or via whose copper touches a
    same-net fill on any layer (module docstring, pour taps)."""
    fills = {l: bg.zone_fill(net, l) for l in bg.layers_with_zone(net)}
    if not fills:
        return False
    own = fills.get(t.layer)
    items = bg.pads_of(net, t.layer) + bg.vias_of(net, t.layer)

    def anchored(xy) -> bool:
        p = Point(xy)
        if own is not None and own.buffer(TOUCH_MM).contains(p):
            return True
        return any(it.poly.buffer(TOUCH_MM).contains(p)
                   and any(fills[l].intersects(it.poly)
                           for l in it.layers if l in fills)
                   for it in items)
    return anchored(t.shape.coords[0]) and anchored(t.shape.coords[-1])


def inside_pad_copper(bg: geom.BoardGeom, net: str, t) -> bool:
    """True when track `t` lies wholly inside same-net pad and via copper
    on its layer: a stub drawn over a pad adds no section of its own."""
    cover = [p.poly for p in bg.pads_of(net, t.layer)] + \
        [v.poly for v in bg.vias_of(net, t.layer)]
    if not cover:
        return False
    return t.shape.difference(unary_union(cover)).length <= TOUCH_MM


def _stitches(bg: geom.BoardGeom, net: str) -> list:
    """(Point, layers) of every same-net via and plated through-hole: the
    places where fills on different layers join."""
    out = [(Point(v.at), frozenset(v.layers)) for v in bg.vias_of(net)]
    out += [(Point(p.center), frozenset(p.layers)) for p in bg.pads_of(net)
            if p.drill is not None and len(p.layers) > 1]
    return out


def _pieces(fill, radius: float) -> list:
    eroded = fill.buffer(-radius) if radius > 0 else fill
    return [] if eroded.is_empty else list(getattr(eroded, "geoms", [eroded]))


def pour_neck(bg: geom.BoardGeom, net: str, layer: str, fill,
              required: float, others: dict | None = None):
    """None if the pour carries `required` width between all via attachments,
    else (neck_width_mm, pos) of the tightest failing neck.

    `others` maps every other copper layer with a fill of this net to
    (fill, required_mm on that layer); pieces join across layers through
    same-net vias and plated through-holes (module docstring)."""
    pts = [Point(v.at) for v in bg.vias_of(net, layer)
           if fill.buffer(0.01).contains(Point(v.at))]
    if len(pts) < 2:
        return None
    others = {l: o for l, o in (others or {}).items()
              if l != layer and not o[0].is_empty}
    stitches = [(p, ls) for p, ls in _stitches(bg, net)
                if layer in ls and any(l in ls for l in others)]
    # other layers' pieces are fixed at their own requirement: erode once
    other_nodes = []                     # (layer, reach polygon)
    for l, (ofill, oreq) in others.items():
        r = oreq / 2.0
        other_nodes += [(l, part.buffer(r + 0.01)) for part in _pieces(ofill, r)]

    def connected(radius: float) -> bool:
        own = [part.buffer(radius + 0.01) for part in _pieces(fill, radius)]
        if not own:
            return False
        nodes = [(layer, g) for g in own] + other_nodes
        parent = list(range(len(nodes)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        if stitches and other_nodes:
            tree = STRtree([g for _, g in nodes])
            for p, ls in stitches:
                hit = [int(i) for i in tree.query(p, predicate="intersects")
                       if nodes[int(i)][0] in ls]
                if len({nodes[i][0] for i in hit}) < 2:
                    continue             # same-layer pieces only: no path
                for i in hit[1:]:
                    parent[find(i)] = find(hit[0])
        common = None
        for p in pts:
            comps = {find(i) for i, g in enumerate(own) if g.contains(p)}
            common = comps if common is None else common & comps
            if not common:
                return False
        return True
    if connected(required / 2.0):
        return None
    lo, hi = 0.0, required / 2.0    # lo connected, hi not
    for _ in range(12):
        mid = (lo + hi) / 2.0
        if connected(mid):
            lo = mid
        else:
            hi = mid
    # locate approximately: centroid gap between split components
    eroded = fill.buffer(-hi)
    parts = list(getattr(eroded, "geoms", [eroded])) if not eroded.is_empty else []
    pos = parts[0].representative_point().coords[0] if parts else \
        fill.representative_point().coords[0]
    return 2.0 * lo, pos


def check_net(bg: geom.BoardGeom, entry: dict):
    net = entry.get("net")
    if not net:
        raise CheckError('power entry without "net"')
    if net not in bg.nets:
        raise CheckError(f"power net {net!r} not on board "
                         f"(nets: {sorted(n for n in bg.nets if n)})")
    if "current_a" not in entry:
        raise CheckError(f'power entry {net!r} without "current_a"')
    budget = float(entry["current_a"])
    dt_c = float(entry.get("dt_c", 10.0))
    via_amps = float(entry.get("via_amps", VIA_AMPS_DEFAULT))
    derived = bool(entry.get("derived", False))
    cu = bg.stackup.copper_thickness
    violations: list[dict] = []

    # ---- plane-fed rail: the declared trunk must exist
    plane_fed = bool(entry.get("plane_fed", False))
    if plane_fed and not bg.layers_with_zone(net):
        pos = None
        for layer in bg.copper_layers:
            cop = bg.net_copper(net, layer)
            if not cop.is_empty:
                pos = cop.representative_point().coords[0]
                break
        violations.append(violation(
            SCRIPT, "error", pos, None, net, [],
            f"{net} is declared plane_fed but has no zone fill on any layer",
            SCRIPT, kind="plane_missing"))
        plane_fed = False       # rest of the check runs at full semantics

    # ---- track segments
    min_seen: dict[str, float] = {}
    undersized: list[tuple[dict, object]] = []   # (violation, Track)
    pour_taps: list = []                         # dropped: pour-shunted taps
    thin = []                                    # (Track, mid, ov, amps, req)
    for t in bg.tracks_of(net):
        mid = t.shape.interpolate(0.5, normalized=True).coords[0]
        ov = region_current(entry, mid)
        amps = budget if ov is None else ov
        req = required_width_mm(amps, dt_c, cu[t.layer])
        min_seen[t.layer] = min(min_seen.get(t.layer, 9e9), t.width)
        if t.width + WIDTH_TOL_MM < req:
            thin.append((t, mid, ov, amps, req))
    exits = pad_exit_necks(bg, net, [(x[0], x[4]) for x in thin]) \
        if thin else {}
    for t, mid, ov, amps, req in thin:
        if id(t) in exits:
            continue
        advisory = plane_fed and ov is None
        msg = (f"{net} track {t.width:.3f} mm wide on {t.layer}; IPC-2152 "
               f"needs {req:.3f} mm for {amps:.2f} A at dT={dt_c:.0f}C")
        extras = {}
        if advisory:
            msg += ("; advisory: plane-fed rail, full-budget worst-case "
                    "screen (per-segment current unattributed)")
            extras["advisory"] = True
        x0, y0 = t.shape.coords[0]
        x1, y1 = t.shape.coords[-1]
        v = violation(
            SCRIPT, "warning" if advisory else "error", mid, t.layer,
            net, [], msg, SCRIPT, kind="undersized_track",
            width_mm=checklib.rnd(t.width), required_mm=checklib.rnd(req),
            current_a=amps, segment={"start": [checklib.rnd(x0),
                                               checklib.rnd(y0)],
                                     "end": [checklib.rnd(x1),
                                             checklib.rnd(y1)]},
            **extras)
        violations.append(v)
        undersized.append((v, t))

    # ---- bridge labeling (LEARNINGS 2026-07-29: cut edge = sole path)
    if undersized:
        g = netconn.build(bg, net, include_zones=True)
        bridges = netconn.bridge_tracks(g)
        # g.tracks maps edge_id -> the SAME Track objects bg.tracks_of yields
        # (geom filters one cached list; netconn stores them unchanged), so
        # identity lookup is sound. Zero-length tracks are absent from the
        # graph: label those bridge=true (sole-path is the conservative call).
        edge_of = {id(trk): eid for eid, trk in g.tracks.items()}
        for v, t in undersized:
            eid = edge_of.get(id(t))
            v["bridge"] = True if eid is None else eid in bridges
        # non-bridge taps inside their own pour carry no load current
        shunted = [(v, t) for v, t in undersized
                   if not v["bridge"] and (pour_shunted(bg, net, t)
                                           or inside_pad_copper(bg, net, t))]
        if shunted:
            drop = {id(v) for v, _ in shunted}
            violations = [v for v in violations if id(v) not in drop]
            undersized = [(v, t) for v, t in undersized if id(v) not in drop]
            pour_taps = [v["pos"] for v, _ in shunted]

    # ---- pour neckdowns (always at the full budget; plane_fed keeps error)
    zone_layers = bg.layers_with_zone(net)

    def others_at(amps, layer):
        # the net's fills on every other layer, at their own requirement
        return {l: (bg.zone_fill(net, l), required_width_mm(amps, dt_c, cu[l]))
                for l in zone_layers if l != layer}

    for z in bg.zones_of(net):
        for layer in z.fills:
            fill = z.fill_on(layer)
            if fill.is_empty:
                continue
            amps = budget
            req = required_width_mm(budget, dt_c, cu[layer])
            neck = pour_neck(bg, net, layer, fill, req,
                             others_at(budget, layer))
            if neck is not None:
                ov = region_current(entry, neck[1])
                if ov is not None:
                    # failing neck sits in an override region: re-test the
                    # fill at the override requirement; passing drops it
                    amps = ov
                    req = required_width_mm(ov, dt_c, cu[layer])
                    neck = pour_neck(bg, net, layer, fill, req,
                                     others_at(ov, layer))
            if neck is not None:
                width, pos = neck
                msg = (f"{net} pour on {layer} necks to ~{width:.2f} mm "
                       f"between via attachments; IPC-2152 needs {req:.3f} mm "
                       f"for {amps:.2f} A at dT={dt_c:.0f}C")
                extras = {}
                if derived:
                    # derived return entry: the budget itself is a heuristic
                    # (max declared rail), so the neck is a labeled screen,
                    # not an error - see module docstring (T6).
                    msg += ("; advisory: derived return-net coverage "
                            "(no declared entry; budget = max declared rail)")
                    extras["advisory"] = True
                violations.append(violation(
                    SCRIPT, "warning" if derived else "error", pos, layer,
                    net, [], msg, SCRIPT,
                    kind="pour_neckdown", neck_mm=checklib.rnd(width),
                    required_mm=checklib.rnd(req), current_a=amps, **extras))

    # ---- transition via count (per-cluster override via centroid)
    clusters = cluster_vias(bg.vias_of(net))
    for group in clusters:
        cx = sum(v.at[0] for v in group) / len(group)
        cy = sum(v.at[1] for v in group) / len(group)
        ov = region_current(entry, (cx, cy))
        amps = budget if ov is None else ov
        need = max(1, math.ceil(amps / via_amps))
        if len(group) < need:
            advisory = plane_fed and ov is None
            msg = (f"{net} layer transition at ({cx:.2f}, {cy:.2f}) has "
                   f"{len(group)} via(s); {amps:.2f} A needs {need} "
                   f"(>= 1 via per {via_amps} A)")
            extras = {}
            if advisory:
                msg += ("; advisory: plane-fed rail, per-cluster current "
                        "unattributed (each via is a leaf tap off the plane)")
                extras["advisory"] = True
            violations.append(violation(
                SCRIPT, "warning" if advisory else "error", (cx, cy), None,
                net, [], msg, SCRIPT, kind="insufficient_transition_vias",
                vias=len(group), required=need, **extras))

    facts = {"net": net, "current_a": budget, "dt_c": dt_c,
             "required_mm_by_layer": {
                 l: checklib.rnd(required_width_mm(budget, dt_c, cu[l]))
                 for l in bg.copper_layers},
             "min_track_mm_by_layer": {l: checklib.rnd(w)
                                       for l, w in min_seen.items()},
             "via_clusters": len(clusters)}
    if undersized or pour_taps:
        facts["bridge_labeled"] = True
    if pour_taps:
        facts["pour_taps"] = pour_taps
    if exits:
        seen = []
        for info in exits.values():
            if info not in seen:
                seen.append(info)
        facts["pad_exit_necks"] = seen
    if entry.get("plane_fed"):
        facts["plane_fed"] = True
        facts["advisory_violations"] = sum(
            1 for v in violations if v.get("advisory"))
    if derived:
        facts["derived"] = True
        for v in violations:
            v["derived"] = True
    elif (not entry.get("plane_fed") and clusters
            and bg.layers_with_zone(net)):
        # sidecar-adoption lint (T6, facts only): a rail with a zone fill
        # whose via clusters are almost all single-via is the plane-fed
        # shape - the entry probably wants "plane_fed": true (the carrier
        # +3V3 gap: T2 built the key, no sidecar ever adopted it).
        single = sum(1 for g in clusters if len(g) == 1)
        if single >= PLANE_HINT_SINGLE_VIA_FRAC * len(clusters):
            facts["plane_fed_candidate"] = True
    return violations, facts


def derived_return_entry(entries: list[dict], bg: geom.BoardGeom) -> dict | None:
    """Synthesize the return-net entry (module docstring, T6), or None.

    Only when: a declared rail reaches RETURN_SYNTH_MIN_A, the return net
    (per-entry "return_net", default "GND") is on the board with a zone fill,
    and it is not already a declared power entry."""
    real = [e for e in entries if e.get("net") and "current_a" in e]
    if not real:
        return None
    mx = max(real, key=lambda e: float(e["current_a"]))
    if float(mx["current_a"]) < RETURN_SYNTH_MIN_A:
        return None
    ret = mx.get("return_net") or next(
        (e["return_net"] for e in real if e.get("return_net")), "GND")
    if ret in {e["net"] for e in real}:
        return None                      # already declared - owner's numbers win
    if ret not in bg.nets or not bg.layers_with_zone(ret):
        return None                      # routed-only return: not judgeable here
    return {"net": ret, "current_a": float(mx["current_a"]),
            "dt_c": float(mx.get("dt_c", 10.0)),
            "via_amps": float(mx.get("via_amps", VIA_AMPS_DEFAULT)),
            "plane_fed": True, "derived": True}


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="Trace width / pour neck / via count vs current (IPC-2152).")
    ap.add_argument("--pcb", required=True, help="path to .kicad_pcb")
    ap.add_argument("--constraints", required=True,
                    help="constraints.json with a power list")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    cons = checklib.load_json(args.constraints, "constraints")
    entries = cons.get("power", [])
    bg = geom.load_board(Path(args.pcb))
    bg.assert_fresh()

    violations: list[dict] = []
    checked: list[dict] = []
    for entry in entries:
        vs, facts = check_net(bg, entry)
        violations.extend(vs)
        checked.append(facts)
    ret_entry = derived_return_entry(entries, bg)
    if ret_entry is not None:
        vs, facts = check_net(bg, ret_entry)
        violations.extend(vs)
        checked.append(facts)

    payload = checklib.report(SCRIPT, args.pcb, violations, checked=checked,
                              stackup_assumed=bg.stackup.assumed)
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
