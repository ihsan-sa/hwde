"""check_return_path.py - return-path continuity for high-speed nets (SPEC 6.3).

Per net in constraints.json["high_speed"]:
 1. Signal track segments per layer; each layer's reference layer(s) come from
    the stackup (adjacent copper: microstrip = one, stripline = two).
 2. Reference copper on a reference layer = the reference net's copper there.
    The spec names the filled-zone polygons; this check unions ALL reference-net
    copper (fill + tracks + pads + vias) and then keeps only the single
    connected component under the corridor, so "continuous reference copper"
    is honored while same-net stitching copper does not false-positive.
 3. Corridor = trace centerline buffered by k x trace_width (k default 3,
    ~return-current spread), flat-capped: the corridor ends where the trace
    ends (a round cap would poke past the landing pad into copper the signal
    never runs over). Violation where the corridor is not contained in that
    continuous reference copper (plane voids, zone gaps, other-net copper all
    surface as corridor deficit).
 4. At every layer transition (signal via joining tracks on two layers): if the
    reference plane changes layer or net, require a same-reference-net via
    (or, for different reference nets, a stitching capacitor) within radius
    r = c / (f_knee * 20) from t_rise, default 2.0 mm.
 5. Output: normalized violations with polygons + coordinates + layer;
    severity by centerline crossing length.

Unavoidable single-item plane punctures are EXCISED from the deficit before
judging it: the annular clearance void around any single via (the signal's
own transition via, and lone other-net vias whose antipad merely nicks the
corridor), and the clearance/thermal ring around the signal's or reference
net's own through pads (thermal spokes carry the return current; the ring is
not a break). Excision removes at most a disk of item radius + one zone
clearance around each such item, so structural voids - slots, moats, merged
antipad chains away from single vias - always survive with their remainder,
and severity is judged on what remains. A through-pad FIELD of another net
(connector row) is deliberately not excised.

CLI: --pcb board.kicad_pcb --constraints constraints.json [--k 3]
     [--verify-fill] [--out report.json]        exit 0/1/2 per SPEC section 6.

constraints.json["high_speed"] entries:
    {"net": "/MCO",                  # required, exact board net name
     "reference": "GND",             # default GND; or {"F.Cu": "GND", ...}
     "k": 3.0,                       # optional per-net corridor factor
     "t_rise_ns": 1.0,               # optional -> r = c/(f_knee*20)
     "return_via_radius_mm": 2.0}    # optional explicit r (wins over t_rise)
"""
from __future__ import annotations

import argparse
import math
import sys
from itertools import product
from pathlib import Path

from shapely.geometry import Point
from shapely.ops import linemerge, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
import geom  # noqa: E402
from checklib import CheckError, violation  # noqa: E402

SCRIPT = "check_return_path"
K_DEFAULT = 3.0
RADIUS_DEFAULT_MM = 2.0
C_MM_PER_S = 2.998e11          # spec formula: r = c / (f_knee * 20)
ALLOW_CLEARANCE_MM = 0.65      # excision margin beyond item copper edge
                               # (>= the corpus 0.5 mm zone clearance)
MIN_DEFICIT_MM2 = 0.05         # deficit remainder below this is an artifact
CROSSING_ERROR_MM = 0.01       # centerline crossing >= this -> error


# ------------------------------------------------------------ constraints

def net_entry_radius(entry: dict) -> float:
    if entry.get("return_via_radius_mm"):
        return float(entry["return_via_radius_mm"])
    if entry.get("t_rise_ns"):
        f_knee = 0.5 / (float(entry["t_rise_ns"]) * 1e-9)
        return C_MM_PER_S / (f_knee * 20.0)
    return RADIUS_DEFAULT_MM


def reference_net_for(entry: dict, layer: str) -> str:
    ref = entry.get("reference", "GND")
    if isinstance(ref, dict):
        return ref.get(layer, ref.get("default", "GND"))
    return ref


# ------------------------------------------------------------ geometry

def corridor_on(bg: geom.BoardGeom, net: str, layer: str, k: float):
    """Flat-capped corridor: merge the net's segments into chains and buffer
    each chain by k x the chain's widest track. Flat caps stop the corridor
    at trace endpoints; round joins still cover outer corners of bends."""
    tracks = bg.tracks_of(net, layer)
    if not tracks:
        return None, []
    union = unary_union([t.shape for t in tracks])
    merged = linemerge(union) if union.geom_type == "MultiLineString" else union
    chains = list(getattr(merged, "geoms", [merged]))
    parts = []
    for chain in chains:
        widths = [t.width for t in tracks
                  if t.shape.intersection(chain).length > 1e-6]
        w = max(widths) if widths else max(t.width for t in tracks)
        parts.append(chain.buffer(k * w, quad_segs=16, cap_style="flat",
                                  join_style="round"))
    return unary_union(parts), tracks


