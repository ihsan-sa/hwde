"""Generate + pre-flight-validate the three ops files for the eth_xtal collapse.

  rip.json    route_edit removes (all replaced copper on the 3 osc nets)
  place.json  place_edit moves for the 5 island parts
  add.json    route_edit adds (new island F.Cu, new /eth/XI B.Cu leg,
              2 transition vias, GND stub+via per island GND pad)

Pre-flight: every NEW pad / track / via is checked against ALL copper that
survives the rip, on every layer, at the netclass clearance; plus board-edge
clearance and hole-to-hole.  Nothing is written unless the check passes.

usage: build_ops.py PLACEMENT.json [--emit]
"""
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
WORK = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "xtal"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))
sys.path.insert(0, str(WORK))

import geom  # noqa: E402
import placelib  # noqa: E402
import route_cleanup as rc  # noqa: E402
import truegeo  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402
PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
NETS = ["/eth/XI", "/eth/XO", "/eth/XO_XTAL"]
ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
CLR = 0.2            # Default netclass clearance
W = 0.2              # Default netclass track width
W_GND = 0.3          # matches the existing GND stubs on this board
VIA_D, VIA_DR = 0.6, 0.3
EDGE_CU = 0.5        # min_copper_edge_clearance
H2H = 0.25           # min_hole_to_hole

