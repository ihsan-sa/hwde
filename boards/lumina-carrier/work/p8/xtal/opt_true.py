"""Final island placement search on EXACT KiCad geometry (truegeo).

Hard constraints (everything drc_routed counts, at any severity):
  clearance / shorting : island pad copper >= 0.2 mm from foreign copper and
                         from island pads of other nets  (checked at 0.25)
  courtyards_overlap   : island extents vs all other extents
  silk_overlap         : island silk vs island silk and vs foreign silk
                         (incl. foreign visible Reference boxes)
  silk_over_copper     : island silk vs any pad; foreign silk vs island pads
  copper to board edge >= 0.5, island courtyard >= 3.0 mm from the outline
  no via-in-pad at either layer transition
Objective: F.Cu MST of the three nets + the new /eth/XI B.Cu leg
           + 1.0 * (driver transition -> R36 pad 1).
"""
import itertools
import json
import math
import random
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
import truegeo  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

PCB = WORK / "pre_xtal.kicad_pcb"
PROBE = WORK / "probe_pre.json"
NETS = {"/eth/XI", "/eth/XO", "/eth/XO_XTAL"}
ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
CLR = 0.25
EDGE_CY = 3.0
EDGE_CU = 0.5
SILK_EDGE = 0.15
STEP = 0.25
WX = (65.0, 77.5)
WY = (3.5, 8.8)
XO_ENTRY = (75.345, 8.868)
XI_BCU_FROM = (75.22, 14.468)
XI_X_RANGE = (66.0, 74.90)
W_R36 = 1.0

bg = geom.load_board(PCB)
model = placelib.PlaceModel(PCB)
TG = truegeo.TrueGeo(PROBE)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
RING = bg.outline.exterior
PADNET = {(p.ref, p.number): p.net for p in bg.pads_of()}


def ab(x, y):
    return (x + OX, y + OY)


def rel(x, y):
    return (x - OX, y - OY)


# --------------------------------------------------------------- obstacles
def _cu(layer):
    """Foreign copper on `layer`: tracks/vias from geom, pads from truegeo."""
    polys = []
    for t in bg.tracks_of(layer=layer):
        if t.net not in NETS:
            polys.append(t.poly)
    for v in bg.vias_of():
        if v.spans(layer) and v.net not in NETS:
            polys.append(v.poly)
    for tag, p in TG.foreign_pads(ISLAND):
        r, n = tag.rsplit(".", 1)
        pd = next((q for q in bg.pads_of(ref=r) if q.number == n), None)
        if pd is not None and layer in pd.layers:
            polys.append(p)
    return polys


ALL_CU = {la: (lambda P: (P, STRtree(P)))(_cu(la)) for la in bg.copper_layers}
F_CU, F_TREE = ALL_CU["F.Cu"]
OTHER_EXT = unary_union([f.extents_abs() for r, f in model.footprints.items()
                         if r not in ISLAND])
FSILK = TG.foreign_silk(ISLAND)
FS_POLY = [p for _t, p in FSILK]
FS_TREE = STRtree(FS_POLY)
FPADS = TG.foreign_pads(ISLAND)
FP_POLY = [p for _t, p in FPADS]
FP_TREE = STRtree(FP_POLY)


def part_geo(ref, deg, xr, yr):
    x, y = ab(xr, yr)
    pads = [{"ref": ref, "n": n, "net": PADNET.get((ref, n)), "poly": p,
             "c": (p.centroid.x, p.centroid.y)}
            for n, p in TG.pads_at(ref, (x, y), deg)]
    f = model.footprints[ref]
    ext = affinity.translate(
        affinity.rotate(f.extents_local(), -deg, origin=(0, 0)), x, y)
    return pads, ext, TG.silk_at(ref, (x, y), deg)


def via_ok(cx, cy, dia=0.6):
    p = Point(cx, cy).buffer(dia / 2.0, quad_segs=32)
    for la, (polys, tree) in ALL_CU.items():
        for k in tree.query(p.buffer(CLR)):
            if polys[k].distance(p) < CLR:
                return False
    return RING.distance(p) >= EDGE_CU


XI_ENTRIES = []


def xi_bcu_len(ent):
    ex, ey = ent
    dx = XI_BCU_FROM[0] - ex
    if dx < 0:
        return None
    run = XI_BCU_FROM[1] - dx - ey
    if run < 0:
        return None
    return dx * math.sqrt(2.0) + run


