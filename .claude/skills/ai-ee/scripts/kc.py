#!/usr/bin/env python
"""kc.py - thin, normalizing wrappers over kicad-cli (the ai-ee "firm bottom").

One place that knows how to drive kicad-cli and how to read its JSON. Every
gate and check consumes the NORMALIZED violation schema this module emits, so
the rest of the pipeline never re-parses kicad-cli's raw output.

Normalized violation schema (SPEC.md S2):

    {check, severity, pos, layer, net, refs, msg}

  check     kicad violation `type` (e.g. "track_width", "silk_over_copper")
  severity  "error" | "warning" | "exclusion"
  pos       [x, y] in mm, board/schematic space (the primary item's position)
  layer     e.g. "F.Cu", "In1.Cu", "F.Silkscreen" (parsed from item text) or null
  net       e.g. "+5V", "GND", "/USB_DP" (parsed from item text) or null
  refs      list of reference designators involved, e.g. ["D1"]
  msg       the human-readable rule description

Plus two traceability fields kept alongside the seven required keys:
  source    "erc" | "drc" | "unconnected" | "parity" (which report section)
  items     [{msg, pos}] for every kicad item in the violation (clearance
            violations name two items; checks/clusterers want both points)

kicad-cli does not expose layer/net/refdes as fields - they are embedded in the
item description strings ("Pad 1 [GND] of D1 on F.Cu"). We parse them
best-effort; `pos`, `check`, `severity`, `msg` are always exact.

Subcommands: erc, drc (-> normalized report, exit 1 if any violations);
gerbers, drill, pos, step, render, sch-pdf, netlist (-> export result, exit 2
on failure). All: JSON to stdout or --out FILE, exit 0/1/2, no interactivity
(SPEC.md section 6). Tools resolve through lib/env.py (KiCad 10.0.3 pin).

Importable: gate.py and render.py call run_erc()/run_drc()/render_png() and the
export_* helpers directly; the pure parsers (parse_drc_data, normalize_violation)
take raw dicts so they can be unit-tested without the toolchain.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import env  # noqa: E402

_TIMEOUT = 300

# The seven required keys, in schema order (used by tests and docs).
SCHEMA_KEYS = ("check", "severity", "pos", "layer", "net", "refs", "msg")

# ---------------------------------------------------------------- item parsing

# Layer token after " on ", e.g. "on F.Cu", "on In1.Cu", "on F.Silkscreen".
# Anchored on "on " so "length 7.5000 mm" cannot masquerade as a layer.
_LAYER_RE = re.compile(r"\bon ([A-Za-z][A-Za-z0-9]*\.[A-Za-z0-9_]+)")
# Net names are bracketed by kicad: "Track [+5V]", "Pad 1 [GND]".
_NET_RE = re.compile(r"\[([^\]]+)\]")
# Reference designators: 1-4 uppercase letters then digits (D1, U1, TP1, J2).
# Lowercase in layer tokens ("In1") cannot match, so layers are not mistaken
# for refdes.
_REF_RE = re.compile(r"\b([A-Z]{1,4}[0-9]+)\b")


def _extract_layer(text: str) -> str | None:
    m = _LAYER_RE.search(text or "")
    return m.group(1) if m else None


def _extract_net(text: str) -> str | None:
    m = _NET_RE.search(text or "")
    return m.group(1) if m else None


def _extract_refs(text: str) -> list[str]:
    # Strip bracketed net / pin names first: "[PB0]", "[GND]" look like refdes
    # but are nets/pins, not reference designators.
    return _REF_RE.findall(_NET_RE.sub("", text or ""))


def normalize_violation(v: dict, source: str) -> dict:
    """One raw kicad violation object -> the normalized schema dict.

    Aggregates layer/net over the violation's items (first non-null wins) and
    unions refdes across them; `pos` is the first item's position.
    """
    layer: str | None = None
    net: str | None = None
    refs: list[str] = []
    norm_items: list[dict] = []
    for it in v.get("items") or []:
        desc = it.get("description", "") or ""
        pos = it.get("pos") or {}
        point = [pos["x"], pos["y"]] if "x" in pos and "y" in pos else None
        if layer is None:
            layer = _extract_layer(desc)
        if net is None:
            net = _extract_net(desc)
        refs.extend(_extract_refs(desc))
        norm_items.append({"msg": desc, "pos": point})
    return {
        "check": v.get("type"),
        "severity": v.get("severity"),
        "pos": norm_items[0]["pos"] if norm_items else None,
        "layer": layer,
        "net": net,
        "refs": sorted(set(refs)),
        "msg": v.get("description"),
        "source": source,
        "items": norm_items,
    }


def parse_erc_data(data: dict) -> list[dict]:
    """kicad-cli `sch erc --format json` dict -> [normalized violation].

    ERC nests violations per sheet under sheets[].violations (DRC's are flat).
    """
    out = []
    for sheet in data.get("sheets", []):
        for v in sheet.get("violations", []):
            n = normalize_violation(v, "erc")
            n["sheet"] = sheet.get("uuid_path")
            out.append(n)
    return out


# DRC report section key -> normalized `source` label.
_DRC_SECTIONS = (
    ("violations", "drc"),
    ("unconnected_items", "unconnected"),
    ("schematic_parity", "parity"),
)


def parse_drc_data(data: dict) -> list[dict]:
    """kicad-cli `pcb drc --format json` dict -> [normalized violation].

    Merges the three parallel sections (violations, unconnected_items,
    schematic_parity) - they share one violation object shape.
    """
    out = []
    for key, source in _DRC_SECTIONS:
        for v in data.get(key, []):
            out.append(normalize_violation(v, source))
    return out


def summarize(violations: list[dict]) -> dict:
    """Counts by severity and by source, plus total."""
    counts = {"total": len(violations)}
    by_sev: dict[str, int] = {}
    by_src: dict[str, int] = {}
    for v in violations:
        by_sev[v["severity"]] = by_sev.get(v["severity"], 0) + 1
        by_src[v["source"]] = by_src.get(v["source"], 0) + 1
    counts["by_severity"] = by_sev
    counts["by_source"] = by_src
    return counts


# ---------------------------------------------------------------- cli plumbing

def resolve_cli() -> Path:
    cli = env.find_kicad_cli()
    if cli is None:
        raise RuntimeError(
            "kicad-cli not found (see check_env.py). The pipeline pins "
            "KiCad 10.0.3; set AIEE_KICAD_CLI to override.")
    return cli


def run_cli(cli: Path, args: list[str], timeout: int = _TIMEOUT
            ) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(cli), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def _run_json_report(cli: Path, section_args: list[str],
                     input_file: Path) -> dict:
    """Run a kicad-cli report command that writes JSON to a temp file; return
    the parsed dict. The temp file is always cleaned up."""
    with tempfile.TemporaryDirectory(prefix="aiee_kc_") as td:
        rep = Path(td) / "report.json"
        cp = run_cli(cli, [*section_args, "--format", "json",
                           "--severity-all", "-o", str(rep), str(input_file)])
        if not rep.exists():
            raise RuntimeError(
                f"kicad-cli produced no report (rc={cp.returncode}): "
                f"{(cp.stderr or cp.stdout).strip()[:400]}")
        return json.loads(rep.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- reports

def run_erc(cli: Path, sch: Path) -> dict:
    data = _run_json_report(cli, ["sch", "erc"], sch)
    violations = parse_erc_data(data)
    return {
        "script": "kc", "tool": "erc", "input": str(sch),
        "units": data.get("coordinate_units", "mm"),
        "kicad_version": data.get("kicad_version"),
        "counts": summarize(violations),
        "status": "pass" if not violations else "violations",
        "violations": violations,
    }


def run_drc(cli: Path, pcb: Path, *, parity: bool = False,
            all_track_errors: bool = False, refill: bool = False,
            save_board: bool = False) -> dict:
    args = ["pcb", "drc"]
    if parity:
        args.append("--schematic-parity")
    if all_track_errors:
        args.append("--all-track-errors")
    if refill:
        args.append("--refill-zones")
        if save_board:
            args.append("--save-board")
    data = _run_json_report(cli, args, pcb)
    violations = parse_drc_data(data)
    return {
        "script": "kc", "tool": "drc", "input": str(pcb),
        "units": data.get("coordinate_units", "mm"),
        "kicad_version": data.get("kicad_version"),
        "options": {"parity": parity, "all_track_errors": all_track_errors,
                    "refill": refill, "save_board": save_board},
        "counts": summarize(violations),
        "status": "pass" if not violations else "violations",
        "violations": violations,
    }


# ---------------------------------------------------------------- exports

def _export_result(tool: str, input_file: Path, cp: subprocess.CompletedProcess,
                   outputs: list[Path]) -> dict:
    existing = [str(p) for p in outputs if p.exists()]
    ok = cp.returncode == 0 and bool(existing)
    return {
        "script": "kc", "tool": tool, "input": str(input_file),
        "status": "pass" if ok else "error",
        "outputs": existing,
        "returncode": cp.returncode,
        "stderr_tail": (cp.stderr or "").strip()[-400:] if not ok else "",
    }


def export_gerbers(cli: Path, pcb: Path, out_dir: Path,
                   layers: str | None = None, extra: list[str] | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in out_dir.iterdir()}
    args = ["pcb", "export", "gerbers", "-o", str(out_dir)]
    if layers:
        args += ["--layers", layers]
    args += (extra or [])
    args.append(str(pcb))
    cp = run_cli(cli, args)
    produced = [out_dir / p.name for p in out_dir.iterdir()
                if p.name not in before]
    res = _export_result("gerbers", pcb, cp, produced or list(out_dir.iterdir()))
    res["output_dir"] = str(out_dir)
    return res


def export_drill(cli: Path, pcb: Path, out_dir: Path,
                 fmt: str = "excellon", extra: list[str] | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in out_dir.iterdir()}
    args = ["pcb", "export", "drill", "-o", str(out_dir) + "/",
            "--format", fmt]
    args += (extra or [])
    args.append(str(pcb))
    cp = run_cli(cli, args)
    produced = [out_dir / p.name for p in out_dir.iterdir()
                if p.name not in before]
    res = _export_result("drill", pcb, cp, produced or list(out_dir.iterdir()))
    res["output_dir"] = str(out_dir)
    return res


def export_pos(cli: Path, pcb: Path, out_file: Path, side: str = "both",
               fmt: str = "csv", units: str = "mm") -> dict:
    # kicad-cli defaults pos units to INCHES (LEARNINGS [kicad-cli]); always
    # force units so downstream CPL geometry is mm.
    out_file.parent.mkdir(parents=True, exist_ok=True)
    args = ["pcb", "export", "pos", "-o", str(out_file), "--side", side,
            "--format", fmt]
    if fmt in ("ascii", "csv"):
        args += ["--units", units]
    args.append(str(pcb))
    cp = run_cli(cli, args)
    return _export_result("pos", pcb, cp, [out_file])


def export_step(cli: Path, pcb: Path, out_file: Path, force: bool = True) -> dict:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    args = ["pcb", "export", "step", "-o", str(out_file)]
    if force:
        args.append("--force")
    args.append(str(pcb))
    cp = run_cli(cli, args, timeout=600)
    return _export_result("step", pcb, cp, [out_file])


def export_sch_pdf(cli: Path, sch: Path, out_file: Path) -> dict:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    args = ["sch", "export", "pdf", "-o", str(out_file), str(sch)]
    cp = run_cli(cli, args)
    return _export_result("sch-pdf", sch, cp, [out_file])


def export_netlist(cli: Path, sch: Path, out_file: Path,
                   fmt: str = "kicadsexpr") -> dict:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    args = ["sch", "export", "netlist", "-o", str(out_file),
            "--format", fmt, str(sch)]
    cp = run_cli(cli, args)
    return _export_result("netlist", sch, cp, [out_file])


# ---------------------------------------------------------------- render

# `pcb render --side` has no "iso"; isometric is orthographic rotate -45,0,45.
ISO_ROTATE = "-45,0,45"


def render_png(cli: Path, pcb: Path, out_file: Path, *, side: str = "top",
               width: int = 1600, height: int = 900, quality: str = "high",
               rotate: str | None = None) -> dict:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    # -h collides with --help; use long form --height (LEARNINGS [kicad-cli]).
    args = ["pcb", "render", "-o", str(out_file), "--side", side,
            "--width", str(width), "--height", str(height),
            "--quality", quality]
    if rotate:
        args += ["--rotate", rotate]
    args.append(str(pcb))
    cp = run_cli(cli, args, timeout=600)
    res = _export_result("render", pcb, cp, [out_file])
    res["view"] = side if not rotate else "iso"
    return res


# ---------------------------------------------------------------- cli

def _emit(report: dict, out: str | None) -> None:
    text = json.dumps(report, indent=2)
    if out:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    else:
        print(text)


def _report_exit(report: dict) -> int:
    # pass -> 0, violations present -> 1, error -> 2
    return 0 if report.get("status") == "pass" else 1


def _export_exit(report: dict) -> int:
    return 0 if report.get("status") == "pass" else 2


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(p, out_help="write JSON report here instead of stdout"):
        p.add_argument("input", help="input .kicad_sch or .kicad_pcb")
        p.add_argument("--out", help=out_help)

    p_erc = sub.add_parser("erc", help="ERC -> normalized violations")
    add_common(p_erc)

    p_drc = sub.add_parser("drc", help="DRC -> normalized violations")
    add_common(p_drc)
    p_drc.add_argument("--parity", action="store_true",
                       help="test schematic/PCB parity")
    p_drc.add_argument("--all-track-errors", action="store_true")
    p_drc.add_argument("--refill", action="store_true",
                       help="refill zones before DRC (in memory)")
    p_drc.add_argument("--save-board", action="store_true",
                       help="persist refilled zones (mutates the board; "
                            "requires --refill)")

    p_ger = sub.add_parser("gerbers", help="export gerbers to a directory")
    p_ger.add_argument("input")
    p_ger.add_argument("--out", required=True, help="output directory")
    p_ger.add_argument("--layers", help="comma list e.g. F.Cu,B.Cu,Edge.Cuts")

    p_dri = sub.add_parser("drill", help="export drill files to a directory")
    p_dri.add_argument("input")
    p_dri.add_argument("--out", required=True, help="output directory")
    p_dri.add_argument("--format", default="excellon",
                       choices=["excellon", "gerber"])

    p_pos = sub.add_parser("pos", help="export placement (pos) file")
    p_pos.add_argument("input")
    p_pos.add_argument("--out", required=True, help="output file")
    p_pos.add_argument("--side", default="both",
                       choices=["front", "back", "both"])
    p_pos.add_argument("--format", default="csv",
                       choices=["ascii", "csv", "gerber"])
    p_pos.add_argument("--units", default="mm", choices=["mm", "in"])

    p_step = sub.add_parser("step", help="export STEP 3D model")
    p_step.add_argument("input")
    p_step.add_argument("--out", required=True, help="output file")

    p_ren = sub.add_parser("render", help="render one 3D view to PNG")
    p_ren.add_argument("input")
    p_ren.add_argument("--out", required=True, help="output PNG")
    p_ren.add_argument("--side", default="top",
                       choices=["top", "bottom", "left", "right",
                                "front", "back"])
    p_ren.add_argument("--iso", action="store_true",
                       help="isometric (rotate -45,0,45)")
    p_ren.add_argument("--width", type=int, default=1600)
    p_ren.add_argument("--height", type=int, default=900)
    p_ren.add_argument("--quality", default="high",
                       choices=["basic", "high", "user", "job_settings"])

    p_pdf = sub.add_parser("sch-pdf", help="export schematic to PDF")
    p_pdf.add_argument("input")
    p_pdf.add_argument("--out", required=True, help="output PDF")

    p_net = sub.add_parser("netlist", help="export netlist")
    p_net.add_argument("input")
    p_net.add_argument("--out", required=True, help="output file")
    p_net.add_argument("--format", default="kicadsexpr")

    args = ap.parse_args(argv)

    try:
        cli = resolve_cli()
        inp = Path(args.input)
        if args.cmd == "erc":
            r = run_erc(cli, inp)
            _emit(r, args.out)
            return _report_exit(r)
        if args.cmd == "drc":
            if args.save_board and not args.refill:
                ap.error("--save-board requires --refill")
            r = run_drc(cli, inp, parity=args.parity,
                        all_track_errors=args.all_track_errors,
                        refill=args.refill, save_board=args.save_board)
            _emit(r, args.out)
            return _report_exit(r)
        if args.cmd == "gerbers":
            r = export_gerbers(cli, inp, Path(args.out), layers=args.layers)
        elif args.cmd == "drill":
            r = export_drill(cli, inp, Path(args.out), fmt=args.format)
        elif args.cmd == "pos":
            r = export_pos(cli, inp, Path(args.out), side=args.side,
                           fmt=args.format, units=args.units)
        elif args.cmd == "step":
            r = export_step(cli, inp, Path(args.out))
        elif args.cmd == "render":
            r = render_png(cli, inp, Path(args.out), side=args.side,
                           width=args.width, height=args.height,
                           quality=args.quality,
                           rotate=ISO_ROTATE if args.iso else None)
        elif args.cmd == "sch-pdf":
            r = export_sch_pdf(cli, inp, Path(args.out))
        elif args.cmd == "netlist":
            r = export_netlist(cli, inp, Path(args.out), fmt=args.format)
        else:  # pragma: no cover - argparse guarantees a known cmd
            ap.error(f"unknown command {args.cmd}")
        # export path: --out is a destination, so echo the result to stdout too
        print(json.dumps(r, indent=2))
        return _export_exit(r)
    except Exception:
        print(json.dumps({"script": "kc", "status": "error",
                          "error": traceback.format_exc()}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
