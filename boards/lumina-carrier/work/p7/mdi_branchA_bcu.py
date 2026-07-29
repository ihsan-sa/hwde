"""mdi_branchA_bcu.py - fallback: route the D10 <-> U10 leg with B.Cu preferred.

The two MDI legs have to be routed on separate branches from the same clean
board (KRT defers whichever leg runs second), so the branches cannot see each
other's copper. Measured at P7: with both legs preferring F.Cu the TX branches
overlap just south of D10 and merge into a short. Forcing the short PHY leg
onto B.Cu (cost 1) with F.Cu only as an escape layer (cost 3) makes the two
branches geometrically disjoint - which is exactly why RX merged cleanly, its
PHY leg already went to B.Cu.

usage: python mdi_branchA_bcu.py <clean.kicad_pcb> <out.kicad_pcb>
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mdi_chain as mc  # noqa: E402

mc.RUNGS = [
    (0.2597, 0.2104, ["F.Cu", "B.Cu"], ["3", "1"]),
    (0.2000, 0.2000, ["F.Cu", "B.Cu"], ["3", "1"]),
]

src, dst = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
work = src.parent
start = work / "bcuA_start.kicad_pcb"
shutil.copy2(src, start)
print("branch A (B.Cu preferred): D10 <-> U10, J1 detached")
out = mc.leg(start, work, "J1", "bcuA")
shutil.copy2(out, dst)
print("wrote", dst)
