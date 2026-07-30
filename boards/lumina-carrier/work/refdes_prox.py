"""Measure each refdes text offset from its own footprint. JSON to stdout."""
import json, math, sys
sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts/lib')
import sexpdata

def tok(x): return x.value() if hasattr(x, "value") else x
def isnode(x): return isinstance(x, list) and x and not isinstance(x[0], list)
def head(n): return tok(n[0]) if isnode(n) else None
def kids(n, name): return [c for c in n[1:] if isnode(c) and head(c) == name]
def kid(n, name):
    for c in n[1:]:
        if isnode(c) and head(c) == name: return c
    return None
def nums(n): return [float(v) for v in n[1:] if isinstance(v, (int, float))]

root = sexpdata.loads(open(sys.argv[1], encoding="utf-8").read())
rows = []
for fp in kids(root, "footprint"):
    at = nums(kid(fp, "at") or ["at"])
    ref = None
    for p in kids(fp, "property"):
        vals = [v for v in p[1:] if isinstance(v, str)]
        if vals and vals[0] == "Reference":
            ref = p; break
    if ref is None: continue
    refname = [v for v in ref[1:] if isinstance(v, str)][1] if len([v for v in ref[1:] if isinstance(v, str)]) > 1 else "?"
    rat = nums(kid(ref, "at") or ["at"])
    if len(rat) < 2: continue
    dx, dy = rat[0], rat[1]
    hidden = kid(ref, "hide") is not None or "hide" in [tok(v) for v in ref[1:] if not isinstance(v, (list, str, int, float))]
    # part extent from pads (local coords)
    ext = 0.0
    for pad in kids(fp, "pad"):
        pat = nums(kid(pad, "at") or ["at"])
        sz = nums(kid(pad, "size") or ["size"])
        if len(pat) >= 2 and len(sz) >= 2:
            ext = max(ext, math.hypot(abs(pat[0]) + sz[0] / 2, abs(pat[1]) + sz[1] / 2))
    d = math.hypot(dx, dy)
    rows.append({"ref": refname, "offset_mm": round(d, 3),
                 "part_extent_mm": round(ext, 3),
                 "beyond_extent_mm": round(d - ext, 3),
                 "hidden": bool(hidden),
                 "board_xy": [round(at[0], 2), round(at[1], 2)] if len(at) >= 2 else None})
vis = [r for r in rows if not r["hidden"]]
far = sorted([r for r in vis if r["beyond_extent_mm"] > 1.0],
             key=lambda r: -r["beyond_extent_mm"])
print(json.dumps({
    "footprints": len(rows), "visible_refdes": len(vis),
    "offset_max": max([r["offset_mm"] for r in vis], default=0),
    "offset_median": sorted([r["offset_mm"] for r in vis])[len(vis)//2] if vis else 0,
    "beyond_extent_over_1mm": len(far),
    "worst": far[:15],
}, indent=1))
