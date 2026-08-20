"""pareto.py - analytic (a_eff, r25) Pareto front for one W x H, pin vs free.

Answers the one question the built candidates cannot: at the delivered 1.89
aspect, can ANY pinned placement reach the free optimum on both measures at
once, or does placement.edges force a choice between them?  Same rectangle-
inset pour model as build_case.py (pads/track excluded), so read the DIFFERENCE
between the two fronts, not their absolute level.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_case as bc  # noqa: E402


def front(W, H, mode, step=0.125):
    pts = []
    for th in bc.CL:
        cx0, cy0, cx1, cy1 = bc.CL[th]
        x = bc.KEEP - cx0
        while x <= W - bc.KEEP - cx1 + 1e-9:
            y = bc.KEEP - cy0
            while y <= H - bc.KEEP - cy1 + 1e-9:
                cb = (x + cx0, y + cy0, x + cx1, y + cy1)
                if bc.seats(mode, W, H, cb):
                    pc = bc.rot(bc.PAD_CENTROID[0], bc.PAD_CENTROID[1], -th)
                    ae = min(bc.A_SAT, bc.cap(x + pc[0], y + pc[1], bc.REACH,
                                              W, H))
                    pts.append((round(ae, 3), round(bc.cap(x, y, 25.0, W, H), 3),
                                th, round(x, 3), round(y, 3)))
                y += step
            x += step
    pts.sort(key=lambda p: (-p[0], -p[1]))
    out, best_r = [], -1e9
    for p in pts:
        if p[1] > best_r + 1e-6:
            out.append(p)
            best_r = p[1]
    return out


def main():
    W, H = float(sys.argv[1]), float(sys.argv[2])
    res = {}
    for mode in ("pin", "free"):
        f = front(W, H, mode)
        res[mode] = [{"a_eff": p[0], "r25": p[1], "theta": p[2],
                      "tab": [p[3], p[4]]} for p in f]
        print(f"--- {mode}  ({len(f)} Pareto points)")
        for p in f:
            print(f"    a_eff {p[0]:8.2f}  r25 {p[1]:8.2f}  theta {int(p[2]):3d} "
                  f"tab {p[3]:7.3f},{p[4]:7.3f}")
    Path(sys.argv[3]).write_text(json.dumps({"W": W, "H": H, **res}, indent=1),
                                 encoding="utf-8")


if __name__ == "__main__":
    main()
