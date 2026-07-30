"""Read-only clearance probe for candidate via positions.

For each candidate, report every copper item (track/arc/pad/via) whose copper
comes within `margin` mm of a via pad of diameter `size` at that point, and
every drill whose hole-to-hole gap to a `drill` mm hole there is below 0.6 mm.

Usage: <bundled py> probe_pos.py <board> <size> <drill> "x,y[,net]" ...
"""
from __future__ import annotations

import json
import math
import sys

import pcbnew

MARGIN = 0.30   # report copper gaps below this
H2H_FLOOR = 0.60


def tomm(v):
    return pcbnew.ToMM(v)


def seg_pt_dist(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def main():
    path = sys.argv[1]
    size = float(sys.argv[2])
    drill = float(sys.argv[3])
    cands = []
    for a in sys.argv[4:]:
        parts = a.split(",")
        cands.append((float(parts[0]), float(parts[1]),
                      parts[2] if len(parts) > 2 else None))

    board = pcbnew.LoadBoard(path)
    r_cu = size / 2.0
    r_dr = drill / 2.0

    out = []
    for (px, py, net) in cands:
        rec = dict(at=[px, py], net=net, copper=[], drills=[])
        for t in board.Tracks():
            if t.Type() == pcbnew.PCB_VIA_T:
                v = t.Cast()
                p = v.GetPosition()
                cc = math.hypot(tomm(p.x) - px, tomm(p.y) - py)
                if cc < 1e-6:
                    continue
                w = tomm(v.GetWidth(v.TopLayer()))
                gap = cc - r_cu - w / 2.0
                if gap < MARGIN:
                    rec["copper"].append(dict(
                        kind="via", net=v.GetNetname(), gap=round(gap, 4),
                        at=[round(tomm(p.x), 4), round(tomm(p.y), 4)],
                        uuid=v.m_Uuid.AsString()))
                dg = cc - r_dr - tomm(v.GetDrillValue()) / 2.0
                if dg < H2H_FLOOR:
                    rec["drills"].append(dict(kind="via", gap=round(dg, 4),
                                              net=v.GetNetname(),
                                              at=[round(tomm(p.x), 4),
                                                  round(tomm(p.y), 4)]))
                continue
            s = t.Cast()
            a, b = s.GetStart(), s.GetEnd()
            d = seg_pt_dist(tomm(a.x), tomm(a.y), tomm(b.x), tomm(b.y), px, py)
            gap = d - r_cu - tomm(s.GetWidth()) / 2.0
            if gap < MARGIN:
                rec["copper"].append(dict(
                    kind="arc" if s.Type() == pcbnew.PCB_ARC_T else "track",
                    net=s.GetNetname(),
                    layer=board.GetLayerName(s.GetLayer()),
                    gap=round(gap, 4),
                    start=[round(tomm(a.x), 4), round(tomm(a.y), 4)],
                    end=[round(tomm(b.x), 4), round(tomm(b.y), 4)],
                    width=round(tomm(s.GetWidth()), 4),
                    uuid=s.m_Uuid.AsString()))
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                p = pad.GetPosition()
                cc = math.hypot(tomm(p.x) - px, tomm(p.y) - py)
                if cc > 3.0:
                    continue
                # bbox-based conservative gap
                bb = pad.GetBoundingBox()
                x1, y1 = tomm(bb.GetLeft()), tomm(bb.GetTop())
                x2, y2 = tomm(bb.GetRight()), tomm(bb.GetBottom())
                ddx = max(x1 - px, 0.0, px - x2)
                ddy = max(y1 - py, 0.0, py - y2)
                gap = math.hypot(ddx, ddy) - r_cu
                if gap < MARGIN:
                    rec["copper"].append(dict(
                        kind="pad", net=pad.GetNetname(),
                        ref=fp.GetReference(), pad=pad.GetNumber(),
                        gap_bbox=round(gap, 4),
                        at=[round(tomm(p.x), 4), round(tomm(p.y), 4)],
                        size=[round(tomm(pad.GetSizeX()), 4),
                              round(tomm(pad.GetSizeY()), 4)],
                        layers=[board.GetLayerName(l) for l in
                                pad.GetLayerSet().CuStack()]))
                dh = pad.GetDrillSize()
                if dh.x > 0 or dh.y > 0:
                    dg = cc - r_dr - max(tomm(dh.x), tomm(dh.y)) / 2.0
                    if dg < H2H_FLOOR:
                        rec["drills"].append(dict(
                            kind="pad", ref=fp.GetReference(),
                            pad=pad.GetNumber(), net=pad.GetNetname(),
                            gap=round(dg, 4),
                            at=[round(tomm(p.x), 4), round(tomm(p.y), 4)]))
        rec["copper"].sort(key=lambda d: d.get("gap", d.get("gap_bbox", 9)))
        rec["drills"].sort(key=lambda d: d["gap"])
        out.append(rec)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
