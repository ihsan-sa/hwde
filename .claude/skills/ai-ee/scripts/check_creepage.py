"""check_creepage.py - same-layer clearance for high-voltage nets (SPEC 6.3, P8).

One concern: IPC-2221 electrical conductor spacing. For every net whose voltage
(from constraints.json) puts it more than 30 V away from another net, the
minimum same-layer copper-to-copper distance must meet the IPC-2221 Table 6-1
clearance for that voltage difference.

IPC-2221 Table 6-1 (verified 2026-07 against protoexpress / smpspowersupply /
ema-eda; PROGRESS S5). Voltage is DC or AC-PEAK, measured BETWEEN the two
conductors (differential). "Bare board" columns:
    band upper V : 15   30   50   100  150  170  250  300  500
    B2 external  : 0.10 0.10 0.60 0.60 0.60 1.25 1.25 1.25 2.50   (mm, uncoated)
    B1 internal  : 0.05 0.05 0.10 0.10 0.20 0.20 0.20 0.20 0.25
  V > 500: external 2.50 + 0.005*(V-500); internal 0.25 + 0.0025*(V-500).

The corpus carries no >30 V nets, so this check is clean on all goldens; supply
voltages via constraints.json to exercise it (a synthetic HV fixture is tested).

CLI: --pcb board.kicad_pcb --constraints constraints.json [--out report.json]
     exit 0/1/2 per SPEC section 6.

constraints.json voltages (either form):
    {"voltages": [{"net": "HV+", "voltage": 400}, {"net": "HV-", "voltage": 0}]}
Nets not listed are treated as 0 V (signal/ground reference). Only net pairs
whose voltage difference exceeds 30 V are checked.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import checklib  # noqa: E402
import geom  # noqa: E402
from checklib import CheckError, violation  # noqa: E402

SCRIPT = "check_creepage"
HV_THRESHOLD_V = 30.0          # IPC-2221 only regulates spacing above this
BAND_UPPER_V = [15, 30, 50, 100, 150, 170, 250, 300, 500]
CLEAR_EXTERNAL = [0.10, 0.10, 0.60, 0.60, 0.60, 1.25, 1.25, 1.25, 2.50]
CLEAR_INTERNAL = [0.05, 0.05, 0.10, 0.10, 0.20, 0.20, 0.20, 0.20, 0.25]


def clearance_mm(dv: float, outer: bool) -> float:
    """IPC-2221 minimum spacing for a `dv`-volt difference, outer/inner layer."""
    v = abs(dv)
    tbl = CLEAR_EXTERNAL if outer else CLEAR_INTERNAL
    for ub, val in zip(BAND_UPPER_V, tbl):
        if v <= ub:
            return val
    return (2.50 + 0.005 * (v - 500)) if outer else (0.25 + 0.0025 * (v - 500))


def voltage_map(cons: dict) -> dict[str, float]:
    vmap: dict[str, float] = {}
    for entry in cons.get("voltages", []):
        net = entry.get("net")
        if net is None or "voltage" not in entry:
            raise CheckError(f"voltages entry needs net+voltage: {entry}")
        vmap[net] = float(entry["voltage"])
    for entry in cons.get("nets", []):
        if entry.get("net") and "voltage" in entry:
            vmap[entry["net"]] = float(entry["voltage"])
    return vmap


def check_net(bg: geom.BoardGeom, hv: str, v_hv: float, vmap: dict):
    """Check the primary net `hv` against every other net that sits >30 V away.
    The violation is attributed to whichever net of the pair has the higher
    magnitude voltage (the one a fixer should move)."""
    if hv not in bg.nets:
        raise CheckError(f"voltage net {hv!r} not on board")
    violations: list[dict] = []
    checked = 0
    for other in sorted(bg.nets):
        if not other or other == hv:
            continue
        v_other = vmap.get(other, 0.0)
        dv = v_hv - v_other
        if abs(dv) <= HV_THRESHOLD_V:
            continue
        # own each pair once: the LISTED net with the larger |V| emits it
        # (tie -> larger name, per tuple compare). Unlisted nets (0 V) are never
        # owners, so a listed HV net always owns its pair with a signal/gnd net.
        if other in vmap and (abs(v_other), other) > (abs(v_hv), hv):
            continue
        prim, sec, v_prim = hv, other, v_hv
        for layer in bg.copper_layers:
            ca = bg.net_copper(hv, layer)
            cb = bg.net_copper(other, layer)
            if ca.is_empty or cb.is_empty:
                continue
            checked += 1
            req = clearance_mm(dv, bg.stackup.is_outer(layer))
            dist = ca.distance(cb)
            if dist + 1e-6 < req:
                p = ca.representative_point()
                violations.append(violation(
                    SCRIPT, "error", (p.x, p.y), layer, prim, [],
                    f"{prim} ({v_prim:.0f} V) to {sec} on {layer}: {dist:.3f} mm "
                    f"copper spacing < IPC-2221 {req:.2f} mm for {abs(dv):.0f} V",
                    SCRIPT, kind="creepage", other_net=sec,
                    delta_v=checklib.rnd(abs(dv)), spacing_mm=checklib.rnd(dist),
                    required_mm=req))
    return violations, {"net": hv, "voltage": v_hv, "pairs_checked": checked}


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="IPC-2221 same-layer clearance for >30 V net pairs.")
    ap.add_argument("--pcb", required=True, help="path to .kicad_pcb")
    ap.add_argument("--constraints", required=True,
                    help="constraints.json with a voltages list")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    cons = checklib.load_json(args.constraints, "constraints")
    vmap = voltage_map(cons)
    bg = geom.load_board(Path(args.pcb))
    bg.assert_fresh()

    violations: list[dict] = []
    checked: list[dict] = []
    skipped: list[str] = []
    for net, v in sorted(vmap.items()):
        # a listed voltage net absent from the board (renamed / not placed) is
        # skipped, not fatal - other nets still get checked. It is still honored
        # as the reference voltage for other nets that DO have copper nearby.
        if net not in bg.nets:
            skipped.append(net)
            continue
        vs, facts = check_net(bg, net, v, vmap)
        violations.extend(vs)
        if facts["pairs_checked"] or vs:
            checked.append(facts)

    payload = checklib.report(SCRIPT, args.pcb, violations, checked=checked,
                              skipped_absent_nets=skipped)
    return payload, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
