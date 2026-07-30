"""Grounding measurements for wo-h4-copper (read-only)."""
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(r"C:\dev\ai-ee3\.claude\skills\ai-ee\scripts")
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))
import geom  # noqa

PCB = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb")
OUT = Path(r"C:\dev\ai-ee3\boards\lumina-carrier\work\p8\h4copper")

TAPS = ["/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"]
LEDS = ["/poe/LED_Y_A", "/poe/LED_G_A", "/poe/LED_Y_C", "/poe/LED_G_C"]
THR = 0.635


def main():
    bg = geom.load_board(PCB)
    print("copper layers:", bg.copper_layers)
    print("outline bounds:", [round(v, 3) for v in bg.outline.bounds])

    # ---- pads of interest
    print("\n--- pads on LED nets / R7 / J1 ---")
    for n in LEDS:
        for p in bg.pads_of(net=n):
            print(f"  {n}: {p.ref}-{p.number} at {[round(c,4) for c in p.center]} "
                  f"layers={p.layers} size={p.size} shape={p.shape}")
    for ref in ("R7",):
        for p in bg.pads_of(ref=ref):
            print(f"  {ref}-{p.number} net={p.net} at {[round(c,4) for c in p.center]} "
                  f"layers={p.layers}")

    # ---- LED vs TAP sweep (segment-pair population)
    print("\n--- LED nets vs POE_TAP nets: segment-pair sweep ---")
    summary = {}
    for led in LEDS:
        ltr = bg.tracks_of(net=led)
        lvia = bg.vias_of(net=led)
        lpad = bg.pads_of(net=led)
        print(f"\n{led}: {len(ltr)} tracks, {len(lvia)} vias, {len(lpad)} pads;"
              f" layers={sorted({t.layer for t in ltr})}")
        for tap in TAPS:
            ttr = bg.tracks_of(net=tap)
            tvia = bg.vias_of(net=tap)
            tpad = bg.pads_of(net=tap)
            mn, cnt, worst = 9e9, 0, None
            for layer in bg.copper_layers:
                # copper of each net on this layer, item-wise (tracks+vias+pads)
                A = ([("t", t.poly) for t in ltr if t.layer == layer]
                     + [("v", v.poly) for v in lvia if v.spans(layer)]
                     + [("p", p.poly) for p in lpad if p.on(layer)])
                B = ([("t", t.poly) for t in ttr if t.layer == layer]
                     + [("v", v.poly) for v in tvia if v.spans(layer)]
                     + [("p", p.poly) for p in tpad if p.on(layer)])
                for ka, a in A:
                    for kb, b in B:
                        d = a.distance(b)
                        if d < THR:
                            cnt += 1
                        if d < mn:
                            mn = d
                            worst = (layer, ka, kb,
                                     [round(c, 4) for c in a.centroid.coords[0]],
                                     [round(c, 4) for c in b.centroid.coords[0]])
            summary[(led, tap)] = (round(mn, 4), cnt)
            flag = "  <-- UNDER" if mn < THR else ""
            print(f"  vs {tap}: min={mn:.4f} mm  pairs<{THR}={cnt}{flag}  worst={worst}")

    # ---- undersized tracks (cluster B)
    print("\n--- tracks below 0.1016 mm ---")
    print("\nall nets containing LED:", [n for n in bg.nets if "LED" in n.upper()])
    thin = [t for t in bg.tracks_of() if t.width < 0.1016 - 1e-9]
    import collections
    print("count:", len(thin))
    print("by (layer,width):", dict(collections.Counter(
        (t.layer, round(t.width, 4)) for t in thin)))
    print("by net:", dict(collections.Counter(t.net for t in thin)))
    # arcs? (LineString with >2 coords means it came from an arc)
    arcs = [t for t in thin if len(t.shape.coords) > 2]
    print("of which arcs:", len(arcs))

    json.dump({f"{k[0]}|{k[1]}": v for k, v in summary.items()},
              open(OUT / "clusterA_before.json", "w"), indent=1)


if __name__ == "__main__":
    main()
