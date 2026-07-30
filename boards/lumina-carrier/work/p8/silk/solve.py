"""Greedy constrained solver: pull every non-H refdes toward its own footprint.

Objective  : minimise r = |text anchor - footprint origin|  (exactly what
             refdes_prox measures as offset_mm).
Constraints: the text's INKED box (from KiCad's own TransformTextToPolySet, so
             it is a superset of the glyph strokes DRC collides) must not touch
               - any footprint's silk polygons        -> silk_overlap
               - any pad's mask aperture              -> silk_over_copper
               - any other refdes text's inked box    -> silk_overlap
               - the board outline                    -> silk_edge_clearance
             TIER A additionally forbids intersecting ANY footprint's pad+silk
             convex hull (keeps labels in the channels, never printed under a
             package). TIER B drops the hull rule and enforces only the true
             DRC geometry - used only where TIER A has no solution.
Tie-break  : among candidates within SLACK of the best radius, prefer the one
             whose nearest OTHER part is clearly farther than its own part.

Usage: solve.py <geom.json> <inv.json> <out_ops.json> <out_plan.json>
       [--frozen frozen.json] [--pad extra_margin_mm] [--only R1,R2]
"""
from __future__ import annotations

import json
import math
import sys

MARGIN = 0.05        # mm gap demanded around the inked text box
EDGE_MARGIN = 0.10   # mm gap demanded to the board outline
R_START = 0.30
R_COARSE = 0.15
R_FINE = 0.05
SLACK = 0.50         # mm: radius band inside which attribution may decide
ATTRIB_MIN = 0.15    # mm: "clearly farther" threshold for own vs other
MAX_SCORE = 44       # candidates (lowest r first) put through attribution
SKIP = {"H1", "H2", "H3", "H4", "H5"}
ANGLES = (0.0, 90.0)
NDIR = 36
ROUNDS = 3


# ----------------------------------------------------------------- geometry
def pt_in_rect(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def pt_in_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        x1, y1 = poly[j]
        x2, y2 = poly[i]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        j = i
    return inside


def _o(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def seg_hit(a, b, c, d):
    d1, d2 = _o(c, d, a), _o(c, d, b)
    d3, d4 = _o(a, b, c), _o(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    for p, q, r in ((c, d, a), (c, d, b), (a, b, c), (a, b, d)):
        if abs(_o(p, q, r)) < 1e-12 \
                and min(p[0], q[0]) - 1e-12 <= r[0] <= max(p[0], q[0]) + 1e-12 \
                and min(p[1], q[1]) - 1e-12 <= r[1] <= max(p[1], q[1]) + 1e-12:
            return True
    return False


def rect_corners(r):
    return ((r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3]))


def rect_edge_list(r):
    c = rect_corners(r)
    return ((c[0], c[1]), (c[1], c[2]), (c[2], c[3]), (c[3], c[0]))


def seg_rect_hit(a, b, r):
    if pt_in_rect(a, r) or pt_in_rect(b, r):
        return True
    for e in rect_edge_list(r):
        if seg_hit(a, b, e[0], e[1]):
            return True
    return False


def rect_poly_hit(rect, poly):
    n = len(poly)
    j = n - 1
    for i in range(n):
        if seg_rect_hit(poly[j], poly[i], rect):
            return True
        j = i
    return pt_in_poly(((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2), poly)


def pt_seg_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    L = vx * vx + vy * vy
    t = 0.0 if L == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L))
    return math.hypot(wx - t * vx, wy - t * vy)


def seg_seg_dist(a, b, c, d):
    if seg_hit(a, b, c, d):
        return 0.0
    return min(pt_seg_dist(a, c, d), pt_seg_dist(b, c, d),
               pt_seg_dist(c, a, b), pt_seg_dist(d, a, b))


def rect_poly_dist(rect, poly):
    if rect_poly_hit(rect, poly):
        return 0.0
    res = 1e9
    redges = rect_edge_list(rect)
    n = len(poly)
    j = n - 1
    for i in range(n):
        a, b = poly[j], poly[i]
        for e in redges:
            v = seg_seg_dist(a, b, e[0], e[1])
            if v < res:
                res = v
        j = i
    return res


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) <= 2:
        return list(pts)

    def build(seq):
        st = []
        for p in seq:
            while len(st) >= 2 and _o(st[-2], st[-1], p) <= 0:
                st.pop()
            st.append(p)
        return st
    lo = build(pts)
    up = build(list(reversed(pts)))
    return lo[:-1] + up[:-1]


def bb_far(a, b, gap=0.0):
    """True if bboxes a,b cannot be within `gap`."""
    return (a[2] + gap < b[0] or a[0] - gap > b[2]
            or a[3] + gap < b[1] or a[1] - gap > b[3])


