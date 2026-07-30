"""Cluster B: widen every track below JLC's 0.1016 mm minimum.

Measures the real widening room for each thin track (foreign copper on its own
layer, unnetted pads, board edge), picks 0.110 mm where it fits and 0.1016 mm
where it does not, and emits route_edit ops in ADD-then-REMOVE order as two
separate files per batch (the add file is applied first so the net is never
electrically broken between invocations; the dedup trap is avoided because the
removes live in a different invocation entirely).

Usage:
  widen_b.py --report r.json                     # measure only
  widen_b.py --batch N --size 40 --prefix p      # emit p_add.json / p_rm.json
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

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
FLOOR = 0.1016        # JLC minimum
GOAL = 0.110          # preferred, off the fab limit
GEN_CLR = 0.2         # Default net class clearance
EDGE_CLR = 0.5        # min_copper_edge_clearance
HV_CLR = 0.635        # adopted board-wide HV figure
HV_NETS = {"+48V_SW", "V48_RAW", "V48_RTN",
           "/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
           "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"}

SEG_RE = re.compile(
    r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
    r'\(width ([\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "([^"]*)"\)\s*'
    r'\(uuid "([^"]+)"\)', re.S)


def seg_uuids(pcb):
    txt = re.sub(r"[\t\n]+", " ", pcb.read_text(encoding="utf-8"))
    out = {}
    for m in SEG_RE.finditer(txt):
        x0, y0, x1, y1, w, layer, net, uid = m.groups()
        a = (round(float(x0), 4), round(float(y0), 4))
        b = (round(float(x1), 4), round(float(y1), 4))
        if b < a:
            a, b = b, a
        out.setdefault((a, b, round(float(w), 4), layer, net), []).append(uid)
    return out


def key_of(t):
    a = (round(t.shape.coords[0][0], 4), round(t.shape.coords[0][1], 4))
    b = (round(t.shape.coords[-1][0], 4), round(t.shape.coords[-1][1], 4))
    return (min(a, b), max(a, b), round(t.width, 4), t.layer, t.net)


def measure(bg):
    """Return a list of rows, one per thin track, with room + target."""
    edge = bg.outline.exterior
    uu = seg_uuids(PCB)
    thin = [t for t in bg.tracks_of() if t.width < FLOOR - 1e-9]
    # foreign copper cache per layer
    cache = {}

    def foreign(layer, net):
        ck = (layer, net)
        if ck in cache:
            return cache[ck]
        parts = []
        for other in bg.nets:
            if not other or other == net:
                continue
            req = HV_CLR if other in HV_NETS else GEN_CLR
            for t in bg.tracks_of(net=other, layer=layer):
                if t.width < FLOOR - 1e-9:
                    # this neighbour is itself going to be widened in this pass;
                    # measure against its FUTURE width so the result is
                    # independent of the order batches are applied in
                    parts.append((req, other,
                                  t.shape.buffer(GOAL / 2.0, quad_segs=16)))
                else:
                    parts.append((req, other, t.poly))
            for v in bg.vias_of(net=other):
                if v.spans(layer):
                    parts.append((req, other, v.poly))
            for p in bg.pads_of(net=other):
                if p.on(layer):
                    parts.append((req, other, p.poly))
            for z in bg.zones_of(net=other):
                f = z.fill_on(layer)
                if not f.is_empty:
                    parts.append((req, other, f))
        for p in bg.pads_of():
            if (not p.net) and p.on(layer):
                parts.append((GEN_CLR, f"<NC {p.ref}-{p.number}>", p.poly))
        cache[ck] = parts
        return parts

    rows = []
    seen = {}
    for t in thin:
        k = key_of(t)
        uids = uu.get(k, [])
        idx = seen.get(k, 0)
        seen[k] = idx + 1
        uid = uids[idx] if idx < len(uids) else None
        # slack = how far each side may grow
        slack, who = 9e9, None
        for req, other, poly in foreign(t.layer, t.net):
            s = poly.distance(t.shape) - t.width / 2.0 - req
            if s < slack:
                slack, who = s, other
        se = edge.distance(t.shape) - t.width / 2.0 - EDGE_CLR
        if se < slack:
            slack, who = se, "<board edge>"
        room = 2.0 * slack                      # total width headroom
        wmax = t.width + room
        if wmax + 1e-9 >= GOAL:
            target, note = GOAL, None
        elif wmax + 1e-9 >= FLOOR:
            target = math.floor(wmax * 10000) / 10000.0
            target = max(target, FLOOR)
            note = "capped below 0.110 by room"
        else:
            target, note = None, "CANNOT REACH 0.1016"
        rows.append(dict(net=t.net, layer=t.layer, w=round(t.width, 4),
                         start=list(k[0]), end=list(k[1]),
                         room=round(room, 4), blocker=who,
                         target=target, note=note, uuid=uid,
                         dup_index=idx, n_uuids=len(uids)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=None)
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--size", type=int, default=40)
    ap.add_argument("--prefix", default=None)
    ap.add_argument("--exclude-nets", default="")
    args = ap.parse_args()

    bg = geom.load_board(PCB)
    rows = measure(bg)
    excl = {n for n in args.exclude_nets.split(",") if n}
    print(f"thin tracks: {len(rows)}")
    bad = [r for r in rows if r["uuid"] is None]
    if bad:
        print(f"  !! {len(bad)} rows with no uuid match")
        for r in bad[:5]:
            print("   ", r)
    ncan = [r for r in rows if r["target"] is None]
    print(f"  cannot reach {FLOOR}: {len(ncan)}")
    for r in ncan:
        print("   ", r["net"], r["layer"], r["start"], r["end"],
              "room", r["room"], "blocker", r["blocker"])
    capped = [r for r in rows if r["note"] == "capped below 0.110 by room"]
    print(f"  capped below {GOAL}: {len(capped)}")
    for r in capped:
        print("   ", r["net"], r["layer"], r["start"], r["end"],
              "room", r["room"], "-> ", r["target"], "blocker", r["blocker"])
    if excl:
        print(f"  excluded nets {sorted(excl)}: "
              f"{len([r for r in rows if r['net'] in excl])} rows")
    mn = min((r["room"] for r in rows), default=None)
    print(f"  room: min={mn} max={round(max(r['room'] for r in rows),4)}")

    if args.report:
        Path(args.report).write_text(json.dumps(rows, indent=1))

    work = [r for r in rows
            if r["uuid"] and r["target"] and r["net"] not in excl]
    if args.batch is not None and args.prefix:
        lo = args.batch * args.size
        chunk = work[lo:lo + args.size]
        add = [{"op": "add_track", "start": r["start"], "end": r["end"],
                "width": r["target"], "layer": r["layer"], "net": r["net"]}
               for r in chunk]
        rm = [{"op": "remove", "uuid": r["uuid"]} for r in chunk]
        Path(args.prefix + "_add.json").write_text(
            json.dumps({"version": 1, "ops": add}, indent=1))
        Path(args.prefix + "_rm.json").write_text(
            json.dumps({"version": 1, "ops": rm}, indent=1))
        print(f"batch {args.batch}: rows {lo}..{lo+len(chunk)-1} of {len(work)}"
              f" -> {len(add)} adds / {len(rm)} removes")
    else:
        print(f"actionable rows: {len(work)}")


if __name__ == "__main__":
    main()
