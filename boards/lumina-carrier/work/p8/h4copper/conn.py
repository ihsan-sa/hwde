"""Explicit connectivity walk of /poe/LED_Y_A (belt-and-braces vs DRC)."""
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
import geom  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
NET = "/poe/LED_Y_A"


def main():
    bg = geom.load_board(PCB)
    items = []
    for t in bg.tracks_of(net=NET):
        items.append((f"trk {t.layer} {[round(c,3) for c in t.shape.coords[0]]}"
                      f"->{[round(c,3) for c in t.shape.coords[-1]]}",
                      {t.layer}, t.poly))
    for v in bg.vias_of(net=NET):
        items.append((f"via {[round(c,3) for c in v.at]}", set(v.layers), v.poly))
    for p in bg.pads_of(net=NET):
        items.append((f"pad {p.ref}-{p.number}", set(p.layers), p.poly))
    n = len(items)
    adj = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if items[i][1] & items[j][1] and items[i][2].intersects(items[j][2]):
                adj[i].add(j)
                adj[j].add(i)
    seen, stack = {0}, [0]
    while stack:
        k = stack.pop()
        for m in adj[k]:
            if m not in seen:
                seen.add(m)
                stack.append(m)
    print(f"{NET}: {n} copper items, largest connected group = {len(seen)}")
    if len(seen) != n:
        print("  ISLANDS:")
        for i in range(n):
            if i not in seen:
                print("   ", items[i][0])
    else:
        print("  single electrically continuous net (pads J1-17 and R7-2 both in)")
    for i in range(n):
        if items[i][0].startswith("pad"):
            print(f"  {items[i][0]} in main group: {i in seen}")


if __name__ == "__main__":
    main()
