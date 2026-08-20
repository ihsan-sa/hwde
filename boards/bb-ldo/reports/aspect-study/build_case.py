"""build_case.py - pick the best legal placement for one W x H candidate and
emit the place_edit ops for it.

Board frame: the candidate outline keeps the delivered board's top-left corner
(5.125, 19.7) - board_edit --outline WxH --anchor topleft - so board-relative
(0,0) maps to that corner.

Bodies:
  cluster   U1+C1+C2 rigid, the exact P6 relative arrangement, rotated by theta
            about U1's tab.  Courtyard bbox rel tab per theta, from the board.
  terminals 10.0 (depth) x 10.42 (along) courtyards.  Wire entry = footprint
            local y=-5.5, so deg 0/90/180/270 -> entry up/left/down/right; the
            terminal is always seated with its entry face on the outer edge.
Legality enforced here: every courtyard >= KEEP mm inside the outline, >= CLR
between bodies.  Verified afterwards by place_metrics on the built board.
"""
import argparse
import json
import math
from pathlib import Path

ORIGIN = (5.125, 19.7)
TAB0 = (33.97, 32.91)
CLUSTER = {"U1": ((31.0, 32.91), 180.0), "C1": ((27.0, 37.31), 180.0),
           "C2": ((21.3775, 32.91), 0.0)}
CL = {0.0: (-17.345, -3.1, 1.42, 5.298), 90.0: (-3.1, -1.42, 5.298, 17.345),
      180.0: (-1.42, -5.298, 17.345, 3.1), 270.0: (-5.298, -17.345, 3.1, 1.42)}
PAD_CENTROID = (-4.455, 0.0)
TW, TL = 10.0, 10.42
CLR, KEEP, INSET, A_SAT = 0.4, 1.0, 0.5, 645.0
REACH = (A_SAT / math.pi) ** 0.5
EDGE_DEG = {"left": 90.0, "right": 270.0, "top": 0.0, "bottom": 180.0}


