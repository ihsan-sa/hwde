"""Search the tightest legal placement of the eth_xtal island in the pocket
north of U10, minimising routed copper on the three oscillator nets.

Hard constraints: pad clearance >= CLR to foreign F.Cu copper, no courtyard
overlap (against other footprints AND among the five island parts), extents
inside the outline and >= EDGE from it, a legal GND via near every GND pad.

Cost = F.Cu MST copper of the three nets given the two B.Cu entry points
       (XO fixed at the existing via, XI free along the y = YXI line)
       + the B.Cu run needed to reach the XI entry.
"""
import itertools
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SC = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SC))
sys.path.insert(0, str(SC / "lib"))

import geom  # noqa: E402
import placelib  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

PCB = ROOT / "boards" / "lumina-carrier" / "kicad" / "lumina-carrier.kicad_pcb"
NETS = {"/eth/XI", "/eth/XO", "/eth/XO_XTAL"}
ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
CLR = 0.25
EDGE = 3.0
STEP = 0.25
# search window, board-relative
WX = (65.0, 77.0)
WY = (3.5, 8.6)
# B.Cu entries
XO_ENTRY = (75.345, 8.868)      # existing /eth/XO via, F.Cu side (unchanged)
XI_BCU_FROM = (75.22, 14.468)   # end of the kept /eth/XI B.Cu escape
# /eth/XI's new B.Cu leg must stay >= 0.4 mm west of /eth/XO's kept B.Cu
# (vertical x = 75.345 for y 8.868..11.793), so the transition via x <= 74.9.
XI_X_RANGE = (66.0, 74.90)
W_R36 = 1.0   # extra weight on driver-transition -> R36 pad 1 (target 2)

