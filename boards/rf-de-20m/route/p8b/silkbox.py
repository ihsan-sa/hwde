"""Approximate F.SilkS text extents, so a new mask opening does not clip one
(KiCad's `silk_over_copper` / 'Silkscreen clipped by solder mask')."""
import math, re, sys
import sexpdata
from shapely.geometry import box
from shapely.ops import unary_union

PCB = r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb'


def _s(x):
    return x.value() if hasattr(x, 'value') else x


def _find(node, key):
    for c in node[1:]:
        if isinstance(c, list) and _s(c[0]) == key:
            return c
    return None


def collect(path=PCB):
    raw = sexpdata.loads(open(path, encoding='utf-8').read())
    boxes = []

    def walk(node, fp=None):
        if not isinstance(node, list) or not node:
            return
        h = _s(node[0])
        if h == 'footprint':
            at = _find(node, 'at')
            fp = ([float(v) for v in at[1:]] if at else [0, 0, 0])
        if h in ('property', 'fp_text', 'gr_text'):
            lay = _find(node, 'layer')
            if lay and _s(lay[1]) in ('F.SilkS',):
                hid = any(isinstance(c, list) and _s(c[0]) == 'hide'
                          and _s(c[1]) in ('yes', True) for c in node[1:])
                if not hid:
                    txt = _s(node[2]) if h == 'property' else _s(node[1])
                    at = _find(node, 'at')
                    if at and isinstance(txt, str) and txt.strip():
                        lx, ly = float(at[1]), float(at[2])
                        if fp is not None and h != 'gr_text':
                            a = math.radians(-(fp[2] if len(fp) > 2 else 0.0))
                            x = fp[0] + lx * math.cos(a) - ly * math.sin(a)
                            y = fp[1] + lx * math.sin(a) + ly * math.cos(a)
                        else:
                            x, y = lx, ly
                        eff = _find(node, 'effects')
                        sz = 1.0
                        if eff:
                            f = _find(eff, 'font')
                            if f:
                                s = _find(f, 'size')
                                if s:
                                    sz = float(s[2])
                        n = max(len(txt), 1)
                        w = 0.78 * sz * n + 0.4
                        hgt = sz + 0.4
                        boxes.append(box(x - w / 2, y - hgt / 2,
                                         x + w / 2, y + hgt / 2))
        for c in node:
            walk(c, fp)
    walk(raw)
    return unary_union(boxes)


if __name__ == '__main__':
    u = collect()
    print(len(u.geoms) if u.geom_type == 'MultiPolygon' else 1, 'silk clusters')
