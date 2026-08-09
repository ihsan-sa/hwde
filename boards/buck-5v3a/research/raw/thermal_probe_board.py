"""Build synthetic probe boards for the buck-5v3a U1 thermal re-check (P2 revisit).

Models the REAL AP63356QZV-7 land pattern: 9 lands, NO exposed/thermal pad.
Heat exits are the VIN land (pad 1) and the GND land (pad 8), per DS41948 p.25
rules 7-8 and Figure 47.  Vias are placed IN and AROUND those two lands - there
is no belly-pad via array, because there is no belly pad.

Two variants: 4-layer (F/In1/In2/B, all inners GND) and 2-layer (F/B).
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent

X0, Y0 = 100.0, 100.0          # board origin (KiCad page coords)
W, H = 50.0, 40.0              # outline
UX, UY = X0 + 18.0, Y0 + 20.0  # U1 centroid

# --- U1 land pattern, from lib/aiee.pretty/V-DFN3020-13-A_...kicad_mod --------
# (x, y, sx, sy, net) relative to the footprint origin.  Signal lands widened to
# the Diodes-recommended 0.30 (u1-land-ruling.md defect 1).
PADS = [
    ("1", -0.92, +0.75, 1.500, 0.750, "+VIN"),
    ("2", +0.13, +0.85, 0.300, 0.600, "/EN"),
    ("3", +0.58, +0.85, 0.300, 0.600, "/FB"),
    ("4", +1.03, +0.85, 0.300, 0.600, "GND"),      # COMP tied to GND (internal comp)
    ("5", +1.03, -0.85, 0.300, 0.600, "/PG"),
    ("6", +0.58, -0.85, 0.300, 0.600, "/BST"),
    ("7", +0.13, -0.85, 0.300, 0.600, "/NC"),
    ("8", -0.92, -0.75, 1.500, 0.750, "GND"),
    ("9", -1.03, +0.00, 1.730, 0.350, "/SW"),
]

# --- thermal vias -------------------------------------------------------------
# GND land is 1.500 x 0.750 at (-0.92, -0.75).
# NOTE: these three in-pad positions are PROBE GEOMETRY ONLY - check_thermal's
# model does not read via positions at all (it is an area/layer-count screen, see
# reports/thermal-recheck.md s4).  The SHIPPED prescription is NO via-in-pad and a
# 12-via field in the pour around the land; three 0.55 mm pads at 0.48 mm pitch
# would not even pass DRC.  Do not copy this list into the real layout.
GND_IN_PAD = [(-1.40, -0.75), (-0.92, -0.75), (-0.44, -0.75)]
# ring immediately outboard of the GND land, in the top GND pour
GND_RING = [(-1.75, -1.55), (-1.15, -1.55), (-0.55, -1.55), (+0.05, -1.55),
            (-2.20, -0.75), (-2.20, -1.55), (+0.50, -1.55),
            (-1.75, -2.25), (-0.95, -2.25), (-0.15, -2.25)]


NETS = ["", "GND", "+VIN", "/SW", "/EN", "/FB", "/PG", "/BST", "/NC"]
NETNUM = {n: i for i, n in enumerate(NETS)}


def fmt_pts(pts):
    return " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in pts)


def rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def zone(net, layer, pts, zid):
    return (f'\t(zone (net {NETNUM[net]} "{net}") (layer "{layer}")\n'
            f'\t\t(uuid "z{zid:08d}") (hatch edge 0.5) (connect_pads (clearance 0.3))\n'
            f'\t\t(min_thickness 0.25) (fill yes (thermal_gap 0.5)'
            f' (thermal_bridge_width 0.5))\n'
            f'\t\t(polygon (pts {fmt_pts(pts)}))\n'
            f'\t\t(filled_polygon (layer "{layer}") (pts {fmt_pts(pts)}))\n'
            f'\t)\n')


def via(x, y, net, layers):
    return (f'\t(via (at {x:.3f} {y:.3f}) (size 0.55) (drill 0.30)\n'
            f'\t\t(layers "{layers[0]}" "{layers[-1]}") (net {NETNUM[net]} "{net}")\n'
            f'\t\t(uuid "v{abs(hash((x, y))) % 10**8:08d}")\n\t)\n')


def build(layers, name):
    four = len(layers) == 4
    lay_decl = "\n".join(
        f'\t\t({i} "{n}" signal)' for i, n in
        (((0, "F.Cu"), (4, "In1.Cu"), (6, "In2.Cu"), (2, "B.Cu")) if four
         else ((0, "F.Cu"), (2, "B.Cu"))))
    body = []

    # ---- U1 footprint (9 lands, no EP) --------------------------------------
    body.append(f'\t(footprint "aiee:V-DFN3020-13-A" (layer "F.Cu")\n'
                f'\t\t(uuid "fp000001") (at {UX:.3f} {UY:.3f})\n'
                f'\t\t(property "Reference" "U1" (at 0 -2.5 0) (layer "F.SilkS"))\n')
    for num, px, py, sx, sy, net in PADS:
        body.append(f'\t\t(pad "{num}" smd rect (at {px:.3f} {py:.3f}) '
                    f'(size {sx:.3f} {sy:.3f}) (layers "F.Cu" "F.Paste" "F.Mask") '
                    f'(net {NETNUM[net]} "{net}") (uuid "p{num}000001"))\n')
    body.append('\t)\n')

    # ---- copper pours -------------------------------------------------------
    zid = 0
    # F.Cu GND pour: an L around U1 on the GND-land side, ~250 mm^2 contiguous,
    # kept off the +VIN / /SW sides.  Modelled as two rectangles.
    body.append(zone("GND", "F.Cu",
                     rect(UX - 4.0, UY - 12.0, UX + 14.0, UY - 1.0), zid)); zid += 1
    body.append(zone("GND", "F.Cu",
                     rect(UX - 12.0, UY - 12.0, UX - 4.0, UY - 3.0), zid)); zid += 1
    # F.Cu +VIN pour: the Cin bank / Q1 drain area, the VIN land's own spreader
    body.append(zone("+VIN", "F.Cu",
                     rect(UX - 10.0, UY + 1.2, UX + 1.0, UY + 8.0), zid)); zid += 1
    if four:
        for l in ("In1.Cu", "In2.Cu"):
            body.append(zone("GND", l, rect(X0 + 0.6, Y0 + 0.6,
                                            X0 + W - 0.6, Y0 + H - 0.6), zid)); zid += 1
    body.append(zone("GND", "B.Cu", rect(X0 + 0.6, Y0 + 0.6,
                                         X0 + W - 0.6, Y0 + H - 0.6), zid)); zid += 1

    # ---- thermal vias -------------------------------------------------------
    span = ("F.Cu", "B.Cu")
    for dx, dy in GND_IN_PAD + GND_RING:
        body.append(via(UX + dx, UY + dy, "GND", span))

    text = (f'(kicad_pcb\n\t(version 20260206)\n\t(generator "aiee-probe")\n'
            f'\t(general (thickness 1.6))\n\t(layers\n{lay_decl}\n'
            f'\t\t(25 "Edge.Cuts" user)\n\t)\n\t(setup)\n'
            + "".join(f'\t(net {i} "{n}")\n' for i, n in enumerate(NETS))
            + f'\t(gr_rect (start {X0} {Y0}) (end {X0+W} {Y0+H}) '
            + f'(stroke (width 0.1) (type solid)) (fill no) (layer "Edge.Cuts"))\n'
            + "".join(body) + ')\n')
    p = OUT / f"{name}.kicad_pcb"
    p.write_text(text, encoding="utf-8")
    print("wrote", p, f"({len(GND_IN_PAD)+len(GND_RING)} GND vias)")
    return p


if __name__ == "__main__":
    build(["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"], "probe4l")
    build(["F.Cu", "B.Cu"], "probe2l")
