"""Read-only local copper dump around a point (all layers/nets).

Usage: <bundled py> dump_local.py <board> x y radius
"""
from __future__ import annotations

import math
import sys

import pcbnew


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
    path, sx, sy, sr = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    px, py, R = float(sx), float(sy), float(sr)
    board = pcbnew.LoadBoard(path)
    rows = []
    for t in board.Tracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            v = t.Cast()
            p = v.GetPosition()
            d = math.hypot(tomm(p.x) - px, tomm(p.y) - py)
            if d <= R:
                rows.append((d, f"VIA  net={v.GetNetname():18} at=({tomm(p.x):.4f},{tomm(p.y):.4f}) "
                                f"cu={tomm(v.GetWidth(v.TopLayer())):.3f} dr={tomm(v.GetDrillValue()):.3f} "
                                f"uuid={v.m_Uuid.AsString()}"))
            continue
        s = t.Cast()
        a, b = s.GetStart(), s.GetEnd()
        d = seg_pt_dist(tomm(a.x), tomm(a.y), tomm(b.x), tomm(b.y), px, py)
        if d <= R:
            kind = "ARC " if s.Type() == pcbnew.PCB_ARC_T else "TRK "
            rows.append((d, f"{kind} net={s.GetNetname():18} {board.GetLayerName(s.GetLayer()):6} "
                            f"({tomm(a.x):.4f},{tomm(a.y):.4f})->({tomm(b.x):.4f},{tomm(b.y):.4f}) "
                            f"w={tomm(s.GetWidth()):.3f} uuid={s.m_Uuid.AsString()}"))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            p = pad.GetPosition()
            d = math.hypot(tomm(p.x) - px, tomm(p.y) - py)
            if d <= R:
                dh = pad.GetDrillSize()
                rows.append((d, f"PAD  net={pad.GetNetname():18} {fp.GetReference()}.{pad.GetNumber():4} "
                                f"at=({tomm(p.x):.4f},{tomm(p.y):.4f}) size=({tomm(pad.GetSizeX()):.3f},"
                                f"{tomm(pad.GetSizeY()):.3f}) drill=({tomm(dh.x):.3f},{tomm(dh.y):.3f}) "
                                f"layers={','.join(board.GetLayerName(l) for l in pad.GetLayerSet().CuStack())[:40]}"))
    rows.sort()
    for d, line in rows:
        print(f"{d:7.4f}  {line}")


if __name__ == "__main__":
    main()
