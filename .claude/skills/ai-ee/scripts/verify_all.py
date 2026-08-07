"""verify_all.py - run the P8 verification suite in parallel, merge results.

Runs every deterministic check (S4 crown jewels + S5) concurrently, each writing
its own reports/checks/<name>.json, then merges them into one stable summary
(reports/checks/summary.json). The orchestrator's `verify` gate (gates.yaml)
reads this summary; cluster_violations.py groups its violations for fixers.

A check is SKIPPED (not failed) when an input it requires is absent - e.g. no
constraints.json means the constraint-driven checks do not run. check_silk and
check_diffpair need only the board.

Summary schema (stable - downstream consumers may rely on it):
    {"script": "verify_all", "board": "<name>", "status": pass|violations|error,
     "counts": {"total", "by_severity"{}, "by_source"{}, "by_check"{}},
     "checks": {"<name>": {"status": pass|violations|error|skipped,
                           "counts"{}, "report": "<path>"|null, "reason"?}},
     "violations": [ ...merged normalized violations, each keeps its "source"... ]}

Exit: 0 all pass, 1 any violations, 2 any check errored (could not verify) or a
bad invocation.

CLI: --pcb board.kicad_pcb [--constraints c.json] [--decoupling d.json]
     [--reports-dir DIR] [--out summary.json] [--jobs N]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import checklib  # noqa: E402

SCRIPT = "verify_all"

# Each check: how to invoke it and which inputs it requires. `report` is the
# per-check JSON filename under the reports dir.
CHECKS = [
    {"name": "check_return_path", "needs": ["constraints"],
     "args": lambda a: ["--constraints", a["constraints"]]},
    {"name": "check_current", "needs": ["constraints"],
     "args": lambda a: ["--constraints", a["constraints"]]},
    {"name": "check_decoupling", "needs": ["decoupling"],
     "args": lambda a: ["--metadata", a["decoupling"]]},
    {"name": "check_diffpair", "needs": [],
     "args": lambda a: (["--constraints", a["constraints"]]
                        if a.get("constraints") else [])},
    {"name": "check_creepage", "needs": ["constraints"],
     "args": lambda a: ["--constraints", a["constraints"]]},
    {"name": "check_thermal", "needs": ["constraints"],
     "args": lambda a: ["--constraints", a["constraints"]]},
    {"name": "check_silk", "needs": [],
     "args": lambda a: []},
    {"name": "check_pdn", "needs": ["constraints", "decoupling"],
     "args": lambda a: ["--constraints", a["constraints"],
                        "--decoupling", a["decoupling"]]},
]


def run_one(check: dict, inputs: dict, reports_dir: Path) -> dict:
    """Run one check as a subprocess; return its merged-summary entry."""
    name = check["name"]
    missing = [k for k in check["needs"] if not inputs.get(k)]
    if missing:
        return {"name": name, "status": "skipped", "counts": {"total": 0},
                "report": None, "reason": f"no {'/'.join(missing)}",
                "violations": []}
    report_path = reports_dir / f"{name}.json"
    # a check that ERRORS does not write --out (cli_wrap prints to stdout); drop
    # any stale report first so this run cannot read a previous run's pass file.
    try:
        report_path.unlink()
    except FileNotFoundError:
        pass
    cmd = [sys.executable, str(HERE / f"{name}.py"), "--pcb", inputs["pcb"],
           *check["args"](inputs), "--out", str(report_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    payload = None
    if report_path.exists():
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
    if payload is None:  # error path: cli_wrap printed JSON to stdout, no file
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"script": name, "status": "error",
                       "error": (proc.stderr or proc.stdout or
                                 f"exit {proc.returncode}").strip()[:400]}
    return {
        "name": name,
        "status": payload.get("status", "error"),
        "counts": payload.get("counts", {"total": 0}),
        "report": str(report_path) if report_path.exists() else None,
        "error": payload.get("error"),
        "violations": payload.get("violations", []),
    }


def constraints_drift(constraints_path: str | None) -> dict | None:
    """Twin-sidecar preflight (T6, ladder row 154): the pipeline keeps
    constraints.json in BOTH <ws>/architecture/ and <ws>/kicad/; checks run
    against the given (kicad/) copy. When the architecture twin exists and
    parses to a DIFFERENT object (formatting drift is fine), return a
    warning violation - the 61-vs-53-answers class becomes visible at H4.
    Reconciliation is an owner decision; no winner is picked here."""
    if not constraints_path:
        return None
    given = Path(constraints_path)
    twin = given.resolve().parent.parent / "architecture" / "constraints.json"
    if not twin.is_file():
        return None
    try:
        a = json.loads(twin.read_text(encoding="utf-8"))
        b = json.loads(given.read_text(encoding="utf-8"))
        same = a == b
    except (OSError, json.JSONDecodeError) as exc:
        same, a = False, f"unreadable twin: {exc}"
    if same:
        return None
    return {
        "check": "verify_all", "severity": "warning", "pos": None,
        "layer": None, "net": None, "refs": [],
        "msg": (f"architecture/constraints.json diverges from {given.name} "
                f"in {given.parent.name}/; checks ran against the latter - "
                "reconcile or delete the stale twin"),
        "source": "verify_all", "kind": "constraints_drift",
        "twin": str(twin).replace("\\", "/"),
        "items": [{"msg": "constraints twin drift", "pos": None}],
    }


def merge(board, results: list[dict]) -> dict:
    all_v: list[dict] = []
    checks: dict[str, dict] = {}
    by_check: dict[str, int] = {}
    errored = False
    for r in results:
        for v in r["violations"]:
            all_v.append(v)
        by_check[r["name"]] = len(r["violations"])
        if r["status"] == "error":
            errored = True
        entry = {"status": r["status"], "counts": r["counts"],
                 "report": r["report"]}
        if r.get("reason"):
            entry["reason"] = r["reason"]
        if r.get("error"):
            entry["error"] = r["error"]
        checks[r["name"]] = entry
    counts = checklib.summarize(all_v)
    counts["by_check"] = by_check
    status = "error" if errored else ("violations" if all_v else "pass")
    return {"script": SCRIPT, "board": Path(board).name, "status": status,
            "counts": counts, "checks": checks, "violations": all_v}


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="Run the P8 verification suite in parallel and merge.")
    ap.add_argument("--pcb", required=True, help="path to .kicad_pcb")
    ap.add_argument("--constraints", help="constraints.json")
    ap.add_argument("--decoupling", help="decoupling.json")
    ap.add_argument("--reports-dir", help="dir for per-check + summary JSON "
                    "(default: <pcb dir>/reports/checks)")
    ap.add_argument("--out", help="write the summary here (also to reports dir)")
    ap.add_argument("--jobs", type=int, default=8, help="max parallel checks")
    args = ap.parse_args(argv)

    pcb = Path(args.pcb)
    if not pcb.exists():
        raise checklib.CheckError(f"board not found: {pcb}")
    reports_dir = Path(args.reports_dir) if args.reports_dir else \
        pcb.parent / "reports" / "checks"
    reports_dir.mkdir(parents=True, exist_ok=True)
    inputs = {"pcb": str(pcb), "constraints": args.constraints,
              "decoupling": args.decoupling}

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) \
            as ex:
        results = list(ex.map(lambda c: run_one(c, inputs, reports_dir), CHECKS))
    # keep CHECKS order (ThreadPoolExecutor.map preserves input order)
    summary = merge(pcb, results)
    drift = constraints_drift(args.constraints)
    if drift is not None:
        summary["violations"].append(drift)
        counts = checklib.summarize(summary["violations"])
        counts["by_check"] = {**summary["counts"]["by_check"],
                              "verify_all": 1}
        summary["counts"] = counts
        if summary["status"] == "pass":
            summary["status"] = "violations"
    (reports_dir / "summary.json").write_text(
        json.dumps(summary, indent=1), encoding="utf-8")
    return summary, args.out


def main(argv=None) -> int:
    return checklib.cli_wrap(SCRIPT, lambda: run(argv))


if __name__ == "__main__":
    raise SystemExit(main())
