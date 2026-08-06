#!/usr/bin/env python
"""board_init.py - initialize a .kicad_pcb from a netlist (SPEC P5).

board-setup phase, script-driven: create the board, import the netlist
(footprints + net assignments), set the stackup from stackups.yaml, draw a
provisional outline and mounting holes. Placement proper is P6 - board_init
just spreads parts legally (no courtyard overlaps) so DRC setup is clean.

kicad-cli has NO netlist->board path, so the import runs under KiCad's bundled
python via lib/board_swig.py (the only interpreter with pcbnew), mirroring the
corpus builder. The venv driver here parses the netlist (sexpdata), picks the
stackup, drives the worker, injects the (stackup) block as text (SWIG can't
serialize it - LEARNINGS [swig]), writes a minimal .kicad_pro, and self-checks.

The .kicad_pro's design-rule minimums come from the selected JLC capability
profile via lib/fabfloors.py - never from a hard-coded default - and the
checks that enforce them are pinned to severity ERROR. Two shipped boards
proved why: a hard-coded `min_track_width: 0.1` (below EVERY JLC profile)
plus KiCad's default `min_hole_to_hole: 0.25` at *warning* let 189 unbuildable
traces and two sub-fab drill pairs pass `drc_routed` 0/0 and only surface at
the P9 DFM gate (LEARNINGS [board_init][rules_gen][dfm][gates]).

Self-check acceptance (SPEC S8): schematic parity == 0 (every part+net imported
correctly) AND zero setup DRC violations, EXCLUDING unconnected_items (the board
is unrouted by design), AND the written project's floors >= the fab profile.
Emits the normalized DRC report alongside.

Usage:
  board_init.py --netlist n.net --name board --out dir --layers 4
                [--copper-oz 1] [--stackup NAME]
                [--outline auto|WxH] [--mounting-holes N]
                [--corner-radius R] [--cutout X,Y,W,H ...]
                [--schematic s.kicad_sch]   # copy next to board -> enables parity
                [--fp-lib DIR ...] [--out-report r.json]

I/O: SPEC section 6 - argparse, JSON to stdout or --out-report, exit 0/1/2.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

import sexpdata
import yaml

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
from lib import env  # noqa: E402
from lib import fabfloors  # noqa: E402
import kc  # noqa: E402

REFERENCE = SCRIPTS.parent / "reference"
STACKUP_FILE = REFERENCE / "stackups.yaml"
WORKER = SCRIPTS / "lib" / "board_swig.py"


# --------------------------------------------------------------- netlist parse

def _sym(x):
    return x.value() if isinstance(x, sexpdata.Symbol) else x


def _head(node):
    return _sym(node[0]) if isinstance(node, list) and node else None


def _find(node, name):
    return [c for c in node if isinstance(c, list) and _head(c) == name]


def _find1(node, name):
    r = _find(node, name)
    return r[0] if r else None


# Symbol fields KiCad's footprint/symbol field parity handles natively (or
# exempts); everything else (LCSC, MPN, ...) must be copied onto the footprint
# or `drc --schematic-parity` warns footprint_symbol_field_mismatch per part.
_NATIVE_FIELDS = {"Reference", "Value", "Footprint", "Datasheet", "Description"}


def _comp_fields(comp) -> dict[str, str]:
    """Custom symbol fields of a netlist (comp ...): {name: value}."""
    fields: dict[str, str] = {}
    fnode = _find1(comp, "fields")
    if fnode:
        for f in _find(fnode, "field"):
            nnode = _find1(f, "name")
            name = _sym(nnode[1]) if nnode and len(nnode) > 1 else None
            value = _sym(f[-1]) if len(f) > 2 else ""
            if name and name not in _NATIVE_FIELDS:
                fields[name] = value
    return fields


def parse_netlist(path: Path) -> tuple[list[dict], dict]:
    """kicadsexpr netlist -> ([{ref, value, fp, fields}], {"REF.PAD": net})."""
    data = sexpdata.loads(path.read_text(encoding="utf-8"))
    components: list[dict] = []
    netmap: dict[str, str] = {}
    for section in data[1:]:
        if _head(section) == "components":
            for comp in _find(section, "comp"):
                ref = _sym(_find1(comp, "ref")[1])
                vnode = _find1(comp, "value")
                value = _sym(vnode[1]) if vnode and len(vnode) > 1 else ""
                fnode = _find1(comp, "footprint")
                fp = _sym(fnode[1]) if fnode and len(fnode) > 1 else None
                components.append({"ref": ref, "value": value, "fp": fp,
                                   "fields": _comp_fields(comp)})
        elif _head(section) == "nets":
            for net in _find(section, "net"):
                nm = _sym(_find1(net, "name")[1])
                for node in _find(net, "node"):
                    r = _sym(_find1(node, "ref")[1])
                    p = _sym(_find1(node, "pin")[1])
                    netmap[f"{r}.{p}"] = nm
    missing = [c["ref"] for c in components if not c["fp"]]
    if missing:
        raise ValueError(f"netlist components without a footprint: {missing}")
    return components, netmap


# --------------------------------------------------------------- stackup block

def build_stackup_block(stackup: dict) -> str:
    """(stackup ...) s-expr text from a stackups.yaml entry, geom-parseable."""
    lines = ["\t\t(stackup",
             '\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))',
             '\t\t\t(layer "F.Paste" (type "Top Solder Paste"))',
             '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))']
    for ly in stackup["stack"]:
        if ly["type"] == "copper":
            lines.append(f'\t\t\t(layer "{ly["name"]}" (type "copper") '
                         f'(thickness {ly["thickness_mm"]}))')
        else:
            mat = ly.get("material", "FR4")
            er = ly.get("epsilon_r", 4.5)
            lt = ly.get("loss_tangent", 0.02)
            lines.append(
                f'\t\t\t(layer "{ly["name"]}" (type "{ly["type"]}") '
                f'(thickness {ly["thickness_mm"]}) (material "{mat}") '
                f'(epsilon_r {er}) (loss_tangent {lt}))')
    lines.append('\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))')
    lines.append('\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))')
    lines.append(f'\t\t\t(copper_finish "{stackup.get("copper_finish", "HASL")}")')
    dc = "yes" if stackup.get("dielectric_constraints") else "no"
    lines.append(f'\t\t\t(dielectric_constraints {dc})')
    lines.append("\t\t)")
    return "\n".join(lines) + "\n"


def inject_stackup(pcb_path: Path, stackup: dict) -> None:
    """Insert the (stackup) block into (setup ...) and set (general thickness)."""
    t = pcb_path.read_text(encoding="utf-8")
    if "(stackup" not in t:
        m = re.search(r"\(setup\n", t)
        if not m:
            raise RuntimeError("no (setup block in board to inject stackup")
        block = build_stackup_block(stackup)
        t = t[:m.end()] + block + t[m.end():]
    # set board thickness to the stackup total
    thick = stackup.get("thickness_mm", 1.6)
    t2 = re.sub(r"\(thickness [\d.]+\)", f"(thickness {thick})", t, count=1)
    if t2 == t and "(general" in t:
        t2 = re.sub(r"(\(general\n)", rf"\1\t\t(thickness {thick})\n", t, count=1)
    pcb_path.write_text(t2, encoding="utf-8")


# --------------------------------------------------------------- project file

def build_pro(pro_name: str, cap: dict) -> dict:
    """Minimal, hand-rolled .kicad_pro (LEARNINGS [kicad]: minimal pro is the
    DRC authority; suppress library-mismatch noise for imported footprints).

    Design-rule minimums and the severities that enforce them come from the
    capability profile (lib/fabfloors.py) - the single source rules_gen
    --pro writes too, so the two can never disagree."""
    severities = {"lib_footprint_issues": "ignore",
                  "lib_footprint_mismatch": "ignore"}
    severities.update(fabfloors.pro_rule_severities())
    return {
        "board": {"design_settings": {
            "rule_severities": severities,
            "rules": fabfloors.pro_rules(cap)}},
        "erc": {"rule_severities": {"lib_symbol_issues": "ignore",
                                    "lib_symbol_mismatch": "ignore",
                                    "footprint_link_issues": "ignore"}},
        "meta": {"filename": pro_name, "version": 3},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    }


def write_pro(pro_path: Path, cap: dict) -> dict:
    """Write the project file and return the floors it carries. Raises if
    what was written does not satisfy the profile (a regression guard on
    build_pro itself, and the standing P7-entry assertion in library form)."""
    pro = build_pro(pro_path.name, cap)
    bad = fabfloors.check_pro(pro, cap)
    if bad:
        raise RuntimeError("project file would ship sub-fab floors: "
                           + "; ".join(bad))
    pro_path.write_text(json.dumps(pro, indent=2), encoding="utf-8")
    return pro["board"]["design_settings"]["rules"]


# --------------------------------------------------------------- self check

SETUP_IGNORE_SOURCES = {"unconnected"}  # unrouted board -> unconnected expected


# Silk checks that a CROSS-footprint pair can trip purely because of the
# temporary shelf packing (refdes text of one part vs a neighbour). Placement
# (P6) re-positions everything, and P7's drc_routed gate re-checks silk at the
# final positions - so these are reported as transient, not init failures.
# A SINGLE-footprint silk violation (own silk over own pad) is a library
# defect and still fails (S14 finding: easyeda2kicad ships such footprints).
_TRANSIENT_SILK_CHECKS = {"silk_overlap", "silk_over_copper"}


def _is_transient_silk(v: dict) -> bool:
    # silk vs the fixed BOARD EDGE at temporary shelf positions is purely
    # positional (single-item by nature) - placement re-seats everything.
    if v.get("check") == "silk_edge_clearance":
        return True
    return (v.get("check") in _TRANSIENT_SILK_CHECKS
            and len(set(v.get("refs") or [])) >= 2)


def self_check(cli: Path, pcb: Path, has_sch: bool) -> dict:
    report = kc.run_drc(cli, pcb, parity=has_sch)
    setup_all = [v for v in report["violations"]
                 if v["source"] not in SETUP_IGNORE_SOURCES]
    transient = [v for v in setup_all if _is_transient_silk(v)]
    setup = [v for v in setup_all if not _is_transient_silk(v)]
    parity = [v for v in report["violations"] if v["source"] == "parity"]
    unconnected = [v for v in report["violations"] if v["source"] == "unconnected"]
    return {
        "drc": report["counts"],
        "setup_violations": setup,
        "transient_silk": transient,
        "parity_count": len(parity),
        "unconnected_count": len(unconnected),
        "clean": len(setup) == 0,
    }


# --------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--netlist", required=True)
    ap.add_argument("--name", required=True, help="board basename")
    ap.add_argument("--out", required=True, help="output directory (workspace/kicad)")
    ap.add_argument("--layers", type=int, default=4, choices=[2, 4])
    ap.add_argument("--copper-oz", type=float,
                    help="outer copper weight, selects the jlc_capabilities "
                         "profile whose minimums are written into the "
                         ".kicad_pro (default: the stackup's own outer copper)")
    ap.add_argument("--stackup", help="stackup name (default: stackups.defaults[layers])")
    ap.add_argument("--outline", default="auto",
                    help="'auto' (bbox+margin) or 'WxH' in mm, e.g. 60x40")
    ap.add_argument("--margin", type=float, default=6.0)
    ap.add_argument("--corner-radius", type=float, default=0.0,
                    help="round the outline corners by this radius in mm "
                         "(0 = square corners; clamped to half the shorter side)")
    ap.add_argument("--cutout", action="append", default=[], metavar="X,Y,W,H",
                    help="rectangular edge notch in mm, relative to the "
                         "outline's top-left corner; repeatable. MUST touch an "
                         "outline edge and must not overlap a corner radius. "
                         "Interior windows are rejected (they mis-parse as the "
                         "board outline downstream).")
    ap.add_argument("--mounting-holes", type=int, default=0,
                    help="corner mounting holes (0..4)")
    ap.add_argument("--schematic", help="copy this .kicad_sch next to the board "
                    "so the self-check can run schematic parity")
    ap.add_argument("--fp-lib", action="append", default=[],
                    help="extra footprint library parent dir (repeatable)")
    ap.add_argument("--out-report", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    try:
        cli = env.find_kicad_cli()
        if cli is None:
            raise RuntimeError("kicad-cli not found (see check_env.py)")
        bp = env.find_kicad_python(cli)
        if bp is None:
            raise RuntimeError("bundled python (pcbnew) not found")

        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        pcb_path = out_dir / f"{args.name}.kicad_pcb"

        components, netmap = parse_netlist(Path(args.netlist))

        stacks = yaml.safe_load(STACKUP_FILE.read_text(encoding="utf-8"))
        stk_name = args.stackup or stacks["defaults"].get(args.layers)
        stackup = stacks["stackups"].get(stk_name)
        if stackup is None:
            raise RuntimeError(f"stackup {stk_name!r} not in stackups.yaml")
        if stackup["layers"] != args.layers:
            raise RuntimeError(f"stackup {stk_name} is {stackup['layers']}-layer, "
                               f"--layers {args.layers}")
        if stackup.get("available") is False:
            # A stackup JLC does not sell must never size a design: the
            # phantom JLC04161H-3313 is why lumina-carrier's 100R MDI was
            # solved against a lamination nobody can build (LEARNINGS
            # 2026-07-30 [stackup][ordering]).
            ret = stackup.get("retired") or {}
            raise RuntimeError(
                f"stackup {stk_name} is marked available: false in "
                f"stackups.yaml - {ret.get('reason', 'not offered by JLC')}. "
                f"Use one of: {', '.join(ret.get('replacements') or []) or 'see stackups.yaml'}")

        # Fab floors come from the capability profile for (layers, outer
        # copper), never from a hard-coded default.
        outer_oz = args.copper_oz
        if outer_oz is None:
            coppers = [ly for ly in stackup["stack"] if ly["type"] == "copper"]
            outer_oz = float(coppers[0].get("copper_oz", 1.0)) if coppers else 1.0
        cap_class, cap = fabfloors.profile(args.layers, outer_oz)

        outline = {"mode": "auto"}
        if args.outline != "auto":
            m = re.fullmatch(r"([\d.]+)x([\d.]+)", args.outline)
            if not m:
                raise RuntimeError(f"bad --outline {args.outline!r} (use auto or WxH)")
            outline = {"mode": "fixed", "w": float(m.group(1)), "h": float(m.group(2))}

        cutouts = []
        for spec in args.cutout:
            m = re.fullmatch(r"\s*([\d.]+),([\d.]+),([\d.]+),([\d.]+)\s*", spec)
            if not m:
                raise RuntimeError(f"bad --cutout {spec!r} (use X,Y,W,H in mm)")
            x, y, w, h = (float(g) for g in m.groups())
            if w <= 0 or h <= 0:
                raise RuntimeError(f"bad --cutout {spec!r}: W and H must be > 0")
            cutouts.append({"x": x, "y": y, "w": w, "h": h})

        job = {
            "out": str(pcb_path), "layers": args.layers,
            "components": components, "netmap": netmap,
            "fp_paths": args.fp_lib, "margin": args.margin, "outline": outline,
            "corner_radius": args.corner_radius, "cutouts": cutouts,
            "mounting_holes": ({"count": args.mounting_holes, "inset": args.margin / 2.0}
                               if args.mounting_holes else None),
        }
        import tempfile
        with tempfile.TemporaryDirectory(prefix="aiee_binit_") as td:
            jf = Path(td) / "job.json"
            jf.write_text(json.dumps(job), encoding="utf-8")
            cp = subprocess.run([str(bp), str(WORKER), str(jf)],
                                capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=300)
        worker = _last_json(cp.stdout)
        if worker is None or worker.get("status") != "pass":
            raise RuntimeError(f"board_swig worker failed: "
                               f"{(cp.stdout or cp.stderr)[-600:]}")

        inject_stackup(pcb_path, stackup)
        floors = write_pro(out_dir / f"{args.name}.kicad_pro", cap)

        has_sch = False
        if args.schematic:
            sch_dst = out_dir / f"{args.name}.kicad_sch"
            src = Path(args.schematic).resolve()
            # The schematic often already lives next to the board (P4 builds
            # into kicad/) - copying a file onto itself raises SameFileError.
            if src != sch_dst.resolve():
                shutil.copy(args.schematic, sch_dst)
            has_sch = True

        check = self_check(cli, pcb_path, has_sch)

        result = {
            "script": "board_init",
            "status": "pass" if check["clean"] else "violations",
            "board": str(pcb_path), "stackup": stk_name, "layers": args.layers,
            "fab_profile": cap_class, "copper_oz": outer_oz,
            "fab_floors": floors,
            "components": len(components), "nets": worker["nets"],
            "outline_bbox": worker["bbox"], "mounting_holes": args.mounting_holes,
            "corner_radius": worker.get("corner_radius", 0.0),
            "outline_origin": worker.get("outline_origin"),
            "cutouts": worker.get("cutouts", []),
            "self_check": check, "worker_notes": worker.get("notes", []),
        }
        _emit(result, args.out_report)
        return 0 if check["clean"] else 1
    except Exception:
        _emit({"script": "board_init", "status": "error",
               "error": traceback.format_exc()}, args.out_report if 'args' in dir() else None)
        return 2


def _last_json(text: str) -> dict | None:
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def _emit(obj: dict, out: str | None) -> None:
    s = json.dumps(obj, indent=2)
    if out:
        Path(out).write_text(s, encoding="utf-8")
    else:
        print(s)


if __name__ == "__main__":
    sys.exit(main())