def feasible(ref):
    out = []
    nx = int(round((WX[1] - WX[0]) / STEP))
    ny = int(round((WY[1] - WY[0]) / STEP))
    for deg in (0, 90, 180, 270):
        for i in range(nx + 1):
            for j in range(ny + 1):
                xr, yr = round(WX[0] + i * STEP, 3), round(WY[0] + j * STEP, 3)
                pads, ext, silk = part_geo(ref, deg, xr, yr)
                if not bg.outline.contains(ext) or RING.distance(ext) < EDGE_CY:
                    continue
                if OTHER_EXT.intersects(ext):
                    continue
                bad = False
                for pd in pads:
                    if RING.distance(pd["poly"]) < EDGE_CU:
                        bad = True
                        break
                    for k in F_TREE.query(pd["poly"].buffer(CLR)):
                        if F_CU[k].distance(pd["poly"]) < CLR:
                            bad = True
                            break
                    if bad:
                        break
                    for k in FS_TREE.query(pd["poly"]):
                        if FS_POLY[k].intersects(pd["poly"]):
                            bad = True
                            break
                    if bad:
                        break
                if bad or silk is None or silk.is_empty:
                    continue
                for k in FS_TREE.query(silk):
                    if FS_POLY[k].intersects(silk):
                        bad = True
                        break
                if bad:
                    continue
                for k in FP_TREE.query(silk):
                    if FP_POLY[k].intersects(silk):
                        bad = True
                        break
                if bad:
                    continue
                if not bg.outline.contains(silk) or \
                        RING.distance(silk) < SILK_EDGE:
                    continue
                out.append((xr, yr, deg))
    return out


def mst(points):
    if len(points) < 2:
        return 0.0
    inside, rest, total = [0], list(range(1, len(points))), 0.0
    while rest:
        bd, bj = 1e9, None
        for i in inside:
            for j in rest:
                d = math.dist(points[i], points[j])
                if d < bd:
                    bd, bj = d, j
        total += bd
        inside.append(bj)
        rest.remove(bj)
    return total


_cache = {}


def evaluate(state):
    geos = {}
    for ref, s in state.items():
        key = (ref, s)
        if key not in _cache:
            _cache[key] = part_geo(ref, s[2], s[0], s[1])
        geos[ref] = _cache[key]
    refs = list(state)
    for a, b in itertools.combinations(refs, 2):
        if geos[a][1].intersects(geos[b][1]):
            return None
        if geos[a][2].intersects(geos[b][2]):
            return None
        for pd in geos[b][0]:
            if geos[a][2].intersects(pd["poly"]):
                return None
        for pd in geos[a][0]:
            if geos[b][2].intersects(pd["poly"]):
                return None
    allpads = [pd for r in refs for pd in geos[r][0]]
    for a, b in itertools.combinations(allpads, 2):
        if a["net"] != b["net"] and a["poly"].distance(b["poly"]) < CLR:
            return None
    xo_v = Point(*ab(*XO_ENTRY)).buffer(0.3, quad_segs=32)
    for pd in allpads:
        if pd["poly"].distance(xo_v) < 0.2:
            return None
    bynet = {}
    for pd in allpads:
        if pd["net"] in NETS:
            bynet.setdefault(pd["net"], []).append(rel(*pd["c"]))
    cost_xo = mst(bynet.get("/eth/XO", []) + [XO_ENTRY])
    cost_xx = mst(bynet.get("/eth/XO_XTAL", []))
    xi = bynet.get("/eth/XI", [])
    bcost, bent, bbcu = 1e9, None, None
    for ent in XI_ENTRIES:
        bcu = xi_bcu_len(ent)
        if bcu is None:
            continue
        xi_v = Point(*ab(*ent)).buffer(0.3, quad_segs=32)
        if any(pd["poly"].distance(xi_v) < 0.2 for pd in allpads):
            continue
        c = mst(xi + [ent]) + bcu
        if c < bcost:
            bcost, bent, bbcu = c, ent, bcu
    if bent is None:
        return None
    r36p1 = next(rel(*pd["c"]) for pd in geos["R36"][0] if pd["n"] == "1")
    d36 = math.dist(r36p1, XO_ENTRY)
    return (cost_xo + cost_xx + bcost + W_R36 * d36,
            {"xo": cost_xo, "xo_xtal": cost_xx, "xi_total": bcost,
             "xi_bcu": bbcu, "r36_to_xo_via": d36,
             "copper_mm": cost_xo + cost_xx + bcost,
             "xi_entry": [round(bent[0], 3), round(bent[1], 3)]})


