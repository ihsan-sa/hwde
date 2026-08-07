"""place_metrics - placement quality metrics + legality violations (S9, SPEC P6).

Read-only. Emits the S2 normalized-violation schema for placement LEGALITY
(courtyard overlaps, outline containment, declared-edge compliance, keepouts,
missing courtyards) plus decoupler DISTANCE violations (reusing S4
check_decoupling's association logic, filtered to kind=decoupler_distance -
loop/via inductance stays P8's job because it needs routing), and a `metrics`
facts block for the annealer/agent:

  metrics: {
    counts: {footprints, movable, nets},
    hpwl: {total_mm, by_net},                        # half-perimeter wirelength
    crossings: {count, pairs[:20]},                  # MST flight-line crossings
    crossings_signal: {count, pairs[:20]},           # gnd-class nets excluded
    congestion: {cell_mm, cols, rows, max, mean_nonzero, hotspots[:10]},
    congestion_signal_max: int,                      # gnd-class nets excluded
    decoupling: [check_association facts...],        # distances pre-route
    utilization: {component_mm2, board_mm2, ratio},
  }

The *_signal variants (T6 P6A-1) exclude gnd-class nets via
placelib.class_sets - the same partition the annealer optimizes with (gnd
rides planes and is never point-to-point routed), so they are the terms a
tuning loop should chase; the all-net fields stay for information.

constraints.json / decoupling.json default to the board's own directory (the
gate.py convention); pass --constraints/--decoupling to override. Exit 0 clean
/ 1 violations / 2 error. This is the P6 `place` gate's tool - the gate fails
on error-severity violations; the fast-route-completion gate term arrives with
S10/S11 route feedback.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))

import checklib  # noqa: E402
import geom  # noqa: E402
import placelib  # noqa: E402


def _sidecar(pcb: Path, explicit: str | None, name: str) -> Path | None:
    if explicit:
        return Path(explicit)
    cand = pcb.parent / name
    return cand if cand.is_file() else None


def collect(pcb: Path, constraints_path: Path | None,
            decoupling_path: Path | None, cell_mm: float):
    model = placelib.PlaceModel(pcb)
    constraints = (checklib.load_json(constraints_path, "constraints")
                   if constraints_path else {})
    placement = constraints.get("placement")
    meta = (checklib.load_json(decoupling_path, "decoupling metadata")
            if decoupling_path else {})

    violations = placelib.legality_violations(model, placement)
    decoupling_facts: list[dict] = []
    if decoupling_path:
        import check_decoupling
        bg = geom.load_board(pcb)
        for a in meta.get("associations", []):
            vs, facts = check_decoupling.check_association(bg, a)
            violations.extend(v for v in vs
                              if v.get("kind") == "decoupler_distance")
            if facts:
                decoupling_facts.append(facts)

    gnd = frozenset(placelib.class_sets(constraints, meta)[0])
    comp = sum(f.extents_abs().area for f in model.footprints.values()
               if f.is_movable)
    metrics = {
        "counts": {"footprints": len(model.footprints),
                   "movable": len(model.movable()),
                   "nets": len(model.nets_with_pads())},
        "hpwl": placelib.hpwl(model),
        "crossings": placelib.crossings(model),
        "crossings_signal": placelib.crossings(model, exclude=gnd),
        "congestion": placelib.congestion(model, cell_mm),
        "congestion_signal_max": placelib.congestion(model, cell_mm,
                                                     exclude=gnd)["max"],
        "decoupling": decoupling_facts,
        "utilization": {"component_mm2": checklib.rnd(comp),
                        "board_mm2": checklib.rnd(model.outline.area),
                        "ratio": checklib.rnd(
                            comp / model.outline.area, 3)
                        if model.outline.area else None},
    }
    return violations, metrics


def run(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--constraints", default=None,
                    help="constraints.json (default: next to the board)")
    ap.add_argument("--decoupling", default=None,
                    help="decoupling.json (default: next to the board)")
    ap.add_argument("--cell-mm", type=float, default=2.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    pcb = Path(args.pcb)
    if not pcb.is_file():
        raise checklib.CheckError(f"board not found: {pcb}")
    violations, metrics = collect(
        pcb,
        _sidecar(pcb, args.constraints, "constraints.json"),
        _sidecar(pcb, args.decoupling, "decoupling.json"),
        args.cell_mm)
    payload = checklib.report("place_metrics", str(pcb), violations,
                              metrics=metrics)
    return payload, args.out


def main(argv: list[str] | None = None) -> int:
    return checklib.cli_wrap("place_metrics", lambda: run(argv))


if __name__ == "__main__":
    sys.exit(main())
