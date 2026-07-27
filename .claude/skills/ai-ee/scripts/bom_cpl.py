#!/usr/bin/env python
"""bom_cpl.py - JLCPCB assembly files: BOM.csv + CPL.csv with rotation fixes.

The P9 assembly-format step (SPEC 6.4). Turns kicad-cli's placement (pos) export
into the two CSVs JLC's SMT assembly wants, replicating the kicad-jlcpcb-tools
conventions (NOT the GUI plugin):

  BOM.csv  columns: Comment, Designator, Footprint, LCSC
           one row per (value, footprint, LCSC) group; Designator is the
           comma-joined refdes list. LCSC comes from a parts.json map
           (BOM-of-record); refs with no LCSC are reported (fab-release gate).

  CPL.csv  columns: Designator, Mid X, Mid Y, Layer, Rotation
           Mid X/Y in mm from the pos file; Layer Top/Bottom; Rotation =
           (kicad rotation + JLC correction) mod 360. The correction is the
           notorious KiCad<->JLC 0-degree-reference offset, vendored per package
           family in reference/jlc_rotations.csv (regex on the footprint name,
           first match wins - LEARNINGS/S8).

bom_cpl GENERATES; polarity/rotation VALIDATION (catching a backwards part) is
dfm_check.py's job. The pos file already omits parts flagged
exclude-from-pos/DNP (board_init marks mounting holes so), so BOM and CPL cover
exactly the assembled set.

CLI:
  bom_cpl.py --pcb board.kicad_pcb --out-dir fab/ [--pos pos.csv]
             [--parts parts.json] [--rotations jlc_rotations.csv]
             [--name NAME] [--out report.json]
Exit 0 ok / 2 error.
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

    def put(ref, lcsc, mpn=None):
        if ref and lcsc:
            out[str(ref)] = {"lcsc": str(lcsc), "mpn": mpn}

    items = data.get("parts", data) if isinstance(data, dict) else data
    if isinstance(items, dict):
        for ref, v in items.items():
            if isinstance(v, dict):
                put(ref, v.get("lcsc") or v.get("LCSC"), v.get("mpn"))
            else:
                put(ref, v)
    elif isinstance(items, list):
        for ent in items:
            if not isinstance(ent, dict):
                continue
            lcsc = ent.get("lcsc") or ent.get("LCSC")
            mpn = ent.get("mpn") or ent.get("mfr_part")
            refs = ent.get("refs") or ([ent["ref"]] if ent.get("ref") else [])
            for ref in refs:
                put(ref, lcsc, mpn)
    return out


# --------------------------------------------------------------- BOM / CPL

def _natural_key(ref: str):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def build_bom(parts: list[dict], parts_map: dict[str, dict]) -> list[dict]:
    """Group by (value, footprint, LCSC) -> BOM rows."""
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


def run(pcb: Path, out_dir: Path, pos: Path | None = None,
        parts_json: Path | None = None, rotations: Path | None = None,
        name: str | None = None) -> dict:
    name = name or pcb.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = load_rotations(rotations or REF_ROTATIONS)
    parts = parse_pos_csv(_get_pos(pcb, pos, out_dir, name))
    parts_map = load_parts_map(parts_json)

    bom_rows = build_bom(parts, parts_map)
    cpl_rows, audit = build_cpl(parts, rules)

    bom_path = out_dir / "BOM.csv"
    cpl_path = out_dir / "CPL.csv"
    _write_csv(bom_path, ["Comment", "Designator", "Footprint", "LCSC"], bom_rows)
    _write_csv(cpl_path, ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"],
               cpl_rows)

    missing = sorted((p["ref"] for p in parts
                      if not parts_map.get(p["ref"], {}).get("lcsc")),
                     key=_natural_key)
    corrected = [a for a in audit if a["correction"] != 0.0]
    return {
        "script": "bom_cpl",
        "status": "pass",
        "board": pcb.name,
        "n_parts": len(parts),
        "bom": str(bom_path),
        "cpl": str(cpl_path),
        "bom_rows": bom_rows,
        "cpl_rows": cpl_rows,
        "rotation_audit": audit,
        "n_rotation_corrections": len(corrected),
        "missing_lcsc": missing,
        "bom_complete": not missing,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