def anneal(feas, iters, seed):
    rng = random.Random(seed)
    state, cur = None, None
    for _ in range(60000):
        state = {r: rng.choice(feas[r]) for r in ISLAND}
        cur = evaluate(state)
        if cur:
            break
    if cur is None:
        return None, None
    best, beststate = cur, dict(state)
    T0, T1 = 2.0, 0.02
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        ref = rng.choice(ISLAND)
        old = state[ref]
        if rng.random() < 0.65:
            c = [s for s in feas[ref] if abs(s[0] - old[0]) <= 1.25
                 and abs(s[1] - old[1]) <= 1.25]
            state[ref] = rng.choice(c) if c else rng.choice(feas[ref])
        else:
            state[ref] = rng.choice(feas[ref])
        new = evaluate(state)
        if new is None or (new[0] > cur[0]
                           and rng.random() > math.exp((cur[0] - new[0]) / T)):
            state[ref] = old
        else:
            cur = new
            if new[0] < best[0]:
                best, beststate = new, dict(state)
    return best, beststate


def polish(feas, state, span=2.5, rounds=10):
    cur = evaluate(state)
    for _ in range(rounds):
        improved = False
        for ref in ISLAND:
            old = state[ref]
            bp, bc = old, cur
            for s in feas[ref]:
                if abs(s[0] - old[0]) > span or abs(s[1] - old[1]) > span:
                    continue
                state[ref] = s
                v = evaluate(state)
                if v is not None and v[0] < bc[0] - 1e-9:
                    bp, bc = s, v
            state[ref] = bp
            if bp != old:
                cur, improved = bc, True
        if not improved:
            break
    return cur, state


if __name__ == "__main__":
    for k in range(int((XI_X_RANGE[1] - XI_X_RANGE[0]) / 0.25) + 1):
        ex = XI_X_RANGE[0] + 0.25 * k
        for ey in (8.55, 8.80):
            if via_ok(*ab(ex, ey)):
                XI_ENTRIES.append((ex, ey))
    print("xi entries %d" % len(XI_ENTRIES), file=sys.stderr)
    feas = {r: feasible(r) for r in ISLAND}
    for r in ISLAND:
        print("%s: %d legal poses" % (r, len(feas[r])), file=sys.stderr)
        if not feas[r]:
            raise SystemExit("no legal pose for %s" % r)
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    seeds = [int(s) for s in (sys.argv[2].split(",") if len(sys.argv) > 2
                              else ["29"])]
    res = []
    for sd in seeds:
        b, st = anneal(feas, iters, sd)
        if not b:
            continue
        b, st = polish(feas, st)
        res.append((b[0], sd, b[1], st))
        print("seed %d -> %.3f (copper %.3f, r36->via %.3f)"
              % (sd, b[0], b[1]["copper_mm"], b[1]["r36_to_xo_via"]),
              file=sys.stderr)
    if not res:
        raise SystemExit("no feasible layout")
    res.sort(key=lambda t: t[0])
    cost, sd, detail, st = res[0]
    geos = {r: part_geo(r, st[r][2], st[r][0], st[r][1]) for r in ISLAND}
    print(json.dumps({
        "cost_mm": round(cost, 3), "seed": sd, "detail": detail,
        "placement": {r: {"x_rel": st[r][0], "y_rel": st[r][1],
                          "deg": st[r][2],
                          "x_abs": round(ab(st[r][0], st[r][1])[0], 4),
                          "y_abs": round(ab(st[r][0], st[r][1])[1], 4)}
                      for r in ISLAND},
        "pads": {r: [{"n": pd["n"], "net": pd["net"],
                      "c_rel": [round(q, 4) for q in rel(*pd["c"])]}
                     for pd in geos[r][0]] for r in ISLAND},
        "alternatives": [{"cost": round(c, 3),
                          "copper": round(d["copper_mm"], 3), "seed": s,
                          "placement": {r: list(v) for r, v in stt.items()}}
                         for c, s, d, stt in res]}, indent=1))
