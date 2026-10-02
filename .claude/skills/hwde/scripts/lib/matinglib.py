"""matinglib - can every mating connector on the board actually be mated?

Shared by the P6 place gate (place_metrics.py, family "mating") and the P8
verify gate (check_mating.py), so the fault fails at placement and stays
failed if a later edit brings it back.

Which footprints are mating connectors, and their plug geometry, come from
reference/connector_mating.yaml (see its header). Three violation kinds, all
error severity, each naming the connector in `connector` (refs also lists
the blocking parts):

  mating_faces_inward  a horizontal connector's mouth faces away from its
                       nearest board edge (PCB-0021-A J4: USB-A with its back
                       at the edge and its mouth toward L1).
  mating_mouth_inset   the mouth faces the nearest edge but sits more than
                       mouth_tol_mm inside it.
  mating_zone_blocked  a part on the connector's side sits in the insertion
                       zone in front of the mouth (horizontal), or a part
                       taller than tall_mm sits within finger_mm of a
                       vertical connector.

and one warning, mating_direction_unknown, for a horizontal connector whose
pad layout is symmetric about its body: it asks for a `mouth` entry in the
table rather than guessing.

Mouth direction is read from the pad layout: the contact pads (the most
common pad size) sit at the back of the housing and the body extends toward
the mouth, so the mouth points from the contact-pad centroid toward the
courtyard centroid. The table's `mouth` map overrides that per footprint.

Part heights (vertical rule) come from the 3D model: a "-H<mm>" in the model
or footprint name, else the highest vertex of a .wrl model found beside the
board (VRML units are 2.54 mm). A part with no readable height is listed in
the facts, never failed.
"""
from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

import yaml
from shapely.geometry import LineString, box

import checklib
from geom import _kid, _kids, _nums, _strs

SOURCE = "matinglib"
TABLE = Path(__file__).resolve().parents[2] / "reference" / "connector_mating.yaml"
EPS_AREA = 0.01
AXES = {"+x": (1.0, 0.0), "-x": (-1.0, 0.0), "+y": (0.0, 1.0), "-y": (0.0, -1.0)}
KINDS = ("mating_faces_inward", "mating_mouth_inset", "mating_zone_blocked",
         "mating_direction_unknown")


@lru_cache(maxsize=1)
def load_table(path: str = str(TABLE)) -> dict:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    d = doc.get("defaults", {})
    fams = []
    for fam in doc.get("families", []):
        fams.append({**d, **fam, "re": re.compile(fam["match"], re.I)})
    mouth = [(re.compile(k, re.I), v) for k, v in (doc.get("mouth") or {}).items()]
    return {"families": fams, "mouth": mouth}


def _name(fpid: str) -> str:
    return fpid.split(":", 1)[-1]


def family_of(fpid: str, table: dict | None = None) -> dict | None:
    table = table or load_table()
    name = _name(fpid)
    for fam in table["families"]:
        if fam["re"].search(name):
            return fam
    return None


def _snap(dx: float, dy: float) -> str:
    if abs(dx) >= abs(dy):
        return "+x" if dx >= 0 else "-x"
    return "+y" if dy >= 0 else "-y"


def mouth_local(f, table: dict | None = None) -> str | None:
    """The mouth direction in the footprint's local frame, or None when the
    pad layout is symmetric about the body (nothing to read it from)."""
    table = table or load_table()
    for rx, d in table["mouth"]:
        if rx.search(_name(f.fpid)):
            return d
    pads = [p for p in f.pads if p.number]
    if not pads:
        return None
    sizes: dict = {}
    for p in pads:
        k = (round(p.size[0], 2), round(p.size[1], 2), p.through)
        sizes.setdefault(k, []).append(p)
    contacts = max(sizes.values(), key=len)
    cx = sum(p.local[0] for p in contacts) / len(contacts)
    cy = sum(p.local[1] for p in contacts) / len(contacts)
    body = f.extents_local().centroid
    dx, dy = body.x - cx, body.y - cy
    if math.hypot(dx, dy) < 0.3:
        return None
    return _snap(dx, dy)


def _to_abs_dir(f, d: str) -> tuple[float, float]:
    ux, uy = AXES[d]
    o = f.to_abs((0.0, 0.0))
    p = f.to_abs((ux, uy))
    return AXES[_snap(p[0] - o[0], p[1] - o[1])]


