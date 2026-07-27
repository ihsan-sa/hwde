"""gerblib.py - gerber/drill -> shapely geometry (the INDEPENDENT path).

geom.py (S3) reads the .kicad_pcb. This module reads what we actually SHIP:
the exported gerbers + Excellon drill. Two different parsers over two different
file formats means an export-stage defect (a layer that did not make it into
the package, a mask expansion that ate an annular ring) shows up as a
disagreement instead of being invisible - that is the whole point of
dfm_check.py being a second geometry path (SPEC P9).

Coordinates: gerbers are emitted with Y pointing UP, the .kicad_pcb has Y
pointing DOWN. Everything this module returns is in BOARD space (y negated),
in millimetres, so DFM violations carry the same coordinates as every other
check in the pipeline (manifest.yaml, geom.py, kc.py).

Public API:
    open_fab(dir) -> FabStack
    FabStack.copper(layer)   -> LayerGeom  (traces, pads, pours, widths)
    FabStack.silk(side)      -> LayerGeom
    FabStack.mask(side)      -> LayerGeom  (flashes = mask OPENINGS)
    FabStack.outline         -> shapely Polygon | None (from Edge.Cuts)
    FabStack.holes           -> [Hole{x, y, diameter, plated}]
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from gerbonara import ExcellonFile, GerberFile
from gerbonara.graphic_objects import Arc, Flash, Line, Region
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

# kicad-cli names exports "<board>-<Layer_Name>.<ext>"; the layer token is what
# we key on so the board name never matters.
_COPPER_RE = re.compile(r"-(F_Cu|B_Cu|In\d+_Cu)\.(gtl|gbl|g\d+|gbr)$", re.I)
_SILK_RE = re.compile(r"-(F|B)_Silkscreen\.(gto|gbo|gbr)$", re.I)
_MASK_RE = re.compile(r"-(F|B)_Mask\.(gts|gbs|gbr)$", re.I)
_PASTE_RE = re.compile(r"-(F|B)_Paste\.(gtp|gbp|gbr)$", re.I)
_EDGE_RE = re.compile(r"-Edge_Cuts\.(gm1|gbr)$", re.I)
_DRILL_RE = re.compile(r"\.(drl|xln|txt)$", re.I)


def _layer_key(token: str) -> str:
    """'F_Cu' -> 'F.Cu' (pipeline layer naming)."""
    return token.replace("_", ".")


@dataclass
class Hole:
    x: float
    y: float
    diameter: float
    plated: bool = True


@dataclass
class LayerGeom:
    """One gerber layer's geometry, in board space."""
    name: str
    traces: list = field(default_factory=list)     # buffered polygons
    trace_widths: list = field(default_factory=list)
    trace_lines: list = field(default_factory=list)  # (LineString, width)
    pads: list = field(default_factory=list)       # flash polygons
    pours: list = field(default_factory=list)      # region polygons
    _union = None

    @property
    def all_polys(self) -> list:
        return self.traces + self.pads + self.pours

    def union(self):
        """Cached union of every feature on the layer."""
        if self._union is None:
            polys = self.all_polys
            self._union = unary_union(polys) if polys else Polygon()
        return self._union

    def components(self) -> list:
        """Electrically-distinct copper islands (union then explode). Gerbers
        carry no net data, so 'touching = same conductor' is the only honest
        grouping - which is exactly what a fab's DFM engine sees."""
        u = self.union()
        if u.is_empty:
            return []
        return list(u.geoms) if u.geom_type.startswith("Multi") else [u]

    @property
    def min_trace_width(self) -> float | None:
        return min(self.trace_widths) if self.trace_widths else None


# ArcPoly.outline carries only the segment ENDPOINTS - a circular pad's
# curvature lives in its arc segments, so taking .outline directly turns a
# round pad into a coarse few-sided polygon (measured: a 0.6 mm pad read as
# ~0.55 mm, i.e. a phantom 0.025 mm annular-ring shortfall). Tessellate arcs
# to 1 um before converting, well under every JLC capability threshold.
ARC_MAX_ERROR_MM = 1e-3


def _flash_polys(obj) -> list:
    """A Flash/Region -> shapely polygons in BOARD space (y negated)."""
    out = []
    for prim in obj.to_primitives("mm"):
        try:
            ap = prim.to_arc_poly()
            pts = list(ap.approximate_arcs(max_error=ARC_MAX_ERROR_MM).outline)
        except Exception:
            try:
                pts = list(prim.to_arc_poly().outline)
            except Exception:
                continue
        if len(pts) >= 3:
            poly = Polygon([(x, -y) for x, y in pts]).buffer(0)
            if not poly.is_empty:
                out.append(poly)
    return out


