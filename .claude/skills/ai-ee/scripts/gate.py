#!/usr/bin/env python
"""gate.py - evaluate a pipeline gate (SPEC.md sections 3-4).

    gate.py --gate <name> <input.kicad_sch|.kicad_pcb> [--out FILE] [--commit MSG]
    gate.py --gate <name> --report <kc-report.json>          (evaluate, don't re-run)
    gate.py --list

A gate (defined in reference/gates.yaml) runs a kc.py report on an artifact and
applies pass criteria: it FAILS when the count of violations whose severity is
in the gate's fail_severities exceeds max_count. On pass, --commit MSG git-adds
and commits the repo (SPEC section 4: "Git commit after every gate pass"); it
never commits on failure and never pushes.

JSON to stdout (or --out): {script, gate, status:pass|fail, counts, criteria,
failing:[violations that triggered], committed?}. Exit 0 = pass, 1 = fail,
2 = error (bad gate name, toolchain, unreadable input).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kc  # noqa: E402
from lib import env  # noqa: E402

import yaml  # noqa: E402

DEFAULT_GATES = (Path(__file__).resolve().parent.parent
                 / "reference" / "gates.yaml")


def load_gates(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    gates = data.get("gates", {})
    if not gates:
        raise RuntimeError(f"no gates defined in {path}")
    return gates


def run_report_for_gate(gate: dict, input_file: Path) -> dict:
    """Produce a normalized report per the gate's tool. erc/drc go through
    kc.py; verify runs the whole P8 suite via verify_all (its merged summary
    carries the same {violations, counts} shape evaluate() needs)."""
    tool = gate.get("tool")
    if tool == "verify":
        return run_verify(input_file)
    if tool == "place":
        import place_metrics  # noqa: E402  (sibling script)
        payload, _ = place_metrics.run(["--pcb", str(input_file)])
        return payload  # sidecars default to the board's own directory
    if tool == "dfm":
        return run_dfm(input_file)
    cli = kc.resolve_cli()
    if tool == "erc":
        return kc.run_erc(cli, input_file)
    if tool == "drc":
        opts = gate.get("drc_options") or {}
        # Gates never mutate the board: no refill / save.
        return kc.run_drc(cli, input_file,
                          parity=bool(opts.get("parity")),
                          all_track_errors=bool(opts.get("all_track_errors")))
    raise RuntimeError(
        "gate tool must be 'erc', 'drc', 'verify', 'place' or 'dfm', "
        f"got {tool!r}")


def run_dfm(board: Path) -> dict:
    """Run dfm_check on the board (P9). Gerbers are exported to a scratch dir,
    so gating never litters the design folder; the schematic beside the board
    (pipeline convention) is the CPL-polarity oracle, and parts.json - when the
    project has one - drives the BOM-completeness leg."""
    import dfm_check  # noqa: E402  (sibling script)
    kwargs: dict = {}
    sch = board.with_suffix(".kicad_sch")
    if sch.exists():
        kwargs["schematic"] = sch
    parts = board.parent / "parts.json"
    if parts.exists():
        kwargs["parts"] = parts
    return dfm_check.run(board, **kwargs)


def run_verify(board: Path) -> dict:
    """Run verify_all on the board, taking constraints.json / decoupling.json
    from the board's own directory (the pipeline places them there). Reports go
    to a scratch dir so gating never litters the design folder."""
    import shutil
    import tempfile
    import verify_all  # noqa: E402  (sibling script)
    reports = Path(tempfile.mkdtemp(prefix="gate_verify_"))
    try:
        argv = ["--pcb", str(board), "--reports-dir", str(reports)]
        for fname, flag in (("constraints.json", "--constraints"),
                            ("decoupling.json", "--decoupling")):
            f = board.parent / fname
            if f.exists():
                argv += [flag, str(f)]
        summary, _ = verify_all.run(argv)
    finally:
        shutil.rmtree(reports, ignore_errors=True)
    if summary.get("status") == "error":
        bad = [n for n, c in summary.get("checks", {}).items()
               if c.get("status") == "error"]
        raise RuntimeError(f"verification could not run (checks errored: {bad})")
    summary["input"] = str(board)
    return summary


def evaluate(gate_name: str, gate: dict, report: dict) -> dict:
    fail_sev = set(gate.get("fail_severities") or ["error"])
    max_count = int(gate.get("max_count", 0))
    violations = report.get("violations", [])
    failing = [v for v in violations if v.get("severity") in fail_sev]
    passed = len(failing) <= max_count
    return {
        "script": "gate",
        "gate": gate_name,
        "phase": gate.get("phase"),
        "tool": gate.get("tool"),
        "input": report.get("input"),
        "status": "pass" if passed else "fail",
        "criteria": {"fail_severities": sorted(fail_sev), "max_count": max_count},
        "counts": report.get("counts", {}),
        "failing_count": len(failing),
        "failing": failing,
    }


def git_commit_on_pass(msg: str, cwd: Path) -> dict:
    """Stage everything and commit (only called when a gate passed).

    Skips cleanly when there is nothing to commit. Never pushes. Returns a
    small status dict recorded in the gate result.
    """
    def git(*args):
        return subprocess.run(["git", *args], cwd=str(cwd),
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    status = git("status", "--porcelain")
    if status.returncode != 0:
        return {"committed": False, "reason": f"git status failed: {status.stderr.strip()}"}
    if not status.stdout.strip():
        return {"committed": False, "reason": "nothing to commit"}
    add = git("add", "-A")
    if add.returncode != 0:
        return {"committed": False, "reason": f"git add failed: {add.stderr.strip()}"}
    commit = git("commit", "-m", msg)
    if commit.returncode != 0:
        return {"committed": False, "reason": f"git commit failed: {commit.stderr.strip()}"}
    rev = git("rev-parse", "--short", "HEAD")
    return {"committed": True, "commit": rev.stdout.strip()}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", nargs="?", help="input .kicad_sch or .kicad_pcb")
    ap.add_argument("--gate", help="gate name from gates.yaml")
    ap.add_argument("--gates", default=str(DEFAULT_GATES),
                    help="path to gates.yaml")
    ap.add_argument("--report", help="evaluate this kc.py report JSON instead "
                                     "of running the tool")
    ap.add_argument("--out", help="write gate result JSON here instead of stdout")
    ap.add_argument("--commit", metavar="MSG",
                    help="git commit the repo on gate pass with this message")
    ap.add_argument("--list", action="store_true", help="list gates and exit")
    args = ap.parse_args(argv)

    try:
        gates = load_gates(Path(args.gates))
        if args.list:
            listing = {name: {"phase": g.get("phase"), "tool": g.get("tool"),
                              "description": g.get("description")}
                       for name, g in gates.items()}
            print(json.dumps({"script": "gate", "gates": listing}, indent=2))
            return 0
        if not args.gate:
            ap.error("--gate is required (or use --list)")
        if args.gate not in gates:
            raise RuntimeError(
                f"unknown gate {args.gate!r}; known: {', '.join(gates)}")
        gate = gates[args.gate]

        if args.report:
            report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        else:
            if not args.input:
                ap.error("an input file is required unless --report is given")
            report = run_report_for_gate(gate, Path(args.input))

        result = evaluate(args.gate, gate, report)

        if result["status"] == "pass" and args.commit:
            result["commit_result"] = git_commit_on_pass(args.commit, env.repo_root())
    except Exception:
        print(json.dumps({"script": "gate", "status": "error",
                          "error": traceback.format_exc()}))
        return 2

    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)

    # one-line human summary to stderr; stdout stays pure JSON
    n = result.get("failing_count", 0)
    print(f"gate {args.gate}: {result['status'].upper()} "
          f"({n} failing / {result['counts'].get('total', 0)} total)",
          file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