def _span(poly, u: tuple[float, float]) -> tuple[float, float]:
    vals = [x * u[0] + y * u[1] for x, y in poly.exterior.coords]
    return min(vals), max(vals)


def _edge_gap(outline, body, u) -> float:
    """Distance from the body's face in direction u to the board edge it
    faces (negative when the face overhangs that edge)."""
    c = body.centroid
    lo, hi = _span(body, u)
    ray = LineString([(c.x, c.y), (c.x + u[0] * 1e4, c.y + u[1] * 1e4)])
    hit = ray.intersection(outline.exterior)
    pts = [g.centroid for g in getattr(hit, "geoms", [hit]) if not g.is_empty]
    ts = [p.x * u[0] + p.y * u[1] for p in pts]
    ts = [t for t in ts if t > c.x * u[0] + c.y * u[1]]
    if not ts:  # centroid already off the board in this direction
        return lo - hi
    return min(ts) - hi


def _zone(body, u, gap: float, plug: float, grip: float):
    """Insertion zone: the mouth's own width from the mouth face to the board
    edge (the plug slides over that ledge), then that width plus grip each
    side out to plug + grip past the edge, where the hand holds it."""
    v = (-u[1], u[0])
    _, front = _span(body, u)
    wlo, whi = _span(body, v)
    edge = front + max(gap, 0.0)

    def rect(a0, a1, b0, b1):
        pts = [(a * u[0] + b * v[0], a * u[1] + b * v[1])
               for a, b in ((a0, b0), (a1, b1))]
        return box(min(pts[0][0], pts[1][0]), min(pts[0][1], pts[1][1]),
                   max(pts[0][0], pts[1][0]), max(pts[0][1], pts[1][1]))

    zone = rect(edge, edge + plug + grip, wlo - grip, whi + grip)
    if edge > front:
        zone = zone.union(rect(front, edge, wlo, whi))
    return zone


# ------------------------------------------------------------ part heights

_H_RE = re.compile(r"[-_]H(\d+(?:\.\d+)?)(?![\d.])", re.I)


def model_paths(pcb: Path) -> dict[str, tuple[str, list[float]]]:
    """ref -> (first 3D model path, its rotate xyz) from the board file."""
    import sexpdata
    tree = sexpdata.loads(Path(pcb).read_text(encoding="utf-8"))
    out = {}
    for fp in _kids(tree, "footprint"):
        ref = None
        for prop in _kids(fp, "property"):
            s = _strs(prop)
            if len(s) >= 2 and s[0] == "Reference":
                ref = s[1]
        m = _kid(fp, "model")
        if ref and m is not None and _strs(m):
            rot = _kid(m, "rotate")
            xyz = _nums(_kid(rot, "xyz")) if rot is not None \
                and _kid(rot, "xyz") is not None else [0.0, 0.0, 0.0]
            out[ref] = (_strs(m)[0], xyz)
    return out


