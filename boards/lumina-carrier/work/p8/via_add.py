"""Find companion vias for power-net via clusters short of ceil(I/via_amps).

A companion via only carries current in parallel if it joins the SAME layers,
so a candidate must sit on the net's copper on every layer the existing via
bridges.  It must hold the net's copper clearance to every foreign item on
every layer (unnetted pads included), 0.5 mm hole-EDGE to every other drill
(KiCad does not test via-drill vs same-net THT pad drill - LEARNINGS
2026-07-28), stay out of the antenna keepout and off the board edge.

Candidates are sampled ALONG the net's own track centrelines (not a grid), and
the foreign geometry is clipped to a local window, so this runs in seconds.
"""
import argparse
import json
import math
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
import check_current  # noqa
from shapely.geometry import Point, box  # noqa
from shapely.ops import unary_union  # noqa
from shapely.prepared import prep  # noqa

BOARD = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad")
PCB = BOARD / "lumina-carrier.kicad_pcb"
CONS = json.loads((BOARD / "constraints.json").read_text())

VIA_D, VIA_DRILL = 0.6, 0.3
HV = {"V48_RAW", "V48_RTN", "+48V_SW"}
HOLE_GAP = 0.5
CLUSTER = 1.9              # stay inside check_current's 2.0 mm cluster radius
STEP = 0.05
KEEPOUT = (109.58, 86.132, 119.58, 108.132)
WIN = 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--report")
    args = ap.parse_args()
    bg = geom.load_board(PCB)

    drills = [(v.at, v.drill) for v in bg.vias_of()]
    for p in bg.pads_of():
        if "F.Cu" in p.layers and "B.Cu" in p.layers and len(p.layers) > 2:
            drills.append((p.center, min(p.size)))

    fore = {}          # layer -> unioned foreign-capable copper WITH net tags
    for layer in bg.copper_layers:
        parts = []
        inner = layer not in ("F.Cu", "B.Cu")
        for onet in bg.nets:
            if not onet:
                continue
            gs = [t.poly for t in bg.tracks_of(onet, layer)]
            gs += [pp.poly for pp in bg.pads_of(onet) if layer in pp.layers]
            gs += [v.poly for v in bg.vias_of(onet) if v.spans(layer)]
            if not inner:            # an inner plane fill re-carves its own
                for z in bg.zones_of(onet, layer):   # antipad on refill, so it
                    f = z.fill_on(layer)             # is not a blocker there
                    if not f.is_empty:
                        gs.append(f)
            gs = [g for g in gs if not g.is_empty]
            if gs:
                parts.append((onet, unary_union(gs)))
        for p in bg.pads_of():
            if (not p.net) and layer in p.layers:
                parts.append((f"<NC {p.ref}-{p.number}>", p.poly))
        fore[layer] = parts

    selfc = {}

    def netcopper(net, layer):
        """Net copper on `layer` EXCLUDING vias: a through via's own barrel
        makes net_copper() report copper on every layer it spans, which would
        make 'which layers does this via bridge' answer 'all of them'."""
        k = (net, layer)
        if k not in selfc:
            gs = [t.poly for t in bg.tracks_of(net, layer)]
            gs += [p.poly for p in bg.pads_of(net) if layer in p.layers]
            for z in bg.zones_of(net, layer):
                f = z.fill_on(layer)
                if not f.is_empty:
                    gs.append(f)
            selfc[k] = unary_union(gs) if gs else Point(0, 0).buffer(0)
        return selfc[k]

    ops, rep = [], []
    for entry in CONS["power"]:
        net = entry["net"]
        budget = float(entry["current_a"])
        va = float(entry.get("via_amps", 0.5))
        need = max(1, math.ceil(budget / va))
        clr = 0.635 if net in HV else 0.2
        clusters = check_current.cluster_vias(bg.vias_of(net))
        for cl in clusters:
            if len(cl) >= need:
                continue
            cx = sum(v.at[0] for v in cl) / len(cl)
            cy = sum(v.at[1] for v in cl) / len(cl)
            v0 = cl[0]
            bridged = [l for l in bg.copper_layers
                       if netcopper(net, l).intersects(v0.poly.buffer(1e-3))]
            win = box(cx - WIN, cy - WIN, cx + WIN, cy + WIN)
            # local foreign geometry per layer, clipped + prepared
            loc = {}
            for layer in bg.copper_layers:
                gs = [c.intersection(win) for onet, c in fore[layer]
                      if onet != net and c.intersects(win)]
                gs = [g for g in gs if not g.is_empty]
                loc[layer] = unary_union(gs) if gs else None
            # candidates: along the net's tracks on the FIRST bridged layer
            cands = []
            for t in bg.tracks_of(net, bridged[0] if bridged else "F.Cu"):
                L = t.shape.length
                n = max(1, int(L / STEP))
                for i in range(n + 1):
                    p = t.shape.interpolate(min(i * STEP, L))
                    d = math.hypot(p.x - cx, p.y - cy)
                    if 0.8 <= d <= CLUSTER:
                        cands.append((p.x, p.y, d))
            cands.sort(key=lambda c: c[2])
            placed, why = [], None
            want = need - len(cl)
            for (px, py, _) in cands:
                if len(placed) >= want:
                    break
                pad = Point(px, py).buffer(VIA_D / 2.0, quad_segs=16)
                if any(not netcopper(net, l).buffer(1e-3).contains(Point(px, py))
                       for l in bridged if l in ("F.Cu", "B.Cu")):
                    why = why or "not on both layers"
                    continue
                bad = False
                for layer in bg.copper_layers:
                    f = loc[layer]
                    if f is not None and f.distance(pad) < clr - 1e-6:
                        bad = True
                        why = f"clearance {layer}"
                        break
                if bad:
                    continue
                if any(math.hypot(dp[0] - px, dp[1] - py)
                       - (dd / 2.0 + VIA_DRILL / 2.0) < HOLE_GAP
                       for dp, dd in drills + [(p, VIA_DRILL) for p in placed]):
                    why = "hole_to_hole"
                    continue
                if (KEEPOUT[0] - 0.5 <= px <= KEEPOUT[2] + 0.5
                        and KEEPOUT[1] - 0.5 <= py <= KEEPOUT[3] + 0.5):
                    why = "antenna keepout"
                    continue
                if bg.outline.exterior.distance(pad) < 0.3:
                    why = "board edge"
                    continue
                placed.append((round(px, 3), round(py, 3)))
            for p in placed:
                ops.append({"op": "add_via", "at": list(p), "size": VIA_D,
                            "drill": VIA_DRILL, "net": net})
            rep.append(dict(net=net, at=[round(cx, 3), round(cy, 3)],
                            have=len(cl), need=need, bridged=bridged,
                            cands=len(cands), placed=placed,
                            still_short=want - len(placed),
                            blocked_by=(None if len(placed) >= want else why)))
            print(f"{net:8s} ({cx:8.3f},{cy:8.3f}) have {len(cl)} need {need} "
                  f"cands {len(cands):4d} placed {len(placed)}/{want} "
                  f"{placed} {'' if len(placed) >= want else '<- ' + str(why)}")
    Path(args.out).write_text(json.dumps({"version": 1, "ops": ops}, indent=1))
    if args.report:
        Path(args.report).write_text(json.dumps(rep, indent=1))
    print(f"\n{len(ops)} vias -> {args.out}")
    print(f"clusters resolved: {sum(1 for r in rep if r['still_short'] == 0)}/{len(rep)}; "
          f"vias still missing: {sum(r['still_short'] for r in rep)}")


if __name__ == "__main__":
    main()
