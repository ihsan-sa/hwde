"""fplib.py - parse a KiCad .kicad_mod footprint into pads + layer presence.

Handles BOTH footprint formats easyeda2kicad and KiCad emit:
  - legacy:  (module NAME (layer F.Cu) ... (pad 1 smd rect (at ..) (size ..)
             (layers F.Cu F.Paste F.Mask)))     <- unquoted layer tokens
  - modern:  (footprint "NAME" ... (pad "1" smd rect (at ..) (size ..)
             (layers "F.Cu" "F.Paste" "F.Mask")))

Pure sexpdata parse - no SWIG/KiCad process. Used by lib_pull.py (report) and
fp_verify.py (land-pattern diff). Everything is millimetres.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import sexpdata


def _tok(x):
    return x.value() if isinstance(x, sexpdata.Symbol) else x


def _is_node(n) -> bool:
    return isinstance(n, list) and bool(n)


def _head(n):
    return _tok(n[0]) if _is_node(n) else None


def _kid(n, name: str):
    for c in n[1:] if _is_node(n) else []:
        if _is_node(c) and _head(c) == name:
            return c
    return None


def _nums(n) -> list[float]:
    return [float(x) for x in n[1:] if isinstance(x, (int, float))]


def _layer_tokens(node) -> list[str]:
    """Layer name(s) of a graphic/pad node from its (layer X) or (layers ...)."""
    out = []
    for key in ("layer", "layers"):
        k = _kid(node, key)
        if k is not None:
            out += [str(_tok(t)) for t in k[1:]]
    return out


_COPPER_SUFFIX = ".Cu"
_GRAPHIC_HEADS = ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc",
                  "fp_text", "fp_curve")


@dataclass
class Pad:
    number: str
    ptype: str          # smd | thru_hole | np_thru_hole | connect | ...
    shape: str          # rect | roundrect | oval | circle | custom | trapezoid
    at: tuple[float, float, float]   # x, y, rotation(deg)
    size: tuple[float, float]
    layers: list[str] = field(default_factory=list)

    @property
    def center(self) -> tuple[float, float]:
        return (self.at[0], self.at[1])

    @property
    def is_copper(self) -> bool:
        # NPTH pads are mechanical (mounting holes) even if they list *.Cu.
        if self.ptype == "np_thru_hole":
            return False
        return any(ly.endswith(_COPPER_SUFFIX) or ly == "*.Cu" for ly in self.layers)


@dataclass
class Footprint:
    name: str
    path: Path
    pads: list[Pad]
    layers_present: set[str]          # every distinct layer token seen on graphics/pads

    @property
    def copper_pads(self) -> list[Pad]:
        return [p for p in self.pads if p.is_copper]

    def has_layer_kind(self, kind: str) -> bool:
        """True if any graphic sits on a *.<kind> layer (CrtYd, SilkS, Fab)."""
        return any(kind in ly for ly in self.layers_present)

    @property
    def has_courtyard(self) -> bool:
        return self.has_layer_kind("CrtYd")


def _parse_pad(node) -> Pad | None:
    # (pad NUMBER TYPE SHAPE ...)
    if len(node) < 4:
        return None
    number = str(_tok(node[1]))
    ptype = str(_tok(node[2]))
    shape = str(_tok(node[3]))
    at = _kid(node, "at")
    size = _kid(node, "size")
    if at is None or size is None:
        return None
    an = _nums(at)
    sn = _nums(size)
    if len(an) < 2 or len(sn) < 2:
        return None
    rot = an[2] if len(an) >= 3 else 0.0
    return Pad(number=number, ptype=ptype, shape=shape,
               at=(an[0], an[1], rot), size=(sn[0], sn[1]),
               layers=[str(_tok(t)) for t in (_kid(node, "layers") or [None])[1:]])


def _strip_lib_prefix(name: str) -> str:
    # "easyeda2kicad:C0402" -> "C0402"
    return name.split(":")[-1]


def parse_footprint(path: str | Path) -> Footprint:
    """Parse one .kicad_mod file into a Footprint."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    root = sexpdata.loads(text)
    if not _is_node(root) or _head(root) not in ("module", "footprint"):
        raise ValueError(f"{p} is not a footprint (head={_head(root)})")
    name = _strip_lib_prefix(str(_tok(root[1]))) if len(root) > 1 else p.stem

    pads: list[Pad] = []
    layers: set[str] = set()
    for child in root[1:]:
        if not _is_node(child):
            continue
        h = _head(child)
        if h == "pad":
            pad = _parse_pad(child)
            if pad is not None:
                pads.append(pad)
                layers.update(pad.layers)
        elif h in _GRAPHIC_HEADS:
            layers.update(_layer_tokens(child))
    return Footprint(name=name, path=p, pads=pads, layers_present=layers)


def footprint_files(pretty_dir: str | Path) -> list[Path]:
    d = Path(pretty_dir)
    return sorted(d.glob("*.kicad_mod")) if d.is_dir() else []


def symbol_names(kicad_sym_path: str | Path) -> list[str]:
    """Top-level symbol names in a .kicad_sym library (best-effort)."""
    p = Path(kicad_sym_path)
    if not p.exists():
        return []
    try:
        root = sexpdata.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    if not _is_node(root) or _head(root) != "kicad_symbol_lib":
        return []
    names = []
    for child in root[1:]:
        if _is_node(child) and _head(child) == "symbol" and len(child) > 1:
            names.append(str(_tok(child[1])))
    return names