def rot(x, y, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (x * c - y * s, x * s + y * c)


def _g(r, x, y):
    if x <= 0 or y <= 0:
        return 0.0
    if x * x + y * y <= r * r:
        return x * y
    if x >= r and y >= r:
        return math.pi * r * r / 4.0
    if x >= r:
        return 0.5 * (y * math.sqrt(r * r - y * y) + r * r * math.asin(y / r))
    if y >= r:
        return 0.5 * (x * math.sqrt(r * r - x * x) + r * r * math.asin(x / r))
    return 0.5 * (y * math.sqrt(r * r - y * y) + x * math.sqrt(r * r - x * x)
                  + r * r * (math.asin(x / r) + math.asin(y / r) - math.pi / 2))


def _f(r, x, y):
    return (1 if x >= 0 else -1) * (1 if y >= 0 else -1) * _g(r, abs(x), abs(y))


def cap(cx, cy, r, W, H):
    x0, y0, x1, y1 = INSET, INSET, W - INSET, H - INSET
    a, b, c, d = x0 - cx, x1 - cx, y0 - cy, y1 - cy
    return _f(r, b, d) - _f(r, a, d) - _f(r, b, c) + _f(r, a, c)


def gaps_for(edge, W, H, cb):
    """Free intervals for a terminal centre along `edge`, given cluster box cb."""
    x0, y0, x1, y1 = cb
    if edge in ("left", "right"):
        bx0 = KEEP if edge == "left" else W - KEEP - TW
        if bx0 + TW <= x0 - CLR or bx0 >= x1 + CLR:
            return ([(KEEP + TL / 2, H - KEEP - TL / 2)]
                    if H - 2 * KEEP >= TL else [])
        lo, hi = KEEP, H - KEEP
        raw = [(lo, min(hi, y0 - CLR)), (max(lo, y1 + CLR), hi)]
    else:
        by0 = KEEP if edge == "top" else H - KEEP - TW
        if by0 + TW <= y0 - CLR or by0 >= y1 + CLR:
            return ([(KEEP + TL / 2, W - KEEP - TL / 2)]
                    if W - 2 * KEEP >= TL else [])
        lo, hi = KEEP, W - KEEP
        raw = [(lo, min(hi, x0 - CLR)), (max(lo, x1 + CLR), hi)]
    return [(a + TL / 2, b - TL / 2) for a, b in raw if b - a >= TL]


def term_box(edge, along, W, H):
    if edge in ("left", "right"):
        x0 = KEEP if edge == "left" else W - KEEP - TW
        return (x0, along - TL / 2, x0 + TW, along + TL / 2)
    y0 = KEEP if edge == "top" else H - KEEP - TW
    return (along - TL / 2, y0, along + TL / 2, y0 + TW)


def _hit(a, b):
    return (min(a[2], b[2]) - max(a[0], b[0]) > -CLR and
            min(a[3], b[3]) - max(a[1], b[1]) > -CLR)


def seats(mode, W, H, cb):
    """Two non-overlapping terminal seats, or None.  Candidate `along` values
    are each free gap's midpoint and both ends, which is enough to dodge a
    corner collision between two terminals on adjacent edges."""
    g = {e: gaps_for(e, W, H, cb) for e in EDGE_DEG}
    cand = {e: [(e, round(v, 4)) for a, b in gg
                for v in (a, (a + b) / 2.0, b)] for e, gg in g.items()}
    if mode == "pin":
        pairs = [(cand["left"], cand["right"])]
    else:
        order = sorted((e for e in EDGE_DEG if g[e]),
                       key=lambda e: -max(b - a for a, b in g[e]))
        pairs = [(cand[e1], cand[e2]) for i, e1 in enumerate(order)
                 for e2 in order[i:]]
    for c1, c2 in pairs:
        for s1 in c1:
            for s2 in c2:
                if s1 == s2:
                    continue
                if not _hit(term_box(*s1, W, H), term_box(*s2, W, H)):
                    return {"J1": s1, "J2": s2}
    return None


def search(W, H, mode, thetas, step=0.125, objective="r25"):
    best = None
    for th in thetas:
        cx0, cy0, cx1, cy1 = CL[th]
        x = KEEP - cx0
        while x <= W - KEEP - cx1 + 1e-9:
            y = KEEP - cy0
            while y <= H - KEEP - cy1 + 1e-9:
                cb = (x + cx0, y + cy0, x + cx1, y + cy1)
                s = seats(mode, W, H, cb)
                if s:
                    r25 = cap(x, y, 25.0, W, H)
                    pc = rot(PAD_CENTROID[0], PAD_CENTROID[1], -th)
                    ae = min(A_SAT, cap(x + pc[0], y + pc[1], REACH, W, H))
                    # lexicographic: primary metric, r25 as the
                    # tie-break so a saturated a_eff still picks a
                    # sensible tab instead of the first one found
                    score = ((round(ae, 3), round(r25, 3))
                             if objective == "a_eff"
                             else (round(r25, 3), round(ae, 3)))
                    if best is None or score > best["_score"]:
                        best = {"_score": score,
                                "objective": objective,
                                "theta": th, "tab": [round(x, 4), round(y, 4)],
                                "seats": s, "r25": round(r25, 3),
                                "r20": round(cap(x, y, 20.0, W, H), 3),
                                "r15": round(cap(x, y, 15.0, W, H), 3),
                                "a_eff": round(ae, 3),
                                "cluster_box": [round(v, 3) for v in cb]}
                y += step
            x += step
    return best


def ops_for(best, W, H):
    ops = []
    tabx = ORIGIN[0] + best["tab"][0]
    taby = ORIGIN[1] + best["tab"][1]
    th = best["theta"]
    for ref, (pos, ang) in CLUSTER.items():
        dx, dy = rot(pos[0] - TAB0[0], pos[1] - TAB0[1], -th)
        ops.append({"op": "place", "ref": ref, "x": round(tabx + dx, 4),
                    "y": round(taby + dy, 4), "deg": (ang + th) % 360.0,
                    "side": "front"})
    for ref, (edge, along) in best["seats"].items():
        deg = EDGE_DEG[edge]
        if edge == "left":
            p = (KEEP + 5.5, along)
        elif edge == "right":
            p = (W - KEEP - 5.5, along)
        elif edge == "top":
            p = (along, KEEP + 5.5)
        else:
            p = (along, H - KEEP - 5.5)
        ops.append({"op": "place", "ref": ref,
                    "x": round(ORIGIN[0] + p[0], 4),
                    "y": round(ORIGIN[1] + p[1], 4), "deg": deg,
                    "side": "front"})
    return ops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--w", type=float, required=True)
    ap.add_argument("--h", type=float, required=True)
    ap.add_argument("--mode", choices=("pin", "free"), default="pin")
    ap.add_argument("--theta", type=float, default=None)
    ap.add_argument("--tab", default=None,
                    help="x,y board-relative; skips the search")
    ap.add_argument("--objective", choices=("r25", "a_eff"), default="r25")
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    thetas = [a.theta] if a.theta is not None else list(CL)
    if a.tab:
        tx, ty = (float(v) for v in a.tab.split(","))
        th = a.theta if a.theta is not None else 0.0
        cx0, cy0, cx1, cy1 = CL[th]
        cb = (tx + cx0, ty + cy0, tx + cx1, ty + cy1)
        s = seats(a.mode, a.w, a.h, cb)
        if not s:
            raise SystemExit("no legal terminal seats for the forced tab")
        pc = rot(PAD_CENTROID[0], PAD_CENTROID[1], -th)
        best = {"theta": th, "tab": [tx, ty], "seats": s,
                "r25": round(cap(tx, ty, 25.0, a.w, a.h), 3),
                "r20": round(cap(tx, ty, 20.0, a.w, a.h), 3),
                "r15": round(cap(tx, ty, 15.0, a.w, a.h), 3),
                "a_eff": round(min(A_SAT, cap(tx + pc[0], ty + pc[1], REACH,
                                              a.w, a.h)), 3),
                "cluster_box": [round(v, 3) for v in cb]}
    else:
        best = search(a.w, a.h, a.mode, thetas, objective=a.objective)
    if best is None:
        raise SystemExit("%s: no legal placement at %sx%s %s"
                         % (a.name, a.w, a.h, a.mode))
    ops = ops_for(best, a.w, a.h)
    d = Path(a.outdir)
    d.mkdir(parents=True, exist_ok=True)
    (d / "ops.json").write_text(json.dumps({"version": 1, "ops": ops}, indent=1),
                                encoding="utf-8")
    plan = {"name": a.name, "W": a.w, "H": a.h, "area_mm2": round(a.w * a.h, 2),
            "aspect": round(max(a.w, a.h) / min(a.w, a.h), 4), "mode": a.mode,
            "predicted": best, "origin": list(ORIGIN), "ops": ops}
    (d / "plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    print(json.dumps({k: plan[k] for k in ("name", "W", "H", "area_mm2",
                                           "aspect", "mode", "predicted")},
                     indent=1))


if __name__ == "__main__":
    main()
