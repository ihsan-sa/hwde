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

T6 additions:
 - --commit stages the board WORKSPACE only (boards/<name>/, derived from the
   input path), never `git add -A` at repo root - a parallel session's dirty
   files no longer ride along in gate commits (LEARNINGS 2026-07-27). Dirty
   paths outside the workspace are listed in commit_result.excluded_dirty.
 - drc gates with drc_options.require_fresh_fills (drc_routed) refuse a
   stale-fill board with exit 2 instead of grading ~375 phantom zone
   clearance errors (LEARNINGS 2026-07-29, hand-run KRT board).
 - --waivers FILE (default <input dir>/reports/verify-waivers.json for the
   verify gate): human-approved residual findings; each waiver needs
   non-empty `reason` and `approved` and matches on (check|kind) + net
   (+ refs subset). Waived violations do not count toward failure but are
   echoed in the result as `waived`.
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
    if tool == "sim":
        return run_sim(input_file)
    if tool == "drc":
        opts = gate.get("drc_options") or {}
        if opts.get("require_fresh_fills"):
            # A stale/unfilled zone makes DRC grade ~375 phantom clearance
            # errors (LEARNINGS 2026-07-29): report staleness, don't grade.
            # Preflight runs BEFORE kicad-cli resolution so the refusal is
            # deterministic. Gates never mutate the board: no refill/save.
            from lib import geom  # noqa: E402
            try:
                geom.load_board(input_file).assert_fresh()
            except geom.StaleFillError as exc:
                raise RuntimeError(
                    "zone fills are stale - refill via kc.py drc "
                    f"--refill --save-board, then re-gate ({exc})") from exc
        cli = kc.resolve_cli()
        return kc.run_drc(cli, input_file,
                          parity=bool(opts.get("parity")),
                          all_track_errors=bool(opts.get("all_track_errors")))
    cli = kc.resolve_cli()
    if tool == "erc":
        return kc.run_erc(cli, input_file)
    raise RuntimeError(
        "gate tool must be 'erc', 'drc', 'verify', 'place', 'dfm' or 'sim', "
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


def run_sim(sims: Path) -> dict:
    """Run sim_run on a sims DIRECTORY (or a single .cir testbench) - the
    only gate whose input is not a board file. Bounds sidecars live beside
    the testbenches (pipeline convention: kicad/sims/)."""
    import sim_run  # noqa: E402  (sibling script)
    return sim_run.run(sims)


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


def load_waivers(path: Path) -> list[dict]:
    """Load and validate a waiver sidecar. Waivers are HUMAN artifacts: every
    entry must carry a non-empty `reason` and `approved` (who/when), and at
    least one of check/kind to match on - else the gate errors (exit 2)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    waivers = data.get("waivers")
    if not isinstance(waivers, list):
        raise RuntimeError(f"{path}: no 'waivers' list")
    for i, w in enumerate(waivers):
        if not str(w.get("reason") or "").strip() \
                or not str(w.get("approved") or "").strip():
            raise RuntimeError(
                f"{path}: waiver {i} lacks reason/approved - waivers are "
                "human artifacts, never agent-invented")
        if not (w.get("check") or w.get("kind")):
            raise RuntimeError(f"{path}: waiver {i} needs check and/or kind")
    return waivers


def waiver_matches(w: dict, v: dict) -> bool:
    """Exact (check|kind) + net; refs subset when the waiver lists refs."""
    if w.get("check") and v.get("check") != w["check"] \
            and v.get("source") != w["check"]:
        return False
    if w.get("kind") and v.get("kind") != w["kind"]:
        return False
    if w.get("net") != v.get("net"):
        return False
    if w.get("refs"):
        if not set(v.get("refs") or []) <= set(w["refs"]):
            return False
    return True


def evaluate(gate_name: str, gate: dict, report: dict,
             waivers: list[dict] | None = None) -> dict:
    fail_sev = set(gate.get("fail_severities") or ["error"])
    max_count = int(gate.get("max_count", 0))
    violations = report.get("violations", [])
    failing = [v for v in violations if v.get("severity") in fail_sev]
    waived = []
    if waivers:
        still = []
        for v in failing:
            if any(waiver_matches(w, v) for w in waivers):
                waived.append(v)
            else:
                still.append(v)
        failing = still
    passed = len(failing) <= max_count
    result = {
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
    if waivers is not None:
        result["waived_count"] = len(waived)
        result["waived"] = waived
    return result


def workspace_dir(input_file: Path | None) -> Path | None:
    """The boards/<name>/ workspace an input path sits in, or None."""
    if input_file is None:
        return None
    p = Path(input_file).resolve()
    for parent in p.parents:
        if parent.parent.name == "boards":
            return parent
    return None


def git_commit_on_pass(msg: str, cwd: Path,
                       input_file: Path | None = None) -> dict:
    """Stage the gate's workspace and commit (only called on gate pass).

    Staging is SCOPED to the board workspace derived from `input_file`
    (ladder row 59: repo-root `git add -A` swept parallel-session WIP into
    gate commits). Dirty paths outside the workspace stay unstaged and are
    listed in the result as `excluded_dirty`. When the input is not under
    boards/ (bench/test invocations), -A is only allowed on an otherwise
    clean tree: any dirty path outside the input file's own top-level tree
    refuses the commit. Skips cleanly when there is nothing to commit.
    Never pushes.
    """
    def git(*args):
        return subprocess.run(["git", *args], cwd=str(cwd),
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    # -uall: porcelain must list untracked FILES, not collapsed directories,
    # or the workspace-scope test below cannot see inside a new workspace
    status = git("status", "--porcelain", "-uall")
    if status.returncode != 0:
        return {"committed": False, "reason": f"git status failed: {status.stderr.strip()}"}
    if not status.stdout.strip():
        return {"committed": False, "reason": "nothing to commit"}
    dirty = [ln[3:].strip().strip('"').replace("\\", "/")
             for ln in status.stdout.splitlines() if ln.strip()]

    ws = workspace_dir(input_file)
    if ws is not None:
        try:
            ws_rel = ws.resolve().relative_to(Path(cwd).resolve()).as_posix()
        except ValueError:
            ws_rel = None
    else:
        ws_rel = None

    extras: dict = {}
    if ws_rel is not None:
        inside = [d for d in dirty
                  if d == ws_rel or d.startswith(ws_rel + "/")]
        outside = [d for d in dirty if d not in inside]
        if not inside:
            return {"committed": False, "scope": ws_rel,
                    "reason": "nothing to commit inside the workspace",
                    "excluded_dirty": outside}
        add = git("add", "--", ws_rel)
        extras = {"scope": ws_rel}
        if outside:
            extras["excluded_dirty"] = outside
    else:
        if input_file is not None:
            # not a boards/ workspace: -A would sweep the whole tree, so it
            # is only allowed when every dirty path is inside the input's own
            # top-level tree (tmp-repo tests) - else refuse, do not sweep.
            try:
                top = (Path(input_file).resolve()
                       .relative_to(Path(cwd).resolve()).parts[0])
            except ValueError:
                top = None
            outside = [d for d in dirty
                       if top is None or d.split("/")[0] != top]
            if outside:
                return {"committed": False,
                        "reason": "dirty paths outside workspace: "
                                  + ", ".join(sorted(outside)[:20])}
        add = git("add", "-A")
    if add.returncode != 0:
        return {"committed": False, "reason": f"git add failed: {add.stderr.strip()}"}
    commit = git("commit", "-m", msg)
    if commit.returncode != 0:
        return {"committed": False, "reason": f"git commit failed: {commit.stderr.strip()}"}
    rev = git("rev-parse", "--short", "HEAD")
    return {"committed": True, "commit": rev.stdout.strip(), **extras}


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
                    help="git commit the workspace on gate pass with this message")
    ap.add_argument("--waivers", help="waiver sidecar JSON (default: <input "
                    "dir>/reports/verify-waivers.json for the verify gate)")
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

        waivers = None
        if args.waivers:
            waivers = load_waivers(Path(args.waivers))
        elif gate.get("tool") == "verify" and args.input:
            sidecar = (Path(args.input).parent / "reports"
                       / "verify-waivers.json")
            if sidecar.is_file():
                waivers = load_waivers(sidecar)

        result = evaluate(args.gate, gate, report, waivers=waivers)

        if result["status"] == "pass" and args.commit:
            inp = Path(args.input) if args.input else None
            result["commit_result"] = git_commit_on_pass(
                args.commit, env.repo_root(), input_file=inp)
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