def excision_disks(bg: geom.BoardGeom, net: str, ref_net: str,
                   ref_layer: str) -> list:
    """Single-item annular voids to excise from the deficit (see docstring):
    every via punching the reference layer, plus the signal/reference nets'
    own through pads. Disk = item copper radius + one zone clearance."""
    disks = []
    for v in bg.vias_of(layer=ref_layer):
        disks.append(Point(v.at).buffer(
            v.diameter / 2.0 + ALLOW_CLEARANCE_MM, quad_segs=12))
    for owner in (net, ref_net):
        for p in bg.pads_of(owner):
            # through pads occupy every copper layer incl. the reference
            if ref_layer in p.layers and len(p.layers) > 1:
                disks.append(Point(p.center).buffer(
                    max(p.size) / 2.0 + ALLOW_CLEARANCE_MM, quad_segs=12))
    return disks


def continuous_reference(ref_copper, corridor):
    """The single connected reference-copper component under the corridor."""
    if ref_copper.is_empty:
        return ref_copper
    parts = list(getattr(ref_copper, "geoms", [ref_copper]))
    best, best_a = None, -1.0
    for p in parts:
        a = p.intersection(corridor).area
        if a > best_a:
            best, best_a = p, a
    return best if best is not None else ref_copper


def deficit_polys(corridor, ref_component, disks) -> list:
    """Corridor regions outside continuous reference copper, with single-item
    annular voids excised; only meaningful remainders are violations."""
    deficit = corridor.difference(ref_component)
    if disks:
        deficit = deficit.difference(unary_union(disks))
    out = []
    for poly in getattr(deficit, "geoms", [deficit]):
        if not poly.is_empty and poly.area >= MIN_DEFICIT_MM2:
            out.append(poly)
    return out


# ------------------------------------------------------------ transitions

def signal_transitions(bg: geom.BoardGeom, net: str) -> list[dict]:
    """Vias of `net` that join its tracks on two or more layers."""
    out = []
    for v in bg.vias_of(net):
        tol = v.diameter / 2.0 + 0.05
        used = []
        for layer in bg.copper_layers:
            for t in bg.tracks_of(net, layer):
                x0, y0 = t.shape.coords[0]
                x1, y1 = t.shape.coords[-1]
                if (math.hypot(x0 - v.at[0], y0 - v.at[1]) <= tol
                        or math.hypot(x1 - v.at[0], y1 - v.at[1]) <= tol):
                    used.append(layer)
                    break
        if len(used) >= 2:
            out.append({"via": v, "layers": used})
    return out


def stitch_cap_near(bg: geom.BoardGeom, net_a: str, net_b: str,
                    at: tuple[float, float], radius: float) -> bool:
    """A two-pad footprint bridging net_a/net_b with both pads within radius
    (the different-DC-net stitching-capacitor case)."""
    by_ref: dict[str, set] = {}
    for p in bg.pads_of():
        if p.net in (net_a, net_b):
            if math.hypot(p.center[0] - at[0], p.center[1] - at[1]) <= radius:
                by_ref.setdefault(p.ref, set()).add(p.net)
    return any(nets == {net_a, net_b} for nets in by_ref.values())


def check_transition(bg: geom.BoardGeom, net: str, entry: dict,
                     trans: dict, radius: float) -> dict | None:
    v = trans["via"]
    layers = sorted(trans["layers"], key=bg.copper_layers.index)
    la, lb = layers[0], layers[-1]
    refs_a = [(rl, reference_net_for(entry, la))
              for rl in bg.adjacent_copper(la) if rl]
    refs_b = [(rl, reference_net_for(entry, lb))
              for rl in bg.adjacent_copper(lb) if rl]
    if set(refs_a) == set(refs_b):
        return None  # same reference plane(s) on both sides
    ref_nets = {n for _, n in refs_a + refs_b}
    if len(ref_nets) > 1:
        a_net, b_net = sorted(ref_nets)[:2]
        if stitch_cap_near(bg, a_net, b_net, v.at, radius):
            return None
        return violation(
            SCRIPT, "error", v.at, None, net, [],
            f"{net} transition {la}->{lb} at ({v.at[0]:.3f}, {v.at[1]:.3f}) "
            f"changes reference net {a_net}->{b_net} with no stitching "
            f"capacitor within {radius:.2f} mm", SCRIPT,
            kind="missing_stitch_cap", radius_mm=checklib.rnd(radius),
            from_layer=la, to_layer=lb, ref_nets=sorted(ref_nets))
    ref_net = next(iter(ref_nets))
    nearest = None
    for rv in bg.vias_of(ref_net):
        if any(rv.spans(ra) and rv.spans(rb)
               for (ra, _), (rb, _) in product(refs_a, refs_b)):
            d = math.hypot(rv.at[0] - v.at[0], rv.at[1] - v.at[1])
            nearest = d if nearest is None or d < nearest else nearest
    if nearest is not None and nearest <= radius:
        return None
    near_txt = f"nearest {nearest:.2f} mm" if nearest is not None else "none found"
    return violation(
        SCRIPT, "error", v.at, None, net, [],
        f"{net} layer transition {la}->{lb} at ({v.at[0]:.3f}, {v.at[1]:.3f}) "
        f"has no {ref_net} return via within {radius:.2f} mm ({near_txt})",
        SCRIPT, kind="missing_return_via", radius_mm=checklib.rnd(radius),
        nearest_ref_via_mm=checklib.rnd(nearest) if nearest is not None else None,
        from_layer=la, to_layer=lb, ref_layers=[sorted({rl for rl, _ in refs_a}),
                                                sorted({rl for rl, _ in refs_b})])


