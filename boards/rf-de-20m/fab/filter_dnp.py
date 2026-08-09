#!/usr/bin/env python
"""filter_dnp.py - strip the DNP sites out of fab/BOM.csv and fab/CPL.csv.

MANDATORY POST-STEP AFTER EVERY bom_cpl.py RUN ON THIS BOARD.

Why this file exists (reports/route-notes.md s17, parts/parts.json _meta):
`kicad-sch-api`'s writer hard-codes `(dnp no)`, so this board's generators mark
do-not-populate with a VISIBLE `Variant=DNP` schematic field - and NOTHING in
the ai-ee pipeline reads `Variant`: not bom_cpl.py, not netlist_audit, not any
check_*. A BOM/CPL straight out of bom_cpl.py therefore tells the assembler to
fit ALL NINE DNP sites. Three of them (C203, C308, C309) are the P8 ZVS fix;
fitting them puts the board back into hard switching at ~53 W instead of
~113.8 W. The other six are bench-trim sites that must ship empty.

The authoritative list is `refdes_dnp` on each line of parts/parts.json - this
script reads it, it does not hard-code it.

BOM.csv has no Quantity column (JLC derives quantity from the Designator list),
so "correcting the quantity" IS removing the refdes from that list. The script
asserts each surviving line's designator count equals the line's
`qty_per_board_populated` (or `qty_per_board` when no site on it is DNP).

Exit 0 = filtered and verified; exit 2 = anything failed to verify.

CLI:  filter_dnp.py [--fab-dir DIR] [--parts parts.json] [--out report.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent


def load_dnp(parts_json: Path) -> tuple[list[str], dict[str, dict]]:
    data = json.loads(parts_json.read_text(encoding="utf-8"))
    dnp: list[str] = []
    by_lcsc: dict[str, dict] = {}
    for line in data["parts"]:
        refs = list(line.get("refdes") or [])
        d = list(line.get("refdes_dnp") or [])
        dnp += d
        want = line.get("qty_per_board_populated")
        if want is None:
            want = line.get("qty_per_board", len(refs))
        by_lcsc[line.get("lcsc") or ""] = {
            "refdes": refs, "dnp": d, "want_populated": want}
    return sorted(set(dnp)), by_lcsc


def filter_cpl(path: Path, dnp: set[str]) -> tuple[int, int, list[str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        fields = rd.fieldnames or []
        rows = list(rd)
    before = len(rows)
    dropped = [r["Designator"] for r in rows if r["Designator"] in dnp]
    keep = [r for r in rows if r["Designator"] not in dnp]
    with path.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, lineterminator="\r\n")
        wr.writeheader()
        wr.writerows(keep)
    return before, len(keep), sorted(dropped)


def filter_bom(path: Path, dnp: set[str]) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        fields = rd.fieldnames or []
        rows = list(rd)
    out, log = [], []
    for r in rows:
        refs = [d.strip() for d in r["Designator"].split(",") if d.strip()]
        keep = [d for d in refs if d not in dnp]
        removed = [d for d in refs if d in dnp]
        if not keep:
            # No line on this board goes to zero; if one ever did it must be
            # DELETED, not shipped with an empty designator list.
            log.append({"lcsc": r.get("LCSC"), "before": len(refs),
                        "after": 0, "removed": removed, "line_dropped": True})
            continue
        r["Designator"] = ",".join(keep)
        out.append(r)
        log.append({"lcsc": r.get("LCSC"), "before": len(refs),
                    "after": len(keep), "removed": removed,
                    "line_dropped": False})
    with path.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, lineterminator="\r\n")
        wr.writeheader()
        wr.writerows(out)
    return log


def verify(fab: Path, dnp: list[str], by_lcsc: dict[str, dict]) -> dict:
    """Re-READ the written files and prove the filter worked."""
    errors: list[str] = []
    dnpset = set(dnp)

    cpl_text = (fab / "CPL.csv").read_text(encoding="utf-8")
    bom_text = (fab / "BOM.csv").read_text(encoding="utf-8")

    with (fab / "CPL.csv").open(newline="", encoding="utf-8") as fh:
        cpl = list(csv.DictReader(fh))
    with (fab / "BOM.csv").open(newline="", encoding="utf-8") as fh:
        bom = list(csv.DictReader(fh))

    cpl_refs = [r["Designator"] for r in cpl]
    bom_refs: list[str] = []
    for r in bom:
        bom_refs += [d.strip() for d in r["Designator"].split(",") if d.strip()]

    for ref in dnp:
        if ref in cpl_refs:
            errors.append(f"{ref} still a CPL row")
        if ref in bom_refs:
            errors.append(f"{ref} still in a BOM designator list")
        # Belt and braces: raw substring scan, so a stray occurrence in any
        # other column (Comment, Footprint, ...) is caught too.
        for label, text in (("CPL.csv", cpl_text), ("BOM.csv", bom_text)):
            for tok in (f",{ref},", f",{ref}\n", f",{ref}\r",
                        f'"{ref},', f',{ref}"', f"\n{ref},"):
                if tok in text:
                    errors.append(f"{ref} appears raw in {label} ({tok!r})")
                    break

    if len(cpl_refs) != len(set(cpl_refs)):
        errors.append("duplicate designators in CPL")
    if len(bom_refs) != len(set(bom_refs)):
        errors.append("duplicate designators in BOM")
    if sorted(cpl_refs) != sorted(bom_refs):
        only_cpl = sorted(set(cpl_refs) - set(bom_refs))
        only_bom = sorted(set(bom_refs) - set(cpl_refs))
        errors.append(f"BOM/CPL disagree - CPL only {only_cpl}, "
                      f"BOM only {only_bom}")

    for r in bom:
        lcsc = r.get("LCSC") or ""
        info = by_lcsc.get(lcsc)
        n = len([d for d in r["Designator"].split(",") if d.strip()])
        if info is None:
            errors.append(f"BOM line {lcsc} not in parts.json")
        elif n != info["want_populated"]:
            errors.append(f"BOM line {lcsc}: {n} designators, parts.json "
                          f"says {info['want_populated']} populated")

    return {"errors": errors, "cpl_rows": len(cpl_refs),
            "bom_lines": len(bom), "bom_refs": len(bom_refs)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fab-dir", default=str(HERE))
    ap.add_argument("--parts", default=str(WORKSPACE / "parts" / "parts.json"))
    ap.add_argument("--expect-cpl-rows", type=int, default=59,
                    help="hard expectation for the populated part count")
    ap.add_argument("--out", help="write JSON report here instead of stdout")
    args = ap.parse_args(argv)

    fab = Path(args.fab_dir)
    dnp, by_lcsc = load_dnp(Path(args.parts))

    before, after, dropped = filter_cpl(fab / "CPL.csv", set(dnp))
    bom_log = filter_bom(fab / "BOM.csv", set(dnp))
    ver = verify(fab, dnp, by_lcsc)

    if sorted(dropped) != sorted(dnp):
        ver["errors"].append(
            f"CPL dropped {sorted(dropped)}, parts.json DNP is {sorted(dnp)}")
    if after != args.expect_cpl_rows:
        ver["errors"].append(
            f"CPL has {after} rows, expected {args.expect_cpl_rows}")

    rep = {
        "script": "filter_dnp",
        "status": "pass" if not ver["errors"] else "error",
        "dnp_refs": dnp,
        "n_dnp": len(dnp),
        "cpl_rows_before": before,
        "cpl_rows_after": after,
        "cpl_dropped": dropped,
        "bom_lines": bom_log,
        "verification": ver,
    }
    text = json.dumps(rep, indent=1)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if rep["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
