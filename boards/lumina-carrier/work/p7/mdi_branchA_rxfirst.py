"""mdi_branchA_rxfirst.py - branch A (D10 <-> U10) with RX routed FIRST, F.Cu only.

check_return_path takes the reference net from constraints.high_speed
(`GND` here), and the plane adjacent to B.Cu is In2.Cu = +3V3 - so ANY MDI
copper on B.Cu is a return-path ERROR with no waiver (measured pre-route:
14-22 mm2 of deficit per B.Cu segment). The RX leg only fell to B.Cu because
TX was routed first and took the F.Cu channel. RX is the harder pair (it has
to clear C34/C35 to reach U10 pins 5/6 from below), so it goes first.

usage: python mdi_branchA_rxfirst.py <clean.kicad_pcb> <out.kicad_pcb>
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mdi_chain as mc  # noqa: E402

mc.PAIRS = [("/ETH_RXP", "/ETH_RXN"), ("/ETH_TXP", "/ETH_TXN")]
mc.RUNGS = [(0.2597, 0.2104, ["F.Cu"], ["1"])]

src, dst = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
work = src.parent
start = work / "rxfA_start.kicad_pcb"
shutil.copy2(src, start)
print("branch A (RX first, F.Cu only): D10 <-> U10, J1 detached")
out = mc.leg(start, work, "J1", "rxfA")
shutil.copy2(out, dst)
print("wrote", dst)
