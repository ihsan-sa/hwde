"""Exact silk / pad / refdes-text geometry from KiCad's own model.

Source: work/p8/silk/probe_geom.py output (TransformShapeToPolygon and
TransformTextToPolySet), so no hand-rolled arc/stroke/font approximation.
Provides rigid-body re-posing of a footprint's silk and pads.

  board = pos0 + R(-deg0).local   =>   P_new = pos1 + R(deg0-deg1).(P - pos0)
"""
import json
from pathlib import Path

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

FSILK = ("F.Silkscreen", "F.SilkS")


def _polys(polylist):
    out = []
    for ring in polylist:
        if len(ring) >= 3:
            p = Polygon(ring)
            if p.is_valid and p.area > 0:
                out.append(p)
            elif not p.is_valid:
                out.append(p.buffer(0))
    return out


class TrueGeo:
    def __init__(self, probe_json):
        d = json.loads(Path(probe_json).read_text(encoding="utf-8"))
        self.fp = {}
        for f in d["footprints"]:
            silk = []
            for g in f.get("silk", []):
                if g.get("layer") in FSILK and g.get("poly"):
                    silk += _polys(g["poly"])
            pads = []
            for p in f.get("pads", []):
                if p.get("poly") and any(c.startswith("F.") or c == "F.Cu"
                                         for c in p.get("cu", [])):
                    pads.append((p["n"], unary_union(_polys(p["poly"]))))
                elif p.get("poly") and p.get("cu"):
                    pads.append((p["n"], unary_union(_polys(p["poly"]))))
            self.fp[f["ref"]] = {
                "pos": (f["x"], f["y"]), "deg": f["deg"], "side": f["side"],
                "silk": unary_union(silk) if silk else None,
                "pads": pads,
                "ref_text": f["ref_text"],
            }
        self.outline = unary_union(_polys(d["outline"]))

    # ------------------------------------------------------------- re-posing
    def repose(self, geo, ref, pos1, deg1):
        if geo is None or geo.is_empty:
            return geo
        f = self.fp[ref]
        x0, y0 = f["pos"]
        g = affinity.translate(geo, -x0, -y0)
        g = affinity.rotate(g, f["deg"] - deg1, origin=(0, 0))
        return affinity.translate(g, pos1[0], pos1[1])

    def silk_at(self, ref, pos1, deg1):
        return self.repose(self.fp[ref]["silk"], ref, pos1, deg1)

    def pads_at(self, ref, pos1, deg1):
        return [(n, self.repose(p, ref, pos1, deg1))
                for n, p in self.fp[ref]["pads"]]

    def silk_now(self, ref):
        return self.fp[ref]["silk"]

    def pads_now(self, ref):
        return self.fp[ref]["pads"]

    # ------------------------------------------------------ refdes text box
    def ref_box(self, ref, cx, cy, deg):
        """EXACT inked box of `ref`'s Reference field if its text POSITION is
        (cx, cy) at absolute angle deg (0 or 90)."""
        rt = self.fp[ref]["ref_text"]
        if not rt.get("visible") or rt.get("layer") not in FSILK:
            return None
        if abs((deg % 180)) < 1e-6:
            w, h, off = rt["inked_w0"], rt["inked_h0"], rt["off0"]
        else:
            w, h, off = rt["inked_w90"], rt["inked_h90"], rt["off90"]
        ecx, ecy = cx + off[0], cy + off[1]
        return Polygon([(ecx - w / 2, ecy - h / 2), (ecx + w / 2, ecy - h / 2),
                        (ecx + w / 2, ecy + h / 2), (ecx - w / 2, ecy + h / 2)])

    def ref_box_now(self, ref):
        rt = self.fp[ref]["ref_text"]
        if not rt.get("visible") or rt.get("layer") not in FSILK:
            return None
        icx, icy, iw, ih = rt["inked"]
        return Polygon([(icx - iw / 2, icy - ih / 2), (icx + iw / 2, icy - ih / 2),
                        (icx + iw / 2, icy + ih / 2), (icx - iw / 2, icy + ih / 2)])

    # ------------------------------------------------------------- obstacles
    def foreign_silk(self, island):
        """[(tag, poly)] of every front-side silk graphic and visible front
        Reference box NOT belonging to `island`."""
        out = []
        for r, f in self.fp.items():
            if r in island or f["side"] != "front":
                continue
            if f["silk"] is not None and not f["silk"].is_empty:
                out.append((r + ":silk", f["silk"]))
            rb = self.ref_box_now(r)
            if rb is not None:
                out.append((r + ":REF", rb))
        return out

    def foreign_pads(self, island):
        out = []
        for r, f in self.fp.items():
            if r in island:
                continue
            for n, p in f["pads"]:
                if p is not None and not p.is_empty:
                    out.append(("%s.%s" % (r, n), p))
        return out


def flatten(g):
    if g is None or g.is_empty:
        return []
    if isinstance(g, (MultiPolygon,)):
        return list(g.geoms)
    return [g]
