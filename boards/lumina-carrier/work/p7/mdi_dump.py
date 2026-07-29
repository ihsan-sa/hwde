"""mdi_dump.py - per-net segment inventory for the four MDI nets.

Groups each net's F.Cu/B.Cu segments into connected chains and reports which
pads each chain touches, so a broken chain (J1 leg present, U10 leg missing)
is visible without opening pcbnew.

usage: python mdi_dump.py <board.kicad_pcb>
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import LineString  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

MDI = ("/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN")
board = Path(sys.argv[1])
txt = board.read_text(encoding="utf-8")
bg = geom.BoardGeom.from_file(str(board))

segs = {n: [] for n in MDI}
i = 0
while True:
    i = txt.find("\n\t(segment", i)
    if i < 0:
        break
    s = i + 1
    d = 0
    j = s
    while j < len(txt):
        if txt[j] == "(":
            d += 1
        elif txt[j] == ")":
            d -= 1
            if d == 0:
                break
        j += 1
    blk = txt[s:j + 1]
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    st = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", blk)
    en = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", blk)
    ly = re.search(r'\(layer "([^"]+)"\)', blk)
    if nm and nm.group(1) in MDI:
        segs[nm.group(1)].append(
            (ly.group(1), (float(st.group(1)), float(st.group(2))),
             (float(en.group(1)), float(en.group(2)))))
    i = j

for n in MDI:
    ss = segs[n]
    lines = [LineString([a, b]) for _l, a, b in ss if a != b]
    merged = unary_union([ln.buffer(0.03, quad_segs=2) for ln in lines])
    parts = list(getattr(merged, "geoms", [merged]))
    pads = list(bg.pads_of(net=n))
    print("%s  segments=%d  chains=%d  total=%.2f mm" % (
        n, len(ss), len(parts),
        sum(ln.length for ln in lines)))
    for k, part in enumerate(parts):
        touched = [f"{p.ref}.{p.number}" for p in pads
                   if p.poly.buffer(0.05).intersects(part)]
        seg_len = sum(ln.length for ln in lines if ln.intersects(part))
        print("    chain %d: %.2f mm, pads %s" % (k, seg_len, touched or ["-"]))
    print("    pads:", [f"{p.ref}.{p.number}@{p.center[0]:.1f},{p.center[1]:.1f}"
                        for p in pads])
