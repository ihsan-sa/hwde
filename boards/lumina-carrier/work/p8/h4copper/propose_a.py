"""Cluster A: propose + numerically pre-verify a LED_Y_A reroute out of the
57 V tap pocket, then emit a route_edit ops file.

Nothing is written to the board here; --emit only writes the ops JSON.
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
from shapely.geometry import LineString, Point  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
OUT = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\h4copper")
NET = "/poe/LED_Y_A"
TAPS = {"/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"}
HV = {"+48V_SW", "V48_RAW", "V48_RTN"}
W = 0.2
VIA_D, VIA_DRILL = 0.6, 0.3
GEN_CLR = 0.2        # Default net class
EDGE_CLR = 0.5       # min_copper_edge_clearance
H2H = 0.25           # min_hole_to_hole
TAP_CLR = 0.635      # adopted board-wide HV figure

# --- proposed new geometry -------------------------------------------------
# F.Cu: leave J1-17 north-east, run east well north of J1's pin row (clear of
# the tap pocket entirely), drop south at x=51.8 east of every POE_TAP_A2
# escape, dive under /poe/LED_G_A's y=66.6 corridor on B.Cu, come back up and
# rejoin the untouched F.Cu run at (58.1, 75.6).
V1 = (51.8, 65.75)
V2 = (51.8, 69.0)
NEW_TRACKS = [
    ("F.Cu", (36.49, 64.123), (38.39, 62.223)),   # out of J1-17, 45 deg NE
    ("F.Cu", (38.39, 62.223), (51.8, 62.223)),    # north transit corridor
    ("F.Cu", (51.8, 62.223), V1),                 # south to the layer change
    ("B.Cu", V1, V2),                             # under LED_G_A's corridor
    ("F.Cu", V2, (58.1, 75.3)),                   # 45 deg SE
    ("F.Cu", (58.1, 75.3), (58.1, 75.6)),         # rejoin kept route
]
NEW_VIAS = [V1, V2]

# --- segments to delete (the whole J1-17 -> (58.1,75.6) leg) ---------------
DROP = [
    "ba6d885b-d57a-4144-bef2-4f326f2befb0", "d592b560-2b21-48b1-a8e1-ba597fc54b9b",
    "dc12fefd-881c-4d6e-9446-efd986b78042", "d1df5e29-510d-479b-9c95-5e552f6dcf0e",
    "95ebe612-9ce0-4da7-8623-47e38ecf4e71", "fd9e016c-73e6-4b34-9ae1-906ba524e2a6",
    "cdeea039-51e4-4959-9bad-d0518503c460", "f5794edf-e736-4c2d-aec5-beaf4f046e9c",
    "65a62697-a050-4f0b-bad1-0a01d2454d94", "000319c3-fd93-4311-969c-dfc25127b4ab",
    "86cef75a-cc18-46a9-899a-538118b5d0e3", "2c0ec17f-621e-4159-8060-c17b6f68fcc0",
    "5f87bbab-1acb-4e8f-9bc6-ecce1a99eda0", "246850fc-8646-4dc1-9827-757e84197ee1",
    "2a0b9d2e-69ca-4eed-8f5a-594bf944be7d", "77775b4e-7499-4130-a756-ea7473edcd32",
    "01739b6f-a840-4860-8898-843bc2fb7113", "5729eea5-41ee-430f-9805-ec603861cde9",
    "f03b4849-5cef-4b13-a7a7-8ab0ac4a8198",
]


def required(other_net: str) -> float:
    if other_net in TAPS or other_net in HV:
        return TAP_CLR
    return GEN_CLR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", default=None)
    args = ap.parse_args()

    bg = geom.load_board(PCB)
    dropped = set(DROP)

    # candidate copper, per layer
    cand = {L: [] for L in bg.copper_layers}
    for layer, a, b in NEW_TRACKS:
        cand[layer].append((f"trk {a}->{b}",
                            LineString([a, b]).buffer(W / 2, quad_segs=16)))
    for v in NEW_VIAS:
        for L in bg.copper_layers:
            cand[L].append((f"via {v}", Point(v).buffer(VIA_D / 2, quad_segs=16)))

    # surviving own-net copper (so we can also report self-consistency)
    print("=== pre-verify candidate LED_Y_A reroute ===")
    worst = []
    for layer in bg.copper_layers:
        if not cand[layer]:
            continue
        inner_plane = layer in ("In1.Cu", "In2.Cu")
        for other in bg.nets:
            if not other or other == NET:
                continue
            parts = []
            for t in bg.tracks_of(net=other, layer=layer):
                parts.append(t.poly)
            for v in bg.vias_of(net=other):
                if v.spans(layer):
                    parts.append(v.poly)
            for p in bg.pads_of(net=other):
                if p.on(layer):
                    parts.append(p.poly)
            if not inner_plane:
                for z in bg.zones_of(net=other):
                    f = z.fill_on(layer)
                    if not f.is_empty:
                        parts.append(f)
            if not parts:
                continue
            req = required(other)
            for name, poly in cand[layer]:
                d = min(poly.distance(q) for q in parts)
                if d < req:
                    worst.append((round(d, 4), req, layer, other, name))
    # unnetted pads (board locks, mount holes) are copper too
    for layer in bg.copper_layers:
        for p in bg.pads_of():
            if p.net or not p.on(layer):
                continue
            for name, poly in cand[layer]:
                d = poly.distance(p.poly)
                if d < GEN_CLR:
                    worst.append((round(d, 4), GEN_CLR, layer,
                                  f"<NC pad {p.ref}-{p.number}>", name))
    # board edge
    edge = bg.outline.exterior
    for layer in bg.copper_layers:
        for name, poly in cand[layer]:
            d = edge.distance(poly)
            if d < EDGE_CLR:
                worst.append((round(d, 4), EDGE_CLR, layer, "<board edge>", name))
    # hole to hole for the new vias
    holes = [(v.at, v.drill) for v in bg.vias_of()]
    for p in bg.pads_of():
        if len(p.layers) > 1:  # THT
            holes.append((p.center, min(p.size)))
    for v in NEW_VIAS:
        for c, d in holes:
            gap = Point(v).distance(Point(c)) - VIA_DRILL / 2 - d / 2
            if gap < H2H:
                worst.append((round(gap, 4), H2H, "drill",
                              f"<hole at {[round(x,3) for x in c]}>", f"via {v}"))

    if worst:
        print("CLEARANCE PROBLEMS:")
        for row in sorted(worst):
            print("  ", row)
    else:
        print("  clean: no candidate item violates its required clearance")

    # tightest few, informational
    print("\n=== tightest neighbours per candidate item (informational) ===")
    for layer in bg.copper_layers:
        if layer in ("In1.Cu", "In2.Cu"):
            continue
        for name, poly in cand[layer]:
            rows = []
            for other in bg.nets:
                if not other or other == NET:
                    continue
                parts = [t.poly for t in bg.tracks_of(net=other, layer=layer)]
                parts += [v.poly for v in bg.vias_of(net=other) if v.spans(layer)]
                parts += [p.poly for p in bg.pads_of(net=other) if p.on(layer)]
                for z in bg.zones_of(net=other):
                    f = z.fill_on(layer)
                    if not f.is_empty:
                        parts.append(f)
                if parts:
                    rows.append((round(min(poly.distance(q) for q in parts), 4), other))
            for p in bg.pads_of():
                if (not p.net) and p.on(layer):
                    rows.append((round(poly.distance(p.poly), 4),
                                 f"<NC {p.ref}-{p.number}>"))
            rows.sort()
            print(f"  {layer:6s} {name}: {rows[:4]}  edge={round(edge.distance(poly),3)}")

    if args.emit:
        ops = []
        for layer, a, b in NEW_TRACKS:
            ops.append({"op": "add_track", "start": list(a), "end": list(b),
                        "width": W, "layer": layer, "net": NET})
        for v in NEW_VIAS:
            ops.append({"op": "add_via", "at": list(v), "size": VIA_D,
                        "drill": VIA_DRILL, "net": NET})
        for u in DROP:
            ops.append({"op": "remove", "uuid": u})
        Path(args.emit).write_text(json.dumps({"version": 1, "ops": ops}, indent=1))
        print(f"\nwrote {len(ops)} ops -> {args.emit}"
              f" ({len(NEW_TRACKS)} adds, {len(NEW_VIAS)} vias,"
              f" {len(DROP)} removes)")
        assert len(dropped) == len(DROP), "duplicate uuid in DROP"


if __name__ == "__main__":
    main()
