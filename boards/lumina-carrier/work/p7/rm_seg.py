"""rm_seg.py - remove segments of a net whose endpoints match given points.

usage: python rm_seg.py <board.kicad_pcb> <net> <x1,y1> <x2,y2> [...]
Each pair of coordinate args is one segment (start, end), order-insensitive.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"

board = Path(sys.argv[1]).resolve()
net = sys.argv[2]
pts = [tuple(round(float(v), 4) for v in a.split(",")) for a in sys.argv[3:]]
want = {frozenset((pts[i], pts[i + 1])) for i in range(0, len(pts), 2)}

txt = board.read_text(encoding="utf-8")
ops = []
i = 0
while True:
    i = txt.find("\n\t(segment", i)
    if i < 0:
        break
    s, d, j = i + 1, 0, i + 1
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
    uu = re.search(r'\(uuid "([^"]+)"\)', blk)
    if nm and nm.group(1) == net:
        key = frozenset(((round(float(st.group(1)), 4), round(float(st.group(2)), 4)),
                         (round(float(en.group(1)), 4), round(float(en.group(2)), 4))))
        if key in want:
            ops.append({"op": "remove", "uuid": uu.group(1)})
    i = j
print("removing", len(ops), "segments of", net)
if not ops:
    raise SystemExit(1)
f = board.parent / (board.stem + "_rm_ops.json")
f.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
cp = subprocess.run([str(VENV), str(ROUTE_EDIT), "--pcb", str(board),
                     "--ops", str(f), "--out-report",
                     str(board.parent / (board.stem + "_rm.json"))],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace")
print((cp.stdout or cp.stderr)[-300:])
