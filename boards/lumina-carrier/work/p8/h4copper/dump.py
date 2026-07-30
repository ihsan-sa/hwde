"""Dump LED_Y_A path + POE_TAP copper + local obstacles (read-only)."""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
TAPS = ["/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"]

SEG_RE = re.compile(
    r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
    r'\(width ([\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "([^"]*)"\)\s*'
    r'\(uuid "([^"]+)"\)', re.S)
VIA_RE = re.compile(
    r'\(via\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\(size ([\d.]+)\)\s*\(drill ([\d.]+)\)\s*'
    r'\(layers ([^)]*)\)\s*(?:\(remove_unused_layers[^)]*\)\s*)?'
    r'(?:\(zone_layer_connections[^)]*\)\s*)?\(net (\d+)\)\s*\(uuid "([^"]+)"\)', re.S)


def flat(pcb):
    return re.sub(r"[\t\n]+", " ", pcb.read_text(encoding="utf-8"))


def seg_rows(pcb):
    rows = []
    for m in SEG_RE.finditer(flat(pcb)):
        x0, y0, x1, y1, w, layer, net, uid = m.groups()
        rows.append(dict(a=(float(x0), float(y0)), b=(float(x1), float(y1)),
                         w=float(w), layer=layer, net=net, uuid=uid))
    return rows


def main():
    bg = geom.load_board(PCB)
    rows = seg_rows(PCB)
    print("segments parsed by regex:", len(rows),
          " geom tracks:", len(bg.tracks_of()))

    print("\n=== /poe/LED_Y_A segments (regex, with uuid) ===")
    ly = [r for r in rows if r["net"] == "/poe/LED_Y_A"]
    for r in sorted(ly, key=lambda r: (r["layer"], r["a"])):
        print(f"  {r['layer']:7s} {r['a']} -> {r['b']}  w={r['w']}  {r['uuid']}")
    print("\n=== /poe/LED_Y_A vias ===")
    for v in bg.vias_of(net="/poe/LED_Y_A"):
        print("  ", v.at, v.diameter, v.drill, v.layers)
    txt = flat(PCB)
    for m in VIA_RE.finditer(txt):
        print("  via raw:", m.groups())

    print("\n=== POE_TAP copper extents per layer ===")
    for tap in TAPS:
        for layer in bg.copper_layers:
            c = bg.net_copper(tap, layer)
            if c.is_empty:
                continue
            print(f"  {tap:20s} {layer:7s} bounds={[round(x,3) for x in c.bounds]}"
                  f" area={c.area:.3f}")
        for p in bg.pads_of(net=tap):
            print(f"    pad {p.ref}-{p.number} at {[round(c,3) for c in p.center]}"
                  f" layers={p.layers} size={p.size}")

    print("\n=== nets with copper in window x[30,60] y[57,75] per layer ===")
    from shapely.geometry import box
    win = box(30, 57, 60, 75)
    for layer in bg.copper_layers:
        acc = defaultdict(float)
        for n in bg.nets:
            if not n:
                continue
            c = bg.net_copper(n, layer)
            if not c.is_empty and c.intersects(win):
                acc[n] = round(c.intersection(win).area, 3)
        print(f"  {layer}: {dict(sorted(acc.items(), key=lambda kv:-kv[1]))}")

    print("\n=== zones ===")
    for z in bg.zones_of():
        print("  zone", z.zone_id, "net=", z.net, "layers=", z.layers,
              "filled=", z.filled,
              {L: round(z.fill_area(L), 2) for L in z.layers})

    print("\n=== footprints near the pocket (refs + centers) ===")
    seen = {}
    for p in bg.pads_of():
        seen.setdefault(p.ref, p.center)
    for ref, c in sorted(seen.items()):
        if 28 <= c[0] <= 62 and 56 <= c[1] <= 78:
            print(f"  {ref} at {[round(v,3) for v in c]}")


if __name__ == "__main__":
    main()
