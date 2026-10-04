"""e2e_run - run ONE model-driven design run in a sandbox and score it.

The eval loop's e2e driver (design: pipeline-arch "The eval loop"). One call
is one run: one held-out brief, one arm, one seed.

  bare  Claude Code alone, told the output layout the scorer reads.
  hwde  Claude Code with the hwde skill copied into its project.

The run happens inside bwrap with an ALLOWLIST filesystem: a fresh tmpfs
HOME, the toolchain read-only at its usual paths (KiCad, the hwde venv and
tools, the claude binary), the claude credentials file, and a writable
/work. Nothing else under /home exists in there, so the repo (tests/, its
.git, results/), ~/dev/boards, ~/.cc and ~/.claude's transcripts cannot be
read. The agent gets brief.md and nothing else from the brief's directory;
bounds.yaml stays outside. The skill copy leaves out reference/e2e-scoring.md
(the grading method). The network is shared, because the agent needs the
API and the part catalogues.

After the run, bench.py --stage E2E scores /work's board OUTSIDE the
sandbox, and one run record (with its findings: every check scoring below 1)
is appended to --out as a JSON line.

Stops: --max-budget-usd (default 40) is passed to claude, so a run that
would cost more is cut off there and recorded with budget_stopped=true.
--seeds N runs seeds 1..N one after another (the cost pilot) and stops
after the first run that hit that cap.

The run starts claude as `-p --permission-mode acceptEdits --allowedTools
<list>`: file edits are accepted, and only the tools a design run needs are
allowed (ALLOWED_TOOLS; Bash only for the hwde venv python running the
skill's scripts and the board's kicad/gen/ generator, kicad-cli, ls,
mkdir and cd /work; the bare arm gets python3 and python on any file instead, since it has no scripts of its own;
the venv's bin is first on the sandbox's PATH). Nothing else is granted, so a call outside the list is denied rather than prompted, and bwrap
stays the boundary around all of it. From a terminal with the hwde toolchain
sourced:
  . ~/.local/kicad10/hwde-env.sh
  .venv/bin/python evals/e2e_run.py --brief usbc_ldo --arm hwde --seeds 1

CLI:
  e2e_run.py --brief usbc_ldo --arm hwde (--seed 1 | --seeds 5) [--model M]
             [--out evals/results.jsonl] [--runs-root DIR] [--timeout-s N]
  e2e_run.py --probe PATH...   read each PATH inside the sandbox; prints
                               {path: readable} JSON (the sandbox's own test)

Exit 0 on a recorded run (whatever it scored), 1 when the run or the score
failed, 2 on bad input (unknown brief, no bwrap).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "hwde"
BENCH = SKILL / "scripts" / "bench.py"
BRIEFS = REPO / "tests" / "fixtures" / "stages" / "e2e"
HOME = Path.home()
WORK = "/work"
BOARD = "board"          # the bare arm's workspace dir under /work
SKILL_HIDE = {"reference/e2e-scoring.md"}

# Host paths bound read-only at the same path; absent ones are skipped.
RO_SYSTEM = ["/usr", "/etc", "/opt", "/run/systemd/resolve"]
RO_HOME = [".local/kicad10", ".local/hwde-venv", ".local/hwde-tools",
           ".local/share/claude", ".local/bin/claude"]
CREDS = ".claude/.credentials.json"


def sandbox_argv(work: Path) -> list[str]:
    """bwrap argv (without the command) that exposes only the allowlist.
    Brief: "a sandbox that cannot read tests/, results/ or ~/dev/boards" -
    /home is an empty tmpfs, so none of them exists in here."""
    if not shutil.which("bwrap"):
        raise SystemExit("e2e_run: bwrap not found")
    a = ["bwrap", "--die-with-parent", "--unshare-pid", "--unshare-ipc",
         "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
         "--tmpfs", "/home", "--tmpfs", "/var", "--tmpfs", "/run",
         "--dir", str(HOME)]
    for p in ("bin", "lib", "lib64", "sbin"):
        top = Path("/") / p
        if top.is_symlink():
            a += ["--symlink", os.readlink(top), str(top)]
        elif top.exists():
            a += ["--ro-bind", str(top), str(top)]
    for p in RO_SYSTEM:
        if Path(p).exists():
            a += ["--ro-bind", p, p]
    for rel in RO_HOME:
        p = HOME / rel
        if p.exists():
            a += ["--ro-bind", str(p), str(p)]
    creds = HOME / CREDS
    if creds.exists():   # rw: an OAuth refresh writes it back
        a += ["--dir", str(HOME / ".claude"), "--bind", str(creds), str(creds)]
    a += ["--bind", str(work), WORK, "--chdir", WORK,
          "--setenv", "HOME", str(HOME),
          "--setenv", "HWDE_BOARDS_ROOT", f"{WORK}/boards",
          "--setenv", "PATH",
          f"{HOME}/.local/hwde-venv/bin:{HOME}/.local/kicad10/bin:"
          f"{HOME}/.local/bin:/usr/bin:/bin"]
    return a + ["--"]


def probe(paths: list[str]) -> dict:
    """{path: readable} as seen from inside the sandbox."""
    with tempfile.TemporaryDirectory() as td:
        out = {}
        for p in paths:
            r = subprocess.run(sandbox_argv(Path(td)) + [
                "/bin/sh", "-c", 'ls -- "$1" >/dev/null 2>&1 || cat -- "$1" '
                                 '>/dev/null 2>&1', "sh", p],
                capture_output=True)
            out[p] = r.returncode == 0
        return out


# Planning, 2026-10-04: "launch the nested run as claude -p --permission-mode
# acceptEdits --allowedTools <explicit list>, naming exactly the tools a design
# run needs (Read, Edit, Write, Glob, Grep, and Bash scoped as narrowly as the
# hwde scripts allow)". Skill and Agent are how /hwde and its agents/ run.
_FILE_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep", "TodoWrite"]
_SHELL = ["Bash(kicad-cli:*)", "Bash(ls:*)", "Bash(mkdir:*)",
          f"Bash(cd {WORK}:*)"]
_PY = ["python3", "python", ".venv/bin/python", f"{WORK}/.venv/bin/python"]
# the skill's scripts, and the schematic generator its P4 agent writes into
# the board (the 2026-10-04 pilot run stopped at P4 when that was denied)
_SCRIPTS = [".claude/skills/hwde/scripts/",
            f"{WORK}/.claude/skills/hwde/scripts/",
            "boards/*/kicad/gen/", f"{WORK}/boards/*/kicad/gen/"]
ALLOWED_TOOLS = {
    "hwde": _FILE_TOOLS + ["Skill", "Agent"] + _SHELL + [
        f"Bash({py} {sc}*)" for py in _PY for sc in _SCRIPTS],
    "bare": _FILE_TOOLS + _SHELL + ["Bash(python3:*)", "Bash(python:*)"],
}


def prompt(arm: str, brief: str) -> str:
    if arm == "hwde":
        return (f"/hwde Take this brief through the full brief-to-order "
                f"pipeline, unattended: there is no human to answer holds, "
                f"so record your assumptions and continue. Put the board "
                f"workspace under {WORK}/boards/. Run the skill's scripts "
                f"from {WORK} as `python3 .claude/skills/hwde/scripts/<name>"
                f".py ...` (python3 is the hwde venv; the HWDE_* tool pins "
                f"are set), one command per call: other shell commands are "
                f"denied.\n\n{brief}")
    return (f"Design this board in KiCad 10 (kicad-cli and its python are "
            f"on PATH), unattended: nobody will answer questions. Leave the "
            f"finished design in {WORK}/{BOARD}/: kicad/{BOARD}.kicad_sch, "
            f"kicad/{BOARD}.kicad_pcb (routed, with a closed Edge.Cuts "
            f"outline), the netlist kicad/{BOARD}.net, and the BOM as "
            f"parts/parts.json (a list of parts with refs, value, LCSC "
            f"number and unit price).\n\n{brief}")


def find_workspace(work: Path, arm: str) -> Path | None:
    if arm == "bare":
        ws = work / BOARD
        return ws if ws.is_dir() else None
    cands = [p.parent for p in (work / "boards").glob("*/kicad")
             if p.is_dir()]
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def git_head() -> str:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def kicad_version() -> str | None:
    cli = shutil.which("kicad-cli") or str(HOME / ".local/kicad10/bin/kicad-cli")
    try:
        r = subprocess.run([cli, "version"], capture_output=True, text=True,
                           timeout=60)
        return r.stdout.strip() or None
    except OSError:
        return None


def score(fixture: str, ws: Path | None, out: Path) -> dict | None:
    if ws is None:
        return None
    r = subprocess.run([sys.executable, str(BENCH), "--stage", "E2E",
                        "--fixture", fixture, "--artifact", str(ws),
                        "--out", str(out)], capture_output=True, text=True)
    if r.returncode != 0 or not out.is_file():
        return {"error": (r.stderr or r.stdout)[-2000:]}
    return json.loads(out.read_text(encoding="utf-8"))


def findings(sc: dict | None) -> list[dict]:
    """The design doc's finding shape, from every e2e check below 1."""
    sc = sc or {}
    checks = list((sc.get("metrics") or {}).get("checks") or [])
    checks += (sc.get("metrics_live") or {}).get("checks") or []
    out = []
    for c in checks:
        if c.get("score") is None or c["score"] >= 1:
            continue
        out.append({"check": c["id"], "kind": c.get("category"),
                    "refs": c.get("refs", []), "net": c.get("net"),
                    "pos": c.get("pos"), "severity": round(1 - c["score"], 4),
                    "failure_mode": None, "ladder": None})
    return out


