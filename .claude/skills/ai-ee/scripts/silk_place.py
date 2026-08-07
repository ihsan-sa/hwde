"""silk_place - refdes silk solver: pull labels to their parts, collision-free (T6 p1).

Owns the machine-verified greedy recipe that previously lived as prose
(LEARNINGS 2026-07-28 [placement][drc][silk]; re-proven at scale by the
lumina-carrier wo-silklegibility order, 116 refdes):

  1. candidates at BOTH text angles on ALL FOUR sides of the part
     (0 deg above/below + 90 deg left/right) plus the lib_refdes_norm
     default target (pad_top - 0.25 - text_height/2, local x 0) - the
     default IS the answer for most parts, deviate only on collision;
  2. score = (min(clearance, 0.30), -distance_to_own_pads_and_silk):
     stop paying for clearance beyond 0.30 mm, then maximise closeness;
  3. process the MOST CROWDED parts first (descending neighbour count
     within 4 mm) - largest-first orphans the boxed-in small caps.

Text box: per-char advance 0.845*size + stroke, height size + stroke
(placelib.text_box, measured constants - 0.75 and 1.0 per char are both
wrong).  A refdes field's stored angle is ABSOLUTE board-frame; its stored
position is LOCAL - never add the footprint rotation to the angle.
min_silk_clearance is read from the live .kicad_pro (per-board values
differ; wo-silklegibility guidance).

Emits a place_edit-compatible {"version": 1, "ops": [move_text ...]} file
(absolute board coords) + a report {moved, residual[],
median_beyond_extent_mm before/after}.  --apply pushes the ops through
place_edit's atomic pipeline; --verify-drc then runs the REAL DRC and
reports silk-class findings (check_silk is lenient and never the oracle,
LEARNINGS 2026-07-27).  Cut from the full recipe (reported): no automatic
batch-bisect on a DRC regression - the report carries the findings and the
agent bisects.  Board-only refs (H*) and hidden texts are never touched.

Exit 0 all placed / 1 residuals or post-apply silk DRC findings / 2 error.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))

import checklib  # noqa: E402
import placelib  # noqa: E402
from checklib import CheckError  # noqa: E402
from geom import _is_node, _kid, _kids, _nums, _pts, _rot, _strs, _tok  # noqa: E402

SCRIPT = "silk_place"
CLEAR_CAP = 0.30       # stop paying for clearance beyond this (recipe rule 2)
HARD_FLOOR = 0.02      # never accept a touching candidate even at min_clear 0
CROWD_RADIUS = 4.0     # neighbour radius for the crowded-first ordering
PUSHES = [i * 0.25 for i in range(13)]        # outward 0..3.0 mm
SLIDES = [0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0]
SILK_LAYERS = {"F.SilkS", "B.SilkS"}


# ---------------------------------------------------------------- parsing

def _fp_abs(pos, deg, local):
    dx, dy = _rot(local[0], local[1], -deg)
    return (pos[0] + dx, pos[1] + dy)


def parse_board(pcb: Path):
    """-> (ref_texts {ref: {...}}, silk {side: [geoms]}, gr_texts [...]).

    ref_texts: local position + ABSOLUTE angle + font of every Reference
    property; silk: footprint silk graphics + board gr_* silk items as
    absolute shapely geoms per side."""
    import sexpdata
    tree = sexpdata.loads(pcb.read_text(encoding="utf-8"))
    ref_texts: dict[str, dict] = {}
    silk = {"front": [], "back": []}

    def _silk_side(layer):
        return "front" if layer == "F.SilkS" else \
            "back" if layer == "B.SilkS" else None

    def _font(node):
        size, thick = 1.0, 0.15
        eff = _kid(node, "effects")
        if eff is not None:
            font = _kid(eff, "font")
            if font is not None:
                s = _kid(font, "size")
                if s is not None:
                    ns = _nums(s)
                    if ns:
                        size = ns[0]
                t = _kid(font, "thickness")
                if t is not None:
                    nt = _nums(t)
                    if nt:
                        thick = nt[0]
        return size, thick

    def _hidden(node):
        # (hide yes) hides, (hide no) does not - test the VALUE (LEARNINGS)
        h = _kid(node, "hide")
        if h is None:
            return False
        vals = [_tok(t) for t in h[1:] if not _is_node(t)]
        return "no" not in vals

    def _graphic_geom(g, head):
        w = 0.12
        stroke = _kid(g, "stroke")
        if stroke is not None:
            wn = _kid(stroke, "width")
            if wn is not None and _nums(wn):
                w = _nums(wn)[0]
        try:
            if head in ("fp_line", "gr_line"):
                s, e = _nums(_kid(g, "start")), _nums(_kid(g, "end"))
                from shapely.geometry import LineString
                return LineString([(s[0], s[1]), (e[0], e[1])]).buffer(w / 2)
            if head in ("fp_rect", "gr_rect"):
                s, e = _nums(_kid(g, "start")), _nums(_kid(g, "end"))
                return box(min(s[0], e[0]), min(s[1], e[1]),
                           max(s[0], e[0]), max(s[1], e[1])) \
                    .exterior.buffer(w / 2)
            if head in ("fp_circle", "gr_circle"):
                c, e = _nums(_kid(g, "center")), _nums(_kid(g, "end"))
                r = math.hypot(e[0] - c[0], e[1] - c[1])
                return Point(c[0], c[1]).buffer(r + w / 2)
            if head in ("fp_poly", "gr_poly"):
                pts = _pts(_kid(g, "pts"))
                if len(pts) >= 3:
                    return Polygon(pts).buffer(w / 2)
            if head in ("fp_arc", "gr_arc"):
                import geom as _g
                s = _nums(_kid(g, "start"))
                m = _nums(_kid(g, "mid"))
                e = _nums(_kid(g, "end"))
                from shapely.geometry import LineString
                return LineString(_g._arc_points(
                    (s[0], s[1]), (m[0], m[1]), (e[0], e[1]))).buffer(w / 2)
        except (TypeError, IndexError):
            return None
        return None

    for fp in _kids(tree, "footprint"):
        at = _kid(fp, "at")
        nums = _nums(at) if at is not None else [0.0, 0.0]
        pos = (nums[0], nums[1])
        deg = nums[2] if len(nums) > 2 else 0.0
        ref = None
        for prop in _kids(fp, "property"):
            s = _strs(prop)
            if len(s) >= 2 and s[0] == "Reference":
                ref = s[1]
                pat = _kid(prop, "at")
                pn = _nums(pat) if pat is not None else [0.0, 0.0, 0.0]
                lay = _kid(prop, "layer")
                layer = _strs(lay)[0] if lay is not None and _strs(lay) \
                    else "F.SilkS"
                size, thick = _font(prop)
                ref_texts[ref] = {
                    "local": (pn[0], pn[1]),
                    "deg": pn[2] if len(pn) > 2 else 0.0,   # ABSOLUTE
                    "layer": layer, "size": size, "thickness": thick,
                    "hidden": _hidden(prop),
                }
                break
        # footprint silk graphics -> absolute geoms
        for head in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc"):
            for g in _kids(fp, head):
                lay = _kid(g, "layer")
                lname = _strs(lay)[0] if lay is not None and _strs(lay) else ""
                side = _silk_side(lname)
                if side is None:
                    continue
                geom_local = _graphic_geom(g, head)
                if geom_local is None or geom_local.is_empty:
                    continue
                geo = affinity.translate(
                    affinity.rotate(geom_local, -deg, origin=(0, 0)),
                    pos[0], pos[1])
                silk[side].append((geo, ref))
        # fp_text user items on silk (DIP-switch style markings)
        for t in _kids(fp, "fp_text"):
            s = _strs(t)
            if len(s) < 2:
                continue
            lay = _kid(t, "layer")
            lname = _strs(lay)[0] if lay is not None and _strs(lay) else ""
            side = _silk_side(lname)
            if side is None or _hidden(t):
                continue
            tat = _kid(t, "at")
            tn = _nums(tat) if tat is not None else [0.0, 0.0]
            tx, ty = _fp_abs(pos, deg, (tn[0], tn[1]))
            tdeg = tn[2] if len(tn) > 2 else 0.0    # absolute, like property
            size, thick = _font(t)
            silk[side].append(
                (placelib.text_box(s[1], size, thick, tx, ty, tdeg), ref))

    # board-frame silk items
    for head in ("gr_text",):
        for t in _kids(tree, head):
            s = _strs(t)
            lay = _kid(t, "layer")
            lname = _strs(lay)[0] if lay is not None and _strs(lay) else ""
            side = _silk_side(lname)
            if side is None or not s:
                continue
            tat = _kid(t, "at")
            tn = _nums(tat) if tat is not None else [0.0, 0.0]
            tdeg = tn[2] if len(tn) > 2 else 0.0
            size, thick = _font(t)
            silk[side].append(
                (placelib.text_box(s[0], size, thick, tn[0], tn[1], tdeg),
                 None))
    for head in ("gr_line", "gr_rect", "gr_circle", "gr_poly", "gr_arc"):
        for g in _kids(tree, head):
            lay = _kid(g, "layer")
            lname = _strs(lay)[0] if lay is not None and _strs(lay) else ""
            side = _silk_side(lname)
            if side is None:
                continue
            geo = _graphic_geom(g, head)
            if geo is not None and not geo.is_empty:
                silk[side].append((geo, None))
    return ref_texts, silk


# ---------------------------------------------------------------- geometry

def _pad_polys_abs(fp: placelib.Footprint):
    """Per-pad absolute polygons, per-pad rotation applied (bbox model)."""
    out = []
    for p in fp.pads:
        th = math.radians(p.rot)
        c, s = abs(math.cos(th)), abs(math.sin(th))
        hx = p.size[0] / 2 * c + p.size[1] / 2 * s
        hy = p.size[0] / 2 * s + p.size[1] / 2 * c
        b = box(p.local[0] - hx, p.local[1] - hy,
                p.local[0] + hx, p.local[1] + hy)
        out.append(affinity.translate(
            affinity.rotate(b, -fp.angle, origin=(0, 0)),
            fp.pos[0], fp.pos[1]))
    return out


def _current_box(ref, fp, info):
    x, y = _fp_abs(fp.pos, fp.angle, info["local"])
    return placelib.text_box(ref, info["size"], info["thickness"],
                             x, y, info["deg"])


def _pad_extent_abs(fp):
    polys = _pad_polys_abs(fp)
    return unary_union(polys) if polys else fp.extents_abs()


# ---------------------------------------------------------------- solver

def _candidates(fp, info, own_pads_local_top):
    """Deterministic candidate list [(x, y, deg)] - normalizer target first,
    then all four sides x slides x outward pushes."""
    h = info["size"] + info["thickness"]
    ext = fp.extents_abs()
    x0, y0, x1, y1 = ext.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cands = []
    if own_pads_local_top is not None:
        tx, ty = _fp_abs(fp.pos, fp.angle,
                         (0.0, own_pads_local_top - 0.25 - h / 2))
        cands.append((tx, ty, 0.0))
    for push in PUSHES:
        for slide in SLIDES:
            g = 0.1 + push
            cands.append((cx + slide, y0 - g - h / 2, 0.0))     # above
            cands.append((cx + slide, y1 + g + h / 2, 0.0))     # below
            cands.append((x0 - g - h / 2, cy + slide, 90.0))    # left
            cands.append((x1 + g + h / 2, cy + slide, 90.0))    # right
    return cands


def _clearance(boxp, obstacles, cap):
    """min distance to obstacles (bounds-prefiltered); None on intersection."""
    bx0, by0, bx1, by1 = boxp.bounds
    clear = cap
    for ob in obstacles:
        ox0, oy0, ox1, oy1 = ob.bounds
        if ox0 > bx1 + cap or ox1 < bx0 - cap \
                or oy0 > by1 + cap or oy1 < by0 - cap:
            continue
        if boxp.intersects(ob):
            return None
        d = boxp.distance(ob)
        if d < clear:
            clear = d
    return clear


def solve(pcb: Path, refs: list[str] | None, min_clear: float):
    """-> (ops, results, residual, skipped) - pure geometry, no board writes."""
    model = placelib.PlaceModel(pcb)
    ref_texts, silk = parse_board(pcb)
    outline = model.outline

    targets = []
    skipped = []
    for ref in sorted(model.footprints):
        fp = model.footprints[ref]
        info = ref_texts.get(ref)
        if refs is not None and ref not in refs:
            continue
        if info is None:
            skipped.append({"ref": ref, "reason": "no Reference property"})
            continue
        if info["hidden"]:
            skipped.append({"ref": ref, "reason": "hidden"})
            continue
        if "board_only" in fp.attrs:
            skipped.append({"ref": ref, "reason": "board_only"})
            continue
        if info["layer"] not in SILK_LAYERS:
            skipped.append({"ref": ref,
                            "reason": f"refdes on {info['layer']}, not silk"})
            continue
        targets.append(ref)

    # crowded-first ordering (recipe rule 3)
    ext_of = {r: model.footprints[r].extents_abs() for r in model.footprints}

    def crowd(ref):
        e = ext_of[ref]
        return sum(1 for o in model.footprints
                   if o != ref and e.distance(ext_of[o]) <= CROWD_RADIUS)

    targets.sort(key=lambda r: (-crowd(r), r))
    target_set = set(targets)

    # static obstacles per side: pads (through pads on both), silk graphics
    # (a part's own geoms are excluded per-candidate), non-target labels
    static = {"front": [], "back": []}
    own_geoms: dict[str, list] = {r: [] for r in model.footprints}
    for ref in sorted(model.footprints):
        fp = model.footprints[ref]
        for i, pp in enumerate(_pad_polys_abs(fp)):
            through = fp.pads[i].through
            for side in ("front", "back"):
                if side == fp.side or through:
                    static[side].append((pp, ref))
            own_geoms[ref].append(pp)
    for side in ("front", "back"):
        for geo, owner in silk[side]:
            static[side].append((geo, owner))
            if owner in own_geoms:
                own_geoms[owner].append(geo)
    for ref, info in ref_texts.items():
        if ref in target_set or info["hidden"] or ref not in model.footprints:
            continue
        side = "front" if info["layer"].startswith("F.") else "back"
        static[side].append((_current_box(ref, model.footprints[ref], info),
                             ref))

    ops, results, residual = [], [], []
    placed_boxes = {"front": [], "back": []}
    for ref in targets:
        fp = model.footprints[ref]
        info = ref_texts[ref]
        side = "front" if info["layer"].startswith("F.") else "back"
        obstacles = [g for g, owner in static[side] if owner != ref] \
            + own_geoms[ref] + placed_boxes[side]
        own = unary_union(own_geoms[ref]) if own_geoms[ref] \
            else ext_of[ref]
        pad_top = min((p.local[1]
                       - (abs(math.sin(math.radians(p.rot))) * p.size[0]
                          + abs(math.cos(math.radians(p.rot))) * p.size[1]) / 2
                       for p in fp.pads), default=None)
        best, best_score = None, None
        for (x, y, deg) in _candidates(fp, info, pad_top):
            b = placelib.text_box(ref, info["size"], info["thickness"],
                                  x, y, deg)
            if not b.within(outline):
                continue
            clear = _clearance(b, obstacles, CLEAR_CAP)
            if clear is None or clear <= max(min_clear, HARD_FLOOR):
                continue
            score = (round(min(clear, CLEAR_CAP), 3),
                     -round(b.distance(own), 3))
            if best_score is None or score > best_score:
                best, best_score = (x, y, deg, b), score
        if best is None:
            residual.append({"ref": ref, "reason":
                             "no collision-free candidate within +3.0 mm "
                             "push (channel narrower than the label)"})
            # current box stays; count it as an obstacle for later labels
            placed_boxes[side].append(_current_box(ref, fp, info))
            continue
        x, y, deg, b = best
        placed_boxes[side].append(b)
        cur = _fp_abs(fp.pos, fp.angle, info["local"])
        moved = (abs(cur[0] - x) > 1e-3 or abs(cur[1] - y) > 1e-3
                 or place_edit_angdiff(info["deg"], deg) > 0.05)
        if moved:
            ops.append({"op": "move_text", "ref": ref, "field": "reference",
                        "x": checklib.rnd(x), "y": checklib.rnd(y),
                        "deg": checklib.rnd(deg)})
        beyond = b.distance(_pad_extent_abs(fp))
        results.append({"ref": ref, "moved": moved,
                        "clearance_mm": best_score[0],
                        "beyond_extent_mm": checklib.rnd(beyond)})
    return ops, results, residual, skipped, model, ref_texts


def place_edit_angdiff(a: float, b: float) -> float:
    d = abs(a - b) % 180.0            # text reads the same at 0/180
    return min(d, 180.0 - d)


def _median(vals):
    if not vals:
        return None
    vals = sorted(vals)
    n = len(vals)
    mid = n // 2
    return checklib.rnd(vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2)


def _beyond_before(model, ref_texts, refs):
    out = []
    for ref in refs:
        fp = model.footprints[ref]
        info = ref_texts[ref]
        b = _current_box(ref, fp, info)
        out.append(b.distance(_pad_extent_abs(fp)))
    return out


def read_min_silk_clearance(pcb: Path) -> float:
    """Live value from the sibling .kicad_pro; 0.0 (the KiCad default) when
    absent - per-board values differ (wo-silklegibility guidance)."""
    pro = pcb.with_suffix(".kicad_pro")
    if not pro.is_file():
        return 0.0
    try:
        doc = json.loads(pro.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0.0
    return float((doc.get("board", {}).get("design_settings", {})
                  .get("rules", {}) or {}).get("min_silk_clearance", 0.0))


# ---------------------------------------------------------------- driver

def run(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--refs", default=None,
                    help="comma-separated refdes subset (default: every "
                         "visible non-board_only silk refdes)")
    ap.add_argument("--ops-out", default=None,
                    help="ops file path (default <board dir>/silk_ops.json)")
    ap.add_argument("--min-clearance", type=float, default=None,
                    help="override the .kicad_pro min_silk_clearance")
    ap.add_argument("--apply", action="store_true",
                    help="apply the ops via place_edit's atomic pipeline")
    ap.add_argument("--verify-drc", action="store_true",
                    help="after --apply, run the real DRC and report "
                         "silk-class findings (the authoritative oracle)")
    ap.add_argument("--out-report", default=None)
    args = ap.parse_args(argv)

    pcb = Path(args.pcb)
    if not pcb.is_file():
        raise CheckError(f"board not found: {pcb}")
    if args.verify_drc and not args.apply:
        raise CheckError("--verify-drc needs --apply (it checks the board "
                         "the ops were applied to)")

    refs = [r.strip() for r in args.refs.split(",")] if args.refs else None
    min_clear = args.min_clearance if args.min_clearance is not None \
        else read_min_silk_clearance(pcb)

    ops, results, residual, skipped, model, ref_texts = \
        solve(pcb, refs, min_clear)

    before = _beyond_before(model, ref_texts, [r["ref"] for r in results])
    ops_path = Path(args.ops_out) if args.ops_out \
        else pcb.parent / "silk_ops.json"
    ops_path.write_text(json.dumps({"version": 1, "ops": ops}, indent=1),
                        encoding="utf-8")

    violations = [checklib.violation(
        SCRIPT, "warning", None, None, None, [r["ref"]],
        f"{r['ref']}: {r['reason']}", SCRIPT, kind="silk_residual")
        for r in residual]

    facts = {
        "targets": len(results) + len(residual),
        "moved": len(ops),
        "residual": residual,
        "skipped": skipped,
        "min_silk_clearance": min_clear,
        "median_beyond_extent_mm_before": _median(before),
        "median_beyond_extent_mm": _median(
            [r["beyond_extent_mm"] for r in results]),
        "ops_out": str(ops_path),
        "results": results,
    }

    if args.apply:
        if ops:
            import place_edit
            place_edit.apply_ops(pcb, ops)
        facts["applied"] = bool(ops)
        if args.verify_drc:
            import env
            import kc
            cli = env.find_kicad_cli()
            if cli is None:
                raise CheckError("--verify-drc needs kicad-cli (env.py)")
            drc = kc.run_drc(cli, pcb)
            silk_hits = [v for v in drc["violations"]
                         if "silk" in (v.get("check") or "")]
            facts["drc_silk_total"] = len(silk_hits)
            facts["drc_total"] = drc["counts"]["total"]
            for v in silk_hits:
                violations.append(checklib.violation(
                    SCRIPT, "error", tuple(v["pos"]) if v.get("pos") else None,
                    v.get("layer"), v.get("net"), v.get("refs"),
                    f"post-apply DRC: {v.get('msg')}", SCRIPT,
                    kind="silk_drc_regression"))

    payload = checklib.report(SCRIPT, str(pcb), violations, **facts)
    return payload, args.out_report


def main(argv: list[str] | None = None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
