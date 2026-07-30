"""Read-only: enumerate every drill (via + THT pad) and report near pairs.

Runs under KiCad bundled python (pcbnew). Usage:
  <bundled-python> inspect_holes.py <board.kicad_pcb> [floor_mm]
Prints JSON to stdout.
"""
from __future__ import annotations

import json
import math
import sys

import pcbnew

TOM = 1e-6  # nm -> mm helper via pcbnew.ToMM instead


def tomm(v):
    return pcbnew.ToMM(v)


def main():
    path = sys.argv[1]
    floor = float(sys.argv[2]) if len(sys.argv) > 2 else 0.60
    board = pcbnew.LoadBoard(path)

    holes = []
    for t in board.Tracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        v = t.Cast()
        p = v.GetPosition()
        holes.append(dict(
            kind="via", ref=None, pad=None,
            net=v.GetNetname(),
            x=round(tomm(p.x), 4), y=round(tomm(p.y), 4),
            drill=round(tomm(v.GetDrillValue()), 4),
            dx=round(tomm(v.GetDrillValue()), 4),
            dy=round(tomm(v.GetDrillValue()), 4),
            width=round(tomm(v.GetWidth(v.TopLayer())), 4),
            uuid=v.m_Uuid.AsString(),
            via_type=str(v.GetViaType()),
            layers=[board.GetLayerName(v.TopLayer()),
                    board.GetLayerName(v.BottomLayer())],
        ))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            dh = pad.GetDrillSize()
            if dh.x <= 0 and dh.y <= 0:
                continue
            p = pad.GetPosition()
            holes.append(dict(
                kind="pad", ref=fp.GetReference(), pad=pad.GetNumber(),
                net=pad.GetNetname(),
                x=round(tomm(p.x), 4), y=round(tomm(p.y), 4),
                drill=round(max(tomm(dh.x), tomm(dh.y)), 4),
                dx=round(tomm(dh.x), 4), dy=round(tomm(dh.y), 4),
                width=round(tomm(pad.GetSizeX()), 4),
                uuid=pad.m_Uuid.AsString(),
                via_type=None,
                layers=[str(pad.GetAttribute())],
            ))

    # circular approximation for pair scan (oval handled via max dim, then
    # exact-ish via per-axis rect approx reported separately)
    pairs = []
    n = len(holes)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = holes[i], holes[j]
            cc = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
            gap = cc - (a["drill"] + b["drill"]) / 2.0
            if gap < floor:
                pairs.append(dict(gap=round(gap, 4), cc=round(cc, 4),
                                  a=a, b=b))
    pairs.sort(key=lambda d: d["gap"])
    print(json.dumps(dict(total_holes=n, floor=floor, near_pairs=pairs),
                     indent=2))


if __name__ == "__main__":
    main()
