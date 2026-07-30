"""Explain what blocks a refdes label: per-direction min r + blocking owner."""
import json, math, sys
sys.path.insert(0, r'C:/dev/ai-ee3/boards/lumina-carrier/work/p8/silk')
from solve import (MARGIN, EDGE_MARGIN, SKIP, bbox, bb_far, hull, rect_poly_hit,
                   rect_poly_dist, pt_in_poly, seg_rect_hit, rect_corners)

BASE = r'C:/dev/ai-ee3/boards/lumina-carrier/work/p8/silk'
geom = json.load(open(f'{BASE}/geom.json', encoding='utf-8'))
plan = json.load(open(sys.argv[2], encoding='utf-8'))
fps = {f["ref"]: f for f in geom["footprints"]}
outline = [tuple(p) for p in geom["outline"][0]]
picks = {r["ref"]: r for r in plan["rows"]}

silk, pads, hulls, bodies = [], [], {}, {}
for ref, f in fps.items():
    bpts = []
    for s in f["silk"]:
        for poly in s["poly"]:
            pl = [tuple(p) for p in poly]; bb = bbox(pl)
            silk.append((ref, pl, bb)); bodies.setdefault(ref, []).append((pl, bb)); bpts += pl
    for p in f["pads"]:
        if not p["on_f_mask"]:
            continue
        for poly in p["poly"]:
            pl = [tuple(q) for q in poly]; bb = bbox(pl)
            pads.append((ref, pl, bb)); bodies.setdefault(ref, []).append((pl, bb)); bpts += pl
    if bpts:
        h = hull(bpts); hulls[ref] = (h, bbox(h))


def box_shape(ref, ang):
    t = fps[ref]["ref_text"]
    w, h, off = ((t["inked_w0"], t["inked_h0"], t["off0"]) if ang == 0
                 else (t["inked_w90"], t["inked_h90"], t["off90"]))
    return (off[0] - w / 2, off[1] - h / 2, off[0] + w / 2, off[1] + h / 2)


# text boxes at their SOLVED positions
tbox = {}
for ref, f in fps.items():
    if ref in picks:
        s = box_shape(ref, picks[ref]["ang"])
        # recover px,py from the ops file
        tbox[ref] = None
    icx, icy, iw, ih = f["ref_text"]["inked"]
    tbox[ref] = (icx - iw / 2, icy - ih / 2, icx + iw / 2, icy + ih / 2)
ops = json.load(open(sys.argv[3], encoding='utf-8'))["ops"]
for o in ops:
    s = box_shape(o["ref"], o["deg"])
    tbox[o["ref"]] = (s[0] + o["x"], s[1] + o["y"], s[2] + o["x"], s[3] + o["y"])

ref = sys.argv[1]
f = fps[ref]
ox, oy = f["x"], f["y"]
print(f"{ref} fp=({ox},{oy},{f['deg']}) hull_bb={hulls[ref][1]}")
print("neighbour hull bboxes within 8mm:")
for o, (h, hb) in hulls.items():
    if o == ref or bb_far(hb, (ox, oy, ox, oy), 8.0):
        continue
    print(f"   {o:6s} hull_bb=({hb[0]:.2f},{hb[1]:.2f},{hb[2]:.2f},{hb[3]:.2f})"
          f"  txt=({tbox[o][0]:.2f},{tbox[o][1]:.2f},{tbox[o][2]:.2f},{tbox[o][3]:.2f})")


def blockers(rect):
    out = []
    for (o, h, hb) in hulls.values() and [(k, v[0], v[1]) for k, v in hulls.items()]:
        if bb_far(hb, rect) or o == ref:
            continue
        if rect_poly_hit(rect, h):
            out.append("hull:" + o)
    if rect_poly_hit(rect, hulls[ref][0]):
        out.append("ownhull")
    for o, b in tbox.items():
        if o == ref:
            continue
        if not (rect[2] < b[0] or rect[0] > b[2] or rect[3] < b[1] or rect[1] > b[3]):
            out.append("txt:" + o)
    for c in rect_corners(rect):
        if not pt_in_poly(c, outline):
            out.append("edge")
            break
    return out


def attrib(rect):
    d_own, d_oth, who = 1e9, 1e9, None
    for other, polys in bodies.items():
        if other in SKIP:
            continue
        dd = 1e9
        for (pl, bb) in polys:
            if bb_far(bb, rect, 9.0):
                continue
            dd = min(dd, rect_poly_dist(rect, pl))
            if dd <= 0:
                break
        if dd > 8:
            continue
        if other == ref:
            d_own = dd
        elif dd < d_oth:
            d_oth, who = dd, other
    return d_own, d_oth, who


print("\ndir(deg)  ang   min_r  blocked_at_min-0.15   attrib(own,other,who)")
for k in range(36):
    th = 2 * math.pi * k / 36
    dx, dy = math.cos(th), math.sin(th)
    for ang in (0.0, 90.0):
        s = box_shape(ref, ang)
        hit, blk = None, None
        r = 0.30
        while r <= 7.0:
            px, py = ox + r * dx, oy + r * dy
            rect = (s[0] + px - MARGIN, s[1] + py - MARGIN,
                    s[2] + px + MARGIN, s[3] + py + MARGIN)
            b = blockers(rect)
            if not b:
                hit = r
                break
            blk = b
            r += 0.05
        if hit is None:
            print(f"{math.degrees(th):7.1f} {ang:5.0f}   ----   {sorted(set(blk or []))}")
        else:
            px, py = ox + hit * dx, oy + hit * dy
            rect = (s[0] + px, s[1] + py, s[2] + px, s[3] + py)
            do, dt, who = attrib(rect)
            print(f"{math.degrees(th):7.1f} {ang:5.0f} {hit:6.2f}   {sorted(set(blk or []))}"
                  f"   own={do:.3f} other={dt:.3f} {who}")
