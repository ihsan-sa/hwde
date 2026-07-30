"""Read-only context around specific vias: attached tracks, zones per layer,
nearby same-net vias/pads. Bundled python (pcbnew).

Usage: <py> inspect_ctx.py <board> "x,y" ["x,y" ...]
"""
from __future__ import annotations

import json
import math
import sys

import pcbnew

TOL = 0.002


def tomm(v):
    return pcbnew.ToMM(v)


def main():
    path = sys.argv[1]
    targets = []
    for a in sys.argv[2:]:
        x, y = a.split(",")
        targets.append((float(x), float(y)))

    board = pcbnew.LoadBoard(path)

    zones = []
    for z in board.Zones():
        lset = [board.GetLayerName(l) for l in z.GetLayerSet().CuStack()]
        zones.append(dict(net=z.GetNetname(), layers=lset,
                          prio=z.GetAssignedPriority(),
                          name=z.GetZoneName(),
                          area=round(tomm(tomm(z.GetFilledArea())), 2)))

    segs = []
    for t in board.Tracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        s = t.Cast()
        segs.append(s)

    out = []
    for (tx, ty) in targets:
        info = dict(target=[tx, ty], attached=[], near_copper=[], vias_nearby=[])
        for s in segs:
            a = s.GetStart()
            b = s.GetEnd()
            ax, ay = tomm(a.x), tomm(a.y)
            bx, by = tomm(b.x), tomm(b.y)
            da = math.hypot(ax - tx, ay - ty)
            db = math.hypot(bx - tx, by - ty)
            if min(da, db) < TOL:
                info["attached"].append(dict(
                    net=s.GetNetname(),
                    layer=board.GetLayerName(s.GetLayer()),
                    start=[round(ax, 4), round(ay, 4)],
                    end=[round(bx, 4), round(by, 4)],
                    width=round(tomm(s.GetWidth()), 4),
                    uuid=s.m_Uuid.AsString(),
                    end_at_target="start" if da < db else "end",
                    typ=("arc" if s.Type() == pcbnew.PCB_ARC_T else "seg"),
                ))
        for t in board.Tracks():
            if t.Type() != pcbnew.PCB_VIA_T:
                continue
            v = t.Cast()
            p = v.GetPosition()
            d = math.hypot(tomm(p.x) - tx, tomm(p.y) - ty)
            if d < 2.5:
                info["vias_nearby"].append(dict(
                    net=v.GetNetname(), dist=round(d, 4),
                    at=[round(tomm(p.x), 4), round(tomm(p.y), 4)],
                    uuid=v.m_Uuid.AsString()))
        info["vias_nearby"].sort(key=lambda d: d["dist"])
        # pads within 2.5mm
        pads = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                p = pad.GetPosition()
                d = math.hypot(tomm(p.x) - tx, tomm(p.y) - ty)
                if d < 2.5:
                    dh = pad.GetDrillSize()
                    pads.append(dict(ref=fp.GetReference(), pad=pad.GetNumber(),
                                     net=pad.GetNetname(), dist=round(d, 4),
                                     at=[round(tomm(p.x), 4), round(tomm(p.y), 4)],
                                     drill=[round(tomm(dh.x), 4), round(tomm(dh.y), 4)],
                                     size=[round(tomm(pad.GetSizeX()), 4),
                                           round(tomm(pad.GetSizeY()), 4)],
                                     layers=[board.GetLayerName(l) for l in
                                             pad.GetLayerSet().CuStack()]))
        pads.sort(key=lambda d: d["dist"])
        info["pads_nearby"] = pads
        out.append(info)

    print(json.dumps(dict(zones=zones, targets=out), indent=2))


if __name__ == "__main__":
    main()
