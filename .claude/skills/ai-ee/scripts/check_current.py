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

from shapely.geometry import Point

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


def pour_neck(bg: geom.BoardGeom, net: str, layer: str, fill,
              required: float):
    """None if the pour carries `required` width between all via attachments,
    else (neck_width_mm, pos) of the tightest failing neck."""
    pts = [Point(v.at) for v in bg.vias_of(net, layer)
           if fill.buffer(0.01).contains(Point(v.at))]
    if len(pts) < 2:
        return None
    def connected(radius: float) -> bool:
        eroded = fill.buffer(-radius)
        if eroded.is_empty:
            return False
        for part in getattr(eroded, "geoms", [eroded]):
            hit = part.buffer(radius + 0.01)
            if all(hit.contains(p) for p in pts):
                return True
        return False
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
    for t in bg.tracks_of(net):
        mid = t.shape.interpolate(0.5, normalized=True).coords[0]
        ov = region_current(entry, mid)
        amps = budget if ov is None else ov
        req = required_width_mm(amps, dt_c, cu[t.layer])
        min_seen[t.layer] = min(min_seen.get(t.layer, 9e9), t.width)
        if t.width + WIDTH_TOL_MM < req:
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

    # ---- pour neckdowns (always at the full budget; plane_fed keeps error)
    for z in bg.zones_of(net):
        for layer in z.fills:
            fill = z.fill_on(layer)
            if fill.is_empty:
                continue
            amps = budget
            req = required_width_mm(budget, dt_c, cu[layer])
            neck = pour_neck(bg, net, layer, fill, req)
            if neck is not None:
                ov = region_current(entry, neck[1])
                if ov is not None:
                    # failing neck sits in an override region: re-test the
                    # fill at the override requirement; passing drops it
                    amps = ov
                    req = required_width_mm(ov, dt_c, cu[layer])
                    neck = pour_neck(bg, net, layer, fill, req)
            if neck is not None:
                width, pos = neck
                violations.append(violation(
                    SCRIPT, "error", pos, layer, net, [],
                    f"{net} pour on {layer} necks to ~{width:.2f} mm between "
                    f"via attachments; IPC-2152 needs {req:.3f} mm for "
                    f"{amps:.2f} A at dT={dt_c:.0f}C", SCRIPT,
                    kind="pour_neckdown", neck_mm=checklib.rnd(width),
                    required_mm=checklib.rnd(req), current_a=amps))

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
    if undersized:
        facts["bridge_labeled"] = True
    if entry.get("plane_fed"):
        facts["plane_fed"] = True
        facts["advisory_violations"] = sum(
            1 for v in violations if v.get("advisory"))
    return violations, facts


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

    payload = checklib.report(SCRIPT, args.pcb, violations, checked=checked,
                              stackup_assumed=bg.stackup.assumed)
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
