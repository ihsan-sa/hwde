"""krt_bulk.py - route the remaining nets with KRT route.py.

Freerouting 2.2.4 wedges on this board: rung1.log shows
"Polyline: must contain at least 2 different points" and an NPE in
PolylineTrace.combine_at_start while normalising the KRT-routed MDI copper,
after which the JVM hangs to the rung timeout (LEARNINGS 2026-07-23
[freerouting][routing]). route_auto's own KRT mop-up only targets the nets
implicated in DRC errors and keeps its result only if the error count strictly
improves, which is the wrong shape for "route the whole remainder", so this
drives KRT directly over the full unrouted set.

usage: python krt_bulk.py <board.kicad_pcb> <drc_report.json> <out.kicad_pcb>
       [extra route.py args...]
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import env  # noqa: E402
import route_critical as rc  # noqa: E402

board, report, out = (Path(p).resolve() for p in sys.argv[1:4])
extra = sys.argv[4:]
work = board.parent

drc = json.loads(report.read_text(encoding="utf-8"))
nets = sorted({v["net"] for v in drc["violations"]
               if v.get("check") == "unconnected_items" and v.get("net")})
print("unrouted nets:", len(nets))

pro = board.with_suffix(".kicad_pro")
floors = rc.grading_floors(pro if pro.is_file() else None)
# grading_floors takes the WIDEST netclass clearance, which is the 48 V
# classes' 0.635 mm. Feeding that to write_fab_overrides would pin KRT's hard
# fab floor to 0.635 mm for EVERY net - unroutable. The per-net map (auto-read
# from the .kicad_pro netclasses, capped by --clearance) is what carries the
# 48 V number; the fab floor stays at the Default class.
floors["clearance"] = 0.2
print("floors:", floors)
fab = rc.write_fab_overrides(work, floors)
krt = Path(env.find_krt())

args = [sys.executable, str(krt / "route.py"), str(board),
        "--output", str(out), "--no-fix-drc-settings",
        "--grid-step", "0.05",
        "--clearance", str(floors["clearance"]),
        "--via-size", "0.6", "--via-drill", "0.3",
        "--board-edge-clearance", str(floors["edge_clearance"]),
        "--fab-overrides", str(fab),
        "--nets", *nets] + extra
cp = subprocess.run(args, cwd=str(krt), capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=3000)
tail = (cp.stdout or "").strip().splitlines()
print("\n".join(tail[-30:]))
if cp.returncode != 0:
    print("STDERR:", (cp.stderr or "")[-1500:])
summary = rc.parse_summary(cp.stdout or "")
if summary:
    print("SUMMARY:", json.dumps({k: v for k, v in summary.items()
                                  if not isinstance(v, list)}))
