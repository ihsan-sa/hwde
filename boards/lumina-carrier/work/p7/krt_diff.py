"""krt_diff.py - run KRT route_diff.py on one pair WITHOUT route_critical's
stub-pad detach.

route_critical detaches "unmatched stub pads" before handing a pair to KRT.
On this board check_diffpair.matched_terminals() does not pair J1's staggered
magjack pads, so J1's MDI pads were detached and the whole J1 -> D10 leg
(~38 mm, the long haul) was never routed as a coupled pair. This driver keeps
every pad attached and pins the pair to F.Cu (In1.Cu GND is its reference,
so no MDI vias and no plane-split crossing).

usage: python krt_diff.py <in.kicad_pcb> <out.kicad_pcb> <netP> <netN>
       [extra KRT args...]
Args go to subprocess as a LIST (LEARNINGS [parts][python]: net names like
"/ETH_TXP" get MSYS-path-mangled through a shell).
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import env  # noqa: E402

krt = env.find_krt()
PAIRS = {"tx": ("/ETH_TXP", "/ETH_TXN"), "rx": ("/ETH_RXP", "/ETH_RXN")}
inp, out, key = sys.argv[1:4]
p, n = PAIRS[key]   # never via argv: MSYS mangles a leading "/" into a path
work = Path(inp).parent
args = [sys.executable, str(Path(krt) / "route_diff.py"), inp,
        "--output", out, "--no-fix-drc-settings",
        "--grid-step", "0.05",
        "--clearance", "0.2",
        "--via-size", "0.5", "--via-drill", "0.3",
        "--board-edge-clearance", "0.5",
        "--fab-overrides", str(work / "fab_overrides.txt"),
        "--nets", p, n,
        "--layers", "F.Cu", "--layer-costs", "1",
        "--track-width", "0.2597", "--diff-pair-gap", "0.2104"] + sys.argv[4:]
cp = subprocess.run(args, cwd=str(krt), capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=900)
tail = (cp.stdout or "").strip().splitlines()
print("\n".join(tail[-25:]))
if cp.returncode != 0:
    print("STDERR:", (cp.stderr or "")[-1500:])
sys.exit(cp.returncode)
