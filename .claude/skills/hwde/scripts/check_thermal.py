"""check_thermal.py - dissipation vs copper heatsink area (SPEC 6.3, P8).

One concern: a regulator / FET that dumps more heat than its copper can shed.
For each dissipating part named in constraints.json, estimate the junction-to-
ambient rise from the heatsink-net copper area and compare to the allowed rise.

Model (calibrated to datasheet anchors 2026-07; PROGRESS S5). theta_JA falls
off exponentially with copper pour area toward a floor:
    theta_JA(A) = theta_floor + (theta_0 - theta_floor) * exp(-A / tau)
    1 oz / 2-layer : theta_0=174, theta_floor=55, tau=350 mm^2
    2 oz / 4-layer : theta_0=140, theta_floor=45, tau=235 mm^2   (planes spread)
Rise ~= power_w * theta_JA(effective_area); a copper pour saturates near
~1 in^2 (645 mm^2), so past A_sat more copper barely helps - the fix there is
thermal vias to an inner/back plane, which the check flags separately. Every
number is +/-30%; this is a screen, not a sign-off (JEDEC JESD51 / TI SLOA122).

The corpus carries no thermal constraints, so this check is clean on all
goldens; supply parts via constraints.json to exercise it (a synthetic fixture
is tested).

CLI: --pcb board.kicad_pcb --constraints constraints.json [--out report.json]
     exit 0/1/2 per SPEC section 6.

constraints.json["thermal"] entries:
    {"ref": "U2",           # dissipating part refdes (its pads locate it)
     "power_w": 0.6,        # estimated dissipation
     "net": "GND",          # heatsink net (thermal-pad / tab net)
     "dt_c": 40,            # allowed junction-to-ambient rise (default 40)
     "min_vias": 9}         # optional explicit thermal-via floor
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
import geom  # noqa: E402
from checklib import CheckError, violation  # noqa: E402

SCRIPT = "check_thermal"
A_SAT_MM2 = 645.0             # ~1 in^2: copper pour saturates here
MODEL_2L = (174.0, 55.0, 350.0)   # theta_0, theta_floor, tau
MODEL_ML = (140.0, 45.0, 235.0)
DEFAULT_DT_C = 40.0
VIA_PITCH_MM = 1.1           # recommended thermal-via pitch
VIA_BENEFIT_CAP = 36         # array benefit flattens past ~36 vias
REACH_MM = (A_SAT_MM2 / math.pi) ** 0.5   # ~14.3 mm: heat spreads only so far


def theta_ja(area_mm2: float, multilayer: bool) -> float:
    t0, tfloor, tau = MODEL_ML if multilayer else MODEL_2L
    a = max(0.0, min(area_mm2, A_SAT_MM2))
    return tfloor + (t0 - tfloor) * math.exp(-a / tau)


def part_region(bg: geom.BoardGeom, ref: str):
    """(centroid, side_layer, footprint_area, pads) for a refdes."""
    pads = bg.pads_of(ref=ref)
    if not pads:
        raise CheckError(f"thermal part {ref!r} has no pads on board")
    cx = sum(p.center[0] for p in pads) / len(pads)
    cy = sum(p.center[1] for p in pads) / len(pads)
    side = "F.Cu" if sum("F.Cu" in p.layers for p in pads) >= \
        sum("B.Cu" in p.layers for p in pads) else "B.Cu"
    hull = geom._union([p.poly for p in pads]).convex_hull
    return (cx, cy), side, hull.area, pads


def check_part(bg: geom.BoardGeom, entry: dict):
    ref = entry.get("ref")
    net = entry.get("net")
    if not ref or not net or "power_w" not in entry:
        raise CheckError(f"thermal entry needs ref/net/power_w: {entry}")
    if net not in bg.nets:
        raise CheckError(f"thermal net {net!r} not on board")
    power = float(entry["power_w"])
    dt = float(entry.get("dt_c", DEFAULT_DT_C))
    (cx, cy), side, fp_area, _ = part_region(bg, ref)
    multilayer = len(bg.copper_layers) >= 4

    # heatsink copper = the net's copper WITHIN reach of the part (heat spreads
    # ~1 in radius; a distant pour of the same net elsewhere on the board is not
    # a heatsink for this part). Summed over layers because thermal vias tie the
    # part's pad to inner/back planes; capped where copper stops helping.
    reach = Point(cx, cy).buffer(REACH_MM)
    a_eff = min(A_SAT_MM2, sum(bg.net_copper(net, layer).intersection(reach).area
                               for layer in bg.copper_layers))
    theta = theta_ja(a_eff, multilayer)
    rise = power * theta

    # thermal vias of the net under the part (needed once copper saturates)
    region = Point(cx, cy).buffer(max(2.0, math.sqrt(fp_area / math.pi) + 1.5))
    vias = [v for v in bg.vias_of(net) if region.contains(Point(v.at))]
    # copper alone bottoms out at theta_ja(A_SAT) (the clamp), NOT the model's
    # asymptotic floor - if the target is below that, only vias/planes reach it.
    floor_cw = theta_ja(A_SAT_MM2, multilayer)
    need_vias = (dt / power) < floor_cw if power > 0 else False
    min_vias = int(entry.get("min_vias",
                             min(VIA_BENEFIT_CAP,
                                 max(4, math.ceil(fp_area / VIA_PITCH_MM ** 2)))))

    violations: list[dict] = []
    if rise > dt + 1e-6:
        saturated = a_eff >= A_SAT_MM2 - 1e-6
        remedy = ("add thermal vias to an inner/back plane" if saturated or
                  need_vias else f"grow the {net} pour")
        violations.append(violation(
            SCRIPT, "error", (cx, cy), side, net, [ref],
            f"{ref} dissipates {power:.2f} W into {a_eff:.0f} mm2 of {net} "
            f"copper: ~{rise:.0f} C rise (theta_JA ~{theta:.0f} C/W) "
            f"> {dt:.0f} C allowed; {remedy}", SCRIPT, kind="thermal_area",
            power_w=power, area_mm2=checklib.rnd(a_eff),
            theta_ja=checklib.rnd(theta), rise_c=checklib.rnd(rise),
            dt_allowed_c=dt))
    if need_vias and len(vias) < min_vias:
        violations.append(violation(
            SCRIPT, "warning", (cx, cy), side, net, [ref],
            f"{ref} ({power:.2f} W) needs a thermal-via array to {net} "
            f"(copper alone tops out ~{floor_cw:.0f} C/W); found {len(vias)} "
            f"via(s), want >= {min_vias}", SCRIPT, kind="thermal_vias",
            vias=len(vias), required=min_vias, power_w=power))

    facts = {"ref": ref, "net": net, "power_w": power,
             "area_mm2": checklib.rnd(a_eff), "theta_ja": checklib.rnd(theta),
             "rise_c": checklib.rnd(rise), "dt_allowed_c": dt,
             "vias_near_part": len(vias), "multilayer": multilayer}
    return violations, facts


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="Dissipation vs copper heatsink area (theta_JA screen).")
    ap.add_argument("--pcb", required=True, help="path to .kicad_pcb")
    ap.add_argument("--constraints", required=True,
                    help="constraints.json with a thermal list")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    cons = checklib.load_json(args.constraints, "constraints")
    bg = geom.load_board(Path(args.pcb))
    bg.assert_fresh()

    violations: list[dict] = []
    checked: list[dict] = []
    for entry in cons.get("thermal", []):
        vs, facts = check_part(bg, entry)
        violations.extend(vs)
        checked.append(facts)

    payload = checklib.report(SCRIPT, args.pcb, violations, checked=checked)
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
