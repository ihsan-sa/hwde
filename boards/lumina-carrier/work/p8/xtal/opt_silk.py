"""opt.py + silkscreen legality.

Adds, as HARD constraints, everything the drc_routed gate counts as a warning:
  silk_overlap    : island silk graphics must not intersect any other silk
                    (island or foreign, including foreign Reference fields)
  silk_over_copper: island silk must not intersect any pad, and foreign silk
                    (incl. foreign Reference fields) must not intersect island
                    pads
Each footprint's own Reference field is EXCLUDED from the island silk (it is
repositioned afterwards by place_edit move_text) but foreign ones are kept.
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
import sexpdata  # noqa: E402
import silk_geo  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

PCB = WORK / "pre_xtal.kicad_pcb"     # the PRE-EDIT board: original positions
NETS = {"/eth/XI", "/eth/XO", "/eth/XO_XTAL"}
ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
CLR = 0.25
EDGE = 3.0
STEP = 0.25
WX = (65.0, 77.5)
WY = (3.5, 8.6)
XO_ENTRY = (75.345, 8.868)
XI_BCU_FROM = (75.22, 14.468)
XI_X_RANGE = (66.0, 74.90)
W_R36 = 1.0

bg = geom.load_board(PCB)
model = placelib.PlaceModel(PCB)
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]
RING = bg.outline.exterior


def ab(x, y):
    return (x + OX, y + OY)


def rel(x, y):
    return (x - OX, y - OY)


# ------------------------------------------------------------------ silk data
root = sexpdata.loads(PCB.read_text(encoding="utf-8"))
SILK_LOCAL = {}     # ref -> shapely in local frame (Reference field EXCLUDED)
REF_FIELD = {}
for fp in silk_geo.kids(root, "footprint"):
    r = None
    for prop in silk_geo.kids(fp, "property"):
        s = silk_geo.strs(prop)
        if len(s) >= 2 and s[0] == "Reference":
            r = s[1]
            break
    if r is None:
        continue
    lay = silk_geo.layer_of(fp) or "F.Cu"
    side = "back" if lay.startswith("B.") else "front"
    g, rf = silk_geo.footprint_silk(fp, side)
    SILK_LOCAL[r] = (g, side)
    REF_FIELD[r] = rf


def ref_box_local(rf):
    """Inked stroke box of a Reference field in the footprint-local frame.
    LEARNINGS: DRC uses the INKED box (~1.16 mm tall for size 1.0), not
    GetTextBox (1.70 mm)."""
    if rf is None or rf.get("hide"):
        return None
    n = len(rf["text"])
    sx, sy = rf["size"][0], rf["size"][1]
    th = rf["thickness"]
    w = n * sx * 0.8 + th          # stroke-font advance ~0.8*size + pen
    h = sy + th
    b = box(-w / 2, -h / 2, w / 2, h / 2)
    b = affinity.rotate(b, -rf["deg_local"], origin=(0, 0))
    return affinity.translate(b, rf["at_local"][0], rf["at_local"][1])


def silk_abs(ref, deg, x, y, with_ref=False):
    g, _side = SILK_LOCAL[ref]
    parts = []
    if g is not None:
        parts.append(g)
    if with_ref:
        rb = ref_box_local(REF_FIELD.get(ref))
        if rb is not None:
            parts.append(rb)
    if not parts:
        return None
    u = unary_union(parts)
    return affinity.translate(affinity.rotate(u, -deg, origin=(0, 0)), x, y)


# ------------------------------------------------------------- static obstacles
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
# foreign silk (front side only - island parts are all front) incl. ref fields
_fs = []
for r, f in model.footprints.items():
    if r in ISLAND or SILK_LOCAL.get(r, (None, "front"))[1] != "front":
        continue
    s = silk_abs(r, f.angle, f.pos[0], f.pos[1], with_ref=True)
    if s is not None and not s.is_empty:
        _fs.append(s)
FOREIGN_SILK = list(_fs)
FS_TREE = STRtree(FOREIGN_SILK)
# foreign F.Cu pads only (silk_over_copper is silk vs mask aperture = pad)
FOREIGN_PADS = [p.poly for p in bg.pads_of(layer="F.Cu") if p.ref not in ISLAND]
FP_TREE = STRtree(FOREIGN_PADS)


def part_geo(ref, deg, x, y):
    f = model.footprints[ref]
    pads = []
    for p in f.pads:
        lx, ly = p.local
        pol = box(lx - p.size[0] / 2, ly - p.size[1] / 2,
                  lx + p.size[0] / 2, ly + p.size[1] / 2)
        pol = affinity.translate(affinity.rotate(pol, -deg, origin=(0, 0)),
                                 x, y)
        cx, cy = geom._rot(lx, ly, -deg)
        pads.append({"ref": ref, "n": p.number, "net": p.net, "poly": pol,
                     "c": (x + cx, y + cy)})
    ext = affinity.translate(
        affinity.rotate(f.extents_local(), -deg, origin=(0, 0)), x, y)
    return pads, ext, silk_abs(ref, deg, x, y, with_ref=False)


def via_ok(cx, cy, dia=0.6):
    p = Point(cx, cy).buffer(dia / 2.0, quad_segs=32)
    for la, (polys, tree) in ALL_CU.items():
        for k in tree.query(p.buffer(CLR)):
            if polys[k].distance(p) < CLR:
                return False
    return RING.distance(p) >= 0.5


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
                xr, yr = WX[0] + i * STEP, WY[0] + j * STEP
                x, y = ab(xr, yr)
                pads, ext, silk = part_geo(ref, deg, x, y)
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
                    for k in FS_TREE.query(pd["poly"]):
                        if FOREIGN_SILK[k].intersects(pd["poly"]):
                            bad = True
                            break
                    if bad:
                        break
                if bad or silk is None:
                    continue
                for k in FS_TREE.query(silk):
                    if FOREIGN_SILK[k].intersects(silk):
                        bad = True
                        break
                if bad:
                    continue
                for k in FP_TREE.query(silk):
                    if FOREIGN_PADS[k].intersects(silk):
                        bad = True
                        break
                if bad:
                    continue
                if not bg.outline.contains(silk) or RING.distance(silk) < 0.15:
                    continue
                out.append((round(xr, 3), round(yr, 3), deg))
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
            _cache[key] = part_geo(ref, s[2], *ab(s[0], s[1]))
        geos[ref] = _cache[key]
    refs = list(state)
    for a, b in itertools.combinations(refs, 2):
        if geos[a][1].intersects(geos[b][1]):
            return None
        if geos[a][2].intersects(geos[b][2]):        # silk vs silk
            return None
        for pd in geos[b][0]:                        # silk vs pad
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
    pen = W_R36 * math.dist(r36p1, XO_ENTRY)
    return (cost_xo + cost_xx + bcost + pen,
            {"xo": cost_xo, "xo_xtal": cost_xx, "xi_total": bcost,
             "xi_bcu": bbcu, "r36_to_xo_via": math.dist(r36p1, XO_ENTRY),
             "copper_mm": cost_xo + cost_xx + bcost,
             "xi_entry": [round(bent[0], 3), round(bent[1], 3)]})


def anneal(feas, iters, seed):
    rng = random.Random(seed)
    state, cur = None, None
    for _ in range(40000):
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
            cands = [s for s in feas[ref]
                     if abs(s[0] - old[0]) <= 1.25 and abs(s[1] - old[1]) <= 1.25]
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


def polish(feas, state, span=2.5, rounds=8):
    """Coordinate descent to a true local optimum: exhaustively re-pose one
    part at a time within +-span mm (all 4 orientations)."""
    cur = evaluate(state)
    for _ in range(rounds):
        improved = False
        for ref in ISLAND:
            old = state[ref]
            bestpose, bestcost = old, cur
            for s in feas[ref]:
                if abs(s[0] - old[0]) > span or abs(s[1] - old[1]) > span:
                    continue
                state[ref] = s
                v = evaluate(state)
                if v is not None and v[0] < bestcost[0] - 1e-9:
                    bestpose, bestcost = s, v
            state[ref] = bestpose
            if bestpose != old:
                cur, improved = bestcost, True
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
        print("%s: %d silk-legal poses" % (r, len(feas[r])), file=sys.stderr)
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
    seeds = [int(s) for s in (sys.argv[2].split(",") if len(sys.argv) > 2
                              else ["1", "3", "7", "13"])]
    res = []
    for sd in seeds:
        b, st = anneal(feas, iters, sd)
        if b:
            print("seed %d anneal -> %.3f (copper %.3f)"
                  % (sd, b[0], b[1]["copper_mm"]), file=sys.stderr)
            b, st = polish(feas, st)
            res.append((b[0], sd, b[1], st))
            print("seed %d polish -> %.3f (copper %.3f, r36->via %.3f)"
                  % (sd, b[0], b[1]["copper_mm"], b[1]["r36_to_xo_via"]),
                  file=sys.stderr)
    if not res:
        raise SystemExit("no feasible silk-legal layout found")
    res.sort(key=lambda t: t[0])
    cost, sd, detail, st = res[0]
    geos = {r: part_geo(r, st[r][2], *ab(st[r][0], st[r][1])) for r in ISLAND}
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
        "alternatives": [{"cost": round(c, 3), "copper": round(d["copper_mm"], 3),
                          "seed": s, "placement": {r: list(v)
                                                   for r, v in stt.items()}}
                         for c, s, d, stt in res]}, indent=1))