# ----------------------------------------------------------------- main
def main():
    argv = sys.argv[1:]
    frozen_path = None
    extra_pad = {}
    only = None
    park = set()
    i = 4
    while i < len(argv):
        if argv[i] == "--frozen":
            frozen_path = argv[i + 1]; i += 2
        elif argv[i] == "--pad":
            extra_pad = json.loads(argv[i + 1]); i += 2
        elif argv[i] == "--only":
            only = set(argv[i + 1].split(",")); i += 2
        elif argv[i] == "--park":
            park = set(argv[i + 1].split(",")); i += 2
        else:
            i += 1

    geom = json.load(open(argv[0], encoding="utf-8"))
    inv = json.load(open(argv[1], encoding="utf-8"))
    fps = {f["ref"]: f for f in geom["footprints"]}
    invm = {f["ref"]: f for f in inv["footprints"]}
    outline = [tuple(p) for p in geom["outline"][0]]
    out_edges = [(outline[j - 1], outline[j]) for j in range(len(outline))]
    out_edge_bb = [bbox(e) for e in out_edges]

    extent = {}
    for ref, f in invm.items():
        e = 0.0
        for p in f["pads"]:
            e = max(e, math.hypot(abs(p["x"]) + p["w"] / 2, abs(p["y"]) + p["h"] / 2))
        extent[ref] = e

    # --- obstacle tables -----------------------------------------------
    silk = []   # (owner, poly, bb)
    pads = []   # (owner, poly, bb)
    hulls = {}
    bodies = {}
    for ref, f in fps.items():
        bpts = []
        for s in f["silk"]:
            for poly in s["poly"]:
                pl = [tuple(p) for p in poly]
                bb = bbox(pl)
                silk.append((ref, pl, bb))
                bodies.setdefault(ref, []).append((pl, bb))
                bpts += pl
        for p in f["pads"]:
            if not p["on_f_mask"]:
                continue
            for poly in p["poly"]:
                pl = [tuple(q) for q in poly]
                bb = bbox(pl)
                pads.append((ref, pl, bb))
                bodies.setdefault(ref, []).append((pl, bb))
                bpts += pl
        if bpts:
            h = hull(bpts)
            hulls[ref] = (h, bbox(h))

    hull_list = [(r, h, hb) for r, (h, hb) in hulls.items()]

    def box_shape(ref, ang):
        t = fps[ref]["ref_text"]
        if ang == 0.0:
            w, h, off = t["inked_w0"], t["inked_h0"], t["off0"]
        else:
            w, h, off = t["inked_w90"], t["inked_h90"], t["off90"]
        return (off[0] - w / 2, off[1] - h / 2, off[0] + w / 2, off[1] + h / 2)

    tbox = {}
    for ref, f in fps.items():
        icx, icy, iw, ih = f["ref_text"]["inked"]
        tbox[ref] = (icx - iw / 2, icy - ih / 2, icx + iw / 2, icy + ih / 2)

    frozen = {}
    if frozen_path:
        frozen = json.load(open(frozen_path, encoding="utf-8"))
        for ref, v in frozen.items():
            s = box_shape(ref, v["deg"])
            tbox[ref] = (s[0] + v["x"], s[1] + v["y"], s[2] + v["x"], s[3] + v["y"])

    # parked refs: not solved here AND their text removed from the obstacle set,
    # so an unattributable label never squats in a slot a solvable label needs.
    for ref in park:
        tbox[ref] = (-1e9, -1e9, -1e9 + 1e-3, -1e9 + 1e-3)

    targets = [r for r in fps if r not in SKIP and r not in frozen and r not in park]
    if only:
        targets = [r for r in targets if r in only]

    dirs = [(math.cos(2 * math.pi * k / NDIR), math.sin(2 * math.pi * k / NDIR))
            for k in range(NDIR)]

    def solve_one(ref):
        f = fps[ref]
        ox, oy = f["x"], f["y"]
        hrad = 1.0
        if ref in hulls:
            hrad = max(math.hypot(p[0] - ox, p[1] - oy) for p in hulls[ref][0])
        rmax = min(18.0, max(3.5, hrad + 4.5))
        pad = MARGIN + extra_pad.get(ref, 0.0)
        win = (ox - rmax - 5, oy - rmax - 5, ox + rmax + 5, oy + rmax + 5)
        L_silk = [(p, bb) for (o, p, bb) in silk if not bb_far(bb, win)]
        L_pad = [(p, bb) for (o, p, bb) in pads if not bb_far(bb, win)]
        L_hull = [(h, hb) for (o, h, hb) in hull_list if not bb_far(hb, win)]
        L_body = [(o, [(pl, bb) for (pl, bb) in polys if not bb_far(bb, win)])
                  for o, polys in bodies.items() if o not in SKIP
                  and not bb_far(hulls[o][1], win)]
        L_tb = [(o, b) for o, b in tbox.items()
                if o != ref and not bb_far(b, win)]
        L_out = [e for e, bb in zip(out_edges, out_edge_bb) if not bb_far(bb, win)]
        centre_in = pt_in_poly((ox, oy), outline)
        shapes = {a: box_shape(ref, a) for a in ANGLES}

        def rect_of(ang, px, py):
            s = shapes[ang]
            return (s[0] + px - pad, s[1] + py - pad,
                    s[2] + px + pad, s[3] + py + pad)

        def ok(ang, px, py, tier):
            r = rect_of(ang, px, py)
            if L_out:
                rr = (r[0] - EDGE_MARGIN + pad, r[1] - EDGE_MARGIN + pad,
                      r[2] + EDGE_MARGIN - pad, r[3] + EDGE_MARGIN - pad)
                for c in rect_corners(rr):
                    if not pt_in_poly(c, outline):
                        return False
                for e in L_out:
                    if seg_rect_hit(e[0], e[1], rr):
                        return False
            elif not centre_in:
                return False
            rx0, ry0, rx1, ry1 = r
            for _o_, b in L_tb:
                if not (rx1 < b[0] or rx0 > b[2] or ry1 < b[1] or ry0 > b[3]):
                    return False
            for poly, bb in (L_hull if tier == 0 else L_silk):
                if rx1 < bb[0] or rx0 > bb[2] or ry1 < bb[1] or ry0 > bb[3]:
                    continue
                if rect_poly_hit(r, poly):
                    return False
            if tier == 1:
                for poly, bb in L_pad:
                    if rx1 < bb[0] or rx0 > bb[2] or ry1 < bb[1] or ry0 > bb[3]:
                        continue
                    if rect_poly_hit(r, poly):
                        return False
            return True

        best_r, found_tier, rays = None, None, {}
        for tier in (0, 1):
            rays = {}
            best_r = None
            for k, (dx, dy) in enumerate(dirs):
                for ang in ANGLES:
                    hit = None
                    r = R_START
                    while r <= rmax + 1e-9:
                        if ok(ang, ox + r * dx, oy + r * dy, tier):
                            hit = r
                            break
                        r += R_COARSE
                    if hit is None:
                        continue
                    lo = hit - R_COARSE
                    while lo > R_START - 1e-9:
                        if ok(ang, ox + lo * dx, oy + lo * dy, tier):
                            hit = lo
                        else:
                            break
                        lo -= R_FINE
                    r2 = hit - R_FINE
                    while r2 > R_START - 1e-9:
                        if ok(ang, ox + r2 * dx, oy + r2 * dy, tier):
                            hit = r2
                            r2 -= R_FINE
                        else:
                            break
                    rays[(k, ang)] = hit
                    if best_r is None or hit < best_r:
                        best_r = hit
            if best_r is not None:
                found_tier = tier
                break
        if best_r is None:
            return None

        pool = sorted(((k, a, r) for (k, a), r in rays.items()),
                      key=lambda c: c[2])[:MAX_SCORE]

        def attribution(rect):
            d_own, d_oth, who = 1e9, 1e9, None
            for other, polys in L_body:
                dd = 1e9
                for (pl, bb) in polys:
                    if bb_far(bb, rect, 9.0):
                        continue
                    v = rect_poly_dist(rect, pl)
                    if v < dd:
                        dd = v
                    if dd <= 0.0:
                        break
                if dd > 8.0:
                    continue
                if other == ref:
                    d_own = dd
                elif dd < d_oth:
                    d_oth, who = dd, other
            return d_own, d_oth, who

        scored = []
        for k, ang, r in pool:
            dx, dy = dirs[k]
            px, py = ox + r * dx, oy + r * dy
            s = shapes[ang]
            rect = (s[0] + px, s[1] + py, s[2] + px, s[3] + py)
            d_own, d_oth, who = attribution(rect)
            th = math.degrees(math.atan2(dy, dx)) % 90.0
            card = min(th, 90.0 - th) <= 6.0
            scored.append({"k": k, "ang": ang, "r": round(r, 4),
                           "px": px, "py": py, "d_own": d_own,
                           "d_other": d_oth, "who": who, "card": card,
                           "own_nearest": d_own < d_oth,
                           "ok": (d_oth - d_own) > ATTRIB_MIN,
                           "margin": d_oth - d_own})
        pure = sorted(scored, key=lambda c: (round(c["r"] / 0.05), not c["card"],
                                             -c["margin"]))[0]
        # HARD attribution filter: the label's own part must be the nearest part.
        # Soft preference (inside the SLACK band): "clearly" nearest by ATTRIB_MIN.
        cand = [c for c in scored if c["own_nearest"]]
        attr_class = 0 if cand else 1
        if not cand:
            cand = scored
        base = min(c["r"] for c in cand)
        band = [c for c in cand if c["r"] <= base + SLACK + 1e-9]
        pick = sorted(band, key=lambda c: (not c["ok"], round(c["r"] / 0.10),
                                           not c["card"], -c["margin"]))[0]
        return {"ref": ref, "tier": found_tier, "pick": pick, "pure": pure,
                "attr_class": attr_class, "n_pool": len(scored),
                "tie_break": (abs(pick["r"] - pure["r"]) > 1e-6
                              or pick["k"] != pure["k"] or pick["ang"] != pure["ang"])}

    def crowd(ref):
        ox, oy = fps[ref]["x"], fps[ref]["y"]
        return sum(1 for o, g in fps.items()
                   if o != ref and math.hypot(g["x"] - ox, g["y"] - oy) <= 4.0)
    order = sorted(targets, key=lambda r: (-crowd(r), r))

    def set_box(ref, p):
        s = box_shape(ref, p["ang"])
        tbox[ref] = (s[0] + p["px"], s[1] + p["py"],
                     s[2] + p["px"], s[3] + p["py"])

    plan, fails = {}, []
    for ref in order:
        res = solve_one(ref)
        if res is None:
            fails.append(ref)
            continue
        set_box(ref, res["pick"])
        plan[ref] = res

    for _ in range(ROUNDS):
        moved = 0
        for ref in order:
            cur = plan.get(ref)
            old = tbox[ref]
            tbox[ref] = (-1e9, -1e9, -1e9 + 1e-3, -1e9 + 1e-3)
            res = solve_one(ref)
            if res is None:
                tbox[ref] = old
                continue
            p = res["pick"]
            key_new = (res["tier"], res["attr_class"], round(p["r"], 3),
                       not p["ok"])
            key_old = (1e9, 1e9, 1e9, True) if cur is None else \
                (cur["tier"], cur["attr_class"], round(cur["pick"]["r"], 3),
                 not cur["pick"]["ok"])
            if key_new < key_old:
                set_box(ref, p)
                plan[ref] = res
                if ref in fails:
                    fails.remove(ref)
                moved += 1
            else:
                tbox[ref] = old
        if not moved:
            break

    ops, rows = [], []
    for ref in sorted(plan):
        p = plan[ref]["pick"]
        ops.append({"op": "move_text", "ref": ref, "field": "reference",
                    "x": round(p["px"], 4), "y": round(p["py"], 4),
                    "deg": p["ang"]})
        rows.append({"ref": ref, "tier": plan[ref]["tier"],
                     "attr_class": plan[ref]["attr_class"], "r": round(p["r"], 4),
                     "extent": round(extent[ref], 3),
                     "beyond": round(p["r"] - extent[ref], 3),
                     "ang": p["ang"], "d_own": round(min(p["d_own"], 99), 3),
                     "d_other": round(min(p["d_other"], 99), 3), "who": p["who"],
                     "tie_break": plan[ref]["tie_break"], "card": p["card"],
                     "pool": plan[ref]["n_pool"]})
    json.dump({"version": 1, "ops": ops}, open(argv[2], "w", encoding="utf-8"), indent=1)
    json.dump({"rows": rows, "unsolved": fails},
              open(argv[3], "w", encoding="utf-8"), indent=1)
    beyond = sorted(r["beyond"] for r in rows)
    print(json.dumps({
        "solved": len(rows), "unsolved": fails,
        "tier1": [r["ref"] for r in rows if r["tier"] == 1],
        "tie_break_count": sum(1 for r in rows if r["tie_break"]),
        "not_own_nearest": [r["ref"] for r in rows if r["attr_class"] == 1],
        "attrib_marginal": [(r["ref"], round(r["d_other"] - r["d_own"], 3))
                            for r in rows
                            if 0 < r["d_other"] - r["d_own"] <= ATTRIB_MIN],
        "beyond_over_1mm": sum(1 for r in rows if r["beyond"] > 1.0),
        "beyond_over_1_5mm": [(r["ref"], r["beyond"]) for r in rows if r["beyond"] > 1.5],
        "median_r": round(sorted(r["r"] for r in rows)[len(rows) // 2], 3),
        "max_r": round(max(r["r"] for r in rows), 3),
        "beyond_median": round(beyond[len(beyond) // 2], 3),
        "beyond_max": round(beyond[-1], 3),
    }, indent=1))


if __name__ == "__main__":
    main()
