"""boardreg.py - a board workspace's part number, read from the boards register.

Board part numbers live in one place: register.yaml at the root of the boards
repo (env.boards_root(), HWDE_BOARDS_ROOT, default ~/dev/boards). Numbering is
the document library's PCB-NNNN-R scheme - four digits and a revision letter
(A, B, C..., skipping I and O):

  products:
    PCB-0001:
      title: <what the board is>
      revs:
        A: {dir: pd-trigger-lite, date: 2026-09-24, bom: pd-trigger-lite/fab/BOM.csv}
        B: {dir: pd-trigger-lite-dip, date: ..., change: "..."}

A workspace's number is the product key plus the rev letter whose `dir` is
the workspace's directory name (PCB-0001-B). The register read is the one in
the directory that holds the workspace, so a scratch copy elsewhere never
borrows a real board's number. hwde only READS the register: it never
allocates a number, and a board that is not in it carries none.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REGISTER = "register.yaml"
_PRODUCT = re.compile(r"^PCB-\d{4}$")
_REV = re.compile(r"^[A-HJ-NP-Z]$")


def part_number(ws: Path) -> tuple[dict | None, str]:
    """(number, why) for the workspace `ws`.

    number is {"pn": "PCB-0001-B", "product": "PCB-0001", "rev": "B",
    "title": ..., "register": <path>} or None; why says in words why there
    is none (no register, not listed, unreadable) and is "" when found.
    """
    ws = Path(ws).resolve()
    reg = ws.parent / REGISTER
    if not reg.is_file():
        return None, f"no {REGISTER} beside the workspace ({ws.parent})"
    try:
        data = yaml.safe_load(reg.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        return None, f"{reg} unreadable: {type(exc).__name__}: {exc}"
    products = data.get("products") if isinstance(data, dict) else None
    if not isinstance(products, dict):
        return None, f"{reg} has no products map"
    hits = []
    for product, ent in products.items():
        revs = (ent or {}).get("revs") if isinstance(ent, dict) else None
        for rev, r in (revs or {}).items():
            if isinstance(r, dict) and r.get("dir") == ws.name:
                hits.append((str(product), str(rev), ent))
    if not hits:
        return None, f"{ws.name} is not in {reg}"
    if len(hits) > 1:
        return None, (f"{ws.name} is listed {len(hits)} times in {reg} ("
                      + ", ".join(f"{p}-{r}" for p, r, _ in hits) + ")")
    product, rev, ent = hits[0]
    if not _PRODUCT.match(product) or not _REV.match(rev):
        return None, f"{product}-{rev} in {reg} is not a PCB-NNNN-R number"
    return {"pn": f"{product}-{rev}", "product": product, "rev": rev,
            "title": ent.get("title"), "register": str(reg)}, ""
