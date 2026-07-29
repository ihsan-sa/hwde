"""simplify_tracks.py - drop degenerate segments and merge collinear runs.

Freerouting 2.2.4 wedges reading KRT copper: rung1.log shows
"WARN Polyline: must contain at least 2 different points" and then an NPE in
PolylineTrace.combine_at_start during normalize_traces, after which the JVM
hangs until the rung timeout (LEARNINGS 2026-07-23 [freerouting][routing]).
KRT emits zero-length crumbs and long chains of exactly-collinear segments;
both are what FR is choking on.

This removes zero-length segments and merges runs of exactly-collinear
segments that meet at a degree-2 node (same net, same layer, same width).
Geometry is preserved exactly - only the segment count changes.

usage: python simplify_tracks.py <board.kicad_pcb> [--dry-run]
"""
import collections
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"

EPS_LEN = 1e-4          # mm: shorter than this is degenerate
EPS_CROSS = 1e-6        # collinearity tolerance on the normalized cross product

board = Path(sys.argv[1]).resolve()
dry = "--dry-run" in sys.argv
txt = board.read_text(encoding="utf-8")

segs = []
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
    w = re.search(r"\(width ([\d.]+)\)", blk)
    ly = re.search(r'\(layer "([^"]+)"\)', blk)
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    uu = re.search(r'\(uuid "([^"]+)"\)', blk)
    segs.append({"a": (float(st.group(1)), float(st.group(2))),
                 "b": (float(en.group(1)), float(en.group(2))),
                 "w": float(w.group(1)), "layer": ly.group(1),
                 "net": nm.group(1) if nm else "", "uuid": uu.group(1)})
    i = j
print("segments on board:", len(segs))

ops = []
# 1. degenerate
alive = []
for s in segs:
    if math.dist(s["a"], s["b"]) < EPS_LEN:
        ops.append({"op": "remove", "uuid": s["uuid"]})
    else:
        alive.append(s)
print("degenerate (zero-length) segments:", len(ops))

# 2. collinear merge, per (net, layer, width)
vias = set()
i = 0
while True:
    i = txt.find("\n\t(via", i)
    if i < 0:
        break
    at = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", txt[i:i + 400])
    vias.add((round(float(at.group(1)), 6), round(float(at.group(2)), 6)))
    i += 6

groups = collections.defaultdict(list)
for s in alive:
    groups[(s["net"], s["layer"], s["w"])].append(s)

merges = 0
for key, gs in groups.items():
    deg = collections.Counter()
    for s in gs:
        deg[tuple(round(c, 6) for c in s["a"])] += 1
        deg[tuple(round(c, 6) for c in s["b"])] += 1
    # global degree over ALL nets/layers at that point (a junction with another
    # group's segment, a via, or a pad tap must not be merged away)
    gdeg = collections.Counter()
    for s in alive:
        if s["net"] != key[0]:
            continue
        gdeg[tuple(round(c, 6) for c in s["a"])] += 1
        gdeg[tuple(round(c, 6) for c in s["b"])] += 1
    by_pt = collections.defaultdict(list)
    for s in gs:
        by_pt[tuple(round(c, 6) for c in s["a"])].append(s)
        by_pt[tuple(round(c, 6) for c in s["b"])].append(s)
    used = set()
    for pt, touching in by_pt.items():
        if len(touching) != 2 or gdeg[pt] != 2 or pt in vias:
            continue
        s1, s2 = touching
        if s1["uuid"] in used or s2["uuid"] in used:
            continue
        o1 = s1["b"] if tuple(round(c, 6) for c in s1["a"]) == pt else s1["a"]
        o2 = s2["b"] if tuple(round(c, 6) for c in s2["a"]) == pt else s2["a"]
        v1 = (pt[0] - o1[0], pt[1] - o1[1])
        v2 = (o2[0] - pt[0], o2[1] - pt[1])
        n1 = math.hypot(*v1)
        n2 = math.hypot(*v2)
        if n1 == 0 or n2 == 0:
            continue
        cross = (v1[0] * v2[1] - v1[1] * v2[0]) / (n1 * n2)
        dot = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
        if abs(cross) > EPS_CROSS or dot <= 0:
            continue
        ops.append({"op": "remove", "uuid": s1["uuid"]})
        ops.append({"op": "remove", "uuid": s2["uuid"]})
        ops.append({"op": "add_track", "start": list(o1), "end": list(o2),
                    "width": key[2], "layer": key[1], "net": key[0]})
        used.update({s1["uuid"], s2["uuid"]})
        merges += 1
print("collinear pairs merged:", merges)
print("total ops:", len(ops))
if dry or not ops:
    raise SystemExit(0)
f = board.parent / (board.stem + "_simplify_ops.json")
f.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
cp = subprocess.run([str(VENV), str(ROUTE_EDIT), "--pcb", str(board),
                     "--ops", str(f), "--out-report",
                     str(board.parent / (board.stem + "_simplify.json"))],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace")
print((cp.stdout or cp.stderr)[-400:])
