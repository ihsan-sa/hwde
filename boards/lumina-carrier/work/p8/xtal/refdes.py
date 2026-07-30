"""Find legal F.Silkscreen positions for the five island parts' Reference
fields, using EXACT KiCad geometry (truegeo over a probe of the CURRENT board),
and emit a place_edit move_text ops file.

Legal = the field's exact inked stroke box intersects no other silk graphic
(island or foreign, including foreign Reference boxes), no pad, and stays
inside the outline.  Objective: keep the label as close to its own part's silk
as possible (P8 silk-legibility rule: refdes within ~1.6 mm of its part).

usage: refdes.py PROBE.json [--emit OUT.json]
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
WORK = ROOT / "boards" / "lumina-carrier" / "work" / "p8" / "xtal"
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "ai-ee" / "scripts" / "lib"))
sys.path.insert(0, str(WORK))

import truegeo  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

ISLAND = ["Y10", "C30", "C31", "R35", "R36"]
EDGE_SILK = 0.2
# work/p8/silk/solve.py used the same 0.05 mm demanded gap around the inked box
MARGIN = 0.05

TG = truegeo.TrueGeo(sys.argv[1])
OUTLINE = TG.outline
RING = OUTLINE.exterior

# static silk: every front-side graphic, plus every NON-island Reference box
static, stag = [], []
for r, f in TG.fp.items():
    if f["side"] == "front" and f["silk"] is not None and not f["silk"].is_empty:
        static.append(f["silk"])
        stag.append(r + ":silk")
    if r not in ISLAND:
        rb = TG.ref_box_now(r)
        if rb is not None:
            static.append(rb)
            stag.append(r + ":REF")
S_TREE = STRtree(static)
PADS = [q for _t, q in TG.foreign_pads([]) if q is not None and not q.is_empty]
P_TREE = STRtree(PADS)


def ok(bx, placed):
    if not OUTLINE.contains(bx) or RING.distance(bx) < EDGE_SILK:
        return False
    g = bx.buffer(MARGIN)
    for k in S_TREE.query(g):
        if static[k].distance(bx) < MARGIN:
            return False
    for k in P_TREE.query(g):
        if PADS[k].distance(bx) < MARGIN:
            return False
    return not any(p.distance(bx) < MARGIN for p in placed)


ops, placed, report = [], [], {}
for ref in sorted(ISLAND, key=lambda r: -len(TG.fp[r]["ref_text"]["text"])):
    f = TG.fp[ref]
    own = f["silk"]
    pos = f["pos"]
    cur = TG.ref_box_now(ref)
    best = None
    if cur is not None and ok(cur, placed):
        rt = f["ref_text"]
        best = (round(own.distance(cur), 4) if own is not None else 0.0,
                cur, rt["x"], rt["y"], rt["angle"], "kept")
    if best is None:
        cands = []
        for deg in (0.0, 90.0):
            for rr in [x / 20.0 for x in range(20, 141)]:   # 1.0 .. 7.0 mm
                for k in range(72):
                    a = 2 * math.pi * k / 72.0
                    cx = pos[0] + rr * math.cos(a)
                    cy = pos[1] + rr * math.sin(a)
                    bx = TG.ref_box(ref, cx, cy, deg)
                    if bx is None or not ok(bx, placed):
                        continue
                    d = own.distance(bx) if own is not None else rr
                    cands.append((round(d, 4), round(rr, 4), bx, cx, cy, deg))
                if cands and rr > min(c[1] for c in cands) + 1.0:
                    break
        if cands:
            d, _rr, bx, cx, cy, deg = min(cands, key=lambda c: (c[0], c[1]))
            best = (d, bx, cx, cy, deg, "moved")
    if best is None:
        raise SystemExit("no legal refdes position for %s" % ref)
    placed.append(best[1])
    report[ref] = {"status": best[5], "gap_to_own_silk_mm": best[0],
                   "x": round(best[2], 4), "y": round(best[3], 4),
                   "deg": best[4],
                   "dist_from_origin_mm": round(
                       math.dist((best[2], best[3]), pos), 4)}
    if best[5] == "moved":
        ops.append({"op": "move_text", "ref": ref, "field": "reference",
                    "x": round(best[2], 4), "y": round(best[3], 4),
                    "deg": best[4]})
print(json.dumps({"refdes": report, "ops": len(ops)}, indent=1))
if "--emit" in sys.argv:
    out = Path(sys.argv[sys.argv.index("--emit") + 1])
    out.write_text(json.dumps({"version": 1, "ops": ops}, indent=1), "utf-8")
    print("emitted %s (%d ops)" % (out, len(ops)), file=sys.stderr)
