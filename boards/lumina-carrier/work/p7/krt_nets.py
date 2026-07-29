"""krt_nets.py - route an explicit net list with KRT route.py.

Two-stage P7 routing: the three 48 V nets first, at their own 0.635 mm
clearance (ICD-01 s5.1 / the HV_48V_* DRU rules) and with the inner plane
layers FORBIDDEN, then everything else at the 0.2 mm Default clearance.
Doing both in one call makes KRT search the whole board at the HV clearance.

usage: python krt_nets.py <board> <out> hv|rest <drc_report.json> [extra...]
Net names never come from argv (Git-Bash mangles a leading "/").
"""
import json
import sys
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import env  # noqa: E402
import route_critical as rc  # noqa: E402

HV = ["V48_RAW", "V48_RTN", "+48V_SW"]
board, out, which, report = (Path(sys.argv[1]).resolve(),
                             Path(sys.argv[2]).resolve(), sys.argv[3],
                             Path(sys.argv[4]).resolve())
extra = sys.argv[5:]
work = board.parent

drc = json.loads(report.read_text(encoding="utf-8"))
unrouted = sorted({v["net"] for v in drc["violations"]
                   if v.get("check") == "unconnected_items" and v.get("net")})
if which == "hv":
    nets = [n for n in unrouted if n in HV]
    clearance = "0.635"
else:
    nets = [n for n in unrouted if n not in HV]
    clearance = "0.2"
print(which, "nets:", len(nets), nets if which == "hv" else "")

floors = rc.grading_floors(board.with_suffix(".kicad_pro"))
floors["clearance"] = 0.2
fab = rc.write_fab_overrides(work, floors)
krt = Path(env.find_krt())
args = [sys.executable, str(krt / "route.py"), str(board),
        "--output", str(out), "--no-fix-drc-settings",
        "--grid-step", "0.05",
        "--via-size", "0.6", "--via-drill", "0.3",
        "--board-edge-clearance", str(floors["edge_clearance"]),
        "--fab-overrides", str(fab),
        "--layers", "F.Cu", "In1.Cu", "In2.Cu", "B.Cu",
        "--layer-costs", "1.0", "-1", "-1", "3.0",
        "--clearance", clearance,
        "--nets", *nets] + extra
cp = subprocess.run(args, cwd=str(krt), capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=2400)
print("\n".join((cp.stdout or "").strip().splitlines()[-18:]))
if cp.returncode != 0:
    print("STDERR:", (cp.stderr or "")[-1200:])
