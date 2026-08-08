"""rf-de-20m: generator for the two etched PCB air-core spiral inductors.

    L301 = L_s = 164 nH   (series tank inductor)   -> SPIRAL_L164N.kicad_mod
    L302 = L_m = 110 nH   (L-match inductor)       -> SPIRAL_L110N.kicad_mod

These are not purchasable parts - the copper IS the component (decisions.md D3,
blocks.md SPIRAL-1..6).  Both are wound on F.Cu AND B.Cu in PARALLEL (SPIRAL-2),
identical plan-view geometry, stitched by via clusters at both terminals, with
the inner terminal escaping on an In1+In2 radial bridge (SPIRAL-4).

Electrical derivation, both inductance methods and the Q / dissipation budget:
    boards/rf-de-20m/reports/spiral-design.md

Rebuild:
    .venv/Scripts/python boards/rf-de-20m/kicad/gen/spirals.py [OUT_PRETTY_DIR]

KiCad 10 facts this file depends on (all machine-verified 2026-08-08, see
LEARNINGS.md):
  * `(net_tie_pad_groups "1, 2")` exempts pads 1 and 2 from the shorted-nets
    DRC.  An inductor IS a DC short between its terminals, so a net tie is the
    correct - and only - KiCad-native encoding for an etched coil.
  * footprint copper *graphics* (`fp_poly` on a copper layer) are NOT part of
    KiCad's connectivity: they plot to Gerber but leave every pad they touch
    reported as `unconnected_items`.  So every piece of the winding is a PAD
    (custom-shaped where it has to be), never a graphic.
  * footprint-level rule areas `(zone ... (keepout ...))` ARE supported and
    round-trip through pcbnew, so "no plane under a spiral" travels with the
    part instead of relying on P6/P7 remembering it.
  * an SMD pad whose layer set has no outer layer (the In1+In2 bridge) raises
    ONE `padstack` DRC *warning* per part - "Padstack is questionable (SMD pad
    has no outer layers)".  That is intentional and must be waived at P7.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
BOARD = HERE.parents[2]
DEFAULT_OUT = BOARD / "lib" / "aiee.pretty"

# ------------------------------------------------------------------ geometry
# Solved in reports/spiral-design.md.  w and s are common to both parts (same
# 6.96 A rms, same fab rules); OD and turn count carry the inductance.
W = 2.5            # trace width, mm
S = 1.0            # turn-to-turn gap, mm
STEP_DEG = 5.0     # spiral polygon step (sagitta < 16 um at OD 33)
VIA_D = 0.6        # via pad diameter, mm
VIA_H = 0.3        # via drill, mm
BRIDGE_W = 5.0     # In1+In2 radial bridge width, mm (SPIRAL-4 wants >= 4)
LAND_W = 2.8       # terminal land radial width, mm
LAND_H = 8.0       # terminal land tangential height, mm
INNER_LAND_L = 10.0  # inner via-cluster land length, mm
CRTYD_M = 0.25     # courtyard margin, mm
NO_POUR_M = 4.0    # keepout margin beyond the outer turn, mm
TURN_CLR = 0.75    # inner land setback from the next turn inwards, mm
                   # (>= 0.6 mm at the land CORNER: IPC-2221 B1, uncoated
                   #  external, 51-150 V - adjacent turns sit at ~68 V pk)

PARTS = [
    dict(name="SPIRAL_L164N", val="164nH", od=33.10, n=3,
         descr="Etched PCB air-core planar spiral 164nH at 20MHz "
               "(rf-de-20m L_s, L301). 3 turns, OD 33.10mm, 2.5mm trace, "
               "1.0mm gap, F.Cu||B.Cu parallel winding, In1+In2 inner-terminal "
               "bridge. NET TIE: pads 1-2 are joined by the winding. "
               "No plane or heatsink beneath - shorted turn."),
    dict(name="SPIRAL_L110N", val="110nH", od=32.57, n=2,
         descr="Etched PCB air-core planar spiral 110nH at 20MHz "
               "(rf-de-20m L_m, L302). 2 turns, OD 32.57mm, 2.5mm trace, "
               "1.0mm gap, F.Cu||B.Cu parallel winding, In1+In2 inner-terminal "
               "bridge. NET TIE: pads 1-2 are joined by the winding. "
               "No plane or heatsink beneath - shorted turn."),
]

TAGS = "inductor spiral air-core RF planar net-tie ai-ee"


# --------------------------------------------------------------------- maths
def spiral_centreline(r0, pitch, nturn, step_deg=STEP_DEG):
    """Archimedean centreline, outermost point at angle 0 (+x)."""
    steps = int(round(360.0 * nturn / step_deg))
    pts = []
    for i in range(steps + 1):
        th = 2 * math.pi * nturn * i / steps
        r = r0 - pitch * th / (2 * math.pi)
        pts.append((r * math.cos(th), r * math.sin(th)))
    return pts


def offset_ribbon(pts, width):
    """Closed polygon of constant `width` centred on the open polyline `pts`."""
    n = len(pts)
    nrm = []
    for i in range(n):
        j0, j1 = max(i - 1, 0), min(i + 1, n - 1)
        tx, ty = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
        m = math.hypot(tx, ty)
        nrm.append((-ty / m, tx / m))
    h = width / 2.0
    left = [(p[0] + h * v[0], p[1] + h * v[1]) for p, v in zip(pts, nrm)]
    right = [(p[0] - h * v[0], p[1] - h * v[1]) for p, v in zip(pts, nrm)]
    return left + right[::-1]


def circle_poly(r, step_deg=3.0):
    k = int(round(360.0 / step_deg))
    return [(r * math.cos(2 * math.pi * i / k),
             r * math.sin(2 * math.pi * i / k)) for i in range(k)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def shift(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


# ------------------------------------------------------------- s-expr output
def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _pts_block(pts, indent):
    out = []
    for i in range(0, len(pts), 6):
        out.append(indent + " ".join(f"(xy {f(x)} {f(y)})"
                                     for x, y in pts[i:i + 6]))
    return "\n".join(out)


def sx_prim(pts):
    return ("\t\t\t(gr_poly\n\t\t\t\t(pts\n"
            + _pts_block(pts, "\t\t\t\t\t")
            + "\n\t\t\t\t)\n\t\t\t\t(width 0)\n\t\t\t\t(fill yes)\n\t\t\t)")


def sx_pad_custom(num, x, y, sx_, sy_, layers, prims):
    lay = " ".join(f'"{l}"' for l in layers)
    body = "\n".join(sx_prim(shift(p, -x, -y)) for p in prims)
    return (f"\t(pad \"{num}\" smd custom\n\t\t(at {f(x)} {f(y)})\n"
            f"\t\t(size {f(sx_)} {f(sy_)})\n\t\t(layers {lay})\n"
            f"\t\t(options\n\t\t\t(clearance outline)\n\t\t\t(anchor rect)\n\t\t)\n"
            f"\t\t(primitives\n{body}\n\t\t)\n\t)")


def sx_pad_rect(num, x, y, sx_, sy_, layers):
    lay = " ".join(f'"{l}"' for l in layers)
    return (f"\t(pad \"{num}\" smd rect\n\t\t(at {f(x)} {f(y)})\n"
            f"\t\t(size {f(sx_)} {f(sy_)})\n\t\t(layers {lay})\n\t)")


def sx_pad_via(num, x, y):
    return (f"\t(pad \"{num}\" thru_hole circle\n\t\t(at {f(x)} {f(y)})\n"
            f"\t\t(size {f(VIA_D)} {f(VIA_D)})\n\t\t(drill {f(VIA_H)})\n"
            f"\t\t(layers \"*.Cu\")\n\t\t(remove_unused_layers no)\n\t)")


def sx_line(x0, y0, x1, y1, layer, width):
    return (f"\t(fp_line\n\t\t(start {f(x0)} {f(y0)})\n"
            f"\t\t(end {f(x1)} {f(y1)})\n"
            f"\t\t(stroke\n\t\t\t(width {f(width)})\n\t\t\t(type solid)\n\t\t)\n"
            f"\t\t(layer \"{layer}\")\n\t)")


def sx_closed(pts, layer, width):
    return [sx_line(pts[i][0], pts[i][1],
                    pts[(i + 1) % len(pts)][0], pts[(i + 1) % len(pts)][1],
                    layer, width) for i in range(len(pts))]


def sx_circle(r, layer, width):
    return (f"\t(fp_circle\n\t\t(center 0 0)\n\t\t(end {f(r)} 0)\n"
            f"\t\t(stroke\n\t\t\t(width {f(width)})\n\t\t\t(type solid)\n\t\t)\n"
            f"\t\t(fill no)\n\t\t(layer \"{layer}\")\n\t)")


def sx_zone(name, layers, pts, tracks, vias):
    lay = " ".join(f'"{l}"' for l in layers)
    return (f"\t(zone\n\t\t(layers {lay})\n\t\t(name \"{name}\")\n"
            f"\t\t(hatch edge 0.5)\n\t\t(connect_pads\n\t\t\t(clearance 0)\n\t\t)\n"
            f"\t\t(min_thickness 0.25)\n\t\t(keepout\n"
            f"\t\t\t(tracks {tracks})\n\t\t\t(vias {vias})\n"
            f"\t\t\t(pads allowed)\n\t\t\t(copperpour not_allowed)\n"
            f"\t\t\t(footprints allowed)\n\t\t)\n"
            f"\t\t(placement\n\t\t\t(enabled no)\n\t\t\t(sheetname \"\")\n\t\t)\n"
            f"\t\t(fill\n\t\t\t(thermal_gap 0.5)\n"
            f"\t\t\t(thermal_bridge_width 0.5)\n"
            f"\t\t\t(island_removal_mode 0)\n\t\t)\n"
            f"\t\t(polygon\n\t\t\t(pts\n" + _pts_block(pts, "\t\t\t\t")
            + "\n\t\t\t)\n\t\t)\n\t)")


def sx_prop(key, value, x, y, layer, hide, size=1.0):
    h = "\n\t\t(hide yes)" if hide else ""
    return (f"\t(property \"{key}\" \"{value}\"\n\t\t(at {f(x)} {f(y)} 0)\n"
            f"\t\t(layer \"{layer}\"){h}\n\t\t(effects\n\t\t\t(font\n"
            f"\t\t\t\t(size {f(size)} {f(size)})\n\t\t\t\t(thickness 0.15)\n"
            f"\t\t\t)\n\t\t)\n\t)")


def sx_text(kind, txt, x, y, layer, size=1.0):
    return (f"\t(fp_text {kind} \"{txt}\"\n\t\t(at {f(x)} {f(y)} 0)\n"
            f"\t\t(layer \"{layer}\")\n\t\t(effects\n\t\t\t(font\n"
            f"\t\t\t\t(size {f(size)} {f(size)})\n\t\t\t\t(thickness 0.15)\n"
            f"\t\t\t)\n\t\t)\n\t)")


# ------------------------------------------------------------------- builder
def build(part) -> str:
    od, n = part["od"], part["n"]
    p = W + S
    r0 = (od - W) / 2.0                       # outer turn centreline radius
    r_in = r0 - n * p                         # inner turn centreline radius
    r_edge = r0 + W / 2.0                     # outer copper edge

    xt_in = r_edge + 0.35                     # terminal land inner x
    xt_out = xt_in + LAND_W                   # terminal land outer x
    xt_mid = (xt_in + xt_out) / 2.0

    # Inner land: local radial widening over the spiral's inner end, kept clear
    # of the next turn's inward-facing edge, long enough for 14 vias that all
    # sit >= 0.25 mm clear of the winding's own copper.
    xb = min(r_in + W / 2.0 + 1.2, r_in + p - W / 2.0 - TURN_CLR)
    xa = xb - INNER_LAND_L
    via_x_hi = (r_in - W / 2.0) - 0.25 - VIA_D / 2.0   # clear of the ribbon
    via_x_lo = xa + 0.6
    ncol, nrow = 7, 2
    dx = (via_x_hi - via_x_lo) / (ncol - 1)

    items = []

    # --- pad 1: the whole winding + its lead-out + the east terminal land.
    # One custom pad per outer layer; the two are stitched by the via cluster.
    ribbon = offset_ribbon(spiral_centreline(r0, p, n), W)
    lead1 = rect(r0 - 1.0, -W / 2.0, xt_in + 0.2, W / 2.0)
    prims = [ribbon, lead1]
    for layer in ("F.Cu", "B.Cu"):
        items.append(sx_pad_custom("1", xt_mid, 0.0, LAND_W, LAND_H,
                                   (layer,), prims))

    # --- pad 2: escaped inner node = inner land + In1/In2 bridge + west land
    for layer in ("F.Cu", "B.Cu"):
        items.append(sx_pad_rect("2", (xa + xb) / 2.0, 0.0, xb - xa, W,
                                 (layer,)))
        items.append(sx_pad_rect("2", -xt_mid, 0.0, LAND_W, LAND_H, (layer,)))
    # the bridge: narrow, radial, NEVER a slab (SPIRAL-4).  Inner-layer-only
    # pad -> one benign `padstack` DRC warning, waived at P7.
    items.append(sx_pad_rect("2", (xb - xt_out) / 2.0, 0.0, xb + xt_out,
                             BRIDGE_W, ("In1.Cu", "In2.Cu")))

    # --- via clusters: 14 per crossing at the declared 0.5 A/via (SPIRAL-4)
    cols = (xt_in + 0.65, xt_out - 0.65)
    rows = [(-3.3 + 1.1 * i) for i in range(7)]
    for cx in cols:
        for cy in rows:
            items.append(sx_pad_via("1", cx, cy))
            items.append(sx_pad_via("2", -cx, cy))
    for i in range(ncol):
        for cy in (-0.6, 0.6):
            items.append(sx_pad_via("2", via_x_lo + i * dx, cy))

    # --- rule areas: the shorted-turn rules travel with the part
    keep = circle_poly(r_edge + NO_POUR_M)
    items.append(sx_zone("SPIRAL_NO_POUR_OUTER", ("F.Cu", "B.Cu"), keep,
                         "allowed", "allowed"))
    items.append(sx_zone("SPIRAL_NO_INNER_COPPER", ("In1.Cu", "In2.Cu"), keep,
                         "not_allowed", "not_allowed"))

    # --- courtyards on both faces: this part owns copper on F.Cu AND B.Cu
    cx_, cy_ = xt_out + CRTYD_M, r_edge + CRTYD_M
    for layer in ("F.CrtYd", "B.CrtYd"):
        items += sx_closed(rect(-cx_, -cy_, cx_, cy_), layer, 0.05)

    items.append(sx_circle(r_edge, "F.Fab", 0.1))
    items.append(sx_text("user", "SPIRAL-6: keep all metal 15mm clear",
                         0.0, cy_ + 2.6, "Cmts.User"))
    items.append(sx_text("user", "no plane / heatsink under this part",
                         0.0, cy_ + 4.0, "Cmts.User"))

    head = [
        f'(footprint "{part["name"]}"',
        "\t(version 20260206)",
        '\t(generator "ai-ee spirals.py")',
        '\t(generator_version "10.0")',
        '\t(layer "F.Cu")',
        f'\t(descr "{part["descr"]}")',
        f'\t(tags "{TAGS}")',
        sx_prop("Reference", "REF**", 0.0, -(cy_ + 1.3), "F.SilkS", False),
        sx_prop("Value", part["val"], 0.0, cy_ + 1.3, "F.Fab", False),
        sx_prop("Datasheet", "", 0.0, 0.0, "F.Fab", True, 1.27),
        sx_prop("Description", part["descr"], 0.0, 0.0, "F.Fab", True, 1.27),
        "\t(attr exclude_from_pos_files exclude_from_bom)",
        '\t(net_tie_pad_groups "1, 2")',
        "\t(duplicate_pad_numbers_are_jumpers no)",
    ]
    return "\n".join(head + items + ["\t(embedded_fonts no)", ")", ""])


def main(argv):
    out = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        txt = build(part)
        txt.encode("ascii")                   # ASCII-safe contract
        path = out / f"{part['name']}.kicad_mod"
        path.write_text(txt, encoding="ascii", newline="\n")
        print(f"wrote {path}  ({len(txt)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
