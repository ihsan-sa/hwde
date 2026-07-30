"""All /ETH_RSTn copper incident on the two zero-room nodes, + nudge check."""
import re
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
from shapely.geometry import LineString  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
NODES = [(96.75, 85.85), (96.75, 86.4)]
DX = 0.03
NEW = {(96.75, 85.85): (96.78, 85.85), (96.75, 86.4): (96.78, 86.4)}
SEG_RE = re.compile(
    r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
    r'\(width ([\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "([^"]*)"\)\s*'
    r'\(uuid "([^"]+)"\)', re.S)


def main():
    bg = geom.load_board(PCB)
    txt = re.sub(r"[\t\n]+", " ", PCB.read_text(encoding="utf-8"))
    print("=== every /ETH_RSTn segment within 1.5 mm of the nodes ===")
    hits = []
    for m in SEG_RE.finditer(txt):
        x0, y0, x1, y1, w, layer, net, uid = m.groups()
        if net != "/ETH_RSTn":
            continue
        a, b = (float(x0), float(y0)), (float(x1), float(y1))
        for n in NODES:
            if (abs(a[0] - n[0]) < 1.5 and abs(a[1] - n[1]) < 1.5) or \
               (abs(b[0] - n[0]) < 1.5 and abs(b[1] - n[1]) < 1.5):
                hits.append((a, b, float(w), layer, uid))
                break
    for a, b, w, layer, uid in sorted(hits):
        touch = [n for n in NODES if a == n or b == n]
        print(f"  {layer:6s} {a} -> {b} w={w} touches={touch} {uid}")

    print("\n=== vias / pads of /ETH_RSTn near there ===")
    for v in bg.vias_of(net="/ETH_RSTn"):
        if abs(v.at[0] - 96.75) < 2 and abs(v.at[1] - 86.1) < 2:
            print("  via", v.at, v.diameter)
    for p in bg.pads_of(net="/ETH_RSTn"):
        if abs(p.center[0] - 96.75) < 3 and abs(p.center[1] - 86.1) < 3:
            print("  pad", p.ref, p.number, p.center)

    print("\n=== nudged geometry clearance check (w=0.110, x 96.75 -> 96.78) ===")
    cands = [
        ("F.Cu", (96.78, 85.85), (96.78, 86.4), 0.110),
        ("F.Cu", (96.78, 85.85), (97.0, 85.6), 0.110),
        ("F.Cu", (96.78, 86.4), (96.775, 86.425), 0.110),
    ]
    edge = bg.outline.exterior
    for layer, a, b, w in cands:
        poly = LineString([a, b]).buffer(w / 2, quad_segs=16)
        rows = []
        for other in bg.nets:
            if not other or other == "/ETH_RSTn":
                continue
            parts = [t.poly for t in bg.tracks_of(net=other, layer=layer)]
            parts += [v.poly for v in bg.vias_of(net=other) if v.spans(layer)]
            parts += [p.poly for p in bg.pads_of(net=other) if p.on(layer)]
            for z in bg.zones_of(net=other):
                f = z.fill_on(layer)
                if not f.is_empty:
                    parts.append(f)
            if parts:
                rows.append((round(min(poly.distance(q) for q in parts), 4), other))
        for p in bg.pads_of():
            if (not p.net) and p.on(layer):
                rows.append((round(poly.distance(p.poly), 4),
                             f"<NC {p.ref}-{p.number}>"))
        rows.sort()
        print(f"  {a}->{b} w={w}: {rows[:4]} edge={round(edge.distance(poly),3)}")


if __name__ == "__main__":
    main()
