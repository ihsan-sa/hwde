"""measure.py - aspect study metric probe (bb-ldo P8 outline-aspect-not-earned).

Reports, for one .kicad_pcb, every number the study compares:
  outline w/h/area/aspect; F.Cu +3V3 pour area + island count + orphan area;
  check_thermal's own a_eff (reach disc R=sqrt(645/pi) about U1's PAD CENTROID,
  summed over layers, clamped at 645) with theta_JA and rise; and the P6
  "effective copper" discs r15/r20/r25 about the TAB (pad 4) centre.
Read-only. JSON to stdout or --out.
"""
import argparse, json, math, sys
from pathlib import Path

SCRIPTS = Path(r"C:/dev/ai-ee3/.claude/skills/ai-ee/scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
import geom  # noqa
from shapely.geometry import Point  # noqa
from shapely.ops import unary_union  # noqa

A_SAT = 645.0
REACH = (A_SAT / math.pi) ** 0.5
T0, TFLOOR, TAU = 174.0, 55.0, 350.0


def theta(a):
    return TFLOOR + (T0 - TFLOOR) * math.exp(-max(0.0, min(a, A_SAT)) / TAU)


def parts(g):
    if g.is_empty:
        return []
    return list(g.geoms) if g.geom_type.startswith("Multi") else [g]


def run(pcb, net="+3V3", ref="U1", tab="4", power=1.0, dt=65.0):
    bg = geom.load_board(pcb)
    minx, miny, maxx, maxy = bg.outline.bounds
    w, h = maxx - minx, maxy - miny
    pads = bg.pads_of(ref=ref)
    cx = sum(p.center[0] for p in pads) / len(pads)
    cy = sum(p.center[1] for p in pads) / len(pads)
    tabpad = [p for p in pads if p.number == tab][0]
    tx, ty = tabpad.center

    fcu = bg.net_copper(net, "F.Cu")
    isl = parts(fcu)
    tab_isl = [p for p in isl if p.buffer(1e-6).intersects(tabpad.poly)]
    tab_area = sum(p.area for p in tab_isl)
    orphan = sum(p.area for p in isl) - tab_area

    reach = Point(cx, cy).buffer(REACH, 256)
    a_eff = min(A_SAT, sum(bg.net_copper(net, L).intersection(reach).area
                           for L in bg.copper_layers))
    th = theta(a_eff)

    tabpt = Point(tx, ty)
    caps = {}
    for r in (15, 20, 25):
        d = tabpt.buffer(float(r), 256)
        caps[f"r{r}"] = round(fcu.intersection(d).area, 3)
        caps[f"r{r}_tabislands"] = round(
            unary_union(tab_isl).intersection(d).area if tab_isl else 0.0, 3)

    gnd = bg.net_copper("GND", "B.Cu")
    gnd_isl = parts(gnd)
    under_tab = gnd.intersection(tabpad.poly).area / max(tabpad.poly.area, 1e-9)

    return {
        "pcb": str(pcb),
        "outline": {"w": round(w, 3), "h": round(h, 3),
                    "area_mm2": round(bg.outline.area, 3),
                    "aspect": round(max(w, h) / min(w, h), 4),
                    "bbox": [round(v, 3) for v in bg.outline.bounds]},
        "pour_fcu": {"net": net, "area_mm2": round(fcu.area, 3),
                     "islands": len(isl),
                     "tab_island_mm2": round(tab_area, 3),
                     "orphan_mm2": round(orphan, 3)},
        "thermal_reach": {
            "_what": "check_thermal's own metric: R=%.3f mm disc about the pad "
                     "CENTROID, all layers, clamped at 645 mm2" % REACH,
            "centroid": [round(cx, 3), round(cy, 3)],
            "reach_mm": round(REACH, 4),
            "a_eff_mm2": round(a_eff, 4),
            "saturated": a_eff >= A_SAT - 1e-6,
            "theta_ja_c_per_w": round(th, 4),
            "rise_c": round(power * th, 4),
            "dt_allowed_c": dt,
            "margin_c": round(dt - power * th, 4)},
        "tab_discs": {"_what": "P6 metric: F.Cu +3V3 within r of the TAB centre",
                      "tab_center": [round(tx, 3), round(ty, 3)], **caps},
        "bcu_gnd": {"area_mm2": round(gnd.area, 3), "islands": len(gnd_isl),
                    "coverage_under_tab": round(under_tab, 4)},
        "tracks": len(bg.tracks_of()), "vias": len(bg.vias_of()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    d = run(Path(a.pcb))
    s = json.dumps(d, indent=1)
    if a.out:
        Path(a.out).write_text(s, encoding="utf-8")
    print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
