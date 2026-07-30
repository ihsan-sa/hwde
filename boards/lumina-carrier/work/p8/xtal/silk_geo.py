"""Extract each footprint's F.Silkscreen graphics (excluding the Reference and
Value fields) as a shapely geometry in the LOCAL frame, plus the inked box of
the Reference field. Reports extents for the island + neighbours."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import sexpdata  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
SILK = ("F.SilkS", "F.Silkscreen", "B.SilkS", "B.Silkscreen")


def tok(x):
    return x.value() if isinstance(x, sexpdata.Symbol) else x


def kid(n, name):
    for c in n[1:]:
        if isinstance(c, list) and c and tok(c[0]) == name:
            return c
    return None


def kids(n, name):
    return [c for c in n[1:] if isinstance(c, list) and c and tok(c[0]) == name]


def nums(n):
    return [float(x) for x in n[1:] if isinstance(x, (int, float))]


def strs(n):
    return [tok(x) for x in n[1:] if isinstance(tok(x), str)]


def layer_of(n):
    ln = kid(n, "layer")
    return strs(ln)[0] if ln is not None and strs(ln) else None


def width_of(n):
    st = kid(n, "stroke")
    if st is not None:
        w = kid(st, "width")
        if w is not None and nums(w):
            return nums(w)[0]
    w = kid(n, "width")
    return nums(w)[0] if w is not None and nums(w) else 0.12


def arc_pts(s, m, e, n=24):
    ax, ay = s
    bx, by = m
    cx, cy = e
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [s, e]
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay)
          + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx)
          + (cx**2 + cy**2) * (bx - ax)) / d
    r = math.dist((ux, uy), s)
    a0 = math.atan2(ay - uy, ax - ux)
    a1 = math.atan2(by - uy, bx - ux)
    a2 = math.atan2(cy - uy, cx - ux)

    def norm(a, ref):
        while a - ref > math.pi:
            a -= 2 * math.pi
        while a - ref < -math.pi:
            a += 2 * math.pi
        return a
    a1n, a2n = norm(a1, a0), norm(a2, norm(a1, a0))
    return [(ux + r * math.cos(a0 + (a2n - a0) * i / n),
             uy + r * math.sin(a0 + (a2n - a0) * i / n)) for i in range(n + 1)]


def footprint_silk(fp, side="front"):
    """(silk geometry, reference-field dict) in the LOCAL frame."""
    want = ("F.SilkS", "F.Silkscreen") if side == "front" else \
        ("B.SilkS", "B.Silkscreen")
    geos = []
    for head in ("fp_line", "fp_arc", "fp_circle", "fp_rect", "fp_poly"):
        for g in kids(fp, head):
            if layer_of(g) not in want:
                continue
            w = max(width_of(g), 0.01)
            if head == "fp_line":
                s, e = nums(kid(g, "start")), nums(kid(g, "end"))
                geos.append(LineString([tuple(s[:2]), tuple(e[:2])])
                            .buffer(w / 2, quad_segs=8))
            elif head == "fp_arc":
                s = nums(kid(g, "start"))[:2]
                m = nums(kid(g, "mid"))[:2]
                e = nums(kid(g, "end"))[:2]
                geos.append(LineString(arc_pts(tuple(s), tuple(m), tuple(e)))
                            .buffer(w / 2, quad_segs=8))
            elif head == "fp_circle":
                c = nums(kid(g, "center"))[:2]
                e = nums(kid(g, "end"))[:2]
                r = math.dist(c, e)
                geos.append(Point(c).buffer(r + w / 2, quad_segs=24)
                            .difference(Point(c).buffer(max(r - w / 2, 0),
                                                        quad_segs=24)))
            elif head == "fp_rect":
                s, e = nums(kid(g, "start"))[:2], nums(kid(g, "end"))[:2]
                ring = LineString([(s[0], s[1]), (e[0], s[1]), (e[0], e[1]),
                                   (s[0], e[1]), (s[0], s[1])])
                geos.append(ring.buffer(w / 2, quad_segs=8))
            elif head == "fp_poly":
                pts = kid(g, "pts")
                p = [tuple(nums(x)[:2]) for x in kids(pts, "xy")]
                if len(p) >= 2:
                    geos.append(LineString(p + [p[0]]).buffer(w / 2,
                                                              quad_segs=8))
    ref = None
    for prop in kids(fp, "property"):
        s = strs(prop)
        if len(s) >= 2 and s[0] == "Reference":
            at = nums(kid(prop, "at"))
            eff = kid(prop, "effects")
            font = kid(eff, "font") if eff is not None else None
            sz = nums(kid(font, "size")) if font is not None and \
                kid(font, "size") is not None else [1.0, 1.0]
            th = nums(kid(font, "thickness")) if font is not None and \
                kid(font, "thickness") is not None else [0.15]
            ref = {"text": s[1], "at_local": at[:2],
                   "deg_local": at[2] if len(at) > 2 else 0.0,
                   "size": sz, "thickness": th[0] if th else 0.15,
                   "layer": layer_of(prop),
                   "hide": kid(prop, "hide") is not None}
            break
    return (unary_union(geos) if geos else None), ref


if __name__ == "__main__":
    root = sexpdata.loads(PCB.read_text(encoding="utf-8"))
    want = sys.argv[1:] or ["Y10", "C30", "C31", "R35", "R36", "R34", "J2"]
    out = {}
    for fp in kids(root, "footprint"):
        ref = None
        for prop in kids(fp, "property"):
            s = strs(prop)
            if len(s) >= 2 and s[0] == "Reference":
                ref = s[1]
                break
        if ref not in want:
            continue
        side = "back" if (layer_of(fp) or "F.Cu").startswith("B.") else "front"
        g, r = footprint_silk(fp, side)
        out[ref] = {
            "silk_bounds_local": [round(v, 4) for v in g.bounds] if g else None,
            "silk_area": round(g.area, 4) if g else None,
            "ref_field": r,
            "at": [round(v, 4) for v in nums(kid(fp, "at"))],
        }
    print(json.dumps(out, indent=1))
