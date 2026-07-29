"""rm_crumbs.py - delete sub-threshold track segments (KRT crumbs).

route_auto's own KRT mop-up does exactly this ("KRT can leave sub-grid crumbs
that KiCad flags track_dangling but sit below route_cleanup's touch tolerance;
removal is connectivity-safe: neighbouring round caps overlap far beyond the
crumb length"). Doing it as a separate step lets the board be re-exported to
Freerouting: FR 2.2.4 logs "Polyline: must contain at least 2 different points"
and then NPEs in PolylineTrace.combine_at_start on this copper.

usage: python rm_crumbs.py <board.kicad_pcb> [max_len_mm] [--dry-run]
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"

board = Path(sys.argv[1]).resolve()
limit = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2][0].isdigit() else 0.05
dry = "--dry-run" in sys.argv
txt = board.read_text(encoding="utf-8")

ops = []
kept = 0
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
    st = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", blk)
    en = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", blk)
    uu = re.search(r'\(uuid "([^"]+)"\)', blk)
    L = math.dist((float(st.group(1)), float(st.group(2))),
                  (float(en.group(1)), float(en.group(2))))
    if L < limit:
        ops.append({"op": "remove", "uuid": uu.group(1)})
    else:
        kept += 1
    i = j
print("segments < %.3f mm: %d (keeping %d)" % (limit, len(ops), kept))
if dry or not ops:
    raise SystemExit(0)
f = board.parent / (board.stem + "_crumb_ops.json")
f.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
cp = subprocess.run([str(VENV), str(ROUTE_EDIT), "--pcb", str(board),
                     "--ops", str(f), "--out-report",
                     str(board.parent / (board.stem + "_crumb.json"))],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace")
print((cp.stdout or cp.stderr)[-300:])