# ------------------------------------------------------------ per-net check

def check_net(bg: geom.BoardGeom, entry: dict, k_cli: float):
    net = entry.get("net")
    if not net:
        raise CheckError('high_speed entry without "net"')
    if net not in bg.nets:
        raise CheckError(f"high-speed net {net!r} not on board "
                         f"(nets: {sorted(n for n in bg.nets if n)})")
    k = float(entry.get("k", k_cli))
    radius = net_entry_radius(entry)
    violations: list[dict] = []
    layers_used: list[str] = []

    for layer in bg.copper_layers:
        corridor, tracks = corridor_on(bg, net, layer, k)
        if corridor is None:
            continue
        layers_used.append(layer)
        centerline = unary_union([t.shape for t in tracks])
        for ref_layer in bg.adjacent_copper(layer):
            if ref_layer is None:
                continue
            ref_net = reference_net_for(entry, layer)
            ref_copper = bg.net_copper(ref_net, ref_layer)
            if ref_copper.is_empty:
                violations.append(violation(
                    SCRIPT, "error", corridor.representative_point().coords[0],
                    ref_layer, net, [],
                    f"{net} on {layer} has no {ref_net} reference copper at "
                    f"all on adjacent layer {ref_layer}", SCRIPT,
                    kind="no_reference_plane", signal_layer=layer,
                    corridor_area_mm2=checklib.rnd(corridor.area)))
                continue
            component = continuous_reference(ref_copper, corridor)
            disks = excision_disks(bg, net, ref_net, ref_layer)
            for poly in deficit_polys(corridor, component, disks):
                crossing = centerline.intersection(poly).length
                sev = "error" if crossing >= CROSSING_ERROR_MM else "warning"
                rp = poly.representative_point()
                violations.append(violation(
                    SCRIPT, sev, (rp.x, rp.y), ref_layer, net, [],
                    f"return corridor of {net} ({layer}) leaves continuous "
                    f"{ref_net} copper on {ref_layer}: {poly.area:.2f} mm2 "
                    f"deficit, {crossing:.2f} mm of trace crossing", SCRIPT,
                    kind="corridor_void", signal_layer=layer,
                    reference_net=ref_net,
                    crossing_len_mm=checklib.rnd(crossing),
                    area_mm2=checklib.rnd(poly.area),
                    polygon=checklib.poly_coords(poly)))

    transitions = signal_transitions(bg, net)
    for trans in transitions:
        vio = check_transition(bg, net, entry, trans, radius)
        if vio is not None:
            violations.append(vio)

    facts = {"net": net, "layers": layers_used, "k": k,
             "return_via_radius_mm": checklib.rnd(radius),
             "transitions": [{"pos": [checklib.rnd(t["via"].at[0]),
                                      checklib.rnd(t["via"].at[1])],
                              "layers": t["layers"]} for t in transitions]}
    return violations, facts


# ------------------------------------------------------------ CLI

def run(argv=None):
    ap = argparse.ArgumentParser(
        description="Return-path continuity check for high-speed nets.")
    ap.add_argument("--pcb", required=True, help="path to .kicad_pcb")
    ap.add_argument("--constraints", required=True,
                    help="constraints.json with a high_speed list")
    ap.add_argument("--k", type=float, default=K_DEFAULT,
                    help="corridor factor x trace width (default 3)")
    ap.add_argument("--verify-fill", action="store_true",
                    help="also diff committed fills vs a fresh kicad-cli refill")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    cons = checklib.load_json(args.constraints, "constraints")
    entries = cons.get("high_speed", [])
    bg = geom.load_board(Path(args.pcb))
    bg.assert_fresh(refill=args.verify_fill)

    violations: list[dict] = []
    checked: list[dict] = []
    for entry in entries:
        vs, facts = check_net(bg, entry, args.k)
        violations.extend(vs)
        checked.append(facts)

    payload = checklib.report(SCRIPT, args.pcb, violations, checked=checked)
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
