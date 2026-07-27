#!/usr/bin/env python
"""dfm_check.py - gerber-level DFM against jlc_capabilities.yaml (SPEC P9).

The INDEPENDENT second geometry path. Every other check in the pipeline reads
the .kicad_pcb through geom.py; this one reads the files we actually ship - the
exported gerbers and Excellon drill, through gerbonara (lib/gerblib.py). Two
parsers over two formats means an export-stage defect shows up as a
disagreement instead of being invisible to a board-file-only checker.

Checks (all thresholds from reference/jlc_capabilities.yaml, keyed
<layers>layer_<oz>oz):

  copper   min_trace_width, min_clearance (gap between distinct copper
           islands - gerbers carry no nets, so "touching = one conductor",
           which is exactly what the fab's own DFM engine sees),
           min_copper_to_edge
  drill    min_hole_diameter, min_hole_to_hole, min_hole_to_edge,
           annular ring (hole vs the pad copper around it)
  mask     silk_over_pad (silk ink inside a mask opening = unprintable/
           unsolderable), solder-mask dam between openings
  silk     min silk stroke width
  assembly CPL polarity: board pad->net vs schematic pin->net. KiCad's own
           --schematic-parity is net-level and does NOT catch a polarized part
           mounted backwards (LEARNINGS/V9); comparing per PAD NUMBER does, and
           the pad geometry gives the apparent rotation delta.
  release  gerber layer completeness, drill validity, BOM completeness

Severity policy: a JLCPCB manufacturing minimum that is actually violated is an
ERROR. Advisory classes that legitimate boards routinely trip - silk stroke
width (KiCad's default 0.12 mm silk prints fine at JLC) and mask dams - are
WARNINGS, so they are reported without failing the gate (the fp_verify /
netlist_audit precedent).

Emits the S2 normalized violation schema via checklib; exit 0/1/2.

CLI:
  dfm_check.py --pcb board.kicad_pcb [--fab-dir DIR] [--copper-oz 1]
               [--schematic s.kicad_sch | --netlist b.net | --no-polarity]
               [--parts parts.json] [--capabilities cap.yaml] [--out r.json]
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
import warnings
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import yaml  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

import checklib  # noqa: E402
import gerblib  # noqa: E402
import geom  # noqa: E402
from checklib import CheckError  # noqa: E402

SOURCE = "check.dfm"
CHECK = "dfm"
CAPABILITIES = SCRIPTS.parent / "reference" / "jlc_capabilities.yaml"

# Two copper features closer than this are numerically touching (one conductor),
# not a clearance violation. Far below any fab capability, far above float noise.
EPS_TOUCH = 1e-4
# Ignore silk/mask overlap smaller than this - antialiasing-scale slivers.
MIN_SILK_OVERLAP_MM2 = 1e-3
# Slack for measurements taken off tessellated arc geometry (gerblib flattens
# arcs to 1 um). A board built EXACTLY at a fab minimum - blinky2's 0.6 mm vias
# on a 0.3 mm drill are exactly the 0.15 mm annular floor - must not be failed
# by micron-scale flattening error. Two orders of magnitude below the smallest
# meaningful DFM delta (~0.01 mm), twice the flattening bound.
GEOM_TOL_MM = 2e-3


def _below(value: float, limit: float, tol: float = GEOM_TOL_MM) -> bool:
    """Is `value` genuinely under `limit` (not just tessellation noise)?"""
    return value + tol < limit


# ------------------------------------------------------------------ rules

def load_capabilities(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CheckError(f"cannot read capabilities {path}: {exc}") from exc
    if not isinstance(data, dict) or "design_rules" not in data:
        raise CheckError(f"{path} has no design_rules block")
    return data


def rule_key(layers: int, copper_oz: float) -> str:
    oz = f"{copper_oz:g}"
    return f"{layers}layer_{oz}oz"


def pick_rules(caps: dict, layers: int, copper_oz: float) -> tuple[str, dict]:
    key = rule_key(layers, copper_oz)
    rules = caps["design_rules"].get(key)
    if rules is None:
        avail = ", ".join(sorted(caps["design_rules"]))
        raise CheckError(f"no capability entry '{key}' (have: {avail})")
    return key, rules


# ------------------------------------------------------------ copper checks

def _mid(ls):
    p = ls.interpolate(0.5, normalized=True)
    return (p.x, p.y)


def check_trace_width(fab, rules, vios: list) -> None:
    lo = rules.get("min_trace_width_mm")
    if lo is None:
        return
    for name in fab.copper_layer_names():
        lg = fab.copper(name)
        if lg is None:
            continue
        for ls, w in lg.trace_lines:
            if w + 1e-9 < lo:
                vios.append(checklib.violation(
                    CHECK, "error", _mid(ls), name, None, [],
                    f"trace width {w:.4f} mm below JLC minimum {lo} mm "
                    f"on {name}", SOURCE, kind="dfm_trace_width",
                    width_mm=checklib.rnd(w), min_mm=lo))


def _pairs_within(polys, limit):
    """Yield (i, j) index pairs whose geometries are within `limit`."""
    if len(polys) < 2:
        return
    tree = STRtree(polys)
    seen = set()
    for i, g in enumerate(polys):
        for j in tree.query(g.buffer(limit)):
            j = int(j)
            if j <= i:
                continue
            key = (i, j)
            if key in seen:
                continue
            seen.add(key)
            yield i, j


def check_clearance(fab, rules, vios: list) -> None:
    lo = rules.get("min_clearance_mm")
    if lo is None:
        return
    for name in fab.copper_layer_names():
        lg = fab.copper(name)
        if lg is None:
            continue
        comps = lg.components()
        for i, j in _pairs_within(comps, lo):
            d = comps[i].distance(comps[j])
            if d <= EPS_TOUCH or not _below(d, lo):
                continue
            a, b = comps[i], comps[j]
            p1, p2 = a.exterior.interpolate(a.exterior.project(
                Point(b.centroid))), b.centroid
            vios.append(checklib.violation(
                CHECK, "error", (p1.x, p1.y), name, None, [],
                f"copper clearance {d:.4f} mm below JLC minimum {lo} mm "
                f"on {name}", SOURCE, kind="dfm_clearance",
                clearance_mm=checklib.rnd(d), min_mm=lo))


def check_copper_to_edge(fab, rules, vios: list) -> None:
    lo = rules.get("min_copper_to_edge_mm")
    outline = fab.outline
    if lo is None or outline.is_empty:
        return
    edge = outline.exterior
    for name in fab.copper_layer_names():
        lg = fab.copper(name)
        if lg is None:
            continue
        for comp in lg.components():
            d = comp.distance(edge)
            # Copper crossing the outline reads as distance 0; both cases are
            # the same defect (copper too close to / past the board edge).
            if _below(d, lo):
                p = comp.centroid
                vios.append(checklib.violation(
                    CHECK, "error", (p.x, p.y), name, None, [],
                    f"copper {d:.4f} mm from board edge, JLC minimum {lo} mm "
                    f"on {name}", SOURCE, kind="dfm_copper_to_edge",
                    distance_mm=checklib.rnd(d), min_mm=lo))


# ------------------------------------------------------------- drill checks

def check_holes(fab, rules, vios: list) -> None:
    holes = fab.holes
    lo_d = rules.get("min_hole_diameter_mm")
    if lo_d is not None:
        for h in holes:
            if _below(h.diameter, lo_d):
                vios.append(checklib.violation(
                    CHECK, "error", (h.x, h.y), None, None, [],
                    f"drill {h.diameter:.4f} mm below JLC minimum {lo_d} mm",
                    SOURCE, kind="dfm_hole_size",
                    diameter_mm=checklib.rnd(h.diameter), min_mm=lo_d))

    lo_hh = rules.get("min_hole_to_hole_mm")
    if lo_hh is not None and len(holes) > 1:
        disks = [Point(h.x, h.y).buffer(h.diameter / 2.0, quad_segs=16)
                 for h in holes]
        for i, j in _pairs_within(disks, lo_hh):
            d = disks[i].distance(disks[j])
            if _below(d, lo_hh):
                vios.append(checklib.violation(
                    CHECK, "error", (holes[i].x, holes[i].y), None, None, [],
                    f"hole-to-hole {d:.4f} mm below JLC minimum {lo_hh} mm",
                    SOURCE, kind="dfm_hole_to_hole",
                    distance_mm=checklib.rnd(d), min_mm=lo_hh,
                    other=[checklib.rnd(holes[j].x), checklib.rnd(holes[j].y)]))

    lo_he = rules.get("min_hole_to_edge_mm")
    outline = fab.outline
    if lo_he is not None and not outline.is_empty:
        edge = outline.exterior
        for h in holes:
            d = Point(h.x, h.y).buffer(h.diameter / 2.0).distance(edge)
            if _below(d, lo_he):
                vios.append(checklib.violation(
                    CHECK, "error", (h.x, h.y), None, None, [],
                    f"hole {d:.4f} mm from board edge, JLC minimum {lo_he} mm",
                    SOURCE, kind="dfm_hole_to_edge",
                    distance_mm=checklib.rnd(d), min_mm=lo_he))


def check_annular_ring(fab, rules, vios: list) -> None:
    """Radial copper around each plated hole, measured on the OUTER layers
    (where the ring is thinnest after registration)."""
    lo = rules.get("min_annular_ring_mm")
    if lo is None:
        return
    outer = [n for n in ("F.Cu", "B.Cu") if n in fab.copper_files]
    pads_by_layer = {}
    for name in outer:
        lg = fab.copper(name)
        if lg is None:
            continue
        # Flashes ONLY. A zone fill is a keyhole ring whose exterior runs right
        # past each via's antipad, so counting pours as "the pad around the
        # hole" measures the antipad gap and invents a ~1 mil ring shortfall.
        polys = lg.pads
        pads_by_layer[name] = (polys, STRtree(polys) if polys else None)

    for h in fab.holes:
        if not h.plated:
            continue
        c = Point(h.x, h.y)
        r = h.diameter / 2.0
        best = None
        for name, (polys, tree) in pads_by_layer.items():
            if tree is None:
                continue
            for idx in tree.query(c):
                poly = polys[int(idx)]
                if not poly.contains(c):
                    continue
                ring = poly.exterior.distance(c) - r
                if best is None or ring < best[0]:
                    best = (ring, name)
        if best is None:
            continue  # no pad around it on an outer layer (NPTH / inner-only)
        ring, name = best
        if _below(ring, lo):
            vios.append(checklib.violation(
                CHECK, "error", (h.x, h.y), name, None, [],
                f"annular ring {ring:.4f} mm below JLC minimum {lo} mm",
                SOURCE, kind="dfm_annular_ring",
                ring_mm=checklib.rnd(ring), min_mm=lo,
                drill_mm=checklib.rnd(h.diameter)))


# -------------------------------------------------------- silk / mask checks

def check_silk(fab, rules, vios: list, bg=None) -> None:
    lo_w = rules.get("min_silk_width_mm")
    for side in ("F", "B"):
        lg = fab.silk(side)
        if lg is None:
            continue
        name = f"{side}.Silkscreen"
        if lo_w is not None:
            thin = [(ls, w) for ls, w in lg.trace_lines if w + 1e-9 < lo_w]
            if thin:
                narrowest = min(w for _, w in thin)
                vios.append(checklib.violation(
                    CHECK, "warning", _mid(thin[0][0]), name, None, [],
                    f"{len(thin)} silk strokes below JLC minimum width "
                    f"{lo_w} mm (narrowest {narrowest:.4f} mm) on {name}",
                    SOURCE, kind="dfm_silk_width",
                    width_mm=checklib.rnd(narrowest), min_mm=lo_w,
                    count=len(thin)))

        mask = fab.mask(side)
        if mask is None:
            continue
        openings = mask.union()
        silk = lg.union()
        if openings.is_empty or silk.is_empty:
            continue
        inter = silk.intersection(openings)
        if inter.is_empty:
            continue
        parts = list(inter.geoms) if inter.geom_type.startswith("Multi") \
            else [inter]
        for part in parts:
            if part.area < MIN_SILK_OVERLAP_MM2:
                continue
            p = part.representative_point()
            pos, refs = (p.x, p.y), []
            if bg is not None:
                hit = _pad_at(bg, p.x, p.y, side)
                if hit is not None:
                    refs = [hit.ref]
                    pos = hit.center
            vios.append(checklib.violation(
                CHECK, "error", pos, name, None, refs,
                f"silkscreen printed over a solder-mask opening "
                f"({part.area:.4f} mm2) on {name}"
                + (f" - pad of {refs[0]}" if refs else ""),
                SOURCE, kind="dfm_silk_over_pad",
                overlap_mm2=checklib.rnd(part.area),
                at=[checklib.rnd(p.x), checklib.rnd(p.y)]))


def _pad_at(bg, x: float, y: float, side: str):
    """The board pad whose copper covers (x, y) on that side, if any."""
    layer = "F.Cu" if side == "F" else "B.Cu"
    pt = Point(x, y)
    best = None
    for pad in bg.pads_of(layer=layer):
        try:
            poly = pad.poly
        except Exception:
            continue
        if poly.contains(pt) or poly.distance(pt) < 0.05:
            d = poly.distance(pt)
            if best is None or d < best[0]:
                best = (d, pad)
    return best[1] if best else None


def check_mask_dam(fab, rules, vios: list) -> None:
    lo = rules.get("min_solder_mask_dam_mm")
    if lo is None:
        return
    for side in ("F", "B"):
        mask = fab.mask(side)
        if mask is None:
            continue
        comps = mask.components()
        thin = []
        for i, j in _pairs_within(comps, lo):
            d = comps[i].distance(comps[j])
            if EPS_TOUCH < d and _below(d, lo):
                thin.append((d, comps[i].centroid))
        if thin:
            d, c = min(thin, key=lambda t: t[0])
            vios.append(checklib.violation(
                CHECK, "warning", (c.x, c.y), f"{side}.Mask", None, [],
                f"{len(thin)} solder-mask dams below {lo} mm "
                f"(narrowest {d:.4f} mm) on {side}.Mask", SOURCE,
                kind="dfm_mask_dam", dam_mm=checklib.rnd(d), min_mm=lo,
                count=len(thin)))


# ----------------------------------------------------------- CPL polarity

def _angle(cx, cy, x, y) -> float:
    return math.degrees(math.atan2(y - cy, x - cx)) % 360.0


def check_polarity(bg, netlist: dict, vios: list) -> dict:
    """Board pad->net vs schematic pin->net, PER PAD NUMBER.

    kicad's --schematic-parity compares net membership, so a polarized part
    rotated 180 deg with its pad nets swapped stays invisible to it (V9). Here
    a swap is a per-pad mismatch, and when the mismatched nets form a clean
    permutation of the expected ones the pad geometry yields the rotation the
    part is off by - which is what the CPL would ship.
    """
    expected: dict[tuple[str, str], str] = {}
    for name, members in netlist.get("nets", {}).items():
        for m in members:
            expected[(m["ref"], str(m["pin"]))] = name

    by_ref: dict[str, list] = {}
    for pad in bg.pads_of():
        if pad.net is None:
            continue
        by_ref.setdefault(pad.ref, []).append(pad)

    checked = 0
    for ref, pads in sorted(by_ref.items()):
        want = {p: n for (r, p), n in expected.items() if r == ref}
        if not want:
            continue  # not an assembled part (mounting hole, board_only)
        checked += 1
        got = {}
        for pad in pads:
            got.setdefault(pad.number, set()).add(pad.net)
        mism = [(num, sorted(nets)[0], want[num])
                for num, nets in sorted(got.items())
                if num in want and want[num] not in nets]
        if not mism:
            continue

        # Where does each expected net actually sit? A consistent non-identity
        # mapping = the part is rotated/mounted wrong, not miswired.
        pos = {}
        for pad in pads:
            pos.setdefault(pad.number, pad.center)
        cx = sum(p[0] for p in pos.values()) / len(pos)
        cy = sum(p[1] for p in pos.values()) / len(pos)
        deltas, permuted = [], True
        for num, _actual, wanted in mism:
            holder = [p for p in pads if p.net == wanted]
            if len(holder) != 1 or num not in pos:
                permuted = False
                break
            a = _angle(cx, cy, *pos[num])
            b = _angle(cx, cy, holder[0].center[0], holder[0].center[1])
            deltas.append((b - a) % 360.0)
        rot = None
        if permuted and deltas:
            spread = max(deltas) - min(deltas)
            if spread < 5.0 or spread > 355.0:
                rot = round(sum(deltas) / len(deltas), 1)

        detail = ", ".join(f"pad {n}: board '{a}' vs schematic '{w}'"
                           for n, a, w in mism)
        if rot is not None:
            msg = (f"{ref} pad nets are rotated {rot:g} deg from the schematic "
                   f"- the part would be assembled backwards ({detail})")
            kind = "cpl_polarity"
        else:
            msg = f"{ref} pad nets disagree with the schematic ({detail})"
            kind = "pad_net_mismatch"
        vios.append(checklib.violation(
            CHECK, "error", (cx, cy), None, None, [ref], msg, SOURCE,
            kind=kind, rotation_delta_deg=rot,
            mismatches=[{"pad": n, "board": a, "schematic": w}
                        for n, a, w in mism]))
    return {"refs_checked": checked}


# ------------------------------------------------------------ release gate

def check_release(fab, layers: int, vios: list, parts_report: dict | None
                  ) -> dict:
    """Fab-release completeness (SPEC P8 table): every layer present, drill
    valid, BOM complete."""
    facts = {}
    missing = []
    have = set(fab.copper_files)
    want_cu = {"F.Cu", "B.Cu"} | {f"In{i}.Cu" for i in range(1, layers - 1)}
    for lyr in sorted(want_cu - have):
        missing.append(lyr)
    for side in ("F", "B"):
        if side not in fab.mask_files:
            missing.append(f"{side}.Mask")
        if side not in fab.silk_files:
            missing.append(f"{side}.Silkscreen")
    if fab.edge_file is None:
        missing.append("Edge.Cuts")
    if missing:
        vios.append(checklib.violation(
            CHECK, "error", None, None, None, [],
            f"fab package is missing layer(s): {', '.join(missing)}",
            SOURCE, kind="dfm_missing_layer", layers=missing))
    facts["layers_present"] = sorted(have) + \
        [f"{s}.Mask" for s in sorted(fab.mask_files)] + \
        [f"{s}.Silkscreen" for s in sorted(fab.silk_files)]

    if not fab.drill_files:
        vios.append(checklib.violation(
            CHECK, "error", None, None, None, [],
            "fab package has no drill file", SOURCE, kind="dfm_no_drill"))
    facts["n_holes"] = len(fab.holes)

    if parts_report is not None:
        missing_lcsc = parts_report.get("missing_lcsc") or []
        facts["missing_lcsc"] = missing_lcsc
        if missing_lcsc:
            vios.append(checklib.violation(
                CHECK, "warning", None, None, None, sorted(missing_lcsc),
                f"{len(missing_lcsc)} assembled part(s) have no LCSC number "
                f"in the BOM", SOURCE, kind="dfm_bom_incomplete",
                refs_missing=sorted(missing_lcsc)))
    return facts


# ------------------------------------------------------------------ driver

def _resolve_netlist(pcb: Path, schematic: Path | None,
                     netlist: Path | None, tmp: Path):
    """-> (parsed netlist dict | None, reason-if-skipped)."""
    import netlist_audit
    if netlist is not None:
        return netlist_audit.parse_netlist(netlist), None
    sch = schematic
    if sch is None:
        cand = pcb.with_suffix(".kicad_sch")
        sch = cand if cand.exists() else None
    if sch is None:
        return None, "no schematic or netlist available"
    import kc
    out = tmp / "polarity.net"
    res = kc.export_netlist(kc.resolve_cli(), Path(sch), out)
    if res.get("status") != "pass":
        return None, f"netlist export failed: {res.get('stderr') or ''}"[:200]
    return netlist_audit.parse_netlist(out), None


def run(pcb: Path, fab_dir: Path | None = None, copper_oz: float = 1.0,
        capabilities: Path | None = None, schematic: Path | None = None,
        netlist: Path | None = None, polarity: bool = True,
        parts: Path | None = None, skip: tuple[str, ...] = ()) -> dict:
    if not pcb.exists():
        raise CheckError(f"board not found: {pcb}")
    caps = load_capabilities(capabilities or CAPABILITIES)

    with tempfile.TemporaryDirectory(prefix="aiee_dfm_") as td:
        tmp = Path(td)
        if fab_dir is None:
            import fab_export
            man = fab_export.run(pcb, tmp / "fab", make_zip=False)
            gdir = Path(man["gerber_dir"])
        else:
            gdir = Path(fab_dir)
            if (gdir / "gerbers").is_dir():
                gdir = gdir / "gerbers"
        fab = gerblib.open_fab(gdir)
        n_layers = len(fab.copper_layer_names())
        if n_layers == 0:
            raise CheckError(f"no copper gerbers found in {gdir}")
        key, rules = pick_rules(caps, n_layers, copper_oz)

        bg = geom.load_board(pcb)
        vios: list = []
        facts: dict = {}

        if "copper" not in skip:
            check_trace_width(fab, rules, vios)
            check_clearance(fab, rules, vios)
            check_copper_to_edge(fab, rules, vios)
        if "drill" not in skip:
            check_holes(fab, rules, vios)
            check_annular_ring(fab, rules, vios)
        if "silk" not in skip:
            check_silk(fab, rules, vios, bg=bg)
            check_mask_dam(fab, rules, vios)

        parts_report = None
        if parts is not None:
            import bom_cpl
            parts_report = bom_cpl.run(pcb, tmp / "bom", parts_json=parts)
        facts.update(check_release(fab, n_layers, vios, parts_report))

        if polarity:
            nl, reason = _resolve_netlist(pcb, schematic, netlist, tmp)
            if nl is None:
                facts["polarity"] = {"status": "skipped", "reason": reason}
            else:
                facts["polarity"] = {"status": "checked",
                                     **check_polarity(bg, nl, vios)}
        else:
            facts["polarity"] = {"status": "disabled"}

        facts.update({
            "capability_key": key,
            "layer_count": n_layers,
            "copper_oz": copper_oz,
            "gerber_dir": str(gdir),
            "min_trace_width_mm": min(
                (w for n in fab.copper_layer_names()
                 if (lg := fab.copper(n)) and lg.trace_widths
                 for w in lg.trace_widths), default=None),
            "min_hole_mm": min((h.diameter for h in fab.holes), default=None),
        })
    payload = checklib.report("dfm_check", pcb, vios, **facts)
    # Warnings alone do not fail the gate (netlist_audit / fp_verify precedent):
    # KiCad's stock 0.12 mm silk and tight mask dams are advisory, not defects.
    has_error = any(v["severity"] == "error" for v in vios)
    payload["status"] = "violations" if has_error else "pass"
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True, help="input .kicad_pcb")
    ap.add_argument("--fab-dir", help="pre-exported fab dir (else export to a "
                                      "temp dir)")
    ap.add_argument("--copper-oz", type=float, default=1.0,
                    help="outer copper weight (capability table key)")
    ap.add_argument("--capabilities", help="override jlc_capabilities.yaml")
    ap.add_argument("--schematic", help="schematic for the polarity oracle")
    ap.add_argument("--netlist", help="netlist for the polarity oracle")
    ap.add_argument("--no-polarity", action="store_true",
                    help="skip the CPL polarity check")
    ap.add_argument("--parts", help="parts.json (BOM completeness)")
    ap.add_argument("--skip", default="",
                    help="comma list of groups to skip: copper,drill,silk")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    def _go():
        with warnings.catch_warnings():
            # gerbonara warns about kicad's G90-after-header drill dialect.
            warnings.simplefilter("ignore")
            rep = run(Path(args.pcb),
                      fab_dir=Path(args.fab_dir) if args.fab_dir else None,
                      copper_oz=args.copper_oz,
                      capabilities=Path(args.capabilities)
                      if args.capabilities else None,
                      schematic=Path(args.schematic) if args.schematic else None,
                      netlist=Path(args.netlist) if args.netlist else None,
                      polarity=not args.no_polarity,
                      parts=Path(args.parts) if args.parts else None,
                      skip=tuple(s for s in args.skip.split(",") if s))
        return rep, args.out

    return checklib.cli_wrap("dfm_check", _go)


if __name__ == "__main__":
    raise SystemExit(main())
