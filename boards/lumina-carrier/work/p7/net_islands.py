"""net_islands.py - electrical islands of one net, item by item, WITH uuids.

Why: kicad-cli DRC names only ONE representative pair per unconnected net, so
"pad 3 <-> pad 9" does not say which of the two is the orphan, nor what the
other items of that net are already tied to. This builds the same graph DRC
builds (pads/tracks/vias touching on a shared layer, vias bridging all layers,
zone fills as connectors) and prints every island with its members.

It parses the .kicad_pcb text directly rather than going through lib/geom,
because geom's Track/Via dataclasses drop the uuid and route_edit's `remove`
op needs it.

Net names are read from argv[1]; call through `python -c` with an explicit
sys.argv so Git-Bash cannot mangle the leading "/".

usage: python net_islands.py <net> [--pcb P] [--no-zones] [--near x,y]
"""
import argparse
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402

CU = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
BS = "\\"


def blocks(t, tok, st=0, en=None):
    en = len(t) if en is None else en
    i, pat = st, "(" + tok
    while True:
        i = t.find(pat, i, en)
        if i < 0:
            return
        j, d, q = i, 0, False
        while j < en:
            c = t[j]
            if c == '"' and t[j - 1] != BS:
                q = not q
            elif not q:
                if c == "(":
                    d += 1
                elif c == ")":
                    d -= 1
                    if d == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


ap = argparse.ArgumentParser()
ap.add_argument("net")
ap.add_argument("--pcb", default=str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
ap.add_argument("--no-zones", action="store_true")
a = ap.parse_args()

txt = Path(a.pcb).read_text(encoding="utf-8")
items = []   # (label, poly, set(layers), kind)

# --- pads (via lib/geom, which already does footprint rotation correctly) ---
bg = geom.BoardGeom.from_file(a.pcb)
for p in bg.pads_of():
    if (p.net or "") != a.net:
        continue
    lys = {x for x in (p.layers or []) if x in CU} or set(CU)
    items.append(("PAD %s.%s @(%.4f,%.4f) %s"
                  % (p.ref, p.number, p.center[0], p.center[1],
                     ",".join(sorted(lys))), p.poly, lys, "pad"))

# --- tracks / arcs / vias from the raw text, so uuids survive ---------------
for tag in ("segment", "arc", "via"):
    for (s, e) in blocks(txt, "\n\t(" + tag if False else tag):
        blk = txt[s:e]
        nm = re.search(r'\(net "([^"]*)"\)', blk)
        if not nm or nm.group(1) != a.net:
            continue
        uu = re.search(r'\(uuid "([^"]+)"\)', blk)
        uid = uu.group(1) if uu else "?"
        if tag == "via":
            at = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            sz = re.search(r"\(size\s+([\d.]+)", blk)
            if not (at and sz):
                continue
            x, y, d = float(at.group(1)), float(at.group(2)), float(sz.group(1))
            items.append(("VIA    @(%.4f,%.4f) d%.2f  %s" % (x, y, d, uid),
                          Point(x, y).buffer(d / 2.0, 32), set(CU), "via"))
        else:
            st = re.search(r"\(start\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            en2 = re.search(r"\(end\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            w = re.search(r"\(width\s+([\d.]+)", blk)
            ly = re.search(r'\(layer "([^"]+)"', blk)
            if not (st and en2 and w and ly):
                continue
            x1, y1 = float(st.group(1)), float(st.group(2))
            x2, y2 = float(en2.group(1)), float(en2.group(2))
            wd = float(w.group(1))
            if math.hypot(x2 - x1, y2 - y1) < 1e-9:
                g = Point(x1, y1).buffer(wd / 2.0, 16)
            else:
                g = LineString([(x1, y1), (x2, y2)]).buffer(wd / 2.0, 16)
            items.append(("%-3s %-6s (%.4f,%.4f)->(%.4f,%.4f) w%.3f  %s"
                          % (tag[:3].upper(), ly.group(1), x1, y1, x2, y2, wd,
                             uid), g, {ly.group(1)}, tag))

if not a.no_zones:
    for ly in CU:
        f = bg.zone_fill(a.net, ly)
        if not f.is_empty:
            items.append(("ZONEFILL %s area %.1f mm2" % (ly, f.area),
                          f, {ly}, "zone"))

n = len(items)
parent = list(range(n))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


for i in range(n):
    for j in range(i + 1, n):
        if not (items[i][2] & items[j][2]):
            continue
        if items[i][1].distance(items[j][1]) <= 1e-6:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[rj] = ri

groups = {}
for i in range(n):
    groups.setdefault(find(i), []).append(i)
print("net %s : %d copper items, %d island(s)" % (a.net, n, len(groups)))
order = sorted(groups.values(), key=lambda g: -len(g))
for k, g in enumerate(order):
    print("\n--- island %d : %d item(s) ---" % (k + 1, len(g)))
    for i in (g if len(g) <= 80 else g[:80]):
        print("   " + items[i][0])
    if len(g) > 80:
        print("   ... %d more" % (len(g) - 80))