@lru_cache(maxsize=512)
def _wrl_height(path: str) -> float | None:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    zs = []
    for blk in re.findall(r"point\s*\[([^\]]*)\]", text):
        v = [float(x) for x in
             re.findall(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", blk)]
        zs.extend(v[2::3])
    return max(zs) * 2.54 if zs else None


def part_height(f, model: tuple[str, list[float]] | None,
                pcb: Path) -> float | None:
    for name in ([Path(model[0]).stem] if model else []) + [_name(f.fpid)]:
        m = _H_RE.search(name)
        if m:
            return float(m.group(1))
    if not model or not model[0].lower().endswith(".wrl"):
        return None
    if any(abs(r) > 1e-6 for r in model[1][:2]):
        return None  # tilted model: its z is not the board's z
    raw = model[0].replace("${KIPRJMOD}", str(Path(pcb).parent))
    base = Path(raw).name
    ws = Path(pcb).resolve().parent.parent
    for cand in [Path(raw), *ws.glob(f"lib/*.3dshapes/{base}")]:
        if cand.is_file():
            return _wrl_height(str(cand))
    return None


# ------------------------------------------------------------ the check

def violations(model, pcb: Path | None = None) -> tuple[list[dict], list[dict]]:
    """(violations, facts) for every mating connector on `model`
    (a placelib.PlaceModel)."""
    table = load_table()
    pcb = Path(pcb or model.path)
    outline = model.outline
    fps = model.footprints
    out: list[dict] = []
    facts: list[dict] = []
    models = None
    fam_of = {r: family_of(f.fpid, table) for r, f in fps.items()}

    for ref in sorted(fps):
        f, fam = fps[ref], fam_of[ref]
        if fam is None:
            continue
        body = f.extents_abs()
        fact = {"ref": ref, "family": fam["family"], "entry": fam["entry"]}
        facts.append(fact)
        others = [o for r, o in fps.items() if r != ref and o.side == f.side]

        if fam["entry"] == "horizontal":
            d = mouth_local(f, table)
            if d is None:
                fact["mouth"] = None
                out.append(checklib.violation(
                    "place", "warning", f.center_abs(), None, None, [ref],
                    f"{ref} ({fam['family']}): cannot read its mouth "
                    "direction from the pad layout - add a `mouth` entry "
                    "to reference/connector_mating.yaml", SOURCE,
                    kind="mating_direction_unknown", connector=ref))
                continue
            u = _to_abs_dir(f, d)
            gap = _edge_gap(outline, body, u)
            gaps = {k: _edge_gap(outline, body, a) for k, a in AXES.items()}
            nearest = min(gaps, key=gaps.get)
            facing = _snap(*u)
            fact.update(mouth=facing, gap_mm=checklib.rnd(gap, 2),
                        nearest_edge=nearest)
            c = f.center_abs()
            # brief: "A connector whose mating direction is horizontal must
            # face the nearest board edge, with its mouth at or over that
            # edge." Mouth more than the tolerance short of the edge it
            # faces -> fail; inward when that edge is not the nearest one.
            if gap > fam["mouth_tol_mm"]:
                inward = nearest != facing
                why = (f"its nearest edge is {nearest} "
                       f"({max(gaps[nearest], 0):.1f} mm) but its mouth "
                       f"faces {facing}, into {gap:.1f} mm of board"
                       if inward else
                       f"its mouth is {gap:.1f} mm inside the {facing} edge "
                       f"(limit {fam['mouth_tol_mm']} mm)")
                out.append(checklib.violation(
                    "place", "error", c, None, None, [ref],
                    f"{ref} ({fam['family']}) cannot be mated: {why}",
                    SOURCE,
                    kind="mating_faces_inward" if inward
                    else "mating_mouth_inset",
                    connector=ref, mouth=facing, nearest_edge=nearest,
                    gap_mm=checklib.rnd(gap, 2)))
            zone = _zone(body, u, gap, fam["plug_mm"], fam["grip_mm"])
            blockers = sorted(o.ref for o in others
                              if o.extents_abs().intersects(zone)
                              and o.precise_extents_abs().intersection(
                                  zone).area > EPS_AREA)
            fact["blocked_by"] = blockers
            if blockers:
                z = zone.centroid
                out.append(checklib.violation(
                    "place", "error", (z.x, z.y), None, None,
                    [ref, *blockers],
                    f"{ref} ({fam['family']}): "
                    f"{', '.join(blockers)} sit in the plug's insertion zone "
                    f"in front of its mouth ({fam['plug_mm']} mm plug + "
                    f"{fam['grip_mm']} mm grip)", SOURCE,
                    kind="mating_zone_blocked", connector=ref,
                    mouth=facing, blocked_by=blockers))
        else:
            if models is None:
                models = model_paths(pcb) if pcb.is_file() else {}
            zone = body.buffer(fam["finger_mm"])
            tall, unknown = [], []
            for o in others:
                ofam = fam_of[o.ref]
                if ofam is not None and ofam["entry"] == "vertical":
                    continue
                if o.precise_extents_abs().intersection(zone).area <= EPS_AREA:
                    continue
                h = part_height(o, models.get(o.ref), pcb)
                if h is None:
                    unknown.append(o.ref)
                elif h > fam["tall_mm"]:
                    tall.append((o.ref, h))
            fact.update(tall_nearby=[r for r, _ in tall],
                        height_unknown=sorted(unknown))
            if tall:
                names = ", ".join(f"{r} ({h:.1f} mm)" for r, h in sorted(tall))
                out.append(checklib.violation(
                    "place", "error", f.center_abs(), None, None,
                    [ref, *(r for r, _ in tall)],
                    f"{ref} ({fam['family']}): {names} within "
                    f"{fam['finger_mm']} mm - taller than {fam['tall_mm']} mm "
                    "leaves no room for the plug housing and a finger",
                    SOURCE, kind="mating_zone_blocked", connector=ref,
                    blocked_by=sorted(r for r, _ in tall)))
    return out, facts
