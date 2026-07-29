"""mdi_join.py - stitch the two grafted MDI legs together inside their shared pad.

The J1<->D10 and D10<->U10 legs are routed on separate branches, so each
lands on the shared D10 pad at its own point. The copper is electrically one
net (both points sit on the pad), but check_diffpair's path walker sees two
chains and reports "not branch-free", which makes it fall back to TOTAL copper
length and invent a 45 mm skew. A short segment joining the two endpoints
inside the pad makes the walk single-path again. Purely cosmetic copper -
it never leaves the pad it is drawn on.

usage: python mdi_join.py <board.kicad_pcb>   (edits in place via route_edit)
"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import Point  # noqa: E402

MDI = ("/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN")
WIDTH = 0.2597
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"

board = Path(sys.argv[1]).resolve()
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


ends = collections.defaultdict(collections.Counter)   # net -> point -> degree
layer_of = {}
for blk in blocks("segment"):
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    if not nm or nm.group(1) not in MDI:
        continue
    st = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", blk)
    en = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", blk)
    ly = re.search(r'\(layer "([^"]+)"\)', blk)
    for m in (st, en):
        p = (round(float(m.group(1)), 4), round(float(m.group(2)), 4))
        ends[nm.group(1)][p] += 1
        layer_of.setdefault((nm.group(1), p), set()).add(ly.group(1))

ops = []
for net in MDI:
    pads = list(bg.pads_of(net=net))
    tips = [p for p, d in ends[net].items() if d == 1]
    by_pad = collections.defaultdict(list)
    for t in tips:
        for pad in pads:
            if pad.poly.buffer(0.02).contains(Point(*t)):
                by_pad["%s.%s" % (pad.ref, pad.number)].append(t)
                break
    for pad_id, pts in sorted(by_pad.items()):
        if len(pts) < 2:
            continue
        pts.sort()
        for a, b in zip(pts, pts[1:]):
            layers = layer_of[(net, a)] & layer_of[(net, b)] or {"F.Cu"}
            lay = "F.Cu" if "F.Cu" in layers else sorted(layers)[0]
            print("join %-10s %-8s %s -> %s on %s" % (net, pad_id, a, b, lay))
            ops.append({"op": "add_track", "start": list(a), "end": list(b),
                        "width": WIDTH, "layer": lay, "net": net})

if not ops:
    print("nothing to join")
    raise SystemExit(0)
ops_file = board.parent / (board.stem + "_join_ops.json")
ops_file.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
cp = subprocess.run(
    [str(VENV), str(ROUTE_EDIT), "--pcb", str(board), "--ops", str(ops_file),
     "--out-report", str(board.parent / (board.stem + "_join.json"))],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
print((cp.stdout or cp.stderr)[-400:])
