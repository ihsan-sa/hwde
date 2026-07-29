"""trim_dangle.py - remove dangling stub copper on named nets ONLY.

route_cleanup is banned on this board (its loop-breaker regressed twice at S14),
so this is the narrow substitute: iteratively drop segments whose endpoint has
degree 1 and does not sit inside a pad or via of the same net. Nothing else is
touched, and only the nets named on the command line are considered, so it cannot
wander into the MDI pairs or the 48 V copper.

Every removal goes through route_edit (atomic + verified), and the caller must
re-run kicad-cli DRC afterwards - that is the only oracle for whether the net is
still connected.

usage: python trim_dangle.py NET [NET ...] [--pcb P] [--dry-run]
"""
import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import Point  # noqa: E402

HERE = Path(__file__).resolve().parent
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"
BS = "\\"


def blocks(t, tok):
    i = 0
    while True:
        i = t.find("(" + tok, i)
        if i < 0:
            return
        j, d, q = i, 0, False
        while j < len(t):
            c = t[j]
            if c == '"' and t[j - 1] != BS:
                q = not q
            elif not q:
                if c == "(":
                    d += 1
                elif c == ")":
                    d -= 1
                    if d == 0:
                        yield t[i:j + 1]
                        break
            j += 1
        i = j + 1


ap = argparse.ArgumentParser()
ap.add_argument("nets", nargs="+")
ap.add_argument("--pcb", default=str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
board = Path(a.pcb)
nets = set(a.nets)

bg = geom.BoardGeom.from_file(str(board))
anchors = collections.defaultdict(list)      # net -> [shapely geom]
for p in bg.pads_of():
    if p.net in nets:
        anchors[p.net].append(p.poly)
for v in bg.vias_of():
    if v.net in nets:
        anchors[v.net].append(v.poly)

txt = board.read_text(encoding="utf-8")
segs = []            # (uuid, net, p1, p2)
for blk in blocks(txt, "segment"):
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    if not nm or nm.group(1) not in nets:
        continue
    st = re.search(r"\(start ([-\d.]+) ([-\d.]+)", blk)
    en = re.search(r"\(end ([-\d.]+) ([-\d.]+)", blk)
    uu = re.search(r'\(uuid "([^"]+)"', blk)
    segs.append((uu.group(1), nm.group(1),
                 (round(float(st.group(1)), 4), round(float(st.group(2)), 4)),
                 (round(float(en.group(1)), 4), round(float(en.group(2)), 4))))

alive = {s[0]: s for s in segs}
removed = []
while True:
    deg = collections.Counter()
    for u, net, p1, p2 in alive.values():
        deg[(net, p1)] += 1
        deg[(net, p2)] += 1
    drop = []
    for u, net, p1, p2 in alive.values():
        for p in (p1, p2):
            if deg[(net, p)] != 1:
                continue
            pt = Point(*p)
            if any(g.buffer(0.02).contains(pt) for g in anchors[net]):
                continue
            drop.append(u)
            break
    if not drop:
        break
    for u in drop:
        removed.append(alive.pop(u))

print("dangling stub segments to remove: %d" % len(removed))
for u, net, p1, p2 in removed:
    print("   %-10s %s -> %s  %s" % (net, p1, p2, u))
if not removed or a.dry_run:
    sys.exit(0)
f = HERE / "trim_dangle_ops.json"
f.write_text(json.dumps({"version": 1,
                         "ops": [{"op": "remove", "uuid": u}
                                 for u, _, _, _ in removed]}, indent=1),
             encoding="utf-8")
cp = subprocess.run(
    [str(VENV), str(ROUTE_EDIT), "--pcb", str(board), "--ops", str(f),
     "--out-report", str(HERE / "trim_dangle_report.json")],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
print((cp.stdout or cp.stderr)[-600:])
sys.exit(cp.returncode)
