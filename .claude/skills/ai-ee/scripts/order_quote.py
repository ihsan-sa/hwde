#!/usr/bin/env python
"""order_quote.py - JLCPCB quote matrix + lead times (SPEC P10).

Builds the qty x surface-finish x mask-colour x assembly matrix the ordering
agent presents at human checkpoint 5, from the board's real geometry (area and
layer count come from the board file, not from a guess) and the transcribed
price points in reference/jlc_pricing.yaml.

HONESTY CONTRACT: every figure here is an ESTIMATE and is labelled as one.
JLC's authoritative price depends on panelisation, promotions, region and
shipping; only the instant-quote page (or the credentialed API) can produce a
real number. The report always carries `estimated: true` and the deep link to
the authoritative quote page, so the human checkpoint compares against reality
instead of trusting this table.

CLI:
  order_quote.py --pcb board.kicad_pcb [--qty 5,10,30] [--assembly]
                 [--parts parts.json] [--finish HASL,ENIG] [--colors green,black]
                 [--pricing jlc_pricing.yaml] [--out quote.json]
Exit 0 ok / 2 error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

import yaml  # noqa: E402

import geom  # noqa: E402

PRICING = SCRIPTS.parent / "reference" / "jlc_pricing.yaml"


def load_pricing(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "pcb" not in data:
        raise ValueError(f"{path} is not a pricing table")
    return data


def board_size(pcb: Path) -> tuple[float, float, float]:
    """(width_mm, height_mm, area_dm2) from the board outline."""
    bg = geom.load_board(pcb)
    outline = bg.outline          # geom exposes this as an attribute
    if outline is None or outline.is_empty:
        raise ValueError(f"{pcb.name} has no board outline (Edge.Cuts)")
    x0, y0, x1, y1 = outline.bounds
    w, h = x1 - x0, y1 - y0
    return w, h, (w * h) / 10000.0


def _nearest_qty_price(table: dict, qty: int) -> tuple[float, int]:
    """Price at the closest listed quantity >= qty (else the largest listed),
    scaled linearly when qty exceeds every listed break."""
    breaks = sorted(int(k) for k in table)
    for b in breaks:
        if qty <= b:
            return float(table[b]), b
    top = breaks[-1]
    return float(table[top]) * qty / top, top


def pcb_cost(pricing: dict, layers: int, qty: int, w: float, h: float,
             finish: str, color: str, thickness: float = 1.6) -> dict:
    pcb = pricing["pcb"]
    base_table = pcb["base"].get(layers) or pcb["base"].get(str(layers))
    if base_table is None:
        raise ValueError(f"no price points for {layers}-layer boards")
    base, at_qty = _nearest_qty_price(base_table, qty)

    promo = float(pcb.get("promo_max_mm", 100))
    oversize = 0.0
    if w > promo or h > promo:
        rate = (pcb.get("oversize_per_dm2", {}).get(layers)
                or pcb.get("oversize_per_dm2", {}).get(str(layers)) or 0.0)
        area_dm2 = (w * h) / 10000.0
        oversize = float(rate) * area_dm2 * qty

    opts = pricing.get("options", {})
    adders = (float(opts.get("surface_finish", {}).get(finish, 0.0))
              + float(opts.get("solder_mask_color", {}).get(color, 0.0))
              + float(opts.get("thickness_mm", {}).get(thickness, 0.0)))
    total = base + oversize + adders
    return {"base": round(base, 2), "base_at_qty": at_qty,
            "oversize": round(oversize, 2), "options": round(adders, 2),
            "total": round(total, 2)}


def assembly_cost(pricing: dict, qty: int, n_parts: int, n_joints: int,
                  n_extended: int, stencil: bool = True) -> dict:
    a = pricing.get("assembly", {})
    setup = float(a.get("setup_fee", 0.0))
    feeders = float(a.get("per_extended_part_feeder", 0.0)) * n_extended
    joints = float(a.get("per_joint", 0.0)) * n_joints * qty
    sten = float(a.get("stencil", 0.0)) if stencil else 0.0
    total = setup + feeders + joints + sten
    return {"setup": round(setup, 2), "feeders": round(feeders, 2),
            "joints": round(joints, 2), "stencil": round(sten, 2),
            "n_parts": n_parts, "n_joints": n_joints,
            "n_extended_parts": n_extended, "total": round(total, 2)}


def _assembly_counts(pcb: Path, parts_json: Path | None) -> tuple[int, int, int]:
    """(n_parts, n_joints, n_extended) from the board's real pads."""
    bg = geom.load_board(pcb)
    refs: dict[str, int] = {}
    for pad in bg.pads_of():
        if pad.net is None:
            continue
        refs[pad.ref] = refs.get(pad.ref, 0) + 1
    n_parts = len(refs)
    n_joints = sum(refs.values())
    n_extended = 0
    if parts_json is not None and Path(parts_json).exists():
        import bom_cpl
        pmap = bom_cpl.load_parts_map(Path(parts_json))
        data = json.loads(Path(parts_json).read_text(encoding="utf-8"))
        items = data.get("parts", data) if isinstance(data, dict) else data
        basic_by_ref: dict[str, bool] = {}
        if isinstance(items, list):
            for ent in items:
                if not isinstance(ent, dict):
                    continue
                is_basic = bool(ent.get("basic", ent.get("type", "") == "Basic"))
                for r in (ent.get("refs") or
                          ([ent["ref"]] if ent.get("ref") else [])):
                    basic_by_ref[str(r)] = is_basic
        n_extended = sum(1 for r in pmap if not basic_by_ref.get(r, False))
    return n_parts, n_joints, n_extended


