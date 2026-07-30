"""Probe the three zero-room /ETH_RSTn tracks and the /eth/XI,/eth/XO thin tracks."""
import json
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa
from shapely.geometry import box  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
ROWS = json.loads(Path(
    r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\h4copper\widen_report.json"
).read_text())


def main():
    bg = geom.load_board(PCB)

    print("=== zero-room / capped rows: what exactly blocks them ===")
    for r in ROWS:
        if r["room"] > 0.02:
            continue
        from shapely.geometry import LineString
        ln = LineString([r["start"], r["end"]])
        print(f"\n{r['net']} {r['layer']} {r['start']}->{r['end']} w={r['w']}"
              f" room={r['room']}")
        cands = []
        for other in bg.nets:
            if not other or other == r["net"]:
                continue
            for t in bg.tracks_of(net=other, layer=r["layer"]):
                cands.append((t.poly.distance(ln), other, "trk",
                              [round(c, 3) for c in t.shape.coords[0]],
                              [round(c, 3) for c in t.shape.coords[-1]]))
            for v in bg.vias_of(net=other):
                if v.spans(r["layer"]):
                    cands.append((v.poly.distance(ln), other, "via",
                                  [round(c, 3) for c in v.at], None))
            for p in bg.pads_of(net=other):
                if p.on(r["layer"]):
                    cands.append((p.poly.distance(ln), other,
                                  f"pad {p.ref}-{p.number}",
                                  [round(c, 3) for c in p.center], None))
            for z in bg.zones_of(net=other):
                f = z.fill_on(r["layer"])
                if not f.is_empty:
                    cands.append((f.distance(ln), other, "zone", None, None))
        for p in bg.pads_of():
            if (not p.net) and p.on(r["layer"]):
                cands.append((p.poly.distance(ln), f"<NC {p.ref}-{p.number}>",
                              "pad", [round(c, 3) for c in p.center], None))
        cands.sort(key=lambda x: x[0])
        for d, net, kind, a, b in cands[:6]:
            print(f"   {round(d,4):8} {net:14s} {kind:14s} {a} {b}")

    print("\n=== /eth/XI and /eth/XO thin tracks vs the oscillator island ===")
    for ref in ("Y10", "C30", "C31", "R35", "R36", "U30"):
        for p in bg.pads_of(ref=ref):
            print(f"  pad {ref}-{p.number} net={p.net} at"
                  f" {[round(c,3) for c in p.center]}")
    for net in ("/eth/XI", "/eth/XO", "/eth/XO_XTAL"):
        print(f"  {net}:")
        for t in bg.tracks_of(net=net):
            print(f"    {t.layer:7s} {[round(c,4) for c in t.shape.coords[0]]}"
                  f" -> {[round(c,4) for c in t.shape.coords[-1]]} w={t.width}")


if __name__ == "__main__":
    main()
