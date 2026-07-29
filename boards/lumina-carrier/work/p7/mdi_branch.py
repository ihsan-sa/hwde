"""mdi_branch.py - find junctions / stubs in a net's routed copper.

check_diffpair falls back to TOTAL copper length when a net is not
branch-free, which turns a small stub into a bogus 45 mm "skew". This locates
the junction nodes (degree >= 3) and the dead-end nodes that touch no pad.

usage: python mdi_branch.py <board.kicad_pcb> [net ...]
"""
import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402

board = Path(sys.argv[1])
nets = sys.argv[2:] or ["/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"]
txt = board.read_text(encoding="utf-8")
bg = geom.BoardGeom.from_file(str(board))


def blocks(tag):
    i = 0
    while True:
        i = txt.find("\n\t(%s" % tag, i)
        if i < 0:
            return
        s, d, j = i + 1, 0, i + 1
        while j < len(txt):
            if txt[j] == "(":
                d += 1
            elif txt[j] == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        yield txt[s:j + 1]
        i = j


seg = collections.defaultdict(list)
via = collections.defaultdict(list)
for blk in blocks("segment"):
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    if not nm or nm.group(1) not in nets:
        continue
    st = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", blk)
    en = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", blk)
    ly = re.search(r'\(layer "([^"]+)"\)', blk)
    uu = re.search(r'\(uuid "([^"]+)"\)', blk)
    seg[nm.group(1)].append(
        (ly.group(1), (round(float(st.group(1)), 3), round(float(st.group(2)), 3)),
         (round(float(en.group(1)), 3), round(float(en.group(2)), 3)),
         uu.group(1)))
for blk in blocks("via"):
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    if nm and nm.group(1) in nets:
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", blk)
        via[nm.group(1)].append((round(float(at.group(1)), 3),
                                 round(float(at.group(2)), 3)))

for n in nets:
    deg = collections.Counter()
    for _ly, a, b, _u in seg[n]:
        deg[a] += 1
        deg[b] += 1
    pads = list(bg.pads_of(net=n))
    vias = set(via[n])
    print("== %s  segments=%d vias=%d" % (n, len(seg[n]), len(via[n])))
    for pt, d in sorted(deg.items()):
        if d == 2:
            continue
        on_pad = [f"{p.ref}.{p.number}" for p in pads
                  if p.poly.buffer(0.05).contains(geom.Point(*pt))]
        on_via = pt in vias
        kind = "JUNCTION" if d >= 3 else "END"
        print("   %-9s deg=%d %-18s pad=%s via=%s"
              % (kind, d, str(pt), on_pad or "-", on_via))
