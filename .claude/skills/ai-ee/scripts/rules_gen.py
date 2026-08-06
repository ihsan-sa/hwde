#!/usr/bin/env python
"""rules_gen.py - constraints.json -> KiCad custom design rules + net classes (SPEC P5).

KiCad custom DRC rules (`.kicad_dru`) are the enforcement backbone: anything
expressible as a rule becomes a named DRC violation, so the standard DRC gate
(gate.py drc) carries it for free. This script emits:

  1. A `<board>.kicad_dru` = fab-floor BASELINE (from reference/jlc_capabilities.yaml
     for the board's layer count / copper weight) + DESIGN rules from constraints:
       - power nets  -> minimum track width (IPC-2152 via check_current) per net
       - diff pairs  -> diff_pair_gap rule + differential width (impedance.py + stackup)
     Baseline rules are emitted FIRST and per-net rules LAST: when two rules of the
     same constraint type match one item, the LATER rule wins (LEARNINGS [drc]), so
     the specific per-net rule overrides the generic floor.
  2. (optional, --pro) net classes written into `<board>.kicad_pro` net_settings:
     ONE POWER CLASS PER REQUIRED WIDTH (never one class at the widest - that put
     pd-trigger's 20 mA /VDD in the same 1.75 mm class as its 5 A VBUS and would
     have had Freerouting drive 1.75 mm traces into 0.6 mm pads; LEARNINGS
     2026-07-28 [routing][rules_gen][freerouting]) and one class per differential
     impedance, assigned by netclass_patterns; plus board.design_settings.rules
     minimums and the fab-floor severities from lib/fabfloors.py - the same single
     source board_init writes, so the two files cannot disagree. These drive the
     router (S11) and placement; DRU is the DRC enforcer.

Conditions use `A.NetName == 'NET'` (NOT `A.Net`, which silently matches nothing -
LEARNINGS [drc]). kicad-cli auto-loads the .kicad_dru sitting next to the board.

I/O: SPEC section 6 - argparse, JSON to stdout or --out, exit 0/1/2, no interactivity.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import traceback
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import check_current  # noqa: E402  (required_width_mm)
import fabfloors  # noqa: E402  (the single source of fab minimums)
import impedance as imp  # noqa: E402

REFERENCE = SCRIPTS.parent / "reference"
CAP_FILE = REFERENCE / "jlc_capabilities.yaml"
STACKUP_FILE = REFERENCE / "stackups.yaml"

# Copper finished thickness (mm) by weight, for IPC-2152 width scaling.
CU_OZ_MM = {1.0: 0.035, 0.5: 0.0175, 2.0: 0.070}


# --------------------------------------------------------------- reference data

def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# capability lookup lives in lib/fabfloors.py (board_init uses the same one)
capability_class = fabfloors.capability_class


# --------------------------------------------------------------- DRU rules

class Rule:
    """One .kicad_dru rule."""
    def __init__(self, name: str, constraint: str, minv: float | None = None,
                 condition: str | None = None, layer: str | None = None,
                 severity: str | None = None, extra: str | None = None):
        self.name = name
        self.constraint = constraint
        self.minv = minv
        self.condition = condition
        self.layer = layer
        self.severity = severity
        self.extra = extra

    def render(self) -> str:
        lines = [f'(rule "{self.name}"']
        if self.severity:
            lines.append(f'\t(severity {self.severity})')
        if self.layer:
            lines.append(f'\t(layer {self.layer})')
        if self.minv is not None:
            lines.append(f'\t(constraint {self.constraint} (min {self.minv:.4f}mm))')
        elif self.extra is not None:
            lines.append(f'\t(constraint {self.constraint} {self.extra})')
        else:
            lines.append(f'\t(constraint {self.constraint})')
        if self.condition:
            lines.append(f'\t(condition "{self.condition}")')
        lines.append(')')
        return "\n".join(lines)


def baseline_rules(cap: dict) -> list[Rule]:
    """Fab-floor rules from a jlc_capabilities.yaml design-rule row."""
    r: list[Rule] = []
    r.append(Rule("aiee_track_width_floor", "track_width", cap["min_trace_width_mm"],
                  condition="A.Type == 'track'"))
    r.append(Rule("aiee_clearance_floor", "clearance", cap["min_clearance_mm"]))
    r.append(Rule("aiee_via_drill_floor", "hole_size", cap["min_via_drill_mm"],
                  condition="A.Type == 'via'"))
    r.append(Rule("aiee_via_diameter_floor", "via_diameter", cap["min_via_diameter_mm"],
                  condition="A.Type == 'via'"))
    r.append(Rule("aiee_annular_floor", "annular_width", cap["min_annular_ring_mm"],
                  condition="A.Type == 'via'"))
    r.append(Rule("aiee_edge_clearance_floor", "edge_clearance", cap["min_copper_to_edge_mm"]))
    r.append(Rule("aiee_hole_to_hole_floor", "hole_to_hole", cap["min_hole_to_hole_mm"]))
    r.append(Rule("aiee_silk_width_floor", "text_thickness", cap["min_silk_width_mm"],
                  condition="A.Type == 'text' && (A.Layer == 'F.Silkscreen' || A.Layer == 'B.Silkscreen')"))
    return r


def power_rules(constraints: dict, cu_mm: float) -> tuple[list[Rule], list[dict]]:
    """Per-power-net minimum track width from IPC-2152 (check_current)."""
    rules: list[Rule] = []
    facts: list[dict] = []
    for entry in constraints.get("power", []):
        net = entry["net"]
        cur = float(entry["current_a"])
        dt = float(entry.get("dt_c", 10.0))
        w = check_current.required_width_mm(cur, dt, cu_mm)
        safe = re.sub(r"[^A-Za-z0-9]", "_", net).strip("_")
        rules.append(Rule(f"aiee_pwr_width_{safe}", "track_width", round(w, 4),
                          condition=f"A.NetName == '{net}' && A.Type == 'track'"))
        facts.append({"net": net, "current_a": cur, "dt_c": dt,
                      "min_width_mm": round(w, 4)})
    return rules, facts


DIFF_SUFFIXES = [("_P", "_N"), ("_DP", "_DM"), ("+", "-"), ("_H", "_L")]


def detect_diff_pairs(constraints: dict) -> list[dict]:
    """Pair high_speed nets by name suffix. Returns [{p, n, base, impedance_ohm}]."""
    nets = [e["net"] for e in constraints.get("high_speed", [])]
    imp_of = {e["net"]: e.get("impedance_ohm") for e in constraints.get("high_speed", [])}
    pairs: list[dict] = []
    used: set[str] = set()
    # explicit diff_pairs section wins
    for dp in constraints.get("diff_pairs", []):
        pairs.append({"p": dp["p"], "n": dp["n"], "base": dp.get("base", dp["p"]),
                      "impedance_ohm": dp.get("impedance_ohm", 90)})
        used.update([dp["p"], dp["n"]])
    for net in nets:
        if net in used:
            continue
        for pa, nb in DIFF_SUFFIXES:
            if net.endswith(pa):
                base = net[:-len(pa)]
                mate = base + nb
                if mate in nets and mate not in used:
                    z = imp_of.get(net) or imp_of.get(mate)
                    if z is None:
                        z = 90 if "USB" in base.upper() else 100
                    pairs.append({"p": net, "n": mate, "base": base,
                                  "impedance_ohm": int(z)})
                    used.update([net, mate])
                break
    return pairs


def diff_pair_rules(pairs: list[dict], stackup: dict) -> tuple[list[Rule], list[dict]]:
    """diff_pair_gap rule + computed width/gap per pair (impedance.py)."""
    rules: list[Rule] = []
    facts: list[dict] = []
    # outer microstrip: dielectric gap to the nearest inner plane + its er
    h, er, cu_oz = outer_microstrip_params(stackup)
    for dp in pairs:
        w, gap = imp.diff_pair(float(dp["impedance_ohm"]), h,
                               imp.CU_OZ_MM.get(cu_oz, 0.035), er)
        safe = re.sub(r"[^A-Za-z0-9]", "_", dp["base"]).strip("_")
        # gap floor: a differential gap smaller than this is a skew/coupling defect
        rules.append(Rule(
            f"aiee_diff_gap_{safe}", "diff_pair_gap", round(gap, 4),
            condition=(f"A.NetName == '{dp['p']}' || A.NetName == '{dp['n']}'")))
        facts.append({"pair": [dp["p"], dp["n"]], "impedance_ohm": dp["impedance_ohm"],
                      "width_mm": w, "gap_mm": gap})
    return rules, facts


def outer_microstrip_params(stackup: dict) -> tuple[float, float, float]:
    """(h, epsilon_r, outer_copper_oz) for outer-layer microstrip from a stackup.

    h = thickness of the dielectric between the outer copper and the next
    (reference) copper; er = its epsilon_r; oz = outer copper weight.
    """
    stack = stackup["stack"]
    outer_oz = stack[0].get("copper_oz", 1.0)
    # first dielectric after the top copper
    for layer in stack[1:]:
        if layer["type"] != "copper":
            return float(layer["thickness_mm"]), float(layer.get("epsilon_r", 4.5)), outer_oz
    return 0.2104, 4.05, outer_oz  # fallback (should not happen for >=2 copper)


# --------------------------------------------------------------- net classes

def power_class_name(width_mm: float) -> str:
    """Class name for a power width: 1.75 -> 'Pwr_1p75mm'."""
    return "Pwr_%smm" % ("%g" % round(width_mm, 4)).replace(".", "p")


def net_classes(constraints: dict, power_facts: list[dict],
                diff_facts: list[dict], cap: dict) -> tuple[list[dict], list[dict]]:
    """Build net_settings classes + netclass_patterns for the .kicad_pro.

    Power nets are bucketed BY THEIR OWN required width (one class per
    distinct width); a net whose IPC-2152 width is at or under the Default
    class width simply joins Default. Flattening every power net into one
    class at the widest width is a routing defect, not a conservatism: the
    netclass width is what the DSN export hands Freerouting, so a 20 mA rail
    inherited the 5 A trunk's 1.75 mm and could not enter its own pads.
    """
    classes: list[dict] = []
    patterns: list[dict] = []

    def base_class(name: str, track: float, clearance: float,
                   dpw: float = 0.2, dpg: float = 0.25) -> dict:
        return {
            "name": name, "clearance": round(clearance, 4), "track_width": round(track, 4),
            "via_diameter": cap["min_via_diameter_mm"], "via_drill": cap["min_via_drill_mm"],
            "diff_pair_width": round(dpw, 4), "diff_pair_gap": round(dpg, 4),
            "diff_pair_via_gap": round(dpg, 4),
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "line_style": 0,
            "bus_width": 12, "wire_width": 6,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
        }

    default_track = default_class(cap)["track_width"]
    buckets: dict[float, list[dict]] = {}
    for f in power_facts:
        w = round(max(float(f["min_width_mm"]), default_track), 4)
        buckets.setdefault(w, []).append(f)
    for w in sorted(buckets):
        if w <= default_track + 1e-9:
            cname = "Default"          # thin rails need no wider class
        else:
            cname = power_class_name(w)
            classes.append(base_class(cname, w, max(cap["min_clearance_mm"], 0.2)))
        for f in buckets[w]:
            f["netclass"] = cname       # traceability in the JSON report
            f["class_width_mm"] = w
            patterns.append({"netclass": cname, "pattern": f["net"]})
    for f in diff_facts:
        cname = f"Diff{f['impedance_ohm']}"
        if not any(c["name"] == cname for c in classes):
            classes.append(base_class(cname, f["width_mm"], cap["min_clearance_mm"],
                                      dpw=f["width_mm"], dpg=f["gap_mm"]))
        for n in f["pair"]:
            patterns.append({"netclass": cname, "pattern": n})
    return classes, patterns


def default_class(cap: dict) -> dict:
    return {
        "name": "Default", "clearance": cap["min_clearance_mm"],
        "track_width": max(cap["min_trace_width_mm"], 0.2),
        "via_diameter": cap["min_via_diameter_mm"], "via_drill": cap["min_via_drill_mm"],
        "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
        "microvia_diameter": 0.3, "microvia_drill": 0.1, "line_style": 0,
        "bus_width": 12, "wire_width": 6,
        "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
    }


def update_pro(pro_path: Path, classes: list[dict], patterns: list[dict],
               cap: dict) -> None:
    """Read-modify-write the .kicad_pro: net_settings + design-rule minimums.

    Keeps the rest of the (minimal, hand-rolled) pro intact - only touches
    net_settings, board.design_settings.rules and the fab-floor severities
    (LEARNINGS [kicad]: a minimal pro is the DRC authority; do not paste a
    full default blob). Floors + severities come from lib/fabfloors.py, the
    same source board_init writes, and are asserted after the merge."""
    pro = json.loads(pro_path.read_text(encoding="utf-8")) if pro_path.exists() else {}
    all_classes = [default_class(cap)] + classes
    pro["net_settings"] = {
        "classes": all_classes,
        "meta": {"version": 3},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": patterns,
    }
    board = pro.setdefault("board", {})
    ds = board.setdefault("design_settings", {})
    ds["rules"] = {**(ds.get("rules") or {}), **fabfloors.pro_rules(cap)}
    ds["rule_severities"] = {**(ds.get("rule_severities") or {}),
                             **fabfloors.pro_rule_severities()}
    bad = fabfloors.check_pro(pro, cap)
    if bad:
        raise RuntimeError("project file would ship sub-fab floors: "
                           + "; ".join(bad))
    pro_path.write_text(json.dumps(pro, indent=2), encoding="utf-8")


# --------------------------------------------------------------- render / main

DRU_HEADER = ("(version 1)\n"
              "# Generated by ai-ee rules_gen.py from constraints + jlc_capabilities.\n"
              "# Baseline (fab floor) first, per-net design rules last (later rule wins).\n")


def render_dru(rules: list[Rule]) -> str:
    return DRU_HEADER + "\n".join(r.render() for r in rules) + "\n"


def build(constraints: dict, cap: dict, stackup: dict, baseline_only: bool
          ) -> tuple[list[Rule], dict]:
    outer_oz = cap.get("outer_copper_oz", 1.0)
    cu_mm = CU_OZ_MM.get(outer_oz, 0.035)
    rules = baseline_rules(cap)
    report: dict = {"power": [], "diff_pairs": [], "classes": [], "patterns": []}
    if not baseline_only:
        pr, pf = power_rules(constraints, cu_mm)
        pairs = detect_diff_pairs(constraints)
        dr, df = diff_pair_rules(pairs, stackup)
        rules += pr + dr
        classes, patterns = net_classes(constraints, pf, df, cap)
        report["power"] = pf
        report["diff_pairs"] = df
        report["classes"] = classes
        report["patterns"] = patterns
    return rules, report


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--constraints", help="constraints.json (high_speed/power/diff_pairs)")
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--copper-oz", type=float, default=1.0,
                    help="outer copper weight (default 1.0)")
    ap.add_argument("--stackup", help="stackup name from stackups.yaml "
                    "(default: defaults[<layers>])")
    ap.add_argument("--out-dru", help="write the .kicad_dru here")
    ap.add_argument("--pro", help="also update this .kicad_pro (net classes + minimums)")
    ap.add_argument("--baseline-only", action="store_true",
                    help="emit only the fab-floor baseline (for template generation)")
    ap.add_argument("--out", help="write the JSON report here instead of stdout")
    args = ap.parse_args(argv)

    try:
        try:
            cls, cap = fabfloors.profile(args.layers, args.copper_oz)
        except fabfloors.FabFloorError as exc:
            raise SystemExit(str(exc)) from exc

        stacks = load_yaml(STACKUP_FILE)
        stk_name = args.stackup or stacks["defaults"].get(args.layers)
        stackup = stacks["stackups"].get(stk_name) if stk_name else None
        if stackup is not None and stackup.get("available") is False \
                and not args.baseline_only:
            ret = stackup.get("retired") or {}
            raise SystemExit(
                f"stackup {stk_name} is marked available: false in "
                f"stackups.yaml - {ret.get('reason', 'not offered by JLC')}; "
                f"use one of: {', '.join(ret.get('replacements') or []) or 'see stackups.yaml'}")
        if stackup is None and not args.baseline_only:
            # only needed for diff pairs; fall back to the first AVAILABLE
            # stackup with a matching layer count, else the first available
            stackup = next(
                (s for s in stacks["stackups"].values()
                 if s.get("available") is not False
                 and s.get("layers") == args.layers),
                next(s for s in stacks["stackups"].values()
                     if s.get("available") is not False))

        constraints = {}
        if args.constraints:
            constraints = json.loads(Path(args.constraints).read_text(encoding="utf-8"))

        rules, report = build(constraints, cap, stackup or {}, args.baseline_only)
        dru_text = render_dru(rules)

        if args.out_dru:
            Path(args.out_dru).write_text(dru_text, encoding="utf-8")
        if args.pro and not args.baseline_only:
            update_pro(Path(args.pro), report["classes"], report["patterns"], cap)

        result = {
            "script": "rules_gen", "status": "pass",
            "capability_class": cls, "stackup": stk_name,
            "rule_count": len(rules),
            "rule_names": [r.name for r in rules],
            "power": report["power"], "diff_pairs": report["diff_pairs"],
            "classes": [c["name"] for c in report["classes"]],
            "out_dru": args.out_dru, "pro": args.pro if not args.baseline_only else None,
        }
        if not args.out_dru:
            result["dru"] = dru_text
        out = json.dumps(result, indent=2)
        if args.out:
            Path(args.out).write_text(out, encoding="utf-8")
        else:
            print(out)
        return 0
    except SystemExit as e:
        print(json.dumps({"script": "rules_gen", "status": "error", "error": str(e)}))
        return 2
    except Exception:
        print(json.dumps({"script": "rules_gen", "status": "error",
                          "error": traceback.format_exc()}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
