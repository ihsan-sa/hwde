"""Local obstacle map around the J1 tap pocket (read-only)."""
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
from shapely.geometry import box  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
WIN = box(33, 56, 62, 78)


def main():
    bg = geom.load_board(PCB)
    print("outline bounds", [round(v, 3) for v in bg.outline.bounds])
    print("outline exterior coords sample:",
          [(round(x, 2), round(y, 2)) for x, y in list(bg.outline.exterior.coords)[:20]])

    print("\n=== /poe/POE_TAP_A2 items ===")
    for t in bg.tracks_of(net="/poe/POE_TAP_A2"):
        print(f"  trk {t.layer:7s} {[round(c,3) for c in t.shape.coords[0]]} ->"
              f" {[round(c,3) for c in t.shape.coords[-1]]} w={t.width}")
    for v in bg.vias_of(net="/poe/POE_TAP_A2"):
        print("  via", v.at, v.diameter, v.layers)

    for layer in ("F.Cu", "B.Cu"):
        print(f"\n=== {layer}: every copper item intersecting x[33,62] y[56,78] ===")
        items = []
        for t in bg.tracks_of(layer=layer):
            if t.poly.intersects(WIN):
                items.append((t.net or "<none>", "trk",
                              [round(c, 3) for c in t.shape.coords[0]],
                              [round(c, 3) for c in t.shape.coords[-1]], t.width))
        for v in bg.vias_of():
            if v.spans(layer) and v.poly.intersects(WIN):
                items.append((v.net or "<none>", "via",
                              [round(c, 3) for c in v.at], None, v.diameter))
        for p in bg.pads_of():
            if p.on(layer) and p.poly.intersects(WIN):
                items.append((p.net or "<none>", f"pad {p.ref}-{p.number}",
                              [round(c, 3) for c in p.center], None, p.size))
        for net, kind, a, b, w in sorted(items):
            print(f"  {net:20s} {kind:14s} {a} {b} {w}")


if __name__ == "__main__":
    main()
