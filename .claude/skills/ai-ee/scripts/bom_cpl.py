#!/usr/bin/env python
"""bom_cpl.py - assembly files: the BOM of record, the JLC upload pair, classes.

The P9 assembly-format step (SPEC 6.4). Membership is decided by an
ASSEMBLY CLASS per refdes - never by "whatever the position export happened to
contain" (codex H1). Three files come out of one run:

  BOM-full.csv  the BOM OF RECORD. EVERY intended part, whatever its class:
                machine-placed, hand-installed, off-board, do-not-populate,
                customer-supplied, select-on-test, board feature. Columns:
                Comment, Designator, Qty Per Board, Footprint, MPN, LCSC,
                Assembly Class, Instructions. This is the engineering
                deliverable and the thing a human reads.

  BOM.csv       the ASSEMBLER UPLOAD: `smt_placed` parts only, in JLC's own
                four columns (Comment, Designator, Footprint, LCSC), one row
                per (value, footprint, LCSC) group with the comma-joined
                designator list. Its designator set is identical to CPL.csv's
                by construction - a DNP site cannot leak into a quote.

  CPL.csv       Designator, Mid X, Mid Y, Layer, Rotation - `smt_placed` only.
                Mid X/Y in mm from the pos file; Layer Top/Bottom; Rotation =
                (kicad rotation + JLC correction) mod 360. The correction is
                the notorious KiCad<->JLC 0-degree-reference offset, vendored
                per package family in reference/jlc_rotations.csv (regex on the
                footprint name, first match wins - LEARNINGS/S8).

Assembly classes (`assembly_class`, canonical parts.json - NOT a board-local
filter script, which is how rf-de-20m's nine DNP sites used to be handled):

  smt_placed        the assembler places it. In BOM.csv AND CPL.csv.
  hand_install      bought, fitted by hand after reflow. BOM-full only.
  off_board         bought, mounted off the PCB (heatsink-flanged loads, ...).
  dnp               a real land that must ship EMPTY.
  customer_supplied not part of the PCBA order at all (screws, straps, sinks).
  select_on_test    value/part chosen at the bench; never machine-placed.
  board_feature     realised in copper or board process - nothing to buy
                    (etched air-core spirals, printed shunts).

Where a class comes from, highest priority first:
  1. parts.json line `refdes_class: {"C203": "dnp"}` (or legacy `refdes_dnp`)
  2. parts.json line `assembly_class` (applies to every ref in `refdes`)
  3. the board file's own footprint `dnp` attribute
  4. default `smt_placed`
Instructions text: `refdes_notes: {ref: text}` > line `assembly_notes` >
a per-class default sentence.

bom_cpl GENERATES; polarity/rotation VALIDATION (catching a backwards part) is
dfm_check.py's job, which also consumes these classes: a missing LCSC on an
`smt_placed` part is a release ERROR, on any other class it is not a finding.

CLI:
  bom_cpl.py --pcb board.kicad_pcb --out-dir fab/ [--pos pos.csv]
             [--parts parts.json] [--rotations jlc_rotations.csv]
             [--name NAME] [--out report.json]
Exit 0 ok / 1 assembly violations (incomplete BOM, unplaced smt_placed part,
declared-quantity mismatch) / 2 error.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import kc  # noqa: E402

REF_ROTATIONS = SCRIPTS.parent / "reference" / "jlc_rotations.csv"

# --------------------------------------------------------- assembly classes

PLACED_CLASS = "smt_placed"
ASSEMBLY_CLASSES = (
    PLACED_CLASS, "hand_install", "off_board", "dnp",
    "customer_supplied", "select_on_test", "board_feature",
)
# Stable presentation order for BOM-full.csv (placed parts first).
CLASS_ORDER = {c: i for i, c in enumerate(ASSEMBLY_CLASSES)}

CLASS_INSTRUCTION = {
    PLACED_CLASS: "",
    "hand_install": "Hand-install after reflow - not machine-placed.",
    "off_board": "Mounted OFF the PCB - not machine-placed.",
    "dnp": "DO NOT POPULATE - this land ships empty.",
    "customer_supplied": "Customer-supplied - not part of the PCBA order.",
    "select_on_test": "SELECT ON TEST - measured/chosen at the bench.",
    "board_feature": "Realised in copper - nothing to buy or place.",
}


class AssemblyDataError(ValueError):
    """Malformed canonical assembly data (unknown class, bad shape)."""


# ------------------------------------------------------------- rotation table

def load_rotations(path: Path) -> list[tuple[re.Pattern, float]]:
    """Parse reference/jlc_rotations.csv -> [(compiled regex, degrees)] in file
    order (first match wins). Skips the header and #-comments."""
    rules: list[tuple[re.Pattern, float]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.lower().startswith("regex,"):
            continue
        # split on the LAST comma (regex may contain commas, rotation cannot)
        idx = line.rfind(",")
        if idx < 0:
            continue
        pat, deg = line[:idx].strip(), line[idx + 1:].strip()
        try:
            rules.append((re.compile(pat), float(deg)))
        except (re.error, ValueError):
            continue
    return rules


def footprint_name(package: str) -> str:
    """The part after a library colon, if any (pos gives the bare name already,
    but board-sourced fpids look like 'LED_SMD:LED_0805_2012Metric')."""
    return package.split(":", 1)[1] if ":" in package else package


def correct_rotation(package: str, base_deg: float,
                     rules: list[tuple[re.Pattern, float]]
                     ) -> tuple[float, float, str | None]:
    """(final_rotation, correction_applied, matched_pattern|None).
    final = (base + correction) mod 360."""
    name = footprint_name(package)
    for pat, deg in rules:
        if pat.search(name):
            final = (base_deg + deg) % 360.0
            return (final, deg, pat.pattern)
    return (base_deg % 360.0, 0.0, None)


# ------------------------------------------------------------------- pos read

def parse_pos_csv(text: str) -> list[dict]:
    """kicad-cli pos CSV -> [{ref,val,package,x,y,rot,side}]. Header:
    Ref,Val,Package,PosX,PosY,Rot,Side."""
    rows: list[dict] = []
    reader = csv.DictReader(io.StringIO(text))
    for r in reader:
        try:
            rows.append({
                "ref": r["Ref"].strip(),
                "val": r["Val"].strip(),
                "package": r["Package"].strip(),
                "x": float(r["PosX"]),
                "y": float(r["PosY"]),
                "rot": float(r["Rot"]),
                "side": r["Side"].strip().lower(),
            })
        except (KeyError, ValueError) as exc:
            raise ValueError(f"unexpected pos-CSV row {r}: {exc}") from exc
    return rows


def _get_pos(pcb: Path, pos: Path | None, out_dir: Path, name: str) -> str:
    if pos is not None:
        return Path(pos).read_text(encoding="utf-8")
    cli = kc.resolve_cli()
    pos_file = out_dir / f"{name}-pos.csv"
    res = kc.export_pos(cli, pcb, pos_file, side="both", fmt="csv", units="mm")
    if res.get("status") != "pass":
        raise RuntimeError(f"pos export failed: {res.get('stderr') or res}")
    return pos_file.read_text(encoding="utf-8")


# ------------------------------------------------------------------ parts map

def board_part_fields(pcb: Path) -> dict[str, dict]:
    """ref -> {lcsc, mpn, dnp, attr_class} read off the BOARD's own footprints.

    board_init copies custom symbol fields (LCSC included) onto footprints
    since S14, so a pipeline board carries its own ref->LCSC mapping - the
    file being fabbed is the closest-to-truth source. parts.json (per-ref
    shapes) remains an explicit override; the S6 per-DISTINCT-part shape has
    no refs and cannot map by itself.

    The footprint `(attr ...)` flags are KiCad's own class statement and are
    read as one: `dnp` -> class dnp, `exclude_from_bom`/`board_only` -> class
    board_feature (mounting holes, fiducials, heatsink lands - board_init marks
    them so, LEARNINGS/S8), `exclude_from_pos_files` alone -> hand_install (in
    the BOM, not machine-placed). parts.json outranks all of them; see
    resolve_assembly.
    """
    import sexpdata
    out: dict[str, dict] = {}
    try:
        data = sexpdata.loads(Path(pcb).read_text(encoding="utf-8"))
    except Exception:
        return out

    def head(n):
        return n[0].value() if isinstance(n, list) and n \
            and isinstance(n[0], sexpdata.Symbol) else None

    def sval(v):
        return v.value() if isinstance(v, sexpdata.Symbol) else str(v)

    for node in data[1:]:
        if head(node) != "footprint":
            continue
        ref = lcsc = None
        attrs: set[str] = set()
        for sub in node[1:]:
            if head(sub) == "property" and len(sub) >= 3:
                pname = sval(sub[1])
                if pname == "Reference":
                    ref = sval(sub[2])
                elif pname.upper() == "LCSC":
                    lcsc = sval(sub[2])
            elif head(sub) == "attr":
                attrs |= {sval(a) for a in sub[1:]}
        if "dnp" in attrs:
            attr_class = "dnp"
        elif {"exclude_from_bom", "board_only"} & attrs:
            attr_class = "board_feature"
        elif "exclude_from_pos_files" in attrs:
            attr_class = "hand_install"
        else:
            attr_class = None
        if ref and (lcsc or attr_class):
            out[ref] = {"lcsc": lcsc, "mpn": None,
                        "dnp": "dnp" in attrs, "attr_class": attr_class}
    return out


def board_lcsc_map(pcb: Path) -> dict[str, dict]:
    """ref -> {lcsc} for refs the board itself carries an LCSC field for."""
    return {r: f for r, f in board_part_fields(pcb).items() if f.get("lcsc")}


def _iter_part_lines(data):
    """The three tolerated parts.json shapes -> an iterable of line dicts (or
    (ref, lcsc) pairs for the bare mapping shape)."""
    items = data.get("parts", data) if isinstance(data, dict) else data
    if isinstance(items, dict):
        for ref, v in items.items():
            yield ({"refdes": [ref], **v} if isinstance(v, dict)
                   else {"refdes": [ref], "lcsc": v})
    elif isinstance(items, list):
        for ent in items:
            if isinstance(ent, dict):
                yield ent


def _line_refs(ent: dict) -> list[str]:
    refs = ent.get("refdes") or ent.get("refs") or []
    if not refs and ent.get("ref"):
        refs = [ent["ref"]]
    return [str(r).strip() for r in refs if str(r).strip()]


def load_parts_map(path: Path | None) -> dict[str, dict]:
    """ref -> {lcsc, mpn?}. Tolerant of several parts.json shapes:
      {"parts":[{"ref":"U1","lcsc":"C123","mpn":".."}, ...]}
      [{"refs":["R1","R2"],"lcsc":"C1"} , ...]
      {"U1":"C123", "R1":{"lcsc":"C1"}}
    """
    if path is None:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for ent in _iter_part_lines(data):
        lcsc = ent.get("lcsc") or ent.get("LCSC")
        mpn = ent.get("mpn") or ent.get("mfr_part")
        for ref in _line_refs(ent):
            if lcsc:
                out[ref] = {"lcsc": str(lcsc), "mpn": mpn}
    return out


def _check_class(value, where: str) -> str:
    cls = str(value).strip()
    if cls not in ASSEMBLY_CLASSES:
        raise AssemblyDataError(
            f"{where}: unknown assembly_class {value!r} - allowed: "
            + ", ".join(ASSEMBLY_CLASSES))
    return cls


def load_parts_records(path: Path | None) -> list[dict]:
    """parts.json -> canonical assembly records, one per part LINE.

    {refs, lcsc, mpn, value, package, qty_per_board, qty_populated,
     cls (line default | None), refdes_class {ref: cls},
     notes (line default | None), refdes_notes {ref: text}}
    """
    if path is None:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    recs: list[dict] = []
    for i, ent in enumerate(_iter_part_lines(data)):
        refs = _line_refs(ent)
        lcsc = ent.get("lcsc") or ent.get("LCSC") or ""
        where = f"parts line {i} ({lcsc or ent.get('mpn') or refs or '?'})"

        cls = None
        if ent.get("assembly_class"):
            cls = _check_class(ent["assembly_class"], where)

        per_ref: dict[str, str] = {}
        raw = ent.get("refdes_class") or {}
        if not isinstance(raw, dict):
            raise AssemblyDataError(f"{where}: refdes_class must be an object")
        for ref, val in raw.items():
            per_ref[str(ref)] = _check_class(val, f"{where} ref {ref}")
        for ref in (ent.get("refdes_dnp") or []):   # legacy sugar for `dnp`
            per_ref.setdefault(str(ref), "dnp")

        notes_map = ent.get("refdes_notes") or {}
        if not isinstance(notes_map, dict):
            raise AssemblyDataError(f"{where}: refdes_notes must be an object")

        recs.append({
            "refs": refs,
            "lcsc": str(lcsc),
            "distributor": ent.get("distributor") or "",
            "distributor_pn": ent.get("distributor_pn") or "",
            "mpn": ent.get("mpn") or ent.get("mfr_part") or "",
            "value": ent.get("value") or "",
            "package": ent.get("package") or "",
            "qty_per_board": ent.get("qty_per_board"),
            "qty_populated": ent.get("qty_per_board_populated"),
            "cls": cls,
            "refdes_class": per_ref,
            "notes": ent.get("assembly_notes") or None,
            "refdes_notes": {str(k): str(v) for k, v in notes_map.items()},
        })
    return recs


def resolve_assembly(pos_refs: set[str], records: list[dict],
                     board_fields: dict[str, dict]
                     ) -> tuple[dict[str, str], dict[str, str],
                                dict[str, str]]:
    """-> (ref -> class, ref -> instructions, ref -> where the class came from).

    Covers every ref in the position export plus every ref named in the
    canonical parts data, so an off-board or customer-supplied part that has no
    placement still reaches the BOM of record."""
    cls: dict[str, str] = {}
    src: dict[str, str] = {}
    note: dict[str, str] = {}

    for ref in pos_refs:
        cls[ref], src[ref] = PLACED_CLASS, "default"
    # 3. the board's own footprint attributes
    for ref, f in board_fields.items():
        if f.get("attr_class"):
            cls[ref], src[ref] = f["attr_class"], "board_attr"
    # 2. the parts line default
    for rec in records:
        for ref in rec["refs"]:
            if rec["cls"]:
                cls[ref], src[ref] = rec["cls"], "parts_line"
            else:
                cls.setdefault(ref, PLACED_CLASS)
                src.setdefault(ref, "default")
            if rec["notes"]:
                note[ref] = rec["notes"]
    # 1. the per-ref override
    for rec in records:
        for ref, c in rec["refdes_class"].items():
            cls[ref], src[ref] = c, "parts_ref"
        for ref, txt in rec["refdes_notes"].items():
            note[ref] = txt

    for ref, c in cls.items():
        if not note.get(ref):
            note[ref] = CLASS_INSTRUCTION[c]
    return cls, note, src


# --------------------------------------------------------------- BOM / CPL

def _natural_key(ref: str):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def build_bom(parts: list[dict], parts_map: dict[str, dict]) -> list[dict]:
    """Group by (value, footprint, LCSC) -> JLC upload rows.

    `parts` must already be the placed set (see run()); this function does not
    decide membership."""
    groups: dict[tuple, list[str]] = {}
    for p in parts:
        lcsc = parts_map.get(p["ref"], {}).get("lcsc", "")
        key = (p["val"], p["package"], lcsc)
        groups.setdefault(key, []).append(p["ref"])
    rows = []
    for (val, pkg, lcsc), refs in groups.items():
        refs_sorted = sorted(refs, key=_natural_key)
        rows.append({
            "Comment": val,
            "Designator": ",".join(refs_sorted),
            "Footprint": pkg,
            "LCSC": lcsc,
        })
    rows.sort(key=lambda r: _natural_key(r["Designator"].split(",")[0]))
    return rows


BOM_FULL_FIELDS = ["Comment", "Designator", "Qty Per Board", "Footprint",
                   "MPN", "LCSC", "Assembly Class", "Instructions"]


def build_bom_full(parts: list[dict], records: list[dict],
                   classes: dict[str, str], notes: dict[str, str],
                   parts_map: dict[str, dict]) -> list[dict]:
    """The BOM of record: every classified refdes, plus refdes-less lines that
    declare a non-placed class (screws, straps, a heatsink)."""
    pos_by_ref = {p["ref"]: p for p in parts}
    rec_by_ref: dict[str, dict] = {}
    for rec in records:
        for ref in rec["refs"]:
            rec_by_ref.setdefault(ref, rec)

    groups: dict[tuple, list[str]] = {}
    for ref in sorted(classes, key=_natural_key):
        pos = pos_by_ref.get(ref)
        rec = rec_by_ref.get(ref, {})
        comment = pos["val"] if pos else (rec.get("value") or "")
        pkg = pos["package"] if pos else (rec.get("package") or "")
        key = (comment, pkg, rec.get("mpn", ""),
               parts_map.get(ref, {}).get("lcsc", "") or rec.get("lcsc", ""),
               classes[ref], notes.get(ref, ""))
        groups.setdefault(key, []).append(ref)

    rows = []
    for key, refs in groups.items():
        comment, pkg, mpn, lcsc, cls, note = key
        refs_sorted = sorted(refs, key=_natural_key)
        rows.append({
            "Comment": comment,
            "Designator": ",".join(refs_sorted),
            "Qty Per Board": str(len(refs_sorted)),
            "Footprint": pkg,
            "MPN": mpn,
            "LCSC": lcsc,
            "Assembly Class": cls,
            "Instructions": note,
        })

    # Lines with no refdes at all are only carried when they explicitly declare
    # a non-placed class - otherwise they are the S6 per-distinct-part shape,
    # already covered through the position export.
    for rec in records:
        if rec["refs"] or not rec["cls"] or rec["cls"] == PLACED_CLASS:
            continue
        rows.append({
            "Comment": rec["value"],
            "Designator": "",
            "Qty Per Board": str(rec["qty_per_board"] or 1),
            "Footprint": rec["package"],
            "MPN": rec["mpn"],
            "LCSC": rec["lcsc"],
            "Assembly Class": rec["cls"],
            "Instructions": rec["notes"] or CLASS_INSTRUCTION[rec["cls"]],
        })

    rows.sort(key=lambda r: (CLASS_ORDER[r["Assembly Class"]],
                             _natural_key(r["Designator"].split(",")[0])))
    return rows


def build_cpl(parts: list[dict], rules) -> tuple[list[dict], list[dict]]:
    """CPL rows + a parallel rotation-correction audit trail."""
    cpl, audit = [], []
    for p in sorted(parts, key=lambda q: _natural_key(q["ref"])):
        final, corr, pat = correct_rotation(p["package"], p["rot"], rules)
        layer = "Bottom" if p["side"] in ("bottom", "back") else "Top"
        cpl.append({
            "Designator": p["ref"],
            "Mid X": f'{p["x"]:.4f}',
            "Mid Y": f'{p["y"]:.4f}',
            "Layer": layer,
            "Rotation": f"{final:.4f}",
        })
        audit.append({"ref": p["ref"], "package": p["package"],
                      "base_rot": round(p["rot"], 4),
                      "correction": corr, "final_rot": round(final, 4),
                      "matched": pat, "layer": layer})
    return cpl, audit


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def check_declared_quantities(records: list[dict],
                              classes: dict[str, str]) -> list[dict]:
    """`qty_per_board_populated` (and `qty_per_board`) on a parts line are the
    owner's declaration of how many sites ship fitted. Derive the same number
    from the classes and refuse to disagree silently - this is the guard the
    board-local rf-de filter used to carry."""
    out = []
    for rec in records:
        if not rec["refs"]:
            continue
        placed = [r for r in rec["refs"]
                  if classes.get(r, PLACED_CLASS) == PLACED_CLASS]
        want = rec["qty_populated"]
        if want is None and rec["qty_per_board"] is not None \
                and len(placed) == len(rec["refs"]):
            want = rec["qty_per_board"]
        if want is None:
            continue
        if int(want) != len(placed):
            out.append({"lcsc": rec["lcsc"], "mpn": rec["mpn"],
                        "declared_populated": int(want),
                        "derived_populated": len(placed),
                        "refs": list(rec["refs"])})
    return out


def run(pcb: Path, out_dir: Path, pos: Path | None = None,
        parts_json: Path | None = None, rotations: Path | None = None,
        name: str | None = None) -> dict:
    name = name or pcb.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = load_rotations(rotations or REF_ROTATIONS)
    parts = parse_pos_csv(_get_pos(pcb, pos, out_dir, name))
    board_fields = board_part_fields(pcb)
    records = load_parts_records(parts_json)
    # board footprint LCSC fields first; per-ref parts.json entries override
    parts_map = {**{r: f for r, f in board_fields.items() if f.get("lcsc")},
                 **load_parts_map(parts_json)}

    pos_refs = {p["ref"] for p in parts}
    classes, notes, sources = resolve_assembly(pos_refs, records, board_fields)

    placed = [p for p in parts if classes[p["ref"]] == PLACED_CLASS]
    # Classed `smt_placed` but never exported a position: either the part is
    # missing from the board or its class is wrong. Both are release defects,
    # so this is a violation rather than a silently shorter BOM.
    unplaced_smt = sorted((r for r, c in classes.items()
                           if c == PLACED_CLASS and r not in pos_refs),
                          key=_natural_key)
    not_placed = [{"ref": r, "class": classes[r], "source": sources[r]}
                  for r in sorted(pos_refs - {p["ref"] for p in placed},
                                  key=_natural_key)]

    bom_rows = build_bom(placed, parts_map)
    bom_full_rows = build_bom_full(parts, records, classes, notes, parts_map)
    cpl_rows, audit = build_cpl(placed, rules)
    qty_mismatch = check_declared_quantities(records, classes)

    bom_path = out_dir / "BOM.csv"
    bom_full_path = out_dir / "BOM-full.csv"
    cpl_path = out_dir / "CPL.csv"
    _write_csv(bom_path, ["Comment", "Designator", "Footprint", "LCSC"], bom_rows)
    _write_csv(bom_full_path, BOM_FULL_FIELDS, bom_full_rows)
    _write_csv(cpl_path, ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"],
               cpl_rows)

    # A BOM line is COMPLETE when the part can actually be bought: an LCSC
    # number, or a manufacturer part number with a named distributor line. A
    # part nobody places needs neither - an off-board load, a customer's screw
    # and an empty DNP land are all complete entries with nothing at all
    # (codex H1). Not being on LCSC is a separate, weaker fact: JLC cannot
    # source it, which only matters if the board is a PCBA build.
    alt_sourced = set()
    for rec in records:
        if rec["mpn"] and (rec["distributor_pn"] or rec["distributor"]):
            alt_sourced |= set(rec["refs"])

    def _no_lcsc(refs):
        return sorted((r for r in refs
                       if not parts_map.get(r, {}).get("lcsc")),
                      key=_natural_key)

    missing = _no_lcsc(p["ref"] for p in placed)
    unsourced = [r for r in missing if r not in alt_sourced]
    off_lcsc = [r for r in missing if r in alt_sourced]
    missing_unplaced = _no_lcsc(r for r, c in classes.items()
                                if c != PLACED_CLASS)

    class_counts: dict[str, int] = {}
    for c in classes.values():
        class_counts[c] = class_counts.get(c, 0) + 1

    violations = []
    if unsourced:
        violations.append({
            "kind": "bom_unsourced", "refs": unsourced,
            "message": f"{len(unsourced)} machine-placed part(s) have neither "
                       f"an LCSC number nor a distributor line"})
    if unplaced_smt:
        violations.append({
            "kind": "assembly_unplaced_smt", "refs": unplaced_smt,
            "message": f"{len(unplaced_smt)} part(s) are classed "
                       f"{PLACED_CLASS} but have no placement"})
    for m in qty_mismatch:
        violations.append({
            "kind": "assembly_qty_mismatch", "refs": m["refs"],
            "message": f"{m['lcsc'] or m['mpn']}: parts.json declares "
                       f"{m['declared_populated']} populated, classes give "
                       f"{m['derived_populated']}"})

    corrected = [a for a in audit if a["correction"] != 0.0]
    return {
        "script": "bom_cpl",
        "status": "violations" if violations else "pass",
        "board": pcb.name,
        "n_parts": len(parts),
        "n_placed": len(placed),
        "bom": str(bom_path),
        "bom_full": str(bom_full_path),
        "cpl": str(cpl_path),
        "bom_rows": bom_rows,
        "bom_full_rows": bom_full_rows,
        "cpl_rows": cpl_rows,
        "assembly_classes": {r: classes[r] for r in sorted(classes,
                                                           key=_natural_key)},
        "class_counts": class_counts,
        "not_placed": not_placed,
        "rotation_audit": audit,
        "n_rotation_corrections": len(corrected),
        "missing_lcsc": missing,
        "missing_lcsc_unplaced": missing_unplaced,
        "unsourced": unsourced,
        "off_lcsc": off_lcsc,
        "unplaced_smt": unplaced_smt,
        "qty_mismatch": qty_mismatch,
        "violations": violations,
        "bom_complete": not unsourced,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True, help="input .kicad_pcb")
    ap.add_argument("--out-dir", required=True, help="fab output directory")
    ap.add_argument("--pos", help="pre-exported pos CSV (else export via kc.py)")
    ap.add_argument("--parts", help="parts.json ref->LCSC map (BOM-of-record)")
    ap.add_argument("--rotations", help="override reference/jlc_rotations.csv")
    ap.add_argument("--name", help="basename (default: board stem)")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    try:
        rep = run(Path(args.pcb), Path(args.out_dir),
                  pos=Path(args.pos) if args.pos else None,
                  parts_json=Path(args.parts) if args.parts else None,
                  rotations=Path(args.rotations) if args.rotations else None,
                  name=args.name)
    except Exception as exc:  # noqa: BLE001 (SPEC: any error -> exit 2)
        err = {"script": "bom_cpl", "status": "error",
               "error": f"{type(exc).__name__}: {exc}"}
        text = json.dumps(err, indent=1)
        (Path(args.out).write_text(text, encoding="utf-8") if args.out
         else print(text))
        return 2

    text = json.dumps(rep, indent=1)
    (Path(args.out).write_text(text, encoding="utf-8") if args.out
     else print(text))
    return 0 if rep["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
