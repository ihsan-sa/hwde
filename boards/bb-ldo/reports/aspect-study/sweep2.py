"""sweep2.py - ANALYTIC pre-sweep #2 (the one the candidate list comes from).

Model, corrected from sweep.py: the board OUTLINE is an explicit W x H at a
fixed AREA (the quantity P6 actually earned), not a fit around wherever the
parts happen to land.  Capture then depends only on the tab position inside
that rectangle; the two screw terminals affect nothing but FEASIBILITY, since
their only copper footprint is 2 pads each.

  pour        = board rect inset 0.5 mm (planes_gen --inset-mm default)
  cluster     = U1+C1+C2 rigid, exactly the P6 relative arrangement, rotated
                by theta about U1's tab; must sit >= 1.0 mm inside the outline
  terminals   = 10.0 x 10.42 courtyards.  PIN: J1 anywhere along the left edge,
                J2 anywhere along the right edge (constraints.json placement.
                edges; `pos` is advisory and unchecked).  FREE: any edge.
                A candidate is feasible iff a non-overlapping slot exists.
Reported: a_eff on check_thermal's own reach disc about the PAD CENTROID, and
the P6 r15/r20/r25 discs about the TAB.
"""
import json, math, sys
from pathlib import Path

A_SAT = 645.0
REACH = (A_SAT / math.pi) ** 0.5
CL = {0.0: (-17.345, -3.1, 1.42, 5.298),
      90.0: (-3.1, -1.42, 5.298, 17.345),
      180.0: (-1.42, -5.298, 17.345, 3.1),
      270.0: (-5.298, -17.345, 3.1, 1.42)}
PAD_CENTROID = (-4.455, 0.0)
TW, TL = 10.0, 10.42          # terminal depth (off the edge) x length (along)
CLR, KEEP, INSET = 0.4, 1.0, 0.5


def rot(x, y, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
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


def cap(cx, cy, r, x0, y0, x1, y1):
    a, b, c, d = x0 - cx, x1 - cx, y0 - cy, y1 - cy
    return _f(r, b, d) - _f(r, a, d) - _f(r, b, c) + _f(r, a, c)


def slot_free(edge, W, H, cb):
    """Is there a legal terminal seat on `edge` clear of cluster box cb?"""
    x0, y0, x1, y1 = cb
    if edge in ("left", "right"):
        bx0 = KEEP if edge == "left" else W - KEEP - TW
        bx1 = bx0 + TW
        if bx1 <= x0 - CLR or bx0 >= x1 + CLR:
            return True                     # no x overlap at all
        lo, hi = KEEP, H - KEEP             # need TL of free y in [lo,hi]
        gaps = [(lo, min(hi, y0 - CLR)), (max(lo, y1 + CLR), hi)]
    else:
        by0 = KEEP if edge == "top" else H - KEEP - TW
        by1 = by0 + TW
        if by1 <= y0 - CLR or by0 >= y1 + CLR:
            return True
        lo, hi = KEEP, W - KEEP
        gaps = [(lo, min(hi, x0 - CLR)), (max(lo, x1 + CLR), hi)]
    return any(b - a >= TL for a, b in gaps)


def evaluate(W, H, theta, mode, step=0.25):
    cx0, cy0, cx1, cy1 = CL[theta]
    P = (INSET, INSET, W - INSET, H - INSET)
    best, n = None, 0
    x = KEEP - cx0
    while x <= W - KEEP - cx1 + 1e-9:
        y = KEEP - cy0
        while y <= H - KEEP - cy1 + 1e-9:
            cb = (x + cx0, y + cy0, x + cx1, y + cy1)
            if mode == "pin":
                ok = slot_free("left", W, H, cb) and slot_free("right", W, H, cb)
            else:
                ok = sum(slot_free(e, W, H, cb)
                         for e in ("left", "right", "top", "bottom")) >= 2
            if ok:
                n += 1
                r25 = cap(x, y, 25.0, *P)
                if best is None or r25 > best["r25"]:
                    pc = rot(*PAD_CENTROID, -theta)
                    best = {"tab": [round(x, 3), round(y, 3)],
                            "r_reach": round(cap(x, y, REACH, *P), 2),
                            "r15": round(cap(x, y, 15.0, *P), 2),
                            "r20": round(cap(x, y, 20.0, *P), 2),
                            "r25": round(r25, 2),
                            "a_eff": round(min(A_SAT, cap(x + pc[0], y + pc[1],
                                                          REACH, *P)), 2)}
            y += step
        x += step
    if best is None:
        return None
    best.update(W=round(W, 3), H=round(H, 3), area=round(W * H, 1), theta=theta,
                aspect=round(max(W, H) / min(W, H), 3), mode=mode,
                pour_model=round((W - 1) * (H - 1), 2), legal_tab_sites=n)
    best["theta_ja"] = round(55 + 119 * math.exp(-best["a_eff"] / 350.0), 2)
    return best


def main():
    area = float(sys.argv[1]) if len(sys.argv) > 1 else 1321.0
    out = sys.argv[2] if len(sys.argv) > 2 else "sweep2.json"
    rows, bymode = [], {}
    for W in [28, 30, 32, 33, 34, 35, math.sqrt(area), 38, 40, 42, 44, 46, 48,
              50, 52, 55, 58, 62, 66, 70]:
        H = area / W
        for mode in ("pin", "free"):
            cands = [evaluate(W, H, th, mode) for th in CL]
            cands = [c for c in cands if c]
            if not cands:
                continue
            b = max(cands, key=lambda c: c["r25"])
            b["all_theta"] = {c["theta"]: c["r25"] for c in cands}
            rows.append(b)
    Path(out).write_text(json.dumps({"area_mm2": area, "reach_mm": round(REACH, 4),
                                     "rows": rows}, indent=1), encoding="utf-8")
    print(f"{'W':>7} {'H':>7} {'asp':>5} {'mode':>5} {'th':>4} {'a_eff':>7} "
          f"{'theta':>6} {'reach':>7} {'r15':>7} {'r20':>8} {'r25':>8} "
          f"{'pour':>8} {'tab':>16}")
    for r in sorted(rows, key=lambda r: (r["W"])):
        print(f"{r['W']:7.2f} {r['H']:7.2f} {r['aspect']:5.2f} {r['mode']:>5} "
              f"{int(r['theta']):4d} {r['a_eff']:7.1f} {r['theta_ja']:6.1f} "
              f"{r['r_reach']:7.1f} {r['r15']:7.1f} {r['r20']:8.1f} "
              f"{r['r25']:8.1f} {r['pour_model']:8.1f} {str(r['tab']):>16}")


if __name__ == "__main__":
    main()