def read_gerber(path: Path, name: str) -> LayerGeom:
    """Parse one gerber into board-space shapely geometry."""
    lg = LayerGeom(name=name)
    gf = GerberFile.open(str(path))
    for obj in gf.objects:
        if isinstance(obj, (Line, Arc)):
            o = obj.converted("mm")
            try:
                w = obj.aperture.equivalent_width("mm")
            except Exception:
                w = 0.0
            # Arcs are approximated by their chord: the DFM measurements that
            # matter here (aperture width, clearance to other conductors) are
            # width-driven, and the corpus routes arcs only as chamfers.
            ls = LineString([(o.x1, -o.y1), (o.x2, -o.y2)])
            if ls.length == 0:
                ls = LineString([(o.x1, -o.y1), (o.x1 + 1e-6, -o.y1)])
            lg.trace_lines.append((ls, w))
            lg.trace_widths.append(w)
            lg.traces.append(ls.buffer(max(w, 1e-6) / 2.0, cap_style=2))
        elif isinstance(obj, Flash):
            lg.pads.extend(_flash_polys(obj))
        elif isinstance(obj, Region):
            lg.pours.extend(_flash_polys(obj))
    return lg


def read_drill(path: Path) -> list[Hole]:
    holes: list[Hole] = []
    with warnings.catch_warnings():
        # kicad-cli emits G90 after the Excellon header; gerbonara warns but
        # parses it correctly. Suppressed here so every caller (gate.py runs
        # dfm_check as a library) gets clean stderr, not just the CLI.
        warnings.simplefilter("ignore")
        ef = ExcellonFile.open(str(path))
    for obj in ef.objects:
        if not isinstance(obj, Flash):
            continue
        o = obj.converted("mm")
        dia = getattr(getattr(obj, "tool", None), "diameter", None)
        if dia is None:
            dia = getattr(getattr(obj, "aperture", None), "diameter", None)
        if dia is None:
            continue
        plated = getattr(obj, "plated", True)
        holes.append(Hole(x=o.x, y=-o.y, diameter=float(dia),
                          plated=True if plated is None else bool(plated)))
    return holes


class FabStack:
    """Every gerber/drill file in one exported fab directory."""

    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self.copper_files: dict[str, Path] = {}
        self.silk_files: dict[str, Path] = {}
        self.mask_files: dict[str, Path] = {}
        self.paste_files: dict[str, Path] = {}
        self.edge_file: Path | None = None
        self.drill_files: list[Path] = []
        self._cache: dict[str, LayerGeom] = {}
        self._holes: list[Hole] | None = None
        self._outline = None
        self._scan()

    def _scan(self) -> None:
        for p in sorted(self.dir.iterdir()):
            if not p.is_file():
                continue
            n = p.name
            if (m := _COPPER_RE.search(n)):
                self.copper_files[_layer_key(m.group(1))] = p
            elif (m := _SILK_RE.search(n)):
                self.silk_files[m.group(1)] = p
            elif (m := _MASK_RE.search(n)):
                self.mask_files[m.group(1)] = p
            elif (m := _PASTE_RE.search(n)):
                self.paste_files[m.group(1)] = p
            elif _EDGE_RE.search(n):
                self.edge_file = p
            elif _DRILL_RE.search(n) and not n.lower().endswith(".gbrjob"):
                self.drill_files.append(p)

    # ------------------------------------------------------------ accessors
    def _get(self, path: Path | None, name: str) -> LayerGeom | None:
        if path is None:
            return None
        if name not in self._cache:
            self._cache[name] = read_gerber(path, name)
        return self._cache[name]

    def copper_layer_names(self) -> list[str]:
        """Physical stackup order: F.Cu, In1.Cu, ..., B.Cu."""
        def key(n: str):
            if n == "F.Cu":
                return (0, 0)
            if n == "B.Cu":
                return (2, 0)
            m = re.match(r"In(\d+)\.Cu", n)
            return (1, int(m.group(1)) if m else 0)
        return sorted(self.copper_files, key=key)

    def copper(self, layer: str) -> LayerGeom | None:
        return self._get(self.copper_files.get(layer), layer)

    def silk(self, side: str) -> LayerGeom | None:
        return self._get(self.silk_files.get(side), f"{side}.Silkscreen")

    def mask(self, side: str) -> LayerGeom | None:
        return self._get(self.mask_files.get(side), f"{side}.Mask")

    @property
    def holes(self) -> list[Hole]:
        if self._holes is None:
            out: list[Hole] = []
            for p in self.drill_files:
                try:
                    out.extend(read_drill(p))
                except Exception:
                    continue
            self._holes = out
        return self._holes

    @property
    def outline(self):
        """Board outline polygon from Edge.Cuts centerlines (board space)."""
        if self._outline is None:
            self._outline = Polygon()
            if self.edge_file is not None:
                lg = self._get(self.edge_file, "Edge.Cuts")
                lines = [ls for ls, _ in lg.trace_lines]
                polys = list(polygonize(unary_union(lines))) if lines else []
                if polys:
                    self._outline = max(polys, key=lambda p: p.area)
                elif lg.pours:
                    self._outline = unary_union(lg.pours)
        return self._outline


def open_fab(directory: Path | str) -> FabStack:
    d = Path(directory)
    if not d.is_dir():
        raise FileNotFoundError(f"fab directory not found: {d}")
    return FabStack(d)
