"""mdi_chain.py - route the MDI pairs as a CHAIN, congested leg first.

Why not plain route_critical: each MDI net carries three pads (magjack J1,
ESD array D10, PHY U10). Handed all three at once, KRT builds a full mesh
(J1-D10, J1-U10, D10-U10) - a ring, ~2x the copper, 51 mm skew on RX.
route_critical's own answer is to detach the "unmatched stub pads", which on
this board are J1's staggered magjack pads, so its result covers only the
short D10 -> U10 leg and leaves the 38 mm J1 -> D10 haul uncoupled.

Here the chain is routed in two coupled legs, using route_critical's own
detach/restore helpers so no file is hand-edited:
  leg 1 (J1 detached):  D10 <-> U10  - the congested PHY fan-in, routed FIRST
                                       while the area is still empty
  leg 2 (U10 detached): J1  <-> D10  - the 38 mm open-board haul
Both legs try F.Cu alone first (In1.Cu GND is the reference plane, so no MDI
vias and no plane-split crossing); a leg that will not close on one layer
retries with B.Cu allowed at cost 3, which keeps the via count symmetric.

usage: python mdi_chain.py <in.kicad_pcb> <out.kicad_pcb>
"""
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import env  # noqa: E402
import route_critical as rc  # noqa: E402

PAIRS = [("/ETH_TXP", "/ETH_TXN"), ("/ETH_RXP", "/ETH_RXN")]
MDI = [n for pr in PAIRS for n in pr]
KRT = Path(env.find_krt())
# (track width, pair gap, layers, layer costs)
RUNGS = [
    (0.2597, 0.2104, ["F.Cu"], ["1"]),
    (0.2597, 0.2104, ["F.Cu", "B.Cu"], ["1", "3"]),
    (0.2000, 0.2000, ["F.Cu", "B.Cu"], ["1", "3"]),
]


def krt_pair(board, out, p, n, rung):
    w, g, layers, costs = rung
    args = [sys.executable, str(KRT / "route_diff.py"), str(board),
            "--output", str(out), "--no-fix-drc-settings",
            "--grid-step", "0.05", "--clearance", "0.2",
            "--via-size", "0.6", "--via-drill", "0.3",
            "--board-edge-clearance", "0.5",
            "--fab-overrides", str(board.parent / "fab_overrides.txt"),
            "--nets", p, n, "--layers", *layers, "--layer-costs", *costs,
            "--track-width", "%g" % w, "--diff-pair-gap", "%g" % g]
    cp = subprocess.run(args, cwd=str(KRT), capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=900)
    summary = rc.parse_summary(cp.stdout or "") or {}
    rep = (summary.get("pair_reports") or [{}])[0]
    return rep.get("outcome"), summary.get("total_vias"), cp.returncode


def leg(board, work, detach_ref, tag):
    """Route both pairs with detach_ref's MDI pads temporarily netless."""
    text = board.read_text(encoding="utf-8")
    detached, restores = rc.detach_stub_pads(
        text, [(detach_ref, net) for net in MDI])
    cur = work / ("%s_in.kicad_pcb" % tag)
    cur.write_text(detached, encoding="utf-8")
    for i, (p, n) in enumerate(PAIRS, 1):
        for r, rung in enumerate(RUNGS, 1):
            out = work / ("%s_%d_r%d.kicad_pcb" % (tag, i, r))
            outcome, vias, rcode = krt_pair(cur, out, p, n, rung)
            print("   %s %s rung%d %s vias=%s rc=%s"
                  % (tag, p.split("_")[-1], r, outcome, vias, rcode))
            if outcome == "coupled" and out.is_file():
                cur = out
                break
        else:
            print("   %s %s: NO RUNG CLOSED - leaving to the next stage"
                  % (tag, p))
    final = work / ("%s_done.kicad_pcb" % tag)
    final.write_text(rc.restore_stub_pads(cur.read_text(encoding="utf-8"),
                                          restores), encoding="utf-8")
    return final


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    work = src.parent
    b = work / "chain_start.kicad_pcb"
    shutil.copy2(src, b)
    print("leg 1: D10 <-> U10 (J1 detached)")
    b = leg(b, work, "J1", "legA")
    print("leg 2: J1 <-> D10 (U10 detached)")
    b = leg(b, work, "U10", "legB")
    shutil.copy2(b, dst)
    print("wrote", dst)


if __name__ == "__main__":
    main()
