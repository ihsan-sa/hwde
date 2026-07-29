"""krt_finish.py - route remaining nets with KRT route.py, driven by a JSON job.

WHY A JOB FILE: every net name on this board starts with "/" and Git-Bash
rewrites a leading "/" into a Windows path, so net names must never reach argv.
The job file carries them instead.

TWO TRAPS this driver exists to avoid:

1. `--clearance` is a CEILING, not a floor. KRT auto-reads the .kicad_pro
   netclasses and caps each at min(class, --clearance). Every PWR_* class on this
   board carries clearance 0.2 - the 0.635 mm 48 V number lives ONLY in the
   hand-written .kicad_dru, which KRT cannot read - so an auto-read run prices
   V48_RAW/+48V_SW/V48_RTN obstacles at 0.2 mm and ships HV violations (the P7
   "480 HV errors" failure). An EXPLICIT --net-clearances file is NOT capped
   (route.py only caps the auto-read path), so HV nets can be pinned at 0.635 mm
   while everything else keeps the 0.2 mm Default floor; KRT grades every pair at
   max(A_class, B_class).
   BUT: the DRU deliberately EXEMPTS same-footprint copper inside U1/U20/U22/
   C1/C61-63 courtyards, and KRT cannot model that exemption - pinning 0.635 mm
   globally boxes in exactly the U22 pin escapes the DRU exempts. So `hv_clr` is
   a per-job knob: 0.635 for board-area routing, 0.2 for the U22-local escapes
   (whose result must then be re-checked by kicad-cli DRC, the only oracle).

2. Freerouting is unusable on this board (NPE in
   PolylineTrace.combine_at_start on the MDI copper), so KRT is the only router.

Inner layers default to routing-FORBIDDEN (layer_costs 1.0 -1 -1 3.0): In1 is the
MDI pairs' GND reference and In2 is the power plane. Through vias still span them.

job JSON keys (all optional except one of nets/from_drc):
  from_drc   : path to a kc.py drc report -> route its unconnected nets
  nets       : explicit net-name list (overrides from_drc)
  only/skip  : filters applied to the resulting list
  rip        : net names KRT may rip and re-route this run
  grid       : --grid-step (default 0.05)
  clearance  : --clearance ceiling (default 0.2)
  track      : --track-width (default: omitted -> per-netclass width)
  hv_clr     : clearance pinned on V48_RAW/+48V_SW/V48_RTN (default 0.635)
  layers     : default [F.Cu, In1.Cu, In2.Cu, B.Cu]
  layer_costs: default [1.0, -1, -1, 3.0]
  extra      : extra route.py argv (no net names!)
  timeout    : seconds (default 3000)

usage: python krt_finish.py <job.json> <out.kicad_pcb>
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import env  # noqa: E402
import route_critical as rc  # noqa: E402

HERE = Path(__file__).resolve().parent
HV = ["V48_RAW", "+48V_SW", "V48_RTN"]
DIFF = ["/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"]

job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2]).resolve()
board = Path(job.get("pcb") or
             REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"
             ).resolve()

nets = list(job.get("nets") or [])
if not nets and job.get("from_drc"):
    d = json.loads(Path(job["from_drc"]).read_text(encoding="utf-8"))
    viol = d.get("violations") or d.get("failing") or []
    nets = sorted({v["net"] for v in viol
                   if v.get("check") == "unconnected_items" and v.get("net")})
if job.get("only"):
    nets = [n for n in nets if n in set(job["only"])]
if job.get("skip"):
    nets = [n for n in nets if n not in set(job["skip"])]
if not nets:
    print("no nets to route")
    sys.exit(0)
print("routing %d net(s): %s" % (len(nets), nets))

hv_clr = float(job.get("hv_clr", 0.635))
clrs = {n: hv_clr for n in HV}
clrs.update({n: 0.15 for n in DIFF})
clr_file = HERE / (out.stem + "_netclr.json")
clr_file.write_text(json.dumps(clrs, indent=1), encoding="utf-8")

floors = rc.grading_floors(board.with_suffix(".kicad_pro"))
floors["clearance"] = float(job.get("fab_clearance", 0.2))
fab = rc.write_fab_overrides(HERE, floors)
krt = Path(env.find_krt())

args = [sys.executable, str(krt / "route.py"), str(board),
        "--output", str(out), "--no-fix-drc-settings",
        "--grid-step", str(job.get("grid", 0.05)),
        "--clearance", str(job.get("clearance", 0.2)),
        "--net-clearances", str(clr_file),
        "--via-size", str(job.get("via_size", 0.6)),
        "--via-drill", str(job.get("via_drill", 0.3)),
        "--board-edge-clearance", str(floors["edge_clearance"]),
        "--fab-overrides", str(fab),
        "--layers", *job.get("layers", ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]),
        "--layer-costs", *[str(c) for c in
                           job.get("layer_costs", [1.0, -1, -1, 3.0])]]
if job.get("track"):
    args += ["--track-width", str(job["track"])]
if job.get("rip"):
    args += ["--rip-existing-nets", *job["rip"]]
args += job.get("extra", [])
args += ["--nets", *nets]

cp = subprocess.run(args, cwd=str(krt), capture_output=True, text=True,
                    encoding="utf-8", errors="replace",
                    timeout=int(job.get("timeout", 3000)))
log = HERE / (out.stem + "_krt.log")
log.write_text(cp.stdout or "", encoding="utf-8")
lines = (cp.stdout or "").strip().splitlines()
for ln in lines:
    if ln.startswith("JSON_SUMMARY:"):
        s = json.loads(ln[len("JSON_SUMMARY:"):])
        print("routed=%s failed=%s vias=%s"
              % (s.get("successful"), s.get("failed"), s.get("total_vias")))
        print("  ok    :", s.get("routed_single"))
        print("  failed:", s.get("failed_single"))
        mp = s.get("failed_multipoint") or []
        if mp:
            print("  failed multipoint:",
                  [(m["net_name"], len(m["failed_pads"])) for m in mp])
print("log:", log)
if cp.returncode != 0:
    print("RC=%s STDERR: %s" % (cp.returncode, (cp.stderr or "")[-1200:]))