def run(pcb: Path, qtys: list[int], finishes: list[str], colors: list[str],
        assembly: bool = False, parts_json: Path | None = None,
        pricing_path: Path | None = None, thickness: float = 1.6) -> dict:
    pricing = load_pricing(pricing_path or PRICING)
    w, h, area_dm2 = board_size(pcb)
    bg = geom.load_board(pcb)
    layers = len(bg.stackup.copper_layers)

    n_parts, n_joints, n_extended = (0, 0, 0)
    if assembly:
        n_parts, n_joints, n_extended = _assembly_counts(pcb, parts_json)

    matrix = []
    for qty in qtys:
        for finish in finishes:
            for color in colors:
                pc = pcb_cost(pricing, layers, qty, w, h, finish, color,
                              thickness)
                row = {"qty": qty, "surface_finish": finish,
                       "solder_mask_color": color, "pcb": pc,
                       "total": pc["total"]}
                if assembly:
                    ac = assembly_cost(pricing, qty, n_parts, n_joints,
                                       n_extended)
                    row["assembly"] = ac
                    row["total"] = round(pc["total"] + ac["total"], 2)
                row["unit_cost"] = round(row["total"] / qty, 2)
                matrix.append(row)
    matrix.sort(key=lambda r: (r["qty"], r["total"]))

    lt = pricing.get("lead_time_days", {})
    pcb_lt = (lt.get("pcb", {}).get(layers)
              or lt.get("pcb", {}).get(str(layers)) or {})
    lead = {"pcb_days": pcb_lt,
            "assembly_additional_days": lt.get("assembly_additional")
            if assembly else 0,
            "note": lt.get("note")}

    return {
        "script": "order_quote",
        "status": "pass",
        "board": pcb.name,
        "estimated": True,
        "disclaimer": "Estimates from reference/jlc_pricing.yaml - NOT a quote. "
                      "Confirm at the authoritative quote URL before ordering.",
        "authoritative_quote_url":
            pricing.get("meta", {}).get("authoritative_quote_url"),
        "pricing_verified": pricing.get("meta", {}).get("verified"),
        "currency": pricing.get("meta", {}).get("currency", "USD"),
        "spec": {"layers": layers, "width_mm": round(w, 2),
                 "height_mm": round(h, 2), "area_dm2": round(area_dm2, 4),
                 "thickness_mm": thickness, "assembly": assembly,
                 "n_parts": n_parts, "n_joints": n_joints,
                 "n_extended_parts": n_extended},
        "lead_time": lead,
        "matrix": matrix,
        "cheapest": matrix[0] if matrix else None,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--qty", default="5,10,30",
                    help="comma list of quantities (default 5,10,30)")
    ap.add_argument("--finish", default="HASL,ENIG")
    ap.add_argument("--colors", default="green")
    ap.add_argument("--thickness", type=float, default=1.6)
    ap.add_argument("--assembly", action="store_true",
                    help="include SMT assembly in the matrix")
    ap.add_argument("--parts", help="parts.json (Basic/Extended feeder fees)")
    ap.add_argument("--pricing", help="override reference/jlc_pricing.yaml")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    try:
        rep = run(Path(args.pcb),
                  [int(q) for q in args.qty.split(",") if q.strip()],
                  [f.strip() for f in args.finish.split(",") if f.strip()],
                  [c.strip() for c in args.colors.split(",") if c.strip()],
                  assembly=args.assembly,
                  parts_json=Path(args.parts) if args.parts else None,
                  pricing_path=Path(args.pricing) if args.pricing else None,
                  thickness=args.thickness)
    except Exception as exc:  # noqa: BLE001
        err = {"script": "order_quote", "status": "error",
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
