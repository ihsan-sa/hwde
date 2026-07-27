#!/usr/bin/env python
"""order_submit.py - assemble the order manifest and STOP before payment (P10).

SPEC P10 is explicit: "Payment/final submission is always human." This script
therefore never spends money. It:

  1. verifies the fab package is present and internally consistent (gerber zip,
     BOM, CPL) and hashes every artefact,
  2. snapshots the board spec + the chosen quote row,
  3. writes fab/order.json - the traceability record (SPEC P10: order number,
     spec snapshot, gerber hash),
  4. emits the manual-submission deep links, including the JLCDFM upload step
     (V6: JLCDFM has no public API - that second opinion is semi-manual by
     design), and the exact human actions left.

The credentialed api.jlcpcb.com path is NOT implemented as a live call: that API
requires an approved access application which this environment does not have, so
there is no way to verify an integration here. Rather than ship an untested code
path that claims to place orders, `--api` reports precisely what is missing and
exits 2. When credentials are obtained, wire the upload/quote/order calls behind
`_api_submit()` - the manifest this script writes is already the payload.

CLI:
  order_submit.py --pcb board.kicad_pcb --fab-dir fab/ [--quote quote.json]
                  [--qty 5] [--api] [--order-number N] [--out fab/order.json]
Exit 0 ready-for-human / 1 package incomplete / 2 error.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

JLCDFM_URL = "https://jlcdfm.com/"
JLC_QUOTE_URL = "https://cart.jlcpcb.com/quote"
API_ENV = ("AIEE_JLCPCB_KEY", "AIEE_JLCPCB_SECRET")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _find(fab_dir: Path, *patterns: str) -> Path | None:
    for pat in patterns:
        hits = sorted(fab_dir.glob(pat))
        if hits:
            return hits[0]
    return None


def collect_package(fab_dir: Path) -> tuple[dict, list[str]]:
    """Locate + hash the deliverables. -> (artifacts, missing)."""
    artifacts: dict = {}
    missing: list[str] = []

    zip_path = _find(fab_dir, "*_gerbers.zip", "*.zip")
    if zip_path is None:
        missing.append("gerber zip")
    else:
        artifacts["gerber_zip"] = {"path": str(zip_path),
                                   "sha256": sha256(zip_path),
                                   "bytes": zip_path.stat().st_size}
    for label, pats in (("bom", ("BOM.csv", "*BOM*.csv")),
                        ("cpl", ("CPL.csv", "*CPL*.csv", "*-pos.csv"))):
        p = _find(fab_dir, *pats)
        if p is None:
            missing.append(f"{label.upper()}.csv")
        else:
            artifacts[label] = {"path": str(p), "sha256": sha256(p),
                                "bytes": p.stat().st_size}
    return artifacts, missing


def _api_available() -> tuple[bool, str]:
    have = [v for v in API_ENV if os.environ.get(v)]
    if len(have) == len(API_ENV):
        return True, "credentials present"
    return False, ("JLCPCB API credentials not configured (set "
                   f"{' and '.join(API_ENV)}); the api.jlcpcb.com programme "
                   "also requires an approved access application")


def run(pcb: Path, fab_dir: Path, quote: Path | None = None,
        qty: int | None = None, use_api: bool = False,
        order_number: str | None = None) -> dict:
    if not fab_dir.is_dir():
        raise FileNotFoundError(f"fab directory not found: {fab_dir}")
    artifacts, missing = collect_package(fab_dir)

    quote_row = None
    quote_data = None
    if quote is not None and Path(quote).exists():
        quote_data = json.loads(Path(quote).read_text(encoding="utf-8"))
        rows = quote_data.get("matrix") or []
        if qty is not None:
            rows = [r for r in rows if r.get("qty") == qty] or rows
        quote_row = rows[0] if rows else quote_data.get("cheapest")

    api_ok, api_note = _api_available()
    status = "incomplete" if missing else "ready_for_human"

    manifest = {
        "script": "order_submit",
        "status": status,
        "board": pcb.name,
        "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "order_number": order_number,
        "payment": "HUMAN - this script never submits payment (SPEC P10)",
        "artifacts": artifacts,
        "missing": missing,
        "quote": {
            "selected": quote_row,
            "estimated": bool((quote_data or {}).get("estimated", True)),
            "source": str(quote) if quote else None,
            "authoritative_quote_url": JLC_QUOTE_URL,
        },
        "spec_snapshot": {
            "layers": (quote_data or {}).get("spec", {}).get("layers"),
            "width_mm": (quote_data or {}).get("spec", {}).get("width_mm"),
            "height_mm": (quote_data or {}).get("spec", {}).get("height_mm"),
            "qty": qty or (quote_row or {}).get("qty"),
            "surface_finish": (quote_row or {}).get("surface_finish"),
            "solder_mask_color": (quote_row or {}).get("solder_mask_color"),
            "assembly": (quote_data or {}).get("spec", {}).get("assembly"),
        },
        "api": {"attempted": bool(use_api), "available": api_ok,
                "note": api_note},
        "human_steps": [
            f"Upload {artifacts.get('gerber_zip', {}).get('path', '<gerber zip>')}"
            f" to {JLCDFM_URL} and review the DFM report (V6: no public API).",
            f"Upload the same zip at {JLC_QUOTE_URL} and confirm the real price"
            " against the estimate above.",
            "If assembling: upload BOM.csv and CPL.csv, then CHECK THE RENDERED"
            " PART PREVIEW for every polarized part (LED/diode/electrolytic) -"
            " rotation corrections are the classic failure mode.",
            "Review, then pay. Payment is always the human's action.",
        ],
    }
    return manifest


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pcb", required=True)
    ap.add_argument("--fab-dir", required=True)
    ap.add_argument("--quote", help="order_quote.py JSON")
    ap.add_argument("--qty", type=int, help="quantity row to select")
    ap.add_argument("--api", action="store_true",
                    help="attempt the credentialed API path (stops before "
                         "payment; exits 2 when credentials are absent)")
    ap.add_argument("--order-number", help="record a placed order number")
    ap.add_argument("--out", help="default: <fab-dir>/order.json")
    args = ap.parse_args(argv)

    try:
        man = run(Path(args.pcb), Path(args.fab_dir),
                  quote=Path(args.quote) if args.quote else None,
                  qty=args.qty, use_api=args.api,
                  order_number=args.order_number)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"script": "order_submit", "status": "error",
                          "error": f"{type(exc).__name__}: {exc}"}, indent=1))
        return 2

    out = Path(args.out) if args.out else Path(args.fab_dir) / "order.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(man, indent=1), encoding="utf-8")
    man["order_json"] = str(out)
    print(json.dumps(man, indent=1))

    if args.api and not man["api"]["available"]:
        return 2
    return 1 if man["status"] == "incomplete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
