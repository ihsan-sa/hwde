import json, math, sys
from pathlib import Path
W = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\xtal")
sys.path.insert(0, str(W))
import opt_true as O
U = {n: next(p for p in O.bg.pads_of(ref="U10") if p.number == n)
     for n in ("30", "31")}
O.WX, O.WY, O.STEP = (64.0, 90.0), (3.0, 16.5), 0.25
feas = O.feasible("Y10")
best = None
for xr, yr, deg in feas:
    pads, _e, _s = O.part_geo("Y10", deg, xr, yr)
    p1 = next(p for p in pads if p["n"] == "1")   # XI
    p3 = next(p for p in pads if p["n"] == "3")   # XO_XTAL
    d = math.dist(p1["c"], U["30"].center) + math.dist(p3["c"], U["31"].center)
    if best is None or d < best[0]:
        best = (d, round(math.dist(p1["c"], U["30"].center), 4),
                round(math.dist(p3["c"], U["31"].center), 4), xr, yr, deg)
print(json.dumps({"Y10_legal_poses": len(feas),
                  "min_sum_XI+XO_XTAL_mm": round(best[0], 4),
                  "Y10.1_to_U10.30_mm": best[1],
                  "Y10.3_to_U10.31_mm": best[2],
                  "at_rel": [best[3], best[4]], "deg": best[5]}, indent=1))
