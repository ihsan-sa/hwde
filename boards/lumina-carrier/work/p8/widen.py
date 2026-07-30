"""Emit a route_edit ops file that widens every undersized power segment whose
clearance envelope allows the IPC-2152 width.

Usage: widen.py <ops.json> [--nets a,b] [--max-per-net N]
Also honours a board-edge clearance and a per-net HV clearance.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
import check_current  # noqa

BOARD = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad")
PCB = BOARD / "lumina-carrier.kicad_pcb"
CONS = json.loads((BOARD / "constraints.json").read_text())

HV = {"V48_RAW", "V48_RTN", "+48V_SW"}
EDGE_CLR = 0.3          # copper-to-edge; DRC uses 0.2, keep margin
SEG_RE = re.compile(
    r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
    r'\(width ([\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "([^"]*)"\)\s*'
    r'\(uuid "([^"]+)"\)', re.S)


def seg_uuids(pcb: Path):
    txt = re.sub(r"[\t\n]+", " ", pcb.read_text(encoding="utf-8"))
    out = {}
    for m in SEG_RE.finditer(txt):
        x0, y0, x1, y1, w, layer, net, uid = m.groups()
        a, b = (round(float(x0), 4), round(float(y0), 4)), (round(float(x1), 4), round(float(y1), 4))
        if b < a:
            a, b = b, a
        out.setdefault((a, b, round(float(w), 4), layer, net), []).append(uid)
    return out


def clr_for(a, b):
    return 0.635 if (a in HV or b in HV) else 0.2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--nets", default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--to-max", action="store_true",
                    help="widen BLOCKED segments to the largest width the "
                         "clearance envelope allows (partial; gate still fails)")
    ap.add_argument("--min-gain", type=float, default=0.05)
    args = ap.parse_args()

    bg = geom.load_board(PCB)
    uu = seg_uuids(PCB)
    cu = bg.stackup.copper_thickness
    edge = bg.outline.exterior
    ops, rep = [], []
    want = set(args.nets.split(",")) if args.nets else None

    for entry in CONS["power"]:
        net = entry["net"]
        if want and net not in want:
            continue
        budget, dt = float(entry["current_a"]), float(entry.get("dt_c", 10))
        tracks = bg.tracks_of(net)
        for layer in sorted({t.layer for t in tracks}):
            req = check_current.required_width_mm(budget, dt, cu[layer])
            target = math.ceil(req * 1000) / 1000.0
            others = []
            for onet in bg.nets:
                if onet and onet != net:
                    c = bg.net_copper(onet, layer)
                    if not c.is_empty:
                        others.append((onet, c))
            # UNNETTED pads (37 on this board: U10 x16, J1 x6, U30/U22 x4 ...)
            # are copper too and are NOT in bg.nets - they bit the first pass
            # with 4 clearance errors against U10-18.
            for p in bg.pads_of():
                if (not p.net) and layer in p.layers:
                    others.append((f"<NC pad {p.ref}-{p.number}>", p.poly))
            for t in [x for x in tracks if x.layer == layer]:
                if t.width + 1e-3 >= req:
                    continue
                lim, who = 9e9, None
                for onet, c in others:
                    d = c.distance(t.shape)
                    room = 2.0 * (d - clr_for(net, onet))
                    if room < lim:
                        lim, who = room, onet
                de = edge.distance(t.shape)
                room_e = 2.0 * (de - EDGE_CLR)
                if room_e < lim:
                    lim, who = room_e, "<board edge>"
                a = (round(t.shape.coords[0][0], 4), round(t.shape.coords[0][1], 4))
                b = (round(t.shape.coords[-1][0], 4), round(t.shape.coords[-1][1], 4))
                k = (min(a, b), max(a, b), round(t.width, 4), layer, net)
                uids = uu.get(k)
                row = dict(net=net, layer=layer, w=round(t.width, 3),
                           req=round(req, 3), target=target, room=round(lim, 3),
                           blocker=who, start=list(a), end=list(b),
                           uuid=(uids[0] if uids else None))
                if not uids:
                    row["skip"] = "uuid not found"
                elif lim + 1e-3 < target:
                    if args.to_max and lim >= t.width + args.min_gain:
                        w2 = math.floor(min(lim, target) * 100) / 100.0
                        ops.append({"op": "remove", "uuid": uids[0]})
                        ops.append({"op": "add_track", "start": list(a),
                                    "end": list(b), "width": w2,
                                    "layer": layer, "net": net})
                        row["skip"] = None
                        row["target"] = w2
                        row["partial"] = True
                        uu[k] = uids[1:]
                    else:
                        row["skip"] = "blocked"
                else:
                    ops.append({"op": "remove", "uuid": uids[0]})
                    ops.append({"op": "add_track", "start": list(a), "end": list(b),
                                "width": target, "layer": layer, "net": net})
                    row["skip"] = None
                    if uids:
                        uu[k] = uids[1:]
                rep.append(row)

    Path(args.out).write_text(json.dumps({"version": 1, "ops": ops}, indent=1))
    if args.report:
        Path(args.report).write_text(json.dumps(rep, indent=1))
    from collections import Counter
    c = Counter((r["net"], r["skip"] or "WIDEN") for r in rep)
    for k, v in sorted(c.items()):
        print(v, k)
    print(f"{len(ops)} ops -> {args.out}")


if __name__ == "__main__":
    main()