bg = geom.load_board(PCB)
model = placelib.PlaceModel(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
RING = bg.outline.exterior


def rel(x, y):
    return (x - OX, y - OY)


def ab(x, y):
    return (x + OX, y + OY)


# ---------------------------------------------------------------- obstacles
def _cu(layer):
    polys = []
    for t in bg.tracks_of(layer=layer):
        if t.net not in NETS:
            polys.append(t.poly)
    for v in bg.vias_of():
        if v.spans(layer) and v.net not in NETS:
            polys.append(v.poly)
    for p in bg.pads_of(layer=layer):
        if p.ref not in ISLAND:
            polys.append(p.poly)
    return polys


F_CU = _cu("F.Cu")
F_TREE = STRtree(F_CU)
ALL_CU = {la: (_cu(la), STRtree(_cu(la))) for la in bg.copper_layers}
OTHER_EXT = unary_union([f.extents_abs() for r, f in model.footprints.items()
                         if r not in ISLAND])


def part_geo(ref, deg, x, y):
    f = model.footprints[ref]
    pads = []
    for p in f.pads:
        lx, ly = p.local
        pol = box(lx - p.size[0] / 2, ly - p.size[1] / 2,
                  lx + p.size[0] / 2, ly + p.size[1] / 2)
        pol = affinity.rotate(pol, -deg, origin=(0, 0))
        pol = affinity.translate(pol, x, y)
        cx, cy = geom._rot(lx, ly, -deg)
        pads.append({"n": p.number, "net": p.net, "poly": pol,
                     "c": (x + cx, y + cy)})
    ext = affinity.translate(
        affinity.rotate(f.extents_local(), -deg, origin=(0, 0)), x, y)
    return pads, ext


def via_ok(cx, cy, dia=0.6, drill=0.3):
    """Is a through via legal at abs (cx,cy) on every copper layer?"""
    p = Point(cx, cy).buffer(dia / 2.0, quad_segs=32)
    for la, (polys, tree) in ALL_CU.items():
        for k in tree.query(p.buffer(CLR)):
            if polys[k].distance(p) < CLR:
                return False
    if RING.distance(p) < 0.5:      # min_copper_edge_clearance
        return False
    return True


def gnd_via_for(pad_center, pads_all):
    """Find a legal GND via <= 1.2 mm from a GND pad center, not clashing with
    any island pad. Returns (x, y) abs or None."""
    best = None
    for r in (0.55, 0.7, 0.85, 1.0, 1.2):
        for k in range(24):
            a = 2 * math.pi * k / 24.0
            cx = pad_center[0] + r * math.cos(a)
            cy = pad_center[1] + r * math.sin(a)
            v = Point(cx, cy).buffer(0.3, quad_segs=32)
            bad = False
            for pd in pads_all:
                if pd["net"] == "GND":
                    continue
                if pd["poly"].distance(v) < CLR:
                    bad = True
                    break
            if bad or not via_ok(cx, cy):
                continue
            if best is None or r < best[2]:
                best = (cx, cy, r)
        if best:
            break
    return best[:2] if best else None


# --------------------------------------------------- per-part feasible sets
def feasible(ref):
    out = []
    nx = int(round((WX[1] - WX[0]) / STEP))
    ny = int(round((WY[1] - WY[0]) / STEP))
    for deg in (0, 90, 180, 270):
        for i in range(nx + 1):
            for j in range(ny + 1):
                xr, yr = WX[0] + i * STEP, WY[0] + j * STEP
                x, y = ab(xr, yr)
                pads, ext = part_geo(ref, deg, x, y)
                if not bg.outline.contains(ext) or RING.distance(ext) < EDGE:
                    continue
                if OTHER_EXT.intersects(ext):
                    continue
                bad = False
                for pd in pads:
                    for k in F_TREE.query(pd["poly"].buffer(CLR)):
                        if F_CU[k].distance(pd["poly"]) < CLR:
                            bad = True
                            break
                    if bad:
                        break
                if bad:
                    continue
                out.append((round(xr, 3), round(yr, 3), deg))
    return out


XI_ENTRIES = []


def xi_bcu_len(ent):
    """B.Cu length of the new /eth/XI leg: 45-degree dogleg from XI_BCU_FROM
    out to the entry column, then straight north. None if geometrically
    impossible."""
    ex, ey = ent
    dx = XI_BCU_FROM[0] - ex
    if dx < 0:
        return None
    run = XI_BCU_FROM[1] - dx - ey     # remaining vertical after the 45 leg
    if run < 0:
        return None
    return dx * math.sqrt(2.0) + run


def build_xi_entries():
    out = []
    for k in range(int((XI_X_RANGE[1] - XI_X_RANGE[0]) / 0.25) + 1):
        ex = XI_X_RANGE[0] + 0.25 * k
        for ey in (8.55, 8.80):
            if via_ok(*ab(ex, ey)):
                out.append((ex, ey))
    return out


def mst(points):
    if len(points) < 2:
        return 0.0
    inside = [0]
    rest = list(range(1, len(points)))
    total = 0.0
    while rest:
        bd, bi, bj = 1e9, None, None
        for i in inside:
            for j in rest:
                d = math.dist(points[i], points[j])
                if d < bd:
                    bd, bi, bj = d, i, j
        total += bd
        inside.append(bj)
        rest.remove(bj)
    return total


def evaluate(state, cache={}):
    """state: {ref: (xr, yr, deg)} -> (cost, detail) or None if illegal."""
    geos = {}
    for ref, s in state.items():
        key = (ref, s)
        if key not in cache:
            cache[key] = part_geo(ref, s[2], *ab(s[0], s[1]))
        geos[ref] = cache[key]
    refs = list(state)
    for a, b in itertools.combinations(refs, 2):
        if geos[a][1].intersects(geos[b][1]):
            return None
    allpads = [pd for r in refs for pd in geos[r][0]]
    for a, b in itertools.combinations(allpads, 2):
        if a["net"] != b["net"] and a["poly"].distance(b["poly"]) < CLR:
            return None
    bynet = {}
    for pd in allpads:
        if pd["net"] in NETS:
            bynet.setdefault(pd["net"], []).append(rel(*pd["c"]))
    # XO net: island pads + fixed entry
    cost_xo = mst(bynet.get("/eth/XO", []) + [XO_ENTRY])
    cost_xx = mst(bynet.get("/eth/XO_XTAL", []))
    # no via-in-pad: the XO transition via must stay clear of every island pad
    xo_v = Point(*ab(*XO_ENTRY)).buffer(0.3, quad_segs=32)
    for pd in allpads:
        if pd["poly"].distance(xo_v) < 0.2:
            return None
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
    r36p1 = next((rel(*pd["c"]) for pd in geos["R36"][0] if pd["n"] == "1"),
                 None)
    pen = W_R36 * math.dist(r36p1, XO_ENTRY) if r36p1 else 0.0
    return (cost_xo + cost_xx + bcost + pen,
            {"xo": cost_xo, "xo_xtal": cost_xx, "xi_total": bcost,
             "xi_bcu": bbcu, "r36_to_xo_via": pen / W_R36 if W_R36 else None,
             "copper_mm": cost_xo + cost_xx + bcost,
             "xi_entry": [round(bent[0], 3), round(bent[1], 3)]})


def anneal(feas, iters=40000, seed=7):
    rng = random.Random(seed)
    # seed: pick the south-east-most legal spot for each
    state = {}
    for ref in ISLAND:
        state[ref] = max(feas[ref], key=lambda s: (s[0] + s[1]))
    cur = evaluate(state)
    tries = 0
    while cur is None and tries < 20000:
        for ref in ISLAND:
            state[ref] = rng.choice(feas[ref])
        cur = evaluate(state)
        tries += 1
    if cur is None:
        return None, None
    best, beststate = cur, dict(state)
    T0, T1 = 2.0, 0.02
    for it in range(iters):
        T = T0 * (T1 / T0) ** (it / iters)
        ref = rng.choice(ISLAND)
        old = state[ref]
        if rng.random() < 0.6:
            cands = [s for s in feas[ref]
                     if abs(s[0] - old[0]) <= 1.0 and abs(s[1] - old[1]) <= 1.0]
            state[ref] = rng.choice(cands) if cands else rng.choice(feas[ref])
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


if __name__ == "__main__":
    XI_ENTRIES.extend(build_xi_entries())
    print("xi entries: %d" % len(XI_ENTRIES), file=sys.stderr)
    feas = {}
    for ref in ISLAND:
        feas[ref] = feasible(ref)
        print("%s: %d legal poses" % (ref, len(feas[ref])), file=sys.stderr)
    results = []
    for seed in (1, 2, 3, 5, 7, 11, 13, 17):
        best, st = anneal(feas, iters=int(sys.argv[1]) if len(sys.argv) > 1
                          else 30000, seed=seed)
        if best:
            results.append((best[0], seed, best[1], st))
            print("seed %d -> %.3f mm" % (seed, best[0]), file=sys.stderr)
    results.sort(key=lambda r: r[0])
    cost, seed, detail, st = results[0]
    # GND via probe for the winner
    geos = {r: part_geo(r, st[r][2], *ab(st[r][0], st[r][1])) for r in ISLAND}
    allpads = [pd for r in ISLAND for pd in geos[r][0]]
    gnd = {}
    for r in ISLAND:
        for pd in geos[r][0]:
            if pd["net"] == "GND":
                v = gnd_via_for(pd["c"], allpads)
                gnd["%s.%s" % (r, pd["n"])] = (
                    [round(q, 4) for q in rel(*v)] if v else None)
    out = {"cost_mm": round(cost, 3), "seed": seed, "detail": detail,
           "placement": {r: {"x_rel": st[r][0], "y_rel": st[r][1],
                             "deg": st[r][2],
                             "x_abs": round(ab(st[r][0], st[r][1])[0], 4),
                             "y_abs": round(ab(st[r][0], st[r][1])[1], 4)}
                         for r in ISLAND},
           "pads": {r: [{"n": pd["n"], "net": pd["net"],
                         "c_rel": [round(q, 4) for q in rel(*pd["c"])]}
                        for pd in geos[r][0]] for r in ISLAND},
           "gnd_vias_rel": gnd,
           "alternatives": [{"cost": round(c, 3), "seed": s,
                             "placement": {r: list(v) for r, v in stt.items()}}
                            for c, s, _d, stt in results]}
    print(json.dumps(out, indent=1))