bg = geom.load_board(PCB)
model = placelib.PlaceModel(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
RING = bg.outline.exterior


def ab(x, y):
    return (x + OX, y + OY)


def rl(x, y):
    return (round(x - OX, 4), round(y - OY, 4))


# ---------------------------------------------------------------- kept copper
# board-relative (layer, start, end) of every segment that SURVIVES the rip
KEEP = {
    "/eth/XI": [
        ("F.Cu", (77.095, 17.293), (77.045, 17.243)),
        ("F.Cu", (77.045, 17.243), (77.045, 16.493)),
        ("F.Cu", (77.045, 16.493), (76.52, 15.968)),
        ("F.Cu", (76.52, 15.968), (76.52, 15.943)),
        ("F.Cu", (76.52, 15.943), (76.295, 15.718)),
        ("F.Cu", (76.295, 15.718), (76.295, 15.693)),
        ("F.Cu", (76.295, 15.693), (76.145, 15.543)),
        ("B.Cu", (76.145, 15.393), (75.22, 14.468)),
        ("B.Cu", (75.22, 14.468), (75.22, 14.443)),
        ("B.Cu", (75.22, 14.443), (73.495, 12.718)),
    ],
    "/eth/XO": [
        ("F.Cu", (76.595, 17.293), (76.595, 18.343)),
        ("B.Cu", (76.595, 18.343), (76.595, 15.843)),
        ("B.Cu", (76.595, 15.843), (76.795, 15.643)),
        ("B.Cu", (76.795, 15.643), (76.795, 13.243)),
        ("B.Cu", (76.795, 13.243), (75.345, 11.793)),
        ("B.Cu", (75.345, 11.793), (75.345, 8.868)),
    ],
    "/eth/XO_XTAL": [],
}
KEEP_VIAS = {"/eth/XI": [(76.145, 15.393)],
             "/eth/XO": [(76.595, 18.343), (75.345, 8.868)],
             "/eth/XO_XTAL": []}
XO_VIA = (75.345, 8.868)      # /eth/XO F.Cu landing (unchanged)

# GND copper that exists ONLY to connect the four island GND pads to the In1
# plane at their OLD positions. Verified (work/p8/xtal): nothing else touches
# these four vias. Left behind they become track_dangling / via_dangling
# warnings, and the drc_routed gate counts warnings.
EXTRA_SEGS = [("GND", "F.Cu", (62.82, 16.015), (63.47, 16.015)),
              ("GND", "F.Cu", (63.47, 16.015), (63.22, 16.015)),
              ("GND", "F.Cu", (53.034, 16.015), (53.684, 16.015)),
              ("GND", "F.Cu", (53.684, 16.015), (53.434, 16.015))]
EXTRA_VIAS = [("GND", (63.47, 16.015)), ("GND", (53.684, 16.015)),
              ("GND", (59.612, 17.39)), ("GND", (56.428, 14.64))]


def near(a, b, tol=0.002):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def build_rip():
    segs, vias = rc.parse_items(PCB, bg.copper_layers)
    removes, kept_s, kept_v = [], [], []
    extra = []
    for s in segs:
        if s.net not in NETS:
            a, b = rl(*s.a), rl(*s.b)
            for e in EXTRA_SEGS:
                if e[0] == s.net and e[1] == s.layer and (
                        (near(a, e[2]) and near(b, e[3]))
                        or (near(a, e[3]) and near(b, e[2]))):
                    removes.append({"op": "remove", "uuid": s.uuid})
                    extra.append(e)
            continue
        a, b = rl(*s.a), rl(*s.b)
        hit = None
        for k in KEEP[s.net]:
            if k[0] == s.layer and ((near(a, k[1]) and near(b, k[2]))
                                    or (near(a, k[2]) and near(b, k[1]))):
                hit = k
                break
        if hit:
            kept_s.append((s.net, hit))
        else:
            removes.append({"op": "remove", "uuid": s.uuid})
    for v in vias:
        if v.net not in NETS:
            p = rl(*v.at)
            for e in EXTRA_VIAS:
                if e[0] == v.net and near(p, e[1]):
                    removes.append({"op": "remove", "uuid": v.uuid})
                    extra.append(e)
            continue
        p = rl(*v.at)
        if any(near(p, q) for q in KEEP_VIAS[v.net]):
            kept_v.append((v.net, p))
        else:
            removes.append({"op": "remove", "uuid": v.uuid})
    exp = sum(len(v) for v in KEEP.values())
    expv = sum(len(v) for v in KEEP_VIAS.values())
    if len(kept_s) != exp or len(kept_v) != expv:
        raise SystemExit("KEEP mismatch: matched %d/%d segs, %d/%d vias\n%s"
                         % (len(kept_s), exp, len(kept_v), expv,
                            json.dumps(sorted(str(k) for k in kept_s),
                                       indent=1)))
    if len(extra) != len(EXTRA_SEGS) + len(EXTRA_VIAS):
        raise SystemExit("EXTRA mismatch: matched %d/%d"
                         % (len(extra), len(EXTRA_SEGS) + len(EXTRA_VIAS)))
    return removes, kept_s, kept_v


# ------------------------------------------------------------- new placement
TG = truegeo.TrueGeo(WORK / "probe_pre.json")
PADNET = {(p.ref, p.number): p.net for p in bg.pads_of()}


def part_geo(ref, deg, xr, yr):
    """EXACT pads / silk from KiCad's own geometry, re-posed rigidly."""
    x, y = ab(xr, yr)
    pads = [{"ref": ref, "n": n, "net": PADNET.get((ref, n)), "poly": p,
             "c": (p.centroid.x, p.centroid.y)}
            for n, p in TG.pads_at(ref, (x, y), deg)]
    f = model.footprints[ref]
    ext = affinity.translate(
        affinity.rotate(f.extents_local(), -deg, origin=(0, 0)), x, y)
    return pads, ext, TG.silk_at(ref, (x, y), deg)


def mst_edges(pts):
    inside, rest, out = [0], list(range(1, len(pts))), []
    while rest:
        bd, bi, bj = 1e9, None, None
        for i in inside:
            for j in rest:
                d = math.dist(pts[i], pts[j])
                if d < bd:
                    bd, bi, bj = d, i, j
        out.append((bi, bj, bd))
        inside.append(bj)
        rest.remove(bj)
    return out


def main():
    place = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    pl = {r: (place["placement"][r]["x_rel"], place["placement"][r]["y_rel"],
              place["placement"][r]["deg"]) for r in ISLAND}
    xi_entry = tuple(place["detail"]["xi_entry"])

    removes, kept_s, kept_v = build_rip()

    geos = {r: part_geo(r, pl[r][2], pl[r][0], pl[r][1]) for r in ISLAND}
    allpads = [pd for r in ISLAND for pd in geos[r][0]]

    # ---- surviving copper index, per layer -------------------------------
    keep_rel = {(k[0], k[1], k[2]) for lst in KEEP.values() for k in lst}
    keep_via_rel = {q for lst in KEEP_VIAS.values() for q in lst}

    def survives_track(t):
        if t.net not in NETS:
            return True
        a, b = rl(*list(t.shape.coords)[0]), rl(*list(t.shape.coords)[-1])
        for lay, s, e in keep_rel:
            if lay == t.layer and ((near(a, s) and near(b, e))
                                   or (near(a, e) and near(b, s))):
                return True
        return False

    def survives_via(v):
        if v.net not in NETS:
            return True
        return any(near(rl(*v.at), q) for q in keep_via_rel)

    surv = {}
    for lay in bg.copper_layers:
        polys, tags = [], []
        for t in bg.tracks_of(layer=lay):
            if survives_track(t):
                polys.append(t.poly)
                tags.append((t.net, "trk"))
        for v in bg.vias_of():
            if v.spans(lay) and survives_via(v):
                polys.append(v.poly)
                tags.append((v.net, "via"))
        for p in bg.pads_of(layer=lay):
            if p.ref in ISLAND:      # island pads move: handled separately
                continue
            polys.append(p.poly)
            tags.append((p.net, "pad:%s.%s" % (p.ref, p.number)))
        surv[lay] = (polys, tags, STRtree(polys))

    holes = [(v.at, v.drill) for v in bg.vias_of() if survives_via(v)]

    # ---- new copper ------------------------------------------------------
    adds, newgeo = [], []      # newgeo: (label, layer(s), shapely poly)

    def add_track(net, layer, a, b, w=W, label=""):
        if math.dist(a, b) < 1e-6:
            return
        A, B = ab(*a), ab(*b)
        adds.append({"op": "add_track", "start": [round(A[0], 4),
                                                  round(A[1], 4)],
                     "end": [round(B[0], 4), round(B[1], 4)],
                     "width": w, "layer": layer, "net": net})
        newgeo.append((label or "%s trk" % net, [layer], net,
                       LineString([A, B]).buffer(w / 2, quad_segs=32,
                                                 cap_style="round")))

    def add_via(net, at, label=""):
        A = ab(*at)
        adds.append({"op": "add_via", "at": [round(A[0], 4), round(A[1], 4)],
                     "size": VIA_D, "drill": VIA_DR, "net": net})
        newgeo.append((label or "%s via" % net, list(bg.copper_layers), net,
                       Point(A).buffer(VIA_D / 2, quad_segs=32)))
        holes.append((A, VIA_DR))

    # /eth/XI: new B.Cu leg + transition via
    dx = 75.22 - xi_entry[0]
    bend = (xi_entry[0], 12.718 - (73.495 - xi_entry[0]))
    add_track("/eth/XI", "B.Cu", (73.495, 12.718), bend, label="XI B.Cu 45")
    add_track("/eth/XI", "B.Cu", bend, xi_entry, label="XI B.Cu run")
    add_via("/eth/XI", xi_entry, label="XI transition via")

    # island F.Cu: MST per net over pads + the transition point
    entries = {"/eth/XI": xi_entry, "/eth/XO": XO_VIA}
    for net in NETS:
        pts, labels = [], []
        if net in entries:
            pts.append(entries[net])
            labels.append("via")
        for pd in allpads:
            if pd["net"] == net:
                pts.append(rl(*pd["c"]))
                labels.append("%s.%s" % (pd["ref"], pd["n"]))
        for i, j, d in mst_edges(pts):
            add_track(net, "F.Cu", pts[i], pts[j],
                      label="%s %s-%s" % (net, labels[i], labels[j]))

    # GND: one stub + via per island GND pad
    gnd_report = {}
    for pd in allpads:
        if pd["net"] != "GND":
            continue
        pc = rl(*pd["c"])
        found = None
        for r in [x / 100.0 for x in range(80, 181, 5)]:
            for k in range(72):
                a = 2 * math.pi * k / 72.0
                cand = (pc[0] + r * math.cos(a), pc[1] + r * math.sin(a))
                V = Point(ab(*cand)).buffer(VIA_D / 2, quad_segs=32)
                # target 1: nothing in this island within 3 mm of the outline
                if RING.distance(V) < 3.0:
                    continue
                if any(math.dist(ab(*cand), h[0]) - VIA_DR / 2 - h[1] / 2 < H2H
                       for h in holes):
                    continue
                bad = False
                for other in allpads:
                    if other is pd or other["net"] == "GND":
                        continue
                    if other["poly"].distance(V) < CLR:
                        bad = True
                        break
                if bad:
                    continue
                # island pad copper of the SAME net may touch, but keep the
                # via body off every pad (no via-in-pad)
                if any(o["poly"].distance(V) < 0.05 for o in allpads):
                    continue
                for lay in bg.copper_layers:
                    polys, tags, tree = surv[lay]
                    for q in tree.query(V.buffer(CLR)):
                        if tags[q][0] != "GND" and polys[q].distance(V) < CLR:
                            bad = True
                            break
                    if bad:
                        break
                if bad:
                    continue
                stub = LineString([ab(*pc), ab(*cand)]).buffer(
                    W_GND / 2, quad_segs=32, cap_style="round")
                for lay in ("F.Cu",):
                    polys, tags, tree = surv[lay]
                    for q in tree.query(stub.buffer(CLR)):
                        if tags[q][0] != "GND" and polys[q].distance(stub) < CLR:
                            bad = True
                            break
                if bad:
                    continue
                for other in allpads:
                    if other["net"] != "GND" and other["poly"].distance(stub) \
                            < CLR:
                        bad = True
                        break
                if bad:
                    continue
                found = cand
                break
            if found:
                break
        if not found:
            raise SystemExit("no legal GND via for %s.%s" % (pd["ref"], pd["n"]))
        lbl = "%s.%s" % (pd["ref"], pd["n"])
        gnd_report[lbl] = [round(q, 4) for q in found]
        add_track("GND", "F.Cu", pc, found, w=W_GND, label="GND stub " + lbl)
        add_via("GND", found, label="GND via " + lbl)

    # ---- pre-flight ------------------------------------------------------
    problems = []
    checks = [(lbl, lays, net, pol) for lbl, lays, net, pol in newgeo]
    for pd in allpads:
        checks.append(("pad %s.%s" % (pd["ref"], pd["n"]),
                       ["F.Cu"], pd["net"], pd["poly"]))
    for lbl, lays, net, pol in checks:
        if RING.distance(pol) < EDGE_CU:
            problems.append("%s: %.4f mm to board edge (< %.2f)"
                            % (lbl, RING.distance(pol), EDGE_CU))
        # target 1: no island copper within 3 mm of the outline
        if RING.distance(pol) < 3.0:
            problems.append("TARGET1 %s: %.4f mm to board edge (< 3.0)"
                            % (lbl, RING.distance(pol)))
        for lay in lays:
            polys, tags, tree = surv[lay]
            for q in tree.query(pol.buffer(CLR)):
                if tags[q][0] == net:
                    continue
                d = polys[q].distance(pol)
                if d < CLR:
                    problems.append("%s vs %s %s on %s: %.4f mm"
                                    % (lbl, tags[q][0], tags[q][1], lay, d))
    # new vs new, and new vs island pads
    for a, b in itertools.combinations(checks, 2):
        if a[2] == b[2]:
            continue
        if not (set(a[1]) & set(b[1])):
            continue
        d = a[3].distance(b[3])
        if d < CLR:
            problems.append("NEW %s vs NEW %s: %.4f mm" % (a[0], b[0], d))
    # island courtyards
    for a, b in itertools.combinations(ISLAND, 2):
        if geos[a][1].intersects(geos[b][1]):
            problems.append("courtyard overlap %s/%s" % (a, b))
    for r in ISLAND:
        for other, f in model.footprints.items():
            if other in ISLAND:
                continue
            if geos[r][1].intersects(f.extents_abs()):
                problems.append("courtyard overlap %s/%s" % (r, other))
        if RING.distance(geos[r][1]) < 3.0:
            problems.append("%s courtyard %.3f mm from outline (< 3.0)"
                            % (r, RING.distance(geos[r][1])))

    # ---- silkscreen (drc_routed counts silk_overlap / silk_over_copper) ----
    _fs = TG.foreign_silk(ISLAND)
    ftag = [t for t, _p in _fs]
    fsilk = [p for _t, p in _fs]
    ftree = STRtree(fsilk) if fsilk else None
    isilk = {r: geos[r][2] for r in ISLAND}
    allpads_poly = [(pd["ref"] + "." + pd["n"], pd["poly"]) for pd in allpads]
    fpads = TG.foreign_pads(ISLAND)
    for r in ISLAND:
        s = isilk[r]
        if s is None:
            continue
        if ftree is not None:
            for k in ftree.query(s):
                if fsilk[k].intersects(s):
                    problems.append("silk_overlap %s:silk vs %s"
                                    % (r, ftag[k]))
        for nm, pol in allpads_poly + fpads:
            if nm.split(".")[0] == r:
                continue
            if s.intersects(pol):
                problems.append("silk_over_copper %s:silk vs pad %s" % (r, nm))
    for a, b in itertools.combinations(ISLAND, 2):
        if isilk[a] is not None and isilk[b] is not None \
                and isilk[a].intersects(isilk[b]):
            problems.append("silk_overlap %s:silk vs %s:silk" % (a, b))
    for r in ISLAND:
        s = isilk[r]
        if s is not None and (not bg.outline.contains(s)
                              or RING.distance(s) < 0.15):
            problems.append("%s silk %.3f mm from outline"
                            % (r, RING.distance(s)))
    for nm, pol in allpads_poly:
        for k in (ftree.query(pol) if ftree is not None else []):
            if fsilk[k].intersects(pol):
                problems.append("silk_over_copper %s vs pad %s"
                                % (ftag[k], nm))
    # hole-to-hole among all holes
    for a, b in itertools.combinations(holes, 2):
        d = math.dist(a[0], b[0]) - a[1] / 2 - b[1] / 2
        if d < H2H:
            problems.append("hole-to-hole %s %s: %.4f mm" % (a[0], b[0], d))

    rep = {"removes": len(removes), "adds": len(adds),
           "kept_segments": len(kept_s), "kept_vias": len(kept_v),
           "gnd_vias_rel": gnd_report,
           "xi_entry_rel": list(xi_entry), "xo_entry_rel": list(XO_VIA),
           "new_copper_mm": {}, "problems": problems}
    for net in NETS + ["GND"]:
        by = {}
        for op in adds:
            if op["op"] != "add_track" or op["net"] != net:
                continue
            L = math.dist(op["start"], op["end"])
            by[op["layer"]] = by.get(op["layer"], 0.0) + L
        rep["new_copper_mm"][net] = {k: round(v, 3) for k, v in by.items()}
    rep["new_vias"] = [(op["net"], rl(*op["at"]))
                       for op in adds if op["op"] == "add_via"]
    print(json.dumps(rep, indent=1))
    if problems:
        print("PRE-FLIGHT FAILED (%d)" % len(problems), file=sys.stderr)
        return 1
    if "--emit" in sys.argv:
        (WORK / "rip.json").write_text(
            json.dumps({"version": 1, "ops": removes}, indent=1), "utf-8")
        (WORK / "place.json").write_text(json.dumps({"version": 1, "ops": [
            {"op": "place", "ref": r, "x": round(ab(pl[r][0], pl[r][1])[0], 4),
             "y": round(ab(pl[r][0], pl[r][1])[1], 4), "deg": pl[r][2],
             "side": "front"} for r in ISLAND]}, indent=1), "utf-8")
        (WORK / "add.json").write_text(
            json.dumps({"version": 1, "ops": adds}, indent=1), "utf-8")
        print("emitted rip.json / place.json / add.json", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
