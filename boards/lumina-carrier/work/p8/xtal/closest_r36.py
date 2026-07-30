"""How close to U10's XO pin can a legal 0603 land actually get?

Searches the whole region north of U10 for legal R36 poses under the SAME
constraint set the placement used (exact pad/silk geometry, foreign copper of
every net except the three oscillator nets, courtyards, silk, board edge) and
reports the minimum R36-pad-1-to-U10-pad-31 distance. This is the measured
ceiling on target 2.
"""
import json
import math
import sys
from pathlib import Path

W = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\xtal")
sys.path.insert(0, str(W))
import opt_true as O  # noqa: E402

U10_XO = next(p for p in O.bg.pads_of(ref="U10") if p.number == "31")
U10_XI = next(p for p in O.bg.pads_of(ref="U10") if p.number == "30")

# wide window: the whole free area north of U10 plus its flanks
O.WX = (64.0, 90.0)
O.WY = (3.0, 16.5)
O.STEP = 0.25

rows = []
for ref, want_pad in (("R36", "1"), ("C31", "1")):
    feas = O.feasible(ref)
    best = None
    for xr, yr, deg in feas:
        pads, _ext, _silk = O.part_geo(ref, deg, xr, yr)
        pd = next(p for p in pads if p["n"] == want_pad)
        d = math.dist(pd["c"], U10_XO.center)
        dc = pd["poly"].distance(U10_XO.poly)
        if best is None or d < best[0]:
            best = (d, dc, xr, yr, deg)
    rows.append({"ref": ref, "pad": want_pad, "legal_poses": len(feas),
                 "min_centre_to_U10_31_mm": round(best[0], 4),
                 "min_copper_to_U10_31_mm": round(best[1], 4),
                 "at_rel": [best[2], best[3]], "deg": best[4]})
print(json.dumps({"note": "search window rel x[64,90] y[3,16.5], step 0.25, "
                          "same constraints as the applied placement",
                  "U10.31_XO_pad_centre_rel": [
                      round(U10_XO.center[0] - O.OX, 3),
                      round(U10_XO.center[1] - O.OY, 3)],
                  "results": rows}, indent=1))