def run(args) -> int:
    bdir = BRIEFS / args.brief
    if not (bdir / "brief.md").is_file():
        print(f"e2e_run: no brief {bdir}", file=sys.stderr)
        return 2, False
    started = dt.datetime.now(dt.timezone.utc)
    run_id = (f"{started:%Y%m%dT%H%M%SZ}-{args.brief}-{args.arm}"
              f"-s{args.seed}")
    root = Path(args.runs_root).expanduser() / run_id
    work = root / "work"
    (work / "boards").mkdir(parents=True)
    if args.arm == "hwde":
        dst = work / ".claude" / "skills" / "hwde"
        shutil.copytree(SKILL, dst, ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc"))
        for rel in SKILL_HIDE:
            (dst / rel).unlink(missing_ok=True)
        # SKILL.md runs scripts with .venv/bin/python from the repo root
        (work / ".venv").symlink_to(HOME / ".local" / "hwde-venv")
    cmd = ["claude", "-p", prompt(args.arm, (bdir / "brief.md").read_text(
               encoding="utf-8")),
           "--output-format", "json", "--permission-mode", "acceptEdits",
           "--allowedTools", *ALLOWED_TOOLS[args.arm],
           "--max-budget-usd", str(args.max_budget_usd)]
    if args.model:
        cmd += ["--model", args.model]
    t0 = time.monotonic()
    try:
        p = subprocess.run(sandbox_argv(work) + cmd, capture_output=True,
                           text=True, timeout=args.timeout_s)
        rc, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc, stdout, stderr = "timeout", e.stdout or "", e.stderr or ""
        stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
    wall = round(time.monotonic() - t0, 1)
    (root / "claude.json").write_text(stdout, encoding="utf-8")
    (root / "claude.err").write_text(stderr, encoding="utf-8")
    try:
        res = json.loads(stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {}
    ws = find_workspace(work, args.arm)
    sc = score(f"e2e_{args.brief}", ws, root / "score.json")
    rec = {
        "schema": 1, "kind": "run", "run_id": run_id,
        "hwde_commit": git_head(), "kicad": kicad_version(),
        "harness": "claude-code",
        "model": args.model or next(iter(res.get("modelUsage") or {}), None),
        "arm": args.arm, "fixture": f"e2e_{args.brief}", "seed": args.seed,
        "started": started.isoformat(timespec="seconds"), "wall_s": wall,
        "cost_usd": res.get("total_cost_usd"), "turns": res.get("num_turns"),
        "usage": res.get("usage"), "exit": rc,
        "budget_stopped": res.get("subtype") == "error_max_budget_usd",
        "workspace": str(ws) if ws else None,
        "composite": (sc or {}).get("composite"),
        "categories": ((sc or {}).get("e2e") or {}).get("categories"),
        "score_error": (sc or {}).get("error"),
        "findings": findings(sc), "dir": str(root),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print(json.dumps({k: rec[k] for k in (
        "run_id", "cost_usd", "wall_s", "composite", "budget_stopped",
        "exit")}), flush=True)
    return (0 if sc and "error" not in sc else 1), rec["budget_stopped"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--brief")
    ap.add_argument("--arm", choices=["bare", "hwde"], default="hwde")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seeds", type=int,
                    help="run seeds 1..N, stopping after a capped run")
    ap.add_argument("--model")
    ap.add_argument("--max-budget-usd", type=float, default=40.0)
    ap.add_argument("--timeout-s", type=int, default=6 * 3600)
    ap.add_argument("--runs-root", default="~/.local/state/hwde-evals/runs")
    ap.add_argument("--out", default=str(REPO / "evals" / "results.jsonl"))
    ap.add_argument("--probe", nargs="+")
    args = ap.parse_args(argv)
    if not shutil.which("bwrap"):
        print("e2e_run: bwrap not found", file=sys.stderr)
        return 2
    if args.probe:
        print(json.dumps(probe(args.probe), indent=1))
        return 0
    if not args.brief:
        ap.error("--brief is required for a run")
    if not args.seeds:
        return run(args)[0]
    worst = 0
    for seed in range(1, args.seeds + 1):
        args.seed = seed
        rc, capped = run(args)
        worst = max(worst, rc)
        if rc == 2:
            break
        if capped:
            print(f"e2e_run: seed {seed} hit the ${args.max_budget_usd:g} "
                  f"cap, pilot stopped", file=sys.stderr)
            break
    return worst


if __name__ == "__main__":
    sys.exit(main())
