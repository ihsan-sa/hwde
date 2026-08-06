"""check_creepage.py - same-layer clearance for high-voltage nets (SPEC 6.3, P8).

One concern: IPC-2221 electrical conductor spacing. For every net pair sitting
more than 30 V apart - derived from constraints.json `voltages`, or declared
explicitly via `voltage_pairs` - every same-layer copper item pair (track
segment, via, pad, zone fill) must meet the IPC-2221 Table 6-1 clearance for
that voltage difference, with the table ROW adjudicated per item type and the
board's coating (see T2; LEARNINGS 2026-07-29 check_creepage entries).

Row adjudication (IPC-2221 6.3.4 - exposed lands do NOT fall back to B2):
    inner layer item                    -> B1 (always)
    outer, coating none:  track/via/zone-> B2   pad -> A6
    outer, soldermask:    track/via/zone-> B4   pad -> A6 (mask relief exposes lands)
    outer, conformal:     track/via/zone-> A5   pad -> A7
Pair requirement = max(row(item_a), row(item_b)). Every violating item pair is
reported (not just the worst per net pair - LEARNINGS 2026-07-29: worst-only
hid 216 siblings), spatially deduped at 0.1 mm and capped at 500 per
(net pair, layer).

The corpus carries no >30 V nets, so this check is clean on all goldens; supply
voltages via constraints.json to exercise it (synthetic HV fixtures are tested).

CLI: --pcb board.kicad_pcb --constraints constraints.json
     [--coating {none,soldermask,conformal}] [--out report.json]
     exit 0/1/2 per SPEC section 6.

constraints.json inputs:
    {"voltages": [{"net": "HV+", "voltage": 400}, ...],
     "voltage_pairs": [{"a": "/TAP_A1", "b": "/TAP_A2", "voltage": 114}, ...],
     "coating": "none" | "soldermask" | "conformal"}
Nets not listed in `voltages` are treated as 0 V. `voltage_pairs` declares a
DIFFERENTIAL requirement between two named nets regardless of their node
voltages (a bridge/AC input that node voltages cannot express); an explicit
pair overrides the `voltages`-derived difference for that net pair - INCLUDING
a pair declared <= 30 V, which WAIVES the derived check for that pair (the
waiver is recorded in skipped_low_voltage_pairs).
`--coating` overrides the constraints key; default "none".
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shapely.ops import nearest_points
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
import geom  # noqa: E402
from checklib import CheckError, violation  # noqa: E402

SCRIPT = "check_creepage"
HV_THRESHOLD_V = 30.0          # IPC-2221 only regulates spacing above this
BAND_UPPER_V = [15, 30, 50, 100, 150, 170, 250, 300, 500]

# IPC-2221B Table 6-1, all seven rows (mm), band upper bounds as above.
# 51-100 / 101-150 V cells machine-verified 2026-07-29 (ema-eda, Altair Pollex
# quoting 6.3.4, protoexpress - LEARNINGS entry); full grid re-verified
# 2026-08-06 against ema-eda.com/ema-resources/blog/
# pcb-clearance-and-creepage-distance-table/ (agrees on every shared cell).
#   B1 internal conductors
#   B2 external, uncoated, <= 3050 m elevation
#   B3 external, uncoated, > 3050 m elevation
#   B4 external, permanent polymer coating (any elevation)
#   A5 external, conformal coating over the assembly
#   A6 external component lead/termination, uncoated
#   A7 external component lead/termination, conformal coated
ROW_TABLE = {
    "B1": [0.05, 0.05, 0.10, 0.10, 0.20, 0.20, 0.20, 0.20, 0.25],
    "B2": [0.10, 0.10, 0.60, 0.60, 0.60, 1.25, 1.25, 1.25, 2.50],
    "B3": [0.10, 0.10, 0.60, 1.50, 3.20, 3.20, 6.40, 12.5, 12.5],
    "B4": [0.05, 0.05, 0.13, 0.13, 0.40, 0.40, 0.40, 0.40, 0.80],
    "A5": [0.13, 0.13, 0.13, 0.13, 0.40, 0.40, 0.40, 0.40, 0.80],
    "A6": [0.13, 0.25, 0.40, 0.50, 0.80, 0.80, 0.80, 0.80, 1.50],
    "A7": [0.13, 0.13, 0.13, 0.13, 0.40, 0.40, 0.40, 0.80, 0.80],
}
# > 500 V: value at 500 V + slope * (V - 500), per the same sources.
ROW_SLOPE_MM_PER_V = {
    "B1": 0.0025, "B2": 0.005, "B3": 0.025, "B4": 0.00305,
    "A5": 0.00305, "A6": 0.00305, "A7": 0.00305,
}
COATINGS = ("none", "soldermask", "conformal")

MAX_EMIT_PER_PAIR_LAYER = 500  # safeguard against pathological pair counts
DEDUP_MM = 0.1                 # gap midpoints closer than this = same gap


def row_clearance_mm(dv: float, row: str) -> float:
    """IPC-2221 Table 6-1 minimum spacing for `dv` volts in the given row."""
    v = abs(dv)
    for ub, val in zip(BAND_UPPER_V, ROW_TABLE[row]):
        if v <= ub:
            return val
    return ROW_TABLE[row][-1] + ROW_SLOPE_MM_PER_V[row] * (v - 500)


def clearance_mm(dv: float, outer: bool) -> float:
    """IPC-2221 minimum spacing for a `dv`-volt difference, outer/inner layer.
    Pinned S5 API: outer -> B2 (external uncoated), inner -> B1."""
    return row_clearance_mm(dv, "B2" if outer else "B1")


def item_row(item_type: str, outer: bool, coating: str) -> str:
    """Table 6-1 row for one copper item (IPC-2221 6.3.4 adjudication)."""
    if not outer:
        return "B1"
    if item_type == "pad":
        # component lands: mask relief exposes them, so soldermask does NOT
        # move them off A6; only conformal coating over the assembly does.
        return "A7" if coating == "conformal" else "A6"
    # track / via / zone fill (vias treated as tented under soldermask)
    return {"none": "B2", "soldermask": "B4", "conformal": "A5"}[coating]


def voltage_map(cons: dict) -> dict[str, float]:
    vmap: dict[str, float] = {}
    for entry in cons.get("voltages", []):
        net = entry.get("net")
        if net is None or "voltage" not in entry:
            raise CheckError(f"voltages entry needs net+voltage: {entry}")
        vmap[net] = float(entry["voltage"])
    for entry in cons.get("nets", []):
        if entry.get("net") and "voltage" in entry:
            vmap[entry["net"]] = float(entry["voltage"])
    return vmap


def voltage_pair_list(cons: dict) -> list[tuple[str, str, float]]:
    """Parse `voltage_pairs`: explicit differential requirements (a, b, |V|)."""
    out: list[tuple[str, str, float]] = []
    for entry in cons.get("voltage_pairs", []):
        a, b = entry.get("a"), entry.get("b")
        if not a or not b or "voltage" not in entry:
            raise CheckError(f"voltage_pairs entry needs a+b+voltage: {entry}")
        if a == b:
            raise CheckError(f"voltage_pairs entry names the same net twice: {a!r}")
        out.append((a, b, abs(float(entry["voltage"]))))
    return out


def _layer_items(bg: geom.BoardGeom, net: str, layer: str, cache: dict) -> list:
    """Copper items of `net` on `layer` as (type, geometry, descriptor, ref)."""
    key = (net, layer)
    if key not in cache:
        items = []
        for t in bg.tracks_of(net, layer):
            c0, c1 = t.shape.coords[0], t.shape.coords[-1]
            items.append(("track", t.poly, {
                "type": "track",
                "ends": [[checklib.rnd(c0[0]), checklib.rnd(c0[1])],
                         [checklib.rnd(c1[0]), checklib.rnd(c1[1])]]}, None))
        for v in bg.vias_of(net, layer):
            items.append(("via", v.poly, {
                "type": "via",
                "at": [checklib.rnd(v.at[0]), checklib.rnd(v.at[1])]}, None))
        for p in bg.pads_of(net, layer):
            items.append(("pad", p.poly, {
                "type": "pad", "ref": p.ref, "pad": p.number}, p.ref))
        for z in bg.zones_of(net, layer):
            for poly in z.fills.get(layer, []):
                items.append(("zone", poly, {"type": "zone", "net": z.net}, None))
        cache[key] = items
    return cache[key]


def sweep_pair(bg: geom.BoardGeom, prim: str, sec: str, dv: float,
               coating: str, cache: dict, prim_label: str):
    """Item-level sweep of one net pair across all copper layers.

    Emits one violation PER violating item pair at the actual gap location
    (midpoint of the nearest points), spatially deduped within DEDUP_MM and
    capped at MAX_EMIT_PER_PAIR_LAYER per (net pair, layer). Returns
    (violations, per-(pair,layer) summaries)."""
    violations: list[dict] = []
    summaries: list[dict] = []
    for layer in bg.copper_layers:
        ia = _layer_items(bg, prim, layer, cache)
        ib = _layer_items(bg, sec, layer, cache)
        if not ia or not ib:
            continue
        outer = bg.stackup.is_outer(layer)
        types = {it[0] for it in ia} | {it[0] for it in ib}
        # prefilter bound: the largest requirement any item-type pair can carry
        req_max = max(row_clearance_mm(dv, item_row(t, outer, coating))
                      for t in types)
        tree = STRtree([it[1] for it in ib])
        hits = []      # (dist, midpoint, item_a, item_b, [row_a,row_b], req)
        min_gap = None
        for a in ia:
            row_a = item_row(a[0], outer, coating)
            req_a = row_clearance_mm(dv, row_a)
            for j in tree.query(a[1], predicate="dwithin",
                                distance=req_max + 1e-6):
                b = ib[int(j)]
                dist = a[1].distance(b[1])
                if min_gap is None or dist < min_gap:
                    min_gap = dist
                row_b = item_row(b[0], outer, coating)
                req = max(req_a, row_clearance_mm(dv, row_b))
                if dist + 1e-6 < req:
                    pa, pb = nearest_points(a[1], b[1])
                    mid = ((pa.x + pb.x) / 2.0, (pa.y + pb.y) / 2.0)
                    hits.append((dist, mid, a, b, [row_a, row_b], req))
        n_under = len(hits)
        # dedup: tightest pair wins within DEDUP_MM (a track inside its own
        # net's zone must not double-report the same physical gap)
        hits.sort(key=lambda h: h[0])
        kept = []
        for h in hits:
            if any((h[1][0] - k[1][0]) ** 2 + (h[1][1] - k[1][1]) ** 2
                   <= DEDUP_MM ** 2 for k in kept):
                continue
            kept.append(h)
        truncated = len(kept) > MAX_EMIT_PER_PAIR_LAYER
        for dist, mid, a, b, rows, req in kept[:MAX_EMIT_PER_PAIR_LAYER]:
            refs = [r for r in (a[3], b[3]) if r]
            violations.append(violation(
                SCRIPT, "error", mid, layer, prim, refs,
                f"{prim_label} to {sec} on {layer}: {dist:.3f} mm copper "
                f"spacing < IPC-2221 {req:.2f} mm ({rows[0]}/{rows[1]}) "
                f"for {abs(dv):.0f} V",
                SCRIPT, kind="creepage", other_net=sec,
                delta_v=checklib.rnd(abs(dv)), spacing_mm=checklib.rnd(dist),
                required_mm=req, rows=rows, item=a[2], other_item=b[2]))
        summaries.append({
            "other_net": sec, "layer": layer, "delta_v": checklib.rnd(abs(dv)),
            "pairs_checked": len(ia) * len(ib),
            "pairs_under_requirement": n_under,
            # min gap among prefiltered candidates; None = all pairs on this
            # layer are farther apart than the largest possible requirement
            "min_gap_mm": checklib.rnd(min_gap) if min_gap is not None else None,
            "truncated": truncated})
    return violations, summaries


def check_net(bg: geom.BoardGeom, hv: str, v_hv: float, vmap: dict,
              coating: str = "none", overrides: frozenset = frozenset(),
              cache: dict | None = None):
    """Check the primary net `hv` against every other net that sits >30 V away.
    The violation is attributed to whichever net of the pair has the higher
    magnitude voltage (the one a fixer should move). Net pairs listed in
    `overrides` (frozensets of two net names) are owned by voltage_pairs."""
    if hv not in bg.nets:
        raise CheckError(f"voltage net {hv!r} not on board")
    cache = {} if cache is None else cache
    violations: list[dict] = []
    pair_summaries: list[dict] = []
    checked = 0
    for other in sorted(bg.nets):
        if not other or other == hv:
            continue
        v_other = vmap.get(other, 0.0)
        dv = v_hv - v_other
        if abs(dv) <= HV_THRESHOLD_V:
            continue
        # own each pair once: the LISTED net with the larger |V| emits it
        # (tie -> larger name, per tuple compare). Unlisted nets (0 V) are never
        # owners, so a listed HV net always owns its pair with a signal/gnd net.
        if other in vmap and (abs(v_other), other) > (abs(v_hv), hv):
            continue
        if frozenset((hv, other)) in overrides:
            continue           # explicit voltage_pairs entry owns this pair
        vs, summ = sweep_pair(bg, hv, other, dv, coating, cache,
                              f"{hv} ({v_hv:.0f} V)")
        violations.extend(vs)
        pair_summaries.extend(summ)
        checked += len(summ)   # (other_net, layer) combos with copper on both
    return violations, {"net": hv, "voltage": v_hv, "pairs_checked": checked,
                        "pairs": pair_summaries}


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="IPC-2221 same-layer clearance for >30 V net pairs.")
    ap.add_argument("--pcb", required=True, help="path to .kicad_pcb")
    ap.add_argument("--constraints", required=True,
                    help="constraints.json with voltages/voltage_pairs/coating")
    ap.add_argument("--coating", choices=list(COATINGS),
                    help="board coating; overrides the constraints.json key "
                         "(default none)")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    cons = checklib.load_json(args.constraints, "constraints")
    coating = args.coating or cons.get("coating", "none")
    if coating not in COATINGS:
        raise CheckError(f"coating must be one of {COATINGS}, got {coating!r}")
    vmap = voltage_map(cons)
    vpairs = voltage_pair_list(cons)
    bg = geom.load_board(Path(args.pcb))
    bg.assert_fresh()

    overrides = frozenset(frozenset((a, b)) for a, b, _v in vpairs)
    cache: dict = {}
    violations: list[dict] = []
    checked: list[dict] = []
    skipped: list[str] = []
    skipped_lv_pairs: list[dict] = []
    for net, v in sorted(vmap.items()):
        # a listed voltage net absent from the board (renamed / not placed) is
        # skipped, not fatal - other nets still get checked. It is still honored
        # as the reference voltage for other nets that DO have copper nearby.
        if net not in bg.nets:
            skipped.append(net)
            continue
        vs, facts = check_net(bg, net, v, vmap, coating=coating,
                              overrides=overrides, cache=cache)
        violations.extend(vs)
        if facts["pairs_checked"] or vs:
            checked.append(facts)
    for a, b, v in vpairs:
        if v <= HV_THRESHOLD_V:
            skipped_lv_pairs.append({"a": a, "b": b, "voltage": v})
            continue
        absent = [n for n in (a, b) if n not in bg.nets]
        if absent:
            skipped.extend(n for n in absent if n not in skipped)
            continue
        vs, summ = sweep_pair(bg, a, b, v, coating, cache,
                              f"{a} (pair {v:.0f} V)")
        violations.extend(vs)
        checked.append({"net": a, "other_net": b, "voltage": v,
                        "voltage_pair": True, "pairs_checked": len(summ),
                        "pairs": summ})

    payload = checklib.report(SCRIPT, args.pcb, violations, checked=checked,
                              skipped_absent_nets=skipped,
                              skipped_low_voltage_pairs=skipped_lv_pairs,
                              coating=coating)
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
